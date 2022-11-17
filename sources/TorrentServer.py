import socket
from Exceptions import *
from ServerMessages import *
from Log import log
from ServerDB import *
import select

class TorrentServer():
    def __init__(self, src_ip: str, src_port: int) -> None:
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.socket.bind((src_ip, src_port))
        self.users = {}
        self.db = ServerDBManager()

    def handle_messages(self):
        try:
            while True:
                ready = select.select([self.socket], [], [], 1)
                if ready[0]:
                    self._handle_message()
        except Exception as e:
            log(e)

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
                case _:
                    raise IllegalMessageError(msg.message_type, self.users[src])
        finally:
            self.clear_unused()
    
    def handle_files_list(self, msg: ServerRequestMessage, src):
        self._add_user(src)
        current_user = self.users[src]
        if current_user.state != ServerMessageTypes.FILES_LIST and current_user.state != ServerMessageTypes.FILES_CHUNK:
            raise IllegalMessageError(msg.message_type, current_user)

        response = self._create_files_info_payload(current_user)
        self.socket.sendto(response, src)

    def handle_files_ack(self, msg: ServerRequestMessage, src):
        current_user = self.users[src]
        if current_user.state != ServerMessageTypes.FILES_CHUNK and current_user.state != ServerMessageTypes.FILES_FIN:
            raise IllegalMessageError(msg.message_type, current_user)
        
        ack_msg = AckMessage(msg)
        current_user.last_file_id = ack_msg.ack_index

        response = self._create_files_info_payload(current_user)
        self.socket.sendto(response, src)

    def handle_peers_list(self, msg: ServerRequestMessage, src):
        self._add_user(src)
        current_user = self.users[src]
        if current_user.state != ServerMessageTypes.FILES_FIN and current_user.state != ServerMessageTypes.PEERS_CHUNK:
            raise IllegalMessageError(msg.message_type, current_user)

        peers_msg = PeersListMessage(msg)
        current_user.wanted_file = peers_msg.file_id

        response = self._create_peers_info_payload(current_user)
        self.socket.sendto(response, src)

    def handle_peers_ack(self, msg: ServerRequestMessage, src):
        current_user = self.users[src]
        if current_user.state != ServerMessageTypes.PEERS_CHUNK and current_user.state != ServerMessageTypes.PEERS_FIN:
            raise IllegalMessageError(msg.message_type, current_user)
        
        ack_msg = AckMessage(msg)
        current_user.last_peer_id = ack_msg.ack_index

        response = self._create_peers_info_payload(current_user)
        self.socket.sendto(response, src)
    
    def handle_thanks(self, msg: ServerRequestMessage, src):
        current_user = self.users[src]
        if current_user.state != ServerMessageTypes.FILES_FIN and current_user.state != ServerMessageTypes.PEERS_FIN:
            raise IllegalMessageError(msg.message_type, current_user)
        
        self._remove_user(src)

    def _clear_unused(self) -> None:
        to_remove = []
        for user in self.users:
            if time.time() - user.last_used < self.UNUSED_TIME_INTERVAL:
                to_remove.append(user.user_id)
        
        for user_id in to_remove:
            self._remove_user(user_id)
    
    def _add_user(self, user_id) -> None:
        if user_id not in self.users.keys():
            log(f"new user connected, id: {user_id} time: {time.time()}")
            self.users[user_id] = UserStruct(user_id, ServerMessageTypes.FILES_LIST)

    def _remove_user(self, user_id) -> None:
        try:
            self.users.pop(user_id)
        except KeyError as e:
            pass
    
    def _create_files_info_payload(self, user: UserStruct) -> bytes:
        files = self.db.get_available_files()
        if len(files) <= user.last_file_id:
            user.state = ServerMessageTypes.FILES_FIN
            return self._create_finish_message(ServerMessageTypes.FILES_FIN)
        
        user.last_file_id = max(0, user.last_file_id)

        payload = bytes()
        for finfo in files[user.last_file_id:][:self.MAX_FILES_INFO_IN_MESSAGE]:
            payload += finfo.serialize()
        
        user.state = ServerMessageTypes.FILES_CHUNK
        return payload

    def _create_peers_info_payload(self, user: UserStruct) -> bytes:
        peers_info = self.db.get_available_peers(user.wanted_file)
        if len(peers_info) <= user.last_peer_id:
            user.state = ServerMessageTypes.PEERS_FIN
            return self._create_finish_message(ServerMessageTypes.PEERS_FIN)
        
        user.last_peer_id = max(0, user.last_peer_id)

        payload = bytes()
        for pinfo in peers_info[user.last_peer_id:][:self.MAX_PEERS_INFO_IN_MESSAGE]:
            payload += pinfo.serialize()
        
        user.state = ServerMessageTypes.PEERS_CHUNK
        return payload
    
    def _create_finish_message(self, message_type) -> bytes:
        return bytes([message_type])

    PACKET_MAX_SIZE = 128
    UNUSED_TIME_INTERVAL = 60 #seconds
    MAX_FILES_INFO_IN_MESSAGE = 8
    MAX_PEERS_INFO_IN_MESSAGE = 8