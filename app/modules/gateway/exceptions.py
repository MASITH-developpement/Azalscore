"""
AZALS MODULE GATEWAY - Exceptions
==================================

Exceptions specifiques au module Gateway.
"""

from typing import Optional
from datetime import datetime


class GatewayException(Exception):
    """Exception de base pour le module Gateway."""

    def __init__(
        self,
        message: str,
        error_code: str = "GATEWAY_ERROR",
        details: Optional[dict] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


# ============================================================================
# AUTHENTIFICATION
# ============================================================================

class AuthenticationError(GatewayException):
    """Erreur d'authentification."""

    def __init__(self, message: str = "Authentication failed", details: Optional[dict] = None):
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class InvalidApiKeyError(AuthenticationError):
    """Cle API invalide."""

    def __init__(self, message: str = "Invalid API key", details: Optional[dict] = None):
        super().__init__(message, details)
        self.error_code = "INVALID_API_KEY"


class ExpiredApiKeyError(AuthenticationError):
    """Cle API expiree."""

    def __init__(self, message: str = "API key has expired", details: Optional[dict] = None):
        super().__init__(message, details)
        self.error_code = "EXPIRED_API_KEY"


class RevokedApiKeyError(AuthenticationError):
    """Cle API revoquee."""

    def __init__(self, message: str = "API key has been revoked", details: Optional[dict] = None):
        super().__init__(message, details)
        self.error_code = "REVOKED_API_KEY"


class SuspendedApiKeyError(AuthenticationError):
    """Cle API suspendue."""

    def __init__(self, message: str = "API key is suspended", details: Optional[dict] = None):
        super().__init__(message, details)
        self.error_code = "SUSPENDED_API_KEY"


class InvalidOAuthTokenError(AuthenticationError):
    """Token OAuth invalide."""

    def __init__(self, message: str = "Invalid OAuth token", details: Optional[dict] = None):
        super().__init__(message, details)
        self.error_code = "INVALID_OAUTH_TOKEN"


class ExpiredOAuthTokenError(AuthenticationError):
    """Token OAuth expire."""

    def __init__(self, message: str = "OAuth token has expired", details: Optional[dict] = None):
        super().__init__(message, details)
        self.error_code = "EXPIRED_OAUTH_TOKEN"


# ============================================================================
# AUTORISATION
# ============================================================================

class AuthorizationError(GatewayException):
    """Erreur d'autorisation."""

    def __init__(self, message: str = "Access denied", details: Optional[dict] = None):
        super().__init__(message, "AUTHORIZATION_ERROR", details)


class InsufficientScopeError(AuthorizationError):
    """Scope insuffisant."""

    def __init__(
        self,
        required_scope: str,
        message: str = "Insufficient scope",
        details: Optional[dict] = None
    ):
        details = details or {}
        details["required_scope"] = required_scope
        super().__init__(message, details)
        self.error_code = "INSUFFICIENT_SCOPE"


class IpNotAllowedError(AuthorizationError):
    """IP non autorisee."""

    def __init__(self, ip_address: str, details: Optional[dict] = None):
        details = details or {}
        details["ip_address"] = ip_address
        super().__init__(f"IP address {ip_address} is not allowed", details)
        self.error_code = "IP_NOT_ALLOWED"


class OriginNotAllowedError(AuthorizationError):
    """Origine non autorisee."""

    def __init__(self, origin: str, details: Optional[dict] = None):
        details = details or {}
        details["origin"] = origin
        super().__init__(f"Origin {origin} is not allowed", details)
        self.error_code = "ORIGIN_NOT_ALLOWED"


class EndpointNotAllowedError(AuthorizationError):
    """Endpoint non autorise pour cette cle."""

    def __init__(self, endpoint: str, details: Optional[dict] = None):
        details = details or {}
        details["endpoint"] = endpoint
        super().__init__(f"Access to endpoint {endpoint} is not allowed", details)
        self.error_code = "ENDPOINT_NOT_ALLOWED"


# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimitError(GatewayException):
    """Erreur de rate limiting."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
        remaining: Optional[int] = None,
        reset: Optional[datetime] = None,
        details: Optional[dict] = None
    ):
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        if limit:
            details["rate_limit"] = limit
        if remaining is not None:
            details["rate_limit_remaining"] = remaining
        if reset:
            details["rate_limit_reset"] = reset.isoformat()

        super().__init__(message, "RATE_LIMIT_EXCEEDED", details)
        self.retry_after = retry_after
        self.limit = limit
        self.remaining = remaining
        self.reset = reset


class QuotaExceededError(RateLimitError):
    """Quota depasse."""

    def __init__(
        self,
        period: str,
        limit: int,
        current: int,
        details: Optional[dict] = None
    ):
        details = details or {}
        details["period"] = period
        details["current_usage"] = current

        super().__init__(
            message=f"Quota exceeded for {period}: {current}/{limit}",
            limit=limit,
            remaining=0,
            details=details
        )
        self.error_code = "QUOTA_EXCEEDED"


# ============================================================================
# CIRCUIT BREAKER
# ============================================================================

class CircuitBreakerError(GatewayException):
    """Erreur de circuit breaker."""

    def __init__(
        self,
        endpoint_id: str,
        message: str = "Service temporarily unavailable",
        details: Optional[dict] = None
    ):
        details = details or {}
        details["endpoint_id"] = endpoint_id
        super().__init__(message, "CIRCUIT_OPEN", details)


class CircuitOpenError(CircuitBreakerError):
    """Circuit ouvert."""

    def __init__(
        self,
        endpoint_id: str,
        retry_after: Optional[int] = None,
        details: Optional[dict] = None
    ):
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(
            endpoint_id,
            "Service temporarily unavailable - circuit breaker open",
            details
        )


# ============================================================================
# WEBHOOK
# ============================================================================

class WebhookError(GatewayException):
    """Erreur de webhook."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "WEBHOOK_ERROR", details)


class WebhookDeliveryError(WebhookError):
    """Erreur de livraison webhook."""

    def __init__(
        self,
        webhook_id: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        details: Optional[dict] = None
    ):
        details = details or {}
        details["webhook_id"] = webhook_id
        if status_code:
            details["status_code"] = status_code
        if response_body:
            details["response_body"] = response_body[:500]  # Truncate
        super().__init__("Webhook delivery failed", details)
        self.error_code = "WEBHOOK_DELIVERY_FAILED"


class WebhookTimeoutError(WebhookError):
    """Timeout de webhook."""

    def __init__(self, webhook_id: str, timeout: int, details: Optional[dict] = None):
        details = details or {}
        details["webhook_id"] = webhook_id
        details["timeout_seconds"] = timeout
        super().__init__(f"Webhook request timed out after {timeout}s", details)
        self.error_code = "WEBHOOK_TIMEOUT"


class WebhookSignatureError(WebhookError):
    """Erreur de signature webhook."""

    def __init__(self, message: str = "Invalid webhook signature", details: Optional[dict] = None):
        super().__init__(message, details)
        self.error_code = "INVALID_WEBHOOK_SIGNATURE"


# ============================================================================
# TRANSFORMATION
# ============================================================================

class TransformationError(GatewayException):
    """Erreur de transformation."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "TRANSFORMATION_ERROR", details)


class InvalidTransformationError(TransformationError):
    """Transformation invalide."""

    def __init__(
        self,
        transform_id: str,
        error: str,
        details: Optional[dict] = None
    ):
        details = details or {}
        details["transform_id"] = transform_id
        details["error"] = error
        super().__init__(f"Transformation failed: {error}", details)
        self.error_code = "INVALID_TRANSFORMATION"


# ============================================================================
# VALIDATION
# ============================================================================

class ValidationError(GatewayException):
    """Erreur de validation."""

    def __init__(self, message: str, errors: Optional[list] = None, details: Optional[dict] = None):
        details = details or {}
        if errors:
            details["validation_errors"] = errors
        super().__init__(message, "VALIDATION_ERROR", details)


class RequestSizeLimitError(ValidationError):
    """Taille de requete depassee."""

    def __init__(
        self,
        size: int,
        max_size: int,
        details: Optional[dict] = None
    ):
        details = details or {}
        details["request_size"] = size
        details["max_size"] = max_size
        super().__init__(
            f"Request body too large: {size} bytes (max: {max_size})",
            details=details
        )
        self.error_code = "REQUEST_TOO_LARGE"


class InvalidContentTypeError(ValidationError):
    """Content-Type invalide."""

    def __init__(
        self,
        received: str,
        expected: str,
        details: Optional[dict] = None
    ):
        details = details or {}
        details["received_content_type"] = received
        details["expected_content_type"] = expected
        super().__init__(
            f"Invalid content type: {received}, expected {expected}",
            details=details
        )
        self.error_code = "INVALID_CONTENT_TYPE"


class SchemaValidationError(ValidationError):
    """Erreur de validation de schema."""

    def __init__(self, errors: list, details: Optional[dict] = None):
        super().__init__("Request body does not match schema", errors, details)
        self.error_code = "SCHEMA_VALIDATION_ERROR"


# ============================================================================
# RESSOURCES
# ============================================================================

class ResourceNotFoundError(GatewayException):
    """Ressource non trouvee."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        details: Optional[dict] = None
    ):
        details = details or {}
        details["resource_type"] = resource_type
        details["resource_id"] = resource_id
        super().__init__(
            f"{resource_type} not found: {resource_id}",
            "NOT_FOUND",
            details
        )


class ResourceConflictError(GatewayException):
    """Conflit de ressource."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "CONFLICT", details)


class DuplicateResourceError(ResourceConflictError):
    """Ressource dupliquee."""

    def __init__(
        self,
        resource_type: str,
        field: str,
        value: str,
        details: Optional[dict] = None
    ):
        details = details or {}
        details["resource_type"] = resource_type
        details["field"] = field
        details["value"] = value
        super().__init__(f"{resource_type} with {field}={value} already exists", details)
        self.error_code = "DUPLICATE"


# ============================================================================
# BACKEND / PROXY
# ============================================================================

class BackendError(GatewayException):
    """Erreur du backend."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "BACKEND_ERROR", details)


class BackendTimeoutError(BackendError):
    """Timeout du backend."""

    def __init__(
        self,
        url: str,
        timeout: int,
        details: Optional[dict] = None
    ):
        details = details or {}
        details["url"] = url
        details["timeout_seconds"] = timeout
        super().__init__(f"Backend request timed out after {timeout}s", details)
        self.error_code = "BACKEND_TIMEOUT"


class BackendConnectionError(BackendError):
    """Erreur de connexion au backend."""

    def __init__(self, url: str, error: str, details: Optional[dict] = None):
        details = details or {}
        details["url"] = url
        details["error"] = error
        super().__init__(f"Cannot connect to backend: {error}", details)
        self.error_code = "BACKEND_CONNECTION_ERROR"


class BackendResponseError(BackendError):
    """Erreur de reponse du backend."""

    def __init__(
        self,
        status_code: int,
        url: str,
        details: Optional[dict] = None
    ):
        details = details or {}
        details["url"] = url
        details["status_code"] = status_code
        super().__init__(f"Backend returned error: {status_code}", details)
        self.error_code = "BACKEND_RESPONSE_ERROR"
