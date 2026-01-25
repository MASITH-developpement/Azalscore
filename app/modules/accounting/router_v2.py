"""
AZALS MODULE - ACCOUNTING: Router v2
=====================================

API REST pour la gestion comptable - CORE SaaS v2.
Migration vers SaaSContext pour l'authentification et l'isolation tenant.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext
from app.core.database import get_db

from .models import AccountType, EntryStatus, FiscalYearStatus
from .schemas import (
    AccountingSummary,
    ChartOfAccountsCreate,
    ChartOfAccountsResponse,
    ChartOfAccountsUpdate,
    FiscalYearCreate,
    FiscalYearResponse,
    FiscalYearUpdate,
    JournalEntryCreate,
    JournalEntryResponse,
    JournalEntryUpdate,
    PaginatedAccounts,
    PaginatedBalanceEntries,
    PaginatedFiscalYears,
    PaginatedJournalEntries,
    PaginatedLedgerAccounts,
)
from .service import AccountingService


router = APIRouter(
    prefix="/v2/accounting",
    tags=["Accounting v2 - CORE SaaS"]
)


def get_accounting_service(
    db: Session,
    tenant_id: str,
    user_id: str
) -> AccountingService:
    """Factory pour créer le service Accounting."""
    return AccountingService(db, tenant_id)


# ============================================================================
# ENDPOINTS SUMMARY / DASHBOARD
# ============================================================================

@router.get("/summary", response_model=AccountingSummary)
async def get_accounting_summary(
    fiscal_year_id: Optional[UUID] = Query(None, description="ID exercice comptable"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Obtenir le résumé comptable (dashboard)."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)
    return service.get_summary(fiscal_year_id)


# ============================================================================
# ENDPOINTS FISCAL YEARS
# ============================================================================

@router.post("/fiscal-years", response_model=FiscalYearResponse, status_code=status.HTTP_201_CREATED)
async def create_fiscal_year(
    data: FiscalYearCreate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Créer un nouvel exercice comptable."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)

    try:
        return service.create_fiscal_year(data, context.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/fiscal-years", response_model=PaginatedFiscalYears)
async def list_fiscal_years(
    status_filter: Optional[FiscalYearStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100, alias="page_size"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Lister les exercices comptables."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)
    items, total = service.list_fiscal_years(status_filter, page, per_page)

    pages = (total + per_page - 1) // per_page

    return PaginatedFiscalYears(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        items=items
    )


@router.get("/fiscal-years/{fiscal_year_id}", response_model=FiscalYearResponse)
async def get_fiscal_year(
    fiscal_year_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Récupérer un exercice comptable."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)
    fiscal_year = service.get_fiscal_year(fiscal_year_id)
    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Exercice comptable non trouvé")
    return fiscal_year


@router.put("/fiscal-years/{fiscal_year_id}", response_model=FiscalYearResponse)
async def update_fiscal_year(
    fiscal_year_id: UUID,
    data: FiscalYearUpdate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Mettre à jour un exercice comptable."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)

    try:
        fiscal_year = service.update_fiscal_year(fiscal_year_id, data)
        if not fiscal_year:
            raise HTTPException(status_code=404, detail="Exercice comptable non trouvé")
        return fiscal_year
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/fiscal-years/{fiscal_year_id}/close", response_model=FiscalYearResponse)
async def close_fiscal_year(
    fiscal_year_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Clôturer un exercice comptable."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)

    try:
        return service.close_fiscal_year(fiscal_year_id, context.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# ENDPOINTS CHART OF ACCOUNTS
# ============================================================================

@router.post("/chart-of-accounts", response_model=ChartOfAccountsResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    data: ChartOfAccountsCreate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Créer un nouveau compte comptable."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)

    try:
        return service.create_account(data, context.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/chart-of-accounts", response_model=PaginatedAccounts)
async def list_accounts(
    account_type: Optional[AccountType] = Query(None, alias="type"),
    account_class: Optional[str] = Query(None, alias="class", max_length=1),
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=500, alias="page_size"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Lister les comptes comptables."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)
    items, total = service.list_accounts(account_type, account_class, search, page, per_page)

    pages = (total + per_page - 1) // per_page

    return PaginatedAccounts(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        items=items
    )


@router.get("/chart-of-accounts/{account_number}", response_model=ChartOfAccountsResponse)
async def get_account(
    account_number: str,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Récupérer un compte comptable."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)
    account = service.get_account(account_number)
    if not account:
        raise HTTPException(status_code=404, detail="Compte comptable non trouvé")
    return account


@router.put("/chart-of-accounts/{account_number}", response_model=ChartOfAccountsResponse)
async def update_account(
    account_number: str,
    data: ChartOfAccountsUpdate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Mettre à jour un compte comptable."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)
    account = service.update_account(account_number, data)
    if not account:
        raise HTTPException(status_code=404, detail="Compte comptable non trouvé")
    return account


# ============================================================================
# ENDPOINTS JOURNAL ENTRIES
# ============================================================================

@router.post("/journal", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(
    data: JournalEntryCreate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Créer une nouvelle écriture comptable."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)

    try:
        return service.create_journal_entry(data, context.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/journal", response_model=PaginatedJournalEntries)
async def list_journal_entries(
    fiscal_year_id: Optional[UUID] = Query(None, description="ID exercice comptable"),
    journal_code: Optional[str] = Query(None, description="Code journal (VT, AC, BQ, etc.)"),
    status_filter: Optional[EntryStatus] = Query(None, alias="status"),
    period: Optional[str] = Query(None, description="Période (YYYY-MM)"),
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200, alias="page_size"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Lister les écritures comptables."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)
    items, total = service.list_journal_entries(
        fiscal_year_id, journal_code, status_filter, period, search, page, per_page
    )

    pages = (total + per_page - 1) // per_page

    return PaginatedJournalEntries(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        items=items
    )


@router.get("/journal/{entry_id}", response_model=JournalEntryResponse)
async def get_journal_entry(
    entry_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Récupérer une écriture comptable."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)
    entry = service.get_journal_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Écriture comptable non trouvée")
    return entry


@router.put("/journal/{entry_id}", response_model=JournalEntryResponse)
async def update_journal_entry(
    entry_id: UUID,
    data: JournalEntryUpdate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Mettre à jour une écriture comptable."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)

    try:
        entry = service.update_journal_entry(entry_id, data)
        if not entry:
            raise HTTPException(status_code=404, detail="Écriture comptable non trouvée")
        return entry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/journal/{entry_id}/post", response_model=JournalEntryResponse)
async def post_journal_entry(
    entry_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Comptabiliser une écriture (DRAFT → POSTED)."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)

    try:
        return service.post_journal_entry(entry_id, context.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/journal/{entry_id}/validate", response_model=JournalEntryResponse)
async def validate_journal_entry(
    entry_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Valider définitivement une écriture (POSTED → VALIDATED)."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)

    try:
        return service.validate_journal_entry(entry_id, context.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/journal/{entry_id}/cancel", response_model=JournalEntryResponse)
async def cancel_journal_entry(
    entry_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Annuler une écriture comptable."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)

    try:
        return service.cancel_journal_entry(entry_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# ENDPOINTS LEDGER (Grand Livre)
# ============================================================================

@router.get("/ledger", response_model=PaginatedLedgerAccounts)
async def get_ledger(
    fiscal_year_id: Optional[UUID] = Query(None, description="ID exercice comptable"),
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=500, alias="page_size"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Obtenir le grand livre (tous les comptes)."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)
    items, total = service.get_ledger(None, fiscal_year_id, page, per_page)

    pages = (total + per_page - 1) // per_page

    return PaginatedLedgerAccounts(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        items=items
    )


@router.get("/ledger/{account_number}", response_model=PaginatedLedgerAccounts)
async def get_ledger_by_account(
    account_number: str,
    fiscal_year_id: Optional[UUID] = Query(None, description="ID exercice comptable"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Obtenir le grand livre pour un compte spécifique."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)
    items, total = service.get_ledger(account_number, fiscal_year_id, 1, 1)

    if total == 0:
        raise HTTPException(status_code=404, detail="Compte non trouvé")

    return PaginatedLedgerAccounts(
        total=total,
        page=1,
        per_page=1,
        pages=1,
        items=items
    )


# ============================================================================
# ENDPOINTS BALANCE
# ============================================================================

@router.get("/balance", response_model=PaginatedBalanceEntries)
async def get_balance(
    fiscal_year_id: Optional[UUID] = Query(None, description="ID exercice comptable"),
    period: Optional[str] = Query(None, description="Période (YYYY-MM)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=500, alias="page_size"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Obtenir la balance générale."""
    service = get_accounting_service(db, context.tenant_id, context.user_id)
    items, total = service.get_balance(fiscal_year_id, period, page, per_page)

    pages = (total + per_page - 1) // per_page

    return PaginatedBalanceEntries(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        items=items
    )
