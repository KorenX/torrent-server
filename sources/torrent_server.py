import socket
import enum
import time
from log import log
from server_db_manager import ServerDBManager

class ServerMessageTypes(enum.Enum):
    FILES_LIST = 1
    FILES_CHUNK = enum.auto()
    FILES_ACK = enum.auto()
    FILES_FIN = enum.auto()
    PEERS_LIST = enum.auto()
    PEERS_CHUNK = enum.auto()
    PEERS_ACK = enum.auto()
    PEERS_FIN = enum.auto()
    THANKS = enum.auto()

class ServerRequestMessage():
    def __init__(self, message: bytes) -> None:
        self.message_type = ord(message[0])
        self.payload = message[1:]

class FilesListMessage():
    def __init__(self, message: ServerRequestMessage) -> None:
        self.base_message = message

class FilesAckMessage():
    def __init__(self, message: ServerRequestMessage) -> None:
        self.base_message = message
        if len(self.base_message.payload) < self.CHUNK_ACK_INDEX_SIZE:
            raise IllegalMessageSizeError(ServerMessageTypes.FILES_ACK, len(message))

        self.ack_index = int(self.base_message.payload[:self.CHUNK_ACK_INDEX_SIZE])
    
    CHUNK_ACK_INDEX_SIZE = 4

class PeersListMessage():
    def __init__(self, message: ServerRequestMessage) -> None:
        self.base_message = message

class PeersAckMessage():
    def __init__(self, message: ServerRequestMessage) -> None:
        self.base_message = message
        if len(self.base_message.payload) < self.CHUNK_ACK_INDEX_SIZE:
            raise IllegalMessageSizeError(ServerMessageTypes.PEERS_ACK, len(message))

        self.ack_index = int(self.base_message.payload[:self.CHUNK_ACK_INDEX_SIZE])
    
    CHUNK_ACK_INDEX_SIZE = 4

class ThanksMessage():
    def __init__(self, message: ServerRequestMessage) -> None:
        self.base_message = message

class UserStruct():
    def __init__(self, user_id, initial_state) -> None:
        self.user_id = user_id
        self.state = initial_state
        self.last_used = time.time()
        self.last_file_id = 0
        self.last_peer_id = 0
        self.wanted_file = 0

class IllegalMessageError(Exception):
    def __init__(self, msg_type, user: UserStruct) -> None:
        self.msg_type = msg_type
        self.user = user
        
    def __str__(self) -> str:
        return f"The message type {self.msg_type} is illegal to handle in {self.user.state} for user {self.user.user_id}"

class IllegalMessageSizeError(Exception):
    def __init__(self, msg_type, msg_size) -> None:
        self.msg_type = msg_type
        self.msg_size = msg_size
        
    def __str__(self) -> str:
        return f"The message type {self.msg_type} got wrong size ({self.msg_size})"

class TorrentServer():
    def __init__(self, src_ip: str, src_port: int) -> None:
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.socket.bind((src_ip, src_port))
        self.users = {}
        self.db = ServerDBManager()

    def handle_message(self):
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
        except IllegalMessageError as e:
            log(e)
        except KeyError:
            pass
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
        
        ack_msg = FilesAckMessage(msg)
        current_user.last_file_id = ack_msg.ack_index

        response = self._create_files_info_payload(current_user)
        self.socket.sendto(response, src)

    def handle_peers_list(self, msg: ServerRequestMessage, src):
        self._add_user(src)
        current_user = self.users[src]
        if current_user.state != ServerMessageTypes.FILES_FIN and current_user.state != ServerMessageTypes.PEERS_CHUNK:
            raise IllegalMessageError(msg.message_type, current_user)

        response = self._create_peers_info_payload(current_user)
        self.socket.sendto(response, src)

    def handle_peers_ack(self, msg: ServerRequestMessage, src):
        current_user = self.users[src]
        if current_user.state != ServerMessageTypes.PEERS_CHUNK and current_user.state != ServerMessageTypes.PEERS_FIN:
            raise IllegalMessageError(msg.message_type, current_user)
        
        ack_msg = PeersAckMessage(msg)
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