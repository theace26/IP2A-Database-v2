"""restore file_attachments table for stress test

Revision ID: d8a4e12155a3
Revises: 7967f77cdbb6
Create Date: 2026-01-27 11:13:55.660803

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8a4e12155a3'
down_revision: Union[str, Sequence[str], None] = '7967f77cdbb6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Restore file_attachments table for stress test and future file management."""
    op.create_table(
        "file_attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("record_type", sa.String(length=50), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_file_attachments_id"), "file_attachments", ["id"], unique=False)
    op.create_index(
        op.f("ix_file_attachments_is_deleted"),
        "file_attachments",
        ["is_deleted"],
        unique=False,
    )
    op.create_index(
        op.f("ix_file_attachments_record_id"),
        "file_attachments",
        ["record_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_file_attachments_record_type"),
        "file_attachments",
        ["record_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_file_attachment_record"),
        "file_attachments",
        ["record_type", "record_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop file_attachments table."""
    op.drop_index(op.f("ix_file_attachment_record"), table_name="file_attachments")
    op.drop_index(op.f("ix_file_attachments_record_type"), table_name="file_attachments")
    op.drop_index(op.f("ix_file_attachments_record_id"), table_name="file_attachments")
    op.drop_index(op.f("ix_file_attachments_is_deleted"), table_name="file_attachments")
    op.drop_index(op.f("ix_file_attachments_id"), table_name="file_attachments")
    op.drop_table("file_attachments")
