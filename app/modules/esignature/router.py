"""
AZALS - Module Signature Électronique - API Router
===================================================
Endpoints API pour la gestion des signatures électroniques.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.saas_context import SaaSContext, get_saas_context
from app.db import get_db

from .models import SignatureProvider, SignatureStatus
from .schemas import (
    DeclineSignatureRequest,
    ProvidersListResponse,
    SendSignatureRequest,
    SignatureDashboard,
    SignatureRequestCreate,
    SignatureRequestListResponse,
    SignatureRequestResponse,
    SignatureRequestUpdate,
    SignatureStats,
)
from .service import ESignatureService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/esignature", tags=["E-Signature"])


# ============================================================================
# DEMANDES DE SIGNATURE
# ============================================================================

@router.post("/requests", response_model=SignatureRequestResponse, status_code=status.HTTP_201_CREATED)
def create_signature_request(
    data: SignatureRequestCreate,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Crée une nouvelle demande de signature électronique.
    
    - **document_type**: Type de document (QUOTE, CONTRACT, INVOICE, etc.)
    - **document_id**: ID du document à signer
    - **signers**: Liste des signataires (au moins 1)
    - **provider**: Provider à utiliser (YOUSIGN par défaut)
    """
    service = ESignatureService(db, ctx.tenant_id, ctx.user_id)
    request = service.create_request(data)
    return SignatureRequestResponse.model_validate(request)


@router.get("/requests/{request_id}", response_model=SignatureRequestResponse)
def get_signature_request(
    request_id: UUID,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Récupère les détails d'une demande de signature."""
    service = ESignatureService(db, ctx.tenant_id, ctx.user_id)
    request = service.get_request(str(request_id))
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demande de signature non trouvée"
        )
    
    return SignatureRequestResponse.model_validate(request)


@router.get("/requests", response_model=SignatureRequestListResponse)
def list_signature_requests(
    status_filter: Optional[SignatureStatus] = None,
    document_type: Optional[str] = None,
    document_id: Optional[UUID] = None,
    page: int = 1,
    page_size: int = 50,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les demandes de signature avec filtres.
    
    - **status**: Filtrer par statut (DRAFT, PENDING, SIGNED, etc.)
    - **document_type**: Filtrer par type de document
    - **document_id**: Filtrer par ID de document
    """
    service = ESignatureService(db, ctx.tenant_id, ctx.user_id)
    return service.list_requests(
        status=status_filter,
        document_type=document_type,
        document_id=str(document_id) if document_id else None,
        page=page,
        page_size=page_size
    )


@router.patch("/requests/{request_id}", response_model=SignatureRequestResponse)
def update_signature_request(
    request_id: UUID,
    data: SignatureRequestUpdate,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Met à jour une demande de signature."""
    service = ESignatureService(db, ctx.tenant_id, ctx.user_id)
    request = service.update_request(str(request_id), data)
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demande de signature non trouvée"
        )
    
    return SignatureRequestResponse.model_validate(request)


# ============================================================================
# ACTIONS SUR DEMANDES
# ============================================================================

@router.post("/requests/{request_id}/send", response_model=SignatureRequestResponse)
def send_signature_request(
    request_id: UUID,
    data: SendSignatureRequest,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Envoie une demande de signature aux signataires.
    
    Cette action crée la demande chez le provider (Yousign/DocuSign)
    et envoie les emails de notification aux signataires.
    """
    service = ESignatureService(db, ctx.tenant_id, ctx.user_id)
    request = service.send_request(
        str(request_id),
        notify_signers=data.notify_signers
    )
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible d'envoyer la demande"
        )
    
    return SignatureRequestResponse.model_validate(request)


@router.post("/requests/{request_id}/cancel", response_model=SignatureRequestResponse)
def cancel_signature_request(
    request_id: UUID,
    data: DeclineSignatureRequest,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Annule une demande de signature."""
    service = ESignatureService(db, ctx.tenant_id, ctx.user_id)
    request = service.cancel_request(str(request_id), data.reason)
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible d'annuler la demande"
        )
    
    return SignatureRequestResponse.model_validate(request)


# ============================================================================
# STATISTIQUES
# ============================================================================

@router.get("/stats", response_model=SignatureStats)
def get_signature_stats(
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Récupère les statistiques des signatures du tenant."""
    service = ESignatureService(db, ctx.tenant_id, ctx.user_id)
    return service.get_stats()


@router.get("/dashboard", response_model=SignatureDashboard)
def get_signature_dashboard(
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère le dashboard des signatures.
    
    Inclut statistiques + demandes récentes + signatures en attente.
    """
    service = ESignatureService(db, ctx.tenant_id, ctx.user_id)
    
    # Statistiques
    stats = service.get_stats()
    
    # Demandes récentes (10 dernières)
    recent = service.list_requests(page=1, page_size=10)
    
    # Signatures en attente
    pending = service.list_requests(
        status=SignatureStatus.PENDING,
        page=1,
        page_size=20
    )
    
    return SignatureDashboard(
        stats=stats,
        recent_requests=recent.requests,
        pending_signatures=[]  # TODO: Extraire les signataires en attente
    )


# ============================================================================
# PROVIDERS
# ============================================================================

@router.get("/providers", response_model=ProvidersListResponse)
def list_providers(
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les providers de signature électronique disponibles.
    
    Retourne la configuration et l'état de chaque provider.
    """
    # TODO: Implémenter récupération configuration depuis tenant settings
    from .schemas import ProviderConfigResponse
    
    providers = [
        ProviderConfigResponse(
            provider=SignatureProvider.YOUSIGN,
            is_configured=False,  # Check tenant settings
            is_active=False,
            supports_features={
                "multi_signers": True,
                "reminders": True,
                "eidas_compliance": True,
                "advanced_signature": True
            }
        ),
        ProviderConfigResponse(
            provider=SignatureProvider.DOCUSIGN,
            is_configured=False,
            is_active=False,
            supports_features={
                "multi_signers": True,
                "reminders": True,
                "international": True,
                "templates": True
            }
        )
    ]
    
    return ProvidersListResponse(
        providers=providers,
        default_provider=SignatureProvider.YOUSIGN
    )


# ============================================================================
# WEBHOOKS
# ============================================================================

@router.post("/webhook/yousign", status_code=status.HTTP_200_OK)
async def yousign_webhook(
    event: dict,
    db: Session = Depends(get_db)
):
    """
    Webhook pour les événements Yousign.
    
    Appelé par Yousign lors d'événements sur les signatures.
    """
    # TODO: Valider signature webhook Yousign
    logger.info(f"Received Yousign webhook: {event}")
    
    # Traiter l'événement (pas de tenant_id dans le webhook, récupérer depuis provider_request_id)
    # service = ESignatureService(db, tenant_id, None)
    # service.handle_webhook(SignatureProvider.YOUSIGN, event)
    
    return {"status": "received"}


@router.post("/webhook/docusign", status_code=status.HTTP_200_OK)
async def docusign_webhook(
    event: dict,
    db: Session = Depends(get_db)
):
    """
    Webhook pour les événements DocuSign.
    
    Appelé par DocuSign lors d'événements sur les enveloppes.
    """
    logger.info(f"Received DocuSign webhook: {event}")
    
    # TODO: Implémenter traitement webhook DocuSign
    
    return {"status": "received"}
