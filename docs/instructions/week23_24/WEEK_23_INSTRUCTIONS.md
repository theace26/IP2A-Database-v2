# Week 23 Instructions — Phase 7: Dispatch Services

> **Document Created:** February 4, 2026
> **Last Updated:** February 4, 2026
> **Version:** 1.0
> **Status:** Active — Ready for implementation (after Week 22 completes)
> **Project Version:** v0.9.5-alpha (Feature-Complete Weeks 1–19, Phase 7 Foundation Weeks 20–22)
> **Phase:** 7 — Referral & Dispatch System
> **Estimated Hours:** 10–12 hours across 3 sessions

---

## Purpose

Paste this document into a new Claude chat (or Claude Code session) to provide full context for Week 23 development. This week builds the three dispatch-side service layers: **LaborRequestService**, **JobBidService**, and **DispatchService**. These services consume the models created in Weeks 20–21 and complete the business rules left unfinished after Week 22.

Week 22 built the registration-side services (ReferralBookService, BookRegistrationService) and implemented business rules 1–10 and 14. Week 23 completes the service layer with dispatch-side logic covering rules 11–13 plus the full dispatch lifecycle.

---

## Project Context (Condensed)

**Project:** IP2A-Database-v2 (UnionCore) — workplace organization operations management platform for IBEW Local 46
**Replaces:** LaborPower (referral/dispatch), Access Database (member records), QuickBooks (dues sync)
**Users:** ~40 staff + ~4,000 members
**GitHub:** theace26

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, **FastAPI**, SQLAlchemy 2.x |
| Frontend | Jinja2 + HTMX + Alpine.js + **DaisyUI** (Tailwind CSS) |
| Database | PostgreSQL 16 (Railway) |
| Payments | Stripe (Checkout Sessions + Webhooks) — live in production |
| Monitoring | **Sentry** (NOT Grafana/Loki) — ADR-007 |
| Auth | JWT + bcrypt + HTTP-only cookies |
| Testing | pytest + httpx (~490+ tests) |
| Reports | WeasyPrint (PDF) + openpyxl (Excel) + Chart.js |

### Current Metrics (Post-Week 22)

| Metric | Value |
|--------|-------|
| Tests | ~490+ |
| ORM Models | 32 (26 existing + 6 Phase 7) |
| API Endpoints | ~150 |
| ADRs | 15 (ADR-015 covers Phase 7 architecture) |
| Phase 7 Enums | 19 in `phase7_enums.py` |
| Phase 7 Models | 6 (ReferralBook, BookRegistration, RegistrationActivity, LaborRequest, JobBid, Dispatch) |
| Phase 7 Services | 2 (ReferralBookService, BookRegistrationService) |

---

## Working Copy & Workflow

- **Working copy (OneDrive):** `D:\OneDrive\Documents\Claude.ai\IP2A-Database-v2\`
- **Live project:** `C:\Users\Xerxes\Projects\IP2A-Database-v2\`
- **Workflow:** Claude outputs files → Xerxes manually copies to live project
- **Branch:** `develop` at v0.9.5-alpha (main needs merge from develop)

---

## Prerequisites Checklist

Before starting Week 23, verify:

- [ ] Week 22 complete — ReferralBookService and BookRegistrationService exist and pass tests
- [ ] All 6 Phase 7 models exist in `src/models/`
- [ ] All 6 Phase 7 schemas exist in `src/schemas/`
- [ ] 19 Phase 7 enums exist in `src/db/enums/phase7_enums.py`
- [ ] `src/seed/phase7_seed.py` seeds 11 referral books
- [ ] `PHASE7_SCHEMA_DECISIONS.md` documents all 5 pre-implementation decisions
- [ ] `pytest -v --tb=short` passes (~490+ tests green)

---

## What Already Exists (from Weeks 20–22)

### Models (all 6 built)

| Model | File | Key Features |
|-------|------|-------------|
| ReferralBook | `src/models/referral_book.py` | classification, region, referral_start_time, internet_bidding_enabled |
| BookRegistration | `src/models/book_registration.py` | registration_number as DECIMAL(10,2), check_marks, exempt status, rolloff |
| RegistrationActivity | `src/models/registration_activity.py` | Append-only (no updated_at), before/after status tracking |
| LaborRequest | `src/models/labor_request.py` | workers_requested/dispatched, bidding windows, generates_checkmark |
| JobBid | `src/models/job_bid.py` | bid_status, rejection tracking for 1-year suspension |
| Dispatch | `src/models/dispatch.py` | Links member → job_request → employer, short call restoration |

### Services (2 built)

| Service | File | Methods |
|---------|------|---------|
| ReferralBookService | `src/services/referral_book_service.py` | get_by_id, get_by_code, get_all_active, get_by_classification, get_by_region, get_book_stats, create_book, update_book, activate/deactivate |
| BookRegistrationService | `src/services/book_registration_service.py` | register_member, re_sign_member, resign_member, roll_off_member, mark_dispatched, get_book_queue, get_member_registrations, record_check_mark, grant/revoke_exempt_status, process_roll_offs, get_re_sign_reminders |

### Key Design Decisions (ADR-015)

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Separate JobBid model | Cleaner audit trail, rejection tracking for 1-year suspension |
| 2 | MemberTransaction independent of DuesPayment | No breaking changes to live Stripe integration |
| 3 | Per-book exempt status on BookRegistration | More flexible than global Member exempt flag |
| 4 | Dual audit pattern (RegistrationActivity + audit_logs) | Fast domain queries + NLRA 7-year compliance |
| 5 | APN as DECIMAL(10,2) | Preserves LaborPower FIFO ordering exactly |

---

## Week 23 Scope — Dispatch Services

### Session 23A: LaborRequestService (3–4 hours)

**Purpose:** Manage employer labor requests — the demand side of the dispatch equation.

**File to create:** `src/services/labor_request_service.py`

#### Methods to Implement

| Method | Description | Business Rules |
|--------|-------------|---------------|
| `create_request` | Create new labor request from employer | Rule 3: Must be submitted by 3 PM for next morning |
| `update_request` | Modify pending request | Only if status is OPEN |
| `cancel_request` | Cancel unfilled request | Update status, release reserved slots |
| `fill_request` | Mark request as filled (all workers dispatched) | Automatic when workers_dispatched == workers_requested |
| `expire_request` | Mark overdue unfilled requests as expired | Batch processing for end-of-day cleanup |
| `get_by_id` | Fetch single request with relationships | Eager-load employer, book, bids |
| `get_open_requests` | All unfilled requests, ordered by date | Filter by book, classification, region |
| `get_requests_for_book` | Requests targeting a specific book | For dispatch board view |
| `get_employer_requests` | Request history for an employer | For employer detail view |
| `determine_check_mark` | Pre-calculate generates_checkmark flag | Rule 11: No check marks for specialty, MOU, early start, under scale, short call, employer rejection |
| `validate_bidding_window` | Check if request is in bidding window | Rule 8: 5:30 PM – 7:00 AM |
| `get_requests_for_morning` | Requests ready for morning referral | Rule 2: Ordered by classification referral time |

#### Business Rules Implemented

**Rule 3 — Labor Request Cutoff:**
- Employer requests must be in by 3:00 PM for next-morning referral
- Requests after 3 PM go to following day or online bidding window
- Internet/Job Line available after 5:30 PM

**Rule 4 — Agreement Types:**
- PLA, CWA, TERO requests follow their own referral terms
- `agreement_type` on LaborRequest acts as rule selector
- TERO requests only match TERO book registrations

**Rule 11 — No Check Mark Exceptions:**
Pre-calculate `generates_checkmark = False` when:
- Specialty skills not in CBA
- MOU site requests
- Start times before 6:00 AM
- Under scale work recovery
- Short call requests (≤10 business days)
- Employer-initiated rejection

#### Expected Code Structure

```python
# src/services/labor_request_service.py
from datetime import datetime, time
from sqlalchemy.orm import Session
from src.models.labor_request import LaborRequest
from src.db.enums.phase7_enums import LaborRequestStatus, AgreementType

class LaborRequestService:
    """Service for managing employer labor requests (dispatch demand side)."""

    # --- CUTOFF CONSTANTS ---
    MORNING_CUTOFF = time(15, 0)     # 3:00 PM for next-morning requests
    BIDDING_OPEN = time(17, 30)       # 5:30 PM online bidding opens
    BIDDING_CLOSE = time(7, 0)        # 7:00 AM online bidding closes
    EMPLOYER_CHECKIN = time(15, 0)    # 3:00 PM check-in deadline for web dispatches

    @staticmethod
    def create_request(db: Session, *, employer_id: int, book_id: int,
                       workers_requested: int, **kwargs) -> LaborRequest:
        """Create a new labor request. Validates cutoff time (Rule 3)."""
        ...

    @staticmethod
    def determine_check_mark(request: LaborRequest) -> bool:
        """Pre-calculate whether this request generates check marks (Rule 11).

        Returns False for: specialty skills, MOU sites, early starts (<6 AM),
        under scale, short calls, employer rejections.
        """
        ...

    @staticmethod
    def validate_bidding_window(request: LaborRequest) -> bool:
        """Check if current time is within the online bidding window (Rule 8).
        Open: 5:30 PM to 7:00 AM next day.
        """
        ...

    @staticmethod
    def get_requests_for_morning(db: Session, *, target_date=None) -> list[LaborRequest]:
        """Get all requests ready for morning referral, ordered by
        classification referral time (Rule 2):
        Wire 8:30 AM → S&C/Marine/Stock/LFM/Residential 9:00 AM → Tradeshow 9:30 AM
        """
        ...

    @staticmethod
    def cancel_request(db: Session, request_id: int, *, reason: str = None) -> LaborRequest:
        """Cancel an open request. Only valid for OPEN status."""
        ...

    @staticmethod
    def expire_request(db: Session, request_id: int) -> LaborRequest:
        """Mark unfilled request as expired. Called by end-of-day batch."""
        ...

    @staticmethod
    def get_open_requests(db: Session, *, book_id: int = None,
                          classification: str = None) -> list[LaborRequest]:
        """All unfilled requests, optionally filtered by book or classification."""
        ...
```

#### Test Scenarios for Session 23A

| Test | Asserts |
|------|---------|
| Create request before 3 PM cutoff | Request created with OPEN status |
| Create request after 3 PM cutoff | Raises ValueError or flags for next-day |
| Cancel open request | Status → CANCELLED |
| Cancel already-filled request | Raises ValueError |
| Expire unfilled request | Status → EXPIRED |
| Check mark determination — normal request | `generates_checkmark = True` |
| Check mark determination — specialty skill | `generates_checkmark = False` |
| Check mark determination — short call | `generates_checkmark = False` |
| Check mark determination — early start (<6 AM) | `generates_checkmark = False` |
| Bidding window validation — 6 PM (in window) | Returns True |
| Bidding window validation — 10 AM (out of window) | Returns False |
| Morning requests ordering | Wire books first, then S&C/Marine/etc., then Tradeshow |
| Agreement type filtering | TERO request only returns TERO registrations |

**Test target for 23A:** +15–18 tests

---

### Session 23B: JobBidService (3–4 hours)

**Purpose:** Manage the online/email bidding workflow — Rule 8 implementation.

**File to create:** `src/services/job_bid_service.py`

#### Methods to Implement

| Method | Description | Business Rules |
|--------|-------------|---------------|
| `place_bid` | Member places bid on a labor request | Rule 8: Only during 5:30 PM – 7:00 AM window |
| `withdraw_bid` | Member withdraws pending bid | Only if still PENDING |
| `accept_bid` | Staff accepts a bid (dispatches member) | Creates Dispatch record, updates registration |
| `reject_bid` | Member rejects accepted bid | Rule 8: Counts as quit; 2nd in 12 months = 1-year suspension |
| `process_bids` | Process all pending bids for a request | FIFO by queue position (APN) |
| `check_bidding_eligibility` | Verify member can bid | Active registration, not exempt, no suspension |
| `check_suspension_status` | Check if member has bidding privileges | Track rejections in last 12 months |
| `get_bids_for_request` | All bids on a labor request | For staff review |
| `get_member_bid_history` | Bid history for a member | For member profile and reports |
| `record_infraction` | Record bidding infraction | Creates entry in bidding_infractions table |
| `revoke_bidding_privileges` | Suspend member's bidding for 1 year | Rule 8: 2nd rejection in 12 months |

#### Business Rules Implemented

**Rule 8 — Internet/Email Bidding:**
- Available 5:30 PM to 7:00 AM Pacific
- Member must check in with employer by 3:00 PM on dispatch day
- Reject after bidding = **counted as quit** (triggers Rule 12 consequences)
- Second rejection within 12 months = **lose bidding privileges for 1 year**
- `bidding_infractions` table tracks violations with `privilege_revoked_until` date

**Bidding Workflow:**
```
Member places bid (5:30 PM – 7 AM)
    → Bid recorded as PENDING
    → Staff processes bids in queue order (FIFO by APN)
    → Bid ACCEPTED: Member dispatched (creates Dispatch record)
    → Bid NOT_SELECTED: Higher-priority member dispatched instead
    → Member REJECTS accepted bid:
        → First rejection in 12 months: Warning, counted as quit
        → Second rejection in 12 months: Bidding privileges revoked for 1 year
```

#### Expected Code Structure

```python
# src/services/job_bid_service.py
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.models.job_bid import JobBid
from src.models.dispatch import Dispatch
from src.db.enums.phase7_enums import BidStatus

class JobBidService:
    """Service for online/email bidding workflow (Rule 8)."""

    REJECTION_WINDOW_MONTHS = 12
    SUSPENSION_DURATION_MONTHS = 12
    MAX_REJECTIONS_BEFORE_SUSPENSION = 2

    @staticmethod
    def place_bid(db: Session, *, member_id: int, labor_request_id: int,
                  registration_id: int, bid_method: str = "online") -> JobBid:
        """Place a bid on a labor request.

        Validates:
        - Current time is within bidding window (5:30 PM – 7:00 AM)
        - Member has active registration on the relevant book
        - Member is not suspended from bidding
        - Member has not already bid on this request
        """
        ...

    @staticmethod
    def reject_bid(db: Session, bid_id: int, *, reason: str = None) -> JobBid:
        """Member rejects an accepted bid. This counts as a quit (Rule 8/12).

        Checks rejection count in last 12 months. If this is the 2nd rejection,
        revokes bidding privileges for 1 year.
        """
        ...

    @staticmethod
    def process_bids(db: Session, labor_request_id: int) -> list[JobBid]:
        """Process all pending bids for a request in FIFO order (by APN).

        For each slot to fill:
        1. Find highest-priority pending bid (lowest APN)
        2. Mark bid as ACCEPTED
        3. Create Dispatch record via DispatchService
        4. Mark remaining bids as NOT_SELECTED if request is filled
        """
        ...

    @staticmethod
    def check_suspension_status(db: Session, member_id: int) -> dict:
        """Check if member has active bidding suspension.

        Returns: {
            'is_suspended': bool,
            'suspended_until': datetime | None,
            'rejections_in_window': int,
            'next_rejection_causes_suspension': bool
        }
        """
        ...
```

#### Test Scenarios for Session 23B

| Test | Asserts |
|------|---------|
| Place bid during valid window (6 PM) | Bid created with PENDING status |
| Place bid outside window (10 AM) | Raises ValueError |
| Place bid while suspended | Raises ValueError |
| Place duplicate bid on same request | Raises ValueError |
| Accept bid → creates Dispatch | Dispatch record exists, registration marked dispatched |
| Reject accepted bid — first time | Counts as quit, warning recorded |
| Reject accepted bid — second in 12 months | Bidding privileges revoked for 1 year |
| Process bids — FIFO ordering | Lowest APN member selected first |
| Process bids — request fully filled | Remaining bids marked NOT_SELECTED |
| Check suspension — no infractions | `is_suspended = False` |
| Check suspension — active suspension | `is_suspended = True`, `suspended_until` set |
| Member bid history query | Returns all bids ordered by date |

**Test target for 23B:** +12–15 tests

---

### Session 23C: DispatchService (3–4 hours)

**Purpose:** The core dispatch workflow — the central service that connects employer requests to member registrations.

**File to create:** `src/services/dispatch_service.py`

#### Methods to Implement

| Method | Description | Business Rules |
|--------|-------------|---------------|
| `create_dispatch` | Dispatch a member to a job | Core workflow: select from queue, create record, update registration |
| `dispatch_from_queue` | Auto-select next member from queue | FIFO by APN, Book 1 before Book 2 |
| `dispatch_by_name` | Foreperson-by-name dispatch | Rule 13: Anti-collusion validation |
| `record_check_in` | Member checks in with employer | Required by 3 PM for web dispatches |
| `terminate_dispatch` | End a dispatch (quit, discharge, RIF, etc.) | Rule 12: Different consequences per reason |
| `process_quit` | Handle member quit | Roll off ALL books, 2-week foreperson blackout |
| `process_discharge` | Handle member discharge | Roll off ALL books, 2-week foreperson blackout |
| `process_rif` | Handle reduction in force | Standard termination, no penalty |
| `process_short_call_end` | Handle end of short call | Rule 9: Restore position if ≤10 days |
| `handle_short_call_restoration` | Restore member to prior queue position | Rule 9: Max 2 per cycle, ≤3 days unlimited |
| `get_dispatch_by_id` | Fetch dispatch with relationships | Eager-load member, request, employer |
| `get_active_dispatches` | All currently active dispatches | For dispatch board |
| `get_member_dispatch_history` | Full dispatch history for a member | For member profile |
| `get_book_dispatch_stats` | Dispatch statistics per book | For dashboard and reports |

#### Business Rules Implemented

**Rule 9 — Short Calls:**
- Jobs ≤10 business days (excluding referral day and holidays)
- Member limited to "unemployed status" (back on book) **twice** for short calls
- Short calls ≤3 working days = **no limit** (don't count toward the 2)
- Laid off during short call period = registration restored (position preserved)
- "Long Call" request = registration restored

**Rule 12 — Quit or Discharge:**
- Member is **rolled completely off ALL books** (not just the dispatched book)
- Cannot fill "Foreperson-by-Name" request for **2 weeks** after quit/discharge from same employer
- Creates entry in `blackout_periods` table
- Different from RIF (Reduction In Force) which has no penalty

**Rule 13 — Foreperson By Name:**
- Anti-collusion rule: employer requests specific member by name
- Member **cannot** be dispatched by-name if they communicated with employer about the job
- Staff must flag/verify foreperson requests
- 2-week blackout after quit/discharge from that employer

**Dispatch Workflow — Morning Referral:**
```
1. Staff opens morning dispatch (per classification time — Rule 2)
2. For each open LaborRequest:
   a. Get book queue (FIFO by APN)
   b. Book 1 members dispatched BEFORE Book 2
   c. For each candidate:
      - Check active registration
      - Check not exempt
      - Check no blackout period with this employer
      - If generates_checkmark: candidate can accept or get check mark
      - If accepted: create Dispatch, mark registration as DISPATCHED
      - If declined (check mark): increment check_marks via BookRegistrationService
3. After morning referral completes, remaining requests enter online bidding
```

**Tier/Book Priority:**
```
Book 1 (local journeymen)  → dispatched FIRST
Book 2 (travelers)         → dispatched ONLY if Book 1 exhausted
Book 3 (travelers/other)   → dispatched ONLY if Book 2 exhausted
Book 4 (apprentice/other)  → last resort
```

#### Expected Code Structure

```python
# src/services/dispatch_service.py
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.models.dispatch import Dispatch
from src.models.book_registration import BookRegistration
from src.db.enums.phase7_enums import DispatchStatus, TermReason

class DispatchService:
    """Core dispatch workflow service — connects employer requests to members."""

    FOREPERSON_BLACKOUT_DAYS = 14  # 2-week blackout after quit/discharge
    SHORT_CALL_MAX_DAYS = 10       # ≤10 business days = short call
    SHORT_CALL_NO_LIMIT_DAYS = 3   # ≤3 days don't count toward limit
    SHORT_CALL_MAX_PER_CYCLE = 2   # Max 2 short call returns per cycle

    @staticmethod
    def create_dispatch(db: Session, *, member_id: int, labor_request_id: int,
                        registration_id: int, dispatch_method: str,
                        is_short_call: bool = False, **kwargs) -> Dispatch:
        """Create a dispatch record and update related entities.

        Side effects:
        - BookRegistration status → DISPATCHED (via BookRegistrationService)
        - LaborRequest workers_dispatched incremented
        - RegistrationActivity logged (via dual audit pattern)
        - audit_logs entry created (NLRA compliance)
        """
        ...

    @staticmethod
    def dispatch_from_queue(db: Session, labor_request_id: int) -> Dispatch | None:
        """Auto-select next eligible member from queue and dispatch.

        Selection order:
        1. Book 1 first, then Book 2, then Book 3+
        2. Within each book tier: FIFO by APN (lowest first)
        3. Skip exempt members, blackout periods, suspended members
        """
        ...

    @staticmethod
    def dispatch_by_name(db: Session, *, labor_request_id: int,
                         member_id: int, **kwargs) -> Dispatch:
        """Foreperson-by-name dispatch (Rule 13).

        Validates:
        - No active blackout period for this member-employer pair
        - Anti-collusion flag (staff must verify)
        """
        ...

    @staticmethod
    def terminate_dispatch(db: Session, dispatch_id: int, *,
                           term_reason: TermReason, **kwargs) -> Dispatch:
        """Terminate a dispatch. Routes to appropriate handler based on reason.

        QUIT/DISCHARGED → process_quit/process_discharge (Rule 12)
        RIF → process_rif (no penalty)
        SHORT_CALL_END → process_short_call_end (Rule 9)
        """
        ...

    @staticmethod
    def process_quit(db: Session, dispatch: Dispatch) -> None:
        """Handle quit termination (Rule 12).

        1. Roll member off ALL books (not just dispatched book)
        2. Create blackout_period entry (2 weeks, foreperson-by-name blocked)
        3. Log to RegistrationActivity and audit_logs
        """
        ...

    @staticmethod
    def process_discharge(db: Session, dispatch: Dispatch) -> None:
        """Handle discharge termination (Rule 12). Same consequences as quit."""
        ...

    @staticmethod
    def process_short_call_end(db: Session, dispatch: Dispatch) -> None:
        """Handle short call completion (Rule 9).

        If job was ≤10 business days:
        - Restore member to original queue position
        - ≤3 days: doesn't count toward 2-per-cycle limit
        - >3 days: counts toward limit (max 2 per registration cycle)
        """
        ...
```

#### Interaction with Existing Services

```
DispatchService
    ├── calls BookRegistrationService.mark_dispatched()
    ├── calls BookRegistrationService.roll_off_member() (for quit/discharge)
    ├── calls BookRegistrationService.restore_position() (for short call end)
    ├── calls BookRegistrationService.record_check_mark() (for declined offers)
    ├── reads LaborRequest model (via LaborRequestService)
    ├── reads JobBid model (via JobBidService for web dispatch)
    ├── writes Dispatch model
    ├── writes RegistrationActivity (dual audit — ADR-015 Decision 4)
    └── writes audit_logs (NLRA compliance — ADR-012)
```

#### Test Scenarios for Session 23C

| Test | Asserts |
|------|---------|
| Create dispatch — happy path | Dispatch created, registration marked DISPATCHED |
| Dispatch from queue — Book 1 before Book 2 | Book 1 member selected over Book 2 |
| Dispatch from queue — FIFO by APN | Lower APN dispatched first |
| Dispatch from queue — skip exempt member | Exempt member skipped, next eligible selected |
| Dispatch from queue — skip blackout member | Blackout member skipped |
| Dispatch by name — no blackout | Dispatch succeeds |
| Dispatch by name — active blackout | Raises ValueError |
| Terminate — quit | Member rolled off ALL books, blackout created |
| Terminate — discharge | Same as quit (Rule 12) |
| Terminate — RIF | Standard termination, no penalty |
| Terminate — short call end (≤3 days) | Position restored, doesn't count toward limit |
| Terminate — short call end (4–10 days) | Position restored, counts toward limit |
| Terminate — short call end (3rd time in cycle) | Raises ValueError (max 2 per cycle) |
| Active dispatches query | Returns only ACTIVE/CHECKED_IN dispatches |
| Member dispatch history | Returns all dispatches ordered by date |

**Test target for 23C:** +15–18 tests

---

## Business Rules Implementation Matrix (Updated)

| Rule | Name | Implemented In | Week |
|------|------|---------------|------|
| 1 | Office Hours & Regions | ReferralBook model (referral_start_time) | 20B |
| 2 | Morning Referral Order | LaborRequestService.get_requests_for_morning | **23A** |
| 3 | Labor Request Cutoff | LaborRequestService.create_request | **23A** |
| 4 | Agreement Types | LaborRequestService (agreement_type filter) | **23A** |
| 5 | Registration Rules | BookRegistrationService.register_member | 22B |
| 6 | Re-Registration Triggers | BookRegistrationService (re-sign logic) | 22B |
| 7 | Re-Sign 30-Day Cycle | BookRegistrationService.get_re_sign_reminders | 22C |
| 8 | Internet/Email Bidding | JobBidService (full workflow) | **23B** |
| 9 | Short Calls | DispatchService.process_short_call_end | **23C** |
| 10 | Check Marks (Penalty) | BookRegistrationService.record_check_mark | 22C |
| 11 | No Check Mark Exceptions | LaborRequestService.determine_check_mark | **23A** |
| 12 | Quit/Discharge | DispatchService.process_quit / process_discharge | **23C** |
| 13 | Foreperson By Name | DispatchService.dispatch_by_name | **23C** |
| 14 | Exempt Status | BookRegistrationService.grant_exempt_status | 22C |

**After Week 23: All 14 business rules will be implemented in the service layer.**

---

## Architecture Reminders

- **Member ≠ Student.** Phase 7 models FK to `members`, NOT `students`. Members are IBEW union members. Students are pre-apprenticeship participants.
- **Book ≠ Contract.** STOCKMAN book → STOCKPERSON contract. 3 books have no contract code (Tradeshow, TERO, Utility Worker).
- **APN is DECIMAL(10,2).** Integer part = Excel serial date. Decimal part = same-day sort key. NEVER truncate to INTEGER.
- **Services raise domain exceptions (ValueError, custom).** Routers handle HTTP status codes. Services NEVER raise HTTPException.
- **Dual audit pattern (ADR-015 Decision 4).** Every registration/dispatch change writes to BOTH RegistrationActivity (domain queries) AND audit_logs (NLRA 7-year compliance).
- **FastAPI — NOT Flask.** Use APIRouter, Depends, HTTPException in routers. Use uvicorn, not flask run.

---

## Session Checklist

### Before Each Session
- [ ] `git checkout develop && git pull origin develop`
- [ ] `pytest -v --tb=short` — verify all tests pass
- [ ] Review this document for the current session's scope

### After Each Session
- [ ] All new tests pass (`pytest -v`)
- [ ] Code formatted (`ruff check . --fix && ruff format .`)
- [ ] `git add . && git commit -m "feat(phase7): [session description]"`
- [ ] `git push origin develop`

---

## Week 23 Completion Criteria

- [ ] `src/services/labor_request_service.py` created with all methods
- [ ] `src/services/job_bid_service.py` created with all methods
- [ ] `src/services/dispatch_service.py` created with all methods
- [ ] Business rules 11, 12, 13 implemented and tested
- [ ] Bidding workflow (Rule 8) fully implemented: place, accept, reject, suspend
- [ ] Dispatch workflow: morning referral, by-name, termination handling
- [ ] Short call restoration logic (Rule 9) in DispatchService
- [ ] Quit/discharge cascade (Rule 12): roll off ALL books + blackout_periods
- [ ] All new tests pass
- [ ] ~540–560 total tests (was ~490+, target +50–70)

---

## What Comes After

| Week | Focus | Status |
|------|-------|--------|
| 20–22 | Models, Enums, Schemas, Registration Services | ✅ Complete |
| **23** | **Dispatch Services (LaborRequest, JobBid, Dispatch)** | **← YOU ARE HERE** |
| 24 | Queue Management (QueueService, enforcement, analytics) | 🔜 Next |
| 25 | API Endpoints (Routers for all Phase 7 services) | 🔜 Pending |
| 26 | Frontend — Books & Registration UI | 🔜 Pending |
| 27 | Frontend — Dispatch Workflow UI | 🔜 Pending |
| 28 | Frontend — Reports Navigation & Dashboard | 🔜 Pending |
| 29–32+ | Report Sprints (78 reports across P0–P3) | 🔜 Pending |

---

## Related Documents

| Document | Location |
|----------|----------|
| Phase 7 Continuity Doc | `docs/phase7/PHASE7_CONTINUITY_DOC.md` |
| Phase 7 Schema Decisions | `docs/phase7/PHASE7_SCHEMA_DECISIONS.md` |
| Implementation Plan v2 | `docs/phase7/PHASE7_IMPLEMENTATION_PLAN_v2.md` |
| Referral & Dispatch Plan | `docs/phase7/PHASE7_REFERRAL_DISPATCH_PLAN.md` |
| ADR-015 (Referral Architecture) | `docs/decisions/ADR-015-referral-dispatch-architecture.md` |
| ADR-012 (Audit Logging) | `docs/decisions/ADR-012-audit-logging.md` |
| LaborPower Gap Analysis | `docs/phase7/LABORPOWER_GAP_ANALYSIS.md` |
| Local 46 Referral Books | `docs/phase7/LOCAL46_REFERRAL_BOOKS.md` |
| Backend Roadmap v3.1 | `docs/IP2A_BACKEND_ROADMAP.md` |
| Week 20 Instructions | `docs/instructions/WEEK_20_INSTRUCTIONS.md` |
| Week 21 Instructions | `docs/instructions/WEEK_21_INSTRUCTIONS.md` |
| Week 22 Instructions | `docs/instructions/WEEK_22_INSTRUCTIONS.md` |

---

## End-of-Session Documentation (MANDATORY)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.

---

## Known Pitfalls (Carry Forward)

- ❌ Flask / flask run / Blueprints → ✅ **FastAPI / uvicorn / APIRouter**
- ❌ Grafana / Loki → ✅ **Sentry** (ADR-007)
- ❌ Missing DaisyUI references → ✅ Always mention DaisyUI with frontend stack
- ❌ `is_locked` → ✅ `locked_until` (datetime, not boolean)
- ❌ 7 contract codes → ✅ **8** (RESIDENTIAL is the 8th)
- ❌ 80–120 hrs Phase 7 → ✅ **100–150 hrs**
- ❌ Week 15 "missing" → ✅ Intentionally skipped (14→16)
- ❌ APN as INTEGER → ✅ **DECIMAL(10,2)** — preserves FIFO ordering
- ❌ LaborPower tier ordering → ✅ **INVERTED** in LaborPower — verify with dispatch staff
- ❌ Services raising HTTP exceptions → ✅ Services raise **domain exceptions** (ValueError, custom). Routers handle HTTP.
- ❌ 14 ADRs → ✅ **15 ADRs** (ADR-015 added February 4, 2026)

---

*Week 23 Instructions — Phase 7: Dispatch Services*
*Created: February 4, 2026*
*Project Version: v0.9.5-alpha*
