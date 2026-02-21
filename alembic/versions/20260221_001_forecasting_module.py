"""Module Forecasting (GAP-076) - Prévisions financières

Revision ID: forecasting_001
Revises: enrichment_module_001
Create Date: 2026-02-21

Tables:
- forecasts: Prévisions (ventes, trésorerie, stocks)
- forecast_models: Modèles statistiques (ARIMA, MA, etc.)
- scenarios: Scénarios What-If
- budgets: Budgétisation annuelle/périodique
- kpis: Indicateurs clés de performance

Multi-tenant strict, Soft delete, Audit complet, Versioning.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'forecasting_001'
down_revision = 'enrichment_module_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Forecasting module tables and enums."""

    # ==========================================================================
    # ENUM TYPES
    # ==========================================================================

    # Forecast Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE forecast_type AS ENUM (
                'sales', 'revenue', 'cash_flow', 'inventory',
                'demand', 'expense', 'headcount', 'custom'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Forecast Method
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE forecast_method AS ENUM (
                'moving_average', 'weighted_average', 'exponential_smoothing',
                'linear_regression', 'seasonal', 'arima', 'manual', 'hybrid'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Granularity
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE granularity AS ENUM (
                'daily', 'weekly', 'monthly', 'quarterly', 'yearly'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Forecast Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE forecast_status AS ENUM (
                'draft', 'active', 'approved', 'archived'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Scenario Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE scenario_type AS ENUM (
                'baseline', 'optimistic', 'pessimistic',
                'best_case', 'worst_case', 'custom'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Budget Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE budget_status AS ENUM (
                'draft', 'submitted', 'under_review',
                'approved', 'rejected', 'locked'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # KPI Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE kpi_status AS ENUM (
                'green', 'amber', 'red'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ==========================================================================
    # FORECAST MODELS TABLE (first for FK reference)
    # ==========================================================================

    op.create_table(
        'forecast_models',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),

        # Configuration
        sa.Column('forecast_type', postgresql.ENUM('sales', 'revenue', 'cash_flow', 'inventory', 'demand', 'expense', 'headcount', 'custom', name='forecast_type', create_type=False), nullable=False, server_default='sales'),
        sa.Column('method', postgresql.ENUM('moving_average', 'weighted_average', 'exponential_smoothing', 'linear_regression', 'seasonal', 'arima', 'manual', 'hybrid', name='forecast_method', create_type=False), nullable=False, server_default='moving_average'),

        # Parameters
        sa.Column('parameters', postgresql.JSONB, server_default='{}'),
        sa.Column('training_period_months', sa.Integer, server_default='12'),
        sa.Column('accuracy_metrics', postgresql.JSONB, server_default='{}'),
        sa.Column('last_trained_at', sa.DateTime, nullable=True),
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

        # Version
        sa.Column('version', sa.Integer, server_default='1'),

        # Constraints
        sa.UniqueConstraint('tenant_id', 'code', name='uq_fmodel_tenant_code'),
    )

    op.create_index('ix_fmodel_tenant', 'forecast_models', ['tenant_id'])
    op.create_index('ix_fmodel_tenant_code', 'forecast_models', ['tenant_id', 'code'])

    # ==========================================================================
    # FORECASTS TABLE
    # ==========================================================================

    op.create_table(
        'forecasts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),

        # Type and method
        sa.Column('forecast_type', postgresql.ENUM('sales', 'revenue', 'cash_flow', 'inventory', 'demand', 'expense', 'headcount', 'custom', name='forecast_type', create_type=False), nullable=False, server_default='sales'),
        sa.Column('method', postgresql.ENUM('moving_average', 'weighted_average', 'exponential_smoothing', 'linear_regression', 'seasonal', 'arima', 'manual', 'hybrid', name='forecast_method', create_type=False), nullable=False, server_default='moving_average'),
        sa.Column('status', postgresql.ENUM('draft', 'active', 'approved', 'archived', name='forecast_status', create_type=False), nullable=False, server_default='draft'),

        # Period
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        sa.Column('granularity', postgresql.ENUM('daily', 'weekly', 'monthly', 'quarterly', 'yearly', name='granularity', create_type=False), nullable=False, server_default='monthly'),

        # Forecast data
        sa.Column('periods', postgresql.JSONB, server_default='[]'),
        sa.Column('total_forecasted', sa.Numeric(18, 2), server_default='0'),
        sa.Column('average_per_period', sa.Numeric(18, 2), server_default='0'),

        # Actual comparison
        sa.Column('actual_to_date', sa.Numeric(18, 2), server_default='0'),
        sa.Column('variance', sa.Numeric(18, 2), server_default='0'),
        sa.Column('variance_percent', sa.Numeric(8, 2), server_default='0'),

        # Categorization
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('tags', postgresql.JSONB, server_default='[]'),

        # Model reference
        sa.Column('model_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('forecast_models.id', ondelete='SET NULL'), nullable=True),

        # Assumptions
        sa.Column('assumptions', postgresql.JSONB, server_default='[]'),
        sa.Column('notes', sa.Text, nullable=True),

        # Approval
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime, nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Soft Delete
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Version
        sa.Column('version', sa.Integer, server_default='1'),

        # Constraints
        sa.UniqueConstraint('tenant_id', 'code', name='uq_forecast_tenant_code'),
        sa.CheckConstraint('end_date >= start_date', name='ck_forecast_dates_valid'),
    )

    op.create_index('ix_forecast_tenant', 'forecasts', ['tenant_id'])
    op.create_index('ix_forecast_tenant_code', 'forecasts', ['tenant_id', 'code'])
    op.create_index('ix_forecast_tenant_type', 'forecasts', ['tenant_id', 'forecast_type'])
    op.create_index('ix_forecast_tenant_status', 'forecasts', ['tenant_id', 'status'])
    op.create_index('ix_forecast_tenant_deleted', 'forecasts', ['tenant_id', 'is_deleted'])

    # ==========================================================================
    # SCENARIOS TABLE
    # ==========================================================================

    op.create_table(
        'scenarios',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),

        # Type
        sa.Column('scenario_type', postgresql.ENUM('baseline', 'optimistic', 'pessimistic', 'best_case', 'worst_case', 'custom', name='scenario_type', create_type=False), nullable=False, server_default='baseline'),

        # Base forecast
        sa.Column('base_forecast_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('forecasts.id', ondelete='CASCADE'), nullable=False),

        # Adjustments
        sa.Column('adjustment_type', sa.String(20), server_default='percent'),
        sa.Column('adjustment_value', sa.Numeric(12, 4), server_default='0'),

        # Assumptions
        sa.Column('assumptions', postgresql.JSONB, server_default='{}'),

        # Results
        sa.Column('periods', postgresql.JSONB, server_default='[]'),
        sa.Column('total_forecasted', sa.Numeric(18, 2), server_default='0'),

        # Comparison
        sa.Column('variance_from_baseline', sa.Numeric(18, 2), server_default='0'),
        sa.Column('variance_percent', sa.Numeric(8, 2), server_default='0'),

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

        # Version
        sa.Column('version', sa.Integer, server_default='1'),

        # Constraints
        sa.UniqueConstraint('tenant_id', 'code', name='uq_scenario_tenant_code'),
    )

    op.create_index('ix_scenario_tenant', 'scenarios', ['tenant_id'])
    op.create_index('ix_scenario_tenant_code', 'scenarios', ['tenant_id', 'code'])
    op.create_index('ix_scenario_forecast', 'scenarios', ['base_forecast_id'])

    # ==========================================================================
    # BUDGETS TABLE
    # ==========================================================================

    op.create_table(
        'budgets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),

        # Period
        sa.Column('fiscal_year', sa.Integer, nullable=False),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        sa.Column('granularity', postgresql.ENUM('daily', 'weekly', 'monthly', 'quarterly', 'yearly', name='granularity', create_type=False), nullable=False, server_default='monthly'),

        # Status
        sa.Column('status', postgresql.ENUM('draft', 'submitted', 'under_review', 'approved', 'rejected', 'locked', name='budget_status', create_type=False), nullable=False, server_default='draft'),

        # Department
        sa.Column('department_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('department_name', sa.String(100), nullable=True),

        # Lines (JSONB for flexibility)
        sa.Column('lines', postgresql.JSONB, server_default='[]'),

        # Totals
        sa.Column('total_budget', sa.Numeric(18, 2), server_default='0'),
        sa.Column('total_actual', sa.Numeric(18, 2), server_default='0'),
        sa.Column('total_variance', sa.Numeric(18, 2), server_default='0'),
        sa.Column('variance_percent', sa.Numeric(8, 2), server_default='0'),

        # Workflow
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('submitted_at', sa.DateTime, nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime, nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),

        # Parent budget (versioning)
        sa.Column('parent_budget_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('budgets.id', ondelete='SET NULL'), nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Soft Delete
        sa.Column('is_deleted', sa.Boolean, server_default='false'),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Version
        sa.Column('version', sa.Integer, server_default='1'),

        # Constraints
        sa.UniqueConstraint('tenant_id', 'code', name='uq_budget_tenant_code'),
        sa.CheckConstraint('end_date >= start_date', name='ck_budget_dates_valid'),
    )

    op.create_index('ix_budget_tenant', 'budgets', ['tenant_id'])
    op.create_index('ix_budget_tenant_code', 'budgets', ['tenant_id', 'code'])
    op.create_index('ix_budget_tenant_year', 'budgets', ['tenant_id', 'fiscal_year'])
    op.create_index('ix_budget_tenant_status', 'budgets', ['tenant_id', 'status'])

    # ==========================================================================
    # KPIS TABLE
    # ==========================================================================

    op.create_table(
        'kpis',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),

        # Configuration
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('formula', sa.Text, nullable=True),
        sa.Column('unit', sa.String(50), nullable=True),

        # Values
        sa.Column('current_value', sa.Numeric(18, 4), server_default='0'),
        sa.Column('target_value', sa.Numeric(18, 4), server_default='0'),
        sa.Column('previous_value', sa.Numeric(18, 4), server_default='0'),

        # Performance
        sa.Column('achievement_percent', sa.Numeric(8, 2), server_default='0'),
        sa.Column('trend', sa.String(20), server_default='stable'),

        # Thresholds
        sa.Column('green_threshold', sa.Numeric(18, 4), server_default='0'),
        sa.Column('amber_threshold', sa.Numeric(18, 4), server_default='0'),
        sa.Column('red_threshold', sa.Numeric(18, 4), server_default='0'),

        # Status
        sa.Column('status', postgresql.ENUM('green', 'amber', 'red', name='kpi_status', create_type=False), nullable=False, server_default='green'),

        # Frequency
        sa.Column('update_frequency', sa.String(20), server_default='monthly'),
        sa.Column('last_measured_at', sa.DateTime, nullable=True),

        # History
        sa.Column('historical_values', postgresql.JSONB, server_default='[]'),

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

        # Version
        sa.Column('version', sa.Integer, server_default='1'),

        # Constraints
        sa.UniqueConstraint('tenant_id', 'code', name='uq_kpi_tenant_code'),
    )

    op.create_index('ix_kpi_tenant', 'kpis', ['tenant_id'])
    op.create_index('ix_kpi_tenant_code', 'kpis', ['tenant_id', 'code'])
    op.create_index('ix_kpi_tenant_category', 'kpis', ['tenant_id', 'category'])
    op.create_index('ix_kpi_tenant_status', 'kpis', ['tenant_id', 'status'])

    print("[MIGRATION] Forecasting module (GAP-076) tables created successfully")


def downgrade() -> None:
    """Drop Forecasting module tables and enums."""

    # Drop tables (reverse order)
    op.drop_table('kpis')
    op.drop_table('budgets')
    op.drop_table('scenarios')
    op.drop_table('forecasts')
    op.drop_table('forecast_models')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS kpi_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS budget_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS scenario_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS forecast_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS granularity CASCADE;")
    op.execute("DROP TYPE IF EXISTS forecast_method CASCADE;")
    op.execute("DROP TYPE IF EXISTS forecast_type CASCADE;")

    print("[MIGRATION] Forecasting module (GAP-076) tables dropped successfully")
