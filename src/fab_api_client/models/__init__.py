"""Models package for Fab API client."""

from .api import (
    AssetFormatsResponse,
    CursorInfo,
    DownloadInfoResponse,
    LibrarySearchResponse,
)
from .domain import (
    Asset,
    AssetFormat,
    AssetFormatType,
    Capabilities,
    DownloadResult,
    Library,
    License,
    Listing,
    ManifestFile,
    ParsedManifest,
    Seller,
    TechnicalSpecs,
)

__all__ = [
    # Domain models
    "Asset",
    "Library",
    "Listing",
    "License",
    "Seller",
    "AssetFormatType",
    "TechnicalSpecs",
    "AssetFormat",
    "Capabilities",
    "ParsedManifest",
    "ManifestFile",
    "DownloadResult",
    # API response types
    "LibrarySearchResponse",
    "CursorInfo",
    "AssetFormatsResponse",
    "DownloadInfoResponse",
]
