"""Trial Registrations - Self-service trial signup workflow

Revision ID: trial_registrations_001
Revises: website_tracking_001
Create Date: 2026-02-06

Tables:
- trial_registrations: Track trial registration workflow with email verification,
  Stripe payment setup, and tenant provisioning.

Ce module permet aux utilisateurs de s'inscrire pour un essai gratuit de 30 jours
via un formulaire multi-étapes avec vérification email et enregistrement CB.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'trial_registrations_001'
down_revision = 'website_tracking_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create trial registration table and enum."""

    # ==========================================================================
    # ENUM TYPE
    # ==========================================================================

    # Trial Registration Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE trial_registration_status AS ENUM (
                'PENDING',
                'EMAIL_SENT',
                'EMAIL_VERIFIED',
                'PAYMENT_PENDING',
                'COMPLETED',
                'EXPIRED'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ==========================================================================
    # TABLE: trial_registrations
    # ==========================================================================

    op.create_table(
        'trial_registrations',
        # Primary Key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Personal Information
        sa.Column('email', sa.String(255), nullable=False, index=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('mobile', sa.String(50), nullable=True),

        # Company Information
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('address_line1', sa.String(255), nullable=False),
        sa.Column('address_line2', sa.String(255), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=False),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('country', sa.String(2), nullable=False, server_default='FR'),
        sa.Column('language', sa.String(5), nullable=False, server_default='fr'),
        sa.Column('activity', sa.String(255), nullable=True),
        sa.Column('revenue_range', sa.String(50), nullable=True),
        sa.Column('max_users', sa.Integer, nullable=False, server_default='5'),
        sa.Column('siret', sa.String(20), nullable=True),

        # Email Verification
        sa.Column('email_verification_token', sa.String(255), nullable=True, index=True),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),

        # CAPTCHA & Acceptations
        sa.Column('captcha_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('cgv_accepted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('cgu_accepted', sa.Boolean, nullable=False, server_default='false'),

        # Stripe Integration
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('stripe_setup_intent_id', sa.String(255), nullable=True),
        sa.Column('stripe_payment_method_id', sa.String(255), nullable=True),

        # Status & Workflow
        sa.Column(
            'status',
            postgresql.ENUM(
                'PENDING', 'EMAIL_SENT', 'EMAIL_VERIFIED',
                'PAYMENT_PENDING', 'COMPLETED', 'EXPIRED',
                name='trial_registration_status',
                create_type=False
            ),
            nullable=False,
            server_default='PENDING'
        ),

        # Link to created tenant (after completion)
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),

        # Security / Audit
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
    )

    # ==========================================================================
    # INDEXES
    # ==========================================================================

    # Index for email lookup (check if email already registered)
    op.create_index(
        'ix_trial_registrations_email_status',
        'trial_registrations',
        ['email', 'status']
    )

    # Index for finding pending registrations that need cleanup
    op.create_index(
        'ix_trial_registrations_status_expires',
        'trial_registrations',
        ['status', 'expires_at']
    )

    # Index for Stripe customer lookup
    op.create_index(
        'ix_trial_registrations_stripe_customer',
        'trial_registrations',
        ['stripe_customer_id'],
        postgresql_where=sa.text("stripe_customer_id IS NOT NULL")
    )


def downgrade() -> None:
    """Remove trial registration table and enum."""

    # Drop indexes
    op.drop_index('ix_trial_registrations_stripe_customer', table_name='trial_registrations')
    op.drop_index('ix_trial_registrations_status_expires', table_name='trial_registrations')
    op.drop_index('ix_trial_registrations_email_status', table_name='trial_registrations')

    # Drop table
    op.drop_table('trial_registrations')

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS trial_registration_status;")
