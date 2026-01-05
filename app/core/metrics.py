"""
AZALS - Métriques Prometheus ÉLITE
===================================
Métriques pour monitoring et alerting.
Endpoint /metrics pour scraping Prometheus.
"""

import time
from typing import Callable
from functools import wraps
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY
)
from fastapi import APIRouter, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings


# ============================================================================
# MÉTRIQUES GLOBALES
# ============================================================================

# Info application
APP_INFO = Info(
    'azals_app',
    'Application information'
)

# Requêtes HTTP
HTTP_REQUESTS_TOTAL = Counter(
    'azals_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'tenant_id']
)

HTTP_REQUEST_DURATION = Histogram(
    'azals_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'tenant_id'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    'azals_http_requests_in_progress',
    'HTTP requests currently in progress',
    ['method', 'endpoint']
)

# Base de données
DB_CONNECTIONS_ACTIVE = Gauge(
    'azals_db_connections_active',
    'Active database connections'
)

DB_QUERY_DURATION = Histogram(
    'azals_db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

# Cache
CACHE_HITS = Counter(
    'azals_cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'azals_cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# Authentification
AUTH_ATTEMPTS = Counter(
    'azals_auth_attempts_total',
    'Total authentication attempts',
    ['method', 'status', 'tenant_id']
)

AUTH_RATE_LIMIT_HITS = Counter(
    'azals_auth_rate_limit_hits_total',
    'Authentication rate limit hits',
    ['tenant_id', 'ip']
)

# Business metrics
TENANTS_ACTIVE = Gauge(
    'azals_tenants_active',
    'Number of active tenants'
)

USERS_TOTAL = Gauge(
    'azals_users_total',
    'Total users by tenant',
    ['tenant_id']
)

DECISIONS_TOTAL = Counter(
    'azals_decisions_total',
    'Total decisions by level',
    ['level', 'tenant_id']
)

# Santé système
SYSTEM_HEALTH = Gauge(
    'azals_system_health',
    'System health status (1=healthy, 0=unhealthy)',
    ['component']
)


# ============================================================================
# MIDDLEWARE DE MÉTRIQUES
# ============================================================================

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour collecter les métriques HTTP automatiquement.
    """

    # Endpoints à exclure des métriques détaillées
    EXCLUDED_PATHS = {'/metrics', '/health', '/favicon.ico'}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip pour certains endpoints
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        method = request.method
        # Normaliser le path pour éviter la cardinalité explosive
        endpoint = self._normalize_path(request.url.path)
        tenant_id = request.headers.get('X-Tenant-ID', 'unknown')

        # Incrémenter les requêtes en cours
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = 500
            raise
        finally:
            # Calculer la durée
            duration = time.perf_counter() - start_time

            # Décrémenter les requêtes en cours
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()

            # Enregistrer les métriques
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code),
                tenant_id=tenant_id
            ).inc()

            HTTP_REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint,
                tenant_id=tenant_id
            ).observe(duration)

    def _normalize_path(self, path: str) -> str:
        """
        Normalise le path pour éviter la cardinalité explosive.
        Remplace les IDs par des placeholders.
        """
        parts = path.strip('/').split('/')
        normalized = []

        for part in parts:
            # Remplacer les UUIDs
            if len(part) == 36 and part.count('-') == 4:
                normalized.append('{uuid}')
            # Remplacer les IDs numériques
            elif part.isdigit():
                normalized.append('{id}')
            else:
                normalized.append(part)

        return '/' + '/'.join(normalized) if normalized else '/'


# ============================================================================
# ROUTER MÉTRIQUES
# ============================================================================

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def metrics():
    """
    Endpoint Prometheus pour scraping des métriques.
    Format: text/plain avec métriques Prometheus.
    """
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/metrics/json")
async def metrics_json():
    """
    Version JSON des métriques pour debug.
    """
    from prometheus_client.parser import text_string_to_metric_families

    metrics_text = generate_latest(REGISTRY).decode('utf-8')
    result = {}

    for family in text_string_to_metric_families(metrics_text):
        result[family.name] = {
            "type": family.type,
            "help": family.documentation,
            "samples": [
                {
                    "labels": dict(sample.labels),
                    "value": sample.value
                }
                for sample in family.samples
            ]
        }

    return result


# ============================================================================
# HELPERS
# ============================================================================

def init_metrics():
    """Initialise les métriques avec les infos de l'application."""
    settings = get_settings()

    APP_INFO.info({
        'version': '0.4.0',
        'environment': settings.environment,
        'app_name': settings.app_name
    })


def track_db_query(operation: str):
    """
    Décorateur pour tracker les requêtes DB.

    Usage:
        @track_db_query("select")
        def get_users():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                DB_QUERY_DURATION.labels(operation=operation).observe(duration)
        return wrapper
    return decorator


def track_db_query_async(operation: str):
    """Version async de track_db_query."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                DB_QUERY_DURATION.labels(operation=operation).observe(duration)
        return wrapper
    return decorator


def record_auth_attempt(method: str, success: bool, tenant_id: str):
    """Enregistre une tentative d'authentification."""
    AUTH_ATTEMPTS.labels(
        method=method,
        status="success" if success else "failure",
        tenant_id=tenant_id
    ).inc()


def record_rate_limit_hit(tenant_id: str, ip: str):
    """Enregistre un hit de rate limit."""
    AUTH_RATE_LIMIT_HITS.labels(tenant_id=tenant_id, ip=ip).inc()


def record_decision(level: str, tenant_id: str):
    """Enregistre une décision."""
    DECISIONS_TOTAL.labels(level=level, tenant_id=tenant_id).inc()


def update_health_status(component: str, healthy: bool):
    """Met à jour le statut de santé d'un composant."""
    SYSTEM_HEALTH.labels(component=component).set(1 if healthy else 0)


def record_cache_access(cache_type: str, hit: bool):
    """Enregistre un accès cache."""
    if hit:
        CACHE_HITS.labels(cache_type=cache_type).inc()
    else:
        CACHE_MISSES.labels(cache_type=cache_type).inc()
