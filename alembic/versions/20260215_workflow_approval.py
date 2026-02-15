"""
Workflow & Approval System tables

Revision ID: 20260215_workflow
Revises: 20260215_accounting_pending_status
Create Date: 2026-02-15

Tables:
- workflow_instances: Instances de workflows en cours
- workflow_steps: Étapes de chaque workflow
- workflow_notifications: Notifications de workflow
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260215_workflow"
down_revision = "20260215_accounting_pending_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Créer les ENUMs
    workflow_status = postgresql.ENUM(
        'DRAFT', 'PENDING', 'IN_PROGRESS', 'APPROVED', 'REJECTED', 'CANCELLED', 'EXPIRED',
        name='workflow_status',
        create_type=False
    )
    workflow_status.create(op.get_bind(), checkfirst=True)

    approval_action = postgresql.ENUM(
        'APPROVE', 'REJECT', 'DELEGATE', 'ESCALATE', 'REQUEST_INFO',
        name='approval_action',
        create_type=False
    )
    approval_action.create(op.get_bind(), checkfirst=True)

    notification_type = postgresql.ENUM(
        'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'ESCALATED', 'REMINDER', 'EXPIRED',
        name='notification_type',
        create_type=False
    )
    notification_type.create(op.get_bind(), checkfirst=True)

    # Table workflow_instances
    op.create_table(
        'workflow_instances',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_name', sa.String(100), nullable=False),
        sa.Column('workflow_version', sa.Integer(), default=1),
        sa.Column('document_type', sa.String(100), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'PENDING', 'IN_PROGRESS', 'APPROVED', 'REJECTED', 'CANCELLED', 'EXPIRED', name='workflow_status'), default='PENDING', nullable=False),
        sa.Column('current_step', sa.Integer(), default=0),
        sa.Column('total_steps', sa.Integer(), default=1),
        sa.Column('metadata', postgresql.JSONB(), default=dict),
        sa.Column('amount', sa.Integer(), nullable=True),
        sa.Column('initiated_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('initiated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('ix_workflow_instances_tenant_id', 'workflow_instances', ['tenant_id'])
    op.create_index('ix_workflow_tenant_doc', 'workflow_instances', ['tenant_id', 'document_type', 'document_id'])
    op.create_index('ix_workflow_status', 'workflow_instances', ['tenant_id', 'status'])

    # Table workflow_steps
    op.create_table(
        'workflow_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('step_name', sa.String(100), nullable=False),
        sa.Column('required_role', sa.String(100), nullable=False),
        sa.Column('required_permission', sa.String(100), nullable=True),
        sa.Column('threshold_amount', sa.Integer(), nullable=True),
        sa.Column('threshold_condition', sa.String(20), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'PENDING', 'IN_PROGRESS', 'APPROVED', 'REJECTED', 'CANCELLED', 'EXPIRED', name='workflow_status'), default='PENDING', nullable=False),
        sa.Column('action_taken', sa.Enum('APPROVE', 'REJECT', 'DELEGATE', 'ESCALATE', 'REQUEST_INFO', name='approval_action'), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reminder_sent', sa.Boolean(), default=False),
        sa.Column('escalated', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflow_instances.id'], ondelete='CASCADE'),
    )

    op.create_index('ix_step_workflow', 'workflow_steps', ['workflow_id', 'step_number'])
    op.create_index('ix_step_assigned', 'workflow_steps', ['assigned_to', 'status'])

    # Table workflow_notifications
    op.create_table(
        'workflow_notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notification_type', sa.Enum('PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'ESCALATED', 'REMINDER', 'EXPIRED', name='notification_type'), nullable=False),
        sa.Column('recipient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('link', sa.String(500), nullable=True),
        sa.Column('is_read', sa.Boolean(), default=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflow_instances.id'], ondelete='CASCADE'),
    )

    op.create_index('ix_workflow_notifications_tenant_id', 'workflow_notifications', ['tenant_id'])
    op.create_index('ix_notif_recipient_read', 'workflow_notifications', ['recipient_id', 'is_read'])


def downgrade() -> None:
    op.drop_table('workflow_notifications')
    op.drop_table('workflow_steps')
    op.drop_table('workflow_instances')

    # Drop ENUMs
    op.execute("DROP TYPE IF EXISTS notification_type")
    op.execute("DROP TYPE IF EXISTS approval_action")
    op.execute("DROP TYPE IF EXISTS workflow_status")
