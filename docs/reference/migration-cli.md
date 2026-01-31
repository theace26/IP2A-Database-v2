# Migration CLI Reference

## Overview

The `ip2adb migrate` commands provide safe migration management with timestamped naming.

## Commands

### Create New Migration

```bash
ip2adb migrate new "description"
# Or directly:
python scripts/alembic_wrapper.py new "description"
```

Creates a timestamped migration file:
- Format: `YYYYMMDD_HHMMSS_description.py`
- Example: `20260129_143052_add_user_preferences.py`

Options:
- `--no-autogenerate`: Create empty migration (don't autogenerate from models)

### Validate Naming

```bash
ip2adb migrate validate
# Or directly:
python scripts/alembic_wrapper.py validate
```

Checks all migrations follow the timestamp naming convention. Legacy migrations are flagged but not treated as errors.

### List Migrations

```bash
ip2adb migrate list
# Or directly:
python scripts/alembic_wrapper.py list
```

Shows all migrations with formatted timestamps and identifies legacy migrations.

### Database Operations

```bash
# Upgrade to latest
ip2adb migrate upgrade head

# Upgrade by one
ip2adb migrate upgrade +1

# Downgrade by one (requires confirmation)
ip2adb migrate downgrade -1

# Downgrade to base (empty database)
ip2adb migrate downgrade base --yes

# Show current revision
ip2adb migrate current

# Show history
ip2adb migrate history -v
```

## Naming Convention

All new migrations MUST follow this pattern:

```
YYYYMMDD_HHMMSS_description.py
```

Where:
- `YYYYMMDD`: Date (e.g., 20260129)
- `HHMMSS`: Time (e.g., 143052)
- `description`: Snake_case description (max 50 chars)

### Examples

Good:
- `20260129_143052_add_user_preferences.py`
- `20260130_091234_create_audit_log_indexes.py`

Legacy (grandfathered):
- `0001_baseline.py` (no timestamp)
- `2b9a7b051766_add_user_model.py` (revision ID format)

## Pre-commit Hook

The migration naming convention is checked by pre-commit:

```bash
# Run manually
pre-commit run migration-naming --all-files

# Runs automatically on commit
git commit -m "..."
```

## Legacy Migrations

Existing migrations without timestamps are grandfathered but flagged as warnings.
New migrations MUST use timestamps via the wrapper script.

## Direct Alembic Usage

The wrapper is recommended, but direct alembic commands still work:

```bash
# Standard alembic upgrade
alembic upgrade head

# Standard alembic downgrade
alembic downgrade -1
```

Note: Direct `alembic revision` will not use timestamp naming.

## Dependency Analysis

### Show FK Graph

```bash
python scripts/migration_graph.py analyze
# Or via CLI:
ip2adb migrate graph
```

Analyzes foreign key relationships and shows:
- Dependencies between tables
- Migration order (create)
- Migration order (drop - reverse)

### Generate Mermaid Diagram

```bash
python scripts/migration_graph.py visualize
ip2adb migrate graph -v
ip2adb migrate graph -v -o docs/architecture/diagrams/migration-deps.mermaid
```

## Destructive Operation Detection

### Check All Migrations

```bash
python scripts/migration_validator.py check
# Or via CLI:
ip2adb migrate check-destructive
```

Scans for:
- DROP TABLE
- DROP COLUMN
- TRUNCATE
- DELETE without WHERE
- ALTER TABLE DROP

### Strict Mode

```bash
ip2adb migrate check-destructive --strict
```

Treats warnings as errors (useful for CI).

### Check Specific File

```bash
ip2adb migrate check-destructive -f 20260129_143052_add_users.py
```

## Pre-commit Hooks

Two hooks validate migrations:

1. **migration-naming** - Validates timestamp format
2. **migration-destructive** - Scans for dangerous operations

```bash
# Run manually
pre-commit run migration-naming --all-files
pre-commit run migration-destructive --all-files
```
