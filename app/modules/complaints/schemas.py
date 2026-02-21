"""
AZALS MODULE - Complaints Schemas
==================================

Schemas Pydantic pour le systeme de gestion des reclamations clients.
Validation des entrees/sorties API conforme OpenAPI 3.0.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .models import (
    ActionType,
    ComplaintCategory,
    ComplaintChannel,
    ComplaintPriority,
    ComplaintStatus,
    EscalationLevel,
    ResolutionType,
    RootCauseCategory,
    SatisfactionRating,
)


# ============================================================================
# BASE SCHEMAS
# ============================================================================

class TenantMixin(BaseModel):
    """Mixin pour tenant_id en reponse."""
    tenant_id: str


class AuditMixin(BaseModel):
    """Mixin pour champs d'audit."""
    created_at: datetime
    updated_at: datetime | None = None
    version: int = 1


class SoftDeleteMixin(BaseModel):
    """Mixin pour soft delete."""
    is_deleted: bool = False
    deleted_at: datetime | None = None


# ============================================================================
# CATEGORY CONFIG SCHEMAS
# ============================================================================

class CategoryConfigBase(BaseModel):
    """Base categorie de reclamation."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: str | None = None
    icon: str | None = Field(None, max_length=50)
    parent_id: UUID | None = None
    default_priority: ComplaintPriority = ComplaintPriority.MEDIUM
    default_team_id: UUID | None = None
    sla_policy_id: UUID | None = None
    require_order: bool = False
    require_product: bool = False
    require_invoice: bool = False
    auto_assign: bool = True
    is_public: bool = True
    sort_order: int = 0


class CategoryConfigCreate(CategoryConfigBase):
    """Creation categorie."""
    pass


class CategoryConfigUpdate(BaseModel):
    """Mise a jour categorie."""
    code: str | None = Field(None, max_length=50)
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    icon: str | None = None
    parent_id: UUID | None = None
    default_priority: ComplaintPriority | None = None
    default_team_id: UUID | None = None
    sla_policy_id: UUID | None = None
    require_order: bool | None = None
    require_product: bool | None = None
    require_invoice: bool | None = None
    auto_assign: bool | None = None
    is_public: bool | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class CategoryConfigResponse(CategoryConfigBase, TenantMixin, AuditMixin):
    """Reponse categorie."""
    id: UUID
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TEAM SCHEMAS
# ============================================================================

class TeamBase(BaseModel):
    """Base equipe."""
    name: str = Field(..., max_length=100)
    description: str | None = None
    email: EmailStr | None = None
    manager_id: UUID | None = None
    default_sla_policy_id: UUID | None = None
    auto_assign_method: str = Field(default="round_robin", max_length=30)
    max_complaints_per_agent: int = Field(default=25, ge=1, le=100)
    working_hours: dict[str, Any] | None = None
    timezone: str = Field(default="Europe/Paris", max_length=50)


class TeamCreate(TeamBase):
    """Creation equipe."""
    pass


class TeamUpdate(BaseModel):
    """Mise a jour equipe."""
    name: str | None = Field(None, max_length=100)
    description: str | None = None
    email: EmailStr | None = None
    manager_id: UUID | None = None
    default_sla_policy_id: UUID | None = None
    auto_assign_method: str | None = None
    max_complaints_per_agent: int | None = Field(None, ge=1, le=100)
    working_hours: dict[str, Any] | None = None
    timezone: str | None = None
    is_active: bool | None = None


class TeamResponse(TeamBase, TenantMixin, AuditMixin):
    """Reponse equipe."""
    id: UUID
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TeamWithStats(TeamResponse):
    """Equipe avec statistiques."""
    member_count: int = 0
    open_complaints: int = 0
    avg_resolution_hours: float = 0.0


# ============================================================================
# AGENT SCHEMAS
# ============================================================================

class AgentBase(BaseModel):
    """Base agent."""
    user_id: UUID
    team_id: UUID | None = None
    display_name: str = Field(..., max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    avatar_url: str | None = Field(None, max_length=500)
    signature: str | None = None
    skills: list[str] | None = None
    categories: list[str] | None = None
    languages: list[str] | None = Field(default=["fr"])
    max_escalation_level: EscalationLevel = EscalationLevel.LEVEL_2
    can_assign: bool = True
    can_escalate: bool = True
    can_resolve: bool = True
    can_close: bool = False
    can_approve_compensation: bool = False
    max_compensation_amount: Decimal = Field(default=Decimal("0"), ge=0)
    can_view_all: bool = False
    is_supervisor: bool = False


class AgentCreate(AgentBase):
    """Creation agent."""
    pass


class AgentUpdate(BaseModel):
    """Mise a jour agent."""
    team_id: UUID | None = None
    display_name: str | None = Field(None, max_length=255)
    email: EmailStr | None = None
    phone: str | None = None
    avatar_url: str | None = None
    signature: str | None = None
    skills: list[str] | None = None
    categories: list[str] | None = None
    languages: list[str] | None = None
    max_escalation_level: EscalationLevel | None = None
    can_assign: bool | None = None
    can_escalate: bool | None = None
    can_resolve: bool | None = None
    can_close: bool | None = None
    can_approve_compensation: bool | None = None
    max_compensation_amount: Decimal | None = None
    can_view_all: bool | None = None
    is_supervisor: bool | None = None
    is_available: bool | None = None
    is_active: bool | None = None


class AgentResponse(AgentBase, TenantMixin, AuditMixin):
    """Reponse agent."""
    id: UUID
    is_available: bool
    current_load: int
    last_assigned_at: datetime | None = None
    complaints_assigned: int
    complaints_resolved: int
    avg_resolution_hours: Decimal
    satisfaction_score: Decimal
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AgentAvailabilityUpdate(BaseModel):
    """Mise a jour disponibilite agent."""
    is_available: bool


# ============================================================================
# SLA POLICY SCHEMAS
# ============================================================================

class SLAPolicyBase(BaseModel):
    """Base politique SLA."""
    name: str = Field(..., max_length=100)
    description: str | None = None
    ack_hours_low: int = Field(default=48, ge=1)
    ack_hours_medium: int = Field(default=24, ge=1)
    ack_hours_high: int = Field(default=4, ge=1)
    ack_hours_urgent: int = Field(default=2, ge=1)
    ack_hours_critical: int = Field(default=1, ge=1)
    resolution_hours_low: int = Field(default=240, ge=1)
    resolution_hours_medium: int = Field(default=120, ge=1)
    resolution_hours_high: int = Field(default=48, ge=1)
    resolution_hours_urgent: int = Field(default=24, ge=1)
    resolution_hours_critical: int = Field(default=8, ge=1)
    escalation_hours_low: int = Field(default=168, ge=1)
    escalation_hours_medium: int = Field(default=72, ge=1)
    escalation_hours_high: int = Field(default=24, ge=1)
    escalation_hours_urgent: int = Field(default=8, ge=1)
    escalation_hours_critical: int = Field(default=2, ge=1)
    business_hours_only: bool = True
    working_hours: dict[str, Any] | None = None
    timezone: str = Field(default="Europe/Paris", max_length=50)
    holidays: list[str] | None = None
    auto_escalation_enabled: bool = True
    escalation_rules: list[dict[str, Any]] | None = None
    notify_on_breach: bool = True
    notify_before_breach_hours: int = Field(default=4, ge=1)
    is_default: bool = False


class SLAPolicyCreate(SLAPolicyBase):
    """Creation SLA."""
    pass


class SLAPolicyUpdate(BaseModel):
    """Mise a jour SLA."""
    name: str | None = Field(None, max_length=100)
    description: str | None = None
    ack_hours_low: int | None = None
    ack_hours_medium: int | None = None
    ack_hours_high: int | None = None
    ack_hours_urgent: int | None = None
    ack_hours_critical: int | None = None
    resolution_hours_low: int | None = None
    resolution_hours_medium: int | None = None
    resolution_hours_high: int | None = None
    resolution_hours_urgent: int | None = None
    resolution_hours_critical: int | None = None
    escalation_hours_low: int | None = None
    escalation_hours_medium: int | None = None
    escalation_hours_high: int | None = None
    escalation_hours_urgent: int | None = None
    escalation_hours_critical: int | None = None
    business_hours_only: bool | None = None
    working_hours: dict[str, Any] | None = None
    timezone: str | None = None
    holidays: list[str] | None = None
    auto_escalation_enabled: bool | None = None
    escalation_rules: list[dict[str, Any]] | None = None
    notify_on_breach: bool | None = None
    notify_before_breach_hours: int | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class SLAPolicyResponse(SLAPolicyBase, TenantMixin, AuditMixin):
    """Reponse SLA."""
    id: UUID
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# COMPLAINT SCHEMAS
# ============================================================================

class ComplaintBase(BaseModel):
    """Base reclamation."""
    subject: str = Field(..., max_length=500, min_length=5)
    description: str = Field(..., min_length=10)
    category: ComplaintCategory = ComplaintCategory.OTHER
    category_config_id: UUID | None = None
    priority: ComplaintPriority = ComplaintPriority.MEDIUM
    channel: ComplaintChannel = ComplaintChannel.EMAIL

    # Client
    customer_id: UUID | None = None
    customer_name: str | None = Field(None, max_length=255)
    customer_email: EmailStr | None = None
    customer_phone: str | None = Field(None, max_length=50)
    customer_company: str | None = Field(None, max_length=255)
    customer_account_number: str | None = Field(None, max_length=50)

    # References
    order_id: UUID | None = None
    order_reference: str | None = Field(None, max_length=100)
    invoice_id: UUID | None = None
    invoice_reference: str | None = Field(None, max_length=100)
    product_id: UUID | None = None
    product_reference: str | None = Field(None, max_length=100)
    product_name: str | None = Field(None, max_length=255)
    contract_id: UUID | None = None

    # Montant
    disputed_amount: Decimal | None = Field(None, ge=0)
    currency: str = Field(default="EUR", max_length=3)

    # Tags
    tags: list[str] | None = None
    custom_fields: dict[str, Any] | None = None


class ComplaintCreate(ComplaintBase):
    """Creation reclamation."""
    team_id: UUID | None = None
    assigned_to_id: UUID | None = None
    sla_policy_id: UUID | None = None
    original_message_id: str | None = None
    source_system: str | None = None

    @field_validator("customer_email", "customer_name", mode="before")
    @classmethod
    def require_customer_info(cls, v, info):
        """Au moins email ou nom client requis."""
        return v


class ComplaintUpdate(BaseModel):
    """Mise a jour reclamation."""
    subject: str | None = Field(None, max_length=500)
    description: str | None = None
    category: ComplaintCategory | None = None
    category_config_id: UUID | None = None
    priority: ComplaintPriority | None = None
    status: ComplaintStatus | None = None

    customer_name: str | None = None
    customer_email: EmailStr | None = None
    customer_phone: str | None = None
    customer_company: str | None = None

    order_id: UUID | None = None
    order_reference: str | None = None
    invoice_id: UUID | None = None
    invoice_reference: str | None = None
    product_id: UUID | None = None
    product_reference: str | None = None
    product_name: str | None = None

    disputed_amount: Decimal | None = None
    tags: list[str] | None = None
    custom_fields: dict[str, Any] | None = None


class ComplaintAssign(BaseModel):
    """Assignation reclamation."""
    agent_id: UUID
    team_id: UUID | None = None
    note: str | None = None


class ComplaintStatusChange(BaseModel):
    """Changement de statut."""
    status: ComplaintStatus
    comment: str | None = None


class ComplaintResolve(BaseModel):
    """Resolution reclamation."""
    resolution_type: ResolutionType
    resolution_summary: str = Field(..., min_length=10)
    compensation_amount: Decimal | None = Field(None, ge=0)
    compensation_type: str | None = Field(None, max_length=50)
    root_cause_category: RootCauseCategory | None = None
    root_cause_description: str | None = None
    requires_approval: bool = False


class ComplaintEscalate(BaseModel):
    """Escalade reclamation."""
    to_level: EscalationLevel
    reason: str = Field(..., min_length=10)
    assign_to_id: UUID | None = None


class ComplaintClose(BaseModel):
    """Cloture reclamation."""
    root_cause_category: RootCauseCategory | None = None
    root_cause_description: str | None = None
    final_notes: str | None = None


class ComplaintReopen(BaseModel):
    """Reouverture reclamation."""
    reason: str = Field(..., min_length=10)


class ComplaintResponse(ComplaintBase, TenantMixin):
    """Reponse reclamation."""
    id: UUID
    reference: str
    status: ComplaintStatus
    is_vip_customer: bool

    # Assignation
    team_id: UUID | None = None
    assigned_to_id: UUID | None = None
    assigned_at: datetime | None = None

    # SLA
    sla_policy_id: UUID | None = None
    acknowledgment_due: datetime | None = None
    acknowledged_at: datetime | None = None
    acknowledgment_breached: bool
    resolution_due: datetime | None = None
    resolved_at: datetime | None = None
    resolution_breached: bool
    escalation_due: datetime | None = None

    # Escalade
    current_escalation_level: EscalationLevel
    escalated_at: datetime | None = None
    escalation_count: int

    # Resolution
    resolution_type: ResolutionType | None = None
    resolution_summary: str | None = None
    compensation_amount: Decimal | None = None
    compensation_type: str | None = None

    # Analyse
    root_cause_category: RootCauseCategory | None = None
    root_cause_description: str | None = None
    sentiment: str | None = None

    # Satisfaction
    satisfaction_rating: SatisfactionRating | None = None
    satisfaction_comment: str | None = None
    nps_score: int | None = None

    # Compteurs
    exchange_count: int
    internal_note_count: int
    attachment_count: int

    # Dates
    closed_at: datetime | None = None
    reopened_at: datetime | None = None
    reopen_count: int

    # Audit
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    version: int

    model_config = ConfigDict(from_attributes=True)


class ComplaintDetail(ComplaintResponse):
    """Detail reclamation avec relations."""
    category_config: CategoryConfigResponse | None = None
    team: TeamResponse | None = None
    assigned_agent: AgentResponse | None = None
    exchanges: list["ExchangeResponse"] = []
    attachments: list["AttachmentResponse"] = []
    actions: list["ActionResponse"] = []
    escalations: list["EscalationResponse"] = []


class ComplaintSummary(BaseModel):
    """Resume reclamation pour listes."""
    id: UUID
    reference: str
    subject: str
    category: ComplaintCategory
    priority: ComplaintPriority
    status: ComplaintStatus
    customer_name: str | None = None
    customer_email: str | None = None
    assigned_to_id: UUID | None = None
    resolution_due: datetime | None = None
    resolution_breached: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# EXCHANGE SCHEMAS
# ============================================================================

class ExchangeBase(BaseModel):
    """Base echange."""
    body: str = Field(..., min_length=1)
    body_html: str | None = None
    subject: str | None = Field(None, max_length=500)
    is_internal: bool = False


class ExchangeCreate(ExchangeBase):
    """Creation echange."""
    exchange_type: str = Field(default="reply", max_length=30)
    channel: ComplaintChannel | None = None
    cc_emails: list[EmailStr] | None = None
    bcc_emails: list[EmailStr] | None = None


class ExchangeResponse(ExchangeBase, TenantMixin):
    """Reponse echange."""
    id: UUID
    complaint_id: UUID
    author_type: str
    author_id: UUID | None = None
    author_name: str | None = None
    author_email: str | None = None
    exchange_type: str
    is_first_response: bool
    channel: ComplaintChannel | None = None
    message_id: str | None = None
    cc_emails: list[str] | None = None
    sentiment: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ATTACHMENT SCHEMAS
# ============================================================================

class AttachmentCreate(BaseModel):
    """Creation piece jointe."""
    filename: str = Field(..., max_length=255)
    original_filename: str | None = Field(None, max_length=255)
    file_path: str | None = Field(None, max_length=500)
    file_url: str | None = Field(None, max_length=500)
    file_size: int | None = Field(None, ge=0)
    mime_type: str | None = Field(None, max_length=100)
    description: str | None = None
    is_evidence: bool = False
    exchange_id: UUID | None = None


class AttachmentResponse(TenantMixin):
    """Reponse piece jointe."""
    id: UUID
    complaint_id: UUID
    exchange_id: UUID | None = None
    filename: str
    original_filename: str | None = None
    file_path: str | None = None
    file_url: str | None = None
    file_size: int | None = None
    mime_type: str | None = None
    description: str | None = None
    is_evidence: bool
    uploaded_by_id: UUID | None = None
    uploaded_by_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ACTION SCHEMAS
# ============================================================================

class ActionBase(BaseModel):
    """Base action."""
    action_type: ActionType = ActionType.OTHER
    title: str = Field(..., max_length=255)
    description: str | None = None
    assigned_to_id: UUID | None = None
    assigned_to_name: str | None = Field(None, max_length=255)
    due_date: datetime | None = None
    reminder_date: datetime | None = None


class ActionCreate(ActionBase):
    """Creation action."""
    pass


class ActionUpdate(BaseModel):
    """Mise a jour action."""
    action_type: ActionType | None = None
    title: str | None = Field(None, max_length=255)
    description: str | None = None
    assigned_to_id: UUID | None = None
    assigned_to_name: str | None = None
    due_date: datetime | None = None
    reminder_date: datetime | None = None
    status: str | None = None


class ActionComplete(BaseModel):
    """Completion action."""
    completion_notes: str | None = None
    outcome: str | None = Field(None, pattern="^(success|partial|failed)$")
    follow_up_required: bool = False


class ActionResponse(ActionBase, TenantMixin, AuditMixin):
    """Reponse action."""
    id: UUID
    complaint_id: UUID
    assigned_at: datetime | None = None
    status: str
    completed_at: datetime | None = None
    completed_by_id: UUID | None = None
    completion_notes: str | None = None
    outcome: str | None = None
    follow_up_required: bool

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ESCALATION SCHEMAS
# ============================================================================

class EscalationResponse(TenantMixin):
    """Reponse escalade."""
    id: UUID
    complaint_id: UUID
    from_level: EscalationLevel
    to_level: EscalationLevel
    reason: str
    is_automatic: bool
    escalated_by_id: UUID | None = None
    escalated_by_name: str | None = None
    assigned_to_id: UUID | None = None
    assigned_to_name: str | None = None
    accepted_at: datetime | None = None
    resolved_at: datetime | None = None
    resolution_notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# HISTORY SCHEMAS
# ============================================================================

class HistoryResponse(TenantMixin):
    """Reponse historique."""
    id: UUID
    complaint_id: UUID
    action: str
    field_name: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    actor_type: str
    actor_id: UUID | None = None
    actor_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TEMPLATE SCHEMAS
# ============================================================================

class TemplateBase(BaseModel):
    """Base modele."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: str | None = None
    category: ComplaintCategory | None = None
    template_type: str = Field(default="response", max_length=30)
    subject: str | None = Field(None, max_length=500)
    body: str = Field(..., min_length=10)
    body_html: str | None = None
    language: str = Field(default="fr", max_length=10)
    variables: list[str] | None = None
    scope: str = Field(default="global", pattern="^(personal|team|global)$")
    team_id: UUID | None = None


class TemplateCreate(TemplateBase):
    """Creation modele."""
    pass


class TemplateUpdate(BaseModel):
    """Mise a jour modele."""
    code: str | None = Field(None, max_length=50)
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    category: ComplaintCategory | None = None
    template_type: str | None = None
    subject: str | None = None
    body: str | None = None
    body_html: str | None = None
    language: str | None = None
    variables: list[str] | None = None
    scope: str | None = None
    team_id: UUID | None = None
    is_active: bool | None = None


class TemplateResponse(TemplateBase, TenantMixin, AuditMixin):
    """Reponse modele."""
    id: UUID
    owner_id: UUID | None = None
    usage_count: int
    last_used_at: datetime | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TemplateRender(BaseModel):
    """Rendu modele."""
    variables: dict[str, str]


class TemplateRendered(BaseModel):
    """Modele rendu."""
    subject: str | None = None
    body: str
    body_html: str | None = None


# ============================================================================
# AUTOMATION RULE SCHEMAS
# ============================================================================

class AutomationRuleBase(BaseModel):
    """Base regle automatisation."""
    name: str = Field(..., max_length=255)
    description: str | None = None
    trigger_event: str = Field(..., max_length=50)
    trigger_conditions: list[dict[str, Any]] | None = None
    actions: list[dict[str, Any]] = Field(...)
    priority: int = Field(default=0, ge=0, le=1000)
    stop_processing: bool = False


class AutomationRuleCreate(AutomationRuleBase):
    """Creation regle."""
    pass


class AutomationRuleUpdate(BaseModel):
    """Mise a jour regle."""
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    trigger_event: str | None = None
    trigger_conditions: list[dict[str, Any]] | None = None
    actions: list[dict[str, Any]] | None = None
    priority: int | None = None
    stop_processing: bool | None = None
    is_active: bool | None = None


class AutomationRuleResponse(AutomationRuleBase, TenantMixin, AuditMixin):
    """Reponse regle."""
    id: UUID
    execution_count: int
    last_executed_at: datetime | None = None
    last_error: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SATISFACTION SCHEMAS
# ============================================================================

class SatisfactionSubmit(BaseModel):
    """Soumission satisfaction."""
    rating: SatisfactionRating
    comment: str | None = Field(None, max_length=2000)
    nps_score: int | None = Field(None, ge=0, le=10)


class SatisfactionStats(BaseModel):
    """Statistiques satisfaction."""
    total_surveys: int = 0
    completed_surveys: int = 0
    response_rate: float = 0.0
    avg_rating: float = 0.0
    avg_nps: float = 0.0
    very_satisfied_percent: float = 0.0
    satisfied_percent: float = 0.0
    neutral_percent: float = 0.0
    dissatisfied_percent: float = 0.0
    very_dissatisfied_percent: float = 0.0
    nps_promoters: int = 0
    nps_passives: int = 0
    nps_detractors: int = 0


# ============================================================================
# STATISTICS & DASHBOARD SCHEMAS
# ============================================================================

class ComplaintStats(BaseModel):
    """Statistiques reclamations."""
    total: int = 0
    new: int = 0
    in_progress: int = 0
    pending: int = 0
    escalated: int = 0
    resolved: int = 0
    closed: int = 0
    sla_breached: int = 0
    sla_at_risk: int = 0
    avg_resolution_hours: float = 0.0
    avg_first_response_hours: float = 0.0
    resolution_rate: float = 0.0
    first_contact_resolution_rate: float = 0.0


class ComplaintsByCategory(BaseModel):
    """Repartition par categorie."""
    category: str
    count: int
    percentage: float


class ComplaintsByPriority(BaseModel):
    """Repartition par priorite."""
    priority: str
    count: int
    percentage: float


class ComplaintsByChannel(BaseModel):
    """Repartition par canal."""
    channel: str
    count: int
    percentage: float


class ComplaintsByStatus(BaseModel):
    """Repartition par statut."""
    status: str
    count: int
    percentage: float


class AgentPerformance(BaseModel):
    """Performance agent."""
    agent_id: UUID
    agent_name: str
    complaints_assigned: int = 0
    complaints_resolved: int = 0
    avg_resolution_hours: float = 0.0
    sla_compliance_rate: float = 0.0
    satisfaction_score: float = 0.0
    first_contact_resolution_rate: float = 0.0


class TeamPerformance(BaseModel):
    """Performance equipe."""
    team_id: UUID
    team_name: str
    complaints_total: int = 0
    complaints_resolved: int = 0
    avg_resolution_hours: float = 0.0
    sla_compliance_rate: float = 0.0
    satisfaction_score: float = 0.0
    backlog: int = 0


class SLAPerformance(BaseModel):
    """Performance SLA."""
    acknowledgment_compliance_rate: float = 0.0
    resolution_compliance_rate: float = 0.0
    avg_time_to_acknowledge_hours: float = 0.0
    avg_time_to_resolve_hours: float = 0.0
    breaches_this_period: int = 0
    at_risk_count: int = 0


class TrendData(BaseModel):
    """Donnees de tendance."""
    date: str
    count: int
    resolved: int = 0
    created: int = 0


class ComplaintDashboard(BaseModel):
    """Dashboard reclamations."""
    stats: ComplaintStats
    by_category: list[ComplaintsByCategory] = []
    by_priority: list[ComplaintsByPriority] = []
    by_channel: list[ComplaintsByChannel] = []
    by_status: list[ComplaintsByStatus] = []
    sla_performance: SLAPerformance
    satisfaction: SatisfactionStats
    agent_performance: list[AgentPerformance] = []
    team_performance: list[TeamPerformance] = []
    trends: list[TrendData] = []
    recent_complaints: list[ComplaintSummary] = []
    top_root_causes: list[dict[str, Any]] = []


# ============================================================================
# SEARCH & FILTER SCHEMAS
# ============================================================================

class ComplaintFilter(BaseModel):
    """Filtres de recherche."""
    query: str | None = None
    status: list[ComplaintStatus] | None = None
    priority: list[ComplaintPriority] | None = None
    category: list[ComplaintCategory] | None = None
    channel: list[ComplaintChannel] | None = None
    team_id: UUID | None = None
    assigned_to_id: UUID | None = None
    customer_id: UUID | None = None
    customer_email: str | None = None
    order_id: UUID | None = None
    sla_breached: bool | None = None
    sla_at_risk: bool | None = None
    escalated: bool | None = None
    has_compensation: bool | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    tags: list[str] | None = None


class PaginatedResponse(BaseModel):
    """Reponse paginee."""
    items: list[Any]
    total: int
    skip: int
    limit: int
    has_more: bool = False


# ============================================================================
# METRICS SCHEMAS
# ============================================================================

class MetricsResponse(BaseModel):
    """Reponse metriques."""
    id: UUID
    tenant_id: str
    metric_date: datetime
    period_type: str
    team_id: UUID | None = None
    agent_id: UUID | None = None
    category: ComplaintCategory | None = None
    channel: ComplaintChannel | None = None
    complaints_created: int
    complaints_resolved: int
    complaints_closed: int
    complaints_reopened: int
    complaints_escalated: int
    sla_ack_met: int
    sla_ack_breached: int
    sla_resolution_met: int
    sla_resolution_breached: int
    avg_first_response_hours: Decimal | None = None
    avg_resolution_hours: Decimal | None = None
    avg_satisfaction_score: Decimal | None = None
    avg_nps_score: Decimal | None = None
    total_compensation_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


# Update forward references
ComplaintDetail.model_rebuild()
