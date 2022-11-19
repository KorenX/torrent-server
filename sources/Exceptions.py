import time

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
