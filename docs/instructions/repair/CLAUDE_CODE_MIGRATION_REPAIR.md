# Claude Code Instructions: Database Migration Diagnosis & Repair

**Document Type:** Automated Diagnostic & Repair Workflow
**Project:** UnionCore (IP2A-Database-v2)
**Target:** Alembic migration drift, schema sync, enum conflicts
**Estimated Time:** 30-60 minutes
**Branch:** `develop`

---

## TL;DR

Run the diagnostic script first. It tells you exactly what's broken. Then follow the decision tree to fix it. Document everything.

---

## Pre-Flight (REQUIRED)

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
```

**Verify Docker is running:**
```bash
docker-compose ps | grep -E "postgres|db"
# Must show "Up" status
```

**If Docker not running:**
```bash
docker-compose up -d db
sleep 5  # Wait for PostgreSQL to initialize
```

---

## Phase 1: Automated Diagnostic

Run this diagnostic block and **capture ALL output**:

```bash
echo "=== MIGRATION DIAGNOSTIC REPORT ==="
echo "Timestamp: $(date -Iseconds)"
echo "Branch: $(git branch --show-current)"
echo "Last commit: $(git log -1 --oneline)"
echo ""

echo "=== 1. DATABASE CONNECTION ==="
if docker-compose exec -T db psql -U postgres -d unioncore -c "SELECT 1" > /dev/null 2>&1; then
    echo "✅ Database connection OK"
else
    echo "❌ DATABASE CONNECTION FAILED"
    echo "   Run: docker-compose up -d db"
    exit 1
fi

echo ""
echo "=== 2. ALEMBIC CURRENT STATE ==="
alembic current 2>&1 || echo "❌ alembic current failed"

echo ""
echo "=== 3. ALEMBIC HEADS (Multiple = Problem) ==="
HEAD_COUNT=$(alembic heads 2>&1 | grep -c "Rev:")
echo "Head count: $HEAD_COUNT"
alembic heads 2>&1

echo ""
echo "=== 4. MIGRATION FILES (Phase 7 related) ==="
ls -la alembic/versions/*phase7* 2>/dev/null || echo "No phase7-named migrations found"
ls -la alembic/versions/*referral* 2>/dev/null || echo "No referral-named migrations found"
ls -la alembic/versions/*dispatch* 2>/dev/null || echo "No dispatch-named migrations found"
echo ""
echo "Total migration files: $(ls alembic/versions/*.py 2>/dev/null | wc -l)"

echo ""
echo "=== 5. POSTGRESQL ENUM TYPES ==="
docker-compose exec -T db psql -U postgres -d unioncore -c \
    "SELECT typname FROM pg_type WHERE typtype = 'e' ORDER BY typname;" 2>&1

echo ""
echo "=== 6. PHASE 7 TABLES (Expected: 6) ==="
docker-compose exec -T db psql -U postgres -d unioncore -c \
    "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN 
    ('referral_books', 'book_registrations', 'registration_activities', 
     'labor_requests', 'job_bids', 'dispatches');" 2>&1

echo ""
echo "=== 7. AUTOGENERATE DRIFT CHECK ==="
alembic check 2>&1 || echo "Note: 'alembic check' may not be available in older versions"

echo ""
echo "=== DIAGNOSTIC COMPLETE ==="
```

---

## Phase 2: Decision Tree

Based on diagnostic output, follow the appropriate path:

### Decision Point A: How many heads?

**If HEAD_COUNT > 1** → Go to [Fix A: Merge Multiple Heads](#fix-a-merge-multiple-heads)

**If HEAD_COUNT = 1** → Continue to Decision Point B

**If HEAD_COUNT = 0** → Go to [Fix B: Initialize Migrations](#fix-b-initialize-migrations)

---

### Decision Point B: Do Phase 7 tables exist?

From diagnostic output section 6, count tables found.

**If tables found = 6** → Go to [Fix E: Column-Level Drift](#fix-e-column-level-drift)

**If tables found = 0** → Go to [Fix C: Generate Phase 7 Migrations](#fix-c-generate-phase-7-migrations)

**If tables found = 1-5** → Go to [Fix D: Partial Migration](#fix-d-partial-migration)

---

### Decision Point C: Do Phase 7 enums exist?

From diagnostic output section 5, check for these enums:
- `bookclassification`
- `bookregion`
- `booktier`
- `registrationstatus`
- `laborrequesttype`
- `laborrequeststatus`
- `dispatchstatus`
- `dispatchoutcome`

**If enums missing** → Go to [Fix F: Enum Creation](#fix-f-enum-creation)

**If enums present but tables missing** → Go to [Fix C: Generate Phase 7 Migrations](#fix-c-generate-phase-7-migrations)

---

## Fix A: Merge Multiple Heads

**Problem:** Multiple migration branches exist (common when features developed in parallel).

```bash
# Show the divergence
alembic history --verbose | head -50

# Create merge migration
alembic merge heads -m "merge_migration_heads_$(date +%Y%m%d)"

# Review the generated file (IMPORTANT)
MERGE_FILE=$(ls -t alembic/versions/*merge_migration_heads*.py | head -1)
echo "Review this file: $MERGE_FILE"
cat "$MERGE_FILE"

# If file looks correct (should just be a merge point with no operations):
alembic upgrade head

# Verify single head
alembic heads | grep -c "Rev:"
# Must output: 1
```

**After merge, return to [Decision Point B](#decision-point-b-do-phase-7-tables-exist)**.

---

## Fix B: Initialize Migrations

**Problem:** No migrations exist at all (fresh install or corrupted state).

```bash
# Check if alembic_version table exists
docker-compose exec -T db psql -U postgres -d unioncore -c \
    "SELECT * FROM alembic_version;"

# If table doesn't exist or is empty, stamp current schema:
# WARNING: Only do this if the database has ALL expected tables
alembic stamp head

# If database is empty, just run upgrade:
alembic upgrade head
```

---

## Fix C: Generate Phase 7 Migrations

**Problem:** Phase 7 models exist in code but no migrations generated.

```bash
# Step 1: Verify models are importable
python -c "from src.models.referral_book import ReferralBook; print('✅ Models import OK')"

# Step 2: Generate migration
alembic revision --autogenerate -m "phase7_add_referral_dispatch_models"

# Step 3: REVIEW GENERATED FILE (CRITICAL)
NEW_MIGRATION=$(ls -t alembic/versions/*.py | head -1)
echo "=== REVIEW THIS FILE ===" 
cat "$NEW_MIGRATION"
echo "========================="

# Step 4: Check for issues before applying:
# - Enums must be created BEFORE tables that use them
# - Tables must be created BEFORE foreign keys reference them
# - Order matters!

# Step 5: If file looks correct:
alembic upgrade head

# Step 6: Verify
docker-compose exec -T db psql -U postgres -d unioncore -c \
    "SELECT tablename FROM pg_tables WHERE schemaname = 'public' 
     ORDER BY tablename;" | grep -E "referral|dispatch|registration|labor|job_bid"
```

**If autogenerate creates enum errors, go to [Fix F: Enum Creation](#fix-f-enum-creation) first.**

---

## Fix D: Partial Migration

**Problem:** Some Phase 7 tables exist but not all. Migration was interrupted or incomplete.

```bash
# Step 1: Determine what's missing
echo "=== Expected Tables ==="
echo "referral_books, book_registrations, registration_activities"
echo "labor_requests, job_bids, dispatches"

echo ""
echo "=== Existing Tables ==="
docker-compose exec -T db psql -U postgres -d unioncore -c \
    "SELECT tablename FROM pg_tables WHERE schemaname = 'public' 
     AND tablename IN ('referral_books', 'book_registrations', 
     'registration_activities', 'labor_requests', 'job_bids', 'dispatches');"

# Step 2: Generate fix-up migration for missing tables only
alembic revision --autogenerate -m "phase7_add_missing_tables"

# Step 3: Review and apply (same as Fix C steps 3-6)
```

---

## Fix E: Column-Level Drift

**Problem:** Tables exist but columns are missing or wrong type.

```bash
# Step 1: Check specific columns
docker-compose exec -T db psql -U postgres -d unioncore -c \
    "SELECT column_name, data_type, is_nullable 
     FROM information_schema.columns 
     WHERE table_name = 'referral_books' ORDER BY ordinal_position;"

docker-compose exec -T db psql -U postgres -d unioncore -c \
    "SELECT column_name, data_type, is_nullable 
     FROM information_schema.columns 
     WHERE table_name = 'book_registrations' ORDER BY ordinal_position;"

docker-compose exec -T db psql -U postgres -d unioncore -c \
    "SELECT column_name, data_type, is_nullable 
     FROM information_schema.columns 
     WHERE table_name = 'dispatches' ORDER BY ordinal_position;"

# Step 2: Compare against models
# Key fields to verify:
# - book_registrations.applicant_priority_number should be NUMERIC(10,2)
# - dispatches.bid_id should exist (foreign key)

# Step 3: Generate fix-up migration
alembic revision --autogenerate -m "phase7_sync_column_drift"

# Step 4: Review and apply
```

---

## Fix F: Enum Creation

**Problem:** Enum types missing from PostgreSQL.

Alembic autogenerate sometimes fails to create enums in the right order. Manual migration may be needed.

```bash
# Step 1: Check which enums exist
docker-compose exec -T db psql -U postgres -d unioncore -c \
    "SELECT typname FROM pg_type WHERE typtype = 'e' ORDER BY typname;"

# Step 2: Create manual enum migration if needed
cat > alembic/versions/$(date +%Y%m%d%H%M%S)_phase7_create_enums.py << 'EOF'
"""phase7 create enums

Revision ID: phase7_enums_001
Revises: [FILL IN PREVIOUS HEAD]
Create Date: [AUTO]
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'phase7_enums_001'
down_revision = None  # FILL THIS IN
branch_labels = None
depends_on = None

def upgrade():
    # Create enums BEFORE tables that use them
    op.execute("CREATE TYPE bookclassification AS ENUM ('WIRE', 'TECHNICIAN', 'SOUND_COMM', 'STOCKMAN', 'LT_FXT_MAINT', 'MARINE', 'RESIDENTIAL', 'TRADESHOW', 'UTILITY_WORKER', 'TERO_APPR_WIRE')")
    op.execute("CREATE TYPE bookregion AS ENUM ('SEATTLE', 'BREMERTON', 'PT_ANGELES', 'JURISDICTION_WIDE')")
    op.execute("CREATE TYPE booktier AS ENUM ('BOOK_1', 'BOOK_2', 'BOOK_3', 'BOOK_4')")
    op.execute("CREATE TYPE registrationstatus AS ENUM ('ACTIVE', 'DISPATCHED', 'RESIGNED', 'DROPPED', 'EXPIRED')")
    op.execute("CREATE TYPE laborrequesttype AS ENUM ('STANDARD', 'SHORT_CALL', 'EMERGENCY', 'BY_NAME')")
    op.execute("CREATE TYPE laborrequeststatus AS ENUM ('OPEN', 'FILLED', 'CANCELLED', 'EXPIRED')")
    op.execute("CREATE TYPE dispatchstatus AS ENUM ('PENDING', 'ACCEPTED', 'REJECTED', 'COMPLETED', 'TERMINATED')")
    op.execute("CREATE TYPE dispatchoutcome AS ENUM ('COMPLETED', 'QUIT', 'LAID_OFF', 'TERMINATED', 'INJURY')")

def downgrade():
    op.execute("DROP TYPE IF EXISTS dispatchoutcome")
    op.execute("DROP TYPE IF EXISTS dispatchstatus")
    op.execute("DROP TYPE IF EXISTS laborrequeststatus")
    op.execute("DROP TYPE IF EXISTS laborrequesttype")
    op.execute("DROP TYPE IF EXISTS registrationstatus")
    op.execute("DROP TYPE IF EXISTS booktier")
    op.execute("DROP TYPE IF EXISTS bookregion")
    op.execute("DROP TYPE IF EXISTS bookclassification")
EOF

echo "⚠️  MANUAL EDIT REQUIRED:"
echo "1. Update 'down_revision' in the file above"
echo "2. Verify enum values match src/db/enums/phase7_enums.py"
echo "3. Then run: alembic upgrade head"
```

---

## Phase 3: Verification Suite

After applying fixes, run the full verification:

```bash
echo "=== POST-FIX VERIFICATION ==="

echo ""
echo "1. Single head check:"
HEAD_COUNT=$(alembic heads 2>&1 | grep -c "Rev:")
if [ "$HEAD_COUNT" -eq 1 ]; then
    echo "✅ Single head confirmed"
else
    echo "❌ Multiple heads still exist: $HEAD_COUNT"
fi

echo ""
echo "2. Current matches head:"
CURRENT=$(alembic current 2>&1 | grep -oP 'Rev: \K\w+' | head -1)
HEAD=$(alembic heads 2>&1 | grep -oP 'Rev: \K\w+' | head -1)
if [ "$CURRENT" = "$HEAD" ]; then
    echo "✅ Current ($CURRENT) matches head"
else
    echo "❌ Current ($CURRENT) != Head ($HEAD)"
fi

echo ""
echo "3. Drift check:"
alembic check 2>&1 && echo "✅ No drift detected" || echo "⚠️  Drift detected or check unavailable"

echo ""
echo "4. Phase 7 tables:"
TABLE_COUNT=$(docker-compose exec -T db psql -U postgres -d unioncore -t -c \
    "SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public' AND tablename IN 
    ('referral_books', 'book_registrations', 'registration_activities', 
     'labor_requests', 'job_bids', 'dispatches');" | tr -d ' ')
if [ "$TABLE_COUNT" -eq 6 ]; then
    echo "✅ All 6 Phase 7 tables exist"
else
    echo "❌ Only $TABLE_COUNT/6 Phase 7 tables found"
fi

echo ""
echo "5. Test suite:"
pytest --tb=short 2>&1 | tail -20
TEST_RESULT=$(pytest --tb=line 2>&1 | tail -1)
echo "Result: $TEST_RESULT"

echo ""
echo "=== VERIFICATION COMPLETE ==="
```

---

## Phase 4: Documentation Updates (MANDATORY)

**Create issue record:**

```bash
mkdir -p docs/issues

cat > docs/issues/ISSUE-001-migration-drift-resolution.md << 'EOF'
# ISSUE-001: Database Migration Drift Resolution

**Date Discovered:** February 5, 2026
**Date Resolved:** $(date +%Y-%m-%d)
**Severity:** Critical (blocked Phase 7 testing)
**Affected Components:** Alembic migrations, Phase 7 models

## Problem Description

Database schema out of sync with SQLAlchemy models.

## Diagnostic Output

```
[PASTE DIAGNOSTIC OUTPUT FROM PHASE 1 HERE]
```

## Root Cause

[FILL IN: What caused the drift?]
- [ ] Migrations created in parallel branches without merging
- [ ] Phase 7 models added without generating migrations
- [ ] Migration applied out of order
- [ ] Manual database changes outside Alembic
- [ ] Other: _______________

## Resolution Steps

[FILL IN: Which Fix path was followed?]

1. 
2. 
3. 

## Migration Files Created/Modified

[LIST FILES]

## Verification Results

```
[PASTE VERIFICATION OUTPUT FROM PHASE 3 HERE]
```

## Prevention Measures

1. Always run `alembic heads` before creating new migrations
2. Merge heads immediately when detected
3. Add `alembic check` to CI/CD pipeline
4. Never commit model changes without corresponding migrations
5. Review autogenerated migrations before applying

---

*Document created: $(date -Iseconds)*
EOF

echo "Created: docs/issues/ISSUE-001-migration-drift-resolution.md"
echo "⚠️  FILL IN the bracketed sections with actual diagnostic data"
```

**Update CHANGELOG.md:**

```bash
# Add entry at top of [Unreleased] section
cat >> /tmp/changelog_entry.md << 'EOF'

### Fixed
- **Database Migration Sync** (February 2026)
  - Diagnosed and resolved Alembic schema drift issue
  - [DESCRIBE WHAT WAS FIXED]
  - All Phase 7 tables and enums now in sync
  - Full test suite passing
EOF

echo "Add this to CHANGELOG.md under [Unreleased] → Fixed:"
cat /tmp/changelog_entry.md
```

---

## Phase 5: Commit Strategy

```bash
# Stage migration files
git add alembic/versions/*.py

# Stage documentation
git add docs/issues/ISSUE-001-migration-drift-resolution.md

# Commit with descriptive message
git commit -m "fix(migrations): resolve Phase 7 schema drift

- Diagnosed: [single/multiple] head(s), [missing tables/enums/columns]
- Resolution: [merged heads/generated migrations/manual fixes]
- Verified: 6 Phase 7 tables, all enums, full test suite passing
- Created: docs/issues/ISSUE-001-migration-drift-resolution.md

Closes migration blocker for Phase 7 testing"

git push origin develop
```

---

## Troubleshooting: Common Errors

### Error: "Target database is not up to date"

```bash
# This means migrations exist but aren't applied
alembic upgrade head
```

### Error: "Can't locate revision identified by 'xxx'"

```bash
# Corrupted alembic_version table
docker-compose exec -T db psql -U postgres -d unioncore -c \
    "SELECT * FROM alembic_version;"

# If points to non-existent revision, reset:
docker-compose exec -T db psql -U postgres -d unioncore -c \
    "DELETE FROM alembic_version;"
alembic stamp head
```

### Error: "type 'xxx' already exists"

```bash
# Enum already in database but migration trying to create again
# Check the migration file and wrap in IF NOT EXISTS or remove

# To check what exists:
docker-compose exec -T db psql -U postgres -d unioncore -c \
    "SELECT typname FROM pg_type WHERE typname = 'xxx';"
```

### Error: "relation 'xxx' does not exist"

```bash
# Table doesn't exist but migration references it
# Need to run table creation migration first
alembic history --verbose  # Find the right order
alembic upgrade <revision_before_problem>
alembic upgrade head
```

### Error: "Could not determine join condition"

```bash
# This is a MODEL error, not migration error
# Check the Dispatch model relationships
# Ensure foreign_keys parameter is set on ambiguous relationships

# Example fix in src/models/dispatch.py:
# bid = relationship("JobBid", foreign_keys=[bid_id], back_populates="dispatch")
```

---

## Success Criteria Checklist

Before closing this task, ALL must be true:

- [ ] `alembic heads` → exactly 1 head
- [ ] `alembic current` → matches head
- [ ] PostgreSQL has 6 Phase 7 tables
- [ ] PostgreSQL has all Phase 7 enums
- [ ] `pytest` → All tests passing (capture count)
- [ ] `docs/issues/ISSUE-001-*.md` → Created and filled in
- [ ] CHANGELOG.md → Entry added
- [ ] Git commit → Pushed to develop

---

## Escalation Triggers

**STOP and create Hub handoff if:**

- Data loss risk detected (tables with data would be dropped)
- Circular dependency in migrations
- More than 5 migration heads
- Tests fail after migration with non-obvious errors
- Production database affected (this should only run on dev)

---

## Quick Reference: File Locations

| Item | Location |
|------|----------|
| Migration files | `alembic/versions/` |
| Alembic config | `alembic.ini` |
| Alembic env | `alembic/env.py` |
| Phase 7 models | `src/models/referral_book.py`, `src/models/dispatch.py`, etc. |
| Phase 7 enums | `src/db/enums/phase7_enums.py` |
| Issue docs | `docs/issues/` |

---

**Document Version:** 1.0
**Created:** February 5, 2026
**Purpose:** Efficient diagnosis and repair of Alembic migration issues
**For:** Claude Code execution in UnionCore project
