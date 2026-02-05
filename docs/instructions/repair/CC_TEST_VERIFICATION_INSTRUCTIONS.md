# Claude Code Instructions: Test Verification & Diagnosis

**Created:** February 5, 2026  
**Source:** Hub Handoff — ISSUE-001 Migration Drift Resolution Follow-up  
**Priority:** High — blocking v0.9.6-alpha stability confirmation  
**Task Type:** Diagnostic + Fix  
**Estimated Time:** 30-45 minutes  
**Branch:** `develop`

---

## Context

A critical migration drift issue (ISSUE-001) was just resolved in the Hub. The database had multiple Alembic heads from parallel feature development (Stripe integration + Grant enrollment). The following fixes were applied:

- Created merge migration (`9d48d853728b`)
- Fixed missing `assigned_at` and `updated_at` columns in `user_roles` INSERT
- Fixed enum existence checks (PostgreSQL doesn't support `CREATE TYPE IF NOT EXISTS`)
- Fixed grant enrollment migration with explicit enum DROP/CREATE

**Current state:** Migrations now apply cleanly. Single Alembic head confirmed.

**Problem:** Out of 593 expected tests, only 568 passed. **25 failures need diagnosis and resolution.**

---

## Pre-Flight Checks

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop

# Verify single migration head
alembic heads
# Expected: Single head (9d48d853728b or later)

# Verify database is clean
alembic current
```

If multiple heads are shown, STOP and report to user — the migration merge was incomplete.

---

## Phase 1: Run Full Test Suite with Failure Capture

```bash
# Run full suite, capture output with verbose failure details
pytest --tb=short -v 2>&1 | tee /tmp/test_output_$(date +%Y%m%d_%H%M%S).txt

# Quick summary
echo "=== Test Summary ==="
tail -20 /tmp/test_output_*.txt | head -25
```

**Record these numbers:**
- Total tests collected: ____
- Passed: ____
- Failed: ____
- Errors: ____
- Skipped: ____

---

## Phase 2: Extract Failure List

```bash
# Extract just the failed test names
pytest --tb=no -v 2>&1 | grep -E "^(FAILED|ERROR)" | tee /tmp/failed_tests.txt

# Count failures
wc -l /tmp/failed_tests.txt
```

---

## Phase 3: Categorize Failures

For each failure, determine the root cause category:

| Category | Symptoms | Likely Fix |
|----------|----------|------------|
| **Migration-related** | Missing columns, enum mismatches, `IntegrityError`, `ProgrammingError` | Update test fixtures to match new schema |
| **Fixture issues** | Tests expecting old data, `KeyError`, missing required fields | Update `conftest.py` or test-specific fixtures |
| **Service layer** | `AssertionError` on business logic, wrong return values | Review service code changes, update test expectations |
| **Import/dependency** | `ImportError`, `ModuleNotFoundError`, circular imports | Fix import paths |
| **Relationship bugs** | `InvalidRequestError`, "Could not determine join condition" | Fix SQLAlchemy relationship definitions |

### Known Likely Failures (from Hub analysis)

Based on the migration fixes applied, watch for these patterns:

1. **`user_roles` tests** — May need `assigned_at` field in test fixtures
2. **Dues payment tests** — Enum value expectations may have changed
3. **Grant enrollment tests** — New table structure, new enums (`GrantStatus`, `GrantEnrollmentStatus`, `GrantOutcome`)
4. **Dispatch relationship tests** — Known bug: `Dispatch.bid` relationship missing `foreign_keys` parameter
5. **Any test using `TimestampMixin`** — Ensure `created_at`/`updated_at` are properly set

---

## Phase 4: Diagnose Each Failure

For each failed test, run it individually with full traceback:

```bash
# Example: Run single failed test with full traceback
pytest src/tests/test_SPECIFIC_FILE.py::test_specific_function -v --tb=long
```

Document each failure using this format:

```markdown
### Failure #N: test_name

**File:** `src/tests/test_xxx.py`
**Error Type:** [AssertionError | IntegrityError | KeyError | etc.]
**Category:** [Migration | Fixture | Service | Import | Relationship]

**Traceback Summary:**
[Key lines from traceback]

**Root Cause:**
[1-2 sentence explanation]

**Fix:**
[Specific fix to apply, or "NEEDS HUB DECISION" if architectural]
```

---

## Phase 5: Apply Fixes

### Rules for Applying Fixes

✅ **Fix directly:**
- Missing fixture fields (add `assigned_at`, `created_at`, etc.)
- Test assertions that need updated expected values
- Import path corrections
- Relationship `foreign_keys` parameter additions

⛔ **DO NOT fix — flag for Hub:**
- Model schema changes (adding/removing columns)
- Migration file modifications
- Changes to enum definitions in `src/db/enums/`
- Architectural changes to service layer
- Deleting or significantly rewriting tests

### Common Fixes Reference

**Fix A: Missing `assigned_at` in user_roles fixture**
```python
# In conftest.py or test file
user_role = UserRole(
    user_id=user.id,
    role_id=role.id,
    assigned_at=datetime.utcnow(),  # ADD THIS
    assigned_by=admin_user.id        # ADD THIS if required
)
```

**Fix B: Dispatch.bid relationship**
```python
# In src/models/dispatch.py
bid = relationship("JobBid", foreign_keys=[bid_id], back_populates="dispatch")
```

**Fix C: Missing timestamp fields in test objects**
```python
# When creating test objects that use TimestampMixin
obj = SomeModel(
    # ... other fields ...
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)
```

**Fix D: Enum value mismatches**
```python
# Check actual enum values in src/db/enums/
# Update test to use correct enum value
from src.db.enums import CorrectEnum
assert obj.status == CorrectEnum.CORRECT_VALUE  # Not old value
```

---

## Phase 6: Verify All Tests Pass

```bash
# Run full suite again
pytest -v

# Expected output: "593 passed" (or close to it)
```

If failures remain:
1. Re-diagnose remaining failures
2. Apply additional fixes
3. Repeat until clean or blockers identified

---

## Phase 7: Document Results

Create a diagnostic report file:

```bash
cat > /tmp/test_diagnosis_report.md << 'EOF'
# Test Verification Report

**Date:** [DATE]
**Branch:** develop
**Initial State:** 568/593 passed (25 failures)
**Final State:** [X]/593 passed

## Summary

- **Total failures diagnosed:** [N]
- **Fixed directly:** [N]
- **Flagged for Hub review:** [N]

## Fixes Applied

### Fix 1: [Description]
**File:** `path/to/file.py`
**Change:** [What was changed]

### Fix 2: [Description]
...

## Issues Requiring Hub Decision

### Issue 1: [Description]
**Reason:** [Why this can't be fixed in Spoke]
**Recommendation:** [Suggested approach]

## Files Modified

- `path/to/file1.py` — [What changed]
- `path/to/file2.py` — [What changed]
- ...

EOF
```

---

## Output Checklist

Before ending session, confirm:

- [ ] All 593 tests pass (or remaining failures documented with Hub escalation)
- [ ] Diagnostic report created
- [ ] List of all modified files provided
- [ ] Any Hub decisions needed are clearly flagged
- [ ] No model schemas were changed
- [ ] No migration files were modified

---

## Files Likely to Need Modification

Based on the migration fixes, expect to touch:

| File | Likely Change |
|------|---------------|
| `src/tests/conftest.py` | Add `assigned_at` to UserRole fixtures |
| `src/tests/test_users.py` | Update user_roles test assertions |
| `src/tests/test_grants.py` | Update for new grant enrollment schema |
| `src/tests/test_dues.py` | Verify enum values match current definitions |
| `src/tests/test_dispatch_frontend.py` | Fix blocked by Dispatch.bid relationship |
| `src/models/dispatch.py` | Add `foreign_keys=[bid_id]` to relationship |

---

## Emergency Stop Conditions

**STOP and report to user if:**

1. Migration head is not singular (merge incomplete)
2. Database connection fails
3. More than 50 tests failing (indicates bigger problem)
4. Tests require model schema changes to pass
5. Circular import errors that can't be resolved with path fixes

---

## Session End Checklist

1. Run `pytest -v` one final time
2. Capture final test count
3. List ALL files modified as `/dir/file` paths
4. Generate diagnostic report
5. Identify any documentation updates needed

---

*Claude Code Test Verification Instructions — February 5, 2026*
*Source: Hub Handoff for ISSUE-001 Follow-up*
