"""
AZALS MODULE INTERVENTIONS - Schemas V2
========================================

Schemas Pydantic enrichis pour l'API v2.

Différences avec v1 :
- Noms résolus (client_name, donneur_ordre_name, intervenant_name)
- Rapport intégré dans la réponse intervention
- Statistiques enrichies (terminees_semaine, terminees_mois, interventions_jour)
- Champs aliasés pour compatibilité frontend
  (travaux_realises = resume_actions, observations = anomalies)
"""
from __future__ import annotations


from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .models import (
    CanalDemande,
    InterventionPriorite,
    InterventionStatut,
    TypeIntervention,
)


# ============================================================================
# RAPPORT V2 (aligné frontend)
# ============================================================================

class RapportInterventionV2Response(BaseModel):
    """
    Rapport d'intervention pour le frontend v2.

    Le frontend utilise :
    - travaux_realises (backend: resume_actions)
    - observations (backend: anomalies)
    """
    id: UUID
    intervention_id: UUID

    travaux_realises: str | None = None
    observations: str | None = None
    recommandations: str | None = None
    pieces_remplacees: str | None = None
    temps_passe_minutes: int | None = None
    materiel_utilise: str | None = None
    photos: list[str] = []

    signature_client: str | None = None
    nom_signataire: str | None = None
    is_signed: bool = False

    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# INTERVENTION V2 RESPONSE (enrichie)
# ============================================================================

class InterventionV2Response(BaseModel):
    """
    Réponse intervention v2, enrichie avec noms résolus et rapport intégré.

    Alignée strictement sur le type TypeScript 'Intervention' du frontend.
    """
    id: str
    reference: str

    # Client
    client_id: str
    client_name: str | None = None
    client_code: str | None = None

    # Donneur d'ordre
    donneur_ordre_id: str | None = None
    donneur_ordre_name: str | None = None

    # Projet / Affaire
    projet_id: str | None = None
    projet_name: str | None = None
    affaire_id: str | None = None
    affaire_reference: str | None = None

    # Type & priorité
    type_intervention: str
    priorite: str
    corps_etat: str | None = None

    # Détails
    titre: str | None = None
    description: str | None = None

    # Planification
    date_prevue: str | None = None
    heure_prevue: str | None = None
    date_prevue_debut: str | None = None
    date_prevue_fin: str | None = None
    duree_prevue_minutes: int | None = None

    # Intervenant
    intervenant_id: str | None = None
    intervenant_name: str | None = None
    equipe: list[dict[str, Any]] = []

    # Statut
    statut: str

    # Exécution réelle
    date_debut_reelle: str | None = None
    date_fin_reelle: str | None = None
    duree_reelle_minutes: int | None = None

    # Adresse
    adresse_intervention: str | None = None
    adresse_ligne1: str | None = None
    adresse_ligne2: str | None = None
    ville: str | None = None
    code_postal: str | None = None

    # Contact sur place
    contact_sur_place: str | None = None
    telephone_contact: str | None = None
    email_contact: str | None = None

    # Notes
    notes_internes: str | None = None
    notes_client: str | None = None
    materiel_necessaire: str | None = None
    materiel_utilise: str | None = None

    # Rapport
    rapport: RapportInterventionV2Response | None = None

    # Documents & History (structure ready)
    documents: list[dict[str, Any]] = []
    history: list[dict[str, Any]] = []

    # Facturation
    facturable: bool | None = True
    montant_ht: float | None = None
    montant_ttc: float | None = None
    facture_id: str | None = None
    facture_reference: str | None = None

    # Référence externe
    reference_externe: str | None = None

    # Méta
    created_at: str
    updated_at: str
    created_by: str | None = None


# ============================================================================
# INTERVENTION V2 STATS (enrichies)
# ============================================================================

class InterventionStatsV2(BaseModel):
    """Statistiques interventions v2, alignées frontend."""
    a_planifier: int = 0
    planifiees: int = 0
    en_cours: int = 0
    terminees_semaine: int = 0
    terminees_mois: int = 0
    duree_moyenne_minutes: float = 0.0
    interventions_jour: int = 0


# ============================================================================
# DONNEUR D'ORDRE V2 RESPONSE
# ============================================================================

class DonneurOrdreV2Response(BaseModel):
    """
    Donneur d'ordre v2, aligné type TypeScript DonneurOrdre.
    """
    id: str
    nom: str
    email: str | None = None
    telephone: str | None = None
    entreprise: str | None = None
    is_active: bool = True
