# Week 21 Instructions — Phase 7: Dispatch Models & Activity Tracking

> **Document Created:** February 3, 2026
> **Last Updated:** February 3, 2026
> **Version:** 1.0
> **Status:** Active — Ready for implementation (after Week 20 completes)
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1–19)
> **Phase:** 7 — Referral & Dispatch System
> **Estimated Hours:** 10–12 hours across 3 sessions

---

## Purpose

This is the **Week 21 instruction document** for IP2A-Database-v2 (UnionCore). Paste this into a new Claude chat session to provide full context for the second week of Phase 7 development. Week 21 builds on the schema decisions and core models from Week 20 to create the dispatch workflow models.

**Prerequisites:** Week 20 must be complete — all 5 pre-implementation decisions locked, enums created, ReferralBook and BookRegistration models in place with seeds and tests.

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
| Testing | pytest (~470 tests → ~490–495 after Week 20) |
| Linting | ruff |

> **⚠️ CRITICAL:** This project uses **Flask** (Blueprints, `request`, `jsonify`, `abort`, `render_template`, `flask run`, port 5000). Do NOT use FastAPI, uvicorn, APIRouter, Depends, HTTPException, or Pydantic `model_dump()`.

---

## Working Copy & Workflow

- **Working copy (for Claude sessions):** `D:\OneDrive\Documents\Claude.ai\IP2A-Database-v2\`
- **Live project:** `C:\Users\Xerxes\Projects\IP2A-Database-v2\`
- **Workflow:** Claude outputs files → Xerxes manually copies to live project
- **Branch:** `develop` at v0.9.4-alpha (main needs merge from develop)

---

## What Was Done in Week 20 (Check Before Starting)

Before starting Week 21, verify these Week 20 deliverables exist and pass tests:

- [ ] `/docs/phase7/PHASE7_SCHEMA_DECISIONS.md` — All 5 decisions documented
- [ ] `src/db/enums/phase7_enums.py` — All Phase 7 enums created
- [ ] `src/models/referral_book.py` — ReferralBook model complete
- [ ] `src/schemas/referral_book.py` — ReferralBook schema complete
- [ ] `src/seed/phase7_seed.py` — 11 referral book seeds loaded
- [ ] `src/models/book_registration.py` — BookRegistration model complete
- [ ] `src/schemas/book_registration.py` — BookRegistration schema complete
- [ ] Alembic migrations for enums, referral_books, book_registrations all applied
- [ ] `src/tests/test_referral_books.py` and `src/tests/test_book_registrations.py` — all passing
- [ ] `PHASE7_SCHEMA_DECISIONS.md` documents the chosen approach for DuesPayment coexistence, exempt status placement, and RegistrationActivity pattern

> **If any of the above are missing or failing, resolve them BEFORE starting Week 21.**

---

## Week 21 Scope

Week 21 has **3 sessions** building the dispatch workflow models — the core of LaborPower replacement.

### Session 21A: LaborRequest & JobBid Models (4 hours)

The LaborRequest model represents an employer's request for workers. The JobBid model represents a member's bid on a posted job (for online bidding).

#### LaborRequest Model

Create `src/models/labor_request.py`:

```python
# Expected fields (adjust based on Week 20 schema decisions):
class LaborRequest(Base):
    __tablename__ = "labor_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    contract_code: Mapped[ContractCode]       # Which CBA this falls under
    book_type: Mapped[BookType]               # Classification of workers needed
    job_class: Mapped[Optional[JobClass]]     # journeyman, apprentice, foreman, etc.
    workers_requested: Mapped[int]            # How many workers
    workers_dispatched: Mapped[int] = mapped_column(default=0)
    worksite_name: Mapped[Optional[str]]      # Job site name/address
    worksite_address: Mapped[Optional[str]]
    start_date: Mapped[date]
    end_date: Mapped[Optional[date]]          # Null = open-ended
    is_short_call: Mapped[bool] = mapped_column(default=False)  # ≤3 days
    short_call_days: Mapped[Optional[int]]    # If short call, how many days
    allows_online_bidding: Mapped[bool] = mapped_column(default=False)
    bidding_opens_at: Mapped[Optional[datetime]]
    bidding_closes_at: Mapped[Optional[datetime]]
    foreman_requested: Mapped[Optional[str]]  # Specific foreman name if employer requests
    special_requirements: Mapped[Optional[str]]
    notes: Mapped[Optional[str]]
    status: Mapped[str]                       # open, partially_filled, filled, cancelled
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    # Relationships
    employer: Mapped["Organization"] = relationship()
    created_by: Mapped["User"] = relationship()
    bids: Mapped[list["JobBid"]] = relationship(back_populates="labor_request")
    dispatches: Mapped[list["Dispatch"]] = relationship(back_populates="labor_request")
```

> **Note:** `employer_id` references the existing `organizations` table. Employers are already seeded as organizations — ~843 employers across 8 contract codes from LaborPower analysis.

#### JobBid Model

Create `src/models/job_bid.py`:

```python
# Expected fields (only if Decision 1 chose separate JobBid model):
class JobBid(Base):
    __tablename__ = "job_bids"

    id: Mapped[int] = mapped_column(primary_key=True)
    labor_request_id: Mapped[int] = mapped_column(ForeignKey("labor_requests.id"))
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    registration_id: Mapped[int] = mapped_column(ForeignKey("book_registrations.id"))
    bid_status: Mapped[BidStatus]             # pending, accepted, declined, expired
    bid_submitted_at: Mapped[datetime]
    bid_responded_at: Mapped[Optional[datetime]]
    bid_position: Mapped[Optional[int]]       # Queue position at time of bid
    notes: Mapped[Optional[str]]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    # Relationships
    labor_request: Mapped["LaborRequest"] = relationship(back_populates="bids")
    member: Mapped["Member"] = relationship()
    registration: Mapped["BookRegistration"] = relationship()
```

#### Session 21A Deliverables

1. `src/models/labor_request.py` — LaborRequest model
2. `src/schemas/labor_request.py` — LaborRequest schema
3. `src/models/job_bid.py` — JobBid model (if Decision 1 = separate model)
4. `src/schemas/job_bid.py` — JobBid schema
5. `alembic/versions/xxx_create_labor_requests.py` — Migration
6. `alembic/versions/xxx_create_job_bids.py` — Migration
7. `src/tests/test_labor_requests.py` — +8–10 tests
8. `src/tests/test_job_bids.py` — +6–8 tests

---

### Session 21B: Dispatch Model & Employment Enhancement (4 hours)

The Dispatch model is the central transaction record — it represents an actual dispatch of a member to an employer.

#### Dispatch Model

Create `src/models/dispatch.py`:

```python
# Expected fields:
class Dispatch(Base):
    __tablename__ = "dispatches"

    id: Mapped[int] = mapped_column(primary_key=True)
    labor_request_id: Mapped[int] = mapped_column(ForeignKey("labor_requests.id"))
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    registration_id: Mapped[int] = mapped_column(ForeignKey("book_registrations.id"))
    bid_id: Mapped[Optional[int]] = mapped_column(ForeignKey("job_bids.id"))  # If dispatched via bid
    employer_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    contract_code: Mapped[ContractCode]
    dispatch_type: Mapped[DispatchType]       # normal, short_call, emergency
    dispatch_status: Mapped[DispatchStatus]   # pending, accepted, declined, completed, terminated
    dispatch_class: Mapped[Optional[JobClass]]
    dispatched_at: Mapped[datetime]
    dispatched_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    start_date: Mapped[date]
    end_date: Mapped[Optional[date]]
    start_rate: Mapped[Optional[Decimal]]     # Hourly rate at start
    term_rate: Mapped[Optional[Decimal]]      # Rate at termination
    days_worked: Mapped[Optional[int]]
    hours_worked: Mapped[Optional[Decimal]]
    term_date: Mapped[Optional[date]]
    term_reason: Mapped[Optional[str]]        # quit, layoff, fired, end_of_job, etc.
    term_comment: Mapped[Optional[str]]
    worksite_name: Mapped[Optional[str]]
    worksite_code: Mapped[Optional[str]]
    restore_to_book: Mapped[bool] = mapped_column(default=False)  # For short calls
    restored_at: Mapped[Optional[datetime]]
    notes: Mapped[Optional[str]]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    # Relationships
    labor_request: Mapped["LaborRequest"] = relationship(back_populates="dispatches")
    member: Mapped["Member"] = relationship()
    registration: Mapped["BookRegistration"] = relationship()
    bid: Mapped[Optional["JobBid"]] = relationship()
    employer: Mapped["Organization"] = relationship()
    dispatched_by: Mapped["User"] = relationship()
```

#### Employment Enhancement

The existing `MemberEmployment` model (from earlier weeks) needs additional fields to connect with the dispatch system:

Modify `src/models/member_employment.py` to add:

```python
# New fields to add to existing MemberEmployment model:
dispatch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dispatches.id"))
employer_code: Mapped[Optional[str]]
worksite_code: Mapped[Optional[str]]
dispatch_class: Mapped[Optional[str]]
dispatch_skill: Mapped[Optional[str]]
dispatch_date: Mapped[Optional[date]]
dispatch_type: Mapped[Optional[str]]
book_id: Mapped[Optional[int]] = mapped_column(ForeignKey("referral_books.id"))
```

> **IMPORTANT:** These fields are OPTIONAL (nullable) because not all employment records come from the dispatch system. Legacy records and direct hires won't have dispatch associations.

#### Session 21B Deliverables

1. `src/models/dispatch.py` — Dispatch model
2. `src/schemas/dispatch.py` — Dispatch schema
3. `src/models/member_employment.py` — MODIFIED with dispatch fields
4. `src/schemas/member_employment.py` — MODIFIED schema
5. `alembic/versions/xxx_create_dispatches.py` — Migration
6. `alembic/versions/xxx_enhance_member_employment.py` — Migration (alter table)
7. `src/tests/test_dispatches.py` — +10–12 tests

---

### Session 21C: RegistrationActivity & Comprehensive Tests (4 hours)

#### RegistrationActivity Model

If Decision 5 from Week 20 includes a dedicated RegistrationActivity model (recommended), create `src/models/registration_activity.py`:

```python
# Expected fields:
class RegistrationActivity(Base):
    __tablename__ = "registration_activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    registration_id: Mapped[int] = mapped_column(ForeignKey("book_registrations.id"))
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    action: Mapped[RegistrationAction]        # register, re_sign, dispatch, resign, roll_off, check_mark_lost, check_mark_restored, exempt_granted, exempt_revoked
    previous_status: Mapped[Optional[RegistrationStatus]]
    new_status: Mapped[RegistrationStatus]
    previous_position: Mapped[Optional[int]]  # Queue position before action
    new_position: Mapped[Optional[int]]       # Queue position after action
    related_dispatch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dispatches.id"))
    performed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[Optional[str]]
    notes: Mapped[Optional[str]]
    created_at: Mapped[datetime]              # Immutable — no updated_at

    # Relationships
    registration: Mapped["BookRegistration"] = relationship(back_populates="activities")
    member: Mapped["Member"] = relationship()
    related_dispatch: Mapped[Optional["Dispatch"]] = relationship()
    performed_by: Mapped["User"] = relationship()
```

> **Design note:** RegistrationActivity is an **append-only** event log. No `updated_at` column — entries are immutable once created. This works alongside the system-level `audit_logs` table (PostgreSQL trigger) to provide both domain-specific event tracking AND compliance audit trails.

#### If Decision 5 Chose Audit-Only (No RegistrationActivity)

Skip this model. Instead, document the audit_logs strategy for registration events in `/docs/phase7/PHASE7_SCHEMA_DECISIONS.md` and ensure all registration state changes go through the existing audit trigger.

#### Comprehensive Test Suite

This session focuses on integration tests that verify the models work together across the full dispatch workflow:

Create `src/tests/test_dispatch_workflow.py`:

```python
# Test scenarios:
# 1. Full dispatch lifecycle: member registers → employer requests → member dispatched → job completes
# 2. Short call flow: dispatch → 3 days → member restored to original book position
# 3. Online bidding flow: employer posts → member bids → bid accepted → dispatch created
# 4. Check mark loss: member misses 3 days → removed from book → registration rolled off
# 5. Re-sign flow: member re-signs before deadline → position maintained
# 6. Re-sign expired: member misses deadline → rolled off
# 7. Exempt member: exempt from check marks → not rolled off
# 8. Multi-book: member on multiple books → dispatched from one → removed from others
# 9. Foreman dispatch: employer requests specific foreman → dispatched outside queue order
# 10. Cascade verification: deleting a labor request doesn't delete dispatches (soft delete pattern)
```

Also expand existing test files:
- `src/tests/test_referral_books.py` — Add relationship tests (book → registrations)
- `src/tests/test_book_registrations.py` — Add status transition tests, APN ordering tests

#### Session 21C Deliverables

1. `src/models/registration_activity.py` — RegistrationActivity model (if applicable)
2. `src/schemas/registration_activity.py` — Schema (if applicable)
3. `alembic/versions/xxx_create_registration_activities.py` — Migration (if applicable)
4. `src/tests/test_dispatch_workflow.py` — Integration tests (+15–20 tests)
5. Expanded tests in existing test files (+5–8 tests)
6. All model `__init__.py` imports updated

---

## Model Dependency Graph (Week 20–21)

```
                    ┌──────────────┐
                    │    Member    │ (existing)
                    └──────┬───────┘
                           │ FK
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────▼──────┐ ┌────▼─────┐ ┌──────▼───────┐
     │ ReferralBook │ │ JobBid   │ │ Dispatch     │
     │  (Week 20)   │ │(Week 21A)│ │ (Week 21B)   │
     └──────┬───────┘ └────┬─────┘ └──────┬───────┘
            │              │              │
     ┌──────▼──────────────┤              │
     │ BookRegistration    │              │
     │   (Week 20)         │◄─────────────┘
     └──────┬──────────────┘
            │
     ┌──────▼───────────┐
     │RegistrationActivity│
     │   (Week 21C)       │
     └────────────────────┘

     ┌──────────────┐          ┌───────────────┐
     │ Organization │ (existing)│ LaborRequest  │
     │ (employers)  │◄─────────│  (Week 21A)   │
     └──────────────┘          └───────────────┘
```

---

## Key Business Rules Relevant to Week 21 Models

These rules are captured in the model fields but are **enforced in the service layer** (Weeks 22–24). During Week 21, focus on ensuring the model can STORE the data needed for these rules:

| Rule | Model Impact |
|------|-------------|
| Short calls ≤3 days | `LaborRequest.is_short_call`, `Dispatch.dispatch_type`, `Dispatch.restore_to_book` |
| Online bidding windows | `LaborRequest.allows_online_bidding`, `bidding_opens_at`, `bidding_closes_at` |
| Foreman requests | `LaborRequest.foreman_requested` |
| Dispatch audit trail | `Dispatch.dispatched_by_id`, `RegistrationActivity` per state change |
| Queue position tracking | `RegistrationActivity.previous_position`, `new_position` |
| Check mark tracking | `BookRegistration.has_check_mark`, `no_check_mark_reason` |
| Term tracking | `Dispatch.term_date`, `term_reason`, `term_comment` |
| Rate tracking | `Dispatch.start_rate`, `term_rate` |

---

## Architecture Reminders

- **Member ≠ Student** — Never merge Member and Student models. Dispatch qualifications ≠ JATC training.
- **`locked_until` datetime** — Not boolean `is_locked`.
- **APN is DECIMAL(10,2)** — `BookRegistration.registration_number` must be Decimal.
- **8 contract codes** — WIREPERSON, S&C, STOCKPERSON, LFM, MARINE, TV&APPL, MARKET RECOVERY, RESIDENTIAL.
- **Audit immutability** — PostgreSQL trigger on `audit_logs`. RegistrationActivity is ALSO immutable (no `updated_at`).
- **Existing employer data** — ~843 employers already in `organizations` table. LaborRequest FK points there.
- **Seed ordering** — Phase 7 seeds must register in the existing dependency-aware ordering system.
- **Inverted tiers** — LaborPower had inverted tier numbering. Confirm correct ordering with dispatch staff before implementing sort logic.

---

## Session Checklist

### Before Starting Each Session

- [ ] Verify Week 20 deliverables are in place (see checklist above)
- [ ] Verify you're on the `develop` branch
- [ ] Run existing tests: `pytest` (all ~490–495 should pass after Week 20)
- [ ] Check `ruff` for any pre-existing lint issues

### After Completing Each Session

- [ ] All new tests pass
- [ ] All existing tests still pass
- [ ] `ruff` reports no new issues
- [ ] Alembic migration runs cleanly (`alembic upgrade head`)
- [ ] New models are importable and relationships resolve

### Week 21 Completion Criteria

- [ ] LaborRequest model, schema, migration complete
- [ ] JobBid model, schema, migration complete (if separate model per Decision 1)
- [ ] Dispatch model, schema, migration complete
- [ ] MemberEmployment enhanced with dispatch fields
- [ ] RegistrationActivity model complete (if per Decision 5)
- [ ] Integration tests cover full dispatch lifecycle
- [ ] +30–40 new tests → ~520–535 total
- [ ] All documentation updated per end-of-session rule

---

## What Comes After Week 21

| Week | Focus | Dependencies |
|------|-------|-------------|
| 22 | Services — Registration (BookRegistrationService, check mark logic, roll-off rules) | Week 21 models |
| 23 | Services — Dispatch (LaborRequestService, JobBidService, DispatchService) | Week 21 models |
| 24 | Queue Management (QueueService, re-sign enforcement, short call restoration) | Weeks 22–23 services |
| 25 | API Endpoints (Book/Registration API, LaborRequest/Bid API, Dispatch API) | Weeks 22–24 services |
| 26–28 | Frontend (Dispatch UI, Book views, Report navigation) | Week 25 APIs |
| 29–32+ | Report sprints (78 reports across P0–P3 priority levels) | Weeks 26–28 frontend |

---

## Related Documents

| Document | Location |
|----------|----------|
| Week 20 Instructions | `/docs/instructions/WEEK_20_INSTRUCTIONS.md` |
| Phase 7 Schema Decisions | `/docs/phase7/PHASE7_SCHEMA_DECISIONS.md` (created Week 20) |
| Phase 7 Continuity Doc | `/docs/phase7/PHASE7_CONTINUITY_DOC.md` |
| Phase 7 Continuity Addendum | `/docs/phase7/PHASE7_CONTINUITY_DOC_ADDENDUM.md` |
| Implementation Plan v2 | `/docs/phase7/PHASE7_IMPLEMENTATION_PLAN_v2.md` |
| Referral & Dispatch Plan | `/docs/phase7/PHASE7_REFERRAL_DISPATCH_PLAN.md` |
| LaborPower Gap Analysis | `/docs/phase7/LABORPOWER_GAP_ANALYSIS.md` |
| Referral Reports Inventory | `/docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` |
| Local 46 Referral Books | `/docs/phase7/LOCAL46_REFERRAL_BOOKS.md` |
| Backend Roadmap v3.0 | `/docs/IP2A_BACKEND_ROADMAP.md` |
| Milestone Checklist | `/docs/IP2A_MILESTONE_CHECKLIST.md` |
| ADR-008: Dues Tracking | `/docs/decisions/ADR-008-dues-tracking.md` |
| ADR-010: Operations Frontend | `/docs/decisions/ADR-010-operations-frontend.md` |
| ADR-012: Audit Logging | `/docs/decisions/ADR-012-audit-logging.md` |

---

## End-of-Session Documentation (MANDATORY)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.

**Minimum updates per session:**
- `/CHANGELOG.md` — version bump and changes
- `/CLAUDE.md` — update with progress
- `/docs/IP2A_MILESTONE_CHECKLIST.md` — check off completed items
- `/docs/phase7/PHASE7_CONTINUITY_DOC.md` — update Session Log table
- Session log in `/docs/reports/session-logs/YYYY-MM-DD-*.md`
- Any affected ADRs

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
*Week 21 of IP2A-Database-v2 (UnionCore) — Phase 7: Referral & Dispatch*
