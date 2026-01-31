import os
from datetime import date
from fastapi import UploadFile
from sqlalchemy.orm import Session
from src.models.file_attachment import FileAttachment
from src.services.file_path_builder import build_file_path, sanitize_filename


def resolve_file_path(
    record_type: str,
    record_id: int,
    filename: str,
    file_category: str = "general",
    ref_date: date | None = None,
    last_name: str | None = None,
    first_name: str | None = None,
    entity_name: str | None = None,
    entity_id: str | int | None = None,
) -> str:
    """Build the organized file path using the path builder.

    Args:
        entity_id: Human-readable identifier (e.g. member_number "M7464416").
                   Falls back to record_id if not provided.
    """
    return build_file_path(
        entity_type=record_type,
        entity_id=entity_id or record_id,
        filename=filename,
        category=file_category,
        ref_date=ref_date,
        last_name=last_name,
        first_name=first_name,
        entity_name=entity_name,
    )


def save_uploaded_file(file_path: str, file: UploadFile) -> str:
    """Save the uploaded file to the organized path on disk."""
    folder = os.path.dirname(file_path)
    os.makedirs(folder, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path


def create_file_attachment(
    db: Session,
    data,
    file: UploadFile,
    last_name: str | None = None,
    first_name: str | None = None,
    entity_name: str | None = None,
    entity_id: str | int | None = None,
):
    """Create a file attachment with organized path structure."""
    file_category = getattr(data, "file_category", "general") or "general"

    file_path = resolve_file_path(
        record_type=data.record_type,
        record_id=data.record_id,
        filename=file.filename,
        file_category=file_category,
        last_name=last_name,
        first_name=first_name,
        entity_name=entity_name,
        entity_id=entity_id,
    )

    save_uploaded_file(file_path, file)

    safe_filename = sanitize_filename(file.filename)
    new_file = FileAttachment(
        record_type=data.record_type,
        record_id=data.record_id,
        file_category=file_category,
        file_name=safe_filename,
        original_name=file.filename,
        file_path=file_path,
        file_type=file.content_type,
        file_size=file.file._file.tell(),
        description=data.description,
    )

    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return new_file


def list_files_for_record(db: Session, record_type: str, record_id: int):
    """List all file attachments for a specific record."""
    return (
        db.query(FileAttachment)
        .filter_by(
            record_type=record_type,
            record_id=record_id,
        )
        .all()
    )


def list_files_by_category(db: Session, record_type: str, record_id: int, category: str):
    """List file attachments filtered by category."""
    return (
        db.query(FileAttachment)
        .filter_by(
            record_type=record_type,
            record_id=record_id,
            file_category=category,
        )
        .all()
    )
