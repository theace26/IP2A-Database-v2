# ADR-015: Referral & Dispatch System Architecture

> **Document Created:** February 4, 2026
> **Last Updated:** February 4, 2026
> **Version:** 1.0
> **Status:** Implemented (partial) — Foundation complete, API/UI pending

## Status

Implemented (partial) — Weeks 20-22 foundation complete

## Date

2026-02-04

## Context

Phase 7 implements the out-of-work referral and dispatch system for IBEW Local 46, replacing the legacy LaborPower system. This is the largest remaining phase of IP2A, requiring:

- 12 new database tables
- 14 business rules from IBEW Local 46 Referral Procedures (effective October 4, 2024)
- ~78 reports to achieve LaborPower parity
- Integration with existing Member, Organization, and Audit infrastructure

Key challenges addressed:
1. **Data Model Complexity**: LaborPower data analysis revealed 8 critical schema findings, including APN as DECIMAL(10,2) and duplicate APNs within books
2. **Audit Requirements**: NLRA 7-year retention mandate for all dispatch records
3. **Business Rule Fidelity**: Must match existing dispatch procedures exactly (30-day re-sign, 3 check marks, exempt status, etc.)
4. **Framework Alignment**: Instruction documents incorrectly stated Flask; actual codebase uses FastAPI

## Options Considered

### Decision 1: Job Bid Model Structure

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A: Separate JobBid model** | Independent table for bid tracking | Cleaner audit trail, supports rejection history, enables 1-year suspension tracking | Additional table, more joins |
| B: Embedded in Dispatch | Bid fields on Dispatch model | Simpler schema | Cannot track bids that didn't result in dispatch |

### Decision 2: DuesPayment Coexistence

| Option | Description | Migration Impact |
|--------|-------------|-----------------|
| A: Wrapper | MemberTransaction wraps DuesPayment | Medium |
| B: Replace | MemberTransaction replaces DuesPayment | High |
| **C: Independent** | Coexist independently | Low |

### Decision 3: Exempt Status Placement

| Option | Scope | Flexibility |
|--------|-------|-------------|
| A: Member model | Global exempt status | Inflexible |
| **B: BookRegistration** | Per-book exempt | Granular |
| C: Both | Global + per-book overrides | Complex |

### Decision 4: Audit Pattern

| Option | Description | Trade-off |
|--------|-------------|-----------|
| A: RegistrationActivity only | Domain-specific table | Duplicates audit functionality |
| B: audit_logs only | Use existing infrastructure | Complex queries for referral reports |
| **C: Dual Pattern (Both)** | Both tables | Two writes per action, but optimal for both use cases |

## Decision

### Key Architectural Decisions Made

| # | Decision | Chosen Option | Rationale |
|---|----------|---------------|-----------|
| 1 | **Separate JobBid model** | Option A | LaborPower reports (B-18, AP-08, C-42) require bid history independent of dispatch. Two rejections in 12 months = 1-year suspension (needs tracking). |
| 2 | **MemberTransaction independent** | Option C | DuesPayment is live in production with Stripe integration (ADR-013). MemberTransaction is for LaborPower import. No breaking changes. |
| 3 | **Per-book exempt status** | Option B | Local 46 procedures allow exempt status for specific classifications. A member might be medically unable to work Wire but available for Tradeshow. |
| 4 | **Dual audit pattern** | Option C | RegistrationActivity for fast domain queries (reports). audit_logs for NLRA 7-year compliance with immutability trigger (ADR-012). |
| 5 | **APN as DECIMAL(10,2)** | Data-driven | LaborPower analysis revealed integer part = Excel serial date, decimal part = same-day sort key. Truncating to INTEGER destroys FIFO ordering. |

### Field Naming Conventions

| Field | Chosen Name | Alternative Rejected |
|-------|-------------|---------------------|
| Classification | `classification` | `job_class`, `skill_type` |
| Referral time | `referral_start_time` | `morning_referral_time` |
| Online bidding | `internet_bidding_enabled` | `allows_online_bidding` |
| APN field | `registration_number` | `applicant_priority_number`, `position_number` |

### Model Architecture

```
┌─────────────────┐      ┌──────────────────┐
│  ReferralBook   │──────│ BookRegistration │
│  (11 books)     │      │ (APN as DECIMAL) │
└─────────────────┘      └────────┬─────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐      ┌──────────────────┐     ┌───────────────────┐
│  LaborRequest   │──────│     JobBid       │     │RegistrationActivity│
│ (employer jobs) │      │ (member bids)    │     │ (append-only audit)│
└────────┬────────┘      └────────┬─────────┘     └───────────────────┘
         │                        │
         └────────────┬───────────┘
                      ▼
              ┌──────────────────┐
              │     Dispatch     │
              │ (member → job)   │
              └──────────────────┘
```

## Implementation Status

| Component | Status | Week | Notes |
|-----------|--------|------|-------|
| Phase 7 enums (19 enums) | ✅ Complete | 20A | `src/db/enums/phase7_enums.py` |
| Schema decisions document | ✅ Complete | 20A | `docs/phase7/PHASE7_SCHEMA_DECISIONS.md` |
| ReferralBook model | ✅ Complete | 20B | 11 book seeds created |
| BookRegistration model | ✅ Complete | 20C | APN as DECIMAL(10,2) |
| LaborRequest model | ✅ Complete | 21A | Employer job requests |
| JobBid model | ✅ Complete | 21A | Separate model per Decision 1 |
| Dispatch model | ✅ Complete | 21B | Links member → job |
| RegistrationActivity model | ✅ Complete | 21C | Append-only (no updated_at) |
| ReferralBookService | ✅ Complete | 22A | CRUD, stats, settings |
| BookRegistrationService | ✅ Complete | 22B-C | Registration, check marks, roll-off |
| Model tests | ✅ Complete | 20-22 | 20+ tests |
| API routers | 🔜 Pending | 23+ | — |
| Frontend UI | 🔜 Pending | 23+ | Dispatch board, book management |
| Reports (78) | 🔜 Pending | 23+ | LaborPower parity |

## Consequences

### Positive

1. **NLRA Compliance**: Dual audit pattern ensures 7-year retention with immutable records (PostgreSQL trigger from ADR-012)
2. **Data Fidelity**: APN as DECIMAL(10,2) preserves LaborPower FIFO ordering exactly
3. **Flexible Exemptions**: Per-book exempt status matches real-world union procedures
4. **Clean Bid History**: Separate JobBid model enables accurate suspension tracking and reporting
5. **No Breaking Changes**: Independent MemberTransaction preserves live Stripe integration

### Negative

1. **Schema Complexity**: 6 new models with many relationships
2. **Dual Writes**: Every registration change writes to both RegistrationActivity and audit_logs
3. **Learning Curve**: Business rules are complex (14 rules from Local 46 procedures)

### Neutral

1. **Migration Required**: Alembic migration needed for 6+ tables (pending)
2. **Report Volume**: 78 reports to build (but matches LaborPower exactly)

## References

- [PHASE7_SCHEMA_DECISIONS.md](../phase7/PHASE7_SCHEMA_DECISIONS.md) — Detailed decision rationale
- [PHASE7_CONTINUITY_DOC.md](../phase7/PHASE7_CONTINUITY_DOC.md) — Session continuity context
- [PHASE7_REFERRAL_DISPATCH_PLAN.md](../phase7/PHASE7_REFERRAL_DISPATCH_PLAN.md) — Full implementation plan
- [LABORPOWER_REFERRAL_REPORTS_INVENTORY.md](../phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md) — 78 reports catalog
- [ADR-012](ADR-012-audit-logging.md) — Audit logging architecture (NLRA compliance)
- [ADR-013](ADR-013-stripe-payment-integration.md) — Stripe integration (why MemberTransaction is independent)
- IBEW Local 46 Referral Procedures (October 4, 2024) — Business rules source

## Files Created

```
src/db/enums/phase7_enums.py
src/models/referral_book.py
src/models/book_registration.py
src/models/registration_activity.py
src/models/labor_request.py
src/models/job_bid.py
src/models/dispatch.py
src/schemas/referral_book.py
src/schemas/book_registration.py
src/schemas/registration_activity.py
src/schemas/labor_request.py
src/schemas/job_bid.py
src/schemas/dispatch.py
src/services/referral_book_service.py
src/services/book_registration_service.py
src/seed/phase7_seed.py
src/tests/test_phase7_models.py
docs/phase7/PHASE7_SCHEMA_DECISIONS.md
```

---

**Document Version:** 1.0
**Last Updated:** February 4, 2026
