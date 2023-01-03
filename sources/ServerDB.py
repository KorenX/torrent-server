from DataStructures import FileInfo, PeerInfo

class ServerDBManager():
    def get_available_files(self) -> list:
        return [FileInfo(1, "name_placeholder", "desc_placeholder")]

    def get_available_peers(self, file_id: int) -> list:
        return [PeerInfo(0x12345678)]
