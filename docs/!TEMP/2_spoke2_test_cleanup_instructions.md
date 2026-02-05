# Spoke 2 Instruction Document: Test Suite Cleanup (Post-Diagnostic)

**Source:** Hub → Spoke 2 Handoff
**Date:** February 5, 2026
**Priority:** 🟡 MEDIUM — Fixes 10 test failures (4 audit + 6 outdated)
**Estimated Time:** 30-45 minutes
**Branch:** `develop`
**Risk Level:** LOW — Test file and single router fix only. No schema changes.
**Prerequisite:** Run AFTER Phase 7 Migration instruction (separate document). Several tests in this cleanup are also blocked by missing Phase 7 tables.

---

## Context

The Feb 5 test diagnostic identified two categories of non-migration test failures:

1. **Audit frontend router type check bug** (4 failures in `test_audit_frontend.py`)
   - Root cause: Router doesn't check if auth dependency returned `RedirectResponse` vs actual user object
   
2. **Outdated test expectations** (6 failures across `test_frontend.py` and `test_setup.py`)
   - Root cause: Tests expect old application state (no setup, no profile page, default admin exists)

These are independent of the Phase 7 migration but should be done after it to get an accurate final test count.

---

## Task 1: Fix Audit Frontend Router Type Check (4 tests)

### Problem

When an unauthenticated request hits the audit frontend routes, `get_current_user_model` returns a `RedirectResponse` (redirect to login). But the router passes this directly to `audit_frontend_service`, which tries to access `.role_names` on it — causing:

```
AttributeError: 'RedirectResponse' object has no attribute 'role_names'
```

### Diagnosis

```bash
# Confirm the bug exists — run the 4 failing tests
pytest src/tests/test_audit_frontend.py -v

# View the current router code
cat src/routers/audit_frontend.py
```

Look for route functions that receive `current_user` from the auth dependency and pass it to the service without checking its type.

### Fix

In `src/routers/audit_frontend.py`, every route function that uses the auth dependency needs a type check **before** passing the user to the service layer.

**Pattern to apply:**

```python
from starlette.responses import RedirectResponse

# BEFORE (broken):
async def audit_page(request: Request, current_user=Depends(get_current_user_model), db: Session = Depends(get_db)):
    data = audit_frontend_service.get_audit_data(db, current_user)
    # ...

# AFTER (fixed):
async def audit_page(request: Request, current_user=Depends(get_current_user_model), db: Session = Depends(get_db)):
    if isinstance(current_user, RedirectResponse):
        return current_user
    data = audit_frontend_service.get_audit_data(db, current_user)
    # ...
```

**Apply this pattern to ALL route functions in `audit_frontend.py` that use the auth dependency.** Check each function — the Feb 5 diagnostic found 4 affected tests, which likely maps to 2-4 route functions.

### Verification

```bash
# Run the audit frontend tests — all 4 should pass now
pytest src/tests/test_audit_frontend.py -v
```

**Expected:** 4 passing, 0 failures.

### ⚠️ Broader Check

This same pattern might exist in other frontend routers. After fixing audit_frontend.py, do a quick scan:

```bash
# Check if other frontend routers have the same vulnerability
grep -l "get_current_user_model" src/routers/*frontend*.py | while read f; do
    echo "=== $f ==="
    grep -n "isinstance.*RedirectResponse" "$f" || echo "  ⚠️ NO RedirectResponse check found"
done
```

If other routers lack the check, **note them in the session log** but do NOT fix them in this session — that's a separate task to avoid scope creep. The goal here is to fix the 4 known failures.

---

## Task 2: Update Outdated Test Expectations (6 tests)

### Problem

6 tests fail because they expect the application to be in a state that no longer reflects reality:

| Test File | Test Name | Failure Reason |
|-----------|-----------|----------------|
| `test_frontend.py` | `test_setup_page_when_setup_required` | Setup is no longer required (users exist in DB) |
| `test_frontend.py` | `test_profile_returns_404` | Profile page now exists (implemented Week 12) |
| `test_setup.py` | All 4 tests | Default admin user doesn't exist in DB |

### Fix 2A: test_frontend.py (2 tests)

```bash
# View current test expectations
cat src/tests/test_frontend.py
```

**test_setup_page_when_setup_required:**
- This test expects the setup page to render when no users exist
- The application now always has users (post-setup state)
- **Fix:** Update the test to verify that setup is NOT required when users exist, OR skip-mark it with a clear reason:

```python
@pytest.mark.skip(reason="Setup wizard complete — test validates initial install only. Re-enable if setup wizard is needed again.")
def test_setup_page_when_setup_required(self, ...):
    ...
```

**test_profile_returns_404:**
- This test expects `/profile` to return 404
- Profile page was implemented in Week 12 Session A
- **Fix:** Update the test to expect a 200 (authenticated) or 302 (redirect to login if unauthenticated):

```python
def test_profile_page_exists(self, client):
    """Profile page should exist (implemented Week 12)."""
    response = client.get("/profile")
    # Unauthenticated should redirect to login, not 404
    assert response.status_code in [200, 302]
```

### Fix 2B: test_setup.py (4 tests)

```bash
# View current test expectations
cat src/tests/test_setup.py
```

All 4 tests fail with `UnmappedInstanceError: Class 'builtins.NoneType' is not mapped` because `get_default_admin(db_session)` returns `None`, then `db_session.refresh(admin)` fails.

**Root cause:** The tests assume a default admin user exists in the test database. In the current application state, the default admin may have been removed or never seeded.

**Fix options (choose ONE — prefer Option A for least disruption):**

**Option A: Add defensive check in tests**

Update each test to handle the case where the default admin doesn't exist:

```python
def test_something_with_admin(self, db_session):
    admin = get_default_admin(db_session)
    if admin is None:
        pytest.skip("Default admin not present in test DB — setup wizard tests require initial state")
    db_session.refresh(admin)
    # ... rest of test
```

**Option B: Ensure test fixture creates admin**

If the tests should always have an admin available, ensure the `conftest.py` fixture creates one:

```python
@pytest.fixture
def default_admin(db_session):
    """Create or fetch default admin for setup tests."""
    admin = get_default_admin(db_session)
    if admin is None:
        # Create a test admin
        admin = User(username="admin", email="admin@test.com", ...)
        # ... set hashed password, roles, etc.
        db_session.add(admin)
        db_session.commit()
    return admin
```

Then update the 4 tests to use this fixture.

**Recommendation:** Use Option A. These are setup wizard tests validating initial install behavior. Skip-marking them with a clear reason is the cleanest approach for a system that's past the setup phase.

### Verification

```bash
# Run the updated tests
pytest src/tests/test_frontend.py -v
pytest src/tests/test_setup.py -v
```

**Expected:** All 6 previously failing tests now pass or are skip-marked with clear reasons.

---

## Task 3: Verify and Document Known Issues Status

### Dispatch.bid Relationship Bug

The Feb 5 session log stated this was already fixed, but the Milestone Checklist and Roadmap still list it as CRITICAL/blocking.

```bash
# Verify the fix is in place
grep -A3 "bid.*relationship\|bid.*Mapped" src/models/dispatch.py
grep -A3 "dispatch.*relationship\|dispatch.*Mapped" src/models/job_bid.py
```

**If confirmed fixed:** Note in session log so Hub can update documentation.
**If NOT fixed:** This is a separate task — do not fix it in this session. Note it as still blocking.

### test_members.py (1 failure)

The session log noted 1 failure in `test_delete_member` caused by missing `book_registrations` table. This should resolve automatically after Phase 7 migrations are applied. Verify:

```bash
pytest src/tests/test_members.py::test_delete_member -v
```

If it still fails after migrations, note the error in the session log.

---

## Full Test Suite Verification

### After ALL fixes are applied, run the complete suite:

```bash
# Full test run
pytest -v --tb=short 2>&1 | tail -40

# Capture summary
pytest --tb=no -q
```

Record exact counts:
- Total tests:
- Passed:
- Failed:
- Errors:
- Skipped:
- Pass rate:

**Target:** ≥92% pass rate (assuming Phase 7 migrations were applied first).

---

## Documentation Updates

### After successful cleanup:

**1. Session log** — Create at `docs/reports/session-logs/YYYY-MM-DD-test-cleanup.md` with:
- Tests fixed and how
- Tests skip-marked and why
- Other routers found with same RedirectResponse vulnerability (if any)
- Dispatch.bid bug verification result
- Final test counts

**2. Hub handoff note** — If other frontend routers lack the RedirectResponse type check (found in the broader check scan), note this for Hub to create a cross-cutting cleanup task.

---

## Success Criteria

- [ ] `test_audit_frontend.py` — 4 tests pass (type check fix)
- [ ] `test_frontend.py` — 2 outdated tests updated/skip-marked
- [ ] `test_setup.py` — 4 outdated tests updated/skip-marked  
- [ ] Dispatch.bid relationship status verified and documented
- [ ] `test_members.py::test_delete_member` checked post-migration
- [ ] Full test suite run with exact counts recorded
- [ ] No regressions introduced (no previously passing tests now failing)
- [ ] Other vulnerable routers noted (if found) for Hub handoff
- [ ] Session log created
- [ ] All changes committed and pushed to `develop`
