"""
AZALS MODULE T0 - Service IAM
=============================

Logique métier pour la gestion des identités et accès.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import secrets
import json
import uuid
import pyotp
import bcrypt
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.config import get_settings
from app.core.security import create_access_token
from .models import (
    IAMUser, IAMRole, IAMPermission, IAMGroup, IAMSession,
    IAMTokenBlacklist, IAMInvitation, IAMPasswordPolicy,
    IAMPasswordHistory, IAMAuditLog, IAMRateLimit,
    user_roles, role_permissions, user_groups, group_roles,
    SessionStatus, InvitationStatus, MFAType, PermissionAction
)
from .schemas import (
    UserCreate, UserUpdate, RoleCreate, RoleUpdate,
    PermissionCreate, GroupCreate
)

settings = get_settings()


class IAMService:
    """Service principal IAM."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # ========================================================================
    # GESTION UTILISATEURS
    # ========================================================================

    def create_user(
        self,
        data: UserCreate,
        created_by: Optional[int] = None
    ) -> IAMUser:
        """Crée un nouvel utilisateur."""
        # Vérifier email unique
        existing = self.db.query(IAMUser).filter(
            IAMUser.tenant_id == self.tenant_id,
            IAMUser.email == data.email
        ).first()
        if existing:
            raise ValueError("Email déjà utilisé")

        # Hash du mot de passe
        password_hash = self._hash_password(data.password)

        # Créer l'utilisateur
        user = IAMUser(
            tenant_id=self.tenant_id,
            email=data.email,
            username=data.username,
            password_hash=password_hash,
            first_name=data.first_name,
            last_name=data.last_name,
            display_name=f"{data.first_name or ''} {data.last_name or ''}".strip() or data.email,
            phone=data.phone,
            job_title=data.job_title,
            department=data.department,
            locale=data.locale,
            timezone=data.timezone,
            created_by=created_by,
            password_changed_at=datetime.utcnow()
        )

        self.db.add(user)
        self.db.flush()

        # Attribuer les rôles
        if data.role_codes:
            for code in data.role_codes:
                self.assign_role_to_user(user.id, code, created_by)

        # Attribuer les groupes
        if data.group_codes:
            for code in data.group_codes:
                self.add_user_to_group(user.id, code, created_by)

        # Sauvegarder le mot de passe dans l'historique
        self._save_password_history(user.id, password_hash)

        # Audit
        self._audit_log("USER_CREATED", "USER", user.id, created_by, new_values={
            "email": user.email,
            "roles": data.role_codes,
            "groups": data.group_codes
        })

        self.db.commit()
        return user

    def get_user(self, user_id: int) -> Optional[IAMUser]:
        """Récupère un utilisateur par ID."""
        return self.db.query(IAMUser).filter(
            IAMUser.tenant_id == self.tenant_id,
            IAMUser.id == user_id
        ).first()

    def get_user_by_email(self, email: str) -> Optional[IAMUser]:
        """Récupère un utilisateur par email."""
        return self.db.query(IAMUser).filter(
            IAMUser.tenant_id == self.tenant_id,
            IAMUser.email == email
        ).first()

    def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        role_code: Optional[str] = None
    ) -> Tuple[List[IAMUser], int]:
        """Liste les utilisateurs avec pagination et filtres."""
        query = self.db.query(IAMUser).filter(
            IAMUser.tenant_id == self.tenant_id
        )

        if is_active is not None:
            query = query.filter(IAMUser.is_active == is_active)

        if search:
            search_filter = f"%{search}%"
            query = query.filter(or_(
                IAMUser.email.ilike(search_filter),
                IAMUser.first_name.ilike(search_filter),
                IAMUser.last_name.ilike(search_filter),
                IAMUser.username.ilike(search_filter)
            ))

        if role_code:
            role = self.get_role_by_code(role_code)
            if role:
                query = query.join(user_roles).filter(
                    user_roles.c.role_id == role.id
                )

        total = query.count()
        users = query.order_by(IAMUser.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return users, total

    def update_user(
        self,
        user_id: int,
        data: UserUpdate,
        updated_by: Optional[int] = None
    ) -> IAMUser:
        """Met à jour un utilisateur."""
        user = self.get_user(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")

        old_values = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active
        }

        # Mise à jour des champs
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        # Mise à jour display_name si nom modifié
        if data.first_name or data.last_name:
            user.display_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email

        # Audit
        self._audit_log("USER_UPDATED", "USER", user_id, updated_by,
                       old_values=old_values,
                       new_values=data.model_dump(exclude_unset=True))

        self.db.commit()
        return user

    def delete_user(self, user_id: int, deleted_by: Optional[int] = None) -> bool:
        """Supprime un utilisateur (soft delete via is_active)."""
        user = self.get_user(user_id)
        if not user:
            return False

        user.is_active = False
        user.is_locked = True
        user.lock_reason = "Account deleted"
        user.locked_at = datetime.utcnow()

        # Révoquer toutes les sessions
        self.revoke_all_sessions(user_id, "Account deleted")

        # Audit
        self._audit_log("USER_DELETED", "USER", user_id, deleted_by)

        self.db.commit()
        return True

    def lock_user(
        self,
        user_id: int,
        reason: str,
        duration_minutes: Optional[int] = None,
        locked_by: Optional[int] = None
    ) -> IAMUser:
        """Verrouille un utilisateur."""
        user = self.get_user(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")

        user.is_locked = True
        user.lock_reason = reason
        user.locked_at = datetime.utcnow()

        if duration_minutes:
            user.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)

        # Révoquer toutes les sessions
        self.revoke_all_sessions(user_id, reason)

        # Audit
        self._audit_log("USER_LOCKED", "USER", user_id, locked_by,
                       details={"reason": reason, "duration_minutes": duration_minutes})

        self.db.commit()
        return user

    def unlock_user(self, user_id: int, unlocked_by: Optional[int] = None) -> IAMUser:
        """Déverrouille un utilisateur."""
        user = self.get_user(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")

        user.is_locked = False
        user.lock_reason = None
        user.locked_at = None
        user.locked_until = None
        user.failed_login_attempts = 0

        # Audit
        self._audit_log("USER_UNLOCKED", "USER", user_id, unlocked_by)

        self.db.commit()
        return user

    # ========================================================================
    # GESTION RÔLES
    # ========================================================================

    def create_role(
        self,
        data: RoleCreate,
        created_by: Optional[int] = None
    ) -> IAMRole:
        """Crée un nouveau rôle."""
        # Vérifier code unique
        existing = self.get_role_by_code(data.code)
        if existing:
            raise ValueError(f"Le rôle {data.code} existe déjà")

        # Récupérer parent si spécifié
        parent_id = None
        if data.parent_code:
            parent = self.get_role_by_code(data.parent_code)
            if not parent:
                raise ValueError(f"Rôle parent {data.parent_code} non trouvé")
            parent_id = parent.id

        # Créer le rôle
        role = IAMRole(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            level=data.level,
            parent_id=parent_id,
            requires_approval=data.requires_approval,
            max_users=data.max_users,
            incompatible_roles=json.dumps(data.incompatible_role_codes) if data.incompatible_role_codes else None,
            created_by=created_by
        )

        self.db.add(role)
        self.db.flush()

        # Attribuer les permissions
        if data.permission_codes:
            for code in data.permission_codes:
                self.assign_permission_to_role(role.id, code)

        # Audit
        self._audit_log("ROLE_CREATED", "ROLE", role.id, created_by,
                       new_values={"code": role.code, "permissions": data.permission_codes})

        self.db.commit()
        return role

    def get_role(self, role_id: int) -> Optional[IAMRole]:
        """Récupère un rôle par ID."""
        return self.db.query(IAMRole).filter(
            IAMRole.tenant_id == self.tenant_id,
            IAMRole.id == role_id
        ).first()

    def get_role_by_code(self, code: str) -> Optional[IAMRole]:
        """Récupère un rôle par code."""
        return self.db.query(IAMRole).filter(
            IAMRole.tenant_id == self.tenant_id,
            IAMRole.code == code
        ).first()

    def list_roles(self, include_inactive: bool = False) -> List[IAMRole]:
        """Liste tous les rôles."""
        query = self.db.query(IAMRole).filter(
            IAMRole.tenant_id == self.tenant_id
        )

        if not include_inactive:
            query = query.filter(IAMRole.is_active == True)

        return query.order_by(IAMRole.level, IAMRole.code).all()

    def update_role(
        self,
        role_id: int,
        data: RoleUpdate,
        updated_by: Optional[int] = None
    ) -> IAMRole:
        """Met à jour un rôle."""
        role = self.get_role(role_id)
        if not role:
            raise ValueError("Rôle non trouvé")

        if role.is_system:
            raise ValueError("Impossible de modifier un rôle système")

        old_values = {"name": role.name, "level": role.level}

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(role, field, value)

        # Audit
        self._audit_log("ROLE_UPDATED", "ROLE", role_id, updated_by,
                       old_values=old_values,
                       new_values=data.model_dump(exclude_unset=True))

        self.db.commit()
        return role

    def delete_role(self, role_id: int, deleted_by: Optional[int] = None) -> bool:
        """Supprime un rôle."""
        role = self.get_role(role_id)
        if not role:
            return False

        if role.is_system:
            raise ValueError("Impossible de supprimer un rôle système")

        # Vérifier si des utilisateurs ont ce rôle
        user_count = self.db.query(user_roles).filter(
            user_roles.c.role_id == role_id,
            user_roles.c.tenant_id == self.tenant_id
        ).count()

        if user_count > 0:
            raise ValueError(f"Impossible de supprimer: {user_count} utilisateur(s) ont ce rôle")

        # Audit
        self._audit_log("ROLE_DELETED", "ROLE", role_id, deleted_by,
                       old_values={"code": role.code})

        self.db.delete(role)
        self.db.commit()
        return True

    def assign_role_to_user(
        self,
        user_id: int,
        role_code: str,
        granted_by: Optional[int] = None,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Attribue un rôle à un utilisateur."""
        user = self.get_user(user_id)
        role = self.get_role_by_code(role_code)

        if not user or not role:
            raise ValueError("Utilisateur ou rôle non trouvé")

        if not role.is_assignable:
            raise ValueError(f"Le rôle {role_code} ne peut pas être attribué")

        # Vérifier incompatibilités
        if role.incompatible_roles:
            incompatible = json.loads(role.incompatible_roles)
            user_roles_codes = [r.code for r in user.roles]
            conflicts = set(incompatible) & set(user_roles_codes)
            if conflicts:
                raise ValueError(f"Rôle incompatible avec: {', '.join(conflicts)}")

        # Vérifier limite utilisateurs
        if role.max_users:
            current_count = self.db.query(user_roles).filter(
                user_roles.c.role_id == role.id,
                user_roles.c.tenant_id == self.tenant_id,
                user_roles.c.is_active == True
            ).count()
            if current_count >= role.max_users:
                raise ValueError(f"Limite de {role.max_users} utilisateurs atteinte pour ce rôle")

        # Vérifier si déjà attribué
        existing = self.db.query(user_roles).filter(
            user_roles.c.user_id == user_id,
            user_roles.c.role_id == role.id,
            user_roles.c.tenant_id == self.tenant_id
        ).first()

        if existing:
            return True  # Déjà attribué

        # Attribuer le rôle
        self.db.execute(user_roles.insert().values(
            tenant_id=self.tenant_id,
            user_id=user_id,
            role_id=role.id,
            granted_by=granted_by,
            granted_at=datetime.utcnow(),
            expires_at=expires_at,
            is_active=True
        ))

        # Audit
        self._audit_log("ROLE_ASSIGNED", "USER", user_id, granted_by,
                       new_values={"role_code": role_code, "expires_at": str(expires_at) if expires_at else None})

        self.db.commit()
        return True

    def revoke_role_from_user(
        self,
        user_id: int,
        role_code: str,
        revoked_by: Optional[int] = None
    ) -> bool:
        """Retire un rôle à un utilisateur."""
        role = self.get_role_by_code(role_code)
        if not role:
            return False

        result = self.db.execute(
            user_roles.delete().where(and_(
                user_roles.c.user_id == user_id,
                user_roles.c.role_id == role.id,
                user_roles.c.tenant_id == self.tenant_id
            ))
        )

        if result.rowcount > 0:
            self._audit_log("ROLE_REVOKED", "USER", user_id, revoked_by,
                           old_values={"role_code": role_code})
            self.db.commit()
            return True

        return False

    # ========================================================================
    # GESTION PERMISSIONS
    # ========================================================================

    def create_permission(
        self,
        data: PermissionCreate,
        created_by: Optional[int] = None
    ) -> IAMPermission:
        """Crée une nouvelle permission."""
        # Vérifier code unique
        existing = self.get_permission_by_code(data.code)
        if existing:
            raise ValueError(f"La permission {data.code} existe déjà")

        permission = IAMPermission(
            tenant_id=self.tenant_id,
            code=data.code,
            module=data.module,
            resource=data.resource,
            action=PermissionAction(data.action),
            name=data.name,
            description=data.description,
            is_dangerous=data.is_dangerous
        )

        self.db.add(permission)

        # Audit
        self._audit_log("PERMISSION_CREATED", "PERMISSION", None, created_by,
                       new_values={"code": data.code})

        self.db.commit()
        return permission

    def get_permission_by_code(self, code: str) -> Optional[IAMPermission]:
        """Récupère une permission par code."""
        return self.db.query(IAMPermission).filter(
            IAMPermission.tenant_id == self.tenant_id,
            IAMPermission.code == code
        ).first()

    def list_permissions(self, module: Optional[str] = None) -> List[IAMPermission]:
        """Liste les permissions."""
        query = self.db.query(IAMPermission).filter(
            IAMPermission.tenant_id == self.tenant_id,
            IAMPermission.is_active == True
        )

        if module:
            query = query.filter(IAMPermission.module == module)

        return query.order_by(IAMPermission.module, IAMPermission.resource, IAMPermission.action).all()

    def assign_permission_to_role(self, role_id: int, permission_code: str) -> bool:
        """Attribue une permission à un rôle."""
        permission = self.get_permission_by_code(permission_code)
        if not permission:
            raise ValueError(f"Permission {permission_code} non trouvée")

        # Vérifier si déjà attribuée
        existing = self.db.query(role_permissions).filter(
            role_permissions.c.role_id == role_id,
            role_permissions.c.permission_id == permission.id,
            role_permissions.c.tenant_id == self.tenant_id
        ).first()

        if existing:
            return True

        self.db.execute(role_permissions.insert().values(
            tenant_id=self.tenant_id,
            role_id=role_id,
            permission_id=permission.id,
            granted_at=datetime.utcnow()
        ))

        self.db.commit()
        return True

    def check_permission(
        self,
        user_id: int,
        permission_code: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Vérifie si un utilisateur a une permission.
        Retourne (granted, source) où source indique d'où vient la permission.
        """
        user = self.get_user(user_id)
        if not user or not user.is_active or user.is_locked:
            return False, None

        # Vérifier via rôles directs
        for role in user.roles:
            if not role.is_active:
                continue

            for perm in role.permissions:
                if perm.code == permission_code or perm.action == PermissionAction.ALL:
                    return True, f"role:{role.code}"

                # Wildcard module.resource.*
                if perm.code.endswith(".*"):
                    prefix = perm.code[:-1]
                    if permission_code.startswith(prefix):
                        return True, f"role:{role.code}"

        # Vérifier via groupes
        for group in user.groups:
            if not group.is_active:
                continue

            for role in group.roles:
                if not role.is_active:
                    continue

                for perm in role.permissions:
                    if perm.code == permission_code or perm.action == PermissionAction.ALL:
                        return True, f"group:{group.code}"

        return False, None

    def get_user_permissions(self, user_id: int) -> List[str]:
        """Récupère toutes les permissions d'un utilisateur."""
        user = self.get_user(user_id)
        if not user:
            return []

        permissions = set()

        # Via rôles directs
        for role in user.roles:
            if role.is_active:
                for perm in role.permissions:
                    permissions.add(perm.code)

        # Via groupes
        for group in user.groups:
            if group.is_active:
                for role in group.roles:
                    if role.is_active:
                        for perm in role.permissions:
                            permissions.add(perm.code)

        return sorted(list(permissions))

    # ========================================================================
    # GESTION GROUPES
    # ========================================================================

    def create_group(
        self,
        data: GroupCreate,
        created_by: Optional[int] = None
    ) -> IAMGroup:
        """Crée un nouveau groupe."""
        existing = self.db.query(IAMGroup).filter(
            IAMGroup.tenant_id == self.tenant_id,
            IAMGroup.code == data.code
        ).first()

        if existing:
            raise ValueError(f"Le groupe {data.code} existe déjà")

        group = IAMGroup(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            created_by=created_by
        )

        self.db.add(group)
        self.db.flush()

        # Attribuer les rôles
        if data.role_codes:
            for code in data.role_codes:
                self.assign_role_to_group(group.id, code)

        # Audit
        self._audit_log("GROUP_CREATED", "GROUP", group.id, created_by,
                       new_values={"code": data.code, "roles": data.role_codes})

        self.db.commit()
        return group

    def get_group(self, group_id: int) -> Optional[IAMGroup]:
        """Récupère un groupe par ID."""
        return self.db.query(IAMGroup).filter(
            IAMGroup.tenant_id == self.tenant_id,
            IAMGroup.id == group_id
        ).first()

    def get_group_by_code(self, code: str) -> Optional[IAMGroup]:
        """Récupère un groupe par code."""
        return self.db.query(IAMGroup).filter(
            IAMGroup.tenant_id == self.tenant_id,
            IAMGroup.code == code
        ).first()

    def list_groups(self) -> List[IAMGroup]:
        """Liste tous les groupes."""
        return self.db.query(IAMGroup).filter(
            IAMGroup.tenant_id == self.tenant_id,
            IAMGroup.is_active == True
        ).order_by(IAMGroup.name).all()

    def add_user_to_group(
        self,
        user_id: int,
        group_code: str,
        added_by: Optional[int] = None
    ) -> bool:
        """Ajoute un utilisateur à un groupe."""
        group = self.get_group_by_code(group_code)
        if not group:
            raise ValueError(f"Groupe {group_code} non trouvé")

        # Vérifier si déjà membre
        existing = self.db.query(user_groups).filter(
            user_groups.c.user_id == user_id,
            user_groups.c.group_id == group.id,
            user_groups.c.tenant_id == self.tenant_id
        ).first()

        if existing:
            return True

        self.db.execute(user_groups.insert().values(
            tenant_id=self.tenant_id,
            user_id=user_id,
            group_id=group.id,
            added_by=added_by,
            added_at=datetime.utcnow()
        ))

        # Audit
        self._audit_log("GROUP_MEMBER_ADDED", "GROUP", group.id, added_by,
                       new_values={"user_id": user_id})

        self.db.commit()
        return True

    def remove_user_from_group(
        self,
        user_id: int,
        group_code: str,
        removed_by: Optional[int] = None
    ) -> bool:
        """Retire un utilisateur d'un groupe."""
        group = self.get_group_by_code(group_code)
        if not group:
            return False

        result = self.db.execute(
            user_groups.delete().where(and_(
                user_groups.c.user_id == user_id,
                user_groups.c.group_id == group.id,
                user_groups.c.tenant_id == self.tenant_id
            ))
        )

        if result.rowcount > 0:
            self._audit_log("GROUP_MEMBER_REMOVED", "GROUP", group.id, removed_by,
                           old_values={"user_id": user_id})
            self.db.commit()
            return True

        return False

    def assign_role_to_group(self, group_id: int, role_code: str) -> bool:
        """Attribue un rôle à un groupe."""
        role = self.get_role_by_code(role_code)
        if not role:
            raise ValueError(f"Rôle {role_code} non trouvé")

        existing = self.db.query(group_roles).filter(
            group_roles.c.group_id == group_id,
            group_roles.c.role_id == role.id,
            group_roles.c.tenant_id == self.tenant_id
        ).first()

        if existing:
            return True

        self.db.execute(group_roles.insert().values(
            tenant_id=self.tenant_id,
            group_id=group_id,
            role_id=role.id,
            granted_at=datetime.utcnow()
        ))

        self.db.commit()
        return True

    # ========================================================================
    # AUTHENTIFICATION
    # ========================================================================

    def authenticate(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[Optional[IAMUser], Optional[str]]:
        """
        Authentifie un utilisateur.
        Retourne (user, error_message).
        """
        # Rate limiting
        if not self._check_rate_limit(f"login:{email}", "login", 5, 300):
            return None, "Trop de tentatives. Réessayez dans 5 minutes."

        user = self.get_user_by_email(email)

        if not user:
            self._increment_rate_limit(f"login:{email}", "login")
            return None, "Email ou mot de passe incorrect"

        # Vérifier verrouillage
        if user.is_locked:
            if user.locked_until and user.locked_until > datetime.utcnow():
                minutes = int((user.locked_until - datetime.utcnow()).total_seconds() / 60) + 1
                return None, f"Compte verrouillé. Réessayez dans {minutes} minute(s)"
            elif user.locked_until and user.locked_until <= datetime.utcnow():
                # Auto-déverrouillage
                user.is_locked = False
                user.locked_until = None
                user.failed_login_attempts = 0

        if not user.is_active:
            return None, "Compte désactivé"

        # Vérifier mot de passe
        if not self._verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            user.last_failed_login = datetime.utcnow()

            # Verrouillage après N tentatives
            policy = self._get_password_policy()
            if user.failed_login_attempts >= policy.max_failed_attempts:
                user.is_locked = True
                user.lock_reason = "Trop de tentatives échouées"
                user.locked_at = datetime.utcnow()
                user.locked_until = datetime.utcnow() + timedelta(minutes=policy.lockout_duration_minutes)

                self._audit_log("USER_LOCKED_AUTO", "USER", user.id, None,
                               details={"reason": "max_failed_attempts"})

            self._audit_log("LOGIN_FAILED", "USER", user.id, None,
                           details={"ip": ip_address, "attempts": user.failed_login_attempts})

            self.db.commit()
            self._increment_rate_limit(f"login:{email}", "login")
            return None, "Email ou mot de passe incorrect"

        # Réinitialiser compteur tentatives
        user.failed_login_attempts = 0
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = ip_address

        self._audit_log("LOGIN_SUCCESS", "USER", user.id, user.id,
                       details={"ip": ip_address})

        self.db.commit()
        return user, None

    def create_session(
        self,
        user: IAMUser,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        remember_me: bool = False
    ) -> Tuple[str, str, IAMSession]:
        """
        Crée une session et génère les tokens.
        Retourne (access_token, refresh_token, session).
        """
        # Générer JTI unique
        jti = str(uuid.uuid4())

        # Durées
        access_expire = timedelta(minutes=30)
        refresh_expire = timedelta(days=7) if remember_me else timedelta(hours=24)

        # Créer access token
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "tenant_id": self.tenant_id,
                "role": user.roles[0].code if user.roles else "USER",
                "jti": jti
            },
            expires_delta=access_expire
        )

        # Créer refresh token
        refresh_token = secrets.token_urlsafe(64)
        refresh_token_hash = self._hash_password(refresh_token)

        # Créer session
        session = IAMSession(
            tenant_id=self.tenant_id,
            user_id=user.id,
            token_jti=jti,
            refresh_token_hash=refresh_token_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            status=SessionStatus.ACTIVE,
            expires_at=datetime.utcnow() + refresh_expire
        )

        self.db.add(session)
        self.db.commit()

        return access_token, refresh_token, session

    def refresh_tokens(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Rafraîchit les tokens.
        Retourne (new_access_token, new_refresh_token, error).
        """
        # Trouver la session avec ce refresh token
        sessions = self.db.query(IAMSession).filter(
            IAMSession.tenant_id == self.tenant_id,
            IAMSession.status == SessionStatus.ACTIVE
        ).all()

        session = None
        for s in sessions:
            if s.refresh_token_hash and self._verify_password(refresh_token, s.refresh_token_hash):
                session = s
                break

        if not session:
            return None, None, "Refresh token invalide"

        if session.expires_at < datetime.utcnow():
            session.status = SessionStatus.EXPIRED
            self.db.commit()
            return None, None, "Session expirée"

        user = self.get_user(session.user_id)
        if not user or not user.is_active or user.is_locked:
            session.status = SessionStatus.REVOKED
            self.db.commit()
            return None, None, "Utilisateur invalide"

        # Générer nouveaux tokens
        new_jti = str(uuid.uuid4())
        access_expire = timedelta(minutes=30)

        new_access_token = create_access_token(
            data={
                "sub": str(user.id),
                "tenant_id": self.tenant_id,
                "role": user.roles[0].code if user.roles else "USER",
                "jti": new_jti
            },
            expires_delta=access_expire
        )

        # Nouveau refresh token
        new_refresh_token = secrets.token_urlsafe(64)
        new_refresh_token_hash = self._hash_password(new_refresh_token)

        # Mettre à jour session
        session.token_jti = new_jti
        session.refresh_token_hash = new_refresh_token_hash
        session.last_activity_at = datetime.utcnow()

        self.db.commit()

        return new_access_token, new_refresh_token, None

    def logout(self, jti: str, all_sessions: bool = False) -> bool:
        """Déconnecte l'utilisateur."""
        if all_sessions:
            # Trouver le user via le JTI courant
            session = self.db.query(IAMSession).filter(
                IAMSession.token_jti == jti,
                IAMSession.tenant_id == self.tenant_id
            ).first()

            if session:
                self.revoke_all_sessions(session.user_id, "Logout all sessions")
        else:
            session = self.db.query(IAMSession).filter(
                IAMSession.token_jti == jti,
                IAMSession.tenant_id == self.tenant_id
            ).first()

            if session:
                session.status = SessionStatus.LOGGED_OUT
                session.revoked_at = datetime.utcnow()

                # Blacklist le token
                self._blacklist_token(jti, session.user_id, session.expires_at)

        self.db.commit()
        return True

    def revoke_all_sessions(self, user_id: int, reason: str) -> int:
        """Révoque toutes les sessions d'un utilisateur."""
        sessions = self.db.query(IAMSession).filter(
            IAMSession.user_id == user_id,
            IAMSession.tenant_id == self.tenant_id,
            IAMSession.status == SessionStatus.ACTIVE
        ).all()

        count = 0
        for session in sessions:
            session.status = SessionStatus.REVOKED
            session.revoked_at = datetime.utcnow()
            session.revoked_reason = reason
            self._blacklist_token(session.token_jti, user_id, session.expires_at)
            count += 1

        self.db.commit()
        return count

    def is_token_blacklisted(self, jti: str) -> bool:
        """Vérifie si un token est blacklisté."""
        return self.db.query(IAMTokenBlacklist).filter(
            IAMTokenBlacklist.token_jti == jti
        ).first() is not None

    # ========================================================================
    # MFA
    # ========================================================================

    def setup_mfa(self, user_id: int) -> Tuple[str, str, List[str]]:
        """
        Configure MFA pour un utilisateur.
        Retourne (secret, qr_uri, backup_codes).
        """
        user = self.get_user(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")

        # Générer secret TOTP
        secret = pyotp.random_base32()

        # Générer backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]

        # Sauvegarder (temporairement, sera confirmé après vérification)
        user.mfa_secret = secret  # TODO: Chiffrer
        user.mfa_backup_codes = json.dumps(backup_codes)  # TODO: Chiffrer
        user.mfa_type = MFAType.TOTP

        # Générer QR code URI
        totp = pyotp.TOTP(secret)
        qr_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="AZALS ERP"
        )

        self.db.commit()

        return secret, qr_uri, backup_codes

    def verify_mfa(self, user_id: int, code: str) -> bool:
        """Vérifie un code MFA et active le MFA si valide."""
        user = self.get_user(user_id)
        if not user or not user.mfa_secret:
            return False

        totp = pyotp.TOTP(user.mfa_secret)

        if totp.verify(code):
            user.mfa_enabled = True
            self._audit_log("MFA_ENABLED", "USER", user_id, user_id)
            self.db.commit()
            return True

        return False

    def check_mfa_code(self, user_id: int, code: str) -> bool:
        """Vérifie un code MFA lors du login."""
        user = self.get_user(user_id)
        if not user or not user.mfa_enabled or not user.mfa_secret:
            return True  # MFA non activé

        # Vérifier code TOTP
        totp = pyotp.TOTP(user.mfa_secret)
        if totp.verify(code):
            return True

        # Vérifier backup codes
        if user.mfa_backup_codes:
            backup_codes = json.loads(user.mfa_backup_codes)
            if code.upper() in backup_codes:
                backup_codes.remove(code.upper())
                user.mfa_backup_codes = json.dumps(backup_codes)
                self.db.commit()
                return True

        return False

    def disable_mfa(self, user_id: int, password: str, code: str) -> bool:
        """Désactive MFA après vérification."""
        user = self.get_user(user_id)
        if not user:
            return False

        if not self._verify_password(password, user.password_hash):
            return False

        if not self.check_mfa_code(user_id, code):
            return False

        user.mfa_enabled = False
        user.mfa_secret = None
        user.mfa_backup_codes = None
        user.mfa_type = None

        self._audit_log("MFA_DISABLED", "USER", user_id, user_id)
        self.db.commit()

        return True

    # ========================================================================
    # MOT DE PASSE
    # ========================================================================

    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """Change le mot de passe d'un utilisateur."""
        user = self.get_user(user_id)
        if not user:
            return False, "Utilisateur non trouvé"

        # Vérifier mot de passe actuel
        if not self._verify_password(current_password, user.password_hash):
            return False, "Mot de passe actuel incorrect"

        # Vérifier politique
        policy = self._get_password_policy()
        valid, error = self._validate_password(new_password, policy)
        if not valid:
            return False, error

        # Vérifier historique
        if not self._check_password_history(user_id, new_password, policy.password_history_count):
            return False, f"Ce mot de passe a été utilisé récemment (derniers {policy.password_history_count})"

        # Mettre à jour
        new_hash = self._hash_password(new_password)
        user.password_hash = new_hash
        user.password_changed_at = datetime.utcnow()
        user.must_change_password = False

        # Sauvegarder dans l'historique
        self._save_password_history(user_id, new_hash)

        # Révoquer toutes les sessions sauf courante
        # (sera fait par l'appelant avec le JTI courant)

        self._audit_log("PASSWORD_CHANGED", "USER", user_id, user_id)
        self.db.commit()

        return True, None

    # ========================================================================
    # INVITATIONS
    # ========================================================================

    def create_invitation(
        self,
        email: str,
        role_codes: Optional[List[str]] = None,
        group_codes: Optional[List[str]] = None,
        expires_in_hours: int = 72,
        invited_by: int = None
    ) -> IAMInvitation:
        """Crée une invitation."""
        # Vérifier email pas déjà utilisé
        existing_user = self.get_user_by_email(email)
        if existing_user:
            raise ValueError("Un compte existe déjà avec cet email")

        # Générer token
        token = secrets.token_urlsafe(32)

        invitation = IAMInvitation(
            tenant_id=self.tenant_id,
            email=email,
            token=token,
            roles_to_assign=json.dumps(role_codes) if role_codes else None,
            groups_to_assign=json.dumps(group_codes) if group_codes else None,
            expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours),
            invited_by=invited_by
        )

        self.db.add(invitation)

        self._audit_log("INVITATION_CREATED", "INVITATION", None, invited_by,
                       new_values={"email": email, "roles": role_codes})

        self.db.commit()

        return invitation

    def accept_invitation(
        self,
        token: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Tuple[Optional[IAMUser], Optional[str]]:
        """Accepte une invitation et crée le compte."""
        invitation = self.db.query(IAMInvitation).filter(
            IAMInvitation.token == token,
            IAMInvitation.tenant_id == self.tenant_id
        ).first()

        if not invitation:
            return None, "Invitation invalide"

        if invitation.status != InvitationStatus.PENDING:
            return None, "Invitation déjà utilisée ou annulée"

        if invitation.expires_at < datetime.utcnow():
            invitation.status = InvitationStatus.EXPIRED
            self.db.commit()
            return None, "Invitation expirée"

        # Créer l'utilisateur
        role_codes = json.loads(invitation.roles_to_assign) if invitation.roles_to_assign else None
        group_codes = json.loads(invitation.groups_to_assign) if invitation.groups_to_assign else None

        user_data = UserCreate(
            email=invitation.email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role_codes=role_codes,
            group_codes=group_codes
        )

        try:
            user = self.create_user(user_data, created_by=invitation.invited_by)
            user.is_verified = True  # Vérifié via invitation

            invitation.status = InvitationStatus.ACCEPTED
            invitation.accepted_at = datetime.utcnow()
            invitation.accepted_user_id = user.id

            self.db.commit()

            return user, None

        except ValueError as e:
            return None, str(e)

    # ========================================================================
    # MÉTHODES PRIVÉES
    # ========================================================================

    def _hash_password(self, password: str) -> str:
        """Hash un mot de passe avec bcrypt."""
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Vérifie un mot de passe."""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed.encode('utf-8')
        )

    def _get_password_policy(self) -> IAMPasswordPolicy:
        """Récupère la politique de mot de passe."""
        policy = self.db.query(IAMPasswordPolicy).filter(
            IAMPasswordPolicy.tenant_id == self.tenant_id
        ).first()

        if not policy:
            # Créer politique par défaut
            policy = IAMPasswordPolicy(tenant_id=self.tenant_id)
            self.db.add(policy)
            self.db.commit()

        return policy

    def _validate_password(
        self,
        password: str,
        policy: IAMPasswordPolicy
    ) -> Tuple[bool, Optional[str]]:
        """Valide un mot de passe selon la politique."""
        import re

        if len(password) < policy.min_length:
            return False, f"Minimum {policy.min_length} caractères requis"

        if policy.require_uppercase and not re.search(r'[A-Z]', password):
            return False, "Au moins une majuscule requise"

        if policy.require_lowercase and not re.search(r'[a-z]', password):
            return False, "Au moins une minuscule requise"

        if policy.require_numbers and not re.search(r'\d', password):
            return False, "Au moins un chiffre requis"

        if policy.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Au moins un caractère spécial requis"

        return True, None

    def _check_password_history(
        self,
        user_id: int,
        new_password: str,
        history_count: int
    ) -> bool:
        """Vérifie que le mot de passe n'est pas dans l'historique."""
        if history_count == 0:
            return True

        history = self.db.query(IAMPasswordHistory).filter(
            IAMPasswordHistory.tenant_id == self.tenant_id,
            IAMPasswordHistory.user_id == user_id
        ).order_by(IAMPasswordHistory.created_at.desc()).limit(history_count).all()

        for entry in history:
            if self._verify_password(new_password, entry.password_hash):
                return False

        return True

    def _save_password_history(self, user_id: int, password_hash: str) -> None:
        """Sauvegarde un mot de passe dans l'historique."""
        entry = IAMPasswordHistory(
            tenant_id=self.tenant_id,
            user_id=user_id,
            password_hash=password_hash
        )
        self.db.add(entry)

    def _blacklist_token(self, jti: str, user_id: int, expires_at: datetime) -> None:
        """Ajoute un token à la blacklist."""
        blacklist = IAMTokenBlacklist(
            tenant_id=self.tenant_id,
            token_jti=jti,
            user_id=user_id,
            expires_at=expires_at
        )
        self.db.add(blacklist)

    def _check_rate_limit(
        self,
        key: str,
        action: str,
        max_attempts: int,
        window_seconds: int
    ) -> bool:
        """Vérifie le rate limiting."""
        entry = self.db.query(IAMRateLimit).filter(
            IAMRateLimit.key == key,
            IAMRateLimit.action == action
        ).first()

        if not entry:
            return True

        # Vérifier si bloqué
        if entry.blocked_until and entry.blocked_until > datetime.utcnow():
            return False

        # Vérifier fenêtre
        window_start = datetime.utcnow() - timedelta(seconds=window_seconds)
        if entry.window_start < window_start:
            # Réinitialiser
            entry.count = 0
            entry.window_start = datetime.utcnow()
            entry.blocked_until = None
            self.db.commit()
            return True

        return entry.count < max_attempts

    def _increment_rate_limit(self, key: str, action: str) -> None:
        """Incrémente le compteur rate limit."""
        entry = self.db.query(IAMRateLimit).filter(
            IAMRateLimit.key == key,
            IAMRateLimit.action == action
        ).first()

        if not entry:
            entry = IAMRateLimit(
                key=key,
                action=action,
                count=1,
                window_start=datetime.utcnow()
            )
            self.db.add(entry)
        else:
            entry.count += 1

        self.db.commit()

    def _audit_log(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[int],
        actor_id: Optional[int],
        old_values: dict = None,
        new_values: dict = None,
        details: dict = None,
        success: bool = True,
        error_message: str = None
    ) -> None:
        """Crée une entrée d'audit."""
        log = IAMAuditLog(
            tenant_id=self.tenant_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            details=json.dumps(details) if details else None,
            success=success,
            error_message=error_message
        )
        self.db.add(log)


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def get_iam_service(db: Session, tenant_id: str) -> IAMService:
    """Factory pour créer un service IAM."""
    return IAMService(db, tenant_id)
