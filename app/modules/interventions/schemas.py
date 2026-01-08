"""
AZALS MODULE INTERVENTIONS - Schemas
=====================================

Schémas Pydantic pour les validations et les API.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator

from .models import (
    InterventionStatut,
    InterventionPriorite,
    TypeIntervention,
    CanalDemande,
)


# ============================================================================
# DONNEUR D'ORDRE SCHEMAS
# ============================================================================

class DonneurOrdreBase(BaseModel):
    """Base donneur d'ordre."""
    code: str = Field(..., max_length=50)
    nom: str = Field(..., max_length=255)
    type: Optional[str] = Field(None, max_length=50)
    client_id: Optional[UUID] = None
    fournisseur_id: Optional[UUID] = None
    email: Optional[str] = Field(None, max_length=255)
    telephone: Optional[str] = Field(None, max_length=50)
    adresse: Optional[str] = None


class DonneurOrdreCreate(DonneurOrdreBase):
    """Création donneur d'ordre."""
    pass


class DonneurOrdreUpdate(BaseModel):
    """Mise à jour donneur d'ordre."""
    nom: Optional[str] = Field(None, max_length=255)
    type: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    telephone: Optional[str] = Field(None, max_length=50)
    adresse: Optional[str] = None
    is_active: Optional[bool] = None


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
    donneur_ordre_id: Optional[UUID] = None  # OPTIONNEL
    projet_id: Optional[UUID] = None  # OPTIONNEL

    type_intervention: TypeIntervention = TypeIntervention.AUTRE
    priorite: InterventionPriorite = InterventionPriorite.NORMAL
    reference_externe: Optional[str] = Field(None, max_length=100)
    canal_demande: Optional[CanalDemande] = None

    titre: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    notes_internes: Optional[str] = None

    # Adresse
    adresse_ligne1: Optional[str] = Field(None, max_length=255)
    adresse_ligne2: Optional[str] = Field(None, max_length=255)
    ville: Optional[str] = Field(None, max_length=100)
    code_postal: Optional[str] = Field(None, max_length=20)
    pays: str = "France"


class InterventionCreate(InterventionBase):
    """
    Création d'une intervention.

    La référence (INT-YYYY-XXXX) est générée automatiquement.
    Le statut initial est A_PLANIFIER.
    """
    date_prevue_debut: Optional[datetime] = None
    date_prevue_fin: Optional[datetime] = None
    intervenant_id: Optional[UUID] = None


class InterventionUpdate(BaseModel):
    """
    Mise à jour intervention.

    ATTENTION: La référence n'est PAS modifiable.
    Le statut ne peut être changé que via les actions terrain.
    """
    donneur_ordre_id: Optional[UUID] = None
    projet_id: Optional[UUID] = None
    type_intervention: Optional[TypeIntervention] = None
    priorite: Optional[InterventionPriorite] = None
    reference_externe: Optional[str] = Field(None, max_length=100)
    canal_demande: Optional[CanalDemande] = None
    titre: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    notes_internes: Optional[str] = None
    adresse_ligne1: Optional[str] = Field(None, max_length=255)
    adresse_ligne2: Optional[str] = Field(None, max_length=255)
    ville: Optional[str] = Field(None, max_length=100)
    code_postal: Optional[str] = Field(None, max_length=20)
    pays: Optional[str] = None


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
    donneur_ordre_id: Optional[UUID] = None
    projet_id: Optional[UUID] = None
    devis_id: Optional[UUID] = None
    facture_client_id: Optional[UUID] = None
    commande_fournisseur_id: Optional[UUID] = None

    type_intervention: TypeIntervention
    priorite: InterventionPriorite
    reference_externe: Optional[str] = None
    canal_demande: Optional[CanalDemande] = None

    titre: Optional[str] = None
    description: Optional[str] = None

    date_prevue_debut: Optional[datetime] = None
    date_prevue_fin: Optional[datetime] = None
    intervenant_id: Optional[UUID] = None
    planning_event_id: Optional[UUID] = None

    date_arrivee_site: Optional[datetime] = None
    date_demarrage: Optional[datetime] = None
    date_fin: Optional[datetime] = None
    duree_reelle_minutes: Optional[int] = None

    geoloc_arrivee_lat: Optional[Decimal] = None
    geoloc_arrivee_lng: Optional[Decimal] = None

    statut: InterventionStatut

    adresse_ligne1: Optional[str] = None
    adresse_ligne2: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    pays: str = "France"

    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class InterventionListResponse(BaseModel):
    """Liste paginée d'interventions."""
    items: List[InterventionResponse]
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
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)


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
    resume_actions: Optional[str] = None
    anomalies: Optional[str] = None
    recommandations: Optional[str] = None


class SignatureRapportRequest(BaseModel):
    """Signature du rapport par le client."""
    signature_client: str  # Base64 du hash/blob sécurisé
    nom_signataire: str = Field(..., max_length=255)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)


class PhotoRequest(BaseModel):
    """Ajout de photo au rapport."""
    url: str
    caption: Optional[str] = None


# ============================================================================
# RAPPORT INTERVENTION SCHEMAS
# ============================================================================

class RapportInterventionBase(BaseModel):
    """Base rapport intervention."""
    resume_actions: Optional[str] = None
    anomalies: Optional[str] = None
    recommandations: Optional[str] = None


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
    donneur_ordre_id: Optional[UUID] = None

    resume_actions: Optional[str] = None
    anomalies: Optional[str] = None
    recommandations: Optional[str] = None
    photos: List[Dict[str, Any]] = []

    signature_client: Optional[str] = None
    date_signature: Optional[datetime] = None
    nom_signataire: Optional[str] = None
    geoloc_signature_lat: Optional[Decimal] = None
    geoloc_signature_lng: Optional[Decimal] = None

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
    projet_id: Optional[UUID] = None
    donneur_ordre_id: Optional[UUID] = None

    interventions_references: List[str]
    temps_total_minutes: int
    synthese: Optional[str] = None

    date_generation: datetime
    is_locked: bool

    created_by: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RapportFinalGenerateRequest(BaseModel):
    """Demande de génération de rapport final."""
    projet_id: Optional[UUID] = None
    donneur_ordre_id: Optional[UUID] = None
    synthese: Optional[str] = None

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
