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
    CorpsEtat,
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
    # Adresse de facturation
    adresse_facturation: str | None = None
    # Facturation et rapports
    delai_paiement: int | None = Field(30, ge=0, le=365, description="Délai de paiement en jours")
    email_rapport: str | None = Field(None, max_length=255, description="Email pour envoi des rapports")
    # Contact commercial
    contact_commercial_nom: str | None = Field(None, max_length=255)
    contact_commercial_email: str | None = Field(None, max_length=255)
    contact_commercial_telephone: str | None = Field(None, max_length=50)
    # Contact comptabilité
    contact_comptabilite_nom: str | None = Field(None, max_length=255)
    contact_comptabilite_email: str | None = Field(None, max_length=255)
    contact_comptabilite_telephone: str | None = Field(None, max_length=50)
    # Contact technique
    contact_technique_nom: str | None = Field(None, max_length=255)
    contact_technique_email: str | None = Field(None, max_length=255)
    contact_technique_telephone: str | None = Field(None, max_length=50)


class DonneurOrdreCreate(DonneurOrdreBase):
    """Création donneur d'ordre. Le code est auto-généré si non fourni."""
    code: str | None = Field(None, max_length=50)  # Optionnel, auto-généré si vide


class DonneurOrdreUpdate(BaseModel):
    """Mise à jour donneur d'ordre."""
    nom: str | None = Field(None, max_length=255)
    type: str | None = Field(None, max_length=50)
    email: str | None = Field(None, max_length=255)
    telephone: str | None = Field(None, max_length=50)
    adresse: str | None = None
    adresse_facturation: str | None = None
    delai_paiement: int | None = Field(None, ge=0, le=365)
    email_rapport: str | None = Field(None, max_length=255)
    contact_commercial_nom: str | None = Field(None, max_length=255)
    contact_commercial_email: str | None = Field(None, max_length=255)
    contact_commercial_telephone: str | None = Field(None, max_length=50)
    contact_comptabilite_nom: str | None = Field(None, max_length=255)
    contact_comptabilite_email: str | None = Field(None, max_length=255)
    contact_comptabilite_telephone: str | None = Field(None, max_length=50)
    contact_technique_nom: str | None = Field(None, max_length=255)
    contact_technique_email: str | None = Field(None, max_length=255)
    contact_technique_telephone: str | None = Field(None, max_length=50)
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
    corps_etat: CorpsEtat | None = None

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
    Le statut initial est DRAFT (brouillon éditable).
    """
    date_prevue_debut: datetime | None = None
    date_prevue_fin: datetime | None = None
    duree_prevue_minutes: int | None = None
    intervenant_id: UUID | None = None
    affaire_id: UUID | None = None

    # Contact sur place
    contact_sur_place: str | None = Field(None, max_length=255)
    telephone_contact: str | None = Field(None, max_length=50)
    email_contact: str | None = Field(None, max_length=255)

    # Notes & matériel
    notes_client: str | None = None
    materiel_necessaire: str | None = None

    # Facturation
    facturable: bool = True
    montant_ht: float | None = None
    montant_ttc: float | None = None


class InterventionUpdate(BaseModel):
    """
    Mise à jour intervention.

    ATTENTION: La référence n'est PAS modifiable.
    Le statut ne peut PAS être changé via cette route.
    Utilisez les actions métier : /valider, /planifier, /demarrer,
    /terminer, /bloquer, /debloquer, /annuler.
    """
    donneur_ordre_id: UUID | None = None
    projet_id: UUID | None = None
    affaire_id: UUID | None = None
    type_intervention: TypeIntervention | None = None
    priorite: InterventionPriorite | None = None
    reference_externe: str | None = Field(None, max_length=100)
    canal_demande: CanalDemande | None = None
    corps_etat: CorpsEtat | None = None
    titre: str | None = Field(None, max_length=500)
    description: str | None = None
    notes_internes: str | None = None
    notes_client: str | None = None
    adresse_ligne1: str | None = Field(None, max_length=255)
    adresse_ligne2: str | None = Field(None, max_length=255)
    ville: str | None = Field(None, max_length=100)
    code_postal: str | None = Field(None, max_length=20)
    pays: str | None = None
    contact_sur_place: str | None = Field(None, max_length=255)
    telephone_contact: str | None = Field(None, max_length=50)
    email_contact: str | None = Field(None, max_length=255)
    materiel_necessaire: str | None = None
    materiel_utilise: str | None = None
    facturable: bool | None = None
    montant_ht: float | None = None
    montant_ttc: float | None = None
    date_prevue_debut: datetime | None = None
    date_prevue_fin: datetime | None = None
    duree_prevue_minutes: int | None = None
    intervenant_id: UUID | None = None


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
    affaire_id: UUID | None = None
    devis_id: UUID | None = None
    facture_client_id: UUID | None = None
    commande_fournisseur_id: UUID | None = None

    type_intervention: TypeIntervention
    priorite: InterventionPriorite
    reference_externe: str | None = None
    canal_demande: CanalDemande | None = None
    corps_etat: CorpsEtat | None = None

    titre: str | None = None
    description: str | None = None
    notes_internes: str | None = None
    notes_client: str | None = None

    date_prevue_debut: datetime | None = None
    date_prevue_fin: datetime | None = None
    duree_prevue_minutes: int | None = None
    intervenant_id: UUID | None = None
    planning_event_id: UUID | None = None

    date_arrivee_site: datetime | None = None
    date_demarrage: datetime | None = None
    date_fin: datetime | None = None
    duree_reelle_minutes: int | None = None

    geoloc_arrivee_lat: Decimal | None = None
    geoloc_arrivee_lng: Decimal | None = None

    statut: InterventionStatut

    # Blocage
    motif_blocage: str | None = None
    date_blocage: datetime | None = None
    date_deblocage: datetime | None = None

    adresse_ligne1: str | None = None
    adresse_ligne2: str | None = None
    ville: str | None = None
    code_postal: str | None = None
    pays: str = "France"

    contact_sur_place: str | None = None
    telephone_contact: str | None = None
    email_contact: str | None = None

    materiel_necessaire: str | None = None
    materiel_utilise: str | None = None

    facturable: bool | None = True
    montant_ht: Decimal | None = None
    montant_ttc: Decimal | None = None

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
    pieces_remplacees: str | None = None
    temps_passe_minutes: int | None = None
    materiel_utilise: str | None = None


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
    pieces_remplacees: str | None = None
    temps_passe_minutes: int | None = None
    materiel_utilise: str | None = None
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

class BlocageRequest(BaseModel):
    """
    Action: bloquer_intervention()

    Motif obligatoire pour traçabilité audit-proof.
    Transition statut: EN_COURS -> BLOQUEE
    """
    motif: str = Field(..., min_length=5, max_length=1000, description="Motif du blocage (obligatoire)")


class InterventionStats(BaseModel):
    """Statistiques interventions."""
    total: int = 0
    brouillons: int = 0
    a_planifier: int = 0
    planifiees: int = 0
    en_cours: int = 0
    bloquees: int = 0
    terminees: int = 0
    duree_moyenne_minutes: float = 0.0


class InterventionsDashboard(BaseModel):
    """Dashboard interventions."""
    stats: InterventionStats
    interventions_jour: int = 0
    intervenants_actifs: int = 0
    retards: int = 0
