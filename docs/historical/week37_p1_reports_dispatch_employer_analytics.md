# Claude Code Instructions: Week 37 — P1 Reports Sprint B: Dispatch & Employer Analytics

**Source:** Spoke 2: Operations (Hub instruction doc: Weeks 36-38)
**Target:** Claude Code execution
**Project Version:** v0.9.11-alpha (post-Week 36)
**Sprint Scope:** ~10 P1 reports — Dispatch operations + employer relationship analytics
**Estimated Effort:** 5-6 hours
**Branch:** `develop`
**Spoke:** Spoke 2: Operations

---

## TL;DR

Build ~10 P1 (High priority) reports focused on dispatch operations analytics and employer relationship management. These are the "what happened and who's doing what?" reports that officers and business agents use for operational oversight. Same pattern as Week 36: service method → router endpoint → PDF/Excel template → tests.

---

## Pre-Flight (MANDATORY)

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
git log --oneline -5

# Verify Week 36 baseline — capture exact pass count
python -m pytest src/tests/ -x -q 2>&1 | tail -20

# Confirm Week 36 reports exist
grep -n "def get_" src/services/referral_report_service.py | wc -l
grep -n "def " src/routers/referral_reports_api.py | wc -l

# Read report inventory — cross-reference what's built vs remaining
cat docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md

# Check what P1 reports were built in Week 36
git log --oneline --since="2026-02-01" | head -10
```

**RECORD THE BASELINE:** Write down the exact test count and pass count from Week 36's final state. Do not proceed if regressions exist — fix Week 36 issues first.

**CRITICAL:** Identify which P1 reports remain after Week 36. The inventory file is the source of truth. Some reports listed below may have been built in Week 36 if they were dual-category — verify before building duplicates.

---

## Context from Week 36

Week 36 built ~10 P1 reports in the registration/book analytics category. The following infrastructure and patterns were established or extended:

- Service methods follow `get_<report_name>(self, db, start_date, end_date, **filters) -> dict` pattern
- Router endpoints follow `GET /api/v1/reports/referral/<report-name>?format=pdf|excel|json` pattern
- PDF templates in `src/templates/reports/referral/` with print-friendly CSS
- Test pattern: minimum 2 tests per report (service data structure + API endpoint response)
- UUID-based test data to avoid fixture collisions

**Reuse all of this. Do not reinvent.**

---

## Reports to Build (Week 37 — ~10 Reports)

**Theme: Dispatch Operations & Employer Analytics — "What happened and who's doing what?"**

Cross-reference each report below against `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` to confirm it's P1 and not yet built. Substitute from the inventory if any below are already complete.

### Report 1: Weekly Dispatch Summary
- **What:** Dispatches per week with breakdown by book and employer
- **Filters:** Date range (defaults to last 4 weeks), book_id (optional), employer_id (optional)
- **Output:** PDF + Excel
- **Access:** Staff+
- **Key columns:** Week, Book, Employer, Dispatches, Short Calls, Long Calls, Avg Duration Days
- **Summary section:** Total dispatches, busiest week, top employer by volume
- **Layout:** Landscape (wide table)

### Report 2: Monthly Dispatch Summary
- **What:** Dispatches per month with trend indicators (up/down/flat vs previous month)
- **Filters:** Date range (defaults to last 12 months), book_id (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Month, Total Dispatches, Short Calls %, By Agreement Type (PLA/CWA/Standard), Trend ↑↓→
- **Summary section:** Year-over-year comparison, peak/trough months, agreement type distribution
- **Trend indicators:** Green ↑ (>5% increase), Red ↓ (>5% decrease), Gray → (within ±5%)

### Report 3: Dispatch by Agreement Type
- **What:** Breakdown of dispatches by PLA, CWA, TERO, and standard agreement types
- **Filters:** Date range, book_id (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Agreement Type, Dispatch Count, Avg Duration, Fill Rate %, Unique Employers, Unique Members
- **Summary section:** Dominant agreement type, PLA/CWA share of total, any unfilled by type

### Report 4: Dispatch Duration Analysis
- **What:** Average dispatch length by book, employer, and classification
- **Filters:** Date range, book_id (optional), employer_id (optional), classification (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Group (Book/Employer/Classification), Avg Days, Median Days, Min, Max, Std Dev, Count
- **Summary section:** Longest avg duration employer, shortest, overall median
- **Note:** Short calls (≤10 business days) should be flagged but included in calculations

### Report 5: Short Call Analysis
- **What:** Short call frequency, average duration, re-registration patterns after short calls
- **Filters:** Date range, book_id (optional), employer_id (optional)
- **Output:** PDF + Excel
- **Access:** Staff+
- **Key columns:** Period, Short Calls, Avg Duration Days, Re-Registrations After, ≤3 Day (Long Call Rule), Max 2 Per Cycle Violations
- **Summary section:** Short call rate (% of all dispatches), employers using short calls most, members with multiple short calls
- **Business rule reminder:** ≤3 days = treated as Long Call (Rule 9). Max 2 short call dispatches per registration cycle.

### Report 6: Employer Utilization Report
- **What:** Requests vs dispatches per employer — fill rate and utilization metrics
- **Filters:** Date range, employer_id (optional), contract_code (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Employer, Requests Made, Workers Requested, Workers Dispatched, Fill Rate %, Avg Fill Time Days, Cancellations
- **Summary section:** Top 10 employers by volume, lowest fill rate employers, total unfilled positions
- **Color coding:** Green (>90% fill), Yellow (70-90%), Red (<70%)

### Report 7: Employer Request Patterns
- **What:** Frequency, average size, and seasonal trends of employer labor requests
- **Filters:** Date range (min 6 months for trend), employer_id (optional), contract_code (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Employer, Requests/Month Avg, Avg Workers/Request, Peak Month, Trough Month, Day-of-Week Distribution
- **Summary section:** Most active employers, seasonal peaks, average lead time (request to dispatch)

### Report 8: Top Employers Report
- **What:** Ranked employers by dispatch volume, request frequency, and worker retention
- **Filters:** Date range, limit (top N, default 20), sort_by (dispatches/requests/fill_rate)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Rank, Employer, Total Dispatches, Total Requests, Fill Rate %, Avg Dispatch Duration, Contract Codes
- **Summary section:** Top 5 employers = X% of all dispatches, new employers this period, dropped employers

### Report 9: Employer Compliance Report
- **What:** Foreperson-by-name requests, agreement adherence, blackout violations
- **Filters:** Date range, employer_id (optional)
- **Output:** PDF
- **Access:** Officer+ (sensitive — anti-collusion data)
- **Key columns:** Employer, By-Name Requests, By-Name %, Blackout Violations, Agreement Violations, Notes
- **Summary section:** Employers with >50% by-name rate (flag for review), any blackout violations
- **Color coding:** Red for any blackout violations, Orange for >50% by-name rate
- **Business rule reminder:** Rule 13 (Foreperson By Name anti-collusion). Rule 12 (2-week blackout after quit/discharge).

### Report 10: Member Dispatch Frequency
- **What:** Dispatch count per member over period — identifies patterns and outliers
- **Filters:** Date range, book_id (optional), min_dispatches (optional threshold)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Member, Total Dispatches, Avg Days Per Dispatch, Unique Employers, Short Call %, Last Dispatch Date
- **Summary section:** Most dispatched members, members with 0 dispatches (still on book), distribution histogram data
- **Privacy note:** Member names in Officer+ reports only. Staff sees anonymized/ID-only version.

---

## Implementation Pattern

**Identical to Week 36.** For each report:

1. **Service method** in `src/services/referral_report_service.py`
   - Query with appropriate filters
   - Return `{"data": [...], "summary": {...}, "filters": {...}, "generated_at": ..., "report_name": ...}`
   - Handle edge cases: empty results, date range validation, missing book_id

2. **Router endpoint** in `src/routers/referral_reports_api.py`
   - `GET /api/v1/reports/referral/<report-name>`
   - Query params: `format`, `start_date`, `end_date`, plus report-specific filters
   - Role decorator: `require_role(["admin", "officer"])` or `require_role(["admin", "officer", "staff"])`
   - Return PDF/Excel/JSON based on format param

3. **PDF template** in `src/templates/reports/referral/<report_name>.html`
   - Follow existing template structure (header, filters summary, stats cards, data table, footer)
   - Landscape for wide tables (>6 columns)
   - Color coding where specified above

4. **Tests** in `src/tests/test_referral_reports.py`
   - Minimum 2 per report: service data structure + API endpoint
   - Use UUID-based test data (Bug #029 lesson)
   - Use existing fixtures where available, create minimal new fixtures if needed

---

## Dispatch-Specific Query Considerations

Several Week 37 reports involve joins across the dispatch chain. The key relationships:

```
labor_requests → dispatches → book_registrations → members
labor_requests → job_bids → members
labor_requests → employers (via employer_id or organization_id)
dispatches → referral_books (via book_id on registration)
```

**Performance note:** Reports spanning large date ranges with multiple joins may be slow. For the service methods:
- Use `.options(joinedload(...))` for relationships you'll access in the template
- Add `.limit()` for member-level detail reports
- Consider caching for the monthly/yearly aggregation reports (future optimization — don't implement caching now, just structure queries cleanly)

**Agreement type filter:** When filtering by agreement type (PLA/CWA/TERO/Standard), the agreement_type lives on both `referral_books` and `labor_requests`. Use the `labor_requests.agreement_type` for dispatch reports since that's the agreement governing the specific request.

---

## Post-Session Documentation (MANDATORY)

Before ending this session, update ALL of the following:

### 1. CLAUDE.md (project root)
- Update test count
- Update report count (P0 + Week 36 P1 + Week 37 P1)
- Update current sprint status

### 2. CHANGELOG.md
```markdown
## [v0.9.12-alpha] - 2026-0X-XX

### Added
- Week 37: P1 Dispatch & Employer Analytics Reports
  - Weekly Dispatch Summary report (PDF + Excel)
  - Monthly Dispatch Summary report with trend indicators (PDF + Excel)
  - [... list each report built ...]
  - X new tests for P1 dispatch/employer reports
```

### 3. docs/IP2A_MILESTONE_CHECKLIST.md
- Add Week 37 section under Phase 7 Reports
- List each report built with Done status
- Update Quick Stats section

### 4. docs/IP2A_BACKEND_ROADMAP.md
- Update Phase 7 progress section
- Update sub-phase 7f P1 report count
- Update test count in Executive Summary

### 5. docs/README.md (Hub README)
- Update Current Status table
- Update report completion count

### 6. Session Log
- Create `docs/reports/session-logs/2026-0X-XX-week37-p1-dispatch-employer-reports.md`
- Include: reports built, test metrics before/after, query complexity notes, any issues

### 7. ADR Review
- If dispatch query patterns required new approaches not covered by ADR-016, document them
- If role-based access for sensitive employer compliance data needed new patterns, create ADR-017

---

## Git Commit

```bash
git add -A
git commit -m "feat(reports): Week 37 — P1 dispatch & employer analytics reports

- Added X P1 reports: [list report names]
- X new tests (total: Y passing)
- Report count: Z (14 P0 + A Week36 P1 + B Week37 P1)
- All existing tests pass — no regressions
- Spoke 2: Operations"

git push origin develop
```

---

## Anti-Patterns (DO NOT)

1. **DO NOT** build P2/P3 reports — P1 only
2. **DO NOT** refactor report service architecture — extend the pattern
3. **DO NOT** change existing P0 or Week 36 report behavior
4. **DO NOT** create new models or migrations — query existing Phase 7 models
5. **DO NOT** add new pip dependencies
6. **DO NOT** skip tests — minimum 2 per report
7. **DO NOT** hardcode non-unique test data — UUID suffixes always
8. **DO NOT** expose member names to Staff role in Officer+ reports — check role decorators
9. **DO NOT** implement caching — clean queries now, optimize later
10. **DO NOT** forget documentation updates

---

## Scope Boundaries

**In scope:** P1 reports (dispatch & employer analytics), tests, documentation updates
**Out of scope:** P2/P3 reports, frontend UI, new models, schema changes, caching, LaborPower import

---

## Files You Will Modify/Create

**Modified:**
- `src/services/referral_report_service.py` — add ~10 new methods
- `src/routers/referral_reports_api.py` — add ~10 new endpoints
- `src/tests/test_referral_reports.py` — add ~20+ new tests
- `CLAUDE.md` — update state
- `CHANGELOG.md` — add Week 37 section
- `docs/IP2A_MILESTONE_CHECKLIST.md` — add Week 37 tasks
- `docs/IP2A_BACKEND_ROADMAP.md` — update progress
- `docs/README.md` — update stats

**Created:**
- `src/templates/reports/referral/weekly_dispatch_summary.html`
- `src/templates/reports/referral/monthly_dispatch_summary.html`
- `src/templates/reports/referral/dispatch_by_agreement_type.html`
- `src/templates/reports/referral/dispatch_duration_analysis.html`
- `src/templates/reports/referral/short_call_analysis.html`
- `src/templates/reports/referral/employer_utilization.html`
- `src/templates/reports/referral/employer_request_patterns.html`
- `src/templates/reports/referral/top_employers.html`
- `src/templates/reports/referral/employer_compliance.html`
- `src/templates/reports/referral/member_dispatch_frequency.html`
- `docs/reports/session-logs/2026-0X-XX-week37-p1-dispatch-employer-reports.md`

---

*Spoke 2: Operations — Week 37 Instruction Document*
*Generated: February 5, 2026*
*Hub Source: Weeks 36-38 P1 Reports Sprint*
