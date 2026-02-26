"""Module Approval Workflow (GAP-083) - Workflow d'approbation

Revision ID: approval_001
Revises: fieldservice_001
Create Date: 2026-02-21

Tables:
- approval_workflows: Définition des workflows d'approbation
- approval_workflow_steps: Étapes de workflow
- approval_requests: Demandes d'approbation
- approval_actions: Actions (approve, reject, delegate)
- approval_delegations: Délégations temporaires

Multi-tenant strict, Audit complet.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'approval_001'
down_revision = 'fieldservice_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Approval module tables and enums."""

    # ==========================================================================
    # ENUM TYPES
    # ==========================================================================

    # Approval Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE approval_type AS ENUM (
                'purchase_order', 'expense_report', 'leave_request', 'timesheet',
                'invoice', 'contract', 'budget', 'requisition', 'document', 'custom'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Workflow Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE workflow_status AS ENUM (
                'active', 'inactive', 'draft', 'archived'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Request Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE request_status AS ENUM (
                'draft', 'pending', 'in_progress', 'approved', 'rejected', 'cancelled', 'expired'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Step Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE step_type AS ENUM (
                'single', 'any', 'all', 'majority', 'sequence'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Approver Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE approver_type AS ENUM (
                'user', 'role', 'manager', 'department_head', 'dynamic'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Action Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE action_type AS ENUM (
                'approve', 'reject', 'delegate', 'escalate', 'request_info', 'return'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ==========================================================================
    # APPROVAL WORKFLOWS TABLE
    # ==========================================================================

    op.create_table(
        'approval_workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),

        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('approval_type', sa.String(50), server_default='custom'),
        sa.Column('status', sa.String(20), server_default='draft'),

        # Conditions
        sa.Column('conditions', postgresql.JSONB, server_default='[]'),
        sa.Column('min_amount', sa.Numeric(18, 4), nullable=True),
        sa.Column('max_amount', sa.Numeric(18, 4), nullable=True),

        # Configuration
        sa.Column('allow_parallel_steps', sa.Boolean, server_default='false'),
        sa.Column('require_comments_on_reject', sa.Boolean, server_default='true'),
        sa.Column('allow_self_approval', sa.Boolean, server_default='false'),
        sa.Column('skip_if_approver_is_requester', sa.Boolean, server_default='true'),

        # Notifications
        sa.Column('notify_on_submit', sa.Boolean, server_default='true'),
        sa.Column('notify_on_approve', sa.Boolean, server_default='true'),
        sa.Column('notify_on_reject', sa.Boolean, server_default='true'),
        sa.Column('notify_requester', sa.Boolean, server_default='true'),

        # Priority
        sa.Column('priority', sa.Integer, server_default='0'),

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

    op.create_index('ix_approval_workflows_tenant_code', 'approval_workflows', ['tenant_id', 'code'], unique=True)
    op.create_index('ix_approval_workflows_tenant_type', 'approval_workflows', ['tenant_id', 'approval_type'])
    op.create_index('ix_approval_workflows_tenant_status', 'approval_workflows', ['tenant_id', 'status'])

    # ==========================================================================
    # APPROVAL WORKFLOW STEPS TABLE
    # ==========================================================================

    op.create_table(
        'approval_workflow_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('approval_workflows.id'), nullable=False),

        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('order', sa.Integer, server_default='0'),
        sa.Column('step_type', sa.String(20), server_default='single'),

        # Approvers (JSON array)
        sa.Column('approvers', postgresql.JSONB, server_default='[]'),

        # Conditions (JSON array)
        sa.Column('conditions', postgresql.JSONB, server_default='[]'),

        # Escalation (JSON array)
        sa.Column('escalation_rules', postgresql.JSONB, server_default='[]'),

        # Timeout
        sa.Column('timeout_hours', sa.Integer, nullable=True),
        sa.Column('auto_approve_on_timeout', sa.Boolean, server_default='false'),
        sa.Column('auto_reject_on_timeout', sa.Boolean, server_default='false'),

        # Notification
        sa.Column('notification_template', sa.String(255), nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_index('ix_approval_workflow_steps_workflow', 'approval_workflow_steps', ['workflow_id', 'order'])

    # ==========================================================================
    # APPROVAL REQUESTS TABLE
    # ==========================================================================

    op.create_table(
        'approval_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('approval_workflows.id'), nullable=False),

        sa.Column('request_number', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), server_default='draft'),

        # Requester
        sa.Column('requester_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requester_name', sa.String(255), nullable=True),
        sa.Column('requester_email', sa.String(255), nullable=True),
        sa.Column('department_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Subject
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_number', sa.String(50), nullable=True),
        sa.Column('entity_description', sa.Text, nullable=True),
        sa.Column('amount', sa.Numeric(18, 4), nullable=True),
        sa.Column('currency', sa.String(3), server_default='EUR'),

        # Workflow progress
        sa.Column('current_step', sa.Integer, server_default='0'),
        sa.Column('step_statuses', postgresql.JSONB, server_default='[]'),

        # Dates
        sa.Column('submitted_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('due_date', sa.DateTime, nullable=True),

        # Metadata
        sa.Column('priority', sa.Integer, server_default='0'),
        sa.Column('tags', postgresql.JSONB, server_default='[]'),
        sa.Column('attachments', postgresql.JSONB, server_default='[]'),
        sa.Column('custom_data', postgresql.JSONB, server_default='{}'),

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

    op.create_index('ix_approval_requests_tenant_number', 'approval_requests', ['tenant_id', 'request_number'], unique=True)
    op.create_index('ix_approval_requests_tenant_status', 'approval_requests', ['tenant_id', 'status'])
    op.create_index('ix_approval_requests_tenant_requester', 'approval_requests', ['tenant_id', 'requester_id'])
    op.create_index('ix_approval_requests_tenant_entity', 'approval_requests', ['tenant_id', 'entity_type', 'entity_id'])

    # ==========================================================================
    # APPROVAL ACTIONS TABLE
    # ==========================================================================

    op.create_table(
        'approval_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('approval_requests.id'), nullable=False),
        sa.Column('step_id', postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column('approver_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approver_name', sa.String(255), nullable=True),
        sa.Column('action_type', sa.String(20), nullable=False),
        sa.Column('comments', sa.Text, nullable=True),

        # Delegation
        sa.Column('delegated_to_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('delegated_to_name', sa.String(255), nullable=True),

        # Metadata
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('action_at', sa.DateTime, server_default=sa.text('NOW()')),
    )

    op.create_index('ix_approval_actions_request', 'approval_actions', ['request_id', 'action_at'])
    op.create_index('ix_approval_actions_approver', 'approval_actions', ['tenant_id', 'approver_id'])

    # ==========================================================================
    # APPROVAL DELEGATIONS TABLE
    # ==========================================================================

    op.create_table(
        'approval_delegations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),

        sa.Column('delegator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('delegator_name', sa.String(255), nullable=True),
        sa.Column('delegate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('delegate_name', sa.String(255), nullable=True),

        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),

        # Restrictions
        sa.Column('approval_types', postgresql.JSONB, server_default='[]'),
        sa.Column('max_amount', sa.Numeric(18, 4), nullable=True),

        sa.Column('reason', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='true'),

        # Audit
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime, nullable=True),
        sa.Column('revoked_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_index('ix_approval_delegations_delegator', 'approval_delegations', ['tenant_id', 'delegator_id', 'is_active'])
    op.create_index('ix_approval_delegations_delegate', 'approval_delegations', ['tenant_id', 'delegate_id', 'is_active'])
    op.create_index('ix_approval_delegations_dates', 'approval_delegations', ['tenant_id', 'start_date', 'end_date'])

    print("[MIGRATION] Approval Workflow module (GAP-083) tables created successfully")


def downgrade() -> None:
    """Drop Approval module tables and enums."""

    # Drop tables (reverse order)
    op.drop_table('approval_delegations')
    op.drop_table('approval_actions')
    op.drop_table('approval_requests')
    op.drop_table('approval_workflow_steps')
    op.drop_table('approval_workflows')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS action_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS approver_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS step_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS request_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS workflow_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS approval_type CASCADE;")

    print("[MIGRATION] Approval Workflow module (GAP-083) tables dropped successfully")
