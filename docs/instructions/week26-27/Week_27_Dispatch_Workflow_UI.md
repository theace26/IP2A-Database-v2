# Phase 7 Week 27: Dispatch Workflow UI

**Document Type:** Claude Code Instruction Document
**Created:** February 3, 2026
**Spoke:** Spoke 2 (Operations)
**Estimated Time:** 8-12 hours ⚠️ (may require split into 27A/27B — see note below)
**Prerequisites:** Week 26 complete (Books & Registration UI), Phase 7 backend complete
**Version Target:** v0.9.8-alpha

---

## ⚠️ Scope Warning: This May Be a Two-Session Week

The dispatch workflow is the most complex UI in UnionCore. It involves:
- 3 backend routers (~38 endpoints combined)
- 5 backend services
- 8 business rules that must be surfaced in the UI
- Time-sensitive operations (bidding windows, morning referral, cutoff times)
- Multi-step workflows (request → match → bid → dispatch)

**If this exceeds 8 hours, stop at a clean boundary and split into:**
- **Week 27A:** Labor Requests + Dispatch Dashboard (Tasks 0-8)
- **Week 27B:** Bid Management + Queue + Enforcement (Tasks 9-14)

Do not rush this. The dispatch screen is what the dispatchers will use every single day. Getting it wrong means rework later. Getting it right means adoption.

---

## Objective

Build the staff-facing UI for the daily dispatch workflow. This is the "operational" side of the referral system — receiving labor requests from contractors, matching members from the books, processing bids, and dispatching members to jobs.

**End State:** Dispatchers can view the dispatch dashboard, manage labor requests, see pending bids, process morning referral, manage the dispatch queue, and view enforcement actions — all through the HTMX + DaisyUI frontend.

**Primary Users:** Dispatchers (Staff role), Officers, Admins.

---

## Pre-Flight Checklist

Before starting, verify:

```bash
# 1. Docker is running
docker-compose ps

# 2. All tests pass (including Week 26 additions)
pytest -v --tb=short 2>&1 | tail -5

# 3. Week 26 is complete — referral pages are working
curl -s http://localhost:8000/referral | head -20

# 4. Backend dispatch APIs are accessible
curl -s http://localhost:8000/docs | grep -i "dispatch\|labor_request\|job_bid\|queue\|enforcement"

# 5. Clean branch
git status
git pull origin main

# 6. Record starting test count
pytest --co -q 2>&1 | tail -1
```

---

## Task 0: Discovery — Read the Dispatch Backend

**Time:** 45 minutes

Same discipline as Week 26. Read before you write.

### 0.1 Read All Three Routers

```bash
cat src/api/labor_request_api.py
cat src/api/job_bid_api.py
cat src/api/dispatch_api.py
```

For each router, document:
- Every endpoint (method, path, params, body, response)
- Required permissions
- Which business rules each endpoint enforces
- Error responses and their HTTP status codes

### 0.2 Read All Five Services

```bash
cat src/services/labor_request_service.py
cat src/services/job_bid_service.py
cat src/services/dispatch_service.py
cat src/services/queue_service.py
cat src/services/enforcement_service.py
```

Pay special attention to:
- How the morning referral processing works (order of operations)
- How the bidding window is enforced (5:30 PM – 7:00 AM)
- How the 3 PM cutoff works
- What happens on quit/discharge (Rule 12)
- How by-name anti-collusion is detected (Rule 13)
- Short call logic and position restoration (Rule 9)
- Suspension triggers and duration (Rule 8: 2 rejections = 1 year)

### 0.3 Read Related Models and Enums

```bash
grep -rl "dispatch\|labor_request\|job_bid\|queue\|enforcement" src/db/models/
grep -rl "dispatch\|labor_request\|job_bid\|queue\|enforcement" src/db/enums/
# Read each file found
```

Note enum values — these become dropdown options, filter choices, and badge states in the UI.

### 0.4 Read Related Schemas

```bash
grep -rl "dispatch\|labor_request\|job_bid\|queue\|enforcement" src/schemas/
# Read each file found
```

### 0.5 Create Discovery Notes

```bash
cat > docs/phase7/week27_api_discovery.md << 'EOF'
# Week 27 API Discovery Notes

## Labor Request Endpoints
| Method | Path | Purpose | Auth Required |
|--------|------|---------|---------------|
...

## Job Bid Endpoints
...

## Dispatch Endpoints
...

## Business Rules Found in Code
| Rule | Implementation Location | UI Implications |
|------|------------------------|-----------------|
...

## Enum Values (for dropdowns/badges)
...

## Time-Sensitive Operations
| Operation | Window | Enforcement |
|-----------|--------|-------------|
...
EOF
```

---

## Task 1: Create Directory Structure

**Time:** 5 minutes

```bash
# Create dispatch template directories
mkdir -p src/templates/dispatch
mkdir -p src/templates/partials/dispatch
```

**Expected new files by end of week:**

```
src/
├── services/
│   └── dispatch_frontend_service.py    # NEW
├── templates/
│   ├── dispatch/
│   │   ├── dashboard.html              # Dispatch operations dashboard
│   │   ├── requests.html               # Labor request list
│   │   ├── request_detail.html         # Single request detail
│   │   ├── morning_referral.html       # Morning referral processing view
│   │   ├── active.html                 # Active dispatches list
│   │   ├── queue.html                  # Queue management
│   │   └── enforcement.html            # Enforcement dashboard
│   ├── partials/
│   │   └── dispatch/
│   │       ├── _stats_cards.html       # Dashboard stats (HTMX refreshable)
│   │       ├── _request_table.html     # Labor request list table
│   │       ├── _request_card.html      # Single request summary card
│   │       ├── _candidate_list.html    # Candidate members for a request
│   │       ├── _bid_table.html         # Bids for a request
│   │       ├── _dispatch_table.html    # Active/completed dispatches
│   │       ├── _queue_table.html       # Queue positions
│   │       ├── _enforcement_table.html # Violations/suspensions
│   │       ├── _create_request_modal.html  # New labor request form
│   │       ├── _dispatch_modal.html    # Confirm dispatch modal
│   │       └── _fulfill_modal.html     # Fulfill request modal
│   └── components/
│       └── _sidebar.html               # MODIFIED — activate Dispatch links
├── routers/
│   └── frontend.py                     # MODIFIED — add dispatch routes
└── tests/
    └── test_dispatch_frontend.py       # NEW
```

---

## Task 2: Activate Sidebar Dispatch Links

**Time:** 10 minutes

**File:** `src/templates/components/_sidebar.html` (MODIFY)

In Week 26, we added the Dispatch items as muted/disabled. Now activate them:

```html
<!-- Change these from muted to active -->
<li><a href="/dispatch" class="{% if request.url.path == '/dispatch' %}active{% endif %}">Dashboard</a></li>
<li><a href="/dispatch/requests" class="{% if request.url.path.startswith('/dispatch/requests') %}active{% endif %}">Requests</a></li>
```

Add new dispatch sub-items:

```html
<li><a href="/dispatch/morning-referral" class="{% if request.url.path == '/dispatch/morning-referral' %}active{% endif %}">Morning Referral</a></li>
<li><a href="/dispatch/active" class="{% if request.url.path.startswith('/dispatch/active') %}active{% endif %}">Active Dispatches</a></li>
<li><a href="/dispatch/queue" class="{% if request.url.path == '/dispatch/queue' %}active{% endif %}">Queue</a></li>
<li><a href="/dispatch/enforcement" class="{% if request.url.path == '/dispatch/enforcement' %}active{% endif %}">Enforcement</a></li>
```

---

## Task 3: Create Dispatch Frontend Service

**Time:** 1 hour

**File:** `src/services/dispatch_frontend_service.py`

This wraps the five dispatch-related backend services. More complex than the referral frontend service because of the business rules and time-sensitive operations.

```python
"""
Frontend service for Dispatch Workflow UI.

Wraps LaborRequestService, JobBidService, DispatchService,
QueueService, and EnforcementService for Jinja2 template rendering.
"""

from datetime import datetime, time
from sqlalchemy.orm import Session

from src.services.labor_request_service import LaborRequestService
from src.services.job_bid_service import JobBidService
from src.services.dispatch_service import DispatchService
from src.services.queue_service import QueueService
from src.services.enforcement_service import EnforcementService


class DispatchFrontendService:
    """
    Provides template-ready data for dispatch workflow pages.
    
    Handles time-sensitive business rules:
    - Bidding window: 5:30 PM – 7:00 AM
    - 3 PM cutoff for next morning dispatch
    - Morning referral processing order
    """

    BIDDING_WINDOW_START = time(17, 30)  # 5:30 PM
    BIDDING_WINDOW_END = time(7, 0)      # 7:00 AM
    CUTOFF_TIME = time(15, 0)            # 3:00 PM

    def __init__(self, db: Session):
        self.db = db
        self.request_service = LaborRequestService(db)
        self.bid_service = JobBidService(db)
        self.dispatch_service = DispatchService(db)
        self.queue_service = QueueService(db)
        self.enforcement_service = EnforcementService(db)

    # --- Dashboard Methods ---

    def get_dashboard_stats(self) -> dict:
        """
        Get key metrics for the dispatch dashboard.
        Returns dict with: pending_requests, todays_dispatches,
        active_dispatches, queue_size, active_suspensions, etc.
        """
        # TODO: Aggregate from multiple services based on discovery
        pass

    def get_todays_activity(self) -> list:
        """
        Get today's dispatch activity timeline.
        Returns list of events: dispatches, returns, requests received.
        """
        pass

    def is_bidding_window_open(self) -> bool:
        """
        Check if the bidding window is currently open.
        Window: 5:30 PM – 7:00 AM next day.
        """
        now = datetime.now().time()
        return now >= self.BIDDING_WINDOW_START or now < self.BIDDING_WINDOW_END

    def is_past_cutoff(self) -> bool:
        """
        Check if we're past the 3 PM cutoff for next morning dispatch.
        """
        return datetime.now().time() >= self.CUTOFF_TIME

    def get_time_context(self) -> dict:
        """
        Get current time context for UI display.
        Returns: bidding_open, past_cutoff, current_time, next_event.
        """
        return {
            "bidding_open": self.is_bidding_window_open(),
            "past_cutoff": self.is_past_cutoff(),
            "current_time": datetime.now(),
            "next_event": self._get_next_event(),
        }

    # --- Labor Request Methods ---

    def get_requests(self, filters: dict = None, page: int = 1, per_page: int = 25) -> dict:
        """
        Get paginated labor requests with optional filters.
        Filters: status, employer, date_range, agreement_type, urgency.
        """
        pass

    def get_request_detail(self, request_id: int) -> dict:
        """
        Get single labor request with employer info, candidates, and bids.
        Includes matching candidates from relevant books based on 
        agreement type filtering (Rule 4) and check mark requirements (Rule 11).
        """
        pass

    def create_request(self, data: dict) -> dict:
        """
        Create a new labor request. Returns success/error.
        """
        pass

    def fulfill_request(self, request_id: int, data: dict) -> dict:
        """
        Fulfill (partially or fully) a labor request with dispatches.
        """
        pass

    def cancel_request(self, request_id: int, reason: str) -> dict:
        """
        Cancel a labor request.
        """
        pass

    # --- Bid Methods ---

    def get_pending_bids(self) -> list:
        """
        Get all pending bids for morning referral processing.
        Ordered by book position (Rule 2: morning referral order).
        """
        pass

    def get_bids_for_request(self, request_id: int) -> list:
        """
        Get all bids for a specific labor request.
        """
        pass

    def process_morning_referral(self) -> dict:
        """
        Process overnight bids for morning referral.
        Returns results: dispatched, rejected, remaining.
        """
        pass

    # --- Dispatch Methods ---

    def get_active_dispatches(self, filters: dict = None) -> list:
        """
        Get active dispatches with optional filters.
        """
        pass

    def get_dispatch_detail(self, dispatch_id: int) -> dict:
        """
        Get single dispatch detail with member, employer, and history.
        """
        pass

    def complete_dispatch(self, dispatch_id: int, data: dict) -> dict:
        """
        Mark a dispatch as complete.
        Handles short call logic (Rule 9: ≤10 days → position restoration).
        """
        pass

    # --- Queue Methods ---

    def get_queue(self, book_id: int = None) -> list:
        """
        Get current queue positions. Optionally filter by book.
        """
        pass

    # --- Enforcement Methods ---

    def get_enforcement_summary(self) -> dict:
        """
        Get enforcement dashboard data.
        Returns: active_suspensions, recent_violations, blackout_members.
        """
        pass

    def get_suspensions(self, status: str = "active") -> list:
        """
        Get suspension records.
        """
        pass

    def get_violations(self, filters: dict = None) -> list:
        """
        Get violation records.
        """
        pass

    # --- Badge & Formatting Helpers ---

    @staticmethod
    def request_status_badge(status: str) -> dict:
        """DaisyUI badge for request status."""
        badges = {
            "pending": {"class": "badge-warning", "label": "Pending"},
            "open": {"class": "badge-info", "label": "Open"},
            "partially_filled": {"class": "badge-accent", "label": "Partial"},
            "filled": {"class": "badge-success", "label": "Filled"},
            "cancelled": {"class": "badge-error", "label": "Cancelled"},
            "expired": {"class": "badge-ghost", "label": "Expired"},
        }
        return badges.get(status, {"class": "badge-ghost", "label": status})

    @staticmethod
    def dispatch_status_badge(status: str) -> dict:
        """DaisyUI badge for dispatch status."""
        badges = {
            "active": {"class": "badge-success", "label": "Active"},
            "completed": {"class": "badge-info", "label": "Completed"},
            "short_call": {"class": "badge-warning", "label": "Short Call"},
            "quit": {"class": "badge-error", "label": "Quit"},
            "discharged": {"class": "badge-error", "label": "Discharged"},
            "returned": {"class": "badge-accent", "label": "Returned"},
        }
        return badges.get(status, {"class": "badge-ghost", "label": status})

    @staticmethod
    def urgency_badge(urgency: str) -> dict:
        """DaisyUI badge for request urgency."""
        badges = {
            "normal": {"class": "badge-ghost", "label": "Normal"},
            "urgent": {"class": "badge-warning", "label": "Urgent"},
            "emergency": {"class": "badge-error", "label": "Emergency"},
        }
        return badges.get(urgency, {"class": "badge-ghost", "label": urgency})

    @staticmethod
    def bidding_window_badge(is_open: bool) -> dict:
        """DaisyUI badge for bidding window status."""
        if is_open:
            return {"class": "badge-success", "label": "Bidding Open"}
        return {"class": "badge-ghost", "label": "Bidding Closed"}

    # --- Private Helpers ---

    def _get_next_event(self) -> dict:
        """Calculate next time-sensitive event (cutoff or window open/close)."""
        now = datetime.now().time()
        if now < self.CUTOFF_TIME:
            return {"event": "3 PM Cutoff", "time": "3:00 PM"}
        elif now < self.BIDDING_WINDOW_START:
            return {"event": "Bidding Opens", "time": "5:30 PM"}
        else:
            return {"event": "Morning Referral", "time": "7:00 AM"}
```

**CRITICAL:** Fill in the actual service method calls based on your Task 0 discovery. The stub methods above show the intent — your implementation must call the real backend services with the correct parameters.

---

## Task 4: Create Dispatch Dashboard

**Time:** 1 hour

**File:** `src/templates/dispatch/dashboard.html`

This is the primary screen dispatchers see every day. It must be immediately useful.

**Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│ Dispatch Dashboard                     🟢 Bidding Open      │
│ Tuesday, Feb 3, 2026 — Next: 3 PM Cutoff in 2h 15m        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │
│  │ Pending   │ │ Today's   │ │ Active    │ │ Suspensions│   │
│  │ Requests  │ │ Dispatched│ │ On Job    │ │ Active     │   │
│  │    3      │ │    12     │ │    156    │ │    2       │   │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘   │
│                                                               │
│  ┌────────────────────────────┐ ┌────────────────────────┐   │
│  │ Pending Requests           │ │ Today's Activity       │   │
│  │ ┌────────────────────────┐ │ │ 7:05 AM — Smith, J     │   │
│  │ │ ABC Electric           │ │ │   dispatched to ABC    │   │
│  │ │ 3 JW, 2 Apprentice    │ │ │ 7:12 AM — Jones, M     │   │
│  │ │ Start: Tomorrow 6AM   │ │ │   dispatched to XYZ    │   │
│  │ │ [View] [Quick Fill]   │ │ │ 8:30 AM — New request  │   │
│  │ └────────────────────────┘ │ │   from DEF Corp (2 JW) │   │
│  │ ┌────────────────────────┐ │ │ 9:15 AM — Brown, A     │   │
│  │ │ XYZ Construction      │ │ │   returned (completed)  │   │
│  │ │ 1 S&C Journeyman      │ │ │                        │   │
│  │ │ Start: Today ASAP     │ │ │                        │   │
│  │ │ [View] [Quick Fill]   │ │ │                        │   │
│  │ └────────────────────────┘ │ │                        │   │
│  └────────────────────────────┘ └────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ ⚠️ Alerts                                            │   │
│  │ • 2 members approaching 2-rejection threshold        │   │
│  │ • 1 by-name request flagged for review (Rule 13)    │   │
│  │ • 3 PM cutoff in 2h 15m — 3 unfilled requests       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Key features:**

1. **Time Context Bar** — Always visible. Shows current time, bidding window status (badge), next event countdown. Use Alpine.js for the countdown timer:

```html
<div class="flex items-center gap-4 bg-base-100 rounded-lg px-4 py-2 shadow-sm mb-4"
     x-data="{ 
         now: new Date(),
         init() { setInterval(() => this.now = new Date(), 60000) }
     }">
    <span class="font-mono" x-text="now.toLocaleTimeString()"></span>
    <div class="badge {{ time_context.bidding_badge.class }}">
        {{ time_context.bidding_badge.label }}
    </div>
    <span class="text-sm text-base-content/60">
        Next: {{ time_context.next_event.event }} at {{ time_context.next_event.time }}
    </span>
</div>
```

2. **Stats Cards** — HTMX auto-refresh every 60 seconds. Use the same pattern as the referral landing page.

3. **Pending Requests Panel** — Shows unfilled labor requests ordered by urgency then date. Each request card shows: employer name, workers needed (count + type), start date, urgency badge, quick action buttons.

4. **Today's Activity Feed** — Chronological timeline of today's dispatch events. Auto-refreshes via HTMX polling:
```html
<div id="activity-feed"
     hx-get="/dispatch/partials/activity-feed"
     hx-trigger="load, every 30s"
     hx-swap="innerHTML">
</div>
```

5. **Alerts Panel** — Business rule alerts that need dispatcher attention. Loaded via HTMX partial.

---

## Task 5: Create Labor Request List Page

**Time:** 45 minutes

**File:** `src/templates/dispatch/requests.html`

All labor requests with rich filtering.

**Filters:**
- Status: Pending, Open, Partially Filled, Filled, Cancelled
- Agreement Type: Standard, PLA, CWA, TERO (Rule 4)
- Urgency: Normal, Urgent, Emergency
- Date range: Request date, Start date
- Employer: Search by name
- Region: Seattle, Bremerton, Port Angeles

**Table columns:**
- ID / Reference #
- Employer name
- Workers needed (count + classification)
- Agreement type (badge)
- Start date
- Urgency (badge)
- Status (badge)
- Filled / Needed ratio
- Actions: View, Fulfill, Cancel

HTMX-powered filtering — same pattern as the books list page from Week 26.

---

## Task 6: Create Labor Request Detail Page

**Time:** 1 hour

**File:** `src/templates/dispatch/request_detail.html`

The most important detail page in the dispatch system. Shows a single request with everything needed to fill it.

**Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│ ← Back to Requests   Request #1234         [Fill] [Cancel]  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Request Info                                             ││
│  │ Employer: ABC Electric          Agreement: PLA          ││
│  │ Needed: 3 Inside Wireman JW     Start: Feb 5, 6:00 AM  ││
│  │ Filled: 1/3                     Urgency: Normal         ││
│  │ Site: 123 Main St, Seattle      Region: Seattle          ││
│  │ Notes: Overtime expected, bring own hand tools           ││
│  └─────────────────────────────────────────────────────────┘│
│                                                               │
│  ┌─────────────────────────┐  ┌─────────────────────────┐   │
│  │ Matching Candidates     │  │ Bids Received           │   │
│  │ (from Book 1, ordered)  │  │                         │   │
│  │ 1. Smith, J — Pos #3    │  │ Jones, M — 6:15 PM     │   │
│  │ 2. Brown, A — Pos #7    │  │ Williams, R — 8:30 PM  │   │
│  │ 3. Davis, K — Pos #12   │  │                         │   │
│  │ 4. Wilson, T — Pos #15  │  │                         │   │
│  │ [Load More]             │  │                         │   │
│  │                         │  │                         │   │
│  │ ⚠️ Check marks:         │  │                         │   │
│  │ Davis has MOU flag      │  │                         │   │
│  └─────────────────────────┘  └─────────────────────────┘   │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Dispatch History for This Request                        ││
│  │ Feb 3 07:05 — Smith, J dispatched (accepted)            ││
│  │ Feb 3 07:02 — Adams, P called (no answer, skipped)      ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**Key interactions:**

1. **Candidate List** — Shows members from the relevant book in position order. Filtered by agreement type (Rule 4) and check mark requirements (Rule 11). Each candidate has a "Dispatch" button that opens a confirmation modal.

2. **Bid List** — Shows bids received during the bidding window. Each bid shows member name, bid time, and action buttons (Accept, Reject).

3. **Fulfill Action** — Opens modal to dispatch a specific member to this request. Validates against business rules before confirming.

4. **Business Rule Indicators** — Visual indicators for:
   - Check marks (Rule 11) — icon next to members with specialty, MOU, early start flags
   - By-name flag (Rule 13) — warning banner if request has by-name specification
   - Suspension status — members on suspension shown but disabled with reason

---

## Task 7: Create Morning Referral Page

**Time:** 1 hour

**File:** `src/templates/dispatch/morning_referral.html`

Specialized view for processing overnight bids into morning dispatches. This is the most operationally critical page — dispatchers use it every morning.

**Key features:**

1. **Bid Queue** — All overnight bids grouped by labor request, ordered by book position (Rule 2). Show bid time, member position, and eligibility.

2. **Processing Controls** — "Process Next" button that dispatches the top-position bidder for each request. "Process All" button that auto-processes all valid bids.

3. **Rejection Tracking** — When a bid is rejected, increment the member's rejection count. Alert if member hits 2 rejections (Rule 8: 1-year suspension).

4. **Time Guards:**
   - If before 7:00 AM: Show "Bidding still open — processing available at 7:00 AM"
   - If after 7:00 AM and before 3:00 PM: Normal processing mode
   - If after 3:00 PM: Show cutoff warning — remaining unfilled requests won't be in tomorrow's bidding

5. **Status Summary** — After processing: X dispatched, Y rejected, Z remaining unfilled.

```html
{% extends "base.html" %}

{% block title %}Morning Referral{% endblock %}

{% block content %}
<div class="flex justify-between items-center mb-6">
    <div>
        <h1 class="text-2xl font-bold">Morning Referral</h1>
        <p class="text-base-content/60">Process overnight bids for {{ date_display }}</p>
    </div>
    <div class="flex items-center gap-2">
        <div class="badge {{ time_context.bidding_badge.class }} badge-lg">
            {{ time_context.bidding_badge.label }}
        </div>
        {% if not time_context.bidding_open %}
        <button class="btn btn-primary btn-sm"
                hx-post="/dispatch/morning-referral/process-all"
                hx-target="#referral-results"
                hx-confirm="Process all valid bids? This cannot be undone.">
            Process All Bids
        </button>
        {% endif %}
    </div>
</div>

{% if time_context.bidding_open %}
<!-- Bidding Still Open -->
<div class="alert alert-info mb-6">
    <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
    <div>
        <h3 class="font-bold">Bidding Window Open</h3>
        <p>Members can still submit bids. Processing will be available after 7:00 AM.</p>
    </div>
</div>
{% endif %}

{% if time_context.past_cutoff %}
<!-- Past Cutoff Warning -->
<div class="alert alert-warning mb-6">
    <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
    <div>
        <h3 class="font-bold">Past 3 PM Cutoff</h3>
        <p>Requests received after 3 PM will not be included in tomorrow's morning referral.</p>
    </div>
</div>
{% endif %}

<!-- Bid Queue -->
<div id="bid-queue"
     hx-get="/dispatch/partials/bid-queue"
     hx-trigger="load"
     hx-swap="innerHTML">
    <div class="skeleton h-96 w-full"></div>
</div>

<!-- Processing Results -->
<div id="referral-results" class="mt-6"></div>
{% endblock %}
```

---

## Task 8: Create Active Dispatches Page

**Time:** 30 minutes

**File:** `src/templates/dispatch/active.html`

List of all currently active dispatches (members currently on jobs).

**Filters:**
- Status: Active, Completed, Short Call
- Employer
- Classification/Book
- Date range

**Table columns:**
- Member name
- Employer
- Job site
- Classification
- Start date
- Duration (days on job)
- Status (badge)
- Actions: View, Complete, Mark as Short Call

**Short Call handling (Rule 9):**
- If dispatch ≤10 days: Button to "Mark Short Call" which triggers position restoration
- Show "Short Call" badge with day count

---

## Task 9: Create Queue Management Page

**Time:** 45 minutes

**File:** `src/templates/dispatch/queue.html`

Shows the current out-of-work queue — members ordered by their position on each book.

**Key features:**
- Book selector (tabs or dropdown to switch between books)
- Position list showing: position number, member name, registration date, check marks, status
- Visual indicators: members on dispatch (grayed out), members on suspension (red), members with check marks (icon)
- Search within queue

**This page is essentially a read-only view of what's on each book.** The Book Detail page from Week 26 shows similar data but with management actions. This queue page is the "dispatcher's reference" — quick lookup of who's next in line.

```html
<!-- Book tabs -->
<div class="tabs tabs-boxed mb-4" x-data="{ activeBook: '{{ default_book_id }}' }">
    {% for book in books %}
    <a class="tab" 
       :class="{ 'tab-active': activeBook === '{{ book.id }}' }"
       @click="activeBook = '{{ book.id }}'"
       hx-get="/dispatch/partials/queue-table?book_id={{ book.id }}"
       hx-target="#queue-table-container"
       hx-swap="innerHTML">
        {{ book.short_name }}
        <span class="badge badge-sm ml-1">{{ book.queue_count }}</span>
    </a>
    {% endfor %}
</div>

<div id="queue-table-container">
    {% include 'partials/dispatch/_queue_table.html' %}
</div>
```

---

## Task 10: Create Enforcement Dashboard

**Time:** 45 minutes

**File:** `src/templates/dispatch/enforcement.html`

Shows active enforcement actions: suspensions, blackouts, and violation history.

**Sections:**

1. **Active Suspensions** — Members currently suspended from dispatch.
   - Member name, reason, start date, end date, days remaining
   - Rule reference (e.g., "Rule 8: 2 rejections" or "Rule 12: Quit/discharge")

2. **Active Blackouts** — Members in 2-week blackout period (Rule 12).
   - Member name, trigger event (quit/discharged), blackout start, blackout end

3. **Violation History** — Searchable log of all enforcement actions.
   - Date, member, violation type, action taken, resolved status

4. **By-Name Flagged Requests** — Requests flagged by anti-collusion enforcement (Rule 13).
   - Request details, flag reason, review status

**Key business rules to surface:**

| Rule | UI Element | Visibility |
|------|-----------|------------|
| Rule 8 | Suspension count + 1-year duration | Active Suspensions table |
| Rule 12 | Quit/discharge + 2-week blackout | Active Blackouts section |
| Rule 13 | By-name request flagging | Flagged Requests section |

---

## Task 11: Create HTMX Partials

**Time:** 1.5 hours

Create partials in `src/templates/partials/dispatch/`:

### 11.1 `_stats_cards.html`
Dashboard stats cards. 4 cards with key metrics. Refreshable.

### 11.2 `_request_table.html`
Labor request list table. Columns: employer, workers needed, agreement type, start date, urgency, status, actions. Supports HTMX swap for filtering.

### 11.3 `_request_card.html`
Compact request card for the dashboard's pending requests panel. Shows employer, count, start date, urgency badge, quick action links.

### 11.4 `_candidate_list.html`
Matching candidates for a labor request. Shows members from relevant book in position order with check marks and status indicators. Each row has a "Dispatch" button.

### 11.5 `_bid_table.html`
Bids for a specific request. Shows member, bid time, position on book, eligibility status, action buttons (Accept/Reject).

### 11.6 `_dispatch_table.html`
Active/completed dispatches table. Reused across dashboard and active dispatches page.

### 11.7 `_queue_table.html`
Queue positions for a specific book. HTMX swap target for book tab switching.

### 11.8 `_enforcement_table.html`
Enforcement actions table. Filterable by type (suspension, blackout, violation).

### 11.9 `_create_request_modal.html`
Form for creating a new labor request.

**Fields:**
- Employer (search/select)
- Workers needed (count)
- Classification (book type)
- Agreement type (Standard/PLA/CWA/TERO)
- Start date + time
- Job site address
- Urgency
- Special requirements (check marks, by-name)
- Notes

### 11.10 `_dispatch_modal.html`
Confirmation modal for dispatching a member. Shows:
- Member name and current position
- Request details (employer, job, start date)
- Business rule checks (any flags)
- Confirm/Cancel buttons

### 11.11 `_fulfill_modal.html`
Modal for fulfilling a request by selecting members from the candidate list.

---

## Task 12: Add Frontend Routes

**Time:** 45 minutes

**File:** `src/routers/frontend.py` (MODIFY)

Add dispatch routes following the same pattern as referral routes from Week 26.

```python
# --- Dispatch Routes ---

@router.get("/dispatch")
async def dispatch_dashboard(request: Request, db: Session = Depends(get_db)):
    """Dispatch operations dashboard."""
    service = DispatchFrontendService(db)
    context = {
        "request": request,
        "current_user": get_current_user_from_cookie(request, db),
        "stats": service.get_dashboard_stats(),
        "time_context": service.get_time_context(),
        "pending_requests": service.get_requests(filters={"status": "pending"}),
    }
    return templates.TemplateResponse("dispatch/dashboard.html", context)


@router.get("/dispatch/requests")
async def dispatch_requests(
    request: Request,
    db: Session = Depends(get_db),
    status: str = None,
    agreement_type: str = None,
    urgency: str = None,
    search: str = None,
    page: int = 1,
):
    """Labor request list with filtering."""
    service = DispatchFrontendService(db)
    filters = {
        "status": status,
        "agreement_type": agreement_type,
        "urgency": urgency,
        "search": search,
    }
    requests_data = service.get_requests(filters=filters, page=page)
    context = {
        "request": request,
        "current_user": get_current_user_from_cookie(request, db),
        "labor_requests": requests_data,
        "filters": filters,
    }
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("partials/dispatch/_request_table.html", context)
    return templates.TemplateResponse("dispatch/requests.html", context)


@router.get("/dispatch/requests/{request_id}")
async def dispatch_request_detail(request_id: int, request: Request, db: Session = Depends(get_db)):
    """Single labor request detail with candidates and bids."""
    service = DispatchFrontendService(db)
    labor_request = service.get_request_detail(request_id)
    if not labor_request:
        raise HTTPException(status_code=404)
    context = {
        "request": request,
        "current_user": get_current_user_from_cookie(request, db),
        "labor_request": labor_request,
        "time_context": service.get_time_context(),
    }
    return templates.TemplateResponse("dispatch/request_detail.html", context)


@router.get("/dispatch/morning-referral")
async def morning_referral(request: Request, db: Session = Depends(get_db)):
    """Morning referral processing page."""
    service = DispatchFrontendService(db)
    context = {
        "request": request,
        "current_user": get_current_user_from_cookie(request, db),
        "time_context": service.get_time_context(),
        "pending_bids": service.get_pending_bids(),
    }
    return templates.TemplateResponse("dispatch/morning_referral.html", context)


@router.get("/dispatch/active")
async def active_dispatches(
    request: Request,
    db: Session = Depends(get_db),
    status: str = None,
    search: str = None,
):
    """Active dispatches list."""
    service = DispatchFrontendService(db)
    dispatches = service.get_active_dispatches(filters={"status": status, "search": search})
    context = {
        "request": request,
        "current_user": get_current_user_from_cookie(request, db),
        "dispatches": dispatches,
    }
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("partials/dispatch/_dispatch_table.html", context)
    return templates.TemplateResponse("dispatch/active.html", context)


@router.get("/dispatch/queue")
async def dispatch_queue(
    request: Request,
    db: Session = Depends(get_db),
    book_id: int = None,
):
    """Queue management page."""
    service = DispatchFrontendService(db)
    ref_service = ReferralFrontendService(db)
    context = {
        "request": request,
        "current_user": get_current_user_from_cookie(request, db),
        "books": ref_service.get_books_overview(),
        "queue": service.get_queue(book_id=book_id),
        "default_book_id": book_id,
    }
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("partials/dispatch/_queue_table.html", context)
    return templates.TemplateResponse("dispatch/queue.html", context)


@router.get("/dispatch/enforcement")
async def enforcement_dashboard(request: Request, db: Session = Depends(get_db)):
    """Enforcement dashboard."""
    service = DispatchFrontendService(db)
    context = {
        "request": request,
        "current_user": get_current_user_from_cookie(request, db),
        "enforcement": service.get_enforcement_summary(),
        "suspensions": service.get_suspensions(),
    }
    return templates.TemplateResponse("dispatch/enforcement.html", context)


# --- HTMX Partials ---

@router.get("/dispatch/partials/stats")
async def dispatch_stats_partial(request: Request, db: Session = Depends(get_db)):
    """HTMX partial: dashboard stats."""
    service = DispatchFrontendService(db)
    context = {"request": request, "stats": service.get_dashboard_stats()}
    return templates.TemplateResponse("partials/dispatch/_stats_cards.html", context)


@router.get("/dispatch/partials/activity-feed")
async def dispatch_activity_partial(request: Request, db: Session = Depends(get_db)):
    """HTMX partial: today's activity feed. Auto-refreshes every 30s."""
    service = DispatchFrontendService(db)
    context = {"request": request, "activity": service.get_todays_activity()}
    return templates.TemplateResponse("partials/dispatch/_activity_feed.html", context)


@router.get("/dispatch/partials/bid-queue")
async def bid_queue_partial(request: Request, db: Session = Depends(get_db)):
    """HTMX partial: morning referral bid queue."""
    service = DispatchFrontendService(db)
    context = {"request": request, "bids": service.get_pending_bids()}
    return templates.TemplateResponse("partials/dispatch/_bid_queue.html", context)


@router.get("/dispatch/partials/queue-table")
async def queue_table_partial(request: Request, db: Session = Depends(get_db), book_id: int = None):
    """HTMX partial: queue table for specific book."""
    service = DispatchFrontendService(db)
    context = {"request": request, "queue": service.get_queue(book_id=book_id)}
    return templates.TemplateResponse("partials/dispatch/_queue_table.html", context)


# --- POST Routes ---

@router.post("/dispatch/requests")
async def create_labor_request(request: Request, db: Session = Depends(get_db)):
    """Create a new labor request."""
    form = await request.form()
    service = DispatchFrontendService(db)
    result = service.create_request(dict(form))
    # Handle success/error response
    pass


@router.post("/dispatch/requests/{request_id}/fulfill")
async def fulfill_labor_request(request_id: int, request: Request, db: Session = Depends(get_db)):
    """Fulfill a labor request with selected members."""
    form = await request.form()
    service = DispatchFrontendService(db)
    result = service.fulfill_request(request_id, dict(form))
    pass


@router.post("/dispatch/requests/{request_id}/cancel")
async def cancel_labor_request(request_id: int, request: Request, db: Session = Depends(get_db)):
    """Cancel a labor request."""
    form = await request.form()
    service = DispatchFrontendService(db)
    result = service.cancel_request(request_id, form.get("reason", ""))
    pass


@router.post("/dispatch/morning-referral/process-all")
async def process_morning_referral(request: Request, db: Session = Depends(get_db)):
    """Process all valid bids for morning referral."""
    service = DispatchFrontendService(db)
    result = service.process_morning_referral()
    context = {"request": request, "result": result}
    return templates.TemplateResponse("partials/dispatch/_referral_results.html", context)


@router.post("/dispatch/{dispatch_id}/complete")
async def complete_dispatch(dispatch_id: int, request: Request, db: Session = Depends(get_db)):
    """Mark a dispatch as complete."""
    form = await request.form()
    service = DispatchFrontendService(db)
    result = service.complete_dispatch(dispatch_id, dict(form))
    pass
```

**IMPORTANT:** Same as Week 26 — these route patterns are templates based on expected API structure. Adjust all service calls based on your Task 0 discovery. The backend may use different parameter names, return different structures, or require different authentication patterns.

---

## Task 13: Write Frontend Tests

**Time:** 1.5 hours

**File:** `src/tests/test_dispatch_frontend.py`

Comprehensive tests for the dispatch UI.

```python
class TestDispatchFrontend:
    """Tests for dispatch frontend routes and HTMX interactions."""

    # --- Page Rendering ---
    def test_dashboard_renders(self): ...
    def test_dashboard_requires_auth(self): ...
    def test_requests_list_renders(self): ...
    def test_request_detail_renders(self): ...
    def test_request_detail_404(self): ...
    def test_morning_referral_renders(self): ...
    def test_active_dispatches_renders(self): ...
    def test_queue_renders(self): ...
    def test_enforcement_renders(self): ...

    # --- HTMX Partials ---
    def test_stats_partial_returns_html(self): ...
    def test_activity_feed_partial(self): ...
    def test_request_table_filter(self): ...
    def test_queue_table_book_filter(self): ...
    def test_bid_queue_partial(self): ...

    # --- Time Context ---
    def test_time_context_includes_bidding_status(self): ...
    def test_time_context_includes_cutoff_status(self): ...

    # --- Form Submissions ---
    def test_create_labor_request(self): ...
    def test_fulfill_request(self): ...
    def test_cancel_request(self): ...
    def test_process_morning_referral(self): ...
    def test_complete_dispatch(self): ...

    # --- Role-Based Access ---
    def test_staff_can_view_dashboard(self): ...
    def test_member_cannot_view_dashboard(self): ...
    def test_admin_sees_all_enforcement(self): ...

    # --- Business Rule UI ---
    def test_bidding_window_indicator_shown(self): ...
    def test_cutoff_warning_after_3pm(self): ...
    def test_suspended_members_disabled_in_candidates(self): ...

    # --- Sidebar ---
    def test_sidebar_dispatch_links_active(self): ...
```

**Target: 25-30 new tests**

---

## Task 14: Commit and Document

**Time:** 15 minutes

### 14.1 Run Full Test Suite

```bash
pytest -v --tb=short
```

### 14.2 Git Commit

```bash
git add -A
git commit -m "feat(frontend): Phase 7 Week 27 - Dispatch Workflow UI

- Add DispatchFrontendService with time-aware business logic
- Add dispatch dashboard with live stats and activity feed
- Add labor request list with rich filtering
- Add labor request detail with candidates and bid management
- Add morning referral processing page with time guards
- Add active dispatches page with short call handling
- Add queue management page with book tabs
- Add enforcement dashboard (suspensions, blackouts, violations)
- Add HTMX partials for dynamic dispatch operations
- Add create/fulfill/cancel request workflows
- Activate dispatch sidebar navigation links
- Add XX new frontend tests (YYY total)

Business rules surfaced: Rules 2,3,4,8,9,11,12,13
Consumes: labor_request_api, job_bid_api, dispatch_api (Phase 7 Weeks 23-25)
Stack: Jinja2 + HTMX + DaisyUI + Alpine.js"
```

### 14.3 Update CHANGELOG.md

```markdown
### Added
- **Phase 7 Week 27: Dispatch Workflow UI**
  * DispatchFrontendService with time-aware operations
  * Dispatch dashboard with live stats and activity feed
  * Labor request management (list, detail, create, fulfill, cancel)
  * Morning referral processing with bid queue
  * Active dispatches with short call tracking
  * Queue management with book tabs
  * Enforcement dashboard (suspensions, blackouts, violations)
  * Time context: bidding window indicator, 3 PM cutoff warning
  * Business rules 2,3,4,8,9,11,12,13 surfaced in UI
  * XX new frontend tests
```

---

## Summary: Week 27 Deliverables

| Item | Status |
|------|--------|
| Task 0: API Discovery | ⬜ |
| Task 1: Directory structure | ⬜ |
| Task 2: Activate sidebar dispatch links | ⬜ |
| Task 3: DispatchFrontendService | ⬜ |
| Task 4: Dispatch dashboard | ⬜ |
| Task 5: Labor request list | ⬜ |
| Task 6: Labor request detail | ⬜ |
| Task 7: Morning referral page | ⬜ |
| Task 8: Active dispatches page | ⬜ |
| Task 9: Queue management page | ⬜ |
| Task 10: Enforcement dashboard | ⬜ |
| Task 11: HTMX partials (11 files) | ⬜ |
| Task 12: Frontend routes | ⬜ |
| Task 13: Frontend tests (25-30) | ⬜ |
| Task 14: Commit + CHANGELOG | ⬜ |

**Estimated Total Time:** 8-12 hours

**If splitting:**
- **Week 27A (Tasks 0-8):** ~5-7 hours — Dashboard + Requests + Morning Referral + Active Dispatches
- **Week 27B (Tasks 9-14):** ~4-5 hours — Queue + Enforcement + Remaining Partials + Tests

---

## Business Rules Quick Reference

Keep this handy during development. Each rule should be visually represented in the UI.

| Rule | Name | UI Location | Visual Indicator |
|------|------|-------------|-----------------|
| 2 | Morning referral order | Morning Referral page | Bid queue sorted by position |
| 3 | 3 PM cutoff | Dashboard + Morning Referral | Warning banner after 3 PM |
| 4 | Agreement type filtering | Request Detail → Candidates | Candidates filtered, type badge |
| 8 | Bidding window + suspension | Dashboard + Request Detail | Window status badge, rejection counter |
| 9 | Short call ≤10 days | Active Dispatches | "Short Call" badge, day counter |
| 11 | Check mark determination | Request Detail → Candidates | Check mark icons next to members |
| 12 | Quit/discharge rolloff | Enforcement | Blackout section, rolloff indicator |
| 13 | By-name anti-collusion | Request Detail | Warning banner on flagged requests |

---

## Week 28 Preview

Week 28: Reports Navigation & Dashboard
- Report listing page (78 reports, P0-P3)
- Report generation UI
- PDF/Excel export
- Report scheduling
- Dashboard integration with key metrics

---

*Week 27 Instruction Document — Spoke 2 (Operations)*
*Created: February 3, 2026*
*UnionCore (IP2A-Database-v2)*
