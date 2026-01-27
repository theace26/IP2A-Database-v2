"""
Reusable SQLAlchemy mixins for common model patterns.

These mixins should be inherited by all domain models to ensure
consistent timestamp tracking and soft delete capability.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.orm import declared_attr


class TimestampMixin:
    """
    Adds created_at and updated_at columns to any model.

    Usage:
        class MyModel(TimestampMixin, SoftDeleteMixin, Base):
            __tablename__ = "my_table"
            ...

    Note: Mixin classes should be listed BEFORE Base in the inheritance chain.
    """

    @declared_attr
    def created_at(cls):
        return Column(
            DateTime,
            default=datetime.utcnow,
            nullable=False,
            index=True,  # Often filtered/sorted by creation date
        )

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False,
        )


class SoftDeleteMixin:
    """
    Adds soft delete capability to any model.

    Instead of actually deleting records, set is_deleted=True.
    This preserves historical data and allows recovery.

    Usage:
        # In your queries, filter out deleted records:
        session.query(MyModel).filter(MyModel.is_deleted == False)

        # Or use a helper method on your service layer

    Note: You may want to add a database-level partial index:
        CREATE INDEX ix_mymodel_active ON my_table(id) WHERE is_deleted = FALSE;
    """

    @declared_attr
    def is_deleted(cls):
        return Column(
            Boolean,
            default=False,
            nullable=False,
            index=True,
        )

    @declared_attr
    def deleted_at(cls):
        return Column(
            DateTime,
            nullable=True,
        )

    def soft_delete(self):
        """Mark this record as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
