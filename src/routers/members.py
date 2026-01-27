"""Members router for API endpoints."""

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

router = APIRouter(prefix="/members", tags=["Members"])


@router.post("/", response_model=MemberRead, status_code=201)
def create(data: MemberCreate, db: Session = Depends(get_db)):
    """Create a new member."""
    return create_member(db, data)


@router.get("/{member_id}", response_model=MemberRead)
def read(member_id: int, db: Session = Depends(get_db)):
    """Get a member by ID."""
    obj = get_member(db, member_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Member not found")
    return obj


@router.get("/by-number/{member_number}", response_model=MemberRead)
def read_by_number(member_number: str, db: Session = Depends(get_db)):
    """Get a member by member number."""
    obj = get_member_by_number(db, member_number)
    if not obj:
        raise HTTPException(status_code=404, detail="Member not found")
    return obj


@router.get("/", response_model=List[MemberRead])
def list_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all members."""
    return list_members(db, skip, limit)


@router.put("/{member_id}", response_model=MemberRead)
def update(member_id: int, data: MemberUpdate, db: Session = Depends(get_db)):
    """Update a member."""
    obj = update_member(db, member_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Member not found")
    return obj


@router.delete("/{member_id}")
def delete(member_id: int, db: Session = Depends(get_db)):
    """Delete a member."""
    if not delete_member(db, member_id):
        raise HTTPException(status_code=404, detail="Member not found")
    return {"message": "Member deleted"}
