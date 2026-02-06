# Claude Code Instructions: Week 38 — P1 Reports Sprint C + Test Hardening

**Source:** Spoke 2: Operations (Hub instruction doc: Weeks 36-38)
**Target:** Claude Code execution
**Project Version:** v0.9.12-alpha (post-Week 37)
**Sprint Scope:** Remaining P1 reports (~10) + test failure cleanup + full documentation sweep
**Estimated Effort:** 5-6 hours
**Branch:** `develop`
**Spoke:** Spoke 2: Operations

---

## TL;DR

This is the P1 sprint closer. Two objectives:
1. **Build remaining P1 reports** (~10) — compliance, operational, and cross-book analytics
2. **Test hardening** — fix remaining ~9 test failures, evaluate unskipping Week 33A tests, push pass rate ≥99%

After this week, all 33 P1 reports should be complete. Combined with the 14 P0 reports, that's ~47 reports covering daily and weekly operational needs.

---

## Pre-Flight (MANDATORY)

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
git log --oneline -10

# Verify Week 37 baseline
python -m pytest src/tests/ -x -q 2>&1 | tail -20

# Count current reports
grep -c "def get_" src/services/referral_report_service.py
grep -c "@router.get" src/routers/referral_reports_api.py

# Inventory check — what P1 reports remain?
cat docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md

# Find ALL current test failures
python -m pytest src/tests/ -q 2>&1 | grep -E "FAILED|ERROR"

# Find ALL skipped tests
grep -rn "@pytest.mark.skip" src/tests/ | grep -v "__pycache__"
grep -rn "pytest.skip" src/tests/ | grep -v "__pycache__"
```

**RECORD THE BASELINE:** Exact test count, pass count, fail count, skip count. This week's goal is ≥99% pass rate.

**CRITICAL:** Identify the exact remaining P1 reports by cross-referencing:
- `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` (source of truth — all 33 P1 reports)
- Reports built in Week 36 (registration/book analytics)
- Reports built in Week 37 (dispatch/employer analytics)
- Any P1 reports already built during P0 sprint

Build ONLY what's missing to complete the P1 tier.

---

## Part 1: Remaining P1 Reports (~3-4 hours, ~10 reports)

**Theme: Compliance, Operational, and Cross-Book Analytics**

These are the P1 reports that don't fit neatly into the registration or dispatch categories. Cross-reference against the inventory — build only what remains.

### Compliance & Audit Reports

#### Report: Internet Bidding Activity
- **What:** Web bid submissions, acceptances, rejections, ban tracking
- **Filters:** Date range, member_id (optional), status (accepted/rejected/pending)
- **Output:** PDF + Excel
- **Access:** Staff+
- **Key columns:** Date, Member, Labor Request, Bid Time, Status, Within Window (Y/N), Rejection Count (rolling 12mo)
- **Summary section:** Total bids, acceptance rate, members approaching 2nd rejection (1-year ban trigger)
- **Business rule:** Rule 8 — 5:30 PM to 7:00 AM window. 2nd rejection in 12 months = lose internet bidding 1 year.
- **Color coding:** Red for members at ban threshold

#### Report: Exempt Status Report
- **What:** Members currently on exempt status by type
- **Filters:** Date (snapshot, defaults to today), exempt_type (optional), book_id (optional)
- **Output:** PDF + Excel
- **Access:** Staff+
- **Key columns:** Member, Exempt Type (military/union business/salting/medical/jury duty), Start Date, Expected End Date, Days Exempt, Book(s) Affected
- **Summary section:** Count by exempt type, longest current exemptions, upcoming expirations (next 30 days)
- **Business rule:** Rule 14 — exempt members retain position but are not eligible for dispatch

#### Report: Penalty Report
- **What:** All penalty actions over period — check marks, bid rejections, quit/discharge roll-offs
- **Filters:** Date range, penalty_type (optional), book_id (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Date, Member, Penalty Type, Book, Details, Resulting Action
- **Summary section:** Total penalties by type, trend vs previous period, most penalized book
- **Color coding:** Yellow (check mark 1), Orange (check mark 2), Red (roll-off/ban)

#### Report: Foreperson By Name Audit
- **What:** By-name request tracking for anti-collusion compliance review
- **Filters:** Date range, employer_id (optional), foreperson_id (optional)
- **Output:** PDF
- **Access:** Officer+ (sensitive compliance data)
- **Key columns:** Date, Employer, Foreperson, Requested Member, Approved (Y/N), Blackout Active, Notes
- **Summary section:** By-name % of total dispatches, employers with highest by-name rates, any blackout violations
- **Business rule:** Rule 13 — anti-collusion. Rule 12 — 2-week blackout after quit/discharge.

### Operational Reports

#### Report: Queue Wait Time Report
- **What:** Average wait time by book — identifies bottlenecks and longest-waiting members
- **Filters:** Date (snapshot), book_id (optional), tier (optional)
- **Output:** PDF + Excel
- **Access:** Staff+
- **Key columns:** Book, Tier, Active Count, Avg Wait Days, Median Wait, Longest Wait Member (anonymized for Staff), 30-Day Re-Sign Due Count
- **Summary section:** Longest avg wait book, members waiting >90 days, re-sign deadlines this week

#### Report: Morning Referral History
- **What:** Historical log of morning referral processing — what was dispatched each morning
- **Filters:** Date range (defaults to last 2 weeks), book_id (optional)
- **Output:** PDF + Excel
- **Access:** Staff+
- **Key columns:** Date, Processing Time, Book, Requests Processed, Members Dispatched, Unfilled, Processing Order Slot
- **Summary section:** Avg dispatches per morning, busiest day of week, unfilled rate trend
- **Business rule:** Rule 2 — processing order: Wire 8:30 AM → S&C/Marine/Stock/LFM/Residential 9:00 AM → Tradeshow 9:30 AM

#### Report: Unfilled Request Report
- **What:** Labor requests not fully filled — aging analysis and root cause
- **Filters:** Date range, status (partially_filled/unfilled), employer_id (optional), book_id (optional)
- **Output:** PDF + Excel
- **Access:** Staff+
- **Key columns:** Request Date, Employer, Workers Requested, Workers Filled, Shortfall, Days Open, Book, Reason (if documented)
- **Summary section:** Total unfilled positions, top unfilled employers, avg age of open requests, shortfall by classification

#### Report: Referral Agent Activity
- **What:** Dispatches processed per staff member — workload distribution
- **Filters:** Date range, staff_member_id (optional)
- **Output:** PDF
- **Access:** Officer+ (performance data)
- **Key columns:** Staff Member, Dispatches Processed, Registrations Processed, Check Marks Issued, By-Name Approvals, Hours Active
- **Summary section:** Total processed by team, workload distribution equity, busiest/quietest agent

### Cross-Book Reports

#### Report: Multi-Book Members
- **What:** Members registered on multiple books simultaneously — validates cross-classification rules
- **Filters:** Date (snapshot), min_books (default 2)
- **Output:** PDF + Excel
- **Access:** Staff+
- **Key columns:** Member, Book 1 (APN, Tier, Reg Date), Book 2 (APN, Tier, Reg Date), ..., Total Books
- **Summary section:** Members on 2 books, 3 books, 4+ books, most common book combinations
- **Business rule:** Rule 5 — one registration per classification. Multiple classifications allowed simultaneously.
- **CRITICAL:** Display APN as DECIMAL(10,2) — never truncate

#### Report: Book Transfer Report
- **What:** Members who moved between books — re-registration patterns after dispatch/drop
- **Filters:** Date range, source_book (optional), destination_book (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Member, Source Book, Source Tier, Drop Date, Drop Reason, New Book, New Tier, Re-Reg Date, Gap Days
- **Summary section:** Most common transfers, avg gap between books, classification change patterns

---

## Part 2: Test Hardening (~1-2 hours)

### Priority A: Fix Remaining Test Failures

```bash
# Get exact failure list
python -m pytest src/tests/ -q 2>&1 | grep "FAILED"
```

For each failure, categorize and fix:

| Category | Action |
|----------|--------|
| **Fixture isolation** | Add proper cleanup, use function-scoped fixtures, or isolate test database sessions |
| **Schema drift** | Fix field name references to match current models |
| **Logic error** | Fix the actual code or test expectation |
| **Flaky/timing** | Add retry decorator or increase timeout — document reason |
| **Genuinely broken feature** | Fix the feature, not just the test |

**DO NOT** just skip failing tests to hit the pass rate target. Fix the root cause. If a test genuinely cannot be fixed this sprint, add `@pytest.mark.skip(reason="Week 38: <specific reason> — fix in Week 39")` with a clear reason string.

### Priority B: Evaluate Skipped Tests

```bash
grep -rn "skip" src/tests/ | grep -v "__pycache__" | grep -v "# skip"
```

For each skipped test:
1. **Read the skip reason**
2. **If the reason has been resolved** (e.g., a bug was fixed in Week 35) → remove skip, run test
3. **If still valid** (e.g., S3/MinIO not available in CI) → leave with clear reason
4. **If reason is vague** (e.g., "TODO" or "fix later") → investigate and either fix or add specific reason

### Priority C: Week 33A API Tests (8 skipped)

These were skipped due to fixture isolation conflicts between API tests and service tests:

```bash
grep -n "skip" src/tests/test_referral_reports.py
```

1. Remove `@pytest.mark.skip` decorators from these 8 tests
2. Run them in isolation: `python -m pytest src/tests/test_referral_reports.py -k "api" -v`
3. If they pass → keep them active
4. If they fail → analyze the fixture conflict:
   - Is it a shared database state issue? → Add cleanup fixture
   - Is it a mock/patch collision? → Scope the patches correctly
   - Is it a test ordering dependency? → Add explicit setup/teardown
5. If unfixable in this sprint → re-skip with updated reason: `@pytest.mark.skip(reason="Week 38: fixture isolation — API tests conflict with service tests on shared DB state. Needs dedicated test session management.")`

### Target Pass Rate

| Metric | Current (est.) | Target |
|--------|---------------|--------|
| Total tests | ~640+ | ~660+ (after new report tests) |
| Passing | ~630+ | ≥99% of total |
| Failing | ~9 | ≤3 (with documented reasons) |
| Skipped | varies | Only with specific, current reasons |

---

## Implementation Pattern (Reports)

Identical to Weeks 36-37. For each report:

1. **Service method** → `src/services/referral_report_service.py`
2. **Router endpoint** → `src/routers/referral_reports_api.py`
3. **PDF template** → `src/templates/reports/referral/<name>.html`
4. **Tests** → `src/tests/test_referral_reports.py` (min 2 per report)

No deviations from the established pattern.

---

## Post-Sprint Documentation (MANDATORY — COMPREHENSIVE)

This is the final week of the P1 sprint. Documentation must be thorough enough to mark sub-phase 7f as partially complete (P0+P1 done, P2+P3 remaining).

### 1. CLAUDE.md (project root)
- Update version to v0.9.13-alpha
- Update test count and pass rate (target ≥99%)
- Update total report count (should be ~47: 14 P0 + ~33 P1)
- Update Phase 7 status: "7f: P0+P1 reports complete, P2+P3 remaining"
- Update "Weeks 20-38 Complete" in phase description

### 2. CHANGELOG.md
```markdown
## [v0.9.13-alpha] - 2026-0X-XX

### Added
- Week 38: P1 Compliance, Operational & Cross-Book Reports
  - Internet Bidding Activity report
  - Exempt Status Report
  - Penalty Report
  - Foreperson By Name Audit
  - Queue Wait Time Report
  - Morning Referral History
  - Unfilled Request Report
  - Referral Agent Activity
  - Multi-Book Members report
  - Book Transfer Report
  - X new tests for remaining P1 reports

### Fixed
- Week 38: Test hardening
  - Fixed X failing tests (describe root causes)
  - Unskipped Y tests (describe which and why)
  - Pass rate improved from A% to B%

### Changed
- Sub-phase 7f status: P0+P1 reports complete (47 of 78 total reports)
```

### 3. docs/IP2A_MILESTONE_CHECKLIST.md
- Add Week 38 section with all report tasks
- Add test hardening tasks with results
- Update Quick Stats:
  - Total tests, pass rate
  - Reports: 47 complete (14 P0 + 33 P1), 29 remaining (22 P2 + 7 P3)
- Update sub-phase 7f status
- **Add new section:** "P1 Report Inventory — Complete" listing all 33 P1 reports with Done status

### 4. docs/IP2A_BACKEND_ROADMAP.md
- Update Executive Summary test count and report count
- Update Phase 7 progress (sub-phase 7f: P0+P1 complete)
- Update version to v0.9.13-alpha
- Update §7.8 Report Inventory Summary with completion counts:
  ```
  | P0 (Critical) | 16 | ✅ ALL | 0 |
  | P1 (High) | 33 | ✅ ALL | 0 |
  | P2 (Medium) | 22 | 0 | 22 |
  | P3 (Low) | 7 | 0 | 7 |
  ```
- Add Week 38 to version history

### 5. docs/README.md (Hub README)
- Update Current Status table
- Update version, test count, report count
- Update Phase 7 sub-phase table (7f partially complete)

### 6. docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md
- **Mark every P0 and P1 report as complete** in the inventory
- Add a "Status" column if one doesn't exist, or update existing status markers
- Note the service method name and endpoint for each completed report

### 7. ADR Review
- **If** the test hardening revealed architectural issues (e.g., fixture isolation patterns need formalization), create ADR-017: Test Architecture Patterns
- **If** compliance reports (foreperson audit, penalty report) required new access control patterns, document in ADR-016 update or new ADR
- **If** no new patterns emerged → no ADR updates needed, but document this decision in session log

### 8. Session Log
- Create `docs/reports/session-logs/2026-0X-XX-week38-p1-complete-test-hardening.md`
- Include:
  - **P1 Report Inventory:** Full list of all 33 P1 reports with endpoint paths
  - **Test metrics:** Before/after counts, pass rate, specific failures fixed
  - **Skip inventory:** All remaining skipped tests with current reasons
  - **Recommendations:** What should Week 39+ prioritize (P2 reports? More test fixes?)

### 9. Handoff Note for Hub
Generate a brief handoff note (copy/paste markdown) for the Hub project:

```markdown
## Spoke 2 → Hub: Post-Week 38 Handoff

**Version:** v0.9.13-alpha
**Date:** [date]
**Sprint:** Weeks 36-38 (P1 Reports Sprint)

### Completed
- All 33 P1 reports implemented (service + endpoint + template + tests)
- Combined with 14 P0 reports = 47 of 78 total reports complete
- Test hardening: pass rate X% (Y/Z tests)
- Sub-phase 7f status: P0+P1 COMPLETE, P2+P3 remaining (~29 reports)

### Metrics
- Total tests: X
- Passing: Y (Z%)
- Reports: 47 complete, 29 remaining
- Endpoints: ~278 (228 existing + 50 Phase 7 API + ~47 report endpoints)

### Recommendations for Next Sprint
- P2 reports (22 analytics/trend reports) — Week 39+
- P3 reports (7 advanced analytics) — Week 42+
- Consider Spoke 3 for report dashboard UI surfacing

### Cross-Cutting Notes
- [any shared file changes]
- [any patterns that affect other Spokes]
```

---

## Git Commits

```bash
# After reports are complete
git add -A
git commit -m "feat(reports): Week 38 — P1 compliance, operational & cross-book reports

- Added X remaining P1 reports completing P1 tier
- P1 report inventory: 33/33 complete
- Total reports: 47 (14 P0 + 33 P1)
- X new tests
- Spoke 2: Operations"

# After test hardening
git add -A
git commit -m "fix(tests): Week 38 — test hardening sprint

- Fixed X failing tests
- Unskipped Y previously-skipped tests
- Pass rate: Z% (A/B tests)
- Remaining skips documented with specific reasons
- Updated test skip inventory in session log"

# After documentation
git add docs/ CLAUDE.md CHANGELOG.md
git commit -m "docs: Week 38 — P1 sprint complete, comprehensive documentation update

- Updated all project docs with P1 completion status
- Report inventory marked P0+P1 complete
- Test metrics updated across all documents
- Session log with full P1 inventory and test analysis
- Hub handoff note generated"

git push origin develop
```

---

## Anti-Patterns (DO NOT)

1. **DO NOT** build P2/P3 reports — complete P1 first, then stop
2. **DO NOT** refactor report architecture mid-sprint
3. **DO NOT** skip failing tests just to hit 99% — fix root causes
4. **DO NOT** add vague skip reasons — every skip needs a specific, actionable reason
5. **DO NOT** create new models or migrations
6. **DO NOT** add new dependencies
7. **DO NOT** skip the documentation sweep — this is the sprint closer, docs must be comprehensive
8. **DO NOT** forget the Hub handoff note — the Hub needs to know P1 is done
9. **DO NOT** modify P0 or Week 36/37 reports
10. **DO NOT** expose sensitive compliance data to Staff role — check role decorators on audit/penalty reports

---

## Scope Boundaries

**In scope:**
- Remaining P1 reports (~10)
- Test failure fixes
- Unskip evaluation
- Comprehensive documentation update
- Hub handoff note

**Out of scope:**
- P2/P3 reports (Week 39+)
- Frontend UI changes
- New models or schema changes
- LaborPower import tooling
- Square payment integration
- Caching or performance optimization

---

## Files You Will Modify/Create

**Modified:**
- `src/services/referral_report_service.py` — add ~10 remaining P1 methods
- `src/routers/referral_reports_api.py` — add ~10 remaining P1 endpoints
- `src/tests/test_referral_reports.py` — add ~20+ tests + fix failures + evaluate skips
- `src/tests/` — any other test files with failures to fix
- `CLAUDE.md` — comprehensive state update
- `CHANGELOG.md` — Weeks 36-38 sections if not already added
- `docs/IP2A_MILESTONE_CHECKLIST.md` — Week 38 tasks + P1 inventory
- `docs/IP2A_BACKEND_ROADMAP.md` — phase progress + version history
- `docs/README.md` — stats update
- `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` — mark P0+P1 complete

**Created:**
- `src/templates/reports/referral/internet_bidding_activity.html`
- `src/templates/reports/referral/exempt_status.html`
- `src/templates/reports/referral/penalty_report.html`
- `src/templates/reports/referral/foreperson_by_name_audit.html`
- `src/templates/reports/referral/queue_wait_time.html`
- `src/templates/reports/referral/morning_referral_history.html`
- `src/templates/reports/referral/unfilled_requests.html`
- `src/templates/reports/referral/referral_agent_activity.html`
- `src/templates/reports/referral/multi_book_members.html`
- `src/templates/reports/referral/book_transfer.html`
- `docs/reports/session-logs/2026-0X-XX-week38-p1-complete-test-hardening.md`

**Potentially modified (test hardening):**
- Any test file with current failures — determine from pre-flight `grep FAILED` output
- Any source file where test failures reveal actual bugs

---

## Success Criteria (End of Week 38)

| Metric | Target |
|--------|--------|
| P1 reports complete | 33/33 |
| Total reports (P0+P1) | ~47 |
| Test pass rate | ≥99% |
| Remaining test failures | ≤3 (with documented reasons) |
| All skipped tests have specific reasons | Yes |
| CLAUDE.md updated | Yes |
| CHANGELOG.md updated | Yes |
| Milestone Checklist updated | Yes |
| Roadmap updated | Yes |
| Hub README updated | Yes |
| Report Inventory updated | Yes |
| Session log created | Yes |
| Hub handoff note generated | Yes |

---

*Spoke 2: Operations — Week 38 Instruction Document*
*Generated: February 5, 2026*
*Hub Source: Weeks 36-38 P1 Reports Sprint*
*This is the P1 sprint closer — documentation thoroughness is non-negotiable.*
