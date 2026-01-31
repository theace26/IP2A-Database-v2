# Infrastructure Phase 2 - Session A: Alembic Wrapper

**Document:** 1 of 2
**Estimated Time:** 2-3 hours
**Focus:** Timestamped migration generator and CLI commands

---

## Objective

Create a CLI wrapper for Alembic that:
- Generates timestamped migration filenames
- Prevents naming conflicts
- Integrates with existing `ip2adb` CLI
- Adds pre-commit validation

---

## Pre-flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Verify tests pass
```

---

## Step 1: Create Alembic Wrapper Script (30 min)

Create `scripts/alembic_wrapper.py`:

```python
#!/usr/bin/env python3
"""
Alembic Wrapper - Timestamped migration generation.

This wrapper ensures all migrations have consistent, conflict-free naming:
- Format: YYYYMMDD_HHMMSS_description.py
- Example: 20260129_143052_add_user_preferences.py

Usage:
    python scripts/alembic_wrapper.py new "add user preferences"
    python scripts/alembic_wrapper.py validate
"""

import os
import re
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
MIGRATIONS_DIR = PROJECT_ROOT / "migrations" / "versions"
ALEMBIC_INI = PROJECT_ROOT / "alembic.ini"


def generate_timestamp() -> str:
    """Generate timestamp in YYYYMMDD_HHMMSS format."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def sanitize_description(description: str) -> str:
    """
    Sanitize description for use in filename.

    - Lowercase
    - Replace spaces/special chars with underscores
    - Remove consecutive underscores
    - Max 50 chars
    """
    # Lowercase and replace non-alphanumeric with underscore
    sanitized = re.sub(r'[^a-zA-Z0-9]+', '_', description.lower())
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Truncate to 50 chars
    return sanitized[:50]


def generate_migration_name(description: str) -> str:
    """Generate full migration filename (without .py)."""
    timestamp = generate_timestamp()
    sanitized = sanitize_description(description)
    return f"{timestamp}_{sanitized}"


def check_existing_migrations() -> List[str]:
    """Get list of existing migration files."""
    if not MIGRATIONS_DIR.exists():
        return []
    return [f.stem for f in MIGRATIONS_DIR.glob("*.py") if f.stem != "__pycache__"]


def validate_migration_naming() -> Tuple[bool, List[str]]:
    """
    Validate all migrations follow timestamp naming convention.

    Returns:
        (is_valid, list_of_violations)
    """
    pattern = re.compile(r'^\d{8}_\d{6}_[a-z0-9_]+$')
    violations = []

    for migration in check_existing_migrations():
        # Skip special files
        if migration.startswith('_'):
            continue

        if not pattern.match(migration):
            violations.append(migration)

    return len(violations) == 0, violations


def create_migration(description: str, autogenerate: bool = True) -> Optional[str]:
    """
    Create a new migration with timestamped name.

    Args:
        description: Human-readable description
        autogenerate: Whether to autogenerate from models

    Returns:
        Migration filename if successful, None otherwise
    """
    migration_name = generate_migration_name(description)

    # Build alembic command
    cmd = [
        "alembic", "revision",
        "-m", migration_name,
    ]

    if autogenerate:
        cmd.append("--autogenerate")

    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"✅ Created migration: {migration_name}")
            print(f"   File: migrations/versions/{migration_name}.py")
            return migration_name
        else:
            print(f"❌ Failed to create migration:")
            print(result.stderr)
            return None

    except Exception as e:
        print(f"❌ Error running alembic: {e}")
        return None


def list_migrations() -> None:
    """List all migrations with their timestamps."""
    migrations = sorted(check_existing_migrations())

    print(f"\n📋 Migrations ({len(migrations)} total):\n")

    for migration in migrations:
        # Try to parse timestamp
        match = re.match(r'^(\d{8})_(\d{6})_(.+)$', migration)
        if match:
            date_str = match.group(1)
            time_str = match.group(2)
            desc = match.group(3).replace('_', ' ')

            # Format date nicely
            try:
                dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted = f"{date_str} {time_str}"

            print(f"  {formatted}  {desc}")
        else:
            print(f"  ⚠️  {migration} (non-standard naming)")

    print()


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Alembic wrapper for timestamped migrations"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # new command
    new_parser = subparsers.add_parser("new", help="Create new migration")
    new_parser.add_argument("description", help="Migration description")
    new_parser.add_argument(
        "--no-autogenerate",
        action="store_true",
        help="Don't autogenerate from models"
    )

    # validate command
    subparsers.add_parser("validate", help="Validate migration naming")

    # list command
    subparsers.add_parser("list", help="List all migrations")

    args = parser.parse_args()

    if args.command == "new":
        create_migration(args.description, not args.no_autogenerate)
    elif args.command == "validate":
        is_valid, violations = validate_migration_naming()
        if is_valid:
            print("✅ All migrations follow naming convention")
            sys.exit(0)
        else:
            print("❌ Migrations with non-standard naming:")
            for v in violations:
                print(f"   - {v}")
            sys.exit(1)
    elif args.command == "list":
        list_migrations()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

---

## Step 2: Add CLI Commands to ip2adb (25 min)

Update or create `src/cli/migrations.py`:

```python
"""
Migration CLI commands for ip2adb.
"""

import click
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


@click.group()
def migrate():
    """Migration management commands."""
    pass


@migrate.command("new")
@click.argument("description")
@click.option("--no-autogenerate", is_flag=True, help="Don't autogenerate from models")
def migrate_new(description: str, no_autogenerate: bool):
    """
    Create a new timestamped migration.

    Example:
        ip2adb migrate new "add user preferences"
    """
    script = PROJECT_ROOT / "scripts" / "alembic_wrapper.py"

    cmd = [sys.executable, str(script), "new", description]
    if no_autogenerate:
        cmd.append("--no-autogenerate")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    sys.exit(result.returncode)


@migrate.command("validate")
def migrate_validate():
    """Validate migration naming conventions."""
    script = PROJECT_ROOT / "scripts" / "alembic_wrapper.py"

    result = subprocess.run(
        [sys.executable, str(script), "validate"],
        cwd=PROJECT_ROOT
    )
    sys.exit(result.returncode)


@migrate.command("list")
def migrate_list():
    """List all migrations with timestamps."""
    script = PROJECT_ROOT / "scripts" / "alembic_wrapper.py"

    result = subprocess.run(
        [sys.executable, str(script), "list"],
        cwd=PROJECT_ROOT
    )
    sys.exit(result.returncode)


@migrate.command("upgrade")
@click.argument("revision", default="head")
def migrate_upgrade(revision: str):
    """
    Upgrade database to a revision.

    Example:
        ip2adb migrate upgrade head
        ip2adb migrate upgrade +1
    """
    result = subprocess.run(
        ["alembic", "upgrade", revision],
        cwd=PROJECT_ROOT
    )
    sys.exit(result.returncode)


@migrate.command("downgrade")
@click.argument("revision")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def migrate_downgrade(revision: str, yes: bool):
    """
    Downgrade database to a revision.

    Example:
        ip2adb migrate downgrade -1
        ip2adb migrate downgrade base
    """
    if not yes:
        click.confirm(
            f"⚠️  Downgrade to '{revision}'? This may cause data loss.",
            abort=True
        )

    result = subprocess.run(
        ["alembic", "downgrade", revision],
        cwd=PROJECT_ROOT
    )
    sys.exit(result.returncode)


@migrate.command("current")
def migrate_current():
    """Show current database revision."""
    result = subprocess.run(
        ["alembic", "current"],
        cwd=PROJECT_ROOT
    )
    sys.exit(result.returncode)


@migrate.command("history")
@click.option("--verbose", "-v", is_flag=True, help="Show verbose output")
def migrate_history(verbose: bool):
    """Show migration history."""
    cmd = ["alembic", "history"]
    if verbose:
        cmd.append("-v")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    sys.exit(result.returncode)
```

---

## Step 3: Register CLI Commands (10 min)

Update `src/cli/__init__.py` or main CLI file:

```python
# Add import
from src.cli.migrations import migrate

# Add to main CLI group
cli.add_command(migrate)
```

If using `pyproject.toml` entry points, ensure it's registered:

```toml
[project.scripts]
ip2adb = "src.cli:cli"
```

---

## Step 4: Add Pre-commit Hook (15 min)

Update `.pre-commit-config.yaml`:

```yaml
repos:
  # ... existing repos ...

  - repo: local
    hooks:
      - id: migration-naming
        name: Validate migration naming
        entry: python scripts/alembic_wrapper.py validate
        language: python
        files: ^migrations/versions/.*\.py$
        pass_filenames: false
        always_run: true
```

Test the hook:

```bash
pre-commit run migration-naming --all-files
```

---

## Step 5: Create Reference Documentation (15 min)

Create `docs/reference/migration-cli.md`:

```markdown
# Migration CLI Reference

## Overview

The `ip2adb migrate` commands provide safe migration management with timestamped naming.

## Commands

### Create New Migration

```bash
ip2adb migrate new "description"
```

Creates a timestamped migration file:
- Format: `YYYYMMDD_HHMMSS_description.py`
- Example: `20260129_143052_add_user_preferences.py`

Options:
- `--no-autogenerate`: Create empty migration (don't autogenerate from models)

### Validate Naming

```bash
ip2adb migrate validate
```

Checks all migrations follow the timestamp naming convention.

### List Migrations

```bash
ip2adb migrate list
```

Shows all migrations with formatted timestamps.

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

All migrations MUST follow this pattern:

```
YYYYMMDD_HHMMSS_description.py
```

Where:
- `YYYYMMDD`: Date (e.g., 20260129)
- `HHMMSS`: Time (e.g., 143052)
- `description`: Snake_case description (max 50 chars)

### Examples

✅ Good:
- `20260129_143052_add_user_preferences.py`
- `20260130_091234_create_audit_log_indexes.py`

❌ Bad:
- `001_initial.py` (no timestamp)
- `add_users.py` (no timestamp)
- `20260129_add_users.py` (missing time)

## Pre-commit Hook

The migration naming convention is enforced by pre-commit:

```bash
# Run manually
pre-commit run migration-naming --all-files

# Runs automatically on commit
git commit -m "..."
```

## Legacy Migrations

Existing migrations without timestamps are grandfathered but flagged as warnings.
New migrations MUST use timestamps.
```

---

## Step 6: Update ROADMAP.md (5 min)

Check off completed item:

```markdown
## Phase 2 — Migration Safety (Current) 🟡
- [x] Migration naming enforcement
- [x] Legacy migration freeze
- [x] Breaking change detection
- [x] Alembic wrapper for timestamped generation  ← DONE
- [ ] Migration dependency graph (FK-based)
- [ ] Auto-detect destructive downgrades
```

---

## Step 7: Test the Implementation (10 min)

```bash
# Test migration creation
ip2adb migrate new "test migration"

# Verify timestamp format
ls migrations/versions/ | tail -1

# Test validation
ip2adb migrate validate

# Test listing
ip2adb migrate list

# Clean up test migration
rm migrations/versions/$(ls migrations/versions/ | tail -1)
```

---

## Step 8: Commit Session A (5 min)

```bash
git add -A
git status

git commit -m "feat(infra): Migration wrapper with timestamped naming

- Create scripts/alembic_wrapper.py for timestamped migrations
- Add ip2adb migrate commands (new, validate, list, upgrade, downgrade)
- Add pre-commit hook for migration naming validation
- Create migration CLI reference documentation
- Update ROADMAP.md with completed task

Migration format: YYYYMMDD_HHMMSS_description.py
Example: 20260129_143052_add_user_preferences.py"

git push origin main
```

---

## Session A Checklist

- [ ] Created `scripts/alembic_wrapper.py`
- [ ] Created `src/cli/migrations.py`
- [ ] Registered CLI commands
- [ ] Added pre-commit hook
- [ ] Created `docs/reference/migration-cli.md`
- [ ] Updated ROADMAP.md
- [ ] Tested all commands
- [ ] Committed changes

---

## 📝 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session.

### Before Ending This Session:

1. **Scan `/docs/*`** - Review all documentation files
2. **Update existing docs** - Reflect changes, progress, and decisions
3. **Create new docs** - If needed for new components or concepts
4. **ADR Review** - Update or create Architecture Decision Records as necessary
5. **Session log entry** - Record what was accomplished

This ensures historical record-keeping and project continuity ("bus factor" protection).

---

*Session A complete. Proceed to Session B for FK Dependency Graph and Destructive Detection.*
