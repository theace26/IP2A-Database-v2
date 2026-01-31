"""Seed member employment data."""

from sqlalchemy.orm import Session
from faker import Faker
from datetime import timedelta
from decimal import Decimal

from src.models.member import Member
from src.models.organization import Organization
from src.models.member_employment import MemberEmployment
from src.db.enums import OrganizationType
from .base_seed import add_records

fake = Faker()


def seed_member_employments(db: Session):
    """Seed employment records for members at employers."""
    members = db.query(Member).all()
    employers = db.query(Organization).filter(
        Organization.org_type == OrganizationType.EMPLOYER
    ).all()

    if not members:
        print("⚠️  No members found. Run seed_members first.")
        return []

    if not employers:
        print("⚠️  No employers found. Run seed_organizations first.")
        return []

    employments = []

    # Each member gets 1-3 employment records (current and past jobs)
    for member in members:
        num_jobs = fake.random_int(min=1, max=3)

        for i in range(num_jobs):
            employer = fake.random_element(employers)

            # Most recent job is current
            is_current = (i == 0) and fake.boolean(chance_of_getting_true=70)

            # Start date
            start_date = fake.date_between(start_date="-8y", end_date="-1d")

            # End date (if not current)
            end_date = None
            if not is_current:
                # Add 6 months to 3 years to start date
                days_employed = fake.random_int(min=180, max=1095)
                end_date = start_date + timedelta(days=days_employed)

            # Hourly rate (electricians typically earn $25-$60/hr)
            hourly_rate = None
            if fake.boolean(chance_of_getting_true=70):
                hourly_rate = Decimal(str(fake.random_int(min=25, max=60))) + Decimal(str(fake.random_int(min=0, max=99))) / 100

            employment = MemberEmployment(
                member_id=member.id,
                organization_id=employer.id,
                start_date=start_date,
                end_date=end_date,
                job_title=fake.random_element([
                    "Electrician",
                    "Apprentice Electrician",
                    "Journeyman Electrician",
                    "Foreman",
                    "General Foreman",
                    "Lead Electrician",
                ]),
                hourly_rate=hourly_rate,
                is_current=is_current,
            )
            employments.append(employment)

    add_records(db, employments)
    print(f"✅ Seeded {len(employments)} member employment records.")
    return employments
