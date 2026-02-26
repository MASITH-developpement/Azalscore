"""
AZALS MODULE GAP-086 - Exceptions Integration
==============================================

Exceptions metier specifiques au module Integration.
"""
from __future__ import annotations



class IntegrationError(Exception):
    """Exception de base du module Integration."""

    def __init__(self, message: str, code: str | None = None, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.code = code or "INTEGRATION_ERROR"
        self.details = details or {}


# ============================================================================
# CONNECTOR ERRORS
# ============================================================================

class ConnectorNotFoundError(IntegrationError):
    """Connecteur non trouve."""

    def __init__(self, connector_type: str):
        super().__init__(
            f"Connecteur non trouve: {connector_type}",
            code="CONNECTOR_NOT_FOUND",
            details={"connector_type": connector_type}
        )


class ConnectorNotSupportedError(IntegrationError):
    """Connecteur non supporte."""

    def __init__(self, connector_type: str, feature: str = None):
        msg = f"Connecteur non supporte: {connector_type}"
        if feature:
            msg += f" (fonctionnalite: {feature})"
        super().__init__(
            msg,
            code="CONNECTOR_NOT_SUPPORTED",
            details={"connector_type": connector_type, "feature": feature}
        )


class ConnectorConfigurationError(IntegrationError):
    """Erreur de configuration du connecteur."""

    def __init__(self, message: str, missing_fields: list[str] = None):
        super().__init__(
            message,
            code="CONNECTOR_CONFIGURATION_ERROR",
            details={"missing_fields": missing_fields or []}
        )


# ============================================================================
# CONNECTION ERRORS
# ============================================================================

class ConnectionNotFoundError(IntegrationError):
    """Connexion non trouvee."""

    def __init__(self, connection_id: str):
        super().__init__(
            f"Connexion non trouvee: {connection_id}",
            code="CONNECTION_NOT_FOUND",
            details={"connection_id": connection_id}
        )


class ConnectionDuplicateError(IntegrationError):
    """Code connexion deja existant."""

    def __init__(self, code: str):
        super().__init__(
            f"Code connexion deja existant: {code}",
            code="CONNECTION_DUPLICATE",
            details={"code": code}
        )


class ConnectionFailedError(IntegrationError):
    """Echec de connexion."""

    def __init__(self, message: str, connection_id: str = None):
        super().__init__(
            message,
            code="CONNECTION_FAILED",
            details={"connection_id": connection_id}
        )


class ConnectionExpiredError(IntegrationError):
    """Token de connexion expire."""

    def __init__(self, connection_id: str):
        super().__init__(
            f"Token expire pour la connexion: {connection_id}",
            code="CONNECTION_EXPIRED",
            details={"connection_id": connection_id}
        )


class ConnectionInactiveError(IntegrationError):
    """Connexion inactive."""

    def __init__(self, connection_id: str):
        super().__init__(
            f"Connexion inactive: {connection_id}",
            code="CONNECTION_INACTIVE",
            details={"connection_id": connection_id}
        )


class ConnectionRateLimitedError(IntegrationError):
    """Rate limit atteint."""

    def __init__(self, connection_id: str, reset_at: str = None):
        super().__init__(
            f"Rate limit atteint pour la connexion: {connection_id}",
            code="CONNECTION_RATE_LIMITED",
            details={"connection_id": connection_id, "reset_at": reset_at}
        )


# ============================================================================
# AUTHENTICATION ERRORS
# ============================================================================

class AuthenticationError(IntegrationError):
    """Erreur d'authentification."""

    def __init__(self, message: str, connection_id: str = None):
        super().__init__(
            message,
            code="AUTHENTICATION_ERROR",
            details={"connection_id": connection_id}
        )


class OAuthError(IntegrationError):
    """Erreur OAuth2."""

    def __init__(self, message: str, oauth_error: str = None, oauth_description: str = None):
        super().__init__(
            message,
            code="OAUTH_ERROR",
            details={"oauth_error": oauth_error, "oauth_description": oauth_description}
        )


class OAuthStateError(IntegrationError):
    """Erreur de state OAuth (CSRF)."""

    def __init__(self):
        super().__init__(
            "State OAuth invalide ou expire",
            code="OAUTH_STATE_ERROR"
        )


class OAuthTokenRefreshError(IntegrationError):
    """Erreur de rafraichissement du token."""

    def __init__(self, connection_id: str, reason: str = None):
        super().__init__(
            f"Impossible de rafraichir le token: {reason or 'erreur inconnue'}",
            code="OAUTH_TOKEN_REFRESH_ERROR",
            details={"connection_id": connection_id, "reason": reason}
        )


# ============================================================================
# MAPPING ERRORS
# ============================================================================

class MappingNotFoundError(IntegrationError):
    """Mapping non trouve."""

    def __init__(self, mapping_id: str):
        super().__init__(
            f"Mapping non trouve: {mapping_id}",
            code="MAPPING_NOT_FOUND",
            details={"mapping_id": mapping_id}
        )


class MappingDuplicateError(IntegrationError):
    """Code mapping deja existant."""

    def __init__(self, code: str):
        super().__init__(
            f"Code mapping deja existant: {code}",
            code="MAPPING_DUPLICATE",
            details={"code": code}
        )


class MappingValidationError(IntegrationError):
    """Erreur de validation du mapping."""

    def __init__(self, message: str, field: str = None):
        super().__init__(
            message,
            code="MAPPING_VALIDATION_ERROR",
            details={"field": field}
        )


class MappingFieldError(IntegrationError):
    """Erreur sur un champ du mapping."""

    def __init__(self, source_field: str, target_field: str, reason: str):
        super().__init__(
            f"Erreur de mapping: {source_field} -> {target_field}: {reason}",
            code="MAPPING_FIELD_ERROR",
            details={"source_field": source_field, "target_field": target_field, "reason": reason}
        )


# ============================================================================
# SYNC CONFIGURATION ERRORS
# ============================================================================

class SyncConfigNotFoundError(IntegrationError):
    """Configuration de sync non trouvee."""

    def __init__(self, config_id: str):
        super().__init__(
            f"Configuration de synchronisation non trouvee: {config_id}",
            code="SYNC_CONFIG_NOT_FOUND",
            details={"config_id": config_id}
        )


class SyncConfigDuplicateError(IntegrationError):
    """Code configuration deja existant."""

    def __init__(self, code: str):
        super().__init__(
            f"Code configuration deja existant: {code}",
            code="SYNC_CONFIG_DUPLICATE",
            details={"code": code}
        )


class SyncConfigInvalidCronError(IntegrationError):
    """Expression cron invalide."""

    def __init__(self, cron_expression: str):
        super().__init__(
            f"Expression cron invalide: {cron_expression}",
            code="SYNC_CONFIG_INVALID_CRON",
            details={"cron_expression": cron_expression}
        )


# ============================================================================
# SYNC EXECUTION ERRORS
# ============================================================================

class SyncExecutionNotFoundError(IntegrationError):
    """Execution de sync non trouvee."""

    def __init__(self, execution_id: str):
        super().__init__(
            f"Execution de synchronisation non trouvee: {execution_id}",
            code="SYNC_EXECUTION_NOT_FOUND",
            details={"execution_id": execution_id}
        )


class SyncExecutionRunningError(IntegrationError):
    """Une execution est deja en cours."""

    def __init__(self, connection_id: str = None, config_id: str = None):
        super().__init__(
            "Une synchronisation est deja en cours",
            code="SYNC_EXECUTION_RUNNING",
            details={"connection_id": connection_id, "config_id": config_id}
        )


class SyncExecutionFailedError(IntegrationError):
    """Echec de l'execution."""

    def __init__(self, execution_id: str, reason: str):
        super().__init__(
            f"Echec de la synchronisation: {reason}",
            code="SYNC_EXECUTION_FAILED",
            details={"execution_id": execution_id, "reason": reason}
        )


class SyncExecutionTimeoutError(IntegrationError):
    """Timeout de l'execution."""

    def __init__(self, execution_id: str, timeout_seconds: int):
        super().__init__(
            f"Timeout de la synchronisation apres {timeout_seconds}s",
            code="SYNC_EXECUTION_TIMEOUT",
            details={"execution_id": execution_id, "timeout_seconds": timeout_seconds}
        )


class SyncExecutionCancelledError(IntegrationError):
    """Execution annulee."""

    def __init__(self, execution_id: str, reason: str = None):
        super().__init__(
            f"Synchronisation annulee{': ' + reason if reason else ''}",
            code="SYNC_EXECUTION_CANCELLED",
            details={"execution_id": execution_id, "reason": reason}
        )


# ============================================================================
# CONFLICT ERRORS
# ============================================================================

class ConflictNotFoundError(IntegrationError):
    """Conflit non trouve."""

    def __init__(self, conflict_id: str):
        super().__init__(
            f"Conflit non trouve: {conflict_id}",
            code="CONFLICT_NOT_FOUND",
            details={"conflict_id": conflict_id}
        )


class ConflictAlreadyResolvedError(IntegrationError):
    """Conflit deja resolu."""

    def __init__(self, conflict_id: str):
        super().__init__(
            f"Conflit deja resolu: {conflict_id}",
            code="CONFLICT_ALREADY_RESOLVED",
            details={"conflict_id": conflict_id}
        )


class ConflictResolutionError(IntegrationError):
    """Erreur de resolution de conflit."""

    def __init__(self, conflict_id: str, reason: str):
        super().__init__(
            f"Impossible de resoudre le conflit: {reason}",
            code="CONFLICT_RESOLUTION_ERROR",
            details={"conflict_id": conflict_id, "reason": reason}
        )


# ============================================================================
# WEBHOOK ERRORS
# ============================================================================

class WebhookNotFoundError(IntegrationError):
    """Webhook non trouve."""

    def __init__(self, webhook_id: str = None, endpoint_path: str = None):
        identifier = webhook_id or endpoint_path
        super().__init__(
            f"Webhook non trouve: {identifier}",
            code="WEBHOOK_NOT_FOUND",
            details={"webhook_id": webhook_id, "endpoint_path": endpoint_path}
        )


class WebhookDuplicateError(IntegrationError):
    """Code ou path webhook deja existant."""

    def __init__(self, code: str = None, endpoint_path: str = None):
        identifier = code or endpoint_path
        super().__init__(
            f"Webhook deja existant: {identifier}",
            code="WEBHOOK_DUPLICATE",
            details={"code": code, "endpoint_path": endpoint_path}
        )


class WebhookValidationError(IntegrationError):
    """Erreur de validation du webhook."""

    def __init__(self, message: str, signature_valid: bool = None):
        super().__init__(
            message,
            code="WEBHOOK_VALIDATION_ERROR",
            details={"signature_valid": signature_valid}
        )


class WebhookDeliveryError(IntegrationError):
    """Erreur de livraison du webhook sortant."""

    def __init__(self, webhook_id: str, target_url: str, status_code: int = None, error: str = None):
        super().__init__(
            f"Echec de livraison du webhook: {error or f'HTTP {status_code}'}",
            code="WEBHOOK_DELIVERY_ERROR",
            details={
                "webhook_id": webhook_id,
                "target_url": target_url,
                "status_code": status_code,
                "error": error
            }
        )


class WebhookTimeoutError(IntegrationError):
    """Timeout du webhook."""

    def __init__(self, webhook_id: str, timeout_seconds: int):
        super().__init__(
            f"Timeout du webhook apres {timeout_seconds}s",
            code="WEBHOOK_TIMEOUT_ERROR",
            details={"webhook_id": webhook_id, "timeout_seconds": timeout_seconds}
        )


# ============================================================================
# TRANSFORMATION ERRORS
# ============================================================================

class TransformationRuleNotFoundError(IntegrationError):
    """Regle de transformation non trouvee."""

    def __init__(self, rule_id: str = None, rule_code: str = None):
        identifier = rule_id or rule_code
        super().__init__(
            f"Regle de transformation non trouvee: {identifier}",
            code="TRANSFORMATION_RULE_NOT_FOUND",
            details={"rule_id": rule_id, "rule_code": rule_code}
        )


class TransformationError(IntegrationError):
    """Erreur de transformation de donnees."""

    def __init__(self, message: str, field: str = None, value: str = None):
        super().__init__(
            message,
            code="TRANSFORMATION_ERROR",
            details={"field": field, "value": value}
        )


class TransformationScriptError(IntegrationError):
    """Erreur dans un script de transformation."""

    def __init__(self, message: str, script_type: str = None, line: int = None):
        super().__init__(
            message,
            code="TRANSFORMATION_SCRIPT_ERROR",
            details={"script_type": script_type, "line": line}
        )


# ============================================================================
# API ERRORS
# ============================================================================

class ExternalAPIError(IntegrationError):
    """Erreur de l'API externe."""

    def __init__(
        self,
        message: str,
        connector_type: str = None,
        status_code: int = None,
        response_body: str = None
    ):
        super().__init__(
            message,
            code="EXTERNAL_API_ERROR",
            details={
                "connector_type": connector_type,
                "status_code": status_code,
                "response_body": response_body
            }
        )


class ExternalAPITimeoutError(IntegrationError):
    """Timeout de l'API externe."""

    def __init__(self, connector_type: str, timeout_seconds: int):
        super().__init__(
            f"Timeout de l'API {connector_type} apres {timeout_seconds}s",
            code="EXTERNAL_API_TIMEOUT",
            details={"connector_type": connector_type, "timeout_seconds": timeout_seconds}
        )


class ExternalAPIRateLimitError(IntegrationError):
    """Rate limit de l'API externe."""

    def __init__(self, connector_type: str, retry_after: int = None):
        super().__init__(
            f"Rate limit atteint pour l'API {connector_type}",
            code="EXTERNAL_API_RATE_LIMIT",
            details={"connector_type": connector_type, "retry_after": retry_after}
        )


# ============================================================================
# DATA ERRORS
# ============================================================================

class DataValidationError(IntegrationError):
    """Erreur de validation des donnees."""

    def __init__(self, message: str, field: str = None, value: str = None, expected: str = None):
        super().__init__(
            message,
            code="DATA_VALIDATION_ERROR",
            details={"field": field, "value": value, "expected": expected}
        )


class DataDeduplicationError(IntegrationError):
    """Erreur de deduplication."""

    def __init__(self, entity_type: str, key_field: str, duplicate_count: int):
        super().__init__(
            f"Plusieurs enregistrements trouves pour la cle {key_field}",
            code="DATA_DEDUPLICATION_ERROR",
            details={
                "entity_type": entity_type,
                "key_field": key_field,
                "duplicate_count": duplicate_count
            }
        )
