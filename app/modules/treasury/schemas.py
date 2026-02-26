"""
AZALS MODULE - TREASURY: Schémas
=================================

Schémas Pydantic pour validation et sérialisation.
"""
from __future__ import annotations


import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .models import AccountType, TransactionType


# ============================================================================
# BANK ACCOUNT SCHEMAS
# ============================================================================

class BankAccountBase(BaseModel):
    """Schéma de base pour compte bancaire."""
    code: Optional[str] = Field(None, max_length=50, description="Code interne")
    name: str = Field(..., max_length=255, description="Nom du compte")
    bank_name: str = Field(..., max_length=255, description="Nom de la banque")
    iban: str = Field(..., max_length=50, description="IBAN")
    bic: Optional[str] = Field(None, max_length=20, description="BIC/SWIFT")
    account_number: Optional[str] = Field(None, max_length=50, description="Numéro de compte")
    account_type: AccountType = Field(AccountType.CURRENT, description="Type de compte")
    is_default: bool = Field(False, description="Compte par défaut")
    opening_date: Optional[datetime.datetime] = None
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class BankAccountCreate(BankAccountBase):
    """Création d'un compte bancaire."""
    balance: Decimal = Field(Decimal("0.00"), description="Solde initial")
    currency: str = Field("EUR", max_length=3)


class BankAccountUpdate(BaseModel):
    """Mise à jour d'un compte bancaire."""
    name: Optional[str] = Field(None, max_length=255)
    bank_name: Optional[str] = Field(None, max_length=255)
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class BankAccountResponse(BankAccountBase):
    """Réponse compte bancaire."""
    id: UUID
    tenant_id: str
    is_active: bool
    balance: Decimal
    available_balance: Optional[Decimal] = None
    pending_in: Decimal
    pending_out: Decimal
    currency: str
    last_sync: Optional[datetime.datetime] = None
    last_statement_date: Optional[datetime.datetime] = None
    transactions_count: Optional[int] = None
    unreconciled_count: Optional[int] = None
    created_by: Optional[UUID] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


# ============================================================================
# TRANSACTION SCHEMAS
# ============================================================================

class BankTransactionBase(BaseModel):
    """Schéma de base pour transaction bancaire."""
    date: datetime.datetime = Field(..., description="Date de transaction")
    value_date: datetime.datetime = Field(..., description="Date de valeur")
    description: str = Field(..., description="Description")
    reference: Optional[str] = Field(None, max_length=100)
    bank_reference: Optional[str] = Field(None, max_length=100)
    amount: Decimal = Field(..., description="Montant")
    currency: str = Field("EUR", max_length=3)
    type: TransactionType = Field(..., description="Type (credit/debit)")
    category: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class BankTransactionCreate(BankTransactionBase):
    """Création d'une transaction bancaire."""
    account_id: UUID = Field(..., description="ID du compte bancaire")


class BankTransactionUpdate(BaseModel):
    """Mise à jour d'une transaction bancaire."""
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class BankTransactionResponse(BankTransactionBase):
    """Réponse transaction bancaire."""
    id: UUID
    tenant_id: str
    account_id: UUID
    account_name: Optional[str] = None
    reconciled: bool
    reconciled_at: Optional[datetime.datetime] = None
    reconciled_by: Optional[UUID] = None
    linked_document: Optional[dict] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


# ============================================================================
# RECONCILIATION SCHEMAS
# ============================================================================

class ReconciliationRequest(BaseModel):
    """Demande de rapprochement bancaire."""
    document_type: str = Field(..., max_length=50, description="Type de document (INVOICE, PURCHASE_INVOICE, etc.)")
    document_id: UUID = Field(..., description="ID du document à lier")


# ============================================================================
# TREASURY SUMMARY & FORECAST
# ============================================================================

class AccountSummary(BaseModel):
    """Résumé simplifié d'un compte pour le dashboard."""
    id: str
    name: str
    bank_name: str = ""
    balance: Decimal
    currency: str = "EUR"


class TreasurySummary(BaseModel):
    """Résumé de trésorerie pour dashboard."""
    total_balance: Decimal = Field(..., description="Solde total")
    total_pending_in: Decimal = Field(..., description="Encaissements en attente")
    total_pending_out: Decimal = Field(..., description="Décaissements en attente")
    forecast_7d: Decimal = Field(..., description="Prévision 7 jours")
    forecast_30d: Decimal = Field(..., description="Prévision 30 jours")
    accounts: List[AccountSummary] = Field(default_factory=list)


class ForecastData(BaseModel):
    """Données de prévision de trésorerie."""
    date: datetime.date
    projected_balance: Decimal
    pending_in: Decimal
    pending_out: Decimal


# ============================================================================
# PAGINATION
# ============================================================================

class PaginatedBankAccounts(BaseModel):
    """Liste paginée de comptes bancaires."""
    total: int
    page: int
    per_page: int
    pages: int
    items: List[BankAccountResponse]


class PaginatedBankTransactions(BaseModel):
    """Liste paginée de transactions bancaires."""
    total: int
    page: int
    per_page: int
    pages: int
    items: List[BankTransactionResponse]
