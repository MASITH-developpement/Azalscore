"""
AZALS MODULE - TREASURY: Modèles
=================================

Modèles SQLAlchemy pour la gestion de la trésorerie.
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

class AccountType(str, enum.Enum):
    """Types de comptes bancaires."""
    CURRENT = "CURRENT"              # Compte courant
    SAVINGS = "SAVINGS"              # Compte épargne
    TERM_DEPOSIT = "TERM_DEPOSIT"    # Dépôt à terme
    CREDIT_LINE = "CREDIT_LINE"      # Ligne de crédit


class TransactionType(str, enum.Enum):
    """Types de transactions."""
    CREDIT = "credit"  # Crédit (encaissement)
    DEBIT = "debit"    # Débit (décaissement)


# ============================================================================
# MODÈLES
# ============================================================================

class BankAccount(Base):
    """Compte bancaire."""
    __tablename__ = "treasury_bank_accounts"

    # Clé primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), index=True)  # Code interne (optionnel)
    name = Column(String(255), nullable=False, index=True)  # Nom du compte

    # Banque
    bank_name = Column(String(255), nullable=False)  # Nom de la banque
    iban = Column(String(50), nullable=False)  # IBAN
    bic = Column(String(20))  # BIC/SWIFT
    account_number = Column(String(50))  # Numéro de compte local

    # Type et statut
    account_type = Column(Enum(AccountType, name='treasury_accounttype'),
                         default=AccountType.CURRENT, nullable=False, index=True)
    is_default = Column(Boolean, default=False)  # Compte par défaut
    is_active = Column(Boolean, default=True, index=True)  # Compte actif

    # Soldes
    balance = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)  # Solde actuel
    available_balance = Column(Numeric(15, 2), default=Decimal("0.00"))  # Solde disponible
    pending_in = Column(Numeric(15, 2), default=Decimal("0.00"))  # Encaissements en attente
    pending_out = Column(Numeric(15, 2), default=Decimal("0.00"))  # Décaissements en attente
    currency = Column(String(3), default="EUR", nullable=False)

    # Dates
    opening_date = Column(DateTime)  # Date d'ouverture du compte
    last_sync = Column(DateTime)  # Dernière synchronisation
    last_statement_date = Column(DateTime)  # Dernière date de relevé

    # Contact banque
    contact_name = Column(String(255))  # Nom du contact
    contact_phone = Column(String(50))  # Téléphone
    contact_email = Column(String(255))  # Email

    # Notes
    notes = Column(Text)

    # Métadonnées
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    transactions = relationship("BankTransaction", back_populates="account", lazy="dynamic",
                               cascade="all, delete-orphan")

    # Index
    __table_args__ = (
        Index('idx_treasury_bank_accounts_tenant_id', 'tenant_id'),
        Index('idx_treasury_bank_accounts_code', 'tenant_id', 'code', unique=True),
        Index('idx_treasury_bank_accounts_iban', 'tenant_id', 'iban', unique=True),
        Index('idx_treasury_bank_accounts_type', 'account_type'),
        Index('idx_treasury_bank_accounts_active', 'is_active'),
    )


class BankTransaction(Base):
    """Transaction bancaire."""
    __tablename__ = "treasury_bank_transactions"

    # Clé primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Relation compte
    account_id = Column(UniversalUUID(), ForeignKey("treasury_bank_accounts.id"), nullable=False, index=True)

    # Dates
    date = Column(DateTime, nullable=False, index=True)  # Date de transaction
    value_date = Column(DateTime, nullable=False)  # Date de valeur

    # Description
    description = Column(Text, nullable=False)  # Description/Libellé
    reference = Column(String(100))  # Référence bancaire
    bank_reference = Column(String(100))  # Référence interne banque

    # Montant
    amount = Column(Numeric(15, 2), nullable=False)  # Montant (positif pour crédit, négatif pour débit)
    currency = Column(String(3), default="EUR", nullable=False)
    type = Column(Enum(TransactionType, name='treasury_transactiontype'), nullable=False, index=True)

    # Catégorisation
    category = Column(String(100))  # Catégorie (automatique ou manuelle)

    # Rapprochement bancaire
    reconciled = Column(Boolean, default=False, nullable=False, index=True)
    reconciled_at = Column(DateTime)
    reconciled_by = Column(UniversalUUID(), ForeignKey("users.id"))

    # Document lié (pour rapprochement)
    linked_document_type = Column(String(50))  # Type de document (INVOICE, PURCHASE_INVOICE, etc.)
    linked_document_id = Column(UniversalUUID())  # ID du document

    # Notes
    notes = Column(Text)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    account = relationship("BankAccount", back_populates="transactions")

    # Index
    __table_args__ = (
        Index('idx_treasury_transactions_tenant_id', 'tenant_id'),
        Index('idx_treasury_transactions_account', 'account_id'),
        Index('idx_treasury_transactions_date', 'date'),
        Index('idx_treasury_transactions_type', 'type'),
        Index('idx_treasury_transactions_reconciled', 'reconciled'),
        Index('idx_treasury_transactions_document', 'linked_document_type', 'linked_document_id'),
        CheckConstraint('amount != 0', name='check_amount_not_zero'),
    )
