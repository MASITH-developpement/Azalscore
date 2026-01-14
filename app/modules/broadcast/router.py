"""
AZALS MODULE T6 - Router API Diffusion Périodique
=================================================

Points d'entrée REST pour la gestion des diffusions automatiques.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.models import User

from .service import get_broadcast_service
from .models import (
    DeliveryChannel, BroadcastFrequency, ContentType,
    BroadcastStatus, DeliveryStatus, RecipientType
)
from .schemas import (
    # Templates
    BroadcastTemplateCreate, BroadcastTemplateUpdate, BroadcastTemplateResponse,
    PaginatedTemplatesResponse,
    # Listes
    RecipientListCreate, RecipientListResponse,
    PaginatedRecipientListsResponse,
    RecipientMemberCreate, RecipientMemberResponse, PaginatedMembersResponse,
    # Broadcasts
    ScheduledBroadcastCreate, ScheduledBroadcastUpdate, ScheduledBroadcastResponse,
    PaginatedBroadcastsResponse,
    # Exécutions
    BroadcastExecutionResponse, PaginatedExecutionsResponse, ExecuteRequest,
    PaginatedDeliveryDetailsResponse,
    # Préférences
    BroadcastPreferenceCreate, BroadcastPreferenceResponse, UnsubscribeRequest,
    # Métriques
    BroadcastMetricResponse, DashboardStatsResponse,
    # Enums
    ContentTypeEnum, BroadcastStatusEnum, DeliveryStatusEnum
)

router = APIRouter(prefix="/api/v1/broadcast", tags=["Broadcast"])


# ============================================================================
# TEMPLATES
# ============================================================================

@router.post("/templates", response_model=BroadcastTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template: BroadcastTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un nouveau template de diffusion."""
    service = get_broadcast_service(db, current_user.tenant_id)

    # Vérifier unicité du code
    existing = service.get_template_by_code(template.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Template avec code '{template.code}' existe déjà"
        )

    return service.create_template(
        **template.model_dump(),
        created_by=current_user.id
    )


@router.get("/templates", response_model=PaginatedTemplatesResponse)
async def list_templates(
    content_type: Optional[ContentTypeEnum] = None,
    is_active: Optional[bool] = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les templates de diffusion."""
    service = get_broadcast_service(db, current_user.tenant_id)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un template par ID."""
    service = get_broadcast_service(db, current_user.tenant_id)
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return template


@router.put("/templates/{template_id}", response_model=BroadcastTemplateResponse)
async def update_template(
    template_id: int,
    updates: BroadcastTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un template."""
    service = get_broadcast_service(db, current_user.tenant_id)
    template = service.update_template(template_id, **updates.model_dump(exclude_unset=True))
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un template."""
    service = get_broadcast_service(db, current_user.tenant_id)
    if not service.delete_template(template_id):
        raise HTTPException(status_code=404, detail="Template non trouvé ou système")


# ============================================================================
# LISTES DE DESTINATAIRES
# ============================================================================

@router.post("/recipient-lists", response_model=RecipientListResponse, status_code=status.HTTP_201_CREATED)
async def create_recipient_list(
    recipient_list: RecipientListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une nouvelle liste de destinataires."""
    service = get_broadcast_service(db, current_user.tenant_id)
    return service.create_recipient_list(
        **recipient_list.model_dump(),
        created_by=current_user.id
    )


@router.get("/recipient-lists", response_model=PaginatedRecipientListsResponse)
async def list_recipient_lists(
    is_active: Optional[bool] = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les listes de destinataires."""
    service = get_broadcast_service(db, current_user.tenant_id)
    items, total = service.list_recipient_lists(is_active=is_active, skip=skip, limit=limit)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/recipient-lists/{list_id}", response_model=RecipientListResponse)
async def get_recipient_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une liste par ID."""
    service = get_broadcast_service(db, current_user.tenant_id)
    recipient_list = service.get_recipient_list(list_id)
    if not recipient_list:
        raise HTTPException(status_code=404, detail="Liste non trouvée")
    return recipient_list


@router.post("/recipient-lists/{list_id}/members", response_model=RecipientMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member_to_list(
    list_id: int,
    member: RecipientMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ajouter un membre à une liste."""
    service = get_broadcast_service(db, current_user.tenant_id)

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
        added_by=current_user.id
    )


@router.get("/recipient-lists/{list_id}/members", response_model=PaginatedMembersResponse)
async def get_list_members(
    list_id: int,
    is_active: Optional[bool] = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les membres d'une liste."""
    service = get_broadcast_service(db, current_user.tenant_id)
    items, total = service.get_list_members(list_id, is_active=is_active, skip=skip, limit=limit)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.delete("/recipient-lists/{list_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_from_list(
    list_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retirer un membre d'une liste."""
    service = get_broadcast_service(db, current_user.tenant_id)
    if not service.remove_member_from_list(member_id):
        raise HTTPException(status_code=404, detail="Membre non trouvé")


# ============================================================================
# DIFFUSIONS PROGRAMMÉES
# ============================================================================

@router.post("/scheduled", response_model=ScheduledBroadcastResponse, status_code=status.HTTP_201_CREATED)
async def create_scheduled_broadcast(
    broadcast: ScheduledBroadcastCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une nouvelle diffusion programmée."""
    service = get_broadcast_service(db, current_user.tenant_id)
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
        created_by=current_user.id
    )


@router.get("/scheduled", response_model=PaginatedBroadcastsResponse)
async def list_scheduled_broadcasts(
    status: Optional[BroadcastStatusEnum] = None,
    content_type: Optional[ContentTypeEnum] = None,
    is_active: Optional[bool] = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les diffusions programmées."""
    service = get_broadcast_service(db, current_user.tenant_id)
    items, total = service.list_scheduled_broadcasts(
        status=BroadcastStatus(status.value) if status else None,
        content_type=ContentType(content_type.value) if content_type else None,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/scheduled/{broadcast_id}", response_model=ScheduledBroadcastResponse)
async def get_scheduled_broadcast(
    broadcast_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une diffusion programmée par ID."""
    service = get_broadcast_service(db, current_user.tenant_id)
    broadcast = service.get_scheduled_broadcast(broadcast_id)
    if not broadcast:
        raise HTTPException(status_code=404, detail="Diffusion non trouvée")
    return broadcast


@router.put("/scheduled/{broadcast_id}", response_model=ScheduledBroadcastResponse)
async def update_scheduled_broadcast(
    broadcast_id: int,
    updates: ScheduledBroadcastUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour une diffusion programmée."""
    service = get_broadcast_service(db, current_user.tenant_id)

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activer une diffusion programmée."""
    service = get_broadcast_service(db, current_user.tenant_id)
    broadcast = service.activate_broadcast(broadcast_id)
    if not broadcast:
        raise HTTPException(status_code=404, detail="Diffusion non trouvée")
    return broadcast


@router.post("/scheduled/{broadcast_id}/pause", response_model=ScheduledBroadcastResponse)
async def pause_broadcast(
    broadcast_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre en pause une diffusion."""
    service = get_broadcast_service(db, current_user.tenant_id)
    broadcast = service.pause_broadcast(broadcast_id)
    if not broadcast:
        raise HTTPException(status_code=404, detail="Diffusion non trouvée")
    return broadcast


@router.post("/scheduled/{broadcast_id}/cancel", response_model=ScheduledBroadcastResponse)
async def cancel_broadcast(
    broadcast_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Annuler une diffusion."""
    service = get_broadcast_service(db, current_user.tenant_id)
    broadcast = service.cancel_broadcast(broadcast_id)
    if not broadcast:
        raise HTTPException(status_code=404, detail="Diffusion non trouvée")
    return broadcast


@router.post("/scheduled/{broadcast_id}/execute", response_model=BroadcastExecutionResponse)
async def execute_broadcast_now(
    broadcast_id: int,
    request: ExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Exécuter une diffusion manuellement."""
    service = get_broadcast_service(db, current_user.tenant_id)
    try:
        return service.execute_broadcast(
            broadcast_id,
            triggered_by=request.triggered_by,
            triggered_user=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# EXÉCUTIONS
# ============================================================================

@router.get("/executions", response_model=PaginatedExecutionsResponse)
async def list_executions(
    broadcast_id: Optional[int] = None,
    status: Optional[DeliveryStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les exécutions de diffusion."""
    service = get_broadcast_service(db, current_user.tenant_id)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une exécution par ID."""
    service = get_broadcast_service(db, current_user.tenant_id)
    execution = service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Exécution non trouvée")
    return execution


@router.get("/executions/{execution_id}/details", response_model=PaginatedDeliveryDetailsResponse)
async def get_execution_details(
    execution_id: int,
    status: Optional[DeliveryStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les détails de livraison d'une exécution."""
    service = get_broadcast_service(db, current_user.tenant_id)
    items, total = service.get_delivery_details(
        execution_id,
        status=DeliveryStatus(status.value) if status else None,
        skip=skip,
        limit=limit
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}


# ============================================================================
# PRÉFÉRENCES UTILISATEUR
# ============================================================================

@router.get("/preferences", response_model=BroadcastPreferenceResponse)
async def get_my_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer mes préférences de diffusion."""
    service = get_broadcast_service(db, current_user.tenant_id)
    prefs = service.get_user_preferences(current_user.id)
    if not prefs:
        # Créer des préférences par défaut
        prefs = service.set_user_preferences(current_user.id)
    return prefs


@router.put("/preferences", response_model=BroadcastPreferenceResponse)
async def update_my_preferences(
    preferences: BroadcastPreferenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour mes préférences de diffusion."""
    service = get_broadcast_service(db, current_user.tenant_id)

    pref_dict = preferences.model_dump()
    # Convertir les enums
    if pref_dict.get("preferred_channel"):
        pref_dict["preferred_channel"] = DeliveryChannel(pref_dict["preferred_channel"].value)
    if pref_dict.get("digest_frequency"):
        pref_dict["digest_frequency"] = BroadcastFrequency(pref_dict["digest_frequency"].value)
    if pref_dict.get("report_frequency"):
        pref_dict["report_frequency"] = BroadcastFrequency(pref_dict["report_frequency"].value)

    return service.set_user_preferences(current_user.id, **pref_dict)


@router.post("/unsubscribe", status_code=status.HTTP_200_OK)
async def unsubscribe(
    request: UnsubscribeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Se désabonner d'une diffusion ou de toutes."""
    service = get_broadcast_service(db, current_user.tenant_id)
    service.unsubscribe_user(current_user.id, request.broadcast_id)
    return {"message": "Désabonnement effectué"}


# ============================================================================
# MÉTRIQUES ET DASHBOARD
# ============================================================================

@router.get("/metrics", response_model=list[BroadcastMetricResponse])
async def get_metrics(
    period_type: str = Query("DAILY", pattern="^(DAILY|WEEKLY|MONTHLY)$"),
    limit: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les métriques de diffusion."""
    service = get_broadcast_service(db, current_user.tenant_id)
    return service.get_metrics(period_type=period_type, limit=limit)


@router.post("/metrics/record", response_model=BroadcastMetricResponse)
async def record_metrics(
    period_type: str = Query("DAILY", pattern="^(DAILY|WEEKLY|MONTHLY)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enregistrer les métriques actuelles."""
    service = get_broadcast_service(db, current_user.tenant_id)
    return service.record_metrics(period_type=period_type)


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les statistiques pour le dashboard."""
    service = get_broadcast_service(db, current_user.tenant_id)
    return service.get_dashboard_stats()


# ============================================================================
# DIFFUSIONS À TRAITER (SCHEDULER)
# ============================================================================

@router.get("/due", response_model=list[ScheduledBroadcastResponse])
async def get_broadcasts_due(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les diffusions à exécuter maintenant."""
    service = get_broadcast_service(db, current_user.tenant_id)
    return service.get_broadcasts_due()


@router.post("/process-due", response_model=list[BroadcastExecutionResponse])
async def process_due_broadcasts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Traiter toutes les diffusions en attente."""
    service = get_broadcast_service(db, current_user.tenant_id)
    due_broadcasts = service.get_broadcasts_due()
    executions = []

    for broadcast in due_broadcasts:
        try:
            execution = service.execute_broadcast(
                broadcast.id,
                triggered_by="scheduler",
                triggered_user=current_user.id
            )
            executions.append(execution)
        except Exception:
            pass  # Log error but continue with other broadcasts

    return executions
