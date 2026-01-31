from sqlalchemy.orm import Session
from faker import Faker

from src.models import Instructor
from .base_seed import add_records

fake = Faker()


def seed_instructors(db: Session, count: int = 5):
    instructors = []

    for _ in range(count):
        instructors.append(
            Instructor(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.unique.email(),
                phone=fake.phone_number(),
                bio=fake.text(),
                certification=fake.job(),
            )
        )

    add_records(db, instructors)
    print(f"Seeded {count} instructors.")
