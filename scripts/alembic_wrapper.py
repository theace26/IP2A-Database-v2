#!/usr/bin/env python3
"""
Alembic Wrapper - Timestamped migration generation.

This wrapper ensures all migrations have consistent, conflict-free naming:
- Format: YYYYMMDD_HHMMSS_description.py
- Example: 20260129_143052_add_user_preferences.py

Usage:
    python scripts/alembic_wrapper.py new "add user preferences"
    python scripts/alembic_wrapper.py validate
    python scripts/alembic_wrapper.py list
"""

import re
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
MIGRATIONS_DIR = PROJECT_ROOT / "src" / "db" / "migrations" / "versions"
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
    sanitized = re.sub(r"[^a-zA-Z0-9]+", "_", description.lower())
    # Remove leading/trailing underscores
    sanitized = sanitized.strip("_")
    # Remove consecutive underscores
    sanitized = re.sub(r"_+", "_", sanitized)
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
    pattern = re.compile(r"^\d{8}_\d{6}_[a-z0-9_]+$")
    violations = []

    for migration in check_existing_migrations():
        # Skip special files
        if migration.startswith("_"):
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
        "alembic",
        "revision",
        "-m",
        migration_name,
    ]

    if autogenerate:
        cmd.append("--autogenerate")

    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"Created migration: {migration_name}")
            print(f"   File: src/db/migrations/versions/{migration_name}.py")
            return migration_name
        else:
            print("Failed to create migration:")
            print(result.stderr)
            return None

    except Exception as e:
        print(f"Error running alembic: {e}")
        return None


def list_migrations() -> None:
    """List all migrations with their timestamps."""
    migrations = sorted(check_existing_migrations())

    print(f"\nMigrations ({len(migrations)} total):\n")

    timestamped_count = 0
    legacy_count = 0

    for migration in migrations:
        # Try to parse timestamp
        match = re.match(r"^(\d{8})_(\d{6})_(.+)$", migration)
        if match:
            date_str = match.group(1)
            time_str = match.group(2)
            desc = match.group(3).replace("_", " ")

            # Format date nicely
            try:
                dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                formatted = f"{date_str} {time_str}"

            print(f"  {formatted}  {desc}")
            timestamped_count += 1
        else:
            print(f"  [legacy]  {migration}")
            legacy_count += 1

    print()
    print(f"Summary: {timestamped_count} timestamped, {legacy_count} legacy migrations")
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
        help="Don't autogenerate from models",
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
            print("All migrations follow naming convention")
            sys.exit(0)
        else:
            print("Migrations with non-standard naming (legacy):")
            for v in violations:
                print(f"   - {v}")
            # Don't fail for legacy migrations - just warn
            print(
                "\nNote: Legacy migrations are grandfathered. New migrations must use timestamps."
            )
            sys.exit(0)
    elif args.command == "list":
        list_migrations()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
