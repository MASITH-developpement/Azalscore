"""
AZALS MODULE T6 - Router API Diffusion Périodique v2 (CORE SaaS)
=================================================================

Points d'entrée REST pour la gestion des diffusions automatiques avec SaaSContext.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext

from .models import BroadcastFrequency, BroadcastStatus, ContentType, DeliveryChannel, DeliveryStatus, RecipientType
from .schemas import (
    # Exécutions
    BroadcastExecutionResponse,
    # Métriques
    BroadcastMetricResponse,
    # Préférences
    BroadcastPreferenceCreate,
    BroadcastPreferenceResponse,
    BroadcastStatusEnum,
    # Templates
    BroadcastTemplateCreate,
    BroadcastTemplateResponse,
    BroadcastTemplateUpdate,
    # Enums
    ContentTypeEnum,
    DashboardStatsResponse,
    DeliveryStatusEnum,
    ExecuteRequest,
    PaginatedBroadcastsResponse,
    PaginatedDeliveryDetailsResponse,
    PaginatedExecutionsResponse,
    PaginatedMembersResponse,
    PaginatedRecipientListsResponse,
    PaginatedTemplatesResponse,
    # Listes
    RecipientListCreate,
    RecipientListResponse,
    RecipientMemberCreate,
    RecipientMemberResponse,
    # Broadcasts
    ScheduledBroadcastCreate,
    ScheduledBroadcastResponse,
    ScheduledBroadcastUpdate,
    UnsubscribeRequest,
)
from .service import BroadcastService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2/broadcast", tags=["Broadcast v2 - CORE SaaS"])


# ============================================================================
# SERVICE FACTORY
# ============================================================================

def get_broadcast_service(db: Session, tenant_id: str, user_id: str) -> BroadcastService:
    """Factory pour créer une instance du service avec contexte SaaS."""
    return BroadcastService(db, tenant_id, user_id)


# ============================================================================
# TEMPLATES (5 endpoints)
# ============================================================================

@router.post("/templates", response_model=BroadcastTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template: BroadcastTemplateCreate,
    context: SaaSContext = Depends(get_saas_context)
):
    """Créer un nouveau template de diffusion."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)

    # Vérifier unicité du code
    existing = service.get_template_by_code(template.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Template avec code '{template.code}' existe déjà"
        )

    return service.create_template(
        **template.model_dump(),
        created_by=int(context.user_id) if context.user_id else None
    )


@router.get("/templates", response_model=PaginatedTemplatesResponse)
async def list_templates(
    content_type: ContentTypeEnum | None = None,
    is_active: bool | None = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    context: SaaSContext = Depends(get_saas_context)
):
    """Lister les templates de diffusion."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    items, total = service.list_templates(
        content_type=ContentType(content_type.value) if content_type else None,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/templates/{template_id}", response_model=BroadcastTemplateResponse)
async def get_template(
    template_id: int,
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer un template par ID."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return template


@router.put("/templates/{template_id}", response_model=BroadcastTemplateResponse)
async def update_template(
    template_id: int,
    updates: BroadcastTemplateUpdate,
    context: SaaSContext = Depends(get_saas_context)
):
    """Mettre à jour un template."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    template = service.update_template(template_id, **updates.model_dump(exclude_unset=True))
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    context: SaaSContext = Depends(get_saas_context)
):
    """Supprimer un template."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    if not service.delete_template(template_id):
        raise HTTPException(status_code=404, detail="Template non trouvé ou système")


# ============================================================================
# LISTES DE DESTINATAIRES (6 endpoints)
# ============================================================================

@router.post("/recipient-lists", response_model=RecipientListResponse, status_code=status.HTTP_201_CREATED)
async def create_recipient_list(
    recipient_list: RecipientListCreate,
    context: SaaSContext = Depends(get_saas_context)
):
    """Créer une nouvelle liste de destinataires."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    return service.create_recipient_list(
        **recipient_list.model_dump(),
        created_by=int(context.user_id) if context.user_id else None
    )


@router.get("/recipient-lists", response_model=PaginatedRecipientListsResponse)
async def list_recipient_lists(
    is_active: bool | None = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    context: SaaSContext = Depends(get_saas_context)
):
    """Lister les listes de destinataires."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    items, total = service.list_recipient_lists(is_active=is_active, skip=skip, limit=limit)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/recipient-lists/{list_id}", response_model=RecipientListResponse)
async def get_recipient_list(
    list_id: int,
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer une liste par ID."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    recipient_list = service.get_recipient_list(list_id)
    if not recipient_list:
        raise HTTPException(status_code=404, detail="Liste non trouvée")
    return recipient_list


@router.post("/recipient-lists/{list_id}/members", response_model=RecipientMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    list_id: int,
    member: RecipientMemberCreate,
    context: SaaSContext = Depends(get_saas_context)
):
    """Ajouter un membre à une liste."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)

    # Vérifier que la liste existe
    recipient_list = service.get_recipient_list(list_id)
    if not recipient_list:
        raise HTTPException(status_code=404, detail="Liste non trouvée")

    return service.add_member_to_list(
        list_id=list_id,
        recipient_type=RecipientType(member.recipient_type.value),
        user_id=member.user_id,
        group_id=member.group_id,
        role_code=member.role_code,
        external_email=member.external_email,
        external_name=member.external_name,
        preferred_channel=DeliveryChannel(member.preferred_channel.value) if member.preferred_channel else None,
        added_by=int(context.user_id) if context.user_id else None
    )


@router.get("/recipient-lists/{list_id}/members", response_model=PaginatedMembersResponse)
async def list_members(
    list_id: int,
    is_active: bool | None = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer les membres d'une liste."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    items, total = service.get_list_members(list_id, is_active=is_active, skip=skip, limit=limit)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.delete("/recipient-lists/{list_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(
    list_id: int,
    member_id: int,
    context: SaaSContext = Depends(get_saas_context)
):
    """Retirer un membre d'une liste."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    if not service.remove_member_from_list(member_id):
        raise HTTPException(status_code=404, detail="Membre non trouvé")


# ============================================================================
# DIFFUSIONS PROGRAMMÉES (8 endpoints)
# ============================================================================

@router.post("/scheduled", response_model=ScheduledBroadcastResponse, status_code=status.HTTP_201_CREATED)
async def create_scheduled_broadcast(
    broadcast: ScheduledBroadcastCreate,
    context: SaaSContext = Depends(get_saas_context)
):
    """Créer une nouvelle diffusion programmée."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    return service.create_scheduled_broadcast(
        code=broadcast.code,
        name=broadcast.name,
        content_type=ContentType(broadcast.content_type.value),
        frequency=BroadcastFrequency(broadcast.frequency.value),
        delivery_channel=DeliveryChannel(broadcast.delivery_channel.value),
        template_id=broadcast.template_id,
        recipient_list_id=broadcast.recipient_list_id,
        subject=broadcast.subject,
        body_content=broadcast.body_content,
        html_content=broadcast.html_content,
        cron_expression=broadcast.cron_expression,
        timezone=broadcast.timezone,
        start_date=broadcast.start_date,
        end_date=broadcast.end_date,
        send_time=broadcast.send_time,
        day_of_week=broadcast.day_of_week,
        day_of_month=broadcast.day_of_month,
        data_query=broadcast.data_query,
        created_by=int(context.user_id) if context.user_id else None
    )


@router.get("/scheduled", response_model=PaginatedBroadcastsResponse)
async def list_scheduled_broadcasts(
    status: BroadcastStatusEnum | None = None,
    frequency: str | None = None,
    is_active: bool | None = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    context: SaaSContext = Depends(get_saas_context)
):
    """Lister les diffusions programmées."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    items, total = service.list_scheduled_broadcasts(
        status=BroadcastStatus(status.value) if status else None,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/scheduled/{broadcast_id}", response_model=ScheduledBroadcastResponse)
async def get_scheduled_broadcast(
    broadcast_id: int,
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer une diffusion programmée par ID."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    broadcast = service.get_scheduled_broadcast(broadcast_id)
    if not broadcast:
        raise HTTPException(status_code=404, detail="Diffusion non trouvée")
    return broadcast


@router.put("/scheduled/{broadcast_id}", response_model=ScheduledBroadcastResponse)
async def update_scheduled_broadcast(
    broadcast_id: int,
    updates: ScheduledBroadcastUpdate,
    context: SaaSContext = Depends(get_saas_context)
):
    """Mettre à jour une diffusion programmée."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)

    update_dict = updates.model_dump(exclude_unset=True)

    # Convertir les enums si présents
    if "delivery_channel" in update_dict and update_dict["delivery_channel"]:
        update_dict["delivery_channel"] = DeliveryChannel(update_dict["delivery_channel"].value)
    if "frequency" in update_dict and update_dict["frequency"]:
        update_dict["frequency"] = BroadcastFrequency(update_dict["frequency"].value)

    broadcast = service.update_scheduled_broadcast(broadcast_id, **update_dict)
    if not broadcast:
        raise HTTPException(status_code=404, detail="Diffusion non trouvée")
    return broadcast


@router.post("/scheduled/{broadcast_id}/activate", response_model=ScheduledBroadcastResponse)
async def activate_broadcast(
    broadcast_id: int,
    context: SaaSContext = Depends(get_saas_context)
):
    """Activer une diffusion programmée."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    broadcast = service.activate_broadcast(broadcast_id)
    if not broadcast:
        raise HTTPException(status_code=404, detail="Diffusion non trouvée")
    return broadcast


@router.post("/scheduled/{broadcast_id}/pause", response_model=ScheduledBroadcastResponse)
async def pause_broadcast(
    broadcast_id: int,
    context: SaaSContext = Depends(get_saas_context)
):
    """Mettre en pause une diffusion."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    broadcast = service.pause_broadcast(broadcast_id)
    if not broadcast:
        raise HTTPException(status_code=404, detail="Diffusion non trouvée")
    return broadcast


@router.post("/scheduled/{broadcast_id}/cancel", response_model=ScheduledBroadcastResponse)
async def cancel_broadcast(
    broadcast_id: int,
    context: SaaSContext = Depends(get_saas_context)
):
    """Annuler une diffusion."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    broadcast = service.cancel_broadcast(broadcast_id)
    if not broadcast:
        raise HTTPException(status_code=404, detail="Diffusion non trouvée")
    return broadcast


@router.post("/scheduled/{broadcast_id}/execute", response_model=BroadcastExecutionResponse)
async def execute_broadcast_now(
    broadcast_id: int,
    request: ExecuteRequest,
    context: SaaSContext = Depends(get_saas_context)
):
    """Exécuter une diffusion manuellement."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    try:
        return service.execute_broadcast(
            broadcast_id,
            triggered_by=request.triggered_by,
            triggered_user=int(context.user_id) if context.user_id else None
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# EXÉCUTIONS (3 endpoints)
# ============================================================================

@router.get("/executions", response_model=PaginatedExecutionsResponse)
async def list_executions(
    broadcast_id: int | None = None,
    status: DeliveryStatusEnum | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    context: SaaSContext = Depends(get_saas_context)
):
    """Lister les exécutions de diffusion."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    items, total = service.list_executions(
        broadcast_id=broadcast_id,
        status=DeliveryStatus(status.value) if status else None,
        skip=skip,
        limit=limit
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/executions/{execution_id}", response_model=BroadcastExecutionResponse)
async def get_execution(
    execution_id: int,
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer une exécution par ID."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    execution = service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Exécution non trouvée")
    return execution


@router.get("/executions/{execution_id}/details", response_model=PaginatedDeliveryDetailsResponse)
async def get_execution_details(
    execution_id: int,
    status: DeliveryStatusEnum | None = None,
    channel: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer les détails de livraison d'une exécution."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    items, total = service.get_delivery_details(
        execution_id,
        status=DeliveryStatus(status.value) if status else None,
        skip=skip,
        limit=limit
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}


# ============================================================================
# PRÉFÉRENCES UTILISATEUR (2 endpoints)
# ============================================================================

@router.get("/preferences", response_model=BroadcastPreferenceResponse)
async def get_preferences(
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer mes préférences de diffusion."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    prefs = service.get_user_preferences(int(context.user_id))
    if not prefs:
        # Créer des préférences par défaut
        prefs = service.set_user_preferences(int(context.user_id))
    return prefs


@router.put("/preferences", response_model=BroadcastPreferenceResponse)
async def update_preferences(
    preferences: BroadcastPreferenceCreate,
    context: SaaSContext = Depends(get_saas_context)
):
    """Mettre à jour mes préférences de diffusion."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)

    pref_dict = preferences.model_dump()
    # Convertir les enums
    if pref_dict.get("preferred_channel"):
        pref_dict["preferred_channel"] = DeliveryChannel(pref_dict["preferred_channel"].value)
    if pref_dict.get("digest_frequency"):
        pref_dict["digest_frequency"] = BroadcastFrequency(pref_dict["digest_frequency"].value)
    if pref_dict.get("report_frequency"):
        pref_dict["report_frequency"] = BroadcastFrequency(pref_dict["report_frequency"].value)

    return service.set_user_preferences(int(context.user_id), **pref_dict)


# ============================================================================
# UNSUBSCRIBE (1 endpoint)
# ============================================================================

@router.post("/unsubscribe", status_code=status.HTTP_200_OK)
async def unsubscribe_from_broadcast(
    request: UnsubscribeRequest,
    context: SaaSContext = Depends(get_saas_context)
):
    """Se désabonner d'une diffusion ou de toutes."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    service.unsubscribe_user(int(context.user_id), request.broadcast_id)
    return {"message": "Désabonnement effectué"}


# ============================================================================
# MÉTRIQUES (2 endpoints)
# ============================================================================

@router.get("/metrics", response_model=list[BroadcastMetricResponse])
async def list_metrics(
    period_type: str = Query("DAILY", pattern="^(DAILY|WEEKLY|MONTHLY)$"),
    limit: int = Query(30, ge=1, le=365),
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer les métriques de diffusion."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    return service.get_metrics(period_type=period_type, limit=limit)


@router.post("/metrics/record", response_model=BroadcastMetricResponse)
async def record_metric(
    period_type: str = Query("DAILY", pattern="^(DAILY|WEEKLY|MONTHLY)$"),
    context: SaaSContext = Depends(get_saas_context)
):
    """Enregistrer les métriques actuelles."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    return service.record_metrics(period_type=period_type)


# ============================================================================
# DASHBOARD & PROCESSING (3 endpoints)
# ============================================================================

@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer les statistiques pour le dashboard."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    return service.get_dashboard_stats()


@router.get("/due", response_model=list[ScheduledBroadcastResponse])
async def get_due_broadcasts(
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer les diffusions à exécuter maintenant."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    return service.get_broadcasts_due()


@router.post("/process-due", response_model=list[BroadcastExecutionResponse])
async def process_due_broadcasts(
    context: SaaSContext = Depends(get_saas_context)
):
    """Traiter toutes les diffusions en attente."""
    service = get_broadcast_service(context.db, context.tenant_id, context.user_id)
    due_broadcasts = service.get_broadcasts_due()
    executions = []

    for broadcast in due_broadcasts:
        try:
            execution = service.execute_broadcast(
                broadcast.id,
                triggered_by="scheduler",
                triggered_user=int(context.user_id) if context.user_id else None
            )
            executions.append(execution)
        except Exception as e:
            logger.error("Failed to execute broadcast %s: %s", broadcast.id, e)
            # Continue with other broadcasts

    return executions
