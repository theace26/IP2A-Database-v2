"""Seed instructor hours data - tracking teaching time."""

from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from faker import Faker

from src.models.instructor_hours import InstructorHours
from src.models.instructor import Instructor
from src.models.location import Location
from src.models.cohort import Cohort
from .base_seed import add_records

fake = Faker()


def seed_instructor_hours(db: Session, entries_per_instructor: int = 20):
    """
    Seed instructor hours records for payroll tracking.
    """
    instructors = db.query(Instructor).filter(Instructor.deleted_at.is_(None)).all()
    locations = db.query(Location).filter(Location.deleted_at.is_(None)).all()
    cohorts = db.query(Cohort).filter(Cohort.deleted_at.is_(None)).all()

    if not instructors:
        print("No instructors found - skipping instructor hours seeding")
        return []

    hours_entries = []

    for instructor in instructors:
        # Create multiple hour entries per instructor over past months
        for _ in range(entries_per_instructor):
            # Random date in past 6 months
            entry_date = fake.date_between(start_date="-6m", end_date="today")

            # Teaching hours (typical class is 3-4 hours)
            hours = Decimal(fake.random_int(min=2, max=8))
            prep_hours = Decimal(fake.random_int(min=0, max=2))
            total_hours = hours + prep_hours

            # Randomly assign location and cohort
            location = fake.random_element(locations) if locations else None
            cohort = fake.random_element(cohorts) if cohorts and fake.boolean(chance_of_getting_true=70) else None

            # Payment status - older entries more likely to be paid
            days_ago = (date.today() - entry_date).days
            is_paid = days_ago > 30 or fake.boolean(chance_of_getting_true=50)
            paid_date = entry_date + timedelta(days=fake.random_int(min=14, max=30)) if is_paid else None

            entry = InstructorHours(
                instructor_id=instructor.id,
                location_id=location.id if location else None,
                cohort_id=cohort.id if cohort else None,
                date=entry_date,
                hours=hours,
                prep_hours=prep_hours,
                total_hours=total_hours,
                rate_override=None,  # Use instructor's default rate
                is_paid=is_paid,
                paid_date=paid_date,
                notes=fake.sentence() if fake.boolean(chance_of_getting_true=10) else None,
            )
            hours_entries.append(entry)

    if hours_entries:
        add_records(db, hours_entries)

    print(f"Seeded {len(hours_entries)} instructor hour entries.")
    return hours_entries
