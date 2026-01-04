"""
AZALS MODULE M9 - Schémas Projets
=================================

Schémas Pydantic pour la gestion de projets.
"""

from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID
import json

from .models import (
    ProjectStatus, ProjectPriority, TaskStatus, TaskPriority,
    MilestoneStatus, RiskStatus, RiskImpact, RiskProbability,
    IssueStatus, IssuePriority, TeamMemberRole, TimeEntryStatus,
    ExpenseStatus, BudgetType
)


# ============================================================================
# SCHÉMAS PROJET
# ============================================================================

class ProjectBase(BaseModel):
    """Base pour les projets."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    @field_validator('tags', mode='before')
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else []
        return v or []


class ProjectCreate(ProjectBase):
    """Création d'un projet."""
    priority: ProjectPriority = ProjectPriority.MEDIUM
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    project_manager_id: Optional[UUID] = None
    sponsor_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    budget_type: Optional[BudgetType] = None
    planned_budget: Decimal = Decimal("0")
    currency: str = "EUR"
    planned_hours: float = 0
    is_billable: bool = False
    billing_rate: Optional[Decimal] = None
    parent_project_id: Optional[UUID] = None
    template_id: Optional[UUID] = None
    settings: dict = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    """Mise à jour d'un projet."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[ProjectStatus] = None
    priority: Optional[ProjectPriority] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    project_manager_id: Optional[UUID] = None
    sponsor_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    planned_budget: Optional[Decimal] = None
    planned_hours: Optional[float] = None
    progress_percent: Optional[float] = None
    health_status: Optional[str] = None
    is_billable: Optional[bool] = None
    billing_rate: Optional[Decimal] = None
    settings: Optional[dict] = None
    is_active: Optional[bool] = None


class ProjectResponse(ProjectBase):
    """Réponse projet."""
    id: UUID
    status: ProjectStatus = ProjectStatus.DRAFT
    priority: ProjectPriority = ProjectPriority.MEDIUM
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    project_manager_id: Optional[UUID] = None
    sponsor_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    budget_type: Optional[BudgetType] = None
    planned_budget: Decimal = Decimal("0")
    actual_cost: Decimal = Decimal("0")
    currency: str = "EUR"
    planned_hours: float = 0
    actual_hours: float = 0
    progress_percent: float = 0
    health_status: Optional[str] = None
    parent_project_id: Optional[UUID] = None
    is_billable: bool = False
    billing_rate: Optional[Decimal] = None
    is_active: bool = True
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectList(BaseModel):
    """Liste de projets."""
    items: List[ProjectResponse]
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
    health_status: Optional[str] = None
    planned_end_date: Optional[date] = None
    tasks_total: int = 0
    tasks_completed: int = 0
    team_size: int = 0


# ============================================================================
# SCHÉMAS PHASE
# ============================================================================

class PhaseBase(BaseModel):
    """Base pour les phases."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    order: int = 0
    color: Optional[str] = None


class PhaseCreate(PhaseBase):
    """Création d'une phase."""
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    planned_hours: float = 0
    planned_budget: Decimal = Decimal("0")


class PhaseUpdate(BaseModel):
    """Mise à jour d'une phase."""
    name: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    color: Optional[str] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    status: Optional[TaskStatus] = None
    progress_percent: Optional[float] = None


class PhaseResponse(PhaseBase):
    """Réponse phase."""
    id: UUID
    project_id: UUID
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
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
    description: Optional[str] = None
    task_type: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    @field_validator('tags', mode='before')
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else []
        return v or []


class TaskCreate(TaskBase):
    """Création d'une tâche."""
    phase_id: Optional[UUID] = None
    parent_task_id: Optional[UUID] = None
    code: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    due_date: Optional[date] = None
    assignee_id: Optional[UUID] = None
    estimated_hours: float = 0
    order: int = 0
    wbs_code: Optional[str] = None
    is_milestone: bool = False
    is_critical: bool = False
    is_billable: bool = True
    dependencies: List[TaskDependencyCreate] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """Mise à jour d'une tâche."""
    name: Optional[str] = None
    description: Optional[str] = None
    phase_id: Optional[UUID] = None
    parent_task_id: Optional[UUID] = None
    task_type: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    due_date: Optional[date] = None
    assignee_id: Optional[UUID] = None
    estimated_hours: Optional[float] = None
    remaining_hours: Optional[float] = None
    progress_percent: Optional[float] = None
    order: Optional[int] = None
    is_critical: Optional[bool] = None
    is_billable: Optional[bool] = None


class TaskResponse(TaskBase):
    """Réponse tâche."""
    id: UUID
    project_id: UUID
    phase_id: Optional[UUID] = None
    parent_task_id: Optional[UUID] = None
    code: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    due_date: Optional[date] = None
    assignee_id: Optional[UUID] = None
    reporter_id: Optional[UUID] = None
    estimated_hours: float = 0
    actual_hours: float = 0
    remaining_hours: float = 0
    progress_percent: float = 0
    order: int = 0
    wbs_code: Optional[str] = None
    is_milestone: bool = False
    is_critical: bool = False
    is_billable: bool = True
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TaskList(BaseModel):
    """Liste de tâches."""
    items: List[TaskResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ============================================================================
# SCHÉMAS JALON
# ============================================================================

class MilestoneBase(BaseModel):
    """Base pour les jalons."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_date: date
    is_key_milestone: bool = False
    is_customer_visible: bool = True


class MilestoneCreate(MilestoneBase):
    """Création d'un jalon."""
    phase_id: Optional[UUID] = None
    deliverables: List[str] = Field(default_factory=list)
    acceptance_criteria: Optional[str] = None


class MilestoneUpdate(BaseModel):
    """Mise à jour d'un jalon."""
    name: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[date] = None
    actual_date: Optional[date] = None
    status: Optional[MilestoneStatus] = None
    is_key_milestone: Optional[bool] = None
    is_customer_visible: Optional[bool] = None
    deliverables: Optional[List[str]] = None
    acceptance_criteria: Optional[str] = None
    validation_notes: Optional[str] = None


class MilestoneResponse(MilestoneBase):
    """Réponse jalon."""
    id: UUID
    project_id: UUID
    phase_id: Optional[UUID] = None
    status: MilestoneStatus = MilestoneStatus.PENDING
    actual_date: Optional[date] = None
    deliverables: List[str] = Field(default_factory=list)
    acceptance_criteria: Optional[str] = None
    validated_by: Optional[UUID] = None
    validated_at: Optional[datetime] = None
    validation_notes: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS ÉQUIPE
# ============================================================================

class TeamMemberBase(BaseModel):
    """Base pour les membres d'équipe."""
    user_id: UUID
    role: TeamMemberRole = TeamMemberRole.MEMBER
    role_description: Optional[str] = None


class TeamMemberCreate(TeamMemberBase):
    """Ajout d'un membre."""
    employee_id: Optional[UUID] = None
    allocation_percent: float = 100
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    hourly_rate: Optional[Decimal] = None
    daily_rate: Optional[Decimal] = None
    is_billable: bool = True
    can_log_time: bool = True
    can_view_budget: bool = False
    can_manage_tasks: bool = False
    can_approve_time: bool = False


class TeamMemberUpdate(BaseModel):
    """Mise à jour d'un membre."""
    role: Optional[TeamMemberRole] = None
    role_description: Optional[str] = None
    allocation_percent: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    hourly_rate: Optional[Decimal] = None
    daily_rate: Optional[Decimal] = None
    is_billable: Optional[bool] = None
    can_log_time: Optional[bool] = None
    can_view_budget: Optional[bool] = None
    can_manage_tasks: Optional[bool] = None
    can_approve_time: Optional[bool] = None
    is_active: Optional[bool] = None


class TeamMemberResponse(TeamMemberBase):
    """Réponse membre."""
    id: UUID
    project_id: UUID
    employee_id: Optional[UUID] = None
    allocation_percent: float = 100
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    hourly_rate: Optional[Decimal] = None
    daily_rate: Optional[Decimal] = None
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
    description: Optional[str] = None
    category: Optional[str] = None
    probability: RiskProbability
    impact: RiskImpact


class RiskCreate(RiskBase):
    """Création d'un risque."""
    code: Optional[str] = None
    owner_id: Optional[UUID] = None
    response_strategy: Optional[str] = None
    mitigation_plan: Optional[str] = None
    contingency_plan: Optional[str] = None
    triggers: List[str] = Field(default_factory=list)
    estimated_impact_min: Optional[Decimal] = None
    estimated_impact_max: Optional[Decimal] = None
    review_date: Optional[date] = None


class RiskUpdate(BaseModel):
    """Mise à jour d'un risque."""
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[RiskStatus] = None
    probability: Optional[RiskProbability] = None
    impact: Optional[RiskImpact] = None
    owner_id: Optional[UUID] = None
    response_strategy: Optional[str] = None
    mitigation_plan: Optional[str] = None
    contingency_plan: Optional[str] = None
    triggers: Optional[List[str]] = None
    monitoring_notes: Optional[str] = None
    review_date: Optional[date] = None


class RiskResponse(RiskBase):
    """Réponse risque."""
    id: UUID
    project_id: UUID
    code: Optional[str] = None
    status: RiskStatus = RiskStatus.IDENTIFIED
    risk_score: Optional[float] = None
    estimated_impact_min: Optional[Decimal] = None
    estimated_impact_max: Optional[Decimal] = None
    identified_date: date
    review_date: Optional[date] = None
    occurred_date: Optional[date] = None
    closed_date: Optional[date] = None
    owner_id: Optional[UUID] = None
    response_strategy: Optional[str] = None
    mitigation_plan: Optional[str] = None
    contingency_plan: Optional[str] = None
    triggers: List[str] = Field(default_factory=list)
    monitoring_notes: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskList(BaseModel):
    """Liste de risques."""
    items: List[RiskResponse]
    total: int


# ============================================================================
# SCHÉMAS ISSUE
# ============================================================================

class IssueBase(BaseModel):
    """Base pour les issues."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    priority: IssuePriority = IssuePriority.MEDIUM


class IssueCreate(IssueBase):
    """Création d'une issue."""
    task_id: Optional[UUID] = None
    code: Optional[str] = None
    assignee_id: Optional[UUID] = None
    due_date: Optional[date] = None
    impact_description: Optional[str] = None
    affected_areas: List[str] = Field(default_factory=list)
    related_risk_id: Optional[UUID] = None


class IssueUpdate(BaseModel):
    """Mise à jour d'une issue."""
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[IssueStatus] = None
    priority: Optional[IssuePriority] = None
    assignee_id: Optional[UUID] = None
    due_date: Optional[date] = None
    impact_description: Optional[str] = None
    affected_areas: Optional[List[str]] = None
    resolution: Optional[str] = None
    resolution_type: Optional[str] = None


class IssueResponse(IssueBase):
    """Réponse issue."""
    id: UUID
    project_id: UUID
    task_id: Optional[UUID] = None
    code: Optional[str] = None
    status: IssueStatus = IssueStatus.OPEN
    reporter_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None
    reported_date: date
    due_date: Optional[date] = None
    resolved_date: Optional[date] = None
    closed_date: Optional[date] = None
    impact_description: Optional[str] = None
    affected_areas: List[str] = Field(default_factory=list)
    resolution: Optional[str] = None
    resolution_type: Optional[str] = None
    is_escalated: bool = False
    related_risk_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IssueList(BaseModel):
    """Liste d'issues."""
    items: List[IssueResponse]
    total: int


# ============================================================================
# SCHÉMAS TIME ENTRY
# ============================================================================

class TimeEntryBase(BaseModel):
    """Base pour les saisies de temps."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    entry_date: date = Field(..., alias="date")
    hours: float = Field(..., gt=0)
    description: Optional[str] = None
    activity_type: Optional[str] = None


class TimeEntryCreate(TimeEntryBase):
    """Création d'une saisie."""
    task_id: Optional[UUID] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_billable: bool = True
    is_overtime: bool = False


class TimeEntryUpdate(BaseModel):
    """Mise à jour d'une saisie."""
    date: Optional[date] = None
    hours: Optional[float] = None
    description: Optional[str] = None
    activity_type: Optional[str] = None
    task_id: Optional[UUID] = None
    is_billable: Optional[bool] = None
    is_overtime: Optional[bool] = None


class TimeEntryResponse(TimeEntryBase):
    """Réponse saisie."""
    id: UUID
    project_id: UUID
    task_id: Optional[UUID] = None
    user_id: UUID
    employee_id: Optional[UUID] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: TimeEntryStatus = TimeEntryStatus.DRAFT
    is_billable: bool = True
    billing_rate: Optional[Decimal] = None
    billing_amount: Optional[Decimal] = None
    is_invoiced: bool = False
    is_overtime: bool = False
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TimeEntryList(BaseModel):
    """Liste de saisies."""
    items: List[TimeEntryResponse]
    total: int
    total_hours: float = 0
    billable_hours: float = 0


# ============================================================================
# SCHÉMAS EXPENSE
# ============================================================================

class ExpenseBase(BaseModel):
    """Base pour les dépenses."""
    description: str = Field(..., min_length=1)
    category: Optional[str] = None
    amount: Decimal = Field(..., gt=0)
    expense_date: date


class ExpenseCreate(ExpenseBase):
    """Création d'une dépense."""
    task_id: Optional[UUID] = None
    budget_line_id: Optional[UUID] = None
    reference: Optional[str] = None
    currency: str = "EUR"
    quantity: float = 1
    unit_price: Optional[Decimal] = None
    vendor: Optional[str] = None
    is_billable: bool = True
    receipt_url: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)


class ExpenseUpdate(BaseModel):
    """Mise à jour d'une dépense."""
    description: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[Decimal] = None
    expense_date: Optional[date] = None
    vendor: Optional[str] = None
    is_billable: Optional[bool] = None
    receipt_url: Optional[str] = None


class ExpenseResponse(ExpenseBase):
    """Réponse dépense."""
    id: UUID
    project_id: UUID
    task_id: Optional[UUID] = None
    budget_line_id: Optional[UUID] = None
    reference: Optional[str] = None
    currency: str = "EUR"
    quantity: float = 1
    unit_price: Optional[Decimal] = None
    due_date: Optional[date] = None
    paid_date: Optional[date] = None
    status: ExpenseStatus = ExpenseStatus.DRAFT
    submitted_by: Optional[UUID] = None
    vendor: Optional[str] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    is_billable: bool = True
    is_invoiced: bool = False
    receipt_url: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS DOCUMENT
# ============================================================================

class DocumentBase(BaseModel):
    """Base pour les documents."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Création d'un document."""
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    version: str = "1.0"
    is_public: bool = False
    access_level: str = "team"
    tags: List[str] = Field(default_factory=list)


class DocumentResponse(DocumentBase):
    """Réponse document."""
    id: UUID
    project_id: UUID
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    version: str = "1.0"
    is_latest: bool = True
    is_public: bool = False
    access_level: str = "team"
    uploaded_by: Optional[UUID] = None
    created_at: datetime
    tags: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS BUDGET
# ============================================================================

class BudgetLineCreate(BaseModel):
    """Création d'une ligne de budget."""
    code: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    budget_amount: Decimal = Decimal("0")
    phase_id: Optional[UUID] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    order: int = 0
    parent_line_id: Optional[UUID] = None
    account_code: Optional[str] = None


class BudgetBase(BaseModel):
    """Base pour les budgets."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    fiscal_year: Optional[str] = None
    budget_type: BudgetType = BudgetType.MIXED


class BudgetCreate(BudgetBase):
    """Création d'un budget."""
    total_budget: Decimal = Decimal("0")
    currency: str = "EUR"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    lines: List[BudgetLineCreate] = Field(default_factory=list)


class BudgetUpdate(BaseModel):
    """Mise à jour d'un budget."""
    name: Optional[str] = None
    description: Optional[str] = None
    total_budget: Optional[Decimal] = None
    total_forecast: Optional[Decimal] = None
    is_locked: Optional[bool] = None


class BudgetLineResponse(BaseModel):
    """Réponse ligne de budget."""
    id: UUID
    budget_id: UUID
    phase_id: Optional[UUID] = None
    code: Optional[str] = None
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    budget_amount: Decimal = Decimal("0")
    committed_amount: Decimal = Decimal("0")
    actual_amount: Decimal = Decimal("0")
    forecast_amount: Decimal = Decimal("0")
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    order: int = 0
    parent_line_id: Optional[UUID] = None
    account_code: Optional[str] = None
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
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    is_active: bool = True
    is_locked: bool = False
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    lines: List[BudgetLineResponse] = Field(default_factory=list)
    created_by: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS TEMPLATE
# ============================================================================

class TemplateBase(BaseModel):
    """Base pour les templates."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None


class TemplateCreate(TemplateBase):
    """Création d'un template."""
    default_priority: ProjectPriority = ProjectPriority.MEDIUM
    default_budget_type: Optional[BudgetType] = None
    estimated_duration_days: Optional[int] = None
    phases_template: List[dict] = Field(default_factory=list)
    tasks_template: List[dict] = Field(default_factory=list)
    milestones_template: List[dict] = Field(default_factory=list)
    risks_template: List[dict] = Field(default_factory=list)
    roles_template: List[dict] = Field(default_factory=list)
    budget_template: List[dict] = Field(default_factory=list)
    checklist: List[str] = Field(default_factory=list)
    settings: dict = Field(default_factory=dict)
    is_public: bool = False


class TemplateResponse(TemplateBase):
    """Réponse template."""
    id: UUID
    default_priority: ProjectPriority = ProjectPriority.MEDIUM
    default_budget_type: Optional[BudgetType] = None
    estimated_duration_days: Optional[int] = None
    phases_template: List[dict] = Field(default_factory=list)
    tasks_template: List[dict] = Field(default_factory=list)
    milestones_template: List[dict] = Field(default_factory=list)
    risks_template: List[dict] = Field(default_factory=list)
    roles_template: List[dict] = Field(default_factory=list)
    budget_template: List[dict] = Field(default_factory=list)
    checklist: List[str] = Field(default_factory=list)
    settings: dict = Field(default_factory=dict)
    is_active: bool = True
    is_public: bool = False
    created_by: Optional[UUID] = None
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
    task_id: Optional[UUID] = None
    parent_comment_id: Optional[UUID] = None
    mentions: List[UUID] = Field(default_factory=list)
    attachments: List[str] = Field(default_factory=list)
    is_internal: bool = True


class CommentResponse(CommentBase):
    """Réponse commentaire."""
    id: UUID
    project_id: UUID
    task_id: Optional[UUID] = None
    parent_comment_id: Optional[UUID] = None
    mentions: List[UUID] = Field(default_factory=list)
    attachments: List[str] = Field(default_factory=list)
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
    recent_tasks: List[TaskResponse] = Field(default_factory=list)
    upcoming_milestones: List[MilestoneResponse] = Field(default_factory=list)
    high_risks: List[RiskResponse] = Field(default_factory=list)
    open_issues: List[IssueResponse] = Field(default_factory=list)
    burndown: List[BurndownData] = Field(default_factory=list)
    health_indicators: dict = Field(default_factory=dict)
