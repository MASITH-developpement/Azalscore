"""
AZALS MODULE INTERVENTIONS - Router
====================================

API endpoints pour le module Interventions v1.

RBAC appliqué:
- Intervenant: actions terrain uniquement
- Manager: création, planification, clôture
- Admin: tout
- Lecture seule: consultation uniquement
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_tenant_id, get_current_user

from .models import InterventionStatut, InterventionPriorite
from .schemas import (
    # Donneur d'ordre
    DonneurOrdreCreate,
    DonneurOrdreUpdate,
    DonneurOrdreResponse,
    # Intervention
    InterventionCreate,
    InterventionUpdate,
    InterventionPlanifier,
    InterventionResponse,
    InterventionListResponse,
    # Actions terrain
    ArriveeRequest,
    DemarrageRequest,
    FinInterventionRequest,
    SignatureRapportRequest,
    PhotoRequest,
    # Rapports
    RapportInterventionUpdate,
    RapportInterventionResponse,
    RapportFinalResponse,
    RapportFinalGenerateRequest,
    # Stats
    InterventionStats,
)
from .service import (
    InterventionsService,
    InterventionWorkflowError,
    InterventionNotFoundError,
    RapportLockedError,
)


router = APIRouter(prefix="/api/v1/interventions", tags=["M-INT - Interventions"])


# ============================================================================
# RBAC HELPERS
# ============================================================================

class RBACRoles:
    """Rôles RBAC pour le module Interventions."""
    ADMIN = "admin"
    MANAGER = "manager"
    INTERVENANT = "intervenant"
    READONLY = "readonly"


def require_role(*allowed_roles):
    """
    Décorateur de vérification de rôle.

    Usage:
        @require_role(RBACRoles.ADMIN, RBACRoles.MANAGER)
    """
    def check_role(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", RBACRoles.READONLY)

        # Admin a tous les droits
        if user_role == RBACRoles.ADMIN:
            return current_user

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès refusé. Rôles autorisés: {', '.join(allowed_roles)}"
            )
        return current_user
    return check_role


def get_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
) -> InterventionsService:
    """Factory service avec tenant."""
    return InterventionsService(db, tenant_id)


# ============================================================================
# DONNEURS D'ORDRE
# ============================================================================

@router.get(
    "/donneurs-ordre",
    response_model=List[DonneurOrdreResponse],
    summary="Lister les donneurs d'ordre",
    description="Liste tous les donneurs d'ordre du tenant."
)
async def list_donneurs_ordre(
    active_only: bool = True,
    service: InterventionsService = Depends(get_service),
    _user: dict = Depends(get_current_user)
):
    """Liste des donneurs d'ordre. Accessible à tous les rôles authentifiés."""
    return service.list_donneurs_ordre(active_only)


@router.get(
    "/donneurs-ordre/{donneur_id}",
    response_model=DonneurOrdreResponse,
    summary="Récupérer un donneur d'ordre"
)
async def get_donneur_ordre(
    donneur_id: UUID,
    service: InterventionsService = Depends(get_service),
    _user: dict = Depends(get_current_user)
):
    """Récupère un donneur d'ordre par ID."""
    donneur = service.get_donneur_ordre(donneur_id)
    if not donneur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donneur d'ordre non trouvé"
        )
    return donneur


@router.post(
    "/donneurs-ordre",
    response_model=DonneurOrdreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un donneur d'ordre"
)
async def create_donneur_ordre(
    data: DonneurOrdreCreate,
    service: InterventionsService = Depends(get_service),
    current_user: dict = Depends(require_role(RBACRoles.ADMIN, RBACRoles.MANAGER))
):
    """Crée un donneur d'ordre. Réservé aux managers et admins."""
    return service.create_donneur_ordre(data)


@router.put(
    "/donneurs-ordre/{donneur_id}",
    response_model=DonneurOrdreResponse,
    summary="Mettre à jour un donneur d'ordre"
)
async def update_donneur_ordre(
    donneur_id: UUID,
    data: DonneurOrdreUpdate,
    service: InterventionsService = Depends(get_service),
    current_user: dict = Depends(require_role(RBACRoles.ADMIN, RBACRoles.MANAGER))
):
    """Met à jour un donneur d'ordre. Réservé aux managers et admins."""
    donneur = service.update_donneur_ordre(donneur_id, data)
    if not donneur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donneur d'ordre non trouvé"
        )
    return donneur


# ============================================================================
# INTERVENTIONS - CRUD
# ============================================================================

@router.get(
    "",
    response_model=InterventionListResponse,
    summary="Lister les interventions"
)
async def list_interventions(
    statut: Optional[InterventionStatut] = None,
    priorite: Optional[InterventionPriorite] = None,
    client_id: Optional[UUID] = None,
    donneur_ordre_id: Optional[UUID] = None,
    projet_id: Optional[UUID] = None,
    intervenant_id: Optional[UUID] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: InterventionsService = Depends(get_service),
    _user: dict = Depends(get_current_user)
):
    """Liste les interventions avec filtres et pagination."""
    items, total = service.list_interventions(
        statut=statut,
        priorite=priorite,
        client_id=client_id,
        donneur_ordre_id=donneur_ordre_id,
        projet_id=projet_id,
        intervenant_id=intervenant_id,
        date_from=date_from,
        date_to=date_to,
        search=search,
        page=page,
        page_size=page_size
    )
    return InterventionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/{intervention_id}",
    response_model=InterventionResponse,
    summary="Récupérer une intervention"
)
async def get_intervention(
    intervention_id: UUID,
    service: InterventionsService = Depends(get_service),
    _user: dict = Depends(get_current_user)
):
    """Récupère une intervention par ID."""
    intervention = service.get_intervention(intervention_id)
    if not intervention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intervention non trouvée"
        )
    return intervention


@router.get(
    "/ref/{reference}",
    response_model=InterventionResponse,
    summary="Récupérer une intervention par référence"
)
async def get_intervention_by_reference(
    reference: str,
    service: InterventionsService = Depends(get_service),
    _user: dict = Depends(get_current_user)
):
    """Récupère une intervention par sa référence officielle (INT-YYYY-XXXX)."""
    intervention = service.get_intervention_by_reference(reference)
    if not intervention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intervention non trouvée"
        )
    return intervention


@router.post(
    "",
    response_model=InterventionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une intervention"
)
async def create_intervention(
    data: InterventionCreate,
    service: InterventionsService = Depends(get_service),
    current_user: dict = Depends(require_role(RBACRoles.ADMIN, RBACRoles.MANAGER))
):
    """
    Crée une nouvelle intervention.

    La référence INT-YYYY-XXXX est générée automatiquement.
    Réservé aux managers et admins.
    """
    return service.create_intervention(
        data,
        created_by=current_user.get("user_id")
    )


@router.put(
    "/{intervention_id}",
    response_model=InterventionResponse,
    summary="Mettre à jour une intervention"
)
async def update_intervention(
    intervention_id: UUID,
    data: InterventionUpdate,
    service: InterventionsService = Depends(get_service),
    current_user: dict = Depends(require_role(RBACRoles.ADMIN, RBACRoles.MANAGER))
):
    """
    Met à jour une intervention.

    ATTENTION: La référence n'est JAMAIS modifiable.
    Réservé aux managers et admins.
    """
    intervention = service.update_intervention(intervention_id, data)
    if not intervention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intervention non trouvée"
        )
    return intervention


@router.delete(
    "/{intervention_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une intervention"
)
async def delete_intervention(
    intervention_id: UUID,
    service: InterventionsService = Depends(get_service),
    current_user: dict = Depends(require_role(RBACRoles.ADMIN))
):
    """Supprime une intervention (soft delete). Réservé aux admins."""
    try:
        if not service.delete_intervention(intervention_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Intervention non trouvée"
            )
    except InterventionWorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# PLANIFICATION
# ============================================================================

@router.post(
    "/{intervention_id}/planifier",
    response_model=InterventionResponse,
    summary="Planifier une intervention"
)
async def planifier_intervention(
    intervention_id: UUID,
    data: InterventionPlanifier,
    service: InterventionsService = Depends(get_service),
    current_user: dict = Depends(require_role(RBACRoles.ADMIN, RBACRoles.MANAGER))
):
    """
    Planifie une intervention.

    Transition: A_PLANIFIER -> PLANIFIEE
    Crée un événement dans le module Planning.
    Réservé aux managers et admins.
    """
    try:
        return service.planifier_intervention(intervention_id, data)
    except InterventionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InterventionWorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{intervention_id}/planification",
    response_model=InterventionResponse,
    summary="Modifier la planification"
)
async def modifier_planification(
    intervention_id: UUID,
    data: InterventionPlanifier,
    service: InterventionsService = Depends(get_service),
    current_user: dict = Depends(require_role(RBACRoles.ADMIN, RBACRoles.MANAGER))
):
    """Modifie la planification d'une intervention PLANIFIEE."""
    try:
        return service.modifier_planification(intervention_id, data)
    except InterventionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InterventionWorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{intervention_id}/planification",
    response_model=InterventionResponse,
    summary="Annuler la planification"
)
async def annuler_planification(
    intervention_id: UUID,
    service: InterventionsService = Depends(get_service),
    current_user: dict = Depends(require_role(RBACRoles.ADMIN, RBACRoles.MANAGER))
):
    """
    Annule la planification d'une intervention.

    Transition: PLANIFIEE -> A_PLANIFIER
    Supprime l'événement Planning.
    """
    try:
        return service.annuler_planification(intervention_id)
    except InterventionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InterventionWorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# ACTIONS TERRAIN
# ============================================================================

@router.post(
    "/{intervention_id}/arrivee",
    response_model=InterventionResponse,
    summary="Signaler l'arrivée sur site"
)
async def arrivee_sur_site(
    intervention_id: UUID,
    data: ArriveeRequest,
    service: InterventionsService = Depends(get_service),
    current_user: dict = Depends(require_role(
        RBACRoles.ADMIN, RBACRoles.MANAGER, RBACRoles.INTERVENANT
    ))
):
    """
    Action terrain: arrivee_sur_site()

    Horodatage automatique + géolocalisation.
    Transition: PLANIFIEE -> EN_COURS
    Accessible aux intervenants, managers et admins.
    """
    try:
        return service.arrivee_sur_site(intervention_id, data)
    except InterventionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InterventionWorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{intervention_id}/demarrer",
    response_model=InterventionResponse,
    summary="Démarrer l'intervention"
)
async def demarrer_intervention(
    intervention_id: UUID,
    service: InterventionsService = Depends(get_service),
    current_user: dict = Depends(require_role(
        RBACRoles.ADMIN, RBACRoles.MANAGER, RBACRoles.INTERVENANT
    ))
):
    """
    Action terrain: demarrer_intervention()

    Horodatage automatique du démarrage effectif.
    Accessible aux intervenants, managers et admins.
    """
    try:
        return service.demarrer_intervention(intervention_id)
    except InterventionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InterventionWorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{intervention_id}/terminer",
    response_model=InterventionResponse,
    summary="Terminer l'intervention"
)
async def terminer_intervention(
    intervention_id: UUID,
    data: FinInterventionRequest,
    service: InterventionsService = Depends(get_service),
    current_user: dict = Depends(require_role(
        RBACRoles.ADMIN, RBACRoles.MANAGER, RBACRoles.INTERVENANT
    ))
):
    """
    Action terrain: terminer_intervention()

    Horodatage automatique.
    Calcul automatique de la durée_reelle_minutes.
    Transition: EN_COURS -> TERMINEE
    Génération automatique du rapport d'intervention.
    """
    try:
        return service.terminer_intervention(intervention_id, data)
    except InterventionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InterventionWorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# RAPPORTS D'INTERVENTION
# ============================================================================

@router.get(
    "/{intervention_id}/rapport",
    response_model=RapportInterventionResponse,
    summary="Récupérer le rapport d'intervention"
)
async def get_rapport_intervention(
    intervention_id: UUID,
    service: InterventionsService = Depends(get_service),
    _user: dict = Depends(get_current_user)
):
    """Récupère le rapport d'une intervention terminée."""
    rapport = service.get_rapport_intervention(intervention_id)
    if not rapport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rapport non trouvé"
        )
    return rapport


@router.put(
    "/{intervention_id}/rapport",
    response_model=RapportInterventionResponse,
    summary="Mettre à jour le rapport"
)
async def update_rapport_intervention(
    intervention_id: UUID,
    data: RapportInterventionUpdate,
    service: InterventionsService = Depends(get_service),
    current_user: dict = Depends(require_role(
        RBACRoles.ADMIN, RBACRoles.MANAGER, RBACRoles.INTERVENANT
    ))
):
    """
    Met à jour le rapport d'intervention.

    IMPOSSIBLE si le rapport est signé ou verrouillé.
    """
    try:
        return service.update_rapport_intervention(intervention_id, data)
    except InterventionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RapportLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{intervention_id}/rapport/photos",
    response_model=RapportInterventionResponse,
    summary="Ajouter une photo au rapport"
)
async def ajouter_photo_rapport(
    intervention_id: UUID,
    photo: PhotoRequest,
    service: InterventionsService = Depends(get_service),
    current_user: dict = Depends(require_role(
        RBACRoles.ADMIN, RBACRoles.MANAGER, RBACRoles.INTERVENANT
    ))
):
    """Ajoute une photo au rapport d'intervention."""
    try:
        return service.ajouter_photo_rapport(intervention_id, photo)
    except InterventionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RapportLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{intervention_id}/rapport/signer",
    response_model=RapportInterventionResponse,
    summary="Signer le rapport"
)
async def signer_rapport(
    intervention_id: UUID,
    data: SignatureRapportRequest,
    service: InterventionsService = Depends(get_service),
    current_user: dict = Depends(require_role(
        RBACRoles.ADMIN, RBACRoles.MANAGER, RBACRoles.INTERVENANT
    ))
):
    """
    Signe le rapport d'intervention.

    Une fois signé, le rapport est figé et non modifiable.
    """
    try:
        return service.signer_rapport(intervention_id, data)
    except InterventionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RapportLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# RAPPORTS FINAUX
# ============================================================================

@router.get(
    "/rapports-finaux",
    response_model=List[RapportFinalResponse],
    summary="Lister les rapports finaux"
)
async def list_rapports_final(
    projet_id: Optional[UUID] = None,
    donneur_ordre_id: Optional[UUID] = None,
    service: InterventionsService = Depends(get_service),
    _user: dict = Depends(get_current_user)
):
    """Liste les rapports finaux consolidés."""
    return service.list_rapports_final(
        projet_id=projet_id,
        donneur_ordre_id=donneur_ordre_id
    )


@router.get(
    "/rapports-finaux/{rapport_id}",
    response_model=RapportFinalResponse,
    summary="Récupérer un rapport final"
)
async def get_rapport_final(
    rapport_id: UUID,
    service: InterventionsService = Depends(get_service),
    _user: dict = Depends(get_current_user)
):
    """Récupère un rapport final par ID."""
    rapport = service.get_rapport_final(rapport_id)
    if not rapport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rapport final non trouvé"
        )
    return rapport


@router.post(
    "/rapports-finaux",
    response_model=RapportFinalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Générer un rapport final"
)
async def generer_rapport_final(
    data: RapportFinalGenerateRequest,
    service: InterventionsService = Depends(get_service),
    current_user: dict = Depends(require_role(RBACRoles.ADMIN, RBACRoles.MANAGER))
):
    """
    Génère un rapport final consolidé.

    Regroupe les interventions terminées par projet ou donneur d'ordre.
    Le rapport final est non modifiable une fois généré.
    """
    try:
        return service.generer_rapport_final(
            data,
            created_by=current_user.get("user_id")
        )
    except InterventionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============================================================================
# STATISTIQUES
# ============================================================================

@router.get(
    "/stats",
    response_model=InterventionStats,
    summary="Statistiques des interventions"
)
async def get_stats(
    service: InterventionsService = Depends(get_service),
    _user: dict = Depends(get_current_user)
):
    """Retourne les statistiques des interventions."""
    return service.get_stats()
