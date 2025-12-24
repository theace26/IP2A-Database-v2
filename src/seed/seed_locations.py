from sqlalchemy.orm import Session
from faker import Faker

from src.models import Location
from .base_seed import add_records

fake = Faker()

def seed_locations(db: Session, count: int = 4):
    locations = []

    for _ in range(count):
        locations.append(
            Location(
                name=f"{fake.city()} Training Center",
                address=fake.address(),
                capacity=fake.random_int(20, 60)
            )
        )

    add_records(db, locations)
    print(f"Seeded {count} locations.")
