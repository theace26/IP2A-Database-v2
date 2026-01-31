"""Stress test seed - Large scale data for database performance testing."""

from sqlalchemy.orm import Session
from src.db.session import get_db_session
from src.config.settings import settings

from .truncate_all import truncate_all_tables
from .stress_test_instructors import stress_test_instructors
from .stress_test_locations import stress_test_locations
from .stress_test_students import stress_test_students
from .stress_test_members import stress_test_members
from .stress_test_organizations import stress_test_organizations
from .stress_test_organization_contacts import stress_test_organization_contacts
from .stress_test_member_employments import stress_test_member_employments
from .base_seed import init_seed


def run_stress_test(force: bool = False, truncate: bool = True):
    """
    Stress test seed with large data volumes:
    - 10,000 members
    - 1,000 students
    - 500 instructors
    - 250 locations
    - 750 organizations (700 employers)
    - ~250,000 employment records
    - ~150,000 file attachments (12MP photos, PDFs, documents) - ~30 GB
    """
    env = settings.IP2A_ENV.lower()

    print("🚀 Running STRESS TEST database seed")
    print(f"   Environment: {env}")
    print("=" * 60)

    # 🚨 HARD STOP FOR PROD
    if env == "prod" and not force:
        raise RuntimeError(
            "❌ Stress testing is blocked in PROD.\n"
            "If you REALLY intend to do this, run with force=True."
        )

    init_seed(42)  # Consistent seed for reproducibility
    db: Session = get_db_session()

    if truncate and env in ("dev", "test"):
        print("🔄 Resetting database...")
        truncate_all_tables(db)

    print("\n🔄 Starting STRESS TEST seed...")
    print("   This will take several minutes...\n")

    # Phase 1: Base data
    print("📍 Phase 1: Locations and Instructors")
    stress_test_locations(db, count=250)  # 250 locations
    stress_test_instructors(db, count=500)  # 500 instructors

    # Phase 2: Organizations
    print("\n🏢 Phase 2: Organizations")
    employers = stress_test_organizations(
        db, employers=700, others=50
    )  # 750 total orgs

    # Phase 3: Contacts for organizations
    print("\n👤 Phase 3: Organization Contacts")
    stress_test_organization_contacts(db, contacts_per_org=3)

    # Phase 4: Students
    print("\n🎓 Phase 4: Students")
    stress_test_students(db, count=1000)  # 1,000 students

    # Phase 5: Members
    print("\n👷 Phase 5: Members (This will take a while...)")
    members = stress_test_members(db, count=10000)  # 10,000 members

    # Phase 6: Member Employments (1-100 per member, 20% employer repeat)
    print("\n💼 Phase 6: Member Employments (This will take even longer...)")
    stress_test_member_employments(
        db,
        members=members,
        employers=employers,
        min_jobs=1,
        max_jobs=100,
        employer_repeat_rate=0.20,
    )

    # Phase 7: File Attachments (DISABLED - table not in current schema)
    print("\n📎 Phase 7: File Attachments (SKIPPED - table schema pending)")
    print("   ⚠️  file_attachments table not in current migration - skipping for now")
    # stress_test_file_attachments(db)

    print("\n" + "=" * 60)
    print("✅ STRESS TEST database seeding complete!")
    print("\n📊 Summary:")
    print("   • 250 locations")
    print("   • 500 instructors")
    print("   • 750 organizations (700 employers)")
    print("   • ~2,250 organization contacts")
    print("   • 1,000 students")
    print("   • 10,000 members")
    print("   • ~432,000+ employment records")
    print("   • File attachments skipped (table pending migration)")
    print("=" * 60)


if __name__ == "__main__":
    import sys

    truncate = "--no-truncate" not in sys.argv
    run_stress_test(truncate=truncate)
