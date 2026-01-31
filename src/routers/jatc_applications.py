from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.db.session import get_db

from src.schemas.jatc_application import (
    JATCApplicationCreate,
    JATCApplicationUpdate,
    JATCApplicationRead,
)

from src.services import jatc_application_service


router = APIRouter(prefix="/jatc-applications", tags=["JATC Applications"])


# ------------------------------------------------------------
# CREATE
# ------------------------------------------------------------
@router.post("/", response_model=JATCApplicationRead)
def create_jatc_application(data: JATCApplicationCreate, db: Session = Depends(get_db)):
    return jatc_application_service.create_application(db, data)


# ------------------------------------------------------------
# READ (List All)
# ------------------------------------------------------------
@router.get("/", response_model=List[JATCApplicationRead])
def list_jatc_applications(
    skip: int = 0, limit: int = 200, db: Session = Depends(get_db)
):
    return jatc_application_service.list_applications(db, skip, limit)


# ------------------------------------------------------------
# READ (Single)
# ------------------------------------------------------------
@router.get("/{application_id}", response_model=JATCApplicationRead)
def get_jatc_application(application_id: int, db: Session = Depends(get_db)):
    app = jatc_application_service.get_application(db, application_id)
    if not app:
        raise HTTPException(status_code=404, detail="JATC application not found")
    return app


# ------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------
@router.patch("/{application_id}", response_model=JATCApplicationRead)
def update_jatc_application(
    application_id: int, data: JATCApplicationUpdate, db: Session = Depends(get_db)
):
    app = jatc_application_service.update_application(db, application_id, data)
    if not app:
        raise HTTPException(status_code=404, detail="JATC application not found")
    return app


# ------------------------------------------------------------
# DELETE
# ------------------------------------------------------------
@router.delete("/{application_id}")
def delete_jatc_application(application_id: int, db: Session = Depends(get_db)):
    success = jatc_application_service.delete_application(db, application_id)
    if not success:
        raise HTTPException(status_code=404, detail="JATC application not found")
    return {"message": "JATC application deleted successfully"}


# ------------------------------------------------------------
# LIST BY STUDENT
# ------------------------------------------------------------
@router.get("/student/{student_id}", response_model=List[JATCApplicationRead])
def list_student_applications(student_id: int, db: Session = Depends(get_db)):
    return jatc_application_service.list_applications_by_student(db, student_id)
