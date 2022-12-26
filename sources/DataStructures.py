import struct
import time
from socket import inet_ntoa

class UserStruct():
    def __init__(self, user_id, initial_state) -> None:
        self.user_id = user_id
        self.state = initial_state
        self.last_used = time.time()
        self.last_file_id = 0
        self.last_peer_id = 0
        self.wanted_file = 0

class FileInfo():
    def __init__(self, file_id: int, file_name: str, file_desc: str) -> None:
        self.file_id = file_id
        self.file_name = file_name
        self.file_desc = file_desc
    
    def __str__(self) -> str:
        return f"{self.file_id}, {self.file_name}, {self.file_desc}:"
    
    def serialize(self) -> bytes:
        return struct.pack(f"I{self.MAX_FILE_NAME_LENGTH}s{self.MAX_FILE_DESC_LENGTH}s", self.file_id, bytes(self.file_name, "utf-8"), bytes(self.file_desc, "utf-8"))
    
    MAX_FILE_NAME_LENGTH = 32
    MAX_FILE_DESC_LENGTH = 64
    TOTAL_SIZE = 4 + MAX_FILE_NAME_LENGTH + MAX_FILE_DESC_LENGTH
    FILE_ID_FORMAT = "I"
    FILE_ID_MIN_LENGTH = 4

class PeerInfo():
    def __init__(self, peer_ip: int, peer_port : int) -> None:
        self.peer_ip = peer_ip
        self.peer_port = peer_port

    def __str__(self) -> str:
        return f'{inet_ntoa(struct.pack("!I", self.peer_ip))}:{self.peer_port}'
    
    def serialize(self) -> bytes:
        return struct.pack("IH", self.peer_ip, self.peer_port)