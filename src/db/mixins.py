from datetime import datetime
from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.orm import declared_attr


class TimestampMixin:
    """Adds created_at and updated_at to any model."""

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
        )


class SoftDeleteMixin:
    """Adds soft delete capability. Never actually delete records."""

    @declared_attr
    def is_deleted(cls):
        return Column(Boolean, default=False, nullable=False, index=True)

    @declared_attr
    def deleted_at(cls):
        return Column(DateTime, nullable=True)
