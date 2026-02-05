# Claude Code Instructions: Post-Diagnostic Test Cleanup + ADR-018 Staging

**Created:** February 5, 2026
**Source:** Hub → Spoke 2 Handoff (Post-Diagnostic Test Cleanup)
**Context:** UnionCore (IP2A-Database-v2) — IBEW Local 46
**Estimated Time:** 1.5–2 hours
**Branch:** `develop`
**Spoke:** Spoke 2 (Operations)

---

## ⚠️ SCOPE BOUNDARIES — READ FIRST

**DO:**
- Skip-mark Stripe tests (they're deprecated — ADR-018)
- Fix the Dispatch.bid relationship bug (blocks 25 tests)
- Apply Phase 7 Alembic migrations (tables don't exist in DB yet)
- Fix miscellaneous frontend test failures
- Stage ADR-018 in `docs/decisions/`
- Update ADR-013 status to "Superseded by ADR-018"
- Update `docs/decisions/README.md` with ADR-018 entry
- Update documentation and test counts

**DO NOT:**
- Write any Square integration code
- Remove Stripe source code (that happens during Square migration later)
- Create new Phase 7 Alembic migrations
- Modify business logic to make tests pass — flag those for review
- Touch grant services test failure (1 test — separate investigation)

---

## Pre-Flight

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
```

Run full test suite and **capture the output**. Record total/passed/failed/errors/skipped counts.

```bash
pytest -v --tb=short 2>&1 | tee /tmp/pre-cleanup-test-results.txt
tail -20 /tmp/pre-cleanup-test-results.txt
```

> **IMPORTANT:** Record the exact test counts BEFORE any changes. We need a before/after comparison for the session log.

---

## Phase 1: Fix Dispatch.bid Relationship Bug (CRITICAL — Unblocks 25 Tests)

**Problem:** SQLAlchemy cannot determine join condition for `Dispatch.bid` relationship because there are multiple foreign keys pointing to the same table (or ambiguous paths).

**File:** `src/models/dispatch.py`

**Error:** `Could not determine join condition between parent/child tables on relationship Dispatch.bid`

**Fix:** Add explicit `foreign_keys` parameter to the `Dispatch.bid` relationship:

```python
bid = relationship("JobBid", foreign_keys=[bid_id], back_populates="dispatch")
```

### Steps:

1. Open `src/models/dispatch.py`
2. Find the `bid` relationship definition on the `Dispatch` model
3. Add `foreign_keys=[bid_id]` to the relationship call
4. Check if `JobBid` model has a corresponding `back_populates="dispatch"` relationship. If not, add it:
   ```python
   # In src/models/job_bid.py (or wherever JobBid is defined)
   dispatch = relationship("Dispatch", back_populates="bid", uselist=False)
   ```
5. Verify the fix compiles:
   ```bash
   python -c "from src.models.dispatch import Dispatch; print('OK')"
   ```

### Verification:

```bash
pytest src/tests/test_dispatch_frontend.py -v --tb=short
```

All 29 dispatch frontend tests should now run (previously 2 passing, 27 blocked).

---

## Phase 2: Skip-Mark Stripe Tests

**Rationale:** Stripe is being replaced by Square (ADR-018, accepted Feb 5, 2026). These tests are dead code. Skip them so they don't pollute the test results.

### Steps:

1. **Find all Stripe test files:**
   ```bash
   find src/tests -name "*stripe*" -type f
   ```

2. **Add module-level skip marker** to the TOP of each Stripe test file, right after the imports:
   ```python
   import pytest

   pytestmark = pytest.mark.skip(
       reason="Stripe deprecated — migrating to Square (ADR-018). Remove with Square migration."
   )
   ```

3. **Also search for Stripe tests embedded in other test files:**
   ```bash
   grep -rn "stripe" src/tests/ --include="*.py" -l
   ```
   If any non-Stripe test files contain Stripe-specific test functions, add `@pytest.mark.skip(reason="Stripe deprecated — ADR-018")` to those individual functions instead.

### Verification:

```bash
pytest -v --tb=short 2>&1 | grep -i stripe
```

All Stripe tests should show as `SKIPPED`, not `FAILED` or `ERROR`.

---

## Phase 3: Apply Phase 7 Alembic Migrations

**Rationale:** Phase 7 models, services, and API routers are written. Tests reference the tables. But the tables don't physically exist in the database yet because migrations haven't been applied.

### Steps:

1. **Check current migration state:**
   ```bash
   alembic current
   alembic history --verbose | head -30
   ```

2. **Check for pending migrations:**
   ```bash
   alembic heads
   ```

3. **Apply pending migrations:**
   ```bash
   alembic upgrade head
   ```

4. **⛔ IF MIGRATIONS FAIL:**
   - **STOP.** Do not force-create tables manually.
   - Document the exact error message.
   - Check if the migration file references tables or columns that don't exist yet.
   - Check if enum types need to be created before the migration runs.
   - Check for circular dependencies between migration files.
   - If the issue is a missing enum type, check `src/db/enums/phase7_enums.py` and ensure the migration creates the enum BEFORE the table that uses it.
   - Document everything and move on to Phase 4. We'll escalate migration issues separately.

5. **Verify Phase 7 tables exist:**
   ```bash
   python -c "
   from src.database import engine
   from sqlalchemy import inspect
   inspector = inspect(engine)
   tables = inspector.get_table_names()
   phase7_tables = ['referral_books', 'book_registrations', 'registrations',
                    'registration_activity', 'registration_activities',
                    'labor_requests', 'job_requests', 'job_bids', 'web_bids',
                    'dispatches']
   for t in phase7_tables:
       status = '✅' if t in tables else '❌'
       if t in tables:
           print(f'{status} {t}')
   print(f'\nAll tables: {sorted([t for t in tables if not t.startswith(\"alembic\")])[:20]}...')
   "
   ```

   > **Note:** Table names may vary (e.g., `book_registrations` vs `registrations`, `labor_requests` vs `job_requests`). Check the actual model definitions to confirm table names.

### Verification:

```bash
pytest src/tests/test_referral_frontend.py -v --tb=short
pytest src/tests/test_dispatch_frontend.py -v --tb=short
```

Phase 7 tests that were failing with "table does not exist" errors should now pass (or fail for legitimate reasons).

---

## Phase 4: Investigate and Fix Miscellaneous Frontend Test Failures

**Rationale:** These are legitimate test failures — not blocked by architecture. Likely root causes: schema drift, stale fixtures, enum mismatches, or stale route references.

### Process for EACH failing test file:

1. Run the file with full traceback:
   ```bash
   pytest src/tests/TEST_FILE.py -v --tb=long 2>&1 | tee /tmp/TEST_FILE_results.txt
   ```

2. **Categorize each failure** into one of:
   - **Schema drift** — Test expects a column/field that was renamed or removed
   - **Missing fixture** — Test depends on a fixture that doesn't exist or has changed signature
   - **Stale route** — Test hits a URL that was renamed or moved
   - **Enum mismatch** — Test uses an enum value that changed
   - **Actual bug** — The application code is wrong (flag for review, do NOT modify business logic)
   - **Blocked by Phase 7** — Should be resolved by Phase 3 above

3. **Fix what's fixable.** If the fix is straightforward (typo, renamed field, stale URL), make the fix. If it requires changing business logic, document it and skip.

### Files to investigate (from diagnostic report):

```bash
# Run each individually
pytest src/tests/test_frontend.py -v --tb=long
pytest src/tests/test_members.py -v --tb=long
pytest src/tests/test_setup.py -v --tb=long
pytest src/tests/test_audit_frontend.py -v --tb=long
```

### Document your findings in this format:

```
File: src/tests/test_XXX.py
Test: test_function_name
Category: [schema drift | missing fixture | stale route | enum mismatch | actual bug | blocked]
Root Cause: [description]
Fix Applied: [yes/no — what was changed]
```

---

## Phase 5: Stage ADR-018 (Square Payment Integration)

### Steps:

1. **Copy ADR-018 to the decisions directory:**
   ```bash
   cp /path/to/ADR-018-square-payment-integration.md docs/decisions/ADR-018-square-payment-integration.md
   ```
   > The user will provide the file or it may already be in the repo root. Find it:
   ```bash
   find . -name "ADR-018*" -type f 2>/dev/null
   ```

2. **Update ADR-013 status to "Superseded":**
   Open `docs/decisions/ADR-013-stripe-payment-integration.md` and change the Status line:
   ```
   **Status:** Superseded by ADR-018 (Square Payment Integration)
   ```
   Add a note at the top of the Context or Decision section:
   ```markdown
   > **⚠️ SUPERSEDED:** This ADR has been superseded by [ADR-018](ADR-018-square-payment-integration.md).
   > Stripe is being replaced by Square. See ADR-018 for rationale and migration plan.
   ```

3. **Update `docs/decisions/README.md`:**
   Add ADR-018 to the index table:
   ```markdown
   | ADR-018 | Square Payment Integration | Accepted | Supersedes ADR-013. Square replaces Stripe for unified payment ecosystem. |
   ```
   Update ADR-013's row to show "Superseded" status.

---

## Phase 6: Final Test Suite Run + Documentation Updates

### Full test run:

```bash
pytest -v --tb=short 2>&1 | tee /tmp/post-cleanup-test-results.txt
tail -30 /tmp/post-cleanup-test-results.txt
```

Record final counts: total, passed, failed, errors, skipped.

### Update test counts in ALL of these locations:

1. **`CLAUDE.md`** — TL;DR section and Current State table
2. **`docs/IP2A_BACKEND_ROADMAP.md`** — Executive Summary (`Total Tests` line) and Known Issues section
3. **`docs/IP2A_MILESTONE_CHECKLIST.md`** — Quick Stats section and Known Issues section
4. **`docs/README.md`** — Current Status table

### Update Known Issues:

If the Dispatch.bid bug is fixed (Phase 1), remove or update the Known Issues section in:
- `docs/IP2A_BACKEND_ROADMAP.md`
- `docs/IP2A_MILESTONE_CHECKLIST.md`

### Create session log:

Create `docs/reports/session-logs/2026-02-05-test-cleanup-adr018-staging.md` with:
- Session date and duration
- Pre-cleanup test counts
- Post-cleanup test counts
- Each fix applied (file, change, reason)
- ADR-018 staging confirmation
- Any unresolved issues escalated to Hub
- Files changed list

---

## Phase 7: Commit

```bash
git add -A
git status  # Review what's staged

git commit -m "fix: test cleanup — Dispatch.bid bug, skip Stripe, apply Phase 7 migrations, stage ADR-018

- Fixed Dispatch.bid relationship bug (foreign_keys parameter) — unblocks 25+ tests
- Skip-marked Stripe test files (ADR-018: Square replacing Stripe)
- Applied Phase 7 Alembic migrations (tables now exist in DB)
- Fixed miscellaneous frontend test failures (schema drift, stale fixtures)
- Staged ADR-018 (Square Payment Integration) in docs/decisions/
- Updated ADR-013 status to 'Superseded by ADR-018'
- Updated test counts across all documentation
- Created session log

Test results: [PASSED]/[TOTAL] passing, [SKIPPED] skipped (Stripe)
"

git push origin develop
```

---

## Expected Outcomes

| Metric | Before (Diagnostic) | Expected After |
|--------|---------------------|----------------|
| Passed | ~495 | 530-560+ |
| Failed | ~65 | 10-20 |
| Errors | ~30 | 0-5 |
| Skipped | 0 | ~30 (Stripe) |
| Pass Rate | ~84% | 90%+ |

---

## Post-Session Checklist

- [ ] Dispatch.bid relationship bug fixed
- [ ] All Stripe test files skip-marked
- [ ] Phase 7 migrations applied (or failure documented)
- [ ] Miscellaneous test failures investigated and fixed where possible
- [ ] ADR-018 staged in `docs/decisions/`
- [ ] ADR-013 marked as superseded
- [ ] `docs/decisions/README.md` updated
- [ ] Test counts updated in CLAUDE.md, Roadmap, Checklist, README
- [ ] Known Issues section updated (Dispatch.bid fix)
- [ ] Session log created
- [ ] All changes committed and pushed to `develop`
- [ ] List of ALL changed files provided to user

---

## Files This Session Will Touch

### Modified:
- `src/models/dispatch.py` — Dispatch.bid relationship fix
- `src/models/job_bid.py` — back_populates for dispatch (if needed)
- `src/tests/test_stripe_integration.py` — skip marker
- `src/tests/test_stripe_frontend.py` — skip marker
- `src/tests/test_frontend.py` — fix failures (if applicable)
- `src/tests/test_members.py` — fix failures (if applicable)
- `src/tests/test_setup.py` — fix failures (if applicable)
- `src/tests/test_audit_frontend.py` — fix failures (if applicable)
- `docs/decisions/ADR-013-stripe-payment-integration.md` — superseded status
- `docs/decisions/README.md` — ADR-018 entry
- `CLAUDE.md` — test counts, known issues
- `docs/IP2A_BACKEND_ROADMAP.md` — test counts, known issues
- `docs/IP2A_MILESTONE_CHECKLIST.md` — test counts, known issues
- `docs/README.md` — test counts

### Created:
- `docs/decisions/ADR-018-square-payment-integration.md`
- `docs/reports/session-logs/2026-02-05-test-cleanup-adr018-staging.md`

---

*Claude Code Post-Diagnostic Test Cleanup Instructions — February 5, 2026*
*Source: Hub → Spoke 2 Handoff*
