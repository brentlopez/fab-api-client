"""Fab API client implementations.

This module provides both synchronous and asynchronous marketplace clients.
"""

# Sync client (always available)
from .sync import FabClient

__all__ = [
    # Sync exports
    "FabClient",
]

# Async client (optional - requires aiohttp)
try:
    from .async_ import FabAsyncClient  # noqa: F401

    __all__.extend(["FabAsyncClient"])
except ImportError:
    # aiohttp not installed - async support not available
    pass
