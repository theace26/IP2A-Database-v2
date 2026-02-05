# Claude Code Instructions: Week 28 — Full Test Suite Repair

**Created:** February 5, 2026
**Source:** Hub → Spoke 2 Consolidated (Multiple Diagnostic Sessions)
**Context:** UnionCore (IP2A-Database-v2) — IBEW Local 46
**Estimated Time:** 2-3 hours
**Branch:** `develop`
**Goal:** Get every fixable test passing. Zero known-broken tests hanging over our heads.

---

## ⚠️ SCOPE — READ FIRST

**THIS SESSION DOES:**
- Diagnose every failing test
- Fix the Dispatch.bid relationship bug (blocks 25 tests)
- Ensure Phase 7 Alembic migrations exist and are applied
- Skip-mark Stripe tests with ADR-018 reference (Square replacing Stripe)
- Fix miscellaneous test failures (fixture issues, import errors, schema drift)
- Stage ADR-018 (Square Payment Integration)
- Update ADR-013 status to "Superseded by ADR-018"
- Update test counts across all documentation

**THIS SESSION DOES NOT:**
- Write any Square integration code
- Remove Stripe source code (that happens later)
- Create new features or new models
- Modify business logic in services
- Change any model schemas (flag for Hub if needed)

---

## Pre-Flight

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
```

### Verify Database is Running

```bash
docker-compose up -d
```

### Verify Alembic State

```bash
alembic current
alembic heads
```

**Expected:** Single head, no multiple heads. If you see multiple heads, there's a merge migration issue — STOP and report.

### Capture Baseline

```bash
pytest -v --tb=short 2>&1 | tee /tmp/baseline_test_output.txt
echo "---"
pytest -v --tb=short 2>&1 | tail -5
```

Record: X passed, Y failed, Z errors. This is our starting point.

---

## Phase 1: Fix Dispatch.bid Relationship Bug (CRITICAL — Blocks 25 Tests)

**File:** `src/models/dispatch.py`
**Error:** `Could not determine join condition between parent/child tables on relationship Dispatch.bid`
**Root Cause:** The Dispatch model has a `bid_id` FK to `job_bids` AND likely another relationship path through `labor_request_id`. SQLAlchemy can't auto-resolve the join when multiple FK paths exist to related tables.

### Investigation

```bash
# Find the Dispatch model
cat src/models/dispatch.py
```

### Fix

Locate the `bid` relationship on the Dispatch model. Add the `foreign_keys` parameter:

```python
# BEFORE (broken):
bid = relationship("JobBid", back_populates="dispatch")

# AFTER (fixed):
bid = relationship("JobBid", foreign_keys=[bid_id], back_populates="dispatch")
```

**ALSO CHECK** the JobBid model for the reciprocal relationship:

```bash
cat src/models/job_bid.py
```

If JobBid has a `dispatch` relationship, verify it also specifies `foreign_keys` if needed. The back_populates must match on both sides.

### Verify Fix

```bash
# Quick smoke test — import the model
python -c "from src.models.dispatch import Dispatch; print('Dispatch model loads OK')"

# Run just dispatch tests
pytest src/tests/test_dispatch_frontend.py -v --tb=short 2>&1 | tail -30
```

**Expected:** 25 previously-blocked tests should now either pass or show NEW errors (which we'll fix in later phases). If you still see the relationship error, the fix didn't land — re-examine the model.

---

## Phase 2: Ensure Phase 7 Alembic Migrations Exist

Phase 7 added 6 tables: `referral_books`, `book_registrations`, `registration_activities`, `labor_requests`, `job_bids`, `dispatches`. These models were created during Weeks 20-21 but migrations may not have been generated.

### Check If Tables Exist

```bash
python -c "
from src.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
phase7 = ['referral_books', 'book_registrations', 'registration_activities', 'labor_requests', 'job_bids', 'dispatches']
for t in phase7:
    print(f\"  {'✅' if t in tables else '❌'} {t}\")
"
```

### If Tables Are MISSING

```bash
# Check if migration file exists
ls alembic/versions/ | grep -i "phase7\|referral\|dispatch\|registration"
```

**If NO migration file exists:**

```bash
# Verify all models are imported in models/__init__.py
grep -E "referral_book|book_registration|registration_activity|labor_request|job_bid|dispatch" src/models/__init__.py
```

If models aren't imported in `__init__.py`, add them. Then:

```bash
alembic revision --autogenerate -m "phase7_referral_dispatch_tables"
```

**CRITICAL CHECKS before applying:**

1. Open the generated migration file
2. Verify `referral_books` has: `applicant_priority_number DECIMAL(10,2)` — NOT INTEGER
3. Verify `book_registrations` unique constraint is `(member_id, book_id, book_priority_number)` — NOT `(member_id, book_id)`
4. Verify `referral_books.contract_code` is NULLABLE
5. If any of these are wrong, the models need fixing FIRST

```bash
alembic upgrade head
```

### If Tables Already Exist

Good — move on.

### Verify

```bash
python -c "
from src.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
phase7 = ['referral_books', 'book_registrations', 'registration_activities', 'labor_requests', 'job_bids', 'dispatches']
missing = [t for t in phase7 if t not in tables]
if missing:
    print(f'FAIL: Missing tables: {missing}')
else:
    print('All 6 Phase 7 tables exist ✅')
"
```

---

## Phase 3: Skip-Mark Stripe Tests (ADR-018 — Square Replacing Stripe)

Stripe is being replaced by Square (ADR-018, decision date February 5, 2026). Stripe tests should be skip-marked, NOT deleted. The code stays as reference for the Square implementation.

### Identify Stripe Test Files

```bash
find src/tests/ -name "*.py" -exec grep -l "stripe\|Stripe\|STRIPE" {} \;
```

### Apply Skip Marks

For each file that contains Stripe-specific tests, add a module-level skip marker at the top of the file (after imports):

```python
import pytest

pytestmark = pytest.mark.skip(reason="Stripe deprecated — ADR-018 Square migration pending")
```

**BE PRECISE.** If a test file mixes Stripe and non-Stripe tests, only skip the Stripe-specific test functions/classes — don't skip the whole module. Use:

```python
@pytest.mark.skip(reason="Stripe deprecated — ADR-018 Square migration pending")
def test_stripe_checkout_session():
    ...
```

### Verify

```bash
pytest -v --tb=short 2>&1 | grep -c "SKIPPED"
```

Record how many tests were skip-marked.

---

## Phase 4: Stage ADR-018 (Square Payment Integration)

### Create ADR-018

```bash
cat > docs/decisions/ADR-018-square-payment-integration.md << 'EOF'
# ADR-018: Square Payment Integration (Replacing Stripe)

**Status:** Accepted
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
1. Stage ADR-018 and skip-mark Stripe tests (this session)
2. Implement Square integration in a future sprint (Spoke 1: Core Platform)
3. Remove Stripe code after Square is verified in production
4. Preserve Stripe code as reference during migration

## Consequences

### Positive
- Unified online + in-person payment processing
- Better fit for union hall walk-in payment scenarios
- Square Terminal/Reader hardware integration
- Native invoicing for dues billing

### Negative
- Migration effort required (Spoke 1 sprint)
- Temporary period with no payment processing during switchover
- Team must learn Square API patterns

### Neutral
- Stripe tests preserved as skip-marked reference during migration
- ADR-013 marked as superseded, not deleted

## Implementation Notes

- Square SDK: `squareup` Python package
- Endpoints: Payments API, Invoices API, Terminal API
- Webhook verification pattern similar to Stripe
- Spoke 1 (Core Platform) owns the migration
EOF
```

### Update ADR-013 Status

```bash
# Find ADR-013 and add superseded notice at top
head -5 docs/decisions/ADR-013-stripe-payment-integration.md
```

Add to the top of ADR-013 (after the title):

```
**Status:** Superseded by [ADR-018](ADR-018-square-payment-integration.md) (2026-02-05)
```

### Update ADR Index

```bash
cat docs/decisions/README.md
```

Add ADR-018 entry to the index table. Ensure ADR-013 shows "Superseded" status.

---

## Phase 5: Diagnose and Fix Remaining Test Failures

Now run the full suite and categorize whatever's left:

```bash
pytest -v --tb=short 2>&1 | tee /tmp/post_fixes_output.txt
```

### Extract Just the Failures

```bash
grep -E "FAILED|ERROR" /tmp/post_fixes_output.txt
```

### Categorize Each Failure

For each failure, determine root cause:

| Category | Symptoms | Action |
|----------|----------|--------|
| **Fixture issues** | Missing required fields, wrong field names | Fix the fixture |
| **Import errors** | Module not found, circular imports | Fix the import path |
| **Schema drift** | Model field doesn't match test expectation | Update test to match model |
| **Missing tables** | IntegrityError on INSERT, relation does not exist | Phase 2 migration needed |
| **Relationship errors** | Can't determine join condition | Add `foreign_keys` parameter |
| **Enum mismatches** | Invalid enum value | Update test to use correct enum |
| **RedirectResponse** | 307 instead of expected 200/302 | Add trailing slash to test URL or router |
| **Auth/permission** | 401/403 when expecting 200 | Fix test fixture auth setup |
| **Architectural** | Fundamental design issue | Flag for Hub — DO NOT GUESS |

### Common Fix Patterns

**RedirectResponse (307 vs 200):**
If a test sends `GET /some-path` and gets 307, the router likely has `GET /some-path/` (trailing slash). Fix: add trailing slash to the test request URL.

**Missing `assigned_at` on user_roles:**
If user_roles INSERT tests fail, the fixture may be missing the `assigned_at` timestamp field added during migration drift resolution. Add it to the test fixture.

**Enum value errors:**
Check `src/db/enums/` for the correct enum values. Tests may use old string values.

### Fix Each Category

Work through failures systematically. After each fix, re-run just that test file to confirm:

```bash
pytest src/tests/test_SPECIFIC_FILE.py -v --tb=short
```

### Failures That Need Hub Review

If you encounter failures that require:
- Model schema changes
- New migration columns
- Business logic changes
- Security/auth architecture changes

**DO NOT FIX.** Instead, document them:

```bash
cat >> /tmp/hub_review_items.txt << EOF
## Hub Review Required

### [Test Name]
- **File:** src/tests/test_xxx.py::test_yyy
- **Error:** [error message]
- **Root Cause:** [1-2 sentences]
- **Proposed Fix:** [what you think should happen]
- **Why Hub:** [architectural/security/schema reason]
EOF
```

---

## Phase 6: Final Verification

```bash
pytest -v --tb=short 2>&1 | tee /tmp/final_test_output.txt
echo "=== SUMMARY ==="
tail -5 /tmp/final_test_output.txt
```

### Expected Outcome

| Category | Count | Status |
|----------|-------|--------|
| Passing | [number] | ✅ |
| Skipped (Stripe/ADR-018) | [number] | ⏭️ Expected |
| Failed | 0 | 🎯 Target |
| Errors | 0 | 🎯 Target |

If any tests are still failing that you couldn't fix, document WHY and categorize them.

---

## Phase 7: Documentation Updates

### Update Test Counts

After all fixes, update these files with the ACTUAL test counts from the final `pytest` run:

**CLAUDE.md** — TL;DR section and Current State table
**docs/IP2A_BACKEND_ROADMAP.md** — Executive Summary `Total Tests` line
**docs/IP2A_MILESTONE_CHECKLIST.md** — Quick Stats section
**docs/README.md** — Current Status table (if this file exists and has test counts)

### Update Known Issues

In both `docs/IP2A_BACKEND_ROADMAP.md` and `docs/IP2A_MILESTONE_CHECKLIST.md`, update or remove the "Known Issues" section for the Dispatch.bid bug (now fixed).

### Create Session Log

```bash
cat > docs/reports/session-logs/2026-02-05-week28-test-repair.md << EOF
# Session Log: Week 28 — Test Suite Repair

**Date:** $(date +%Y-%m-%d)
**Sprint:** Week 28
**Spoke:** Spoke 2 (Operations)
**Version:** v0.9.8-alpha → v0.9.9-alpha (if version bumped)

## Work Completed

### Dispatch.bid Relationship Fix
- Added \`foreign_keys=[bid_id]\` to Dispatch.bid relationship
- Unblocked [X] tests

### Phase 7 Migration Status
- [Tables existed / Migration generated and applied]

### Stripe Test Skip-Marking (ADR-018)
- [X] tests skip-marked across [Y] files
- ADR-018 staged in docs/decisions/
- ADR-013 marked as superseded

### Other Test Fixes
- [List each fix: file, what was wrong, how fixed]

## Test Results

| Category | Count |
|----------|-------|
| Total | [X] |
| Passing | [X] |
| Skipped | [X] |
| Failed | [X] |

## Hub Review Items
- [List any items that need Hub decision, or "None"]

## Files Changed
- [List every file changed as /dir/file paths]
EOF
```

---

## Phase 8: Commit

```bash
ruff check . --fix
ruff format .

git add -A
git status

git commit -m "fix: Week 28 test suite repair — Dispatch.bid bug, Stripe skip-marks, ADR-018

- Fixed Dispatch.bid relationship (foreign_keys parameter) — unblocked 25 tests
- Skip-marked Stripe tests (ADR-018: Square replacing Stripe)
- Staged ADR-018, marked ADR-013 as superseded
- Applied Phase 7 migrations (if needed)
- Fixed [N] additional test failures: [brief list]
- Updated test counts in CLAUDE.md, Roadmap, Checklist
- Session log: docs/reports/session-logs/2026-02-05-week28-test-repair.md

Test suite: [X] passed, [Y] skipped, 0 failed
"

git push origin develop
```

---

## Checklist (Verify Before Closing)

- [ ] Dispatch.bid relationship fixed
- [ ] Phase 7 tables exist in database
- [ ] Stripe tests skip-marked (not deleted)
- [ ] ADR-018 created in docs/decisions/
- [ ] ADR-013 marked superseded
- [ ] ADR index (docs/decisions/README.md) updated
- [ ] All fixable tests passing
- [ ] Test counts updated in: CLAUDE.md, Roadmap, Checklist
- [ ] Session log created
- [ ] Hub review items documented (if any)
- [ ] `ruff check` and `ruff format` clean
- [ ] Committed and pushed to `develop`
- [ ] List of ALL changed files provided

---

## ⚠️ CHANGED FILES — MANDATORY

**After completing all tasks, list every file you changed or created as `/dir/file` paths.** The developer needs this list to track what was touched. This is non-negotiable.

---

*End of Instructions*
