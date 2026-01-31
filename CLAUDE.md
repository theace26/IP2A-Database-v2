# IP2A-Database-v2: Project Context Document

**Document Purpose:** Bring Claude (Code or AI) up to speed for development sessions
**Last Updated:** January 30, 2026
**Current Version:** v0.8.1-alpha
**Current Phase:** Stripe Integration & Audit Infrastructure Complete

---

## TL;DR

**What:** Union operations management system for IBEW Local 46 (Seattle-area electrical workers union)

**Who:** Xerxes - Business Representative by day, solo developer (5-10 hrs/week)

**Where:** Backend COMPLETE. Frontend FEATURE-COMPLETE. Stripe Payments LIVE. **Deployed to Railway.**

**Stack:** FastAPI + PostgreSQL + SQLAlchemy + Jinja2 + HTMX + DaisyUI + Alpine.js + WeasyPrint + openpyxl + Stripe

**Status:** 200+ frontend tests, ~375 total tests, ~135 API endpoints, 13 ADRs, Railway deployment live, Stripe integration complete

---

## Current State

### Backend: COMPLETE

| Component | Models | Endpoints | Tests | Status |
|-----------|--------|-----------|-------|--------|
| Core (Org, Member, Employment) | 4 | ~20 | 17 | Done |
| Auth (JWT, RBAC, Registration) | 4 | 13 | 52 | Done |
| Union Ops (SALTing, Benevolence, Grievance) | 5 | 27 | 31 | Done |
| Training (Students, Courses, Grades, Certs) | 7 | ~35 | 33 | Done |
| Documents (S3/MinIO) | 1 | 8 | 11 | Done |
| Dues (Rates, Periods, Payments, Adjustments) | 4 | ~35 | 21 | Done |
| **Total** | **25** | **~120** | **165** | Done |

### Frontend: PHASE 6 COMPLETE

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

### Frontend Tests: 167 tests

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
| **Testing** | pytest + httpx | 149 frontend tests passing |
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
│   ├── decisions/              # ADRs (001-011)
│   ├── instructions/           # Claude Code instruction docs
│   │   ├── week2_instructions/
│   │   ├── week3_instructions/
│   │   ├── week4_instructions/
│   │   ├── week5_instructions/
│   │   ├── week6_instructions/
│   │   └── infra_phase2_instructions/
│   ├── architecture/           # System docs
│   ├── guides/                 # How-to guides
│   ├── BUGS_LOG.md             # Historical bugs record
│   └── archive/                # Old documentation
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
| `main` | Demo/Production (FROZEN) | Stable v0.8.0-alpha1 | Railway |
| `develop` | Active development | Current work | None (local only) |

**Why Separate Branches:**
- `main` is frozen for leadership demo on Railway
- `develop` allows continued development without affecting demo
- Merge `develop → main` only when ready to update demo
- Protects demo from showing half-finished features

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
