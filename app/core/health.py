"""
AZALS - Health Checks ÉLITE
============================
Endpoints de santé détaillés pour monitoring.
Support Kubernetes liveness/readiness probes.
"""

import asyncio
import time
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import engine
from app.core.metrics import update_health_status

router = APIRouter(tags=["health"])


class HealthStatus(str, Enum):
    """Statuts de santé possibles."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Santé d'un composant."""
    name: str
    status: HealthStatus
    latency_ms: float | None = None
    message: str | None = None
    details: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    """Réponse de health check."""
    status: HealthStatus
    timestamp: str
    version: str
    environment: str
    uptime_seconds: float
    components: list[ComponentHealth]


# Timestamp de démarrage
_start_time = time.time()


async def check_database() -> ComponentHealth:
    """Vérifie la connexion à la base de données."""
    start = time.perf_counter()
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()

        latency = (time.perf_counter() - start) * 1000
        update_health_status("database", True)

        return ComponentHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            latency_ms=round(latency, 2),
            message="PostgreSQL connected"
        )
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        update_health_status("database", False)

        return ComponentHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            latency_ms=round(latency, 2),
            message=f"Connection failed: {str(e)[:100]}"
        )


async def check_redis() -> ComponentHealth:
    """Vérifie la connexion à Redis."""
    settings = get_settings()

    if not settings.redis_url:
        return ComponentHealth(
            name="redis",
            status=HealthStatus.HEALTHY,
            message="Redis not configured (using memory cache)"
        )

    start = time.perf_counter()
    try:
        import redis
        client = redis.from_url(
            settings.redis_url,
            socket_timeout=2,
            socket_connect_timeout=2
        )
        client.ping()
        client.close()

        latency = (time.perf_counter() - start) * 1000
        update_health_status("redis", True)

        return ComponentHealth(
            name="redis",
            status=HealthStatus.HEALTHY,
            latency_ms=round(latency, 2),
            message="Redis connected"
        )
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        update_health_status("redis", False)

        return ComponentHealth(
            name="redis",
            status=HealthStatus.DEGRADED,  # Dégradé car fallback mémoire existe
            latency_ms=round(latency, 2),
            message=f"Redis unavailable (fallback to memory): {str(e)[:50]}"
        )


async def check_disk_space() -> ComponentHealth:
    """Vérifie l'espace disque disponible."""
    try:
        import psutil
        disk = psutil.disk_usage('/')
        free_percent = 100 - disk.percent

        update_health_status("disk", free_percent > 10)

        if free_percent < 5:
            status = HealthStatus.UNHEALTHY
            message = f"CRITICAL: Only {free_percent:.1f}% disk space free"
        elif free_percent < 10:
            status = HealthStatus.DEGRADED
            message = f"WARNING: {free_percent:.1f}% disk space free"
        else:
            status = HealthStatus.HEALTHY
            message = f"{free_percent:.1f}% disk space free"

        return ComponentHealth(
            name="disk",
            status=status,
            message=message,
            details={
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_percent": disk.percent
            }
        )
    except Exception as e:
        return ComponentHealth(
            name="disk",
            status=HealthStatus.DEGRADED,
            message=f"Unable to check disk: {str(e)[:50]}"
        )


async def check_memory() -> ComponentHealth:
    """Vérifie l'utilisation mémoire."""
    try:
        import psutil
        memory = psutil.virtual_memory()
        available_percent = 100 - memory.percent

        update_health_status("memory", available_percent > 10)

        if available_percent < 5:
            status = HealthStatus.UNHEALTHY
            message = f"CRITICAL: Only {available_percent:.1f}% memory available"
        elif available_percent < 15:
            status = HealthStatus.DEGRADED
            message = f"WARNING: {available_percent:.1f}% memory available"
        else:
            status = HealthStatus.HEALTHY
            message = f"{available_percent:.1f}% memory available"

        return ComponentHealth(
            name="memory",
            status=status,
            message=message,
            details={
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_percent": memory.percent
            }
        )
    except Exception as e:
        return ComponentHealth(
            name="memory",
            status=HealthStatus.DEGRADED,
            message=f"Unable to check memory: {str(e)[:50]}"
        )


def aggregate_status(components: list[ComponentHealth]) -> HealthStatus:
    """Calcule le statut global à partir des composants."""
    statuses = [c.status for c in components]

    if HealthStatus.UNHEALTHY in statuses:
        return HealthStatus.UNHEALTHY
    if HealthStatus.DEGRADED in statuses:
        return HealthStatus.DEGRADED
    return HealthStatus.HEALTHY


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check détaillé.
    Vérifie tous les composants et retourne un statut agrégé.
    """
    settings = get_settings()

    # Exécuter les checks en parallèle
    components = await asyncio.gather(
        check_database(),
        check_redis(),
        check_disk_space(),
        check_memory(),
        return_exceptions=True
    )

    # Gérer les exceptions
    valid_components = []
    for comp in components:
        if isinstance(comp, ComponentHealth):
            valid_components.append(comp)
        elif isinstance(comp, Exception):
            valid_components.append(ComponentHealth(
                name="unknown",
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {str(comp)[:50]}"
            ))

    # Statut global
    overall_status = aggregate_status(valid_components)

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat() + "Z",
        version="0.4.0",
        environment=settings.environment,
        uptime_seconds=round(time.time() - _start_time, 2),
        components=valid_components
    )


@router.get("/health/live")
async def liveness_probe():
    """
    Kubernetes liveness probe.
    Retourne 200 si l'application est vivante.
    Simple check sans dépendances externes.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe(response: Response):
    """
    Kubernetes readiness probe.
    Retourne 200 si l'application peut recevoir du trafic.
    Vérifie la base de données obligatoirement.
    """
    db_health = await check_database()

    if db_health.status == HealthStatus.UNHEALTHY:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "reason": "Database unavailable"
        }

    return {"status": "ready"}


@router.get("/health/startup")
async def startup_probe():
    """
    Kubernetes startup probe.
    Vérifie que l'application a bien démarré.
    """
    settings = get_settings()

    return {
        "status": "started",
        "environment": settings.environment,
        "uptime_seconds": round(time.time() - _start_time, 2)
    }


@router.get("/health/db")
async def database_health():
    """Health check spécifique base de données."""
    return await check_database()


@router.get("/health/redis")
async def redis_health():
    """Health check spécifique Redis."""
    return await check_redis()
