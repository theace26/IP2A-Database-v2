"""Enrollment service for business logic."""

from sqlalchemy.orm import Session
from typing import List, Optional

from src.models.enrollment import Enrollment
from src.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate


def create_enrollment(db: Session, data: EnrollmentCreate) -> Enrollment:
    """Create a new enrollment."""
    obj = Enrollment(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_enrollment(db: Session, enrollment_id: int) -> Optional[Enrollment]:
    """Get enrollment by ID."""
    return db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()


def get_student_enrollments(
    db: Session, student_id: int, skip: int = 0, limit: int = 100
) -> List[Enrollment]:
    """Get all enrollments for a student."""
    return db.query(Enrollment).filter(
        Enrollment.student_id == student_id
    ).offset(skip).limit(limit).all()


def get_course_enrollments(
    db: Session, course_id: int, skip: int = 0, limit: int = 100
) -> List[Enrollment]:
    """Get all enrollments for a course."""
    return db.query(Enrollment).filter(
        Enrollment.course_id == course_id
    ).offset(skip).limit(limit).all()


def list_enrollments(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = None,
    course_id: Optional[int] = None,
    cohort: Optional[str] = None,
    status: Optional[str] = None
) -> List[Enrollment]:
    """List enrollments with pagination and optional filters."""
    query = db.query(Enrollment)

    if student_id:
        query = query.filter(Enrollment.student_id == student_id)

    if course_id:
        query = query.filter(Enrollment.course_id == course_id)

    if cohort:
        query = query.filter(Enrollment.cohort == cohort)

    if status:
        query = query.filter(Enrollment.status == status)

    return query.offset(skip).limit(limit).all()


def update_enrollment(
    db: Session, enrollment_id: int, data: EnrollmentUpdate
) -> Optional[Enrollment]:
    """Update an enrollment."""
    obj = get_enrollment(db, enrollment_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_enrollment(db: Session, enrollment_id: int) -> bool:
    """Delete an enrollment."""
    obj = get_enrollment(db, enrollment_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
