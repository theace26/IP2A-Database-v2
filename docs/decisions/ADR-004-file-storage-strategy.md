# ADR-004: File Storage Strategy

## Status
Implemented (Phase 3 - January 2026)

## Date
2025-XX-XX (Decided), 2026-01-28 (Implemented)

## Context

IP2A needs to store files:
- Member certifications (images, PDFs)
- Grievance evidence documents
- Grant reports
- Training materials

Requirements:
- Files must be associated with database records
- Access control (only authorized users see files)
- Reasonable storage costs at scale
- Backup strategy
- 10+ year retention for some documents

## Options Considered

### Option A: Store Files in Database (BLOB)
- Simple: everything in one place
- Backups include files automatically
- Database bloat (slow backups, expensive storage)
- Not recommended for files > 1MB

### Option B: Local Filesystem
- Simple implementation
- No additional services
- Difficult to scale
- No built-in redundancy
- Backup complexity

### Option C: Object Storage (S3-compatible)
- Industry standard for file storage
- Lifecycle policies (hot → cold storage)
- Built-in redundancy
- Scales independently from database
- Cost-effective for large volumes

## Decision

We will use **Object Storage** with:
- **Development:** MinIO (S3-compatible, runs in Docker)
- **Production:** Backblaze B2 or AWS S3
- **Database stores:** Metadata only (path, size, type, owner)
- **Lifecycle tiers:** Hot (30 days) → Warm (1 year) → Cold (archive)

## Consequences

### Positive
- Database stays small (fast backups)
- Storage scales independently
- Lifecycle policies reduce costs 70%+
- Industry-standard pattern

### Negative
- Additional service to manage
- Two backup strategies needed (DB + files)

### Risks
- Object storage provider outage
- Mitigation: Keep local copies of critical files, consider multi-region

## Implementation (Phase 3 - January 2026)

The decision has been implemented with the following components:

### Core Modules
- `src/config/s3_config.py` - Environment-based S3 configuration
- `src/services/s3_service.py` - S3 operations (upload, download, presigned URLs, delete)
- `src/services/document_service.py` - Document CRUD with validation
- `src/schemas/document.py` - Pydantic schemas for API requests/responses
- `src/routers/documents.py` - REST API endpoints

### API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /documents/upload | Direct file upload |
| POST | /documents/presigned-upload | Get presigned URL for large files |
| POST | /documents/confirm-upload | Confirm presigned URL upload |
| GET | /documents/{id} | Get document metadata |
| GET | /documents/{id}/download-url | Get presigned download URL |
| GET | /documents/{id}/download | Stream document content |
| DELETE | /documents/{id} | Soft/hard delete document |
| GET | /documents/ | List with filters (record_type, record_id, category) |

### Infrastructure
- Development: MinIO service in docker-compose.yml
- Production-ready: Configurable endpoint for AWS S3, Backblaze B2, etc.
- Environment variables: S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET_NAME

### Features
- File validation (extension whitelist, max size 50MB)
- Presigned URLs for large file uploads (browser → S3 direct)
- Soft delete (mark as deleted) or hard delete (remove from S3)
- Organized storage paths: `uploads/{type}s/{name}_{id}/{category}/{year}/{month}/`

## References
- See: docs/architecture/FILE_STORAGE_ARCHITECTURE.md
