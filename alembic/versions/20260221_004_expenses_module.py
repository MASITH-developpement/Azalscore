"""Module Expenses (GAP-084) - Gestion des notes de frais

Revision ID: expenses_001
Revises: approval_001
Create Date: 2026-02-21

Tables:
- expense_policies: Politiques de dépenses
- expense_mileage_rates: Barèmes kilométriques (URSSAF)
- expense_employee_vehicles: Véhicules employés
- expense_reports: Notes de frais
- expense_lines: Lignes de dépenses

Multi-tenant strict, Audit complet, Conformité URSSAF.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'expenses_001'
down_revision = 'approval_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Expenses module tables and enums."""

    # ==========================================================================
    # ENUM TYPES
    # ==========================================================================

    # Expense Category
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE expense_category AS ENUM (
                'mileage', 'public_transport', 'taxi', 'parking', 'toll', 'rental_car', 'fuel',
                'hotel', 'airbnb', 'restaurant', 'meal_solo', 'meal_business', 'meal_team',
                'flight', 'train', 'visa', 'travel_insurance',
                'phone', 'internet', 'office_supplies', 'it_equipment', 'books',
                'representation', 'subscription', 'other'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Expense Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE expense_status AS ENUM (
                'draft', 'submitted', 'pending_approval', 'approved', 'rejected', 'paid', 'cancelled'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Payment Method
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE expense_payment_method AS ENUM (
                'personal_card', 'company_card', 'cash', 'company_account', 'mileage'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Vehicle Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE expense_vehicle_type AS ENUM (
                'car_3cv', 'car_4cv', 'car_5cv', 'car_6cv', 'car_7cv_plus',
                'moto_50cc', 'moto_125cc', 'moto_3_5cv', 'moto_5cv_plus',
                'bicycle', 'electric_bicycle'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ==========================================================================
    # EXPENSE POLICIES TABLE
    # ==========================================================================

    op.create_table(
        'expense_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),

        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_default', sa.Boolean, server_default='false'),
        sa.Column('is_active', sa.Boolean, server_default='true'),

        # Category limits (JSON)
        sa.Column('category_limits', postgresql.JSONB, server_default='{}'),

        # General limits
        sa.Column('single_expense_limit', sa.Numeric(18, 4), server_default='500'),
        sa.Column('daily_limit', sa.Numeric(18, 4), server_default='200'),
        sa.Column('monthly_limit', sa.Numeric(18, 4), server_default='2000'),

        # Receipt rules
        sa.Column('receipt_required_above', sa.Numeric(18, 4), server_default='10'),
        sa.Column('receipt_required_categories', postgresql.JSONB, server_default='[]'),

        # Meal rules
        sa.Column('meal_solo_limit', sa.Numeric(18, 4), server_default='20.20'),
        sa.Column('meal_business_limit', sa.Numeric(18, 4), server_default='50'),
        sa.Column('meal_require_guests', sa.Boolean, server_default='true'),

        # Transport rules
        sa.Column('mileage_max_daily_km', sa.Numeric(10, 2), server_default='500'),
        sa.Column('require_train_over_km', sa.Numeric(10, 2), server_default='300'),

        # Approval thresholds (JSON)
        sa.Column('approval_thresholds', postgresql.JSONB, server_default='{}'),

        # Blocked categories (JSON)
        sa.Column('blocked_categories', postgresql.JSONB, server_default='[]'),

        # Advanced rules (JSON)
        sa.Column('rules', postgresql.JSONB, server_default='[]'),

        # Audit
        sa.Column('version', sa.Integer, server_default='1'),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_index('ix_expense_policies_tenant_code', 'expense_policies', ['tenant_id', 'code'], unique=True)
    op.create_index('ix_expense_policies_tenant_default', 'expense_policies', ['tenant_id', 'is_default'])

    # ==========================================================================
    # EXPENSE MILEAGE RATES TABLE
    # ==========================================================================

    op.create_table(
        'expense_mileage_rates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),

        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('vehicle_type', sa.String(30), nullable=False),

        # Rates by tier
        sa.Column('rate_up_to_5000', sa.Numeric(6, 4), nullable=True),
        sa.Column('rate_5001_to_20000', sa.Numeric(6, 4), nullable=True),
        sa.Column('fixed_5001_to_20000', sa.Numeric(10, 2), nullable=True),
        sa.Column('rate_above_20000', sa.Numeric(6, 4), nullable=True),

        # For bicycles
        sa.Column('flat_rate', sa.Numeric(6, 4), nullable=True),

        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('source', sa.String(100), nullable=True),

        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_index('ix_mileage_rates_tenant_year', 'expense_mileage_rates', ['tenant_id', 'year', 'vehicle_type'], unique=True)

    # ==========================================================================
    # EXPENSE EMPLOYEE VEHICLES TABLE
    # ==========================================================================

    op.create_table(
        'expense_employee_vehicles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),

        sa.Column('vehicle_type', sa.String(30), nullable=False),
        sa.Column('registration_number', sa.String(20), nullable=True),
        sa.Column('fiscal_power', sa.Integer, nullable=True),
        sa.Column('make', sa.String(100), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('is_default', sa.Boolean, server_default='false'),
        sa.Column('is_active', sa.Boolean, server_default='true'),

        # Annual mileage by year
        sa.Column('annual_mileage', postgresql.JSONB, server_default='{}'),

        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()')),
    )

    op.create_index('ix_employee_vehicles_tenant_employee', 'expense_employee_vehicles', ['tenant_id', 'employee_id'])

    # ==========================================================================
    # EXPENSE REPORTS TABLE
    # ==========================================================================

    op.create_table(
        'expense_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),

        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),

        # Employee
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('employee_name', sa.String(255), nullable=True),
        sa.Column('department_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Period
        sa.Column('period_start', sa.Date, nullable=True),
        sa.Column('period_end', sa.Date, nullable=True),
        sa.Column('mission_reference', sa.String(100), nullable=True),

        # Status
        sa.Column('status', sa.String(20), server_default='draft'),

        # Totals
        sa.Column('total_amount', sa.Numeric(18, 4), server_default='0'),
        sa.Column('total_vat', sa.Numeric(18, 4), server_default='0'),
        sa.Column('total_reimbursable', sa.Numeric(18, 4), server_default='0'),
        sa.Column('currency', sa.String(3), server_default='EUR'),

        # Workflow
        sa.Column('current_approver_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approval_history', postgresql.JSONB, server_default='[]'),

        # Dates
        sa.Column('submitted_at', sa.DateTime, nullable=True),
        sa.Column('approved_at', sa.DateTime, nullable=True),
        sa.Column('paid_at', sa.DateTime, nullable=True),

        # Accounting export
        sa.Column('exported_to_accounting', sa.Boolean, server_default='false'),
        sa.Column('accounting_entry_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('accounting_export_date', sa.DateTime, nullable=True),

        # Audit
        sa.Column('version', sa.Integer, server_default='1'),
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_index('ix_expense_reports_tenant_code', 'expense_reports', ['tenant_id', 'code'], unique=True)
    op.create_index('ix_expense_reports_tenant_employee', 'expense_reports', ['tenant_id', 'employee_id'])
    op.create_index('ix_expense_reports_tenant_status', 'expense_reports', ['tenant_id', 'status'])
    op.create_index('ix_expense_reports_tenant_period', 'expense_reports', ['tenant_id', 'period_start', 'period_end'])

    # ==========================================================================
    # EXPENSE LINES TABLE
    # ==========================================================================

    op.create_table(
        'expense_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('expense_reports.id'), nullable=False),

        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('expense_date', sa.Date, nullable=False),

        # Amounts
        sa.Column('amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('currency', sa.String(3), server_default='EUR'),
        sa.Column('vat_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('vat_amount', sa.Numeric(18, 4), nullable=True),
        sa.Column('amount_excl_vat', sa.Numeric(18, 4), nullable=True),
        sa.Column('vat_recoverable', sa.Boolean, server_default='true'),

        # Payment
        sa.Column('payment_method', sa.String(30), server_default='personal_card'),

        # Receipt
        sa.Column('receipt_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('receipt_file_path', sa.String(500), nullable=True),
        sa.Column('receipt_required', sa.Boolean, server_default='true'),

        # Mileage
        sa.Column('mileage_departure', sa.String(255), nullable=True),
        sa.Column('mileage_arrival', sa.String(255), nullable=True),
        sa.Column('mileage_distance_km', sa.Numeric(10, 2), nullable=True),
        sa.Column('mileage_is_round_trip', sa.Boolean, server_default='false'),
        sa.Column('vehicle_type', sa.String(30), nullable=True),
        sa.Column('mileage_rate', sa.Numeric(6, 4), nullable=True),
        sa.Column('mileage_purpose', sa.Text, nullable=True),

        # Business meals
        sa.Column('guests', postgresql.JSONB, server_default='[]'),
        sa.Column('guest_count', sa.Integer, server_default='0'),

        # Project/Client
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('billable', sa.Boolean, server_default='false'),

        # Compliance
        sa.Column('is_policy_compliant', sa.Boolean, server_default='true'),
        sa.Column('policy_violation_reason', sa.Text, nullable=True),

        # Accounting
        sa.Column('accounting_code', sa.String(20), nullable=True),
        sa.Column('cost_center', sa.String(50), nullable=True),
        sa.Column('analytic_axis', postgresql.JSONB, nullable=True),

        # OCR
        sa.Column('ocr_processed', sa.Boolean, server_default='false'),
        sa.Column('ocr_data', postgresql.JSONB, nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()')),
    )

    op.create_index('ix_expense_lines_report', 'expense_lines', ['report_id', 'expense_date'])
    op.create_index('ix_expense_lines_category', 'expense_lines', ['tenant_id', 'category'])

    print("[MIGRATION] Expenses module (GAP-084) tables created successfully")


def downgrade() -> None:
    """Drop Expenses module tables and enums."""

    # Drop tables (reverse order)
    op.drop_table('expense_lines')
    op.drop_table('expense_reports')
    op.drop_table('expense_employee_vehicles')
    op.drop_table('expense_mileage_rates')
    op.drop_table('expense_policies')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS expense_vehicle_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS expense_payment_method CASCADE;")
    op.execute("DROP TYPE IF EXISTS expense_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS expense_category CASCADE;")

    print("[MIGRATION] Expenses module (GAP-084) tables dropped successfully")
