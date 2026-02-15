"""
AZALS MODULE M2 - FINANCE: Router Unifié
=========================================

Router complet compatible v1, v2 et v3 via app.azals.
Utilise get_context() qui fonctionne avec les deux patterns d'authentification.

Ce router remplace router.py et router_v2.py.

Enregistrement dans main.py:
    from app.modules.finance.router_unified import router as finance_router

    # Double enregistrement pour compatibilité
    app.include_router(finance_router, prefix="/v2")
    app.include_router(finance_router, prefix="/v1", deprecated=True)

Conformité : AZA-NF-006

ENDPOINTS (46):
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

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db

from .models import AccountType, BankTransactionType, EntryStatus, ForecastPeriod, JournalType
from .schemas import (
    AccountCreate, AccountList, AccountResponse, AccountUpdate,
    BankAccountCreate, BankAccountResponse, BankAccountUpdate,
    BankStatementCreate, BankStatementResponse,
    BankTransactionCreate, BankTransactionResponse,
    CashFlowCategoryCreate, CashFlowCategoryResponse,
    CashForecastCreate, CashForecastResponse, CashForecastUpdate,
    EntryCreate, EntryLineResponse, EntryList, EntryResponse, EntryUpdate,
    FinanceDashboard, FinancialReportCreate, FinancialReportResponse,
    FiscalPeriodResponse, FiscalYearCreate, FiscalYearResponse,
    IncomeStatement, JournalCreate, JournalResponse, JournalUpdate, TrialBalance,
)
from .service import get_finance_service

router = APIRouter(prefix="/finance", tags=["Finance - Comptabilité"])

# =============================================================================
# COMPTES COMPTABLES
# =============================================================================

@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(data: AccountCreate, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Créer un compte comptable."""
    service = get_finance_service(db, context.tenant_id)
    existing = service.get_account_by_code(data.code)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Account with code {data.code} already exists")
    return service.create_account(data)

@router.get("/accounts", response_model=AccountList)
def list_accounts(
    account_type: AccountType | None = None, parent_id: UUID | None = None,
    is_active: bool = True, search: str | None = None,
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)
):
    """Lister les comptes comptables."""
    service = get_finance_service(db, context.tenant_id)
    items, total = service.list_accounts(account_type=account_type, parent_id=parent_id, is_active=is_active, search=search, skip=skip, limit=limit)
    return AccountList(items=items, total=total)

@router.get("/accounts/{account_id}", response_model=AccountResponse)
def get_account(account_id: UUID, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Récupérer un compte par ID."""
    service = get_finance_service(db, context.tenant_id)
    account = service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.put("/accounts/{account_id}", response_model=AccountResponse)
def update_account(account_id: UUID, data: AccountUpdate, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Mettre à jour un compte."""
    service = get_finance_service(db, context.tenant_id)
    account = service.update_account(account_id, data)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.get("/accounts/{account_id}/balance")
def get_account_balance(account_id: UUID, start_date: date | None = None, end_date: date | None = None, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Récupérer le solde d'un compte."""
    service = get_finance_service(db, context.tenant_id)
    account = service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return service.get_account_balance(account_id, start_date, end_date)

# =============================================================================
# JOURNAUX COMPTABLES
# =============================================================================

@router.post("/journals", response_model=JournalResponse, status_code=status.HTTP_201_CREATED)
def create_journal(data: JournalCreate, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Créer un journal comptable."""
    service = get_finance_service(db, context.tenant_id)
    return service.create_journal(data)

@router.get("/journals", response_model=list[JournalResponse])
def list_journals(journal_type: JournalType | None = None, is_active: bool = True, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Lister les journaux comptables."""
    service = get_finance_service(db, context.tenant_id)
    return service.list_journals(journal_type, is_active)

@router.get("/journals/{journal_id}", response_model=JournalResponse)
def get_journal(journal_id: UUID, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Récupérer un journal par ID."""
    service = get_finance_service(db, context.tenant_id)
    journal = service.get_journal(journal_id)
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found")
    return journal

@router.put("/journals/{journal_id}", response_model=JournalResponse)
def update_journal(journal_id: UUID, data: JournalUpdate, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Mettre à jour un journal."""
    service = get_finance_service(db, context.tenant_id)
    journal = service.update_journal(journal_id, data)
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found")
    return journal

# =============================================================================
# EXERCICES FISCAUX
# =============================================================================

@router.post("/fiscal-years", response_model=FiscalYearResponse, status_code=status.HTTP_201_CREATED)
def create_fiscal_year(data: FiscalYearCreate, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Créer un exercice fiscal."""
    service = get_finance_service(db, context.tenant_id)
    return service.create_fiscal_year(data)

@router.get("/fiscal-years", response_model=list[FiscalYearResponse])
def list_fiscal_years(db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Lister les exercices fiscaux."""
    service = get_finance_service(db, context.tenant_id)
    return service.list_fiscal_years()

@router.get("/fiscal-years/current", response_model=FiscalYearResponse)
def get_current_fiscal_year(db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Récupérer l'exercice en cours."""
    service = get_finance_service(db, context.tenant_id)
    fiscal_year = service.get_current_fiscal_year()
    if not fiscal_year:
        raise HTTPException(status_code=404, detail="No open fiscal year found")
    return fiscal_year

@router.get("/fiscal-years/{fiscal_year_id}", response_model=FiscalYearResponse)
def get_fiscal_year(fiscal_year_id: UUID, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Récupérer un exercice par ID."""
    service = get_finance_service(db, context.tenant_id)
    fiscal_year = service.get_fiscal_year(fiscal_year_id)
    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")
    return fiscal_year

@router.get("/fiscal-years/{fiscal_year_id}/periods", response_model=list[FiscalPeriodResponse])
def get_fiscal_periods(fiscal_year_id: UUID, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Récupérer les périodes d'un exercice."""
    service = get_finance_service(db, context.tenant_id)
    return service.get_fiscal_periods(fiscal_year_id)

@router.post("/fiscal-years/{fiscal_year_id}/close", response_model=FiscalYearResponse)
def close_fiscal_year(fiscal_year_id: UUID, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Clôturer un exercice fiscal."""
    service = get_finance_service(db, context.tenant_id)
    try:
        fiscal_year = service.close_fiscal_year(fiscal_year_id, context.user_id)
        if not fiscal_year:
            raise HTTPException(status_code=404, detail="Fiscal year not found or already closed")
        return fiscal_year
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/periods/{period_id}/close", response_model=FiscalPeriodResponse)
def close_fiscal_period(period_id: UUID, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Clôturer une période."""
    service = get_finance_service(db, context.tenant_id)
    period = service.close_fiscal_period(period_id, context.user_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found or already closed")
    return period

# =============================================================================
# ÉCRITURES COMPTABLES
# =============================================================================

@router.post("/entries", response_model=EntryResponse, status_code=status.HTTP_201_CREATED)
def create_entry(data: EntryCreate, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Créer une écriture comptable."""
    service = get_finance_service(db, context.tenant_id)
    try:
        return service.create_entry(data, context.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/entries", response_model=EntryList)
def list_entries(
    journal_id: UUID | None = None, fiscal_year_id: UUID | None = None,
    entry_status: EntryStatus | None = None, start_date: date | None = None, end_date: date | None = None,
    skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)
):
    """Lister les écritures comptables."""
    service = get_finance_service(db, context.tenant_id)
    items, total = service.list_entries(journal_id=journal_id, fiscal_year_id=fiscal_year_id, entry_status=entry_status, start_date=start_date, end_date=end_date, skip=skip, limit=limit)
    return EntryList(items=items, total=total)

@router.get("/entries/{entry_id}", response_model=EntryResponse)
def get_entry(entry_id: UUID, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Récupérer une écriture par ID."""
    service = get_finance_service(db, context.tenant_id)
    entry = service.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

@router.put("/entries/{entry_id}", response_model=EntryResponse)
def update_entry(entry_id: UUID, data: EntryUpdate, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Mettre à jour une écriture (seulement si brouillon)."""
    service = get_finance_service(db, context.tenant_id)
    try:
        entry = service.update_entry(entry_id, data)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found or not in draft status")
        return entry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/entries/{entry_id}/lines", response_model=list[EntryLineResponse])
def get_entry_lines(entry_id: UUID, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Récupérer les lignes d'une écriture."""
    service = get_finance_service(db, context.tenant_id)
    return service.get_entry_lines(entry_id)

@router.post("/entries/{entry_id}/validate", response_model=EntryResponse)
def validate_entry(entry_id: UUID, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Valider une écriture."""
    service = get_finance_service(db, context.tenant_id)
    try:
        entry = service.validate_entry(entry_id, context.user_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found or already validated")
        return entry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/entries/{entry_id}/post", response_model=EntryResponse)
def post_entry(entry_id: UUID, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Passer une écriture (la rendre définitive)."""
    service = get_finance_service(db, context.tenant_id)
    try:
        entry = service.post_entry(entry_id, context.user_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found or already posted")
        return entry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/entries/{entry_id}/cancel", response_model=EntryResponse)
def cancel_entry(entry_id: UUID, reason: str | None = None, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Annuler une écriture (contrepassation)."""
    service = get_finance_service(db, context.tenant_id)
    try:
        entry = service.cancel_entry(entry_id, context.user_id, reason)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found or already cancelled")
        return entry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# =============================================================================
# COMPTES BANCAIRES
# =============================================================================

@router.post("/bank-accounts", response_model=BankAccountResponse, status_code=status.HTTP_201_CREATED)
def create_bank_account(data: BankAccountCreate, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Créer un compte bancaire."""
    service = get_finance_service(db, context.tenant_id)
    return service.create_bank_account(data)

@router.get("/bank-accounts", response_model=list[BankAccountResponse])
def list_bank_accounts(is_active: bool = True, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Lister les comptes bancaires."""
    service = get_finance_service(db, context.tenant_id)
    return service.list_bank_accounts(is_active)

@router.get("/bank-accounts/{bank_account_id}", response_model=BankAccountResponse)
def get_bank_account(bank_account_id: UUID, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Récupérer un compte bancaire par ID."""
    service = get_finance_service(db, context.tenant_id)
    bank_account = service.get_bank_account(bank_account_id)
    if not bank_account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return bank_account

@router.put("/bank-accounts/{bank_account_id}", response_model=BankAccountResponse)
def update_bank_account(bank_account_id: UUID, data: BankAccountUpdate, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Mettre à jour un compte bancaire."""
    service = get_finance_service(db, context.tenant_id)
    try:
        bank_account = service.update_bank_account(bank_account_id, data)
        if not bank_account:
            raise HTTPException(status_code=404, detail="Bank account not found")
        return bank_account
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# =============================================================================
# RELEVÉS BANCAIRES
# =============================================================================

@router.post("/bank-statements", response_model=BankStatementResponse, status_code=status.HTTP_201_CREATED)
def create_bank_statement(data: BankStatementCreate, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Créer un relevé bancaire."""
    service = get_finance_service(db, context.tenant_id)
    return service.create_bank_statement(data)

@router.get("/bank-statements")
def list_bank_statements(bank_account_id: UUID | None = None, start_date: date | None = None, end_date: date | None = None, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Lister les relevés bancaires."""
    service = get_finance_service(db, context.tenant_id)
    return service.list_bank_statements(bank_account_id, start_date, end_date)

@router.get("/bank-statements/{statement_id}", response_model=BankStatementResponse)
def get_bank_statement(statement_id: UUID, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Récupérer un relevé bancaire par ID."""
    service = get_finance_service(db, context.tenant_id)
    statement = service.get_bank_statement(statement_id)
    if not statement:
        raise HTTPException(status_code=404, detail="Bank statement not found")
    return statement

@router.post("/bank-statements/lines/{line_id}/reconcile")
def reconcile_statement_line(line_id: UUID, entry_id: UUID, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Rapprocher une ligne de relevé avec une écriture."""
    service = get_finance_service(db, context.tenant_id)
    try:
        success = service.reconcile_statement_line(line_id, entry_id, context.user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Statement line or entry not found")
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# =============================================================================
# TRANSACTIONS BANCAIRES
# =============================================================================

@router.post("/bank-transactions", response_model=BankTransactionResponse, status_code=status.HTTP_201_CREATED)
def create_bank_transaction(data: BankTransactionCreate, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Créer une transaction bancaire."""
    service = get_finance_service(db, context.tenant_id)
    return service.create_bank_transaction(data)

@router.get("/bank-transactions")
@router.get("/transactions")  # Alias pour compatibilité frontend
def list_bank_transactions(
    bank_account_id: UUID | None = None, transaction_type: BankTransactionType | None = None,
    start_date: date | None = None, end_date: date | None = None,
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)
):
    """Lister les transactions bancaires."""
    service = get_finance_service(db, context.tenant_id)
    transactions, total = service.list_bank_transactions(bank_account_id=bank_account_id, transaction_type=transaction_type, start_date=start_date, end_date=end_date, skip=skip, limit=limit)
    return {"items": transactions, "total": total}

# =============================================================================
# PRÉVISIONS DE TRÉSORERIE
# =============================================================================

@router.post("/cash-forecasts", response_model=CashForecastResponse, status_code=status.HTTP_201_CREATED)
def create_cash_forecast(data: CashForecastCreate, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Créer une prévision de trésorerie."""
    service = get_finance_service(db, context.tenant_id)
    return service.create_cash_forecast(data)

@router.get("/cash-forecasts", response_model=list[CashForecastResponse])
def list_cash_forecasts(period: ForecastPeriod | None = None, start_date: date | None = None, end_date: date | None = None, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Lister les prévisions de trésorerie."""
    service = get_finance_service(db, context.tenant_id)
    return service.list_cash_forecasts(period, start_date, end_date)

@router.get("/cash-forecasts/{forecast_id}", response_model=CashForecastResponse)
def get_cash_forecast(forecast_id: UUID, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Récupérer une prévision par ID."""
    service = get_finance_service(db, context.tenant_id)
    forecast = service.get_cash_forecast(forecast_id)
    if not forecast:
        raise HTTPException(status_code=404, detail="Cash forecast not found")
    return forecast

@router.put("/cash-forecasts/{forecast_id}", response_model=CashForecastResponse)
def update_cash_forecast(forecast_id: UUID, data: CashForecastUpdate, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Mettre à jour une prévision."""
    service = get_finance_service(db, context.tenant_id)
    try:
        forecast = service.update_cash_forecast(forecast_id, data)
        if not forecast:
            raise HTTPException(status_code=404, detail="Cash forecast not found")
        return forecast
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# =============================================================================
# CATÉGORIES FLUX DE TRÉSORERIE
# =============================================================================

@router.post("/cash-flow-categories", response_model=CashFlowCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_cash_flow_category(data: CashFlowCategoryCreate, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Créer une catégorie de flux de trésorerie."""
    service = get_finance_service(db, context.tenant_id)
    return service.create_cash_flow_category(data)

@router.get("/cash-flow-categories", response_model=list[CashFlowCategoryResponse])
def list_cash_flow_categories(is_active: bool = True, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Lister les catégories de flux."""
    service = get_finance_service(db, context.tenant_id)
    return service.list_cash_flow_categories(is_active)

# =============================================================================
# RAPPORTS
# =============================================================================

@router.get("/reports/trial-balance", response_model=TrialBalance)
def get_trial_balance(as_of_date: date | None = None, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Balance générale."""
    service = get_finance_service(db, context.tenant_id)
    return service.get_trial_balance(as_of_date)

@router.get("/reports/income-statement", response_model=IncomeStatement)
def get_income_statement(start_date: date, end_date: date, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Compte de résultat."""
    service = get_finance_service(db, context.tenant_id)
    return service.get_income_statement(start_date, end_date)

@router.post("/reports", response_model=FinancialReportResponse, status_code=status.HTTP_201_CREATED)
def create_financial_report(data: FinancialReportCreate, db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Générer un rapport financier personnalisé."""
    service = get_finance_service(db, context.tenant_id)
    return service.create_financial_report(data)

@router.get("/reports")
def list_financial_reports(
    report_type: str | None = None, start_date: date | None = None, end_date: date | None = None,
    skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)
):
    """Lister les rapports générés."""
    service = get_finance_service(db, context.tenant_id)
    reports, total = service.list_financial_reports(report_type=report_type, start_date=start_date, end_date=end_date, skip=skip, limit=limit)
    return {"items": reports, "total": total}

# =============================================================================
# DASHBOARD
# =============================================================================

@router.get("/dashboard", response_model=FinanceDashboard)
def get_finance_dashboard(db: Session = Depends(get_db), context: SaaSContext = Depends(get_context)):
    """Dashboard finance/trésorerie."""
    service = get_finance_service(db, context.tenant_id)
    return service.get_dashboard()
