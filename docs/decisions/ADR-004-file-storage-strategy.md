# ADR-004: File Storage Strategy

## Status
Accepted

## Date
2025-XX-XX

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

## References
- See: docs/architecture/FILE_STORAGE_ARCHITECTURE.md
