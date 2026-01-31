"""Benevolence application service for business logic."""

from sqlalchemy.orm import Session
from typing import List, Optional

from src.models.benevolence_application import BenevolenceApplication
from src.schemas.benevolence_application import (
    BenevolenceApplicationCreate,
    BenevolenceApplicationUpdate,
)


def create_benevolence_application(
    db: Session, data: BenevolenceApplicationCreate
) -> BenevolenceApplication:
    """Create a new benevolence application."""
    obj = BenevolenceApplication(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_benevolence_application(
    db: Session, application_id: int
) -> Optional[BenevolenceApplication]:
    """Get benevolence application by ID."""
    return (
        db.query(BenevolenceApplication)
        .filter(BenevolenceApplication.id == application_id)
        .first()
    )


def list_benevolence_applications(
    db: Session, skip: int = 0, limit: int = 100
) -> List[BenevolenceApplication]:
    """List benevolence applications with pagination."""
    return db.query(BenevolenceApplication).offset(skip).limit(limit).all()


def update_benevolence_application(
    db: Session, application_id: int, data: BenevolenceApplicationUpdate
) -> Optional[BenevolenceApplication]:
    """Update a benevolence application."""
    obj = get_benevolence_application(db, application_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_benevolence_application(db: Session, application_id: int) -> bool:
    """Delete a benevolence application."""
    obj = get_benevolence_application(db, application_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
