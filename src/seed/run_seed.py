# src/seed/run_seed.py
from sqlalchemy.orm import Session
from src.db.session import get_db_session
from src.config.settings import settings

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
from .base_seed import init_seed
from .training_seed import run_training_seed
from .dues_seed import run_dues_seed


def run(force: bool = False):
    env = settings.IP2A_ENV.lower()

    print(f"🌱 Running database seed in environment: {env}")

    # 🚨 HARD STOP FOR PROD
    if env == "prod" and not force:
        raise RuntimeError(
            "❌ Seeding is blocked in PROD.\n"
            "If you REALLY intend to do this, run with force=True."
        )

    init_seed(42)
    db: Session = get_db_session()

    if env in ("dev", "test"):
        print("🔄 Resetting database...")
        truncate_all_tables(db)

    print("🔄 Starting full database seed...")

    # Existing seeds
    seed_instructors(db, count=50)
    seed_locations(db)
    seed_students(db, count=500)
    seed_cohorts(db, count=10)
    seed_tools_issued(db)
    seed_credentials(db)
    seed_jatc_applications(db)

    # Auth seeds
    auth_results = run_auth_seed(db)
    print(f"Auth: Created {auth_results['roles_created']} roles")

    # Phase 1 seeds
    seed_organizations(db, count=20)
    seed_organization_contacts(db, contacts_per_org=2)
    seed_members(db, count=50)
    seed_member_employments(db)

    # Phase 2 seeds - Union Operations
    seed_phase2(db, verbose=True)

    # Phase 2 seeds - Training System
    run_training_seed(db, num_students=20)

    # Phase 4 seeds - Dues Tracking
    run_dues_seed(db, verbose=True)

    print("✅ Database seeding complete.")


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    run(force=force)
