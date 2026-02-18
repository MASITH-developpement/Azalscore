"""
AZALS MODULE T0 - Modèles IAM
=============================

Modèles SQLAlchemy pour la gestion des identités et accès.
Tous les modèles héritent de TenantMixin pour l'isolation multi-tenant.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.types import UniversalUUID
from app.db import Base

# ============================================================================
# ENUMS
# ============================================================================

class RoleCode(str, enum.Enum):
    """Codes des rôles prédéfinis AZALS."""
    SUPER_ADMIN = "SUPER_ADMIN"
    TENANT_ADMIN = "TENANT_ADMIN"
    DIRIGEANT = "DIRIGEANT"
    DAF = "DAF"
    DRH = "DRH"
    RESPONSABLE_COMMERCIAL = "RESPONSABLE_COMMERCIAL"
    RESPONSABLE_ACHATS = "RESPONSABLE_ACHATS"
    RESPONSABLE_PRODUCTION = "RESPONSABLE_PRODUCTION"
    COMPTABLE = "COMPTABLE"
    COMMERCIAL = "COMMERCIAL"
    ACHETEUR = "ACHETEUR"
    MAGASINIER = "MAGASINIER"
    RH = "RH"
    CONSULTANT = "CONSULTANT"
    AUDITEUR = "AUDITEUR"
    CUSTOM = "CUSTOM"  # Pour rôles personnalisés


class PermissionAction(str, enum.Enum):
    """Actions possibles sur une ressource."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    VALIDATE = "validate"
    EXPORT = "export"
    ADMIN = "admin"
    ALL = "*"


class SessionStatus(str, enum.Enum):
    """Statut d'une session utilisateur."""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    LOGGED_OUT = "LOGGED_OUT"


class InvitationStatus(str, enum.Enum):
    """Statut d'une invitation utilisateur."""
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class MFAType(str, enum.Enum):
    """Types de MFA supportés."""
    TOTP = "TOTP"
    EMAIL = "EMAIL"
    SMS = "SMS"


# ============================================================================
# TABLES D'ASSOCIATION
# ============================================================================

# Association User <-> Role (many-to-many)
user_roles = Table(
    'iam_user_roles',
    Base.metadata,
    Column('id', UniversalUUID(), primary_key=True, default=uuid.uuid4),
    Column('tenant_id', String(255), nullable=False, index=True),
    Column('user_id', UniversalUUID(), ForeignKey('iam_users.id', ondelete='CASCADE'), nullable=False),
    Column('role_id', UniversalUUID(), ForeignKey('iam_roles.id', ondelete='CASCADE'), nullable=False),
    Column('granted_by', UniversalUUID(), nullable=True),  # Audit only, no FK to avoid ambiguity
    Column('granted_at', DateTime, default=datetime.utcnow, nullable=False),
    Column('expires_at', DateTime, nullable=True),
    Column('is_active', Boolean, default=True, nullable=False),
    UniqueConstraint('tenant_id', 'user_id', 'role_id', name='uq_user_role_tenant'),
    Index('idx_user_roles_tenant', 'tenant_id'),
    Index('idx_user_roles_user', 'user_id'),
    Index('idx_user_roles_role', 'role_id'),
)

# Association Role <-> Permission (many-to-many)
role_permissions = Table(
    'iam_role_permissions',
    Base.metadata,
    Column('id', UniversalUUID(), primary_key=True, default=uuid.uuid4),
    Column('tenant_id', String(255), nullable=False, index=True),
    Column('role_id', UniversalUUID(), ForeignKey('iam_roles.id', ondelete='CASCADE'), nullable=False),
    Column('permission_id', UniversalUUID(), ForeignKey('iam_permissions.id', ondelete='CASCADE'), nullable=False),
    Column('granted_at', DateTime, default=datetime.utcnow, nullable=False),
    UniqueConstraint('tenant_id', 'role_id', 'permission_id', name='uq_role_permission_tenant'),
    Index('idx_role_permissions_tenant', 'tenant_id'),
    Index('idx_role_permissions_role', 'role_id'),
)

# Association User <-> Group (many-to-many)
user_groups = Table(
    'iam_user_groups',
    Base.metadata,
    Column('id', UniversalUUID(), primary_key=True, default=uuid.uuid4),
    Column('tenant_id', String(255), nullable=False, index=True),
    Column('user_id', UniversalUUID(), ForeignKey('iam_users.id', ondelete='CASCADE'), nullable=False),
    Column('group_id', UniversalUUID(), ForeignKey('iam_groups.id', ondelete='CASCADE'), nullable=False),
    Column('added_by', UniversalUUID(), nullable=True),  # Audit only, no FK to avoid ambiguity
    Column('added_at', DateTime, default=datetime.utcnow, nullable=False),
    UniqueConstraint('tenant_id', 'user_id', 'group_id', name='uq_user_group_tenant'),
    Index('idx_user_groups_tenant', 'tenant_id'),
    Index('idx_user_groups_user', 'user_id'),
    Index('idx_user_groups_group', 'group_id'),
)

# Association Group <-> Role (many-to-many)
group_roles = Table(
    'iam_group_roles',
    Base.metadata,
    Column('id', UniversalUUID(), primary_key=True, default=uuid.uuid4),
    Column('tenant_id', String(255), nullable=False, index=True),
    Column('group_id', UniversalUUID(), ForeignKey('iam_groups.id', ondelete='CASCADE'), nullable=False),
    Column('role_id', UniversalUUID(), ForeignKey('iam_roles.id', ondelete='CASCADE'), nullable=False),
    Column('granted_at', DateTime, default=datetime.utcnow, nullable=False),
    UniqueConstraint('tenant_id', 'group_id', 'role_id', name='uq_group_role_tenant'),
    Index('idx_group_roles_tenant', 'tenant_id'),
)


# ============================================================================
# MODÈLES PRINCIPAUX
# ============================================================================

class IAMUser(Base):
    """
    Utilisateur IAM étendu.
    Étend le modèle User existant avec profil complet.
    """
    __tablename__ = "iam_users"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identifiants
    email = Column(String(255), nullable=False, index=True)
    username = Column(String(100), nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profil
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    display_name = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    locale = Column(String(10), default='fr', nullable=False)
    timezone = Column(String(50), default='Europe/Paris', nullable=False)

    # Fonction/Poste
    job_title = Column(String(200), nullable=True)
    department = Column(String(200), nullable=True)
    employee_id = Column(String(50), nullable=True)

    # Préférences UI
    default_view = Column(String(50), nullable=True)  # Vue par défaut après connexion (cockpit, admin, saisie, etc.)

    # Statut
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    lock_reason = Column(String(500), nullable=True)
    locked_at = Column(DateTime, nullable=True)
    locked_until = Column(DateTime, nullable=True)

    # Sécurité
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    last_failed_login = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    must_change_password = Column(Boolean, default=False, nullable=False)

    # MFA
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_type = Column(Enum(MFAType), nullable=True)
    mfa_secret = Column(String(255), nullable=True)  # Chiffré
    mfa_backup_codes = Column(Text, nullable=True)  # JSON chiffré

    # Protection système (compte créateur)
    is_system_account = Column(Boolean, default=False, nullable=False)  # Compte système
    is_protected = Column(Boolean, default=False, nullable=False)  # Empêche rétrogradation/suppression
    created_via = Column(String(50), default='api', nullable=True)  # api, cli, migration, bootstrap

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(50), nullable=True)

    # Relations (simples car plus d'ambiguïté FK après suppression des FK audit)
    roles = relationship("IAMRole", secondary=user_roles, back_populates="users")
    groups = relationship("IAMGroup", secondary=user_groups, back_populates="users")
    sessions = relationship("IAMSession", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'email', name='uq_iam_user_tenant_email'),
        Index('idx_iam_users_tenant', 'tenant_id'),
        Index('idx_iam_users_email', 'email'),
        Index('idx_iam_users_active', 'tenant_id', 'is_active'),
    )


class IAMRole(Base):
    """
    Rôle avec permissions.
    Les rôles peuvent être hiérarchiques (parent_id).
    """
    __tablename__ = "iam_roles"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Hiérarchie
    level = Column(Integer, default=5, nullable=False)  # 0=max, 5=min
    parent_id = Column(UniversalUUID(), ForeignKey('iam_roles.id'), nullable=True)

    # Configuration
    is_system = Column(Boolean, default=False, nullable=False)  # Non modifiable
    is_active = Column(Boolean, default=True, nullable=False)
    is_assignable = Column(Boolean, default=True, nullable=False)  # Peut être attribué
    max_users = Column(Integer, nullable=True)  # Limite utilisateurs par rôle

    # Protection système (super_admin)
    is_protected = Column(Boolean, default=False, nullable=False)  # Empêche modification
    is_deletable = Column(Boolean, default=True, nullable=False)  # Empêche suppression
    max_assignments = Column(Integer, nullable=True)  # Limite d'utilisateurs avec ce rôle

    # Séparation des pouvoirs
    incompatible_roles = Column(Text, nullable=True)  # JSON: ["ROLE1", "ROLE2"]
    requires_approval = Column(Boolean, default=False, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)

    # Relations (simples car plus d'ambiguïté FK)
    users = relationship("IAMUser", secondary=user_roles, back_populates="roles")
    permissions = relationship("IAMPermission", secondary=role_permissions, back_populates="roles")
    children = relationship("IAMRole", backref="parent", remote_side=[id])
    groups = relationship("IAMGroup", secondary=group_roles, back_populates="roles")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_iam_role_tenant_code'),
        Index('idx_iam_roles_tenant', 'tenant_id'),
        Index('idx_iam_roles_code', 'code'),
        Index('idx_iam_roles_level', 'level'),
    )


class IAMPermission(Base):
    """
    Permission granulaire.
    Format: module.ressource.action
    """
    __tablename__ = "iam_permissions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification (module.resource.action)
    code = Column(String(200), nullable=False)  # ex: treasury.forecast.create
    module = Column(String(50), nullable=False)  # ex: treasury
    resource = Column(String(100), nullable=False)  # ex: forecast
    action = Column(Enum(PermissionAction), nullable=False)  # ex: create

    # Métadonnées
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Configuration
    is_system = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_dangerous = Column(Boolean, default=False, nullable=False)  # Nécessite confirmation

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    roles = relationship("IAMRole", secondary=role_permissions, back_populates="permissions")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_iam_permission_code'),
        Index('idx_iam_permissions_tenant', 'tenant_id'),
        Index('idx_iam_permissions_module', 'module'),
        Index('idx_iam_permissions_code', 'code'),
    )


class IAMGroup(Base):
    """
    Groupe d'utilisateurs.
    Simplifie l'attribution de rôles à plusieurs utilisateurs.
    """
    __tablename__ = "iam_groups"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Configuration
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)

    # Relations (simples car plus d'ambiguïté FK)
    users = relationship("IAMUser", secondary=user_groups, back_populates="groups")
    roles = relationship("IAMRole", secondary=group_roles, back_populates="groups")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_iam_group_code'),
        Index('idx_iam_groups_tenant', 'tenant_id'),
    )


class IAMSession(Base):
    """
    Session utilisateur pour tracking et révocation.
    """
    __tablename__ = "iam_sessions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    user_id = Column(UniversalUUID(), ForeignKey('iam_users.id', ondelete='CASCADE'), nullable=False)

    # Token
    token_jti = Column(String(100), unique=True, nullable=False, index=True)  # JWT ID
    refresh_token_hash = Column(String(255), nullable=True)

    # Contexte
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_info = Column(Text, nullable=True)  # JSON

    # Statut
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_activity_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(String(200), nullable=True)

    # Relations
    user = relationship("IAMUser", back_populates="sessions")

    __table_args__ = (
        Index('idx_iam_sessions_tenant', 'tenant_id'),
        Index('idx_iam_sessions_user', 'user_id'),
        Index('idx_iam_sessions_token', 'token_jti'),
        Index('idx_iam_sessions_status', 'status'),
        Index('idx_iam_sessions_expires', 'expires_at'),
    )


class IAMTokenBlacklist(Base):
    """
    Liste noire des tokens révoqués.
    Permet l'invalidation immédiate de tokens JWT.
    """
    __tablename__ = "iam_token_blacklist"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    token_jti = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False)
    blacklisted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)  # Pour nettoyage auto
    reason = Column(String(200), nullable=True)

    __table_args__ = (
        Index('idx_token_blacklist_jti', 'token_jti'),
        Index('idx_token_blacklist_expires', 'expires_at'),
    )


class IAMInvitation(Base):
    """
    Invitation utilisateur par email.
    """
    __tablename__ = "iam_invitations"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Destinataire
    email = Column(String(255), nullable=False)

    # Token invitation
    token = Column(String(255), unique=True, nullable=False, index=True)

    # Configuration
    roles_to_assign = Column(Text, nullable=True)  # JSON: ["ROLE1", "ROLE2"]
    groups_to_assign = Column(Text, nullable=True)  # JSON: ["GROUP1"]

    # Statut
    status = Column(Enum(InvitationStatus), default=InvitationStatus.PENDING, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    invited_by = Column(UniversalUUID(), nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    accepted_user_id = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index('idx_iam_invitations_tenant', 'tenant_id'),
        Index('idx_iam_invitations_email', 'email'),
        Index('idx_iam_invitations_token', 'token'),
        Index('idx_iam_invitations_status', 'status'),
    )


class IAMPasswordPolicy(Base):
    """
    Politique de mot de passe par tenant.
    """
    __tablename__ = "iam_password_policies"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), unique=True, nullable=False, index=True)

    # Complexité
    min_length = Column(Integer, default=12, nullable=False)
    require_uppercase = Column(Boolean, default=True, nullable=False)
    require_lowercase = Column(Boolean, default=True, nullable=False)
    require_numbers = Column(Boolean, default=True, nullable=False)
    require_special = Column(Boolean, default=True, nullable=False)

    # Historique
    password_history_count = Column(Integer, default=5, nullable=False)  # N derniers interdits

    # Expiration
    password_expires_days = Column(Integer, default=90, nullable=False)  # 0 = jamais

    # Verrouillage
    max_failed_attempts = Column(Integer, default=5, nullable=False)
    lockout_duration_minutes = Column(Integer, default=30, nullable=False)

    # Audit
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(UniversalUUID(), nullable=True)


class IAMPasswordHistory(Base):
    """
    Historique des mots de passe pour empêcher réutilisation.
    """
    __tablename__ = "iam_password_history"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_password_history_user', 'tenant_id', 'user_id'),
    )


class IAMAuditLog(Base):
    """
    Log d'audit IAM spécifique.
    Complète le journal général avec détails IAM.
    """
    __tablename__ = "iam_audit_logs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Action
    action = Column(String(100), nullable=False)  # LOGIN, LOGOUT, ROLE_ASSIGNED, etc.
    entity_type = Column(String(50), nullable=False)  # USER, ROLE, PERMISSION, etc.
    entity_id = Column(UniversalUUID(), nullable=True)

    # Acteur
    actor_id = Column(UniversalUUID(), nullable=True)  # NULL si système
    actor_ip = Column(String(50), nullable=True)
    actor_user_agent = Column(String(500), nullable=True)

    # Détails
    old_values = Column(Text, nullable=True)  # JSON
    new_values = Column(Text, nullable=True)  # JSON
    details = Column(Text, nullable=True)

    # Résultat
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)

    __table_args__ = (
        Index('idx_iam_audit_tenant', 'tenant_id'),
        Index('idx_iam_audit_action', 'action'),
        Index('idx_iam_audit_entity', 'entity_type', 'entity_id'),
        Index('idx_iam_audit_actor', 'actor_id'),
        Index('idx_iam_audit_created', 'created_at'),
    )


class IAMRateLimit(Base):
    """
    Tracking rate limiting pour protection brute-force.
    """
    __tablename__ = "iam_rate_limits"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)

    # Identification
    key = Column(String(255), nullable=False, index=True)  # IP ou user:action
    action = Column(String(50), nullable=False)  # login, password_reset, etc.

    # Compteur
    count = Column(Integer, default=1, nullable=False)
    window_start = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Blocage
    blocked_until = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint('key', 'action', name='uq_rate_limit_key_action'),
        Index('idx_rate_limit_key', 'key'),
        Index('idx_rate_limit_blocked', 'blocked_until'),
    )
