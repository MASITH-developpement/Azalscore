"""
AZALS - Format erreur standardise backend
==========================================
Classe Pydantic pour reponses d'erreur unifiees.
Compatible avec StandardHttpError frontend (TypeScript).

Conformite : AZA-NF-003
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class StandardError(BaseModel):
    """
    Reponse erreur unifiee AZALSCORE.

    Compatible avec frontend StandardHttpError :
    - error_code -> error (backend utilise codes detailles)
    - message -> message (identique)
    - http_status -> code (clarification)

    Exemple reponse :
    {
        "error_code": "AUTH_INVALID_TOKEN",
        "message": "Token JWT invalide ou expire",
        "http_status": 401,
        "timestamp": "2024-01-01T10:30:00Z",
        "request_id": "req_abc123",
        "path": "/api/v1/protected/me"
    }
    """
    error_code: str = Field(
        ...,
        description="Code erreur business (ex: AUTH_INVALID_TOKEN)",
        max_length=100
    )
    message: str = Field(
        ...,
        description="Message utilisateur (francais)",
        max_length=1000
    )
    http_status: int = Field(
        ...,
        description="Code HTTP (400, 401, 403, 404, 500...)",
        ge=100,
        le=599
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp UTC de l'erreur"
    )
    request_id: str = Field(
        ...,
        description="ID requete pour tracabilite (correlation_id)",
        max_length=64
    )
    path: Optional[str] = Field(
        None,
        description="Chemin de la requete ayant echoue",
        max_length=500
    )
    details: Optional[dict] = Field(
        None,
        description="Details additionnels (validation errors, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "AUTH_INVALID_TOKEN",
                "message": "Token JWT invalide ou expire",
                "http_status": 401,
                "timestamp": "2024-01-01T10:30:00Z",
                "request_id": "req_abc123",
                "path": "/api/v1/protected/me"
            }
        }


class ErrorCode:
    """
    Codes standardises AZALSCORE.
    Utilises dans StandardError.error_code.

    Convention de nommage :
    - Prefixe = domaine (AUTH, TENANT, VALIDATION, etc.)
    - Suffixe = action/raison (INVALID, DENIED, NOT_FOUND, etc.)
    """
    # =========================================================================
    # AUTHENTICATION (401)
    # =========================================================================
    AUTH_INVALID_TOKEN = "AUTH_INVALID_TOKEN"
    AUTH_EXPIRED_TOKEN = "AUTH_EXPIRED_TOKEN"
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_MFA_REQUIRED = "AUTH_MFA_REQUIRED"
    AUTH_TOKEN_REVOKED = "AUTH_TOKEN_REVOKED"

    # =========================================================================
    # AUTHORIZATION (403)
    # =========================================================================
    TENANT_ACCESS_DENIED = "TENANT_ACCESS_DENIED"
    TENANT_NOT_FOUND = "TENANT_NOT_FOUND"
    TENANT_MISMATCH = "TENANT_MISMATCH"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    CAPABILITY_DENIED = "CAPABILITY_DENIED"

    # =========================================================================
    # CSRF (403)
    # =========================================================================
    CSRF_TOKEN_MISSING = "CSRF_TOKEN_MISSING"
    CSRF_TOKEN_INVALID = "CSRF_TOKEN_INVALID"

    # =========================================================================
    # VALIDATION (400, 422)
    # =========================================================================
    VALIDATION_ERROR = "VALIDATION_ERROR"
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    INVALID_INPUT = "INVALID_INPUT"

    # =========================================================================
    # RESOURCES (404)
    # =========================================================================
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    ENDPOINT_NOT_FOUND = "ENDPOINT_NOT_FOUND"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"

    # =========================================================================
    # CONFLICT (409)
    # =========================================================================
    INTEGRITY_ERROR = "INTEGRITY_ERROR"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"

    # =========================================================================
    # RATE LIMITING (429)
    # =========================================================================
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # =========================================================================
    # SERVER ERRORS (500, 503, 504)
    # =========================================================================
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    DATABASE_UNAVAILABLE = "DATABASE_UNAVAILABLE"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"


def create_standard_error(
    error_code: str,
    message: str,
    http_status: int,
    request_id: str,
    path: Optional[str] = None,
    details: Optional[dict] = None
) -> StandardError:
    """
    Factory pour creer une StandardError.

    Usage dans les middlewares et exception handlers :

        from app.core.errors import create_standard_error, ErrorCode

        error = create_standard_error(
            error_code=ErrorCode.VALIDATION_ERROR,
            message="Le champ 'email' est invalide",
            http_status=400,
            request_id=correlation_id,
            path="/api/v1/users",
            details={"field": "email", "reason": "format_invalid"}
        )

        return JSONResponse(
            status_code=error.http_status,
            content=error.model_dump()
        )

    Args:
        error_code: Code erreur (utiliser ErrorCode.*)
        message: Message utilisateur en francais
        http_status: Code HTTP (400, 401, 403, 404, 500, etc.)
        request_id: ID de correlation pour tracabilite
        path: Chemin de la requete (optionnel)
        details: Details additionnels (optionnel)

    Returns:
        Instance StandardError prete a etre serialisee
    """
    return StandardError(
        error_code=error_code,
        message=message,
        http_status=http_status,
        request_id=request_id,
        path=path,
        details=details
    )


# Mapping HTTP status -> ErrorCode par defaut
HTTP_STATUS_TO_ERROR_CODE = {
    400: ErrorCode.VALIDATION_ERROR,
    401: ErrorCode.AUTH_INVALID_TOKEN,
    403: ErrorCode.PERMISSION_DENIED,
    404: ErrorCode.RESOURCE_NOT_FOUND,
    409: ErrorCode.INTEGRITY_ERROR,
    422: ErrorCode.VALIDATION_ERROR,
    429: ErrorCode.RATE_LIMIT_EXCEEDED,
    500: ErrorCode.INTERNAL_SERVER_ERROR,
    501: ErrorCode.NOT_IMPLEMENTED,
    503: ErrorCode.DATABASE_UNAVAILABLE,
    504: ErrorCode.TIMEOUT_ERROR,
}


def get_error_code_for_status(http_status: int) -> str:
    """
    Retourne le ErrorCode par defaut pour un status HTTP.

    Args:
        http_status: Code HTTP (400, 401, etc.)

    Returns:
        ErrorCode correspondant ou INTERNAL_SERVER_ERROR par defaut
    """
    return HTTP_STATUS_TO_ERROR_CODE.get(http_status, ErrorCode.INTERNAL_SERVER_ERROR)
