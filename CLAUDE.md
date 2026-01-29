# IP2A-Database-v2: Project Context Document

**Document Purpose:** Bring Claude (Code or AI) up to speed for development sessions
**Last Updated:** January 29, 2026
**Current Version:** v0.7.5
**Current Phase:** Phase 6 Week 6 - Union Operations (COMPLETE)

---

## TL;DR

**What:** Union operations management system for IBEW Local 46 (Seattle-area electrical workers union)

**Who:** Xerxes - Business Representative by day, solo developer (5-10 hrs/week)

**Where:** Backend COMPLETE. Frontend COMPLETE through Week 6 (Union Operations).

**Stack:** FastAPI + PostgreSQL + SQLAlchemy + Jinja2 + HTMX + DaisyUI

**Status:** 94 frontend tests passing, 259 total tests, ~120 API endpoints, 9 ADRs, Phase 6 Week 6 complete

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

### Frontend Tests: 94 tests

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
| **Testing** | pytest + httpx | 73 frontend tests passing |
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
│   │   └── operations_frontend_service.py  # Union ops (Week 6)
│   ├── routers/                # API endpoints
│   │   ├── dependencies/
│   │   │   ├── auth.py         # Bearer token auth
│   │   │   └── auth_cookie.py  # Cookie-based auth (Week 2)
│   │   ├── staff.py            # Staff management (Week 3)
│   │   ├── training_frontend.py # Training pages (Week 4)
│   │   ├── member_frontend.py   # Member pages (Week 5)
│   │   └── operations_frontend.py  # Union ops (Week 6)
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
│   │   └── errors/
│   ├── static/                 # CSS, JS, images (Phase 6)
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── seed/                   # Seed data
│   └── tests/                  # pytest tests
├── docs/
│   ├── decisions/              # ADRs (001-010)
│   ├── instructions/           # Claude Code instruction docs
│   │   ├── week2_instructions/
│   │   ├── week3_instructions/
│   │   ├── week4_instructions/
│   │   ├── week5_instructions/
│   │   ├── week6_instructions/
│   │   └── infra_phase2_instructions/
│   ├── architecture/           # System docs
│   ├── guides/                 # How-to guides
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

---

## Session Workflow

### Starting a Session
1. `git pull origin main`
2. `docker-compose up -d`
3. `pytest -v --tb=short` (verify green)
4. Check instruction document for current tasks

### During Session
- Commit incrementally
- Run tests after significant changes
- Update CHANGELOG.md

### Ending a Session
1. `pytest -v` (verify green)
2. `git status` (check for uncommitted changes)
3. Commit with conventional commit message
4. `git push origin main`
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
