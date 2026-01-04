"""
AZALS MODULE T9 - Schémas Tenants
==================================

Schémas Pydantic pour l'API des tenants.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import json


# ============================================================================
# ENUMS
# ============================================================================

class TenantStatus(str):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"
    TRIAL = "TRIAL"


class SubscriptionPlan(str):
    STARTER = "STARTER"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"
    CUSTOM = "CUSTOM"


class BillingCycle(str):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"


class ModuleStatus(str):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    PENDING = "PENDING"


# ============================================================================
# TENANT
# ============================================================================

class TenantCreate(BaseModel):
    """Création d'un tenant."""
    tenant_id: str = Field(..., min_length=3, max_length=50, pattern="^[a-z0-9_-]+$")
    name: str = Field(..., min_length=1, max_length=255)
    legal_name: Optional[str] = None
    siret: Optional[str] = None
    vat_number: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "FR"
    email: str = Field(..., min_length=5, max_length=255)
    phone: Optional[str] = None
    website: Optional[str] = None
    plan: str = "STARTER"
    timezone: str = "Europe/Paris"
    language: str = "fr"
    currency: str = "EUR"
    max_users: int = 5
    max_storage_gb: int = 10
    logo_url: Optional[str] = None
    primary_color: str = "#1976D2"
    secondary_color: str = "#424242"
    features: Optional[Dict[str, Any]] = None
    extra_data: Optional[Dict[str, Any]] = None


class TenantUpdate(BaseModel):
    """Mise à jour d'un tenant."""
    name: Optional[str] = None
    legal_name: Optional[str] = None
    siret: Optional[str] = None
    vat_number: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    currency: Optional[str] = None
    max_users: Optional[int] = None
    max_storage_gb: Optional[int] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    features: Optional[Dict[str, Any]] = None
    extra_data: Optional[Dict[str, Any]] = None


class TenantResponse(BaseModel):
    """Réponse tenant."""
    id: int
    tenant_id: str
    name: str
    legal_name: Optional[str]
    siret: Optional[str]
    vat_number: Optional[str]
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    postal_code: Optional[str]
    country: str
    email: str
    phone: Optional[str]
    website: Optional[str]
    status: str
    plan: str
    timezone: str
    language: str
    currency: str
    date_format: str
    max_users: int
    max_storage_gb: int
    storage_used_gb: float
    logo_url: Optional[str]
    primary_color: str
    secondary_color: str
    features: Optional[Dict[str, Any]]
    extra_data: Optional[Dict[str, Any]]
    trial_ends_at: Optional[datetime]
    activated_at: Optional[datetime]
    suspended_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @field_validator("features", "extra_data", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    class Config:
        from_attributes = True


class TenantListResponse(BaseModel):
    """Liste de tenants."""
    id: int
    tenant_id: str
    name: str
    email: str
    status: str
    plan: str
    country: str
    max_users: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SUBSCRIPTION
# ============================================================================

class SubscriptionCreate(BaseModel):
    """Création d'un abonnement."""
    plan: str
    billing_cycle: str = "MONTHLY"
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    discount_percent: float = 0
    starts_at: datetime
    ends_at: Optional[datetime] = None
    is_trial: bool = False
    auto_renew: bool = True
    payment_method: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    """Mise à jour d'un abonnement."""
    plan: Optional[str] = None
    billing_cycle: Optional[str] = None
    auto_renew: Optional[bool] = None
    payment_method: Optional[str] = None


class SubscriptionResponse(BaseModel):
    """Réponse abonnement."""
    id: int
    tenant_id: str
    plan: str
    billing_cycle: str
    price_monthly: Optional[float]
    price_yearly: Optional[float]
    discount_percent: float
    starts_at: datetime
    ends_at: Optional[datetime]
    next_billing_at: Optional[datetime]
    is_active: bool
    is_trial: bool
    auto_renew: bool
    payment_method: Optional[str]
    last_payment_at: Optional[datetime]
    last_payment_amount: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# MODULES
# ============================================================================

class ModuleActivation(BaseModel):
    """Activation d'un module."""
    module_code: str = Field(..., min_length=2, max_length=10)
    module_name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    limits: Optional[Dict[str, Any]] = None


class ModuleDeactivation(BaseModel):
    """Désactivation d'un module."""
    module_code: str


class TenantModuleResponse(BaseModel):
    """Réponse module tenant."""
    id: int
    tenant_id: str
    module_code: str
    module_name: Optional[str]
    module_version: Optional[str]
    status: str
    config: Optional[Dict[str, Any]]
    limits: Optional[Dict[str, Any]]
    activated_at: datetime
    deactivated_at: Optional[datetime]

    @field_validator("config", "limits", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    class Config:
        from_attributes = True


# ============================================================================
# INVITATION
# ============================================================================

class TenantInvitationCreate(BaseModel):
    """Création d'invitation tenant."""
    email: str = Field(..., min_length=5, max_length=255)
    tenant_id: Optional[str] = None
    tenant_name: Optional[str] = None
    plan: str = "STARTER"
    proposed_role: str = "TENANT_ADMIN"
    expires_in_days: int = 7


class TenantInvitationResponse(BaseModel):
    """Réponse invitation."""
    id: int
    token: str
    email: str
    tenant_id: Optional[str]
    tenant_name: Optional[str]
    plan: Optional[str]
    proposed_role: str
    status: str
    expires_at: datetime
    accepted_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# USAGE
# ============================================================================

class TenantUsageResponse(BaseModel):
    """Réponse utilisation."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True, from_attributes=True)

    id: int
    tenant_id: str
    usage_date: datetime = Field(..., alias="date")
    period: str
    active_users: int
    total_users: int
    new_users: int
    storage_used_gb: float
    files_count: int
    api_calls: int
    api_errors: int
    module_usage: Optional[Dict[str, int]]

    @field_validator("module_usage", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v


# ============================================================================
# SETTINGS
# ============================================================================

class TenantSettingsUpdate(BaseModel):
    """Mise à jour des paramètres."""
    two_factor_required: Optional[bool] = None
    session_timeout_minutes: Optional[int] = None
    password_expiry_days: Optional[int] = None
    ip_whitelist: Optional[List[str]] = None
    notify_admin_on_signup: Optional[bool] = None
    notify_admin_on_error: Optional[bool] = None
    daily_digest_enabled: Optional[bool] = None
    webhook_url: Optional[str] = None
    api_rate_limit: Optional[int] = None
    auto_backup_enabled: Optional[bool] = None
    backup_retention_days: Optional[int] = None
    custom_settings: Optional[Dict[str, Any]] = None


class TenantSettingsResponse(BaseModel):
    """Réponse paramètres."""
    id: int
    tenant_id: str
    two_factor_required: bool
    session_timeout_minutes: int
    password_expiry_days: int
    ip_whitelist: Optional[List[str]]
    notify_admin_on_signup: bool
    notify_admin_on_error: bool
    daily_digest_enabled: bool
    webhook_url: Optional[str]
    api_rate_limit: int
    auto_backup_enabled: bool
    backup_retention_days: int
    custom_settings: Optional[Dict[str, Any]]
    updated_at: datetime

    @field_validator("ip_whitelist", "custom_settings", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    class Config:
        from_attributes = True


# ============================================================================
# ONBOARDING
# ============================================================================

class OnboardingStepUpdate(BaseModel):
    """Mise à jour d'une étape onboarding."""
    step: str
    completed: bool = True


class TenantOnboardingResponse(BaseModel):
    """Réponse onboarding."""
    id: int
    tenant_id: str
    company_info_completed: bool
    admin_created: bool
    users_invited: bool
    modules_configured: bool
    country_pack_selected: bool
    first_data_imported: bool
    training_completed: bool
    progress_percent: int
    current_step: str
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# ÉVÉNEMENTS
# ============================================================================

class TenantEventResponse(BaseModel):
    """Réponse événement."""
    id: int
    tenant_id: str
    event_type: str
    event_data: Optional[Dict[str, Any]]
    description: Optional[str]
    actor_id: Optional[int]
    actor_email: Optional[str]
    actor_ip: Optional[str]
    created_at: datetime

    @field_validator("event_data", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    class Config:
        from_attributes = True


# ============================================================================
# DASHBOARD
# ============================================================================

class TenantDashboardResponse(BaseModel):
    """Dashboard tenant."""
    tenant: TenantResponse
    subscription: Optional[SubscriptionResponse]
    modules: List[TenantModuleResponse]
    onboarding: Optional[TenantOnboardingResponse]
    usage_today: Optional[TenantUsageResponse]
    recent_events: List[TenantEventResponse]


# ============================================================================
# PROVISIONING
# ============================================================================

class ProvisionTenantRequest(BaseModel):
    """Demande de provisioning complet."""
    tenant: TenantCreate
    admin_email: str
    admin_first_name: str
    admin_last_name: str
    admin_password: Optional[str] = None  # Auto-généré si absent
    modules: List[str] = ["T0", "T1", "T2", "T3", "T4"]
    country_pack: str = "FR"
    send_welcome_email: bool = True


class ProvisionTenantResponse(BaseModel):
    """Réponse provisioning."""
    tenant: TenantResponse
    admin_user_id: int
    admin_email: str
    temporary_password: Optional[str]
    activated_modules: List[str]
    onboarding_url: str


# ============================================================================
# STATS PLATFORM
# ============================================================================

class PlatformStatsResponse(BaseModel):
    """Statistiques plateforme."""
    total_tenants: int
    active_tenants: int
    trial_tenants: int
    suspended_tenants: int
    total_users: int
    storage_used_gb: float
    tenants_by_plan: Dict[str, int]
    tenants_by_country: Dict[str, int]
    new_tenants_this_month: int
    revenue_this_month: float
