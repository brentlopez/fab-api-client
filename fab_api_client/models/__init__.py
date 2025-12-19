"""Models package for Fab API client."""

from .domain import (
    Asset,
    Library,
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

from .api import (
    LibrarySearchResponse,
    CursorInfo,
    AssetFormatsResponse,
    DownloadInfoResponse,
)

__all__ = [
    # Domain models
    'Asset',
    'Library',
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
]
