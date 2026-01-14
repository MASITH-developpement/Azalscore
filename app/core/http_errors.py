"""
AZALS - Gestion Centralisee des Erreurs HTTP
=============================================
Module de gestion INDUSTRIELLE des erreurs HTTP (401, 403, 404, 500)
Compatible V0, production-ready, tracable.

OBJECTIFS:
- Reponses JSON standardisees
- Logging structure (niveau ERROR pour 500)
- Tracabilite via trace_id pour les erreurs serveur
- Aucune fuite d'information sensible
- Compatible production (uvicorn/gunicorn)
"""

import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging_config import get_logger

logger = get_logger(__name__)


# ===========================================================================
# SCHEMAS DE REPONSE STANDARDISES
# ===========================================================================

def create_error_response(
    error: str,
    message: str,
    code: int,
    path: str | None = None,
    trace_id: str | None = None
) -> dict:
    """
    Cree une reponse d'erreur standardisee.

    Format uniforme pour TOUTES les erreurs HTTP:
    {
        "error": "<type_erreur>",
        "message": "<message_humain>",
        "code": <code_http>,
        "path": "<chemin_requete>" (optionnel, pour 404),
        "trace_id": "<uuid>" (optionnel, pour 500)
    }
    """
    response = {
        "error": error,
        "message": message,
        "code": code
    }

    if path is not None:
        response["path"] = path

    if trace_id is not None:
        response["trace_id"] = trace_id

    return response


# ===========================================================================
# EXCEPTION HANDLERS
# ===========================================================================

async def unauthorized_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handler pour erreur 401 - Unauthorized

    Declenchee quand:
    - Token JWT absent ou invalide
    - Session expiree
    - Authentification requise
    """
    logger.warning(
        "Erreur 401: Authentification requise",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown",
            "error_type": "unauthorized"
        }
    )

    return JSONResponse(
        status_code=401,
        content=create_error_response(
            error="unauthorized",
            message="Authentication required",
            code=401
        ),
        headers={"WWW-Authenticate": "Bearer"}
    )


async def forbidden_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handler pour erreur 403 - Forbidden

    Declenchee quand:
    - Utilisateur authentifie mais sans les droits requis
    - Acces a une ressource restreinte
    - Tenant invalide ou non autorise
    """
    logger.warning(
        "Erreur 403: Acces refuse",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown",
            "error_type": "forbidden",
            "tenant_id": getattr(request.state, "tenant_id", None)
        }
    )

    return JSONResponse(
        status_code=403,
        content=create_error_response(
            error="forbidden",
            message="Access denied",
            code=403
        )
    )


async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handler pour erreur 404 - Not Found

    Declenchee quand:
    - Route API inexistante
    - Ressource non trouvee
    - ID invalide (ressource supprimee ou inexistante)
    """
    path = str(request.url.path)

    logger.info(
        "Erreur 404: Ressource non trouvee",
        extra={
            "path": path,
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown",
            "error_type": "not_found"
        }
    )

    return JSONResponse(
        status_code=404,
        content=create_error_response(
            error="not_found",
            message="Resource not found",
            code=404,
            path=path
        )
    )


async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler pour erreur 500 - Internal Server Error

    Declenchee quand:
    - Exception non geree
    - Erreur de base de donnees
    - Bug applicatif

    IMPORTANT:
    - Genere un trace_id unique pour le suivi
    - Log complet niveau ERROR
    - NE PAS exposer le message d'erreur technique
    """
    # Generer un trace_id unique pour le suivi
    trace_id = str(uuid.uuid4())[:8]  # Format court pour lisibilite

    # Recuperer le message d'erreur de maniere securisee
    error_message = str(exc) if exc else "Unknown error"

    # Log COMPLET pour diagnostic (niveau ERROR)
    logger.error(
        f"Erreur 500: {error_message}",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown",
            "error_type": "internal_error",
            "trace_id": trace_id,
            "exception_type": type(exc).__name__,
            "exception_message": error_message[:500],  # Tronquer si trop long
            "tenant_id": getattr(request.state, "tenant_id", None)
        },
        exc_info=True  # Inclure la stack trace complete
    )

    return JSONResponse(
        status_code=500,
        content=create_error_response(
            error="internal_error",
            message="Unexpected server error",
            code=500,
            trace_id=trace_id
        )
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handler pour erreur 422 - Validation Error

    Declenchee quand:
    - Donnees de requete invalides
    - Schema Pydantic non respecte
    - Parametres manquants ou mal formes
    """
    logger.warning(
        "Erreur 422: Validation echouee",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown",
            "error_type": "validation_error",
            "validation_errors": exc.errors()
        }
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Request validation failed",
            "code": 422,
            "details": exc.errors()
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handler generique pour toutes les HTTPException Starlette.

    Route vers le handler specifique selon le code d'erreur,
    ou retourne une reponse generique pour les codes non geres.
    """
    status_code = exc.status_code

    # Router vers les handlers specifiques
    if status_code == 401:
        return await unauthorized_handler(request, exc)
    elif status_code == 403:
        return await forbidden_handler(request, exc)
    elif status_code == 404:
        return await not_found_handler(request, exc)
    elif status_code >= 500:
        return await internal_error_handler(request, exc)

    # Handler generique pour les autres codes HTTP
    logger.info(
        f"Erreur HTTP {status_code}",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "status_code": status_code,
            "detail": exc.detail
        }
    )

    # Determiner le type d'erreur selon le code
    error_type = "client_error" if 400 <= status_code < 500 else "server_error"

    return JSONResponse(
        status_code=status_code,
        content=create_error_response(
            error=error_type,
            message=str(exc.detail) if exc.detail else f"HTTP {status_code}",
            code=status_code
        )
    )


# ===========================================================================
# ENREGISTREMENT DES HANDLERS
# ===========================================================================

def register_error_handlers(app: FastAPI) -> None:
    """
    Enregistre tous les handlers d'erreur sur l'application FastAPI.

    A appeler une seule fois au demarrage de l'application.

    Usage:
        from app.core.http_errors import register_error_handlers
        register_error_handlers(app)
    """
    # Handler generique pour toutes les HTTPException (inclut 401, 403, 404)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Handler specifique pour les erreurs de validation Pydantic
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    # Handler catch-all pour les exceptions non gerees (500)
    app.add_exception_handler(Exception, internal_error_handler)

    logger.info(
        "[HTTP_ERRORS] Handlers d'erreur enregistres",
        extra={
            "handlers": ["401", "403", "404", "422", "500", "generic"]
        }
    )


# ===========================================================================
# EXCEPTIONS PERSONNALISEES AZALS
# ===========================================================================

class AzalsHTTPException(HTTPException):
    """
    Exception HTTP personnalisee AZALS.

    Permet de lever des erreurs HTTP avec un format coherent.
    """

    def __init__(
        self,
        status_code: int,
        error: str,
        message: str,
        detail: str | None = None
    ):
        super().__init__(status_code=status_code, detail=detail or message)
        self.error = error
        self.message = message


class UnauthorizedException(AzalsHTTPException):
    """Exception 401 - Authentification requise."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            status_code=401,
            error="unauthorized",
            message=message
        )


class ForbiddenException(AzalsHTTPException):
    """Exception 403 - Acces refuse."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            status_code=403,
            error="forbidden",
            message=message
        )


class NotFoundException(AzalsHTTPException):
    """Exception 404 - Ressource non trouvee."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            status_code=404,
            error="not_found",
            message=message
        )


class InternalServerException(AzalsHTTPException):
    """Exception 500 - Erreur serveur interne."""

    def __init__(self, message: str = "Unexpected server error"):
        super().__init__(
            status_code=500,
            error="internal_error",
            message=message
        )
