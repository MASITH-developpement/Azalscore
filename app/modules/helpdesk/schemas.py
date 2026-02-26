"""
AZALS MODULE 16 - Helpdesk Schemas
===================================
Schémas Pydantic pour le système de support client.
"""
from __future__ import annotations


from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .models import AgentStatus, TicketPriority, TicketSource, TicketStatus

# ============================================================================
# CATEGORY SCHEMAS
# ============================================================================

class CategoryBase(BaseModel):
    """Base catégorie."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: str | None = None
    parent_id: int | None = None
    default_priority: TicketPriority = TicketPriority.MEDIUM
    default_team_id: int | None = None
    sla_id: int | None = None
    is_public: bool = True
    require_approval: bool = False
    auto_assign: bool = True
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    """Création catégorie."""
    pass


class CategoryUpdate(BaseModel):
    """Mise à jour catégorie."""
    code: str | None = Field(None, max_length=50)
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    parent_id: int | None = None
    default_priority: TicketPriority | None = None
    default_team_id: int | None = None
    sla_id: int | None = None
    is_public: bool | None = None
    require_approval: bool | None = None
    auto_assign: bool | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class CategoryResponse(CategoryBase):
    """Réponse catégorie."""
    id: int
    tenant_id: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TEAM SCHEMAS
# ============================================================================

class TeamBase(BaseModel):
    """Base équipe."""
    name: str = Field(..., max_length=100)
    description: str | None = None
    email: str | None = None
    manager_id: int | None = None
    default_sla_id: int | None = None
    auto_assign_method: str = "round_robin"
    max_tickets_per_agent: int = 20
    working_hours: dict[str, Any] | None = None
    timezone: str = "Europe/Paris"


class TeamCreate(TeamBase):
    """Création équipe."""
    pass


class TeamUpdate(BaseModel):
    """Mise à jour équipe."""
    name: str | None = Field(None, max_length=100)
    description: str | None = None
    email: str | None = None
    manager_id: int | None = None
    default_sla_id: int | None = None
    auto_assign_method: str | None = None
    max_tickets_per_agent: int | None = None
    working_hours: dict[str, Any] | None = None
    timezone: str | None = None
    is_active: bool | None = None


class TeamResponse(TeamBase):
    """Réponse équipe."""
    id: int
    tenant_id: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# AGENT SCHEMAS
# ============================================================================

class AgentBase(BaseModel):
    """Base agent."""
    user_id: int
    team_id: int | None = None
    display_name: str = Field(..., max_length=255)
    email: str | None = None
    avatar_url: str | None = None
    signature: str | None = None
    skills: list[str] | None = None
    languages: list[str] = ["fr"]
    can_assign: bool = True
    can_merge: bool = False
    can_delete: bool = False
    can_view_all: bool = False
    is_supervisor: bool = False


class AgentCreate(AgentBase):
    """Création agent."""
    pass


class AgentUpdate(BaseModel):
    """Mise à jour agent."""
    team_id: int | None = None
    display_name: str | None = Field(None, max_length=255)
    email: str | None = None
    avatar_url: str | None = None
    signature: str | None = None
    status: AgentStatus | None = None
    skills: list[str] | None = None
    languages: list[str] | None = None
    can_assign: bool | None = None
    can_merge: bool | None = None
    can_delete: bool | None = None
    can_view_all: bool | None = None
    is_supervisor: bool | None = None
    is_active: bool | None = None


class AgentResponse(AgentBase):
    """Réponse agent."""
    id: int
    tenant_id: str
    status: AgentStatus
    last_seen: datetime | None = None
    tickets_assigned: int
    tickets_resolved: int
    avg_resolution_time: int
    satisfaction_score: Decimal
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentStatusUpdate(BaseModel):
    """Mise à jour statut agent."""
    status: AgentStatus


# ============================================================================
# SLA SCHEMAS
# ============================================================================

class SLABase(BaseModel):
    """Base SLA."""
    name: str = Field(..., max_length=100)
    description: str | None = None
    first_response_low: int = 1440
    first_response_medium: int = 480
    first_response_high: int = 120
    first_response_urgent: int = 60
    first_response_critical: int = 15
    resolution_low: int = 10080
    resolution_medium: int = 2880
    resolution_high: int = 1440
    resolution_urgent: int = 480
    resolution_critical: int = 120
    business_hours_only: bool = True
    working_hours: dict[str, Any] | None = None
    timezone: str = "Europe/Paris"
    holidays: list[str] | None = None
    escalation_enabled: bool = True
    escalation_rules: list[dict[str, Any]] | None = None
    is_default: bool = False


class SLACreate(SLABase):
    """Création SLA."""
    pass


class SLAUpdate(BaseModel):
    """Mise à jour SLA."""
    name: str | None = Field(None, max_length=100)
    description: str | None = None
    first_response_low: int | None = None
    first_response_medium: int | None = None
    first_response_high: int | None = None
    first_response_urgent: int | None = None
    first_response_critical: int | None = None
    resolution_low: int | None = None
    resolution_medium: int | None = None
    resolution_high: int | None = None
    resolution_urgent: int | None = None
    resolution_critical: int | None = None
    business_hours_only: bool | None = None
    working_hours: dict[str, Any] | None = None
    timezone: str | None = None
    holidays: list[str] | None = None
    escalation_enabled: bool | None = None
    escalation_rules: list[dict[str, Any]] | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class SLAResponse(SLABase):
    """Réponse SLA."""
    id: int
    tenant_id: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TICKET SCHEMAS
# ============================================================================

class TicketBase(BaseModel):
    """Base ticket."""
    subject: str = Field(..., max_length=500)
    description: str | None = None
    category_id: int | None = None
    priority: TicketPriority = TicketPriority.MEDIUM
    source: TicketSource = TicketSource.WEB
    requester_name: str | None = None
    requester_email: str | None = None
    requester_phone: str | None = None
    requester_id: int | None = None
    company_id: int | None = None
    tags: list[str] | None = None
    custom_fields: dict[str, Any] | None = None


class TicketCreate(TicketBase):
    """Création ticket."""
    team_id: int | None = None
    assigned_to_id: int | None = None


class TicketUpdate(BaseModel):
    """Mise à jour ticket."""
    subject: str | None = Field(None, max_length=500)
    description: str | None = None
    category_id: int | None = None
    team_id: int | None = None
    priority: TicketPriority | None = None
    status: TicketStatus | None = None
    assigned_to_id: int | None = None
    tags: list[str] | None = None
    custom_fields: dict[str, Any] | None = None


class TicketAssign(BaseModel):
    """Assignation ticket."""
    agent_id: int


class TicketStatusChange(BaseModel):
    """Changement statut."""
    status: TicketStatus
    comment: str | None = None


class TicketResponse(TicketBase):
    """Réponse ticket."""
    id: int
    tenant_id: str
    ticket_number: str
    team_id: int | None = None
    sla_id: int | None = None
    status: TicketStatus
    assigned_to_id: int | None = None
    first_response_due: datetime | None = None
    first_responded_at: datetime | None = None
    resolution_due: datetime | None = None
    resolved_at: datetime | None = None
    sla_breached: bool
    parent_ticket_id: int | None = None
    merged_into_id: int | None = None
    reply_count: int
    internal_note_count: int
    satisfaction_rating: int | None = None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TicketDetail(TicketResponse):
    """Détail ticket avec relations."""
    category: CategoryResponse | None = None
    team: TeamResponse | None = None
    assigned_agent: AgentResponse | None = None
    replies: list["ReplyResponse"] = []


# ============================================================================
# REPLY SCHEMAS
# ============================================================================

class ReplyBase(BaseModel):
    """Base réponse."""
    body: str
    body_html: str | None = None
    is_internal: bool = False
    cc_emails: list[str] | None = None
    bcc_emails: list[str] | None = None


class ReplyCreate(ReplyBase):
    """Création réponse."""
    pass


class ReplyResponse(ReplyBase):
    """Réponse."""
    id: int
    tenant_id: str
    ticket_id: int
    author_type: str
    author_id: int | None = None
    author_name: str | None = None
    author_email: str | None = None
    is_first_response: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ATTACHMENT SCHEMAS
# ============================================================================

class AttachmentCreate(BaseModel):
    """Création pièce jointe."""
    filename: str = Field(..., max_length=255)
    file_path: str | None = None
    file_url: str | None = None
    file_size: int | None = None
    mime_type: str | None = None
    reply_id: int | None = None


class AttachmentResponse(BaseModel):
    """Réponse pièce jointe."""
    id: int
    tenant_id: str
    ticket_id: int
    reply_id: int | None = None
    filename: str
    file_path: str | None = None
    file_url: str | None = None
    file_size: int | None = None
    mime_type: str | None = None
    uploaded_by_id: int | None = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# HISTORY SCHEMAS
# ============================================================================

class HistoryResponse(BaseModel):
    """Réponse historique."""
    id: int
    tenant_id: str
    ticket_id: int
    action: str
    field_name: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    actor_type: str | None = None
    actor_id: int | None = None
    actor_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CANNED RESPONSE SCHEMAS
# ============================================================================

class CannedResponseBase(BaseModel):
    """Base réponse pré-enregistrée."""
    title: str = Field(..., max_length=255)
    shortcut: str | None = Field(None, max_length=50)
    body: str
    body_html: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    scope: str = "team"
    team_id: int | None = None


class CannedResponseCreate(CannedResponseBase):
    """Création réponse pré-enregistrée."""
    pass


class CannedResponseUpdate(BaseModel):
    """Mise à jour réponse pré-enregistrée."""
    title: str | None = Field(None, max_length=255)
    shortcut: str | None = Field(None, max_length=50)
    body: str | None = None
    body_html: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    scope: str | None = None
    team_id: int | None = None
    is_active: bool | None = None


class CannedResponseResponse(CannedResponseBase):
    """Réponse."""
    id: int
    tenant_id: str
    agent_id: int | None = None
    usage_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# KNOWLEDGE BASE SCHEMAS
# ============================================================================

class KBCategoryBase(BaseModel):
    """Base catégorie KB."""
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255)
    description: str | None = None
    icon: str | None = None
    parent_id: int | None = None
    sort_order: int = 0
    is_public: bool = True


class KBCategoryCreate(KBCategoryBase):
    """Création catégorie KB."""
    pass


class KBCategoryUpdate(BaseModel):
    """Mise à jour catégorie KB."""
    name: str | None = Field(None, max_length=255)
    slug: str | None = Field(None, max_length=255)
    description: str | None = None
    icon: str | None = None
    parent_id: int | None = None
    sort_order: int | None = None
    is_public: bool | None = None
    is_active: bool | None = None


class KBCategoryResponse(KBCategoryBase):
    """Réponse catégorie KB."""
    id: int
    tenant_id: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KBArticleBase(BaseModel):
    """Base article KB."""
    title: str = Field(..., max_length=500)
    slug: str = Field(..., max_length=500)
    excerpt: str | None = None
    body: str
    body_html: str | None = None
    category_id: int | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    keywords: list[str] | None = None
    status: str = "draft"
    is_featured: bool = False
    is_public: bool = True


class KBArticleCreate(KBArticleBase):
    """Création article KB."""
    pass


class KBArticleUpdate(BaseModel):
    """Mise à jour article KB."""
    title: str | None = Field(None, max_length=500)
    slug: str | None = Field(None, max_length=500)
    excerpt: str | None = None
    body: str | None = None
    body_html: str | None = None
    category_id: int | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    keywords: list[str] | None = None
    status: str | None = None
    is_featured: bool | None = None
    is_public: bool | None = None


class KBArticleResponse(KBArticleBase):
    """Réponse article KB."""
    id: int
    tenant_id: str
    author_id: int | None = None
    author_name: str | None = None
    view_count: int
    helpful_count: int
    not_helpful_count: int
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SATISFACTION SCHEMAS
# ============================================================================

class SatisfactionCreate(BaseModel):
    """Création enquête satisfaction."""
    ticket_id: int
    rating: int = Field(..., ge=1, le=5)
    feedback: str | None = None
    customer_email: str | None = None


class SatisfactionResponse(BaseModel):
    """Réponse satisfaction."""
    id: int
    tenant_id: str
    ticket_id: int
    rating: int
    feedback: str | None = None
    customer_id: int | None = None
    customer_email: str | None = None
    agent_id: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# AUTOMATION SCHEMAS
# ============================================================================

class AutomationBase(BaseModel):
    """Base automatisation."""
    name: str = Field(..., max_length=255)
    description: str | None = None
    trigger_type: str = Field(..., max_length=50)
    trigger_conditions: list[dict[str, Any]] | None = None
    actions: list[dict[str, Any]] | None = None
    priority: int = 0


class AutomationCreate(AutomationBase):
    """Création automatisation."""
    pass


class AutomationUpdate(BaseModel):
    """Mise à jour automatisation."""
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    trigger_type: str | None = None
    trigger_conditions: list[dict[str, Any]] | None = None
    actions: list[dict[str, Any]] | None = None
    priority: int | None = None
    is_active: bool | None = None


class AutomationResponse(AutomationBase):
    """Réponse automatisation."""
    id: int
    tenant_id: str
    execution_count: int
    last_executed_at: datetime | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# DASHBOARD & STATS
# ============================================================================

class TicketStats(BaseModel):
    """Statistiques tickets."""
    total: int = 0
    new: int = 0
    open: int = 0
    pending: int = 0
    on_hold: int = 0
    resolved: int = 0
    closed: int = 0
    overdue: int = 0
    avg_resolution_time: float = 0.0
    first_response_sla_met: float = 0.0
    resolution_sla_met: float = 0.0


class AgentStats(BaseModel):
    """Statistiques agent."""
    agent_id: int
    agent_name: str
    tickets_assigned: int = 0
    tickets_resolved: int = 0
    avg_resolution_time: float = 0.0
    satisfaction_score: float = 0.0
    response_rate: float = 0.0


class HelpdeskDashboard(BaseModel):
    """Dashboard Helpdesk."""
    ticket_stats: TicketStats
    agent_stats: list[AgentStats] = []
    tickets_by_priority: dict[str, int] = {}
    tickets_by_category: dict[str, int] = {}
    tickets_by_source: dict[str, int] = {}
    recent_tickets: list[TicketResponse] = []
    sla_performance: dict[str, float] = {}


# Update forward references
TicketDetail.model_rebuild()
