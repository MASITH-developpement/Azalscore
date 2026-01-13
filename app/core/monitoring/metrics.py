"""
AZALS - Métriques Prometheus
============================
Collecte et export des métriques pour monitoring production.
"""

import time
from collections.abc import Callable

from fastapi import APIRouter, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware

# ============================================================================
# MÉTRIQUES DÉFINITIONS
# ============================================================================

# Info application
APP_INFO = Info(
    "azals_app",
    "AZALS Application Information"
)
APP_INFO.info({
    "version": "0.3.0",
    "name": "AZALS",
    "description": "ERP Décisionnel Critique Multi-Tenant"
})

# Compteur de requêtes
REQUEST_COUNT = Counter(
    "azals_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code", "tenant_id"]
)

# Latence des requêtes (histogramme)
REQUEST_LATENCY = Histogram(
    "azals_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Requêtes actives
ACTIVE_REQUESTS = Gauge(
    "azals_http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method"]
)

# Utilisation pool DB
DB_POOL_USAGE = Gauge(
    "azals_db_pool_connections",
    "Database connection pool usage",
    ["state"]  # active, idle, overflow
)

# Requêtes par tenant
TENANT_REQUESTS = Counter(
    "azals_tenant_requests_total",
    "Total requests per tenant",
    ["tenant_id", "module"]
)

# Erreurs applicatives
APP_ERRORS = Counter(
    "azals_errors_total",
    "Application errors",
    ["error_type", "module"]
)

# Opérations métier
BUSINESS_OPERATIONS = Counter(
    "azals_business_operations_total",
    "Business operations counter",
    ["operation", "module", "status"]
)

# Temps de traitement métier
BUSINESS_LATENCY = Histogram(
    "azals_business_operation_duration_seconds",
    "Business operation duration",
    ["operation", "module"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# Décisions IA
AI_DECISIONS = Counter(
    "azals_ai_decisions_total",
    "AI decisions and recommendations",
    ["decision_type", "risk_level", "status"]
)

# Points rouges (décisions critiques)
RED_POINTS = Counter(
    "azals_red_points_total",
    "Critical red points requiring double confirmation",
    ["status"]  # pending, confirmed, rejected
)


# ============================================================================
# MIDDLEWARE MÉTRIQUES
# ============================================================================

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware collectant les métriques de chaque requête HTTP.
    - Comptage des requêtes
    - Latence
    - Requêtes actives
    - Segmentation par tenant
    """

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method

        # Extraction endpoint normalisé (éviter cardinality explosion)
        endpoint = self._normalize_endpoint(request.url.path)

        # Extraction tenant_id
        tenant_id = getattr(request.state, "tenant_id", "unknown")
        if not hasattr(request.state, "tenant_id"):
            tenant_id = request.headers.get("X-Tenant-ID", "unknown")

        # Incrémenter requêtes actives
        ACTIVE_REQUESTS.labels(method=method).inc()

        # Mesure du temps de traitement
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            status_code = str(response.status_code)
        except Exception as e:
            status_code = "500"
            APP_ERRORS.labels(
                error_type=type(e).__name__,
                module=self._extract_module(endpoint)
            ).inc()
            raise
        finally:
            # Calcul latence
            duration = time.perf_counter() - start_time

            # Enregistrement métriques
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                tenant_id=tenant_id[:50] if tenant_id else "unknown"  # Limite longueur
            ).inc()

            REQUEST_LATENCY.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            # Décrémenter requêtes actives
            ACTIVE_REQUESTS.labels(method=method).dec()

            # Comptage par tenant
            if tenant_id and tenant_id != "unknown":
                TENANT_REQUESTS.labels(
                    tenant_id=tenant_id[:50],
                    module=self._extract_module(endpoint)
                ).inc()

        return response

    @staticmethod
    def _normalize_endpoint(path: str) -> str:
        """
        Normalise les endpoints pour éviter l'explosion de cardinalité.
        Remplace les IDs numériques par des placeholders.
        """
        import re

        # Remplacer les UUIDs
        path = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '{uuid}',
            path
        )

        # Remplacer les IDs numériques
        path = re.sub(r'/\d+(?=/|$)', '/{id}', path)

        return path

    @staticmethod
    def _extract_module(endpoint: str) -> str:
        """Extrait le nom du module depuis l'endpoint."""
        parts = endpoint.strip('/').split('/')
        if parts:
            return parts[0]
        return "root"


# ============================================================================
# ROUTER MÉTRIQUES
# ============================================================================

metrics_router = APIRouter(tags=["Monitoring"])


@metrics_router.get("/metrics")
async def get_metrics():
    """
    Endpoint Prometheus pour scraping des métriques.
    Format: text/plain compatible Prometheus.
    Endpoint PUBLIC (pas de validation tenant).
    """
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def record_business_operation(
    operation: str,
    module: str,
    status: str = "success",
    duration: float = None
):
    """
    Enregistre une opération métier.

    Args:
        operation: Nom de l'opération (ex: "create_invoice", "validate_order")
        module: Module concerné (ex: "commercial", "finance")
        status: success, failure, pending
        duration: Durée optionnelle en secondes
    """
    BUSINESS_OPERATIONS.labels(
        operation=operation,
        module=module,
        status=status
    ).inc()

    if duration is not None:
        BUSINESS_LATENCY.labels(
            operation=operation,
            module=module
        ).observe(duration)


def record_ai_decision(
    decision_type: str,
    risk_level: str,
    status: str = "proposed"
):
    """
    Enregistre une décision IA.

    Args:
        decision_type: Type de décision (recommendation, alert, prediction)
        risk_level: green, orange, red
        status: proposed, confirmed, rejected
    """
    AI_DECISIONS.labels(
        decision_type=decision_type,
        risk_level=risk_level,
        status=status
    ).inc()

    # Comptage spécial points rouges
    if risk_level == "red":
        RED_POINTS.labels(status=status).inc()


def update_db_pool_metrics(active: int, idle: int, overflow: int):
    """Met à jour les métriques du pool de connexions DB."""
    DB_POOL_USAGE.labels(state="active").set(active)
    DB_POOL_USAGE.labels(state="idle").set(idle)
    DB_POOL_USAGE.labels(state="overflow").set(overflow)
