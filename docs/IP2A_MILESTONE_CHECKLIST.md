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
