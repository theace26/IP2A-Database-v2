"""Seed organizations data."""

from sqlalchemy.orm import Session
from faker import Faker

from src.models.organization import Organization
from src.db.enums import OrganizationType, SaltingScore
from .base_seed import add_records

fake = Faker()


def seed_organizations(db: Session, count: int = 20):
    """Seed organizations: employers, unions, training partners, JATCs."""
    organizations = []

    # Seed some specific real-ish organizations
    real_orgs = [
        {
            "name": "IBEW Local 46",
            "org_type": OrganizationType.UNION,
            "city": "Seattle",
            "state": "WA",
            "phone": "206-728-0826",
            "email": "info@ibew46.com",
            "website": "https://www.ibew46.com",
        },
        {
            "name": "Seattle City Light",
            "org_type": OrganizationType.EMPLOYER,
            "city": "Seattle",
            "state": "WA",
            "phone": "206-684-3000",
            "salting_score": SaltingScore.NEUTRAL,
            "salting_notes": "Large municipal utility, pro-union",
        },
        {
            "name": "WECA Training Center",
            "org_type": OrganizationType.TRAINING_PARTNER,
            "city": "Renton",
            "state": "WA",
            "phone": "425-277-8000",
            "email": "info@weca.org",
        },
        {
            "name": "IBEW/NECA Joint Apprenticeship",
            "org_type": OrganizationType.JATC,
            "city": "Seattle",
            "state": "WA",
            "phone": "206-441-5566",
        },
    ]

    for org_data in real_orgs:
        organizations.append(Organization(**org_data))

    # Generate random organizations
    org_types = list(OrganizationType)

    for _ in range(count - len(real_orgs)):
        org_type = fake.random_element(org_types)

        org_data = {
            "name": fake.company(),
            "org_type": org_type,
            "address": fake.street_address(),
            "city": fake.city(),
            "state": fake.state_abbr(),
            "zip_code": fake.zipcode(),
            "phone": fake.phone_number()[:50],
            "email": fake.company_email(),
        }

        # Add salting info for employers
        if org_type == OrganizationType.EMPLOYER:
            if fake.boolean(chance_of_getting_true=60):
                org_data["salting_score"] = fake.random_element(list(SaltingScore))
                org_data["salting_notes"] = fake.sentence()

        organizations.append(Organization(**org_data))

    add_records(db, organizations)
    print(f"✅ Seeded {len(organizations)} organizations.")
    return organizations
