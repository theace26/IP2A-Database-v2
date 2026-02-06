# Claude Code Instructions: Week 35 — Stripe Removal & Bug Squash

**Sprint:** Week 35 (split across 2-3 sessions: 35A, 35B, 35C)
**Spoke:** Spoke 2 (Operations) — executing Hub architectural decision
**Source:** Hub Handoff — February 5, 2026
**Context:** UnionCore (IP2A-Database-v2) — IBEW Local 46
**Estimated Time:** 8-12 hours (2-3 sprint sessions)
**Branch:** `develop`
**Priority:** HIGH — Complete before any new P1 report work

---

## ⚠️ READ BEFORE STARTING — SCOPE & SEQUENCING

This sprint has TWO parts, executed in strict order:

1. **Session 35A: Stripe Removal** — Delete all Stripe code, tests, config. This changes the test baseline.
2. **Session 35B/C: Bug Squash** — Diagnose fresh, then fix by category until ≥95% pass rate.

**THIS SPRINT DOES:**
- Remove ALL Stripe code (SDK imports, services, routes, webhooks, templates, JS, config)
- Remove ALL Stripe tests (~27 currently skipped)
- Remove Stripe from `requirements.txt` / `pyproject.toml`
- Update ADR-018 with Stripe Removal section
- Run fresh diagnostic against the clean baseline
- Categorize and fix test failures systematically
- Target ≥95% pass rate on non-skipped tests
- Update ALL documentation with final test counts

**THIS SPRINT DOES NOT:**
- Write any Square integration code (that's Phase 8, Spoke 1)
- Touch dues tracking models, services, routes, or tests (payment *recording* ≠ payment *processing*)
- Create new features, endpoints, or models
- Modify business logic unless a test reveals an actual production bug

**THE DUES LAYER IS SACRED — DO NOT TOUCH:**
- `src/models/dues_payment.py`, `dues_rate.py`, `dues_period.py`, `dues_adjustment.py`
- `src/services/dues_service.py`, `dues_frontend_service.py`
- `src/routers/dues.py` (API), dues frontend routes
- `src/templates/dues/*`
- All dues tests that don't import or reference Stripe
- The `payment_method` field on DuesPayment (gateway-agnostic, stays)

---

## Pre-Flight (Every Session)

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
docker-compose up -d
```

### Verify Alembic State

```bash
alembic current
alembic heads
```

**Expected:** Single head, no multiple heads. If you see multiple heads — STOP and report.

### Capture Baseline (CRITICAL — Do This Before ANY Changes)

```bash
pytest -v --tb=short 2>&1 | tee /tmp/week35_baseline.txt

echo "=== BASELINE SUMMARY ==="
grep -c "PASSED" /tmp/week35_baseline.txt || echo "0 PASSED"
grep -c "FAILED" /tmp/week35_baseline.txt || echo "0 FAILED"
grep -c "ERROR" /tmp/week35_baseline.txt || echo "0 ERROR"
grep -c "SKIPPED" /tmp/week35_baseline.txt || echo "0 SKIPPED"
echo "Total tests:"
grep -E "passed|failed|error|skipped" /tmp/week35_baseline.txt | tail -1
```

Record these numbers. All subsequent work is measured against this baseline.

---

# SESSION 35A: STRIPE REMOVAL

**Goal:** Surgically remove all Stripe code while preserving the dues tracking layer.
**Estimated Time:** 2-3 hours
**Commit after completion.**

---

## Phase 1: Discovery — Find Every Stripe Reference (30 min)

Before deleting anything, build a complete inventory. This prevents orphaned imports and partial removal.

### Step 1.1: Find all Stripe references in source code

```bash
echo "=== STRIPE IN SOURCE CODE ==="
grep -rn "stripe\|Stripe\|STRIPE" src/ --include="*.py" | grep -v __pycache__ | grep -v ".pyc"

echo ""
echo "=== STRIPE IN TEMPLATES ==="
grep -rn "stripe\|Stripe\|STRIPE" src/templates/ --include="*.html"

echo ""
echo "=== STRIPE IN STATIC FILES ==="
grep -rn "stripe\|Stripe\|STRIPE" src/static/ 2>/dev/null || echo "No static Stripe references"

echo ""
echo "=== STRIPE IN CONFIG ==="
grep -rn "stripe\|Stripe\|STRIPE" src/config.py .env .env.example docker-compose.yml 2>/dev/null

echo ""
echo "=== STRIPE IN REQUIREMENTS ==="
grep -in "stripe" requirements.txt pyproject.toml 2>/dev/null

echo ""
echo "=== STRIPE IN TESTS ==="
grep -rn "stripe\|Stripe\|STRIPE" src/tests/ --include="*.py" | grep -v __pycache__

echo ""
echo "=== STRIPE IN DOCS ==="
grep -rn "stripe\|Stripe\|STRIPE" docs/ --include="*.md" | head -30
echo "(docs references are informational only — don't delete docs mentions yet)"
```

### Step 1.2: Categorize findings into DELETE vs KEEP vs MODIFY

Build a working list. Sort every file from Step 1.1 into one of three buckets:

| Bucket | Action | Example |
|--------|--------|---------|
| **DELETE** | Entire file is Stripe-only | `src/routers/webhooks/stripe_webhook.py`, Stripe test files |
| **MODIFY** | File has Stripe AND non-Stripe code | `src/config.py` (remove Stripe vars, keep everything else) |
| **KEEP** | Reference is informational only | ADR-013, ADR-018, CHANGELOG entries |

**CRITICAL CHECK:** Any file in `src/services/dues_service.py`, `src/routers/dues.py`, or `src/models/dues_*.py` that references Stripe goes in **MODIFY** (remove the Stripe import/reference), NOT **DELETE** (never delete dues files).

### Step 1.3: Map import chains

```bash
echo "=== FILES THAT IMPORT STRIPE MODULES ==="
grep -rn "from.*stripe\|import.*stripe" src/ --include="*.py" | grep -v __pycache__ | grep -v tests/
```

Check if any non-Stripe files import from Stripe modules. These need the import removed, not the whole file deleted.

---

## Phase 2: Remove Stripe Source Code (45 min)

Work through the DELETE and MODIFY lists from Phase 1.

### Step 2.1: Delete Stripe-only files

For each file categorized as DELETE:

```bash
# Example — adjust paths based on your Phase 1 findings:
# rm src/routers/webhooks/stripe_webhook.py  (if it exists)
# rm src/services/stripe_service.py  (if it exists)
# rm src/services/payment_service.py  (if Stripe-only — verify first!)
```

**BEFORE DELETING ANY FILE:** Open it and verify it's 100% Stripe code. If it has ANY non-Stripe functionality, it goes in MODIFY, not DELETE.

### Step 2.2: Modify mixed files

For each file categorized as MODIFY:

1. Open the file
2. Remove Stripe imports (`import stripe`, `from stripe import ...`)
3. Remove Stripe configuration variables
4. Remove Stripe-specific functions/methods/classes
5. Remove Stripe-specific route handlers
6. Verify the remaining code still makes sense
7. If removing Stripe code leaves an empty class/module, delete the file

**Common patterns to remove:**
```python
# REMOVE these patterns:
import stripe
from stripe import ...
STRIPE_SECRET_KEY = ...
STRIPE_PUBLISHABLE_KEY = ...
STRIPE_WEBHOOK_SECRET = ...
stripe.api_key = ...

# Any function that creates Stripe Checkout sessions
# Any webhook handler that processes Stripe events
# Any template rendering that includes Stripe.js
```

### Step 2.3: Remove Stripe from config

**File:** `src/config.py` (or wherever Settings/config class lives)

Remove:
- `STRIPE_SECRET_KEY` setting
- `STRIPE_PUBLISHABLE_KEY` setting
- `STRIPE_WEBHOOK_SECRET` setting
- Any Stripe initialization code

**File:** `.env.example`

Remove all `STRIPE_*` entries.

**File:** `docker-compose.yml`

Remove any `STRIPE_*` environment variables passed to containers.

### Step 2.4: Remove Stripe from dependencies

**File:** `requirements.txt`

```bash
# Remove the stripe line
sed -i '/^stripe/d' requirements.txt
```

**File:** `pyproject.toml` (if dependencies listed there)

```bash
grep -n "stripe" pyproject.toml
# Manually remove the stripe dependency line if found
```

### Step 2.5: Remove Stripe from templates

```bash
# Find and review all Stripe template references
grep -rn "stripe\|Stripe\|STRIPE" src/templates/ --include="*.html"
```

Remove:
- `<script src="https://js.stripe.com/v3/"></script>` includes
- Stripe Elements markup
- Stripe checkout redirect JavaScript
- Stripe-branded payment buttons/forms
- Success/cancel pages IF they are Stripe-specific (not generic payment pages)

**Keep:** Generic payment success/cancel pages that could be reused for Square. Just remove any Stripe branding/references from them.

### Step 2.6: Remove Stripe from router registration

**File:** `src/main.py`

Remove any `app.include_router(...)` lines that register Stripe webhook or payment routers.

```bash
grep -n "stripe\|webhook\|payment" src/main.py
```

Remove the relevant `include_router` calls. If there's a payment router that handles BOTH Stripe and non-Stripe logic, only remove the Stripe parts.

### Step 2.7: Clean up __init__.py files

Check any `__init__.py` that exported Stripe modules:

```bash
grep -rn "stripe\|Stripe" src/**/__init__.py 2>/dev/null
```

Remove exports of deleted modules.

---

## Phase 3: Remove Stripe Tests (30 min)

### Step 3.1: Identify all Stripe test files and test functions

```bash
echo "=== STRIPE TEST FILES ==="
find src/tests/ -name "*.py" -exec grep -l "stripe\|Stripe\|STRIPE" {} \;

echo ""
echo "=== STRIPE TEST FUNCTIONS ==="
grep -rn "def test.*stripe\|def test.*Stripe\|def test.*payment.*stripe" src/tests/ --include="*.py"

echo ""
echo "=== STRIPE SKIP MARKERS ==="
grep -rn "skip.*stripe\|skip.*Stripe\|skip.*ADR-018" src/tests/ --include="*.py"
```

### Step 3.2: Delete Stripe-only test files

If a test file is 100% Stripe tests:

```bash
# rm src/tests/test_stripe_*.py  (adjust based on findings)
# rm src/tests/test_payment*.py  (ONLY if 100% Stripe — verify first!)
```

### Step 3.3: Remove Stripe tests from mixed test files

If a test file has both Stripe and non-Stripe tests:
1. Open the file
2. Remove Stripe-specific test functions
3. Remove Stripe-specific test fixtures
4. Remove Stripe imports
5. Verify remaining tests still work

### Step 3.4: Clean up conftest.py

```bash
grep -n "stripe\|Stripe\|STRIPE" src/tests/conftest.py
```

Remove:
- Stripe mock objects
- Stripe webhook payload fixtures
- Stripe session fixtures
- Any fixture that exists solely for Stripe testing

**DO NOT remove:**
- Auth fixtures (JWT tokens, cookie auth)
- Database fixtures (test DB, sessions)
- Member/user/dues fixtures (these serve non-Stripe tests too)

---

## Phase 4: Verify Clean Removal (20 min)

### Step 4.1: Zero Stripe references in source

```bash
echo "=== REMAINING STRIPE REFS IN SRC ==="
grep -ri "stripe" src/ --include="*.py" | grep -v __pycache__ | grep -v ".pyc"
```

**Expected output:** ZERO lines. If any remain, go back and remove them.

**Exception:** If you find a comment like `# Removed: was Stripe payment method` in the dues models — that's fine, it's a breadcrumb. But actual import/config/function references must be zero.

### Step 4.2: Zero Stripe in requirements

```bash
grep -i "stripe" requirements.txt pyproject.toml 2>/dev/null
```

**Expected:** ZERO results.

### Step 4.3: Server starts cleanly

```bash
# Test that the app starts without import errors
cd ~/Projects/IP2A-Database-v2
python -c "from src.main import app; print('App imports OK ✅')"
```

If this fails with an ImportError, there's a dangling import somewhere. Trace and fix.

### Step 4.4: Run test suite against clean baseline

```bash
pytest -v --tb=short 2>&1 | tee /tmp/week35_post_stripe_removal.txt

echo "=== POST-STRIPE-REMOVAL SUMMARY ==="
grep -c "PASSED" /tmp/week35_post_stripe_removal.txt || echo "0 PASSED"
grep -c "FAILED" /tmp/week35_post_stripe_removal.txt || echo "0 FAILED"
grep -c "ERROR" /tmp/week35_post_stripe_removal.txt || echo "0 ERROR"
grep -c "SKIPPED" /tmp/week35_post_stripe_removal.txt || echo "0 SKIPPED"
echo "Total:"
grep -E "passed|failed|error|skipped" /tmp/week35_post_stripe_removal.txt | tail -1
```

**Expected changes from baseline:**
- Total test count drops by ~27 (removed Stripe tests)
- Skipped count drops by ~27
- Pass count should remain the same or increase slightly
- No NEW failures introduced by the removal

### Step 4.5: Dues pages still work

```bash
# Verify dues routes don't error
pytest src/tests/test_dues*.py -v --tb=short 2>&1 | tail -20
pytest src/tests/test_frontend.py -v -k "dues" --tb=short 2>&1 | tail -20
```

All dues tests that were passing before must still pass.

---

## Phase 5: Update ADR-018 (15 min)

### Step 5.1: Update ADR-018 with Stripe Removal section

**File:** `docs/decisions/ADR-018-square-payment-integration.md`

If ADR-018 already exists (from a previous instruction session), add this section. If it doesn't exist yet, create the full ADR first (see Appendix A), then add this section.

Add after the "Decision" section:

```markdown
## Stripe Removal (Week 35 — February 2026)

All Stripe code was removed from the codebase in Week 35 sprint:

### What Was Removed
- Stripe SDK imports and initialization
- Stripe Checkout session creation service/route
- Stripe webhook handler and verification
- Stripe configuration variables (STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_WEBHOOK_SECRET)
- Stripe.js includes and frontend payment markup
- All Stripe-specific tests (~27 tests)
- `stripe` package from requirements.txt

### What Was Preserved
- Dues tracking models (DuesPayment, DuesRate, DuesPeriod, DuesAdjustment)
- Dues service layer (calculation, recording, querying)
- Dues API routes and frontend routes
- Dues frontend templates and partials
- All non-Stripe dues tests
- `payment_method` field on DuesPayment (gateway-agnostic)
- ADR-013 (marked Superseded, not deleted — retained for historical reference)

### Status
- **In Progress** — Stripe Removed, Square Phase A Pending
- Square implementation trigger: After Phase 7 stabilizes
```

### Step 5.2: Verify ADR-013 shows Superseded

```bash
head -10 docs/decisions/ADR-013-stripe-payment-integration.md
```

If it doesn't already say `**Status:** Superseded by ADR-018`, add it after the title line.

### Step 5.3: Verify ADR Index includes both

```bash
grep -n "018\|013" docs/decisions/README.md
```

Ensure ADR-013 shows "Superseded" and ADR-018 shows "Accepted" or "In Progress".

---

## Phase 6: Commit Session 35A

```bash
git add -A
git status  # Review staged changes — verify no dues files were modified

git commit -m "refactor: remove all Stripe code — ADR-018 (Week 35A)

- Removed Stripe SDK imports, services, routes, and webhook handlers
- Removed Stripe Checkout session creation and payment flow
- Removed Stripe configuration (env vars, settings, docker-compose)
- Removed Stripe.js includes and frontend payment markup
- Removed stripe package from requirements.txt/pyproject.toml
- Removed ~27 Stripe-specific tests
- Updated ADR-018 with Stripe Removal section
- Verified ADR-013 status: Superseded

Preserved: All dues tracking models, services, routes, templates, and tests.
Payment recording layer is gateway-agnostic and untouched.

Pre-removal: [X] total tests, [Y] passing, [Z] skipped
Post-removal: [A] total tests, [B] passing, [C] skipped
"

git push origin develop
```

**Replace [X/Y/Z/A/B/C] with actual numbers from your baseline and post-removal runs.**

---

# SESSION 35B/C: BUG SQUASH

**Goal:** Reach ≥95% pass rate on non-skipped tests.
**Prerequisite:** Session 35A complete and committed.
**Estimated Time:** 4-6 hours across 1-2 sessions.
**Strategy:** Diagnostic first, categorize, then fix by category.

---

## Phase 7: Fresh Diagnostic (30 min)

**CRITICAL:** Do NOT start fixing tests blindly. The test numbers from Hub docs, CLAUDE.md, Roadmap, and Checklist are all slightly different. Only the live test suite output matters.

### Step 7.1: Full test suite with captured output

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
docker-compose up -d

pytest -v --tb=short 2>&1 | tee /tmp/week35b_diagnostic.txt

echo "=== DIAGNOSTIC SUMMARY ==="
PASSED=$(grep -c "PASSED" /tmp/week35b_diagnostic.txt)
FAILED=$(grep -c "FAILED" /tmp/week35b_diagnostic.txt)
ERRORS=$(grep -c "ERROR" /tmp/week35b_diagnostic.txt)
SKIPPED=$(grep -c "SKIPPED" /tmp/week35b_diagnostic.txt)
TOTAL=$((PASSED + FAILED + ERRORS + SKIPPED))
NON_SKIPPED=$((TOTAL - SKIPPED))
PASS_RATE=$(echo "scale=1; $PASSED * 100 / $NON_SKIPPED" | bc)

echo "Total:      $TOTAL"
echo "Passed:     $PASSED"
echo "Failed:     $FAILED"
echo "Errors:     $ERRORS"
echo "Skipped:    $SKIPPED"
echo "Non-skipped: $NON_SKIPPED"
echo "Pass rate:  $PASS_RATE%"
echo "Target:     ≥95%"
echo "Need:       $(echo "$NON_SKIPPED * 95 / 100" | bc) passing to hit 95%"
```

### Step 7.2: List every failure and error

```bash
echo "=== ALL FAILURES ==="
grep "FAILED" /tmp/week35b_diagnostic.txt | sort

echo ""
echo "=== ALL ERRORS ==="
grep "ERROR" /tmp/week35b_diagnostic.txt | sort

echo ""
echo "=== ALL SKIPS ==="
grep "SKIPPED" /tmp/week35b_diagnostic.txt | sort
```

### Step 7.3: Categorize every failure

Read each failure/error and assign it to exactly ONE category:

| Category | Description | Fix Approach | Priority |
|----------|-------------|--------------|----------|
| **A: Fixture Issues** | Wrong enum values, missing fixtures, stale test data | Update fixtures in conftest.py | 1st — highest impact |
| **B: Schema Drift** | Column name mismatches, missing columns, wrong types | Fix model ↔ test alignment | 2nd |
| **C: Test Collisions** | Pass alone, fail together (Bug #031 pattern) | Fixture isolation, unique test data | 3rd |
| **D: Logic Errors** | Test expectation wrong OR production code bug | Investigate each individually | 4th |
| **E: Flaky/Timing** | Intermittent failures, race conditions | Mock time or add retries | 5th |
| **F: Legitimate Skips** | Setup wizard, S3, environment-specific | Leave as skipped with reason | Skip |

**HOW TO CATEGORIZE:**

For each failure, run it in isolation first:

```bash
pytest path/to/test.py::test_name -v --tb=long
```

- If it **passes alone** but **fails in suite** → Category C (collision)
- If it **fails alone** with fixture/import error → Category A
- If it **fails alone** with column/attribute error → Category B
- If it **fails alone** with assertion mismatch → Category D
- If it **passes sometimes, fails sometimes** → Category E

Record your categorization. Example format:

```
CATEGORY A (Fixture):
  - test_referral_frontend.py::test_books_page — missing referral_book fixture
  - test_dispatch_frontend.py::test_dashboard — auth cookie not set

CATEGORY B (Schema Drift):
  - test_member_notes.py::test_create_note — column 'user_id' should be 'changed_by'

CATEGORY C (Collision):
  - test_dues.py::test_create_payment — unique constraint on period_id + member_id

CATEGORY D (Logic):
  - test_enrollment.py::test_grade_calc — expected 3.5, got 3.45

CATEGORY F (Legitimate Skip):
  - test_documents.py::test_upload — requires S3/MinIO running
```

---

## Phase 8: Fix Category A — Fixture Issues (1-2 hours)

These are the highest-impact fixes. One fixture fix often resolves 5-20 tests.

### Common Fixture Patterns to Check

**8.1: Enum values in test data**

```bash
# Check if test fixtures use string enum values instead of enum objects
grep -rn "status.*=.*['\"]" src/tests/conftest.py | head -20
```

If fixtures use `status="active"` instead of `status=MemberStatus.ACTIVE`, fix them.

**8.2: Auth fixtures (cookie-based)**

Many Phase 7 frontend tests fail because the auth cookie fixture doesn't work with the new routes.

```bash
# Check the auth fixture setup
grep -A 20 "def auth_client\|def authenticated_client\|def logged_in_client" src/tests/conftest.py
```

Verify:
- The fixture creates a valid JWT token
- The fixture sets the token as an HTTP-only cookie (not just a header)
- The fixture uses a user with appropriate roles (Admin/Staff for dispatch pages)
- The cookie name matches what the app expects

**8.3: Phase 7 seed data fixtures**

Phase 7 tests need referral books, registrations, etc. in the test DB.

```bash
# Check for Phase 7 fixtures
grep -n "referral_book\|book_registration\|labor_request\|dispatch\|job_bid" src/tests/conftest.py
```

If Phase 7 fixtures don't exist, they need to be created. Pattern:

```python
@pytest.fixture
def sample_referral_book(db_session):
    """Create a sample referral book for testing."""
    from src.models.referral_book import ReferralBook
    book = ReferralBook(
        book_name="WIRE SEATTLE",
        classification="Wire",
        region="Seattle",
        contract_code="WIREPERSON",
        agreement_type="STANDARD",
        work_level="JOURNEYMAN",
        book_type="PRIMARY",
        is_active=True,
    )
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)
    return book
```

**8.4: Missing model imports in conftest**

```bash
# Check if Phase 7 models are imported in conftest
grep -n "from src.models" src/tests/conftest.py
```

Add any missing imports for models used in fixtures.

### After fixing Category A

```bash
pytest -v --tb=short 2>&1 | tee /tmp/week35b_after_cat_a.txt
echo "=== AFTER CATEGORY A FIXES ==="
grep -c "PASSED" /tmp/week35b_after_cat_a.txt
grep -c "FAILED" /tmp/week35b_after_cat_a.txt
grep -c "ERROR" /tmp/week35b_after_cat_a.txt
```

Commit:

```bash
git add -A
git commit -m "fix(tests): Week 35B Category A — fixture issues

- [describe each fixture fix]
- Tests before: X passing / Y failing
- Tests after: A passing / B failing
"
```

---

## Phase 9: Fix Category B — Schema Drift (1 hour)

These are tests that reference column names or field names that have changed since the test was written.

### Common patterns

```bash
# Find column name references in tests that might be stale
grep -rn "user_id\|is_locked\|position_number" src/tests/ --include="*.py" | grep -v __pycache__
```

Known corrections from project history:
- `is_locked` → `locked_until` (User model)
- `position_number` → `applicant_priority_number` (Registration model)
- `user_id` → `changed_by` (in audit contexts)

For each schema drift failure:
1. Check the current model definition
2. Update the test to match the model
3. Run the specific test to verify the fix

### After fixing Category B

```bash
pytest -v --tb=short 2>&1 | tee /tmp/week35b_after_cat_b.txt
echo "=== AFTER CATEGORY B FIXES ==="
grep -c "PASSED" /tmp/week35b_after_cat_b.txt
grep -c "FAILED" /tmp/week35b_after_cat_b.txt
```

Commit:

```bash
git add -A
git commit -m "fix(tests): Week 35B Category B — schema drift alignment

- [describe each fix]
- Tests before: X passing / Y failing
- Tests after: A passing / B failing
"
```

---

## Phase 10: Fix Category C — Test Collisions (1-2 hours)

Tests that pass in isolation but fail when run together. The classic pattern is unique constraint violations because two tests create records with overlapping data.

### Diagnosis

For each suspected collision, run it both ways:

```bash
# Alone (should pass)
pytest src/tests/test_X.py::test_name -v

# Full suite (should fail)
pytest src/tests/ -v -k "test_name"
```

### Common fixes

**10.1: Use unique identifiers in test data**

```python
# BAD — collides with other tests
member = create_member(card_number="12345")

# GOOD — unique per test
import uuid
member = create_member(card_number=f"TEST-{uuid.uuid4().hex[:8]}")
```

**10.2: Function-scoped DB sessions**

If fixtures use session-scoped DB sessions, data from one test leaks into another.

```python
# If using module-scoped session, switch to function-scoped for problem tests
@pytest.fixture(scope="function")
def clean_db_session(db_engine):
    ...
```

**10.3: Explicit cleanup**

```python
@pytest.fixture
def sample_payment(db_session):
    payment = create_payment(...)
    db_session.add(payment)
    db_session.commit()
    yield payment
    # Cleanup
    db_session.delete(payment)
    db_session.commit()
```

### After fixing Category C

Run the full suite THREE times to verify no intermittent collisions:

```bash
pytest -v --tb=short 2>&1 | tail -5
pytest -v --tb=short 2>&1 | tail -5
pytest -v --tb=short 2>&1 | tail -5
```

All three runs should produce identical pass/fail counts.

Commit:

```bash
git add -A
git commit -m "fix(tests): Week 35B Category C — test collision isolation

- [describe each collision fix]
- Verified: 3 consecutive runs produce identical results
"
```

---

## Phase 11: Fix Category D — Logic Errors (1-2 hours)

Each one requires individual investigation. This is the most time-consuming category.

### For each failure

1. Run in isolation with full traceback:
   ```bash
   pytest src/tests/test_X.py::test_name -v --tb=long
   ```

2. Read the assertion error carefully:
   - Is the **test expectation** wrong? (test was written against old behavior)
   - Is the **production code** buggy? (test found a real bug)

3. If **test is wrong** → fix the test, add a comment explaining why
4. If **production code is buggy** → fix the code AND document in session log as a bug found during testing

**IMPORTANT:** If fixing production code, verify it doesn't break other tests:

```bash
# After fixing production code, run full suite
pytest -v --tb=short
```

### Known Logic Issues from Project History

**Dispatch.bid relationship bug:** If not already fixed by a previous session, this is the fix:

```python
# File: src/models/dispatch.py
# Find the Dispatch.bid relationship and add foreign_keys parameter:
bid = relationship("JobBid", foreign_keys=[bid_id], back_populates="dispatch")
```

Check if this is still an issue:

```bash
grep -n "bid.*relationship\|relationship.*bid" src/models/dispatch.py
```

### After fixing Category D

```bash
pytest -v --tb=short 2>&1 | tee /tmp/week35b_after_cat_d.txt
echo "=== AFTER CATEGORY D FIXES ==="
grep -c "PASSED" /tmp/week35b_after_cat_d.txt
grep -c "FAILED" /tmp/week35b_after_cat_d.txt
```

Commit:

```bash
git add -A
git commit -m "fix(tests): Week 35B Category D — logic error corrections

- [describe each fix, noting whether test or production code was changed]
- Any production bugs found: [list or 'none']
"
```

---

## Phase 12: Handle Category E — Flaky Tests (30 min)

If any tests are truly timing-dependent and cannot be made deterministic:

```python
@pytest.mark.skip(reason="Flaky: timing-dependent bidding window check. See Bug #XXX")
def test_bidding_window_edge_case():
    ...
```

**Rules for flaky skips:**
- Every skip MUST have a reason string
- Every skip SHOULD reference a bug number
- Prefer fixing over skipping
- If you mock `datetime.now()` or `time.time()`, the test is no longer flaky — it's deterministic

---

## Phase 13: Handle Category F — Legitimate Skips (15 min)

Review all currently skipped tests. Every skip must have a clear reason:

```bash
grep -rn "skip\|SKIP" src/tests/ --include="*.py" | grep -v __pycache__
```

Acceptable skip reasons:
- `"Requires S3/MinIO running"` — infrastructure dependency
- `"Setup wizard not implemented"` — feature not built yet
- `"Requires LaborPower data import"` — blocked by external data

Unacceptable:
- `"TODO"` or `"Fix later"` — these need a real reason or need to be fixed now
- No reason at all — add one

---

## Phase 14: Final Verification (30 min)

### Step 14.1: Three consecutive clean runs

```bash
pytest -v --tb=short 2>&1 | tee /tmp/week35_final_run1.txt
pytest -v --tb=short 2>&1 | tee /tmp/week35_final_run2.txt
pytest -v --tb=short 2>&1 | tee /tmp/week35_final_run3.txt

# Compare results
echo "Run 1:" && tail -3 /tmp/week35_final_run1.txt
echo "Run 2:" && tail -3 /tmp/week35_final_run2.txt
echo "Run 3:" && tail -3 /tmp/week35_final_run3.txt
```

All three must produce identical results.

### Step 14.2: Calculate final pass rate

```bash
PASSED=$(grep -c "PASSED" /tmp/week35_final_run1.txt)
FAILED=$(grep -c "FAILED" /tmp/week35_final_run1.txt)
ERRORS=$(grep -c "ERROR" /tmp/week35_final_run1.txt)
SKIPPED=$(grep -c "SKIPPED" /tmp/week35_final_run1.txt)
TOTAL=$((PASSED + FAILED + ERRORS + SKIPPED))
NON_SKIPPED=$((TOTAL - SKIPPED))
PASS_RATE=$(echo "scale=1; $PASSED * 100 / $NON_SKIPPED" | bc)

echo "============================="
echo "FINAL RESULTS — WEEK 35"
echo "============================="
echo "Total:       $TOTAL"
echo "Passed:      $PASSED"
echo "Failed:      $FAILED"
echo "Errors:      $ERRORS"
echo "Skipped:     $SKIPPED"
echo "Non-skipped: $NON_SKIPPED"
echo "Pass rate:   $PASS_RATE%"
echo "Target:      ≥95%"
echo "============================="

if (( $(echo "$PASS_RATE >= 95.0" | bc -l) )); then
    echo "✅ TARGET MET"
else
    echo "❌ TARGET NOT MET — document remaining failures in session log"
fi
```

### Step 14.3: Verify zero ERROR tests

```bash
ERROR_COUNT=$(grep -c "ERROR" /tmp/week35_final_run1.txt)
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "❌ $ERROR_COUNT ERROR tests remain — these are broken tests, not failures"
    grep "ERROR" /tmp/week35_final_run1.txt
else
    echo "✅ Zero ERROR tests"
fi
```

### Step 14.4: Verify all skips have reasons

```bash
# Check for bare skips without reasons
grep -rn "@pytest.mark.skip$" src/tests/ --include="*.py"
# Should return 0 results — all skips must have reason= parameter
```

---

## Phase 15: Documentation Updates (30 min)

### Step 15.1: Update CLAUDE.md

Update the TL;DR and Current State sections with:
- New total test count (post-Stripe-removal)
- New passing count
- New pass rate
- Remove Stripe references (payment method, webhook handler, etc.)
- Version bump if appropriate

```bash
# Find current test count references
grep -n "test\|Test" CLAUDE.md | head -20
```

### Step 15.2: Update Milestone Checklist

**File:** `docs/IP2A_MILESTONE_CHECKLIST.md`

- Quick Stats table: update all test numbers
- Remove or update Stripe-related entries
- Add Week 35 section under a new heading

### Step 15.3: Update Roadmap

**File:** `docs/IP2A_BACKEND_ROADMAP.md`

- Executive Summary: update test count, ADR count
- Known Issues: remove Dispatch.bid bug if fixed, add any new bugs
- Phase 7 progress block: update numbers
- Remove Stripe from Technology Decisions if it was listed there, or mark as "Removed (ADR-018)"

### Step 15.4: Update CHANGELOG

**File:** `CHANGELOG.md`

Add Week 35 entry:

```markdown
### Week 35 — Stripe Removal & Bug Squash (February 2026)
- **Removed:** All Stripe payment processing code (ADR-018 — Square migration)
  - Deleted Stripe SDK, services, routes, webhook handlers, frontend integration
  - Removed ~27 Stripe-specific tests
  - Preserved all dues tracking models, services, and tests
- **Fixed:** [X] test failures across [Y] categories
  - Category A (Fixtures): [describe]
  - Category B (Schema Drift): [describe]
  - Category C (Collisions): [describe]
  - Category D (Logic): [describe]
- **Updated:** ADR-018 with Stripe Removal section
- **Test Results:** [TOTAL] total, [PASSED] passing, [FAILED] failing, [SKIPPED] skipped ([RATE]% pass rate)
```

### Step 15.5: Create session log

**File:** `docs/reports/session-logs/2026-02-XX-week35-stripe-removal-bug-squash.md`

(Use actual date)

```markdown
# Session Log: Week 35 — Stripe Removal & Bug Squash

**Date:** [DATE]
**Duration:** [X] hours across [Y] sessions
**Branch:** develop
**Starting Version:** v0.9.8-alpha

## Pre-Session Baseline
- Total: [X] | Passed: [Y] | Failed: [Z] | Errors: [E] | Skipped: [S]
- Pass rate: [X]%

## Session 35A: Stripe Removal
- Files deleted: [list]
- Files modified: [list]
- Tests removed: [count]
- Post-removal: Total [X] | Passed [Y] | Failed [Z] | Skipped [S]

## Session 35B: Bug Squash
- Category A fixes: [count] — [describe]
- Category B fixes: [count] — [describe]
- Category C fixes: [count] — [describe]
- Category D fixes: [count] — [describe]
- New bugs found: [list or none]

## Final Results
- Total: [X] | Passed: [Y] | Failed: [Z] | Errors: [E] | Skipped: [S]
- Pass rate: [X]%
- Target met: [yes/no]

## Files Changed
[list every file path, one per line]
```

---

## Phase 16: Final Commit (Session 35B/C)

```bash
git add -A
git status

git commit -m "fix: Week 35 bug squash — [PASS_RATE]% pass rate achieved

Session 35B/C: Systematic test repair across [X] categories
- Category A (Fixtures): [count] fixes
- Category B (Schema Drift): [count] fixes
- Category C (Collisions): [count] fixes
- Category D (Logic): [count] fixes
- Updated documentation: CLAUDE.md, Roadmap, Checklist, CHANGELOG
- Created session log

Final: [TOTAL] tests, [PASSED] passing, [FAILED] failing, [SKIPPED] skipped
Pass rate: [RATE]% (target: ≥95%)
"

git push origin develop
```

---

## Definition of Done — Week 35 Complete

| Criteria | Target |
|----------|--------|
| Stripe code in `src/` | Zero references (grep returns nothing) |
| Stripe in `requirements.txt` | Removed |
| Stripe tests | Deleted (not skipped) |
| Dues models/services/routes | Untouched |
| Dues tests | All still passing |
| ADR-018 | Updated with Stripe Removal section |
| ADR-013 | Status: Superseded |
| Pass rate (non-skipped) | ≥95% across 3 consecutive runs |
| ERROR tests | 0 |
| Every SKIP has reason string | Yes |
| Every remaining FAIL documented | Yes (in session log) |
| CLAUDE.md updated | Yes |
| CHANGELOG updated | Yes |
| Roadmap updated | Yes |
| Checklist updated | Yes |
| Session log created | Yes |

---

## Appendix A: ADR-018 Full Template (If Not Already Created)

If ADR-018 doesn't exist yet, create it at `docs/decisions/ADR-018-square-payment-integration.md`:

```markdown
# ADR-018: Square Payment Integration (Replacing Stripe)

**Status:** In Progress — Stripe Removed, Square Phase A Pending
**Date:** 2026-02-05
**Decision Makers:** Xerxes (Project Lead)
**Supersedes:** ADR-013 (Stripe Payment Integration)

## Context

UnionCore initially integrated Stripe (ADR-013) for dues payment processing. After evaluating operational needs, Square was selected as the replacement payment platform.

Key factors:
- Square's in-person payment hardware better fits union hall walk-in scenarios
- Square Terminal and Reader integration for on-site dues collection
- Combined online + in-person payment processing under one platform
- Square's invoicing capabilities align with dues billing workflows
- Competitive processing fees for the transaction volume expected

## Decision

Replace Stripe with Square as the payment processing platform.

**Migration approach:**
1. ✅ Stage ADR-018 and skip-mark Stripe tests (Week 28)
2. ✅ Remove all Stripe code (Week 35)
3. Implement Square integration in Phase 8 (Spoke 1: Core Platform)
4. Preserve ADR-013 for historical reference

## Stripe Removal (Week 35 — February 2026)

[Content from Phase 5 above]

## Consequences

### Positive
- Unified online + in-person payment processing
- Better fit for union hall walk-in payment scenarios
- Square Terminal/Reader hardware integration
- Native invoicing for dues billing
- Clean codebase — no dead Stripe code

### Negative
- Migration effort required (Spoke 1 sprint)
- Temporary period with no online payment processing
- Team must learn Square API patterns

### Neutral
- ADR-013 retained as historical reference
- Dues tracking layer is gateway-agnostic (no changes needed for Square)

## Implementation Phases

| Phase | Scope | Spoke | Status |
|-------|-------|-------|--------|
| Stripe Skip-Mark | Skip Stripe tests with ADR-018 ref | Spoke 2 | ✅ Done (Week 28) |
| Stripe Removal | Delete all Stripe code | Spoke 2 | ✅ Done (Week 35) |
| Square Phase A | Online payments (Square Web Payments SDK) | Spoke 1 | Pending |
| Square Phase B | In-person payments (Square Terminal API) | Spoke 1 | Pending |
| Square Phase C | Invoicing and auto-pay | Spoke 1 | Pending |
```

---

## Appendix B: Quick Reference — Files That Likely Contain Stripe

Based on project history, check these locations (paths may vary):

```
src/services/payment_service.py          — Stripe Checkout session creation
src/routers/webhooks/stripe_webhook.py   — Webhook handler
src/routers/webhooks/__init__.py         — May export stripe routes
src/config.py                            — STRIPE_* settings
src/main.py                              — Router registration
src/templates/dues/payment_*.html        — Stripe.js includes
src/templates/dues/success.html          — Post-payment redirect
src/templates/dues/cancel.html           — Payment cancelled page
src/static/js/stripe*.js                 — Stripe frontend code
src/tests/test_stripe*.py               — Stripe test files
src/tests/test_payment*.py              — Payment test files
src/tests/conftest.py                    — Stripe fixtures
.env.example                             — STRIPE_* vars
docker-compose.yml                       — STRIPE_* env passthrough
requirements.txt                         — stripe>=X.X.X
pyproject.toml                           — stripe dependency
```

---

*Claude Code Week 35 Instructions — February 5, 2026*
*Source: Hub Handoff → Spoke 2 (Operations)*
*For execution via Claude Code in VS Code*
