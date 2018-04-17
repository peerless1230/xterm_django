
class WebSocketError(Exception):
    """Exception raised during websocket operations into errors."""
    pass


class WebSocketClosedError(WebSocketError):
    """Exception raised during websocket closing into errors."""
    pass


class SSHShellException(Exception):
    """Exception raised during deal with SSHShell channel."""
    pass

class InvalidSchema(Exception):
    """Exception raised during the schema of request's URL invaild."""
    pass