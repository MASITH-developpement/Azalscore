"""
AZALS MODULE M11 - Schémas Conformité
=====================================

Schémas Pydantic pour la gestion de la conformité réglementaire.
"""

from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Any, Dict
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from .models import (
    ComplianceStatus, RegulationType, RequirementPriority,
    AssessmentStatus, RiskLevel, ActionStatus, DocumentType,
    AuditStatus, FindingSeverity, IncidentSeverity, IncidentStatus, ReportType
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
    version: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    scope: Optional[str] = None
    authority: Optional[str] = Field(None, max_length=200)
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    next_review_date: Optional[date] = None
    is_mandatory: bool = True
    external_reference: Optional[str] = Field(None, max_length=200)
    source_url: Optional[str] = None
    notes: Optional[str] = None


class RegulationCreate(RegulationBase):
    """Schéma de création de réglementation."""
    pass


class RegulationUpdate(BaseModel):
    """Schéma de mise à jour de réglementation."""
    name: Optional[str] = Field(None, max_length=200)
    version: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    scope: Optional[str] = None
    authority: Optional[str] = Field(None, max_length=200)
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    next_review_date: Optional[date] = None
    is_mandatory: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class RegulationResponse(RegulationBase):
    """Schéma de réponse pour les réglementations."""
    id: UUID
    tenant_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    requirements_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - EXIGENCES
# =============================================================================

class RequirementBase(BaseModel):
    """Schéma de base pour les exigences."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    priority: RequirementPriority = RequirementPriority.MEDIUM
    category: Optional[str] = Field(None, max_length=100)
    clause_reference: Optional[str] = Field(None, max_length=100)
    target_score: Decimal = Field(default=Decimal("100"), ge=0, le=100)
    control_frequency: Optional[str] = Field(None, max_length=50)
    evidence_required: Optional[List[str]] = None
    is_key_control: bool = False


class RequirementCreate(RequirementBase):
    """Schéma de création d'exigence."""
    regulation_id: UUID
    parent_id: Optional[UUID] = None
    responsible_id: Optional[UUID] = None
    department: Optional[str] = Field(None, max_length=100)
    next_assessment: Optional[date] = None


class RequirementUpdate(BaseModel):
    """Schéma de mise à jour d'exigence."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    priority: Optional[RequirementPriority] = None
    category: Optional[str] = Field(None, max_length=100)
    compliance_status: Optional[ComplianceStatus] = None
    current_score: Optional[Decimal] = Field(None, ge=0, le=100)
    target_score: Optional[Decimal] = Field(None, ge=0, le=100)
    responsible_id: Optional[UUID] = None
    control_frequency: Optional[str] = Field(None, max_length=50)
    next_assessment: Optional[date] = None
    is_active: Optional[bool] = None


class RequirementResponse(RequirementBase):
    """Schéma de réponse pour les exigences."""
    id: UUID
    tenant_id: str
    regulation_id: UUID
    parent_id: Optional[UUID] = None
    compliance_status: ComplianceStatus
    current_score: Optional[Decimal] = None
    responsible_id: Optional[UUID] = None
    department: Optional[str] = None
    last_assessed: Optional[datetime] = None
    next_assessment: Optional[date] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - ÉVALUATIONS
# =============================================================================

class AssessmentBase(BaseModel):
    """Schéma de base pour les évaluations."""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    assessment_type: Optional[str] = Field(None, max_length=50)
    scope_description: Optional[str] = None
    planned_date: Optional[date] = None


class AssessmentCreate(AssessmentBase):
    """Schéma de création d'évaluation."""
    regulation_id: Optional[UUID] = None
    lead_assessor_id: Optional[UUID] = None
    assessor_ids: Optional[List[UUID]] = None


class AssessmentUpdate(BaseModel):
    """Schéma de mise à jour d'évaluation."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    scope_description: Optional[str] = None
    planned_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[AssessmentStatus] = None
    overall_score: Optional[Decimal] = Field(None, ge=0, le=100)
    overall_status: Optional[ComplianceStatus] = None
    findings_summary: Optional[str] = None
    recommendations: Optional[str] = None


class AssessmentResponse(AssessmentBase):
    """Schéma de réponse pour les évaluations."""
    id: UUID
    tenant_id: str
    number: str
    regulation_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: AssessmentStatus
    overall_score: Optional[Decimal] = None
    overall_status: Optional[ComplianceStatus] = None
    total_requirements: int
    compliant_count: int
    non_compliant_count: int
    partial_count: int
    lead_assessor_id: Optional[UUID] = None
    findings_summary: Optional[str] = None
    recommendations: Optional[str] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - ÉCARTS
# =============================================================================

class GapBase(BaseModel):
    """Schéma de base pour les écarts."""
    gap_description: str
    root_cause: Optional[str] = None
    impact_description: Optional[str] = None
    severity: RiskLevel = RiskLevel.MEDIUM
    target_closure_date: Optional[date] = None


class GapCreate(GapBase):
    """Schéma de création d'écart."""
    assessment_id: UUID
    requirement_id: UUID
    evidence_reviewed: Optional[List[str]] = None
    evidence_gaps: Optional[str] = None


class GapResponse(GapBase):
    """Schéma de réponse pour les écarts."""
    id: UUID
    tenant_id: str
    assessment_id: UUID
    requirement_id: UUID
    risk_score: Optional[Decimal] = None
    current_status: ComplianceStatus
    identified_date: date
    actual_closure_date: Optional[date] = None
    is_open: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - ACTIONS
# =============================================================================

class ActionBase(BaseModel):
    """Schéma de base pour les actions."""
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    action_type: Optional[str] = Field(None, max_length=50)
    due_date: date
    priority: RequirementPriority = RequirementPriority.MEDIUM
    estimated_cost: Optional[Decimal] = Field(None, ge=0)


class ActionCreate(ActionBase):
    """Schéma de création d'action."""
    gap_id: Optional[UUID] = None
    requirement_id: Optional[UUID] = None
    responsible_id: UUID
    department: Optional[str] = Field(None, max_length=100)


class ActionUpdate(BaseModel):
    """Schéma de mise à jour d'action."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[ActionStatus] = None
    priority: Optional[RequirementPriority] = None
    progress_percent: Optional[int] = Field(None, ge=0, le=100)
    start_date: Optional[date] = None
    completion_date: Optional[date] = None
    resolution_notes: Optional[str] = None
    evidence_provided: Optional[List[str]] = None
    actual_cost: Optional[Decimal] = Field(None, ge=0)


class ActionResponse(ActionBase):
    """Schéma de réponse pour les actions."""
    id: UUID
    tenant_id: str
    number: str
    gap_id: Optional[UUID] = None
    requirement_id: Optional[UUID] = None
    responsible_id: UUID
    department: Optional[str] = None
    status: ActionStatus
    progress_percent: int
    start_date: Optional[date] = None
    completion_date: Optional[date] = None
    resolution_notes: Optional[str] = None
    verified_by: Optional[UUID] = None
    verified_at: Optional[datetime] = None
    actual_cost: Optional[Decimal] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - POLITIQUES
# =============================================================================

class PolicyBase(BaseModel):
    """Schéma de base pour les politiques."""
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    document_type: DocumentType = Field(default=DocumentType.POLICY, alias="type")
    category: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    content: Optional[str] = None
    summary: Optional[str] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    requires_acknowledgment: bool = True


class PolicyCreate(PolicyBase):
    """Schéma de création de politique."""
    owner_id: Optional[UUID] = None
    target_audience: Optional[List[str]] = None


class PolicyUpdate(BaseModel):
    """Schéma de mise à jour de politique."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    next_review_date: Optional[date] = None
    requires_acknowledgment: Optional[bool] = None
    is_published: Optional[bool] = None
    is_active: Optional[bool] = None


class PolicyResponse(PolicyBase):
    """Schéma de réponse pour les politiques."""
    id: UUID
    tenant_id: str
    version: str
    version_date: Optional[date] = None
    next_review_date: Optional[date] = None
    owner_id: Optional[UUID] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    is_published: bool
    is_active: bool
    file_name: Optional[str] = None
    acknowledgments_count: Optional[int] = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - ACCUSÉS DE RÉCEPTION
# =============================================================================

class AcknowledgmentCreate(BaseModel):
    """Schéma de création d'accusé de réception."""
    policy_id: UUID
    notes: Optional[str] = None


class AcknowledgmentResponse(BaseModel):
    """Schéma de réponse pour les accusés de réception."""
    id: UUID
    tenant_id: str
    policy_id: UUID
    user_id: UUID
    acknowledged_at: datetime
    is_valid: bool

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - FORMATIONS
# =============================================================================

class TrainingBase(BaseModel):
    """Schéma de base pour les formations."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    content_type: Optional[str] = Field(None, max_length=50)
    duration_hours: Optional[Decimal] = Field(None, ge=0)
    passing_score: Optional[int] = Field(None, ge=0, le=100)
    category: Optional[str] = Field(None, max_length=100)
    is_mandatory: bool = True
    recurrence_months: Optional[int] = None


class TrainingCreate(TrainingBase):
    """Schéma de création de formation."""
    regulation_id: Optional[UUID] = None
    target_departments: Optional[List[str]] = None
    target_roles: Optional[List[str]] = None
    available_from: Optional[date] = None
    available_until: Optional[date] = None
    materials_url: Optional[str] = None
    quiz_enabled: bool = False


class TrainingUpdate(BaseModel):
    """Schéma de mise à jour de formation."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    duration_hours: Optional[Decimal] = Field(None, ge=0)
    passing_score: Optional[int] = Field(None, ge=0, le=100)
    is_mandatory: Optional[bool] = None
    recurrence_months: Optional[int] = None
    available_from: Optional[date] = None
    available_until: Optional[date] = None
    is_active: Optional[bool] = None


class TrainingResponse(TrainingBase):
    """Schéma de réponse pour les formations."""
    id: UUID
    tenant_id: str
    regulation_id: Optional[UUID] = None
    target_departments: Optional[List[str]] = None
    target_roles: Optional[List[str]] = None
    available_from: Optional[date] = None
    available_until: Optional[date] = None
    is_active: bool
    materials_url: Optional[str] = None
    quiz_enabled: bool
    completions_count: Optional[int] = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - COMPLÉTIONS DE FORMATION
# =============================================================================

class CompletionCreate(BaseModel):
    """Schéma de création de complétion."""
    training_id: UUID
    user_id: UUID
    assigned_date: Optional[date] = None
    due_date: Optional[date] = None


class CompletionUpdate(BaseModel):
    """Schéma de mise à jour de complétion."""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    score: Optional[int] = Field(None, ge=0, le=100)
    passed: Optional[bool] = None
    certificate_number: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[date] = None


class CompletionResponse(BaseModel):
    """Schéma de réponse pour les complétions."""
    id: UUID
    tenant_id: str
    training_id: UUID
    user_id: UUID
    assigned_date: Optional[date] = None
    due_date: Optional[date] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    score: Optional[int] = None
    passed: Optional[bool] = None
    attempts: int
    certificate_number: Optional[str] = None
    expiry_date: Optional[date] = None
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
    description: Optional[str] = None
    document_type: DocumentType = Field(..., alias="type")
    category: Optional[str] = Field(None, max_length=100)
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None


class DocumentCreate(DocumentBase):
    """Schéma de création de document."""
    regulation_id: Optional[UUID] = None
    owner_id: Optional[UUID] = None
    department: Optional[str] = Field(None, max_length=100)
    next_review_date: Optional[date] = None
    is_controlled: bool = True
    tags: Optional[List[str]] = None
    external_reference: Optional[str] = Field(None, max_length=200)


class DocumentUpdate(BaseModel):
    """Schéma de mise à jour de document."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    next_review_date: Optional[date] = None
    owner_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None


class DocumentResponse(DocumentBase):
    """Schéma de réponse pour les documents."""
    id: UUID
    tenant_id: str
    regulation_id: Optional[UUID] = None
    version: str
    version_date: date
    next_review_date: Optional[date] = None
    owner_id: Optional[UUID] = None
    department: Optional[str] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    is_active: bool
    is_controlled: bool
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - AUDITS
# =============================================================================

class AuditBase(BaseModel):
    """Schéma de base pour les audits."""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    audit_type: str = Field(..., max_length=50)
    scope: Optional[str] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None


class AuditCreate(AuditBase):
    """Schéma de création d'audit."""
    regulation_id: Optional[UUID] = None
    departments: Optional[List[str]] = None
    lead_auditor_id: Optional[UUID] = None
    auditor_ids: Optional[List[UUID]] = None
    auditee_ids: Optional[List[UUID]] = None


class AuditUpdate(BaseModel):
    """Schéma de mise à jour d'audit."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    scope: Optional[str] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    status: Optional[AuditStatus] = None
    executive_summary: Optional[str] = None
    conclusions: Optional[str] = None
    recommendations: Optional[str] = None


class AuditResponse(AuditBase):
    """Schéma de réponse pour les audits."""
    id: UUID
    tenant_id: str
    number: str
    regulation_id: Optional[UUID] = None
    departments: Optional[List[str]] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    status: AuditStatus
    lead_auditor_id: Optional[UUID] = None
    total_findings: int
    critical_findings: int
    major_findings: int
    minor_findings: int
    observations: int
    executive_summary: Optional[str] = None
    conclusions: Optional[str] = None
    recommendations: Optional[str] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - CONSTATATIONS D'AUDIT
# =============================================================================

class FindingBase(BaseModel):
    """Schéma de base pour les constatations."""
    title: str = Field(..., max_length=200)
    description: str
    severity: FindingSeverity = FindingSeverity.OBSERVATION
    category: Optional[str] = Field(None, max_length=100)
    evidence: Optional[str] = None
    root_cause: Optional[str] = None
    recommendation: Optional[str] = None


class FindingCreate(FindingBase):
    """Schéma de création de constatation."""
    audit_id: UUID
    requirement_id: Optional[UUID] = None
    response_due_date: Optional[date] = None
    responsible_id: Optional[UUID] = None


class FindingUpdate(BaseModel):
    """Schéma de mise à jour de constatation."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    severity: Optional[FindingSeverity] = None
    evidence: Optional[str] = None
    root_cause: Optional[str] = None
    recommendation: Optional[str] = None
    response: Optional[str] = None
    response_date: Optional[date] = None
    is_closed: Optional[bool] = None
    closure_date: Optional[date] = None


class FindingResponse(FindingBase):
    """Schéma de réponse pour les constatations."""
    id: UUID
    tenant_id: str
    number: str
    audit_id: UUID
    requirement_id: Optional[UUID] = None
    identified_date: date
    response_due_date: Optional[date] = None
    closure_date: Optional[date] = None
    responsible_id: Optional[UUID] = None
    is_closed: bool
    response: Optional[str] = None
    response_date: Optional[date] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - RISQUES
# =============================================================================

class RiskBase(BaseModel):
    """Schéma de base pour les risques."""
    code: str = Field(..., max_length=50)
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    likelihood: int = Field(..., ge=1, le=5)
    impact: int = Field(..., ge=1, le=5)


class RiskCreate(RiskBase):
    """Schéma de création de risque."""
    regulation_id: Optional[UUID] = None
    treatment_strategy: Optional[str] = Field(None, max_length=50)
    treatment_description: Optional[str] = None
    current_controls: Optional[str] = None
    planned_controls: Optional[str] = None
    owner_id: Optional[UUID] = None
    department: Optional[str] = Field(None, max_length=100)


class RiskUpdate(BaseModel):
    """Schéma de mise à jour de risque."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    likelihood: Optional[int] = Field(None, ge=1, le=5)
    impact: Optional[int] = Field(None, ge=1, le=5)
    residual_likelihood: Optional[int] = Field(None, ge=1, le=5)
    residual_impact: Optional[int] = Field(None, ge=1, le=5)
    treatment_strategy: Optional[str] = Field(None, max_length=50)
    treatment_description: Optional[str] = None
    current_controls: Optional[str] = None
    planned_controls: Optional[str] = None
    owner_id: Optional[UUID] = None
    is_accepted: Optional[bool] = None
    is_active: Optional[bool] = None


class RiskResponse(RiskBase):
    """Schéma de réponse pour les risques."""
    id: UUID
    tenant_id: str
    regulation_id: Optional[UUID] = None
    risk_score: int
    risk_level: RiskLevel
    residual_likelihood: Optional[int] = None
    residual_impact: Optional[int] = None
    residual_score: Optional[int] = None
    residual_level: Optional[RiskLevel] = None
    treatment_strategy: Optional[str] = None
    treatment_description: Optional[str] = None
    current_controls: Optional[str] = None
    planned_controls: Optional[str] = None
    owner_id: Optional[UUID] = None
    department: Optional[str] = None
    identified_date: date
    last_review_date: Optional[date] = None
    next_review_date: Optional[date] = None
    is_active: bool
    is_accepted: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - INCIDENTS
# =============================================================================

class IncidentBase(BaseModel):
    """Schéma de base pour les incidents."""
    title: str = Field(..., max_length=200)
    description: str
    incident_type: Optional[str] = Field(None, max_length=100)
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    incident_date: datetime


class IncidentCreate(IncidentBase):
    """Schéma de création d'incident."""
    regulation_id: Optional[UUID] = None
    department: Optional[str] = Field(None, max_length=100)


class IncidentUpdate(BaseModel):
    """Schéma de mise à jour d'incident."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    assigned_to: Optional[UUID] = None
    investigation_notes: Optional[str] = None
    root_cause: Optional[str] = None
    impact_assessment: Optional[str] = None
    resolution: Optional[str] = None
    lessons_learned: Optional[str] = None
    resolved_date: Optional[datetime] = None
    requires_disclosure: Optional[bool] = None


class IncidentResponse(IncidentBase):
    """Schéma de réponse pour les incidents."""
    id: UUID
    tenant_id: str
    number: str
    regulation_id: Optional[UUID] = None
    reporter_id: UUID
    assigned_to: Optional[UUID] = None
    department: Optional[str] = None
    status: IncidentStatus
    reported_date: datetime
    resolved_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None
    investigation_notes: Optional[str] = None
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    requires_disclosure: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHÉMAS - RAPPORTS
# =============================================================================

class ReportBase(BaseModel):
    """Schéma de base pour les rapports."""
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    report_type: ReportType = Field(..., alias="type")
    period_start: Optional[date] = None
    period_end: Optional[date] = None


class ReportCreate(ReportBase):
    """Schéma de création de rapport."""
    regulation_ids: Optional[List[UUID]] = None
    department_ids: Optional[List[str]] = None


class ReportResponse(ReportBase):
    """Schéma de réponse pour les rapports."""
    id: UUID
    tenant_id: str
    number: str
    executive_summary: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    file_name: Optional[str] = None
    is_published: bool
    published_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime

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
    compliance_by_regulation: List[Dict[str, Any]]
    compliance_trend: List[Dict[str, Any]]
    upcoming_assessments: List[AssessmentResponse]
    overdue_actions: List[ActionResponse]
    recent_incidents: List[IncidentResponse]
    high_risks: List[RiskResponse]


class ComplianceStatusSummary(BaseModel):
    """Résumé du statut de conformité."""
    regulation_id: Optional[UUID] = None
    regulation_name: Optional[str] = None
    total_requirements: int
    compliant: int
    non_compliant: int
    partial: int
    pending: int
    compliance_rate: Decimal
    last_assessment_date: Optional[date] = None
    next_assessment_date: Optional[date] = None


class TrainingStatusSummary(BaseModel):
    """Résumé du statut des formations."""
    total_employees: int
    employees_trained: int
    employees_pending: int
    employees_overdue: int
    compliance_rate: Decimal
    trainings_by_status: Dict[str, int]
