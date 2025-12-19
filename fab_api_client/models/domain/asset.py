"""Asset domain model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

from .capabilities import Capabilities
from .license import License
from .listing import Listing


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
