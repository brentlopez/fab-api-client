"""Listing domain model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .asset_format import AssetFormat
from .license import License
from .seller import Seller


@dataclass
class Listing:
    """Marketplace listing details for an asset."""

    title: str
    uid: str
    listing_type: str
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    is_mature: bool = False
    last_updated_at: Optional[datetime] = None
    licenses: list[License] = field(default_factory=list)
    seller: Optional[Seller] = None
    asset_formats: list[AssetFormat] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)
