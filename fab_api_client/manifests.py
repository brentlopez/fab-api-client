"""Manifest validation and utility functions."""

import json
from pathlib import Path
from typing import Optional

# Optional jsonschema dependency
try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


def validate_manifest(manifest_path: Path, schema_path: Optional[Path] = None) -> bool:
    """
    Validate a JSON manifest file against the Epic manifest schema.
    
    Note: Requires the 'jsonschema' package to be installed. If not available,
    this function will raise an ImportError.
    
    Args:
        manifest_path: Path to manifest file to validate
        schema_path: Optional path to JSON schema file. If not provided,
                    uses the bundled schema.
    
    Returns:
        True if manifest is valid, False otherwise
    
    Raises:
        ImportError: If jsonschema package is not installed
        FileNotFoundError: If manifest or schema file not found
        ValueError: If manifest is not JSON format
    
    Example:
        >>> from pathlib import Path
        >>> from fab_api_client import validate_manifest
        >>> is_valid = validate_manifest(Path("./my_asset.manifest"))
        >>> if is_valid:
        ...     print("Manifest is valid!")
    """
    if not JSONSCHEMA_AVAILABLE:
        raise ImportError(
            "jsonschema package is required for manifest validation. "
            "Install it with: pip install jsonschema"
        )
    
    # Check if manifest exists
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    # Read manifest
    with open(manifest_path, 'rb') as f:
        data = f.read()
    
    # Check if it's JSON
    if not data.startswith(b'{'):
        raise ValueError(
            f"Manifest file is not JSON format (appears to be binary): {manifest_path}"
        )
    
    try:
        manifest_data = json.loads(data.decode('utf-8'))
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse manifest JSON: {e}")
    
    # Load schema
    if schema_path is None:
        # Use bundled schema
        schema_path = Path(__file__).parent / 'schemas' / 'manifest.json'
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    # Validate
    try:
        jsonschema.validate(instance=manifest_data, schema=schema)
        return True
    except jsonschema.ValidationError:
        return False
    except jsonschema.SchemaError as e:
        raise ValueError(f"Invalid schema: {e}")


def detect_manifest_format(manifest_path: Path) -> str:
    """
    Detect whether a manifest file is JSON or binary format.
    
    Args:
        manifest_path: Path to manifest file
    
    Returns:
        "json" if JSON format, "binary" if binary/compressed
    
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, 'rb') as f:
        # Read first byte
        first_byte = f.read(1)
    
    if first_byte == b'{':
        return "json"
    else:
        return "binary"
