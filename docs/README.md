# UnionCore Documentation

**Project:** UnionCore (formerly IP2A-Database-v2)
**Version:** v0.9.8-alpha
**Last Updated:** February 5, 2026
**Repository:** https://github.com/theace26/IP2A-Database-v2

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](../CLAUDE.md) | Project context for Claude AI sessions |
| [Backend Roadmap](IP2A_BACKEND_ROADMAP.md) | Master development plan with phases and milestones |
| [Milestone Checklist](IP2A_MILESTONE_CHECKLIST.md) | Actionable task lists by phase and week |
| [CHANGELOG.md](../CHANGELOG.md) | Version history and release notes |

---

## Hub/Spoke Project Structure

UnionCore uses a **Hub/Spoke model** for development planning via Claude AI projects. This is an organizational structure for conversations, NOT a code architecture change.

### What This Means

| Project | Scope | Status |
|---------|-------|--------|
| **Hub** | Strategy, architecture, cross-cutting decisions, roadmap, documentation | Active |
| **Spoke 2: Operations** | Dispatch/Referral, Pre-Apprenticeship, SALTing, Benevolence | Active — Phase 7 |
| **Spoke 1: Core Platform** | Members, Dues, Employers, Member Portal | Create when needed |
| **Spoke 3: Infrastructure** | Dashboard/UI, Reports, Documents, Import/Export, Logging | Create when needed |

### Key Principles

1. **Claude Code executes all instruction documents** — regardless of which Spoke produced them
2. **Hub handles cross-cutting concerns** — changes to `main.py`, `conftest.py`, base templates, ADRs
3. **Spokes handle module-specific work** — feature implementation, tests, module-specific docs
4. **Sprint weeks ≠ calendar weeks** — At 5-10 hrs/week, each sprint takes 1-2 calendar weeks

### Cross-Project Communication

Claude cannot access conversations across projects. When decisions affect multiple Spokes:
- The user provides a **handoff note** to the receiving project
- All handoff notes follow a standard format (context, decisions, action items)
- CLAUDE.md remains the single source of truth for project state

---

## Current Status

| Metric | Value |
|--------|-------|
| **Version** | v0.9.8-alpha |
| **Test Pass Rate** | 92.7% (517/558 non-skipped) |
| **Total Tests** | 593 (517 passing, 35 skipped, 41 failing/errors) |
| **API Endpoints** | ~228+ |
| **Models** | 32 (26 existing + 6 Phase 7) |
| **ADRs** | 18 |
| **Deployment** | Railway (live) |

### Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phases 1-4 | Core Platform (Members, Dues, Training, Auth) | ✅ Complete |
| Phase 5 | Access DB Migration | ⏸️ Blocked (stakeholder approval) |
| Phase 6 | Frontend (Weeks 1-19) | ✅ Complete |
| **Phase 7** | Referral & Dispatch System | 🔄 In Progress (Weeks 20-30 done) |
| Phase 8 | Square Payment Migration | 📋 Planned (after Phase 7 stabilizes) |

---

## Documentation Structure

### `/docs/` — Main Documentation

| Folder/File | Contents |
|-------------|----------|
| `decisions/` | Architecture Decision Records (ADR-001 through ADR-018) |
| `phase7/` | Phase 7 planning docs, LaborPower analysis, continuity documents |
| `instructions/` | Claude Code instruction documents by week |
| `guides/` | How-to guides and tutorials |
| `standards/` | Coding standards, naming conventions |
| `runbooks/` | Deployment, backup, disaster recovery, incident response |
| `reports/` | Session logs, test reports |
| `historical/` | Archived documentation versions |
| `architecture/` | System architecture diagrams and docs |

### Key Phase 7 Documents

| Document | Purpose |
|----------|---------|
| `phase7/UnionCore_Continuity_Document_Consolidated.md` | Master reference (Volumes 1+2 merged) |
| `phase7/PHASE7_IMPLEMENTATION_PLAN_v2.md` | Technical implementation details |
| `phase7/LOCAL46_REFERRAL_BOOKS.md` | Book catalog and business rules |
| `phase7/LABORPOWER_GAP_ANALYSIS.md` | Data gaps and resolution strategy |
| `phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` | 78 reports to build |

---

## Architecture Decision Records (ADRs)

| ADR | Title | Status |
|-----|-------|--------|
| ADR-001 | Database (PostgreSQL) | Accepted |
| ADR-002 | Frontend (HTMX + Alpine.js) | Accepted |
| ADR-003 | Authentication (JWT) | Accepted |
| ADR-004 | File Storage (Object Storage) | Accepted |
| ADR-005 | CSS Framework (Tailwind + DaisyUI) | Accepted |
| ADR-006 | Background Jobs (TaskService) | Accepted |
| ADR-007 | Observability (Grafana + Loki) | Accepted |
| ADR-008 | Audit Logging (Two-Tier) | Accepted |
| ADR-009 | Dependency Management | Accepted |
| ADR-010 | Dues UI Patterns | Accepted |
| ADR-011 | Dues Frontend Patterns | Accepted |
| ADR-012 | Report Generation (WeasyPrint + openpyxl) | Accepted |
| ADR-013 | Grant Compliance Reporting | Accepted |
| ADR-014 | Production Security Headers | Accepted |
| ADR-015 | Phase 7 Foundation | Accepted |
| ADR-016 | Phase 7 Frontend UI Patterns | Accepted |
| ADR-017 | Schema Drift Prevention | Proposed |
| ADR-018 | Square Payment Integration | Accepted |

---

## Quick Commands

```bash
# Start development environment
docker-compose up -d

# Run all tests
pytest -v

# Run specific test file
pytest src/tests/test_dispatch_frontend.py -v

# Apply database migrations
alembic upgrade head

# Run API server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Format code
ruff check . --fix && ruff format .
```

---

## Getting Help

1. **Start with CLAUDE.md** — comprehensive project context
2. **Check the Roadmap** — for phase-level planning
3. **Check the Checklist** — for actionable tasks
4. **Check session logs** — in `docs/reports/session-logs/` for recent work
5. **Check ADRs** — for architectural decisions and rationale

---

## End-of-Session Documentation

At the end of any development session:

1. Update `CHANGELOG.md` with changes made
2. Update `CLAUDE.md` if project state changed (test counts, version, etc.)
3. Create session log in `docs/reports/session-logs/` for significant work
4. Generate handoff note if work affects other Spokes

---

*UnionCore Documentation README — v1.0 — February 5, 2026*
