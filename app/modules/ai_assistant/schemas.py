"""
AZALS - MODULE IA TRANSVERSE - Schémas Pydantic
================================================
Schémas pour validation et sérialisation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# CONVERSATION SCHEMAS
# ============================================================================

class ConversationCreate(BaseModel):
    """Création conversation."""
    title: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    module_source: Optional[str] = None


class ConversationResponse(BaseModel):
    """Réponse conversation."""
    id: int
    title: Optional[str]
    context: Optional[Dict[str, Any]]
    module_source: Optional[str]
    is_active: bool
    message_count: int
    created_at: datetime
    last_activity: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    """Création message."""
    content: str = Field(..., min_length=1, max_length=10000)
    request_type: str = "question"
    context: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """Réponse message."""
    id: int
    role: str
    request_type: Optional[str]
    content: str
    message_metadata: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIQuestionRequest(BaseModel):
    """Requête question à l'IA."""
    question: str = Field(..., min_length=1, max_length=5000)
    context: Optional[Dict[str, Any]] = None
    module_source: Optional[str] = None
    include_data: Optional[bool] = False


class AIQuestionResponse(BaseModel):
    """Réponse de l'IA."""
    answer: str
    confidence: float
    sources: Optional[List[str]] = None
    related_topics: Optional[List[str]] = None
    follow_up_suggestions: Optional[List[str]] = None


# ============================================================================
# ANALYSIS SCHEMAS
# ============================================================================

class AnalysisRequest(BaseModel):
    """Requête d'analyse."""
    title: str = Field(..., min_length=1, max_length=255)
    analysis_type: str = Field(..., description="Type: 360, financial, operational, risk, etc.")
    description: Optional[str] = None
    module_source: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    data_period_start: Optional[datetime] = None
    data_period_end: Optional[datetime] = None
    parameters: Optional[Dict[str, Any]] = None


class AnalysisFinding(BaseModel):
    """Constat d'analyse."""
    category: str
    title: str
    description: str
    severity: str  # info, warning, critical
    data: Optional[Dict[str, Any]] = None


class AnalysisRecommendation(BaseModel):
    """Recommandation d'analyse."""
    priority: int  # 1-5
    title: str
    description: str
    rationale: str
    expected_impact: Optional[str] = None
    implementation_effort: Optional[str] = None
    actions: Optional[List[str]] = None


class AnalysisResponse(BaseModel):
    """Réponse analyse."""
    id: int
    analysis_code: str
    title: str
    analysis_type: str
    status: str
    summary: Optional[str]
    findings: Optional[List[Dict[str, Any]]]
    metrics: Optional[Dict[str, Any]]
    confidence_score: Optional[float]
    risks_identified: Optional[List[Dict[str, Any]]]
    overall_risk_level: Optional[str]
    recommendations: Optional[List[Dict[str, Any]]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# DECISION SUPPORT SCHEMAS
# ============================================================================

class DecisionOption(BaseModel):
    """Option de décision."""
    title: str
    description: str
    pros: List[str]
    cons: List[str]
    estimated_cost: Optional[float] = None
    estimated_benefit: Optional[float] = None
    risk_level: Optional[str] = None
    implementation_time: Optional[str] = None


class DecisionSupportCreate(BaseModel):
    """Création support de décision."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    decision_type: str
    module_source: Optional[str] = None
    priority: str = "normal"
    deadline: Optional[datetime] = None
    context: Optional[Dict[str, Any]] = None
    analysis_id: Optional[int] = None


class DecisionSupportResponse(BaseModel):
    """Réponse support de décision."""
    id: int
    decision_code: str
    title: str
    description: Optional[str]
    decision_type: str
    priority: str
    deadline: Optional[datetime]
    options: Optional[List[Dict[str, Any]]]
    recommended_option: Optional[int]
    recommendation_rationale: Optional[str]
    risk_level: Optional[str]
    risks: Optional[List[Dict[str, Any]]]
    is_red_point: bool
    requires_double_confirmation: bool
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DecisionConfirmation(BaseModel):
    """Confirmation de décision."""
    decision_made: int  # Index de l'option choisie
    notes: Optional[str] = None


# ============================================================================
# RISK SCHEMAS
# ============================================================================

class RiskAlertCreate(BaseModel):
    """Création alerte risque."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    risk_level: str
    probability: Optional[float] = None
    impact_score: Optional[float] = None
    detection_source: Optional[str] = None
    trigger_data: Optional[Dict[str, Any]] = None
    affected_entities: Optional[List[Dict[str, Any]]] = None
    recommended_actions: Optional[List[str]] = None


class RiskAlertResponse(BaseModel):
    """Réponse alerte risque."""
    id: int
    alert_code: str
    title: str
    description: Optional[str]
    category: str
    risk_level: str
    probability: Optional[float]
    impact_score: Optional[float]
    status: str
    affected_entities: Optional[List[Dict[str, Any]]]
    recommended_actions: Optional[List[str]]
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskAcknowledge(BaseModel):
    """Accusé de réception risque."""
    notes: Optional[str] = None


class RiskResolve(BaseModel):
    """Résolution risque."""
    resolution_notes: str
    actions_taken: Optional[List[str]] = None


# ============================================================================
# PREDICTION SCHEMAS
# ============================================================================

class PredictionRequest(BaseModel):
    """Requête de prédiction."""
    title: str
    prediction_type: str  # sales, cashflow, demand, etc.
    target_metric: Optional[str] = None
    module_source: Optional[str] = None
    prediction_start: datetime
    prediction_end: datetime
    granularity: str = "daily"  # daily, weekly, monthly
    parameters: Optional[Dict[str, Any]] = None


class PredictionValue(BaseModel):
    """Valeur prédite."""
    date: datetime
    value: float
    confidence: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None


class PredictionResponse(BaseModel):
    """Réponse prédiction."""
    id: int
    prediction_code: str
    title: str
    prediction_type: str
    prediction_start: datetime
    prediction_end: datetime
    granularity: str
    predicted_values: Optional[List[Dict[str, Any]]]
    confidence_score: Optional[float]
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
    rating: Optional[int] = Field(None, ge=1, le=5)
    is_helpful: Optional[bool] = None
    is_accurate: Optional[bool] = None
    feedback_text: Optional[str] = None
    improvement_suggestion: Optional[str] = None
    feedback_category: Optional[str] = None


# ============================================================================
# CONFIGURATION SCHEMAS
# ============================================================================

class AIConfigUpdate(BaseModel):
    """Mise à jour configuration IA."""
    is_enabled: Optional[bool] = None
    enabled_features: Optional[List[str]] = None
    daily_request_limit: Optional[int] = None
    response_language: Optional[str] = None
    formality_level: Optional[str] = None
    detail_level: Optional[str] = None
    require_confirmation_threshold: Optional[str] = None
    auto_escalation_enabled: Optional[bool] = None
    notify_on_risk: Optional[bool] = None
    notify_on_anomaly: Optional[bool] = None


class AIConfigResponse(BaseModel):
    """Réponse configuration."""
    is_enabled: bool
    enabled_features: Optional[List[str]]
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
    features_status: Dict[str, str]
    last_error: Optional[str] = None
    uptime_percent: float = 100.0


# ============================================================================
# SYNTHESIS SCHEMAS
# ============================================================================

class SynthesisRequest(BaseModel):
    """Requête de synthèse."""
    title: str
    synthesis_type: str  # daily, weekly, monthly, custom
    modules: Optional[List[str]] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    focus_areas: Optional[List[str]] = None


class SynthesisResponse(BaseModel):
    """Réponse synthèse."""
    title: str
    period: str
    executive_summary: str
    key_metrics: Dict[str, Any]
    highlights: List[str]
    concerns: List[str]
    action_items: List[str]
    generated_at: datetime
