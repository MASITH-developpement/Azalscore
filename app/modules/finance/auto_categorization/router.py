"""
AZALSCORE Finance Auto Categorization Router V3
================================================

Endpoints REST pour la catégorisation automatique.

Endpoints:
- POST /v3/finance/auto-categorization/categorize - Catégoriser une transaction
- POST /v3/finance/auto-categorization/batch - Catégoriser un lot
- GET  /v3/finance/auto-categorization/rules - Lister les règles
- POST /v3/finance/auto-categorization/rules - Créer une règle
- PUT  /v3/finance/auto-categorization/rules/{id} - Modifier une règle
- DELETE /v3/finance/auto-categorization/rules/{id} - Supprimer une règle
- GET  /v3/finance/auto-categorization/stats - Statistiques
- GET  /v3/finance/auto-categorization/health - Health check
"""

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
    CategorizationService,
    CategorizationRule,
    Transaction,
    TransactionType,
    RuleType,
    MatchConfidence,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v3/finance/auto-categorization", tags=["Finance Auto Categorization"])


# =============================================================================
# SCHEMAS
# =============================================================================


class TransactionRequest(BaseModel):
    """Transaction à catégoriser."""

    id: str
    label: str
    amount: Decimal
    date: str  # ISO format
    transaction_type: str = Field(..., description="debit ou credit")
    reference: Optional[str] = None
    counterpart_name: Optional[str] = None
    counterpart_iban: Optional[str] = None
    bank_account_id: Optional[str] = None


class CategorySuggestionResponse(BaseModel):
    """Suggestion de catégorie."""

    account_code: str
    account_name: str
    category: Optional[str] = None
    confidence: float
    match_confidence: str
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    reason: str


class CategorizationResponse(BaseModel):
    """Réponse de catégorisation."""

    success: bool
    transaction_id: Optional[str] = None
    auto_applied: bool = False
    applied_account_code: Optional[str] = None
    applied_account_name: Optional[str] = None
    applied_category: Optional[str] = None
    applied_rule_id: Optional[str] = None
    suggestions: list[CategorySuggestionResponse] = Field(default_factory=list)
    confidence: float = 0.0
    match_confidence: str = "suggested"
    error: Optional[str] = None


class BatchCategorizationRequest(BaseModel):
    """Requête de catégorisation par lot."""

    transactions: list[TransactionRequest]
    auto_apply: bool = False


class BatchCategorizationResponse(BaseModel):
    """Réponse de catégorisation par lot."""

    total: int
    categorized: int
    auto_applied: int
    results: list[CategorizationResponse] = Field(default_factory=list)


class RuleRequest(BaseModel):
    """Requête de création/modification de règle."""

    name: str
    rule_type: str = Field(..., description="keyword, pattern, amount_range, vendor, customer, iban, combined")
    priority: int = 0
    keywords: list[str] = Field(default_factory=list)
    pattern: Optional[str] = None
    amount_min: Optional[Decimal] = None
    amount_max: Optional[Decimal] = None
    transaction_type: Optional[str] = None
    iban: Optional[str] = None
    partner_id: Optional[str] = None
    account_code: Optional[str] = None
    account_id: Optional[str] = None
    category: Optional[str] = None
    tax_code: Optional[str] = None
    journal_id: Optional[str] = None
    is_active: bool = True
    auto_apply: bool = False


class RuleResponse(BaseModel):
    """Règle de catégorisation."""

    id: str
    tenant_id: str
    name: str
    rule_type: str
    priority: int
    keywords: list[str] = Field(default_factory=list)
    pattern: Optional[str] = None
    amount_min: Optional[Decimal] = None
    amount_max: Optional[Decimal] = None
    transaction_type: Optional[str] = None
    account_code: Optional[str] = None
    category: Optional[str] = None
    is_active: bool
    auto_apply: bool
    usage_count: int
    last_used: Optional[str] = None


class StatsResponse(BaseModel):
    """Statistiques de catégorisation."""

    total_rules: int
    active_rules: int
    auto_apply_rules: int
    most_used_rules: list[dict] = Field(default_factory=list)


# =============================================================================
# DEPENDENCIES
# =============================================================================


def get_categorization_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
) -> CategorizationService:
    """Dépendance pour obtenir le service de catégorisation."""
    return CategorizationService(db=db, tenant_id=context.tenant_id)


# =============================================================================
# HELPERS
# =============================================================================


def request_to_transaction(req: TransactionRequest) -> Transaction:
    """Convertit une requête en Transaction."""
    try:
        trans_type = TransactionType(req.transaction_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type de transaction invalide: {req.transaction_type}. Valeurs: debit, credit",
        )

    try:
        trans_date = datetime.fromisoformat(req.date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format de date invalide. Utilisez ISO format (YYYY-MM-DD)",
        )

    return Transaction(
        id=req.id,
        label=req.label,
        amount=req.amount,
        date=trans_date,
        transaction_type=trans_type,
        reference=req.reference,
        counterpart_name=req.counterpart_name,
        counterpart_iban=req.counterpart_iban,
        bank_account_id=req.bank_account_id,
    )


def result_to_response(result) -> CategorizationResponse:
    """Convertit un résultat en réponse."""
    suggestions = [
        CategorySuggestionResponse(
            account_code=s.account_code,
            account_name=s.account_name,
            category=s.category,
            confidence=s.confidence,
            match_confidence=s.match_confidence.value,
            rule_id=s.rule_id,
            rule_name=s.rule_name,
            reason=s.reason,
        )
        for s in result.suggestions
    ]

    return CategorizationResponse(
        success=result.success,
        transaction_id=result.transaction_id,
        auto_applied=result.auto_applied,
        applied_account_code=result.applied_account_code,
        applied_account_name=result.applied_account_name,
        applied_category=result.applied_category,
        applied_rule_id=result.applied_rule_id,
        suggestions=suggestions,
        confidence=result.confidence,
        match_confidence=result.match_confidence.value,
        error=result.error,
    )


def rule_to_response(rule: CategorizationRule) -> RuleResponse:
    """Convertit une règle en réponse."""
    return RuleResponse(
        id=rule.id,
        tenant_id=rule.tenant_id,
        name=rule.name,
        rule_type=rule.rule_type.value,
        priority=rule.priority,
        keywords=rule.keywords,
        pattern=rule.pattern,
        amount_min=rule.amount_min,
        amount_max=rule.amount_max,
        transaction_type=rule.transaction_type.value if rule.transaction_type else None,
        account_code=rule.account_code,
        category=rule.category,
        is_active=rule.is_active,
        auto_apply=rule.auto_apply,
        usage_count=rule.usage_count,
        last_used=rule.last_used.isoformat() if rule.last_used else None,
    )


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post(
    "/categorize",
    response_model=CategorizationResponse,
    summary="Catégoriser une transaction",
    description="Analyse une transaction et suggère des comptes comptables.",
)
async def categorize_transaction(
    request: TransactionRequest,
    auto_apply: bool = Query(False, description="Appliquer automatiquement si confiance élevée"),
    service: CategorizationService = Depends(get_categorization_service),
):
    """
    Catégorise une transaction bancaire.

    Retourne des suggestions de comptes comptables basées sur:
    - Règles personnalisées du tenant
    - Patterns par défaut (salaires, loyers, etc.)
    - Historique des catégorisations similaires

    Si auto_apply=True et confiance >= 95%, applique automatiquement.
    """
    transaction = request_to_transaction(request)
    result = await service.categorize_transaction(transaction, auto_apply)
    return result_to_response(result)


@router.post(
    "/batch",
    response_model=BatchCategorizationResponse,
    summary="Catégoriser un lot de transactions",
    description="Catégorise plusieurs transactions en une seule requête.",
)
async def categorize_batch(
    request: BatchCategorizationRequest,
    service: CategorizationService = Depends(get_categorization_service),
):
    """
    Catégorise un lot de transactions.

    Utile pour traiter un relevé bancaire complet.
    """
    transactions = [request_to_transaction(t) for t in request.transactions]
    results = await service.categorize_batch(transactions, request.auto_apply)

    responses = [result_to_response(r) for r in results]
    auto_applied = sum(1 for r in results if r.auto_applied)
    categorized = sum(1 for r in results if r.suggestions)

    return BatchCategorizationResponse(
        total=len(results),
        categorized=categorized,
        auto_applied=auto_applied,
        results=responses,
    )


@router.get(
    "/rules",
    response_model=list[RuleResponse],
    summary="Lister les règles de catégorisation",
    description="Retourne les règles de catégorisation du tenant.",
)
async def list_rules(
    active_only: bool = Query(True, description="Ne retourner que les règles actives"),
    service: CategorizationService = Depends(get_categorization_service),
):
    """
    Liste les règles de catégorisation.

    Les règles définissent comment catégoriser automatiquement les transactions
    en fonction de leur libellé, montant, IBAN, etc.
    """
    rules = await service.list_rules(active_only)
    return [rule_to_response(r) for r in rules]


@router.post(
    "/rules",
    response_model=RuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une règle de catégorisation",
    description="Crée une nouvelle règle personnalisée.",
)
async def create_rule(
    request: RuleRequest,
    service: CategorizationService = Depends(get_categorization_service),
):
    """
    Crée une nouvelle règle de catégorisation.

    Types de règles:
    - **keyword**: Correspond si un mot-clé est présent dans le libellé
    - **pattern**: Correspond si le libellé match une expression régulière
    - **amount_range**: Correspond si le montant est dans une plage
    - **vendor/customer**: Correspond si le partenaire match
    - **iban**: Correspond si l'IBAN du compte tiers match
    - **combined**: Combinaison de plusieurs critères
    """
    try:
        rule_type = RuleType(request.rule_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type de règle invalide: {request.rule_type}",
        )

    trans_type = None
    if request.transaction_type:
        try:
            trans_type = TransactionType(request.transaction_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Type de transaction invalide: {request.transaction_type}",
            )

    rule = CategorizationRule(
        id="",  # Sera généré
        tenant_id="",  # Sera défini par le service
        name=request.name,
        rule_type=rule_type,
        priority=request.priority,
        keywords=request.keywords,
        pattern=request.pattern,
        amount_min=request.amount_min,
        amount_max=request.amount_max,
        transaction_type=trans_type,
        iban=request.iban,
        partner_id=request.partner_id,
        account_code=request.account_code,
        account_id=request.account_id,
        category=request.category,
        tax_code=request.tax_code,
        journal_id=request.journal_id,
        is_active=request.is_active,
        auto_apply=request.auto_apply,
    )

    created = await service.create_rule(rule)
    return rule_to_response(created)


@router.put(
    "/rules/{rule_id}",
    response_model=RuleResponse,
    summary="Modifier une règle",
    description="Met à jour une règle existante.",
)
async def update_rule(
    rule_id: str,
    request: RuleRequest,
    service: CategorizationService = Depends(get_categorization_service),
):
    """
    Met à jour une règle de catégorisation existante.
    """
    updates = request.model_dump(exclude_unset=True)

    # Convertir les types
    if "rule_type" in updates:
        try:
            updates["rule_type"] = RuleType(updates["rule_type"].lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Type de règle invalide: {updates['rule_type']}",
            )

    if "transaction_type" in updates and updates["transaction_type"]:
        try:
            updates["transaction_type"] = TransactionType(updates["transaction_type"].lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Type de transaction invalide: {updates['transaction_type']}",
            )

    updated = await service.update_rule(rule_id, updates)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Règle non trouvée: {rule_id}",
        )

    return rule_to_response(updated)


@router.delete(
    "/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une règle",
    description="Supprime une règle de catégorisation.",
)
async def delete_rule(
    rule_id: str,
    service: CategorizationService = Depends(get_categorization_service),
):
    """
    Supprime une règle de catégorisation.
    """
    deleted = await service.delete_rule(rule_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Règle non trouvée: {rule_id}",
        )


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Statistiques de catégorisation",
    description="Retourne les statistiques d'utilisation des règles.",
)
async def get_stats(
    service: CategorizationService = Depends(get_categorization_service),
):
    """
    Retourne les statistiques de catégorisation.

    Inclut:
    - Nombre de règles actives
    - Règles les plus utilisées
    - Taux d'application automatique
    """
    stats = await service.get_stats()
    return StatsResponse(**stats)


@router.get(
    "/patterns",
    summary="Patterns par défaut",
    description="Retourne les patterns de catégorisation par défaut.",
)
async def get_default_patterns():
    """
    Retourne les patterns de catégorisation par défaut.

    Ces patterns sont utilisés comme fallback quand aucune règle
    personnalisée ne correspond.
    """
    from .service import DefaultPatterns

    return {
        "categories": [
            {
                "id": "salary",
                "name": "Salaires",
                "account_code": "641100",
                "patterns": DefaultPatterns.SALARY,
            },
            {
                "id": "rent",
                "name": "Loyers",
                "account_code": "613200",
                "patterns": DefaultPatterns.RENT,
            },
            {
                "id": "bank_fees",
                "name": "Frais bancaires",
                "account_code": "627100",
                "patterns": DefaultPatterns.BANK_FEES,
            },
            {
                "id": "telecom",
                "name": "Télécommunications",
                "account_code": "626200",
                "patterns": DefaultPatterns.TELECOM,
            },
            {
                "id": "energy",
                "name": "Énergie",
                "account_code": "606100",
                "patterns": DefaultPatterns.ENERGY,
            },
            {
                "id": "insurance",
                "name": "Assurances",
                "account_code": "616100",
                "patterns": DefaultPatterns.INSURANCE,
            },
            {
                "id": "taxes",
                "name": "Impôts et taxes",
                "account_code": "631000",
                "patterns": DefaultPatterns.TAXES,
            },
        ],
    }


@router.get(
    "/health",
    summary="Health check catégorisation",
    description="Vérifie que le service de catégorisation est fonctionnel.",
)
async def health_check():
    """Health check pour le service de catégorisation."""
    return {
        "status": "healthy",
        "service": "finance-auto-categorization",
        "features": [
            "rule_based_categorization",
            "pattern_matching",
            "historical_learning",
            "auto_apply",
            "batch_processing",
        ],
        "rule_types": ["keyword", "pattern", "amount_range", "vendor", "customer", "iban", "combined"],
    }
