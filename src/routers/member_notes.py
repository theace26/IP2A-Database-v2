"""API endpoints for member notes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.models.user import User
from src.routers.dependencies.auth import get_current_user
from src.schemas.member_note import (
    MemberNoteCreate,
    MemberNoteUpdate,
    MemberNoteRead,
    MemberNoteList,
)
from src.services.member_note_service import member_note_service

router = APIRouter(prefix="/member-notes", tags=["member-notes"])


@router.post("/", response_model=MemberNoteRead, status_code=status.HTTP_201_CREATED)
def create_note(
    data: MemberNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new member note."""
    note = member_note_service.create(db, data, current_user)
    return _note_to_read(note)


@router.get("/member/{member_id}", response_model=MemberNoteList)
def get_notes_for_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all notes for a member (filtered by permission)."""
    notes = member_note_service.get_by_member(db, member_id, current_user)
    return MemberNoteList(
        items=[_note_to_read(n) for n in notes],
        total=len(notes)
    )


@router.get("/{note_id}", response_model=MemberNoteRead)
def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific note by ID."""
    note = member_note_service.get_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Check visibility permission
    visible_levels = member_note_service._get_visible_levels(current_user)
    if note.visibility not in visible_levels and note.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this note")

    return _note_to_read(note)


@router.patch("/{note_id}", response_model=MemberNoteRead)
def update_note(
    note_id: int,
    data: MemberNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a member note."""
    note = member_note_service.update(db, note_id, data, current_user)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return _note_to_read(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft delete a member note."""
    success = member_note_service.soft_delete(db, note_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")


def _note_to_read(note) -> MemberNoteRead:
    """Convert MemberNote model to read schema."""
    return MemberNoteRead(
        id=note.id,
        member_id=note.member_id,
        note_text=note.note_text,
        visibility=note.visibility,
        category=note.category,
        created_by_id=note.created_by_id,
        created_by_name=note.created_by.email if note.created_by else None,
        created_at=note.created_at,
        updated_at=note.updated_at,
        is_deleted=note.is_deleted,
    )
