# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-12-23

### Breaking Changes

#### Python Version
- **Minimum Python version increased from 3.7 to 3.9**
  - Required to align with `asset-marketplace-client-core` and use modern Python features

#### Project Structure
- **Migrated to src/ layout**
  - Source code moved from `fab_api_client/` to `src/fab_api_client/`
  - Improves package isolation and prevents accidental imports

#### Build System
- **Migrated from setup.py to modern Python tooling**
  - Now uses `pyproject.toml` with hatchling backend (PEP 517/518)
  - Uses `uv` for dependency management with lockfile (`uv.lock`)
  - Removed `setup.py` and `requirements.txt`

#### Core Library Integration
- **Now depends on `asset-marketplace-client-core>=0.1.0`**
  - Extends base classes for multi-platform compatibility
  - Enables unified interface across different marketplace clients

#### Type Name Changes
- **`ApiEndpoints` → `FabEndpoints`**
  - New name extends `EndpointConfig` from core
  - `ApiEndpoints` kept as backward compatibility alias
  - Now requires `base_url` field from parent class

- **`DownloadResult` → `ManifestDownloadResult`**
  - Renamed to avoid conflict with core's `DownloadResult`
  - `DownloadResult` kept as backward compatibility alias
  - Manifest-specific operations remain unchanged

#### Class Inheritance Changes
- **`FabAuthProvider` now extends `AuthProvider` from core**
  - Return types updated to use `FabEndpoints`
  - Core methods `refresh()` and `close()` now available

- **`Asset` now extends `BaseAsset` from core**
  - Inherits: `uid`, `title`, `description`, `created_at`, `updated_at`, `raw_data`
  - Fab-specific fields: `status`, `capabilities`, `granted_licenses`, `listing`

- **`Library` now extends `BaseCollection` from core**
  - Inherits: `assets`, `total_count`, `filter()`, `find_by_uid()`, `__len__()`
  - Added Fab-specific method: `filter_by_status()`

- **`FabClient` now extends `MarketplaceClient` from core**
  - Context manager support inherited from core
  - Must implement: `get_collection()`, `get_asset()`, `download_asset()`, `close()`

#### Exception Hierarchy
- **All exceptions now extend core marketplace exceptions**
  - `FabError` extends `MarketplaceError`
  - `FabAuthenticationError` extends both `FabError` and `MarketplaceAuthenticationError`
  - `FabAPIError` extends both `FabError` and `MarketplaceAPIError`
  - `FabNotFoundError` extends both `FabError` and `MarketplaceNotFoundError`
  - `FabNetworkError` extends both `FabError` and `MarketplaceNetworkError`
  - Backward compatible: existing `except FabError` blocks still work
  - Forward compatible: can catch `MarketplaceError` for multi-platform code

### Added

#### New Methods on `FabClient`
- **`get_collection(**kwargs) -> Library`**
  - Implements core `MarketplaceClient` interface
  - Alias for `get_library()` for consistency across platforms

- **`get_asset(asset_uid: str) -> Asset`**
  - NEW: Retrieve single asset by UID
  - Implements core `MarketplaceClient` interface
  - Fetches library and filters (Fab API has no single-asset endpoint)

- **`download_asset(asset_uid, output_dir, progress_callback, **kwargs) -> DownloadResult`**
  - NEW: Download asset using core's `DownloadResult` type
  - Implements core `MarketplaceClient` interface
  - Returns core's `DownloadResult` (not `ManifestDownloadResult`)

- **`close() -> None`**
  - NEW: Explicit resource cleanup method
  - Implements core `MarketplaceClient` interface
  - Automatically called when using context manager

#### Security Improvements
- **Path traversal prevention**
  - Uses `safe_create_directory()` from core to prevent directory traversal attacks
  - Validates output directories before writing files

- **URL validation**
  - Uses `validate_url()` from core to validate manifest URLs before download
  - Prevents requests to invalid or malicious URLs

- **Filename sanitization**
  - Uses `sanitize_filename()` from core (replaces local implementation)
  - Removes invalid filesystem characters from filenames

- **Enhanced authentication security**
  - `CookieAuthProvider` now includes default user agent
  - SSL verification enabled by default
  - Request timeouts configured (connect: 5s, read: 30s)

- **Rate limiting**
  - Configurable rate limit delays between API requests
  - Default 1.5 second delay to respect API limits

### Changed

#### Method Signatures
- **`download_manifest()` return type changed**
  - Before: `-> ParsedManifest`
  - After: `-> ManifestDownloadResult`
  - Returns result object instead of parsed manifest
  - Use `result.load()` to get `ParsedManifest`

- **`download_manifests()` return type changed**
  - Before: `-> List[ParsedManifest]`
  - After: `-> List[ManifestDownloadResult]`
  - Returns result objects for better error handling

#### Development Tools
- **Replaced black, isort, flake8, pylint with ruff**
  - 10-100x faster linting and formatting
  - Single tool for all code quality checks

- **Added pip-audit for security scanning**
  - Automated vulnerability detection in dependencies

- **Type checking with mypy in strict mode**
  - Full type hint coverage required
  - Catches type errors at development time

### Deprecated

#### Backward Compatibility Aliases
These aliases are maintained for backward compatibility but may be removed in v3.0.0:

- **`ApiEndpoints`** - Use `FabEndpoints` instead
- **`DownloadResult`** (for manifests) - Use `ManifestDownloadResult` instead

### Migration Guide

#### Updating Imports

```python
# Old (v1.x)
from fab_api_client import FabClient, ApiEndpoints

# New (v2.x) - Recommended
from fab_api_client import FabClient, FabEndpoints

# New (v2.x) - Still works (backward compatible)
from fab_api_client import FabClient, ApiEndpoints
```

#### Updating Endpoint Configuration

```python
# Old (v1.x)
endpoints = ApiEndpoints(
    library_search="https://...",
    asset_formats="https://...",
    download_info="https://..."
)

# New (v2.x)
endpoints = FabEndpoints(
    base_url="https://...",  # NEW: Required field from core
    library_search="https://...",
    asset_formats="https://...",
    download_info="https://..."
)
```

#### Updating Manifest Downloads

```python
# Old (v1.x)
manifest = client.download_manifest(asset, "./output")
print(f"Version: {manifest.version}")

# New (v2.x)
result = client.download_manifest(asset, "./output")
if result.success:
    manifest = result.load()  # Parse the manifest
    print(f"Version: {manifest.version}")
else:
    print(f"Failed: {result.error}")
```

#### Using New Core Methods

```python
# New in v2.x: Get single asset
asset = client.get_asset("asset-uid-123")

# New in v2.x: Download using core interface
from asset_marketplace_core import DownloadResult

result: DownloadResult = client.download_asset(
    "asset-uid-123",
    "./downloads"
)
if result.success:
    print(f"Downloaded: {result.files}")
```

#### Exception Handling

```python
# Old (v1.x) - Still works in v2.x
try:
    library = client.get_library()
except FabError as e:
    print(f"Fab error: {e}")

# New (v2.x) - Multi-platform compatible
from asset_marketplace_core import MarketplaceError

try:
    library = client.get_library()
except MarketplaceError as e:  # Catches errors from any marketplace client
    print(f"Marketplace error: {e}")
```

### Installation

```bash
# Using uv (recommended)
uv pip install fab-api-client

# Using pip (still supported)
pip install fab-api-client

# For development
uv sync --extra dev
```

### Full Changelog
[Unreleased]: https://github.com/brentlopez/fab-api-client/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/brentlopez/fab-api-client/releases/tag/v2.0.0
