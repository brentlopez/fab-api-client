"""Asset format domain models."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AssetFormatType:
    """Asset format type information."""
    code: str
    name: str
    icon: str
    group_name: str
    extensions: List[str] = field(default_factory=list)


@dataclass
class TechnicalSpecs:
    """Technical specifications for an asset format."""
    unreal_engine_engine_versions: List[str] = field(default_factory=list)
    unreal_engine_target_platforms: List[str] = field(default_factory=list)
    unreal_engine_distribution_method: str = ""
    technical_details: Optional[str] = None


@dataclass
class AssetFormat:
    """Asset format details including technical specifications."""
    asset_format_type: AssetFormatType
    technical_specs: Optional[TechnicalSpecs] = None
    versions: List[Dict[str, Any]] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)
