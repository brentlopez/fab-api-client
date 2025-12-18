"""Utility functions for Fab API client."""

import re


def sanitize_filename(title: str) -> str:
    """
    Sanitize asset title for use in filename.
    
    Args:
        title: Asset title to sanitize
    
    Returns:
        Sanitized filename-safe string
    
    Example:
        >>> sanitize_filename("My Asset: Cool Edition")
        'My_Asset_Cool_Edition'
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', title)
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Trim to reasonable length (200 chars)
    sanitized = sanitized[:200]
    return sanitized.strip('_')
