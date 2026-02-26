"""
Schémas Pydantic - Module Integrations (GAP-086)
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


# ============== Enums ==============

class ConnectorType(str, Enum):
    SAGE = "sage"
    CEGID = "cegid"
    PENNYLANE = "pennylane"
    ODOO = "odoo"
    SAP = "sap"
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    STRIPE = "stripe"
    GOCARDLESS = "gocardless"
    QONTO = "qonto"
    MAILCHIMP = "mailchimp"
    SLACK = "slack"
    GOOGLE_DRIVE = "google_drive"
    CUSTOM = "custom"


class AuthType(str, Enum):
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC = "basic"
    BEARER = "bearer"
    HMAC = "hmac"
    CERTIFICATE = "certificate"


class SyncDirection(str, Enum):
    IMPORT = "import"
    EXPORT = "export"
    BIDIRECTIONAL = "bidirectional"


class SyncFrequency(str, Enum):
    REALTIME = "realtime"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MANUAL = "manual"


class ConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    EXPIRED = "expired"
    PENDING = "pending"


class SyncStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConflictResolution(str, Enum):
    SOURCE_WINS = "source_wins"
    TARGET_WINS = "target_wins"
    NEWEST_WINS = "newest_wins"
    MANUAL = "manual"
    MERGE = "merge"


class EntityType(str, Enum):
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    PRODUCT = "product"
    ORDER = "order"
    INVOICE = "invoice"
    PAYMENT = "payment"
    CONTACT = "contact"
    LEAD = "lead"


# ============== Field Mapping ==============

class FieldMappingSchema(BaseModel):
    source_field: str
    target_field: str
    transform: Optional[str] = None
    default_value: Optional[Any] = None
    is_required: bool = False
    source_type: Optional[str] = None
    target_type: Optional[str] = None


# ============== Connection Schemas ==============

class ConnectionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    connector_type: ConnectorType
    auth_type: AuthType
    base_url: Optional[str] = Field(None, max_length=500)
    settings: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v


class ConnectionCreate(ConnectionBase):
    credentials: Dict[str, str] = Field(default_factory=dict)
    custom_headers: Dict[str, str] = Field(default_factory=dict)


class ConnectionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    base_url: Optional[str] = None
    credentials: Optional[Dict[str, str]] = None
    custom_headers: Optional[Dict[str, str]] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ConnectionResponse(ConnectionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    status: ConnectionStatus
    last_connected_at: Optional[datetime] = None
    last_error: Optional[str] = None
    last_health_check: Optional[datetime] = None
    consecutive_errors: int = 0
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False


class ConnectionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    connector_type: ConnectorType
    status: ConnectionStatus
    is_active: bool
    last_connected_at: Optional[datetime] = None


class ConnectionList(BaseModel):
    items: List[ConnectionListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Entity Mapping Schemas ==============

class EntityMappingBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    entity_type: EntityType
    source_entity: str = Field(..., max_length=100)
    target_entity: str = Field(..., max_length=100)
    direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    dedup_key_source: Optional[str] = None
    dedup_key_target: Optional[str] = None


class EntityMappingCreate(EntityMappingBase):
    connection_id: UUID
    field_mappings: List[FieldMappingSchema] = Field(default_factory=list)
    source_filter: Optional[Dict[str, Any]] = None
    target_filter: Optional[Dict[str, Any]] = None


class EntityMappingUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    direction: Optional[SyncDirection] = None
    field_mappings: Optional[List[FieldMappingSchema]] = None
    source_filter: Optional[Dict[str, Any]] = None
    target_filter: Optional[Dict[str, Any]] = None
    dedup_key_source: Optional[str] = None
    dedup_key_target: Optional[str] = None
    is_active: Optional[bool] = None


class EntityMappingResponse(EntityMappingBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    connection_id: UUID
    field_mappings: List[Dict[str, Any]] = Field(default_factory=list)
    source_filter: Optional[Dict[str, Any]] = None
    target_filter: Optional[Dict[str, Any]] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============== Sync Job Schemas ==============

class SyncJobCreate(BaseModel):
    connection_id: UUID
    entity_mapping_id: UUID
    direction: SyncDirection
    conflict_resolution: ConflictResolution = ConflictResolution.NEWEST_WINS
    frequency: SyncFrequency = SyncFrequency.MANUAL
    cron_expression: Optional[str] = None


class SyncJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    connection_id: UUID
    entity_mapping_id: UUID
    direction: SyncDirection
    conflict_resolution: ConflictResolution
    frequency: SyncFrequency
    next_run_at: Optional[datetime] = None
    cron_expression: Optional[str] = None
    status: SyncStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_records: int = 0
    processed_records: int = 0
    created_records: int = 0
    updated_records: int = 0
    skipped_records: int = 0
    failed_records: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    last_sync_at: Optional[datetime] = None
    created_at: datetime


class SyncJobListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    connection_id: UUID
    entity_mapping_id: UUID
    direction: SyncDirection
    status: SyncStatus
    total_records: int
    processed_records: int
    failed_records: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class SyncJobList(BaseModel):
    items: List[SyncJobListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Sync Log Schemas ==============

class SyncLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    source_id: str
    target_id: Optional[str] = None
    entity_type: EntityType
    action: str
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime


class SyncLogList(BaseModel):
    items: List[SyncLogResponse]
    total: int


# ============== Conflict Schemas ==============

class ConflictResolveRequest(BaseModel):
    resolution: ConflictResolution
    resolved_data: Optional[Dict[str, Any]] = None


class ConflictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    source_id: str
    target_id: str
    entity_type: EntityType
    source_data: Dict[str, Any] = Field(default_factory=dict)
    target_data: Dict[str, Any] = Field(default_factory=dict)
    conflicting_fields: List[str] = Field(default_factory=list)
    resolution: Optional[ConflictResolution] = None
    resolved_data: Optional[Dict[str, Any]] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime


class ConflictList(BaseModel):
    items: List[ConflictResponse]
    total: int


# ============== Webhook Schemas ==============

class WebhookCreate(BaseModel):
    connection_id: UUID
    endpoint_path: str = Field(..., max_length=255)
    subscribed_events: List[str] = Field(default_factory=list)


class WebhookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    connection_id: UUID
    endpoint_path: str
    is_active: bool
    subscribed_events: List[str] = Field(default_factory=list)
    last_received_at: Optional[datetime] = None
    total_received: int = 0
    created_at: datetime


# ============== Health Check ==============

class ConnectionHealthResponse(BaseModel):
    connection_id: UUID
    is_healthy: bool
    last_check_at: datetime
    response_time_ms: int = 0
    success_rate_24h: float = 100.0
    total_requests_24h: int = 0
    last_error: Optional[str] = None
    consecutive_errors: int = 0


# ============== Stats ==============

class IntegrationStatsResponse(BaseModel):
    tenant_id: UUID
    total_connections: int = 0
    active_connections: int = 0
    total_sync_jobs: int = 0
    pending_conflicts: int = 0
    syncs_last_24h: int = 0
    records_synced_last_24h: int = 0
    failed_syncs_last_24h: int = 0
    by_connector_type: Dict[str, int] = Field(default_factory=dict)


# ============== Filters ==============

class ConnectionFilters(BaseModel):
    search: Optional[str] = Field(None, min_length=2)
    connector_type: Optional[List[ConnectorType]] = None
    status: Optional[List[ConnectionStatus]] = None
    is_active: Optional[bool] = None


class SyncJobFilters(BaseModel):
    connection_id: Optional[UUID] = None
    entity_mapping_id: Optional[UUID] = None
    status: Optional[List[SyncStatus]] = None
    direction: Optional[SyncDirection] = None


# ============== Common ==============

class AutocompleteItem(BaseModel):
    id: str
    code: str
    name: str
    label: str


class AutocompleteResponse(BaseModel):
    items: List[AutocompleteItem]


# ============== Connector Definition (read-only) ==============

class ConnectorDefinitionResponse(BaseModel):
    connector_type: ConnectorType
    name: str
    description: str
    auth_type: AuthType
    base_url: str
    supported_entities: List[EntityType] = Field(default_factory=list)
    supported_directions: List[SyncDirection] = Field(default_factory=list)
    required_fields: List[str] = Field(default_factory=list)
    optional_fields: List[str] = Field(default_factory=list)
    oauth_authorize_url: Optional[str] = None
    rate_limit_per_minute: int = 60
    icon_url: Optional[str] = None
    documentation_url: Optional[str] = None
