# IP2A Backend Architecture

## Overview
The IP2A backend is a FastAPI + SQLAlchemy + Alembic application designed with
**preventative safeguards** against schema drift, import breakage, migration
regressions, and seed-order corruption.

This system prioritizes **early failure** over runtime surprises.

---

## Repository Layout

src/
├── main.py # FastAPI entrypoint
├── config/
│ └── settings.py # Environment & config management
├── db/
│ ├── base.py # SQLAlchemy Base
│ ├── session.py # Engine / Session factory
│ └── migrations/
│ ├── env.py # Alembic env (src-aware)
│ └── versions/ # Migration history (governed)
├── models/ # ORM models (single source of truth)
├── services/ # Business logic layer
├── routers/ # API layer
├── seed/
│ ├── run_seed.py # Controlled seed entrypoint
│ ├── seed_registry.py # Canonical seed order
│ ├── seed_integrity.py # Seed dependency validation
│ └── seed_*.py # Individual seeds
└── scripts/
├── validate_imports.py
├── check_alembic_drift.py
├── check_offline_drift.py
├── validate_migrations.py
├── check_breaking_migrations.py
└── preflight.py


---

## Core Principles

### 1. Single Source of Truth
- **Models define reality**
- Alembic migrations must align with models
- Drift is detected automatically

### 2. Fail Fast
- Import graph validated before app start
- Migrations validated before commit
- Seeds validated before execution

### 3. Legacy Respect, Forward Discipline
- Legacy migrations allowed but frozen
- New migrations must follow strict naming + safety rules

---

## Migration Governance

### Naming Rules
| Type | Format |
|-----|------|
| Bootstrap | `0001_baseline.py` (frozen) |
| Legacy | `<hash>_description.py` |
| New | `YYYYMMDDHHMMSS_description.py` |

### Breaking Change Rules
Blocked unless explicitly acknowledged:
- `op.drop_table`
- `op.drop_column`
- `op.alter_column`

Override requires:
```python
# BREAKING_OK


Drift Detection
Online Drift
Requires live database
Used in CI
Detects actual schema mismatch
Offline Drift
No database required
Used in pre-commit
Detects model vs migration divergence
Seeding System
Registry-based ordering
Dependency-aware
Environment protected
PROD seeding hard-blocked unless forced
Enforcement Layers
Layer	Tool
Local dev	pre-commit
CI	GitHub Actions
Runtime	preflight checks
Design Philosophy
Every mistake should fail early, loudly, and with context.
This architecture is intentionally conservative to protect data integrity
as the schema and business rules scale.

---

## Domain Components

### Phase 1: Core Member Management
- **Organizations** - Employers, unions, JATCs
- **Members** - Union members with classifications
- **Member Employments** - Employment history
- **Audit Logs** - Comprehensive change tracking

### Phase 2: Union Operations
- **SALTing Activities** - Organizing campaigns
- **Benevolence Applications** - Financial assistance
- **Grievances** - Formal complaint tracking

### Phase 2 (Roadmap): Pre-Apprenticeship Training
- **Students** - Training program participants
- **Courses** - Training course definitions
- **Class Sessions** - Scheduled sessions
- **Enrollments** - Student-course links
- **Attendances** - Session attendance records
- **Grades** - Assessment results
- **Certifications** - Earned certifications

### Phase 3: Document Management
- **Documents** - S3/MinIO file storage
- Presigned URLs for secure access
- File validation and soft delete

### Phase 4: Dues Tracking
- **Dues Rates** - Classification-based pricing
- **Dues Periods** - Monthly billing cycles
- **Dues Payments** - Payment records
- **Dues Adjustments** - Waivers, credits with approval workflow

See [ADR-008: Dues Tracking System](../decisions/ADR-008-dues-tracking-system.md) for design details.

---

# 2️⃣ Mermaid Architecture Diagram

📁 **Location:** `docs/architecture.mmd` (or inline in README)

```mermaid
flowchart TB
    subgraph Developer
        DEV[Developer]
        PC[Pre-Commit Hooks]
    end

    subgraph Repo
        SRC[src/]
        MODELS[Models]
        MIGRATIONS[Alembic Migrations]
        SEEDS[Seed System]
        SCRIPTS[Validation Scripts]
    end

    subgraph CI
        GH[GitHub Actions]
        PG[(Postgres)]
    end

    subgraph Runtime
        API[FastAPI App]
        DB[(Postgres DB)]
    end

    DEV --> PC
    PC -->|validate_imports| SCRIPTS
    PC -->|offline_drift| SCRIPTS
    PC -->|migration_rules| MIGRATIONS
    PC -->|seed_integrity| SEEDS

    SRC --> MODELS
    MODELS --> MIGRATIONS
    MIGRATIONS --> DB

    GH -->|online_drift| MIGRATIONS
    GH -->|upgrade head| DB

    API --> MODELS
    API --> DB
