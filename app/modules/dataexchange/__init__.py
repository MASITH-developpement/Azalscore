"""
AZALS - Module DataExchange (Import/Export de Donnees)
======================================================
Module complet d'echange de donnees multi-format avec:
- Import CSV, Excel, JSON, XML
- Export multi-formats
- Mapping de champs configurable
- Profils d'import/export
- Validation et erreurs
- Transformations de donnees
- Planification automatique
- Historique des echanges
- Connecteurs fichiers (FTP, S3, etc.)
- Notifications de resultats
- Rollback si erreur

Inspire de: Sage Data Exchange, Axonaut Import, Pennylane Connect,
Odoo Import/Export, Microsoft Dynamics 365 Data Management.

GAP-048: Import/Export de donnees
"""

# ============== Models ==============
from .models import (
    # Enumerations
    FileFormat,
    ExchangeType,
    ExchangeStatus,
    ConnectorType,
    ScheduleFrequency,
    TransformationType,
    FieldDataType,
    ValidationRuleType,
    NotificationType,
    NotificationEvent,
    ValidationSeverity,
    EntityTargetType,

    # Models
    ExchangeProfile,
    FieldMapping,
    ValidationRule,
    Transformation,
    FileConnector,
    ScheduledExchange,
    ExchangeJob,
    ExchangeLog,
    ExchangeError,
    ExchangeHistory,
    NotificationConfig,
    LookupTable,
)

# ============== Schemas ==============
from .schemas import (
    # Profile schemas
    ExchangeProfileCreate,
    ExchangeProfileUpdate,
    ExchangeProfileResponse,
    ExchangeProfileDetail,
    ExchangeProfileListItem,
    ExchangeProfileList,

    # Field Mapping schemas
    FieldMappingCreate,
    FieldMappingUpdate,
    FieldMappingResponse,

    # Validation Rule schemas
    ValidationRuleCreate,
    ValidationRuleUpdate,
    ValidationRuleResponse,

    # Transformation schemas
    TransformationCreate,
    TransformationUpdate,
    TransformationResponse,

    # Connector schemas
    FileConnectorCreate,
    FileConnectorUpdate,
    FileConnectorResponse,
    FileConnectorListItem,
    FileConnectorList,
    FileConnectorTestResult,

    # Scheduled Exchange schemas
    ScheduledExchangeCreate,
    ScheduledExchangeUpdate,
    ScheduledExchangeResponse,
    ScheduledExchangeListItem,
    ScheduledExchangeList,

    # Job schemas
    ExchangeJobCreate,
    ExchangeJobResponse,
    ExchangeJobListItem,
    ExchangeJobList,
    ExchangeJobDetail,

    # Log schemas
    ExchangeLogResponse,
    ExchangeLogList,

    # Error schemas
    ExchangeErrorResponse,
    ExchangeErrorList,

    # History schemas
    ExchangeHistoryResponse,
    ExchangeHistoryList,

    # Notification schemas
    NotificationConfigCreate,
    NotificationConfigUpdate,
    NotificationConfigResponse,

    # Lookup Table schemas
    LookupTableCreate,
    LookupTableUpdate,
    LookupTableResponse,
    LookupTableListItem,

    # Filter schemas
    ProfileFilters,
    ConnectorFilters,
    JobFilters,
    HistoryFilters,

    # Request schemas
    ImportRequest,
    ImportFromConnectorRequest,
    ExportRequest,
    RollbackRequest,

    # Preview schemas
    ImportPreviewRow,
    ImportPreviewResponse,

    # Stats schemas
    DataExchangeStatsResponse,

    # Autocomplete schemas
    AutocompleteItem,
    AutocompleteResponse,

    # Schema enums (duplicated for convenience)
    OnDuplicate,
    OnError,
)

# ============== Repository ==============
from .repository import (
    ExchangeProfileRepository,
    FieldMappingRepository,
    ValidationRuleRepository,
    TransformationRepository,
    FileConnectorRepository,
    ScheduledExchangeRepository,
    ExchangeJobRepository,
    ExchangeLogRepository,
    ExchangeErrorRepository,
    ExchangeHistoryRepository,
    NotificationConfigRepository,
    LookupTableRepository,
)

# ============== Service ==============
from .service import (
    # Legacy enumerations (from GAP-048)
    ImportFormat,
    ExportFormat,
    ImportStatus,
    ExportStatus,
    FieldType,
    ValidationAction,
    DuplicateAction,

    # Legacy data classes
    FieldMapping as LegacyFieldMapping,
    ImportProfile,
    ValidationError as LegacyValidationError,
    ImportJob,
    ExportProfile,
    ExportJob,
    ScheduledExport,

    # Service
    DataExchangeService,
    create_dataexchange_service,
)

# ============== Exceptions ==============
from .exceptions import (
    # Base exception
    DataExchangeError,

    # Profile errors
    ProfileNotFoundError,
    ProfileDuplicateCodeError,
    ProfileInUseError,
    SystemProfileError,

    # Connector errors
    ConnectorNotFoundError,
    ConnectorDuplicateCodeError,
    ConnectorConnectionError,
    ConnectorAuthenticationError,
    ConnectorInUseError,

    # Schedule errors
    ScheduledExchangeNotFoundError,
    ScheduledExchangeDuplicateCodeError,
    InvalidCronExpressionError,

    # Job errors
    JobNotFoundError,
    JobAlreadyRunningError,
    JobCannotBeCancelledError,
    JobCannotBeRolledBackError,
    JobAlreadyRolledBackError,

    # File errors
    FileNotFoundError as DataExchangeFileNotFoundError,
    FileFormatError,
    FileReadError,
    FileWriteError,
    FileTooLargeError,
    FileEncodingError,

    # Validation errors
    ValidationError,
    RequiredFieldMissingError,
    InvalidFieldValueError,
    DuplicateKeyError,
    ReferenceNotFoundError,

    # Mapping errors
    MappingNotFoundError,
    MappingConfigurationError,
    NoKeyFieldDefinedError,

    # Transformation errors
    TransformationError,
    TransformationScriptError,
    LookupTableNotFoundError,
    LookupValueNotFoundError,

    # Notification errors
    NotificationConfigNotFoundError,
    NotificationSendError,

    # Processing errors
    ProcessingError,
    EntityCreationError,
    EntityUpdateError,
    RollbackError,
)

# ============== Router ==============
from .router import router

__all__ = [
    # Router
    "router",

    # Enumerations (models)
    "FileFormat",
    "ExchangeType",
    "ExchangeStatus",
    "ConnectorType",
    "ScheduleFrequency",
    "TransformationType",
    "FieldDataType",
    "ValidationRuleType",
    "NotificationType",
    "NotificationEvent",
    "ValidationSeverity",
    "EntityTargetType",

    # Models
    "ExchangeProfile",
    "FieldMapping",
    "ValidationRule",
    "Transformation",
    "FileConnector",
    "ScheduledExchange",
    "ExchangeJob",
    "ExchangeLog",
    "ExchangeError",
    "ExchangeHistory",
    "NotificationConfig",
    "LookupTable",

    # Schemas - Profile
    "ExchangeProfileCreate",
    "ExchangeProfileUpdate",
    "ExchangeProfileResponse",
    "ExchangeProfileDetail",
    "ExchangeProfileListItem",
    "ExchangeProfileList",

    # Schemas - Field Mapping
    "FieldMappingCreate",
    "FieldMappingUpdate",
    "FieldMappingResponse",

    # Schemas - Validation Rule
    "ValidationRuleCreate",
    "ValidationRuleUpdate",
    "ValidationRuleResponse",

    # Schemas - Transformation
    "TransformationCreate",
    "TransformationUpdate",
    "TransformationResponse",

    # Schemas - Connector
    "FileConnectorCreate",
    "FileConnectorUpdate",
    "FileConnectorResponse",
    "FileConnectorListItem",
    "FileConnectorList",
    "FileConnectorTestResult",

    # Schemas - Scheduled Exchange
    "ScheduledExchangeCreate",
    "ScheduledExchangeUpdate",
    "ScheduledExchangeResponse",
    "ScheduledExchangeListItem",
    "ScheduledExchangeList",

    # Schemas - Job
    "ExchangeJobCreate",
    "ExchangeJobResponse",
    "ExchangeJobListItem",
    "ExchangeJobList",
    "ExchangeJobDetail",

    # Schemas - Log
    "ExchangeLogResponse",
    "ExchangeLogList",

    # Schemas - Error
    "ExchangeErrorResponse",
    "ExchangeErrorList",

    # Schemas - History
    "ExchangeHistoryResponse",
    "ExchangeHistoryList",

    # Schemas - Notification
    "NotificationConfigCreate",
    "NotificationConfigUpdate",
    "NotificationConfigResponse",

    # Schemas - Lookup Table
    "LookupTableCreate",
    "LookupTableUpdate",
    "LookupTableResponse",
    "LookupTableListItem",

    # Schemas - Filters
    "ProfileFilters",
    "ConnectorFilters",
    "JobFilters",
    "HistoryFilters",

    # Schemas - Requests
    "ImportRequest",
    "ImportFromConnectorRequest",
    "ExportRequest",
    "RollbackRequest",

    # Schemas - Preview
    "ImportPreviewRow",
    "ImportPreviewResponse",

    # Schemas - Stats
    "DataExchangeStatsResponse",

    # Schemas - Autocomplete
    "AutocompleteItem",
    "AutocompleteResponse",

    # Schema enums
    "OnDuplicate",
    "OnError",

    # Repositories
    "ExchangeProfileRepository",
    "FieldMappingRepository",
    "ValidationRuleRepository",
    "TransformationRepository",
    "FileConnectorRepository",
    "ScheduledExchangeRepository",
    "ExchangeJobRepository",
    "ExchangeLogRepository",
    "ExchangeErrorRepository",
    "ExchangeHistoryRepository",
    "NotificationConfigRepository",
    "LookupTableRepository",

    # Service (legacy from GAP-048)
    "ImportFormat",
    "ExportFormat",
    "ImportStatus",
    "ExportStatus",
    "FieldType",
    "ValidationAction",
    "DuplicateAction",
    "LegacyFieldMapping",
    "ImportProfile",
    "LegacyValidationError",
    "ImportJob",
    "ExportProfile",
    "ExportJob",
    "ScheduledExport",
    "DataExchangeService",
    "create_dataexchange_service",

    # Exceptions
    "DataExchangeError",
    "ProfileNotFoundError",
    "ProfileDuplicateCodeError",
    "ProfileInUseError",
    "SystemProfileError",
    "ConnectorNotFoundError",
    "ConnectorDuplicateCodeError",
    "ConnectorConnectionError",
    "ConnectorAuthenticationError",
    "ConnectorInUseError",
    "ScheduledExchangeNotFoundError",
    "ScheduledExchangeDuplicateCodeError",
    "InvalidCronExpressionError",
    "JobNotFoundError",
    "JobAlreadyRunningError",
    "JobCannotBeCancelledError",
    "JobCannotBeRolledBackError",
    "JobAlreadyRolledBackError",
    "DataExchangeFileNotFoundError",
    "FileFormatError",
    "FileReadError",
    "FileWriteError",
    "FileTooLargeError",
    "FileEncodingError",
    "ValidationError",
    "RequiredFieldMissingError",
    "InvalidFieldValueError",
    "DuplicateKeyError",
    "ReferenceNotFoundError",
    "MappingNotFoundError",
    "MappingConfigurationError",
    "NoKeyFieldDefinedError",
    "TransformationError",
    "TransformationScriptError",
    "LookupTableNotFoundError",
    "LookupValueNotFoundError",
    "NotificationConfigNotFoundError",
    "NotificationSendError",
    "ProcessingError",
    "EntityCreationError",
    "EntityUpdateError",
    "RollbackError",
]
