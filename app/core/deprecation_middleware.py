"""
AZALS - Middleware de Dépréciation API v1
==========================================
Log les appels aux endpoints v1 dépréciés et ajoute un header d'avertissement.

Ce middleware permet de:
1. Tracer les clients qui utilisent encore l'API v1
2. Informer les clients via header HTTP qu'ils doivent migrer
3. Collecter des métriques sur l'utilisation v1 vs v2

Conformité : AZA-NF-005
"""
from __future__ import annotations


import logging
import time
from datetime import datetime
from typing import Callable, Dict, Set
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# Header d'avertissement de dépréciation
V1_DEPRECATION_WARNING = "API v1 is deprecated. Please migrate to v2. See docs at /docs/migration"

# Endpoints exclus du logging (health checks, etc.)
EXCLUDED_PATHS: Set[str] = {
    "/v1/health",
    "/v1/health/ready",
    "/v1/health/live",
    "/v1/metrics",
}

# Compteur d'appels v1 par tenant (pour métriques)
_v1_call_counts: Dict[str, int] = defaultdict(int)


class DeprecationMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour tracer et avertir des appels à l'API v1 dépréciée.

    Usage dans main.py:
        from app.core.deprecation_middleware import DeprecationMiddleware

        app.add_middleware(DeprecationMiddleware)
    """

    def __init__(
        self,
        app: ASGIApp,
        log_level: str = "WARNING",
        add_header: bool = True,
        track_metrics: bool = True
    ):
        """
        Initialise le middleware.

        Args:
            app: Application ASGI
            log_level: Niveau de log pour les appels v1 (WARNING, INFO, DEBUG)
            add_header: Ajouter le header X-Deprecation-Warning
            track_metrics: Collecter des métriques d'utilisation
        """
        super().__init__(app)
        self.log_level = getattr(logging, log_level.upper(), logging.WARNING)
        self.add_header = add_header
        self.track_metrics = track_metrics

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Intercepte les requêtes et traite les appels v1."""

        path = request.url.path

        # Ignorer les chemins exclus
        if path in EXCLUDED_PATHS:
            return await call_next(request)

        # Détecter les appels à l'API v1
        is_v1_call = path.startswith("/v1/")

        if is_v1_call:
            # Extraire les infos pour le logging
            tenant_id = request.headers.get("X-Tenant-ID", "unknown")
            user_agent = request.headers.get("User-Agent", "unknown")
            method = request.method

            # Log l'appel déprécié
            logger.log(
                self.log_level,
                "Deprecated API v1 endpoint called",
                extra={
                    "path": path,
                    "method": method,
                    "tenant_id": tenant_id,
                    "user_agent": user_agent,
                    "deprecation": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            # Métriques
            if self.track_metrics:
                _v1_call_counts[tenant_id] += 1

        # Exécuter la requête
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        # Ajouter le header de dépréciation aux réponses v1
        if is_v1_call and self.add_header:
            response.headers["X-Deprecation-Warning"] = V1_DEPRECATION_WARNING
            response.headers["X-API-Version"] = "v1 (deprecated)"

            # Suggérer l'endpoint v2 équivalent
            v2_path = path.replace("/v1/", "/v2/", 1)
            response.headers["X-Upgrade-To"] = v2_path

        # Log additionnel pour les appels lents v1 (potentiellement à optimiser en v2)
        if is_v1_call and duration > 1.0:
            logger.warning(
                "Slow deprecated v1 endpoint",
                extra={
                    "path": path,
                    "duration_seconds": round(duration, 3),
                    "tenant_id": request.headers.get("X-Tenant-ID", "unknown")
                }
            )

        return response


def get_v1_usage_stats() -> Dict[str, int]:
    """
    Retourne les statistiques d'utilisation de l'API v1 par tenant.

    Usage:
        stats = get_v1_usage_stats()
        for tenant_id, count in stats.items():
            print(f"{tenant_id}: {count} appels v1")
    """
    return dict(_v1_call_counts)


def reset_v1_usage_stats() -> None:
    """Remet à zéro les compteurs (pour tests ou rotation)."""
    global _v1_call_counts
    _v1_call_counts = defaultdict(int)


# =============================================================================
# Endpoint pour exposer les métriques de dépréciation
# =============================================================================

def create_deprecation_stats_router():
    """
    Crée un router FastAPI pour exposer les stats de dépréciation.

    Usage dans main.py:
        from app.core.deprecation_middleware import create_deprecation_stats_router
        app.include_router(create_deprecation_stats_router(), prefix="/admin")
    """
    from fastapi import APIRouter, Depends
    from app.core.dependencies import get_current_user
    from app.core.models import User

    router = APIRouter(tags=["Admin - Deprecation"])

    @router.get("/deprecation/stats")
    async def get_deprecation_stats(
        current_user: User = Depends(get_current_user)
    ):
        """
        Retourne les statistiques d'utilisation de l'API v1 dépréciée.
        Réservé aux administrateurs.
        """
        if not hasattr(current_user, 'role') or current_user.role not in ['SUPERADMIN', 'ADMIN', 'DIRIGEANT']:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )

        stats = get_v1_usage_stats()
        total = sum(stats.values())

        return {
            "total_v1_calls": total,
            "by_tenant": stats,
            "warning": V1_DEPRECATION_WARNING
        }

    return router
