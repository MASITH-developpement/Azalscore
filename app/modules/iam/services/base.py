"""
AZALS MODULE T0 - Base IAM Service
===================================

Classe de base pour tous les sous-services IAM.
"""

import json
import logging
from datetime import datetime
from typing import TypeVar, Generic, Type, Optional
from uuid import UUID

import bcrypt
from sqlalchemy.orm import Session

from app.modules.iam.models import IAMAuditLog, IAMPasswordHistory

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseIAMService(Generic[T]):
    """Classe de base pour les services IAM."""

    model: Type[T] = None

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(self.model).filter(
            self.model.tenant_id == self.tenant_id
        )

    def _hash_password(self, password: str) -> str:
        """Hash un mot de passe avec bcrypt."""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Vérifie un mot de passe contre son hash."""
        try:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except Exception:
            return False

    def _save_password_history(self, user_id: UUID, password_hash: str):
        """Sauvegarde un mot de passe dans l'historique."""
        history = IAMPasswordHistory(
            tenant_id=self.tenant_id,
            user_id=user_id,
            password_hash=password_hash
        )
        self.db.add(history)

    def _audit_log(
        self,
        action: str,
        entity_type: str,
        entity_id: UUID | None,
        performed_by: int | None,
        old_values: dict | None = None,
        new_values: dict | None = None,
        details: dict | None = None
    ):
        """Crée une entrée dans le journal d'audit."""
        log = IAMAuditLog(
            tenant_id=self.tenant_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            performed_by=performed_by,
            performed_at=datetime.utcnow(),
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            details=json.dumps(details) if details else None
        )
        self.db.add(log)
