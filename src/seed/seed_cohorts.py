from sqlalchemy.orm import Session
from faker import Faker
import random

from src.models import Cohort, Instructor, Location
from src.models.associations import InstructorCohortAssignment
from src.db.enums import CohortStatus
from .base_seed import add_records

fake = Faker()


def seed_cohorts(db: Session, count: int = 3):
    instructors = db.query(Instructor).all()
    locations = db.query(Location).all()

    if not instructors or not locations:
        print("❌ Cannot seed cohorts — missing instructors or locations.")
        return

    cohorts = []

    for i in range(count):
        start = fake.date_this_year()
        end = fake.date_between(start_date=start, end_date="+6m")

        cohort = Cohort(
            name=f"IP2A Cohort {fake.random_int(100, 999)}",
            code=f"IP2A-{fake.random_int(2024, 2026)}-{i:02d}",
            description=fake.sentence(),
            start_date=start,
            end_date=end,
            status=random.choice(list(CohortStatus)),
            max_students=random.randint(15, 30),
            location_id=random.choice(locations).id,
        )
        cohorts.append(cohort)

    add_records(db, cohorts)
    print(f"Seeded {count} cohorts.")

    # Now assign instructors via Association Object pattern
    all_cohorts = db.query(Cohort).all()
    assignments = []

    for cohort in all_cohorts:
        # Pick 1-3 instructors for this cohort
        assigned_instructors = random.sample(
            instructors, k=min(random.randint(1, 3), len(instructors))
        )

        for idx, instructor in enumerate(assigned_instructors):
            assignment = InstructorCohortAssignment(
                instructor_id=instructor.id,
                cohort_id=cohort.id,
                is_primary=(idx == 0),  # First instructor is primary
            )
            assignments.append(assignment)

    add_records(db, assignments)
    print(f"Seeded {len(assignments)} instructor-cohort assignments.")
