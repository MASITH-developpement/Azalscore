"""
Schémas Pydantic - Module Approval Workflow (GAP-083)
"""
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


# ============== Enums ==============

class ApprovalType(str, Enum):
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
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"


class RequestStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class StepType(str, Enum):
    SINGLE = "single"
    ANY = "any"
    ALL = "all"
    MAJORITY = "majority"
    SEQUENCE = "sequence"


class ApproverType(str, Enum):
    USER = "user"
    ROLE = "role"
    MANAGER = "manager"
    DEPARTMENT_HEAD = "department_head"
    DYNAMIC = "dynamic"


class ActionType(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    DELEGATE = "delegate"
    ESCALATE = "escalate"
    REQUEST_INFO = "request_info"
    RETURN = "return"


# ============== Sub-schemas ==============

class ConditionSchema(BaseModel):
    field: str
    operator: str
    value: Any
    value2: Optional[Any] = None


class ApproverSchema(BaseModel):
    approver_type: ApproverType
    approver_id: UUID
    approver_name: str
    order: int = 0
    is_required: bool = True
    can_delegate: bool = True


class EscalationRuleSchema(BaseModel):
    trigger_hours: int = Field(..., ge=1)
    escalate_to_type: ApproverType
    escalate_to_id: UUID
    escalate_to_name: str
    notify_original: bool = True
    auto_approve: bool = False


class StepStatusSchema(BaseModel):
    step_id: UUID
    step_name: str
    status: str = "pending"
    required_approvals: int = 1
    received_approvals: int = 0
    received_rejections: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    pending_approvers: List[UUID] = Field(default_factory=list)


# ============== Workflow Schemas ==============

class WorkflowStepBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    order: int = 0
    step_type: StepType = StepType.SINGLE
    approvers: List[ApproverSchema] = Field(default_factory=list)
    conditions: List[ConditionSchema] = Field(default_factory=list)
    escalation_rules: List[EscalationRuleSchema] = Field(default_factory=list)
    timeout_hours: Optional[int] = Field(None, ge=1)
    auto_approve_on_timeout: bool = False
    auto_reject_on_timeout: bool = False
    notification_template: Optional[str] = None


class WorkflowStepCreate(WorkflowStepBase):
    pass


class WorkflowStepResponse(WorkflowStepBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    workflow_id: UUID
    created_at: datetime


class WorkflowBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    approval_type: ApprovalType = ApprovalType.CUSTOM
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    allow_parallel_steps: bool = False
    require_comments_on_reject: bool = True
    allow_self_approval: bool = False
    skip_if_approver_is_requester: bool = True
    notify_on_submit: bool = True
    notify_on_approve: bool = True
    notify_on_reject: bool = True
    notify_requester: bool = True
    priority: int = Field(default=0, ge=0)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v


class WorkflowCreate(WorkflowBase):
    steps: List[WorkflowStepCreate] = Field(default_factory=list)
    conditions: List[ConditionSchema] = Field(default_factory=list)


class WorkflowUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    approval_type: Optional[ApprovalType] = None
    status: Optional[WorkflowStatus] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    allow_parallel_steps: Optional[bool] = None
    require_comments_on_reject: Optional[bool] = None
    allow_self_approval: Optional[bool] = None
    skip_if_approver_is_requester: Optional[bool] = None
    notify_on_submit: Optional[bool] = None
    notify_on_approve: Optional[bool] = None
    notify_on_reject: Optional[bool] = None
    notify_requester: Optional[bool] = None
    priority: Optional[int] = None
    conditions: Optional[List[ConditionSchema]] = None


class WorkflowResponse(WorkflowBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    status: WorkflowStatus
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    steps: List[WorkflowStepResponse] = Field(default_factory=list)
    version: int = 1
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    is_deleted: bool = False


class WorkflowListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    approval_type: ApprovalType
    status: WorkflowStatus
    steps_count: int = 0
    created_at: datetime


class WorkflowList(BaseModel):
    items: List[WorkflowListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Request Schemas ==============

class ApprovalRequestBase(BaseModel):
    entity_type: str = Field(..., max_length=100)
    entity_id: UUID
    entity_number: Optional[str] = Field(None, max_length=50)
    entity_description: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: str = Field(default="EUR", max_length=3)
    due_date: Optional[datetime] = None
    priority: int = Field(default=0, ge=0)
    tags: List[str] = Field(default_factory=list)
    custom_data: Dict[str, Any] = Field(default_factory=dict)


class ApprovalRequestCreate(ApprovalRequestBase):
    workflow_id: UUID


class ApprovalRequestUpdate(BaseModel):
    entity_description: Optional[str] = None
    amount: Optional[Decimal] = None
    due_date: Optional[datetime] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None
    custom_data: Optional[Dict[str, Any]] = None


class ApprovalRequestResponse(ApprovalRequestBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    workflow_id: UUID
    request_number: str
    status: RequestStatus
    requester_id: UUID
    requester_name: Optional[str] = None
    requester_email: Optional[str] = None
    department_id: Optional[UUID] = None
    current_step: int = 0
    step_statuses: List[Dict[str, Any]] = Field(default_factory=list)
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    version: int = 1
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False


class ApprovalRequestListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_number: str
    status: RequestStatus
    entity_type: str
    entity_number: Optional[str] = None
    entity_description: Optional[str] = None
    amount: Optional[Decimal] = None
    requester_name: Optional[str] = None
    current_step: int
    submitted_at: Optional[datetime] = None
    due_date: Optional[datetime] = None


class ApprovalRequestList(BaseModel):
    items: List[ApprovalRequestListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Action Schemas ==============

class TakeActionRequest(BaseModel):
    action_type: ActionType
    comments: Optional[str] = Field(None, max_length=2000)
    delegate_to_id: Optional[UUID] = None
    delegate_to_name: Optional[str] = None


class ApprovalActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_id: UUID
    step_id: Optional[UUID] = None
    approver_id: UUID
    approver_name: Optional[str] = None
    action_type: ActionType
    comments: Optional[str] = None
    delegated_to_id: Optional[UUID] = None
    delegated_to_name: Optional[str] = None
    action_at: datetime


# ============== Delegation Schemas ==============

class DelegationBase(BaseModel):
    delegate_id: UUID
    delegate_name: str = Field(..., max_length=255)
    start_date: date
    end_date: date
    approval_types: List[ApprovalType] = Field(default_factory=list)
    max_amount: Optional[Decimal] = None
    reason: Optional[str] = None


class DelegationCreate(DelegationBase):
    pass


class DelegationResponse(DelegationBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    delegator_id: UUID
    delegator_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    revoked_at: Optional[datetime] = None


class DelegationList(BaseModel):
    items: List[DelegationResponse]
    total: int


# ============== Stats ==============

class ApprovalStatsResponse(BaseModel):
    tenant_id: UUID
    period_start: date
    period_end: date
    total_requests: int = 0
    pending_requests: int = 0
    approved_requests: int = 0
    rejected_requests: int = 0
    average_approval_time_hours: Decimal = Decimal("0")
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_department: Dict[str, int] = Field(default_factory=dict)


# ============== Filters ==============

class WorkflowFilters(BaseModel):
    search: Optional[str] = Field(None, min_length=2)
    status: Optional[List[WorkflowStatus]] = None
    approval_type: Optional[List[ApprovalType]] = None


class ApprovalRequestFilters(BaseModel):
    search: Optional[str] = Field(None, min_length=2)
    status: Optional[List[RequestStatus]] = None
    entity_type: Optional[str] = None
    requester_id: Optional[UUID] = None
    pending_for_user: Optional[UUID] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


# ============== Common ==============

class AutocompleteItem(BaseModel):
    id: str
    code: str
    name: str
    label: str


class AutocompleteResponse(BaseModel):
    items: List[AutocompleteItem]
