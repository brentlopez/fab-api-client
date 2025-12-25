"""Manifest domain models."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class ManifestFile:
    """Individual file entry in manifest."""

    filename: str
    file_hash: str
    file_chunk_parts: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ParsedManifest:
    """
    Parsed JSON manifest data.

    Attributes:
        version: Manifest file version
        app_id: Application ID
        app_name: Application name
        build_version: Build version string
        files: List of files in manifest
        raw_data: Complete raw manifest data
    """

    version: str
    app_id: str
    app_name: str
    build_version: str
    files: list[ManifestFile]
    raw_data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ParsedManifest":
        """Create ParsedManifest from dictionary."""
        files = []
        for file_data in data.get("FileManifestList", []):
            files.append(
                ManifestFile(
                    filename=file_data.get("Filename", ""),
                    file_hash=file_data.get("FileHash", ""),
                    file_chunk_parts=file_data.get("FileChunkParts", []),
                )
            )

        return cls(
            version=data.get("ManifestFileVersion", ""),
            app_id=data.get("AppID", ""),
            app_name=data.get("AppNameString", ""),
            build_version=data.get("BuildVersionString", ""),
            files=files,
            raw_data=data,
        )


@dataclass
class ManifestDownloadResult:
    """
    Result of manifest download operation (Fab-specific).

    Note: This is separate from core's DownloadResult which is used for
    generic asset downloads. This type is specific to manifest operations.

    Attributes:
        success: Whether download was successful
        file_path: Path to downloaded manifest file
        size: File size in bytes
        error: Error message if download failed
    """

    success: bool
    file_path: Optional[Path] = None
    size: Optional[int] = None
    error: Optional[str] = None

    def load(self) -> ParsedManifest:
        """
        Load and parse manifest file.

        Returns:
            ParsedManifest object

        Raises:
            ValueError: If download was not successful or file doesn't exist
        """
        if not self.success or not self.file_path:
            raise ValueError("Cannot load manifest: download was not successful")

        if not self.file_path.exists():
            raise ValueError(f"Manifest file not found: {self.file_path}")

        # Read file
        with open(self.file_path, "rb") as f:
            data = f.read()

        # Parse JSON
        manifest_dict = json.loads(data.decode("utf-8"))
        return ParsedManifest.from_dict(manifest_dict)


# Backward compatibility alias
DownloadResult = ManifestDownloadResult
