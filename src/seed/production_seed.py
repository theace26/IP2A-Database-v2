"""
One-time production database seeding.

This module handles seeding the production database with initial data.
It clears existing data and seeds fresh.

Usage:
    Set RUN_PRODUCTION_SEED=true environment variable
    The startup script will call this module automatically
"""

from sqlalchemy.orm import Session
from src.db.session import get_db_session
from src.config.settings import settings

from .base_seed import init_seed
from .truncate_all import truncate_all_tables
from .seed_instructors import seed_instructors
from .seed_locations import seed_locations
from .seed_students import seed_students
from .seed_cohorts import seed_cohorts
from .seed_tools_issued import seed_tools_issued
from .seed_credentials import seed_credentials
from .seed_jatc_applications import seed_jatc_applications
from .seed_organizations import seed_organizations
from .seed_organization_contacts import seed_organization_contacts
from .seed_members import seed_members
from .seed_member_employments import seed_member_employments
from .phase2_seed import seed_phase2
from .auth_seed import run_auth_seed
from .training_seed import run_training_seed
from .dues_seed import run_dues_seed
from .seed_grants import seed_grants
from .seed_expenses import seed_expenses
from .seed_instructor_hours import seed_instructor_hours


def run_production_seed():
    """
    Run production seed - clears database and seeds fresh data.

    Seed counts:
    - Members: 1000
    - Students: 500
    - Organizations: 100
    - Instructors: 75
    - Grants: 10
    - Expenses: 200
    """
    env = settings.IP2A_ENV.lower()

    print(f"Production seed check - Environment: {env}")

    if env not in ("prod", "production"):
        print("Not in production environment, skipping production seed.")
        return

    db: Session = get_db_session()

    print("=" * 60)
    print("RUNNING PRODUCTION DATABASE SEED")
    print("=" * 60)

    try:
        # Clear all existing data
        print("\n[0/18] Clearing existing data...")
        truncate_all_tables(db)

        init_seed(42)  # Consistent seed for reproducibility

        # Auth seeds FIRST (roles and default admin)
        print("\n[1/18] Seeding authentication (roles, default admin)...")
        auth_results = run_auth_seed(db)
        admin_status = "created" if auth_results['admin_created'] else "already exists"
        print(f"       Created {auth_results['roles_created']} roles, admin user {admin_status}")

        # Locations (needed for other seeds)
        print("\n[2/18] Seeding locations...")
        seed_locations(db)

        # Instructors
        print("\n[3/18] Seeding instructors...")
        seed_instructors(db, count=75)

        # Organizations (employers)
        print("\n[4/18] Seeding organizations...")
        seed_organizations(db, count=100)

        # Organization contacts
        print("\n[5/18] Seeding organization contacts...")
        seed_organization_contacts(db, contacts_per_org=3)

        # Members (increased to 1000)
        print("\n[6/18] Seeding members...")
        seed_members(db, count=1000)

        # Member employments
        print("\n[7/18] Seeding member employments...")
        seed_member_employments(db)

        # Students (increased to 500, linked to members)
        print("\n[8/18] Seeding students...")
        seed_students(db, count=500)

        # Cohorts
        print("\n[9/18] Seeding cohorts...")
        seed_cohorts(db, count=15)

        # Tools issued to students
        print("\n[10/18] Seeding tools issued...")
        seed_tools_issued(db, count_per_student=2)

        # Student credentials
        print("\n[11/18] Seeding credentials...")
        seed_credentials(db, count_per_student=2)

        # JATC applications
        print("\n[12/18] Seeding JATC applications...")
        seed_jatc_applications(db, count_per_student=1)

        # Grants (funding sources)
        print("\n[13/18] Seeding grants...")
        seed_grants(db, count=10)

        # Expenses (linked to grants, students, locations)
        print("\n[14/18] Seeding expenses...")
        seed_expenses(db, count=200)

        # Instructor hours
        print("\n[15/18] Seeding instructor hours...")
        seed_instructor_hours(db, entries_per_instructor=20)

        # Training system data (courses, enrollments, grades)
        print("\n[16/18] Seeding training system...")
        run_training_seed(db, num_students=200)

        # Phase 2 - Union operations (SALTing, Benevolence, Grievances)
        print("\n[17/18] Seeding union operations...")
        seed_phase2(db, verbose=False)

        # Dues system
        print("\n[18/18] Seeding dues system...")
        run_dues_seed(db, verbose=False)

        db.commit()

        print("\n" + "=" * 60)
        print("PRODUCTION SEED COMPLETE")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\nERROR during production seed: {e}")
        raise


if __name__ == "__main__":
    run_production_seed()
