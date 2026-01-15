"""
AZALS MODULE T6 - Schémas Pydantic Diffusion Périodique
=======================================================

Schémas de validation pour les API du module Broadcast.
"""


import json
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ============================================================================
# ENUMS
# ============================================================================

class DeliveryChannelEnum(str, Enum):
    EMAIL = "EMAIL"
    IN_APP = "IN_APP"
    WEBHOOK = "WEBHOOK"
    PDF_DOWNLOAD = "PDF_DOWNLOAD"
    SMS = "SMS"


class BroadcastFrequencyEnum(str, Enum):
    ONCE = "ONCE"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    BIWEEKLY = "BIWEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"
    CUSTOM = "CUSTOM"


class ContentTypeEnum(str, Enum):
    DIGEST = "DIGEST"
    NEWSLETTER = "NEWSLETTER"
    REPORT = "REPORT"
    ALERT = "ALERT"
    KPI_SUMMARY = "KPI_SUMMARY"


class BroadcastStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"


class DeliveryStatusEnum(str, Enum):
    PENDING = "PENDING"
    SENDING = "SENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    BOUNCED = "BOUNCED"
    OPENED = "OPENED"
    CLICKED = "CLICKED"


class RecipientTypeEnum(str, Enum):
    USER = "USER"
    GROUP = "GROUP"
    ROLE = "ROLE"
    EXTERNAL = "EXTERNAL"
    DYNAMIC = "DYNAMIC"


# ============================================================================
# TEMPLATES
# ============================================================================

class BroadcastTemplateBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    content_type: ContentTypeEnum
    subject_template: str | None = None
    body_template: str | None = None
    html_template: str | None = None
    default_channel: DeliveryChannelEnum = DeliveryChannelEnum.EMAIL
    available_channels: list[str] | None = None
    variables: dict[str, Any] | None = None
    styling: dict[str, Any] | None = None
    data_sources: list[dict[str, Any]] | None = None
    language: str = "fr"


class BroadcastTemplateCreate(BroadcastTemplateBase):
    pass


class BroadcastTemplateUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    subject_template: str | None = None
    body_template: str | None = None
    html_template: str | None = None
    default_channel: DeliveryChannelEnum | None = None
    available_channels: list[str] | None = None
    variables: dict[str, Any] | None = None
    styling: dict[str, Any] | None = None
    data_sources: list[dict[str, Any]] | None = None
    language: str | None = None
    is_active: bool | None = None


class BroadcastTemplateResponse(BroadcastTemplateBase):
    id: int
    is_active: bool
    is_system: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("available_channels", "variables", "styling", "data_sources", mode="before")
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return v
        return v


# ============================================================================
# LISTES DE DESTINATAIRES
# ============================================================================

class RecipientListBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    is_dynamic: bool = False
    query_config: dict[str, Any] | None = None


class RecipientListCreate(RecipientListBase):
    pass


class RecipientListUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    query_config: dict[str, Any] | None = None
    is_active: bool | None = None


class RecipientListResponse(RecipientListBase):
    id: int
    total_recipients: int
    active_recipients: int
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("query_config", mode="before")
    @classmethod
    def parse_query_config(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v


# ============================================================================
# MEMBRES DE LISTE
# ============================================================================

class RecipientMemberCreate(BaseModel):
    recipient_type: RecipientTypeEnum
    user_id: int | None = None
    group_id: int | None = None
    role_code: str | None = None
    external_email: str | None = None
    external_name: str | None = None
    preferred_channel: DeliveryChannelEnum | None = None
    preferred_language: str | None = None


class RecipientMemberResponse(BaseModel):
    id: int
    list_id: int
    recipient_type: RecipientTypeEnum
    user_id: int | None = None
    group_id: int | None = None
    role_code: str | None = None
    external_email: str | None = None
    external_name: str | None = None
    preferred_channel: DeliveryChannelEnum | None = None
    is_active: bool
    is_unsubscribed: bool
    added_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# DIFFUSIONS PROGRAMMÉES
# ============================================================================

class ScheduledBroadcastBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    content_type: ContentTypeEnum
    frequency: BroadcastFrequencyEnum
    delivery_channel: DeliveryChannelEnum = DeliveryChannelEnum.EMAIL


class ScheduledBroadcastCreate(ScheduledBroadcastBase):
    template_id: int | None = None
    recipient_list_id: int | None = None
    subject: str | None = None
    body_content: str | None = None
    html_content: str | None = None
    cron_expression: str | None = None
    timezone: str = "Europe/Paris"
    start_date: datetime.datetime | None = None
    end_date: datetime.datetime | None = None
    send_time: str | None = None
    day_of_week: int | None = Field(None, ge=0, le=6)
    day_of_month: int | None = Field(None, ge=1, le=31)
    data_query: dict[str, Any] | None = None


class ScheduledBroadcastUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    template_id: int | None = None
    recipient_list_id: int | None = None
    subject: str | None = None
    body_content: str | None = None
    html_content: str | None = None
    delivery_channel: DeliveryChannelEnum | None = None
    frequency: BroadcastFrequencyEnum | None = None
    cron_expression: str | None = None
    timezone: str | None = None
    start_date: datetime.datetime | None = None
    end_date: datetime.datetime | None = None
    send_time: str | None = None
    day_of_week: int | None = Field(None, ge=0, le=6)
    day_of_month: int | None = Field(None, ge=1, le=31)
    data_query: dict[str, Any] | None = None


class ScheduledBroadcastResponse(ScheduledBroadcastBase):
    id: int
    template_id: int | None = None
    recipient_list_id: int | None = None
    subject: str | None = None
    cron_expression: str | None = None
    timezone: str
    start_date: datetime.datetime | None = None
    end_date: datetime.datetime | None = None
    send_time: str | None = None
    day_of_week: int | None = None
    day_of_month: int | None = None
    data_query: dict[str, Any] | None = None
    status: BroadcastStatusEnum
    is_active: bool
    total_sent: int
    total_delivered: int
    total_failed: int
    total_opened: int
    last_run_at: datetime.datetime | None = None
    next_run_at: datetime.datetime | None = None
    last_error: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("data_query", mode="before")
    @classmethod
    def parse_data_query(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v


# ============================================================================
# EXÉCUTIONS
# ============================================================================

class BroadcastExecutionResponse(BaseModel):
    id: int
    scheduled_broadcast_id: int
    execution_number: int
    started_at: datetime.datetime
    completed_at: datetime.datetime | None = None
    duration_seconds: float | None = None
    status: DeliveryStatusEnum
    total_recipients: int
    sent_count: int
    delivered_count: int
    failed_count: int
    bounced_count: int
    opened_count: int
    clicked_count: int
    error_message: str | None = None
    triggered_by: str
    triggered_user: int | None = None

    model_config = ConfigDict(from_attributes=True)


class ExecuteRequest(BaseModel):
    triggered_by: str = "manual"


# ============================================================================
# DÉTAILS DE LIVRAISON
# ============================================================================

class DeliveryDetailResponse(BaseModel):
    id: int
    execution_id: int
    recipient_type: RecipientTypeEnum
    user_id: int | None = None
    email: str | None = None
    channel: DeliveryChannelEnum
    status: DeliveryStatusEnum
    queued_at: datetime.datetime
    sent_at: datetime.datetime | None = None
    delivered_at: datetime.datetime | None = None
    opened_at: datetime.datetime | None = None
    clicked_at: datetime.datetime | None = None
    error_code: str | None = None
    error_message: str | None = None
    retry_count: int
    tracking_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PRÉFÉRENCES
# ============================================================================

class BroadcastPreferenceCreate(BaseModel):
    receive_digests: bool = True
    receive_newsletters: bool = True
    receive_reports: bool = True
    receive_alerts: bool = True
    preferred_channel: DeliveryChannelEnum = DeliveryChannelEnum.EMAIL
    preferred_language: str = "fr"
    preferred_format: str = "HTML"
    digest_frequency: BroadcastFrequencyEnum = BroadcastFrequencyEnum.DAILY
    report_frequency: BroadcastFrequencyEnum = BroadcastFrequencyEnum.WEEKLY
    preferred_send_time: str | None = None
    timezone: str = "Europe/Paris"


class BroadcastPreferenceResponse(BaseModel):
    id: int
    user_id: int
    receive_digests: bool
    receive_newsletters: bool
    receive_reports: bool
    receive_alerts: bool
    preferred_channel: DeliveryChannelEnum
    preferred_language: str
    preferred_format: str
    digest_frequency: BroadcastFrequencyEnum
    report_frequency: BroadcastFrequencyEnum
    preferred_send_time: str | None = None
    timezone: str
    is_unsubscribed_all: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class UnsubscribeRequest(BaseModel):
    broadcast_id: int | None = None  # None = unsubscribe all


# ============================================================================
# MÉTRIQUES
# ============================================================================

class BroadcastMetricResponse(BaseModel):
    id: int
    metric_date: datetime.datetime
    period_type: str
    total_broadcasts: int
    total_executions: int
    total_messages: int
    delivered_count: int
    failed_count: int
    bounced_count: int
    delivery_rate: float | None = None
    opened_count: int
    clicked_count: int
    open_rate: float | None = None
    click_rate: float | None = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardStatsResponse(BaseModel):
    total_broadcasts: int
    active_broadcasts: int
    executions_this_week: int
    messages_sent_this_week: int
    delivery_rate: float
    open_rate: float
    upcoming_broadcasts: list[dict[str, Any]]


# ============================================================================
# LISTES PAGINÉES
# ============================================================================

class PaginatedTemplatesResponse(BaseModel):
    items: list[BroadcastTemplateResponse]
    total: int
    skip: int
    limit: int


class PaginatedRecipientListsResponse(BaseModel):
    items: list[RecipientListResponse]
    total: int
    skip: int
    limit: int


class PaginatedMembersResponse(BaseModel):
    items: list[RecipientMemberResponse]
    total: int
    skip: int
    limit: int


class PaginatedBroadcastsResponse(BaseModel):
    items: list[ScheduledBroadcastResponse]
    total: int
    skip: int
    limit: int


class PaginatedExecutionsResponse(BaseModel):
    items: list[BroadcastExecutionResponse]
    total: int
    skip: int
    limit: int


class PaginatedDeliveryDetailsResponse(BaseModel):
    items: list[DeliveryDetailResponse]
    total: int
    skip: int
    limit: int
