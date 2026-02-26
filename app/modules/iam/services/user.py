"""
AZALS MODULE T0 - User Service
===============================

Gestion des utilisateurs.
"""
from __future__ import annotations


import logging
from datetime import datetime
from typing import Optional, Tuple, List
from uuid import UUID

from sqlalchemy import or_

from app.modules.iam.models import IAMUser, user_roles, user_groups
from app.modules.iam.schemas import UserCreate, UserUpdate
from .base import BaseIAMService

logger = logging.getLogger(__name__)


class UserService(BaseIAMService[IAMUser]):
    """Service de gestion des utilisateurs."""

    model = IAMUser

    def create(self, data: UserCreate, created_by: int | None = None) -> IAMUser:
        """Crée un nouvel utilisateur."""
        logger.info(
            "User creation attempt | tenant=%s email=%s created_by=%s",
            self.tenant_id, data.email, created_by
        )

        # Vérifier email unique
        existing = self.get_by_email(data.email)
        if existing:
            logger.warning(
                "User creation failed | tenant=%s email=%s reason=email_already_used",
                self.tenant_id, data.email
            )
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

        # Sauvegarder le mot de passe dans l'historique
        self._save_password_history(user.id, password_hash)

        # Audit
        self._audit_log("USER_CREATED", "USER", user.id, created_by, new_values={
            "email": user.email,
            "roles": data.role_codes,
            "groups": data.group_codes
        })

        logger.info(
            "User created | tenant=%s user_id=%s email=%s",
            self.tenant_id, user.id, user.email
        )
        self.db.commit()
        return user

    def get(self, user_id: UUID) -> Optional[IAMUser]:
        """Récupère un utilisateur par ID."""
        return self._base_query().filter(IAMUser.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[IAMUser]:
        """Récupère un utilisateur par email."""
        return self._base_query().filter(IAMUser.email == email).first()

    def get_by_username(self, username: str) -> Optional[IAMUser]:
        """Récupère un utilisateur par username."""
        return self._base_query().filter(IAMUser.username == username).first()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
        search: str | None = None,
        role_code: str | None = None
    ) -> Tuple[List[IAMUser], int]:
        """Liste les utilisateurs avec pagination et filtres."""
        query = self._base_query()

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
            from app.modules.iam.models import IAMRole
            role = self.db.query(IAMRole).filter(
                IAMRole.tenant_id == self.tenant_id,
                IAMRole.code == role_code
            ).first()
            if role:
                query = query.join(user_roles).filter(
                    user_roles.c.role_id == role.id
                )

        total = query.count()
        users = query.order_by(IAMUser.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return users, total

    def update(self, user_id: UUID, data: UserUpdate, updated_by: int | None = None) -> IAMUser:
        """Met à jour un utilisateur."""
        user = self.get(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")

        old_values = {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active
        }

        for field, value in data.model_dump(exclude_unset=True).items():
            if field == "password" and value:
                user.password_hash = self._hash_password(value)
                user.password_changed_at = datetime.utcnow()
                self._save_password_history(user.id, user.password_hash)
            elif hasattr(user, field):
                setattr(user, field, value)

        # Audit
        self._audit_log("USER_UPDATED", "USER", user_id, updated_by,
                       old_values=old_values,
                       new_values=data.model_dump(exclude_unset=True, exclude={"password"}))

        self.db.commit()
        return user

    def deactivate(self, user_id: UUID, deactivated_by: int | None = None) -> IAMUser:
        """Désactive un utilisateur."""
        user = self.get(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")

        user.is_active = False
        user.deactivated_at = datetime.utcnow()
        user.deactivated_by = deactivated_by

        self._audit_log("USER_DEACTIVATED", "USER", user_id, deactivated_by)
        self.db.commit()
        return user

    def activate(self, user_id: UUID, activated_by: int | None = None) -> IAMUser:
        """Réactive un utilisateur."""
        user = self.get(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")

        user.is_active = True
        user.deactivated_at = None
        user.deactivated_by = None

        self._audit_log("USER_ACTIVATED", "USER", user_id, activated_by)
        self.db.commit()
        return user

    def lock(self, user_id: UUID, reason: str, locked_by: int | None = None, until: datetime | None = None) -> IAMUser:
        """Verrouille un compte utilisateur."""
        user = self.get(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")

        user.is_locked = True
        user.lock_reason = reason
        user.locked_at = datetime.utcnow()
        user.locked_until = until
        user.locked_by = locked_by

        self._audit_log("USER_LOCKED", "USER", user_id, locked_by,
                       new_values={"reason": reason, "until": str(until) if until else None})
        self.db.commit()
        return user

    def unlock(self, user_id: UUID, unlocked_by: int | None = None) -> IAMUser:
        """Déverrouille un compte utilisateur."""
        user = self.get(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")

        user.is_locked = False
        user.lock_reason = None
        user.locked_at = None
        user.locked_until = None
        user.failed_login_attempts = 0

        self._audit_log("USER_UNLOCKED", "USER", user_id, unlocked_by)
        self.db.commit()
        return user
