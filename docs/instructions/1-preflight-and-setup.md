# Phase 6 Week 1: Document 1 - Pre-flight & Setup

**Execution Order:** 1 of 6
**Estimated Time:** 30-45 minutes
**Goal:** Verify environment, tag v0.7.0, update documentation, create directory structure

---

## Pre-flight Checklist

Run these commands to verify your environment is ready:

```bash
# Navigate to project
cd ~/Projects/IP2A-Database-v2

# 1. Docker is running
docker-compose ps
# Should show postgres and app containers

# 2. Tests pass
pytest -v --tb=short
# Should show 165 tests passing

# 3. API is accessible
curl -s http://localhost:8000/docs | head -5
# Should return HTML

# 4. Clean git state
git status
# Should be clean or have known changes

# 5. On main branch
git branch --show-current
# Should show: main
```

**If any check fails, resolve before proceeding.**

---

## Task 1.1: Tag v0.7.0

Backend is complete. Tag it before starting frontend work.

```bash
# Create annotated tag
git tag -a v0.7.0 -m "Phase 4 complete - Backend production-ready

Features complete:
- Core: Organizations, Members, Employment
- Auth: JWT, RBAC, Registration (52 tests)
- Union Ops: SALTing, Benevolence, Grievances
- Training: Students, Courses, Grades, Certifications
- Documents: S3/MinIO integration
- Dues: Rates, Periods, Payments, Adjustments

Stats: 165 tests, ~120 endpoints, 8 ADRs"

# Push tag to remote
git push origin v0.7.0

# Verify
git tag -l
```

---

## Task 1.2: Create Archive Directory

Archive old documentation before updating:

```bash
mkdir -p docs/archive
```

---

## Task 1.3: Update CLAUDE.md

Replace the root CLAUDE.md with frontend-ready version.

**Action:** Replace `CLAUDE.md` content with this:

```markdown
# IP2A-Database-v2: Project Context Document

**Document Purpose:** Bring Claude (Code or AI) up to speed for development sessions
**Last Updated:** January 28, 2026
**Current Version:** v0.7.0
**Current Phase:** Phase 6 Week 1 - Frontend Foundation

---

## 🎯 TL;DR

**What:** Union operations management system for IBEW Local 46 (Seattle-area electrical workers union)

**Who:** Xerxes - Business Representative by day, solo developer (5-10 hrs/week)

**Where:** Backend COMPLETE. Starting frontend build.

**Stack:** FastAPI + PostgreSQL + SQLAlchemy + Jinja2 + HTMX + DaisyUI

**Status:** 165 tests passing, ~120 API endpoints, 8 ADRs, backend production-ready

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
| Week 1 | Setup + Login | ← CURRENT |
| Week 2 | Auth cookies + Dashboard | Pending |
| Week 3 | Staff management | Pending |
| Week 4 | Training landing | Pending |

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
| **Testing** | pytest + httpx | 165 tests passing |
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
│   │   ├── components/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   └── errors/
│   ├── static/                 # CSS, JS, images (Phase 6)
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

## 🎯 Current Focus: Phase 6 Week 1

**Objective:** Set up frontend foundation and working login page

**Instruction Documents:** `docs/instructions/1-preflight-and-setup.md` through `6-testing-and-commit.md`

### Acceptance Criteria

- [ ] `/login` renders styled login form
- [ ] Form submits via HTMX to `/api/auth/login`
- [ ] `/dashboard` renders with sidebar and stats cards
- [ ] Static files served correctly
- [ ] All tests pass (165 existing + new frontend tests)

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

*Welcome to IP2A. Let's build something that lasts.*
```

---

## Task 1.4: Create Instructions Directory

```bash
mkdir -p docs/instructions
```

---

## Task 1.5: Update CHANGELOG.md

Add this section at the top of CHANGELOG.md (after any existing [Unreleased] section, or create one):

```markdown
## [Unreleased]

### Added
- **Phase 6 Week 1: Frontend Foundation** (In Progress)
  * Base templates with DaisyUI + Tailwind CSS + HTMX + Alpine.js (CDN)
  * Login page with HTMX form submission
  * Forgot password page
  * Dashboard placeholder with stats cards
  * Responsive sidebar navigation with drawer component
  * Component templates (navbar, sidebar, flash messages, modal)
  * Custom CSS and JavaScript
  * Error pages (404, 500)
  * Frontend router for HTML page serving
  * Frontend tests

### Changed
- Updated CLAUDE.md with frontend phase context
- Created docs/instructions/ for Claude Code instruction documents

---

## [0.7.0] - 2026-01-28

### Added
- **Phase 4: Dues Tracking System**
  * 4 new models: DuesRate, DuesPeriod, DuesPayment, DuesAdjustment
  * Complete dues lifecycle: rate management, period tracking, payments, adjustments
  * Member classification-based rate lookup (9 classifications)
  * Approval workflow for dues adjustments
  * ~35 API endpoints across 4 routers
  * 21 new tests (165 total passing)
  * ADR-008: Dues Tracking System design document

**Note:** This marks the completion of all backend phases. The system now has:
- 165 tests passing
- ~120 API endpoints
- 8 Architecture Decision Records
```

---

## Task 1.6: Create Frontend Directory Structure

```bash
# Create template directories
mkdir -p src/templates/{components,auth,dashboard,staff,training,errors}

# Create static directories  
mkdir -p src/static/{css,js,images}

# Create placeholder favicon to prevent 404s
touch src/static/images/favicon.ico
```

**Verify structure:**

```bash
find src/templates -type d | sort
find src/static -type d | sort
```

Expected output:
```
src/templates
src/templates/auth
src/templates/components
src/templates/dashboard
src/templates/errors
src/templates/staff
src/templates/training

src/static
src/static/css
src/static/images
src/static/js
```

---

## Task 1.7: Commit Setup Changes

```bash
git add -A
git commit -m "chore: Setup Phase 6 frontend development

- Tag v0.7.0 (backend complete)
- Update CLAUDE.md with frontend context
- Create docs/instructions/ directory
- Create src/templates/ structure
- Create src/static/ structure
- Update CHANGELOG.md with v0.7.0 and Phase 6"
```

---

## ✅ Document 1 Complete

**Checklist:**
- [ ] Pre-flight checks passed
- [ ] v0.7.0 tagged and pushed
- [ ] CLAUDE.md updated
- [ ] CHANGELOG.md updated
- [ ] Directory structure created
- [ ] Changes committed

**Next:** Run Document 2 - Base Templates

---

*Document 1 of 6 | Phase 6 Week 1*
