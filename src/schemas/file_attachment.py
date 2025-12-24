from pydantic import BaseModel
from datetime import datetime


class FileAttachmentBase(BaseModel):
    record_type: str
    record_id: int
    description: str | None = None


class FileAttachmentCreate(FileAttachmentBase):
    pass  # file is handled separately via UploadFile


class FileAttachmentResponse(FileAttachmentBase):
    id: int
    file_name: str
    file_path: str
    file_type: str
    file_size: int | None
    uploaded_at: datetime

    class Config:
        from_attributes = True
