"""
AZALSCORE - Workflow Automation Types
Types, enums et dataclasses pour l'automatisation des workflows
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ============================================================================
# Enums
# ============================================================================

class WorkflowStatus(str, Enum):
    """Statut d'un workflow"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    """Statut d'exécution"""
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TriggerType(str, Enum):
    """Types de déclencheurs"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT = "event"
    WEBHOOK = "webhook"
    CONDITION = "condition"


class ActionType(str, Enum):
    """Types d'actions"""
    SEND_EMAIL = "send_email"
    SEND_NOTIFICATION = "send_notification"
    UPDATE_RECORD = "update_record"
    CREATE_RECORD = "create_record"
    HTTP_REQUEST = "http_request"
    EXECUTE_SCRIPT = "execute_script"
    APPROVAL = "approval"
    DELAY = "delay"
    CONDITION = "condition"
    PARALLEL = "parallel"
    LOOP = "loop"
    SET_VARIABLE = "set_variable"
    LOG = "log"
    CALL_WORKFLOW = "call_workflow"


class ConditionOperator(str, Enum):
    """Opérateurs de condition"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_THAN = "less_than"
    LESS_OR_EQUAL = "less_or_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
    MATCHES_REGEX = "matches_regex"


class ApprovalStatus(str, Enum):
    """Statut d'approbation"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    EXPIRED = "expired"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class WorkflowVariable:
    """Variable de workflow"""
    name: str
    value: Any
    data_type: str = "string"
    is_input: bool = False
    is_output: bool = False
    description: str = ""


@dataclass
class Condition:
    """Condition d'évaluation"""
    field: str
    operator: ConditionOperator
    value: Any
    logical_operator: str = "AND"


@dataclass
class ConditionGroup:
    """Groupe de conditions"""
    conditions: list[Condition]
    logical_operator: str = "AND"


@dataclass
class TriggerConfig:
    """Configuration d'un déclencheur"""
    type: TriggerType
    event_name: Optional[str] = None
    schedule: Optional[str] = None
    conditions: Optional[ConditionGroup] = None
    webhook_secret: Optional[str] = None


@dataclass
class ActionConfig:
    """Configuration d'une action"""
    id: str
    type: ActionType
    name: str
    description: str = ""
    parameters: dict = field(default_factory=dict)
    timeout_seconds: int = 300
    retry_count: int = 0
    retry_delay_seconds: int = 60
    on_error: str = "fail"
    conditions: Optional[ConditionGroup] = None
    next_action_id: Optional[str] = None
    on_true_action_id: Optional[str] = None
    on_false_action_id: Optional[str] = None


@dataclass
class ApprovalConfig:
    """Configuration d'approbation"""
    approvers: list[str]
    approval_type: str = "any"
    min_approvals: int = 1
    escalation_timeout_hours: int = 24
    escalation_to: Optional[list[str]] = None
    reminder_hours: list[int] = field(default_factory=lambda: [4, 12])
    allow_delegation: bool = False
    require_comment: bool = False


@dataclass
class WorkflowDefinition:
    """Définition d'un workflow"""
    id: str
    name: str
    description: str
    version: int
    tenant_id: str
    entity_type: Optional[str]
    triggers: list[TriggerConfig]
    actions: list[ActionConfig]
    variables: list[WorkflowVariable] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ActionResult:
    """Résultat d'exécution d'une action"""
    action_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime]
    output: Any = None
    error: Optional[str] = None
    duration_ms: int = 0


@dataclass
class ApprovalRequest:
    """Demande d'approbation"""
    id: str
    execution_id: str
    action_id: str
    tenant_id: str
    approvers: list[str]
    approval_config: ApprovalConfig
    entity_type: str
    entity_id: str
    entity_data: dict
    status: ApprovalStatus
    created_at: datetime
    expires_at: datetime
    decisions: list[dict] = field(default_factory=list)
    comments: list[dict] = field(default_factory=list)
    escalation_count: int = 0


@dataclass
class WorkflowExecution:
    """Exécution d'un workflow"""
    id: str
    workflow_id: str
    workflow_version: int
    tenant_id: str
    trigger_type: TriggerType
    trigger_data: dict
    entity_type: Optional[str]
    entity_id: Optional[str]
    status: ExecutionStatus
    current_action_id: Optional[str]
    variables: dict
    action_results: list[ActionResult]
    started_at: datetime
    completed_at: Optional[datetime]
    error: Optional[str] = None
    parent_execution_id: Optional[str] = None
    retry_count: int = 0


@dataclass
class ScheduledWorkflow:
    """Workflow planifié"""
    id: str
    workflow_id: str
    tenant_id: str
    schedule: str
    next_run_at: datetime
    last_run_at: Optional[datetime]
    last_run_status: Optional[ExecutionStatus]
    is_active: bool
    created_at: datetime
    input_variables: dict = field(default_factory=dict)
