# Changelog

All notable changes to haiec-isaf-logger will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2026-10-08

### Fixed

- **Security**: Raised `numpy` floor to `>=1.22.0` — 1.19–1.21 are covered by GHSA-6p56-wp2h-9hxr, GHSA-fpfv-jqm9-f5jm, and PYSEC-2021-856
- **Metadata**: Repository URLs now point to `github.com/subodhkc/isaf-logger` (previously dead `github.com/haiec/*` links)
- **Docs**: Added builder and company backlinks (subodhkc.com, HAIEC — Human AI Evidence Company)

### Chore

- Published via GitHub Actions OIDC trusted publishing (no PyPI token)

## [0.3.0] - 2026-02-02

### Enhanced

**Enterprise Multi-Tenant Support**
- **Context-Based Session Management**: Thread-safe session isolation using Python contextvars for concurrent AI workloads
- **Multi-Tenant Architecture**: Isolated sessions per tenant with automatic context switching for SaaS AI platforms
- **Zero Cross-Contamination**: Complete session isolation prevents data leakage between tenants or concurrent requests

**Cryptographic Data Integrity**
- **Full Dataset Hashing**: Enhanced from partial (1KB) to complete dataset hashing with memory-efficient 1MB chunking
- **Salted Hash Generation**: Session-specific salt prevents rainbow table attacks and ensures hash uniqueness
- **64-Character SHA-256**: Upgraded from 16-character to full 64-character hashes for cryptographic strength

**Production Reliability**
- **Comprehensive Error Logging**: All errors logged to `isaf_errors.log` with context for troubleshooting
- **Emergency Fallback Storage**: Automatic fallback to `.isaf_fallback/` directory when primary storage fails
- **Alert Threshold System**: Automatic alerts when 3+ errors occur within 5 minutes

**Developer Experience**
- **Backward Compatible API**: Existing code works without modifications
- **Optional Multi-Tenant Mode**: Single-tenant usage unchanged, multi-tenant opt-in via `tenant_id` parameter
- **Enhanced Documentation**: Clear migration guides and usage examples

### Added

- `tenant_id` parameter for multi-tenant session management
- `set_session()` - Manually set current session
- `clear_session()` - Clear session(s) for cleanup
- Context-based session storage using Python contextvars
- Thread-safe session registry with locking
- Full dataset hashing with 1MB chunking
- Session ID salt for hash uniqueness
- Error logging system (`isaf_errors.log`)
- Fallback storage system (`.isaf_fallback/`)
- Alert threshold monitoring (3 errors in 5 minutes)

### Changed

- Data hash length: 16 characters → 64 characters (full SHA-256)
- Hashing scope: First 1KB → Complete dataset
- Session management: Global state → Context-based isolation
- Error handling: Silent failures → Logged with fallback storage
- Hash chains: Now mandatory (removed optional parameter)

### Migration Notes

**For New Installations:**
- No action required - works out-of-box

**For Existing Users (Single-Tenant):**
```python
# Before (still works)
import isaf
isaf.init(backend='sqlite')

# After (same API, enhanced internally)
import isaf
isaf.init(backend='sqlite')
```

**For Multi-Tenant Deployments:**
```python
# New multi-tenant support
import isaf

# Initialize per tenant
isaf.init(backend='sqlite', tenant_id='customer-123')

# Get tenant-specific session
session = isaf.get_session(tenant_id='customer-123')
```

**Hash Length Change:**
- Old exports with 16-character hashes remain valid
- New exports have 64-character hashes
- No migration required for existing data

**Error Logs:**
- Check `isaf_errors.log` for any issues
- Add to `.gitignore` if needed
- Monitor for repeated errors

**Fallback Storage:**
- Check `.isaf_fallback/` directory if primary storage fails
- Use provided import script to recover data
- Add to `.gitignore` if needed

---

## [0.1.0] - 2025-11-01

### Initial Release

- Automatic compliance logging for AI systems
- Layer 6 (Framework), Layer 7 (Data), Layer 8 (Objective) coverage
- Cryptographic hash chains for lineage verification
- EU AI Act, NIST AI RMF, ISO 42001 compliance mappings
- SQLite and MLflow storage backends
- CLI tools for inspection and verification
- Framework-agnostic design (PyTorch, TensorFlow, scikit-learn)
