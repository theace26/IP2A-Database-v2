"""add timestamp and soft delete columns to all tables

Revision ID: ad4f65911cd7
Revises: 974d80591af2
Create Date: 2026-01-25 16:04:56.942865

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ad4f65911cd7"
down_revision: Union[str, Sequence[str], None] = "974d80591af2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # For each table, add the columns
    for table in [
        "students",
        "instructors",
        "cohorts",
        "locations",
        "credentials",
        "tools_issued",
        "jatc_applications",
        "instructor_hours",
        "expenses",
        "grants",
        "class_sessions",
        "attendance",
    ]:
        op.add_column(table, sa.Column("created_at", sa.DateTime(), nullable=True))
        op.add_column(table, sa.Column("updated_at", sa.DateTime(), nullable=True))
        op.add_column(
            table,
            sa.Column(
                "is_deleted", sa.Boolean(), server_default="false", nullable=False
            ),
        )
        op.add_column(table, sa.Column("deleted_at", sa.DateTime(), nullable=True))

        # Backfill existing records
        op.execute(
            f"UPDATE {table} SET created_at = NOW(), updated_at = NOW() WHERE created_at IS NULL"
        )

        # Now make created_at non-nullable
        op.alter_column(table, "created_at", nullable=False)
        op.alter_column(table, "updated_at", nullable=False)
