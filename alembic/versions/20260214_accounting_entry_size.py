"""Augmenter la taille des colonnes entry_number et piece_number.

Revision ID: 20260214_accounting_entry_size
Revises: 20260214_odoo_accounting_sync
Create Date: 2026-02-14 23:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260214_accounting_entry_size'
down_revision = '20260214_odoo_accounting_sync'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Augmenter la taille des colonnes pour les ecritures comptables."""

    # Augmenter entry_number de 50 a 100 caracteres
    op.alter_column(
        'accounting_journal_entries',
        'entry_number',
        type_=sa.String(100),
        existing_type=sa.String(50),
        existing_nullable=False
    )

    # Augmenter piece_number de 50 a 100 caracteres
    op.alter_column(
        'accounting_journal_entries',
        'piece_number',
        type_=sa.String(100),
        existing_type=sa.String(50),
        existing_nullable=False
    )


def downgrade() -> None:
    """Revenir aux tailles originales."""

    op.alter_column(
        'accounting_journal_entries',
        'entry_number',
        type_=sa.String(50),
        existing_type=sa.String(100),
        existing_nullable=False
    )

    op.alter_column(
        'accounting_journal_entries',
        'piece_number',
        type_=sa.String(50),
        existing_type=sa.String(100),
        existing_nullable=False
    )
