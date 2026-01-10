"""
AZALS MODULE M2A - Modèles Comptabilité Automatisée
====================================================

Modèles SQLAlchemy pour l'automatisation comptable complète.
"""

import enum
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Date,
    Text, ForeignKey, Enum, Numeric, Index, CheckConstraint,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.db import Base
from app.core.types import UniversalUUID, JSON


# ============================================================================
# ENUMS
# ============================================================================

class DocumentType(str, enum.Enum):
    """Type de document source."""
    INVOICE_RECEIVED = "INVOICE_RECEIVED"       # Facture fournisseur reçue
    INVOICE_SENT = "INVOICE_SENT"               # Facture client émise
    EXPENSE_NOTE = "EXPENSE_NOTE"               # Note de frais
    CREDIT_NOTE_RECEIVED = "CREDIT_NOTE_RECEIVED"  # Avoir fournisseur
    CREDIT_NOTE_SENT = "CREDIT_NOTE_SENT"       # Avoir client
    QUOTE = "QUOTE"                             # Devis
    PURCHASE_ORDER = "PURCHASE_ORDER"           # Bon de commande
    DELIVERY_NOTE = "DELIVERY_NOTE"             # Bon de livraison
    BANK_STATEMENT = "BANK_STATEMENT"           # Relevé bancaire
    OTHER = "OTHER"                             # Autre document


class DocumentStatus(str, enum.Enum):
    """Statut de traitement du document."""
    RECEIVED = "RECEIVED"                       # Reçu, non traité
    PROCESSING = "PROCESSING"                   # En cours de traitement OCR/IA
    ANALYZED = "ANALYZED"                       # Analysé par IA
    PENDING_VALIDATION = "PENDING_VALIDATION"   # En attente validation expert
    VALIDATED = "VALIDATED"                     # Validé
    ACCOUNTED = "ACCOUNTED"                     # Comptabilisé
    REJECTED = "REJECTED"                       # Rejeté
    ERROR = "ERROR"                             # Erreur de traitement


class DocumentSource(str, enum.Enum):
    """Source d'entrée du document."""
    EMAIL = "EMAIL"                             # Reçu par email
    UPLOAD = "UPLOAD"                           # Upload manuel
    MOBILE_SCAN = "MOBILE_SCAN"                 # Scan mobile
    API = "API"                                 # API fournisseur/client
    BANK_SYNC = "BANK_SYNC"                     # Synchronisation bancaire
    INTERNAL = "INTERNAL"                       # Généré en interne


class ConfidenceLevel(str, enum.Enum):
    """Niveau de confiance IA."""
    HIGH = "HIGH"                               # > 95% - Pas de validation nécessaire
    MEDIUM = "MEDIUM"                           # 80-95% - Validation optionnelle
    LOW = "LOW"                                 # 60-80% - Validation requise
    VERY_LOW = "VERY_LOW"                       # < 60% - Révision manuelle nécessaire


class BankConnectionStatus(str, enum.Enum):
    """Statut de connexion bancaire."""
    ACTIVE = "ACTIVE"                           # Connexion active
    EXPIRED = "EXPIRED"                         # Token expiré
    REQUIRES_ACTION = "REQUIRES_ACTION"         # Action utilisateur requise
    ERROR = "ERROR"                             # Erreur de connexion
    DISCONNECTED = "DISCONNECTED"               # Déconnecté


class PaymentStatus(str, enum.Enum):
    """Statut de paiement."""
    UNPAID = "UNPAID"                           # Non payé
    PARTIALLY_PAID = "PARTIALLY_PAID"           # Partiellement payé
    PAID = "PAID"                               # Payé intégralement
    OVERPAID = "OVERPAID"                       # Trop-perçu
    CANCELLED = "CANCELLED"                     # Annulé


class ReconciliationStatusAuto(str, enum.Enum):
    """Statut de rapprochement automatique."""
    PENDING = "PENDING"                         # En attente
    MATCHED = "MATCHED"                         # Rapproché automatiquement
    PARTIAL = "PARTIAL"                         # Rapprochement partiel
    MANUAL = "MANUAL"                           # Rapproché manuellement
    UNMATCHED = "UNMATCHED"                     # Non rapproché


class AlertType(str, enum.Enum):
    """Type d'alerte."""
    DOCUMENT_UNREADABLE = "DOCUMENT_UNREADABLE"   # Document illisible
    MISSING_INFO = "MISSING_INFO"                 # Information manquante
    LOW_CONFIDENCE = "LOW_CONFIDENCE"             # Confiance IA faible
    DUPLICATE_SUSPECTED = "DUPLICATE_SUSPECTED"   # Doublon suspecté
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"           # Montant incohérent
    TAX_ERROR = "TAX_ERROR"                       # Erreur de TVA
    OVERDUE_PAYMENT = "OVERDUE_PAYMENT"           # Paiement en retard
    CASH_FLOW_WARNING = "CASH_FLOW_WARNING"       # Alerte trésorerie
    RECONCILIATION_ISSUE = "RECONCILIATION_ISSUE" # Problème de rapprochement


class AlertSeverity(str, enum.Enum):
    """Sévérité d'alerte."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ViewType(str, enum.Enum):
    """Type de vue utilisateur."""
    DIRIGEANT = "DIRIGEANT"                     # Vue dirigeant
    ASSISTANTE = "ASSISTANTE"                   # Vue assistante
    EXPERT_COMPTABLE = "EXPERT_COMPTABLE"       # Vue expert-comptable


class SyncType(str, enum.Enum):
    """Type de synchronisation bancaire."""
    MANUAL = "MANUAL"                           # Manuelle (à la demande)
    SCHEDULED = "SCHEDULED"                     # Planifiée
    ON_DEMAND = "ON_DEMAND"                     # À l'ouverture du dashboard


class SyncStatus(str, enum.Enum):
    """Statut de synchronisation."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EmailInboxType(str, enum.Enum):
    """Type de boîte email."""
    INVOICES = "INVOICES"                       # factures@
    EXPENSE_NOTES = "EXPENSE_NOTES"             # notesdefrais@
    GENERAL = "GENERAL"                         # Générique


# ============================================================================
# MODÈLES DOCUMENTS
# ============================================================================

class AccountingDocument(Base):
    """Document source pour comptabilité (facture, note de frais, etc.)."""
    __tablename__ = "accounting_documents"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Type et source
    document_type = Column(Enum(DocumentType), nullable=False)
    source = Column(Enum(DocumentSource), nullable=False)
    status = Column(Enum(DocumentStatus), nullable=False, default=DocumentStatus.RECEIVED)

    # Identification
    reference = Column(String(100))                    # Numéro de facture/document
    external_id = Column(String(255))                  # ID externe

    # Fichier original
    original_filename = Column(String(255))
    file_path = Column(String(500))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    file_hash = Column(String(64))                     # SHA-256 pour détection doublons

    # Dates
    document_date = Column(Date)
    due_date = Column(Date)
    received_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    processed_at = Column(DateTime)

    # Partenaire (fournisseur/client)
    partner_id = Column(UniversalUUID())
    partner_name = Column(String(255))
    partner_tax_id = Column(String(50))                # SIRET, TVA intracommunautaire

    # Montants (extraits par OCR/IA)
    amount_untaxed = Column(Numeric(15, 2))            # HT
    amount_tax = Column(Numeric(15, 2))                # TVA
    amount_total = Column(Numeric(15, 2))              # TTC
    currency = Column(String(3), default="EUR")

    # Paiement
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.UNPAID)
    amount_paid = Column(Numeric(15, 2), default=0)
    amount_remaining = Column(Numeric(15, 2))

    # OCR Data brutes
    ocr_raw_text = Column(Text)
    ocr_confidence = Column(Numeric(5, 2))             # Score OCR global 0-100

    # IA Classification
    ai_confidence = Column(Enum(ConfidenceLevel))
    ai_confidence_score = Column(Numeric(5, 2))        # Score numérique 0-100
    ai_suggested_account = Column(String(20))          # Compte comptable suggéré
    ai_suggested_journal = Column(String(20))          # Journal suggéré
    ai_analysis = Column(JSON)                         # Analyse complète IA

    # Écriture comptable générée
    journal_entry_id = Column(UniversalUUID(), ForeignKey("journal_entries.id"))

    # Validation
    requires_validation = Column(Boolean, default=False)
    validated_by = Column(UniversalUUID())
    validated_at = Column(DateTime)
    validation_notes = Column(Text)

    # Source email
    email_from = Column(String(255))
    email_subject = Column(String(500))
    email_received_at = Column(DateTime)

    # Métadonnées
    tags = Column(JSON, default=list)
    custom_fields = Column(JSON, default=dict)
    notes = Column(Text)

    # Audit
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    ocr_results = relationship("OCRResult", back_populates="document", cascade="all, delete-orphan")
    ai_classifications = relationship("AIClassification", back_populates="document", cascade="all, delete-orphan")
    auto_entries = relationship("AutoEntry", back_populates="document")
    alerts = relationship("AccountingAlert", back_populates="document")
    reconciliation_history = relationship("ReconciliationHistory", back_populates="document")

    __table_args__ = (
        Index("idx_accdocs_tenant", "tenant_id"),
        Index("idx_accdocs_tenant_status", "tenant_id", "status"),
        Index("idx_accdocs_tenant_type", "tenant_id", "document_type"),
        Index("idx_accdocs_tenant_date", "tenant_id", "document_date"),
        Index("idx_accdocs_tenant_partner", "tenant_id", "partner_id"),
        Index("idx_accdocs_tenant_payment", "tenant_id", "payment_status"),
        Index("idx_accdocs_file_hash", "tenant_id", "file_hash"),
        Index("idx_accdocs_reference", "tenant_id", "reference"),
    )


class OCRResult(Base):
    """Résultats OCR détaillés pour un document."""
    __tablename__ = "accounting_ocr_results"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    document_id = Column(UniversalUUID(), ForeignKey("accounting_documents.id", ondelete="CASCADE"), nullable=False)

    # Moteur OCR utilisé
    ocr_engine = Column(String(50), nullable=False)    # tesseract, aws_textract, azure_cognitive
    ocr_version = Column(String(20))

    # Résultat global
    processing_time_ms = Column(Integer)
    overall_confidence = Column(Numeric(5, 2))

    # Texte brut extrait
    raw_text = Column(Text)
    structured_data = Column(JSON)                     # Données structurées extraites

    # Champs extraits avec confiance
    extracted_fields = Column(JSON, nullable=False)    # {field_name: {value, confidence, bounding_box}}

    # Erreurs éventuelles
    errors = Column(JSON, default=list)
    warnings = Column(JSON, default=list)

    # Métadonnées image
    image_quality_score = Column(Numeric(5, 2))
    image_resolution = Column(String(20))
    page_count = Column(Integer, default=1)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relations
    document = relationship("AccountingDocument", back_populates="ocr_results")

    __table_args__ = (
        Index("idx_ocr_tenant_doc", "tenant_id", "document_id"),
    )


class AIClassification(Base):
    """Classification IA d'un document."""
    __tablename__ = "accounting_ai_classifications"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    document_id = Column(UniversalUUID(), ForeignKey("accounting_documents.id", ondelete="CASCADE"), nullable=False)

    # Modèle IA utilisé
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(20))

    # Classification document
    document_type_predicted = Column(Enum(DocumentType))
    document_type_confidence = Column(Numeric(5, 2))

    # Extraction entités
    vendor_name = Column(String(255))
    vendor_confidence = Column(Numeric(5, 2))

    invoice_number = Column(String(100))
    invoice_number_confidence = Column(Numeric(5, 2))

    invoice_date = Column(Date)
    invoice_date_confidence = Column(Numeric(5, 2))

    due_date = Column(Date)
    due_date_confidence = Column(Numeric(5, 2))

    # Montants
    amount_untaxed = Column(Numeric(15, 2))
    amount_untaxed_confidence = Column(Numeric(5, 2))

    amount_tax = Column(Numeric(15, 2))
    amount_tax_confidence = Column(Numeric(5, 2))

    amount_total = Column(Numeric(15, 2))
    amount_total_confidence = Column(Numeric(5, 2))

    # Détail TVA
    tax_rates = Column(JSON)                           # [{rate: 20, amount: 100, confidence: 95}]

    # Classification comptable
    suggested_account_code = Column(String(20))
    suggested_account_confidence = Column(Numeric(5, 2))

    suggested_journal_code = Column(String(20))
    suggested_journal_confidence = Column(Numeric(5, 2))

    # Catégorisation
    expense_category = Column(String(100))
    expense_category_confidence = Column(Numeric(5, 2))

    # Confiance globale
    overall_confidence = Column(Enum(ConfidenceLevel), nullable=False)
    overall_confidence_score = Column(Numeric(5, 2), nullable=False)

    # Raisons de la classification
    classification_reasons = Column(JSON)

    # Apprentissage
    was_corrected = Column(Boolean, default=False)
    corrected_by = Column(UniversalUUID())
    corrected_at = Column(DateTime)
    correction_feedback = Column(Text)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relations
    document = relationship("AccountingDocument", back_populates="ai_classifications")

    __table_args__ = (
        Index("idx_aiclass_tenant_doc", "tenant_id", "document_id"),
        Index("idx_aiclass_tenant_confidence", "tenant_id", "overall_confidence"),
    )


class AutoEntry(Base):
    """Écriture comptable générée automatiquement."""
    __tablename__ = "accounting_auto_entries"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    document_id = Column(UniversalUUID(), ForeignKey("accounting_documents.id"), nullable=False)

    # Écriture générée
    journal_entry_id = Column(UniversalUUID(), ForeignKey("journal_entries.id"))

    # Confiance IA
    confidence_level = Column(Enum(ConfidenceLevel), nullable=False)
    confidence_score = Column(Numeric(5, 2), nullable=False)

    # Schéma d'écriture appliqué
    entry_template = Column(String(100))
    accounting_rules_applied = Column(JSON)

    # Lignes proposées (avant création effective)
    proposed_lines = Column(JSON, nullable=False)      # [{account_code, debit, credit, label}]

    # Validation
    auto_validated = Column(Boolean, default=False)    # Validé automatiquement (haute confiance)
    requires_review = Column(Boolean, default=True)
    reviewed_by = Column(UniversalUUID())
    reviewed_at = Column(DateTime)

    # Modifications
    was_modified = Column(Boolean, default=False)
    original_lines = Column(JSON)
    modification_reason = Column(Text)

    # Statut
    is_posted = Column(Boolean, default=False)
    posted_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    document = relationship("AccountingDocument", back_populates="auto_entries")

    __table_args__ = (
        Index("idx_autoentry_tenant_doc", "tenant_id", "document_id"),
        Index("idx_autoentry_tenant_confidence", "tenant_id", "confidence_level"),
        Index("idx_autoentry_tenant_review", "tenant_id", "requires_review"),
    )


# ============================================================================
# MODÈLES CONNEXION BANCAIRE (MODE PULL)
# ============================================================================

class BankConnection(Base):
    """Connexion Open Banking (mode PULL)."""
    __tablename__ = "accounting_bank_connections"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Institution bancaire
    institution_id = Column(String(100), nullable=False)
    institution_name = Column(String(255), nullable=False)
    institution_logo_url = Column(String(500))

    # Connexion
    provider = Column(String(50), nullable=False)       # plaid, bridge, nordigen
    connection_id = Column(String(255), nullable=False)
    status = Column(Enum(BankConnectionStatus), nullable=False, default=BankConnectionStatus.ACTIVE)

    # Tokens (chiffrés - à utiliser avec le service de chiffrement)
    access_token_encrypted = Column(Text)
    refresh_token_encrypted = Column(Text)
    token_expires_at = Column(DateTime)

    # Consentement
    consent_expires_at = Column(DateTime)
    last_consent_renewed_at = Column(DateTime)

    # Dernière synchronisation
    last_sync_at = Column(DateTime)
    last_sync_status = Column(String(50))
    last_sync_error = Column(Text)

    # Comptes liés
    linked_accounts = Column(JSON, default=list)

    # Metadonnees
    extra_data = Column(JSON, default=dict)

    # Audit
    created_by = Column(UniversalUUID(), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    synced_accounts = relationship("SyncedBankAccount", back_populates="connection", cascade="all, delete-orphan")
    sync_sessions = relationship("BankSyncSession", back_populates="connection", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_bankconn_tenant", "tenant_id"),
        Index("idx_bankconn_tenant_status", "tenant_id", "status"),
        UniqueConstraint("tenant_id", "provider", "connection_id", name="uq_bankconn_provider"),
    )


class SyncedBankAccount(Base):
    """Compte bancaire synchronisé via Open Banking."""
    __tablename__ = "accounting_synced_bank_accounts"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    connection_id = Column(UniversalUUID(), ForeignKey("accounting_bank_connections.id", ondelete="CASCADE"), nullable=False)

    # Compte bancaire interne lié
    bank_account_id = Column(UniversalUUID(), ForeignKey("bank_accounts.id"))

    # Identification externe
    external_account_id = Column(String(255), nullable=False)
    account_name = Column(String(255), nullable=False)
    account_number_masked = Column(String(50))         # ****1234
    iban_masked = Column(String(50))

    # Type de compte
    account_type = Column(String(50))                  # checking, savings, credit_card
    account_subtype = Column(String(50))

    # Soldes (mis à jour à chaque sync)
    balance_current = Column(Numeric(15, 2))
    balance_available = Column(Numeric(15, 2))
    balance_limit = Column(Numeric(15, 2))             # Pour cartes de crédit
    balance_currency = Column(String(3), default="EUR")
    balance_updated_at = Column(DateTime)

    # Synchronisation
    is_sync_enabled = Column(Boolean, default=True)
    last_transaction_date = Column(Date)
    oldest_transaction_date = Column(Date)

    # Metadonnees
    extra_data = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    connection = relationship("BankConnection", back_populates="synced_accounts")
    transactions = relationship("SyncedTransaction", back_populates="synced_account", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_syncedacc_tenant", "tenant_id"),
        Index("idx_syncedacc_connection", "connection_id"),
        UniqueConstraint("tenant_id", "connection_id", "external_account_id", name="uq_syncedacc_external"),
    )


class SyncedTransaction(Base):
    """Transaction bancaire synchronisée."""
    __tablename__ = "accounting_synced_transactions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    synced_account_id = Column(UniversalUUID(), ForeignKey("accounting_synced_bank_accounts.id", ondelete="CASCADE"), nullable=False)

    # Identification
    external_transaction_id = Column(String(255), nullable=False)

    # Transaction
    transaction_date = Column(Date, nullable=False)
    value_date = Column(Date)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="EUR")

    # Description
    description = Column(String(500))
    merchant_name = Column(String(255))
    merchant_category = Column(String(100))

    # Catégorisation automatique
    ai_category = Column(String(100))
    ai_category_confidence = Column(Numeric(5, 2))

    # Rapprochement
    reconciliation_status = Column(Enum(ReconciliationStatusAuto), default=ReconciliationStatusAuto.PENDING)
    matched_document_id = Column(UniversalUUID(), ForeignKey("accounting_documents.id"))
    matched_entry_line_id = Column(UniversalUUID(), ForeignKey("journal_entry_lines.id"))
    matched_at = Column(DateTime)
    match_confidence = Column(Numeric(5, 2))

    # Métadonnées bancaires
    raw_data = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    synced_account = relationship("SyncedBankAccount", back_populates="transactions")
    reconciliation_history = relationship("ReconciliationHistory", back_populates="transaction")

    __table_args__ = (
        Index("idx_syncedtrans_tenant", "tenant_id"),
        Index("idx_syncedtrans_account", "synced_account_id"),
        Index("idx_syncedtrans_date", "tenant_id", "transaction_date"),
        Index("idx_syncedtrans_recon", "tenant_id", "reconciliation_status"),
        UniqueConstraint("tenant_id", "synced_account_id", "external_transaction_id", name="uq_syncedtrans_external"),
    )


class BankSyncSession(Base):
    """Session de synchronisation bancaire."""
    __tablename__ = "accounting_bank_sync_sessions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    connection_id = Column(UniversalUUID(), ForeignKey("accounting_bank_connections.id"), nullable=False)

    # Type de sync
    sync_type = Column(Enum(SyncType), nullable=False)
    triggered_by = Column(UniversalUUID())

    # Statut
    status = Column(Enum(SyncStatus), nullable=False, default=SyncStatus.PENDING)

    # Période synchronisée
    sync_from_date = Column(Date)
    sync_to_date = Column(Date)

    # Résultats
    accounts_synced = Column(Integer, default=0)
    transactions_fetched = Column(Integer, default=0)
    transactions_new = Column(Integer, default=0)
    transactions_updated = Column(Integer, default=0)
    reconciliations_auto = Column(Integer, default=0)

    # Erreurs
    error_message = Column(Text)
    error_details = Column(JSON)

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relations
    connection = relationship("BankConnection", back_populates="sync_sessions")

    __table_args__ = (
        Index("idx_banksync_tenant", "tenant_id"),
        Index("idx_banksync_connection", "connection_id"),
        Index("idx_banksync_status", "tenant_id", "status"),
    )


# ============================================================================
# MODÈLES RAPPROCHEMENT
# ============================================================================

class ReconciliationRule(Base):
    """Règle de rapprochement automatique."""
    __tablename__ = "accounting_reconciliation_rules"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Conditions de matching
    match_criteria = Column(JSON, nullable=False)

    # Action si match
    auto_reconcile = Column(Boolean, default=False)
    min_confidence = Column(Numeric(5, 2), default=90)

    # Compte comptable par défaut
    default_account_code = Column(String(20))
    default_tax_code = Column(String(20))

    # Priorité
    priority = Column(Integer, default=0)

    # Activation
    is_active = Column(Boolean, default=True)

    # Stats
    times_matched = Column(Integer, default=0)
    last_matched_at = Column(DateTime)

    # Audit
    created_by = Column(UniversalUUID(), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    history = relationship("ReconciliationHistory", back_populates="rule")

    __table_args__ = (
        Index("idx_reconrule_tenant", "tenant_id"),
        Index("idx_reconrule_tenant_active", "tenant_id", "is_active"),
    )


class ReconciliationHistory(Base):
    """Historique des rapprochements."""
    __tablename__ = "accounting_reconciliation_history"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Éléments rapprochés
    transaction_id = Column(UniversalUUID(), ForeignKey("accounting_synced_transactions.id"))
    document_id = Column(UniversalUUID(), ForeignKey("accounting_documents.id"))
    entry_line_id = Column(UniversalUUID(), ForeignKey("journal_entry_lines.id"))

    # Type de rapprochement
    reconciliation_type = Column(String(50), nullable=False)  # auto, manual, rule_based
    rule_id = Column(UniversalUUID(), ForeignKey("accounting_reconciliation_rules.id"))

    # Confiance
    confidence_score = Column(Numeric(5, 2))
    match_details = Column(JSON)

    # Montants
    transaction_amount = Column(Numeric(15, 2))
    document_amount = Column(Numeric(15, 2))
    difference = Column(Numeric(15, 2))

    # Validation
    validated_by = Column(UniversalUUID())
    validated_at = Column(DateTime)

    # Si annulé
    is_cancelled = Column(Boolean, default=False)
    cancelled_by = Column(UniversalUUID())
    cancelled_at = Column(DateTime)
    cancellation_reason = Column(Text)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relations
    transaction = relationship("SyncedTransaction", back_populates="reconciliation_history")
    document = relationship("AccountingDocument", back_populates="reconciliation_history")
    rule = relationship("ReconciliationRule", back_populates="history")

    __table_args__ = (
        Index("idx_reconhist_tenant", "tenant_id"),
        Index("idx_reconhist_transaction", "transaction_id"),
        Index("idx_reconhist_document", "document_id"),
    )


# ============================================================================
# MODÈLES ALERTES
# ============================================================================

class AccountingAlert(Base):
    """Alerte comptable intelligente."""
    __tablename__ = "accounting_alerts"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Type et sévérité
    alert_type = Column(Enum(AlertType), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False, default=AlertSeverity.WARNING)

    # Sujet
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Entité concernée
    entity_type = Column(String(50))
    entity_id = Column(UniversalUUID())

    # Lien avec document (optionnel)
    document_id = Column(UniversalUUID(), ForeignKey("accounting_documents.id"))

    # Destinataires
    target_roles = Column(JSON, default=lambda: ["EXPERT_COMPTABLE"])
    target_users = Column(JSON, default=list)

    # Statut
    is_read = Column(Boolean, default=False)
    read_by = Column(UniversalUUID())
    read_at = Column(DateTime)

    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(UniversalUUID())
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)

    # Auto-expiration
    expires_at = Column(DateTime)

    # Metadonnees
    extra_data = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relations
    document = relationship("AccountingDocument", back_populates="alerts")

    __table_args__ = (
        Index("idx_alert_tenant", "tenant_id"),
        Index("idx_alert_tenant_type", "tenant_id", "alert_type"),
        Index("idx_alert_tenant_unresolved", "tenant_id", "is_resolved"),
        Index("idx_alert_entity", "entity_type", "entity_id"),
    )


# ============================================================================
# MODÈLES PLAN COMPTABLE UNIVERSEL
# ============================================================================

class UniversalChartAccount(Base):
    """Plan comptable universel Azalscore."""
    __tablename__ = "accounting_universal_chart"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)

    # Code universel
    universal_code = Column(String(20), nullable=False, unique=True)
    name_en = Column(String(255), nullable=False)
    name_fr = Column(String(255), nullable=False)

    # Type
    account_type = Column(String(20), nullable=False)

    # Hiérarchie
    parent_code = Column(String(20), ForeignKey("accounting_universal_chart.universal_code"))
    level = Column(Integer, nullable=False, default=1)

    # Mappings pays
    country_mappings = Column(JSON, default=dict)

    # Règles IA
    ai_keywords = Column(JSON, default=list)
    ai_patterns = Column(JSON, default=list)

    # Métadonnées
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    children = relationship("UniversalChartAccount", backref="parent", remote_side=[universal_code])
    mappings = relationship("ChartMapping", back_populates="universal_account")

    __table_args__ = (
        Index("idx_univchart_code", "universal_code"),
        Index("idx_univchart_parent", "parent_code"),
        Index("idx_univchart_type", "account_type"),
    )


class ChartMapping(Base):
    """Mapping plan comptable universel vers local."""
    __tablename__ = "accounting_chart_mappings"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Code universel source
    universal_code = Column(String(20), ForeignKey("accounting_universal_chart.universal_code"), nullable=False)

    # Compte local
    local_account_id = Column(UniversalUUID(), ForeignKey("accounts.id"))
    local_account_code = Column(String(20))

    # Priorité
    priority = Column(Integer, default=0)

    # Conditions d'application
    conditions = Column(JSON, default=dict)

    # Activation
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    universal_account = relationship("UniversalChartAccount", back_populates="mappings")

    __table_args__ = (
        Index("idx_chartmap_tenant", "tenant_id"),
        UniqueConstraint("tenant_id", "universal_code", name="uq_chartmap_universal"),
    )


# ============================================================================
# MODÈLES CONFIGURATION FISCALE
# ============================================================================

class TaxConfiguration(Base):
    """Configuration fiscale par pays."""
    __tablename__ = "accounting_tax_configurations"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), index=True)         # NULL = configuration globale

    # Pays
    country_code = Column(String(2), nullable=False)
    country_name = Column(String(100), nullable=False)

    # Type de taxe
    tax_type = Column(String(50), nullable=False)      # VAT, GST, SALES_TAX

    # Taux applicables
    tax_rates = Column(JSON, nullable=False)

    # Règles spécifiques
    special_rules = Column(JSON, default=dict)

    # Validation
    is_active = Column(Boolean, default=True)
    valid_from = Column(Date)
    valid_to = Column(Date)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_taxconfig_tenant", "tenant_id"),
        Index("idx_taxconfig_country", "country_code"),
    )


# ============================================================================
# MODÈLES PRÉFÉRENCES UTILISATEUR
# ============================================================================

class UserPreferences(Base):
    """Préférences utilisateur par vue."""
    __tablename__ = "accounting_user_preferences"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False)

    # Type de vue
    view_type = Column(Enum(ViewType), nullable=False)

    # Préférences dashboard
    dashboard_widgets = Column(JSON, default=list)
    default_period = Column(String(20), default="MONTH")

    # Préférences liste
    list_columns = Column(JSON, default=list)
    default_sort = Column(JSON)
    default_filters = Column(JSON, default=dict)

    # Alertes
    alert_preferences = Column(JSON, default=dict)

    # Métadonnées
    last_accessed_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "view_type", name="uq_userprefs_view"),
    )


# ============================================================================
# MODÈLES EMAIL
# ============================================================================

class EmailInbox(Base):
    """Boîte email dédiée par tenant."""
    __tablename__ = "accounting_email_inboxes"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Adresse email
    email_address = Column(String(255), nullable=False, unique=True)
    email_type = Column(Enum(EmailInboxType), nullable=False)

    # Configuration
    is_active = Column(Boolean, default=True)
    auto_process = Column(Boolean, default=True)

    # Provider email
    provider = Column(String(50))
    provider_config = Column(JSON)

    # Stats
    emails_received = Column(Integer, default=0)
    emails_processed = Column(Integer, default=0)
    last_email_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    processing_logs = relationship("EmailProcessingLog", back_populates="inbox", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_emailinbox_tenant", "tenant_id"),
    )


class EmailProcessingLog(Base):
    """Log de traitement email."""
    __tablename__ = "accounting_email_processing_logs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    inbox_id = Column(UniversalUUID(), ForeignKey("accounting_email_inboxes.id"), nullable=False)

    # Email
    email_id = Column(String(255), nullable=False)
    email_from = Column(String(255))
    email_subject = Column(String(500))
    email_received_at = Column(DateTime)

    # Traitement
    status = Column(String(50), nullable=False)

    # Pièces jointes
    attachments_count = Column(Integer, default=0)
    attachments_processed = Column(Integer, default=0)

    # Documents créés
    documents_created = Column(JSON, default=list)

    # Erreur
    error_message = Column(Text)

    # Timestamps
    processed_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relations
    inbox = relationship("EmailInbox", back_populates="processing_logs")

    __table_args__ = (
        Index("idx_emaillog_tenant", "tenant_id"),
        Index("idx_emaillog_inbox", "inbox_id"),
        Index("idx_emaillog_status", "tenant_id", "status"),
    )


# ============================================================================
# MODÈLES DASHBOARD
# ============================================================================

class DashboardMetrics(Base):
    """Métriques dashboard temps réel."""
    __tablename__ = "accounting_dashboard_metrics"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Période
    metric_date = Column(Date, nullable=False)
    metric_type = Column(String(50), nullable=False)   # DAILY, WEEKLY, MONTHLY

    # Trésorerie
    cash_balance = Column(Numeric(15, 2))
    cash_balance_updated_at = Column(DateTime)

    # Factures à payer
    invoices_to_pay_count = Column(Integer, default=0)
    invoices_to_pay_amount = Column(Numeric(15, 2), default=0)
    invoices_overdue_count = Column(Integer, default=0)
    invoices_overdue_amount = Column(Numeric(15, 2), default=0)

    # Factures à encaisser
    invoices_to_collect_count = Column(Integer, default=0)
    invoices_to_collect_amount = Column(Numeric(15, 2), default=0)
    invoices_overdue_collect_count = Column(Integer, default=0)
    invoices_overdue_collect_amount = Column(Numeric(15, 2), default=0)

    # Résultat
    revenue_period = Column(Numeric(15, 2), default=0)
    expenses_period = Column(Numeric(15, 2), default=0)
    result_period = Column(Numeric(15, 2), default=0)

    # Documents
    documents_pending_count = Column(Integer, default=0)
    documents_error_count = Column(Integer, default=0)

    # Rapprochement
    transactions_unreconciled = Column(Integer, default=0)

    # Fraîcheur données
    data_freshness_score = Column(Numeric(5, 2))
    last_bank_sync = Column(DateTime)

    # Timestamps
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_dashmetrics_tenant", "tenant_id"),
        Index("idx_dashmetrics_date", "tenant_id", "metric_date"),
        UniqueConstraint("tenant_id", "metric_date", "metric_type", name="uq_dashmetrics_date_type"),
    )
