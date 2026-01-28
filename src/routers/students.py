"""Students router for API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.db.session import get_db
from src.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentRead,
    StudentReadWithDetails,
)
from src.services.student_service import (
    create_student,
    get_student,
    get_student_by_number,
    get_student_by_member_id,
    list_students,
    update_student,
    delete_student,
    generate_student_number,
    get_student_attendance_rate,
)

router = APIRouter(prefix="/training/students", tags=["Training - Students"])


@router.post("/", response_model=StudentRead, status_code=201)
def create(data: StudentCreate, db: Session = Depends(get_db)):
    """Create a new student."""
    return create_student(db, data)


@router.get("/generate-number", response_model=dict)
def get_next_student_number(db: Session = Depends(get_db)):
    """Generate the next available student number."""
    return {"student_number": generate_student_number(db)}


@router.get("/{student_id}", response_model=StudentRead)
def read(student_id: int, db: Session = Depends(get_db)):
    """Get a student by ID."""
    obj = get_student(db, student_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Student not found")
    return obj


@router.get("/{student_id}/details", response_model=StudentReadWithDetails)
def read_with_details(student_id: int, db: Session = Depends(get_db)):
    """Get a student by ID with enrollment, certification, and attendance details."""
    obj = get_student(db, student_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Student not found")

    # Calculate computed fields
    enrollment_count = len(obj.enrollments)
    certification_count = len(obj.certifications)
    attendance_rate = get_student_attendance_rate(db, student_id)

    # Convert to dict and add computed fields
    student_dict = {
        **obj.__dict__,
        "enrollment_count": enrollment_count,
        "certification_count": certification_count,
        "attendance_rate": attendance_rate,
    }

    return student_dict


@router.get("/by-number/{student_number}", response_model=StudentRead)
def read_by_number(student_number: str, db: Session = Depends(get_db)):
    """Get a student by student number."""
    obj = get_student_by_number(db, student_number)
    if not obj:
        raise HTTPException(status_code=404, detail="Student not found")
    return obj


@router.get("/by-member/{member_id}", response_model=StudentRead)
def read_by_member(member_id: int, db: Session = Depends(get_db)):
    """Get a student by member ID."""
    obj = get_student_by_member_id(db, member_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Student not found")
    return obj


@router.get("/", response_model=List[StudentRead])
def list_all(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None),
    cohort: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List all students with optional filters."""
    return list_students(db, skip, limit, status, cohort)


@router.patch("/{student_id}", response_model=StudentRead)
def update(student_id: int, data: StudentUpdate, db: Session = Depends(get_db)):
    """Update a student."""
    obj = update_student(db, student_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Student not found")
    return obj


@router.delete("/{student_id}")
def delete(student_id: int, db: Session = Depends(get_db)):
    """Soft delete a student."""
    if not delete_student(db, student_id):
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student deleted"}
