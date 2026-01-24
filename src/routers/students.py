from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentRead,
)
from src.services.student_service import (
    create_student,
    get_student,
    list_students,
    update_student,
    delete_student,
)

router = APIRouter(prefix="/students", tags=["Students"])


@router.post("/", response_model=StudentRead)
def create(data: StudentCreate, db: Session = Depends(get_db)):
    return create_student(db, data)


@router.get("/{student_id}", response_model=StudentRead)
def read(student_id: int, db: Session = Depends(get_db)):
    obj = get_student(db, student_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Student not found")
    return obj


@router.get("/", response_model=list[StudentRead])
def list_all(db: Session = Depends(get_db)):
    return list_students(db)


@router.put("/{student_id}", response_model=StudentRead)
def update(student_id: int, data: StudentUpdate, db: Session = Depends(get_db)):
    return update_student(db, student_id, data)


@router.delete("/{student_id}")
def delete(student_id: int, db: Session = Depends(get_db)):
    delete_student(db, student_id)
    return {"message": "Student deleted"}
