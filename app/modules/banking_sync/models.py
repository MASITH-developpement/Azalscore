"""
AZALS MODULE - Modèles Synchronisation Bancaire
================================================

Modèles SQLAlchemy pour la synchronisation bancaire automatique.
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.core.types import JSON, UniversalUUID
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class BankProvider(str, enum.Enum):
    """Fournisseur d'agrégation bancaire."""
    BUDGET_INSIGHT = "BUDGET_INSIGHT"  # Français, bien intégré banques FR
    BRIDGE = "BRIDGE"  # Français, API moderne
    PLAID = "PLAID"  # International
    INTERNAL = "INTERNAL"  # Import manuel


class ConnectionStatus(str, enum.Enum):
    """Statut d'une connexion bancaire."""
    ACTIVE = "ACTIVE"  # Connexion active
    PENDING = "PENDING"  # En attente d'activation
    ERROR = "ERROR"  # Erreur de connexion
    EXPIRED = "EXPIRED"  # Credentials expirés
    SUSPENDED = "SUSPENDED"  # Suspendue par l'utilisateur
    DELETED = "DELETED"  # Supprimée


class SyncStatus(str, enum.Enum):
    """Statut d'une synchronisation."""
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"  # Partiellement réussie
    FAILED = "FAILED"
    IN_PROGRESS = "IN_PROGRESS"


class TransactionStatus(str, enum.Enum):
    """Statut d'une transaction importée."""
    PENDING = "PENDING"  # En attente de rapprochement
    MATCHED = "MATCHED"  # Rapprochée automatiquement
    REVIEWED = "REVIEWED"  # Revue manuellement
    IGNORED = "IGNORED"  # Ignorée


# ============================================================================
# MODELS
# ============================================================================

class BankConnection(Base):
    """
    Connexion bancaire.
    
    Représente une connexion authentifiée à une banque via un provider
    d'agrégation (Budget Insight, Bridge, etc.).
    """
    __tablename__ = "banking_connections"

    # Identifiants
    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UniversalUUID, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Provider et identifiants externes
    provider = Column(Enum(BankProvider), nullable=False, default=BankProvider.BUDGET_INSIGHT)
    provider_connection_id = Column(String(255), unique=True, index=True)
    provider_user_id = Column(String(255))  # ID utilisateur chez le provider
    
    # Informations bancaires
    bank_name = Column(String(255), nullable=False)
    bank_code = Column(String(50))  # Code banque (ex: BNP, SG, etc.)
    bank_logo_url = Column(String(512))
    
    # Statut et configuration
    status = Column(Enum(ConnectionStatus), nullable=False, default=ConnectionStatus.PENDING, index=True)
    is_active = Column(Boolean, default=True)
    auto_sync = Column(Boolean, default=True)  # Synchronisation automatique
    sync_frequency_hours = Column(Integer, default=24)  # Fréquence de sync
    
    # Credentials (chiffrés)
    # Note: Les credentials sont généralement stockés chez le provider
    # on garde juste un token d'accès chiffré
    access_token_encrypted = Column(Text)
    refresh_token_encrypted = Column(Text)
    
    # Métadonnées
    metadata = Column(JSON, default=dict)
    
    # Dates
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID, ForeignKey("users.id"), nullable=True)
    
    # Dernière synchronisation
    last_sync_at = Column(DateTime, index=True)
    last_sync_status = Column(Enum(SyncStatus))
    next_sync_at = Column(DateTime)  # Prochaine sync planifiée
    
    # Relations
    accounts = relationship("BankAccount", back_populates="connection", cascade="all, delete-orphan")
    sync_logs = relationship("BankSyncLog", back_populates="connection", cascade="all, delete-orphan")
    
    # Index
    __table_args__ = (
        Index("idx_banking_conn_tenant_status", "tenant_id", "status"),
    )

    def __repr__(self):
        return f"<BankConnection {self.bank_name} - {self.status}>"


class BankAccount(Base):
    """
    Compte bancaire synchronisé.
    
    Un compte bancaire découvert via une connexion bancaire.
    """
    __tablename__ = "banking_accounts"

    # Identifiants
    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    connection_id = Column(UniversalUUID, ForeignKey("banking_connections.id"), nullable=False, index=True)
    tenant_id = Column(UniversalUUID, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Provider et identifiants externes
    provider_account_id = Column(String(255), unique=True, index=True)
    
    # Informations compte
    account_name = Column(String(255), nullable=False)
    account_number = Column(String(100))  # IBAN masqué
    account_type = Column(String(50))  # checking, savings, credit_card, etc.
    currency = Column(String(3), default="EUR")
    
    # Solde
    balance = Column(Numeric(15, 2))
    balance_date = Column(DateTime)
    
    # Liaison avec compte comptable AzalScore
    linked_account_id = Column(UniversalUUID, ForeignKey("finance_accounts.id"), nullable=True)
    
    # Configuration
    is_active = Column(Boolean, default=True)
    import_transactions = Column(Boolean, default=True)
    
    # Métadonnées
    metadata = Column(JSON, default=dict)
    
    # Dates
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    connection = relationship("BankConnection", back_populates="accounts")
    transactions = relationship("BankTransaction", back_populates="account", cascade="all, delete-orphan")
    
    # Index
    __table_args__ = (
        Index("idx_banking_account_tenant", "tenant_id", "is_active"),
    )

    def __repr__(self):
        return f"<BankAccount {self.account_name}>"


class BankTransaction(Base):
    """
    Transaction bancaire importée.
    
    Transaction découverte lors de la synchronisation avec la banque.
    """
    __tablename__ = "banking_transactions"

    # Identifiants
    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    account_id = Column(UniversalUUID, ForeignKey("banking_accounts.id"), nullable=False, index=True)
    tenant_id = Column(UniversalUUID, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Provider et identifiants externes
    provider_transaction_id = Column(String(255), unique=True, index=True)
    
    # Informations transaction
    transaction_date = Column(DateTime, nullable=False, index=True)
    value_date = Column(DateTime)  # Date de valeur
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="EUR")
    
    # Description
    description = Column(Text, nullable=False)
    original_description = Column(Text)  # Description brute de la banque
    category = Column(String(100))  # Catégorie provider
    
    # Partie prenante
    counterparty_name = Column(String(255))
    counterparty_iban = Column(String(100))
    
    # Rapprochement
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, index=True)
    matched_entry_id = Column(UniversalUUID, ForeignKey("finance_entries.id"), nullable=True)
    confidence_score = Column(Float)  # Score de confiance matching (0-1)
    
    # Métadonnées
    metadata = Column(JSON, default=dict)
    
    # Dates
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    imported_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    reviewed_at = Column(DateTime)
    reviewed_by = Column(UniversalUUID, ForeignKey("users.id"), nullable=True)
    
    # Relations
    account = relationship("BankAccount", back_populates="transactions")
    
    # Index
    __table_args__ = (
        Index("idx_banking_tx_tenant_date", "tenant_id", "transaction_date"),
        Index("idx_banking_tx_status", "tenant_id", "status"),
    )

    def __repr__(self):
        return f"<BankTransaction {self.amount} {self.currency} - {self.description[:30]}>"


class BankSyncLog(Base):
    """
    Journal des synchronisations bancaires.
    
    Trace de chaque synchronisation effectuée avec une connexion bancaire.
    """
    __tablename__ = "banking_sync_logs"

    # Identifiants
    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    connection_id = Column(UniversalUUID, ForeignKey("banking_connections.id"), nullable=False, index=True)
    tenant_id = Column(UniversalUUID, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Statut et résultats
    status = Column(Enum(SyncStatus), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # Résultats
    accounts_synced = Column(Integer, default=0)
    transactions_imported = Column(Integer, default=0)
    transactions_updated = Column(Integer, default=0)
    transactions_skipped = Column(Integer, default=0)
    
    # Erreurs
    error_message = Column(Text)
    error_code = Column(String(50))
    
    # Détails
    details = Column(JSON, default=dict)
    
    # Source
    triggered_by = Column(String(50))  # cron, manual, webhook, etc.
    triggered_by_user = Column(UniversalUUID, ForeignKey("users.id"), nullable=True)
    
    # Relations
    connection = relationship("BankConnection", back_populates="sync_logs")
    
    # Index
    __table_args__ = (
        Index("idx_banking_sync_tenant_status", "tenant_id", "status"),
    )

    def __repr__(self):
        return f"<BankSyncLog {self.status} - {self.started_at}>"
