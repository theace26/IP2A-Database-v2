from sqlalchemy.orm import Session
from sqlalchemy import text


def truncate_all_tables(db: Session):
    """
    Truncate all tables in dependency-safe order.
    """

    tables = [
        "instructor_hours",
        "instructor_cohort",
        "tools_issued",
        "credentials",
        "jatc_applications",
        "students",
        "cohorts",
        "instructors",
        "locations",
    ]

    for table in tables:
        db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))

    db.commit()
