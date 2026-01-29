# IP2A-Database-v2: Project Context Document

**Document Purpose:** Bring Claude (Code or AI) up to speed for development sessions
**Last Updated:** January 29, 2026
**Current Version:** v0.7.2
**Current Phase:** Phase 6 Week 4 - Training Landing (Week 3 Complete)

---

## TL;DR

**What:** Union operations management system for IBEW Local 46 (Seattle-area electrical workers union)

**Who:** Xerxes - Business Representative by day, solo developer (5-10 hrs/week)

**Where:** Backend COMPLETE. Frontend authentication COMPLETE. Staff management COMPLETE.

**Stack:** FastAPI + PostgreSQL + SQLAlchemy + Jinja2 + HTMX + DaisyUI

**Status:** 205 tests passing, ~120 API endpoints, 8 ADRs, Phase 6 Week 3 complete

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

### Frontend: IN PROGRESS

| Week | Focus | Status |
|------|-------|--------|
| Week 1 | Setup + Login | Done |
| Week 2 | Auth cookies + Dashboard | Done |
| Week 3 | Staff management | Done |
| Week 4 | Training landing | NEXT |

### Frontend Tests: 40 tests

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
| Placeholder Routes | 3 | Done |

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
| **Testing** | pytest + httpx | 205 tests passing |
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
│   │   └── dashboard_service.py # Dashboard stats aggregation (Week 2)
│   ├── routers/                # API endpoints
│   │   └── dependencies/
│   │       ├── auth.py         # Bearer token auth
│   │       └── auth_cookie.py  # Cookie-based auth (Week 2)
│   ├── templates/              # Jinja2 templates (Phase 6)
│   │   ├── base.html
│   │   ├── base_auth.html
│   │   ├── components/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   └── errors/
│   ├── static/                 # CSS, JS, images (Phase 6)
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── seed/                   # Seed data
│   └── tests/                  # pytest tests
├── docs/
│   ├── decisions/              # ADRs (001-008)
│   ├── instructions/           # Claude Code instruction docs
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
pytest src/tests/test_frontend.py -v

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
from src.db.enums import MemberStatus, CohortStatus

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

## Phase 6 Week 2 Files Created/Modified

### New Files
```
src/routers/dependencies/
└── auth_cookie.py         # Cookie-based JWT validation

src/services/
└── dashboard_service.py   # Dashboard stats aggregation
```

### Modified Files
```
src/routers/
├── auth.py                # Added cookie setting on login/logout
└── frontend.py            # Added auth middleware, real data, placeholders

src/templates/
├── auth/login.html        # Flash messages, correct /auth/login path
└── dashboard/index.html   # HTMX refresh, activity feed

src/tests/
└── test_frontend.py       # 22 tests (10 new auth tests)
```

---

*Welcome to IP2A. Let's build something that lasts.*
