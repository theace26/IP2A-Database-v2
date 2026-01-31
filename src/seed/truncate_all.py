from sqlalchemy.orm import Session
from sqlalchemy import text


def truncate_all_tables(db: Session):
    """
    Truncate all tables in dependency-safe order.
    Uses CASCADE to handle foreign key constraints.
    Handles missing tables gracefully using savepoints.
    """

    # Order matters - child tables first, then parent tables
    tables = [
        # Dues system
        "dues_adjustments",
        "dues_payments",
        "dues_periods",
        "dues_rates",
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
            # Use savepoint so one failure doesn't abort entire transaction
            db.execute(text("SAVEPOINT truncate_savepoint"))
            db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
            db.execute(text("RELEASE SAVEPOINT truncate_savepoint"))
            print(f"  Truncated: {table}")
        except Exception as e:
            # Rollback to savepoint and continue
            db.execute(text("ROLLBACK TO SAVEPOINT truncate_savepoint"))
            error_msg = str(e).split('\n')[0][:60]
            print(f"  Skipped {table}: {error_msg}")

    db.commit()
    print("All tables truncated.")
