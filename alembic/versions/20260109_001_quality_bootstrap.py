"""BOOTSTRAP QUALITY - Create Quality module tables (UUID, no FK)

Revision ID: quality_bootstrap_001
Revises:
Create Date: 2026-01-09

DESCRIPTION:
============
Migration bootstrap pour le module Quality (M7) et QC Central (T4).
- Crée TOUTES les tables Quality avec UUID
- NE CONTIENT AUCUNE ForeignKey
- NE CONTIENT AUCUN ON DELETE
- Ordre de création maîtrisé pour éviter rollback PostgreSQL
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'quality_bootstrap_001'
down_revision = None
branch_labels = ('quality',)
depends_on = None


def upgrade() -> None:
    """Create Quality module tables without foreign keys."""

    # ========================================================================
    # ENUMS - Module Quality (M7)
    # ========================================================================

    # Create all enums first
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE nonconformancetype AS ENUM (
                'PRODUCT', 'PROCESS', 'SERVICE', 'SUPPLIER', 'CUSTOMER',
                'INTERNAL', 'EXTERNAL', 'AUDIT', 'REGULATORY'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE nonconformancestatus AS ENUM (
                'DRAFT', 'OPEN', 'UNDER_ANALYSIS', 'ACTION_REQUIRED',
                'IN_PROGRESS', 'VERIFICATION', 'CLOSED', 'CANCELLED'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE nonconformanceseverity AS ENUM (
                'MINOR', 'MAJOR', 'CRITICAL', 'BLOCKING'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE controltype AS ENUM (
                'INCOMING', 'IN_PROCESS', 'FINAL', 'OUTGOING', 'SAMPLING',
                'DESTRUCTIVE', 'NON_DESTRUCTIVE', 'VISUAL', 'DIMENSIONAL',
                'FUNCTIONAL', 'LABORATORY'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE controlstatus AS ENUM (
                'PLANNED', 'PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE controlresult AS ENUM (
                'PASSED', 'FAILED', 'CONDITIONAL', 'PENDING', 'NOT_APPLICABLE'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE audittype AS ENUM (
                'INTERNAL', 'EXTERNAL', 'SUPPLIER', 'CUSTOMER', 'CERTIFICATION',
                'SURVEILLANCE', 'PROCESS', 'PRODUCT', 'SYSTEM'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE auditstatus AS ENUM (
                'PLANNED', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED',
                'REPORT_PENDING', 'CLOSED', 'CANCELLED'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE findingseverity AS ENUM (
                'OBSERVATION', 'MINOR', 'MAJOR', 'CRITICAL'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE capatype AS ENUM (
                'CORRECTIVE', 'PREVENTIVE', 'IMPROVEMENT'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE capastatus AS ENUM (
                'DRAFT', 'OPEN', 'ANALYSIS', 'ACTION_PLANNING', 'IN_PROGRESS',
                'VERIFICATION', 'CLOSED_EFFECTIVE', 'CLOSED_INEFFECTIVE', 'CANCELLED'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE claimstatus AS ENUM (
                'RECEIVED', 'ACKNOWLEDGED', 'UNDER_INVESTIGATION', 'PENDING_RESPONSE',
                'RESPONSE_SENT', 'IN_RESOLUTION', 'RESOLVED', 'CLOSED', 'REJECTED'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE certificationstatus AS ENUM (
                'PLANNED', 'IN_PREPARATION', 'AUDIT_SCHEDULED', 'AUDIT_COMPLETED',
                'CERTIFIED', 'SUSPENDED', 'WITHDRAWN', 'EXPIRED'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ========================================================================
    # ENUMS - Module QC Central (T4)
    # ========================================================================

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE qcrulecategory AS ENUM (
                'ARCHITECTURE', 'SECURITY', 'PERFORMANCE', 'CODE_QUALITY',
                'TESTING', 'DOCUMENTATION', 'API', 'DATABASE', 'INTEGRATION', 'COMPLIANCE'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE qcruleseverity AS ENUM (
                'INFO', 'WARNING', 'CRITICAL', 'BLOCKER'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE qccheckstatus AS ENUM (
                'PENDING', 'RUNNING', 'PASSED', 'FAILED', 'SKIPPED', 'ERROR'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE modulestatus AS ENUM (
                'DRAFT', 'IN_DEVELOPMENT', 'READY_FOR_QC', 'QC_IN_PROGRESS',
                'QC_PASSED', 'QC_FAILED', 'PRODUCTION', 'DEPRECATED'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE qctesttype AS ENUM (
                'UNIT', 'INTEGRATION', 'E2E', 'PERFORMANCE', 'SECURITY', 'REGRESSION'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE validationphase AS ENUM (
                'PRE_QC', 'AUTOMATED', 'MANUAL', 'FINAL', 'POST_DEPLOY'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ========================================================================
    # TABLES - Module Quality (M7) - Tables indépendantes d'abord
    # ========================================================================

    # 1. quality_capas (table parent pour plusieurs FK)
    op.create_table(
        'quality_capas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('capa_number', sa.String(50), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('capa_type', postgresql.ENUM('CORRECTIVE', 'PREVENTIVE', 'IMPROVEMENT', name='capatype', create_type=False), nullable=False),
        sa.Column('source_type', sa.String(50)),
        sa.Column('source_reference', sa.String(100)),
        sa.Column('source_id', postgresql.UUID(as_uuid=True)),
        sa.Column('status', postgresql.ENUM('DRAFT', 'OPEN', 'ANALYSIS', 'ACTION_PLANNING', 'IN_PROGRESS', 'VERIFICATION', 'CLOSED_EFFECTIVE', 'CLOSED_INEFFECTIVE', 'CANCELLED', name='capastatus', create_type=False), default='DRAFT'),
        sa.Column('priority', sa.String(20), default='MEDIUM'),
        sa.Column('open_date', sa.Date, nullable=False),
        sa.Column('target_close_date', sa.Date),
        sa.Column('actual_close_date', sa.Date),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('department', sa.String(100)),
        sa.Column('problem_statement', sa.Text),
        sa.Column('immediate_containment', sa.Text),
        sa.Column('root_cause_analysis', sa.Text),
        sa.Column('root_cause_method', sa.String(100)),
        sa.Column('root_cause_verified', sa.Boolean, default=False),
        sa.Column('impact_assessment', sa.Text),
        sa.Column('risk_level', sa.String(50)),
        sa.Column('effectiveness_criteria', sa.Text),
        sa.Column('effectiveness_verified', sa.Boolean, default=False),
        sa.Column('effectiveness_date', sa.Date),
        sa.Column('effectiveness_result', sa.Text),
        sa.Column('verified_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('extension_required', sa.Boolean, default=False),
        sa.Column('extension_scope', sa.Text),
        sa.Column('extension_completed', sa.Boolean, default=False),
        sa.Column('closure_comments', sa.Text),
        sa.Column('closed_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('attachments', postgresql.JSONB, default=[]),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('idx_capa_tenant', 'quality_capas', ['tenant_id'])
    op.create_index('idx_capa_number', 'quality_capas', ['tenant_id', 'capa_number'])
    op.create_index('idx_capa_type', 'quality_capas', ['tenant_id', 'capa_type'])
    op.create_index('idx_capa_status', 'quality_capas', ['tenant_id', 'status'])

    # 2. quality_non_conformances
    op.create_table(
        'quality_non_conformances',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('nc_number', sa.String(50), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('nc_type', postgresql.ENUM('PRODUCT', 'PROCESS', 'SERVICE', 'SUPPLIER', 'CUSTOMER', 'INTERNAL', 'EXTERNAL', 'AUDIT', 'REGULATORY', name='nonconformancetype', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('DRAFT', 'OPEN', 'UNDER_ANALYSIS', 'ACTION_REQUIRED', 'IN_PROGRESS', 'VERIFICATION', 'CLOSED', 'CANCELLED', name='nonconformancestatus', create_type=False), default='DRAFT'),
        sa.Column('severity', postgresql.ENUM('MINOR', 'MAJOR', 'CRITICAL', 'BLOCKING', name='nonconformanceseverity', create_type=False), nullable=False),
        sa.Column('detected_date', sa.Date, nullable=False),
        sa.Column('detected_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('detection_location', sa.String(200)),
        sa.Column('detection_phase', sa.String(100)),
        sa.Column('source_type', sa.String(50)),
        sa.Column('source_reference', sa.String(100)),
        sa.Column('source_id', postgresql.UUID(as_uuid=True)),
        sa.Column('product_id', postgresql.UUID(as_uuid=True)),
        sa.Column('lot_number', sa.String(100)),
        sa.Column('serial_number', sa.String(100)),
        sa.Column('quantity_affected', sa.Numeric(15, 3)),
        sa.Column('unit_id', postgresql.UUID(as_uuid=True)),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True)),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True)),
        sa.Column('immediate_cause', sa.Text),
        sa.Column('root_cause', sa.Text),
        sa.Column('cause_analysis_method', sa.String(100)),
        sa.Column('cause_analysis_date', sa.Date),
        sa.Column('cause_analyzed_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('impact_description', sa.Text),
        sa.Column('estimated_cost', sa.Numeric(15, 2)),
        sa.Column('actual_cost', sa.Numeric(15, 2)),
        sa.Column('cost_currency', sa.String(3), default='EUR'),
        sa.Column('immediate_action', sa.Text),
        sa.Column('immediate_action_date', sa.DateTime),
        sa.Column('immediate_action_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('responsible_id', postgresql.UUID(as_uuid=True)),
        sa.Column('department', sa.String(100)),
        sa.Column('disposition', sa.String(50)),
        sa.Column('disposition_date', sa.Date),
        sa.Column('disposition_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('disposition_justification', sa.Text),
        sa.Column('capa_id', postgresql.UUID(as_uuid=True)),
        sa.Column('capa_required', sa.Boolean, default=False),
        sa.Column('closed_date', sa.Date),
        sa.Column('closed_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('closure_justification', sa.Text),
        sa.Column('effectiveness_verified', sa.Boolean, default=False),
        sa.Column('effectiveness_date', sa.Date),
        sa.Column('attachments', postgresql.JSONB, default=[]),
        sa.Column('notes', sa.Text),
        sa.Column('is_recurrent', sa.Boolean, default=False),
        sa.Column('recurrence_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('idx_nc_tenant', 'quality_non_conformances', ['tenant_id'])
    op.create_index('idx_nc_type', 'quality_non_conformances', ['tenant_id', 'nc_type'])
    op.create_index('idx_nc_status', 'quality_non_conformances', ['tenant_id', 'status'])
    op.create_index('idx_nc_severity', 'quality_non_conformances', ['tenant_id', 'severity'])
    op.create_index('idx_nc_detected', 'quality_non_conformances', ['tenant_id', 'detected_date'])

    # 3. quality_nc_actions
    op.create_table(
        'quality_nc_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('nc_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_number', sa.Integer, nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('responsible_id', postgresql.UUID(as_uuid=True)),
        sa.Column('planned_date', sa.Date),
        sa.Column('due_date', sa.Date),
        sa.Column('completed_date', sa.Date),
        sa.Column('status', sa.String(50), default='PLANNED'),
        sa.Column('verified', sa.Boolean, default=False),
        sa.Column('verified_date', sa.Date),
        sa.Column('verified_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('verification_result', sa.Text),
        sa.Column('comments', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('idx_nc_action_tenant', 'quality_nc_actions', ['tenant_id'])
    op.create_index('idx_nc_action_nc', 'quality_nc_actions', ['nc_id'])
    op.create_index('idx_nc_action_status', 'quality_nc_actions', ['status'])

    # 4. quality_control_templates
    op.create_table(
        'quality_control_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('version', sa.String(20), default='1.0'),
        sa.Column('control_type', postgresql.ENUM('INCOMING', 'IN_PROCESS', 'FINAL', 'OUTGOING', 'SAMPLING', 'DESTRUCTIVE', 'NON_DESTRUCTIVE', 'VISUAL', 'DIMENSIONAL', 'FUNCTIONAL', 'LABORATORY', name='controltype', create_type=False), nullable=False),
        sa.Column('applies_to', sa.String(50)),
        sa.Column('product_category_id', postgresql.UUID(as_uuid=True)),
        sa.Column('instructions', sa.Text),
        sa.Column('sampling_plan', sa.Text),
        sa.Column('acceptance_criteria', sa.Text),
        sa.Column('estimated_duration_minutes', sa.Integer),
        sa.Column('required_equipment', postgresql.JSONB, default=[]),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('valid_from', sa.Date),
        sa.Column('valid_until', sa.Date),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.UniqueConstraint('tenant_id', 'code', name='uq_qct_code'),
    )
    op.create_index('idx_qct_tenant', 'quality_control_templates', ['tenant_id'])
    op.create_index('idx_qct_code', 'quality_control_templates', ['tenant_id', 'code'])

    # 5. quality_control_template_items
    op.create_table(
        'quality_control_template_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sequence', sa.Integer, nullable=False),
        sa.Column('characteristic', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('measurement_type', sa.String(50), nullable=False),
        sa.Column('unit', sa.String(50)),
        sa.Column('nominal_value', sa.Numeric(15, 6)),
        sa.Column('tolerance_min', sa.Numeric(15, 6)),
        sa.Column('tolerance_max', sa.Numeric(15, 6)),
        sa.Column('upper_limit', sa.Numeric(15, 6)),
        sa.Column('lower_limit', sa.Numeric(15, 6)),
        sa.Column('expected_result', sa.String(200)),
        sa.Column('measurement_method', sa.Text),
        sa.Column('equipment_code', sa.String(100)),
        sa.Column('is_critical', sa.Boolean, default=False),
        sa.Column('is_mandatory', sa.Boolean, default=True),
        sa.Column('sampling_frequency', sa.String(100)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('idx_qcti_tenant', 'quality_control_template_items', ['tenant_id'])
    op.create_index('idx_qcti_template', 'quality_control_template_items', ['template_id'])

    # 6. quality_controls
    op.create_table(
        'quality_controls',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('control_number', sa.String(50), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True)),
        sa.Column('control_type', postgresql.ENUM('INCOMING', 'IN_PROCESS', 'FINAL', 'OUTGOING', 'SAMPLING', 'DESTRUCTIVE', 'NON_DESTRUCTIVE', 'VISUAL', 'DIMENSIONAL', 'FUNCTIONAL', 'LABORATORY', name='controltype', create_type=False), nullable=False),
        sa.Column('source_type', sa.String(50)),
        sa.Column('source_reference', sa.String(100)),
        sa.Column('source_id', postgresql.UUID(as_uuid=True)),
        sa.Column('product_id', postgresql.UUID(as_uuid=True)),
        sa.Column('lot_number', sa.String(100)),
        sa.Column('serial_number', sa.String(100)),
        sa.Column('quantity_to_control', sa.Numeric(15, 3)),
        sa.Column('quantity_controlled', sa.Numeric(15, 3)),
        sa.Column('quantity_conforming', sa.Numeric(15, 3)),
        sa.Column('quantity_non_conforming', sa.Numeric(15, 3)),
        sa.Column('unit_id', postgresql.UUID(as_uuid=True)),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True)),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True)),
        sa.Column('control_date', sa.Date, nullable=False),
        sa.Column('start_time', sa.DateTime),
        sa.Column('end_time', sa.DateTime),
        sa.Column('location', sa.String(200)),
        sa.Column('controller_id', postgresql.UUID(as_uuid=True)),
        sa.Column('status', postgresql.ENUM('PLANNED', 'PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='controlstatus', create_type=False), default='PLANNED'),
        sa.Column('result', postgresql.ENUM('PASSED', 'FAILED', 'CONDITIONAL', 'PENDING', 'NOT_APPLICABLE', name='controlresult', create_type=False)),
        sa.Column('result_date', sa.DateTime),
        sa.Column('decision', sa.String(50)),
        sa.Column('decision_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('decision_date', sa.DateTime),
        sa.Column('decision_comments', sa.Text),
        sa.Column('nc_id', postgresql.UUID(as_uuid=True)),
        sa.Column('observations', sa.Text),
        sa.Column('attachments', postgresql.JSONB, default=[]),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('idx_qc_tenant', 'quality_controls', ['tenant_id'])
    op.create_index('idx_qc_number', 'quality_controls', ['tenant_id', 'control_number'])
    op.create_index('idx_qc_type', 'quality_controls', ['tenant_id', 'control_type'])
    op.create_index('idx_qc_status', 'quality_controls', ['tenant_id', 'status'])
    op.create_index('idx_qc_date', 'quality_controls', ['tenant_id', 'control_date'])

    # 7. quality_control_lines
    op.create_table(
        'quality_control_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('control_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_item_id', postgresql.UUID(as_uuid=True)),
        sa.Column('sequence', sa.Integer, nullable=False),
        sa.Column('characteristic', sa.String(200), nullable=False),
        sa.Column('nominal_value', sa.Numeric(15, 6)),
        sa.Column('tolerance_min', sa.Numeric(15, 6)),
        sa.Column('tolerance_max', sa.Numeric(15, 6)),
        sa.Column('unit', sa.String(50)),
        sa.Column('measured_value', sa.Numeric(15, 6)),
        sa.Column('measured_text', sa.String(500)),
        sa.Column('measured_boolean', sa.Boolean),
        sa.Column('measurement_date', sa.DateTime),
        sa.Column('result', postgresql.ENUM('PASSED', 'FAILED', 'CONDITIONAL', 'PENDING', 'NOT_APPLICABLE', name='controlresult', create_type=False)),
        sa.Column('deviation', sa.Numeric(15, 6)),
        sa.Column('equipment_code', sa.String(100)),
        sa.Column('equipment_serial', sa.String(100)),
        sa.Column('comments', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('idx_qcl_tenant', 'quality_control_lines', ['tenant_id'])
    op.create_index('idx_qcl_control', 'quality_control_lines', ['control_id'])

    # 8. quality_audits
    op.create_table(
        'quality_audits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('audit_number', sa.String(50), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('audit_type', postgresql.ENUM('INTERNAL', 'EXTERNAL', 'SUPPLIER', 'CUSTOMER', 'CERTIFICATION', 'SURVEILLANCE', 'PROCESS', 'PRODUCT', 'SYSTEM', name='audittype', create_type=False), nullable=False),
        sa.Column('reference_standard', sa.String(200)),
        sa.Column('reference_version', sa.String(50)),
        sa.Column('audit_scope', sa.Text),
        sa.Column('planned_date', sa.Date),
        sa.Column('planned_end_date', sa.Date),
        sa.Column('actual_date', sa.Date),
        sa.Column('actual_end_date', sa.Date),
        sa.Column('status', postgresql.ENUM('PLANNED', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'REPORT_PENDING', 'CLOSED', 'CANCELLED', name='auditstatus', create_type=False), default='PLANNED'),
        sa.Column('lead_auditor_id', postgresql.UUID(as_uuid=True)),
        sa.Column('auditors', postgresql.JSONB, default=[]),
        sa.Column('audited_entity', sa.String(200)),
        sa.Column('audited_department', sa.String(200)),
        sa.Column('auditee_contact_id', postgresql.UUID(as_uuid=True)),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True)),
        sa.Column('total_findings', sa.Integer, default=0),
        sa.Column('critical_findings', sa.Integer, default=0),
        sa.Column('major_findings', sa.Integer, default=0),
        sa.Column('minor_findings', sa.Integer, default=0),
        sa.Column('observations', sa.Integer, default=0),
        sa.Column('overall_score', sa.Numeric(5, 2)),
        sa.Column('max_score', sa.Numeric(5, 2)),
        sa.Column('audit_conclusion', sa.Text),
        sa.Column('recommendation', sa.Text),
        sa.Column('report_date', sa.Date),
        sa.Column('report_file', sa.String(500)),
        sa.Column('follow_up_required', sa.Boolean, default=False),
        sa.Column('follow_up_date', sa.Date),
        sa.Column('follow_up_completed', sa.Boolean, default=False),
        sa.Column('closed_date', sa.Date),
        sa.Column('closed_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('idx_audit_tenant', 'quality_audits', ['tenant_id'])
    op.create_index('idx_audit_number', 'quality_audits', ['tenant_id', 'audit_number'])
    op.create_index('idx_audit_type', 'quality_audits', ['tenant_id', 'audit_type'])
    op.create_index('idx_audit_status', 'quality_audits', ['tenant_id', 'status'])
    op.create_index('idx_audit_date', 'quality_audits', ['tenant_id', 'planned_date'])

    # 9. quality_audit_findings
    op.create_table(
        'quality_audit_findings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('audit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('finding_number', sa.Integer, nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('severity', postgresql.ENUM('OBSERVATION', 'MINOR', 'MAJOR', 'CRITICAL', name='findingseverity', create_type=False), nullable=False),
        sa.Column('category', sa.String(100)),
        sa.Column('clause_reference', sa.String(100)),
        sa.Column('process_reference', sa.String(100)),
        sa.Column('evidence', sa.Text),
        sa.Column('risk_description', sa.Text),
        sa.Column('risk_level', sa.String(50)),
        sa.Column('capa_required', sa.Boolean, default=False),
        sa.Column('capa_id', postgresql.UUID(as_uuid=True)),
        sa.Column('auditee_response', sa.Text),
        sa.Column('response_date', sa.Date),
        sa.Column('action_due_date', sa.Date),
        sa.Column('action_completed_date', sa.Date),
        sa.Column('status', sa.String(50), default='OPEN'),
        sa.Column('verified', sa.Boolean, default=False),
        sa.Column('verified_date', sa.Date),
        sa.Column('verified_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('verification_comments', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('idx_finding_tenant', 'quality_audit_findings', ['tenant_id'])
    op.create_index('idx_finding_audit', 'quality_audit_findings', ['audit_id'])
    op.create_index('idx_finding_severity', 'quality_audit_findings', ['severity'])

    # 10. quality_capa_actions
    op.create_table(
        'quality_capa_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('capa_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_number', sa.Integer, nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('responsible_id', postgresql.UUID(as_uuid=True)),
        sa.Column('planned_date', sa.Date),
        sa.Column('due_date', sa.Date, nullable=False),
        sa.Column('completed_date', sa.Date),
        sa.Column('status', sa.String(50), default='PLANNED'),
        sa.Column('result', sa.Text),
        sa.Column('evidence', sa.Text),
        sa.Column('verification_required', sa.Boolean, default=True),
        sa.Column('verified', sa.Boolean, default=False),
        sa.Column('verified_date', sa.Date),
        sa.Column('verified_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('verification_result', sa.Text),
        sa.Column('estimated_cost', sa.Numeric(15, 2)),
        sa.Column('actual_cost', sa.Numeric(15, 2)),
        sa.Column('comments', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('idx_capa_action_tenant', 'quality_capa_actions', ['tenant_id'])
    op.create_index('idx_capa_action_capa', 'quality_capa_actions', ['capa_id'])
    op.create_index('idx_capa_action_status', 'quality_capa_actions', ['status'])

    # 11. quality_customer_claims
    op.create_table(
        'quality_customer_claims',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('claim_number', sa.String(50), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_contact', sa.String(200)),
        sa.Column('customer_reference', sa.String(100)),
        sa.Column('received_date', sa.Date, nullable=False),
        sa.Column('received_via', sa.String(50)),
        sa.Column('received_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('product_id', postgresql.UUID(as_uuid=True)),
        sa.Column('order_reference', sa.String(100)),
        sa.Column('invoice_reference', sa.String(100)),
        sa.Column('lot_number', sa.String(100)),
        sa.Column('quantity_affected', sa.Numeric(15, 3)),
        sa.Column('claim_type', sa.String(50)),
        sa.Column('severity', postgresql.ENUM('MINOR', 'MAJOR', 'CRITICAL', 'BLOCKING', name='nonconformanceseverity', create_type=False)),
        sa.Column('priority', sa.String(20), default='MEDIUM'),
        sa.Column('status', postgresql.ENUM('RECEIVED', 'ACKNOWLEDGED', 'UNDER_INVESTIGATION', 'PENDING_RESPONSE', 'RESPONSE_SENT', 'IN_RESOLUTION', 'RESOLVED', 'CLOSED', 'REJECTED', name='claimstatus', create_type=False), default='RECEIVED'),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True)),
        sa.Column('investigation_summary', sa.Text),
        sa.Column('root_cause', sa.Text),
        sa.Column('our_responsibility', sa.Boolean),
        sa.Column('nc_id', postgresql.UUID(as_uuid=True)),
        sa.Column('capa_id', postgresql.UUID(as_uuid=True)),
        sa.Column('response_due_date', sa.Date),
        sa.Column('response_date', sa.Date),
        sa.Column('response_content', sa.Text),
        sa.Column('response_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('resolution_type', sa.String(50)),
        sa.Column('resolution_description', sa.Text),
        sa.Column('resolution_date', sa.Date),
        sa.Column('claim_amount', sa.Numeric(15, 2)),
        sa.Column('accepted_amount', sa.Numeric(15, 2)),
        sa.Column('cost_currency', sa.String(3), default='EUR'),
        sa.Column('customer_satisfied', sa.Boolean),
        sa.Column('satisfaction_feedback', sa.Text),
        sa.Column('closed_date', sa.Date),
        sa.Column('closed_by_id', postgresql.UUID(as_uuid=True)),
        sa.Column('attachments', postgresql.JSONB, default=[]),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('idx_claim_tenant', 'quality_customer_claims', ['tenant_id'])
    op.create_index('idx_claim_number', 'quality_customer_claims', ['tenant_id', 'claim_number'])
    op.create_index('idx_claim_status', 'quality_customer_claims', ['tenant_id', 'status'])
    op.create_index('idx_claim_customer', 'quality_customer_claims', ['tenant_id', 'customer_id'])
    op.create_index('idx_claim_date', 'quality_customer_claims', ['tenant_id', 'received_date'])

    # 12. quality_claim_actions
    op.create_table(
        'quality_claim_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('claim_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_number', sa.Integer, nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('responsible_id', postgresql.UUID(as_uuid=True)),
        sa.Column('due_date', sa.Date),
        sa.Column('completed_date', sa.Date),
        sa.Column('status', sa.String(50), default='PLANNED'),
        sa.Column('result', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('idx_claim_action_tenant', 'quality_claim_actions', ['tenant_id'])
    op.create_index('idx_claim_action_claim', 'quality_claim_actions', ['claim_id'])

    # 13. quality_indicators
    op.create_table(
        'quality_indicators',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('category', sa.String(100)),
        sa.Column('formula', sa.Text),
        sa.Column('unit', sa.String(50)),
        sa.Column('target_value', sa.Numeric(15, 4)),
        sa.Column('target_min', sa.Numeric(15, 4)),
        sa.Column('target_max', sa.Numeric(15, 4)),
        sa.Column('warning_threshold', sa.Numeric(15, 4)),
        sa.Column('critical_threshold', sa.Numeric(15, 4)),
        sa.Column('direction', sa.String(20)),
        sa.Column('measurement_frequency', sa.String(50)),
        sa.Column('data_source', sa.String(100)),
        sa.Column('calculation_query', sa.Text),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.UniqueConstraint('tenant_id', 'code', name='uq_qi_code'),
    )
    op.create_index('idx_qi_tenant', 'quality_indicators', ['tenant_id'])
    op.create_index('idx_qi_code', 'quality_indicators', ['tenant_id', 'code'])

    # 14. quality_indicator_measurements
    op.create_table(
        'quality_indicator_measurements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('indicator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('measurement_date', sa.Date, nullable=False),
        sa.Column('period_start', sa.Date),
        sa.Column('period_end', sa.Date),
        sa.Column('value', sa.Numeric(15, 4), nullable=False),
        sa.Column('numerator', sa.Numeric(15, 4)),
        sa.Column('denominator', sa.Numeric(15, 4)),
        sa.Column('target_value', sa.Numeric(15, 4)),
        sa.Column('deviation', sa.Numeric(15, 4)),
        sa.Column('achievement_rate', sa.Numeric(5, 2)),
        sa.Column('status', sa.String(20)),
        sa.Column('comments', sa.Text),
        sa.Column('action_required', sa.Boolean, default=False),
        sa.Column('source', sa.String(100)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('idx_qim_tenant', 'quality_indicator_measurements', ['tenant_id'])
    op.create_index('idx_qim_indicator', 'quality_indicator_measurements', ['indicator_id'])
    op.create_index('idx_qim_date', 'quality_indicator_measurements', ['measurement_date'])

    # 15. quality_certifications
    op.create_table(
        'quality_certifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('standard', sa.String(100), nullable=False),
        sa.Column('standard_version', sa.String(50)),
        sa.Column('scope', sa.Text),
        sa.Column('certification_body', sa.String(200)),
        sa.Column('certification_body_accreditation', sa.String(100)),
        sa.Column('initial_certification_date', sa.Date),
        sa.Column('current_certificate_date', sa.Date),
        sa.Column('expiry_date', sa.Date),
        sa.Column('next_surveillance_date', sa.Date),
        sa.Column('next_renewal_date', sa.Date),
        sa.Column('certificate_number', sa.String(100)),
        sa.Column('certificate_file', sa.String(500)),
        sa.Column('status', postgresql.ENUM('PLANNED', 'IN_PREPARATION', 'AUDIT_SCHEDULED', 'AUDIT_COMPLETED', 'CERTIFIED', 'SUSPENDED', 'WITHDRAWN', 'EXPIRED', name='certificationstatus', create_type=False), default='PLANNED'),
        sa.Column('manager_id', postgresql.UUID(as_uuid=True)),
        sa.Column('annual_cost', sa.Numeric(15, 2)),
        sa.Column('cost_currency', sa.String(3), default='EUR'),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('idx_cert_tenant', 'quality_certifications', ['tenant_id'])
    op.create_index('idx_cert_code', 'quality_certifications', ['tenant_id', 'code'])
    op.create_index('idx_cert_status', 'quality_certifications', ['tenant_id', 'status'])

    # 16. quality_certification_audits
    op.create_table(
        'quality_certification_audits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('certification_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('audit_type', sa.String(50), nullable=False),
        sa.Column('audit_date', sa.Date, nullable=False),
        sa.Column('audit_end_date', sa.Date),
        sa.Column('lead_auditor', sa.String(200)),
        sa.Column('audit_team', postgresql.JSONB, default=[]),
        sa.Column('result', sa.String(50)),
        sa.Column('findings_count', sa.Integer, default=0),
        sa.Column('major_nc_count', sa.Integer, default=0),
        sa.Column('minor_nc_count', sa.Integer, default=0),
        sa.Column('observations_count', sa.Integer, default=0),
        sa.Column('report_date', sa.Date),
        sa.Column('report_file', sa.String(500)),
        sa.Column('corrective_actions_due', sa.Date),
        sa.Column('corrective_actions_closed', sa.Date),
        sa.Column('follow_up_audit_date', sa.Date),
        sa.Column('quality_audit_id', postgresql.UUID(as_uuid=True)),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('idx_cert_audit_tenant', 'quality_certification_audits', ['tenant_id'])
    op.create_index('idx_cert_audit_cert', 'quality_certification_audits', ['certification_id'])
    op.create_index('idx_cert_audit_date', 'quality_certification_audits', ['audit_date'])

    # ========================================================================
    # TABLES - Module QC Central (T4)
    # ========================================================================

    # 17. qc_rules
    op.create_table(
        'qc_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('category', postgresql.ENUM('ARCHITECTURE', 'SECURITY', 'PERFORMANCE', 'CODE_QUALITY', 'TESTING', 'DOCUMENTATION', 'API', 'DATABASE', 'INTEGRATION', 'COMPLIANCE', name='qcrulecategory', create_type=False), nullable=False),
        sa.Column('severity', postgresql.ENUM('INFO', 'WARNING', 'CRITICAL', 'BLOCKER', name='qcruleseverity', create_type=False), default='WARNING', nullable=False),
        sa.Column('applies_to_modules', sa.Text),
        sa.Column('applies_to_phases', sa.Text),
        sa.Column('check_type', sa.String(50), nullable=False),
        sa.Column('check_config', sa.Text),
        sa.Column('threshold_value', sa.Float),
        sa.Column('threshold_operator', sa.String(10)),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('is_system', sa.Boolean, default=False, nullable=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('idx_qc_rules_tenant_code', 'qc_rules', ['tenant_id', 'code'], unique=True)
    op.create_index('idx_qc_rules_category', 'qc_rules', ['tenant_id', 'category'])

    # 18. qc_module_registry
    op.create_table(
        'qc_module_registry',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('module_code', sa.String(10), nullable=False),
        sa.Column('module_name', sa.String(200), nullable=False),
        sa.Column('module_version', sa.String(20), default='1.0.0', nullable=False),
        sa.Column('module_type', sa.String(20), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('dependencies', sa.Text),
        sa.Column('status', postgresql.ENUM('DRAFT', 'IN_DEVELOPMENT', 'READY_FOR_QC', 'QC_IN_PROGRESS', 'QC_PASSED', 'QC_FAILED', 'PRODUCTION', 'DEPRECATED', name='modulestatus', create_type=False), default='DRAFT', nullable=False),
        sa.Column('overall_score', sa.Float, default=0.0),
        sa.Column('architecture_score', sa.Float, default=0.0),
        sa.Column('security_score', sa.Float, default=0.0),
        sa.Column('performance_score', sa.Float, default=0.0),
        sa.Column('code_quality_score', sa.Float, default=0.0),
        sa.Column('testing_score', sa.Float, default=0.0),
        sa.Column('documentation_score', sa.Float, default=0.0),
        sa.Column('total_checks', sa.Integer, default=0),
        sa.Column('passed_checks', sa.Integer, default=0),
        sa.Column('failed_checks', sa.Integer, default=0),
        sa.Column('blocked_checks', sa.Integer, default=0),
        sa.Column('last_qc_run', sa.DateTime),
        sa.Column('validated_at', sa.DateTime),
        sa.Column('validated_by', postgresql.UUID(as_uuid=True)),
        sa.Column('production_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_module_registry_tenant_code', 'qc_module_registry', ['tenant_id', 'module_code'], unique=True)
    op.create_index('idx_module_registry_status', 'qc_module_registry', ['tenant_id', 'status'])

    # 19. qc_validations
    op.create_table(
        'qc_validations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('module_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('validation_phase', postgresql.ENUM('PRE_QC', 'AUTOMATED', 'MANUAL', 'FINAL', 'POST_DEPLOY', name='validationphase', create_type=False), nullable=False),
        sa.Column('started_at', sa.DateTime, default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('started_by', postgresql.UUID(as_uuid=True)),
        sa.Column('status', postgresql.ENUM('PENDING', 'RUNNING', 'PASSED', 'FAILED', 'SKIPPED', 'ERROR', name='qccheckstatus', create_type=False), default='PENDING', nullable=False),
        sa.Column('overall_score', sa.Float),
        sa.Column('total_rules', sa.Integer, default=0),
        sa.Column('passed_rules', sa.Integer, default=0),
        sa.Column('failed_rules', sa.Integer, default=0),
        sa.Column('skipped_rules', sa.Integer, default=0),
        sa.Column('blocked_rules', sa.Integer, default=0),
        sa.Column('category_scores', sa.Text),
        sa.Column('report_summary', sa.Text),
        sa.Column('report_details', sa.Text),
    )
    op.create_index('idx_validations_tenant_module', 'qc_validations', ['tenant_id', 'module_id'])
    op.create_index('idx_validations_status', 'qc_validations', ['tenant_id', 'status'])

    # 20. qc_check_results
    op.create_table(
        'qc_check_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('validation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rule_id', postgresql.UUID(as_uuid=True)),
        sa.Column('rule_code', sa.String(50), nullable=False),
        sa.Column('rule_name', sa.String(200)),
        sa.Column('category', postgresql.ENUM('ARCHITECTURE', 'SECURITY', 'PERFORMANCE', 'CODE_QUALITY', 'TESTING', 'DOCUMENTATION', 'API', 'DATABASE', 'INTEGRATION', 'COMPLIANCE', name='qcrulecategory', create_type=False), nullable=False),
        sa.Column('severity', postgresql.ENUM('INFO', 'WARNING', 'CRITICAL', 'BLOCKER', name='qcruleseverity', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'RUNNING', 'PASSED', 'FAILED', 'SKIPPED', 'ERROR', name='qccheckstatus', create_type=False), default='PENDING', nullable=False),
        sa.Column('executed_at', sa.DateTime, default=sa.func.now()),
        sa.Column('duration_ms', sa.Integer),
        sa.Column('expected_value', sa.String(255)),
        sa.Column('actual_value', sa.String(255)),
        sa.Column('score', sa.Float),
        sa.Column('message', sa.Text),
        sa.Column('error_details', sa.Text),
        sa.Column('recommendation', sa.Text),
        sa.Column('evidence', sa.Text),
    )
    op.create_index('idx_check_results_validation', 'qc_check_results', ['validation_id'])
    op.create_index('idx_check_results_status', 'qc_check_results', ['tenant_id', 'status'])
    op.create_index('idx_check_results_category', 'qc_check_results', ['tenant_id', 'category'])

    # 21. qc_test_runs
    op.create_table(
        'qc_test_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('module_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('validation_id', postgresql.UUID(as_uuid=True)),
        sa.Column('test_type', postgresql.ENUM('UNIT', 'INTEGRATION', 'E2E', 'PERFORMANCE', 'SECURITY', 'REGRESSION', name='qctesttype', create_type=False), nullable=False),
        sa.Column('test_suite', sa.String(200)),
        sa.Column('started_at', sa.DateTime, default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('duration_seconds', sa.Float),
        sa.Column('status', postgresql.ENUM('PENDING', 'RUNNING', 'PASSED', 'FAILED', 'SKIPPED', 'ERROR', name='qccheckstatus', create_type=False), default='PENDING', nullable=False),
        sa.Column('total_tests', sa.Integer, default=0),
        sa.Column('passed_tests', sa.Integer, default=0),
        sa.Column('failed_tests', sa.Integer, default=0),
        sa.Column('skipped_tests', sa.Integer, default=0),
        sa.Column('error_tests', sa.Integer, default=0),
        sa.Column('coverage_percent', sa.Float),
        sa.Column('failed_test_details', sa.Text),
        sa.Column('output_log', sa.Text),
        sa.Column('triggered_by', sa.String(50)),
        sa.Column('triggered_user', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('idx_test_runs_tenant_module', 'qc_test_runs', ['tenant_id', 'module_id'])
    op.create_index('idx_test_runs_type', 'qc_test_runs', ['tenant_id', 'test_type'])

    # 22. qc_metrics
    op.create_table(
        'qc_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('module_id', postgresql.UUID(as_uuid=True)),
        sa.Column('metric_date', sa.DateTime, nullable=False),
        sa.Column('modules_total', sa.Integer, default=0),
        sa.Column('modules_validated', sa.Integer, default=0),
        sa.Column('modules_production', sa.Integer, default=0),
        sa.Column('modules_failed', sa.Integer, default=0),
        sa.Column('avg_overall_score', sa.Float),
        sa.Column('avg_architecture_score', sa.Float),
        sa.Column('avg_security_score', sa.Float),
        sa.Column('avg_performance_score', sa.Float),
        sa.Column('avg_code_quality_score', sa.Float),
        sa.Column('avg_testing_score', sa.Float),
        sa.Column('avg_documentation_score', sa.Float),
        sa.Column('total_tests_run', sa.Integer, default=0),
        sa.Column('total_tests_passed', sa.Integer, default=0),
        sa.Column('avg_coverage', sa.Float),
        sa.Column('total_checks_run', sa.Integer, default=0),
        sa.Column('total_checks_passed', sa.Integer, default=0),
        sa.Column('critical_issues', sa.Integer, default=0),
        sa.Column('blocker_issues', sa.Integer, default=0),
        sa.Column('score_trend', sa.String(10)),
        sa.Column('score_delta', sa.Float),
        sa.Column('created_at', sa.DateTime, default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_qc_metrics_tenant_date', 'qc_metrics', ['tenant_id', 'metric_date'])
    op.create_index('idx_qc_metrics_module', 'qc_metrics', ['tenant_id', 'module_id'])

    # 23. qc_alerts
    op.create_table(
        'qc_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('module_id', postgresql.UUID(as_uuid=True)),
        sa.Column('validation_id', postgresql.UUID(as_uuid=True)),
        sa.Column('check_result_id', postgresql.UUID(as_uuid=True)),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('severity', postgresql.ENUM('INFO', 'WARNING', 'CRITICAL', 'BLOCKER', name='qcruleseverity', create_type=False), default='WARNING', nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('details', sa.Text),
        sa.Column('is_read', sa.Boolean, default=False, nullable=False),
        sa.Column('is_resolved', sa.Boolean, default=False, nullable=False),
        sa.Column('resolved_at', sa.DateTime),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True)),
        sa.Column('resolution_notes', sa.Text),
        sa.Column('created_at', sa.DateTime, default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_qc_alerts_tenant_unresolved', 'qc_alerts', ['tenant_id', 'is_resolved'])
    op.create_index('idx_qc_alerts_severity', 'qc_alerts', ['tenant_id', 'severity'])

    # 24. qc_dashboards
    op.create_table(
        'qc_dashboards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('layout', sa.Text),
        sa.Column('widgets', sa.Text),
        sa.Column('filters', sa.Text),
        sa.Column('is_default', sa.Boolean, default=False, nullable=False),
        sa.Column('is_public', sa.Boolean, default=False, nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True)),
        sa.Column('shared_with', sa.Text),
        sa.Column('auto_refresh', sa.Boolean, default=True, nullable=False),
        sa.Column('refresh_interval', sa.Integer, default=60),
        sa.Column('created_at', sa.DateTime, default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_qc_dashboards_tenant_owner', 'qc_dashboards', ['tenant_id', 'owner_id'])

    # 25. qc_templates
    op.create_table(
        'qc_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('rules', sa.Text, nullable=False),
        sa.Column('category', sa.String(50)),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('is_system', sa.Boolean, default=False, nullable=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('idx_qc_templates_tenant_code', 'qc_templates', ['tenant_id', 'code'], unique=True)


def downgrade() -> None:
    """Drop all Quality module tables."""

    # Drop tables in reverse order (dependants first)
    op.drop_table('qc_templates')
    op.drop_table('qc_dashboards')
    op.drop_table('qc_alerts')
    op.drop_table('qc_metrics')
    op.drop_table('qc_test_runs')
    op.drop_table('qc_check_results')
    op.drop_table('qc_validations')
    op.drop_table('qc_module_registry')
    op.drop_table('qc_rules')

    op.drop_table('quality_certification_audits')
    op.drop_table('quality_certifications')
    op.drop_table('quality_indicator_measurements')
    op.drop_table('quality_indicators')
    op.drop_table('quality_claim_actions')
    op.drop_table('quality_customer_claims')
    op.drop_table('quality_capa_actions')
    op.drop_table('quality_audit_findings')
    op.drop_table('quality_audits')
    op.drop_table('quality_control_lines')
    op.drop_table('quality_controls')
    op.drop_table('quality_control_template_items')
    op.drop_table('quality_control_templates')
    op.drop_table('quality_nc_actions')
    op.drop_table('quality_non_conformances')
    op.drop_table('quality_capas')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS validationphase CASCADE')
    op.execute('DROP TYPE IF EXISTS qctesttype CASCADE')
    op.execute('DROP TYPE IF EXISTS modulestatus CASCADE')
    op.execute('DROP TYPE IF EXISTS qccheckstatus CASCADE')
    op.execute('DROP TYPE IF EXISTS qcruleseverity CASCADE')
    op.execute('DROP TYPE IF EXISTS qcrulecategory CASCADE')
    op.execute('DROP TYPE IF EXISTS certificationstatus CASCADE')
    op.execute('DROP TYPE IF EXISTS claimstatus CASCADE')
    op.execute('DROP TYPE IF EXISTS capastatus CASCADE')
    op.execute('DROP TYPE IF EXISTS capatype CASCADE')
    op.execute('DROP TYPE IF EXISTS findingseverity CASCADE')
    op.execute('DROP TYPE IF EXISTS auditstatus CASCADE')
    op.execute('DROP TYPE IF EXISTS audittype CASCADE')
    op.execute('DROP TYPE IF EXISTS controlresult CASCADE')
    op.execute('DROP TYPE IF EXISTS controlstatus CASCADE')
    op.execute('DROP TYPE IF EXISTS controltype CASCADE')
    op.execute('DROP TYPE IF EXISTS nonconformanceseverity CASCADE')
    op.execute('DROP TYPE IF EXISTS nonconformancestatus CASCADE')
    op.execute('DROP TYPE IF EXISTS nonconformancetype CASCADE')
