"""
AZALS MODULE M3 - Schémas RH
============================

Schémas Pydantic pour la gestion des ressources humaines.
"""

from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID
import json

from .models import (
    ContractType, EmployeeStatus, LeaveType, LeaveStatus,
    PayrollStatus, PayElementType, DocumentType,
    EvaluationType, EvaluationStatus, TrainingType, TrainingStatus
)


# ============================================================================
# SCHÉMAS DÉPARTEMENTS
# ============================================================================

class DepartmentBase(BaseModel):
    """Base pour les départements."""
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    cost_center: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    """Création d'un département."""
    pass


class DepartmentUpdate(BaseModel):
    """Mise à jour d'un département."""
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    cost_center: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    """Réponse département."""
    id: UUID
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS POSTES
# ============================================================================

class PositionBase(BaseModel):
    """Base pour les postes."""
    code: str = Field(..., min_length=1, max_length=20)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    department_id: Optional[UUID] = None
    category: Optional[str] = None
    level: int = 1
    min_salary: Optional[Decimal] = None
    max_salary: Optional[Decimal] = None
    requirements: List[str] = Field(default_factory=list)


class PositionCreate(PositionBase):
    """Création d'un poste."""
    pass


class PositionUpdate(BaseModel):
    """Mise à jour d'un poste."""
    title: Optional[str] = None
    description: Optional[str] = None
    department_id: Optional[UUID] = None
    category: Optional[str] = None
    level: Optional[int] = None
    min_salary: Optional[Decimal] = None
    max_salary: Optional[Decimal] = None
    requirements: Optional[List[str]] = None
    is_active: Optional[bool] = None


class PositionResponse(PositionBase):
    """Réponse poste."""
    id: UUID
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS EMPLOYÉS
# ============================================================================

class EmployeeBase(BaseModel):
    """Base pour les employés."""
    employee_number: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    maiden_name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    birth_place: Optional[str] = None
    nationality: Optional[str] = None
    social_security_number: Optional[str] = None
    email: Optional[str] = None
    personal_email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: str = "France"


class EmployeeCreate(EmployeeBase):
    """Création d'un employé."""
    user_id: Optional[int] = None
    department_id: Optional[UUID] = None
    position_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    work_location: Optional[str] = None
    contract_type: Optional[ContractType] = None
    hire_date: Optional[date] = None
    start_date: Optional[date] = None
    gross_salary: Optional[Decimal] = None
    currency: str = "EUR"
    weekly_hours: Decimal = Decimal("35.0")
    bank_name: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None


class EmployeeUpdate(BaseModel):
    """Mise à jour d'un employé."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    maiden_name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    birth_place: Optional[str] = None
    nationality: Optional[str] = None
    email: Optional[str] = None
    personal_email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    department_id: Optional[UUID] = None
    position_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    work_location: Optional[str] = None
    status: Optional[EmployeeStatus] = None
    gross_salary: Optional[Decimal] = None
    weekly_hours: Optional[Decimal] = None
    bank_name: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class EmployeeResponse(EmployeeBase):
    """Réponse employé."""
    id: UUID
    user_id: Optional[int] = None
    department_id: Optional[UUID] = None
    position_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    work_location: Optional[str] = None
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    contract_type: Optional[ContractType] = None
    hire_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gross_salary: Optional[Decimal] = None
    currency: str = "EUR"
    weekly_hours: Decimal = Decimal("35.0")
    annual_leave_balance: Decimal = Decimal("0")
    rtt_balance: Decimal = Decimal("0")
    photo_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator('tags', mode='before')
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else []
        return v or []


class EmployeeList(BaseModel):
    """Liste d'employés."""
    items: List[EmployeeResponse]
    total: int


# ============================================================================
# SCHÉMAS CONTRATS
# ============================================================================

class ContractBase(BaseModel):
    """Base pour les contrats."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    contract_number: str = Field(..., min_length=1, max_length=50)
    contract_type: ContractType = Field(..., alias="type")
    title: Optional[str] = None
    department_id: Optional[UUID] = None
    position_id: Optional[UUID] = None
    start_date: date
    end_date: Optional[date] = None
    probation_duration: Optional[int] = None
    gross_salary: Decimal
    currency: str = "EUR"
    pay_frequency: str = "MONTHLY"
    weekly_hours: Decimal = Decimal("35.0")
    work_schedule: str = "FULL_TIME"


class ContractCreate(ContractBase):
    """Création d'un contrat."""
    employee_id: UUID
    bonus_clause: Optional[str] = None
    notice_period: Optional[int] = None
    non_compete_clause: bool = False
    confidentiality_clause: bool = True


class ContractResponse(ContractBase):
    """Réponse contrat."""
    id: UUID
    employee_id: UUID
    probation_end_date: Optional[date] = None
    signed_date: Optional[date] = None
    is_current: bool = True
    terminated_date: Optional[date] = None
    termination_reason: Optional[str] = None
    document_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS CONGÉS
# ============================================================================

class LeaveRequestBase(BaseModel):
    """Base pour les demandes de congé."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    leave_type: LeaveType = Field(..., alias="type")
    start_date: date
    end_date: date
    start_half_day: bool = False
    end_half_day: bool = False
    reason: Optional[str] = None
    replacement_id: Optional[UUID] = None


class LeaveRequestCreate(LeaveRequestBase):
    """Création d'une demande de congé."""
    pass


class LeaveRequestResponse(LeaveRequestBase):
    """Réponse demande de congé."""
    id: UUID
    employee_id: UUID
    status: LeaveStatus = LeaveStatus.PENDING
    days_count: Decimal
    attachment_url: Optional[str] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime



class LeaveBalanceResponse(BaseModel):
    """Réponse solde de congés."""
    id: UUID
    employee_id: UUID
    year: int
    leave_type: LeaveType
    entitled_days: Decimal = Decimal("0")
    taken_days: Decimal = Decimal("0")
    pending_days: Decimal = Decimal("0")
    remaining_days: Decimal = Decimal("0")
    carried_over: Decimal = Decimal("0")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS PAIE
# ============================================================================

class PayrollPeriodBase(BaseModel):
    """Base pour les périodes de paie."""
    name: str = Field(..., min_length=1, max_length=100)
    year: int
    month: int
    start_date: date
    end_date: date
    payment_date: Optional[date] = None


class PayrollPeriodCreate(PayrollPeriodBase):
    """Création d'une période de paie."""
    pass


class PayrollPeriodResponse(PayrollPeriodBase):
    """Réponse période de paie."""
    id: UUID
    status: PayrollStatus = PayrollStatus.DRAFT
    is_closed: bool = False
    closed_at: Optional[datetime] = None
    total_gross: Decimal = Decimal("0")
    total_net: Decimal = Decimal("0")
    total_employer_charges: Decimal = Decimal("0")
    employee_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PayslipLineCreate(BaseModel):
    """Création d'une ligne de bulletin."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    element_type: PayElementType = Field(..., alias="type")
    code: str
    label: str
    base: Optional[Decimal] = None
    rate: Optional[Decimal] = None
    quantity: Optional[Decimal] = None
    amount: Decimal
    is_deduction: bool = False
    is_employer_charge: bool = False


class PayslipLineResponse(PayslipLineCreate):
    """Réponse ligne de bulletin."""
    id: UUID
    payslip_id: UUID
    line_number: int
    created_at: datetime



class PayslipCreate(BaseModel):
    """Création d'un bulletin de paie."""
    employee_id: UUID
    period_id: UUID
    start_date: date
    end_date: date
    payment_date: Optional[date] = None
    worked_hours: Decimal = Decimal("0")
    overtime_hours: Decimal = Decimal("0")
    absence_hours: Decimal = Decimal("0")
    gross_salary: Decimal
    lines: List[PayslipLineCreate] = Field(default_factory=list)


class PayslipResponse(BaseModel):
    """Réponse bulletin de paie."""
    id: UUID
    employee_id: UUID
    period_id: UUID
    payslip_number: str
    status: PayrollStatus = PayrollStatus.DRAFT
    start_date: date
    end_date: date
    payment_date: Optional[date] = None
    worked_hours: Decimal = Decimal("0")
    overtime_hours: Decimal = Decimal("0")
    absence_hours: Decimal = Decimal("0")
    gross_salary: Decimal
    total_gross: Decimal = Decimal("0")
    total_deductions: Decimal = Decimal("0")
    employee_charges: Decimal = Decimal("0")
    employer_charges: Decimal = Decimal("0")
    taxable_income: Decimal = Decimal("0")
    tax_withheld: Decimal = Decimal("0")
    net_before_tax: Decimal = Decimal("0")
    net_salary: Decimal = Decimal("0")
    ytd_gross: Decimal = Decimal("0")
    ytd_net: Decimal = Decimal("0")
    ytd_tax: Decimal = Decimal("0")
    document_url: Optional[str] = None
    sent_at: Optional[datetime] = None
    validated_by: Optional[UUID] = None
    validated_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    lines: List[PayslipLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS TEMPS DE TRAVAIL
# ============================================================================

class TimeEntryBase(BaseModel):
    """Base pour les entrées de temps."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    entry_date: date = Field(..., alias="date")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    break_duration: int = 0
    worked_hours: Decimal
    overtime_hours: Decimal = Decimal("0")
    project_id: Optional[UUID] = None
    task_description: Optional[str] = None


class TimeEntryCreate(TimeEntryBase):
    """Création d'une entrée de temps."""
    pass


class TimeEntryResponse(TimeEntryBase):
    """Réponse entrée de temps."""
    id: UUID
    employee_id: UUID
    is_approved: bool = False
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime



# ============================================================================
# SCHÉMAS COMPÉTENCES
# ============================================================================

class SkillBase(BaseModel):
    """Base pour les compétences."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = None
    description: Optional[str] = None


class SkillCreate(SkillBase):
    """Création d'une compétence."""
    pass


class SkillResponse(SkillBase):
    """Réponse compétence."""
    id: UUID
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmployeeSkillCreate(BaseModel):
    """Création d'une compétence employé."""
    skill_id: UUID
    level: int = Field(1, ge=1, le=5)
    acquired_date: Optional[date] = None
    expiry_date: Optional[date] = None
    certification_url: Optional[str] = None
    notes: Optional[str] = None


class EmployeeSkillResponse(EmployeeSkillCreate):
    """Réponse compétence employé."""
    id: UUID
    employee_id: UUID
    validated_by: Optional[UUID] = None
    validated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS FORMATIONS
# ============================================================================

class TrainingBase(BaseModel):
    """Base pour les formations."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    training_type: TrainingType = Field(..., alias="type")
    provider: Optional[str] = None
    trainer: Optional[str] = None
    location: Optional[str] = None
    start_date: date
    end_date: date
    duration_hours: Optional[Decimal] = None
    max_participants: Optional[int] = None
    cost_per_person: Optional[Decimal] = None


class TrainingCreate(TrainingBase):
    """Création d'une formation."""
    skills_acquired: List[UUID] = Field(default_factory=list)


class TrainingResponse(TrainingBase):
    """Réponse formation."""
    id: UUID
    status: TrainingStatus = TrainingStatus.PLANNED
    total_cost: Optional[Decimal] = None
    skills_acquired: List[UUID] = Field(default_factory=list)
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrainingParticipantCreate(BaseModel):
    """Inscription à une formation."""
    employee_id: UUID


class TrainingParticipantResponse(BaseModel):
    """Réponse participant formation."""
    id: UUID
    training_id: UUID
    employee_id: UUID
    status: str = "ENROLLED"
    attendance_rate: Optional[Decimal] = None
    score: Optional[Decimal] = None
    passed: Optional[bool] = None
    certificate_url: Optional[str] = None
    feedback: Optional[str] = None
    enrolled_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS ÉVALUATIONS
# ============================================================================

class EvaluationBase(BaseModel):
    """Base pour les évaluations."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    evaluation_type: EvaluationType = Field(..., alias="type")
    period_start: date
    period_end: date
    scheduled_date: Optional[date] = None
    evaluator_id: Optional[UUID] = None


class EvaluationCreate(EvaluationBase):
    """Création d'une évaluation."""
    employee_id: UUID


class EvaluationUpdate(BaseModel):
    """Mise à jour d'une évaluation."""
    status: Optional[EvaluationStatus] = None
    completed_date: Optional[date] = None
    overall_score: Optional[Decimal] = None
    objectives_score: Optional[Decimal] = None
    skills_score: Optional[Decimal] = None
    behavior_score: Optional[Decimal] = None
    objectives_achieved: Optional[List[str]] = None
    objectives_next: Optional[List[str]] = None
    strengths: Optional[str] = None
    improvements: Optional[str] = None
    employee_comments: Optional[str] = None
    evaluator_comments: Optional[str] = None
    promotion_recommended: Optional[bool] = None
    salary_increase_recommended: Optional[bool] = None
    training_needs: Optional[List[str]] = None


class EvaluationResponse(EvaluationBase):
    """Réponse évaluation."""
    id: UUID
    employee_id: UUID
    status: EvaluationStatus = EvaluationStatus.SCHEDULED
    completed_date: Optional[date] = None
    overall_score: Optional[Decimal] = None
    objectives_score: Optional[Decimal] = None
    skills_score: Optional[Decimal] = None
    behavior_score: Optional[Decimal] = None
    objectives_achieved: List[str] = Field(default_factory=list)
    objectives_next: List[str] = Field(default_factory=list)
    strengths: Optional[str] = None
    improvements: Optional[str] = None
    employee_comments: Optional[str] = None
    evaluator_comments: Optional[str] = None
    promotion_recommended: bool = False
    salary_increase_recommended: bool = False
    training_needs: List[str] = Field(default_factory=list)
    employee_signed_at: Optional[datetime] = None
    evaluator_signed_at: Optional[datetime] = None
    document_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS DOCUMENTS
# ============================================================================

class HRDocumentCreate(BaseModel):
    """Création d'un document RH."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    employee_id: UUID
    document_type: DocumentType = Field(..., alias="type")
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    file_url: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    is_confidential: bool = False


class HRDocumentResponse(BaseModel):
    """Réponse document RH."""
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True, populate_by_name=True)

    id: UUID
    employee_id: UUID
    document_type: DocumentType = Field(..., alias="type")
    name: str
    description: Optional[str] = None
    file_url: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    is_confidential: bool = False
    uploaded_by: Optional[UUID] = None
    created_at: datetime


# ============================================================================
# SCHÉMAS DASHBOARD
# ============================================================================

class HRDashboard(BaseModel):
    """Dashboard RH."""
    # Effectifs
    total_employees: int = 0
    active_employees: int = 0
    on_leave_employees: int = 0
    new_hires_this_month: int = 0
    departures_this_month: int = 0

    # Contrats
    cdi_count: int = 0
    cdd_count: int = 0
    probation_ending_soon: int = 0
    contracts_ending_soon: int = 0

    # Congés
    pending_leave_requests: int = 0
    employees_on_leave_today: int = 0
    average_leave_balance: Decimal = Decimal("0")

    # Paie
    current_payroll_status: str = "NONE"
    last_payroll_total: Decimal = Decimal("0")
    average_salary: Decimal = Decimal("0")

    # Formation
    trainings_in_progress: int = 0
    employees_trained_this_year: int = 0

    # Évaluations
    pending_evaluations: int = 0
    overdue_evaluations: int = 0

    # Répartition
    by_department: dict = {}
    by_contract_type: dict = {}
    by_gender: dict = {}
