from sqlalchemy.orm import Session
from sqlalchemy import text


def truncate_all_tables(db: Session):
    """
    Truncate all tables in dependency-safe order.
    Uses CASCADE to handle foreign key constraints.
    """

    # Order matters - child tables first, then parent tables
    tables = [
        # Dues system
        "dues_adjustments",
        "dues_payments",
        "dues_periods",
        "dues_rates",
        # Documents
        "documents",
        # Training system
        "certifications",
        "grades",
        "attendances",
        "enrollments",
        "class_sessions",
        "courses",
        # Union operations
        "grievances",
        "benevolence_reviews",
        "benevolence_applications",
        "salting_activities",
        # Original training
        "instructor_hours",
        "instructor_cohort",
        "tools_issued",
        "credentials",
        "jatc_applications",
        "students",
        "cohorts",
        "instructors",
        # Members and organizations
        "member_employments",
        "members",
        "organization_contacts",
        "organizations",
        # Auth (keep roles, clear users except system)
        "user_roles",
        "users",
        "roles",
        # Audit
        "audit_logs",
        # Locations last
        "locations",
    ]

    print("Truncating all tables...")
    for table in tables:
        try:
            db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
            print(f"  Truncated: {table}")
        except Exception as e:
            print(f"  Skipped {table}: {e}")

    db.commit()
    print("All tables truncated.")
