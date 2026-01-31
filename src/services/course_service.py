"""Course service for business logic."""

from sqlalchemy.orm import Session
from typing import List, Optional

from src.models.course import Course
from src.schemas.course import CourseCreate, CourseUpdate


def create_course(db: Session, data: CourseCreate) -> Course:
    """Create a new course."""
    obj = Course(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_course(db: Session, course_id: int) -> Optional[Course]:
    """Get course by ID."""
    return db.query(Course).filter(Course.id == course_id).first()


def get_course_by_code(db: Session, code: str) -> Optional[Course]:
    """Get course by course code."""
    return db.query(Course).filter(Course.code == code).first()


def list_courses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    course_type: Optional[str] = None
) -> List[Course]:
    """List courses with pagination and optional filters."""
    query = db.query(Course)

    if is_active is not None:
        query = query.filter(Course.is_active == is_active)

    if course_type:
        query = query.filter(Course.course_type == course_type)

    return query.offset(skip).limit(limit).all()


def update_course(
    db: Session, course_id: int, data: CourseUpdate
) -> Optional[Course]:
    """Update a course."""
    obj = get_course(db, course_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_course(db: Session, course_id: int) -> bool:
    """Soft delete a course."""
    obj = get_course(db, course_id)
    if not obj:
        return False
    obj.soft_delete()
    db.commit()
    return True
