# Spoke 2 — Week 41 Instruction Document
# P2 Reports Batch 2: Dispatch, Employer & Enforcement Analytics

> **Hub → Spoke 2 Handoff**
> **Sprint:** Week 41
> **Phase:** 7g (P2+P3 Reports)
> **Estimated Hours:** ~8 hrs (expanded scope — 19 reports)
> **Pre-requisite:** Week 40 P2 Batch 1 complete (v0.9.14-alpha)
> **Generated:** February 6, 2026 (Merged — Hub + Spoke 2 report sets)

---

## Objective

Build the second (and final) batch of P2 reports. This sprint has **19 reports** organized into three themes:
- **Theme A:** Dispatch Operations Analytics (6 reports)
- **Theme B:** Employer Intelligence (6 reports)
- **Theme C:** Business Rule Enforcement Analytics (7 reports)

Theme C is critical — these are the reports that prove the new system tracks IBEW referral procedure compliance **better** than LaborPower. They justify the replacement.

After this sprint, all P2 reports are complete.

Follow the **exact same patterns** from Weeks 36-38 (P1) and Week 40 (P2 Batch 1). Do NOT invent new patterns.

> **⚠️ Scope Note:** 19 reports is aggressive for a single sprint. If time runs short, prioritize Theme C (enforcement analytics) — those have the highest strategic value. Themes A and B can spill into a Week 41B if needed. Flag this in the Hub Return Summary if it happens.

---

## Pre-Flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
git status  # Clean working tree

# Verify baseline (should include Week 40 tests)
pytest --tb=short -q 2>&1 | tail -5
# Expected: ~690+ passed, 16 skipped, 0 failed

# Verify Week 40 reports exist
grep -c "def generate_" src/services/referral_report_service.py
# Expected: ≥56 (44 P0/P1 + 12 P2 Batch 1)

# Verify Phase 7 enforcement tables exist
python -c "
from src.db.session import engine
from sqlalchemy import inspect
i = inspect(engine)
tables = i.get_table_names()
for t in ['check_marks', 'member_exemptions', 'bidding_infractions', 'blackout_periods', 'job_bids']:
    print(f'{t}: {\"EXISTS\" if t in tables else \"MISSING\"}')"
```

**STOP if pre-flight fails.** Do not proceed with broken baseline.

---

## Reports to Build (19)

### Theme A: Dispatch Operations Analytics (6 reports)

| # | Report Name | Description | Output | Auth | Rationale |
|---|-------------|-------------|--------|------|-----------|
| 1 | Dispatch Success Rate | Offers accepted vs declined vs expired, by book and period | PDF + Excel | Staff+ | Process optimization |
| 2 | Time-to-Fill Analysis | Days from labor request creation to dispatch completion | PDF + Excel | Staff+ | Employer SLA tracking |
| 3 | Dispatch Method Comparison | Standard queue vs by-name vs short call volume and trends | PDF + Excel | Staff+ | Rule fairness audit |
| 4 | Dispatch Geographic Distribution | Dispatches by region (Seattle/Bremerton/Pt Angeles) over time | PDF + Excel | Staff+ | Regional equity |
| 5 | Termination Reason Analysis | Dispatches ended by reason (completed, quit, discharged, laid off) | PDF + Excel | Staff+ | Retention patterns |
| 6 | Return Dispatch Report | Members dispatched to same employer more than once in 12 months | PDF + Excel | Staff+ | Pattern detection |

### Theme B: Employer Intelligence (6 reports)

| # | Report Name | Description | Output | Auth | Rationale |
|---|-------------|-------------|--------|------|-----------|
| 7 | Employer Growth/Decline Trends | Year-over-year labor request volume per employer | PDF + Excel | Officer+ | Market intelligence (sensitive) |
| 8 | Employer Workforce Size | Current active dispatches per employer with trend indicators | PDF + Excel | Staff+ | Relationship management |
| 9 | New Employer Activity | First-time employers by period with initial request patterns | PDF + Excel | Staff+ | Growth tracking |
| 10 | Contract Code Utilization | Dispatch volume by contract code (all 8 codes) | PDF + Excel | Staff+ | CBA analytics |
| 11 | Queue Velocity Report | Average days between position changes (dispatches clearing the queue) | PDF + Excel | Staff+ | Queue health metrics |
| 12 | Peak Demand Analysis | Dispatch volume by day-of-week and hour, identifying peak periods | PDF + Excel | Staff+ | Staffing optimization |

### Theme C: Business Rule Enforcement Analytics (7 reports)

These reports directly map to IBEW Local 46 Referral Procedures (Oct 2024). Each report monitors compliance with a specific rule or set of rules.

| # | Report Name | Rule(s) | Description | Output | Auth | Rationale |
|---|-------------|---------|-------------|--------|------|-----------|
| 13 | Check Mark Pattern Analysis | Rule 10 | Check marks by book, member, and period. Identifies members approaching 3rd check mark (roll-off threshold) | PDF + Excel | Staff+ | Penalty monitoring — prevents surprise roll-offs |
| 14 | Check Mark Exception Tracking | Rule 11 | Dispatches that qualified for no-check-mark exceptions (specialty, MOU, early start, under scale, employer downsize) | PDF + Excel | Staff+ | Exception audit — ensures exceptions are applied correctly |
| 15 | Internet Bidding Analytics | Rule 8 | Bid volume by time window (5:30 PM - 7:00 AM), acceptance/rejection rates, members approaching 2nd rejection (1-year privilege loss) | PDF + Excel | Staff+ | Bidding enforcement — identifies at-risk members |
| 16 | Exemption Status Report | Rule 14 | Active exemptions by type (military, union business, salting, medical, jury duty) with expiration dates | PDF + Excel | Staff+ | Exemption tracking — ensures timely removal |
| 17 | Agreement Type Performance | Rule 4 | Dispatches by agreement type (PLA/CWA/TERO/Standard) with fill rate, avg duration, check mark rate | PDF + Excel | Officer+ | Agreement effectiveness — informs CBA negotiations |
| 18 | Foreperson By-Name Analysis | Rule 13 | By-name requests by employer/foreperson, frequency, and any anti-collusion flags | PDF + Excel | Officer+ | Anti-collusion audit — highest sensitivity |
| 19 | Blackout Period Tracking | Rule 12 | Active and historical blackout periods after quit/discharge, violations (dispatches during blackout) | PDF + Excel | Officer+ | Blackout enforcement — ensures 2-week restriction is honored |

---

## Implementation Pattern (Follow Existing Exactly)

### Service Layer

Add 19 methods to existing `src/services/referral_report_service.py`:

```python
# Same pattern as all previous weeks:
async def generate_dispatch_success_rate_report(
    self, db: Session, format: str = "pdf",
    book_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> Union[bytes, StreamingResponse]:
    """Dispatch offer acceptance rates with configurable filters."""
    pass
```

### Report-Specific Implementation Notes

**Report 3 (Dispatch Method Comparison):**
- Three categories: standard queue dispatch, foreperson by-name request, short call
- Query `dispatches` table — determine method from `by_name_request` boolean and short call duration
- Show volume, percentage, and trend per method
- Fairness metric: what % of dispatches go through the queue vs by-name?

**Report 6 (Return Dispatch):**
- Query `dispatches` joined to `labor_requests` → employer
- Group by (member_id, employer_id) with COUNT > 1
- Show member name, employer, dispatch count, dates
- Flag patterns: same member → same employer 3+ times in 12 months

**Report 10 (Contract Code Utilization):**
- All **8 contract codes**: WIREPERSON, SOUND & COMM, STOCKPERSON, LT FXT MAINT, GROUP MARINE, GROUP TV & APPL, MARKET RECOVERY, RESIDENTIAL
- Join through `labor_requests` → `referral_books` → `contract_code`
- Remember: contract_code is NULLABLE (Tradeshow, TERO books have no contract)
- Handle NULL contract codes as "No Contract / Supplemental"

**Report 13 (Check Mark Pattern Analysis):**
- Query `check_marks` table grouped by book and member
- **Check marks are per area book** — a check mark on Wire Seattle does NOT affect Wire Bremerton
- Color coding: 0 marks (green), 1 mark (yellow), 2 marks (orange/warning), 3+ marks (red/rolled off)
- Summary: total marks issued by period, approaching-threshold count

**Report 14 (Check Mark Exception Tracking):**
- Query dispatches where `generates_checkmark = FALSE` (the pre-calculated boolean from Rule 11)
- Group by exception reason (specialty call, MOU, early start, under scale, employer downsize)
- Audit value: shows whether exceptions are being applied fairly across members

**Report 15 (Internet Bidding Analytics):**
- Query `job_bids` table for bids placed during the 5:30 PM - 7:00 AM window
- Track rejection count per member per 12-month rolling window
- Flag members at 1 rejection (warning) and 2 rejections (privilege revocation)
- Include `bidding_infractions` table for members who have lost privileges

**Report 17 (Agreement Type Performance):**
- Agreement type is on BOTH `referral_books` AND `labor_requests`
- Use `labor_requests.agreement_type` for dispatch-specific analysis
- Compare fill rates across PLA/CWA/TERO/Standard
- Officer+ only — informs CBA negotiation strategy

**Report 18 (Foreperson By-Name Analysis):**
- Query `dispatches` where `by_name_request = TRUE`
- Group by employer + foreperson
- Flag: same foreperson requesting same member 3+ times (collusion indicator)
- **Highest sensitivity** — Officer+ only, audit-logged with extra context

**Report 19 (Blackout Period Tracking):**
- Query `blackout_periods` table
- Show active blackouts (end_date > today) and historical
- **Violations:** Join against `dispatches` to find any dispatches to the blackout employer during the blackout window
- Violations are serious compliance failures — flag prominently

### API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/reports/referral/dispatch-success-rate` | GET | Staff+ | Accept vs decline |
| `/api/v1/reports/referral/time-to-fill` | GET | Staff+ | Request-to-dispatch days |
| `/api/v1/reports/referral/dispatch-method-comparison` | GET | Staff+ | Queue vs by-name vs short call |
| `/api/v1/reports/referral/dispatch-geographic` | GET | Staff+ | Regional distribution |
| `/api/v1/reports/referral/termination-reason-analysis` | GET | Staff+ | End-of-dispatch reasons |
| `/api/v1/reports/referral/return-dispatch` | GET | Staff+ | Repeat member-employer pairs |
| `/api/v1/reports/referral/employer-growth-trends` | GET | Officer+ | YoY employer volume |
| `/api/v1/reports/referral/employer-workforce-size` | GET | Staff+ | Active dispatches per employer |
| `/api/v1/reports/referral/new-employer-activity` | GET | Staff+ | First-time employers |
| `/api/v1/reports/referral/contract-code-utilization` | GET | Staff+ | Dispatch by CBA code |
| `/api/v1/reports/referral/queue-velocity` | GET | Staff+ | Queue movement speed |
| `/api/v1/reports/referral/peak-demand` | GET | Staff+ | Day/hour demand patterns |
| `/api/v1/reports/referral/check-mark-patterns` | GET | Staff+ | Rule 10 penalty analysis |
| `/api/v1/reports/referral/check-mark-exceptions` | GET | Staff+ | Rule 11 exception audit |
| `/api/v1/reports/referral/internet-bidding-analytics` | GET | Staff+ | Rule 8 bidding analysis |
| `/api/v1/reports/referral/exemption-status` | GET | Staff+ | Rule 14 active exemptions |
| `/api/v1/reports/referral/agreement-type-performance` | GET | Officer+ | Rule 4 CBA analytics |
| `/api/v1/reports/referral/foreperson-by-name` | GET | Officer+ | Rule 13 anti-collusion audit |
| `/api/v1/reports/referral/blackout-period-tracking` | GET | Officer+ | Rule 12 blackout enforcement |

### Tests

**Minimum 2 tests per report** (1 service + 1 API):
- **Target: 38 new tests** (19 reports × 2 tests each)
- Use UUID-based test data (BUG-029/030 lesson)
- Theme C tests should verify business rule logic (e.g., check mark count thresholds, bidding window enforcement, blackout violation detection)

---

## File Modification Plan

### Modified:
```
src/services/referral_report_service.py      # ADD 19 new methods
src/routers/referral_reports_api.py          # ADD 19 new endpoints
src/tests/test_referral_reports_p2b.py       # NEW test file (38 tests)
CLAUDE.md                                     # Version, test count, report count
CHANGELOG.md                                  # Week 41 entries
```

### Created:
```
# Theme A templates
src/templates/reports/referral/dispatch_success_rate.html
src/templates/reports/referral/time_to_fill.html
src/templates/reports/referral/dispatch_method_comparison.html
src/templates/reports/referral/dispatch_geographic.html
src/templates/reports/referral/termination_reason_analysis.html
src/templates/reports/referral/return_dispatch.html

# Theme B templates
src/templates/reports/referral/employer_growth_trends.html
src/templates/reports/referral/employer_workforce_size.html
src/templates/reports/referral/new_employer_activity.html
src/templates/reports/referral/contract_code_utilization.html
src/templates/reports/referral/queue_velocity.html
src/templates/reports/referral/peak_demand.html

# Theme C templates
src/templates/reports/referral/check_mark_patterns.html
src/templates/reports/referral/check_mark_exceptions.html
src/templates/reports/referral/internet_bidding_analytics.html
src/templates/reports/referral/exemption_status.html
src/templates/reports/referral/agreement_type_performance.html
src/templates/reports/referral/foreperson_by_name.html
src/templates/reports/referral/blackout_period_tracking.html

docs/reports/session-logs/2026-XX-XX-week41-p2-reports-batch2.md
```

---

## Priority If Time Runs Short

If the 8-hour estimate proves tight, build in this order:

1. **Theme C first** (reports 13-19) — these justify the LaborPower replacement
2. **Theme A next** (reports 1-6) — operational analytics
3. **Theme B last** (reports 7-12) — employer intelligence

If Theme B doesn't fit, it becomes **Week 41B** — note in Hub Return Summary.

---

## Anti-Patterns (DO NOT)

1. **DO NOT** build P3 reports — P2 only this sprint
2. **DO NOT** refactor the report service architecture — extend the existing pattern
3. **DO NOT** change existing P0/P1/P2 Batch 1 report behavior
4. **DO NOT** create new models or migrations — reports query existing Phase 7 models
5. **DO NOT** add new pip dependencies — WeasyPrint + openpyxl are sufficient
6. **DO NOT** skip tests — minimum 2 per report, no exceptions
7. **DO NOT** hardcode non-unique test data — use UUID suffixes
8. **DO NOT** store APN as anything other than DECIMAL(10,2)
9. **DO NOT** expose member names in Officer+-only reports to Staff role
10. **DO NOT** forget: check marks are **per area book**, not global
11. **DO NOT** forget: bidding window is **5:30 PM - 7:00 AM Pacific**
12. **DO NOT** forget: contract_code is **NULLABLE** for some books
13. **DO NOT** implement caching — clean queries now, optimize later
14. **DO NOT** forget documentation updates — they are mandatory

---

## Document Update Directive

**⚠️ MANDATORY: Update *ANY* & *ALL* relevant documents (i.e. Bug log, ADR's, anything under /app/* *AND/OR* /app/docs/*). Again as you feel is necessary.**

Specifically check and update:
- `CLAUDE.md` — version bump to v0.9.15-alpha, test count, report count (should be 75 total: 14 P0 + 30 P1 + 31 P2 after this sprint)
- `CHANGELOG.md` — Add Week 41 entries under [Unreleased]
- `docs/BUGS_LOG.md` — Log any new bugs found and fixed
- `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` — Mark ALL P2 reports as complete
- Create individual `docs/bugs/BUG-0XX-*.md` files for any bugs found
- Session log creation

### P2 Completion Verification

After this sprint, verify:
```
P2 total = 31 reports (12 Batch 1 from Week 40 + 19 Batch 2 from Week 41)
Grand total = 75 reports (14 P0 + 30 P1 + 31 P2)
Remaining = 7 P3 reports (Week 42) + any blocked reports
```

> **Note:** The original inventory had 22 P2 reports. This merged sprint builds 31 P2 reports (9 more than originally inventoried). The extras come from detailed business-rule enforcement reports that weren't individually listed in the LaborPower inventory but are necessary for compliance monitoring. Update the inventory accordingly — add new line items for the enforcement reports.

---

## End-of-Session Requirements

1. **Run full test suite:**
   ```bash
   pytest --tb=short -q 2>&1 | tail -10
   ```
   - Confirm pass rate ≥ 98% (target: maintain 100%)
   - Report: total, passed, failed, skipped

2. **Commit and push:**
   ```bash
   git add -A
   git commit -m "feat(reports): Week 41 P2 reports batch 2 — dispatch, employer & enforcement analytics (19 reports, 38 tests)

   Theme A: Dispatch operations (success rate, time-to-fill, method comparison,
   geographic distribution, termination reasons, return dispatch patterns)

   Theme B: Employer intelligence (growth trends, workforce size, new employers,
   contract code utilization, queue velocity, peak demand)

   Theme C: Business rule enforcement (check marks Rules 10/11, internet bidding
   Rule 8, exemptions Rule 14, agreement types Rule 4, foreperson by-name
   Rule 13, blackout periods Rule 12)"
   git push origin develop
   ```

3. **Session log:**
   Create `docs/reports/session-logs/2026-XX-XX-week41-p2-reports-batch2.md`

4. **Hub Return Summary:**
   ```
   === WEEK 41 HUB RETURN SUMMARY ===
   Version: v0.9.15-alpha
   Tests: XXX total (XXX passed, XX skipped, 0 failed)
   Reports built this sprint: 19 P2 (dispatch + employer + enforcement analytics)
   Reports total: 75 (14 P0 + 30 P1 + 31 P2)
   P2 tier: COMPLETE
   Phase 7g progress: P2 done, P3 next (Week 42, 7 reports)
   Theme C enforcement reports: 7 new reports covering Rules 4, 8, 10, 11, 12, 13, 14
   Files modified: [list]
   Bugs found: [list or "none"]
   Spillover: [Theme B if not completed — becomes Week 41B]
   ```

5. **Update documents per directive above**

---

## Scope Boundaries

### IN SCOPE:
- 19 P2 reports (3 themes)
- PDF + Excel output for each
- Tests for each report (38 minimum)
- Document updates per directive
- Report inventory updates (add enforcement reports as new line items)

### OUT OF SCOPE (do NOT attempt):
- P3 reports (Week 42)
- New models or schema changes
- Refactoring existing P0/P1/P2 Batch 1 reports
- Square payment integration
- Frontend page redesigns
- LaborPower data import (blocked)
- Phase 5: Access DB Migration
- Spoke 1/3 activation

---

## Session Reminders

> **Member ≠ Student.** Phase 7 models FK to `members`, NOT `students`.

> **Book ≠ Contract.** STOCKMAN book → STOCKPERSON contract. 3 books have NO contract code.

> **APN = DECIMAL(10,2).** Integer part is Excel serial date. Decimal part is secondary sort key. NEVER truncate.

> **Check marks are per area book.** Wire Seattle check marks ≠ Wire Bremerton check marks.

> **Bidding window: 5:30 PM - 7:00 AM Pacific.** Any bids outside this window are invalid.

> **8 Contract Codes:** WIREPERSON, SOUND & COMM, STOCKPERSON, LT FXT MAINT, GROUP MARINE, GROUP TV & APPL, MARKET RECOVERY, RESIDENTIAL

> **Audit.** Report generation MUST be audit-logged. Enforcement reports (Theme C) carry extra audit sensitivity.

> **Pattern First.** Follow Weeks 36-40 patterns exactly. No new patterns.

> **Test isolation.** UUID-based test data. BUG-029/030/031/032/033 lessons apply.

---

*Spoke 2 — Week 41 Instruction Document (Merged)*
*UnionCore (IP2A-Database-v2)*
*Generated: February 6, 2026 by Hub*
