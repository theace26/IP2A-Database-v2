from sqlalchemy.orm import Session
from faker import Faker
import random

from app.models import Cohort, Instructor, Location
from .base_seed import add_records

fake = Faker()

def seed_cohorts(db: Session, count: int = 3):
    instructors = db.query(Instructor).all()
    locations = db.query(Location).all()

    if not instructors or not locations:
        print("❌ Cannot seed cohorts — missing instructors or locations.")
        return

    cohorts = []

    for _ in range(count):
        primary = random.choice(instructors)
        assigned = random.sample(instructors, k=min(3, len(instructors)))

        cohort = Cohort(
            name=f"IP2A Cohort {fake.random_int(100,999)}",
            description=fake.sentence(),
            start_date=fake.date_this_year(),
            end_date=fake.date_this_year(),
            primary_instructor_id=primary.id,
            location_id=random.choice(locations).id,
        )

        cohort.instructors = assigned
        cohorts.append(cohort)

    add_records(db, cohorts)
    print(f"Seeded {count} cohorts.")
