# Claude Code Instructions: Week 40 — P2 Reports Batch 1: Registration & Book Analytics

**Source:** Spoke 2: Operations (Hub Handoff: Weeks 40-42)
**Target:** Claude Code execution
**Project Version at Start:** v0.9.13-alpha
**Sprint Scope:** ~10 P2 reports — Registration trends, book analytics, member movement patterns
**Estimated Effort:** 5 hours
**Branch:** `develop`
**Spoke:** Spoke 2: Operations

---

## TL;DR

Build ~10 P2 (Medium priority) reports focused on registration trends, book health analytics, and member movement patterns over time. These are the "how are things trending?" reports used by officers and leadership for strategic decision-making — NOT daily operational use (that's P0/P1).

P2 reports are analytics-grade. They aggregate larger date ranges, compare periods, and surface trends. They are NOT time-critical like P0 dispatch logs. They follow the exact same implementation pattern as Weeks 36-38 P1 reports: service method → router endpoint → PDF/Excel template → tests.

---

## Pre-Flight (MANDATORY)

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
git log --oneline -5

# Verify Week 39 baseline — must be ~100% pass rate
python -m pytest src/tests/ -x -q 2>&1 | tail -20

# RECORD THE EXACT NUMBERS:
# Total: ___  Passed: ___  Skipped: ___  Failed: ___

# Confirm existing report count
grep -n "def get_\|def generate_" src/services/referral_report_service.py | wc -l
grep -n "@router" src/routers/referral_reports_api.py | wc -l

# Read report inventory — identify P2 reports
cat docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md

# Check existing P0+P1 reports to avoid duplication
grep -n "def get_\|def generate_" src/services/referral_report_service.py
```

**STOP IF:**
- Any non-skipped tests are failing → fix first, do not proceed
- Pass rate is below 98% → stabilize before adding new code
- Report inventory file is missing → escalate to Hub

**RECORD THE BASELINE.** Write down total tests, passing, skipped, and exact report method count. You'll need these for the Hub Return Summary.

---

## Context

- Weeks 36-38 built 30 P1 reports (service methods + API endpoints + templates + tests)
- Week 39 fixed 18 test failures across 4 bug categories (BUG-030 through BUG-033)
- Test suite is at ~100% non-skipped pass rate with 682 total tests (666 passing, 16 skipped infra-only)
- 14 P0 + 30 P1 = 44 reports complete
- P2 target: 22 reports across Weeks 40-41 (~10 this week, ~12 next week)

**This week's theme:** Registration & Book Analytics — trend analysis, movement patterns, historical comparisons. These reports answer questions like "How has Book 1 changed over the past year?" and "What's the re-registration trend by quarter?"

---

## Reports to Build (Week 40 — ~10 Reports)

**CRITICAL:** Cross-reference each report below against `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` to confirm it's listed as P2 and not already built. If any report below overlaps with an existing P0/P1 report, skip it and substitute the next unbuilt P2 report from the inventory that fits the registration/book theme.

### Report 1: Registration Trend Analysis
- **What:** Monthly/quarterly registration volume over time with trend line data
- **Filters:** Date range (min 6 months recommended), book_id (optional), classification (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Period, New Registrations, Re-Registrations, Drops, Net Change, Cumulative Active
- **Summary section:** Growth/decline rate, busiest/slowest months, year-over-year comparison if data allows
- **Analytics note:** Include period-over-period percentage change column

### Report 2: Book Composition Analysis
- **What:** Demographics and classification breakdown of current book membership — who's on the books right now
- **Filters:** book_id (optional — all books if omitted), as_of_date (optional, defaults to today)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Book, Total Registrants, By Tier (B1/B2/B3/B4), Classification Mix, Avg Time on Book (days), Median APN Age
- **Summary section:** Largest book, most concentrated tier, books with inverted distributions (B3 > B1)
- **Business context:** Inverted distributions (STOCKMAN B3 = 8.6× B1, TECHNICIAN B3 > B1) suggest heavy traveler presence

### Report 3: Book Velocity Report
- **What:** How fast members move through books — average time from registration to dispatch or drop
- **Filters:** Date range, book_id (optional), tier (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Book, Tier, Avg Days to Dispatch, Median Days, Avg Days to Drop, Still Active %, Fastest (days), Slowest (days)
- **Summary section:** Fastest-moving book, slowest, tier comparison
- **Note:** This is a key strategic indicator — fast books mean healthy demand, slow books mean surplus labor

### Report 4: Re-Registration Pattern Analysis
- **What:** Why and how often members re-register — trigger analysis
- **Filters:** Date range, book_id (optional), re_registration_reason (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Reason, Count, % of Total, Avg Days Before Re-Reg, Repeat Offenders (>2 re-regs in period)
- **Summary section:** Most common trigger, short call vs quit/discharge ratio, members with 3+ re-registrations
- **Business rules:** Rule 6 defines triggers — Short Call termination, Under Scale, 90-Day Rule, Turnarounds

### Report 5: 30-Day Re-Sign Compliance Report
- **What:** Re-sign compliance rates — who's re-signing on time vs late vs dropping
- **Filters:** Date range, book_id (optional)
- **Output:** PDF + Excel
- **Access:** Staff+
- **Key columns:** Book, Total Due, On-Time Re-Signs, Late Re-Signs, Drops (failed re-sign), Compliance Rate %
- **Summary section:** Overall compliance rate, worst-performing book, trend (improving or declining)
- **Business rules:** Rule 7 — must re-sign every 30 days. Miss it = dropped from books.
- **Color coding:** Green (>90% compliance), Yellow (80-90%), Red (<80%)

### Report 6: Cross-Book Registration Analysis
- **What:** Members registered on multiple books simultaneously — overlap analysis
- **Filters:** as_of_date (optional), classification (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Member (anonymized for Staff), Books Registered, Classifications, Primary Book (lowest APN), Days Since Registration
- **Summary section:** % of members on multiple books, most common book combinations, avg books per member
- **Business context:** 87% of Wire Book 1 members are on ALL THREE regional books. Cross-classification (Wire + Technician) = 88 members.

### Report 7: APN Distribution Analysis
- **What:** Statistical analysis of APN values — age of registrations, distribution shape, outliers
- **Filters:** book_id (required), tier (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Percentile (10th/25th/50th/75th/90th), APN Value, Estimated Registration Date, Days Since Registration
- **Summary section:** Median APN age, newest vs oldest registration, APN gap analysis (clusters vs even distribution)
- **CRITICAL:** APN = DECIMAL(10,2). Integer part = Excel serial date. Report must display both the raw APN and the decoded registration date.

### Report 8: Book Tier Migration Report
- **What:** Track members moving between tiers (Book 1 → Book 2, etc.) over time
- **Filters:** Date range, book_id (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** From Tier, To Tier, Count, Direction (promotion/demotion), Avg Days at Prior Tier
- **Summary section:** Most common migration path, net tier movement, members who've been through 3+ tiers
- **Note:** Tier migration data may be sparse if the system hasn't been running long. If < 5 records exist, report should say "Insufficient data for trend analysis" rather than erroring.

### Report 9: Registration Aging Report
- **What:** How long current registrants have been on the book — aging buckets
- **Filters:** book_id (optional), tier (optional)
- **Output:** PDF + Excel
- **Access:** Staff+
- **Key columns:** Aging Bucket (0-30 days, 31-60, 61-90, 91-180, 181-365, 365+), Count, % of Total
- **Summary section:** Average age, median age, oldest registration, % in each bucket
- **Color coding:** Green (0-90 days), Yellow (91-180), Orange (181-365), Red (365+)

### Report 10: Seasonal Registration Patterns
- **What:** Month-by-month registration patterns — when do members register vs dispatch
- **Filters:** Date range (min 12 months recommended), book_id (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Month, Registrations, Dispatches, Net Change, Registration-to-Dispatch Ratio
- **Summary section:** Peak registration months, peak dispatch months, seasonal lag patterns
- **Analytics note:** Construction industry has strong seasonality (spring ramp-up, winter slowdown). This report helps predict staffing needs.

---

## Implementation Pattern

**Identical to Weeks 36-38.** For each report:

1. **Service method** in `src/services/referral_report_service.py`
   - Signature: `def get_<report_name>(self, db, start_date=None, end_date=None, **filters) -> dict`
   - Returns: `{"data": [...], "summary": {...}, "filters": {...}, "generated_at": datetime, "report_name": str}`
   - Handle edge cases: empty results → return valid structure with empty data list and zero-value summary, NOT an error
   - Date range validation: if start > end, swap them. If no dates, default to last 12 months for trend reports.

2. **Router endpoint** in `src/routers/referral_reports_api.py`
   - URL: `GET /api/v1/reports/referral/<report-name>`
   - Query params: `format` (pdf/excel/json), `start_date`, `end_date`, plus report-specific filters
   - Role decorator: `require_role(["admin", "officer"])` for most P2 reports (analytics are leadership-grade)
   - Return: PDF/Excel/JSON based on format param

3. **PDF template** in `src/templates/reports/referral/<report_name>.html`
   - Follow existing template structure: header → filters summary → stats cards → data table → footer
   - Landscape layout for tables with >6 columns
   - Color coding per report specs above
   - Print-friendly CSS (no background colors that waste ink, borders for readability)

4. **Tests** in `src/tests/test_referral_reports.py`
   - Minimum 2 per report: service data structure test + API endpoint response test
   - Use UUID-based test data to avoid fixture collisions (lesson from BUG-030)
   - For API tests needing fixtures → use `async_client_with_db` pattern (BUG-032)
   - For frontend tests with TestClient → fixtures must commit to real DB (BUG-033)
   - Cleanup fixtures: run BEFORE and AFTER each test (BUG-030)
   - User model: use `user.has_role("admin")`, NOT `user.role == "admin"` (BUG-031)

---

## Query Considerations for P2 Analytics

P2 reports operate on larger date ranges and more complex aggregations than P1. Keep these in mind:

- **Trend reports** (Reports 1, 5, 10): Group by month/quarter using `func.date_trunc('month', column)`. Return chronologically sorted.
- **Distribution reports** (Reports 2, 7, 9): Use SQL `PERCENTILE_CONT` or Python percentile calculation on fetched data. PostgreSQL supports `percentile_cont(0.5) WITHIN GROUP (ORDER BY col)`.
- **Cross-reference reports** (Reports 6, 8): Join across `book_registrations`, `referral_books`, and `registration_activities`. Use `joinedload()` for relationships accessed in templates.
- **Aging calculations** use `func.now() - column` for PostgreSQL interval math, or compute in Python after query.
- **Empty data handling:** Analytics reports on new systems will often have sparse data. Every report must gracefully handle < 5 records, returning "Insufficient data" messages rather than division-by-zero or empty charts.

---

## Anti-Patterns — DO NOT

1. **DO NOT** build P3 reports — P2 only this week
2. **DO NOT** refactor the report service architecture — extend the existing pattern
3. **DO NOT** change existing P0 or P1 report behavior
4. **DO NOT** create new models or migrations — reports query existing Phase 7 models
5. **DO NOT** add new pip dependencies
6. **DO NOT** skip tests — minimum 2 per report, no exceptions
7. **DO NOT** hardcode non-unique test data — UUID suffixes always (BUG-030)
8. **DO NOT** expose member names to Staff role in Officer+ reports
9. **DO NOT** implement caching or Chart.js yet — clean queries only, visualization comes in P3/future
10. **DO NOT** forget documentation updates — they are mandatory
11. **DO NOT** store or display APN as INTEGER anywhere — always DECIMAL(10,2)

---

## Scope Boundaries

**In scope:** P2 reports (registration & book analytics), tests, documentation updates
**Out of scope:** P3 reports (Week 42), frontend UI changes, new models, schema changes, LaborPower import, Chart.js, caching

---

## Files You Will Modify/Create

**Modified:**
- `src/services/referral_report_service.py` — add ~10 new service methods
- `src/routers/referral_reports_api.py` — add ~10 new endpoints
- `src/tests/test_referral_reports.py` — add ~20+ new tests
- `CLAUDE.md` — version bump to v0.9.14-alpha, update test count, update report count
- `CHANGELOG.md` — add Week 40 section
- `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` — mark P2 Batch 1 reports as complete

**Created:**
- `src/templates/reports/referral/registration_trend_analysis.html`
- `src/templates/reports/referral/book_composition_analysis.html`
- `src/templates/reports/referral/book_velocity.html`
- `src/templates/reports/referral/re_registration_patterns.html`
- `src/templates/reports/referral/re_sign_compliance.html`
- `src/templates/reports/referral/cross_book_registration.html`
- `src/templates/reports/referral/apn_distribution.html`
- `src/templates/reports/referral/book_tier_migration.html`
- `src/templates/reports/referral/registration_aging.html`
- `src/templates/reports/referral/seasonal_registration_patterns.html`
- `docs/reports/session-logs/2026-XX-XX-week40-p2-registration-book-analytics.md`

---

## Post-Session Documentation (MANDATORY)

> ⚠️ **Update *ANY* & *ALL* relevant documents (i.e. Bug log, ADR's, anything under /app/* *AND/OR* /app/docs/*). Again as you feel is necessary.**

Specifically — before ending this session, update ALL of the following:

### 1. CLAUDE.md (project root)
- Update version to v0.9.14-alpha
- Update test count (should be ~700+)
- Update report count: "54 of ~78 (14 P0 + 30 P1 + 10 P2)"
- Update Phase 7 status: "7g: P2 Batch 1 complete"

### 2. CHANGELOG.md
Add entry:
```markdown
## [v0.9.14-alpha] - 2026-XX-XX
### Added
- 10 P2 registration & book analytics reports (registration trends, book composition, velocity, re-registration patterns, re-sign compliance, cross-book analysis, APN distribution, tier migration, aging, seasonal patterns)
- ~20 new tests for P2 Batch 1 reports
### Changed
- Updated report count: 54 of ~78 (14 P0 + 30 P1 + 10 P2)
```

### 3. docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md
- Mark each P2 Batch 1 report as "✅ Complete" with the week number

### 4. Session Log
Create `docs/reports/session-logs/2026-XX-XX-week40-p2-registration-book-analytics.md` with:
- Reports built (list with endpoint URLs)
- Test count delta
- Any issues encountered
- Files modified

### 5. Bug Documentation (IF APPLICABLE)
- If any bugs found: add to `docs/BUGS_LOG.md` AND create individual `docs/bugs/BUG-0XX-*.md`
- If no bugs: note "No new bugs" in session log

### 6. Any Other /docs/* Files
- Scan `docs/` for anything else that needs updating based on work done this session
- ADRs — update if any architectural decisions were made or patterns changed

---

## Hub Return Summary (Paste Back to Hub After Session)

```
=== WEEK 40 HUB RETURN SUMMARY ===
Version: v0.9.14-alpha
Tests: XXX total (XXX passed, 16 skipped, 0 failed)
Reports: 54 of ~78 (14 P0 + 30 P1 + 10 P2 + 0 P3)
Phase 7g: IN PROGRESS (P2 Batch 1 complete)
Bugs Found: [list or "none"]
Files Modified: [list]
Hub Escalations: [list or "none"]
```

---

## Session Reminders

> **Member ≠ Student.** Phase 7 models FK to `members`, NOT `students`.

> **Book ≠ Contract.** Books are out-of-work registration lists. Contracts are CBAs. Mapping is NOT 1:1. 3 books have NO contract code.

> **APN = DECIMAL(10,2).** Integer part is Excel serial date. Decimal part is secondary sort key. NEVER truncate to INTEGER. Reports must display the decoded registration date alongside the raw APN value.

> **Audit.** Report generation MUST be audit-logged.

> **8 Contract Codes:** WIREPERSON, SOUND & COMM, STOCKPERSON, LT FXT MAINT, GROUP MARINE, GROUP TV & APPL, MARKET RECOVERY, RESIDENTIAL

> **User.has_role()** — NOT `user.role`. The User model supports multiple roles via UserRole junction table.

> **Fixture Isolation.** Follow BUG-030 through BUG-033 patterns for ALL new tests.

> **Empty Data.** P2 analytics on a new system WILL have sparse data. Handle gracefully — "Insufficient data" messages, not errors.

---

## Commit

```bash
# After all reports built and tests passing
git add -A
git commit -m "feat(reports): P2 Batch 1 — 10 registration & book analytics reports (Week 40)

- Registration trend analysis, book composition, book velocity
- Re-registration patterns, 30-day re-sign compliance
- Cross-book registration, APN distribution analysis
- Book tier migration, registration aging, seasonal patterns
- ~20 new tests, all passing
- Version bump: v0.9.14-alpha
- Reports: 54 of ~78 (14 P0 + 30 P1 + 10 P2)"

git push origin develop
```

---

*Spoke 2: Operations — Week 40 Instruction Document*
*Generated: February 6, 2026*
*Hub Source: Hub → Spoke 2 Handoff: Weeks 40-42*
