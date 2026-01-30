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


def run_production_seed():
    """
    Run production seed - clears database and seeds fresh data.
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
        print("\n[0/12] Clearing existing data...")
        truncate_all_tables(db)

        init_seed(42)  # Consistent seed for reproducibility

        # Auth seeds FIRST (roles and default admin)
        print("\n[1/12] Seeding authentication (roles, default admin)...")
        auth_results = run_auth_seed(db)
        admin_status = "created" if auth_results['admin_created'] else "already exists"
        print(f"       Created {auth_results['roles_created']} roles, admin user {admin_status}")

        # Locations (needed for other seeds)
        print("\n[2/12] Seeding locations...")
        seed_locations(db)

        # Instructors
        print("\n[3/12] Seeding instructors...")
        seed_instructors(db, count=50)

        # Organizations (employers)
        print("\n[4/12] Seeding organizations...")
        seed_organizations(db, count=50)

        # Organization contacts
        print("\n[5/12] Seeding organization contacts...")
        seed_organization_contacts(db, contacts_per_org=3)

        # Members
        print("\n[6/12] Seeding members...")
        seed_members(db, count=500)

        # Member employments
        print("\n[7/12] Seeding member employments...")
        seed_member_employments(db)

        # Students (linked to members)
        print("\n[8/12] Seeding students...")
        seed_students(db, count=200)

        # Cohorts
        print("\n[9/12] Seeding cohorts...")
        seed_cohorts(db, count=10)

        # Training system data
        print("\n[10/12] Seeding training system...")
        run_training_seed(db, num_students=100)

        # Phase 2 - Union operations (SALTing, Benevolence, Grievances)
        print("\n[11/12] Seeding union operations...")
        seed_phase2(db, verbose=False)

        # Dues system
        print("\n[12/12] Seeding dues system...")
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
