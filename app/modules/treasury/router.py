"""
AZALS MODULE - TREASURY: Router
================================

API REST pour la gestion de la trésorerie.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.models import User

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


router = APIRouter(prefix="/treasury", tags=["Treasury - Trésorerie"])


def get_treasury_service(db: Session, tenant_id: str) -> TreasuryService:
    """Factory pour créer le service Treasury."""
    return TreasuryService(db, tenant_id)


# ============================================================================
# ENDPOINTS SUMMARY / DASHBOARD
# ============================================================================

@router.get("/summary", response_model=TreasurySummary)
async def get_treasury_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtenir le résumé de trésorerie (dashboard)."""
    service = get_treasury_service(db, current_user.tenant_id)
    return service.get_summary()


@router.get("/forecast", response_model=list[ForecastData])
async def get_forecast(
    days: int = Query(30, ge=1, le=365, description="Nombre de jours de prévision"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtenir les prévisions de trésorerie."""
    service = get_treasury_service(db, current_user.tenant_id)
    return service.get_forecast(days)


# ============================================================================
# ENDPOINTS BANK ACCOUNTS
# ============================================================================

@router.post("/accounts", response_model=BankAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    data: BankAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un nouveau compte bancaire."""
    service = get_treasury_service(db, current_user.tenant_id)

    try:
        return service.create_account(data, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/accounts", response_model=PaginatedBankAccounts)
async def list_accounts(
    is_active: Optional[bool] = Query(None, description="Filtrer par statut actif"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100, alias="page_size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les comptes bancaires."""
    service = get_treasury_service(db, current_user.tenant_id)
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
    current_user: User = Depends(get_current_user)
):
    """Récupérer un compte bancaire."""
    service = get_treasury_service(db, current_user.tenant_id)
    account = service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Compte bancaire non trouvé")
    return account


@router.put("/accounts/{account_id}", response_model=BankAccountResponse)
async def update_account(
    account_id: UUID,
    data: BankAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un compte bancaire."""
    service = get_treasury_service(db, current_user.tenant_id)
    account = service.update_account(account_id, data)
    if not account:
        raise HTTPException(status_code=404, detail="Compte bancaire non trouvé")
    return account


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un compte bancaire (soft delete)."""
    service = get_treasury_service(db, current_user.tenant_id)

    try:
        success = service.delete_account(account_id)
        if not success:
            raise HTTPException(status_code=404, detail="Compte bancaire non trouvé")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# ENDPOINTS TRANSACTIONS
# ============================================================================

@router.post("/transactions", response_model=BankTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: BankTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une nouvelle transaction bancaire."""
    service = get_treasury_service(db, current_user.tenant_id)

    try:
        return service.create_transaction(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/transactions", response_model=PaginatedBankTransactions)
async def list_transactions(
    account_id: Optional[UUID] = Query(None, description="Filtrer par compte"),
    transaction_type: Optional[TransactionType] = Query(None, alias="type", description="Filtrer par type"),
    reconciled: Optional[bool] = Query(None, description="Filtrer par statut rapproché"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100, alias="page_size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les transactions bancaires."""
    service = get_treasury_service(db, current_user.tenant_id)
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
    current_user: User = Depends(get_current_user)
):
    """Lister les transactions d'un compte spécifique."""
    service = get_treasury_service(db, current_user.tenant_id)

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
    current_user: User = Depends(get_current_user)
):
    """Récupérer une transaction bancaire."""
    service = get_treasury_service(db, current_user.tenant_id)
    transaction = service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction non trouvée")
    return transaction


@router.put("/transactions/{transaction_id}", response_model=BankTransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    data: BankTransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour une transaction bancaire."""
    service = get_treasury_service(db, current_user.tenant_id)
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
    current_user: User = Depends(get_current_user)
):
    """Rapprocher une transaction avec un document."""
    service = get_treasury_service(db, current_user.tenant_id)

    try:
        return service.reconcile_transaction(transaction_id, data, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/transactions/{transaction_id}/unreconcile", response_model=BankTransactionResponse)
async def unreconcile_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Annuler le rapprochement d'une transaction."""
    service = get_treasury_service(db, current_user.tenant_id)

    try:
        return service.unreconcile_transaction(transaction_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
