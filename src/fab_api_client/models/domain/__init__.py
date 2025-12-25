"""Domain models for Fab API client."""

from .asset import Asset
from .asset_format import AssetFormat, AssetFormatType, TechnicalSpecs
from .capabilities import Capabilities
from .library import Library
from .license import License
from .listing import Listing
from .manifest import (
    DownloadResult,
    ManifestDownloadResult,
    ManifestFile,
    ParsedManifest,
)
from .seller import Seller

__all__ = [
    "Asset",
    "AssetFormat",
    "AssetFormatType",
    "Capabilities",
    "DownloadResult",  # Backward compatibility alias
    "ManifestDownloadResult",
    "License",
    "Library",
    "Listing",
    "ManifestFile",
    "ParsedManifest",
    "Seller",
    "TechnicalSpecs",
]
