from sqlalchemy.orm import Session
from faker import Faker
import random
from datetime import timedelta

from app.models import JATCApplication, Student
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

            applied = fake.date_between(start_date="-14m", end_date="-1m")
            status = random.choice(APPLICATION_STATUSES)

            interview_date = (
                applied + timedelta(days=random.randint(7, 45))
                if status in ["interview_scheduled", "awaiting_results", "accepted", "rejected"]
                else None
            )

            applications.append(
                JATCApplication(
                    student_id=student.id,
                    application_date=applied,
                    status=status,
                    interview_date=interview_date,
                    notes=fake.sentence() if random.random() < 0.25 else None,
                )
            )

    add_records(db, applications)
    print(f"Seeded {len(applications)} JATC applications.")
