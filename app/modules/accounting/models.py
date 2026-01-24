"""
AZALS MODULE - ACCOUNTING: Modèles
===================================

Modèles SQLAlchemy pour la gestion comptable.
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text, CheckConstraint
from sqlalchemy.orm import relationship

from app.core.types import UniversalUUID
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class FiscalYearStatus(str, enum.Enum):
    """Statuts d'exercice comptable."""
    OPEN = "OPEN"          # Ouvert (saisie autorisée)
    CLOSED = "CLOSED"      # Clôturé (saisie interdite)
    ARCHIVED = "ARCHIVED"  # Archivé


class EntryStatus(str, enum.Enum):
    """Statuts d'écriture comptable."""
    DRAFT = "DRAFT"          # Brouillon (modifiable)
    POSTED = "POSTED"        # Comptabilisée (validée)
    VALIDATED = "VALIDATED"  # Validée définitivement
    CANCELLED = "CANCELLED"  # Annulée


class AccountType(str, enum.Enum):
    """Types de comptes comptables."""
    ASSET = "ASSET"              # Actif (classe 1, 2, 3, 5)
    LIABILITY = "LIABILITY"      # Passif (classe 1, 4)
    EQUITY = "EQUITY"            # Capitaux propres (classe 1)
    REVENUE = "REVENUE"          # Produits (classe 7)
    EXPENSE = "EXPENSE"          # Charges (classe 6)
    SPECIAL = "SPECIAL"          # Comptes spéciaux (classe 8)


# ============================================================================
# MODÈLES
# ============================================================================

class FiscalYear(Base):
    """Exercice comptable."""
    __tablename__ = "accounting_fiscal_years"

    # Clé primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    name = Column(String(100), nullable=False)  # Ex: "Exercice 2024"
    code = Column(String(20), nullable=False)   # Ex: "FY2024"

    # Période
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Statut
    status = Column(Enum(FiscalYearStatus, name='accounting_fiscalyearstatus'),
                   default=FiscalYearStatus.OPEN, nullable=False, index=True)

    # Clôture
    closed_at = Column(DateTime)
    closed_by = Column(UniversalUUID(), ForeignKey("users.id"))

    # Notes
    notes = Column(Text)

    # Métadonnées
    is_active = Column(Boolean, default=True)
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    journal_entries = relationship("AccountingJournalEntry", back_populates="fiscal_year", lazy="dynamic")

    # Index
    __table_args__ = (
        Index('idx_accounting_fiscal_years_tenant_id', 'tenant_id'),
        Index('idx_accounting_fiscal_years_code', 'tenant_id', 'code', unique=True),
        Index('idx_accounting_fiscal_years_period', 'start_date', 'end_date'),
        Index('idx_accounting_fiscal_years_status', 'status'),
        CheckConstraint('end_date > start_date', name='check_fiscal_year_period'),
    )


class ChartOfAccounts(Base):
    """Plan comptable - Comptes comptables."""
    __tablename__ = "accounting_chart_of_accounts"

    # Clé primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    account_number = Column(String(20), nullable=False, index=True)  # Ex: "411000", "701000"
    account_label = Column(String(255), nullable=False)               # Ex: "Clients", "Ventes de produits finis"

    # Classification
    account_type = Column(Enum(AccountType, name='accounting_accounttype'), nullable=False, index=True)
    account_class = Column(String(1), nullable=False, index=True)  # Classe PCG (1-8)
    parent_account = Column(String(20))  # Compte parent (pour hiérarchie)

    # Comportement
    is_auxiliary = Column(Boolean, default=False)  # Compte auxiliaire (ex: clients, fournisseurs)
    requires_analytics = Column(Boolean, default=False)  # Nécessite analytique

    # Solde
    opening_balance_debit = Column(Numeric(15, 2), default=Decimal("0.00"))
    opening_balance_credit = Column(Numeric(15, 2), default=Decimal("0.00"))

    # Notes
    notes = Column(Text)

    # Métadonnées
    is_active = Column(Boolean, default=True)
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    debit_entries = relationship("AccountingJournalEntryLine",
                                foreign_keys="AccountingJournalEntryLine.account_number",
                                back_populates="account",
                                lazy="dynamic",
                                primaryjoin="and_(ChartOfAccounts.account_number==AccountingJournalEntryLine.account_number, "
                                           "ChartOfAccounts.tenant_id==AccountingJournalEntryLine.tenant_id)")

    # Index
    __table_args__ = (
        Index('idx_accounting_coa_tenant_id', 'tenant_id'),
        Index('idx_accounting_coa_account_number', 'tenant_id', 'account_number', unique=True),
        Index('idx_accounting_coa_type', 'account_type'),
        Index('idx_accounting_coa_class', 'account_class'),
    )


class AccountingJournalEntry(Base):
    """Écriture comptable (en-tête de pièce)."""
    __tablename__ = "accounting_journal_entries"

    # Clé primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    entry_number = Column(String(50), nullable=False, index=True)  # Ex: "VT-2024-001"
    piece_number = Column(String(50), nullable=False)              # Numéro de pièce justificative

    # Journal
    journal_code = Column(String(10), nullable=False, index=True)  # VT, AC, BQ, CA, OD, AN
    journal_label = Column(String(100))                             # Libellé du journal

    # Exercice
    fiscal_year_id = Column(UniversalUUID(), ForeignKey("accounting_fiscal_years.id"), nullable=False, index=True)

    # Date et période
    entry_date = Column(DateTime, nullable=False, index=True)  # Date de l'écriture
    posting_date = Column(DateTime)                             # Date de comptabilisation
    period = Column(String(7), nullable=False, index=True)     # Période (YYYY-MM)

    # Libellé
    label = Column(Text, nullable=False)  # Libellé général de l'écriture

    # Origine (traçabilité)
    document_type = Column(String(50))  # Type de document source (INVOICE, ORDER, PAYMENT, etc.)
    document_id = Column(UniversalUUID())  # ID du document source

    # Statut
    status = Column(Enum(EntryStatus, name='accounting_entrystatus'),
                   default=EntryStatus.DRAFT, nullable=False, index=True)

    # Équilibre (calculé depuis lignes)
    total_debit = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_credit = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    is_balanced = Column(Boolean, default=False, nullable=False)  # total_debit == total_credit

    # Currency
    currency = Column(String(3), default="EUR")

    # Validation
    posted_at = Column(DateTime)
    posted_by = Column(UniversalUUID(), ForeignKey("users.id"))
    validated_at = Column(DateTime)
    validated_by = Column(UniversalUUID(), ForeignKey("users.id"))

    # Notes
    notes = Column(Text)

    # Métadonnées
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    fiscal_year = relationship("FiscalYear", back_populates="journal_entries")
    lines = relationship("AccountingJournalEntryLine", back_populates="entry", cascade="all, delete-orphan")

    # Index
    __table_args__ = (
        Index('idx_accounting_entries_tenant_id', 'tenant_id'),
        Index('idx_accounting_entries_number', 'tenant_id', 'entry_number', unique=True),
        Index('idx_accounting_entries_journal', 'journal_code'),
        Index('idx_accounting_entries_fiscal_year', 'fiscal_year_id'),
        Index('idx_accounting_entries_date', 'entry_date'),
        Index('idx_accounting_entries_period', 'period'),
        Index('idx_accounting_entries_status', 'status'),
        Index('idx_accounting_entries_document', 'document_type', 'document_id'),
        CheckConstraint('total_debit >= 0', name='check_total_debit_positive'),
        CheckConstraint('total_credit >= 0', name='check_total_credit_positive'),
    )


class AccountingJournalEntryLine(Base):
    """Ligne d'écriture comptable."""
    __tablename__ = "accounting_journal_entry_lines"

    # Clé primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Relation écriture
    entry_id = Column(UniversalUUID(), ForeignKey("accounting_journal_entries.id"), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)  # Numéro de ligne (1, 2, 3...)

    # Compte
    account_number = Column(String(20), nullable=False, index=True)
    account_label = Column(String(255), nullable=False)

    # Libellé
    label = Column(Text)  # Libellé spécifique de la ligne (peut différer de l'écriture)

    # Montants
    debit = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    credit = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    currency = Column(String(3), default="EUR")

    # Analytique (optionnel)
    analytics_code = Column(String(50))  # Code analytique
    analytics_label = Column(String(255))  # Libellé analytique

    # Auxiliaire (optionnel pour comptes tiers)
    auxiliary_code = Column(String(50))  # Code auxiliaire (ex: code client, fournisseur)

    # Notes
    notes = Column(Text)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    entry = relationship("AccountingJournalEntry", back_populates="lines")
    account = relationship("ChartOfAccounts",
                          foreign_keys=[account_number, tenant_id],
                          primaryjoin="and_(AccountingJournalEntryLine.account_number==ChartOfAccounts.account_number, "
                                     "AccountingJournalEntryLine.tenant_id==ChartOfAccounts.tenant_id)",
                          viewonly=True)

    # Index
    __table_args__ = (
        Index('idx_accounting_entry_lines_tenant_id', 'tenant_id'),
        Index('idx_accounting_entry_lines_entry', 'entry_id'),
        Index('idx_accounting_entry_lines_account', 'account_number'),
        Index('idx_accounting_entry_lines_analytics', 'analytics_code'),
        CheckConstraint('debit >= 0', name='check_debit_positive'),
        CheckConstraint('credit >= 0', name='check_credit_positive'),
        CheckConstraint('NOT (debit > 0 AND credit > 0)', name='check_debit_or_credit_only'),
    )
