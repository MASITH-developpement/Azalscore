"""
AZALS MODULE T0 - Role Service
===============================

Gestion des rôles.
"""

import json
import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import and_

from app.modules.iam.models import IAMRole, IAMUser, user_roles, role_permissions
from app.modules.iam.schemas import RoleCreate, RoleUpdate
from .base import BaseIAMService

logger = logging.getLogger(__name__)


class RoleService(BaseIAMService[IAMRole]):
    """Service de gestion des rôles."""

    model = IAMRole

    def create(self, data: RoleCreate, created_by: int | None = None) -> IAMRole:
        """Crée un nouveau rôle."""
        existing = self.get_by_code(data.code)
        if existing:
            raise ValueError(f"Le rôle {data.code} existe déjà")

        parent_id = None
        if data.parent_code:
            parent = self.get_by_code(data.parent_code)
            if not parent:
                raise ValueError(f"Rôle parent {data.parent_code} non trouvé")
            parent_id = parent.id

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

        self._audit_log("ROLE_CREATED", "ROLE", role.id, created_by,
                       new_values={"code": role.code, "permissions": data.permission_codes})

        self.db.commit()
        return role

    def get(self, role_id: UUID) -> Optional[IAMRole]:
        """Récupère un rôle par ID."""
        return self._base_query().filter(IAMRole.id == role_id).first()

    def get_by_code(self, code: str) -> Optional[IAMRole]:
        """Récupère un rôle par code."""
        return self._base_query().filter(IAMRole.code == code).first()

    def list(self, include_inactive: bool = False) -> List[IAMRole]:
        """Liste tous les rôles."""
        query = self._base_query()
        if not include_inactive:
            query = query.filter(IAMRole.is_active == True)
        return query.order_by(IAMRole.level, IAMRole.code).all()

    def update(self, role_id: UUID, data: RoleUpdate, updated_by: int | None = None) -> IAMRole:
        """Met à jour un rôle."""
        role = self.get(role_id)
        if not role:
            raise ValueError("Rôle non trouvé")

        if role.is_system:
            raise ValueError("Impossible de modifier un rôle système")

        if getattr(role, 'is_protected', False):
            raise ValueError(f"Le rôle '{role.code}' est protégé")

        old_values = {"name": role.name, "level": role.level}

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(role, field, value)

        self._audit_log("ROLE_UPDATED", "ROLE", role_id, updated_by,
                       old_values=old_values,
                       new_values=data.model_dump(exclude_unset=True))

        self.db.commit()
        return role

    def delete(self, role_id: UUID, deleted_by: int | None = None) -> bool:
        """Supprime un rôle."""
        role = self.get(role_id)
        if not role:
            return False

        if role.is_system:
            raise ValueError("Impossible de supprimer un rôle système")

        if getattr(role, 'is_deletable', True) is False:
            raise ValueError(f"Le rôle '{role.code}' ne peut pas être supprimé")

        user_count = self.db.query(user_roles).filter(
            user_roles.c.role_id == role_id,
            user_roles.c.tenant_id == self.tenant_id
        ).count()

        if user_count > 0:
            raise ValueError(f"Impossible de supprimer: {user_count} utilisateur(s) ont ce rôle")

        self._audit_log("ROLE_DELETED", "ROLE", role_id, deleted_by,
                       old_values={"code": role.code})

        self.db.delete(role)
        self.db.commit()
        return True

    def assign_to_user(
        self,
        user_id: UUID,
        role_code: str,
        granted_by: int | None = None,
        expires_at: datetime | None = None
    ) -> bool:
        """Attribue un rôle à un utilisateur."""
        logger.info(
            "Role assignment attempt | tenant=%s user_id=%s role=%s",
            self.tenant_id, user_id, role_code
        )

        user = self.db.query(IAMUser).filter(
            IAMUser.tenant_id == self.tenant_id,
            IAMUser.id == user_id
        ).first()
        role = self.get_by_code(role_code)

        if not user or not role:
            raise ValueError("Utilisateur ou rôle non trouvé")

        if not role.is_assignable:
            raise ValueError(f"Le rôle {role_code} ne peut pas être attribué")

        # Vérifier si déjà attribué
        existing = self.db.query(user_roles).filter(
            user_roles.c.user_id == user_id,
            user_roles.c.role_id == role.id,
            user_roles.c.tenant_id == self.tenant_id
        ).first()

        if existing:
            return True

        self.db.execute(user_roles.insert().values(
            tenant_id=self.tenant_id,
            user_id=user_id,
            role_id=role.id,
            granted_by=granted_by,
            granted_at=datetime.utcnow(),
            expires_at=expires_at,
            is_active=True
        ))

        self._audit_log("ROLE_ASSIGNED", "USER", user_id, granted_by,
                       new_values={"role_code": role_code})

        logger.info("Role assigned | tenant=%s user_id=%s role=%s", self.tenant_id, user_id, role_code)
        self.db.commit()
        return True

    def revoke_from_user(self, user_id: UUID, role_code: str, revoked_by: int | None = None) -> bool:
        """Retire un rôle à un utilisateur."""
        role = self.get_by_code(role_code)
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

    def get_user_roles(self, user_id: UUID) -> List[IAMRole]:
        """Récupère les rôles d'un utilisateur."""
        return self.db.query(IAMRole).join(user_roles).filter(
            user_roles.c.user_id == user_id,
            user_roles.c.tenant_id == self.tenant_id,
            user_roles.c.is_active == True
        ).all()
