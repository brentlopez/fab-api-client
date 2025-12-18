# Fab API Client

A generic Python HTTP client library with pluggable authentication and content parsing. Designed for building API integrations with marketplace-style services.

## Features

- 🔌 **Pluggable Auth** - Bring your own authentication provider
- 🌐 **Configurable Endpoints** - Runtime endpoint configuration
- 📦 **Custom Parsers** - Implement parsers for any content format
- ✅ **Type Safe** - Full type hints and dataclasses
- 🔍 **Validation** - Optional JSON schema validation
- 🎯 **Clean API** - Callback-based, no side effects, proper exception handling

## Installation

```bash
# Core library only
pip install -e .

# With manifest validation support
pip install -e .[validation]

# With CLI tools
pip install -e .[cli]

# Full development install
pip install -e .[dev]
```

## Quick Start

### Basic Usage

```python
from fab_api_client import FabClient, CookieAuthProvider, ApiEndpoints

# Configure API endpoints
endpoints = ApiEndpoints(
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
- `filter(predicate) -> Library` - Filter assets
- `find_by_uid(uid: str) -> Optional[Asset]` - Find by UID

#### `Asset`
Represents a Fab asset/entitlement.
- `uid: str` - Unique identifier
- `title: str` - Asset name
- `created_at: Optional[datetime]` - When added to library
- `listing: Optional[Listing]` - Marketplace info

#### `ParsedManifest`
Parsed manifest.
- `version: str`, `app_id: str`, `app_name: str`, `build_version: str`
- `files: List[ManifestFile]` - File list
- `raw_data: Dict` - Complete raw data

#### `DownloadResult`
Result of manifest download.
- `success: bool` - Whether successful
- `file_path: Optional[Path]` - Saved file path
- `size: Optional[int]` - File size in bytes
- `error: Optional[str]` - Error message if failed
- `load() -> ParsedManifest` - Load and parse manifest

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
# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Type checking
mypy fab_api_client
```

## Requirements

- Python 3.7+
- `requests` >= 2.31.0

### Optional Dependencies
- `jsonschema` >= 4.0.0 - For manifest validation
- `tqdm` >= 4.66.0 - For CLI progress bars

## License

MIT License - see LICENSE file for details.
