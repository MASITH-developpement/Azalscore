"""
AZALS MODULE - Marceau Dependencies
====================================

Dependances FastAPI pour le module Marceau.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.core.models import User

from .config import get_or_create_marceau_config, is_module_enabled
from .models import MarceauConfig


def get_marceau_config(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
) -> MarceauConfig:
    """
    Recupere la configuration Marceau du tenant courant.
    Cree la configuration par defaut si elle n'existe pas.
    """
    return get_or_create_marceau_config(tenant_id, db)


def require_module_enabled(module_name: str):
    """
    Dependency factory qui verifie qu'un module est active.

    Usage:
        @router.post("/telephonie/call")
        async def handle_call(
            _: None = Depends(require_module_enabled("telephonie"))
        ):
            ...
    """
    def dependency(
        config: MarceauConfig = Depends(get_marceau_config)
    ) -> None:
        if not is_module_enabled(config, module_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Module '{module_name}' non active pour ce tenant"
            )
    return dependency


def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verifie que l'utilisateur a les droits d'administration Marceau.
    """
    # NOTE: Phase 2 - Vérification IAMService.check_permission("marceau.admin")
    return current_user


class RateLimiter:
    """
    Rate limiter pour les appels API Marceau.
    """

    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self._cache: dict = {}

    async def __call__(
        self,
        tenant_id: str = Depends(get_tenant_id),
        current_user: User = Depends(get_current_user)
    ) -> None:
        """
        Verifie le rate limit.
        TODO: Implementation complete avec Redis.
        """
        # Pour l'instant, pas de limitation
        pass


# Instance par defaut
rate_limiter = RateLimiter(calls_per_minute=60)
