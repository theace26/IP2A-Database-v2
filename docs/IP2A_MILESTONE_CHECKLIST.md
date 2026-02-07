# UnionCore Milestone Checklist

**Document Purpose:** Actionable task tracking by phase and week
**Version:** v3.0
**Last Updated:** February 6, 2026
**Project Version:** v0.9.10-alpha

---

## Quick Stats

| Metric | Value |
|--------|-------|
| Tests | 764 total (~720-730 passing, ≥95% pass rate) |
| Endpoints | ~320+ (260 baseline + 62 Phase 7) |
| Models | 32 (26 core + 6 Phase 7) |
| ADRs | 18 |
| Frontend Weeks | 1-19 complete |
| Phase 7 Weeks | 20-42 complete (5 of 7 sub-phases) |
| Phase 7 Reports | 85 implemented (14 P0, 30 P1, 31 P2, 10 P3) |

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

### Week 31: Close the Loops ✅
- [x] Hub documentation generation (checklist, roadmap, README)
- [x] Phase 7a-7g instruction framework

### Weeks 32-34: Reports Sprint ✅
- [x] Out-of-Work List Reports (4 P0 reports)
- [x] Dispatch & Labor Request Reports (5 P0 reports)
- [x] Employer & Registration Reports (5 P0/P1 reports)
- [x] 14 of 78 reports complete

### Week 35: Stripe Removal & Bug Squash ✅
- [x] Session 35A: Stripe code removal (ADR-018)
- [x] Removed 27 Stripe tests
- [x] Session 35B: Bug squash (fixture + schema drift fixes)
- [x] 92.7% → 98.5% pass rate achieved
- [x] Documentation reconciliation

### Weeks 40-42: P2+P3 Reports (Sub-phase 7g) ✅
- [x] 31 P2 reports implemented (analytics, trends, utilization)
- [x] 10 P3 reports implemented (projections, forecasts, ad-hoc)
- [x] 38 P2+P3 report tests created
- [x] Total: 85 reports across all priorities
- [x] Version: v0.9.16-alpha

### Week 43: Test Validation 🔄
- [x] Dispatch.bid relationship bug verified (already fixed)
- [ ] Full test suite baseline run
- [ ] Test failures categorized and fixed/skipped
- [ ] ≥98% pass rate target

### Week 44: Phase 7 Close-Out 🔄
- [x] Phase 7 Retrospective created
- [x] Spoke 1 Onboarding Context Document created (CRITICAL)
- [x] Report inventory updated with implementation status
- [x] Milestone checklist updated (this file)
- [ ] Backend roadmap updated
- [ ] CLAUDE.md updated to v0.9.18-alpha
- [ ] CHANGELOG.md updated

### Sub-Phases 7a-7g — 5 of 7 COMPLETE

| Sub-Phase | Focus | Hours | Status | Completed |
|-----------|-------|-------|--------|-----------|
| 7a | Data Collection (3 LaborPower exports) | 3-5 | ⛔ BLOCKED (LaborPower access) | — |
| 7b | Schema Finalization (DDL, migrations) | 10-15 | ✅ COMPLETE | Weeks 20-21 |
| 7c | Core Services + API (14 business rules) | 25-35 | ✅ COMPLETE | Weeks 22-25 |
| 7d | Import Tooling (CSV pipeline) | 15-20 | ⛔ BLOCKED (depends on 7a) | — |
| 7e | Frontend UI (dispatch board, web bidding) | 20-30 | ✅ COMPLETE | Weeks 26-28, 32 |
| 7f | Reports P0+P1 (44 critical/high) | 20-30 | ✅ COMPLETE | Weeks 33-34 |
| 7g | Reports P2+P3 (41 medium/low) | 10-15 | ✅ COMPLETE | Weeks 40-42 |

**Summary:**
- ✅ **5 of 7 sub-phases COMPLETE** (7b, 7c, 7e, 7f, 7g)
- ⛔ **2 of 7 sub-phases BLOCKED** (7a, 7d) — LaborPower data access required
- 📊 **85 reports implemented** across P0-P3 tiers
- 🧪 **82 new report tests** (44 P0/P1 + 38 P2/P3)
- 📈 **+294 tests** total Phase 7 contribution (+62%)

---

## Phase 8: Square Payment Migration — 📋 PLANNED

**Owner:** Spoke 1 (Core Platform)
**Trigger:** Weeks 47-49 (after demo prep)
**Reference:** ADR-018

### Phase 8 Preparation ✅
- [x] Stripe code removed (Week 35)
- [x] Stripe tests skip-marked (27 tests)
- [x] ADR-018 created and updated
- [x] Spoke 1 Onboarding Context Document created (Week 44)

### Phase 8A: Online Payments (Weeks 47-49) — 📋 Ready to Start
- [ ] Week 47: Square SDK + SquarePaymentService
- [ ] Week 48: Square API router + frontend integration
- [ ] Week 49: Tests (15-20 mocked) + Phase 8A close-out

### Phase 8B-C: Future
- [ ] Phase B: Terminal/POS Integration (not yet scoped)
- [ ] Phase C: Invoice Generation (not yet scoped)

---

## Test Categories Remaining

| Category | Failures | Status | Effort |
|----------|----------|--------|--------|
| Flaky/Fixture Tests | ~8 | ⏸️ Skipped (legitimate) | — |
| Infrastructure-Dependent | ~8 | ⏸️ Skipped (S3/setup) | — |
| Remaining Failures | ~9 | Investigate | 2-3 hrs |

**Pass Rate:** 98.5% (596/606 non-skipped tests) — Week 35 target exceeded

---

## Documentation Tasks

- [x] Update CLAUDE.md to v0.9.10-alpha (Week 35)
- [x] Generate Phase 7a-7g instruction doc framework
- [x] Create ADR-017 (Schema Drift Prevention)
- [x] Archive Week 28-30 temp files
- [x] Week 35 session log created
- [x] ADR-018 updated with Stripe removal

---

*UnionCore Milestone Checklist — v3.0 — February 6, 2026*
