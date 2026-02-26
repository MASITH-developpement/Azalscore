"""
AZALS MODULE M2 - Schémas Finance
==================================

Schémas Pydantic pour la comptabilité et la trésorerie.
"""
from __future__ import annotations



import json
import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import (
    AccountType,
    BankTransactionType,
    EntryStatus,
    FiscalYearStatus,
    ForecastPeriod,
    JournalType,
    ReconciliationStatus,
)

# ============================================================================
# SCHÉMAS COMPTES
# ============================================================================

class AccountBase(BaseModel):
    """Base pour les comptes."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    account_type: AccountType = Field(..., alias="type")
    parent_id: UUID | None = None
    is_auxiliary: bool = False
    auxiliary_type: str | None = None
    is_reconcilable: bool = False
    allow_posting: bool = True


class AccountCreate(AccountBase):
    """Création d'un compte."""
    pass


class AccountUpdate(BaseModel):
    """Mise à jour d'un compte."""
    name: str | None = None
    description: str | None = None
    parent_id: UUID | None = None
    is_reconcilable: bool | None = None
    allow_posting: bool | None = None
    is_active: bool | None = None


class AccountResponse(AccountBase):
    """Réponse compte."""
    id: UUID
    balance_debit: Decimal = Decimal("0")
    balance_credit: Decimal = Decimal("0")
    balance: Decimal = Decimal("0")
    is_active: bool = True
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class AccountList(BaseModel):
    """Liste de comptes."""
    items: list[AccountResponse]
    total: int


# ============================================================================
# SCHÉMAS JOURNAUX
# ============================================================================

class JournalBase(BaseModel):
    """Base pour les journaux."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    journal_type: JournalType = Field(..., alias="type")
    default_debit_account_id: UUID | None = None
    default_credit_account_id: UUID | None = None
    sequence_prefix: str | None = None


class JournalCreate(JournalBase):
    """Création d'un journal."""
    pass


class JournalUpdate(BaseModel):
    """Mise à jour d'un journal."""
    name: str | None = None
    default_debit_account_id: UUID | None = None
    default_credit_account_id: UUID | None = None
    sequence_prefix: str | None = None
    is_active: bool | None = None


class JournalResponse(JournalBase):
    """Réponse journal."""
    id: UUID
    is_active: bool = True
    next_sequence: int = 1
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS EXERCICES FISCAUX
# ============================================================================

class FiscalYearBase(BaseModel):
    """Base pour les exercices."""
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    start_date: datetime.date
    end_date: datetime.date


class FiscalYearCreate(FiscalYearBase):
    """Création d'un exercice."""
    pass


class FiscalYearResponse(FiscalYearBase):
    """Réponse exercice."""
    id: UUID
    status: FiscalYearStatus = FiscalYearStatus.OPEN
    closed_at: datetime.datetime | None = None
    closed_by: UUID | None = None
    total_debit: Decimal = Decimal("0")
    total_credit: Decimal = Decimal("0")
    result: Decimal = Decimal("0")
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class FiscalPeriodResponse(BaseModel):
    """Réponse période."""
    id: UUID
    fiscal_year_id: UUID
    name: str
    number: int
    start_date: datetime.date
    end_date: datetime.date
    is_closed: bool = False
    closed_at: datetime.datetime | None = None
    total_debit: Decimal = Decimal("0")
    total_credit: Decimal = Decimal("0")
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS ÉCRITURES COMPTABLES
# ============================================================================

class EntryLineBase(BaseModel):
    """Base pour les lignes d'écriture."""
    account_id: UUID
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    label: str | None = None
    partner_id: UUID | None = None
    partner_type: str | None = None
    analytic_account: str | None = None
    analytic_tags: list[str] = Field(default_factory=list)

    @field_validator('analytic_tags', mode='before')
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else []
        return v or []


class EntryLineCreate(EntryLineBase):
    """Création d'une ligne."""
    pass


class EntryLineResponse(EntryLineBase):
    """Réponse ligne."""
    id: UUID
    entry_id: UUID
    line_number: int
    reconcile_ref: str | None = None
    reconciled_at: datetime.datetime | None = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class EntryBase(BaseModel):
    """Base pour les écritures."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    journal_id: UUID
    entry_date: datetime.date = Field(..., alias="date")
    reference: str | None = None
    description: str | None = None


class EntryCreate(EntryBase):
    """Création d'une écriture."""
    lines: list[EntryLineCreate] = Field(..., min_length=2)  # Au moins 2 lignes


class EntryUpdate(BaseModel):
    """Mise à jour d'une écriture."""
    reference: str | None = None
    description: str | None = None


class EntryResponse(EntryBase):
    """Réponse écriture."""
    id: UUID
    fiscal_year_id: UUID
    number: str
    status: EntryStatus = EntryStatus.DRAFT
    total_debit: Decimal = Decimal("0")
    total_credit: Decimal = Decimal("0")
    source_type: str | None = None
    source_id: UUID | None = None
    validated_by: UUID | None = None
    validated_at: datetime.datetime | None = None
    posted_by: UUID | None = None
    posted_at: datetime.datetime | None = None
    lines: list[EntryLineResponse] = Field(default_factory=list)
    created_by: UUID | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class EntryList(BaseModel):
    """Liste d'écritures."""
    items: list[EntryResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ============================================================================
# SCHÉMAS BANQUE
# ============================================================================

class BankAccountBase(BaseModel):
    """Base pour les comptes bancaires."""
    name: str = Field(..., min_length=1, max_length=255)
    bank_name: str | None = None
    account_number: str | None = None
    iban: str | None = None
    bic: str | None = None
    account_id: UUID | None = None
    journal_id: UUID | None = None
    currency: str = "EUR"
    initial_balance: Decimal = Decimal("0")


class BankAccountCreate(BankAccountBase):
    """Création d'un compte bancaire."""
    pass


class BankAccountUpdate(BaseModel):
    """Mise à jour d'un compte bancaire."""
    name: str | None = None
    bank_name: str | None = None
    account_number: str | None = None
    iban: str | None = None
    bic: str | None = None
    account_id: UUID | None = None
    journal_id: UUID | None = None
    is_active: bool | None = None
    is_default: bool | None = None


class BankAccountResponse(BankAccountBase):
    """Réponse compte bancaire."""
    id: UUID
    current_balance: Decimal = Decimal("0")
    reconciled_balance: Decimal = Decimal("0")
    is_active: bool = True
    is_default: bool = False
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class BankStatementLineBase(BaseModel):
    """Base pour les lignes de relevé."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    line_date: datetime.date = Field(..., alias="date")
    value_date: datetime.date | None = None
    label: str
    reference: str | None = None
    amount: Decimal


class BankStatementLineCreate(BankStatementLineBase):
    """Création d'une ligne de relevé."""
    pass


class BankStatementLineResponse(BankStatementLineBase):
    """Réponse ligne de relevé."""
    id: UUID
    statement_id: UUID
    status: ReconciliationStatus = ReconciliationStatus.PENDING
    matched_entry_line_id: UUID | None = None
    matched_at: datetime.datetime | None = None
    created_at: datetime.datetime



class BankStatementBase(BaseModel):
    """Base pour les relevés."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    bank_account_id: UUID
    name: str
    reference: str | None = None
    statement_date: datetime.date = Field(..., alias="date")
    start_date: datetime.date
    end_date: datetime.date
    opening_balance: Decimal
    closing_balance: Decimal


class BankStatementCreate(BankStatementBase):
    """Création d'un relevé."""
    lines: list[BankStatementLineCreate] = Field(default_factory=list)


class BankStatementResponse(BankStatementBase):
    """Réponse relevé."""
    id: UUID
    total_credits: Decimal = Decimal("0")
    total_debits: Decimal = Decimal("0")
    is_reconciled: bool = False
    reconciled_at: datetime.datetime | None = None
    reconciled_by: UUID | None = None
    lines: list[BankStatementLineResponse] = Field(default_factory=list)
    created_by: UUID | None = None
    created_at: datetime.datetime



class BankTransactionBase(BaseModel):
    """Base pour les transactions."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    bank_account_id: UUID
    transaction_type: BankTransactionType = Field(..., alias="type")
    transaction_date: datetime.date = Field(..., alias="date")
    value_date: datetime.date | None = None
    amount: Decimal
    label: str
    reference: str | None = None
    partner_name: str | None = None
    category: str | None = None


class BankTransactionCreate(BankTransactionBase):
    """Création d'une transaction."""
    pass


class BankTransactionResponse(BankTransactionBase):
    """Réponse transaction."""
    id: UUID
    currency: str = "EUR"
    entry_line_id: UUID | None = None
    created_by: UUID | None = None
    created_at: datetime.datetime



# ============================================================================
# SCHÉMAS TRÉSORERIE
# ============================================================================

class CashForecastBase(BaseModel):
    """Base pour les prévisions."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    period: ForecastPeriod
    forecast_date: datetime.date = Field(..., alias="date")
    opening_balance: Decimal
    expected_receipts: Decimal = Decimal("0")
    expected_payments: Decimal = Decimal("0")
    details: dict = Field(default_factory=dict)


class CashForecastCreate(CashForecastBase):
    """Création d'une prévision."""
    pass


class CashForecastUpdate(BaseModel):
    """Mise à jour d'une prévision."""
    expected_receipts: Decimal | None = None
    expected_payments: Decimal | None = None
    actual_receipts: Decimal | None = None
    actual_payments: Decimal | None = None
    actual_closing: Decimal | None = None
    details: dict | None = None


class CashForecastResponse(CashForecastBase):
    """Réponse prévision."""
    id: UUID
    actual_receipts: Decimal = Decimal("0")
    actual_payments: Decimal = Decimal("0")
    expected_closing: Decimal = Decimal("0")
    actual_closing: Decimal | None = None
    created_by: UUID | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class CashFlowCategoryBase(BaseModel):
    """Base pour les catégories de flux."""
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    is_receipt: bool
    parent_id: UUID | None = None
    order: int = 0
    default_account_id: UUID | None = None


class CashFlowCategoryCreate(CashFlowCategoryBase):
    """Création d'une catégorie."""
    pass


class CashFlowCategoryResponse(CashFlowCategoryBase):
    """Réponse catégorie."""
    id: UUID
    is_active: bool = True
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS REPORTING
# ============================================================================

class BalanceSheetItem(BaseModel):
    """Élément du bilan."""
    account_code: str
    account_name: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    balance: Decimal = Decimal("0")


class TrialBalance(BaseModel):
    """Balance générale."""
    start_date: datetime.date
    end_date: datetime.date
    items: list[BalanceSheetItem]
    total_debit: Decimal = Decimal("0")
    total_credit: Decimal = Decimal("0")
    is_balanced: bool = True


class IncomeStatementItem(BaseModel):
    """Élément du compte de résultat."""
    category: str
    label: str
    amount: Decimal = Decimal("0")
    is_subtotal: bool = False


class IncomeStatement(BaseModel):
    """Compte de résultat."""
    start_date: datetime.date
    end_date: datetime.date
    revenues: list[IncomeStatementItem]
    expenses: list[IncomeStatementItem]
    total_revenues: Decimal = Decimal("0")
    total_expenses: Decimal = Decimal("0")
    net_income: Decimal = Decimal("0")


class FinancialReportCreate(BaseModel):
    """Création d'un rapport."""
    report_type: str
    start_date: datetime.date
    end_date: datetime.date
    fiscal_year_id: UUID | None = None
    period_id: UUID | None = None
    parameters: dict = Field(default_factory=dict)


class FinancialReportResponse(BaseModel):
    """Réponse rapport."""
    id: UUID
    report_type: str
    name: str
    fiscal_year_id: UUID | None = None
    period_id: UUID | None = None
    start_date: datetime.date
    end_date: datetime.date
    data: dict
    parameters: dict = Field(default_factory=dict)
    generated_by: UUID | None = None
    generated_at: datetime.datetime
    pdf_url: str | None = None
    excel_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS DASHBOARD
# ============================================================================

class FinanceDashboard(BaseModel):
    """Dashboard financier."""
    # Soldes
    cash_balance: Decimal = Decimal("0")
    bank_balance: Decimal = Decimal("0")
    total_receivables: Decimal = Decimal("0")
    total_payables: Decimal = Decimal("0")

    # Exercice en cours
    current_year_revenues: Decimal = Decimal("0")
    current_year_expenses: Decimal = Decimal("0")
    current_year_result: Decimal = Decimal("0")

    # Période en cours
    period_revenues: Decimal = Decimal("0")
    period_expenses: Decimal = Decimal("0")
    period_result: Decimal = Decimal("0")

    # Comptabilité
    pending_entries: int = 0
    unreconciled_transactions: int = 0

    # Trésorerie
    forecast_30_days: Decimal = Decimal("0")
    forecast_90_days: Decimal = Decimal("0")


class AccountBalanceReport(BaseModel):
    """Rapport de balance par compte."""
    accounts: list[BalanceSheetItem]
    total_assets: Decimal = Decimal("0")
    total_liabilities: Decimal = Decimal("0")
    total_equity: Decimal = Decimal("0")
    total_revenues: Decimal = Decimal("0")
    total_expenses: Decimal = Decimal("0")
