"""
Models SQLAlchemy - Module Approval Workflow (GAP-083)

CRITIQUE: Tous les modèles ont tenant_id pour isolation multi-tenant.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, Numeric,
    ForeignKey, Index, JSON, Date
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


# ============== Enums ==============

class ApprovalType(str, Enum):
    """Types d'approbation"""
    PURCHASE_ORDER = "purchase_order"
    EXPENSE_REPORT = "expense_report"
    LEAVE_REQUEST = "leave_request"
    TIMESHEET = "timesheet"
    INVOICE = "invoice"
    CONTRACT = "contract"
    BUDGET = "budget"
    REQUISITION = "requisition"
    DOCUMENT = "document"
    CUSTOM = "custom"


class WorkflowStatus(str, Enum):
    """Statuts workflow"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"


class RequestStatus(str, Enum):
    """Statuts demande"""
    DRAFT = "draft"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

    def allowed_transitions(self) -> List["RequestStatus"]:
        """Transitions autorisées"""
        transitions = {
            RequestStatus.DRAFT: [RequestStatus.PENDING, RequestStatus.CANCELLED],
            RequestStatus.PENDING: [RequestStatus.IN_PROGRESS, RequestStatus.CANCELLED],
            RequestStatus.IN_PROGRESS: [RequestStatus.APPROVED, RequestStatus.REJECTED, RequestStatus.CANCELLED, RequestStatus.EXPIRED],
            RequestStatus.APPROVED: [],
            RequestStatus.REJECTED: [RequestStatus.DRAFT],
            RequestStatus.CANCELLED: [],
            RequestStatus.EXPIRED: [],
        }
        return transitions.get(self, [])


class StepType(str, Enum):
    """Types d'étape"""
    SINGLE = "single"
    ANY = "any"
    ALL = "all"
    MAJORITY = "majority"
    SEQUENCE = "sequence"


class ApproverType(str, Enum):
    """Types d'approbateur"""
    USER = "user"
    ROLE = "role"
    MANAGER = "manager"
    DEPARTMENT_HEAD = "department_head"
    DYNAMIC = "dynamic"


class ActionType(str, Enum):
    """Types d'action"""
    APPROVE = "approve"
    REJECT = "reject"
    DELEGATE = "delegate"
    ESCALATE = "escalate"
    REQUEST_INFO = "request_info"
    RETURN = "return"


class ConditionOperator(str, Enum):
    """Opérateurs de condition"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_OR_EQUAL = "less_or_equal"
    CONTAINS = "contains"
    IN = "in"
    BETWEEN = "between"


# ============== Models ==============

class Workflow(Base):
    """Workflow d'approbation"""
    __tablename__ = "approval_workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    approval_type = Column(String(50), default=ApprovalType.CUSTOM.value)
    status = Column(String(20), default=WorkflowStatus.DRAFT.value)

    # Conditions d'activation
    conditions = Column(JSON, default=list)
    min_amount = Column(Numeric(18, 4))
    max_amount = Column(Numeric(18, 4))

    # Configuration
    allow_parallel_steps = Column(Boolean, default=False)
    require_comments_on_reject = Column(Boolean, default=True)
    allow_self_approval = Column(Boolean, default=False)
    skip_if_approver_is_requester = Column(Boolean, default=True)

    # Notifications
    notify_on_submit = Column(Boolean, default=True)
    notify_on_approve = Column(Boolean, default=True)
    notify_on_reject = Column(Boolean, default=True)
    notify_requester = Column(Boolean, default=True)

    # Priorité pour workflow matching
    priority = Column(Integer, default=0)

    # Audit
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID(as_uuid=True))

    # Relations
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan")
    requests = relationship("ApprovalRequest", back_populates="workflow")

    __table_args__ = (
        Index("ix_approval_workflows_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_approval_workflows_tenant_type", "tenant_id", "approval_type"),
        Index("ix_approval_workflows_tenant_status", "tenant_id", "status"),
    )


class WorkflowStep(Base):
    """Étape de workflow"""
    __tablename__ = "approval_workflow_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("approval_workflows.id"), nullable=False)

    name = Column(String(255), nullable=False)
    description = Column(Text)
    order = Column(Integer, default=0)
    step_type = Column(String(20), default=StepType.SINGLE.value)

    # Approbateurs (JSON array)
    approvers = Column(JSON, default=list)

    # Conditions (JSON array)
    conditions = Column(JSON, default=list)

    # Escalade (JSON array)
    escalation_rules = Column(JSON, default=list)

    # Timeout
    timeout_hours = Column(Integer)
    auto_approve_on_timeout = Column(Boolean, default=False)
    auto_reject_on_timeout = Column(Boolean, default=False)

    # Notification
    notification_template = Column(String(255))

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))

    # Relations
    workflow = relationship("Workflow", back_populates="steps")

    __table_args__ = (
        Index("ix_approval_workflow_steps_workflow", "workflow_id", "order"),
    )


class ApprovalRequest(Base):
    """Demande d'approbation"""
    __tablename__ = "approval_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("approval_workflows.id"), nullable=False)

    request_number = Column(String(50), nullable=False)
    status = Column(String(20), default=RequestStatus.DRAFT.value)

    # Demandeur
    requester_id = Column(UUID(as_uuid=True), nullable=False)
    requester_name = Column(String(255))
    requester_email = Column(String(255))
    department_id = Column(UUID(as_uuid=True))

    # Objet de la demande
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    entity_number = Column(String(50))
    entity_description = Column(Text)
    amount = Column(Numeric(18, 4))
    currency = Column(String(3), default="EUR")

    # Workflow progress
    current_step = Column(Integer, default=0)
    step_statuses = Column(JSON, default=list)

    # Dates
    submitted_at = Column(DateTime)
    completed_at = Column(DateTime)
    due_date = Column(DateTime)

    # Métadonnées
    priority = Column(Integer, default=0)
    tags = Column(JSON, default=list)
    attachments = Column(JSON, default=list)
    custom_data = Column(JSON, default=dict)

    # Audit
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID(as_uuid=True))

    # Relations
    workflow = relationship("Workflow", back_populates="requests")
    actions = relationship("ApprovalAction", back_populates="request", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_approval_requests_tenant_number", "tenant_id", "request_number", unique=True),
        Index("ix_approval_requests_tenant_status", "tenant_id", "status"),
        Index("ix_approval_requests_tenant_requester", "tenant_id", "requester_id"),
        Index("ix_approval_requests_tenant_entity", "tenant_id", "entity_type", "entity_id"),
    )


class ApprovalAction(Base):
    """Action d'approbation"""
    __tablename__ = "approval_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    request_id = Column(UUID(as_uuid=True), ForeignKey("approval_requests.id"), nullable=False)
    step_id = Column(UUID(as_uuid=True))

    approver_id = Column(UUID(as_uuid=True), nullable=False)
    approver_name = Column(String(255))
    action_type = Column(String(20), nullable=False)
    comments = Column(Text)

    # Délégation
    delegated_to_id = Column(UUID(as_uuid=True))
    delegated_to_name = Column(String(255))

    # Métadonnées
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    action_at = Column(DateTime, default=datetime.utcnow)

    # Relation
    request = relationship("ApprovalRequest", back_populates="actions")

    __table_args__ = (
        Index("ix_approval_actions_request", "request_id", "action_at"),
        Index("ix_approval_actions_approver", "tenant_id", "approver_id"),
    )


class Delegation(Base):
    """Délégation d'approbation"""
    __tablename__ = "approval_delegations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    delegator_id = Column(UUID(as_uuid=True), nullable=False)
    delegator_name = Column(String(255))
    delegate_id = Column(UUID(as_uuid=True), nullable=False)
    delegate_name = Column(String(255))

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Restrictions
    approval_types = Column(JSON, default=list)
    max_amount = Column(Numeric(18, 4))

    reason = Column(Text)
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))
    revoked_at = Column(DateTime)
    revoked_by = Column(UUID(as_uuid=True))

    __table_args__ = (
        Index("ix_approval_delegations_delegator", "tenant_id", "delegator_id", "is_active"),
        Index("ix_approval_delegations_delegate", "tenant_id", "delegate_id", "is_active"),
        Index("ix_approval_delegations_dates", "tenant_id", "start_date", "end_date"),
    )
