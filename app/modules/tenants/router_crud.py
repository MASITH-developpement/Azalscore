"""
AZALS MODULE T9 - TENANTS: Router Unifié
=========================================

Router complet compatible v1, v2 et v3 via app.azals.
Utilise get_context() qui fonctionne avec les deux patterns d'authentification.

Ce router remplace router.py et router_v2.py.

Enregistrement dans main.py:
    from app.modules.tenants.router_unified import router as tenants_router

    # Double enregistrement pour compatibilité
    app.include_router(tenants_router, prefix="/v2")
    app.include_router(tenants_router, prefix="/v1", deprecated=True)

Conformité : AZA-NF-006

ENDPOINTS (30 total):
- Tenants (9): CRUD + activate/suspend/cancel/trial + me
- Subscriptions (3): create + get active + update
- Modules (4): activate + list + deactivate + check active
- Invitations (3): create + get + accept
- Usage & Events (3): get/record usage + get events
- Settings (2): get + update
- Onboarding (2): get + update
- Dashboard (1): get tenant dashboard
- Provisioning (2): provision + provision_masith
- Platform (1): stats
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db

from app.core.models import UserRole

from .service import get_tenant_service
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
# SÉCURITÉ: Fonctions de vérification des accès
# ============================================================================

def verify_tenant_ownership(context: SaaSContext, tenant_id: str) -> None:
    """Vérifie que l'utilisateur a accès au tenant spécifié."""
    if context.role == UserRole.SUPERADMIN:
        return
    if context.tenant_id != tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé. Vous ne pouvez accéder qu'aux données de votre propre tenant."
        )

def require_super_admin(context: SaaSContext) -> None:
    """Vérifie que l'utilisateur est super_admin (opérations plateforme)."""
    if context.role != UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé. Droits super_admin requis pour cette opération."
        )

def require_tenant_admin(context: SaaSContext) -> None:
    """Vérifie que l'utilisateur a un rôle admin dans son tenant."""
    if context.role not in [UserRole.SUPERADMIN, UserRole.DIRIGEANT, UserRole.ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé. Rôle ADMIN ou DIRIGEANT requis."
        )

# ============================================================================
# TENANTS
# ============================================================================

@router.post("", response_model=TenantResponse, status_code=201)
def create_tenant(
    data: TenantCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer un nouveau tenant."""
    require_super_admin(context)
    service = get_tenant_service(db, context.user_id, actor_email=None)

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
    context: SaaSContext = Depends(get_context)
):
    """Lister les tenants."""
    require_super_admin(context)
    service = get_tenant_service(db)
    return service.list_tenants(status, plan, country, skip, limit)

@router.get("/me", response_model=TenantResponse)
def get_current_tenant(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer le tenant courant."""
    service = get_tenant_service(db)
    tenant = service.get_tenant(context.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")
    return tenant

@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un tenant."""
    verify_tenant_ownership(context, tenant_id)
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
    context: SaaSContext = Depends(get_context)
):
    """Mettre à jour un tenant."""
    verify_tenant_ownership(context, tenant_id)
    require_tenant_admin(context)
    service = get_tenant_service(db, context.user_id, actor_email=None)
    tenant = service.update_tenant(tenant_id, data)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")
    return tenant

@router.post("/{tenant_id}/activate", response_model=TenantResponse)
def activate_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Activer un tenant."""
    require_super_admin(context)
    service = get_tenant_service(db, context.user_id, actor_email=None)
    tenant = service.activate_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")
    return tenant

@router.post("/{tenant_id}/suspend", response_model=TenantResponse)
def suspend_tenant(
    tenant_id: str,
    reason: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Suspendre un tenant."""
    require_super_admin(context)
    service = get_tenant_service(db, context.user_id, actor_email=None)
    tenant = service.suspend_tenant(tenant_id, reason)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")
    return tenant

@router.post("/{tenant_id}/cancel", response_model=TenantResponse)
def cancel_tenant(
    tenant_id: str,
    reason: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Annuler un tenant."""
    require_super_admin(context)
    service = get_tenant_service(db, context.user_id, actor_email=None)
    tenant = service.cancel_tenant(tenant_id, reason)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")
    return tenant

@router.post("/{tenant_id}/trial", response_model=TenantResponse)
def start_trial(
    tenant_id: str,
    days: int = 14,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Démarrer un essai gratuit."""
    service = get_tenant_service(db, context.user_id, actor_email=None)
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
    context: SaaSContext = Depends(get_context)
):
    """Créer un abonnement."""
    require_super_admin(context)
    service = get_tenant_service(db, context.user_id, actor_email=None)

    if not service.get_tenant(tenant_id):
        raise HTTPException(status_code=404, detail="Tenant non trouvé")

    return service.create_subscription(tenant_id, data)

@router.get("/{tenant_id}/subscriptions/active", response_model=SubscriptionResponse)
def get_active_subscription(
    tenant_id: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
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
    context: SaaSContext = Depends(get_context)
):
    """Mettre à jour l'abonnement."""
    service = get_tenant_service(db, context.user_id, actor_email=None)
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
    context: SaaSContext = Depends(get_context)
):
    """Activer un module."""
    service = get_tenant_service(db, context.user_id, actor_email=None)

    if not service.get_tenant(tenant_id):
        raise HTTPException(status_code=404, detail="Tenant non trouvé")

    return service.activate_module(tenant_id, data)

@router.get("/{tenant_id}/modules", response_model=list[TenantModuleResponse])
def list_tenant_modules(
    tenant_id: str,
    active_only: bool = True,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les modules d'un tenant."""
    service = get_tenant_service(db)
    return service.list_tenant_modules(tenant_id, active_only)

@router.delete("/{tenant_id}/modules/{module_code}", response_model=TenantModuleResponse)
def deactivate_module(
    tenant_id: str,
    module_code: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Désactiver un module."""
    service = get_tenant_service(db, context.user_id, actor_email=None)
    module = service.deactivate_module(tenant_id, module_code)
    if not module:
        raise HTTPException(status_code=404, detail="Module non trouvé")
    return module

@router.get("/{tenant_id}/modules/{module_code}/active")
def check_module_active(
    tenant_id: str,
    module_code: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Vérifier si un module est actif."""
    service = get_tenant_service(db)
    is_active = service.is_module_active(tenant_id, module_code)
    return {"module_code": module_code, "is_active": is_active}

@router.get("/modules/available")
def list_available_modules(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister tous les modules disponibles pour activation."""
    from app.modules.tenants import AVAILABLE_MODULES, MODULE_DETAILS

    modules = []
    for code in AVAILABLE_MODULES:
        details = MODULE_DETAILS.get(code, {})
        modules.append({
            "code": code,
            "name": details.get("name", code),
            "description": details.get("description", ""),
            "category": details.get("category", "Autre"),
        })

    categories = {}
    for module in modules:
        cat = module["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(module)

    return {
        "modules": modules,
        "by_category": categories,
        "total": len(modules),
    }

# ============================================================================
# INVITATIONS
# ============================================================================

@router.post("/invitations", response_model=TenantInvitationResponse, status_code=201)
def create_invitation(
    data: TenantInvitationCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer une invitation."""
    service = get_tenant_service(db, context.user_id, actor_email=None)
    return service.create_invitation(data)

@router.get("/invitations/{token}", response_model=TenantInvitationResponse)
def get_invitation(
    token: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
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
    context: SaaSContext = Depends(get_context)
):
    """Accepter une invitation."""
    service = get_tenant_service(db, context.user_id, actor_email=None)
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
    context: SaaSContext = Depends(get_context)
):
    """Récupérer l'utilisation."""
    service = get_tenant_service(db)
    return service.get_usage(tenant_id, start_date, end_date, period)

@router.post("/{tenant_id}/usage")
def record_tenant_usage(
    tenant_id: str,
    data: dict,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
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
    context: SaaSContext = Depends(get_context)
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
    context: SaaSContext = Depends(get_context)
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
    context: SaaSContext = Depends(get_context)
):
    """Mettre à jour les paramètres."""
    service = get_tenant_service(db, context.user_id, actor_email=None)
    return service.update_settings(tenant_id, data)

# ============================================================================
# ONBOARDING
# ============================================================================

@router.get("/{tenant_id}/onboarding", response_model=TenantOnboardingResponse)
def get_tenant_onboarding(
    tenant_id: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
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
    context: SaaSContext = Depends(get_context)
):
    """Mettre à jour une étape onboarding."""
    service = get_tenant_service(db, context.user_id, actor_email=None)
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
    context: SaaSContext = Depends(get_context)
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
    context: SaaSContext = Depends(get_context)
):
    """Provisionner un tenant complet."""
    require_super_admin(context)
    service = get_tenant_service(db, context.user_id, actor_email=None)

    if service.get_tenant(data.tenant.tenant_id):
        raise HTTPException(status_code=409, detail="Tenant ID déjà utilisé")

    return service.provision_tenant(data)

@router.post("/provision/masith", status_code=201)
def provision_masith(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Provisionner le tenant SAS MASITH (premier client)."""
    require_super_admin(context)
    service = get_tenant_service(db, context.user_id, actor_email=None)
    return service.provision_masith()

# ============================================================================
# PLATFORM STATS
# ============================================================================

@router.get("/platform/stats", response_model=PlatformStatsResponse)
def get_platform_stats(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Statistiques globales de la plateforme."""
    require_super_admin(context)
    service = get_tenant_service(db)
    return service.get_platform_stats()
