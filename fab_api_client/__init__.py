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

__version__ = "0.1.0"

# Core client
from .client import FabClient

# Authentication & Configuration
from .auth import (
    ApiEndpoints,
    FabAuthProvider,
    CookieAuthProvider,
)

# Manifest Parsing
from .manifest_parser import (
    ManifestParser,
    JsonManifestParser,
)

# Domain models
from .models.domain import (
    Library,
    Asset,
    Listing,
    License,
    Seller,
    AssetFormatType,
    TechnicalSpecs,
    AssetFormat,
    Capabilities,
    ParsedManifest,
    ManifestFile,
    DownloadResult,
)

# API response types (for advanced users)
from .models.api import (
    LibrarySearchResponse,
    CursorInfo,
    AssetFormatsResponse,
    DownloadInfoResponse,
)

# Exceptions
from .exceptions import (
    FabError,
    FabAuthenticationError,
    FabAPIError,
    FabNotFoundError,
    FabNetworkError,
)

# Utilities
from .utils import sanitize_filename

# Manifest utilities
from .manifests import validate_manifest, detect_manifest_format

__all__ = [
    # Version
    '__version__',
    # Core
    'FabClient',
    # Authentication & Configuration
    'ApiEndpoints',
    'FabAuthProvider',
    'CookieAuthProvider',
    # Manifest Parsing
    'ManifestParser',
    'JsonManifestParser',
    # Domain models
    'Library',
    'Asset',
    'Listing',
    'License',
    'Seller',
    'AssetFormatType',
    'TechnicalSpecs',
    'AssetFormat',
    'Capabilities',
    'ParsedManifest',
    'ManifestFile',
    'DownloadResult',
    # API response types
    'LibrarySearchResponse',
    'CursorInfo',
    'AssetFormatsResponse',
    'DownloadInfoResponse',
    # Exceptions
    'FabError',
    'FabAuthenticationError',
    'FabAPIError',
    'FabNotFoundError',
    'FabNetworkError',
    # Utilities
    'sanitize_filename',
    'validate_manifest',
    'detect_manifest_format',
]
