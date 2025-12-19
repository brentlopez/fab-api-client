"""License domain model."""

from dataclasses import dataclass
from typing import Optional


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
