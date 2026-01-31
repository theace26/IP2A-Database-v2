"""Courses router for API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.db.session import get_db
from src.schemas.course import CourseCreate, CourseUpdate, CourseRead
from src.services.course_service import (
    create_course,
    get_course,
    get_course_by_code,
    list_courses,
    update_course,
    delete_course,
)

router = APIRouter(prefix="/training/courses", tags=["Training - Courses"])


@router.post("/", response_model=CourseRead, status_code=201)
def create(data: CourseCreate, db: Session = Depends(get_db)):
    """Create a new course."""
    return create_course(db, data)


@router.get("/{course_id}", response_model=CourseRead)
def read(course_id: int, db: Session = Depends(get_db)):
    """Get a course by ID."""
    obj = get_course(db, course_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Course not found")
    return obj


@router.get("/by-code/{code}", response_model=CourseRead)
def read_by_code(code: str, db: Session = Depends(get_db)):
    """Get a course by course code."""
    obj = get_course_by_code(db, code)
    if not obj:
        raise HTTPException(status_code=404, detail="Course not found")
    return obj


@router.get("/", response_model=List[CourseRead])
def list_all(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = Query(None),
    course_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List all courses with optional filters."""
    return list_courses(db, skip, limit, is_active, course_type)


@router.patch("/{course_id}", response_model=CourseRead)
def update(course_id: int, data: CourseUpdate, db: Session = Depends(get_db)):
    """Update a course."""
    obj = update_course(db, course_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Course not found")
    return obj


@router.delete("/{course_id}")
def delete(course_id: int, db: Session = Depends(get_db)):
    """Soft delete a course."""
    if not delete_course(db, course_id):
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course deleted"}
