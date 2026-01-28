"""Class session service for business logic."""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from src.models.class_session import ClassSession
from src.schemas.class_session import ClassSessionCreate, ClassSessionUpdate


def create_class_session(db: Session, data: ClassSessionCreate) -> ClassSession:
    """Create a new class session."""
    obj = ClassSession(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_class_session(db: Session, session_id: int) -> Optional[ClassSession]:
    """Get class session by ID."""
    return db.query(ClassSession).filter(ClassSession.id == session_id).first()


def list_class_sessions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    course_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[ClassSession]:
    """List class sessions with pagination and optional filters."""
    query = db.query(ClassSession)

    if course_id:
        query = query.filter(ClassSession.course_id == course_id)

    if start_date:
        query = query.filter(ClassSession.session_date >= start_date)

    if end_date:
        query = query.filter(ClassSession.session_date <= end_date)

    query = query.order_by(ClassSession.session_date.desc())

    return query.offset(skip).limit(limit).all()


def update_class_session(
    db: Session, session_id: int, data: ClassSessionUpdate
) -> Optional[ClassSession]:
    """Update a class session."""
    obj = get_class_session(db, session_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_class_session(db: Session, session_id: int) -> bool:
    """Delete a class session."""
    obj = get_class_session(db, session_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
