"""
Generic file attachment model for storing files linked to any record.

File storage follows an organized path structure:
    uploads/{entity_type}s/{Owner_Name_ID}/{category}/{year}/{MM-Month}/{filename}

Example:
    uploads/members/Smith_John_M7464416/grievances/2026/01-January/safety_report.pdf
"""

from sqlalchemy import Column, Integer, String, Index

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin


class FileAttachment(TimestampMixin, SoftDeleteMixin, Base):
    """
    Generic file attachment storage.

    Uses polymorphic pattern (record_type + record_id) to link files
    to any entity type without foreign key constraints.

    This allows attaching files to students, credentials, applications, etc.
    without modifying those tables.

    Note: created_at from TimestampMixin replaces uploaded_at.
    """

    __tablename__ = "file_attachments"

    id = Column(Integer, primary_key=True, index=True)

    # Polymorphic reference - links to any table
    # Examples: 'member', 'student', 'organization', 'grievance'
    record_type = Column(String(50), nullable=False, index=True)
    record_id = Column(Integer, nullable=False, index=True)

    # Business category for organized folder structure
    # Examples: 'grievances', 'benevolence', 'certifications', 'general'
    file_category = Column(String(50), nullable=False, server_default="general", index=True)

    # File metadata
    file_name = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=True)  # Original upload name
    file_path = Column(String(500), nullable=False)  # Path on disk/storage
    file_type = Column(String(100), nullable=False)  # MIME type
    file_size = Column(Integer, nullable=True)  # Size in bytes

    # User-provided description
    description = Column(String(500), nullable=True)

    # Note: uploaded_at is now covered by created_at from TimestampMixin

    __table_args__ = (
        # Composite index for looking up attachments for a specific record
        Index("ix_file_attachment_record", "record_type", "record_id"),
    )

    def __repr__(self):
        return f"<FileAttachment(id={self.id}, type='{self.record_type}', record={self.record_id}, category='{self.file_category}', file='{self.file_name}')>"
