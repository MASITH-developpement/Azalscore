"""
AZALS MODULE GAP-086 - Schemas Integration
============================================

Schemas Pydantic pour validation et serialisation.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, EmailStr

from .models import (
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


# ============================================================================
# BASE SCHEMAS
# ============================================================================

class BaseSchema(BaseModel):
    """Schema de base avec configuration commune."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PaginatedResponse(BaseModel):
    """Reponse paginee generique."""
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# FIELD MAPPING SCHEMAS
# ============================================================================

class FieldMappingSchema(BaseModel):
    """Mapping d'un champ."""
    source_field: str = Field(..., min_length=1, max_length=100)
    target_field: str = Field(..., min_length=1, max_length=100)
    transform: str | None = Field(None, max_length=500)  # Expression de transformation
    transform_rule_code: str | None = None  # Reference a une regle
    default_value: Any | None = None
    is_required: bool = False
    source_type: str | None = None
    target_type: str | None = None


# ============================================================================
# CONNECTOR DEFINITION SCHEMAS
# ============================================================================

class ConnectorDefinitionResponse(BaseSchema):
    """Reponse pour une definition de connecteur."""
    id: UUID
    connector_type: str
    name: str
    display_name: str
    description: str | None
    category: str | None

    icon_url: str | None
    logo_url: str | None
    color: str | None

    auth_type: AuthType
    base_url: str | None
    api_version: str | None

    oauth_authorize_url: str | None
    oauth_token_url: str | None
    oauth_scopes: list[str]
    oauth_pkce_required: bool

    required_fields: list[str]
    optional_fields: list[str]

    supported_entities: list[str]
    supported_directions: list[str]

    rate_limit_requests: int
    rate_limit_daily: int | None

    supports_webhooks: bool
    webhook_events: list[str]

    documentation_url: str | None
    setup_guide_url: str | None

    is_active: bool
    is_beta: bool
    is_premium: bool


class ConnectorDefinitionList(BaseModel):
    """Liste des connecteurs."""
    items: list[ConnectorDefinitionResponse]
    total: int


# ============================================================================
# CONNECTION SCHEMAS
# ============================================================================

class ConnectionBase(BaseModel):
    """Base pour les connexions."""
    name: str = Field(..., min_length=1, max_length=255)
    code: str | None = Field(None, min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    description: str | None = Field(None, max_length=2000)
    connector_type: ConnectorType
    auth_type: AuthType
    base_url: str | None = Field(None, max_length=500)
    api_version: str | None = Field(None, max_length=20)
    settings: dict[str, Any] = Field(default_factory=dict)

    @field_validator('code', mode='before')
    @classmethod
    def uppercase_code(cls, v: str | None) -> str | None:
        if v:
            return v.upper().strip()
        return v


class ConnectionCreate(ConnectionBase):
    """Creation d'une connexion."""
    credentials: dict[str, str] = Field(default_factory=dict)
    custom_headers: dict[str, str] = Field(default_factory=dict)


class ConnectionUpdate(BaseModel):
    """Mise a jour d'une connexion."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    base_url: str | None = None
    api_version: str | None = None
    credentials: dict[str, str] | None = None
    custom_headers: dict[str, str] | None = None
    settings: dict[str, Any] | None = None
    is_active: bool | None = None


class ConnectionResponse(ConnectionBase):
    """Reponse pour une connexion."""
    id: UUID
    tenant_id: str
    status: ConnectionStatus
    health_status: HealthStatus

    last_connected_at: datetime | None
    last_error: str | None
    last_error_at: datetime | None

    last_health_check: datetime | None
    consecutive_errors: int
    success_rate_24h: float | None
    avg_response_time_ms: int | None

    is_active: bool
    is_deleted: bool

    version: int
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ConnectionListItem(BaseSchema):
    """Element de liste de connexions."""
    id: UUID
    code: str
    name: str
    connector_type: str
    auth_type: AuthType
    status: ConnectionStatus
    health_status: HealthStatus
    is_active: bool
    last_connected_at: datetime | None
    created_at: datetime


class ConnectionList(PaginatedResponse):
    """Liste de connexions."""
    items: list[ConnectionListItem]


class ConnectionHealthResponse(BaseModel):
    """Reponse de test de connexion."""
    connection_id: UUID
    is_healthy: bool
    status: ConnectionStatus
    health_status: HealthStatus
    last_check_at: datetime
    response_time_ms: int
    error: str | None = None
    details: dict[str, Any] | None = None


# ============================================================================
# DATA MAPPING SCHEMAS
# ============================================================================

class DataMappingBase(BaseModel):
    """Base pour les mappings."""
    name: str = Field(..., min_length=1, max_length=255)
    code: str | None = Field(None, min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    description: str | None = Field(None, max_length=2000)
    entity_type: EntityType
    source_entity: str = Field(..., max_length=100)
    target_entity: str = Field(..., max_length=100)
    direction: SyncDirection = SyncDirection.BIDIRECTIONAL


class DataMappingCreate(DataMappingBase):
    """Creation d'un mapping."""
    connection_id: UUID
    field_mappings: list[FieldMappingSchema] = Field(default_factory=list)
    source_key_field: str | None = None
    target_key_field: str | None = None
    source_filter: dict[str, Any] | None = None
    target_filter: dict[str, Any] | None = None
    conflict_resolution: ConflictResolution = ConflictResolution.NEWEST_WINS
    batch_size: int = Field(default=100, ge=1, le=10000)


class DataMappingUpdate(BaseModel):
    """Mise a jour d'un mapping."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    direction: SyncDirection | None = None
    field_mappings: list[FieldMappingSchema] | None = None
    source_key_field: str | None = None
    target_key_field: str | None = None
    source_filter: dict[str, Any] | None = None
    target_filter: dict[str, Any] | None = None
    conflict_resolution: ConflictResolution | None = None
    batch_size: int | None = Field(None, ge=1, le=10000)
    is_active: bool | None = None


class DataMappingResponse(DataMappingBase):
    """Reponse pour un mapping."""
    id: UUID
    tenant_id: str
    connection_id: UUID
    field_mappings: list[dict[str, Any]]
    source_key_field: str | None
    target_key_field: str | None
    source_filter: dict[str, Any] | None
    target_filter: dict[str, Any] | None
    conflict_resolution: ConflictResolution
    batch_size: int
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class DataMappingList(PaginatedResponse):
    """Liste de mappings."""
    items: list[DataMappingResponse]


# ============================================================================
# SYNC CONFIGURATION SCHEMAS
# ============================================================================

class SyncConfigurationBase(BaseModel):
    """Base pour les configurations de sync."""
    name: str = Field(..., min_length=1, max_length=255)
    code: str | None = Field(None, min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    description: str | None = Field(None, max_length=2000)
    direction: SyncDirection
    sync_mode: SyncMode = SyncMode.SCHEDULED


class SyncConfigurationCreate(SyncConfigurationBase):
    """Creation d'une configuration de sync."""
    connection_id: UUID
    mapping_id: UUID
    frequency: SyncFrequency | None = None
    cron_expression: str | None = Field(None, max_length=100)
    timezone: str = Field(default='Europe/Paris', max_length=50)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: int = Field(default=60, ge=10, le=3600)
    use_delta_sync: bool = True
    delta_field: str | None = None
    notify_on_error: bool = True
    notify_on_success: bool = False
    notification_emails: list[EmailStr] = Field(default_factory=list)
    notification_webhook_url: str | None = Field(None, max_length=500)


class SyncConfigurationUpdate(BaseModel):
    """Mise a jour d'une configuration de sync."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    sync_mode: SyncMode | None = None
    frequency: SyncFrequency | None = None
    cron_expression: str | None = None
    timezone: str | None = None
    max_retries: int | None = Field(None, ge=0, le=10)
    retry_delay_seconds: int | None = Field(None, ge=10, le=3600)
    use_delta_sync: bool | None = None
    delta_field: str | None = None
    notify_on_error: bool | None = None
    notify_on_success: bool | None = None
    notification_emails: list[EmailStr] | None = None
    notification_webhook_url: str | None = None
    is_active: bool | None = None
    is_paused: bool | None = None
    pause_reason: str | None = None


class SyncConfigurationResponse(SyncConfigurationBase):
    """Reponse pour une configuration de sync."""
    id: UUID
    tenant_id: str
    connection_id: UUID
    mapping_id: UUID
    frequency: SyncFrequency | None
    cron_expression: str | None
    timezone: str
    next_run_at: datetime | None
    last_run_at: datetime | None
    last_run_status: SyncStatus | None
    max_retries: int
    retry_delay_seconds: int
    use_delta_sync: bool
    delta_field: str | None
    notify_on_error: bool
    notify_on_success: bool
    notification_emails: list[str]
    notification_webhook_url: str | None
    is_active: bool
    is_paused: bool
    pause_reason: str | None
    total_executions: int
    successful_executions: int
    failed_executions: int
    total_records_synced: int
    version: int
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class SyncConfigurationListItem(BaseSchema):
    """Element de liste de configurations."""
    id: UUID
    code: str
    name: str
    direction: SyncDirection
    sync_mode: SyncMode
    frequency: SyncFrequency | None
    is_active: bool
    is_paused: bool
    last_run_at: datetime | None
    last_run_status: SyncStatus | None
    next_run_at: datetime | None


class SyncConfigurationList(PaginatedResponse):
    """Liste de configurations."""
    items: list[SyncConfigurationListItem]


# ============================================================================
# SYNC EXECUTION SCHEMAS
# ============================================================================

class SyncExecutionCreate(BaseModel):
    """Creation d'une execution manuelle."""
    config_id: UUID | None = None
    connection_id: UUID | None = None
    mapping_id: UUID | None = None
    direction: SyncDirection | None = None
    force_full_sync: bool = False  # Ignorer le delta


class SyncExecutionResponse(BaseSchema):
    """Reponse pour une execution."""
    id: UUID
    tenant_id: str
    connection_id: UUID | None
    config_id: UUID | None
    execution_number: str
    direction: SyncDirection
    entity_type: EntityType
    started_at: datetime
    completed_at: datetime | None
    duration_seconds: float | None
    status: SyncStatus
    total_records: int
    processed_records: int
    created_records: int
    updated_records: int
    deleted_records: int
    skipped_records: int
    failed_records: int
    progress_percent: float
    current_step: str | None
    error_count: int
    errors: list[dict[str, Any]]
    last_error: str | None
    retry_count: int
    is_retry: bool
    triggered_by: str | None
    created_at: datetime


class SyncExecutionListItem(BaseSchema):
    """Element de liste d'executions."""
    id: UUID
    execution_number: str
    connection_id: UUID | None
    config_id: UUID | None
    direction: SyncDirection
    entity_type: EntityType
    status: SyncStatus
    started_at: datetime
    completed_at: datetime | None
    duration_seconds: float | None
    total_records: int
    processed_records: int
    failed_records: int
    progress_percent: float


class SyncExecutionList(PaginatedResponse):
    """Liste d'executions."""
    items: list[SyncExecutionListItem]


# ============================================================================
# EXECUTION LOG SCHEMAS
# ============================================================================

class ExecutionLogResponse(BaseSchema):
    """Reponse pour un log d'execution."""
    id: UUID
    execution_id: UUID
    level: LogLevel
    message: str
    source_id: str | None
    target_id: str | None
    entity_type: str | None
    action: str | None
    error_code: str | None
    error_details: dict[str, Any] | None
    processing_time_ms: int | None
    timestamp: datetime


class ExecutionLogList(PaginatedResponse):
    """Liste de logs."""
    items: list[ExecutionLogResponse]


# ============================================================================
# SYNC CONFLICT SCHEMAS
# ============================================================================

class ConflictResolveRequest(BaseModel):
    """Requete de resolution de conflit."""
    resolution_strategy: ConflictResolution
    resolved_data: dict[str, Any] | None = None
    resolution_notes: str | None = Field(None, max_length=2000)


class SyncConflictResponse(BaseSchema):
    """Reponse pour un conflit."""
    id: UUID
    tenant_id: str
    execution_id: UUID
    source_id: str
    target_id: str
    entity_type: EntityType
    source_data: dict[str, Any]
    target_data: dict[str, Any]
    conflicting_fields: list[str]
    resolution_strategy: ConflictResolution | None
    resolved_data: dict[str, Any] | None
    resolved_at: datetime | None
    resolved_by: UUID | None
    resolution_notes: str | None
    is_resolved: bool
    is_ignored: bool
    created_at: datetime


class SyncConflictList(PaginatedResponse):
    """Liste de conflits."""
    items: list[SyncConflictResponse]


# ============================================================================
# WEBHOOK SCHEMAS
# ============================================================================

class WebhookBase(BaseModel):
    """Base pour les webhooks."""
    name: str = Field(..., min_length=1, max_length=255)
    code: str | None = Field(None, min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    description: str | None = Field(None, max_length=2000)
    direction: WebhookDirection


class WebhookInboundCreate(WebhookBase):
    """Creation d'un webhook entrant."""
    connection_id: UUID
    subscribed_events: list[str] = Field(default_factory=list)
    signature_header: str | None = Field(None, max_length=100)
    signature_algorithm: str | None = Field(None, max_length=20)


class WebhookOutboundCreate(WebhookBase):
    """Creation d'un webhook sortant."""
    connection_id: UUID
    target_url: str = Field(..., max_length=500)
    http_method: str = Field(default='POST', pattern=r'^(POST|PUT|PATCH)$')
    headers: dict[str, str] = Field(default_factory=dict)
    auth_type: AuthType | None = None
    auth_credentials: dict[str, str] = Field(default_factory=dict)
    subscribed_events: list[str] = Field(default_factory=list)
    payload_template: str | None = None
    include_metadata: bool = True
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: int = Field(default=30, ge=5, le=3600)
    timeout_seconds: int = Field(default=30, ge=5, le=120)


class WebhookUpdate(BaseModel):
    """Mise a jour d'un webhook."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    target_url: str | None = None
    headers: dict[str, str] | None = None
    subscribed_events: list[str] | None = None
    payload_template: str | None = None
    max_retries: int | None = Field(None, ge=0, le=10)
    retry_delay_seconds: int | None = Field(None, ge=5, le=3600)
    timeout_seconds: int | None = Field(None, ge=5, le=120)
    is_active: bool | None = None


class WebhookResponse(WebhookBase):
    """Reponse pour un webhook."""
    id: UUID
    tenant_id: str
    connection_id: UUID
    endpoint_path: str | None
    secret_key: str | None  # Masque partiellement en reponse
    target_url: str | None
    http_method: str
    headers: dict[str, str]
    auth_type: AuthType | None
    subscribed_events: list[str]
    payload_template: str | None
    include_metadata: bool
    max_retries: int
    retry_delay_seconds: int
    timeout_seconds: int
    status: WebhookStatus
    is_active: bool
    last_triggered_at: datetime | None
    total_calls: int
    successful_calls: int
    failed_calls: int
    last_error: str | None
    last_error_at: datetime | None
    version: int
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

    @field_validator('secret_key', mode='before')
    @classmethod
    def mask_secret(cls, v: str | None) -> str | None:
        if v and len(v) > 8:
            return v[:4] + '****' + v[-4:]
        return '****' if v else None


class WebhookList(PaginatedResponse):
    """Liste de webhooks."""
    items: list[WebhookResponse]


class WebhookTestRequest(BaseModel):
    """Requete de test de webhook sortant."""
    sample_payload: dict[str, Any] | None = None


class WebhookTestResponse(BaseModel):
    """Reponse de test de webhook."""
    success: bool
    status_code: int | None
    response_time_ms: int | None
    response_body: str | None
    error: str | None


# ============================================================================
# WEBHOOK LOG SCHEMAS
# ============================================================================

class WebhookLogResponse(BaseSchema):
    """Reponse pour un log webhook."""
    id: UUID
    webhook_id: UUID
    direction: WebhookDirection
    event_type: str | None
    event_id: str | None
    request_url: str | None
    request_method: str | None
    response_status_code: int | None
    duration_ms: int | None
    success: bool
    error_message: str | None
    retry_count: int
    source_ip: str | None
    timestamp: datetime


class WebhookLogList(PaginatedResponse):
    """Liste de logs webhook."""
    items: list[WebhookLogResponse]


# ============================================================================
# TRANSFORMATION RULE SCHEMAS
# ============================================================================

class TransformationRuleBase(BaseModel):
    """Base pour les regles de transformation."""
    name: str = Field(..., min_length=1, max_length=255)
    code: str | None = Field(None, min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    description: str | None = Field(None, max_length=2000)
    transformation_type: TransformationType


class TransformationRuleCreate(TransformationRuleBase):
    """Creation d'une regle de transformation."""
    config: dict[str, Any] = Field(default_factory=dict)
    source_type: str | None = None
    target_type: str | None = None
    validation_regex: str | None = Field(None, max_length=500)


class TransformationRuleUpdate(BaseModel):
    """Mise a jour d'une regle."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    config: dict[str, Any] | None = None
    source_type: str | None = None
    target_type: str | None = None
    validation_regex: str | None = None
    is_active: bool | None = None


class TransformationRuleResponse(TransformationRuleBase):
    """Reponse pour une regle."""
    id: UUID
    tenant_id: str
    config: dict[str, Any]
    source_type: str | None
    target_type: str | None
    validation_regex: str | None
    is_active: bool
    is_system: bool
    version: int
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class TransformationRuleList(PaginatedResponse):
    """Liste de regles."""
    items: list[TransformationRuleResponse]


# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================

class WidgetConfig(BaseModel):
    """Configuration d'un widget."""
    widget_type: str  # connection_status, sync_stats, recent_errors...
    title: str
    config: dict[str, Any] = Field(default_factory=dict)
    position: dict[str, int] = Field(default_factory=dict)  # x, y, width, height


class IntegrationDashboardCreate(BaseModel):
    """Creation d'un dashboard."""
    name: str = Field(..., min_length=1, max_length=200)
    code: str | None = Field(None, min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    description: str | None = Field(None, max_length=2000)
    widgets: list[WidgetConfig]
    layout: dict[str, Any] | None = None
    refresh_interval_seconds: int = Field(default=60, ge=10, le=3600)
    is_default: bool = False


class IntegrationDashboardResponse(BaseSchema):
    """Reponse pour un dashboard."""
    id: UUID
    tenant_id: str
    code: str
    name: str
    description: str | None
    widgets: list[dict[str, Any]]
    layout: dict[str, Any] | None
    refresh_interval_seconds: int
    is_default: bool
    is_public: bool
    owner_id: UUID
    shared_with: list[str]
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime | None


# ============================================================================
# STATISTICS SCHEMAS
# ============================================================================

class IntegrationStatsResponse(BaseModel):
    """Statistiques globales d'integration."""
    tenant_id: str
    total_connections: int
    active_connections: int
    connected_connections: int
    error_connections: int
    total_mappings: int
    active_mappings: int
    total_sync_configs: int
    active_sync_configs: int
    pending_conflicts: int
    executions_today: int
    executions_last_7_days: int
    records_synced_today: int
    records_synced_last_7_days: int
    failed_executions_today: int
    success_rate_today: float
    success_rate_7_days: float
    by_connector_type: dict[str, int]
    by_entity_type: dict[str, int]
    by_status: dict[str, int]


class ConnectionStatsResponse(BaseModel):
    """Statistiques d'une connexion."""
    connection_id: UUID
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    total_records_synced: int
    avg_execution_time_seconds: float
    last_execution_at: datetime | None
    executions_last_24h: int
    records_last_24h: int


# ============================================================================
# OAUTH SCHEMAS
# ============================================================================

class OAuthInitiateRequest(BaseModel):
    """Requete d'initiation OAuth."""
    connector_type: ConnectorType
    redirect_uri: str
    state: str | None = None
    scopes: list[str] | None = None


class OAuthInitiateResponse(BaseModel):
    """Reponse d'initiation OAuth."""
    authorization_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    """Requete de callback OAuth."""
    code: str
    state: str
    redirect_uri: str


class OAuthCallbackResponse(BaseModel):
    """Reponse de callback OAuth."""
    success: bool
    connection_id: UUID | None = None
    error: str | None = None


# ============================================================================
# FILTERS
# ============================================================================

class ConnectionFilters(BaseModel):
    """Filtres pour les connexions."""
    search: str | None = Field(None, min_length=2)
    connector_type: list[ConnectorType] | None = None
    status: list[ConnectionStatus] | None = None
    health_status: list[HealthStatus] | None = None
    is_active: bool | None = None


class SyncExecutionFilters(BaseModel):
    """Filtres pour les executions."""
    connection_id: UUID | None = None
    config_id: UUID | None = None
    status: list[SyncStatus] | None = None
    direction: SyncDirection | None = None
    entity_type: EntityType | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class ConflictFilters(BaseModel):
    """Filtres pour les conflits."""
    execution_id: UUID | None = None
    entity_type: EntityType | None = None
    is_resolved: bool | None = None


# ============================================================================
# AUTOCOMPLETE
# ============================================================================

class AutocompleteItem(BaseModel):
    """Element d'autocomplete."""
    id: str
    code: str
    name: str
    label: str
    extra: dict[str, Any] | None = None


class AutocompleteResponse(BaseModel):
    """Reponse d'autocomplete."""
    items: list[AutocompleteItem]
