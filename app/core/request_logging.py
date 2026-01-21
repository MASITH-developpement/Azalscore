"""
AZALS - Middleware de Logging des Requetes
==========================================
Log detaille de toutes les requetes HTTP pour debug et audit.
Active via LOG_VERBOSE=true ou LOG_REQUESTS=true.
"""

import os
import time
from datetime import datetime
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import (
    get_logger,
    get_correlation_id,
    set_correlation_id,
    generate_correlation_id,
    set_tenant_context,
)

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour logger toutes les requetes et reponses.

    Active par defaut en mode verbose (LOG_VERBOSE=true).
    Peut etre active separement avec LOG_REQUESTS=true.

    Logs:
    - Methode HTTP et path
    - Headers (filtres pour securite)
    - Temps de reponse
    - Code de statut
    - Taille de la reponse
    - Erreurs eventuelles
    """

    # Headers sensibles a ne pas logger
    SENSITIVE_HEADERS = {
        'authorization',
        'cookie',
        'x-api-key',
        'x-auth-token',
        'x-secret',
    }

    # Paths a exclure du logging detaille (health checks, etc.)
    EXCLUDED_PATHS = {
        '/health',
        '/health/live',
        '/health/ready',
        '/health/startup',
        '/metrics',
    }

    def __init__(self, app, log_headers: bool = True, log_body: bool = False):
        super().__init__(app)
        self.log_headers = log_headers
        self.log_body = log_body
        self.enabled = self._is_enabled()

    def _is_enabled(self) -> bool:
        """Verifie si le logging des requetes est active."""
        verbose = os.environ.get("LOG_VERBOSE", "false").lower() == "true"
        requests_logging = os.environ.get("LOG_REQUESTS", "false").lower() == "true"
        return verbose or requests_logging

    def _filter_headers(self, headers: dict) -> dict:
        """Filtre les headers sensibles."""
        filtered = {}
        for key, value in headers.items():
            key_lower = key.lower()
            if key_lower in self.SENSITIVE_HEADERS:
                filtered[key] = "[REDACTED]"
            else:
                filtered[key] = value
        return filtered

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Si desactive, passer directement
        if not self.enabled:
            return await call_next(request)

        # Exclure certains paths du logging detaille
        path = request.url.path
        if path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Generer ou recuperer correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = generate_correlation_id()
        set_correlation_id(correlation_id)

        # Recuperer tenant ID
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            set_tenant_context(tenant_id)

        # Demarrer le timer
        start_time = time.perf_counter()

        # Log de la requete entrante
        log_data = {
            "event": "request_start",
            "method": request.method,
            "path": path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else "unknown",
            "correlation_id": correlation_id,
            "tenant_id": tenant_id,
        }

        if self.log_headers:
            headers = dict(request.headers)
            log_data["headers"] = self._filter_headers(headers)

        logger.info(
            f"[REQUEST] {request.method} {path}",
            extra=log_data
        )

        # Executer la requete
        response = None
        error = None
        try:
            response = await call_next(request)
        except Exception as e:
            error = e
            logger.error(
                f"[REQUEST] {request.method} {path} - Exception: {type(e).__name__}: {e}",
                extra={
                    "event": "request_error",
                    "method": request.method,
                    "path": path,
                    "correlation_id": correlation_id,
                    "tenant_id": tenant_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True
            )
            raise

        # Calculer le temps de reponse
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log de la reponse
        status_code = response.status_code if response else 500

        # Determiner le niveau de log selon le status code
        if status_code >= 500:
            log_level = "error"
        elif status_code >= 400:
            log_level = "warning"
        else:
            log_level = "info"

        log_method = getattr(logger, log_level)
        log_method(
            f"[RESPONSE] {request.method} {path} - {status_code} ({duration_ms:.2f}ms)",
            extra={
                "event": "request_complete",
                "method": request.method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "correlation_id": correlation_id,
                "tenant_id": tenant_id,
            }
        )

        # Ajouter le correlation ID a la reponse
        if response:
            response.headers["X-Correlation-ID"] = correlation_id

        return response


def setup_request_logging(app) -> None:
    """
    Configure le middleware de logging des requetes.

    Usage:
        from app.core.request_logging import setup_request_logging
        setup_request_logging(app)
    """
    # Verifier si le logging est active
    verbose = os.environ.get("LOG_VERBOSE", "false").lower() == "true"
    requests_logging = os.environ.get("LOG_REQUESTS", "false").lower() == "true"

    if verbose or requests_logging:
        app.add_middleware(RequestLoggingMiddleware)
        logger.info("[REQUEST_LOGGING] Middleware de logging des requetes active")
    else:
        logger.debug("[REQUEST_LOGGING] Middleware desactive (LOG_VERBOSE=false et LOG_REQUESTS=false)")
