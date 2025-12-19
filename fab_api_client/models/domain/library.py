"""Library domain model."""

from dataclasses import dataclass
from typing import List, Optional

from .asset import Asset


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
