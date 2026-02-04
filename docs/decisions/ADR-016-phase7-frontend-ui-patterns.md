# ADR-016: Phase 7 Referral & Dispatch Frontend UI Patterns

**Status:** Accepted
**Date:** February 4, 2026
**Decision Makers:** Xerxes (Product Owner), Claude Code (Implementation)
**Related:** ADR-002 (Frontend Framework), ADR-010 (Operations Frontend Patterns), ADR-015 (Referral Dispatch Architecture)

---

## Context

Phase 7 (Referral & Dispatch System) required building complex staff-facing UI for managing IBEW Local 46's out-of-work referral books and daily dispatch operations. This UI surfaces 14 business rules from union procedures and handles time-sensitive workflows (bidding windows, morning referral processing, 3 PM cutoffs).

**Key Challenges:**
1. **Time-Aware UI** - Bidding window (5:30 PM - 7:00 AM), 3 PM cutoff warnings
2. **Complex State Management** - Queue positions, registration status, dispatch lifecycle
3. **Business Rule Visibility** - 14 rules must be clearly surfaced in UI
4. **Real-Time Updates** - Dashboard stats, activity feeds, pending requests
5. **Pattern Consistency** - Must follow established frontend patterns from Phase 6

**Prior Art:**
- ADR-002: Established HTMX + Jinja2 + DaisyUI stack
- ADR-010: Defined operations frontend patterns (services, routes, partials)
- Phase 6 Weeks 1-19: Completed frontend foundation with 200+ tests

---

## Decision

We will implement Phase 7 frontend using the **Frontend Service Wrapper Pattern** with **Time-Aware Business Logic** and **HTMX Progressive Enhancement**.

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Routes                      │
│  (referral_frontend.py, dispatch_frontend.py)          │
└──────────────────┬──────────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
┌────────▼────────┐  ┌──────▼──────────┐
│ Referral        │  │ Dispatch        │
│ FrontendService │  │ FrontendService │
│                 │  │                 │
│ - Badge helpers │  │ - Time context  │
│ - Stats queries │  │ - Badge helpers │
│ - Pagination    │  │ - Stats queries │
└────────┬────────┘  └──────┬──────────┘
         │                   │
    ┌────▼───────────────────▼────┐
    │   Backend Services          │
    │ (ReferralBook, Registration,│
    │  LaborRequest, JobBid,      │
    │  Dispatch, Queue,           │
    │  Enforcement)               │
    └─────────────────────────────┘
```

### Key Patterns

#### 1. Frontend Service Wrapper Pattern

**What:** Separate service layer between routes and backend services for template formatting.

**Why:**
- Separates presentation logic from business logic
- Provides consistent badge/status helpers
- Handles pagination, filtering, sorting for templates
- Centralizes API error handling for HTMX responses

**Example:**
```python
# src/services/dispatch_frontend_service.py
class DispatchFrontendService:
    def __init__(self, db: Session):
        self.db = db
        self.dispatch_service = DispatchService(db)
        self.queue_service = QueueService(db)

    def get_dashboard_stats(self) -> dict:
        """Aggregate stats from multiple backend services."""
        return {
            "pending_requests": self.dispatch_service.count_pending(),
            "todays_dispatches": self.dispatch_service.count_today(),
            "active_on_job": self.dispatch_service.count_active(),
            "pending_bids": self.bid_service.count_pending(),
        }

    @staticmethod
    def dispatch_status_badge(status: str) -> dict:
        """DaisyUI badge for dispatch status."""
        badges = {
            "active": {"class": "badge-success", "label": "Active"},
            "completed": {"class": "badge-info", "label": "Completed"},
            "short_call": {"class": "badge-warning", "label": "Short Call"},
        }
        return badges.get(status, {"class": "badge-ghost", "label": status})
```

#### 2. Time-Aware Business Logic

**What:** Frontend service enforces time-based business rules and provides time context.

**Why:**
- Bidding window (5:30 PM - 7:00 AM) must control UI state
- 3 PM cutoff determines request eligibility for next morning
- Morning referral processing order affects UI sorting
- UI must warn users when actions are time-restricted

**Implementation:**
```python
class DispatchFrontendService:
    BIDDING_WINDOW_START = time(17, 30)  # 5:30 PM
    BIDDING_WINDOW_END = time(7, 0)      # 7:00 AM
    CUTOFF_TIME = time(15, 0)            # 3:00 PM

    def is_bidding_window_open(self) -> bool:
        """Check if bidding window is currently open."""
        now = datetime.now().time()
        return now >= self.BIDDING_WINDOW_START or now < self.BIDDING_WINDOW_END

    def get_time_context(self) -> dict:
        """Time context for UI warnings and badges."""
        return {
            "bidding_open": self.is_bidding_window_open(),
            "past_cutoff": datetime.now().time() >= self.CUTOFF_TIME,
            "current_time": datetime.now(),
            "next_event": self._get_next_event(),
        }
```

**Template Usage:**
```html
{% if time_context.bidding_open %}
<div class="badge badge-success">Bidding Open</div>
{% else %}
<div class="badge badge-ghost">Bidding Closed</div>
{% endif %}

{% if time_context.past_cutoff %}
<div class="alert alert-warning">
  Past 3 PM cutoff - new requests won't be in tomorrow's morning referral
</div>
{% endif %}
```

#### 3. HTMX Auto-Refresh for Real-Time Data

**What:** Stats and activity feeds auto-refresh without page reload.

**Why:**
- Dashboard must show live dispatch activity
- Pending requests change frequently
- Queue positions update as members are dispatched
- Reduces manual refresh burden on staff

**Implementation:**
```html
<!-- Auto-refresh every 60 seconds -->
<div id="dashboard-stats"
     hx-get="/dispatch/partials/stats"
     hx-trigger="load, every 60s"
     hx-swap="innerHTML">
  <!-- Stats load here -->
</div>

<!-- Auto-refresh every 30 seconds for activity feed -->
<div id="activity-feed"
     hx-get="/dispatch/partials/activity-feed"
     hx-trigger="load, every 30s"
     hx-swap="innerHTML">
  <!-- Activity timeline loads here -->
</div>
```

#### 4. Business Rule Visibility

**What:** UI explicitly shows which business rules apply to each operation.

**Why:**
- 14 business rules govern dispatch operations
- Staff must understand why certain members are/aren't eligible
- Compliance requires audit trail of rule application
- Training new dispatchers requires clear rule indicators

**Implementation:**
```html
<!-- Rule 9: Short Call indicator -->
{% if dispatch.days_on_job <= 10 %}
<div class="badge badge-warning">
  Short Call ({{ dispatch.days_on_job }} days)
  <span class="text-xs ml-1">Rule 9</span>
</div>
{% endif %}

<!-- Rule 11: Check mark exceptions -->
{% if candidate.has_check_mark_exception %}
<svg class="h-4 w-4 text-info" title="Check mark exception: {{ candidate.exception_reason }}">
  <path d="..."/>
</svg>
<span class="text-xs">Rule 11: {{ candidate.exception_reason }}</span>
{% endif %}

<!-- Rule 12: Blackout period -->
{% if member.in_blackout %}
<div class="alert alert-error">
  Member in 2-week blackout period (quit/discharge on {{ member.blackout_start }})
  <span class="text-xs">Rule 12</span>
</div>
{% endif %}
```

#### 5. Progressive Enhancement with Alpine.js

**What:** Use Alpine.js for lightweight client-side interactivity (time displays, tab state).

**Why:**
- Live clock updates without server polling
- Tab state management for book switching
- Countdown timers for time-sensitive events
- Minimal JavaScript footprint

**Implementation:**
```html
<!-- Live clock -->
<div x-data="{
       now: new Date(),
       init() { setInterval(() => this.now = new Date(), 60000) }
     }">
  <span x-text="now.toLocaleTimeString()"></span>
</div>

<!-- Tab state for book switching -->
<div class="tabs" x-data="{ activeBook: '{{ default_book_id }}' }">
  {% for book in books %}
  <a class="tab"
     :class="{ 'tab-active': activeBook === '{{ book.id }}' }"
     @click="activeBook = '{{ book.id }}'"
     hx-get="/dispatch/partials/queue-table?book_id={{ book.id }}"
     hx-target="#queue-table"
     hx-swap="innerHTML">
    {{ book.name }}
  </a>
  {% endfor %}
</div>
```

---

## Implementation Details

### File Structure

```
src/
├── services/
│   ├── referral_frontend_service.py   # Weeks 26: Books & Registration
│   └── dispatch_frontend_service.py   # Weeks 27: Dispatch Workflow
├── routers/
│   ├── referral_frontend.py           # 17 routes (5 pages, 8 partials, 3 forms, 1 search)
│   └── dispatch_frontend.py           # 11 routes (6 pages, 5 partials)
├── templates/
│   ├── referral/
│   │   ├── landing.html               # Overview with stats
│   │   ├── books.html                 # Books list
│   │   ├── book_detail.html           # Book detail with queue
│   │   ├── registrations.html         # Cross-book registrations
│   │   └── registration_detail.html   # Single registration
│   ├── dispatch/
│   │   ├── dashboard.html             # Daily operations dashboard
│   │   ├── requests.html              # Labor request list
│   │   ├── morning_referral.html      # Bid queue processing (CRITICAL)
│   │   ├── active.html                # Active dispatches
│   │   ├── queue.html                 # Queue management
│   │   └── enforcement.html           # Suspensions/violations
│   └── partials/
│       ├── referral/ (8 partials)
│       └── dispatch/ (7 partials)
```

### Route Patterns

**Pattern:** Dual-response routes (full page vs HTMX partial)

```python
@router.get("/dispatch/requests")
async def dispatch_requests(
    request: Request,
    db: Session = Depends(get_db),
    status: str = None,
    search: str = None,
):
    service = DispatchFrontendService(db)
    context = {
        "request": request,
        "labor_requests": service.get_requests(filters={"status": status, "search": search}),
    }

    # Return partial for HTMX requests, full page otherwise
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("partials/dispatch/_request_table.html", context)
    return templates.TemplateResponse("dispatch/requests.html", context)
```

### Badge Helper Pattern

**Convention:** All enum-based statuses get badge helper functions

```python
@staticmethod
def registration_status_badge(status: str) -> dict:
    """Returns DaisyUI badge class and label."""
    badges = {
        "active": {"class": "badge-success", "label": "Active"},
        "resigned": {"class": "badge-warning", "label": "Resigned"},
        "dispatched": {"class": "badge-info", "label": "Dispatched"},
        "suspended": {"class": "badge-error", "label": "Suspended"},
    }
    return badges.get(status, {"class": "badge-ghost", "label": status})
```

**Template Usage:**
```html
{% set badge = service.registration_status_badge(reg.status) %}
<div class="badge {{ badge.class }}">{{ badge.label }}</div>
```

---

## Consequences

### Positive

1. **Consistency** - All Phase 7 frontend follows same patterns as Phase 6 (Weeks 1-19)
2. **Testability** - Frontend services easy to unit test (badge helpers, time context)
3. **Maintainability** - Business logic centralized in services, not scattered in templates
4. **Performance** - HTMX auto-refresh reduces server load vs full page reloads
5. **Compliance** - Business rule visibility supports NLRA audit requirements
6. **Developer Experience** - Clear separation of concerns, predictable file structure

### Negative

1. **Duplication** - Some data transformation happens in both backend and frontend services
2. **Complexity** - Time-aware logic adds complexity to frontend service
3. **Testing Challenges** - Time-based tests require mocking `datetime.now()`
4. **HTMX Dependency** - Heavy reliance on HTMX for interactivity (but consistent with ADR-002)

### Risks

| Risk | Mitigation |
|------|------------|
| **Time zone issues** | Use server timezone consistently, document in UI |
| **Auto-refresh performance** | Configurable intervals, disable on mobile/slow connections |
| **HTMX version changes** | Pin HTMX version in CDN import, test upgrades carefully |
| **Badge helper maintenance** | Unit test all badge helpers, centralize in base class if needed |

---

## Metrics

**Implementation:**
- **Files Created:** 37 (2 services, 2 routers, 13 pages, 15 partials, 2 tests, 2 docs, 1 ADR)
- **Files Modified:** 3 (main.py, sidebar, CHANGELOG)
- **Lines of Code:** 9,587+ insertions (Week 26: 3,869 | Week 27: 5,718)
- **Routes:** 28 (17 referral, 11 dispatch)
- **Templates:** 28 (13 pages, 15 partials)
- **Tests:** 51 new tests (22 Week 26, 29 Week 27)

**Test Coverage:**
- **Total Tests:** 593 (up from 542)
- **Passing:** 568 (95.8%)
- **Blocked:** 25 (pre-existing backend model relationship issue)

**Business Rules Surfaced:** 8/14 (Rules 2, 3, 4, 8, 9, 11, 12, 13)

---

## Alternatives Considered

### 1. Single Unified FrontendService

**Pros:**
- Less code duplication
- Shared badge helpers

**Cons:**
- Massive service class (600+ lines)
- Violates single responsibility principle
- Harder to test

**Decision:** Rejected. Separate services by domain (Referral vs Dispatch)

### 2. Backend Services Directly in Routes

**Pros:**
- No frontend service layer
- Simpler architecture

**Cons:**
- Business logic in routes (harder to test)
- Duplicated badge helpers across templates
- Pagination/filtering logic scattered

**Decision:** Rejected. Frontend service layer provides clear separation.

### 3. React/Vue SPA with API

**Pros:**
- Rich client-side interactivity
- Better separation of concerns

**Cons:**
- Requires build step (violates ADR-002)
- More complex deployment
- Higher development time

**Decision:** Rejected. HTMX + Jinja2 sufficient for dispatch UI complexity.

---

## Related Decisions

- **ADR-002**: Frontend Framework (HTMX + Jinja2 stack)
- **ADR-010**: Operations Frontend Patterns (established service wrapper pattern)
- **ADR-015**: Referral Dispatch Architecture (backend design)

---

## References

- Instruction Documents: `docs/instructions/week26-27/`
- API Discovery: `docs/phase7/week26_api_discovery.md`, `docs/phase7/week27_api_discovery.md`
- Implementation Commits: `a3f60e9` (Week 26), `27aadf4` (Week 27)
- Business Rules: IBEW Local 46 Referral Procedures (Effective October 4, 2024)
