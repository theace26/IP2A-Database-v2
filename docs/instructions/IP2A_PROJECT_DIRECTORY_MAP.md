# IP2A-Database-v2 — Project Directory Structure & Summary

> **Purpose:** Quick-reference map of the entire project for Claude context.  
> Upload this to Claude Project knowledge base so every conversation starts informed.  
> **Project Path:** `C:\Users\Xerxes\Projects\IP2A-Database-v2\`  
> **Last Verified:** February 2, 2026  
> **Version:** v0.9.4-alpha (FEATURE-COMPLETE for Weeks 1-19)

---

## What This Project Is

**IP2A-Database-v2** is a union operations management platform for IBEW Local 46 (Seattle-area electrical workers). It handles member management, training programs, dues tracking, organizing activities (SALTing), benevolence fund applications, grievance management, and (in Phase 7) the out-of-work referral and dispatch system.

**Tech Stack:** Python 3.12 · FastAPI · PostgreSQL 16 · SQLAlchemy 2.x · Jinja2 + HTMX + Alpine.js + DaisyUI · JWT auth · Stripe payments · Docker

**Developer:** Xerxes (solo, 5-10 hrs/week hobby project)

---

## Top-Level Directory Structure

```
C:\Users\Xerxes\Projects\IP2A-Database-v2\
│
├── CLAUDE.md                       # 🔑 Claude Code reads this first every session
├── CHANGELOG.md                    # Version history and changes
├── CONTRIBUTING.md                 # Contribution guidelines
├── README.md                       # Project overview
├── docker-compose.yml              # Docker services (API, DB, MinIO, etc.)
├── Dockerfile                      # Multi-stage build for API
├── pyproject.toml / requirements.txt  # Python dependencies
├── alembic.ini                     # Database migration config
├── .env / .env.example             # Environment variables
├── .devcontainer/                  # VS Code devcontainer config
├── .pre-commit-config.yaml         # Ruff linting hooks
│
├── src/                            # 📦 APPLICATION SOURCE CODE
│   ├── main.py                     # FastAPI application entry point
│   ├── config.py                   # Settings and configuration
│   ├── database.py                 # SQLAlchemy engine and session
│   │
│   ├── models/                     # 🗄️ SQLAlchemy ORM Models (~26 models)
│   │   ├── __init__.py
│   │   ├── user.py                 # User (locked_until datetime, NOT boolean)
│   │   ├── role.py                 # Role + permissions JSON
│   │   ├── user_role.py            # User-Role junction (Association Object)
│   │   ├── refresh_token.py        # JWT refresh tokens
│   │   ├── member.py               # Union member (SEPARATE from Student)
│   │   ├── member_employment.py    # Employment history
│   │   ├── member_note.py          # Staff notes with visibility levels
│   │   ├── student.py              # Training program student (FK to Member)
│   │   ├── course.py               # Training courses
│   │   ├── cohort.py               # Course cohorts/sections
│   │   ├── enrollment.py           # Student-Cohort enrollment
│   │   ├── grade.py                # Student grades
│   │   ├── instructor.py           # Instructor assignments
│   │   ├── instructor_cohort.py    # Instructor-Cohort (Association Object)
│   │   ├── organization.py         # Employers/contractors
│   │   ├── salt_activity.py        # Organizing activities
│   │   ├── benevolence_application.py  # Financial assistance
│   │   ├── grievance.py            # Grievance tracking
│   │   ├── document.py             # File/document metadata
│   │   ├── audit_log.py            # Immutable audit trail (NLRA compliant)
│   │   ├── dues_rate.py            # Dues rate definitions
│   │   ├── dues_period.py          # Billing periods
│   │   ├── dues_payment.py         # Payment records
│   │   ├── dues_adjustment.py      # Payment adjustments
│   │   └── grant_enrollment.py     # Grant compliance tracking
│   │
│   ├── schemas/                    # 📋 Pydantic Schemas (request/response)
│   │   ├── user.py
│   │   ├── member.py
│   │   ├── student.py
│   │   ├── dues.py
│   │   ├── ... (mirrors models/)
│   │   └── common.py               # Shared schemas (pagination, etc.)
│   │
│   ├── services/                   # ⚙️ Business Logic Layer
│   │   ├── auth_service.py         # Login, registration, JWT management
│   │   ├── user_service.py         # User CRUD
│   │   ├── member_service.py       # Member CRUD
│   │   ├── student_service.py      # Student CRUD
│   │   ├── enrollment_service.py   # Enrollment management
│   │   ├── salt_service.py         # SALT activity management
│   │   ├── benevolence_service.py  # Benevolence fund
│   │   ├── grievance_service.py    # Grievance tracking
│   │   ├── document_service.py     # File upload/download (S3/MinIO)
│   │   ├── audit_service.py        # Audit logging (AUDITED_TABLES list)
│   │   ├── dues_service.py         # Dues calculation and tracking
│   │   ├── dues_frontend_service.py  # Frontend helpers for dues UI
│   │   ├── audit_frontend_service.py # Role-filtered audit queries
│   │   ├── member_note_service.py  # Member notes CRUD
│   │   ├── report_service.py       # Report generation
│   │   └── task_service.py         # Abstract background tasks
│   │
│   ├── routers/                    # 🌐 API Endpoints (~150 routes)
│   │   ├── auth.py                 # /auth/*
│   │   ├── users.py                # /users/*
│   │   ├── members.py              # /members/*
│   │   ├── students.py             # /students/*
│   │   ├── courses.py              # /courses/*
│   │   ├── enrollments.py          # /enrollments/*
│   │   ├── salt.py                 # /salt/*
│   │   ├── benevolence.py          # /benevolence/*
│   │   ├── grievances.py           # /grievances/*
│   │   ├── documents.py            # /documents/*
│   │   ├── dues.py                 # /dues/*
│   │   ├── audit.py                # /admin/audit-logs/*
│   │   ├── member_notes.py         # /members/{id}/notes/*
│   │   ├── reports.py              # /reports/*
│   │   └── frontend.py             # Frontend page routes (Jinja2)
│   │
│   ├── db/                         # Database utilities
│   │   ├── enums/                  # 📌 ALL enums defined here
│   │   │   ├── __init__.py         # Central import point
│   │   │   ├── user_enums.py
│   │   │   ├── member_enums.py
│   │   │   ├── dues_enums.py
│   │   │   └── ...
│   │   └── seed.py                 # Seed data (roles, admin user, etc.)
│   │
│   ├── middleware/                  # Request middleware
│   │   ├── auth_middleware.py       # JWT verification
│   │   └── audit_middleware.py      # Audit context injection
│   │
│   ├── templates/                  # 🎨 Jinja2 Frontend Templates
│   │   ├── base.html               # Master layout (DaisyUI + HTMX + Alpine)
│   │   ├── components/
│   │   │   ├── _sidebar.html       # Navigation sidebar
│   │   │   ├── _navbar.html
│   │   │   ├── _flash.html
│   │   │   ├── _pagination.html
│   │   │   ├── _modal.html
│   │   │   └── _audit_history.html # Reusable audit trail partial
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   ├── dashboard/
│   │   │   └── index.html          # Main dashboard with metrics
│   │   ├── members/
│   │   │   ├── list.html
│   │   │   ├── detail.html
│   │   │   ├── _search_results.html
│   │   │   └── _notes_section.html
│   │   ├── students/
│   │   │   ├── list.html
│   │   │   └── detail.html
│   │   ├── staff/
│   │   │   └── list.html
│   │   ├── training/
│   │   │   └── landing.html
│   │   ├── union_ops/
│   │   │   └── landing.html
│   │   ├── dues/
│   │   │   ├── landing.html
│   │   │   ├── rates.html
│   │   │   └── _rates_table.html
│   │   ├── reports/
│   │   │   └── landing.html
│   │   ├── documents/
│   │   │   └── landing.html
│   │   ├── admin/
│   │   │   ├── audit_logs.html
│   │   │   └── _audit_row.html
│   │   └── errors/
│   │       ├── 404.html
│   │       └── 500.html
│   │
│   ├── static/                     # Static assets
│   │   ├── css/
│   │   └── js/
│   │
│   └── tests/                      # 🧪 Test Suite (~470 tests)
│       ├── conftest.py             # Fixtures, test DB setup
│       ├── test_auth.py
│       ├── test_users.py
│       ├── test_members.py
│       ├── test_students.py
│       ├── test_enrollments.py
│       ├── test_salt.py
│       ├── test_benevolence.py
│       ├── test_grievances.py
│       ├── test_documents.py
│       ├── test_dues.py
│       ├── test_audit*.py
│       ├── test_member_notes*.py
│       ├── test_frontend.py        # Frontend route tests (200+ tests)
│       └── ...
│
├── alembic/                        # 🔄 Database Migrations
│   ├── env.py
│   └── versions/                   # Timestamped migration files
│       └── *.py
│
├── scripts/                        # Utility scripts
│   ├── seed_data.py
│   └── ...
│
└── docs/                           # 📚 PROJECT DOCUMENTATION
    ├── README.md                   # Documentation index/hub
    ├── IP2A_MILESTONE_CHECKLIST.md # Progress tracking (update every session)
    ├── IP2A_BACKEND_ROADMAP.md     # Master development roadmap
    │
    ├── architecture/               # How the system is built
    │   ├── SYSTEM_OVERVIEW.md
    │   ├── AUTHENTICATION_ARCHITECTURE.md
    │   ├── FILE_STORAGE_ARCHITECTURE.md
    │   ├── SCALABILITY_ARCHITECTURE.md
    │   ├── AUDIT_ARCHITECTURE.md
    │   └── diagrams/               # Mermaid diagrams
    │
    ├── decisions/                  # Architecture Decision Records (ADRs)
    │   ├── README.md               # ADR index
    │   ├── ADR-001-postgresql.md
    │   ├── ADR-002-jinja2-htmx.md
    │   ├── ADR-003-jwt-auth.md
    │   ├── ADR-004-file-storage.md
    │   ├── ADR-005-tailwind-daisyui.md
    │   ├── ADR-006-background-tasks.md
    │   ├── ADR-007-observability.md
    │   ├── ADR-008-audit-logging.md
    │   └── ... (up to ADR-015+)
    │
    ├── guides/                     # How-to guides
    │   ├── getting-started.md
    │   ├── dues-tracking.md
    │   ├── audit-logging.md
    │   ├── project-strategy.md
    │   └── testing-strategy.md
    │
    ├── reference/                  # Quick reference
    │   ├── ip2adb-cli.md
    │   ├── dues-api.md
    │   ├── audit-api.md
    │   ├── phase2-quick-reference.md
    │   └── integrity-check.md
    │
    ├── reports/                    # Generated reports and session logs
    │   ├── phase-2.1-summary.md
    │   ├── scaling-readiness.md
    │   ├── stress-test-analytics.md
    │   └── session-logs/           # Per-session summaries
    │       └── YYYY-MM-DD-*.md
    │
    ├── runbooks/                   # Operational procedures
    │   ├── deployment.md
    │   ├── backup-restore.md
    │   ├── disaster-recovery.md
    │   └── audit-maintenance.md
    │
    ├── standards/                  # Coding standards
    │   ├── END_OF_SESSION_DOCUMENTATION.md  # ⚠️ MANDATORY session rule
    │   ├── audit-logging.md
    │   ├── coding-standards.md
    │   └── naming-conventions.md
    │
    ├── instructions/               # Claude Code session instructions
    │   ├── week8_instructions/
    │   ├── week9_instructions/
    │   ├── dues_ui_session_a.md    # Week 10
    │   ├── week11_instructions/
    │   └── information to capture in database/   # 📌 NEW FEATURE SPECS
    │       └── (new features that need DB modeling)
    │
    └── phase7/                     # Phase 7: Referral & Dispatch
        ├── PHASE7_REFERRAL_DISPATCH_PLAN.md
        ├── PHASE7_IMPLEMENTATION_PLAN_v2.md
        ├── PHASE7_CONTINUITY_DOC.md
        ├── LOCAL46_REFERRAL_BOOKS.md
        ├── LABORPOWER_GAP_ANALYSIS.md
        └── LABORPOWER_REFERRAL_REPORTS_INVENTORY.md  # 78+ reports to build
```

---

## Key Stats

| Metric | Value |
|--------|-------|
| Version | v0.9.4-alpha |
| ORM Models | ~26 |
| API Endpoints | ~150 |
| Total Tests | ~470 |
| Frontend Tests | 200+ |
| Backend Tests | 165+ |
| ADRs | 10+ |
| Deployment | Railway (prod), Render (backup) |

---

## Critical Patterns to Follow

### Entities
- **Member** is SEPARATE from **Student** (linked via FK on Student)
- **User** model uses `locked_until` datetime field (NOT a boolean `is_locked`)
- **Instructor-Cohort** uses Association Object pattern (not simple M2M)

### Code Organization
- **Enums** always go in `src/db/enums/` and import from `src.db.enums`
- **Services** contain business logic (not routers)
- **Dependency injection** pattern for all services
- Field alignment between SQLAlchemy models ↔ Pydantic schemas ↔ services is critical

### Auth
- JWT access + refresh tokens via HTTP-only cookies
- Role-based access: Admin, Officer, Staff, Organizer, Instructor
- Account lockout uses `locked_until` datetime

### Audit
- All member-related changes audited (NLRA 7-year requirement)
- `audit_logs` table has immutability trigger (no UPDATE/DELETE)
- Sensitive fields (SSN, bank info) redacted for non-admin roles

### Session Rule
> **MANDATORY:** At the end of every session, update *ANY* and *ALL* relevant
> documents. Scan `/docs/*` and make or create relevant updates. Don't forget ADRs.
> See `/docs/standards/END_OF_SESSION_DOCUMENTATION.md`

---

## Branch Strategy
- `main` — Stable, demo-ready (production deployments)
- `develop` — Active development work
- Merge `develop → main` when ready for deployment

---

## Where Things Live (Quick Lookup)

| I need to... | Look in... |
|--------------|------------|
| Start a Claude Code session | `CLAUDE.md` (project root) |
| See what to build next | `docs/IP2A_MILESTONE_CHECKLIST.md` |
| Understand the roadmap | `docs/IP2A_BACKEND_ROADMAP.md` |
| Find new feature specs | `docs/instructions/information to capture in database/` |
| Phase 7 referral plan | `docs/phase7/PHASE7_REFERRAL_DISPATCH_PLAN.md` |
| LaborPower reports to build | `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` |
| Why a decision was made | `docs/decisions/ADR-*.md` |
| End-of-session checklist | `docs/standards/END_OF_SESSION_DOCUMENTATION.md` |
| Past session logs | `docs/reports/session-logs/` |

---

## ⚠️ Note for Claude Instances

This document is a snapshot. Always verify against the actual filesystem — files may have been added, renamed, or moved since this was last updated. When in doubt, run `tree` or `ls` on the actual project directory.

---

*Generated: February 2, 2026*  
*Update this document whenever the project structure changes significantly.*
