"""
Module Intégrations et Connecteurs - GAP-086

Gestion des intégrations tierces:
- Connecteurs OAuth2/API Key
- Synchronisation bidirectionnelle
- Mapping des données
- Logs de synchronisation
- Gestion des conflits
- Monitoring des connexions
- Webhooks entrants
"""

# Models SQLAlchemy
from .models import (
    Connection as ConnectionModel,
    EntityMapping as EntityMappingModel,
    SyncJob as SyncJobModel,
    SyncLog as SyncLogModel,
    Conflict as ConflictModel,
    Webhook as WebhookModel,
    ConnectorType,
    AuthType,
    ConnectionStatus,
    SyncStatus,
    SyncDirection,
    SyncFrequency,
    ConflictResolution,
    EntityType,
)

# Repositories
from .repository import (
    ConnectionRepository,
    EntityMappingRepository,
    SyncJobRepository,
    SyncLogRepository,
    ConflictRepository,
    WebhookRepository,
)

# Router
from .router import router

# Exceptions
from .exceptions import (
    IntegrationError,
    ConnectionNotFoundError,
    ConnectionDuplicateError,
    ConnectionInactiveError,
    ConnectionFailedError,
    ConnectionExpiredError,
    AuthenticationError,
    OAuthError,
    EntityMappingNotFoundError,
    EntityMappingDuplicateError,
    EntityMappingValidationError,
    SyncJobNotFoundError,
    SyncJobRunningError,
    SyncError,
    ConflictNotFoundError,
    ConflictResolutionError,
    WebhookNotFoundError,
    WebhookValidationError,
    RateLimitError,
    TransformationError,
)

# Service legacy (si utilisé)
try:
    from .service import (
        ConnectorDefinition,
        Connection,
        FieldMapping,
        EntityMapping,
        SyncJob,
        SyncLog,
        Conflict,
        ConnectionHealth,
        CONNECTOR_DEFINITIONS,
        IntegrationService,
        create_integration_service,
    )
    _has_service = True
except ImportError:
    _has_service = False

__all__ = [
    # Models
    "ConnectionModel",
    "EntityMappingModel",
    "SyncJobModel",
    "SyncLogModel",
    "ConflictModel",
    "WebhookModel",
    # Enums
    "ConnectorType",
    "AuthType",
    "ConnectionStatus",
    "SyncStatus",
    "SyncDirection",
    "SyncFrequency",
    "ConflictResolution",
    "EntityType",
    # Repositories
    "ConnectionRepository",
    "EntityMappingRepository",
    "SyncJobRepository",
    "SyncLogRepository",
    "ConflictRepository",
    "WebhookRepository",
    # Router
    "router",
    # Exceptions
    "IntegrationError",
    "ConnectionNotFoundError",
    "ConnectionDuplicateError",
    "ConnectionInactiveError",
    "ConnectionFailedError",
    "ConnectionExpiredError",
    "AuthenticationError",
    "OAuthError",
    "EntityMappingNotFoundError",
    "EntityMappingDuplicateError",
    "EntityMappingValidationError",
    "SyncJobNotFoundError",
    "SyncJobRunningError",
    "SyncError",
    "ConflictNotFoundError",
    "ConflictResolutionError",
    "WebhookNotFoundError",
    "WebhookValidationError",
    "RateLimitError",
    "TransformationError",
]

# Ajouter exports service si disponible
if _has_service:
    __all__.extend([
        "ConnectorDefinition",
        "Connection",
        "FieldMapping",
        "EntityMapping",
        "SyncJob",
        "SyncLog",
        "Conflict",
        "ConnectionHealth",
        "CONNECTOR_DEFINITIONS",
        "IntegrationService",
        "create_integration_service",
    ])
