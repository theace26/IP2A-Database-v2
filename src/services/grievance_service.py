"""Grievance service for business logic."""

from sqlalchemy.orm import Session
from typing import List, Optional

from src.models.grievance import Grievance, GrievanceStepRecord
from src.schemas.grievance import (
    GrievanceCreate,
    GrievanceUpdate,
    GrievanceStepRecordCreate,
    GrievanceStepRecordUpdate,
)


# --- Grievance CRUD ---


def create_grievance(db: Session, data: GrievanceCreate) -> Grievance:
    """Create a new grievance."""
    obj = Grievance(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_grievance(db: Session, grievance_id: int) -> Optional[Grievance]:
    """Get grievance by ID."""
    return db.query(Grievance).filter(Grievance.id == grievance_id).first()


def get_grievance_by_number(db: Session, grievance_number: str) -> Optional[Grievance]:
    """Get grievance by grievance number."""
    return (
        db.query(Grievance)
        .filter(Grievance.grievance_number == grievance_number)
        .first()
    )


def list_grievances(db: Session, skip: int = 0, limit: int = 100) -> List[Grievance]:
    """List grievances with pagination."""
    return db.query(Grievance).offset(skip).limit(limit).all()


def update_grievance(
    db: Session, grievance_id: int, data: GrievanceUpdate
) -> Optional[Grievance]:
    """Update a grievance."""
    obj = get_grievance(db, grievance_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_grievance(db: Session, grievance_id: int) -> bool:
    """Delete a grievance."""
    obj = get_grievance(db, grievance_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


# --- Grievance Step Record CRUD ---


def create_step_record(db: Session, data: GrievanceStepRecordCreate) -> GrievanceStepRecord:
    """Create a new grievance step record."""
    obj = GrievanceStepRecord(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_step_record(db: Session, record_id: int) -> Optional[GrievanceStepRecord]:
    """Get grievance step record by ID."""
    return (
        db.query(GrievanceStepRecord)
        .filter(GrievanceStepRecord.id == record_id)
        .first()
    )


def list_step_records(db: Session, grievance_id: int) -> List[GrievanceStepRecord]:
    """List all step records for a grievance."""
    return (
        db.query(GrievanceStepRecord)
        .filter(GrievanceStepRecord.grievance_id == grievance_id)
        .all()
    )


def update_step_record(
    db: Session, record_id: int, data: GrievanceStepRecordUpdate
) -> Optional[GrievanceStepRecord]:
    """Update a grievance step record."""
    obj = get_step_record(db, record_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_step_record(db: Session, record_id: int) -> bool:
    """Delete a grievance step record."""
    obj = get_step_record(db, record_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
