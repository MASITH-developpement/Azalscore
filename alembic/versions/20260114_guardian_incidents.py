"""GUARDIAN: Add incidents and daily reports tables

Revision ID: guardian_incidents_001
Revises:
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'guardian_incidents_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create guardian_incidents and guardian_daily_reports tables."""

    # Table guardian_incidents
    op.create_table(
        'guardian_incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('incident_uid', sa.String(36), nullable=False),
        sa.Column('tenant_id', sa.String(255), nullable=False),

        # Classification
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),

        # Contexte utilisateur
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_role', sa.String(50), nullable=True),

        # Localisation
        sa.Column('page', sa.String(500), nullable=False),
        sa.Column('route', sa.String(500), nullable=False),

        # HTTP
        sa.Column('endpoint', sa.String(500), nullable=True),
        sa.Column('method', sa.String(10), nullable=True),
        sa.Column('http_status', sa.Integer(), nullable=True),

        # Détails
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('stack_trace', sa.Text(), nullable=True),

        # Screenshot
        sa.Column('screenshot_path', sa.String(500), nullable=True),
        sa.Column('has_screenshot', sa.Boolean(), nullable=False, default=False),

        # Timestamp frontend
        sa.Column('frontend_timestamp', sa.DateTime(), nullable=False),

        # Guardian actions
        sa.Column('guardian_actions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Statut
        sa.Column('is_processed', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, default=False),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),

        # Lien
        sa.Column('error_detection_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('incident_uid'),
    )

    # Index pour guardian_incidents
    op.create_index('idx_guardian_incidents_tenant_created', 'guardian_incidents', ['tenant_id', 'created_at'])
    op.create_index('idx_guardian_incidents_severity_type', 'guardian_incidents', ['severity', 'type'])
    op.create_index('idx_guardian_incidents_unprocessed', 'guardian_incidents', ['is_processed', 'created_at'])
    op.create_index('idx_guardian_incidents_incident_uid', 'guardian_incidents', ['incident_uid'])

    # Table guardian_daily_reports
    op.create_table(
        'guardian_daily_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_uid', sa.String(36), nullable=False),
        sa.Column('tenant_id', sa.String(255), nullable=False),

        # Période
        sa.Column('report_date', sa.DateTime(), nullable=False),

        # Statistiques incidents
        sa.Column('total_incidents', sa.Integer(), nullable=False, default=0),
        sa.Column('incidents_by_type', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('incidents_by_severity', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Statistiques corrections
        sa.Column('total_corrections', sa.Integer(), nullable=False, default=0),
        sa.Column('successful_corrections', sa.Integer(), nullable=False, default=0),
        sa.Column('failed_corrections', sa.Integer(), nullable=False, default=0),
        sa.Column('rollbacks', sa.Integer(), nullable=False, default=0),

        # Actions Guardian
        sa.Column('guardian_actions_count', sa.Integer(), nullable=False, default=0),
        sa.Column('guardian_actions_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Pages impactées
        sa.Column('affected_pages', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Contenu
        sa.Column('report_content', sa.Text(), nullable=True),

        # Métadonnées
        sa.Column('generated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('sent_to', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('report_uid'),
    )

    # Index pour guardian_daily_reports
    op.create_index('idx_guardian_reports_tenant_date', 'guardian_daily_reports', ['tenant_id', 'report_date'])
    op.create_index('idx_guardian_reports_report_uid', 'guardian_daily_reports', ['report_uid'])


def downgrade() -> None:
    """Remove guardian_incidents and guardian_daily_reports tables."""

    # Drop indexes
    op.drop_index('idx_guardian_reports_report_uid', table_name='guardian_daily_reports')
    op.drop_index('idx_guardian_reports_tenant_date', table_name='guardian_daily_reports')
    op.drop_index('idx_guardian_incidents_incident_uid', table_name='guardian_incidents')
    op.drop_index('idx_guardian_incidents_unprocessed', table_name='guardian_incidents')
    op.drop_index('idx_guardian_incidents_severity_type', table_name='guardian_incidents')
    op.drop_index('idx_guardian_incidents_tenant_created', table_name='guardian_incidents')

    # Drop tables
    op.drop_table('guardian_daily_reports')
    op.drop_table('guardian_incidents')
