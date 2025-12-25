# Fab API Client - AI Assistant Guide

## Project Overview

The `fab-api-client` is a **platform-specific implementation** that extends `asset-marketplace-client-core` for marketplace API integration. It provides concrete HTTP client functionality with pluggable authentication and content parsing, but contains **no hardcoded service-specific details**.

### Version: 2.0.0

**Major Changes in v2.0.0:**
- ✅ Extends `asset-marketplace-client-core` base classes
- ✅ Modern build system (pyproject.toml + uv)
- ✅ Enhanced security (path traversal prevention, filename sanitization)
- ✅ Python 3.9+ minimum (was 3.7+)
- ✅ Type-safe (mypy strict mode)
- ⚠️ **Breaking changes** - See CHANGELOG.md for migration guide

### Key Features

- **Extends Core Library** - Built on `asset-marketplace-client-core` with zero-dependency base classes
- **Clean Public API** - No side effects, callback-based, proper exception handling
- **Two-layer type system** - Domain models (Library, Asset) + API response types (LibrarySearchResponse)
- **Pluggable authentication** - Bring your own auth provider via `FabAuthProvider` ABC
- **Configurable endpoints** - Runtime endpoint configuration via `FabEndpoints`
- **Custom parsers** - Implement `ManifestParser` for any content format
- **Manifest validation** - Optional JSON schema validation
- **Context manager support** - Automatic session cleanup
- **Security by default** - SSL verification, timeouts, rate limiting, path security

### Tech Stack

- **Python 3.9+** - Minimum version (modern type hints, dataclasses)
- **asset-marketplace-client-core** - Base classes and utilities
- **requests>=2.28.0** - HTTP client
- **jsonschema>=4.0.0** (optional) - Manifest validation
- **uv** - Build and dependency management

## Project Structure

```
fab-api-client/
├── README.md                           # User documentation
├── CHANGELOG.md                        # Version history and migration guides
├── SECURITY.md                         # Security policy and best practices
├── SECURITY_AUDIT.md                   # Comprehensive security assessment
├── WARP.md                             # This file - AI assistant guidance
├── pyproject.toml                      # Modern build config (PEP 621)
├── uv.lock                             # Locked dependencies for reproducible builds
├── .gitignore                          # Git ignore patterns (includes security patterns)
├── src/fab_api_client/                 # Source code (src/ layout)
│   ├── __init__.py                     # Public API exports
│   ├── client.py                       # FabClient - extends MarketplaceClient
│   ├── auth.py                         # FabAuthProvider, CookieAuthProvider, FabEndpoints
│   ├── manifest_parser.py              # ManifestParser, JsonManifestParser
│   ├── exceptions.py                   # Exception hierarchy (extends core)
│   ├── utils.py                        # Imports from core for backward compatibility
│   ├── manifests.py                    # validate_manifest(), detect_manifest_format()
│   ├── models/
│   │   ├── __init__.py                 # Exports all models
│   │   ├── domain/                     # Business/domain models
│   │   │   ├── __init__.py
│   │   │   ├── asset.py                # Asset - extends BaseAsset
│   │   │   ├── asset_format.py         # AssetFormat, AssetFormatType, TechnicalSpecs
│   │   │   ├── capabilities.py         # Capabilities
│   │   │   ├── library.py              # Library - extends BaseCollection
│   │   │   ├── license.py              # License
│   │   │   ├── listing.py              # Listing
│   │   │   ├── manifest.py             # ParsedManifest, ManifestFile, ManifestDownloadResult
│   │   │   └── seller.py               # Seller
│   │   └── api/                        # API response types
│   │       ├── __init__.py
│   │       ├── asset_formats.py        # AssetFormatsResponse
│   │       ├── cursor.py               # CursorInfo
│   │       ├── download_info.py        # DownloadInfoResponse
│   │       └── library_search.py       # LibrarySearchResponse
│   └── schemas/
│       └── manifest.json               # JSON Schema for manifest format
└── tests/
    └── test_enhanced_models.py         # Tests for extended models

## Architecture

### Core Library Integration

As of v2.0.0, `fab-api-client` extends `asset-marketplace-client-core`:

**Architecture Benefits:**
- ✅ **Separation of concerns** - Core has zero dependencies, platform client has runtime deps
- ✅ **Security by default** - Inherits security utilities from core
- ✅ **Type safety** - Full mypy strict mode compliance
- ✅ **Forward compatibility** - Can catch both platform and core exception types

**Class Hierarchy:**
```
Core Library (asset-marketplace-client-core):
├── MarketplaceClient (ABC) → FabClient extends this
├── MarketplaceError → FabError extends this
├── BaseAsset → Asset extends this
└── BaseCollection → Library extends this
```

**Key Interfaces Implemented:**
- `FabClient.get_collection()` - Returns Library (delegates to `get_library()`)
- `FabClient.get_asset(uid)` - Fetches library and filters by UID
- `FabClient.download_asset(asset, path)` - Returns core's `DownloadResult`
- `FabClient.close()` - Closes HTTP session

### Pluggable Authentication Pattern

The library uses an abstract base class pattern for authentication:

**`FabAuthProvider` (ABC)**:
- `get_session() -> requests.Session` - Return configured HTTP session
- `get_endpoints() -> ApiEndpoints` - Return endpoint configuration

**`CookieAuthProvider` (built-in implementation)**:
- Generic cookie-based authentication
- Accepts cookies dict and `ApiEndpoints` configuration
- No service-specific details

**`FabEndpoints` (extends `EndpointConfig` from core)**:
- `base_url: str` - Base URL for the marketplace API (required by core)
- `library_search: str` - Library search endpoint URL
- `asset_formats: str` - Asset formats endpoint (template with `{asset_uid}`)
- `download_info: str` - Download info endpoint (template with `{asset_uid}`, `{file_uid}`)

**Backward Compatibility:**
- `ApiEndpoints` - Alias for `FabEndpoints` (deprecated, use `FabEndpoints`)

**Why this pattern?**
- Library is service-agnostic
- Users can implement custom auth (OAuth, JWT, API keys, etc.)
- Endpoint URLs are not hardcoded
- Easy to test with mock providers
- Extends core's `EndpointConfig` for forward compatibility

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
- `ManifestDownloadResult` (`manifest.py`) - Manifest download result with `load()` method
  - Note: `DownloadResult` is backward compatibility alias (deprecated)

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

**Exception hierarchy (multiple inheritance from core):**
```
FabError(MarketplaceError) - base exception
├── FabAuthenticationError(FabError, MarketplaceAuthenticationError) - 401, 403
├── FabAPIError(FabError, MarketplaceAPIError) - other HTTP errors
├── FabNotFoundError(FabError, MarketplaceNotFoundError) - 404
└── FabNetworkError(FabError, MarketplaceNetworkError) - timeouts, connection
```

**Multiple Inheritance Benefits:**
- ✅ Backward compatible - Can catch `FabError` or `FabAuthenticationError`
- ✅ Forward compatible - Can catch core's `MarketplaceAuthenticationError`
- ✅ Type safe - Works with both exception hierarchies

**Philosophy:**
- Library never calls `sys.exit()` or prints to stdout
- All errors propagate as exceptions
- Callers decide how to handle errors
- Authentication errors are distinct from other API errors

### Security Features

**Built-in security (v2.0.0):**
- ✅ **Path traversal prevention** - Uses `safe_create_directory()` from core
- ✅ **Filename sanitization** - Uses `sanitize_filename()` from core
- ✅ **URL validation** - Uses `validate_url()` from core
- ✅ **SSL verification** - Enabled by default in `CookieAuthProvider`
- ✅ **Request timeouts** - 5s connect, 30s read (configurable)
- ✅ **Rate limiting** - Configurable delay between requests
- ✅ **Type safety** - Full mypy strict mode compliance

**Security Documentation:**
- See `SECURITY.md` for vulnerability reporting and best practices
- See `SECURITY_AUDIT.md` for comprehensive security assessment

## Usage Patterns

### Basic Library Usage

```python
import os
from fab_api_client import FabClient, CookieAuthProvider, FabEndpoints

# Configure endpoints (v2.0.0 - note FabEndpoints and base_url required)
endpoints = FabEndpoints(
    base_url="https://marketplace.example.com",  # Required in v2.0.0
    library_search="/api/library/search",
    asset_formats="/api/assets/{asset_uid}/formats",
    download_info="/api/assets/{asset_uid}/files/{file_uid}/download"
)

# Create auth provider (NEVER hardcode credentials - use environment variables)
auth = CookieAuthProvider(
    cookies={
        "session_id": os.environ["MARKETPLACE_SESSION"],
        "csrf_token": os.environ["MARKETPLACE_CSRF"]
    },
    endpoints=endpoints,
    verify_ssl=True,  # Default - always keep enabled
    timeout=(5, 30)   # (connect, read) timeouts
)

# Use client
with FabClient(auth=auth) as client:
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
# download_manifest() returns ManifestDownloadResult (not ParsedManifest directly)
result = client.download_manifest(asset, "./manifests")

# Check success and load parsed manifest
if result.success:
    manifest = result.load()  # Returns ParsedManifest
    
    print(f"Manifest version: {manifest.version}")
    print(f"Files: {len(manifest.files)}")
    for file in manifest.files[:5]:
        print(f"  {file.filename} ({file.file_size} bytes)")
else:
    print(f"Failed: {result.error}")
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
- **Security first** - Always use core's security utilities (safe_create_directory, sanitize_filename, validate_url)
- **Mypy strict mode** - All code must pass `uv run mypy src/` with strict=true

### Testing Approach

When making changes:
1. **Type checking**: Run `uv run mypy src/` (must pass with strict mode)
2. **Linting**: Run `uv run ruff check src/` and `uv run ruff format src/`
3. **Dependency audit**: Run `uv run pip-audit` (no vulnerabilities)
4. **Unit tests**: Run `uv run pytest` with coverage
5. **API response parsing**: Test with `isinstance()` checks for lists
6. **Union type handling**: Verify works with both manifest types
7. **Exception hierarchy**: Verify multiple inheritance works correctly
8. **Context manager**: Test session cleanup
9. **Security**: Test path traversal prevention, filename sanitization, URL validation

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
1. Create response type file in `src/fab_api_client/models/api/` (e.g., `new_endpoint.py`)
2. Add conversion method to appropriate domain model
3. Export from `models/api/__init__.py`
4. Add method to `FabClient` class
5. Export from main `__init__.py` if needed
6. Add type hints and ensure mypy strict mode passes
7. Document in README.md and CHANGELOG.md

**Adding new domain model:**
1. Create model file in `src/fab_api_client/models/domain/` (e.g., `new_model.py`)
2. Consider if it should extend a core base class (BaseAsset, BaseCollection)
3. Add corresponding API response type if needed
4. Add conversion logic in API response type
5. Export from `models/domain/__init__.py`
6. Export from main `__init__.py` if public API
7. Add type hints and ensure mypy strict mode passes
8. Update CHANGELOG.md

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

## Build System & Dependencies

**Build System:**
- `pyproject.toml` - Modern PEP 621 build configuration
- `uv` - Fast dependency manager and build tool
- `uv.lock` - Locked dependencies for reproducible builds
- `hatchling` - Build backend

**Runtime Dependencies:**
- `asset-marketplace-client-core>=0.1.0` - Core library (zero dependencies)
- `requests>=2.28.0` - HTTP client

**Optional:**
- `jsonschema>=4.0.0` - Manifest validation (install with `[validation]`)

**Development:**
- `pytest>=7.0.0` - Testing framework
- `mypy>=1.0.0` - Static type checking (strict mode)
- `ruff>=0.1.0` - Linting and formatting (replaces black, isort, flake8)
- `pip-audit` - Dependency vulnerability scanning

**Installation:**
```bash
# Install for development
uv sync --extra dev

# Install with validation support
uv sync --extra validation

# Run tests
uv run pytest

# Type check
uv run mypy src/

# Lint and format
uv run ruff check src/
uv run ruff format src/

# Security audit
uv run pip-audit
```

## License & Terms

MIT License - see LICENSE file for details.

## Security

Security is a top priority in v2.0.0:

### Security Documentation

- **SECURITY.md** - Vulnerability reporting, best practices, secure usage patterns
- **SECURITY_AUDIT.md** - Comprehensive security assessment, risk analysis, recommendations

### Security Features

- ✅ **Path traversal prevention** - Uses `safe_create_directory()` from core
- ✅ **Filename sanitization** - Uses `sanitize_filename()` from core
- ✅ **URL validation** - Uses `validate_url()` from core
- ✅ **SSL verification** - Enabled by default
- ✅ **Request timeouts** - Prevents hanging requests
- ✅ **Rate limiting** - Application-level rate limiting
- ✅ **Type safety** - Full mypy strict mode compliance
- ✅ **No unsafe operations** - No eval, exec, or shell commands

### Security Best Practices

1. **Never hardcode credentials** - Use environment variables or secret managers
2. **Always verify SSL** - Never disable in production
3. **Enable schema validation** - Use `JsonManifestParser(validate_schema=True)`
4. **Monitor dependencies** - Run `uv run pip-audit` regularly
5. **Keep updated** - Watch for security advisories
6. **Handle errors safely** - Don't expose credentials in logs

**Example Secure Usage:**
```python
import os
from fab_api_client import FabClient, CookieAuthProvider, FabEndpoints

# ✅ GOOD - Load credentials from environment
endpoints = FabEndpoints(
    base_url="https://marketplace.example.com",
    library_search="/api/library/search",
    asset_formats="/api/assets/{asset_uid}/formats",
    download_info="/api/assets/{asset_uid}/files/{file_uid}/download"
)

auth = CookieAuthProvider(
    cookies={
        "session_id": os.environ["MARKETPLACE_SESSION"],
        "csrf_token": os.environ["MARKETPLACE_CSRF"]
    },
    endpoints=endpoints,
    verify_ssl=True,  # Always keep enabled
    timeout=(5, 30)
)

with FabClient(auth=auth, rate_limit_delay=1.0) as client:
    library = client.get_library()
```

**See SECURITY.md for complete security guidelines.**

## Related Projects

- **asset-marketplace-client-core** - Core library with base classes and utilities
- **asset-marketplace-client-system** - System integration library
- Can be paired with service-specific adapter projects that implement the authentication and parsing abstractions (e.g., fab-egl-adapter for Epic Games Launcher)
- Can be used with manifest parsing tools for asset management
- Can be integrated into CI/CD pipelines for automated asset tracking

## Migration Guides

### Migrating from v1.x to v2.0.0

See `CHANGELOG.md` for detailed migration guide covering:
- Updated dependencies (Python 3.9+, requests>=2.28.0)
- API changes (`ApiEndpoints` → `FabEndpoints`, requires `base_url`)
- Return type changes (`download_manifest()` returns `ManifestDownloadResult`)
- New security features
- Project structure changes (root → src/ layout)

### Adapter Migration

If you maintain an adapter that uses fab-api-client:
- See `../asset-marketplace-client-system/docs/migration/fab_egl_adapter_migration.md`
- Update to FabEndpoints with base_url
- Handle ManifestDownloadResult return type
- Test with new exception hierarchy
