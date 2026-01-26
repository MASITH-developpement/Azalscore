"""
AZALS MODULE INTERVENTIONS - Router API v2 (CORE SaaS)
========================================================

✅ MIGRÉ CORE SaaS Phase 2.2
- Utilise get_saas_context() au lieu de get_current_user()
- Isolation tenant automatique via context.tenant_id
- Audit trail automatique via context.user_id

API endpoints pour le module Interventions v2.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext

from .models import InterventionPriorite, InterventionStatut
from .schemas import (
    ArriveeRequest,
    DonneurOrdreCreate,
    DonneurOrdreResponse,
    DonneurOrdreUpdate,
    FinInterventionRequest,
    InterventionCreate,
    InterventionListResponse,
    InterventionPlanifier,
    InterventionResponse,
    InterventionStats,
    InterventionUpdate,
    PhotoRequest,
    RapportFinalGenerateRequest,
    RapportFinalResponse,
    RapportInterventionResponse,
    RapportInterventionUpdate,
    SignatureRapportRequest,
)
from .service import (
    InterventionNotFoundError,
    InterventionsService,
    InterventionWorkflowError,
    RapportLockedError,
)

router = APIRouter(prefix="/v2/interventions", tags=["Interventions v2 - CORE SaaS"])


# ============================================================================
# SERVICE DEPENDENCY v2
# ============================================================================

def get_interventions_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
) -> InterventionsService:
    """✅ MIGRÉ CORE SaaS: Utilise context.tenant_id et context.user_id"""
    return InterventionsService(db, context.tenant_id, context.user_id)


# ============================================================================
# DONNEURS D'ORDRE
# ============================================================================

@router.get(
    "/donneurs-ordre",
    response_model=list[DonneurOrdreResponse],
    summary="Lister les donneurs d'ordre"
)
async def list_donneurs_ordre(
    active_only: bool = True,
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Liste des donneurs d'ordre."""
    return service.list_donneurs_ordre(active_only)


@router.get(
    "/donneurs-ordre/{donneur_id}",
    response_model=DonneurOrdreResponse,
    summary="Récupérer un donneur d'ordre"
)
async def get_donneur_ordre(
    donneur_id: UUID,
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Récupère un donneur d'ordre par ID."""
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
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Crée un donneur d'ordre."""
    return service.create_donneur_ordre(data)


@router.put(
    "/donneurs-ordre/{donneur_id}",
    response_model=DonneurOrdreResponse,
    summary="Mettre à jour un donneur d'ordre"
)
async def update_donneur_ordre(
    donneur_id: UUID,
    data: DonneurOrdreUpdate,
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Met à jour un donneur d'ordre."""
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
    statut: InterventionStatut | None = None,
    priorite: InterventionPriorite | None = None,
    client_id: UUID | None = None,
    donneur_ordre_id: UUID | None = None,
    projet_id: UUID | None = None,
    intervenant_id: UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Liste les interventions avec filtres et pagination."""
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
    "/stats",
    response_model=InterventionStats,
    summary="Statistiques des interventions"
)
async def get_stats(
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Retourne les statistiques des interventions."""
    return service.get_stats()


@router.get(
    "/{intervention_id}",
    response_model=InterventionResponse,
    summary="Récupérer une intervention"
)
async def get_intervention(
    intervention_id: UUID,
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Récupère une intervention par ID."""
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
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Récupère une intervention par référence (INT-YYYY-XXXX)."""
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
    service: InterventionsService = Depends(get_interventions_service),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Crée une nouvelle intervention avec référence auto."""
    return service.create_intervention(
        data,
        created_by=context.user_id
    )


@router.put(
    "/{intervention_id}",
    response_model=InterventionResponse,
    summary="Mettre à jour une intervention"
)
async def update_intervention(
    intervention_id: UUID,
    data: InterventionUpdate,
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Met à jour une intervention (référence non modifiable)."""
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
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Supprime une intervention (soft delete)."""
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
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Planifie une intervention (A_PLANIFIER -> PLANIFIEE)."""
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
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Modifie la planification d'une intervention PLANIFIEE."""
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
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Annule la planification (PLANIFIEE -> A_PLANIFIER)."""
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
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Enregistre l'arrivée sur site (PLANIFIEE -> EN_COURS)."""
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
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Démarre l'intervention (horodatage automatique)."""
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
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Termine l'intervention (EN_COURS -> TERMINEE)."""
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
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Récupère le rapport d'une intervention terminée."""
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
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Met à jour le rapport (impossible si signé/verrouillé)."""
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
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Ajoute une photo au rapport d'intervention."""
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
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Signe le rapport (devient non modifiable)."""
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
    response_model=list[RapportFinalResponse],
    summary="Lister les rapports finaux"
)
async def list_rapports_final(
    projet_id: UUID | None = None,
    donneur_ordre_id: UUID | None = None,
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Liste les rapports finaux consolidés."""
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
    service: InterventionsService = Depends(get_interventions_service)
):
    """✅ MIGRÉ CORE SaaS: Récupère un rapport final par ID."""
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
    service: InterventionsService = Depends(get_interventions_service),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Génère un rapport final consolidé (non modifiable)."""
    try:
        return service.generer_rapport_final(
            data,
            created_by=context.user_id
        )
    except InterventionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
