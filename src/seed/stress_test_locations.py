"""Stress test seed for locations - 200+ locations."""

from sqlalchemy.orm import Session
from faker import Faker

from src.models import Location
from .base_seed import add_records

fake = Faker()


def stress_test_locations(db: Session, count: int = 250):
    """Generate 250 diverse training locations."""
    locations = []

    # Some specific location types
    location_types = [
        "Training Center",
        "Community College",
        "Technical Institute",
        "Union Hall",
        "Workshop Facility",
        "Apprenticeship Center",
        "Skills Lab",
        "Career Center",
    ]

    for i in range(count):
        location_type = fake.random_element(location_types)

        location = Location(
            name=f"{fake.city()} {location_type}",
            address=fake.street_address(),
            city=fake.city(),
            state=fake.state_abbr(),
            postal_code=fake.zipcode(),
            capacity=fake.random_int(min=15, max=80),
        )
        locations.append(location)

    add_records(db, locations, batch_size=100)
    print(f"   ✅ Seeded {len(locations)} locations")
    return locations
