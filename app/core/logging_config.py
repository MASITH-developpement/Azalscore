"""
AZALS - Logging Structuré ÉLITE
================================
Logs JSON pour production, colorés pour développement.
Correlation ID pour traçabilité.
"""

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from functools import wraps

from app.core.config import get_settings

# Context variable pour correlation ID (thread-safe)
correlation_id_var: ContextVar[str | None] = ContextVar('correlation_id', default=None)
tenant_id_var: ContextVar[str | None] = ContextVar('tenant_id', default=None)


def get_correlation_id() -> str | None:
    """Récupère le correlation ID du contexte actuel."""
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """Définit le correlation ID pour le contexte actuel."""
    correlation_id_var.set(correlation_id)


def generate_correlation_id() -> str:
    """Génère un nouveau correlation ID."""
    return str(uuid.uuid4())[:8]


def get_tenant_context() -> str | None:
    """Récupère le tenant ID du contexte."""
    return tenant_id_var.get()


def set_tenant_context(tenant_id: str) -> None:
    """Définit le tenant ID pour le contexte."""
    tenant_id_var.set(tenant_id)


class JSONFormatter(logging.Formatter):
    """
    Formateur JSON pour logs structurés.
    Idéal pour agrégation (ELK, CloudWatch, Datadog).
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

        # Ajouter correlation_id si présent
        correlation_id = get_correlation_id()
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        # Ajouter tenant_id si présent
        tenant_id = get_tenant_context()
        if tenant_id:
            log_data["tenant_id"] = tenant_id

        # Ajouter exception si présente
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Ajouter extra fields
        for key, value in record.__dict__.items():
            if key not in (
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'pathname', 'process', 'processName', 'relativeCreated',
                'stack_info', 'exc_info', 'exc_text', 'message', 'taskName'
            ):
                log_data[key] = value

        return json.dumps(log_data, default=str)


class ColoredFormatter(logging.Formatter):
    """
    Formateur coloré pour développement.
    Facilite la lecture des logs en local.
    """

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, '')
        reset = self.RESET

        # Format de base
        timestamp = datetime.now().strftime('%H:%M:%S')
        level = record.levelname.ljust(8)

        # Correlation ID
        correlation_id = get_correlation_id()
        corr_str = f"[{correlation_id}] " if correlation_id else ""

        # Tenant ID
        tenant_id = get_tenant_context()
        tenant_str = f"({tenant_id}) " if tenant_id else ""

        message = f"{timestamp} {color}{level}{reset} {corr_str}{tenant_str}{record.getMessage()}"

        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: str | None = None,
    verbose: bool = False
) -> None:
    """
    Configure le logging pour l'application.

    Args:
        level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Utiliser le format JSON (production)
        log_file: Fichier de log optionnel
        verbose: Mode verbose (log tout, meme les librairies)
    """
    import os
    settings = get_settings()

    # Mode verbose force depuis env
    verbose = verbose or os.environ.get("LOG_VERBOSE", "false").lower() == "true"

    # Determiner le niveau effectif
    effective_level = "DEBUG" if verbose else level

    # Déterminer le format selon l'environnement
    formatter = JSONFormatter() if json_format or settings.is_production else ColoredFormatter()

    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Handler fichier (optionnel)
    handlers = [console_handler]
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())  # Toujours JSON en fichier
        handlers.append(file_handler)

    # Configuration root logger
    logging.basicConfig(
        level=getattr(logging, effective_level.upper()),
        handlers=handlers,
        force=True
    )

    # Configuration des loggers selon mode verbose
    if verbose:
        # Mode verbose: tout logger en DEBUG
        logging.getLogger("uvicorn").setLevel(logging.DEBUG)
        logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)
        logging.getLogger("uvicorn.error").setLevel(logging.DEBUG)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
        logging.getLogger("sqlalchemy.pool").setLevel(logging.DEBUG)
        logging.getLogger("fastapi").setLevel(logging.DEBUG)
        logging.getLogger("httpx").setLevel(logging.DEBUG)
        logging.getLogger("httpcore").setLevel(logging.DEBUG)
        _logger = logging.getLogger(__name__)
        _logger.info("[VERBOSE] Mode verbose active - tous les logs sont en DEBUG")
    else:
        # Mode normal: reduire le bruit des librairies
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(
            logging.DEBUG if settings.debug else logging.WARNING
        )
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger configuré."""
    return logging.getLogger(name)


# Décorateur pour logger les performances
def log_performance(logger: logging.Logger | None = None, level: str = "INFO"):
    """
    Décorateur pour mesurer et logger le temps d'exécution.

    Usage:
        @log_performance()
        def my_function():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)

            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                log_method = getattr(logger, level.lower())
                log_method(
                    f"{func.__name__} completed",
                    extra={
                        "function": func.__name__,
                        "duration_ms": round(elapsed * 1000, 2),
                        "status": "success"
                    }
                )
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                logger.error(
                    "%s failed: %s", func.__name__, e,
                    extra={
                        "function": func.__name__,
                        "duration_ms": round(elapsed * 1000, 2),
                        "status": "error",
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


# Décorateur async
def log_performance_async(logger: logging.Logger | None = None, level: str = "INFO"):
    """Version async du décorateur log_performance."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)

            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                log_method = getattr(logger, level.lower())
                log_method(
                    f"{func.__name__} completed",
                    extra={
                        "function": func.__name__,
                        "duration_ms": round(elapsed * 1000, 2),
                        "status": "success"
                    }
                )
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                logger.error(
                    "%s failed: %s", func.__name__, e,
                    extra={
                        "function": func.__name__,
                        "duration_ms": round(elapsed * 1000, 2),
                        "status": "error",
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


class LogContext:
    """
    Context manager pour ajouter des données aux logs.

    Usage:
        with LogContext(user_id=123, action="update"):
            logger.info("Processing...")
    """

    def __init__(self, **kwargs):
        self.extra = kwargs
        self.old_factory = None

    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()

        extra = self.extra

        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in extra.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)
        return False
