from pydantic import BaseModel
from datetime import datetime


class FileAttachmentBase(BaseModel):
    record_type: str
    record_id: int
    file_category: str = "general"
    description: str | None = None


class FileAttachmentCreate(FileAttachmentBase):
    pass  # file is handled separately via UploadFile


class FileAttachmentResponse(FileAttachmentBase):
    id: int
    file_name: str
    original_name: str | None = None
    file_path: str
    file_type: str
    file_size: int | None
    created_at: datetime

    class Config:
        from_attributes = True
