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
from .base_seed import init_seed


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

    seed_instructors(db, count=50)
    seed_locations(db)
    seed_students(db, count=500)
    seed_cohorts(db, count=10)
    seed_tools_issued(db)
    seed_credentials(db)
    seed_jatc_applications(db)

    print("✅ Database seeding complete.")


if __name__ == "__main__":
    run()
