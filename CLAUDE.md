# IP2A-Database-v2: Project Context Document

**Document Purpose:** Bring Claude (Code or AI) up to speed for development sessions
**Last Updated:** February 4, 2026
**Current Version:** v0.9.8-alpha
**Current Phase:** Phase 7 (Referral & Dispatch) IN PROGRESS — Weeks 20-27 Complete (Backend + Frontend UI) | Spoke 2

---

## TL;DR

**What:** Union operations management system for IBEW Local 46 (Seattle-area electrical workers union)

**Who:** Xerxes - Business Representative by day, solo developer (5-10 hrs/week)

**Where:** Backend COMPLETE. Frontend FEATURE-COMPLETE (Weeks 1-19). Stripe Payments LIVE. **Deployed to Railway.**

**Stack:** FastAPI + PostgreSQL + SQLAlchemy + Jinja2 + HTMX + DaisyUI + Alpine.js + WeasyPrint + openpyxl + Stripe

**Status:** 593 total tests (250+ frontend, 185+ backend, 78 production, 25 Stripe, 51 Phase 7), ~228+ API endpoints, 32 models (26 existing + 6 Phase 7), 15 ADRs, Railway deployment live, Stripe integration complete, Grant compliance complete, Mobile PWA enabled, Analytics dashboard live

**Current:** Phase 7 — Referral & Dispatch System (~78 LaborPower reports to build). **Weeks 20-27 complete:** models, enums, schemas, 7 services, 5 API routers, 2 frontend services, 2 frontend routers, 13 pages, 15 HTMX partials. See `docs/phase7/`

---

## Development Model: Hub/Spoke

This project uses a **Hub/Spoke model** for planning and coordination via Claude AI projects (claude.ai). This does NOT affect the code architecture — it's about how development conversations are organized.

| Project | Scope | What Goes There |
|---------|-------|-----------------|
| **Hub** | Strategy, architecture, cross-cutting decisions, roadmap, docs | "How should we approach X?" |
| **Spoke 2: Operations** | Dispatch/Referral, Pre-Apprenticeship, SALTing, Benevolence | Phase 7 implementation, instruction docs |
| **Spoke 1: Core Platform** | Members, Dues, Employers, Member Portal | Create when needed |
| **Spoke 3: Infrastructure** | Dashboard/UI, Reports, Documents, Import/Export, Logging | Create when needed |

**What this means for you (Claude Code):**
- You operate directly on the codebase regardless of which Spoke produced the instruction document
- Instruction documents are created in Hub or Spoke projects and provided to you for execution
- If you encounter **cross-cutting concerns** (e.g., changes to `src/main.py`, shared test fixtures in `conftest.py`, or modifications to base templates), note them in your session summary so the user can create a handoff note for the Hub
- The Hub/Spoke model is for human/AI planning coordination, not code architecture. Do not create separate code directories for Spokes.

**Sprint Weeks ≠ Calendar Weeks:** Instruction document "weeks" (Week 20, Week 25, etc.) are sprint numbers, not calendar weeks. At 5-10 hours/week development pace, each sprint takes 1-2 calendar weeks to complete. Do not assume sprint numbers map to specific dates.

---

## Current State

### Backend: COMPLETE + Phase 7 In Progress

| Component | Models | Endpoints | Tests | Status |
|-----------|--------|-----------|-------|--------|
| Core (Org, Member, Employment) | 4 | ~20 | 17 | Done |
| Auth (JWT, RBAC, Registration) | 4 | 13 | 52 | Done |
| Union Ops (SALTing, Benevolence, Grievance) | 5 | 27 | 31 | Done |
| Training (Students, Courses, Grades, Certs) | 7 | ~35 | 33 | Done |
| Documents (S3/MinIO) | 1 | 8 | 11 | Done |
| Dues (Rates, Periods, Payments, Adjustments) | 4 | ~35 | 21 | Done |
| **Phase 7 (Referral & Dispatch)** | **6** | **~50** | **20+** | Services + API Complete |
| **Total** | **32** | **~200** | **185+** | Phase 7 Service Layer Complete |

### Frontend: PHASE 6 COMPLETE + POST-LAUNCH (Weeks 1-19)

| Week | Focus | Status |
|------|-------|--------|
| Week 1 | Setup + Login | Done |
| Week 2 | Auth cookies + Dashboard | Done |
| Week 3 | Staff management | Done |
| Week 4 | Training landing | Done |
| Week 5 | Members landing | Done |
| Week 6 | Union operations | Done |
| Week 7 | (Skipped - docs only) | N/A |
| Week 8 | Reports & Export | Done |
| Week 9 | Documents Frontend | Done |
| Week 10 | Dues UI | Done |
| Week 11 | Audit UI & Member Notes + Stripe | Done |
| Week 12 | Profile & Settings | Done |
| Week 13 | Entity Audit (verified existing) | Done |
| Week 14 | Grant Compliance Reporting | Done |
| Week 16 | Production Hardening & Security | Done |
| Week 17 | Post-Launch Operations & Maintenance | Done |
| Week 18 | Mobile Optimization & PWA | Done |
| Week 19 | Analytics Dashboard & Report Builder | Done |

### Frontend Tests: 200+ tests

| Component | Tests | Status |
|-----------|-------|--------|
| Public Routes (login, forgot-password) | 3 | Done |
| Protected Routes (dashboard, logout) | 2 | Done |
| Static Files (CSS, JS) | 2 | Done |
| Error Pages (404, 500) | 2 | Done |
| Page Content | 3 | Done |
| Cookie Auth | 3 | Done |
| Flash Messages | 2 | Done |
| Dashboard API | 2 | Done |
| Placeholder Routes | 2 | Done |
| Staff Management | 18 | Done |
| Training Frontend | 19 | Done |
| Members Frontend | 15 | Done |
| Operations Frontend | 21 | Done |
| Reports | 30 | Done |
| Documents Frontend | 6 | Done |
| Dues Frontend | 37 | Done |
| Security Headers + Health Checks + Rate Limiting | 32 | Done |
| Admin Metrics | 13 | Done |
| Mobile PWA | 14 | Done |
| Analytics Dashboard | 19 | Done |

---

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| **API** | FastAPI | Async, auto-docs |
| **ORM** | SQLAlchemy 2.0 | Models = source of truth |
| **Database** | PostgreSQL 16 | JSONB, proper constraints |
| **Migrations** | Alembic | Governed, drift-detected |
| **Auth** | JWT + bcrypt | 30min access, 7day refresh, HTTP-only cookies |
| **Files** | MinIO (dev) / S3 (prod) | Presigned URLs |
| **Templates** | Jinja2 | Server-side rendering |
| **Interactivity** | HTMX | HTML-over-the-wire |
| **Micro-interactions** | Alpine.js | Dropdowns, toggles |
| **CSS** | DaisyUI + Tailwind | CDN, no build step |
| **Testing** | pytest + httpx | ~470 total tests (~200+ frontend) |
| **Reports** | WeasyPrint + openpyxl | PDF/Excel generation |
| **Container** | Docker | Full dev environment |

---

## Project Structure

```
IP2A-Database-v2/
├── src/
│   ├── main.py                 # FastAPI entrypoint
│   ├── config/                 # Settings, S3 config, auth config
│   ├── core/                   # Security, JWT utilities
│   ├── db/
│   │   ├── base.py             # SQLAlchemy Base
│   │   ├── session.py          # Engine/Session factory
│   │   ├── enums/              # All enums (import from here!)
│   │   └── migrations/         # Alembic migrations
│   ├── models/                 # ORM models
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic
│   │   ├── dashboard_service.py  # Dashboard stats (Week 2)
│   │   ├── staff_service.py      # Staff management (Week 3)
│   │   ├── training_frontend_service.py  # Training stats (Week 4)
│   │   ├── member_frontend_service.py    # Member stats (Week 5)
│   │   ├── operations_frontend_service.py  # Union ops (Week 6)
│   │   └── dues_frontend_service.py  # Dues UI (Week 10)
│   ├── routers/                # API endpoints
│   │   ├── dependencies/
│   │   │   ├── auth.py         # Bearer token auth
│   │   │   └── auth_cookie.py  # Cookie-based auth (Week 2)
│   │   ├── staff.py            # Staff management (Week 3)
│   │   ├── training_frontend.py # Training pages (Week 4)
│   │   ├── member_frontend.py   # Member pages (Week 5)
│   │   ├── operations_frontend.py  # Union ops (Week 6)
│   │   └── dues_frontend.py     # Dues UI (Week 10)
│   ├── templates/              # Jinja2 templates (Phase 6)
│   │   ├── base.html
│   │   ├── base_auth.html
│   │   ├── components/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── staff/              # Week 3
│   │   ├── training/           # Week 4
│   │   │   ├── index.html
│   │   │   ├── students/
│   │   │   └── courses/
│   │   ├── members/            # Week 5
│   │   │   ├── index.html
│   │   │   ├── detail.html
│   │   │   └── partials/
│   │   ├── operations/         # Week 6
│   │   │   ├── index.html
│   │   │   ├── salting/
│   │   │   ├── benevolence/
│   │   │   └── grievances/
│   │   ├── dues/               # Week 10
│   │   │   ├── index.html
│   │   │   ├── rates/
│   │   │   ├── periods/
│   │   │   ├── payments/
│   │   │   └── adjustments/
│   │   └── errors/
│   ├── static/                 # CSS, JS, images (Phase 6)
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── seed/                   # Seed data
│   └── tests/                  # pytest tests
├── docs/
│   ├── decisions/              # ADRs (001-014)
│   ├── instructions/           # Claude Code instruction docs
│   │   ├── week2_instructions/
│   │   ├── week3_instructions/
│   │   ├── week4_instructions/
│   │   ├── week5_instructions/
│   │   ├── week6_instructions/
│   │   ├── week11–stripe/
│   │   ├── week12_istructions/
│   │   ├── week12_overlooked/
│   │   ├── dues/
│   │   ├── deployment_instructions/
│   │   ├── stripe/
│   │   └── infra_phase2_instructions/
│   ├── phase7/                 # Phase 7: Referral & Dispatch
│   │   ├── PHASE7_REFERRAL_DISPATCH_PLAN.md
│   │   ├── PHASE7_IMPLEMENTATION_PLAN_v2.md
│   │   ├── PHASE7_CONTINUITY_DOC.md
│   │   ├── PHASE7_CONTINUITY_DOC_ADDENDUM.md
│   │   ├── LOCAL46_REFERRAL_BOOKS.md
│   │   ├── LABORPOWER_GAP_ANALYSIS.md
│   │   ├── LABORPOWER_IMPLEMENTATION_PLAN.md
│   │   └── LABORPOWER_REFERRAL_REPORTS_INVENTORY.md
│   ├── architecture/           # System docs
│   ├── guides/                 # How-to guides
│   ├── standards/              # Coding standards + END_OF_SESSION_DOCUMENTATION.md
│   ├── runbooks/               # Deployment, backup, DR, incident response, audit-maintenance
│   ├── BUGS_LOG.md             # Historical bugs record
│   └── archive/                # Old documentation
├── scripts/                    # Operational scripts (Week 17)
│   ├── backup_database.sh      # Database backup
│   ├── verify_backup.sh        # Backup verification
│   ├── archive_audit_logs.sh   # Audit log archival
│   ├── cleanup_sessions.sh     # Session cleanup
│   └── crontab.example         # Scheduled tasks example
├── docker-compose.yml
├── CLAUDE.md                   # This file
├── CHANGELOG.md
└── requirements.txt
```

---

## Quick Commands

```bash
# Start environment
cd ~/Projects/IP2A-Database-v2
docker-compose up -d

# Run tests
pytest -v

# Run specific test file
pytest src/tests/test_training_frontend.py -v

# Apply migrations
alembic upgrade head

# Seed database
python -m src.seed.run_seed

# Run API server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Format code
ruff check . --fix && ruff format .
```

---

## Phase 6 Week 10: COMPLETE

**Objective:** Implement dues management frontend UI

**Instruction Documents:** `docs/instructions/dues/`

### All Sessions Complete (January 30, 2026)

| Task | Status |
|------|--------|
| DuesFrontendService with stats and badge helpers | Done |
| Dues landing page with current period display | Done |
| Stats cards (MTD, YTD, overdue, pending) | Done |
| Quick action cards for rates/periods/payments/adjustments | Done |
| Rates list page with HTMX filtering | Done |
| Rates table partial with status badges | Done |
| Sidebar navigation with Dues dropdown | Done |
| Periods list page with year/status filters | Done |
| Generate year modal | Done |
| Period detail with payment summary | Done |
| Close period workflow | Done |
| Payments list with search and filters | Done |
| Record payment modal | Done |
| Member payment history page | Done |
| Adjustments list with status/type filters | Done |
| Adjustment detail with approve/deny | Done |
| Comprehensive tests (37 total) | Done |
| ADR-011: Dues Frontend Patterns | Done |

### Files Created

```
src/
├── services/
│   └── dues_frontend_service.py    # Stats, badge helpers, formatting
├── routers/
│   └── dues_frontend.py            # Dues page routes
├── templates/
│   └── dues/
│       ├── index.html              # Landing page with stats
│       ├── rates/
│       │   ├── index.html          # Rates list with filters
│       │   └── partials/_table.html
│       ├── periods/
│       │   ├── index.html          # Periods list
│       │   ├── detail.html         # Period detail
│       │   └── partials/_table.html
│       ├── payments/
│       │   ├── index.html          # Payments list
│       │   ├── member.html         # Member payment history
│       │   └── partials/_table.html
│       └── adjustments/
│           ├── index.html          # Adjustments list
│           ├── detail.html         # Adjustment detail
│           └── partials/_table.html
└── tests/
    └── test_dues_frontend.py       # 37 tests
```

### Modified Files

```
src/main.py                              # Added dues_frontend router
src/templates/components/_sidebar.html   # Converted Dues to dropdown menu
```

**Version:** v0.7.9 (Week 10 Complete)

**Next:** Deployment Prep (Railway/Render)

---

## Phase 6 Week 8: COMPLETE

**Objective:** Implement report generation with PDF and Excel export capabilities

**Instruction Documents:** `docs/instructions/week8_instructions/`

### Session A-C: Reports Implementation (January 29, 2026)

| Task | Status |
|------|--------|
| Add weasyprint and openpyxl dependencies | Done |
| Create ReportService with PDF/Excel generation | Done |
| Create reports router with landing page | Done |
| Create reports landing template | Done |
| Create PDF templates (member roster, dues, etc.) | Done |
| Member roster report (PDF/Excel) | Done |
| Dues summary report (PDF/Excel) | Done |
| Overdue members report (PDF/Excel) | Done |
| Training enrollment report (Excel) | Done |
| Grievance summary report (PDF) | Done |
| SALTing activities report (Excel) | Done |
| Comprehensive tests (30 total) | Done |

**Note:** WeasyPrint requires system libraries (libpango, libgdk-pixbuf) for PDF generation. Tests skip PDF generation when these aren't available.

### Files Created

```
src/
├── services/
│   └── report_service.py            # PDF/Excel generation utilities
├── routers/
│   └── reports.py                   # Report routes
├── templates/
│   └── reports/
│       ├── index.html               # Reports landing page
│       ├── base_pdf.html            # PDF base template
│       ├── member_roster.html       # Member roster PDF
│       ├── dues_summary.html        # Dues summary PDF
│       ├── overdue_report.html      # Overdue members PDF
│       └── grievance_summary.html   # Grievance PDF
└── tests/
    └── test_reports.py              # 30 tests
```

### Modified Files

```
requirements.txt                     # Added weasyprint, openpyxl
src/main.py                          # Added reports router
```

---

## Phase 6 Week 9: COMPLETE

**Objective:** Implement document management frontend with upload, browse, and file operations

**Instruction Documents:** `docs/instructions/week9_instructions/`

### Session A-C: Documents Implementation (January 29, 2026)

| Task | Status |
|------|--------|
| Create documents_frontend router | Done |
| Create documents landing page with stats | Done |
| Create upload page with drag-drop zone (Alpine.js) | Done |
| Create browse page with file list | Done |
| Add download redirect endpoint | Done |
| Add delete endpoint with HTMX | Done |
| Create HTMX partials for success/error | Done |
| Add Documents link to sidebar | Done |
| Comprehensive tests (6 total) | Done |

**Note:** S3/MinIO connection required for full functionality. Tests skip S3-dependent operations when unavailable.

### Files Created

```
src/
├── routers/
│   └── documents_frontend.py       # Document management routes
├── templates/
│   └── documents/
│       ├── index.html              # Landing page with stats
│       ├── upload.html             # Drag-drop upload (Alpine.js)
│       ├── browse.html             # File browser with filters
│       └── partials/
│           ├── _file_list.html     # HTMX file list
│           ├── _upload_success.html
│           ├── _upload_error.html
│           ├── _delete_success.html
│           └── _delete_error.html
└── tests/
    └── test_documents_frontend.py  # 6 tests
```

### Modified Files

```
src/main.py                          # Added documents_frontend router
src/templates/components/_sidebar.html  # Added Documents link
```

---

## Phase 6 Week 5: COMPLETE

**Objective:** Build Members landing page with search, detail, and employment/dues views

**Instruction Documents:** `docs/instructions/week5_instructions/`

### Session A: Members Overview (January 29, 2026)

| Task | Status |
|------|--------|
| Create MemberFrontendService with stats queries | Done |
| Create member_frontend router | Done |
| Create members/index.html landing page | Done |
| Stats: total, active, inactive/suspended, dues current % | Done |
| Classification breakdown with badges | Done |
| Search and filter controls | Done |

### Session B: Member List (January 29, 2026)

| Task | Status |
|------|--------|
| Create _table.html with pagination | Done |
| Create _row.html with badges | Done |
| HTMX live search with 300ms debounce | Done |
| Filter by status and classification | Done |
| Status and classification badges | Done |
| Current employer display | Done |
| Quick edit modal | Done |
| Row actions dropdown | Done |

### Session C: Member Detail + Tests (January 29, 2026)

| Task | Status |
|------|--------|
| Create members/detail.html page | Done |
| Contact information section | Done |
| Employment history timeline (HTMX loaded) | Done |
| Dues summary section (HTMX loaded) | Done |
| Current employer sidebar | Done |
| Quick actions sidebar | Done |
| Comprehensive tests (15 total) | Done |

**Commit:**
- `d6f7132 feat(members): Phase 6 Week 5 Complete - Members Landing Page`

### Files Created

```
src/
├── services/
│   └── member_frontend_service.py   # Stats and queries
├── routers/
│   └── member_frontend.py           # Member page routes
├── templates/
│   └── members/
│       ├── index.html               # Landing page
│       ├── detail.html              # Detail page
│       └── partials/
│           ├── _stats.html          # Stats cards
│           ├── _table.html          # Table with pagination
│           ├── _row.html            # Single row
│           ├── _edit_modal.html     # Quick edit
│           ├── _employment.html     # Employment timeline
│           └── _dues_summary.html   # Dues section
└── tests/
    └── test_member_frontend.py      # 15 tests
```

---

## Phase 6 Week 4: COMPLETE

**Objective:** Build Training module landing page with student/course management

**Instruction Documents:** `docs/instructions/week4_instructions/`

### Session A: Training Overview (January 29, 2026)

| Task | Status |
|------|--------|
| Create TrainingFrontendService with stats queries | Done |
| Create training_frontend router | Done |
| Create training/index.html landing page | Done |
| Stats: students, completed, courses, completion rate | Done |
| Recent students table | Done |
| Quick action buttons | Done |

### Session B: Student List (January 29, 2026)

| Task | Status |
|------|--------|
| Create students/index.html with search/filter | Done |
| Create _table.html and _row.html partials | Done |
| HTMX live search with 300ms debounce | Done |
| Filter by status and cohort | Done |
| Status badges with colors | Done |
| Pagination component | Done |
| Create students/detail.html page | Done |
| Add student detail route | Done |

### Session C: Course List + Tests (January 29, 2026)

| Task | Status |
|------|--------|
| Create courses/index.html with card layout | Done |
| Create courses/detail.html page | Done |
| Add course detail route | Done |
| Enrollment counts per course | Done |
| Comprehensive tests (19 total) | Done |

**Commits:**
- `ef77cb8 feat(training): Phase 6 Week 4 Session A - Training landing page`
- `db19cac feat(training): Phase 6 Week 4 Session B - Student list enhancements`
- `bbcd7ca feat(training): Phase 6 Week 4 Session C - Course detail and comprehensive tests`

### Files Created

```
src/
├── services/
│   └── training_frontend_service.py  # Stats and queries
├── routers/
│   └── training_frontend.py          # Training page routes
├── templates/
│   └── training/
│       ├── index.html                # Landing page
│       ├── students/
│       │   ├── index.html            # Student list
│       │   ├── detail.html           # Student detail
│       │   └── partials/
│       │       ├── _table.html       # Table with pagination
│       │       └── _row.html         # Single row
│       └── courses/
│           ├── index.html            # Course cards
│           └── detail.html           # Course detail
└── tests/
    └── test_training_frontend.py     # 19 tests
```

---

## Phase 6 Week 3: COMPLETE

**Objective:** Build Staff Management feature with search, edit, and account actions

**Instruction Documents:** `docs/instructions/week3_instructions/`

### Session A: User List with Search (January 29, 2026)

| Task | Status |
|------|--------|
| Create StaffService with search/filter/paginate | Done |
| Create staff router with list endpoints | Done |
| Create staff/index.html with user table | Done |
| Create table partials (_table_body.html, _row.html) | Done |
| Add 403 error page | Done |
| HTMX live search with debounce | Done |
| Filter by role and status | Done |
| Pagination component | Done |

### Session B: Quick Edit Modal (January 29, 2026)

| Task | Status |
|------|--------|
| Create _edit_modal.html template | Done |
| Add edit modal GET/POST endpoints | Done |
| Multi-select role checkboxes | Done |
| Account status toggle | Done |
| HTMX save with feedback | Done |
| Auto-dismiss alerts | Done |

### Session C: Account Actions + Detail Page (January 29, 2026)

| Task | Status |
|------|--------|
| Add lock/unlock endpoints | Done |
| Add password reset endpoint | Done |
| Add soft delete endpoint | Done |
| Create detail.html full page | Done |
| Service methods for actions | Done |
| Comprehensive tests (18 total) | Done |

**Commits:**
- `4d80365 feat(staff): Phase 6 Week 3 Session A - User list with search`
- `85ada48 feat(staff): Phase 6 Week 3 Session B - Quick edit modal`
- `89a045c feat(staff): Phase 6 Week 3 Session C - Actions and detail page`

### Files Created

```
src/
├── services/
│   └── staff_service.py         # User CRUD, search, audit
├── routers/
│   └── staff.py                 # All staff endpoints
├── templates/
│   ├── staff/
│   │   ├── index.html           # List page
│   │   ├── detail.html          # Detail page
│   │   └── partials/
│   │       ├── _table_body.html
│   │       ├── _row.html
│   │       └── _edit_modal.html
│   └── errors/
│       └── 403.html             # Access denied
└── tests/
    └── test_staff.py            # 18 tests
```

---

## Phase 6 Week 2: COMPLETE

**Objective:** Implement cookie-based authentication and dashboard with real data

**Instruction Documents:** `docs/instructions/week2_instructions/`

### Session A: Cookie-Based Authentication (January 29, 2026)

| Task | Status |
|------|--------|
| Create auth_cookie.py dependency | Done |
| Update auth router to set HTTP-only cookies | Done |
| Update frontend router with auth middleware | Done |
| Fix login template path (/auth/login) | Done |

**Key Changes:**
- HTTP-only cookies for access_token (30 min) and refresh_token (7 days)
- Protected routes redirect to login with flash message
- Token expiry handled gracefully

### Session B: Dashboard with Real Data (January 29, 2026)

| Task | Status |
|------|--------|
| Create dashboard_service.py | Done |
| Count active members from Member model | Done |
| Count active students from Student model | Done |
| Count pending grievances | Done |
| Sum dues collected this month | Done |
| Add HTMX refresh for stats | Done |
| Add recent activity from audit log | Done |

**Key Changes:**
- DashboardService class with efficient COUNT queries
- Stats: active_members, members_change, active_students, pending_grievances, dues_mtd
- Activity feed from AuditLog with badges and time-ago formatting

### Session C: Polish and Tests (January 29, 2026)

| Task | Status |
|------|--------|
| Add flash message support | Done |
| Handle token expiry with redirect | Done |
| Add comprehensive auth tests | Done |
| All 187 tests passing | Done |

**Commit:** `b997022 feat(frontend): Phase 6 Week 2 - Auth cookies and dashboard data`

### Acceptance Criteria - All Met

- [x] Login sets HTTP-only cookies
- [x] Protected routes redirect to login when not authenticated
- [x] Dashboard shows real member/student/grievance/dues stats
- [x] Activity feed shows recent audit log entries
- [x] Flash messages display on login page
- [x] All tests pass (177 existing + 10 new = 187)

---

## Phase 6 Week 1: COMPLETE

**Objective:** Set up frontend foundation and working login page

### Session A Complete (January 28, 2026)

| Task | Status |
|------|--------|
| Pre-flight checks (Docker, tests, API, git) | Done |
| Tag v0.7.0 (backend milestone) | Done |
| Create directory structure (templates, static) | Done |
| Create base templates and components | Done |
| Create custom.css and app.js | Done |

**Commit:** `009fa3b feat(frontend): Phase 6 Week 1 Session A - Frontend foundation`

### Session B Complete (January 28, 2026)

| Task | Status |
|------|--------|
| Create login.html and forgot_password.html | Done |
| Create dashboard/index.html | Done |
| Create error pages (404, 500) | Done |
| Create frontend router | Done |
| Add frontend tests (12 tests) | Done |

**Commit:** `1274c12 feat(frontend): Phase 6 Week 1 Session B - Pages and integration`

---

## Important Patterns

### Enum Imports
```python
# CORRECT
from src.db.enums import MemberStatus, StudentStatus, CourseEnrollmentStatus

# WRONG (old location)
from src.models.enums import MemberStatus
```

### Service Layer Pattern
All business logic goes through services, not directly in routes.

### Cookie-Based Auth (Week 2)
```python
from src.routers.dependencies.auth_cookie import require_auth

@router.get("/protected")
async def protected_page(
    request: Request,
    current_user: dict = Depends(require_auth),
):
    # Handle redirect
    if isinstance(current_user, RedirectResponse):
        return current_user
    # current_user has: id, email, roles
```

### JWT Secret Key Configuration (CRITICAL - Bug #006 Fix)

**IMPORTANT:** The `AUTH_JWT_SECRET_KEY` environment variable MUST be set in production.

If not set, a random secret is generated on each container restart, which:
- Invalidates ALL existing user sessions
- Causes "Signature verification failed" errors
- Forces all users to re-login after every deployment

**To Fix (Railway/Production):**
```bash
# 1. Generate a secure key
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# 2. Add to Railway environment variables:
AUTH_JWT_SECRET_KEY=<paste-generated-key-here>

# 3. Redeploy
```

**Startup Warning:** If the key is not set, the app logs a warning at startup:
```
WARNING: AUTH_JWT_SECRET_KEY not set in environment!
A random secret was generated. This means:
  - All user sessions will be invalidated on restart
  - Users will see 'Signature verification failed' errors
```

See: `docs/BUGS_LOG.md` Bug #006 for full details.

### Form-Based Login (IMPORTANT - Bug #005 Fix)

The login form uses a **form-based endpoint** that accepts URL-encoded data directly:

```html
<!-- Login form posts to form-based endpoint (NOT /auth/login) -->
<form hx-post="/login">
    <input name="email" type="email">
    <input name="password" type="password">
</form>
```

**Two Login Endpoints:**
| Endpoint | Content-Type | Use Case |
|----------|--------------|----------|
| `POST /login` | Form data | HTML forms (HTMX) - in `frontend.py` |
| `POST /auth/login` | JSON | API clients (mobile apps) - in `auth.py` |

**Why:** The HTMX `json-enc` extension was unreliable in production. Instead of converting form data to JSON, we accept form data directly using FastAPI's `Form()` parameters.

```python
# frontend.py - accepts form data
@router.post("/login")
async def login_form_submit(
    email: str = Form(...),
    password: str = Form(...),
):
    user = authenticate_user(db, email, password)
    # ... set cookies and return
```

See: `docs/BUGS_LOG.md` Bug #005 for full details.

### System Setup Flow

The system has a first-time setup flow that requires creating a personal administrator account:

1. **Default Admin Account** (`admin@ibew46.com`)
   - Seeded automatically on deployment
   - Cannot be deleted or have email/password changed via setup page
   - CAN be disabled via checkbox during setup (recommended for production)
   - Can be re-enabled later from Staff Management

2. **Setup Required When**
   - No users exist at all
   - Only the default admin account exists

3. **Setup Process**
   - User must create their own administrator account
   - Optionally disable the default admin account
   - Default admin email cannot be used for the new account

```python
from src.services.setup_service import (
    is_setup_required,
    get_default_admin_status,
    create_setup_user,
    disable_default_admin,
    DEFAULT_ADMIN_EMAIL,
)

# Check if setup is needed
if is_setup_required(db):
    # Show setup page

# Create user during setup
create_setup_user(
    db=db,
    email="user@example.com",
    password="SecurePass@247!",
    first_name="John",
    last_name="Doe",
    role="admin",
    disable_default_admin_account=True,  # Optional
)
```

### Template Rendering
```python
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="src/templates")

@router.get("/page")
async def page(request: Request):
    return templates.TemplateResponse("page.html", {"request": request})
```

### HTMX Form Pattern
```html
<form hx-post="/auth/login" hx-target="#result" hx-swap="innerHTML">
    <!-- form fields -->
</form>
```

### HTMX Search Pattern (Week 3/4)
```html
<input
    type="search"
    name="q"
    hx-get="/training/students/search"
    hx-trigger="input changed delay:300ms, search"
    hx-target="#table-container"
    hx-include="[name='status'], [name='cohort']"
/>
```

### HTMX 401 Error Handling (Bug #022 Fix)

When HTMX requests return 401 (session expired), the backend should include the `HX-Redirect` header:

```python
# In router endpoints for HTMX partials
if isinstance(current_user, RedirectResponse):
    return HTMLResponse(
        "Session expired",
        status_code=401,
        headers={"HX-Redirect": "/auth/login?next=/current/path"},
    )
```

The frontend JavaScript also handles 401 with automatic redirect:

```javascript
// src/static/js/app.js
if (status === 401) {
    showToast('Session expired. Redirecting to login...', 'warning');
    setTimeout(function() {
        window.location.href = '/auth/login?next=' + encodeURIComponent(window.location.pathname);
    }, 1000);
    return;
}
```

### Synchronous Database Sessions (Bug #024 Fix)

**IMPORTANT:** This codebase uses **synchronous** SQLAlchemy sessions, NOT async.

```python
# CORRECT - synchronous
from sqlalchemy.orm import Session

def some_function(db: Session = Depends(get_db)):
    result = db.execute(stmt)  # NO await
    items = result.scalars().all()

# WRONG - async (will cause 500 errors)
from sqlalchemy.ext.asyncio import AsyncSession

async def some_function(db: AsyncSession = Depends(get_db)):
    result = await db.execute(stmt)  # FAILS - get_db returns sync session
```

---

## Production Deployment (Railway)

### Required Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection | Auto-set by Railway |
| `AUTH_JWT_SECRET_KEY` | JWT signing key | **YES - CRITICAL** |
| `DEFAULT_ADMIN_PASSWORD` | admin@ibew46.com password | YES |
| `IP2A_ENV` | Environment (`prod`) | Recommended |
| `RUN_PRODUCTION_SEED` | One-time seed flag | Set to `false` after initial |

### Generate JWT Secret Key
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Common Deployment Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Container restart loop | `RUN_PRODUCTION_SEED=true` | Set to `false` |
| "Signature verification failed" | `AUTH_JWT_SECRET_KEY` not set | Add the env var |
| Users can't log in | Old browser cookies | Cookies now auto-clear on invalid token |
| Health check fails | Production seed error (KeyError) | Ensure latest code deployed |
| passlib errors | Bcrypt compatibility | Code uses direct bcrypt now |
| Enum value errors | Old seed data | Update to current enum values |
| Reports page 500 error | `category.items` dict conflict (Bug #013) | Fixed in `013cf92` |
| SQLAlchemy cartesian product warning | Count query with selectinload (Bug #014) | Fixed in `013cf92` |
| Truncate transaction abort | Missing table aborts transaction (Bug #018) | Fixed with SAVEPOINTs in `ca54c6a` |
| StudentStatus.GRADUATED error | Wrong enum value in seed (Bug #017) | Use COMPLETED not GRADUATED |
| Migration is_system_role NOT NULL | Raw SQL INSERT missing column (Bug #020) | Fixed in `8916563` |
| MemberClassification.JOURNEYMAN_WIREMAN error | Service used non-existent enum values (Bug #021) | Fixed in `70df236` |
| HTMX 401 errors show generic message | Missing status-specific error handling (Bug #022) | Fixed in `8564840` |
| bcrypt `__about__` AttributeError | bcrypt 4.1.x incompatible with passlib (Bug #023) | Pin bcrypt>=4.0.1 |
| Reports 500 error (async/sync mismatch) | Router used `await` with sync Session (Bug #024) | Fixed in `9543c5b` |
| Setup users have no roles | Role assignment failed silently (Bug #025) | Fixed in `2f16502` |

**Note:** As of commit `013cf92`, invalid JWT cookies are automatically cleared on redirect to login, preventing repeated "Signature verification failed" log spam.

### Production Seed Data Counts

The expanded production seed (18 steps) creates:
- **1000** Members
- **500** Students
- **100** Organizations
- **75** Instructors
- **10** Grants
- **200** Expenses
- **15** Cohorts
- **1500** Instructor hour entries (20 per instructor)
- **1000** Tools issued (2 per student)
- **1000** Credentials (2 per student)
- **500** JATC applications (1 per student)
- Plus: Training enrollments, union ops (SALTing, Benevolence, Grievances), dues

### Production Seed Technical Notes

**Truncate Safety (Bug #018 fix):**
The `truncate_all.py` uses PostgreSQL SAVEPOINTs to handle missing tables gracefully:
- Each table truncation is wrapped in a SAVEPOINT
- If a table doesn't exist, the savepoint is rolled back
- Subsequent tables can still be truncated
- Missing tables are logged and skipped

**Seed Idempotency:**
- Seed clears ALL data before inserting (via `truncate_all_tables()`)
- Running seed multiple times produces the same result
- Auth seed checks for existing roles/admin before creating
- Set `RUN_PRODUCTION_SEED=false` after initial seed to prevent re-runs

### Documents Feature Status

The Documents feature is currently disabled with a "Feature not implemented" placeholder page. This feature requires S3/MinIO configuration which will be set up in a future deployment phase. See Bug #016 for details.

### Documentation
- Deployment instructions: `docs/instructions/deployment_instructions/`
- Bugs encountered: `docs/BUGS_LOG.md` (Bugs #006-#019)
- Session log: `docs/reports/session-logs/2026-01-30-deployment-session.md`

---

## Branching Strategy (January 30, 2026)

**IMPORTANT:** As of January 30, 2026, development occurs on the `develop` branch.

### Branch Overview

| Branch | Purpose | Status | Auto-Deploy |
|--------|---------|--------|-------------|
| `main` | Demo/Production | Stable (needs update from develop) | Railway |
| `develop` | Active development | v0.9.4-alpha (FEATURE-COMPLETE) | None (local only) |

**Current Action:** Merge `develop → main` to deploy v0.9.4-alpha feature-complete build to Railway.

**Why Separate Branches:**
- `main` is the production branch deployed to Railway
- `develop` allows continued development without affecting demo
- Merge `develop → main` only when ready to update production
- Protects production from showing half-finished features

### Branch Commands

```bash
# Switch to develop (for all development work)
git checkout develop
git pull origin develop

# Merge develop to main (when ready to update demo)
git checkout main
git pull origin main
git merge develop
git push origin main
```

---

## Session Workflow

### Starting a Session
1. `git checkout develop` (ALWAYS work on develop branch)
2. `git pull origin develop`
3. `docker-compose up -d`
4. `pytest -v --tb=short` (verify green)
5. Check instruction document for current tasks

### During Session
- Commit incrementally
- Run tests after significant changes
- Update CHANGELOG.md
- **Stay on develop branch**

### Ending a Session
1. `pytest -v` (verify green)
2. `git status` (check for uncommitted changes)
3. Commit with conventional commit message
4. `git push origin develop` (push to develop, NOT main)
5. Note any blockers or next steps
6. **⚠️ MANDATORY: End-of-session documentation update (see below)**

### 📝 End-of-Session Documentation (MANDATORY — DO NOT SKIP)

> Update *ANY* and *ALL* relevant documents to capture progress made this session.
> Scan `/docs/*` and make or create any relevant updates/documents to keep a
> historical record as the project progresses. Do not forget about ADRs —
> update as necessary.

**Before closing the session:**
1. **Scan `/docs/*`** — Review all documentation files
2. **Update existing docs** — Reflect changes, progress, and decisions
3. **Create new docs** — If needed for new components or concepts
4. **ADR Review** — Update or create Architecture Decision Records as necessary
5. **Session log entry** — Record what was accomplished in `docs/reports/session-logs/`
6. **CHANGELOG.md** — Add entries for work completed
7. **CLAUDE.md** — Update current state if significant progress made

This ensures historical record-keeping and project continuity ("bus factor" protection).
See `docs/standards/END_OF_SESSION_DOCUMENTATION.md` for full checklist.

---

## Claude.ai Sync Schedule

### When to Update Claude.ai

**Update immediately when:**
- Major phase complete
- Critical decisions needed
- Blockers encountered

**Update weekly for:**
- Progress report
- Planning sessions

### What to Share

**For syncs, share:**
- Latest session summary from `docs/reports/session-logs/`
- List of completed tasks
- Outstanding questions/decisions needed
- Blockers or risks identified

---

## Documentation Standardization (January 30, 2026)

**Objective:** Standardize documentation practices across all instruction documents to ensure consistent historical record-keeping

### Work Completed

| Task | Status |
|------|--------|
| Added mandatory "End-of-Session Documentation" section to all instruction documents | Done |
| Updated 55 instruction documents with standardized documentation reminders | Done |
| Created ADR-013: Stripe Payment Integration | Done |
| Updated ADR README index | Done |

### Files Updated

**Instruction Documents (55 total):**
- 10 MASTER instruction files
- 32 session-specific instruction files
- 6 Week 1 instruction files
- 6 deployment instruction files
- 1 instruction template

**New ADR:**
- [ADR-013-stripe-payment-integration.md](docs/decisions/ADR-013-stripe-payment-integration.md)

### Standardized Documentation Section

All instruction documents now include this mandatory end-of-session reminder:

```markdown
## 📝 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session.

### Before Ending This Session:

1. **Scan `/docs/*`** - Review all documentation files
2. **Update existing docs** - Reflect changes, progress, and decisions
3. **Create new docs** - If needed for new components or concepts
4. **ADR Review** - Update or create Architecture Decision Records as necessary
5. **Session log entry** - Record what was accomplished

This ensures historical record-keeping and project continuity ("bus factor" protection).
```

---

## Stripe Payment Integration (January 30, 2026)

**Status:** ✅ **FULLY COMPLETE** - All 3 phases implemented (Backend + Database + Frontend)

### Overview

Stripe integration enables online dues payment for IBEW Local 46 members. Decision documented in [ADR-013](docs/decisions/ADR-013-stripe-payment-integration.md).

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| **Stripe over Square** | Better developer experience, superior subscription support, ACH support |
| **Checkout Sessions** | PCI compliance stays with Stripe, simpler integration |
| **Payment Methods** | Credit/debit cards (2.9% + $0.30), ACH bank transfers (0.8%, $5 cap) |
| **Webhook Verification** | Never trust redirects alone, always verify via webhook signature |

### Implementation Status

**Phase 1: Backend (Completed January 30, 2026)**

| Component | Status | Location |
|-----------|--------|----------|
| PaymentService | ✅ Complete | `src/services/payment_service.py` |
| Stripe Webhook Handler | ✅ Complete | `src/routers/webhooks/stripe_webhook.py` |
| Settings Configuration | ✅ Complete | `src/config/settings.py` |
| Environment Variables | ✅ Complete | `.env.example` |
| Requirements | ✅ Complete | `requirements.txt` (stripe>=8.0.0) |
| Router Registration | ✅ Complete | `src/main.py` |

**Phase 2: Database & Testing (Completed January 30, 2026)**

| Component | Status | Location |
|-----------|--------|----------|
| Member.stripe_customer_id field | ✅ Complete | Migration `f1a2b3c4d5e6`, `src/models/member.py` |
| DuesPaymentMethod enum updates | ✅ Complete | Migration `g2b3c4d5e6f7`, `src/db/enums/dues_enums.py` |
| Member schema updated | ✅ Complete | `src/schemas/member.py` |
| Integration tests | ✅ Complete | `src/tests/test_stripe_integration.py` (11 tests) |

**Phase 3: Frontend Payment Flow (Completed January 30, 2026)**

| Component | Status | Location |
|-----------|--------|----------|
| Payment initiation endpoint | ✅ Complete | `src/routers/dues_frontend.py::initiate_payment` |
| Success page | ✅ Complete | `src/templates/dues/payments/success.html` |
| Cancel page | ✅ Complete | `src/templates/dues/payments/cancel.html` |
| "Pay Now" button (member payments) | ✅ Complete | `src/templates/dues/payments/member.html` |
| Rate lookup service | ✅ Complete | `src/services/dues_frontend_service.py::get_rate_for_member` |
| Payment method display | ✅ Complete | Stripe methods added to display names |
| Frontend tests | ✅ Complete | `src/tests/test_stripe_frontend.py` (14 tests) |

### Environment Variables Needed

```bash
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
```

### Database Changes Required

```sql
ALTER TABLE members ADD COLUMN stripe_customer_id VARCHAR(100) UNIQUE;

-- DuesPayment payment_method enum needs:
-- 'stripe_card', 'stripe_ach'
```

### Integration Flow

```
Member → "Pay Dues" button → Backend creates Checkout Session
                          → Redirect to Stripe hosted page
                          → Member pays
                          → Stripe webhook fires
                          → Backend records payment in DuesPayment table
```

### Test Mode Setup

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Forward webhooks to local dev
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe

# Trigger test events
stripe trigger checkout.session.completed
```

**Test Cards:**
- Success: 4242 4242 4242 4242
- Decline: 4000 0000 0000 0002
- 3D Secure: 4000 0000 0000 3220

### Future Enhancements

- Phase 1: One-time payments (use `mode='payment'`)
- Phase 2: Recurring subscriptions (use `mode='subscription'`)
- Phase 3: Payment plans for large balances
- Phase 4: Stripe Customer Portal for member self-service
- Phase 5: QuickBooks integration for accounting sync

**Reference:** See [docs/instructions/stripe/CONTINUITY_STRIPE_UPDATED.md](docs/instructions/stripe/CONTINUITY_STRIPE_UPDATED.md) for full implementation guide.

---

## Week 11 Session A: Audit Infrastructure (January 30, 2026)

**Status:** ✅ **COMPLETE** - NLRA compliance audit infrastructure implemented

### Overview

Implements critical audit infrastructure for NLRA compliance, including database-level immutability for audit logs and staff notes functionality.

**Instruction Documents:** `docs/instructions/week11–stripe/WEEK11_SESSION_A_AUDIT_INFRASTRUCTURE.md`

### Implementation Status

**Task 1: Audit Log Immutability (Completed January 30, 2026)**

| Component | Status | Location |
|-----------|--------|----------|
| Immutability trigger migration | ✅ Complete | Migration `h3c4d5e6f7g8` |
| prevent_audit_modification() function | ✅ Complete | PostgreSQL trigger function |
| UPDATE trigger | ✅ Complete | Blocks all UPDATE operations on audit_logs |
| DELETE trigger | ✅ Complete | Blocks all DELETE operations on audit_logs |
| Immutability tests | ✅ Complete | `src/tests/test_audit_immutability.py` (4 tests) |

**Task 2: Member Notes Table (Completed January 30, 2026)**

| Component | Status | Location |
|-----------|--------|----------|
| MemberNote model | ✅ Complete | `src/models/member_note.py` |
| NoteVisibility levels | ✅ Complete | staff_only, officers, all_authorized |
| Member relationship | ✅ Complete | `src/models/member.py` notes relationship |
| Pydantic schemas | ✅ Complete | `src/schemas/member_note.py` |
| Database migration | ✅ Complete | Migration `i4d5e6f7g8h9` |
| AUDITED_TABLES update | ✅ Complete | Added member_notes to audit service |

**Task 3-4: Service & Router (Completed January 30, 2026)**

| Component | Status | Location |
|-----------|--------|----------|
| MemberNoteService | ✅ Complete | `src/services/member_note_service.py` |
| CRUD operations | ✅ Complete | create, get_by_id, get_by_member, update, soft_delete |
| Role-based visibility filtering | ✅ Complete | Admin/Officer/Staff permission levels |
| Audit integration | ✅ Complete | All operations logged via audit_service |
| Member notes router | ✅ Complete | `src/routers/member_notes.py` |
| Router registration | ✅ Complete | Registered in `src/main.py` at /api/v1/member-notes |

**Task 5: Tests (Completed January 30, 2026)**

| Component | Status | Coverage |
|-----------|--------|----------|
| Model tests | ✅ Complete | 2 tests |
| Service tests | ✅ Complete | 6 tests |
| API tests | ✅ Complete | 7 tests |
| Total | ✅ Complete | 15 tests + 4 immutability tests = 19 new tests |

### NLRA Compliance Features

- **Audit Log Immutability**: PostgreSQL triggers prevent any modification or deletion of audit records (7-year retention required)
- **Automatic Auditing**: All member_notes operations automatically logged
- **Role-Based Access**: Three visibility levels control who can view sensitive notes
- **Soft Delete**: Notes are never hard-deleted, preserving audit trail

### Files Created

```
src/models/member_note.py
src/schemas/member_note.py
src/services/member_note_service.py
src/routers/member_notes.py
src/tests/test_member_notes.py
src/tests/test_audit_immutability.py
src/db/migrations/versions/h3c4d5e6f7g8_add_audit_logs_immutability_trigger.py
src/db/migrations/versions/i4d5e6f7g8h9_create_member_notes_table.py
```

### Files Modified

```
src/models/member.py                 # Added notes relationship
src/services/audit_service.py        # Added member_notes to AUDITED_TABLES
src/main.py                          # Registered member_notes router
```

---

## Week 11 Session B: Audit UI & Role Permissions (January 31, 2026)

**Status:** ✅ **COMPLETE** - Audit log viewer with role-based access and field redaction

### Overview

Implements audit log viewer UI with role-based permissions and sensitive field redaction. Staff can view audit history filtered by permission level, with automatic masking for non-admin users.

**Instruction Documents:** `docs/instructions/week12_istructions/WEEK11_SESSION_B_AUDIT_UI.md`

### Implementation Status

**Files Created:**
```
src/core/permissions.py
src/services/audit_frontend_service.py
src/routers/audit_frontend.py
src/templates/admin/audit_logs.html
src/templates/admin/audit_detail.html
src/templates/admin/partials/_audit_table.html
src/templates/components/_audit_history.html
src/tests/test_audit_frontend.py
```

**Files Modified:**
```
src/main.py                              # Registered audit_frontend router
src/templates/components/_sidebar.html   # Added Audit Logs link (admin/officer only)
src/routers/dependencies/auth_cookie.py  # Added get_current_user_model dependency
src/tests/conftest.py                    # Added test_user, auth_headers, test_member fixtures
```

### Key Features

- **Role-Based Permissions**: VIEW_OWN, VIEW_MEMBERS, VIEW_USERS, VIEW_ALL, EXPORT
- **Sensitive Field Redaction**: Non-admin users see [REDACTED] for SSN, passwords, etc.
- **HTMX Filtering**: Filter by table, action, date range, search query
- **CSV Export**: Admin-only export of audit logs
- **Detail View**: Before/after value comparison for updates

---

## Week 11 Session C: Inline History & Member Notes UI (January 31, 2026)

**Status:** ✅ **COMPLETE** - Member notes and audit history inline display

### Overview

Adds inline audit history to entity detail pages and member notes UI. Users see recent activity directly on member pages with HTMX loading.

**Instruction Documents:** `docs/instructions/week12_istructions/WEEK11_SESSION_C_INLINE_HISTORY.md`

### Implementation Status

**Files Created:**
```
src/templates/members/partials/_notes_list.html
src/templates/members/partials/_add_note_modal.html
```

**Files Modified:**
```
src/templates/members/detail.html       # Added Notes and Audit History sections
src/templates/components/_audit_history.html  # Updated to timeline style
src/routers/member_frontend.py          # Added notes GET/POST endpoints
```

### Key Features

- **Inline Audit History**: Timeline display on member detail pages
- **Member Notes**: Add/view/delete with visibility controls
- **HTMX Loading**: Notes and history load asynchronously
- **Visibility Levels**: staff_only, officers, all_authorized
- **Note Categories**: contact, dues, grievance, referral, training, general

---

## Week 12 Session A: User Profile & Settings (January 31, 2026)

**Status:** ✅ **COMPLETE** - Profile management and password change

### Overview

Implements user profile view and password change functionality with audit logging.

**Instruction Documents:** `docs/instructions/week12_istructions/WEEK12_SESSION_A_SETTINGS_PROFILE.md`

### Implementation Status

**Files Created:**
```
src/services/profile_service.py
src/routers/profile_frontend.py
src/templates/profile/index.html
src/templates/profile/change_password.html
```

**Files Modified:**
```
src/main.py  # Registered profile_frontend router
```

### Key Features

- **Profile View**: Display user info, roles, and activity summary
- **Password Change**: Secure password update with current password verification
- **Activity Tracking**: Show user's actions from audit logs (past 7 days)
- **Password Validation**: Minimum 8 characters, must be different from current
- **Audit Logging**: Password changes logged without exposing actual passwords

---

## Phase 6 Week 4 Files Created/Modified

### New Files
```
src/services/
└── training_frontend_service.py   # Training stats and queries

src/routers/
└── training_frontend.py           # Training page routes

src/templates/training/
├── index.html                     # Landing page
├── students/
│   ├── index.html                 # Student list
│   ├── detail.html                # Student detail
│   └── partials/
│       ├── _table.html
│       └── _row.html
└── courses/
    ├── index.html                 # Course cards
    └── detail.html                # Course detail

src/tests/
└── test_training_frontend.py      # 19 tests
```

### Modified Files
```
src/main.py                        # Added training_frontend router
src/templates/components/_sidebar.html  # Training nav already present
```

---

*Welcome to IP2A. Let's build something that lasts.*

---

## Week 11 Session B: Audit UI & Role Permissions (January 31, 2026)

**Status:** ✅ **COMPLETE** - Audit log viewer with role-based access and field redaction

### Overview

Implements audit log viewer UI with role-based permissions and sensitive field redaction. Staff can view audit history filtered by permission level, with automatic masking for non-admin users.

### Key Features

- **Role-Based Permissions**: VIEW_OWN, VIEW_MEMBERS, VIEW_USERS, VIEW_ALL, EXPORT
- **Sensitive Field Redaction**: Non-admin users see [REDACTED] for SSN, passwords, etc.
- **HTMX Filtering**: Filter by table, action, date range, search query
- **CSV Export**: Admin-only export of audit logs

### Files Created

```
src/core/permissions.py
src/services/audit_frontend_service.py
src/routers/audit_frontend.py
src/templates/admin/{audit_logs.html,audit_detail.html}
src/templates/admin/partials/_audit_table.html
src/tests/test_audit_frontend.py
```

---

## Week 11 Session C: Inline History & Member Notes UI (January 31, 2026)

**Status:** ✅ **COMPLETE** - Member notes and audit history inline display

### Overview

Adds inline audit history to entity detail pages and member notes UI. Users see recent activity directly on member pages.

### Key Features

- **Inline Audit History**: Timeline display on member detail pages
- **Member Notes**: Add/view/delete with visibility controls  
- **HTMX Loading**: Notes and history load asynchronously
- **Visibility Levels**: staff_only, officers, all_authorized

### Files Created

```
src/templates/members/partials/{_notes_list.html,_add_note_modal.html}
```

---

## Week 12 Session A: User Profile & Settings (January 31, 2026)

**Status:** ✅ **COMPLETE** - Profile management and password change

### Overview

Implements user profile view and password change functionality with audit logging.

### Key Features

- **Profile View**: Display user info, roles, and activity summary
- **Password Change**: Secure password update with validation
- **Activity Tracking**: Show user's actions from audit logs
- **Audit Logging**: Password changes logged without exposing passwords

### Files Created

```
src/services/profile_service.py
src/routers/profile_frontend.py
src/templates/profile/{index.html,change_password.html}
```

---

## Week 13: IP2A Entity Completion Audit (February 2, 2026)

**Status:** ✅ **COMPLETE** - All IP2A entities verified as existing

### Overview

Audited existing models against original IP2A design requirements. All entities already implemented:

| Entity | Status | Notes |
|--------|--------|-------|
| Location | ✅ Exists | Full address, capacity, contacts, LocationType enum |
| InstructorHours | ✅ Exists | Hours tracking, prep_hours, payroll support |
| ToolsIssued | ✅ Exists | Checkout/return tracking, condition, value |
| Expense | ✅ Exists | Has grant_id FK - serves as GrantExpense |

No new models required. Week 13 instruction document verified feature parity.

---

## Week 14: Grant Module Expansion (February 2, 2026)

**Status:** ✅ **COMPLETE** - Full grant compliance reporting implemented

### Overview

Implements comprehensive grant tracking and compliance reporting for IP2A program funding sources.

### Files Created

```
src/db/enums/grant_enums.py                    # GrantStatus, GrantEnrollmentStatus, GrantOutcome
src/models/grant_enrollment.py                  # Student-to-grant association with outcomes
src/schemas/grant.py                            # Grant-related Pydantic schemas
src/schemas/grant_enrollment.py                 # Enrollment schemas with outcome recording
src/services/grant_metrics_service.py           # Metrics calculation for compliance
src/services/grant_report_service.py            # Report generation (summary, detailed, funder, Excel)
src/routers/grants_frontend.py                  # Frontend routes for grant management
src/templates/grants/index.html                 # Grant dashboard landing page
src/templates/grants/list.html                  # All grants list
src/templates/grants/detail.html                # Grant detail with metrics
src/templates/grants/enrollments.html           # Enrollment management
src/templates/grants/expenses.html              # Expense tracking
src/templates/grants/reports.html               # Report generation page
src/templates/grants/report_summary.html        # Summary report view
src/templates/grants/partials/_enrollments_table.html
src/tests/test_grant_enrollment.py              # Enum, model, schema tests
src/tests/test_grant_services.py                # Service and router tests
src/db/migrations/versions/j5e6f7g8h9i0_*.py    # Migration for grant enhancements
docs/decisions/ADR-014-grant-compliance-reporting.md
```

### Files Modified

```
src/db/enums/__init__.py                        # Export new grant enums
src/models/grant.py                             # Added status, targets, enrollments relationship
src/models/student.py                           # Added grant_enrollments relationship
src/models/__init__.py                          # Export GrantEnrollment
src/schemas/__init__.py                         # Export grant schemas
src/main.py                                     # Register grants_frontend router
src/templates/components/_sidebar.html          # Added Grants nav link
```

### Key Features

- **Grant Status Tracking**: Lifecycle states (pending, active, completed, closed, suspended)
- **Target Metrics**: enrollment, completion, placement targets
- **Enrollment Tracking**: Students linked to grants with outcome recording
- **Outcome Types**: Program completion, credential, apprenticeship, employment, education
- **Placement Tracking**: Employer, date, wage, job title
- **Metrics Calculation**: Retention rate, utilization rate, progress toward targets
- **Report Generation**: Summary, detailed, funder-formatted, Excel export
- **Dashboard UI**: Grant list, detail views, enrollment/expense management

---

## Week 16: Production Hardening & Performance Optimization (February 2, 2026)

**Status:** ✅ **COMPLETE** - Security headers, health checks, monitoring, connection pooling

### Overview

Implements production-grade security and monitoring infrastructure.

### Key Features

- **SecurityHeadersMiddleware**: X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy, CSP, Permissions-Policy
- **Enhanced Health Checks**: /health/live, /health/ready, /health/metrics endpoints
- **Sentry Integration**: Error tracking and performance monitoring (`src/core/monitoring.py`)
- **Structured JSON Logging**: Production logging config (`src/core/logging_config.py`)
- **Connection Pooling**: Configurable DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_TIMEOUT, DB_POOL_RECYCLE
- **New Settings**: SENTRY_DSN, APP_VERSION, ALLOWED_ORIGINS, JSON_LOGS

### Files Created

```
src/core/monitoring.py             # Sentry integration
src/core/logging_config.py         # Structured JSON logging
src/middleware/security_headers.py  # SecurityHeadersMiddleware
src/routers/health.py              # Enhanced health check endpoints
src/tests/test_security_headers.py # 12 tests
src/tests/test_health_checks.py    # 10 tests
src/tests/test_rate_limiting.py    # 10 tests
```

**Version:** v0.9.1-alpha (32 new tests)

---

## Week 17: Post-Launch Operations & Maintenance (February 2, 2026)

**Status:** ✅ **COMPLETE** - Backup scripts, archival, admin metrics dashboard

### Key Features

- **Backup Scripts**: `scripts/backup_database.sh`, `scripts/verify_backup.sh`
- **Audit Log Archival**: `scripts/archive_audit_logs.sh`
- **Session Cleanup**: `scripts/cleanup_sessions.sh`
- **Crontab Example**: `scripts/crontab.example` with scheduled tasks
- **Admin Metrics Dashboard**: System health metrics at `/admin/metrics`
- **Incident Response Runbook**: `docs/runbooks/incident-response.md`

### Files Created

```
scripts/backup_database.sh
scripts/verify_backup.sh
scripts/archive_audit_logs.sh
scripts/cleanup_sessions.sh
scripts/crontab.example
src/routers/admin_metrics.py
src/templates/admin/metrics.html
docs/runbooks/incident-response.md
src/tests/test_admin_metrics.py     # 13 tests
```

**Version:** v0.9.2-alpha

---

## Week 18: Mobile Optimization & Progressive Web App (February 2, 2026)

**Status:** ✅ **COMPLETE** - Mobile-responsive CSS, PWA manifest, service worker, offline support

### Key Features

- **Mobile CSS**: Touch-friendly styles with 48x48px minimum touch targets (`src/static/css/mobile.css`)
- **PWA Manifest**: App icons and shortcuts (`src/static/manifest.json`)
- **Service Worker**: Offline support and caching (`src/static/js/sw.js`)
- **Offline Page**: Graceful degradation when device has no connection
- **Mobile Drawer**: Slide-out navigation component
- **Bottom Navigation**: Mobile-friendly bottom nav bar

### Files Created

```
src/static/css/mobile.css
src/static/manifest.json
src/static/js/sw.js
src/templates/offline.html
src/templates/components/_mobile_drawer.html
src/templates/components/_bottom_nav.html
src/tests/test_mobile_pwa.py         # 14 tests
```

### Files Modified

```
src/templates/base.html               # PWA meta tags, service worker registration
src/routers/frontend.py               # Added /offline route
```

**Version:** v0.9.3-alpha

---

## Week 19: Advanced Analytics Dashboard & Report Builder (February 2, 2026)

**Status:** ✅ **COMPLETE** - Executive analytics, membership trends, dues analytics, custom report builder

### Key Features

- **AnalyticsService**: Membership stats, trends, dues analytics, training metrics, activity tracking
- **ReportBuilderService**: Custom report generation with CSV/Excel export, dynamic field selection, status filtering
- **Executive Dashboard**: Key metrics with Chart.js integration for membership trends and payment method charts
- **Membership Analytics**: 24-month trend chart and data table
- **Dues Analytics**: Collection stats and delinquency reporting
- **Custom Report Builder**: Dynamic field selection and export
- **Role Checking**: Officer-level access required for analytics

### Files Created

```
src/services/analytics_service.py
src/services/report_builder_service.py
src/routers/analytics_frontend.py
src/templates/analytics/dashboard.html
src/templates/analytics/membership.html
src/templates/analytics/dues.html
src/templates/analytics/report_builder.html
src/tests/test_analytics.py            # 19 tests
```

### Files Modified

```
src/main.py                            # Registered analytics_frontend router
src/templates/components/_sidebar.html  # Added Analytics nav link
```

**Version:** v0.9.4-alpha (FEATURE-COMPLETE for Weeks 1-19)

---

## Phase 7: Referral & Dispatch System (IN PROGRESS)

**Status:** 🚧 **WEEKS 20-27 COMPLETE** — Backend + Frontend Books & Dispatch UI (Models, Services, API, Frontend)
**Effort Estimate:** 100-150 hours across 7 sub-phases (7a–7g)
**Documentation:** `docs/phase7/` — 8+ planning documents

### Overview

Phase 7 implements the out-of-work referral and dispatch system for IBEW Local 46, replacing LaborPower with a modern, auditable system built on verified data structures. This is the largest remaining phase — 12 new database tables, 14 business rules, and ~78 reports to achieve LaborPower report parity.

### Weeks 20-22 Implementation (February 4, 2026)

**Week 20: Schema Foundation**

| Session | Focus | Status |
|---------|-------|--------|
| 20A | Schema Reconciliation & Enums | ✅ Complete |
| 20B | ReferralBook Model & Seeds | ✅ Complete |
| 20C | BookRegistration Model | ✅ Complete |

**Week 21: Core Models**

| Session | Focus | Status |
|---------|-------|--------|
| 21A | LaborRequest & JobBid Models | ✅ Complete |
| 21B | Dispatch Model | ✅ Complete |
| 21C | RegistrationActivity Model | ✅ Complete |

**Week 22: Services**

| Session | Focus | Status |
|---------|-------|--------|
| 22A | ReferralBookService | ✅ Complete |
| 22B | BookRegistrationService Core | ✅ Complete |
| 22C | Check Mark Logic & Roll-Off Rules | ✅ Complete |

### Weeks 23-25 Implementation (February 4, 2026)

**Week 23: Dispatch Services**

| Session | Focus | Status |
|---------|-------|--------|
| 23A | LaborRequestService | ✅ Complete |
| 23B | JobBidService | ✅ Complete |
| 23C | DispatchService | ✅ Complete |

**Week 24: Queue Management & Enforcement**

| Session | Focus | Status |
|---------|-------|--------|
| 24A | QueueService Core | ✅ Complete |
| 24B | EnforcementService | ✅ Complete |
| 24C | Analytics & Integration | ✅ Complete |

**Week 25: API Endpoints**

| Session | Focus | Status |
|---------|-------|--------|
| 25A | Book & Registration API | ✅ Complete |
| 25B | LaborRequest & Bid API | ✅ Complete |
| 25C | Dispatch & Admin API | ✅ Complete |

### Files Created (Weeks 23-25)

```
src/services/
├── labor_request_service.py         # Rules 2,3,4,11: Request lifecycle, cutoff, ordering
├── job_bid_service.py               # Rule 8: Bidding window, suspension tracking
├── dispatch_service.py              # Rules 9,12,13: Core dispatch, termination, by-name
├── queue_service.py                 # Queue snapshots, next-eligible, wait estimation
└── enforcement_service.py           # Batch processing: re-sign, expired cleanup

src/routers/
├── referral_books_api.py            # ~12 endpoints: Book CRUD, stats, settings
├── registration_api.py              # ~12 endpoints: Registration, re-sign, resign
├── labor_request_api.py             # ~12 endpoints: Request CRUD, fulfillment
├── job_bid_api.py                   # ~10 endpoints: Bid submission, acceptance
└── dispatch_api.py                  # ~16 endpoints: Dispatch, queue, enforcement
```

### Files Modified (Weeks 23-25)

```
src/main.py                          # Registered 5 Phase 7 API routers, version 0.9.6-alpha
```

### Weeks 26-27 Implementation (February 4, 2026)

**Week 26: Books & Registration UI**

| Task | Status |
|------|--------|
| ReferralFrontendService | ✅ Complete |
| Referral landing page with stats | ✅ Complete |
| Books list with HTMX filtering | ✅ Complete |
| Book detail with queue table | ✅ Complete |
| Registration list (cross-book) | ✅ Complete |
| Registration detail with history | ✅ Complete |
| 8 HTMX partials | ✅ Complete |
| Register/re-sign/resign modals | ✅ Complete |
| 22 frontend tests | ✅ Complete |

**Week 27: Dispatch Workflow UI**

| Task | Status |
|------|--------|
| DispatchFrontendService (time-aware) | ✅ Complete |
| Dispatch dashboard with live stats | ✅ Complete |
| Labor request list | ✅ Complete |
| Morning referral page | ✅ Complete |
| Active dispatches page | ✅ Complete |
| Queue management with book tabs | ✅ Complete |
| Enforcement dashboard | ✅ Complete |
| 7 HTMX partials | ✅ Complete |
| 29 frontend tests | ✅ Complete |

### Files Created (Weeks 26-27)

```
src/services/
├── referral_frontend_service.py         # Frontend wrapper for book/registration data
└── dispatch_frontend_service.py         # Time-aware dispatch workflow service

src/routers/
├── referral_frontend.py                 # 17 routes (books, registrations, partials)
└── dispatch_frontend.py                 # 11 routes (dashboard, requests, queue, enforcement)

src/templates/referral/
├── landing.html                         # Overview with stats cards
├── books.html                           # Books list with filters
├── book_detail.html                     # Book detail with queue
├── registrations.html                   # Cross-book registration list
└── registration_detail.html             # Single registration view

src/templates/dispatch/
├── dashboard.html                       # Daily dispatch operations dashboard
├── requests.html                        # Labor request list
├── morning_referral.html                # Bid queue processing (critical daily page)
├── active.html                          # Active dispatches with short call tracking
├── queue.html                           # Queue positions by book
└── enforcement.html                     # Suspensions and violations

src/templates/partials/referral/
├── _stats.html                          # Stats cards
├── _books_overview.html                 # Books grid
├── _books_table.html                    # Filterable books table
├── _queue_table.html                    # Members on book
├── _registrations_table.html            # Registration list
├── _register_modal.html                 # Register form
├── _re_sign_modal.html                  # Re-sign confirmation
└── _resign_modal.html                   # Resign confirmation

src/templates/partials/dispatch/
├── _stats_cards.html                    # Dashboard stats (auto-refresh 60s)
├── _activity_feed.html                  # Today's activity (auto-refresh 30s)
├── _pending_requests.html               # Unfilled requests cards
├── _bid_queue.html                      # Morning referral bids
├── _queue_table.html                    # Queue by book
├── _request_table.html                  # Request list with pagination
└── _dispatch_table.html                 # Active/completed dispatches

src/tests/
├── test_referral_frontend.py            # 22 tests (Week 26)
└── test_dispatch_frontend.py            # 29 tests (Week 27)

docs/phase7/
├── week26_api_discovery.md              # Backend API documentation
└── week27_api_discovery.md              # Dispatch API documentation
```

### Files Modified (Weeks 26-27)

```
src/main.py                              # Registered referral_frontend + dispatch_frontend routers
src/templates/components/_sidebar.html   # Added Referral & Dispatch section
CHANGELOG.md                             # Added v0.9.7-alpha and v0.9.8-alpha entries
```

### Business Rules Surfaced in UI (Weeks 26-27)

| Rule | UI Location | Visual Indicator |
|------|-------------|------------------|
| Rule 2 | Morning Referral page | Bid queue sorted by position |
| Rule 3 | Dashboard + Morning Referral | Warning banner after 3 PM |
| Rule 4 | Request Detail → Candidates | Agreement type badge |
| Rule 8 | Dashboard | Bidding window status badge |
| Rule 9 | Active Dispatches | "Short Call" badge + day counter |
| Rule 11 | Request Detail → Candidates | Check mark icons |
| Rule 12 | Enforcement Dashboard | Blackout section |
| Rule 13 | Request Detail | By-name warning banner |

### Business Rules Implemented (Weeks 23-25)

| Rule | Implementation | Service |
|------|---------------|---------|
| Rule 2 | Morning referral processing order | LaborRequestService |
| Rule 3 | 3 PM cutoff for next morning dispatch | LaborRequestService |
| Rule 4 | Agreement type filtering (PLA/CWA/TERO) | LaborRequestService |
| Rule 8 | 5:30 PM–7:00 AM bidding window, 2 rejection = 1-year suspension | JobBidService |
| Rule 9 | Short call ≤10 days, position restoration | DispatchService |
| Rule 11 | Check mark determination (specialty, MOU, early start) | LaborRequestService |
| Rule 12 | Quit/discharge = all-books rolloff + 2-week blackout | DispatchService |
| Rule 13 | By-name anti-collusion enforcement | DispatchService |

### Files Created (Weeks 20-22)

```
docs/phase7/
└── PHASE7_SCHEMA_DECISIONS.md          # 5 pre-implementation decisions

src/db/enums/
└── phase7_enums.py                      # 19 Phase 7 enums (BookClassification, RegistrationStatus, etc.)

src/models/
├── referral_book.py                     # ReferralBook model
├── book_registration.py                 # BookRegistration model (APN as DECIMAL)
├── registration_activity.py             # Append-only audit trail
├── labor_request.py                     # Employer job request model
├── job_bid.py                           # Member bid tracking
└── dispatch.py                          # Central dispatch record

src/schemas/
├── referral_book.py                     # ReferralBook Pydantic schemas
├── book_registration.py                 # BookRegistration schemas + QueuePosition
├── registration_activity.py             # Activity schemas
├── labor_request.py                     # LaborRequest schemas
├── job_bid.py                           # JobBid schemas
└── dispatch.py                          # Dispatch schemas

src/services/
├── referral_book_service.py             # Book CRUD, stats, settings
└── book_registration_service.py         # Registration, check marks, roll-off logic

src/seed/
└── phase7_seed.py                       # Seeds 11 referral books

src/tests/
└── test_phase7_models.py                # Model and enum tests (20+ tests)
```

### Files Modified (Weeks 20-22)

```
src/db/enums/__init__.py                 # Export Phase 7 enums
src/models/__init__.py                   # Export Phase 7 models
src/models/member.py                     # Added book_registrations relationship
src/schemas/__init__.py                  # Export Phase 7 schemas
```

### Key Schema Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Separate JobBid model** | Cleaner audit trail, supports rejection tracking for 1-year suspension |
| 2 | **MemberTransaction independent** | Separates financial transactions from dues payments |
| 3 | **Per-book exempt status** | Exempt on BookRegistration, not Member (more flexible) |
| 4 | **Field naming standardized** | `registration_number` (APN), `referral_start_time`, etc. |
| 5 | **Dual audit pattern** | Both RegistrationActivity AND audit_logs for NLRA compliance |

### Phase 7 Enums Implemented (19)

`BookClassification`, `BookRegion`, `RegistrationStatus`, `RegistrationAction`, `ExemptReason`, `RolloffReason`, `NoCheckMarkReason`, `LaborRequestStatus`, `BidStatus`, `DispatchMethod`, `DispatchStatus`, `DispatchType`, `TermReason`, `JobClass`, `MemberType`, `ReferralStatus`, `ActivityCode`, `PaymentSource`, `AgreementType`

### Business Rules Implemented in Services

- **30-day re-sign cycle** with automated reminder queries
- **3 check marks = roll-off** with per-book tracking
- **Exempt status** (7 reason types: military, medical, union_business, salting, jury_duty, training, other)
- **Short call position restoration** (max 2 per cycle)
- **FIFO queue ordering** by APN (DECIMAL(10,2))

### Data Analysis Status

Two batches of production data analyzed from LaborPower Custom Reports module:

| Batch | Date | Files | Contents |
|-------|------|-------|----------|
| Batch 1 | Feb 2, 2026 | 12 | Wire SEA/BREM/PA + Technician + Utility Worker reg lists; 7 employer lists |
| Batch 2 | Feb 2, 2026 | 12 | STOCKMAN + TRADESHOW + TERO APPR WIRE + Technician + Utility Worker; 7 employer lists (+ RESIDENTIAL discovery) |
| **Total** | | **24 files** | 4,033 registrations across 8 books; ~843 unique employers across 8 contract codes |

Analysis documents:
- `LaborPower_Data_Analysis_Schema_Guidance_1.docx` — Volume 1 (Batch 1)
- `LaborPower_Data_Analysis_Schema_Guidance_2.docx` — Volume 2 (Batch 2 + schema corrections)
- `UnionCore_Continuity_Document_Consolidated.md` — Master reference merging both volumes

### Critical Schema Findings (8)

| # | Finding | Severity |
|---|---------|----------|
| 1 | **APN = DECIMAL(10,2), NOT INTEGER** — Integer part is Excel serial date, decimal is secondary sort key (.23–.91). INTEGER destroys dispatch ordering. | 🔴 Critical |
| 2 | **Duplicate APNs within books** — Cannot use APN as unique key. Must use UNIQUE(member_id, book_id, book_priority_number). | 🔴 Critical |
| 3 | **RESIDENTIAL = 8th contract code** — 259 employers, 80% also WIREPERSON, 52 residential-only shops. Missing from all prior docs. | 🟡 High |
| 4 | **Book Name ≠ Contract Code** — STOCKMAN book → STOCKPERSON contract. TECHNICIAN/TRADESHOW/UTILITY WORKER have NO matching contract code. Schema must separate book_name, classification, and contract_code. | 🔴 Critical |
| 5 | **TERO APPR WIRE = compound book** — Encodes agreement_type (TERO) + work_level (APPRENTICE) + classification (WIRE). Needs `agreement_type`, `work_level`, `book_type` columns on `referral_books`. | 🟡 High |
| 6 | **Cross-regional registration** — 87% of Wire Book 1 on ALL THREE regional books. registrations table will have ~3× rows vs unique Wire members. | 🟢 Medium |
| 7 | **APN 45880.41 on FOUR books** — One member on Technician, TERO Appr Wire, Tradeshow, Utility Worker simultaneously. Validates many-to-many model. | 🟢 Medium |
| 8 | **Inverted tier distributions** — STOCKMAN Book 3 = 8.6× Book 1; TECHNICIAN Book 3 > Book 1. Strengthens "Book 3 = Travelers" hypothesis. | 🟢 Medium |

### Known Books (11)

| Book Name | Classification | Region | Contract Code | Agreement | Work Level |
|-----------|---------------|--------|---------------|-----------|------------|
| WIRE SEATTLE | Wire | Seattle | WIREPERSON | Standard | Journeyman |
| WIRE BREMERTON | Wire | Bremerton | WIREPERSON | Standard | Journeyman |
| WIRE PT ANGELES | Wire | Pt. Angeles | WIREPERSON | Standard | Journeyman |
| TECHNICIAN | Technician | Jurisdiction-wide | *(unknown)* | Standard | Journeyman |
| UTILITY WORKER | Utility Worker | Jurisdiction-wide | *(unknown)* | Standard | Journeyman |
| STOCKMAN | Stockman | Jurisdiction-wide | STOCKPERSON | Standard | Journeyman |
| TRADESHOW | Tradeshow | Jurisdiction-wide | *(none — supplemental)* | Standard | Journeyman |
| TERO APPR WIRE | Wire | *(unknown)* | *(WIREPERSON?)* | **TERO** | **Apprentice** |
| *(implied)* SOUND & COMM | Sound & Comm | *(unknown)* | SOUND & COMM | Standard | Journeyman |
| *(implied)* LT FXT MAINT | Lt. Fixture Maint. | *(unknown)* | LT FXT MAINT | Standard | Journeyman |
| *(implied)* MARINE | Marine | *(unknown)* | GROUP MARINE | Standard | Journeyman |

**Employer Contract Codes (8 confirmed):** WIREPERSON, SOUND & COMM, STOCKPERSON, LT FXT MAINT, GROUP MARINE, GROUP TV & APPL, MARKET RECOVERY, RESIDENTIAL

### Business Rules (14)

Source: "IBEW Local 46 Referral Procedures" — Effective October 4, 2024

| # | Rule | System Impact |
|---|------|---------------|
| 1 | Office Hours & Regions | Region entities with operating parameters |
| 2 | Morning Referral Processing Order | Wire 8:30 AM → S&C/Marine/Stock/LFM/Residential 9:00 AM → Tradeshow 9:30 AM |
| 3 | Labor Request Cutoff | Employer requests by 3 PM for next morning; web bids after 5:30 PM |
| 4 | Agreement Types (PLA/CWA/TERO) | `agreement_type` on job_requests AND referral_books |
| 5 | Registration Rules | One per classification per member |
| 6 | Re-Registration Triggers | Short call termination, under scale, 90-day rule, turnarounds |
| 7 | Re-Sign 30-Day Cycle | Automated alert/drop logic |
| 8 | Internet/Email Bidding | 5:30 PM – 7:00 AM window; 2nd rejection = lose privileges 1 year |
| 9 | Short Calls | ≤10 business days; max 2 per cycle; ≤3 days don't count |
| 10 | Check Marks (Penalty) | 2 allowed, 3rd = rolled off that book. Separate per area book |
| 11 | No Check Mark Exceptions | Specialty skills, MOU sites, early starts, under scale, short calls |
| 12 | Quit or Discharge | Rolled off ALL books; 2-week foreperson-by-name blackout |
| 13 | Foreperson By Name | Anti-collusion: cannot be filled by registrants who communicated with employer |
| 14 | Exempt Status | Military, union business, salting, medical, jury duty |

### New Tables (12)

| Table | Purpose |
|-------|---------|
| `referral_books` | Book definitions — name, contract_code (NULLABLE), agreement_type, work_level, book_type |
| `registrations` | Member out-of-work entries — APN as DECIMAL(10,2), status, re-sign tracking |
| `employer_contracts` | Employer-to-contract relationships — 8 contract codes including RESIDENTIAL |
| `job_requests` | Employer labor requests — lifecycle: OPEN→FILLED/CANCELLED/EXPIRED |
| `job_requirements` | Per-request skill/cert requirements (junction table) |
| `dispatches` | Referral transactions — links registration → job_request → member → employer |
| `web_bids` | Internet bidding records — BID/NO_BID/RETRACT actions |
| `check_marks` | Penalty tracking — 2 allowed per book, 3rd = roll-off |
| `member_exemptions` | Exempt status periods — 7 reason types |
| `bidding_infractions` | Bidding privilege violations and revocation periods |
| `worksites` | Physical job locations separate from employer entity |
| `blackout_periods` | Quit/discharge restrictions — per member-employer |

### Schema Corrections Applied (9)

| Item | Original Assumption | Corrected To |
|------|---------------------|--------------|
| APN data type | INTEGER | DECIMAL(10,2) |
| APN field name | position_number | applicant_priority_number |
| Unique constraint | (member_id, book_id) | (member_id, book_id, book_priority_number) |
| Book tier field | Not explicit | book_priority_number INTEGER (1–4) |
| referral_books.contract_code | NOT NULL | **NULLABLE** (Tradeshow, TERO have no contract) |
| referral_books.agreement_type | Not proposed | **NEW:** VARCHAR(20) DEFAULT 'STANDARD' |
| referral_books.work_level | Not proposed | **NEW:** VARCHAR(20) DEFAULT 'JOURNEYMAN' |
| referral_books.book_type | Not proposed | **NEW:** VARCHAR(20) DEFAULT 'PRIMARY' |
| employer_contracts domain | 7 contract codes | **8 codes (+ RESIDENTIAL)** |

### Data Gaps (16)

#### Priority 1 — BLOCKING (before schema DDL)

| # | Gap | How to Resolve |
|---|-----|----------------|
| 1 | REGLIST with member identifiers | LaborPower Custom Report: REGLIST |
| 2 | RAW DISPATCH DATA | LaborPower Custom Report: RAW DISPATCH DATA |
| 3 | EMPLOYCONTRACT report | LaborPower Custom Report: EMPLOYCONTRACT |

#### Priority 2 — IMPORTANT (6 items)
Book catalog confirmation, book-to-contract mapping, sample registration detail, sample dispatch history, TERO/PLA/CWA catalog, duplicate employer resolution strategy.

#### Priority 3 — CLARIFICATION (7 items)
90-day rule definition, "too many days" threshold, total region count, tier semantics, TRADESHOW-specific rules, apprentice book rules, RESIDENTIAL vs WIREPERSON differences.

⚠️ **Do NOT finalize schema DDL or begin migration code until Priority 1 gaps are resolved.**

### Sub-Phases (7a–7g) — 100-150 hrs total

| Sub-Phase | Focus | Hours | Blocked By |
|-----------|-------|-------|------------|
| 7a | Data Collection — 3 Priority 1 exports from LaborPower | 3-5 | ⛔ LaborPower access |
| 7b | Schema Finalization — DDL, Alembic migrations, seed data | 10-15 | 7a |
| 7c | Core Services + API — 14 business rules, CRUD, dispatch logic | 25-35 | 7b |
| 7d | Import Tooling — CSV pipeline: employers → registrations → dispatch | 15-20 | 7b (parallel with 7c) |
| 7e | Frontend UI — book management, dispatch board, web bidding | 20-30 | 7c |
| 7f | Reports P0+P1 — 49 critical/high priority reports | 20-30 | 7c |
| 7g | Reports P2+P3 — 29 medium/low priority reports | 10-15 | 7f |

### LaborPower Report Inventory

~78 de-duplicated reports (91 raw) organized by priority:

| Priority | Count | Examples |
|----------|-------|---------|
| P0 (Critical) | 16 | Out-of-work lists, dispatch logs, employer active list |
| P1 (High) | 33 | Registration history, dispatch summaries, check mark reports |
| P2 (Medium) | 22 | Analytics, trend reports, employer utilization |
| P3 (Low) | 7 | Projections, ad-hoc queries |

Full inventory: `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md`

### ⚠️ Phase 7 Session Reminders

> **Member ≠ Student.** Members are IBEW union members in the referral system. Students are pre-apprenticeship program participants. NEVER conflate. Phase 7 models FK to `members`, NOT `students`.

> **Book ≠ Contract.** Books are out-of-work registration lists. Contracts are collective bargaining agreements. The mapping is NOT 1:1. STOCKMAN book dispatches under STOCKPERSON contract. 3 books have NO contract code.

> **APN = DECIMAL(10,2).** Integer part is Excel serial date. Decimal part (.23–.91) is secondary sort key for same-day dispatch ordering. NEVER truncate to INTEGER.

> **Audit.** `registrations`, `dispatches`, and `check_marks` tables MUST be in AUDITED_TABLES (NLRA 7-year compliance).

### Key Planning Documents

| Document | Location |
|----------|----------|
| **Master reference (Volumes 1+2 merged)** | **`docs/phase7/UnionCore_Continuity_Document_Consolidated.md`** |
| Full implementation plan | `docs/phase7/PHASE7_REFERRAL_DISPATCH_PLAN.md` |
| Technical details (v2) | `docs/phase7/PHASE7_IMPLEMENTATION_PLAN_v2.md` |
| Session continuity doc | `docs/phase7/PHASE7_CONTINUITY_DOC.md` |
| Session continuity addendum | `docs/phase7/PHASE7_CONTINUITY_DOC_ADDENDUM.md` |
| Local 46 referral books | `docs/phase7/LOCAL46_REFERRAL_BOOKS.md` |
| Gap analysis | `docs/phase7/LABORPOWER_GAP_ANALYSIS.md` |
| Reports inventory (78 reports) | `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` |
| Schema Guidance Vol. 1 | `LaborPower_Data_Analysis_Schema_Guidance_1.docx` |
| Schema Guidance Vol. 2 | `LaborPower_Data_Analysis_Schema_Guidance_2.docx` |

---

*Welcome to IP2A. Let's build something that lasts.*

---

**Document Version:** 5.0
**Last Updated:** February 4, 2026
**Previous Version:** 4.0 (February 4, 2026 — Phase 7 Weeks 20-25 detail added)
**Hub/Spoke Model:** Added February 2026
