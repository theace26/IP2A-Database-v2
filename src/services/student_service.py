from sqlalchemy.orm import Session
from typing import List, Optional

from src.models import Student, Cohort, Credential, ToolsIssued, JATCApplication
from src.schemas.student import StudentCreate, StudentUpdate


# --------------------------------------------------------------------
# CREATE
# --------------------------------------------------------------------
def create_student(db: Session, data: StudentCreate) -> Student:
    student = Student(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.phone,
        birthdate=data.birthdate,
        address=data.address,
        cohort_id=data.cohort_id,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


# --------------------------------------------------------------------
# READ
# --------------------------------------------------------------------
def get_student(db: Session, student_id: int) -> Optional[Student]:
    return db.query(Student).filter(Student.id == student_id).first()


def list_students(db: Session, skip: int = 0, limit: int = 100) -> List[Student]:
    return (
        db.query(Student)
        .order_by(Student.last_name.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# --------------------------------------------------------------------
# UPDATE
# --------------------------------------------------------------------
def update_student(
    db: Session, student_id: int, data: StudentUpdate
) -> Optional[Student]:
    student = get_student(db, student_id)
    if not student:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(student, key, value)

    db.commit()
    db.refresh(student)
    return student


# --------------------------------------------------------------------
# DELETE
# --------------------------------------------------------------------
def delete_student(db: Session, student_id: int) -> bool:
    student = get_student(db, student_id)
    if not student:
        return False

    db.delete(student)
    db.commit()
    return True


# --------------------------------------------------------------------
# RELATIONSHIPS
# --------------------------------------------------------------------
def assign_student_to_cohort(
    db: Session, student_id: int, cohort_id: int
) -> Optional[Student]:
    student = get_student(db, student_id)
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()

    if not student or not cohort:
        return None

    student.cohort_id = cohort_id
    db.commit()
    db.refresh(student)
    return student


def list_student_credentials(db: Session, student_id: int) -> List[Credential]:
    return (
        db.query(Credential)
        .filter(Credential.student_id == student_id)
        .order_by(Credential.issue_date.desc())
        .all()
    )


def list_student_tools(db: Session, student_id: int) -> List[ToolsIssued]:
    return (
        db.query(ToolsIssued)
        .filter(ToolsIssued.student_id == student_id)
        .order_by(ToolsIssued.date_issued.desc())
        .all()
    )


def list_student_jatc_applications(
    db: Session, student_id: int
) -> List[JATCApplication]:
    return (
        db.query(JATCApplication)
        .filter(JATCApplication.student_id == student_id)
        .order_by(JATCApplication.application_date.desc())
        .all()
    )
