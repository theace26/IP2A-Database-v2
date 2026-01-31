from sqlalchemy.orm import Session
from typing import List, Optional

from src.models import Cohort, Instructor, Student
from src.schemas.cohort import CohortCreate, CohortUpdate


# ------------------------------------------------------------
# CREATE
# ------------------------------------------------------------
def create_cohort(db: Session, data: CohortCreate) -> Cohort:
    cohort = Cohort(
        name=data.name,
        start_date=data.start_date,
        end_date=data.end_date,
        location_id=data.location_id,
    )
    db.add(cohort)
    db.commit()
    db.refresh(cohort)

    # Attach instructors if provided
    if data.instructor_ids:
        instructors = (
            db.query(Instructor).filter(Instructor.id.in_(data.instructor_ids)).all()
        )
        for instructor in instructors:
            cohort.instructors.append(instructor)

    # Attach students if provided
    if data.student_ids:
        students = db.query(Student).filter(Student.id.in_(data.student_ids)).all()
        for student in students:
            student.cohort_id = cohort.id

    db.commit()
    db.refresh(cohort)
    return cohort


# ------------------------------------------------------------
# READ (Single)
# ------------------------------------------------------------
def get_cohort(db: Session, cohort_id: int) -> Optional[Cohort]:
    return db.query(Cohort).filter(Cohort.id == cohort_id).first()


# ------------------------------------------------------------
# READ (List)
# ------------------------------------------------------------
def list_cohorts(db: Session, skip: int = 0, limit: int = 100) -> List[Cohort]:
    return (
        db.query(Cohort)
        .order_by(Cohort.start_date.desc(), Cohort.name.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------
def update_cohort(db: Session, cohort_id: int, data: CohortUpdate) -> Optional[Cohort]:
    cohort = get_cohort(db, cohort_id)
    if not cohort:
        return None

    update_data = data.model_dump(exclude_unset=True)

    # Update simple fields
    for key, value in update_data.items():
        if key not in ["instructor_ids", "student_ids"]:
            setattr(cohort, key, value)

    # Update instructor assignments
    if "instructor_ids" in update_data:
        cohort.instructors.clear()
        if update_data["instructor_ids"]:
            instructors = (
                db.query(Instructor)
                .filter(Instructor.id.in_(update_data["instructor_ids"]))
                .all()
            )
            cohort.instructors.extend(instructors)

    # Update student assignments
    if "student_ids" in update_data:
        # Remove current cohort assignments
        current_students = (
            db.query(Student).filter(Student.cohort_id == cohort.id).all()
        )
        for student in current_students:
            student.cohort_id = None

        # Assign new students
        if update_data["student_ids"]:
            new_students = (
                db.query(Student)
                .filter(Student.id.in_(update_data["student_ids"]))
                .all()
            )
            for student in new_students:
                student.cohort_id = cohort.id

    db.commit()
    db.refresh(cohort)
    return cohort


# ------------------------------------------------------------
# DELETE
# ------------------------------------------------------------
def delete_cohort(db: Session, cohort_id: int) -> bool:
    cohort = get_cohort(db, cohort_id)
    if not cohort:
        return False

    # Remove students from cohort
    students = db.query(Student).filter(Student.cohort_id == cohort.id).all()
    for student in students:
        student.cohort_id = None

    # Clear instructor links
    cohort.instructors.clear()

    db.delete(cohort)
    db.commit()
    return True


# ------------------------------------------------------------
# RELATIONSHIP HELPERS
# ------------------------------------------------------------
def add_instructor_to_cohort(
    db: Session, cohort_id: int, instructor_id: int
) -> Optional[Cohort]:
    cohort = get_cohort(db, cohort_id)
    instructor = db.query(Instructor).filter(Instructor.id == instructor_id).first()

    if not cohort or not instructor:
        return None

    if instructor not in cohort.instructors:
        cohort.instructors.append(instructor)

    db.commit()
    db.refresh(cohort)
    return cohort


def remove_instructor_from_cohort(
    db: Session, cohort_id: int, instructor_id: int
) -> Optional[Cohort]:
    cohort = get_cohort(db, cohort_id)
    instructor = db.query(Instructor).filter(Instructor.id == instructor_id).first()

    if not cohort or not instructor:
        return None

    if instructor in cohort.instructors:
        cohort.instructors.remove(instructor)

    db.commit()
    db.refresh(cohort)
    return cohort


def add_student_to_cohort(
    db: Session, cohort_id: int, student_id: int
) -> Optional[Cohort]:
    cohort = get_cohort(db, cohort_id)
    student = db.query(Student).filter(Student.id == student_id).first()

    if not cohort or not student:
        return None

    student.cohort_id = cohort.id

    db.commit()
    db.refresh(cohort)
    return cohort


def remove_student_from_cohort(
    db: Session, cohort_id: int, student_id: int
) -> Optional[Cohort]:
    cohort = get_cohort(db, cohort_id)
    student = db.query(Student).filter(Student.id == student_id).first()

    if not cohort or not student:
        return None

    if student.cohort_id == cohort.id:
        student.cohort_id = None

    db.commit()
    db.refresh(cohort)
    return cohort
