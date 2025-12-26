"""Authentication and endpoint configuration for Fab API client."""

from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional

import requests
from asset_marketplace_core import AuthProvider, EndpointConfig


@dataclass
class FabEndpoints(EndpointConfig):
    """Configuration for Fab API endpoint URLs.

    Extends EndpointConfig from core library with Fab-specific endpoints.

    Attributes:
        base_url: Base URL for the API (inherited from EndpointConfig)
        library_search: URL for library search endpoint
        asset_formats: URL template for asset formats (use {asset_uid})
        download_info: URL template for download info (use {asset_uid}, {file_uid})
    """

    library_search: str
    asset_formats: str
    download_info: str


# Backward compatibility alias
ApiEndpoints = FabEndpoints


class FabAuthProvider(AuthProvider):
    """Abstract base class for Fab authentication providers.

    Extends AuthProvider from core library with Fab-specific type hints.
    Implementations must provide both session configuration and endpoint URLs.
    """

    @abstractmethod
    def get_session(self) -> requests.Session:
        """Return configured requests.Session with authentication.

        Returns:
            Configured Session object ready for API requests
        """
        pass

    @abstractmethod
    def get_endpoints(self) -> FabEndpoints:
        """Return Fab API endpoint configuration.

        Returns:
            FabEndpoints with URL configuration
        """
        pass


class CookieAuthProvider(FabAuthProvider):
    """Generic cookie-based authentication provider with security best practices.

    This is a generic implementation that requires all configuration
    to be provided explicitly - no hardcoded values.
    """

    def __init__(
        self,
        cookies: dict[str, str],
        endpoints: FabEndpoints,
        user_agent: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
        verify_ssl: bool = True,
        timeout: tuple = (5, 30),
    ) -> None:
        """Initialize cookie-based authentication.

        Args:
            cookies: Dictionary of cookies for authentication
            endpoints: API endpoint configuration
            user_agent: Optional user agent string (defaults to fab-api-client/2.0.0)
            headers: Optional additional headers
            verify_ssl: Whether to verify SSL certificates (always True in production)
            timeout: Request timeout tuple (connect_timeout, read_timeout) in seconds
        """
        self.cookies = cookies
        self.endpoints = endpoints
        self.user_agent = user_agent or "fab-api-client/2.0.0"
        self.headers = headers or {}
        self.verify_ssl = verify_ssl
        self.timeout = timeout

    def get_session(self) -> requests.Session:
        """Create and configure a requests session with security settings.

        Returns:
            Configured Session with cookies, headers, and security settings
        """
        session = requests.Session()

        # Security: Always verify SSL certificates in production
        session.verify = self.verify_ssl

        # Set cookies for authentication
        session.cookies.update(self.cookies)

        # Set user agent
        session.headers["User-Agent"] = self.user_agent

        # Add any additional headers
        session.headers.update(self.headers)

        return session

    def get_endpoints(self) -> FabEndpoints:
        """Return the configured endpoints.

        Returns:
            FabEndpoints configuration
        """
        return self.endpoints
