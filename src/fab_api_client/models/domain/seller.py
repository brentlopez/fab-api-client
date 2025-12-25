"""Seller domain model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Seller:
    """Seller/creator information."""

    seller_id: str
    seller_name: str
    uid: str
    profile_image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    is_seller: bool = True
