"""
AZALS MODULE M3 - Schémas RH
============================

Schémas Pydantic pour la gestion des ressources humaines.
"""


import json
import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import (
    ContractType,
    DocumentType,
    EmployeeStatus,
    EvaluationStatus,
    EvaluationType,
    LeaveStatus,
    LeaveType,
    PayElementType,
    PayrollStatus,
    TrainingStatus,
    TrainingType,
)

# ============================================================================
# SCHÉMAS DÉPARTEMENTS
# ============================================================================

class DepartmentBase(BaseModel):
    """Base pour les départements."""
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    parent_id: UUID | None = None
    manager_id: UUID | None = None
    cost_center: str | None = None


class DepartmentCreate(DepartmentBase):
    """Création d'un département."""
    pass


class DepartmentUpdate(BaseModel):
    """Mise à jour d'un département."""
    name: str | None = None
    description: str | None = None
    parent_id: UUID | None = None
    manager_id: UUID | None = None
    cost_center: str | None = None
    is_active: bool | None = None


class DepartmentResponse(DepartmentBase):
    """Réponse département."""
    id: UUID
    is_active: bool = True
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS POSTES
# ============================================================================

class PositionBase(BaseModel):
    """Base pour les postes."""
    code: str = Field(..., min_length=1, max_length=20)
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    department_id: UUID | None = None
    category: str | None = None
    level: int = 1
    min_salary: Decimal | None = None
    max_salary: Decimal | None = None
    requirements: list[str] = Field(default_factory=list)


class PositionCreate(PositionBase):
    """Création d'un poste."""
    pass


class PositionUpdate(BaseModel):
    """Mise à jour d'un poste."""
    title: str | None = None
    description: str | None = None
    department_id: UUID | None = None
    category: str | None = None
    level: int | None = None
    min_salary: Decimal | None = None
    max_salary: Decimal | None = None
    requirements: list[str] | None = None
    is_active: bool | None = None


class PositionResponse(PositionBase):
    """Réponse poste."""
    id: UUID
    is_active: bool = True
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS EMPLOYÉS
# ============================================================================

class EmployeeBase(BaseModel):
    """Base pour les employés."""
    employee_number: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    maiden_name: str | None = None
    gender: str | None = None
    birth_date: datetime.date | None = None
    birth_place: str | None = None
    nationality: str | None = None
    social_security_number: str | None = None
    email: str | None = None
    personal_email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str = "France"


class EmployeeCreate(EmployeeBase):
    """Création d'un employé."""
    user_id: int | None = None
    department_id: UUID | None = None
    position_id: UUID | None = None
    manager_id: UUID | None = None
    work_location: str | None = None
    contract_type: ContractType | None = None
    hire_date: datetime.date | None = None
    start_date: datetime.date | None = None
    gross_salary: Decimal | None = None
    currency: str = "EUR"
    weekly_hours: Decimal = Decimal("35.0")
    bank_name: str | None = None
    iban: str | None = None
    bic: str | None = None


class EmployeeUpdate(BaseModel):
    """Mise à jour d'un employé."""
    first_name: str | None = None
    last_name: str | None = None
    maiden_name: str | None = None
    gender: str | None = None
    birth_date: datetime.date | None = None
    birth_place: str | None = None
    nationality: str | None = None
    email: str | None = None
    personal_email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str | None = None
    department_id: UUID | None = None
    position_id: UUID | None = None
    manager_id: UUID | None = None
    work_location: str | None = None
    status: EmployeeStatus | None = None
    gross_salary: Decimal | None = None
    weekly_hours: Decimal | None = None
    bank_name: str | None = None
    iban: str | None = None
    bic: str | None = None
    photo_url: str | None = None
    notes: str | None = None
    tags: list[str] | None = None
    is_active: bool | None = None


class EmployeeResponse(EmployeeBase):
    """Réponse employé."""
    id: UUID
    user_id: int | None = None
    department_id: UUID | None = None
    position_id: UUID | None = None
    manager_id: UUID | None = None
    work_location: str | None = None
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    contract_type: ContractType | None = None
    hire_date: datetime.date | None = None
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None
    gross_salary: Decimal | None = None
    currency: str = "EUR"
    weekly_hours: Decimal = Decimal("35.0")
    annual_leave_balance: Decimal = Decimal("0")
    rtt_balance: Decimal = Decimal("0")
    photo_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator('tags', mode='before')
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else []
        return v or []


class EmployeeList(BaseModel):
    """Liste d'employés."""
    items: list[EmployeeResponse]
    total: int


# ============================================================================
# SCHÉMAS CONTRATS
# ============================================================================

class ContractBase(BaseModel):
    """Base pour les contrats."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    contract_number: str = Field(..., min_length=1, max_length=50)
    contract_type: ContractType = Field(..., alias="type")
    title: str | None = None
    department_id: UUID | None = None
    position_id: UUID | None = None
    start_date: datetime.date
    end_date: datetime.date | None = None
    probation_duration: int | None = None
    gross_salary: Decimal
    currency: str = "EUR"
    pay_frequency: str = "MONTHLY"
    weekly_hours: Decimal = Decimal("35.0")
    work_schedule: str = "FULL_TIME"


class ContractCreate(ContractBase):
    """Création d'un contrat."""
    employee_id: UUID
    bonus_clause: str | None = None
    notice_period: int | None = None
    non_compete_clause: bool = False
    confidentiality_clause: bool = True


class ContractResponse(ContractBase):
    """Réponse contrat."""
    id: UUID
    employee_id: UUID
    probation_end_date: datetime.date | None = None
    signed_date: datetime.date | None = None
    is_current: bool = True
    terminated_date: datetime.date | None = None
    termination_reason: str | None = None
    document_url: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS CONGÉS
# ============================================================================

class LeaveRequestBase(BaseModel):
    """Base pour les demandes de congé."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    leave_type: LeaveType = Field(..., alias="type")
    start_date: datetime.date
    end_date: datetime.date
    start_half_day: bool = Field(default=False, alias="half_day_start")
    end_half_day: bool = Field(default=False, alias="half_day_end")
    reason: str | None = None
    replacement_id: UUID | None = None


class LeaveRequestCreate(LeaveRequestBase):
    """Création d'une demande de congé."""
    pass


class LeaveRequestUpdate(BaseModel):
    """Mise à jour d'une demande de congé."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    leave_type: LeaveType | None = Field(default=None, alias="type")
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None
    start_half_day: bool | None = Field(default=None, alias="half_day_start")
    end_half_day: bool | None = Field(default=None, alias="half_day_end")
    reason: str | None = None
    replacement_id: UUID | None = None
    resubmit: bool = Field(default=False, description="Si True, remet le statut en PENDING")


class LeaveRequestResponse(LeaveRequestBase):
    """Réponse demande de congé."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=(), populate_by_name=True, serialize_by_alias=True)

    id: UUID
    employee_id: UUID
    employee_name: str | None = None
    status: LeaveStatus = LeaveStatus.PENDING
    days_count: Decimal = Field(..., alias="days")
    attachment_url: str | None = None
    approved_by: UUID | None = None
    approved_at: datetime.datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime | None = None



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
    start_date: datetime.date
    end_date: datetime.date
    payment_date: datetime.date | None = None


class PayrollPeriodCreate(PayrollPeriodBase):
    """Création d'une période de paie."""
    pass


class PayrollPeriodResponse(PayrollPeriodBase):
    """Réponse période de paie."""
    id: UUID
    status: PayrollStatus = PayrollStatus.DRAFT
    is_closed: bool = False
    closed_at: datetime.datetime | None = None
    total_gross: Decimal = Decimal("0")
    total_net: Decimal = Decimal("0")
    total_employer_charges: Decimal = Decimal("0")
    employee_count: int = 0
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class PayslipLineCreate(BaseModel):
    """Création d'une ligne de bulletin."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    element_type: PayElementType = Field(..., alias="type")
    code: str
    label: str
    base: Decimal | None = None
    rate: Decimal | None = None
    quantity: Decimal | None = None
    amount: Decimal
    is_deduction: bool = False
    is_employer_charge: bool = False


class PayslipLineResponse(PayslipLineCreate):
    """Réponse ligne de bulletin."""
    id: UUID
    payslip_id: UUID
    line_number: int
    created_at: datetime.datetime



class PayslipCreate(BaseModel):
    """Création d'un bulletin de paie."""
    employee_id: UUID
    period_id: UUID
    start_date: datetime.date
    end_date: datetime.date
    payment_date: datetime.date | None = None
    worked_hours: Decimal = Decimal("0")
    overtime_hours: Decimal = Decimal("0")
    absence_hours: Decimal = Decimal("0")
    gross_salary: Decimal
    lines: list[PayslipLineCreate] = Field(default_factory=list)


class PayslipResponse(BaseModel):
    """Réponse bulletin de paie."""
    id: UUID
    employee_id: UUID
    period_id: UUID
    payslip_number: str
    status: PayrollStatus = PayrollStatus.DRAFT
    start_date: datetime.date
    end_date: datetime.date
    payment_date: datetime.date | None = None
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
    document_url: str | None = None
    sent_at: datetime.datetime | None = None
    validated_by: UUID | None = None
    validated_at: datetime.datetime | None = None
    paid_at: datetime.datetime | None = None
    lines: list[PayslipLineResponse] = Field(default_factory=list)
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS TEMPS DE TRAVAIL
# ============================================================================

class TimeEntryBase(BaseModel):
    """Base pour les entrées de temps."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    entry_date: datetime.date = Field(..., alias="date")
    start_time: datetime.datetime | None = None
    end_time: datetime.datetime | None = None
    break_duration: int = 0
    worked_hours: Decimal
    overtime_hours: Decimal = Decimal("0")
    project_id: UUID | None = None
    task_description: str | None = None


class TimeEntryCreate(TimeEntryBase):
    """Création d'une entrée de temps."""
    pass


class TimeEntryResponse(TimeEntryBase):
    """Réponse entrée de temps."""
    id: UUID
    employee_id: UUID
    is_approved: bool = False
    approved_by: UUID | None = None
    approved_at: datetime.datetime | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime



# ============================================================================
# SCHÉMAS COMPÉTENCES
# ============================================================================

class SkillBase(BaseModel):
    """Base pour les compétences."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    category: str | None = None
    description: str | None = None


class SkillCreate(SkillBase):
    """Création d'une compétence."""
    pass


class SkillResponse(SkillBase):
    """Réponse compétence."""
    id: UUID
    is_active: bool = True
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class EmployeeSkillCreate(BaseModel):
    """Création d'une compétence employé."""
    skill_id: UUID
    level: int = Field(1, ge=1, le=5)
    acquired_date: datetime.date | None = None
    expiry_date: datetime.date | None = None
    certification_url: str | None = None
    notes: str | None = None


class EmployeeSkillResponse(EmployeeSkillCreate):
    """Réponse compétence employé."""
    id: UUID
    employee_id: UUID
    validated_by: UUID | None = None
    validated_at: datetime.datetime | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS FORMATIONS
# ============================================================================

class TrainingBase(BaseModel):
    """Base pour les formations."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    training_type: TrainingType = Field(..., alias="type")
    provider: str | None = None
    trainer: str | None = None
    location: str | None = None
    start_date: datetime.date
    end_date: datetime.date
    duration_hours: Decimal | None = None
    max_participants: int | None = None
    cost_per_person: Decimal | None = None


class TrainingCreate(TrainingBase):
    """Création d'une formation."""
    skills_acquired: list[UUID] = Field(default_factory=list)


class TrainingResponse(TrainingBase):
    """Réponse formation."""
    id: UUID
    status: TrainingStatus = TrainingStatus.PLANNED
    total_cost: Decimal | None = None
    skills_acquired: list[UUID] = Field(default_factory=list)
    created_by: UUID | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

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
    attendance_rate: Decimal | None = None
    score: Decimal | None = None
    passed: bool | None = None
    certificate_url: str | None = None
    feedback: str | None = None
    enrolled_at: datetime.datetime
    completed_at: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS ÉVALUATIONS
# ============================================================================

class EvaluationBase(BaseModel):
    """Base pour les évaluations."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    evaluation_type: EvaluationType = Field(..., alias="type")
    period_start: datetime.date
    period_end: datetime.date
    scheduled_date: datetime.date | None = None
    evaluator_id: UUID | None = None


class EvaluationCreate(EvaluationBase):
    """Création d'une évaluation."""
    employee_id: UUID


class EvaluationUpdate(BaseModel):
    """Mise à jour d'une évaluation."""
    status: EvaluationStatus | None = None
    completed_date: datetime.date | None = None
    overall_score: Decimal | None = None
    objectives_score: Decimal | None = None
    skills_score: Decimal | None = None
    behavior_score: Decimal | None = None
    objectives_achieved: list[str] | None = None
    objectives_next: list[str] | None = None
    strengths: str | None = None
    improvements: str | None = None
    employee_comments: str | None = None
    evaluator_comments: str | None = None
    promotion_recommended: bool | None = None
    salary_increase_recommended: bool | None = None
    training_needs: list[str] | None = None


class EvaluationResponse(EvaluationBase):
    """Réponse évaluation."""
    id: UUID
    employee_id: UUID
    status: EvaluationStatus = EvaluationStatus.SCHEDULED
    completed_date: datetime.date | None = None
    overall_score: Decimal | None = None
    objectives_score: Decimal | None = None
    skills_score: Decimal | None = None
    behavior_score: Decimal | None = None
    objectives_achieved: list[str] = Field(default_factory=list)
    objectives_next: list[str] = Field(default_factory=list)
    strengths: str | None = None
    improvements: str | None = None
    employee_comments: str | None = None
    evaluator_comments: str | None = None
    promotion_recommended: bool = False
    salary_increase_recommended: bool = False
    training_needs: list[str] = Field(default_factory=list)
    employee_signed_at: datetime.datetime | None = None
    evaluator_signed_at: datetime.datetime | None = None
    document_url: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

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
    description: str | None = None
    file_url: str
    file_size: int | None = None
    mime_type: str | None = None
    issue_date: datetime.date | None = None
    expiry_date: datetime.date | None = None
    is_confidential: bool = False


class HRDocumentResponse(BaseModel):
    """Réponse document RH."""
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True, populate_by_name=True)

    id: UUID
    employee_id: UUID
    document_type: DocumentType = Field(..., alias="type")
    name: str
    description: str | None = None
    file_url: str
    file_size: int | None = None
    mime_type: str | None = None
    issue_date: datetime.date | None = None
    expiry_date: datetime.date | None = None
    is_confidential: bool = False
    uploaded_by: UUID | None = None
    created_at: datetime.datetime


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
