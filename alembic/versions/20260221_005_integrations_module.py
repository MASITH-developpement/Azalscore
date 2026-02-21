"""Module Integrations (GAP-086) - Connecteurs externes

Revision ID: integrations_001
Revises: expenses_001
Create Date: 2026-02-21

Tables:
- integration_connections: Connexions aux services externes
- integration_entity_mappings: Mappings d'entités
- integration_sync_jobs: Jobs de synchronisation
- integration_sync_logs: Logs de synchronisation
- integration_conflicts: Conflits à résoudre
- integration_webhooks: Webhooks entrants

Multi-tenant strict, Audit complet, Support OAuth2.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'integrations_001'
down_revision = 'expenses_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Integrations module tables and enums."""

    # ==========================================================================
    # ENUM TYPES
    # ==========================================================================

    # Connector Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE connector_type AS ENUM (
                'sage', 'cegid', 'pennylane', 'odoo', 'sap', 'salesforce', 'hubspot',
                'shopify', 'woocommerce', 'stripe', 'gocardless', 'qonto',
                'mailchimp', 'slack', 'google_drive', 'custom'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Auth Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE integration_auth_type AS ENUM (
                'api_key', 'oauth2', 'basic', 'bearer', 'hmac', 'certificate'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Sync Direction
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE sync_direction AS ENUM (
                'import', 'export', 'bidirectional'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Sync Frequency
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE sync_frequency AS ENUM (
                'realtime', 'hourly', 'daily', 'weekly', 'manual'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Connection Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE connection_status AS ENUM (
                'connected', 'disconnected', 'error', 'expired', 'pending'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Sync Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE sync_status AS ENUM (
                'pending', 'running', 'completed', 'partial', 'failed', 'cancelled'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Conflict Resolution
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE conflict_resolution AS ENUM (
                'source_wins', 'target_wins', 'newest_wins', 'manual', 'merge'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Integration Entity Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE integration_entity_type AS ENUM (
                'customer', 'supplier', 'product', 'order', 'invoice', 'payment', 'contact', 'lead'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ==========================================================================
    # INTEGRATION CONNECTIONS TABLE
    # ==========================================================================

    op.create_table(
        'integration_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),

        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('connector_type', sa.String(50), nullable=False),
        sa.Column('auth_type', sa.String(30), nullable=False),

        # Configuration
        sa.Column('base_url', sa.String(500), nullable=True),
        sa.Column('credentials', postgresql.JSONB, server_default='{}'),
        sa.Column('custom_headers', postgresql.JSONB, server_default='{}'),
        sa.Column('settings', postgresql.JSONB, server_default='{}'),

        # OAuth2
        sa.Column('access_token', sa.Text, nullable=True),
        sa.Column('refresh_token', sa.Text, nullable=True),
        sa.Column('token_expires_at', sa.DateTime, nullable=True),

        # State
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('last_connected_at', sa.DateTime, nullable=True),
        sa.Column('last_error', sa.Text, nullable=True),

        # Health
        sa.Column('last_health_check', sa.DateTime, nullable=True),
        sa.Column('consecutive_errors', sa.Integer, server_default='0'),

        # Audit
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_index('ix_integration_connections_tenant_code', 'integration_connections', ['tenant_id', 'code'], unique=True)
    op.create_index('ix_integration_connections_tenant_type', 'integration_connections', ['tenant_id', 'connector_type'])
    op.create_index('ix_integration_connections_tenant_status', 'integration_connections', ['tenant_id', 'status'])

    # ==========================================================================
    # INTEGRATION ENTITY MAPPINGS TABLE
    # ==========================================================================

    op.create_table(
        'integration_entity_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('integration_connections.id'), nullable=False),

        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),

        # Source and target
        sa.Column('source_entity', sa.String(100), nullable=False),
        sa.Column('target_entity', sa.String(100), nullable=False),
        sa.Column('direction', sa.String(20), server_default='bidirectional'),

        # Field mappings (JSON)
        sa.Column('field_mappings', postgresql.JSONB, server_default='[]'),

        # Filters (JSON)
        sa.Column('source_filter', postgresql.JSONB, nullable=True),
        sa.Column('target_filter', postgresql.JSONB, nullable=True),

        # Dedup key
        sa.Column('dedup_key_source', sa.String(100), nullable=True),
        sa.Column('dedup_key_target', sa.String(100), nullable=True),

        # State
        sa.Column('is_active', sa.Boolean, server_default='true'),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_index('ix_entity_mappings_connection', 'integration_entity_mappings', ['connection_id', 'entity_type'])
    op.create_index('ix_entity_mappings_tenant_code', 'integration_entity_mappings', ['tenant_id', 'code'], unique=True)

    # ==========================================================================
    # INTEGRATION SYNC JOBS TABLE
    # ==========================================================================

    op.create_table(
        'integration_sync_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('integration_connections.id'), nullable=False),
        sa.Column('entity_mapping_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('integration_entity_mappings.id'), nullable=False),

        # Configuration
        sa.Column('direction', sa.String(20), nullable=False),
        sa.Column('conflict_resolution', sa.String(20), server_default='newest_wins'),

        # Scheduling
        sa.Column('frequency', sa.String(20), server_default='manual'),
        sa.Column('next_run_at', sa.DateTime, nullable=True),
        sa.Column('cron_expression', sa.String(100), nullable=True),

        # State
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),

        # Statistics
        sa.Column('total_records', sa.Integer, server_default='0'),
        sa.Column('processed_records', sa.Integer, server_default='0'),
        sa.Column('created_records', sa.Integer, server_default='0'),
        sa.Column('updated_records', sa.Integer, server_default='0'),
        sa.Column('skipped_records', sa.Integer, server_default='0'),
        sa.Column('failed_records', sa.Integer, server_default='0'),

        # Errors (JSON)
        sa.Column('errors', postgresql.JSONB, server_default='[]'),

        # Delta sync
        sa.Column('last_sync_at', sa.DateTime, nullable=True),
        sa.Column('sync_cursor', sa.Text, nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_index('ix_sync_jobs_tenant_status', 'integration_sync_jobs', ['tenant_id', 'status'])
    op.create_index('ix_sync_jobs_connection', 'integration_sync_jobs', ['connection_id', 'status'])

    # ==========================================================================
    # INTEGRATION SYNC LOGS TABLE
    # ==========================================================================

    op.create_table(
        'integration_sync_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('integration_sync_jobs.id'), nullable=False),

        # Record
        sa.Column('source_id', sa.String(255), nullable=False),
        sa.Column('target_id', sa.String(255), nullable=True),
        sa.Column('entity_type', sa.String(50), nullable=False),

        # Action
        sa.Column('action', sa.String(20), nullable=False),

        # Data (JSON)
        sa.Column('source_data', postgresql.JSONB, nullable=True),
        sa.Column('target_data', postgresql.JSONB, nullable=True),
        sa.Column('changes', postgresql.JSONB, nullable=True),

        # Result
        sa.Column('success', sa.Boolean, server_default='true'),
        sa.Column('error_message', sa.Text, nullable=True),

        # Timestamp
        sa.Column('timestamp', sa.DateTime, server_default=sa.text('NOW()')),
    )

    op.create_index('ix_sync_logs_job', 'integration_sync_logs', ['job_id', 'timestamp'])
    op.create_index('ix_sync_logs_source', 'integration_sync_logs', ['tenant_id', 'source_id'])

    # ==========================================================================
    # INTEGRATION CONFLICTS TABLE
    # ==========================================================================

    op.create_table(
        'integration_conflicts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('integration_sync_jobs.id'), nullable=False),

        # Conflicting records
        sa.Column('source_id', sa.String(255), nullable=False),
        sa.Column('target_id', sa.String(255), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),

        # Data (JSON)
        sa.Column('source_data', postgresql.JSONB, server_default='{}'),
        sa.Column('target_data', postgresql.JSONB, server_default='{}'),
        sa.Column('conflicting_fields', postgresql.JSONB, server_default='[]'),

        # Resolution
        sa.Column('resolution', sa.String(20), nullable=True),
        sa.Column('resolved_data', postgresql.JSONB, nullable=True),
        sa.Column('resolved_at', sa.DateTime, nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Timestamp
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
    )

    op.create_index('ix_conflicts_tenant_pending', 'integration_conflicts', ['tenant_id', 'resolved_at'])
    op.create_index('ix_conflicts_job', 'integration_conflicts', ['job_id'])

    # ==========================================================================
    # INTEGRATION WEBHOOKS TABLE
    # ==========================================================================

    op.create_table(
        'integration_webhooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('integration_connections.id'), nullable=False),

        # Configuration
        sa.Column('endpoint_path', sa.String(255), nullable=False),
        sa.Column('secret_key', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='true'),

        # Events (JSON)
        sa.Column('subscribed_events', postgresql.JSONB, server_default='[]'),

        # Stats
        sa.Column('last_received_at', sa.DateTime, nullable=True),
        sa.Column('total_received', sa.Integer, server_default='0'),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_index('ix_webhooks_tenant_path', 'integration_webhooks', ['tenant_id', 'endpoint_path'], unique=True)

    print("[MIGRATION] Integrations module (GAP-086) tables created successfully")


def downgrade() -> None:
    """Drop Integrations module tables and enums."""

    # Drop tables (reverse order)
    op.drop_table('integration_webhooks')
    op.drop_table('integration_conflicts')
    op.drop_table('integration_sync_logs')
    op.drop_table('integration_sync_jobs')
    op.drop_table('integration_entity_mappings')
    op.drop_table('integration_connections')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS integration_entity_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS conflict_resolution CASCADE;")
    op.execute("DROP TYPE IF EXISTS sync_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS connection_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS sync_frequency CASCADE;")
    op.execute("DROP TYPE IF EXISTS sync_direction CASCADE;")
    op.execute("DROP TYPE IF EXISTS integration_auth_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS connector_type CASCADE;")

    print("[MIGRATION] Integrations module (GAP-086) tables dropped successfully")
