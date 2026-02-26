"""Ajouter champs sync comptable aux configs Odoo.

Revision ID: 20260214_odoo_accounting_sync
Revises: 20260214_odoo_scheduling
Create Date: 2026-02-14 18:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260214_odoo_accounting_sync'
down_revision = '20260214_odoo_scheduling'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Ajouter les colonnes de sync comptable a odoo_connection_configs."""

    # Ajouter la colonne accounting_last_sync_at
    op.add_column(
        'odoo_connection_configs',
        sa.Column('accounting_last_sync_at', sa.DateTime(), nullable=True)
    )

    # Ajouter la colonne bank_last_sync_at
    op.add_column(
        'odoo_connection_configs',
        sa.Column('bank_last_sync_at', sa.DateTime(), nullable=True)
    )

    # Ajouter la colonne total_accounting_entries_imported
    op.add_column(
        'odoo_connection_configs',
        sa.Column(
            'total_accounting_entries_imported',
            sa.Integer(),
            nullable=False,
            server_default='0'
        )
    )


def downgrade() -> None:
    """Supprimer les colonnes de sync comptable."""

    op.drop_column('odoo_connection_configs', 'total_accounting_entries_imported')
    op.drop_column('odoo_connection_configs', 'bank_last_sync_at')
    op.drop_column('odoo_connection_configs', 'accounting_last_sync_at')
