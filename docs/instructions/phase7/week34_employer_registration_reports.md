# Claude Code Instruction: Week 34 — Employer & Registration Reports (P0/P1)

**Source:** Spoke 2 → Claude Code
**Date:** February 5, 2026
**Priority:** 🟡 MEDIUM (P0/P1 mix — completes core operational report set)
**Estimated Time:** 5 hours
**Branch:** develop
**Risk Level:** LOW — extends established ReferralReportService pattern from 33A/33B
**Prerequisite:** Week 33B complete (9 reports functional, report infrastructure mature)

---

## Context

This is the third and final P0 batch plus the first P1 reports. After this sprint, all 16 P0 (Critical) reports will be accounted for across Weeks 33A, 33B, and 34. The remaining P1 reports (28 more) continue in Week 35+.

These reports serve two audiences: **dispatch staff** (check marks, re-sign deadlines) and **business agents** (employer workforce visibility, registration trends). The Re-Sign Due List is operationally critical — missing a 30-day re-sign deadline means a member loses their book position (Business Rule #7).

**Reports in this batch:**

| # | Report Name | Priority | Output | Audience |
|---|-------------|----------|--------|----------|
| 1 | Employer Active List | P0 | PDF + Excel | Business agents, dispatch staff |
| 2 | Employer Dispatch History | P1 | PDF + Excel | Business agents |
| 3 | Registration History | P1 | Excel | Dispatch staff, compliance |
| 4 | Check Mark Report | P1 | PDF | Dispatch staff, officers |
| 5 | Re-Sign Due List | P0 | PDF | Dispatch staff (**daily operational**) |

---

## Pre-Flight Checklist

- [ ] `git checkout develop && git pull origin develop`
- [ ] `docker-compose up -d`
- [ ] `pytest -v --tb=short` — verify baseline (should be ~545+ after Week 33B)
- [ ] Read `CLAUDE.md` for current state
- [ ] Confirm `ReferralReportService` has all 9 report methods from Weeks 33A and 33B
- [ ] Confirm `referral_reports_api` router has 9 endpoints
- [ ] Confirm reports navigation dashboard shows 9 available reports

---

## Task 1: Add Report Methods to ReferralReportService (~2 hrs)

### Files to Modify

| File | Change |
|------|--------|
| `src/services/referral_report_service.py` | Add 5 report data methods + PDF/Excel renderers |

### Implementation Details

```python
# --- Report 10: Employer Active List (P0) ---
def get_employer_active_list(
    self, contract_code: Optional[str] = None
) -> dict:
    """Assemble list of employers with active labor requests.
    
    "Active" = has at least one OPEN labor request, OR has members 
    currently dispatched to them.
    
    Args:
        contract_code: Filter to specific contract (e.g., 'WIREPERSON'). 
                       None = all contracts.
    
    Returns: {
        'employers': [{
            'employer_id': int,
            'employer_name': str,
            'contract_codes': [str],  # May have multiple (e.g., WIREPERSON + RESIDENTIAL)
            'open_requests': int,
            'workers_currently_dispatched': int,
            'total_dispatches_ytd': int,
            'last_dispatch_date': date,
            'contact_info': str (if available),
        }],
        'total_employers': int,
        'total_open_requests': int,
        'total_dispatched_workers': int,
        'contract_code_filter': str or 'All',
        'generated_at': datetime,
    }
    
    Sort: employer_name ascending.
    """

def render_employer_active_list_pdf(self, **kwargs) -> BytesIO:
    """Render PDF."""

def render_employer_active_list_excel(self, **kwargs) -> BytesIO:
    """Render Excel."""

# --- Report 11: Employer Dispatch History (P1) ---
def get_employer_dispatch_history(
    self, employer_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> dict:
    """Assemble dispatch history for a specific employer.
    
    Args:
        employer_id: Target employer
        start_date/end_date: Filter range. Defaults to current year.
    
    Returns: {
        'employer': Organization object,
        'contract_codes': [str],
        'dispatches': [{
            'dispatch_date': datetime,
            'member_name': str,
            'member_card': str,
            'book_name': str,
            'dispatch_type': str,
            'duration_days': int (if completed),
            'outcome': str,
            'was_short_call': bool,
        }],
        'total_dispatches': int,
        'unique_members': int,
        'average_duration': float (days),
        'short_call_percentage': float,
        'date_range': {'start': date, 'end': date},
        'generated_at': datetime,
    }
    
    Sort: dispatch_date descending.
    """

def render_employer_dispatch_history_pdf(self, **kwargs) -> BytesIO:
    """Render PDF."""

def render_employer_dispatch_history_excel(self, **kwargs) -> BytesIO:
    """Render Excel."""

# --- Report 12: Registration History (P1) ---
def get_registration_history(
    self,
    book_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    activity_type: Optional[str] = None,
) -> dict:
    """Assemble registration activity history (registrations, re-signs, 
    resignations, roll-offs, re-registrations).
    
    This report uses the registration_activities table, NOT the 
    book_registrations table directly. It shows the activity log.
    
    Args:
        book_id: Filter to specific book. None = all books.
        start_date/end_date: Filter range. Defaults to last 30 days.
        activity_type: Filter by type (REGISTER, RE_SIGN, RESIGN, 
                       ROLL_OFF, RE_REGISTER). None = all.
    
    Returns: {
        'activities': [{
            'activity_date': datetime,
            'member_name': str,
            'member_card': str,
            'book_name': str,
            'tier': int,
            'activity_type': str,
            'reason': str (for roll-offs and re-registrations),
            'previous_apn': Decimal (for re-registrations),
            'new_apn': Decimal (for registrations/re-registrations),
            'performed_by': str (staff who processed),
        }],
        'activity_counts': {'REGISTER': n, 'RE_SIGN': n, ...},
        'total_activities': int,
        'book_filter': str or 'All Books',
        'date_range': {'start': date, 'end': date},
        'generated_at': datetime,
    }
    
    Sort: activity_date descending.
    """

def render_registration_history_excel(self) -> BytesIO:
    """Render Excel only — this report is data-heavy, not a printable PDF.
    
    Sheets:
    - Sheet 1: Activity Log (all activity records)
    - Sheet 2: Summary (counts by type, by book, by week)
    """

# --- Report 13: Check Mark Report (P1) ---
def get_check_mark_report(
    self, book_id: Optional[int] = None
) -> dict:
    """Assemble check mark status across members.
    
    Shows all members with 1+ active check marks, organized by book.
    Highlights members at the 2-mark limit (one more = roll-off).
    
    Args:
        book_id: Filter to specific book. None = all books.
    
    Returns: {
        'books': [{
            'book_name': str,
            'book_id': int,
            'members_with_marks': [{
                'member_name': str,
                'member_card': str,
                'check_mark_count': int,
                'at_limit': bool (count >= 2),
                'marks': [{
                    'date': date,
                    'reason': str,
                    'associated_dispatch_id': int (if applicable),
                }],
            }],
            'total_with_marks': int,
            'at_limit_count': int,
        }],
        'total_members_with_marks': int,
        'total_at_limit': int,
        'book_filter': str or 'All Books',
        'generated_at': datetime,
    }
    
    Sort: Within each book, members sorted by check_mark_count descending
    (most marks first — the members closest to roll-off appear at top).
    """

def render_check_mark_report_pdf(self, **kwargs) -> BytesIO:
    """Render PDF with visual indicators:
    - 1 mark: yellow row
    - 2 marks: orange/red row with ⚠ icon
    """

# --- Report 14: Re-Sign Due List (P0) ---
def get_re_sign_due_list(
    self, 
    days_ahead: int = 7,
    include_overdue: bool = True,
) -> dict:
    """Assemble list of members whose 30-day re-sign is approaching or overdue.
    
    THIS IS A CRITICAL DAILY REPORT. Missing a re-sign = member dropped 
    from ALL books (Rule #7). Dispatchers check this daily.
    
    Args:
        days_ahead: Show members due within this many days (default 7)
        include_overdue: Include already-overdue members (default True)
    
    Returns: {
        'overdue': [{
            'member_name': str,
            'member_card': str,
            'book_name': str,
            'tier': int,
            'apn': Decimal,
            'last_re_sign': date,
            're_sign_due': date,
            'days_overdue': int,
        }],
        'due_soon': [{
            'member_name': str,
            'member_card': str,
            'book_name': str,
            'tier': int,
            'apn': Decimal,
            'last_re_sign': date,
            're_sign_due': date,
            'days_until_due': int,
        }],
        'overdue_count': int,
        'due_soon_count': int,
        'days_ahead': int,
        'generated_at': datetime,
    }
    
    Calculation: re_sign_due = last_re_sign_date + 30 days
                 (or registered_date + 30 days if never re-signed)
    
    Sort: 
    - Overdue: days_overdue descending (most critical first)
    - Due soon: days_until_due ascending (soonest first)
    """

def render_re_sign_due_list_pdf(self, **kwargs) -> BytesIO:
    """Render PDF with urgency styling:
    - Overdue section: red header, bold rows
    - Due within 3 days: orange rows
    - Due within 7 days: yellow rows
    """
```

---

## Task 2: Create PDF/Excel Templates (~1 hr)

### Files to Create

| File | Purpose |
|------|---------|
| `src/templates/reports/referral/employer_active_list.html` | Active employers with open requests |
| `src/templates/reports/referral/employer_dispatch_history.html` | Single employer's dispatch history |
| `src/templates/reports/referral/check_mark_report.html` | Check mark status with visual urgency |
| `src/templates/reports/referral/re_sign_due_list.html` | Re-sign deadlines with urgency coloring |

**Note:** Registration History is Excel-only (no PDF template needed).

### Template Details

**Employer Active List columns:**
| Employer | Contracts | Open Requests | Workers Dispatched | YTD Total | Last Dispatch |

**Employer Dispatch History columns:**
| Date | Member | Card # | Book | Type | Duration | Short Call? | Outcome |

**Check Mark Report layout:**
- Grouped by book
- Each book section: table of members with marks
- Row coloring: 1 mark = `background: #fef9c3` (yellow), 2 marks = `background: #fed7aa` (orange) with ⚠ prefix
- Summary line per book: "X members with marks, Y at limit"

**Re-Sign Due List layout:**
- Two sections: "OVERDUE" (red header) and "DUE WITHIN X DAYS" (yellow header)
- Overdue section at top, always visible even if empty ("No overdue members ✓")
- Row styling based on urgency:
  - Overdue: `background: #fecaca; font-weight: bold;`
  - Due in 1-3 days: `background: #fed7aa;`
  - Due in 4-7 days: `background: #fef9c3;`

---

## Task 3: Add API Endpoints (~30 min)

### Files to Modify

| File | Change |
|------|--------|
| `src/routers/referral_reports_api.py` | Add 5 report endpoints |

### Endpoints

```python
@router.get("/employers/active")
# Query params: format (pdf|xlsx), contract_code (optional)
# Returns: StreamingResponse

@router.get("/employers/{employer_id}/dispatch-history")
# Query params: format (pdf|xlsx), start_date (optional), end_date (optional)
# Returns: StreamingResponse

@router.get("/registrations/history")
# Query params: format (xlsx ONLY), book_id (optional), start_date, end_date, activity_type
# Note: Excel only — no PDF for this report
# Returns: StreamingResponse

@router.get("/check-marks")
# Query params: format (pdf), book_id (optional)
# Returns: StreamingResponse

@router.get("/re-sign-due")
# Query params: format (pdf), days_ahead (default 7), include_overdue (default true)
# Returns: StreamingResponse
```

**Validation for registration history — Excel only:**
```python
@router.get("/registrations/history")
def get_registration_history(
    format: str = Query("xlsx", regex="^xlsx$"),  # Excel only
    # ...
):
    # ...
```

---

## Task 4: Wire Reports to Navigation Dashboard (~30 min)

### Files to Modify

| File | Change |
|------|--------|
| `src/services/dispatch_frontend_service.py` | Mark 5 more reports as available (14 total) |
| `src/templates/dispatch/reports_landing.html` | Add employer selector for employer-specific reports, contract code filter |

### Implementation Details

Reports that need an employer selector (Employer Dispatch History) require a searchable dropdown. Use the existing HTMX search pattern:

```html
<!-- Employer search for dispatch history report -->
<div x-data="{ employerId: null, employerName: '' }">
    <input type="text" 
           placeholder="Search employer..."
           hx-get="/api/v1/employers/search" 
           hx-trigger="keyup changed delay:300ms"
           hx-target="#employer-results"
           name="q"
           class="input input-bordered input-sm w-full">
    <div id="employer-results">
        <!-- HTMX loads employer suggestions here -->
    </div>
</div>
```

> **Note:** Check if an employer search endpoint already exists in `src/routers/`. If not, the report can use a simple ID input field as fallback. Do NOT create new CRUD endpoints for employers in this sprint — that's Spoke 1 territory.

The Re-Sign Due List should have a prominent "Print Today's Due List" button at the top of the reports page, similar to the Morning Referral Sheet treatment from Week 33B.

---

## Task 5: Tests (~1 hr)

### Files to Modify

| File | Change |
|------|--------|
| `src/tests/test_referral_reports.py` | Add employer/registration/checkmark/re-sign report tests |

### Tests Required (8 minimum)

```python
class TestEmployerReports:
    def test_employer_active_list_data(self, db, sample_employers_with_requests):
        """Service returns employers with open requests and dispatched workers"""

    def test_employer_active_list_contract_filter(self, db, sample_employers_with_requests):
        """Contract code filter limits to matching employers only"""

    def test_employer_dispatch_history(self, db, sample_employer_with_dispatches):
        """Returns complete dispatch history for one employer"""

class TestRegistrationReport:
    def test_registration_history_activity_types(self, db, sample_registration_activities):
        """Returns correct activity records with type filtering"""

    def test_registration_history_excel_two_sheets(self, db, sample_registration_activities):
        """Excel output has both Activity Log and Summary sheets"""

class TestCheckMarkReport:
    def test_check_mark_report_groups_by_book(self, db, sample_checkmarks):
        """Check marks organized by book, sorted by count descending"""

    def test_check_mark_report_at_limit_flag(self, db, sample_checkmarks):
        """Members with 2+ marks flagged as at_limit"""

class TestReSignDueList:
    def test_re_sign_due_list_finds_overdue(self, db, sample_registrations_with_stale_re_signs):
        """Identifies members past their 30-day re-sign deadline"""

    def test_re_sign_due_list_finds_upcoming(self, db, sample_registrations_with_stale_re_signs):
        """Identifies members due within days_ahead window"""

    def test_re_sign_due_list_calculation(self, db, sample_registrations_with_stale_re_signs):
        """Re-sign due date calculated correctly: last_re_sign + 30 days"""
```

**Test fixtures needed:**
- `sample_employers_with_requests` — 3+ employers, mix of open/filled requests, some with active dispatches
- `sample_employer_with_dispatches` — One employer with 5+ dispatches (varied types/outcomes)
- `sample_registration_activities` — 10+ activity records across multiple books and types
- `sample_checkmarks` — Members with 0, 1, and 2 check marks across different books
- `sample_registrations_with_stale_re_signs` — Registrations with varied `last_re_sign_date` values: some overdue, some due within 7 days, some fresh

Add fixtures to `test_referral_reports.py` (not conftest) to avoid cross-test pollution.

---

## Anti-Patterns (DO NOT)

- Do NOT calculate re-sign due date in the template — do it in the service layer
- Do NOT show employer contact details (phone, email) to non-Staff roles
- Do NOT create new models for reports — use existing models with query joins
- Do NOT create Alembic migrations — service + template changes only
- Do NOT create employer CRUD endpoints — that's Spoke 1 scope
- Do NOT modify existing report methods from Weeks 33A/33B
- Do NOT hardcode the 30-day re-sign period — use a constant that can be updated
- Do NOT return PDF for Registration History — it's too data-dense, Excel only

---

## Success Criteria

- [ ] 5 new report methods added to `ReferralReportService` (14 total methods)
- [ ] Re-Sign Due List correctly calculates `last_re_sign + 30 days` with urgency tiers
- [ ] Check Mark Report visually distinguishes 1-mark vs 2-mark (at-limit) members
- [ ] Registration History Excel has two sheets (Activity Log + Summary)
- [ ] 4 new PDF templates + 1 Excel-only report template
- [ ] 5 new API endpoints (14 total report endpoints)
- [ ] Reports navigation dashboard shows 14 available reports
- [ ] All P0 reports now functional (16 of 16 accounted for across 33A/33B/34)
- [ ] Minimum 8 new tests passing
- [ ] No regression in existing tests

---

## End-of-Session (MANDATORY)

- [ ] `pytest -v` — verify green (or document new failures)
- [ ] `ruff check . --fix && ruff format .`
- [ ] `git add -A && git commit -m "feat(phase7): Week 34 — employer, registration, check mark, re-sign reports (P0/P1)"`
- [ ] `git push origin develop`
- [ ] Update `CLAUDE.md` — test counts, note all P0 reports complete
- [ ] Update `CHANGELOG.md`
- [ ] Create session log: `docs/reports/session-logs/2026-XX-XX-week34-employer-registration-reports.md`
- [ ] Update `docs/IP2A_MILESTONE_CHECKLIST.md` — mark 7f progress (14 of 78 reports built)
- [ ] **Generate Hub handoff note** — all P0 reports complete, ready for Hub to assess version bump and P1 batch strategy

---

## Files Changed/Created Summary (Expected)

**Created:**
- `/src/templates/reports/referral/employer_active_list.html`
- `/src/templates/reports/referral/employer_dispatch_history.html`
- `/src/templates/reports/referral/check_mark_report.html`
- `/src/templates/reports/referral/re_sign_due_list.html`

**Modified:**
- `/src/services/referral_report_service.py` — 5 report methods + renderers added (14 total)
- `/src/routers/referral_reports_api.py` — 5 new endpoints (14 total)
- `/src/services/dispatch_frontend_service.py` — 5 more reports marked available (14 total)
- `/src/templates/dispatch/reports_landing.html` — employer selector, contract filter, re-sign button
- `/src/tests/test_referral_reports.py` — 8+ new tests (24+ total report tests)

---

## Post-Sprint: Hub Handoff Checklist

After Week 34, generate a handoff note for the Hub covering:

| Item | Detail |
|------|--------|
| All P0 reports complete | 16 of 16 critical reports functional |
| Total report endpoints | 14 API endpoints on `/api/v1/reports/referral/` |
| Reports dashboard | 14 of 78 reports available via navigation page |
| Test count | ~553+ expected (baseline + ~24 new report tests) |
| Version question | Is this v0.9.9-alpha or v1.0.0-beta? Hub decides. |
| Next work | P1 reports (28 remaining), then P2 (22) and P3 (7) |
| Shared file impact | `src/main.py` was modified in Week 33A (new router). No further shared file changes in 33B or 34. |
| Open question | Should P1 reports continue in Spoke 2, or move to Spoke 3 (Infrastructure/Reports)? |

---

## Session Reminders

> **Re-Sign Due List is safety-critical.** If a member misses their 30-day re-sign, they lose their position on ALL books. The report must be accurate. Use `last_re_sign_date + 30 days` (or `registered_date + 30` if never re-signed).

> **Check marks are per-book.** A member can have 2 marks on WIRE SEATTLE and 0 on WIRE BREMERTON. The report must show per-book breakdown, not a global count.

> **RESIDENTIAL is the 8th contract code.** The employer active list must include it in filter options.

> **Book ≠ Contract.** When filtering employers by contract code, remember STOCKMAN book = STOCKPERSON contract. The report should use contract codes for employer filtering, not book names.

> **Audit.** Report generation is an auditable action. Log every download.

---

*Week 34 Instruction — Spoke 2: Operations*
*UnionCore (IP2A-Database-v2) — February 5, 2026*
