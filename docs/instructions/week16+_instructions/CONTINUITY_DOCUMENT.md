# UnionCore (IP2A-Database-v2) Continuity Document

**Generated:** February 2, 2026  
**Purpose:** Copy this entire document into a new Claude thread to maintain project context  
**Project Path:** `~/Projects/IP2A-Database-v2` (macOS) or equivalent

---

## 🎯 Project Overview

**UnionCore** (aka IP2A-Database-v2) is a workplace organization operations management platform for IBEW Local 46 (Seattle-area electrical workers). It handles:

- **Member Management** - Profiles, employment history, notes
- **Dues Tracking** - Rates, periods, payments, adjustments, Stripe integration
- **Training Program** - Students, courses, grades, cohorts, instructors
- **Union Operations** - SALTing, benevolence fund, grievances
- **Grant Compliance** - Enrollment tracking, outcome reporting, Excel exports
- **Audit Trail** - NLRA-compliant 7-year retention with immutability

### Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, PostgreSQL 16 |
| Frontend | Jinja2 + HTMX + Alpine.js + DaisyUI (CDN) |
| Auth | JWT tokens (API), HTTP-only cookies (UI) |
| Payments | Stripe Checkout Sessions (card + ACH) |
| Storage | S3/MinIO for documents |
| Deployment | Railway (primary), Render (backup) |
| Testing | pytest (~375+ tests) |

---

## 📊 Current State (as of Feb 2, 2026)

### Version: v0.9.4-alpha (develop branch)

| Component | Status | Tests |
|-----------|--------|-------|
| Backend API | ✅ Complete | 165 |
| Frontend UI | ✅ Feature Complete | ~220 |
| Stripe Integration | ✅ Complete | Integrated |
| Grant Compliance | ✅ Complete | Integrated |
| Production Hardening | ✅ Complete | 32 |
| Mobile PWA | ✅ Complete | 14 |
| Analytics Dashboard | ✅ Complete | 19 |
| **Total** | **~95% Complete** | **~470** |

### Completed Frontend Weeks

| Week | Focus | Status |
|------|-------|--------|
| 1-6 | Foundation, Auth, Dashboard, Staff, Training, Members, Operations | ✅ |
| 8-9 | Reports & Export, Documents | ✅ |
| 10 | Dues UI | ✅ |
| 11-12 | Audit Trail, Member Notes, Profile | ✅ |
| 13-14 | IP2A Entities, Grant Module | ✅ |
| 16 | Production Hardening (security headers, health checks, Sentry) | ✅ |
| 17 | Post-Launch Operations (backups, runbooks, admin metrics) | ✅ |
| 18 | Mobile PWA (service worker, offline support, mobile CSS) | ✅ |
| 19 | Analytics Dashboard (executive dashboard, report builder) | ✅ |

### Remaining Work (Optional Enhancements)

| Item | Focus | Priority |
|------|-------|----------|
| Scheduled Reports | Email delivery of reports | 🟢 LOW |
| PDF Report Export | Add PDF option to report builder | 🟢 LOW |
| Dashboard Customization | User-configurable widgets | 🟢 LOW |

---

## 🏗️ Architecture Patterns

### Key Design Decisions

1. **Modular Monolith** - Single codebase, service-layer separation for future microservices
2. **Member ≠ Student** - Separate entities linked via foreign key
3. **Salting Score** - 1-5 scale for employer receptiveness
4. **User Lockout** - `locked_until` datetime field (NOT boolean `is_locked`)
5. **Audit Immutability** - PostgreSQL trigger prevents UPDATE/DELETE on audit_logs
6. **File Storage** - Transitioning from local filesystem to S3/cloud

### Service Layer Pattern

```python
# All business logic in services, not routers
from src.services.member_service import MemberService

service = MemberService(db)
member = await service.create(data)
```

### Frontend Pattern (HTMX)

```html
<!-- Partial updates via HTMX -->
<div hx-get="/members/table" hx-trigger="load" hx-target="this"></div>
```

### Enum Import Pattern

```python
# CORRECT - Always import from db.enums
from src.db.enums import MemberStatus, PaymentStatus

# WRONG - Never import from models
from src.models.member import MemberStatus  # ❌
```

---

## 📁 Project Structure

```
~/Projects/IP2A-Database-v2/
├── src/
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic validation schemas
│   ├── services/         # Business logic layer
│   ├── routers/          # API + UI routes
│   │   ├── api/          # REST API endpoints
│   │   └── ui/           # Frontend UI routes
│   ├── templates/        # Jinja2 templates
│   ├── static/           # CSS, JS
│   ├── db/               # Database config, enums
│   │   └── enums/        # All enum definitions
│   └── tests/            # pytest tests
├── alembic/              # Database migrations
├── docs/                 # Documentation
│   ├── decisions/        # ADRs (Architecture Decision Records)
│   ├── instructions/     # Week instruction docs
│   ├── runbooks/         # Operational procedures
│   └── reports/          # Session logs
├── scripts/              # Operational scripts
├── CLAUDE.md             # AI assistant context
├── CHANGELOG.md          # Version history
└── requirements.txt      # Python dependencies
```

---

## 🔑 Critical Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project context for AI assistants |
| `docs/IP2A_MILESTONE_CHECKLIST.md` | Progress tracking |
| `docs/decisions/ADR-*.md` | Architecture decisions |
| `src/db/enums/__init__.py` | All enum definitions |
| `src/services/audit_service.py` | AUDITED_TABLES list |
| `src/config/settings.py` | Environment configuration |

---

## 🚨 Important Constraints

### MUST Follow

1. **All member changes MUST be audited** (NLRA 7-year requirement)
2. **Sensitive fields MUST be redacted** for non-admin users (SSN, bank info)
3. **Import enums from `src.db.enums`** (not model files)
4. **Tests MUST pass before commit** (`pytest -v`)
5. **Update docs at end of session** (CHANGELOG, CLAUDE.md, milestone checklist)

### AVOID

- ❌ Boolean `is_locked` on User (use `locked_until` datetime)
- ❌ Direct model imports for enums
- ❌ Skipping audit logging for member-related endpoints
- ❌ Committing without running tests

---

## 📋 Complete Instruction Documents List

Located at: `/docs/instructions/` (or uploaded as files)

| Document | Focus | Est. Hours | Status |
|----------|-------|------------|--------|
| `WEEK_07_DUES_MANAGEMENT_UI.md` | Periods, payments, adjustments, Stripe UI | 6-8 | ✅ Done |
| `WEEK_11_AUDIT_TRAIL_MEMBER_NOTES.md` | Audit UI, member notes, immutability trigger | 8-10 | ✅ Done |
| `WEEK_12_PROFILE_SETTINGS.md` | User profile, password change, preferences | 4-6 | ✅ Done |
| `WEEK_13_IP2A_ENTITY_COMPLETION.md` | Entity verification | - | ✅ Done |
| `WEEK_14_GRANT_MODULE_EXPANSION.md` | Grant compliance system | - | ✅ Done |
| `WEEK_15_DEPLOYMENT_PREPARATION.md` | Railway/Render deployment, demo prep | 4-6 | ✅ Done |
| `WEEK_16_PRODUCTION_HARDENING.md` | Security headers, health checks, Sentry | 6-8 | ✅ Done |
| `WEEK_17_POST_LAUNCH_OPERATIONS.md` | Backups, runbooks, admin metrics | 4-6 | ✅ Done |
| `WEEK_18_MOBILE_PWA.md` | Mobile optimization, PWA, offline support | 6-8 | ✅ Done |
| `WEEK_19_ANALYTICS_DASHBOARD.md` | Executive dashboard, custom reports, exports | 8-10 | ✅ Done |

---

## 🎮 Quick Start Commands

```bash
# Navigate to project
cd ~/Projects/IP2A-Database-v2

# Start development environment
docker-compose up -d

# Run tests
pytest -v --tb=short

# Run specific test file
pytest src/tests/test_dues_ui.py -v

# Apply migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Check code quality
ruff check . --fix && ruff format .

# Run server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🔄 Session Workflow

### Starting a Session

1. `git checkout develop && git pull`
2. `docker-compose up -d`
3. `pytest -v --tb=short` (verify all green)
4. Review CLAUDE.md for current task
5. Read relevant instruction document

### Ending a Session (MANDATORY)

1. `pytest -v` (verify all green)
2. Update `/CHANGELOG.md`
3. Update `/CLAUDE.md` with session summary
4. Update `/docs/IP2A_MILESTONE_CHECKLIST.md`
5. Create session log: `/docs/reports/session-logs/YYYY-MM-DD-*.md`
6. **Scan `/docs/*` for any other docs needing updates**
7. Check if ADR needed for architectural decisions
8. `git add -A && git commit -m "feat/fix: description"`
9. `git push origin develop`

---

## 📝 End-of-Session Documentation Reminder

**MANDATORY:** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. **Do not forget about ADRs—update as necessary.**

### Quick Checklist

- [ ] `/CHANGELOG.md` — Version bump, changes summary
- [ ] `/CLAUDE.md` — If architecture/patterns changed
- [ ] `/docs/IP2A_MILESTONE_CHECKLIST.md` — Progress updates
- [ ] `/docs/decisions/ADR-XXX.md` — If architectural decisions made
- [ ] `/docs/reports/session-logs/YYYY-MM-DD-*.md` — **Create new session log**
- [ ] Any other relevant docs in `/docs/*`

---

## 🎯 Recommended Next Steps

### All Core Work Complete

All major development milestones have been completed:
- ✅ Backend API complete
- ✅ Frontend UI feature complete
- ✅ Production hardening done
- ✅ Mobile PWA implemented
- ✅ Analytics dashboard deployed

### Optional Enhancements

1. **Scheduled Reports** - Email delivery of analytics reports
2. **PDF Export** - Add PDF option to report builder
3. **Dashboard Widgets** - User-configurable dashboard
4. **Additional Mobile Features** - Push notifications, app shortcuts

### Maintenance Path

1. Regular security updates
2. Database backups verification
3. Performance monitoring via Sentry
4. User feedback implementation

---

## 📚 Related ADRs

| ADR | Topic |
|-----|-------|
| ADR-008 | Audit Logging (NLRA compliance, 7-year retention) |
| ADR-011 | Dues Frontend Patterns (HTMX + DaisyUI) |
| ADR-013 | Stripe Payment Integration (Checkout Sessions) |
| ADR-014 | Grant Compliance Reporting (enrollment tracking) |

---

## 🧠 Memory Context (for Claude.ai)

```
IP2A-v2 project path: ~/Projects/IP2A-Database-v2
IP2A-v2: v0.9.4-alpha on develop branch. Backend complete (165 tests), frontend feature-complete (~220 tests), production-hardened (~470 total tests).
IP2A-v2: All weeks 1-19 complete. Production hardening, Mobile PWA, and Analytics Dashboard deployed.
IP2A-v2 architecture: Member separate from Student (linked via FK). Salting score 1-5. File storage local→S3.
IP2A-v2: User model uses locked_until datetime not boolean.
IP2A-v2: Import enums from src.db.enums, not from models.
IP2A-v2: All member changes must be audited (NLRA 7-year requirement).
IP2A-v2: Analytics dashboard requires officer-level access (admin, officer, secretary, treasurer, business_manager).
```

---

## 📞 Support

- **Developer:** Xerxes (IBEW Local 46 Business Rep)
- **Repository:** github.com/theace26/IP2A-Database-v2
- **Development Time:** 5-10 hours/week (hobby project)

---

## ⚠️ Before Starting Any Work

1. **Read this entire document** for context
2. **Check the instruction document** for the specific week you're working on
3. **Verify tests pass** before making changes
4. **Update documentation** at end of session

---

*Copy this entire document into a new Claude thread to maintain project continuity.*
*Generated: February 2, 2026*
