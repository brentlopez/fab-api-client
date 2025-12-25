"""Asset domain model."""

from dataclasses import dataclass, field
from typing import Optional

from asset_marketplace_core import BaseAsset

from .capabilities import Capabilities
from .license import License
from .listing import Listing


@dataclass
class Asset(BaseAsset):
    """
    Fab asset/entitlement representation.

    Extends BaseAsset from core library with Fab-specific fields.

    Attributes:
        uid: Unique identifier for the entitlement (inherited)
        title: Asset name (inherited)
        description: Asset description (inherited)
        created_at: When asset was added to library (inherited)
        updated_at: When asset was last updated (inherited)
        raw_data: Complete raw API data for extensibility (inherited)
        status: Entitlement status (e.g., "approved") - Fab-specific
        capabilities: Entitlement capabilities - Fab-specific
        granted_licenses: Licenses granted with this entitlement - Fab-specific
        listing: Marketplace listing information - Fab-specific
    """

    # Fab-specific fields
    status: str = ""
    capabilities: Optional[Capabilities] = None
    granted_licenses: list[License] = field(default_factory=list)
    listing: Optional[Listing] = None
