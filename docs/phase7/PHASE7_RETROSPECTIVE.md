# Phase 7 Retrospective: Referral & Dispatch System

> **Phase Duration:** Weeks 20–42 (approximately 22-24 calendar weeks at 5-10 hrs/week)
> **Effort:** ~100-150 hours estimated, ~120-140 hours actual
> **Sub-phases Completed:** 5 of 7 (7b, 7c, 7e, 7f, 7g)
> **Final Report Count:** 85 implemented (14 P0, 30 P1, 31 P2, 10 P3)
> **Version Progress:** v0.9.4-alpha → v0.9.16-alpha

---

## What Was Delivered

### Sub-Phase 7b: Schema Foundation (Weeks 20-21)

**Models Created (6):**
- `ReferralBook` — Out-of-work book definitions
- `BookRegistration` — Member registrations with APN (DECIMAL(10,2))
- `RegistrationActivity` — Append-only audit trail
- `LaborRequest` — Employer job requests
- `JobBid` — Member bid tracking
- `Dispatch` — Central dispatch records

**Enums Created (19):**
- BookClassification, BookRegion, RegistrationStatus, RegistrationAction
- ExemptReason, RolloffReason, NoCheckMarkReason
- LaborRequestStatus, BidStatus, DispatchMethod, DispatchStatus, DispatchType
- TermReason, JobClass, MemberType, ReferralStatus
- ActivityCode, PaymentSource, AgreementType

**Key Decisions:**
- APN as DECIMAL(10,2) not INTEGER (critical finding from data analysis)
- Separate JobBid model for cleaner audit trail
- Per-book exempt status for flexibility
- Dual audit pattern (RegistrationActivity + audit_logs)

### Sub-Phase 7c: Core Services + API (Weeks 22-25)

**Services Created (7):**
- `ReferralBookService` — Book CRUD, stats, settings
- `BookRegistrationService` — Registration, check marks, roll-off logic
- `LaborRequestService` — Rules 2,3,4,11 enforcement
- `JobBidService` — Rule 8 enforcement
- `DispatchService` — Rules 9,12,13 enforcement
- `QueueService` — Queue snapshots, next-eligible, wait estimation
- `EnforcementService` — Batch processing (re-sign, expired cleanup)

**API Routers Created (5):**
- `referral_books_api.py` — ~12 endpoints
- `registration_api.py` — ~12 endpoints
- `labor_request_api.py` — ~12 endpoints
- `job_bid_api.py` — ~10 endpoints
- `dispatch_api.py` — ~16 endpoints

**Business Rules Implemented (14):**
| Rule | Description | Services |
|------|-------------|---------|
| 1 | Office Hours & Regions | Region entities with operating parameters |
| 2 | Morning Referral Processing Order | LaborRequestService |
| 3 | 3 PM Cutoff | LaborRequestService |
| 4 | Agreement Types (PLA/CWA/TERO) | LaborRequestService |
| 5 | Registration Rules | BookRegistrationService |
| 6 | Re-Registration Triggers | BookRegistrationService |
| 7 | Re-Sign 30-Day Cycle | BookRegistrationService |
| 8 | Internet/Email Bidding | JobBidService |
| 9 | Short Calls | DispatchService |
| 10 | Check Marks (Penalty) | BookRegistrationService |
| 11 | No Check Mark Exceptions | LaborRequestService |
| 12 | Quit or Discharge | DispatchService |
| 13 | Foreperson By Name | DispatchService |
| 14 | Exempt Status | BookRegistrationService |

### Sub-Phase 7e: Frontend UI (Weeks 26-28, 32)

**Frontend Services Created (2):**
- `ReferralFrontendService` — Book/registration data
- `DispatchFrontendService` — Time-aware dispatch workflow

**Frontend Routers Created (2):**
- `referral_frontend.py` — 17 routes
- `dispatch_frontend.py` — 11 routes

**Templates Created (10 pages + 15 partials):**

**Referral Pages:**
- Landing page with stats cards
- Books list with filters
- Book detail with queue table
- Registrations list (cross-book)
- Registration detail with history

**Dispatch Pages:**
- Dashboard with live stats
- Labor request list
- Morning referral page (critical daily workflow)
- Active dispatches with short call tracking
- Queue management by book
- Enforcement dashboard

**HTMX Partials:** 15 partials for dynamic updates

**Tests:** 51 frontend tests (22 referral + 29 dispatch)

### Sub-Phase 7f: P0+P1 Reports (Weeks 33-34)

**Report Service:** `ReferralReportService` created

**P0 Reports Implemented (14):**
- Out-of-work lists (by book, all books)
- Morning referral sheet
- Daily dispatch log
- Open labor requests
- Active dispatches
- Re-sign reminder lists
- Check mark tracking
- Employer active list
- (Full list in report inventory)

**P1 Reports Implemented (30):**
- Registration history
- Dispatch summaries by period
- Member dispatch history
- Employer utilization
- Check mark history
- Exemption tracking
- (Full list in report inventory)

**Tests:** 44 P0+P1 report tests

### Sub-Phase 7g: P2+P3 Reports (Weeks 40-42)

**P2 Reports Implemented (31):**
- Analytics reports
- Trend analysis
- Utilization metrics
- Compliance reports
- (Full list in report inventory)

**P3 Reports Implemented (10):**
- Projections
- Forecasts
- Ad-hoc queries
- Custom reports

**Tests:** 38 P2+P3 report tests

**Total Report Tests:** 82 (44 P0/P1 + 38 P2/P3)

### Data Analysis (Critical Success Factor)

**LaborPower Data Analysis:**
- 24 PDF reports analyzed across 2 batches
- 4,033 registrations across 8 books
- ~843 unique employers across 8 contract codes
- 8 critical schema findings identified BEFORE implementation

**Key Findings:**
1. APN = DECIMAL(10,2), NOT INTEGER
2. Duplicate APNs within books (can't use as unique key)
3. RESIDENTIAL = 8th contract code (not documented)
4. Book Name ≠ Contract Code (e.g., STOCKMAN book → STOCKPERSON contract)
5. TERO APPR WIRE = compound book
6. Cross-regional registration (87% on multiple books)
7. APN 45880.41 on FOUR books simultaneously
8. Inverted tier distributions (Book 3 > Book 1 for some classifications)

**Impact:** These findings prevented costly schema rework that would have required database migrations and code refactoring after implementation.

---

## What Went Well

### 1. Hub/Spoke Model

The Hub/Spoke model enabled parallel planning (Hub) and implementation (Spoke 2) without context-switching overhead. Strategic decisions stayed in Hub, tactical execution in Spoke 2.

### 2. Data-Driven Schema Design

Analyzing 24 LaborPower reports BEFORE coding prevented schema mistakes. The 8 critical findings (especially APN as DECIMAL, not INTEGER) would have been discovered late and required expensive refactoring.

### 3. WeasyPrint Pipeline Established

Week 14's WeasyPrint infrastructure (ADR-014) was reusable for all 85 Phase 7 reports. No additional PDF generation setup required.

### 4. Dual Audit Trail Pattern

Both `RegistrationActivity` (domain-specific) and `audit_logs` (system-wide) provide comprehensive 7-year NLRA compliance without performance overhead.

### 5. Business Rules Codified

Converting the "IBEW Local 46 Referral Procedures" document into 14 testable business rules created clear acceptance criteria and prevented scope creep.

### 6. Test Coverage

82 new report tests + 51 frontend tests + 68 model/service/API tests = ~200 new tests. Phase 7 testing discipline maintained throughout.

### 7. Incremental Delivery

Breaking Phase 7 into 7 sub-phases allowed progress validation at each milestone. Sub-phases 7b/7c/7e/7f/7g each had clear deliverables and acceptance criteria.

---

## What Was Challenging

### 1. LaborPower Access Blocked 7a/7d

Sub-phases 7a (Data Collection) and 7d (Import Tooling) remain blocked waiting for LaborPower data access. This prevented:
- Real data migration testing
- Production data validation
- Import CSV pipeline development

**Resolution:** Week 46 stakeholder demo designed to unblock access.

### 2. Dispatch.bid Relationship Bug

`Dispatch.bid` relationship lacked `foreign_keys=[bid_id]` specification, causing SQLAlchemy to mis-infer the relationship. Blocked ~25 tests.

**Impact:** Discovered late in Week 27, required model fix and test updates.
**Prevention:** Future relationship definitions will always specify `foreign_keys` explicitly.

### 3. Report Count Expansion

Initial estimate: 78 reports (from LaborPower inventory)
Actual delivery: 85 reports (9% increase)

**Cause:** Discovered additional report variants during P2/P3 implementation.
**Impact:** Weeks 40-42 took longer than estimated.

### 4. Field Name Mismatches (Bug #029)

Phase 7 model field names didn't match service layer expectations. 14 field name corrections required across dispatch frontend service.

**Examples:**
- `Dispatch.status` vs `Dispatch.dispatch_status`
- `JobBid.bid_time` vs `JobBid.submitted_at`
- `BookRegistration.book_priority_number` vs `BookRegistration.priority_number`

**Resolution:** Fixed in Week 30 (commit `8480366`)
**Prevention:** Future phases will verify model-service field alignment during schema design.

### 5. Test Suite Stability

Pass rate progression:
- Week 29: 90.9% (507/558 non-skipped tests)
- Week 30: 92.7% (517/558 non-skipped tests)
- Week 43: Target ≥98%

**Challenges:**
- Fixture isolation issues
- Database state leaks between tests
- Unique constraint violations in test data

**Ongoing:** Week 43 stabilization sprint addresses remaining failures.

---

## Blocked Items (Carrying Forward to Future Phases)

### 7a: Data Collection

**Blockers:**
- LaborPower database access not granted
- Need 3 Priority 1 exports: REGLIST, RAW DISPATCH DATA, EMPLOYCONTRACT

**Unblock Path:** Week 46 stakeholder demo → Access DB owner sees working system → Grants data access

### 7d: Import Tooling

**Blockers:**
- Depends on 7a data
- Cannot build CSV pipeline without real data samples
- Cannot test data mapping without production records

**Unblock Path:** 7a completion → Build import scripts → Validate against production data

---

## Lessons for Phase 8 (Square Payment Migration)

### 1. Read Existing Code First

Don't assume patterns from documentation. Always inspect:
- Auth dependency import paths (varies by router)
- Database session dependency names (`db` vs `db_session`)
- Test fixture names in `conftest.py`
- Service constructor patterns

### 2. Verify Cross-Cutting Changes

Changes to `main.py`, `conftest.py`, base templates, and settings affect ALL modules. Always:
- Note cross-cutting changes in session summary
- Test after modifications
- Coordinate with Hub for multi-Spoke impact

### 3. Mock External APIs in Tests

NEVER hit real APIs (Square sandbox, Stripe, etc.) in tests. Always mock. This:
- Speeds up test suite (no network calls)
- Prevents flaky tests (no API downtime)
- Avoids rate limits and costs

### 4. Time-Box Test Fixes

Per Week 43 instructions: 15 minutes per test max. If longer, document as bug and skip-mark. This prevents test debugging from consuming implementation time.

### 5. Database Field Naming

Explicitly specify column names in models when field name differs from DB column:
```python
general_notes = Column("notes", Text)  # Model field ≠ DB column
```

This prevents "column doesn't exist" errors.

---

## Metrics

| Metric | Start of Phase 7 (v0.9.4-alpha) | End of Phase 7 (v0.9.16-alpha) |
|--------|----------------------------------|----------------------------------|
| **Tests** | ~470 | ~764 (+294, +62%) |
| **Passing Tests** | ~450 | ~710-730 (pending Week 43 final) |
| **API Endpoints** | ~178 (26 core + 152 Phase 1-6) | ~320+ (+142, +80%) |
| **Models** | 26 (core + Phase 1-6) | 32 (+6, +23%) |
| **Enums** | ~15 | ~34 (+19, +127%) |
| **ADRs** | 14 | 18 (+4, +29%) |
| **Reports** | 6 (baseline from Week 8/14) | 91 (+85, +1417%) |
| **Frontend Pages** | ~15 (Weeks 1-19) | ~25 (+10, +67%) |
| **Code Version** | v0.9.4-alpha | v0.9.16-alpha (+12 minor versions) |

**Total Phase 7 Additions:**
- 6 models
- 19 enums
- 7 services
- 5 API routers (~62 endpoints)
- 2 frontend routers (~28 routes)
- 10 pages + 15 partials
- 85 reports (14 P0, 30 P1, 31 P2, 10 P3)
- ~200 tests (82 reports + 51 frontend + 68 backend)
- 4 ADRs (ADR-015 through ADR-018)

---

## Phase 7 Sub-Phase Summary

| Sub-Phase | Status | Weeks | Deliverables | Tests |
|-----------|--------|-------|--------------|-------|
| **7a** | ⛔ BLOCKED | N/A | Data collection from LaborPower | N/A |
| **7b** | ✅ COMPLETE | 20-21 | 6 models, 19 enums, schema | 20 |
| **7c** | ✅ COMPLETE | 22-25 | 7 services, 5 API routers, 14 rules | 68 |
| **7d** | ⛔ BLOCKED | N/A | Import tooling, CSV pipeline | N/A |
| **7e** | ✅ COMPLETE | 26-28, 32 | 2 frontend routers, 10 pages, 15 partials | 51 |
| **7f** | ✅ COMPLETE | 33-34 | 44 reports (14 P0 + 30 P1) | 44 |
| **7g** | ✅ COMPLETE | 40-42 | 41 reports (31 P2 + 10 P3) | 38 |

**Completion Rate:** 5/7 (71%) — 2 blocked by external dependency

---

## What's Next

### Immediate: Demo Preparation (Weeks 45-46)

- **Week 45:** Demo environment with seed data
- **Week 46:** Demo script and stakeholder presentation

**Objective:** Demonstrate working dispatch/referral system to:
1. Union leadership (show business value)
2. Access DB owner (request LaborPower data access)
3. IT contractor (show containment and isolation)

**Success Criteria:**
- Access DB owner grants LaborPower data access
- Leadership approves project continuation
- 7a/7d unblocked

### Phase 8A: Square Payment Migration (Weeks 47-49)

**Owner:** Spoke 1 (Core Platform)

- Replace Stripe with Square Web Payments SDK
- Client-side tokenization (PCI compliant)
- SquarePaymentService + API router + frontend
- 15-20 tests (all mocked)

**Blocked Dependencies:** None — independent of Phase 7

### Phase 7 Completion: 7a + 7d (After Demo)

**Owner:** Spoke 2 (Operations)

- 7a: Data collection (3 Priority 1 exports)
- 7d: Import tooling (CSV pipeline)
- Validation against production data
- Data migration testing

**Blocked Until:** Week 46 demo success

---

## Key Takeaways

1. **Data analysis before coding** saved weeks of refactoring
2. **Incremental delivery** kept progress visible and validated
3. **Test discipline** maintained quality throughout long phase
4. **Business rules codified** prevented scope creep
5. **Hub/Spoke model** enabled parallel work without context switching
6. **External dependencies** (LaborPower access) blocked 2 of 7 sub-phases

**Phase 7 Status:** 71% complete, 2 sub-phases blocked by external access

**Next Milestone:** Week 46 stakeholder demo to unblock 7a/7d

---

*Phase 7 Retrospective Document*
*Version: 1.0*
*Created: February 7, 2026*
*Spoke: Spoke 2 (Operations)*
