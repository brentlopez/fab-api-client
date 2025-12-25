"""Utility functions for Fab API client.

Backward compatibility module - utilities now provided by core library.
"""

# Import from core for backward compatibility
from asset_marketplace_core import sanitize_filename

__all__ = ["sanitize_filename"]
