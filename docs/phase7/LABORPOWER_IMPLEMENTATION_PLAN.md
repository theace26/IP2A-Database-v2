# IP2A-Database-v2: LaborPower Feature Parity Implementation Plan

> **Document Created:** February 2, 2026
> **Last Updated:** February 3, 2026
> **Version:** 2.0
> **Status:** Phase 7 Planning — Authoritative Build Schedule
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1-19)

---

## 🎯 Overview

This plan outlines the implementation of features identified in the LaborPower gap analysis to achieve feature parity with the existing IBEW Local 46 member management system. It provides session-level granularity (file trees, test targets, hour estimates) for each implementation phase.

### Current Baseline (v0.9.4-alpha)

| Metric | Value |
|---|---|
| ORM Models | 26 |
| API Endpoints | ~150 |
| Tests | ~470 (~200+ frontend, 165 backend, ~78 production, 25 Stripe) |
| ADRs | 14 |
| Deployment | Railway (prod), Render (backup) |
| Payments | Stripe live (Checkout Sessions + webhooks) |
| Mobile | PWA with offline support and service worker |
| Analytics | Chart.js dashboard with custom report builder |

Week numbering continues from the v0.9.4-alpha feature-complete milestone (Week 19). Phase 7 begins at **Week 20**.

### Related Documents

| Document | Purpose |
|---|---|
| `LABORPOWER_GAP_ANALYSIS.md` | Feature gaps, proposed schemas, priority assessment |
| `PHASE7_REFERRAL_DISPATCH_PLAN.md` | Referral & dispatch system deep-dive |
| `PHASE7_IMPLEMENTATION_PLAN_v2.md` | Broader Phase 7 plan (models, services, API, frontend) |
| `PHASE7_CONTINUITY_DOC.md` | Session-to-session continuity for Phase 7 work |
| `PHASE7_CONTINUITY_DOC_ADDENDUM.md` | Report sprint schedule (Weeks 29-32+), session mandate |
| `LOCAL46_REFERRAL_BOOKS.md` | Referral book seed data and open questions |
| `LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` | Full inventory of ~78 LaborPower reports to replicate |

### Target Completion

- **Core features (Phases 1-6):** ~32 weeks from start (Weeks 20-32)
- **Report sprints:** Weeks 29-32+ (overlaps with Phases 5-6; see Addendum)
- **Estimated Hours:** 160-220 hours total (at ~10 hrs/week)

---

## 📊 New Database Schema Summary

### Entity Relationship Diagram (Text)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DISPATCH / REFERRAL                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  referral_books ────┬──── book_registrations ────── members         │
│       │             │            │                     │             │
│       │             │            ▼                     │             │
│       │             │    registration_activities       │             │
│       │             │                                  │             │
│       └─────────────┴──── dispatches ─────────────────┘             │
│                              │                                       │
│                              ▼                                       │
│                      member_employments (enhanced)                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         FINANCIAL / DUES                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  members ──────── member_financials                                  │
│     │                   │                                            │
│     │                   ▼                                            │
│     ├──────────── member_charges                                     │
│     │                   │                                            │
│     │                   ▼                                            │
│     └──────────── dues_payments (enhanced)                           │
│                        │                                             │
│                        ▼                                             │
│                 Stripe (ADR-013, existing)                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      SKILLS & QUALIFICATIONS                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  members ──┬──── member_skills                                       │
│            ├──── member_conditions                                   │
│            ├──── member_exclusions ──── organizations                │
│            └──── member_qualified_books ──── referral_books          │
│                                                                      │
│  NOTE: Separate from Student/JATC training certifications.           │
│  Member ≠ Student (linked via FK on Student).                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       PENSION & BENEFITS                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  members ──┬──── member_pension                                      │
│            └──── beneficiaries                                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        EARNINGS & HISTORY                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  members ──┬──── member_earnings ──── organizations                  │
│            └──── web_activity_logs                                   │
│                                                                      │
│  NOTE: Extends existing audit_logs (ADR-012) and                     │
│  Sentry/structured logging (ADR-007, Week 16).                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📅 Implementation Phases

### PHASE 1: Out-of-Work List / Dispatch System
**Priority:** 🔴 HIGH
**Duration:** Weeks 20-22 (30-40 hours)
**Dependencies:** None
**Builds on:** Organization/employer model (Week 13), Member model (existing)

#### Week 20: Core Models & Migrations

**Session 20A: Referral Books (4 hrs)**
```
Files to Create:
├── src/db/enums/dispatch_enums.py          # Per convention: enums in src/db/enums/
│   ├── RegistrationAction
│   ├── TermReason
│   ├── DispatchType
│   └── BookType
├── src/models/referral_book.py
├── src/schemas/referral_book.py
├── src/services/referral_book_service.py
├── src/routers/api/referral_books.py
└── alembic/versions/xxx_create_referral_books.py

Seed Data (from LOCAL46_REFERRAL_BOOKS.md):
- WIRE SEATTLE [1, 2]
- WIRE BREMERTON [1, 2]
- WIRE PT ANGELES [1, 2]
- (Sound & Comm, VDV, Residential TBD — see open questions in LOCAL46_REFERRAL_BOOKS.md)
```

**Session 20B: Book Registrations (4 hrs)**
```
Files to Create:
├── src/models/book_registration.py
├── src/schemas/book_registration.py
├── src/services/book_registration_service.py
├── src/routers/api/book_registrations.py
└── alembic/versions/xxx_create_book_registrations.py
```

**Session 20C: Registration Activities (4 hrs)**
```
Files to Create:
├── src/models/registration_activity.py
├── src/schemas/registration_activity.py
├── src/services/registration_activity_service.py
└── alembic/versions/xxx_create_registration_activities.py

NOTE: Integrate with existing audit log infrastructure (ADR-012).
Extend immutability trigger pattern for dispatch-critical records.
```

#### Week 21: Dispatch Workflow

**Session 21A: Dispatch Model (4 hrs)**
```
Files to Create:
├── src/models/dispatch.py
├── src/schemas/dispatch.py
├── src/services/dispatch_service.py
├── src/routers/api/dispatches.py
└── alembic/versions/xxx_create_dispatches.py

Key Features:
- Create dispatch from registration
- Link to employer/worksite (via existing organizations model)
- Track days/hours worked
- Termination workflow
```

**Session 21B: Employment Enhancement (4 hrs)**
```
Files to Modify:
├── src/models/member_employment.py (add dispatch fields)
├── src/schemas/member_employment.py
├── src/services/member_employment_service.py
└── alembic/versions/xxx_enhance_member_employment.py

New Fields:
- employer_code, worksite_code
- dispatch_class, dispatch_skill
- dispatch_date, dispatch_type
- start_rate, term_rate
- days_worked, hours_worked
- term_reason, term_comment
- book_id FK
```

#### Week 22: Dispatch UI & Tests

**Session 22A: Dispatch Frontend (6 hrs)**
```
Files to Create:
├── src/services/dispatch_frontend_service.py
├── src/routers/dispatch_frontend.py
├── src/templates/dispatch/
│   ├── index.html          # Dashboard with queue stats
│   ├── books.html          # List of all books
│   ├── book_detail.html    # Members on specific book
│   ├── register.html       # Add member to book
│   ├── dispatch.html       # Dispatch workflow
│   └── partials/
│       ├── _queue_table.html
│       ├── _registration_form.html
│       └── _dispatch_form.html

Frontend Patterns (per ADR-002, ADR-010):
- HTMX for partial updates (hx-get, hx-post, hx-swap)
- Alpine.js for modals and interactive state
- DaisyUI components (tables, badges, modals)
- Combined service pattern for frontend data assembly
```

**Session 22B: Tests (4 hrs)**
```
Files to Create:
├── src/tests/test_referral_books.py
├── src/tests/test_book_registrations.py
├── src/tests/test_dispatches.py
└── src/tests/test_dispatch_frontend.py

Test Count Target: +40 tests → ~510 total
```

---

### PHASE 2: Enhanced Member Financial Tracking
**Priority:** 🔴 HIGH
**Duration:** Weeks 23-24 (20-25 hours)
**Dependencies:** Phase 1 complete
**Builds on:** DuesPayment model (Week 10, ADR-008), Stripe (Week 11, ADR-013), Analytics (Week 19)

#### Week 23: Financial Models

**Session 23A: Member Financials (4 hrs)**
```
Files to Create:
├── src/models/member_financial.py
├── src/schemas/member_financial.py
├── src/services/member_financial_service.py
└── alembic/versions/xxx_create_member_financials.py

Key Fields:
- basic_paid_thru, work_paid_thru
- account_balance
- init_fee_due, init_fee_paid
- vacation_balance, jury_paid_thru, sick_paid_thru
- deferral_level_401k
```

**Session 23B: Member Charges (4 hrs)**
```
Files to Create:
├── src/models/member_charge.py
├── src/schemas/member_charge.py
├── src/services/member_charge_service.py
├── src/routers/api/member_charges.py
└── alembic/versions/xxx_create_member_charges.py

NOTE: member_charges.payment_id → dues_payments(id) FK.
Outstanding charges can route through Stripe Checkout (ADR-013).
```

**Session 23C: Dues Enhancement (4 hrs)**
```
Files to Modify:
├── src/models/dues_payment.py (add IO codes, batching)
├── src/schemas/dues_payment.py
├── src/services/dues_payment_service.py
└── alembic/versions/xxx_enhance_dues_payments.py

New Fields:
- io_code, receipt_number, check_number
- batch_id, batch_date
- transaction_type, transaction_number
- io_period, activity_code

NOTE: Existing Stripe records will have NULL for these columns.
Stripe payments use stripe_payment_id; LaborPower-style use io_code/batch_id.
Both coexist.
```

#### Week 24: Financial UI & Reporting

**Session 24A: Financial Dashboard (6 hrs)**
```
Files to Create/Modify:
├── src/templates/members/detail.html (add Financial tab)
├── src/templates/members/partials/
│   ├── _financial_summary.html
│   ├── _charges_table.html
│   └── _transaction_history.html
├── src/services/member_frontend_service.py (enhance)

Extends Week 19 analytics with financial visualizations.
```

**Session 24B: Financial Reports (4 hrs)**
```
Files to Create:
├── src/services/financial_report_service.py
├── src/templates/reports/
│   ├── account_balance_report.html
│   └── transaction_history_report.html

Export formats: PDF (WeasyPrint), CSV (openpyxl) — per existing patterns.
```

**Test Count Target:** +25 tests → ~535 total

---

### PHASE 3: Skills & Qualifications
**Priority:** 🟡 MEDIUM
**Duration:** Weeks 25-26 (15-20 hours)
**Dependencies:** None (can run parallel with Phase 2)

> **Important:** Member skills are separate from Student/JATC training certifications. Member is SEPARATE from Student (linked via FK on Student). Do not conflate dispatch qualifications with JATC educational records.

#### Week 25: Skills Models

**Session 25A: Member Skills (4 hrs)**
```
Files to Create:
├── src/db/enums/skill_enums.py
├── src/models/member_skill.py
├── src/schemas/member_skill.py
├── src/services/member_skill_service.py
└── alembic/versions/xxx_create_member_skills.py

Seed Skills:
- Electrical License types
- OSHA certifications
- Signal/Flagging
- First Aid/CPR
- Forklift/Equipment
```

**Session 25B: Conditions & Exclusions (4 hrs)**
```
Files to Create:
├── src/models/member_condition.py
├── src/models/member_exclusion.py
├── src/schemas/member_condition.py
├── src/schemas/member_exclusion.py
├── src/services/member_condition_service.py
├── src/services/member_exclusion_service.py
└── alembic/versions/xxx_create_conditions_exclusions.py
```

**Session 25C: Qualified Books (3 hrs)**
```
Files to Create:
├── src/models/member_qualified_book.py
├── src/schemas/member_qualified_book.py
├── src/services/member_qualified_book_service.py
└── alembic/versions/xxx_create_member_qualified_books.py

NOTE: Depends on referral_books table from Phase 1.
```

#### Week 26: Skills UI

**Session 26A: Skills Frontend (6 hrs)**
```
Files to Create:
├── src/templates/members/partials/
│   ├── _skills_tab.html
│   ├── _conditions_tab.html
│   ├── _exclusions_tab.html
│   └── _qualified_books_tab.html
├── src/routers/member_skills_frontend.py

Frontend Patterns: HTMX + Alpine.js + DaisyUI (per ADR-002, ADR-010).
```

**Test Count Target:** +20 tests → ~555 total

---

### PHASE 4: Pension & Benefits
**Priority:** 🟡 MEDIUM
**Duration:** Weeks 27-28 (25-30 hours)
**Dependencies:** None

#### Week 27: Pension Models

**Session 27A: Pension Tracking (4 hrs)**
```
Files to Create:
├── src/db/enums/pension_enums.py
│   ├── PensionStatus
│   ├── BeneficiaryRelation
│   └── PensionType
├── src/models/member_pension.py
├── src/schemas/member_pension.py
├── src/services/member_pension_service.py
└── alembic/versions/xxx_create_member_pension.py
```

**Session 27B: Beneficiaries (4 hrs)**
```
Files to Create:
├── src/models/beneficiary.py
├── src/schemas/beneficiary.py
├── src/services/beneficiary_service.py
├── src/routers/api/beneficiaries.py
└── alembic/versions/xxx_create_beneficiaries.py
```

#### Week 28: Pension UI

**Session 28A: Pension Frontend (6 hrs)**
```
Files to Create:
├── src/routers/pension_frontend.py
├── src/templates/members/partials/
│   ├── _pension_tab.html
│   ├── _beneficiaries_list.html
│   └── _beneficiary_form.html
├── src/templates/pension/
│   ├── dashboard.html
│   └── reports.html
```

**Test Count Target:** +20 tests → ~575 total

---

### PHASE 5: Earnings & Activity History
**Priority:** 🟢 LOW
**Duration:** Weeks 29-30 (20-25 hours)
**Dependencies:** Phase 2

> **Schedule note:** Weeks 29-30 overlap with Report Sprint 1 (P0 Critical Reports) per the Continuity Doc Addendum. Coordinate session scheduling to avoid conflicts, or interleave report work between earnings sessions.

#### Week 29: Earnings Models

**Session 29A: Earnings History (4 hrs)**
```
Files to Create:
├── src/models/member_earnings.py
├── src/schemas/member_earnings.py
├── src/services/member_earnings_service.py
└── alembic/versions/xxx_create_member_earnings.py
```

**Session 29B: Activity Logging (4 hrs)**
```
Files to Create:
├── src/models/web_activity_log.py
├── src/services/web_activity_service.py
├── src/middleware/activity_logger.py
└── alembic/versions/xxx_create_web_activity_logs.py

NOTE: Supplements existing audit_logs (ADR-012) and Sentry (ADR-007).
Different purpose: user sessions vs. data changes vs. errors.
```

**Session 29C: Import Tools (4 hrs)**
```
Files to Create:
├── scripts/import_earnings.py
├── src/services/earnings_import_service.py
└── docs/guides/EARNINGS_IMPORT.md
```

#### Week 30: Earnings UI

**Session 30A: Earnings Frontend (6 hrs)**
```
Files to Create:
├── src/templates/members/partials/
│   ├── _earnings_tab.html
│   └── _earnings_chart.html           # Extends Chart.js (Week 19)
├── src/templates/admin/
│   └── earnings_import.html
```

**Test Count Target:** +15 tests → ~590 total

---

### PHASE 6: Integration & Polish
**Priority:** 🟢 LOW
**Duration:** Weeks 31-32 (15-20 hours)
**Dependencies:** All previous phases

> **Schedule note:** Weeks 31-32 overlap with Report Sprints 2-3 per the Continuity Doc Addendum. Report work may push Phase 6 completion beyond Week 32.

#### Week 31: Integration

**Session 31A: Workflow Integration (6 hrs)**
- Dispatch → Employment History auto-creation
- Earnings → Dues calculation helpers
- Book registration → Qualified books validation

**Session 31B: Enhanced Reporting (4 hrs)**
```
New Reports:
├── Out-of-Work List by Book
├── Dispatch History Report
├── Member Earnings Annual Summary
├── Pension Status Report
└── Skills Expiration Report

NOTE: These are IP2A-native reports. For LaborPower report parity (~78 reports),
see LABORPOWER_REFERRAL_REPORTS_INVENTORY.md and the report sprint schedule.
```

#### Week 32: Migration & Documentation

**Session 32A: Migration Tools (4 hrs)**
```
Files to Create:
├── scripts/migrate_from_laborpower/
│   ├── export_members.py
│   ├── export_registrations.py
│   ├── export_earnings.py
│   └── import_to_ip2a.py
└── docs/guides/LABORPOWER_MIGRATION.md
```

**Session 32B: Documentation (4 hrs)**
```
Documentation Updates:
├── CLAUDE.md (update with new modules)
├── CONTINUITY.md (add new entities)
├── docs/decisions/ADR-015-dispatch-system.md
├── docs/decisions/ADR-016-member-financials.md
├── docs/decisions/ADR-017-skills-qualifications.md
└── docs/decisions/ADR-018-pension-benefits.md
```

**Test Count Target:** +10 tests → ~600 total

---

### Report Sprints (Weeks 29-32+, per Addendum)

These sprints replicate LaborPower's ~78 referral reports. They overlap with Phases 5-6 and may extend beyond Week 32.

| Sprint | Weeks | Focus | Reports |
|---|---|---|---|
| Sprint 1 | 29-30 | P0 Critical Reports | 16 |
| Sprint 2 | 30-31 | P1 High Priority Reports | 33 |
| Sprint 3 | 32+ | P2/P3 Reports (as time allows) | 29 |

**Report Infrastructure Required:**
- Multi-dimensional filtering (date, book, employer, class, region, demographics)
- PDF export (WeasyPrint — existing)
- CSV export (openpyxl — existing)
- Print-optimized CSS
- Detail/Summary format toggle
- Report navigation UI

See `LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` for the full report inventory.

---

## 📋 New Enum Definitions

All enums follow the project convention: defined in `src/db/enums/`, imported from `src.db.enums`.

```python
# src/db/enums/dispatch_enums.py

class RegistrationAction(str, Enum):
    REGISTER = "register"
    WEB_SIGN_IN = "web_sign_in"
    DEACTIVATED = "deactivated"
    EMPLOY_STATUS_CHANGE = "employ_status_change"
    MANUAL_EDIT = "manual_edit"
    DROPPED = "dropped"
    REACTIVATED = "reactivated"

class TermReason(str, Enum):
    RIF = "rif"                      # Reduction in Force
    QUIT = "quit"
    FIRED = "fired"
    LAID_OFF = "laid_off"
    CONTRACT_END = "contract_end"
    MEDICAL = "medical"
    RETIREMENT = "retirement"
    TRANSFER = "transfer"
    OTHER = "other"

class DispatchType(str, Enum):
    NORMAL = "normal"
    SHORT_CALL = "short_call"
    BY_NAME = "by_name"
    EMERGENCY = "emergency"
    TRANSFER = "transfer"

class BookType(str, Enum):
    BOOK_1 = "book_1"               # Primary/first out
    BOOK_2 = "book_2"               # Secondary
    BOOK_3 = "book_3"               # Tertiary
    APPRENTICE = "apprentice"
    SPECIAL = "special"


# src/db/enums/skill_enums.py

class SkillCategory(str, Enum):
    LICENSE = "license"
    CERTIFICATION = "certification"
    TRAINING = "training"
    EQUIPMENT = "equipment"
    SAFETY = "safety"

class ConditionType(str, Enum):
    MEDICAL = "medical"
    DISCIPLINE = "discipline"
    LEGAL = "legal"
    ADMINISTRATIVE = "administrative"

class ExclusionType(str, Enum):
    EMPLOYER = "employer"
    WORKSITE = "worksite"
    JOB_TYPE = "job_type"


# src/db/enums/pension_enums.py

class PensionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    VESTED = "vested"
    RETIRED = "retired"
    WITHDRAWN = "withdrawn"
    DECEASED = "deceased"

class BeneficiaryRelation(str, Enum):
    SPOUSE = "spouse"
    CHILD = "child"
    PARENT = "parent"
    SIBLING = "sibling"
    DOMESTIC_PARTNER = "domestic_partner"
    TRUST = "trust"
    ESTATE = "estate"
    OTHER = "other"

class PensionType(str, Enum):
    IO_PENSION = "io_pension"       # International Office
    NEBF = "nebf"                   # National Electrical Benefit Fund
    LOCAL = "local"                 # Local pension plan
    ANNUITY = "annuity"
```

---

## 📊 Test Coverage Targets

| Phase | Module | New Tests | Running Total |
|-------|--------|-----------|---------------|
| Current (v0.9.4-alpha) | All existing | — | ~470 |
| Phase 1 | Dispatch/Referral | 40 | ~510 |
| Phase 2 | Financial | 25 | ~535 |
| Phase 3 | Skills | 20 | ~555 |
| Phase 4 | Pension | 20 | ~575 |
| Phase 5 | Earnings | 15 | ~590 |
| Phase 6 | Integration | 10 | ~600 |

**Target:** 600+ tests by end of Phase 6

---

## 🚀 Quick Start for Phase 1

When you're ready to start, copy this into a Claude Code session:

```
I'm working on IP2A-Database-v2. We're implementing Phase 1 of the LaborPower 
feature parity plan - the Out-of-Work List / Dispatch System.

Current task: Session 20A - Create Referral Books model

Please:
1. Create src/db/enums/dispatch_enums.py with RegistrationAction, TermReason, 
   DispatchType, and BookType enums
2. Create src/models/referral_book.py
3. Create src/schemas/referral_book.py  
4. Create src/services/referral_book_service.py
5. Create the Alembic migration
6. Add seed data for Local 46 books (WIRE SEATTLE, WIRE BREMERTON, etc.)

Follow existing project patterns from CLAUDE.md.
```

---

## 📝 End-of-Session Documentation (MANDATORY)

**CRITICAL:** Before completing each implementation session, you MUST:

> **Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.**

### Documentation Checklist

- [ ] `/CHANGELOG.md` — Version bump, changes summary
- [ ] `/CLAUDE.md` — Update with new modules/models
- [ ] `/docs/IP2A_MILESTONE_CHECKLIST.md` — Progress updates
- [ ] `/docs/decisions/ADR-XXX.md` — Create for architectural decisions
- [ ] `/docs/reports/session-logs/YYYY-MM-DD-*.md` — Create session log
- [ ] Scan `/docs/*` for any other relevant documentation updates

See `/docs/standards/END_OF_SESSION_DOCUMENTATION.md` for full checklist.

---

Document Version: 2.0
Last Updated: February 3, 2026
Previous Version: 1.0 (February 2, 2026 — Initial implementation plan from gap analysis)
