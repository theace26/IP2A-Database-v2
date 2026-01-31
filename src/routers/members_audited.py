"""
Members router WITH AUDIT LOGGING - Example Implementation.

This file demonstrates how to integrate comprehensive audit logging
into a router. Copy this pattern to other routers for user-related data.

Key changes from original:
1. Import audit_service and get_audit_context
2. Convert SQLAlchemy objects to dicts for logging
3. Add audit logging after each operation
4. Log READ operations (viewing records)
5. Log BULK_READ operations (listing records)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.db.session import get_db
from src.schemas.member import MemberCreate, MemberUpdate, MemberRead
from src.services.member_service import (
    create_member,
    get_member,
    get_member_by_number,
    list_members,
    update_member,
    delete_member,
)

# Import audit logging
from src.services import audit_service
from src.middleware import get_audit_context

router = APIRouter(prefix="/members", tags=["Members (Audited)"])


def _member_to_dict(member) -> dict:
    """Convert Member SQLAlchemy object to dict for audit logging."""
    return {
        "id": member.id,
        "member_number": member.member_number,
        "first_name": member.first_name,
        "last_name": member.last_name,
        "middle_name": member.middle_name,
        "address": member.address,
        "city": member.city,
        "state": member.state,
        "zip_code": member.zip_code,
        "phone": member.phone,
        "email": member.email,
        "date_of_birth": member.date_of_birth,
        "hire_date": member.hire_date,
        "status": member.status.value if member.status else None,
        "classification": member.classification.value if member.classification else None,
        "student_id": member.student_id,
        "notes": member.notes,
    }


@router.post("/", response_model=MemberRead, status_code=201)
def create(data: MemberCreate, db: Session = Depends(get_db)):
    """Create a new member."""
    # Create member
    member = create_member(db, data)

    # Log CREATE action
    audit_context = get_audit_context()
    audit_service.log_create(
        db=db,
        table_name="members",
        record_id=member.id,
        new_values=_member_to_dict(member),
        **audit_context
    )

    return member


@router.get("/{member_id}", response_model=MemberRead)
def read(member_id: int, db: Session = Depends(get_db)):
    """Get a member by ID."""
    member = get_member(db, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Log READ action
    audit_context = get_audit_context()
    audit_service.log_read(
        db=db,
        table_name="members",
        record_id=member.id,
        record_data=_member_to_dict(member),
        **audit_context
    )

    return member


@router.get("/by-number/{member_number}", response_model=MemberRead)
def read_by_number(member_number: str, db: Session = Depends(get_db)):
    """Get a member by member number."""
    member = get_member_by_number(db, member_number)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Log READ action
    audit_context = get_audit_context()
    audit_service.log_read(
        db=db,
        table_name="members",
        record_id=member.id,
        record_data=_member_to_dict(member),
        notes=f"Viewed member by number: {member_number}",
        **audit_context
    )

    return member


@router.get("/", response_model=List[MemberRead])
def list_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all members."""
    members = list_members(db, skip, limit)

    # Log BULK_READ action
    audit_context = get_audit_context()
    audit_service.log_bulk_read(
        db=db,
        table_name="members",
        record_count=len(members),
        filters={"skip": skip, "limit": limit},
        **audit_context
    )

    return members


@router.put("/{member_id}", response_model=MemberRead)
def update(member_id: int, data: MemberUpdate, db: Session = Depends(get_db)):
    """Update a member."""
    # Get old state before update
    old_member = get_member(db, member_id)
    if not old_member:
        raise HTTPException(status_code=404, detail="Member not found")
    old_values = _member_to_dict(old_member)

    # Perform update
    updated_member = update_member(db, member_id, data)
    if not updated_member:
        raise HTTPException(status_code=404, detail="Member not found")
    new_values = _member_to_dict(updated_member)

    # Log UPDATE action
    audit_context = get_audit_context()
    audit_service.log_update(
        db=db,
        table_name="members",
        record_id=member_id,
        old_values=old_values,
        new_values=new_values,
        **audit_context
    )

    return updated_member


@router.delete("/{member_id}")
def delete(member_id: int, db: Session = Depends(get_db)):
    """Delete a member (soft delete)."""
    # Get current state before deletion
    member = get_member(db, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    old_values = _member_to_dict(member)

    # Perform deletion
    if not delete_member(db, member_id):
        raise HTTPException(status_code=404, detail="Member not found")

    # Log DELETE action
    audit_context = get_audit_context()
    audit_service.log_delete(
        db=db,
        table_name="members",
        record_id=member_id,
        old_values=old_values,
        **audit_context
    )

    return {"message": "Member deleted"}
