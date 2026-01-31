"""Stress test seed for instructors - 500 instructors."""

from sqlalchemy.orm import Session
from faker import Faker

from src.models import Instructor
from .base_seed import add_records

fake = Faker()


def stress_test_instructors(db: Session, count: int = 500):
    """Generate 500 instructors with complete data."""
    instructors = []

    certifications = [
        "Master Electrician",
        "Journeyman Electrician",
        "Industrial Electrician",
        "Residential Electrician",
        "Commercial Electrician",
        "Electrical Safety Instructor",
        "OSHA Certified Trainer",
        "NFPA 70E Instructor",
        "PLC Specialist",
        "High Voltage Specialist",
    ]

    for _ in range(count):
        instructor = Instructor(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.unique.email(),
            phone=fake.phone_number()[:50],
            bio=fake.paragraph(nb_sentences=3) if fake.boolean(chance_of_getting_true=80) else None,
            certification=fake.random_element(certifications),
        )
        instructors.append(instructor)

    add_records(db, instructors, batch_size=100)
    print(f"   ✅ Seeded {len(instructors)} instructors")
    return instructors
