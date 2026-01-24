from sqlalchemy.orm import Session
from faker import Faker

from src.models import Student
from .base_seed import add_records

fake = Faker()


def seed_students(db: Session, count: int = 15):
    students = []

    for _ in range(count):
        students.append(
            Student(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.unique.email(),
                phone=fake.phone_number(),
                birthdate=fake.date_of_birth(minimum_age=17, maximum_age=45),
                address=fake.address(),
            )
        )

    add_records(db, students)
    print(f"Seeded {count} students.")
