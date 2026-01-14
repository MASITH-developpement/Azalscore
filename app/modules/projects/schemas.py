"""
AZALS MODULE M9 - Schémas Projets
=================================

Schémas Pydantic pour la gestion de projets.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import (
    BudgetType,
    ExpenseStatus,
    IssuePriority,
    IssueStatus,
    MilestoneStatus,
    ProjectPriority,
    ProjectStatus,
    RiskImpact,
    RiskProbability,
    RiskStatus,
    TaskPriority,
    TaskStatus,
    TeamMemberRole,
    TimeEntryStatus,
)

# ============================================================================
# SCHÉMAS PROJET
# ============================================================================

class ProjectBase(BaseModel):
    """Base pour les projets."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator('tags', mode='before')
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else []
        return v or []


class ProjectCreate(ProjectBase):
    """Création d'un projet."""
    priority: ProjectPriority = ProjectPriority.MEDIUM
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    project_manager_id: UUID | None = None
    sponsor_id: UUID | None = None
    customer_id: UUID | None = None
    budget_type: BudgetType | None = None
    planned_budget: Decimal = Decimal("0")
    currency: str = "EUR"
    planned_hours: float = 0
    is_billable: bool = False
    billing_rate: Decimal | None = None
    parent_project_id: UUID | None = None
    template_id: UUID | None = None
    settings: dict = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    """Mise à jour d'un projet."""
    name: str | None = None
    description: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    status: ProjectStatus | None = None
    priority: ProjectPriority | None = None
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    actual_start_date: date | None = None
    actual_end_date: date | None = None
    project_manager_id: UUID | None = None
    sponsor_id: UUID | None = None
    customer_id: UUID | None = None
    planned_budget: Decimal | None = None
    planned_hours: float | None = None
    progress_percent: float | None = None
    health_status: str | None = None
    is_billable: bool | None = None
    billing_rate: Decimal | None = None
    settings: dict | None = None
    is_active: bool | None = None


class ProjectResponse(ProjectBase):
    """Réponse projet."""
    id: UUID
    status: ProjectStatus = ProjectStatus.DRAFT
    priority: ProjectPriority = ProjectPriority.MEDIUM
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    actual_start_date: date | None = None
    actual_end_date: date | None = None
    project_manager_id: UUID | None = None
    sponsor_id: UUID | None = None
    customer_id: UUID | None = None
    budget_type: BudgetType | None = None
    planned_budget: Decimal = Decimal("0")
    actual_cost: Decimal = Decimal("0")
    currency: str = "EUR"
    planned_hours: float = 0
    actual_hours: float = 0
    progress_percent: float = 0
    health_status: str | None = None
    parent_project_id: UUID | None = None
    is_billable: bool = False
    billing_rate: Decimal | None = None
    is_active: bool = True
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ProjectList(BaseModel):
    """Liste de projets."""
    items: list[ProjectResponse]
    total: int
    page: int = 1
    page_size: int = 20


class ProjectSummary(BaseModel):
    """Résumé d'un projet."""
    id: UUID
    code: str
    name: str
    status: ProjectStatus
    priority: ProjectPriority
    progress_percent: float
    health_status: str | None = None
    planned_end_date: date | None = None
    tasks_total: int = 0
    tasks_completed: int = 0
    team_size: int = 0


# ============================================================================
# SCHÉMAS PHASE
# ============================================================================

class PhaseBase(BaseModel):
    """Base pour les phases."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    order: int = 0
    color: str | None = None


class PhaseCreate(PhaseBase):
    """Création d'une phase."""
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    planned_hours: float = 0
    planned_budget: Decimal = Decimal("0")


class PhaseUpdate(BaseModel):
    """Mise à jour d'une phase."""
    name: str | None = None
    description: str | None = None
    order: int | None = None
    color: str | None = None
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    actual_start_date: date | None = None
    actual_end_date: date | None = None
    status: TaskStatus | None = None
    progress_percent: float | None = None


class PhaseResponse(PhaseBase):
    """Réponse phase."""
    id: UUID
    project_id: UUID
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    actual_start_date: date | None = None
    actual_end_date: date | None = None
    progress_percent: float = 0
    status: TaskStatus = TaskStatus.TODO
    planned_hours: float = 0
    actual_hours: float = 0
    planned_budget: Decimal = Decimal("0")
    actual_cost: Decimal = Decimal("0")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS TÂCHE
# ============================================================================

class TaskDependencyCreate(BaseModel):
    """Création d'une dépendance."""
    predecessor_id: UUID
    dependency_type: str = "FS"  # FS, FF, SS, SF
    lag_days: int = 0


class TaskBase(BaseModel):
    """Base pour les tâches."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    task_type: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator('tags', mode='before')
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else []
        return v or []


class TaskCreate(TaskBase):
    """Création d'une tâche."""
    phase_id: UUID | None = None
    parent_task_id: UUID | None = None
    code: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    due_date: date | None = None
    assignee_id: UUID | None = None
    estimated_hours: float = 0
    order: int = 0
    wbs_code: str | None = None
    is_milestone: bool = False
    is_critical: bool = False
    is_billable: bool = True
    dependencies: list[TaskDependencyCreate] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """Mise à jour d'une tâche."""
    name: str | None = None
    description: str | None = None
    phase_id: UUID | None = None
    parent_task_id: UUID | None = None
    task_type: str | None = None
    tags: list[str] | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    due_date: date | None = None
    assignee_id: UUID | None = None
    estimated_hours: float | None = None
    remaining_hours: float | None = None
    progress_percent: float | None = None
    order: int | None = None
    is_critical: bool | None = None
    is_billable: bool | None = None


class TaskResponse(TaskBase):
    """Réponse tâche."""
    id: UUID
    project_id: UUID
    phase_id: UUID | None = None
    parent_task_id: UUID | None = None
    code: str | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    actual_start_date: date | None = None
    actual_end_date: date | None = None
    due_date: date | None = None
    assignee_id: UUID | None = None
    reporter_id: UUID | None = None
    estimated_hours: float = 0
    actual_hours: float = 0
    remaining_hours: float = 0
    progress_percent: float = 0
    order: int = 0
    wbs_code: str | None = None
    is_milestone: bool = False
    is_critical: bool = False
    is_billable: bool = True
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TaskList(BaseModel):
    """Liste de tâches."""
    items: list[TaskResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ============================================================================
# SCHÉMAS JALON
# ============================================================================

class MilestoneBase(BaseModel):
    """Base pour les jalons."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    target_date: date
    is_key_milestone: bool = False
    is_customer_visible: bool = True


class MilestoneCreate(MilestoneBase):
    """Création d'un jalon."""
    phase_id: UUID | None = None
    deliverables: list[str] = Field(default_factory=list)
    acceptance_criteria: str | None = None


class MilestoneUpdate(BaseModel):
    """Mise à jour d'un jalon."""
    name: str | None = None
    description: str | None = None
    target_date: date | None = None
    actual_date: date | None = None
    status: MilestoneStatus | None = None
    is_key_milestone: bool | None = None
    is_customer_visible: bool | None = None
    deliverables: list[str] | None = None
    acceptance_criteria: str | None = None
    validation_notes: str | None = None


class MilestoneResponse(MilestoneBase):
    """Réponse jalon."""
    id: UUID
    project_id: UUID
    phase_id: UUID | None = None
    status: MilestoneStatus = MilestoneStatus.PENDING
    actual_date: date | None = None
    deliverables: list[str] = Field(default_factory=list)
    acceptance_criteria: str | None = None
    validated_by: UUID | None = None
    validated_at: datetime | None = None
    validation_notes: str | None = None
    created_by: UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS ÉQUIPE
# ============================================================================

class TeamMemberBase(BaseModel):
    """Base pour les membres d'équipe."""
    user_id: UUID
    role: TeamMemberRole = TeamMemberRole.MEMBER
    role_description: str | None = None


class TeamMemberCreate(TeamMemberBase):
    """Ajout d'un membre."""
    employee_id: UUID | None = None
    allocation_percent: float = 100
    start_date: date | None = None
    end_date: date | None = None
    hourly_rate: Decimal | None = None
    daily_rate: Decimal | None = None
    is_billable: bool = True
    can_log_time: bool = True
    can_view_budget: bool = False
    can_manage_tasks: bool = False
    can_approve_time: bool = False


class TeamMemberUpdate(BaseModel):
    """Mise à jour d'un membre."""
    role: TeamMemberRole | None = None
    role_description: str | None = None
    allocation_percent: float | None = None
    start_date: date | None = None
    end_date: date | None = None
    hourly_rate: Decimal | None = None
    daily_rate: Decimal | None = None
    is_billable: bool | None = None
    can_log_time: bool | None = None
    can_view_budget: bool | None = None
    can_manage_tasks: bool | None = None
    can_approve_time: bool | None = None
    is_active: bool | None = None


class TeamMemberResponse(TeamMemberBase):
    """Réponse membre."""
    id: UUID
    project_id: UUID
    employee_id: UUID | None = None
    allocation_percent: float = 100
    start_date: date | None = None
    end_date: date | None = None
    hourly_rate: Decimal | None = None
    daily_rate: Decimal | None = None
    is_billable: bool = True
    can_log_time: bool = True
    can_view_budget: bool = False
    can_manage_tasks: bool = False
    can_approve_time: bool = False
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS RISQUE
# ============================================================================

class RiskBase(BaseModel):
    """Base pour les risques."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None
    probability: RiskProbability
    impact: RiskImpact


class RiskCreate(RiskBase):
    """Création d'un risque."""
    code: str | None = None
    owner_id: UUID | None = None
    response_strategy: str | None = None
    mitigation_plan: str | None = None
    contingency_plan: str | None = None
    triggers: list[str] = Field(default_factory=list)
    estimated_impact_min: Decimal | None = None
    estimated_impact_max: Decimal | None = None
    review_date: date | None = None


class RiskUpdate(BaseModel):
    """Mise à jour d'un risque."""
    title: str | None = None
    description: str | None = None
    category: str | None = None
    status: RiskStatus | None = None
    probability: RiskProbability | None = None
    impact: RiskImpact | None = None
    owner_id: UUID | None = None
    response_strategy: str | None = None
    mitigation_plan: str | None = None
    contingency_plan: str | None = None
    triggers: list[str] | None = None
    monitoring_notes: str | None = None
    review_date: date | None = None


class RiskResponse(RiskBase):
    """Réponse risque."""
    id: UUID
    project_id: UUID
    code: str | None = None
    status: RiskStatus = RiskStatus.IDENTIFIED
    risk_score: float | None = None
    estimated_impact_min: Decimal | None = None
    estimated_impact_max: Decimal | None = None
    identified_date: date
    review_date: date | None = None
    occurred_date: date | None = None
    closed_date: date | None = None
    owner_id: UUID | None = None
    response_strategy: str | None = None
    mitigation_plan: str | None = None
    contingency_plan: str | None = None
    triggers: list[str] = Field(default_factory=list)
    monitoring_notes: str | None = None
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskList(BaseModel):
    """Liste de risques."""
    items: list[RiskResponse]
    total: int


# ============================================================================
# SCHÉMAS ISSUE
# ============================================================================

class IssueBase(BaseModel):
    """Base pour les issues."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None
    priority: IssuePriority = IssuePriority.MEDIUM


class IssueCreate(IssueBase):
    """Création d'une issue."""
    task_id: UUID | None = None
    code: str | None = None
    assignee_id: UUID | None = None
    due_date: date | None = None
    impact_description: str | None = None
    affected_areas: list[str] = Field(default_factory=list)
    related_risk_id: UUID | None = None


class IssueUpdate(BaseModel):
    """Mise à jour d'une issue."""
    title: str | None = None
    description: str | None = None
    category: str | None = None
    status: IssueStatus | None = None
    priority: IssuePriority | None = None
    assignee_id: UUID | None = None
    due_date: date | None = None
    impact_description: str | None = None
    affected_areas: list[str] | None = None
    resolution: str | None = None
    resolution_type: str | None = None


class IssueResponse(IssueBase):
    """Réponse issue."""
    id: UUID
    project_id: UUID
    task_id: UUID | None = None
    code: str | None = None
    status: IssueStatus = IssueStatus.OPEN
    reporter_id: UUID | None = None
    assignee_id: UUID | None = None
    reported_date: date
    due_date: date | None = None
    resolved_date: date | None = None
    closed_date: date | None = None
    impact_description: str | None = None
    affected_areas: list[str] = Field(default_factory=list)
    resolution: str | None = None
    resolution_type: str | None = None
    is_escalated: bool = False
    related_risk_id: UUID | None = None
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IssueList(BaseModel):
    """Liste d'issues."""
    items: list[IssueResponse]
    total: int


# ============================================================================
# SCHÉMAS TIME ENTRY
# ============================================================================

class TimeEntryBase(BaseModel):
    """Base pour les saisies de temps."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    entry_date: date = Field(..., alias="date")
    hours: float = Field(..., gt=0)
    description: str | None = None
    activity_type: str | None = None


class TimeEntryCreate(TimeEntryBase):
    """Création d'une saisie."""
    task_id: UUID | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    is_billable: bool = True
    is_overtime: bool = False


class TimeEntryUpdate(BaseModel):
    """Mise à jour d'une saisie."""
    date: date | None = None
    hours: float | None = None
    description: str | None = None
    activity_type: str | None = None
    task_id: UUID | None = None
    is_billable: bool | None = None
    is_overtime: bool | None = None


class TimeEntryResponse(TimeEntryBase):
    """Réponse saisie."""
    id: UUID
    project_id: UUID
    task_id: UUID | None = None
    user_id: UUID
    employee_id: UUID | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: TimeEntryStatus = TimeEntryStatus.DRAFT
    is_billable: bool = True
    billing_rate: Decimal | None = None
    billing_amount: Decimal | None = None
    is_invoiced: bool = False
    is_overtime: bool = False
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TimeEntryList(BaseModel):
    """Liste de saisies."""
    items: list[TimeEntryResponse]
    total: int
    total_hours: float = 0
    billable_hours: float = 0


# ============================================================================
# SCHÉMAS EXPENSE
# ============================================================================

class ExpenseBase(BaseModel):
    """Base pour les dépenses."""
    description: str = Field(..., min_length=1)
    category: str | None = None
    amount: Decimal = Field(..., gt=0)
    expense_date: date


class ExpenseCreate(ExpenseBase):
    """Création d'une dépense."""
    task_id: UUID | None = None
    budget_line_id: UUID | None = None
    reference: str | None = None
    currency: str = "EUR"
    quantity: float = 1
    unit_price: Decimal | None = None
    vendor: str | None = None
    is_billable: bool = True
    receipt_url: str | None = None
    attachments: list[str] = Field(default_factory=list)


class ExpenseUpdate(BaseModel):
    """Mise à jour d'une dépense."""
    description: str | None = None
    category: str | None = None
    amount: Decimal | None = None
    expense_date: date | None = None
    vendor: str | None = None
    is_billable: bool | None = None
    receipt_url: str | None = None


class ExpenseResponse(ExpenseBase):
    """Réponse dépense."""
    id: UUID
    project_id: UUID
    task_id: UUID | None = None
    budget_line_id: UUID | None = None
    reference: str | None = None
    currency: str = "EUR"
    quantity: float = 1
    unit_price: Decimal | None = None
    due_date: date | None = None
    paid_date: date | None = None
    status: ExpenseStatus = ExpenseStatus.DRAFT
    submitted_by: UUID | None = None
    vendor: str | None = None
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    is_billable: bool = True
    is_invoiced: bool = False
    receipt_url: str | None = None
    attachments: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS DOCUMENT
# ============================================================================

class DocumentBase(BaseModel):
    """Base pour les documents."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None


class DocumentCreate(DocumentBase):
    """Création d'un document."""
    file_name: str | None = None
    file_url: str | None = None
    file_size: int | None = None
    file_type: str | None = None
    version: str = "1.0"
    is_public: bool = False
    access_level: str = "team"
    tags: list[str] = Field(default_factory=list)


class DocumentResponse(DocumentBase):
    """Réponse document."""
    id: UUID
    project_id: UUID
    file_name: str | None = None
    file_url: str | None = None
    file_size: int | None = None
    file_type: str | None = None
    version: str = "1.0"
    is_latest: bool = True
    is_public: bool = False
    access_level: str = "team"
    uploaded_by: UUID | None = None
    created_at: datetime
    tags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS BUDGET
# ============================================================================

class BudgetLineCreate(BaseModel):
    """Création d'une ligne de budget."""
    code: str | None = None
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None
    budget_amount: Decimal = Decimal("0")
    phase_id: UUID | None = None
    quantity: float | None = None
    unit: str | None = None
    unit_price: Decimal | None = None
    order: int = 0
    parent_line_id: UUID | None = None
    account_code: str | None = None


class BudgetBase(BaseModel):
    """Base pour les budgets."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    fiscal_year: str | None = None
    budget_type: BudgetType = BudgetType.MIXED


class BudgetCreate(BudgetBase):
    """Création d'un budget."""
    total_budget: Decimal = Decimal("0")
    currency: str = "EUR"
    start_date: date | None = None
    end_date: date | None = None
    lines: list[BudgetLineCreate] = Field(default_factory=list)


class BudgetUpdate(BaseModel):
    """Mise à jour d'un budget."""
    name: str | None = None
    description: str | None = None
    total_budget: Decimal | None = None
    total_forecast: Decimal | None = None
    is_locked: bool | None = None


class BudgetLineResponse(BaseModel):
    """Réponse ligne de budget."""
    id: UUID
    budget_id: UUID
    phase_id: UUID | None = None
    code: str | None = None
    name: str
    description: str | None = None
    category: str | None = None
    budget_amount: Decimal = Decimal("0")
    committed_amount: Decimal = Decimal("0")
    actual_amount: Decimal = Decimal("0")
    forecast_amount: Decimal = Decimal("0")
    quantity: float | None = None
    unit: str | None = None
    unit_price: Decimal | None = None
    order: int = 0
    parent_line_id: UUID | None = None
    account_code: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BudgetResponse(BudgetBase):
    """Réponse budget."""
    id: UUID
    project_id: UUID
    version: str = "1.0"
    total_budget: Decimal = Decimal("0")
    total_committed: Decimal = Decimal("0")
    total_actual: Decimal = Decimal("0")
    total_forecast: Decimal = Decimal("0")
    currency: str = "EUR"
    is_approved: bool = False
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    is_active: bool = True
    is_locked: bool = False
    start_date: date | None = None
    end_date: date | None = None
    lines: list[BudgetLineResponse] = Field(default_factory=list)
    created_by: UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS TEMPLATE
# ============================================================================

class TemplateBase(BaseModel):
    """Base pour les templates."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None


class TemplateCreate(TemplateBase):
    """Création d'un template."""
    default_priority: ProjectPriority = ProjectPriority.MEDIUM
    default_budget_type: BudgetType | None = None
    estimated_duration_days: int | None = None
    phases_template: list[dict] = Field(default_factory=list)
    tasks_template: list[dict] = Field(default_factory=list)
    milestones_template: list[dict] = Field(default_factory=list)
    risks_template: list[dict] = Field(default_factory=list)
    roles_template: list[dict] = Field(default_factory=list)
    budget_template: list[dict] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)
    settings: dict = Field(default_factory=dict)
    is_public: bool = False


class TemplateResponse(TemplateBase):
    """Réponse template."""
    id: UUID
    default_priority: ProjectPriority = ProjectPriority.MEDIUM
    default_budget_type: BudgetType | None = None
    estimated_duration_days: int | None = None
    phases_template: list[dict] = Field(default_factory=list)
    tasks_template: list[dict] = Field(default_factory=list)
    milestones_template: list[dict] = Field(default_factory=list)
    risks_template: list[dict] = Field(default_factory=list)
    roles_template: list[dict] = Field(default_factory=list)
    budget_template: list[dict] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)
    settings: dict = Field(default_factory=dict)
    is_active: bool = True
    is_public: bool = False
    created_by: UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS COMMENTAIRE
# ============================================================================

class CommentBase(BaseModel):
    """Base pour les commentaires."""
    content: str = Field(..., min_length=1)
    comment_type: str = "comment"


class CommentCreate(CommentBase):
    """Création d'un commentaire."""
    task_id: UUID | None = None
    parent_comment_id: UUID | None = None
    mentions: list[UUID] = Field(default_factory=list)
    attachments: list[str] = Field(default_factory=list)
    is_internal: bool = True


class CommentResponse(CommentBase):
    """Réponse commentaire."""
    id: UUID
    project_id: UUID
    task_id: UUID | None = None
    parent_comment_id: UUID | None = None
    mentions: list[UUID] = Field(default_factory=list)
    attachments: list[str] = Field(default_factory=list)
    is_internal: bool = True
    author_id: UUID
    created_at: datetime
    updated_at: datetime
    is_edited: bool = False

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS DASHBOARD ET KPI
# ============================================================================

class ProjectStats(BaseModel):
    """Statistiques projet."""
    tasks_total: int = 0
    tasks_completed: int = 0
    tasks_in_progress: int = 0
    tasks_blocked: int = 0
    tasks_overdue: int = 0
    milestones_total: int = 0
    milestones_achieved: int = 0
    milestones_overdue: int = 0
    risks_total: int = 0
    risks_open: int = 0
    risks_high: int = 0
    issues_total: int = 0
    issues_open: int = 0
    issues_critical: int = 0
    team_size: int = 0
    hours_planned: float = 0
    hours_actual: float = 0
    hours_remaining: float = 0
    budget_planned: Decimal = Decimal("0")
    budget_actual: Decimal = Decimal("0")
    budget_remaining: Decimal = Decimal("0")


class BurndownData(BaseModel):
    """Données de burndown chart."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    chart_date: date = Field(..., alias="date")
    planned_remaining: float
    actual_remaining: float
    completed: float


class ProjectDashboard(BaseModel):
    """Dashboard projet."""
    project: ProjectResponse
    stats: ProjectStats
    recent_tasks: list[TaskResponse] = Field(default_factory=list)
    upcoming_milestones: list[MilestoneResponse] = Field(default_factory=list)
    high_risks: list[RiskResponse] = Field(default_factory=list)
    open_issues: list[IssueResponse] = Field(default_factory=list)
    burndown: list[BurndownData] = Field(default_factory=list)
    health_indicators: dict = Field(default_factory=dict)
