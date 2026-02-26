"""
CORE SaaS - Contexte d'exécution immuable
==========================================

Ce module définit le SaaSContext, structure immuable contenant toutes
les informations nécessaires pour l'exécution d'une action métier.

PRINCIPE CLÉ:
- Immuable (frozen dataclass)
- Créé une seule fois par requête
- Passé à TOUTES les fonctions métier
- Contient: tenant, user, role, permissions, scope, audit trail
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Set
from uuid import UUID
import enum

# Import canonical de UserRole depuis models.py
# Ré-exporté ici pour compatibilité avec les imports existants
from app.core.models import UserRole  # noqa: F401 - re-export intentionnel


class TenantScope(str, enum.Enum):
    """Scope d'exécution."""
    TENANT = "tenant"    # Actions limitées au tenant
    GLOBAL = "global"    # Actions système (superadmin only)


@dataclass(frozen=True)
class SaaSContext:
    """
    Contexte SaaS immuable.

    Contient toutes les informations nécessaires pour:
    - Authentification (tenant_id, user_id)
    - Authorization (role, permissions)
    - Isolation tenant (scope)
    - Audit trail (ip_address, user_agent, correlation_id)

    Créé par le middleware et injecté via FastAPI Depends.
    """

    # Identification
    tenant_id: str
    user_id: UUID

    # Authorization
    role: UserRole
    permissions: Set[str] = field(default_factory=set)

    # Scope
    scope: TenantScope = TenantScope.TENANT

    # Audit trail
    ip_address: str = ""
    user_agent: str = ""
    correlation_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Propriétés dérivées
    @property
    def is_creator(self) -> bool:
        """True si l'utilisateur est le créateur système (SUPERADMIN)."""
        return self.role == UserRole.SUPERADMIN

    @property
    def is_dirigeant(self) -> bool:
        """True si l'utilisateur est dirigeant du tenant."""
        return self.role == UserRole.DIRIGEANT

    @property
    def is_admin(self) -> bool:
        """True si l'utilisateur est admin ou plus."""
        return self.role in [UserRole.SUPERADMIN, UserRole.DIRIGEANT, UserRole.ADMIN]

    @property
    def is_global_scope(self) -> bool:
        """True si le contexte est en scope global."""
        return self.scope == TenantScope.GLOBAL

    def has_permission(self, permission: str) -> bool:
        """
        Vérifie si le contexte possède une permission donnée.

        Args:
            permission: Format "module.resource.action" (ex: "commercial.customer.create")

        Returns:
            True si la permission est accordée
        """
        # SUPERADMIN a toutes les permissions
        if self.is_creator:
            return True

        # Vérifier permission exacte
        if permission in self.permissions:
            return True

        # Vérifier wildcards
        parts = permission.split(".")
        if len(parts) == 3:
            module, resource, action = parts

            # Vérifier "module.resource.*"
            if f"{module}.{resource}.*" in self.permissions:
                return True

            # Vérifier "module.*"
            if f"{module}.*" in self.permissions:
                return True

        return False

    def to_audit_dict(self) -> dict:
        """
        Convertit le contexte en dictionnaire pour l'audit.

        Returns:
            Dictionnaire avec les informations d'audit
        """
        return {
            "tenant_id": self.tenant_id,
            "user_id": str(self.user_id),
            "role": self.role.value,
            "scope": self.scope.value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
        }

    def __repr__(self) -> str:
        """Représentation lisible du contexte (sans permissions pour éviter verbosité)."""
        return (
            f"SaaSContext("
            f"tenant={self.tenant_id}, "
            f"user={self.user_id}, "
            f"role={self.role.value}, "
            f"scope={self.scope.value}, "
            f"perms={len(self.permissions)}"
            f")"
        )


@dataclass(frozen=True)
class Result:
    """
    Résultat d'exécution d'une action métier.

    Pattern Result/Either pour la gestion d'erreurs explicite.
    """

    success: bool
    data: Optional[any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None

    @staticmethod
    def ok(data: any = None) -> "Result":
        """Crée un résultat de succès."""
        return Result(success=True, data=data)

    @staticmethod
    def fail(error: str, error_code: Optional[str] = None) -> "Result":
        """Crée un résultat d'échec."""
        return Result(success=False, error=error, error_code=error_code)

    def unwrap(self) -> any:
        """Retourne la data ou lève une exception si échec."""
        if not self.success:
            raise ValueError(f"Result failed: {self.error}")
        return self.data

    def unwrap_or(self, default: any) -> any:
        """Retourne la data ou une valeur par défaut si échec."""
        return self.data if self.success else default
