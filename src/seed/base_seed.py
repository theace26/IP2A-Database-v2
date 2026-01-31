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


def add_records(db: Session, records: list, batch_size: int = None):
    """
    Bulk add records with proper session handling.

    Args:
        db: Database session
        records: List of model instances to add
        batch_size: If provided, commit in batches for better performance with large datasets
    """
    if batch_size is None or len(records) <= batch_size:
        # Add all at once for small datasets
        for record in records:
            db.add(record)
        db.commit()
    else:
        # Add in batches for large datasets
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            for record in batch:
                db.add(record)
            db.commit()
            db.flush()  # Clear session between batches
