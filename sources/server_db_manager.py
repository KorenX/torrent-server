
class FileInfo():
    def __init__(self, file_id: int, file_name: str, file_desc: str) -> None:
        self.file_id = file_id
        self.file_name = file_name
        self.file_desc = file_desc
    
    def __str__(self) -> str:
        file_id_len = len(str(self.file_id))
        file_name_len = len(self.file_name)
        file_desc_len = len(self.file_desc)

        available_file_name_len = max(self.MAX_FILE_STRING_LENGTH - file_id_len, 0)
        available_file_desc_len = max(available_file_name_len - file_name_len, 0)
        return f"{self.file_id},{self.file_name[:min(available_file_name_len, file_name_len)]},{self.file_desc[:min(available_file_desc_len, file_desc_len)]}:"
    
    def serialize(self) -> bytes:
        return bytes(str(self))
    
    MAX_FILE_STRING_LENGTH = 128 - len(",,:")

class PeerInfo():
    def __init__(self, peer_ip: int) -> None:
        self.peer_ip = peer_ip

    def __str__(self) -> str:
        return f"{self.peer_ip}:"
    
    def serialize(self) -> bytes:
        return bytes([self.peer_ip])
    
    MAX_PEER_INFO_LENGTH = 5

class ServerDBManager():
    def get_available_files(self) -> list:
        return [FileInfo(0, "name_placeholder", "desc_placeholder")]

    def get_available_peers(self, file_id: int) -> list:
        return [PeerInfo(0)]
