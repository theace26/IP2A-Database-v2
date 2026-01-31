"""SALTing activity service for business logic."""

from sqlalchemy.orm import Session
from typing import List, Optional

from src.models.salting_activity import SALTingActivity
from src.schemas.salting_activity import SALTingActivityCreate, SALTingActivityUpdate


def create_salting_activity(db: Session, data: SALTingActivityCreate) -> SALTingActivity:
    """Create a new SALTing activity."""
    obj = SALTingActivity(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_salting_activity(db: Session, activity_id: int) -> Optional[SALTingActivity]:
    """Get SALTing activity by ID."""
    return db.query(SALTingActivity).filter(SALTingActivity.id == activity_id).first()


def list_salting_activities(db: Session, skip: int = 0, limit: int = 100) -> List[SALTingActivity]:
    """List SALTing activities with pagination."""
    return db.query(SALTingActivity).offset(skip).limit(limit).all()


def update_salting_activity(
    db: Session, activity_id: int, data: SALTingActivityUpdate
) -> Optional[SALTingActivity]:
    """Update a SALTing activity."""
    obj = get_salting_activity(db, activity_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_salting_activity(db: Session, activity_id: int) -> bool:
    """Delete a SALTing activity."""
    obj = get_salting_activity(db, activity_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
