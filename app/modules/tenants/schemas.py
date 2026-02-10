"""
AZALS MODULE T9 - Schémas Tenants
==================================

Schémas Pydantic pour l'API des tenants.
"""


import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
    legal_name: str | None = None
    siret: str | None = None
    vat_number: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    postal_code: str | None = None
    country: str = "FR"
    email: str = Field(..., min_length=5, max_length=255)
    phone: str | None = None
    website: str | None = None
    plan: str = "STARTER"
    timezone: str = "Europe/Paris"
    language: str = "fr"
    currency: str = "EUR"
    max_users: int = 5
    max_storage_gb: int = 10
    logo_url: str | None = None
    primary_color: str = "#1976D2"
    secondary_color: str = "#424242"
    features: dict[str, Any] | None = None
    extra_data: dict[str, Any] | None = None


class TenantUpdate(BaseModel):
    """Mise à jour d'un tenant."""
    name: str | None = None
    legal_name: str | None = None
    siret: str | None = None
    vat_number: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    postal_code: str | None = None
    country: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    timezone: str | None = None
    language: str | None = None
    currency: str | None = None
    max_users: int | None = None
    max_storage_gb: int | None = None
    logo_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    features: dict[str, Any] | None = None
    extra_data: dict[str, Any] | None = None


class TenantResponse(BaseModel):
    """Réponse tenant."""
    id: UUID
    tenant_id: str
    name: str
    legal_name: str | None
    siret: str | None
    vat_number: str | None
    address_line1: str | None
    address_line2: str | None
    city: str | None
    postal_code: str | None
    country: str
    email: str
    phone: str | None
    website: str | None
    status: str
    plan: str
    timezone: str
    language: str
    currency: str
    date_format: str
    max_users: int
    max_storage_gb: int
    storage_used_gb: float
    logo_url: str | None
    primary_color: str
    secondary_color: str
    features: dict[str, Any] | None
    extra_data: dict[str, Any] | None
    trial_ends_at: datetime | None
    activated_at: datetime | None
    suspended_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @field_validator("features", "extra_data", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    model_config = ConfigDict(from_attributes=True)


class TenantListResponse(BaseModel):
    """Liste de tenants."""
    id: UUID
    tenant_id: str
    name: str
    email: str
    status: str
    plan: str
    country: str
    max_users: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator('status', 'plan', mode='before')
    @classmethod
    def convert_enum_to_str(cls, v):
        """Convertir les enums en string."""
        if hasattr(v, 'value'):
            return v.value
        return str(v) if v else v


# ============================================================================
# SUBSCRIPTION
# ============================================================================

class SubscriptionCreate(BaseModel):
    """Création d'un abonnement."""
    plan: str
    billing_cycle: str = "MONTHLY"
    price_monthly: float | None = None
    price_yearly: float | None = None
    discount_percent: float = 0
    starts_at: datetime
    ends_at: datetime | None = None
    is_trial: bool = False
    auto_renew: bool = True
    payment_method: str | None = None


class SubscriptionUpdate(BaseModel):
    """Mise à jour d'un abonnement."""
    plan: str | None = None
    billing_cycle: str | None = None
    auto_renew: bool | None = None
    payment_method: str | None = None


class SubscriptionResponse(BaseModel):
    """Réponse abonnement."""
    id: UUID
    tenant_id: str
    plan: str
    billing_cycle: str
    price_monthly: float | None
    price_yearly: float | None
    discount_percent: float
    starts_at: datetime
    ends_at: datetime | None
    next_billing_at: datetime | None
    is_active: bool
    is_trial: bool
    auto_renew: bool
    payment_method: str | None
    last_payment_at: datetime | None
    last_payment_amount: float | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# MODULES
# ============================================================================

class ModuleActivation(BaseModel):
    """Activation d'un module."""
    module_code: str = Field(..., min_length=2, max_length=10)
    module_name: str | None = None
    config: dict[str, Any] | None = None
    limits: dict[str, Any] | None = None


class ModuleDeactivation(BaseModel):
    """Désactivation d'un module."""
    module_code: str


class TenantModuleResponse(BaseModel):
    """Réponse module tenant."""
    id: UUID
    tenant_id: str
    module_code: str
    module_name: str | None
    module_version: str | None
    status: str
    config: dict[str, Any] | None
    limits: dict[str, Any] | None
    activated_at: datetime
    deactivated_at: datetime | None

    @field_validator("config", "limits", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# INVITATION
# ============================================================================

class TenantInvitationCreate(BaseModel):
    """Création d'invitation tenant."""
    email: str = Field(..., min_length=5, max_length=255)
    tenant_id: str | None = None
    tenant_name: str | None = None
    plan: str = "STARTER"
    proposed_role: str = "TENANT_ADMIN"
    expires_in_days: int = 7


class TenantInvitationResponse(BaseModel):
    """Réponse invitation."""
    id: UUID
    token: str
    email: str
    tenant_id: str | None
    tenant_name: str | None
    plan: str | None
    proposed_role: str
    status: str
    expires_at: datetime
    accepted_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# USAGE
# ============================================================================

class TenantUsageResponse(BaseModel):
    """Réponse utilisation."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True, from_attributes=True)

    id: UUID
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
    module_usage: dict[str, int] | None

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
    two_factor_required: bool | None = None
    session_timeout_minutes: int | None = None
    password_expiry_days: int | None = None
    ip_whitelist: list[str] | None = None
    notify_admin_on_signup: bool | None = None
    notify_admin_on_error: bool | None = None
    daily_digest_enabled: bool | None = None
    webhook_url: str | None = None
    api_rate_limit: int | None = None
    auto_backup_enabled: bool | None = None
    backup_retention_days: int | None = None
    custom_settings: dict[str, Any] | None = None


class TenantSettingsResponse(BaseModel):
    """Réponse paramètres."""
    id: UUID
    tenant_id: str
    two_factor_required: bool
    session_timeout_minutes: int
    password_expiry_days: int
    ip_whitelist: list[str] | None
    notify_admin_on_signup: bool
    notify_admin_on_error: bool
    daily_digest_enabled: bool
    webhook_url: str | None
    api_rate_limit: int
    auto_backup_enabled: bool
    backup_retention_days: int
    custom_settings: dict[str, Any] | None
    updated_at: datetime

    @field_validator("ip_whitelist", "custom_settings", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ONBOARDING
# ============================================================================

class OnboardingStepUpdate(BaseModel):
    """Mise à jour d'une étape onboarding."""
    step: str
    completed: bool = True


class TenantOnboardingResponse(BaseModel):
    """Réponse onboarding."""
    id: UUID
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
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ÉVÉNEMENTS
# ============================================================================

class TenantEventResponse(BaseModel):
    """Réponse événement."""
    id: UUID
    tenant_id: str
    event_type: str
    event_data: dict[str, Any] | None
    description: str | None
    actor_id: int | None
    actor_email: str | None
    actor_ip: str | None
    created_at: datetime

    @field_validator("event_data", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# DASHBOARD
# ============================================================================

class TenantDashboardResponse(BaseModel):
    """Dashboard tenant."""
    tenant: TenantResponse
    subscription: SubscriptionResponse | None
    modules: list[TenantModuleResponse]
    onboarding: TenantOnboardingResponse | None
    usage_today: TenantUsageResponse | None
    recent_events: list[TenantEventResponse]


# ============================================================================
# PROVISIONING
# ============================================================================

class ProvisionTenantRequest(BaseModel):
    """Demande de provisioning complet."""
    tenant: TenantCreate
    admin_email: str
    admin_first_name: str
    admin_last_name: str
    admin_password: str | None = None  # Auto-généré si absent
    modules: list[str] = ["T0", "T1", "T2", "T3", "T4"]
    country_pack: str = "FR"
    send_welcome_email: bool = True


class ProvisionTenantResponse(BaseModel):
    """Réponse provisioning."""
    tenant: TenantResponse
    admin_user_id: UUID
    admin_email: str
    temporary_password: str | None
    activated_modules: list[str]
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
    tenants_by_plan: dict[str, int]
    tenants_by_country: dict[str, int]
    new_tenants_this_month: int
    revenue_this_month: float
