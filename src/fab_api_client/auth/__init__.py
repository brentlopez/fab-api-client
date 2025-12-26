"""Authentication and endpoint configuration for Fab API client.

This module provides both synchronous and asynchronous authentication providers.
"""

# Sync authentication (always available)
from .sync import ApiEndpoints, CookieAuthProvider, FabAuthProvider, FabEndpoints

__all__ = [
    # Sync exports
    "FabAuthProvider",
    "CookieAuthProvider",
    "FabEndpoints",
    "ApiEndpoints",  # Backward compatibility alias
]

# Async authentication (optional - requires aiohttp)
try:
    from .async_ import AsyncCookieAuthProvider  # noqa: F401

    __all__.extend(["AsyncCookieAuthProvider"])
except ImportError:
    # aiohttp not installed - async support not available
    pass
