"""
AZALS MODULE M7 - Schémas Pydantic Qualité
==========================================

Schémas de validation pour les API du module Qualité.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# ENUMS
# ============================================================================

class NonConformanceTypeEnum(str, Enum):
    PRODUCT = "PRODUCT"
    PROCESS = "PROCESS"
    SERVICE = "SERVICE"
    SUPPLIER = "SUPPLIER"
    CUSTOMER = "CUSTOMER"
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"
    AUDIT = "AUDIT"
    REGULATORY = "REGULATORY"


class NonConformanceStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    UNDER_ANALYSIS = "UNDER_ANALYSIS"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    IN_PROGRESS = "IN_PROGRESS"
    VERIFICATION = "VERIFICATION"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class NonConformanceSeverityEnum(str, Enum):
    MINOR = "MINOR"
    MAJOR = "MAJOR"
    CRITICAL = "CRITICAL"
    BLOCKING = "BLOCKING"


class ControlTypeEnum(str, Enum):
    INCOMING = "INCOMING"
    IN_PROCESS = "IN_PROCESS"
    FINAL = "FINAL"
    OUTGOING = "OUTGOING"
    SAMPLING = "SAMPLING"
    DESTRUCTIVE = "DESTRUCTIVE"
    NON_DESTRUCTIVE = "NON_DESTRUCTIVE"
    VISUAL = "VISUAL"
    DIMENSIONAL = "DIMENSIONAL"
    FUNCTIONAL = "FUNCTIONAL"
    LABORATORY = "LABORATORY"


class ControlStatusEnum(str, Enum):
    PLANNED = "PLANNED"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ControlResultEnum(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    CONDITIONAL = "CONDITIONAL"
    PENDING = "PENDING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AuditTypeEnum(str, Enum):
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"
    SUPPLIER = "SUPPLIER"
    CUSTOMER = "CUSTOMER"
    CERTIFICATION = "CERTIFICATION"
    SURVEILLANCE = "SURVEILLANCE"
    PROCESS = "PROCESS"
    PRODUCT = "PRODUCT"
    SYSTEM = "SYSTEM"


class AuditStatusEnum(str, Enum):
    PLANNED = "PLANNED"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REPORT_PENDING = "REPORT_PENDING"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class FindingSeverityEnum(str, Enum):
    OBSERVATION = "OBSERVATION"
    MINOR = "MINOR"
    MAJOR = "MAJOR"
    CRITICAL = "CRITICAL"


class CAPATypeEnum(str, Enum):
    CORRECTIVE = "CORRECTIVE"
    PREVENTIVE = "PREVENTIVE"
    IMPROVEMENT = "IMPROVEMENT"


class CAPAStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    ANALYSIS = "ANALYSIS"
    ACTION_PLANNING = "ACTION_PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    VERIFICATION = "VERIFICATION"
    CLOSED_EFFECTIVE = "CLOSED_EFFECTIVE"
    CLOSED_INEFFECTIVE = "CLOSED_INEFFECTIVE"
    CANCELLED = "CANCELLED"


class ClaimStatusEnum(str, Enum):
    RECEIVED = "RECEIVED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    PENDING_RESPONSE = "PENDING_RESPONSE"
    RESPONSE_SENT = "RESPONSE_SENT"
    IN_RESOLUTION = "IN_RESOLUTION"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


class CertificationStatusEnum(str, Enum):
    PLANNED = "PLANNED"
    IN_PREPARATION = "IN_PREPARATION"
    AUDIT_SCHEDULED = "AUDIT_SCHEDULED"
    AUDIT_COMPLETED = "AUDIT_COMPLETED"
    CERTIFIED = "CERTIFIED"
    SUSPENDED = "SUSPENDED"
    WITHDRAWN = "WITHDRAWN"
    EXPIRED = "EXPIRED"


# ============================================================================
# NON-CONFORMITÉS
# ============================================================================

class NonConformanceBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    description: str | None = None
    nc_type: NonConformanceTypeEnum
    severity: NonConformanceSeverityEnum
    detected_date: date
    detection_location: str | None = None
    detection_phase: str | None = None


class NonConformanceCreate(NonConformanceBase):
    source_type: str | None = None
    source_reference: str | None = None
    source_id: int | None = None
    product_id: int | None = None
    lot_number: str | None = None
    serial_number: str | None = None
    quantity_affected: Decimal | None = None
    unit_id: int | None = None
    supplier_id: int | None = None
    customer_id: int | None = None
    immediate_action: str | None = None
    responsible_id: int | None = None
    department: str | None = None
    notes: str | None = None


class NonConformanceUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=300)
    description: str | None = None
    severity: NonConformanceSeverityEnum | None = None
    status: NonConformanceStatusEnum | None = None

    # Analyse des causes
    immediate_cause: str | None = None
    root_cause: str | None = None
    cause_analysis_method: str | None = None

    # Impact
    impact_description: str | None = None
    estimated_cost: Decimal | None = None
    actual_cost: Decimal | None = None

    # Traitement
    immediate_action: str | None = None
    disposition: str | None = None
    disposition_justification: str | None = None

    # CAPA
    capa_required: bool | None = None
    capa_id: int | None = None

    # Responsable
    responsible_id: int | None = None
    department: str | None = None

    notes: str | None = None


class NonConformanceClose(BaseModel):
    closure_justification: str = Field(..., min_length=10)
    effectiveness_verified: bool = False


class NonConformanceActionCreate(BaseModel):
    action_type: str = Field(..., min_length=2, max_length=50)
    description: str = Field(..., min_length=10)
    responsible_id: int | None = None
    planned_date: date | None = None
    due_date: date | None = None
    comments: str | None = None


class NonConformanceActionUpdate(BaseModel):
    description: str | None = None
    responsible_id: int | None = None
    due_date: date | None = None
    status: str | None = None
    completed_date: date | None = None
    comments: str | None = None


class NonConformanceActionResponse(BaseModel):
    id: int
    nc_id: int
    action_number: int
    action_type: str
    description: str
    responsible_id: int | None = None
    planned_date: date | None = None
    due_date: date | None = None
    completed_date: date | None = None
    status: str
    verified: bool
    verified_date: date | None = None
    comments: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NonConformanceResponse(NonConformanceBase):
    id: int
    nc_number: str
    status: NonConformanceStatusEnum
    detected_by_id: int | None = None
    source_type: str | None = None
    source_reference: str | None = None
    product_id: int | None = None
    lot_number: str | None = None
    quantity_affected: Decimal | None = None
    supplier_id: int | None = None
    customer_id: int | None = None

    immediate_cause: str | None = None
    root_cause: str | None = None
    cause_analysis_method: str | None = None

    impact_description: str | None = None
    estimated_cost: Decimal | None = None
    actual_cost: Decimal | None = None

    immediate_action: str | None = None
    disposition: str | None = None

    responsible_id: int | None = None
    department: str | None = None

    capa_required: bool
    capa_id: int | None = None

    closed_date: date | None = None
    effectiveness_verified: bool

    is_recurrent: bool
    recurrence_count: int

    actions: list[NonConformanceActionResponse] = []

    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TEMPLATES DE CONTRÔLE QUALITÉ
# ============================================================================

class ControlTemplateItemBase(BaseModel):
    sequence: int
    characteristic: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    measurement_type: str = Field(..., min_length=2, max_length=50)
    unit: str | None = None
    nominal_value: Decimal | None = None
    tolerance_min: Decimal | None = None
    tolerance_max: Decimal | None = None
    expected_result: str | None = None
    measurement_method: str | None = None
    equipment_code: str | None = None
    is_critical: bool = False
    is_mandatory: bool = True
    sampling_frequency: str | None = None


class ControlTemplateItemCreate(ControlTemplateItemBase):
    pass


class ControlTemplateItemResponse(ControlTemplateItemBase):
    id: int
    template_id: int
    upper_limit: Decimal | None = None
    lower_limit: Decimal | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ControlTemplateBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    version: str = "1.0"
    control_type: ControlTypeEnum


class ControlTemplateCreate(ControlTemplateBase):
    applies_to: str | None = None
    product_category_id: int | None = None
    instructions: str | None = None
    sampling_plan: str | None = None
    acceptance_criteria: str | None = None
    estimated_duration_minutes: int | None = None
    required_equipment: list[str] | None = None
    items: list[ControlTemplateItemCreate] | None = None


class ControlTemplateUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    version: str | None = None
    instructions: str | None = None
    sampling_plan: str | None = None
    acceptance_criteria: str | None = None
    estimated_duration_minutes: int | None = None
    is_active: bool | None = None


class ControlTemplateResponse(ControlTemplateBase):
    id: int
    applies_to: str | None = None
    product_category_id: int | None = None
    instructions: str | None = None
    sampling_plan: str | None = None
    acceptance_criteria: str | None = None
    estimated_duration_minutes: int | None = None
    required_equipment: list[str] | None = None
    is_active: bool
    valid_from: date | None = None
    valid_until: date | None = None
    items: list[ControlTemplateItemResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CONTRÔLES QUALITÉ
# ============================================================================

class ControlLineBase(BaseModel):
    sequence: int
    characteristic: str = Field(..., min_length=2, max_length=200)
    nominal_value: Decimal | None = None
    tolerance_min: Decimal | None = None
    tolerance_max: Decimal | None = None
    unit: str | None = None


class ControlLineCreate(ControlLineBase):
    template_item_id: int | None = None
    measured_value: Decimal | None = None
    measured_text: str | None = None
    measured_boolean: bool | None = None
    result: ControlResultEnum | None = None
    equipment_code: str | None = None
    comments: str | None = None


class ControlLineUpdate(BaseModel):
    measured_value: Decimal | None = None
    measured_text: str | None = None
    measured_boolean: bool | None = None
    result: ControlResultEnum | None = None
    equipment_code: str | None = None
    comments: str | None = None


class ControlLineResponse(ControlLineBase):
    id: int
    control_id: int
    template_item_id: int | None = None
    measured_value: Decimal | None = None
    measured_text: str | None = None
    measured_boolean: bool | None = None
    measurement_date: datetime | None = None
    result: ControlResultEnum | None = None
    deviation: Decimal | None = None
    equipment_code: str | None = None
    comments: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ControlBase(BaseModel):
    control_type: ControlTypeEnum
    control_date: date


class ControlCreate(ControlBase):
    template_id: int | None = None
    source_type: str | None = None
    source_reference: str | None = None
    source_id: int | None = None
    product_id: int | None = None
    lot_number: str | None = None
    serial_number: str | None = None
    quantity_to_control: Decimal | None = None
    unit_id: int | None = None
    supplier_id: int | None = None
    customer_id: int | None = None
    location: str | None = None
    controller_id: int | None = None
    observations: str | None = None
    lines: list[ControlLineCreate] | None = None


class ControlUpdate(BaseModel):
    control_date: date | None = None
    quantity_controlled: Decimal | None = None
    quantity_conforming: Decimal | None = None
    quantity_non_conforming: Decimal | None = None
    location: str | None = None
    controller_id: int | None = None
    status: ControlStatusEnum | None = None
    result: ControlResultEnum | None = None
    decision: str | None = None
    decision_comments: str | None = None
    observations: str | None = None


class ControlResponse(ControlBase):
    id: int
    control_number: str
    template_id: int | None = None
    source_type: str | None = None
    source_reference: str | None = None
    product_id: int | None = None
    lot_number: str | None = None
    serial_number: str | None = None
    quantity_to_control: Decimal | None = None
    quantity_controlled: Decimal | None = None
    quantity_conforming: Decimal | None = None
    quantity_non_conforming: Decimal | None = None
    supplier_id: int | None = None
    customer_id: int | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    location: str | None = None
    controller_id: int | None = None
    status: ControlStatusEnum
    result: ControlResultEnum | None = None
    result_date: datetime | None = None
    decision: str | None = None
    decision_by_id: int | None = None
    decision_date: datetime | None = None
    decision_comments: str | None = None
    nc_id: int | None = None
    observations: str | None = None
    lines: list[ControlLineResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# AUDITS
# ============================================================================

class AuditFindingBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=300)
    description: str = Field(..., min_length=10)
    severity: FindingSeverityEnum
    category: str | None = None
    clause_reference: str | None = None
    process_reference: str | None = None


class AuditFindingCreate(AuditFindingBase):
    evidence: str | None = None
    risk_description: str | None = None
    capa_required: bool = False
    action_due_date: date | None = None


class AuditFindingUpdate(BaseModel):
    title: str | None = Field(None, min_length=5, max_length=300)
    description: str | None = None
    severity: FindingSeverityEnum | None = None
    category: str | None = None
    evidence: str | None = None
    risk_description: str | None = None
    auditee_response: str | None = None
    action_due_date: date | None = None
    status: str | None = None
    capa_id: int | None = None


class AuditFindingResponse(AuditFindingBase):
    id: int
    audit_id: int
    finding_number: int
    evidence: str | None = None
    risk_description: str | None = None
    risk_level: str | None = None
    capa_required: bool
    capa_id: int | None = None
    auditee_response: str | None = None
    response_date: date | None = None
    action_due_date: date | None = None
    action_completed_date: date | None = None
    status: str
    verified: bool
    verified_date: date | None = None
    verification_comments: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=300)
    description: str | None = None
    audit_type: AuditTypeEnum
    reference_standard: str | None = None


class AuditCreate(AuditBase):
    reference_version: str | None = None
    audit_scope: str | None = None
    planned_date: date | None = None
    planned_end_date: date | None = None
    lead_auditor_id: int | None = None
    auditors: list[int] | None = None
    audited_entity: str | None = None
    audited_department: str | None = None
    auditee_contact_id: int | None = None
    supplier_id: int | None = None


class AuditUpdate(BaseModel):
    title: str | None = Field(None, min_length=5, max_length=300)
    description: str | None = None
    audit_scope: str | None = None
    planned_date: date | None = None
    planned_end_date: date | None = None
    actual_date: date | None = None
    actual_end_date: date | None = None
    status: AuditStatusEnum | None = None
    lead_auditor_id: int | None = None
    auditors: list[int] | None = None
    audited_entity: str | None = None
    audited_department: str | None = None
    overall_score: Decimal | None = None
    max_score: Decimal | None = None
    audit_conclusion: str | None = None
    recommendation: str | None = None
    follow_up_required: bool | None = None
    follow_up_date: date | None = None


class AuditClose(BaseModel):
    audit_conclusion: str = Field(..., min_length=10)
    recommendation: str | None = None


class AuditResponse(AuditBase):
    id: int
    audit_number: str
    reference_version: str | None = None
    audit_scope: str | None = None
    planned_date: date | None = None
    planned_end_date: date | None = None
    actual_date: date | None = None
    actual_end_date: date | None = None
    status: AuditStatusEnum
    lead_auditor_id: int | None = None
    auditors: list[int] | None = None
    audited_entity: str | None = None
    audited_department: str | None = None
    auditee_contact_id: int | None = None
    supplier_id: int | None = None
    total_findings: int
    critical_findings: int
    major_findings: int
    minor_findings: int
    observations: int
    overall_score: Decimal | None = None
    max_score: Decimal | None = None
    audit_conclusion: str | None = None
    recommendation: str | None = None
    report_date: date | None = None
    report_file: str | None = None
    follow_up_required: bool
    follow_up_date: date | None = None
    follow_up_completed: bool
    closed_date: date | None = None
    findings: list[AuditFindingResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CAPA
# ============================================================================

class CAPAActionBase(BaseModel):
    action_type: str = Field(..., min_length=2, max_length=50)
    description: str = Field(..., min_length=10)
    responsible_id: int | None = None
    due_date: date


class CAPAActionCreate(CAPAActionBase):
    planned_date: date | None = None
    verification_required: bool = True
    estimated_cost: Decimal | None = None


class CAPAActionUpdate(BaseModel):
    description: str | None = None
    responsible_id: int | None = None
    due_date: date | None = None
    status: str | None = None
    completed_date: date | None = None
    result: str | None = None
    evidence: str | None = None
    actual_cost: Decimal | None = None
    comments: str | None = None


class CAPAActionResponse(CAPAActionBase):
    id: int
    capa_id: int
    action_number: int
    planned_date: date | None = None
    completed_date: date | None = None
    status: str
    result: str | None = None
    evidence: str | None = None
    verification_required: bool
    verified: bool
    verified_date: date | None = None
    verification_result: str | None = None
    estimated_cost: Decimal | None = None
    actual_cost: Decimal | None = None
    comments: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CAPABase(BaseModel):
    title: str = Field(..., min_length=5, max_length=300)
    description: str = Field(..., min_length=10)
    capa_type: CAPATypeEnum


class CAPACreate(CAPABase):
    source_type: str | None = None
    source_reference: str | None = None
    source_id: int | None = None
    priority: str = "MEDIUM"
    open_date: date
    target_close_date: date | None = None
    owner_id: int
    department: str | None = None
    problem_statement: str | None = None
    immediate_containment: str | None = None
    effectiveness_criteria: str | None = None


class CAPAUpdate(BaseModel):
    title: str | None = Field(None, min_length=5, max_length=300)
    description: str | None = None
    priority: str | None = None
    status: CAPAStatusEnum | None = None
    target_close_date: date | None = None
    owner_id: int | None = None
    department: str | None = None
    problem_statement: str | None = None
    immediate_containment: str | None = None
    root_cause_analysis: str | None = None
    root_cause_method: str | None = None
    root_cause_verified: bool | None = None
    impact_assessment: str | None = None
    risk_level: str | None = None
    effectiveness_criteria: str | None = None
    extension_required: bool | None = None
    extension_scope: str | None = None


class CAPAClose(BaseModel):
    effectiveness_verified: bool
    effectiveness_result: str = Field(..., min_length=10)
    closure_comments: str | None = None


class CAPAResponse(CAPABase):
    id: int
    capa_number: str
    source_type: str | None = None
    source_reference: str | None = None
    status: CAPAStatusEnum
    priority: str
    open_date: date
    target_close_date: date | None = None
    actual_close_date: date | None = None
    owner_id: int
    department: str | None = None
    problem_statement: str | None = None
    immediate_containment: str | None = None
    root_cause_analysis: str | None = None
    root_cause_method: str | None = None
    root_cause_verified: bool
    impact_assessment: str | None = None
    risk_level: str | None = None
    effectiveness_criteria: str | None = None
    effectiveness_verified: bool
    effectiveness_date: date | None = None
    effectiveness_result: str | None = None
    extension_required: bool
    extension_scope: str | None = None
    extension_completed: bool
    closure_comments: str | None = None
    actions: list[CAPAActionResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# RÉCLAMATIONS CLIENTS
# ============================================================================

class ClaimActionBase(BaseModel):
    action_type: str = Field(..., min_length=2, max_length=50)
    description: str = Field(..., min_length=10)
    responsible_id: int | None = None
    due_date: date | None = None


class ClaimActionCreate(ClaimActionBase):
    pass


class ClaimActionResponse(ClaimActionBase):
    id: int
    claim_id: int
    action_number: int
    completed_date: date | None = None
    status: str
    result: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClaimBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=300)
    description: str = Field(..., min_length=10)
    customer_id: int
    received_date: date


class ClaimCreate(ClaimBase):
    customer_contact: str | None = None
    customer_reference: str | None = None
    received_via: str | None = None
    product_id: int | None = None
    order_reference: str | None = None
    invoice_reference: str | None = None
    lot_number: str | None = None
    quantity_affected: Decimal | None = None
    claim_type: str | None = None
    severity: NonConformanceSeverityEnum | None = None
    priority: str = "MEDIUM"
    owner_id: int | None = None
    response_due_date: date | None = None
    claim_amount: Decimal | None = None


class ClaimUpdate(BaseModel):
    title: str | None = Field(None, min_length=5, max_length=300)
    description: str | None = None
    customer_contact: str | None = None
    severity: NonConformanceSeverityEnum | None = None
    priority: str | None = None
    status: ClaimStatusEnum | None = None
    owner_id: int | None = None
    investigation_summary: str | None = None
    root_cause: str | None = None
    our_responsibility: bool | None = None
    nc_id: int | None = None
    capa_id: int | None = None
    response_due_date: date | None = None
    response_content: str | None = None
    resolution_type: str | None = None
    resolution_description: str | None = None
    claim_amount: Decimal | None = None
    accepted_amount: Decimal | None = None


class ClaimRespond(BaseModel):
    response_content: str = Field(..., min_length=10)


class ClaimResolve(BaseModel):
    resolution_type: str = Field(..., min_length=2, max_length=50)
    resolution_description: str = Field(..., min_length=10)
    accepted_amount: Decimal | None = None


class ClaimClose(BaseModel):
    customer_satisfied: bool | None = None
    satisfaction_feedback: str | None = None


class ClaimResponse(ClaimBase):
    id: int
    claim_number: str
    customer_contact: str | None = None
    customer_reference: str | None = None
    received_via: str | None = None
    received_by_id: int | None = None
    product_id: int | None = None
    order_reference: str | None = None
    invoice_reference: str | None = None
    lot_number: str | None = None
    quantity_affected: Decimal | None = None
    claim_type: str | None = None
    severity: NonConformanceSeverityEnum | None = None
    priority: str
    status: ClaimStatusEnum
    owner_id: int | None = None
    investigation_summary: str | None = None
    root_cause: str | None = None
    our_responsibility: bool | None = None
    nc_id: int | None = None
    capa_id: int | None = None
    response_due_date: date | None = None
    response_date: date | None = None
    response_content: str | None = None
    resolution_type: str | None = None
    resolution_description: str | None = None
    resolution_date: date | None = None
    claim_amount: Decimal | None = None
    accepted_amount: Decimal | None = None
    customer_satisfied: bool | None = None
    satisfaction_feedback: str | None = None
    closed_date: date | None = None
    actions: list[ClaimActionResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# INDICATEURS QUALITÉ
# ============================================================================

class IndicatorMeasurementBase(BaseModel):
    measurement_date: date
    value: Decimal


class IndicatorMeasurementCreate(IndicatorMeasurementBase):
    period_start: date | None = None
    period_end: date | None = None
    numerator: Decimal | None = None
    denominator: Decimal | None = None
    comments: str | None = None
    source: str = "MANUAL"


class IndicatorMeasurementResponse(IndicatorMeasurementBase):
    id: int
    indicator_id: int
    period_start: date | None = None
    period_end: date | None = None
    numerator: Decimal | None = None
    denominator: Decimal | None = None
    target_value: Decimal | None = None
    deviation: Decimal | None = None
    achievement_rate: Decimal | None = None
    status: str | None = None
    comments: str | None = None
    action_required: bool
    source: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IndicatorBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    category: str | None = None


class IndicatorCreate(IndicatorBase):
    formula: str | None = None
    unit: str | None = None
    target_value: Decimal | None = None
    target_min: Decimal | None = None
    target_max: Decimal | None = None
    warning_threshold: Decimal | None = None
    critical_threshold: Decimal | None = None
    direction: str | None = None
    measurement_frequency: str | None = None
    data_source: str | None = None
    owner_id: int | None = None


class IndicatorUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    category: str | None = None
    formula: str | None = None
    unit: str | None = None
    target_value: Decimal | None = None
    target_min: Decimal | None = None
    target_max: Decimal | None = None
    warning_threshold: Decimal | None = None
    critical_threshold: Decimal | None = None
    direction: str | None = None
    measurement_frequency: str | None = None
    owner_id: int | None = None
    is_active: bool | None = None


class IndicatorResponse(IndicatorBase):
    id: int
    formula: str | None = None
    unit: str | None = None
    target_value: Decimal | None = None
    target_min: Decimal | None = None
    target_max: Decimal | None = None
    warning_threshold: Decimal | None = None
    critical_threshold: Decimal | None = None
    direction: str | None = None
    measurement_frequency: str | None = None
    data_source: str | None = None
    owner_id: int | None = None
    is_active: bool
    measurements: list[IndicatorMeasurementResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CERTIFICATIONS
# ============================================================================

class CertificationAuditBase(BaseModel):
    audit_type: str = Field(..., min_length=2, max_length=50)
    audit_date: date


class CertificationAuditCreate(CertificationAuditBase):
    audit_end_date: date | None = None
    lead_auditor: str | None = None
    audit_team: list[str] | None = None
    notes: str | None = None


class CertificationAuditUpdate(BaseModel):
    audit_date: date | None = None
    audit_end_date: date | None = None
    lead_auditor: str | None = None
    result: str | None = None
    findings_count: int | None = None
    major_nc_count: int | None = None
    minor_nc_count: int | None = None
    observations_count: int | None = None
    report_date: date | None = None
    report_file: str | None = None
    corrective_actions_due: date | None = None
    corrective_actions_closed: date | None = None
    follow_up_audit_date: date | None = None
    notes: str | None = None


class CertificationAuditResponse(CertificationAuditBase):
    id: int
    certification_id: int
    audit_end_date: date | None = None
    lead_auditor: str | None = None
    audit_team: list[str] | None = None
    result: str | None = None
    findings_count: int
    major_nc_count: int
    minor_nc_count: int
    observations_count: int
    report_date: date | None = None
    report_file: str | None = None
    corrective_actions_due: date | None = None
    corrective_actions_closed: date | None = None
    follow_up_audit_date: date | None = None
    quality_audit_id: int | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CertificationBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    standard: str = Field(..., min_length=2, max_length=100)


class CertificationCreate(CertificationBase):
    standard_version: str | None = None
    scope: str | None = None
    certification_body: str | None = None
    certification_body_accreditation: str | None = None
    initial_certification_date: date | None = None
    manager_id: int | None = None
    annual_cost: Decimal | None = None
    notes: str | None = None


class CertificationUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    standard_version: str | None = None
    scope: str | None = None
    certification_body: str | None = None
    status: CertificationStatusEnum | None = None
    current_certificate_date: date | None = None
    expiry_date: date | None = None
    certificate_number: str | None = None
    certificate_file: str | None = None
    next_surveillance_date: date | None = None
    next_renewal_date: date | None = None
    manager_id: int | None = None
    annual_cost: Decimal | None = None
    notes: str | None = None


class CertificationResponse(CertificationBase):
    id: int
    standard_version: str | None = None
    scope: str | None = None
    certification_body: str | None = None
    certification_body_accreditation: str | None = None
    initial_certification_date: date | None = None
    current_certificate_date: date | None = None
    expiry_date: date | None = None
    next_surveillance_date: date | None = None
    next_renewal_date: date | None = None
    certificate_number: str | None = None
    certificate_file: str | None = None
    status: CertificationStatusEnum
    manager_id: int | None = None
    annual_cost: Decimal | None = None
    audits: list[CertificationAuditResponse] = []
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# LISTES PAGINÉES
# ============================================================================

class PaginatedNCResponse(BaseModel):
    items: list[NonConformanceResponse]
    total: int
    skip: int
    limit: int


class PaginatedControlTemplateResponse(BaseModel):
    items: list[ControlTemplateResponse]
    total: int
    skip: int
    limit: int


class PaginatedControlResponse(BaseModel):
    items: list[ControlResponse]
    total: int
    skip: int
    limit: int


class PaginatedAuditResponse(BaseModel):
    items: list[AuditResponse]
    total: int
    skip: int
    limit: int


class PaginatedCAPAResponse(BaseModel):
    items: list[CAPAResponse]
    total: int
    skip: int
    limit: int


class PaginatedClaimResponse(BaseModel):
    items: list[ClaimResponse]
    total: int
    skip: int
    limit: int


class PaginatedIndicatorResponse(BaseModel):
    items: list[IndicatorResponse]
    total: int
    skip: int
    limit: int


class PaginatedCertificationResponse(BaseModel):
    items: list[CertificationResponse]
    total: int
    skip: int
    limit: int


# ============================================================================
# DASHBOARD QUALITÉ
# ============================================================================

class QualityDashboard(BaseModel):
    # Non-conformités
    nc_total: int = 0
    nc_open: int = 0
    nc_critical: int = 0
    nc_by_type: dict[str, int] = {}
    nc_by_status: dict[str, int] = {}

    # Contrôles qualité
    controls_total: int = 0
    controls_completed: int = 0
    controls_pass_rate: Decimal = Decimal("0")
    controls_by_type: dict[str, int] = {}

    # Audits
    audits_planned: int = 0
    audits_completed: int = 0
    audit_findings_open: int = 0

    # CAPA
    capa_total: int = 0
    capa_open: int = 0
    capa_overdue: int = 0
    capa_effectiveness_rate: Decimal = Decimal("0")

    # Réclamations clients
    claims_total: int = 0
    claims_open: int = 0
    claims_avg_resolution_days: Decimal | None = None
    claims_satisfaction_rate: Decimal | None = None

    # Certifications
    certifications_active: int = 0
    certifications_expiring_soon: int = 0

    # Indicateurs
    indicators_on_target: int = 0
    indicators_warning: int = 0
    indicators_critical: int = 0

    # Tendances
    nc_trend_30_days: list[dict[str, Any]] = []
    control_trend_30_days: list[dict[str, Any]] = []
