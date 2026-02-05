# Claude Code Instruction Document: Week 29 — Test Suite Stabilization

**Sprint:** Week 29
**Spoke:** Spoke 2 (Operations)
**Source:** Hub — generated February 4, 2026
**Prerequisite:** Week 28 Test Repair session complete (v0.9.8-alpha, 491 passing / 593 total)
**Goal:** Resolve remaining test failures to reach ≥92% pass rate (≥546 passing of 593)
**Estimated Effort:** 3-5 hours across 2-3 sessions

---

## IMPORTANT: Read Before Starting

1. **Read `CLAUDE.md` first.** It is the project context document.
2. **Do NOT create new features, endpoints, models, or migrations.** This is a repair-only sprint.
3. **Do NOT modify any business logic** unless a test reveals an actual bug (document it if so).
4. **Do NOT delete or skip-mark tests** to make numbers look better. Fix them or document why they cannot be fixed yet.
5. **Run the full test suite** (`pytest -v`) at baseline before making any changes. Record the exact counts.
6. **Commit after each phase** with message format: `fix(tests): Week 29 Phase X — [description]`

---

## Current State (Post-Week 28)

| Metric | Count |
|--------|-------|
| **Passing** | 491 |
| **Failed** | 51 |
| **Errors** | 16 |
| **Skipped** | 35 (27 Stripe + 5 setup + 3 S3) |
| **Total** | 593 |
| **Pass Rate** | 88.0% |
| **Target** | ≥92% (≥546 passing) |

### Failure Breakdown

| Category | Count | Type | Root Cause |
|----------|-------|------|------------|
| Phase 7 test fixtures | 16 | ERROR | Unique constraint violations from seed data collision |
| Dispatch frontend auth | 27 | FAIL | 302 redirects instead of 200 (cookie auth fixture issue) |
| Referral frontend auth | 11 | FAIL | Same auth fixture issue as dispatch |
| Member notes API auth | 5 | FAIL | 401 unauthorized (Bearer token fixture issue) |
| **Total actionable** | **59** | | |
| Stripe (skipped) | 27 | SKIP | Expected per ADR-018 — do not touch |

---

## Phase 1: Diagnostic Baseline (Do This First)

**Time estimate:** 15-20 minutes

### Step 1.1: Run full test suite and capture output

```bash
pytest -v 2>&1 | tee /tmp/week29-baseline.txt
```

### Step 1.2: Generate categorized failure report

```bash
# Count by status
pytest -v 2>&1 | grep -c "PASSED"
pytest -v 2>&1 | grep -c "FAILED"
pytest -v 2>&1 | grep -c "ERROR"
pytest -v 2>&1 | grep -c "SKIPPED"

# List all failures with file and test name
pytest -v 2>&1 | grep "FAILED" | sort

# List all errors with file and test name
pytest -v 2>&1 | grep "ERROR" | sort
```

### Step 1.3: Verify baseline matches expected counts

Compare your output against the table above. If counts differ significantly (±5), **stop and report to user** before proceeding. The codebase may have changed since this instruction was written.

### Step 1.4: Inspect conftest.py

Before fixing anything, read and understand the test fixtures:

```bash
cat src/tests/conftest.py
```

**Document these findings:**
- What fixtures exist for authentication? (Look for `auth_cookies`, `auth_headers`, `authenticated_client`, or similar)
- How is the test database created and seeded?
- Are there any `autouse=True` fixtures?
- Is there a `test_client` or `client` fixture? What base URL does it use?
- Does seed data run automatically or on-demand?
- Are there Phase 7-specific fixtures? Where?

This understanding is **critical** for Phases 2 and 3.

---

## Phase 2: Phase 7 Test Fixture Errors (16 errors)

**Time estimate:** 45-60 minutes
**Files:** `src/tests/test_phase7_models.py`, `src/tests/test_referral_frontend.py`
**Expected fix count:** 16 errors → 0 errors

### Problem Statement

Phase 7 test fixtures create referral books and registrations using codes that collide with seed data. When tests run, the database already contains seed entries (e.g., book code `WIRE_BREM_1`), and the test fixtures try to INSERT records with the same unique-constrained values, causing `IntegrityError`.

Example error:
```
IntegrityError: duplicate key value violates unique constraint "ix_referral_books_code"
Key (code)=(WIRE_BREM_1) already exists.
```

### Fix Strategy

There are three valid approaches. **Choose ONE and apply it consistently:**

#### Option A: Use unique test-specific codes (RECOMMENDED)

Change test fixture data to use codes that won't collide with seed data. Prefix test data with `TEST_` or use UUIDs.

```python
# BEFORE (collides with seed)
book = ReferralBook(code="WIRE_BREM_1", name="Wire Bremerton Book 1", ...)

# AFTER (unique to tests)
book = ReferralBook(code="TEST_WIRE_BREM_1", name="Test Wire Bremerton Book 1", ...)
```

**Rules for Option A:**
- Prefix ALL test fixture codes with `TEST_` to make collisions impossible
- Apply to `test_phase7_models.py` AND `test_referral_frontend.py`
- Check every fixture that creates: `ReferralBook`, `BookRegistration`, `LaborRequest`, `JobBid`, `Dispatch`
- Verify the test assertions still make sense with the new codes

#### Option B: Use database transaction rollback per test

If conftest.py doesn't already do this, wrap each test in a transaction that rolls back:

```python
@pytest.fixture(autouse=True)
def db_session_rollback(db_session):
    """Roll back all changes after each test."""
    yield db_session
    db_session.rollback()
```

**Caution:** This may interact with existing fixtures. Only use if Option A causes cascading issues.

#### Option C: Clear seed data in Phase 7 test setup

Add a module-level fixture that deletes Phase 7 seed data before tests run:

```python
@pytest.fixture(autouse=True, scope="module")
def clean_phase7_seed_data(db_session):
    """Remove Phase 7 seed data before running Phase 7 tests."""
    db_session.execute(text("DELETE FROM dispatches"))
    db_session.execute(text("DELETE FROM job_bids"))
    db_session.execute(text("DELETE FROM labor_requests"))
    db_session.execute(text("DELETE FROM registration_activities"))
    db_session.execute(text("DELETE FROM book_registrations"))
    db_session.execute(text("DELETE FROM referral_books"))
    db_session.commit()
    yield
```

**Caution:** Only use if the test module is self-contained and doesn't depend on seed data for other assertions.

### Verification

After applying fixes:

```bash
# Run ONLY Phase 7 tests to verify
pytest src/tests/test_phase7_models.py -v
pytest src/tests/test_referral_frontend.py -v

# Count should show 0 errors in these files
```

### Commit

```bash
git add -A
git commit -m "fix(tests): Week 29 Phase 2 — resolve Phase 7 fixture unique constraint errors"
```

---

## Phase 3: Frontend Authentication Failures (43 failures)

**Time estimate:** 1.5-2 hours
**Files:** Multiple test files + likely `src/tests/conftest.py`
**Expected fix count:** Up to 43 failures → 0 failures

### Problem Statement

Frontend tests are receiving:
- **302 redirects** instead of 200 OK (27 dispatch + 11 referral = 38 tests)
- **401 Unauthorized** instead of 200 OK (5 member notes API tests)

This is NOT an application bug — the auth system works in production and in other test files that pass. The issue is that **test fixtures are not properly providing authentication credentials** to the test HTTP client for these specific test files.

### Investigation Steps

#### Step 3.1: Find a working frontend test for comparison

Look at a frontend test file that PASSES (e.g., `test_training_frontend.py`, `test_member_frontend.py`, `test_dues_frontend.py`). Examine:

```bash
# Find a passing frontend test file
pytest src/tests/test_training_frontend.py -v 2>&1 | head -30
```

Then read how it sets up authentication:

```bash
cat src/tests/test_training_frontend.py | head -50
```

**Document:**
- What fixture does the passing test use for the HTTP client?
- Does it use `auth_cookies`, `auth_headers`, `authenticated_client`, or something else?
- How are cookies/tokens set on the client?

#### Step 3.2: Compare with a failing frontend test

```bash
cat src/tests/test_dispatch_frontend.py | head -50
cat src/tests/test_referral_frontend.py | head -50
```

**Look for differences in:**
- Which fixtures are used
- How the test client is created
- Whether cookies are explicitly set
- Whether `follow_redirects=True` is used or not

#### Step 3.3: Identify the specific discrepancy

The most common causes of this pattern are:

**Cause A: Missing cookie fixture**
The failing tests don't inject auth cookies into the test client.

```python
# BROKEN — no auth
def test_dispatch_dashboard(client):
    response = client.get("/dispatch/dashboard")
    assert response.status_code == 200  # Gets 302 redirect to login

# FIXED — with auth cookies
def test_dispatch_dashboard(authenticated_client):
    response = authenticated_client.get("/dispatch/dashboard")
    assert response.status_code == 200
```

**Cause B: Wrong auth method**
API tests need Bearer tokens. Frontend tests need HTTP-only cookies. If the test uses the wrong one, auth fails.

```python
# WRONG for frontend routes (these use cookie auth)
headers = {"Authorization": f"Bearer {token}"}
response = client.get("/dispatch/dashboard", headers=headers)

# RIGHT for frontend routes
client.cookies.set("access_token", token)
response = client.get("/dispatch/dashboard")
```

**Cause C: Cookie fixture not setting the right cookie name**
The auth middleware expects a specific cookie name (likely `access_token`). If the fixture sets a different name, auth fails silently.

**Cause D: Test client not configured to handle cookies**
`httpx.AsyncClient` or `TestClient` may need specific configuration to send cookies.

#### Step 3.4: Apply the fix

Once you identify the pattern from a passing test, apply it consistently to ALL failing frontend test files:

- `src/tests/test_dispatch_frontend.py` (27 failures)
- `src/tests/test_referral_frontend.py` (11 failures — some may already be fixed by Phase 2)
- `src/tests/test_member_notes.py` (5 failures — if these are API tests, they need Bearer tokens, not cookies)

**Important distinctions:**
- Routes under `/dispatch/*`, `/referral/*`, `/members/*` etc. → Cookie auth (frontend)
- Routes under `/api/v1/*` → Bearer token auth (API)
- Check each test file to determine which auth method is appropriate

#### Step 3.5: Handle the member notes tests separately

The 5 member notes tests failing with 401 may be a different issue than the frontend 302s. From Week 28:

> Fix 1 fixed audit logging parameter names (`changed_by` vs `user_id`) for 5 member note service tests. But 5 additional member notes tests still fail with 401.

Check if these are API-level tests that need Bearer tokens or frontend tests that need cookies. Fix accordingly.

### Verification

```bash
# Run each file individually
pytest src/tests/test_dispatch_frontend.py -v
pytest src/tests/test_referral_frontend.py -v
pytest src/tests/test_member_notes.py -v

# Then run full suite
pytest -v 2>&1 | tee /tmp/week29-phase3.txt
```

### Commit

```bash
git add -A
git commit -m "fix(tests): Week 29 Phase 3 — resolve frontend auth fixture failures"
```

---

## Phase 4: Sweep and Verify (Final)

**Time estimate:** 20-30 minutes

### Step 4.1: Run full test suite

```bash
pytest -v 2>&1 | tee /tmp/week29-final.txt
```

### Step 4.2: Calculate pass rate

```
Passing / (Total - Skipped) = Pass Rate
Target: ≥92%
```

### Step 4.3: Categorize any remaining failures

If any tests still fail after Phases 2-3, categorize them:

| Category | Action |
|----------|--------|
| Actual bugs discovered | Document in session log as bug findings, DO NOT fix business logic in this sprint |
| Environment-dependent (S3, external services) | Skip-mark with clear reason |
| Unclear root cause | Document with full traceback for Hub review |

### Step 4.4: Update CLAUDE.md test counts

Update the test metrics in `CLAUDE.md`:
- Line 20: Update the `Status:` line with new pass/fail/skip/total counts
- Lines 1913-1931: Update the "Remaining Issues" section
- Remove or update any categories that are now resolved

### Step 4.5: Commit final state

```bash
git add -A
git commit -m "fix(tests): Week 29 Complete — test suite stabilization [X passing / 593 total, Y% pass rate]"
```

---

## Session Log Template

Create this file at the end of the session:

**Location:** `docs/reports/session-logs/2026-02-XX-week29-test-stabilization.md`

```markdown
# Session Log: Week 29 — Test Suite Stabilization

**Date:** [date]
**Sprint:** Week 29
**Spoke:** Spoke 2 (Operations)
**Version:** v0.9.8-alpha → v0.9.9-alpha
**Instruction Document:** `docs/!TEMP/CC_WEEK29_TEST_STABILIZATION.md`

## Test Results

| Metric | Baseline (Week 28) | Final (Week 29) | Change |
|--------|---------------------|------------------|--------|
| Passing | 491 | | |
| Failed | 51 | | |
| Errors | 16 | | |
| Skipped | 35 | | |
| Total | 593 | | |
| Pass Rate | 88.0% | | |

## Work Completed

### Phase 1: Diagnostic Baseline
[findings]

### Phase 2: Phase 7 Test Fixture Errors
**Approach chosen:** [A/B/C]
**Tests fixed:** [count]
[details]

### Phase 3: Frontend Auth Fixture Failures
**Root cause identified:** [description]
**Tests fixed:** [count]
[details]

### Phase 4: Final Sweep
[remaining issues if any]

## Bug Discoveries (if any)
[any actual application bugs found during test repair]

## Files Changed
[list]

## Hub Review Items
[any architectural issues or cross-cutting concerns discovered]

## CLAUDE.md Updates Applied
[list of sections updated]
```

---

## Rules of Engagement

1. **Fix the tests, not the symptoms.** If a test is wrong, fix the test. If the test reveals a bug, document the bug and note it for the user — don't change business logic in a test repair sprint.

2. **One category at a time.** Complete Phase 2 fully before starting Phase 3. Don't jump between categories.

3. **If you get stuck on a test for more than 15 minutes**, move on and document it. Some failures may need user input or domain knowledge to resolve.

4. **Preserve the audit trail.** Tests related to audit logging are the most important tests in the system (NLRA compliance). If an audit test fails, investigate thoroughly — it may be a real bug.

5. **The 27 Stripe skips are correct.** Do not un-skip them, do not delete them, do not touch them. They exist as reference for the Square migration (ADR-018).

6. **No new skip-marks without justification.** Every skip needs a comment explaining WHY and WHEN it will be un-skipped.

---

## Success Criteria

| Criteria | Target |
|----------|--------|
| Pass rate | ≥92% (≥546 of 593) |
| Phase 7 errors | 0 |
| Auth fixture failures | 0 (or documented with clear blocker reason) |
| CLAUDE.md updated | Yes |
| Session log created | Yes |
| No business logic changes | Yes |
| All commits have descriptive messages | Yes |

---

**End of Instruction Document**
*Generated by Hub — February 4, 2026*
*For execution via Claude Code in Spoke 2 (Operations)*
