from sqlalchemy.orm import Session
from src.models.instructor_hours import InstructorHours
from src.schemas.instructor_hours import InstructorHoursCreate, InstructorHoursUpdate


# ------------------------------------------------------------
# GET
# ------------------------------------------------------------
def get_instructor_hours(db: Session, hours_id: int) -> InstructorHours | None:
    return db.query(InstructorHours).filter(InstructorHours.id == hours_id).first()


def list_instructor_hours(db: Session) -> list[InstructorHours]:
    return db.query(InstructorHours).all()


def list_hours_by_instructor(db: Session, instructor_id: int) -> list[InstructorHours]:
    return (
        db.query(InstructorHours)
        .filter(InstructorHours.instructor_id == instructor_id)
        .all()
    )


def list_hours_by_location(db: Session, location_id: int) -> list[InstructorHours]:
    return (
        db.query(InstructorHours)
        .filter(InstructorHours.location_id == location_id)
        .all()
    )


# ------------------------------------------------------------
# CREATE
# ------------------------------------------------------------
def create_instructor_hours(
    db: Session, data: InstructorHoursCreate
) -> InstructorHours:
    obj = InstructorHours(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------
def update_instructor_hours(
    db: Session, hours_id: int, data: InstructorHoursUpdate
) -> InstructorHours:
    entry = get_instructor_hours(db, hours_id)
    if not entry:
        return None

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(entry, key, value)

    db.commit()
    db.refresh(entry)
    return entry


# ------------------------------------------------------------
# DELETE
# ------------------------------------------------------------
def delete_instructor_hours(db: Session, hours_id: int) -> bool:
    entry = get_instructor_hours(db, hours_id)
    if not entry:
        return False

    db.delete(entry)
    db.commit()
    return True
