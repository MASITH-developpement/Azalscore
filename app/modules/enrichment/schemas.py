"""
AZALS MODULE - Auto-Enrichment - Schemas
=========================================

Schemas Pydantic pour l'API d'enrichissement.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .models import (
    EnrichmentAction,
    EnrichmentProvider,
    EnrichmentStatus,
    EntityType,
    LookupType,
)


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class EnrichmentLookupRequest(BaseModel):
    """Requete de recherche d'enrichissement."""

    lookup_type: LookupType = Field(
        ...,
        description="Type de recherche: siret, siren, address, barcode"
    )
    lookup_value: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Valeur a rechercher"
    )
    entity_type: EntityType = Field(
        default=EntityType.CONTACT,
        description="Type d'entite cible: contact, product"
    )
    entity_id: Optional[UUID] = Field(
        default=None,
        description="ID de l'entite existante (optionnel)"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "lookup_type": "siret",
                    "lookup_value": "44306184100047",
                    "entity_type": "contact"
                },
                {
                    "lookup_type": "barcode",
                    "lookup_value": "3017620422003",
                    "entity_type": "product"
                },
                {
                    "lookup_type": "address",
                    "lookup_value": "10 rue de la paix paris",
                    "entity_type": "contact"
                }
            ]
        }


class EnrichmentAcceptRequest(BaseModel):
    """Requete d'acceptation/rejet des donnees enrichies."""

    accepted_fields: list[str] = Field(
        default_factory=list,
        description="Liste des champs acceptes"
    )
    rejected_fields: list[str] = Field(
        default_factory=list,
        description="Liste des champs rejetes"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "accepted_fields": ["name", "address_line1", "postal_code", "city"],
                "rejected_fields": ["legal_form"]
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class AddressSuggestion(BaseModel):
    """Suggestion d'adresse pour autocomplete."""

    label: str = Field(..., description="Adresse complete formatee")
    address_line1: str = Field(default="", description="Numero et voie")
    house_number: Optional[str] = Field(default=None, description="Numero")
    street: Optional[str] = Field(default=None, description="Nom de la voie")
    postal_code: str = Field(default="", description="Code postal")
    city: str = Field(default="", description="Ville")
    context: Optional[str] = Field(default=None, description="Departement, region")
    latitude: Optional[float] = Field(default=None, description="Latitude GPS")
    longitude: Optional[float] = Field(default=None, description="Longitude GPS")
    score: float = Field(default=0, description="Score de pertinence (0-1)")
    type: Optional[str] = Field(default=None, description="Type: housenumber, street, municipality")


class CompanySuggestion(BaseModel):
    """Suggestion d'entreprise pour autocomplete."""

    label: str = Field(..., description="Nom entreprise formate")
    value: str = Field(default="", description="SIRET ou SIREN")
    siren: str = Field(default="", description="Numero SIREN (9 chiffres)")
    siret: str = Field(default="", description="Numero SIRET (14 chiffres)")
    name: str = Field(default="", description="Nom de l'entreprise")
    address: str = Field(default="", description="Adresse du siege")
    city: str = Field(default="", description="Ville")
    postal_code: str = Field(default="", description="Code postal")
    data: Optional[dict[str, Any]] = Field(default=None, description="Donnees completes")


class RiskFactor(BaseModel):
    """Facteur de risque individuel."""

    factor: str = Field(..., description="Description du facteur")
    impact: int = Field(..., description="Impact sur le score (-80 a +15)")
    severity: str = Field(..., description="Gravite: positive, low, medium, high, critical")
    source: Optional[str] = Field(default=None, description="Source du facteur")


class RiskAnalysis(BaseModel):
    """Analyse de risque complete d'une entreprise."""

    score: int = Field(..., ge=0, le=100, description="Score de risque (0-100)")
    level: str = Field(..., description="Niveau: low, medium, elevated, high")
    level_label: str = Field(..., description="Libelle du niveau en francais")
    color: str = Field(..., description="Couleur associee: green, yellow, orange, red")
    factors: list[RiskFactor] = Field(default_factory=list, description="Facteurs de risque")
    alerts: list[str] = Field(default_factory=list, description="Alertes critiques")
    recommendation: str = Field(default="", description="Recommandation")
    cotation_bdf: Optional[str] = Field(default=None, description="Cotation Banque de France")

    class Config:
        json_schema_extra = {
            "example": {
                "score": 75,
                "level": "medium",
                "level_label": "Risque modere",
                "color": "yellow",
                "factors": [
                    {"factor": "Entreprise etablie (12 ans)", "impact": 5, "severity": "positive"},
                    {"factor": "Aucun compte publie", "impact": -5, "severity": "low"}
                ],
                "alerts": [],
                "recommendation": "Surveillance recommandee - Limiter les encours"
            }
        }


class EnrichmentLookupResponse(BaseModel):
    """Reponse de recherche d'enrichissement."""

    success: bool = Field(..., description="Recherche reussie")
    enriched_fields: dict[str, Any] = Field(
        default_factory=dict,
        description="Champs enrichis mappes pour l'entite"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Score de confiance (0-1)"
    )
    source: Optional[str] = Field(
        default=None,
        description="Provider source des donnees"
    )
    cached: bool = Field(
        default=False,
        description="Donnees provenant du cache"
    )
    history_id: Optional[str] = Field(
        default=None,
        description="ID de l'historique pour accept/reject"
    )
    suggestions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Suggestions d'adresses ou d'entreprises (pour autocomplete)"
    )
    error: Optional[str] = Field(
        default=None,
        description="Message d'erreur si echec"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "enriched_fields": {
                    "name": "GOOGLE FRANCE",
                    "address_line1": "8 rue de Londres",
                    "postal_code": "75009",
                    "city": "Paris",
                    "legal_form": "SAS"
                },
                "confidence": 1.0,
                "source": "insee",
                "cached": False,
                "history_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class EnrichmentHistoryResponse(BaseModel):
    """Historique d'un enrichissement."""

    id: UUID
    entity_type: str
    entity_id: Optional[UUID]
    lookup_type: str
    lookup_value: str
    provider: str
    status: str
    enriched_fields: dict[str, Any]
    confidence_score: Optional[Decimal]
    api_response_time_ms: Optional[int]
    cached: bool
    error_message: Optional[str]
    action: str
    accepted_fields: list[str]
    rejected_fields: list[str]
    action_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_custom(cls, obj) -> "EnrichmentHistoryResponse":
        """Constructeur personnalise depuis ORM."""
        return cls(
            id=obj.id,
            entity_type=obj.entity_type.value if obj.entity_type else "",
            entity_id=obj.entity_id,
            lookup_type=obj.lookup_type.value if obj.lookup_type else "",
            lookup_value=obj.lookup_value,
            provider=obj.provider.value if obj.provider else "",
            status=obj.status.value if obj.status else "",
            enriched_fields=obj.enriched_fields or {},
            confidence_score=obj.confidence_score,
            api_response_time_ms=obj.api_response_time_ms,
            cached=obj.cached or False,
            error_message=obj.error_message,
            action=obj.action.value if obj.action else "",
            accepted_fields=obj.accepted_fields or [],
            rejected_fields=obj.rejected_fields or [],
            action_at=obj.action_at,
            created_at=obj.created_at,
        )


class EnrichmentStatsResponse(BaseModel):
    """Statistiques d'enrichissement."""

    total_lookups: int = Field(default=0, description="Total de recherches")
    successful_lookups: int = Field(default=0, description="Recherches reussies")
    cached_lookups: int = Field(default=0, description="Recherches en cache")
    accepted_enrichments: int = Field(default=0, description="Enrichissements acceptes")
    rejected_enrichments: int = Field(default=0, description="Enrichissements rejetes")
    avg_confidence: float = Field(default=0.0, description="Confiance moyenne")
    avg_response_time_ms: float = Field(default=0.0, description="Temps de reponse moyen")
    by_provider: dict[str, int] = Field(default_factory=dict, description="Lookups par provider")
    by_lookup_type: dict[str, int] = Field(default_factory=dict, description="Lookups par type")


# ============================================================================
# RATE LIMIT SCHEMAS
# ============================================================================

class RateLimitStatus(BaseModel):
    """Statut des limites de taux pour un provider."""

    provider: str
    is_enabled: bool
    requests_per_minute: int
    requests_per_day: int
    minute_remaining: int
    day_remaining: int
    reset_minute_at: Optional[datetime]
    reset_day_at: Optional[datetime]
