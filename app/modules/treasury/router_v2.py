"""
AZALS MODULE - TREASURY: Router v2 (MIGRÉ CORE SaaS)
=====================================================

API REST pour la gestion de la trésorerie - Version CORE SaaS v2.

✅ MIGRATION 100% COMPLÈTE vers CORE SaaS (Phase 2.2):
- Utilise get_saas_context() au lieu de get_current_user()
- 14/14 endpoints protégés migrés vers pattern CORE ✅
- Service adapté pour utiliser context.tenant_id + context.user_id

ENDPOINTS MIGRÉS (14):
- Summary/Forecast (2): summary + forecast
- Bank Accounts (5): CRUD + soft delete
- Transactions (7): CRUD + reconcile/unreconcile + list by account
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext

from .models import TransactionType
from .schemas import (
    BankAccountCreate,
    BankAccountResponse,
    BankAccountUpdate,
    BankTransactionCreate,
    BankTransactionResponse,
    BankTransactionUpdate,
    ForecastData,
    PaginatedBankAccounts,
    PaginatedBankTransactions,
    ReconciliationRequest,
    TreasurySummary,
)
from .service import TreasuryService


router = APIRouter(prefix="/v2/treasury", tags=["Treasury v2 - CORE SaaS"])


# ============================================================================
# FACTORY
# ============================================================================

def get_treasury_service(db: Session, tenant_id: str, user_id: str) -> TreasuryService:
    """
    Factory pour créer le service Treasury (CORE SaaS v2).

    ✅ MIGRÉ CORE SaaS:
    - Utilise tenant_id + user_id pour isolation tenant et audit
    """
    return TreasuryService(db, tenant_id, user_id)


# ============================================================================
# ENDPOINTS SUMMARY / DASHBOARD
# ============================================================================

@router.get("/summary", response_model=TreasurySummary)
async def get_treasury_summary(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Obtenir le résumé de trésorerie (dashboard).

    ✅ MIGRÉ CORE SaaS v2:
    - Utilise SaaSContext pour isolation tenant
    """
    service = get_treasury_service(db, context.tenant_id, str(context.user_id))
    return service.get_summary()


@router.get("/forecast", response_model=list[ForecastData])
async def get_forecast(
    days: int = Query(30, ge=1, le=365, description="Nombre de jours de prévision"),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Obtenir les prévisions de trésorerie.

    ✅ MIGRÉ CORE SaaS v2:
    - Utilise SaaSContext pour isolation tenant
    """
    service = get_treasury_service(db, context.tenant_id, str(context.user_id))
    return service.get_forecast(days)


# ============================================================================
# ENDPOINTS BANK ACCOUNTS
# ============================================================================

@router.post("/accounts", response_model=BankAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    data: BankAccountCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer un nouveau compte bancaire.

    ✅ MIGRÉ CORE SaaS v2:
    - Utilise context.user_id pour audit trail
    """
    service = get_treasury_service(db, context.tenant_id, str(context.user_id))
    return service.create_account(data, context.user_id)


@router.get("/accounts", response_model=PaginatedBankAccounts)
async def list_accounts(
    is_active: Optional[bool] = Query(None, description="Filtrer par statut actif"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100, alias="page_size"),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les comptes bancaires.

    ✅ MIGRÉ CORE SaaS v2:
    - Utilise SaaSContext pour isolation tenant
    """
    service = get_treasury_service(db, context.tenant_id, str(context.user_id))
    items, total = service.list_accounts(is_active, page, per_page)

    pages = (total + per_page - 1) // per_page

    return PaginatedBankAccounts(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        items=items
    )


@router.get("/accounts/{account_id}", response_model=BankAccountResponse)
async def get_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Récupérer un compte bancaire.

    ✅ MIGRÉ CORE SaaS v2:
    - Utilise SaaSContext pour isolation tenant
    """
    service = get_treasury_service(db, context.tenant_id, str(context.user_id))
    account = service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Compte bancaire non trouvé")
    return account


@router.put("/accounts/{account_id}", response_model=BankAccountResponse)
async def update_account(
    account_id: UUID,
    data: BankAccountUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Mettre à jour un compte bancaire.

    ✅ MIGRÉ CORE SaaS v2:
    - Utilise SaaSContext pour isolation tenant
    """
    service = get_treasury_service(db, context.tenant_id, str(context.user_id))
    account = service.update_account(account_id, data)
    if not account:
        raise HTTPException(status_code=404, detail="Compte bancaire non trouvé")
    return account


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Supprimer un compte bancaire (soft delete).

    ✅ MIGRÉ CORE SaaS v2:
    - Utilise SaaSContext pour isolation tenant
    """
    service = get_treasury_service(db, context.tenant_id, str(context.user_id))
    success = service.delete_account(account_id)
    if not success:
        raise HTTPException(status_code=404, detail="Compte bancaire non trouvé")


# ============================================================================
# ENDPOINTS TRANSACTIONS
# ============================================================================

@router.post("/transactions", response_model=BankTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: BankTransactionCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer une nouvelle transaction bancaire.

    ✅ MIGRÉ CORE SaaS v2:
    - Utilise SaaSContext pour isolation tenant
    """
    service = get_treasury_service(db, context.tenant_id, str(context.user_id))
    return service.create_transaction(data)


@router.get("/transactions", response_model=PaginatedBankTransactions)
async def list_transactions(
    account_id: Optional[UUID] = Query(None, description="Filtrer par compte"),
    transaction_type: Optional[TransactionType] = Query(None, alias="type", description="Filtrer par type"),
    reconciled: Optional[bool] = Query(None, description="Filtrer par statut rapproché"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100, alias="page_size"),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les transactions bancaires.

    ✅ MIGRÉ CORE SaaS v2:
    - Utilise SaaSContext pour isolation tenant
    """
    service = get_treasury_service(db, context.tenant_id, str(context.user_id))
    items, total = service.list_transactions(account_id, transaction_type, reconciled, page, per_page)

    pages = (total + per_page - 1) // per_page

    return PaginatedBankTransactions(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        items=items
    )


@router.get("/accounts/{account_id}/transactions", response_model=PaginatedBankTransactions)
async def list_account_transactions(
    account_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100, alias="page_size"),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les transactions d'un compte spécifique.

    ✅ MIGRÉ CORE SaaS v2:
    - Utilise SaaSContext pour isolation tenant
    """
    service = get_treasury_service(db, context.tenant_id, str(context.user_id))

    # Vérifier que le compte existe
    account = service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Compte bancaire non trouvé")

    items, total = service.list_transactions(account_id=account_id, page=page, per_page=per_page)

    pages = (total + per_page - 1) // per_page

    return PaginatedBankTransactions(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        items=items
    )


@router.get("/transactions/{transaction_id}", response_model=BankTransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Récupérer une transaction bancaire.

    ✅ MIGRÉ CORE SaaS v2:
    - Utilise SaaSContext pour isolation tenant
    """
    service = get_treasury_service(db, context.tenant_id, str(context.user_id))
    transaction = service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction non trouvée")
    return transaction


@router.put("/transactions/{transaction_id}", response_model=BankTransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    data: BankTransactionUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Mettre à jour une transaction bancaire.

    ✅ MIGRÉ CORE SaaS v2:
    - Utilise SaaSContext pour isolation tenant
    """
    service = get_treasury_service(db, context.tenant_id, str(context.user_id))
    transaction = service.update_transaction(transaction_id, data)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction non trouvée")
    return transaction


# ============================================================================
# ENDPOINTS RECONCILIATION
# ============================================================================

@router.post("/transactions/{transaction_id}/reconcile", response_model=BankTransactionResponse)
async def reconcile_transaction(
    transaction_id: UUID,
    data: ReconciliationRequest,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Rapprocher une transaction avec un document.

    ✅ MIGRÉ CORE SaaS v2:
    - Utilise context.user_id pour audit trail
    """
    service = get_treasury_service(db, context.tenant_id, str(context.user_id))
    return service.reconcile_transaction(transaction_id, data, context.user_id)


@router.post("/transactions/{transaction_id}/unreconcile", response_model=BankTransactionResponse)
async def unreconcile_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Annuler le rapprochement d'une transaction.

    ✅ MIGRÉ CORE SaaS v2:
    - Utilise SaaSContext pour isolation tenant
    """
    service = get_treasury_service(db, context.tenant_id, str(context.user_id))
    return service.unreconcile_transaction(transaction_id)
