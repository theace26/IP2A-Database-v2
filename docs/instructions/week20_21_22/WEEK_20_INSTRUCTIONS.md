# Week 20 Instructions — Phase 7: Schema Reconciliation & Core Referral Models

> **Document Created:** February 3, 2026
> **Last Updated:** February 3, 2026
> **Version:** 1.0
> **Status:** Active — Ready for implementation
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1–19)
> **Phase:** 7 — Referral & Dispatch System
> **Estimated Hours:** 10–12 hours across 3 sessions

---

## Purpose

This is the **Week 20 instruction document** for IP2A-Database-v2 (UnionCore). Paste this into a new Claude chat session to provide full context for the first week of Phase 7 development. Week 20 is the critical foundation week — all schema decisions made here cascade through Weeks 21–32+.

---

## Project Context

**Project:** IP2A-Database-v2 (UnionCore) — union operations management platform for IBEW Local 46
**What it replaces:** LaborPower (referral/dispatch), Access Database (member records), QuickBooks (dues — sync, not replace)
**Users:** ~40 staff + ~4,000 members
**GitHub:** theace26

### Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, **Flask**, SQLAlchemy 2.x |
| Frontend | **Jinja2 + HTMX + Alpine.js + DaisyUI** (Tailwind CSS) |
| Database | PostgreSQL 16 |
| Deployment | **Railway** (cloud PaaS) |
| Payments | **Stripe** (Checkout Sessions + Webhooks) |
| Monitoring | **Sentry** (NOT Grafana/Loki) |
| PDF Export | WeasyPrint |
| Excel Export | openpyxl |
| PWA | Service Worker (offline support, Week 18) |
| Analytics | Chart.js (Week 19) |
| Testing | pytest (~470 tests) |
| Linting | ruff |

> **⚠️ CRITICAL:** This project uses **Flask** (Blueprints, `request`, `jsonify`, `abort`, `render_template`, `flask run`, port 5000). Do NOT use FastAPI, uvicorn, APIRouter, Depends, HTTPException, or Pydantic `model_dump()`.

### Current Metrics
- ~470 tests, 26 ORM models, ~150 API endpoints, 14 ADRs
- 19 weeks of development (feature-complete)
- Phase 7 is the current focus — Referral & Dispatch system

---

## Working Copy & Workflow

- **Working copy (for Claude sessions):** `D:\OneDrive\Documents\Claude.ai\IP2A-Database-v2\`
- **Live project:** `C:\Users\Xerxes\Projects\IP2A-Database-v2\`
- **Workflow:** Claude outputs files → Xerxes manually copies to live project
- **Branch:** `develop` at v0.9.4-alpha (main needs merge from develop)

---

## Phase 7 Overview

Phase 7 builds the Referral & Dispatch module — the replacement for LaborPower. This is the largest single phase: 12 new database tables, 14 business rules, 11 books, ~843 employers across 8 contract codes, 78 de-duped reports.

**Total Phase 7 estimate:** 100–150 hours across Weeks 20–32+

### Sub-Phases

| Sub-Phase | Weeks | Focus |
|-----------|-------|-------|
| 7a | 20–22 | Core models, enums, seeds, schema |
| 7b | 23–24 | Services (registration, dispatch, queue management) |
| 7c | 25 | API endpoints |
| 7d | 26–28 | Frontend (books, dispatch, reports UI) |
| 7e | 29–30 | P0 Critical Reports (16 reports) |
| 7f | 30–31 | P1 High Priority Reports (33 reports) |
| 7g | 32+ | P2/P3 Reports, integration, polish |

### Blocking Items

**3 Priority 1 data gaps** block full data migration but do NOT block schema/model creation:

| Data Gap | What's Missing | Impact |
|----------|---------------|--------|
| REGLIST with member IDs | Registration list with member identifiers (not just names) | Cannot map registrations to existing Member records |
| RAW DISPATCH DATA | Actual dispatch transaction history | Cannot build migration scripts for historical dispatches |
| EMPLOYCONTRACT | Employer-to-contract-code mapping table | Cannot verify employer seed data completeness |

> **Note:** Schema design, model creation, and service logic can proceed based on the planning documents. The data gaps block the CSV import/migration step, not the code.

---

## Week 20 Scope

Week 20 has **3 sessions** focused on resolving schema conflicts and creating the foundational models.

### Session 20A: Schema Reconciliation & Enums (4 hours)

**This is the most critical session of Phase 7.** Two planning documents propose overlapping but different schemas. ALL decisions made here become the authoritative reference for Weeks 21–32+.

#### The 5 Pre-Implementation Decisions

Before writing ANY model code, resolve these:

**Decision 1: Schema Reconciliation**

Two documents conflict on field names and model structure:

| Aspect | Implementation Plan v2 | Referral & Dispatch Plan |
|--------|----------------------|--------------------------|
| Job Bids | Bid fields embedded in Dispatch model | Separate `JobBid` model |
| ReferralBook fields | `classification`, `referral_start_time`, `internet_bidding_enabled` | `job_class`, `skill_type`, `morning_referral_time`, `allows_online_bidding` |
| Exempt status | On Member model (global) | On BookRegistration model (per-book) |
| Dispatch `employer_id` | Optional (nullable) | Required (nullable=False) |
| Enum file | `phase7_enums.py` | `referral_enums.py` |
| Additional enums | Basic set | Richer set: `NoCheckMarkReason`, `BidStatus`, `JobClass`, `Region` |

**Recommendation:** Use the Referral & Dispatch Plan's more detailed models (separate JobBid, richer enums) as the base, with the Implementation Plan v2's scheduling and integration notes.

**Decision 2: DuesPayment Coexistence**

How should the new `MemberTransaction` model interact with the existing `DuesPayment` model?

- **Option A:** MemberTransaction wraps DuesPayment — new payments create both records
- **Option B:** MemberTransaction replaces DuesPayment — migrate existing data
- **Option C:** Independent — MemberTransaction for LaborPower-era data, DuesPayment for Stripe-era

**Decision 3: Exempt Status Placement**

Where does exempt status live?

- **Option A:** On Member model — simpler, member is globally exempt
- **Option B:** On BookRegistration — more granular, member can be exempt on one book but not another
- **Option C:** Both — `Member.is_exempt` as global flag, `BookRegistration` for per-book overrides

**Decision 4: Referral Book Seed Data**

Open questions from `LOCAL46_REFERRAL_BOOKS.md`:
- Final field naming (resolve during schema reconciliation)
- Book number meaning (priority vs. member type vs. queue)
- Which fields from gap analysis vs. referral books doc to keep
- Grace period days and max days on book values

**Decision 5: RegistrationActivity vs. Dual Audit Pattern**

Should registration state changes be tracked via:
- A dedicated `RegistrationActivity` model (explicit history table)
- The existing audit_logs table (immutable, NLRA 7-year, PostgreSQL trigger)
- Both (RegistrationActivity for domain events, audit_logs for compliance)

#### Session 20A Deliverables

1. **Decision document** — Record all 5 decisions with rationale in `/docs/phase7/PHASE7_SCHEMA_DECISIONS.md`
2. **Enum file** — `src/db/enums/phase7_enums.py` with all Phase 7 enums:

```python
# Expected enums (adjust based on reconciliation decisions):
class BookType(str, Enum):          # inside_wireperson, tradeshow, stockperson, etc.
class BookRegion(str, Enum):        # seattle, bremerton, port_angeles
class RegistrationStatus(str, Enum): # registered, dispatched, resigned, rolled_off, etc.
class RegistrationAction(str, Enum): # register, re_sign, dispatch, resign, roll_off, etc.
class DispatchType(str, Enum):      # normal, short_call, emergency
class DispatchStatus(str, Enum):    # pending, accepted, declined, completed, terminated
class ContractCode(str, Enum):      # WIREPERSON, S_AND_C, STOCKPERSON, LFM, MARINE, TV_AND_APPL, MARKET_RECOVERY, RESIDENTIAL
class BidStatus(str, Enum):         # pending, accepted, declined, expired
class NoCheckMarkReason(str, Enum): # absent, declined, medical, etc.
class JobClass(str, Enum):          # journeyman, apprentice, foreman, general_foreman
```

> **Convention:** All enums go in `src/db/enums/`, import from `src.db.enums`. Follow the established pattern from existing enums.

3. **Alembic migration** — `alembic/versions/xxx_create_phase7_enums.py`

#### Architecture Reminders for Session 20A

- **Member ≠ Student** — `Member` model handles union members (dues, employment). `Student` model handles JATC training. Dispatch qualifications ≠ JATC training. Never merge.
- **`locked_until` datetime** — User model uses `datetime`, NOT boolean `is_locked`. Always reference correctly.
- **Enum convention** — All enums in `src/db/enums/`, import from `src.db.enums`.
- **Seed ordering** — Registry-based pattern. New seeds must register in correct dependency order. See `docs/architecture/diagrams/seeds.mmd`.
- **Audit immutability** — PostgreSQL trigger prevents UPDATE/DELETE on `audit_logs`. NLRA 7-year compliance.
- **APN is DECIMAL(10,2)** — NOT INTEGER. Preserves FIFO ordering from LaborPower.
- **8 contract codes** — WIREPERSON, S&C, STOCKPERSON, LFM, MARINE, TV&APPL, MARKET RECOVERY, **RESIDENTIAL** (the 8th, discovered in Batch 2 analysis).

---

### Session 20B: ReferralBook Model & Seeds (4 hours)

**Prerequisites:** Session 20A decisions are locked.

#### Deliverables

1. **ReferralBook model** — `src/models/referral_book.py`

```python
# Expected fields (finalized in Session 20A):
class ReferralBook(Base):
    __tablename__ = "referral_books"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]                    # "Wire Seattle", "Tradeshow Seattle", etc.
    code: Mapped[str]                    # "WIRE_SEA_1", "TRADE_SEA_1", etc. (unique)
    classification: Mapped[BookType]     # inside_wireperson, tradeshow, etc.
    book_number: Mapped[int]             # 1 = Book 1, 2 = Book 2
    region: Mapped[BookRegion]           # seattle, bremerton, port_angeles
    referral_start_time: Mapped[time]    # 08:30:00, 09:00:00, etc.
    internet_bidding_enabled: Mapped[bool] = mapped_column(default=False)
    max_days_on_book: Mapped[Optional[int]]     # Max days before roll-off
    re_sign_days: Mapped[Optional[int]]         # Days allowed to re-sign
    grace_period_days: Mapped[Optional[int]]    # Grace period after roll-off
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    # Relationships
    registrations: Mapped[list["BookRegistration"]] = relationship(back_populates="book")
```

2. **ReferralBook schema** — `src/schemas/referral_book.py` (Marshmallow or similar, following existing patterns)

3. **Seed data** — `src/seed/phase7_seed.py`

Known books from LaborPower analysis (11 confirmed books across 3 regions):

| Classification | Seattle | Bremerton | Port Angeles | Books |
|---------------|---------|-----------|--------------|-------|
| Inside Wireperson | Book 1, 2 | Book 1, 2 | Book 1, 2 | 6 |
| Tradeshow | Book 1 | — | — | 1 |
| Stockperson | Book 1 | — | — | 1 |
| Technician | Book 1 | — | — | 1 |
| Utility Worker | Book 1 | — | — | 1 |
| TERO Apprentice Wire | Book 1 | — | — | 1 |

> **Seed ordering:** Must register in the existing registry-based ordering system. See `docs/architecture/diagrams/seeds.mmd`.

4. **Alembic migration** — `alembic/versions/xxx_create_referral_books.py`

5. **Tests** — `src/tests/test_referral_books.py`

Target: +8–10 tests for model CRUD, seed verification, unique constraint on `code`.

---

### Session 20C: BookRegistration Model (4 hours)

**Prerequisites:** ReferralBook model complete with seeds.

#### Deliverables

1. **BookRegistration model** — `src/models/book_registration.py`

```python
# Expected fields:
class BookRegistration(Base):
    __tablename__ = "book_registrations"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    book_id: Mapped[int] = mapped_column(ForeignKey("referral_books.id"))
    registration_number: Mapped[Decimal]    # APN — DECIMAL(10,2), NOT integer
    status: Mapped[RegistrationStatus]      # registered, dispatched, resigned, etc.
    registered_at: Mapped[datetime]
    re_sign_date: Mapped[Optional[datetime]]
    roll_off_date: Mapped[Optional[datetime]]
    has_check_mark: Mapped[bool] = mapped_column(default=True)
    no_check_mark_reason: Mapped[Optional[NoCheckMarkReason]]
    check_mark_restored_at: Mapped[Optional[datetime]]
    is_exempt: Mapped[bool] = mapped_column(default=False)  # If Decision 3 = Option B or C
    exempt_reason: Mapped[Optional[str]]
    notes: Mapped[Optional[str]]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    # Relationships
    member: Mapped["Member"] = relationship()
    book: Mapped["ReferralBook"] = relationship(back_populates="registrations")
    activities: Mapped[list["RegistrationActivity"]] = relationship(back_populates="registration")  # If Decision 5 includes this
```

> **CRITICAL:** `registration_number` (APN) is `DECIMAL(10,2)`, NOT `Integer`. This preserves FIFO ordering from LaborPower where APNs like 1234.01 and 1234.02 represent separate entries.

2. **BookRegistration schema** — `src/schemas/book_registration.py`

3. **Alembic migration** — `alembic/versions/xxx_create_book_registrations.py`

4. **Tests** — `src/tests/test_book_registrations.py`

Target: +10–12 tests for registration CRUD, APN decimal handling, status transitions, FK constraints.

---

## Key Business Rules Reference

These rules come from the 14 business rules in the LaborPower Referral Procedures document. They inform the model design but are fully implemented in the service layer (Week 23+).

| Rule | Summary |
|------|---------|
| Registration | Members sign the appropriate out-of-work list (book) upon becoming unemployed |
| Re-sign | Members must re-sign within the allowed period or be rolled off |
| Check Marks | Members must maintain daily check marks; 3 missed = removal from book |
| Short Calls | Jobs ≤3 days; member returns to original position on book after completion |
| Online Bidding | Members can bid on jobs online during designated windows |
| Quit/Discharge | Different re-registration rules for voluntary quit vs. employer discharge |
| Exempt Status | Certain members exempt from check mark requirements (medical, union business, etc.) |
| Foreman Dispatch | Foremen dispatched separately; employer may request specific foremen |
| Tier System | Book 1 members dispatched before Book 2 (NOTE: LaborPower had INVERTED tiers — verify with dispatch staff) |
| TERO/PLA/CWA | Special dispatch categories with their own rules |

---

## Integration Points with Existing System

These Week 1–19 features are already built and available for Phase 7 to use:

| Feature | How Phase 7 Uses It |
|---------|-------------------|
| Member model (Week 2) | FK from BookRegistration → Member |
| Authentication (Week 3) | Staff-only access to dispatch operations |
| Audit logging (Week 11) | Immutable audit trail for all dispatch actions |
| Stripe (Week 11) | Future: online payment of registration fees if applicable |
| WeasyPrint (Week 14) | PDF export for all 78 reports |
| openpyxl (Week 14) | Excel export for registration lists |
| HTMX + Alpine.js (all weeks) | Frontend patterns for dispatch UI |
| DaisyUI components | Tables, badges, modals, steps for workflow UI |
| PWA (Week 18) | Offline access to book status for dispatchers |
| Chart.js (Week 19) | Analytics dashboards for dispatch metrics |
| Sentry (ADR-007) | Error monitoring and performance tracking |

---

## Related Documents

| Document | Location |
|----------|----------|
| Phase 7 Continuity Doc | `/docs/phase7/PHASE7_CONTINUITY_DOC.md` |
| Phase 7 Continuity Addendum | `/docs/phase7/PHASE7_CONTINUITY_DOC_ADDENDUM.md` |
| Implementation Plan v2 | `/docs/phase7/PHASE7_IMPLEMENTATION_PLAN_v2.md` |
| Referral & Dispatch Plan | `/docs/phase7/PHASE7_REFERRAL_DISPATCH_PLAN.md` |
| LaborPower Gap Analysis | `/docs/phase7/LABORPOWER_GAP_ANALYSIS.md` |
| LaborPower Implementation Plan | `/docs/phase7/LABORPOWER_IMPLEMENTATION_PLAN.md` |
| Referral Reports Inventory | `/docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` |
| Local 46 Referral Books | `/docs/phase7/LOCAL46_REFERRAL_BOOKS.md` |
| Backend Roadmap v3.0 | `/docs/IP2A_BACKEND_ROADMAP.md` |
| Milestone Checklist | `/docs/IP2A_MILESTONE_CHECKLIST.md` |
| ADR-008: Dues Tracking | `/docs/decisions/ADR-008-dues-tracking.md` |
| ADR-012: Audit Logging | `/docs/decisions/ADR-012-audit-logging.md` |
| ADR-013: Stripe Integration | `/docs/decisions/ADR-013-stripe-integration.md` |

---

## Session Checklist

### Before Starting Each Session

- [ ] Verify you're on the `develop` branch
- [ ] Run existing tests: `pytest` (all ~470 should pass)
- [ ] Check `ruff` for any pre-existing lint issues

### After Completing Each Session

- [ ] All new tests pass
- [ ] All existing tests still pass
- [ ] `ruff` reports no new issues
- [ ] Alembic migration runs cleanly (`alembic upgrade head`)

### Week 20 Completion Criteria

- [ ] All 5 pre-implementation decisions documented
- [ ] Phase 7 enums created and tested
- [ ] ReferralBook model, schema, migration, and seeds complete
- [ ] BookRegistration model, schema, and migration complete
- [ ] +20–25 new tests → ~490–495 total
- [ ] All documentation updated per end-of-session rule

---

## End-of-Session Documentation (MANDATORY)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.

**Minimum updates per session:**
- `/CHANGELOG.md` — version bump and changes
- `/CLAUDE.md` — update with progress
- `/docs/IP2A_MILESTONE_CHECKLIST.md` — check off completed items
- `/docs/phase7/PHASE7_CONTINUITY_DOC.md` — update Session Log table
- Session log in `/docs/reports/session-logs/YYYY-MM-DD-*.md`
- Any affected ADRs (likely ADR-015 for Phase 7 architecture decisions)

---

## Known Pitfalls (Carry Forward)

- ❌ FastAPI / uvicorn / APIRouter → ✅ **Flask / flask run / Blueprints**
- ❌ Grafana / Loki → ✅ **Sentry** (ADR-007)
- ❌ Missing DaisyUI references → ✅ Always mention DaisyUI with frontend stack
- ❌ `is_locked` → ✅ `locked_until` (datetime, not boolean)
- ❌ 7 contract codes → ✅ **8** (RESIDENTIAL is the 8th)
- ❌ 80–120 hrs Phase 7 → ✅ **100–150 hrs**
- ❌ Week 15 "missing" → ✅ Intentionally skipped (14→16)
- ❌ APN as INTEGER → ✅ **DECIMAL(10,2)** — preserves FIFO ordering
- ❌ LaborPower tier ordering → ✅ **INVERTED** in LaborPower — verify with dispatch staff

---

*Document Version: 1.0*
*Last Updated: February 3, 2026*
*Week 20 of IP2A-Database-v2 (UnionCore) — Phase 7: Referral & Dispatch*
