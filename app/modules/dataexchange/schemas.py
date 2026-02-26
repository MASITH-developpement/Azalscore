"""
AZALS - Module DataExchange - Schemas Pydantic
===============================================
Schemas de validation pour Import/Export de donnees.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# ============== Enumerations ==============

class FileFormat(str, Enum):
    CSV = "csv"
    EXCEL = "excel"
    XLSX = "xlsx"
    XLS = "xls"
    JSON = "json"
    XML = "xml"
    OFX = "ofx"
    QIF = "qif"
    CFONB = "cfonb"
    FEC = "fec"
    EBICS = "ebics"


class ExchangeType(str, Enum):
    IMPORT = "import"
    EXPORT = "export"


class ExchangeStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    VALIDATING = "validating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"


class ConnectorType(str, Enum):
    LOCAL = "local"
    FTP = "ftp"
    SFTP = "sftp"
    S3 = "s3"
    GCS = "gcs"
    AZURE_BLOB = "azure_blob"
    WEBDAV = "webdav"
    API = "api"


class ScheduleFrequency(str, Enum):
    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"


class TransformationType(str, Enum):
    NONE = "none"
    UPPERCASE = "uppercase"
    LOWERCASE = "lowercase"
    TRIM = "trim"
    REPLACE = "replace"
    FORMAT_DATE = "format_date"
    FORMAT_NUMBER = "format_number"
    LOOKUP = "lookup"
    FORMULA = "formula"
    CONCAT = "concat"
    SPLIT = "split"
    DEFAULT = "default"
    MAP = "map"
    CUSTOM = "custom"


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class EntityTargetType(str, Enum):
    CONTACT = "contact"
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    PRODUCT = "product"
    INVOICE = "invoice"
    ORDER = "order"
    PAYMENT = "payment"
    JOURNAL_ENTRY = "journal_entry"
    ACCOUNT = "account"
    EMPLOYEE = "employee"
    PROJECT = "project"
    TASK = "task"
    EXPENSE = "expense"
    INVENTORY = "inventory"
    CUSTOM = "custom"


class NotificationType(str, Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    SMS = "sms"
    IN_APP = "in_app"


class OnDuplicate(str, Enum):
    SKIP = "skip"
    UPDATE = "update"
    ERROR = "error"
    CREATE_NEW = "create_new"


class OnError(str, Enum):
    CONTINUE = "continue"
    STOP = "stop"
    ROLLBACK = "rollback"


# ============== Field Mapping Schemas ==============

class FieldMappingBase(BaseModel):
    source_field: str = Field(..., min_length=1, max_length=255)
    target_field: str = Field(..., min_length=1, max_length=255)
    source_column_index: Optional[int] = Field(None, ge=0)
    source_type: str = Field(default="string", max_length=50)
    target_type: str = Field(default="string", max_length=50)
    is_required: bool = False
    is_key: bool = False
    default_value: Optional[str] = None
    format_pattern: Optional[str] = Field(None, max_length=255)
    transformation_type: TransformationType = TransformationType.NONE
    transformation_config: Dict[str, Any] = Field(default_factory=dict)
    sort_order: int = Field(default=0, ge=0)


class FieldMappingCreate(FieldMappingBase):
    pass


class FieldMappingUpdate(BaseModel):
    source_field: Optional[str] = Field(None, min_length=1, max_length=255)
    target_field: Optional[str] = Field(None, min_length=1, max_length=255)
    source_column_index: Optional[int] = Field(None, ge=0)
    source_type: Optional[str] = Field(None, max_length=50)
    target_type: Optional[str] = Field(None, max_length=50)
    is_required: Optional[bool] = None
    is_key: Optional[bool] = None
    default_value: Optional[str] = None
    format_pattern: Optional[str] = None
    transformation_type: Optional[TransformationType] = None
    transformation_config: Optional[Dict[str, Any]] = None
    sort_order: Optional[int] = Field(None, ge=0)


class FieldMappingResponse(FieldMappingBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    profile_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============== Validation Rule Schemas ==============

class ValidationRuleBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_field: Optional[str] = Field(None, max_length=255)
    rule_type: str = Field(..., max_length=50)  # required, regex, range, unique, lookup, custom
    rule_config: Dict[str, Any] = Field(default_factory=dict)
    severity: ValidationSeverity = ValidationSeverity.ERROR
    stop_on_fail: bool = False
    error_message: Optional[str] = Field(None, max_length=500)
    error_message_template: Optional[str] = Field(None, max_length=500)
    is_active: bool = True
    sort_order: int = Field(default=0, ge=0)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.upper().strip()


class ValidationRuleCreate(ValidationRuleBase):
    pass


class ValidationRuleUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_field: Optional[str] = None
    rule_type: Optional[str] = None
    rule_config: Optional[Dict[str, Any]] = None
    severity: Optional[ValidationSeverity] = None
    stop_on_fail: Optional[bool] = None
    error_message: Optional[str] = None
    error_message_template: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class ValidationRuleResponse(ValidationRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    profile_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============== Transformation Schemas ==============

class TransformationBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    transformation_type: TransformationType
    source_fields: List[str] = Field(default_factory=list)
    target_field: Optional[str] = Field(None, max_length=255)
    config: Dict[str, Any] = Field(default_factory=dict)
    script: Optional[str] = None
    apply_on: str = Field(default="row", pattern="^(row|cell|file)$")
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.upper().strip()


class TransformationCreate(TransformationBase):
    pass


class TransformationUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    name: Optional[str] = None
    description: Optional[str] = None
    transformation_type: Optional[TransformationType] = None
    source_fields: Optional[List[str]] = None
    target_field: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    script: Optional[str] = None
    apply_on: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class TransformationResponse(TransformationBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    profile_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============== Exchange Profile Schemas ==============

class ExchangeProfileBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    exchange_type: ExchangeType
    file_format: FileFormat
    entity_type: EntityTargetType

    # File options
    file_encoding: str = Field(default="utf-8", max_length=20)
    csv_delimiter: str = Field(default=",", max_length=5)
    csv_quote_char: str = Field(default='"', max_length=5)
    csv_has_header: bool = True
    excel_sheet_name: Optional[str] = Field(None, max_length=100)
    excel_start_row: int = Field(default=1, ge=1)
    xml_root_element: Optional[str] = Field(None, max_length=100)
    xml_row_element: Optional[str] = Field(None, max_length=100)
    json_root_path: Optional[str] = Field(None, max_length=255)

    # Advanced options
    skip_empty_rows: bool = True
    trim_values: bool = True
    date_format: str = Field(default="%Y-%m-%d", max_length=50)
    decimal_separator: str = Field(default=".", max_length=5)
    thousand_separator: str = Field(default="", max_length=5)
    null_value: str = Field(default="", max_length=20)

    # Export options
    include_header: bool = True
    export_template: Optional[str] = None

    # Behavior
    on_duplicate: OnDuplicate = OnDuplicate.UPDATE
    on_error: OnError = OnError.CONTINUE
    batch_size: int = Field(default=100, ge=1, le=10000)
    enable_rollback: bool = True

    # Validation
    validate_before_import: bool = True
    strict_validation: bool = False

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.upper().strip()


class ExchangeProfileCreate(ExchangeProfileBase):
    field_mappings: List[FieldMappingCreate] = Field(default_factory=list)
    validation_rules: List[ValidationRuleCreate] = Field(default_factory=list)
    transformations: List[TransformationCreate] = Field(default_factory=list)


class ExchangeProfileUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    file_format: Optional[FileFormat] = None
    entity_type: Optional[EntityTargetType] = None

    file_encoding: Optional[str] = None
    csv_delimiter: Optional[str] = None
    csv_quote_char: Optional[str] = None
    csv_has_header: Optional[bool] = None
    excel_sheet_name: Optional[str] = None
    excel_start_row: Optional[int] = None
    xml_root_element: Optional[str] = None
    xml_row_element: Optional[str] = None
    json_root_path: Optional[str] = None

    skip_empty_rows: Optional[bool] = None
    trim_values: Optional[bool] = None
    date_format: Optional[str] = None
    decimal_separator: Optional[str] = None
    thousand_separator: Optional[str] = None
    null_value: Optional[str] = None

    include_header: Optional[bool] = None
    export_template: Optional[str] = None

    on_duplicate: Optional[OnDuplicate] = None
    on_error: Optional[OnError] = None
    batch_size: Optional[int] = None
    enable_rollback: Optional[bool] = None

    validate_before_import: Optional[bool] = None
    strict_validation: Optional[bool] = None

    is_active: Optional[bool] = None


class ExchangeProfileResponse(ExchangeProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    is_system: bool = False
    is_active: bool = True
    is_deleted: bool = False
    version: int = 1
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[UUID] = None


class ExchangeProfileDetail(ExchangeProfileResponse):
    field_mappings: List[FieldMappingResponse] = Field(default_factory=list)
    validations: List[ValidationRuleResponse] = Field(default_factory=list)
    transformations: List[TransformationResponse] = Field(default_factory=list)


class ExchangeProfileListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    exchange_type: ExchangeType
    file_format: FileFormat
    entity_type: EntityTargetType
    is_active: bool
    is_system: bool
    created_at: datetime


class ExchangeProfileList(BaseModel):
    items: List[ExchangeProfileListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============== File Connector Schemas ==============

class FileConnectorBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    connector_type: ConnectorType

    # Connection
    host: Optional[str] = Field(None, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    username: Optional[str] = Field(None, max_length=255)

    # S3/Cloud
    bucket_name: Optional[str] = Field(None, max_length=255)
    region: Optional[str] = Field(None, max_length=50)
    endpoint_url: Optional[str] = Field(None, max_length=500)

    # Paths
    base_path: str = Field(default="/", max_length=500)
    input_path: Optional[str] = Field(None, max_length=500)
    output_path: Optional[str] = Field(None, max_length=500)
    archive_path: Optional[str] = Field(None, max_length=500)
    error_path: Optional[str] = Field(None, max_length=500)

    # Options
    passive_mode: bool = True
    verify_ssl: bool = True
    timeout_seconds: int = Field(default=30, ge=5, le=300)
    retry_count: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: int = Field(default=5, ge=1, le=60)

    # File pattern
    file_pattern: Optional[str] = Field(None, max_length=255)
    archive_after_process: bool = True
    delete_after_process: bool = False

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.upper().strip()


class FileConnectorCreate(FileConnectorBase):
    password: Optional[str] = None
    private_key: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None


class FileConnectorUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    name: Optional[str] = None
    description: Optional[str] = None

    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    private_key: Optional[str] = None

    bucket_name: Optional[str] = None
    region: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    endpoint_url: Optional[str] = None

    base_path: Optional[str] = None
    input_path: Optional[str] = None
    output_path: Optional[str] = None
    archive_path: Optional[str] = None
    error_path: Optional[str] = None

    passive_mode: Optional[bool] = None
    verify_ssl: Optional[bool] = None
    timeout_seconds: Optional[int] = None
    retry_count: Optional[int] = None
    retry_delay_seconds: Optional[int] = None

    file_pattern: Optional[str] = None
    archive_after_process: Optional[bool] = None
    delete_after_process: Optional[bool] = None

    is_active: Optional[bool] = None


class FileConnectorResponse(FileConnectorBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    is_active: bool = True
    is_deleted: bool = False
    last_connected_at: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_errors: int = 0
    version: int = 1
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: Optional[datetime] = None


class FileConnectorListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    connector_type: ConnectorType
    is_active: bool
    last_connected_at: Optional[datetime] = None
    consecutive_errors: int = 0


class FileConnectorList(BaseModel):
    items: List[FileConnectorListItem]
    total: int
    page: int
    page_size: int
    pages: int


class FileConnectorTestResult(BaseModel):
    success: bool
    message: str
    response_time_ms: int = 0
    files_found: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)


# ============== Scheduled Exchange Schemas ==============

class ScheduledExchangeBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

    profile_id: UUID
    connector_id: Optional[UUID] = None

    frequency: ScheduleFrequency
    cron_expression: Optional[str] = Field(None, max_length=100)
    scheduled_time: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    scheduled_day: Optional[int] = Field(None, ge=0, le=6)
    scheduled_day_of_month: Optional[int] = Field(None, ge=1, le=31)
    timezone: str = Field(default="Europe/Paris", max_length=50)

    source_path: Optional[str] = Field(None, max_length=500)
    destination_path: Optional[str] = Field(None, max_length=500)
    file_naming_pattern: Optional[str] = Field(None, max_length=255)

    notify_on_success: bool = False
    notify_on_failure: bool = True
    notification_config: Dict[str, Any] = Field(default_factory=dict)

    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_minutes: int = Field(default=15, ge=1, le=1440)
    pause_on_consecutive_failures: int = Field(default=5, ge=1, le=100)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.upper().strip()

    @model_validator(mode='after')
    def validate_schedule(self):
        if self.frequency == ScheduleFrequency.CRON and not self.cron_expression:
            raise ValueError("cron_expression is required when frequency is CRON")
        return self


class ScheduledExchangeCreate(ScheduledExchangeBase):
    pass


class ScheduledExchangeUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    name: Optional[str] = None
    description: Optional[str] = None
    connector_id: Optional[UUID] = None

    frequency: Optional[ScheduleFrequency] = None
    cron_expression: Optional[str] = None
    scheduled_time: Optional[str] = None
    scheduled_day: Optional[int] = None
    scheduled_day_of_month: Optional[int] = None
    timezone: Optional[str] = None

    source_path: Optional[str] = None
    destination_path: Optional[str] = None
    file_naming_pattern: Optional[str] = None

    notify_on_success: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
    notification_config: Optional[Dict[str, Any]] = None

    max_retries: Optional[int] = None
    retry_delay_minutes: Optional[int] = None
    pause_on_consecutive_failures: Optional[int] = None

    is_active: Optional[bool] = None


class ScheduledExchangeResponse(ScheduledExchangeBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    is_active: bool = True
    is_deleted: bool = False
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    next_run_at: Optional[datetime] = None
    run_count: int = 0
    failure_count: int = 0
    consecutive_failures: int = 0
    version: int = 1
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: Optional[datetime] = None


class ScheduledExchangeListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    frequency: ScheduleFrequency
    is_active: bool
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    next_run_at: Optional[datetime] = None


class ScheduledExchangeList(BaseModel):
    items: List[ScheduledExchangeListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Exchange Job Schemas ==============

class ExchangeJobCreate(BaseModel):
    profile_id: UUID
    connector_id: Optional[UUID] = None
    options: Dict[str, Any] = Field(default_factory=dict)


class ExchangeJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    reference: str
    profile_id: UUID
    scheduled_id: Optional[UUID] = None
    connector_id: Optional[UUID] = None

    exchange_type: ExchangeType
    entity_type: str
    status: ExchangeStatus

    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_format: Optional[str] = None

    output_file_name: Optional[str] = None
    output_file_path: Optional[str] = None
    output_file_size: Optional[int] = None

    total_rows: int = 0
    processed_rows: int = 0
    created_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    warning_count: int = 0

    progress_percent: Decimal = Decimal("0")
    current_phase: Optional[str] = None

    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None

    error_message: Optional[str] = None
    error_details: Dict[str, Any] = Field(default_factory=dict)

    rolled_back_at: Optional[datetime] = None
    triggered_by: str = "manual"

    version: int = 1
    created_at: datetime
    created_by: Optional[UUID] = None


class ExchangeJobListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reference: str
    exchange_type: ExchangeType
    entity_type: str
    status: ExchangeStatus
    file_name: Optional[str] = None
    total_rows: int = 0
    processed_rows: int = 0
    error_count: int = 0
    progress_percent: Decimal = Decimal("0")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    triggered_by: str = "manual"


class ExchangeJobList(BaseModel):
    items: List[ExchangeJobListItem]
    total: int
    page: int
    page_size: int
    pages: int


class ExchangeJobDetail(ExchangeJobResponse):
    logs_count: int = 0
    errors_count: int = 0
    warnings_count: int = 0


# ============== Exchange Log Schemas ==============

class ExchangeLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    row_number: int
    action: str
    entity_id: Optional[UUID] = None
    entity_reference: Optional[str] = None
    source_data: Dict[str, Any] = Field(default_factory=dict)
    target_data: Dict[str, Any] = Field(default_factory=dict)
    changes: Dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    timestamp: datetime


class ExchangeLogList(BaseModel):
    items: List[ExchangeLogResponse]
    total: int


# ============== Exchange Error Schemas ==============

class ExchangeErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    row_number: Optional[int] = None
    column_name: Optional[str] = None
    field_name: Optional[str] = None
    error_code: str
    error_type: str
    severity: ValidationSeverity
    message: str
    source_value: Optional[str] = None
    expected_value: Optional[str] = None
    rule_code: Optional[str] = None
    row_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class ExchangeErrorList(BaseModel):
    items: List[ExchangeErrorResponse]
    total: int


# ============== History Schemas ==============

class ExchangeHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    exchange_type: ExchangeType
    entity_type: str
    profile_code: Optional[str] = None
    status: ExchangeStatus
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_format: Optional[str] = None
    total_rows: int = 0
    created_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    triggered_by: Optional[str] = None
    executed_by: Optional[UUID] = None
    created_at: datetime


class ExchangeHistoryList(BaseModel):
    items: List[ExchangeHistoryResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Notification Config Schemas ==============

class NotificationConfigBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    notification_type: NotificationType

    email_to: List[str] = Field(default_factory=list)
    email_cc: List[str] = Field(default_factory=list)
    email_template: Optional[str] = None

    webhook_url: Optional[str] = Field(None, max_length=500)
    webhook_headers: Dict[str, str] = Field(default_factory=dict)
    webhook_method: str = Field(default="POST", pattern="^(POST|PUT)$")

    channel_id: Optional[str] = Field(None, max_length=255)

    notify_on_success: bool = False
    notify_on_failure: bool = True
    notify_on_warning: bool = False
    min_error_count: int = Field(default=0, ge=0)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.upper().strip()


class NotificationConfigCreate(NotificationConfigBase):
    bot_token: Optional[str] = None


class NotificationConfigUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    name: Optional[str] = None
    notification_type: Optional[NotificationType] = None

    email_to: Optional[List[str]] = None
    email_cc: Optional[List[str]] = None
    email_template: Optional[str] = None

    webhook_url: Optional[str] = None
    webhook_headers: Optional[Dict[str, str]] = None
    webhook_method: Optional[str] = None

    channel_id: Optional[str] = None
    bot_token: Optional[str] = None

    notify_on_success: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
    notify_on_warning: Optional[bool] = None
    min_error_count: Optional[int] = None

    is_active: Optional[bool] = None


class NotificationConfigResponse(NotificationConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    is_active: bool = True
    is_deleted: bool = False
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: Optional[datetime] = None


# ============== Lookup Table Schemas ==============

class LookupTableBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    entries: Dict[str, str] = Field(default_factory=dict)
    case_sensitive: bool = False
    default_value: Optional[str] = Field(None, max_length=255)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.upper().strip()


class LookupTableCreate(LookupTableBase):
    pass


class LookupTableUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    name: Optional[str] = None
    description: Optional[str] = None
    entries: Optional[Dict[str, str]] = None
    case_sensitive: Optional[bool] = None
    default_value: Optional[str] = None
    is_active: Optional[bool] = None


class LookupTableResponse(LookupTableBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    is_active: bool = True
    is_deleted: bool = False
    version: int = 1
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: Optional[datetime] = None


class LookupTableListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    entries_count: int = 0
    is_active: bool


# ============== Import/Export Request Schemas ==============

class ImportRequest(BaseModel):
    """Demande d'import depuis un fichier uploade."""
    profile_id: UUID
    options: Dict[str, Any] = Field(default_factory=dict)
    validate_only: bool = False


class ImportFromConnectorRequest(BaseModel):
    """Demande d'import depuis un connecteur."""
    profile_id: UUID
    connector_id: UUID
    file_path: Optional[str] = None
    options: Dict[str, Any] = Field(default_factory=dict)
    validate_only: bool = False


class ExportRequest(BaseModel):
    """Demande d'export."""
    profile_id: UUID
    connector_id: Optional[UUID] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)


class RollbackRequest(BaseModel):
    """Demande de rollback."""
    reason: Optional[str] = Field(None, max_length=500)


# ============== Preview Schemas ==============

class ImportPreviewRow(BaseModel):
    row_number: int
    data: Dict[str, Any]
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    action: str = "create"  # create, update, skip


class ImportPreviewResponse(BaseModel):
    total_rows: int
    valid_rows: int
    error_rows: int
    warning_rows: int
    sample_rows: List[ImportPreviewRow]
    detected_columns: List[str]
    mapped_fields: Dict[str, str]
    validation_errors: List[ExchangeErrorResponse]


# ============== Stats Schemas ==============

class DataExchangeStatsResponse(BaseModel):
    tenant_id: str
    total_profiles: int = 0
    active_profiles: int = 0
    total_connectors: int = 0
    active_connectors: int = 0
    total_scheduled: int = 0
    active_scheduled: int = 0
    total_jobs_24h: int = 0
    successful_jobs_24h: int = 0
    failed_jobs_24h: int = 0
    records_imported_24h: int = 0
    records_exported_24h: int = 0
    by_entity_type: Dict[str, int] = Field(default_factory=dict)
    by_format: Dict[str, int] = Field(default_factory=dict)


# ============== Filters ==============

class ProfileFilters(BaseModel):
    search: Optional[str] = Field(None, min_length=2)
    exchange_type: Optional[ExchangeType] = None
    file_format: Optional[FileFormat] = None
    entity_type: Optional[EntityTargetType] = None
    is_active: Optional[bool] = None


class ConnectorFilters(BaseModel):
    search: Optional[str] = Field(None, min_length=2)
    connector_type: Optional[ConnectorType] = None
    is_active: Optional[bool] = None


class JobFilters(BaseModel):
    search: Optional[str] = Field(None, min_length=2)
    exchange_type: Optional[ExchangeType] = None
    status: Optional[List[ExchangeStatus]] = None
    profile_id: Optional[UUID] = None
    triggered_by: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class HistoryFilters(BaseModel):
    exchange_type: Optional[ExchangeType] = None
    entity_type: Optional[str] = None
    status: Optional[ExchangeStatus] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


# ============== Common ==============

class AutocompleteItem(BaseModel):
    id: str
    code: str
    name: str
    label: str


class AutocompleteResponse(BaseModel):
    items: List[AutocompleteItem]
