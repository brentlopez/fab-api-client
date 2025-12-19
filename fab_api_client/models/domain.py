"""Domain models for Fab API client."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class License:
    """License information for an asset."""
    name: str
    slug: str
    url: Optional[str] = None
    type: Optional[str] = None
    is_cc0: bool = False
    price_tier: Optional[str] = None
    uid: Optional[str] = None


@dataclass
class Seller:
    """Seller/creator information."""
    seller_id: str
    seller_name: str
    uid: str
    profile_image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    is_seller: bool = True


@dataclass
class AssetFormatType:
    """Asset format type information."""
    code: str
    name: str
    icon: str
    group_name: str
    extensions: List[str] = field(default_factory=list)


@dataclass
class TechnicalSpecs:
    """Technical specifications for an asset format."""
    unreal_engine_engine_versions: List[str] = field(default_factory=list)
    unreal_engine_target_platforms: List[str] = field(default_factory=list)
    unreal_engine_distribution_method: str = ""
    technical_details: Optional[str] = None


@dataclass
class AssetFormat:
    """Asset format details including technical specifications."""
    asset_format_type: AssetFormatType
    technical_specs: Optional[TechnicalSpecs] = None
    versions: List[Dict[str, Any]] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Capabilities:
    """Entitlement capabilities."""
    add_by_verse: bool = False
    request_download_url: bool = False


@dataclass
class Listing:
    """Marketplace listing details for an asset."""
    title: str
    uid: str
    listing_type: str
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    is_mature: bool = False
    last_updated_at: Optional[datetime] = None
    licenses: List[License] = field(default_factory=list)
    seller: Optional[Seller] = None
    asset_formats: List[AssetFormat] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Asset:
    """
    Unified asset/entitlement representation.
    
    Attributes:
        uid: Unique identifier for the entitlement
        title: Asset name
        created_at: When asset was added to library
        status: Entitlement status (e.g., "approved")
        capabilities: Entitlement capabilities
        granted_licenses: Licenses granted with this entitlement
        listing: Marketplace listing information
        raw_data: Complete raw API data for extensibility
    """
    uid: str
    title: str
    created_at: Optional[datetime] = None
    status: str = ""
    capabilities: Optional[Capabilities] = None
    granted_licenses: List[License] = field(default_factory=list)
    listing: Optional[Listing] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Library:
    """
    Collection of assets with metadata.
    
    Attributes:
        assets: Complete list of assets
        total_count: Total number of assets
    """
    assets: List[Asset]
    total_count: int
    
    def filter(self, predicate) -> 'Library':
        """Filter assets by predicate function."""
        filtered = [asset for asset in self.assets if predicate(asset)]
        return Library(assets=filtered, total_count=len(filtered))
    
    def find_by_uid(self, uid: str) -> Optional[Asset]:
        """Find asset by UID."""
        for asset in self.assets:
            if asset.uid == uid:
                return asset
        return None


@dataclass
class ManifestFile:
    """Individual file entry in manifest."""
    filename: str
    file_hash: str
    file_chunk_parts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ParsedManifest:
    """
    Parsed JSON manifest data.
    
    Attributes:
        version: Manifest file version
        app_id: Application ID
        app_name: Application name
        build_version: Build version string
        files: List of files in manifest
        raw_data: Complete raw manifest data
    """
    version: str
    app_id: str
    app_name: str
    build_version: str
    files: List[ManifestFile]
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParsedManifest':
        """Create ParsedManifest from dictionary."""
        files = []
        for file_data in data.get('FileManifestList', []):
            files.append(ManifestFile(
                filename=file_data.get('Filename', ''),
                file_hash=file_data.get('FileHash', ''),
                file_chunk_parts=file_data.get('FileChunkParts', [])
            ))
        
        return cls(
            version=data.get('ManifestFileVersion', ''),
            app_id=data.get('AppID', ''),
            app_name=data.get('AppNameString', ''),
            build_version=data.get('BuildVersionString', ''),
            files=files,
            raw_data=data
        )




@dataclass
class DownloadResult:
    """
    Result of manifest download operation.
    
    Attributes:
        success: Whether download was successful
        file_path: Path to downloaded manifest file
        size: File size in bytes
        error: Error message if download failed
    """
    success: bool
    file_path: Optional[Path] = None
    size: Optional[int] = None
    error: Optional[str] = None
    
    def load(self) -> ParsedManifest:
        """
        Load and parse manifest file.
        
        Returns:
            ParsedManifest object
        
        Raises:
            ValueError: If download was not successful or file doesn't exist
        """
        if not self.success or not self.file_path:
            raise ValueError("Cannot load manifest: download was not successful")
        
        if not self.file_path.exists():
            raise ValueError(f"Manifest file not found: {self.file_path}")
        
        # Read file
        with open(self.file_path, 'rb') as f:
            data = f.read()
        
        # Parse JSON
        manifest_dict = json.loads(data.decode('utf-8'))
        return ParsedManifest.from_dict(manifest_dict)
