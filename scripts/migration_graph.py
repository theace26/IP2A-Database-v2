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

import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


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
            User,
            Role,
            UserRole,
            RefreshToken,
            EmailToken,
            Student,
            Course,
            Enrollment,
            Grade,
            Certification,
            Cohort,
            Instructor,
            Location,
            Expense,
            InstructorHours,
            Grant,
            ClassSession,
            Attendance,
            ToolsIssued,
            Credential,
            JATCApplication,
            InstructorCohortAssignment,
            Organization,
            OrganizationContact,
            Member,
            MemberEmployment,
            AuditLog,
            FileAttachment,
            SALTingActivity,
            BenevolenceApplication,
            BenevolenceReview,
            Grievance,
            GrievanceStepRecord,
            DuesRate,
            DuesPeriod,
            DuesPayment,
            DuesAdjustment,
        )

        # Get all model classes
        model_classes = [
            User,
            Role,
            UserRole,
            RefreshToken,
            EmailToken,
            Student,
            Course,
            Enrollment,
            Grade,
            Certification,
            Cohort,
            Instructor,
            Location,
            Expense,
            InstructorHours,
            Grant,
            ClassSession,
            Attendance,
            ToolsIssued,
            Credential,
            JATCApplication,
            InstructorCohortAssignment,
            Organization,
            OrganizationContact,
            Member,
            MemberEmployment,
            AuditLog,
            FileAttachment,
            SALTingActivity,
            BenevolenceApplication,
            BenevolenceReview,
            Grievance,
            GrievanceStepRecord,
            DuesRate,
            DuesPeriod,
            DuesPayment,
            DuesAdjustment,
        ]

        for model in model_classes:
            if hasattr(model, "__tablename__"):
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
    from sqlalchemy import inspect

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
            print(f"Warning: Circular dependency detected among: {remaining}")
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

    print("\nForeign Key Dependencies:\n")
    for table in sorted(dependencies.keys()):
        deps = dependencies[table]
        if deps:
            print(f"  {table}")
            for dep in sorted(deps):
                print(f"    -> depends on: {dep}")

    print("\nMigration Order (create):\n")
    for i, table in enumerate(order, 1):
        deps = dependencies.get(table, set())
        dep_str = (
            f" (depends on: {', '.join(sorted(deps))})"
            if deps
            else " (no dependencies)"
        )
        print(f"  {i:2}. {table}{dep_str}")

    print("\nMigration Order (drop/reverse):\n")
    for i, table in enumerate(reversed(order), 1):
        print(f"  {i:2}. {table}")

    print()


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Migration dependency analyzer")
    parser.add_argument(
        "command", choices=["analyze", "visualize", "order"], help="Command to run"
    )
    parser.add_argument("--output", "-o", help="Output file for visualization")

    args = parser.parse_args()

    # Load models and analyze
    print("Loading models...")
    models = get_all_models()
    print(f"   Found {len(models)} models")

    print("Analyzing foreign keys...")
    dependencies = analyze_foreign_keys(models)

    print("Computing migration order...")
    order = topological_sort(dependencies)

    if args.command == "analyze":
        print_analysis(dependencies, order)

    elif args.command == "visualize":
        diagram = generate_mermaid_diagram(dependencies)
        if args.output:
            Path(args.output).write_text(diagram)
            print(f"Diagram saved to {args.output}")
        else:
            print("\n" + diagram + "\n")

    elif args.command == "order":
        print("\nTables in migration order:\n")
        for table in order:
            print(f"  {table}")
        print()


if __name__ == "__main__":
    main()
