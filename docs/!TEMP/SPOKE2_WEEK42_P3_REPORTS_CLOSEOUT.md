# Claude Code Instructions: Week 42 — P3 Reports + Phase 7g Close-Out

**Source:** Spoke 2: Operations (Hub Handoff: Weeks 40-42)
**Target:** Claude Code execution
**Project Version at Start:** v0.9.15-alpha (post-Week 41)
**Sprint Scope:** 7 P3 reports + Phase 7g close-out + comprehensive documentation reconciliation
**Estimated Effort:** 5 hours
**Branch:** `develop`
**Spoke:** Spoke 2: Operations

---

## TL;DR

This is the **final Phase 7 sprint**. Two objectives:

1. **Build 7 P3 (Low priority) reports** — projections, ad-hoc analytics, and advanced forecasting. These are "nice-to-have" strategic tools. (~3 hours)
2. **Phase 7g close-out and documentation reconciliation** — mark Phase 7g complete, update ALL project documentation to reflect the full Phase 7 journey from Weeks 20-42. (~2 hours)

After this sprint, Phase 7 reports are DONE (all 78 reports — or as many as data allows — across P0/P1/P2/P3). The remaining Phase 7 work (7a data collection, 7b schema finalization, 7d import tooling) is blocked on LaborPower access and is NOT this sprint's concern.

---

## Pre-Flight (MANDATORY)

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
git log --oneline -5

# Verify Week 41 baseline — must be ~100% pass rate
python -m pytest src/tests/ -x -q 2>&1 | tail -20

# RECORD THE EXACT NUMBERS:
# Total: ___  Passed: ___  Skipped: ___  Failed: ___

# Confirm report count
grep -n "def get_\|def generate_" src/services/referral_report_service.py | wc -l
# Expected: ~66 methods (14 P0 + 30 P1 + 22 P2)

# Confirm P2 tier is fully complete
grep -c "✅" docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md
# Expected: ~66

# Read full report inventory to identify P3 reports
cat docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md
```

**STOP IF:**
- Any non-skipped tests are failing → fix first
- Week 41 P2 reports are incomplete → complete Week 41 first
- Inventory doesn't show P2 fully complete → reconcile

---

## PART 1: P3 Reports (~3 hours)

### Context

P3 reports are the lowest priority — projections, forecasting, and advanced ad-hoc analytics. Some may be partially blocked by data gaps (the system hasn't been running long enough for certain projections to be meaningful). For any report where data is genuinely insufficient, implement the endpoint and service method that returns `{"data": [], "summary": {"note": "Insufficient historical data. This report requires minimum X months of data."}}` — do NOT skip the implementation entirely.

**CRITICAL:** Cross-reference each report below against `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` to confirm it's listed as P3. Substitute from the inventory if any below are already built or don't appear.

### Report 1: Dispatch Volume Forecast
- **What:** Project future dispatch volume based on historical trends — 3/6/12 month projection
- **Filters:** projection_months (3/6/12), book_id (optional), contract_code (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Projected Period, Estimated Dispatches (low/mid/high), Confidence Level, Historical Basis (months of data used)
- **Method:** Simple moving average + linear trend. NOT machine learning — keep it straightforward.
- **Summary section:** Projected growth/decline rate, seasonal adjustment factor, data quality warning if <6 months history
- **Minimum data:** Needs ≥6 months of dispatch data for meaningful projection. If <6 months, return "Insufficient data" with explanation.

### Report 2: Book Demand Forecast
- **What:** Project future book sizes and demand based on registration/dispatch velocity
- **Filters:** projection_months (3/6/12), book_id (optional)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Book, Current Size, Projected Size (3/6/12mo), Dispatch Rate Trend, Expected Wait Time (days)
- **Summary section:** Books expected to grow vs shrink, projected bottlenecks, estimated wait times
- **Minimum data:** Needs ≥6 months. If <6, return "Insufficient data."

### Report 3: Employer Workforce Planning
- **What:** Help employers anticipate workforce needs based on their historical request patterns
- **Filters:** employer_id (required), projection_months (3/6/12)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Period, Historical Avg Requests, Historical Avg Workers, Projected Requests, Projected Workers, Seasonal Factor
- **Summary section:** Peak demand months, recommended advance request timing, contract code utilization
- **Note:** This is a strategic tool for business reps to share with employer contacts

### Report 4: System Health Dashboard Report
- **What:** Comprehensive system health metrics — a "state of the referral system" snapshot
- **Filters:** as_of_date (optional, defaults to today)
- **Output:** PDF
- **Access:** Officer+
- **Key columns/sections:**
  - Book Status: active registrants per book, avg wait time, velocity
  - Dispatch Pipeline: open requests, pending bids, today's dispatches
  - Compliance: re-sign compliance rate, check mark rate, exemption count
  - Employer Activity: active employers, new employers this quarter, fill rate
- **Summary section:** Overall system health score (green/yellow/red based on thresholds), top 3 issues requiring attention
- **Note:** This is the "executive summary" report — the one an officer opens Monday morning

### Report 5: Ad-Hoc Member Journey Report
- **What:** Complete referral lifecycle for a specific member — registration → dispatches → re-registrations → current status
- **Filters:** member_id (required)
- **Output:** PDF
- **Access:** Officer+ (contains full member history)
- **Key columns:** Date, Event Type, Book, Employer (if dispatch), Duration, Outcome, Notes
- **Summary section:** Total registrations, total dispatches, avg dispatch duration, current status on each book, check mark count
- **Privacy:** This is a sensitive per-member report. Full PII visible only to Officer+.

### Report 6: Comparative Book Performance
- **What:** Side-by-side comparison of all books on key performance metrics
- **Filters:** Date range, metric_set (registration/dispatch/compliance)
- **Output:** PDF + Excel
- **Access:** Officer+
- **Key columns:** Book, Registrants, Dispatches, Avg Wait (days), Fill Rate %, Check Mark Rate, Re-Sign Compliance %, Velocity Score
- **Summary section:** Best-performing book, worst-performing, most improved, most declined
- **Note:** "Velocity Score" = composite metric of registration-to-dispatch speed. Define as: `dispatches / (avg_wait_days * active_registrants)` — higher = faster-moving book.

### Report 7: Annual Operations Summary
- **What:** Year-end comprehensive summary — designed for annual reports and leadership presentations
- **Filters:** year (required, e.g. 2026)
- **Output:** PDF
- **Access:** Officer+
- **Sections (not just columns — this is a multi-section report):**
  1. Executive Summary (key metrics, year-over-year comparison)
  2. Registration Activity (monthly breakdown, net growth)
  3. Dispatch Activity (monthly breakdown, fill rates, agreement types)
  4. Employer Engagement (top 20 employers, new employers, lost employers)
  5. Compliance (check marks, exemptions, bidding infractions, blackouts)
  6. Workforce Demographics (classification breakdown, book distribution)
  7. Outlook (based on current trends — ties to Report 1/2 forecast logic)
- **Summary section:** 5 key takeaways for leadership
- **Note:** This is the flagship report. It should look polished — larger fonts for section headers, page breaks between sections.

---

## Implementation Pattern

**Same as Weeks 36-41.** For each report:

1. **Service method** in `src/services/referral_report_service.py`
2. **Router endpoint** in `src/routers/referral_reports_api.py`
   - URL: `GET /api/v1/reports/referral/<report-name>`
3. **PDF template** in `src/templates/reports/referral/<report_name>.html`
4. **Tests** in `src/tests/test_referral_reports.py` — minimum 2 per report

**P3-Specific Notes:**
- Forecast reports (1, 2, 3): Use simple moving average, not complex ML. If insufficient data, return graceful "Insufficient data" response.
- Multi-section reports (4, 7): Use Jinja2 template sections with page-break CSS (`page-break-before: always`).
- Member journey report (5): Requires member_id parameter. Handle "member not found" with 404.
- Velocity Score (Report 6): Define and document the formula in the service method docstring.

---

## Anti-Patterns — DO NOT

1. **DO NOT** implement machine learning or complex statistics — simple moving averages and linear trends only
2. **DO NOT** refactor report service architecture
3. **DO NOT** change existing P0/P1/P2 report behavior
4. **DO NOT** create new models or migrations
5. **DO NOT** add new pip dependencies
6. **DO NOT** skip tests
7. **DO NOT** hardcode non-unique test data — UUID suffixes
8. **DO NOT** expose member PII to Staff role
9. **DO NOT** forget documentation (this is the close-out sprint — docs are CRITICAL)
10. **DO NOT** mark reports as "complete" in inventory if they return "Insufficient data" — mark them as "✅ Implemented (data-dependent)" instead

---

## PART 2: Phase 7g Close-Out & Documentation Reconciliation (~2 hours)

This is as important as the reports. Phase 7 has spanned 23 sprints (Weeks 20-42). Documentation must be reconciled to reflect the complete journey.

### Close-Out Checklist

#### 2.1 CLAUDE.md (project root) — COMPREHENSIVE UPDATE

Update ALL of the following:
- Version: v0.9.16-alpha
- Test count: actual from pytest
- Report count: "71+ of ~78 (14 P0 + 30 P1 + 22 P2 + 7 P3)" — note "some P3 data-dependent"
- Phase 7 status: "7g COMPLETE. Sub-phases 7a/7b/7d remain blocked (LaborPower access)."
- Phase 7 summary: total models, services, endpoints, frontend routes, reports, tests added
- Current focus: "Phase 7g complete. Awaiting Hub direction for next phase."

#### 2.2 CHANGELOG.md — Week 42 Entry + Phase 7 Summary Block

```markdown
## [v0.9.16-alpha] - 2026-XX-XX
### Added
- 7 P3 advanced analytics reports (dispatch forecast, book demand forecast, employer workforce planning, system health dashboard, member journey, comparative book performance, annual operations summary)
- ~14 new tests for P3 reports
### Changed
- Phase 7g (P2+P3 Reports) COMPLETE
- Updated report count: 71+ of ~78 (14 P0 + 30 P1 + 22 P2 + 7 P3)
- Some P3 reports return "Insufficient data" — data-dependent on system runtime

### Phase 7 Complete Summary (Weeks 20-42)
- 6 ORM models added
- 19 enums added
- 7 services implemented (14 business rules)
- 5 backend API routers (~51 endpoints)
- 2 frontend routers (28 routes)
- 11 page templates, 15 HTMX partials
- 71+ operational reports (PDF + Excel)
- Sub-phases complete: 7c, 7e, 7f, 7g
- Sub-phases blocked: 7a, 7b, 7d (LaborPower system access)
```

#### 2.3 docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md

- Mark ALL P3 reports as complete (or "Implemented (data-dependent)")
- Add summary at top of file:
  ```
  ## Completion Status
  - P0: 14/14 ✅
  - P1: 30/30 ✅ (some may be 33 — verify against file)
  - P2: 22/22 ✅
  - P3: 7/7 ✅ (some data-dependent)
  - Total: 71+/78 ✅
  ```
- Note any reports that were discovered to be duplicates or not applicable during implementation

#### 2.4 docs/IP2A_MILESTONE_CHECKLIST.md

Update the Phase 7 section:
- Sub-Phase 7g: mark as ✅ COMPLETE
- Update the report inventory summary table
- Update Quick Stats section with final numbers
- Update version history table

#### 2.5 docs/IP2A_BACKEND_ROADMAP.md

Update:
- Phase 7 section → "7g: COMPLETE"
- Implementation Status table → 7g marked complete with hours and dates
- Known Issues → remove any resolved items
- Risk Register → update Phase 7 items

#### 2.6 docs/README.md (hub_README)

Update:
- Current Status table
- Phase 7 Progress Summary
- What's Next section (should say "Awaiting Hub direction")

#### 2.7 Session Log

Create `docs/reports/session-logs/2026-XX-XX-week42-p3-reports-phase7g-closeout.md` with:
- P3 reports built
- Phase 7g close-out summary
- Final test count
- Final report count
- Complete list of files modified
- Any items flagged for Hub

#### 2.8 Bug Documentation (IF APPLICABLE)
- Bugs → `docs/BUGS_LOG.md` + individual files
- No bugs → note in session log

---

## Files You Will Modify/Create

**Modified:**
- `src/services/referral_report_service.py` — add 7 new service methods
- `src/routers/referral_reports_api.py` — add 7 new endpoints
- `src/tests/test_referral_reports.py` — add ~14 new tests
- `CLAUDE.md` — comprehensive Phase 7g close-out update
- `CHANGELOG.md` — Week 42 entry + Phase 7 summary block
- `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` — mark P3 complete, add summary
- `docs/IP2A_MILESTONE_CHECKLIST.md` — Phase 7g complete, final stats
- `docs/IP2A_BACKEND_ROADMAP.md` — Phase 7g complete, implementation status
- `docs/README.md` — current status, what's next

**Created:**
- `src/templates/reports/referral/dispatch_volume_forecast.html`
- `src/templates/reports/referral/book_demand_forecast.html`
- `src/templates/reports/referral/employer_workforce_planning.html`
- `src/templates/reports/referral/system_health_dashboard.html`
- `src/templates/reports/referral/member_journey.html`
- `src/templates/reports/referral/comparative_book_performance.html`
- `src/templates/reports/referral/annual_operations_summary.html`
- `docs/reports/session-logs/2026-XX-XX-week42-p3-reports-phase7g-closeout.md`

---

## Post-Session Documentation (MANDATORY — THIS IS THE CLOSE-OUT)

> ⚠️ **Update *ANY* & *ALL* relevant documents (i.e. Bug log, ADR's, anything under /app/* *AND/OR* /app/docs/*). Again as you feel is necessary.**

**This sprint's documentation is the MOST IMPORTANT of the entire Phase 7 run.** When leadership asks "what did Phase 7 build?" — the documentation updated in this session is the answer. Take the time to make it complete and accurate.

The close-out checklist in Part 2 above IS your documentation mandate. Complete every item.

---

## Hub Return Summary

```
=== WEEK 42 HUB RETURN SUMMARY ===
Version: v0.9.16-alpha
Tests: XXX total (XXX passed, 16 skipped, 0 failed)
Reports: 71+ of ~78 (14 P0 + 30 P1 + 22 P2 + 7 P3)
Phase 7g: COMPLETE
Phase 7 Overall: 7c ✅ 7e ✅ 7f ✅ 7g ✅ | 7a ⛔ 7b ⛔ 7d ⛔ (LaborPower blocked)
Bugs Found: [list or "none"]
Files Modified: [list]
Hub Escalations: [list or "none"]
Next Steps: Awaiting Hub direction (Square migration? Demo prep? Spoke 1/3 activation?)
```

---

## Session Reminders

> **Member ≠ Student.** Phase 7 models FK to `members`, NOT `students`.

> **Book ≠ Contract.** Mapping is NOT 1:1. 3 books have NO contract code.

> **APN = DECIMAL(10,2).** NEVER truncate to INTEGER.

> **Check marks are PER AREA BOOK.**

> **Audit.** Report generation MUST be audit-logged.

> **8 Contract Codes:** WIREPERSON, SOUND & COMM, STOCKPERSON, LT FXT MAINT, GROUP MARINE, GROUP TV & APPL, MARKET RECOVERY, RESIDENTIAL

> **User.has_role()** — NOT `user.role`.

> **Fixture Isolation.** BUG-030 through BUG-033 patterns.

> **Empty Data.** P3 forecasts on a new system WILL have sparse data. "Insufficient data" messages, not errors.

> **This is the close-out.** Leave the codebase and documentation in a state where anyone picking this up in 6 months can understand what was built, why, and what remains.

---

## Commit

```bash
# Commit 1: P3 reports
git add src/services/ src/routers/ src/tests/ src/templates/reports/
git commit -m "feat(reports): P3 — 7 advanced analytics & forecast reports (Week 42)

- Dispatch volume forecast, book demand forecast
- Employer workforce planning, system health dashboard
- Member journey report, comparative book performance
- Annual operations summary (flagship multi-section report)
- ~14 new tests, all passing
- Phase 7g COMPLETE
- Reports: 71+ of ~78 (14 P0 + 30 P1 + 22 P2 + 7 P3)"

# Commit 2: Documentation close-out
git add CLAUDE.md CHANGELOG.md docs/
git commit -m "docs: Phase 7g close-out — comprehensive documentation reconciliation

- CLAUDE.md: v0.9.16-alpha, Phase 7g complete
- CHANGELOG: Week 42 + Phase 7 summary block
- Reports inventory: all tiers marked complete
- Milestone checklist: 7g complete, final stats
- Roadmap: 7g complete, implementation status
- README: updated status and next steps
- Session log: Week 42 close-out summary"

git push origin develop
```

---

## BLOCKED ITEMS (DO NOT WORK ON)

| Item | Blocker | When |
|------|---------|------|
| 7a: Data Collection | LaborPower system access | When Xerxes obtains access |
| 7b: Schema Finalization | 7a must complete first | After 7a |
| 7d: Import Tooling | 7b must complete first | After 7b |
| Square Migration | Hub decision | After Phase 7g |
| Phase 5: Access DB | Stakeholder approval | Separate timeline |
| Spoke 1/3 Activation | Hub decision | After Phase 7g |
| Demo Preparation | Hub decision | After Phase 7g |

**After this sprint is committed, STOP and await Hub direction.** Do not begin new feature work without explicit instruction.

---

*Spoke 2: Operations — Week 42 Instruction Document (PHASE 7 CLOSE-OUT)*
*Generated: February 6, 2026*
*Hub Source: Hub → Spoke 2 Handoff: Weeks 40-42*
