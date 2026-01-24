from sqlalchemy.orm import Session
from faker import Faker
import random

from src.models import JATCApplication, Student
from .base_seed import add_records

fake = Faker()

APPLICATION_STATUSES = [
    "submitted",
    "in_review",
    "interview_scheduled",
    "awaiting_results",
    "accepted",
    "rejected",
]


def seed_jatc_applications(db: Session, count_per_student: int = 1):
    students = db.query(Student).all()

    if not students:
        print("❌ Cannot seed JATC applications — no students found.")
        return

    applications = []

    for student in students:
        for _ in range(count_per_student):
            application_date = fake.date_between(start_date="-14m", end_date="-1m")
            status = random.choice(APPLICATION_STATUSES)

            applications.append(
                JATCApplication(
                    student_id=student.id,
                    application_date=application_date,
                    status=status,
                    notes=fake.sentence() if random.random() < 0.25 else None,
                )
            )

    add_records(db, applications)
    print(f"Seeded {len(applications)} JATC applications.")
