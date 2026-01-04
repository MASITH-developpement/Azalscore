"""
AZALS MODULE M2 - Schémas Finance
==================================

Schémas Pydantic pour la comptabilité et la trésorerie.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
import json

from .models import (
    AccountType, JournalType, EntryStatus, FiscalYearStatus,
    BankTransactionType, ReconciliationStatus, ForecastPeriod
)


# ============================================================================
# SCHÉMAS COMPTES
# ============================================================================

class AccountBase(BaseModel):
    """Base pour les comptes."""
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: AccountType
    parent_id: Optional[UUID] = None
    is_auxiliary: bool = False
    auxiliary_type: Optional[str] = None
    is_reconcilable: bool = False
    allow_posting: bool = True


class AccountCreate(AccountBase):
    """Création d'un compte."""
    pass


class AccountUpdate(BaseModel):
    """Mise à jour d'un compte."""
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    is_reconcilable: Optional[bool] = None
    allow_posting: Optional[bool] = None
    is_active: Optional[bool] = None


class AccountResponse(AccountBase):
    """Réponse compte."""
    id: UUID
    balance_debit: Decimal = Decimal("0")
    balance_credit: Decimal = Decimal("0")
    balance: Decimal = Decimal("0")
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AccountList(BaseModel):
    """Liste de comptes."""
    items: List[AccountResponse]
    total: int


# ============================================================================
# SCHÉMAS JOURNAUX
# ============================================================================

class JournalBase(BaseModel):
    """Base pour les journaux."""
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    type: JournalType
    default_debit_account_id: Optional[UUID] = None
    default_credit_account_id: Optional[UUID] = None
    sequence_prefix: Optional[str] = None


class JournalCreate(JournalBase):
    """Création d'un journal."""
    pass


class JournalUpdate(BaseModel):
    """Mise à jour d'un journal."""
    name: Optional[str] = None
    default_debit_account_id: Optional[UUID] = None
    default_credit_account_id: Optional[UUID] = None
    sequence_prefix: Optional[str] = None
    is_active: Optional[bool] = None


class JournalResponse(JournalBase):
    """Réponse journal."""
    id: UUID
    is_active: bool = True
    next_sequence: int = 1
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHÉMAS EXERCICES FISCAUX
# ============================================================================

class FiscalYearBase(BaseModel):
    """Base pour les exercices."""
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    start_date: date
    end_date: date


class FiscalYearCreate(FiscalYearBase):
    """Création d'un exercice."""
    pass


class FiscalYearResponse(FiscalYearBase):
    """Réponse exercice."""
    id: UUID
    status: FiscalYearStatus = FiscalYearStatus.OPEN
    closed_at: Optional[datetime] = None
    closed_by: Optional[UUID] = None
    total_debit: Decimal = Decimal("0")
    total_credit: Decimal = Decimal("0")
    result: Decimal = Decimal("0")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FiscalPeriodResponse(BaseModel):
    """Réponse période."""
    id: UUID
    fiscal_year_id: UUID
    name: str
    number: int
    start_date: date
    end_date: date
    is_closed: bool = False
    closed_at: Optional[datetime] = None
    total_debit: Decimal = Decimal("0")
    total_credit: Decimal = Decimal("0")
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHÉMAS ÉCRITURES COMPTABLES
# ============================================================================

class EntryLineBase(BaseModel):
    """Base pour les lignes d'écriture."""
    account_id: UUID
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    label: Optional[str] = None
    partner_id: Optional[UUID] = None
    partner_type: Optional[str] = None
    analytic_account: Optional[str] = None
    analytic_tags: List[str] = Field(default_factory=list)

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
    reconcile_ref: Optional[str] = None
    reconciled_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EntryBase(BaseModel):
    """Base pour les écritures."""
    journal_id: UUID
    date: date
    reference: Optional[str] = None
    description: Optional[str] = None


class EntryCreate(EntryBase):
    """Création d'une écriture."""
    lines: List[EntryLineCreate] = Field(..., min_length=2)  # Au moins 2 lignes


class EntryUpdate(BaseModel):
    """Mise à jour d'une écriture."""
    reference: Optional[str] = None
    description: Optional[str] = None


class EntryResponse(EntryBase):
    """Réponse écriture."""
    id: UUID
    fiscal_year_id: UUID
    number: str
    status: EntryStatus = EntryStatus.DRAFT
    total_debit: Decimal = Decimal("0")
    total_credit: Decimal = Decimal("0")
    source_type: Optional[str] = None
    source_id: Optional[UUID] = None
    validated_by: Optional[UUID] = None
    validated_at: Optional[datetime] = None
    posted_by: Optional[UUID] = None
    posted_at: Optional[datetime] = None
    lines: List[EntryLineResponse] = Field(default_factory=list)
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EntryList(BaseModel):
    """Liste d'écritures."""
    items: List[EntryResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ============================================================================
# SCHÉMAS BANQUE
# ============================================================================

class BankAccountBase(BaseModel):
    """Base pour les comptes bancaires."""
    name: str = Field(..., min_length=1, max_length=255)
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    account_id: Optional[UUID] = None
    journal_id: Optional[UUID] = None
    currency: str = "EUR"
    initial_balance: Decimal = Decimal("0")


class BankAccountCreate(BankAccountBase):
    """Création d'un compte bancaire."""
    pass


class BankAccountUpdate(BaseModel):
    """Mise à jour d'un compte bancaire."""
    name: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    account_id: Optional[UUID] = None
    journal_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class BankAccountResponse(BankAccountBase):
    """Réponse compte bancaire."""
    id: UUID
    current_balance: Decimal = Decimal("0")
    reconciled_balance: Decimal = Decimal("0")
    is_active: bool = True
    is_default: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BankStatementLineBase(BaseModel):
    """Base pour les lignes de relevé."""
    date: date
    value_date: Optional[date] = None
    label: str
    reference: Optional[str] = None
    amount: Decimal


class BankStatementLineCreate(BankStatementLineBase):
    """Création d'une ligne de relevé."""
    pass


class BankStatementLineResponse(BankStatementLineBase):
    """Réponse ligne de relevé."""
    id: UUID
    statement_id: UUID
    status: ReconciliationStatus = ReconciliationStatus.PENDING
    matched_entry_line_id: Optional[UUID] = None
    matched_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BankStatementBase(BaseModel):
    """Base pour les relevés."""
    bank_account_id: UUID
    name: str
    reference: Optional[str] = None
    date: date
    start_date: date
    end_date: date
    opening_balance: Decimal
    closing_balance: Decimal


class BankStatementCreate(BankStatementBase):
    """Création d'un relevé."""
    lines: List[BankStatementLineCreate] = Field(default_factory=list)


class BankStatementResponse(BankStatementBase):
    """Réponse relevé."""
    id: UUID
    total_credits: Decimal = Decimal("0")
    total_debits: Decimal = Decimal("0")
    is_reconciled: bool = False
    reconciled_at: Optional[datetime] = None
    reconciled_by: Optional[UUID] = None
    lines: List[BankStatementLineResponse] = Field(default_factory=list)
    created_by: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BankTransactionBase(BaseModel):
    """Base pour les transactions."""
    bank_account_id: UUID
    type: BankTransactionType
    date: date
    value_date: Optional[date] = None
    amount: Decimal
    label: str
    reference: Optional[str] = None
    partner_name: Optional[str] = None
    category: Optional[str] = None


class BankTransactionCreate(BankTransactionBase):
    """Création d'une transaction."""
    pass


class BankTransactionResponse(BankTransactionBase):
    """Réponse transaction."""
    id: UUID
    currency: str = "EUR"
    entry_line_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHÉMAS TRÉSORERIE
# ============================================================================

class CashForecastBase(BaseModel):
    """Base pour les prévisions."""
    period: ForecastPeriod
    date: date
    opening_balance: Decimal
    expected_receipts: Decimal = Decimal("0")
    expected_payments: Decimal = Decimal("0")
    details: dict = Field(default_factory=dict)


class CashForecastCreate(CashForecastBase):
    """Création d'une prévision."""
    pass


class CashForecastUpdate(BaseModel):
    """Mise à jour d'une prévision."""
    expected_receipts: Optional[Decimal] = None
    expected_payments: Optional[Decimal] = None
    actual_receipts: Optional[Decimal] = None
    actual_payments: Optional[Decimal] = None
    actual_closing: Optional[Decimal] = None
    details: Optional[dict] = None


class CashForecastResponse(CashForecastBase):
    """Réponse prévision."""
    id: UUID
    actual_receipts: Decimal = Decimal("0")
    actual_payments: Decimal = Decimal("0")
    expected_closing: Decimal = Decimal("0")
    actual_closing: Optional[Decimal] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CashFlowCategoryBase(BaseModel):
    """Base pour les catégories de flux."""
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_receipt: bool
    parent_id: Optional[UUID] = None
    order: int = 0
    default_account_id: Optional[UUID] = None


class CashFlowCategoryCreate(CashFlowCategoryBase):
    """Création d'une catégorie."""
    pass


class CashFlowCategoryResponse(CashFlowCategoryBase):
    """Réponse catégorie."""
    id: UUID
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


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
    start_date: date
    end_date: date
    items: List[BalanceSheetItem]
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
    start_date: date
    end_date: date
    revenues: List[IncomeStatementItem]
    expenses: List[IncomeStatementItem]
    total_revenues: Decimal = Decimal("0")
    total_expenses: Decimal = Decimal("0")
    net_income: Decimal = Decimal("0")


class FinancialReportCreate(BaseModel):
    """Création d'un rapport."""
    report_type: str
    start_date: date
    end_date: date
    fiscal_year_id: Optional[UUID] = None
    period_id: Optional[UUID] = None
    parameters: dict = Field(default_factory=dict)


class FinancialReportResponse(BaseModel):
    """Réponse rapport."""
    id: UUID
    report_type: str
    name: str
    fiscal_year_id: Optional[UUID] = None
    period_id: Optional[UUID] = None
    start_date: date
    end_date: date
    data: dict
    parameters: dict = Field(default_factory=dict)
    generated_by: Optional[UUID] = None
    generated_at: datetime
    pdf_url: Optional[str] = None
    excel_url: Optional[str] = None

    class Config:
        from_attributes = True


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
    accounts: List[BalanceSheetItem]
    total_assets: Decimal = Decimal("0")
    total_liabilities: Decimal = Decimal("0")
    total_equity: Decimal = Decimal("0")
    total_revenues: Decimal = Decimal("0")
    total_expenses: Decimal = Decimal("0")
