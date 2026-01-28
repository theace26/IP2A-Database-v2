"""Add dues tracking models

Revision ID: ee8ead726e9b
Revises: 9b75a876ef60
Create Date: 2026-01-28 19:56:24.888920

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee8ead726e9b'
down_revision: Union[str, Sequence[str], None] = '9b75a876ef60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create new enum types for dues tracking
    op.execute("CREATE TYPE duespaymentmethod AS ENUM ('PAYROLL_DEDUCTION', 'CHECK', 'CASH', 'MONEY_ORDER', 'CREDIT_CARD', 'ACH_TRANSFER', 'ONLINE', 'OTHER')")
    op.execute("CREATE TYPE duespaymentstatus AS ENUM ('PENDING', 'DUE', 'PARTIAL', 'PAID', 'OVERDUE', 'WAIVED', 'WRITTEN_OFF')")
    op.execute("CREATE TYPE duesadjustmenttype AS ENUM ('WAIVER', 'HARDSHIP', 'CREDIT', 'CORRECTION', 'LATE_FEE', 'REINSTATEMENT', 'OTHER')")
    op.execute("CREATE TYPE adjustmentstatus AS ENUM ('PENDING', 'APPROVED', 'DENIED')")

    # Create dues_rates table - uses existing memberclassification enum
    op.execute("""
        CREATE TABLE dues_rates (
            id SERIAL PRIMARY KEY,
            classification memberclassification NOT NULL,
            monthly_amount NUMERIC(10, 2) NOT NULL,
            effective_date DATE NOT NULL,
            end_date DATE,
            description VARCHAR(255),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_dues_rate_class_effective UNIQUE (classification, effective_date)
        )
    """)
    op.create_index('ix_dues_rates_id', 'dues_rates', ['id'])

    # Create dues_periods table
    op.create_table('dues_periods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('period_year', sa.Integer(), nullable=False),
        sa.Column('period_month', sa.Integer(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('grace_period_end', sa.Date(), nullable=False),
        sa.Column('is_closed', sa.Boolean(), nullable=True, default=False),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('closed_by_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['closed_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('period_year', 'period_month', name='uq_dues_period_year_month')
    )
    op.create_index('ix_dues_periods_id', 'dues_periods', ['id'])

    # Create dues_payments table
    op.execute("""
        CREATE TABLE dues_payments (
            id SERIAL PRIMARY KEY,
            member_id INTEGER NOT NULL REFERENCES members(id),
            period_id INTEGER NOT NULL REFERENCES dues_periods(id),
            amount_due NUMERIC(10, 2) NOT NULL,
            amount_paid NUMERIC(10, 2) NOT NULL DEFAULT 0,
            payment_date DATE,
            payment_method duespaymentmethod,
            status duespaymentstatus NOT NULL DEFAULT 'PENDING',
            reference_number VARCHAR(100),
            receipt_number VARCHAR(50) UNIQUE,
            processed_by_id INTEGER REFERENCES users(id),
            processed_at TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
            deleted_at TIMESTAMP
        )
    """)
    op.create_index('ix_dues_payments_id', 'dues_payments', ['id'])
    op.create_index('ix_dues_payments_member_id', 'dues_payments', ['member_id'])
    op.create_index('ix_dues_payments_period_id', 'dues_payments', ['period_id'])
    op.create_index('ix_dues_payments_is_deleted', 'dues_payments', ['is_deleted'])

    # Create dues_adjustments table
    op.execute("""
        CREATE TABLE dues_adjustments (
            id SERIAL PRIMARY KEY,
            member_id INTEGER NOT NULL REFERENCES members(id),
            payment_id INTEGER REFERENCES dues_payments(id),
            adjustment_type duesadjustmenttype NOT NULL,
            amount NUMERIC(10, 2) NOT NULL,
            reason TEXT NOT NULL,
            requested_by_id INTEGER NOT NULL REFERENCES users(id),
            approved_by_id INTEGER REFERENCES users(id),
            approved_at TIMESTAMP,
            status adjustmentstatus NOT NULL DEFAULT 'PENDING',
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    op.create_index('ix_dues_adjustments_id', 'dues_adjustments', ['id'])
    op.create_index('ix_dues_adjustments_member_id', 'dues_adjustments', ['member_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_dues_adjustments_member_id', table_name='dues_adjustments')
    op.drop_index('ix_dues_adjustments_id', table_name='dues_adjustments')
    op.drop_table('dues_adjustments')

    op.drop_index('ix_dues_payments_is_deleted', table_name='dues_payments')
    op.drop_index('ix_dues_payments_period_id', table_name='dues_payments')
    op.drop_index('ix_dues_payments_member_id', table_name='dues_payments')
    op.drop_index('ix_dues_payments_id', table_name='dues_payments')
    op.drop_table('dues_payments')

    op.drop_index('ix_dues_periods_id', table_name='dues_periods')
    op.drop_table('dues_periods')

    op.drop_index('ix_dues_rates_id', table_name='dues_rates')
    op.drop_table('dues_rates')

    # Drop the new enum types
    op.execute("DROP TYPE adjustmentstatus")
    op.execute("DROP TYPE duesadjustmenttype")
    op.execute("DROP TYPE duespaymentstatus")
    op.execute("DROP TYPE duespaymentmethod")
