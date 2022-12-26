from DataStructures import FileInfo, PeerInfo
from Log import log

class ServerDBManager():

    def __init__(self):
        self.files = []
        self.clients_to_files = {}

    def get_available_files(self) -> list:
        return self.files

    def get_available_peers(self, file_id: int) -> list:
        peers = []
        for client in self.clients_to_files.keys():
            for client_file in self.clients_to_files[client]:
                if client_file.file_id == file_id:
                    peers.append(client)
                    break

        return peers

    def add_client(self, client: PeerInfo):
        for known_client in self.clients_to_files.keys():
            if client.peer_ip == known_client.peer_ip:
                known_client.peer_port = client.peer_port
                return

        # adding all files to all clients. should be changed when we have files information.
        self.clients_to_files[client] = self.files

    def add_file(self, file: FileInfo):
        for known_file in self.files:
            if file.file_id == known_file.file_id:
                log("Tried to add an already existing file")
                return

        self.files.append(file)
