# IP2A Milestone Checklist (Quick Reference)

> **Print this or keep it open during sessions**
> Last Updated: January 27, 2026

---

## Current Focus: Phase 0 → Phase 1

### ✅ = Complete | 🟡 = In Progress | ⬜ = Not Started

---

## Phase 0: Documentation & Structure (Week 1)

### 0.1 Documentation Reorganization
| Status | Task | Est. |
|--------|------|------|
| ⬜ | Execute DOCS_REORGANIZATION_INSTRUCTIONS.md | 2h |
| ⬜ | Create ADRs (001-004) | 1h |
| ⬜ | Create runbook templates | 1h |
| ⬜ | Create CHANGELOG.md + CONTRIBUTING.md | 30m |
| ⬜ | Update CLAUDE.md | 30m |

### 0.2 Frontend Scaffolding
| Status | Task | Est. |
|--------|------|------|
| ⬜ | Create templates/ directory structure | 30m |
| ⬜ | Set up Tailwind CSS (CLI or CDN) | 1h |
| ⬜ | Add HTMX + Alpine.js (CDN) | 30m |
| ⬜ | Create base.html layout | 1h |
| ⬜ | Create health check page | 30m |

**Phase 0 Target:** End of Week 1

---

## Phase 1: Foundation (Weeks 2-9)

### 1.1 Auth Database Schema (Week 2)
| Status | Task |
|--------|------|
| ⬜ | User model |
| ⬜ | Role model |
| ⬜ | UserRole junction |
| ⬜ | RefreshToken model |
| ⬜ | Alembic migration |
| ⬜ | Seed default roles + admin |

### 1.2 Password Service (Week 3)
| Status | Task |
|--------|------|
| ⬜ | Install bcrypt |
| ⬜ | hash_password() |
| ⬜ | verify_password() |
| ⬜ | check_strength() |
| ⬜ | Unit tests (8+) |

### 1.3 JWT Service (Week 3-4)
| Status | Task |
|--------|------|
| ⬜ | Install PyJWT |
| ⬜ | create_access_token() |
| ⬜ | create_refresh_token() |
| ⬜ | verify_token() |
| ⬜ | refresh_access_token() |
| ⬜ | revoke_refresh_token() |
| ⬜ | Unit tests (10+) |

### 1.4 Auth Endpoints (Week 4-5)
| Status | Task |
|--------|------|
| ⬜ | POST /auth/login |
| ⬜ | POST /auth/logout |
| ⬜ | POST /auth/refresh |
| ⬜ | POST /auth/password/reset-request |
| ⬜ | POST /auth/password/reset-confirm |
| ⬜ | GET /auth/me |
| ⬜ | Rate limiting |
| ⬜ | Integration tests (12+) |

### 1.5 Task Service Abstraction (Week 5)
| Status | Task |
|--------|------|
| ⬜ | TaskService ABC |
| ⬜ | FastAPITaskService implementation |
| ⬜ | Task status tracking |
| ⬜ | Dependency injection |
| ⬜ | Unit tests |
| ⬜ | Document Celery migration path (ADR-006) |

### 1.6 Auth Middleware (Week 5-6)
| Status | Task |
|--------|------|
| ⬜ | get_current_user dependency |
| ⬜ | require_roles() factory |
| ⬜ | Protect existing endpoints |
| ⬜ | Update audit logs with user_id |
| ⬜ | Tests for role enforcement |

### 1.7 Login UI (Week 6-7)
| Status | Task |
|--------|------|
| ⬜ | Login page (Tailwind styled) |
| ⬜ | Logout page |
| ⬜ | Forgot password page |
| ⬜ | Reset password page |
| ⬜ | Flash messages |
| ⬜ | Redirect handling |

### 1.8 File Storage (Week 7-8)
| Status | Task |
|--------|------|
| ⬜ | Add MinIO to docker-compose |
| ⬜ | FileStorageService |
| ⬜ | upload_file() |
| ⬜ | download_file() |
| ⬜ | delete_file() |
| ⬜ | generate_presigned_url() |
| ⬜ | Update FileAttachment model |
| ⬜ | Integration tests |

### 1.9 File Upload UI (Week 8-9)
| Status | Task |
|--------|------|
| ⬜ | Upload component (HTMX) |
| ⬜ | Drag-and-drop |
| ⬜ | Progress indicator |
| ⬜ | File list display |
| ⬜ | Download links |
| ⬜ | Delete confirmation |

### 1.10 Phase 1 Stabilization (Week 9-10)
| Status | Task |
|--------|------|
| ⬜ | Full test suite passes |
| ⬜ | Security checklist complete |
| ⬜ | Documentation updated |
| ⬜ | Merge to main |
| ⬜ | Tag v0.3.0 |

**Phase 1 Target:** End of Week 10

---

## Quick Stats Tracker

| Metric | Target | Actual |
|--------|--------|--------|
| Phase 0 Hours | 5-8 | ___ |
| Phase 1 Hours | 55-70 | ___ |
| Tests Written | 50+ | ___ |
| Pages Created | 8+ | ___ |

---

## Blockers Log

| Date | Blocker | Resolution |
|------|---------|------------|
| | | |
| | | |

---

## Session Log

| Date | Time | Milestone | Tasks Completed |
|------|------|-----------|-----------------|
| | | | |
| | | | |
| | | | |

---

## Commands Cheat Sheet

```bash
# Start dev environment
cd $IP2A && docker-compose up -d

# Run tests
pytest -v

# Run specific test file
pytest src/tests/test_auth.py -v

# Check code quality
ruff check . --fix && ruff format .

# Database migration
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# View logs
docker-compose logs -f api

# Access MinIO console (file storage)
open http://localhost:9001

# Access Grafana (Phase 4+)
open http://localhost:3000

# Build Tailwind CSS (watch mode)
npm run build:css
```

---

*Keep this checklist updated during each session!*
