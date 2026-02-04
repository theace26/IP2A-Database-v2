# ADR-004: File Storage Strategy

> **Document Created:** 2025 (backfill — original decision predates ADR process)
> **Last Updated:** February 3, 2026
> **Version:** 2.0
> **Status:** Implemented (partial) — Local/S3 Document model live, full S3 lifecycle planned

## Status
Implemented (partial) — Document model, upload/download, and frontend UI are complete. Full S3 lifecycle management (tiering, archival) is planned for post-v1.0.

## Date
2025 (Decided), 2026-01-28 (Implemented)

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

## Implementation Status

| Component | Status | Week | Notes |
|-----------|--------|------|-------|
| Document model (SQLAlchemy) | ✅ | 5–6 | Metadata storage with polymorphic record linking |
| S3 config (`s3_config.py`) | ✅ | 5–6 | Environment-based, supports any S3-compatible endpoint |
| S3 service (`s3_service.py`) | ✅ | 5–6 | Upload, download, presigned URLs, delete |
| Document service | ✅ | 5–6 | CRUD with file validation |
| REST API endpoints (8 endpoints) | ✅ | 5–6 | Upload, presigned upload, download, list, delete |
| Frontend document management UI | ✅ | 9 | Week 9 — upload, browse, download |
| MinIO in docker-compose | ✅ | 5–6 | Local dev environment |
| File validation (extensions, size) | ✅ | 5–6 | Whitelist + 50MB max |
| Presigned URLs for large files | ✅ | 5–6 | Browser → S3 direct upload |
| Railway production deployment | ✅ | 16 | Using local/volume storage currently |
| Full S3 lifecycle (hot → cold) | 🔜 | — | Post-v1.0 priority |
| Backblaze B2 / AWS S3 production | 🔜 | — | Evaluating providers |
| Automated archival jobs | 🔜 | — | Depends on S3 lifecycle setup |

### API Endpoints (Implemented)

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

- **Development:** MinIO service in `docker-compose.yml`
- **Production (current):** Railway volume storage
- **Production (planned):** Configurable endpoint for AWS S3, Backblaze B2, etc.
- **Environment variables:** `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET_NAME`

### Features

- File validation (extension whitelist, max size 50MB)
- Presigned URLs for large file uploads (browser → S3 direct)
- Soft delete (mark as deleted) or hard delete (remove from storage)
- Organized storage paths: `uploads/{type}s/{name}_{id}/{category}/{year}/{month}/`

## Consequences

### Positive
- Database stays small (fast backups)
- Storage scales independently
- Lifecycle policies will reduce costs 70%+ once implemented
- Industry-standard pattern
- Presigned URLs keep large files off the application server

### Negative
- Additional service to manage
- Two backup strategies needed (DB + files)
- Currently using Railway volume storage in production (not yet S3)

### Risks
- Object storage provider outage
  - **Mitigation:** Keep local copies of critical files, consider multi-region
- Railway volume storage limitations
  - **Mitigation:** S3 migration is a post-v1.0 priority

## References
- Architecture: [docs/architecture/FILE_STORAGE_ARCHITECTURE.md](../architecture/FILE_STORAGE_ARCHITECTURE.md)
- S3 config: `src/config/s3_config.py`
- S3 service: `src/services/s3_service.py`
- Document service: `src/services/document_service.py`
- Document model: `src/models/document.py`
- Schemas: `src/schemas/document.py`
- Router: `src/routers/documents.py`
- Frontend: `src/templates/documents/`

---

## 🔄 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs, update as necessary.

---

Document Version: 2.0
Last Updated: February 3, 2026
Previous Version: 1.0 (2026-01-28 — added implementation section)
