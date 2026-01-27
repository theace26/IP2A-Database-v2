#!/usr/bin/env python
"""
Database Integrity Check and Repair Tool

Validates database integrity and repairs issues automatically or interactively.

Usage:
    python run_integrity_check.py                  # Check only, no repairs
    python run_integrity_check.py --repair         # Auto-repair fixable issues
    python run_integrity_check.py --interactive    # Interactive repair for complex issues
    python run_integrity_check.py --dry-run        # Test repairs without committing
    python run_integrity_check.py --no-files       # Skip file system checks (faster)
    python run_integrity_check.py --export report.txt  # Export report to file

Features:
- Checks foreign key integrity (orphaned records)
- Validates required fields
- Verifies enum values
- Checks date logic
- Validates employment and contact logic
- Detects duplicates
- Checks file attachment integrity (optional)

For production use, always run with --dry-run first to preview changes.
"""

import sys
import argparse
from datetime import datetime

from src.db.session import get_db_session
from src.db.integrity_check import IntegrityChecker
from src.db.integrity_repair import IntegrityRepairer
from src.config.settings import settings


def main():
    parser = argparse.ArgumentParser(
        description="Database Integrity Check and Repair Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--repair",
        action="store_true",
        help="Automatically repair all auto-fixable issues"
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactively repair complex issues (e.g., missing files)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview repairs without making changes (use with --repair)"
    )

    parser.add_argument(
        "--no-files",
        action="store_true",
        help="Skip file system integrity checks (faster)"
    )

    parser.add_argument(
        "--export",
        type=str,
        metavar="FILE",
        help="Export report to file"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force run in production (dangerous)"
    )

    args = parser.parse_args()

    # Production safety check
    env = settings.IP2A_ENV.lower()
    if env == "production" and not args.force:
        print("🚨 ERROR: Integrity check is blocked in production environment")
        print("   Use --force flag if you really need to run this in production")
        print("   Consider running in a read-only mode or during maintenance window")
        sys.exit(1)

    print("=" * 70)
    print("  DATABASE INTEGRITY CHECK AND REPAIR")
    print("=" * 70)
    print()
    print(f"Environment: {env}")
    print(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'local'}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    if args.dry_run:
        print("🧪 DRY RUN MODE - No changes will be made to the database")
        print()

    if not args.repair and not args.interactive:
        print("Running in CHECK-ONLY mode (no repairs will be performed)")
        print("Use --repair to auto-fix issues or --interactive for manual fixes")
        print()

    # Initialize database session
    db = get_db_session()

    try:
        # === STEP 1: RUN INTEGRITY CHECKS ===
        checker = IntegrityChecker(db)
        check_files = not args.no_files

        issues = checker.run_all_checks(check_files=check_files)

        # Display report
        report = checker.generate_report()
        print(report)

        if args.export:
            with open(args.export, "w") as f:
                f.write(report)
            print(f"\n📄 Report exported to: {args.export}")

        # If no issues, we're done
        if not issues:
            print("\n🎉 Database integrity check complete - no issues found!")
            return 0

        # === STEP 2: AUTO-REPAIR (if requested) ===
        if args.repair:
            confirm = "yes"
            if not args.dry_run:
                print("\n⚠️  WARNING: About to perform automatic repairs")
                confirm = input("Continue? (yes/no): ")

            if confirm.lower() == "yes":
                repairer = IntegrityRepairer(db, dry_run=args.dry_run)
                actions = repairer.repair_all_auto_fixable(issues)

                # Display repair report
                repair_report = repairer.generate_repair_report()
                print(repair_report)

                if args.export:
                    export_repair = args.export.replace(".txt", "_repair.txt")
                    with open(export_repair, "w") as f:
                        f.write(repair_report)
                    print(f"📄 Repair report exported to: {export_repair}")

        # === STEP 3: INTERACTIVE REPAIR (if requested) ===
        if args.interactive:
            print("\n🤝 Starting Interactive Repair Mode")
            print("   You will be prompted for complex issues requiring decisions")
            print()

            confirm = input("Continue with interactive repair? (yes/no): ")
            if confirm.lower() == "yes":
                repairer = IntegrityRepairer(db, dry_run=args.dry_run)
                actions = repairer.interactive_repair_files(issues)

                if actions:
                    repair_report = repairer.generate_repair_report()
                    print(repair_report)

        # === STEP 4: SUMMARY ===
        print("\n" + "=" * 70)
        print("✅ INTEGRITY CHECK COMPLETE")
        print("=" * 70)

        remaining_critical = [i for i in issues if i.severity == "critical" and not any(
            a.issue.record_id == i.record_id and a.success for a in (repairer.actions if args.repair or args.interactive else [])
        )]

        if remaining_critical:
            print(f"\n⚠️  {len(remaining_critical)} critical issues still need attention")
            print("   Run again with --repair or --interactive to fix them")
            return 1
        else:
            print("\n🎉 All critical issues resolved!")
            return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        db.rollback()
        return 130

    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
