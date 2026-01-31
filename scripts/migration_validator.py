#!/usr/bin/env python3
"""
Migration Validator - Detect destructive operations.

Scans migration files for potentially dangerous operations:
- DROP TABLE
- DROP COLUMN
- TRUNCATE
- DELETE without WHERE

Usage:
    python scripts/migration_validator.py check
    python scripts/migration_validator.py check --strict
"""

import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).parent.parent
MIGRATIONS_DIR = PROJECT_ROOT / "src" / "db" / "migrations" / "versions"


class Severity(Enum):
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Issue:
    """Represents a detected issue in a migration."""

    file: str
    line: int
    severity: Severity
    operation: str
    context: str
    message: str


# Patterns to detect
DESTRUCTIVE_PATTERNS = [
    # (pattern, severity, operation_name)
    (r"\bop\.drop_table\s*\(", Severity.CRITICAL, "DROP TABLE"),
    (r"\bop\.drop_column\s*\(", Severity.ERROR, "DROP COLUMN"),
    (r"\bop\.drop_index\s*\(", Severity.WARNING, "DROP INDEX"),
    (r"\bop\.drop_constraint\s*\(", Severity.WARNING, "DROP CONSTRAINT"),
    (r"\bDROP\s+TABLE\b", Severity.CRITICAL, "DROP TABLE (raw SQL)"),
    (r"\bDROP\s+COLUMN\b", Severity.ERROR, "DROP COLUMN (raw SQL)"),
    (r"\bTRUNCATE\b", Severity.CRITICAL, "TRUNCATE"),
    (r"\bDELETE\s+FROM\s+\w+\s*;", Severity.CRITICAL, "DELETE without WHERE"),
    (r"\bALTER\s+TABLE\s+\w+\s+DROP\b", Severity.ERROR, "ALTER TABLE DROP"),
]

# Patterns that indicate this is a downgrade (more lenient)
DOWNGRADE_INDICATORS = [
    r"def\s+downgrade\s*\(\s*\)\s*:",
]

# Timestamp pattern for new migrations
TIMESTAMP_PATTERN = re.compile(r"^\d{8}_\d{6}_[a-z0-9_]+\.py$")


def scan_migration(filepath: Path) -> List[Issue]:
    """
    Scan a migration file for destructive operations.

    Returns:
        List of detected issues
    """
    issues = []
    content = filepath.read_text()
    lines = content.split("\n")

    in_downgrade = False

    for line_num, line in enumerate(lines, 1):
        # Track if we're in downgrade function
        for indicator in DOWNGRADE_INDICATORS:
            if re.search(indicator, line):
                in_downgrade = True
                break

        # Check for upgrade function (reset flag)
        if re.search(r"def\s+upgrade\s*\(\s*\)\s*:", line):
            in_downgrade = False

        # Check for destructive patterns
        for pattern, severity, operation in DESTRUCTIVE_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                # Downgrade functions are expected to have drops
                if in_downgrade:
                    # Still flag but as warning
                    adjusted_severity = Severity.WARNING
                    message = f"{operation} in downgrade (expected but verify)"
                else:
                    adjusted_severity = severity
                    message = f"{operation} detected in upgrade"

                issues.append(
                    Issue(
                        file=filepath.name,
                        line=line_num,
                        severity=adjusted_severity,
                        operation=operation,
                        context=line.strip()[:80],
                        message=message,
                    )
                )

    return issues


def is_legacy_migration(filename: str) -> bool:
    """Check if migration uses legacy (non-timestamp) naming."""
    return not TIMESTAMP_PATTERN.match(filename)


def scan_all_migrations(skip_legacy: bool = False) -> Dict[str, List[Issue]]:
    """
    Scan all migration files.

    Args:
        skip_legacy: If True, skip migrations without timestamp naming

    Returns:
        Dict mapping filename to list of issues
    """
    results = {}
    skipped = 0

    if not MIGRATIONS_DIR.exists():
        print(f"Warning: Migrations directory not found: {MIGRATIONS_DIR}")
        return results

    for migration_file in sorted(MIGRATIONS_DIR.glob("*.py")):
        if migration_file.name.startswith("_"):
            continue

        # Skip legacy migrations if requested
        if skip_legacy and is_legacy_migration(migration_file.name):
            skipped += 1
            continue

        issues = scan_migration(migration_file)
        if issues:
            results[migration_file.name] = issues

    if skipped > 0:
        print(
            f"Skipped {skipped} legacy migrations (use --include-legacy to check all)"
        )

    return results


def print_results(results: Dict[str, List[Issue]], strict: bool = False) -> int:
    """
    Print scan results.

    Returns:
        Exit code (0 = pass, 1 = warnings, 2 = errors)
    """
    if not results:
        print("No destructive operations detected")
        return 0

    has_errors = False
    has_warnings = False

    print("\n" + "=" * 60)
    print("MIGRATION VALIDATOR RESULTS")
    print("=" * 60)

    for filename, issues in sorted(results.items()):
        print(f"\n{filename}")

        for issue in issues:
            icon = {
                Severity.WARNING: "WARN",
                Severity.ERROR: "ERROR",
                Severity.CRITICAL: "CRIT",
            }[issue.severity]

            print(f"  [{icon}] Line {issue.line}: {issue.message}")
            print(f"      {issue.context}")

            if issue.severity == Severity.CRITICAL:
                has_errors = True
            elif issue.severity == Severity.ERROR:
                has_errors = True
            else:
                has_warnings = True

    print("\n" + "-" * 60)

    # Summary
    total_issues = sum(len(issues) for issues in results.values())
    critical = sum(
        1
        for issues in results.values()
        for i in issues
        if i.severity == Severity.CRITICAL
    )
    errors = sum(
        1 for issues in results.values() for i in issues if i.severity == Severity.ERROR
    )
    warnings = sum(
        1
        for issues in results.values()
        for i in issues
        if i.severity == Severity.WARNING
    )

    print(
        f"Total: {total_issues} issues ({critical} critical, {errors} errors, {warnings} warnings)"
    )

    if has_errors:
        print("\nFAILED: Destructive operations require review")
        return 2
    elif has_warnings:
        if strict:
            print("\nWARNINGS treated as errors in strict mode")
            return 1
        print("\nPASSED with warnings")
        return 0
    else:
        print("\nPASSED")
        return 0


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migration destructive operation detector"
    )
    parser.add_argument("command", choices=["check"], help="Command to run")
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as errors"
    )
    parser.add_argument("--file", "-f", help="Check specific migration file")
    parser.add_argument(
        "--skip-legacy",
        action="store_true",
        help="Skip legacy migrations (non-timestamp naming)",
    )
    parser.add_argument(
        "--include-legacy",
        action="store_true",
        help="Include legacy migrations in check",
    )

    args = parser.parse_args()

    if args.command == "check":
        if args.file:
            filepath = MIGRATIONS_DIR / args.file
            if not filepath.exists():
                print(f"File not found: {args.file}")
                sys.exit(1)
            results = {args.file: scan_migration(filepath)}
        else:
            # Default: skip legacy migrations (they can't be changed anyway)
            skip_legacy = not args.include_legacy
            print("Scanning migrations...")
            results = scan_all_migrations(skip_legacy=skip_legacy)

        exit_code = print_results(results, args.strict)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
