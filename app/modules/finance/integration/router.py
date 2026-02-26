"""
AZALSCORE Finance Integration Router V3
========================================

Endpoints REST pour l'intégration Finance ↔ Comptabilité/Facturation.

Endpoints:
- GET  /v3/finance/integration/mappings - Liste des mappings
- POST /v3/finance/integration/mappings - Créer un mapping
- DELETE /v3/finance/integration/mappings/{id} - Supprimer un mapping
- POST /v3/finance/integration/sync/to-accounting - Sync vers compta
- POST /v3/finance/integration/sync/from-accounting - Import compta
- POST /v3/finance/integration/sync/invoice-payment - Paiement facture
- POST /v3/finance/integration/validate/balance - Valider équilibre
- POST /v3/finance/integration/validate/entries - Valider écritures
- GET  /v3/finance/integration/history - Historique sync
- GET  /v3/finance/integration/stats - Statistiques
- GET  /v3/finance/integration/health - Health check
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
    FinanceIntegrationService,
    IntegrationMapping,
    SyncResult,
    SyncDirection,
    SyncStatus,
    MappingType,
    TransactionType,
    FinanceTransaction,
    AccountingEntry,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v3/finance/integration", tags=["Finance Integration"])


# =============================================================================
# SCHEMAS
# =============================================================================


class CreateMappingRequest(BaseModel):
    """Requête de création de mapping."""

    mapping_type: MappingType = Field(..., description="Type de mapping")
    source_code: str = Field(..., min_length=1, description="Code source")
    target_code: str = Field(..., min_length=1, description="Code cible")
    source_system: str = Field("finance", description="Système source")
    target_system: str = Field("accounting", description="Système cible")
    description: Optional[str] = Field(None, description="Description")
    priority: int = Field(0, ge=0, description="Priorité")
    conditions: Optional[dict] = Field(None, description="Conditions")


class MappingResponse(BaseModel):
    """Réponse mapping."""

    id: str
    mapping_type: str
    source_code: str
    target_code: str
    source_system: str
    target_system: str
    description: Optional[str] = None
    is_active: bool
    priority: int
    created_at: str


class TransactionRequest(BaseModel):
    """Transaction financière pour sync."""

    id: str = Field(..., description="ID de la transaction")
    transaction_type: TransactionType = Field(..., description="Type")
    date: datetime = Field(..., description="Date")
    amount: Decimal = Field(..., gt=0, description="Montant")
    currency: str = Field("EUR", min_length=3, max_length=3)
    description: str = Field(..., min_length=1)
    bank_account: Optional[str] = None
    counterparty: Optional[str] = None
    category: Optional[str] = None
    reference: Optional[str] = None
    tax_amount: Optional[Decimal] = None
    metadata: Optional[dict] = None


class SyncToAccountingRequest(BaseModel):
    """Requête de synchronisation vers comptabilité."""

    transactions: list[TransactionRequest]
    create_entries: bool = Field(True, description="Créer les écritures")


class AccountingEntryRequest(BaseModel):
    """Écriture comptable pour import."""

    id: str
    journal_code: str
    date: datetime
    reference: str
    description: str
    debit_account: str
    credit_account: str
    amount: Decimal
    currency: str = "EUR"
    tax_code: Optional[str] = None
    cost_center: Optional[str] = None


class SyncFromAccountingRequest(BaseModel):
    """Requête d'import depuis comptabilité."""

    entries: list[AccountingEntryRequest]


class InvoicePaymentRequest(BaseModel):
    """Requête de paiement facture."""

    invoice_id: str = Field(..., description="ID de la facture")
    payment_amount: Decimal = Field(..., gt=0, description="Montant payé")
    payment_date: datetime = Field(..., description="Date du paiement")
    payment_method: str = Field("bank_transfer", description="Méthode de paiement")


class ValidateBalanceRequest(BaseModel):
    """Requête de validation d'équilibre."""

    start_date: datetime
    end_date: datetime


class ValidateEntriesRequest(BaseModel):
    """Requête de validation d'écritures."""

    entries: list[AccountingEntryRequest]


class EntryResponse(BaseModel):
    """Écriture comptable en réponse."""

    id: str
    journal_code: str
    date: str
    reference: str
    description: str
    debit_account: str
    credit_account: str
    amount: Decimal
    currency: str


class SyncResultResponse(BaseModel):
    """Résultat de synchronisation."""

    success: bool
    sync_id: str
    direction: str
    status: str
    records_processed: int
    records_created: int
    records_updated: int
    records_skipped: int
    records_failed: int
    errors: list[str] = Field(default_factory=list)
    entries: list[EntryResponse] = Field(default_factory=list)
    started_at: str
    completed_at: Optional[str] = None


class ValidationResponse(BaseModel):
    """Résultat de validation."""

    is_valid: bool
    validation_type: str
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    details: dict = Field(default_factory=dict)


class IntegrationStatsResponse(BaseModel):
    """Statistiques d'intégration."""

    total_syncs: int
    successful_syncs: int
    failed_syncs: int
    success_rate: str
    total_records_processed: int
    total_records_created: int
    total_records_failed: int
    mappings_count: int


# =============================================================================
# DEPENDENCIES
# =============================================================================


def get_integration_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
) -> FinanceIntegrationService:
    """Dépendance pour obtenir le service d'intégration."""
    return FinanceIntegrationService(db=db, tenant_id=context.tenant_id)


# =============================================================================
# HELPERS
# =============================================================================


def mapping_to_response(mapping: IntegrationMapping) -> MappingResponse:
    """Convertit un mapping en réponse."""
    return MappingResponse(
        id=mapping.id,
        mapping_type=mapping.mapping_type.value,
        source_code=mapping.source_code,
        target_code=mapping.target_code,
        source_system=mapping.source_system,
        target_system=mapping.target_system,
        description=mapping.description,
        is_active=mapping.is_active,
        priority=mapping.priority,
        created_at=mapping.created_at.isoformat(),
    )


def entry_to_response(entry: AccountingEntry) -> EntryResponse:
    """Convertit une écriture en réponse."""
    return EntryResponse(
        id=entry.id,
        journal_code=entry.journal_code,
        date=entry.date.isoformat(),
        reference=entry.reference,
        description=entry.description,
        debit_account=entry.debit_account,
        credit_account=entry.credit_account,
        amount=entry.amount,
        currency=entry.currency,
    )


def sync_result_to_response(result: SyncResult) -> SyncResultResponse:
    """Convertit un résultat de sync en réponse."""
    return SyncResultResponse(
        success=result.success,
        sync_id=result.sync_id,
        direction=result.direction.value,
        status=result.status.value,
        records_processed=result.records_processed,
        records_created=result.records_created,
        records_updated=result.records_updated,
        records_skipped=result.records_skipped,
        records_failed=result.records_failed,
        errors=result.errors,
        entries=[entry_to_response(e) for e in result.entries],
        started_at=result.started_at.isoformat(),
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
    )


# =============================================================================
# ENDPOINTS - MAPPINGS
# =============================================================================


@router.get(
    "/mappings",
    response_model=list[MappingResponse],
    summary="Liste des mappings",
    description="Retourne toutes les règles de mapping.",
)
async def list_mappings(
    mapping_type: Optional[MappingType] = Query(None, description="Filtrer par type"),
    source_system: Optional[str] = Query(None, description="Filtrer par système source"),
    service: FinanceIntegrationService = Depends(get_integration_service),
):
    """Liste les mappings d'intégration."""
    mappings = await service.list_mappings(
        mapping_type=mapping_type,
        source_system=source_system,
    )
    return [mapping_to_response(m) for m in mappings]


@router.post(
    "/mappings",
    response_model=MappingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un mapping",
    description="Crée une nouvelle règle de mapping.",
)
async def create_mapping(
    request: CreateMappingRequest,
    service: FinanceIntegrationService = Depends(get_integration_service),
):
    """
    Crée une règle de mapping personnalisée.

    Types de mapping:
    - **account**: Comptes bancaires → comptables
    - **journal**: Types de transactions → journaux
    - **tax_code**: Codes TVA
    - **cost_center**: Centres de coût
    - **payment_method**: Méthodes de paiement
    """
    mapping = await service.create_mapping(
        mapping_type=request.mapping_type,
        source_code=request.source_code,
        target_code=request.target_code,
        source_system=request.source_system,
        target_system=request.target_system,
        description=request.description,
        priority=request.priority,
        conditions=request.conditions,
    )

    return mapping_to_response(mapping)


@router.delete(
    "/mappings/{mapping_id}",
    response_model=dict,
    summary="Supprimer un mapping",
    description="Supprime une règle de mapping.",
)
async def delete_mapping(
    mapping_id: str,
    service: FinanceIntegrationService = Depends(get_integration_service),
):
    """Supprime une règle de mapping."""
    success = await service.delete_mapping(mapping_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping non trouvé",
        )

    return {"success": True, "message": "Mapping supprimé"}


@router.get(
    "/mappings/resolve",
    summary="Résoudre un mapping",
    description="Retourne le code cible pour un code source.",
)
async def resolve_mapping(
    mapping_type: MappingType = Query(..., description="Type de mapping"),
    source_code: str = Query(..., description="Code source"),
    source_system: str = Query("finance", description="Système source"),
    service: FinanceIntegrationService = Depends(get_integration_service),
):
    """Résout un mapping vers son code cible."""
    target_code = service.resolve_mapping(mapping_type, source_code, source_system)

    if not target_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping non trouvé",
        )

    return {
        "source_code": source_code,
        "target_code": target_code,
        "mapping_type": mapping_type.value,
    }


# =============================================================================
# ENDPOINTS - SYNCHRONISATION
# =============================================================================


@router.post(
    "/sync/to-accounting",
    response_model=SyncResultResponse,
    summary="Synchroniser vers comptabilité",
    description="Synchronise des transactions financières vers la comptabilité.",
)
async def sync_to_accounting(
    request: SyncToAccountingRequest,
    service: FinanceIntegrationService = Depends(get_integration_service),
):
    """
    Synchronise les transactions vers la comptabilité.

    Génère les écritures comptables correspondantes.
    """
    # Convertir les requêtes en objets FinanceTransaction
    transactions = []
    for tx_req in request.transactions:
        tx = FinanceTransaction(
            id=tx_req.id,
            tenant_id=service.tenant_id,
            transaction_type=tx_req.transaction_type,
            date=tx_req.date,
            amount=tx_req.amount,
            currency=tx_req.currency,
            description=tx_req.description,
            bank_account=tx_req.bank_account,
            counterparty=tx_req.counterparty,
            category=tx_req.category,
            reference=tx_req.reference,
            tax_amount=tx_req.tax_amount,
            metadata=tx_req.metadata or {},
        )
        transactions.append(tx)

    result = await service.sync_to_accounting(
        transactions=transactions,
        create_entries=request.create_entries,
    )

    return sync_result_to_response(result)


@router.post(
    "/sync/from-accounting",
    response_model=SyncResultResponse,
    summary="Importer depuis comptabilité",
    description="Importe des écritures comptables vers Finance.",
)
async def sync_from_accounting(
    request: SyncFromAccountingRequest,
    service: FinanceIntegrationService = Depends(get_integration_service),
):
    """Importe des écritures comptables."""
    # Convertir les requêtes en objets AccountingEntry
    entries = []
    for entry_req in request.entries:
        entry = AccountingEntry(
            id=entry_req.id,
            tenant_id=service.tenant_id,
            journal_code=entry_req.journal_code,
            date=entry_req.date,
            reference=entry_req.reference,
            description=entry_req.description,
            debit_account=entry_req.debit_account,
            credit_account=entry_req.credit_account,
            amount=entry_req.amount,
            currency=entry_req.currency,
            tax_code=entry_req.tax_code,
            cost_center=entry_req.cost_center,
        )
        entries.append(entry)

    result = await service.sync_from_accounting(entries=entries)

    return sync_result_to_response(result)


@router.post(
    "/sync/invoice-payment",
    response_model=SyncResultResponse,
    summary="Synchroniser paiement facture",
    description="Synchronise un paiement de facture.",
)
async def sync_invoice_payment(
    request: InvoicePaymentRequest,
    service: FinanceIntegrationService = Depends(get_integration_service),
):
    """
    Synchronise un paiement de facture.

    Crée l'écriture de règlement client.
    """
    result = await service.sync_invoice_payment(
        invoice_id=request.invoice_id,
        payment_amount=request.payment_amount,
        payment_date=request.payment_date,
        payment_method=request.payment_method,
    )

    return sync_result_to_response(result)


# =============================================================================
# ENDPOINTS - VALIDATION
# =============================================================================


@router.post(
    "/validate/balance",
    response_model=ValidationResponse,
    summary="Valider l'équilibre",
    description="Valide l'équilibre Finance ↔ Comptabilité.",
)
async def validate_balance(
    request: ValidateBalanceRequest,
    service: FinanceIntegrationService = Depends(get_integration_service),
):
    """
    Valide que les totaux Finance et Comptabilité correspondent.
    """
    result = await service.validate_balance(
        start_date=request.start_date,
        end_date=request.end_date,
    )

    return ValidationResponse(
        is_valid=result.is_valid,
        validation_type=result.validation_type,
        errors=result.errors,
        warnings=result.warnings,
        details=result.details,
    )


@router.post(
    "/validate/entries",
    response_model=ValidationResponse,
    summary="Valider des écritures",
    description="Valide une liste d'écritures comptables.",
)
async def validate_entries(
    request: ValidateEntriesRequest,
    service: FinanceIntegrationService = Depends(get_integration_service),
):
    """Valide des écritures avant import."""
    entries = []
    for entry_req in request.entries:
        entry = AccountingEntry(
            id=entry_req.id,
            tenant_id=service.tenant_id,
            journal_code=entry_req.journal_code,
            date=entry_req.date,
            reference=entry_req.reference,
            description=entry_req.description,
            debit_account=entry_req.debit_account,
            credit_account=entry_req.credit_account,
            amount=entry_req.amount,
            currency=entry_req.currency,
        )
        entries.append(entry)

    result = await service.validate_entries(entries=entries)

    return ValidationResponse(
        is_valid=result.is_valid,
        validation_type=result.validation_type,
        errors=result.errors,
        warnings=result.warnings,
        details=result.details,
    )


# =============================================================================
# ENDPOINTS - HISTORY & STATS
# =============================================================================


@router.get(
    "/history",
    response_model=list[SyncResultResponse],
    summary="Historique de synchronisation",
    description="Retourne l'historique des synchronisations.",
)
async def get_sync_history(
    direction: Optional[SyncDirection] = Query(None, description="Filtrer par direction"),
    sync_status: Optional[SyncStatus] = Query(None, alias="status", description="Filtrer par statut"),
    limit: int = Query(50, ge=1, le=500, description="Nombre max de résultats"),
    service: FinanceIntegrationService = Depends(get_integration_service),
):
    """Liste l'historique des synchronisations."""
    history = await service.get_sync_history(
        direction=direction,
        status=sync_status,
        limit=limit,
    )

    return [sync_result_to_response(r) for r in history]


@router.get(
    "/history/{sync_id}",
    response_model=SyncResultResponse,
    summary="Détails d'une synchronisation",
    description="Retourne les détails d'une synchronisation.",
)
async def get_sync_result(
    sync_id: str,
    service: FinanceIntegrationService = Depends(get_integration_service),
):
    """Récupère les détails d'une synchronisation."""
    result = await service.get_sync_result(sync_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Synchronisation non trouvée",
        )

    return sync_result_to_response(result)


@router.get(
    "/stats",
    response_model=IntegrationStatsResponse,
    summary="Statistiques d'intégration",
    description="Retourne les statistiques d'intégration.",
)
async def get_integration_stats(
    service: FinanceIntegrationService = Depends(get_integration_service),
):
    """Statistiques d'intégration Finance."""
    stats = await service.get_integration_stats()
    return IntegrationStatsResponse(**stats)


@router.get(
    "/health",
    summary="Health check intégration",
    description="Vérifie que le service d'intégration est fonctionnel.",
)
async def health_check():
    """Health check pour le service d'intégration."""
    return {
        "status": "healthy",
        "service": "finance-integration",
        "features": [
            "sync_to_accounting",
            "sync_from_accounting",
            "invoice_payment",
            "balance_validation",
            "entry_validation",
            "custom_mappings",
        ],
        "sync_directions": [d.value for d in SyncDirection],
        "mapping_types": [m.value for m in MappingType],
    }
