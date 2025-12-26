"""Asynchronous authentication and endpoint configuration for Fab API client."""

from typing import Any, Optional

import aiohttp
from asset_marketplace_core import AsyncAuthProvider

from .sync import FabEndpoints


class AsyncCookieAuthProvider(AsyncAuthProvider):
    """Asynchronous cookie-based authentication provider with security best practices.

    This is a generic async implementation that requires all configuration
    to be provided explicitly - no hardcoded values. Uses aiohttp for
    async HTTP requests.

        Example:
        >>> async with AsyncCookieAuthProvider(
        ...     cookies={...}, endpoints=endpoints
        ... ) as auth:
        ...     session = await auth.get_session()
        ...     async with session.get(url) as response:
        ...         data = await response.json()
    """

    def __init__(
        self,
        cookies: dict[str, str],
        endpoints: FabEndpoints,
        user_agent: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
        verify_ssl: bool = True,
        timeout: Optional[aiohttp.ClientTimeout] = None,
    ) -> None:
        """Initialize async cookie-based authentication.

        Args:
            cookies: Dictionary of cookies for authentication
            endpoints: API endpoint configuration
            user_agent: Optional user agent string (defaults to fab-api-client/2.1.0)
            headers: Optional additional headers
            verify_ssl: Whether to verify SSL certificates (always True in production)
            timeout: Optional aiohttp timeout configuration
                (defaults to 5s connect, 30s total)
        """
        self.cookies = cookies
        self.endpoints = endpoints
        self.user_agent = user_agent or "fab-api-client/2.1.0"
        self.headers = headers or {}
        self.verify_ssl = verify_ssl
        self.timeout = timeout or aiohttp.ClientTimeout(
            total=30, connect=5, sock_connect=5, sock_read=30
        )
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> Any:
        """Create and configure an aiohttp session with security settings.

        Returns:
            Configured aiohttp.ClientSession with cookies, headers,
            and security settings

        Note:
            Session is lazily initialized and reused across calls.
            Call close() or use context manager to clean up properly.
        """
        if self._session is None or self._session.closed:
            # Prepare headers
            session_headers = {
                "User-Agent": self.user_agent,
                **self.headers,
            }

            # Create session with security settings
            # Note: aiohttp TCPConnector ssl parameter is bool or SSLContext
            # If verify_ssl is True, pass True (default SSL verification)
            # If verify_ssl is False, pass False (disable SSL verification)
            self._session = aiohttp.ClientSession(
                cookies=self.cookies,
                headers=session_headers,
                timeout=self.timeout,
                connector=aiohttp.TCPConnector(ssl=self.verify_ssl, limit=100),
            )

        return self._session

    def get_endpoints(self) -> FabEndpoints:
        """Return the configured endpoints.

        Returns:
            FabEndpoints configuration
        """
        return self.endpoints

    async def close(self) -> None:
        """Close the aiohttp session and clean up resources.

        Should be called when done with the auth provider to ensure
        proper cleanup of network connections.

        When using the async context manager, this is called automatically.
        """
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> "AsyncCookieAuthProvider":
        """Enter async context manager.

        Returns:
            Self for use in async with statement
        """
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager and clean up resources.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        await self.close()
