"""Enrichment Module - Auto-enrichissement via APIs externes

Revision ID: enrichment_module_001
Revises: marceau_module_001
Create Date: 2026-02-10

Tables:
- enrichment_history: Historique des enrichissements (audit complet)
- enrichment_rate_limits: Limites de taux par provider et tenant

Ce module permet l'enrichissement automatique des formulaires via APIs externes:
- SIRENE/INSEE: Lookup entreprises francaises (SIRET/SIREN)
- API Adresse gouv.fr: Autocomplete adresses francaises
- Open Food Facts: Produits alimentaires par code-barres
- Open Beauty Facts: Produits cosmetiques
- Open Pet Food Facts: Produits animaliers
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'enrichment_module_001'
down_revision = ('marceau_module_001', '078dfbe1e5a3')  # Merge point for both heads
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Enrichment module tables and enums."""

    # ==========================================================================
    # ENUM TYPES
    # ==========================================================================

    # Enrichment Provider
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE enrichment_provider AS ENUM (
                'insee',
                'adresse_gouv',
                'openfoodfacts',
                'openbeautyfacts',
                'openpetfoodfacts',
                'pappers',
                'google_places',
                'amazon_paapi',
                'pages_jaunes'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Enrichment Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE enrichment_status AS ENUM (
                'pending',
                'success',
                'partial',
                'not_found',
                'error',
                'rate_limited'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Enrichment Action
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE enrichment_action AS ENUM (
                'pending',
                'accepted',
                'rejected',
                'partial'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Lookup Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE enrichment_lookup_type AS ENUM (
                'siret',
                'siren',
                'address',
                'barcode'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Entity Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE enrichment_entity_type AS ENUM (
                'contact',
                'product'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ==========================================================================
    # ENRICHMENT HISTORY TABLE
    # ==========================================================================

    op.create_table(
        'enrichment_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),

        # Reference polymorphique vers l'entite enrichie
        sa.Column('entity_type', postgresql.ENUM('contact', 'product', name='enrichment_entity_type', create_type=False), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Cle de recherche
        sa.Column('lookup_type', postgresql.ENUM('siret', 'siren', 'address', 'barcode', name='enrichment_lookup_type', create_type=False), nullable=False),
        sa.Column('lookup_value', sa.String(255), nullable=False),

        # Provider
        sa.Column('provider', postgresql.ENUM(
            'insee', 'adresse_gouv', 'openfoodfacts', 'openbeautyfacts', 'openpetfoodfacts',
            'pappers', 'google_places', 'amazon_paapi', 'pages_jaunes',
            name='enrichment_provider', create_type=False
        ), nullable=False),
        sa.Column('status', postgresql.ENUM(
            'pending', 'success', 'partial', 'not_found', 'error', 'rate_limited',
            name='enrichment_status', create_type=False
        ), default='pending'),

        # Requete/Reponse
        sa.Column('request_data', postgresql.JSONB, server_default='{}'),
        sa.Column('response_data', postgresql.JSONB, server_default='{}'),
        sa.Column('enriched_fields', postgresql.JSONB, server_default='{}'),

        # Confiance et audit
        sa.Column('confidence_score', sa.Numeric(3, 2), default=0.00),
        sa.Column('api_response_time_ms', sa.Integer, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('cached', sa.Boolean, default=False),

        # Action utilisateur
        sa.Column('action', postgresql.ENUM(
            'pending', 'accepted', 'rejected', 'partial',
            name='enrichment_action', create_type=False
        ), default='pending'),
        sa.Column('accepted_fields', postgresql.JSONB, server_default='[]'),
        sa.Column('rejected_fields', postgresql.JSONB, server_default='[]'),
        sa.Column('action_at', sa.DateTime, nullable=True),
        sa.Column('action_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Metadata
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
    )

    # Indexes
    op.create_index('idx_enrichment_tenant', 'enrichment_history', ['tenant_id'])
    op.create_index('idx_enrichment_entity', 'enrichment_history', ['tenant_id', 'entity_type', 'entity_id'])
    op.create_index('idx_enrichment_lookup', 'enrichment_history', ['tenant_id', 'lookup_type', 'lookup_value'])
    op.create_index('idx_enrichment_provider', 'enrichment_history', ['tenant_id', 'provider'])
    op.create_index('idx_enrichment_status', 'enrichment_history', ['tenant_id', 'status'])
    op.create_index('idx_enrichment_created', 'enrichment_history', ['tenant_id', 'created_at'])

    # ==========================================================================
    # ENRICHMENT RATE LIMITS TABLE
    # ==========================================================================

    op.create_table(
        'enrichment_rate_limits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False),
        sa.Column('provider', postgresql.ENUM(
            'insee', 'adresse_gouv', 'openfoodfacts', 'openbeautyfacts', 'openpetfoodfacts',
            'pappers', 'google_places', 'amazon_paapi', 'pages_jaunes',
            name='enrichment_provider', create_type=False
        ), nullable=False),

        # Limites configurees
        sa.Column('requests_per_minute', sa.Integer, default=60),
        sa.Column('requests_per_day', sa.Integer, default=1000),

        # Utilisation actuelle
        sa.Column('minute_count', sa.Integer, default=0),
        sa.Column('minute_reset_at', sa.DateTime, nullable=True),
        sa.Column('day_count', sa.Integer, default=0),
        sa.Column('day_reset_at', sa.DateTime, nullable=True),

        # Configuration
        sa.Column('is_enabled', sa.Boolean, default=True),
        sa.Column('custom_config', postgresql.JSONB, server_default='{}'),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()')),

        # Contrainte unique
        sa.UniqueConstraint('tenant_id', 'provider', name='uq_rate_limit_tenant_provider'),
    )

    # Index
    op.create_index('idx_rate_limit_tenant', 'enrichment_rate_limits', ['tenant_id'])

    print("[MIGRATION] Enrichment module tables created successfully")


def downgrade() -> None:
    """Drop Enrichment module tables and enums."""

    # Drop tables
    op.drop_table('enrichment_rate_limits')
    op.drop_table('enrichment_history')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS enrichment_entity_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS enrichment_lookup_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS enrichment_action CASCADE;")
    op.execute("DROP TYPE IF EXISTS enrichment_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS enrichment_provider CASCADE;")

    print("[MIGRATION] Enrichment module tables dropped successfully")
