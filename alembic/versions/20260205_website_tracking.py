"""Website Tracking - Create analytics, leads, and demo request tables

Revision ID: website_tracking_001
Revises: contacts_unified_001
Create Date: 2026-02-05

Tables:
- website_visitors: Track anonymous visitors with session, UTM, device info
- website_leads: Capture leads from contact forms, demo requests
- demo_requests: Demo scheduling and follow-up

Ce module permet de tracker les visiteurs du site web public,
capturer les leads et gérer les demandes de démo.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'website_tracking_001'
down_revision = 'contacts_unified_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create website tracking module tables."""

    # ==========================================================================
    # ENUM TYPES
    # ==========================================================================

    # Lead Source
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE lead_source AS ENUM (
                'website_form',
                'demo_request',
                'contact_form',
                'pricing_inquiry',
                'newsletter'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Lead Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE lead_status AS ENUM (
                'new',
                'contacted',
                'qualified',
                'demo_scheduled',
                'proposal_sent',
                'won',
                'lost'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ==========================================================================
    # TABLE: website_visitors
    # ==========================================================================
    op.create_table(
        'website_visitors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', sa.String(255), nullable=False, unique=True),
        sa.Column('visitor_ip', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('referrer', sa.String(1000), nullable=True),
        sa.Column('landing_page', sa.String(500), nullable=False),
        sa.Column('current_page', sa.String(500), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('device_type', sa.String(50), nullable=True),
        sa.Column('browser', sa.String(100), nullable=True),
        sa.Column('os', sa.String(100), nullable=True),
        sa.Column('page_views', sa.Integer(), server_default='1'),
        sa.Column('time_on_site', sa.Integer(), server_default='0'),
        sa.Column('pages_visited', postgresql.JSONB(), server_default='[]'),
        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_medium', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(100), nullable=True),
        sa.Column('utm_term', sa.String(100), nullable=True),
        sa.Column('utm_content', sa.String(100), nullable=True),
        sa.Column('converted_to_lead', sa.Boolean(), server_default='false'),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('first_visit', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('last_visit', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
    )

    # Indexes for visitors
    op.create_index('idx_visitor_session', 'website_visitors', ['session_id'])
    op.create_index('idx_visitor_date', 'website_visitors', ['first_visit'])
    op.create_index('idx_visitor_converted', 'website_visitors', ['converted_to_lead'])

    # ==========================================================================
    # TABLE: website_leads
    # ==========================================================================
    op.create_table(
        'website_leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('job_title', sa.String(100), nullable=True),
        sa.Column('source', postgresql.ENUM('website_form', 'demo_request',
                  'contact_form', 'pricing_inquiry', 'newsletter',
                  name='lead_source', create_type=False),
                  server_default='website_form'),
        sa.Column('status', postgresql.ENUM('new', 'contacted', 'qualified',
                  'demo_scheduled', 'proposal_sent', 'won', 'lost',
                  name='lead_status', create_type=False),
                  server_default='new'),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('company_size', sa.String(50), nullable=True),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('visitor_session_id', sa.String(255), nullable=True),
        sa.Column('referrer_url', sa.String(1000), nullable=True),
        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(100), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_contact_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_follow_up', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('converted_to_customer', sa.Boolean(), server_default='false'),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
    )

    # Indexes for leads
    op.create_index('idx_lead_email', 'website_leads', ['email'])
    op.create_index('idx_lead_status', 'website_leads', ['status'])
    op.create_index('idx_lead_created', 'website_leads', ['created_at'])

    # ==========================================================================
    # TABLE: demo_requests
    # ==========================================================================
    op.create_table(
        'demo_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('company', sa.String(255), nullable=False),
        sa.Column('preferred_date', sa.Date(), nullable=True),
        sa.Column('preferred_time', sa.String(50), nullable=True),
        sa.Column('timezone', sa.String(50), nullable=True),
        sa.Column('modules_interested', sa.Text(), nullable=True),
        sa.Column('company_size', sa.String(50), nullable=True),
        sa.Column('current_solution', sa.String(255), nullable=True),
        sa.Column('specific_needs', sa.Text(), nullable=True),
        sa.Column('scheduled', sa.Boolean(), server_default='false'),
        sa.Column('demo_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('demo_completed', sa.Boolean(), server_default='false'),
        sa.Column('meeting_link', sa.String(500), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
    )

    # Foreign key: demo_requests -> website_leads
    op.create_foreign_key(
        'fk_demo_lead',
        'demo_requests', 'website_leads',
        ['lead_id'], ['id'],
        ondelete='SET NULL'
    )

    # Index for demos
    op.create_index('idx_demo_created', 'demo_requests', ['created_at'])


def downgrade() -> None:
    """Drop website tracking tables."""
    op.drop_table('demo_requests')
    op.drop_table('website_leads')
    op.drop_table('website_visitors')

    # Drop ENUMs
    op.execute("DROP TYPE IF EXISTS lead_status")
    op.execute("DROP TYPE IF EXISTS lead_source")
