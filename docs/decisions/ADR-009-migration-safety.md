# ADR-009: Migration Safety Strategy

> **Document Created:** 2026-01-29
> **Last Updated:** February 3, 2026
> **Version:** 2.0
> **Status:** Implemented — Multi-layer migration safety active since adoption

## Status
Implemented

## Date
January 29, 2026

## Context
Database migrations are a critical risk area:
- Naming conflicts when multiple developers create migrations
- Destructive operations can cause irreversible data loss
- FK dependencies require specific ordering
- Production deployments need extra safeguards

We needed a comprehensive strategy to prevent migration-related incidents.

## Decision
We implemented a multi-layer migration safety strategy:

### 1. Timestamped Migration Names
All new migrations use the format: `YYYYMMDD_HHMMSS_description.py`

**Rationale:**
- Eliminates naming conflicts (timestamps are unique)
- Natural chronological sorting
- Easy to identify when migrations were created

**Implementation:**
- `python scripts/alembic_wrapper.py new "description"` generates timestamped names
- Pre-commit hook validates naming convention
- Legacy migrations are grandfathered but flagged

### 2. FK Dependency Analysis
The `migration_graph.py` script analyzes SQLAlchemy models to:
- Map foreign key relationships
- Generate topological sort for migration order
- Detect circular dependencies

**Usage:**
```bash
python scripts/migration_graph.py analyze    # Show analysis
python scripts/migration_graph.py visualize  # Output Mermaid diagram
python scripts/migration_graph.py order      # List table order
```

### 3. Destructive Operation Detection
The `migration_validator.py` script scans for:

| Operation | Severity | In Upgrade | In Downgrade |
|-----------|----------|------------|--------------|
| DROP TABLE | CRITICAL | Block | Warn |
| DROP COLUMN | ERROR | Block | Warn |
| TRUNCATE | CRITICAL | Block | Block |
| DELETE without WHERE | CRITICAL | Block | Block |
| DROP INDEX | WARNING | Warn | Allow |
| DROP CONSTRAINT | WARNING | Warn | Allow |

**Usage:**
```bash
python scripts/migration_validator.py check
python scripts/migration_validator.py check --strict
```

### 4. Pre-commit Enforcement
Two hooks run automatically:
1. `migration-naming` — Validates timestamp format
2. `migration-destructive` — Scans for dangerous operations

## Implementation Status

| Component | Status | Week | Notes |
|-----------|--------|------|-------|
| Timestamped migration naming | ✅ | 9 | `YYYYMMDD_HHMMSS_description.py` format |
| Alembic wrapper script | ✅ | 9 | `scripts/alembic_wrapper.py` |
| FK dependency analyzer | ✅ | 9 | `scripts/migration_graph.py` |
| Destructive operation scanner | ✅ | 9 | `scripts/migration_validator.py` |
| Pre-commit hooks | ✅ | 9 | naming + destructive checks |
| Mermaid migration diagram | ✅ | Batch 2 | `docs/architecture/diagrams/migrations.mmd` |
| Railway deploy migrations | ✅ | 16 | Auto-run on deploy |

### Current Scale
- **26 ORM models** with complex FK relationships
- Multiple migration files from Weeks 1–19
- Zero migration-related incidents since adoption

## Consequences

### Benefits
- Zero naming conflicts since adoption
- Early detection of destructive changes
- Clear migration ordering
- Consistent developer experience
- Audit trail through timestamps

### Tradeoffs
- Slightly longer migration filenames
- Additional CI/pre-commit time (~2s)
- Legacy migrations require manual review

### Alternatives Considered
1. **Sequential numbering** — Rejected due to conflict risk
2. **UUID-based names** — Rejected, not human-readable
3. **Branch-based prefixes** — Rejected, too complex

## Related ADRs
- ADR-001: Database Choice (PostgreSQL)
- ADR-003: Authentication (migrations for auth tables)
- ADR-012: Audit Logging (immutability trigger migration)

## References
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- `scripts/alembic_wrapper.py` — Timestamped migration generator
- `scripts/migration_graph.py` — FK dependency analysis
- `scripts/migration_validator.py` — Destructive operation detection
- `docs/architecture/diagrams/migrations.mmd` — Migration phase diagram (updated Batch 2)
- `docs/architecture/diagrams/models_fk.mmd` — Full ER diagram with 26 models (Batch 2)

---

## 🔄 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs, update as necessary.

---

Document Version: 2.0
Last Updated: February 3, 2026
Previous Version: 1.0 (2026-01-29 — original decision record)
