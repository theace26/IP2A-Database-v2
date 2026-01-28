"""Document service for managing file uploads and records."""

import uuid
from datetime import datetime
from typing import Optional, BinaryIO, List
from sqlalchemy.orm import Session

from src.models.file_attachment import FileAttachment
from src.services.s3_service import get_s3_service
from src.services.file_path_builder import build_file_path
from src.config.s3_config import get_s3_settings


class DocumentService:
    """Service for document management operations."""

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self.s3 = get_s3_service()
        self.settings = get_s3_settings()

    def _validate_file(self, filename: str, size: int) -> tuple[bool, str]:
        """
        Validate file extension and size.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check extension
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in self.settings.ALLOWED_EXTENSIONS:
            return False, f"File extension '{ext}' not allowed. Allowed: {self.settings.ALLOWED_EXTENSIONS}"

        # Check size
        max_size = self.settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if size > max_size:
            return False, f"File too large. Maximum size: {self.settings.MAX_FILE_SIZE_MB}MB"

        return True, ""

    def _generate_s3_key(
        self,
        record_type: str,
        record_id: int,
        filename: str,
        category: Optional[str] = None,
    ) -> str:
        """Generate S3 key for a file."""
        # Use the existing file path builder for consistency
        base_path = build_file_path(
            entity_type=record_type,
            entity_name=f"{record_type}_{record_id}",
            entity_id=str(record_id),
            category=category or "general",
            filename=filename,
        )
        # Add unique prefix to prevent collisions
        unique_id = uuid.uuid4().hex[:8]
        return f"{base_path.rsplit('/', 1)[0]}/{unique_id}_{filename}"

    def upload_document(
        self,
        file_data: BinaryIO,
        filename: str,
        content_type: str,
        size: int,
        record_type: str,
        record_id: int,
        category: Optional[str] = None,
        uploaded_by: Optional[str] = None,
    ) -> Optional[FileAttachment]:
        """
        Upload a document to S3 and create a database record.

        Args:
            file_data: File content as file-like object
            filename: Original filename
            content_type: MIME type
            size: File size in bytes
            record_type: Type of record (member, grievance, etc.)
            record_id: ID of the related record
            category: Optional category (grievances, certifications, etc.)
            uploaded_by: User ID who uploaded the file

        Returns:
            FileAttachment record if successful, None otherwise
        """
        # Validate file
        is_valid, error_msg = self._validate_file(filename, size)
        if not is_valid:
            raise ValueError(error_msg)

        # Ensure bucket exists
        if not self.s3.ensure_bucket_exists():
            raise RuntimeError("Failed to ensure S3 bucket exists")

        # Generate S3 key
        s3_key = self._generate_s3_key(record_type, record_id, filename, category)

        # Upload to S3
        result = self.s3.upload_file(
            file_data=file_data,
            object_key=s3_key,
            content_type=content_type,
            metadata={
                "original_filename": filename,
                "record_type": record_type,
                "record_id": str(record_id),
                "uploaded_by": uploaded_by or "system",
            },
        )

        if not result:
            raise RuntimeError("Failed to upload file to S3")

        # Create database record
        attachment = FileAttachment(
            record_type=record_type,
            record_id=record_id,
            file_name=s3_key.split("/")[-1],  # Just the filename part
            original_name=filename,
            file_type=content_type,  # MIME type stored in file_type field
            file_size=size,
            file_path=s3_key,  # Full S3 key
            file_category=category or "general",
        )
        self.db.add(attachment)
        self.db.commit()
        self.db.refresh(attachment)

        return attachment

    def get_document(self, document_id: int) -> Optional[FileAttachment]:
        """Get a document record by ID."""
        return self.db.query(FileAttachment).filter(
            FileAttachment.id == document_id,
            FileAttachment.is_deleted == False,
        ).first()

    def get_download_url(
        self,
        document_id: int,
        expiry: Optional[int] = None,
    ) -> Optional[str]:
        """
        Get a presigned download URL for a document.

        Args:
            document_id: Document ID
            expiry: URL expiry in seconds

        Returns:
            Presigned URL if successful, None otherwise
        """
        doc = self.get_document(document_id)
        if not doc:
            return None

        return self.s3.get_presigned_url(
            object_key=doc.file_path,
            expiry=expiry,
            download=True,
            filename=doc.original_name,
        )

    def download_document(self, document_id: int) -> Optional[tuple]:
        """
        Download document content directly.

        Returns:
            Tuple of (BytesIO content, filename, content_type) if successful
        """
        doc = self.get_document(document_id)
        if not doc:
            return None

        content = self.s3.download_file(doc.file_path)
        if not content:
            return None

        return content, doc.original_name, doc.file_type

    def delete_document(self, document_id: int, soft_delete: bool = True) -> bool:
        """
        Delete a document.

        Args:
            document_id: Document ID
            soft_delete: If True, mark as deleted. If False, delete from S3 too.

        Returns:
            True if successful
        """
        doc = self.get_document(document_id)
        if not doc:
            return False

        if soft_delete:
            doc.is_deleted = True
            doc.deleted_at = datetime.utcnow()
            self.db.commit()
        else:
            # Delete from S3
            self.s3.delete_file(doc.file_path)
            # Delete from database
            self.db.delete(doc)
            self.db.commit()

        return True

    def list_documents(
        self,
        record_type: Optional[str] = None,
        record_id: Optional[int] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[FileAttachment]:
        """
        List documents with optional filters.

        Args:
            record_type: Filter by record type
            record_id: Filter by record ID
            category: Filter by category
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of FileAttachment records
        """
        query = self.db.query(FileAttachment).filter(
            FileAttachment.is_deleted == False
        )

        if record_type:
            query = query.filter(FileAttachment.record_type == record_type)
        if record_id:
            query = query.filter(FileAttachment.record_id == record_id)
        if category:
            query = query.filter(FileAttachment.file_category == category)

        return query.order_by(FileAttachment.created_at.desc()).offset(skip).limit(limit).all()

    def count_documents(
        self,
        record_type: Optional[str] = None,
        record_id: Optional[int] = None,
        category: Optional[str] = None,
    ) -> int:
        """Count documents with optional filters."""
        query = self.db.query(FileAttachment).filter(
            FileAttachment.is_deleted == False
        )

        if record_type:
            query = query.filter(FileAttachment.record_type == record_type)
        if record_id:
            query = query.filter(FileAttachment.record_id == record_id)
        if category:
            query = query.filter(FileAttachment.file_category == category)

        return query.count()

    def get_presigned_upload_url(
        self,
        filename: str,
        content_type: str,
        record_type: str,
        record_id: int,
        category: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Get a presigned URL for direct upload.

        Returns:
            Dict with upload_url and s3_key if successful
        """
        # Validate file extension
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in self.settings.ALLOWED_EXTENSIONS:
            raise ValueError(f"File extension '{ext}' not allowed")

        # Ensure bucket exists
        if not self.s3.ensure_bucket_exists():
            raise RuntimeError("Failed to ensure S3 bucket exists")

        # Generate S3 key
        s3_key = self._generate_s3_key(record_type, record_id, filename, category)

        # Get presigned URL
        upload_url = self.s3.get_upload_presigned_url(
            object_key=s3_key,
            content_type=content_type,
        )

        if not upload_url:
            return None

        return {
            "upload_url": upload_url,
            "s3_key": s3_key,
            "expires_in": self.settings.S3_PRESIGNED_URL_EXPIRY,
        }

    def confirm_upload(
        self,
        s3_key: str,
        filename: str,
        content_type: str,
        record_type: str,
        record_id: int,
        category: Optional[str] = None,
        uploaded_by: Optional[str] = None,
    ) -> Optional[FileAttachment]:
        """
        Confirm a direct upload and create database record.

        Called after client completes presigned URL upload.
        """
        # Verify file exists in S3
        metadata = self.s3.get_file_metadata(s3_key)
        if not metadata:
            raise RuntimeError("File not found in S3")

        # Create database record
        attachment = FileAttachment(
            record_type=record_type,
            record_id=record_id,
            file_name=s3_key.split("/")[-1],
            original_name=filename,
            file_type=content_type,
            file_size=metadata["size"],
            file_path=s3_key,
            file_category=category or "general",
        )
        self.db.add(attachment)
        self.db.commit()
        self.db.refresh(attachment)

        return attachment
