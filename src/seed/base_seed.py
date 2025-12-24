from sqlalchemy.orm import Session
from sqlalchemy import text
import random
from faker import Faker

faker = Faker()


def init_seed(seed: int | None = None):
    """
    Initialize deterministic randomness for all seed operations.
    """
    if seed is not None:
        random.seed(seed)
        faker.seed_instance(seed)


def clear_table(db: Session, table_name: str, cascade: bool = False):
    """
    Truncate a table safely.
    - cascade=False (default): prevents wiping related tables.
    - cascade=True: only used for pure junction/association tables.
    """
    if cascade:
        db.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;"))
    else:
        db.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY;"))
    db.commit()


def add_records(db: Session, records: list):
    """Bulk add records with proper session handling."""
    for record in records:
        db.add(record)
    db.commit()
