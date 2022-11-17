import struct
from socket import inet_ntoa

class FileInfo():
    def __init__(self, file_id: int, file_name: str, file_desc: str) -> None:
        self.file_id = file_id
        self.file_name = file_name
        self.file_desc = file_desc
    
    def __str__(self) -> str:
        return f"{self.file_id}, {self.file_name}, {self.file_desc}:"
    
    def serialize(self) -> bytes:
        return struct.pack(f"I{self.MAX_FILE_NAME_LENGTH}s{self.MAX_FILE_DESC_LENGTH}s", self.file_id, self.file_name, self.file_desc)
    
    MAX_FILE_NAME_LENGTH = 64
    MAX_FILE_DESC_LENGTH = 128
    TOTAL_SIZE = 4 + MAX_FILE_NAME_LENGTH + MAX_FILE_DESC_LENGTH
    FILE_ID_FORMAT = "I"
    FILE_ID_MIN_LENGTH = 4

class PeerInfo():
    def __init__(self, peer_ip: int) -> None:
        self.peer_ip = peer_ip

    def __str__(self) -> str:
        return inet_ntoa(struct.pack("!I", self.peer_ip))
    
    def serialize(self) -> bytes:
        return struct.pack("I", self.peer_ip)

class ServerDBManager():
    def get_available_files(self) -> list:
        return [FileInfo(0, "name_placeholder", "desc_placeholder")]

    def get_available_peers(self, file_id: int) -> list:
        return [PeerInfo(0)]
