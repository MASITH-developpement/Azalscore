"""
Exceptions métier - Module Integrations (GAP-086)
"""


class IntegrationError(Exception):
    """Exception de base du module Integrations."""
    pass


class ConnectionNotFoundError(IntegrationError):
    """Connexion non trouvée."""
    pass


class ConnectionDuplicateError(IntegrationError):
    """Code connexion déjà existant."""
    pass


class ConnectionFailedError(IntegrationError):
    """Échec de connexion."""
    pass


class ConnectionExpiredError(IntegrationError):
    """Token de connexion expiré."""
    pass


class ConnectionInactiveError(IntegrationError):
    """Connexion inactive."""
    pass


class AuthenticationError(IntegrationError):
    """Erreur d'authentification."""
    pass


class OAuthError(IntegrationError):
    """Erreur OAuth2."""
    pass


class EntityMappingNotFoundError(IntegrationError):
    """Mapping d'entité non trouvé."""
    pass


class EntityMappingDuplicateError(IntegrationError):
    """Code mapping déjà existant."""
    pass


class EntityMappingValidationError(IntegrationError):
    """Erreur de validation mapping."""
    pass


class SyncJobNotFoundError(IntegrationError):
    """Job de synchronisation non trouvé."""
    pass


class SyncJobRunningError(IntegrationError):
    """Job déjà en cours d'exécution."""
    pass


class SyncError(IntegrationError):
    """Erreur de synchronisation."""
    pass


class ConflictNotFoundError(IntegrationError):
    """Conflit non trouvé."""
    pass


class ConflictResolutionError(IntegrationError):
    """Erreur de résolution de conflit."""
    pass


class WebhookNotFoundError(IntegrationError):
    """Webhook non trouvé."""
    pass


class WebhookValidationError(IntegrationError):
    """Erreur de validation webhook."""
    pass


class RateLimitError(IntegrationError):
    """Limite de requêtes dépassée."""
    pass


class TransformationError(IntegrationError):
    """Erreur de transformation de données."""
    pass
