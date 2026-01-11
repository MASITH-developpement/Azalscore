"""core_init_0000_create_tenants

Revision ID: a15a43ff0165
Revises: 078dfbe1e5a3
Create Date: 2026-01-11 14:27:56.402031+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a15a43ff0165"
down_revision = "system_setting_001"   # ou None si vraiment racine
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("tenants"):
        op.create_table(
            "tenants",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, unique=True),

            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("legal_name", sa.String(255)),
            sa.Column("siret", sa.String(20)),
            sa.Column("vat_number", sa.String(30)),

            sa.Column("email", sa.String(255)),
            sa.Column("phone", sa.String(50)),
            sa.Column("website", sa.String(255)),

            sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
            sa.Column("environment", sa.String(20), nullable=False, server_default="prod"),

            sa.Column("timezone", sa.String(50), server_default="Europe/Paris"),
            sa.Column("language", sa.String(10), server_default="fr"),
            sa.Column("currency", sa.String(3), server_default="EUR"),

            sa.Column("features", postgresql.JSONB),
            sa.Column("extra_data", postgresql.JSONB),

            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )


def downgrade():
    op.drop_table("tenants")
