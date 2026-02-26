"""Add Odoo Import module tables

Revision ID: odoo_import_001
Revises: product_erp_fields_001
Create Date: 2026-02-14

Tables creees:
- odoo_connection_configs: Configuration de connexion Odoo par tenant
- odoo_import_history: Historique des operations d'import
- odoo_field_mappings: Mappings personnalises des champs
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'odoo_import_001'
down_revision = 'product_erp_fields_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # ENUMS
    # =========================================================================

    # OdooAuthMethod enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE odooauthmethod AS ENUM ('password', 'api_key');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # OdooSyncType enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE odoosynctype AS ENUM (
                'products', 'contacts', 'suppliers', 'purchase_orders', 'full'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # OdooImportStatus enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE odooimportstatus AS ENUM (
                'pending', 'running', 'success', 'partial', 'error', 'cancelled'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # =========================================================================
    # TABLE: odoo_connection_configs
    # =========================================================================

    op.create_table(
        'odoo_connection_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),

        # Identification
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Connexion Odoo
        sa.Column('odoo_url', sa.String(500), nullable=False),
        sa.Column('odoo_database', sa.String(100), nullable=False),
        sa.Column('odoo_version', sa.String(10), nullable=True),

        # Authentification
        sa.Column('auth_method', postgresql.ENUM(
            'password', 'api_key',
            name='odooauthmethod',
            create_type=False
        ), nullable=False, server_default='api_key'),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('encrypted_credential', sa.Text(), nullable=True),

        # Options de synchronisation
        sa.Column('sync_products', sa.Boolean(), server_default='true'),
        sa.Column('sync_contacts', sa.Boolean(), server_default='true'),
        sa.Column('sync_suppliers', sa.Boolean(), server_default='true'),
        sa.Column('sync_purchase_orders', sa.Boolean(), server_default='false'),

        # Configuration delta sync
        sa.Column('products_last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('contacts_last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('suppliers_last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('orders_last_sync_at', sa.DateTime(), nullable=True),

        # Statistiques
        sa.Column('total_imports', sa.Integer(), server_default='0'),
        sa.Column('total_products_imported', sa.Integer(), server_default='0'),
        sa.Column('total_contacts_imported', sa.Integer(), server_default='0'),
        sa.Column('total_suppliers_imported', sa.Integer(), server_default='0'),
        sa.Column('total_orders_imported', sa.Integer(), server_default='0'),
        sa.Column('last_error_message', sa.Text(), nullable=True),

        # Etat
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('is_connected', sa.Boolean(), server_default='false'),
        sa.Column('last_connection_test_at', sa.DateTime(), nullable=True),

        # Mapping personnalise
        sa.Column('custom_field_mapping', postgresql.JSONB(), server_default='{}'),

        # Audit
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_odoo_config_tenant_name'),
    )

    op.create_index('idx_odoo_config_tenant', 'odoo_connection_configs', ['tenant_id'])
    op.create_index('idx_odoo_config_active', 'odoo_connection_configs', ['tenant_id', 'is_active'])

    # =========================================================================
    # TABLE: odoo_import_history
    # =========================================================================

    op.create_table(
        'odoo_import_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),
        sa.Column('config_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Type de sync
        sa.Column('sync_type', postgresql.ENUM(
            'products', 'contacts', 'suppliers', 'purchase_orders', 'full',
            name='odoosynctype',
            create_type=False
        ), nullable=False),

        # Statut
        sa.Column('status', postgresql.ENUM(
            'pending', 'running', 'success', 'partial', 'error', 'cancelled',
            name='odooimportstatus',
            create_type=False
        ), nullable=False, server_default='pending'),

        # Timing
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),

        # Statistiques
        sa.Column('total_records', sa.Integer(), server_default='0'),
        sa.Column('created_count', sa.Integer(), server_default='0'),
        sa.Column('updated_count', sa.Integer(), server_default='0'),
        sa.Column('skipped_count', sa.Integer(), server_default='0'),
        sa.Column('error_count', sa.Integer(), server_default='0'),

        # Details
        sa.Column('error_details', postgresql.JSONB(), server_default='[]'),
        sa.Column('import_summary', postgresql.JSONB(), server_default='{}'),

        # Parametres
        sa.Column('is_delta_sync', sa.Boolean(), server_default='true'),
        sa.Column('delta_from_date', sa.DateTime(), nullable=True),

        # Audit
        sa.Column('triggered_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('trigger_method', sa.String(50), server_default="'manual'"),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['config_id'], ['odoo_connection_configs.id'], ondelete='CASCADE'),
    )

    op.create_index('idx_import_history_tenant', 'odoo_import_history', ['tenant_id'])
    op.create_index('idx_import_history_config', 'odoo_import_history', ['config_id'])
    op.create_index('idx_import_history_status', 'odoo_import_history', ['tenant_id', 'status'])
    op.create_index('idx_import_history_date', 'odoo_import_history', ['tenant_id', 'started_at'])

    # =========================================================================
    # TABLE: odoo_field_mappings
    # =========================================================================

    op.create_table(
        'odoo_field_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),
        sa.Column('config_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Modeles
        sa.Column('odoo_model', sa.String(100), nullable=False),
        sa.Column('azals_model', sa.String(100), nullable=False),

        # Mapping
        sa.Column('field_mapping', postgresql.JSONB(), nullable=False),
        sa.Column('transformations', postgresql.JSONB(), server_default='{}'),

        # Configuration
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('priority', sa.Integer(), server_default='100'),

        # Audit
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['config_id'], ['odoo_connection_configs.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('config_id', 'odoo_model', 'azals_model', name='uq_field_mapping'),
    )

    op.create_index('idx_field_mapping_tenant', 'odoo_field_mappings', ['tenant_id'])
    op.create_index('idx_field_mapping_config', 'odoo_field_mappings', ['config_id'])
    op.create_index('idx_field_mapping_model', 'odoo_field_mappings', ['tenant_id', 'odoo_model'])


def downgrade() -> None:
    # Supprimer les tables dans l'ordre inverse
    op.drop_table('odoo_field_mappings')
    op.drop_table('odoo_import_history')
    op.drop_table('odoo_connection_configs')

    # Supprimer les enums
    op.execute("DROP TYPE IF EXISTS odooimportstatus")
    op.execute("DROP TYPE IF EXISTS odoosynctype")
    op.execute("DROP TYPE IF EXISTS odooauthmethod")
