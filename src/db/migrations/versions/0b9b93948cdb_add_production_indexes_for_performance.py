"""add production indexes for performance

Revision ID: 0b9b93948cdb
Revises: d8a4e12155a3
Create Date: 2026-01-27 11:15:43.859792

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b9b93948cdb'
down_revision: Union[str, Sequence[str], None] = 'd8a4e12155a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add production indexes for common query patterns.

    Note: These indexes are created WITHOUT CONCURRENTLY to work within
    Alembic transactions. For zero-downtime production deployment, use:
    CREATE INDEX CONCURRENTLY in a separate psql session.
    """

    # Indexes for member_employments (most queried table - 84% of records)
    op.create_index(
        'idx_member_employments_member_id',
        'member_employments',
        ['member_id'],
        unique=False
    )
    op.create_index(
        'idx_member_employments_organization_id',
        'member_employments',
        ['organization_id'],
        unique=False
    )

    # Composite index for date range queries on employments
    op.create_index(
        'idx_member_employments_dates',
        'member_employments',
        ['start_date', 'end_date'],
        unique=False
    )

    # Index for organization_contacts lookups
    op.create_index(
        'idx_organization_contacts_org_id',
        'organization_contacts',
        ['organization_id'],
        unique=False
    )

    # Partial index for active members (common query pattern)
    op.execute("""
        CREATE INDEX idx_members_active
        ON members(status)
        WHERE status = 'ACTIVE'
    """)

    # Partial index for primary contacts (common query pattern)
    op.execute("""
        CREATE INDEX idx_contacts_primary
        ON organization_contacts(organization_id)
        WHERE is_primary = true
    """)

    # Index for member lookups by status and classification (analytics queries)
    op.create_index(
        'idx_members_status_classification',
        'members',
        ['status', 'classification'],
        unique=False
    )


def downgrade() -> None:
    """Remove production indexes."""

    op.drop_index('idx_members_status_classification', table_name='members')
    op.drop_index('idx_contacts_primary', table_name='organization_contacts')
    op.drop_index('idx_members_active', table_name='members')
    op.drop_index('idx_organization_contacts_org_id', table_name='organization_contacts')
    op.drop_index('idx_member_employments_dates', table_name='member_employments')
    op.drop_index('idx_member_employments_organization_id', table_name='member_employments')
    op.drop_index('idx_member_employments_member_id', table_name='member_employments')
