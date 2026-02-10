"""
AZALS MODULE 16 - Helpdesk Router v2
=====================================
API endpoints pour le système de support client - CORE SaaS v2.
Migration complète avec SaaSContext.
"""


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext

from .models import AgentStatus, TicketPriority, TicketStatus
from .schemas import (
    AgentCreate,
    AgentResponse,
    AgentStatusUpdate,
    AgentUpdate,
    AttachmentCreate,
    AttachmentResponse,
    AutomationCreate,
    AutomationResponse,
    AutomationUpdate,
    CannedResponseCreate,
    CannedResponseResponse,
    CannedResponseUpdate,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    HelpdeskDashboard,
    HistoryResponse,
    KBArticleCreate,
    KBArticleResponse,
    KBArticleUpdate,
    KBCategoryCreate,
    KBCategoryResponse,
    KBCategoryUpdate,
    ReplyCreate,
    ReplyResponse,
    SatisfactionCreate,
    SatisfactionResponse,
    SLACreate,
    SLAResponse,
    SLAUpdate,
    TeamCreate,
    TeamResponse,
    TeamUpdate,
    TicketAssign,
    TicketCreate,
    TicketResponse,
    TicketStats,
    TicketStatusChange,
    TicketUpdate,
)
from .service import HelpdeskService

router = APIRouter(prefix="/v2/helpdesk", tags=["Helpdesk v2 - CORE SaaS"])


def get_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
) -> HelpdeskService:
    """Factory service avec SaaSContext pour CORE SaaS v2."""
    return HelpdeskService(db, context.tenant_id, context.user_id)


# ============================================================================
# CATEGORIES
# ============================================================================

@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    active_only: bool = True,
    public_only: bool = False,
    parent_id: int | None = None,
    service: HelpdeskService = Depends(get_service)
):
    """Liste des catégories de tickets."""
    return service.list_categories(active_only, public_only, parent_id)


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    service: HelpdeskService = Depends(get_service)
):
    """Récupère une catégorie."""
    category = service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return category


@router.post("/categories", response_model=CategoryResponse)
async def create_category(
    data: CategoryCreate,
    service: HelpdeskService = Depends(get_service)
):
    """Crée une catégorie."""
    return service.create_category(data)


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    service: HelpdeskService = Depends(get_service)
):
    """Met à jour une catégorie."""
    category = service.update_category(category_id, data)
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return category


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    service: HelpdeskService = Depends(get_service)
):
    """Supprime une catégorie."""
    if not service.delete_category(category_id):
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return {"status": "deleted"}


# ============================================================================
# TEAMS
# ============================================================================

@router.get("/teams", response_model=list[TeamResponse])
async def list_teams(
    active_only: bool = True,
    service: HelpdeskService = Depends(get_service)
):
    """Liste des équipes support."""
    return service.list_teams(active_only)


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int,
    service: HelpdeskService = Depends(get_service)
):
    """Récupère une équipe."""
    team = service.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Équipe non trouvée")
    return team


@router.post("/teams", response_model=TeamResponse)
async def create_team(
    data: TeamCreate,
    service: HelpdeskService = Depends(get_service)
):
    """Crée une équipe."""
    return service.create_team(data)


@router.put("/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    data: TeamUpdate,
    service: HelpdeskService = Depends(get_service)
):
    """Met à jour une équipe."""
    team = service.update_team(team_id, data)
    if not team:
        raise HTTPException(status_code=404, detail="Équipe non trouvée")
    return team


@router.delete("/teams/{team_id}")
async def delete_team(
    team_id: int,
    service: HelpdeskService = Depends(get_service)
):
    """Supprime une équipe."""
    if not service.delete_team(team_id):
        raise HTTPException(status_code=404, detail="Équipe non trouvée")
    return {"status": "deleted"}


# ============================================================================
# AGENTS
# ============================================================================

@router.get("/agents", response_model=list[AgentResponse])
async def list_agents(
    active_only: bool = True,
    team_id: int | None = None,
    status: AgentStatus | None = None,
    service: HelpdeskService = Depends(get_service)
):
    """Liste des agents support."""
    return service.list_agents(active_only, team_id, status)


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    service: HelpdeskService = Depends(get_service)
):
    """Récupère un agent."""
    agent = service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent non trouvé")
    return agent


@router.post("/agents", response_model=AgentResponse)
async def create_agent(
    data: AgentCreate,
    service: HelpdeskService = Depends(get_service)
):
    """Crée un agent."""
    return service.create_agent(data)


@router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    data: AgentUpdate,
    service: HelpdeskService = Depends(get_service)
):
    """Met à jour un agent."""
    agent = service.update_agent(agent_id, data)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent non trouvé")
    return agent


@router.post("/agents/{agent_id}/status", response_model=AgentResponse)
async def update_agent_status(
    agent_id: int,
    data: AgentStatusUpdate,
    service: HelpdeskService = Depends(get_service)
):
    """Met à jour le statut d'un agent."""
    agent = service.update_agent_status(agent_id, data.status)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent non trouvé")
    return agent


@router.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: int,
    service: HelpdeskService = Depends(get_service)
):
    """Supprime un agent."""
    if not service.delete_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent non trouvé")
    return {"status": "deleted"}


# ============================================================================
# SLA
# ============================================================================

@router.get("/sla", response_model=list[SLAResponse])
async def list_slas(
    active_only: bool = True,
    service: HelpdeskService = Depends(get_service)
):
    """Liste des SLAs."""
    return service.list_slas(active_only)


@router.get("/sla/{sla_id}", response_model=SLAResponse)
async def get_sla(
    sla_id: int,
    service: HelpdeskService = Depends(get_service)
):
    """Récupère un SLA."""
    sla = service.get_sla(sla_id)
    if not sla:
        raise HTTPException(status_code=404, detail="SLA non trouvé")
    return sla


@router.post("/sla", response_model=SLAResponse)
async def create_sla(
    data: SLACreate,
    service: HelpdeskService = Depends(get_service)
):
    """Crée un SLA."""
    return service.create_sla(data)


@router.put("/sla/{sla_id}", response_model=SLAResponse)
async def update_sla(
    sla_id: int,
    data: SLAUpdate,
    service: HelpdeskService = Depends(get_service)
):
    """Met à jour un SLA."""
    sla = service.update_sla(sla_id, data)
    if not sla:
        raise HTTPException(status_code=404, detail="SLA non trouvé")
    return sla


@router.delete("/sla/{sla_id}")
async def delete_sla(
    sla_id: int,
    service: HelpdeskService = Depends(get_service)
):
    """Supprime un SLA."""
    if not service.delete_sla(sla_id):
        raise HTTPException(status_code=404, detail="SLA non trouvé")
    return {"status": "deleted"}


# ============================================================================
# TICKETS
# ============================================================================

@router.get("/tickets")
async def list_tickets(
    status: TicketStatus | None = None,
    priority: TicketPriority | None = None,
    category_id: int | None = None,
    team_id: int | None = None,
    assigned_to_id: int | None = None,
    requester_id: int | None = None,
    requester_email: str | None = None,
    overdue_only: bool = False,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: HelpdeskService = Depends(get_service)
):
    """Liste des tickets avec filtres."""
    tickets, total = service.list_tickets(
        status=status,
        priority=priority,
        category_id=category_id,
        team_id=team_id,
        assigned_to_id=assigned_to_id,
        requester_id=requester_id,
        requester_email=requester_email,
        overdue_only=overdue_only,
        search=search,
        skip=skip,
        limit=limit
    )
    return {
        "items": tickets,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    service: HelpdeskService = Depends(get_service)
):
    """Récupère un ticket."""
    ticket = service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    return ticket


@router.get("/tickets/number/{ticket_number}", response_model=TicketResponse)
async def get_ticket_by_number(
    ticket_number: str,
    service: HelpdeskService = Depends(get_service)
):
    """Récupère un ticket par numéro."""
    ticket = service.get_ticket_by_number(ticket_number)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    return ticket


@router.post("/tickets", response_model=TicketResponse)
async def create_ticket(
    data: TicketCreate,
    service: HelpdeskService = Depends(get_service)
):
    """Crée un ticket."""
    return service.create_ticket(data)


@router.put("/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    data: TicketUpdate,
    service: HelpdeskService = Depends(get_service)
):
    """Met à jour un ticket."""
    ticket = service.update_ticket(ticket_id, data)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    return ticket


@router.post("/tickets/{ticket_id}/assign", response_model=TicketResponse)
async def assign_ticket(
    ticket_id: int,
    data: TicketAssign,
    service: HelpdeskService = Depends(get_service)
):
    """Assigne un ticket à un agent."""
    ticket = service.assign_ticket(ticket_id, data.agent_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket ou agent non trouvé")
    return ticket


@router.post("/tickets/{ticket_id}/status", response_model=TicketResponse)
async def change_ticket_status(
    ticket_id: int,
    data: TicketStatusChange,
    service: HelpdeskService = Depends(get_service)
):
    """Change le statut d'un ticket."""
    ticket = service.change_ticket_status(
        ticket_id,
        data.status,
        comment=data.comment
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    return ticket


@router.post("/tickets/{ticket_id}/merge/{target_id}", response_model=TicketResponse)
async def merge_tickets(
    ticket_id: int,
    target_id: int,
    service: HelpdeskService = Depends(get_service)
):
    """Fusionne un ticket dans un autre."""
    ticket = service.merge_tickets(ticket_id, target_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket(s) non trouvé(s)")
    return ticket


# ============================================================================
# REPLIES
# ============================================================================

@router.get("/tickets/{ticket_id}/replies", response_model=list[ReplyResponse])
async def list_replies(
    ticket_id: int,
    include_internal: bool = True,
    service: HelpdeskService = Depends(get_service)
):
    """Liste les réponses d'un ticket."""
    return service.list_replies(ticket_id, include_internal)


@router.post("/tickets/{ticket_id}/replies", response_model=ReplyResponse)
async def add_reply(
    ticket_id: int,
    data: ReplyCreate,
    author_type: str = Query("agent", pattern="^(agent|customer|system)$"),
    author_id: int | None = None,
    author_name: str | None = None,
    author_email: str | None = None,
    service: HelpdeskService = Depends(get_service)
):
    """Ajoute une réponse à un ticket."""
    reply = service.add_reply(
        ticket_id,
        data,
        author_id=author_id,
        author_name=author_name,
        author_email=author_email,
        author_type=author_type
    )
    if not reply:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    return reply


# ============================================================================
# ATTACHMENTS
# ============================================================================

@router.get("/tickets/{ticket_id}/attachments", response_model=list[AttachmentResponse])
async def list_attachments(
    ticket_id: int,
    service: HelpdeskService = Depends(get_service)
):
    """Liste les pièces jointes d'un ticket."""
    return service.list_attachments(ticket_id)


@router.post("/tickets/{ticket_id}/attachments", response_model=AttachmentResponse)
async def add_attachment(
    ticket_id: int,
    data: AttachmentCreate,
    uploaded_by_id: int | None = None,
    service: HelpdeskService = Depends(get_service)
):
    """Ajoute une pièce jointe."""
    attachment = service.add_attachment(ticket_id, data, uploaded_by_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    return attachment


# ============================================================================
# HISTORY
# ============================================================================

@router.get("/tickets/{ticket_id}/history", response_model=list[HistoryResponse])
async def get_ticket_history(
    ticket_id: int,
    service: HelpdeskService = Depends(get_service)
):
    """Récupère l'historique d'un ticket."""
    return service.get_ticket_history(ticket_id)


# ============================================================================
# CANNED RESPONSES
# ============================================================================

@router.get("/canned-responses", response_model=list[CannedResponseResponse])
async def list_canned_responses(
    team_id: int | None = None,
    agent_id: int | None = None,
    category: str | None = None,
    search: str | None = None,
    service: HelpdeskService = Depends(get_service)
):
    """Liste les réponses pré-enregistrées."""
    return service.list_canned_responses(team_id, agent_id, category, search)


@router.get("/canned-responses/{response_id}", response_model=CannedResponseResponse)
async def get_canned_response(
    response_id: int,
    service: HelpdeskService = Depends(get_service)
):
    """Récupère une réponse pré-enregistrée."""
    response = service.get_canned_response(response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Réponse non trouvée")
    return response


@router.get("/canned-responses/shortcut/{shortcut}", response_model=CannedResponseResponse)
async def get_canned_by_shortcut(
    shortcut: str,
    service: HelpdeskService = Depends(get_service)
):
    """Récupère une réponse par shortcut."""
    response = service.get_canned_by_shortcut(shortcut)
    if not response:
        raise HTTPException(status_code=404, detail="Réponse non trouvée")
    return response


@router.post("/canned-responses", response_model=CannedResponseResponse)
async def create_canned_response(
    data: CannedResponseCreate,
    agent_id: int | None = None,
    service: HelpdeskService = Depends(get_service)
):
    """Crée une réponse pré-enregistrée."""
    return service.create_canned_response(data, agent_id)


@router.put("/canned-responses/{response_id}", response_model=CannedResponseResponse)
async def update_canned_response(
    response_id: int,
    data: CannedResponseUpdate,
    service: HelpdeskService = Depends(get_service)
):
    """Met à jour une réponse pré-enregistrée."""
    response = service.update_canned_response(response_id, data)
    if not response:
        raise HTTPException(status_code=404, detail="Réponse non trouvée")
    return response


@router.post("/canned-responses/{response_id}/use", response_model=CannedResponseResponse)
async def use_canned_response(
    response_id: int,
    service: HelpdeskService = Depends(get_service)
):
    """Incrémente le compteur d'utilisation."""
    response = service.use_canned_response(response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Réponse non trouvée")
    return response


@router.delete("/canned-responses/{response_id}")
async def delete_canned_response(
    response_id: int,
    service: HelpdeskService = Depends(get_service)
):
    """Supprime une réponse pré-enregistrée."""
    if not service.delete_canned_response(response_id):
        raise HTTPException(status_code=404, detail="Réponse non trouvée")
    return {"status": "deleted"}


# ============================================================================
# KNOWLEDGE BASE - CATEGORIES
# ============================================================================

@router.get("/kb/categories", response_model=list[KBCategoryResponse])
async def list_kb_categories(
    parent_id: int | None = None,
    public_only: bool = False,
    service: HelpdeskService = Depends(get_service)
):
    """Liste les catégories de la base de connaissances."""
    return service.list_kb_categories(parent_id, public_only)


@router.get("/kb/categories/{category_id}", response_model=KBCategoryResponse)
async def get_kb_category(
    category_id: int,
    service: HelpdeskService = Depends(get_service)
):
    """Récupère une catégorie KB."""
    category = service.get_kb_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return category


@router.post("/kb/categories", response_model=KBCategoryResponse)
async def create_kb_category(
    data: KBCategoryCreate,
    service: HelpdeskService = Depends(get_service)
):
    """Crée une catégorie KB."""
    return service.create_kb_category(data)


@router.put("/kb/categories/{category_id}", response_model=KBCategoryResponse)
async def update_kb_category(
    category_id: int,
    data: KBCategoryUpdate,
    service: HelpdeskService = Depends(get_service)
):
    """Met à jour une catégorie KB."""
    category = service.update_kb_category(category_id, data)
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return category


# ============================================================================
# KNOWLEDGE BASE - ARTICLES
# ============================================================================

@router.get("/kb/articles")
async def list_kb_articles(
    category_id: int | None = None,
    status: str | None = None,
    public_only: bool = False,
    featured_only: bool = False,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: HelpdeskService = Depends(get_service)
):
    """Liste les articles de la base de connaissances."""
    articles, total = service.list_kb_articles(
        category_id=category_id,
        status=status,
        public_only=public_only,
        featured_only=featured_only,
        search=search,
        skip=skip,
        limit=limit
    )
    return {
        "items": articles,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/kb/articles/{article_id}", response_model=KBArticleResponse)
async def get_kb_article(
    article_id: int,
    increment_view: bool = True,
    service: HelpdeskService = Depends(get_service)
):
    """Récupère un article KB."""
    if increment_view:
        service.view_kb_article(article_id)
    article = service.get_kb_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    return article


@router.get("/kb/articles/slug/{slug}", response_model=KBArticleResponse)
async def get_kb_article_by_slug(
    slug: str,
    increment_view: bool = True,
    service: HelpdeskService = Depends(get_service)
):
    """Récupère un article par slug."""
    article = service.get_kb_article_by_slug(slug)
    if not article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    if increment_view:
        service.view_kb_article(article.id)
    return article


@router.post("/kb/articles", response_model=KBArticleResponse)
async def create_kb_article(
    data: KBArticleCreate,
    author_id: int | None = None,
    author_name: str | None = None,
    service: HelpdeskService = Depends(get_service)
):
    """Crée un article KB."""
    return service.create_kb_article(data, author_id, author_name)


@router.put("/kb/articles/{article_id}", response_model=KBArticleResponse)
async def update_kb_article(
    article_id: int,
    data: KBArticleUpdate,
    service: HelpdeskService = Depends(get_service)
):
    """Met à jour un article KB."""
    article = service.update_kb_article(article_id, data)
    if not article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    return article


@router.post("/kb/articles/{article_id}/rate")
async def rate_kb_article(
    article_id: int,
    helpful: bool = True,
    service: HelpdeskService = Depends(get_service)
):
    """Note un article (utile/pas utile)."""
    article = service.rate_kb_article(article_id, helpful)
    if not article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    return {"status": "rated", "helpful": helpful}


# ============================================================================
# SATISFACTION
# ============================================================================

@router.post("/satisfaction", response_model=SatisfactionResponse)
async def submit_satisfaction(
    data: SatisfactionCreate,
    customer_id: int | None = None,
    service: HelpdeskService = Depends(get_service)
):
    """Soumet une enquête de satisfaction."""
    survey = service.submit_satisfaction(data, customer_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    return survey


@router.get("/satisfaction/stats")
async def get_satisfaction_stats(
    agent_id: int | None = None,
    days: int = Query(30, ge=1, le=365),
    service: HelpdeskService = Depends(get_service)
):
    """Statistiques de satisfaction."""
    return service.get_satisfaction_stats(agent_id, days)


# ============================================================================
# AUTOMATIONS
# ============================================================================

@router.get("/automations", response_model=list[AutomationResponse])
async def list_automations(
    active_only: bool = True,
    service: HelpdeskService = Depends(get_service)
):
    """Liste des automatisations."""
    return service.list_automations(active_only)


@router.get("/automations/{automation_id}", response_model=AutomationResponse)
async def get_automation(
    automation_id: int,
    service: HelpdeskService = Depends(get_service)
):
    """Récupère une automatisation."""
    automation = service.get_automation(automation_id)
    if not automation:
        raise HTTPException(status_code=404, detail="Automatisation non trouvée")
    return automation


@router.post("/automations", response_model=AutomationResponse)
async def create_automation(
    data: AutomationCreate,
    service: HelpdeskService = Depends(get_service)
):
    """Crée une automatisation."""
    return service.create_automation(data)


@router.put("/automations/{automation_id}", response_model=AutomationResponse)
async def update_automation(
    automation_id: int,
    data: AutomationUpdate,
    service: HelpdeskService = Depends(get_service)
):
    """Met à jour une automatisation."""
    automation = service.update_automation(automation_id, data)
    if not automation:
        raise HTTPException(status_code=404, detail="Automatisation non trouvée")
    return automation


@router.delete("/automations/{automation_id}")
async def delete_automation(
    automation_id: int,
    service: HelpdeskService = Depends(get_service)
):
    """Supprime une automatisation."""
    if not service.delete_automation(automation_id):
        raise HTTPException(status_code=404, detail="Automatisation non trouvée")
    return {"status": "deleted"}


# ============================================================================
# DASHBOARD & STATS
# ============================================================================

@router.get("/stats/tickets", response_model=TicketStats)
async def get_ticket_stats(
    days: int = Query(30, ge=1, le=365),
    service: HelpdeskService = Depends(get_service)
):
    """Statistiques des tickets."""
    return service.get_ticket_stats(days)


@router.get("/stats/agents")
async def get_agent_stats(
    days: int = Query(30, ge=1, le=365),
    service: HelpdeskService = Depends(get_service)
):
    """Statistiques par agent."""
    return service.get_agent_stats(days)


@router.get("/dashboard", response_model=HelpdeskDashboard)
async def get_dashboard(
    days: int = Query(30, ge=1, le=365),
    service: HelpdeskService = Depends(get_service)
):
    """Dashboard Helpdesk complet."""
    return service.get_dashboard(days)
