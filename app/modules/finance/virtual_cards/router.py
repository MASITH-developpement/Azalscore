"""
AZALSCORE Finance Virtual Cards Router V3
==========================================

Endpoints REST pour la gestion des cartes virtuelles.

Endpoints:
- GET  /v3/finance/virtual-cards/cards - Liste des cartes
- POST /v3/finance/virtual-cards/cards - Créer une carte
- GET  /v3/finance/virtual-cards/cards/{card_id} - Détails d'une carte
- POST /v3/finance/virtual-cards/cards/{card_id}/block - Bloquer
- POST /v3/finance/virtual-cards/cards/{card_id}/unblock - Débloquer
- POST /v3/finance/virtual-cards/cards/{card_id}/cancel - Annuler
- PUT  /v3/finance/virtual-cards/cards/{card_id}/limits - Modifier limites
- POST /v3/finance/virtual-cards/authorize - Autoriser transaction
- GET  /v3/finance/virtual-cards/transactions - Historique
- POST /v3/finance/virtual-cards/transactions/{id}/reverse - Annuler
- GET  /v3/finance/virtual-cards/stats/{card_id} - Statistiques
- GET  /v3/finance/virtual-cards/alerts - Alertes
- GET  /v3/finance/virtual-cards/health - Health check
"""
from __future__ import annotations


import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.saas_context import SaaSContext
from app.core.dependencies_v2 import get_saas_context

from .service import (
    VirtualCardService,
    VirtualCard,
    CardTransaction,
    CardStatus,
    CardType,
    CardLimitType,
    TransactionStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v3/finance/virtual-cards", tags=["Finance Virtual Cards"])


# =============================================================================
# SCHEMAS
# =============================================================================


class CreateCardRequest(BaseModel):
    """Requête de création de carte."""

    holder_name: str = Field(..., min_length=2, max_length=100, description="Nom du titulaire")
    card_type: CardType = Field(CardType.STANDARD, description="Type de carte")
    limit_per_transaction: Optional[Decimal] = Field(None, gt=0, description="Limite par transaction")
    limit_daily: Optional[Decimal] = Field(None, gt=0, description="Limite quotidienne")
    limit_monthly: Optional[Decimal] = Field(None, gt=0, description="Limite mensuelle")
    limit_total: Optional[Decimal] = Field(None, gt=0, description="Budget total")
    merchant_categories: Optional[list[str]] = Field(None, description="Catégories MCC autorisées")
    expires_in_days: Optional[int] = Field(None, gt=0, le=365, description="Jours avant expiration")
    metadata: Optional[dict] = Field(None, description="Métadonnées")


class CardLimitResponse(BaseModel):
    """Limite de carte."""

    limit_type: str
    amount: Decimal
    used: Decimal
    remaining: Decimal
    usage_percent: Decimal


class CardResponse(BaseModel):
    """Réponse carte."""

    id: str
    masked_number: str
    expiry_date: str
    holder_name: str
    card_type: str
    status: str
    limits: list[CardLimitResponse] = Field(default_factory=list)
    merchant_categories: list[str] = Field(default_factory=list)
    blocked_merchants: list[str] = Field(default_factory=list)
    created_at: str
    expires_at: Optional[str] = None
    used_count: int
    total_spent: Decimal


class CardDetailsResponse(CardResponse):
    """Réponse carte avec détails sensibles (accès restreint)."""

    card_number_full: str
    cvv: str
    expiry_month: int
    expiry_year: int


class UpdateLimitsRequest(BaseModel):
    """Requête de mise à jour des limites."""

    limit_per_transaction: Optional[Decimal] = Field(None, gt=0)
    limit_daily: Optional[Decimal] = Field(None, gt=0)
    limit_monthly: Optional[Decimal] = Field(None, gt=0)
    limit_total: Optional[Decimal] = Field(None, gt=0)


class AuthorizeTransactionRequest(BaseModel):
    """Requête d'autorisation de transaction."""

    card_id: str = Field(..., description="ID de la carte")
    amount: Decimal = Field(..., gt=0, description="Montant")
    currency: str = Field("EUR", min_length=3, max_length=3, description="Devise")
    merchant_name: str = Field(..., min_length=1, description="Nom du marchand")
    merchant_category: str = Field(..., min_length=4, max_length=4, description="Code MCC")
    merchant_country: str = Field("FR", min_length=2, max_length=2, description="Pays")
    metadata: Optional[dict] = None


class TransactionResponse(BaseModel):
    """Réponse transaction."""

    id: str
    card_id: str
    amount: Decimal
    currency: str
    merchant_name: str
    merchant_category: str
    merchant_country: str
    status: str
    decline_reason: Optional[str] = None
    authorization_code: Optional[str] = None
    transaction_date: str


class AuthorizationResponse(BaseModel):
    """Réponse d'autorisation."""

    success: bool
    transaction: Optional[TransactionResponse] = None
    decline_reason: Optional[str] = None
    error: Optional[str] = None


class CardStatsResponse(BaseModel):
    """Statistiques de carte."""

    card_id: str
    total_transactions: int
    approved_transactions: int
    declined_transactions: int
    total_spent: Decimal
    average_transaction: Decimal
    most_used_merchant: Optional[str] = None
    most_used_category: Optional[str] = None
    spending_by_category: dict = Field(default_factory=dict)


class AlertResponse(BaseModel):
    """Alerte de dépense."""

    card_id: str
    card_number: str
    limit_type: str
    limit_amount: str
    used: str
    remaining: str
    usage_percent: str
    alert_level: str


class BlockRequest(BaseModel):
    """Requête de blocage."""

    reason: Optional[str] = Field(None, max_length=500, description="Raison du blocage")


# =============================================================================
# DEPENDENCIES
# =============================================================================


def get_virtual_card_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
) -> VirtualCardService:
    """Dépendance pour obtenir le service de cartes virtuelles."""
    return VirtualCardService(db=db, tenant_id=context.tenant_id)


# =============================================================================
# HELPERS
# =============================================================================


def card_to_response(card: VirtualCard) -> CardResponse:
    """Convertit une carte en réponse."""
    return CardResponse(
        id=card.id,
        masked_number=card.masked_number,
        expiry_date=card.expiry_date,
        holder_name=card.holder_name,
        card_type=card.card_type.value,
        status=card.status.value,
        limits=[
            CardLimitResponse(
                limit_type=l.limit_type.value,
                amount=l.amount,
                used=l.used,
                remaining=l.remaining,
                usage_percent=l.usage_percent,
            )
            for l in card.limits
        ],
        merchant_categories=card.merchant_categories,
        blocked_merchants=card.blocked_merchants,
        created_at=card.created_at.isoformat(),
        expires_at=card.expires_at.isoformat() if card.expires_at else None,
        used_count=card.used_count,
        total_spent=card.total_spent,
    )


def card_to_details(card: VirtualCard) -> CardDetailsResponse:
    """Convertit une carte en réponse détaillée."""
    return CardDetailsResponse(
        id=card.id,
        masked_number=card.masked_number,
        card_number_full=card.card_number_full,
        cvv=card.cvv,
        expiry_date=card.expiry_date,
        expiry_month=card.expiry_month,
        expiry_year=card.expiry_year,
        holder_name=card.holder_name,
        card_type=card.card_type.value,
        status=card.status.value,
        limits=[
            CardLimitResponse(
                limit_type=l.limit_type.value,
                amount=l.amount,
                used=l.used,
                remaining=l.remaining,
                usage_percent=l.usage_percent,
            )
            for l in card.limits
        ],
        merchant_categories=card.merchant_categories,
        blocked_merchants=card.blocked_merchants,
        created_at=card.created_at.isoformat(),
        expires_at=card.expires_at.isoformat() if card.expires_at else None,
        used_count=card.used_count,
        total_spent=card.total_spent,
    )


def transaction_to_response(tx: CardTransaction) -> TransactionResponse:
    """Convertit une transaction en réponse."""
    return TransactionResponse(
        id=tx.id,
        card_id=tx.card_id,
        amount=tx.amount,
        currency=tx.currency,
        merchant_name=tx.merchant_name,
        merchant_category=tx.merchant_category,
        merchant_country=tx.merchant_country,
        status=tx.status.value,
        decline_reason=tx.decline_reason.value if tx.decline_reason else None,
        authorization_code=tx.authorization_code,
        transaction_date=tx.transaction_date.isoformat(),
    )


# =============================================================================
# ENDPOINTS - CARDS
# =============================================================================


@router.post(
    "/cards",
    response_model=CardDetailsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une carte virtuelle",
    description="Crée une nouvelle carte virtuelle avec les limites spécifiées.",
)
async def create_card(
    request: CreateCardRequest,
    service: VirtualCardService = Depends(get_virtual_card_service),
):
    """
    Crée une carte virtuelle.

    Types disponibles:
    - **standard**: Carte réutilisable
    - **single_use**: Usage unique (expire après 1 transaction)
    - **recurring**: Pour abonnements
    - **team**: Partagée entre membres
    - **expense**: Notes de frais
    """
    result = await service.create_card(
        holder_name=request.holder_name,
        card_type=request.card_type,
        limit_per_transaction=request.limit_per_transaction,
        limit_daily=request.limit_daily,
        limit_monthly=request.limit_monthly,
        limit_total=request.limit_total,
        merchant_categories=request.merchant_categories,
        expires_in_days=request.expires_in_days,
        metadata=request.metadata,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error,
        )

    return card_to_details(result.card)


@router.get(
    "/cards",
    response_model=list[CardResponse],
    summary="Liste des cartes",
    description="Retourne toutes les cartes virtuelles du tenant.",
)
async def list_cards(
    card_status: Optional[CardStatus] = Query(None, alias="status", description="Filtrer par statut"),
    card_type: Optional[CardType] = Query(None, alias="type", description="Filtrer par type"),
    service: VirtualCardService = Depends(get_virtual_card_service),
):
    """Liste les cartes virtuelles avec filtres optionnels."""
    cards = await service.list_cards(status=card_status, card_type=card_type)
    return [card_to_response(c) for c in cards]


@router.get(
    "/cards/{card_id}",
    response_model=CardDetailsResponse,
    summary="Détails d'une carte",
    description="Retourne les détails complets d'une carte (incluant numéro et CVV).",
)
async def get_card(
    card_id: str,
    service: VirtualCardService = Depends(get_virtual_card_service),
):
    """Récupère les détails d'une carte avec informations sensibles."""
    card = await service.get_card(card_id)

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée",
        )

    return card_to_details(card)


@router.post(
    "/cards/{card_id}/block",
    response_model=dict,
    summary="Bloquer une carte",
    description="Bloque temporairement une carte virtuelle.",
)
async def block_card(
    card_id: str,
    request: BlockRequest = BlockRequest(),
    service: VirtualCardService = Depends(get_virtual_card_service),
):
    """Bloque une carte. Elle pourra être débloquée ultérieurement."""
    success = await service.block_card(card_id, reason=request.reason)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée",
        )

    return {"success": True, "message": "Carte bloquée"}


@router.post(
    "/cards/{card_id}/unblock",
    response_model=dict,
    summary="Débloquer une carte",
    description="Débloque une carte préalablement bloquée.",
)
async def unblock_card(
    card_id: str,
    service: VirtualCardService = Depends(get_virtual_card_service),
):
    """Débloque une carte bloquée."""
    success = await service.unblock_card(card_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Carte non trouvée ou non bloquée",
        )

    return {"success": True, "message": "Carte débloquée"}


@router.post(
    "/cards/{card_id}/cancel",
    response_model=dict,
    summary="Annuler une carte",
    description="Annule définitivement une carte virtuelle.",
)
async def cancel_card(
    card_id: str,
    request: BlockRequest = BlockRequest(),
    service: VirtualCardService = Depends(get_virtual_card_service),
):
    """Annule définitivement une carte. Cette action est irréversible."""
    success = await service.cancel_card(card_id, reason=request.reason)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée",
        )

    return {"success": True, "message": "Carte annulée définitivement"}


@router.put(
    "/cards/{card_id}/limits",
    response_model=CardResponse,
    summary="Modifier les limites",
    description="Modifie les limites d'une carte.",
)
async def update_limits(
    card_id: str,
    request: UpdateLimitsRequest,
    service: VirtualCardService = Depends(get_virtual_card_service),
):
    """Modifie les limites d'une carte existante."""
    success = await service.update_limits(
        card_id=card_id,
        limit_per_transaction=request.limit_per_transaction,
        limit_daily=request.limit_daily,
        limit_monthly=request.limit_monthly,
        limit_total=request.limit_total,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée",
        )

    card = await service.get_card(card_id)
    return card_to_response(card)


# =============================================================================
# ENDPOINTS - MERCHANTS
# =============================================================================


@router.post(
    "/cards/{card_id}/blocked-merchants",
    response_model=dict,
    summary="Bloquer un marchand",
    description="Ajoute un marchand à la liste bloquée.",
)
async def add_blocked_merchant(
    card_id: str,
    merchant_id: str = Query(..., description="ID ou nom du marchand"),
    service: VirtualCardService = Depends(get_virtual_card_service),
):
    """Bloque un marchand pour cette carte."""
    success = await service.add_blocked_merchant(card_id, merchant_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée",
        )

    return {"success": True, "message": f"Marchand {merchant_id} bloqué"}


@router.delete(
    "/cards/{card_id}/blocked-merchants/{merchant_id}",
    response_model=dict,
    summary="Débloquer un marchand",
    description="Retire un marchand de la liste bloquée.",
)
async def remove_blocked_merchant(
    card_id: str,
    merchant_id: str,
    service: VirtualCardService = Depends(get_virtual_card_service),
):
    """Débloque un marchand pour cette carte."""
    success = await service.remove_blocked_merchant(card_id, merchant_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée",
        )

    return {"success": True, "message": f"Marchand {merchant_id} débloqué"}


# =============================================================================
# ENDPOINTS - TRANSACTIONS
# =============================================================================


@router.post(
    "/authorize",
    response_model=AuthorizationResponse,
    summary="Autoriser une transaction",
    description="Tente d'autoriser une transaction sur une carte.",
)
async def authorize_transaction(
    request: AuthorizeTransactionRequest,
    service: VirtualCardService = Depends(get_virtual_card_service),
):
    """
    Autorisation de transaction.

    Vérifie:
    - Statut de la carte
    - Limites disponibles
    - Marchand autorisé
    - Catégorie MCC autorisée
    """
    result = await service.authorize_transaction(
        card_id=request.card_id,
        amount=request.amount,
        currency=request.currency,
        merchant_name=request.merchant_name,
        merchant_category=request.merchant_category,
        merchant_country=request.merchant_country,
        metadata=request.metadata,
    )

    if not result.success:
        return AuthorizationResponse(
            success=False,
            decline_reason=result.decline_reason.value if result.decline_reason else None,
            error=result.error,
        )

    return AuthorizationResponse(
        success=True,
        transaction=transaction_to_response(result.transaction),
    )


@router.get(
    "/transactions",
    response_model=list[TransactionResponse],
    summary="Historique des transactions",
    description="Retourne l'historique des transactions.",
)
async def get_transactions(
    card_id: Optional[str] = Query(None, description="Filtrer par carte"),
    tx_status: Optional[TransactionStatus] = Query(None, alias="status", description="Filtrer par statut"),
    start_date: Optional[datetime] = Query(None, description="Date de début"),
    end_date: Optional[datetime] = Query(None, description="Date de fin"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre max de résultats"),
    service: VirtualCardService = Depends(get_virtual_card_service),
):
    """Liste les transactions avec filtres optionnels."""
    transactions = await service.get_transactions(
        card_id=card_id,
        status=tx_status,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

    return [transaction_to_response(t) for t in transactions]


@router.post(
    "/transactions/{transaction_id}/reverse",
    response_model=dict,
    summary="Annuler une transaction",
    description="Annule une transaction approuvée (remboursement).",
)
async def reverse_transaction(
    transaction_id: str,
    reason: Optional[str] = Query(None, description="Raison de l'annulation"),
    service: VirtualCardService = Depends(get_virtual_card_service),
):
    """Annule une transaction et recrédite les limites."""
    success = await service.reverse_transaction(transaction_id, reason=reason)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction non trouvée ou déjà annulée",
        )

    return {"success": True, "message": "Transaction annulée"}


# =============================================================================
# ENDPOINTS - STATISTICS & ALERTS
# =============================================================================


@router.get(
    "/stats/{card_id}",
    response_model=CardStatsResponse,
    summary="Statistiques d'une carte",
    description="Retourne les statistiques d'utilisation d'une carte.",
)
async def get_card_stats(
    card_id: str,
    service: VirtualCardService = Depends(get_virtual_card_service),
):
    """Calcule et retourne les statistiques d'une carte."""
    stats = await service.get_card_stats(card_id)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée",
        )

    return CardStatsResponse(
        card_id=stats.card_id,
        total_transactions=stats.total_transactions,
        approved_transactions=stats.approved_transactions,
        declined_transactions=stats.declined_transactions,
        total_spent=stats.total_spent,
        average_transaction=stats.average_transaction,
        most_used_merchant=stats.most_used_merchant,
        most_used_category=stats.most_used_category,
        spending_by_category=stats.spending_by_category,
    )


@router.get(
    "/alerts",
    response_model=list[AlertResponse],
    summary="Alertes de dépense",
    description="Retourne les cartes proches de leurs limites.",
)
async def get_alerts(
    threshold: Decimal = Query(Decimal("80"), ge=0, le=100, description="Seuil d'alerte en %"),
    service: VirtualCardService = Depends(get_virtual_card_service),
):
    """
    Alertes de dépassement de limites.

    Retourne les cartes dont l'utilisation dépasse le seuil spécifié.
    """
    alerts = await service.get_spending_alerts(threshold_percent=threshold)
    return [AlertResponse(**a) for a in alerts]


@router.get(
    "/card-types",
    summary="Types de cartes",
    description="Liste les types de cartes disponibles.",
)
async def get_card_types(
    service: VirtualCardService = Depends(get_virtual_card_service),
):
    """Retourne la liste des types de cartes avec leurs descriptions."""
    return service.get_card_types()


@router.get(
    "/health",
    summary="Health check cartes virtuelles",
    description="Vérifie que le service de cartes virtuelles est fonctionnel.",
)
async def health_check():
    """Health check pour le service de cartes virtuelles."""
    return {
        "status": "healthy",
        "service": "finance-virtual-cards",
        "features": [
            "card_creation",
            "card_limits",
            "transaction_authorization",
            "merchant_blocking",
            "spending_alerts",
            "single_use_cards",
        ],
        "card_types": [t.value for t in CardType],
        "limit_types": [l.value for l in CardLimitType],
    }
