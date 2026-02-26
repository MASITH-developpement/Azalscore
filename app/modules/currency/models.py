"""
AZALS MODULE - CURRENCY: Models SQLAlchemy
==========================================

Modeles pour la gestion multi-devises complete.
ISO 4217 compliant avec taux BCE/Forex.

INSPIRATION CONCURRENTIELLE:
- Sage: Gestion multi-devises avec taux manuels
- Odoo: Taux automatiques BCE, historique complet
- Microsoft Dynamics 365: Triangulation, devise pivot
- Pennylane: Conversion temps reel
- Axonaut: Multi-devises par document

REGLES AZALSCORE:
- tenant_id obligatoire sur tous les modeles
- Soft delete avec is_deleted, deleted_at, deleted_by
- Audit complet avec created_by, updated_by
- Versioning avec column 'version'
"""

import uuid
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, Numeric,
    ForeignKey, Index, Date, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship

from app.core.types import UniversalUUID, JSON, JSONB
from app.db import Base


# ============================================================================
# ENUMERATIONS
# ============================================================================

class RateSource(str, Enum):
    """Sources des taux de change."""
    ECB = "ecb"                      # Banque Centrale Europeenne
    FOREX = "forex"                   # Marche Forex
    OPENEXCHANGE = "openexchange"     # Open Exchange Rates API
    FIXER = "fixer"                   # Fixer.io API
    CURRENCYLAYER = "currencylayer"   # CurrencyLayer API
    XE = "xe"                         # XE.com
    MANUAL = "manual"                 # Saisie manuelle


class RateType(str, Enum):
    """Types de taux de change."""
    SPOT = "spot"           # Taux au comptant
    AVERAGE = "average"     # Taux moyen
    CLOSING = "closing"     # Taux de cloture
    OPENING = "opening"     # Taux d'ouverture
    HIGH = "high"           # Plus haut du jour
    LOW = "low"             # Plus bas du jour
    CUSTOM = "custom"       # Taux personnalise


class ConversionMethod(str, Enum):
    """Methodes de conversion."""
    DIRECT = "direct"               # Conversion directe
    TRIANGULATION = "triangulation" # Via devise pivot
    CROSS_RATE = "cross_rate"       # Taux croise
    AVERAGE = "average"             # Moyenne des taux


class GainLossType(str, Enum):
    """Types de gains/pertes de change."""
    REALIZED = "realized"       # Realise (transaction effectuee)
    UNREALIZED = "unrealized"   # Latent (non encore realise)


class CurrencyStatus(str, Enum):
    """Statut d'une devise."""
    ACTIVE = "active"       # Active et utilisable
    INACTIVE = "inactive"   # Desactivee
    DEPRECATED = "deprecated"  # Obsolete (ex: ancien franc)


class RevaluationStatus(str, Enum):
    """Statut d'une reevaluation."""
    DRAFT = "draft"           # Brouillon
    POSTED = "posted"         # Comptabilisee
    CANCELLED = "cancelled"   # Annulee


# ============================================================================
# MODELES
# ============================================================================

class Currency(Base):
    """
    Devise ISO 4217.

    Represente une devise avec ses proprietes (symbole, decimales, etc.)
    et son statut d'utilisation par le tenant.
    """
    __tablename__ = "currencies"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification ISO 4217
    code = Column(String(3), nullable=False)      # EUR, USD, GBP
    numeric_code = Column(String(3))               # 978, 840, 826
    name = Column(String(100), nullable=False)     # Euro, Dollar americain
    name_en = Column(String(100))                  # English name
    symbol = Column(String(10), nullable=False)    # €, $, £
    symbol_native = Column(String(10))             # Symbole natif

    # Precision
    decimals = Column(Integer, default=2)          # Nombre de decimales
    rounding = Column(Numeric(10, 6), default=Decimal("0.01"))  # Arrondi minimal

    # Format d'affichage
    format_pattern = Column(String(50))            # Ex: "#,##0.00 €"
    decimal_separator = Column(String(1), default=",")
    thousands_separator = Column(String(1), default=" ")
    symbol_position = Column(String(10), default="after")  # before, after

    # Classification
    country_codes = Column(JSON, default=list)     # Liste des pays utilisant cette devise
    is_major = Column(Boolean, default=False)      # Devise majeure (EUR, USD, etc.)
    is_crypto = Column(Boolean, default=False)     # Crypto-monnaie

    # Configuration tenant
    is_enabled = Column(Boolean, default=False)    # Active pour ce tenant
    is_default = Column(Boolean, default=False)    # Devise par defaut
    is_reporting = Column(Boolean, default=False)  # Devise de reporting/consolidation
    is_functional = Column(Boolean, default=False) # Devise fonctionnelle

    # Statut
    status = Column(String(20), default=CurrencyStatus.ACTIVE.value)

    # Comptes comptables associes
    exchange_gain_account = Column(String(20))     # Compte gains de change
    exchange_loss_account = Column(String(20))     # Compte pertes de change
    rounding_account = Column(String(20))          # Compte ecarts d'arrondi
    revaluation_account = Column(String(20))       # Compte reevaluation

    # Notes
    notes = Column(Text)

    # Audit
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID())

    # Relations
    rates_as_base = relationship("ExchangeRate", foreign_keys="ExchangeRate.base_currency_id",
                                 back_populates="base_currency_rel", lazy="dynamic")
    rates_as_quote = relationship("ExchangeRate", foreign_keys="ExchangeRate.quote_currency_id",
                                  back_populates="quote_currency_rel", lazy="dynamic")

    __table_args__ = (
        Index('ix_currencies_tenant_code', 'tenant_id', 'code', unique=True),
        Index('ix_currencies_tenant_enabled', 'tenant_id', 'is_enabled'),
        Index('ix_currencies_tenant_default', 'tenant_id', 'is_default'),
        Index('ix_currencies_status', 'status'),
        CheckConstraint('decimals >= 0 AND decimals <= 8', name='check_decimals_range'),
    )


class ExchangeRate(Base):
    """
    Taux de change entre deux devises.

    Stocke les taux avec leur source et type,
    permettant un historique complet.
    """
    __tablename__ = "exchange_rates"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Paire de devises
    base_currency_id = Column(UniversalUUID(), ForeignKey("currencies.id"), nullable=False)
    quote_currency_id = Column(UniversalUUID(), ForeignKey("currencies.id"), nullable=False)
    base_currency_code = Column(String(3), nullable=False)   # Denormalise pour performance
    quote_currency_code = Column(String(3), nullable=False)  # Denormalise pour performance

    # Taux
    rate = Column(Numeric(24, 12), nullable=False)     # Taux: 1 base = X quote
    inverse_rate = Column(Numeric(24, 12))             # Taux inverse
    bid_rate = Column(Numeric(24, 12))                 # Taux achat
    ask_rate = Column(Numeric(24, 12))                 # Taux vente
    spread = Column(Numeric(10, 6))                    # Spread bid/ask

    # Type et source
    rate_type = Column(String(20), default=RateType.SPOT.value, nullable=False)
    source = Column(String(30), default=RateSource.MANUAL.value, nullable=False)
    source_reference = Column(String(100))             # Reference API source

    # Date du taux
    rate_date = Column(Date, nullable=False, index=True)
    effective_from = Column(DateTime)                   # Debut validite
    effective_to = Column(DateTime)                     # Fin validite

    # Metadonnees source
    fetched_at = Column(DateTime)                       # Date recuperation
    api_response = Column(JSONB)                        # Reponse API brute

    # Flags
    is_manual = Column(Boolean, default=False)          # Saisie manuelle
    is_official = Column(Boolean, default=False)        # Taux officiel (BCE)
    is_interpolated = Column(Boolean, default=False)    # Taux interpole
    is_locked = Column(Boolean, default=False)          # Verrouille (non modifiable)

    # Audit
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID())

    # Relations
    base_currency_rel = relationship("Currency", foreign_keys=[base_currency_id],
                                     back_populates="rates_as_base")
    quote_currency_rel = relationship("Currency", foreign_keys=[quote_currency_id],
                                      back_populates="rates_as_quote")

    __table_args__ = (
        Index('ix_exchange_rates_tenant_pair_date', 'tenant_id', 'base_currency_code',
              'quote_currency_code', 'rate_date', unique=True),
        Index('ix_exchange_rates_tenant_date', 'tenant_id', 'rate_date'),
        Index('ix_exchange_rates_source', 'source'),
        Index('ix_exchange_rates_type', 'rate_type'),
        CheckConstraint('rate > 0', name='check_rate_positive'),
        CheckConstraint('base_currency_id != quote_currency_id', name='check_different_currencies'),
    )


class CurrencyConfig(Base):
    """
    Configuration multi-devises du tenant.

    Definit la devise par defaut, de reporting, les sources de taux,
    et les parametres de conversion.
    """
    __tablename__ = "currency_configs"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, unique=True, index=True)

    # Devises principales
    default_currency_code = Column(String(3), default="EUR", nullable=False)
    reporting_currency_code = Column(String(3), default="EUR", nullable=False)
    functional_currency_code = Column(String(3), default="EUR")

    # Source des taux
    primary_rate_source = Column(String(30), default=RateSource.ECB.value)
    fallback_rate_source = Column(String(30), default=RateSource.OPENEXCHANGE.value)

    # Cles API
    api_keys = Column(JSONB, default=dict)  # Chiffre en production

    # Mise a jour automatique
    auto_update_rates = Column(Boolean, default=True)
    update_frequency_hours = Column(Integer, default=24)
    update_time = Column(String(5), default="06:00")  # Heure de MAJ quotidienne
    last_rate_update = Column(DateTime)
    next_rate_update = Column(DateTime)

    # Methode de conversion
    conversion_method = Column(String(30), default=ConversionMethod.DIRECT.value)
    pivot_currency_code = Column(String(3), default="EUR")
    allow_triangulation = Column(Boolean, default=True)

    # Arrondi
    rounding_method = Column(String(20), default="ROUND_HALF_UP")
    rounding_precision = Column(Integer, default=2)

    # Gains/pertes de change
    track_exchange_gains = Column(Boolean, default=True)
    exchange_gain_account = Column(String(20), default="766000")  # PCG
    exchange_loss_account = Column(String(20), default="666000")  # PCG
    unrealized_gain_account = Column(String(20), default="476000")
    unrealized_loss_account = Column(String(20), default="476000")

    # Reevaluation
    revaluation_method = Column(String(30), default="closing_rate")
    revaluation_frequency = Column(String(20), default="monthly")
    auto_revaluation = Column(Boolean, default=False)
    last_revaluation_date = Column(Date)

    # Options avancees
    allow_manual_rates = Column(Boolean, default=True)
    require_rate_approval = Column(Boolean, default=False)
    rate_tolerance_percent = Column(Numeric(5, 2), default=Decimal("5.00"))  # Alerte si ecart > 5%
    historical_rate_retention_days = Column(Integer, default=365 * 5)  # 5 ans

    # Notifications
    notify_rate_changes = Column(Boolean, default=True)
    notification_threshold_percent = Column(Numeric(5, 2), default=Decimal("2.00"))
    notification_emails = Column(JSON, default=list)

    # Audit
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID())

    __table_args__ = (
        CheckConstraint('update_frequency_hours >= 1 AND update_frequency_hours <= 168',
                        name='check_update_frequency_range'),
        CheckConstraint('rate_tolerance_percent >= 0 AND rate_tolerance_percent <= 100',
                        name='check_tolerance_range'),
    )


class ExchangeGainLoss(Base):
    """
    Gain ou perte de change sur une operation.

    Trace les ecarts de change realises et latents
    pour chaque document (facture, paiement, etc.).
    """
    __tablename__ = "exchange_gains_losses"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Document source
    document_type = Column(String(50), nullable=False)  # invoice, payment, etc.
    document_id = Column(UniversalUUID(), nullable=False, index=True)
    document_reference = Column(String(100))

    # Type de gain/perte
    gain_loss_type = Column(String(20), nullable=False)  # realized, unrealized

    # Montants originaux
    original_amount = Column(Numeric(18, 4), nullable=False)
    original_currency_code = Column(String(3), nullable=False)

    # Taux
    booking_rate = Column(Numeric(24, 12), nullable=False)    # Taux a la comptabilisation
    settlement_rate = Column(Numeric(24, 12))                 # Taux au reglement
    revaluation_rate = Column(Numeric(24, 12))                # Taux reevaluation

    # Montants en devise de reporting
    booking_amount = Column(Numeric(18, 4), nullable=False)   # Montant initial converti
    settlement_amount = Column(Numeric(18, 4))                # Montant final converti
    reporting_currency_code = Column(String(3), nullable=False)

    # Gain/Perte
    gain_loss_amount = Column(Numeric(18, 4), nullable=False)  # Positif = gain, Negatif = perte
    is_gain = Column(Boolean)                                   # True = gain, False = perte

    # Dates
    booking_date = Column(Date, nullable=False)
    settlement_date = Column(Date)
    revaluation_date = Column(Date)

    # Comptabilisation
    is_posted = Column(Boolean, default=False)
    journal_entry_id = Column(UniversalUUID())
    posting_date = Column(Date)

    # Reference reevaluation
    revaluation_id = Column(UniversalUUID(), ForeignKey("currency_revaluations.id"))

    # Notes
    notes = Column(Text)

    # Audit
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID())

    # Relations
    revaluation = relationship("CurrencyRevaluation", back_populates="gain_loss_entries")

    __table_args__ = (
        Index('ix_exchange_gains_losses_tenant_doc', 'tenant_id', 'document_type', 'document_id'),
        Index('ix_exchange_gains_losses_type', 'gain_loss_type'),
        Index('ix_exchange_gains_losses_dates', 'booking_date', 'settlement_date'),
        Index('ix_exchange_gains_losses_posted', 'is_posted'),
    )


class CurrencyRevaluation(Base):
    """
    Reevaluation periodique des postes en devises.

    Recalcule les gains/pertes latents sur les postes ouverts
    (creances, dettes) au taux de cloture.
    """
    __tablename__ = "currency_revaluations"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)

    # Periode
    fiscal_year_id = Column(UniversalUUID())
    period = Column(String(7), nullable=False)  # YYYY-MM
    revaluation_date = Column(Date, nullable=False)

    # Devises traitees
    currencies_revalued = Column(JSON, default=list)
    base_currency_code = Column(String(3), nullable=False)

    # Statut
    status = Column(String(20), default=RevaluationStatus.DRAFT.value)

    # Totaux
    total_gain = Column(Numeric(18, 4), default=Decimal("0"))
    total_loss = Column(Numeric(18, 4), default=Decimal("0"))
    net_amount = Column(Numeric(18, 4), default=Decimal("0"))
    document_count = Column(Integer, default=0)

    # Comptabilisation
    journal_entry_id = Column(UniversalUUID())
    posted_at = Column(DateTime)
    posted_by = Column(UniversalUUID())

    # Annulation
    reversed_by_id = Column(UniversalUUID())  # Reference a la reevaluation d'annulation
    reversal_of_id = Column(UniversalUUID())  # Si c'est une annulation

    # Notes
    notes = Column(Text)

    # Audit
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID())

    # Relations
    gain_loss_entries = relationship("ExchangeGainLoss", back_populates="revaluation")

    __table_args__ = (
        Index('ix_revaluations_tenant_code', 'tenant_id', 'code', unique=True),
        Index('ix_revaluations_tenant_period', 'tenant_id', 'period'),
        Index('ix_revaluations_status', 'status'),
        Index('ix_revaluations_date', 'revaluation_date'),
    )


class CurrencyConversionLog(Base):
    """
    Journal des conversions de devises.

    Trace toutes les conversions effectuees pour audit
    et analyse des couts de change.
    """
    __tablename__ = "currency_conversion_logs"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Montants
    original_amount = Column(Numeric(18, 4), nullable=False)
    original_currency_code = Column(String(3), nullable=False)
    converted_amount = Column(Numeric(18, 4), nullable=False)
    target_currency_code = Column(String(3), nullable=False)

    # Taux utilise
    exchange_rate = Column(Numeric(24, 12), nullable=False)
    rate_date = Column(Date, nullable=False)
    rate_source = Column(String(30), nullable=False)
    rate_type = Column(String(20), nullable=False)

    # Methode
    conversion_method = Column(String(30), nullable=False)
    pivot_currency_code = Column(String(3))  # Si triangulation
    intermediate_rate = Column(Numeric(24, 12))  # Taux intermediaire

    # Arrondi
    rounding_difference = Column(Numeric(18, 6), default=Decimal("0"))

    # Document source
    document_type = Column(String(50))
    document_id = Column(UniversalUUID())
    line_id = Column(UniversalUUID())

    # Module appelant
    calling_module = Column(String(50))
    calling_function = Column(String(100))

    # Horodatage
    converted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(UniversalUUID())

    __table_args__ = (
        Index('ix_conversion_logs_tenant_date', 'tenant_id', 'converted_at'),
        Index('ix_conversion_logs_currencies', 'original_currency_code', 'target_currency_code'),
        Index('ix_conversion_logs_document', 'document_type', 'document_id'),
    )


class RateAlert(Base):
    """
    Alertes sur les variations de taux.

    Notifie les utilisateurs lors de variations importantes
    ou d'anomalies detectees.
    """
    __tablename__ = "currency_rate_alerts"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Paire de devises
    base_currency_code = Column(String(3), nullable=False)
    quote_currency_code = Column(String(3), nullable=False)

    # Type d'alerte
    alert_type = Column(String(30), nullable=False)  # threshold, anomaly, manual_override, api_error
    severity = Column(String(20), default="info")    # info, warning, critical

    # Details
    old_rate = Column(Numeric(24, 12))
    new_rate = Column(Numeric(24, 12))
    variation_percent = Column(Numeric(10, 4))
    threshold_percent = Column(Numeric(10, 4))

    # Message
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Statut
    is_read = Column(Boolean, default=False)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(UniversalUUID())
    acknowledged_at = Column(DateTime)

    # Notifications envoyees
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime)
    notification_recipients = Column(JSON, default=list)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('ix_rate_alerts_tenant_unread', 'tenant_id', 'is_read'),
        Index('ix_rate_alerts_severity', 'severity'),
        Index('ix_rate_alerts_type', 'alert_type'),
    )
