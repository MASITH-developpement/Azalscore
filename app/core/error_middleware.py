"""
Middleware de gestion d'erreurs centralise AZALSCORE

Conformite : AZA-NF-003, Charte Developpeur
Principe : "Aucune logique de gestion d'erreur dans le code metier"

Ce middleware capture TOUTES les exceptions et les convertit en reponses HTTP appropriees.
Cela permet d'eliminer les 116 try/except P0 (validation) du code metier.

Utilise StandardError pour des reponses uniformes (compatible frontend StandardHttpError).
"""

import logging
import uuid
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError, DataError
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.errors import StandardError, ErrorCode, create_standard_error
from app.core.logging_config import get_correlation_id

logger = logging.getLogger(__name__)


def _serialize_pydantic_errors(errors: list) -> list:
    """
    Serialise les erreurs Pydantic en JSON-safe.

    Convertit les objets non serialisables (UUID, etc.) en strings.
    """
    import json

    def default_serializer(obj):
        if hasattr(obj, '__str__'):
            return str(obj)
        return repr(obj)

    # Re-serialize via JSON pour nettoyer les types
    try:
        return json.loads(json.dumps(errors, default=default_serializer))
    except Exception:
        # Fallback: convertir tout en strings
        return [{"msg": str(e)} for e in errors]


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware de gestion centralisée des erreurs

    Capture toutes les exceptions non gérées et les convertit en réponses JSON standardisées.

    Avantages :
    - Élimine les try/except du code métier
    - Réponses d'erreur cohérentes
    - Traçabilité centralisée
    - Code métier PUR
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Intercepte toutes les requêtes et gère les exceptions

        Args:
            request: Requête HTTP
            call_next: Handler suivant dans la chaîne

        Returns:
            Response HTTP (normale ou d'erreur)
        """
        try:
            # Exécution normale
            response = await call_next(request)
            return response

        except RequestValidationError as e:
            # Erreurs de validation Pydantic (requêtes malformées)
            logger.warning(
                "[ERROR_MW] Erreur de validation requête — données malformées",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": "RequestValidationError",
                    "error": str(e)[:500],
                    "consequence": "422_response"
                }
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": "Validation Error",
                    "message": "Les données fournies sont invalides",
                    "details": _serialize_pydantic_errors(e.errors())
                }
            )

        except ValidationError as e:
            # Erreurs de validation Pydantic (modèles internes)
            logger.warning(
                "[ERROR_MW] Erreur de validation Pydantic — modèle interne invalide",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": "ValidationError",
                    "error": str(e)[:500],
                    "consequence": "422_response"
                }
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": "Validation Error",
                    "message": "Les données fournies sont invalides",
                    "details": _serialize_pydantic_errors(e.errors())
                }
            )

        except ValueError as e:
            # Erreurs de valeur (business logic validation)
            # C'est le type d'erreur principal leve par le code metier pur
            correlation_id = get_correlation_id() or str(uuid.uuid4())

            error = create_standard_error(
                error_code=ErrorCode.VALIDATION_ERROR,
                message=str(e),
                http_status=400,
                request_id=correlation_id,
                path=request.url.path
            )

            logger.warning(
                "validation_error",
                extra={
                    "error_code": error.error_code,
                    "message": error.message,
                    "path": request.url.path,
                    "method": request.method,
                    "correlation_id": correlation_id
                }
            )

            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error.model_dump(mode="json")
            )

        except IntegrityError as e:
            # Erreurs d'integrite base de donnees (contraintes)
            correlation_id = get_correlation_id() or str(uuid.uuid4())
            error_detail = str(e.orig)[:500] if hasattr(e, 'orig') else str(e)[:500]

            error = create_standard_error(
                error_code=ErrorCode.INTEGRITY_ERROR,
                message="Cette operation viole une contrainte d'integrite",
                http_status=409,
                request_id=correlation_id,
                path=request.url.path,
                details={"db_error": error_detail}
            )

            logger.error(
                "integrity_error",
                extra={
                    "error_code": error.error_code,
                    "path": request.url.path,
                    "method": request.method,
                    "db_error": error_detail,
                    "correlation_id": correlation_id
                }
            )

            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=error.model_dump(mode="json")
            )

        except OperationalError as e:
            # Erreurs opérationnelles base de données (connexion, etc.)
            logger.error(
                "[ERROR_MW] Erreur opérationnelle DB — connexion ou infrastructure",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": "OperationalError",
                    "error": str(e)[:500],
                    "consequence": "503_response"
                }
            )
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "Service Unavailable",
                    "message": "Le service base de données est temporairement indisponible"
                }
            )

        except DataError as e:
            # Erreurs de données base de données (type mismatch, etc.)
            logger.error(
                "[ERROR_MW] Erreur de données DB — type mismatch ou format invalide",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": "DataError",
                    "error": str(e)[:500],
                    "consequence": "400_response"
                }
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Bad Request",
                    "message": "Les données fournies ne correspondent pas au format attendu"
                }
            )

        except PermissionError as e:
            # Erreurs de permission
            correlation_id = get_correlation_id() or str(uuid.uuid4())

            error = create_standard_error(
                error_code=ErrorCode.PERMISSION_DENIED,
                message=str(e) or "Vous n'avez pas les permissions necessaires",
                http_status=403,
                request_id=correlation_id,
                path=request.url.path
            )

            logger.warning(
                "permission_denied",
                extra={
                    "error_code": error.error_code,
                    "path": request.url.path,
                    "method": request.method,
                    "correlation_id": correlation_id
                }
            )

            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=error.model_dump(mode="json")
            )

        except FileNotFoundError as e:
            # Erreurs de fichier non trouve
            correlation_id = get_correlation_id() or str(uuid.uuid4())

            error = create_standard_error(
                error_code=ErrorCode.FILE_NOT_FOUND,
                message=str(e) or "Le fichier ou la ressource demandee n'existe pas",
                http_status=404,
                request_id=correlation_id,
                path=request.url.path
            )

            logger.warning(
                "resource_not_found",
                extra={
                    "error_code": error.error_code,
                    "path": request.url.path,
                    "method": request.method,
                    "correlation_id": correlation_id
                }
            )

            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error.model_dump(mode="json")
            )

        except NotImplementedError as e:
            # Fonctionnalités non implémentées
            logger.warning(
                "[ERROR_MW] Fonctionnalité non implémentée",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": "NotImplementedError",
                    "error": str(e)[:500],
                    "consequence": "501_response"
                }
            )
            return JSONResponse(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                content={
                    "error": "Not Implemented",
                    "message": str(e) or "Cette fonctionnalité n'est pas encore implémentée"
                }
            )

        except TimeoutError as e:
            # Erreurs de timeout
            logger.error(
                "[ERROR_MW] Timeout — opération trop longue",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": "TimeoutError",
                    "error": str(e)[:500],
                    "consequence": "504_response"
                }
            )
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={
                    "error": "Timeout",
                    "message": "L'opération a pris trop de temps à s'exécuter"
                }
            )

        except Exception as e:
            # Erreur generique inattendue
            correlation_id = get_correlation_id() or str(uuid.uuid4())

            error = create_standard_error(
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                message="Une erreur inattendue s'est produite",
                http_status=500,
                request_id=correlation_id,
                path=request.url.path,
                details={"exception_type": type(e).__name__}
            )

            logger.exception(
                "internal_server_error",
                extra={
                    "error_code": error.error_code,
                    "path": request.url.path,
                    "method": request.method,
                    "exception_type": type(e).__name__,
                    "exception_message": str(e)[:500],
                    "correlation_id": correlation_id
                }
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error.model_dump(mode="json")
            )


def setup_error_handling(app):
    """
    Configure le middleware de gestion d'erreurs

    Args:
        app: Instance FastAPI
    """
    app.add_middleware(ErrorHandlingMiddleware)
    logger.info("Error handling middleware installed")


# Types d'exceptions gérées par le middleware
HANDLED_EXCEPTIONS = [
    RequestValidationError,
    ValidationError,
    ValueError,
    IntegrityError,
    OperationalError,
    DataError,
    PermissionError,
    FileNotFoundError,
    NotImplementedError,
    TimeoutError,
]


def get_handled_exception_types():
    """Retourne la liste des types d'exceptions gérées"""
    return HANDLED_EXCEPTIONS
