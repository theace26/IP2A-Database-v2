# File Storage Architecture
## IP2A Database v2 - Industry Best Practices for Long-Term File Management

**Document Created:** January 27, 2026
**Last Updated:** January 27, 2026
**Status:** Architecture Specification
**Applies To:** All file attachments in IP2A Database v2

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
- **Maintain compliance** with retention requirements
- **Remain organized** with logical, predictable file paths

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Store files in database? | **No** | Doesn't scale, kills backup performance |
| Storage technology | **S3-compatible object storage** | Industry standard, lifecycle policies |
| File organization | **Entity-based paths** | Easy to find, easy to purge, logical |
| Lifecycle management | **Hot → Warm → Cold tiers** | 70%+ cost savings over time |
| Development storage | **MinIO (self-hosted)** | Free, S3-compatible, runs locally |
| Production storage | **Backblaze B2 or AWS S3** | Durable, affordable, managed |

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
│  file_attachments                           │
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
│           Object Storage (S3)               │
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
│   │   Client    │ ───► │   Server    │ ───► │      (S3 / MinIO)           │ │
│   └─────────────┘      └──────┬──────┘      └─────────────────────────────┘ │
│                               │                                              │
│                               │ Store metadata only                          │
│                               ▼                                              │
│                        ┌─────────────┐                                       │
│                        │  PostgreSQL │                                       │
│                        │  (metadata) │                                       │
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

### Storage Tiers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STORAGE TIERS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│   │   HOT (Active)   │  │  WARM (Archive)  │  │  COLD (Glacier)  │          │
│   ├──────────────────┤  ├──────────────────┤  ├──────────────────┤          │
│   │ Age: 0-2 years   │  │ Age: 2-7 years   │  │ Age: 7+ years    │          │
│   │ Access: Instant  │  │ Access: <1 sec   │  │ Access: Hours    │          │
│   │ Cost: $0.023/GB  │  │ Cost: $0.0125/GB │  │ Cost: $0.004/GB  │          │
│   │                  │  │                  │  │                  │          │
│   │ Use for:         │  │ Use for:         │  │ Use for:         │          │
│   │ • Active files   │  │ • Old records    │  │ • Legal holds    │          │
│   │ • Frequent access│  │ • Rare access    │  │ • Compliance     │          │
│   │ • Current year   │  │ • Historical     │  │ • "Just in case" │          │
│   └──────────────────┘  └──────────────────┘  └──────────────────┘          │
│            │                    │                      │                     │
│            │   After 2 years    │    After 7 years     │                     │
│            └───────────────────►└─────────────────────►│                     │
│                 Automatic lifecycle transitions                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. File Organization Structure

### Directory Hierarchy

The file organization must be:
- **Logical** - Easy to understand
- **Predictable** - Know where files are without querying
- **Scalable** - Works with 1,000 or 1,000,000 files
- **Purgeable** - Easy to delete all files for an entity

```
ip2a-files/                              # Root bucket
│
├── members/                             # Union member documents
│   └── {member_id}/                     # e.g., members/12345/
│       ├── profile/                     # Profile photos, signatures
│       │   ├── photo_2026-01-27.jpg
│       │   └── signature_2026-01-27.png
│       ├── certifications/              # OSHA, First Aid, etc.
│       │   ├── osha10_2026-01-15.pdf
│       │   ├── osha30_2025-06-01.pdf
│       │   └── firstaid_2025-06-01.pdf
│       ├── employment/                  # Employment-related docs
│       │   └── {employer_id}/           # Grouped by employer
│       │       ├── hire_letter_2026-01.pdf
│       │       └── termination_2026-06.pdf
│       ├── dues/                        # Dues-related documents
│       │   └── receipt_2026-01.pdf
│       ├── grievances/                  # Quick access to member's grievances
│       │   └── GR-2026-001/             # Symlink or reference
│       └── correspondence/              # Letters, notices
│           ├── dues_notice_2026-01.pdf
│           └── election_notice_2026-03.pdf
│
├── students/                            # Pre-apprenticeship students
│   └── {student_id}/                    # e.g., students/S-2026-0001/
│       ├── intake/                      # Application materials
│       │   ├── application_2026-01-15.pdf
│       │   ├── id_front_2026-01-15.jpg
│       │   ├── id_back_2026-01-15.jpg
│       │   └── hs_diploma_2026-01-15.pdf
│       ├── certifications/              # Earned during program
│       │   ├── osha10_2026-03-01.pdf
│       │   └── firstaid_2026-03-15.pdf
│       ├── progress/                    # Assessments, evaluations
│       │   ├── assessment_week4_2026-02.pdf
│       │   └── evaluation_final_2026-04.pdf
│       ├── attendance/                  # Attendance records
│       │   └── attendance_march_2026.pdf
│       └── placement/                   # Apprenticeship placement
│           ├── application_ibew_2026-04.pdf
│           └── acceptance_letter_2026-05.pdf
│
├── organizations/                       # Employers, unions, training centers
│   └── {org_id}/                        # e.g., organizations/ORG-0001/
│       ├── contracts/                   # CBAs, agreements
│       │   ├── cba_2024-2027.pdf
│       │   └── side_letter_2025-06.pdf
│       ├── contacts/                    # Business cards, contact info
│       │   └── business_card_john_2026-01.jpg
│       ├── insurance/                   # Certificates of insurance
│       │   └── coi_2026.pdf
│       └── correspondence/              # Letters, communications
│           └── wage_increase_2026-01.pdf
│
├── grievances/                          # Grievance case files
│   └── {grievance_number}/              # e.g., grievances/GR-2026-0001/
│       ├── filing/                      # Initial grievance documents
│       │   ├── grievance_form_2026-01-15.pdf
│       │   └── contract_violation_2026-01-15.pdf
│       ├── evidence/                    # Supporting documentation
│       │   ├── photo_001_2026-01-15.jpg
│       │   ├── photo_002_2026-01-15.jpg
│       │   ├── witness_statement_jones_2026-01-16.pdf
│       │   └── email_exchange_2026-01-10.pdf
│       ├── steps/                       # Step meeting documentation
│       │   ├── step1/
│       │   │   ├── meeting_notes_2026-01-20.pdf
│       │   │   └── employer_response_2026-01-25.pdf
│       │   ├── step2/
│       │   │   ├── meeting_notes_2026-02-10.pdf
│       │   │   └── employer_response_2026-02-15.pdf
│       │   └── step3/
│       │       └── meeting_notes_2026-03-01.pdf
│       ├── arbitration/                 # If escalated to arbitration
│       │   ├── demand_2026-03-15.pdf
│       │   ├── brief_2026-04-01.pdf
│       │   └── award_2026-05-15.pdf
│       └── resolution/                  # Settlement or outcome
│           ├── settlement_agreement_2026-03-10.pdf
│           └── backpay_calculation_2026-03-10.xlsx
│
├── grants/                              # Grant documentation
│   └── {grant_id}/                      # e.g., grants/DOL-2026-001/
│       ├── application/                 # Grant application
│       │   ├── application_2025-08.pdf
│       │   └── budget_narrative_2025-08.xlsx
│       ├── award/                       # Award documents
│       │   ├── award_letter_2025-10.pdf
│       │   └── agreement_2025-10.pdf
│       ├── reports/                     # Submitted reports
│       │   ├── quarterly_q1_2026.pdf
│       │   ├── quarterly_q2_2026.pdf
│       │   └── annual_2026.pdf
│       ├── modifications/               # Budget mods, extensions
│       │   └── extension_request_2026-06.pdf
│       └── correspondence/              # Funder communications
│           └── site_visit_schedule_2026-04.pdf
│
├── market-recovery/                     # Market recovery program docs
│   └── {program_id}/                    # e.g., market-recovery/MRP-2026/
│       ├── program/                     # Program-level documents
│       │   ├── guidelines_2026.pdf
│       │   └── contractor_agreement_template.pdf
│       └── assignments/
│           └── {assignment_id}/         # Per-assignment documents
│               ├── timesheets/
│               │   ├── timesheet_2026-01-w1.pdf
│               │   └── timesheet_2026-01-w2.pdf
│               └── approvals/
│                   └── approval_2026-01.pdf
│
├── benevolence/                         # Benevolence fund applications
│   └── {application_id}/                # e.g., benevolence/BEN-2026-001/
│       ├── application_2026-01-15.pdf
│       ├── supporting_docs/
│       │   ├── medical_bill_2026-01.pdf
│       │   └── hardship_letter_2026-01.pdf
│       └── approval/
│           └── approval_letter_2026-01-20.pdf
│
├── cohorts/                             # Training cohort documents
│   └── {cohort_id}/                     # e.g., cohorts/COHORT-2026-SPRING/
│       ├── roster/
│       │   └── final_roster_2026-01.pdf
│       ├── curriculum/
│       │   └── syllabus_2026.pdf
│       ├── schedules/
│       │   └── class_schedule_2026-01.pdf
│       └── completions/
│           └── completion_certificates_2026-04.pdf
│
└── system/                              # System-level files
    ├── templates/                       # Document templates
    │   ├── grievance_form_template.pdf
    │   ├── benevolence_application.pdf
    │   └── dues_notice_template.docx
    ├── reports/                         # Generated reports
    │   └── {year}/
    │       └── {month}/
    │           └── dues_report_2026-01.pdf
    ├── exports/                         # Data exports
    │   └── member_export_2026-01-27.csv
    └── backups/                         # Database backups (metadata only)
        └── db_backup_2026-01-27.sql.gz
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| **Directories** | lowercase, hyphens | `market-recovery/` |
| **Entity IDs** | Original ID format | `12345/`, `S-2026-0001/` |
| **Filenames** | `{description}_{date}.{ext}` | `osha10_2026-01-15.pdf` |
| **Dates in names** | `YYYY-MM-DD` or `YYYY-MM` | `2026-01-15`, `2026-01` |
| **Versions** | `_v2`, `_v3` suffix | `cba_2024-2027_v2.pdf` |

### Path Generation Rules

```python
def generate_storage_path(
    entity_type: str,      # 'member', 'student', 'grievance', etc.
    entity_id: str,        # The unique ID
    category: str,         # 'certifications', 'evidence', etc.
    filename: str,         # Original filename
    date: datetime = None  # Date for the filename prefix
) -> str:
    """
    Generate a standardized storage path.
    
    Examples:
        generate_storage_path('member', '12345', 'certifications', 'osha.pdf')
        → 'members/12345/certifications/2026-01-27_osha.pdf'
        
        generate_storage_path('grievance', 'GR-2026-001', 'evidence', 'photo.jpg')
        → 'grievances/GR-2026-001/evidence/2026-01-27_photo.jpg'
    """
    date = date or datetime.now()
    date_prefix = date.strftime('%Y-%m-%d')
    safe_filename = sanitize_filename(filename)
    
    # Pluralize entity type for directory
    entity_dir = f"{entity_type}s"  # member → members
    
    return f"{entity_dir}/{entity_id}/{category}/{date_prefix}_{safe_filename}"
```

---

## 5. Database Schema

### File Attachments Table

```sql
-- Main file metadata table
CREATE TABLE file_attachments (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- What is this file attached to?
    entity_type VARCHAR(50) NOT NULL,      -- 'member', 'student', 'grievance', etc.
    entity_id VARCHAR(50) NOT NULL,        -- The ID of the parent record
    
    -- File categorization
    category VARCHAR(50) NOT NULL,         -- 'certification', 'evidence', 'intake'
    subcategory VARCHAR(50),               -- Optional: 'osha', 'firstaid', etc.
    
    -- Original file information
    original_filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100),
    size_bytes BIGINT NOT NULL,
    
    -- Storage location (pointer to actual file)
    storage_provider VARCHAR(20) NOT NULL DEFAULT 's3',  -- 's3', 'minio', 'local'
    storage_bucket VARCHAR(100) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,    -- Full path within bucket
    storage_region VARCHAR(50),            -- AWS region or equivalent
    storage_tier VARCHAR(20) NOT NULL DEFAULT 'hot',  -- 'hot', 'warm', 'cold'
    
    -- Integrity verification
    checksum_sha256 VARCHAR(64) NOT NULL,  -- SHA-256 hash of file content
    checksum_verified_at TIMESTAMP,        -- Last verification timestamp
    
    -- Security
    is_encrypted BOOLEAN NOT NULL DEFAULT FALSE,
    encryption_algorithm VARCHAR(50),      -- 'AES-256-GCM', etc.
    encryption_key_id VARCHAR(100),        -- Reference to key management system
    
    -- Access control
    visibility VARCHAR(20) NOT NULL DEFAULT 'private',  -- 'private', 'internal', 'member', 'public'
    access_roles JSONB DEFAULT '[]',       -- Roles allowed to access: ['staff', 'officer']
    requires_auth BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Lifecycle management
    retention_policy VARCHAR(50),          -- 'standard', 'legal_hold', 'permanent'
    retention_until DATE,                  -- Cannot delete before this date
    delete_after DATE,                     -- Auto-delete after this date
    archived_at TIMESTAMP,                 -- When moved to cold storage
    
    -- Usage tracking
    last_accessed_at TIMESTAMP,
    access_count INTEGER NOT NULL DEFAULT 0,
    
    -- Audit trail
    uploaded_by VARCHAR(100) NOT NULL,     -- User ID who uploaded
    uploaded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Human-readable metadata
    display_name VARCHAR(255),             -- Friendly name for UI
    description TEXT,
    tags JSONB DEFAULT '[]',               -- ['important', 'reviewed', etc.]
    metadata JSONB DEFAULT '{}',           -- Flexible additional data
    
    -- Soft delete (never hard delete files)
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP,
    deleted_by VARCHAR(100),
    deletion_reason TEXT,
    
    -- Constraints
    CONSTRAINT unique_storage_path UNIQUE (storage_bucket, storage_path),
    CONSTRAINT valid_tier CHECK (storage_tier IN ('hot', 'warm', 'cold')),
    CONSTRAINT valid_visibility CHECK (visibility IN ('private', 'internal', 'member', 'public'))
);

-- Indexes for common queries
CREATE INDEX idx_files_entity ON file_attachments(entity_type, entity_id) 
    WHERE is_deleted = FALSE;

CREATE INDEX idx_files_category ON file_attachments(entity_type, category) 
    WHERE is_deleted = FALSE;

CREATE INDEX idx_files_uploaded ON file_attachments(uploaded_at DESC) 
    WHERE is_deleted = FALSE;

CREATE INDEX idx_files_tier ON file_attachments(storage_tier) 
    WHERE is_deleted = FALSE;

CREATE INDEX idx_files_retention ON file_attachments(retention_until) 
    WHERE retention_until IS NOT NULL AND is_deleted = FALSE;

CREATE INDEX idx_files_delete_after ON file_attachments(delete_after) 
    WHERE delete_after IS NOT NULL AND is_deleted = FALSE;

CREATE INDEX idx_files_checksum ON file_attachments(checksum_sha256);

-- Full-text search on filename and description
CREATE INDEX idx_files_search ON file_attachments 
    USING gin(to_tsvector('english', original_filename || ' ' || COALESCE(description, '')));
```

### File Access Log Table

```sql
-- Track all file access for audit/compliance
CREATE TABLE file_access_log (
    id BIGSERIAL PRIMARY KEY,
    file_id UUID NOT NULL REFERENCES file_attachments(id),
    
    -- Who accessed
    accessed_by VARCHAR(100) NOT NULL,
    access_ip VARCHAR(45),
    user_agent VARCHAR(500),
    
    -- What action
    action VARCHAR(20) NOT NULL,  -- 'view', 'download', 'preview'
    
    -- When
    accessed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Additional context
    access_method VARCHAR(50),    -- 'api', 'web', 'presigned_url'
    request_id VARCHAR(100)       -- For tracing
);

CREATE INDEX idx_file_access_file ON file_access_log(file_id, accessed_at DESC);
CREATE INDEX idx_file_access_user ON file_access_log(accessed_by, accessed_at DESC);
CREATE INDEX idx_file_access_date ON file_access_log(accessed_at DESC);

-- Partition by month for large installations
-- CREATE TABLE file_access_log_2026_01 PARTITION OF file_access_log
--     FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

### File Versions Table (Optional)

```sql
-- Track file versions when files are updated
CREATE TABLE file_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES file_attachments(id),
    
    version_number INTEGER NOT NULL,
    
    -- Storage for this version
    storage_path VARCHAR(500) NOT NULL,
    size_bytes BIGINT NOT NULL,
    checksum_sha256 VARCHAR(64) NOT NULL,
    
    -- Audit
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    change_notes TEXT,
    
    -- Is this the current version?
    is_current BOOLEAN NOT NULL DEFAULT FALSE,
    
    CONSTRAINT unique_version UNIQUE (file_id, version_number)
);

CREATE INDEX idx_file_versions_file ON file_versions(file_id, version_number DESC);
```

---

## 6. Storage Provider Options

### Comparison Matrix

| Feature | MinIO (Self-Hosted) | AWS S3 | Backblaze B2 | Google Cloud Storage |
|---------|---------------------|--------|--------------|---------------------|
| **Cost/GB/mo** | Free (+ hardware) | $0.023 | $0.006 | $0.020 |
| **Egress Cost** | Free | $0.09/GB | Free (w/Cloudflare) | $0.12/GB |
| **S3 Compatible** | ✅ 100% | ✅ Native | ✅ Yes | ⚠️ Partial |
| **Lifecycle Policies** | ⚠️ Manual | ✅ Built-in | ✅ Built-in | ✅ Built-in |
| **Glacier/Archive** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **Data Location** | Your servers | AWS regions | US/EU | Google regions |
| **Durability** | Your responsibility | 99.999999999% | 99.999999999% | 99.999999999% |
| **Best For** | Dev, on-premise | Enterprise | Budget prod | Google ecosystem |

### Recommended Setup

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RECOMMENDED CONFIGURATION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   DEVELOPMENT (Local/Home Lab)          PRODUCTION (Cloud)                   │
│   ┌─────────────────────────┐          ┌─────────────────────────┐          │
│   │        MinIO            │          │     Backblaze B2        │          │
│   ├─────────────────────────┤          ├─────────────────────────┤          │
│   │ • Free                  │          │ • $0.006/GB/month       │          │
│   │ • Runs in Docker        │          │ • Free egress via CF    │          │
│   │ • S3-compatible API     │          │ • S3-compatible         │          │
│   │ • Learn S3 patterns     │          │ • Lifecycle policies    │          │
│   │ • Full control          │    OR    │ • 11 nines durability   │          │
│   └─────────────────────────┘          └─────────────────────────┘          │
│                                                                              │
│                                        ┌─────────────────────────┐          │
│                                        │       AWS S3            │          │
│                                        ├─────────────────────────┤          │
│                                        │ • $0.023/GB/month       │          │
│                                        │ • Glacier integration   │          │
│                                        │ • Industry standard     │          │
│                                        │ • Most tooling support  │          │
│                                        └─────────────────────────┘          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### MinIO Setup (Development)

Add to `docker-compose.yml`:

```yaml
services:
  # ... existing services ...

  minio:
    image: minio/minio:latest
    container_name: ip2a-minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-ip2a_admin}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-changeme_dev_only}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"   # S3 API endpoint
      - "9001:9001"   # Web console
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - ip2a-network

  # Initialize MinIO bucket on startup
  minio-init:
    image: minio/mc:latest
    depends_on:
      minio:
        condition: service_healthy
    entrypoint: >
      /bin/sh -c "
      mc alias set myminio http://minio:9000 ip2a_admin changeme_dev_only;
      mc mb --ignore-existing myminio/ip2a-files;
      mc anonymous set none myminio/ip2a-files;
      echo 'MinIO bucket initialized';
      "
    networks:
      - ip2a-network

volumes:
  minio_data:
    driver: local
```

Add to `.env.compose`:

```bash
# MinIO Configuration (Development)
MINIO_ROOT_USER=ip2a_admin
MINIO_ROOT_PASSWORD=your_secure_password_here

# File Storage Configuration
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=ip2a_admin
S3_SECRET_KEY=your_secure_password_here
S3_BUCKET=ip2a-files
S3_REGION=us-east-1
S3_USE_SSL=false
```

---

## 7. Implementation Guide

### Configuration

```python
# src/config/settings.py

from pydantic_settings import BaseSettings
from typing import Optional


class StorageSettings(BaseSettings):
    """File storage configuration."""
    
    # Provider: 's3', 'minio', 'b2', 'gcs', 'local'
    STORAGE_PROVIDER: str = "minio"
    
    # S3-compatible settings
    S3_ENDPOINT: Optional[str] = "http://minio:9000"
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET: str = "ip2a-files"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False
    
    # Lifecycle settings
    HOT_STORAGE_DAYS: int = 730       # 2 years
    WARM_STORAGE_DAYS: int = 2555     # 7 years
    DEFAULT_RETENTION_DAYS: int = 2555
    
    # Limits
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_MIME_TYPES: list = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/gif",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]
    
    class Config:
        env_prefix = ""
        case_sensitive = True


storage_settings = StorageSettings()
```

### File Storage Service

```python
# src/services/file_storage.py
"""
File storage service - abstracts S3/MinIO/B2 operations.
Swap providers by changing configuration, not code.
"""

import boto3
import hashlib
import mimetypes
from botocore.config import Config as BotoConfig
from datetime import datetime, timedelta
from io import BytesIO
from typing import BinaryIO, Optional, Dict, Any
from uuid import uuid4

from src.config.settings import storage_settings


class FileStorageService:
    """
    Handles file upload, download, and lifecycle management.
    Works with S3, MinIO, Backblaze B2, or any S3-compatible storage.
    """
    
    def __init__(self):
        """Initialize storage client."""
        self.client = boto3.client(
            's3',
            endpoint_url=storage_settings.S3_ENDPOINT,
            aws_access_key_id=storage_settings.S3_ACCESS_KEY,
            aws_secret_access_key=storage_settings.S3_SECRET_KEY,
            region_name=storage_settings.S3_REGION,
            config=BotoConfig(
                signature_version='s3v4',
                s3={'addressing_style': 'path'}
            )
        )
        self.bucket = storage_settings.S3_BUCKET
    
    def generate_path(
        self,
        entity_type: str,
        entity_id: str,
        category: str,
        filename: str,
        subcategory: Optional[str] = None
    ) -> str:
        """
        Generate organized storage path.
        
        Args:
            entity_type: 'member', 'student', 'grievance', etc.
            entity_id: Unique identifier for the entity
            category: 'certifications', 'evidence', 'intake', etc.
            filename: Original filename
            subcategory: Optional subcategory for deeper organization
            
        Returns:
            Storage path like: members/12345/certifications/2026-01-27_osha10.pdf
        """
        # Pluralize entity type
        entity_dir = f"{entity_type}s" if not entity_type.endswith('s') else entity_type
        
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        
        # Add date prefix for uniqueness and sorting
        date_prefix = datetime.now().strftime('%Y-%m-%d')
        
        # Build path
        if subcategory:
            return f"{entity_dir}/{entity_id}/{category}/{subcategory}/{date_prefix}_{safe_filename}"
        return f"{entity_dir}/{entity_id}/{category}/{date_prefix}_{safe_filename}"
    
    def upload_file(
        self,
        file: BinaryIO,
        entity_type: str,
        entity_id: str,
        category: str,
        filename: str,
        content_type: Optional[str] = None,
        subcategory: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload file to storage.
        
        Args:
            file: File-like object to upload
            entity_type: Type of entity this file belongs to
            entity_id: ID of the parent entity
            category: Category for organization
            filename: Original filename
            content_type: MIME type (auto-detected if not provided)
            subcategory: Optional subcategory
            metadata: Additional metadata to store with file
            
        Returns:
            Dict with storage metadata for database record
        """
        # Generate storage path
        storage_path = self.generate_path(
            entity_type, entity_id, category, filename, subcategory
        )
        
        # Read file content
        content = file.read()
        file_size = len(content)
        
        # Validate file size
        max_bytes = storage_settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise ValueError(
                f"File size ({file_size / 1024 / 1024:.1f} MB) exceeds "
                f"maximum ({storage_settings.MAX_FILE_SIZE_MB} MB)"
            )
        
        # Auto-detect content type if not provided
        if not content_type:
            content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
        # Validate content type
        if content_type not in storage_settings.ALLOWED_MIME_TYPES:
            raise ValueError(f"File type '{content_type}' is not allowed")
        
        # Calculate checksum
        checksum = hashlib.sha256(content).hexdigest()
        
        # Prepare S3 metadata
        s3_metadata = {
            'original-filename': filename,
            'checksum-sha256': checksum,
            'uploaded-at': datetime.utcnow().isoformat(),
            'entity-type': entity_type,
            'entity-id': entity_id,
        }
        if metadata:
            s3_metadata.update(metadata)
        
        # Upload to S3/MinIO
        self.client.put_object(
            Bucket=self.bucket,
            Key=storage_path,
            Body=content,
            ContentType=content_type,
            Metadata=s3_metadata
        )
        
        return {
            'storage_provider': storage_settings.STORAGE_PROVIDER,
            'storage_bucket': self.bucket,
            'storage_path': storage_path,
            'storage_region': storage_settings.S3_REGION,
            'size_bytes': file_size,
            'checksum_sha256': checksum,
            'mime_type': content_type,
            'original_filename': filename,
        }
    
    def download_file(self, storage_path: str) -> bytes:
        """
        Download file content.
        
        Args:
            storage_path: Path to file in storage
            
        Returns:
            File content as bytes
        """
        response = self.client.get_object(
            Bucket=self.bucket,
            Key=storage_path
        )
        return response['Body'].read()
    
    def download_file_stream(self, storage_path: str) -> BinaryIO:
        """
        Get file as a stream (for large files).
        
        Args:
            storage_path: Path to file in storage
            
        Returns:
            File stream
        """
        response = self.client.get_object(
            Bucket=self.bucket,
            Key=storage_path
        )
        return response['Body']
    
    def get_presigned_url(
        self, 
        storage_path: str, 
        expires_in: int = 3600,
        response_content_type: Optional[str] = None,
        response_filename: Optional[str] = None
    ) -> str:
        """
        Generate temporary URL for direct download.
        
        Use this for large files to avoid proxying through your API.
        
        Args:
            storage_path: Path to file in storage
            expires_in: URL expiration in seconds (default 1 hour)
            response_content_type: Override Content-Type header
            response_filename: Override download filename
            
        Returns:
            Presigned URL valid for expires_in seconds
        """
        params = {
            'Bucket': self.bucket,
            'Key': storage_path
        }
        
        if response_content_type:
            params['ResponseContentType'] = response_content_type
        
        if response_filename:
            params['ResponseContentDisposition'] = f'attachment; filename="{response_filename}"'
        
        return self.client.generate_presigned_url(
            'get_object',
            Params=params,
            ExpiresIn=expires_in
        )
    
    def get_presigned_upload_url(
        self,
        storage_path: str,
        content_type: str,
        expires_in: int = 3600
    ) -> Dict[str, str]:
        """
        Generate presigned URL for direct upload from browser.
        
        Useful for large file uploads without proxying through your API.
        
        Args:
            storage_path: Destination path in storage
            content_type: Expected Content-Type of upload
            expires_in: URL expiration in seconds
            
        Returns:
            Dict with 'url' and 'fields' for form-based upload
        """
        return self.client.generate_presigned_post(
            Bucket=self.bucket,
            Key=storage_path,
            Fields={'Content-Type': content_type},
            Conditions=[
                {'Content-Type': content_type},
                ['content-length-range', 1, storage_settings.MAX_FILE_SIZE_MB * 1024 * 1024]
            ],
            ExpiresIn=expires_in
        )
    
    def delete_file(self, storage_path: str) -> None:
        """
        Delete file from storage.
        
        Note: In production, prefer soft-delete in database.
        Only hard-delete after retention period.
        """
        self.client.delete_object(
            Bucket=self.bucket,
            Key=storage_path
        )
    
    def file_exists(self, storage_path: str) -> bool:
        """Check if file exists in storage."""
        try:
            self.client.head_object(Bucket=self.bucket, Key=storage_path)
            return True
        except self.client.exceptions.ClientError:
            return False
    
    def get_file_info(self, storage_path: str) -> Dict[str, Any]:
        """Get file metadata from storage."""
        response = self.client.head_object(
            Bucket=self.bucket,
            Key=storage_path
        )
        return {
            'size_bytes': response['ContentLength'],
            'content_type': response['ContentType'],
            'last_modified': response['LastModified'],
            'etag': response['ETag'],
            'metadata': response.get('Metadata', {})
        }
    
    def copy_file(self, source_path: str, dest_path: str) -> None:
        """Copy file within storage."""
        self.client.copy_object(
            Bucket=self.bucket,
            Key=dest_path,
            CopySource={'Bucket': self.bucket, 'Key': source_path}
        )
    
    def move_file(self, source_path: str, dest_path: str) -> None:
        """Move file within storage."""
        self.copy_file(source_path, dest_path)
        self.delete_file(source_path)
    
    def change_storage_class(
        self, 
        storage_path: str, 
        storage_class: str
    ) -> None:
        """
        Change storage class (for lifecycle transitions).
        
        Args:
            storage_path: Path to file
            storage_class: 'STANDARD', 'STANDARD_IA', 'GLACIER', etc.
        """
        self.client.copy_object(
            Bucket=self.bucket,
            Key=storage_path,
            CopySource={'Bucket': self.bucket, 'Key': storage_path},
            StorageClass=storage_class,
            MetadataDirective='COPY'
        )
    
    def list_files(
        self, 
        prefix: str, 
        max_keys: int = 1000
    ) -> list:
        """
        List files with a given prefix.
        
        Args:
            prefix: Path prefix (e.g., 'members/12345/')
            max_keys: Maximum number of results
            
        Returns:
            List of file paths
        """
        response = self.client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix,
            MaxKeys=max_keys
        )
        
        return [obj['Key'] for obj in response.get('Contents', [])]
    
    def verify_checksum(self, storage_path: str, expected_checksum: str) -> bool:
        """
        Verify file integrity against stored checksum.
        
        Args:
            storage_path: Path to file
            expected_checksum: Expected SHA-256 hash
            
        Returns:
            True if checksum matches
        """
        content = self.download_file(storage_path)
        actual_checksum = hashlib.sha256(content).hexdigest()
        return actual_checksum == expected_checksum
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Remove dangerous characters from filename.
        
        Keeps: alphanumeric, dots, hyphens, underscores
        """
        import re
        
        # Get just the filename, not any path components
        filename = filename.split('/')[-1].split('\\')[-1]
        
        # Replace spaces with underscores
        filename = filename.replace(' ', '_')
        
        # Keep only safe characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
        
        # Ensure it's not empty
        if not filename or filename.startswith('.'):
            filename = f"file_{uuid4().hex[:8]}"
        
        # Ensure reasonable length
        if len(filename) > 200:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = f"{name[:190]}.{ext}" if ext else name[:200]
        
        return filename


# Singleton instance
file_storage = FileStorageService()
```

### File Attachment CRUD Service

```python
# src/services/file_attachments.py
"""
Database operations for file attachments.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.models.file_attachment import FileAttachment
from src.services.file_storage import file_storage
from src.services.audit import audit_service


class FileAttachmentService:
    """
    Manages file attachment records in database.
    Coordinates with FileStorageService for actual file operations.
    """
    
    def create(
        self,
        db: Session,
        file,  # UploadFile or BinaryIO
        entity_type: str,
        entity_id: str,
        category: str,
        uploaded_by: str,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
        subcategory: Optional[str] = None,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        visibility: str = 'private',
        retention_days: Optional[int] = None
    ) -> FileAttachment:
        """
        Upload file and create database record.
        
        Args:
            db: Database session
            file: File to upload
            entity_type: 'member', 'student', etc.
            entity_id: ID of parent entity
            category: 'certifications', 'evidence', etc.
            uploaded_by: User ID performing upload
            filename: Override filename (uses file.filename if not provided)
            content_type: MIME type (auto-detected if not provided)
            subcategory: Optional subcategory
            display_name: Friendly name for UI
            description: File description
            tags: List of tags
            visibility: 'private', 'internal', 'member', 'public'
            retention_days: Days until auto-delete (None = default policy)
            
        Returns:
            Created FileAttachment record
        """
        # Get filename
        if filename is None:
            filename = getattr(file, 'filename', None) or f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get content type
        if content_type is None:
            content_type = getattr(file, 'content_type', None)
        
        # Upload to storage
        storage_info = file_storage.upload_file(
            file=file.file if hasattr(file, 'file') else file,
            entity_type=entity_type,
            entity_id=entity_id,
            category=category,
            filename=filename,
            content_type=content_type,
            subcategory=subcategory
        )
        
        # Calculate retention dates
        retention_until = None
        delete_after = None
        if retention_days:
            delete_after = datetime.now() + timedelta(days=retention_days)
        
        # Create database record
        attachment = FileAttachment(
            entity_type=entity_type,
            entity_id=entity_id,
            category=category,
            subcategory=subcategory,
            original_filename=filename,
            display_name=display_name or filename,
            description=description,
            tags=tags or [],
            visibility=visibility,
            mime_type=storage_info['mime_type'],
            size_bytes=storage_info['size_bytes'],
            storage_provider=storage_info['storage_provider'],
            storage_bucket=storage_info['storage_bucket'],
            storage_path=storage_info['storage_path'],
            storage_region=storage_info.get('storage_region'),
            storage_tier='hot',
            checksum_sha256=storage_info['checksum_sha256'],
            retention_until=retention_until,
            delete_after=delete_after,
            uploaded_by=uploaded_by
        )
        
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        
        # Audit log
        audit_service.log_create(
            db=db,
            table_name='file_attachments',
            record_id=str(attachment.id),
            new_values={
                'entity_type': entity_type,
                'entity_id': entity_id,
                'category': category,
                'filename': filename,
                'size_bytes': storage_info['size_bytes']
            },
            changed_by=uploaded_by
        )
        
        return attachment
    
    def get(self, db: Session, file_id: UUID) -> Optional[FileAttachment]:
        """Get file attachment by ID."""
        return db.query(FileAttachment).filter(
            and_(
                FileAttachment.id == file_id,
                FileAttachment.is_deleted == False
            )
        ).first()
    
    def get_by_entity(
        self,
        db: Session,
        entity_type: str,
        entity_id: str,
        category: Optional[str] = None
    ) -> List[FileAttachment]:
        """Get all attachments for an entity."""
        query = db.query(FileAttachment).filter(
            and_(
                FileAttachment.entity_type == entity_type,
                FileAttachment.entity_id == entity_id,
                FileAttachment.is_deleted == False
            )
        )
        
        if category:
            query = query.filter(FileAttachment.category == category)
        
        return query.order_by(FileAttachment.uploaded_at.desc()).all()
    
    def get_download_url(
        self,
        db: Session,
        file_id: UUID,
        accessed_by: str,
        expires_in: int = 3600
    ) -> str:
        """
        Get presigned download URL and log access.
        
        Args:
            db: Database session
            file_id: File attachment ID
            accessed_by: User ID requesting download
            expires_in: URL expiration in seconds
            
        Returns:
            Presigned URL for download
        """
        attachment = self.get(db, file_id)
        if not attachment:
            raise ValueError(f"File attachment {file_id} not found")
        
        # Update access tracking
        attachment.last_accessed_at = datetime.utcnow()
        attachment.access_count += 1
        db.commit()
        
        # Log access
        audit_service.log_read(
            db=db,
            table_name='file_attachments',
            record_id=str(file_id),
            changed_by=accessed_by,
            notes=f"Download requested: {attachment.original_filename}"
        )
        
        # Generate presigned URL
        return file_storage.get_presigned_url(
            storage_path=attachment.storage_path,
            expires_in=expires_in,
            response_filename=attachment.original_filename
        )
    
    def soft_delete(
        self,
        db: Session,
        file_id: UUID,
        deleted_by: str,
        reason: Optional[str] = None
    ) -> FileAttachment:
        """
        Soft delete a file attachment.
        
        File remains in storage until retention period expires.
        """
        attachment = self.get(db, file_id)
        if not attachment:
            raise ValueError(f"File attachment {file_id} not found")
        
        old_values = {
            'is_deleted': attachment.is_deleted,
            'deleted_at': attachment.deleted_at
        }
        
        attachment.is_deleted = True
        attachment.deleted_at = datetime.utcnow()
        attachment.deleted_by = deleted_by
        attachment.deletion_reason = reason
        
        db.commit()
        
        # Audit log
        audit_service.log_delete(
            db=db,
            table_name='file_attachments',
            record_id=str(file_id),
            old_values=old_values,
            changed_by=deleted_by,
            notes=reason
        )
        
        return attachment
    
    def hard_delete(
        self,
        db: Session,
        file_id: UUID,
        deleted_by: str
    ) -> None:
        """
        Permanently delete file from storage and database.
        
        WARNING: Only use after retention period has expired.
        """
        attachment = self.get(db, file_id)
        if not attachment:
            # Try to find even if soft-deleted
            attachment = db.query(FileAttachment).filter(
                FileAttachment.id == file_id
            ).first()
        
        if not attachment:
            raise ValueError(f"File attachment {file_id} not found")
        
        # Delete from storage
        try:
            file_storage.delete_file(attachment.storage_path)
        except Exception as e:
            # Log error but continue with database deletion
            print(f"Warning: Could not delete file from storage: {e}")
        
        # Delete from database
        db.delete(attachment)
        db.commit()
        
        # Audit log (for compliance, log even hard deletes)
        audit_service.log_delete(
            db=db,
            table_name='file_attachments',
            record_id=str(file_id),
            old_values={'storage_path': attachment.storage_path},
            changed_by=deleted_by,
            notes='HARD DELETE - file permanently removed'
        )


# Singleton instance
file_attachment_service = FileAttachmentService()
```

---

## 8. Lifecycle Management

### Automated Lifecycle Service

```python
# src/services/file_lifecycle.py
"""
Automated file lifecycle management.

Run via cron:
    0 2 * * * cd /app && python -m src.services.file_lifecycle

Or via CLI:
    ip2adb files lifecycle
"""

import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import text, and_
from sqlalchemy.orm import Session

from src.db.session import SessionLocal
from src.models.file_attachment import FileAttachment
from src.services.file_storage import file_storage
from src.config.settings import storage_settings


class FileLifecycleService:
    """
    Manages file lifecycle:
    - Hot → Warm → Cold tier transitions
    - Retention enforcement
    - Integrity verification
    - Cleanup of expired files
    """
    
    def run_full_cycle(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Run complete lifecycle management cycle.
        
        Args:
            dry_run: If True, report what would happen without making changes
            
        Returns:
            Summary of actions taken
        """
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'dry_run': dry_run,
            'archived_to_warm': 0,
            'archived_to_cold': 0,
            'deleted_expired': 0,
            'integrity_issues': [],
            'errors': []
        }
        
        db = SessionLocal()
        try:
            # 1. Archive old files to warm storage
            warm_count = self.archive_to_warm(db, dry_run=dry_run)
            results['archived_to_warm'] = warm_count
            
            # 2. Archive very old files to cold storage
            cold_count = self.archive_to_cold(db, dry_run=dry_run)
            results['archived_to_cold'] = cold_count
            
            # 3. Delete expired files
            deleted_count = self.delete_expired(db, dry_run=dry_run)
            results['deleted_expired'] = deleted_count
            
            # 4. Verify integrity (sample)
            issues = self.verify_integrity_sample(db)
            results['integrity_issues'] = issues
            
        except Exception as e:
            results['errors'].append(str(e))
        finally:
            db.close()
        
        return results
    
    def archive_to_warm(
        self, 
        db: Session, 
        days_old: int = None,
        dry_run: bool = False
    ) -> int:
        """
        Move files older than X days from hot to warm storage.
        
        Default: 2 years (730 days)
        """
        days_old = days_old or storage_settings.HOT_STORAGE_DAYS
        cutoff = datetime.utcnow() - timedelta(days=days_old)
        
        # Find files to archive
        files = db.query(FileAttachment).filter(
            and_(
                FileAttachment.storage_tier == 'hot',
                FileAttachment.uploaded_at < cutoff,
                FileAttachment.is_deleted == False
            )
        ).all()
        
        if dry_run:
            print(f"[DRY RUN] Would archive {len(files)} files to warm storage")
            return len(files)
        
        archived = 0
        for attachment in files:
            try:
                # Change storage class (S3 only - MinIO ignores this)
                file_storage.change_storage_class(
                    attachment.storage_path,
                    'STANDARD_IA'  # Infrequent Access
                )
                
                # Update database
                attachment.storage_tier = 'warm'
                attachment.archived_at = datetime.utcnow()
                archived += 1
                
            except Exception as e:
                print(f"Error archiving {attachment.storage_path}: {e}")
        
        db.commit()
        print(f"Archived {archived} files to warm storage")
        return archived
    
    def archive_to_cold(
        self, 
        db: Session, 
        days_old: int = None,
        dry_run: bool = False
    ) -> int:
        """
        Move files older than X days from warm to cold (Glacier) storage.
        
        Default: 7 years (2555 days)
        """
        days_old = days_old or storage_settings.WARM_STORAGE_DAYS
        cutoff = datetime.utcnow() - timedelta(days=days_old)
        
        # Find files to archive
        files = db.query(FileAttachment).filter(
            and_(
                FileAttachment.storage_tier == 'warm',
                FileAttachment.uploaded_at < cutoff,
                FileAttachment.is_deleted == False
            )
        ).all()
        
        if dry_run:
            print(f"[DRY RUN] Would archive {len(files)} files to cold storage")
            return len(files)
        
        archived = 0
        for attachment in files:
            try:
                # Change to Glacier
                file_storage.change_storage_class(
                    attachment.storage_path,
                    'GLACIER'
                )
                
                # Update database
                attachment.storage_tier = 'cold'
                attachment.archived_at = datetime.utcnow()
                archived += 1
                
            except Exception as e:
                print(f"Error archiving to cold {attachment.storage_path}: {e}")
        
        db.commit()
        print(f"Archived {archived} files to cold storage (Glacier)")
        return archived
    
    def delete_expired(self, db: Session, dry_run: bool = False) -> int:
        """
        Permanently delete files past their delete_after date.
        
        Only deletes files that:
        1. Have passed their delete_after date
        2. Have passed their retention_until date (if set)
        3. Are already soft-deleted OR have explicit delete_after
        """
        now = datetime.utcnow()
        
        # Find expired files
        files = db.query(FileAttachment).filter(
            and_(
                FileAttachment.delete_after < now,
                # Respect retention_until if set
                (
                    (FileAttachment.retention_until == None) |
                    (FileAttachment.retention_until < now)
                )
            )
        ).all()
        
        if dry_run:
            print(f"[DRY RUN] Would permanently delete {len(files)} expired files")
            for f in files[:10]:  # Show first 10
                print(f"  - {f.storage_path}")
            return len(files)
        
        deleted = 0
        for attachment in files:
            try:
                # Delete from storage
                file_storage.delete_file(attachment.storage_path)
                
                # Delete from database
                db.delete(attachment)
                deleted += 1
                
            except Exception as e:
                print(f"Error deleting {attachment.storage_path}: {e}")
        
        db.commit()
        print(f"Permanently deleted {deleted} expired files")
        return deleted
    
    def verify_integrity_sample(
        self, 
        db: Session, 
        sample_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Verify checksum integrity for a sample of files.
        
        Run weekly to detect storage corruption.
        """
        # Random sample of hot-tier files
        files = db.query(FileAttachment).filter(
            and_(
                FileAttachment.storage_tier == 'hot',
                FileAttachment.is_deleted == False
            )
        ).order_by(text('RANDOM()')).limit(sample_size).all()
        
        issues = []
        verified = 0
        
        for attachment in files:
            try:
                # Download and verify
                is_valid = file_storage.verify_checksum(
                    attachment.storage_path,
                    attachment.checksum_sha256
                )
                
                if is_valid:
                    attachment.checksum_verified_at = datetime.utcnow()
                    verified += 1
                else:
                    issues.append({
                        'file_id': str(attachment.id),
                        'path': attachment.storage_path,
                        'error': 'Checksum mismatch - possible corruption'
                    })
                    
            except Exception as e:
                issues.append({
                    'file_id': str(attachment.id),
                    'path': attachment.storage_path,
                    'error': str(e)
                })
        
        db.commit()
        
        print(f"Verified {verified}/{len(files)} files")
        if issues:
            print(f"WARNING: {len(issues)} integrity issues found!")
            for issue in issues:
                print(f"  - {issue['path']}: {issue['error']}")
        
        return issues
    
    def get_storage_stats(self, db: Session) -> Dict[str, Any]:
        """Get storage statistics by tier."""
        result = db.execute(text("""
            SELECT 
                storage_tier,
                COUNT(*) as file_count,
                SUM(size_bytes) as total_bytes,
                AVG(size_bytes) as avg_bytes
            FROM file_attachments
            WHERE is_deleted = FALSE
            GROUP BY storage_tier
        """))
        
        stats = {}
        for row in result:
            stats[row.storage_tier] = {
                'file_count': row.file_count,
                'total_bytes': row.total_bytes,
                'total_gb': round(row.total_bytes / (1024**3), 2) if row.total_bytes else 0,
                'avg_bytes': round(row.avg_bytes) if row.avg_bytes else 0
            }
        
        return stats


# Singleton
file_lifecycle = FileLifecycleService()


# CLI entry point
if __name__ == "__main__":
    import sys
    
    dry_run = '--dry-run' in sys.argv
    
    print(f"{'[DRY RUN] ' if dry_run else ''}Running file lifecycle management...")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print("-" * 50)
    
    results = file_lifecycle.run_full_cycle(dry_run=dry_run)
    
    print("-" * 50)
    print("Summary:")
    print(f"  Archived to warm: {results['archived_to_warm']}")
    print(f"  Archived to cold: {results['archived_to_cold']}")
    print(f"  Deleted expired: {results['deleted_expired']}")
    print(f"  Integrity issues: {len(results['integrity_issues'])}")
    if results['errors']:
        print(f"  Errors: {len(results['errors'])}")
        for err in results['errors']:
            print(f"    - {err}")
```

---

## 9. Security Considerations

### Access Control Matrix

| Visibility | Who Can Access | Use Case |
|------------|----------------|----------|
| `private` | Only uploading user + admins | Personal documents, drafts |
| `internal` | All staff users | Internal reports, procedures |
| `member` | The member it belongs to + staff | Member's own certifications |
| `public` | Anyone with link | Public documents (rare) |

### Security Checklist

```
✅ IMPLEMENTED / TO IMPLEMENT

Authentication & Authorization:
[ ] All file endpoints require authentication
[ ] Presigned URLs have short expiration (1 hour default)
[ ] Access logged for audit trail
[ ] Role-based access control on file categories

Data Protection:
[ ] Files stored with server-side encryption (S3 SSE-S3 or SSE-KMS)
[ ] HTTPS only for all transfers
[ ] Checksums verified on upload/download
[ ] No file content in URLs (use presigned URLs)

Input Validation:
[ ] Filename sanitization (remove path traversal attempts)
[ ] MIME type validation (whitelist only)
[ ] File size limits enforced
[ ] Virus scanning on upload (future: ClamAV integration)

Operational Security:
[ ] Storage credentials in environment variables, not code
[ ] Credentials rotated regularly
[ ] Bucket policies restrict public access
[ ] Logging enabled on storage bucket
```

### Encryption at Rest

```python
# For AWS S3 - enable default encryption on bucket
# Or specify per-upload:

def upload_with_encryption(self, file, storage_path):
    self.client.put_object(
        Bucket=self.bucket,
        Key=storage_path,
        Body=file,
        ServerSideEncryption='aws:kms',
        SSEKMSKeyId='your-kms-key-id'
    )
```

---

## 10. Cost Projections

### 10-Year Growth Model

Assumptions:
- Start with 100 GB
- Grow 50% per year
- Proper lifecycle management (Hot → Warm → Cold)
- Using Backblaze B2 pricing

| Year | Total Size | Hot | Warm | Cold | Monthly Cost | Annual Cost |
|------|------------|-----|------|------|--------------|-------------|
| 1 | 100 GB | 100 GB | - | - | $0.60 | $7 |
| 2 | 150 GB | 100 GB | 50 GB | - | $0.92 | $11 |
| 3 | 225 GB | 100 GB | 100 GB | 25 GB | $1.35 | $16 |
| 4 | 340 GB | 100 GB | 150 GB | 90 GB | $1.90 | $23 |
| 5 | 500 GB | 100 GB | 200 GB | 200 GB | $2.60 | $31 |
| 6 | 750 GB | 100 GB | 250 GB | 400 GB | $3.50 | $42 |
| 7 | 1.1 TB | 100 GB | 300 GB | 700 GB | $4.70 | $56 |
| 8 | 1.7 TB | 100 GB | 350 GB | 1.25 TB | $6.50 | $78 |
| 9 | 2.5 TB | 100 GB | 400 GB | 2 TB | $9.00 | $108 |
| 10 | 3.8 TB | 100 GB | 450 GB | 3.25 TB | $13.00 | $156 |

**10-Year Total: ~$530** (with lifecycle management)
**Without lifecycle (all hot): ~$2,500**

### Cost by Provider (1 TB)

| Provider | Hot Storage | Archive | Total/Month |
|----------|-------------|---------|-------------|
| Backblaze B2 | $6/TB | $2/TB | ~$8 |
| AWS S3 | $23/TB | $4/TB | ~$12 |
| Google Cloud | $20/TB | $4/TB | ~$11 |
| Wasabi | $7/TB | N/A | $7 (no tiers) |
| MinIO (self) | Hardware cost | Same | ~$2-5 (power) |

---

## 11. Migration Path

### From Current System

If migrating from files stored elsewhere:

```python
# scripts/migrate_files.py
"""
Migrate existing files to new storage architecture.
"""

import os
from pathlib import Path
from src.services.file_storage import file_storage
from src.services.file_attachments import file_attachment_service
from src.db.session import SessionLocal


def migrate_local_files(
    source_dir: str,
    entity_type: str,
    entity_id_extractor,  # Function to extract entity ID from path
    category_extractor,   # Function to extract category from path
    dry_run: bool = True
):
    """
    Migrate files from local directory to object storage.
    
    Args:
        source_dir: Root directory containing files to migrate
        entity_type: 'member', 'student', etc.
        entity_id_extractor: Function(path) -> entity_id
        category_extractor: Function(path) -> category
        dry_run: Preview without actually migrating
    """
    db = SessionLocal()
    migrated = 0
    errors = []
    
    for filepath in Path(source_dir).rglob('*'):
        if filepath.is_file():
            try:
                entity_id = entity_id_extractor(str(filepath))
                category = category_extractor(str(filepath))
                
                if dry_run:
                    print(f"Would migrate: {filepath} → {entity_type}/{entity_id}/{category}/")
                else:
                    with open(filepath, 'rb') as f:
                        file_attachment_service.create(
                            db=db,
                            file=f,
                            entity_type=entity_type,
                            entity_id=entity_id,
                            category=category,
                            uploaded_by='system:migration',
                            filename=filepath.name
                        )
                    migrated += 1
                    
            except Exception as e:
                errors.append({'file': str(filepath), 'error': str(e)})
    
    db.close()
    
    print(f"{'Would migrate' if dry_run else 'Migrated'}: {migrated} files")
    if errors:
        print(f"Errors: {len(errors)}")
        for err in errors[:10]:
            print(f"  - {err}")


# Example usage:
# migrate_local_files(
#     source_dir='/old/member_files',
#     entity_type='member',
#     entity_id_extractor=lambda p: p.split('/')[3],  # Extract from path
#     category_extractor=lambda p: 'documents',
#     dry_run=True
# )
```

---

## 12. Disaster Recovery

### Backup Strategy

| Level | What | Frequency | Retention | Location |
|-------|------|-----------|-----------|----------|
| **Database** | PostgreSQL dump | Daily | 30 days | S3 (different bucket) |
| **File Metadata** | file_attachments table | Daily | 30 days | With DB backup |
| **Files** | S3 replication | Real-time | Indefinite | Different region |
| **Cold Archives** | Glacier | N/A | Per policy | Same as source |

### Recovery Procedures

```bash
# Scenario 1: Single file corrupted
# → Restore from S3 versioning (if enabled) or backup

# Scenario 2: Database lost, files intact
# 1. Restore database from backup
# 2. Files are already in S3, linked by storage_path
# 3. Run integrity check to verify

# Scenario 3: S3 bucket lost
# 1. Restore database from backup
# 2. Restore files from cross-region replica or backup
# 3. Update storage_bucket in database if bucket name changed

# Scenario 4: Complete disaster (everything lost)
# 1. Restore database from off-site backup
# 2. Restore files from cross-region replica
# 3. Verify integrity checksums
# 4. Notify affected users of any data loss
```

---

## 13. API Design

### File Upload Endpoint

```python
# src/routers/files.py

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import Optional, List
from uuid import UUID

from src.services.file_attachments import file_attachment_service
from src.auth.dependencies import get_current_user
from src.db.session import get_db


router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    entity_type: str = Form(...),
    entity_id: str = Form(...),
    category: str = Form(...),
    subcategory: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # Comma-separated
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Upload a file attachment.
    
    - **file**: The file to upload
    - **entity_type**: Type of entity (member, student, grievance, etc.)
    - **entity_id**: ID of the parent entity
    - **category**: Category for organization (certifications, evidence, etc.)
    - **subcategory**: Optional subcategory
    - **description**: Optional description
    - **tags**: Optional comma-separated tags
    """
    # Parse tags
    tag_list = [t.strip() for t in tags.split(',')] if tags else []
    
    # Create attachment
    attachment = file_attachment_service.create(
        db=db,
        file=file,
        entity_type=entity_type,
        entity_id=entity_id,
        category=category,
        subcategory=subcategory,
        description=description,
        tags=tag_list,
        uploaded_by=current_user.id
    )
    
    return {
        "id": str(attachment.id),
        "filename": attachment.original_filename,
        "size_bytes": attachment.size_bytes,
        "storage_path": attachment.storage_path,
        "message": "File uploaded successfully"
    }


@router.get("/{file_id}")
async def get_file_info(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get file metadata."""
    attachment = file_attachment_service.get(db, file_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="File not found")
    
    return attachment


@router.get("/{file_id}/download")
async def download_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get presigned download URL."""
    try:
        url = file_attachment_service.get_download_url(
            db=db,
            file_id=file_id,
            accessed_by=current_user.id
        )
        return {"download_url": url, "expires_in": 3600}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/entity/{entity_type}/{entity_id}")
async def list_entity_files(
    entity_type: str,
    entity_id: str,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all files for an entity."""
    files = file_attachment_service.get_by_entity(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        category=category
    )
    return {"files": files, "count": len(files)}


@router.delete("/{file_id}")
async def delete_file(
    file_id: UUID,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Soft delete a file."""
    try:
        file_attachment_service.soft_delete(
            db=db,
            file_id=file_id,
            deleted_by=current_user.id,
            reason=reason
        )
        return {"message": "File deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

---

## 14. Cron Jobs & Automation

### Recommended Schedule

```bash
# /etc/cron.d/ip2a-file-lifecycle

# Daily: Archive old files and delete expired
0 2 * * * app cd /app && python -m src.services.file_lifecycle >> /var/log/ip2a/file_lifecycle.log 2>&1

# Weekly: Full integrity check (Sundays at 3 AM)
0 3 * * 0 app cd /app && python -m src.services.file_lifecycle --verify-all >> /var/log/ip2a/file_integrity.log 2>&1

# Monthly: Generate storage report (1st of month at 4 AM)
0 4 1 * * app cd /app && python -m src.services.file_lifecycle --report >> /var/log/ip2a/file_report.log 2>&1
```

### CLI Integration

```bash
# Add to ip2adb CLI

# Run lifecycle management
ip2adb files lifecycle

# Preview what would happen
ip2adb files lifecycle --dry-run

# Force archive files older than 1 year
ip2adb files archive --days 365

# Verify all file checksums (slow!)
ip2adb files verify --all

# Storage report
ip2adb files stats
```

---

## 15. Monitoring & Alerts

### Key Metrics to Monitor

| Metric | Warning Threshold | Critical Threshold |
|--------|-------------------|-------------------|
| Storage used | 80% of budget | 90% of budget |
| Upload failures | >1% of uploads | >5% of uploads |
| Checksum failures | Any | - |
| Cold retrieval time | >4 hours | >12 hours |
| Presigned URL errors | >1% | >5% |

### Health Check Endpoint

```python
@router.get("/health")
async def file_storage_health():
    """Check file storage system health."""
    try:
        # Test storage connectivity
        test_key = f"_health_check/{datetime.utcnow().isoformat()}"
        file_storage.client.put_object(
            Bucket=file_storage.bucket,
            Key=test_key,
            Body=b"health check"
        )
        file_storage.delete_file(test_key)
        
        # Get stats
        db = SessionLocal()
        stats = file_lifecycle.get_storage_stats(db)
        db.close()
        
        return {
            "status": "healthy",
            "storage_provider": storage_settings.STORAGE_PROVIDER,
            "bucket": storage_settings.S3_BUCKET,
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

---

## Summary

This architecture provides:

✅ **Scalability** - Handles growth from GBs to TBs seamlessly
✅ **Cost Efficiency** - 70%+ savings through lifecycle tiers
✅ **Data Integrity** - Checksums, verification, audit trails
✅ **Security** - Encryption, access control, presigned URLs
✅ **Compliance** - Retention policies, audit logging
✅ **Disaster Recovery** - Backups, replication, recovery procedures
✅ **Flexibility** - Works with MinIO (dev), B2/S3 (prod)

**Next Steps:**
1. Add MinIO to docker-compose.yml
2. Run database migration for new schema
3. Implement FileStorageService
4. Create file upload/download API endpoints
5. Set up lifecycle cron jobs

---

*Document Version: 1.0*
*Last Updated: January 27, 2026*
*Status: Architecture Specification - Ready for Implementation*
