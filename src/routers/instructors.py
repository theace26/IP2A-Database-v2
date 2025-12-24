from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.schemas.instructor import (
    InstructorCreate,
    InstructorUpdate,
    InstructorRead,
)
from src.services.instructor_service import (
    create_instructor,
    get_instructor,
    list_instructors,
    update_instructor,
    delete_instructor,
)

router = APIRouter(prefix="/instructors", tags=["Instructors"])

@router.post("/", response_model=InstructorRead)
def create(data: InstructorCreate, db: Session = Depends(get_db)):
    return create_instructor(db, data)

@router.get("/{instructor_id}", response_model=InstructorRead)
def read(instructor_id: int, db: Session = Depends(get_db)):
    obj = get_instructor(db, instructor_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Instructor not found")
    return obj

@router.get("/", response_model=list[InstructorRead])
def list_all(db: Session = Depends(get_db)):
    return list_instructors(db)

@router.put("/{instructor_id}", response_model=InstructorRead)
def update(instructor_id: int, data: InstructorUpdate, db: Session = Depends(get_db)):
    return update_instructor(db, instructor_id, data)

@router.delete("/{instructor_id}")
def delete(instructor_id: int, db: Session = Depends(get_db)):
    delete_instructor(db, instructor_id)
    return {"message": "Instructor deleted"}
