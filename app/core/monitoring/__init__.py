"""
AZALS - Module Monitoring & Observabilité
==========================================
Prometheus metrics, structured logging, health checks.
"""

from app.core.monitoring.metrics import (
    MetricsMiddleware,
    metrics_router,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    ACTIVE_REQUESTS,
    DB_POOL_USAGE,
    TENANT_REQUESTS,
)
from app.core.monitoring.logging import (
    setup_logging,
    get_logger,
    LoggingMiddleware,
)
from app.core.monitoring.health import (
    health_router,
    HealthStatus,
    DetailedHealthCheck,
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
