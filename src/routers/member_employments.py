"""MemberEmployments router for API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.db.session import get_db
from src.schemas.member_employment import (
    MemberEmploymentCreate,
    MemberEmploymentUpdate,
    MemberEmploymentRead,
)
from src.services.member_employment_service import (
    create_member_employment,
    get_member_employment,
    list_member_employments,
    list_member_employments_by_member,
    update_member_employment,
    delete_member_employment,
)

router = APIRouter(prefix="/member-employments", tags=["Member Employments"])


@router.post("/", response_model=MemberEmploymentRead, status_code=201)
def create(data: MemberEmploymentCreate, db: Session = Depends(get_db)):
    """Create a new member employment record."""
    return create_member_employment(db, data)


@router.get("/{employment_id}", response_model=MemberEmploymentRead)
def read(employment_id: int, db: Session = Depends(get_db)):
    """Get a member employment record by ID."""
    obj = get_member_employment(db, employment_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Member employment not found")
    return obj


@router.get("/", response_model=List[MemberEmploymentRead])
def list_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all member employment records."""
    return list_member_employments(db, skip, limit)


@router.get("/by-member/{member_id}", response_model=List[MemberEmploymentRead])
def list_by_member(member_id: int, db: Session = Depends(get_db)):
    """List all employment records for a specific member."""
    return list_member_employments_by_member(db, member_id)


@router.put("/{employment_id}", response_model=MemberEmploymentRead)
def update(
    employment_id: int, data: MemberEmploymentUpdate, db: Session = Depends(get_db)
):
    """Update a member employment record."""
    obj = update_member_employment(db, employment_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Member employment not found")
    return obj


@router.delete("/{employment_id}")
def delete(employment_id: int, db: Session = Depends(get_db)):
    """Delete a member employment record."""
    if not delete_member_employment(db, employment_id):
        raise HTTPException(status_code=404, detail="Member employment not found")
    return {"message": "Member employment deleted"}
