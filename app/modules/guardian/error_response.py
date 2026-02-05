"""
AZALS MODULE GUARDIAN - Safe Error Response
=============================================

Fonctions utilitaires pour la gestion SAFE des erreurs HTTP.

GARANTIES:
- Ne dépend JAMAIS d'un fichier HTML pour répondre
- Renvoie TOUJOURS une réponse HTTP valide (JSON en fallback)
- Ne lève jamais d'exception non gérée

Ce module est séparé du middleware principal pour éviter les
imports circulaires et permettre son utilisation dans tous
les middlewares de l'application.
"""

import enum
from pathlib import Path

from fastapi.responses import FileResponse
from starlette.responses import JSONResponse, Response

from app.core.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# ENUMS (copies locales pour éviter les imports circulaires)
# ============================================================================

class ErrorType(str, enum.Enum):
    """Type d'erreur détectée."""
    EXCEPTION = "EXCEPTION"
    VALIDATION = "VALIDATION"
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    CONFIGURATION = "CONFIGURATION"
    DATA_INTEGRITY = "DATA_INTEGRITY"
    BUSINESS_LOGIC = "BUSINESS_LOGIC"
    DEPENDENCY = "DEPENDENCY"
    MEMORY = "MEMORY"
    STORAGE = "STORAGE"
    UNKNOWN = "UNKNOWN"


class ErrorSeverity(str, enum.Enum):
    """Niveau de gravité des erreurs."""
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    WARNING = "WARNING"
    INFO = "INFO"


# ============================================================================
# FONCTION UTILITAIRE SAFE DE RÉPONSE D'ERREUR
# ============================================================================

def build_error_response(
    status_code: int,
    error_type: ErrorType,
    message: str,
    html_path: str | None = None,
    extra_data: dict | None = None
) -> Response:
    """
    Construit une réponse d'erreur HTTP de manière SAFE.

    GARANTIES:
    - Ne lève JAMAIS d'exception
    - Renvoie TOUJOURS une réponse HTTP valide
    - Tente HTML si fichier existe, sinon JSON
    - JSON minimal: error_type, http_status, message

    Args:
        status_code: Code HTTP (401, 403, 404, 500, etc.)
        error_type: Type d'erreur métier (ErrorType enum)
        message: Message d'erreur lisible
        html_path: Chemin optionnel vers un fichier HTML d'erreur
        extra_data: Données supplémentaires à inclure dans la réponse JSON

    Returns:
        Response: FileResponse (HTML) ou JSONResponse (fallback)

    Example:
        >>> error_type = ErrorType.AUTHENTICATION
        >>> return build_error_response(
        ...     status_code=401,
        ...     error_type=error_type,
        ...     message="Authentification requise",
        ...     html_path="frontend/errors/401.html"
        ... )
    """
    try:
        # Tentative de réponse HTML si le fichier existe
        if html_path:
            html_file = Path(html_path)
            if html_file.exists() and html_file.is_file():
                try:
                    return FileResponse(
                        path=str(html_file),
                        status_code=status_code,
                        media_type="text/html"
                    )
                except Exception as e:
                    # Échec silencieux, on continue vers JSON
                    logger.debug("Impossible de servir le fichier HTML %s: %s", html_path, e)
    except Exception as e:
        # Sécurité: si même la vérification du path échoue, on continue
        logger.debug("Erreur lors de la vérification du fichier HTML: %s", e)

    # Réponse JSON (fallback toujours disponible)
    json_content = {
        "error_type": error_type.value if isinstance(error_type, ErrorType) else str(error_type),
        "http_status": status_code,
        "message": message,
        "detail": message,  # Compatibilité FastAPI HTTPException
    }

    # Ajouter les données supplémentaires si fournies
    if extra_data and isinstance(extra_data, dict):
        json_content.update(extra_data)

    return JSONResponse(
        status_code=status_code,
        content=json_content
    )


def get_error_type_for_status(status_code: int) -> ErrorType:
    """
    Détermine le type d'erreur selon le code HTTP.

    Mapping standardisé utilisé dans toute l'application.
    Ce mapping NE DOIT PAS être modifié sans revue approfondie.

    Args:
        status_code: Code HTTP

    Returns:
        ErrorType correspondant
    """
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


def get_error_severity_for_status(status_code: int) -> ErrorSeverity:
    """
    Détermine la sévérité selon le code HTTP.

    Args:
        status_code: Code HTTP

    Returns:
        ErrorSeverity correspondante
    """
    if status_code >= 500:
        return ErrorSeverity.CRITICAL
    elif status_code == 429:  # Rate limit
        return ErrorSeverity.WARNING
    elif status_code in [401, 403]:  # Auth errors
        return ErrorSeverity.MAJOR
    elif status_code >= 400:
        return ErrorSeverity.MINOR
    return ErrorSeverity.INFO


# Messages d'erreur par défaut selon le code HTTP
DEFAULT_ERROR_MESSAGES = {
    400: "Requête invalide",
    401: "Authentification requise",
    403: "Accès refusé",
    404: "Ressource non trouvée",
    408: "Délai d'attente dépassé",
    409: "Conflit de données",
    422: "Données non valides",
    429: "Trop de requêtes - veuillez réessayer plus tard",
    500: "Erreur interne du serveur",
    502: "Service temporairement indisponible",
    503: "Service en maintenance",
    504: "Délai de réponse dépassé",
}


def build_safe_error_response(
    status_code: int,
    message: str | None = None,
    html_path: str | None = None,
    extra_data: dict | None = None
) -> Response:
    """
    Version simplifiée de build_error_response qui détermine automatiquement
    le type d'erreur et utilise un message par défaut si non fourni.

    C'est la fonction recommandée pour les cas simples.

    Args:
        status_code: Code HTTP
        message: Message optionnel (utilise le message par défaut si None)
        html_path: Chemin optionnel vers un fichier HTML d'erreur
        extra_data: Données supplémentaires

    Returns:
        Response HTTP (HTML ou JSON)
    """
    error_type = get_error_type_for_status(status_code)
    final_message = message or DEFAULT_ERROR_MESSAGES.get(status_code, "Erreur inattendue")

    return build_error_response(
        status_code=status_code,
        error_type=error_type,
        message=final_message,
        html_path=html_path,
        extra_data=extra_data
    )
