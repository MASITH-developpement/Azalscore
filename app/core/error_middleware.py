"""
Middleware de gestion d'erreurs centralisé AZALSCORE

Conformité : AZA-NF-003, Charte Développeur
Principe : "Aucune logique de gestion d'erreur dans le code métier"

Ce middleware capture TOUTES les exceptions et les convertit en réponses HTTP appropriées.
Cela permet d'éliminer les 116 try/except P0 (validation) du code métier.
"""

import logging
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError, DataError
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


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
                    "details": e.errors()
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
                    "details": e.errors()
                }
            )

        except ValueError as e:
            # Erreurs de valeur (business logic validation)
            # C'est le type d'erreur principal levé par le code métier pur
            logger.warning(
                "[ERROR_MW] Erreur métier (ValueError) — validation business échouée",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": "ValueError",
                    "error": str(e)[:500],
                    "consequence": "400_response"
                }
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Bad Request",
                    "message": str(e)
                }
            )

        except IntegrityError as e:
            # Erreurs d'intégrité base de données (contraintes)
            logger.error(
                "[ERROR_MW] Erreur d'intégrité DB — contrainte violée",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": "IntegrityError",
                    "error": str(e.orig)[:500] if hasattr(e, 'orig') else str(e)[:500],
                    "consequence": "409_response"
                }
            )
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "error": "Conflict",
                    "message": "Cette opération viole une contrainte d'intégrité",
                    "details": str(e.orig) if hasattr(e, 'orig') else str(e)
                }
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
            logger.warning(
                "[ERROR_MW] Erreur de permission — accès refusé",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": "PermissionError",
                    "error": str(e)[:500],
                    "consequence": "403_response"
                }
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Forbidden",
                    "message": str(e) or "Vous n'avez pas les permissions nécessaires"
                }
            )

        except FileNotFoundError as e:
            # Erreurs de fichier non trouvé
            logger.warning(
                "[ERROR_MW] Ressource non trouvée (FileNotFoundError)",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": "FileNotFoundError",
                    "error": str(e)[:500],
                    "consequence": "404_response"
                }
            )
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": "Not Found",
                    "message": "Le fichier ou la ressource demandée n'existe pas"
                }
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
            # Erreur générique inattendue
            logger.exception(
                "[ERROR_MW] EXCEPTION NON GÉRÉE — erreur inattendue",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": type(e).__name__,
                    "error": str(e)[:500],
                    "consequence": "500_response"
                }
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "message": "Une erreur inattendue s'est produite",
                    "type": type(e).__name__
                }
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
