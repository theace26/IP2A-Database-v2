# Bug #030: Dues Test Unique Constraint Collisions

**Filed:** February 5, 2026 (Week 31)
**Fixed:** February 6, 2026 (Week 39 Bug Squash)
**Severity:** Medium — 9 test failures
**Status:** ✅ RESOLVED
**Category:** Test infrastructure / Fixture isolation

## Issue

Dues tests fail with UniqueViolation errors when run together, but pass when run individually.

## Error

```
sqlalchemy.exc.IntegrityError: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "uq_dues_period_year_month"
DETAIL:  Key (period_year, period_month)=(2093, 7) already exists.
```

Also affected `uq_dues_rate_class_effective` constraint.

## Root Cause

The test file uses `get_unique_date()` and `get_unique_year_month()` helper functions that generate "unique" values based on nanosecond timestamps and modulo math. However, when tests run in sequence, these values collide:

1. `get_unique_year_month()` only has 132 combinations (11 years × 12 months)
2. Global `_call_counter` wraps around when tests run in sequence
3. No cleanup between tests — data persisted in database
4. Second test with same (year, month) triggers UniqueViolation

The collision happens on:
- ✅ `dues_periods` table: (period_year, period_month) constraint — CONFIRMED
- ✅ `dues_rates` table: (classification, effective_date) constraint — CONFIRMED

## Solution (Implemented Week 39)

Added function-scoped autouse cleanup fixture that runs **BEFORE and AFTER** each test:

```python
@pytest.fixture(scope="function", autouse=True)
def cleanup_test_dues_data():
    """Clean up test dues data before and after each test."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from src.config.settings import settings

    def cleanup():
        engine = create_engine(str(settings.DATABASE_URL), echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        try:
            # Delete in reverse dependency order
            session.execute(text("DELETE FROM dues_payments WHERE period_id IN (SELECT id FROM dues_periods WHERE period_year >= 2090)"))
            session.execute(text("DELETE FROM dues_periods WHERE period_year >= 2090"))
            session.execute(text("DELETE FROM dues_rates WHERE effective_date >= '2200-01-01'"))
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    cleanup()  # Before test
    yield
    cleanup()  # After test
```

**Why this works:**
- Runs BEFORE test to clean leftover data from previous failed tests
- Runs AFTER test to clean up test's own data
- Uses direct SQL DELETE for efficiency
- Creates separate engine/session outside test transactions
- Targets test data ranges (years 2090+, dates 2200+)

## Files Modified

- ✅ `src/tests/test_dues.py` — Added `cleanup_test_dues_data()` fixture

## Impact

**Fixed 9 test failures:**
- test_create_dues_period ✅
- test_get_dues_period ✅
- test_close_dues_period ✅
- test_create_dues_payment ✅
- test_get_dues_payment ✅
- test_create_dues_rate ✅
- test_get_dues_rate ✅
- test_update_dues_rate ✅
- test_get_period_by_month ✅

All 21 dues tests now passing.

## Lessons Learned

1. **Cleanup pattern:** Always cleanup BEFORE and AFTER, not just after
2. **Separate session:** Cleanup must use separate DB connection, not test fixtures
3. **Dependency order:** DELETE child records before parent records
4. **Test isolation:** Don't rely on unique value generation alone — always cleanup

## References

- Commit: `f8a566d` (Week 39 bug squash)
- Session log: `docs/reports/session-logs/2026-02-06-week39-bug-squash.md`
- BUGS_LOG.md: Entry #030
- Similar fix: Bug #029 (Phase 7 model test cleanup)
