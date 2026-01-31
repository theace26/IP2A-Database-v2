"""Class sessions router for API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from src.db.session import get_db
from src.schemas.class_session import ClassSessionCreate, ClassSessionUpdate, ClassSessionRead
from src.services.class_session_service import (
    create_class_session,
    get_class_session,
    list_class_sessions,
    update_class_session,
    delete_class_session,
)

router = APIRouter(prefix="/training/class-sessions", tags=["Training - Class Sessions"])


@router.post("/", response_model=ClassSessionRead, status_code=201)
def create(data: ClassSessionCreate, db: Session = Depends(get_db)):
    """Create a new class session."""
    return create_class_session(db, data)


@router.get("/{session_id}", response_model=ClassSessionRead)
def read(session_id: int, db: Session = Depends(get_db)):
    """Get a class session by ID."""
    obj = get_class_session(db, session_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Class session not found")
    return obj


@router.get("/", response_model=List[ClassSessionRead])
def list_all(
    skip: int = 0,
    limit: int = 100,
    course_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """List all class sessions with optional filters."""
    return list_class_sessions(db, skip, limit, course_id, start_date, end_date)


@router.patch("/{session_id}", response_model=ClassSessionRead)
def update(session_id: int, data: ClassSessionUpdate, db: Session = Depends(get_db)):
    """Update a class session."""
    obj = update_class_session(db, session_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Class session not found")
    return obj


@router.delete("/{session_id}")
def delete(session_id: int, db: Session = Depends(get_db)):
    """Delete a class session."""
    if not delete_class_session(db, session_id):
        raise HTTPException(status_code=404, detail="Class session not found")
    return {"message": "Class session deleted"}
