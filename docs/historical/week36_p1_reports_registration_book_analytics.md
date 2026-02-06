# Claude Code Instructions: Week 36 — P1 Reports Sprint A: Registration & Book Analytics

**Source:** Spoke 2: Operations (Hub instruction doc: Weeks 36-38)
**Target:** Claude Code execution
**Project Version:** v0.9.10-alpha (baseline)
**Sprint Scope:** ~10 P1 reports — Registration management + book health monitoring
**Estimated Effort:** 5-6 hours
**Branch:** `develop`
**Spoke:** Spoke 2: Operations

---

## TL;DR

Build ~10 P1 (High priority) reports focused on registration analytics and book management. These are the "how is our book doing?" reports that dispatch staff and officers use weekly/monthly. Follow the established pattern from P0 reports: service method → router endpoint → PDF/Excel template → tests.

---

## Pre-Flight (MANDATORY)

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
git log --oneline -5

# Verify baseline — capture exact pass count
python -m pytest src/tests/ -x -q 2>&1 | tail -20

# Read report inventory — this is the source of truth
cat docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md

# Read current report service to understand existing methods
cat src/services/referral_report_service.py

# Check what report endpoints already exist
grep -n "def " src/routers/referral_reports_api.py

# Check what report templates exist
ls -la src/templates/reports/referral/

# Check existing report tests
grep -n "def test_" src/tests/test_referral_reports.py
```

**RECORD THE BASELINE:** Write down the exact test count and pass count before making any changes. Week 35 left us at 596/621 passing (98.5%). Do not proceed if tests are broken — fix first.

**CRITICAL:** Cross-reference the report inventory file against existing service methods. Identify exactly which P1 reports are already built (some may have been pulled forward during P0 work) and which need building. Do NOT duplicate existing reports.

---

## What Already Exists (Reuse These Patterns)

**Infrastructure:**
- `src/services/referral_report_service.py` — ReferralReportService with 14 P0 report methods
- `src/routers/referral_reports_api.py` — API router with 14 P0 endpoints
- `src/templates/reports/referral/` — 9+ PDF templates with established styling
- WeasyPrint (PDF) + openpyxl (Excel) generation pipeline
- Test patterns in `src/tests/test_referral_reports.py`

**Established Patterns:**
- Service method returns structured dict with `data`, `summary`, `filters`, `generated_at`
- Router endpoint accepts query params: `format` (pdf/excel/json), `start_date`, `end_date`, `book_id`, `status`
- PDF templates use Jinja2 with DaisyUI/Tailwind print classes
- Landscape layout for wide tables, portrait for narrow ones
- Color-coded severity: yellow (warning), orange (caution), red (critical)
- Summary statistics section at top of every PDF
- Role-based access: Staff+ for operational reports, Officer+ for sensitive analytics

---

## Reports to Build (Week 36 — ~10 Reports)

**Theme: Registration & Book Analytics — "How is our book doing?"**

Cross-reference each report below against `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` to confirm it's listed as P1 and not yet built. If a report below doesn't appear in the inventory, skip it and substitute the next P1 report from the inventory that fits the registration/book theme.

### Report 1: Registration Activity Summary
- **What:** Aggregate registration, drop, re-sign, and dispatch-out activity by time period
- **Filters:** Date range, book_id (optional), activity_type (optional)
- **Output:** PDF + Excel
- **Access:** Staff+
- **Key columns:** Period, Registrations In, Re-Signs, Drops, Dispatched Out, Net Change
- **Summary section:** Total activity counts, busiest period, net growth/decline

### Report 2: Registration by Classification
- **What:** Breakdown of active registrations by member classification (JW, Apprentice, CE, etc.)
- **Filters:** Date (snapshot), book_id (optional)
- **Output:** PDF + Excel
- **Access:** Staff+
- **Key columns:** Classification, Book 1, Book 2, Book 3, Book 4, Total
- **Summary section:** Total by tier, dominant classification per book

### Report 3: Re-Registration Analysis
- **What:** Patterns of re-registration — short call re-registrations, 90-day cycles, voluntary re-signs
- **Filters:** Date range, book_id (optional), re_registration_reason (optional)
- **Output:** PDF + Excel
- **Access:** Staff+
- **Key columns:** Member, Book, Re-Reg Date, Reason, Previous Reg Date, Gap Days
- **Summary section:** Count by reason, avg gap between registrations, repeat re-registrants

### Report 4: Registration Duration Report
- **What:** Average time on book before dispatch or drop, by book and tier
- **Filters:** Date range, book_id (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Book, Tier, Avg Days, Median Days, Min, Max, Still Active Count
- **Summary section:** Overall avg wait time, fastest/slowest book, trend vs previous period

### Report 5: Book Health Summary
- **What:** Per-book dashboard stats — active registrants, dispatched this period, dropped, avg wait, fill rate
- **Filters:** Date range (period), book_id (optional, defaults to all books)
- **Output:** PDF
- **Access:** Officer+
- **Key columns:** Book Name, Active, Dispatched, Dropped, Re-Signed, Avg Wait Days, Fill Rate %
- **Summary section:** Healthiest book (highest fill rate), concerning books (low activity)
- **Layout:** Landscape for wide table

### Report 6: Book Comparison
- **What:** Side-by-side metrics for selected books — fill rate, avg days on book, active count, dispatch velocity
- **Filters:** Date range, book_ids (multi-select, min 2)
- **Output:** PDF
- **Access:** Officer+
- **Key columns:** Metric rows with book columns (pivoted layout)
- **Summary section:** Key differentiators, recommended attention areas

### Report 7: Book Position Report (Detailed Queue)
- **What:** Full position listing for a specific book — every active registrant with APN, reg date, tier, days waiting
- **Filters:** book_id (required), tier (optional), status (optional)
- **Output:** PDF + Excel
- **Access:** Staff+
- **Key columns:** Position #, APN (DECIMAL!), Member Name, Tier, Reg Date, Days Waiting, Re-Sign Due
- **Summary section:** Total active, by-tier counts, next re-sign deadlines approaching
- **CRITICAL:** APN must render as DECIMAL(10,2), never truncated to integer

### Report 8: Book Turnover Report
- **What:** Registrations in vs out by period per book — measures churn
- **Filters:** Date range, book_id (optional), period_granularity (weekly/monthly)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Period, Book, In (New Reg + Re-Reg), Out (Dispatched + Dropped + Expired), Net, Turnover Rate %
- **Summary section:** Highest churn book, steadiest book, trend direction

### Report 9: Check Mark Summary
- **What:** Aggregate check mark statistics by book and period
- **Filters:** Date range, book_id (optional)
- **Output:** PDF + Excel
- **Access:** Staff+
- **Key columns:** Book, Period, Check Marks Issued, Members at 1 CM, Members at 2 CM (warning), Members Rolled Off (3rd CM)
- **Summary section:** Total CMs issued, members approaching limit, rolled-off count
- **Color coding:** Yellow for 1 CM, Orange for 2 CM, Red for rolled off

### Report 10: Check Mark Trend
- **What:** Check mark issuance over time with trend line and approaching-limit warnings
- **Filters:** Date range (min 3 months), book_id (optional)
- **Output:** PDF
- **Access:** Officer+
- **Key columns:** Period, CMs Issued, Cumulative, Members at Risk (2 CMs), Rolling Avg
- **Summary section:** Trend direction (increasing/decreasing/stable), projected risk members next period

---

## Implementation Pattern (Per Report)

Follow this exact sequence for each report:

### Step 1: Service Method

Add to `src/services/referral_report_service.py`:

```python
def get_registration_activity_summary(
    self,
    db: Session,
    start_date: date | None = None,
    end_date: date | None = None,
    book_id: int | None = None,
) -> dict:
    """Registration activity summary — aggregate reg/drop/re-sign by period."""
    # Query with filters
    query = db.query(...)
    if book_id:
        query = query.filter(...)
    if start_date:
        query = query.filter(...)
    # ...
    return {
        "data": [...],
        "summary": {...},
        "filters": {"start_date": start_date, "end_date": end_date, "book_id": book_id},
        "generated_at": datetime.utcnow().isoformat(),
        "report_name": "Registration Activity Summary",
    }
```

### Step 2: Router Endpoint

Add to `src/routers/referral_reports_api.py`:

```python
@router.get("/registration-activity-summary")
def registration_activity_summary(
    format: str = Query("pdf", regex="^(pdf|excel|json)$"),
    start_date: date | None = None,
    end_date: date | None = None,
    book_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "officer", "staff"])),
):
    data = report_service.get_registration_activity_summary(db, start_date, end_date, book_id)
    if format == "json":
        return data
    elif format == "excel":
        return generate_excel_response(data, "registration_activity_summary")
    else:
        html = templates.TemplateResponse("reports/referral/registration_activity_summary.html", {...})
        return generate_pdf_response(html, "registration_activity_summary")
```

### Step 3: PDF Template

Create `src/templates/reports/referral/registration_activity_summary.html`:

Follow existing template patterns — include:
- Report title and generated timestamp
- Filter summary (date range, book filter applied)
- Summary statistics cards at top
- Main data table
- Print-friendly CSS (use existing print stylesheet)

### Step 4: Tests

Add to `src/tests/test_referral_reports.py`:

```python
class TestRegistrationActivitySummary:
    def test_service_returns_data(self, db_session, seed_registrations):
        """Service method returns expected structure."""
        result = report_service.get_registration_activity_summary(db_session)
        assert "data" in result
        assert "summary" in result
        assert "generated_at" in result

    def test_api_endpoint_returns_pdf(self, client, auth_headers_staff):
        """API endpoint returns PDF for staff user."""
        response = client.get(
            "/api/v1/reports/referral/registration-activity-summary?format=pdf",
            headers=auth_headers_staff,
        )
        assert response.status_code == 200
```

**MINIMUM 2 tests per report.** More is better if the report has complex filtering logic.

---

## Test Data Strategy

**DO NOT hardcode test data with non-unique values.** Use UUID-based or timestamp-based unique identifiers in test fixtures. This was a lesson from Bug #029 (Week 35) — collisions between test data cause flaky tests.

```python
# WRONG — will collide
member = create_member(name="Test Member")

# RIGHT — unique per test run
import uuid
member = create_member(name=f"Test Member {uuid.uuid4().hex[:8]}")
```

If the existing `conftest.py` has report-specific fixtures (like `seed_registrations`), use them. If not, create minimal fixtures that set up just enough data for the report queries to return results.

---

## Bonus Task: Unskip Week 33A API Tests

If time allows after completing the 10 reports:

```bash
# Find the skipped tests
grep -n "skip" src/tests/test_referral_reports.py
```

These 8 tests were skipped due to fixture isolation conflicts between API tests and service tests. Week 35's bug squash may have resolved the underlying issue. Try:

1. Remove the `@pytest.mark.skip` decorators
2. Run just those tests: `python -m pytest src/tests/test_referral_reports.py -k "api" -v`
3. If they pass → commit. If they fail → re-skip with updated reason string noting what still fails.

---

## Post-Session Documentation (MANDATORY)

Before ending this session, update ALL of the following:

### 1. CLAUDE.md (project root)
- Update test count (record exact number after this session)
- Update report count (14 P0 + however many P1 built this week)
- Update current sprint status

### 2. CHANGELOG.md
```markdown
## [v0.9.11-alpha] - 2026-0X-XX

### Added
- Week 36: P1 Registration & Book Analytics Reports
  - Registration Activity Summary report (PDF + Excel)
  - Registration by Classification report (PDF + Excel)
  - [... list each report built ...]
  - X new tests for P1 reports
```

### 3. docs/IP2A_MILESTONE_CHECKLIST.md
- Add Week 36 section under Phase 7 Frontend / Reports
- List each report built with Done status
- Update Quick Stats section (test count, report count)

### 4. docs/IP2A_BACKEND_ROADMAP.md
- Update Phase 7 progress section
- Update sub-phase 7f status to reflect P1 progress
- Update test count in Executive Summary

### 5. docs/README.md (Hub README)
- Update Current Status table test count
- Update report completion count if shown

### 6. Session Log
- Create `docs/reports/session-logs/2026-0X-XX-week36-p1-registration-book-reports.md`
- Include: reports built, test metrics before/after, any issues encountered

### 7. ADR Review
- If any new patterns were established for P1 reports that differ from P0 patterns, document in ADR-016 or create ADR-017
- If no new patterns → no ADR update needed

---

## Git Commit

```bash
# After all reports built and tests pass
git add -A
git commit -m "feat(reports): Week 36 — P1 registration & book analytics reports

- Added X P1 reports: [list report names]
- X new tests (total: Y passing)
- Report count: Z (14 P0 + X P1)
- All existing tests pass — no regressions
- Spoke 2: Operations"

git push origin develop
```

---

## Anti-Patterns (DO NOT)

1. **DO NOT** build P2/P3 reports — stay on P1 only
2. **DO NOT** refactor the report service architecture — extend the existing pattern
3. **DO NOT** change existing P0 report behavior
4. **DO NOT** create new models or migrations — reports query existing Phase 7 models
5. **DO NOT** add new pip dependencies — WeasyPrint + openpyxl are sufficient
6. **DO NOT** skip tests — minimum 2 per report, no exceptions
7. **DO NOT** hardcode non-unique test data — use UUID suffixes
8. **DO NOT** store APN as anything other than DECIMAL(10,2) in any report output
9. **DO NOT** forget the documentation updates — they are mandatory, not optional

---

## Scope Boundaries

**In scope:** P1 reports (registration & book analytics), tests, documentation updates
**Out of scope:** P2/P3 reports, frontend UI changes, new models, schema changes, LaborPower import

---

## Files You Will Modify/Create

**Modified:**
- `src/services/referral_report_service.py` — add ~10 new methods
- `src/routers/referral_reports_api.py` — add ~10 new endpoints
- `src/tests/test_referral_reports.py` — add ~20+ new tests
- `CLAUDE.md` — update state
- `CHANGELOG.md` — add Week 36 section
- `docs/IP2A_MILESTONE_CHECKLIST.md` — add Week 36 tasks
- `docs/IP2A_BACKEND_ROADMAP.md` — update progress
- `docs/README.md` — update stats

**Created:**
- `src/templates/reports/referral/registration_activity_summary.html`
- `src/templates/reports/referral/registration_by_classification.html`
- `src/templates/reports/referral/re_registration_analysis.html`
- `src/templates/reports/referral/registration_duration.html`
- `src/templates/reports/referral/book_health_summary.html`
- `src/templates/reports/referral/book_comparison.html`
- `src/templates/reports/referral/book_position_report.html`
- `src/templates/reports/referral/book_turnover.html`
- `src/templates/reports/referral/check_mark_summary.html`
- `src/templates/reports/referral/check_mark_trend.html`
- `docs/reports/session-logs/2026-0X-XX-week36-p1-registration-book-reports.md`

---

*Spoke 2: Operations — Week 36 Instruction Document*
*Generated: February 5, 2026*
*Hub Source: Weeks 36-38 P1 Reports Sprint*
