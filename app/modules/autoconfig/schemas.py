"""
AZALS MODULE T1 - Schémas Pydantic Configuration Automatique
=============================================================

Schémas de validation pour les endpoints de configuration automatique.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

# ============================================================================
# SCHÉMAS PROFILS
# ============================================================================

class ProfileBase(BaseModel):
    """Base profil métier."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: str | None = None
    level: str
    hierarchy_order: int = Field(default=5, ge=0, le=10)


class ProfileCreate(ProfileBase):
    """Création profil."""
    title_patterns: list[str] | None = None
    department_patterns: list[str] | None = None
    default_roles: list[str]
    default_permissions: list[str] | None = None
    default_modules: list[str] | None = None
    max_data_access_level: int = Field(default=5, ge=0, le=5)
    requires_mfa: bool = False
    requires_training: bool = True
    priority: int = Field(default=100, ge=1)


class ProfileUpdate(BaseModel):
    """Mise à jour profil."""
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    title_patterns: list[str] | None = None
    department_patterns: list[str] | None = None
    default_roles: list[str] | None = None
    default_permissions: list[str] | None = None
    default_modules: list[str] | None = None
    max_data_access_level: int | None = Field(None, ge=0, le=5)
    requires_mfa: bool | None = None
    requires_training: bool | None = None
    is_active: bool | None = None
    priority: int | None = Field(None, ge=1)


class ProfileResponse(BaseModel):
    """Réponse profil."""
    id: int
    tenant_id: str
    code: str
    name: str
    description: str | None
    level: str
    hierarchy_order: int
    title_patterns: list[str]
    department_patterns: list[str]
    default_roles: list[str]
    default_permissions: list[str]
    default_modules: list[str]
    max_data_access_level: int
    requires_mfa: bool
    requires_training: bool
    is_active: bool
    is_system: bool
    priority: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileListResponse(BaseModel):
    """Liste des profils."""
    items: list[ProfileResponse]
    total: int


class ProfileDetectionRequest(BaseModel):
    """Demande de détection de profil."""
    job_title: str
    department: str | None = None


class ProfileDetectionResponse(BaseModel):
    """Réponse détection de profil."""
    detected: bool
    profile: ProfileResponse | None = None
    confidence: float = 0.0


# ============================================================================
# SCHÉMAS ATTRIBUTIONS
# ============================================================================

class ProfileAssignmentResponse(BaseModel):
    """Réponse attribution de profil."""
    id: int
    tenant_id: str
    user_id: int
    profile_id: int
    profile_code: str
    profile_name: str
    job_title: str | None
    department: str | None
    manager_id: int | None
    is_active: bool
    is_auto: bool
    assigned_at: datetime
    assigned_by: int | None

    model_config = {"from_attributes": True}


class ManualAssignmentRequest(BaseModel):
    """Demande d'attribution manuelle."""
    user_id: int
    profile_code: str
    job_title: str | None = None
    department: str | None = None


class AutoAssignmentRequest(BaseModel):
    """Demande d'attribution automatique."""
    user_id: int
    job_title: str
    department: str | None = None
    manager_id: int | None = None


class EffectiveConfigResponse(BaseModel):
    """Configuration effective d'un utilisateur."""
    profile_code: str | None
    profile_name: str | None
    roles: list[str]
    permissions: list[str]
    modules: list[str]
    requires_mfa: bool
    data_access_level: int
    overrides_applied: int


# ============================================================================
# SCHÉMAS OVERRIDES
# ============================================================================

class OverrideRequest(BaseModel):
    """Demande d'override."""
    user_id: int
    override_type: str  # EXECUTIVE, IT_ADMIN, TEMPORARY, EMERGENCY
    reason: str = Field(..., min_length=10)
    business_justification: str | None = None
    added_roles: list[str] | None = None
    removed_roles: list[str] | None = None
    added_permissions: list[str] | None = None
    removed_permissions: list[str] | None = None
    added_modules: list[str] | None = None
    removed_modules: list[str] | None = None
    expires_at: datetime | None = None


class OverrideResponse(BaseModel):
    """Réponse override."""
    id: int
    tenant_id: str
    user_id: int
    override_type: str
    status: str
    added_roles: list[str] | None
    removed_roles: list[str] | None
    added_permissions: list[str] | None
    removed_permissions: list[str] | None
    added_modules: list[str] | None
    removed_modules: list[str] | None
    reason: str
    business_justification: str | None
    starts_at: datetime | None
    expires_at: datetime | None
    requested_by: int
    requested_at: datetime
    approved_by: int | None
    approved_at: datetime | None
    rejected_by: int | None
    rejected_at: datetime | None
    rejection_reason: str | None

    model_config = {"from_attributes": True}


class OverrideListResponse(BaseModel):
    """Liste des overrides."""
    items: list[OverrideResponse]
    total: int


class OverrideApprovalRequest(BaseModel):
    """Demande d'approbation override."""
    override_id: int


class OverrideRejectionRequest(BaseModel):
    """Demande de rejet override."""
    override_id: int
    rejection_reason: str = Field(..., min_length=10)


# ============================================================================
# SCHÉMAS ONBOARDING
# ============================================================================

class OnboardingCreate(BaseModel):
    """Création onboarding."""
    email: str
    first_name: str | None = None
    last_name: str | None = None
    job_title: str
    department: str | None = None
    manager_id: int | None = None
    start_date: datetime
    profile_override: int | None = None  # ID profil si override


class OnboardingResponse(BaseModel):
    """Réponse onboarding."""
    id: int
    tenant_id: str
    user_id: int | None
    email: str
    first_name: str | None
    last_name: str | None
    job_title: str
    department: str | None
    manager_id: int | None
    start_date: datetime
    detected_profile_id: int | None
    detected_profile_code: str | None
    profile_override: int | None
    status: str
    steps_completed: dict
    welcome_email_sent: bool
    manager_notified: bool
    it_notified: bool
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class OnboardingListResponse(BaseModel):
    """Liste des onboardings."""
    items: list[OnboardingResponse]
    total: int


class OnboardingExecutionResult(BaseModel):
    """Résultat exécution onboarding."""
    steps: list[str]
    errors: list[str]


# ============================================================================
# SCHÉMAS OFFBOARDING
# ============================================================================

class OffboardingCreate(BaseModel):
    """Création offboarding."""
    user_id: int
    departure_date: datetime
    departure_type: str  # resignation, termination, end_of_contract
    transfer_to_user_id: int | None = None
    transfer_notes: str | None = None


class OffboardingResponse(BaseModel):
    """Réponse offboarding."""
    id: int
    tenant_id: str
    user_id: int
    departure_date: datetime
    departure_type: str
    transfer_to_user_id: int | None
    transfer_notes: str | None
    status: str
    steps_completed: dict
    account_deactivated: bool
    access_revoked: bool
    data_archived: bool
    data_deleted: bool
    manager_notified: bool
    it_notified: bool
    team_notified: bool
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class OffboardingListResponse(BaseModel):
    """Liste des offboardings."""
    items: list[OffboardingResponse]
    total: int


class OffboardingExecutionResult(BaseModel):
    """Résultat exécution offboarding."""
    steps: list[str]
    errors: list[str]


# ============================================================================
# SCHÉMAS LOGS
# ============================================================================

class AutoConfigLogResponse(BaseModel):
    """Réponse log configuration automatique."""
    id: int
    tenant_id: str
    action: str
    entity_type: str
    entity_id: int | None
    user_id: int | None
    source: str
    triggered_by: int | None
    success: bool
    error_message: str | None
    details: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AutoConfigLogListResponse(BaseModel):
    """Liste des logs."""
    items: list[AutoConfigLogResponse]
    total: int
    page: int
    page_size: int
