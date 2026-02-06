# Spoke 2 — Week 42 Instruction Document
# P3 Reports + Phase 7g Close-Out

> **Hub → Spoke 2 Handoff**
> **Sprint:** Week 42
> **Phase:** 7g (P2+P3 Reports) — FINAL SPRINT
> **Estimated Hours:** ~6 hrs (3 hrs reports, 3 hrs close-out + documentation)
> **Pre-requisite:** Week 41 P2 Batch 2 complete (v0.9.15-alpha)
> **Generated:** February 6, 2026 (Merged — Hub + Spoke 2 report sets)

---

## Objective

1. Build the final **10 P3** (Low priority) reports — projections, ad-hoc tools, compliance diagnostics, and year-in-review
2. Close out Phase 7g (all unblocked reports complete)
3. Reconcile ALL Phase 7 documentation
4. Version bump to **v0.9.16-alpha** (v1.0.0-beta is a Hub decision — do not self-promote)

Follow the **exact same patterns** from Weeks 36-41. Do NOT invent new patterns.

> **⚠️ P3 Data Dependency Note:** Several P3 reports rely on historical data that may not exist yet in a fresh system. Service methods should handle empty datasets gracefully — return a valid report structure with "Insufficient historical data for projection" messaging rather than errors. These reports become more valuable as the system accumulates data over months/years.

---

## Pre-Flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
git status  # Clean working tree

# Verify baseline (should include Week 40+41 tests)
pytest --tb=short -q 2>&1 | tail -5
# Expected: ~728+ passed, 16 skipped, 0 failed

# Verify total report methods built so far
grep -c "def generate_" src/services/referral_report_service.py
# Expected: ≥75 (14 P0 + 30 P1 + 31 P2)

# Quick inventory check
echo "P0: $(grep -c 'P0.*✅\|P0.*Complete\|P0.*DONE' docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md 2>/dev/null || echo 'check manually')"
echo "P1: $(grep -c 'P1.*✅\|P1.*Complete\|P1.*DONE' docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md 2>/dev/null || echo 'check manually')"
echo "P2: $(grep -c 'P2.*✅\|P2.*Complete\|P2.*DONE' docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md 2>/dev/null || echo 'check manually')"
```

**STOP if pre-flight fails.** Do not proceed with broken baseline.

---

## Part 1: P3 Reports to Build (10)

### P3-A: Forecasting & Projections (3 reports)

| # | Report Name | Description | Output | Auth | Rationale |
|---|-------------|-------------|--------|------|-----------|
| 1 | Workforce Projection | Project 30/60/90 day queue levels based on current registration velocity and dispatch rates | PDF | Officer+ | Strategic workforce planning |
| 2 | Dispatch Volume Forecast | Project next month's dispatch volume by classification based on historical seasonal patterns | PDF + Excel | Officer+ | Budget planning, staffing |
| 3 | Book Demand Forecast | Per-book projected demand based on employer request history and seasonal trends | PDF + Excel | Officer+ | Capacity planning |

### P3-B: Operational Intelligence (4 reports)

| # | Report Name | Description | Output | Auth | Rationale |
|---|-------------|-------------|--------|------|-----------|
| 4 | Member Availability Index | Score each book's fill capability: registrations available ÷ recent request rate | PDF | Staff+ | Real-time capacity gauge |
| 5 | Employer Loyalty Score | Rank employers by composite: repeat requests, low terminations, on-time requests, no violations | PDF + Excel | Officer+ | Relationship value ranking |
| 6 | Member Journey Report | Individual member lifecycle: registration → bids → dispatches → outcomes → re-registrations | PDF | Officer+ | Case-level audit trail |
| 7 | Comparative Book Performance | Normalized comparison across all books: fill rate, avg wait, dispatch velocity, check mark rate | PDF + Excel | Staff+ | Cross-book benchmarking |

### P3-C: Administrative & Ad-Hoc (3 reports)

| # | Report Name | Description | Output | Auth | Rationale |
|---|-------------|-------------|--------|------|-----------|
| 8 | Custom Date Range Export | Export any combination of dispatch/registration/employer data for custom date range and filters | Excel only | Staff+ | Ad-hoc analysis tool |
| 9 | Annual Operations Summary | Year-in-review: total dispatches, unique members, top employers, book trends, compliance summary | PDF | Officer+ | Annual board report |
| 10 | Data Quality Report | Flag: missing data, orphaned records, duplicate APNs, stale registrations, constraint violations | PDF | Admin only | Data hygiene audit |

---

## Implementation Pattern (Follow Existing Exactly)

### Service Layer

Add 10 methods to existing `src/services/referral_report_service.py`:

```python
async def generate_workforce_projection_report(
    self, db: Session, format: str = "pdf",
    projection_days: int = 90,
) -> Union[bytes, StreamingResponse]:
    """Project queue levels based on velocity trends."""
    # Handle insufficient data gracefully
    pass
```

### Report-Specific Implementation Notes

**Report 1 (Workforce Projection):**
- Calculate registration velocity: new registrations per week over last 90 days
- Calculate dispatch velocity: dispatches per week over last 90 days
- Project: current_queue + (registration_velocity × weeks) - (dispatch_velocity × weeks)
- Show 30/60/90 day projections per book
- If < 90 days of data exist, return "Insufficient historical data" with whatever partial projection is possible

**Report 2 (Dispatch Volume Forecast):**
- Look at same-month dispatch volumes from previous year(s)
- Apply trend adjustment (current year's growth/decline rate)
- If no prior year data, use rolling 3-month average as baseline
- Show confidence indicator: "High" (2+ years data), "Medium" (1 year), "Low" (< 1 year)

**Report 3 (Book Demand Forecast):**
- Similar methodology to Report 2 but per-book
- Factor in seasonal patterns (construction industry ramps up spring/summer)
- Cross-reference with employer request patterns from Theme B reports

**Report 5 (Employer Loyalty Score):**
- Composite score (0-100) based on weighted factors:
  - Repeat request frequency (25%)
  - Low termination rate (25%)
  - On-time labor request submission before 3 PM cutoff (20%)
  - No blackout violations (15%)
  - No foreperson by-name abuse flags (15%)
- Rank employers from highest to lowest
- Officer+ only — sensitive relationship intelligence

**Report 6 (Member Journey Report):**
- Accepts a single `member_id` parameter
- Builds chronological timeline: registration → re-signs → bids → dispatches → outcomes → re-registrations
- Include check marks, exemptions, bidding infractions
- This is essentially an individual member audit trail for the referral system
- Officer+ — contains full member dispatch history

**Report 8 (Custom Date Range Export):**
- Flexible export tool with parameters:
  - `entity_type`: registrations | dispatches | labor_requests | employers
  - `start_date`, `end_date`
  - `book_id` (optional), `classification` (optional), `employer_id` (optional)
- Excel only (no PDF — this is a data dump, not a formatted report)
- Include all available columns for the selected entity type
- Respect role-based field visibility (Staff sees less than Officer)

**Report 9 (Annual Operations Summary):**
- Accepts `year` parameter (default: current year)
- Sections: Executive Summary, Dispatch Volume, Member Activity, Employer Activity, Compliance Summary, Book Performance
- Executive Summary: total dispatches, unique members dispatched, unique employers served, avg fill time
- Compliance: check marks issued, exemptions granted, bidding infractions, blackout violations
- This is the report the Business Manager presents at the annual membership meeting

**Report 10 (Data Quality Report):**
- Admin only — internal diagnostics
- Checks:
  - Registrations with NULL or invalid APN
  - Duplicate APN within same book (known valid case but flag for review)
  - Members with active registrations but no re-sign in 30+ days
  - Labor requests in OPEN status older than 30 days
  - Dispatches with no matching labor request
  - Orphaned job bids (bid exists but labor request deleted/cancelled)
  - Check marks without corresponding dispatch
- Each issue type: count, sample records, severity level

### API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/reports/referral/workforce-projection` | GET | Officer+ | Queue level projections |
| `/api/v1/reports/referral/dispatch-forecast` | GET | Officer+ | Volume forecast |
| `/api/v1/reports/referral/book-demand-forecast` | GET | Officer+ | Per-book demand forecast |
| `/api/v1/reports/referral/member-availability-index` | GET | Staff+ | Book fill capability score |
| `/api/v1/reports/referral/employer-loyalty-score` | GET | Officer+ | Employer ranking |
| `/api/v1/reports/referral/member-journey` | GET | Officer+ | Individual member lifecycle |
| `/api/v1/reports/referral/comparative-book-performance` | GET | Staff+ | Cross-book benchmarks |
| `/api/v1/reports/referral/custom-export` | GET | Staff+ | Ad-hoc data dump |
| `/api/v1/reports/referral/annual-summary` | GET | Officer+ | Year-in-review |
| `/api/v1/reports/referral/data-quality` | GET | Admin | Data hygiene audit |

### Tests

**Minimum 2 tests per report:**
- **Target: 20 new tests** (10 reports × 2 tests each)
- P3 forecast tests should verify graceful handling of insufficient data
- Data Quality report test should seed known-bad data and verify detection

---

## Part 2: Phase 7g Close-Out

After P3 reports are built, execute these close-out tasks.

### Task 1: Report Inventory Reconciliation

Open `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` and reconcile:

```
Total reports built:
  P0 (Critical):    14 ✅
  P1 (High):        30 ✅
  P2 (Medium):      31 ✅ (12 Batch 1 + 19 Batch 2)
  P3 (Low):         10 ✅ (Week 42)
  ──────────────────────
  Subtotal built:   85 reports

Original LaborPower inventory: ~78 de-duplicated from 91 raw
New enforcement/analytics reports added: ~7 (Theme C from Week 41)

Remaining blocked:
  Reports requiring LaborPower raw data (7a/7d): list specific reports
  Mark each with: ⛔ Blocked — requires LaborPower data access
```

Mark every report in the inventory:
- ✅ Complete (with week number)
- ⛔ Blocked (with blocker reason)
- ❌ Deferred (with rationale)

### Task 2: Phase 7 Sub-Phase Status Update

Update CLAUDE.md Phase 7 section:

| Sub-Phase | Status | Sprint | Notes |
|-----------|--------|--------|-------|
| 7a Data Collection | ⛔ BLOCKED | — | LaborPower access needed |
| 7b Schema Finalization | ✅ COMPLETE | Weeks 20-21 | May need refinement when 7a resolves |
| 7c Core Services + API | ✅ COMPLETE | Weeks 22-25 | 7 services, 5 routers, ~51 endpoints |
| 7d Import Tooling | ⛔ BLOCKED | — | Depends on 7a |
| 7e Frontend UI | ✅ COMPLETE | Weeks 26-27, 32 | 28 routes, 11 pages, 15 partials |
| 7f Reports P0+P1 | ✅ COMPLETE | Weeks 33-38 | 44 reports (14 P0 + 30 P1) |
| 7g Reports P2+P3 | ✅ COMPLETE | Weeks 40-42 | 41 reports (31 P2 + 10 P3) |

**Completion: 5 of 7 sub-phases done. 2 blocked on external dependency.**

### Task 3: Test Suite Metrics Snapshot

```bash
# Full test run
pytest -v --tb=short 2>&1 | tee /tmp/week42_test_results.txt

# Count by file
pytest --co -q 2>&1 | grep "test_" | sort | uniq -c | sort -rn

# Summary
echo "=== WEEK 42 FINAL METRICS ==="
pytest --tb=short -q 2>&1 | tail -5
```

Document in session log:
- Total tests, pass/fail/skip/error counts, pass rate
- New tests added in Weeks 40-42
- Breakdown: Phase 7 report tests vs other tests

### Task 4: Version Bump

Bump to **v0.9.16-alpha** with CHANGELOG note:

```markdown
## [v0.9.16-alpha] — 2026-XX-XX

### Phase 7g COMPLETE: All Unblocked Reports Built

**Reports:** 85 total (14 P0 + 30 P1 + 31 P2 + 10 P3)
- Week 40: P2 Batch 1 — 12 registration & book analytics reports
- Week 41: P2 Batch 2 — 19 dispatch, employer & enforcement analytics reports
- Week 42: P3 — 10 projection, intelligence & administrative reports

**Phase 7 Status:** 5 of 7 sub-phases complete
- ✅ 7b Schema, 7c Services/API, 7e Frontend, 7f P0+P1 Reports, 7g P2+P3 Reports
- ⛔ 7a Data Collection, 7d Import Tooling (blocked on LaborPower access)

**Test Suite:** XXX tests (XXX passed, XX skipped, 0 failed)
```

---

## File Modification Plan

### Modified:
```
src/services/referral_report_service.py      # ADD 10 new methods (P3)
src/routers/referral_reports_api.py          # ADD 10 new endpoints
src/tests/test_referral_reports_p3.py        # NEW test file (20 tests)
CLAUDE.md                                     # Major update — Phase 7g complete
CHANGELOG.md                                  # Week 42 + Phase 7g summary
docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md  # Full reconciliation
docs/phase7/PHASE7_CONTINUITY_DOC.md         # Final status update
docs/IP2A_MILESTONE_CHECKLIST.md             # Phase 7g status
docs/IP2A_BACKEND_ROADMAP.md                 # Phase 7g status
docs/README.md                                # Updated stats
```

### Created:
```
src/templates/reports/referral/workforce_projection.html
src/templates/reports/referral/dispatch_forecast.html
src/templates/reports/referral/book_demand_forecast.html
src/templates/reports/referral/member_availability_index.html
src/templates/reports/referral/employer_loyalty_score.html
src/templates/reports/referral/member_journey.html
src/templates/reports/referral/comparative_book_performance.html
src/templates/reports/referral/annual_summary.html
src/templates/reports/referral/data_quality.html
docs/reports/session-logs/2026-XX-XX-week42-p3-reports-phase7g-closeout.md
```

**Note:** Report 8 (Custom Export) is Excel-only — no PDF template needed.

---

## Anti-Patterns (DO NOT)

1. **DO NOT** self-promote version to v1.0.0-beta — that's a Hub decision
2. **DO NOT** refactor existing report service architecture
3. **DO NOT** change P0/P1/P2 report behavior
4. **DO NOT** create new models or migrations
5. **DO NOT** add new pip dependencies
6. **DO NOT** skip tests — minimum 2 per report
7. **DO NOT** let projection reports error on empty data — return graceful "Insufficient data" messaging
8. **DO NOT** hardcode test data — UUID suffixes always
9. **DO NOT** skip the close-out documentation — **this is the most important documentation sprint of all of Phase 7**
10. **DO NOT** forget: check marks are per area book, APN is DECIMAL(10,2), contract_code is NULLABLE

---

## Document Update Directive

**⚠️ MANDATORY: Update *ANY* & *ALL* relevant documents (i.e. Bug log, ADR's, anything under /app/* *AND/OR* /app/docs/*). Again as you feel is necessary.**

**This sprint's documentation is the MOST IMPORTANT of the entire Phase 7 run.** When leadership asks "what did Phase 7 build?" — the documentation updated in this session is the answer.

### Comprehensive Document Update Checklist:

| Document | Updates Required |
|----------|-----------------|
| `CLAUDE.md` | Version → v0.9.16-alpha, test count, report count (85), Phase 7 sub-phase status table, current focus line |
| `CHANGELOG.md` | Week 42 entries + Phase 7g completion summary block |
| `docs/IP2A_MILESTONE_CHECKLIST.md` | Phase 7g marked COMPLETE, updated stats, remaining blockers |
| `docs/IP2A_BACKEND_ROADMAP.md` | Phase 7 progress updated, sub-phase 7g → COMPLETE |
| `docs/README.md` | Updated version, test count, report count, Phase 7 status |
| `docs/BUGS_LOG.md` | Any bugs found during P3 implementation |
| `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` | FULL RECONCILIATION — every report marked ✅/⛔/❌ |
| `docs/phase7/PHASE7_CONTINUITY_DOC.md` | Final status: 7g complete, what remains blocked |
| Individual `docs/bugs/BUG-0XX-*.md` | Create for any bugs found |
| Session log | Full session summary with metrics |

---

## End-of-Session Requirements

1. **Run full test suite:**
   ```bash
   pytest --tb=short -q 2>&1 | tail -10
   ```
   - Confirm pass rate ≥ 98% (target: maintain 100%)

2. **Commit and push:**
   ```bash
   git add -A
   git commit -m "feat(reports): Week 42 P3 reports + Phase 7g close-out — 85 reports complete (v0.9.16-alpha)

   P3 Reports: workforce projection, dispatch/book demand forecasts,
   member availability index, employer loyalty score, member journey,
   comparative book performance, custom export, annual summary, data quality

   Phase 7g: COMPLETE — 5 of 7 sub-phases done
   85 total reports (14 P0 + 30 P1 + 31 P2 + 10 P3)
   Remaining: 7a (data collection), 7d (import tooling) blocked on LaborPower"
   git push origin develop
   ```

3. **Session log:**
   Create `docs/reports/session-logs/2026-XX-XX-week42-p3-reports-phase7g-closeout.md`

4. **Hub Return Summary:**
   ```
   === WEEK 42 HUB RETURN SUMMARY ===
   Version: v0.9.16-alpha
   Tests: XXX total (XXX passed, XX skipped, 0 failed)
   Reports built: 85 total (14 P0 + 30 P1 + 31 P2 + 10 P3)
   Phase 7g: ✅ COMPLETE
   Phase 7 overall: 5/7 sub-phases complete
     ✅ 7b Schema, 7c Services/API, 7e Frontend, 7f P0+P1, 7g P2+P3
     ⛔ 7a Data Collection, 7d Import Tooling (LaborPower access)
   Blocked reports: [count and list — reports requiring LaborPower raw data]
   Next: Hub decision required:
     - Phase 8 (Square migration)?
     - Demo prep for leadership?
     - Push for LaborPower access to unblock 7a/7d?
     - Spoke 1/3 activation?
   Files modified: [list]
   Bugs found: [list or "none"]
   ```

5. **Update ALL documents per comprehensive checklist above**

---

## Scope Boundaries

### IN SCOPE:
- 10 P3 reports (projections, intelligence, admin)
- Phase 7g close-out documentation
- Test suite metrics snapshot
- Version bump to v0.9.16-alpha
- Comprehensive document reconciliation
- Hub Return Summary

### OUT OF SCOPE (do NOT attempt):
- Version promotion to v1.0.0-beta (Hub decision)
- Square payment integration (Phase 8A — Hub decision pending)
- LaborPower data collection (blocked — 7a)
- Schema changes or new models
- Frontend redesigns
- Refactoring existing P0/P1/P2 reports
- Hub-owned documents (Roadmap version bumps, Checklist version bumps — update content but don't change document version numbers)
- Spoke 1/3 activation

---

## Session Reminders

> **This is Phase 7's final unblocked sprint.** Make it count. Clean documentation matters as much as working code.

> **Member ≠ Student.** Phase 7 models FK to `members`, NOT `students`.

> **Book ≠ Contract.** STOCKMAN book → STOCKPERSON contract. 3 books have NO contract code.

> **APN = DECIMAL(10,2).** Integer part is Excel serial date. Decimal part is secondary sort key. NEVER truncate.

> **Check marks are per area book.** Wire Seattle ≠ Wire Bremerton.

> **Graceful empty data.** P3 forecast reports MUST handle insufficient historical data without errors.

> **Audit.** Report generation MUST be audit-logged.

> **Pattern First.** Follow Weeks 36-41 patterns exactly. No new patterns.

> **Test isolation.** UUID-based test data. All BUG-029 through BUG-033 lessons apply.

---

*Spoke 2 — Week 42 Instruction Document (Merged)*
*UnionCore (IP2A-Database-v2)*
*Generated: February 6, 2026 by Hub*
