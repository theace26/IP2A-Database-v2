from sqlalchemy.orm import Session
from src.models.credential import Credential
from src.schemas.credential import CredentialCreate, CredentialUpdate

# ------------------------------------------------------------
# GET
# ------------------------------------------------------------
def get_credential(db: Session, credential_id: int) -> Credential | None:
    return db.query(Credential).filter(Credential.id == credential_id).first()

def list_credentials(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Credential).offset(skip).limit(limit).all()

def list_credentials_by_student(db: Session, student_id: int):
    return db.query(Credential).filter(Credential.student_id == student_id).all()

# ------------------------------------------------------------
# CREATE
# ------------------------------------------------------------
def create_credential(db: Session, data: CredentialCreate) -> Credential:
    obj = Credential(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

# ------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------
def update_credential(db: Session, credential_id: int, data: CredentialUpdate):
    obj = get_credential(db, credential_id)
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
def delete_credential(db: Session, credential_id: int) -> bool:
    obj = get_credential(db, credential_id)
    if not obj:
        return False

    db.delete(obj)
    db.commit()
    return True
