"""Documents router for file upload and management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List

from src.db.session import get_db
from src.services.document_service import DocumentService
from src.schemas.document import (
    DocumentUploadResponse,
    DocumentRead,
    DocumentDownloadResponse,
    PresignedUploadRequest,
    PresignedUploadResponse,
    DocumentListResponse,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    """Dependency to get DocumentService instance."""
    return DocumentService(db)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    record_type: str = Form(..., description="Type of record (member, grievance, etc.)"),
    record_id: int = Form(..., description="ID of the related record"),
    category: Optional[str] = Form(None, description="Document category"),
    service: DocumentService = Depends(get_document_service),
):
    """
    Upload a document file.

    The file will be stored in S3 and a database record will be created.
    """
    try:
        # Read file content
        content = await file.read()
        size = len(content)

        # Reset file position for upload
        from io import BytesIO
        file_obj = BytesIO(content)

        # Upload document
        attachment = service.upload_document(
            file_data=file_obj,
            filename=file.filename or "unnamed",
            content_type=file.content_type or "application/octet-stream",
            size=size,
            record_type=record_type,
            record_id=record_id,
            category=category,
        )

        if not attachment:
            raise HTTPException(status_code=500, detail="Failed to upload document")

        # Get download URL
        download_url = service.get_download_url(attachment.id)

        return DocumentUploadResponse(
            id=attachment.id,
            filename=attachment.file_name,
            original_filename=attachment.original_name,
            content_type=attachment.file_type,
            size=attachment.file_size,
            s3_key=attachment.file_path,
            record_type=attachment.record_type,
            record_id=attachment.record_id,
            category=attachment.file_category,
            uploaded_at=attachment.created_at,
            download_url=download_url,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/presigned-upload", response_model=PresignedUploadResponse)
def get_presigned_upload_url(
    request: PresignedUploadRequest,
    service: DocumentService = Depends(get_document_service),
):
    """
    Get a presigned URL for direct upload to S3.

    Use this for large files to upload directly to S3 from the client.
    After upload completes, call /documents/confirm-upload to create the record.
    """
    try:
        result = service.get_presigned_upload_url(
            filename=request.filename,
            content_type=request.content_type,
            record_type=request.record_type,
            record_id=request.record_id,
            category=request.category,
        )

        if not result:
            raise HTTPException(status_code=500, detail="Failed to generate upload URL")

        return PresignedUploadResponse(
            upload_url=result["upload_url"],
            s3_key=result["s3_key"],
            expires_in=result["expires_in"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/confirm-upload", response_model=DocumentUploadResponse, status_code=201)
def confirm_upload(
    s3_key: str = Form(...),
    filename: str = Form(...),
    content_type: str = Form(...),
    record_type: str = Form(...),
    record_id: int = Form(...),
    category: Optional[str] = Form(None),
    service: DocumentService = Depends(get_document_service),
):
    """
    Confirm a direct upload and create database record.

    Call this after completing a presigned URL upload.
    """
    try:
        attachment = service.confirm_upload(
            s3_key=s3_key,
            filename=filename,
            content_type=content_type,
            record_type=record_type,
            record_id=record_id,
            category=category,
        )

        if not attachment:
            raise HTTPException(status_code=500, detail="Failed to confirm upload")

        return DocumentUploadResponse(
            id=attachment.id,
            filename=attachment.file_name,
            original_filename=attachment.original_name,
            content_type=attachment.file_type,
            size=attachment.file_size,
            s3_key=attachment.file_path,
            record_type=attachment.record_type,
            record_id=attachment.record_id,
            category=attachment.file_category,
            uploaded_at=attachment.created_at,
        )

    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(
    document_id: int,
    service: DocumentService = Depends(get_document_service),
):
    """Get document metadata by ID."""
    doc = service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentRead(
        id=doc.id,
        filename=doc.file_name,
        original_filename=doc.original_name,
        content_type=doc.file_type,
        size=doc.file_size,
        s3_key=doc.file_path,
        record_type=doc.record_type,
        record_id=doc.record_id,
        category=doc.file_category,
        uploaded_at=doc.created_at,
        is_deleted=doc.is_deleted,
    )


@router.get("/{document_id}/download-url", response_model=DocumentDownloadResponse)
def get_download_url(
    document_id: int,
    expiry: int = Query(3600, ge=60, le=86400, description="URL expiry in seconds"),
    service: DocumentService = Depends(get_document_service),
):
    """Get a presigned download URL for a document."""
    doc = service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    url = service.get_download_url(document_id, expiry=expiry)
    if not url:
        raise HTTPException(status_code=500, detail="Failed to generate download URL")

    return DocumentDownloadResponse(
        id=doc.id,
        filename=doc.original_name,
        content_type=doc.file_type,
        size=doc.file_size,
        download_url=url,
        expires_in=expiry,
    )


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    service: DocumentService = Depends(get_document_service),
):
    """Download document content directly (streaming)."""
    result = service.download_document(document_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")

    content, filename, content_type = result

    return StreamingResponse(
        content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    hard_delete: bool = Query(False, description="If true, also delete from S3"),
    service: DocumentService = Depends(get_document_service),
):
    """Delete a document (soft delete by default)."""
    success = service.delete_document(document_id, soft_delete=not hard_delete)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"message": "Document deleted", "hard_delete": hard_delete}


@router.get("/", response_model=DocumentListResponse)
def list_documents(
    record_type: Optional[str] = Query(None, description="Filter by record type"),
    record_id: Optional[int] = Query(None, description="Filter by record ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: DocumentService = Depends(get_document_service),
):
    """List documents with optional filters."""
    skip = (page - 1) * page_size

    documents = service.list_documents(
        record_type=record_type,
        record_id=record_id,
        category=category,
        skip=skip,
        limit=page_size,
    )

    total = service.count_documents(
        record_type=record_type,
        record_id=record_id,
        category=category,
    )

    return DocumentListResponse(
        documents=[
            DocumentRead(
                id=doc.id,
                filename=doc.file_name,
                original_filename=doc.original_name,
                content_type=doc.file_type,
                size=doc.file_size,
                s3_key=doc.file_path,
                record_type=doc.record_type,
                record_id=doc.record_id,
                category=doc.file_category,
                uploaded_at=doc.created_at,
                is_deleted=doc.is_deleted,
            )
            for doc in documents
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
