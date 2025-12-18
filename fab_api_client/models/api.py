"""API response types for Fab API client."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

from .domain import Asset, Listing


@dataclass
class CursorInfo:
    """Pagination cursor data."""
    next: Optional[str] = None
    previous: Optional[str] = None


@dataclass
class LibrarySearchResponse:
    """
    Paginated API response from /i/library/entitlements/search.
    
    Represents one page of library results.
    """
    results: List[Dict[str, Any]]
    cursors: Optional[CursorInfo] = None
    next: Optional[str] = None
    aggregations: Optional[Dict[str, Any]] = None
    
    def to_assets(self) -> List[Asset]:
        """Convert raw API results to Asset domain models."""
        assets = []
        for result in self.results:
            # Extract listing data
            listing_data = result.get('listing', {})
            listing = None
            if listing_data:
                listing = Listing(
                    title=listing_data.get('title', ''),
                    description=listing_data.get('description'),
                    tags=listing_data.get('tags', []),
                    raw_data=listing_data
                )
            
            # Parse created_at timestamp
            created_at = None
            created_at_str = result.get('createdAt')
            if created_at_str:
                try:
                    # Handle ISO format: "2024-12-17T15:30:00.000Z"
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass
            
            # Extract title (from listing or fallback)
            title = ''
            if listing:
                title = listing.title
            elif 'title' in result:
                title = result['title']
            
            assets.append(Asset(
                uid=result.get('uid', ''),
                title=title,
                created_at=created_at,
                listing=listing,
                raw_data=result
            ))
        
        return assets
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LibrarySearchResponse':
        """Create LibrarySearchResponse from API response dictionary."""
        cursors = None
        cursor_data = data.get('cursors', {})
        if cursor_data:
            cursors = CursorInfo(
                next=cursor_data.get('next'),
                previous=cursor_data.get('previous')
            )
        
        return cls(
            results=data.get('results', []),
            cursors=cursors,
            next=data.get('next'),
            aggregations=data.get('aggregations')
        )


@dataclass
class AssetFormatsResponse:
    """
    Raw file format data from /i/library/entitlements/{uid}/asset-formats.
    
    API returns a list of format objects directly.
    """
    formats: List[Dict[str, Any]]
    
    def find_unreal_file_uid(self) -> Optional[str]:
        """
        Find file UID for Unreal Engine format.
        
        Returns:
            File UID if found, None otherwise
        """
        for format_obj in self.formats:
            if not isinstance(format_obj, dict):
                continue
            
            # Check assetFormatType
            format_type = format_obj.get('assetFormatType', {})
            if isinstance(format_type, dict) and format_type.get('code') == 'unreal-engine':
                files = format_obj.get('files', [])
                if files and isinstance(files, list):
                    for f in files:
                        if isinstance(f, dict) and 'uid' in f:
                            return f['uid']
        
        return None
    
    @classmethod
    def from_api_response(cls, data: Any) -> 'AssetFormatsResponse':
        """
        Create from API response.
        
        API returns either a list directly or a dict with 'assetFormats' key.
        """
        if isinstance(data, list):
            return cls(formats=data)
        elif isinstance(data, dict):
            # Try 'assetFormats' key
            if 'assetFormats' in data:
                return cls(formats=data['assetFormats'])
            # Otherwise treat dict as single format
            return cls(formats=[data])
        else:
            return cls(formats=[])


@dataclass
class DownloadInfoResponse:
    """
    Raw download info from download-info endpoint.
    """
    download_info: List[Dict[str, Any]]
    
    def find_manifest_url(self) -> Optional[str]:
        """
        Find manifest download URL.
        
        Returns:
            Download URL if found, None otherwise
        """
        for info in self.download_info:
            if isinstance(info, dict) and info.get('type') == 'manifest':
                return info.get('downloadUrl')
        return None
    
    def get_manifest_expires(self) -> Optional[str]:
        """Get manifest download URL expiration time."""
        for info in self.download_info:
            if isinstance(info, dict) and info.get('type') == 'manifest':
                return info.get('expires')
        return None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DownloadInfoResponse':
        """Create from API response dictionary."""
        return cls(
            download_info=data.get('downloadInfo', [])
        )
