"""
AZALS MODULE M2 - Router Finance (MIGRÉ CORE SaaS)
===================================================

Endpoints API pour la comptabilité et la trésorerie.

✅ MIGRATION 100% COMPLÈTE vers CORE SaaS (Phase 2.2):
- Utilise get_saas_context() au lieu de get_current_user() + get_tenant_id()
- 46/46 endpoints protégés migrés vers pattern CORE ✅
- Service adapté pour utiliser context.tenant_id

ENDPOINTS MIGRÉS (46):
- Accounts (5): CRUD + get balance
- Journals (4): CRUD
- Fiscal Years (7): CRUD + current + periods + close year/period
- Entries (8): CRUD + lines + validate/post/cancel
- Bank Accounts (4): CRUD
- Bank Statements (4): CRUD + reconcile
- Bank Transactions (2): create + list
- Cash Forecasts (4): CRUD
- Cash Flow Categories (2): create + list
- Reports (4): trial balance + income statement + create + list
- Dashboard (1): get dashboard
"""
from __future__ import annotations


from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext

from .models import AccountType, BankTransactionType, EntryStatus, ForecastPeriod, JournalType
from .schemas import (
    AccountCreate,
    AccountList,
    AccountResponse,
    AccountUpdate,
    BankAccountCreate,
    BankAccountResponse,
    BankAccountUpdate,
    BankStatementCreate,
    BankStatementResponse,
    BankTransactionCreate,
    BankTransactionResponse,
    CashFlowCategoryCreate,
    CashFlowCategoryResponse,
    CashForecastCreate,
    CashForecastResponse,
    CashForecastUpdate,
    EntryCreate,
    EntryLineResponse,
    EntryList,
    EntryResponse,
    EntryUpdate,
    FinanceDashboard,
    FinancialReportCreate,
    FinancialReportResponse,
    FiscalPeriodResponse,
    FiscalYearCreate,
    FiscalYearResponse,
    IncomeStatement,
    JournalCreate,
    JournalResponse,
    JournalUpdate,
    TrialBalance,
)
from .service import get_finance_service

router = APIRouter(prefix="/v2/finance", tags=["Finance"])


# ============================================================================
# DÉPENDANCES
# ============================================================================

def get_service_v2(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
) -> object:
    """
    Dépendance pour obtenir le service Finance (endpoints PROTÉGÉS).

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation tenant
    """
    return get_finance_service(db, context.tenant_id)


# =============================================================================
# COMPTES COMPTABLES (Endpoints PROTÉGÉS - MIGRÉS)
# =============================================================================

@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    data: AccountCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer un compte comptable.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_finance_service(db, context.tenant_id)

    # Vérifier unicité du code
    existing = service.get_account_by_code(data.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Account with code {data.code} already exists"
        )

    return service.create_account(data)


@router.get("/accounts", response_model=AccountList)
def list_accounts(
    account_type: AccountType | None = None,
    parent_id: UUID | None = None,
    is_active: bool = True,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les comptes comptables.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    items, total = service.list_accounts(
        account_type=account_type,
        parent_id=parent_id,
        is_active=is_active,
        search=search,
        skip=skip,
        limit=limit
    )
    return AccountList(items=items, total=total)


@router.get("/accounts/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Récupérer un compte par ID.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    account = service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.put("/accounts/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: UUID,
    data: AccountUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Mettre à jour un compte.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_finance_service(db, context.tenant_id)
    account = service.update_account(account_id, data)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.get("/accounts/{account_id}/balance")
def get_account_balance(
    account_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Récupérer le solde d'un compte.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    account = service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return service.get_account_balance(account_id, start_date, end_date)


# =============================================================================
# JOURNAUX COMPTABLES (Endpoints PROTÉGÉS - MIGRÉS)
# =============================================================================

@router.post("/journals", response_model=JournalResponse, status_code=status.HTTP_201_CREATED)
def create_journal(
    data: JournalCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer un journal comptable.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_finance_service(db, context.tenant_id)
    return service.create_journal(data)


@router.get("/journals", response_model=list[JournalResponse])
def list_journals(
    journal_type: JournalType | None = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les journaux comptables.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    return service.list_journals(journal_type, is_active)


@router.get("/journals/{journal_id}", response_model=JournalResponse)
def get_journal(
    journal_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Récupérer un journal par ID.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    journal = service.get_journal(journal_id)
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found")
    return journal


@router.put("/journals/{journal_id}", response_model=JournalResponse)
def update_journal(
    journal_id: UUID,
    data: JournalUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Mettre à jour un journal.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_finance_service(db, context.tenant_id)
    journal = service.update_journal(journal_id, data)
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found")
    return journal


# =============================================================================
# EXERCICES FISCAUX (Endpoints PROTÉGÉS - MIGRÉS)
# =============================================================================

@router.post("/fiscal-years", response_model=FiscalYearResponse, status_code=status.HTTP_201_CREATED)
def create_fiscal_year(
    data: FiscalYearCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer un exercice fiscal.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_finance_service(db, context.tenant_id)
    return service.create_fiscal_year(data)


@router.get("/fiscal-years", response_model=list[FiscalYearResponse])
def list_fiscal_years(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les exercices fiscaux.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    return service.list_fiscal_years()


@router.get("/fiscal-years/current", response_model=FiscalYearResponse)
def get_current_fiscal_year(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Récupérer l'exercice en cours.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    fiscal_year = service.get_current_fiscal_year()
    if not fiscal_year:
        raise HTTPException(status_code=404, detail="No open fiscal year found")
    return fiscal_year


@router.get("/fiscal-years/{fiscal_year_id}", response_model=FiscalYearResponse)
def get_fiscal_year(
    fiscal_year_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Récupérer un exercice par ID.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    fiscal_year = service.get_fiscal_year(fiscal_year_id)
    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")
    return fiscal_year


@router.get("/fiscal-years/{fiscal_year_id}/periods", response_model=list[FiscalPeriodResponse])
def get_fiscal_periods(
    fiscal_year_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Récupérer les périodes d'un exercice.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    return service.get_fiscal_periods(fiscal_year_id)


@router.post("/fiscal-years/{fiscal_year_id}/close", response_model=FiscalYearResponse)
def close_fiscal_year(
    fiscal_year_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Clôturer un exercice fiscal.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    - Utilise context.user_id pour audit (closed_by)
    """
    service = get_finance_service(db, context.tenant_id)
    try:
        fiscal_year = service.close_fiscal_year(fiscal_year_id, context.user_id)
        if not fiscal_year:
            raise HTTPException(status_code=404, detail="Fiscal year not found or already closed")
        return fiscal_year
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/periods/{period_id}/close", response_model=FiscalPeriodResponse)
def close_fiscal_period(
    period_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Clôturer une période.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    - Utilise context.user_id pour audit (closed_by)
    """
    service = get_finance_service(db, context.tenant_id)
    period = service.close_fiscal_period(period_id, context.user_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found or already closed")
    return period


# =============================================================================
# ÉCRITURES COMPTABLES (Endpoints PROTÉGÉS - MIGRÉS)
# =============================================================================

@router.post("/entries", response_model=EntryResponse, status_code=status.HTTP_201_CREATED)
def create_entry(
    data: EntryCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer une écriture comptable.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    - Utilise context.user_id pour audit (created_by)
    """
    service = get_finance_service(db, context.tenant_id)
    try:
        return service.create_entry(data, context.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/entries", response_model=EntryList)
def list_entries(
    journal_id: UUID | None = None,
    fiscal_year_id: UUID | None = None,
    entry_status: EntryStatus | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les écritures comptables.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    items, total = service.list_entries(
        journal_id=journal_id,
        fiscal_year_id=fiscal_year_id,
        entry_status=entry_status,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    return EntryList(items=items, total=total)


@router.get("/entries/{entry_id}", response_model=EntryResponse)
def get_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Récupérer une écriture par ID.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    entry = service.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.put("/entries/{entry_id}", response_model=EntryResponse)
def update_entry(
    entry_id: UUID,
    data: EntryUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Mettre à jour une écriture (seulement si brouillon).

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_finance_service(db, context.tenant_id)
    try:
        entry = service.update_entry(entry_id, data)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found or not in draft status")
        return entry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/entries/{entry_id}/lines", response_model=list[EntryLineResponse])
def get_entry_lines(
    entry_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Récupérer les lignes d'une écriture.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    return service.get_entry_lines(entry_id)


@router.post("/entries/{entry_id}/validate", response_model=EntryResponse)
def validate_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Valider une écriture.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    - Utilise context.user_id pour audit (validated_by)
    """
    service = get_finance_service(db, context.tenant_id)
    try:
        entry = service.validate_entry(entry_id, context.user_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found or already validated")
        return entry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/entries/{entry_id}/post", response_model=EntryResponse)
def post_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Passer une écriture (la rendre définitive).

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    - Utilise context.user_id pour audit (posted_by)
    """
    service = get_finance_service(db, context.tenant_id)
    try:
        entry = service.post_entry(entry_id, context.user_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found or already posted")
        return entry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/entries/{entry_id}/cancel", response_model=EntryResponse)
def cancel_entry(
    entry_id: UUID,
    reason: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Annuler une écriture (contrepassation).

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    - Utilise context.user_id pour audit (cancelled_by)
    """
    service = get_finance_service(db, context.tenant_id)
    try:
        entry = service.cancel_entry(entry_id, context.user_id, reason)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found or already cancelled")
        return entry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# COMPTES BANCAIRES (Endpoints PROTÉGÉS - MIGRÉS)
# =============================================================================

@router.post("/bank-accounts", response_model=BankAccountResponse, status_code=status.HTTP_201_CREATED)
def create_bank_account(
    data: BankAccountCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer un compte bancaire.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_finance_service(db, context.tenant_id)
    return service.create_bank_account(data)


@router.get("/bank-accounts", response_model=list[BankAccountResponse])
def list_bank_accounts(
    is_active: bool = True,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les comptes bancaires.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    return service.list_bank_accounts(is_active)


@router.get("/bank-accounts/{bank_account_id}", response_model=BankAccountResponse)
def get_bank_account(
    bank_account_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Récupérer un compte bancaire par ID.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    bank_account = service.get_bank_account(bank_account_id)
    if not bank_account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return bank_account


@router.put("/bank-accounts/{bank_account_id}", response_model=BankAccountResponse)
def update_bank_account(
    bank_account_id: UUID,
    data: BankAccountUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Mettre à jour un compte bancaire.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_finance_service(db, context.tenant_id)
    try:
        bank_account = service.update_bank_account(bank_account_id, data)
        if not bank_account:
            raise HTTPException(status_code=404, detail="Bank account not found")
        return bank_account
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# RELEVÉS BANCAIRES (Endpoints PROTÉGÉS - MIGRÉS)
# =============================================================================

@router.post("/bank-statements", response_model=BankStatementResponse, status_code=status.HTTP_201_CREATED)
def create_bank_statement(
    data: BankStatementCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer un relevé bancaire.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_finance_service(db, context.tenant_id)
    return service.create_bank_statement(data)


@router.get("/bank-statements")
def list_bank_statements(
    bank_account_id: UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les relevés bancaires.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    return service.list_bank_statements(bank_account_id, start_date, end_date)


@router.get("/bank-statements/{statement_id}", response_model=BankStatementResponse)
def get_bank_statement(
    statement_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Récupérer un relevé bancaire par ID.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    statement = service.get_bank_statement(statement_id)
    if not statement:
        raise HTTPException(status_code=404, detail="Bank statement not found")
    return statement


@router.post("/bank-statements/lines/{line_id}/reconcile")
def reconcile_statement_line(
    line_id: UUID,
    entry_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Rapprocher une ligne de relevé avec une écriture.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    - Utilise context.user_id pour audit (reconciled_by)
    """
    service = get_finance_service(db, context.tenant_id)
    try:
        success = service.reconcile_statement_line(line_id, entry_id, context.user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Statement line or entry not found")
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# TRANSACTIONS BANCAIRES (Endpoints PROTÉGÉS - MIGRÉS)
# =============================================================================

@router.post("/bank-transactions", response_model=BankTransactionResponse, status_code=status.HTTP_201_CREATED)
def create_bank_transaction(
    data: BankTransactionCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer une transaction bancaire.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_finance_service(db, context.tenant_id)
    return service.create_bank_transaction(data)


@router.get("/bank-transactions")
@router.get("/transactions")  # Alias pour compatibilité frontend
def list_bank_transactions(
    bank_account_id: UUID | None = None,
    transaction_type: BankTransactionType | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les transactions bancaires.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    transactions, total = service.list_bank_transactions(
        bank_account_id=bank_account_id,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    return {"items": transactions, "total": total}


# =============================================================================
# PRÉVISIONS DE TRÉSORERIE (Endpoints PROTÉGÉS - MIGRÉS)
# =============================================================================

@router.post("/cash-forecasts", response_model=CashForecastResponse, status_code=status.HTTP_201_CREATED)
def create_cash_forecast(
    data: CashForecastCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer une prévision de trésorerie.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_finance_service(db, context.tenant_id)
    return service.create_cash_forecast(data)


@router.get("/cash-forecasts", response_model=list[CashForecastResponse])
def list_cash_forecasts(
    period: ForecastPeriod | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les prévisions de trésorerie.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    return service.list_cash_forecasts(period, start_date, end_date)


@router.get("/cash-forecasts/{forecast_id}", response_model=CashForecastResponse)
def get_cash_forecast(
    forecast_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Récupérer une prévision par ID.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    forecast = service.get_cash_forecast(forecast_id)
    if not forecast:
        raise HTTPException(status_code=404, detail="Cash forecast not found")
    return forecast


@router.put("/cash-forecasts/{forecast_id}", response_model=CashForecastResponse)
def update_cash_forecast(
    forecast_id: UUID,
    data: CashForecastUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Mettre à jour une prévision.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_finance_service(db, context.tenant_id)
    try:
        forecast = service.update_cash_forecast(forecast_id, data)
        if not forecast:
            raise HTTPException(status_code=404, detail="Cash forecast not found")
        return forecast
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# CATÉGORIES FLUX DE TRÉSORERIE (Endpoints PROTÉGÉS - MIGRÉS)
# =============================================================================

@router.post("/cash-flow-categories", response_model=CashFlowCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_cash_flow_category(
    data: CashFlowCategoryCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer une catégorie de flux de trésorerie.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_finance_service(db, context.tenant_id)
    return service.create_cash_flow_category(data)


@router.get("/cash-flow-categories", response_model=list[CashFlowCategoryResponse])
def list_cash_flow_categories(
    is_active: bool = True,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les catégories de flux.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    return service.list_cash_flow_categories(is_active)


# =============================================================================
# RAPPORTS (Endpoints PROTÉGÉS - MIGRÉS)
# =============================================================================

@router.get("/reports/trial-balance", response_model=TrialBalance)
def get_trial_balance(
    as_of_date: date | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Balance générale.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    return service.get_trial_balance(as_of_date)


@router.get("/reports/income-statement", response_model=IncomeStatement)
def get_income_statement(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Compte de résultat.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    return service.get_income_statement(start_date, end_date)


@router.post("/reports", response_model=FinancialReportResponse, status_code=status.HTTP_201_CREATED)
def create_financial_report(
    data: FinancialReportCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Générer un rapport financier personnalisé.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_finance_service(db, context.tenant_id)
    return service.create_financial_report(data)


@router.get("/reports")
def list_financial_reports(
    report_type: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les rapports générés.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    reports, total = service.list_financial_reports(
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    return {"items": reports, "total": total}


# =============================================================================
# DASHBOARD (Endpoints PROTÉGÉS - MIGRÉS)
# =============================================================================

@router.get("/dashboard", response_model=FinanceDashboard)
def get_finance_dashboard(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Dashboard finance/trésorerie.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_finance_service(db, context.tenant_id)
    return service.get_dashboard()


# ============================================================================
# MIGRATION FINANCE COMPLÈTE - CORE SaaS
# ============================================================================
#
# TOTAL ENDPOINTS: 46
# - Tous endpoints protégés (MIGRÉS): 46
#
# - Accounts (5): CRUD + get balance
# - Journals (4): CRUD
# - Fiscal Years (7): CRUD + current + periods + close year/period
# - Entries (8): CRUD + lines + validate/post/cancel
# - Bank Accounts (4): CRUD
# - Bank Statements (4): CRUD + reconcile
# - Bank Transactions (2): create + list (+ 1 alias)
# - Cash Forecasts (4): CRUD
# - Cash Flow Categories (2): create + list
# - Reports (4): trial balance + income statement + create + list
# - Dashboard (1): get dashboard
#
# ✅ MIGRATION 100% COMPLÈTE (46/46 endpoints protégés migrés)
# ============================================================================
