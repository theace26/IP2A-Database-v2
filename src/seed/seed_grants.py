"""Seed grants data - funding sources for the IP2A program."""

from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from faker import Faker

from src.models.grant import Grant
from .base_seed import add_records

fake = Faker()


def seed_grants(db: Session, count: int = 10):
    """
    Seed grant records for funding tracking.
    """
    grants = []

    grant_templates = [
        {
            "name": "DOL Apprenticeship Grant",
            "funding_source": "Department of Labor",
            "allowable_categories": ["tools", "supplies", "instruction", "travel"],
            "reporting_frequency": "quarterly",
        },
        {
            "name": "State Workforce Development",
            "funding_source": "Washington State",
            "allowable_categories": ["tools", "supplies", "equipment", "instruction"],
            "reporting_frequency": "monthly",
        },
        {
            "name": "IBEW Education Fund",
            "funding_source": "IBEW International",
            "allowable_categories": ["instruction", "materials", "certifications"],
            "reporting_frequency": "annual",
        },
        {
            "name": "NECA Training Trust",
            "funding_source": "NECA",
            "allowable_categories": ["equipment", "tools", "safety", "instruction"],
            "reporting_frequency": "quarterly",
        },
        {
            "name": "Local 46 Training Fund",
            "funding_source": "IBEW Local 46",
            "allowable_categories": ["tools", "supplies", "travel", "certifications"],
            "reporting_frequency": "monthly",
        },
    ]

    for i in range(count):
        template = grant_templates[i % len(grant_templates)]

        # Vary the dates
        start_date = fake.date_between(start_date="-2y", end_date="-6m")
        end_date = start_date + timedelta(days=fake.random_int(min=365, max=730))

        total_amount = Decimal(fake.random_int(min=50000, max=500000))
        spent_percent = fake.random_int(min=10, max=80) / 100
        spent_amount = total_amount * Decimal(spent_percent)

        grant = Grant(
            name=f"{template['name']} {start_date.year}-{i+1:02d}",
            grant_number=f"GR-{start_date.year}-{fake.random_int(min=1000, max=9999)}",
            funding_source=template["funding_source"],
            total_amount=total_amount,
            spent_amount=spent_amount.quantize(Decimal("0.01")),
            start_date=start_date,
            end_date=end_date,
            allowable_categories=template["allowable_categories"],
            reporting_frequency=template["reporting_frequency"],
            next_report_due=fake.date_between(start_date="today", end_date="+90d"),
            is_active=end_date >= date.today(),
            notes=fake.sentence() if fake.boolean(chance_of_getting_true=30) else None,
        )
        grants.append(grant)

    if grants:
        add_records(db, grants)

    print(f"Seeded {len(grants)} grants.")
    return grants
