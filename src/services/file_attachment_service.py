import os
from typing import Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session
from src.models.file_attachment import FileAttachment

UPLOAD_ROOT = "/app/uploads"


def save_uploaded_file(record_type: str, record_id: int, file: UploadFile) -> str:
    folder = f"{UPLOAD_ROOT}/{record_type}/{record_id}"
    os.makedirs(folder, exist_ok=True)

    file_path = f"{folder}/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path


def create_file_attachment(db: Session, data, file: UploadFile):
    file_path = save_uploaded_file(data.record_type, data.record_id, file)

    new_file = FileAttachment(
        record_type=data.record_type,
        record_id=data.record_id,
        file_name=file.filename,
        file_path=file_path,
        file_type=file.content_type,
        file_size=file.file._file.tell(),  # only works after reading
        description=data.description
    )

    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return new_file


def list_files_for_record(db: Session, record_type: str, record_id: int):
    return db.query(FileAttachment).filter_by(
        record_type=record_type,
        record_id=record_id,
    ).all()
