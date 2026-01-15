"""
AZALS MODULE T2 - Schémas Déclencheurs & Diffusion
===================================================

Schémas Pydantic pour validation et sérialisation.
"""


import json
from datetime import datetime
from typing import Any, Union

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .models import (
    AlertSeverity,
    ConditionOperator,
    EscalationLevel,
    NotificationChannel,
    NotificationStatus,
    ReportFrequency,
    TriggerStatus,
    TriggerType,
)

# ============================================================================
# SCHEMAS DE BASE
# ============================================================================

class ConditionSchema(BaseModel):
    """Condition simple."""
    field: str = Field(..., min_length=1, description="Champ à évaluer")
    operator: ConditionOperator = Field(..., description="Opérateur de comparaison")
    value: Any = Field(..., description="Valeur de comparaison")


class CompositeConditionSchema(BaseModel):
    """Condition composite (AND/OR/NOT)."""
    and_: list[ConditionUnion] | None = Field(None, alias='and')
    or_: list[ConditionUnion] | None = Field(None, alias='or')
    not_: ConditionUnion | None = Field(None, alias='not')

    # Condition simple
    field: str | None = None
    operator: ConditionOperator | None = None
    value: Any | None = None

    model_config = ConfigDict(populate_by_name=True)


ConditionUnion = Union[ConditionSchema, CompositeConditionSchema]


# ============================================================================
# TRIGGERS - SCHEMAS
# ============================================================================

class TriggerCreateSchema(BaseModel):
    """Création d'un trigger."""
    code: str = Field(..., min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = Field(None, max_length=2000)

    trigger_type: TriggerType
    source_module: str = Field(..., min_length=2, max_length=50)
    source_entity: str | None = Field(None, max_length=100)
    source_field: str | None = Field(None, max_length=100)

    condition: dict[str, Any] = Field(..., description="Condition JSON")

    threshold_value: str | None = Field(None, max_length=255)
    threshold_operator: ConditionOperator | None = None

    schedule_cron: str | None = Field(None, max_length=100)
    schedule_timezone: str = Field(default='Europe/Paris', max_length=50)

    severity: AlertSeverity = Field(default=AlertSeverity.WARNING)
    escalation_enabled: bool = Field(default=False)
    escalation_delay_minutes: int = Field(default=60, ge=1, le=10080)

    cooldown_minutes: int = Field(default=60, ge=1, le=10080)
    action_template_id: int | None = None

    @field_validator('condition')
    @classmethod
    def validate_condition(cls, v):
        if not v:
            raise ValueError("La condition ne peut pas être vide")
        return v


class TriggerUpdateSchema(BaseModel):
    """Mise à jour d'un trigger."""
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = Field(None, max_length=2000)

    trigger_type: TriggerType | None = None
    source_module: str | None = Field(None, min_length=2, max_length=50)
    source_entity: str | None = Field(None, max_length=100)
    source_field: str | None = Field(None, max_length=100)

    condition: dict[str, Any] | None = None

    threshold_value: str | None = Field(None, max_length=255)
    threshold_operator: ConditionOperator | None = None

    schedule_cron: str | None = Field(None, max_length=100)
    schedule_timezone: str | None = Field(None, max_length=50)

    severity: AlertSeverity | None = None
    escalation_enabled: bool | None = None
    escalation_delay_minutes: int | None = Field(None, ge=1, le=10080)

    cooldown_minutes: int | None = Field(None, ge=1, le=10080)
    action_template_id: int | None = None

    is_active: bool | None = None


class TriggerResponseSchema(BaseModel):
    """Réponse pour un trigger."""
    id: int
    tenant_id: str
    code: str
    name: str
    description: str | None

    trigger_type: TriggerType
    status: TriggerStatus

    source_module: str
    source_entity: str | None
    source_field: str | None

    condition: dict[str, Any]

    threshold_value: str | None
    threshold_operator: ConditionOperator | None

    schedule_cron: str | None
    schedule_timezone: str | None

    severity: AlertSeverity
    escalation_enabled: bool
    escalation_delay_minutes: int | None
    escalation_level: EscalationLevel | None

    cooldown_minutes: int
    is_active: bool

    last_triggered_at: datetime | None
    trigger_count: int

    created_at: datetime
    updated_at: datetime
    created_by: int | None

    @field_validator('condition', mode='before')
    @classmethod
    def parse_condition(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = ConfigDict(from_attributes=True)


class TriggerListResponseSchema(BaseModel):
    """Liste de triggers."""
    triggers: list[TriggerResponseSchema]
    total: int


# ============================================================================
# SUBSCRIPTIONS - SCHEMAS
# ============================================================================

class SubscriptionCreateSchema(BaseModel):
    """Création d'un abonnement."""
    trigger_id: int

    user_id: int | None = None
    role_code: str | None = Field(None, max_length=50)
    group_code: str | None = Field(None, max_length=50)
    email_external: EmailStr | None = None

    channel: NotificationChannel = Field(default=NotificationChannel.IN_APP)
    channel_config: dict[str, Any] | None = None

    escalation_level: EscalationLevel = Field(default=EscalationLevel.L1)

    @field_validator('email_external', 'user_id', 'role_code', 'group_code')
    @classmethod
    def validate_at_least_one_target(cls, v, info):
        return v


class SubscriptionResponseSchema(BaseModel):
    """Réponse pour un abonnement."""
    id: int
    tenant_id: str
    trigger_id: int

    user_id: int | None
    role_code: str | None
    group_code: str | None
    email_external: str | None

    channel: NotificationChannel
    channel_config: dict[str, Any] | None

    escalation_level: EscalationLevel
    is_active: bool

    created_at: datetime
    created_by: int | None

    @field_validator('channel_config', mode='before')
    @classmethod
    def parse_channel_config(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# EVENTS - SCHEMAS
# ============================================================================

class EventResponseSchema(BaseModel):
    """Réponse pour un événement."""
    id: int
    tenant_id: str
    trigger_id: int

    triggered_at: datetime
    triggered_value: str | None
    condition_details: dict[str, Any] | None

    severity: AlertSeverity
    escalation_level: EscalationLevel
    escalated_at: datetime | None

    resolved: bool
    resolved_at: datetime | None
    resolved_by: int | None
    resolution_notes: str | None

    @field_validator('condition_details', mode='before')
    @classmethod
    def parse_condition_details(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = ConfigDict(from_attributes=True)


class EventListResponseSchema(BaseModel):
    """Liste d'événements."""
    events: list[EventResponseSchema]
    total: int


class ResolveEventSchema(BaseModel):
    """Résolution d'un événement."""
    resolution_notes: str | None = Field(None, max_length=2000)


class FireTriggerSchema(BaseModel):
    """Déclenchement manuel d'un trigger."""
    triggered_value: str | None = None
    condition_details: dict[str, Any] | None = None


# ============================================================================
# NOTIFICATIONS - SCHEMAS
# ============================================================================

class NotificationResponseSchema(BaseModel):
    """Réponse pour une notification."""
    id: int
    tenant_id: str
    event_id: int

    user_id: int | None
    email: str | None

    channel: NotificationChannel
    subject: str | None
    body: str

    status: NotificationStatus

    sent_at: datetime | None
    delivered_at: datetime | None
    read_at: datetime | None
    failed_at: datetime | None
    failure_reason: str | None

    retry_count: int
    next_retry_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponseSchema(BaseModel):
    """Liste de notifications."""
    notifications: list[NotificationResponseSchema]
    total: int
    unread_count: int


# ============================================================================
# TEMPLATES - SCHEMAS
# ============================================================================

class TemplateCreateSchema(BaseModel):
    """Création d'un template."""
    code: str = Field(..., min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = Field(None, max_length=2000)

    subject_template: str | None = Field(None, max_length=500)
    body_template: str = Field(..., min_length=1)
    body_html: str | None = None

    available_variables: list[str] | None = None


class TemplateUpdateSchema(BaseModel):
    """Mise à jour d'un template."""
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = Field(None, max_length=2000)

    subject_template: str | None = Field(None, max_length=500)
    body_template: str | None = Field(None, min_length=1)
    body_html: str | None = None

    available_variables: list[str] | None = None
    is_active: bool | None = None


class TemplateResponseSchema(BaseModel):
    """Réponse pour un template."""
    id: int
    tenant_id: str
    code: str
    name: str
    description: str | None

    subject_template: str | None
    body_template: str
    body_html: str | None

    available_variables: list[str] | None

    is_active: bool
    is_system: bool

    created_at: datetime
    updated_at: datetime
    created_by: int | None

    @field_validator('available_variables', mode='before')
    @classmethod
    def parse_variables(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHEDULED REPORTS - SCHEMAS
# ============================================================================

class RecipientsSchema(BaseModel):
    """Configuration des destinataires."""
    users: list[int] | None = None
    roles: list[str] | None = None
    emails: list[EmailStr] | None = None


class ScheduledReportCreateSchema(BaseModel):
    """Création d'un rapport planifié."""
    code: str = Field(..., min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = Field(None, max_length=2000)

    report_type: str = Field(..., min_length=2, max_length=50)
    report_config: dict[str, Any] | None = None

    frequency: ReportFrequency
    schedule_day: int | None = Field(None, ge=1, le=31)
    schedule_time: str | None = Field(None, pattern=r'^[0-2][0-9]:[0-5][0-9]$')
    schedule_timezone: str = Field(default='Europe/Paris', max_length=50)
    schedule_cron: str | None = Field(None, max_length=100)

    recipients: RecipientsSchema
    output_format: str = Field(default='PDF', pattern=r'^(PDF|EXCEL|HTML)$')


class ScheduledReportUpdateSchema(BaseModel):
    """Mise à jour d'un rapport planifié."""
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = Field(None, max_length=2000)

    report_config: dict[str, Any] | None = None

    frequency: ReportFrequency | None = None
    schedule_day: int | None = Field(None, ge=1, le=31)
    schedule_time: str | None = Field(None, pattern=r'^[0-2][0-9]:[0-5][0-9]$')
    schedule_timezone: str | None = Field(None, max_length=50)

    recipients: RecipientsSchema | None = None
    output_format: str | None = Field(None, pattern=r'^(PDF|EXCEL|HTML)$')

    is_active: bool | None = None


class ScheduledReportResponseSchema(BaseModel):
    """Réponse pour un rapport planifié."""
    id: int
    tenant_id: str
    code: str
    name: str
    description: str | None

    report_type: str
    report_config: dict[str, Any] | None

    frequency: ReportFrequency
    schedule_day: int | None
    schedule_time: str | None
    schedule_timezone: str
    schedule_cron: str | None

    recipients: dict[str, Any]
    output_format: str

    is_active: bool

    last_generated_at: datetime | None
    next_generation_at: datetime | None
    generation_count: int

    created_at: datetime
    updated_at: datetime
    created_by: int | None

    @field_validator('report_config', 'recipients', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = ConfigDict(from_attributes=True)


class ReportHistoryResponseSchema(BaseModel):
    """Réponse pour l'historique d'un rapport."""
    id: int
    tenant_id: str
    report_id: int

    generated_at: datetime
    generated_by: int | None

    file_name: str
    file_path: str | None
    file_size: int | None
    file_format: str

    sent_to: dict[str, Any] | None
    sent_at: datetime | None

    success: bool
    error_message: str | None

    @field_validator('sent_to', mode='before')
    @classmethod
    def parse_sent_to(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# WEBHOOKS - SCHEMAS
# ============================================================================

class WebhookCreateSchema(BaseModel):
    """Création d'un webhook."""
    code: str = Field(..., min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = Field(None, max_length=2000)

    url: str = Field(..., min_length=10, max_length=500)
    method: str = Field(default='POST', pattern=r'^(POST|PUT)$')
    headers: dict[str, str] | None = None

    auth_type: str | None = Field(None, pattern=r'^(none|basic|bearer|api_key)$')
    auth_config: dict[str, str] | None = None

    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: int = Field(default=60, ge=10, le=3600)


class WebhookUpdateSchema(BaseModel):
    """Mise à jour d'un webhook."""
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = Field(None, max_length=2000)

    url: str | None = Field(None, min_length=10, max_length=500)
    method: str | None = Field(None, pattern=r'^(POST|PUT)$')
    headers: dict[str, str] | None = None

    auth_type: str | None = Field(None, pattern=r'^(none|basic|bearer|api_key)$')
    auth_config: dict[str, str] | None = None

    max_retries: int | None = Field(None, ge=0, le=10)
    retry_delay_seconds: int | None = Field(None, ge=10, le=3600)

    is_active: bool | None = None


class WebhookResponseSchema(BaseModel):
    """Réponse pour un webhook."""
    id: int
    tenant_id: str
    code: str
    name: str
    description: str | None

    url: str
    method: str
    headers: dict[str, str] | None

    auth_type: str | None
    # auth_config omis pour sécurité

    max_retries: int
    retry_delay_seconds: int

    is_active: bool
    last_success_at: datetime | None
    last_failure_at: datetime | None
    consecutive_failures: int

    created_at: datetime
    updated_at: datetime
    created_by: int | None

    @field_validator('headers', mode='before')
    @classmethod
    def parse_headers(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = ConfigDict(from_attributes=True)


class WebhookTestResponseSchema(BaseModel):
    """Réponse test d'un webhook."""
    success: bool
    status_code: int | None = None
    response_time_ms: float | None = None
    error: str | None = None


# ============================================================================
# LOGS - SCHEMAS
# ============================================================================

class TriggerLogResponseSchema(BaseModel):
    """Réponse pour un log."""
    id: int
    tenant_id: str
    action: str
    entity_type: str
    entity_id: int | None
    details: dict[str, Any] | None
    success: bool
    error_message: str | None
    created_at: datetime

    @field_validator('details', mode='before')
    @classmethod
    def parse_details(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = ConfigDict(from_attributes=True)


class TriggerLogListResponseSchema(BaseModel):
    """Liste de logs."""
    logs: list[TriggerLogResponseSchema]
    total: int


# ============================================================================
# DASHBOARD - SCHEMAS
# ============================================================================

class TriggerStatsSchema(BaseModel):
    """Statistiques des triggers."""
    total_triggers: int
    active_triggers: int
    paused_triggers: int
    disabled_triggers: int

    total_events_24h: int
    unresolved_events: int
    critical_events: int

    total_notifications_24h: int
    pending_notifications: int
    failed_notifications: int

    scheduled_reports: int
    reports_generated_24h: int


class TriggerDashboardSchema(BaseModel):
    """Dashboard des triggers."""
    stats: TriggerStatsSchema
    recent_events: list[EventResponseSchema]
    upcoming_reports: list[ScheduledReportResponseSchema]
