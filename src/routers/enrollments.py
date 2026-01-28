"""Enrollments router for API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.db.session import get_db
from src.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate, EnrollmentRead
from src.services.enrollment_service import (
    create_enrollment,
    get_enrollment,
    get_student_enrollments,
    get_course_enrollments,
    list_enrollments,
    update_enrollment,
    delete_enrollment,
)

router = APIRouter(prefix="/training/enrollments", tags=["Training - Enrollments"])


@router.post("/", response_model=EnrollmentRead, status_code=201)
def create(data: EnrollmentCreate, db: Session = Depends(get_db)):
    """Create a new enrollment."""
    return create_enrollment(db, data)


@router.get("/{enrollment_id}", response_model=EnrollmentRead)
def read(enrollment_id: int, db: Session = Depends(get_db)):
    """Get an enrollment by ID."""
    obj = get_enrollment(db, enrollment_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return obj


@router.get("/student/{student_id}", response_model=List[EnrollmentRead])
def list_by_student(
    student_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """List all enrollments for a student."""
    return get_student_enrollments(db, student_id, skip, limit)


@router.get("/course/{course_id}", response_model=List[EnrollmentRead])
def list_by_course(
    course_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """List all enrollments for a course."""
    return get_course_enrollments(db, course_id, skip, limit)


@router.get("/", response_model=List[EnrollmentRead])
def list_all(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = Query(None),
    course_id: Optional[int] = Query(None),
    cohort: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List all enrollments with optional filters."""
    return list_enrollments(db, skip, limit, student_id, course_id, cohort, status)


@router.patch("/{enrollment_id}", response_model=EnrollmentRead)
def update(enrollment_id: int, data: EnrollmentUpdate, db: Session = Depends(get_db)):
    """Update an enrollment."""
    obj = update_enrollment(db, enrollment_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return obj


@router.delete("/{enrollment_id}")
def delete(enrollment_id: int, db: Session = Depends(get_db)):
    """Delete an enrollment."""
    if not delete_enrollment(db, enrollment_id):
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return {"message": "Enrollment deleted"}
