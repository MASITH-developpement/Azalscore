"""
AZALS MODULE T9 - Router Tenants
=================================

API REST pour la gestion des tenants.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.models import User

from .service import get_tenant_service

# ============================================================================
# SÉCURITÉ: Fonctions de vérification des accès
# ============================================================================

def verify_tenant_ownership(current_user: User, tenant_id: str) -> None:
    """
    Vérifie que l'utilisateur a accès au tenant spécifié.
    Seuls les utilisateurs du même tenant ou les super_admin peuvent accéder.
    """
    from fastapi import HTTPException

    user_tenant_id = current_user.tenant_id
    user_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)

    # Super admin peut tout faire
    if user_role == "SUPER_ADMIN":
        return

    # Vérifier que l'utilisateur appartient au tenant
    if user_tenant_id != tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé. Vous ne pouvez accéder qu'aux données de votre propre tenant."
        )


def require_super_admin(current_user: User) -> None:
    """Vérifie que l'utilisateur est super_admin (opérations plateforme)."""
    from fastapi import HTTPException

    user_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    if user_role != "SUPER_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Accès refusé. Droits super_admin requis pour cette opération."
        )


def require_tenant_admin(current_user: User) -> None:
    """Vérifie que l'utilisateur a un rôle admin dans son tenant."""
    from fastapi import HTTPException

    user_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    if user_role not in ["SUPER_ADMIN", "DIRIGEANT", "ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé. Rôle ADMIN ou DIRIGEANT requis."
        )
from .schemas import (
    ModuleActivation,
    OnboardingStepUpdate,
    PlatformStatsResponse,
    ProvisionTenantRequest,
    ProvisionTenantResponse,
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionUpdate,
    TenantCreate,
    TenantDashboardResponse,
    TenantEventResponse,
    TenantInvitationCreate,
    TenantInvitationResponse,
    TenantListResponse,
    TenantModuleResponse,
    TenantOnboardingResponse,
    TenantResponse,
    TenantSettingsResponse,
    TenantSettingsUpdate,
    TenantUpdate,
    TenantUsageResponse,
)

router = APIRouter(prefix="/tenants", tags=["Tenants"])


# ============================================================================
# TENANTS
# ============================================================================

@router.post("", response_model=TenantResponse, status_code=201)
def create_tenant(
    data: TenantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un nouveau tenant."""
    # SÉCURITÉ: Seul super_admin peut créer de nouveaux tenants
    require_super_admin(current_user)

    service = get_tenant_service(db, current_user.id, current_user.email)

    # Vérifier si tenant_id existe déjà
    if service.get_tenant(data.tenant_id):
        raise HTTPException(status_code=409, detail="Tenant ID déjà utilisé")

    return service.create_tenant(data)


@router.get("", response_model=list[TenantListResponse])
def list_tenants(
    status: str | None = None,
    plan: str | None = None,
    country: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les tenants."""
    # SÉCURITÉ: Seul super_admin peut voir tous les tenants
    require_super_admin(current_user)
    service = get_tenant_service(db)
    return service.list_tenants(status, plan, country, skip, limit)


@router.get("/me", response_model=TenantResponse)
def get_current_tenant(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer le tenant courant."""
    service = get_tenant_service(db)
    tenant = service.get_tenant(current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")
    return tenant


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un tenant."""
    # SÉCURITÉ: Vérifier l'accès au tenant
    verify_tenant_ownership(current_user, tenant_id)

    service = get_tenant_service(db)
    tenant = service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")
    return tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: str,
    data: TenantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un tenant."""
    # SÉCURITÉ: Vérifier l'accès au tenant + rôle admin
    verify_tenant_ownership(current_user, tenant_id)
    require_tenant_admin(current_user)

    service = get_tenant_service(db, current_user.id, current_user.email)
    tenant = service.update_tenant(tenant_id, data)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")
    return tenant


@router.post("/{tenant_id}/activate", response_model=TenantResponse)
def activate_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activer un tenant."""
    # SÉCURITÉ: Seul super_admin peut activer un tenant
    require_super_admin(current_user)

    service = get_tenant_service(db, current_user.id, current_user.email)
    tenant = service.activate_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")
    return tenant


@router.post("/{tenant_id}/suspend", response_model=TenantResponse)
def suspend_tenant(
    tenant_id: str,
    reason: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Suspendre un tenant."""
    # SÉCURITÉ: Seul super_admin peut suspendre un tenant
    require_super_admin(current_user)

    service = get_tenant_service(db, current_user.id, current_user.email)
    tenant = service.suspend_tenant(tenant_id, reason)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")
    return tenant


@router.post("/{tenant_id}/cancel", response_model=TenantResponse)
def cancel_tenant(
    tenant_id: str,
    reason: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Annuler un tenant."""
    # SÉCURITÉ: Seul super_admin peut annuler un tenant
    require_super_admin(current_user)

    service = get_tenant_service(db, current_user.id, current_user.email)
    tenant = service.cancel_tenant(tenant_id, reason)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")
    return tenant


@router.post("/{tenant_id}/trial", response_model=TenantResponse)
def start_trial(
    tenant_id: str,
    days: int = 14,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Démarrer un essai gratuit."""
    service = get_tenant_service(db, current_user.id, current_user.email)
    tenant = service.start_trial(tenant_id, days)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")
    return tenant


# ============================================================================
# SUBSCRIPTIONS
# ============================================================================

@router.post("/{tenant_id}/subscriptions", response_model=SubscriptionResponse, status_code=201)
def create_subscription(
    tenant_id: str,
    data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un abonnement."""
    # SÉCURITÉ: Seul super_admin peut créer des abonnements
    require_super_admin(current_user)

    service = get_tenant_service(db, current_user.id, current_user.email)

    if not service.get_tenant(tenant_id):
        raise HTTPException(status_code=404, detail="Tenant non trouvé")

    return service.create_subscription(tenant_id, data)


@router.get("/{tenant_id}/subscriptions/active", response_model=SubscriptionResponse)
def get_active_subscription(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer l'abonnement actif."""
    service = get_tenant_service(db)
    subscription = service.get_active_subscription(tenant_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Aucun abonnement actif")
    return subscription


@router.put("/{tenant_id}/subscriptions", response_model=SubscriptionResponse)
def update_subscription(
    tenant_id: str,
    data: SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour l'abonnement."""
    service = get_tenant_service(db, current_user.id, current_user.email)
    subscription = service.update_subscription(tenant_id, data)
    if not subscription:
        raise HTTPException(status_code=404, detail="Aucun abonnement actif")
    return subscription


# ============================================================================
# MODULES
# ============================================================================

@router.post("/{tenant_id}/modules", response_model=TenantModuleResponse, status_code=201)
def activate_module(
    tenant_id: str,
    data: ModuleActivation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activer un module."""
    service = get_tenant_service(db, current_user.id, current_user.email)

    if not service.get_tenant(tenant_id):
        raise HTTPException(status_code=404, detail="Tenant non trouvé")

    return service.activate_module(tenant_id, data)


@router.get("/{tenant_id}/modules", response_model=list[TenantModuleResponse])
def list_tenant_modules(
    tenant_id: str,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les modules d'un tenant."""
    service = get_tenant_service(db)
    return service.list_tenant_modules(tenant_id, active_only)


@router.delete("/{tenant_id}/modules/{module_code}", response_model=TenantModuleResponse)
def deactivate_module(
    tenant_id: str,
    module_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Désactiver un module."""
    service = get_tenant_service(db, current_user.id, current_user.email)
    module = service.deactivate_module(tenant_id, module_code)
    if not module:
        raise HTTPException(status_code=404, detail="Module non trouvé")
    return module


@router.get("/{tenant_id}/modules/{module_code}/active")
def check_module_active(
    tenant_id: str,
    module_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Vérifier si un module est actif."""
    service = get_tenant_service(db)
    is_active = service.is_module_active(tenant_id, module_code)
    return {"module_code": module_code, "is_active": is_active}


# ============================================================================
# INVITATIONS
# ============================================================================

@router.post("/invitations", response_model=TenantInvitationResponse, status_code=201)
def create_invitation(
    data: TenantInvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une invitation."""
    service = get_tenant_service(db, current_user.id, current_user.email)
    return service.create_invitation(data)


@router.get("/invitations/{token}", response_model=TenantInvitationResponse)
def get_invitation(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une invitation."""
    service = get_tenant_service(db)
    invitation = service.get_invitation_by_token(token)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation non trouvée")
    return invitation


@router.post("/invitations/{token}/accept", response_model=TenantInvitationResponse)
def accept_invitation(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accepter une invitation."""
    service = get_tenant_service(db, current_user.id, current_user.email)
    invitation = service.accept_invitation(token)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation invalide ou expirée")
    return invitation


# ============================================================================
# USAGE & EVENTS
# ============================================================================

@router.get("/{tenant_id}/usage", response_model=list[TenantUsageResponse])
def get_tenant_usage(
    tenant_id: str,
    start_date: datetime,
    end_date: datetime,
    period: str = "daily",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer l'utilisation."""
    service = get_tenant_service(db)
    return service.get_usage(tenant_id, start_date, end_date, period)


@router.post("/{tenant_id}/usage")
def record_tenant_usage(
    tenant_id: str,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enregistrer l'utilisation."""
    service = get_tenant_service(db)
    return service.record_usage(tenant_id, data)


@router.get("/{tenant_id}/events", response_model=list[TenantEventResponse])
def get_tenant_events(
    tenant_id: str,
    event_type: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les événements."""
    service = get_tenant_service(db)
    return service.get_events(tenant_id, event_type, skip, limit)


# ============================================================================
# SETTINGS
# ============================================================================

@router.get("/{tenant_id}/settings", response_model=TenantSettingsResponse)
def get_tenant_settings(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les paramètres."""
    service = get_tenant_service(db)
    settings = service.get_settings(tenant_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Paramètres non trouvés")
    return settings


@router.put("/{tenant_id}/settings", response_model=TenantSettingsResponse)
def update_tenant_settings(
    tenant_id: str,
    data: TenantSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour les paramètres."""
    service = get_tenant_service(db, current_user.id, current_user.email)
    return service.update_settings(tenant_id, data)


# ============================================================================
# ONBOARDING
# ============================================================================

@router.get("/{tenant_id}/onboarding", response_model=TenantOnboardingResponse)
def get_tenant_onboarding(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer l'onboarding."""
    service = get_tenant_service(db)
    onboarding = service.get_onboarding(tenant_id)
    if not onboarding:
        raise HTTPException(status_code=404, detail="Onboarding non trouvé")
    return onboarding


@router.put("/{tenant_id}/onboarding", response_model=TenantOnboardingResponse)
def update_onboarding_step(
    tenant_id: str,
    data: OnboardingStepUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour une étape onboarding."""
    service = get_tenant_service(db, current_user.id, current_user.email)
    onboarding = service.update_onboarding_step(tenant_id, data)
    if not onboarding:
        raise HTTPException(status_code=404, detail="Onboarding non trouvé")
    return onboarding


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/{tenant_id}/dashboard", response_model=TenantDashboardResponse)
def get_tenant_dashboard(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dashboard complet du tenant."""
    service = get_tenant_service(db)

    tenant = service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")

    subscription = service.get_active_subscription(tenant_id)
    modules = service.list_tenant_modules(tenant_id)
    onboarding = service.get_onboarding(tenant_id)
    events = service.get_events(tenant_id, limit=10)

    # Usage aujourd'hui
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    usage = service.get_usage(tenant_id, today, today + timedelta(days=1), "daily")

    return {
        "tenant": tenant,
        "subscription": subscription,
        "modules": modules,
        "onboarding": onboarding,
        "usage_today": usage[0] if usage else None,
        "recent_events": events,
    }


# ============================================================================
# PROVISIONING
# ============================================================================

@router.post("/provision", response_model=ProvisionTenantResponse, status_code=201)
def provision_tenant(
    data: ProvisionTenantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Provisionner un tenant complet."""
    # SÉCURITÉ: Seul super_admin peut provisionner des tenants
    require_super_admin(current_user)

    service = get_tenant_service(db, current_user.id, current_user.email)

    # Vérifier si tenant_id existe déjà
    if service.get_tenant(data.tenant.tenant_id):
        raise HTTPException(status_code=409, detail="Tenant ID déjà utilisé")

    result = service.provision_tenant(data)
    return result


@router.post("/provision/masith", status_code=201)
def provision_masith(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Provisionner le tenant SAS MASITH (premier client)."""
    # SÉCURITÉ: Seul super_admin peut provisionner des tenants
    require_super_admin(current_user)

    service = get_tenant_service(db, current_user.id, current_user.email)
    return service.provision_masith()


# ============================================================================
# PLATFORM STATS
# ============================================================================

@router.get("/platform/stats", response_model=PlatformStatsResponse)
def get_platform_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Statistiques globales de la plateforme."""
    # SÉCURITÉ: Seul super_admin peut voir les stats de la plateforme
    require_super_admin(current_user)

    service = get_tenant_service(db)
    return service.get_platform_stats()
