# File Storage Architecture
## IP2A Database v2 - Industry Best Practices for Long-Term File Management

**Document Created:** January 27, 2026
**Last Updated:** February 3, 2026
**Status:** 🔶 PARTIALLY IMPLEMENTED — Document model exists, basic upload/download works, full S3 lifecycle management pending
**Applies To:** All file attachments in IP2A Database v2

---

## Implementation Status

> **This document was originally written as a pre-implementation specification (v1.0, January 27, 2026).**
> As of v0.9.4-alpha (February 2026), file storage is **partially implemented**. The table below shows current status.

| Component | Status | Notes |
|-----------|--------|-------|
| Document model (`src/models/document.py`) | ✅ Implemented | File metadata stored in PostgreSQL |
| Basic file upload/download API | ✅ Implemented | `src/routers/documents.py`, `src/services/document_service.py` |
| Entity-based file organization | ✅ Implemented | Files linked to members, students, grievances, etc. |
| File validation & soft delete | ✅ Implemented | MIME type checking, soft delete with audit trail |
| MinIO in Docker Compose | ✅ Configured | S3-compatible local development storage |
| Presigned URL generation | ✅ Implemented | Secure temporary download URLs |
| Frontend document management UI | ✅ Implemented | Week 9 — upload, browse, download interface |
| S3/cloud production storage | 🔶 In Progress | Transitioning from local filesystem to S3/MinIO |
| Storage tier lifecycle (hot→warm→cold) | 🔜 Future | Planned for post-v1.0 |
| Automated file integrity verification | 🔜 Future | SHA-256 checksums designed, automation pending |
| Lifecycle cron jobs | 🔜 Future | Archival and cleanup automation |
| Backblaze B2 / AWS S3 production setup | 🔜 Future | Currently using Railway + MinIO |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Golden Rule](#2-the-golden-rule)
3. [Architecture Overview](#3-architecture-overview)
4. [File Organization Structure](#4-file-organization-structure)
5. [Database Schema](#5-database-schema)
6. [Storage Provider Options](#6-storage-provider-options)
7. [Implementation Guide](#7-implementation-guide)
8. [Lifecycle Management](#8-lifecycle-management)
9. [Security Considerations](#9-security-considerations)
10. [Cost Projections](#10-cost-projections)
11. [Migration Path](#11-migration-path)
12. [Disaster Recovery](#12-disaster-recovery)
13. [API Design](#13-api-design)
14. [Cron Jobs & Automation](#14-cron-jobs--automation)
15. [Monitoring & Alerts](#15-monitoring--alerts)

---

## 1. Executive Summary

This document defines the file storage architecture for IP2A Database v2, designed to:

- **Scale to terabytes** over 10+ years of operation
- **Minimize costs** through intelligent lifecycle management
- **Ensure data integrity** with checksums and verification
- **Maintain compliance** with NLRA retention requirements (7-year minimum for member records)
- **Remain organized** with logical, predictable file paths

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Store files in database? | **No** | Doesn't scale, kills backup performance |
| Storage technology | **S3-compatible object storage** | Industry standard, lifecycle policies |
| File organization | **Entity-based paths** | Easy to find, easy to purge, logical |
| Lifecycle management | **Hot → Warm → Cold tiers** | 70%+ cost savings over time |
| Development storage | **MinIO (self-hosted)** | Free, S3-compatible, runs locally in Docker |
| Production storage | **S3/MinIO on Railway** | Current deployment; Backblaze B2 or AWS S3 for future scale |

---

## 2. The Golden Rule

> **Never store file content in the database. Store metadata in the database, files in object storage.**

### Why This Matters

```
❌ WRONG: Files in Database
┌─────────────────────────────────────────────┐
│              PostgreSQL                      │
├─────────────────────────────────────────────┤
│  file_attachments                           │
│  ├── id                                     │
│  ├── filename                               │
│  ├── file_data BYTEA  ← Actual file bytes  │
│  └── uploaded_at                            │
└─────────────────────────────────────────────┘

Problems:
• Database grows to 100+ GB (backup takes hours)
• Queries slow down as table grows
• Can't use CDN for file delivery
• Can't use tiered storage pricing
• Database restore requires ALL files
• Memory pressure during file operations
```

```
✅ RIGHT: Metadata in DB, Files in Object Storage
┌─────────────────────────────────────────────┐
│              PostgreSQL                      │
├─────────────────────────────────────────────┤
│  documents                                  │
│  ├── id                                     │
│  ├── filename                               │
│  ├── storage_path  ← Just a pointer        │
│  ├── size_bytes                             │
│  └── uploaded_at                            │
└──────────────────────┬──────────────────────┘
                       │
                       │ References
                       ▼
┌─────────────────────────────────────────────┐
│           Object Storage (S3/MinIO)         │
├─────────────────────────────────────────────┤
│  Actual file bytes live here                │
│  Scales to petabytes                        │
│  Tiered pricing available                   │
│  CDN integration possible                   │
└─────────────────────────────────────────────┘

Benefits:
• Database stays small (~100 MB)
• Backups complete in minutes
• Files scale independently
• Use cheap storage for old files
• Restore DB without restoring all files
```

---

## 3. Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FILE STORAGE ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────────────────────┐ │
│   │   Browser   │      │   FastAPI   │      │      Object Storage         │ │
│   │   Client    │ ───► │   Server    │ ───► │   (S3 / MinIO / Railway)    │ │
│   │   (PWA)     │      │  (Railway)  │      └─────────────────────────────┘ │
│   └─────────────┘      └──────┬──────┘                                      │
│                               │                                              │
│                               │ Store metadata only                          │
│                               ▼                                              │
│                        ┌─────────────┐                                       │
│                        │ PostgreSQL  │                                       │
│                        │ (metadata)  │                                       │
│                        └─────────────┘                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Upload Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │     │   API    │     │  Storage │     │   Hash   │     │    DB    │
│  Upload  │────►│  Server  │────►│  Service │────►│  Verify  │────►│  Record  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │                │                │
     │  POST /upload  │                │                │                │
     │  + file bytes  │                │                │                │
     │ ──────────────►│                │                │                │
     │                │  Upload to S3  │                │                │
     │                │ ──────────────►│                │                │
     │                │                │  Store file    │                │
     │                │                │ ──────────────►│                │
     │                │                │                │  SHA256        │
     │                │                │                │ ──────────────►│
     │                │                │                │                │
     │                │  Return path   │                │                │
     │                │ ◄──────────────│                │                │
     │                │                                 │                │
     │                │  INSERT metadata                │                │
     │                │ ────────────────────────────────────────────────►│
     │                │                                                  │
     │  201 Created   │                                                  │
     │  + file_id     │                                                  │
     │ ◄──────────────│                                                  │
```

### Download Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │     │   API    │     │    DB    │     │  Storage │
│  Request │────►│  Server  │────►│  Lookup  │────►│  Service │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │                │
     │ GET /files/123 │                │                │
     │ ──────────────►│                │                │
     │                │  Find metadata │                │
     │                │ ──────────────►│                │
     │                │                │                │
     │                │  storage_path  │                │
     │                │ ◄──────────────│                │
     │                │                                 │
     │                │  Generate presigned URL         │
     │                │ ───────────────────────────────►│
     │                │                                 │
     │                │  Temporary URL (1 hour)         │
     │                │ ◄───────────────────────────────│
     │                │                                 │
     │  302 Redirect  │                                 │
     │  to presigned  │                                 │
     │ ◄──────────────│                                 │
     │                                                  │
     │  Download directly from S3                       │
     │ ────────────────────────────────────────────────►│
```

---

## 4. File Organization Structure

### Directory Hierarchy

The file organization is entity-based:

```
ip2a-files/                              # Root bucket
│
├── members/{member_id}/                 # Union member documents
│   ├── profile/                         # Photos, signatures
│   ├── certifications/                  # OSHA, First Aid, etc.
│   ├── employment/{employer_id}/        # Per-employer docs
│   ├── dues/                            # Dues receipts
│   ├── grievances/                      # Quick-access grievance refs
│   └── correspondence/                  # Letters, notices
│
├── students/{student_id}/               # Pre-apprenticeship students
│   ├── intake/                          # Application materials, IDs
│   ├── certifications/                  # Earned during program
│   ├── progress/                        # Assessments, evaluations
│   ├── attendance/                      # Attendance records
│   └── placement/                       # Apprenticeship placement docs
│
├── organizations/{org_id}/              # Employers, unions, JATCs
│   ├── contracts/                       # CBAs, agreements
│   ├── insurance/                       # Certificates of insurance
│   └── correspondence/                  # Letters, communications
│
├── grievances/{grievance_number}/       # Grievance case files
│   ├── filing/                          # Initial grievance documents
│   ├── evidence/                        # Supporting documentation
│   ├── steps/{step_number}/             # Step meeting documentation
│   ├── arbitration/                     # If escalated
│   └── resolution/                      # Settlement or outcome
│
├── grants/{grant_id}/                   # Grant documentation
│   ├── application/                     # Grant application
│   ├── award/                           # Award documents
│   ├── reports/                         # Submitted compliance reports
│   └── modifications/                   # Budget mods, extensions
│
├── benevolence/{application_id}/        # Benevolence fund applications
│   ├── supporting_docs/                 # Medical bills, hardship letters
│   └── approval/                        # Approval documentation
│
├── cohorts/{cohort_id}/                 # Training cohort documents
│   ├── curriculum/                      # Syllabi
│   ├── schedules/                       # Class schedules
│   └── completions/                     # Completion certificates
│
└── system/                              # System-level files
    ├── templates/                       # Document templates
    ├── reports/{year}/{month}/           # Generated reports (PDF/Excel)
    ├── exports/                         # Data exports
    └── backups/                         # Database backup metadata
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| **Directories** | lowercase, hyphens | `market-recovery/` |
| **Entity IDs** | Original ID format | `12345/`, `S-2026-0001/` |
| **Filenames** | `{description}_{date}.{ext}` | `osha10_2026-01-15.pdf` |
| **Dates in names** | `YYYY-MM-DD` or `YYYY-MM` | `2026-01-15`, `2026-01` |
| **Versions** | `_v2`, `_v3` suffix | `cba_2024-2027_v2.pdf` |

---

## 5-12. Detailed Specifications

> **The following sections are preserved from the v1.0 specification (January 27, 2026) and remain the target design:**
>
> - **§5 Database Schema** — `file_attachments` table with entity linkage, checksum verification, lifecycle tracking, encryption support, and soft delete
> - **§6 Storage Provider Options** — MinIO (dev), Backblaze B2 or AWS S3 (prod), with per-provider configuration
> - **§7 Implementation Guide** — `FileStorageService` class with upload/download/delete operations
> - **§8 Lifecycle Management** — Hot (0-2 years), Warm (2-7 years), Cold (7+ years) storage tiers
> - **§9 Security Considerations** — Encryption at rest, presigned URLs with expiry, role-based file access
> - **§10 Cost Projections** — Estimated $5-15/month for first year, scaling with lifecycle tiers
> - **§11 Migration Path** — Local → MinIO → S3 with zero-downtime migration
> - **§12 Disaster Recovery** — Cross-region replication, backup verification, recovery procedures
>
> **Refer to the v1.0 specification for complete code examples and configuration details.**

---

## 13. API Design

The document management API is implemented at `src/routers/documents.py`:

```python
# Implemented endpoints
POST   /documents/upload                    # Upload file with entity linkage
GET    /documents/{file_id}                 # Get file metadata
GET    /documents/{file_id}/download        # Get presigned download URL
GET    /documents/entity/{type}/{id}        # List files for an entity
DELETE /documents/{file_id}                 # Soft delete a file
```

Frontend document management UI was implemented in Week 9 and provides:
- File upload with drag-and-drop support
- Browse documents by entity type
- Download via presigned URLs
- Soft delete with confirmation

---

## 14-15. Cron Jobs & Monitoring

> **Future implementation.** Lifecycle automation (tier transitions, integrity checks, cleanup) and monitoring dashboards will be implemented as the system scales beyond the initial deployment.

---

## Current Deployment Context

### Railway Production
- File storage currently uses local/MinIO storage
- PostgreSQL stores file metadata via the `document` model
- Presigned URLs provide secure download access
- The transition to full S3-compatible cloud storage is in progress

### Next Steps (Priority Order)

1. ~~Add MinIO to docker-compose.yml~~ ✅ Done
2. ~~Database model for file metadata~~ ✅ Done (`src/models/document.py`)
3. ~~Implement document upload/download API~~ ✅ Done (`src/routers/documents.py`)
4. ~~Create document management frontend~~ ✅ Done (Week 9)
5. **Configure S3/MinIO for Railway production** ← Current priority
6. Set up lifecycle automation (cron jobs for tier transitions)
7. Implement file integrity verification automation
8. Set up cross-region backup for file storage

---

## Summary

This architecture provides:

✅ **Scalability** — Handles growth from GBs to TBs seamlessly
✅ **Cost Efficiency** — 70%+ savings through lifecycle tiers (when implemented)
✅ **Data Integrity** — Checksums, verification, audit trails
✅ **Security** — Encryption, access control, presigned URLs
✅ **Compliance** — NLRA retention policies, audit logging
✅ **Disaster Recovery** — Backups, replication, recovery procedures (planned)
✅ **Flexibility** — Works with MinIO (dev), S3 (prod)

---

> **⚠️ SESSION RULE — MANDATORY:**
> At the end of every development session, update *ANY* and *ALL* relevant documents to capture progress made. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.
> See `/docs/standards/END_OF_SESSION_DOCUMENTATION.md`

---

*Document Version: 2.0*
*Last Updated: February 3, 2026*
*Previous Version: 1.0 (January 27, 2026 — pre-implementation specification with full code examples)*
