#!/usr/bin/env python
"""
Database Load Testing Tool

Simulates concurrent users performing realistic database operations.
Tests performance, throughput, and scalability under load.

Usage:
    python run_load_test.py                         # Default: 50 users, 50 ops each
    python run_load_test.py --users 100             # 100 concurrent users
    python run_load_test.py --ops 100               # 100 operations per user
    python run_load_test.py --quick                 # Quick test: 10 users, 20 ops
    python run_load_test.py --stress                # Stress test: 200 users, 100 ops
    python run_load_test.py --pattern read_heavy    # All users read-heavy
    python run_load_test.py --export report.txt     # Export report to file

Patterns:
    read_heavy      - 90% reads, 10% writes (typical viewer/searcher)
    write_heavy     - 70% writes, 30% reads (data entry user)
    mixed           - 60% reads, 40% writes (typical user)
    file_operations - File attachment operations

For production testing, ensure database has seed data first.
"""

import sys
import argparse
from datetime import datetime

from src.tests.load_test import LoadTest
from src.config.settings import settings


def main():
    parser = argparse.ArgumentParser(
        description="Database Load Testing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--users",
        type=int,
        default=50,
        help="Number of concurrent users (default: 50)"
    )

    parser.add_argument(
        "--ops",
        type=int,
        default=50,
        help="Operations per user (default: 50)"
    )

    parser.add_argument(
        "--think-time",
        type=int,
        default=100,
        help="Think time between operations in ms (default: 100)"
    )

    parser.add_argument(
        "--ramp-up",
        type=int,
        default=10,
        help="Ramp-up time in seconds (default: 10)"
    )

    parser.add_argument(
        "--pattern",
        choices=["read_heavy", "write_heavy", "mixed", "file_operations", "distributed"],
        default="distributed",
        help="User pattern (default: distributed mix)"
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick test: 10 users, 20 ops each"
    )

    parser.add_argument(
        "--stress",
        action="store_true",
        help="Stress test: 200 users, 100 ops each"
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
        print("🚨 ERROR: Load test is blocked in production environment")
        print("   Load testing can impact production users!")
        print("   Use --force flag if you really need to run this in production")
        print("   Consider running in staging environment instead")
        sys.exit(1)

    # Preset configurations
    if args.quick:
        args.users = 10
        args.ops = 20
        print("🏃 Quick Test Mode: 10 users, 20 ops each")
    elif args.stress:
        args.users = 200
        args.ops = 100
        print("💪 Stress Test Mode: 200 users, 100 ops each")

    print("=" * 70)
    print("  DATABASE LOAD TEST")
    print("=" * 70)
    print()
    print(f"Environment: {env}")
    print(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'local'}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    if not args.quick and not args.stress and sys.stdin.isatty():
        confirm = input(f"Start load test with {args.users} users? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            sys.exit(0)
        print()

    # Configure pattern distribution
    pattern_distribution = None
    if args.pattern != "distributed":
        # Single pattern mode
        pattern_distribution = {args.pattern: 1.0}
    else:
        # Distributed pattern (default)
        pattern_distribution = {
            "read_heavy": 0.5,       # 50% read-heavy users
            "write_heavy": 0.2,      # 20% write-heavy users
            "mixed": 0.25,           # 25% mixed users
            "file_operations": 0.05  # 5% file operations
        }

    # Create and run load test
    load_test = LoadTest(
        num_users=args.users,
        operations_per_user=args.ops,
        think_time_ms=args.think_time,
        ramp_up_seconds=args.ramp_up
    )

    try:
        load_test.run(pattern_distribution=pattern_distribution)

        # Generate report
        report = load_test.generate_report()
        print(report)

        # Export report if requested
        if args.export:
            with open(args.export, "w") as f:
                f.write(report)
            print(f"\n📄 Report exported to: {args.export}")

        # Determine exit code based on performance
        all_operations = []
        for user in load_test.users:
            all_operations.extend(user.metrics.operations)

        failed_ops = sum(1 for op in all_operations if not op.success)
        total_ops = len(all_operations)
        failure_rate = (failed_ops / total_ops) if total_ops > 0 else 0

        if failure_rate > 0.05:  # More than 5% failures
            print("\n⚠️  High failure rate detected - review database performance")
            return 1

        print("\n✅ Load test completed successfully")
        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Load test interrupted by user")
        return 130

    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
