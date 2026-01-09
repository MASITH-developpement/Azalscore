"""
AZALS MODULE GUARDIAN - Middleware
==================================

Middleware pour l'interception automatique des erreurs HTTP.
Enregistre les erreurs détectées dans le système GUARDIAN.

IMPORTANT: Ce module utilise les fonctions SAFE de error_response.py qui:
- Ne dépendent JAMAIS d'un fichier HTML pour répondre
- Renvoient toujours une réponse HTTP valide (JSON en fallback)
- Ne lèvent jamais d'exception non gérée
"""

import traceback
import hashlib
from datetime import datetime
from typing import Optional, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.core.database import SessionLocal
from app.core.logging_config import get_logger, get_correlation_id

from .models import (
    ErrorDetection,
    ErrorSeverity,
    ErrorSource,
    ErrorType,
    Environment,
    GuardianConfig,
)
from .service import GuardianService
from .schemas import ErrorDetectionCreate

# Import des fonctions SAFE de gestion des erreurs
# Ces fonctions sont dans un module séparé pour éviter les imports circulaires
from .error_response import (
    build_error_response,
    build_safe_error_response,
    get_error_type_for_status,
    get_error_severity_for_status,
    DEFAULT_ERROR_MESSAGES,
)

logger = get_logger(__name__)

# Flag global pour savoir si les tables existent
_tables_verified = False
_tables_exist = False


def _check_tables_exist() -> bool:
    """Vérifie si les tables du système de correction existent."""
    global _tables_verified, _tables_exist

    if _tables_verified:
        return _tables_exist

    try:
        db = SessionLocal()
        try:
            # Tenter une requête simple
            db.query(GuardianConfig).limit(1).all()
            _tables_exist = True
        except (OperationalError, ProgrammingError):
            # Tables non créées
            _tables_exist = False
        finally:
            db.close()
    except Exception:
        _tables_exist = False

    _tables_verified = True
    return _tables_exist


class GuardianMiddleware(BaseHTTPMiddleware):
    """
    Middleware GUARDIAN pour l'interception automatique des erreurs.

    Ce middleware:
    - Intercepte toutes les erreurs HTTP 4xx et 5xx
    - Enregistre les erreurs dans le système GUARDIAN
    - Déclenche l'analyse et la correction automatique si configuré
    - Préserve le comportement original de l'application

    IMPORTANT: Ce middleware ne modifie pas la réponse originale.
    L'erreur est transmise à GUARDIAN en parallèle.
    """

    def __init__(self, app, environment: str = "production"):
        super().__init__(app)
        self.environment = self._parse_environment(environment)
        # Routes à exclure de la surveillance
        self.excluded_paths = {
            "/health",
            "/health/live",
            "/health/ready",
            "/health/startup",
            "/health/db",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/guardian",  # Éviter boucle infinie
        }

    def _parse_environment(self, env: str) -> Environment:
        """Parse l'environnement."""
        env_map = {
            "production": Environment.PRODUCTION,
            "staging": Environment.BETA,
            "beta": Environment.BETA,
            "development": Environment.SANDBOX,
            "sandbox": Environment.SANDBOX,
            "test": Environment.SANDBOX,
        }
        return env_map.get(env.lower(), Environment.PRODUCTION)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Intercepte les requêtes et enregistre les erreurs."""
        # Ignorer certaines routes
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            return await call_next(request)

        # Extraire le tenant_id du header
        tenant_id = request.headers.get("X-Tenant-ID")

        # Exécuter la requête
        start_time = datetime.utcnow()
        response = None
        error_captured = None

        try:
            response = await call_next(request)

            # Vérifier si c'est une erreur HTTP
            if response.status_code >= 400:
                await self._record_http_error(
                    request=request,
                    response=response,
                    tenant_id=tenant_id,
                    start_time=start_time
                )

            return response

        except HTTPException as e:
            # Erreur HTTP FastAPI
            error_captured = e
            await self._record_exception(
                request=request,
                exception=e,
                tenant_id=tenant_id,
                start_time=start_time,
                http_status=e.status_code
            )
            raise

        except Exception as e:
            # Erreur non gérée
            error_captured = e
            await self._record_exception(
                request=request,
                exception=e,
                tenant_id=tenant_id,
                start_time=start_time,
                http_status=500
            )
            raise

    async def _record_http_error(
        self,
        request: Request,
        response: Response,
        tenant_id: Optional[str],
        start_time: datetime
    ):
        """Enregistre une erreur HTTP."""
        if not tenant_id:
            # Pas de tenant, on ne peut pas enregistrer
            return

        # Vérifier si les tables existent (évite les erreurs au démarrage)
        if not _check_tables_exist():
            return

        try:
            db = SessionLocal()
            try:
                # Vérifier si le système est activé pour ce tenant
                config = db.query(GuardianConfig).filter(
                    GuardianConfig.tenant_id == tenant_id
                ).first()

                if not config or not config.is_enabled:
                    return

                # Déterminer la sévérité
                severity = self._determine_severity(response.status_code)

                # Déterminer le type d'erreur
                error_type = self._determine_error_type(response.status_code)

                # Créer l'enregistrement
                error_data = ErrorDetectionCreate(
                    severity=severity,
                    source=ErrorSource.API_ERROR,
                    error_type=error_type,
                    environment=self.environment,
                    error_message=f"HTTP {response.status_code} on {request.method} {request.url.path}",
                    module=self._extract_module(request.url.path),
                    route=str(request.url.path),
                    http_status=response.status_code,
                    http_method=request.method,
                    correlation_id=get_correlation_id(),
                    context_data={
                        "query_params": dict(request.query_params),
                        "path_params": dict(request.path_params) if hasattr(request, 'path_params') else {},
                        "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000
                    }
                )

                service = GuardianService(db, tenant_id)
                service.detect_error(error_data)

            finally:
                db.close()

        except (OperationalError, ProgrammingError):
            # Tables non créées - ignorer silencieusement
            global _tables_verified, _tables_exist
            _tables_verified = True
            _tables_exist = False
        except Exception as e:
            # Ne jamais faire échouer la requête
            logger.debug(f"Error recording middleware: {e}")

    async def _record_exception(
        self,
        request: Request,
        exception: Exception,
        tenant_id: Optional[str],
        start_time: datetime,
        http_status: int = 500
    ):
        """Enregistre une exception."""
        if not tenant_id:
            return

        # Vérifier si les tables existent (évite les erreurs au démarrage)
        if not _check_tables_exist():
            return

        try:
            db = SessionLocal()
            try:
                # Vérifier si le système est activé
                config = db.query(GuardianConfig).filter(
                    GuardianConfig.tenant_id == tenant_id
                ).first()

                if not config or not config.is_enabled:
                    return

                # Extraire le stack trace
                stack_trace = traceback.format_exc()

                # Anonymiser le stack trace (enlever les chemins absolus)
                stack_trace = self._anonymize_stack_trace(stack_trace)

                severity = self._determine_severity(http_status)
                error_type = self._map_exception_to_type(exception)

                error_data = ErrorDetectionCreate(
                    severity=severity,
                    source=ErrorSource.BACKEND_LOG,
                    error_type=error_type,
                    environment=self.environment,
                    error_message=str(exception)[:1000],
                    module=self._extract_module(request.url.path),
                    route=str(request.url.path),
                    function_name=exception.__class__.__name__,
                    stack_trace=stack_trace[:5000] if stack_trace else None,
                    http_status=http_status,
                    http_method=request.method,
                    correlation_id=get_correlation_id(),
                    context_data={
                        "exception_type": type(exception).__name__,
                        "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000
                    }
                )

                service = GuardianService(db, tenant_id)
                service.detect_error(error_data)

            finally:
                db.close()

        except (OperationalError, ProgrammingError):
            # Tables non créées - ignorer silencieusement
            global _tables_verified, _tables_exist
            _tables_verified = True
            _tables_exist = False
        except Exception as e:
            # Ne jamais faire échouer la requête
            logger.debug(f"Exception recording error: {e}")

    def _determine_severity(self, status_code: int) -> ErrorSeverity:
        """Détermine la sévérité selon le code HTTP."""
        if status_code >= 500:
            return ErrorSeverity.CRITICAL
        elif status_code == 429:  # Rate limit
            return ErrorSeverity.WARNING
        elif status_code in [401, 403]:  # Auth errors
            return ErrorSeverity.MAJOR
        elif status_code >= 400:
            return ErrorSeverity.MINOR
        return ErrorSeverity.INFO

    def _determine_error_type(self, status_code: int) -> ErrorType:
        """Détermine le type d'erreur selon le code HTTP."""
        error_map = {
            400: ErrorType.VALIDATION,
            401: ErrorType.AUTHENTICATION,
            403: ErrorType.AUTHORIZATION,
            404: ErrorType.UNKNOWN,
            408: ErrorType.TIMEOUT,
            409: ErrorType.DATA_INTEGRITY,
            422: ErrorType.VALIDATION,
            429: ErrorType.RATE_LIMIT,
            500: ErrorType.EXCEPTION,
            502: ErrorType.NETWORK,
            503: ErrorType.DEPENDENCY,
            504: ErrorType.TIMEOUT,
        }
        return error_map.get(status_code, ErrorType.UNKNOWN)

    def _map_exception_to_type(self, exception: Exception) -> ErrorType:
        """Mappe une exception Python vers un ErrorType."""
        exception_map = {
            "ValueError": ErrorType.VALIDATION,
            "TypeError": ErrorType.EXCEPTION,
            "KeyError": ErrorType.EXCEPTION,
            "AttributeError": ErrorType.EXCEPTION,
            "ConnectionError": ErrorType.NETWORK,
            "TimeoutError": ErrorType.TIMEOUT,
            "PermissionError": ErrorType.AUTHORIZATION,
            "SQLAlchemyError": ErrorType.DATABASE,
            "IntegrityError": ErrorType.DATA_INTEGRITY,
            "OperationalError": ErrorType.DATABASE,
        }

        for exc_name, error_type in exception_map.items():
            if exc_name in type(exception).__name__:
                return error_type

        return ErrorType.EXCEPTION

    def _extract_module(self, path: str) -> Optional[str]:
        """Extrait le nom du module depuis le chemin."""
        # /api/v1/commercial/... -> commercial
        parts = path.strip("/").split("/")
        if len(parts) >= 3 and parts[0] == "api" and parts[1] == "v1":
            return parts[2]
        elif len(parts) >= 2 and parts[0] == "api":
            return parts[1]
        return None

    def _anonymize_stack_trace(self, stack_trace: str) -> str:
        """
        Anonymise le stack trace pour la conformité RGPD.
        Supprime les chemins absolus et autres informations sensibles.
        """
        if not stack_trace:
            return stack_trace

        # Remplacer les chemins absolus par des chemins relatifs
        lines = stack_trace.split("\n")
        anonymized_lines = []

        for line in lines:
            # Remplacer /home/user/... par ./...
            if "/home/" in line:
                parts = line.split("/home/")
                if len(parts) > 1:
                    # Trouver le premier / après /home/user/
                    remaining = parts[1]
                    slash_pos = remaining.find("/", remaining.find("/") + 1)
                    if slash_pos > 0:
                        line = parts[0] + "./" + remaining[slash_pos + 1:]

            anonymized_lines.append(line)

        return "\n".join(anonymized_lines)


def setup_guardian_middleware(app, environment: str = "production"):
    """Configure le middleware GUARDIAN sur l'application FastAPI."""
    app.add_middleware(GuardianMiddleware, environment=environment)
    logger.info(f"GUARDIAN middleware initialized for environment: {environment}")
