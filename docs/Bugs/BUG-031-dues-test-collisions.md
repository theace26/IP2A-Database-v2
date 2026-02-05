# Bug #031: Dues Test Unique Constraint Collisions

**Filed:** February 5, 2026
**Sprint:** Week 31
**Severity:** Low — test-only issue, does not affect production
**Status:** Open — Investigation needed
**Category:** Test infrastructure

## Issue

Dues tests fail with UniqueViolation errors when run together, but pass when run individually.

## Error

```
sqlalchemy.exc.IntegrityError: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "uq_dues_rate_class_effective"
DETAIL:  Key (classification, effective_date)=(JOURNEYMAN, 2843-02-02) already exists.
```

## Root Cause

The test file uses `get_unique_date()` and `get_unique_year_month()` helper functions that generate "unique" values based on nanosecond timestamps. However, when tests run in parallel or when the test suite runs multiple times, these values collide.

The collision happens on:
- `dues_rates` table: (classification, effective_date) constraint
- Possibly also on `dues_periods` table: (period_year, period_month) constraint

## Attempted Fix

Tried adding a cleanup fixture with `scope="module"` to delete test data before tests run. This caused tests to hang, likely due to transaction/connection management conflicts with the test fixtures.

## Proposed Solution

1. **Option A:** Modify `get_unique_date()` to use UUIDs in the date string or increase the year range to avoid collisions entirely
2. **Option B:** Create a session-scoped cleanup fixture that runs outside test transactions
3. **Option C:** Use database rollback/transaction isolation per test to prevent cross-test pollution

## Files Involved

- `src/tests/test_dues.py` — Test file with helper functions
- `src/tests/conftest.py` — Test fixture definitions

## Impact

- Tests fail when run together: `pytest src/tests/test_dues.py`
- Tests pass when run individually: `pytest src/tests/test_dues.py::test_create_dues_rate`
- Does not affect production code or user-facing functionality

## Next Steps

1. Investigate why cleanup fixture causes hanging
2. Review test transaction management in conftest.py
3. Consider rewriting helper functions to guarantee uniqueness
