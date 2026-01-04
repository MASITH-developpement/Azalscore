"""
AZALS MODULE T2 - Schémas Déclencheurs & Diffusion
===================================================

Schémas Pydantic pour validation et sérialisation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, EmailStr, field_validator
import json

from .models import (
    TriggerType, TriggerStatus, ConditionOperator, AlertSeverity,
    NotificationChannel, NotificationStatus, ReportFrequency, EscalationLevel
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
    and_: Optional[List['ConditionUnion']] = Field(None, alias='and')
    or_: Optional[List['ConditionUnion']] = Field(None, alias='or')
    not_: Optional['ConditionUnion'] = Field(None, alias='not')

    # Condition simple
    field: Optional[str] = None
    operator: Optional[ConditionOperator] = None
    value: Optional[Any] = None

    class Config:
        populate_by_name = True


ConditionUnion = Union[ConditionSchema, CompositeConditionSchema]


# ============================================================================
# TRIGGERS - SCHEMAS
# ============================================================================

class TriggerCreateSchema(BaseModel):
    """Création d'un trigger."""
    code: str = Field(..., min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

    trigger_type: TriggerType
    source_module: str = Field(..., min_length=2, max_length=50)
    source_entity: Optional[str] = Field(None, max_length=100)
    source_field: Optional[str] = Field(None, max_length=100)

    condition: Dict[str, Any] = Field(..., description="Condition JSON")

    threshold_value: Optional[str] = Field(None, max_length=255)
    threshold_operator: Optional[ConditionOperator] = None

    schedule_cron: Optional[str] = Field(None, max_length=100)
    schedule_timezone: str = Field(default='Europe/Paris', max_length=50)

    severity: AlertSeverity = Field(default=AlertSeverity.WARNING)
    escalation_enabled: bool = Field(default=False)
    escalation_delay_minutes: int = Field(default=60, ge=1, le=10080)

    cooldown_minutes: int = Field(default=60, ge=1, le=10080)
    action_template_id: Optional[int] = None

    @field_validator('condition')
    @classmethod
    def validate_condition(cls, v):
        if not v:
            raise ValueError("La condition ne peut pas être vide")
        return v


class TriggerUpdateSchema(BaseModel):
    """Mise à jour d'un trigger."""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

    trigger_type: Optional[TriggerType] = None
    source_module: Optional[str] = Field(None, min_length=2, max_length=50)
    source_entity: Optional[str] = Field(None, max_length=100)
    source_field: Optional[str] = Field(None, max_length=100)

    condition: Optional[Dict[str, Any]] = None

    threshold_value: Optional[str] = Field(None, max_length=255)
    threshold_operator: Optional[ConditionOperator] = None

    schedule_cron: Optional[str] = Field(None, max_length=100)
    schedule_timezone: Optional[str] = Field(None, max_length=50)

    severity: Optional[AlertSeverity] = None
    escalation_enabled: Optional[bool] = None
    escalation_delay_minutes: Optional[int] = Field(None, ge=1, le=10080)

    cooldown_minutes: Optional[int] = Field(None, ge=1, le=10080)
    action_template_id: Optional[int] = None

    is_active: Optional[bool] = None


class TriggerResponseSchema(BaseModel):
    """Réponse pour un trigger."""
    id: int
    tenant_id: str
    code: str
    name: str
    description: Optional[str]

    trigger_type: TriggerType
    status: TriggerStatus

    source_module: str
    source_entity: Optional[str]
    source_field: Optional[str]

    condition: Dict[str, Any]

    threshold_value: Optional[str]
    threshold_operator: Optional[ConditionOperator]

    schedule_cron: Optional[str]
    schedule_timezone: Optional[str]

    severity: AlertSeverity
    escalation_enabled: bool
    escalation_delay_minutes: Optional[int]
    escalation_level: Optional[EscalationLevel]

    cooldown_minutes: int
    is_active: bool

    last_triggered_at: Optional[datetime]
    trigger_count: int

    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]

    @field_validator('condition', mode='before')
    @classmethod
    def parse_condition(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    class Config:
        from_attributes = True


class TriggerListResponseSchema(BaseModel):
    """Liste de triggers."""
    triggers: List[TriggerResponseSchema]
    total: int


# ============================================================================
# SUBSCRIPTIONS - SCHEMAS
# ============================================================================

class SubscriptionCreateSchema(BaseModel):
    """Création d'un abonnement."""
    trigger_id: int

    user_id: Optional[int] = None
    role_code: Optional[str] = Field(None, max_length=50)
    group_code: Optional[str] = Field(None, max_length=50)
    email_external: Optional[EmailStr] = None

    channel: NotificationChannel = Field(default=NotificationChannel.IN_APP)
    channel_config: Optional[Dict[str, Any]] = None

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

    user_id: Optional[int]
    role_code: Optional[str]
    group_code: Optional[str]
    email_external: Optional[str]

    channel: NotificationChannel
    channel_config: Optional[Dict[str, Any]]

    escalation_level: EscalationLevel
    is_active: bool

    created_at: datetime
    created_by: Optional[int]

    @field_validator('channel_config', mode='before')
    @classmethod
    def parse_channel_config(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    class Config:
        from_attributes = True


# ============================================================================
# EVENTS - SCHEMAS
# ============================================================================

class EventResponseSchema(BaseModel):
    """Réponse pour un événement."""
    id: int
    tenant_id: str
    trigger_id: int

    triggered_at: datetime
    triggered_value: Optional[str]
    condition_details: Optional[Dict[str, Any]]

    severity: AlertSeverity
    escalation_level: EscalationLevel
    escalated_at: Optional[datetime]

    resolved: bool
    resolved_at: Optional[datetime]
    resolved_by: Optional[int]
    resolution_notes: Optional[str]

    @field_validator('condition_details', mode='before')
    @classmethod
    def parse_condition_details(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    class Config:
        from_attributes = True


class EventListResponseSchema(BaseModel):
    """Liste d'événements."""
    events: List[EventResponseSchema]
    total: int


class ResolveEventSchema(BaseModel):
    """Résolution d'un événement."""
    resolution_notes: Optional[str] = Field(None, max_length=2000)


class FireTriggerSchema(BaseModel):
    """Déclenchement manuel d'un trigger."""
    triggered_value: Optional[str] = None
    condition_details: Optional[Dict[str, Any]] = None


# ============================================================================
# NOTIFICATIONS - SCHEMAS
# ============================================================================

class NotificationResponseSchema(BaseModel):
    """Réponse pour une notification."""
    id: int
    tenant_id: str
    event_id: int

    user_id: Optional[int]
    email: Optional[str]

    channel: NotificationChannel
    subject: Optional[str]
    body: str

    status: NotificationStatus

    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    failed_at: Optional[datetime]
    failure_reason: Optional[str]

    retry_count: int
    next_retry_at: Optional[datetime]

    class Config:
        from_attributes = True


class NotificationListResponseSchema(BaseModel):
    """Liste de notifications."""
    notifications: List[NotificationResponseSchema]
    total: int
    unread_count: int


# ============================================================================
# TEMPLATES - SCHEMAS
# ============================================================================

class TemplateCreateSchema(BaseModel):
    """Création d'un template."""
    code: str = Field(..., min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

    subject_template: Optional[str] = Field(None, max_length=500)
    body_template: str = Field(..., min_length=1)
    body_html: Optional[str] = None

    available_variables: Optional[List[str]] = None


class TemplateUpdateSchema(BaseModel):
    """Mise à jour d'un template."""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

    subject_template: Optional[str] = Field(None, max_length=500)
    body_template: Optional[str] = Field(None, min_length=1)
    body_html: Optional[str] = None

    available_variables: Optional[List[str]] = None
    is_active: Optional[bool] = None


class TemplateResponseSchema(BaseModel):
    """Réponse pour un template."""
    id: int
    tenant_id: str
    code: str
    name: str
    description: Optional[str]

    subject_template: Optional[str]
    body_template: str
    body_html: Optional[str]

    available_variables: Optional[List[str]]

    is_active: bool
    is_system: bool

    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]

    @field_validator('available_variables', mode='before')
    @classmethod
    def parse_variables(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    class Config:
        from_attributes = True


# ============================================================================
# SCHEDULED REPORTS - SCHEMAS
# ============================================================================

class RecipientsSchema(BaseModel):
    """Configuration des destinataires."""
    users: Optional[List[int]] = None
    roles: Optional[List[str]] = None
    emails: Optional[List[EmailStr]] = None


class ScheduledReportCreateSchema(BaseModel):
    """Création d'un rapport planifié."""
    code: str = Field(..., min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

    report_type: str = Field(..., min_length=2, max_length=50)
    report_config: Optional[Dict[str, Any]] = None

    frequency: ReportFrequency
    schedule_day: Optional[int] = Field(None, ge=1, le=31)
    schedule_time: Optional[str] = Field(None, pattern=r'^[0-2][0-9]:[0-5][0-9]$')
    schedule_timezone: str = Field(default='Europe/Paris', max_length=50)
    schedule_cron: Optional[str] = Field(None, max_length=100)

    recipients: RecipientsSchema
    output_format: str = Field(default='PDF', pattern=r'^(PDF|EXCEL|HTML)$')


class ScheduledReportUpdateSchema(BaseModel):
    """Mise à jour d'un rapport planifié."""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

    report_config: Optional[Dict[str, Any]] = None

    frequency: Optional[ReportFrequency] = None
    schedule_day: Optional[int] = Field(None, ge=1, le=31)
    schedule_time: Optional[str] = Field(None, pattern=r'^[0-2][0-9]:[0-5][0-9]$')
    schedule_timezone: Optional[str] = Field(None, max_length=50)

    recipients: Optional[RecipientsSchema] = None
    output_format: Optional[str] = Field(None, pattern=r'^(PDF|EXCEL|HTML)$')

    is_active: Optional[bool] = None


class ScheduledReportResponseSchema(BaseModel):
    """Réponse pour un rapport planifié."""
    id: int
    tenant_id: str
    code: str
    name: str
    description: Optional[str]

    report_type: str
    report_config: Optional[Dict[str, Any]]

    frequency: ReportFrequency
    schedule_day: Optional[int]
    schedule_time: Optional[str]
    schedule_timezone: str
    schedule_cron: Optional[str]

    recipients: Dict[str, Any]
    output_format: str

    is_active: bool

    last_generated_at: Optional[datetime]
    next_generation_at: Optional[datetime]
    generation_count: int

    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]

    @field_validator('report_config', 'recipients', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    class Config:
        from_attributes = True


class ReportHistoryResponseSchema(BaseModel):
    """Réponse pour l'historique d'un rapport."""
    id: int
    tenant_id: str
    report_id: int

    generated_at: datetime
    generated_by: Optional[int]

    file_name: str
    file_path: Optional[str]
    file_size: Optional[int]
    file_format: str

    sent_to: Optional[Dict[str, Any]]
    sent_at: Optional[datetime]

    success: bool
    error_message: Optional[str]

    @field_validator('sent_to', mode='before')
    @classmethod
    def parse_sent_to(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    class Config:
        from_attributes = True


# ============================================================================
# WEBHOOKS - SCHEMAS
# ============================================================================

class WebhookCreateSchema(BaseModel):
    """Création d'un webhook."""
    code: str = Field(..., min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

    url: str = Field(..., min_length=10, max_length=500)
    method: str = Field(default='POST', pattern=r'^(POST|PUT)$')
    headers: Optional[Dict[str, str]] = None

    auth_type: Optional[str] = Field(None, pattern=r'^(none|basic|bearer|api_key)$')
    auth_config: Optional[Dict[str, str]] = None

    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: int = Field(default=60, ge=10, le=3600)


class WebhookUpdateSchema(BaseModel):
    """Mise à jour d'un webhook."""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

    url: Optional[str] = Field(None, min_length=10, max_length=500)
    method: Optional[str] = Field(None, pattern=r'^(POST|PUT)$')
    headers: Optional[Dict[str, str]] = None

    auth_type: Optional[str] = Field(None, pattern=r'^(none|basic|bearer|api_key)$')
    auth_config: Optional[Dict[str, str]] = None

    max_retries: Optional[int] = Field(None, ge=0, le=10)
    retry_delay_seconds: Optional[int] = Field(None, ge=10, le=3600)

    is_active: Optional[bool] = None


class WebhookResponseSchema(BaseModel):
    """Réponse pour un webhook."""
    id: int
    tenant_id: str
    code: str
    name: str
    description: Optional[str]

    url: str
    method: str
    headers: Optional[Dict[str, str]]

    auth_type: Optional[str]
    # auth_config omis pour sécurité

    max_retries: int
    retry_delay_seconds: int

    is_active: bool
    last_success_at: Optional[datetime]
    last_failure_at: Optional[datetime]
    consecutive_failures: int

    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]

    @field_validator('headers', mode='before')
    @classmethod
    def parse_headers(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    class Config:
        from_attributes = True


class WebhookTestResponseSchema(BaseModel):
    """Réponse test d'un webhook."""
    success: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error: Optional[str] = None


# ============================================================================
# LOGS - SCHEMAS
# ============================================================================

class TriggerLogResponseSchema(BaseModel):
    """Réponse pour un log."""
    id: int
    tenant_id: str
    action: str
    entity_type: str
    entity_id: Optional[int]
    details: Optional[Dict[str, Any]]
    success: bool
    error_message: Optional[str]
    created_at: datetime

    @field_validator('details', mode='before')
    @classmethod
    def parse_details(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    class Config:
        from_attributes = True


class TriggerLogListResponseSchema(BaseModel):
    """Liste de logs."""
    logs: List[TriggerLogResponseSchema]
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
    recent_events: List[EventResponseSchema]
    upcoming_reports: List[ScheduledReportResponseSchema]
