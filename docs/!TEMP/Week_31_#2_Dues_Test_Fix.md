# Claude Code Instruction Document: Week 31 — Dues Test Fixture Fix

**Sprint:** Week 31 — Work Package 1
**Spoke:** Spoke 2 (Operations)
**Source:** Hub guidance → Spoke 2 generation, February 5, 2026
**Effort:** 15-30 minutes
**Goal:** Fix 4 dues test failures caused by unique constraint collisions
**Expected Result:** +4 passing tests → 521/558 (93.4% pass rate)
**Branch:** `develop`

---

## IMPORTANT: Read Before Starting

1. **Read `CLAUDE.md` first.** It is the project context document.
2. **This is a test-only fix.** Do NOT modify business logic, models, services, or routers.
3. **Do NOT delete or skip-mark tests.** Fix the underlying collision.
4. **Commit when done** with the exact message format specified below.

---

## Context

Week 30 closed at **517/558 passing tests (92.7%)**. Bug #029 fixed 14 field name mismatches in `dispatch_frontend_service.py`. 4 dues tests remain failing due to a test data collision pattern — the same pattern that was fixed for Phase 7 fixtures in Week 29.

### Root Cause

Multiple dues tests insert test data with the same `(year=2093, month=7)` values without cleanup between test runs. When tests execute in parallel or across modules, the second insertion hits the unique constraint on `dues_periods(year, month)`.

---

## Phase 1: Diagnostic (5 minutes)

### Step 1.1: Confirm baseline test count

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
pytest -v --tb=short 2>&1 | tail -20
```

Record the exact counts: `X passed, Y failed, Z skipped, W total`

**Expected baseline:** ~517 passed, ~6 failed (4 dues + others), ~35 skipped, 558 total

### Step 1.2: Isolate the 4 dues failures

```bash
pytest src/tests/test_dues*.py -v 2>&1 | grep -E "(FAILED|ERROR|PASSED)"
```

### Step 1.3: Get the constraint violation details

```bash
pytest src/tests/test_dues*.py -v --tb=long 2>&1 | grep -B 5 -A 10 "constraint\|UniqueViolation\|IntegrityError\|2093"
```

**Document:**
- Which 4 tests are failing?
- What table/constraint is being violated?
- What values are colliding? (Expected: `year=2093, month=7` or similar high-value test data)

### Step 1.4: Find the test data insertion points

```bash
grep -rn "2093\|2090\|2091\|2092" src/tests/test_dues*.py
grep -rn "2093\|2090\|2091\|2092" src/tests/conftest.py
```

Identify every location that inserts dues period test data with year >= 2090.

---

## Phase 2: Fix (10-15 minutes)

### Strategy: Module-scoped cleanup fixture

The proven pattern from Phase 7 test fixes (Week 29): add a cleanup fixture that removes test data BEFORE the module runs, preventing collision from prior test runs.

### Step 2.1: Determine where to place the fixture

Check if dues tests have their own conftest or use the global one:

```bash
ls src/tests/conftest*.py
ls src/tests/test_dues*.py
head -30 src/tests/test_dues*.py  # Check imports and existing fixtures
```

### Step 2.2: Add the cleanup fixture

**Option A (preferred): Add to the dues test file directly**

If the dues tests are in a single file (e.g., `test_dues.py`), add at the top of that file:

```python
import pytest
from sqlalchemy import text


@pytest.fixture(autouse=True, scope="module")
def clean_dues_test_data(db_session):
    """Remove stale dues test data to prevent unique constraint collisions.
    
    Test dues periods use year >= 2090 to avoid collision with real data.
    This fixture cleans up leftover test data from previous runs.
    Added: Week 31 (Category 4 fix — same pattern as Phase 7 Week 29 fixtures).
    """
    # Delete in dependency order to respect foreign keys
    db_session.execute(text("DELETE FROM dues_adjustments WHERE period_id IN (SELECT id FROM dues_periods WHERE year >= 2090)"))
    db_session.execute(text("DELETE FROM dues_payments WHERE period_id IN (SELECT id FROM dues_periods WHERE year >= 2090)"))
    db_session.execute(text("DELETE FROM dues_periods WHERE year >= 2090"))
    db_session.commit()
    yield
    # Post-test cleanup (belt and suspenders)
    db_session.execute(text("DELETE FROM dues_adjustments WHERE period_id IN (SELECT id FROM dues_periods WHERE year >= 2090)"))
    db_session.execute(text("DELETE FROM dues_payments WHERE period_id IN (SELECT id FROM dues_periods WHERE year >= 2090)"))
    db_session.execute(text("DELETE FROM dues_periods WHERE year >= 2090"))
    db_session.commit()
```

**Option B: Add to conftest.py if dues tests span multiple files**

Same fixture code, but place it in `src/tests/conftest.py` with a module scope. Use this only if there are multiple `test_dues_*.py` files.

**Option C: Use unique test data per test**

If the cleanup approach causes issues with other fixtures, modify the failing tests to use unique year values:

```python
import uuid

def _unique_year():
    """Generate a unique test year in the 2090-2099 range."""
    return 2090 + (hash(uuid.uuid4()) % 10)
```

Replace hardcoded `year=2093` with `year=_unique_year()` in each test.

### Step 2.3: Important — Check for foreign key dependencies

Before committing to Option A, verify the FK chain:

```bash
grep -rn "dues_periods\|period_id" src/models/dues*.py | grep -i "foreign\|relationship"
```

The DELETE statements must respect the dependency order:
1. `dues_adjustments` (references `dues_periods`)
2. `dues_payments` (references `dues_periods`)
3. `dues_periods` (the parent)

If there are additional child tables, add them to the cleanup sequence.

---

## Phase 3: Verification (5 minutes)

### Step 3.1: Run dues tests only

```bash
pytest src/tests/test_dues*.py -v
```

**All 4 previously failing tests must now pass.** No new failures in this file.

### Step 3.2: Run full test suite

```bash
pytest -v --tb=short 2>&1 | tail -20
```

**Expected:** 521 passed (was 517), 0 new failures, same skip count.

### Step 3.3: Verify no regressions

Compare the full list of passing tests before and after. No test that was passing should now be failing.

```bash
# Quick regression check
pytest -v 2>&1 | grep "FAILED" | sort
```

The FAILED list should be shorter than or equal to the baseline (minus the 4 dues tests you fixed).

---

## Phase 4: Documentation (5 minutes)

### Step 4.1: Update CLAUDE.md

Find the "Remaining Issues" or test status section in `CLAUDE.md` and:
- Update pass count: 517 → 521
- Update pass rate: 92.7% → 93.4%
- Remove or update the Category 4 (dues test) entry
- Add a note: "Category 4 fixed: Week 31 — cleanup fixture for dues test data collision"

### Step 4.2: Update CHANGELOG.md

Add under the current version section (or create a new entry):

```markdown
### Fixed
- Dues test fixture collision — added module-scoped cleanup for `year >= 2090` test data (Category 4, 4 tests)
```

### Step 4.3: Commit

```bash
git add -A
git commit -m "fix(dues): add cleanup fixture for test data collision (Category 4)

- Added module-scoped cleanup fixture removing stale dues_periods test data
- Fixes 4 dues test failures caused by unique constraint on (year, month)
- Same pattern as Phase 7 fixture fixes from Week 29
- Test results: 521/558 passing (93.4%), up from 517/558 (92.7%)
"
git push origin develop
```

---

## Files Expected to Change

```
src/tests/test_dues.py          — Added cleanup fixture (or test_dues_*.py if multiple files)
CLAUDE.md                       — Updated test counts and remaining issues
CHANGELOG.md                    — Added fix entry
```

If Option B was used: `src/tests/conftest.py` instead of the test file directly.

---

## Acceptance Criteria

- [ ] All 4 dues test failures resolved
- [ ] No regressions — no previously passing tests now fail
- [ ] Pass rate ≥ 93.4% (521/558)
- [ ] CLAUDE.md updated with new test counts
- [ ] CHANGELOG.md updated with fix entry
- [ ] Committed to develop branch with descriptive message
- [ ] `git push origin develop` completed

---

## Troubleshooting

**If the cleanup fixture causes NEW failures:**
The cleanup may be deleting seed data that other tests depend on. In that case:
1. Revert the fixture
2. Use Option C (unique years per test) instead
3. Document which tests depend on the seed data

**If there are more than 4 dues failures:**
The baseline count may have shifted since the guidance doc was written. Fix all constraint-related dues failures, not just 4.

**If the constraint violation is on a different table:**
Adjust the DELETE statements to target the actual colliding table. The year >= 2090 range should still be safe for isolating test data.

---

**End of Instruction Document**
*Generated by Spoke 2 — February 5, 2026*
*For execution via Claude Code*
