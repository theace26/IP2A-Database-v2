"""Document schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""

    id: int
    filename: str
    original_filename: str
    content_type: str
    size: int
    s3_key: str
    record_type: str
    record_id: int
    category: Optional[str] = None
    uploaded_at: datetime
    download_url: Optional[str] = None


class DocumentRead(BaseModel):
    """Schema for reading a document record."""

    id: int
    filename: str
    original_filename: str
    content_type: str
    size: int
    s3_key: str
    record_type: str
    record_id: int
    category: Optional[str] = None
    uploaded_by: Optional[str] = None
    uploaded_at: datetime
    is_deleted: bool = False

    class Config:
        from_attributes = True


class DocumentDownloadResponse(BaseModel):
    """Response with presigned download URL."""

    id: int
    filename: str
    content_type: str
    size: int
    download_url: str
    expires_in: int = Field(default=3600, description="URL expiry in seconds")


class PresignedUploadRequest(BaseModel):
    """Request for getting a presigned upload URL."""

    filename: str = Field(..., max_length=255)
    content_type: str = Field(..., max_length=100)
    record_type: str = Field(..., max_length=50, description="e.g., member, grievance")
    record_id: int
    category: Optional[str] = Field(None, max_length=50)


class PresignedUploadResponse(BaseModel):
    """Response with presigned upload URL."""

    upload_url: str
    s3_key: str
    expires_in: int = Field(default=3600)
    fields: Optional[dict] = None  # For POST-based uploads


class DocumentListResponse(BaseModel):
    """Response for listing documents."""

    documents: list[DocumentRead]
    total: int
    page: int = 1
    page_size: int = 50
