"""Capabilities domain model."""

from dataclasses import dataclass


@dataclass
class Capabilities:
    """Entitlement capabilities."""

    add_by_verse: bool = False
    request_download_url: bool = False
