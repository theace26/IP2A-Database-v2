# Release Notes - v0.6.0

**Release Date:** January 28, 2026
**Tag:** v0.6.0
**Branch:** main

---

## Phase 3 Complete: Document Management System

v0.6.0 delivers a production-ready document management system with S3-compatible storage.

---

## What's New

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

## Project Statistics

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

## Configuration

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

## Installation & Upgrade

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

## What's Next

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

## Links

- **Repository:** https://github.com/theace26/IP2A-Database-v2
- **v0.6.0 Tag:** https://github.com/theace26/IP2A-Database-v2/releases/tag/v0.6.0
- **ADR-004:** docs/decisions/ADR-004-file-storage-strategy.md

---

*Released: January 28, 2026*
