# Spoke 2 — Week 40 Instruction Document
# P2 Reports Batch 1: Registration & Book Analytics

> **Hub → Spoke 2 Handoff**
> **Sprint:** Week 40
> **Phase:** 7g (P2+P3 Reports)
> **Estimated Hours:** ~6 hrs
> **Pre-requisite:** Week 39 Bug Squash complete (v0.9.13-alpha, ~100% pass rate)
> **Generated:** February 6, 2026 (Merged — Hub + Spoke 2 report sets)

---

## Objective

Build 12 P2 (Medium priority) reports covering registration analytics and book utilization. These are operational analytics reports — not daily-use like P0/P1, but valuable for monthly reviews, board meetings, trend analysis, and IBEW referral procedure compliance monitoring.

Follow the **exact same patterns** established in Weeks 36-38 P1 report implementation. Do NOT invent new patterns.

---

## Pre-Flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
git status  # Clean working tree

# Verify baseline
pytest --tb=short -q 2>&1 | tail -5
# Expected: ~666 passed, 16 skipped, 0 failed

# Verify report service exists and has P0/P1 methods
grep -c "def generate_" src/services/referral_report_service.py
# Expected: ≥44 (14 P0 + 30 P1 from Weeks 33-38)

# Read report inventory for cross-reference
cat docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md
```

**STOP if pre-flight fails.** Do not proceed with broken baseline.

---

## Reports to Build (12)

All reports extend the existing `ReferralReportService` in `src/services/referral_report_service.py`.

### Batch 1A: Registration Analytics (7 reports)

| # | Report Name | Description | Output | Auth | Rationale |
|---|-------------|-------------|--------|------|-----------|
| 1 | Registration Aging Report | Members on each book by duration bucket (0-30, 31-90, 91-180, 180+ days) | PDF + Excel | Staff+ | Monthly board review, stale data identification |
| 2 | Registration Turnover Report | New registrations vs departures (dispatched, rolled-off, resigned) by period | PDF + Excel | Staff+ | Net queue growth/shrinkage trends |
| 3 | Re-Sign Compliance Report | Re-sign on-time vs late vs missed by book — **Rule 7 enforcement analytics** | PDF + Excel | Staff+ | 30-day cycle compliance monitoring |
| 4 | Re-Registration Pattern Analysis | Re-registration triggers (short call, under scale, 90-day, turnaround) by frequency and book — **Rule 6 analytics** | PDF + Excel | Staff+ | Identifies which triggers drive most churn |
| 5 | Inactive Registration Report | Registrations with no activity (no re-sign, no dispatch, no bid) for 60+ days | PDF + Excel | Staff+ | Stale data cleanup, queue hygiene |
| 6 | Cross-Book Registration Analysis | Members registered on multiple books simultaneously — **Rule 5 validation** | PDF + Excel | Officer+ | Validates one-per-classification rule; shows cross-regional patterns (87% Wire members on all 3 regional books) |
| 7 | Classification Demand Gap | Registrations available vs labor requests received per classification | PDF + Excel | Staff+ | Skills gap / supply-demand mismatch |

### Batch 1B: Book Analytics (5 reports)

| # | Report Name | Description | Output | Auth | Rationale |
|---|-------------|-------------|--------|------|-----------|
| 8 | Book Comparison Dashboard | Side-by-side metrics per book: avg wait time, dispatch rate, turnover, fill rate | PDF + Excel | Staff+ | Cross-book performance comparison |
| 9 | Tier Distribution Report | Book 1/2/3/4 registration counts and percentages per classification | PDF + Excel | Staff+ | Tests "Book 3 = Travelers" hypothesis; inverted distributions (STOCKMAN B3 = 8.6× B1) |
| 10 | Book Capacity Trends | Registration counts over time (weekly/monthly) per book with period-over-period change | PDF + Excel | Staff+ | Capacity planning, seasonal staffing |
| 11 | APN Wait Time Distribution | Histogram of wait times from registration to first dispatch, bucketed by book | PDF + Excel | Staff+ | Queue fairness analysis |
| 12 | Seasonal Registration Patterns | Registration volume by month/quarter overlaid with dispatch volume for correlation | PDF + Excel | Staff+ | Workforce planning, seasonal hiring patterns |

---

## Implementation Pattern (Follow Weeks 36-38 Exactly)

### Service Layer

Add 12 methods to existing `src/services/referral_report_service.py`:

```python
# Pattern from Weeks 36-38:
async def generate_registration_aging_report(
    self, db: Session, format: str = "pdf",
    book_id: Optional[int] = None,
    as_of_date: Optional[date] = None,
) -> Union[bytes, StreamingResponse]:
    """Registration aging analysis with configurable buckets."""
    # 1. Query data with filters
    # 2. Aggregate into report structure
    # 3. Generate PDF (WeasyPrint) or Excel (openpyxl)
    # 4. Log report generation to audit
    pass
```

**Service method naming:** `generate_{report_name_snake_case}_report()`

**Return structure (consistent with P1):**
```python
{
    "data": [...],           # Report rows
    "summary": {...},        # Aggregate stats (totals, averages)
    "filters": {...},        # Applied filters for display
    "generated_at": ...,     # Timestamp
    "generated_by": ...,     # User who requested
    "report_name": "..."     # Human-readable name
}
```

### Report-Specific Implementation Notes

**Report 3 (Re-Sign Compliance):**
- Query `registration_activities` for re-sign events
- Calculate days between re-signs; flag any gap > 30 days as "late"
- Missing re-sign within 30-day window = "missed"
- Color coding: green (on-time), yellow (late 1-5 days), red (missed)

**Report 4 (Re-Registration Patterns):**
- Query `registration_activities` where `activity_type = 're_registration'`
- Group by `re_registration_reason` enum values
- Show frequency distribution and which books see the most churn

**Report 6 (Cross-Book Registration):**
- Query members with COUNT(DISTINCT book_id) > 1 in `book_registrations`
- Officer+ only — shows member names and book combinations
- Expected finding: ~87% of Wire members on all 3 regional books
- Flag any member on 4+ books (rare but validates cross-classification like APN 45880.41)

**Report 9 (Tier Distribution):**
- Group `book_registrations` by `book_priority_number` per book
- Calculate percentages
- Highlight inverted distributions (where Book 3 > Book 1) with visual indicator

**Report 11 (APN Wait Time):**
- APN is DECIMAL(10,2) — integer part is Excel serial date (registration date)
- Wait time = dispatch_date minus registration_date (derived from APN integer part)
- Bucket into: <7 days, 7-30, 31-90, 91-180, 180+ days
- Handle members never dispatched separately ("Still waiting" bucket)

### API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/reports/referral/registration-aging` | GET | Staff+ | Duration buckets per book |
| `/api/v1/reports/referral/registration-turnover` | GET | Staff+ | In vs out per period |
| `/api/v1/reports/referral/re-sign-compliance` | GET | Staff+ | Rule 7 analytics |
| `/api/v1/reports/referral/re-registration-patterns` | GET | Staff+ | Rule 6 trigger analysis |
| `/api/v1/reports/referral/inactive-registrations` | GET | Staff+ | Stale registrations |
| `/api/v1/reports/referral/cross-book-registration` | GET | Officer+ | Multi-book members |
| `/api/v1/reports/referral/classification-demand-gap` | GET | Staff+ | Supply vs demand |
| `/api/v1/reports/referral/book-comparison` | GET | Staff+ | Cross-book metrics |
| `/api/v1/reports/referral/tier-distribution` | GET | Staff+ | Book tier breakdown |
| `/api/v1/reports/referral/book-capacity-trends` | GET | Staff+ | Registration trends |
| `/api/v1/reports/referral/apn-wait-time` | GET | Staff+ | Wait time histogram |
| `/api/v1/reports/referral/seasonal-registration` | GET | Staff+ | Seasonal patterns |

**Standard query params on all endpoints:**
- `format` (pdf|xlsx, default pdf)
- `book_id` (optional — filter to single book)
- `start_date`, `end_date` (optional — date range)

### PDF Templates

Create in `src/templates/reports/referral/`:
- Follow existing P1 template structure (header, filters summary, stats cards, data table, footer)
- Union branding (IBEW Local 46 header)
- Generated date + generated by
- Print-friendly CSS (`@media print`)
- Landscape orientation for wide tables (>6 columns)
- Color coding where specified in report notes above

### Excel Templates

Follow existing pattern:
- openpyxl with proper headers
- Auto-column-width
- Freeze panes (row 1)
- Sheet name matches report name

### Tests

**Minimum 2 tests per report** (1 service + 1 API):
- Service: verify data aggregation logic with test fixtures
- API: verify endpoint returns 200 with correct content-type
- Use UUID-based test data (BUG-029/030 lesson)
- Use existing fixtures where possible

**Target: 24 new tests** (12 reports × 2 tests each)

---

## File Modification Plan

### Modified:
```
src/services/referral_report_service.py      # ADD 12 new methods
src/routers/referral_reports_api.py          # ADD 12 new endpoints
src/tests/test_referral_reports_p2.py        # NEW or extend existing test file
CLAUDE.md                                     # Version, test count, report count
CHANGELOG.md                                  # Week 40 entries
```

### Created:
```
src/templates/reports/referral/registration_aging.html
src/templates/reports/referral/registration_turnover.html
src/templates/reports/referral/re_sign_compliance.html
src/templates/reports/referral/re_registration_patterns.html
src/templates/reports/referral/inactive_registrations.html
src/templates/reports/referral/cross_book_registration.html
src/templates/reports/referral/classification_demand_gap.html
src/templates/reports/referral/book_comparison.html
src/templates/reports/referral/tier_distribution.html
src/templates/reports/referral/book_capacity_trends.html
src/templates/reports/referral/apn_wait_time.html
src/templates/reports/referral/seasonal_registration.html
docs/reports/session-logs/2026-XX-XX-week40-p2-reports-batch1.md
```

---

## Anti-Patterns (DO NOT)

1. **DO NOT** build P3 reports — P2 only this sprint
2. **DO NOT** refactor the report service architecture — extend the existing pattern
3. **DO NOT** change existing P0 or P1 report behavior
4. **DO NOT** create new models or migrations — reports query existing Phase 7 models
5. **DO NOT** add new pip dependencies — WeasyPrint + openpyxl are sufficient
6. **DO NOT** skip tests — minimum 2 per report, no exceptions
7. **DO NOT** hardcode non-unique test data — use UUID suffixes (BUG-029/030 lesson)
8. **DO NOT** store APN as anything other than DECIMAL(10,2) in any report output
9. **DO NOT** expose member names in Staff-level reports that should be Officer+ only (Report 6)
10. **DO NOT** forget documentation updates — they are mandatory, not optional

---

## Document Update Directive

**⚠️ MANDATORY: Update *ANY* & *ALL* relevant documents (i.e. Bug log, ADR's, anything under /app/* *AND/OR* /app/docs/*). Again as you feel is necessary.**

Specifically check and update:
- `CLAUDE.md` — version bump, test count, report count (54 total: 14 P0 + 30 P1 + 10 P2 after this sprint... wait, 12 P2), Phase 7 status
- `CHANGELOG.md` — Add Week 40 entries under [Unreleased]
- `docs/BUGS_LOG.md` — Log any new bugs found and fixed
- `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` — Mark P2 batch 1 reports as complete
- Create individual `docs/bugs/BUG-0XX-*.md` files for any bugs found
- Session log creation

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
   git commit -m "feat(reports): Week 40 P2 reports batch 1 — registration & book analytics (12 reports, 24 tests)

   P2 Registration Analytics: aging, turnover, re-sign compliance (Rule 7),
   re-registration patterns (Rule 6), inactive registrations, cross-book
   registration (Rule 5), classification demand gap

   P2 Book Analytics: comparison dashboard, tier distribution, capacity
   trends, APN wait time, seasonal registration patterns"
   git push origin develop
   ```

3. **Session log:**
   Create `docs/reports/session-logs/2026-XX-XX-week40-p2-reports-batch1.md`

4. **Hub Return Summary:**
   ```
   === WEEK 40 HUB RETURN SUMMARY ===
   Version: v0.9.14-alpha
   Tests: XXX total (XXX passed, XX skipped, 0 failed)
   Reports built this sprint: 12 P2 (registration & book analytics)
   Reports total: 56 (14 P0 + 30 P1 + 12 P2)
   Phase 7g progress: P2 Batch 1 complete, Batch 2 next (Week 41)
   Files modified: [list]
   Bugs found: [list or "none"]
   ```

---

## Scope Boundaries

### IN SCOPE:
- 12 P2 reports (registration + book analytics)
- PDF + Excel output for each
- Tests for each report (24 minimum)
- Document updates per directive

### OUT OF SCOPE (do NOT attempt):
- P3 reports (Week 42)
- P2 Batch 2 dispatch/employer reports (Week 41)
- New models or schema changes
- Frontend page changes
- Refactoring existing P0/P1 reports
- Square payment integration
- LaborPower data import (blocked)
- Phase 5: Access DB Migration (stakeholder approval)
- Spoke 1/3 activation (Hub decision)

---

## Session Reminders

> **Member ≠ Student.** Phase 7 models FK to `members`, NOT `students`.

> **Book ≠ Contract.** STOCKMAN book → STOCKPERSON contract. 3 books have NO contract code.

> **APN = DECIMAL(10,2).** Integer part is Excel serial date. Decimal part is secondary sort key. NEVER truncate.

> **Check marks are per area book.** A check mark on Wire Seattle doesn't affect Wire Bremerton.

> **Audit.** Report generation MUST be audit-logged.

> **Pattern First.** Follow Weeks 36-38 patterns exactly. Do not invent new patterns for P2 reports.

> **Test isolation.** Use UUID-based test data to prevent fixture collisions (BUG-029/030 lessons).

---

*Spoke 2 — Week 40 Instruction Document (Merged)*
*UnionCore (IP2A-Database-v2)*
*Generated: February 6, 2026 by Hub*
