"""Stress test seed for member employments - massive scale."""

from sqlalchemy.orm import Session
from faker import Faker
from datetime import timedelta
from decimal import Decimal
import random

from src.models.member_employment import MemberEmployment
from .base_seed import add_records

fake = Faker()


def stress_test_member_employments(
    db: Session,
    members: list,
    employers: list,
    min_jobs: int = 1,
    max_jobs: int = 100,
    employer_repeat_rate: float = 0.20
):
    """
    Generate employment records for members.

    Args:
        members: List of Member objects
        employers: List of Organization objects (employers only)
        min_jobs: Minimum jobs per member (default: 1)
        max_jobs: Maximum jobs per member (default: 100)
        employer_repeat_rate: Chance of returning to previous employer (default: 0.20 = 20%)
    """
    if not members or not employers:
        print("   ⚠️  No members or employers found")
        return []

    employments = []
    job_titles = [
        "Electrician",
        "Apprentice Electrician",
        "Journeyman Electrician",
        "Foreman",
        "General Foreman",
        "Lead Electrician",
        "Senior Electrician",
        "Field Electrician",
        "Maintenance Electrician",
        "Construction Electrician",
        "Industrial Electrician",
    ]

    total_members = len(members)
    estimated_records = sum([random.randint(min_jobs, max_jobs) for _ in range(100)]) * total_members // 100

    print(f"   Generating employment records for {total_members} members...")
    print(f"   Estimated ~{estimated_records:,} employment records...")
    print(f"   This will take several minutes. Progress updates every 1000 members...")

    records_generated = 0

    for member_idx, member in enumerate(members):
        # Each member gets 1-100 jobs (weighted towards fewer jobs)
        # Use triangular distribution weighted towards lower numbers
        num_jobs = int(random.triangular(min_jobs, max_jobs, min_jobs + (max_jobs - min_jobs) * 0.3))

        member_employers = []  # Track employers for this member for repeat rate
        member_job_history = []

        for job_idx in range(num_jobs):
            # 20% chance to work for a previous employer again (if they have history)
            if member_employers and fake.boolean(chance_of_getting_true=int(employer_repeat_rate * 100)):
                employer = random.choice(member_employers)
            else:
                employer = random.choice(employers)
                if employer not in member_employers:
                    member_employers.append(employer)

            # Most recent job is current for active members
            is_current = (job_idx == num_jobs - 1) and fake.boolean(chance_of_getting_true=65)

            # Start date - spread over last 20 years
            start_date = fake.date_between(start_date="-20y", end_date="-1d")

            # End date (if not current)
            end_date = None
            if not is_current:
                # Employment duration: 1 month to 5 years
                days_employed = fake.random_int(min=30, max=1825)
                end_date = start_date + timedelta(days=days_employed)

            # Hourly rate ($18-$75/hr range for electricians at all levels)
            hourly_rate = None
            if fake.boolean(chance_of_getting_true=75):
                base_rate = fake.random_int(min=18, max=75)
                cents = fake.random_int(min=0, max=99)
                hourly_rate = Decimal(f"{base_rate}.{cents:02d}")

            employment = MemberEmployment(
                member_id=member.id,
                organization_id=employer.id,
                start_date=start_date,
                end_date=end_date,
                job_title=fake.random_element(job_titles) if fake.boolean(chance_of_getting_true=90) else None,
                hourly_rate=hourly_rate,
                is_current=is_current,
            )
            member_job_history.append(employment)

        employments.extend(member_job_history)
        records_generated += len(member_job_history)

        # Progress indicator every 1000 members
        if (member_idx + 1) % 1000 == 0:
            print(f"      {member_idx + 1}/{total_members} members processed ({records_generated:,} records generated)...")

    print(f"   Adding {len(employments):,} employment records to database...")
    print(f"   This will take several minutes. Please wait...")

    # Add in large batches for performance
    add_records(db, employments, batch_size=1000)

    print(f"   ✅ Seeded {len(employments):,} member employment records")
    print(f"   Average jobs per member: {len(employments) / len(members):.1f}")
    return employments
