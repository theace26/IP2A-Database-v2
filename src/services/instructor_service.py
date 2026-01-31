from sqlalchemy.orm import Session
from typing import List, Optional

from src.models import Instructor, Cohort
from src.schemas.instructor import (
    InstructorCreate,
    InstructorUpdate,
)


# ------------------------------------------------------------
# CREATE
# ------------------------------------------------------------
def create_instructor(db: Session, data: InstructorCreate) -> Instructor:
    instructor = Instructor(
        first_name=data.first_name, last_name=data.last_name, email=data.email
    )
    db.add(instructor)
    db.commit()
    db.refresh(instructor)
    return instructor


# ------------------------------------------------------------
# READ (Single)
# ------------------------------------------------------------
def get_instructor(db: Session, instructor_id: int) -> Optional[Instructor]:
    return db.query(Instructor).filter(Instructor.id == instructor_id).first()


# ------------------------------------------------------------
# READ (List)
# ------------------------------------------------------------
def list_instructors(db: Session, skip: int = 0, limit: int = 100) -> List[Instructor]:
    return (
        db.query(Instructor)
        .order_by(Instructor.last_name.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------
def update_instructor(
    db: Session, instructor_id: int, data: InstructorUpdate
) -> Optional[Instructor]:
    instructor = get_instructor(db, instructor_id)
    if not instructor:
        return None

    # Only update fields that are provided
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(instructor, key, value)

    db.commit()
    db.refresh(instructor)
    return instructor


# ------------------------------------------------------------
# DELETE
# ------------------------------------------------------------
def delete_instructor(db: Session, instructor_id: int) -> bool:
    instructor = get_instructor(db, instructor_id)
    if not instructor:
        return False

    db.delete(instructor)
    db.commit()
    return True


# ------------------------------------------------------------
# RELATIONSHIP HELPERS (optional but powerful)
# ------------------------------------------------------------
def assign_instructor_to_cohort(
    db: Session, instructor_id: int, cohort_id: int
) -> Optional[Instructor]:
    instructor = get_instructor(db, instructor_id)
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()

    if not instructor or not cohort:
        return None

    if cohort not in instructor.cohorts:
        instructor.cohorts.append(cohort)

    db.commit()
    db.refresh(instructor)
    return instructor


def remove_instructor_from_cohort(
    db: Session, instructor_id: int, cohort_id: int
) -> Optional[Instructor]:
    instructor = get_instructor(db, instructor_id)
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()

    if not instructor or not cohort:
        return None

    if cohort in instructor.cohorts:
        instructor.cohorts.remove(cohort)

    db.commit()
    db.refresh(instructor)
    return instructor
