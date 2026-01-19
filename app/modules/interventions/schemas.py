"""
AZALS MODULE INTERVENTIONS - Schemas
=====================================

Schémas Pydantic pour les validations et les API.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import (
    CanalDemande,
    InterventionPriorite,
    InterventionStatut,
    TypeIntervention,
)

# ============================================================================
# DONNEUR D'ORDRE SCHEMAS
# ============================================================================

class DonneurOrdreBase(BaseModel):
    """Base donneur d'ordre."""
    code: str = Field(..., max_length=50)
    nom: str = Field(..., max_length=255)
    type: str | None = Field(None, max_length=50)
    client_id: UUID | None = None
    fournisseur_id: UUID | None = None
    email: str | None = Field(None, max_length=255)
    telephone: str | None = Field(None, max_length=50)
    adresse: str | None = None


class DonneurOrdreCreate(DonneurOrdreBase):
    """Création donneur d'ordre."""
    pass


class DonneurOrdreUpdate(BaseModel):
    """Mise à jour donneur d'ordre."""
    nom: str | None = Field(None, max_length=255)
    type: str | None = Field(None, max_length=50)
    email: str | None = Field(None, max_length=255)
    telephone: str | None = Field(None, max_length=50)
    adresse: str | None = None
    is_active: bool | None = None


class DonneurOrdreResponse(DonneurOrdreBase):
    """Réponse donneur d'ordre."""
    id: UUID
    tenant_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# INTERVENTION SCHEMAS
# ============================================================================

class InterventionBase(BaseModel):
    """Base intervention."""
    client_id: UUID  # OBLIGATOIRE
    donneur_ordre_id: UUID | None = None  # OPTIONNEL
    projet_id: UUID | None = None  # OPTIONNEL

    type_intervention: TypeIntervention = TypeIntervention.AUTRE
    priorite: InterventionPriorite = InterventionPriorite.NORMAL
    reference_externe: str | None = Field(None, max_length=100)
    canal_demande: CanalDemande | None = None

    titre: str | None = Field(None, max_length=500)
    description: str | None = None
    notes_internes: str | None = None

    # Adresse
    adresse_ligne1: str | None = Field(None, max_length=255)
    adresse_ligne2: str | None = Field(None, max_length=255)
    ville: str | None = Field(None, max_length=100)
    code_postal: str | None = Field(None, max_length=20)
    pays: str = "France"


class InterventionCreate(InterventionBase):
    """
    Création d'une intervention.

    La référence (INT-YYYY-XXXX) est générée automatiquement.
    Le statut initial est A_PLANIFIER.
    """
    date_prevue_debut: datetime | None = None
    date_prevue_fin: datetime | None = None
    intervenant_id: UUID | None = None


class InterventionUpdate(BaseModel):
    """
    Mise à jour intervention.

    ATTENTION: La référence n'est PAS modifiable.
    Le statut ne peut être changé que via les actions terrain.
    """
    donneur_ordre_id: UUID | None = None
    projet_id: UUID | None = None
    type_intervention: TypeIntervention | None = None
    priorite: InterventionPriorite | None = None
    reference_externe: str | None = Field(None, max_length=100)
    canal_demande: CanalDemande | None = None
    titre: str | None = Field(None, max_length=500)
    description: str | None = None
    notes_internes: str | None = None
    adresse_ligne1: str | None = Field(None, max_length=255)
    adresse_ligne2: str | None = Field(None, max_length=255)
    ville: str | None = Field(None, max_length=100)
    code_postal: str | None = Field(None, max_length=20)
    pays: str | None = None


class InterventionPlanifier(BaseModel):
    """Planification d'une intervention."""
    date_prevue_debut: datetime
    date_prevue_fin: datetime
    intervenant_id: UUID

    @field_validator('date_prevue_fin')
    @classmethod
    def validate_dates(cls, v, info):
        """Vérifie que date_fin >= date_debut."""
        if 'date_prevue_debut' in info.data and v < info.data['date_prevue_debut']:
            raise ValueError("date_prevue_fin doit être >= date_prevue_debut")
        return v


class InterventionResponse(BaseModel):
    """Réponse intervention complète."""
    id: UUID
    tenant_id: str
    reference: str  # INT-YYYY-XXXX (NON MODIFIABLE)

    client_id: UUID
    donneur_ordre_id: UUID | None = None
    projet_id: UUID | None = None
    devis_id: UUID | None = None
    facture_client_id: UUID | None = None
    commande_fournisseur_id: UUID | None = None

    type_intervention: TypeIntervention
    priorite: InterventionPriorite
    reference_externe: str | None = None
    canal_demande: CanalDemande | None = None

    titre: str | None = None
    description: str | None = None

    date_prevue_debut: datetime | None = None
    date_prevue_fin: datetime | None = None
    intervenant_id: UUID | None = None
    planning_event_id: UUID | None = None

    date_arrivee_site: datetime | None = None
    date_demarrage: datetime | None = None
    date_fin: datetime | None = None
    duree_reelle_minutes: int | None = None

    geoloc_arrivee_lat: Decimal | None = None
    geoloc_arrivee_lng: Decimal | None = None

    statut: InterventionStatut

    adresse_ligne1: str | None = None
    adresse_ligne2: str | None = None
    ville: str | None = None
    code_postal: str | None = None
    pays: str = "France"

    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class InterventionListResponse(BaseModel):
    """Liste paginée d'interventions."""
    items: list[InterventionResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# ACTIONS TERRAIN SCHEMAS
# ============================================================================

class ArriveeRequest(BaseModel):
    """
    Action: arrivee_sur_site()

    Horodate l'arrivée sur site avec géolocalisation.
    Transition statut: PLANIFIEE -> EN_COURS
    """
    latitude: Decimal | None = Field(None, ge=-90, le=90)
    longitude: Decimal | None = Field(None, ge=-180, le=180)


class DemarrageRequest(BaseModel):
    """
    Action: demarrer_intervention()

    Horodate le démarrage effectif de l'intervention.
    Requiert: statut EN_COURS (arrivée déjà enregistrée)
    """
    pass  # Aucun paramètre requis, l'horodatage est automatique


class FinInterventionRequest(BaseModel):
    """
    Action: terminer_intervention()

    Horodate la fin de l'intervention.
    Calcule automatiquement la durée_reelle_minutes.
    Transition statut: EN_COURS -> TERMINEE
    Déclenche la génération du rapport d'intervention.
    """
    resume_actions: str | None = None
    anomalies: str | None = None
    recommandations: str | None = None


class SignatureRapportRequest(BaseModel):
    """Signature du rapport par le client."""
    signature_client: str  # Base64 du hash/blob sécurisé
    nom_signataire: str = Field(..., max_length=255)
    latitude: Decimal | None = Field(None, ge=-90, le=90)
    longitude: Decimal | None = Field(None, ge=-180, le=180)


class PhotoRequest(BaseModel):
    """Ajout de photo au rapport."""
    url: str
    caption: str | None = None


# ============================================================================
# RAPPORT INTERVENTION SCHEMAS
# ============================================================================

class RapportInterventionBase(BaseModel):
    """Base rapport intervention."""
    resume_actions: str | None = None
    anomalies: str | None = None
    recommandations: str | None = None


class RapportInterventionUpdate(RapportInterventionBase):
    """
    Mise à jour rapport.

    ATTENTION: Impossible si le rapport est signé/verrouillé.
    """
    pass


class RapportInterventionResponse(BaseModel):
    """Réponse rapport intervention."""
    id: UUID
    tenant_id: str
    intervention_id: UUID
    reference_intervention: str
    client_id: UUID
    donneur_ordre_id: UUID | None = None

    resume_actions: str | None = None
    anomalies: str | None = None
    recommandations: str | None = None
    photos: list[dict[str, Any]] = []

    signature_client: str | None = None
    date_signature: datetime | None = None
    nom_signataire: str | None = None
    geoloc_signature_lat: Decimal | None = None
    geoloc_signature_lng: Decimal | None = None

    is_signed: bool
    is_locked: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# RAPPORT FINAL SCHEMAS
# ============================================================================

class RapportFinalResponse(BaseModel):
    """Réponse rapport final consolidé."""
    id: UUID
    tenant_id: str
    reference: str
    projet_id: UUID | None = None
    donneur_ordre_id: UUID | None = None

    interventions_references: list[str]
    temps_total_minutes: int
    synthese: str | None = None

    date_generation: datetime
    is_locked: bool

    created_by: UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RapportFinalGenerateRequest(BaseModel):
    """Demande de génération de rapport final."""
    projet_id: UUID | None = None
    donneur_ordre_id: UUID | None = None
    synthese: str | None = None

    @field_validator('donneur_ordre_id')
    @classmethod
    def validate_critere(cls, v, info):
        """Au moins un critère de regroupement requis."""
        if not v and not info.data.get('projet_id'):
            raise ValueError("Au moins projet_id ou donneur_ordre_id requis")
        return v


# ============================================================================
# STATISTIQUES SCHEMAS
# ============================================================================

class InterventionStats(BaseModel):
    """Statistiques interventions."""
    total: int = 0
    a_planifier: int = 0
    planifiees: int = 0
    en_cours: int = 0
    terminees: int = 0
    duree_moyenne_minutes: float = 0.0


class InterventionsDashboard(BaseModel):
    """Dashboard interventions."""
    stats: InterventionStats
    interventions_jour: int = 0
    intervenants_actifs: int = 0
    retards: int = 0
