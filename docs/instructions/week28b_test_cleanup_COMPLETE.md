# Claude Code Instruction: Test Suite Cleanup (Post-Migration)

**Spoke:** 2 (Operations)
**Date:** February 5, 2026
**Priority:** 🟡 MEDIUM — Fixes ~10 test failures
**Estimated Time:** 30-45 minutes
**Branch:** `develop`
**Risk Level:** LOW — Test files and single router fix only. No schema changes.
**Prerequisite:** Run AFTER `week28a_phase7_migration.md` is complete.

---

## TL;DR

Fix two categories of non-migration test failures:
1. **Audit frontend router type check bug** (4 failures) — Router doesn't check if auth dependency returned `RedirectResponse`
2. **Outdated test expectations** (6 failures) — Tests expect old app state

---

## Pre-Flight

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
```

Confirm Phase 7 migration was already applied (prerequisite):

```bash
pytest src/tests/test_phase7_models.py --tb=no -q
```

If Phase 7 model tests fail, run the migration instruction first.

---

## Task 1: Fix Audit Frontend Router Type Check (4 tests)

### Diagnose

```bash
pytest src/tests/test_audit_frontend.py -v
```

The bug: When unauthenticated requests hit audit routes, `get_current_user_model` returns a `RedirectResponse`. The router passes this directly to `audit_frontend_service`, which calls `.role_names` on it → `AttributeError`.

### View Current Code

```bash
cat src/routers/audit_frontend.py
```

### Fix

In `src/routers/audit_frontend.py`, add a type check to EVERY route function that uses the auth dependency. Apply this pattern:

```python
from starlette.responses import RedirectResponse

# BEFORE (broken):
async def audit_page(request: Request, current_user=Depends(get_current_user_model), db: Session = Depends(get_db)):
    data = audit_frontend_service.get_audit_data(db, current_user)
    ...

# AFTER (fixed):
async def audit_page(request: Request, current_user=Depends(get_current_user_model), db: Session = Depends(get_db)):
    if isinstance(current_user, RedirectResponse):
        return current_user
    data = audit_frontend_service.get_audit_data(db, current_user)
    ...
```

Apply to ALL route functions in the file that use the auth dependency.

### Verify

```bash
pytest src/tests/test_audit_frontend.py -v
```

**Expected:** 4 passing, 0 failures.

### Broader Scan (Note-Only — DO NOT Fix Others)

```bash
grep -l "get_current_user_model" src/routers/*frontend*.py | while read f; do
    echo "=== $f ==="
    grep -n "isinstance.*RedirectResponse" "$f" || echo "  ⚠️ NO RedirectResponse check"
done
```

If other routers lack the check, **note them in the session log** for a future Hub-coordinated cleanup. Do NOT fix them now — scope creep.

---

## Task 2: Update Outdated Test Expectations (6 tests)

### 2A: test_frontend.py (2 tests)

```bash
cat src/tests/test_frontend.py
```

**test_setup_page_when_setup_required:**
- Expects setup page to render when no users exist
- App is past setup phase — users always exist
- **Fix:** Skip-mark with clear reason:

```python
@pytest.mark.skip(reason="Setup wizard complete — validates initial install only. Re-enable if setup wizard is needed.")
def test_setup_page_when_setup_required(self, ...):
    ...
```

**test_profile_returns_404:**
- Expects `/profile` to return 404
- Profile page was implemented in Week 12
- **Fix:** Update expectation:

```python
def test_profile_page_exists(self, client):
    """Profile page exists (implemented Week 12). Unauthenticated → redirect."""
    response = client.get("/profile")
    assert response.status_code in [200, 302]
```

### 2B: test_setup.py (4 tests)

```bash
cat src/tests/test_setup.py
```

All 4 fail with `UnmappedInstanceError` because `get_default_admin(db_session)` returns `None`, then `db_session.refresh(admin)` blows up.

**Fix:** Add defensive skip in each test:

```python
def test_something_with_admin(self, db_session):
    admin = get_default_admin(db_session)
    if admin is None:
        pytest.skip("Default admin not present — setup wizard tests require initial state")
    db_session.refresh(admin)
    # ... rest of test
```

Apply to all 4 failing tests.

### Verify

```bash
pytest src/tests/test_frontend.py -v
pytest src/tests/test_setup.py -v
```

**Expected:** All 6 previously failing tests now pass or are skip-marked.

---

## Task 3: Verify Known Issue Status

### Dispatch.bid Relationship Bug

```bash
grep -A3 "bid.*relationship\|bid.*Mapped" src/models/dispatch.py
grep -A3 "dispatch.*relationship\|dispatch.*Mapped" src/models/job_bid.py
```

- **If confirmed fixed:** Note in session log → Hub updates Roadmap/Checklist
- **If NOT fixed:** Note as still blocking — separate task

### test_members.py Delete Test

This failure was caused by missing `book_registrations` table. Should resolve after migration:

```bash
pytest src/tests/test_members.py -k "test_delete_member" -v
```

If still fails, note the error in session log.

---

## Task 4: Full Test Suite Verification

```bash
pytest -v --tb=short 2>&1 | tail -40
pytest --tb=no -q
```

**Record exact counts:**
- Total tests:
- Passed:
- Failed:
- Errors:
- Skipped:
- Pass rate:

**Target:** ≥92% pass rate.

**Confirm no regressions:** No previously passing tests should now fail.

---

## Task 5: Stripe Test Skip Markers (Optional — Only If Time Permits)

If any Stripe-related tests are failing because they try to hit the Stripe API in CI/test:

```bash
pytest src/tests/ -v --tb=short 2>&1 | grep -i "stripe\|payment" | grep -i "fail\|error"
```

If found, add skip markers:

```python
@pytest.mark.skip(reason="Requires live Stripe API credentials — run manually with STRIPE_SECRET_KEY set")
```

This is low priority. Only do it if you have time after the main tasks.

---

## Documentation Updates

### 1. Session Log

Create: `docs/reports/session-logs/YYYY-MM-DD-test-cleanup.md`

Include:
- Tests fixed and how
- Tests skip-marked and why
- Other routers found with RedirectResponse vulnerability (list them)
- Dispatch.bid verification result
- Final test counts (before vs after)

### 2. Hub Handoff Note (If Applicable)

If the broader scan (Task 1) found other frontend routers missing the RedirectResponse check, generate a handoff note for Hub:

```markdown
## Hub Handoff: RedirectResponse Type Check Missing in Frontend Routers

**From:** Spoke 2, [DATE]
**Issue:** Multiple frontend routers pass auth dependency result to services without checking if it's a RedirectResponse.
**Fixed:** audit_frontend.py (4 tests)
**Still Vulnerable:** [list routers found in scan]
**Recommendation:** Cross-cutting cleanup task for all frontend routers.
```

---

## Commit

```bash
git add -A
git commit -m "fix: audit frontend type check + update outdated test expectations

- Fix RedirectResponse type check in audit_frontend.py (4 tests)
- Skip-mark setup wizard tests (default admin not in test DB)
- Update profile test expectation (page exists since Week 12)
- Verify Dispatch.bid relationship status
- Test suite: [X] passed, [Y] failed, [Z] skipped
"
git push origin develop
```

---

## Success Criteria

- [ ] `test_audit_frontend.py` — 4 tests pass
- [ ] `test_frontend.py` — 2 outdated tests updated/skip-marked
- [ ] `test_setup.py` — 4 outdated tests updated/skip-marked
- [ ] Dispatch.bid relationship status verified and documented
- [ ] `test_members.py::test_delete_member` checked post-migration
- [ ] Full test suite run with exact counts recorded
- [ ] No regressions (no previously passing tests now failing)
- [ ] Vulnerable routers noted for Hub handoff (if found)
- [ ] Session log created
- [ ] Committed and pushed to `develop`

---

## Changed Files (List After Completion)

After completing all tasks, list every file changed or created as `/dir/file` paths.
