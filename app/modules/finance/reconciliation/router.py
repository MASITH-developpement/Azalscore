"""
AZALSCORE Finance Reconciliation AI Router V3
==============================================

Endpoints REST pour le rapprochement bancaire intelligent.

Endpoints:
- GET  /v3/finance/reconciliation/suggestions - Obtenir suggestions de match
- POST /v3/finance/reconciliation/auto - Auto-réconciliation
- POST /v3/finance/reconciliation/manual - Réconciliation manuelle
- POST /v3/finance/reconciliation/undo - Annuler une réconciliation
- GET  /v3/finance/reconciliation/stats - Statistiques
"""

import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.saas_context import SaaSContext
from app.core.dependencies_v2 import get_saas_context

from .service import (
    ReconciliationService,
    MatchSuggestion,
    ReconciliationResult,
    ReconciliationStats,
    MatchType,
    MatchConfidence,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v3/finance/reconciliation", tags=["Finance Reconciliation AI"])


# =============================================================================
# SCHEMAS
# =============================================================================


class SuggestionResponse(BaseModel):
    """Suggestion de rapprochement."""

    id: str
    bank_line_id: str
    entry_line_id: str
    score: int = Field(..., ge=0, le=100, description="Score de confiance 0-100")
    confidence: str = Field(..., description="Niveau: high, medium, low, very_low")
    match_type: str = Field(..., description="Type: exact, amount, fuzzy, pattern, reference")
    reasons: list[str] = Field(default_factory=list)

    # Détails ligne bancaire
    bank_amount: Decimal
    bank_date: Optional[str] = None
    bank_label: str = ""

    # Détails écriture
    entry_amount: Decimal
    entry_date: Optional[str] = None
    entry_label: str = ""

    # Écarts
    amount_diff: Decimal = Decimal("0")
    days_diff: int = 0


class SuggestionsListResponse(BaseModel):
    """Liste de suggestions."""

    suggestions: list[SuggestionResponse]
    total: int
    bank_account_id: str


class AutoReconcileRequest(BaseModel):
    """Requête d'auto-réconciliation."""

    bank_account_id: str = Field(..., description="ID du compte bancaire")
    statement_id: Optional[str] = Field(None, description="ID du relevé (optionnel)")
    min_score: int = Field(
        default=95,
        ge=50,
        le=100,
        description="Score minimum pour auto-match",
    )
    dry_run: bool = Field(
        default=False,
        description="Si True, ne fait pas les modifications",
    )


class ManualReconcileRequest(BaseModel):
    """Requête de réconciliation manuelle."""

    bank_line_id: str = Field(..., description="ID de la ligne bancaire")
    entry_line_id: str = Field(..., description="ID de la ligne d'écriture")


class UndoReconcileRequest(BaseModel):
    """Requête d'annulation de réconciliation."""

    bank_line_id: str = Field(..., description="ID de la ligne bancaire")


class ReconcileResponse(BaseModel):
    """Réponse de réconciliation."""

    success: bool
    matched_count: int = 0
    auto_matched_count: int = 0
    suggested_count: int = 0
    error: Optional[str] = None
    suggestions: list[SuggestionResponse] = Field(default_factory=list)


class StatsResponse(BaseModel):
    """Statistiques de réconciliation."""

    total_bank_lines: int = 0
    reconciled_lines: int = 0
    pending_lines: int = 0
    auto_matched: int = 0
    manually_matched: int = 0
    unmatched: int = 0
    total_amount_reconciled: Decimal = Decimal("0")
    total_amount_pending: Decimal = Decimal("0")
    reconciliation_rate: float = 0.0


# =============================================================================
# HELPERS
# =============================================================================


def get_reconciliation_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
) -> ReconciliationService:
    """Dépendance pour obtenir le service de réconciliation."""
    return ReconciliationService(db=db, tenant_id=context.tenant_id)


def suggestion_to_response(s: MatchSuggestion) -> SuggestionResponse:
    """Convertit une suggestion interne en réponse API."""
    return SuggestionResponse(
        id=s.id,
        bank_line_id=str(s.bank_line_id),
        entry_line_id=str(s.entry_line_id),
        score=s.score,
        confidence=s.confidence.value,
        match_type=s.match_type.value,
        reasons=s.reasons,
        bank_amount=s.bank_amount,
        bank_date=s.bank_date.isoformat() if s.bank_date else None,
        bank_label=s.bank_label,
        entry_amount=s.entry_amount,
        entry_date=s.entry_date.isoformat() if s.entry_date else None,
        entry_label=s.entry_label,
        amount_diff=s.amount_diff,
        days_diff=s.days_diff,
    )


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get(
    "/suggestions",
    response_model=SuggestionsListResponse,
    summary="Obtenir les suggestions de rapprochement",
    description="Génère des suggestions de correspondance entre lignes bancaires et écritures comptables.",
)
async def get_suggestions(
    bank_account_id: str = Query(..., description="ID du compte bancaire"),
    statement_id: Optional[str] = Query(None, description="ID du relevé (optionnel)"),
    limit: int = Query(50, ge=1, le=200, description="Nombre max de suggestions"),
    min_score: int = Query(50, ge=0, le=100, description="Score minimum"),
    service: ReconciliationService = Depends(get_reconciliation_service),
):
    """
    Génère des suggestions de rapprochement automatique.

    L'algorithme analyse:
    - Montants (exact ou proche)
    - Dates (exact ou dans une fenêtre)
    - Références communes
    - Similarité des labels

    Chaque suggestion a un score de 0 à 100.
    """
    try:
        suggestions = await service.get_match_suggestions(
            bank_account_id=UUID(bank_account_id),
            statement_id=UUID(statement_id) if statement_id else None,
            limit=limit,
            min_score=min_score,
        )

        return SuggestionsListResponse(
            suggestions=[suggestion_to_response(s) for s in suggestions],
            total=len(suggestions),
            bank_account_id=bank_account_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/auto",
    response_model=ReconcileResponse,
    summary="Auto-réconciliation",
    description="Réconcilie automatiquement les correspondances à haut score de confiance.",
)
async def auto_reconcile(
    request: AutoReconcileRequest,
    service: ReconciliationService = Depends(get_reconciliation_service),
):
    """
    Auto-réconcilie les correspondances certaines.

    Par défaut, seules les correspondances avec un score >= 95 sont auto-réconciliées.
    Utilisez dry_run=true pour voir les correspondances sans les appliquer.
    """
    try:
        result = await service.auto_reconcile(
            bank_account_id=UUID(request.bank_account_id),
            statement_id=UUID(request.statement_id) if request.statement_id else None,
            min_score=request.min_score,
            dry_run=request.dry_run,
        )

        return ReconcileResponse(
            success=result.success,
            matched_count=result.matched_count,
            auto_matched_count=result.auto_matched_count,
            suggested_count=result.suggested_count,
            error=result.error,
            suggestions=[suggestion_to_response(s) for s in result.suggestions],
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/manual",
    response_model=ReconcileResponse,
    summary="Réconciliation manuelle",
    description="Réconcilie manuellement une ligne bancaire avec une écriture.",
)
async def manual_reconcile(
    request: ManualReconcileRequest,
    service: ReconciliationService = Depends(get_reconciliation_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """
    Réconcilie manuellement une paire ligne bancaire / écriture.

    Cette action est enregistrée pour améliorer les suggestions futures
    (apprentissage des patterns utilisateur).
    """
    try:
        result = await service.manual_reconcile(
            bank_line_id=UUID(request.bank_line_id),
            entry_line_id=UUID(request.entry_line_id),
            user_id=context.user_id,
        )

        return ReconcileResponse(
            success=result.success,
            matched_count=result.matched_count,
            error=result.error,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/undo",
    response_model=ReconcileResponse,
    summary="Annuler une réconciliation",
    description="Annule une réconciliation existante.",
)
async def undo_reconciliation(
    request: UndoReconcileRequest,
    service: ReconciliationService = Depends(get_reconciliation_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """
    Annule une réconciliation.

    La ligne bancaire et l'écriture redeviennent disponibles pour
    un nouveau rapprochement.
    """
    try:
        result = await service.undo_reconciliation(
            bank_line_id=UUID(request.bank_line_id),
            user_id=context.user_id,
        )

        return ReconcileResponse(
            success=result.success,
            matched_count=result.matched_count,
            error=result.error,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Statistiques de réconciliation",
    description="Récupère les statistiques de réconciliation pour un compte.",
)
async def get_stats(
    bank_account_id: str = Query(..., description="ID du compte bancaire"),
    statement_id: Optional[str] = Query(None, description="ID du relevé (optionnel)"),
    service: ReconciliationService = Depends(get_reconciliation_service),
):
    """
    Récupère les statistiques de réconciliation.

    Retourne:
    - Nombre de lignes total/réconciliées/en attente
    - Montants total/réconciliés/en attente
    - Taux de réconciliation
    """
    try:
        stats = await service.get_stats(
            bank_account_id=UUID(bank_account_id),
            statement_id=UUID(statement_id) if statement_id else None,
        )

        rate = 0.0
        if stats.total_bank_lines > 0:
            rate = round(stats.reconciled_lines / stats.total_bank_lines * 100, 1)

        return StatsResponse(
            total_bank_lines=stats.total_bank_lines,
            reconciled_lines=stats.reconciled_lines,
            pending_lines=stats.pending_lines,
            auto_matched=stats.auto_matched,
            manually_matched=stats.manually_matched,
            unmatched=stats.unmatched,
            total_amount_reconciled=stats.total_amount_reconciled,
            total_amount_pending=stats.total_amount_pending,
            reconciliation_rate=rate,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/health",
    summary="Health check réconciliation",
    description="Vérifie que le service de réconciliation est fonctionnel.",
)
async def health_check():
    """Health check pour le service de réconciliation IA."""
    return {
        "status": "healthy",
        "service": "finance-reconciliation-ai",
        "features": [
            "exact_match",
            "fuzzy_match",
            "pattern_match",
            "auto_reconcile",
            "suggestions",
        ],
    }
