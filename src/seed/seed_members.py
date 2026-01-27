"""Seed members data."""

from sqlalchemy.orm import Session
from faker import Faker
from datetime import date, timedelta

from src.models.member import Member
from src.db.enums import MemberStatus, MemberClassification
from .base_seed import add_records

fake = Faker()


def seed_members(db: Session, count: int = 50):
    """Seed union members."""
    members = []

    classifications = list(MemberClassification)
    statuses = list(MemberStatus)

    for i in range(count):
        # Generate member number (alphanumeric like 7464416, a22555555, d5555555)
        if i < 10:
            # Some numeric only
            member_number = str(7000000 + fake.random_int(min=100000, max=999999))
        elif i < 20:
            # Some with letter prefix
            member_number = fake.random_letter().lower() + str(fake.random_int(min=1000000, max=9999999))
        else:
            # Mix
            member_number = str(fake.random_int(min=1000000, max=9999999))

        classification = fake.random_element(classifications)

        # Most members are active
        if fake.boolean(chance_of_getting_true=85):
            status = MemberStatus.ACTIVE
        else:
            status = fake.random_element([s for s in statuses if s != MemberStatus.ACTIVE])

        # Generate hire date (joined union)
        hire_date = None
        if fake.boolean(chance_of_getting_true=80):
            hire_date = fake.date_between(start_date="-10y", end_date="today")

        member_data = {
            "member_number": member_number,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "middle_name": fake.first_name() if fake.boolean(chance_of_getting_true=40) else None,
            "address": fake.street_address() if fake.boolean(chance_of_getting_true=70) else None,
            "city": fake.city() if fake.boolean(chance_of_getting_true=70) else None,
            "state": fake.state_abbr() if fake.boolean(chance_of_getting_true=70) else None,
            "zip_code": fake.zipcode() if fake.boolean(chance_of_getting_true=70) else None,
            "phone": fake.phone_number()[:50] if fake.boolean(chance_of_getting_true=80) else None,
            "email": fake.email() if fake.boolean(chance_of_getting_true=60) else None,
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=70) if fake.boolean(chance_of_getting_true=50) else None,
            "hire_date": hire_date,
            "status": status,
            "classification": classification,
            "notes": fake.sentence() if fake.boolean(chance_of_getting_true=20) else None,
        }

        members.append(Member(**member_data))

    add_records(db, members)
    print(f"✅ Seeded {len(members)} members.")
    return members
