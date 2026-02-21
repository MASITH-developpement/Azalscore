"""
AZALS MODULE GAP-086 - Integration Hub
======================================

Module de gestion des integrations tierces:
- Connecteurs preconfigures (Google, Microsoft, Slack, etc.)
- Configuration OAuth par tenant
- Mappings de donnees
- Synchronisation temps reel et batch
- Logs d'execution
- Retry automatique
- Webhooks entrants/sortants
- Transformations de donnees
- Monitoring sante connecteurs
- Dashboard integrations

Inspire de Zapier, Make, Microsoft Dynamics 365, Odoo.
"""

# Models SQLAlchemy
from .models import (
    Connection,
    ConnectorDefinition as ConnectorDefinitionModel,
    DataMapping as DataMappingModel,
    ExecutionLog,
    IntegrationDashboard,
    SyncConfiguration,
    SyncConflict,
    SyncExecution,
    TransformationRule,
    Webhook,
    WebhookLog,
    # Enums
    AuthType,
    ConflictResolution,
    ConnectionStatus,
    ConnectorType,
    EntityType,
    HealthStatus,
    LogLevel,
    SyncDirection,
    SyncFrequency,
    SyncMode,
    SyncStatus,
    TransformationType,
    WebhookDirection,
    WebhookStatus,
)

# Repositories
from .repository import (
    ConnectionRepository,
    ConnectorDefinitionRepository,
    DataMappingRepository,
    ExecutionLogRepository,
    IntegrationDashboardRepository,
    SyncConfigurationRepository,
    SyncConflictRepository,
    SyncExecutionRepository,
    TransformationRuleRepository,
    WebhookLogRepository,
    WebhookRepository,
)

# Service
from .service import (
    ConnectorDefinition,
    CONNECTOR_DEFINITIONS,
    IntegrationService,
    create_integration_service,
)

# Router
from .router import router

# Exceptions
from .exceptions import (
    IntegrationError,
    ConnectorNotFoundError,
    ConnectorNotSupportedError,
    ConnectorConfigurationError,
    ConnectionNotFoundError,
    ConnectionDuplicateError,
    ConnectionFailedError,
    ConnectionExpiredError,
    ConnectionInactiveError,
    ConnectionRateLimitedError,
    AuthenticationError,
    OAuthError,
    OAuthStateError,
    OAuthTokenRefreshError,
    MappingNotFoundError,
    MappingDuplicateError,
    MappingValidationError,
    MappingFieldError,
    SyncConfigNotFoundError,
    SyncConfigDuplicateError,
    SyncConfigInvalidCronError,
    SyncExecutionNotFoundError,
    SyncExecutionRunningError,
    SyncExecutionFailedError,
    SyncExecutionTimeoutError,
    SyncExecutionCancelledError,
    ConflictNotFoundError,
    ConflictAlreadyResolvedError,
    ConflictResolutionError,
    WebhookNotFoundError,
    WebhookDuplicateError,
    WebhookValidationError,
    WebhookDeliveryError,
    WebhookTimeoutError,
    TransformationRuleNotFoundError,
    TransformationError,
    TransformationScriptError,
    ExternalAPIError,
    ExternalAPITimeoutError,
    ExternalAPIRateLimitError,
    DataValidationError,
    DataDeduplicationError,
)

__all__ = [
    # Models
    "Connection",
    "ConnectorDefinitionModel",
    "DataMappingModel",
    "ExecutionLog",
    "IntegrationDashboard",
    "SyncConfiguration",
    "SyncConflict",
    "SyncExecution",
    "TransformationRule",
    "Webhook",
    "WebhookLog",
    # Enums
    "AuthType",
    "ConflictResolution",
    "ConnectionStatus",
    "ConnectorType",
    "EntityType",
    "HealthStatus",
    "LogLevel",
    "SyncDirection",
    "SyncFrequency",
    "SyncMode",
    "SyncStatus",
    "TransformationType",
    "WebhookDirection",
    "WebhookStatus",
    # Repositories
    "ConnectionRepository",
    "ConnectorDefinitionRepository",
    "DataMappingRepository",
    "ExecutionLogRepository",
    "IntegrationDashboardRepository",
    "SyncConfigurationRepository",
    "SyncConflictRepository",
    "SyncExecutionRepository",
    "TransformationRuleRepository",
    "WebhookLogRepository",
    "WebhookRepository",
    # Service
    "ConnectorDefinition",
    "CONNECTOR_DEFINITIONS",
    "IntegrationService",
    "create_integration_service",
    # Router
    "router",
    # Exceptions
    "IntegrationError",
    "ConnectorNotFoundError",
    "ConnectorNotSupportedError",
    "ConnectorConfigurationError",
    "ConnectionNotFoundError",
    "ConnectionDuplicateError",
    "ConnectionFailedError",
    "ConnectionExpiredError",
    "ConnectionInactiveError",
    "ConnectionRateLimitedError",
    "AuthenticationError",
    "OAuthError",
    "OAuthStateError",
    "OAuthTokenRefreshError",
    "MappingNotFoundError",
    "MappingDuplicateError",
    "MappingValidationError",
    "MappingFieldError",
    "SyncConfigNotFoundError",
    "SyncConfigDuplicateError",
    "SyncConfigInvalidCronError",
    "SyncExecutionNotFoundError",
    "SyncExecutionRunningError",
    "SyncExecutionFailedError",
    "SyncExecutionTimeoutError",
    "SyncExecutionCancelledError",
    "ConflictNotFoundError",
    "ConflictAlreadyResolvedError",
    "ConflictResolutionError",
    "WebhookNotFoundError",
    "WebhookDuplicateError",
    "WebhookValidationError",
    "WebhookDeliveryError",
    "WebhookTimeoutError",
    "TransformationRuleNotFoundError",
    "TransformationError",
    "TransformationScriptError",
    "ExternalAPIError",
    "ExternalAPITimeoutError",
    "ExternalAPIRateLimitError",
    "DataValidationError",
    "DataDeduplicationError",
]
