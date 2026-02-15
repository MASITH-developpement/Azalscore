"""Add enrichment_provider_config table

Revision ID: 20260214_enrichment_provider_config
Revises: 20260213_ui_events
Create Date: 2026-02-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'enrichment_provider_config_001'
down_revision = 'ui_events_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ajouter nouvelles valeurs a l'enum EnrichmentProvider si necessaire
    # Note: Les enums PostgreSQL necessitent ALTER TYPE
    op.execute("ALTER TYPE enrichmentprovider ADD VALUE IF NOT EXISTS 'opencorporates'")
    op.execute("ALTER TYPE enrichmentprovider ADD VALUE IF NOT EXISTS 'creditsafe'")
    op.execute("ALTER TYPE enrichmentprovider ADD VALUE IF NOT EXISTS 'kompany'")

    # Creer la table enrichment_provider_config
    op.create_table(
        'enrichment_provider_config',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),
        sa.Column('provider', sa.Enum(
            'insee', 'adresse_gouv', 'openfoodfacts', 'openbeautyfacts',
            'openpetfoodfacts', 'vies', 'opencorporates', 'pappers',
            'google_places', 'amazon_paapi', 'pages_jaunes', 'creditsafe', 'kompany',
            name='enrichmentprovider'
        ), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), default=True),
        sa.Column('is_primary', sa.Boolean(), default=False),
        sa.Column('priority', sa.Integer(), default=100),
        sa.Column('api_key', sa.String(500), nullable=True),
        sa.Column('api_secret', sa.String(500), nullable=True),
        sa.Column('api_endpoint', sa.String(500), nullable=True),
        sa.Column('custom_requests_per_minute', sa.Integer(), nullable=True),
        sa.Column('custom_requests_per_day', sa.Integer(), nullable=True),
        sa.Column('config_data', sa.JSON(), default={}),
        sa.Column('last_success_at', sa.DateTime(), nullable=True),
        sa.Column('last_error_at', sa.DateTime(), nullable=True),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('total_requests', sa.Integer(), default=0),
        sa.Column('total_errors', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'provider', name='uq_provider_config_tenant_provider'),
    )

    # Creer les index
    op.create_index('idx_provider_config_tenant', 'enrichment_provider_config', ['tenant_id'])
    op.create_index('idx_provider_config_enabled', 'enrichment_provider_config', ['tenant_id', 'is_enabled'])
    op.create_index('idx_provider_config_primary', 'enrichment_provider_config', ['tenant_id', 'is_primary'])


def downgrade() -> None:
    # Supprimer les index
    op.drop_index('idx_provider_config_primary', table_name='enrichment_provider_config')
    op.drop_index('idx_provider_config_enabled', table_name='enrichment_provider_config')
    op.drop_index('idx_provider_config_tenant', table_name='enrichment_provider_config')

    # Supprimer la table
    op.drop_table('enrichment_provider_config')

    # Note: On ne supprime pas les valeurs de l'enum car cela casserait les donnees existantes
