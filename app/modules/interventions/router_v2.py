"""
AZALS MODULE INTERVENTIONS - Router API v2 (CORE SaaS)
======================================================

Router v2 aligné strictement sur le frontend React/TypeScript.

Différences avec le v2 précédent (simple copie v1) :
- Réponses enrichies avec noms résolus (client_name, donneur_ordre_name, intervenant_name)
- Rapport intégré dans la réponse intervention
- Statistiques enrichies (terminees_semaine, terminees_mois, interventions_jour)
- Champs aliasés pour le frontend (travaux_realises, observations, date_debut_reelle)
- Filtres string (le frontend envoie des strings, pas des enums)
- Endpoint /annuler pour le statut ANNULEE
- Format de réponse { items: [...], total: N } pour les listes

Endpoints :
- GET    /v2/interventions              → Liste paginée avec filtres
- GET    /v2/interventions/stats        → Statistiques enrichies
- GET    /v2/interventions/donneurs-ordre → Liste donneurs d'ordre
- GET    /v2/interventions/donneurs-ordre/{id}
- POST   /v2/interventions/donneurs-ordre
- PUT    /v2/interventions/donneurs-ordre/{id}
- GET    /v2/interventions/rapports-finaux
- GET    /v2/interventions/rapports-finaux/{id}
- POST   /v2/interventions/rapports-finaux
- GET    /v2/interventions/ref/{reference}
- GET    /v2/interventions/{id}
- POST   /v2/interventions
- PUT    /v2/interventions/{id}
- DELETE /v2/interventions/{id}
- POST   /v2/interventions/{id}/planifier
- PUT    /v2/interventions/{id}/planification
- DELETE /v2/interventions/{id}/planification
- POST   /v2/interventions/{id}/arrivee
- POST   /v2/interventions/{id}/demarrer
- POST   /v2/interventions/{id}/terminer
- POST   /v2/interventions/{id}/annuler
- POST   /v2/interventions/{id}/valider
- POST   /v2/interventions/{id}/bloquer
- POST   /v2/interventions/{id}/debloquer
- GET    /v2/interventions/{id}/analyse-ia
- GET    /v2/interventions/{id}/rapport
- PUT    /v2/interventions/{id}/rapport
- POST   /v2/interventions/{id}/rapport/photos
- POST   /v2/interventions/{id}/rapport/signer
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.entity_resolver import EntityResolver
from app.core.saas_context import SaaSContext

from .models import DonneurOrdre, Intervention, InterventionPriorite, InterventionStatut
from .schemas import (
    ArriveeRequest,
    BlocageRequest,
    DonneurOrdreCreate,
    DonneurOrdreUpdate,
    FinInterventionRequest,
    InterventionCreate,
    InterventionPlanifier,
    InterventionUpdate,
    PhotoRequest,
    RapportFinalGenerateRequest,
    RapportFinalResponse,
    RapportInterventionUpdate,
    SignatureRapportRequest,
)
from .schemas_v2 import (
    DonneurOrdreV2Response,
    InterventionV2Response,
    RapportInterventionV2Response,
)
from .service import (
    InterventionNotFoundError,
    InterventionsService,
    InterventionWorkflowError,
    RapportLockedError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2/interventions", tags=["Interventions v2 - CORE SaaS"])


# ============================================================================
# SERVICE FACTORY
# ============================================================================

def _get_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
) -> InterventionsService:
    """Factory service avec SaaSContext v2."""
    return InterventionsService(
        db=db,
        tenant_id=context.tenant_id,
        user_id=str(context.user_id),
    )


# ============================================================================
# HELPERS — SERIALISATION V2
# ============================================================================

def _require_write_access(context: SaaSContext) -> None:
    """
    Vérifie que l'utilisateur a les droits d'écriture (AZA-SEC).

    Rôles autorisés en écriture:
    - SUPERADMIN, DIRIGEANT, ADMIN : accès complet
    - DAF, COMPTABLE : accès écriture (gestion financière)
    - COMMERCIAL : accès écriture (création/modification interventions)
    - EMPLOYE : lecture seule
    """
    if context.role.value in ("EMPLOYE",):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès en écriture refusé. Rôle EMPLOYE : lecture seule.",
        )


def _require_admin_access(context: SaaSContext) -> None:
    """
    Vérifie que l'utilisateur a les droits d'administration (AZA-SEC).

    Requis pour : suppression, annulation d'intervention.
    """
    if context.role.value not in ("SUPERADMIN", "DIRIGEANT", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès administrateur requis pour cette opération.",
        )


def _iso(dt: datetime | None) -> str | None:
    """Formate un datetime en ISO 8601 string."""
    return dt.isoformat() if dt else None


def _uid(val) -> str | None:
    """Formate un UUID en string."""
    return str(val) if val else None


def _build_address(intervention: Intervention) -> str | None:
    """Construit l'adresse complète en une chaîne."""
    parts = [
        intervention.adresse_ligne1,
        intervention.adresse_ligne2,
    ]
    if intervention.code_postal and intervention.ville:
        parts.append(f"{intervention.code_postal} {intervention.ville}")
    elif intervention.ville:
        parts.append(intervention.ville)
    filtered = [p for p in parts if p]
    return ", ".join(filtered) if filtered else None


def _get_resolver(db: Session, tenant_id: str) -> EntityResolver:
    """Construit un EntityResolver pour la résolution cross-modules (AZA-NF-003)."""
    return EntityResolver(db=db, tenant_id=tenant_id)


def _build_rapport_v2(rapport) -> dict | None:
    """Transforme un RapportIntervention en dict v2 (champs aliasés pour le frontend)."""
    if rapport is None:
        return None

    # Le frontend attend photos comme liste de strings (URLs)
    photos_raw = rapport.photos or []
    photos_urls = []
    for p in photos_raw:
        if isinstance(p, dict):
            photos_urls.append(p.get("url", ""))
        elif isinstance(p, str):
            photos_urls.append(p)

    return {
        "id": str(rapport.id),
        "intervention_id": str(rapport.intervention_id),
        "travaux_realises": rapport.resume_actions,
        "observations": rapport.anomalies,
        "recommandations": rapport.recommandations,
        "pieces_remplacees": getattr(rapport, "pieces_remplacees", None),
        "temps_passe_minutes": getattr(rapport, "temps_passe_minutes", None),
        "materiel_utilise": getattr(rapport, "materiel_utilise", None),
        "photos": photos_urls,
        "signature_client": rapport.signature_client,
        "nom_signataire": rapport.nom_signataire,
        "is_signed": rapport.is_signed,
        "created_at": _iso(rapport.created_at),
    }


def _serialize_intervention(intervention: Intervention, db: Session, tenant_id: str) -> dict:
    """
    Sérialise une Intervention en dict v2 aligné sur le type TypeScript.

    Résout les noms depuis les modules liés via EntityResolver (AZA-NF-003),
    intègre le rapport, construit l'adresse complète, et aliase les champs.
    """
    resolver = _get_resolver(db, tenant_id)
    client_name, client_code = resolver.resolve_client(intervention.client_id)
    intervenant_name = resolver.resolve_employee(intervention.intervenant_id)
    donneur_name = intervention.donneur_ordre.nom if intervention.donneur_ordre else None

    # Rapport intégré
    rapport_v2 = _build_rapport_v2(intervention.rapport)

    # Durée prévue : champ direct ou calcul à partir des dates
    duree_prevue = getattr(intervention, "duree_prevue_minutes", None)
    if duree_prevue is None and intervention.date_prevue_debut and intervention.date_prevue_fin:
        delta = (intervention.date_prevue_fin - intervention.date_prevue_debut).total_seconds()
        duree_prevue = int(delta / 60) if delta > 0 else None

    return {
        "id": str(intervention.id),
        "reference": intervention.reference,

        # Client
        "client_id": str(intervention.client_id),
        "client_name": client_name,
        "client_code": client_code,

        # Donneur d'ordre
        "donneur_ordre_id": _uid(intervention.donneur_ordre_id),
        "donneur_ordre_name": donneur_name,

        # Projet / Affaire
        "projet_id": _uid(intervention.projet_id),
        "projet_name": None,
        "affaire_id": _uid(getattr(intervention, "affaire_id", None)),
        "affaire_reference": None,

        # Type & priorité
        "type_intervention": intervention.type_intervention.value if intervention.type_intervention else "AUTRE",
        "priorite": intervention.priorite.value if intervention.priorite else "NORMAL",
        "corps_etat": intervention.corps_etat.value if intervention.corps_etat else None,

        # Détails
        "titre": intervention.titre,
        "description": intervention.description,

        # Planification
        "date_prevue": _iso(intervention.date_prevue_debut),
        "heure_prevue": (
            intervention.date_prevue_debut.strftime("%H:%M")
            if intervention.date_prevue_debut else None
        ),
        "date_prevue_debut": _iso(intervention.date_prevue_debut),
        "date_prevue_fin": _iso(intervention.date_prevue_fin),
        "duree_prevue_minutes": duree_prevue,

        # Intervenant
        "intervenant_id": _uid(intervention.intervenant_id),
        "intervenant_name": intervenant_name,
        "equipe": [],

        # Statut
        "statut": intervention.statut.value,

        # Blocage
        "motif_blocage": getattr(intervention, "motif_blocage", None),
        "date_blocage": _iso(getattr(intervention, "date_blocage", None)),
        "date_deblocage": _iso(getattr(intervention, "date_deblocage", None)),

        # Exécution réelle (aliasés pour le frontend)
        "date_debut_reelle": _iso(intervention.date_demarrage),
        "date_fin_reelle": _iso(intervention.date_fin),
        "duree_reelle_minutes": intervention.duree_reelle_minutes,

        # Adresse
        "adresse_intervention": _build_address(intervention),
        "adresse_ligne1": intervention.adresse_ligne1,
        "adresse_ligne2": intervention.adresse_ligne2,
        "ville": intervention.ville,
        "code_postal": intervention.code_postal,

        # Contact sur place
        "contact_sur_place": getattr(intervention, "contact_sur_place", None),
        "telephone_contact": getattr(intervention, "telephone_contact", None),
        "email_contact": getattr(intervention, "email_contact", None),

        # Notes & matériel
        "notes_internes": intervention.notes_internes,
        "notes_client": getattr(intervention, "notes_client", None),
        "materiel_necessaire": getattr(intervention, "materiel_necessaire", None),
        "materiel_utilise": getattr(intervention, "materiel_utilise", None),

        # Rapport
        "rapport": rapport_v2,

        # Documents & historique (structure prête, vide pour l'instant)
        "documents": [],
        "history": [],

        # Facturation
        "facturable": getattr(intervention, "facturable", True),
        "montant_ht": float(intervention.montant_ht) if getattr(intervention, "montant_ht", None) else None,
        "montant_ttc": float(intervention.montant_ttc) if getattr(intervention, "montant_ttc", None) else None,
        "facture_id": _uid(intervention.facture_client_id),
        "facture_reference": None,

        # Référence externe
        "reference_externe": intervention.reference_externe,

        # Méta
        "created_at": _iso(intervention.created_at),
        "updated_at": _iso(intervention.updated_at),
        "created_by": _uid(intervention.created_by),
    }


def _serialize_donneur(donneur: DonneurOrdre) -> dict:
    """Sérialise un DonneurOrdre en dict v2 aligné sur le type TypeScript."""
    return {
        "id": str(donneur.id),
        "nom": donneur.nom,
        "email": donneur.email,
        "telephone": donneur.telephone,
        "entreprise": getattr(donneur, "adresse", None),
        "is_active": donneur.is_active,
    }


# ============================================================================
# DONNEURS D'ORDRE
# ============================================================================

@router.get(
    "/donneurs-ordre",
    summary="Lister les donneurs d'ordre (v2)",
)
async def list_donneurs_ordre(
    active_only: bool = True,
    service: InterventionsService = Depends(_get_service),
):
    """Liste tous les donneurs d'ordre du tenant."""
    donneurs = service.list_donneurs_ordre(active_only=active_only)
    return [_serialize_donneur(d) for d in donneurs]


@router.get(
    "/donneurs-ordre/{donneur_id}",
    summary="Récupérer un donneur d'ordre (v2)",
)
async def get_donneur_ordre(
    donneur_id: UUID,
    service: InterventionsService = Depends(_get_service),
):
    """Récupère un donneur d'ordre par ID."""
    donneur = service.get_donneur_ordre(donneur_id)
    if not donneur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donneur d'ordre non trouvé",
        )
    return _serialize_donneur(donneur)


@router.post(
    "/donneurs-ordre",
    status_code=status.HTTP_201_CREATED,
    summary="Créer un donneur d'ordre (v2)",
)
async def create_donneur_ordre(
    data: DonneurOrdreCreate,
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """Crée un donneur d'ordre. Accès écriture requis."""
    _require_write_access(context)
    donneur = service.create_donneur_ordre(data)
    return _serialize_donneur(donneur)


@router.put(
    "/donneurs-ordre/{donneur_id}",
    summary="Mettre à jour un donneur d'ordre (v2)",
)
async def update_donneur_ordre(
    donneur_id: UUID,
    data: DonneurOrdreUpdate,
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """Met à jour un donneur d'ordre. Accès écriture requis."""
    _require_write_access(context)
    donneur = service.update_donneur_ordre(donneur_id, data)
    if not donneur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donneur d'ordre non trouvé",
        )
    return _serialize_donneur(donneur)


# ============================================================================
# STATISTIQUES (AVANT /{id} pour éviter conflit de route)
# ============================================================================

@router.get(
    "/stats",
    summary="Statistiques interventions (v2)",
)
async def get_stats(
    service: InterventionsService = Depends(_get_service),
):
    """Retourne les statistiques enrichies pour le dashboard frontend."""
    return service.get_stats()


# ============================================================================
# RAPPORTS FINAUX (AVANT /{id} pour éviter conflit de route)
# ============================================================================

@router.get(
    "/rapports-finaux",
    summary="Lister les rapports finaux (v2)",
)
async def list_rapports_finaux(
    projet_id: UUID | None = None,
    donneur_ordre_id: UUID | None = None,
    service: InterventionsService = Depends(_get_service),
):
    """Liste les rapports finaux consolidés."""
    rapports = service.list_rapports_final(
        projet_id=projet_id,
        donneur_ordre_id=donneur_ordre_id,
    )
    return [RapportFinalResponse.model_validate(r) for r in rapports]


@router.get(
    "/rapports-finaux/{rapport_id}",
    summary="Récupérer un rapport final (v2)",
)
async def get_rapport_final(
    rapport_id: UUID,
    service: InterventionsService = Depends(_get_service),
):
    """Récupère un rapport final par ID."""
    rapport = service.get_rapport_final(rapport_id)
    if not rapport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rapport final non trouvé",
        )
    return RapportFinalResponse.model_validate(rapport)


@router.post(
    "/rapports-finaux",
    status_code=status.HTTP_201_CREATED,
    summary="Générer un rapport final (v2)",
)
async def generer_rapport_final(
    data: RapportFinalGenerateRequest,
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """Génère un rapport final consolidé. Non modifiable une fois créé."""
    _require_write_access(context)
    try:
        rapport = service.generer_rapport_final(data, created_by=context.user_id)
        return RapportFinalResponse.model_validate(rapport)
    except InterventionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================================
# INTERVENTION PAR RÉFÉRENCE (AVANT /{id})
# ============================================================================

@router.get(
    "/ref/{reference}",
    summary="Intervention par référence (v2)",
)
async def get_intervention_by_reference(
    reference: str,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """Récupère une intervention par sa référence officielle (INT-YYYY-XXXX)."""
    intervention = service.get_intervention_by_reference(reference)
    if not intervention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intervention non trouvée",
        )
    return _serialize_intervention(intervention, db, context.tenant_id)


# ============================================================================
# INTERVENTIONS — CRUD
# ============================================================================

@router.get(
    "",
    summary="Lister les interventions (v2)",
)
async def list_interventions(
    statut: str | None = None,
    type_intervention: str | None = None,
    priorite: str | None = None,
    client_id: UUID | None = None,
    donneur_ordre_id: UUID | None = None,
    projet_id: UUID | None = None,
    intervenant_id: UUID | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """
    Liste les interventions avec filtres et pagination.

    Le frontend envoie les filtres en string (pas en enum).
    Retourne { items: [...], total: N }.
    """
    # Convertir strings en enums
    statut_enum = None
    if statut:
        try:
            statut_enum = InterventionStatut(statut)
        except ValueError:
            pass

    priorite_enum = None
    if priorite:
        try:
            priorite_enum = InterventionPriorite(priorite)
        except ValueError:
            pass

    items, total = service.list_interventions(
        statut=statut_enum,
        priorite=priorite_enum,
        client_id=client_id,
        donneur_ordre_id=donneur_ordre_id,
        projet_id=projet_id,
        intervenant_id=intervenant_id,
        search=search,
        page=page,
        page_size=page_size,
    )

    serialized = [_serialize_intervention(i, db, context.tenant_id) for i in items]
    return {"items": serialized, "total": total}


@router.get(
    "/{intervention_id}",
    summary="Détail intervention (v2)",
)
async def get_intervention(
    intervention_id: UUID,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """Récupère une intervention par ID avec données enrichies."""
    intervention = service.get_intervention(intervention_id)
    if not intervention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intervention non trouvée",
        )
    return _serialize_intervention(intervention, db, context.tenant_id)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Créer une intervention (v2)",
)
async def create_intervention(
    data: InterventionCreate,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """
    Crée une nouvelle intervention.

    Référence INT-YYYY-XXXX générée automatiquement.
    Statut initial : A_PLANIFIER.
    L'adresse est auto-remplie depuis le client si non fournie.
    """
    _require_write_access(context)

    # Auto-remplir l'adresse depuis le client si aucune adresse fournie (AZA-NF-003)
    if not data.adresse_ligne1:
        resolver = _get_resolver(db, context.tenant_id)
        client_addr = resolver.resolve_client_address(data.client_id)
        if client_addr:
            data.adresse_ligne1 = client_addr.get("adresse_ligne1")
            data.adresse_ligne2 = client_addr.get("adresse_ligne2")
            data.ville = client_addr.get("ville")
            data.code_postal = client_addr.get("code_postal")

    intervention = service.create_intervention(data, created_by=context.user_id)
    return _serialize_intervention(intervention, db, context.tenant_id)


@router.put(
    "/{intervention_id}",
    summary="Mettre à jour une intervention (v2)",
)
async def update_intervention(
    intervention_id: UUID,
    data: InterventionUpdate,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """
    Met à jour une intervention.

    La référence est JAMAIS modifiable.
    Le statut ne change que via les actions dédiées.
    """
    _require_write_access(context)
    try:
        intervention = service.update_intervention(intervention_id, data)
    except InterventionWorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    if not intervention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intervention non trouvée",
        )
    return _serialize_intervention(intervention, db, context.tenant_id)


@router.delete(
    "/{intervention_id}",
    status_code=status.HTTP_200_OK,
    summary="Supprimer une intervention (v2)",
)
async def delete_intervention(
    intervention_id: UUID,
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """Supprime une intervention (soft delete). Accès administrateur requis."""
    _require_admin_access(context)
    try:
        if not service.delete_intervention(intervention_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Intervention non trouvée",
            )
        return {"success": True}
    except InterventionWorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# PLANIFICATION
# ============================================================================

@router.post(
    "/{intervention_id}/planifier",
    summary="Planifier une intervention (v2)",
)
async def planifier_intervention(
    intervention_id: UUID,
    data: InterventionPlanifier,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """Planifie une intervention. Transition: A_PLANIFIER -> PLANIFIEE."""
    _require_write_access(context)
    try:
        intervention = service.planifier_intervention(intervention_id, data)
        return _serialize_intervention(intervention, db, context.tenant_id)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InterventionWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/{intervention_id}/planification",
    summary="Modifier la planification (v2)",
)
async def modifier_planification(
    intervention_id: UUID,
    data: InterventionPlanifier,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """Modifie la planification d'une intervention PLANIFIEE."""
    _require_write_access(context)
    try:
        intervention = service.modifier_planification(intervention_id, data)
        return _serialize_intervention(intervention, db, context.tenant_id)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InterventionWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{intervention_id}/planification",
    summary="Annuler la planification (v2)",
)
async def annuler_planification(
    intervention_id: UUID,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """Annule la planification. Transition: PLANIFIEE -> A_PLANIFIER."""
    _require_write_access(context)
    try:
        intervention = service.annuler_planification(intervention_id)
        return _serialize_intervention(intervention, db, context.tenant_id)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InterventionWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# ACTIONS TERRAIN
# ============================================================================

@router.post(
    "/{intervention_id}/arrivee",
    summary="Arrivée sur site (v2)",
)
async def arrivee_sur_site(
    intervention_id: UUID,
    data: ArriveeRequest = ArriveeRequest(),
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """Action terrain: arrivée sur site. Transition: PLANIFIEE -> EN_COURS."""
    try:
        intervention = service.arrivee_sur_site(intervention_id, data)
        return _serialize_intervention(intervention, db, context.tenant_id)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InterventionWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{intervention_id}/demarrer",
    summary="Démarrer l'intervention (v2)",
)
async def demarrer_intervention(
    intervention_id: UUID,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """Action terrain: démarrage effectif. Horodatage automatique."""
    try:
        intervention = service.demarrer_intervention(intervention_id)
        return _serialize_intervention(intervention, db, context.tenant_id)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InterventionWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{intervention_id}/terminer",
    summary="Terminer l'intervention (v2)",
)
async def terminer_intervention(
    intervention_id: UUID,
    data: FinInterventionRequest = FinInterventionRequest(),
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """
    Action terrain: fin d'intervention.

    Calcul automatique durée_reelle_minutes.
    Transition: EN_COURS -> TERMINEE.
    Génération automatique du rapport.
    """
    try:
        intervention = service.terminer_intervention(intervention_id, data)
        return _serialize_intervention(intervention, db, context.tenant_id)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InterventionWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{intervention_id}/annuler",
    summary="Annuler l'intervention (v2)",
)
async def annuler_intervention(
    intervention_id: UUID,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """
    Annule une intervention.

    Transition: tout sauf TERMINEE/ANNULEE -> ANNULEE.
    Traçable et auditable. Accès administrateur requis.
    """
    _require_admin_access(context)
    try:
        intervention = service.annuler_intervention(intervention_id)
        return _serialize_intervention(intervention, db, context.tenant_id)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InterventionWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# ACTIONS MÉTIER — VALIDATION, BLOCAGE, DÉBLOCAGE, ANALYSE IA
# ============================================================================

@router.post(
    "/{intervention_id}/valider",
    summary="Valider un brouillon (v2)",
)
async def valider_intervention(
    intervention_id: UUID,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """
    Valide un brouillon. Transition: DRAFT -> A_PLANIFIER.

    Vérifie les champs obligatoires (client_id, titre).
    """
    _require_write_access(context)
    try:
        intervention = service.valider_intervention(intervention_id)
        return _serialize_intervention(intervention, db, context.tenant_id)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InterventionWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{intervention_id}/bloquer",
    summary="Bloquer une intervention (v2)",
)
async def bloquer_intervention(
    intervention_id: UUID,
    data: BlocageRequest,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """
    Bloque une intervention en cours. Transition: EN_COURS -> BLOQUEE.

    Motif obligatoire (audit-proof).
    """
    _require_write_access(context)
    try:
        intervention = service.bloquer_intervention(intervention_id, data.motif)
        return _serialize_intervention(intervention, db, context.tenant_id)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InterventionWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{intervention_id}/debloquer",
    summary="Débloquer une intervention (v2)",
)
async def debloquer_intervention(
    intervention_id: UUID,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """
    Débloque une intervention bloquée. Transition: BLOQUEE -> EN_COURS.
    """
    _require_write_access(context)
    try:
        intervention = service.debloquer_intervention(intervention_id)
        return _serialize_intervention(intervention, db, context.tenant_id)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InterventionWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{intervention_id}/analyse-ia",
    summary="Analyse IA intervention (v2)",
)
async def analyse_ia_intervention(
    intervention_id: UUID,
    service: InterventionsService = Depends(_get_service),
):
    """
    Analyse IA audit-proof de l'intervention.

    Retourne indicateurs métier, score de préparation, actions suggérées,
    et justification explicite du niveau de risque.
    """
    try:
        return service.analyser_ia(intervention_id)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# RAPPORTS D'INTERVENTION
# ============================================================================

@router.get(
    "/{intervention_id}/rapport",
    summary="Rapport intervention (v2)",
)
async def get_rapport_intervention(
    intervention_id: UUID,
    service: InterventionsService = Depends(_get_service),
):
    """Récupère le rapport d'une intervention terminée."""
    rapport = service.get_rapport_intervention(intervention_id)
    if not rapport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rapport non trouvé",
        )
    return _build_rapport_v2(rapport)


@router.put(
    "/{intervention_id}/rapport",
    summary="Mettre à jour le rapport (v2)",
)
async def update_rapport_intervention(
    intervention_id: UUID,
    data: RapportInterventionUpdate,
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """Met à jour le rapport. Impossible si signé/verrouillé."""
    _require_write_access(context)
    try:
        rapport = service.update_rapport_intervention(intervention_id, data)
        return _build_rapport_v2(rapport)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RapportLockedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{intervention_id}/rapport/photos",
    summary="Ajouter photo au rapport (v2)",
)
async def ajouter_photo_rapport(
    intervention_id: UUID,
    photo: PhotoRequest,
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """Ajoute une photo au rapport d'intervention."""
    try:
        rapport = service.ajouter_photo_rapport(intervention_id, photo)
        return _build_rapport_v2(rapport)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RapportLockedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{intervention_id}/rapport/signer",
    summary="Signer le rapport (v2)",
)
async def signer_rapport(
    intervention_id: UUID,
    data: SignatureRapportRequest,
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_saas_context),
):
    """Signe le rapport d'intervention. Après signature, le rapport est figé."""
    try:
        rapport = service.signer_rapport(intervention_id, data)
        return _build_rapport_v2(rapport)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RapportLockedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
