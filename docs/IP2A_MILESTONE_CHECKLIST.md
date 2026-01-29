# IP2A Milestone Checklist (Quick Reference)

> **Print this or keep it open during sessions**
> Last Updated: January 29, 2026

---

## Current Focus: Phase 6 Frontend (Week 4 - Training Landing)

### Legend: Done | In Progress | Pending

---

## Backend Phases: ALL COMPLETE

| Phase | Description | Models | Endpoints | Tests | Status |
|-------|-------------|--------|-----------|-------|--------|
| Phase 0 | Documentation & Structure | - | - | - | Done |
| Phase 1 | Auth (JWT, RBAC, Registration) | 4 | 13 | 52 | Done |
| Phase 2a | Union Ops (SALT, Benevolence, Grievance) | 5 | 27 | 31 | Done |
| Phase 2b | Training (Students, Courses, Grades) | 7 | ~35 | 33 | Done |
| Phase 3 | Documents (S3/MinIO) | 1 | 8 | 11 | Done |
| Phase 4 | Dues Tracking | 4 | ~35 | 21 | Done |
| **Total** | **Backend Complete** | **25** | **~120** | **165** | **Done** |

---

## Phase 6: Frontend Build

### Week 1: Setup + Login (COMPLETE)

| Task | Status |
|------|--------|
| Base templates (DaisyUI + Tailwind + HTMX + Alpine.js) | Done |
| Component templates (navbar, sidebar, flash, modal) | Done |
| Login page with HTMX form | Done |
| Forgot password page | Done |
| Dashboard placeholder | Done |
| Error pages (404, 500) | Done |
| Frontend router | Done |
| 12 frontend tests | Done |

**Commit:** `1274c12` - v0.7.0 (Week 1 Complete)

### Week 2: Auth Cookies + Dashboard (COMPLETE)

| Task | Status |
|------|--------|
| Cookie-based authentication (auth_cookie.py) | Done |
| HTTP-only cookies on login/logout | Done |
| Protected routes redirect to login | Done |
| Dashboard service with real stats | Done |
| Activity feed from audit log | Done |
| HTMX refresh for dashboard | Done |
| Flash message support | Done |
| 10 new auth tests (22 total) | Done |

**Commit:** `b997022` - v0.7.1 (Week 2 Complete)

### Week 3: Staff Management (COMPLETE)

| Task | Status |
|------|--------|
| StaffService with search/filter/paginate | Done |
| User list page with table and stats | Done |
| HTMX live search (300ms debounce) | Done |
| Filter by role and status | Done |
| Pagination component | Done |
| Quick edit modal with role checkboxes | Done |
| Account status toggle (active/locked) | Done |
| Full detail page with edit form | Done |
| Account actions (lock, unlock, reset password, delete) | Done |
| 403 error page | Done |
| 18 new staff tests (40 frontend total) | Done |

**Commits:**
- `4d80365` - Session A: User list with search
- `85ada48` - Session B: Quick edit modal
- `89a045c` - Session C: Actions and detail page

**Version:** v0.7.2 (Week 3 Complete)

### Week 4: Training Landing (NEXT)

| Task | Status |
|------|--------|
| Training overview page | Pending |
| Student list with status indicators | Pending |
| Course list | Pending |
| Quick enrollment actions | Pending |

---

## Quick Stats

| Metric | Current |
|--------|---------|
| Total Tests | 205 |
| Backend Tests | 165 |
| Frontend Tests | 40 |
| API Endpoints | ~120 |
| ORM Models | 25 |
| ADRs | 8 |
| Version | v0.7.2 |

---

## Version History

| Version | Date | Milestone |
|---------|------|-----------|
| v0.7.2 | 2026-01-29 | Phase 6 Week 3 - Staff Management |
| v0.7.1 | 2026-01-29 | Phase 6 Week 2 - Auth cookies + Dashboard |
| v0.7.0 | 2026-01-28 | Phase 4 Complete (Backend milestone) |
| v0.6.0 | 2026-01-28 | Phase 3 + Auth + Training |
| v0.2.0 | 2026-01-27 | Phase 1 Services Layer |
| v0.1.0 | 2026-01-XX | Initial backend stabilization |

---

## Commands Cheat Sheet

```bash
# Start dev environment
docker-compose up -d

# Run tests
pytest -v

# Run frontend tests only
pytest src/tests/test_frontend.py -v

# Run staff tests only
pytest src/tests/test_staff.py -v

# Check code quality
ruff check . --fix && ruff format .

# Database migration
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Run API server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# View logs
docker-compose logs -f api

# Access MinIO console (file storage)
open http://localhost:9001
```

---

## Session Workflow

### Starting a Session
1. `git pull origin main`
2. `docker-compose up -d`
3. `pytest -v --tb=short` (verify green)
4. Check CLAUDE.md for current tasks

### Ending a Session
1. `pytest -v` (verify green)
2. `git status` (check for uncommitted changes)
3. Commit with conventional commit message
4. `git push origin main`
5. Update CLAUDE.md with session summary

---

*Keep this checklist updated during each session!*
