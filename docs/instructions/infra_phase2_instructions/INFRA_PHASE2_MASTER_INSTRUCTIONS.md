# Infrastructure Phase 2: Migration Safety

**Created:** January 29, 2026
**Estimated Time:** 4-6 hours (2-3 sessions)
**Prerequisites:** Infrastructure Phase 1 complete (src layout, CI, pre-commit)

---

## Overview

Infrastructure Phase 2 focuses on migration safety - preventing accidental data loss and ensuring database changes are tracked, validated, and reversible.

| Session | Focus | Time |
|---------|-------|------|
| A | Alembic Wrapper + Timestamped Migrations | 2-3 hrs |
| B | FK Dependency Graph + Destructive Detection | 2-3 hrs |

---

## Phase 2 Status (From ROADMAP.md)

| Task | Status |
|------|--------|
| Migration naming enforcement | ✅ Done |
| Legacy migration freeze | ✅ Done |
| Breaking change detection | ✅ Done |
| Alembic wrapper for timestamped generation | ⬜ **This Phase** |
| Migration dependency graph (FK-based) | ⬜ **This Phase** |
| Auto-detect destructive downgrades | ⬜ **This Phase** |

---

## Goals

### Must Have (MVP)
- [ ] CLI wrapper for `alembic revision` with auto-timestamp
- [ ] Migration dependency graph based on FK relationships
- [ ] Destructive downgrade detection (DROP TABLE, DROP COLUMN)
- [ ] Pre-commit hook for migration validation
- [ ] Updated ADR for migration safety strategy

### Nice to Have
- [ ] Visual dependency graph output (Mermaid)
- [ ] Migration impact estimation
- [ ] Automated migration tests

---

## Architecture Overview

### New Files

```
scripts/
├── alembic_wrapper.py           # CLI wrapper with timestamps
├── migration_graph.py           # FK dependency analysis
└── migration_validator.py       # Destructive operation detection

src/
└── cli/
    └── migrations.py            # Click CLI commands

docs/
└── decisions/
    └── ADR-010-migration-safety.md

.pre-commit-config.yaml          # Updated with migration hooks
```

### CLI Commands

```bash
# Generate timestamped migration
ip2adb migrate new "add_user_preferences"
# Creates: migrations/versions/20260129_143052_add_user_preferences.py

# Validate migrations
ip2adb migrate validate

# Show dependency graph
ip2adb migrate graph

# Check for destructive operations
ip2adb migrate check-destructive
```

---

## Key Concepts

### Timestamped Migration Names

**Current (problematic):**
```
migrations/versions/
├── 001_initial.py
├── 002_add_users.py
├── 003_add_members.py     # Conflict risk if two devs create "003"
```

**Target (safe):**
```
migrations/versions/
├── 20260127_100000_initial.py
├── 20260127_143052_add_users.py
├── 20260128_091234_add_members.py  # No conflicts
```

### FK Dependency Graph

Models with foreign keys must be migrated in order:
```
Organization (no FK)
    ↓
Member (FK: organization_id)
    ↓
MemberEmployment (FK: member_id, organization_id)
    ↓
DuesPayment (FK: member_id)
```

The dependency graph ensures:
1. Tables are created in correct order
2. Tables are dropped in reverse order
3. No orphaned foreign keys

### Destructive Operation Detection

Flag migrations that contain:
- `DROP TABLE`
- `DROP COLUMN`
- `ALTER TABLE ... DROP`
- `DELETE FROM` without WHERE
- `TRUNCATE`

These require explicit confirmation or are blocked entirely.

---

## Session Breakdown

### Session A: Alembic Wrapper (Document 1)
- Create timestamped migration generator
- Create CLI commands
- Add pre-commit hook
- Test migration naming
- Update documentation

### Session B: Dependency Graph + Validation (Document 2)
- Analyze FK relationships
- Build dependency graph
- Detect destructive operations
- Create validation pre-commit hook
- Create ADR-010

---

## Documentation Requirements

### MUST Update
1. **CHANGELOG.md** - Add infrastructure improvements
2. **ROADMAP.md** - Check off completed Phase 2 tasks
3. **docs/reference/** - Add migration CLI reference

### MUST Create
1. **ADR-010** - Migration Safety Strategy
2. **Session log** - `docs/reports/session-logs/2026-01-XX-infra-phase2.md`

### SHOULD Update
1. **CLAUDE.md** - Add infrastructure phase context
2. **docs/README.md** - Update infrastructure status

---

## Success Criteria

Infrastructure Phase 2 is complete when:
- [ ] `ip2adb migrate new "name"` generates timestamped migration
- [ ] Dependency graph correctly orders tables
- [ ] Destructive operations are detected and flagged
- [ ] Pre-commit hooks validate migrations
- [ ] ADR-010 documents the strategy
- [ ] All documentation updated
- [ ] Session log created

---

*Proceed to Document 1 (Session A) to begin Alembic Wrapper implementation.*
