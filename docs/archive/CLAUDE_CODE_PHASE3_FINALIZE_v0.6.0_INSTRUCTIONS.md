# Claude Code Instructions: Finalize Phase 3 & Tag v0.6.0

**Document Version:** 1.0
**Created:** January 28, 2026
**Estimated Time:** 30-45 minutes
**Priority:** High (milestone release)

---

## Objective

Finalize Phase 3 (Document Management), create release documentation, and tag v0.6.0.

---

## Pre-Flight Checklist

Before starting, verify the current state:

```bash
cd ~/Projects/IP2A-Database-v2
git status                    # Should be clean
git branch --show-current     # Should be main
pytest -v                     # Should show 144 passing
docker-compose ps             # Verify services running (including minio)
```

---

## Step-by-Step Instructions

### Step 1: Verify All Phase 3 Components Exist

Run these checks to confirm Phase 3 is complete:

```bash
# Check core files exist
ls -la src/config/s3_config.py
ls -la src/services/s3_service.py
ls -la src/services/document_service.py
ls -la src/schemas/document.py
ls -la src/routers/documents.py
ls -la src/tests/test_documents.py

# Check MinIO in docker-compose
grep -A 10 "minio:" docker-compose.yml

# Check S3 env vars in example
grep "S3_" .env.compose.example

# Verify router is registered
grep "documents" src/main.py
```

### Step 2: Run Full Test Suite

```bash
# Run all tests with verbose output
pytest -v

# Expected: 144 tests passing
# If any failures, fix before proceeding
```

### Step 3: Test Document Endpoints Manually (Optional but Recommended)

```bash
# Start services if not running
docker-compose up -d

# Check MinIO is accessible
curl -s http://localhost:9000/minio/health/live

# Test upload endpoint (requires auth token)
# This is optional - tests cover functionality
```

### Step 4: Update CHANGELOG.md

Add a new version section. Edit `CHANGELOG.md`:

```markdown
## [0.6.0] - 2026-01-28

### Added
- **Phase 3: Document Management System**
  * S3-compatible object storage integration (MinIO dev, AWS S3/Backblaze B2 production)
  * Complete document lifecycle: upload, download, delete with soft/hard delete options
  * Presigned URLs for secure, time-limited file access
  * Direct-to-S3 uploads for large files (presigned upload URLs)
  * File validation: extension whitelist, 50MB max size
  * Organized storage paths: `uploads/{type}s/{name}_{id}/{category}/{year}/{month}/`
  * 8 REST API endpoints for document operations
  * Environment-based S3 configuration (works with any S3-compatible service)
  * MinIO service added to docker-compose for development
  * 11 new tests with mock S3 service
  * ADR-004 implemented

### Changed
- Legacy Phase 0 tests archived to `archive/phase0_legacy/`
- Test count optimized: 144 tests (down from 183, legacy tests archived)
- Downgraded bcrypt to 4.1.3 for passlib compatibility

### Fixed
- Test isolation issues resolved
- pytest.ini updated to exclude archive folder
```

### Step 5: Create Release Notes

Create `docs/releases/RELEASE_NOTES_v0.6.0.md`:

```bash
mkdir -p docs/releases
```

Then create the file with this content:

```markdown
# Release Notes - v0.6.0

**Release Date:** January 28, 2026
**Tag:** v0.6.0
**Branch:** main

---

## 🎉 Phase 3 Complete: Document Management System

v0.6.0 delivers a production-ready document management system with S3-compatible storage.

---

## ✨ What's New

### Document Management API

8 new REST API endpoints for complete document lifecycle:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/documents/upload` | Direct file upload |
| POST | `/documents/presigned-upload` | Get presigned URL for large files |
| POST | `/documents/confirm-upload` | Confirm presigned upload completion |
| GET | `/documents/{id}` | Get document metadata |
| GET | `/documents/{id}/download-url` | Get presigned download URL |
| GET | `/documents/{id}/download` | Stream document content |
| DELETE | `/documents/{id}` | Soft or hard delete |
| GET | `/documents/` | List with filters |

### Key Features

- **S3-Compatible Storage:** Works with MinIO (dev), AWS S3, Backblaze B2, Cloudflare R2
- **Presigned URLs:** Secure, time-limited access without exposing credentials
- **Direct Uploads:** Large files upload directly to S3, bypassing the API server
- **File Validation:** Extension whitelist (pdf, doc, docx, jpg, png, etc.), 50MB max
- **Organized Storage:** `uploads/{type}s/{name}_{id}/{category}/{year}/{month}/`
- **Soft Delete:** Mark as deleted while preserving for audit trail
- **Hard Delete:** Permanent removal from S3 when required

### Infrastructure

- **Development:** MinIO service in docker-compose.yml
- **Production:** Configure S3_* environment variables for your provider

---

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| Total Tests | 144 passing |
| API Endpoints | ~85 total |
| Database Tables | 20+ |
| Lines of Code | ~20,000+ |

### Test Breakdown
- Core Models: 17 tests
- Auth System: 52 tests
- Union Operations: 31 tests
- Training System: 33 tests
- Document Management: 11 tests

---

## 🔧 Configuration

### Environment Variables

```bash
# S3/MinIO Configuration
S3_ENDPOINT=http://minio:9000      # or https://s3.amazonaws.com
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_BUCKET_NAME=ip2a-files
S3_REGION=us-east-1                # optional for MinIO
```

### Development Setup

```bash
# MinIO starts automatically with docker-compose
docker-compose up -d

# Access MinIO Console
# URL: http://localhost:9001
# Default credentials: minioadmin / minioadmin
```

---

## 📦 Installation & Upgrade

### New Installation

```bash
git clone https://github.com/theace26/IP2A-Database-v2.git
cd IP2A-Database-v2
git checkout v0.6.0
cp .env.compose.example .env.compose
# Edit .env.compose with your settings
docker-compose up -d
docker exec -it ip2a-api alembic upgrade head
docker exec -it ip2a-api python -m src.seed.run_seed
```

### Upgrade from v0.5.0

```bash
git fetch origin
git checkout v0.6.0
docker-compose up -d  # Pulls new MinIO service
# No new migrations required
```

---

## 🎯 What's Next

### Phase 4: Dues Tracking
- Member dues payments and schedules
- Payment history and receipts
- Arrears tracking and notifications
- Financial reporting

### Phase 5: TradeSchool Integration
- External system connectivity
- Data synchronization

### Phase 6: Frontend
- Jinja2 + HTMX + Alpine.js
- Dashboard and CRUD interfaces
- Mobile-responsive design

---

## 🔗 Links

- **Repository:** https://github.com/theace26/IP2A-Database-v2
- **v0.6.0 Tag:** https://github.com/theace26/IP2A-Database-v2/releases/tag/v0.6.0
- **ADR-004:** docs/decisions/ADR-004-file-storage-strategy.md

---

*Released: January 28, 2026*
```

### Step 6: Update CLAUDE.md Current State

Update the "Current State" section in CLAUDE.md to reflect v0.6.0:

Find and update this section:
```markdown
### 📊 Current State
- **Branch:** main
- **Tag:** v0.6.0 (Phase 3 Document Management)
- **Tests:** 144 total (all passing) ✅
```

And update the "Next Task" line:
```markdown
*Next Task: Phase 4 Dues Tracking*
```

### Step 7: Add Changelog Entry to CLAUDE.md

Add to the changelog table:

```markdown
| 2026-01-28 XX:XX UTC | Claude Code | v0.6.0 Tagged: Phase 3 Document Management complete. Release notes created. Ready for Phase 4 Dues Tracking. |
```

### Step 8: Commit All Changes

```bash
git add -A
git status  # Review changes

git commit -m "docs: Finalize Phase 3, prepare v0.6.0 release

- Update CHANGELOG.md with v0.6.0 release notes
- Create docs/releases/RELEASE_NOTES_v0.6.0.md
- Update CLAUDE.md current state and next steps
- Document Management System complete:
  * 8 API endpoints
  * S3/MinIO integration
  * Presigned URLs
  * File validation
  * 11 tests passing
- ADR-004 implemented"
```

### Step 9: Create Git Tag

```bash
# Create annotated tag
git tag -a v0.6.0 -m "v0.6.0 - Phase 3: Document Management System

Features:
- S3-compatible object storage (MinIO/AWS S3/Backblaze B2)
- 8 document API endpoints
- Presigned URLs for secure access
- Direct-to-S3 uploads for large files
- File validation and organized storage paths
- Soft and hard delete support

Stats:
- 144 tests passing
- ~85 API endpoints total
- ADR-004 implemented

Next: Phase 4 Dues Tracking"

# Verify tag
git tag -l -n1 v0.6.0
```

### Step 10: Push to Remote

```bash
# Push commits
git push origin main

# Push tag
git push origin v0.6.0

# Verify on GitHub
echo "Check: https://github.com/theace26/IP2A-Database-v2/releases/tag/v0.6.0"
```

### Step 11: Create GitHub Release (Optional)

If you want a proper GitHub release with the release notes:

1. Go to https://github.com/theace26/IP2A-Database-v2/releases
2. Click "Draft a new release"
3. Select tag: v0.6.0
4. Title: "v0.6.0 - Phase 3: Document Management System"
5. Copy content from `docs/releases/RELEASE_NOTES_v0.6.0.md`
6. Publish release

---

## Checklist

- [ ] Verify all Phase 3 files exist
- [ ] Run pytest - 144 tests passing
- [ ] Update CHANGELOG.md with v0.6.0 section
- [ ] Create docs/releases/RELEASE_NOTES_v0.6.0.md
- [ ] Update CLAUDE.md current state
- [ ] Add CLAUDE.md changelog entry
- [ ] Commit changes
- [ ] Create v0.6.0 tag
- [ ] Push commits and tag
- [ ] (Optional) Create GitHub release

---

## Expected Outcome

- ✅ v0.6.0 tag created and pushed
- ✅ Release notes documented
- ✅ CHANGELOG.md updated
- ✅ CLAUDE.md reflects current state
- ✅ Ready for Phase 4 Dues Tracking

---

## Next Milestone

**v0.7.0 - Phase 4: Dues Tracking**
- Member dues payments
- Payment schedules
- Arrears tracking
- Financial reporting

---

*End of Instructions*
