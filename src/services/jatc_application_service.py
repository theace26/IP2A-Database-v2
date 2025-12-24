from sqlalchemy.orm import Session
from src.models.jatc_application import JATCApplication
from src.schemas.jatc_application import (
    JATCApplicationCreate,
    JATCApplicationUpdate,
)


# ------------------------------------------------------------
# GET
# ------------------------------------------------------------
def get_application(db: Session, application_id: int):
    return db.query(JATCApplication).filter(JATCApplication.id == application_id).first()


def list_applications(db: Session, skip: int = 0, limit: int = 200):
    return db.query(JATCApplication).offset(skip).limit(limit).all()


def list_applications_by_student(db: Session, student_id: int):
    return (
        db.query(JATCApplication)
        .filter(JATCApplication.student_id == student_id)
        .all()
    )


# ------------------------------------------------------------
# CREATE
# ------------------------------------------------------------
def create_application(db: Session, data: JATCApplicationCreate):
    obj = JATCApplication(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------
def update_application(db: Session, application_id: int, data: JATCApplicationUpdate):
    obj = get_application(db, application_id)
    if not obj:
        return None

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)

    db.commit()
    db.refresh(obj)
    return obj


# ------------------------------------------------------------
# DELETE
# ------------------------------------------------------------
def delete_application(db: Session, application_id: int) -> bool:
    obj = get_application(db, application_id)
    if not obj:
        return False

    db.delete(obj)
    db.commit()
    return True
