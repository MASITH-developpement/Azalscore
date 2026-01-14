"""
AZALS - MODULE IA TRANSVERSE - Schémas Pydantic
================================================
Schémas pour validation et sérialisation.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# CONVERSATION SCHEMAS
# ============================================================================

class ConversationCreate(BaseModel):
    """Création conversation."""
    title: str | None = None
    context: dict[str, Any] | None = None
    module_source: str | None = None


class ConversationResponse(BaseModel):
    """Réponse conversation."""
    id: int
    title: str | None
    context: dict[str, Any] | None
    module_source: str | None
    is_active: bool
    message_count: int
    created_at: datetime
    last_activity: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    """Création message."""
    content: str = Field(..., min_length=1, max_length=10000)
    request_type: str = "question"
    context: dict[str, Any] | None = None


class MessageResponse(BaseModel):
    """Réponse message."""
    id: int
    role: str
    request_type: str | None
    content: str
    message_metadata: dict[str, Any] | None = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIQuestionRequest(BaseModel):
    """Requête question à l'IA."""
    question: str = Field(..., min_length=1, max_length=5000)
    context: dict[str, Any] | None = None
    module_source: str | None = None
    include_data: bool | None = False


class AIQuestionResponse(BaseModel):
    """Réponse de l'IA."""
    answer: str
    confidence: float
    sources: list[str] | None = None
    related_topics: list[str] | None = None
    follow_up_suggestions: list[str] | None = None


# ============================================================================
# ANALYSIS SCHEMAS
# ============================================================================

class AnalysisRequest(BaseModel):
    """Requête d'analyse."""
    title: str = Field(..., min_length=1, max_length=255)
    analysis_type: str = Field(..., description="Type: 360, financial, operational, risk, etc.")
    description: str | None = None
    module_source: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    data_period_start: datetime | None = None
    data_period_end: datetime | None = None
    parameters: dict[str, Any] | None = None


class AnalysisFinding(BaseModel):
    """Constat d'analyse."""
    category: str
    title: str
    description: str
    severity: str  # info, warning, critical
    data: dict[str, Any] | None = None


class AnalysisRecommendation(BaseModel):
    """Recommandation d'analyse."""
    priority: int  # 1-5
    title: str
    description: str
    rationale: str
    expected_impact: str | None = None
    implementation_effort: str | None = None
    actions: list[str] | None = None


class AnalysisResponse(BaseModel):
    """Réponse analyse."""
    id: int
    analysis_code: str
    title: str
    analysis_type: str
    status: str
    summary: str | None
    findings: list[dict[str, Any]] | None
    metrics: dict[str, Any] | None
    confidence_score: float | None
    risks_identified: list[dict[str, Any]] | None
    overall_risk_level: str | None
    recommendations: list[dict[str, Any]] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# DECISION SUPPORT SCHEMAS
# ============================================================================

class DecisionOption(BaseModel):
    """Option de décision."""
    title: str
    description: str
    pros: list[str]
    cons: list[str]
    estimated_cost: float | None = None
    estimated_benefit: float | None = None
    risk_level: str | None = None
    implementation_time: str | None = None


class DecisionSupportCreate(BaseModel):
    """Création support de décision."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    decision_type: str
    module_source: str | None = None
    priority: str = "normal"
    deadline: datetime | None = None
    context: dict[str, Any] | None = None
    analysis_id: int | None = None


class DecisionSupportResponse(BaseModel):
    """Réponse support de décision."""
    id: int
    decision_code: str
    title: str
    description: str | None
    decision_type: str
    priority: str
    deadline: datetime | None
    options: list[dict[str, Any]] | None
    recommended_option: int | None
    recommendation_rationale: str | None
    risk_level: str | None
    risks: list[dict[str, Any]] | None
    is_red_point: bool
    requires_double_confirmation: bool
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DecisionConfirmation(BaseModel):
    """Confirmation de décision."""
    decision_made: int  # Index de l'option choisie
    notes: str | None = None


# ============================================================================
# RISK SCHEMAS
# ============================================================================

class RiskAlertCreate(BaseModel):
    """Création alerte risque."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str
    subcategory: str | None = None
    risk_level: str
    probability: float | None = None
    impact_score: float | None = None
    detection_source: str | None = None
    trigger_data: dict[str, Any] | None = None
    affected_entities: list[dict[str, Any]] | None = None
    recommended_actions: list[str] | None = None


class RiskAlertResponse(BaseModel):
    """Réponse alerte risque."""
    id: int
    alert_code: str
    title: str
    description: str | None
    category: str
    risk_level: str
    probability: float | None
    impact_score: float | None
    status: str
    affected_entities: list[dict[str, Any]] | None
    recommended_actions: list[str] | None
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskAcknowledge(BaseModel):
    """Accusé de réception risque."""
    notes: str | None = None


class RiskResolve(BaseModel):
    """Résolution risque."""
    resolution_notes: str
    actions_taken: list[str] | None = None


# ============================================================================
# PREDICTION SCHEMAS
# ============================================================================

class PredictionRequest(BaseModel):
    """Requête de prédiction."""
    title: str
    prediction_type: str  # sales, cashflow, demand, etc.
    target_metric: str | None = None
    module_source: str | None = None
    prediction_start: datetime
    prediction_end: datetime
    granularity: str = "daily"  # daily, weekly, monthly
    parameters: dict[str, Any] | None = None


class PredictionValue(BaseModel):
    """Valeur prédite."""
    date: datetime
    value: float
    confidence: float
    lower_bound: float | None = None
    upper_bound: float | None = None


class PredictionResponse(BaseModel):
    """Réponse prédiction."""
    id: int
    prediction_code: str
    title: str
    prediction_type: str
    prediction_start: datetime
    prediction_end: datetime
    granularity: str
    predicted_values: list[dict[str, Any]] | None
    confidence_score: float | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# FEEDBACK SCHEMAS
# ============================================================================

class FeedbackCreate(BaseModel):
    """Création feedback."""
    reference_type: str
    reference_id: int
    rating: int | None = Field(None, ge=1, le=5)
    is_helpful: bool | None = None
    is_accurate: bool | None = None
    feedback_text: str | None = None
    improvement_suggestion: str | None = None
    feedback_category: str | None = None


# ============================================================================
# CONFIGURATION SCHEMAS
# ============================================================================

class AIConfigUpdate(BaseModel):
    """Mise à jour configuration IA."""
    is_enabled: bool | None = None
    enabled_features: list[str] | None = None
    daily_request_limit: int | None = None
    response_language: str | None = None
    formality_level: str | None = None
    detail_level: str | None = None
    require_confirmation_threshold: str | None = None
    auto_escalation_enabled: bool | None = None
    notify_on_risk: bool | None = None
    notify_on_anomaly: bool | None = None


class AIConfigResponse(BaseModel):
    """Réponse configuration."""
    is_enabled: bool
    enabled_features: list[str] | None
    daily_request_limit: int
    response_language: str
    formality_level: str
    detail_level: str
    require_confirmation_threshold: str
    auto_escalation_enabled: bool
    notify_on_risk: bool
    notify_on_anomaly: bool

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================

class AIStats(BaseModel):
    """Statistiques IA."""
    total_conversations: int = 0
    total_messages: int = 0
    total_analyses: int = 0
    pending_decisions: int = 0
    active_risks: int = 0
    critical_risks: int = 0
    avg_response_time_ms: float = 0
    avg_satisfaction_rating: float = 0
    requests_today: int = 0
    predictions_accuracy: float = 0


class AIHealthCheck(BaseModel):
    """État de santé IA."""
    status: str  # healthy, degraded, unhealthy
    response_time_ms: int
    features_status: dict[str, str]
    last_error: str | None = None
    uptime_percent: float = 100.0


# ============================================================================
# SYNTHESIS SCHEMAS
# ============================================================================

class SynthesisRequest(BaseModel):
    """Requête de synthèse."""
    title: str
    synthesis_type: str  # daily, weekly, monthly, custom
    modules: list[str] | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    focus_areas: list[str] | None = None


class SynthesisResponse(BaseModel):
    """Réponse synthèse."""
    title: str
    period: str
    executive_summary: str
    key_metrics: dict[str, Any]
    highlights: list[str]
    concerns: list[str]
    action_items: list[str]
    generated_at: datetime
