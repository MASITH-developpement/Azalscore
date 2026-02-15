"""
AZALS MODULE INTERVENTIONS - Router Unifié
===========================================
Router unifié compatible v1/v2 avec get_context().
Migration: Remplace router.py et router_v2.py.

Endpoints alignés sur le frontend React/TypeScript avec:
- Réponses enrichies (client_name, donneur_ordre_name, intervenant_name)
- Rapport intégré dans la réponse intervention
- Statistiques enrichies
- Format de réponse { items: [...], total: N }
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db
from app.core.entity_resolver import EntityResolver

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

router = APIRouter(prefix="/interventions", tags=["Interventions - Gestion Terrain"])

# ============================================================================
# SERVICE FACTORY
# ============================================================================

def _get_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context),
) -> InterventionsService:
    """Factory service avec SaaSContext unifié."""
    return InterventionsService(
        db=db,
        tenant_id=context.tenant_id,
        user_id=str(context.user_id),
    )

# ============================================================================
# HELPERS — SERIALISATION
# ============================================================================

def _require_write_access(context: SaaSContext) -> None:
    """Vérifie que l'utilisateur a les droits d'écriture."""
    if context.role.value in ("EMPLOYE",):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès en écriture refusé. Rôle EMPLOYE : lecture seule.",
        )

def _require_admin_access(context: SaaSContext) -> None:
    """Vérifie que l'utilisateur a les droits d'administration."""
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
    """Construit un EntityResolver pour la résolution cross-modules."""
    return EntityResolver(db=db, tenant_id=tenant_id)

def _build_rapport_v2(rapport) -> dict | None:
    """Transforme un RapportIntervention en dict v2."""
    if rapport is None:
        return None

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
    """Sérialise une Intervention en dict aligné sur le type TypeScript."""
    resolver = _get_resolver(db, tenant_id)
    client_name, client_code = resolver.resolve_client(intervention.client_id)
    intervenant_name = resolver.resolve_employee(intervention.intervenant_id)
    donneur_name = intervention.donneur_ordre.nom if intervention.donneur_ordre else None

    rapport_v2 = _build_rapport_v2(intervention.rapport)

    duree_prevue = getattr(intervention, "duree_prevue_minutes", None)
    if duree_prevue is None and intervention.date_prevue_debut and intervention.date_prevue_fin:
        delta = (intervention.date_prevue_fin - intervention.date_prevue_debut).total_seconds()
        duree_prevue = int(delta / 60) if delta > 0 else None

    return {
        "id": str(intervention.id),
        "reference": intervention.reference,
        "client_id": str(intervention.client_id),
        "client_name": client_name,
        "client_code": client_code,
        "donneur_ordre_id": _uid(intervention.donneur_ordre_id),
        "donneur_ordre_name": donneur_name,
        "projet_id": _uid(intervention.projet_id),
        "projet_name": None,
        "affaire_id": _uid(getattr(intervention, "affaire_id", None)),
        "affaire_reference": None,
        "type_intervention": intervention.type_intervention.value if intervention.type_intervention else "AUTRE",
        "priorite": intervention.priorite.value if intervention.priorite else "NORMAL",
        "corps_etat": intervention.corps_etat.value if intervention.corps_etat else None,
        "titre": intervention.titre,
        "description": intervention.description,
        "date_prevue": _iso(intervention.date_prevue_debut),
        "heure_prevue": (
            intervention.date_prevue_debut.strftime("%H:%M")
            if intervention.date_prevue_debut else None
        ),
        "date_prevue_debut": _iso(intervention.date_prevue_debut),
        "date_prevue_fin": _iso(intervention.date_prevue_fin),
        "duree_prevue_minutes": duree_prevue,
        "intervenant_id": _uid(intervention.intervenant_id),
        "intervenant_name": intervenant_name,
        "equipe": [],
        "statut": intervention.statut.value,
        "motif_blocage": getattr(intervention, "motif_blocage", None),
        "date_blocage": _iso(getattr(intervention, "date_blocage", None)),
        "date_deblocage": _iso(getattr(intervention, "date_deblocage", None)),
        "date_debut_reelle": _iso(intervention.date_demarrage),
        "date_fin_reelle": _iso(intervention.date_fin),
        "duree_reelle_minutes": intervention.duree_reelle_minutes,
        "adresse_intervention": _build_address(intervention),
        "adresse_ligne1": intervention.adresse_ligne1,
        "adresse_ligne2": intervention.adresse_ligne2,
        "ville": intervention.ville,
        "code_postal": intervention.code_postal,
        "contact_sur_place": getattr(intervention, "contact_sur_place", None),
        "telephone_contact": getattr(intervention, "telephone_contact", None),
        "email_contact": getattr(intervention, "email_contact", None),
        "notes_internes": intervention.notes_internes,
        "notes_client": getattr(intervention, "notes_client", None),
        "materiel_necessaire": getattr(intervention, "materiel_necessaire", None),
        "materiel_utilise": getattr(intervention, "materiel_utilise", None),
        "rapport": rapport_v2,
        "documents": [],
        "history": [],
        "facturable": getattr(intervention, "facturable", True),
        "montant_ht": float(intervention.montant_ht) if getattr(intervention, "montant_ht", None) else None,
        "montant_ttc": float(intervention.montant_ttc) if getattr(intervention, "montant_ttc", None) else None,
        "facture_id": _uid(intervention.facture_client_id),
        "facture_reference": None,
        "reference_externe": intervention.reference_externe,
        "created_at": _iso(intervention.created_at),
        "updated_at": _iso(intervention.updated_at),
        "created_by": _uid(intervention.created_by),
    }

def _serialize_donneur(donneur: DonneurOrdre) -> dict:
    """Sérialise un DonneurOrdre en dict."""
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

@router.get("/donneurs-ordre", summary="Lister les donneurs d'ordre")
async def list_donneurs_ordre(
    active_only: bool = True,
    service: InterventionsService = Depends(_get_service),
):
    """Liste tous les donneurs d'ordre du tenant."""
    donneurs = service.list_donneurs_ordre(active_only=active_only)
    return [_serialize_donneur(d) for d in donneurs]

@router.get("/donneurs-ordre/{donneur_id}", summary="Récupérer un donneur d'ordre")
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
    summary="Créer un donneur d'ordre",
)
async def create_donneur_ordre(
    data: DonneurOrdreCreate,
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
):
    """Crée un donneur d'ordre. Accès écriture requis."""
    _require_write_access(context)
    donneur = service.create_donneur_ordre(data)
    return _serialize_donneur(donneur)

@router.put("/donneurs-ordre/{donneur_id}", summary="Mettre à jour un donneur d'ordre")
async def update_donneur_ordre(
    donneur_id: UUID,
    data: DonneurOrdreUpdate,
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
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

@router.delete("/donneurs-ordre/{donneur_id}", summary="Supprimer un donneur d'ordre")
async def delete_donneur_ordre(
    donneur_id: UUID,
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
):
    """Supprime un donneur d'ordre. Accès écriture requis."""
    _require_write_access(context)
    success = service.delete_donneur_ordre(donneur_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donneur d'ordre non trouvé",
        )
    return {"message": "Donneur d'ordre supprimé"}

# ============================================================================
# STATISTIQUES
# ============================================================================

@router.get("/stats", summary="Statistiques interventions")
async def get_stats(
    service: InterventionsService = Depends(_get_service),
):
    """Retourne les statistiques enrichies pour le dashboard frontend."""
    return service.get_stats()

# ============================================================================
# RAPPORTS FINAUX
# ============================================================================

@router.get("/rapports-finaux", summary="Lister les rapports finaux")
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

@router.get("/rapports-finaux/{rapport_id}", summary="Récupérer un rapport final")
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
    summary="Générer un rapport final",
)
async def generer_rapport_final(
    data: RapportFinalGenerateRequest,
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
):
    """Génère un rapport final consolidé."""
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
# INTERVENTION PAR RÉFÉRENCE
# ============================================================================

@router.get("/ref/{reference}", summary="Intervention par référence")
async def get_intervention_by_reference(
    reference: str,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
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

@router.get("", summary="Lister les interventions")
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
    context: SaaSContext = Depends(get_context),
):
    """Liste les interventions avec filtres et pagination."""
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

@router.get("/{intervention_id}", summary="Détail intervention")
async def get_intervention(
    intervention_id: UUID,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
):
    """Récupère une intervention par ID avec données enrichies."""
    intervention = service.get_intervention(intervention_id)
    if not intervention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intervention non trouvée",
        )
    return _serialize_intervention(intervention, db, context.tenant_id)

@router.post("", status_code=status.HTTP_201_CREATED, summary="Créer une intervention")
async def create_intervention(
    data: InterventionCreate,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
):
    """Crée une nouvelle intervention."""
    _require_write_access(context)

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

@router.put("/{intervention_id}", summary="Mettre à jour une intervention")
async def update_intervention(
    intervention_id: UUID,
    data: InterventionUpdate,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
):
    """Met à jour une intervention."""
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
    summary="Supprimer une intervention",
)
async def delete_intervention(
    intervention_id: UUID,
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
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

@router.post("/{intervention_id}/planifier", summary="Planifier une intervention")
async def planifier_intervention(
    intervention_id: UUID,
    data: InterventionPlanifier,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
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

@router.put("/{intervention_id}/planification", summary="Modifier la planification")
async def modifier_planification(
    intervention_id: UUID,
    data: InterventionPlanifier,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
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

@router.delete("/{intervention_id}/planification", summary="Annuler la planification")
async def annuler_planification(
    intervention_id: UUID,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
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

@router.post("/{intervention_id}/arrivee", summary="Arrivée sur site")
async def arrivee_sur_site(
    intervention_id: UUID,
    data: ArriveeRequest = ArriveeRequest(),
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
):
    """Action terrain: arrivée sur site. Transition: PLANIFIEE -> EN_COURS."""
    try:
        intervention = service.arrivee_sur_site(intervention_id, data)
        return _serialize_intervention(intervention, db, context.tenant_id)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InterventionWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{intervention_id}/demarrer", summary="Démarrer l'intervention")
async def demarrer_intervention(
    intervention_id: UUID,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
):
    """Action terrain: démarrage effectif. Horodatage automatique."""
    try:
        intervention = service.demarrer_intervention(intervention_id)
        return _serialize_intervention(intervention, db, context.tenant_id)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InterventionWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{intervention_id}/terminer", summary="Terminer l'intervention")
async def terminer_intervention(
    intervention_id: UUID,
    data: FinInterventionRequest = FinInterventionRequest(),
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
):
    """Action terrain: fin d'intervention."""
    try:
        intervention = service.terminer_intervention(intervention_id, data)
        return _serialize_intervention(intervention, db, context.tenant_id)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InterventionWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{intervention_id}/annuler", summary="Annuler l'intervention")
async def annuler_intervention(
    intervention_id: UUID,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
):
    """Annule une intervention. Accès administrateur requis."""
    _require_admin_access(context)
    try:
        intervention = service.annuler_intervention(intervention_id)
        return _serialize_intervention(intervention, db, context.tenant_id)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InterventionWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# ============================================================================
# ACTIONS MÉTIER
# ============================================================================

@router.post("/{intervention_id}/valider", summary="Valider un brouillon")
async def valider_intervention(
    intervention_id: UUID,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
):
    """Valide un brouillon. Transition: DRAFT -> A_PLANIFIER."""
    _require_write_access(context)
    try:
        intervention = service.valider_intervention(intervention_id)
        return _serialize_intervention(intervention, db, context.tenant_id)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InterventionWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{intervention_id}/bloquer", summary="Bloquer une intervention")
async def bloquer_intervention(
    intervention_id: UUID,
    data: BlocageRequest,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
):
    """Bloque une intervention en cours. Transition: EN_COURS -> BLOQUEE."""
    _require_write_access(context)
    try:
        intervention = service.bloquer_intervention(intervention_id, data.motif)
        return _serialize_intervention(intervention, db, context.tenant_id)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InterventionWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{intervention_id}/debloquer", summary="Débloquer une intervention")
async def debloquer_intervention(
    intervention_id: UUID,
    db: Session = Depends(get_db),
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
):
    """Débloque une intervention bloquée. Transition: BLOQUEE -> EN_COURS."""
    _require_write_access(context)
    try:
        intervention = service.debloquer_intervention(intervention_id)
        return _serialize_intervention(intervention, db, context.tenant_id)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InterventionWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{intervention_id}/analyse-ia", summary="Analyse IA intervention")
async def analyse_ia_intervention(
    intervention_id: UUID,
    service: InterventionsService = Depends(_get_service),
):
    """Analyse IA audit-proof de l'intervention."""
    try:
        return service.analyser_ia(intervention_id)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# ============================================================================
# RAPPORTS D'INTERVENTION
# ============================================================================

@router.get("/{intervention_id}/rapport", summary="Rapport intervention")
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

@router.put("/{intervention_id}/rapport", summary="Mettre à jour le rapport")
async def update_rapport_intervention(
    intervention_id: UUID,
    data: RapportInterventionUpdate,
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
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

@router.post("/{intervention_id}/rapport/photos", summary="Ajouter photo au rapport")
async def ajouter_photo_rapport(
    intervention_id: UUID,
    photo: PhotoRequest,
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
):
    """Ajoute une photo au rapport d'intervention."""
    try:
        rapport = service.ajouter_photo_rapport(intervention_id, photo)
        return _build_rapport_v2(rapport)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RapportLockedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{intervention_id}/rapport/signer", summary="Signer le rapport")
async def signer_rapport(
    intervention_id: UUID,
    data: SignatureRapportRequest,
    service: InterventionsService = Depends(_get_service),
    context: SaaSContext = Depends(get_context),
):
    """Signe le rapport d'intervention. Après signature, le rapport est figé."""
    try:
        rapport = service.signer_rapport(intervention_id, data)
        return _build_rapport_v2(rapport)
    except InterventionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RapportLockedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
