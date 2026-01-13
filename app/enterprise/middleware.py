"""
AZALSCORE Enterprise - Middleware Integration
==============================================
Middleware d'intégration enterprise pour FastAPI.

Intègre:
- Gouvernance des tenants
- Observabilité SRE
- Circuit breaker
- Back-pressure
- Audit de sécurité
"""

import time
import logging
from typing import Optional, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.enterprise.governance import get_governor, TenantGovernor, ViolationType
from app.enterprise.observability import get_observer, EnterpriseObserver
from app.enterprise.resilience import (
    get_circuit_breaker,
    get_back_pressure,
    CircuitBreaker,
    BackPressure,
    CircuitBreakerOpenError,
)
from app.enterprise.security import (
    get_audit_logger,
    SecurityEventType,
    SecurityAuditLogger,
)
from app.enterprise.sla import TenantTier

logger = logging.getLogger(__name__)


class EnterpriseMiddleware(BaseHTTPMiddleware):
    """
    Middleware Enterprise - Intégration complète.

    Ordre d'exécution:
    1. Back-pressure check
    2. Circuit breaker check
    3. Tenant governance (quotas)
    4. Request execution
    5. Metrics recording
    6. Audit logging
    """

    # Endpoints publics (pas de gouvernance)
    PUBLIC_PATHS = {
        "/health",
        "/health/",
        "/health/live",
        "/health/ready",
        "/health/startup",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    def __init__(
        self,
        app,
        governor: Optional[TenantGovernor] = None,
        observer: Optional[EnterpriseObserver] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        back_pressure: Optional[BackPressure] = None,
        audit_logger: Optional[SecurityAuditLogger] = None,
        enable_back_pressure: bool = True,
        enable_circuit_breaker: bool = True,
        enable_governance: bool = True,
        enable_observability: bool = True,
        enable_audit: bool = True,
    ):
        super().__init__(app)

        # Composants (utilise les instances globales si non fournis)
        self._governor = governor or get_governor()
        self._observer = observer or get_observer()
        self._circuit_breaker = circuit_breaker or get_circuit_breaker("api")
        self._back_pressure = back_pressure or get_back_pressure("api")
        self._audit_logger = audit_logger or get_audit_logger()

        # Flags d'activation
        self._enable_back_pressure = enable_back_pressure
        self._enable_circuit_breaker = enable_circuit_breaker
        self._enable_governance = enable_governance
        self._enable_observability = enable_observability
        self._enable_audit = enable_audit

        logger.info("[ENTERPRISE_MIDDLEWARE] Initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Traite une requête."""
        # Skip pour endpoints publics
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Extraire informations
        tenant_id = request.headers.get("X-Tenant-ID", "unknown")
        user_id = getattr(request.state, "user_id", None)
        method = request.method
        endpoint = self._normalize_path(request.url.path)
        request_id = request.headers.get("X-Request-ID")

        start_time = time.perf_counter()
        status_code = 500
        error_type = None

        try:
            # 1. Back-pressure check
            if self._enable_back_pressure:
                priority = self._get_tenant_priority(tenant_id)
                if not self._back_pressure.should_accept(priority):
                    logger.warning(f"[ENTERPRISE] Request rejected - back pressure: {tenant_id}")
                    return self._create_service_unavailable_response(
                        "Service temporarily overloaded",
                        retry_after=self._back_pressure.get_recommended_delay_ms() // 1000,
                    )

            # 2. Circuit breaker check
            if self._enable_circuit_breaker:
                if not self._circuit_breaker.can_execute():
                    logger.warning(f"[ENTERPRISE] Request rejected - circuit open")
                    return self._create_service_unavailable_response(
                        "Service temporarily unavailable",
                        retry_after=30,
                    )

            # 3. Tenant governance check
            if self._enable_governance and tenant_id != "unknown":
                decision = self._governor.check_request(tenant_id)
                if not decision.allowed:
                    logger.warning(f"[ENTERPRISE] Request throttled: {tenant_id} - {decision.reason}")

                    # Audit
                    if self._enable_audit:
                        self._audit_logger.log_event(
                            SecurityEventType.RATE_LIMIT_HIT,
                            tenant_id=tenant_id,
                            ip_address=request.client.host if request.client else None,
                            action="request",
                            outcome="blocked",
                            details={"reason": decision.reason},
                            request_id=request_id,
                        )

                    return self._create_rate_limited_response(
                        decision.reason,
                        retry_after=decision.retry_after_seconds,
                    )

                # Enregistrer début de requête
                self._governor.record_request_start(tenant_id)

            # Incrémenter compteurs
            if self._enable_back_pressure:
                self._back_pressure.increment_concurrent()

            # 4. Exécuter la requête
            try:
                response = await call_next(request)
                status_code = response.status_code

                if status_code >= 400:
                    error_type = f"http_{status_code}"

            except CircuitBreakerOpenError:
                status_code = 503
                error_type = "circuit_breaker_open"
                raise

            except Exception as e:
                status_code = 500
                error_type = type(e).__name__
                raise

            return response

        except Exception as e:
            # En cas d'erreur, créer une réponse 500
            logger.error(f"[ENTERPRISE] Request error: {e}")
            return self._create_error_response(str(e))

        finally:
            # Calculer durée
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Décrémenter compteurs
            if self._enable_back_pressure:
                self._back_pressure.decrement_concurrent()

            # 5. Enregistrer métriques
            if self._enable_observability:
                self._observer.record_request(
                    tenant_id=tenant_id,
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    latency_ms=duration_ms,
                    error_type=error_type,
                )

            # 6. Enregistrer fin de requête pour gouvernance
            if self._enable_governance and tenant_id != "unknown":
                self._governor.record_request_end(
                    tenant_id=tenant_id,
                    latency_ms=duration_ms,
                    success=status_code < 400,
                    error_type=error_type,
                )

            # 7. Enregistrer dans circuit breaker
            if self._enable_circuit_breaker:
                if status_code >= 500:
                    self._circuit_breaker._record_failure(duration_ms)
                else:
                    self._circuit_breaker._record_success(duration_ms)

            # 8. Audit des accès (seulement pour actions importantes)
            if self._enable_audit and method in ["POST", "PUT", "DELETE", "PATCH"]:
                self._audit_logger.log_event(
                    SecurityEventType.DATA_ACCESS,
                    tenant_id=tenant_id,
                    user_id=str(user_id) if user_id else None,
                    ip_address=request.client.host if request.client else None,
                    action=f"{method} {endpoint}",
                    outcome="success" if status_code < 400 else "failure",
                    details={
                        "status_code": status_code,
                        "duration_ms": duration_ms,
                    },
                    request_id=request_id,
                )

    def _is_public_path(self, path: str) -> bool:
        """Vérifie si le path est public."""
        return any(path.startswith(p) for p in self.PUBLIC_PATHS)

    def _normalize_path(self, path: str) -> str:
        """Normalise le path pour les métriques."""
        parts = path.strip('/').split('/')
        normalized = []

        for part in parts:
            # Remplacer UUIDs
            if len(part) == 36 and part.count('-') == 4:
                normalized.append('{uuid}')
            # Remplacer IDs numériques
            elif part.isdigit():
                normalized.append('{id}')
            else:
                normalized.append(part)

        return '/' + '/'.join(normalized) if normalized else '/'

    def _get_tenant_priority(self, tenant_id: str) -> int:
        """Détermine la priorité d'un tenant."""
        tier = self._governor.get_tenant_tier(tenant_id)
        priority_map = {
            TenantTier.CRITICAL: 1,
            TenantTier.PREMIUM: 2,
            TenantTier.STANDARD: 5,
            TenantTier.TRIAL: 8,
            TenantTier.SANDBOX: 10,
        }
        return priority_map.get(tier, 5)

    def _create_rate_limited_response(
        self,
        message: str,
        retry_after: Optional[int] = None,
    ) -> Response:
        """Crée une réponse 429."""
        from fastapi.responses import JSONResponse

        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)

        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limited",
                "message": message,
                "retry_after": retry_after,
            },
            headers=headers,
        )

    def _create_service_unavailable_response(
        self,
        message: str,
        retry_after: Optional[int] = None,
    ) -> Response:
        """Crée une réponse 503."""
        from fastapi.responses import JSONResponse

        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)

        return JSONResponse(
            status_code=503,
            content={
                "error": "service_unavailable",
                "message": message,
                "retry_after": retry_after,
            },
            headers=headers,
        )

    def _create_error_response(self, message: str) -> Response:
        """Crée une réponse d'erreur."""
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "An internal error occurred",
            },
        )


def setup_enterprise_middleware(
    app,
    enable_back_pressure: bool = True,
    enable_circuit_breaker: bool = True,
    enable_governance: bool = True,
    enable_observability: bool = True,
    enable_audit: bool = True,
) -> None:
    """
    Configure le middleware enterprise sur une application FastAPI.

    Usage:
        from app.enterprise.middleware import setup_enterprise_middleware
        setup_enterprise_middleware(app)
    """
    app.add_middleware(
        EnterpriseMiddleware,
        enable_back_pressure=enable_back_pressure,
        enable_circuit_breaker=enable_circuit_breaker,
        enable_governance=enable_governance,
        enable_observability=enable_observability,
        enable_audit=enable_audit,
    )

    logger.info("[ENTERPRISE_MIDDLEWARE] Middleware configured on app")
