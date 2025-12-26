"""
Fab API Client - Python library for generic marketplace API access.

This library provides pluggable abstractions for API authentication,
endpoint configuration, and manifest parsing.

Example:
    >>> from fab_api_client import FabClient, CookieAuthProvider, ApiEndpoints
    >>> endpoints = ApiEndpoints(
    ...     library_search="https://example.com/library/search",
    ...     asset_formats="https://example.com/assets/{asset_uid}/formats",
    ...     download_info="https://example.com/assets/{asset_uid}/files/{file_uid}/download"
    ... )
    >>> auth = CookieAuthProvider(cookies={...}, endpoints=endpoints)
    >>> client = FabClient(auth=auth)
    >>> library = client.get_library()
"""

__version__ = "2.1.0"

# Core client
# Authentication & Configuration
from .auth import (
    ApiEndpoints,  # Backward compatibility alias
    CookieAuthProvider,
    FabAuthProvider,
    FabEndpoints,
)
from .client import FabClient

# Async support (optional - requires aiohttp)
_async_available = False
try:
    from .auth import AsyncCookieAuthProvider  # noqa: F401
    from .client import FabAsyncClient  # noqa: F401

    _async_available = True
except ImportError:
    # aiohttp not installed - async support not available
    pass

# Exceptions
from .exceptions import (
    FabAPIError,
    FabAuthenticationError,
    FabError,
    FabNetworkError,
    FabNotFoundError,
)

# Manifest Parsing
from .manifest_parser import (
    JsonManifestParser,
    ManifestParser,
)

# Manifest utilities
from .manifests import detect_manifest_format, validate_manifest

# API response types (for advanced users)
from .models.api import (
    AssetFormatsResponse,
    CursorInfo,
    DownloadInfoResponse,
    LibrarySearchResponse,
)

# Domain models
from .models.domain import (
    Asset,
    AssetFormat,
    AssetFormatType,
    Capabilities,
    DownloadResult,  # Backward compatibility alias for ManifestDownloadResult
    Library,
    License,
    Listing,
    ManifestDownloadResult,
    ManifestFile,
    ParsedManifest,
    Seller,
    TechnicalSpecs,
)

# Utilities
from .utils import sanitize_filename

__all__ = [
    # Version
    "__version__",
    # Core
    "FabClient",
    # Authentication & Configuration
    "ApiEndpoints",  # Backward compatibility
    "FabEndpoints",
    "FabAuthProvider",
    "CookieAuthProvider",
    # Manifest Parsing
    "ManifestParser",
    "JsonManifestParser",
    # Domain models
    "Library",
    "Asset",
    "Listing",
    "License",
    "Seller",
    "AssetFormatType",
    "TechnicalSpecs",
    "AssetFormat",
    "Capabilities",
    "ParsedManifest",
    "ManifestFile",
    "ManifestDownloadResult",
    "DownloadResult",  # Backward compatibility
    # API response types
    "LibrarySearchResponse",
    "CursorInfo",
    "AssetFormatsResponse",
    "DownloadInfoResponse",
    # Exceptions
    "FabError",
    "FabAuthenticationError",
    "FabAPIError",
    "FabNotFoundError",
    "FabNetworkError",
    # Utilities
    "sanitize_filename",
    "validate_manifest",
    "detect_manifest_format",
]

# Add async exports if available
if _async_available:
    __all__.extend(
        [
            "FabAsyncClient",
            "AsyncCookieAuthProvider",
        ]
    )
