"""
AZALS MODULE T0 - Schémas Pydantic IAM
======================================

Schémas de validation pour les endpoints IAM.
"""


import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

# ============================================================================
# SCHÉMAS UTILISATEUR
# ============================================================================

class UserBase(BaseModel):
    """Base utilisateur."""
    email: EmailStr
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=50)
    job_title: str | None = Field(None, max_length=200)
    department: str | None = Field(None, max_length=200)
    locale: str = Field(default="fr", max_length=10)
    timezone: str = Field(default="Europe/Paris", max_length=50)


class UserCreate(UserBase):
    """Création utilisateur."""
    password: str = Field(..., min_length=12, max_length=128)
    username: str | None = Field(None, max_length=100)
    role_codes: list[str] | None = None
    group_codes: list[str] | None = None

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
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=50)
    job_title: str | None = Field(None, max_length=200)
    department: str | None = Field(None, max_length=200)
    locale: str | None = Field(None, max_length=10)
    timezone: str | None = Field(None, max_length=50)
    is_active: bool | None = None


class UserResponse(BaseModel):
    """Réponse utilisateur."""
    id: str
    tenant_id: str
    email: str
    username: str | None
    first_name: str | None
    last_name: str | None
    display_name: str | None
    phone: str | None
    job_title: str | None
    department: str | None
    locale: str
    timezone: str
    is_active: bool
    is_verified: bool
    is_locked: bool
    mfa_enabled: bool
    created_at: datetime
    last_login_at: datetime | None
    roles: list[str] = []  # Codes des rôles
    groups: list[str] = []  # Codes des groupes

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Liste paginée d'utilisateurs."""
    items: list[UserResponse]
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
    description: str | None = None
    level: int = Field(default=5, ge=0, le=10)


class RoleCreate(RoleBase):
    """Création rôle."""
    parent_code: str | None = None
    permission_codes: list[str] | None = None
    incompatible_role_codes: list[str] | None = None
    requires_approval: bool = False
    max_users: int | None = None


class RoleUpdate(BaseModel):
    """Mise à jour rôle."""
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    level: int | None = Field(None, ge=0, le=10)
    is_active: bool | None = None
    requires_approval: bool | None = None
    max_users: int | None = None


class RoleResponse(BaseModel):
    """Réponse rôle."""
    id: str
    tenant_id: str
    code: str
    name: str
    description: str | None
    level: int
    parent_id: str | None
    is_system: bool
    is_active: bool
    is_assignable: bool
    requires_approval: bool
    max_users: int | None
    user_count: int = 0
    permissions: list[str] = []  # Codes des permissions
    incompatible_roles: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleListResponse(BaseModel):
    """Liste des rôles."""
    items: list[RoleResponse]
    total: int


class RoleAssignment(BaseModel):
    """Attribution de rôle."""
    user_id: str
    role_code: str
    expires_at: datetime | None = None


class RoleBulkAssignment(BaseModel):
    """Attribution de rôles en masse."""
    user_ids: list[int]
    role_codes: list[str]
    expires_at: datetime | None = None


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
    description: str | None = None


class PermissionCreate(PermissionBase):
    """Création permission."""
    is_dangerous: bool = False


class PermissionResponse(BaseModel):
    """Réponse permission."""
    id: str
    tenant_id: str
    code: str
    module: str
    resource: str
    action: str
    name: str
    description: str | None
    is_system: bool
    is_active: bool
    is_dangerous: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PermissionListResponse(BaseModel):
    """Liste des permissions."""
    items: list[PermissionResponse]
    total: int


class PermissionCheck(BaseModel):
    """Vérification de permission."""
    permission_code: str
    user_id: str | None = None  # Si absent, utilisateur courant


class PermissionCheckResult(BaseModel):
    """Résultat vérification permission."""
    permission_code: str
    granted: bool
    source: str | None = None  # "role:ADMIN" ou "group:MANAGERS"


# ============================================================================
# SCHÉMAS GROUPE
# ============================================================================

class GroupBase(BaseModel):
    """Base groupe."""
    code: str = Field(..., max_length=50, pattern=r'^[A-Z][A-Z0-9_]*$')
    name: str = Field(..., max_length=200)
    description: str | None = None


class GroupCreate(GroupBase):
    """Création groupe."""
    role_codes: list[str] | None = None


class GroupUpdate(BaseModel):
    """Mise à jour groupe."""
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    is_active: bool | None = None


class GroupResponse(BaseModel):
    """Réponse groupe."""
    id: str
    tenant_id: str
    code: str
    name: str
    description: str | None
    is_active: bool
    user_count: int = 0
    roles: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class GroupListResponse(BaseModel):
    """Liste des groupes."""
    items: list[GroupResponse]
    total: int


class GroupMembership(BaseModel):
    """Gestion membres groupe."""
    user_ids: list[int]


# ============================================================================
# SCHÉMAS SESSION
# ============================================================================

class SessionResponse(BaseModel):
    """Réponse session."""
    id: str
    token_jti: str
    ip_address: str | None
    user_agent: str | None
    status: str
    created_at: datetime
    expires_at: datetime
    last_activity_at: datetime
    is_current: bool = False

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    """Liste des sessions."""
    items: list[SessionResponse]
    total: int


class SessionRevoke(BaseModel):
    """Révocation de session."""
    session_ids: list[str] | None = None  # Si absent, toutes sauf courante
    reason: str | None = None


# ============================================================================
# SCHÉMAS INVITATION
# ============================================================================

class InvitationCreate(BaseModel):
    """Création invitation."""
    email: EmailStr
    role_codes: list[str] | None = None
    group_codes: list[str] | None = None
    expires_in_hours: int = Field(default=72, ge=1, le=720)  # Max 30 jours


class InvitationResponse(BaseModel):
    """Réponse invitation."""
    id: str
    tenant_id: str
    email: str
    status: str
    roles_to_assign: list[str] = []
    groups_to_assign: list[str] = []
    created_at: datetime
    expires_at: datetime
    invited_by: str
    accepted_at: datetime | None

    model_config = {"from_attributes": True}


class InvitationAccept(BaseModel):
    """Acceptation invitation."""
    token: str
    password: str = Field(..., min_length=12, max_length=128)
    first_name: str | None = None
    last_name: str | None = None


# ============================================================================
# SCHÉMAS MFA
# ============================================================================

class MFASetupResponse(BaseModel):
    """Réponse configuration MFA."""
    secret: str
    qr_code_uri: str
    backup_codes: list[str]


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
    mfa_code: str | None = None
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
    min_length: int | None = Field(None, ge=8, le=128)
    require_uppercase: bool | None = None
    require_lowercase: bool | None = None
    require_numbers: bool | None = None
    require_special: bool | None = None
    password_history_count: int | None = Field(None, ge=0, le=24)
    password_expires_days: int | None = Field(None, ge=0, le=365)
    max_failed_attempts: int | None = Field(None, ge=3, le=10)
    lockout_duration_minutes: int | None = Field(None, ge=5, le=1440)


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
    id: str
    tenant_id: str
    action: str
    entity_type: str
    entity_id: str | None
    actor_id: str | None
    actor_ip: str | None
    success: bool
    error_message: str | None
    details: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Liste des logs audit."""
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AuditLogFilter(BaseModel):
    """Filtres pour logs audit."""
    action: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    actor_id: str | None = None
    success: bool | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
