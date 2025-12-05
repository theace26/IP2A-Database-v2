from sqlalchemy.orm import Session
from app.db.session import get_db_session

from .truncate_all import truncate_all_tables

from .seed_instructors import seed_instructors
from .seed_locations import seed_locations
from .seed_students import seed_students
from .seed_cohorts import seed_cohorts
from .seed_tools_issued import seed_tools_issued
from .seed_credentials import seed_credentials
from .seed_jatc_applications import seed_jatc_applications


def run():
    db: Session = get_db_session()

    print("🔄 Resetting database...")
    truncate_all_tables(db)

    print("🔄 Starting full database seed...")

    seed_instructors(db)
    seed_locations(db)
    seed_students(db)
    seed_cohorts(db)
    seed_tools_issued(db)
    seed_credentials(db)
    seed_jatc_applications(db)

    print("✅ Database seeding complete.")


if __name__ == "__main__":
    run()
