"""
AZALS MODULE - Auto-Enrichment - Models
========================================

Modeles SQLAlchemy pour le suivi des enrichissements.
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)

from app.core.types import JSON, UniversalUUID
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class EnrichmentProvider(str, enum.Enum):
    """Fournisseurs d'enrichissement disponibles."""
    # APIs gratuites (implementees)
    INSEE = "insee"
    ADRESSE_GOUV = "adresse_gouv"
    OPENFOODFACTS = "openfoodfacts"
    OPENBEAUTYFACTS = "openbeautyfacts"
    OPENPETFOODFACTS = "openpetfoodfacts"
    VIES = "vies"  # Validation TVA UE
    # APIs payantes (documentation future)
    PAPPERS = "pappers"
    GOOGLE_PLACES = "google_places"
    AMAZON_PAAPI = "amazon_paapi"
    PAGES_JAUNES = "pages_jaunes"


class EnrichmentStatus(str, enum.Enum):
    """Statut d'une requete d'enrichissement."""
    PENDING = "pending"
    SUCCESS = "success"
    PARTIAL = "partial"           # Certains champs enrichis
    NOT_FOUND = "not_found"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


class EnrichmentAction(str, enum.Enum):
    """Action utilisateur sur les donnees suggerees."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PARTIAL = "partial"           # Certains champs acceptes


class LookupType(str, enum.Enum):
    """Types de recherche supportes."""
    SIRET = "siret"
    SIREN = "siren"
    NAME = "name"          # Recherche entreprise par nom
    ADDRESS = "address"
    BARCODE = "barcode"
    VAT_NUMBER = "vat_number"  # Numero TVA UE (validation VIES)
    RISK = "risk"          # Analyse de risque externe (Pappers/INSEE)
    INTERNAL_SCORE = "internal_score"  # Scoring interne basé sur historique


class EntityType(str, enum.Enum):
    """Types d'entites enrichissables."""
    CONTACT = "contact"
    PRODUCT = "product"


# ============================================================================
# MODELS
# ============================================================================

class EnrichmentHistory(Base):
    """
    Historique des tentatives d'enrichissement.
    Lien polymorphique vers l'entite enrichie.
    """
    __tablename__ = "enrichment_history"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Reference polymorphique vers l'entite enrichie
    entity_type = Column(
        Enum(EntityType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    entity_id = Column(UniversalUUID(), nullable=True)  # NULL si avant creation

    # Cle de recherche utilisee
    lookup_type = Column(
        Enum(LookupType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    lookup_value = Column(String(255), nullable=False)

    # Details du fournisseur
    provider = Column(
        Enum(EnrichmentProvider, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    status = Column(
        Enum(EnrichmentStatus, values_callable=lambda x: [e.value for e in x]),
        default=EnrichmentStatus.PENDING
    )

    # Suivi requete/reponse
    request_data = Column(JSON, default=dict)
    response_data = Column(JSON, default=dict)       # Reponse brute API
    enriched_fields = Column(JSON, default=dict)     # Champs mappes pour l'entite

    # Confiance et audit
    confidence_score = Column(Numeric(3, 2), default=Decimal("0.00"))  # 0.00-1.00
    api_response_time_ms = Column(Integer)
    error_message = Column(Text, nullable=True)
    cached = Column(Boolean, default=False)

    # Action utilisateur
    action = Column(
        Enum(EnrichmentAction, values_callable=lambda x: [e.value for e in x]),
        default=EnrichmentAction.PENDING
    )
    accepted_fields = Column(JSON, default=list)     # Champs acceptes
    rejected_fields = Column(JSON, default=list)     # Champs rejetes
    action_at = Column(DateTime, nullable=True)
    action_by = Column(UniversalUUID(), nullable=True)

    # Metadata
    created_by = Column(UniversalUUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_enrichment_tenant', 'tenant_id'),
        Index('idx_enrichment_entity', 'tenant_id', 'entity_type', 'entity_id'),
        Index('idx_enrichment_lookup', 'tenant_id', 'lookup_type', 'lookup_value'),
        Index('idx_enrichment_provider', 'tenant_id', 'provider'),
        Index('idx_enrichment_status', 'tenant_id', 'status'),
        Index('idx_enrichment_created', 'tenant_id', 'created_at'),
    )


class EnrichmentRateLimit(Base):
    """
    Suivi des limites de taux par fournisseur et tenant.
    """
    __tablename__ = "enrichment_rate_limits"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False)
    provider = Column(
        Enum(EnrichmentProvider, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )

    # Limites configurees
    requests_per_minute = Column(Integer, default=60)
    requests_per_day = Column(Integer, default=1000)

    # Utilisation actuelle (reset periodiquement via cache)
    minute_count = Column(Integer, default=0)
    minute_reset_at = Column(DateTime, nullable=True)
    day_count = Column(Integer, default=0)
    day_reset_at = Column(DateTime, nullable=True)

    # Configuration
    is_enabled = Column(Boolean, default=True)
    custom_config = Column(JSON, default=dict)  # Config specifique au provider

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'provider', name='uq_rate_limit_tenant_provider'),
        Index('idx_rate_limit_tenant', 'tenant_id'),
    )


# ============================================================================
# RATE LIMIT DEFAULTS BY PROVIDER
# ============================================================================

PROVIDER_RATE_LIMITS = {
    EnrichmentProvider.INSEE: {
        "requests_per_minute": 30,
        "requests_per_day": 1000,
    },
    EnrichmentProvider.ADRESSE_GOUV: {
        "requests_per_minute": 100,
        "requests_per_day": 10000,
    },
    EnrichmentProvider.OPENFOODFACTS: {
        "requests_per_minute": 60,
        "requests_per_day": 5000,
    },
    EnrichmentProvider.OPENBEAUTYFACTS: {
        "requests_per_minute": 60,
        "requests_per_day": 5000,
    },
    EnrichmentProvider.OPENPETFOODFACTS: {
        "requests_per_minute": 60,
        "requests_per_day": 5000,
    },
    # Pappers gratuit: 100 req/mois = ~3/jour
    EnrichmentProvider.PAPPERS: {
        "requests_per_minute": 10,
        "requests_per_day": 5,  # Limite conservative pour version gratuite
    },
    # VIES: API gratuite UE, pas de limite stricte mais prudence
    EnrichmentProvider.VIES: {
        "requests_per_minute": 20,
        "requests_per_day": 500,
    },
}
