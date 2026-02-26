"""
AZALS - Modèles Facturation Électronique France 2026
=====================================================

Modèles SQLAlchemy pour la gestion multi-tenant de la facturation électronique.
Chaque tenant peut configurer son/ses PDP et gérer ses factures électroniques.
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.types import JSON, UniversalUUID
from app.db import Base


# =============================================================================
# ENUMS
# =============================================================================

class PDPProviderType(str, enum.Enum):
    """Types de providers PDP."""
    CHORUS_PRO = "chorus_pro"
    PPF = "ppf"
    YOOZ = "yooz"
    DOCAPOSTE = "docaposte"
    SAGE = "sage"
    CEGID = "cegid"
    GENERIX = "generix"
    EDICOM = "edicom"
    BASWARE = "basware"
    CUSTOM = "custom"


class EInvoiceStatusDB(str, enum.Enum):
    """Statuts de facture électronique."""
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    RECEIVED = "RECEIVED"
    ACCEPTED = "ACCEPTED"
    REFUSED = "REFUSED"
    PAID = "PAID"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"


class EInvoiceDirection(str, enum.Enum):
    """Direction de la facture."""
    OUTBOUND = "OUTBOUND"  # Émise
    INBOUND = "INBOUND"    # Reçue


class EInvoiceFormatDB(str, enum.Enum):
    """Formats supportés."""
    FACTURX_MINIMUM = "FACTURX_MINIMUM"
    FACTURX_BASIC = "FACTURX_BASIC"
    FACTURX_EN16931 = "FACTURX_EN16931"
    FACTURX_EXTENDED = "FACTURX_EXTENDED"
    UBL_21 = "UBL_21"
    CII_D16B = "CII_D16B"


class CompanySizeType(str, enum.Enum):
    """Taille d'entreprise pour obligations."""
    GE = "GE"        # Grande Entreprise
    ETI = "ETI"      # ETI
    PME = "PME"      # PME
    MICRO = "MICRO"  # Micro-entreprise


# =============================================================================
# CONFIGURATION PDP PAR TENANT
# =============================================================================

class TenantPDPConfig(Base):
    """Configuration PDP pour un tenant."""
    __tablename__ = "einvoice_pdp_configs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Provider - utiliser values_callable pour utiliser .value au lieu de .name
    provider = Column(
        Enum(PDPProviderType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    name = Column(String(100), nullable=False)  # Nom pour identification
    description = Column(Text)

    # Credentials (chiffrés en base)
    api_url = Column(String(500), nullable=False)
    token_url = Column(String(500))
    client_id = Column(String(255))  # Chiffré
    client_secret = Column(String(500))  # Chiffré
    scope = Column(String(255))

    # Certificats (chemins ou références)
    certificate_ref = Column(String(255))  # Référence au certificat (vault/secret manager)
    private_key_ref = Column(String(255))

    # Identifiants entreprise
    siret = Column(String(14))
    siren = Column(String(9))
    tva_number = Column(String(20))
    company_size = Column(Enum(CompanySizeType), default=CompanySizeType.PME)

    # Configuration
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)  # Provider par défaut pour ce tenant
    test_mode = Column(Boolean, default=True)
    timeout_seconds = Column(Integer, default=30)
    retry_count = Column(Integer, default=3)

    # Webhook pour notifications
    webhook_url = Column(String(500))
    webhook_secret = Column(String(255))

    # Options spécifiques au provider (JSON)
    provider_options = Column(JSON, default=dict)

    # Endpoints personnalisés (pour PDP génériques)
    custom_endpoints = Column(JSON, default=dict)

    # Formats préférés
    preferred_format = Column(Enum(EInvoiceFormatDB), default=EInvoiceFormatDB.FACTURX_EN16931)
    generate_pdf = Column(Boolean, default=True)

    # Métadonnées
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_sync_at = Column(DateTime)  # Dernière synchronisation avec le PDP

    # Relations
    einvoices = relationship("EInvoiceRecord", back_populates="pdp_config")

    __table_args__ = (
        Index("ix_pdp_configs_tenant", "tenant_id"),
        Index("ix_pdp_configs_tenant_provider", "tenant_id", "provider"),
        Index("ix_pdp_configs_tenant_default", "tenant_id", "is_default"),
        UniqueConstraint("tenant_id", "name", name="uq_pdp_config_tenant_name"),
    )


# =============================================================================
# FACTURES ÉLECTRONIQUES
# =============================================================================

class EInvoiceRecord(Base):
    """Enregistrement d'une facture électronique."""
    __tablename__ = "einvoice_records"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    pdp_config_id = Column(UniversalUUID(), ForeignKey("einvoice_pdp_configs.id"))

    # Direction
    direction = Column(Enum(EInvoiceDirection), nullable=False)

    # Identification
    invoice_number = Column(String(100), nullable=False)
    invoice_type = Column(String(10), default="380")  # Code type facture
    format = Column(Enum(EInvoiceFormatDB), default=EInvoiceFormatDB.FACTURX_EN16931)

    # Références PDP/PPF
    transaction_id = Column(String(100))  # Notre référence interne
    ppf_id = Column(String(100))  # Référence PPF
    pdp_id = Column(String(100))  # Référence PDP

    # Lien avec facture AZALS
    source_invoice_id = Column(UniversalUUID())  # ID facture module commercial
    source_type = Column(String(50))  # INVOICE, CREDIT_NOTE, etc.

    # Dates
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date)
    submission_date = Column(DateTime)  # Date d'envoi au PDP
    reception_date = Column(DateTime)   # Date de réception (si INBOUND)

    # Parties
    seller_siret = Column(String(14))
    seller_name = Column(String(255))
    seller_tva = Column(String(20))
    buyer_siret = Column(String(14))
    buyer_name = Column(String(255))
    buyer_tva = Column(String(20))
    buyer_routing_id = Column(String(100))  # ID routage destinataire

    # Montants
    currency = Column(String(3), default="EUR")
    total_ht = Column(Numeric(15, 2), default=0)
    total_tva = Column(Numeric(15, 2), default=0)
    total_ttc = Column(Numeric(15, 2), default=0)

    # Détail TVA (JSON: {taux: montant})
    vat_breakdown = Column(JSON, default=dict)

    # Statut
    status = Column(Enum(EInvoiceStatusDB), default=EInvoiceStatusDB.DRAFT)
    lifecycle_status = Column(String(50))  # Statut cycle Y PPF

    # Contenu
    xml_content = Column(Text)  # XML Factur-X
    xml_hash = Column(String(64))  # SHA-256 du XML
    pdf_storage_ref = Column(String(500))  # Référence stockage PDF

    # Validation
    validation_errors = Column(JSON, default=list)
    validation_warnings = Column(JSON, default=list)
    is_valid = Column(Boolean, default=False)

    # Erreurs
    last_error = Column(Text)
    error_count = Column(Integer, default=0)

    # Métadonnées
    extra_data = Column(JSON, default=dict)  # renamed from metadata (reserved)
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    pdp_config = relationship("TenantPDPConfig", back_populates="einvoices")
    lifecycle_events = relationship("EInvoiceLifecycleEvent", back_populates="einvoice", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_einvoice_tenant", "tenant_id"),
        Index("ix_einvoice_tenant_number", "tenant_id", "invoice_number"),
        Index("ix_einvoice_tenant_status", "tenant_id", "status"),
        Index("ix_einvoice_tenant_direction", "tenant_id", "direction"),
        Index("ix_einvoice_tenant_date", "tenant_id", "issue_date"),
        Index("ix_einvoice_ppf_id", "ppf_id"),
        Index("ix_einvoice_pdp_id", "pdp_id"),
        Index("ix_einvoice_source", "source_type", "source_invoice_id"),
    )


# =============================================================================
# CYCLE DE VIE
# =============================================================================

class EInvoiceLifecycleEvent(Base):
    """Événement du cycle de vie d'une facture."""
    __tablename__ = "einvoice_lifecycle_events"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    einvoice_id = Column(UniversalUUID(), ForeignKey("einvoice_records.id", ondelete="CASCADE"), nullable=False)

    # Événement
    status = Column(String(50), nullable=False)  # DEPOSITED, TRANSMITTED, RECEIVED, etc.
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    actor = Column(String(100))  # Qui a déclenché l'événement
    message = Column(Text)

    # Détails (JSON)
    details = Column(JSON, default=dict)

    # Source
    source = Column(String(50))  # PPF, PDP, WEBHOOK, MANUAL

    # Relation
    einvoice = relationship("EInvoiceRecord", back_populates="lifecycle_events")

    __table_args__ = (
        Index("ix_lifecycle_tenant", "tenant_id"),
        Index("ix_lifecycle_einvoice", "einvoice_id"),
        Index("ix_lifecycle_timestamp", "timestamp"),
    )


# =============================================================================
# E-REPORTING B2C
# =============================================================================

class EReportingSubmission(Base):
    """Soumission e-reporting B2C."""
    __tablename__ = "ereporting_submissions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    pdp_config_id = Column(UniversalUUID(), ForeignKey("einvoice_pdp_configs.id"))

    # Période
    period = Column(String(7), nullable=False)  # YYYY-MM
    reporting_type = Column(String(50), nullable=False)  # B2C_DOMESTIC, B2C_EXPORT, etc.

    # Identifiants
    submission_id = Column(String(100))
    ppf_reference = Column(String(100))

    # Totaux
    total_ht = Column(Numeric(15, 2), default=0)
    total_tva = Column(Numeric(15, 2), default=0)
    total_ttc = Column(Numeric(15, 2), default=0)
    transaction_count = Column(Integer, default=0)

    # Ventilation TVA
    vat_breakdown = Column(JSON, default=dict)

    # Statut
    status = Column(String(50), default="DRAFT")  # DRAFT, SUBMITTED, ACCEPTED, REJECTED
    submitted_at = Column(DateTime)
    response_at = Column(DateTime)

    # Erreurs
    errors = Column(JSON, default=list)

    # Métadonnées
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_ereporting_tenant", "tenant_id"),
        Index("ix_ereporting_tenant_period", "tenant_id", "period"),
        UniqueConstraint("tenant_id", "period", "reporting_type", name="uq_ereporting_period"),
    )


# =============================================================================
# STATISTIQUES TENANT
# =============================================================================

class EInvoiceStats(Base):
    """Statistiques e-invoicing par tenant."""
    __tablename__ = "einvoice_stats"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Période
    period = Column(String(7), nullable=False)  # YYYY-MM

    # Compteurs émission
    outbound_total = Column(Integer, default=0)
    outbound_sent = Column(Integer, default=0)
    outbound_delivered = Column(Integer, default=0)
    outbound_accepted = Column(Integer, default=0)
    outbound_refused = Column(Integer, default=0)
    outbound_errors = Column(Integer, default=0)

    # Compteurs réception
    inbound_total = Column(Integer, default=0)
    inbound_received = Column(Integer, default=0)
    inbound_accepted = Column(Integer, default=0)
    inbound_refused = Column(Integer, default=0)

    # Montants
    outbound_amount_ttc = Column(Numeric(18, 2), default=0)
    inbound_amount_ttc = Column(Numeric(18, 2), default=0)

    # e-reporting
    ereporting_submitted = Column(Integer, default=0)
    ereporting_amount = Column(Numeric(18, 2), default=0)

    # Mise à jour
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_einvoice_stats_tenant", "tenant_id"),
        UniqueConstraint("tenant_id", "period", name="uq_einvoice_stats_period"),
    )
