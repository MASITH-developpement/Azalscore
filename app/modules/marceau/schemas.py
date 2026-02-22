"""
AZALS MODULE - Marceau Schemas
===============================

Schemas Pydantic pour validation des donnees Marceau.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# CONFIGURATION
# ============================================================================

class TelephonyConfigSchema(BaseModel):
    """Configuration telephonie."""
    asterisk_ami_host: str = "localhost"
    asterisk_ami_port: int = 5038
    asterisk_ami_username: str = ""
    asterisk_ami_password: str = ""
    working_hours: dict = Field(default={"start": "09:00", "end": "18:00"})
    overflow_threshold: int = 2
    overflow_number: str = ""
    appointment_duration_minutes: int = 60
    max_wait_days: int = 14
    use_travel_time: bool = True
    travel_buffer_minutes: int = 15


class IntegrationsConfigSchema(BaseModel):
    """Configuration integrations externes."""
    ors_api_key: str | None = None
    gmail_credentials: dict | None = None
    google_calendar_id: str | None = None
    linkedin_token: str | None = None
    facebook_token: str | None = None
    instagram_token: str | None = None
    slack_webhook: str | None = None
    hubspot_api_key: str | None = None
    wordpress_url: str | None = None
    wordpress_token: str | None = None


class MarceauConfigCreate(BaseModel):
    """Schema creation configuration Marceau."""
    enabled_modules: dict[str, bool] | None = None
    autonomy_levels: dict[str, int] | None = None
    llm_temperature: float = 0.2
    llm_model: str = "llama3-8b-instruct"
    stt_model: str = "whisper-small"
    tts_voice: str = "fr_FR-sise-medium"
    telephony_config: TelephonyConfigSchema | None = None
    integrations: IntegrationsConfigSchema | None = None


class MarceauConfigUpdate(BaseModel):
    """Schema mise a jour configuration Marceau."""
    enabled_modules: dict[str, bool] | None = None
    autonomy_levels: dict[str, int] | None = None
    llm_temperature: float | None = None
    llm_model: str | None = None
    stt_model: str | None = None
    tts_voice: str | None = None
    telephony_config: dict | None = None
    integrations: dict | None = None


class MarceauConfigResponse(BaseModel):
    """Schema reponse configuration Marceau."""
    id: UUID
    tenant_id: str
    enabled_modules: dict[str, bool]
    autonomy_levels: dict[str, int]
    llm_temperature: float
    llm_model: str
    stt_model: str
    tts_voice: str
    telephony_config: dict
    integrations: dict
    total_actions: int
    total_conversations: int
    total_quotes_created: int
    total_appointments_scheduled: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ACTIONS
# ============================================================================

class MarceauActionCreate(BaseModel):
    """Schema creation action Marceau."""
    module: str
    action_type: str
    input_data: dict = Field(default_factory=dict)
    confidence_score: float = 1.0
    related_entity_type: str | None = None
    related_entity_id: UUID | None = None
    conversation_id: UUID | None = None


class MarceauActionResponse(BaseModel):
    """Schema reponse action Marceau."""
    id: UUID
    tenant_id: str
    module: str
    action_type: str
    status: str
    input_data: dict
    output_data: dict
    confidence_score: float
    required_human_validation: bool
    validated_by: UUID | None
    validated_at: datetime | None
    validation_notes: str | None
    related_entity_type: str | None
    related_entity_id: UUID | None
    conversation_id: UUID | None
    duration_seconds: float
    tokens_used: int
    error_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ActionValidationRequest(BaseModel):
    """Schema validation/rejet d'une action."""
    approved: bool
    notes: str | None = None


class ActionListResponse(BaseModel):
    """Schema liste d'actions paginee."""
    items: list[MarceauActionResponse]
    total: int
    skip: int
    limit: int


# ============================================================================
# CONVERSATIONS
# ============================================================================

class MarceauConversationResponse(BaseModel):
    """Schema reponse conversation Marceau."""
    id: UUID
    tenant_id: str
    caller_phone: str
    caller_name: str | None
    customer_id: UUID | None
    transcript: str | None
    summary: str | None
    intent: str | None
    duration_seconds: int
    satisfaction_score: float | None
    outcome: str | None
    recording_url: str | None
    asterisk_call_id: str | None
    transferred_to: str | None
    transfer_reason: str | None
    started_at: datetime
    ended_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Schema liste conversations paginee."""
    items: list[MarceauConversationResponse]
    total: int
    skip: int
    limit: int


class ConversationStatsResponse(BaseModel):
    """Statistiques conversations."""
    total_conversations: int
    avg_duration_seconds: float
    avg_satisfaction_score: float | None
    outcomes_distribution: dict[str, int]
    intents_distribution: dict[str, int]
    calls_by_hour: dict[int, int]
    calls_by_day: dict[str, int]


# ============================================================================
# MEMOIRE
# ============================================================================

class MarceauMemoryCreate(BaseModel):
    """Schema creation memoire."""
    memory_type: str
    content: str
    summary: str | None = None
    tags: list[str] = Field(default_factory=list)
    importance_score: float = 0.5
    is_permanent: bool = False
    source: str | None = None


class MarceauMemoryResponse(BaseModel):
    """Schema reponse memoire."""
    id: UUID
    tenant_id: str
    memory_type: str
    content: str
    summary: str | None
    tags: list[str]
    importance_score: float
    is_permanent: bool
    source: str | None
    source_file_name: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MemorySearchRequest(BaseModel):
    """Schema recherche memoire."""
    query: str
    memory_types: list[str] | None = None
    tags: list[str] | None = None
    limit: int = 10


class MemorySearchResponse(BaseModel):
    """Schema resultat recherche memoire."""
    memories: list[MarceauMemoryResponse]
    query: str
    total_results: int


# ============================================================================
# DOCUMENTS DE CONNAISSANCE
# ============================================================================

class KnowledgeDocumentResponse(BaseModel):
    """Schema reponse document connaissance."""
    id: UUID
    tenant_id: str
    file_name: str
    file_type: str
    file_size: int
    is_processed: bool
    chunks_count: int
    processing_error: str | None
    category: str | None
    tags: list[str]
    uploaded_by: UUID | None
    created_at: datetime
    processed_at: datetime | None

    class Config:
        from_attributes = True


# ============================================================================
# CHAT
# ============================================================================

class ChatMessageRequest(BaseModel):
    """Schema message chat entrant."""
    message: str
    context: dict | None = None
    conversation_id: UUID | None = None


class ChatMessageResponse(BaseModel):
    """Schema reponse chat."""
    message: str
    conversation_id: UUID
    intent: str | None
    actions_taken: list[dict] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    confidence: float = 1.0


# ============================================================================
# TELEPHONIE
# ============================================================================

class IncomingCallRequest(BaseModel):
    """Schema appel entrant."""
    caller_phone: str
    caller_name: str | None = None
    asterisk_call_id: str | None = None
    asterisk_channel: str | None = None


class CallActionRequest(BaseModel):
    """Schema action sur appel."""
    action: str  # answer, transfer, hold, hangup
    target: str | None = None  # Numero de transfert
    reason: str | None = None


class QuoteRequestData(BaseModel):
    """Donnees pour demande de devis."""
    customer_name: str
    phone: str
    email: str | None = None
    address: str | None = None
    description: str
    articles: list[dict] = Field(default_factory=list)


class AppointmentRequestData(BaseModel):
    """Donnees pour demande de RDV."""
    customer_name: str
    phone: str
    address: str
    description: str
    preferred_date: datetime | None = None
    preferred_time_slot: str | None = None  # morning, afternoon


class AvailableSlotResponse(BaseModel):
    """Creneau disponible."""
    technician_id: UUID
    technician_name: str
    start: datetime
    end: datetime
    travel_time_minutes: int
    distance_km: float


# ============================================================================
# DASHBOARD
# ============================================================================

class MarceauDashboardResponse(BaseModel):
    """Dashboard Marceau complet."""
    # Statistiques globales
    total_actions_today: int
    total_conversations_today: int
    total_quotes_today: int
    total_appointments_today: int

    # Tendances (vs jour precedent)
    actions_trend: float  # % variation
    conversations_trend: float
    quotes_trend: float
    appointments_trend: float

    # Actions par module
    actions_by_module: dict[str, int]

    # Actions en attente de validation
    pending_validations: int

    # Dernières actions
    recent_actions: list[MarceauActionResponse]

    # Alertes
    alerts: list[dict]

    # Metriques IA
    avg_confidence_score: float
    avg_response_time_seconds: float
    tokens_used_today: int

    # Statut LLM
    llm_configured: bool = False
    llm_provider: str | None = None


class ModuleStatsResponse(BaseModel):
    """Statistiques par module."""
    module: str
    total_actions: int
    successful_actions: int
    failed_actions: int
    pending_validations: int
    avg_confidence_score: float
    avg_duration_seconds: float


# ============================================================================
# FEEDBACK
# ============================================================================

class FeedbackCreate(BaseModel):
    """Schema creation feedback."""
    action_id: UUID
    rating: int = Field(ge=-1, le=5)
    feedback_type: str  # positive, negative, correction
    comment: str | None = None
    correction_data: dict | None = None


class FeedbackResponse(BaseModel):
    """Schema reponse feedback."""
    id: UUID
    action_id: UUID
    rating: int
    feedback_type: str
    comment: str | None
    is_processed: bool
    applied_to_learning: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TACHES PLANIFIEES
# ============================================================================

class ScheduledTaskCreate(BaseModel):
    """Schema creation tache planifiee."""
    name: str
    description: str | None = None
    module: str
    action_type: str
    action_params: dict = Field(default_factory=dict)
    cron_expression: str
    timezone: str = "Europe/Paris"


class ScheduledTaskResponse(BaseModel):
    """Schema reponse tache planifiee."""
    id: UUID
    tenant_id: str
    name: str
    description: str | None
    module: str
    action_type: str
    action_params: dict
    cron_expression: str
    timezone: str
    is_active: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    last_run_status: str | None
    run_count: int
    success_count: int
    failure_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ScheduledTaskUpdate(BaseModel):
    """Schema mise a jour tache planifiee."""
    name: str | None = None
    description: str | None = None
    action_params: dict | None = None
    cron_expression: str | None = None
    timezone: str | None = None
    is_active: bool | None = None
