"""
AZALS MODULE M3 - Modèles RH
============================

Modèles SQLAlchemy pour la gestion des ressources humaines.
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Text, Boolean, ForeignKey,
    Integer, Numeric, Date, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


# ============================================================================
# ENUMS
# ============================================================================

class ContractType(str, enum.Enum):
    """Types de contrats."""
    CDI = "CDI"
    CDD = "CDD"
    INTERIM = "INTERIM"
    STAGE = "STAGE"
    APPRENTISSAGE = "APPRENTISSAGE"
    FREELANCE = "FREELANCE"


class EmployeeStatus(str, enum.Enum):
    """Statuts d'employé."""
    ACTIVE = "ACTIVE"
    ON_LEAVE = "ON_LEAVE"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"
    RETIRED = "RETIRED"


class LeaveType(str, enum.Enum):
    """Types de congés."""
    PAID = "PAID"
    UNPAID = "UNPAID"
    SICK = "SICK"
    MATERNITY = "MATERNITY"
    PATERNITY = "PATERNITY"
    PARENTAL = "PARENTAL"
    RTT = "RTT"
    TRAINING = "TRAINING"
    SPECIAL = "SPECIAL"
    COMPENSATION = "COMPENSATION"


class LeaveStatus(str, enum.Enum):
    """Statuts de demande de congé."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class PayrollStatus(str, enum.Enum):
    """Statuts de paie."""
    DRAFT = "DRAFT"
    CALCULATED = "CALCULATED"
    VALIDATED = "VALIDATED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class PayElementType(str, enum.Enum):
    """Types d'éléments de paie."""
    GROSS_SALARY = "GROSS_SALARY"
    BONUS = "BONUS"
    COMMISSION = "COMMISSION"
    OVERTIME = "OVERTIME"
    ALLOWANCE = "ALLOWANCE"
    DEDUCTION = "DEDUCTION"
    SOCIAL_CHARGE = "SOCIAL_CHARGE"
    EMPLOYER_CHARGE = "EMPLOYER_CHARGE"
    TAX = "TAX"
    ADVANCE = "ADVANCE"
    REIMBURSEMENT = "REIMBURSEMENT"


class DocumentType(str, enum.Enum):
    """Types de documents RH."""
    CONTRACT = "CONTRACT"
    AMENDMENT = "AMENDMENT"
    PAYSLIP = "PAYSLIP"
    CERTIFICATE = "CERTIFICATE"
    WARNING = "WARNING"
    EVALUATION = "EVALUATION"
    TRAINING_CERT = "TRAINING_CERT"
    ID_DOCUMENT = "ID_DOCUMENT"
    OTHER = "OTHER"


class EvaluationType(str, enum.Enum):
    """Types d'évaluations."""
    ANNUAL = "ANNUAL"
    PROBATION = "PROBATION"
    PROJECT = "PROJECT"
    PROMOTION = "PROMOTION"
    EXIT = "EXIT"


class EvaluationStatus(str, enum.Enum):
    """Statuts d'évaluation."""
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TrainingType(str, enum.Enum):
    """Types de formation."""
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"
    ONLINE = "ONLINE"
    ON_THE_JOB = "ON_THE_JOB"
    CERTIFICATION = "CERTIFICATION"


class TrainingStatus(str, enum.Enum):
    """Statuts de formation."""
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# ============================================================================
# MODÈLES ORGANISATION
# ============================================================================

class Department(Base):
    """Département/Service."""
    __tablename__ = "hr_departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    code = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("hr_departments.id"), nullable=True)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("hr_employees.id"), nullable=True)
    cost_center = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='unique_department_code'),
        Index('idx_departments_tenant', 'tenant_id'),
    )


class Position(Base):
    """Poste/Fonction."""
    __tablename__ = "hr_positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    code = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("hr_departments.id"), nullable=True)
    category = Column(String(50), nullable=True)  # CADRE, NON_CADRE, etc.
    level = Column(Integer, default=1)
    min_salary = Column(Numeric(12, 2), nullable=True)
    max_salary = Column(Numeric(12, 2), nullable=True)
    requirements = Column(JSONB, default=list)  # Compétences requises
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='unique_position_code'),
        Index('idx_positions_tenant', 'tenant_id'),
        Index('idx_positions_department', 'tenant_id', 'department_id'),
    )


# ============================================================================
# MODÈLES EMPLOYÉS
# ============================================================================

class Employee(Base):
    """Employé."""
    __tablename__ = "hr_employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identifiants
    employee_number = Column(String(50), nullable=False)
    user_id = Column(Integer, nullable=True)  # Lien vers User si existe

    # Informations personnelles
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    maiden_name = Column(String(100), nullable=True)
    gender = Column(String(10), nullable=True)  # M, F, OTHER
    birth_date = Column(Date, nullable=True)
    birth_place = Column(String(255), nullable=True)
    nationality = Column(String(100), nullable=True)
    social_security_number = Column(String(50), nullable=True)

    # Contact
    email = Column(String(255), nullable=True)
    personal_email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    mobile = Column(String(50), nullable=True)

    # Adresse
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    postal_code = Column(String(20), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), default="France")

    # Organisation
    department_id = Column(UUID(as_uuid=True), ForeignKey("hr_departments.id"), nullable=True)
    position_id = Column(UUID(as_uuid=True), ForeignKey("hr_positions.id"), nullable=True)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("hr_employees.id"), nullable=True)
    work_location = Column(String(255), nullable=True)

    # Contrat actuel
    status = Column(SQLEnum(EmployeeStatus), default=EmployeeStatus.ACTIVE)
    contract_type = Column(SQLEnum(ContractType), nullable=True)
    hire_date = Column(Date, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    seniority_date = Column(Date, nullable=True)
    probation_end_date = Column(Date, nullable=True)

    # Rémunération
    gross_salary = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="EUR")
    pay_frequency = Column(String(20), default="MONTHLY")  # MONTHLY, WEEKLY, etc.

    # Temps de travail
    weekly_hours = Column(Numeric(5, 2), default=35.0)
    work_schedule = Column(String(50), nullable=True)  # FULL_TIME, PART_TIME

    # Congés
    annual_leave_balance = Column(Numeric(5, 2), default=0)
    rtt_balance = Column(Numeric(5, 2), default=0)

    # Banque
    bank_name = Column(String(255), nullable=True)
    iban = Column(String(50), nullable=True)
    bic = Column(String(20), nullable=True)

    # Photo
    photo_url = Column(String(500), nullable=True)

    # Métadonnées
    notes = Column(Text, nullable=True)
    tags = Column(JSONB, default=list)
    custom_fields = Column(JSONB, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    department = relationship("Department", foreign_keys=[department_id])
    position = relationship("Position", foreign_keys=[position_id])

    __table_args__ = (
        UniqueConstraint('tenant_id', 'employee_number', name='unique_employee_number'),
        Index('idx_employees_tenant', 'tenant_id'),
        Index('idx_employees_department', 'tenant_id', 'department_id'),
        Index('idx_employees_manager', 'tenant_id', 'manager_id'),
        Index('idx_employees_status', 'tenant_id', 'status'),
    )


class Contract(Base):
    """Contrat de travail."""
    __tablename__ = "hr_contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hr_employees.id"), nullable=False)

    contract_number = Column(String(50), nullable=False)
    type = Column(SQLEnum(ContractType), nullable=False)
    title = Column(String(255), nullable=True)  # Intitulé du poste
    department_id = Column(UUID(as_uuid=True), ForeignKey("hr_departments.id"), nullable=True)
    position_id = Column(UUID(as_uuid=True), ForeignKey("hr_positions.id"), nullable=True)

    # Dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # NULL pour CDI
    probation_duration = Column(Integer, nullable=True)  # En jours
    probation_end_date = Column(Date, nullable=True)
    signed_date = Column(Date, nullable=True)

    # Rémunération
    gross_salary = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="EUR")
    pay_frequency = Column(String(20), default="MONTHLY")
    bonus_clause = Column(Text, nullable=True)

    # Temps de travail
    weekly_hours = Column(Numeric(5, 2), default=35.0)
    work_schedule = Column(String(50), default="FULL_TIME")
    remote_work_policy = Column(String(100), nullable=True)

    # Conditions
    notice_period = Column(Integer, nullable=True)  # En jours
    non_compete_clause = Column(Boolean, default=False)
    confidentiality_clause = Column(Boolean, default=True)

    # Statut
    is_current = Column(Boolean, default=True)
    terminated_date = Column(Date, nullable=True)
    termination_reason = Column(String(255), nullable=True)

    # Documents
    document_url = Column(String(500), nullable=True)

    notes = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    employee = relationship("Employee", foreign_keys=[employee_id])

    __table_args__ = (
        UniqueConstraint('tenant_id', 'contract_number', name='unique_contract_number'),
        Index('idx_contracts_tenant', 'tenant_id'),
        Index('idx_contracts_employee', 'tenant_id', 'employee_id'),
    )


# ============================================================================
# MODÈLES CONGÉS
# ============================================================================

class LeaveRequest(Base):
    """Demande de congé."""
    __tablename__ = "hr_leave_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hr_employees.id"), nullable=False)

    type = Column(SQLEnum(LeaveType), nullable=False)
    status = Column(SQLEnum(LeaveStatus), default=LeaveStatus.PENDING)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    start_half_day = Column(Boolean, default=False)  # Débute l'après-midi
    end_half_day = Column(Boolean, default=False)    # Termine le matin
    days_count = Column(Numeric(5, 2), nullable=False)

    reason = Column(Text, nullable=True)
    attachment_url = Column(String(500), nullable=True)

    # Approbation
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Remplacement
    replacement_id = Column(UUID(as_uuid=True), ForeignKey("hr_employees.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    employee = relationship("Employee", foreign_keys=[employee_id])

    __table_args__ = (
        Index('idx_leaves_tenant', 'tenant_id'),
        Index('idx_leaves_employee', 'tenant_id', 'employee_id'),
        Index('idx_leaves_status', 'tenant_id', 'status'),
        Index('idx_leaves_dates', 'tenant_id', 'start_date', 'end_date'),
    )


class LeaveBalance(Base):
    """Solde de congés par type."""
    __tablename__ = "hr_leave_balances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hr_employees.id"), nullable=False)
    year = Column(Integer, nullable=False)
    leave_type = Column(SQLEnum(LeaveType), nullable=False)

    entitled_days = Column(Numeric(5, 2), default=0)
    taken_days = Column(Numeric(5, 2), default=0)
    pending_days = Column(Numeric(5, 2), default=0)
    remaining_days = Column(Numeric(5, 2), default=0)
    carried_over = Column(Numeric(5, 2), default=0)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'employee_id', 'year', 'leave_type', name='unique_leave_balance'),
        Index('idx_leave_balances_tenant', 'tenant_id'),
        Index('idx_leave_balances_employee', 'tenant_id', 'employee_id'),
    )


# ============================================================================
# MODÈLES PAIE
# ============================================================================

class PayrollPeriod(Base):
    """Période de paie."""
    __tablename__ = "hr_payroll_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    name = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    payment_date = Column(Date, nullable=True)

    status = Column(SQLEnum(PayrollStatus), default=PayrollStatus.DRAFT)
    is_closed = Column(Boolean, default=False)
    closed_at = Column(DateTime, nullable=True)
    closed_by = Column(UUID(as_uuid=True), nullable=True)

    total_gross = Column(Numeric(15, 2), default=0)
    total_net = Column(Numeric(15, 2), default=0)
    total_employer_charges = Column(Numeric(15, 2), default=0)
    employee_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'year', 'month', name='unique_payroll_period'),
        Index('idx_payroll_periods_tenant', 'tenant_id'),
    )


class Payslip(Base):
    """Bulletin de paie."""
    __tablename__ = "hr_payslips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hr_employees.id"), nullable=False)
    period_id = Column(UUID(as_uuid=True), ForeignKey("hr_payroll_periods.id"), nullable=False)

    payslip_number = Column(String(50), nullable=False)
    status = Column(SQLEnum(PayrollStatus), default=PayrollStatus.DRAFT)

    # Période
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    payment_date = Column(Date, nullable=True)

    # Heures
    worked_hours = Column(Numeric(6, 2), default=0)
    overtime_hours = Column(Numeric(6, 2), default=0)
    absence_hours = Column(Numeric(6, 2), default=0)

    # Montants
    gross_salary = Column(Numeric(12, 2), nullable=False)
    total_gross = Column(Numeric(12, 2), default=0)  # Brut total (salaire + primes)
    total_deductions = Column(Numeric(12, 2), default=0)
    employee_charges = Column(Numeric(12, 2), default=0)
    employer_charges = Column(Numeric(12, 2), default=0)
    taxable_income = Column(Numeric(12, 2), default=0)
    tax_withheld = Column(Numeric(12, 2), default=0)  # Prélèvement à la source
    net_before_tax = Column(Numeric(12, 2), default=0)
    net_salary = Column(Numeric(12, 2), default=0)

    # Cumuls annuels
    ytd_gross = Column(Numeric(15, 2), default=0)
    ytd_net = Column(Numeric(15, 2), default=0)
    ytd_tax = Column(Numeric(15, 2), default=0)

    # Document
    document_url = Column(String(500), nullable=True)
    sent_at = Column(DateTime, nullable=True)

    validated_by = Column(UUID(as_uuid=True), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    employee = relationship("Employee", foreign_keys=[employee_id])
    period = relationship("PayrollPeriod", foreign_keys=[period_id])

    __table_args__ = (
        UniqueConstraint('tenant_id', 'payslip_number', name='unique_payslip_number'),
        Index('idx_payslips_tenant', 'tenant_id'),
        Index('idx_payslips_employee', 'tenant_id', 'employee_id'),
        Index('idx_payslips_period', 'tenant_id', 'period_id'),
    )


class PayslipLine(Base):
    """Ligne de bulletin de paie."""
    __tablename__ = "hr_payslip_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    payslip_id = Column(UUID(as_uuid=True), ForeignKey("hr_payslips.id"), nullable=False)

    line_number = Column(Integer, nullable=False)
    type = Column(SQLEnum(PayElementType), nullable=False)
    code = Column(String(50), nullable=False)
    label = Column(String(255), nullable=False)

    base = Column(Numeric(12, 2), nullable=True)
    rate = Column(Numeric(8, 4), nullable=True)
    quantity = Column(Numeric(8, 2), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)

    is_deduction = Column(Boolean, default=False)
    is_employer_charge = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_payslip_lines_payslip', 'payslip_id'),
        Index('idx_payslip_lines_tenant', 'tenant_id'),
    )


# ============================================================================
# MODÈLES TEMPS DE TRAVAIL
# ============================================================================

class TimeEntry(Base):
    """Entrée de temps de travail."""
    __tablename__ = "hr_time_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hr_employees.id"), nullable=False)

    date = Column(Date, nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    break_duration = Column(Integer, default=0)  # En minutes
    worked_hours = Column(Numeric(5, 2), nullable=False)
    overtime_hours = Column(Numeric(5, 2), default=0)

    project_id = Column(UUID(as_uuid=True), nullable=True)
    task_description = Column(String(500), nullable=True)

    is_approved = Column(Boolean, default=False)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_time_entries_tenant', 'tenant_id'),
        Index('idx_time_entries_employee', 'tenant_id', 'employee_id'),
        Index('idx_time_entries_date', 'tenant_id', 'date'),
    )


# ============================================================================
# MODÈLES FORMATION & COMPÉTENCES
# ============================================================================

class Skill(Base):
    """Compétence."""
    __tablename__ = "hr_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='unique_skill_code'),
        Index('idx_skills_tenant', 'tenant_id'),
    )


class EmployeeSkill(Base):
    """Compétence d'un employé."""
    __tablename__ = "hr_employee_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hr_employees.id"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("hr_skills.id"), nullable=False)

    level = Column(Integer, default=1)  # 1-5
    acquired_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    certification_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    validated_by = Column(UUID(as_uuid=True), nullable=True)
    validated_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'employee_id', 'skill_id', name='unique_employee_skill'),
        Index('idx_employee_skills_tenant', 'tenant_id'),
        Index('idx_employee_skills_employee', 'tenant_id', 'employee_id'),
    )


class Training(Base):
    """Session de formation."""
    __tablename__ = "hr_trainings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(SQLEnum(TrainingType), nullable=False)
    status = Column(SQLEnum(TrainingStatus), default=TrainingStatus.PLANNED)

    provider = Column(String(255), nullable=True)
    trainer = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    duration_hours = Column(Numeric(6, 2), nullable=True)

    max_participants = Column(Integer, nullable=True)
    cost_per_person = Column(Numeric(12, 2), nullable=True)
    total_cost = Column(Numeric(12, 2), nullable=True)

    skills_acquired = Column(JSONB, default=list)  # Liste des skill_id

    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='unique_training_code'),
        Index('idx_trainings_tenant', 'tenant_id'),
        Index('idx_trainings_dates', 'tenant_id', 'start_date', 'end_date'),
    )


class TrainingParticipant(Base):
    """Participant à une formation."""
    __tablename__ = "hr_training_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    training_id = Column(UUID(as_uuid=True), ForeignKey("hr_trainings.id"), nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hr_employees.id"), nullable=False)

    status = Column(String(50), default="ENROLLED")  # ENROLLED, ATTENDED, CANCELLED, NO_SHOW
    attendance_rate = Column(Numeric(5, 2), nullable=True)
    score = Column(Numeric(5, 2), nullable=True)
    passed = Column(Boolean, nullable=True)
    certificate_url = Column(String(500), nullable=True)
    feedback = Column(Text, nullable=True)

    enrolled_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'training_id', 'employee_id', name='unique_training_participant'),
        Index('idx_training_participants_tenant', 'tenant_id'),
        Index('idx_training_participants_training', 'training_id'),
    )


# ============================================================================
# MODÈLES ÉVALUATIONS
# ============================================================================

class Evaluation(Base):
    """Évaluation de performance."""
    __tablename__ = "hr_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hr_employees.id"), nullable=False)

    type = Column(SQLEnum(EvaluationType), nullable=False)
    status = Column(SQLEnum(EvaluationStatus), default=EvaluationStatus.SCHEDULED)

    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    scheduled_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)

    evaluator_id = Column(UUID(as_uuid=True), ForeignKey("hr_employees.id"), nullable=True)

    # Scores (1-5 ou pourcentage)
    overall_score = Column(Numeric(5, 2), nullable=True)
    objectives_score = Column(Numeric(5, 2), nullable=True)
    skills_score = Column(Numeric(5, 2), nullable=True)
    behavior_score = Column(Numeric(5, 2), nullable=True)

    # Contenu
    objectives_achieved = Column(JSONB, default=list)
    objectives_next = Column(JSONB, default=list)
    strengths = Column(Text, nullable=True)
    improvements = Column(Text, nullable=True)
    employee_comments = Column(Text, nullable=True)
    evaluator_comments = Column(Text, nullable=True)

    # Recommandations
    promotion_recommended = Column(Boolean, default=False)
    salary_increase_recommended = Column(Boolean, default=False)
    training_needs = Column(JSONB, default=list)

    # Signatures
    employee_signed_at = Column(DateTime, nullable=True)
    evaluator_signed_at = Column(DateTime, nullable=True)

    document_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    employee = relationship("Employee", foreign_keys=[employee_id])

    __table_args__ = (
        Index('idx_evaluations_tenant', 'tenant_id'),
        Index('idx_evaluations_employee', 'tenant_id', 'employee_id'),
        Index('idx_evaluations_status', 'tenant_id', 'status'),
    )


# ============================================================================
# MODÈLES DOCUMENTS RH
# ============================================================================

class HRDocument(Base):
    """Document RH."""
    __tablename__ = "hr_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hr_employees.id"), nullable=False)

    type = Column(SQLEnum(DocumentType), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)

    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    is_confidential = Column(Boolean, default=False)

    uploaded_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_hr_documents_tenant', 'tenant_id'),
        Index('idx_hr_documents_employee', 'tenant_id', 'employee_id'),
        Index('idx_hr_documents_type', 'tenant_id', 'type'),
    )
