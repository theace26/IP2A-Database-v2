#!/usr/bin/env python
"""
Stress Test Seed Runner

Populates the database with large-scale test data:
- 10,000 members
- 1,000 students
- 500 instructors
- 250 locations
- 200 organizations
- ~250,000+ employment records

Usage:
    python run_stress_test.py              # With truncate
    python run_stress_test.py --no-truncate  # Without truncate (append data)

WARNING: This will take 10-30 minutes depending on your hardware.
"""

from src.seed.stress_test_seed import run_stress_test

if __name__ == "__main__":
    import sys

    print("=" * 70)
    print("  STRESS TEST SEED - Database Performance Testing")
    print("=" * 70)
    print()
    print("This will generate:")
    print("  • 10,000 members")
    print("  • ~250,000+ employment records (1-100 jobs per member)")
    print("  • ~150,000+ file attachments (~30 GB simulated)")
    print("     - 12MP photos, PDFs, scanned documents")
    print("     - 10+ files per member")
    print("     - Grievance files (1-50 per grievance)")
    print("  • 1,000 students")
    print("  • 500 instructors")
    print("  • 250 locations")
    print("  • 200 organizations")
    print()
    print("⚠️  WARNING: This process will take 15-45 minutes")
    print()

    truncate = "--no-truncate" not in sys.argv

    if truncate:
        confirm = input("This will TRUNCATE all existing data. Continue? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    print()
    run_stress_test(truncate=truncate)
