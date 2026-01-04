"""
AZALS MODULE T0 - Schémas Pydantic IAM
======================================

Schémas de validation pour les endpoints IAM.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


# ============================================================================
# SCHÉMAS UTILISATEUR
# ============================================================================

class UserBase(BaseModel):
    """Base utilisateur."""
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    job_title: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=200)
    locale: str = Field(default="fr", max_length=10)
    timezone: str = Field(default="Europe/Paris", max_length=50)


class UserCreate(UserBase):
    """Création utilisateur."""
    password: str = Field(..., min_length=12, max_length=128)
    username: Optional[str] = Field(None, max_length=100)
    role_codes: Optional[List[str]] = None
    group_codes: Optional[List[str]] = None

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validation complexité mot de passe."""
        if len(v) < 12:
            raise ValueError('Le mot de passe doit contenir au moins 12 caractères')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule')
        if not re.search(r'[a-z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une minuscule')
        if not re.search(r'\d', v):
            raise ValueError('Le mot de passe doit contenir au moins un chiffre')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Le mot de passe doit contenir au moins un caractère spécial')
        return v


class UserUpdate(BaseModel):
    """Mise à jour utilisateur."""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    job_title: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=200)
    locale: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Réponse utilisateur."""
    id: int
    tenant_id: str
    email: str
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    display_name: Optional[str]
    phone: Optional[str]
    job_title: Optional[str]
    department: Optional[str]
    locale: str
    timezone: str
    is_active: bool
    is_verified: bool
    is_locked: bool
    mfa_enabled: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    roles: List[str] = []  # Codes des rôles
    groups: List[str] = []  # Codes des groupes

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Liste paginée d'utilisateurs."""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
    pages: int


class PasswordChange(BaseModel):
    """Changement de mot de passe."""
    current_password: str
    new_password: str = Field(..., min_length=12, max_length=128)

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 12:
            raise ValueError('Le mot de passe doit contenir au moins 12 caractères')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule')
        if not re.search(r'[a-z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une minuscule')
        if not re.search(r'\d', v):
            raise ValueError('Le mot de passe doit contenir au moins un chiffre')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Le mot de passe doit contenir au moins un caractère spécial')
        return v


class PasswordReset(BaseModel):
    """Demande de réinitialisation mot de passe."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirmation réinitialisation mot de passe."""
    token: str
    new_password: str = Field(..., min_length=12, max_length=128)


# ============================================================================
# SCHÉMAS RÔLE
# ============================================================================

class RoleBase(BaseModel):
    """Base rôle."""
    code: str = Field(..., max_length=50, pattern=r'^[A-Z][A-Z0-9_]*$')
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    level: int = Field(default=5, ge=0, le=10)


class RoleCreate(RoleBase):
    """Création rôle."""
    parent_code: Optional[str] = None
    permission_codes: Optional[List[str]] = None
    incompatible_role_codes: Optional[List[str]] = None
    requires_approval: bool = False
    max_users: Optional[int] = None


class RoleUpdate(BaseModel):
    """Mise à jour rôle."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    level: Optional[int] = Field(None, ge=0, le=10)
    is_active: Optional[bool] = None
    requires_approval: Optional[bool] = None
    max_users: Optional[int] = None


class RoleResponse(BaseModel):
    """Réponse rôle."""
    id: int
    tenant_id: str
    code: str
    name: str
    description: Optional[str]
    level: int
    parent_id: Optional[int]
    is_system: bool
    is_active: bool
    is_assignable: bool
    requires_approval: bool
    max_users: Optional[int]
    user_count: int = 0
    permissions: List[str] = []  # Codes des permissions
    incompatible_roles: List[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleListResponse(BaseModel):
    """Liste des rôles."""
    items: List[RoleResponse]
    total: int


class RoleAssignment(BaseModel):
    """Attribution de rôle."""
    user_id: int
    role_code: str
    expires_at: Optional[datetime] = None


class RoleBulkAssignment(BaseModel):
    """Attribution de rôles en masse."""
    user_ids: List[int]
    role_codes: List[str]
    expires_at: Optional[datetime] = None


# ============================================================================
# SCHÉMAS PERMISSION
# ============================================================================

class PermissionBase(BaseModel):
    """Base permission."""
    code: str = Field(..., max_length=200)
    module: str = Field(..., max_length=50)
    resource: str = Field(..., max_length=100)
    action: str  # PermissionAction
    name: str = Field(..., max_length=200)
    description: Optional[str] = None


class PermissionCreate(PermissionBase):
    """Création permission."""
    is_dangerous: bool = False


class PermissionResponse(BaseModel):
    """Réponse permission."""
    id: int
    tenant_id: str
    code: str
    module: str
    resource: str
    action: str
    name: str
    description: Optional[str]
    is_system: bool
    is_active: bool
    is_dangerous: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PermissionListResponse(BaseModel):
    """Liste des permissions."""
    items: List[PermissionResponse]
    total: int


class PermissionCheck(BaseModel):
    """Vérification de permission."""
    permission_code: str
    user_id: Optional[int] = None  # Si absent, utilisateur courant


class PermissionCheckResult(BaseModel):
    """Résultat vérification permission."""
    permission_code: str
    granted: bool
    source: Optional[str] = None  # "role:ADMIN" ou "group:MANAGERS"


# ============================================================================
# SCHÉMAS GROUPE
# ============================================================================

class GroupBase(BaseModel):
    """Base groupe."""
    code: str = Field(..., max_length=50, pattern=r'^[A-Z][A-Z0-9_]*$')
    name: str = Field(..., max_length=200)
    description: Optional[str] = None


class GroupCreate(GroupBase):
    """Création groupe."""
    role_codes: Optional[List[str]] = None


class GroupUpdate(BaseModel):
    """Mise à jour groupe."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class GroupResponse(BaseModel):
    """Réponse groupe."""
    id: int
    tenant_id: str
    code: str
    name: str
    description: Optional[str]
    is_active: bool
    user_count: int = 0
    roles: List[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class GroupListResponse(BaseModel):
    """Liste des groupes."""
    items: List[GroupResponse]
    total: int


class GroupMembership(BaseModel):
    """Gestion membres groupe."""
    user_ids: List[int]


# ============================================================================
# SCHÉMAS SESSION
# ============================================================================

class SessionResponse(BaseModel):
    """Réponse session."""
    id: int
    token_jti: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    status: str
    created_at: datetime
    expires_at: datetime
    last_activity_at: datetime
    is_current: bool = False

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    """Liste des sessions."""
    items: List[SessionResponse]
    total: int


class SessionRevoke(BaseModel):
    """Révocation de session."""
    session_ids: Optional[List[int]] = None  # Si absent, toutes sauf courante
    reason: Optional[str] = None


# ============================================================================
# SCHÉMAS INVITATION
# ============================================================================

class InvitationCreate(BaseModel):
    """Création invitation."""
    email: EmailStr
    role_codes: Optional[List[str]] = None
    group_codes: Optional[List[str]] = None
    expires_in_hours: int = Field(default=72, ge=1, le=720)  # Max 30 jours


class InvitationResponse(BaseModel):
    """Réponse invitation."""
    id: int
    tenant_id: str
    email: str
    status: str
    roles_to_assign: List[str] = []
    groups_to_assign: List[str] = []
    created_at: datetime
    expires_at: datetime
    invited_by: int
    accepted_at: Optional[datetime]

    model_config = {"from_attributes": True}


class InvitationAccept(BaseModel):
    """Acceptation invitation."""
    token: str
    password: str = Field(..., min_length=12, max_length=128)
    first_name: Optional[str] = None
    last_name: Optional[str] = None


# ============================================================================
# SCHÉMAS MFA
# ============================================================================

class MFASetupResponse(BaseModel):
    """Réponse configuration MFA."""
    secret: str
    qr_code_uri: str
    backup_codes: List[str]


class MFAVerify(BaseModel):
    """Vérification code MFA."""
    code: str = Field(..., min_length=6, max_length=6)


class MFADisable(BaseModel):
    """Désactivation MFA."""
    password: str
    code: str = Field(..., min_length=6, max_length=6)


# ============================================================================
# SCHÉMAS AUTHENTIFICATION
# ============================================================================

class LoginRequest(BaseModel):
    """Requête de connexion."""
    email: EmailStr
    password: str
    mfa_code: Optional[str] = None
    remember_me: bool = False


class LoginResponse(BaseModel):
    """Réponse de connexion."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Secondes
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Requête de rafraîchissement token."""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Réponse rafraîchissement token."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutRequest(BaseModel):
    """Requête de déconnexion."""
    all_sessions: bool = False  # Déconnecter toutes les sessions


# ============================================================================
# SCHÉMAS POLITIQUE MOT DE PASSE
# ============================================================================

class PasswordPolicyUpdate(BaseModel):
    """Mise à jour politique mot de passe."""
    min_length: Optional[int] = Field(None, ge=8, le=128)
    require_uppercase: Optional[bool] = None
    require_lowercase: Optional[bool] = None
    require_numbers: Optional[bool] = None
    require_special: Optional[bool] = None
    password_history_count: Optional[int] = Field(None, ge=0, le=24)
    password_expires_days: Optional[int] = Field(None, ge=0, le=365)
    max_failed_attempts: Optional[int] = Field(None, ge=3, le=10)
    lockout_duration_minutes: Optional[int] = Field(None, ge=5, le=1440)


class PasswordPolicyResponse(BaseModel):
    """Réponse politique mot de passe."""
    tenant_id: str
    min_length: int
    require_uppercase: bool
    require_lowercase: bool
    require_numbers: bool
    require_special: bool
    password_history_count: int
    password_expires_days: int
    max_failed_attempts: int
    lockout_duration_minutes: int

    model_config = {"from_attributes": True}


# ============================================================================
# SCHÉMAS AUDIT
# ============================================================================

class AuditLogResponse(BaseModel):
    """Réponse log audit."""
    id: int
    tenant_id: str
    action: str
    entity_type: str
    entity_id: Optional[int]
    actor_id: Optional[int]
    actor_ip: Optional[str]
    success: bool
    error_message: Optional[str]
    details: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Liste des logs audit."""
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AuditLogFilter(BaseModel):
    """Filtres pour logs audit."""
    action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    actor_id: Optional[int] = None
    success: Optional[bool] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
