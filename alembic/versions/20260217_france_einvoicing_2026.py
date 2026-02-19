"""
France E-Invoicing 2026 Module

Revision ID: 20260217_einvoicing
Revises: 20260215_workflow_approval
Create Date: 2026-02-17

Tables créées:
- einvoice_pdp_configs: Configuration PDP par tenant
- einvoice_records: Factures électroniques
- einvoice_lifecycle_events: Événements cycle de vie
- ereporting_submissions: Soumissions e-reporting B2C
- einvoice_stats: Statistiques par tenant/période
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '20260217_einvoicing'
down_revision = '20260215_workflow'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # ENUMS
    # ==========================================================================
    pdp_provider_type = postgresql.ENUM(
        'chorus_pro', 'ppf', 'yooz', 'docaposte', 'sage', 'cegid',
        'generix', 'edicom', 'basware', 'custom',
        name='pdpprovidertype'
    )
    pdp_provider_type.create(op.get_bind(), checkfirst=True)

    einvoice_status = postgresql.ENUM(
        'DRAFT', 'VALIDATED', 'SENT', 'DELIVERED', 'RECEIVED',
        'ACCEPTED', 'REFUSED', 'PAID', 'ERROR', 'CANCELLED',
        name='einvoicestatusdb'
    )
    einvoice_status.create(op.get_bind(), checkfirst=True)

    einvoice_direction = postgresql.ENUM(
        'OUTBOUND', 'INBOUND',
        name='einvoicedirection'
    )
    einvoice_direction.create(op.get_bind(), checkfirst=True)

    einvoice_format = postgresql.ENUM(
        'FACTURX_MINIMUM', 'FACTURX_BASIC', 'FACTURX_EN16931',
        'FACTURX_EXTENDED', 'UBL_21', 'CII_D16B',
        name='einvoiceformatdb'
    )
    einvoice_format.create(op.get_bind(), checkfirst=True)

    company_size_type = postgresql.ENUM(
        'GE', 'ETI', 'PME', 'MICRO',
        name='companysizetype'
    )
    company_size_type.create(op.get_bind(), checkfirst=True)

    # ==========================================================================
    # TABLE: einvoice_pdp_configs
    # ==========================================================================
    op.create_table(
        'einvoice_pdp_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),

        # Provider
        sa.Column('provider', postgresql.ENUM('chorus_pro', 'ppf', 'yooz', 'docaposte', 'sage', 'cegid', 'generix', 'edicom', 'basware', 'custom', name='pdpprovidertype', create_type=False), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),

        # Credentials
        sa.Column('api_url', sa.String(500), nullable=False),
        sa.Column('token_url', sa.String(500)),
        sa.Column('client_id', sa.String(255)),
        sa.Column('client_secret', sa.String(500)),
        sa.Column('scope', sa.String(255)),

        # Certificats
        sa.Column('certificate_ref', sa.String(255)),
        sa.Column('private_key_ref', sa.String(255)),

        # Identifiants entreprise
        sa.Column('siret', sa.String(14)),
        sa.Column('siren', sa.String(9)),
        sa.Column('tva_number', sa.String(20)),
        sa.Column('company_size', postgresql.ENUM('GE', 'ETI', 'PME', 'MICRO', name='companysizetype', create_type=False), default='PME'),

        # Configuration
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('test_mode', sa.Boolean, default=True),
        sa.Column('timeout_seconds', sa.Integer, default=30),
        sa.Column('retry_count', sa.Integer, default=3),

        # Webhook
        sa.Column('webhook_url', sa.String(500)),
        sa.Column('webhook_secret', sa.String(255)),

        # Options
        sa.Column('provider_options', postgresql.JSON, default={}),
        sa.Column('custom_endpoints', postgresql.JSON, default={}),

        # Format
        sa.Column('preferred_format', postgresql.ENUM('FACTURX_MINIMUM', 'FACTURX_BASIC', 'FACTURX_EN16931', 'FACTURX_EXTENDED', 'UBL_21', 'CII_D16B', name='einvoiceformatdb', create_type=False), default='FACTURX_EN16931'),
        sa.Column('generate_pdf', sa.Boolean, default=True),

        # Métadonnées
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_sync_at', sa.DateTime),
    )

    # Indexes
    op.create_index('ix_pdp_configs_tenant', 'einvoice_pdp_configs', ['tenant_id'])
    op.create_index('ix_pdp_configs_tenant_provider', 'einvoice_pdp_configs', ['tenant_id', 'provider'])
    op.create_index('ix_pdp_configs_tenant_default', 'einvoice_pdp_configs', ['tenant_id', 'is_default'])

    # Unique constraint
    op.create_unique_constraint('uq_pdp_config_tenant_name', 'einvoice_pdp_configs', ['tenant_id', 'name'])

    # ==========================================================================
    # TABLE: einvoice_records
    # ==========================================================================
    op.create_table(
        'einvoice_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('pdp_config_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('einvoice_pdp_configs.id')),

        # Direction
        sa.Column('direction', postgresql.ENUM('OUTBOUND', 'INBOUND', name='einvoicedirection', create_type=False), nullable=False),

        # Identification
        sa.Column('invoice_number', sa.String(100), nullable=False),
        sa.Column('invoice_type', sa.String(10), default='380'),
        sa.Column('format', postgresql.ENUM('FACTURX_MINIMUM', 'FACTURX_BASIC', 'FACTURX_EN16931', 'FACTURX_EXTENDED', 'UBL_21', 'CII_D16B', name='einvoiceformatdb', create_type=False), default='FACTURX_EN16931'),

        # Références
        sa.Column('transaction_id', sa.String(100)),
        sa.Column('ppf_id', sa.String(100)),
        sa.Column('pdp_id', sa.String(100)),

        # Lien source
        sa.Column('source_invoice_id', postgresql.UUID(as_uuid=True)),
        sa.Column('source_type', sa.String(50)),

        # Dates
        sa.Column('issue_date', sa.Date, nullable=False),
        sa.Column('due_date', sa.Date),
        sa.Column('submission_date', sa.DateTime),
        sa.Column('reception_date', sa.DateTime),

        # Parties
        sa.Column('seller_siret', sa.String(14)),
        sa.Column('seller_name', sa.String(255)),
        sa.Column('seller_tva', sa.String(20)),
        sa.Column('buyer_siret', sa.String(14)),
        sa.Column('buyer_name', sa.String(255)),
        sa.Column('buyer_tva', sa.String(20)),
        sa.Column('buyer_routing_id', sa.String(100)),

        # Montants
        sa.Column('currency', sa.String(3), default='EUR'),
        sa.Column('total_ht', sa.Numeric(15, 2), default=0),
        sa.Column('total_tva', sa.Numeric(15, 2), default=0),
        sa.Column('total_ttc', sa.Numeric(15, 2), default=0),
        sa.Column('vat_breakdown', postgresql.JSON, default={}),

        # Statut
        sa.Column('status', postgresql.ENUM('DRAFT', 'VALIDATED', 'SENT', 'DELIVERED', 'RECEIVED', 'ACCEPTED', 'REFUSED', 'PAID', 'ERROR', 'CANCELLED', name='einvoicestatusdb', create_type=False), default='DRAFT'),
        sa.Column('lifecycle_status', sa.String(50)),

        # Contenu
        sa.Column('xml_content', sa.Text),
        sa.Column('xml_hash', sa.String(64)),
        sa.Column('pdf_storage_ref', sa.String(500)),

        # Validation
        sa.Column('validation_errors', postgresql.JSON, default=[]),
        sa.Column('validation_warnings', postgresql.JSON, default=[]),
        sa.Column('is_valid', sa.Boolean, default=False),

        # Erreurs
        sa.Column('last_error', sa.Text),
        sa.Column('error_count', sa.Integer, default=0),

        # Métadonnées
        sa.Column('extra_data', postgresql.JSON, default={}),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes
    op.create_index('ix_einvoice_tenant', 'einvoice_records', ['tenant_id'])
    op.create_index('ix_einvoice_tenant_number', 'einvoice_records', ['tenant_id', 'invoice_number'])
    op.create_index('ix_einvoice_tenant_status', 'einvoice_records', ['tenant_id', 'status'])
    op.create_index('ix_einvoice_tenant_direction', 'einvoice_records', ['tenant_id', 'direction'])
    op.create_index('ix_einvoice_tenant_date', 'einvoice_records', ['tenant_id', 'issue_date'])
    op.create_index('ix_einvoice_ppf_id', 'einvoice_records', ['ppf_id'])
    op.create_index('ix_einvoice_pdp_id', 'einvoice_records', ['pdp_id'])
    op.create_index('ix_einvoice_source', 'einvoice_records', ['source_type', 'source_invoice_id'])

    # ==========================================================================
    # TABLE: einvoice_lifecycle_events
    # ==========================================================================
    op.create_table(
        'einvoice_lifecycle_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('einvoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('einvoice_records.id', ondelete='CASCADE'), nullable=False),

        # Événement
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('actor', sa.String(100)),
        sa.Column('message', sa.Text),
        sa.Column('details', postgresql.JSON, default={}),
        sa.Column('source', sa.String(50)),
    )

    # Indexes
    op.create_index('ix_lifecycle_tenant', 'einvoice_lifecycle_events', ['tenant_id'])
    op.create_index('ix_lifecycle_einvoice', 'einvoice_lifecycle_events', ['einvoice_id'])
    op.create_index('ix_lifecycle_timestamp', 'einvoice_lifecycle_events', ['timestamp'])

    # ==========================================================================
    # TABLE: ereporting_submissions
    # ==========================================================================
    op.create_table(
        'ereporting_submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('pdp_config_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('einvoice_pdp_configs.id')),

        # Période
        sa.Column('period', sa.String(7), nullable=False),
        sa.Column('reporting_type', sa.String(50), nullable=False),

        # Identifiants
        sa.Column('submission_id', sa.String(100)),
        sa.Column('ppf_reference', sa.String(100)),

        # Totaux
        sa.Column('total_ht', sa.Numeric(15, 2), default=0),
        sa.Column('total_tva', sa.Numeric(15, 2), default=0),
        sa.Column('total_ttc', sa.Numeric(15, 2), default=0),
        sa.Column('transaction_count', sa.Integer, default=0),
        sa.Column('vat_breakdown', postgresql.JSON, default={}),

        # Statut
        sa.Column('status', sa.String(50), default='DRAFT'),
        sa.Column('submitted_at', sa.DateTime),
        sa.Column('response_at', sa.DateTime),

        # Erreurs
        sa.Column('errors', postgresql.JSON, default=[]),

        # Métadonnées
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes
    op.create_index('ix_ereporting_tenant', 'ereporting_submissions', ['tenant_id'])
    op.create_index('ix_ereporting_tenant_period', 'ereporting_submissions', ['tenant_id', 'period'])

    # Unique constraint
    op.create_unique_constraint('uq_ereporting_period', 'ereporting_submissions', ['tenant_id', 'period', 'reporting_type'])

    # ==========================================================================
    # TABLE: einvoice_stats
    # ==========================================================================
    op.create_table(
        'einvoice_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),

        # Période
        sa.Column('period', sa.String(7), nullable=False),

        # Compteurs émission
        sa.Column('outbound_total', sa.Integer, default=0),
        sa.Column('outbound_sent', sa.Integer, default=0),
        sa.Column('outbound_delivered', sa.Integer, default=0),
        sa.Column('outbound_accepted', sa.Integer, default=0),
        sa.Column('outbound_refused', sa.Integer, default=0),
        sa.Column('outbound_errors', sa.Integer, default=0),

        # Compteurs réception
        sa.Column('inbound_total', sa.Integer, default=0),
        sa.Column('inbound_received', sa.Integer, default=0),
        sa.Column('inbound_accepted', sa.Integer, default=0),
        sa.Column('inbound_refused', sa.Integer, default=0),

        # Montants
        sa.Column('outbound_amount_ttc', sa.Numeric(18, 2), default=0),
        sa.Column('inbound_amount_ttc', sa.Numeric(18, 2), default=0),

        # e-reporting
        sa.Column('ereporting_submitted', sa.Integer, default=0),
        sa.Column('ereporting_amount', sa.Numeric(18, 2), default=0),

        # Mise à jour
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes
    op.create_index('ix_einvoice_stats_tenant', 'einvoice_stats', ['tenant_id'])

    # Unique constraint
    op.create_unique_constraint('uq_einvoice_stats_period', 'einvoice_stats', ['tenant_id', 'period'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('einvoice_stats')
    op.drop_table('ereporting_submissions')
    op.drop_table('einvoice_lifecycle_events')
    op.drop_table('einvoice_records')
    op.drop_table('einvoice_pdp_configs')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS companysizetype')
    op.execute('DROP TYPE IF EXISTS einvoiceformatdb')
    op.execute('DROP TYPE IF EXISTS einvoicedirection')
    op.execute('DROP TYPE IF EXISTS einvoicestatusdb')
    op.execute('DROP TYPE IF EXISTS pdpprovidertype')
