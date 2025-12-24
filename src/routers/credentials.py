from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.db.session import get_db
from src.schemas.credential import (
    CredentialCreate,
    CredentialUpdate,
    CredentialRead,
)

from src.services import credential_service


router = APIRouter(
    prefix="/credentials",
    tags=["Credentials"]
)


# ------------------------------------------------------------
# CREATE
# ------------------------------------------------------------
@router.post("/", response_model=CredentialRead)
def create_credential(
    data: CredentialCreate,
    db: Session = Depends(get_db)
):
    return credential_service.create_credential(db, data)


# ------------------------------------------------------------
# READ (List All)
# ------------------------------------------------------------
@router.get("/", response_model=List[CredentialRead])
def list_credentials(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return credential_service.list_credentials(db, skip, limit)


# ------------------------------------------------------------
# READ (Single)
# ------------------------------------------------------------
@router.get("/{credential_id}", response_model=CredentialRead)
def get_credential(
    credential_id: int,
    db: Session = Depends(get_db)
):
    cred = credential_service.get_credential(db, credential_id)
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    return cred


# ------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------
@router.patch("/{credential_id}", response_model=CredentialRead)
def update_credential(
    credential_id: int,
    data: CredentialUpdate,
    db: Session = Depends(get_db)
):
    cred = credential_service.update_credential(db, credential_id, data)
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    return cred


# ------------------------------------------------------------
# DELETE
# ------------------------------------------------------------
@router.delete("/{credential_id}")
def delete_credential(
    credential_id: int,
    db: Session = Depends(get_db)
):
    success = credential_service.delete_credential(db, credential_id)
    if not success:
        raise HTTPException(status_code=404, detail="Credential not found")
    return {"message": "Credential deleted successfully"}


# ------------------------------------------------------------
# LIST BY STUDENT
# ------------------------------------------------------------
@router.get("/student/{student_id}", response_model=List[CredentialRead])
def list_credentials_by_student(
    student_id: int,
    db: Session = Depends(get_db)
):
    return credential_service.list_credentials_by_student(db, student_id)
