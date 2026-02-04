# Week 22 Instructions — Phase 7: Registration Services & Business Rules

> **Document Created:** February 3, 2026
> **Last Updated:** February 3, 2026
> **Version:** 1.0
> **Status:** Active — Ready for implementation (after Week 21 completes)
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1–19)
> **Phase:** 7 — Referral & Dispatch System
> **Estimated Hours:** 10–12 hours across 3 sessions

---

## Purpose

This is the **Week 22 instruction document** for IP2A-Database-v2 (UnionCore). Paste this into a new Claude chat session to provide full context for the third week of Phase 7 development. Week 22 is the first **service layer** week — this is where the 14 business rules from the LaborPower Referral Procedures begin turning into actual enforceable code on top of the models built in Weeks 20–21.

**Prerequisites:** Weeks 20 and 21 must be complete — all schema decisions locked, all 6+ Phase 7 models created (ReferralBook, BookRegistration, LaborRequest, JobBid, Dispatch, RegistrationActivity), enums in place, seeds loaded, and ~520–535 tests passing.

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
| Testing | pytest (~520–535 tests after Weeks 20–21) |
| Linting | ruff |

> **⚠️ CRITICAL:** This project uses **Flask** (Blueprints, `request`, `jsonify`, `abort`, `render_template`, `flask run`, port 5000). Do NOT use FastAPI, uvicorn, APIRouter, Depends, HTTPException, or Pydantic `model_dump()`.

---

## Working Copy & Workflow

- **Working copy (for Claude sessions):** `D:\OneDrive\Documents\Claude.ai\IP2A-Database-v2\`
- **Live project:** `C:\Users\Xerxes\Projects\IP2A-Database-v2\`
- **Workflow:** Claude outputs files → Xerxes manually copies to live project
- **Branch:** `develop` at v0.9.4-alpha (main needs merge from develop)

---

## What Was Done in Weeks 20–21 (Check Before Starting)

Before starting Week 22, verify these deliverables exist and pass tests:

### Week 20 Deliverables
- [ ] `/docs/phase7/PHASE7_SCHEMA_DECISIONS.md` — All 5 pre-implementation decisions documented
- [ ] `src/db/enums/phase7_enums.py` — All Phase 7 enums
- [ ] `src/models/referral_book.py` — ReferralBook model + schema + migration
- [ ] `src/seed/phase7_seed.py` — 11 referral book seeds
- [ ] `src/models/book_registration.py` — BookRegistration model + schema + migration

### Week 21 Deliverables
- [ ] `src/models/labor_request.py` — LaborRequest model + schema + migration
- [ ] `src/models/job_bid.py` — JobBid model + schema + migration (if separate per Decision 1)
- [ ] `src/models/dispatch.py` — Dispatch model + schema + migration
- [ ] `src/models/member_employment.py` — Enhanced with dispatch fields
- [ ] `src/models/registration_activity.py` — RegistrationActivity model (if per Decision 5)
- [ ] `src/tests/test_dispatch_workflow.py` — Integration tests passing
- [ ] All Alembic migrations applied cleanly
- [ ] ~520–535 tests all passing

> **If any of the above are missing or failing, resolve them BEFORE starting Week 22.**

---

## Service Layer Pattern (Existing Convention)

UnionCore follows an established service layer pattern from Weeks 1–19. All new Phase 7 services MUST follow this pattern:

```python
# Typical service structure (see existing services for reference):
# src/services/some_service.py

from src.db.database import db  # SQLAlchemy session
from src.models.some_model import SomeModel

class SomeService:
    """Service layer for SomeModel business logic."""

    @staticmethod
    def get_by_id(id: int) -> SomeModel | None:
        return db.session.get(SomeModel, id)

    @staticmethod
    def get_all(**filters) -> list[SomeModel]:
        query = db.session.query(SomeModel)
        # Apply filters...
        return query.all()

    @staticmethod
    def create(**kwargs) -> SomeModel:
        instance = SomeModel(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

    @staticmethod
    def update(id: int, **kwargs) -> SomeModel:
        instance = db.session.get(SomeModel, id)
        for key, value in kwargs.items():
            setattr(instance, key, value)
        db.session.commit()
        return instance
```

> **Key conventions:**
> - Services use `@staticmethod` methods (no instance state)
> - Services handle `db.session` commit/rollback
> - Services raise domain exceptions, NOT HTTP exceptions
> - Services are imported by routers/blueprints — services never import from routers
> - Complex operations that touch multiple models go through a **coordinating service** (e.g., `dispatch_service.py` coordinates between BookRegistration, Dispatch, RegistrationActivity)
> - Frontend-facing services (e.g., `*_frontend_service.py`) assemble data for Jinja2 templates — these come in Week 26+

---

## Week 22 Scope

Week 22 has **3 sessions** building the registration service layer — the business logic that enforces referral book and registration rules.

### Session 22A: ReferralBookService (3–4 hours)

The ReferralBookService manages referral book queries, filtering, and seed data integration. This is the simpler of the two services — most complexity lives in BookRegistrationService.

#### Deliverables

**1. `src/services/referral_book_service.py`**

```python
class ReferralBookService:
    """
    Service layer for ReferralBook management.
    Handles book queries, filtering, and administrative operations.
    """

    # --- Query Methods ---

    @staticmethod
    def get_by_id(book_id: int) -> ReferralBook | None:
        """Get a single book by ID."""

    @staticmethod
    def get_by_code(code: str) -> ReferralBook | None:
        """Get a single book by unique code (e.g., 'WIRE_SEA_1')."""

    @staticmethod
    def get_all_active() -> list[ReferralBook]:
        """Get all active referral books, ordered by classification then region."""

    @staticmethod
    def get_by_classification(classification: BookType) -> list[ReferralBook]:
        """Get all books for a given classification (e.g., inside_wireperson)."""

    @staticmethod
    def get_by_region(region: BookRegion) -> list[ReferralBook]:
        """Get all books in a given region (e.g., seattle)."""

    @staticmethod
    def get_by_classification_and_region(
        classification: BookType, region: BookRegion
    ) -> list[ReferralBook]:
        """Get books matching both classification and region."""

    # --- Book Statistics ---

    @staticmethod
    def get_book_stats(book_id: int) -> dict:
        """
        Get registration statistics for a book.
        Returns: {
            'total_registered': int,
            'active_count': int,
            'dispatched_count': int,
            'with_check_mark': int,
            'without_check_mark': int,
            'exempt_count': int,
        }
        """

    @staticmethod
    def get_all_books_summary() -> list[dict]:
        """
        Get summary stats for ALL active books.
        Used by the dispatch dashboard (Week 26+).
        Returns list of dicts with book info + registration counts.
        """

    # --- Administrative ---

    @staticmethod
    def activate_book(book_id: int) -> ReferralBook:
        """Reactivate a deactivated book."""

    @staticmethod
    def deactivate_book(book_id: int) -> ReferralBook:
        """
        Deactivate a book. Does NOT remove registrations —
        members remain registered but book won't appear in active lists.
        """

    @staticmethod
    def update_book_settings(
        book_id: int,
        max_days_on_book: int | None = None,
        re_sign_days: int | None = None,
        grace_period_days: int | None = None,
        internet_bidding_enabled: bool | None = None,
    ) -> ReferralBook:
        """Update configurable book settings."""
```

**2. `src/tests/test_referral_book_service.py`**

Test scenarios:

| Test | What It Validates |
|------|------------------|
| `test_get_by_code` | Returns correct book for known codes like `WIRE_SEA_1` |
| `test_get_by_code_not_found` | Returns None for invalid code |
| `test_get_all_active` | Returns only active books, in correct order |
| `test_get_by_classification` | Filters by BookType enum correctly |
| `test_get_by_region` | Filters by BookRegion enum correctly |
| `test_get_by_classification_and_region` | Combined filter (e.g., inside_wireperson + seattle → Wire SEA 1 & 2) |
| `test_get_book_stats` | Returns correct counts for registrations on a book |
| `test_get_book_stats_empty_book` | Returns all zeros for a book with no registrations |
| `test_deactivate_book` | Sets `is_active=False`, keeps registrations intact |
| `test_activate_book` | Restores `is_active=True` |
| `test_update_book_settings` | Partial update works, unchanged fields preserved |
| `test_get_all_books_summary` | Returns one entry per active book with stats |

Target: **+12–14 tests**

---

### Session 22B: BookRegistrationService — Core Operations (4 hours)

This is the most business-rule-heavy service in Phase 7. It enforces the registration, re-sign, and status transition rules from the LaborPower Referral Procedures.

#### Deliverables

**1. `src/services/book_registration_service.py`**

```python
class BookRegistrationService:
    """
    Service layer for BookRegistration business logic.
    Enforces referral rules: registration, re-sign, status transitions,
    queue positioning, and member eligibility.
    """

    # --- Registration ---

    @staticmethod
    def register_member(
        member_id: int,
        book_id: int,
        performed_by_id: int,
        notes: str | None = None,
    ) -> BookRegistration:
        """
        Register a member on a referral book.

        Business Rules:
        - Member must not already be REGISTERED on this book
        - Member CAN be registered on multiple different books simultaneously
        - Assigns next APN (registration_number) in sequence
        - Sets status = REGISTERED, has_check_mark = True
        - Creates RegistrationActivity record
        - Triggers audit log (via existing PostgreSQL trigger)

        Raises:
        - ValueError: Member already registered on this book
        - ValueError: Book is not active
        - ValueError: Member not found
        """

    @staticmethod
    def get_next_apn(book_id: int) -> Decimal:
        """
        Calculate the next APN (registration number) for a book.
        APNs are DECIMAL(10,2) — e.g., 1234.00, 1234.01, 1234.02
        New registrations get the next whole number.
        Re-registrations after short calls may get decimal suffixes.
        """

    @staticmethod
    def re_sign_member(
        registration_id: int,
        performed_by_id: int,
        notes: str | None = None,
    ) -> BookRegistration:
        """
        Re-sign a member on their book (extend registration).

        Business Rules:
        - Member must currently be REGISTERED on the book
        - Re-sign resets the roll-off countdown
        - Updates re_sign_date to now
        - Creates RegistrationActivity record

        Raises:
        - ValueError: Registration not found or not in REGISTERED status
        - ValueError: Re-sign period expired (past grace period)
        """

    # --- Status Transitions ---

    @staticmethod
    def resign_member(
        registration_id: int,
        performed_by_id: int,
        reason: str | None = None,
    ) -> BookRegistration:
        """
        Member voluntarily resigns from a book.

        Business Rules:
        - Sets status = RESIGNED
        - Creates RegistrationActivity record
        - Does NOT affect registrations on other books

        Raises:
        - ValueError: Registration not in REGISTERED status
        """

    @staticmethod
    def roll_off_member(
        registration_id: int,
        performed_by_id: int,
        reason: str = "Exceeded max days on book",
    ) -> BookRegistration:
        """
        Roll a member off a book (involuntary removal).

        Business Rules:
        - Sets status = ROLLED_OFF
        - Sets roll_off_date to now
        - Creates RegistrationActivity record
        - Typically triggered by check mark loss or expiration

        Raises:
        - ValueError: Registration not in REGISTERED status
        """

    @staticmethod
    def mark_dispatched(
        registration_id: int,
        dispatch_id: int,
        performed_by_id: int,
    ) -> BookRegistration:
        """
        Mark a registration as dispatched (member accepted a job).

        Business Rules:
        - Sets status = DISPATCHED
        - Links to the Dispatch record
        - Creates RegistrationActivity record
        - For short calls: does NOT change status (handled by DispatchService)

        Raises:
        - ValueError: Registration not in REGISTERED status
        """

    # --- Query Methods ---

    @staticmethod
    def get_book_queue(
        book_id: int,
        status: RegistrationStatus | None = None,
        include_exempt: bool = True,
    ) -> list[BookRegistration]:
        """
        Get the ordered queue for a book.

        Ordering: by registration_number (APN) ascending.
        This is FIFO — lowest APN = longest waiting = first dispatched.

        NOTE: LaborPower had INVERTED tier numbering. Our system uses
        natural ordering (lower APN = higher priority). Verify with
        dispatch staff that this matches their expectation.
        """

    @staticmethod
    def get_member_registrations(
        member_id: int,
        active_only: bool = True,
    ) -> list[BookRegistration]:
        """Get all registrations for a member, optionally filtered to active only."""

    @staticmethod
    def get_member_position(registration_id: int) -> int | None:
        """
        Get a member's current position in the book queue.
        Position 1 = next to be dispatched.
        Returns None if not in REGISTERED status.
        """

    @staticmethod
    def get_registrations_expiring_soon(
        days_threshold: int = 7,
    ) -> list[BookRegistration]:
        """
        Get registrations approaching their roll-off date.
        Used by the re-sign reminder system.
        """

    # --- Validation Helpers ---

    @staticmethod
    def can_register(member_id: int, book_id: int) -> tuple[bool, str | None]:
        """
        Check if a member can register on a book.
        Returns (True, None) or (False, reason_string).

        Checks:
        - Book exists and is active
        - Member exists
        - Member not already REGISTERED on this specific book
        - Member not currently DISPATCHED from this book (must complete dispatch first)
        """

    @staticmethod
    def can_re_sign(registration_id: int) -> tuple[bool, str | None]:
        """
        Check if a registration can be re-signed.
        Returns (True, None) or (False, reason_string).

        Checks:
        - Registration exists and is REGISTERED
        - Within re-sign window (not past grace period)
        """
```

**2. `src/tests/test_book_registration_service.py`**

Test scenarios:

| Test | What It Validates |
|------|------------------|
| `test_register_member_success` | Creates registration with correct APN, status, check mark |
| `test_register_member_duplicate` | Raises ValueError for duplicate registration on same book |
| `test_register_member_multiple_books` | Member CAN register on multiple different books |
| `test_register_member_inactive_book` | Raises ValueError for inactive book |
| `test_get_next_apn_empty_book` | Returns 1.00 for first registration |
| `test_get_next_apn_existing` | Returns next whole number after existing registrations |
| `test_re_sign_member_success` | Updates re_sign_date, resets countdown |
| `test_re_sign_expired` | Raises ValueError if past grace period |
| `test_resign_member` | Sets status to RESIGNED, creates activity |
| `test_roll_off_member` | Sets status to ROLLED_OFF, sets roll_off_date |
| `test_mark_dispatched` | Sets status to DISPATCHED, links dispatch |
| `test_get_book_queue_ordering` | Returns registrations ordered by APN ascending |
| `test_get_member_position` | Returns correct 1-based position in queue |
| `test_get_member_registrations` | Returns all registrations for a member |
| `test_can_register_checks` | Validates all eligibility checks |
| `test_can_re_sign_checks` | Validates re-sign eligibility |
| `test_status_transition_invalid` | Cannot dispatch from RESIGNED status, etc. |
| `test_registration_creates_activity` | RegistrationActivity record created for each state change |

Target: **+18–22 tests**

---

### Session 22C: Check Mark Logic & Roll-Off Rules (3–4 hours)

This session implements the check mark enforcement system and automatic roll-off rules — two of the most operationally critical business rules from LaborPower.

#### Check Mark Business Rules (from Referral Procedures)

| Rule | Detail |
|------|--------|
| Daily check marks required | Members must check in daily to maintain their position on the book |
| 3 missed = removal | After 3 consecutive missed check marks, member is rolled off the book |
| Exempt members skip | Members with exempt status (medical, union business, etc.) are not required to check in |
| Check mark restoration | A dispatcher can restore a lost check mark with a reason |
| Check mark window | Check marks are only valid during the book's referral window (e.g., 8:30 AM for Wire books) |

#### Roll-Off Business Rules

| Rule | Detail |
|------|--------|
| Max days on book | Each book has a `max_days_on_book` setting — registration expires after this period |
| Re-sign window | Members get `re_sign_days` to re-sign before the deadline |
| Grace period | After the re-sign deadline, a `grace_period_days` window before final roll-off |
| Short call protection | Members on short calls (≤3 days) are NOT rolled off — their position is preserved |
| Dispatched protection | Members currently dispatched are not subject to roll-off |

#### Deliverables

**1. Add check mark methods to `src/services/book_registration_service.py`:**

```python
    # --- Check Mark Operations ---

    @staticmethod
    def record_check_mark(
        registration_id: int,
        performed_by_id: int,
    ) -> BookRegistration:
        """
        Record a daily check mark for a member.

        Business Rules:
        - Only valid for REGISTERED status
        - Resets missed check mark counter
        - Creates RegistrationActivity record

        Raises:
        - ValueError: Registration not in REGISTERED status
        - ValueError: Member is exempt (no check mark needed)
        """

    @staticmethod
    def record_missed_check_mark(
        registration_id: int,
        performed_by_id: int,
        reason: NoCheckMarkReason | None = None,
    ) -> BookRegistration:
        """
        Record a missed check mark.

        Business Rules:
        - Skip if member is exempt
        - Increment missed counter
        - If 3 consecutive misses → auto roll-off
        - Creates RegistrationActivity record

        Returns the updated registration (may have status=ROLLED_OFF after 3rd miss).
        """

    @staticmethod
    def restore_check_mark(
        registration_id: int,
        performed_by_id: int,
        reason: str,
    ) -> BookRegistration:
        """
        Restore a member's check mark (dispatcher override).

        Business Rules:
        - Resets has_check_mark to True
        - Clears missed counter
        - Records the restoration reason
        - Creates RegistrationActivity record
        - Can only be done by authorized dispatchers

        Raises:
        - ValueError: Registration not in REGISTERED status
        """

    # --- Exempt Status Operations ---

    @staticmethod
    def grant_exempt_status(
        registration_id: int,
        performed_by_id: int,
        reason: str,
    ) -> BookRegistration:
        """
        Grant exempt status to a member on a book.

        Business Rules:
        - Exempt members skip check mark requirements
        - Reason must be documented (medical, union business, etc.)
        - Creates RegistrationActivity record
        """

    @staticmethod
    def revoke_exempt_status(
        registration_id: int,
        performed_by_id: int,
        reason: str,
    ) -> BookRegistration:
        """
        Revoke exempt status from a member.

        Business Rules:
        - Member resumes normal check mark requirements
        - Creates RegistrationActivity record
        """

    # --- Roll-Off Operations ---

    @staticmethod
    def process_roll_offs(performed_by_id: int) -> list[BookRegistration]:
        """
        Batch process: find and roll off all expired registrations.

        Scans ALL active books for registrations where:
        - Status is REGISTERED
        - NOT exempt
        - NOT currently on a short call dispatch
        - max_days_on_book exceeded AND grace_period expired

        Returns list of registrations that were rolled off.
        This is designed to run as a scheduled job (daily or per-referral-window).
        """

    @staticmethod
    def get_re_sign_reminders() -> list[dict]:
        """
        Get members who need to re-sign soon.

        Returns list of dicts with:
        - registration info
        - days_remaining until roll-off
        - book info

        Filters to registrations within the re-sign window.
        Used by notification system / dispatcher dashboard.
        """

    @staticmethod
    def is_protected_from_rolloff(registration_id: int) -> tuple[bool, str | None]:
        """
        Check if a registration is protected from roll-off.

        Protected if:
        - Member is exempt
        - Member is currently on a short call dispatch
        - Member is currently dispatched (any type)

        Returns (True, reason) or (False, None).
        """
```

**2. Add check mark tracking fields (if not already in Week 20 model):**

Verify `BookRegistration` has these fields. If missing, create an Alembic migration:

```python
# Fields needed for check mark tracking:
consecutive_missed_check_marks: Mapped[int] = mapped_column(default=0)
last_check_mark_at: Mapped[Optional[datetime]]
```

> **Check with Week 20 schema decisions:** If these fields were already included in the BookRegistration model, skip the migration. If not, add them now.

**3. `src/tests/test_check_mark_logic.py`**

| Test | What It Validates |
|------|------------------|
| `test_record_check_mark` | Resets missed counter, updates last_check_mark_at |
| `test_record_missed_once` | Increments counter to 1, no roll-off |
| `test_record_missed_twice` | Increments counter to 2, no roll-off |
| `test_record_missed_three_times` | Third miss triggers auto roll-off, status → ROLLED_OFF |
| `test_missed_check_mark_exempt_member` | Exempt members skipped, no counter increment |
| `test_restore_check_mark` | Resets counter, sets has_check_mark = True |
| `test_grant_exempt_status` | Sets is_exempt = True, records reason |
| `test_revoke_exempt_status` | Sets is_exempt = False, creates activity |
| `test_exempt_member_not_rolled_off` | process_roll_offs skips exempt members |
| `test_dispatched_member_not_rolled_off` | process_roll_offs skips dispatched members |
| `test_short_call_member_not_rolled_off` | process_roll_offs skips short call dispatches |
| `test_process_roll_offs_batch` | Correctly identifies and rolls off expired registrations |
| `test_process_roll_offs_respects_grace` | Doesn't roll off during grace period |
| `test_get_re_sign_reminders` | Returns correct members within re-sign window |
| `test_is_protected_from_rolloff` | Correctly identifies all protection types |
| `test_check_mark_creates_activity` | Each check mark operation creates RegistrationActivity |

Target: **+16–18 tests**

**4. `src/tests/test_roll_off_rules.py`**

| Test | What It Validates |
|------|------------------|
| `test_roll_off_after_max_days` | Registration rolled off when max_days exceeded + grace expired |
| `test_no_roll_off_within_max_days` | Registration safe within max_days window |
| `test_no_roll_off_during_grace_period` | Registration safe during grace period after max_days |
| `test_roll_off_date_calculation` | Correct date math for max_days + grace_period |
| `test_re_sign_resets_countdown` | Re-signing resets the max_days clock |
| `test_roll_off_multiple_books` | Member rolled off one book doesn't affect other books |
| `test_roll_off_with_null_max_days` | Books with no max_days never auto-roll-off |

Target: **+7–8 tests**

---

## Business Rules Implementation Matrix

This matrix maps the 14 LaborPower business rules to which Week 22 session implements them:

| # | Business Rule | Session | Method/Test |
|---|--------------|---------|-------------|
| 1 | Members sign out-of-work list | 22B | `register_member()` |
| 2 | Must re-sign within allowed period | 22B | `re_sign_member()`, `can_re_sign()` |
| 3 | 3 missed check marks = removal | 22C | `record_missed_check_mark()`, auto roll-off |
| 4 | Daily check mark requirement | 22C | `record_check_mark()` |
| 5 | Check mark restoration by dispatcher | 22C | `restore_check_mark()` |
| 6 | Exempt status (medical, union business) | 22C | `grant_exempt_status()`, `revoke_exempt_status()` |
| 7 | Roll-off after max days | 22C | `process_roll_offs()` |
| 8 | Grace period before final roll-off | 22C | `process_roll_offs()`, `is_protected_from_rolloff()` |
| 9 | Short call position preservation | 22C | `is_protected_from_rolloff()` — full impl in Week 23 DispatchService |
| 10 | Online bidding | — | Week 23 (JobBidService) |
| 11 | Quit/discharge re-registration | — | Week 23 (DispatchService termination handling) |
| 12 | Foreman dispatch | — | Week 23 (DispatchService) |
| 13 | Tier/book priority dispatch | — | Week 23 (DispatchService queue selection) |
| 14 | TERO/PLA/CWA special categories | — | Week 23 (DispatchService) |

> **Rules 10–14 are NOT implemented in Week 22.** They belong to the dispatch service layer in Week 23. Week 22 focuses on registration and the member's relationship to the book.

---

## Model Fields Quick Reference (Weeks 20–21)

For service implementation, here's a quick reference of the Phase 7 model fields you'll be working with. Exact field names come from the Week 20 Schema Decisions document — adjust if your decisions changed any names:

### BookRegistration Key Fields

| Field | Type | Notes |
|-------|------|-------|
| `registration_number` | `Decimal(10,2)` | APN — FIFO ordering. Lower = dispatched first |
| `status` | `RegistrationStatus` | registered, dispatched, resigned, rolled_off |
| `has_check_mark` | `bool` | Default True. False after missed marks |
| `no_check_mark_reason` | `NoCheckMarkReason` | Optional — why check mark was lost |
| `consecutive_missed_check_marks` | `int` | Counter. 3 = auto roll-off |
| `last_check_mark_at` | `datetime` | Last successful check-in |
| `is_exempt` | `bool` | Exempt from check mark requirements |
| `exempt_reason` | `str` | Why exempt (medical, union business, etc.) |
| `re_sign_date` | `datetime` | Last re-sign timestamp |
| `roll_off_date` | `datetime` | When member was rolled off (null if active) |

### ReferralBook Key Fields

| Field | Type | Notes |
|-------|------|-------|
| `max_days_on_book` | `int` (nullable) | Null = no auto-expiry |
| `re_sign_days` | `int` (nullable) | Window to re-sign before deadline |
| `grace_period_days` | `int` (nullable) | Additional window after re-sign deadline |
| `referral_start_time` | `time` | Check mark window start (e.g., 08:30) |
| `internet_bidding_enabled` | `bool` | Whether this book supports online bidding |

### RegistrationActivity Key Fields

| Field | Type | Notes |
|-------|------|-------|
| `action` | `RegistrationAction` | register, re_sign, check_mark_lost, roll_off, etc. |
| `previous_status` | `RegistrationStatus` | Status before action |
| `new_status` | `RegistrationStatus` | Status after action |
| `previous_position` | `int` | Queue position before |
| `new_position` | `int` | Queue position after |

---

## Architecture Reminders

- **APN is DECIMAL(10,2)** — All queue ordering uses `registration_number`. Never cast to int.
- **Inverted tiers** — LaborPower had inverted tier numbering. Our system uses natural ordering (lower APN = higher priority = dispatched first). Confirm with dispatch staff.
- **Audit immutability** — The PostgreSQL trigger on `audit_logs` fires automatically. RegistrationActivity is ALSO append-only (no updates).
- **Service layer owns transactions** — Services call `db.session.commit()`. Routers/blueprints do not.
- **Domain exceptions** — Services raise `ValueError` or custom exceptions. They do NOT raise HTTP exceptions (that's the router's job).
- **Member ≠ Student** — Never merge. Dispatch qualifications ≠ JATC training.
- **`locked_until` datetime** — User model uses datetime, not boolean `is_locked`.
- **8 contract codes** — WIREPERSON, S&C, STOCKPERSON, LFM, MARINE, TV&APPL, MARKET RECOVERY, RESIDENTIAL.

---

## Session Checklist

### Before Starting Each Session

- [ ] Verify Weeks 20–21 deliverables are in place (see checklist above)
- [ ] Verify you're on the `develop` branch
- [ ] Run existing tests: `pytest` (all ~520–535 should pass)
- [ ] Check `ruff` for lint issues

### After Completing Each Session

- [ ] All new tests pass
- [ ] All existing tests still pass
- [ ] `ruff` reports no new issues
- [ ] No new Alembic migrations needed (unless adding check mark tracking fields)

### Week 22 Completion Criteria

- [ ] ReferralBookService complete with all query and admin methods
- [ ] BookRegistrationService complete with registration, re-sign, and status transitions
- [ ] Check mark logic implemented (record, miss, restore, exempt)
- [ ] Roll-off rules implemented (max days, grace period, batch processing)
- [ ] RegistrationActivity records created for every state change
- [ ] All protection checks working (exempt, dispatched, short call)
- [ ] +53–62 new tests → ~575–595 total
- [ ] All documentation updated per end-of-session rule

---

## What Comes After Week 22

| Week | Focus | Dependencies |
|------|-------|-------------|
| **23** | **Services — Dispatch** (LaborRequestService, JobBidService, DispatchService) | Week 22 registration services |
| 24 | Queue Management (QueueService, re-sign enforcement, short call restoration) | Weeks 22–23 services |
| 25 | API Endpoints (Book/Registration API, LaborRequest/Bid API, Dispatch API) | Weeks 22–24 services |
| 26–28 | Frontend (Dispatch UI, Book views, Report navigation) | Week 25 APIs |
| 29–32+ | Report sprints (78 reports across P0–P3 priority levels) | Weeks 26–28 frontend |

---

## Related Documents

| Document | Location |
|----------|----------|
| Week 20 Instructions | `/docs/instructions/WEEK_20_INSTRUCTIONS.md` |
| Week 21 Instructions | `/docs/instructions/WEEK_21_INSTRUCTIONS.md` |
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
- ❌ Services raising HTTP exceptions → ✅ Services raise **domain exceptions** (ValueError, custom). Routers handle HTTP.

---

*Document Version: 1.0*
*Last Updated: February 3, 2026*
*Week 22 of IP2A-Database-v2 (UnionCore) — Phase 7: Referral & Dispatch*
