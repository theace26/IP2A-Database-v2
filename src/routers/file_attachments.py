from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from src.database import get_db
from src.schemas.file_attachment import FileAttachmentCreate, FileAttachmentResponse
from src.services.file_attachment_service import (
    create_file_attachment,
    list_files_for_record,
    list_files_by_category,
)
from src.services.file_path_builder import get_valid_categories

router = APIRouter(prefix="/files", tags=["Files & Attachments"])


def _lookup_entity_names(db: Session, record_type: str, record_id: int) -> dict:
    """Look up entity names for building human-readable file paths."""
    if record_type == "member":
        from src.models.member import Member

        member = db.query(Member).filter(Member.id == record_id).first()
        if member:
            return {
                "last_name": member.last_name,
                "first_name": member.first_name,
                "entity_id": member.member_number,
            }
    elif record_type == "student":
        from src.models.student import Student

        student = db.query(Student).filter(Student.id == record_id).first()
        if student:
            return {
                "last_name": student.last_name,
                "first_name": student.first_name,
                "entity_id": f"STU{record_id:04d}",
            }
    elif record_type == "organization":
        from src.models.organization import Organization

        org = db.query(Organization).filter(Organization.id == record_id).first()
        if org:
            return {
                "entity_name": org.name,
                "entity_id": f"ORG{record_id:04d}",
            }
    return {}


@router.post("/", response_model=FileAttachmentResponse)
def upload_attachment(
    record_type: str = Form(...),
    record_id: int = Form(...),
    file_category: str = Form("general"),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a file attachment with organized storage.

    Files are stored in: uploads/{type}s/{Name_ID}/{category}/{year}/{MM-Month}/
    """
    data = FileAttachmentCreate(
        record_type=record_type,
        record_id=record_id,
        file_category=file_category,
        description=description,
    )

    # Look up entity names for human-readable folder names
    names = _lookup_entity_names(db, record_type, record_id)
    entity_id = names.pop("entity_id", record_id)

    return create_file_attachment(db, data, file, entity_id=entity_id, **names)


@router.get("/{record_type}/{record_id}", response_model=list[FileAttachmentResponse])
def list_record_files(record_type: str, record_id: int, db: Session = Depends(get_db)):
    """List all file attachments for a specific record."""
    return list_files_for_record(db, record_type, record_id)


@router.get(
    "/{record_type}/{record_id}/{category}",
    response_model=list[FileAttachmentResponse],
)
def list_record_files_by_category(
    record_type: str,
    record_id: int,
    category: str,
    db: Session = Depends(get_db),
):
    """List file attachments for a record filtered by category."""
    return list_files_by_category(db, record_type, record_id, category)


@router.get("/categories/{record_type}")
def list_categories(record_type: str):
    """List valid file categories for an entity type."""
    return {"record_type": record_type, "categories": get_valid_categories(record_type)}
