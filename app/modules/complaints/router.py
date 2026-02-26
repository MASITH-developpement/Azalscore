"""
AZALS MODULE - Complaints Router
=================================

API endpoints pour le systeme de gestion des reclamations clients.
"""
from __future__ import annotations


from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.core.models import User

from .exceptions import (
    AgentNotAvailableError,
    AgentNotFoundError,
    CategoryNotFoundError,
    CompensationLimitExceededError,
    ComplaintAlreadyClosedError,
    ComplaintException,
    ComplaintNotFoundError,
    ComplaintNotResolvedError,
    CustomerInfoRequiredError,
    DuplicateCodeError,
    InsufficientPermissionError,
    InvalidEscalationLevelError,
    InvalidStatusTransitionError,
    SLAPolicyNotFoundError,
    TeamNotFoundError,
    TemplateNotFoundError,
    TemplateVariableError,
)
from .models import ComplaintCategory, ComplaintChannel, ComplaintPriority, ComplaintStatus
from .schemas import (
    ActionComplete,
    ActionCreate,
    ActionResponse,
    ActionUpdate,
    AgentCreate,
    AgentResponse,
    AgentUpdate,
    AttachmentCreate,
    AttachmentResponse,
    AutomationRuleCreate,
    AutomationRuleResponse,
    AutomationRuleUpdate,
    CategoryConfigCreate,
    CategoryConfigResponse,
    CategoryConfigUpdate,
    ComplaintAssign,
    ComplaintClose,
    ComplaintCreate,
    ComplaintDashboard,
    ComplaintDetail,
    ComplaintEscalate,
    ComplaintFilter,
    ComplaintReopen,
    ComplaintResolve,
    ComplaintResponse,
    ComplaintStats,
    ComplaintStatusChange,
    ComplaintSummary,
    ComplaintUpdate,
    EscalationResponse,
    ExchangeCreate,
    ExchangeResponse,
    HistoryResponse,
    SatisfactionSubmit,
    SLAPolicyCreate,
    SLAPolicyResponse,
    SLAPolicyUpdate,
    TeamCreate,
    TeamResponse,
    TeamUpdate,
    TemplateCreate,
    TemplateRender,
    TemplateRendered,
    TemplateResponse,
    TemplateUpdate,
)
from .service import ComplaintService

router = APIRouter(prefix="/complaints", tags=["Complaints"])


# ============================================================================
# DEPENDENCY
# ============================================================================

def get_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
) -> ComplaintService:
    """Factory service avec tenant et authentification obligatoire."""
    return ComplaintService(db, tenant_id)


def handle_exception(e: ComplaintException):
    """Convertit une exception metier en HTTPException."""
    status_map = {
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "INVALID": status.HTTP_400_BAD_REQUEST,
        "PERMISSION": status.HTTP_403_FORBIDDEN,
        "DUPLICATE": status.HTTP_409_CONFLICT,
        "REQUIRED": status.HTTP_400_BAD_REQUEST,
    }

    http_status = status.HTTP_400_BAD_REQUEST
    for key, val in status_map.items():
        if key in e.code:
            http_status = val
            break

    raise HTTPException(
        status_code=http_status,
        detail={
            "code": e.code,
            "message": e.message,
            "details": e.details
        }
    )


# ============================================================================
# COMPLAINTS - CRUD
# ============================================================================

@router.get("", response_model=dict)
async def list_complaints(
    query: str | None = None,
    status: list[ComplaintStatus] | None = Query(None),
    priority: list[ComplaintPriority] | None = Query(None),
    category: list[ComplaintCategory] | None = Query(None),
    channel: list[ComplaintChannel] | None = Query(None),
    team_id: UUID | None = None,
    assigned_to_id: UUID | None = None,
    customer_id: UUID | None = None,
    customer_email: str | None = None,
    sla_breached: bool | None = None,
    sla_at_risk: bool | None = None,
    escalated: bool | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: ComplaintService = Depends(get_service)
):
    """Liste des reclamations avec filtres."""
    filters = ComplaintFilter(
        query=query,
        status=status,
        priority=priority,
        category=category,
        channel=channel,
        team_id=team_id,
        assigned_to_id=assigned_to_id,
        customer_id=customer_id,
        customer_email=customer_email,
        sla_breached=sla_breached,
        sla_at_risk=sla_at_risk,
        escalated=escalated,
        date_from=date_from,
        date_to=date_to
    )

    complaints, total = service.search_complaints(filters, skip, limit)

    return {
        "items": [ComplaintSummary.model_validate(c) for c in complaints],
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + limit < total
    }


@router.get("/{complaint_id}", response_model=ComplaintDetail)
async def get_complaint(
    complaint_id: UUID,
    service: ComplaintService = Depends(get_service)
):
    """Recupere une reclamation avec ses details."""
    try:
        return service.get_complaint_detail(complaint_id)
    except ComplaintNotFoundError as e:
        handle_exception(e)


@router.get("/reference/{reference}", response_model=ComplaintResponse)
async def get_complaint_by_reference(
    reference: str,
    service: ComplaintService = Depends(get_service)
):
    """Recupere une reclamation par reference."""
    try:
        return service.get_complaint_by_reference(reference)
    except ComplaintNotFoundError as e:
        handle_exception(e)


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def create_complaint(
    data: ComplaintCreate,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_service)
):
    """Cree une nouvelle reclamation."""
    try:
        return service.create_complaint(
            data,
            created_by=current_user.id,
            created_by_name=current_user.full_name
        )
    except CustomerInfoRequiredError as e:
        handle_exception(e)


@router.put("/{complaint_id}", response_model=ComplaintResponse)
async def update_complaint(
    complaint_id: UUID,
    data: ComplaintUpdate,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_service)
):
    """Met a jour une reclamation."""
    try:
        return service.update_complaint(
            complaint_id,
            data,
            updated_by=current_user.id,
            updated_by_name=current_user.full_name
        )
    except ComplaintException as e:
        handle_exception(e)


@router.delete("/{complaint_id}")
async def delete_complaint(
    complaint_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_service)
):
    """Supprime une reclamation (soft delete)."""
    try:
        service.delete_complaint(
            complaint_id,
            deleted_by=current_user.id,
            deleted_by_name=current_user.full_name
        )
        return {"status": "deleted"}
    except ComplaintNotFoundError as e:
        handle_exception(e)


# ============================================================================
# WORKFLOW
# ============================================================================

@router.post("/{complaint_id}/acknowledge", response_model=ComplaintResponse)
async def acknowledge_complaint(
    complaint_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_service)
):
    """Accuse reception d'une reclamation."""
    try:
        return service.acknowledge_complaint(
            complaint_id,
            acknowledged_by=current_user.id,
            acknowledged_by_name=current_user.full_name
        )
    except ComplaintException as e:
        handle_exception(e)


@router.post("/{complaint_id}/assign", response_model=ComplaintResponse)
async def assign_complaint(
    complaint_id: UUID,
    data: ComplaintAssign,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_service)
):
    """Assigne une reclamation a un agent."""
    try:
        return service.assign_complaint(
            complaint_id,
            data,
            assigned_by=current_user.id,
            assigned_by_name=current_user.full_name
        )
    except ComplaintException as e:
        handle_exception(e)


@router.post("/{complaint_id}/status", response_model=ComplaintResponse)
async def change_status(
    complaint_id: UUID,
    data: ComplaintStatusChange,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_service)
):
    """Change le statut d'une reclamation."""
    try:
        return service.change_status(
            complaint_id,
            data,
            changed_by=current_user.id,
            changed_by_name=current_user.full_name
        )
    except ComplaintException as e:
        handle_exception(e)


@router.post("/{complaint_id}/escalate", response_model=ComplaintResponse)
async def escalate_complaint(
    complaint_id: UUID,
    data: ComplaintEscalate,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_service)
):
    """Escalade une reclamation."""
    try:
        return service.escalate_complaint(
            complaint_id,
            data,
            escalated_by=current_user.id,
            escalated_by_name=current_user.full_name
        )
    except ComplaintException as e:
        handle_exception(e)


@router.post("/{complaint_id}/resolve", response_model=ComplaintResponse)
async def resolve_complaint(
    complaint_id: UUID,
    data: ComplaintResolve,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_service)
):
    """Resout une reclamation."""
    try:
        return service.resolve_complaint(
            complaint_id,
            data,
            resolved_by=current_user.id,
            resolved_by_name=current_user.full_name
        )
    except ComplaintException as e:
        handle_exception(e)


@router.post("/{complaint_id}/close", response_model=ComplaintResponse)
async def close_complaint(
    complaint_id: UUID,
    data: ComplaintClose,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_service)
):
    """Cloture une reclamation."""
    try:
        return service.close_complaint(
            complaint_id,
            data,
            closed_by=current_user.id,
            closed_by_name=current_user.full_name
        )
    except ComplaintException as e:
        handle_exception(e)


@router.post("/{complaint_id}/reopen", response_model=ComplaintResponse)
async def reopen_complaint(
    complaint_id: UUID,
    data: ComplaintReopen,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_service)
):
    """Reouvre une reclamation."""
    try:
        return service.reopen_complaint(
            complaint_id,
            data,
            reopened_by=current_user.id,
            reopened_by_name=current_user.full_name
        )
    except ComplaintException as e:
        handle_exception(e)


# ============================================================================
# EXCHANGES
# ============================================================================

@router.get("/{complaint_id}/exchanges", response_model=list[ExchangeResponse])
async def list_exchanges(
    complaint_id: UUID,
    include_internal: bool = True,
    service: ComplaintService = Depends(get_service)
):
    """Liste les echanges d'une reclamation."""
    return service.get_exchanges(complaint_id, include_internal)


@router.post("/{complaint_id}/exchanges", response_model=ExchangeResponse, status_code=status.HTTP_201_CREATED)
async def add_exchange(
    complaint_id: UUID,
    data: ExchangeCreate,
    author_type: str = Query("agent", pattern="^(agent|customer|system)$"),
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_service)
):
    """Ajoute un echange a une reclamation."""
    try:
        return service.add_exchange(
            complaint_id,
            data,
            author_type=author_type,
            author_id=current_user.id,
            author_name=current_user.full_name,
            author_email=current_user.email
        )
    except ComplaintNotFoundError as e:
        handle_exception(e)


# ============================================================================
# ATTACHMENTS
# ============================================================================

@router.get("/{complaint_id}/attachments", response_model=list[AttachmentResponse])
async def list_attachments(
    complaint_id: UUID,
    service: ComplaintService = Depends(get_service)
):
    """Liste les pieces jointes d'une reclamation."""
    return service.get_attachments(complaint_id)


@router.post("/{complaint_id}/attachments", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def add_attachment(
    complaint_id: UUID,
    data: AttachmentCreate,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_service)
):
    """Ajoute une piece jointe."""
    try:
        return service.add_attachment(
            complaint_id,
            data,
            uploaded_by_id=current_user.id,
            uploaded_by_name=current_user.full_name
        )
    except ComplaintNotFoundError as e:
        handle_exception(e)


# ============================================================================
# ACTIONS
# ============================================================================

@router.get("/{complaint_id}/actions", response_model=list[ActionResponse])
async def list_actions(
    complaint_id: UUID,
    service: ComplaintService = Depends(get_service)
):
    """Liste les actions d'une reclamation."""
    return service.get_actions(complaint_id)


@router.post("/{complaint_id}/actions", response_model=ActionResponse, status_code=status.HTTP_201_CREATED)
async def create_action(
    complaint_id: UUID,
    data: ActionCreate,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_service)
):
    """Cree une action corrective."""
    try:
        return service.create_action(complaint_id, data, created_by=current_user.id)
    except ComplaintNotFoundError as e:
        handle_exception(e)


@router.put("/actions/{action_id}", response_model=ActionResponse)
async def update_action(
    action_id: UUID,
    data: ActionUpdate,
    service: ComplaintService = Depends(get_service)
):
    """Met a jour une action."""
    try:
        return service.update_action(action_id, data)
    except ComplaintException as e:
        handle_exception(e)


@router.post("/actions/{action_id}/complete", response_model=ActionResponse)
async def complete_action(
    action_id: UUID,
    data: ActionComplete,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_service)
):
    """Complete une action."""
    try:
        return service.complete_action(action_id, data, completed_by=current_user.id)
    except ComplaintException as e:
        handle_exception(e)


# ============================================================================
# HISTORY
# ============================================================================

@router.get("/{complaint_id}/history", response_model=list[HistoryResponse])
async def get_history(
    complaint_id: UUID,
    service: ComplaintService = Depends(get_service)
):
    """Recupere l'historique d'une reclamation."""
    return service.get_history(complaint_id)


# ============================================================================
# ESCALATIONS
# ============================================================================

@router.get("/{complaint_id}/escalations", response_model=list[EscalationResponse])
async def get_escalations(
    complaint_id: UUID,
    service: ComplaintService = Depends(get_service)
):
    """Recupere les escalades d'une reclamation."""
    complaint = service.get_complaint_detail(complaint_id)
    return complaint.escalations


# ============================================================================
# SATISFACTION
# ============================================================================

@router.post("/{complaint_id}/satisfaction", response_model=ComplaintResponse)
async def submit_satisfaction(
    complaint_id: UUID,
    data: SatisfactionSubmit,
    service: ComplaintService = Depends(get_service)
):
    """Enregistre la satisfaction client."""
    try:
        return service.submit_satisfaction(complaint_id, data)
    except ComplaintNotFoundError as e:
        handle_exception(e)


# ============================================================================
# TEAMS
# ============================================================================

@router.get("/config/teams", response_model=list[TeamResponse])
async def list_teams(
    active_only: bool = True,
    service: ComplaintService = Depends(get_service)
):
    """Liste les equipes."""
    return service.get_teams(active_only)


@router.get("/config/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: UUID,
    service: ComplaintService = Depends(get_service)
):
    """Recupere une equipe."""
    team = service.teams.get_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipe non trouvee")
    return team


@router.post("/config/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    data: TeamCreate,
    service: ComplaintService = Depends(get_service)
):
    """Cree une equipe."""
    return service.create_team(data)


@router.put("/config/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: UUID,
    data: TeamUpdate,
    service: ComplaintService = Depends(get_service)
):
    """Met a jour une equipe."""
    try:
        return service.update_team(team_id, data)
    except TeamNotFoundError as e:
        handle_exception(e)


# ============================================================================
# AGENTS
# ============================================================================

@router.get("/config/agents", response_model=list[AgentResponse])
async def list_agents(
    team_id: UUID | None = None,
    available_only: bool = False,
    service: ComplaintService = Depends(get_service)
):
    """Liste les agents."""
    return service.get_agents(team_id, available_only)


@router.get("/config/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    service: ComplaintService = Depends(get_service)
):
    """Recupere un agent."""
    agent = service.agents.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent non trouve")
    return agent


@router.post("/config/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    data: AgentCreate,
    service: ComplaintService = Depends(get_service)
):
    """Cree un agent."""
    return service.create_agent(data)


@router.put("/config/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    data: AgentUpdate,
    service: ComplaintService = Depends(get_service)
):
    """Met a jour un agent."""
    try:
        return service.update_agent(agent_id, data)
    except AgentNotFoundError as e:
        handle_exception(e)


# ============================================================================
# SLA POLICIES
# ============================================================================

@router.get("/config/sla-policies", response_model=list[SLAPolicyResponse])
async def list_sla_policies(
    active_only: bool = True,
    service: ComplaintService = Depends(get_service)
):
    """Liste les politiques SLA."""
    return service.get_sla_policies(active_only)


@router.get("/config/sla-policies/{sla_id}", response_model=SLAPolicyResponse)
async def get_sla_policy(
    sla_id: UUID,
    service: ComplaintService = Depends(get_service)
):
    """Recupere une politique SLA."""
    policy = service.sla_policies.get_by_id(sla_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Politique SLA non trouvee")
    return policy


@router.post("/config/sla-policies", response_model=SLAPolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_sla_policy(
    data: SLAPolicyCreate,
    service: ComplaintService = Depends(get_service)
):
    """Cree une politique SLA."""
    return service.create_sla_policy(data)


@router.put("/config/sla-policies/{sla_id}", response_model=SLAPolicyResponse)
async def update_sla_policy(
    sla_id: UUID,
    data: SLAPolicyUpdate,
    service: ComplaintService = Depends(get_service)
):
    """Met a jour une politique SLA."""
    try:
        return service.update_sla_policy(sla_id, data)
    except SLAPolicyNotFoundError as e:
        handle_exception(e)


# ============================================================================
# CATEGORIES
# ============================================================================

@router.get("/config/categories", response_model=list[CategoryConfigResponse])
async def list_categories(
    active_only: bool = True,
    public_only: bool = False,
    service: ComplaintService = Depends(get_service)
):
    """Liste les categories."""
    return service.get_categories(active_only, public_only)


@router.get("/config/categories/{category_id}", response_model=CategoryConfigResponse)
async def get_category(
    category_id: UUID,
    service: ComplaintService = Depends(get_service)
):
    """Recupere une categorie."""
    category = service.categories.get_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categorie non trouvee")
    return category


@router.post("/config/categories", response_model=CategoryConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryConfigCreate,
    service: ComplaintService = Depends(get_service)
):
    """Cree une categorie."""
    try:
        return service.create_category(data)
    except DuplicateCodeError as e:
        handle_exception(e)


@router.put("/config/categories/{category_id}", response_model=CategoryConfigResponse)
async def update_category(
    category_id: UUID,
    data: CategoryConfigUpdate,
    service: ComplaintService = Depends(get_service)
):
    """Met a jour une categorie."""
    try:
        return service.update_category(category_id, data)
    except CategoryNotFoundError as e:
        handle_exception(e)


# ============================================================================
# TEMPLATES
# ============================================================================

@router.get("/config/templates", response_model=list[TemplateResponse])
async def list_templates(
    category: ComplaintCategory | None = None,
    template_type: str | None = None,
    team_id: UUID | None = None,
    search: str | None = None,
    service: ComplaintService = Depends(get_service)
):
    """Liste les modeles de reponse."""
    return service.get_templates(category, template_type, team_id, search)


@router.get("/config/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: UUID,
    service: ComplaintService = Depends(get_service)
):
    """Recupere un modele."""
    template = service.templates.get_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Modele non trouve")
    return template


@router.post("/config/templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: TemplateCreate,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_service)
):
    """Cree un modele de reponse."""
    try:
        return service.create_template(data, owner_id=current_user.id)
    except DuplicateCodeError as e:
        handle_exception(e)


@router.put("/config/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    data: TemplateUpdate,
    service: ComplaintService = Depends(get_service)
):
    """Met a jour un modele."""
    template = service.templates.get_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Modele non trouve")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(template, field):
            setattr(template, field, value)

    return service.templates.update(template)


@router.post("/config/templates/{template_id}/render", response_model=TemplateRendered)
async def render_template(
    template_id: UUID,
    data: TemplateRender,
    service: ComplaintService = Depends(get_service)
):
    """Rend un modele avec les variables."""
    try:
        result = service.render_template(template_id, data)
        return TemplateRendered(**result)
    except (TemplateNotFoundError, TemplateVariableError) as e:
        handle_exception(e)


# ============================================================================
# AUTOMATION RULES
# ============================================================================

@router.get("/config/automation-rules", response_model=list[AutomationRuleResponse])
async def list_automation_rules(
    active_only: bool = True,
    service: ComplaintService = Depends(get_service)
):
    """Liste les regles d'automatisation."""
    return service.get_automation_rules(active_only)


@router.get("/config/automation-rules/{rule_id}", response_model=AutomationRuleResponse)
async def get_automation_rule(
    rule_id: UUID,
    service: ComplaintService = Depends(get_service)
):
    """Recupere une regle d'automatisation."""
    rule = service.automation_rules.get_by_id(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Regle non trouvee")
    return rule


@router.post("/config/automation-rules", response_model=AutomationRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_automation_rule(
    data: AutomationRuleCreate,
    service: ComplaintService = Depends(get_service)
):
    """Cree une regle d'automatisation."""
    return service.create_automation_rule(data)


@router.put("/config/automation-rules/{rule_id}", response_model=AutomationRuleResponse)
async def update_automation_rule(
    rule_id: UUID,
    data: AutomationRuleUpdate,
    service: ComplaintService = Depends(get_service)
):
    """Met a jour une regle d'automatisation."""
    rule = service.automation_rules.get_by_id(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Regle non trouvee")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(rule, field):
            setattr(rule, field, value)

    return service.automation_rules.update(rule)


# ============================================================================
# STATISTICS & DASHBOARD
# ============================================================================

@router.get("/stats", response_model=ComplaintStats)
async def get_stats(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    team_id: UUID | None = None,
    agent_id: UUID | None = None,
    service: ComplaintService = Depends(get_service)
):
    """Statistiques des reclamations."""
    return service.get_stats(date_from, date_to, team_id, agent_id)


@router.get("/dashboard", response_model=ComplaintDashboard)
async def get_dashboard(
    days: int = Query(30, ge=1, le=365),
    service: ComplaintService = Depends(get_service)
):
    """Dashboard complet des reclamations."""
    return service.get_dashboard(days)


# ============================================================================
# SLA MANAGEMENT
# ============================================================================

@router.post("/sla/check-breaches")
async def check_sla_breaches(
    service: ComplaintService = Depends(get_service)
):
    """Verifie et marque les depassements SLA (tache planifiee)."""
    complaints = service.check_sla_breaches()
    return {
        "status": "completed",
        "breaches_detected": len(complaints),
        "complaint_ids": [str(c.id) for c in complaints]
    }


@router.post("/sla/process-escalations")
async def process_auto_escalations(
    service: ComplaintService = Depends(get_service)
):
    """Traite les escalades automatiques (tache planifiee)."""
    complaints = service.process_auto_escalations()
    return {
        "status": "completed",
        "escalations_processed": len(complaints),
        "complaint_ids": [str(c.id) for c in complaints]
    }


# ============================================================================
# BULK OPERATIONS
# ============================================================================

@router.post("/bulk/assign")
async def bulk_assign(
    complaint_ids: list[UUID],
    agent_id: UUID,
    team_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_service)
):
    """Assigne plusieurs reclamations a un agent."""
    results = {"success": [], "errors": []}

    for complaint_id in complaint_ids:
        try:
            service.assign_complaint(
                complaint_id,
                ComplaintAssign(agent_id=agent_id, team_id=team_id),
                assigned_by=current_user.id,
                assigned_by_name=current_user.full_name
            )
            results["success"].append(str(complaint_id))
        except Exception as e:
            results["errors"].append({
                "complaint_id": str(complaint_id),
                "error": str(e)
            })

    return results


@router.post("/bulk/status")
async def bulk_change_status(
    complaint_ids: list[UUID],
    status: ComplaintStatus,
    comment: str | None = None,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_service)
):
    """Change le statut de plusieurs reclamations."""
    results = {"success": [], "errors": []}

    for complaint_id in complaint_ids:
        try:
            service.change_status(
                complaint_id,
                ComplaintStatusChange(status=status, comment=comment),
                changed_by=current_user.id,
                changed_by_name=current_user.full_name
            )
            results["success"].append(str(complaint_id))
        except Exception as e:
            results["errors"].append({
                "complaint_id": str(complaint_id),
                "error": str(e)
            })

    return results
