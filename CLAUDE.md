# IP2A-Database-v2: Project Context Document

**Document Purpose:** Bring Claude (Code or AI) up to speed for development sessions
**Last Updated:** January 28, 2026
**Current Version:** v0.7.0
**Current Phase:** Phase 6 Week 2 - Auth Cookies + Dashboard (Week 1 Complete)

---

## 🎯 TL;DR

**What:** Union operations management system for IBEW Local 46 (Seattle-area electrical workers union)

**Who:** Xerxes - Business Representative by day, solo developer (5-10 hrs/week)

**Where:** Backend COMPLETE. Starting frontend build.

**Stack:** FastAPI + PostgreSQL + SQLAlchemy + Jinja2 + HTMX + DaisyUI

**Status:** 177 tests passing, ~120 API endpoints, 8 ADRs, Phase 6 Week 1 complete

---

## 📊 Current State

### Backend: COMPLETE ✅

| Component | Models | Endpoints | Tests | Status |
|-----------|--------|-----------|-------|--------|
| Core (Org, Member, Employment) | 4 | ~20 | 17 | ✅ |
| Auth (JWT, RBAC, Registration) | 4 | 13 | 52 | ✅ |
| Union Ops (SALTing, Benevolence, Grievance) | 5 | 27 | 31 | ✅ |
| Training (Students, Courses, Grades, Certs) | 7 | ~35 | 33 | ✅ |
| Documents (S3/MinIO) | 1 | 8 | 11 | ✅ |
| Dues (Rates, Periods, Payments, Adjustments) | 4 | ~35 | 21 | ✅ |
| **Total** | **25** | **~120** | **165** | ✅ |

### Frontend: IN PROGRESS 🟡

| Week | Focus | Status |
|------|-------|--------|
| Week 1 | Setup + Login | ✅ Complete |
| Week 2 | Auth cookies + Dashboard | ← NEXT |
| Week 3 | Staff management | Pending |
| Week 4 | Training landing | Pending |

### Frontend Tests: 12 tests

| Component | Tests | Status |
|-----------|-------|--------|
| Public Routes (login, forgot-password) | 3 | ✅ |
| Protected Routes (dashboard, logout) | 2 | ✅ |
| Static Files (CSS, JS) | 2 | ✅ |
| Error Pages (404, 500) | 2 | ✅ |
| Page Content | 3 | ✅ |

---

## 🏗️ Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| **API** | FastAPI | Async, auto-docs |
| **ORM** | SQLAlchemy 2.0 | Models = source of truth |
| **Database** | PostgreSQL 16 | JSONB, proper constraints |
| **Migrations** | Alembic | Governed, drift-detected |
| **Auth** | JWT + bcrypt | 30min access, 7day refresh |
| **Files** | MinIO (dev) / S3 (prod) | Presigned URLs |
| **Templates** | Jinja2 | Server-side rendering |
| **Interactivity** | HTMX | HTML-over-the-wire |
| **Micro-interactions** | Alpine.js | Dropdowns, toggles |
| **CSS** | DaisyUI + Tailwind | CDN, no build step |
| **Testing** | pytest + httpx | 177 tests passing |
| **Container** | Docker | Full dev environment |

---

## 📁 Project Structure

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
│   ├── routers/                # API endpoints
│   │   └── dependencies/       # Auth dependencies
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

## 🔧 Quick Commands

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

## 🎯 Phase 6 Week 1: COMPLETE ✅

**Objective:** Set up frontend foundation and working login page

**Instruction Documents:** `docs/instructions/1-preflight-and-setup.md` through `6-testing-and-commit.md`

### Session A Complete ✅ (January 28, 2026)

**Documents Completed:** 1, 2, 3 of 6

| Task | Status |
|------|--------|
| Pre-flight checks (Docker, tests, API, git) | ✅ |
| Tag v0.7.0 (backend milestone) | ✅ |
| Update CLAUDE.md for frontend phase | ✅ |
| Create directory structure (templates, static) | ✅ |
| Create base.html (sidebar layout) | ✅ |
| Create base_auth.html (centered layout) | ✅ |
| Create _navbar.html component | ✅ |
| Create _sidebar.html component | ✅ |
| Create _flash.html component | ✅ |
| Create _modal.html component | ✅ |
| Create custom.css (2.3 KB) | ✅ |
| Create app.js (4.7 KB) | ✅ |
| Archive old instruction files to docs/archive/ | ✅ |
| All 165 tests passing | ✅ |

**Commit:** `009fa3b feat(frontend): Phase 6 Week 1 Session A - Frontend foundation`

### Session B Complete ✅ (January 28, 2026)

**Documents Completed:** 4, 5, 6 of 6

| Task | Status |
|------|--------|
| Create login.html (HTMX form, error handling) | ✅ |
| Create forgot_password.html | ✅ |
| Create dashboard/index.html (stats cards, quick actions) | ✅ |
| Create errors/404.html | ✅ |
| Create errors/500.html | ✅ |
| Create src/routers/frontend.py | ✅ |
| Update main.py (static files, router, exception handlers) | ✅ |
| Add jinja2 to requirements.txt | ✅ |
| Create test_frontend.py (12 tests) | ✅ |
| All 177 tests passing | ✅ |

### Acceptance Criteria - All Met ✅

- [x] `/login` renders styled login form
- [x] Form submits via HTMX to `/api/auth/login`
- [x] `/dashboard` renders with sidebar and stats cards
- [x] Static files created (CSS/JS)
- [x] All tests pass (165 existing + 12 frontend = 177)

---

## 🚨 Important Patterns

### Enum Imports
```python
# ✅ CORRECT
from src.db.enums import MemberStatus, CohortStatus

# ❌ WRONG (old location)
from src.models.enums import MemberStatus
```

### Service Layer Pattern
All business logic goes through services, not directly in routes.

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
<form hx-post="/api/endpoint" hx-target="#result" hx-swap="innerHTML">
    <!-- form fields -->
</form>
```

---

## 📝 Session Workflow

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

## 🔄 Claude.ai Sync Schedule

### When to Update Claude.ai

**Update immediately when:**
- ✅ Major phase complete
- ✅ Critical decisions needed
- ✅ Blockers encountered

**Update weekly for:**
- 📊 Progress report
- 🎯 Planning sessions

### What to Share

**For syncs, share:**
- Latest session summary from `docs/reports/session-logs/`
- List of completed tasks
- Outstanding questions/decisions needed
- Blockers or risks identified

---

## 📂 Phase 6 Week 1 Files Created

### Session A
```
src/templates/
├── base.html              # Main layout with sidebar
├── base_auth.html         # Centered layout for auth pages
└── components/
    ├── _navbar.html       # Top navigation bar
    ├── _sidebar.html      # Left sidebar menu
    ├── _flash.html        # Alert messages with auto-dismiss
    └── _modal.html        # HTMX modal container

src/static/
├── css/custom.css         # Custom styles (transitions, cards, tables)
├── js/app.js              # HTMX handlers, toast notifications, utilities
└── images/favicon.ico     # Placeholder
```

### Session B
```
src/templates/
├── auth/
│   ├── login.html         # Login page with HTMX form
│   └── forgot_password.html
├── dashboard/
│   └── index.html         # Dashboard with stats cards
└── errors/
    ├── 404.html           # Not found page
    └── 500.html           # Server error page

src/routers/
└── frontend.py            # Frontend router (HTML pages)

src/tests/
└── test_frontend.py       # 12 frontend tests
```

---

*Welcome to IP2A. Let's build something that lasts.*
