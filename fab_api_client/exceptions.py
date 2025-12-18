"""Exception types for Fab API client."""


class FabError(Exception):
    """Base exception for all Fab API errors."""
    pass


class FabAuthenticationError(FabError):
    """Raised when authentication fails (401, 403)."""
    pass


class FabAPIError(FabError):
    """Raised for HTTP errors from Fab API."""
    
    def __init__(self, message: str, status_code: int = None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class FabNotFoundError(FabError):
    """Raised when a resource is not found (404)."""
    pass


class FabNetworkError(FabError):
    """Raised for network-related errors (timeouts, connection errors)."""
    pass
