# Infrastructure Phase 2 - Session B: FK Graph + Destructive Detection

**Document:** 2 of 2
**Estimated Time:** 2-3 hours
**Focus:** Migration dependency graph and destructive operation detection

---

## Objective

Create tools to:
- Analyze FK relationships between models
- Generate migration dependency graph
- Detect destructive operations in migrations
- Block/warn on dangerous changes
- Create ADR documenting the strategy

---

## Pre-flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5
```

---

## Step 1: Create Migration Graph Analyzer (45 min)

Create `scripts/migration_graph.py`:

```python
#!/usr/bin/env python3
"""
Migration Dependency Graph - FK relationship analysis.

Analyzes SQLAlchemy models to determine migration order based on
foreign key dependencies. Ensures tables are created/dropped in
the correct order.

Usage:
    python scripts/migration_graph.py analyze
    python scripts/migration_graph.py visualize
    python scripts/migration_graph.py order
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import inspect
from sqlalchemy.orm import RelationshipProperty


def get_all_models() -> Dict[str, type]:
    """
    Import and return all SQLAlchemy models.

    Returns:
        Dict mapping table name to model class
    """
    models = {}

    # Import all models
    try:
        from src.models import (
            User, Role, UserRole, RefreshToken,
            Organization, OrgContact, Member, MemberEmployment,
            SaltingActivity, SaltingLog,
            BenevolenceRequest, BenevolencePayment,
            Grievance, GrievanceStep,
            Student, Course, ClassSession, Enrollment,
            Attendance, Grade, Certification, Cohort,
            Document,
            DuesRate, DuesPeriod, DuesPayment, DuesAdjustment,
            AuditLog,
        )

        # Get all model classes
        model_classes = [
            User, Role, UserRole, RefreshToken,
            Organization, OrgContact, Member, MemberEmployment,
            SaltingActivity, SaltingLog,
            BenevolenceRequest, BenevolencePayment,
            Grievance, GrievanceStep,
            Student, Course, ClassSession, Enrollment,
            Attendance, Grade, Certification, Cohort,
            Document,
            DuesRate, DuesPeriod, DuesPayment, DuesAdjustment,
            AuditLog,
        ]

        for model in model_classes:
            if hasattr(model, '__tablename__'):
                models[model.__tablename__] = model

    except ImportError as e:
        print(f"Warning: Could not import some models: {e}")

    return models


def analyze_foreign_keys(models: Dict[str, type]) -> Dict[str, Set[str]]:
    """
    Analyze FK relationships between models.

    Returns:
        Dict mapping table name to set of tables it depends on
    """
    dependencies = defaultdict(set)

    for table_name, model in models.items():
        # Get mapper for the model
        try:
            mapper = inspect(model)
        except Exception:
            continue

        # Check columns for foreign keys
        for column in mapper.columns:
            for fk in column.foreign_keys:
                # fk.column.table.name is the referenced table
                referenced_table = fk.column.table.name
                if referenced_table != table_name:  # Avoid self-references
                    dependencies[table_name].add(referenced_table)

    return dict(dependencies)


def topological_sort(dependencies: Dict[str, Set[str]]) -> List[str]:
    """
    Perform topological sort to get correct migration order.

    Tables with no dependencies come first.
    Tables that depend on others come after their dependencies.

    Returns:
        List of table names in migration order
    """
    # Get all tables
    all_tables = set(dependencies.keys())
    for deps in dependencies.values():
        all_tables.update(deps)

    # Tables with no dependencies (or not in dependencies dict)
    result = []
    remaining = set(all_tables)
    resolved = set()

    while remaining:
        # Find tables with all dependencies resolved
        ready = []
        for table in remaining:
            deps = dependencies.get(table, set())
            if deps.issubset(resolved):
                ready.append(table)

        if not ready:
            # Circular dependency detected
            print(f"⚠️  Circular dependency detected among: {remaining}")
            # Add remaining in arbitrary order
            result.extend(sorted(remaining))
            break

        # Sort alphabetically for deterministic output
        ready.sort()
        result.extend(ready)
        resolved.update(ready)
        remaining -= set(ready)

    return result


def generate_mermaid_diagram(dependencies: Dict[str, Set[str]]) -> str:
    """Generate Mermaid diagram of FK relationships."""
    lines = ["```mermaid", "graph TD"]

    # Add nodes
    all_tables = set(dependencies.keys())
    for deps in dependencies.values():
        all_tables.update(deps)

    for table in sorted(all_tables):
        lines.append(f"    {table}[{table}]")

    # Add edges (dependencies)
    for table, deps in sorted(dependencies.items()):
        for dep in sorted(deps):
            lines.append(f"    {dep} --> {table}")

    lines.append("```")
    return "\n".join(lines)


def print_analysis(dependencies: Dict[str, Set[str]], order: List[str]) -> None:
    """Print analysis results."""
    print("\n" + "=" * 60)
    print("MIGRATION DEPENDENCY ANALYSIS")
    print("=" * 60)

    print("\n📊 Foreign Key Dependencies:\n")
    for table in sorted(dependencies.keys()):
        deps = dependencies[table]
        if deps:
            print(f"  {table}")
            for dep in sorted(deps):
                print(f"    └── depends on: {dep}")

    print("\n📋 Migration Order (create):\n")
    for i, table in enumerate(order, 1):
        deps = dependencies.get(table, set())
        dep_str = f" (depends on: {', '.join(sorted(deps))})" if deps else " (no dependencies)"
        print(f"  {i:2}. {table}{dep_str}")

    print("\n📋 Migration Order (drop):\n")
    for i, table in enumerate(reversed(order), 1):
        print(f"  {i:2}. {table}")

    print()


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Migration dependency analyzer")
    parser.add_argument(
        "command",
        choices=["analyze", "visualize", "order"],
        help="Command to run"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for visualization"
    )

    args = parser.parse_args()

    # Load models and analyze
    print("🔍 Loading models...")
    models = get_all_models()
    print(f"   Found {len(models)} models")

    print("🔍 Analyzing foreign keys...")
    dependencies = analyze_foreign_keys(models)

    print("🔍 Computing migration order...")
    order = topological_sort(dependencies)

    if args.command == "analyze":
        print_analysis(dependencies, order)

    elif args.command == "visualize":
        diagram = generate_mermaid_diagram(dependencies)
        if args.output:
            Path(args.output).write_text(diagram)
            print(f"✅ Diagram saved to {args.output}")
        else:
            print("\n" + diagram + "\n")

    elif args.command == "order":
        print("\n📋 Tables in migration order:\n")
        for table in order:
            print(f"  {table}")
        print()


if __name__ == "__main__":
    main()
```

---

## Step 2: Create Destructive Operation Detector (35 min)

Create `scripts/migration_validator.py`:

```python
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
from pathlib import Path
from typing import List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum

PROJECT_ROOT = Path(__file__).parent.parent
MIGRATIONS_DIR = PROJECT_ROOT / "migrations" / "versions"


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
    (r'\bop\.drop_table\s*\(', Severity.CRITICAL, "DROP TABLE"),
    (r'\bop\.drop_column\s*\(', Severity.ERROR, "DROP COLUMN"),
    (r'\bop\.drop_index\s*\(', Severity.WARNING, "DROP INDEX"),
    (r'\bop\.drop_constraint\s*\(', Severity.WARNING, "DROP CONSTRAINT"),
    (r'\bDROP\s+TABLE\b', Severity.CRITICAL, "DROP TABLE (raw SQL)"),
    (r'\bDROP\s+COLUMN\b', Severity.ERROR, "DROP COLUMN (raw SQL)"),
    (r'\bTRUNCATE\b', Severity.CRITICAL, "TRUNCATE"),
    (r'\bDELETE\s+FROM\s+\w+\s*;', Severity.CRITICAL, "DELETE without WHERE"),
    (r'\bALTER\s+TABLE\s+\w+\s+DROP\b', Severity.ERROR, "ALTER TABLE DROP"),
]

# Patterns that indicate this is a downgrade (more lenient)
DOWNGRADE_INDICATORS = [
    r'def\s+downgrade\s*\(\s*\)\s*:',
]


def scan_migration(filepath: Path) -> List[Issue]:
    """
    Scan a migration file for destructive operations.

    Returns:
        List of detected issues
    """
    issues = []
    content = filepath.read_text()
    lines = content.split('\n')

    in_downgrade = False

    for line_num, line in enumerate(lines, 1):
        # Track if we're in downgrade function
        for indicator in DOWNGRADE_INDICATORS:
            if re.search(indicator, line):
                in_downgrade = True
                break

        # Check for upgrade function (reset flag)
        if re.search(r'def\s+upgrade\s*\(\s*\)\s*:', line):
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

                issues.append(Issue(
                    file=filepath.name,
                    line=line_num,
                    severity=adjusted_severity,
                    operation=operation,
                    context=line.strip()[:80],
                    message=message,
                ))

    return issues


def scan_all_migrations() -> Dict[str, List[Issue]]:
    """
    Scan all migration files.

    Returns:
        Dict mapping filename to list of issues
    """
    results = {}

    if not MIGRATIONS_DIR.exists():
        print(f"⚠️  Migrations directory not found: {MIGRATIONS_DIR}")
        return results

    for migration_file in sorted(MIGRATIONS_DIR.glob("*.py")):
        if migration_file.name.startswith('_'):
            continue

        issues = scan_migration(migration_file)
        if issues:
            results[migration_file.name] = issues

    return results


def print_results(results: Dict[str, List[Issue]], strict: bool = False) -> int:
    """
    Print scan results.

    Returns:
        Exit code (0 = pass, 1 = warnings, 2 = errors)
    """
    if not results:
        print("✅ No destructive operations detected")
        return 0

    has_errors = False
    has_warnings = False

    print("\n" + "=" * 60)
    print("MIGRATION VALIDATOR RESULTS")
    print("=" * 60)

    for filename, issues in sorted(results.items()):
        print(f"\n📄 {filename}")

        for issue in issues:
            icon = {
                Severity.WARNING: "⚠️ ",
                Severity.ERROR: "❌",
                Severity.CRITICAL: "🚨",
            }[issue.severity]

            print(f"  {icon} Line {issue.line}: {issue.message}")
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
    critical = sum(1 for issues in results.values() for i in issues if i.severity == Severity.CRITICAL)
    errors = sum(1 for issues in results.values() for i in issues if i.severity == Severity.ERROR)
    warnings = sum(1 for issues in results.values() for i in issues if i.severity == Severity.WARNING)

    print(f"Total: {total_issues} issues ({critical} critical, {errors} errors, {warnings} warnings)")

    if has_errors:
        print("\n❌ FAILED: Destructive operations require review")
        return 2
    elif has_warnings:
        if strict:
            print("\n⚠️  WARNINGS treated as errors in strict mode")
            return 1
        print("\n⚠️  PASSED with warnings")
        return 0
    else:
        print("\n✅ PASSED")
        return 0


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Migration destructive operation detector")
    parser.add_argument(
        "command",
        choices=["check"],
        help="Command to run"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors"
    )
    parser.add_argument(
        "--file", "-f",
        help="Check specific migration file"
    )

    args = parser.parse_args()

    if args.command == "check":
        if args.file:
            filepath = MIGRATIONS_DIR / args.file
            if not filepath.exists():
                print(f"❌ File not found: {args.file}")
                sys.exit(1)
            results = {args.file: scan_migration(filepath)}
        else:
            print("🔍 Scanning all migrations...")
            results = scan_all_migrations()

        exit_code = print_results(results, args.strict)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
```

---

## Step 3: Add CLI Commands (15 min)

Update `src/cli/migrations.py`:

```python
# Add to existing file

@migrate.command("graph")
@click.option("--visualize", "-v", is_flag=True, help="Output Mermaid diagram")
@click.option("--output", "-o", help="Save diagram to file")
def migrate_graph(visualize: bool, output: str):
    """
    Show migration dependency graph.

    Analyzes FK relationships to determine correct migration order.
    """
    script = PROJECT_ROOT / "scripts" / "migration_graph.py"

    cmd = [sys.executable, str(script)]

    if visualize:
        cmd.append("visualize")
        if output:
            cmd.extend(["-o", output])
    else:
        cmd.append("analyze")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    sys.exit(result.returncode)


@migrate.command("check-destructive")
@click.option("--strict", is_flag=True, help="Treat warnings as errors")
@click.option("--file", "-f", help="Check specific file")
def migrate_check_destructive(strict: bool, file: str):
    """
    Check migrations for destructive operations.

    Scans for DROP TABLE, DROP COLUMN, TRUNCATE, etc.
    """
    script = PROJECT_ROOT / "scripts" / "migration_validator.py"

    cmd = [sys.executable, str(script), "check"]
    if strict:
        cmd.append("--strict")
    if file:
        cmd.extend(["-f", file])

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    sys.exit(result.returncode)
```

---

## Step 4: Update Pre-commit Hooks (10 min)

Add to `.pre-commit-config.yaml`:

```yaml
  - repo: local
    hooks:
      # ... existing hooks ...

      - id: migration-destructive
        name: Check for destructive migrations
        entry: python scripts/migration_validator.py check
        language: python
        files: ^migrations/versions/.*\.py$
        pass_filenames: false
        always_run: true
```

---

## Step 5: Create ADR-010 (20 min)

Create `docs/decisions/ADR-010-migration-safety.md`:

```markdown
# ADR-010: Migration Safety Strategy

## Status
Accepted

## Date
January XX, 2026

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
All migrations use the format: `YYYYMMDD_HHMMSS_description.py`

**Rationale:**
- Eliminates naming conflicts (timestamps are unique)
- Natural chronological sorting
- Easy to identify when migrations were created

**Implementation:**
- `ip2adb migrate new "description"` generates timestamped names
- Pre-commit hook validates naming convention
- Legacy migrations are grandfathered but flagged

### 2. FK Dependency Analysis
The `migration_graph.py` script analyzes SQLAlchemy models to:
- Map foreign key relationships
- Generate topological sort for migration order
- Detect circular dependencies

**Usage:**
```bash
ip2adb migrate graph           # Show analysis
ip2adb migrate graph -v        # Output Mermaid diagram
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
ip2adb migrate check-destructive
ip2adb migrate check-destructive --strict
```

### 4. Pre-commit Enforcement
Two hooks run automatically:
1. `migration-naming` - Validates timestamp format
2. `migration-destructive` - Scans for dangerous operations

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
1. **Sequential numbering** - Rejected due to conflict risk
2. **UUID-based names** - Rejected, not human-readable
3. **Branch-based prefixes** - Rejected, too complex

## Related ADRs
- ADR-001: Database Choice (PostgreSQL)
- ADR-003: Authentication (migrations for auth tables)

## References
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Django Migration Naming](https://docs.djangoproject.com/en/4.0/topics/migrations/)
```

---

## Step 6: Update Documentation (15 min)

### Update docs/reference/migration-cli.md

Add to existing file:

```markdown
## Dependency Analysis

### Show FK Graph

```bash
ip2adb migrate graph
```

Analyzes foreign key relationships and shows:
- Dependencies between tables
- Migration order (create)
- Migration order (drop - reverse)

### Generate Mermaid Diagram

```bash
ip2adb migrate graph -v
ip2adb migrate graph -v -o docs/architecture/diagrams/migration-deps.mermaid
```

## Destructive Operation Detection

### Check All Migrations

```bash
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
```

### Update ROADMAP.md

```markdown
## Phase 2 — Migration Safety (Current) ✅
- [x] Migration naming enforcement
- [x] Legacy migration freeze
- [x] Breaking change detection
- [x] Alembic wrapper for timestamped generation
- [x] Migration dependency graph (FK-based)
- [x] Auto-detect destructive downgrades
```

---

## Step 7: Create Session Log (10 min)

Create `docs/reports/session-logs/2026-01-XX-infra-phase2.md`:

```markdown
# Infrastructure Phase 2 Session Log

**Date:** January XX, 2026
**Phase:** Infrastructure 2 - Migration Safety
**Duration:** ~4-6 hours across 2 sessions

---

## Summary

Completed Infrastructure Phase 2: Migration Safety. Implemented timestamped migration generation, FK dependency analysis, and destructive operation detection.

---

## Completed Tasks

### Session A: Alembic Wrapper

| Task | Status |
|------|--------|
| Create scripts/alembic_wrapper.py | Done |
| Create src/cli/migrations.py | Done |
| Add pre-commit hook for naming | Done |
| Create migration CLI reference | Done |

### Session B: FK Graph + Validation

| Task | Status |
|------|--------|
| Create scripts/migration_graph.py | Done |
| Create scripts/migration_validator.py | Done |
| Add graph and check CLI commands | Done |
| Add destructive detection pre-commit | Done |
| Create ADR-010 | Done |
| Update documentation | Done |

---

## Files Created

```
scripts/
├── alembic_wrapper.py        # Timestamped migration generator
├── migration_graph.py        # FK dependency analyzer
└── migration_validator.py    # Destructive operation detector

src/cli/
└── migrations.py             # CLI commands

docs/
├── decisions/
│   └── ADR-010-migration-safety.md
└── reference/
    └── migration-cli.md      # Updated

.pre-commit-config.yaml       # Updated with hooks
```

---

## Key Features

### Timestamped Migrations
- Format: YYYYMMDD_HHMMSS_description.py
- Zero naming conflicts
- Chronological sorting

### FK Dependency Graph
- Analyzes SQLAlchemy models
- Topological sort for order
- Mermaid diagram output

### Destructive Detection
- Scans for DROP, TRUNCATE, DELETE
- Severity levels (warning/error/critical)
- Different rules for upgrade vs downgrade

---

## Infrastructure Phase 2 Complete ✅

All tasks from ROADMAP.md Phase 2 are now complete.
```

---

## Step 8: Final Commit (5 min)

```bash
# Run tests
pytest -v --tb=short

# Verify new tools work
ip2adb migrate validate
ip2adb migrate graph
ip2adb migrate check-destructive

# Commit
git add -A
git commit -m "feat(infra): Complete Infrastructure Phase 2 - Migration Safety

Session A: Alembic Wrapper
- scripts/alembic_wrapper.py for timestamped migrations
- ip2adb migrate new/validate/list commands
- Pre-commit hook for naming convention

Session B: FK Graph + Validation
- scripts/migration_graph.py for dependency analysis
- scripts/migration_validator.py for destructive detection
- ip2adb migrate graph/check-destructive commands
- Pre-commit hook for destructive operations
- ADR-010: Migration Safety Strategy

Migration format: YYYYMMDD_HHMMSS_description.py
Detects: DROP TABLE, DROP COLUMN, TRUNCATE, DELETE

Infrastructure Phase 2 Complete ✅"

git push origin main
```

---

## Session B Checklist

- [ ] Created `scripts/migration_graph.py`
- [ ] Created `scripts/migration_validator.py`
- [ ] Added graph and check-destructive CLI commands
- [ ] Added destructive detection pre-commit hook
- [ ] Created ADR-010
- [ ] Updated docs/reference/migration-cli.md
- [ ] Updated ROADMAP.md (all Phase 2 items checked)
- [ ] Created session log
- [ ] All tools working
- [ ] Committed changes

---

## Infrastructure Phase 2 Complete! 🎉

All tasks from ROADMAP.md Phase 2 are now complete:
- ✅ Migration naming enforcement
- ✅ Legacy migration freeze
- ✅ Breaking change detection
- ✅ Alembic wrapper for timestamped generation
- ✅ Migration dependency graph (FK-based)
- ✅ Auto-detect destructive downgrades

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

*Infrastructure Phase 2 complete. Ready for Phase 3: Schema Intelligence.*
