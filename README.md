# Fab API Client

A Python client library for Fab.com marketplace API, extending `asset-marketplace-client-core` for multi-platform compatibility.

> **Version 2.0.0** - Now extends asset-marketplace-client-core. See [Migration Guide](#migration-from-v1x) for upgrading from v1.x.

## Features

- 🔌 **Pluggable Auth** - Bring your own authentication provider
- 🌐 **Configurable Endpoints** - Runtime endpoint configuration
- 📦 **Custom Parsers** - Implement parsers for any content format
- ✅ **Type Safe** - Full type hints and dataclasses with mypy strict mode
- 🔍 **Validation** - Optional JSON schema validation
- 🎯 **Clean API** - Callback-based, no side effects, proper exception handling
- 🔒 **Security First** - Path traversal prevention, URL validation, secure defaults
- 🚀 **Modern Tooling** - uv + hatchling + pyproject.toml
- 🤝 **Multi-Platform** - Extends core library for compatibility across marketplaces

## Requirements

- Python 3.9 or higher
- Dependencies: `asset-marketplace-client-core>=0.1.0`, `requests>=2.28.0`

## Installation

```bash
# Using uv (recommended)
uv pip install fab-api-client

# Using pip
pip install fab-api-client

# For development
cd fab-api-client
uv sync --extra dev

# Optional extras
uv pip install fab-api-client[validation]  # JSON schema validation
uv pip install fab-api-client[cli]          # CLI tools (tqdm)
```

## Quick Start

### Basic Usage

```python
from fab_api_client import FabClient, CookieAuthProvider, FabEndpoints

# Configure API endpoints
endpoints = FabEndpoints(
    base_url="https://example.com",
    library_search="https://example.com/api/library/search",
    asset_formats="https://example.com/api/assets/{asset_uid}/formats",
    download_info="https://example.com/api/assets/{asset_uid}/files/{file_uid}/download"
)

# Create authentication provider
auth = CookieAuthProvider(
    cookies={"session_id": "xxx", "csrf_token": "yyy"},
    endpoints=endpoints
)

# Create client
client = FabClient(auth=auth)

# Fetch library
library = client.get_library()
print(f"Found {library.total_count} assets")

# Download manifests
for asset in library.assets[:5]:
    result = client.download_manifest(asset, output_dir="./manifests")
    if result.success:
        manifest = result.load()
        print(f"✅ {asset.title}: {len(manifest.files)} files")
```

### Custom Authentication Provider

Implement `FabAuthProvider` for your service:

```python
from fab_api_client import FabAuthProvider, ApiEndpoints
import requests

class MyAuthProvider(FabAuthProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {api_key}"
    
    def get_session(self) -> requests.Session:
        return self.session
    
    def get_endpoints(self) -> ApiEndpoints:
        return ApiEndpoints(
            library_search="https://myapi.com/library",
            asset_formats="https://myapi.com/assets/{asset_uid}/formats",
            download_info="https://myapi.com/assets/{asset_uid}/download/{file_uid}"
        )

# Use custom provider
auth = MyAuthProvider(api_key="your-key")
client = FabClient(auth=auth)
```

### Custom Manifest Parser

Implement `ManifestParser` for your format:

```python
from fab_api_client import ManifestParser, ParsedManifest
import json

class CustomParser(ManifestParser):
    def parse(self, data: bytes) -> ParsedManifest:
        # Parse your custom format
        manifest_data = json.loads(data)
        return ParsedManifest.from_dict(manifest_data)

# Use custom parser
parser = CustomParser()
client = FabClient(auth=auth, manifest_parser=parser)
```

### Advanced Usage

#### Pagination

```python
# Manual pagination for large libraries
for page in client.get_library_pages():
    assets = page.to_assets()
    print(f"Page: {len(assets)} assets")
    # Process page...
```

#### Progress Callbacks

```python
def on_progress(asset, status):
    print(f"[{asset.title}] {status}")

results = client.download_manifests(
    library.assets,
    output_dir="./manifests",
    on_progress=on_progress
)
```

#### Context Manager

```python
with FabClient(auth=auth) as client:
    library = client.get_library()
    # Session automatically closed
```

#### Library Filtering

```python
library = client.get_library()

# Filter by predicate
matching = library.filter(lambda a: "keyword" in a.title)

# Find specific asset
asset = library.find_by_uid("asset-uid-here")
```

## Architecture

### Model Organization

The library uses a clean two-layer type system with models organized into separate files:

**Domain Models** (`fab_api_client.models.domain`):
- Business entities: `Asset`, `Library`, `Listing`, `License`, `Seller`
- Format details: `AssetFormat`, `AssetFormatType`, `TechnicalSpecs`
- Manifest types: `ParsedManifest`, `ManifestFile`, `DownloadResult`
- Capabilities: `Capabilities`

**API Response Types** (`fab_api_client.models.api`):
- `LibrarySearchResponse` - Paginated library search results
- `AssetFormatsResponse` - Asset format information
- `DownloadInfoResponse` - Download URLs and metadata
- `CursorInfo` - Pagination cursor data

All models are exported from `fab_api_client.models` for convenient imports.

## API Reference

### Core Classes

#### `FabClient`

Main API client.

```python
FabClient(
    auth: FabAuthProvider,
    manifest_parser: Optional[ManifestParser] = None,
    verify_ssl: bool = True,
    timeout: int = 30,
)
```

**Methods:**
- `get_library(sort_by: str = '-createdAt') -> Library` - Fetch complete library
- `get_library_pages(sort_by: str = '-createdAt') -> Iterator[LibrarySearchResponse]` - Paginated access
- `download_manifest(asset: Asset, output_dir: Path, on_progress: Optional[Callable] = None) -> DownloadResult`
- `download_manifests(assets: List[Asset], output_dir: Path, on_progress: Optional[Callable] = None) -> List[DownloadResult]`

### Domain Models

#### `Library`
Collection of assets with helper methods.
- `assets: List[Asset]` - All assets
- `total_count: int` - Total count
- `filter(predicate) -> Library` - Filter assets by predicate function
- `find_by_uid(uid: str) -> Optional[Asset]` - Find asset by UID

#### `Asset`
Represents an asset/entitlement in your library.
- `uid: str` - Unique identifier
- `title: str` - Asset name
- `created_at: Optional[datetime]` - When added to library
- `status: str` - Entitlement status (e.g., "approved")
- `capabilities: Optional[Capabilities]` - Entitlement capabilities
- `granted_licenses: List[License]` - Licenses granted with this entitlement
- `listing: Optional[Listing]` - Marketplace listing information
- `raw_data: Dict[str, Any]` - Complete raw API data for extensibility

#### `Listing`
Marketplace listing details for an asset.
- `title: str` - Listing title
- `uid: str` - Unique identifier
- `listing_type: str` - Type of listing
- `description: Optional[str]` - Description
- `tags: List[str]` - Tags
- `is_mature: bool` - Mature content flag
- `last_updated_at: Optional[datetime]` - Last update timestamp
- `licenses: List[License]` - Available licenses
- `seller: Optional[Seller]` - Seller information
- `asset_formats: List[AssetFormat]` - Available formats
- `raw_data: Dict[str, Any]` - Complete raw data

#### `License`
License information for an asset.
- `name: str` - License name
- `slug: str` - License slug
- `url: Optional[str]` - License URL
- `type: Optional[str]` - License type
- `is_cc0: bool` - Whether it's CC0 licensed
- `price_tier: Optional[str]` - Price tier
- `uid: Optional[str]` - Unique identifier

#### `Seller`
Seller/creator information.
- `seller_id: str` - Seller ID
- `seller_name: str` - Seller name
- `uid: str` - Unique identifier
- `profile_image_url: Optional[str]` - Profile image URL
- `cover_image_url: Optional[str]` - Cover image URL
- `is_seller: bool` - Whether user is a seller

#### `AssetFormat`
Asset format details including technical specifications.
- `asset_format_type: AssetFormatType` - Format type information
- `technical_specs: Optional[TechnicalSpecs]` - Technical specifications
- `versions: List[Dict[str, Any]]` - Version information
- `raw_data: Dict[str, Any]` - Complete raw data

#### `AssetFormatType`
Asset format type information.
- `code: str` - Format code (e.g., "unreal-engine")
- `name: str` - Format name
- `icon: str` - Icon identifier
- `group_name: str` - Format group name
- `extensions: List[str]` - File extensions

#### `TechnicalSpecs`
Technical specifications for an asset format.
- `unreal_engine_engine_versions: List[str]` - Supported UE versions
- `unreal_engine_target_platforms: List[str]` - Target platforms
- `unreal_engine_distribution_method: str` - Distribution method
- `technical_details: Optional[str]` - Additional technical details

#### `Capabilities`
Entitlement capabilities.
- `add_by_verse: bool` - Can add by Verse
- `request_download_url: bool` - Can request download URL

#### `ParsedManifest`
Parsed manifest data.
- `version: str` - Manifest file version
- `app_id: str` - Application ID
- `app_name: str` - Application name
- `build_version: str` - Build version string
- `files: List[ManifestFile]` - File list
- `raw_data: Dict[str, Any]` - Complete raw manifest data
- `from_dict(data: Dict) -> ParsedManifest` - Create from dictionary

#### `ManifestFile`
Individual file entry in manifest.
- `filename: str` - File name
- `file_hash: str` - File hash
- `file_chunk_parts: List[Dict[str, Any]]` - Chunk parts information

#### `DownloadResult`
Result of manifest download operation.
- `success: bool` - Whether successful
- `file_path: Optional[Path]` - Saved file path
- `size: Optional[int]` - File size in bytes
- `error: Optional[str]` - Error message if failed
- `load() -> ParsedManifest` - Load and parse manifest file

### Abstractions

#### `FabAuthProvider`
Abstract base for authentication providers.
- `get_session() -> requests.Session` - Return configured session
- `get_endpoints() -> ApiEndpoints` - Return endpoint configuration

#### `CookieAuthProvider`
Generic cookie-based authentication.
- `__init__(cookies: Dict[str, str], endpoints: ApiEndpoints)`

#### `ApiEndpoints`
Endpoint URL configuration.
- `library_search: str` - Library search endpoint
- `asset_formats: str` - Asset formats endpoint (template with `{asset_uid}`)
- `download_info: str` - Download info endpoint (template with `{asset_uid}` and `{file_uid}`)

#### `ManifestParser`
Abstract base for manifest parsers.
- `parse(data: bytes) -> ParsedManifest` - Parse manifest bytes

#### `JsonManifestParser`
Default JSON manifest parser.

### Exceptions

- `FabError` - Base exception
- `FabAuthenticationError` - Authentication failed (401, 403)
- `FabAPIError` - HTTP errors from API
- `FabNotFoundError` - Resource not found (404)
- `FabNetworkError` - Network/timeout errors

### Utilities

```python
sanitize_filename(title: str) -> str
validate_manifest(manifest_path: Path, schema_path: Optional[Path] = None) -> bool
detect_manifest_format(manifest_path: Path) -> str  # "json" or "binary"
```

## Manifest Validation

Requires optional `jsonschema` package:

```bash
pip install jsonschema
```

```python
from fab_api_client import validate_manifest
from pathlib import Path

result = client.download_manifest(asset, "./manifests")
manifest = result.load()

if isinstance(manifest, ParsedManifest):
    is_valid = validate_manifest(result.file_path)
    if is_valid:
        print("✅ Manifest schema is valid")
```

## Development

```bash
# Clone and setup
git clone https://github.com/brentlopez/fab-api-client
cd fab-api-client
uv sync --extra dev

# Run tests
uv run pytest

# Type checking
uv run mypy src/

# Linting and formatting
uv run ruff format src/
uv run ruff check src/

# Security audit
uv run pip-audit
```

## Migration from v1.x

### Breaking Changes in v2.0.0

**Python Version:**
- Minimum version increased from 3.7 to 3.9

**Type Names:**
- `ApiEndpoints` → `FabEndpoints` (alias maintained for compatibility)
- `DownloadResult` → `ManifestDownloadResult` for manifest operations (alias maintained)

**Endpoint Configuration:**
```python
# v1.x
endpoints = ApiEndpoints(
    library_search="https://...",
    asset_formats="https://...",
    download_info="https://..."
)

# v2.x (requires base_url)
endpoints = FabEndpoints(
    base_url="https://...",  # NEW: Required field
    library_search="https://...",
    asset_formats="https://...",
    download_info="https://..."
)
```

**Manifest Downloads:**
```python
# v1.x
manifest = client.download_manifest(asset, "./manifests")
print(f"Version: {manifest.version}")

# v2.x
result = client.download_manifest(asset, "./manifests")
if result.success:
    manifest = result.load()  # Parse the manifest
    print(f"Version: {manifest.version}")
```

### New Features in v2.0.0

**New Methods:**
- `client.get_asset(asset_uid)` - Fetch single asset by UID
- `client.download_asset(asset_uid, output_dir, ...)` - Download using core interface
- `client.close()` - Explicit resource cleanup

**Security Improvements:**
- Path traversal prevention
- URL validation before downloads
- Secure filename sanitization
- Configurable rate limiting

**Multi-Platform Compatibility:**
Now extends `asset-marketplace-client-core` for compatibility with other marketplace clients.

For detailed migration instructions, see [CHANGELOG.md](CHANGELOG.md).

## License

MIT License - see LICENSE file for details.
