"""Grade service for business logic."""

from sqlalchemy.orm import Session
from typing import List, Optional

from src.models.grade import Grade
from src.schemas.grade import GradeCreate, GradeUpdate


def create_grade(db: Session, data: GradeCreate) -> Grade:
    """Create a new grade."""
    obj = Grade(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_grade(db: Session, grade_id: int) -> Optional[Grade]:
    """Get grade by ID."""
    return db.query(Grade).filter(Grade.id == grade_id).first()


def get_student_grades(
    db: Session, student_id: int, skip: int = 0, limit: int = 100
) -> List[Grade]:
    """Get all grades for a student."""
    return db.query(Grade).filter(
        Grade.student_id == student_id
    ).offset(skip).limit(limit).all()


def get_course_grades(
    db: Session, course_id: int, skip: int = 0, limit: int = 100
) -> List[Grade]:
    """Get all grades for a course."""
    return db.query(Grade).filter(
        Grade.course_id == course_id
    ).offset(skip).limit(limit).all()


def get_student_course_grades(
    db: Session, student_id: int, course_id: int
) -> List[Grade]:
    """Get all grades for a student in a specific course."""
    return db.query(Grade).filter(
        Grade.student_id == student_id,
        Grade.course_id == course_id
    ).all()


def list_grades(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = None,
    course_id: Optional[int] = None,
    grade_type: Optional[str] = None
) -> List[Grade]:
    """List grades with pagination and optional filters."""
    query = db.query(Grade)

    if student_id:
        query = query.filter(Grade.student_id == student_id)

    if course_id:
        query = query.filter(Grade.course_id == course_id)

    if grade_type:
        query = query.filter(Grade.grade_type == grade_type)

    return query.offset(skip).limit(limit).all()


def update_grade(
    db: Session, grade_id: int, data: GradeUpdate
) -> Optional[Grade]:
    """Update a grade."""
    obj = get_grade(db, grade_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_grade(db: Session, grade_id: int) -> bool:
    """Delete a grade."""
    obj = get_grade(db, grade_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
