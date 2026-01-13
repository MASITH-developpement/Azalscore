"""
AZALS - Module Monitoring & Observabilité
==========================================
Prometheus metrics, structured logging, health checks.
"""

from app.core.monitoring.health import (
    DetailedHealthCheck,
    HealthStatus,
    health_router,
)
from app.core.monitoring.logging import (
    LoggingMiddleware,
    get_logger,
    setup_logging,
)
from app.core.monitoring.metrics import (
    ACTIVE_REQUESTS,
    DB_POOL_USAGE,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    TENANT_REQUESTS,
    MetricsMiddleware,
    metrics_router,
)

__all__ = [
    # Metrics
    "MetricsMiddleware",
    "metrics_router",
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
    "ACTIVE_REQUESTS",
    "DB_POOL_USAGE",
    "TENANT_REQUESTS",
    # Logging
    "setup_logging",
    "get_logger",
    "LoggingMiddleware",
    # Health
    "health_router",
    "HealthStatus",
    "DetailedHealthCheck",
]
