import socket
from Exceptions import *
from ServerMessages import *
from Log import log
from ServerDB import *
import select
import time

class TorrentServer():
    def __init__(self, src_ip: str, src_port: int) -> None:
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
        self.socket.bind((src_ip, src_port))
        self.users = {}
        self.db = ServerDBManager()

        #adding default values:
        self.db.add_file(FileInfo(1, "name_placeholder", "desc_placeholder"))
        self.db.add_client(PeerInfo(0x7f00001, 23523))

    def handle_messages(self):
        while True:
            ready = select.select([self.socket], [], [], 1)
            if ready[0]:
                self._handle_message()
            else:
                self._clear_unused()

    def _handle_message(self):
        packet, src = self.socket.recvfrom(self.PACKET_MAX_SIZE)
        msg = ServerRequestMessage(packet)

        try:
            match msg.message_type:
                case ServerMessageTypes.FILES_LIST:
                    self.handle_files_list(msg, src)
                case ServerMessageTypes.FILES_ACK:
                    self.handle_files_ack(msg, src)
                case ServerMessageTypes.PEERS_LIST:
                    self.handle_peers_list(msg, src)
                case ServerMessageTypes.PEERS_ACK:
                    self.handle_peers_ack(msg, src)
                case ServerMessageTypes.THANKS:
                    self.handle_thanks(msg, src)
                case ServerMessageTypes.REGISTER:
                    self.handle_register(msg, src)
                case _:
                    raise IllegalMessageError(msg.message_type, self.users[src])
        except (IllegalMessageError, IllegalMessageSizeError) as e:
            log(str(e))
    
    def handle_files_list(self, msg: ServerRequestMessage, src):
        self._add_user(src, ServerFlows.FILES_AND_PEERS)
        current_user = self.users[src]
        if current_user.state != ServerMessageTypes.FILES_LIST and current_user.state != ServerMessageTypes.FILES_CHUNK:
            raise IllegalMessageError(msg.message_type, current_user)

        self._send_files_list_response(current_user, src)

    def handle_files_ack(self, msg: ServerRequestMessage, src):
        current_user = self.users[src]
        if current_user.state != ServerMessageTypes.FILES_CHUNK and current_user.state != ServerMessageTypes.FILES_FIN:
            raise IllegalMessageError(msg.message_type, current_user)
        
        ack_msg = AckMessage(msg)
        current_user.last_file_id = ack_msg.ack_index

        self._send_files_list_response(current_user, src)

    def handle_peers_list(self, msg: ServerRequestMessage, src):
        self._add_user(src, ServerFlows.FILES_AND_PEERS)
        current_user = self.users[src]
        if current_user.state != ServerMessageTypes.FILES_FIN and current_user.state != ServerMessageTypes.PEERS_CHUNK:
            raise IllegalMessageError(msg.message_type, current_user)

        peers_msg = PeersListMessage(msg)
        current_user.wanted_file = peers_msg.file_id

        self._send_peers_list_response(current_user, src)

    def handle_peers_ack(self, msg: ServerRequestMessage, src):
        current_user = self.users[src]
        if current_user.state != ServerMessageTypes.PEERS_CHUNK and current_user.state != ServerMessageTypes.PEERS_FIN:
            raise IllegalMessageError(msg.message_type, current_user)
        
        ack_msg = AckMessage(msg)
        current_user.last_peer_id = ack_msg.ack_index

        response = self._create_peers_info_payload(current_user)
        self._send_peers_list_response(current_user, src)
    
    def handle_thanks(self, msg: ServerRequestMessage, src):
        current_user = self.users[src]
        if current_user.state != ServerMessageTypes.FILES_FIN and current_user.state != ServerMessageTypes.PEERS_FIN and current_user.state != ServerMessageTypes.REGISTER_ACK:
            raise IllegalMessageError(msg.message_type, current_user)
        
        self._remove_user(src)

    def handle_register(self, msg: ServerRequestMessage, src):
        self._add_user(src, ServerFlows.REGISTER_CLIENT)
        current_user = self.users[src]
        if current_user.state != ServerMessageTypes.REGISTER:
            raise IllegalMessageError(msg.message_type, current_user)

        request_msg = RegisterMessage(msg)
        self.db.add_client(PeerInfo(request_msg.client_ip, request_msg.client_port))

        self._send_register_ack(current_user, src)

    def _send_files_list_response(self, user: UserStruct, src) -> None:
        payload = self._create_files_info_payload(user)
        packet = bytes([user.state.value]) + payload
        self.socket.sendto(packet, src)

    def _send_peers_list_response(self, user: UserStruct, src) -> None:
        payload = self._create_peers_info_payload(user)
        packet = bytes([user.state.value]) + payload
        self.socket.sendto(packet, src)
    
    def _send_register_ack(self, user: UserStruct, src) -> None:
        user.state = ServerMessageTypes.REGISTER_ACK
        packet = bytes([user.state.value])
        self.socket.sendto(packet, src)

    def _clear_unused(self) -> None:
        to_remove = []
        for user in self.users.values():
            if time.time() - user.last_used > self.UNUSED_TIME_INTERVAL:
                to_remove.append(user.user_id)
        
        for user_id in to_remove:
            self._remove_user(user_id)
    
    def _add_user(self, user_id, server_flow : ServerFlows) -> None:
        if user_id not in self.users.keys():
            log(f"new user connected, id: {user_id} time: {time.time()}")
            if server_flow == ServerFlows.FILES_AND_PEERS:
                self.users[user_id] = UserStruct(user_id, ServerMessageTypes.FILES_LIST)
            elif server_flow == ServerFlows.REGISTER_CLIENT:
                self.users[user_id] = UserStruct(user_id, ServerMessageTypes.REGISTER)
            else:
                log(f"couldn't add user, bad server flow {server_flow}")

    def _remove_user(self, user_id) -> None:
        try:
            log(f"removing user: {user_id}")
            self.users.pop(user_id)
        except KeyError as e:
            log(e)
    
    def _create_files_info_payload(self, user: UserStruct) -> bytes:
        files = self.db.get_available_files()
        if len(files) <= user.last_file_id:
            user.state = ServerMessageTypes.FILES_FIN
            return bytes()

        user.last_file_id = max(0, user.last_file_id)

        payload = bytes()
        payload += struct.pack("I", len(files[user.last_file_id:][:self.MAX_FILES_INFO_IN_MESSAGE]))
        payload += struct.pack("I", user.last_file_id)

        for finfo in files[user.last_file_id:][:self.MAX_FILES_INFO_IN_MESSAGE]:
            payload += finfo.serialize()
        
        user.state = ServerMessageTypes.FILES_CHUNK
        return payload

    def _create_peers_info_payload(self, user: UserStruct) -> bytes:
        peers_info = self.db.get_available_peers(user.wanted_file)
        if len(peers_info) <= user.last_peer_id:
            user.state = ServerMessageTypes.PEERS_FIN
            return bytes()
        
        user.last_peer_id = max(0, user.last_peer_id)

        payload = bytes()
        payload += struct.pack("I", len(peers_info[user.last_peer_id:][:self.MAX_PEERS_INFO_IN_MESSAGE]))
        payload += struct.pack("I", user.last_peer_id)

        for pinfo in peers_info[user.last_peer_id:][:self.MAX_PEERS_INFO_IN_MESSAGE]:
            payload += pinfo.serialize()

        user.state = ServerMessageTypes.PEERS_CHUNK
        return payload
    
    PACKET_MAX_SIZE = 128
    UNUSED_TIME_INTERVAL = 60 #seconds
    MAX_FILES_INFO_IN_MESSAGE = 8
    MAX_PEERS_INFO_IN_MESSAGE = 64