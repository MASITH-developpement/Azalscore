"""
AZALS - Accounting Router (CRUDRouter v3)
==========================================

Router complet pour le module Accounting (Comptabilite).
Compatible v1, v2, et v3 via app.azals.

Conformite : AZA-NF-006
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db
from app.core.pagination import PaginatedResponse

from .models import AccountType, EntryStatus, FiscalYearStatus
from .schemas import (
    AccountingStatus,
    AccountingSummary,
    BalanceEntry,
    ChartOfAccountsCreate,
    ChartOfAccountsResponse,
    ChartOfAccountsUpdate,
    FiscalYearCreate,
    FiscalYearResponse,
    FiscalYearUpdate,
    JournalEntryCreate,
    JournalEntryResponse,
    LedgerAccount,
)
from .service import AccountingService


# =============================================================================
# ROUTER PRINCIPAL
# =============================================================================

router = APIRouter(prefix="/accounting", tags=["Accounting - Comptabilite"])


# =============================================================================
# HELPER: Conversion Result -> HTTPException
# =============================================================================

def handle_result(result, success_status: int = 200):
    """
    Convertit un Result en reponse HTTP.
    """
    if not result.success:
        status_map = {
            "NOT_FOUND": 404,
            "DUPLICATE_CODE": 409,
            "DUPLICATE_ACCOUNT": 409,
            "INVALID_DATES": 400,
            "INVALID_STATUS": 400,
            "FISCAL_YEAR_CLOSED": 400,
            "FISCAL_YEAR_NOT_FOUND": 404,
            "DATE_OUT_OF_RANGE": 400,
            "DRAFT_ENTRIES_EXIST": 400,
            "UNBALANCED_ENTRY": 400,
        }
        http_status = status_map.get(result.error_code, 400)
        raise HTTPException(status_code=http_status, detail=result.error)

    return result.data


# =============================================================================
# STATUS
# =============================================================================

@router.get("/status")
async def get_module_status():
    """Statut du module Accounting."""
    return {
        "module": "accounting",
        "version": "v3",
        "status": "active"
    }


# =============================================================================
# ENDPOINTS SUMMARY / DASHBOARD
# =============================================================================

@router.get("/summary", response_model=AccountingSummary)
async def get_accounting_summary(
    fiscal_year_id: Optional[UUID] = Query(None, description="ID exercice comptable"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """
    Obtenir le resume comptable (dashboard).

    Retourne les totaux par type de compte:
    - Actif total
    - Passif total
    - Capitaux propres
    - Chiffre d'affaires
    - Charges
    - Resultat net
    """
    service = AccountingService(db, context.tenant_id)
    return service.get_summary(fiscal_year_id)


@router.get("/monitoring", response_model=AccountingStatus)
async def get_accounting_monitoring(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """
    Obtenir le statut de la comptabilite (monitoring).

    Retourne:
    - Indicateur visuel
    - Nombre d'ecritures en attente
    - Date de derniere cloture
    """
    service = AccountingService(db, context)
    return service.get_status()


# =============================================================================
# ENDPOINTS FISCAL YEARS
# =============================================================================

@router.post(
    "/fiscal-years",
    response_model=FiscalYearResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_fiscal_year(
    data: FiscalYearCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """
    Creer un nouvel exercice comptable.

    Validation:
    - Code unique
    - Date de fin > date de debut
    """
    service = AccountingService(db, context)
    result = service.create_fiscal_year(data)
    return handle_result(result, 201)


@router.get("/fiscal-years", response_model=PaginatedResponse[FiscalYearResponse])
async def list_fiscal_years(
    status_filter: Optional[FiscalYearStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les exercices comptables avec pagination."""
    service = AccountingService(db, context)
    return service.list_fiscal_years(status_filter, page, page_size)


@router.get("/fiscal-years/active", response_model=FiscalYearResponse)
async def get_active_fiscal_year(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Recuperer l'exercice comptable actif."""
    service = AccountingService(db, context)
    fiscal_year = service.get_active_fiscal_year()
    if not fiscal_year:
        raise HTTPException(
            status_code=404,
            detail="Aucun exercice comptable actif"
        )
    return fiscal_year


@router.get("/fiscal-years/{fiscal_year_id}", response_model=FiscalYearResponse)
async def get_fiscal_year(
    fiscal_year_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Recuperer un exercice comptable par ID."""
    service = AccountingService(db, context)
    fiscal_year = service.get_fiscal_year(fiscal_year_id)
    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Exercice comptable non trouve")
    return fiscal_year


@router.put("/fiscal-years/{fiscal_year_id}", response_model=FiscalYearResponse)
async def update_fiscal_year(
    fiscal_year_id: UUID,
    data: FiscalYearUpdate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Mettre a jour un exercice comptable (seulement si OPEN)."""
    service = AccountingService(db, context)
    result = service.update_fiscal_year(fiscal_year_id, data)
    return handle_result(result)


@router.post("/fiscal-years/{fiscal_year_id}/close", response_model=FiscalYearResponse)
async def close_fiscal_year(
    fiscal_year_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """
    Cloturer un exercice comptable.

    Pre-requis:
    - Exercice doit etre OPEN
    - Aucune ecriture en brouillon
    """
    service = AccountingService(db, context)
    result = service.close_fiscal_year(fiscal_year_id)
    return handle_result(result)


# =============================================================================
# ENDPOINTS CHART OF ACCOUNTS
# =============================================================================

@router.post(
    "/accounts",
    response_model=ChartOfAccountsResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_account(
    data: ChartOfAccountsCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Creer un compte comptable."""
    service = AccountingService(db, context)
    result = service.create_account(data)
    return handle_result(result, 201)


@router.get("/accounts", response_model=PaginatedResponse[ChartOfAccountsResponse])
async def list_accounts(
    account_type: Optional[AccountType] = Query(None),
    account_class: Optional[str] = Query(None, max_length=1),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les comptes comptables avec filtres."""
    service = AccountingService(db, context)
    return service.list_accounts(account_type, account_class, search, page, page_size)


@router.get("/accounts/{account_number}", response_model=ChartOfAccountsResponse)
async def get_account(
    account_number: str,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Recuperer un compte comptable par numero."""
    service = AccountingService(db, context)
    account = service.get_account(account_number)
    if not account:
        raise HTTPException(status_code=404, detail="Compte non trouve")
    return account


@router.put("/accounts/{account_number}", response_model=ChartOfAccountsResponse)
async def update_account(
    account_number: str,
    data: ChartOfAccountsUpdate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Mettre a jour un compte comptable."""
    service = AccountingService(db, context)
    result = service.update_account(account_number, data)
    return handle_result(result)


# =============================================================================
# ENDPOINTS JOURNAL ENTRIES
# =============================================================================

@router.post(
    "/journal",
    response_model=JournalEntryResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_journal_entry(
    data: JournalEntryCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """
    Creer une ecriture comptable.

    Validation:
    - Exercice doit exister et etre OPEN
    - Date dans la periode de l'exercice
    - Ecriture equilibree (debit = credit)
    """
    service = AccountingService(db, context)
    result = service.create_journal_entry(data)
    return handle_result(result, 201)


@router.get("/journal", response_model=PaginatedResponse[JournalEntryResponse])
async def list_journal_entries(
    fiscal_year_id: Optional[UUID] = Query(None),
    journal_code: Optional[str] = Query(None),
    status_filter: Optional[EntryStatus] = Query(None, alias="status"),
    period: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les ecritures comptables avec filtres."""
    service = AccountingService(db, context)
    return service.list_journal_entries(
        fiscal_year_id, journal_code, status_filter, period, search, page, page_size
    )


@router.get("/journal/{entry_id}", response_model=JournalEntryResponse)
async def get_journal_entry(
    entry_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Recuperer une ecriture comptable avec ses lignes."""
    service = AccountingService(db, context)
    entry = service.get_journal_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Ecriture non trouvee")
    return entry


@router.post("/journal/{entry_id}/post", response_model=JournalEntryResponse)
async def post_journal_entry(
    entry_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """
    Comptabiliser une ecriture (DRAFT -> POSTED).

    Pre-requis:
    - Ecriture en brouillon (DRAFT)
    - Ecriture equilibree
    """
    service = AccountingService(db, context)
    result = service.post_journal_entry(entry_id)
    return handle_result(result)


@router.post("/journal/{entry_id}/validate", response_model=JournalEntryResponse)
async def validate_journal_entry(
    entry_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """
    Valider definitivement une ecriture (POSTED -> VALIDATED).

    Pre-requis:
    - Ecriture comptabilisee (POSTED)
    """
    service = AccountingService(db, context)
    result = service.validate_journal_entry(entry_id)
    return handle_result(result)


# =============================================================================
# ENDPOINTS REPORTS
# =============================================================================

@router.get("/ledger", response_model=PaginatedResponse[LedgerAccount])
async def get_ledger(
    account_number: Optional[str] = Query(None),
    fiscal_year_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """
    Obtenir le grand livre.

    Retourne les soldes par compte avec debits/credits totaux.
    """
    service = AccountingService(db, context)
    return service.get_ledger(account_number, fiscal_year_id, page, page_size)


@router.get("/balance", response_model=PaginatedResponse[BalanceEntry])
async def get_balance(
    fiscal_year_id: Optional[UUID] = Query(None),
    period: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """
    Obtenir la balance generale.

    Retourne pour chaque compte:
    - Solde d'ouverture
    - Mouvements de la periode
    - Solde de cloture
    """
    service = AccountingService(db, context)
    return service.get_balance(fiscal_year_id, period, page, page_size)
