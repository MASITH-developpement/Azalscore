"""
AZALS MODULE T1 - Router API Configuration Automatique
=======================================================

Endpoints REST pour la configuration automatique par fonction.
"""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.core.models import User

from .models import OverrideStatus, OverrideType
from .schemas import (
    AutoAssignmentRequest,
    EffectiveConfigResponse,
    ManualAssignmentRequest,
    # Offboarding
    OffboardingCreate,
    OffboardingExecutionResult,
    OffboardingListResponse,
    OffboardingResponse,
    # Onboarding
    OnboardingCreate,
    OnboardingExecutionResult,
    OnboardingListResponse,
    OnboardingResponse,
    OverrideListResponse,
    OverrideRejectionRequest,
    # Overrides
    OverrideRequest,
    OverrideResponse,
    # Attributions
    ProfileAssignmentResponse,
    ProfileDetectionRequest,
    ProfileDetectionResponse,
    ProfileListResponse,
    # Profils
    ProfileResponse,
)
from .service import AutoConfigService, get_autoconfig_service

router = APIRouter(prefix="/autoconfig", tags=["autoconfig"])


# ============================================================================
# DÉPENDANCES
# ============================================================================

def get_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
) -> AutoConfigService:
    """Dépendance pour obtenir le service de configuration automatique."""
    return get_autoconfig_service(db, tenant_id)


# ============================================================================
# PROFILS
# ============================================================================

@router.post("/profiles/initialize", status_code=status.HTTP_201_CREATED)
async def initialize_profiles(
    current_user: User = Depends(get_current_user),
    service: AutoConfigService = Depends(get_service)
):
    """Initialise les profils prédéfinis pour le tenant."""
    count = service.initialize_predefined_profiles(created_by=current_user.id)
    return {"message": f"{count} profils initialisés", "count": count}


@router.get("/profiles", response_model=ProfileListResponse)
async def list_profiles(
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    service: AutoConfigService = Depends(get_service)
):
    """Liste tous les profils métier."""
    profiles = service.list_profiles(include_inactive=include_inactive)

    return ProfileListResponse(
        items=[
            ProfileResponse(
                id=p.id,
                tenant_id=p.tenant_id,
                code=p.code,
                name=p.name,
                description=p.description,
                level=p.level.value,
                hierarchy_order=p.hierarchy_order,
                title_patterns=json.loads(p.title_patterns) if p.title_patterns else [],
                department_patterns=json.loads(p.department_patterns) if p.department_patterns else [],
                default_roles=json.loads(p.default_roles) if p.default_roles else [],
                default_permissions=json.loads(p.default_permissions) if p.default_permissions else [],
                default_modules=json.loads(p.default_modules) if p.default_modules else [],
                max_data_access_level=p.max_data_access_level,
                requires_mfa=p.requires_mfa,
                requires_training=p.requires_training,
                is_active=p.is_active,
                is_system=p.is_system,
                priority=p.priority,
                created_at=p.created_at
            )
            for p in profiles
        ],
        total=len(profiles)
    )


@router.get("/profiles/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    service: AutoConfigService = Depends(get_service)
):
    """Récupère un profil par ID."""
    profile = service.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profil non trouvé")

    return ProfileResponse(
        id=profile.id,
        tenant_id=profile.tenant_id,
        code=profile.code,
        name=profile.name,
        description=profile.description,
        level=profile.level.value,
        hierarchy_order=profile.hierarchy_order,
        title_patterns=json.loads(profile.title_patterns) if profile.title_patterns else [],
        department_patterns=json.loads(profile.department_patterns) if profile.department_patterns else [],
        default_roles=json.loads(profile.default_roles) if profile.default_roles else [],
        default_permissions=json.loads(profile.default_permissions) if profile.default_permissions else [],
        default_modules=json.loads(profile.default_modules) if profile.default_modules else [],
        max_data_access_level=profile.max_data_access_level,
        requires_mfa=profile.requires_mfa,
        requires_training=profile.requires_training,
        is_active=profile.is_active,
        is_system=profile.is_system,
        priority=profile.priority,
        created_at=profile.created_at
    )


@router.post("/profiles/detect", response_model=ProfileDetectionResponse)
async def detect_profile(
    data: ProfileDetectionRequest,
    current_user: User = Depends(get_current_user),
    service: AutoConfigService = Depends(get_service)
):
    """Détecte le profil correspondant à un titre/département."""
    profile = service.detect_profile(data.job_title, data.department)

    if profile:
        return ProfileDetectionResponse(
            detected=True,
            profile=ProfileResponse(
                id=profile.id,
                tenant_id=profile.tenant_id,
                code=profile.code,
                name=profile.name,
                description=profile.description,
                level=profile.level.value,
                hierarchy_order=profile.hierarchy_order,
                title_patterns=json.loads(profile.title_patterns) if profile.title_patterns else [],
                department_patterns=json.loads(profile.department_patterns) if profile.department_patterns else [],
                default_roles=json.loads(profile.default_roles) if profile.default_roles else [],
                default_permissions=json.loads(profile.default_permissions) if profile.default_permissions else [],
                default_modules=json.loads(profile.default_modules) if profile.default_modules else [],
                max_data_access_level=profile.max_data_access_level,
                requires_mfa=profile.requires_mfa,
                requires_training=profile.requires_training,
                is_active=profile.is_active,
                is_system=profile.is_system,
                priority=profile.priority,
                created_at=profile.created_at
            ),
            confidence=1.0
        )

    return ProfileDetectionResponse(detected=False, confidence=0.0)


# ============================================================================
# ATTRIBUTIONS
# ============================================================================

@router.post("/assignments/auto", response_model=ProfileAssignmentResponse)
async def auto_assign_profile(
    data: AutoAssignmentRequest,
    current_user: User = Depends(get_current_user),
    service: AutoConfigService = Depends(get_service)
):
    """Attribue automatiquement un profil à un utilisateur."""
    assignment = service.auto_assign_profile(
        user_id=data.user_id,
        job_title=data.job_title,
        department=data.department,
        manager_id=data.manager_id,
        assigned_by=current_user.id
    )

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun profil détecté pour ce titre/département"
        )

    return ProfileAssignmentResponse(
        id=assignment.id,
        tenant_id=assignment.tenant_id,
        user_id=assignment.user_id,
        profile_id=assignment.profile_id,
        profile_code=assignment.profile.code,
        profile_name=assignment.profile.name,
        job_title=assignment.job_title,
        department=assignment.department,
        manager_id=assignment.manager_id,
        is_active=assignment.is_active,
        is_auto=assignment.is_auto,
        assigned_at=assignment.assigned_at,
        assigned_by=assignment.assigned_by
    )


@router.post("/assignments/manual", response_model=ProfileAssignmentResponse)
async def manual_assign_profile(
    data: ManualAssignmentRequest,
    current_user: User = Depends(get_current_user),
    service: AutoConfigService = Depends(get_service)
):
    """Attribue manuellement un profil à un utilisateur."""
    try:
        assignment = service.manual_assign_profile(
            user_id=data.user_id,
            profile_code=data.profile_code,
            assigned_by=current_user.id,
            job_title=data.job_title,
            department=data.department
        )

        return ProfileAssignmentResponse(
            id=assignment.id,
            tenant_id=assignment.tenant_id,
            user_id=assignment.user_id,
            profile_id=assignment.profile_id,
            profile_code=assignment.profile.code,
            profile_name=assignment.profile.name,
            job_title=assignment.job_title,
            department=assignment.department,
            manager_id=assignment.manager_id,
            is_active=assignment.is_active,
            is_auto=assignment.is_auto,
            assigned_at=assignment.assigned_at,
            assigned_by=assignment.assigned_by
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/users/{user_id}/profile", response_model=ProfileAssignmentResponse)
async def get_user_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    service: AutoConfigService = Depends(get_service)
):
    """Récupère l'attribution de profil d'un utilisateur."""
    assignment = service.get_user_profile(user_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aucun profil attribué")

    return ProfileAssignmentResponse(
        id=assignment.id,
        tenant_id=assignment.tenant_id,
        user_id=assignment.user_id,
        profile_id=assignment.profile_id,
        profile_code=assignment.profile.code,
        profile_name=assignment.profile.name,
        job_title=assignment.job_title,
        department=assignment.department,
        manager_id=assignment.manager_id,
        is_active=assignment.is_active,
        is_auto=assignment.is_auto,
        assigned_at=assignment.assigned_at,
        assigned_by=assignment.assigned_by
    )


@router.get("/users/{user_id}/effective-config", response_model=EffectiveConfigResponse)
async def get_user_effective_config(
    user_id: int,
    current_user: User = Depends(get_current_user),
    service: AutoConfigService = Depends(get_service)
):
    """Récupère la configuration effective d'un utilisateur (profil + overrides)."""
    config = service.get_user_effective_config(user_id)
    return EffectiveConfigResponse(**config)


# ============================================================================
# OVERRIDES
# ============================================================================

@router.post("/overrides", response_model=OverrideResponse, status_code=status.HTTP_201_CREATED)
async def request_override(
    data: OverrideRequest,
    current_user: User = Depends(get_current_user),
    service: AutoConfigService = Depends(get_service)
):
    """Demande un override de permissions."""
    try:
        override = service.request_override(
            user_id=data.user_id,
            override_type=OverrideType(data.override_type),
            reason=data.reason,
            requested_by=current_user.id,
            added_roles=data.added_roles,
            removed_roles=data.removed_roles,
            added_permissions=data.added_permissions,
            removed_permissions=data.removed_permissions,
            added_modules=data.added_modules,
            removed_modules=data.removed_modules,
            expires_at=data.expires_at,
            business_justification=data.business_justification
        )

        return OverrideResponse(
            id=override.id,
            tenant_id=override.tenant_id,
            user_id=override.user_id,
            override_type=override.override_type.value,
            status=override.status.value,
            added_roles=json.loads(override.added_roles) if override.added_roles else None,
            removed_roles=json.loads(override.removed_roles) if override.removed_roles else None,
            added_permissions=json.loads(override.added_permissions) if override.added_permissions else None,
            removed_permissions=json.loads(override.removed_permissions) if override.removed_permissions else None,
            added_modules=json.loads(override.added_modules) if override.added_modules else None,
            removed_modules=json.loads(override.removed_modules) if override.removed_modules else None,
            reason=override.reason,
            business_justification=override.business_justification,
            starts_at=override.starts_at,
            expires_at=override.expires_at,
            requested_by=override.requested_by,
            requested_at=override.requested_at,
            approved_by=override.approved_by,
            approved_at=override.approved_at,
            rejected_by=override.rejected_by,
            rejected_at=override.rejected_at,
            rejection_reason=override.rejection_reason
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/overrides", response_model=OverrideListResponse)
async def list_overrides(
    user_id: int | None = None,
    status_filter: str | None = None,
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    service: AutoConfigService = Depends(get_service)
):
    """Liste les overrides."""
    if user_id:
        overrides = service.list_user_overrides(user_id, include_inactive=include_inactive)
    else:
        # Liste tous les overrides du tenant
        from .models import PermissionOverride
        query = service.db.query(PermissionOverride).filter(
            PermissionOverride.tenant_id == service.tenant_id
        )
        if status_filter:
            query = query.filter(PermissionOverride.status == OverrideStatus(status_filter))
        overrides = query.all()

    return OverrideListResponse(
        items=[
            OverrideResponse(
                id=o.id,
                tenant_id=o.tenant_id,
                user_id=o.user_id,
                override_type=o.override_type.value,
                status=o.status.value,
                added_roles=json.loads(o.added_roles) if o.added_roles else None,
                removed_roles=json.loads(o.removed_roles) if o.removed_roles else None,
                added_permissions=json.loads(o.added_permissions) if o.added_permissions else None,
                removed_permissions=json.loads(o.removed_permissions) if o.removed_permissions else None,
                added_modules=json.loads(o.added_modules) if o.added_modules else None,
                removed_modules=json.loads(o.removed_modules) if o.removed_modules else None,
                reason=o.reason,
                business_justification=o.business_justification,
                starts_at=o.starts_at,
                expires_at=o.expires_at,
                requested_by=o.requested_by,
                requested_at=o.requested_at,
                approved_by=o.approved_by,
                approved_at=o.approved_at,
                rejected_by=o.rejected_by,
                rejected_at=o.rejected_at,
                rejection_reason=o.rejection_reason
            )
            for o in overrides
        ],
        total=len(overrides)
    )


@router.post("/overrides/{override_id}/approve", response_model=OverrideResponse)
async def approve_override(
    override_id: int,
    current_user: User = Depends(get_current_user),
    service: AutoConfigService = Depends(get_service)
):
    """Approuve un override en attente."""
    try:
        override = service.approve_override(override_id, approved_by=current_user.id)
        return OverrideResponse(
            id=override.id,
            tenant_id=override.tenant_id,
            user_id=override.user_id,
            override_type=override.override_type.value,
            status=override.status.value,
            added_roles=json.loads(override.added_roles) if override.added_roles else None,
            removed_roles=json.loads(override.removed_roles) if override.removed_roles else None,
            added_permissions=json.loads(override.added_permissions) if override.added_permissions else None,
            removed_permissions=json.loads(override.removed_permissions) if override.removed_permissions else None,
            added_modules=json.loads(override.added_modules) if override.added_modules else None,
            removed_modules=json.loads(override.removed_modules) if override.removed_modules else None,
            reason=override.reason,
            business_justification=override.business_justification,
            starts_at=override.starts_at,
            expires_at=override.expires_at,
            requested_by=override.requested_by,
            requested_at=override.requested_at,
            approved_by=override.approved_by,
            approved_at=override.approved_at,
            rejected_by=override.rejected_by,
            rejected_at=override.rejected_at,
            rejection_reason=override.rejection_reason
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/overrides/{override_id}/reject", response_model=OverrideResponse)
async def reject_override(
    override_id: int,
    data: OverrideRejectionRequest,
    current_user: User = Depends(get_current_user),
    service: AutoConfigService = Depends(get_service)
):
    """Rejette un override en attente."""
    try:
        override = service.reject_override(
            override_id,
            rejected_by=current_user.id,
            rejection_reason=data.rejection_reason
        )
        return OverrideResponse(
            id=override.id,
            tenant_id=override.tenant_id,
            user_id=override.user_id,
            override_type=override.override_type.value,
            status=override.status.value,
            added_roles=json.loads(override.added_roles) if override.added_roles else None,
            removed_roles=json.loads(override.removed_roles) if override.removed_roles else None,
            added_permissions=json.loads(override.added_permissions) if override.added_permissions else None,
            removed_permissions=json.loads(override.removed_permissions) if override.removed_permissions else None,
            added_modules=json.loads(override.added_modules) if override.added_modules else None,
            removed_modules=json.loads(override.removed_modules) if override.removed_modules else None,
            reason=override.reason,
            business_justification=override.business_justification,
            starts_at=override.starts_at,
            expires_at=override.expires_at,
            requested_by=override.requested_by,
            requested_at=override.requested_at,
            approved_by=override.approved_by,
            approved_at=override.approved_at,
            rejected_by=override.rejected_by,
            rejected_at=override.rejected_at,
            rejection_reason=override.rejection_reason
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/overrides/{override_id}/revoke", response_model=OverrideResponse)
async def revoke_override(
    override_id: int,
    current_user: User = Depends(get_current_user),
    service: AutoConfigService = Depends(get_service)
):
    """Révoque un override actif."""
    try:
        override = service.revoke_override(override_id, revoked_by=current_user.id)
        return OverrideResponse(
            id=override.id,
            tenant_id=override.tenant_id,
            user_id=override.user_id,
            override_type=override.override_type.value,
            status=override.status.value,
            added_roles=json.loads(override.added_roles) if override.added_roles else None,
            removed_roles=json.loads(override.removed_roles) if override.removed_roles else None,
            added_permissions=json.loads(override.added_permissions) if override.added_permissions else None,
            removed_permissions=json.loads(override.removed_permissions) if override.removed_permissions else None,
            added_modules=json.loads(override.added_modules) if override.added_modules else None,
            removed_modules=json.loads(override.removed_modules) if override.removed_modules else None,
            reason=override.reason,
            business_justification=override.business_justification,
            starts_at=override.starts_at,
            expires_at=override.expires_at,
            requested_by=override.requested_by,
            requested_at=override.requested_at,
            approved_by=override.approved_by,
            approved_at=override.approved_at,
            rejected_by=override.rejected_by,
            rejected_at=override.rejected_at,
            rejection_reason=override.rejection_reason
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# ONBOARDING
# ============================================================================

@router.post("/onboarding", response_model=OnboardingResponse, status_code=status.HTTP_201_CREATED)
async def create_onboarding(
    data: OnboardingCreate,
    current_user: User = Depends(get_current_user),
    service: AutoConfigService = Depends(get_service)
):
    """Crée un processus d'onboarding."""
    onboarding = service.create_onboarding(
        email=data.email,
        job_title=data.job_title,
        start_date=data.start_date,
        created_by=current_user.id,
        first_name=data.first_name,
        last_name=data.last_name,
        department=data.department,
        manager_id=data.manager_id
    )

    return OnboardingResponse(
        id=onboarding.id,
        tenant_id=onboarding.tenant_id,
        user_id=onboarding.user_id,
        email=onboarding.email,
        first_name=onboarding.first_name,
        last_name=onboarding.last_name,
        job_title=onboarding.job_title,
        department=onboarding.department,
        manager_id=onboarding.manager_id,
        start_date=onboarding.start_date,
        detected_profile_id=onboarding.detected_profile_id,
        detected_profile_code=onboarding.detected_profile.code if onboarding.detected_profile else None,
        profile_override=onboarding.profile_override,
        status=onboarding.status.value,
        steps_completed=json.loads(onboarding.steps_completed) if onboarding.steps_completed else {},
        welcome_email_sent=onboarding.welcome_email_sent,
        manager_notified=onboarding.manager_notified,
        it_notified=onboarding.it_notified,
        created_at=onboarding.created_at,
        completed_at=onboarding.completed_at
    )


@router.get("/onboarding", response_model=OnboardingListResponse)
async def list_onboardings(
    current_user: User = Depends(get_current_user),
    service: AutoConfigService = Depends(get_service)
):
    """Liste les onboardings en attente."""
    onboardings = service.list_pending_onboardings()

    return OnboardingListResponse(
        items=[
            OnboardingResponse(
                id=o.id,
                tenant_id=o.tenant_id,
                user_id=o.user_id,
                email=o.email,
                first_name=o.first_name,
                last_name=o.last_name,
                job_title=o.job_title,
                department=o.department,
                manager_id=o.manager_id,
                start_date=o.start_date,
                detected_profile_id=o.detected_profile_id,
                detected_profile_code=o.detected_profile.code if o.detected_profile else None,
                profile_override=o.profile_override,
                status=o.status.value,
                steps_completed=json.loads(o.steps_completed) if o.steps_completed else {},
                welcome_email_sent=o.welcome_email_sent,
                manager_notified=o.manager_notified,
                it_notified=o.it_notified,
                created_at=o.created_at,
                completed_at=o.completed_at
            )
            for o in onboardings
        ],
        total=len(onboardings)
    )


@router.post("/onboarding/{onboarding_id}/execute", response_model=OnboardingExecutionResult)
async def execute_onboarding(
    onboarding_id: int,
    current_user: User = Depends(get_current_user),
    service: AutoConfigService = Depends(get_service)
):
    """Exécute le processus d'onboarding."""
    try:
        result = service.execute_onboarding(onboarding_id, executed_by=current_user.id)
        return OnboardingExecutionResult(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# OFFBOARDING
# ============================================================================

@router.post("/offboarding", response_model=OffboardingResponse, status_code=status.HTTP_201_CREATED)
async def create_offboarding(
    data: OffboardingCreate,
    current_user: User = Depends(get_current_user),
    service: AutoConfigService = Depends(get_service)
):
    """Crée un processus d'offboarding."""
    offboarding = service.create_offboarding(
        user_id=data.user_id,
        departure_date=data.departure_date,
        departure_type=data.departure_type,
        created_by=current_user.id,
        transfer_to_user_id=data.transfer_to_user_id,
        transfer_notes=data.transfer_notes
    )

    return OffboardingResponse(
        id=offboarding.id,
        tenant_id=offboarding.tenant_id,
        user_id=offboarding.user_id,
        departure_date=offboarding.departure_date,
        departure_type=offboarding.departure_type,
        transfer_to_user_id=offboarding.transfer_to_user_id,
        transfer_notes=offboarding.transfer_notes,
        status=offboarding.status.value,
        steps_completed=json.loads(offboarding.steps_completed) if offboarding.steps_completed else {},
        account_deactivated=offboarding.account_deactivated,
        access_revoked=offboarding.access_revoked,
        data_archived=offboarding.data_archived,
        data_deleted=offboarding.data_deleted,
        manager_notified=offboarding.manager_notified,
        it_notified=offboarding.it_notified,
        team_notified=offboarding.team_notified,
        created_at=offboarding.created_at,
        completed_at=offboarding.completed_at
    )


@router.get("/offboarding", response_model=OffboardingListResponse)
async def list_offboardings(
    current_user: User = Depends(get_current_user),
    service: AutoConfigService = Depends(get_service)
):
    """Liste les offboardings planifiés."""
    offboardings = service.list_scheduled_offboardings()

    return OffboardingListResponse(
        items=[
            OffboardingResponse(
                id=o.id,
                tenant_id=o.tenant_id,
                user_id=o.user_id,
                departure_date=o.departure_date,
                departure_type=o.departure_type,
                transfer_to_user_id=o.transfer_to_user_id,
                transfer_notes=o.transfer_notes,
                status=o.status.value,
                steps_completed=json.loads(o.steps_completed) if o.steps_completed else {},
                account_deactivated=o.account_deactivated,
                access_revoked=o.access_revoked,
                data_archived=o.data_archived,
                data_deleted=o.data_deleted,
                manager_notified=o.manager_notified,
                it_notified=o.it_notified,
                team_notified=o.team_notified,
                created_at=o.created_at,
                completed_at=o.completed_at
            )
            for o in offboardings
        ],
        total=len(offboardings)
    )


@router.post("/offboarding/{offboarding_id}/execute", response_model=OffboardingExecutionResult)
async def execute_offboarding(
    offboarding_id: int,
    current_user: User = Depends(get_current_user),
    service: AutoConfigService = Depends(get_service)
):
    """Exécute le processus d'offboarding."""
    try:
        result = service.execute_offboarding(offboarding_id, executed_by=current_user.id)
        return OffboardingExecutionResult(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
