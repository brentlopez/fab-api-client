"""Exception types for Fab API client."""

from typing import Any, Optional

from asset_marketplace_core import (
    MarketplaceAPIError,
    MarketplaceAuthenticationError,
    MarketplaceError,
    MarketplaceNetworkError,
    MarketplaceNotFoundError,
)


class FabError(MarketplaceError):
    """Base exception for all Fab API errors.

    Inherits from MarketplaceError for multi-platform compatibility.
    """

    pass


class FabAuthenticationError(FabError, MarketplaceAuthenticationError):
    """Raised when authentication fails (401, 403).

    Inherits from both FabError and MarketplaceAuthenticationError
    for backward and forward compatibility.
    """

    pass


class FabAPIError(FabError, MarketplaceAPIError):
    """Raised for HTTP errors from Fab API.

    Inherits from both FabError and MarketplaceAPIError
    for backward and forward compatibility.
    """

    def __init__(
        self, message: str, status_code: Optional[int] = None, response: Any = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class FabNotFoundError(FabError, MarketplaceNotFoundError):
    """Raised when a resource is not found (404).

    Inherits from both FabError and MarketplaceNotFoundError
    for backward and forward compatibility.
    """

    pass


class FabNetworkError(FabError, MarketplaceNetworkError):
    """Raised for network-related errors (timeouts, connection errors).

    Inherits from both FabError and MarketplaceNetworkError
    for backward and forward compatibility.
    """

    pass
