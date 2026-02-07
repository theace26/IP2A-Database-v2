# Claude Code Instructions: Week 41 — P2 Reports Batch 2: Dispatch & Employer Analytics

**Source:** Spoke 2: Operations (Hub Handoff: Weeks 40-42)
**Target:** Claude Code execution
**Project Version at Start:** v0.9.14-alpha (post-Week 40)
**Sprint Scope:** ~12 P2 reports — Dispatch trends, employer analytics, check mark patterns, exemption analysis
**Estimated Effort:** 5 hours
**Branch:** `develop`
**Spoke:** Spoke 2: Operations

---

## TL;DR

Build the remaining ~12 P2 (Medium priority) reports focused on dispatch trend analytics, employer relationship patterns, penalty system analysis, and operational efficiency metrics. These complement Week 40's registration/book analytics — together they complete the full P2 tier.

Same pattern as always: service method → router endpoint → PDF/Excel template → tests.

---

## Pre-Flight (MANDATORY)

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
git log --oneline -5

# Verify Week 40 baseline — must be ~100% pass rate
python -m pytest src/tests/ -x -q 2>&1 | tail -20

# RECORD THE EXACT NUMBERS:
# Total: ___  Passed: ___  Skipped: ___  Failed: ___

# Confirm Week 40 reports were added
grep -n "def get_\|def generate_" src/services/referral_report_service.py | wc -l
# Expected: ~54 methods (14 P0 + 30 P1 + 10 P2 Batch 1)

# Verify P2 Batch 1 marked complete in inventory
grep -c "✅" docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md
```

**STOP IF:**
- Any non-skipped tests are failing → fix first
- Week 40 reports are missing → complete Week 40 first, do not skip ahead
- Inventory file doesn't show P2 Batch 1 as complete → reconcile first

---

## Context

- Week 40 built 10 P2 registration & book analytics reports
- Running total: 14 P0 + 30 P1 + 10 P2 = 54 reports complete
- This week finishes P2: ~12 remaining reports focused on dispatch operations and employer analytics
- After this week: 14 P0 + 30 P1 + 22 P2 = 66 reports → only P3 (7 reports) remain for Week 42

---

## Reports to Build (Week 41 — ~12 Reports)

**CRITICAL:** Cross-reference each report below against `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` to confirm it's listed as P2 and not already built. Substitute from the inventory if any below overlap with existing reports.

### Report 1: Dispatch Trend Analysis
- **What:** Monthly/quarterly dispatch volume and patterns over time
- **Filters:** Date range (min 6 months recommended), book_id (optional), contract_code (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Period, Total Dispatches, Short Calls, Long Calls, Avg Duration (days), Fill Rate %, Rejections
- **Summary section:** Dispatch volume trend (growing/declining), busiest month, year-over-year comparison
- **Analytics note:** Include period-over-period percentage change. Distinguish short call vs long call trends.

### Report 2: Dispatch Duration Distribution
- **What:** How long dispatches last — distribution and outlier identification
- **Filters:** Date range, book_id (optional), contract_code (optional), employer_id (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Duration Bucket (1-5 days, 6-10, 11-30, 31-90, 91-180, 180+), Count, %, Avg Employer Size, Most Common Contract
- **Summary section:** Median dispatch duration, % short calls (<10 days), % long-term (>90 days), outliers
- **Business rules:** Rule 9 — Short calls ≤10 business days. Max 2 per cycle. ≤3 days = treated as Long Call.

### Report 3: Dispatch Outcome Analysis
- **What:** What happens after dispatch — completion, quit, discharge, layoff breakdown
- **Filters:** Date range, book_id (optional), employer_id (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Outcome, Count, % of Total, Avg Duration, Most Common Employer, Re-Registration Rate
- **Summary section:** Completion rate, quit rate, discharge rate, layoff rate, re-registration speed by outcome
- **Business rules:** Rule 12 — Quit/discharge = rolled off ALL books + 2-week foreperson blackout

### Report 4: Internet Bidding Analytics
- **What:** Web bidding activity — volume, acceptance rates, infraction tracking
- **Filters:** Date range, book_id (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Period, Bids Placed, Bids Accepted, Bids Rejected, Rejection Rate %, Infractions Issued, Privileges Suspended
- **Summary section:** Total bid volume trend, acceptance rate, members with 2+ rejections (at risk of 1-year suspension)
- **Business rules:** Rule 8 — Bidding window 5:30 PM – 7:00 AM. 2nd rejection in 12 months = lose privileges 1 year.

### Report 5: Employer Dispatch History
- **What:** Per-employer dispatch history with workforce stability metrics
- **Filters:** Date range, employer_id (required OR top_n), contract_code (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Employer, Total Dispatches, Unique Workers, Avg Duration, Return Rate %, Quit Rate %, Contract Codes Active
- **Summary section:** Most stable employers (high return rate), most volatile (high turnover), employers with declining requests
- **Note:** "Return Rate" = % of workers dispatched to same employer more than once in period

### Report 6: Employer Contract Code Analysis
- **What:** Which contract codes employers use, multi-code employer identification
- **Filters:** contract_code (optional), min_dispatches (optional threshold)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Employer, Contract Codes (list), Primary Code (by volume), Total Dispatches per Code, Workers per Code
- **Summary section:** Multi-code employers count, RESIDENTIAL + WIREPERSON overlap analysis, contract code distribution
- **Business context:** 80% of RESIDENTIAL employers also have WIREPERSON contracts. 52 are residential-only.

### Report 7: Check Mark Pattern Analysis
- **What:** Check mark accumulation trends — who's getting them, why, and how often
- **Filters:** Date range, book_id (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Period, Check Marks Issued, Unique Members Affected, Avg per Member, Roll-Offs (3rd check), Most Common Reason
- **Summary section:** Check mark rate trend, books with highest check mark rates, members approaching 3rd mark
- **Business rules:** Rule 10 — 2 allowed per area book. 3rd = rolled off that book. Separate per area book.
- **Color coding:** Yellow (1 check), Orange (2 checks — at risk), Red (3rd — rolled off)

### Report 8: Check Mark Exception Tracking
- **What:** No-check-mark exceptions granted — volume, types, and fairness analysis
- **Filters:** Date range, exemption_type (optional), book_id (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Exception Type, Count, % of Total Dispatches, Members Benefiting, Books Affected
- **Summary section:** Most common exception type, exception-to-check-mark ratio, members with most exceptions
- **Business rules:** Rule 11 — Specialty calls, MOU, early start, under scale, employer downsize exempt from check marks

### Report 9: Exemption Status Report
- **What:** Active exemptions — military, union business, salting, medical, jury duty
- **Filters:** as_of_date (optional), exemption_type (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Member (anonymized for Staff), Exemption Type, Start Date, End Date (if applicable), Duration, Books Affected, Approved By
- **Summary section:** Active exemptions by type, avg duration by type, expiring within 30 days
- **Business rules:** Rule 14 — Exempt members keep book position without re-sign requirement

### Report 10: Agreement Type Performance
- **What:** PLA/CWA/TERO vs Standard agreement dispatch comparison
- **Filters:** Date range, agreement_type (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Agreement Type, Total Dispatches, Avg Duration, Avg Workers/Request, Fill Rate %, Check Mark Rate
- **Summary section:** Volume by agreement type, which agreements generate fewer check marks, performance comparison
- **Business rules:** Rule 4 — PLA/CWA/TERO follow their own referral terms

### Report 11: Foreperson By-Name Request Analysis
- **What:** By-name request patterns — frequency, employers, anti-collusion monitoring
- **Filters:** Date range, employer_id (optional)
- **Output:** PDF
- **Access:** Officer+ (sensitive — anti-collusion data)
- **Key columns:** Employer, By-Name Requests, Total Requests, By-Name %, Unique Members Named, Repeat Names (same member >1x)
- **Summary section:** Employers with highest by-name rates, members most frequently named, potential collusion flags (>70% by-name rate)
- **Business rules:** Rule 13 — Anti-collusion. Foreperson requesting specific members subject to procedures and blackout.
- **Color coding:** Red for >70% by-name rate (flag for review), Orange for >50%

### Report 12: Blackout Period Tracking
- **What:** Active and historical blackout periods after quit/discharge events
- **Filters:** Date range, employer_id (optional), status (active/expired/all)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Employer, Foreperson, Trigger Event (quit/discharge), Start Date, End Date, Status, Violations (dispatches during blackout)
- **Summary section:** Active blackouts count, expired this period, any violations detected
- **Business rules:** Rule 12 — 2-week foreperson blackout after quit/discharge. Violations = audit flag.
- **Color coding:** Red for any violations

---

## Implementation Pattern

**Identical to Weeks 36-40.** For each report:

1. **Service method** in `src/services/referral_report_service.py`
   - Signature: `def get_<report_name>(self, db, start_date=None, end_date=None, **filters) -> dict`
   - Returns: `{"data": [...], "summary": {...}, "filters": {...}, "generated_at": datetime, "report_name": str}`
   - Empty data → valid structure with empty list and zero-value summary, NOT an error

2. **Router endpoint** in `src/routers/referral_reports_api.py`
   - URL: `GET /api/v1/reports/referral/<report-name>`
   - Query params: `format` (pdf/excel/json), `start_date`, `end_date`, plus report-specific filters
   - Role decorator: `require_role(["admin", "officer"])` — P2 analytics are leadership-grade
   - Exception: Report 9 (Exemption Status) could be Staff+ if exemptions aren't considered sensitive

3. **PDF template** in `src/templates/reports/referral/<report_name>.html`
   - Existing structure: header → filters summary → stats cards → data table → footer
   - Landscape for tables with >6 columns
   - Color coding per report specs above

4. **Tests** in `src/tests/test_referral_reports.py`
   - Minimum 2 per report: service data structure + API endpoint
   - UUID-based test data (BUG-030)
   - `async_client_with_db` for API tests (BUG-032)
   - Real DB commit for frontend tests (BUG-033)
   - Cleanup BEFORE and AFTER (BUG-030)
   - `user.has_role()` not `user.role` (BUG-031)

---

## Query Considerations for Dispatch Analytics

Several Week 41 reports involve complex joins across the dispatch chain:

```
labor_requests → dispatches → book_registrations → members
labor_requests → job_bids → members
labor_requests → employers (via employer_id or organization_id)
dispatches → referral_books (via book_id on registration)
check_marks → book_registrations → referral_books
member_exemptions → members
```

- **Agreement type filter:** Use `labor_requests.agreement_type` for dispatch reports (the agreement governing the specific request)
- **Check mark queries:** Join through `book_registrations` to get the book context. Check marks are PER AREA BOOK, not per member globally.
- **By-name analysis:** The `by_name_request` flag lives on the dispatch/labor_request. Join to employer for aggregation.
- **Blackout periods:** Query `blackout_periods` table. Cross-reference dispatches within blackout windows for violation detection.
- **Performance:** Reports 5 and 6 may involve heavy employer joins. Use `.options(joinedload(...))` for accessed relationships. Consider `.limit()` for top-N style reports.

---

## Anti-Patterns — DO NOT

1. **DO NOT** build P3 reports — P2 only this week (P3 is Week 42)
2. **DO NOT** refactor report service architecture — extend the pattern
3. **DO NOT** change existing P0/P1/P2-Batch-1 report behavior
4. **DO NOT** create new models or migrations
5. **DO NOT** add new pip dependencies
6. **DO NOT** skip tests — minimum 2 per report
7. **DO NOT** hardcode non-unique test data — UUID suffixes always
8. **DO NOT** expose member names to Staff role in Officer+ reports
9. **DO NOT** implement caching or Chart.js
10. **DO NOT** forget documentation updates
11. **DO NOT** store or display APN as INTEGER — always DECIMAL(10,2)
12. **DO NOT** conflate check marks across books — they are PER AREA BOOK

---

## Scope Boundaries

**In scope:** P2 reports (dispatch & employer analytics), tests, documentation
**Out of scope:** P3 reports (Week 42), frontend UI, new models, schema changes, import tooling, Chart.js, caching

---

## Files You Will Modify/Create

**Modified:**
- `src/services/referral_report_service.py` — add ~12 new service methods
- `src/routers/referral_reports_api.py` — add ~12 new endpoints
- `src/tests/test_referral_reports.py` — add ~24+ new tests
- `CLAUDE.md` — version bump to v0.9.15-alpha, update test count, update report count
- `CHANGELOG.md` — add Week 41 section
- `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` — mark P2 Batch 2 reports as complete

**Created:**
- `src/templates/reports/referral/dispatch_trend_analysis.html`
- `src/templates/reports/referral/dispatch_duration_distribution.html`
- `src/templates/reports/referral/dispatch_outcome_analysis.html`
- `src/templates/reports/referral/internet_bidding_analytics.html`
- `src/templates/reports/referral/employer_dispatch_history.html`
- `src/templates/reports/referral/employer_contract_code_analysis.html`
- `src/templates/reports/referral/check_mark_patterns.html`
- `src/templates/reports/referral/check_mark_exceptions.html`
- `src/templates/reports/referral/exemption_status.html`
- `src/templates/reports/referral/agreement_type_performance.html`
- `src/templates/reports/referral/foreperson_by_name_analysis.html`
- `src/templates/reports/referral/blackout_period_tracking.html`
- `docs/reports/session-logs/2026-XX-XX-week41-p2-dispatch-employer-analytics.md`

---

## Post-Session Documentation (MANDATORY)

> ⚠️ **Update *ANY* & *ALL* relevant documents (i.e. Bug log, ADR's, anything under /app/* *AND/OR* /app/docs/*). Again as you feel is necessary.**

### 1. CLAUDE.md (project root)
- Update version to v0.9.15-alpha
- Update test count (should be ~724+)
- Update report count: "66 of ~78 (14 P0 + 30 P1 + 22 P2)"
- Update Phase 7 status: "7g: P2 complete, P3 remaining (Week 42)"

### 2. CHANGELOG.md
```markdown
## [v0.9.15-alpha] - 2026-XX-XX
### Added
- 12 P2 dispatch & employer analytics reports (dispatch trends, duration distribution, outcome analysis, internet bidding, employer dispatch history, contract code analysis, check mark patterns, check mark exceptions, exemption status, agreement type performance, foreperson by-name analysis, blackout tracking)
- ~24 new tests for P2 Batch 2 reports
### Changed
- Updated report count: 66 of ~78 (14 P0 + 30 P1 + 22 P2)
- P2 tier complete
```

### 3. docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md
- Mark each P2 Batch 2 report as "✅ Complete"
- P2 section should now be fully checked off

### 4. Session Log
Create `docs/reports/session-logs/2026-XX-XX-week41-p2-dispatch-employer-analytics.md`

### 5. Bug Documentation (IF APPLICABLE)
- Bugs → `docs/BUGS_LOG.md` + individual `docs/bugs/BUG-0XX-*.md`
- No bugs → note in session log

### 6. Any Other /docs/* Files
- Scan for anything affected by this session's work

---

## Hub Return Summary

```
=== WEEK 41 HUB RETURN SUMMARY ===
Version: v0.9.15-alpha
Tests: XXX total (XXX passed, 16 skipped, 0 failed)
Reports: 66 of ~78 (14 P0 + 30 P1 + 22 P2 + 0 P3)
Phase 7g: IN PROGRESS (P2 complete, P3 remaining)
Bugs Found: [list or "none"]
Files Modified: [list]
Hub Escalations: [list or "none"]
```

---

## Session Reminders

> **Member ≠ Student.** Phase 7 models FK to `members`, NOT `students`.

> **Book ≠ Contract.** Mapping is NOT 1:1. 3 books have NO contract code.

> **APN = DECIMAL(10,2).** NEVER truncate to INTEGER.

> **Check marks are PER AREA BOOK.** Wire Seattle check marks don't affect Wire Bremerton. Do NOT aggregate across books without making this explicit.

> **Audit.** Report generation MUST be audit-logged.

> **8 Contract Codes:** WIREPERSON, SOUND & COMM, STOCKPERSON, LT FXT MAINT, GROUP MARINE, GROUP TV & APPL, MARKET RECOVERY, RESIDENTIAL

> **User.has_role()** — NOT `user.role`.

> **Fixture Isolation.** BUG-030 through BUG-033 patterns for ALL new tests.

> **Empty Data.** Handle gracefully — "Insufficient data" messages, not errors.

---

## Commit

```bash
git add -A
git commit -m "feat(reports): P2 Batch 2 — 12 dispatch & employer analytics reports (Week 41)

- Dispatch trends, duration distribution, outcome analysis
- Internet bidding analytics, employer dispatch history
- Contract code analysis, check mark patterns & exceptions
- Exemption status, agreement type performance
- Foreperson by-name analysis, blackout period tracking
- ~24 new tests, all passing
- P2 tier complete (22 reports)
- Version bump: v0.9.15-alpha
- Reports: 66 of ~78 (14 P0 + 30 P1 + 22 P2)"

git push origin develop
```

---

*Spoke 2: Operations — Week 41 Instruction Document*
*Generated: February 6, 2026*
*Hub Source: Hub → Spoke 2 Handoff: Weeks 40-42*
