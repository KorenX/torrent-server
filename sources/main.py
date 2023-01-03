from TorrentServer import TorrentServer

SELF_IP = "0.0.0.0"
MAIN_PORT = 9001

def main():
    print("starting server")
    srv = TorrentServer(SELF_IP, MAIN_PORT)
    srv.handle_messages()


if __name__ == "__main__":
    main()
    exit(0)
else:
    print("You shouldn't import main!")
    exit(1)