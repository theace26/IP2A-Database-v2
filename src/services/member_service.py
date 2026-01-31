"""Member service for business logic."""

from sqlalchemy.orm import Session
from typing import List, Optional

from src.models.member import Member
from src.schemas.member import MemberCreate, MemberUpdate


def create_member(db: Session, data: MemberCreate) -> Member:
    """Create a new member."""
    obj = Member(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_member(db: Session, member_id: int) -> Optional[Member]:
    """Get member by ID."""
    return db.query(Member).filter(Member.id == member_id).first()


def get_member_by_number(db: Session, member_number: str) -> Optional[Member]:
    """Get member by member number."""
    return db.query(Member).filter(Member.member_number == member_number).first()


def list_members(db: Session, skip: int = 0, limit: int = 100) -> List[Member]:
    """List members with pagination."""
    return db.query(Member).offset(skip).limit(limit).all()


def update_member(
    db: Session, member_id: int, data: MemberUpdate
) -> Optional[Member]:
    """Update a member."""
    obj = get_member(db, member_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_member(db: Session, member_id: int) -> bool:
    """Delete a member."""
    obj = get_member(db, member_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
