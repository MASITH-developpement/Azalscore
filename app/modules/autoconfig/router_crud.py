"""
AZALS MODULE AUTOCONFIG - Router Unifié
========================================
Router unifié compatible v1/v2 via double enregistrement.
Utilise get_context() de app.core.compat pour l'isolation tenant.

Configuration automatique par fonction avec gestion des profils de poste.
"""
from __future__ import annotations


from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db

from .service import AutoConfigService
from .models import OverrideType

router = APIRouter(prefix="/autoconfig", tags=["AutoConfig"])

def get_autoconfig_service(db: Session, tenant_id: str, user_id: str) -> AutoConfigService:
    """Factory pour créer le service AutoConfig avec contexte SaaS."""
    return AutoConfigService(db, tenant_id, user_id)

# ============================================================================
# PROFILES (PROFILS DE POSTE)
# ============================================================================

@router.post("/profiles/initialize", status_code=201)
async def initialize_predefined_profiles(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Initialiser les profils prédéfinis pour le tenant."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    count = service.initialize_predefined_profiles(user_id)
    return {"profiles_created": count}

@router.get("/profiles")
async def list_profiles(
    include_inactive: bool = Query(False, description="Inclure profils inactifs"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister tous les profils de poste."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    return service.list_profiles(include_inactive)

@router.get("/profiles/code/{code}")
async def get_profile_by_code(
    code: str,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer un profil par code."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    profile = service.get_profile_by_code(code)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile '{code}' not found")
    return profile

@router.get("/profiles/{profile_id}")
async def get_profile(
    profile_id: int,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer un profil par ID."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    profile = service.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.post("/profiles/detect")
async def detect_profile(
    job_title: str = Query(..., description="Titre du poste"),
    department: str | None = Query(None, description="Département"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Détecter le profil approprié pour un titre/département."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    profile = service.detect_profile(job_title, department)
    if not profile:
        return {"detected": False, "profile": None}
    return {"detected": True, "profile": profile}

# ============================================================================
# ASSIGNMENTS (ATTRIBUTIONS)
# ============================================================================

@router.post("/assignments/auto", status_code=201)
async def auto_assign_profile(
    target_user_id: int = Query(..., description="ID de l'utilisateur cible"),
    job_title: str = Query(..., description="Titre du poste"),
    department: str | None = Query(None, description="Département"),
    manager_id: int | None = Query(None, description="ID du manager"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Attribuer automatiquement un profil à un utilisateur."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    assigned_by = int(context.user_id) if context.user_id else None

    assignment = service.auto_assign_profile(
        target_user_id, job_title, department, manager_id, assigned_by
    )

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="No suitable profile found for this job title/department"
        )

    return assignment

@router.post("/assignments/manual", status_code=201)
async def manual_assign_profile(
    target_user_id: int = Query(..., description="ID de l'utilisateur cible"),
    profile_code: str = Query(..., description="Code du profil"),
    job_title: str | None = Query(None, description="Titre du poste"),
    department: str | None = Query(None, description="Département"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Attribuer manuellement un profil à un utilisateur."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    assigned_by = int(context.user_id) if context.user_id else None
    if not assigned_by:
        raise HTTPException(status_code=401, detail="User ID required")

    try:
        return service.manual_assign_profile(
            target_user_id, profile_code, assigned_by, job_title, department
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/assignments/user/{user_id}")
async def get_user_profile(
    user_id: int,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer l'attribution de profil active d'un utilisateur."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    assignment = service.get_user_profile(user_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="No active profile assignment")
    return assignment

@router.get("/config/user/{user_id}")
async def get_user_effective_config(
    user_id: int,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer la configuration effective d'un utilisateur (profil + overrides)."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    return service.get_user_effective_config(user_id)

# ============================================================================
# OVERRIDES (SURCHARGES PERMISSIONS)
# ============================================================================

@router.post("/overrides", status_code=201)
async def request_override(
    target_user_id: int = Query(..., description="ID de l'utilisateur cible"),
    override_type: OverrideType = Query(..., description="Type d'override"),
    reason: str = Query(..., description="Raison de la demande"),
    added_roles: list[str] | None = None,
    removed_roles: list[str] | None = None,
    added_permissions: list[str] | None = None,
    removed_permissions: list[str] | None = None,
    added_modules: list[str] | None = None,
    removed_modules: list[str] | None = None,
    expires_at: datetime | None = None,
    business_justification: str | None = None,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Demander un override de permissions."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    requested_by = int(context.user_id) if context.user_id else None
    if not requested_by:
        raise HTTPException(status_code=401, detail="User ID required")

    return service.request_override(
        target_user_id, override_type, reason, requested_by,
        added_roles, removed_roles,
        added_permissions, removed_permissions,
        added_modules, removed_modules,
        expires_at, business_justification
    )

@router.get("/overrides/user/{user_id}")
async def list_user_overrides(
    user_id: int,
    include_inactive: bool = Query(False, description="Inclure overrides inactifs"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les overrides d'un utilisateur."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    return service.list_user_overrides(user_id, include_inactive)

@router.post("/overrides/{override_id}/approve")
async def approve_override(
    override_id: int,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Approuver un override en attente."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    approved_by = int(context.user_id) if context.user_id else None
    if not approved_by:
        raise HTTPException(status_code=401, detail="User ID required")

    try:
        return service.approve_override(override_id, approved_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/overrides/{override_id}/reject")
async def reject_override(
    override_id: int,
    rejection_reason: str = Query(..., description="Raison du rejet"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Rejeter un override en attente."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    rejected_by = int(context.user_id) if context.user_id else None
    if not rejected_by:
        raise HTTPException(status_code=401, detail="User ID required")

    try:
        return service.reject_override(override_id, rejected_by, rejection_reason)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/overrides/{override_id}/revoke")
async def revoke_override(
    override_id: int,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Révoquer un override actif."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    revoked_by = int(context.user_id) if context.user_id else None
    if not revoked_by:
        raise HTTPException(status_code=401, detail="User ID required")

    try:
        return service.revoke_override(override_id, revoked_by)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/overrides/expire")
async def expire_overrides(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Expirer les overrides dont la date est passée (tâche planifiée)."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    count = service.expire_overrides()
    return {"expired_count": count}

# ============================================================================
# ONBOARDING
# ============================================================================

@router.post("/onboarding", status_code=201)
async def create_onboarding(
    email: str = Query(..., description="Email du nouvel arrivant"),
    job_title: str = Query(..., description="Titre du poste"),
    start_date: datetime = Query(..., description="Date de début"),
    first_name: str | None = Query(None),
    last_name: str | None = Query(None),
    department: str | None = Query(None),
    manager_id: int | None = Query(None),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Créer un processus d'onboarding."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    created_by = int(context.user_id) if context.user_id else None

    return service.create_onboarding(
        email, job_title, start_date, created_by,
        first_name, last_name, department, manager_id
    )

@router.get("/onboarding/pending")
async def list_pending_onboardings(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les onboardings en attente."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    return service.list_pending_onboardings()

@router.post("/onboarding/{onboarding_id}/execute")
async def execute_onboarding(
    onboarding_id: int,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Exécuter un processus d'onboarding."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    executed_by = int(context.user_id) if context.user_id else None

    try:
        return service.execute_onboarding(onboarding_id, executed_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# OFFBOARDING
# ============================================================================

@router.post("/offboarding", status_code=201)
async def create_offboarding(
    target_user_id: int = Query(..., description="ID de l'utilisateur partant"),
    departure_date: datetime = Query(..., description="Date de départ"),
    departure_type: str = Query(..., description="Type de départ (resignation, termination, etc.)"),
    transfer_to_user_id: int | None = Query(None, description="ID utilisateur récupérant les dossiers"),
    transfer_notes: str | None = Query(None),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Créer un processus d'offboarding."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    created_by = int(context.user_id) if context.user_id else None
    if not created_by:
        raise HTTPException(status_code=401, detail="User ID required")

    return service.create_offboarding(
        target_user_id, departure_date, departure_type,
        created_by, transfer_to_user_id, transfer_notes
    )

@router.get("/offboarding/scheduled")
async def list_scheduled_offboardings(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les offboardings planifiés."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    return service.list_scheduled_offboardings()

@router.post("/offboarding/{offboarding_id}/execute")
async def execute_offboarding(
    offboarding_id: int,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Exécuter un processus d'offboarding."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    executed_by = int(context.user_id) if context.user_id else None

    try:
        return service.execute_offboarding(offboarding_id, executed_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/offboarding/execute-due")
async def execute_due_offboardings(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Exécuter les offboardings arrivés à échéance (tâche planifiée)."""
    service = get_autoconfig_service(db, context.tenant_id, context.user_id)
    count = service.execute_due_offboardings()
    return {"executed_count": count}
