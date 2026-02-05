# Spoke 2 Instruction Document: Phase 7 Alembic Migration Generation

**Source:** Hub → Spoke 2 Handoff
**Date:** February 5, 2026
**Priority:** 🔴 HIGH — Blocks 68 tests
**Estimated Time:** 1-2 hours
**Branch:** `develop`
**Risk Level:** HIGH — Database schema changes. Follow every step. Do not skip verification.

---

## Context

Phase 7 models (6 total) were created during Weeks 20-21 but **Alembic migrations were never generated**. The models exist in `src/models/` and are imported, but the corresponding database tables do not exist. This blocks 68 tests (19 Phase 7 model tests + 22 referral frontend tests + 27 dispatch frontend tests).

The Feb 5 test diagnostic confirmed:
- Alembic HEAD: `9d48d853728b` (merge migration from Feb 5, 2026)
- Phase 7 migration files: **None found**
- Phase 7 tables in database: **None exist**

### ⚠️ IMPORTANT: "Schema is Law"

This is a migration that creates **6 new tables** for the referral and dispatch system — the single most critical business domain in UnionCore. Every column, constraint, and index matters. Do NOT rush this.

---

## Pre-Flight Checks (Do These First)

### Step 1: Verify Current State

```bash
# Check current Alembic HEAD
alembic current

# List existing migration files (confirm no Phase 7 migrations exist)
ls -la src/db/migrations/versions/ | grep -i "phase7\|referral\|dispatch\|registration\|labor\|bid"

# Check that Phase 7 tables do NOT exist in the database
python -c "
from src.db.session import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
phase7_tables = ['referral_books', 'book_registrations', 'registration_activities', 'labor_requests', 'job_bids', 'dispatches']
for t in phase7_tables:
    status = '✅ EXISTS' if t in tables else '❌ MISSING'
    print(f'{t}: {status}')
"
```

**Expected result:** All 6 tables should show ❌ MISSING. If any table already exists, STOP and report — something unexpected happened.

### Step 2: Verify Models Are Importable

```bash
# Confirm all 6 Phase 7 models import cleanly
python -c "
from src.models.referral_book import ReferralBook
from src.models.book_registration import BookRegistration
from src.models.registration_activity import RegistrationActivity
from src.models.labor_request import LaborRequest
from src.models.job_bid import JobBid
from src.models.dispatch import Dispatch
print('All 6 Phase 7 models imported successfully')
print(f'ReferralBook table: {ReferralBook.__tablename__}')
print(f'BookRegistration table: {BookRegistration.__tablename__}')
print(f'RegistrationActivity table: {RegistrationActivity.__tablename__}')
print(f'LaborRequest table: {LaborRequest.__tablename__}')
print(f'JobBid table: {JobBid.__tablename__}')
print(f'Dispatch table: {Dispatch.__tablename__}')
"
```

**Expected result:** All 6 models import with their `__tablename__` values printed. Note the exact table names — these are what Alembic will create.

### Step 3: Verify Models Are Registered in Alembic's Target Metadata

Check that all Phase 7 models are imported in the file that Alembic uses for autogenerate. This is typically `src/db/base.py` or whichever file collects all models for `Base.metadata`.

```bash
# Check what models are imported in the base module
grep -n "from src.models" src/db/base.py
# OR check Alembic's env.py for metadata source
grep -n "target_metadata\|import.*models\|import.*Base" src/db/migrations/env.py
```

**⛔ IF Phase 7 models are NOT imported in the metadata source:** Add the imports before generating the migration. The models must be registered with SQLAlchemy's `Base.metadata` for autogenerate to detect them.

```python
# Add these imports to src/db/base.py (or equivalent) if missing:
from src.models.referral_book import ReferralBook
from src.models.book_registration import BookRegistration
from src.models.registration_activity import RegistrationActivity
from src.models.labor_request import LaborRequest
from src.models.job_bid import JobBid
from src.models.dispatch import Dispatch
```

### Step 4: Verify Dispatch.bid Relationship Fix

The Feb 5 session log confirmed this was already fixed, but let's verify since the Known Issues docs still list it as CRITICAL.

```bash
# Check that foreign_keys parameter exists on both sides
grep -n "foreign_keys" src/models/dispatch.py
grep -n "foreign_keys" src/models/job_bid.py
```

**Expected:** Both files should have `foreign_keys=[bid_id]` or `foreign_keys="[Dispatch.bid_id]"` in their relationship definitions. If NOT present, fix this BEFORE generating the migration — the relationship definition can affect how Alembic generates foreign key constraints.

---

## Migration Generation

### Step 5: Generate the Migration (Autogenerate)

```bash
# Generate the migration
alembic revision --autogenerate -m "phase7_referral_dispatch_tables"
```

This should produce a new migration file in `src/db/migrations/versions/`.

### Step 6: REVIEW the Generated Migration (CRITICAL)

**⛔ DO NOT apply the migration without reviewing it first.**

Open the generated migration file and verify:

```bash
# Find and display the new migration file
ls -lt src/db/migrations/versions/ | head -5
# Then read it:
cat src/db/migrations/versions/<new_migration_filename>.py
```

**Review checklist — verify the migration contains:**

| Check | What to Look For |
|-------|-----------------|
| **6 tables created** | `op.create_table('referral_books', ...)`, `op.create_table('book_registrations', ...)`, etc. |
| **No unexpected tables** | Should NOT create tables for models that don't exist yet (check_marks, member_exemptions, etc.) |
| **No table drops** | `upgrade()` should only have `create_table` and `create_index`, never `drop_table` |
| **APN is DECIMAL(10,2)** | `book_registrations.applicant_priority_number` must be `sa.Numeric(10, 2)` — NOT Integer |
| **referral_books.contract_code is NULLABLE** | Should NOT have `nullable=False` on contract_code |
| **Foreign keys** | FK to `members.id`, FK relationships between Phase 7 tables |
| **Audit columns** | `created_at`, `updated_at`, `created_by`, `updated_by` on tables that need them |
| **Indexes** | Any indexes defined in the models should appear |
| **downgrade() is clean** | Should drop tables in reverse FK order |
| **No unrelated changes** | Autogenerate sometimes detects schema drift in existing tables — remove any unrelated operations |

**🔴 CRITICAL APN CHECK:** If `applicant_priority_number` is Integer instead of Numeric/Decimal, **DO NOT PROCEED**. Fix the model definition first. Integer truncation of APN data will destroy dispatch ordering (see ADR-015, CLAUDE.md Phase 7 reminders).

**If the migration contains unrelated changes** (schema drift detection for existing tables), remove those operations from both `upgrade()` and `downgrade()`. This migration should ONLY create Phase 7 tables.

### Step 7: Fix Any Issues Found in Review

If the review found problems:

1. Fix the model definitions in `src/models/`
2. Delete the generated migration file
3. Re-run `alembic revision --autogenerate -m "phase7_referral_dispatch_tables"`
4. Re-review

Repeat until the migration is clean.

---

## Migration Application

### Step 8: Apply the Migration

```bash
# Apply the migration
alembic upgrade head
```

### Step 9: Verify Tables Were Created

```bash
# Confirm all 6 tables now exist
python -c "
from src.db.session import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
phase7_tables = ['referral_books', 'book_registrations', 'registration_activities', 'labor_requests', 'job_bids', 'dispatches']
for t in phase7_tables:
    status = '✅ EXISTS' if t in tables else '❌ MISSING'
    print(f'{t}: {status}')
print(f'\nTotal tables in database: {len(tables)}')
"
```

**Expected:** All 6 tables show ✅ EXISTS.

### Step 10: Verify Table Structure

Spot-check the critical columns:

```bash
python -c "
from src.db.session import engine
from sqlalchemy import inspect
inspector = inspect(engine)

# Check APN column type on book_registrations
for col in inspector.get_columns('book_registrations'):
    if 'priority' in col['name'].lower() or 'apn' in col['name'].lower():
        print(f\"APN column: {col['name']} — Type: {col['type']} — Nullable: {col['nullable']}\")

# Check contract_code nullable on referral_books
for col in inspector.get_columns('referral_books'):
    if 'contract' in col['name'].lower():
        print(f\"Contract column: {col['name']} — Nullable: {col['nullable']}\")

# Check foreign keys on dispatches
fks = inspector.get_foreign_keys('dispatches')
print(f'\nDispatches foreign keys: {len(fks)}')
for fk in fks:
    print(f\"  {fk['constrained_columns']} → {fk['referred_table']}.{fk['referred_columns']}\")
"
```

**Expected:**
- APN type should be NUMERIC (not INTEGER)
- contract_code should be nullable=True
- dispatches should have FK references to other tables

---

## Test Verification

### Step 11: Run Phase 7 Tests

```bash
# Run Phase 7 model tests first
pytest src/tests/test_phase7_models.py -v

# Run referral frontend tests
pytest src/tests/test_referral_frontend.py -v

# Run dispatch frontend tests
pytest src/tests/test_dispatch_frontend.py -v
```

### Step 12: Run Full Test Suite

```bash
# Full suite with summary
pytest -v --tb=short 2>&1 | tail -30
```

**Expected improvement:** ~68 previously blocked tests should now pass. Target pass rate: **90%+** (up from 84.7%).

Record the exact counts:
- Total tests:
- Passed:
- Failed:
- Errors:
- Skipped:

---

## ⛔ Rollback Plan

If something goes wrong after applying the migration:

```bash
# Downgrade to the previous migration
alembic downgrade -1

# Verify tables are removed
python -c "
from src.db.session import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
phase7 = ['referral_books', 'book_registrations', 'registration_activities', 'labor_requests', 'job_bids', 'dispatches']
for t in phase7:
    print(f'{t}: {\"EXISTS\" if t in tables else \"REMOVED\"}')
"
```

---

## Documentation Updates

### After successful migration, update these files:

**1. Milestone Checklist (`docs/IP2A_MILESTONE_CHECKLIST.md`):**

The checklist line 546 currently says:
```
| Create Alembic migration for all 12 tables | 2 hrs | Done |
```

This was marked "Done" prematurely. Update the note under Sub-Phase 7b to clarify:
```
**Note:** Alembic migration generated and applied [DATE]. Creates 6 tables (not 12 — remaining 6 tables deferred to future sub-phases).
```

**2. Known Issues section** — If Dispatch.bid bug is confirmed fixed (Step 4), update:
- Milestone Checklist §7.8 item #1: Change from 🔴 HIGH PRIORITY to ✅ RESOLVED
- Known Issues section: Update status from 🔴 to ✅ RESOLVED with date
- Quick Stats: Update from "568 passing, 25 blocked" to actual post-migration numbers

**3. CLAUDE.md** — Update the "Remaining Issues" section to remove "Phase 7 migrations not yet applied" and update test counts.

---

## Session Log Template

After completing this session, create a session log at:
`docs/reports/session-logs/YYYY-MM-DD-phase7-migration.md`

Include:
- Pre-migration state (Alembic HEAD, table status)
- Migration file name and contents summary
- Post-migration verification results
- Test suite results (before/after)
- Any issues encountered and how they were resolved
- Documentation updates made

---

## Success Criteria

- [ ] All 6 Phase 7 tables exist in the database
- [ ] APN column is NUMERIC(10,2), not INTEGER
- [ ] referral_books.contract_code is NULLABLE
- [ ] Phase 7 model tests pass
- [ ] Referral frontend tests pass (or failures are unrelated to missing tables)
- [ ] Dispatch frontend tests pass (or failures are unrelated to missing tables)
- [ ] Full test suite pass rate ≥ 90%
- [ ] Migration has clean downgrade path
- [ ] Dispatch.bid relationship status verified and documented
- [ ] Documentation updated (Checklist, Known Issues, CLAUDE.md)
- [ ] Session log created
- [ ] All changes committed and pushed to `develop`
