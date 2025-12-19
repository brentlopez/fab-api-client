"""Asset formats API response types."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class AssetFormatsResponse:
    """
    Raw file format data from /i/library/entitlements/{uid}/asset-formats.
    
    API returns a list of format objects directly.
    """
    formats: List[Dict[str, Any]]
    
    def find_unreal_file_uid(self) -> Optional[str]:
        """
        Find file UID for Unreal Engine format.
        
        Returns:
            File UID if found, None otherwise
        """
        for format_obj in self.formats:
            if not isinstance(format_obj, dict):
                continue
            
            # Check assetFormatType
            format_type = format_obj.get('assetFormatType', {})
            if isinstance(format_type, dict) and format_type.get('code') == 'unreal-engine':
                files = format_obj.get('files', [])
                if files and isinstance(files, list):
                    for f in files:
                        if isinstance(f, dict) and 'uid' in f:
                            return f['uid']
        
        return None
    
    @classmethod
    def from_api_response(cls, data: Any) -> 'AssetFormatsResponse':
        """
        Create from API response.
        
        API returns either a list directly or a dict with 'assetFormats' key.
        """
        if isinstance(data, list):
            return cls(formats=data)
        elif isinstance(data, dict):
            # Try 'assetFormats' key
            if 'assetFormats' in data:
                return cls(formats=data['assetFormats'])
            # Otherwise treat dict as single format
            return cls(formats=[data])
        else:
            return cls(formats=[])
