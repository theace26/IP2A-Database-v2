# Week 24 Instructions — Phase 7: Queue Management & Enforcement

> **Document Created:** February 4, 2026
> **Last Updated:** February 4, 2026
> **Version:** 1.0
> **Status:** Active — Ready for implementation (after Week 23 completes)
> **Project Version:** v0.9.5-alpha (Feature-Complete Weeks 1–19, Phase 7 Foundation Weeks 20–22)
> **Phase:** 7 — Referral & Dispatch System
> **Estimated Hours:** 10–12 hours across 3 sessions

---

## Purpose

Paste this document into a new Claude chat (or Claude Code session) to provide full context for Week 24 development. This week builds the **QueueService** for centralized queue management, implements **automated enforcement** (re-sign deadlines, roll-off processing, short call limits), and adds **queue analytics** for the dashboard.

Week 23 built the dispatch-side services (LaborRequestService, JobBidService, DispatchService). Week 24 ties everything together with a centralized queue orchestrator and the batch processing jobs that keep the system clean.

---

## Project Context (Condensed)

**Project:** IP2A-Database-v2 (UnionCore) — IBEW Local 46 operations management platform
**Replaces:** LaborPower (referral/dispatch), Access Database, QuickBooks (sync)
**Users:** ~40 staff + ~4,000 members | **GitHub:** theace26

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, **FastAPI**, SQLAlchemy 2.x |
| Frontend | Jinja2 + HTMX + Alpine.js + **DaisyUI** (Tailwind CSS) |
| Database | PostgreSQL 16 (Railway) |
| Auth | JWT + bcrypt + HTTP-only cookies |
| Testing | pytest + httpx |

### Current Metrics (Post-Week 23 — Estimated)

| Metric | Value |
|--------|-------|
| Tests | ~540–560 |
| ORM Models | 32 (26 existing + 6 Phase 7) |
| Phase 7 Services | 5 (ReferralBookService, BookRegistrationService, LaborRequestService, JobBidService, DispatchService) |
| ADRs | 15 |

---

## Working Copy & Workflow

- **Working copy (OneDrive):** `D:\OneDrive\Documents\Claude.ai\IP2A-Database-v2\`
- **Live project:** `C:\Users\Xerxes\Projects\IP2A-Database-v2\`
- **Workflow:** Claude outputs files → Xerxes manually copies to live project
- **Branch:** `develop` at v0.9.5-alpha

---

## Prerequisites Checklist

Before starting Week 24, verify:

- [ ] Week 23 complete — LaborRequestService, JobBidService, DispatchService exist and pass tests
- [ ] All 14 business rules have service-layer implementations
- [ ] Quit/discharge cascade (Rule 12) tested — member rolled off ALL books
- [ ] Short call termination (Rule 9) tested — position restoration works
- [ ] Bidding workflow (Rule 8) tested — suspension logic works
- [ ] `pytest -v --tb=short` passes (~540–560 tests green)

---

## What Already Exists (Post-Week 23)

### Services Built (5 total)

| Service | File | Key Methods |
|---------|------|-------------|
| ReferralBookService | `referral_book_service.py` | Book CRUD, stats, settings, activate/deactivate |
| BookRegistrationService | `book_registration_service.py` | Register, re-sign, resign, roll-off, check marks, exempt status, queue queries |
| LaborRequestService | `labor_request_service.py` | Create/cancel/expire requests, check mark determination, bidding window, morning referral ordering |
| JobBidService | `job_bid_service.py` | Place/withdraw/accept/reject bids, suspension tracking, infraction recording |
| DispatchService | `dispatch_service.py` | Dispatch from queue, by-name, termination handling (quit/discharge/RIF/short call), position restoration |

### Queue-Related Methods Already in BookRegistrationService

These methods were built in Week 22 but will be **called by QueueService** as a centralized orchestrator:

| Existing Method | What It Does |
|----------------|-------------|
| `get_book_queue(db, book_id)` | Returns FIFO-ordered queue by APN |
| `get_member_position(db, registration_id)` | Member's position in queue |
| `get_registrations_expiring_soon(db, days=7)` | Re-sign reminders approaching deadline |
| `process_roll_offs(db)` | Batch process expired re-signs |
| `record_check_mark(db, registration_id)` | Increment check marks, auto-rolloff at 3 |
| `is_protected_from_rolloff(registration)` | Check specialty/MOU/short call protection |

**Week 24 adds a QueueService layer ON TOP of these** for centralized orchestration, position recalculation, and analytics.

---

## Week 24 Scope — Queue Management & Enforcement

### Session 24A: QueueService — Core Queue Operations (3–4 hours)

**Purpose:** Centralized queue management that coordinates across all books and services.

**File to create:** `src/services/queue_service.py`

#### Methods to Implement

| Method | Description | Notes |
|--------|-------------|-------|
| `get_queue_snapshot` | Full queue state for a book | Position, member, APN, status, days_on_book, check marks |
| `get_multi_book_queue` | Queue state across multiple books | For members registered on Wire Seattle + Bremerton + Pt Angeles |
| `recalculate_positions` | Recalculate queue positions after dispatch/rolloff | Fill gaps when members leave the queue |
| `get_next_eligible` | Next member eligible for dispatch | Respects: exempt, blackout, suspension, Book 1→2→3 priority |
| `get_queue_depth` | How many eligible members on a book | For request fulfillment estimation |
| `estimate_wait_time` | Estimated days until dispatch for a member | Based on historical dispatch rate |
| `get_position_history` | How a member's position changed over time | For member profile and fairness auditing |
| `transfer_registration` | Move member between books (admin action) | Rare but needed for classification changes |

#### Queue Position Recalculation Logic

When a member is dispatched, quits, or is rolled off, the queue has a "gap." The system needs to determine how to handle this:

```
BEFORE dispatch of Member C (position 3):
  Position 1: Member A (APN 45001.23)
  Position 2: Member B (APN 45002.15)
  Position 3: Member C (APN 45003.00) ← DISPATCHED
  Position 4: Member D (APN 45004.50)
  Position 5: Member E (APN 45005.01)

AFTER dispatch — positions shift:
  Position 1: Member A (APN 45001.23) — unchanged
  Position 2: Member B (APN 45002.15) — unchanged
  Position 3: Member D (APN 45004.50) — moved up
  Position 4: Member E (APN 45005.01) — moved up
```

**Key rule:** Queue order is ALWAYS determined by APN (DECIMAL). Position numbers are **derived**, not stored. The `registration_number` (APN) field IS the ordering key. "Position" in the UI is just `ROW_NUMBER() OVER (ORDER BY registration_number)` for active registrations.

#### Expected Code Structure

```python
# src/services/queue_service.py
from datetime import datetime
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from src.models.book_registration import BookRegistration
from src.models.referral_book import ReferralBook
from src.db.enums.phase7_enums import RegistrationStatus

class QueueService:
    """Centralized queue management and analytics.

    This service coordinates across BookRegistrationService and
    DispatchService to provide a unified view of queue state.
    Queue ordering is ALWAYS by APN (DECIMAL) — position numbers are derived.
    """

    @staticmethod
    def get_queue_snapshot(db: Session, book_id: int, *,
                           include_exempt: bool = False) -> list[dict]:
        """Full queue state with derived positions.

        Returns list of dicts:
        [
            {
                'position': 1,
                'member_id': 123,
                'member_name': 'John Smith',
                'registration_number': Decimal('45001.23'),
                'registered_date': datetime,
                'days_on_book': 45,
                'check_marks': 1,
                'is_exempt': False,
                'exempt_reason': None,
                'last_re_sign': datetime,
                're_sign_due': datetime,
            },
            ...
        ]
        """
        ...

    @staticmethod
    def get_next_eligible(db: Session, book_id: int, *,
                          employer_id: int = None,
                          classification: str = None) -> BookRegistration | None:
        """Get next eligible member for dispatch.

        Skips:
        - Exempt members
        - Members with active blackout for this employer
        - Members with suspended bidding privileges (if web dispatch)
        - Rolled-off members

        Order: Book 1 before Book 2, then FIFO by APN within each tier.
        """
        ...

    @staticmethod
    def estimate_wait_time(db: Session, registration_id: int) -> dict:
        """Estimate days until dispatch based on historical rates.

        Returns:
        {
            'position': 15,
            'avg_dispatches_per_week': 3.2,
            'estimated_days': 33,
            'confidence': 'medium'  # low/medium/high based on data volume
        }
        """
        ...

    @staticmethod
    def get_queue_depth(db: Session, book_id: int) -> dict:
        """Queue depth analytics.

        Returns:
        {
            'total_registered': 150,
            'active': 130,
            'exempt': 12,
            'dispatched': 8,
            'eligible_for_dispatch': 120,
            'by_tier': {1: 80, 2: 40, 3: 10}
        }
        """
        ...
```

#### Test Scenarios for Session 24A

| Test | Asserts |
|------|---------|
| Queue snapshot — ordered by APN | Positions are sequential, ordered by registration_number |
| Queue snapshot — excludes rolled-off | Only ACTIVE registrations |
| Queue snapshot — include_exempt flag | Exempt shown when True, hidden when False |
| Multi-book queue — Wire member on 3 books | Returns entries from all 3 books |
| Next eligible — happy path | Returns lowest-APN active member |
| Next eligible — skips exempt | Exempt member bypassed |
| Next eligible — skips blackout | Blackout member bypassed |
| Next eligible — Book 1 before Book 2 | Book 1 member returned over Book 2 |
| Next eligible — empty book | Returns None |
| Queue depth — counts by category | Correct totals for active, exempt, dispatched |
| Wait time estimate — with history | Returns reasonable estimate |
| Wait time estimate — no dispatch history | Returns low confidence |

**Test target for 24A:** +12–15 tests

---

### Session 24B: Automated Enforcement (3–4 hours)

**Purpose:** Build batch processing for re-sign deadlines, expired registration cleanup, and check mark enforcement.

**File to create:** `src/services/enforcement_service.py`

These are the "cron job" operations that run daily (or on-demand) to keep the dispatch system clean and enforce business rules automatically.

#### Methods to Implement

| Method | Description | Business Rule |
|--------|-------------|---------------|
| `enforce_re_sign_deadlines` | Process expired re-signs (>30 days) | Rule 7: Roll off members who missed re-sign |
| `send_re_sign_reminders` | Flag members approaching re-sign deadline | Rule 7: Notification 7 days before due |
| `enforce_check_mark_limits` | Batch verify check mark counts | Rule 10: 3rd check mark = roll off |
| `process_expired_requests` | Expire unfilled labor requests past their date | Rule 3: Cleanup old requests |
| `process_expired_exemptions` | Revoke expired exempt statuses | Rule 14: Exempt periods have end dates |
| `process_expired_blackouts` | Clean up expired blackout periods | Rule 12: 2-week blackouts expire |
| `process_expired_suspensions` | Clean up expired bidding suspensions | Rule 8: 1-year suspensions expire |
| `daily_enforcement_run` | Master method — runs all enforcement checks | Called by scheduled task or admin trigger |
| `get_enforcement_report` | Summary of what enforcement would do (dry run) | For admin review before executing |

#### Re-Sign Enforcement Logic (Rule 7)

```
For each active BookRegistration:
    days_since_re_sign = today - last_re_sign_date

    IF days_since_re_sign >= 30 AND NOT is_exempt:
        → Roll off member from THIS book
        → Log to RegistrationActivity: "AUTO_ROLLOFF_RESIGN_EXPIRED"
        → Log to audit_logs (NLRA compliance)

    IF days_since_re_sign >= 23 AND days_since_re_sign < 30:
        → Flag for reminder notification
        → Add to re_sign_reminders query result

Note: Exempt members (Rule 14) are SKIPPED during re-sign enforcement.
Their re-sign timer is paused during exemption period.
```

#### Expected Code Structure

```python
# src/services/enforcement_service.py
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.services.book_registration_service import BookRegistrationService
from src.db.enums.phase7_enums import RegistrationStatus, RegistrationAction

class EnforcementService:
    """Automated enforcement of dispatch business rules.

    These methods are designed for batch processing — called by
    scheduled tasks (FastAPI BackgroundTasks or future Celery — ADR-006)
    or triggered manually by admin staff.
    """

    RE_SIGN_DEADLINE_DAYS = 30
    RE_SIGN_REMINDER_DAYS = 7   # Remind 7 days before deadline
    BLACKOUT_DURATION_DAYS = 14
    SUSPENSION_DURATION_MONTHS = 12

    @staticmethod
    def daily_enforcement_run(db: Session, *, dry_run: bool = False) -> dict:
        """Master enforcement method — runs all checks.

        If dry_run=True, returns report of what WOULD happen without making changes.

        Returns:
        {
            'timestamp': datetime,
            'dry_run': bool,
            're_sign_rolloffs': 5,
            're_sign_reminders': 12,
            'expired_requests': 3,
            'expired_exemptions': 1,
            'expired_blackouts': 2,
            'expired_suspensions': 0,
            'details': [...]
        }
        """
        ...

    @staticmethod
    def enforce_re_sign_deadlines(db: Session, *, dry_run: bool = False) -> list[dict]:
        """Process all registrations past 30-day re-sign deadline.

        Skips exempt members (Rule 14).
        Returns list of affected registrations with action taken.
        """
        ...

    @staticmethod
    def send_re_sign_reminders(db: Session) -> list[dict]:
        """Flag members with re-sign due within 7 days.

        Returns list of registrations needing reminders.
        Does NOT roll off — just flags for notification.
        """
        ...

    @staticmethod
    def process_expired_requests(db: Session, *, dry_run: bool = False) -> list[dict]:
        """Expire unfilled labor requests past their target date."""
        ...

    @staticmethod
    def process_expired_exemptions(db: Session, *, dry_run: bool = False) -> list[dict]:
        """Revoke exempt status where end_date has passed.

        After revocation, member's re-sign timer resumes.
        If re-sign would now be overdue, give grace period (end_date + 7 days).
        """
        ...

    @staticmethod
    def get_enforcement_report(db: Session) -> dict:
        """Preview what enforcement would do without making changes.

        Calls daily_enforcement_run with dry_run=True.
        For admin dashboard display.
        """
        return EnforcementService.daily_enforcement_run(db, dry_run=True)
```

#### Test Scenarios for Session 24B

| Test | Asserts |
|------|---------|
| Re-sign enforcement — member at 31 days | Rolled off |
| Re-sign enforcement — member at 29 days | NOT rolled off |
| Re-sign enforcement — exempt member at 45 days | NOT rolled off (exempt) |
| Re-sign reminder — member at 25 days | Included in reminders |
| Re-sign reminder — member at 15 days | NOT included (too early) |
| Expired request processing | OPEN requests past date → EXPIRED |
| Expired exemption — past end_date | Exempt status revoked, re-sign timer resumes |
| Expired exemption — grace period | 7-day grace period for re-sign after exemption ends |
| Expired blackout — 15 days old | Blackout removed |
| Expired suspension — 13 months old | Suspension removed, bidding restored |
| Daily enforcement — dry run | Returns report, NO database changes |
| Daily enforcement — live run | Changes committed, report returned |
| Enforcement report matches dry run | Same output as dry_run=True |

**Test target for 24B:** +13–16 tests

---

### Session 24C: Queue Analytics & Integration Tests (3–4 hours)

**Purpose:** Add analytics methods to QueueService and write integration tests that verify the full dispatch lifecycle end-to-end.

**Methods to add to `src/services/queue_service.py`:**

| Method | Description | Used By |
|--------|-------------|---------|
| `get_book_utilization` | Dispatch rate, avg days on book, turnover | Dashboard + reports |
| `get_dispatch_rate` | Dispatches per day/week/month per book | Dashboard |
| `get_avg_wait_time` | Average days between registration and dispatch | Reports |
| `get_classification_summary` | Cross-book summary by classification | Landing page |
| `get_daily_activity_log` | All queue changes for a given day | Daily operations report |
| `get_member_queue_status` | All books a member is on, with positions | Member profile |

#### Analytics Data Structures

```python
# Return types for analytics methods

# get_book_utilization(db, book_id, period_days=30)
{
    'book_id': 1,
    'book_name': 'Wire Seattle',
    'period_days': 30,
    'total_dispatches': 45,
    'dispatches_per_week': 11.25,
    'avg_days_on_book': 32,
    'current_registered': 150,
    'current_active': 130,
    'turnover_rate': 0.30,  # dispatched / registered
    'fill_rate': 0.85,       # requests filled / total requests
}

# get_classification_summary(db)
[
    {
        'classification': 'inside_wireperson',
        'books': ['Wire Seattle', 'Wire Bremerton', 'Wire Pt Angeles'],
        'total_registered': 1186,
        'total_active': 980,
        'total_dispatched_30d': 120,
        'avg_wait_days': 28,
    },
    ...
]

# get_member_queue_status(db, member_id)
{
    'member_id': 123,
    'member_name': 'John Smith',
    'registrations': [
        {
            'book_name': 'Wire Seattle',
            'book_tier': 1,
            'position': 45,
            'total_on_book': 150,
            'registration_number': Decimal('45123.55'),
            'registered_date': datetime,
            'days_on_book': 21,
            'check_marks': 0,
            're_sign_due': datetime,
            'status': 'ACTIVE',
        },
        ...
    ]
}
```

#### Integration Tests — Full Dispatch Lifecycle

These end-to-end tests verify the complete workflow across multiple services:

| Integration Test | Services Involved | Asserts |
|-----------------|-------------------|---------|
| Register → Re-sign → Dispatch → Terminate (RIF) | BookRegistration, Queue, Dispatch | Full lifecycle completes, member removed from queue |
| Register → Miss re-sign → Auto-rolloff | BookRegistration, Enforcement | Member rolled off at 30 days |
| Register → 3 check marks → Auto-rolloff | BookRegistration, LaborRequest, Dispatch | Rolled off after 3rd check mark |
| Register → Dispatch (short call ≤3 days) → Restore | BookRegistration, Dispatch, Queue | Position restored, doesn't count toward limit |
| Register → Dispatch (short call 5 days) → Restore → Dispatch (short call) → Restore → Dispatch (short call) → FAIL | Dispatch, Queue | Third short call blocked (max 2 per cycle for >3 days) |
| Register → Quit → Rolled off ALL books + Blackout | BookRegistration, Dispatch, Queue | All 3 Wire books cleared, blackout created |
| Bid placed → Accepted → Dispatched | JobBid, Dispatch, Queue | Full bidding workflow |
| Bid placed → Rejected → Second rejection → Suspended | JobBid, Enforcement | 1-year suspension applied |
| Exempt member → Enforcement runs → NOT rolled off | BookRegistration, Enforcement | Exempt status protects from re-sign and check marks |
| Morning referral → Book 1 before Book 2 | LaborRequest, Queue, Dispatch | Correct dispatch ordering |

**Test target for 24C:** +15–20 tests (including 10 integration tests)

---

## Architecture Reminders

- **Member ≠ Student.** Phase 7 FKs to `members`, NOT `students`.
- **APN is DECIMAL(10,2).** Queue ordering is ALWAYS by `registration_number`. Position numbers are **derived** via `ROW_NUMBER()`, not stored.
- **Services raise domain exceptions.** Routers handle HTTP. EnforcementService returns result dicts, not HTTP responses.
- **Dual audit pattern.** RegistrationActivity + audit_logs for every state change.
- **FastAPI BackgroundTasks** for enforcement jobs (ADR-006). Future upgrade path to Celery + Redis when scheduling is needed.

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

## Week 24 Completion Criteria

- [ ] `src/services/queue_service.py` created with queue snapshot, next eligible, analytics
- [ ] `src/services/enforcement_service.py` created with daily enforcement run
- [ ] Re-sign deadline enforcement tested (30-day rolloff, 7-day reminders)
- [ ] Expired request/exemption/blackout/suspension cleanup tested
- [ ] Dry-run enforcement report works correctly
- [ ] Queue analytics: utilization, dispatch rate, wait time, classification summary
- [ ] 10+ integration tests covering full dispatch lifecycle
- [ ] All tests pass
- [ ] ~590–620 total tests (was ~540–560, target +50–60)

---

## What Comes After

| Week | Focus | Status |
|------|-------|--------|
| 20–22 | Models, Enums, Schemas, Registration Services | ✅ Complete |
| 23 | Dispatch Services (LaborRequest, JobBid, Dispatch) | ✅ Complete |
| **24** | **Queue Management (QueueService, enforcement, analytics)** | **← YOU ARE HERE** |
| 25 | API Endpoints (Routers for all Phase 7 services) | 🔜 Next |
| 26 | Frontend — Books & Registration UI | 🔜 Pending |
| 27 | Frontend — Dispatch Workflow UI | 🔜 Pending |
| 28+ | Reports Navigation, Dashboard, Report Sprints | 🔜 Pending |

---

## Related Documents

| Document | Location |
|----------|----------|
| Week 23 Instructions | `docs/instructions/WEEK_23_INSTRUCTIONS.md` |
| Phase 7 Continuity Doc | `docs/phase7/PHASE7_CONTINUITY_DOC.md` |
| ADR-015 (Referral Architecture) | `docs/decisions/ADR-015-referral-dispatch-architecture.md` |
| ADR-006 (Background Jobs) | `docs/decisions/ADR-006-background-jobs.md` |
| ADR-012 (Audit Logging) | `docs/decisions/ADR-012-audit-logging.md` |
| Backend Roadmap v3.1 | `docs/IP2A_BACKEND_ROADMAP.md` |

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
- ❌ Services raising HTTP exceptions → ✅ Services raise **domain exceptions**. Routers handle HTTP.
- ❌ 14 ADRs → ✅ **15 ADRs** (ADR-015 added February 4, 2026)
- ❌ Queue position as stored field → ✅ **Derived** from APN via `ROW_NUMBER()`. NEVER store position.

---

*Week 24 Instructions — Phase 7: Queue Management & Enforcement*
*Created: February 4, 2026*
*Project Version: v0.9.5-alpha*
