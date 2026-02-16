"""
AZALS MODULE T0 - Group Service
================================

Gestion des groupes.
"""

import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import and_

from app.modules.iam.models import IAMGroup, IAMUser, user_groups, group_roles
from app.modules.iam.schemas import GroupCreate
from .base import BaseIAMService

logger = logging.getLogger(__name__)


class GroupService(BaseIAMService[IAMGroup]):
    """Service de gestion des groupes."""

    model = IAMGroup

    def create(self, data: GroupCreate, created_by: int | None = None) -> IAMGroup:
        """Crée un nouveau groupe."""
        existing = self.get_by_code(data.code)
        if existing:
            raise ValueError(f"Le groupe {data.code} existe déjà")

        group = IAMGroup(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            is_active=True,
            created_by=created_by
        )

        self.db.add(group)
        self._audit_log("GROUP_CREATED", "GROUP", None, created_by,
                       new_values={"code": data.code})
        self.db.commit()
        self.db.refresh(group)
        return group

    def get(self, group_id: UUID) -> Optional[IAMGroup]:
        """Récupère un groupe par ID."""
        return self._base_query().filter(IAMGroup.id == group_id).first()

    def get_by_code(self, code: str) -> Optional[IAMGroup]:
        """Récupère un groupe par code."""
        return self._base_query().filter(IAMGroup.code == code).first()

    def list(self, include_inactive: bool = False) -> List[IAMGroup]:
        """Liste tous les groupes."""
        query = self._base_query()
        if not include_inactive:
            query = query.filter(IAMGroup.is_active == True)
        return query.order_by(IAMGroup.code).all()

    def add_user(self, user_id: UUID, group_code: str, added_by: int | None = None) -> bool:
        """Ajoute un utilisateur à un groupe."""
        group = self.get_by_code(group_code)
        if not group:
            raise ValueError(f"Groupe {group_code} non trouvé")

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
            joined_at=datetime.utcnow(),
            added_by=added_by
        ))

        self._audit_log("USER_ADDED_TO_GROUP", "USER", user_id, added_by,
                       new_values={"group_code": group_code})
        self.db.commit()
        return True

    def remove_user(self, user_id: UUID, group_code: str, removed_by: int | None = None) -> bool:
        """Retire un utilisateur d'un groupe."""
        group = self.get_by_code(group_code)
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
            self._audit_log("USER_REMOVED_FROM_GROUP", "USER", user_id, removed_by,
                           old_values={"group_code": group_code})
            self.db.commit()
            return True
        return False

    def get_group_members(self, group_id: UUID) -> List[IAMUser]:
        """Récupère les membres d'un groupe."""
        return self.db.query(IAMUser).join(user_groups).filter(
            user_groups.c.group_id == group_id,
            user_groups.c.tenant_id == self.tenant_id
        ).all()

    def get_user_groups(self, user_id: UUID) -> List[IAMGroup]:
        """Récupère les groupes d'un utilisateur."""
        return self.db.query(IAMGroup).join(user_groups).filter(
            user_groups.c.user_id == user_id,
            user_groups.c.tenant_id == self.tenant_id
        ).all()
