# Phase 7 Schema Decisions

> **Document Created:** February 4, 2026
> **Status:** APPROVED - Authoritative reference for Weeks 20-32+
> **Decision Meeting:** Week 20 Session A

---

## Purpose

This document records the 5 pre-implementation decisions required before writing Phase 7 code. These decisions reconcile the two schema proposals (`PHASE7_REFERRAL_DISPATCH_PLAN.md` and `PHASE7_IMPLEMENTATION_PLAN_v2.md`) into one authoritative reference.

---

## Decision 1: Job Bid Model Structure

**Question:** Should job bids be tracked as a separate model or embedded in the Dispatch model?

| Option | Pros | Cons |
|--------|------|------|
| **A: Separate JobBid model** | Cleaner audit trail, easier bid history queries, supports reports B-18, AP-08, C-42, C-43, C-44 | Additional table, more complex relationships |
| **B: Embedded in Dispatch** | Simpler schema, fewer joins | Harder to track bids that didn't result in dispatch, incomplete audit trail |

### Decision: **Option A - Separate JobBid model**

**Rationale:**
- LaborPower reports (B-18, AP-08, C-42, C-43, C-44) require bid history independent of dispatch outcomes
- Members can bid on jobs they don't get dispatched to
- Internet bidding rejection tracking needs standalone records
- Two rejections in 12 months = 1-year suspension (needs bid history)

### Implementation:
- Create `src/models/job_bid.py` with separate `JobBid` model
- `Dispatch.bid_id` (nullable FK) links to accepted bids
- `JobBid` tracks: `status` (pending, accepted, rejected, withdrawn, expired), `bid_submitted_at`, `rejection_reason`

---

## Decision 2: DuesPayment Coexistence

**Question:** How should the new `MemberTransaction` model interact with the existing `DuesPayment` model?

| Option | Description | Migration Impact |
|--------|-------------|-----------------|
| **A: Wrapper** | MemberTransaction wraps DuesPayment — new payments create both records | Medium - add foreign key |
| **B: Replace** | MemberTransaction replaces DuesPayment — migrate existing data | High - data migration |
| **C: Independent** | Coexist independently — MemberTransaction for LaborPower-era/import, DuesPayment for Stripe-era | Low - no migration |

### Decision: **Option C - Independent Coexistence**

**Rationale:**
- DuesPayment model is live in production with Stripe integration (ADR-013)
- MemberTransaction is primarily for importing historical LaborPower data
- No breaking changes to existing Stripe payment flow
- Can later add optional FK linkage if needed

### Implementation:
- Create `src/models/member_transaction.py` as independent model
- Keep existing `DuesPayment` untouched
- `MemberTransaction.stripe_session_id` available for future Stripe linkage
- No foreign key between the two models initially

---

## Decision 3: Exempt Status Placement

**Question:** Where should exempt status fields live?

| Option | Scope | Use Case |
|--------|-------|----------|
| **A: Member model** | Global — member exempt everywhere | Simple, but inflexible |
| **B: BookRegistration** | Per-book — member can be exempt on one book but not another | Granular, matches Local 46 procedures |
| **C: Both** | Global flag + per-book overrides | Flexible but complex |

### Decision: **Option B - On BookRegistration Model**

**Rationale:**
- Local 46 procedures allow exempt status for specific classifications
- A member might be medically unable to work Wire but still available for Tradeshow
- Per-book tracking is more granular and matches real-world scenarios
- Simpler than Option C without sacrificing functionality

### Implementation:
- `BookRegistration.is_exempt` — boolean flag
- `BookRegistration.exempt_reason` — enum (ExemptReason)
- `BookRegistration.exempt_start_date` — date when exempt status granted
- `BookRegistration.exempt_end_date` — date when exempt status expires (max 6 months per rules)
- No exempt fields on Member model

---

## Decision 4: Referral Book Field Naming & Seed Data

**Question:** Resolve conflicting field names between the two schema proposals.

| Field | Dispatch Plan | Implementation Plan v2 | **Decision** |
|-------|--------------|----------------------|--------------|
| Classification field | `job_class` / `skill_type` | `classification` | **`classification`** (cleaner) |
| Referral time | `morning_referral_time` | `referral_start_time` | **`referral_start_time`** (clearer) |
| Online bidding | `allows_online_bidding` | `internet_bidding_enabled` | **`internet_bidding_enabled`** (more specific) |
| Region | `region` (string) | `region` (string) | **`region`** (string, use BookRegion enum for validation) |

### Book Number Meaning

**Decision:** `book_number` represents the tier priority:
- **Book 1** = Local members (journeymen who are Local 46 members)
- **Book 2** = Travelers (journeymen from other locals)
- **Book 3** = Other (as applicable per LaborPower data analysis)

### Seed Data Fields

```python
# Authoritative ReferralBook seed structure:
{
    "name": str,                    # "Wire Seattle"
    "code": str,                    # "WIRE_SEA_1" (unique)
    "classification": str,          # BookClassification enum value
    "book_number": int,             # 1, 2, or 3
    "region": str,                  # BookRegion enum value
    "referral_start_time": time,    # "08:30:00"
    "re_sign_days": int,            # 30
    "max_check_marks": int,         # 2 (rolled off at 3rd)
    "grace_period_days": int,       # Days after re-sign deadline
    "max_days_on_book": int | None, # Max days before auto-rolloff (null = no limit)
    "internet_bidding_enabled": bool,
    "is_active": bool,
}
```

---

## Decision 5: RegistrationActivity vs. Dual Audit Pattern

**Question:** Should registration state changes be tracked via a dedicated model, the global audit_logs table, or both?

| Option | Pros | Cons |
|--------|------|------|
| **A: RegistrationActivity only** | Referral-specific queries are fast | Duplicates audit functionality |
| **B: audit_logs only** | Single source of truth, NLRA compliant | Complex queries for referral-specific reports |
| **C: Both (Dual Pattern)** | Best of both — domain queries + compliance | Two writes per action |

### Decision: **Option C - Dual Audit Pattern (Both)**

**Rationale:**
- `RegistrationActivity` provides fast domain-specific queries for operational reports (B-17, A-11, AP-02, C-42)
- `audit_logs` provides NLRA 7-year compliance record with PostgreSQL immutability trigger (ADR-012)
- Different consumers need different views of the same data
- Performance: `RegistrationActivity` can be indexed for book-specific queries without touching audit_logs

### Implementation:
- Create `src/models/registration_activity.py` — append-only (no `updated_at`)
- Every registration state change writes to:
  1. `RegistrationActivity` (domain-specific, query-optimized)
  2. `audit_logs` (global, immutable, NLRA compliance via PostgreSQL trigger)
- Service layer ensures both writes happen atomically

---

## Summary of Authoritative Schema

### Models to Create (Week 20-21)

| Model | Source | Notes |
|-------|--------|-------|
| `ReferralBook` | Both docs | Use `classification`, `referral_start_time`, `internet_bidding_enabled` |
| `BookRegistration` | Both docs | Exempt fields ON registration (Decision 3) |
| `LaborRequest` | Both docs | `employer_id` is NOT NULL (FK to organizations) |
| `JobBid` | Dispatch Plan | **Separate model** (Decision 1) |
| `Dispatch` | Both docs | `bid_id` nullable FK to JobBid |
| `RegistrationActivity` | Both docs | Append-only, supplements audit_logs (Decision 5) |
| `MemberTransaction` | Impl Plan v2 | Independent of DuesPayment (Decision 2) |
| `MemberFinancial` | Impl Plan v2 | LaborPower-style financial tracking |

### Enum File

**Location:** `src/db/enums/phase7_enums.py`

Enums to include (merged from both proposals):
- `BookClassification` — inside_wireperson, tradeshow, sound_comm, etc.
- `BookRegion` — seattle, bremerton, port_angeles
- `RegistrationStatus` — active, rolled_off, dispatched, exempt, quit, discharged
- `RegistrationAction` — register, re_sign, check_mark, roll_off, dispatch, etc.
- `ExemptReason` — military, union_business, salting, medical, jury_duty, etc.
- `RolloffReason` — check_marks, quit, discharged, failed_re_sign, etc.
- `LaborRequestStatus` — open, partially_filled, filled, cancelled, expired
- `BidStatus` — pending, accepted, rejected, withdrawn, expired
- `DispatchMethod` — morning_referral, internet_bid, email_bid, by_name, emergency
- `DispatchStatus` — dispatched, checked_in, working, terminated, rejected, no_show
- `TermReason` — rif, quit, fired, laid_off, short_call_end, etc.
- `NoCheckMarkReason` — specialty, mou_jobsite, early_start, etc.
- `JobClass` — JRY_WIRE, SOUND, RESIDENTIAL, etc.

---

## APN (Applicant Priority Number) Format

**CRITICAL:** APN is `DECIMAL(10,2)`, NOT INTEGER.

From LaborPower data analysis:
- Integer part = Excel serial date (days since epoch)
- Decimal part = secondary sort key for same-day registrations (.01, .02, etc.)
- Preserves FIFO ordering for dispatch

Example: `45880.41` means:
- Registered on day 45880 (Excel serial)
- 41st person to register that day (or manual sort key)

**Implementation:**
- `BookRegistration.registration_number` — `Decimal(10, 2)`
- Service layer generates next APN as: `next_whole_number + .00`
- Short call restorations may use decimal increments

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-04 | Initial decisions document |

---

*Phase 7 Schema Decisions v1.0*
*Authoritative reference for IP2A-Database-v2 Phase 7*
