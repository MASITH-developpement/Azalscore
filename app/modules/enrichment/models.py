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
    OPENCORPORATES = "opencorporates"  # Registres mondiaux
    # APIs payantes (documentation future)
    PAPPERS = "pappers"
    GOOGLE_PLACES = "google_places"
    AMAZON_PAAPI = "amazon_paapi"
    PAGES_JAUNES = "pages_jaunes"
    CREDITSAFE = "creditsafe"
    KOMPANY = "kompany"


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
    # OpenCorporates: API gratuite limitee (500 req/mois pour version gratuite)
    EnrichmentProvider.OPENCORPORATES: {
        "requests_per_minute": 10,
        "requests_per_day": 20,  # ~600/mois
    },
    # APIs payantes - limites elevees si cle API configuree
    EnrichmentProvider.CREDITSAFE: {
        "requests_per_minute": 30,
        "requests_per_day": 1000,
    },
    EnrichmentProvider.KOMPANY: {
        "requests_per_minute": 30,
        "requests_per_day": 1000,
    },
}


# ============================================================================
# PROVIDER CONFIG MODEL
# ============================================================================

class EnrichmentProviderConfig(Base):
    """
    Configuration des fournisseurs d'enrichissement par tenant.
    Stocke les API keys et parametres specifiques.
    """
    __tablename__ = "enrichment_provider_config"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    provider = Column(
        Enum(EnrichmentProvider, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )

    # Configuration
    is_enabled = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)  # Provider principal pour ce type
    priority = Column(Integer, default=100)  # Ordre de priorite (plus bas = plus prioritaire)

    # Credentials (chiffres en DB)
    api_key = Column(String(500), nullable=True)  # Cle API principale
    api_secret = Column(String(500), nullable=True)  # Secret optionnel
    api_endpoint = Column(String(500), nullable=True)  # URL custom si applicable

    # Limites personnalisees
    custom_requests_per_minute = Column(Integer, nullable=True)
    custom_requests_per_day = Column(Integer, nullable=True)

    # Metadata
    config_data = Column(JSON, default=dict)  # Config specifique au provider
    last_success_at = Column(DateTime, nullable=True)
    last_error_at = Column(DateTime, nullable=True)
    last_error_message = Column(Text, nullable=True)
    total_requests = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'provider', name='uq_provider_config_tenant_provider'),
        Index('idx_provider_config_tenant', 'tenant_id'),
        Index('idx_provider_config_enabled', 'tenant_id', 'is_enabled'),
        Index('idx_provider_config_primary', 'tenant_id', 'is_primary'),
    )


# Informations sur les providers (pour l'interface admin)
PROVIDER_INFO = {
    EnrichmentProvider.INSEE: {
        "name": "INSEE (SIRENE)",
        "description": "Recherche entreprises francaises par SIRET/SIREN/nom",
        "requires_api_key": False,
        "is_free": True,
        "country": "FR",
        "capabilities": ["siret", "siren", "name"],
        "documentation_url": "https://api.insee.fr/catalogue/site/themes/wso2/subthemes/insee/pages/item-info.jag?name=Sirene&version=V3&provider=insee",
    },
    EnrichmentProvider.ADRESSE_GOUV: {
        "name": "API Adresse (data.gouv.fr)",
        "description": "Geocodage et autocomplete adresses francaises",
        "requires_api_key": False,
        "is_free": True,
        "country": "FR",
        "capabilities": ["address"],
        "documentation_url": "https://adresse.data.gouv.fr/api-doc/adresse",
    },
    EnrichmentProvider.OPENFOODFACTS: {
        "name": "Open Food Facts",
        "description": "Base de donnees produits alimentaires par code-barres",
        "requires_api_key": False,
        "is_free": True,
        "country": "WORLD",
        "capabilities": ["barcode"],
        "documentation_url": "https://openfoodfacts.github.io/openfoodfacts-server/api/",
    },
    EnrichmentProvider.VIES: {
        "name": "VIES (Commission Europeenne)",
        "description": "Validation numeros TVA intracommunautaires",
        "requires_api_key": False,
        "is_free": True,
        "country": "EU",
        "capabilities": ["vat_number"],
        "documentation_url": "https://ec.europa.eu/taxation_customs/vies/#/vat-validation",
    },
    EnrichmentProvider.PAPPERS: {
        "name": "Pappers",
        "description": "Analyse de risque et informations legales entreprises francaises",
        "requires_api_key": True,
        "is_free": False,  # Version gratuite limitee
        "country": "FR",
        "capabilities": ["risk", "siret", "siren"],
        "documentation_url": "https://www.pappers.fr/api",
    },
    EnrichmentProvider.OPENCORPORATES: {
        "name": "OpenCorporates",
        "description": "Registres d'entreprises mondiaux (140+ pays)",
        "requires_api_key": True,
        "is_free": False,  # Version gratuite limitee
        "country": "WORLD",
        "capabilities": ["name", "company_number"],
        "documentation_url": "https://api.opencorporates.com/documentation",
    },
    EnrichmentProvider.CREDITSAFE: {
        "name": "Creditsafe",
        "description": "Notation credit et risque internationale",
        "requires_api_key": True,
        "is_free": False,
        "country": "WORLD",
        "capabilities": ["risk", "credit_score"],
        "documentation_url": "https://www.creditsafe.com/",
    },
    EnrichmentProvider.KOMPANY: {
        "name": "Kompany",
        "description": "Documents officiels et comptes annuels europeens",
        "requires_api_key": True,
        "is_free": False,
        "country": "EU",
        "capabilities": ["documents", "financials"],
        "documentation_url": "https://www.kompany.com/",
    },
}
