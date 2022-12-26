import enum
import ServerDB
import struct
from Exceptions import *

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
    REGISTER = enum.auto()
    REGISTER_ACK = enum.auto()

class ServerRequestMessage():
    def __init__(self, message: bytes) -> None:
        self.message_type = ServerMessageTypes(message[0])
        self.payload = message[1:]

class FilesListMessage():
    def __init__(self, message: ServerRequestMessage) -> None:
        self.base_message = message

class AckMessage():
    def __init__(self, message: ServerRequestMessage) -> None:
        self.base_message = message
        if len(self.base_message.payload) < self.CHUNK_ACK_INDEX_SIZE:
            raise IllegalMessageSizeError(message.message_type, len(message))

        self.ack_index = struct.unpack("I", self.base_message.payload[:self.CHUNK_ACK_INDEX_SIZE])[0]
    
    CHUNK_ACK_INDEX_SIZE = 4

class PeersListMessage():
    def __init__(self, message: ServerRequestMessage) -> None:
        self.base_message = message
        if len(self.base_message.payload) < ServerDB.FileInfo.FILE_ID_MIN_LENGTH:
            raise IllegalMessageSizeError(message.message_type, len(message))

        self.file_id = struct.unpack(ServerDB.FileInfo.FILE_ID_FORMAT, self.base_message.payload[:ServerDB.FileInfo.FILE_ID_MIN_LENGTH])[0]

class ThanksMessage():
    def __init__(self, message: ServerRequestMessage) -> None:
        self.base_message = message
