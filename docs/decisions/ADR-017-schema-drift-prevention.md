# ADR-017: Schema Drift Prevention Strategy

**Status:** Accepted
**Date:** February 5, 2026
**Deciders:** Xerxes, Claude Code
**Context:** Post-ISSUE-001 migration drift resolution

---

## Context and Problem Statement

During test verification following the resolution of ISSUE-001 (parallel Stripe + Grant development causing migration drift), three critical schema drift issues were discovered that had been silently degrading the system:

1. **Bug #026:** Member model attribute `general_notes` didn't map to database column `notes`, causing all Member CRUD operations to fail
2. **Bug #027:** Audit log tests used incorrect column names (`user_id`/`created_at` instead of `changed_by`/`changed_at`)
3. **Bug #028:** Test fixtures used obsolete enum string values instead of current enum objects

These issues existed undetected because:
- Tests were failing but no CI/CD pipeline caught them
- Model-database mismatches only surface at runtime
- No automated validation of migration vs. model state

**Question:** How do we prevent schema drift between models, migrations, and the database?

---

## Decision Drivers

- **Developer Velocity:** Solo developer (5-10 hrs/week) can't manually verify every schema change
- **Bus Factor:** System must be maintainable if developer is unavailable
- **Parallel Development:** Multiple features developed in parallel (Stripe + Grants) increases drift risk
- **Migration Complexity:** 32 models, 50+ migrations, complex relationships
- **Test Coverage:** 590 tests, but many were silently failing

---

## Considered Options

### Option 1: Manual Review Checklist
- **Pros:** Simple, no tooling needed
- **Cons:** Error-prone, doesn't scale, relies on human memory
- **Decision:** Rejected - already failed in practice

### Option 2: Automated Schema Validation Tests
- **Pros:** Catches drift immediately, runs in CI/CD, low maintenance
- **Cons:** Requires test infrastructure setup
- **Decision:** **ACCEPTED** - Primary defense

### Option 3: Migration Linting Tools (e.g., alembic-autogenerate-checker)
- **Pros:** Pre-commit detection, prevents bad migrations from being created
- **Cons:** Tool ecosystem maturity, may have false positives
- **Decision:** **DEFERRED** - Evaluate in future

### Option 4: Stricter Code Review Process
- **Pros:** Human oversight catches logic errors tools miss
- **Cons:** Solo developer, no reviewer available
- **Decision:** Rejected for this project

---

## Decision Outcome

**Chosen Option:** Implement automated schema validation tests (Option 2)

### Implementation Strategy

#### Phase 1: Schema Consistency Tests (Immediate)

Create `src/tests/test_schema_validation.py` with:

```python
def test_model_columns_match_database():
    """Verify all model columns exist in database with correct types."""
    for table_name in Base.metadata.tables:
        model_columns = get_model_columns(table_name)
        db_columns = inspect_database_columns(table_name)
        assert model_columns == db_columns, f"Mismatch in {table_name}"

def test_enum_values_match_database():
    """Verify Python enum definitions match PostgreSQL enum types."""
    for enum_type in get_all_enum_types():
        python_values = get_python_enum_values(enum_type)
        db_values = get_database_enum_values(enum_type)
        assert python_values == db_values, f"Enum mismatch: {enum_type}"

def test_migrations_applied():
    """Verify no pending migrations (alembic head == database state)."""
    assert no_pending_migrations(), "Unapplied migrations detected"
```

#### Phase 2: Pre-commit Hooks (When Time Permits)

```bash
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: schema-validation
      name: Validate schema consistency
      entry: pytest src/tests/test_schema_validation.py -v
      language: system
      pass_filenames: false
```

#### Phase 3: CI/CD Integration (Future)

- Add schema validation to GitHub Actions / Railway deploy pipeline
- Block deployments if schema drift detected
- Generate schema diff reports on PR creation

---

## Consequences

### Positive

✅ **Early Detection:** Schema drift caught in development, not production
✅ **Confidence:** Tests verify model-database alignment after every migration
✅ **Documentation:** Tests serve as living documentation of schema expectations
✅ **Regression Prevention:** Once fixed, drift issues can't silently return
✅ **Low Maintenance:** Tests run automatically, no manual checking needed

### Negative

❌ **Initial Setup Time:** ~2-4 hours to write comprehensive validation tests
❌ **Test Runtime:** Adds ~5-10 seconds to test suite execution
❌ **False Positives:** May need tuning to handle intentional model-database mismatches

### Neutral

🔷 **Test Count:** Adds ~10-15 schema validation tests to suite
🔷 **Dependencies:** May need `alembic` testing utilities

---

## Lessons Learned from ISSUE-001

### What Went Wrong

1. **No CI/CD Pipeline:** Tests run manually, so failures go unnoticed
2. **Parallel Development:** Stripe (branch A) + Grants (branch B) both modified enums/migrations
3. **Manual Merges:** Merging branches created dual Alembic heads without detection
4. **Missing Column Name Mappings:** Model attributes assumed database column names matched

### What Went Right

1. **Comprehensive Tests:** Once run, tests caught all 3 drift issues immediately
2. **Transaction Rollback:** Test isolation prevented bad data from persisting
3. **Alembic Merge Migrations:** Tool exists to resolve dual heads
4. **Documentation:** Good model comments (e.g., "deprecated - use MemberNote") guided fixes

---

## Validation Checklist for Future Migrations

Before merging any branch with migrations:

- [ ] Run `alembic heads` - confirm single head
- [ ] Run `pytest src/tests/test_schema_validation.py` (once implemented)
- [ ] Run full test suite (`pytest -v`)
- [ ] Check for explicit column names in model definitions (e.g., `Column("db_name", ...)`)
- [ ] Verify enum imports use current values, not hardcoded strings
- [ ] Update test fixtures if model changes affect them

---

## Implementation Timeline

| Phase | Task | Priority | Status |
|-------|------|----------|--------|
| 1 | Fix existing schema drift (Bugs #026-028) | P0 | ✅ Complete (Feb 5, 2026) |
| 2 | Create `test_schema_validation.py` | P1 | ⏳ Pending Hub Review |
| 3 | Add to CI/CD (if implemented) | P2 | 📅 Future |
| 4 | Evaluate migration linting tools | P3 | 📅 Future |

---

## Related Documents

- **Diagnostic Report:** `docs/reports/session-logs/2026-02-05-test-verification-diagnostic-report.md`
- **Bug #026:** Member model column name mapping issue
- **Bug #027:** Audit log test column names
- **Bug #028:** Test fixture enum values
- **ISSUE-001:** Migration drift from parallel development

---

## References

- [Alembic Autogenerate Documentation](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [SQLAlchemy Column Naming](https://docs.sqlalchemy.org/en/20/core/metadata.html#column-table-metadata-api)
- [pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)

---

**Approved by:** Xerxes
**Review Date:** February 5, 2026
**Next Review:** After Phase 7 completion
