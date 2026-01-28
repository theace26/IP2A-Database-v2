"""Grades router for API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.db.session import get_db
from src.schemas.grade import GradeCreate, GradeUpdate, GradeRead
from src.services.grade_service import (
    create_grade,
    get_grade,
    get_student_grades,
    get_course_grades,
    get_student_course_grades,
    list_grades,
    update_grade,
    delete_grade,
)

router = APIRouter(prefix="/training/grades", tags=["Training - Grades"])


@router.post("/", response_model=GradeRead, status_code=201)
def create(data: GradeCreate, db: Session = Depends(get_db)):
    """Create a new grade."""
    return create_grade(db, data)


@router.get("/{grade_id}", response_model=GradeRead)
def read(grade_id: int, db: Session = Depends(get_db)):
    """Get a grade by ID."""
    obj = get_grade(db, grade_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Grade not found")
    return obj


@router.get("/student/{student_id}", response_model=List[GradeRead])
def list_by_student(
    student_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """List all grades for a student."""
    return get_student_grades(db, student_id, skip, limit)


@router.get("/course/{course_id}", response_model=List[GradeRead])
def list_by_course(
    course_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """List all grades for a course."""
    return get_course_grades(db, course_id, skip, limit)


@router.get("/student/{student_id}/course/{course_id}", response_model=List[GradeRead])
def list_by_student_and_course(
    student_id: int, course_id: int, db: Session = Depends(get_db)
):
    """List all grades for a student in a specific course."""
    return get_student_course_grades(db, student_id, course_id)


@router.get("/", response_model=List[GradeRead])
def list_all(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = Query(None),
    course_id: Optional[int] = Query(None),
    grade_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List all grades with optional filters."""
    return list_grades(db, skip, limit, student_id, course_id, grade_type)


@router.patch("/{grade_id}", response_model=GradeRead)
def update(grade_id: int, data: GradeUpdate, db: Session = Depends(get_db)):
    """Update a grade."""
    obj = update_grade(db, grade_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Grade not found")
    return obj


@router.delete("/{grade_id}")
def delete(grade_id: int, db: Session = Depends(get_db)):
    """Delete a grade."""
    if not delete_grade(db, grade_id):
        raise HTTPException(status_code=404, detail="Grade not found")
    return {"message": "Grade deleted"}
