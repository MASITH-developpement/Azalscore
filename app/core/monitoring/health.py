"""
AZALS - Health Checks Avancés
=============================
Endpoints de santé pour orchestration et monitoring.
"""

import logging
import time

logger = logging.getLogger(__name__)
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import engine

# ============================================================================
# MODÈLES
# ============================================================================

class HealthStatus(str, Enum):
    """Statuts de santé."""
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


class DetailedHealthCheck(BaseModel):
    """Réponse health check détaillée."""
    status: HealthStatus
    version: str
    timestamp: str
    uptime_seconds: float
    components: list[ComponentHealth]
    checks_passed: int
    checks_failed: int


# ============================================================================
# VARIABLES GLOBALES
# ============================================================================

# Timestamp de démarrage (défini au premier import)
_startup_time: float = time.time()


# ============================================================================
# CHECKS INDIVIDUELS
# ============================================================================

def check_database(db: Session = None) -> ComponentHealth:
    """
    Vérifie la connexion à la base de données.
    """
    start = time.perf_counter()

    try:
        if db:
            db.execute(text("SELECT 1"))
        else:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

        latency = (time.perf_counter() - start) * 1000

        # Récupérer infos pool si disponible
        pool_info = {}
        try:
            pool = engine.pool
            pool_info = {
                "pool_size": pool.size(),
                "checkedin": pool.checkedin(),
                "checkedout": pool.checkedout(),
                "overflow": pool.overflow(),
            }
        except AttributeError as e:
            logger.debug("Could not retrieve pool info (pool may not support these methods): %s", e)

        return ComponentHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            latency_ms=round(latency, 2),
            message="PostgreSQL connection OK",
            details=pool_info if pool_info else None
        )

    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return ComponentHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            latency_ms=round(latency, 2),
            message=f"Database error: {str(e)[:100]}"
        )


def check_memory() -> ComponentHealth:
    """
    Vérifie l'utilisation mémoire.
    """
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)

        # Seuils
        if memory_mb > 2000:  # > 2GB
            status = HealthStatus.UNHEALTHY
            message = f"High memory usage: {memory_mb:.0f}MB"
        elif memory_mb > 1000:  # > 1GB
            status = HealthStatus.DEGRADED
            message = f"Elevated memory usage: {memory_mb:.0f}MB"
        else:
            status = HealthStatus.HEALTHY
            message = f"Memory usage: {memory_mb:.0f}MB"

        return ComponentHealth(
            name="memory",
            status=status,
            message=message,
            details={
                "rss_mb": round(memory_mb, 2),
                "vms_mb": round(memory_info.vms / (1024 * 1024), 2),
                "percent": round(process.memory_percent(), 2)
            }
        )

    except ImportError:
        return ComponentHealth(
            name="memory",
            status=HealthStatus.HEALTHY,
            message="psutil not available, check skipped"
        )
    except Exception as e:
        return ComponentHealth(
            name="memory",
            status=HealthStatus.DEGRADED,
            message=f"Memory check error: {str(e)[:100]}"
        )


def check_disk() -> ComponentHealth:
    """
    Vérifie l'espace disque disponible.
    """
    try:
        import psutil
        disk = psutil.disk_usage('/')
        free_gb = disk.free / (1024 ** 3)
        percent_used = disk.percent

        if percent_used > 95:
            status = HealthStatus.UNHEALTHY
            message = f"Critical disk space: {percent_used}% used"
        elif percent_used > 85:
            status = HealthStatus.DEGRADED
            message = f"Low disk space: {percent_used}% used"
        else:
            status = HealthStatus.HEALTHY
            message = f"Disk space OK: {percent_used}% used"

        return ComponentHealth(
            name="disk",
            status=status,
            message=message,
            details={
                "total_gb": round(disk.total / (1024 ** 3), 2),
                "free_gb": round(free_gb, 2),
                "percent_used": percent_used
            }
        )

    except ImportError:
        return ComponentHealth(
            name="disk",
            status=HealthStatus.HEALTHY,
            message="psutil not available, check skipped"
        )
    except Exception as e:
        return ComponentHealth(
            name="disk",
            status=HealthStatus.DEGRADED,
            message=f"Disk check error: {str(e)[:100]}"
        )


def check_cpu() -> ComponentHealth:
    """
    Vérifie l'utilisation CPU.
    """
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)

        if cpu_percent > 90:
            status = HealthStatus.UNHEALTHY
            message = f"Critical CPU usage: {cpu_percent}%"
        elif cpu_percent > 70:
            status = HealthStatus.DEGRADED
            message = f"High CPU usage: {cpu_percent}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"CPU usage: {cpu_percent}%"

        return ComponentHealth(
            name="cpu",
            status=status,
            message=message,
            details={
                "percent": cpu_percent,
                "count": psutil.cpu_count()
            }
        )

    except ImportError:
        return ComponentHealth(
            name="cpu",
            status=HealthStatus.HEALTHY,
            message="psutil not available, check skipped"
        )
    except Exception as e:
        return ComponentHealth(
            name="cpu",
            status=HealthStatus.DEGRADED,
            message=f"CPU check error: {str(e)[:100]}"
        )


# ============================================================================
# ROUTER HEALTH
# ============================================================================

health_router = APIRouter(tags=["Health"])


@health_router.get("/health")
async def basic_health():
    """
    Health check basique pour load balancers.
    Endpoint PUBLIC - pas de validation tenant.

    Returns:
        {"status": "ok"} si l'API répond
    """
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@health_router.get("/health/live")
async def liveness_probe():
    """
    Liveness probe pour Kubernetes.
    Vérifie que l'application tourne.
    Endpoint PUBLIC.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": round(time.time() - _startup_time, 2)
    }


@health_router.get("/health/ready")
async def readiness_probe():
    """
    Readiness probe pour Kubernetes.
    Vérifie que l'application peut recevoir du trafic.
    Endpoint PUBLIC.
    """
    db_check = check_database()

    if db_check.status == HealthStatus.UNHEALTHY:
        return {
            "status": "not_ready",
            "reason": "database_unavailable",
            "details": db_check.message
        }

    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }


@health_router.get("/health/detailed", response_model=DetailedHealthCheck)
async def detailed_health():
    """
    Health check détaillé pour monitoring.
    Vérifie tous les composants.
    Endpoint PUBLIC.
    """
    components = [
        check_database(),
        check_memory(),
        check_disk(),
        check_cpu(),
    ]

    # Calcul du statut global
    checks_failed = sum(1 for c in components if c.status == HealthStatus.UNHEALTHY)
    checks_degraded = sum(1 for c in components if c.status == HealthStatus.DEGRADED)

    if checks_failed > 0:
        overall_status = HealthStatus.UNHEALTHY
    elif checks_degraded > 0:
        overall_status = HealthStatus.DEGRADED
    else:
        overall_status = HealthStatus.HEALTHY

    return DetailedHealthCheck(
        status=overall_status,
        version="0.3.0",
        timestamp=datetime.utcnow().isoformat() + "Z",
        uptime_seconds=round(time.time() - _startup_time, 2),
        components=components,
        checks_passed=len(components) - checks_failed,
        checks_failed=checks_failed
    )


@health_router.get("/health/startup")
async def startup_probe():
    """
    Startup probe pour Kubernetes.
    Vérifie que l'application a démarré correctement.
    Utilisé uniquement au démarrage.
    Endpoint PUBLIC.
    """
    db_check = check_database()

    return {
        "status": "started" if db_check.status != HealthStatus.UNHEALTHY else "starting",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_check.status.value,
        "uptime_seconds": round(time.time() - _startup_time, 2)
    }
