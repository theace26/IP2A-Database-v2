"""Seed organization contacts data."""

from sqlalchemy.orm import Session
from faker import Faker

from src.models.organization import Organization
from src.models.organization_contact import OrganizationContact
from .base_seed import add_records

fake = Faker()


def seed_organization_contacts(db: Session, contacts_per_org: int = 2):
    """Seed contacts for organizations (2-3 per org)."""
    organizations = db.query(Organization).all()

    if not organizations:
        print("⚠️  No organizations found. Run seed_organizations first.")
        return []

    contacts = []

    for org in organizations:
        num_contacts = fake.random_int(min=1, max=contacts_per_org + 1)

        for i in range(num_contacts):
            is_primary = i == 0  # First contact is primary

            contact = OrganizationContact(
                organization_id=org.id,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                title=fake.job(),
                phone=fake.phone_number()[:50],
                email=fake.email(),
                is_primary=is_primary,
                notes=fake.sentence() if fake.boolean(chance_of_getting_true=30) else None,
            )
            contacts.append(contact)

    add_records(db, contacts)
    print(f"✅ Seeded {len(contacts)} organization contacts.")
    return contacts
