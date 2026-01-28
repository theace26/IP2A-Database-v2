"""Student service for business logic."""

from sqlalchemy.orm import Session
from typing import List, Optional

from src.models.student import Student
from src.models.attendance import Attendance
from src.schemas.student import StudentCreate, StudentUpdate
from src.db.enums import SessionAttendanceStatus


def generate_student_number(db: Session) -> str:
    """Generate a unique student number."""
    # Get the latest student number
    latest = db.query(Student).order_by(Student.id.desc()).first()
    if not latest:
        return "S000001"

    # Extract number and increment
    try:
        current_num = int(latest.student_number[1:])
        next_num = current_num + 1
        return f"S{next_num:06d}"
    except (ValueError, IndexError):
        # If format is unexpected, count total students
        count = db.query(Student).count()
        return f"S{count + 1:06d}"


def get_student_attendance_rate(db: Session, student_id: int) -> float:
    """Calculate attendance rate for a student."""
    total_attendances = (
        db.query(Attendance).filter(Attendance.student_id == student_id).count()
    )

    if total_attendances == 0:
        return 0.0

    present_count = (
        db.query(Attendance)
        .filter(
            Attendance.student_id == student_id,
            Attendance.status.in_(
                [
                    SessionAttendanceStatus.PRESENT,
                    SessionAttendanceStatus.LATE,
                    SessionAttendanceStatus.LEFT_EARLY,
                ]
            ),
        )
        .count()
    )

    return (present_count / total_attendances) * 100


def create_student(db: Session, data: StudentCreate) -> Student:
    """Create a new student."""
    obj = Student(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_student(db: Session, student_id: int) -> Optional[Student]:
    """Get student by ID."""
    return db.query(Student).filter(Student.id == student_id).first()


def get_student_by_number(db: Session, student_number: str) -> Optional[Student]:
    """Get student by student number."""
    return db.query(Student).filter(Student.student_number == student_number).first()


def get_student_by_member_id(db: Session, member_id: int) -> Optional[Student]:
    """Get student by member ID."""
    return db.query(Student).filter(Student.member_id == member_id).first()


def list_students(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    cohort: Optional[str] = None,
) -> List[Student]:
    """List students with pagination and optional filters."""
    query = db.query(Student)

    if status:
        query = query.filter(Student.status == status)

    if cohort:
        query = query.filter(Student.cohort == cohort)

    return query.offset(skip).limit(limit).all()


def update_student(
    db: Session, student_id: int, data: StudentUpdate
) -> Optional[Student]:
    """Update a student."""
    obj = get_student(db, student_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_student(db: Session, student_id: int) -> bool:
    """Soft delete a student."""
    obj = get_student(db, student_id)
    if not obj:
        return False
    obj.soft_delete()
    db.commit()
    return True
