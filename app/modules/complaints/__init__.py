"""
AZALS MODULE - Complaints (Reclamations Clients)
=================================================

Module complet de gestion des reclamations clients pour AZALSCORE ERP.

Fonctionnalites:
- Saisie reclamations multi-canal (email, telephone, web, chat, reseaux sociaux)
- Categorisation et priorite automatique
- Attribution automatique (round-robin, least-busy)
- Workflow de traitement complet
- SLA et delais avec escalade automatique
- Actions correctives et suivi
- Liens produits/commandes/factures
- Historique complet des echanges
- Satisfaction client et NPS
- Rapports et KPIs

Conformite:
- ISO 10002 (Satisfaction client - Traitement des reclamations)
- RGPD (Protection des donnees personnelles)
- Mediation de la consommation (Code de la consommation)

Inspire des meilleures pratiques de:
- Microsoft Dynamics 365 Customer Service
- Odoo Helpdesk
- Sage X3 Alerts & Workflow
- Axonaut Ticketing SAV
- Pennylane (integration comptable)

Architecture:
- Multi-tenant avec isolation stricte par tenant_id
- Soft delete sur toutes les entites
- Audit complet avec versioning
- Pattern Repository avec _base_query() filtre
"""

from .models import (
    # Enums
    ActionType,
    ComplaintCategory,
    ComplaintChannel,
    ComplaintPriority,
    ComplaintStatus,
    EscalationLevel,
    ResolutionType,
    RootCauseCategory,
    SatisfactionRating,
    # Models
    Complaint,
    ComplaintAction,
    ComplaintAgent,
    ComplaintAttachment,
    ComplaintAutomationRule,
    ComplaintCategoryConfig,
    ComplaintEscalation,
    ComplaintExchange,
    ComplaintHistory,
    ComplaintMetrics,
    ComplaintSLAPolicy,
    ComplaintTeam,
    ComplaintTemplate,
)

from .schemas import (
    # Category
    CategoryConfigCreate,
    CategoryConfigResponse,
    CategoryConfigUpdate,
    # Team
    TeamCreate,
    TeamResponse,
    TeamUpdate,
    TeamWithStats,
    # Agent
    AgentCreate,
    AgentResponse,
    AgentUpdate,
    AgentAvailabilityUpdate,
    # SLA Policy
    SLAPolicyCreate,
    SLAPolicyResponse,
    SLAPolicyUpdate,
    # Complaint
    ComplaintCreate,
    ComplaintUpdate,
    ComplaintResponse,
    ComplaintDetail,
    ComplaintSummary,
    ComplaintAssign,
    ComplaintStatusChange,
    ComplaintEscalate,
    ComplaintResolve,
    ComplaintClose,
    ComplaintReopen,
    ComplaintFilter,
    # Exchange
    ExchangeCreate,
    ExchangeResponse,
    # Attachment
    AttachmentCreate,
    AttachmentResponse,
    # Action
    ActionCreate,
    ActionUpdate,
    ActionComplete,
    ActionResponse,
    # Escalation & History
    EscalationResponse,
    HistoryResponse,
    # Template
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateRender,
    TemplateRendered,
    # Automation
    AutomationRuleCreate,
    AutomationRuleUpdate,
    AutomationRuleResponse,
    # Satisfaction
    SatisfactionSubmit,
    SatisfactionStats,
    # Statistics & Dashboard
    ComplaintStats,
    ComplaintsByCategory,
    ComplaintsByPriority,
    ComplaintsByChannel,
    ComplaintsByStatus,
    AgentPerformance,
    TeamPerformance,
    SLAPerformance,
    TrendData,
    ComplaintDashboard,
    MetricsResponse,
    PaginatedResponse,
)

from .exceptions import (
    ComplaintException,
    ComplaintNotFoundError,
    TeamNotFoundError,
    AgentNotFoundError,
    CategoryNotFoundError,
    SLAPolicyNotFoundError,
    TemplateNotFoundError,
    ActionNotFoundError,
    ExchangeNotFoundError,
    AttachmentNotFoundError,
    AutomationRuleNotFoundError,
    InvalidStatusTransitionError,
    InvalidEscalationLevelError,
    ComplaintAlreadyClosedError,
    ComplaintNotResolvedError,
    DuplicateReferenceError,
    DuplicateCodeError,
    CustomerInfoRequiredError,
    ResolutionRequiredError,
    AgentNotAvailableError,
    AgentOverloadedError,
    InsufficientPermissionError,
    CompensationLimitExceededError,
    ApprovalRequiredError,
    SLABreachWarning,
    SLABreachedError,
    TemplateVariableError,
    TemplateRenderError,
    AutomationExecutionError,
    InvalidAutomationConditionError,
    InvalidAutomationActionError,
    FileTooLargeError,
    InvalidFileTypeError,
    FileUploadError,
)

from .repository import (
    ComplaintRepository,
    TeamRepository,
    AgentRepository,
    CategoryConfigRepository,
    SLAPolicyRepository,
    ExchangeRepository,
    AttachmentRepository,
    ActionRepository,
    EscalationRepository,
    HistoryRepository,
    TemplateRepository,
    AutomationRuleRepository,
    MetricsRepository,
)

from .service import ComplaintService

from .router import router

__all__ = [
    # Router
    "router",
    # Service
    "ComplaintService",
    # Repositories
    "ComplaintRepository",
    "TeamRepository",
    "AgentRepository",
    "CategoryConfigRepository",
    "SLAPolicyRepository",
    "ExchangeRepository",
    "AttachmentRepository",
    "ActionRepository",
    "EscalationRepository",
    "HistoryRepository",
    "TemplateRepository",
    "AutomationRuleRepository",
    "MetricsRepository",
    # Enums
    "ActionType",
    "ComplaintCategory",
    "ComplaintChannel",
    "ComplaintPriority",
    "ComplaintStatus",
    "EscalationLevel",
    "ResolutionType",
    "RootCauseCategory",
    "SatisfactionRating",
    # Models
    "Complaint",
    "ComplaintAction",
    "ComplaintAgent",
    "ComplaintAttachment",
    "ComplaintAutomationRule",
    "ComplaintCategoryConfig",
    "ComplaintEscalation",
    "ComplaintExchange",
    "ComplaintHistory",
    "ComplaintMetrics",
    "ComplaintSLAPolicy",
    "ComplaintTeam",
    "ComplaintTemplate",
    # Schemas
    "CategoryConfigCreate",
    "CategoryConfigResponse",
    "CategoryConfigUpdate",
    "TeamCreate",
    "TeamResponse",
    "TeamUpdate",
    "TeamWithStats",
    "AgentCreate",
    "AgentResponse",
    "AgentUpdate",
    "AgentAvailabilityUpdate",
    "SLAPolicyCreate",
    "SLAPolicyResponse",
    "SLAPolicyUpdate",
    "ComplaintCreate",
    "ComplaintUpdate",
    "ComplaintResponse",
    "ComplaintDetail",
    "ComplaintSummary",
    "ComplaintAssign",
    "ComplaintStatusChange",
    "ComplaintEscalate",
    "ComplaintResolve",
    "ComplaintClose",
    "ComplaintReopen",
    "ComplaintFilter",
    "ExchangeCreate",
    "ExchangeResponse",
    "AttachmentCreate",
    "AttachmentResponse",
    "ActionCreate",
    "ActionUpdate",
    "ActionComplete",
    "ActionResponse",
    "EscalationResponse",
    "HistoryResponse",
    "TemplateCreate",
    "TemplateUpdate",
    "TemplateResponse",
    "TemplateRender",
    "TemplateRendered",
    "AutomationRuleCreate",
    "AutomationRuleUpdate",
    "AutomationRuleResponse",
    "SatisfactionSubmit",
    "SatisfactionStats",
    "ComplaintStats",
    "ComplaintsByCategory",
    "ComplaintsByPriority",
    "ComplaintsByChannel",
    "ComplaintsByStatus",
    "AgentPerformance",
    "TeamPerformance",
    "SLAPerformance",
    "TrendData",
    "ComplaintDashboard",
    "MetricsResponse",
    "PaginatedResponse",
    # Exceptions
    "ComplaintException",
    "ComplaintNotFoundError",
    "TeamNotFoundError",
    "AgentNotFoundError",
    "CategoryNotFoundError",
    "SLAPolicyNotFoundError",
    "TemplateNotFoundError",
    "ActionNotFoundError",
    "ExchangeNotFoundError",
    "AttachmentNotFoundError",
    "AutomationRuleNotFoundError",
    "InvalidStatusTransitionError",
    "InvalidEscalationLevelError",
    "ComplaintAlreadyClosedError",
    "ComplaintNotResolvedError",
    "DuplicateReferenceError",
    "DuplicateCodeError",
    "CustomerInfoRequiredError",
    "ResolutionRequiredError",
    "AgentNotAvailableError",
    "AgentOverloadedError",
    "InsufficientPermissionError",
    "CompensationLimitExceededError",
    "ApprovalRequiredError",
    "SLABreachWarning",
    "SLABreachedError",
    "TemplateVariableError",
    "TemplateRenderError",
    "AutomationExecutionError",
    "InvalidAutomationConditionError",
    "InvalidAutomationActionError",
    "FileTooLargeError",
    "InvalidFileTypeError",
    "FileUploadError",
]
