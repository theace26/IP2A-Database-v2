# Week 31 — Hub Documentation Generation

**Date:** February 5, 2026
**Type:** Claude Code Instruction Document
**Purpose:** Generate three pending Hub documents and deploy them to the repository

---

## Context

The Hub/Spoke documentation migration has been discussed across multiple threads since early February. The Claude Code FileOps instructions were generated, but the three actual documents were never produced. This instruction document completes that work.

**Current Project State (as of Week 30):**
- Version: v0.9.8-alpha
- Tests: 593 total (517 passing, 35 skipped, 41 failing/errors)
- Pass Rate: 92.7%
- Endpoints: ~228+
- Models: 32 (26 existing + 6 Phase 7)
- ADRs: 18
- Deployment: Railway (live)
- Current Phase: Phase 7 Weeks 20-27 complete (backend + frontend UI)

---

## Pre-Flight Verification

Before generating documents, verify the current state:

```bash
# Get actual test counts
pytest --collect-only -q 2>/dev/null | tail -5

# Get current version from CLAUDE.md
head -10 CLAUDE.md | grep -E "Version|version"

# Verify docs directory structure
ls -la docs/*.md | head -10

# Check if historical directory exists
ls -la docs/historical/ 2>/dev/null || echo "docs/historical/ does not exist"
```

---

## Phase 1: Create Directory Structure

```bash
# Create historical archive directory if it doesn't exist
mkdir -p docs/historical

# Archive any floating README variants
for f in docs/docs_README*.md docs_README*.md; do
    [ -f "$f" ] && mv "$f" docs/historical/ && echo "Archived: $f"
done
```

---

## Phase 2: Generate hub_README_v1.md

**Deploys to:** `docs/README.md`
**Purpose:** Navigation document with Hub/Spoke explainer for first-time readers

Create file `docs/README.md` with the following content:

```markdown
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
| ADR-015 | Mobile PWA Strategy | Accepted |
| ADR-016 | Analytics Dashboard Architecture | Accepted |
| ADR-017 | Schema Drift Prevention | Proposed |
| ADR-018 | Stripe to Square Migration | Accepted |

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
```

---

## Phase 3: Generate IP2A_MILESTONE_CHECKLIST_v2.md

**Deploys to:** `docs/IP2A_MILESTONE_CHECKLIST.md`
**Purpose:** Actionable task checkboxes organized by phase and week

Create file `docs/IP2A_MILESTONE_CHECKLIST.md` with the following content:

```markdown
# UnionCore Milestone Checklist

**Document Purpose:** Actionable task tracking by phase and week
**Version:** v2.0
**Last Updated:** February 5, 2026
**Project Version:** v0.9.8-alpha

---

## Quick Stats

| Metric | Value |
|--------|-------|
| Tests | 593 total (517 passing, 92.7% pass rate) |
| Endpoints | ~228+ |
| Models | 32 |
| ADRs | 18 |
| Frontend Weeks | 1-19 complete |
| Phase 7 Weeks | 20-30 complete |

---

## Hub/Spoke Ownership

| Spoke | Phases Owned |
|-------|--------------|
| Hub | Architecture, ADRs, Roadmap, Cross-cutting |
| Spoke 2: Operations | Phase 7 (Dispatch/Referral) |
| Spoke 1: Core Platform | Phases 1-4 (future maintenance) |
| Spoke 3: Infrastructure | Phase 6 UI, Reports (future maintenance) |

**Note:** Sprint weeks ≠ calendar weeks. At 5-10 hrs/week, each sprint takes 1-2 calendar weeks.

---

## Phases 1-4: Core Platform — ✅ COMPLETE

- [x] Phase 1: Organization & Members
- [x] Phase 2: Authentication & RBAC
- [x] Phase 3: Union Operations (SALTing, Benevolence, Grievances)
- [x] Phase 4: Training Module (Students, Courses, Grades, Certs)
- [x] Phase 4b: Documents (S3/MinIO integration)
- [x] Phase 4c: Dues (Rates, Periods, Payments, Adjustments)

---

## Phase 5: Access DB Migration — ⏸️ BLOCKED

- [ ] Stakeholder approval for Market Recovery data access
- [ ] Proof-of-concept demo for Access Database owner
- [ ] Data export from Access
- [ ] Schema mapping to UnionCore
- [ ] Migration scripts
- [ ] Validation and reconciliation

**Blocked By:** Stakeholder approval pending. Frame as complementary, not replacement.

---

## Phase 6: Frontend — ✅ COMPLETE (Weeks 1-19)

### Week 1: Setup + Login ✅
- [x] Jinja2 template structure
- [x] Login page with form validation
- [x] Base templates (base.html, base_auth.html)
- [x] Static file serving

### Week 2: Auth Cookies + Dashboard ✅
- [x] Cookie-based authentication
- [x] Dashboard with stats cards
- [x] Sidebar navigation
- [x] DashboardService

### Week 3: Staff Management ✅
- [x] Staff list page with search/filter
- [x] Staff create/edit forms
- [x] Role assignment UI
- [x] HTMX inline editing
- [x] 18 staff management tests

### Week 4: Training Landing ✅
- [x] Training dashboard
- [x] Student list with filters
- [x] Course management
- [x] TrainingFrontendService
- [x] 19 training tests

### Week 5: Members Landing ✅
- [x] Members list page
- [x] Member detail view
- [x] Classification filters
- [x] MemberFrontendService
- [x] 15 member tests

### Week 6: Union Operations ✅
- [x] Operations dashboard
- [x] SALTing management
- [x] Benevolence tracking
- [x] Grievance workflow
- [x] OperationsFrontendService
- [x] 21 operations tests

### Weeks 7-19: Extended Frontend ✅
- [x] Week 8: Reports & Export (30 tests)
- [x] Week 9: Documents Frontend (6 tests)
- [x] Week 10: Dues UI (37 tests)
- [x] Week 11: Audit UI + Member Notes + Stripe
- [x] Week 12: Profile & Settings
- [x] Week 13: Entity Audit verification
- [x] Week 14: Grant Compliance Reporting
- [x] Week 16: Production Hardening + Security
- [x] Week 17: Post-Launch Operations
- [x] Week 18: Mobile Optimization + PWA (14 tests)
- [x] Week 19: Analytics Dashboard (19 tests)

---

## Phase 7: Referral & Dispatch — 🔄 IN PROGRESS

**Owner:** Spoke 2: Operations
**Status:** Weeks 20-30 complete, sub-phases 7a-7g remaining

### Weeks 20-21: Phase 7 Models ✅
- [x] 6 new models created (ReferralBook, BookRegistration, LaborRequest, Dispatch, JobBid, RegistrationActivity)
- [x] Enums defined (BookType, DispatchStatus, BidStatus, etc.)
- [x] Schemas created
- [x] Alembic migration generated

### Weeks 22-24: Phase 7 Services ✅
- [x] 7 services created:
  - [x] ReferralBookService
  - [x] BookRegistrationService
  - [x] LaborRequestService
  - [x] DispatchService
  - [x] JobBidService
  - [x] RegistrationActivityService
  - [x] DispatchBusinessRulesService
- [x] 14 business rules implemented

### Week 25: Phase 7 API Routers ✅
- [x] 5 API routers created:
  - [x] referral_books.py
  - [x] book_registrations.py
  - [x] labor_requests.py
  - [x] dispatches.py
  - [x] job_bids.py
- [x] ~50 endpoints added

### Weeks 26-27: Phase 7 Frontend UI ✅
- [x] DispatchFrontendService with time-aware logic
- [x] BooksFrontendService
- [x] dispatch_frontend router (15 routes + 5 partials)
- [x] books_frontend router
- [x] 13 pages created
- [x] 15 HTMX partials created
- [x] Sidebar navigation activated

### Week 28: Migration & Test Cleanup ✅
- [x] Phase 7 migration applied (6 tables)
- [x] `db` fixture alias added
- [x] Test fixtures updated
- [x] 89 → 16 errors reduced

### Week 29: Test Stabilization ✅
- [x] Enum value fixes (Bug #028)
- [x] Audit log column fixes (Bug #027)
- [x] Phase 7 model test PostgreSQL compatibility
- [x] 86.6% → 90.9% pass rate

### Week 30: Bug #029 Field Name Fix ✅
- [x] 14 field name corrections in dispatch_frontend_service.py
- [x] 507 → 517 passing tests
- [x] 90.9% → 92.7% pass rate
- [x] Bug #029 documented

### Week 31: Close the Loops 📋
- [ ] Category 4: Dues test cleanup (+4 tests → 93.4%)
- [ ] Dispatch template investigation (3 remaining failures)
- [ ] Hub documentation generation (this checklist, roadmap, README)
- [ ] Phase 7a-7g instruction framework

### Sub-Phases 7a-7g — ⏸️ BLOCKED/PLANNED

| Sub-Phase | Focus | Hours | Status |
|-----------|-------|-------|--------|
| 7a | Data Collection (3 LaborPower exports) | 3-5 | ⛔ Blocked (LaborPower access) |
| 7b | Schema Finalization (DDL, migrations) | 10-15 | Ready when 7a complete |
| 7c | Core Services + API (14 business rules) | 25-35 | Waiting on 7b |
| 7d | Import Tooling (CSV pipeline) | 15-20 | Parallel with 7c |
| 7e | Frontend UI (dispatch board, web bidding) | 20-30 | Waiting on 7c |
| 7f | Reports P0+P1 (49 critical/high) | 20-30 | Waiting on 7c |
| 7g | Reports P2+P3 (29 medium/low) | 10-15 | Waiting on 7f |

---

## Phase 8: Square Payment Migration — 📋 PLANNED

**Owner:** Spoke 3: Infrastructure (when created)
**Trigger:** After Phase 7 stabilizes
**Reference:** ADR-018

- [ ] Phase A: Online Payments (Square Web Payments SDK)
- [ ] Phase B: Terminal/POS Integration
- [ ] Phase C: Invoice Generation
- [ ] Remove Stripe skip markers from tests
- [ ] Archive Stripe code

---

## Test Categories Remaining

| Category | Failures | Status | Effort |
|----------|----------|--------|--------|
| Cat 4: Dues Tests | 4 | 🎯 Quick Win | 15 min |
| Dispatch Templates | 3 | Investigate | 1-2 hrs |
| Cat 5: Referral Frontend | 5 | Mixed | 2-3 hrs |
| Cat 3: Member Notes API | 5 | Refactor | 2-3 hrs |
| Cat 2: Phase 7 Models | 13 | Flaky | 3-5 hrs |
| Cat 6: Stripe (skipped) | 27 | Parked | — |

---

## Documentation Tasks

- [ ] Update CLAUDE.md to v5.1 (post-Week 31)
- [ ] Generate Phase 7a-7g instruction doc framework
- [ ] Create ADR-017 (Schema Drift Prevention)
- [ ] Archive Week 28-30 temp files

---

*UnionCore Milestone Checklist — v2.0 — February 5, 2026*
```

---

## Phase 4: Generate IP2A_BACKEND_ROADMAP_v4.md

**Deploys to:** `docs/IP2A_BACKEND_ROADMAP.md`
**Purpose:** Narrative development plan with phase descriptions and milestones

Create file `docs/IP2A_BACKEND_ROADMAP.md` with the following content:

```markdown
# UnionCore Backend Roadmap

**Document Purpose:** Master development plan with phases, milestones, and strategic context
**Version:** v4.0
**Last Updated:** February 5, 2026
**Project Version:** v0.9.8-alpha

---

## Executive Summary

UnionCore is a comprehensive union management platform for IBEW Local 46, replacing three fragmented legacy systems (LaborPower, Access Database, manual processes) with a unified, auditable system. QuickBooks integration is maintained for accounting (sync-don't-replace philosophy).

| Metric | Value |
|--------|-------|
| **Users** | ~4,000 external (members, stewards, applicants) + ~40 internal (staff, officers) |
| **Tests** | 593 total (517 passing, 92.7% pass rate) |
| **Endpoints** | ~228+ |
| **Models** | 32 (26 core + 6 Phase 7) |
| **ADRs** | 18 |
| **Deployment** | Railway (live) |

### Phase Overview

| Phase | Description | Status | Owner |
|-------|-------------|--------|-------|
| 1-4 | Core Platform (Members, Auth, Training, Dues) | ✅ Complete | Spoke 1 |
| 5 | Access DB Migration | ⏸️ Blocked | Spoke 1 |
| 6 | Frontend (Weeks 1-19) | ✅ Complete | Spoke 3 |
| 7 | Referral & Dispatch | 🔄 In Progress | Spoke 2 |
| 8 | Square Payment Migration | 📋 Planned | Spoke 3 |

---

## Hub/Spoke Development Model

UnionCore uses a Hub/Spoke model for development planning. This is an organizational structure for Claude AI conversations, not a code architecture pattern.

### Project Assignments

| Project | Scope | Phases |
|---------|-------|--------|
| **Hub** | Strategy, architecture, ADRs, cross-cutting decisions | All |
| **Spoke 2: Operations** | Dispatch/Referral, Pre-Apprenticeship, SALTing | Phase 7 |
| **Spoke 1: Core Platform** | Members, Dues, Employers, Training | Phases 1-4, 5 |
| **Spoke 3: Infrastructure** | UI, Reports, Deployment, Monitoring | Phase 6, 8 |

### Key Principles

1. **CLAUDE.md is the single source of truth** for project state
2. **Claude Code executes all instruction documents** regardless of source Spoke
3. **Sprint weeks ≠ calendar weeks** — at 5-10 hrs/week, each sprint takes 1-2 calendar weeks
4. **Handoff notes bridge Spokes** since Claude cannot access cross-project conversations

---

## Governance Philosophy

**"The Schema is Law"** — data accuracy, auditability, and production safeguards above all else.

- 7-year NLRA record retention requirement
- All member data changes logged with who/what/when/old-value/new-value
- Audit logs are IMMUTABLE (no UPDATE or DELETE, ever)
- Two-tier logging: PostgreSQL for business audit, Grafana+Loki for operational monitoring
- Defense-in-depth security with JWT authentication and RBAC

---

## Phases 1-4: Core Platform — ✅ COMPLETE

### Phase 1: Organization & Members
- Organization, Member, Employment, MemberClassification models
- CRUD services and API endpoints
- Member search and filtering
- Employment history tracking

### Phase 2: Authentication & RBAC
- JWT with bcrypt password hashing
- Access tokens (15 min) + refresh tokens (7 days)
- Role hierarchy (Admin → Officer → Staff → Organizer → Instructor → Member → Applicant)
- Permission matrix enforcement
- Account lockout and password history

### Phase 3: Union Operations
- SALTing campaigns and contacts
- Benevolence Fund applications and disbursements
- Grievance filing and workflow
- Status tracking and audit trails

### Phase 4: Training Module
- Student enrollment and cohort management
- Course catalog and scheduling
- Grade recording and certificate generation
- Attendance tracking
- FERPA-adjacent access controls

### Phase 4b: Documents
- MinIO (dev) / S3 (prod) object storage
- Presigned URLs for secure access
- Lifecycle management tiers
- Entity-organized file structure (members/, students/, grievances/, grants/)

### Phase 4c: Dues
- Dues rates by member classification
- Dues periods (monthly/quarterly)
- Payment recording and tracking
- Adjustment workflow (waivers, credits, refunds)
- Overdue notifications

---

## Phase 5: Access DB Migration — ⏸️ BLOCKED

**Blocker:** Stakeholder approval pending for Market Recovery data access

### Strategy
- Frame UnionCore as complementary, not replacement
- Demonstrate proof-of-concept with test data before requesting production access
- Protect Access Database owner's role (her system, her baby)

### Tasks (When Unblocked)
1. Export Market Recovery data from Access
2. Map schema to UnionCore models
3. Build import pipeline
4. Validate and reconcile
5. Parallel run period
6. Cutover

---

## Phase 6: Frontend — ✅ COMPLETE

### Technology Stack
- Jinja2 templates (server-side rendering)
- HTMX (dynamic interactions without JavaScript complexity)
- Alpine.js (micro-interactions: dropdowns, toggles)
- Tailwind CSS + DaisyUI (styling via CDN, no build step)

### Weeks 1-19 Summary
| Week | Focus | Tests |
|------|-------|-------|
| 1 | Setup + Login | 10 |
| 2 | Auth Cookies + Dashboard | 8 |
| 3 | Staff Management | 18 |
| 4 | Training Landing | 19 |
| 5 | Members Landing | 15 |
| 6 | Union Operations | 21 |
| 8 | Reports & Export | 30 |
| 9 | Documents Frontend | 6 |
| 10 | Dues UI | 37 |
| 11 | Audit UI + Stripe | 15 |
| 12 | Profile & Settings | 8 |
| 14 | Grant Compliance | 12 |
| 16 | Production Hardening | 32 |
| 18 | Mobile PWA | 14 |
| 19 | Analytics Dashboard | 19 |

---

## Phase 7: Referral & Dispatch — 🔄 IN PROGRESS

**Owner:** Spoke 2: Operations
**Scope:** Replace LaborPower with modern, auditable dispatch system
**Estimated Total:** 100-150 hours across sub-phases 7a-7g

### What Phase 7 Replaces

LaborPower is the legacy dispatch system managing:
- Out-of-work registration lists (11 books)
- Labor request intake from employers
- Morning referral processing
- Web/email bidding
- Check mark (penalty) tracking
- Dispatch history

### Completed Work (Weeks 20-30)

**Models (6 new tables):**
- ReferralBook — Book definitions with contract codes and agreement types
- BookRegistration — Member out-of-work entries with APN (DECIMAL(10,2))
- LaborRequest — Employer labor requests with lifecycle management
- Dispatch — Referral transactions linking all entities
- JobBid — Internet bidding records
- RegistrationActivity — Audit trail for registration changes

**Services (7):**
- ReferralBookService, BookRegistrationService, LaborRequestService
- DispatchService, JobBidService, RegistrationActivityService
- DispatchBusinessRulesService (14 business rules)

**API Routers (5):**
- referral_books.py, book_registrations.py, labor_requests.py
- dispatches.py, job_bids.py
- ~50 new endpoints

**Frontend (13 pages, 15 partials):**
- Dispatch dashboard with live stats
- Labor request list and detail views
- Morning referral processing page with time guards
- Active dispatches tracking
- Queue management with book tabs
- Enforcement dashboard (suspensions, violations)

**Migration:**
- Phase 7 Alembic migration applied (6 tables)
- All relationships verified

### Business Rules Implemented (14)

| # | Rule | Implementation |
|---|------|----------------|
| 1 | Office Hours & Regions | Region entities with operating parameters |
| 2 | Morning Referral Order | Wire 8:30 AM → S&C 9:00 AM → Tradeshow 9:30 AM |
| 3 | Labor Request Cutoff | 3 PM for next morning; web bids after 5:30 PM |
| 4 | Agreement Types | PLA/CWA/TERO on requests and books |
| 5 | Registration Rules | One per classification per member |
| 6 | Re-Registration Triggers | Short call, under scale, 90-day, turnarounds |
| 7 | Re-Sign 30-Day Cycle | Automated alert/drop logic |
| 8 | Internet/Email Bidding | 5:30 PM – 7:00 AM window; 2 rejections = 1 year ban |
| 9 | Short Calls | ≤10 days; max 2 per cycle; ≤3 days don't count |
| 10 | Check Marks | 2 allowed, 3rd = rolled off book |
| 11 | No Check Mark Exceptions | Specialty skills, MOU, early starts |
| 12 | Quit or Discharge | Rolled off ALL books; 2-week blackout |
| 13 | Foreperson By Name | Anti-collusion enforcement |
| 14 | Exempt Status | Military, union, salting, medical, jury |

### Sub-Phases 7a-7g (Remaining Work)

| Sub-Phase | Focus | Hours | Status |
|-----------|-------|-------|--------|
| 7a | Data Collection — 3 LaborPower exports | 3-5 | ⛔ Blocked |
| 7b | Schema Finalization — DDL, migrations | 10-15 | Ready when 7a done |
| 7c | Core Services + API — 14 rules, CRUD | 25-35 | After 7b |
| 7d | Import Tooling — CSV pipeline | 15-20 | Parallel with 7c |
| 7e | Frontend UI — dispatch board, bidding | 20-30 | After 7c |
| 7f | Reports P0+P1 — 49 critical reports | 20-30 | After 7c |
| 7g | Reports P2+P3 — 29 lower priority | 10-15 | After 7f |

### LaborPower Report Inventory (~78 reports)

| Priority | Count | Examples |
|----------|-------|----------|
| P0 (Critical) | 16 | Out-of-work lists, dispatch logs |
| P1 (High) | 33 | Registration history, check marks |
| P2 (Medium) | 22 | Analytics, trend reports |
| P3 (Low) | 7 | Projections, ad-hoc queries |

---

## Phase 8: Square Payment Migration — 📋 PLANNED

**Reference:** ADR-018
**Trigger:** After Phase 7 stabilizes
**Rationale:** Square already used at union hall; consolidate payment processing

### Sub-Phases
- **Phase A:** Online Payments (Square Web Payments SDK)
- **Phase B:** Terminal/POS Integration
- **Phase C:** Invoice Generation

### Migration Steps
1. Create Square developer account
2. Implement Square Web Payments SDK
3. Update dues payment flow
4. Migrate existing Stripe webhooks
5. Remove Stripe skip markers from tests
6. Archive Stripe code
7. Update ADR-003 (Auth) and ADR-018

---

## Key Documents Reference

| Document | Location |
|----------|----------|
| Project Context | `CLAUDE.md` |
| Milestone Checklist | `docs/IP2A_MILESTONE_CHECKLIST.md` |
| Phase 7 Consolidated | `docs/phase7/UnionCore_Continuity_Document_Consolidated.md` |
| LaborPower Gap Analysis | `docs/phase7/LABORPOWER_GAP_ANALYSIS.md` |
| Reports Inventory | `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` |
| ADRs | `docs/decisions/ADR-*.md` |

---

## Timeline Expectations

**Developer Context:** Part-time volunteer project, 5-10 hours/week

| Phase | Estimated Duration |
|-------|-------------------|
| Phase 7 completion | 3-4 months |
| Phase 8 (Square) | 1-2 months |
| Full LaborPower parity | 6-8 months |

**Sprint weeks ≠ calendar weeks.** Instruction documents reference "Week 30" etc. as sprint numbers. At 5-10 hrs/week, each sprint takes 1-2 calendar weeks to complete.

---

*UnionCore Backend Roadmap — v4.0 — February 5, 2026*
```

---

## Phase 5: Deploy Files

```bash
# Verify files were created correctly
wc -l docs/README.md docs/IP2A_MILESTONE_CHECKLIST.md docs/IP2A_BACKEND_ROADMAP.md

# Check for any syntax issues (markdown lint if available)
# If markdownlint is installed: markdownlint docs/README.md docs/IP2A_MILESTONE_CHECKLIST.md docs/IP2A_BACKEND_ROADMAP.md
```

---

## Phase 6: Update CLAUDE.md

Update CLAUDE.md with the following changes:

1. **Update TL;DR line** — change "Week 30" to "Week 31" when work is complete
2. **Verify Hub/Spoke section exists** — if not present, the FileOps instructions from the previous thread should have added it
3. **Update Remaining Issues section** — reflect Week 31 work
4. **Update version footer** — to v5.1

---

## Phase 7: Commit

```bash
# Stage all documentation changes
git add docs/README.md docs/IP2A_MILESTONE_CHECKLIST.md docs/IP2A_BACKEND_ROADMAP.md docs/historical/

# Commit with descriptive message
git commit -m "docs: generate Hub documentation suite (Week 31)

- Created docs/README.md v1.0 with Hub/Spoke explainer
- Updated IP2A_MILESTONE_CHECKLIST.md to v2.0 with Weeks 20-30
- Updated IP2A_BACKEND_ROADMAP.md to v4.0 with Phase 7 detail
- Archived old README variants to docs/historical/

All documents aligned to v0.9.8-alpha, 517 passing tests, 92.7% pass rate."

# Push to develop
git push origin develop
```

---

## Verification Checklist

- [ ] `docs/README.md` exists and contains Hub/Spoke section
- [ ] `docs/IP2A_MILESTONE_CHECKLIST.md` updated to v2.0
- [ ] `docs/IP2A_BACKEND_ROADMAP.md` updated to v4.0
- [ ] All three documents reference v0.9.8-alpha
- [ ] All three documents show 517 passing / 92.7% pass rate
- [ ] Old README variants archived to `docs/historical/`
- [ ] Committed and pushed to develop

---

## Acceptance Criteria

- [ ] Three Hub documents generated and deployed
- [ ] Version numbers consistent across all documents
- [ ] Hub/Spoke model explained in all three documents
- [ ] Phase 7 Weeks 20-30 reflected in Checklist and Roadmap
- [ ] Sprint vs calendar week clarification present
- [ ] All documents cross-reference each other correctly

---

*Week 31 Hub Documentation Generation — Claude Code Instructions — February 5, 2026*
