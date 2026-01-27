"""Stress test seed for organizations - 200 organizations."""

from sqlalchemy.orm import Session
from faker import Faker

from src.models.organization import Organization
from src.db.enums import OrganizationType, SaltingScore
from .base_seed import add_records

fake = Faker()


def stress_test_organizations(db: Session, employers: int = 700, others: int = 50):
    """
    Generate organizations:
    - 700 employers (for employment records) - realistic union local coverage
    - 50 others (unions, training partners, JATCs)
    """
    organizations = []

    # Generate employers
    for _ in range(employers):
        org_data = {
            "name": fake.company(),
            "org_type": OrganizationType.EMPLOYER,
            "address": fake.street_address() if fake.boolean(chance_of_getting_true=80) else None,
            "city": fake.city() if fake.boolean(chance_of_getting_true=85) else None,
            "state": fake.state_abbr() if fake.boolean(chance_of_getting_true=85) else None,
            "zip_code": fake.zipcode() if fake.boolean(chance_of_getting_true=80) else None,
            "phone": fake.phone_number()[:50] if fake.boolean(chance_of_getting_true=75) else None,
            "email": fake.company_email() if fake.boolean(chance_of_getting_true=60) else None,
            "website": fake.url() if fake.boolean(chance_of_getting_true=50) else None,
        }

        # 70% of employers get salting data
        if fake.boolean(chance_of_getting_true=70):
            org_data["salting_score"] = fake.random_element(list(SaltingScore))
            org_data["salting_notes"] = fake.sentence() if fake.boolean(chance_of_getting_true=60) else None

        organizations.append(Organization(**org_data))

    # Generate other organization types
    other_types = [OrganizationType.UNION, OrganizationType.TRAINING_PARTNER, OrganizationType.JATC]

    for _ in range(others):
        org_type = fake.random_element(other_types)

        org_data = {
            "name": fake.company(),
            "org_type": org_type,
            "address": fake.street_address() if fake.boolean(chance_of_getting_true=75) else None,
            "city": fake.city() if fake.boolean(chance_of_getting_true=80) else None,
            "state": fake.state_abbr() if fake.boolean(chance_of_getting_true=80) else None,
            "zip_code": fake.zipcode() if fake.boolean(chance_of_getting_true=75) else None,
            "phone": fake.phone_number()[:50] if fake.boolean(chance_of_getting_true=70) else None,
            "email": fake.company_email() if fake.boolean(chance_of_getting_true=55) else None,
            "website": fake.url() if fake.boolean(chance_of_getting_true=45) else None,
        }

        organizations.append(Organization(**org_data))

    add_records(db, organizations, batch_size=100)
    print(f"   ✅ Seeded {len(organizations)} organizations ({employers} employers)")

    # Return only employers for employment seeding
    return organizations[:employers]
