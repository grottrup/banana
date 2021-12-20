class IMAPError(Exception):
    def __init__(self, returned_message) -> None:
        self.message = returned_message
        super().__init__(self.message)