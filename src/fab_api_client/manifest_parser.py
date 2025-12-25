"""Manifest parsing abstraction for Fab API client."""

import json
from abc import ABC, abstractmethod

from .models.domain import ParsedManifest


class ManifestParser(ABC):
    """Abstract base class for manifest parsers.

    Implementations can handle different manifest formats (JSON, binary, etc.)
    and return a standardized ParsedManifest object.
    """

    @abstractmethod
    def parse(self, raw_data: bytes) -> ParsedManifest:
        """Parse raw manifest bytes into ParsedManifest object.

        Args:
            raw_data: Raw manifest bytes from download

        Returns:
            ParsedManifest object

        Raises:
            Exception: If parsing fails
        """
        pass


class JsonManifestParser(ManifestParser):
    """Standard JSON manifest parser.

    Parses JSON-formatted manifests into ParsedManifest objects.
    This is the default parser for standard JSON responses.
    """

    def parse(self, raw_data: bytes) -> ParsedManifest:
        """Parse JSON manifest data.

        Args:
            raw_data: Raw JSON manifest bytes

        Returns:
            ParsedManifest object

        Raises:
            json.JSONDecodeError: If JSON parsing fails
            UnicodeDecodeError: If bytes cannot be decoded as UTF-8
        """
        data = json.loads(raw_data.decode("utf-8"))
        return ParsedManifest.from_dict(data)
