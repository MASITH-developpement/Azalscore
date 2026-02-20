"""
AZALS MODULE - Dunning (Relances Impayés): Router
==================================================

Endpoints REST pour la gestion des relances impayés.
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.dependencies import get_tenant_id
from app.core.models import User

from .service import DunningService
from .schemas import (
    DunningLevelCreate,
    DunningLevelUpdate,
    DunningLevelResponse,
    DunningTemplateCreate,
    DunningTemplateResponse,
    DunningRuleCreate,
    DunningRuleResponse,
    DunningActionCreate,
    DunningActionResponse,
    DunningActionListResponse,
    DunningCampaignCreate,
    DunningCampaignResponse,
    PaymentPromiseCreate,
    PaymentPromiseUpdate,
    PaymentPromiseResponse,
    CustomerDunningProfileCreate,
    CustomerDunningProfileUpdate,
    CustomerDunningProfileResponse,
    DunningStatistics,
    OverdueAnalysis,
    BulkDunningRequest,
    BulkDunningResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dunning", tags=["Dunning - Relances Impayés"])


# ============================================================================
# INITIALIZATION
# ============================================================================


@router.post(
    "/initialize",
    status_code=status.HTTP_201_CREATED,
    summary="Initialiser les niveaux par défaut",
    description="Crée les 6 niveaux de relance standard (rappel → recouvrement).",
)
def initialize_dunning(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Initialiser les niveaux de relance par défaut."""
    service = DunningService(db, tenant_id)
    count = service.initialize_default_levels()

    if count == 0:
        return {"message": "Niveaux déjà initialisés", "levels_created": 0}

    return {"message": f"{count} niveaux de relance créés", "levels_created": count}


# ============================================================================
# DUNNING LEVELS
# ============================================================================


@router.get(
    "/levels",
    response_model=list[DunningLevelResponse],
    summary="Lister les niveaux de relance",
)
def list_levels(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> list[DunningLevelResponse]:
    """Lister les niveaux de relance."""
    service = DunningService(db, tenant_id)
    levels = service.list_levels(active_only=active_only)
    return [DunningLevelResponse.model_validate(l) for l in levels]


@router.post(
    "/levels",
    response_model=DunningLevelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un niveau de relance",
)
def create_level(
    data: DunningLevelCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> DunningLevelResponse:
    """Créer un niveau de relance personnalisé."""
    service = DunningService(db, tenant_id)
    level = service.create_level(data)
    return DunningLevelResponse.model_validate(level)


@router.get(
    "/levels/{level_id}",
    response_model=DunningLevelResponse,
    summary="Récupérer un niveau de relance",
)
def get_level(
    level_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> DunningLevelResponse:
    """Récupérer un niveau de relance."""
    service = DunningService(db, tenant_id)
    level = service.get_level(level_id)
    if not level:
        raise HTTPException(status_code=404, detail="Niveau introuvable")
    return DunningLevelResponse.model_validate(level)


# ============================================================================
# TEMPLATES
# ============================================================================


@router.post(
    "/templates",
    response_model=DunningTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un template de relance",
)
def create_template(
    data: DunningTemplateCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> DunningTemplateResponse:
    """Créer un template de relance."""
    service = DunningService(db, tenant_id)
    template = service.create_template(data)
    return DunningTemplateResponse.model_validate(template)


@router.get(
    "/templates/{level_id}/{channel}",
    response_model=DunningTemplateResponse,
    summary="Récupérer un template",
)
def get_template(
    level_id: UUID,
    channel: str,
    language: str = Query("fr"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> DunningTemplateResponse:
    """Récupérer un template pour un niveau et canal."""
    service = DunningService(db, tenant_id)
    template = service.get_template(level_id, channel, language)
    if not template:
        raise HTTPException(status_code=404, detail="Template introuvable")
    return DunningTemplateResponse.model_validate(template)


# ============================================================================
# RULES
# ============================================================================


@router.post(
    "/rules",
    response_model=DunningRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une règle de relance",
)
def create_rule(
    data: DunningRuleCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> DunningRuleResponse:
    """Créer une règle de relance."""
    service = DunningService(db, tenant_id)
    rule = service.create_rule(data)
    return DunningRuleResponse.model_validate(rule)


# ============================================================================
# ACTIONS
# ============================================================================


@router.get(
    "/actions",
    response_model=DunningActionListResponse,
    summary="Lister les actions de relance",
)
def list_actions(
    invoice_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    level_id: Optional[UUID] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> DunningActionListResponse:
    """Lister les actions de relance."""
    service = DunningService(db, tenant_id)
    skip = (page - 1) * page_size
    actions, total = service.get_actions(
        invoice_id=invoice_id,
        customer_id=customer_id,
        status=status,
        level_id=level_id,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=page_size,
    )
    return DunningActionListResponse(
        items=[DunningActionResponse.model_validate(a) for a in actions],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/actions/{action_id}/send",
    response_model=DunningActionResponse,
    summary="Envoyer une action de relance",
)
def send_action(
    action_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> DunningActionResponse:
    """Envoyer une action de relance."""
    service = DunningService(db, tenant_id)
    try:
        action = service.send_action(action_id)
        return DunningActionResponse.model_validate(action)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/actions/{action_id}/payment",
    response_model=DunningActionResponse,
    summary="Marquer un paiement reçu",
)
def mark_payment(
    action_id: UUID,
    payment_amount: Decimal,
    payment_date: date,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> DunningActionResponse:
    """Marquer une action comme payée."""
    service = DunningService(db, tenant_id)
    try:
        action = service.mark_payment_received(action_id, payment_amount, payment_date)
        return DunningActionResponse.model_validate(action)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# CAMPAIGNS
# ============================================================================


@router.post(
    "/campaigns",
    response_model=DunningCampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une campagne de relance",
)
def create_campaign(
    data: DunningCampaignCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> DunningCampaignResponse:
    """Créer une campagne de relance."""
    service = DunningService(db, tenant_id)
    campaign = service.create_campaign(data, created_by=str(current_user.id))
    return DunningCampaignResponse.model_validate(campaign)


@router.post(
    "/campaigns/{campaign_id}/run",
    response_model=DunningCampaignResponse,
    summary="Exécuter une campagne",
)
def run_campaign(
    campaign_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> DunningCampaignResponse:
    """Exécuter une campagne de relance."""
    service = DunningService(db, tenant_id)
    try:
        campaign = service.run_campaign(campaign_id)
        return DunningCampaignResponse.model_validate(campaign)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/bulk",
    response_model=BulkDunningResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Relance en masse",
    description="Créer et envoyer des relances pour toutes les factures éligibles.",
)
def bulk_dunning(
    request: BulkDunningRequest,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> BulkDunningResponse:
    """Relance en masse."""
    service = DunningService(db, tenant_id)

    # Créer une campagne
    campaign_data = DunningCampaignCreate(
        name=f"Relance automatique {date.today().strftime('%Y-%m-%d')}",
        level_id=request.level_id,
        scheduled_at=request.schedule_at,
    )
    campaign = service.create_campaign(campaign_data, created_by=str(current_user.id))

    # Exécuter si pas de planification
    if not request.schedule_at:
        campaign = service.run_campaign(campaign.id)

    return BulkDunningResponse(
        campaign_id=campaign.id,
        total_invoices=campaign.total_invoices,
        total_amount=campaign.total_amount,
        scheduled_at=campaign.scheduled_at,
        status=campaign.status.value,
    )


# ============================================================================
# PAYMENT PROMISES
# ============================================================================


@router.post(
    "/promises",
    response_model=PaymentPromiseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enregistrer une promesse de paiement",
)
def create_promise(
    data: PaymentPromiseCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> PaymentPromiseResponse:
    """Enregistrer une promesse de paiement."""
    service = DunningService(db, tenant_id)
    promise = service.create_promise(data, recorded_by=str(current_user.id))
    return PaymentPromiseResponse.model_validate(promise)


@router.patch(
    "/promises/{promise_id}",
    response_model=PaymentPromiseResponse,
    summary="Mettre à jour une promesse",
)
def update_promise(
    promise_id: UUID,
    data: PaymentPromiseUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> PaymentPromiseResponse:
    """Mettre à jour une promesse de paiement."""
    service = DunningService(db, tenant_id)
    try:
        promise = service.update_promise(promise_id, data)
        return PaymentPromiseResponse.model_validate(promise)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/promises/check-broken",
    summary="Vérifier les promesses non tenues",
)
def check_broken_promises(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Vérifier et marquer les promesses non tenues."""
    service = DunningService(db, tenant_id)
    broken = service.check_broken_promises()
    return {
        "broken_count": len(broken),
        "promise_ids": [str(p.id) for p in broken],
    }


# ============================================================================
# CUSTOMER PROFILES
# ============================================================================


@router.get(
    "/profiles/{customer_id}",
    response_model=CustomerDunningProfileResponse,
    summary="Récupérer le profil de relance d'un client",
)
def get_customer_profile(
    customer_id: str,
    customer_name: str = Query(..., description="Nom du client (pour création auto)"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> CustomerDunningProfileResponse:
    """Récupérer ou créer le profil de relance d'un client."""
    service = DunningService(db, tenant_id)
    profile = service.get_or_create_profile(customer_id, customer_name)
    return CustomerDunningProfileResponse.model_validate(profile)


@router.patch(
    "/profiles/{customer_id}",
    response_model=CustomerDunningProfileResponse,
    summary="Mettre à jour le profil d'un client",
)
def update_customer_profile(
    customer_id: str,
    data: CustomerDunningProfileUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> CustomerDunningProfileResponse:
    """Mettre à jour le profil de relance d'un client."""
    service = DunningService(db, tenant_id)
    try:
        profile = service.update_profile(customer_id, data)
        return CustomerDunningProfileResponse.model_validate(profile)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/profiles/{customer_id}/block",
    response_model=CustomerDunningProfileResponse,
    summary="Bloquer les relances pour un client",
)
def block_customer(
    customer_id: str,
    reason: str = Query(..., description="Raison du blocage"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> CustomerDunningProfileResponse:
    """Bloquer les relances pour un client."""
    service = DunningService(db, tenant_id)
    try:
        profile = service.block_customer_dunning(customer_id, reason)
        return CustomerDunningProfileResponse.model_validate(profile)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# STATISTICS & ANALYSIS
# ============================================================================


@router.get(
    "/statistics",
    response_model=DunningStatistics,
    summary="Statistiques des relances",
)
def get_statistics(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> DunningStatistics:
    """Récupérer les statistiques des relances."""
    service = DunningService(db, tenant_id)
    return service.get_statistics(from_date, to_date)


@router.get(
    "/aging",
    response_model=OverdueAnalysis,
    summary="Analyse du vieillissement des créances",
)
def get_aging_analysis(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
) -> OverdueAnalysis:
    """Analyse du vieillissement des créances (aging report)."""
    service = DunningService(db, tenant_id)
    return service.get_aging_analysis()
