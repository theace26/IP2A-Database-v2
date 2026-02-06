# Week 39: Bug Squash & Test Stabilization Sprint

**Type:** Spoke 2 → Claude Code Instruction Document
**Sprint:** Week 39
**Objective:** Stabilize test suite after 3-week P1 report sprint, achieve ≥98% pass rate
**Estimated Effort:** 5-6 hours
**Priority:** HIGH — Consolidation before next feature work
**Version at Start:** v0.9.12-alpha

---

## Context

Weeks 36-38 shipped 30 P1 reports (30 endpoints, 30 PDF templates, 60 new tests). Pass rate dropped from ~98.5% (Week 35) to ~96% (Week 38). This sprint fixes regressions and addresses lingering test debt before P2 reports or sub-phase 7a work begins.

**Estimated Starting State (VERIFY during Pre-Flight — these are projections, not confirmed):**
- ~620-660 total tests (verify with pytest)
- ~16 skipped tests (infrastructure-dependent: S3/MinIO, WeasyPrint system libs)
- Stripe code fully removed (Week 35) — no Stripe skip markers should remain
- Railway deployment live

**Historical Context (Week 30/35 — reference only, do NOT assume these still exist):**
Previous bug squash sprints addressed fixture isolation, member notes visibility, dues unique constraints, and referral frontend rendering. Week 35 specifically targeted these categories. If similar patterns appear during triage, the historical context may help diagnose — but let the Phase 1 triage discover what's actually failing. Do not go hunting for ghosts.

**Target:** ≥98% pass rate on non-skipped tests (matching Week 35 baseline)

---

## Pre-Flight Checklist

Before making ANY changes, establish the baseline. This is the single most important step.

```bash
# 1. Pull latest from develop
git checkout develop
git pull origin develop

# 2. Ensure database is current
alembic upgrade head

# 3. Run FULL test suite — capture baseline
pytest -v --tb=short 2>&1 | tee /tmp/week39_baseline.txt

# 4. Extract summary stats
echo "=== BASELINE SUMMARY ==="
grep -E "passed|failed|error|skipped" /tmp/week39_baseline.txt | tail -5

# 5. Extract ALL failing test names
pytest -v --tb=no 2>&1 | grep -E "FAILED|ERROR" | sort > /tmp/week39_failures.txt
cat /tmp/week39_failures.txt
wc -l /tmp/week39_failures.txt
```

### ⛔ STOP AND RECORD — Do Not Proceed Without This

Document the exact baseline in your session summary before touching any code:

```
- Total tests: ___
- Passing: ___
- Failing: ___
- Errors: ___
- Skipped: ___
- Pass rate (non-skipped): ___
```

These numbers are the single source of truth. All projections in this document are estimates — your pytest output is reality.

### Decision Gate: Early Exit

**If baseline pass rate is already ≥98% with ≤5 total failures:**
Skip Phases 2-3. Go directly to fixing each failure individually, then run the Skipped Test Audit (Phase 5), document (Phase 6), and ship. Don't burn 5 hours on a full 6-phase sprint for 3 fixes.

**If baseline pass rate is ≥98% with ZERO failures:**
Skip to Phase 5 (Skipped Test Audit) and Phase 6 (Documentation). Commit the clean baseline confirmation and move on.

---

## Phase 1: Triage & Categorize (30 minutes)

**Goal:** Sort every failing test into a category so we can fix them in the right order.

### Step 1.1: Categorize Each Failure

For each test in `/tmp/week39_failures.txt`, determine its category:

| Category | Pattern | Fix Approach | Priority |
|----------|---------|--------------|----------|
| A: Fixture Isolation | `UniqueViolation`, `IntegrityError`, duplicate key | Add cleanup fixtures, use UUID-based test data | HIGH — Fix first, unblocks others |
| B: Schema Drift | `AttributeError: type object 'Model' has no attribute 'field'` | Correct field references | HIGH — Simple but critical |
| C: Auth/Session | `401 Unauthorized`, `302` redirect in test | Fix fixture auth setup, use correct auth method | MEDIUM |
| D: Template Rendering | `AssertionError: 'expected text' not in response` | Fix template data binding or assertions | MEDIUM |
| E: Import/Module | `ImportError`, `ModuleNotFoundError`, `NameError` | Fix imports | HIGH — Usually trivial |
| F: New Regressions (Weeks 36-38) | Tests in `test_referral_reports*.py` or report-related | Investigate individually | HIGH — These are fresh |
| G: Flaky/Timing | Passes alone, fails in suite | Fixture ordering, add `yield` cleanup | LOW — Skip-mark if stubborn |
| H: Report Data Gaps | Report test expects content but gets empty PDF/Excel | Fixture doesn't seed enough referral data for the report query | HIGH — Most likely new category |

### Step 1.2: Create Triage Report

```bash
# Group failures by test file
cat /tmp/week39_failures.txt | awk -F'::' '{print $1}' | sort | uniq -c | sort -rn > /tmp/week39_by_file.txt
cat /tmp/week39_by_file.txt
```

Record the triage in your session summary as a table:

```markdown
| # | Test File | Failures | Category | Root Cause (suspected) |
|---|-----------|----------|----------|----------------------|
| 1 | test_xxx.py | 5 | A | Fixture collision |
| 2 | test_yyy.py | 3 | H | Report query returns empty — missing seed data |
```

**Decision Gate:** If total failures are ≤5, skip to Phase 3 (individual fixes). If >5, proceed through Phases 2-4 in order.

---

## Phase 2: Fixture Isolation Fixes (Category A — 60-90 minutes)

**These are the highest-value fixes because fixture collisions cascade.** One bad fixture can cause 5-10 downstream failures.

### Known Pattern: Unique Constraint Violations

**Root Cause:** Tests create records with hardcoded identifiers that collide when tests run in sequence.

**Fix Pattern:**
```python
# BAD — hardcoded, will collide
test_book = ReferralBook(book_code="TEST_WIRE", ...)

# GOOD — UUID-unique per test run
import uuid
test_book = ReferralBook(book_code=f"TEST_WIRE_{uuid.uuid4().hex[:8]}", ...)
```

### Known Pattern: Missing Cleanup Fixtures

**Root Cause:** Test data persists between test functions when using module/session-scoped fixtures.

**Fix Pattern:**
```python
@pytest.fixture(autouse=True)
def cleanup_test_data(db):
    """Clean up test data after each test."""
    yield
    # Delete in reverse dependency order (children before parents)
    db.query(RegistrationActivity).filter(
        RegistrationActivity.notes.like("TEST_%")
    ).delete(synchronize_session=False)
    db.query(BookRegistration).filter(
        BookRegistration.book_id.in_(
            db.query(ReferralBook.id).filter(ReferralBook.book_code.like("TEST_%"))
        )
    ).delete(synchronize_session=False)
    db.commit()
```

### Step 2.1: Fix Dues Test Collisions (if still present)

If dues tests fail with unique constraint on `(year, month)`:

```bash
pytest src/tests/test_dues*.py -v --tb=short 2>&1 | grep -E "FAILED|ERROR"
```

Fix: Add cleanup fixture or use unique year values (e.g., `2090 + random.randint(1,9)`).

### Step 2.2: Fix Phase 7 Model Test Isolation (if still present)

```bash
pytest src/tests/test_phase7_models.py -v --tb=short 2>&1
```

If these show `UniqueViolation` errors:
1. Ensure all test codes use UUID suffixes
2. Ensure cleanup runs in correct dependency order
3. Verify `autouse=True` cleanup fixture exists and fires

### Step 2.3: Verify Cascade Effect

After fixing Category A, re-run the full suite — fixture fixes often resolve other categories:

```bash
pytest -v --tb=short 2>&1 | tee /tmp/week39_post_fixtures.txt
grep -E "passed|failed|error|skipped" /tmp/week39_post_fixtures.txt | tail -5
```

**If pass rate is now ≥98%:** Skip to Phase 5 (Skipped Test Audit). Don't over-engineer.

---

## Phase 3: Schema Drift & Import Fixes (Categories B, E — 30-45 minutes)

These are typically one-line fixes with high impact.

### Step 3.1: Schema Drift (Category B)

For any `AttributeError` on model fields:

1. Check the actual model definition: `grep -n "field_name" src/models/relevant_model.py`
2. Check the migration: `grep -rn "field_name" alembic/versions/`
3. Fix the reference to match the model (the model is the source of truth)

### Step 3.2: Import Fixes (Category E)

For any `ImportError` or `NameError`:

```bash
# Find the failing import
pytest src/tests/test_xxx.py -v --tb=long 2>&1 | grep -A5 "ImportError\|NameError"
```

Fix the import path. Common causes:
- Module renamed during refactor
- Circular import from new report modules
- Missing `__init__.py` entry

---

## Phase 4: Auth, Template, Report & Regression Fixes (Categories C, D, F, H — 60-90 minutes)

### Step 4.1: Auth/Session Failures (Category C)

For tests returning 401 or 302 unexpectedly:

**Diagnosis:**
```bash
# Check if test uses correct auth fixture
grep -n "auth_headers\|auth_cookies\|client" src/tests/test_failing_file.py
```

**Common fixes:**
- Test declares `auth_headers` but actually needs `auth_cookies` (frontend routes use cookies)
- Test doesn't pass auth at all — add the appropriate fixture parameter
- Cookie token expired in test setup — ensure token generation happens fresh per test

### Step 4.2: Template Rendering (Category D)

For `AssertionError` where expected text isn't in response:

**Diagnosis:**
```bash
# Run single test with full output
pytest src/tests/test_xxx.py::test_specific_function -v --tb=long -s 2>&1
```

**Common fixes:**
- Template text changed during report sprint (heading renamed, stat label moved)
- Stats calculation returns different format than test expects (e.g., `0` vs `"0"`)
- HTMX partial returns fragment, test expects full page
- DaisyUI class change altered rendered structure

**Important:** If a template was intentionally changed during Weeks 36-38, update the TEST to match the new template — don't revert the template.

### Step 4.3: Week 36-38 Report Regressions (Category F)

These are the freshest failures and most likely to be simple oversights.

```bash
# Run just the report tests
pytest src/tests/test_referral_reports*.py -v --tb=short 2>&1
pytest src/tests/test_report*.py -v --tb=short 2>&1
```

Common report test issues:
- Missing fixture data for report queries (report returns empty, test expects content)
- PDF generation test fails without WeasyPrint system libs (should be skip-marked, not failing)
- Excel generation test expects specific cell value that varies by test data

### Step 4.4: Report Data Gaps (Category H)

**This is the most likely new failure category after the P1 report sprint.**

Report services query across `referral_books`, `book_registrations`, `dispatches`, `labor_requests`, and `registration_activities`. If the test fixtures don't seed these tables with enough data, report endpoints will return 200 OK but produce empty results, causing assertion failures like:

- `assert "Wire Seattle" in response.text` → fails because no referral book was seeded
- `assert len(rows) > 0` → fails because no dispatch records exist in test DB

**Diagnosis:**
```bash
# Check what fixtures the report test file uses
grep -n "def test_\|@pytest.fixture\|conftest" src/tests/test_referral_reports*.py | head -30
```

**Fix:** Ensure report test fixtures create at minimum:
- 1 referral book (with valid book_code, classification)
- 2+ book registrations (with APN as DECIMAL, proper status)
- 1 labor request (with employer reference)
- 1 dispatch (linking registration → labor_request → member → employer)
- 1 registration activity (for activity-based reports)

Use the UUID pattern for all identifiers to avoid collisions.

### Step 4.5: WeasyPrint Skip Marking

**For any test that requires WeasyPrint/S3 infrastructure and is FAILING (not just slow):** Skip-mark it properly. Do NOT use `shutil.which()` — it detects the binary but not the system libraries (cairo, pango) that actually cause failures.

**Correct pattern:**
```python
import pytest

try:
    import weasyprint
    HAS_WEASYPRINT = True
except (ImportError, OSError):
    HAS_WEASYPRINT = False

@pytest.mark.skipif(not HAS_WEASYPRINT, reason="WeasyPrint not available in test environment")
def test_pdf_generation():
    ...
```

---

## Phase 5: Skipped Test Audit (20-30 minutes)

### Step 5.1: Inventory All Skipped Tests

```bash
pytest -v --tb=no 2>&1 | grep "SKIPPED" > /tmp/week39_skipped.txt
cat /tmp/week39_skipped.txt
wc -l /tmp/week39_skipped.txt
```

### Step 5.2: Classify Each Skip

| Skip Reason | Action |
|-------------|--------|
| S3/MinIO not configured | Keep skipped — infrastructure dependency |
| WeasyPrint not installed / OSError | Keep skipped — infrastructure dependency |
| Stripe-related | **These should NOT exist** — Stripe was fully removed in Week 35. DELETE the test function/file entirely. |
| "TODO" or "not implemented" | Evaluate: is the feature now implemented? If yes, unskip and fix. If no, keep. |
| Flaky/timing | Attempt to fix. If still flaky after 10 min effort, keep skipped with clear reason. |

### Step 5.3: Stripe Verification (should take <2 minutes)

Week 35 was a dedicated Stripe removal sprint. This is a confirmation check, not a discovery exercise.

```bash
grep -rn "stripe\|Stripe" src/tests/ --include="*.py" | grep -v __pycache__
```

**Expected:** Zero results. If anything surfaces, it's a Week 35 miss — delete the code, don't skip-mark it.

---

## Phase 6: Final Verification & Documentation (30 minutes)

### Step 6.1: Full Suite Final Run

```bash
pytest -v --tb=short 2>&1 | tee /tmp/week39_final.txt
grep -E "passed|failed|error|skipped" /tmp/week39_final.txt | tail -5
```

### Step 6.2: Calculate Final Stats

```
Total: ___
Passing: ___
Failing: ___
Errors: ___
Skipped: ___
Pass Rate (non-skipped): ___ %
```

**Success Criteria:**
- [ ] Pass rate ≥98% on non-skipped tests
- [ ] Zero new skip markers added (only infrastructure-dependent skips retained)
- [ ] All Stripe code remnants removed (if any found)
- [ ] No Category A (fixture isolation) failures remaining

**If pass rate is still <98%:** Document the remaining failures with root cause analysis. Flag any that require architectural changes (e.g., async/sync session mismatches that need service layer refactoring) vs. simple test fixes. Do NOT force-skip tests to hit the target — that's cheating.

### Step 6.3: Update Project Documentation

**CLAUDE.md updates (MANDATORY):**
```
- Update "Weeks 20-XX" to include Week 39
- Update test counts and pass rate with verified numbers from Step 6.2
- Update date
```

**CHANGELOG.md — Add entry:**
```markdown
### Fixed (February [DATE], 2026 — Week 39: Bug Squash Sprint)
- **Test stabilization after P1 report sprint (Weeks 36-38)**
  * [List specific fixes by category]
  * Pass rate: [before]% → [after]%
  * [X] fixture isolation fixes, [Y] schema corrections, [Z] auth/template fixes
- **Skipped test audit:** [results]
- **Target:** ≥98% pass rate — [ACHIEVED/NOT ACHIEVED]
```

**Session log:**
Create `docs/reports/session-logs/2026-02-[DATE]-week39-bug-squash.md` with the Session Summary Template (see below).

**Milestone Checklist update:**
- Add Week 39 row to the Phase 7 table
- Update Quick Stats with verified test counts

**Roadmap update:**
- Update test count in Executive Summary
- Add Week 39 to version history

### Step 6.4: Commit and Push

**Two commits maximum:**

```bash
# Commit 1: All test fixes
git add -A
git commit -m "fix: Week 39 bug squash — test pass rate [BEFORE]% → [AFTER]%

- [X] Category A fixes (fixture isolation)
- [Y] Category B/E fixes (schema drift, imports)
- [Z] Category C/D fixes (auth, templates)
- [W] Category F/H fixes (report regressions, data gaps)
- Stripe remnants: [none found / X items removed]
- Ref: Week 39 Bug Squash Sprint"

# Commit 2: Documentation
git add -A
git commit -m "docs: Week 39 bug squash session documentation

- Updated CLAUDE.md, CHANGELOG.md, Milestone Checklist, Roadmap
- Created session log
- Pass rate: [X]% → [Y]%"

git push origin develop
```

---

## Anti-Patterns — DO NOT

- ❌ **DO NOT** create new features, endpoints, or templates during this sprint
- ❌ **DO NOT** skip-mark tests just to hit the pass rate target
- ❌ **DO NOT** modify business logic in services — test fixes only
- ❌ **DO NOT** change model definitions unless correcting an actual bug
- ❌ **DO NOT** start P2 reports "since you have time" — stay disciplined
- ❌ **DO NOT** refactor working code — this is a repair sprint, not a cleanup sprint
- ❌ **DO NOT** change the database migration — if schema is wrong, that's a separate sprint
- ❌ **DO NOT** use `shutil.which("weasyprint")` for skip checks — it doesn't detect missing system libs

## Rules of Engagement

- ✅ **DO** run the full suite after every commit to catch regressions
- ✅ **DO** fix tests in dependency order (fixtures first, then consumers)
- ✅ **DO** document every fix with clear commit messages
- ✅ **DO** investigate before fixing — understand the root cause, don't guess
- ✅ **DO** use the triage categories to stay organized
- ✅ **DO** stop and document if you hit something that needs architectural discussion (flag for Hub)
- ✅ **DO** use the Decision Gates to avoid over-engineering when few failures exist

---

## Escalation to Hub

If during this sprint you encounter any of the following, **STOP and document for Hub review:**

1. **Model definition appears incorrect** (not just a field name typo — an actual design flaw)
2. **Migration needs modification** (never modify applied migrations — needs ADR discussion)
3. **Async/sync architecture conflict** that can't be resolved with test changes
4. **More than 3 tests that need skip-marking** for reasons other than infrastructure dependency
5. **Test count decreases** (we should never lose tests — only fix or legitimately remove dead code)

Document the escalation in the session log with:
- What you found
- Why it can't be fixed in this sprint
- Recommended next steps
- Impact on pass rate if not fixed

---

## Session Summary Template

Copy this into your session log at `docs/reports/session-logs/2026-02-[DATE]-week39-bug-squash.md`:

```markdown
# Week 39: Bug Squash Sprint — Session Summary

**Date:** February [DATE], 2026
**Sprint:** Week 39
**Objective:** Test stabilization after P1 report sprint

## Baseline (Pre-Flight)
- Total: ___  |  Passing: ___  |  Failing: ___  |  Errors: ___  |  Skipped: ___
- Pass Rate: ___% (non-skipped)

## Decision Gate Result
- [ ] Early exit (≤5 failures, ≥98%) — went to individual fix mode
- [ ] Full sprint (>5 failures) — ran all phases

## Triage Results
| Category | Count | Files Affected |
|----------|-------|----------------|
| A: Fixture Isolation | ___ | |
| B: Schema Drift | ___ | |
| C: Auth/Session | ___ | |
| D: Template Rendering | ___ | |
| E: Import/Module | ___ | |
| F: Report Regressions | ___ | |
| G: Flaky/Timing | ___ | |
| H: Report Data Gaps | ___ | |

## Fixes Applied
### Phase 2: Fixture Isolation
- [list fixes]

### Phase 3: Schema Drift / Imports
- [list fixes]

### Phase 4: Auth / Template / Report Fixes
- [list fixes]

### Phase 5: Skipped Test Audit
- Total skipped: ___
- Stripe remnants found: [yes/no — if yes, what was removed]
- Tests unskipped: ___
- Tests deleted: ___

## Final Results
- Total: ___  |  Passing: ___  |  Failing: ___  |  Errors: ___  |  Skipped: ___
- Pass Rate: ___% (non-skipped)
- Target ≥98%: [ACHIEVED / NOT ACHIEVED]

## Remaining Issues (if any)
| Test | Category | Root Cause | Recommended Action |
|------|----------|------------|-------------------|
| | | | |

## Files Modified
- [list all modified files as /dir/file paths]

## Commits
- [list commit hashes and messages]

## Hub Escalations (if any)
- [list items requiring Hub review]
```

---

*Week 39 Bug Squash Sprint — Generated by Hub, Revised February 2026*
*Execute via Claude Code in Spoke 2*
