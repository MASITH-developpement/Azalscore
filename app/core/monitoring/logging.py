"""
AZALS - Structured Logging
==========================
JSON logging pour observabilité production.
"""

import json
import logging
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Callable, Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


# ============================================================================
# FORMATTER JSON
# ============================================================================

class JSONFormatter(logging.Formatter):
    """
    Formatter qui produit des logs structurés en JSON.
    Compatible avec ELK Stack, Datadog, CloudWatch, etc.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Ajouter les extras si présents
        if hasattr(record, "tenant_id"):
            log_data["tenant_id"] = record.tenant_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        if hasattr(record, "operation"):
            log_data["operation"] = record.operation
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data

        # Ajouter exception si présente
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }

        return json.dumps(log_data, ensure_ascii=False, default=str)


# ============================================================================
# CONFIGURATION LOGGING
# ============================================================================

def setup_logging(
    level: str = "INFO",
    json_output: bool = True,
    include_stdlib: bool = False
) -> None:
    """
    Configure le système de logging.

    Args:
        level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: True pour JSON, False pour format lisible
        include_stdlib: Inclure les loggers de bibliothèques tierces
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Handler console
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    if json_output:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        ))

    # Configuration du logger racine AZALS
    azals_logger = logging.getLogger("azals")
    azals_logger.setLevel(log_level)
    azals_logger.handlers = [handler]
    azals_logger.propagate = False

    # Réduire le bruit des bibliothèques tierces
    if not include_stdlib:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)


# ============================================================================
# LOGGER CONTEXTUEL
# ============================================================================

class ContextualLogger:
    """
    Logger enrichi avec contexte automatique.
    Ajoute tenant_id, user_id, request_id aux logs.
    """

    def __init__(self, name: str):
        self._logger = logging.getLogger(f"azals.{name}")
        self._context = {}

    def bind(self, **kwargs) -> "ContextualLogger":
        """Crée un nouveau logger avec contexte additionnel."""
        new_logger = ContextualLogger(self._logger.name.replace("azals.", ""))
        new_logger._context = {**self._context, **kwargs}
        return new_logger

    def _log(self, level: int, msg: str, *args, **kwargs):
        """Log interne avec contexte."""
        extra = kwargs.pop("extra", {})
        extra.update(self._context)

        # Extraire les champs spéciaux
        for key in ["tenant_id", "user_id", "request_id", "trace_id",
                    "operation", "duration_ms", "extra_data"]:
            if key in kwargs:
                extra[key] = kwargs.pop(key)

        self._logger.log(level, msg, *args, extra=extra, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        self._log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self._log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        self._log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        self._log(logging.CRITICAL, msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        kwargs["exc_info"] = True
        self._log(logging.ERROR, msg, *args, **kwargs)


def get_logger(name: str) -> ContextualLogger:
    """
    Retourne un logger contextuel pour le module spécifié.

    Args:
        name: Nom du module (ex: "commercial", "finance", "ai_assistant")

    Returns:
        Logger enrichi avec contexte
    """
    return ContextualLogger(name)


# ============================================================================
# MIDDLEWARE LOGGING
# ============================================================================

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware de logging des requêtes HTTP.
    - Génère un request_id unique
    - Log entrée/sortie de chaque requête
    - Mesure la durée
    """

    def __init__(self, app, logger_name: str = "http"):
        super().__init__(app)
        self.logger = get_logger(logger_name)

    async def dispatch(self, request: Request, call_next: Callable):
        # Générer request_id
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        trace_id = request.headers.get("X-Trace-ID", request_id)

        # Stocker dans request.state
        request.state.request_id = request_id
        request.state.trace_id = trace_id

        # Extraction contexte
        tenant_id = getattr(request.state, "tenant_id", None)
        if not tenant_id:
            tenant_id = request.headers.get("X-Tenant-ID", "unknown")

        # Logger contextualisé
        log = self.logger.bind(
            request_id=request_id,
            trace_id=trace_id,
            tenant_id=tenant_id
        )

        # Log entrée
        log.info(
            f"Request started: {request.method} {request.url.path}",
            operation="http_request_start",
            extra_data={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("User-Agent", ""),
            }
        )

        # Exécution
        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            status_code = response.status_code
            error_msg = None
        except Exception as e:
            status_code = 500
            error_msg = str(e)
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log sortie
            if status_code >= 500:
                log.error(
                    f"Request failed: {request.method} {request.url.path} -> {status_code}",
                    operation="http_request_error",
                    duration_ms=duration_ms,
                    extra_data={
                        "status_code": status_code,
                        "error": error_msg,
                    }
                )
            elif status_code >= 400:
                log.warning(
                    f"Request client error: {request.method} {request.url.path} -> {status_code}",
                    operation="http_request_client_error",
                    duration_ms=duration_ms,
                    extra_data={"status_code": status_code}
                )
            else:
                log.info(
                    f"Request completed: {request.method} {request.url.path} -> {status_code}",
                    operation="http_request_complete",
                    duration_ms=duration_ms,
                    extra_data={"status_code": status_code}
                )

        # Ajouter headers de traçabilité à la réponse
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id

        return response


# ============================================================================
# LOGS AUDIT MÉTIER
# ============================================================================

class AuditLogger:
    """
    Logger spécialisé pour l'audit métier.
    Trace les actions importantes pour conformité.
    """

    def __init__(self):
        self.logger = get_logger("audit")

    def log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: Any,
        tenant_id: str,
        user_id: int,
        details: Optional[dict] = None,
        result: str = "success"
    ):
        """
        Log une action métier auditable.

        Args:
            action: Type d'action (create, update, delete, validate, export)
            resource_type: Type de ressource (invoice, order, user, etc.)
            resource_id: ID de la ressource
            tenant_id: ID du tenant
            user_id: ID de l'utilisateur
            details: Détails additionnels
            result: success, failure, pending
        """
        self.logger.info(
            f"Audit: {action} {resource_type} {resource_id}",
            tenant_id=tenant_id,
            user_id=user_id,
            operation=f"audit_{action}",
            extra_data={
                "action": action,
                "resource_type": resource_type,
                "resource_id": str(resource_id),
                "result": result,
                "details": details or {}
            }
        )

    def log_red_point(
        self,
        decision_id: int,
        action: str,
        tenant_id: str,
        first_validator: int,
        second_validator: Optional[int] = None,
        details: Optional[dict] = None
    ):
        """
        Log spécifique pour les points rouges (double validation).
        Critique pour la traçabilité des décisions sensibles.
        """
        self.logger.warning(
            f"RED POINT: Decision {decision_id} - {action}",
            tenant_id=tenant_id,
            operation="red_point_action",
            extra_data={
                "decision_id": decision_id,
                "action": action,
                "first_validator": first_validator,
                "second_validator": second_validator,
                "requires_second_validation": second_validator is None and action == "first_confirmation",
                "details": details or {}
            }
        )


# Instance singleton pour audit
audit_logger = AuditLogger()
