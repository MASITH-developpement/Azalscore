"""Module Field Service (GAP-081) - Service terrain

Revision ID: fieldservice_001
Revises: forecasting_001
Create Date: 2026-02-21

Tables:
- service_zones: Zones de service géographiques
- skills: Compétences techniques
- technicians: Techniciens terrain
- customer_sites: Sites clients
- work_orders: Ordres de travail / Interventions

Multi-tenant strict, Soft delete, Audit complet, Géolocalisation.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fieldservice_001'
down_revision = 'forecasting_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Field Service module tables and enums."""

    # ==========================================================================
    # ENUM TYPES
    # ==========================================================================

    # Work Order Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE work_order_type AS ENUM (
                'installation', 'maintenance', 'repair', 'inspection',
                'emergency', 'preventive', 'corrective', 'upgrade'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Work Order Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE work_order_status AS ENUM (
                'draft', 'scheduled', 'dispatched', 'en_route', 'on_site',
                'in_progress', 'pending_parts', 'completed', 'cancelled'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Technician Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE technician_status AS ENUM (
                'available', 'en_route', 'on_site', 'on_break', 'off_duty', 'unavailable'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Priority
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE fs_priority AS ENUM (
                'low', 'medium', 'high', 'critical', 'emergency'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Skill Level
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE skill_level AS ENUM (
                'junior', 'intermediate', 'senior', 'expert'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ==========================================================================
    # SERVICE ZONES TABLE (first for FK reference)
    # ==========================================================================

    op.create_table(
        'service_zones',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),

        # Geography
        sa.Column('polygon_coordinates', postgresql.JSONB, server_default='[]'),
        sa.Column('center_lat', sa.Numeric(10, 8), nullable=True),
        sa.Column('center_lng', sa.Numeric(11, 8), nullable=True),
        sa.Column('radius_km', sa.Numeric(8, 2), nullable=True),

        sa.Column('assigned_technicians', postgresql.JSONB, server_default='[]'),
        sa.Column('travel_time_minutes', sa.Integer, server_default='30'),

        sa.Column('is_active', sa.Boolean, server_default='true'),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Soft Delete
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column('version', sa.Integer, server_default='1'),

        # Constraints
        sa.UniqueConstraint('tenant_id', 'code', name='uq_zone_tenant_code'),
    )

    op.create_index('ix_zone_tenant', 'service_zones', ['tenant_id'])
    op.create_index('ix_zone_tenant_code', 'service_zones', ['tenant_id', 'code'])

    # ==========================================================================
    # SKILLS TABLE
    # ==========================================================================

    op.create_table(
        'skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String(100), nullable=True),

        sa.Column('certification_required', sa.Boolean, server_default='false'),
        sa.Column('certification_validity_days', sa.Integer, server_default='365'),

        sa.Column('is_active', sa.Boolean, server_default='true'),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Soft Delete
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column('version', sa.Integer, server_default='1'),

        # Constraints
        sa.UniqueConstraint('tenant_id', 'code', name='uq_skill_tenant_code'),
    )

    op.create_index('ix_skill_tenant', 'skills', ['tenant_id'])
    op.create_index('ix_skill_tenant_code', 'skills', ['tenant_id', 'code'])

    # ==========================================================================
    # TECHNICIANS TABLE
    # ==========================================================================

    op.create_table(
        'technicians',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),

        sa.Column('status', postgresql.ENUM('available', 'en_route', 'on_site', 'on_break', 'off_duty', 'unavailable', name='technician_status', create_type=False), nullable=False, server_default='available'),

        # Geolocation
        sa.Column('current_location_lat', sa.Numeric(10, 8), nullable=True),
        sa.Column('current_location_lng', sa.Numeric(11, 8), nullable=True),
        sa.Column('last_location_update', sa.DateTime, nullable=True),

        # Configuration
        sa.Column('home_zone_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('service_zones.id'), nullable=True),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('max_daily_work_orders', sa.Integer, server_default='8'),

        # Rates
        sa.Column('hourly_rate', sa.Numeric(10, 2), server_default='0'),
        sa.Column('overtime_rate', sa.Numeric(10, 2), server_default='0'),

        # Skills (JSON)
        sa.Column('skills', postgresql.JSONB, server_default='[]'),

        sa.Column('is_active', sa.Boolean, server_default='true'),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Soft Delete
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column('version', sa.Integer, server_default='1'),

        # Constraints
        sa.UniqueConstraint('tenant_id', 'code', name='uq_tech_tenant_code'),
    )

    op.create_index('ix_tech_tenant', 'technicians', ['tenant_id'])
    op.create_index('ix_tech_tenant_code', 'technicians', ['tenant_id', 'code'])
    op.create_index('ix_tech_tenant_status', 'technicians', ['tenant_id', 'status'])

    # ==========================================================================
    # CUSTOMER SITES TABLE
    # ==========================================================================

    op.create_table(
        'customer_sites',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),

        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('customer_name', sa.String(255), nullable=True),

        # Address
        sa.Column('address_line1', sa.String(255), nullable=False),
        sa.Column('address_line2', sa.String(255), nullable=True),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('postal_code', sa.String(20), nullable=False),
        sa.Column('country', sa.String(100), server_default='France'),

        # Geolocation
        sa.Column('latitude', sa.Numeric(10, 8), nullable=True),
        sa.Column('longitude', sa.Numeric(11, 8), nullable=True),

        # Contact
        sa.Column('contact_name', sa.String(255), nullable=True),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),

        # Instructions
        sa.Column('access_instructions', sa.Text, nullable=True),
        sa.Column('special_requirements', sa.Text, nullable=True),

        sa.Column('equipment_list', postgresql.JSONB, server_default='[]'),
        sa.Column('zone_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('service_zones.id'), nullable=True),

        sa.Column('is_active', sa.Boolean, server_default='true'),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Soft Delete
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column('version', sa.Integer, server_default='1'),

        # Constraints
        sa.UniqueConstraint('tenant_id', 'code', name='uq_site_tenant_code'),
    )

    op.create_index('ix_site_tenant', 'customer_sites', ['tenant_id'])
    op.create_index('ix_site_tenant_code', 'customer_sites', ['tenant_id', 'code'])
    op.create_index('ix_site_tenant_customer', 'customer_sites', ['tenant_id', 'customer_id'])

    # ==========================================================================
    # WORK ORDERS TABLE
    # ==========================================================================

    op.create_table(
        'work_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),

        # Type and status
        sa.Column('work_order_type', postgresql.ENUM('installation', 'maintenance', 'repair', 'inspection', 'emergency', 'preventive', 'corrective', 'upgrade', name='work_order_type', create_type=False), nullable=False, server_default='maintenance'),
        sa.Column('status', postgresql.ENUM('draft', 'scheduled', 'dispatched', 'en_route', 'on_site', 'in_progress', 'pending_parts', 'completed', 'cancelled', name='work_order_status', create_type=False), nullable=False, server_default='draft'),
        sa.Column('priority', postgresql.ENUM('low', 'medium', 'high', 'critical', 'emergency', name='fs_priority', create_type=False), nullable=False, server_default='medium'),

        # Relations
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('customer_name', sa.String(255), nullable=True),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customer_sites.id'), nullable=True),
        sa.Column('technician_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('technicians.id'), nullable=True),

        # Scheduling
        sa.Column('scheduled_date', sa.Date, nullable=True),
        sa.Column('scheduled_start_time', sa.DateTime, nullable=True),
        sa.Column('scheduled_end_time', sa.DateTime, nullable=True),
        sa.Column('estimated_duration_minutes', sa.Integer, server_default='60'),

        # Execution
        sa.Column('actual_start_time', sa.DateTime, nullable=True),
        sa.Column('actual_end_time', sa.DateTime, nullable=True),
        sa.Column('actual_duration_minutes', sa.Integer, nullable=True),

        # Details
        sa.Column('lines', postgresql.JSONB, server_default='[]'),
        sa.Column('parts_used', postgresql.JSONB, server_default='[]'),
        sa.Column('labor_entries', postgresql.JSONB, server_default='[]'),

        # Result
        sa.Column('resolution_notes', sa.Text, nullable=True),
        sa.Column('customer_signature', sa.Text, nullable=True),
        sa.Column('technician_signature', sa.Text, nullable=True),
        sa.Column('photos', postgresql.JSONB, server_default='[]'),

        # Billing
        sa.Column('billable', sa.Boolean, server_default='true'),
        sa.Column('labor_total', sa.Numeric(12, 2), server_default='0'),
        sa.Column('parts_total', sa.Numeric(12, 2), server_default='0'),
        sa.Column('total_amount', sa.Numeric(12, 2), server_default='0'),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=True),

        # SLA
        sa.Column('sla_due_date', sa.DateTime, nullable=True),
        sa.Column('sla_met', sa.Boolean, nullable=True),

        sa.Column('tags', postgresql.JSONB, server_default='[]'),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Soft Delete
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column('version', sa.Integer, server_default='1'),

        # Constraints
        sa.UniqueConstraint('tenant_id', 'code', name='uq_wo_tenant_code'),
    )

    op.create_index('ix_wo_tenant', 'work_orders', ['tenant_id'])
    op.create_index('ix_wo_tenant_code', 'work_orders', ['tenant_id', 'code'])
    op.create_index('ix_wo_tenant_status', 'work_orders', ['tenant_id', 'status'])
    op.create_index('ix_wo_tenant_date', 'work_orders', ['tenant_id', 'scheduled_date'])
    op.create_index('ix_wo_tenant_customer', 'work_orders', ['tenant_id', 'customer_id'])
    op.create_index('ix_wo_tenant_technician', 'work_orders', ['tenant_id', 'technician_id'])

    print("[MIGRATION] Field Service module (GAP-081) tables created successfully")


def downgrade() -> None:
    """Drop Field Service module tables and enums."""

    # Drop tables (reverse order)
    op.drop_table('work_orders')
    op.drop_table('customer_sites')
    op.drop_table('technicians')
    op.drop_table('skills')
    op.drop_table('service_zones')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS skill_level CASCADE;")
    op.execute("DROP TYPE IF EXISTS fs_priority CASCADE;")
    op.execute("DROP TYPE IF EXISTS technician_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS work_order_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS work_order_type CASCADE;")

    print("[MIGRATION] Field Service module (GAP-081) tables dropped successfully")
