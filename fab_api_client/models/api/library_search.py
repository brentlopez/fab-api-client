"""Library search API response types."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..domain import (
    Asset,
    Listing,
    License,
    Seller,
    AssetFormatType,
    TechnicalSpecs,
    AssetFormat,
    Capabilities,
)
from .cursor import CursorInfo


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
                # Parse tags (extract slug from tag objects)
                tags = []
                for tag in listing_data.get('tags', []):
                    if isinstance(tag, dict):
                        tags.append(tag.get('slug', ''))
                    elif isinstance(tag, str):
                        tags.append(tag)
                
                # Parse listing licenses
                listing_licenses = []
                for lic_data in listing_data.get('licenses', []):
                    if isinstance(lic_data, dict):
                        listing_licenses.append(License(
                            name=lic_data.get('name', ''),
                            slug=lic_data.get('slug', ''),
                            url=lic_data.get('url'),
                            type=lic_data.get('type'),
                            is_cc0=lic_data.get('isCc0', False),
                            price_tier=lic_data.get('priceTier'),
                            uid=lic_data.get('uid')
                        ))
                
                # Parse seller/user info
                seller = None
                user_data = listing_data.get('user', {})
                if user_data and isinstance(user_data, dict):
                    seller = Seller(
                        seller_id=user_data.get('sellerId', ''),
                        seller_name=user_data.get('sellerName', ''),
                        uid=user_data.get('uid', ''),
                        profile_image_url=user_data.get('profileImageUrl'),
                        cover_image_url=user_data.get('coverImageUrl'),
                        is_seller=user_data.get('isSeller', True)
                    )
                
                # Parse asset formats
                asset_formats = []
                for fmt_data in listing_data.get('assetFormats', []):
                    if isinstance(fmt_data, dict):
                        # Parse asset format type
                        fmt_type_data = fmt_data.get('assetFormatType', {})
                        asset_format_type = AssetFormatType(
                            code=fmt_type_data.get('code', ''),
                            name=fmt_type_data.get('name', ''),
                            icon=fmt_type_data.get('icon', ''),
                            group_name=fmt_type_data.get('groupName', ''),
                            extensions=fmt_type_data.get('extensions', [])
                        )
                        
                        # Parse technical specs
                        tech_specs = None
                        tech_specs_data = fmt_data.get('technicalSpecs', {})
                        if tech_specs_data and isinstance(tech_specs_data, dict):
                            tech_specs = TechnicalSpecs(
                                unreal_engine_engine_versions=tech_specs_data.get('unrealEngineEngineVersions', []),
                                unreal_engine_target_platforms=tech_specs_data.get('unrealEngineTargetPlatforms', []),
                                unreal_engine_distribution_method=tech_specs_data.get('unrealEngineDistributionMethod', ''),
                                technical_details=tech_specs_data.get('technicalDetails')
                            )
                        
                        asset_formats.append(AssetFormat(
                            asset_format_type=asset_format_type,
                            technical_specs=tech_specs,
                            versions=fmt_data.get('versions', []),
                            raw_data=fmt_data
                        ))
                
                # Parse last updated timestamp
                last_updated_at = None
                last_updated_str = listing_data.get('lastUpdatedAt')
                if last_updated_str:
                    try:
                        last_updated_at = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        pass
                
                listing = Listing(
                    title=listing_data.get('title', ''),
                    uid=listing_data.get('uid', ''),
                    listing_type=listing_data.get('listingType', ''),
                    description=listing_data.get('description'),
                    tags=tags,
                    is_mature=listing_data.get('isMature', False),
                    last_updated_at=last_updated_at,
                    licenses=listing_licenses,
                    seller=seller,
                    asset_formats=asset_formats,
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
            
            # Parse capabilities
            capabilities = None
            cap_data = result.get('capabilities', {})
            if cap_data and isinstance(cap_data, dict):
                capabilities = Capabilities(
                    add_by_verse=cap_data.get('addByVerse', False),
                    request_download_url=cap_data.get('requestDownloadUrl', False)
                )
            
            # Parse granted licenses (top-level, distinct from listing licenses)
            granted_licenses = []
            for lic_data in result.get('licenses', []):
                if isinstance(lic_data, dict):
                    granted_licenses.append(License(
                        name=lic_data.get('name', ''),
                        slug=lic_data.get('slug', ''),
                        url=lic_data.get('url'),
                        type=lic_data.get('type'),
                        is_cc0=lic_data.get('isCc0', False),
                        price_tier=lic_data.get('priceTier'),
                        uid=lic_data.get('uid')
                    ))
            
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
                status=result.get('status', ''),
                capabilities=capabilities,
                granted_licenses=granted_licenses,
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
