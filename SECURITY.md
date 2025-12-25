# Security Policy

## Supported Versions

We actively support and provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.x     | :x: (deprecated)   |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in `fab-api-client`, please report it responsibly.

### How to Report

**Please DO NOT open a public GitHub issue for security vulnerabilities.**

Instead, please use one of these methods:

1. **GitHub Security Advisories** (Preferred)
   - Go to: https://github.com/brentlopez/fab-api-client/security/advisories
   - Click "Report a vulnerability"
   - Provide detailed information about the vulnerability

2. **Email** (Alternative)
   - Email: brent@brentlopez.dev
   - Include "SECURITY: fab-api-client" in the subject line
   - Provide detailed information about the vulnerability

### What to Include

When reporting a vulnerability, please include:

- **Description** of the vulnerability
- **Steps to reproduce** the issue
- **Affected versions**
- **Potential impact** assessment
- **Suggested fix** (if you have one)
- **Your contact information** (for follow-up)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt within 48 hours
- **Assessment**: We will assess the vulnerability within 7 days
- **Updates**: We will keep you informed of progress
- **Resolution**: We aim to release a fix within 30 days for critical issues
- **Credit**: We will credit you in the security advisory (unless you prefer to remain anonymous)

## Security Best Practices for Users

### Credential Management

1. **Never Hardcode Credentials**
   ```python
   # ❌ BAD - Credentials in code
   cookies = {"session_id": "abc123...", "csrf": "xyz789..."}
   
   # ✅ GOOD - Load from environment
   import os
   cookies = {
       "session_id": os.environ["FAB_SESSION_COOKIE"],
       "csrf": os.environ["FAB_CSRF_TOKEN"]
   }
   ```

2. **Use Environment Variables**
   - Store credentials in `.env` files (never commit to git)
   - Use libraries like `python-dotenv` for local development
   - Use secure secret management in production (AWS Secrets Manager, HashiCorp Vault, etc.)

3. **Rotate Credentials Regularly**
   - Marketplace session cookies expire - handle refresh appropriately
   - Don't reuse the same credentials across environments

### Network Security

1. **Always Verify SSL**
   ```python
   # ✅ GOOD - SSL verification enabled (default)
   auth = CookieAuthProvider(
       cookies=cookies,
       endpoints=endpoints,
       verify_ssl=True  # This is the default
   )
   
   # ❌ NEVER DO THIS IN PRODUCTION
   auth = CookieAuthProvider(..., verify_ssl=False)
   ```

2. **Use HTTPS Endpoints**
   - All API endpoints should use `https://`, never `http://`
   - The library validates URLs but you should verify endpoint configuration

3. **Implement Rate Limiting**
   ```python
   client = FabClient(
       auth=auth,
       rate_limit_delay=1.5  # Delay between requests
   )
   ```

### Path Security

1. **Validate Download Directories**
   ```python
   from pathlib import Path
   
   # ✅ GOOD - Validate output directory
   output_dir = Path("./downloads").resolve()
   if not output_dir.exists():
       output_dir.mkdir(parents=True, exist_ok=True)
   
   result = client.download_manifest(asset, output_dir)
   ```

2. **Prevent Path Traversal**
   - The library uses `safe_create_directory()` from core to prevent traversal
   - Filenames are sanitized using `sanitize_filename()` from core
   - Always use absolute paths when possible

### Input Validation

1. **Validate Asset UIDs**
   ```python
   import re
   
   def is_valid_asset_uid(uid: str) -> bool:
       """Validate asset UID format."""
       # Example: UUIDs or specific format
       return bool(re.match(r'^[a-f0-9-]{36}$', uid))
   
   if not is_valid_asset_uid(asset_uid):
       raise ValueError("Invalid asset UID")
   ```

2. **Sanitize User Inputs**
   - Use the library's `sanitize_filename()` utility
   - Validate URLs with `validate_url()` (from core)
   - Don't trust user input for file paths

### Error Handling

1. **Don't Expose Sensitive Information**
   ```python
   # ❌ BAD - Might expose credentials in logs
   try:
       client = FabClient(auth=auth)
       library = client.get_library()
   except Exception as e:
       logger.error(f"Error: {e}, auth: {auth}")  # Don't log auth!
   
   # ✅ GOOD - Log safely
   try:
       client = FabClient(auth=auth)
       library = client.get_library()
   except FabAuthenticationError:
       logger.error("Authentication failed - check credentials")
   except FabAPIError as e:
       logger.error(f"API error: {e}")  # Safe - no credentials
   ```

2. **Handle Exceptions Gracefully**
   - Use specific exception types (`FabAuthenticationError`, `FabAPIError`)
   - Don't expose stack traces to end users
   - Log security events appropriately

### Dependency Management

1. **Keep Dependencies Updated**
   ```bash
   # Check for vulnerabilities
   uv run pip-audit
   
   # Update dependencies
   uv lock --upgrade
   uv sync
   ```

2. **Monitor Security Advisories**
   - Watch this repository for security updates
   - Subscribe to GitHub security advisories
   - Monitor `asset-marketplace-client-core` security updates

3. **Review Lockfile**
   - Always commit `uv.lock` to version control
   - Review changes in `uv.lock` during updates
   - Use `uv lock` to ensure reproducible builds

## Security Features

This library implements security best practices:

### Built-In Security

- ✅ **Path Traversal Prevention** - Uses `safe_create_directory()` from core
- ✅ **Filename Sanitization** - Uses `sanitize_filename()` from core
- ✅ **URL Validation** - Uses `validate_url()` from core
- ✅ **Type Safety** - Full mypy strict mode compliance
- ✅ **Secure Defaults** - SSL verification enabled by default
- ✅ **Rate Limiting** - Configurable delays between requests
- ✅ **No Unsafe Operations** - No eval, exec, or shell commands

### Inherited from Core

Since v2.0.0, this library extends `asset-marketplace-client-core`, inheriting:
- Zero-dependency core (minimal attack surface)
- Secure utility functions
- Well-tested security patterns
- Clear security boundaries

## Known Security Considerations

### Authentication

- **Cookie-based authentication** - Cookies can be stolen if exposed
  - Solution: Store securely, use HTTPS only, rotate regularly
  
- **No built-in token refresh** - Sessions expire
  - Solution: Implement refresh logic in your auth provider

### Network

- **Rate limiting** - Application-level only (not enforced by API)
  - Solution: Configure `rate_limit_delay` appropriately
  
- **No request signing** - Relies on cookie authentication
  - Solution: Follow marketplace's authentication requirements

### Downloads

- **Manifest parsing** - Parses JSON from remote sources
  - Solution: Optional schema validation with `jsonschema`
  
- **No file integrity checks** - Downloads files as-is
  - Solution: Verify file hashes from manifest if needed

## Secure Development

If you're contributing to this project:

1. **Run Security Checks**
   ```bash
   # Type safety
   uv run mypy src/
   
   # Linting (includes security rules)
   uv run ruff check src/
   
   # Dependency audit
   uv run pip-audit
   ```

2. **Follow Secure Coding Practices**
   - Never commit credentials or API keys
   - Use type hints for all functions
   - Validate all inputs
   - Handle errors properly
   - Document security considerations

3. **Test Security Features**
   - Test path traversal prevention
   - Test filename sanitization
   - Test error handling
   - Test with invalid inputs

## Responsible Disclosure

We appreciate security researchers who report vulnerabilities responsibly:

1. Report privately via GitHub Security Advisories or email
2. Allow reasonable time for a fix (30 days for critical issues)
3. Don't disclose publicly until a fix is released
4. We will credit you in the security advisory

## Acknowledgments

We appreciate the security research community and will acknowledge security researchers who responsibly disclose vulnerabilities.

## Questions?

For general security questions (not vulnerabilities):
- Open a GitHub Discussion
- Review our [Security Audit](SECURITY_AUDIT.md)
- Check the [Platform Client Guide](https://github.com/brentlopez/asset-marketplace-client-core/blob/main/docs/platform_client_guide.md)

---

**Last Updated:** 2025-12-23  
**Version:** 2.0.0
