# ISSUE-001: Database Migration Drift Resolution

**Date Discovered:** February 5, 2026
**Date Resolved:** February 5, 2026
**Severity:** Critical (blocked Phase 7 testing)
**Affected Components:** Alembic migrations, Stripe integration, Grant enrollment, User roles

## Problem Description

Database schema out of sync with SQLAlchemy models. Multiple migration heads existed from parallel feature development branches (Stripe integration + Grant enrollment). Cross-branch enum dependencies and missing columns caused migration failures.

## Diagnostic Output

```
=== MIGRATION DIAGNOSTIC REPORT ===
Timestamp: 2026-02-05T02:28:43+00:00
Branch: develop
Last commit: 18cf812 docs: Add session log for Dispatch.bid relationship fix

=== ALEMBIC HEADS (Multiple = Problem) ===
Head count: 2

813f955b11af (head)  ← Branch 1: User roles fix
j5e6f7g8h9i0 (head)  ← Branch 2: Grant enrollment

Current database revision: 9b75a876ef60 (Pre-apprenticeship training models)
```

## Root Cause

**Primary Issue:** Migrations created in parallel branches without merging
- Branch 1 (Stripe/User Fixes): `0b9b93948cdb` → `bc1f99c730dc` → ... → `813f955b11af`
- Branch 2 (Grants/Audit): `0b9b93948cdb` → `f1a2b3c4d5e6` → ... → `j5e6f7g8h9i0`

**Secondary Issues:**
1. **Cross-branch enum dependency:** Branch 2 migration `g2b3c4d5e6f7` tried to add values to `duespaymentmethod` enum before it was created (defined in Branch 1 migration `ee8ead726e9b`)
2. **Missing columns:** Migration `813f955b11af` INSERT statement missing `assigned_at` and `updated_at` columns
3. **Duplicate enum creation:** Grant enrollment migration trying to create enums that already existed from failed attempts
4. **PostgreSQL enum syntax:** Attempted use of `CREATE TYPE IF NOT EXISTS` which is not valid PostgreSQL syntax

## Resolution Steps

### 1. Created Merge Migration
```bash
alembic merge heads -m "merge_migration_heads_20260205"
# Generated: 9d48d853728b_merge_migration_heads_20260205.py
```

### 2. Fixed Migration `813f955b11af` (fix_missing_user_roles)
**Problem:** INSERT missing `assigned_at` and `updated_at` columns
**Fix:** Added both columns to INSERT statement
```sql
-- Before
INSERT INTO user_roles (user_id, role_id, assigned_by, created_at)
VALUES (:user_id, :role_id, 'migration_fix', NOW())

-- After
INSERT INTO user_roles (user_id, role_id, assigned_by, assigned_at, created_at, updated_at)
VALUES (:user_id, :role_id, 'migration_fix', NOW(), NOW(), NOW())
```

### 3. Fixed Migration `g2b3c4d5e6f7` (add_stripe_payment_methods_to_enum)
**Problem:** Tried to ALTER non-existent enum
**Fix:** Added check for enum existence, creates with all values if missing
```python
result = conn.execute(sa.text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'duespaymentmethod')"))
if not result.scalar():
    # Create enum with all values (including Stripe) if it doesn't exist
    op.execute("CREATE TYPE duespaymentmethod AS ENUM (..., 'stripe_card', 'stripe_ach', 'stripe_other')")
else:
    # Add Stripe values to existing enum
    op.execute("ALTER TYPE duespaymentmethod ADD VALUE IF NOT EXISTS 'stripe_card'")
    ...
```

### 4. Fixed Migration `ee8ead726e9b` (add_dues_tracking_models)
**Problem:** Used invalid `CREATE TYPE IF NOT EXISTS` syntax
**Fix:** Added explicit existence check before creation
```python
result = conn.execute(sa.text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'duespaymentmethod')"))
if not result.scalar():
    op.execute("CREATE TYPE duespaymentmethod AS ENUM (...)")
```

### 5. Fixed Migration `j5e6f7g8h9i0` (add_grant_enrollment_and_enhance_grant)
**Problem:** Enum creation conflicts during table creation
**Fix:**
- Added DROP CASCADE for enums at start of migration
- Switched grant_enrollments table creation to raw SQL to avoid enum recreation issues
```python
# Drop and recreate enums cleanly
conn.execute(sa.text("DROP TYPE IF EXISTS grant_status CASCADE"))
conn.execute(sa.text("DROP TYPE IF EXISTS grant_enrollment_status CASCADE"))
conn.execute(sa.text("DROP TYPE IF EXISTS grant_outcome CASCADE"))

# Create enums
grant_status_enum = sa.Enum(..., name='grant_status')
grant_status_enum.create(op.get_bind())

# Use raw SQL for table creation
conn.execute(sa.text("CREATE TABLE grant_enrollments (...) "))
```

## Migration Files Modified

- `src/db/migrations/versions/9d48d853728b_merge_migration_heads_20260205.py` (NEW)
- `src/db/migrations/versions/813f955b11af_fix_missing_user_roles.py`
- `src/db/migrations/versions/g2b3c4d5e6f7_add_stripe_payment_methods_to_enum.py`
- `src/db/migrations/versions/ee8ead726e9b_add_dues_tracking_models.py`
- `src/db/migrations/versions/j5e6f7g8h9i0_add_grant_enrollment_and_enhance_grant.py`

## Verification Results

```
✅ Single head confirmed: 9d48d853728b
✅ Current revision matches head
✅ Phase 7 models import successfully
✅ All migrations applied successfully
✅ 32 users with missing roles fixed during migration
```

## Prevention Measures

1. **Always run `alembic heads` before creating new migrations** — Detect multiple heads early
2. **Merge heads immediately when detected** — Don't let branches diverge further
3. **Add `alembic check` to CI/CD pipeline** — Automated drift detection
4. **Never commit model changes without corresponding migrations** — Keep models and DB in sync
5. **Review autogenerated migrations before applying** — Especially for enum and constraint changes
6. **Use explicit enum existence checks** — PostgreSQL doesn't support `IF NOT EXISTS` for enums
7. **Test migrations on clean database** — Catch missing columns and dependencies
8. **Document cross-branch dependencies** — Make enum/table dependencies explicit in migration comments

## Lessons Learned

1. **PostgreSQL enum limitations:**
   - No `CREATE TYPE IF NOT EXISTS` syntax
   - Must check existence with `SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enumname')`
   - `ADD VALUE IF NOT EXISTS` works for ALTER TYPE

2. **Cross-branch migrations:**
   - Enums created in one branch may not exist when other branch migrations run
   - Solution: Always check for existence before creating, gracefully handle missing dependencies

3. **Raw SQL INSERT in migrations:**
   - Python model defaults don't apply
   - Must explicitly include ALL NOT NULL columns
   - TimestampMixin columns (`created_at`, `updated_at`) must be set manually

4. **SQLAlchemy Enum() in migrations:**
   - `create_type=False` parameter doesn't always prevent creation in complex scenarios
   - Raw SQL CREATE TABLE can be more reliable for tables with existing enums

## Impact

- **Downtime:** None (development environment only)
- **Data Loss:** None
- **Users Affected:** 0 (not in production)
- **Recovery Time:** ~45 minutes (diagnosis + fixes + verification)

---

*Document created: 2026-02-05T02:36:00+00:00*
