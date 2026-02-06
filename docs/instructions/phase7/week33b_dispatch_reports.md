# Claude Code Instruction: Week 33B — Dispatch & Labor Request Reports (P0 Critical)

**Source:** Spoke 2 → Claude Code
**Date:** February 5, 2026
**Priority:** 🔴 HIGH
**Estimated Time:** 5 hours
**Branch:** develop
**Risk Level:** MEDIUM — extends ReferralReportService from 33A, time-sensitive report logic
**Prerequisite:** Week 33A complete (ReferralReportService exists, 4 OWL reports functional)

---

## Context

This is the second batch of P0 reports. While Week 33A covered the "who is available" view (out-of-work lists), this batch covers the "what happened / what's happening" view — dispatch activity, labor requests, and the critical Morning Referral Sheet.

The Morning Referral Sheet is the most time-sensitive report in the system. It must reflect the state of affairs as of the 3:00 PM cutoff the previous day (Business Rule #3). Dispatchers print this at 7:30-8:00 AM and use it to process referrals in the morning sequence defined by Rule #2.

**Reports in this batch:**

| # | Report Name | Output Formats | Usage |
|---|-------------|---------------|-------|
| 1 | Daily Dispatch Log | PDF + Excel | End-of-day record: all dispatches for a date/range |
| 2 | Dispatch History by Member | PDF | Lookup: complete dispatch history for one member |
| 3 | Labor Request Status | PDF + Excel | Active/filled/cancelled/expired request tracking |
| 4 | Morning Referral Sheet | PDF | **Critical daily report** — next-morning's processing queue |
| 5 | Active Dispatches | PDF + Excel | Currently dispatched members by employer |

---

## Pre-Flight Checklist

- [ ] `git checkout develop && git pull origin develop`
- [ ] `docker-compose up -d`
- [ ] `pytest -v --tb=short` — verify baseline (should be ~537+ after Week 33A)
- [ ] Read `CLAUDE.md` for current state
- [ ] Confirm `ReferralReportService` exists at `src/services/referral_report_service.py`
- [ ] Confirm `referral_reports_api` router exists and is registered in `src/main.py`
- [ ] Confirm base report template exists at `src/templates/reports/referral/_base_report.html`

---

## Task 1: Add Dispatch Report Methods to ReferralReportService (~1.5 hrs)

### Files to Modify

| File | Change |
|------|--------|
| `src/services/referral_report_service.py` | Add 5 report data methods + PDF/Excel renderers |

### Implementation Details

**Add these methods to `ReferralReportService`:**

```python
# --- Report 5: Daily Dispatch Log ---
def get_daily_dispatch_log(
    self, start_date: date, end_date: Optional[date] = None
) -> dict:
    """Assemble all dispatches within a date range.
    
    Args:
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive). Defaults to start_date (single day).
    
    Returns: {
        'dispatches': [{
            'dispatch_id': int,
            'dispatch_date': datetime,
            'member_name': str,
            'member_card': str,
            'book_name': str,
            'employer_name': str,
            'job_site': str (if available),
            'labor_request_id': int,
            'dispatch_type': str (regular, short_call, by_name),
            'status': str,
            'generates_checkmark': bool,
        }],
        'date_range': {'start': date, 'end': date},
        'total_dispatches': int,
        'by_book_count': {book_name: count},
        'by_employer_count': {employer_name: count},
        'generated_at': datetime,
    }
    
    Sort: dispatch_date descending (most recent first within the range).
    """

def render_daily_dispatch_log_pdf(
    self, start_date: date, end_date: Optional[date] = None
) -> BytesIO:
    """Render PDF for daily dispatch log."""

def render_daily_dispatch_log_excel(
    self, start_date: date, end_date: Optional[date] = None
) -> BytesIO:
    """Render Excel for daily dispatch log."""

# --- Report 6: Dispatch History by Member ---
def get_member_dispatch_history(self, member_id: int) -> dict:
    """Assemble complete dispatch history for one member.
    
    Returns: {
        'member': Member object,
        'dispatches': [{
            'dispatch_date': datetime,
            'book_name': str,
            'employer_name': str,
            'job_site': str,
            'dispatch_type': str,
            'duration_days': int (if completed),
            'outcome': str (completed, quit, discharged, laid_off),
            'was_short_call': bool,
            'generated_checkmark': bool,
        }],
        'total_dispatches': int,
        'total_employers': int,
        'average_duration': float (days),
        'check_marks_total': int,
        'generated_at': datetime,
    }
    
    Sort: dispatch_date descending (most recent first).
    """

def render_member_dispatch_history_pdf(self, member_id: int) -> BytesIO:
    """Render PDF for member dispatch history."""

# --- Report 7: Labor Request Status ---
def get_labor_request_status(
    self, 
    status_filter: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> dict:
    """Assemble labor request status report.
    
    Args:
        status_filter: OPEN, FILLED, CANCELLED, EXPIRED, or None (all)
        start_date/end_date: Filter by request creation date range
    
    Returns: {
        'requests': [{
            'request_id': int,
            'employer_name': str,
            'book_name': str,
            'workers_requested': int,
            'workers_filled': int,
            'status': str,
            'created_at': datetime,
            'filled_at': datetime (if filled),
            'agreement_type': str,
            'is_short_call': bool,
            'is_by_name': bool,
        }],
        'status_counts': {'OPEN': n, 'FILLED': n, 'CANCELLED': n, 'EXPIRED': n},
        'total_workers_requested': int,
        'total_workers_filled': int,
        'fill_rate': float (percentage),
        'generated_at': datetime,
    }
    """

def render_labor_request_status_pdf(self, **kwargs) -> BytesIO:
    """Render PDF for labor request status."""

def render_labor_request_status_excel(self, **kwargs) -> BytesIO:
    """Render Excel for labor request status."""

# --- Report 8: Morning Referral Sheet ---
def get_morning_referral_sheet(self, target_date: Optional[date] = None) -> dict:
    """Assemble the morning referral processing sheet.
    
    THIS IS THE MOST CRITICAL DAILY REPORT.
    
    Logic:
    1. Get all OPEN labor requests received before 3:00 PM the previous working day
    2. Group by book, sorted in morning processing order (Rule #2)
    3. For each request, show the next N members on the book (by APN) 
       where N = workers_requested
    4. Flag any members with 2 check marks (at-limit warning)
    5. Flag any web bids received during the 5:30 PM - 7:00 AM window
    
    Args:
        target_date: The morning being processed. Defaults to today.
                     Uses previous working day's 3 PM cutoff for request inclusion.
    
    Returns: {
        'target_date': date,
        'cutoff_datetime': datetime (previous working day at 3 PM),
        'processing_groups': [{
            'time_slot': '8:30 AM',
            'books': [{
                'book_name': str,
                'requests': [{
                    'request_id': int,
                    'employer_name': str,
                    'workers_needed': int,
                    'agreement_type': str,
                    'is_short_call': bool,
                    'is_by_name': bool,
                    'web_bids': [{member_name, bid_time}],
                    'next_in_queue': [{
                        'position': int,
                        'member_name': str,
                        'apn': Decimal,
                        'tier': int,
                        'check_marks': int,
                        'at_check_limit': bool,
                        'has_web_bid': bool,
                    }],
                }],
            }],
        }],
        'total_requests': int,
        'total_workers_needed': int,
        'generated_at': datetime,
    }
    """

def render_morning_referral_sheet_pdf(
    self, target_date: Optional[date] = None
) -> BytesIO:
    """Render PDF for morning referral sheet.
    
    Layout: Landscape orientation for wide tables.
    Grouped by processing time slot, then by book.
    Visual flags: yellow highlight for at-limit check marks, 
                  blue highlight for web bids.
    """

# --- Report 9: Active Dispatches ---
def get_active_dispatches(self) -> dict:
    """Assemble currently active (outstanding) dispatches.
    
    "Active" = dispatched but not yet completed/terminated.
    
    Returns: {
        'dispatches': [{
            'member_name': str,
            'member_card': str,
            'employer_name': str,
            'book_name': str,
            'dispatch_date': datetime,
            'days_on_job': int (calculated from dispatch_date to today),
            'is_short_call': bool,
            'short_call_days_remaining': int (if short call),
            'agreement_type': str,
        }],
        'total_active': int,
        'by_employer': {employer_name: count},
        'by_book': {book_name: count},
        'short_call_count': int,
        'long_call_count': int,
        'generated_at': datetime,
    }
    
    Sort: employer_name ascending, then dispatch_date ascending.
    """

def render_active_dispatches_pdf(self) -> BytesIO:
    """Render PDF for active dispatches."""

def render_active_dispatches_excel(self) -> BytesIO:
    """Render Excel for active dispatches."""
```

**Previous working day calculation** (for Morning Referral Sheet):
```python
from datetime import date, timedelta

def _previous_working_day(self, target: date) -> date:
    """Return the previous working day (skip weekends, no holiday awareness yet).
    
    Monday → Friday, Sunday → Friday, Saturday → Friday
    Tuesday-Friday → previous day
    """
    delta = 1
    if target.weekday() == 0:  # Monday
        delta = 3
    elif target.weekday() == 6:  # Sunday
        delta = 2
    return target - timedelta(days=delta)
```

> **Note:** Holiday awareness (Rule #1 mentions no holidays) is a Priority 3 gap. For now, weekends-only logic is acceptable. Add a `TODO` comment for holiday calendar integration.

---

## Task 2: Create PDF Report Templates (~1 hr)

### Files to Create

| File | Purpose |
|------|---------|
| `src/templates/reports/referral/daily_dispatch_log.html` | Dispatch log with summary stats header |
| `src/templates/reports/referral/member_dispatch_history.html` | Member-focused dispatch timeline |
| `src/templates/reports/referral/labor_request_status.html` | Request tracking with status badges |
| `src/templates/reports/referral/morning_referral_sheet.html` | **Landscape layout**, grouped by time slot |
| `src/templates/reports/referral/active_dispatches.html` | Employer-grouped active dispatch list |

### Implementation Details

All templates extend `_base_report.html` from Week 33A.

**Morning Referral Sheet — special layout:**

```html
{% extends "_base_report.html" %}
{% block title %}Morning Referral Sheet{% endblock %}
{% block subtitle %}Processing Date: {{ target_date.strftime('%A, %B %d, %Y') }}{% endblock %}

<!-- Override page style for landscape -->
<style>
    @page { size: letter landscape; margin: 0.5in; }
</style>

{% block content %}
<div class="meta">
    Cutoff: Requests received before {{ cutoff_datetime.strftime('%I:%M %p on %A, %B %d') }}
    | Total Requests: {{ total_requests }}
    | Workers Needed: {{ total_workers_needed }}
</div>

{% for group in processing_groups %}
<h2 class="time-slot-header">{{ group.time_slot }} Processing</h2>
{% for book_data in group.books %}
<h3>{{ book_data.book_name }}</h3>
{% for request in book_data.requests %}
<!-- Request card with employer, workers needed, type -->
<!-- Queue table: next N members by APN -->
<!-- Yellow row highlight: member at 2 check marks -->
<!-- Blue row highlight: member has pending web bid -->
{% endfor %}
{% endfor %}
{% endfor %}
{% endblock %}
```

**Daily Dispatch Log columns:**
| Dispatch # | Date/Time | Member | Card # | Book | Employer | Type | Checkmark? | Status |

**Labor Request Status columns:**
| Request # | Employer | Book | Workers Req/Filled | Status | Agreement | Type | Created | Filled |

**Active Dispatches columns:**
| Member | Card # | Employer | Book | Dispatched | Days on Job | Short Call? | Days Left | Agreement |

---

## Task 3: Add API Endpoints (~45 min)

### Files to Modify

| File | Change |
|------|--------|
| `src/routers/referral_reports_api.py` | Add 5 report endpoints |

### Implementation Details

```python
@router.get("/dispatch-log")
# Query params: format (pdf|xlsx), start_date (required), end_date (optional)
# Returns: StreamingResponse

@router.get("/member/{member_id}/dispatch-history")
# Query params: format (pdf)
# Returns: StreamingResponse

@router.get("/labor-requests")
# Query params: format (pdf|xlsx), status (optional), start_date, end_date (optional)
# Returns: StreamingResponse

@router.get("/morning-referral")
# Query params: format (pdf), target_date (optional, defaults to today)
# Returns: StreamingResponse
# NOTE: This is the report dispatchers print every morning.

@router.get("/active-dispatches")
# Query params: format (pdf|xlsx)
# Returns: StreamingResponse
```

**Date parameter handling:**
```python
from datetime import date

@router.get("/dispatch-log")
def get_dispatch_log(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date, defaults to start_date"),
    format: str = Query("pdf", regex="^(pdf|xlsx)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ... (same StreamingResponse pattern as 33A)
```

---

## Task 4: Wire Reports to Navigation Dashboard (~30 min)

### Files to Modify

| File | Change |
|------|--------|
| `src/services/dispatch_frontend_service.py` | Update `get_report_categories()` — mark 5 more reports as available |
| `src/templates/dispatch/reports_landing.html` | Add date picker controls for date-ranged reports |

### Implementation Details

Reports that need date inputs (Dispatch Log, Labor Request Status) require a simple date picker form on the landing page before download. Pattern:

```html
<!-- For dispatch log: show start_date and end_date inputs -->
<div x-data="{ showDates: false }">
    <button @click="showDates = !showDates" class="btn btn-sm btn-outline">
        📥 Daily Dispatch Log
    </button>
    <div x-show="showDates" class="mt-2 p-3 bg-base-200 rounded-lg">
        <label>Start Date: <input type="date" name="start_date" required></label>
        <label>End Date: <input type="date" name="end_date"></label>
        <a :href="`/api/v1/reports/referral/dispatch-log?format=pdf&start_date=${...}&end_date=${...}`"
           class="btn btn-sm btn-primary">Download PDF</a>
    </div>
</div>
```

The Morning Referral Sheet should have a "Print Today's Sheet" prominent button with no date picker needed (defaults to today).

---

## Task 5: Tests (~45 min)

### Files to Modify

| File | Change |
|------|--------|
| `src/tests/test_referral_reports.py` | Add dispatch report tests |

### Tests Required (8 minimum)

```python
class TestDispatchReports:
    def test_daily_dispatch_log_date_range(self, db, sample_dispatches):
        """Service returns only dispatches within the specified date range"""

    def test_daily_dispatch_log_single_day(self, db, sample_dispatches):
        """When end_date omitted, returns single day of dispatches"""

    def test_member_dispatch_history_complete(self, db, sample_member_with_dispatches):
        """Returns all dispatches for the member, most recent first"""

    def test_labor_request_status_filter(self, db, sample_labor_requests):
        """Status filter correctly limits results (e.g., OPEN only)"""

    def test_morning_referral_sheet_cutoff(self, db, sample_labor_requests):
        """Only includes requests received before 3 PM previous working day"""

    def test_morning_referral_sheet_processing_order(self, db, sample_labor_requests):
        """Processing groups follow Rule #2 morning sequence"""

    def test_active_dispatches_excludes_completed(self, db, sample_dispatches):
        """Only includes dispatches without completion/termination"""

class TestDispatchReportAPI:
    def test_dispatch_log_endpoint(self, auth_client, sample_dispatches):
        """GET /api/v1/reports/referral/dispatch-log returns 200"""

    def test_morning_referral_requires_auth(self, client):
        """Unauthenticated morning referral request returns 401/302"""
```

**Additional test fixtures needed:**
- `sample_dispatches` — 5+ dispatch records across 2+ days, mixed statuses (active, completed, short_call)
- `sample_member_with_dispatches` — One member with 3+ dispatches to various employers
- `sample_labor_requests` — Mix of OPEN/FILLED/CANCELLED requests across different books

---

## Anti-Patterns (DO NOT)

- Do NOT calculate the morning referral cutoff using `datetime.now()` in tests — use a fixed date to ensure test determinism
- Do NOT include expired/cancelled requests in the Morning Referral Sheet — only OPEN requests
- Do NOT show member SSN or sensitive PII in reports — use name + card number only
- Do NOT sort dispatches by ID — sort by dispatch_date
- Do NOT modify existing service methods from Week 33A
- Do NOT skip the `_previous_working_day()` calculation for the morning sheet
- Do NOT put rendering logic in API endpoints — all rendering in service layer

---

## Success Criteria

- [ ] 5 new report methods added to `ReferralReportService` with PDF/Excel renderers
- [ ] Morning Referral Sheet correctly implements 3 PM cutoff and processing order
- [ ] 5 PDF templates created (morning sheet in landscape)
- [ ] 5 API endpoints returning correct content types
- [ ] Reports navigation dashboard updated with 5 more available reports (9 total)
- [ ] Date picker controls functional for date-ranged reports
- [ ] Minimum 8 new tests passing
- [ ] No regression in existing tests

---

## End-of-Session (MANDATORY)

- [ ] `pytest -v` — verify green (or document new failures)
- [ ] `ruff check . --fix && ruff format .`
- [ ] `git add -A && git commit -m "feat(phase7): Week 33B — dispatch & labor request reports (P0)"`
- [ ] `git push origin develop`
- [ ] Update `CLAUDE.md` — test counts, mark reports batch 2 complete
- [ ] Update `CHANGELOG.md`
- [ ] Create session log: `docs/reports/session-logs/2026-XX-XX-week33b-dispatch-reports.md`
- [ ] If `conftest.py` modified (new fixtures), note in session summary for Hub handoff

---

## Files Changed/Created Summary (Expected)

**Created:**
- `/src/templates/reports/referral/daily_dispatch_log.html`
- `/src/templates/reports/referral/member_dispatch_history.html`
- `/src/templates/reports/referral/labor_request_status.html`
- `/src/templates/reports/referral/morning_referral_sheet.html`
- `/src/templates/reports/referral/active_dispatches.html`

**Modified:**
- `/src/services/referral_report_service.py` — 5 report methods + renderers added
- `/src/routers/referral_reports_api.py` — 5 new endpoints
- `/src/services/dispatch_frontend_service.py` — 5 more reports marked available
- `/src/templates/dispatch/reports_landing.html` — date picker controls, available links
- `/src/tests/test_referral_reports.py` — 8+ new tests

---

## Session Reminders

> **Morning Referral Sheet = most critical report.** Dispatchers rely on this every morning. The 3 PM cutoff and processing order (Rule #2 + Rule #3) must be correct. A wrong sheet = members dispatched out of order = grievance.

> **APN = DECIMAL(10,2).** Queue position in Morning Referral Sheet is determined by APN sort order. Never truncate.

> **Short calls (Rule #9):** ≤10 business days. Mark them clearly in dispatch log and active dispatches reports. Show days remaining for active short calls.

> **Audit.** Report generation is an auditable action. Log it.

---

*Week 33B Instruction — Spoke 2: Operations*
*UnionCore (IP2A-Database-v2) — February 5, 2026*
