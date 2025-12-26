"""Library domain model."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Callable

from asset_marketplace_core import BaseCollection

from .asset import Asset


@dataclass
class Library(BaseCollection):
    """
    Fab library collection extending BaseCollection.

    Extends BaseCollection from core library with type-specific overrides.

    Attributes:
        assets: Complete list of Fab assets (inherited, overridden for type)
        total_count: Total number of assets (inherited)

    Methods inherited from BaseCollection:
        filter(predicate) -> Library: Filter assets by predicate
        find_by_uid(uid) -> Optional[Asset]: Find asset by UID
        __len__() -> int: Get number of assets
    """

    # Override to specify Fab's Asset type
    # Use Sequence for compatibility with BaseCollection's list[BaseAsset]
    assets: Sequence[Asset] = field(default_factory=list)  # type: ignore[assignment]

    def filter(self, predicate: Callable[[Asset], bool]) -> "Library":
        """Filter assets by predicate function.

        Args:
            predicate: Function that takes an asset and returns True to include it

        Returns:
            New Library with filtered assets
        """
        filtered = [asset for asset in self.assets if predicate(asset)]
        return Library(assets=filtered, total_count=len(filtered))

    def filter_by_status(self, status: str) -> "Library":
        """Filter assets by entitlement status (Fab-specific method).

        Args:
            status: Status to filter by (e.g., "approved")

        Returns:
            New Library with assets matching the status
        """
        filtered = [a for a in self.assets if a.status == status]
        return Library(assets=filtered, total_count=len(filtered))
