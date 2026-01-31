"""add supporting_docs_path to jatc_applications

Revision ID: dd55a5a4513a
Revises: ea296d2988d7
Create Date: 2026-01-18 00:08:04.038649

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "dd55a5a4513a"
down_revision: Union[str, Sequence[str], None] = "ea296d2988d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "jatc_applications",
        sa.Column("supporting_docs_path", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("jatc_applications", "supporting_docs_path")
