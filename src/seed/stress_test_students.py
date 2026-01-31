"""Stress test seed for students - 1,000 students."""

from sqlalchemy.orm import Session
from faker import Faker

from src.models import Student
from .base_seed import add_records

fake = Faker()


def stress_test_students(db: Session, count: int = 1000):
    """Generate 1,000 students with complete profile data."""
    students = []

    shirt_sizes = ["XS", "S", "M", "L", "XL", "XXL", "XXXL"]
    shoe_sizes = ["7", "7.5", "8", "8.5", "9", "9.5", "10", "10.5", "11", "11.5", "12", "13", "14"]

    for _ in range(count):
        first_name = fake.first_name()
        last_name = fake.last_name()

        student = Student(
            first_name=first_name,
            last_name=last_name,
            middle_name=fake.first_name() if fake.boolean(chance_of_getting_true=40) else None,
            email=fake.unique.email(),
            phone=fake.phone_number()[:50],
            birthdate=fake.date_of_birth(minimum_age=18, maximum_age=50) if fake.boolean(chance_of_getting_true=85) else None,
            address_line1=fake.street_address() if fake.boolean(chance_of_getting_true=90) else None,
            address_line2=fake.secondary_address() if fake.boolean(chance_of_getting_true=25) else None,
            city=fake.city() if fake.boolean(chance_of_getting_true=90) else None,
            state=fake.state_abbr() if fake.boolean(chance_of_getting_true=90) else None,
            postal_code=fake.zipcode() if fake.boolean(chance_of_getting_true=90) else None,
            shoe_size=fake.random_element(shoe_sizes) if fake.boolean(chance_of_getting_true=70) else None,
            shirt_size=fake.random_element(shirt_sizes) if fake.boolean(chance_of_getting_true=70) else None,
            emergency_contact_name=fake.name() if fake.boolean(chance_of_getting_true=85) else None,
            emergency_contact_phone=fake.phone_number()[:50] if fake.boolean(chance_of_getting_true=85) else None,
            emergency_contact_relation=fake.random_element(["Spouse", "Parent", "Sibling", "Friend", "Partner"]) if fake.boolean(chance_of_getting_true=85) else None,
        )
        students.append(student)

    add_records(db, students, batch_size=100)
    print(f"   ✅ Seeded {len(students)} students")
    return students
