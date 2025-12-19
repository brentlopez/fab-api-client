"""Listing domain model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

from .license import License
from .seller import Seller
from .asset_format import AssetFormat


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
