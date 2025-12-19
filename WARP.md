# Fab API Client - AI Assistant Guide

## Project Overview

The `fab-api-client` is a **generic** Python HTTP client library with pluggable authentication and content parsing. It's designed for building API integrations with marketplace-style services but contains **no hardcoded service-specific details**.

### Key Features

- **Clean Public API** - No side effects, callback-based, proper exception handling
- **Two-layer type system** - Domain models (Library, Asset) + API response types (LibrarySearchResponse)
- **Pluggable authentication** - Bring your own auth provider via `FabAuthProvider` ABC
- **Configurable endpoints** - Runtime endpoint configuration via `ApiEndpoints`
- **Custom parsers** - Implement `ManifestParser` for any content format
- **Manifest validation** - Optional JSON schema validation
- **Context manager support** - Automatic session cleanup

### Tech Stack

- **Python 3.7+** - Minimum version (uses dataclasses, type hints, pathlib)
- **requests** - HTTP client
- **jsonschema** (optional) - Manifest validation
- **tqdm** (optional) - CLI progress bars

## Project Structure

```
fab-api-client/
├── README.md                           # User documentation
├── WARP.md                             # This file - AI assistant guidance
├── setup.py                            # Package setup with optional dependencies
├── requirements.txt                    # Core dependencies
├── fab_api_client/
│   ├── __init__.py                     # Public API exports
│   ├── client.py                       # FabClient - main API client
│   ├── auth.py                         # Authentication abstractions (FabAuthProvider, CookieAuthProvider, ApiEndpoints)
│   ├── manifest_parser.py              # Parser abstractions (ManifestParser, JsonManifestParser)
│   ├── exceptions.py                   # Exception hierarchy
│   ├── utils.py                        # sanitize_filename()
│   ├── manifests.py                    # validate_manifest(), detect_manifest_format()
│   ├── models/
│   │   ├── __init__.py                 # Exports all models
│   │   ├── domain/                     # Business/domain models
│   │   │   ├── __init__.py
│   │   │   ├── asset.py                # Asset model
│   │   │   ├── asset_format.py         # AssetFormat, AssetFormatType, TechnicalSpecs
│   │   │   ├── capabilities.py         # Capabilities
│   │   │   ├── library.py              # Library collection
│   │   │   ├── license.py              # License
│   │   │   ├── listing.py              # Listing
│   │   │   ├── manifest.py             # ParsedManifest, ManifestFile, DownloadResult
│   │   │   └── seller.py               # Seller
│   │   └── api/                        # API response types
│   │       ├── __init__.py
│   │       ├── asset_formats.py        # AssetFormatsResponse
│   │       ├── cursor.py               # CursorInfo
│   │       ├── download_info.py        # DownloadInfoResponse
│   │       └── library_search.py       # LibrarySearchResponse
│   └── schemas/
│       └── manifest.json               # JSON Schema for manifest format
```

## Architecture

### Pluggable Authentication Pattern

The library uses an abstract base class pattern for authentication:

**`FabAuthProvider` (ABC)**:
- `get_session() -> requests.Session` - Return configured HTTP session
- `get_endpoints() -> ApiEndpoints` - Return endpoint configuration

**`CookieAuthProvider` (built-in implementation)**:
- Generic cookie-based authentication
- Accepts cookies dict and `ApiEndpoints` configuration
- No service-specific details

**`ApiEndpoints` (dataclass)**:
- `library_search: str` - Library search endpoint URL
- `asset_formats: str` - Asset formats endpoint (template with `{asset_uid}`)
- `download_info: str` - Download info endpoint (template with `{asset_uid}`, `{file_uid}`)

**Why this pattern?**
- Library is service-agnostic
- Users can implement custom auth (OAuth, JWT, API keys, etc.)
- Endpoint URLs are not hardcoded
- Easy to test with mock providers

### Pluggable Manifest Parsing

**`ManifestParser` (ABC)**:
- `parse(data: bytes) -> ParsedManifest` - Parse manifest bytes to domain model

**`JsonManifestParser` (built-in)**:
- Default parser for JSON manifests
- Converts JSON to `ParsedManifest` dataclass

**Why this pattern?**
- Support multiple manifest formats without hardcoding knowledge
- Users can implement custom parsers for proprietary formats
- Library doesn't need to know about binary compression, encryption, etc.

### Two-Layer Type System

The library maintains a clear separation between API responses and business logic:

**Layer 1: API Response Types** (`models/api/`)
- `LibrarySearchResponse` (`library_search.py`) - Raw paginated API response
- `AssetFormatsResponse` (`asset_formats.py`) - Raw response from asset formats endpoint
- `DownloadInfoResponse` (`download_info.py`) - Raw response from download info endpoint
- `CursorInfo` (`cursor.py`) - Pagination cursor data
- Each has conversion methods: `to_assets()`, `find_unreal_file_uid()`, etc.

**Layer 2: Domain Models** (`models/domain/`)
- `Library` (`library.py`) - Collection with filtering, searching (`filter()`, `find_by_uid()`)
- `Asset` (`asset.py`) - Business entity representing an asset
- `Listing` (`listing.py`) - Marketplace metadata
- `License` (`license.py`) - License information
- `Seller` (`seller.py`) - Seller/creator information
- `AssetFormat` (`asset_format.py`) - Asset format details with technical specs
- `Capabilities` (`capabilities.py`) - Entitlement capabilities
- `ParsedManifest` (`manifest.py`) - Parsed manifest with files list
- `ManifestFile` (`manifest.py`) - File entry in parsed manifest
- `DownloadResult` (`manifest.py`) - Download operation result with `load()` method

**Why this separation?**
- API types can evolve independently from business logic
- Domain models provide user-friendly interface
- Conversion happens at API boundary, not scattered throughout code

### API Response Handling

The library expects API responses in a specific structure:

**Library Search Endpoint**:
```json
{
  "results": [...],  // Array of asset objects
  "cursors": {"next": "cursor_string", "previous": null},
  "next": "https://api.example.com/...",
  "aggregations": null
}
```

**Asset Formats Endpoint**:
- Can return a list or an object
- Code handles both: `isinstance(response, list)`
- Each item should have format type and files array

**Download Info Endpoint**:
```json
{
  "downloadInfo": [
    {"type": "manifest", "downloadUrl": "...", "expires": "..."}
  ]
}
```

### Error Handling

**Exception hierarchy:**
```
FabError (base)
├── FabAuthenticationError (401, 403)
├── FabAPIError (other HTTP errors)
├── FabNotFoundError (404)
└── FabNetworkError (timeouts, connection errors)
```

**Philosophy:**
- Library never calls `sys.exit()` or prints to stdout
- All errors propagate as exceptions
- Callers decide how to handle errors
- Authentication errors are distinct from other API errors

## Usage Patterns

### Basic Library Usage

```python
from fab_api_client import FabClient, CookieAuthProvider, ApiEndpoints

# Configure endpoints
endpoints = ApiEndpoints(
    library_search="https://example.com/api/library/search",
    asset_formats="https://example.com/api/assets/{asset_uid}/formats",
    download_info="https://example.com/api/assets/{asset_uid}/files/{file_uid}/download"
)

# Create auth provider
auth = CookieAuthProvider(
    cookies={"session_id": "xxx", "csrf_token": "yyy"},
    endpoints=endpoints
)

# Use client
client = FabClient(auth=auth)
library = client.get_library()

# Filter and process
matching = library.filter(lambda a: "keyword" in a.title)
for asset in matching:
    print(f"{asset.title} ({asset.uid})")
```

### Batch Downloads with Progress

```python
def progress_callback(asset, status):
    print(f"[{asset.title}] {status}")

results = client.download_manifests(
    library.assets,
    output_dir="./manifests",
    on_progress=progress_callback
)

# Check results
successful = [r for r in results if r.success]
failed = [r for r in results if not r.success]
```

### Manifest Handling

```python
result = client.download_manifest(asset, "./manifests")
manifest = result.load()

print(f"Manifest version: {manifest.version}")
print(f"Files: {len(manifest.files)}")
for file in manifest.files[:5]:
    print(f"  {file.filename} ({file.file_size} bytes)")
```

### Context Manager Usage

```python
with FabClient(auth=auth) as client:
    library = client.get_library()
    # Process library...
# Session automatically closed
```

## Development Guidelines

### Code Style

- **Type hints** - Use Optional, Union, List, Dict for all function signatures
- **Dataclasses** - Use @dataclass for models with default_factory for mutable defaults
- **No side effects** - Library code never prints, exits, or writes files without explicit API call
- **Callbacks** - Use `on_progress` callbacks for status updates
- **Error messages** - Clear, actionable error messages in exceptions

### Testing Approach

When making changes:
1. Test API response parsing with `isinstance()` checks for lists
2. Verify union type handling works with both manifest types
3. Test cookie extraction (mock subprocess for Proxyman)
4. Verify exception hierarchy propagates correctly
5. Test context manager cleanup

### Common Gotchas

1. **Asset Formats API returns list, not dict**
   - Always check: `isinstance(formats_response, list)`
   - Handle empty lists gracefully

2. **Authentication cookies may expire**
   - Library should fail fast with FabAuthenticationError
   - Authentication provider handles refresh/retry logic

3. **Pagination cursors are opaque**
   - Don't parse or manipulate cursor strings
   - Treat as opaque tokens from API

### Adding New Features

**Adding a new API endpoint:**
1. Create response type file in `models/api/` (e.g., `new_endpoint.py`)
2. Add conversion method to appropriate domain model
3. Export from `models/api/__init__.py`
4. Add method to `FabClient` class
5. Export from main `__init__.py` if needed
6. Document in README.md

**Adding new domain model:**
1. Create model file in `models/domain/` (e.g., `new_model.py`)
2. Add corresponding API response type if needed
3. Add conversion logic in API response type
4. Export from `models/domain/__init__.py`
5. Export from main `__init__.py` if public API

## Git Workflow

**Always gitignore:**
- `*.pyc`, `__pycache__/` - Python bytecode
- `*.egg-info/` - Package metadata
- `.venv/`, `venv/` - Virtual environments
- `.pytest_cache/` - Test cache

**Commit guidelines:**
- Include co-author: `Co-Authored-By: Warp <agent@warp.dev>`
- Use descriptive messages
- No sensitive data (cookies, tokens, personal info)

## Integration Example

This library is designed to be integrated into other Python projects:

```python
# Example: Download all manifests for assets matching pattern
from fab_api_client import FabClient, CookieAuthProvider, ApiEndpoints
import os

endpoints = ApiEndpoints(
    library_search="https://example.com/api/library/search",
    asset_formats="https://example.com/api/assets/{asset_uid}/formats",
    download_info="https://example.com/api/assets/{asset_uid}/files/{file_uid}/download"
)

auth = CookieAuthProvider(
    cookies={"session_id": os.environ["SESSION_ID"]},
    endpoints=endpoints
)

client = FabClient(auth=auth)
library = client.get_library()
matching = library.filter(lambda a: "keyword" in a.title)

for asset in matching:
    result = client.download_manifest(asset, "./output")
    if result.success:
        manifest = result.load()
        print(f"Downloaded {asset.title}: {len(manifest.files)} files")
```

## Future Improvements

Potential enhancements to consider:

1. **Async API** - Add async version of FabClient using aiohttp
2. **Caching layer** - Cache library responses to reduce API calls
3. **Retry logic** - Automatic retry with exponential backoff
4. **Rate limit detection** - Detect 429 responses and back off
5. **Parallel downloads** - Download manifests concurrently with asyncio
6. **CLI tool** - Command-line interface using the library

## Dependencies

**Core:**
- `requests>=2.31.0` - HTTP client

**Optional:**
- `jsonschema>=4.0.0` - Manifest validation (install with `[validation]`)
- `tqdm>=4.66.0` - Progress bars (install with `[cli]`)

**Development:**
- `pytest` - Testing framework
- `mypy` - Static type checking
- `black` - Code formatting

## License & Terms

MIT License - see LICENSE file for details.

## Related Projects

- Can be paired with service-specific adapter projects that implement the authentication and parsing abstractions (e.g., fab-egl-adapter for Epic Games Launcher)
- Can be used with manifest parsing tools for asset management
- Can be integrated into CI/CD pipelines for automated asset tracking
