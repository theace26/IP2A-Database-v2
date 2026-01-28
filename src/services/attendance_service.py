"""Attendance service for business logic."""

from sqlalchemy.orm import Session
from typing import List, Optional

from src.models.attendance import Attendance
from src.schemas.attendance import AttendanceCreate, AttendanceUpdate


def create_attendance(db: Session, data: AttendanceCreate) -> Attendance:
    """Create a new attendance record."""
    obj = Attendance(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_attendance(db: Session, attendance_id: int) -> Optional[Attendance]:
    """Get attendance record by ID."""
    return db.query(Attendance).filter(Attendance.id == attendance_id).first()


def get_student_attendance(
    db: Session, student_id: int, skip: int = 0, limit: int = 100
) -> List[Attendance]:
    """Get all attendance records for a student."""
    return db.query(Attendance).filter(
        Attendance.student_id == student_id
    ).offset(skip).limit(limit).all()


def get_session_attendance(
    db: Session, session_id: int, skip: int = 0, limit: int = 100
) -> List[Attendance]:
    """Get all attendance records for a class session."""
    return db.query(Attendance).filter(
        Attendance.class_session_id == session_id
    ).offset(skip).limit(limit).all()


def list_attendances(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = None,
    class_session_id: Optional[int] = None,
    status: Optional[str] = None
) -> List[Attendance]:
    """List attendance records with pagination and optional filters."""
    query = db.query(Attendance)

    if student_id:
        query = query.filter(Attendance.student_id == student_id)

    if class_session_id:
        query = query.filter(Attendance.class_session_id == class_session_id)

    if status:
        query = query.filter(Attendance.status == status)

    return query.offset(skip).limit(limit).all()


def update_attendance(
    db: Session, attendance_id: int, data: AttendanceUpdate
) -> Optional[Attendance]:
    """Update an attendance record."""
    obj = get_attendance(db, attendance_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_attendance(db: Session, attendance_id: int) -> bool:
    """Delete an attendance record."""
    obj = get_attendance(db, attendance_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
