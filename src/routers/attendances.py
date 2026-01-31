"""Attendances router for API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.db.session import get_db
from src.schemas.attendance import AttendanceCreate, AttendanceUpdate, AttendanceRead
from src.services.attendance_service import (
    create_attendance,
    get_attendance,
    get_student_attendance,
    get_session_attendance,
    list_attendances,
    update_attendance,
    delete_attendance,
)

router = APIRouter(prefix="/training/attendances", tags=["Training - Attendances"])


@router.post("/", response_model=AttendanceRead, status_code=201)
def create(data: AttendanceCreate, db: Session = Depends(get_db)):
    """Create a new attendance record."""
    return create_attendance(db, data)


@router.get("/{attendance_id}", response_model=AttendanceRead)
def read(attendance_id: int, db: Session = Depends(get_db)):
    """Get an attendance record by ID."""
    obj = get_attendance(db, attendance_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return obj


@router.get("/student/{student_id}", response_model=List[AttendanceRead])
def list_by_student(
    student_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """List all attendance records for a student."""
    return get_student_attendance(db, student_id, skip, limit)


@router.get("/session/{session_id}", response_model=List[AttendanceRead])
def list_by_session(
    session_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """List all attendance records for a class session."""
    return get_session_attendance(db, session_id, skip, limit)


@router.get("/", response_model=List[AttendanceRead])
def list_all(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = Query(None),
    class_session_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List all attendance records with optional filters."""
    return list_attendances(db, skip, limit, student_id, class_session_id, status)


@router.patch("/{attendance_id}", response_model=AttendanceRead)
def update(attendance_id: int, data: AttendanceUpdate, db: Session = Depends(get_db)):
    """Update an attendance record."""
    obj = update_attendance(db, attendance_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return obj


@router.delete("/{attendance_id}")
def delete(attendance_id: int, db: Session = Depends(get_db)):
    """Delete an attendance record."""
    if not delete_attendance(db, attendance_id):
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return {"message": "Attendance record deleted"}
