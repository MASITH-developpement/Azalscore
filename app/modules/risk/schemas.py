"""
Schémas Pydantic Risk Management - GAP-075
===========================================
"""
from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============== RiskMatrix Schemas ==============

class RiskMatrixCreate(BaseModel):
    """Création matrice de risques."""
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    description: str = ""
    probability_scale: int = Field(default=5, ge=3, le=10)
    impact_scale: int = Field(default=5, ge=3, le=10)
    low_threshold: int = Field(default=4, ge=1)
    medium_threshold: int = Field(default=9, ge=1)
    high_threshold: int = Field(default=15, ge=1)
    probability_labels: Dict[str, str] = Field(default_factory=dict)
    impact_labels: Dict[str, str] = Field(default_factory=dict)
    color_low: str = "#4CAF50"
    color_medium: str = "#FFC107"
    color_high: str = "#FF9800"
    color_critical: str = "#F44336"
    is_default: bool = False
    is_active: bool = True


class RiskMatrixUpdate(BaseModel):
    """Mise à jour matrice."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    probability_scale: Optional[int] = Field(None, ge=3, le=10)
    impact_scale: Optional[int] = Field(None, ge=3, le=10)
    low_threshold: Optional[int] = Field(None, ge=1)
    medium_threshold: Optional[int] = Field(None, ge=1)
    high_threshold: Optional[int] = Field(None, ge=1)
    probability_labels: Optional[Dict[str, str]] = None
    impact_labels: Optional[Dict[str, str]] = None
    color_low: Optional[str] = None
    color_medium: Optional[str] = None
    color_high: Optional[str] = None
    color_critical: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class RiskMatrixResponse(BaseModel):
    """Réponse matrice."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    code: str
    description: str
    probability_scale: int
    impact_scale: int
    low_threshold: int
    medium_threshold: int
    high_threshold: int
    probability_labels: Dict[str, str]
    impact_labels: Dict[str, str]
    color_low: str
    color_medium: str
    color_high: str
    color_critical: str
    is_default: bool
    is_active: bool
    created_at: datetime
    version: int


class RiskMatrixListResponse(BaseModel):
    """Liste paginée matrices."""
    items: List[RiskMatrixResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Risk Schemas ==============

class RiskCreate(BaseModel):
    """Création risque."""
    code: Optional[str] = Field(None, max_length=50)
    title: str = Field(..., min_length=1, max_length=300)
    description: str = ""
    category: str = "operational"
    matrix_id: Optional[UUID] = None
    inherent_probability: str = "possible"
    inherent_impact: str = "moderate"
    target_probability: Optional[str] = None
    target_impact: Optional[str] = None
    financial_impact_min: Decimal = Decimal("0")
    financial_impact_max: Decimal = Decimal("0")
    financial_impact_expected: Decimal = Decimal("0")
    owner_id: Optional[UUID] = None
    reviewer_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    next_review_date: Optional[date] = None
    causes: List[str] = Field(default_factory=list)
    consequences: List[str] = Field(default_factory=list)
    affected_objectives: List[str] = Field(default_factory=list)
    affected_processes: List[str] = Field(default_factory=list)
    related_risk_ids: List[UUID] = Field(default_factory=list)
    parent_risk_id: Optional[UUID] = None
    mitigation_strategy: str = "reduce"
    tags: List[str] = Field(default_factory=list)


class RiskUpdate(BaseModel):
    """Mise à jour risque."""
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None
    category: Optional[str] = None
    matrix_id: Optional[UUID] = None
    inherent_probability: Optional[str] = None
    inherent_impact: Optional[str] = None
    target_probability: Optional[str] = None
    target_impact: Optional[str] = None
    financial_impact_min: Optional[Decimal] = None
    financial_impact_max: Optional[Decimal] = None
    financial_impact_expected: Optional[Decimal] = None
    owner_id: Optional[UUID] = None
    reviewer_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    next_review_date: Optional[date] = None
    causes: Optional[List[str]] = None
    consequences: Optional[List[str]] = None
    affected_objectives: Optional[List[str]] = None
    affected_processes: Optional[List[str]] = None
    related_risk_ids: Optional[List[UUID]] = None
    parent_risk_id: Optional[UUID] = None
    mitigation_strategy: Optional[str] = None
    tags: Optional[List[str]] = None


class RiskResponse(BaseModel):
    """Réponse risque."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    title: str
    description: str
    category: str
    status: str
    matrix_id: Optional[UUID]
    inherent_probability: str
    inherent_impact: str
    inherent_score: int
    inherent_level: str
    residual_probability: Optional[str]
    residual_impact: Optional[str]
    residual_score: int
    residual_level: Optional[str]
    target_probability: Optional[str]
    target_impact: Optional[str]
    target_level: Optional[str]
    financial_impact_min: Decimal
    financial_impact_max: Decimal
    financial_impact_expected: Decimal
    owner_id: Optional[UUID]
    reviewer_id: Optional[UUID]
    department_id: Optional[UUID]
    identified_at: datetime
    last_assessed_at: Optional[datetime]
    next_review_date: Optional[date]
    closed_at: Optional[datetime]
    causes: List[str]
    consequences: List[str]
    affected_objectives: List[str]
    affected_processes: List[str]
    related_risk_ids: List[UUID]
    parent_risk_id: Optional[UUID]
    mitigation_strategy: str
    tags: List[str]
    extra_data: Dict[str, Any]
    created_at: datetime
    version: int


class RiskListResponse(BaseModel):
    """Liste paginée risques."""
    items: List[RiskResponse]
    total: int
    page: int
    page_size: int
    pages: int


class RiskFilters(BaseModel):
    """Filtres risques."""
    category: Optional[str] = None
    status: Optional[str] = None
    level: Optional[str] = None
    owner_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    include_closed: bool = False


# ============== Control Schemas ==============

class ControlCreate(BaseModel):
    """Création contrôle."""
    risk_id: UUID
    code: Optional[str] = Field(None, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    control_type: str = "preventive"
    effectiveness: str = "effective"
    cost: Decimal = Decimal("0")
    owner_id: Optional[UUID] = None
    operator_id: Optional[UUID] = None
    frequency: str = ""
    procedure: str = ""
    evidence_required: str = ""
    evidence_links: List[str] = Field(default_factory=list)
    is_automated: bool = False
    is_active: bool = True


class ControlUpdate(BaseModel):
    """Mise à jour contrôle."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    control_type: Optional[str] = None
    effectiveness: Optional[str] = None
    cost: Optional[Decimal] = None
    owner_id: Optional[UUID] = None
    operator_id: Optional[UUID] = None
    frequency: Optional[str] = None
    procedure: Optional[str] = None
    evidence_required: Optional[str] = None
    evidence_links: Optional[List[str]] = None
    is_automated: Optional[bool] = None
    is_active: Optional[bool] = None


class ControlResponse(BaseModel):
    """Réponse contrôle."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    risk_id: UUID
    code: str
    name: str
    description: str
    control_type: str
    effectiveness: str
    cost: Decimal
    owner_id: Optional[UUID]
    operator_id: Optional[UUID]
    frequency: str
    last_executed_at: Optional[datetime]
    next_execution_at: Optional[datetime]
    procedure: str
    evidence_required: str
    evidence_links: List[str]
    is_automated: bool
    is_active: bool
    created_at: datetime
    version: int


class ControlListResponse(BaseModel):
    """Liste paginée contrôles."""
    items: List[ControlResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ControlExecutionRecord(BaseModel):
    """Enregistrement d'exécution contrôle."""
    effectiveness: str = "effective"
    notes: str = ""
    evidence_links: List[str] = Field(default_factory=list)


# ============== MitigationAction Schemas ==============

class ActionCreate(BaseModel):
    """Création action."""
    risk_id: UUID
    code: Optional[str] = Field(None, max_length=50)
    title: str = Field(..., min_length=1, max_length=300)
    description: str = ""
    assignee_id: Optional[UUID] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    estimated_cost: Decimal = Decimal("0")
    currency: str = "EUR"
    expected_probability_reduction: int = Field(default=0, ge=0, le=5)
    expected_impact_reduction: int = Field(default=0, ge=0, le=5)
    priority: int = Field(default=0, ge=0, le=10)
    notes: str = ""


class ActionUpdate(BaseModel):
    """Mise à jour action."""
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None
    assignee_id: Optional[UUID] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    estimated_cost: Optional[Decimal] = None
    currency: Optional[str] = None
    expected_probability_reduction: Optional[int] = Field(None, ge=0, le=5)
    expected_impact_reduction: Optional[int] = Field(None, ge=0, le=5)
    priority: Optional[int] = Field(None, ge=0, le=10)
    notes: Optional[str] = None


class ActionProgressUpdate(BaseModel):
    """Mise à jour progression action."""
    progress_percent: int = Field(..., ge=0, le=100)
    actual_cost: Optional[Decimal] = None
    notes: str = ""


class ActionResponse(BaseModel):
    """Réponse action."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    risk_id: UUID
    code: str
    title: str
    description: str
    status: str
    assignee_id: Optional[UUID]
    planned_start: Optional[date]
    planned_end: Optional[date]
    actual_start: Optional[date]
    actual_end: Optional[date]
    progress_percent: int
    estimated_cost: Decimal
    actual_cost: Decimal
    currency: str
    expected_probability_reduction: int
    expected_impact_reduction: int
    priority: int
    notes: str
    created_at: datetime
    version: int


class ActionListResponse(BaseModel):
    """Liste paginée actions."""
    items: List[ActionResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============== RiskIndicator Schemas ==============

class IndicatorCreate(BaseModel):
    """Création indicateur."""
    risk_id: UUID
    code: Optional[str] = Field(None, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    metric_type: str = "count"
    unit: str = ""
    green_threshold: Decimal = Decimal("0")
    amber_threshold: Decimal = Decimal("0")
    red_threshold: Decimal = Decimal("0")
    higher_is_worse: bool = True
    measurement_frequency: str = "monthly"
    data_source: str = ""
    is_automated: bool = False
    is_active: bool = True


class IndicatorUpdate(BaseModel):
    """Mise à jour indicateur."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    metric_type: Optional[str] = None
    unit: Optional[str] = None
    green_threshold: Optional[Decimal] = None
    amber_threshold: Optional[Decimal] = None
    red_threshold: Optional[Decimal] = None
    higher_is_worse: Optional[bool] = None
    measurement_frequency: Optional[str] = None
    data_source: Optional[str] = None
    is_automated: Optional[bool] = None
    is_active: Optional[bool] = None


class IndicatorValueRecord(BaseModel):
    """Enregistrement de valeur indicateur."""
    value: Decimal
    measurement_date: Optional[datetime] = None
    notes: str = ""


class IndicatorResponse(BaseModel):
    """Réponse indicateur."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    risk_id: UUID
    code: str
    name: str
    description: str
    metric_type: str
    unit: str
    current_value: Decimal
    green_threshold: Decimal
    amber_threshold: Decimal
    red_threshold: Decimal
    higher_is_worse: bool
    current_status: str
    measurement_frequency: str
    last_measured_at: Optional[datetime]
    historical_values: List[Dict[str, Any]]
    data_source: str
    is_automated: bool
    is_active: bool
    created_at: datetime
    version: int


class IndicatorListResponse(BaseModel):
    """Liste paginée indicateurs."""
    items: List[IndicatorResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============== RiskAssessment Schemas ==============

class AssessmentCreate(BaseModel):
    """Création évaluation."""
    risk_id: UUID
    probability: str = "possible"
    impact: str = "moderate"
    assessment_type: str = "periodic"
    is_residual: bool = False
    trigger_event: str = ""
    rationale: str = ""
    supporting_evidence: List[str] = Field(default_factory=list)
    controls_evaluated: List[UUID] = Field(default_factory=list)
    control_effectiveness_summary: str = ""


class AssessmentValidation(BaseModel):
    """Validation évaluation."""
    notes: str = ""


class AssessmentResponse(BaseModel):
    """Réponse évaluation."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    risk_id: UUID
    assessment_date: datetime
    assessor_id: Optional[UUID]
    probability: str
    impact: str
    score: int
    level: str
    assessment_type: str
    is_residual: bool
    trigger_event: str
    rationale: str
    supporting_evidence: List[str]
    controls_evaluated: List[UUID]
    control_effectiveness_summary: str
    is_validated: bool
    validated_by: Optional[UUID]
    validated_at: Optional[datetime]
    created_at: datetime


class AssessmentListResponse(BaseModel):
    """Liste paginée évaluations."""
    items: List[AssessmentResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============== RiskIncident Schemas ==============

class IncidentCreate(BaseModel):
    """Création incident."""
    risk_id: Optional[UUID] = None
    code: Optional[str] = Field(None, max_length=50)
    title: str = Field(..., min_length=1, max_length=300)
    description: str = ""
    occurred_at: Optional[datetime] = None
    detected_at: Optional[datetime] = None
    actual_impact: str = "moderate"
    financial_loss: Decimal = Decimal("0")
    currency: str = "EUR"
    affected_parties: List[str] = Field(default_factory=list)
    root_cause: str = ""
    contributing_factors: List[str] = Field(default_factory=list)
    owner_id: Optional[UUID] = None


class IncidentUpdate(BaseModel):
    """Mise à jour incident."""
    risk_id: Optional[UUID] = None
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None
    occurred_at: Optional[datetime] = None
    detected_at: Optional[datetime] = None
    actual_impact: Optional[str] = None
    financial_loss: Optional[Decimal] = None
    currency: Optional[str] = None
    affected_parties: Optional[List[str]] = None
    root_cause: Optional[str] = None
    contributing_factors: Optional[List[str]] = None
    control_failures: Optional[List[UUID]] = None
    owner_id: Optional[UUID] = None


class IncidentResolution(BaseModel):
    """Résolution incident."""
    lessons_learned: str = ""
    corrective_action_ids: List[UUID] = Field(default_factory=list)


class IncidentResponse(BaseModel):
    """Réponse incident."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    risk_id: Optional[UUID]
    code: str
    title: str
    description: str
    status: str
    occurred_at: datetime
    detected_at: Optional[datetime]
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    actual_impact: str
    financial_loss: Decimal
    currency: str
    affected_parties: List[str]
    root_cause: str
    contributing_factors: List[str]
    control_failures: List[UUID]
    corrective_action_ids: List[UUID]
    lessons_learned: str
    reporter_id: Optional[UUID]
    owner_id: Optional[UUID]
    created_at: datetime
    version: int


class IncidentListResponse(BaseModel):
    """Liste paginée incidents."""
    items: List[IncidentResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Report Schemas ==============

class RiskReportRequest(BaseModel):
    """Demande de rapport."""
    report_date: Optional[date] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    include_closed: bool = False


class RiskReportResponse(BaseModel):
    """Rapport de risques."""
    tenant_id: UUID
    report_date: date
    period_start: Optional[date]
    period_end: Optional[date]

    # Vue d'ensemble
    total_risks: int
    active_risks: int
    new_risks: int
    closed_risks: int

    # Par niveau
    critical_risks: int
    high_risks: int
    medium_risks: int
    low_risks: int

    # Par catégorie et statut
    risks_by_category: Dict[str, int]
    risks_by_status: Dict[str, int]

    # Actions
    total_actions: int
    completed_actions: int
    overdue_actions: int
    action_completion_rate: Decimal

    # KRIs
    total_kris: int
    kris_in_red: int
    kris_in_amber: int

    # Incidents
    total_incidents: int
    total_financial_loss: Decimal

    # Tendances
    risk_trend: str
    top_risks: List[Dict[str, Any]]
    heatmap_data: List[Dict[str, Any]]


class HeatmapCell(BaseModel):
    """Cellule de la heatmap."""
    probability: str
    impact: str
    count: int
    risk_ids: List[UUID] = Field(default_factory=list)


class RiskHeatmapResponse(BaseModel):
    """Heatmap des risques."""
    cells: List[HeatmapCell]
    probability_labels: Dict[str, str]
    impact_labels: Dict[str, str]


# ============== Common Schemas ==============

class AutocompleteResponse(BaseModel):
    """Réponse autocomplete."""
    items: List[Dict[str, Any]]


class BulkResult(BaseModel):
    """Résultat opération en masse."""
    success_count: int
    failure_count: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
