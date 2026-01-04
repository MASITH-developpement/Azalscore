"""
AZALS MODULE 16 - Helpdesk Schemas
===================================
Schémas Pydantic pour le système de support client.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr

from .models import TicketStatus, TicketPriority, TicketSource, AgentStatus


# ============================================================================
# CATEGORY SCHEMAS
# ============================================================================

class CategoryBase(BaseModel):
    """Base catégorie."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    default_priority: TicketPriority = TicketPriority.MEDIUM
    default_team_id: Optional[int] = None
    sla_id: Optional[int] = None
    is_public: bool = True
    require_approval: bool = False
    auto_assign: bool = True
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    """Création catégorie."""
    pass


class CategoryUpdate(BaseModel):
    """Mise à jour catégorie."""
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    default_priority: Optional[TicketPriority] = None
    default_team_id: Optional[int] = None
    sla_id: Optional[int] = None
    is_public: Optional[bool] = None
    require_approval: Optional[bool] = None
    auto_assign: Optional[bool] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    """Réponse catégorie."""
    id: int
    tenant_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TEAM SCHEMAS
# ============================================================================

class TeamBase(BaseModel):
    """Base équipe."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    email: Optional[str] = None
    manager_id: Optional[int] = None
    default_sla_id: Optional[int] = None
    auto_assign_method: str = "round_robin"
    max_tickets_per_agent: int = 20
    working_hours: Optional[Dict[str, Any]] = None
    timezone: str = "Europe/Paris"


class TeamCreate(TeamBase):
    """Création équipe."""
    pass


class TeamUpdate(BaseModel):
    """Mise à jour équipe."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    email: Optional[str] = None
    manager_id: Optional[int] = None
    default_sla_id: Optional[int] = None
    auto_assign_method: Optional[str] = None
    max_tickets_per_agent: Optional[int] = None
    working_hours: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None


class TeamResponse(TeamBase):
    """Réponse équipe."""
    id: int
    tenant_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# AGENT SCHEMAS
# ============================================================================

class AgentBase(BaseModel):
    """Base agent."""
    user_id: int
    team_id: Optional[int] = None
    display_name: str = Field(..., max_length=255)
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    signature: Optional[str] = None
    skills: Optional[List[str]] = None
    languages: List[str] = ["fr"]
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
    team_id: Optional[int] = None
    display_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    signature: Optional[str] = None
    status: Optional[AgentStatus] = None
    skills: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    can_assign: Optional[bool] = None
    can_merge: Optional[bool] = None
    can_delete: Optional[bool] = None
    can_view_all: Optional[bool] = None
    is_supervisor: Optional[bool] = None
    is_active: Optional[bool] = None


class AgentResponse(AgentBase):
    """Réponse agent."""
    id: int
    tenant_id: str
    status: AgentStatus
    last_seen: Optional[datetime] = None
    tickets_assigned: int
    tickets_resolved: int
    avg_resolution_time: int
    satisfaction_score: Decimal
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AgentStatusUpdate(BaseModel):
    """Mise à jour statut agent."""
    status: AgentStatus


# ============================================================================
# SLA SCHEMAS
# ============================================================================

class SLABase(BaseModel):
    """Base SLA."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
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
    working_hours: Optional[Dict[str, Any]] = None
    timezone: str = "Europe/Paris"
    holidays: Optional[List[str]] = None
    escalation_enabled: bool = True
    escalation_rules: Optional[List[Dict[str, Any]]] = None
    is_default: bool = False


class SLACreate(SLABase):
    """Création SLA."""
    pass


class SLAUpdate(BaseModel):
    """Mise à jour SLA."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    first_response_low: Optional[int] = None
    first_response_medium: Optional[int] = None
    first_response_high: Optional[int] = None
    first_response_urgent: Optional[int] = None
    first_response_critical: Optional[int] = None
    resolution_low: Optional[int] = None
    resolution_medium: Optional[int] = None
    resolution_high: Optional[int] = None
    resolution_urgent: Optional[int] = None
    resolution_critical: Optional[int] = None
    business_hours_only: Optional[bool] = None
    working_hours: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None
    holidays: Optional[List[str]] = None
    escalation_enabled: Optional[bool] = None
    escalation_rules: Optional[List[Dict[str, Any]]] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class SLAResponse(SLABase):
    """Réponse SLA."""
    id: int
    tenant_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TICKET SCHEMAS
# ============================================================================

class TicketBase(BaseModel):
    """Base ticket."""
    subject: str = Field(..., max_length=500)
    description: Optional[str] = None
    category_id: Optional[int] = None
    priority: TicketPriority = TicketPriority.MEDIUM
    source: TicketSource = TicketSource.WEB
    requester_name: Optional[str] = None
    requester_email: Optional[str] = None
    requester_phone: Optional[str] = None
    requester_id: Optional[int] = None
    company_id: Optional[int] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class TicketCreate(TicketBase):
    """Création ticket."""
    team_id: Optional[int] = None
    assigned_to_id: Optional[int] = None


class TicketUpdate(BaseModel):
    """Mise à jour ticket."""
    subject: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    category_id: Optional[int] = None
    team_id: Optional[int] = None
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None
    assigned_to_id: Optional[int] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class TicketAssign(BaseModel):
    """Assignation ticket."""
    agent_id: int


class TicketStatusChange(BaseModel):
    """Changement statut."""
    status: TicketStatus
    comment: Optional[str] = None


class TicketResponse(TicketBase):
    """Réponse ticket."""
    id: int
    tenant_id: str
    ticket_number: str
    team_id: Optional[int] = None
    sla_id: Optional[int] = None
    status: TicketStatus
    assigned_to_id: Optional[int] = None
    first_response_due: Optional[datetime] = None
    first_responded_at: Optional[datetime] = None
    resolution_due: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    sla_breached: bool
    parent_ticket_id: Optional[int] = None
    merged_into_id: Optional[int] = None
    reply_count: int
    internal_note_count: int
    satisfaction_rating: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketDetail(TicketResponse):
    """Détail ticket avec relations."""
    category: Optional[CategoryResponse] = None
    team: Optional[TeamResponse] = None
    assigned_agent: Optional[AgentResponse] = None
    replies: List["ReplyResponse"] = []


# ============================================================================
# REPLY SCHEMAS
# ============================================================================

class ReplyBase(BaseModel):
    """Base réponse."""
    body: str
    body_html: Optional[str] = None
    is_internal: bool = False
    cc_emails: Optional[List[str]] = None
    bcc_emails: Optional[List[str]] = None


class ReplyCreate(ReplyBase):
    """Création réponse."""
    pass


class ReplyResponse(ReplyBase):
    """Réponse."""
    id: int
    tenant_id: str
    ticket_id: int
    author_type: str
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    is_first_response: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ATTACHMENT SCHEMAS
# ============================================================================

class AttachmentCreate(BaseModel):
    """Création pièce jointe."""
    filename: str = Field(..., max_length=255)
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    reply_id: Optional[int] = None


class AttachmentResponse(BaseModel):
    """Réponse pièce jointe."""
    id: int
    tenant_id: str
    ticket_id: int
    reply_id: Optional[int] = None
    filename: str
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_by_id: Optional[int] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# HISTORY SCHEMAS
# ============================================================================

class HistoryResponse(BaseModel):
    """Réponse historique."""
    id: int
    tenant_id: str
    ticket_id: int
    action: str
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    actor_type: Optional[str] = None
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# CANNED RESPONSE SCHEMAS
# ============================================================================

class CannedResponseBase(BaseModel):
    """Base réponse pré-enregistrée."""
    title: str = Field(..., max_length=255)
    shortcut: Optional[str] = Field(None, max_length=50)
    body: str
    body_html: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    scope: str = "team"
    team_id: Optional[int] = None


class CannedResponseCreate(CannedResponseBase):
    """Création réponse pré-enregistrée."""
    pass


class CannedResponseUpdate(BaseModel):
    """Mise à jour réponse pré-enregistrée."""
    title: Optional[str] = Field(None, max_length=255)
    shortcut: Optional[str] = Field(None, max_length=50)
    body: Optional[str] = None
    body_html: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    scope: Optional[str] = None
    team_id: Optional[int] = None
    is_active: Optional[bool] = None


class CannedResponseResponse(CannedResponseBase):
    """Réponse."""
    id: int
    tenant_id: str
    agent_id: Optional[int] = None
    usage_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# KNOWLEDGE BASE SCHEMAS
# ============================================================================

class KBCategoryBase(BaseModel):
    """Base catégorie KB."""
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int = 0
    is_public: bool = True


class KBCategoryCreate(KBCategoryBase):
    """Création catégorie KB."""
    pass


class KBCategoryUpdate(BaseModel):
    """Mise à jour catégorie KB."""
    name: Optional[str] = Field(None, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None


class KBCategoryResponse(KBCategoryBase):
    """Réponse catégorie KB."""
    id: int
    tenant_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class KBArticleBase(BaseModel):
    """Base article KB."""
    title: str = Field(..., max_length=500)
    slug: str = Field(..., max_length=500)
    excerpt: Optional[str] = None
    body: str
    body_html: Optional[str] = None
    category_id: Optional[int] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    keywords: Optional[List[str]] = None
    status: str = "draft"
    is_featured: bool = False
    is_public: bool = True


class KBArticleCreate(KBArticleBase):
    """Création article KB."""
    pass


class KBArticleUpdate(BaseModel):
    """Mise à jour article KB."""
    title: Optional[str] = Field(None, max_length=500)
    slug: Optional[str] = Field(None, max_length=500)
    excerpt: Optional[str] = None
    body: Optional[str] = None
    body_html: Optional[str] = None
    category_id: Optional[int] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    keywords: Optional[List[str]] = None
    status: Optional[str] = None
    is_featured: Optional[bool] = None
    is_public: Optional[bool] = None


class KBArticleResponse(KBArticleBase):
    """Réponse article KB."""
    id: int
    tenant_id: str
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    view_count: int
    helpful_count: int
    not_helpful_count: int
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SATISFACTION SCHEMAS
# ============================================================================

class SatisfactionCreate(BaseModel):
    """Création enquête satisfaction."""
    ticket_id: int
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None
    customer_email: Optional[str] = None


class SatisfactionResponse(BaseModel):
    """Réponse satisfaction."""
    id: int
    tenant_id: str
    ticket_id: int
    rating: int
    feedback: Optional[str] = None
    customer_id: Optional[int] = None
    customer_email: Optional[str] = None
    agent_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# AUTOMATION SCHEMAS
# ============================================================================

class AutomationBase(BaseModel):
    """Base automatisation."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    trigger_type: str = Field(..., max_length=50)
    trigger_conditions: Optional[List[Dict[str, Any]]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    priority: int = 0


class AutomationCreate(AutomationBase):
    """Création automatisation."""
    pass


class AutomationUpdate(BaseModel):
    """Mise à jour automatisation."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    trigger_type: Optional[str] = None
    trigger_conditions: Optional[List[Dict[str, Any]]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class AutomationResponse(AutomationBase):
    """Réponse automatisation."""
    id: int
    tenant_id: str
    execution_count: int
    last_executed_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


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
    agent_stats: List[AgentStats] = []
    tickets_by_priority: Dict[str, int] = {}
    tickets_by_category: Dict[str, int] = {}
    tickets_by_source: Dict[str, int] = {}
    recent_tickets: List[TicketResponse] = []
    sla_performance: Dict[str, float] = {}


# Update forward references
TicketDetail.model_rebuild()
