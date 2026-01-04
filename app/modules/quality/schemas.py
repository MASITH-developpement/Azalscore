"""
AZALS MODULE M7 - Schémas Pydantic Qualité
==========================================

Schémas de validation pour les API du module Qualité.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, field_validator


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
    description: Optional[str] = None
    nc_type: NonConformanceTypeEnum
    severity: NonConformanceSeverityEnum
    detected_date: date
    detection_location: Optional[str] = None
    detection_phase: Optional[str] = None


class NonConformanceCreate(NonConformanceBase):
    source_type: Optional[str] = None
    source_reference: Optional[str] = None
    source_id: Optional[int] = None
    product_id: Optional[int] = None
    lot_number: Optional[str] = None
    serial_number: Optional[str] = None
    quantity_affected: Optional[Decimal] = None
    unit_id: Optional[int] = None
    supplier_id: Optional[int] = None
    customer_id: Optional[int] = None
    immediate_action: Optional[str] = None
    responsible_id: Optional[int] = None
    department: Optional[str] = None
    notes: Optional[str] = None


class NonConformanceUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=300)
    description: Optional[str] = None
    severity: Optional[NonConformanceSeverityEnum] = None
    status: Optional[NonConformanceStatusEnum] = None

    # Analyse des causes
    immediate_cause: Optional[str] = None
    root_cause: Optional[str] = None
    cause_analysis_method: Optional[str] = None

    # Impact
    impact_description: Optional[str] = None
    estimated_cost: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None

    # Traitement
    immediate_action: Optional[str] = None
    disposition: Optional[str] = None
    disposition_justification: Optional[str] = None

    # CAPA
    capa_required: Optional[bool] = None
    capa_id: Optional[int] = None

    # Responsable
    responsible_id: Optional[int] = None
    department: Optional[str] = None

    notes: Optional[str] = None


class NonConformanceClose(BaseModel):
    closure_justification: str = Field(..., min_length=10)
    effectiveness_verified: bool = False


class NonConformanceActionCreate(BaseModel):
    action_type: str = Field(..., min_length=2, max_length=50)
    description: str = Field(..., min_length=10)
    responsible_id: Optional[int] = None
    planned_date: Optional[date] = None
    due_date: Optional[date] = None
    comments: Optional[str] = None


class NonConformanceActionUpdate(BaseModel):
    description: Optional[str] = None
    responsible_id: Optional[int] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    completed_date: Optional[date] = None
    comments: Optional[str] = None


class NonConformanceActionResponse(BaseModel):
    id: int
    nc_id: int
    action_number: int
    action_type: str
    description: str
    responsible_id: Optional[int] = None
    planned_date: Optional[date] = None
    due_date: Optional[date] = None
    completed_date: Optional[date] = None
    status: str
    verified: bool
    verified_date: Optional[date] = None
    comments: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NonConformanceResponse(NonConformanceBase):
    id: int
    nc_number: str
    status: NonConformanceStatusEnum
    detected_by_id: Optional[int] = None
    source_type: Optional[str] = None
    source_reference: Optional[str] = None
    product_id: Optional[int] = None
    lot_number: Optional[str] = None
    quantity_affected: Optional[Decimal] = None
    supplier_id: Optional[int] = None
    customer_id: Optional[int] = None

    immediate_cause: Optional[str] = None
    root_cause: Optional[str] = None
    cause_analysis_method: Optional[str] = None

    impact_description: Optional[str] = None
    estimated_cost: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None

    immediate_action: Optional[str] = None
    disposition: Optional[str] = None

    responsible_id: Optional[int] = None
    department: Optional[str] = None

    capa_required: bool
    capa_id: Optional[int] = None

    closed_date: Optional[date] = None
    effectiveness_verified: bool

    is_recurrent: bool
    recurrence_count: int

    actions: List[NonConformanceActionResponse] = []

    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================================
# TEMPLATES DE CONTRÔLE QUALITÉ
# ============================================================================

class ControlTemplateItemBase(BaseModel):
    sequence: int
    characteristic: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    measurement_type: str = Field(..., min_length=2, max_length=50)
    unit: Optional[str] = None
    nominal_value: Optional[Decimal] = None
    tolerance_min: Optional[Decimal] = None
    tolerance_max: Optional[Decimal] = None
    expected_result: Optional[str] = None
    measurement_method: Optional[str] = None
    equipment_code: Optional[str] = None
    is_critical: bool = False
    is_mandatory: bool = True
    sampling_frequency: Optional[str] = None


class ControlTemplateItemCreate(ControlTemplateItemBase):
    pass


class ControlTemplateItemResponse(ControlTemplateItemBase):
    id: int
    template_id: int
    upper_limit: Optional[Decimal] = None
    lower_limit: Optional[Decimal] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ControlTemplateBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    version: str = "1.0"
    control_type: ControlTypeEnum


class ControlTemplateCreate(ControlTemplateBase):
    applies_to: Optional[str] = None
    product_category_id: Optional[int] = None
    instructions: Optional[str] = None
    sampling_plan: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    required_equipment: Optional[List[str]] = None
    items: Optional[List[ControlTemplateItemCreate]] = None


class ControlTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    version: Optional[str] = None
    instructions: Optional[str] = None
    sampling_plan: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class ControlTemplateResponse(ControlTemplateBase):
    id: int
    applies_to: Optional[str] = None
    product_category_id: Optional[int] = None
    instructions: Optional[str] = None
    sampling_plan: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    required_equipment: Optional[List[str]] = None
    is_active: bool
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    items: List[ControlTemplateItemResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================================
# CONTRÔLES QUALITÉ
# ============================================================================

class ControlLineBase(BaseModel):
    sequence: int
    characteristic: str = Field(..., min_length=2, max_length=200)
    nominal_value: Optional[Decimal] = None
    tolerance_min: Optional[Decimal] = None
    tolerance_max: Optional[Decimal] = None
    unit: Optional[str] = None


class ControlLineCreate(ControlLineBase):
    template_item_id: Optional[int] = None
    measured_value: Optional[Decimal] = None
    measured_text: Optional[str] = None
    measured_boolean: Optional[bool] = None
    result: Optional[ControlResultEnum] = None
    equipment_code: Optional[str] = None
    comments: Optional[str] = None


class ControlLineUpdate(BaseModel):
    measured_value: Optional[Decimal] = None
    measured_text: Optional[str] = None
    measured_boolean: Optional[bool] = None
    result: Optional[ControlResultEnum] = None
    equipment_code: Optional[str] = None
    comments: Optional[str] = None


class ControlLineResponse(ControlLineBase):
    id: int
    control_id: int
    template_item_id: Optional[int] = None
    measured_value: Optional[Decimal] = None
    measured_text: Optional[str] = None
    measured_boolean: Optional[bool] = None
    measurement_date: Optional[datetime] = None
    result: Optional[ControlResultEnum] = None
    deviation: Optional[Decimal] = None
    equipment_code: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ControlBase(BaseModel):
    control_type: ControlTypeEnum
    control_date: date


class ControlCreate(ControlBase):
    template_id: Optional[int] = None
    source_type: Optional[str] = None
    source_reference: Optional[str] = None
    source_id: Optional[int] = None
    product_id: Optional[int] = None
    lot_number: Optional[str] = None
    serial_number: Optional[str] = None
    quantity_to_control: Optional[Decimal] = None
    unit_id: Optional[int] = None
    supplier_id: Optional[int] = None
    customer_id: Optional[int] = None
    location: Optional[str] = None
    controller_id: Optional[int] = None
    observations: Optional[str] = None
    lines: Optional[List[ControlLineCreate]] = None


class ControlUpdate(BaseModel):
    control_date: Optional[date] = None
    quantity_controlled: Optional[Decimal] = None
    quantity_conforming: Optional[Decimal] = None
    quantity_non_conforming: Optional[Decimal] = None
    location: Optional[str] = None
    controller_id: Optional[int] = None
    status: Optional[ControlStatusEnum] = None
    result: Optional[ControlResultEnum] = None
    decision: Optional[str] = None
    decision_comments: Optional[str] = None
    observations: Optional[str] = None


class ControlResponse(ControlBase):
    id: int
    control_number: str
    template_id: Optional[int] = None
    source_type: Optional[str] = None
    source_reference: Optional[str] = None
    product_id: Optional[int] = None
    lot_number: Optional[str] = None
    serial_number: Optional[str] = None
    quantity_to_control: Optional[Decimal] = None
    quantity_controlled: Optional[Decimal] = None
    quantity_conforming: Optional[Decimal] = None
    quantity_non_conforming: Optional[Decimal] = None
    supplier_id: Optional[int] = None
    customer_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    controller_id: Optional[int] = None
    status: ControlStatusEnum
    result: Optional[ControlResultEnum] = None
    result_date: Optional[datetime] = None
    decision: Optional[str] = None
    decision_by_id: Optional[int] = None
    decision_date: Optional[datetime] = None
    decision_comments: Optional[str] = None
    nc_id: Optional[int] = None
    observations: Optional[str] = None
    lines: List[ControlLineResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================================
# AUDITS
# ============================================================================

class AuditFindingBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=300)
    description: str = Field(..., min_length=10)
    severity: FindingSeverityEnum
    category: Optional[str] = None
    clause_reference: Optional[str] = None
    process_reference: Optional[str] = None


class AuditFindingCreate(AuditFindingBase):
    evidence: Optional[str] = None
    risk_description: Optional[str] = None
    capa_required: bool = False
    action_due_date: Optional[date] = None


class AuditFindingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=300)
    description: Optional[str] = None
    severity: Optional[FindingSeverityEnum] = None
    category: Optional[str] = None
    evidence: Optional[str] = None
    risk_description: Optional[str] = None
    auditee_response: Optional[str] = None
    action_due_date: Optional[date] = None
    status: Optional[str] = None
    capa_id: Optional[int] = None


class AuditFindingResponse(AuditFindingBase):
    id: int
    audit_id: int
    finding_number: int
    evidence: Optional[str] = None
    risk_description: Optional[str] = None
    risk_level: Optional[str] = None
    capa_required: bool
    capa_id: Optional[int] = None
    auditee_response: Optional[str] = None
    response_date: Optional[date] = None
    action_due_date: Optional[date] = None
    action_completed_date: Optional[date] = None
    status: str
    verified: bool
    verified_date: Optional[date] = None
    verification_comments: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AuditBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=300)
    description: Optional[str] = None
    audit_type: AuditTypeEnum
    reference_standard: Optional[str] = None


class AuditCreate(AuditBase):
    reference_version: Optional[str] = None
    audit_scope: Optional[str] = None
    planned_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    lead_auditor_id: Optional[int] = None
    auditors: Optional[List[int]] = None
    audited_entity: Optional[str] = None
    audited_department: Optional[str] = None
    auditee_contact_id: Optional[int] = None
    supplier_id: Optional[int] = None


class AuditUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=300)
    description: Optional[str] = None
    audit_scope: Optional[str] = None
    planned_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    status: Optional[AuditStatusEnum] = None
    lead_auditor_id: Optional[int] = None
    auditors: Optional[List[int]] = None
    audited_entity: Optional[str] = None
    audited_department: Optional[str] = None
    overall_score: Optional[Decimal] = None
    max_score: Optional[Decimal] = None
    audit_conclusion: Optional[str] = None
    recommendation: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[date] = None


class AuditClose(BaseModel):
    audit_conclusion: str = Field(..., min_length=10)
    recommendation: Optional[str] = None


class AuditResponse(AuditBase):
    id: int
    audit_number: str
    reference_version: Optional[str] = None
    audit_scope: Optional[str] = None
    planned_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    status: AuditStatusEnum
    lead_auditor_id: Optional[int] = None
    auditors: Optional[List[int]] = None
    audited_entity: Optional[str] = None
    audited_department: Optional[str] = None
    auditee_contact_id: Optional[int] = None
    supplier_id: Optional[int] = None
    total_findings: int
    critical_findings: int
    major_findings: int
    minor_findings: int
    observations: int
    overall_score: Optional[Decimal] = None
    max_score: Optional[Decimal] = None
    audit_conclusion: Optional[str] = None
    recommendation: Optional[str] = None
    report_date: Optional[date] = None
    report_file: Optional[str] = None
    follow_up_required: bool
    follow_up_date: Optional[date] = None
    follow_up_completed: bool
    closed_date: Optional[date] = None
    findings: List[AuditFindingResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================================
# CAPA
# ============================================================================

class CAPAActionBase(BaseModel):
    action_type: str = Field(..., min_length=2, max_length=50)
    description: str = Field(..., min_length=10)
    responsible_id: Optional[int] = None
    due_date: date


class CAPAActionCreate(CAPAActionBase):
    planned_date: Optional[date] = None
    verification_required: bool = True
    estimated_cost: Optional[Decimal] = None


class CAPAActionUpdate(BaseModel):
    description: Optional[str] = None
    responsible_id: Optional[int] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    completed_date: Optional[date] = None
    result: Optional[str] = None
    evidence: Optional[str] = None
    actual_cost: Optional[Decimal] = None
    comments: Optional[str] = None


class CAPAActionResponse(CAPAActionBase):
    id: int
    capa_id: int
    action_number: int
    planned_date: Optional[date] = None
    completed_date: Optional[date] = None
    status: str
    result: Optional[str] = None
    evidence: Optional[str] = None
    verification_required: bool
    verified: bool
    verified_date: Optional[date] = None
    verification_result: Optional[str] = None
    estimated_cost: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    comments: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CAPABase(BaseModel):
    title: str = Field(..., min_length=5, max_length=300)
    description: str = Field(..., min_length=10)
    capa_type: CAPATypeEnum


class CAPACreate(CAPABase):
    source_type: Optional[str] = None
    source_reference: Optional[str] = None
    source_id: Optional[int] = None
    priority: str = "MEDIUM"
    open_date: date
    target_close_date: Optional[date] = None
    owner_id: int
    department: Optional[str] = None
    problem_statement: Optional[str] = None
    immediate_containment: Optional[str] = None
    effectiveness_criteria: Optional[str] = None


class CAPAUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=300)
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[CAPAStatusEnum] = None
    target_close_date: Optional[date] = None
    owner_id: Optional[int] = None
    department: Optional[str] = None
    problem_statement: Optional[str] = None
    immediate_containment: Optional[str] = None
    root_cause_analysis: Optional[str] = None
    root_cause_method: Optional[str] = None
    root_cause_verified: Optional[bool] = None
    impact_assessment: Optional[str] = None
    risk_level: Optional[str] = None
    effectiveness_criteria: Optional[str] = None
    extension_required: Optional[bool] = None
    extension_scope: Optional[str] = None


class CAPAClose(BaseModel):
    effectiveness_verified: bool
    effectiveness_result: str = Field(..., min_length=10)
    closure_comments: Optional[str] = None


class CAPAResponse(CAPABase):
    id: int
    capa_number: str
    source_type: Optional[str] = None
    source_reference: Optional[str] = None
    status: CAPAStatusEnum
    priority: str
    open_date: date
    target_close_date: Optional[date] = None
    actual_close_date: Optional[date] = None
    owner_id: int
    department: Optional[str] = None
    problem_statement: Optional[str] = None
    immediate_containment: Optional[str] = None
    root_cause_analysis: Optional[str] = None
    root_cause_method: Optional[str] = None
    root_cause_verified: bool
    impact_assessment: Optional[str] = None
    risk_level: Optional[str] = None
    effectiveness_criteria: Optional[str] = None
    effectiveness_verified: bool
    effectiveness_date: Optional[date] = None
    effectiveness_result: Optional[str] = None
    extension_required: bool
    extension_scope: Optional[str] = None
    extension_completed: bool
    closure_comments: Optional[str] = None
    actions: List[CAPAActionResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================================
# RÉCLAMATIONS CLIENTS
# ============================================================================

class ClaimActionBase(BaseModel):
    action_type: str = Field(..., min_length=2, max_length=50)
    description: str = Field(..., min_length=10)
    responsible_id: Optional[int] = None
    due_date: Optional[date] = None


class ClaimActionCreate(ClaimActionBase):
    pass


class ClaimActionResponse(ClaimActionBase):
    id: int
    claim_id: int
    action_number: int
    completed_date: Optional[date] = None
    status: str
    result: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClaimBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=300)
    description: str = Field(..., min_length=10)
    customer_id: int
    received_date: date


class ClaimCreate(ClaimBase):
    customer_contact: Optional[str] = None
    customer_reference: Optional[str] = None
    received_via: Optional[str] = None
    product_id: Optional[int] = None
    order_reference: Optional[str] = None
    invoice_reference: Optional[str] = None
    lot_number: Optional[str] = None
    quantity_affected: Optional[Decimal] = None
    claim_type: Optional[str] = None
    severity: Optional[NonConformanceSeverityEnum] = None
    priority: str = "MEDIUM"
    owner_id: Optional[int] = None
    response_due_date: Optional[date] = None
    claim_amount: Optional[Decimal] = None


class ClaimUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=300)
    description: Optional[str] = None
    customer_contact: Optional[str] = None
    severity: Optional[NonConformanceSeverityEnum] = None
    priority: Optional[str] = None
    status: Optional[ClaimStatusEnum] = None
    owner_id: Optional[int] = None
    investigation_summary: Optional[str] = None
    root_cause: Optional[str] = None
    our_responsibility: Optional[bool] = None
    nc_id: Optional[int] = None
    capa_id: Optional[int] = None
    response_due_date: Optional[date] = None
    response_content: Optional[str] = None
    resolution_type: Optional[str] = None
    resolution_description: Optional[str] = None
    claim_amount: Optional[Decimal] = None
    accepted_amount: Optional[Decimal] = None


class ClaimRespond(BaseModel):
    response_content: str = Field(..., min_length=10)


class ClaimResolve(BaseModel):
    resolution_type: str = Field(..., min_length=2, max_length=50)
    resolution_description: str = Field(..., min_length=10)
    accepted_amount: Optional[Decimal] = None


class ClaimClose(BaseModel):
    customer_satisfied: Optional[bool] = None
    satisfaction_feedback: Optional[str] = None


class ClaimResponse(ClaimBase):
    id: int
    claim_number: str
    customer_contact: Optional[str] = None
    customer_reference: Optional[str] = None
    received_via: Optional[str] = None
    received_by_id: Optional[int] = None
    product_id: Optional[int] = None
    order_reference: Optional[str] = None
    invoice_reference: Optional[str] = None
    lot_number: Optional[str] = None
    quantity_affected: Optional[Decimal] = None
    claim_type: Optional[str] = None
    severity: Optional[NonConformanceSeverityEnum] = None
    priority: str
    status: ClaimStatusEnum
    owner_id: Optional[int] = None
    investigation_summary: Optional[str] = None
    root_cause: Optional[str] = None
    our_responsibility: Optional[bool] = None
    nc_id: Optional[int] = None
    capa_id: Optional[int] = None
    response_due_date: Optional[date] = None
    response_date: Optional[date] = None
    response_content: Optional[str] = None
    resolution_type: Optional[str] = None
    resolution_description: Optional[str] = None
    resolution_date: Optional[date] = None
    claim_amount: Optional[Decimal] = None
    accepted_amount: Optional[Decimal] = None
    customer_satisfied: Optional[bool] = None
    satisfaction_feedback: Optional[str] = None
    closed_date: Optional[date] = None
    actions: List[ClaimActionResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================================
# INDICATEURS QUALITÉ
# ============================================================================

class IndicatorMeasurementBase(BaseModel):
    measurement_date: date
    value: Decimal


class IndicatorMeasurementCreate(IndicatorMeasurementBase):
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    numerator: Optional[Decimal] = None
    denominator: Optional[Decimal] = None
    comments: Optional[str] = None
    source: str = "MANUAL"


class IndicatorMeasurementResponse(IndicatorMeasurementBase):
    id: int
    indicator_id: int
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    numerator: Optional[Decimal] = None
    denominator: Optional[Decimal] = None
    target_value: Optional[Decimal] = None
    deviation: Optional[Decimal] = None
    achievement_rate: Optional[Decimal] = None
    status: Optional[str] = None
    comments: Optional[str] = None
    action_required: bool
    source: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class IndicatorBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None


class IndicatorCreate(IndicatorBase):
    formula: Optional[str] = None
    unit: Optional[str] = None
    target_value: Optional[Decimal] = None
    target_min: Optional[Decimal] = None
    target_max: Optional[Decimal] = None
    warning_threshold: Optional[Decimal] = None
    critical_threshold: Optional[Decimal] = None
    direction: Optional[str] = None
    measurement_frequency: Optional[str] = None
    data_source: Optional[str] = None
    owner_id: Optional[int] = None


class IndicatorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    formula: Optional[str] = None
    unit: Optional[str] = None
    target_value: Optional[Decimal] = None
    target_min: Optional[Decimal] = None
    target_max: Optional[Decimal] = None
    warning_threshold: Optional[Decimal] = None
    critical_threshold: Optional[Decimal] = None
    direction: Optional[str] = None
    measurement_frequency: Optional[str] = None
    owner_id: Optional[int] = None
    is_active: Optional[bool] = None


class IndicatorResponse(IndicatorBase):
    id: int
    formula: Optional[str] = None
    unit: Optional[str] = None
    target_value: Optional[Decimal] = None
    target_min: Optional[Decimal] = None
    target_max: Optional[Decimal] = None
    warning_threshold: Optional[Decimal] = None
    critical_threshold: Optional[Decimal] = None
    direction: Optional[str] = None
    measurement_frequency: Optional[str] = None
    data_source: Optional[str] = None
    owner_id: Optional[int] = None
    is_active: bool
    measurements: List[IndicatorMeasurementResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================================
# CERTIFICATIONS
# ============================================================================

class CertificationAuditBase(BaseModel):
    audit_type: str = Field(..., min_length=2, max_length=50)
    audit_date: date


class CertificationAuditCreate(CertificationAuditBase):
    audit_end_date: Optional[date] = None
    lead_auditor: Optional[str] = None
    audit_team: Optional[List[str]] = None
    notes: Optional[str] = None


class CertificationAuditUpdate(BaseModel):
    audit_date: Optional[date] = None
    audit_end_date: Optional[date] = None
    lead_auditor: Optional[str] = None
    result: Optional[str] = None
    findings_count: Optional[int] = None
    major_nc_count: Optional[int] = None
    minor_nc_count: Optional[int] = None
    observations_count: Optional[int] = None
    report_date: Optional[date] = None
    report_file: Optional[str] = None
    corrective_actions_due: Optional[date] = None
    corrective_actions_closed: Optional[date] = None
    follow_up_audit_date: Optional[date] = None
    notes: Optional[str] = None


class CertificationAuditResponse(CertificationAuditBase):
    id: int
    certification_id: int
    audit_end_date: Optional[date] = None
    lead_auditor: Optional[str] = None
    audit_team: Optional[List[str]] = None
    result: Optional[str] = None
    findings_count: int
    major_nc_count: int
    minor_nc_count: int
    observations_count: int
    report_date: Optional[date] = None
    report_file: Optional[str] = None
    corrective_actions_due: Optional[date] = None
    corrective_actions_closed: Optional[date] = None
    follow_up_audit_date: Optional[date] = None
    quality_audit_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CertificationBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    standard: str = Field(..., min_length=2, max_length=100)


class CertificationCreate(CertificationBase):
    standard_version: Optional[str] = None
    scope: Optional[str] = None
    certification_body: Optional[str] = None
    certification_body_accreditation: Optional[str] = None
    initial_certification_date: Optional[date] = None
    manager_id: Optional[int] = None
    annual_cost: Optional[Decimal] = None
    notes: Optional[str] = None


class CertificationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    standard_version: Optional[str] = None
    scope: Optional[str] = None
    certification_body: Optional[str] = None
    status: Optional[CertificationStatusEnum] = None
    current_certificate_date: Optional[date] = None
    expiry_date: Optional[date] = None
    certificate_number: Optional[str] = None
    certificate_file: Optional[str] = None
    next_surveillance_date: Optional[date] = None
    next_renewal_date: Optional[date] = None
    manager_id: Optional[int] = None
    annual_cost: Optional[Decimal] = None
    notes: Optional[str] = None


class CertificationResponse(CertificationBase):
    id: int
    standard_version: Optional[str] = None
    scope: Optional[str] = None
    certification_body: Optional[str] = None
    certification_body_accreditation: Optional[str] = None
    initial_certification_date: Optional[date] = None
    current_certificate_date: Optional[date] = None
    expiry_date: Optional[date] = None
    next_surveillance_date: Optional[date] = None
    next_renewal_date: Optional[date] = None
    certificate_number: Optional[str] = None
    certificate_file: Optional[str] = None
    status: CertificationStatusEnum
    manager_id: Optional[int] = None
    annual_cost: Optional[Decimal] = None
    audits: List[CertificationAuditResponse] = []
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================================
# LISTES PAGINÉES
# ============================================================================

class PaginatedNCResponse(BaseModel):
    items: List[NonConformanceResponse]
    total: int
    skip: int
    limit: int


class PaginatedControlTemplateResponse(BaseModel):
    items: List[ControlTemplateResponse]
    total: int
    skip: int
    limit: int


class PaginatedControlResponse(BaseModel):
    items: List[ControlResponse]
    total: int
    skip: int
    limit: int


class PaginatedAuditResponse(BaseModel):
    items: List[AuditResponse]
    total: int
    skip: int
    limit: int


class PaginatedCAPAResponse(BaseModel):
    items: List[CAPAResponse]
    total: int
    skip: int
    limit: int


class PaginatedClaimResponse(BaseModel):
    items: List[ClaimResponse]
    total: int
    skip: int
    limit: int


class PaginatedIndicatorResponse(BaseModel):
    items: List[IndicatorResponse]
    total: int
    skip: int
    limit: int


class PaginatedCertificationResponse(BaseModel):
    items: List[CertificationResponse]
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
    nc_by_type: Dict[str, int] = {}
    nc_by_status: Dict[str, int] = {}

    # Contrôles qualité
    controls_total: int = 0
    controls_completed: int = 0
    controls_pass_rate: Decimal = Decimal("0")
    controls_by_type: Dict[str, int] = {}

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
    claims_avg_resolution_days: Optional[Decimal] = None
    claims_satisfaction_rate: Optional[Decimal] = None

    # Certifications
    certifications_active: int = 0
    certifications_expiring_soon: int = 0

    # Indicateurs
    indicators_on_target: int = 0
    indicators_warning: int = 0
    indicators_critical: int = 0

    # Tendances
    nc_trend_30_days: List[Dict[str, Any]] = []
    control_trend_30_days: List[Dict[str, Any]] = []
