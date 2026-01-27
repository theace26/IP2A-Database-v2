"""Stress test seed for organization contacts."""

from sqlalchemy.orm import Session
from faker import Faker

from src.models.organization import Organization
from src.models.organization_contact import OrganizationContact
from .base_seed import add_records

fake = Faker()


def stress_test_organization_contacts(db: Session, contacts_per_org: int = 3):
    """Generate 2-4 contacts per organization."""
    organizations = db.query(Organization).all()

    if not organizations:
        print("   ⚠️  No organizations found")
        return []

    contacts = []
    job_titles = [
        "HR Manager",
        "Hiring Manager",
        "Operations Manager",
        "Project Manager",
        "Safety Manager",
        "Site Supervisor",
        "General Manager",
        "Vice President",
        "Director",
        "Coordinator",
    ]

    for org in organizations:
        num_contacts = fake.random_int(min=2, max=contacts_per_org + 1)

        for i in range(num_contacts):
            is_primary = i == 0

            contact = OrganizationContact(
                organization_id=org.id,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                title=fake.random_element(job_titles) if fake.boolean(chance_of_getting_true=85) else None,
                phone=fake.phone_number()[:50] if fake.boolean(chance_of_getting_true=80) else None,
                email=fake.email() if fake.boolean(chance_of_getting_true=75) else None,
                is_primary=is_primary,
                notes=fake.sentence() if fake.boolean(chance_of_getting_true=25) else None,
            )
            contacts.append(contact)

    add_records(db, contacts, batch_size=200)
    print(f"   ✅ Seeded {len(contacts)} organization contacts")
    return contacts
