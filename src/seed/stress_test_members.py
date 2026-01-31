"""Stress test seed for members - 10,000 members."""

from sqlalchemy.orm import Session
from faker import Faker
from collections import OrderedDict

from src.models.member import Member
from src.db.enums import MemberStatus, MemberClassification
from .base_seed import add_records

fake = Faker()


def stress_test_members(db: Session, count: int = 10000):
    """Generate 10,000 union members with complete data."""
    members = []

    classifications = list(MemberClassification)
    statuses = list(MemberStatus)

    print(f"   Generating {count} members (this may take a minute)...")

    for i in range(count):
        # Generate diverse member numbers (using i to ensure uniqueness)
        if i < 1000:
            # Pure numeric - use i + base to ensure uniqueness
            member_number = str(7000000 + i)
        elif i < 2000:
            # Letter prefix
            member_number = fake.random_letter().lower() + str(8000000 + (i - 1000))
        elif i < 3000:
            # Letter suffix
            member_number = str(9000000 + (i - 2000)) + fake.random_letter().lower()
        else:
            # 10 million range for remaining 7000 members
            member_number = str(10000000 + (i - 3000))

        # Weight classification towards journeyman and apprentices
        classification_weights = OrderedDict(
            [
                (MemberClassification.APPRENTICE_1ST_YEAR, 0.10),
                (MemberClassification.APPRENTICE_2ND_YEAR, 0.10),
                (MemberClassification.APPRENTICE_3RD_YEAR, 0.08),
                (MemberClassification.APPRENTICE_4TH_YEAR, 0.07),
                (MemberClassification.APPRENTICE_5TH_YEAR, 0.05),
                (MemberClassification.JOURNEYMAN, 0.40),
                (MemberClassification.FOREMAN, 0.12),
                (MemberClassification.RETIREE, 0.05),
                (MemberClassification.HONORARY, 0.03),
            ]
        )
        classification = fake.random_choices(elements=classification_weights, length=1)[
            0
        ]

        # Most members are active
        if fake.boolean(chance_of_getting_true=88):
            status = MemberStatus.ACTIVE
        else:
            status = fake.random_element(
                [s for s in statuses if s != MemberStatus.ACTIVE]
            )

        # Generate hire date (when joined union)
        hire_date = None
        if fake.boolean(chance_of_getting_true=85):
            hire_date = fake.date_between(start_date="-20y", end_date="today")

        # Date of birth
        date_of_birth = None
        if fake.boolean(chance_of_getting_true=75):
            date_of_birth = fake.date_of_birth(minimum_age=18, maximum_age=75)

        member_data = {
            "member_number": member_number,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "middle_name": fake.first_name()
            if fake.boolean(chance_of_getting_true=45)
            else None,
            "address": fake.street_address()
            if fake.boolean(chance_of_getting_true=80)
            else None,
            "city": fake.city() if fake.boolean(chance_of_getting_true=82) else None,
            "state": fake.state_abbr()
            if fake.boolean(chance_of_getting_true=82)
            else None,
            "zip_code": fake.zipcode()
            if fake.boolean(chance_of_getting_true=78)
            else None,
            "phone": fake.phone_number()[:50]
            if fake.boolean(chance_of_getting_true=85)
            else None,
            "email": fake.email() if fake.boolean(chance_of_getting_true=65) else None,
            "date_of_birth": date_of_birth,
            "hire_date": hire_date,
            "status": status,
            "classification": classification,
            "notes": fake.sentence()
            if fake.boolean(chance_of_getting_true=15)
            else None,
        }

        members.append(Member(**member_data))

        # Progress indicator every 1000 members
        if (i + 1) % 1000 == 0:
            print(f"      {i + 1}/{count} members generated...")

    print("   Adding members to database (this will take a moment)...")
    add_records(db, members, batch_size=500)
    print(f"   ✅ Seeded {len(members)} members")
    return members
