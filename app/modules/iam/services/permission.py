"""
AZALS MODULE T0 - Permission Service
=====================================

Gestion des permissions.
"""

import logging
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from app.modules.iam.models import IAMPermission, IAMRole, role_permissions, PermissionAction
from app.modules.iam.schemas import PermissionCreate
from .base import BaseIAMService

logger = logging.getLogger(__name__)


class PermissionService(BaseIAMService[IAMPermission]):
    """Service de gestion des permissions."""

    model = IAMPermission

    def create(self, data: PermissionCreate, created_by: int | None = None) -> IAMPermission:
        """Crée une nouvelle permission."""
        existing = self.get_by_code(data.code)
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
        self._audit_log("PERMISSION_CREATED", "PERMISSION", None, created_by,
                       new_values={"code": data.code})
        self.db.commit()
        return permission

    def get_by_code(self, code: str) -> Optional[IAMPermission]:
        """Récupère une permission par code."""
        return self._base_query().filter(IAMPermission.code == code).first()

    def list(self, module: str | None = None) -> List[IAMPermission]:
        """Liste les permissions."""
        query = self._base_query().filter(IAMPermission.is_active == True)

        if module:
            query = query.filter(IAMPermission.module == module)

        return query.order_by(
            IAMPermission.module,
            IAMPermission.resource,
            IAMPermission.action
        ).all()

    def assign_to_role(self, role_id: UUID, permission_code: str) -> bool:
        """Attribue une permission à un rôle."""
        permission = self.get_by_code(permission_code)
        if not permission:
            raise ValueError(f"Permission {permission_code} non trouvée")

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

    def revoke_from_role(self, role_id: UUID, permission_code: str) -> bool:
        """Retire une permission d'un rôle."""
        permission = self.get_by_code(permission_code)
        if not permission:
            return False

        result = self.db.execute(
            role_permissions.delete().where(
                role_permissions.c.role_id == role_id,
                role_permissions.c.permission_id == permission.id,
                role_permissions.c.tenant_id == self.tenant_id
            )
        )

        if result.rowcount > 0:
            self.db.commit()
            return True
        return False

    def check_user_permission(self, user_id: UUID, permission_code: str) -> Tuple[bool, str | None]:
        """Vérifie si un utilisateur a une permission."""
        from app.modules.iam.models import IAMUser, user_roles

        user = self.db.query(IAMUser).filter(
            IAMUser.tenant_id == self.tenant_id,
            IAMUser.id == user_id
        ).first()

        if not user:
            return False, "Utilisateur non trouvé"

        if not user.is_active:
            return False, "Utilisateur inactif"

        if user.is_locked:
            return False, "Utilisateur verrouillé"

        # Récupérer les rôles actifs de l'utilisateur
        roles = self.db.query(IAMRole).join(user_roles).filter(
            user_roles.c.user_id == user_id,
            user_roles.c.tenant_id == self.tenant_id,
            user_roles.c.is_active == True
        ).all()

        # Admin bypass
        for role in roles:
            if role.code in ['ADMIN', 'SUPERADMIN', 'admin', 'super_admin']:
                return True, None

        # Vérifier la permission dans les rôles
        permission = self.get_by_code(permission_code)
        if not permission:
            return False, f"Permission {permission_code} non trouvée"

        for role in roles:
            has_perm = self.db.query(role_permissions).filter(
                role_permissions.c.role_id == role.id,
                role_permissions.c.permission_id == permission.id,
                role_permissions.c.tenant_id == self.tenant_id
            ).first()
            if has_perm:
                return True, None

        return False, f"Permission {permission_code} non accordée"

    def get_role_permissions(self, role_id: UUID) -> List[IAMPermission]:
        """Récupère les permissions d'un rôle."""
        return self.db.query(IAMPermission).join(role_permissions).filter(
            role_permissions.c.role_id == role_id,
            role_permissions.c.tenant_id == self.tenant_id
        ).all()
