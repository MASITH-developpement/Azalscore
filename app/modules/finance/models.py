"""
AZALS MODULE M2 - Modèles Finance
==================================

Modèles SQLAlchemy pour la comptabilité et la trésorerie.
"""

import enum
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date,
    Text, ForeignKey, Enum, Numeric, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


# ============================================================================
# ENUMS
# ============================================================================

class AccountType(str, enum.Enum):
    """Type de compte."""
    ASSET = "ASSET"           # Actif
    LIABILITY = "LIABILITY"   # Passif
    EQUITY = "EQUITY"         # Capitaux propres
    REVENUE = "REVENUE"       # Produits
    EXPENSE = "EXPENSE"       # Charges


class JournalType(str, enum.Enum):
    """Type de journal comptable."""
    GENERAL = "GENERAL"
    PURCHASES = "PURCHASES"
    SALES = "SALES"
    BANK = "BANK"
    CASH = "CASH"
    OD = "OD"
    OPENING = "OPENING"
    CLOSING = "CLOSING"


class EntryStatus(str, enum.Enum):
    """Statut d'écriture comptable."""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    POSTED = "POSTED"
    CANCELLED = "CANCELLED"


class FiscalYearStatus(str, enum.Enum):
    """Statut d'exercice fiscal."""
    OPEN = "OPEN"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"


class BankTransactionType(str, enum.Enum):
    """Type de transaction bancaire."""
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"
    TRANSFER = "TRANSFER"
    FEE = "FEE"
    INTEREST = "INTEREST"


class ReconciliationStatus(str, enum.Enum):
    """Statut de rapprochement."""
    PENDING = "PENDING"
    MATCHED = "MATCHED"
    PARTIAL = "PARTIAL"
    UNMATCHED = "UNMATCHED"


class ForecastPeriod(str, enum.Enum):
    """Période de prévision."""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"


# ============================================================================
# MODÈLES PLAN COMPTABLE
# ============================================================================

class Account(Base):
    """Compte du plan comptable."""
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(20), nullable=False)  # Numéro de compte
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Classification
    type = Column(Enum(AccountType), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))

    # Compte auxiliaire
    is_auxiliary = Column(Boolean, default=False)  # Compte auxiliaire
    auxiliary_type = Column(String(50))  # customer, supplier, bank, etc.

    # Paramètres
    is_active = Column(Boolean, default=True)
    is_reconcilable = Column(Boolean, default=False)  # Lettrable
    allow_posting = Column(Boolean, default=True)  # Imputable

    # Soldes (mis à jour par triggers)
    balance_debit = Column(Numeric(15, 2), default=0)
    balance_credit = Column(Numeric(15, 2), default=0)
    balance = Column(Numeric(15, 2), default=0)  # Débit - Crédit ou Crédit - Débit selon type

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    parent = relationship("Account", remote_side=[id], backref="children")
    entry_lines = relationship("JournalEntryLine", back_populates="account")

    __table_args__ = (
        Index("ix_accounts_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_accounts_tenant_type", "tenant_id", "type"),
        Index("ix_accounts_tenant_parent", "tenant_id", "parent_id"),
    )


class Journal(Base):
    """Journal comptable."""
    __tablename__ = "journals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(Enum(JournalType), nullable=False)

    # Compte par défaut
    default_debit_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    default_credit_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))

    # Paramètres
    is_active = Column(Boolean, default=True)
    sequence_prefix = Column(String(10))  # Préfixe numérotation
    next_sequence = Column(Integer, default=1)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    entries = relationship("JournalEntry", back_populates="journal")

    __table_args__ = (
        Index("ix_journals_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_journals_tenant_type", "tenant_id", "type"),
    )


# ============================================================================
# MODÈLES EXERCICES FISCAUX
# ============================================================================

class FiscalYear(Base):
    """Exercice fiscal."""
    __tablename__ = "fiscal_years"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    name = Column(String(100), nullable=False)  # Ex: "Exercice 2026"
    code = Column(String(20), nullable=False)  # Ex: "2026"

    # Dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Statut
    status = Column(Enum(FiscalYearStatus), default=FiscalYearStatus.OPEN)
    closed_at = Column(DateTime)
    closed_by = Column(UUID(as_uuid=True))

    # Totaux (calculés)
    total_debit = Column(Numeric(15, 2), default=0)
    total_credit = Column(Numeric(15, 2), default=0)
    result = Column(Numeric(15, 2), default=0)  # Résultat de l'exercice

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    periods = relationship("FiscalPeriod", back_populates="fiscal_year", cascade="all, delete-orphan")
    entries = relationship("JournalEntry", back_populates="fiscal_year")

    __table_args__ = (
        Index("ix_fiscal_years_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_fiscal_years_tenant_dates", "tenant_id", "start_date", "end_date"),
        CheckConstraint("end_date > start_date", name="check_fiscal_year_dates"),
    )


class FiscalPeriod(Base):
    """Période comptable (mois)."""
    __tablename__ = "fiscal_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    fiscal_year_id = Column(UUID(as_uuid=True), ForeignKey("fiscal_years.id"), nullable=False)

    # Identification
    name = Column(String(100), nullable=False)  # Ex: "Janvier 2026"
    number = Column(Integer, nullable=False)  # 1-12

    # Dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Statut
    is_closed = Column(Boolean, default=False)
    closed_at = Column(DateTime)

    # Totaux période
    total_debit = Column(Numeric(15, 2), default=0)
    total_credit = Column(Numeric(15, 2), default=0)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    fiscal_year = relationship("FiscalYear", back_populates="periods")

    __table_args__ = (
        Index("ix_fiscal_periods_tenant_year", "tenant_id", "fiscal_year_id"),
        Index("ix_fiscal_periods_tenant_number", "tenant_id", "fiscal_year_id", "number", unique=True),
    )


# ============================================================================
# MODÈLES ÉCRITURES COMPTABLES
# ============================================================================

class JournalEntry(Base):
    """Écriture comptable (pièce)."""
    __tablename__ = "journal_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    journal_id = Column(UUID(as_uuid=True), ForeignKey("journals.id"), nullable=False)
    fiscal_year_id = Column(UUID(as_uuid=True), ForeignKey("fiscal_years.id"), nullable=False)

    # Identification
    number = Column(String(50), nullable=False)  # Numéro de pièce
    date = Column(Date, nullable=False)
    reference = Column(String(100))  # Référence externe (facture, etc.)
    description = Column(Text)

    # Statut
    status = Column(Enum(EntryStatus), default=EntryStatus.DRAFT)

    # Totaux
    total_debit = Column(Numeric(15, 2), default=0)
    total_credit = Column(Numeric(15, 2), default=0)

    # Lien avec documents source
    source_type = Column(String(50))  # invoice, payment, etc.
    source_id = Column(UUID(as_uuid=True))

    # Validation
    validated_by = Column(UUID(as_uuid=True))
    validated_at = Column(DateTime)
    posted_by = Column(UUID(as_uuid=True))
    posted_at = Column(DateTime)

    # Métadonnées
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    journal = relationship("Journal", back_populates="entries")
    fiscal_year = relationship("FiscalYear", back_populates="entries")
    lines = relationship("JournalEntryLine", back_populates="entry", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_entries_tenant_number", "tenant_id", "journal_id", "number", unique=True),
        Index("ix_entries_tenant_date", "tenant_id", "date"),
        Index("ix_entries_tenant_status", "tenant_id", "status"),
        Index("ix_entries_tenant_journal", "tenant_id", "journal_id"),
    )


class JournalEntryLine(Base):
    """Ligne d'écriture comptable."""
    __tablename__ = "journal_entry_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)

    # Position
    line_number = Column(Integer, nullable=False)

    # Montants
    debit = Column(Numeric(15, 2), default=0)
    credit = Column(Numeric(15, 2), default=0)

    # Description
    label = Column(String(255))

    # Auxiliaire
    partner_id = Column(UUID(as_uuid=True))  # Client ou fournisseur
    partner_type = Column(String(20))  # customer, supplier

    # Lettrage
    reconcile_ref = Column(String(50))  # Référence lettrage
    reconciled_at = Column(DateTime)

    # Analytique (optionnel)
    analytic_account = Column(String(50))
    analytic_tags = Column(JSON, default=list)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account", back_populates="entry_lines")

    __table_args__ = (
        Index("ix_entry_lines_tenant_entry", "tenant_id", "entry_id"),
        Index("ix_entry_lines_tenant_account", "tenant_id", "account_id"),
        Index("ix_entry_lines_tenant_reconcile", "tenant_id", "reconcile_ref"),
        CheckConstraint("(debit = 0 OR credit = 0)", name="check_debit_or_credit"),
        CheckConstraint("(debit >= 0 AND credit >= 0)", name="check_positive_amounts"),
    )


# ============================================================================
# MODÈLES BANQUE
# ============================================================================

class BankAccount(Base):
    """Compte bancaire."""
    __tablename__ = "bank_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    name = Column(String(255), nullable=False)
    bank_name = Column(String(255))
    account_number = Column(String(50))
    iban = Column(String(50))
    bic = Column(String(20))

    # Compte comptable lié
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    journal_id = Column(UUID(as_uuid=True), ForeignKey("journals.id"))

    # Soldes
    initial_balance = Column(Numeric(15, 2), default=0)
    current_balance = Column(Numeric(15, 2), default=0)
    reconciled_balance = Column(Numeric(15, 2), default=0)

    # Devise
    currency = Column(String(3), default="EUR")

    # Paramètres
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    transactions = relationship("BankTransaction", back_populates="bank_account")
    statements = relationship("BankStatement", back_populates="bank_account")

    __table_args__ = (
        Index("ix_bank_accounts_tenant", "tenant_id"),
        Index("ix_bank_accounts_tenant_iban", "tenant_id", "iban"),
    )


class BankStatement(Base):
    """Relevé bancaire."""
    __tablename__ = "bank_statements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)

    # Identification
    name = Column(String(255), nullable=False)  # Ex: "Relevé Janvier 2026"
    reference = Column(String(100))

    # Dates
    date = Column(Date, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Soldes
    opening_balance = Column(Numeric(15, 2), nullable=False)
    closing_balance = Column(Numeric(15, 2), nullable=False)
    total_credits = Column(Numeric(15, 2), default=0)
    total_debits = Column(Numeric(15, 2), default=0)

    # Statut
    is_reconciled = Column(Boolean, default=False)
    reconciled_at = Column(DateTime)
    reconciled_by = Column(UUID(as_uuid=True))

    # Métadonnées
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    bank_account = relationship("BankAccount", back_populates="statements")
    lines = relationship("BankStatementLine", back_populates="statement", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_bank_statements_tenant_account", "tenant_id", "bank_account_id"),
        Index("ix_bank_statements_tenant_date", "tenant_id", "date"),
    )


class BankStatementLine(Base):
    """Ligne de relevé bancaire."""
    __tablename__ = "bank_statement_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    statement_id = Column(UUID(as_uuid=True), ForeignKey("bank_statements.id", ondelete="CASCADE"), nullable=False)

    # Date et libellé
    date = Column(Date, nullable=False)
    value_date = Column(Date)
    label = Column(String(255), nullable=False)
    reference = Column(String(100))

    # Montant
    amount = Column(Numeric(15, 2), nullable=False)  # Positif = crédit, négatif = débit

    # Rapprochement
    status = Column(Enum(ReconciliationStatus), default=ReconciliationStatus.PENDING)
    matched_entry_line_id = Column(UUID(as_uuid=True), ForeignKey("journal_entry_lines.id"))
    matched_at = Column(DateTime)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    statement = relationship("BankStatement", back_populates="lines")

    __table_args__ = (
        Index("ix_bank_lines_tenant_statement", "tenant_id", "statement_id"),
        Index("ix_bank_lines_tenant_status", "tenant_id", "status"),
    )


class BankTransaction(Base):
    """Transaction bancaire (mouvement réel)."""
    __tablename__ = "bank_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)

    # Type et date
    type = Column(Enum(BankTransactionType), nullable=False)
    date = Column(Date, nullable=False)
    value_date = Column(Date)

    # Montant
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="EUR")

    # Description
    label = Column(String(255), nullable=False)
    reference = Column(String(100))
    partner_name = Column(String(255))

    # Catégorisation
    category = Column(String(100))

    # Lien comptable
    entry_line_id = Column(UUID(as_uuid=True), ForeignKey("journal_entry_lines.id"))

    # Métadonnées
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    bank_account = relationship("BankAccount", back_populates="transactions")

    __table_args__ = (
        Index("ix_bank_trans_tenant_account", "tenant_id", "bank_account_id"),
        Index("ix_bank_trans_tenant_date", "tenant_id", "date"),
        Index("ix_bank_trans_tenant_type", "tenant_id", "type"),
    )


# ============================================================================
# MODÈLES TRÉSORERIE
# ============================================================================

class CashForecast(Base):
    """Prévision de trésorerie."""
    __tablename__ = "cash_forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Période
    period = Column(Enum(ForecastPeriod), nullable=False)
    date = Column(Date, nullable=False)  # Date de début de la période

    # Solde initial
    opening_balance = Column(Numeric(15, 2), nullable=False)

    # Encaissements prévus
    expected_receipts = Column(Numeric(15, 2), default=0)
    actual_receipts = Column(Numeric(15, 2), default=0)

    # Décaissements prévus
    expected_payments = Column(Numeric(15, 2), default=0)
    actual_payments = Column(Numeric(15, 2), default=0)

    # Solde final
    expected_closing = Column(Numeric(15, 2), default=0)
    actual_closing = Column(Numeric(15, 2))

    # Détails
    details = Column(JSON, default=dict)  # Détail par catégorie

    # Métadonnées
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_forecasts_tenant_date", "tenant_id", "period", "date", unique=True),
    )


class CashFlowCategory(Base):
    """Catégorie de flux de trésorerie."""
    __tablename__ = "cash_flow_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Type
    is_receipt = Column(Boolean, nullable=False)  # True = encaissement, False = décaissement

    # Hiérarchie
    parent_id = Column(UUID(as_uuid=True), ForeignKey("cash_flow_categories.id"))
    order = Column(Integer, default=0)

    # Compte comptable par défaut
    default_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))

    # Métadonnées
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_cash_categories_tenant_code", "tenant_id", "code", unique=True),
    )


# ============================================================================
# MODÈLES REPORTING
# ============================================================================

class FinancialReport(Base):
    """Rapport financier généré."""
    __tablename__ = "financial_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Type de rapport
    report_type = Column(String(50), nullable=False)  # balance, income_statement, balance_sheet, etc.
    name = Column(String(255), nullable=False)

    # Période
    fiscal_year_id = Column(UUID(as_uuid=True), ForeignKey("fiscal_years.id"))
    period_id = Column(UUID(as_uuid=True), ForeignKey("fiscal_periods.id"))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Données du rapport
    data = Column(JSON, nullable=False)  # Contenu du rapport

    # Paramètres utilisés
    parameters = Column(JSON, default=dict)

    # Génération
    generated_by = Column(UUID(as_uuid=True))
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Export
    pdf_url = Column(String(500))
    excel_url = Column(String(500))

    __table_args__ = (
        Index("ix_reports_tenant_type", "tenant_id", "report_type"),
        Index("ix_reports_tenant_dates", "tenant_id", "start_date", "end_date"),
    )
