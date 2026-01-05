"""
AZALS MODULE T6 - Schémas Pydantic Diffusion Périodique
=======================================================

Schémas de validation pour les API du module Broadcast.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict
import json


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
    description: Optional[str] = None
    content_type: ContentTypeEnum
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    html_template: Optional[str] = None
    default_channel: DeliveryChannelEnum = DeliveryChannelEnum.EMAIL
    available_channels: Optional[List[str]] = None
    variables: Optional[Dict[str, Any]] = None
    styling: Optional[Dict[str, Any]] = None
    data_sources: Optional[List[Dict[str, Any]]] = None
    language: str = "fr"


class BroadcastTemplateCreate(BroadcastTemplateBase):
    pass


class BroadcastTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    html_template: Optional[str] = None
    default_channel: Optional[DeliveryChannelEnum] = None
    available_channels: Optional[List[str]] = None
    variables: Optional[Dict[str, Any]] = None
    styling: Optional[Dict[str, Any]] = None
    data_sources: Optional[List[Dict[str, Any]]] = None
    language: Optional[str] = None
    is_active: Optional[bool] = None


class BroadcastTemplateResponse(BroadcastTemplateBase):
    id: int
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

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
    description: Optional[str] = None
    is_dynamic: bool = False
    query_config: Optional[Dict[str, Any]] = None


class RecipientListCreate(RecipientListBase):
    pass


class RecipientListUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    query_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class RecipientListResponse(RecipientListBase):
    id: int
    total_recipients: int
    active_recipients: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

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
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    role_code: Optional[str] = None
    external_email: Optional[str] = None
    external_name: Optional[str] = None
    preferred_channel: Optional[DeliveryChannelEnum] = None
    preferred_language: Optional[str] = None


class RecipientMemberResponse(BaseModel):
    id: int
    list_id: int
    recipient_type: RecipientTypeEnum
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    role_code: Optional[str] = None
    external_email: Optional[str] = None
    external_name: Optional[str] = None
    preferred_channel: Optional[DeliveryChannelEnum] = None
    is_active: bool
    is_unsubscribed: bool
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# DIFFUSIONS PROGRAMMÉES
# ============================================================================

class ScheduledBroadcastBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    content_type: ContentTypeEnum
    frequency: BroadcastFrequencyEnum
    delivery_channel: DeliveryChannelEnum = DeliveryChannelEnum.EMAIL


class ScheduledBroadcastCreate(ScheduledBroadcastBase):
    template_id: Optional[int] = None
    recipient_list_id: Optional[int] = None
    subject: Optional[str] = None
    body_content: Optional[str] = None
    html_content: Optional[str] = None
    cron_expression: Optional[str] = None
    timezone: str = "Europe/Paris"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    send_time: Optional[str] = None
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    data_query: Optional[Dict[str, Any]] = None


class ScheduledBroadcastUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    template_id: Optional[int] = None
    recipient_list_id: Optional[int] = None
    subject: Optional[str] = None
    body_content: Optional[str] = None
    html_content: Optional[str] = None
    delivery_channel: Optional[DeliveryChannelEnum] = None
    frequency: Optional[BroadcastFrequencyEnum] = None
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    send_time: Optional[str] = None
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    data_query: Optional[Dict[str, Any]] = None


class ScheduledBroadcastResponse(ScheduledBroadcastBase):
    id: int
    template_id: Optional[int] = None
    recipient_list_id: Optional[int] = None
    subject: Optional[str] = None
    cron_expression: Optional[str] = None
    timezone: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    send_time: Optional[str] = None
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    data_query: Optional[Dict[str, Any]] = None
    status: BroadcastStatusEnum
    is_active: bool
    total_sent: int
    total_delivered: int
    total_failed: int
    total_opened: int
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

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
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    status: DeliveryStatusEnum
    total_recipients: int
    sent_count: int
    delivered_count: int
    failed_count: int
    bounced_count: int
    opened_count: int
    clicked_count: int
    error_message: Optional[str] = None
    triggered_by: str
    triggered_user: Optional[int] = None

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
    user_id: Optional[int] = None
    email: Optional[str] = None
    channel: DeliveryChannelEnum
    status: DeliveryStatusEnum
    queued_at: datetime
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int
    tracking_id: Optional[str] = None

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
    preferred_send_time: Optional[str] = None
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
    preferred_send_time: Optional[str] = None
    timezone: str
    is_unsubscribed_all: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UnsubscribeRequest(BaseModel):
    broadcast_id: Optional[int] = None  # None = unsubscribe all


# ============================================================================
# MÉTRIQUES
# ============================================================================

class BroadcastMetricResponse(BaseModel):
    id: int
    metric_date: datetime
    period_type: str
    total_broadcasts: int
    total_executions: int
    total_messages: int
    delivered_count: int
    failed_count: int
    bounced_count: int
    delivery_rate: Optional[float] = None
    opened_count: int
    clicked_count: int
    open_rate: Optional[float] = None
    click_rate: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardStatsResponse(BaseModel):
    total_broadcasts: int
    active_broadcasts: int
    executions_this_week: int
    messages_sent_this_week: int
    delivery_rate: float
    open_rate: float
    upcoming_broadcasts: List[Dict[str, Any]]


# ============================================================================
# LISTES PAGINÉES
# ============================================================================

class PaginatedTemplatesResponse(BaseModel):
    items: List[BroadcastTemplateResponse]
    total: int
    skip: int
    limit: int


class PaginatedRecipientListsResponse(BaseModel):
    items: List[RecipientListResponse]
    total: int
    skip: int
    limit: int


class PaginatedMembersResponse(BaseModel):
    items: List[RecipientMemberResponse]
    total: int
    skip: int
    limit: int


class PaginatedBroadcastsResponse(BaseModel):
    items: List[ScheduledBroadcastResponse]
    total: int
    skip: int
    limit: int


class PaginatedExecutionsResponse(BaseModel):
    items: List[BroadcastExecutionResponse]
    total: int
    skip: int
    limit: int


class PaginatedDeliveryDetailsResponse(BaseModel):
    items: List[DeliveryDetailResponse]
    total: int
    skip: int
    limit: int
