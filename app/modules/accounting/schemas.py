"""
AZALS MODULE - ACCOUNTING: Schémas
===================================

Schémas Pydantic pour validation et sérialisation.
"""

import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from .models import AccountType, EntryStatus, FiscalYearStatus


# ============================================================================
# FISCAL YEAR SCHEMAS
# ============================================================================

class FiscalYearBase(BaseModel):
    """Schéma de base pour exercice comptable."""
    name: str = Field(..., max_length=100, description="Nom de l'exercice")
    code: str = Field(..., max_length=20, description="Code de l'exercice")
    start_date: datetime.datetime = Field(..., description="Date de début")
    end_date: datetime.datetime = Field(..., description="Date de fin")
    notes: Optional[str] = None


class FiscalYearCreate(FiscalYearBase):
    """Création d'un exercice comptable."""
    pass


class FiscalYearUpdate(BaseModel):
    """Mise à jour d'un exercice comptable."""
    name: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class FiscalYearResponse(FiscalYearBase):
    """Réponse exercice comptable."""
    id: UUID
    tenant_id: str
    status: FiscalYearStatus
    closed_at: Optional[datetime.datetime] = None
    closed_by: Optional[UUID] = None
    is_active: bool
    created_by: Optional[UUID] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


# ============================================================================
# CHART OF ACCOUNTS SCHEMAS
# ============================================================================

class ChartOfAccountsBase(BaseModel):
    """Schéma de base pour compte comptable."""
    account_number: str = Field(..., max_length=20, description="Numéro de compte")
    account_label: str = Field(..., max_length=255, description="Libellé du compte")
    account_type: AccountType = Field(..., description="Type de compte")
    parent_account: Optional[str] = Field(None, max_length=20, description="Compte parent")
    is_auxiliary: bool = Field(False, description="Compte auxiliaire")
    requires_analytics: bool = Field(False, description="Nécessite analytique")
    opening_balance_debit: Decimal = Field(Decimal("0.00"), description="Solde d'ouverture débit")
    opening_balance_credit: Decimal = Field(Decimal("0.00"), description="Solde d'ouverture crédit")
    notes: Optional[str] = None

    @field_validator('account_number')
    @classmethod
    def validate_account_number(cls, v: str) -> str:
        """Valider le numéro de compte."""
        if not v or not v[0].isdigit():
            raise ValueError("Le numéro de compte doit commencer par un chiffre")
        return v


class ChartOfAccountsCreate(ChartOfAccountsBase):
    """Création d'un compte comptable."""
    pass


class ChartOfAccountsUpdate(BaseModel):
    """Mise à jour d'un compte comptable."""
    account_label: Optional[str] = Field(None, max_length=255)
    is_auxiliary: Optional[bool] = None
    requires_analytics: Optional[bool] = None
    notes: Optional[str] = None


class ChartOfAccountsResponse(ChartOfAccountsBase):
    """Réponse compte comptable."""
    id: UUID
    tenant_id: str
    account_class: str
    is_active: bool
    created_by: Optional[UUID] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


# ============================================================================
# JOURNAL ENTRY SCHEMAS
# ============================================================================

class JournalEntryLineBase(BaseModel):
    """Schéma de base pour ligne d'écriture."""
    account_number: str = Field(..., max_length=20, description="Numéro de compte")
    account_label: str = Field(..., max_length=255, description="Libellé du compte")
    label: Optional[str] = Field(None, description="Libellé de la ligne")
    debit: Decimal = Field(Decimal("0.00"), ge=0, description="Montant débit")
    credit: Decimal = Field(Decimal("0.00"), ge=0, description="Montant crédit")
    analytics_code: Optional[str] = Field(None, max_length=50)
    analytics_label: Optional[str] = Field(None, max_length=255)
    auxiliary_code: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None

    @field_validator('debit', 'credit')
    @classmethod
    def validate_debit_credit(cls, v: Decimal, info) -> Decimal:
        """Valider que débit OU crédit est saisi, pas les deux."""
        values = info.data
        if 'debit' in values and 'credit' in values:
            if values['debit'] > 0 and values['credit'] > 0:
                raise ValueError("Une ligne ne peut avoir à la fois débit ET crédit")
        return v


class JournalEntryLineCreate(JournalEntryLineBase):
    """Création d'une ligne d'écriture."""
    pass


class JournalEntryLineResponse(JournalEntryLineBase):
    """Réponse ligne d'écriture."""
    id: UUID
    tenant_id: str
    entry_id: UUID
    line_number: int
    currency: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class JournalEntryBase(BaseModel):
    """Schéma de base pour écriture comptable."""
    piece_number: str = Field(..., max_length=50, description="Numéro de pièce justificative")
    journal_code: str = Field(..., max_length=10, description="Code journal (VT, AC, BQ, CA, OD, AN)")
    journal_label: Optional[str] = Field(None, max_length=100, description="Libellé du journal")
    entry_date: datetime.datetime = Field(..., description="Date de l'écriture")
    label: str = Field(..., description="Libellé de l'écriture")
    document_type: Optional[str] = Field(None, max_length=50)
    document_id: Optional[UUID] = None
    currency: str = Field("EUR", max_length=3)
    notes: Optional[str] = None


class JournalEntryCreate(JournalEntryBase):
    """Création d'une écriture comptable."""
    fiscal_year_id: UUID = Field(..., description="ID de l'exercice comptable")
    lines: List[JournalEntryLineCreate] = Field(..., min_length=2, description="Lignes d'écriture (min 2)")

    @field_validator('lines')
    @classmethod
    def validate_balanced_entry(cls, v: List[JournalEntryLineCreate]) -> List[JournalEntryLineCreate]:
        """Valider que l'écriture est équilibrée (débit = crédit)."""
        total_debit = sum(line.debit for line in v)
        total_credit = sum(line.credit for line in v)

        if total_debit != total_credit:
            raise ValueError(
                f"L'écriture n'est pas équilibrée: débit={total_debit}, crédit={total_credit}"
            )

        return v


class JournalEntryUpdate(BaseModel):
    """Mise à jour d'une écriture comptable."""
    piece_number: Optional[str] = Field(None, max_length=50)
    journal_label: Optional[str] = Field(None, max_length=100)
    entry_date: Optional[datetime.datetime] = None
    label: Optional[str] = None
    notes: Optional[str] = None
    lines: Optional[List[JournalEntryLineCreate]] = Field(None, min_length=2)

    @field_validator('lines')
    @classmethod
    def validate_balanced_entry(cls, v: Optional[List[JournalEntryLineCreate]]) -> Optional[List[JournalEntryLineCreate]]:
        """Valider que l'écriture est équilibrée."""
        if v is None:
            return v

        total_debit = sum(line.debit for line in v)
        total_credit = sum(line.credit for line in v)

        if total_debit != total_credit:
            raise ValueError(
                f"L'écriture n'est pas équilibrée: débit={total_debit}, crédit={total_credit}"
            )

        return v


class JournalEntryResponse(JournalEntryBase):
    """Réponse écriture comptable."""
    id: UUID
    tenant_id: str
    entry_number: str
    fiscal_year_id: UUID
    period: str
    status: EntryStatus
    total_debit: Decimal
    total_credit: Decimal
    is_balanced: bool
    posted_at: Optional[datetime.datetime] = None
    posted_by: Optional[UUID] = None
    validated_at: Optional[datetime.datetime] = None
    validated_by: Optional[UUID] = None
    created_by: Optional[UUID] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    lines: List[JournalEntryLineResponse] = []

    class Config:
        from_attributes = True


# ============================================================================
# ACCOUNTING SUMMARY & REPORTS
# ============================================================================

class AccountingSummary(BaseModel):
    """Résumé comptable pour dashboard."""
    total_assets: Decimal = Field(..., description="Actif total")
    total_liabilities: Decimal = Field(..., description="Passif total")
    total_equity: Decimal = Field(..., description="Capitaux propres")
    revenue: Decimal = Field(..., description="Chiffre d'affaires (produits)")
    expenses: Decimal = Field(..., description="Charges")
    net_income: Decimal = Field(..., description="Résultat net")
    currency: str = "EUR"


class AccountingStatus(BaseModel):
    """Statut de la comptabilité pour monitoring."""
    status: str = Field(..., description="Indicateur visuel (🟢 ou 🟠)")
    entries_up_to_date: bool = Field(..., description="Ecritures à jour")
    last_closure_date: Optional[datetime.date] = Field(None, description="Date dernière clôture")
    pending_entries_count: int = Field(0, description="Nombre d'écritures en attente")
    days_since_closure: Optional[int] = Field(None, description="Jours depuis dernière clôture")


class LedgerAccount(BaseModel):
    """Compte du grand livre."""
    account_number: str
    account_label: str
    debit_total: Decimal
    credit_total: Decimal
    balance: Decimal
    currency: str = "EUR"


class BalanceEntry(BaseModel):
    """Entrée de balance."""
    account_number: str
    account_label: str
    opening_debit: Decimal
    opening_credit: Decimal
    period_debit: Decimal
    period_credit: Decimal
    closing_debit: Decimal
    closing_credit: Decimal


# ============================================================================
# PAGINATION
# ============================================================================

class PaginatedFiscalYears(BaseModel):
    """Liste paginée d'exercices comptables."""
    total: int
    page: int
    per_page: int
    pages: int
    items: List[FiscalYearResponse]


class PaginatedAccounts(BaseModel):
    """Liste paginée de comptes."""
    total: int
    page: int
    per_page: int
    pages: int
    items: List[ChartOfAccountsResponse]


class PaginatedJournalEntries(BaseModel):
    """Liste paginée d'écritures."""
    total: int
    page: int
    per_page: int
    pages: int
    items: List[JournalEntryResponse]


class PaginatedLedgerAccounts(BaseModel):
    """Liste paginée de comptes du grand livre."""
    total: int
    page: int
    per_page: int
    pages: int
    items: List[LedgerAccount]


class PaginatedBalanceEntries(BaseModel):
    """Liste paginée d'entrées de balance."""
    total: int
    page: int
    per_page: int
    pages: int
    items: List[BalanceEntry]
