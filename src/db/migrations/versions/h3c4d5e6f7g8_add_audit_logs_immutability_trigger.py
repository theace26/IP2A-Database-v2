"""add_audit_logs_immutability_trigger

Revision ID: h3c4d5e6f7g8
Revises: g2b3c4d5e6f7
Create Date: 2026-01-30 21:00:00.000000

CRITICAL: This migration enforces NLRA compliance by making audit logs immutable.
DO NOT modify or remove this trigger without legal review.
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "h3c4d5e6f7g8"
down_revision: Union[str, Sequence[str], None] = "g2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add immutability triggers to audit_logs table."""
    # Create the trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Audit logs are immutable. UPDATE and DELETE operations are prohibited for NLRA compliance.';
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create triggers for UPDATE and DELETE
    op.execute("""
        CREATE TRIGGER audit_logs_prevent_update
            BEFORE UPDATE ON audit_logs
            FOR EACH ROW
            EXECUTE FUNCTION prevent_audit_modification();
    """)

    op.execute("""
        CREATE TRIGGER audit_logs_prevent_delete
            BEFORE DELETE ON audit_logs
            FOR EACH ROW
            EXECUTE FUNCTION prevent_audit_modification();
    """)

    # Add comments explaining the triggers
    op.execute("""
        COMMENT ON TRIGGER audit_logs_prevent_update ON audit_logs IS
        'NLRA compliance: Prevents modification of audit records. 7-year retention required.';
    """)

    op.execute("""
        COMMENT ON TRIGGER audit_logs_prevent_delete ON audit_logs IS
        'NLRA compliance: Prevents deletion of audit records. 7-year retention required.';
    """)


def downgrade() -> None:
    """Remove immutability triggers from audit_logs table.

    WARNING: Removing this trigger may violate NLRA compliance requirements.
    Only downgrade if you have legal approval.
    """
    op.execute("DROP TRIGGER IF EXISTS audit_logs_prevent_update ON audit_logs;")
    op.execute("DROP TRIGGER IF EXISTS audit_logs_prevent_delete ON audit_logs;")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_modification();")
