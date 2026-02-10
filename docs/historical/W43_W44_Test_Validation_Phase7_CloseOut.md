# Claude Code Instructions: Weeks 43–44 — Test Validation & Phase 7 Close-Out

**Spoke:** Spoke 2: Operations
**Created:** February 6, 2026
**Estimated Hours:** 5–7 (2–3 for W43, 3–4 for W44)
**Branch:** `develop`
**Starting Version:** v0.9.16-alpha
**Target Version:** v0.9.18-alpha
**Dependency:** None — this is the foundation sprint. Everything else depends on this.

---

## Context

Weeks 40–42 produced 82 new report tests across P2+P3 tiers that were never validated against the full suite. Phase 7 has 5 of 7 sub-phases complete (7b, 7c, 7e, 7f, 7g) with 7a and 7d blocked on LaborPower access. Before moving to demo prep or Phase 8, we need a verified green baseline and clean documentation close-out.

**Week 43** stabilizes the test suite. **Week 44** closes the books on Phase 7 and generates the critical Spoke 1 Onboarding Context Document (Spoke 1 has never been used — that document is its ONLY context).

---

## Pre-Flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
git status  # Must be clean
git log --oneline -5  # Verify Week 40-42 commits exist

# Check Python environment
python --version  # 3.12.x expected
pip list | grep -E "fastapi|sqlalchemy|weasyprint|pytest"

# Start services
docker-compose up -d

# Baseline test run — CAPTURE THIS OUTPUT
pytest -v --tb=short 2>&1 | tee /tmp/test_results_week43_baseline.log
echo "Baseline test count:"
grep -E "passed|failed|error|skipped" /tmp/test_results_week43_baseline.log | tail -1
```

> ⚠️ **CAPTURE THE BASELINE NUMBERS.** You need the exact pass/fail/skip counts before making any changes.

---

## WEEK 43: Test Validation & Stabilization

### Objective

Verify all ~764 tests pass. Fix failures. Achieve a clean, verified baseline.

### Step 1: Analyze Baseline Results

After the pre-flight test run, categorize failures:

| Category | Symptom | Action | Time Limit |
|----------|---------|--------|------------|
| Import errors | `ModuleNotFoundError`, `ImportError` | Fix imports immediately | 5 min each |
| Fixture isolation | Tests pass alone, fail in suite | Check for shared state, add cleanup | 10 min each |
| WeasyPrint system deps | `OSError` related to fonts/cairo/pango | Skip-mark with `@pytest.mark.skip(reason="WeasyPrint system dep — requires manual install")` | 2 min each |
| Auth fixture conflicts | 401/403 in tests that should pass | Check `conftest.py` fixture scoping, verify JWT creation | 10 min each |
| Database state leaks | Stale data from prior tests | Add explicit cleanup or use fresh UUIDs | 10 min each |
| Flaky timing | Passes sometimes, fails sometimes | Run 3x; if inconsistent, skip-mark as flaky | 5 min each |

### Step 2: Fix or Skip (TIME-BOXED: 2 HOURS MAX)

Rules:
- **Quick fix (<15 min per issue):** Fix it. Commit atomically.
- **Structural issue (>15 min):** Create `Bug #034+` entry in bug log, add `@pytest.mark.skip(reason="Bug #0XX — [description]")`, move on.
- **WeasyPrint system dependency:** Always skip-mark. These require system-level package installs that vary by environment.
- **Do NOT refactor tests.** Fix, skip, or document. Refactoring is scope creep.

### Step 3: Known Issue — Dispatch.bid Relationship Bug

This was documented in v0.9.8-alpha and may or may not have been fixed in later weeks. Check:

```bash
# Check if the bug still exists
grep -n "bid = relationship" src/models/dispatch.py
```

If the relationship lacks `foreign_keys=[bid_id]`, fix it:

```python
# In src/models/dispatch.py
bid = relationship("JobBid", foreign_keys=[bid_id], back_populates="dispatch")
```

This should unblock up to 25 tests.

### Step 4: Final Validation

```bash
# Full suite run after fixes
pytest -v --tb=short 2>&1 | tee /tmp/test_results_week43_final.log

# Compare baseline vs final
echo "=== BASELINE ==="
grep -E "passed|failed|error|skipped" /tmp/test_results_week43_baseline.log | tail -1
echo "=== FINAL ==="
grep -E "passed|failed|error|skipped" /tmp/test_results_week43_final.log | tail -1
```

### Week 43 Acceptance Criteria

- [ ] Full test suite executed (all test files discovered)
- [ ] ≥98% non-skipped pass rate achieved
- [ ] Every failure either fixed or documented as Bug #0XX with skip-mark
- [ ] No regressions from Weeks 32–42 work
- [ ] Dispatch.bid relationship bug verified (fixed or confirmed already fixed)
- [ ] Test results log saved

### Week 43 Git Commit

```bash
git add -A
git commit -m "fix(tests): Week 43 — test validation and stabilization for P2+P3 reports

- Ran full suite: [ACTUAL_COUNT] tests total, [PASS] passing, [SKIP] skipped
- Fixed: [list specific fixes]
- Skip-marked: [list skip-marked tests with bug numbers]
- Baseline verified for Phase 7 close-out

Version: v0.9.17-alpha
Spoke: Spoke 2 (Operations)"
git push origin develop
```

---

## WEEK 44: Phase 7 Close-Out & Documentation

### Objective

Close the books on Phase 7's completed sub-phases. Update all tracking documents. Create Phase 7 retrospective. **Generate the Spoke 1 Onboarding Context Document** — this is the critical deliverable.

---

### Task 1: Update Report Inventory

**File:** `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md`

For each of the 85 implemented reports:
- Mark status as ✅ IMPLEMENTED
- Add implementation references: service method, API route, template path
- For reports blocked by 7a data: mark as ⏸️ BLOCKED — awaiting LaborPower data
- Add summary table at top:

```markdown
## Implementation Summary (as of Week 44)

| Priority | Total | Implemented | Blocked | Remaining |
|----------|-------|-------------|---------|-----------|
| P0       | 14    | [count]     | [count] | [count]   |
| P1       | 24    | [count]     | [count] | [count]   |
| P2       | 30    | [count]     | [count] | [count]   |
| P3       | 17    | [count]     | [count] | [count]   |
| **Total**| **85**| **[count]** | **[count]** | **[count]** |
```

---

### Task 2: Update Milestone Checklist

**File:** `docs/IP2A_MILESTONE_CHECKLIST.md`

- Mark sub-phases with completion status and dates:
  - 7b: ✅ COMPLETE (Weeks 20–21)
  - 7c: ✅ COMPLETE (Weeks 22–25)
  - 7e: ✅ COMPLETE (Weeks 26–28 + Week 32)
  - 7f: ✅ COMPLETE (Weeks 33–34)
  - 7g: ✅ COMPLETE (Weeks 40–42)
  - 7a: ⛔ BLOCKED — LaborPower access
  - 7d: ⛔ BLOCKED — depends on 7a
- Add Week 40–43 task entries
- Update Quick Stats section with verified test counts from Week 43

---

### Task 3: Update Backend Roadmap

**File:** `docs/IP2A_BACKEND_ROADMAP.md`

- Update Phase 7 status section:
  - 5 of 7 sub-phases complete
  - 85 reports implemented (14 P0, 24 P1, 30 P2, 17 P3)
  - 2 sub-phases blocked (7a, 7d) — pending demo to unblock
- Add Phase 8 as next active phase:
  - Phase 8A: Square Payment Migration (Spoke 1 — Weeks 47–49)
  - Phase 8B: TBD (demo feedback drives scope)
- Add demo preparation as intermediate milestone between Phase 7 and Phase 8

---

### Task 4: Create Phase 7 Retrospective

**New File:** `docs/phase7/PHASE7_RETROSPECTIVE.md`

Structure:

```markdown
# Phase 7 Retrospective: Referral & Dispatch System

> **Phase Duration:** Weeks 20–42 (approximately [X] calendar weeks)
> **Effort:** ~[X] hours estimated, ~[X] hours actual
> **Sub-phases Completed:** 5 of 7
> **Final Report Count:** 85 (14 P0, 24 P1, 30 P2, 17 P3)

## What Was Delivered
[Summary of all Phase 7 deliverables — models, services, endpoints, UI, reports]

## What Went Well
- Hub/Spoke model enabled parallel planning and implementation
- Data analysis (24 LaborPower PDFs) before coding prevented costly schema rework
- 8 critical schema findings caught before implementation
- WeasyPrint PDF pipeline established and reusable
- [more items from session history]

## What Was Challenging
- LaborPower access blocked 7a/7d for entire phase
- Dispatch.bid relationship bug blocked 25 tests
- Report count expanded from 78 to 85 during implementation
- [more items]

## Blocked Items (Carrying Forward)
- 7a: Data collection — 3 Priority 1 exports from LaborPower
- 7d: Import tooling — CSV pipeline for employer/registration/dispatch data
- These are unblocked by the stakeholder demo (Week 46)

## Lessons for Phase 8
- [lessons learned]

## Metrics
| Metric | Start of Phase 7 | End of Phase 7 |
|--------|-------------------|----------------|
| Tests  | ~470              | ~[actual]      |
| Endpoints | ~178           | ~[actual]      |
| Models | 26                | 32             |
| ADRs   | 14                | 18             |
```

---

### Task 5: Update CLAUDE.md

Verify all counts match reality:
- Version: v0.9.18-alpha
- Test count: [verified from Week 43]
- Endpoint count: ~320+
- Model count: 32
- ADR count: 18
- Phase 7 status: "5/7 sub-phases complete, 7a/7d blocked"
- Next: "Demo preparation (Weeks 45–46), Phase 8A Square migration (Weeks 47–49)"

---

### Task 6: ⚠️ CRITICAL — Generate Spoke 1 Onboarding Context Document

**New File:** `docs/handoffs/SPOKE1_ONBOARDING_CONTEXT.md`

Create the directory first:
```bash
mkdir -p docs/handoffs
```

**This document is the ONLY context Spoke 1 will have.** Spoke 1 has never been used. It cannot search Spoke 2's conversation history. Everything it needs must be in this single document.

**Required Sections:**

```markdown
# Spoke 1 Onboarding Context: Core Platform

> **Created:** [DATE]
> **Created By:** Spoke 2 (Operations) during Phase 7 close-out
> **Purpose:** Provide Spoke 1 with complete project context for Phase 8A (Square Payment Migration)
> **Reviewed By:** Hub (pending)

## 1. Project Baseline State

| Metric | Value |
|--------|-------|
| Project | UnionCore (IP2A-Database-v2) |
| Repository | https://github.com/theace26/IP2A-Database-v2 |
| Version | v0.9.18-alpha |
| Tests | [verified count] |
| API Endpoints | ~320+ |
| ORM Models | 32 (26 core + 6 Phase 7) |
| ADRs | 18 |
| Branch Strategy | develop (active work) → main (stable/deploy) |

## 2. Tech Stack
[Condensed from CLAUDE.md — Python 3.12, FastAPI, PostgreSQL 16, SQLAlchemy 2.x, etc.]

## 3. Dues Domain Summary (Your Primary Domain)

### Existing Models
- `DuesRate` — Rate definitions per classification/type
- `DuesPeriod` — Billing period boundaries
- `DuesPayment` — Individual payment records
- `DuesAdjustment` — Credit/debit adjustments with approval workflow

### Existing Endpoints (~35)
[List the key endpoint groups: /api/v1/dues/rates, /api/v1/dues/periods, etc.]

### Existing Tests
- Backend: 21 tests (test_dues.py)
- Frontend: 37 tests (test_frontend.py — dues section)
- Stripe tests: 25 tests (DEPRECATED — see ADR-018)

### Frontend Pages
- Dues landing, rates list, periods management, payment recording, adjustment workflow

## 4. Payment Processing History

**CRITICAL TIMELINE:**
1. **Week 11 (v0.8.0-alpha1):** Stripe integration built — PaymentService, webhook handler, checkout flow
2. **Week 35 (v0.9.11-alpha):** Stripe REMOVED — ADR-018 decision to migrate to Square
3. **Current state:** NO active payment processor. Payment models exist. Processing logic removed.

### ADR-018 Summary: Square Payment Migration
- **Decision:** Replace Stripe with Square for payment processing
- **Rationale:** [Include the key reasons from ADR-018 — likely Square's flat-rate pricing, in-person POS support, or union-specific advantages]
- **Phase A:** Client-side tokenization, Square SDK integration, basic payment flow
- **Phase B:** Recurring dues auto-pay, payment plans
- **Phase C:** In-person POS integration (if applicable)

### Square SDK Integration Notes
- Square uses client-side tokenization (Web Payments SDK)
- Server-side: Payments API to process tokens
- Environment: Square Sandbox for dev/test, Production for live
- Key difference from Stripe: No webhook-driven checkout sessions — tokenize → charge → verify

## 5. Cross-Cutting File Warnings

These files are shared across all Spokes. Modifications require noting in session summary:

| File | Why It's Shared | Caution |
|------|-----------------|---------|
| `src/main.py` | Router registration, middleware, startup events | Adding routers here affects all modules |
| `src/tests/conftest.py` | Auth fixtures, DB session, seed data | Fixture changes can break 700+ tests |
| `src/templates/base.html` | Master layout for all pages | CSS/JS changes affect every page |
| `src/templates/components/_sidebar.html` | Navigation for all modules | Adding links affects all users |
| `alembic/versions/` | Migration chain | Only one Spoke should create migrations at a time |

## 6. Coding Standards Quick Reference

| Item | Convention | Example |
|------|-----------|---------|
| Tables | snake_case, plural | dues_payments |
| Models | PascalCase, singular | DuesPayment |
| Services | PascalCase + Service | PaymentService |
| API routes | /api/v1/plural-nouns | /api/v1/dues/payments |
| Git commits | Conventional commits | feat(dues): add Square tokenization |
| Templates | snake_case | payment_form.html |
| Partials | underscore prefix | _payment_row.html |

## 7. Git Commit Message Format

```
type(scope): description

- Detail 1
- Detail 2

Version: vX.Y.Z-alpha
Spoke: Spoke 1 (Core Platform)
```

Types: feat, fix, docs, refactor, test, chore

## 8. Session Summary Requirements

Every Claude Code session MUST end with:
1. All tests passing (or failures documented)
2. CLAUDE.md updated with session summary
3. CHANGELOG.md updated
4. Any modified docs/* files updated
5. Git commit and push to develop
6. If shared files modified → note for Hub handoff

## 9. Security Notes for Payment Processing

- NEVER store raw card numbers in the database
- Square tokenization happens client-side — server only sees tokens
- PCI compliance: tokens are ephemeral, not reusable (unless stored as Cards on File)
- Payment amounts stored as integers (cents) to avoid floating point issues
- All payment operations require audit trail logging
- Payment endpoints require Staff+ role minimum

## 10. Audit Requirements

All payment-related changes MUST be audited:
- `dues_payments` is already in AUDITED_TABLES
- New Square payment records must log: amount, token (last 4 only), timestamp, user
- Refunds require Officer+ approval and separate audit entry
- 7-year NLRA retention applies to all financial records
```

> **⚠️ This document must be SELF-CONTAINED.** Review it as if you are Spoke 1 seeing this project for the first time. Does it have everything needed to start Week 47? If not, add it.

---

### Week 44 Acceptance Criteria

- [ ] Report inventory updated with implementation status for all 85 reports
- [ ] Milestone checklist updated with all sub-phase completion dates
- [ ] Backend roadmap updated with Phase 7 status and Phase 8 preview
- [ ] Phase 7 retrospective created with metrics and lessons learned
- [ ] CLAUDE.md updated to v0.9.18-alpha with verified counts
- [ ] `docs/handoffs/` directory created
- [ ] Spoke 1 Onboarding Context Document created and comprehensive
- [ ] All documentation internally consistent (no conflicting numbers)

### Week 44 Git Commit

```bash
git add -A
git commit -m "docs: Week 44 — Phase 7 close-out and Spoke 1 onboarding context

- Updated report inventory: 85 reports with implementation status
- Updated milestone checklist: 7b/7c/7e/7f/7g marked complete
- Updated backend roadmap: Phase 7 status, Phase 8 preview
- Created Phase 7 retrospective (docs/phase7/PHASE7_RETROSPECTIVE.md)
- Created Spoke 1 onboarding context (docs/handoffs/SPOKE1_ONBOARDING_CONTEXT.md)
- Updated CLAUDE.md to v0.9.18-alpha
- All counts verified against Week 43 test run

Version: v0.9.18-alpha
Spoke: Spoke 2 (Operations)"
git push origin develop
```

---

## Anti-Patterns (DO NOT)

- ❌ Do NOT refactor existing test code — fix or skip only
- ❌ Do NOT create new features — this is stabilization and documentation
- ❌ Do NOT modify service logic — if a test fails due to a service bug, document as Bug #0XX
- ❌ Do NOT spend >15 minutes on any single test failure
- ❌ Do NOT skip the Spoke 1 Onboarding Document — it is the critical deliverable of Week 44
- ❌ Do NOT assume Spoke 1 has any context — the onboarding doc must stand alone
- ❌ Do NOT update main branch — all work stays on develop

## Files Created / Modified

### Week 43 — Modified
- `src/models/dispatch.py` (if Dispatch.bid bug still exists)
- `src/tests/test_*.py` (any test files requiring fixes or skip-marks)
- `CLAUDE.md` (version bump to v0.9.17-alpha, test counts)
- `CHANGELOG.md` (Week 43 entry)

### Week 44 — Created
- `docs/phase7/PHASE7_RETROSPECTIVE.md` (NEW)
- `docs/handoffs/SPOKE1_ONBOARDING_CONTEXT.md` (NEW — CRITICAL)

### Week 44 — Modified
- `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md`
- `docs/IP2A_MILESTONE_CHECKLIST.md`
- `docs/IP2A_BACKEND_ROADMAP.md`
- `CLAUDE.md` (version bump to v0.9.18-alpha)
- `CHANGELOG.md` (Week 44 entry)

---

## Documentation Mandate

> Make sure to update *ANY* & *ALL* documents to track our progress and for the historical record located in the directory /app/* OR /app/docs/* as necessary. Including ADR's, bug log, etc.

---

## Session Summary Template

```markdown
## Session: Weeks 43–44 — Test Validation & Phase 7 Close-Out
**Date:** [DATE]
**Duration:** [X] hours
**Spoke:** Spoke 2 (Operations)
**Starting Version:** v0.9.16-alpha
**Ending Version:** v0.9.18-alpha

### Week 43 Results
- Baseline test count: [X] total, [X] passing, [X] failing, [X] skipped
- Final test count: [X] total, [X] passing, [X] failing, [X] skipped
- Fixes applied: [list]
- Bugs documented: [Bug #0XX list]
- Dispatch.bid bug status: [fixed/already fixed/still present]

### Week 44 Results
- Report inventory: [X] of 85 reports marked with implementation status
- Phase 7 retrospective: created at docs/phase7/PHASE7_RETROSPECTIVE.md
- Spoke 1 onboarding doc: created at docs/handoffs/SPOKE1_ONBOARDING_CONTEXT.md
- Documents updated: [list all modified docs]

### Cross-Cutting Changes
- [List any changes to shared files: main.py, conftest.py, base templates]
- Hub handoff needed: [yes/no — describe if yes]

### Blockers for Next Sprint
- [Any issues that affect Week 45–46]
```

---

*Spoke 2: Operations — Weeks 43–44 Instruction Document*
*Generated: February 6, 2026*
