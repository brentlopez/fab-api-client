"""Download info API response types."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class DownloadInfoResponse:
    """
    Raw download info from download-info endpoint.
    """
    download_info: List[Dict[str, Any]]
    
    def find_manifest_url(self) -> Optional[str]:
        """
        Find manifest download URL.
        
        Returns:
            Download URL if found, None otherwise
        """
        for info in self.download_info:
            if isinstance(info, dict) and info.get('type') == 'manifest':
                return info.get('downloadUrl')
        return None
    
    def get_manifest_expires(self) -> Optional[str]:
        """Get manifest download URL expiration time."""
        for info in self.download_info:
            if isinstance(info, dict) and info.get('type') == 'manifest':
                return info.get('expires')
        return None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DownloadInfoResponse':
        """Create from API response dictionary."""
        return cls(
            download_info=data.get('downloadInfo', [])
        )
