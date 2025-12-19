"""Cursor API model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CursorInfo:
    """Pagination cursor data."""
    next: Optional[str] = None
    previous: Optional[str] = None
