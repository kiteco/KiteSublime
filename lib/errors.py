class ExpectedError(Exception):
    """Raised when an expected error happens.
    """
    def __init__(self, exc, message):
        self.exc = exc
        self.message = message
