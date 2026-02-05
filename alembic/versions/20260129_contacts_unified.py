"""MODULE Contacts Unifiés - Create unified contacts tables

Revision ID: contacts_unified_001
Revises: interventions_business_001
Create Date: 2026-01-29

Tables:
- contact_sequences: Séquences de numérotation par tenant/année
- contacts: Contacts unifiés (Client ET/OU Fournisseur)
- contact_persons: Personnes de contact (Commercial, Comptabilité, etc.)
- contact_addresses: Adresses multiples (Facturation, Livraison, Chantier)

Ce module remplace à terme customers et purchases_suppliers par une
fiche contact unifiée qui peut être à la fois Client et Fournisseur.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'contacts_unified_001'
down_revision = 'interventions_biz_v2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create unified contacts module tables."""

    # ==========================================================================
    # ENUM TYPES
    # ==========================================================================

    # Type d'entité (Particulier / Société)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE contact_entity_type AS ENUM ('INDIVIDUAL', 'COMPANY');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Type d'adresse
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE contact_address_type AS ENUM ('BILLING', 'SHIPPING', 'SITE', 'HEAD_OFFICE', 'OTHER');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Rôle de personne de contact
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE contact_person_role AS ENUM (
                'MANAGER', 'COMMERCIAL', 'ACCOUNTING', 'BUYER',
                'TECHNICAL', 'ADMINISTRATIVE', 'LOGISTICS', 'OTHER'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Type de client (CRM)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE contact_customer_type AS ENUM (
                'PROSPECT', 'LEAD', 'CUSTOMER', 'VIP', 'PARTNER', 'CHURNED'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Statut fournisseur
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE contact_supplier_status AS ENUM (
                'PROSPECT', 'PENDING', 'APPROVED', 'BLOCKED', 'INACTIVE'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Type de fournisseur
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE contact_supplier_type AS ENUM (
                'GOODS', 'SERVICES', 'BOTH', 'RAW_MATERIALS', 'EQUIPMENT'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ==========================================================================
    # Table contact_sequences - Numérotation automatique
    # ==========================================================================
    op.create_table(
        'contact_sequences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('last_number', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'year', name='uq_contact_seq_tenant_year'),
    )
    op.create_index('idx_contact_seq_tenant_year', 'contact_sequences', ['tenant_id', 'year'])

    # ==========================================================================
    # Table contacts - Fiche contact unifiée
    # ==========================================================================
    op.create_table(
        'contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),

        # Code auto-généré (CONT-YYYY-XXXX)
        sa.Column('code', sa.String(20), nullable=False),

        # Type d'entité (Particulier / Société) - exclusif
        sa.Column('entity_type', postgresql.ENUM('INDIVIDUAL', 'COMPANY', name='contact_entity_type', create_type=False),
                  nullable=False, server_default='COMPANY'),

        # Types de relation (Client / Fournisseur) - multiple via JSONB
        sa.Column('relation_types', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),

        # ===== IDENTIFICATION =====
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('legal_name', sa.String(255), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),

        # ===== COORDONNEES =====
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('mobile', sa.String(50), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),

        # ===== INFORMATIONS LEGALES =====
        sa.Column('tax_id', sa.String(50), nullable=True),
        sa.Column('registration_number', sa.String(50), nullable=True),
        sa.Column('legal_form', sa.String(50), nullable=True),

        # ===== LOGO =====
        sa.Column('logo_url', sa.String(500), nullable=True),

        # ===== CONDITIONS CLIENT =====
        sa.Column('customer_type', postgresql.ENUM(
            'PROSPECT', 'LEAD', 'CUSTOMER', 'VIP', 'PARTNER', 'CHURNED',
            name='contact_customer_type', create_type=False
        ), nullable=True, server_default='PROSPECT'),
        sa.Column('customer_payment_terms', sa.String(50), nullable=True),
        sa.Column('customer_payment_method', sa.String(50), nullable=True),
        sa.Column('customer_credit_limit', sa.Numeric(15, 2), nullable=True),
        sa.Column('customer_discount_rate', sa.Numeric(5, 2), nullable=True, server_default='0'),
        sa.Column('customer_currency', sa.String(3), server_default='EUR'),

        # CRM
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('segment', sa.String(50), nullable=True),
        sa.Column('lead_score', sa.Integer(), server_default='0'),
        sa.Column('health_score', sa.Integer(), server_default='100'),

        # Statistiques client
        sa.Column('customer_total_revenue', sa.Numeric(15, 2), server_default='0'),
        sa.Column('customer_order_count', sa.Integer(), server_default='0'),
        sa.Column('customer_last_order_date', sa.DateTime(), nullable=True),
        sa.Column('customer_first_order_date', sa.DateTime(), nullable=True),

        # ===== CONDITIONS FOURNISSEUR =====
        sa.Column('supplier_status', postgresql.ENUM(
            'PROSPECT', 'PENDING', 'APPROVED', 'BLOCKED', 'INACTIVE',
            name='contact_supplier_status', create_type=False
        ), nullable=True, server_default='PROSPECT'),
        sa.Column('supplier_type', postgresql.ENUM(
            'GOODS', 'SERVICES', 'BOTH', 'RAW_MATERIALS', 'EQUIPMENT',
            name='contact_supplier_type', create_type=False
        ), nullable=True, server_default='BOTH'),
        sa.Column('supplier_payment_terms', sa.String(100), nullable=True),
        sa.Column('supplier_currency', sa.String(3), server_default='EUR'),
        sa.Column('supplier_credit_limit', sa.Numeric(15, 2), nullable=True),
        sa.Column('supplier_category', sa.String(100), nullable=True),

        # Statistiques fournisseur
        sa.Column('supplier_total_purchases', sa.Numeric(15, 2), server_default='0'),
        sa.Column('supplier_order_count', sa.Integer(), server_default='0'),
        sa.Column('supplier_last_order_date', sa.DateTime(), nullable=True),

        # ===== CLASSIFICATION =====
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), server_default='[]'),

        # ===== NOTES =====
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),

        # ===== METADONNEES =====
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
    )

    # Index sur contacts
    op.create_index('idx_contacts_tenant_id', 'contacts', ['tenant_id'])
    op.create_index('idx_contacts_tenant_code', 'contacts', ['tenant_id', 'code'], unique=True)
    op.create_index('idx_contacts_tenant_name', 'contacts', ['tenant_id', 'name'])
    op.create_index('idx_contacts_tenant_email', 'contacts', ['tenant_id', 'email'])
    op.create_index('idx_contacts_tenant_entity_type', 'contacts', ['tenant_id', 'entity_type'])
    op.create_index('idx_contacts_tenant_active', 'contacts', ['tenant_id', 'is_active'])
    op.create_index('idx_contacts_relation_types', 'contacts', ['relation_types'], postgresql_using='gin')
    op.create_index('idx_contacts_tags', 'contacts', ['tags'], postgresql_using='gin')

    # ==========================================================================
    # Table contact_persons - Personnes de contact
    # ==========================================================================
    op.create_table(
        'contact_persons',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Rôle
        sa.Column('role', postgresql.ENUM(
            'MANAGER', 'COMMERCIAL', 'ACCOUNTING', 'BUYER',
            'TECHNICAL', 'ADMINISTRATIVE', 'LOGISTICS', 'OTHER',
            name='contact_person_role', create_type=False
        ), server_default='OTHER'),
        sa.Column('custom_role', sa.String(100), nullable=True),

        # Identité
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('job_title', sa.String(100), nullable=True),

        # Coordonnées
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('mobile', sa.String(50), nullable=True),

        # Statut
        sa.Column('is_primary', sa.Boolean(), server_default='false'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Métadonnées
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
    )

    # Index sur contact_persons
    op.create_index('idx_contact_persons_tenant_id', 'contact_persons', ['tenant_id'])
    op.create_index('idx_contact_persons_tenant_contact', 'contact_persons', ['tenant_id', 'contact_id'])
    op.create_index('idx_contact_persons_role', 'contact_persons', ['contact_id', 'role'])

    # ==========================================================================
    # Table contact_addresses - Adresses de contact
    # ==========================================================================
    op.create_table(
        'contact_addresses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Type et libellé
        sa.Column('address_type', postgresql.ENUM(
            'BILLING', 'SHIPPING', 'SITE', 'HEAD_OFFICE', 'OTHER',
            name='contact_address_type', create_type=False
        ), nullable=False, server_default='BILLING'),
        sa.Column('label', sa.String(100), nullable=True),

        # Adresse
        sa.Column('address_line1', sa.String(255), nullable=True),
        sa.Column('address_line2', sa.String(255), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('country_code', sa.String(3), server_default='FR'),

        # Coordonnées GPS
        sa.Column('latitude', sa.Numeric(10, 7), nullable=True),
        sa.Column('longitude', sa.Numeric(10, 7), nullable=True),

        # Contact sur site
        sa.Column('contact_name', sa.String(255), nullable=True),
        sa.Column('contact_phone', sa.String(50), nullable=True),

        # Statut
        sa.Column('is_default', sa.Boolean(), server_default='false'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Métadonnées
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
    )

    # Index sur contact_addresses
    op.create_index('idx_contact_addresses_tenant_id', 'contact_addresses', ['tenant_id'])
    op.create_index('idx_contact_addresses_tenant_contact', 'contact_addresses', ['tenant_id', 'contact_id'])
    op.create_index('idx_contact_addresses_type', 'contact_addresses', ['contact_id', 'address_type'])
    op.create_index('idx_contact_addresses_default', 'contact_addresses', ['contact_id', 'address_type', 'is_default'])


def downgrade() -> None:
    """Drop unified contacts module tables."""

    # Supprimer les tables dans l'ordre inverse (enfants d'abord)
    op.drop_table('contact_addresses')
    op.drop_table('contact_persons')
    op.drop_table('contacts')
    op.drop_table('contact_sequences')

    # Supprimer les types ENUM
    op.execute('DROP TYPE IF EXISTS contact_supplier_type CASCADE')
    op.execute('DROP TYPE IF EXISTS contact_supplier_status CASCADE')
    op.execute('DROP TYPE IF EXISTS contact_customer_type CASCADE')
    op.execute('DROP TYPE IF EXISTS contact_person_role CASCADE')
    op.execute('DROP TYPE IF EXISTS contact_address_type CASCADE')
    op.execute('DROP TYPE IF EXISTS contact_entity_type CASCADE')
