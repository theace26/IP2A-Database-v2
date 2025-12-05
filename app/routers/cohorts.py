from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.cohort import (
    CohortCreate,
    CohortUpdate,
    CohortRead,
)
from app.services.cohort_service import (
    create_cohort,
    get_cohort,
    list_cohorts,
    update_cohort,
    delete_cohort,
)

router = APIRouter(prefix="/cohorts", tags=["Cohorts"])

@router.post("/", response_model=CohortRead)
def create(data: CohortCreate, db: Session = Depends(get_db)):
    return create_cohort(db, data)

@router.get("/{cohort_id}", response_model=CohortRead)
def read(cohort_id: int, db: Session = Depends(get_db)):
    obj = get_cohort(db, cohort_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Cohort not found")
    return obj

@router.get("/", response_model=list[CohortRead])
def list_all(db: Session = Depends(get_db)):
    return list_cohorts(db)

@router.put("/{cohort_id}", response_model=CohortRead)
def update(cohort_id: int, data: CohortUpdate, db: Session = Depends(get_db)):
    return update_cohort(db, cohort_id, data)

@router.delete("/{cohort_id}")
def delete(cohort_id: int, db: Session = Depends(get_db)):
    delete_cohort(db, cohort_id)
    return {"message": "Cohort deleted"}
