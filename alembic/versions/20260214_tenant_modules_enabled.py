"""Ajout colonne modules_enabled sur tenants

Revision ID: tenant_modules_enabled
Revises:
Create Date: 2026-02-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision = 'tenant_modules_enabled'
down_revision = 'odoo_import_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ajouter la colonne modules_enabled sur la table tenants (if not exists)
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'tenants' AND column_name = 'modules_enabled'
    """))
    if not result.fetchone():
        op.add_column('tenants', sa.Column('modules_enabled', JSON, nullable=True, default=list))


def downgrade() -> None:
    op.drop_column('tenants', 'modules_enabled')
