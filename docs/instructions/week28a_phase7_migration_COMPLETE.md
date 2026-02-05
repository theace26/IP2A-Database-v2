# Claude Code Instruction: Phase 7 Alembic Migration

**Spoke:** 2 (Operations)
**Date:** February 5, 2026
**Priority:** 🔴 HIGH — Blocks 68 tests
**Estimated Time:** 1-2 hours
**Branch:** `develop`
**Risk Level:** HIGH — Database schema changes

---

## TL;DR

Phase 7 models (6 total: ReferralBook, BookRegistration, RegistrationActivity, LaborRequest, JobBid, Dispatch) were created during Weeks 20-21 but **Alembic migrations were never generated**. Tables don't exist in the database. This blocks 68 tests.

---

## Pre-Flight

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
```

---

## Step 1: Verify Current State

Confirm Phase 7 tables do NOT exist yet and identify current Alembic HEAD.

```bash
alembic current
```

```bash
ls -la src/db/migrations/versions/ | grep -i "phase7\|referral\|dispatch\|registration\|labor\|bid"
```

```python
# Run this to check table existence
from src.db.session import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
phase7_tables = ['referral_books', 'book_registrations', 'registration_activities', 'labor_requests', 'job_bids', 'dispatches']
for t in phase7_tables:
    status = '✅ EXISTS' if t in tables else '❌ MISSING'
    print(f'{t}: {status}')
```

**Expected:** All 6 tables ❌ MISSING. If any exist, STOP — something unexpected happened.

---

## Step 2: Verify Models Import Cleanly

```python
from src.models.referral_book import ReferralBook
from src.models.book_registration import BookRegistration
from src.models.registration_activity import RegistrationActivity
from src.models.labor_request import LaborRequest
from src.models.job_bid import JobBid
from src.models.dispatch import Dispatch
print('All 6 Phase 7 models imported successfully')
for m in [ReferralBook, BookRegistration, RegistrationActivity, LaborRequest, JobBid, Dispatch]:
    print(f'  {m.__name__}: {m.__tablename__}')
```

**Expected:** All 6 import with table names printed.

---

## Step 3: Verify Models Are in Alembic's Target Metadata

Models must be imported somewhere that feeds `Base.metadata` for autogenerate to detect them.

```bash
grep -n "from src.models" src/db/base.py
grep -n "target_metadata\|import.*models\|import.*Base" src/db/migrations/env.py
```

**⛔ IF Phase 7 models are NOT imported in the metadata source:** Add the imports before generating the migration:

```python
# Add to src/db/base.py (or equivalent) if missing:
from src.models.referral_book import ReferralBook
from src.models.book_registration import BookRegistration
from src.models.registration_activity import RegistrationActivity
from src.models.labor_request import LaborRequest
from src.models.job_bid import JobBid
from src.models.dispatch import Dispatch
```

---

## Step 4: Verify Dispatch.bid Relationship Fix

The Dispatch.bid bug was reported as blocking 25 tests. Verify the fix is in place BEFORE generating the migration.

```bash
grep -n "foreign_keys" src/models/dispatch.py
grep -n "foreign_keys" src/models/job_bid.py
```

**Expected:** Both files have `foreign_keys=[bid_id]` or equivalent. If NOT present, fix this first:

```python
# In src/models/dispatch.py:
bid = relationship("JobBid", foreign_keys=[bid_id], back_populates="dispatch")
```

---

## Step 5: Generate the Migration

```bash
alembic revision --autogenerate -m "phase7_referral_dispatch_tables"
```

---

## Step 6: REVIEW the Generated Migration (CRITICAL — DO NOT SKIP)

```bash
ls -lt src/db/migrations/versions/ | head -5
```

Open and read the new migration file. **Verify ALL of these:**

| Check | What to Look For |
|-------|------------------|
| **6 tables created** | `op.create_table('referral_books')`, `op.create_table('book_registrations')`, etc. |
| **No unexpected tables** | Should NOT create check_marks, member_exemptions, etc. |
| **No table drops** | `upgrade()` should ONLY have `create_table` and `create_index` |
| **🔴 APN is DECIMAL(10,2)** | `book_registrations.applicant_priority_number` → `sa.Numeric(10, 2)` — **NOT Integer** |
| **referral_books.contract_code is NULLABLE** | Must NOT have `nullable=False` |
| **Foreign keys present** | FK to `members.id`, FKs between Phase 7 tables |
| **Audit columns** | `created_at`, `updated_at`, `created_by`, `updated_by` where needed |
| **Indexes** | Any model-defined indexes should appear |
| **downgrade() is clean** | Should drop tables in reverse FK order |
| **No unrelated changes** | Remove any autogenerate drift for existing tables |

### 🔴 CRITICAL APN CHECK

If `applicant_priority_number` is `sa.Integer()` instead of `sa.Numeric(10, 2)`:

1. **DO NOT PROCEED**
2. Fix the model in `src/models/book_registration.py`
3. Delete the generated migration file
4. Re-run `alembic revision --autogenerate -m "phase7_referral_dispatch_tables"`
5. Re-review

**Why:** Integer truncation of APN destroys dispatch ordering. APN encodes Excel serial date (integer part) + secondary sort key (decimal part). This is a data-destroying bug if deployed. See ADR-015.

### If Migration Contains Unrelated Changes

Remove those operations from BOTH `upgrade()` and `downgrade()`. This migration should ONLY create Phase 7 tables.

---

## Step 7: Apply the Migration

```bash
alembic upgrade head
```

---

## Step 8: Verify Tables Created

```python
from src.db.session import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
phase7_tables = ['referral_books', 'book_registrations', 'registration_activities', 'labor_requests', 'job_bids', 'dispatches']
for t in phase7_tables:
    status = '✅ EXISTS' if t in tables else '❌ MISSING'
    print(f'{t}: {status}')
print(f'\nTotal tables in database: {len(tables)}')
```

**Expected:** All 6 ✅ EXISTS.

---

## Step 9: Verify Critical Column Types

```python
from src.db.session import engine
from sqlalchemy import inspect
inspector = inspect(engine)

# APN column type
for col in inspector.get_columns('book_registrations'):
    if 'priority' in col['name'].lower() or 'apn' in col['name'].lower():
        print(f"APN column: {col['name']} — Type: {col['type']} — Nullable: {col['nullable']}")

# contract_code nullable
for col in inspector.get_columns('referral_books'):
    if 'contract' in col['name'].lower():
        print(f"Contract column: {col['name']} — Nullable: {col['nullable']}")

# dispatches foreign keys
fks = inspector.get_foreign_keys('dispatches')
print(f'\nDispatches foreign keys: {len(fks)}')
for fk in fks:
    print(f"  {fk['constrained_columns']} → {fk['referred_table']}.{fk['referred_columns']}")
```

**Expected:**
- APN type = NUMERIC (not INTEGER)
- contract_code nullable = True
- dispatches has FK references

---

## Step 10: Run Phase 7 Tests

```bash
# Phase 7 model tests
pytest src/tests/test_phase7_models.py -v

# Referral frontend tests
pytest src/tests/test_referral_frontend.py -v

# Dispatch frontend tests
pytest src/tests/test_dispatch_frontend.py -v
```

---

## Step 11: Full Test Suite

```bash
pytest -v --tb=short 2>&1 | tail -30
pytest --tb=no -q
```

**Record exact counts:**
- Total tests:
- Passed:
- Failed:
- Errors:
- Skipped:

**Target:** ≥90% pass rate (up from 84.7% pre-migration).

---

## Rollback Plan

If something goes wrong:

```bash
alembic downgrade -1
```

Verify tables removed, then investigate and fix before retrying.

---

## Documentation Updates (After Successful Migration)

### 1. Milestone Checklist (`docs/IP2A_MILESTONE_CHECKLIST.md`)

Update Sub-Phase 7b note:
```
**Note:** Alembic migration generated and applied [DATE]. Creates 6 tables.
```

### 2. Known Issues

If Dispatch.bid bug confirmed fixed (Step 4):
- Milestone Checklist §7.8 item #1: ⛔ → ✅ RESOLVED
- Known Issues section: Update status with date
- Quick Stats: Update from "568 passing, 25 blocked" to actual numbers

### 3. CLAUDE.md

- Remove "Phase 7 migrations not yet applied" from Remaining Issues
- Update test counts

### 4. Session Log

Create: `docs/reports/session-logs/YYYY-MM-DD-phase7-migration.md`

Include: pre-migration state, migration file summary, post-migration verification, test results, issues encountered.

---

## Success Criteria

- [ ] All 6 Phase 7 tables exist in database
- [ ] APN column is NUMERIC(10,2), not INTEGER
- [ ] referral_books.contract_code is NULLABLE
- [ ] Phase 7 model tests pass
- [ ] Referral frontend tests pass (or failures unrelated to tables)
- [ ] Dispatch frontend tests pass (or failures unrelated to tables)
- [ ] Full test suite ≥ 90% pass rate
- [ ] Migration has clean downgrade path
- [ ] Dispatch.bid relationship verified and documented
- [ ] Documentation updated
- [ ] Session log created
- [ ] Committed and pushed to `develop`

---

## Changed Files (List After Completion)

After completing all tasks, list every file changed or created as `/dir/file` paths.
