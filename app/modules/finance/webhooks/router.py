"""
AZALSCORE Finance Webhook Router V3
===================================

Endpoints REST pour la réception et la gestion des webhooks finance.

Endpoints:
- POST /v3/finance/webhooks/{provider} - Recevoir un webhook
- GET  /v3/finance/webhooks/events - Lister les événements
- GET  /v3/finance/webhooks/events/{event_id} - Détails d'un événement
- POST /v3/finance/webhooks/retry - Retenter les événements échoués
- GET  /v3/finance/webhooks/health - Health check webhooks
"""
from __future__ import annotations


import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.saas_context import SaaSContext
from app.core.dependencies_v2 import get_saas_context
from .service import WebhookService, WebhookResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v3/finance/webhooks", tags=["Finance Webhooks"])


# =============================================================================
# SCHEMAS
# =============================================================================


class WebhookResponse(BaseModel):
    """Réponse standard pour les webhooks."""

    success: bool
    event_id: str
    message: Optional[str] = None


class EventListResponse(BaseModel):
    """Liste des événements webhook."""

    events: list[dict]
    total: int
    limit: int
    offset: int


class RetryResponse(BaseModel):
    """Résultat du retry."""

    total: int
    success: int
    failed: int
    skipped: int


# =============================================================================
# DEPENDENCIES
# =============================================================================


def get_webhook_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
) -> WebhookService:
    """Dépendance pour obtenir le service webhook."""
    return WebhookService(db=db, tenant_id=context.tenant_id)


# =============================================================================
# WEBHOOK RECEPTION
# =============================================================================


@router.post(
    "/{provider}",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Recevoir un webhook",
    description="Endpoint pour recevoir les webhooks de tous les providers finance.",
)
async def receive_webhook(
    provider: str,
    request: Request,
    db: Session = Depends(get_db),
    x_swan_signature: Optional[str] = Header(None),
    x_nmi_signature: Optional[str] = Header(None),
    x_defacto_signature: Optional[str] = Header(None),
    x_solaris_signature: Optional[str] = Header(None),
):
    """
    Reçoit et traite un webhook d'un provider finance.

    Ce endpoint est appelé par les providers (Swan, NMI, Defacto, Solaris)
    lorsqu'un événement se produit (paiement, transaction, etc.).

    La signature est vérifiée pour garantir l'authenticité du webhook.

    Args:
        provider: Nom du provider (swan, nmi, defacto, solaris)
        request: Requête FastAPI

    Returns:
        WebhookResponse avec le statut du traitement
    """
    # Valider le provider
    valid_providers = ["swan", "nmi", "defacto", "solaris"]
    if provider.lower() not in valid_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider invalide. Valeurs acceptées: {valid_providers}",
        )

    # Lire le body brut
    try:
        payload = await request.body()
    except Exception as e:
        logger.error(f"Erreur lecture body: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de lire le body de la requête",
        )

    # Extraire la signature selon le provider
    signature_map = {
        "swan": x_swan_signature,
        "nmi": x_nmi_signature,
        "defacto": x_defacto_signature,
        "solaris": x_solaris_signature,
    }
    signature = signature_map.get(provider.lower())

    # Extraire le tenant_id
    # En production, ceci serait extrait du path ou d'un header
    # Pour les webhooks, on peut utiliser un mapping provider -> tenant
    # ou un sous-domaine
    tenant_id = request.headers.get("X-Tenant-ID")

    if not tenant_id:
        # Fallback: essayer d'extraire du query param
        tenant_id = request.query_params.get("tenant_id")

    if not tenant_id:
        # Pour les tests/dev, on accepte sans tenant_id
        # En production, ceci devrait être une erreur
        logger.warning("Webhook reçu sans tenant_id")
        tenant_id = "default"

    # Traiter le webhook
    service = WebhookService(db=db, tenant_id=tenant_id)

    result = await service.process_webhook(
        provider=provider,
        payload=payload,
        signature=signature,
        headers=dict(request.headers),
    )

    # Toujours retourner 200 pour éviter les retries inutiles
    # Le statut interne est dans la réponse
    return WebhookResponse(
        success=result.success,
        event_id=result.event_id,
        message=result.message or result.error,
    )


# =============================================================================
# EVENT MANAGEMENT (Authenticated)
# =============================================================================


@router.get(
    "/events",
    response_model=EventListResponse,
    summary="Lister les événements webhook",
    description="Liste les événements webhook reçus pour ce tenant.",
)
async def list_events(
    provider: Optional[str] = None,
    event_type: Optional[str] = None,
    processed: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    service: WebhookService = Depends(get_webhook_service),
):
    """
    Liste les événements webhook.

    Args:
        provider: Filtrer par provider
        event_type: Filtrer par type d'événement
        processed: Filtrer par statut de traitement
        limit: Nombre max de résultats
        offset: Décalage pour pagination

    Returns:
        Liste paginée des événements
    """
    events = await service.get_events(
        provider=provider,
        event_type=event_type,
        processed=processed,
        limit=limit,
        offset=offset,
    )

    return EventListResponse(
        events=events,
        total=len(events),  # NOTE: Phase 2 - Count query séparé
        limit=limit,
        offset=offset,
    )


@router.get(
    "/events/{event_id}",
    summary="Détails d'un événement",
    description="Récupère les détails d'un événement webhook spécifique.",
)
async def get_event(
    event_id: str,
    service: WebhookService = Depends(get_webhook_service),
):
    """
    Récupère les détails d'un événement webhook.

    Args:
        event_id: ID de l'événement

    Returns:
        Détails de l'événement
    """
    event = await service.get_event(event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Événement {event_id} non trouvé",
        )

    return event


@router.post(
    "/retry",
    response_model=RetryResponse,
    summary="Retenter les événements échoués",
    description="Retente le traitement des événements webhook échoués.",
)
async def retry_failed_events(
    max_retries: int = 3,
    limit: int = 100,
    service: WebhookService = Depends(get_webhook_service),
):
    """
    Retente le traitement des événements échoués.

    Args:
        max_retries: Nombre max de tentatives par événement
        limit: Nombre max d'événements à traiter

    Returns:
        Statistiques de retry
    """
    stats = await service.retry_failed_events(
        max_retries=max_retries,
        limit=limit,
    )

    return RetryResponse(**stats)


# =============================================================================
# HEALTH CHECK
# =============================================================================


@router.get(
    "/health",
    summary="Health check webhooks",
    description="Vérifie que le service de webhooks est fonctionnel.",
)
async def health_check():
    """Health check pour le service de webhooks."""
    return {
        "status": "healthy",
        "service": "finance-webhooks",
        "providers": ["swan", "nmi", "defacto", "solaris"],
    }
