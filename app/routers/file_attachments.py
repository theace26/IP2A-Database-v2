from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.file_attachment import FileAttachmentCreate, FileAttachmentResponse
from app.services.file_attachment_service import create_file_attachment, list_files_for_record

router = APIRouter(prefix="/files", tags=["Files & Attachments"])


@router.post("/", response_model=FileAttachmentResponse)
def upload_attachment(
    record_type: str = Form(...),
    record_id: int = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    data = FileAttachmentCreate(
        record_type=record_type,
        record_id=record_id,
        description=description,
    )
    return create_file_attachment(db, data, file)


@router.get("/{record_type}/{record_id}", response_model=list[FileAttachmentResponse])
def list_record_files(record_type: str, record_id: int, db: Session = Depends(get_db)):
    return list_files_for_record(db, record_type, record_id)
