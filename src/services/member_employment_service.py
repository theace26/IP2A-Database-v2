"""MemberEmployment service for business logic."""

from sqlalchemy.orm import Session
from typing import List, Optional

from src.models.member_employment import MemberEmployment
from src.schemas.member_employment import (
    MemberEmploymentCreate,
    MemberEmploymentUpdate,
)


def create_member_employment(
    db: Session, data: MemberEmploymentCreate
) -> MemberEmployment:
    """Create a new member employment record."""
    obj = MemberEmployment(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_member_employment(
    db: Session, employment_id: int
) -> Optional[MemberEmployment]:
    """Get member employment by ID."""
    return (
        db.query(MemberEmployment)
        .filter(MemberEmployment.id == employment_id)
        .first()
    )


def list_member_employments(
    db: Session, skip: int = 0, limit: int = 100
) -> List[MemberEmployment]:
    """List member employments with pagination."""
    return db.query(MemberEmployment).offset(skip).limit(limit).all()


def list_member_employments_by_member(
    db: Session, member_id: int
) -> List[MemberEmployment]:
    """List all employment records for a specific member."""
    return (
        db.query(MemberEmployment)
        .filter(MemberEmployment.member_id == member_id)
        .all()
    )


def update_member_employment(
    db: Session, employment_id: int, data: MemberEmploymentUpdate
) -> Optional[MemberEmployment]:
    """Update a member employment record."""
    obj = get_member_employment(db, employment_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_member_employment(db: Session, employment_id: int) -> bool:
    """Delete a member employment record."""
    obj = get_member_employment(db, employment_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
