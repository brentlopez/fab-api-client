# Security Audit

**Project:** fab-api-client  
**Version:** 2.0.0  
**Audit Date:** 2025-12-23  
**Auditor:** Automated Security Review

## Executive Summary

`fab-api-client` is a platform-specific implementation that extends `asset-marketplace-client-core` for marketplace API integration. This audit assesses the security posture of the platform client implementation.

**Overall Security Rating:** 🟢 GOOD

**Key Findings:**
- ✅ Extends secure core library (asset-marketplace-client-core)
- ✅ Uses secure defaults (SSL verification, timeouts)
- ✅ Implements path traversal prevention
- ✅ Has runtime dependencies - requires ongoing monitoring
- ✅ Type-safe implementation (mypy strict mode)
- ⚠️ Cookie-based authentication requires secure handling
- ⚠️ No built-in file integrity verification

## Audit Scope

This audit covers:

1. **Architecture & Dependencies** - Platform client design and dependency security
2. **Authentication Implementation** - Cookie-based auth security
3. **Network Security** - HTTP client configuration and request handling
4. **Data Handling** - Manifest parsing and file downloads
5. **Path Operations** - File system operations and path traversal prevention
6. **Error Handling** - Exception hierarchy and information leakage
7. **Input Validation** - User input sanitization
8. **Type Safety** - Static type checking coverage

## Detailed Findings

### 1. Architecture & Dependencies

**Status:** 🟢 GOOD

**Strengths:**
- ✅ Extends `asset-marketplace-client-core` with minimal attack surface core
- ✅ Clear separation: core (zero dependencies) vs platform (runtime dependencies)
- ✅ Uses modern build system (pyproject.toml + uv)
- ✅ Pinned dependencies in uv.lock for reproducible builds
- ✅ Minimal runtime dependencies (requests>=2.28.0, jsonschema for optional validation)

**Concerns:**
- ⚠️ `requests` library dependency - monitor for CVEs
- ℹ️ No automated dependency scanning in CI (pip-audit should be run regularly)

**Recommendations:**
1. Add `pip-audit` to CI/CD pipeline
2. Enable GitHub Dependabot for automated dependency updates
3. Document dependency upgrade policy

**Implementation Examples:**

`pyproject.toml`:
```toml
[project]
dependencies = [
    "asset-marketplace-client-core>=0.1.0",  # Core with zero deps
    "requests>=2.28.0",                       # HTTP client
]

[project.optional-dependencies]
validation = ["jsonschema>=4.0.0"]
```

### 2. Authentication Implementation

**Status:** 🟡 MODERATE - Requires Careful Use

**Strengths:**
- ✅ Abstract `FabAuthProvider` interface allows custom implementations
- ✅ Built-in `CookieAuthProvider` with secure defaults
- ✅ SSL verification enabled by default
- ✅ Request timeouts configured (5s connect, 30s read)
- ✅ User-Agent header set for identification

**Concerns:**
- ⚠️ Cookie-based auth is vulnerable if cookies are exposed
- ⚠️ No built-in token refresh mechanism
- ⚠️ Cookies stored in memory - can leak via debugging/logging
- ⚠️ No credential rotation enforcement

**Recommendations:**
1. **Never hardcode cookies** - Use environment variables or secret managers
2. **Implement secure cookie storage** - Consider keyring/keychain integration
3. **Add session refresh logic** - Implement in custom auth providers
4. **Document credential lifecycle** - Clear guidance on rotation and expiry

**Secure Usage Pattern:**
```python
import os
from fab_api_client import FabClient, CookieAuthProvider, FabEndpoints

# ✅ GOOD - Load from environment
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
    verify_ssl=True,  # Default - always keep enabled
    timeout=(5, 30)   # (connect, read) timeouts
)

with FabClient(auth=auth) as client:
    library = client.get_library()
```

**NEVER do this:**
```python
# ❌ BAD - Hardcoded credentials
auth = CookieAuthProvider(
    cookies={"session_id": "abc123..."},
    endpoints=endpoints
)

# ❌ BAD - Disabled SSL verification
auth = CookieAuthProvider(
    cookies=cookies,
    endpoints=endpoints,
    verify_ssl=False  # NEVER DISABLE IN PRODUCTION
)
```

### 3. Network Security

**Status:** 🟢 GOOD

**Strengths:**
- ✅ Uses `requests.Session` for connection pooling
- ✅ SSL verification enabled by default
- ✅ Configurable timeouts prevent hanging requests
- ✅ Rate limiting with configurable delays
- ✅ URL validation using `validate_url()` from core
- ✅ User-Agent header for identification

**Implementation:** `src/fab_api_client/client.py`
```python
def _make_request(self, url: str, method: str = "GET", **kwargs):
    """Make HTTP request with security defaults."""
    validate_url(url)  # Validate URL format
    
    if self.rate_limit_delay > 0:
        time.sleep(self.rate_limit_delay)
    
    response = self.session.request(method, url, **kwargs)
    response.raise_for_status()
    return response
```

**Concerns:**
- ⚠️ Rate limiting is application-level (not enforced by API)
- ℹ️ No built-in retry logic for transient failures

**Recommendations:**
1. Document rate limit recommendations for marketplace API
2. Consider adding exponential backoff for retries
3. Add request/response logging option (with credential redaction)

### 4. Data Handling

**Status:** 🟡 MODERATE - JSON Parsing Risk

**Strengths:**
- ✅ JSON parsing using standard library (no eval/exec)
- ✅ Optional manifest schema validation with jsonschema
- ✅ Type-safe data models using dataclasses
- ✅ Clear separation: API responses → domain models

**Concerns:**
- ⚠️ No file integrity verification (checksums/hashes)
- ⚠️ Manifest parsing trusts remote JSON data
- ⚠️ No size limits on downloaded manifests
- ℹ️ Schema validation is optional (not enabled by default)

**Implementation:** `src/fab_api_client/manifest_parser.py`
```python
class JsonManifestParser(ManifestParser):
    """Parse JSON manifests with optional schema validation."""
    
    def parse(self, data: bytes) -> ParsedManifest:
        """Parse manifest data into structured format."""
        try:
            manifest_dict = json.loads(data.decode("utf-8"))
            
            # Optional schema validation
            if self.validate_schema:
                validate_manifest(manifest_dict)
            
            return self._dict_to_manifest(manifest_dict)
        except json.JSONDecodeError as e:
            raise FabError(f"Invalid manifest JSON: {e}")
```

**Recommendations:**
1. **Enable schema validation by default** - Protect against malformed data
2. **Add size limits** - Prevent memory exhaustion attacks
3. **Verify file integrity** - Check checksums if provided in manifest
4. **Document manifest security** - Clear guidance on trusted sources

**Secure Usage:**
```python
from fab_api_client import FabClient, JsonManifestParser

# ✅ GOOD - Enable schema validation
parser = JsonManifestParser(validate_schema=True)
client = FabClient(auth=auth, manifest_parser=parser)

result = client.download_manifest(asset, "./output")
if result.success:
    manifest = result.load()
    
    # Verify file sizes are reasonable
    total_size = sum(f.file_size for f in manifest.files)
    if total_size > 10 * 1024 * 1024 * 1024:  # 10GB limit
        raise ValueError("Manifest total size exceeds limit")
```

### 5. Path Operations

**Status:** 🟢 GOOD

**Strengths:**
- ✅ Uses `safe_create_directory()` from core (prevents path traversal)
- ✅ Uses `sanitize_filename()` from core (removes dangerous characters)
- ✅ Uses `pathlib.Path` for path manipulation
- ✅ No shell command execution

**Implementation:** `src/fab_api_client/client.py`
```python
from asset_marketplace_client_core.security import safe_create_directory
from asset_marketplace_client_core.utils import sanitize_filename

def download_manifest(
    self,
    asset: Asset,
    output_dir: Union[str, Path]
) -> ManifestDownloadResult:
    """Download manifest with path traversal prevention."""
    output_path = Path(output_dir)
    safe_create_directory(output_path)  # Prevents traversal
    
    filename = sanitize_filename(f"{asset.title}.json")  # Sanitize
    file_path = output_path / filename
    
    # Download manifest to safe path
    ...
```

**Testing:**
```python
# Test cases from core library apply here:
# - Path traversal: "../../../etc/passwd"
# - Absolute paths: "/tmp/evil"
# - Special characters: "file<>:?\"|*.txt"
# - Unicode: "file\u202E.txt" (right-to-left override)
```

**Recommendations:**
1. Add integration tests for path operations
2. Document path security guarantees
3. Consider adding file size validation before writing

### 6. Error Handling

**Status:** 🟢 GOOD

**Strengths:**
- ✅ Uses multiple inheritance from core exceptions
- ✅ Clear exception hierarchy
- ✅ Type-safe exception handling
- ✅ No information leakage in error messages

**Exception Hierarchy:**
```python
# src/fab_api_client/exceptions.py
class FabError(MarketplaceError):
    """Base exception."""

class FabAuthenticationError(FabError, MarketplaceAuthenticationError):
    """Authentication/authorization errors."""

class FabAPIError(FabError, MarketplaceAPIError):
    """API response errors."""

class FabNotFoundError(FabError, MarketplaceNotFoundError):
    """Resource not found errors."""

class FabNetworkError(FabError, MarketplaceNetworkError):
    """Network connectivity errors."""
```

**Usage:**
```python
from fab_api_client import (
    FabClient,
    FabAuthenticationError,
    FabAPIError,
    FabNetworkError
)

try:
    client = FabClient(auth=auth)
    library = client.get_library()
except FabAuthenticationError:
    # Handle auth errors - don't log credentials
    logger.error("Authentication failed")
except FabNetworkError as e:
    # Handle network errors
    logger.error(f"Network error: {e}")
except FabAPIError as e:
    # Handle API errors
    logger.error(f"API error: {e}")
```

**Concerns:**
- ℹ️ No automatic credential redaction in error messages
- ℹ️ Stack traces might expose sensitive information if logged

**Recommendations:**
1. Add credential redaction utility for logging
2. Document error handling best practices
3. Consider adding error context without exposing sensitive data

### 7. Input Validation

**Status:** 🟢 GOOD

**Strengths:**
- ✅ Uses `validate_url()` from core for URL validation
- ✅ Uses `sanitize_filename()` from core for filename sanitization
- ✅ Type hints enforce expected input types
- ✅ No direct shell command execution

**Implementation:**
```python
from asset_marketplace_client_core.security import validate_url
from asset_marketplace_client_core.utils import sanitize_filename

# URL validation
def _fetch_library_page(self, cursor: Optional[str] = None):
    url = self.endpoints.library_search
    if cursor:
        url = cursor  # API might return full URL
    validate_url(url)  # Raises if invalid
    ...

# Filename sanitization
filename = sanitize_filename(f"{asset.title}.json")
```

**Concerns:**
- ⚠️ No validation of asset UID format (accepts any string)
- ⚠️ No validation of file UID format
- ℹ️ No input length limits

**Recommendations:**
1. Add asset UID format validation (e.g., UUID format)
2. Add file UID format validation
3. Add input length limits to prevent DoS
4. Document expected input formats

**Example Validation:**
```python
import re
from typing import Pattern

# Asset UID validation
ASSET_UID_PATTERN: Pattern = re.compile(r'^[a-f0-9-]{36}$')  # UUID format

def validate_asset_uid(uid: str) -> None:
    """Validate asset UID format."""
    if not ASSET_UID_PATTERN.match(uid):
        raise ValueError(f"Invalid asset UID format: {uid}")
```

### 8. Type Safety

**Status:** 🟢 EXCELLENT

**Strengths:**
- ✅ Full mypy strict mode compliance
- ✅ Type hints on all public APIs
- ✅ Generic types for collections
- ✅ Optional types where applicable
- ✅ Dataclasses for structured data

**Configuration:** `pyproject.toml`
```toml
[tool.mypy]
strict = true
warn_unused_configs = true
disallow_any_generics = true
disallow_subclassing_any = true
disallow_untyped_calls = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_return_any = true
no_implicit_reexport = true
strict_equality = true
```

**Verification:**
```bash
$ uv run mypy src/
Success: no issues found in 20 source files
```

**Recommendations:**
1. Maintain strict mode in CI/CD
2. Run mypy on all PRs
3. Consider adding runtime type checking for critical paths (e.g., pydantic)

## Dependency Security Analysis

### Current Dependencies

**Runtime:**
- `asset-marketplace-client-core>=0.1.0` - Zero dependencies, minimal attack surface ✅
- `requests>=2.28.0` - Well-maintained, requires monitoring ⚠️

**Optional:**
- `jsonschema>=4.0.0` - For manifest validation ℹ️

**Development:**
- `pytest>=7.0.0` - Testing framework ✅
- `mypy>=1.0.0` - Type checking ✅
- `ruff>=0.1.0` - Linting and formatting ✅

### Vulnerability Scan Results

**Last Scan:** 2025-12-23

```bash
$ uv run pip-audit
No known vulnerabilities found
```

**Notes:**
- ✅ All dependencies are up-to-date
- ✅ No known CVEs in dependency tree
- ⚠️ Should be run regularly (weekly recommended)

### Supply Chain Security

**Strengths:**
- ✅ Uses uv.lock for reproducible builds
- ✅ Minimal dependency tree
- ✅ Well-known, reputable dependencies

**Recommendations:**
1. Enable GitHub Dependabot
2. Add pip-audit to CI/CD
3. Consider adding SBOM generation
4. Review dependency changes in PRs

## Security Testing

### Current Test Coverage

**Unit Tests:** ✅ Present (tests/test_enhanced_models.py)

**Security Tests Needed:**
- [ ] Path traversal prevention tests
- [ ] Filename sanitization tests
- [ ] URL validation tests
- [ ] Authentication error handling tests
- [ ] Rate limiting tests
- [ ] Manifest size limit tests
- [ ] Invalid JSON handling tests

### Recommended Test Cases

```python
# tests/security/test_path_traversal.py
def test_path_traversal_prevention():
    """Test that path traversal is prevented."""
    asset = Asset(uid="test", title="../../../etc/passwd")
    result = client.download_manifest(asset, "/tmp/output")
    
    # Should sanitize to "etcpasswd.json"
    assert "etc" not in result.file_path.name

def test_filename_sanitization():
    """Test filename sanitization."""
    dangerous_names = [
        "file<>:\"|*.txt",
        "file\u202E.txt",  # Right-to-left override
        "CON", "PRN", "AUX",  # Windows reserved
    ]
    for name in dangerous_names:
        asset = Asset(uid="test", title=name)
        result = client.download_manifest(asset, "/tmp/output")
        assert result.file_path.name.isidentifier() or result.file_path.name.replace("_", "").replace(".", "").isalnum()

def test_url_validation():
    """Test URL validation."""
    invalid_urls = [
        "javascript:alert(1)",
        "file:///etc/passwd",
        "data:text/html,<script>alert(1)</script>",
    ]
    for url in invalid_urls:
        with pytest.raises(ValueError):
            validate_url(url)

def test_authentication_error_no_leak():
    """Test that auth errors don't leak credentials."""
    auth = CookieAuthProvider(
        cookies={"session": "secret123"},
        endpoints=endpoints
    )
    try:
        client = FabClient(auth=auth)
        # Simulate 401 response
        ...
    except FabAuthenticationError as e:
        # Error message should not contain cookie value
        assert "secret123" not in str(e)
```

## Security Checklist

### For Developers

- [x] Type hints on all functions
- [x] mypy strict mode enabled
- [x] ruff linting enabled
- [x] No hardcoded credentials
- [x] Uses secure defaults (SSL, timeouts)
- [x] Path traversal prevention
- [x] Filename sanitization
- [x] URL validation
- [ ] Comprehensive security tests
- [ ] SBOM generation
- [ ] Automated dependency scanning in CI

### For Users

- [ ] Credentials stored securely (environment variables or secret manager)
- [ ] SSL verification enabled (default)
- [ ] Rate limiting configured appropriately
- [ ] Manifest schema validation enabled
- [ ] Error logging doesn't expose credentials
- [ ] Regular dependency updates (pip-audit)
- [ ] Monitor security advisories

## Risk Assessment

### HIGH RISK
None identified.

### MEDIUM RISK

1. **Cookie-based Authentication**
   - **Impact:** HIGH - Compromised cookies allow unauthorized access
   - **Likelihood:** MEDIUM - Depends on user's credential management
   - **Mitigation:** Document secure storage, use HTTPS only, rotate regularly

2. **No File Integrity Checks**
   - **Impact:** MEDIUM - Malicious manifests could be undetected
   - **Likelihood:** LOW - Requires MITM or compromised API
   - **Mitigation:** Add checksum verification, enable schema validation

3. **Dependency Vulnerabilities**
   - **Impact:** VARIES - Depends on CVE severity
   - **Likelihood:** MEDIUM - requests library has had CVEs historically
   - **Mitigation:** Regular scanning (pip-audit), automated updates (Dependabot)

### LOW RISK

1. **Rate Limiting**
   - **Impact:** LOW - API abuse or DoS
   - **Likelihood:** LOW - Application-level rate limiting present
   - **Mitigation:** Configure appropriate delays, document API limits

2. **Input Validation**
   - **Impact:** LOW - Malformed inputs could cause errors
   - **Likelihood:** LOW - Type system provides protection
   - **Mitigation:** Add format validation for UIDs

## Compliance Considerations

### Data Privacy

- ✅ No telemetry or analytics
- ✅ No data collection
- ✅ Credentials stored locally only
- ℹ️ Users responsible for GDPR compliance in their usage

### Licensing

- ✅ MIT License (permissive)
- ✅ Compatible with core library (MIT)
- ✅ All dependencies have compatible licenses

## Recommendations Priority

### CRITICAL (Implement Immediately)

None identified - library follows security best practices.

### HIGH (Implement Soon)

1. **Add automated dependency scanning**
   - Add pip-audit to CI/CD pipeline
   - Enable GitHub Dependabot
   - Weekly vulnerability checks

2. **Document security best practices**
   - Create security guide for users ✅ (SECURITY.md created)
   - Add credential management examples ✅
   - Document secure configuration ✅

3. **Enable manifest validation by default**
   - Make schema validation non-optional
   - Add size limits for manifests
   - Validate file metadata

### MEDIUM (Consider for Future Releases)

1. **Add file integrity verification**
   - Support checksum validation
   - Verify file sizes from manifest
   - Detect tampering

2. **Implement comprehensive security tests**
   - Path traversal tests
   - Authentication error tests
   - Malformed input tests

3. **Add credential redaction**
   - Redact cookies in logs
   - Redact tokens in error messages
   - Safe debugging utilities

### LOW (Nice to Have)

1. **SBOM generation**
   - Generate Software Bill of Materials
   - Track dependency provenance

2. **Add retry logic with backoff**
   - Handle transient failures
   - Exponential backoff

3. **Keyring integration**
   - Secure credential storage
   - OS keychain support

## Audit Conclusion

**Overall Assessment:** 🟢 GOOD

`fab-api-client` v2.0.0 demonstrates good security practices:

✅ **Strengths:**
- Extends secure core library with minimal attack surface
- Secure defaults (SSL, timeouts, rate limiting)
- Type-safe implementation (mypy strict)
- Path traversal prevention and filename sanitization
- Clear exception hierarchy
- Minimal dependencies

⚠️ **Areas for Improvement:**
- Cookie-based auth requires careful handling (documented)
- No file integrity verification (plan to add)
- Missing comprehensive security tests (planned)
- Dependency monitoring should be automated (recommended)

The library is suitable for production use when following documented security best practices. Users must:
1. Store credentials securely
2. Keep dependencies updated
3. Enable schema validation
4. Use HTTPS only
5. Configure rate limiting appropriately

---

**Next Audit:** Recommended after major version changes or annually  
**Contact:** brent@brentlopez.dev for security concerns  
**Report Date:** 2025-12-23
