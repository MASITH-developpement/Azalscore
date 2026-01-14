"""
AZALS MODULE M2 - Router Finance
================================

Endpoints API pour la comptabilité et la trésorerie.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_tenant_id
from app.core.database import get_db

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

router = APIRouter(prefix="/finance", tags=["Finance"])


# =============================================================================
# COMPTES COMPTABLES
# =============================================================================

@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    data: AccountCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer un compte comptable."""
    service = get_finance_service(db, tenant_id)

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
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les comptes comptables."""
    service = get_finance_service(db, tenant_id)
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
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer un compte par ID."""
    service = get_finance_service(db, tenant_id)
    account = service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.put("/accounts/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: UUID,
    data: AccountUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Mettre à jour un compte."""
    service = get_finance_service(db, tenant_id)
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
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer le solde d'un compte."""
    service = get_finance_service(db, tenant_id)
    account = service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return service.get_account_balance(account_id, start_date, end_date)


# =============================================================================
# JOURNAUX COMPTABLES
# =============================================================================

@router.post("/journals", response_model=JournalResponse, status_code=status.HTTP_201_CREATED)
def create_journal(
    data: JournalCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer un journal comptable."""
    service = get_finance_service(db, tenant_id)
    return service.create_journal(data)


@router.get("/journals", response_model=list[JournalResponse])
def list_journals(
    journal_type: JournalType | None = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les journaux comptables."""
    service = get_finance_service(db, tenant_id)
    return service.list_journals(journal_type, is_active)


@router.get("/journals/{journal_id}", response_model=JournalResponse)
def get_journal(
    journal_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer un journal par ID."""
    service = get_finance_service(db, tenant_id)
    journal = service.get_journal(journal_id)
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found")
    return journal


@router.put("/journals/{journal_id}", response_model=JournalResponse)
def update_journal(
    journal_id: UUID,
    data: JournalUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Mettre à jour un journal."""
    service = get_finance_service(db, tenant_id)
    journal = service.update_journal(journal_id, data)
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found")
    return journal


# =============================================================================
# EXERCICES FISCAUX
# =============================================================================

@router.post("/fiscal-years", response_model=FiscalYearResponse, status_code=status.HTTP_201_CREATED)
def create_fiscal_year(
    data: FiscalYearCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer un exercice fiscal."""
    service = get_finance_service(db, tenant_id)
    return service.create_fiscal_year(data)


@router.get("/fiscal-years", response_model=list[FiscalYearResponse])
def list_fiscal_years(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les exercices fiscaux."""
    service = get_finance_service(db, tenant_id)
    return service.list_fiscal_years()


@router.get("/fiscal-years/current", response_model=FiscalYearResponse)
def get_current_fiscal_year(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer l'exercice en cours."""
    service = get_finance_service(db, tenant_id)
    fiscal_year = service.get_current_fiscal_year()
    if not fiscal_year:
        raise HTTPException(status_code=404, detail="No open fiscal year found")
    return fiscal_year


@router.get("/fiscal-years/{fiscal_year_id}", response_model=FiscalYearResponse)
def get_fiscal_year(
    fiscal_year_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer un exercice par ID."""
    service = get_finance_service(db, tenant_id)
    fiscal_year = service.get_fiscal_year(fiscal_year_id)
    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")
    return fiscal_year


@router.get("/fiscal-years/{fiscal_year_id}/periods", response_model=list[FiscalPeriodResponse])
def get_fiscal_periods(
    fiscal_year_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer les périodes d'un exercice."""
    service = get_finance_service(db, tenant_id)
    return service.get_fiscal_periods(fiscal_year_id)


@router.post("/fiscal-years/{fiscal_year_id}/close", response_model=FiscalYearResponse)
def close_fiscal_year(
    fiscal_year_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Clôturer un exercice fiscal."""
    service = get_finance_service(db, tenant_id)
    try:
        fiscal_year = service.close_fiscal_year(fiscal_year_id, current_user.id)
        if not fiscal_year:
            raise HTTPException(status_code=404, detail="Fiscal year not found or already closed")
        return fiscal_year
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/periods/{period_id}/close", response_model=FiscalPeriodResponse)
def close_fiscal_period(
    period_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Clôturer une période."""
    service = get_finance_service(db, tenant_id)
    period = service.close_fiscal_period(period_id, current_user.id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found or already closed")
    return period


# =============================================================================
# ÉCRITURES COMPTABLES
# =============================================================================

@router.post("/entries", response_model=EntryResponse, status_code=status.HTTP_201_CREATED)
def create_entry(
    data: EntryCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer une écriture comptable."""
    service = get_finance_service(db, tenant_id)
    try:
        return service.create_entry(data, current_user.id)
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
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les écritures comptables."""
    service = get_finance_service(db, tenant_id)
    items, total = service.list_entries(
        journal_id=journal_id,
        fiscal_year_id=fiscal_year_id,
        status=entry_status,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    return EntryList(items=items, total=total, page=skip // limit + 1, page_size=limit)


@router.get("/entries/{entry_id}", response_model=EntryResponse)
def get_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer une écriture par ID."""
    service = get_finance_service(db, tenant_id)
    entry = service.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.put("/entries/{entry_id}", response_model=EntryResponse)
def update_entry(
    entry_id: UUID,
    data: EntryUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Mettre à jour une écriture (brouillon uniquement)."""
    service = get_finance_service(db, tenant_id)
    entry = service.update_entry(entry_id, data)
    if not entry:
        raise HTTPException(
            status_code=400,
            detail="Entry not found or not in draft status"
        )
    return entry


@router.get("/entries/{entry_id}/lines", response_model=list[EntryLineResponse])
def get_entry_lines(
    entry_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer les lignes d'une écriture."""
    service = get_finance_service(db, tenant_id)
    return service.get_entry_lines(entry_id)


@router.post("/entries/{entry_id}/validate", response_model=EntryResponse)
def validate_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Valider une écriture."""
    service = get_finance_service(db, tenant_id)
    entry = service.validate_entry(entry_id, current_user.id)
    if not entry:
        raise HTTPException(
            status_code=400,
            detail="Entry not found or not in draft status"
        )
    return entry


@router.post("/entries/{entry_id}/post", response_model=EntryResponse)
def post_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Comptabiliser une écriture."""
    service = get_finance_service(db, tenant_id)
    entry = service.post_entry(entry_id, current_user.id)
    if not entry:
        raise HTTPException(
            status_code=400,
            detail="Entry not found or already posted"
        )
    return entry


@router.post("/entries/{entry_id}/cancel", response_model=EntryResponse)
def cancel_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Annuler une écriture."""
    service = get_finance_service(db, tenant_id)
    entry = service.cancel_entry(entry_id)
    if not entry:
        raise HTTPException(
            status_code=400,
            detail="Entry not found or already cancelled"
        )
    return entry


# =============================================================================
# COMPTES BANCAIRES
# =============================================================================

@router.post("/bank-accounts", response_model=BankAccountResponse, status_code=status.HTTP_201_CREATED)
def create_bank_account(
    data: BankAccountCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer un compte bancaire."""
    service = get_finance_service(db, tenant_id)
    return service.create_bank_account(data)


@router.get("/bank-accounts", response_model=list[BankAccountResponse])
def list_bank_accounts(
    is_active: bool = True,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les comptes bancaires."""
    service = get_finance_service(db, tenant_id)
    return service.list_bank_accounts(is_active)


@router.get("/bank-accounts/{bank_account_id}", response_model=BankAccountResponse)
def get_bank_account(
    bank_account_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer un compte bancaire par ID."""
    service = get_finance_service(db, tenant_id)
    bank_account = service.get_bank_account(bank_account_id)
    if not bank_account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return bank_account


@router.put("/bank-accounts/{bank_account_id}", response_model=BankAccountResponse)
def update_bank_account(
    bank_account_id: UUID,
    data: BankAccountUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Mettre à jour un compte bancaire."""
    service = get_finance_service(db, tenant_id)
    bank_account = service.update_bank_account(bank_account_id, data)
    if not bank_account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return bank_account


# =============================================================================
# RELEVÉS BANCAIRES
# =============================================================================

@router.post("/bank-statements", response_model=BankStatementResponse, status_code=status.HTTP_201_CREATED)
def create_bank_statement(
    data: BankStatementCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer un relevé bancaire."""
    service = get_finance_service(db, tenant_id)
    return service.create_bank_statement(data, current_user.id)


@router.get("/bank-statements")
def list_bank_statements(
    bank_account_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les relevés bancaires."""
    service = get_finance_service(db, tenant_id)
    items, total = service.list_bank_statements(bank_account_id, skip, limit)
    return {"items": items, "total": total}


@router.get("/bank-statements/{statement_id}", response_model=BankStatementResponse)
def get_bank_statement(
    statement_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer un relevé par ID."""
    service = get_finance_service(db, tenant_id)
    statement = service.get_bank_statement(statement_id)
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")
    return statement


@router.post("/bank-statements/lines/{line_id}/reconcile")
def reconcile_statement_line(
    line_id: UUID,
    entry_line_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Rapprocher une ligne de relevé avec une écriture."""
    service = get_finance_service(db, tenant_id)
    line = service.reconcile_statement_line(line_id, entry_line_id)
    if not line:
        raise HTTPException(
            status_code=400,
            detail="Line not found or already reconciled"
        )
    return {"message": "Line reconciled successfully", "line_id": str(line.id)}


# =============================================================================
# TRANSACTIONS BANCAIRES
# =============================================================================

@router.post("/bank-transactions", response_model=BankTransactionResponse, status_code=status.HTTP_201_CREATED)
def create_bank_transaction(
    data: BankTransactionCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer une transaction bancaire."""
    service = get_finance_service(db, tenant_id)
    return service.create_bank_transaction(data, current_user.id)


@router.get("/bank-transactions")
def list_bank_transactions(
    bank_account_id: UUID | None = None,
    transaction_type: BankTransactionType | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les transactions bancaires."""
    service = get_finance_service(db, tenant_id)
    items, total = service.list_bank_transactions(
        bank_account_id=bank_account_id,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    return {"items": items, "total": total}


# =============================================================================
# TRÉSORERIE - PRÉVISIONS
# =============================================================================

@router.post("/cash-forecasts", response_model=CashForecastResponse, status_code=status.HTTP_201_CREATED)
def create_cash_forecast(
    data: CashForecastCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer une prévision de trésorerie."""
    service = get_finance_service(db, tenant_id)
    return service.create_cash_forecast(data, current_user.id)


@router.get("/cash-forecasts", response_model=list[CashForecastResponse])
def list_cash_forecasts(
    period: ForecastPeriod | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les prévisions de trésorerie."""
    service = get_finance_service(db, tenant_id)
    return service.list_cash_forecasts(period, start_date, end_date)


@router.get("/cash-forecasts/{forecast_id}", response_model=CashForecastResponse)
def get_cash_forecast(
    forecast_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer une prévision par ID."""
    service = get_finance_service(db, tenant_id)
    forecast = service.get_cash_forecast(forecast_id)
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    return forecast


@router.put("/cash-forecasts/{forecast_id}", response_model=CashForecastResponse)
def update_cash_forecast(
    forecast_id: UUID,
    data: CashForecastUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Mettre à jour une prévision."""
    service = get_finance_service(db, tenant_id)
    forecast = service.update_cash_forecast(forecast_id, data)
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    return forecast


# =============================================================================
# CATÉGORIES DE FLUX
# =============================================================================

@router.post("/cash-flow-categories", response_model=CashFlowCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_cash_flow_category(
    data: CashFlowCategoryCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer une catégorie de flux de trésorerie."""
    service = get_finance_service(db, tenant_id)
    return service.create_cash_flow_category(data)


@router.get("/cash-flow-categories", response_model=list[CashFlowCategoryResponse])
def list_cash_flow_categories(
    is_receipt: bool | None = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les catégories de flux."""
    service = get_finance_service(db, tenant_id)
    return service.list_cash_flow_categories(is_receipt)


# =============================================================================
# REPORTING FINANCIER
# =============================================================================

@router.get("/reports/trial-balance", response_model=TrialBalance)
def get_trial_balance(
    start_date: date,
    end_date: date,
    fiscal_year_id: UUID | None = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Générer la balance générale."""
    service = get_finance_service(db, tenant_id)
    return service.get_trial_balance(start_date, end_date, fiscal_year_id)


@router.get("/reports/income-statement", response_model=IncomeStatement)
def get_income_statement(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Générer le compte de résultat."""
    service = get_finance_service(db, tenant_id)
    return service.get_income_statement(start_date, end_date)


@router.post("/reports", response_model=FinancialReportResponse, status_code=status.HTTP_201_CREATED)
def create_financial_report(
    data: FinancialReportCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Générer et sauvegarder un rapport financier."""
    service = get_finance_service(db, tenant_id)
    return service.create_financial_report(data, current_user.id)


@router.get("/reports")
def list_financial_reports(
    report_type: str | None = None,
    fiscal_year_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les rapports financiers."""
    service = get_finance_service(db, tenant_id)
    items, total = service.list_financial_reports(report_type, fiscal_year_id, skip, limit)
    return {"items": items, "total": total}


# =============================================================================
# DASHBOARD
# =============================================================================

@router.get("/dashboard", response_model=FinanceDashboard)
def get_finance_dashboard(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer le dashboard financier."""
    service = get_finance_service(db, tenant_id)
    return service.get_dashboard()
