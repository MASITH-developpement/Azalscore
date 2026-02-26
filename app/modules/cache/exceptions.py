"""
AZALS MODULE - Cache - Exceptions
=================================

Exceptions metier pour la gestion du cache.
"""


class CacheError(Exception):
    """Exception de base du module Cache."""
    pass


class CacheConfigNotFoundError(CacheError):
    """Configuration cache non trouvee."""
    pass


class CacheConfigAlreadyExistsError(CacheError):
    """Configuration cache deja existante pour ce tenant."""
    pass


class CacheRegionNotFoundError(CacheError):
    """Region cache non trouvee."""
    pass


class CacheRegionDuplicateError(CacheError):
    """Code de region cache deja existant."""
    pass


class CacheRegionInUseError(CacheError):
    """Region cache en cours d'utilisation."""
    pass


class CacheEntryNotFoundError(CacheError):
    """Entree cache non trouvee."""
    pass


class CacheKeyInvalidError(CacheError):
    """Cle de cache invalide."""
    pass


class CacheKeyTooLongError(CacheError):
    """Cle de cache trop longue."""
    pass


class CacheValueTooLargeError(CacheError):
    """Valeur trop grande pour le cache."""
    pass


class CacheSerializationError(CacheError):
    """Erreur de serialisation de la valeur."""
    pass


class CacheDeserializationError(CacheError):
    """Erreur de deserialisation de la valeur."""
    pass


class CacheConnectionError(CacheError):
    """Erreur de connexion au cache (Redis)."""
    pass


class CacheTimeoutError(CacheError):
    """Timeout lors d'une operation cache."""
    pass


class InvalidationError(CacheError):
    """Erreur lors de l'invalidation."""
    pass


class InvalidPatternError(CacheError):
    """Pattern d'invalidation invalide."""
    pass


class PreloadTaskNotFoundError(CacheError):
    """Tache de prechargement non trouvee."""
    pass


class PreloadTaskDuplicateError(CacheError):
    """Tache de prechargement deja existante."""
    pass


class PreloadExecutionError(CacheError):
    """Erreur lors de l'execution du prechargement."""
    pass


class PreloadLoaderNotFoundError(CacheError):
    """Loader de prechargement non trouve."""
    pass


class CacheAlertNotFoundError(CacheError):
    """Alerte cache non trouvee."""
    pass


class CacheAlertAlreadyResolvedError(CacheError):
    """Alerte deja resolue."""
    pass


class PurgeConfirmationRequiredError(CacheError):
    """Confirmation requise pour la purge."""
    pass


class CacheCapacityExceededError(CacheError):
    """Capacite du cache depassee."""
    pass


class CompressionError(CacheError):
    """Erreur de compression."""
    pass


class DecompressionError(CacheError):
    """Erreur de decompression."""
    pass


class CacheOperationNotAllowedError(CacheError):
    """Operation cache non autorisee."""
    pass


class CacheMaintenanceModeError(CacheError):
    """Cache en mode maintenance."""
    pass
