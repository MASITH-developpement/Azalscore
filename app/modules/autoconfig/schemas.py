"""
AZALS MODULE T1 - Schémas Pydantic Configuration Automatique
=============================================================

Schémas de validation pour les endpoints de configuration automatique.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================================================
# SCHÉMAS PROFILS
# ============================================================================

class ProfileBase(BaseModel):
    """Base profil métier."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    level: str
    hierarchy_order: int = Field(default=5, ge=0, le=10)


class ProfileCreate(ProfileBase):
    """Création profil."""
    title_patterns: Optional[List[str]] = None
    department_patterns: Optional[List[str]] = None
    default_roles: List[str]
    default_permissions: Optional[List[str]] = None
    default_modules: Optional[List[str]] = None
    max_data_access_level: int = Field(default=5, ge=0, le=5)
    requires_mfa: bool = False
    requires_training: bool = True
    priority: int = Field(default=100, ge=1)


class ProfileUpdate(BaseModel):
    """Mise à jour profil."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    title_patterns: Optional[List[str]] = None
    department_patterns: Optional[List[str]] = None
    default_roles: Optional[List[str]] = None
    default_permissions: Optional[List[str]] = None
    default_modules: Optional[List[str]] = None
    max_data_access_level: Optional[int] = Field(None, ge=0, le=5)
    requires_mfa: Optional[bool] = None
    requires_training: Optional[bool] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1)


class ProfileResponse(BaseModel):
    """Réponse profil."""
    id: int
    tenant_id: str
    code: str
    name: str
    description: Optional[str]
    level: str
    hierarchy_order: int
    title_patterns: List[str]
    department_patterns: List[str]
    default_roles: List[str]
    default_permissions: List[str]
    default_modules: List[str]
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
    items: List[ProfileResponse]
    total: int


class ProfileDetectionRequest(BaseModel):
    """Demande de détection de profil."""
    job_title: str
    department: Optional[str] = None


class ProfileDetectionResponse(BaseModel):
    """Réponse détection de profil."""
    detected: bool
    profile: Optional[ProfileResponse] = None
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
    job_title: Optional[str]
    department: Optional[str]
    manager_id: Optional[int]
    is_active: bool
    is_auto: bool
    assigned_at: datetime
    assigned_by: Optional[int]

    model_config = {"from_attributes": True}


class ManualAssignmentRequest(BaseModel):
    """Demande d'attribution manuelle."""
    user_id: int
    profile_code: str
    job_title: Optional[str] = None
    department: Optional[str] = None


class AutoAssignmentRequest(BaseModel):
    """Demande d'attribution automatique."""
    user_id: int
    job_title: str
    department: Optional[str] = None
    manager_id: Optional[int] = None


class EffectiveConfigResponse(BaseModel):
    """Configuration effective d'un utilisateur."""
    profile_code: Optional[str]
    profile_name: Optional[str]
    roles: List[str]
    permissions: List[str]
    modules: List[str]
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
    business_justification: Optional[str] = None
    added_roles: Optional[List[str]] = None
    removed_roles: Optional[List[str]] = None
    added_permissions: Optional[List[str]] = None
    removed_permissions: Optional[List[str]] = None
    added_modules: Optional[List[str]] = None
    removed_modules: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


class OverrideResponse(BaseModel):
    """Réponse override."""
    id: int
    tenant_id: str
    user_id: int
    override_type: str
    status: str
    added_roles: Optional[List[str]]
    removed_roles: Optional[List[str]]
    added_permissions: Optional[List[str]]
    removed_permissions: Optional[List[str]]
    added_modules: Optional[List[str]]
    removed_modules: Optional[List[str]]
    reason: str
    business_justification: Optional[str]
    starts_at: Optional[datetime]
    expires_at: Optional[datetime]
    requested_by: int
    requested_at: datetime
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    rejected_by: Optional[int]
    rejected_at: Optional[datetime]
    rejection_reason: Optional[str]

    model_config = {"from_attributes": True}


class OverrideListResponse(BaseModel):
    """Liste des overrides."""
    items: List[OverrideResponse]
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
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    job_title: str
    department: Optional[str] = None
    manager_id: Optional[int] = None
    start_date: datetime
    profile_override: Optional[int] = None  # ID profil si override


class OnboardingResponse(BaseModel):
    """Réponse onboarding."""
    id: int
    tenant_id: str
    user_id: Optional[int]
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    job_title: str
    department: Optional[str]
    manager_id: Optional[int]
    start_date: datetime
    detected_profile_id: Optional[int]
    detected_profile_code: Optional[str]
    profile_override: Optional[int]
    status: str
    steps_completed: dict
    welcome_email_sent: bool
    manager_notified: bool
    it_notified: bool
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class OnboardingListResponse(BaseModel):
    """Liste des onboardings."""
    items: List[OnboardingResponse]
    total: int


class OnboardingExecutionResult(BaseModel):
    """Résultat exécution onboarding."""
    steps: List[str]
    errors: List[str]


# ============================================================================
# SCHÉMAS OFFBOARDING
# ============================================================================

class OffboardingCreate(BaseModel):
    """Création offboarding."""
    user_id: int
    departure_date: datetime
    departure_type: str  # resignation, termination, end_of_contract
    transfer_to_user_id: Optional[int] = None
    transfer_notes: Optional[str] = None


class OffboardingResponse(BaseModel):
    """Réponse offboarding."""
    id: int
    tenant_id: str
    user_id: int
    departure_date: datetime
    departure_type: str
    transfer_to_user_id: Optional[int]
    transfer_notes: Optional[str]
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
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class OffboardingListResponse(BaseModel):
    """Liste des offboardings."""
    items: List[OffboardingResponse]
    total: int


class OffboardingExecutionResult(BaseModel):
    """Résultat exécution offboarding."""
    steps: List[str]
    errors: List[str]


# ============================================================================
# SCHÉMAS LOGS
# ============================================================================

class AutoConfigLogResponse(BaseModel):
    """Réponse log configuration automatique."""
    id: int
    tenant_id: str
    action: str
    entity_type: str
    entity_id: Optional[int]
    user_id: Optional[int]
    source: str
    triggered_by: Optional[int]
    success: bool
    error_message: Optional[str]
    details: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


class AutoConfigLogListResponse(BaseModel):
    """Liste des logs."""
    items: List[AutoConfigLogResponse]
    total: int
    page: int
    page_size: int
