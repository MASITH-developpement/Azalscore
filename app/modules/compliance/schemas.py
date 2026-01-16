"""
AZALS MODULE M11 - Schémas Conformité
=====================================

Schémas Pydantic pour la gestion de la conformité réglementaire.
"""


import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .models import (
    ActionStatus,
    AssessmentStatus,
    AuditStatus,
    ComplianceStatus,
    DocumentType,
    FindingSeverity,
    IncidentSeverity,
    IncidentStatus,
    RegulationType,
    ReportType,
    RequirementPriority,
    RiskLevel,
)

# =============================================================================
# SCHÉMAS - RÉGLEMENTATIONS
# =============================================================================

class RegulationBase(BaseModel):
    """Schéma de base pour les réglementations."""
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    regulation_type: RegulationType = Field(default=RegulationType.INTERNAL, alias="type")
    version: str | None = Field(None, max_length=50)
    description: str | None = None
    scope: str | None = None
    authority: str | None = Field(None, max_length=200)
    effective_date: datetime.date | None = None
    expiry_date: datetime.date | None = None
    next_review_date: datetime.date | None = None
    is_mandatory: bool = True
    external_reference: str | None = Field(None, max_length=200)
    source_url: str | None = None
    notes: str | None = None


class RegulationCreate(RegulationBase):
    """Schéma de création de réglementation."""
    pass


class RegulationUpdate(BaseModel):
    """Schéma de mise à jour de réglementation."""
    name: str | None = Field(None, max_length=200)
    version: str | None = Field(None, max_length=50)
    description: str | None = None
    scope: str | None = None
    authority: str | None = Field(None, max_length=200)
    effective_date: datetime.date | None = None
    expiry_date: datetime.date | None = None
    next_review_date: datetime.date | None = None
    is_mandatory: bool | None = None
    is_active: bool | None = None
    notes: str | None = None


class RegulationResponse(RegulationBase):
    """Schéma de réponse pour les réglementations."""
    id: UUID
    tenant_id: str
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    requirements_count: int | None = 0

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - EXIGENCES
# =============================================================================

class RequirementBase(BaseModel):
    """Schéma de base pour les exigences."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: str | None = None
    priority: RequirementPriority = RequirementPriority.MEDIUM
    category: str | None = Field(None, max_length=100)
    clause_reference: str | None = Field(None, max_length=100)
    target_score: Decimal = Field(default=Decimal("100"), ge=0, le=100)
    control_frequency: str | None = Field(None, max_length=50)
    evidence_required: list[str] | None = None
    is_key_control: bool = False


class RequirementCreate(RequirementBase):
    """Schéma de création d'exigence."""
    regulation_id: UUID
    parent_id: UUID | None = None
    responsible_id: UUID | None = None
    department: str | None = Field(None, max_length=100)
    next_assessment: datetime.date | None = None


class RequirementUpdate(BaseModel):
    """Schéma de mise à jour d'exigence."""
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    priority: RequirementPriority | None = None
    category: str | None = Field(None, max_length=100)
    compliance_status: ComplianceStatus | None = None
    current_score: Decimal | None = Field(None, ge=0, le=100)
    target_score: Decimal | None = Field(None, ge=0, le=100)
    responsible_id: UUID | None = None
    control_frequency: str | None = Field(None, max_length=50)
    next_assessment: datetime.date | None = None
    is_active: bool | None = None


class RequirementResponse(RequirementBase):
    """Schéma de réponse pour les exigences."""
    id: UUID
    tenant_id: str
    regulation_id: UUID
    parent_id: UUID | None = None
    compliance_status: ComplianceStatus
    current_score: Decimal | None = None
    responsible_id: UUID | None = None
    department: str | None = None
    last_assessed: datetime.datetime | None = None
    next_assessment: datetime.date | None = None
    is_active: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - ÉVALUATIONS
# =============================================================================

class AssessmentBase(BaseModel):
    """Schéma de base pour les évaluations."""
    name: str = Field(..., max_length=200)
    description: str | None = None
    assessment_type: str | None = Field(None, max_length=50)
    scope_description: str | None = None
    planned_date: datetime.date | None = None


class AssessmentCreate(AssessmentBase):
    """Schéma de création d'évaluation."""
    regulation_id: UUID | None = None
    lead_assessor_id: UUID | None = None
    assessor_ids: list[UUID] | None = None


class AssessmentUpdate(BaseModel):
    """Schéma de mise à jour d'évaluation."""
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    scope_description: str | None = None
    planned_date: datetime.date | None = None
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None
    status: AssessmentStatus | None = None
    overall_score: Decimal | None = Field(None, ge=0, le=100)
    overall_status: ComplianceStatus | None = None
    findings_summary: str | None = None
    recommendations: str | None = None


class AssessmentResponse(AssessmentBase):
    """Schéma de réponse pour les évaluations."""
    id: UUID
    tenant_id: str
    number: str
    regulation_id: UUID | None = None
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None
    status: AssessmentStatus
    overall_score: Decimal | None = None
    overall_status: ComplianceStatus | None = None
    total_requirements: int
    compliant_count: int
    non_compliant_count: int
    partial_count: int
    lead_assessor_id: UUID | None = None
    findings_summary: str | None = None
    recommendations: str | None = None
    approved_by: UUID | None = None
    approved_at: datetime.datetime | None = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - ÉCARTS
# =============================================================================

class GapBase(BaseModel):
    """Schéma de base pour les écarts."""
    gap_description: str
    root_cause: str | None = None
    impact_description: str | None = None
    severity: RiskLevel = RiskLevel.MEDIUM
    target_closure_date: datetime.date | None = None


class GapCreate(GapBase):
    """Schéma de création d'écart."""
    assessment_id: UUID
    requirement_id: UUID
    evidence_reviewed: list[str] | None = None
    evidence_gaps: str | None = None


class GapResponse(GapBase):
    """Schéma de réponse pour les écarts."""
    id: UUID
    tenant_id: str
    assessment_id: UUID
    requirement_id: UUID
    risk_score: Decimal | None = None
    current_status: ComplianceStatus
    identified_date: datetime.date
    actual_closure_date: datetime.date | None = None
    is_open: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - ACTIONS
# =============================================================================

class ActionBase(BaseModel):
    """Schéma de base pour les actions."""
    title: str = Field(..., max_length=200)
    description: str | None = None
    action_type: str | None = Field(None, max_length=50)
    due_date: datetime.date
    priority: RequirementPriority = RequirementPriority.MEDIUM
    estimated_cost: Decimal | None = Field(None, ge=0)


class ActionCreate(ActionBase):
    """Schéma de création d'action."""
    gap_id: UUID | None = None
    requirement_id: UUID | None = None
    responsible_id: UUID
    department: str | None = Field(None, max_length=100)


class ActionUpdate(BaseModel):
    """Schéma de mise à jour d'action."""
    title: str | None = Field(None, max_length=200)
    description: str | None = None
    due_date: datetime.date | None = None
    status: ActionStatus | None = None
    priority: RequirementPriority | None = None
    progress_percent: int | None = Field(None, ge=0, le=100)
    start_date: datetime.date | None = None
    completion_date: datetime.date | None = None
    resolution_notes: str | None = None
    evidence_provided: list[str] | None = None
    actual_cost: Decimal | None = Field(None, ge=0)


class ActionResponse(ActionBase):
    """Schéma de réponse pour les actions."""
    id: UUID
    tenant_id: str
    number: str
    gap_id: UUID | None = None
    requirement_id: UUID | None = None
    responsible_id: UUID
    department: str | None = None
    status: ActionStatus
    progress_percent: int
    start_date: datetime.date | None = None
    completion_date: datetime.date | None = None
    resolution_notes: str | None = None
    verified_by: UUID | None = None
    verified_at: datetime.datetime | None = None
    actual_cost: Decimal | None = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - POLITIQUES
# =============================================================================

class PolicyBase(BaseModel):
    """Schéma de base pour les politiques."""
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: str | None = None
    document_type: DocumentType = Field(default=DocumentType.POLICY, alias="type")
    category: str | None = Field(None, max_length=100)
    department: str | None = Field(None, max_length=100)
    content: str | None = None
    summary: str | None = None
    effective_date: datetime.date | None = None
    expiry_date: datetime.date | None = None
    requires_acknowledgment: bool = True


class PolicyCreate(PolicyBase):
    """Schéma de création de politique."""
    owner_id: UUID | None = None
    target_audience: list[str] | None = None


class PolicyUpdate(BaseModel):
    """Schéma de mise à jour de politique."""
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    content: str | None = None
    summary: str | None = None
    effective_date: datetime.date | None = None
    expiry_date: datetime.date | None = None
    next_review_date: datetime.date | None = None
    requires_acknowledgment: bool | None = None
    is_published: bool | None = None
    is_active: bool | None = None


class PolicyResponse(PolicyBase):
    """Schéma de réponse pour les politiques."""
    id: UUID
    tenant_id: str
    version: str
    version_date: datetime.date | None = None
    next_review_date: datetime.date | None = None
    owner_id: UUID | None = None
    approved_by: UUID | None = None
    approved_at: datetime.datetime | None = None
    is_published: bool
    is_active: bool
    file_name: str | None = None
    acknowledgments_count: int | None = 0
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - ACCUSÉS DE RÉCEPTION
# =============================================================================

class AcknowledgmentCreate(BaseModel):
    """Schéma de création d'accusé de réception."""
    policy_id: UUID
    notes: str | None = None


class AcknowledgmentResponse(BaseModel):
    """Schéma de réponse pour les accusés de réception."""
    id: UUID
    tenant_id: str
    policy_id: UUID
    user_id: UUID
    acknowledged_at: datetime.datetime
    is_valid: bool

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - FORMATIONS
# =============================================================================

class TrainingBase(BaseModel):
    """Schéma de base pour les formations."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: str | None = None
    content_type: str | None = Field(None, max_length=50)
    duration_hours: Decimal | None = Field(None, ge=0)
    passing_score: int | None = Field(None, ge=0, le=100)
    category: str | None = Field(None, max_length=100)
    is_mandatory: bool = True
    recurrence_months: int | None = None


class TrainingCreate(TrainingBase):
    """Schéma de création de formation."""
    regulation_id: UUID | None = None
    target_departments: list[str] | None = None
    target_roles: list[str] | None = None
    available_from: datetime.date | None = None
    available_until: datetime.date | None = None
    materials_url: str | None = None
    quiz_enabled: bool = False


class TrainingUpdate(BaseModel):
    """Schéma de mise à jour de formation."""
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    duration_hours: Decimal | None = Field(None, ge=0)
    passing_score: int | None = Field(None, ge=0, le=100)
    is_mandatory: bool | None = None
    recurrence_months: int | None = None
    available_from: datetime.date | None = None
    available_until: datetime.date | None = None
    is_active: bool | None = None


class TrainingResponse(TrainingBase):
    """Schéma de réponse pour les formations."""
    id: UUID
    tenant_id: str
    regulation_id: UUID | None = None
    target_departments: list[str] | None = None
    target_roles: list[str] | None = None
    available_from: datetime.date | None = None
    available_until: datetime.date | None = None
    is_active: bool
    materials_url: str | None = None
    quiz_enabled: bool
    completions_count: int | None = 0
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - COMPLÉTIONS DE FORMATION
# =============================================================================

class CompletionCreate(BaseModel):
    """Schéma de création de complétion."""
    training_id: UUID
    user_id: UUID
    assigned_date: datetime.date | None = None
    due_date: datetime.date | None = None


class CompletionUpdate(BaseModel):
    """Schéma de mise à jour de complétion."""
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
    score: int | None = Field(None, ge=0, le=100)
    passed: bool | None = None
    certificate_number: str | None = Field(None, max_length=100)
    expiry_date: datetime.date | None = None


class CompletionResponse(BaseModel):
    """Schéma de réponse pour les complétions."""
    id: UUID
    tenant_id: str
    training_id: UUID
    user_id: UUID
    assigned_date: datetime.date | None = None
    due_date: datetime.date | None = None
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
    score: int | None = None
    passed: bool | None = None
    attempts: int
    certificate_number: str | None = None
    expiry_date: datetime.date | None = None
    is_current: bool

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - DOCUMENTS
# =============================================================================

class DocumentBase(BaseModel):
    """Schéma de base pour les documents."""
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: str | None = None
    document_type: DocumentType = Field(..., alias="type")
    category: str | None = Field(None, max_length=100)
    effective_date: datetime.date | None = None
    expiry_date: datetime.date | None = None


class DocumentCreate(DocumentBase):
    """Schéma de création de document."""
    regulation_id: UUID | None = None
    owner_id: UUID | None = None
    department: str | None = Field(None, max_length=100)
    next_review_date: datetime.date | None = None
    is_controlled: bool = True
    tags: list[str] | None = None
    external_reference: str | None = Field(None, max_length=200)


class DocumentUpdate(BaseModel):
    """Schéma de mise à jour de document."""
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    effective_date: datetime.date | None = None
    expiry_date: datetime.date | None = None
    next_review_date: datetime.date | None = None
    owner_id: UUID | None = None
    is_active: bool | None = None
    tags: list[str] | None = None


class DocumentResponse(DocumentBase):
    """Schéma de réponse pour les documents."""
    id: UUID
    tenant_id: str
    regulation_id: UUID | None = None
    version: str
    version_date: datetime.date
    next_review_date: datetime.date | None = None
    owner_id: UUID | None = None
    department: str | None = None
    approved_by: UUID | None = None
    approved_at: datetime.datetime | None = None
    is_active: bool
    is_controlled: bool
    file_name: str | None = None
    file_size: int | None = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - AUDITS
# =============================================================================

class AuditBase(BaseModel):
    """Schéma de base pour les audits."""
    name: str = Field(..., max_length=200)
    description: str | None = None
    audit_type: str = Field(..., max_length=50)
    scope: str | None = None
    planned_start: datetime.date | None = None
    planned_end: datetime.date | None = None


class AuditCreate(AuditBase):
    """Schéma de création d'audit."""
    regulation_id: UUID | None = None
    departments: list[str] | None = None
    lead_auditor_id: UUID | None = None
    auditor_ids: list[UUID] | None = None
    auditee_ids: list[UUID] | None = None


class AuditUpdate(BaseModel):
    """Schéma de mise à jour d'audit."""
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    scope: str | None = None
    planned_start: datetime.date | None = None
    planned_end: datetime.date | None = None
    actual_start: datetime.date | None = None
    actual_end: datetime.date | None = None
    status: AuditStatus | None = None
    executive_summary: str | None = None
    conclusions: str | None = None
    recommendations: str | None = None


class AuditResponse(AuditBase):
    """Schéma de réponse pour les audits."""
    id: UUID
    tenant_id: str
    number: str
    regulation_id: UUID | None = None
    departments: list[str] | None = None
    actual_start: datetime.date | None = None
    actual_end: datetime.date | None = None
    status: AuditStatus
    lead_auditor_id: UUID | None = None
    total_findings: int
    critical_findings: int
    major_findings: int
    minor_findings: int
    observations: int
    executive_summary: str | None = None
    conclusions: str | None = None
    recommendations: str | None = None
    approved_by: UUID | None = None
    approved_at: datetime.datetime | None = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - CONSTATATIONS D'AUDIT
# =============================================================================

class FindingBase(BaseModel):
    """Schéma de base pour les constatations."""
    title: str = Field(..., max_length=200)
    description: str
    severity: FindingSeverity = FindingSeverity.OBSERVATION
    category: str | None = Field(None, max_length=100)
    evidence: str | None = None
    root_cause: str | None = None
    recommendation: str | None = None


class FindingCreate(FindingBase):
    """Schéma de création de constatation."""
    audit_id: UUID
    requirement_id: UUID | None = None
    response_due_date: datetime.date | None = None
    responsible_id: UUID | None = None


class FindingUpdate(BaseModel):
    """Schéma de mise à jour de constatation."""
    title: str | None = Field(None, max_length=200)
    description: str | None = None
    severity: FindingSeverity | None = None
    evidence: str | None = None
    root_cause: str | None = None
    recommendation: str | None = None
    response: str | None = None
    response_date: datetime.date | None = None
    is_closed: bool | None = None
    closure_date: datetime.date | None = None


class FindingResponse(FindingBase):
    """Schéma de réponse pour les constatations."""
    id: UUID
    tenant_id: str
    number: str
    audit_id: UUID
    requirement_id: UUID | None = None
    identified_date: datetime.date
    response_due_date: datetime.date | None = None
    closure_date: datetime.date | None = None
    responsible_id: UUID | None = None
    is_closed: bool
    response: str | None = None
    response_date: datetime.date | None = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - RISQUES
# =============================================================================

class RiskBase(BaseModel):
    """Schéma de base pour les risques."""
    code: str = Field(..., max_length=50)
    title: str = Field(..., max_length=200)
    description: str | None = None
    category: str | None = Field(None, max_length=100)
    likelihood: int = Field(..., ge=1, le=5)
    impact: int = Field(..., ge=1, le=5)


class RiskCreate(RiskBase):
    """Schéma de création de risque."""
    regulation_id: UUID | None = None
    treatment_strategy: str | None = Field(None, max_length=50)
    treatment_description: str | None = None
    current_controls: str | None = None
    planned_controls: str | None = None
    owner_id: UUID | None = None
    department: str | None = Field(None, max_length=100)


class RiskUpdate(BaseModel):
    """Schéma de mise à jour de risque."""
    title: str | None = Field(None, max_length=200)
    description: str | None = None
    category: str | None = Field(None, max_length=100)
    likelihood: int | None = Field(None, ge=1, le=5)
    impact: int | None = Field(None, ge=1, le=5)
    residual_likelihood: int | None = Field(None, ge=1, le=5)
    residual_impact: int | None = Field(None, ge=1, le=5)
    treatment_strategy: str | None = Field(None, max_length=50)
    treatment_description: str | None = None
    current_controls: str | None = None
    planned_controls: str | None = None
    owner_id: UUID | None = None
    is_accepted: bool | None = None
    is_active: bool | None = None


class RiskResponse(RiskBase):
    """Schéma de réponse pour les risques."""
    id: UUID
    tenant_id: str
    regulation_id: UUID | None = None
    risk_score: int
    risk_level: RiskLevel
    residual_likelihood: int | None = None
    residual_impact: int | None = None
    residual_score: int | None = None
    residual_level: RiskLevel | None = None
    treatment_strategy: str | None = None
    treatment_description: str | None = None
    current_controls: str | None = None
    planned_controls: str | None = None
    owner_id: UUID | None = None
    department: str | None = None
    identified_date: datetime.date
    last_review_date: datetime.date | None = None
    next_review_date: datetime.date | None = None
    is_active: bool
    is_accepted: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - INCIDENTS
# =============================================================================

class IncidentBase(BaseModel):
    """Schéma de base pour les incidents."""
    title: str = Field(..., max_length=200)
    description: str
    incident_type: str | None = Field(None, max_length=100)
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    incident_date: datetime.datetime


class IncidentCreate(IncidentBase):
    """Schéma de création d'incident."""
    regulation_id: UUID | None = None
    department: str | None = Field(None, max_length=100)


class IncidentUpdate(BaseModel):
    """Schéma de mise à jour d'incident."""
    title: str | None = Field(None, max_length=200)
    description: str | None = None
    severity: IncidentSeverity | None = None
    status: IncidentStatus | None = None
    assigned_to: UUID | None = None
    investigation_notes: str | None = None
    root_cause: str | None = None
    impact_assessment: str | None = None
    resolution: str | None = None
    lessons_learned: str | None = None
    resolved_date: datetime.datetime | None = None
    requires_disclosure: bool | None = None


class IncidentResponse(IncidentBase):
    """Schéma de réponse pour les incidents."""
    id: UUID
    tenant_id: str
    number: str
    regulation_id: UUID | None = None
    reporter_id: UUID
    assigned_to: UUID | None = None
    department: str | None = None
    status: IncidentStatus
    reported_date: datetime.datetime
    resolved_date: datetime.datetime | None = None
    closed_date: datetime.datetime | None = None
    investigation_notes: str | None = None
    root_cause: str | None = None
    resolution: str | None = None
    requires_disclosure: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - RAPPORTS
# =============================================================================

class ReportBase(BaseModel):
    """Schéma de base pour les rapports."""
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., max_length=200)
    description: str | None = None
    report_type: ReportType = Field(..., alias="type")
    period_start: datetime.date | None = None
    period_end: datetime.date | None = None


class ReportCreate(ReportBase):
    """Schéma de création de rapport."""
    regulation_ids: list[UUID] | None = None
    department_ids: list[str] | None = None


class ReportResponse(ReportBase):
    """Schéma de réponse pour les rapports."""
    id: UUID
    tenant_id: str
    number: str
    executive_summary: str | None = None
    content: dict[str, Any] | None = None
    metrics: dict[str, Any] | None = None
    file_name: str | None = None
    is_published: bool
    published_at: datetime.datetime | None = None
    approved_by: UUID | None = None
    approved_at: datetime.datetime | None = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - DASHBOARDS
# =============================================================================

class ComplianceMetrics(BaseModel):
    """Métriques de conformité."""
    overall_compliance_rate: Decimal
    compliant_requirements: int
    non_compliant_requirements: int
    partial_requirements: int
    pending_requirements: int
    total_requirements: int

    open_gaps: int
    open_actions: int
    overdue_actions: int

    active_audits: int
    open_findings: int
    critical_findings: int

    active_risks: int
    high_risks: int
    critical_risks: int

    open_incidents: int
    training_compliance_rate: Decimal
    policies_requiring_acknowledgment: int


class ComplianceDashboard(BaseModel):
    """Tableau de bord conformité."""
    metrics: ComplianceMetrics
    compliance_by_regulation: list[dict[str, Any]]
    compliance_trend: list[dict[str, Any]]
    upcoming_assessments: list[AssessmentResponse]
    overdue_actions: list[ActionResponse]
    recent_incidents: list[IncidentResponse]
    high_risks: list[RiskResponse]


class ComplianceStatusSummary(BaseModel):
    """Résumé du statut de conformité."""
    regulation_id: UUID | None = None
    regulation_name: str | None = None
    total_requirements: int
    compliant: int
    non_compliant: int
    partial: int
    pending: int
    compliance_rate: Decimal
    last_assessment_date: datetime.date | None = None
    next_assessment_date: datetime.date | None = None


class TrainingStatusSummary(BaseModel):
    """Résumé du statut des formations."""
    total_employees: int
    employees_trained: int
    employees_pending: int
    employees_overdue: int
    compliance_rate: Decimal
    trainings_by_status: dict[str, int]
