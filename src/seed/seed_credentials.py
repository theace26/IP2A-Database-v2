from sqlalchemy.orm import Session
from faker import Faker
import random
from datetime import timedelta

from src.models import Credential, Student
from .base_seed import add_records

fake = Faker()

CREDENTIAL_TYPES = [
    "OSHA 10 General Industry",
    "OSHA 10 Construction",
    "Flagger Certification",
    "First Aid / CPR",
    "Forklift Operator",
    "Aerial Lift Safety",
    "Confined Space Awareness",
    "Basic Electrical Safety",
    "Ladder Safety Training",
]


def seed_credentials(db: Session, count_per_student: int = 2):
    students = db.query(Student).all()

    if not students:
        print("❌ Cannot seed credentials — no students found.")
        return

    credentials = []

    for student in students:
        for _ in range(count_per_student):
            issue_date = fake.date_between(start_date="-10m", end_date="-1m")
            expiration = (
                issue_date + timedelta(days=random.randint(180, 720))
                if random.random() < 0.7
                else None
            )

            credentials.append(
                Credential(
                    student_id=student.id,
                    credential_name=random.choice(CREDENTIAL_TYPES),
                    certificate_number=str(fake.random_number(digits=8)),
                    issue_date=issue_date,
                    expiration_date=expiration,
                    issuing_org=fake.company(),
                    notes=fake.sentence() if random.random() < 0.2 else None,
                )
            )

    add_records(db, credentials)
    print(f"Seeded {len(credentials)} credentials.")
