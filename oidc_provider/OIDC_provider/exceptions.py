class UnsupportedResponceTypeError(Exception):
    """
    Respose type validation error
    """
    def __init__(self, description: str, code: int = 400) -> None:
        self.description = description
        self.code = code


class MissingParamsError(Exception):
    """
    Missing required authorize request parameters
    """
    def __init__(self, description: str, code: int = 400) -> None:
        self.description = description
        self.code = code


class InvalidAuthCodeError(Exception):
    """
    Invalid or expired authorization code
    """
    def __init(self, description: str, code: int = 400) -> None:
        self.description = description
        self.code = code


class InvalidClientCallbackError(Exception):
    """
    Invalid client callback uri
    """
    def __init__(self, description: str, code: int = 400) -> None:
        self.description = description
        self.code = code


class ServerError(Exception):
    def __init__(self, description: str, code: int = 500) -> None:
        self.description = description
        self.code = code