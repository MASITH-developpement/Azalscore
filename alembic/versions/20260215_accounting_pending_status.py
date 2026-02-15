"""Add PENDING status to accounting_entrystatus enum

Revision ID: accounting_pending_status
Revises: 20260214_odoo_accounting_sync
Create Date: 2026-02-15

Adds PENDING status to align with service code that uses EntryStatus.PENDING.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '20260215_accounting_pending_status'
down_revision = '20260214_accounting_entry_size'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add PENDING to accounting_entrystatus enum."""
    # PostgreSQL: Add new value to existing enum
    # Note: ALTER TYPE ... ADD VALUE cannot be executed inside a transaction block
    # We must use autocommit mode
    op.execute("COMMIT")  # Close current transaction
    op.execute("ALTER TYPE accounting_entrystatus ADD VALUE IF NOT EXISTS 'PENDING' AFTER 'DRAFT'")


def downgrade() -> None:
    """Remove PENDING from accounting_entrystatus enum.

    Note: PostgreSQL does not support removing enum values directly.
    This would require recreating the enum type, which is complex.
    We leave the value in place - it's harmless if unused.
    """
    pass
