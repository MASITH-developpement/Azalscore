"""
AZALS MODULE M3 - Service RH
============================

Service métier pour la gestion des ressources humaines.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from uuid import UUID

from .models import (
    Department, Position, Employee, Contract, LeaveRequest, LeaveBalance,
    PayrollPeriod, Payslip, PayslipLine, HRTimeEntry,
    Skill, EmployeeSkill, Training, TrainingParticipant,
    Evaluation, HRDocument,
    ContractType, EmployeeStatus, LeaveType, LeaveStatus,
    PayrollStatus, PayElementType, DocumentType,
    EvaluationType, EvaluationStatus, TrainingType, TrainingStatus
)
from .schemas import (
    DepartmentCreate, DepartmentUpdate, PositionCreate, PositionUpdate,
    EmployeeCreate, EmployeeUpdate, ContractCreate,
    LeaveRequestCreate, PayrollPeriodCreate, PayslipCreate, PayslipLineCreate,
    TimeEntryCreate, SkillCreate, EmployeeSkillCreate,
    TrainingCreate, TrainingParticipantCreate,
    EvaluationCreate, EvaluationUpdate, HRDocumentCreate,
    HRDashboard
)


class HRService:
    """Service pour la gestion RH."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # =========================================================================
    # DÉPARTEMENTS
    # =========================================================================

    def create_department(self, data: DepartmentCreate) -> Department:
        """Créer un département."""
        dept = Department(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            parent_id=data.parent_id,
            manager_id=data.manager_id,
            cost_center=data.cost_center
        )
        self.db.add(dept)
        self.db.commit()
        self.db.refresh(dept)
        return dept

    def get_department(self, dept_id: UUID) -> Optional[Department]:
        """Récupérer un département."""
        return self.db.query(Department).filter(
            Department.id == dept_id,
            Department.tenant_id == self.tenant_id
        ).first()

    def list_departments(self, is_active: bool = True) -> List[Department]:
        """Lister les départements."""
        return self.db.query(Department).filter(
            Department.tenant_id == self.tenant_id,
            Department.is_active == is_active
        ).order_by(Department.name).all()

    def update_department(self, dept_id: UUID, data: DepartmentUpdate) -> Optional[Department]:
        """Mettre à jour un département."""
        dept = self.get_department(dept_id)
        if not dept:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(dept, field, value)
        self.db.commit()
        self.db.refresh(dept)
        return dept

    # =========================================================================
    # POSTES
    # =========================================================================

    def create_position(self, data: PositionCreate) -> Position:
        """Créer un poste."""
        position = Position(
            tenant_id=self.tenant_id,
            code=data.code,
            title=data.title,
            description=data.description,
            department_id=data.department_id,
            category=data.category,
            level=data.level,
            min_salary=data.min_salary,
            max_salary=data.max_salary,
            requirements=data.requirements
        )
        self.db.add(position)
        self.db.commit()
        self.db.refresh(position)
        return position

    def get_position(self, position_id: UUID) -> Optional[Position]:
        """Récupérer un poste."""
        return self.db.query(Position).filter(
            Position.id == position_id,
            Position.tenant_id == self.tenant_id
        ).first()

    def list_positions(
        self,
        department_id: Optional[UUID] = None,
        is_active: bool = True
    ) -> List[Position]:
        """Lister les postes."""
        query = self.db.query(Position).filter(
            Position.tenant_id == self.tenant_id,
            Position.is_active == is_active
        )
        if department_id:
            query = query.filter(Position.department_id == department_id)
        return query.order_by(Position.title).all()

    def update_position(self, position_id: UUID, data: PositionUpdate) -> Optional[Position]:
        """Mettre à jour un poste."""
        position = self.get_position(position_id)
        if not position:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(position, field, value)
        self.db.commit()
        self.db.refresh(position)
        return position

    # =========================================================================
    # EMPLOYÉS
    # =========================================================================

    def create_employee(self, data: EmployeeCreate) -> Employee:
        """Créer un employé."""
        employee = Employee(
            tenant_id=self.tenant_id,
            employee_number=data.employee_number,
            user_id=data.user_id,
            first_name=data.first_name,
            last_name=data.last_name,
            maiden_name=data.maiden_name,
            gender=data.gender,
            birth_date=data.birth_date,
            birth_place=data.birth_place,
            nationality=data.nationality,
            social_security_number=data.social_security_number,
            email=data.email,
            personal_email=data.personal_email,
            phone=data.phone,
            mobile=data.mobile,
            address_line1=data.address_line1,
            address_line2=data.address_line2,
            postal_code=data.postal_code,
            city=data.city,
            country=data.country,
            department_id=data.department_id,
            position_id=data.position_id,
            manager_id=data.manager_id,
            work_location=data.work_location,
            contract_type=data.contract_type,
            hire_date=data.hire_date,
            start_date=data.start_date,
            gross_salary=data.gross_salary,
            currency=data.currency,
            weekly_hours=data.weekly_hours,
            bank_name=data.bank_name,
            iban=data.iban,
            bic=data.bic
        )
        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def get_employee(self, employee_id: UUID) -> Optional[Employee]:
        """Récupérer un employé."""
        return self.db.query(Employee).filter(
            Employee.id == employee_id,
            Employee.tenant_id == self.tenant_id
        ).first()

    def get_employee_by_number(self, employee_number: str) -> Optional[Employee]:
        """Récupérer un employé par numéro."""
        return self.db.query(Employee).filter(
            Employee.employee_number == employee_number,
            Employee.tenant_id == self.tenant_id
        ).first()

    def list_employees(
        self,
        department_id: Optional[UUID] = None,
        status: Optional[EmployeeStatus] = None,
        manager_id: Optional[UUID] = None,
        search: Optional[str] = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Employee], int]:
        """Lister les employés."""
        query = self.db.query(Employee).filter(
            Employee.tenant_id == self.tenant_id,
            Employee.is_active == is_active
        )

        if department_id:
            query = query.filter(Employee.department_id == department_id)
        if status:
            query = query.filter(Employee.status == status)
        if manager_id:
            query = query.filter(Employee.manager_id == manager_id)
        if search:
            query = query.filter(
                or_(
                    Employee.first_name.ilike(f"%{search}%"),
                    Employee.last_name.ilike(f"%{search}%"),
                    Employee.employee_number.ilike(f"%{search}%"),
                    Employee.email.ilike(f"%{search}%")
                )
            )

        total = query.count()
        items = query.order_by(Employee.last_name, Employee.first_name).offset(skip).limit(limit).all()
        return items, total

    def update_employee(self, employee_id: UUID, data: EmployeeUpdate) -> Optional[Employee]:
        """Mettre à jour un employé."""
        employee = self.get_employee(employee_id)
        if not employee:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(employee, field, value)
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def terminate_employee(
        self,
        employee_id: UUID,
        end_date: date,
        reason: Optional[str] = None
    ) -> Optional[Employee]:
        """Terminer le contrat d'un employé."""
        employee = self.get_employee(employee_id)
        if not employee:
            return None
        employee.status = EmployeeStatus.TERMINATED
        employee.end_date = end_date
        # Mettre à jour le contrat actuel
        current_contract = self.db.query(Contract).filter(
            Contract.employee_id == employee_id,
            Contract.is_current == True
        ).first()
        if current_contract:
            current_contract.is_current = False
            current_contract.terminated_date = end_date
            current_contract.termination_reason = reason
        self.db.commit()
        self.db.refresh(employee)
        return employee

    # =========================================================================
    # CONTRATS
    # =========================================================================

    def create_contract(self, data: ContractCreate, user_id: UUID) -> Contract:
        """Créer un contrat."""
        # Désactiver les anciens contrats
        self.db.query(Contract).filter(
            Contract.employee_id == data.employee_id,
            Contract.is_current == True
        ).update({"is_current": False})

        contract = Contract(
            tenant_id=self.tenant_id,
            employee_id=data.employee_id,
            contract_number=data.contract_number,
            type=data.type,
            title=data.title,
            department_id=data.department_id,
            position_id=data.position_id,
            start_date=data.start_date,
            end_date=data.end_date,
            probation_duration=data.probation_duration,
            gross_salary=data.gross_salary,
            currency=data.currency,
            pay_frequency=data.pay_frequency,
            weekly_hours=data.weekly_hours,
            work_schedule=data.work_schedule,
            bonus_clause=data.bonus_clause,
            notice_period=data.notice_period,
            non_compete_clause=data.non_compete_clause,
            confidentiality_clause=data.confidentiality_clause,
            created_by=user_id
        )

        # Calculer la fin de période d'essai
        if data.probation_duration:
            contract.probation_end_date = data.start_date + timedelta(days=data.probation_duration)

        self.db.add(contract)

        # Mettre à jour l'employé
        employee = self.get_employee(data.employee_id)
        if employee:
            employee.contract_type = data.type
            employee.start_date = data.start_date
            employee.end_date = data.end_date
            employee.gross_salary = data.gross_salary
            employee.weekly_hours = data.weekly_hours
            employee.probation_end_date = contract.probation_end_date
            if data.department_id:
                employee.department_id = data.department_id
            if data.position_id:
                employee.position_id = data.position_id

        self.db.commit()
        self.db.refresh(contract)
        return contract

    def get_contract(self, contract_id: UUID) -> Optional[Contract]:
        """Récupérer un contrat."""
        return self.db.query(Contract).filter(
            Contract.id == contract_id,
            Contract.tenant_id == self.tenant_id
        ).first()

    def list_employee_contracts(self, employee_id: UUID) -> List[Contract]:
        """Lister les contrats d'un employé."""
        return self.db.query(Contract).filter(
            Contract.employee_id == employee_id,
            Contract.tenant_id == self.tenant_id
        ).order_by(Contract.start_date.desc()).all()

    # =========================================================================
    # CONGÉS
    # =========================================================================

    def create_leave_request(
        self,
        employee_id: UUID,
        data: LeaveRequestCreate
    ) -> LeaveRequest:
        """Créer une demande de congé."""
        # Calculer le nombre de jours
        days_count = self._calculate_leave_days(
            data.start_date,
            data.end_date,
            data.start_half_day,
            data.end_half_day
        )

        leave = LeaveRequest(
            tenant_id=self.tenant_id,
            employee_id=employee_id,
            type=data.type,
            start_date=data.start_date,
            end_date=data.end_date,
            start_half_day=data.start_half_day,
            end_half_day=data.end_half_day,
            days_count=days_count,
            reason=data.reason,
            replacement_id=data.replacement_id
        )
        self.db.add(leave)

        # Mettre à jour le solde pending
        self._update_leave_balance(employee_id, data.type, pending_delta=days_count)

        self.db.commit()
        self.db.refresh(leave)
        return leave

    def _calculate_leave_days(
        self,
        start_date: date,
        end_date: date,
        start_half_day: bool,
        end_half_day: bool
    ) -> Decimal:
        """Calculer le nombre de jours de congé (hors week-ends)."""
        days = Decimal("0")
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # Lundi à Vendredi
                if current == start_date and start_half_day:
                    days += Decimal("0.5")
                elif current == end_date and end_half_day:
                    days += Decimal("0.5")
                else:
                    days += Decimal("1")
            current += timedelta(days=1)
        return days

    def _update_leave_balance(
        self,
        employee_id: UUID,
        leave_type: LeaveType,
        pending_delta: Decimal = Decimal("0"),
        taken_delta: Decimal = Decimal("0")
    ):
        """Mettre à jour le solde de congés."""
        year = date.today().year
        balance = self.db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.year == year,
            LeaveBalance.leave_type == leave_type,
            LeaveBalance.tenant_id == self.tenant_id
        ).first()

        if not balance:
            balance = LeaveBalance(
                tenant_id=self.tenant_id,
                employee_id=employee_id,
                year=year,
                leave_type=leave_type,
                entitled_days=Decimal("25") if leave_type == LeaveType.PAID else Decimal("0")
            )
            self.db.add(balance)

        balance.pending_days += pending_delta
        balance.taken_days += taken_delta
        balance.remaining_days = balance.entitled_days + balance.carried_over - balance.taken_days - balance.pending_days

    def approve_leave_request(
        self,
        leave_id: UUID,
        approver_id: UUID
    ) -> Optional[LeaveRequest]:
        """Approuver une demande de congé."""
        leave = self.db.query(LeaveRequest).filter(
            LeaveRequest.id == leave_id,
            LeaveRequest.tenant_id == self.tenant_id
        ).first()

        if not leave or leave.status != LeaveStatus.PENDING:
            return None

        leave.status = LeaveStatus.APPROVED
        leave.approved_by = approver_id
        leave.approved_at = datetime.utcnow()

        # Transférer de pending à taken
        self._update_leave_balance(
            leave.employee_id,
            leave.type,
            pending_delta=-leave.days_count,
            taken_delta=leave.days_count
        )

        self.db.commit()
        self.db.refresh(leave)
        return leave

    def reject_leave_request(
        self,
        leave_id: UUID,
        approver_id: UUID,
        reason: str
    ) -> Optional[LeaveRequest]:
        """Rejeter une demande de congé."""
        leave = self.db.query(LeaveRequest).filter(
            LeaveRequest.id == leave_id,
            LeaveRequest.tenant_id == self.tenant_id
        ).first()

        if not leave or leave.status != LeaveStatus.PENDING:
            return None

        leave.status = LeaveStatus.REJECTED
        leave.approved_by = approver_id
        leave.approved_at = datetime.utcnow()
        leave.rejection_reason = reason

        # Annuler pending
        self._update_leave_balance(
            leave.employee_id,
            leave.type,
            pending_delta=-leave.days_count
        )

        self.db.commit()
        self.db.refresh(leave)
        return leave

    def get_employee_leave_balance(
        self,
        employee_id: UUID,
        year: Optional[int] = None
    ) -> List[LeaveBalance]:
        """Récupérer les soldes de congés d'un employé."""
        if year is None:
            year = date.today().year
        return self.db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.year == year,
            LeaveBalance.tenant_id == self.tenant_id
        ).all()

    def list_leave_requests(
        self,
        employee_id: Optional[UUID] = None,
        status: Optional[LeaveStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[LeaveRequest], int]:
        """Lister les demandes de congé."""
        query = self.db.query(LeaveRequest).filter(
            LeaveRequest.tenant_id == self.tenant_id
        )

        if employee_id:
            query = query.filter(LeaveRequest.employee_id == employee_id)
        if status:
            query = query.filter(LeaveRequest.status == status)
        if start_date:
            query = query.filter(LeaveRequest.start_date >= start_date)
        if end_date:
            query = query.filter(LeaveRequest.end_date <= end_date)

        total = query.count()
        items = query.order_by(LeaveRequest.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    # =========================================================================
    # PAIE
    # =========================================================================

    def create_payroll_period(self, data: PayrollPeriodCreate) -> PayrollPeriod:
        """Créer une période de paie."""
        period = PayrollPeriod(
            tenant_id=self.tenant_id,
            name=data.name,
            year=data.year,
            month=data.month,
            start_date=data.start_date,
            end_date=data.end_date,
            payment_date=data.payment_date
        )
        self.db.add(period)
        self.db.commit()
        self.db.refresh(period)
        return period

    def get_payroll_period(self, period_id: UUID) -> Optional[PayrollPeriod]:
        """Récupérer une période de paie."""
        return self.db.query(PayrollPeriod).filter(
            PayrollPeriod.id == period_id,
            PayrollPeriod.tenant_id == self.tenant_id
        ).first()

    def list_payroll_periods(self, year: Optional[int] = None) -> List[PayrollPeriod]:
        """Lister les périodes de paie."""
        query = self.db.query(PayrollPeriod).filter(
            PayrollPeriod.tenant_id == self.tenant_id
        )
        if year:
            query = query.filter(PayrollPeriod.year == year)
        return query.order_by(PayrollPeriod.year.desc(), PayrollPeriod.month.desc()).all()

    def create_payslip(self, data: PayslipCreate, user_id: UUID) -> Payslip:
        """Créer un bulletin de paie."""
        # Générer le numéro
        period = self.get_payroll_period(data.period_id)
        if not period:
            raise ValueError("Period not found")

        count = self.db.query(Payslip).filter(
            Payslip.period_id == data.period_id
        ).count()

        payslip_number = f"PAY-{period.year}{period.month:02d}-{count + 1:04d}"

        payslip = Payslip(
            tenant_id=self.tenant_id,
            employee_id=data.employee_id,
            period_id=data.period_id,
            payslip_number=payslip_number,
            start_date=data.start_date,
            end_date=data.end_date,
            payment_date=data.payment_date,
            worked_hours=data.worked_hours,
            overtime_hours=data.overtime_hours,
            absence_hours=data.absence_hours,
            gross_salary=data.gross_salary
        )
        self.db.add(payslip)
        self.db.flush()

        # Créer les lignes
        total_gross = data.gross_salary
        total_deductions = Decimal("0")
        employee_charges = Decimal("0")
        employer_charges = Decimal("0")

        for i, line_data in enumerate(data.lines, 1):
            line = PayslipLine(
                tenant_id=self.tenant_id,
                payslip_id=payslip.id,
                line_number=i,
                type=line_data.type,
                code=line_data.code,
                label=line_data.label,
                base=line_data.base,
                rate=line_data.rate,
                quantity=line_data.quantity,
                amount=line_data.amount,
                is_deduction=line_data.is_deduction,
                is_employer_charge=line_data.is_employer_charge
            )
            self.db.add(line)

            if line_data.is_employer_charge:
                employer_charges += line_data.amount
            elif line_data.is_deduction:
                total_deductions += line_data.amount
                employee_charges += line_data.amount
            else:
                total_gross += line_data.amount

        payslip.total_gross = total_gross
        payslip.total_deductions = total_deductions
        payslip.employee_charges = employee_charges
        payslip.employer_charges = employer_charges
        payslip.net_before_tax = total_gross - employee_charges
        payslip.net_salary = payslip.net_before_tax - payslip.tax_withheld

        self.db.commit()
        self.db.refresh(payslip)
        return payslip

    def validate_payslip(self, payslip_id: UUID, user_id: UUID) -> Optional[Payslip]:
        """Valider un bulletin de paie."""
        payslip = self.db.query(Payslip).filter(
            Payslip.id == payslip_id,
            Payslip.tenant_id == self.tenant_id
        ).first()

        if not payslip or payslip.status not in [PayrollStatus.DRAFT, PayrollStatus.CALCULATED]:
            return None

        payslip.status = PayrollStatus.VALIDATED
        payslip.validated_by = user_id
        payslip.validated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(payslip)
        return payslip

    def get_employee_payslips(
        self,
        employee_id: UUID,
        year: Optional[int] = None
    ) -> List[Payslip]:
        """Récupérer les bulletins d'un employé."""
        query = self.db.query(Payslip).filter(
            Payslip.employee_id == employee_id,
            Payslip.tenant_id == self.tenant_id
        )
        if year:
            query = query.join(PayrollPeriod).filter(PayrollPeriod.year == year)
        return query.order_by(Payslip.start_date.desc()).all()

    # =========================================================================
    # TEMPS DE TRAVAIL
    # =========================================================================

    def create_time_entry(
        self,
        employee_id: UUID,
        data: TimeEntryCreate
    ) -> HRTimeEntry:
        """Créer une entrée de temps."""
        entry = HRTimeEntry(
            tenant_id=self.tenant_id,
            employee_id=employee_id,
            date=data.date,
            start_time=data.start_time,
            end_time=data.end_time,
            break_duration=data.break_duration,
            worked_hours=data.worked_hours,
            overtime_hours=data.overtime_hours,
            project_id=data.project_id,
            task_description=data.task_description
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_time_entries(
        self,
        employee_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[HRTimeEntry]:
        """Lister les entrées de temps."""
        query = self.db.query(HRTimeEntry).filter(
            HRTimeEntry.tenant_id == self.tenant_id
        )
        if employee_id:
            query = query.filter(HRTimeEntry.employee_id == employee_id)
        if start_date:
            query = query.filter(HRTimeEntry.date >= start_date)
        if end_date:
            query = query.filter(HRTimeEntry.date <= end_date)
        return query.order_by(HRTimeEntry.date.desc()).all()

    # =========================================================================
    # COMPÉTENCES
    # =========================================================================

    def create_skill(self, data: SkillCreate) -> Skill:
        """Créer une compétence."""
        skill = Skill(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            category=data.category,
            description=data.description
        )
        self.db.add(skill)
        self.db.commit()
        self.db.refresh(skill)
        return skill

    def list_skills(self, category: Optional[str] = None) -> List[Skill]:
        """Lister les compétences."""
        query = self.db.query(Skill).filter(
            Skill.tenant_id == self.tenant_id,
            Skill.is_active == True
        )
        if category:
            query = query.filter(Skill.category == category)
        return query.order_by(Skill.name).all()

    def add_employee_skill(
        self,
        employee_id: UUID,
        data: EmployeeSkillCreate
    ) -> EmployeeSkill:
        """Ajouter une compétence à un employé."""
        emp_skill = EmployeeSkill(
            tenant_id=self.tenant_id,
            employee_id=employee_id,
            skill_id=data.skill_id,
            level=data.level,
            acquired_date=data.acquired_date,
            expiry_date=data.expiry_date,
            certification_url=data.certification_url,
            notes=data.notes
        )
        self.db.add(emp_skill)
        self.db.commit()
        self.db.refresh(emp_skill)
        return emp_skill

    def get_employee_skills(self, employee_id: UUID) -> List[EmployeeSkill]:
        """Récupérer les compétences d'un employé."""
        return self.db.query(EmployeeSkill).filter(
            EmployeeSkill.employee_id == employee_id,
            EmployeeSkill.tenant_id == self.tenant_id
        ).all()

    # =========================================================================
    # FORMATIONS
    # =========================================================================

    def create_training(self, data: TrainingCreate, user_id: UUID) -> Training:
        """Créer une formation."""
        training = Training(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            type=data.type,
            provider=data.provider,
            trainer=data.trainer,
            location=data.location,
            start_date=data.start_date,
            end_date=data.end_date,
            duration_hours=data.duration_hours,
            max_participants=data.max_participants,
            cost_per_person=data.cost_per_person,
            skills_acquired=[str(s) for s in data.skills_acquired],
            created_by=user_id
        )
        self.db.add(training)
        self.db.commit()
        self.db.refresh(training)
        return training

    def get_training(self, training_id: UUID) -> Optional[Training]:
        """Récupérer une formation."""
        return self.db.query(Training).filter(
            Training.id == training_id,
            Training.tenant_id == self.tenant_id
        ).first()

    def list_trainings(
        self,
        status: Optional[TrainingStatus] = None,
        training_type: Optional[TrainingType] = None
    ) -> List[Training]:
        """Lister les formations."""
        query = self.db.query(Training).filter(
            Training.tenant_id == self.tenant_id
        )
        if status:
            query = query.filter(Training.status == status)
        if training_type:
            query = query.filter(Training.type == training_type)
        return query.order_by(Training.start_date.desc()).all()

    def enroll_in_training(
        self,
        training_id: UUID,
        employee_id: UUID
    ) -> TrainingParticipant:
        """Inscrire un employé à une formation."""
        participant = TrainingParticipant(
            tenant_id=self.tenant_id,
            training_id=training_id,
            employee_id=employee_id
        )
        self.db.add(participant)
        self.db.commit()
        self.db.refresh(participant)
        return participant

    # =========================================================================
    # ÉVALUATIONS
    # =========================================================================

    def create_evaluation(self, data: EvaluationCreate) -> Evaluation:
        """Créer une évaluation."""
        evaluation = Evaluation(
            tenant_id=self.tenant_id,
            employee_id=data.employee_id,
            type=data.type,
            period_start=data.period_start,
            period_end=data.period_end,
            scheduled_date=data.scheduled_date,
            evaluator_id=data.evaluator_id
        )
        self.db.add(evaluation)
        self.db.commit()
        self.db.refresh(evaluation)
        return evaluation

    def get_evaluation(self, evaluation_id: UUID) -> Optional[Evaluation]:
        """Récupérer une évaluation."""
        return self.db.query(Evaluation).filter(
            Evaluation.id == evaluation_id,
            Evaluation.tenant_id == self.tenant_id
        ).first()

    def update_evaluation(
        self,
        evaluation_id: UUID,
        data: EvaluationUpdate
    ) -> Optional[Evaluation]:
        """Mettre à jour une évaluation."""
        evaluation = self.get_evaluation(evaluation_id)
        if not evaluation:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(evaluation, field, value)
        self.db.commit()
        self.db.refresh(evaluation)
        return evaluation

    def list_evaluations(
        self,
        employee_id: Optional[UUID] = None,
        status: Optional[EvaluationStatus] = None,
        evaluator_id: Optional[UUID] = None
    ) -> List[Evaluation]:
        """Lister les évaluations."""
        query = self.db.query(Evaluation).filter(
            Evaluation.tenant_id == self.tenant_id
        )
        if employee_id:
            query = query.filter(Evaluation.employee_id == employee_id)
        if status:
            query = query.filter(Evaluation.status == status)
        if evaluator_id:
            query = query.filter(Evaluation.evaluator_id == evaluator_id)
        return query.order_by(Evaluation.scheduled_date.desc()).all()

    # =========================================================================
    # DOCUMENTS
    # =========================================================================

    def create_document(self, data: HRDocumentCreate, user_id: UUID) -> HRDocument:
        """Créer un document RH."""
        doc = HRDocument(
            tenant_id=self.tenant_id,
            employee_id=data.employee_id,
            type=data.type,
            name=data.name,
            description=data.description,
            file_url=data.file_url,
            file_size=data.file_size,
            mime_type=data.mime_type,
            issue_date=data.issue_date,
            expiry_date=data.expiry_date,
            is_confidential=data.is_confidential,
            uploaded_by=user_id
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get_employee_documents(
        self,
        employee_id: UUID,
        doc_type: Optional[DocumentType] = None
    ) -> List[HRDocument]:
        """Récupérer les documents d'un employé."""
        query = self.db.query(HRDocument).filter(
            HRDocument.employee_id == employee_id,
            HRDocument.tenant_id == self.tenant_id
        )
        if doc_type:
            query = query.filter(HRDocument.type == doc_type)
        return query.order_by(HRDocument.created_at.desc()).all()

    # =========================================================================
    # DASHBOARD
    # =========================================================================

    def get_dashboard(self) -> HRDashboard:
        """Générer le dashboard RH."""
        today = date.today()
        first_of_month = today.replace(day=1)

        # Effectifs
        total = self.db.query(Employee).filter(
            Employee.tenant_id == self.tenant_id,
            Employee.is_active == True
        ).count()

        active = self.db.query(Employee).filter(
            Employee.tenant_id == self.tenant_id,
            Employee.status == EmployeeStatus.ACTIVE
        ).count()

        on_leave = self.db.query(Employee).filter(
            Employee.tenant_id == self.tenant_id,
            Employee.status == EmployeeStatus.ON_LEAVE
        ).count()

        new_hires = self.db.query(Employee).filter(
            Employee.tenant_id == self.tenant_id,
            Employee.hire_date >= first_of_month
        ).count()

        departures = self.db.query(Employee).filter(
            Employee.tenant_id == self.tenant_id,
            Employee.end_date >= first_of_month,
            Employee.status == EmployeeStatus.TERMINATED
        ).count()

        # Contrats
        cdi = self.db.query(Employee).filter(
            Employee.tenant_id == self.tenant_id,
            Employee.contract_type == ContractType.CDI,
            Employee.is_active == True
        ).count()

        cdd = self.db.query(Employee).filter(
            Employee.tenant_id == self.tenant_id,
            Employee.contract_type == ContractType.CDD,
            Employee.is_active == True
        ).count()

        probation_soon = self.db.query(Employee).filter(
            Employee.tenant_id == self.tenant_id,
            Employee.probation_end_date.between(today, today + timedelta(days=30))
        ).count()

        contracts_ending = self.db.query(Employee).filter(
            Employee.tenant_id == self.tenant_id,
            Employee.end_date.between(today, today + timedelta(days=30))
        ).count()

        # Congés
        pending_leaves = self.db.query(LeaveRequest).filter(
            LeaveRequest.tenant_id == self.tenant_id,
            LeaveRequest.status == LeaveStatus.PENDING
        ).count()

        on_leave_today = self.db.query(LeaveRequest).filter(
            LeaveRequest.tenant_id == self.tenant_id,
            LeaveRequest.status == LeaveStatus.APPROVED,
            LeaveRequest.start_date <= today,
            LeaveRequest.end_date >= today
        ).count()

        # Évaluations
        pending_evals = self.db.query(Evaluation).filter(
            Evaluation.tenant_id == self.tenant_id,
            Evaluation.status.in_([EvaluationStatus.SCHEDULED, EvaluationStatus.IN_PROGRESS])
        ).count()

        overdue_evals = self.db.query(Evaluation).filter(
            Evaluation.tenant_id == self.tenant_id,
            Evaluation.status == EvaluationStatus.SCHEDULED,
            Evaluation.scheduled_date < today
        ).count()

        # Formations en cours
        trainings = self.db.query(Training).filter(
            Training.tenant_id == self.tenant_id,
            Training.status == TrainingStatus.IN_PROGRESS
        ).count()

        # Salaire moyen
        avg_salary = self.db.query(func.avg(Employee.gross_salary)).filter(
            Employee.tenant_id == self.tenant_id,
            Employee.is_active == True,
            Employee.gross_salary.isnot(None)
        ).scalar() or Decimal("0")

        # Répartition par département
        dept_counts = self.db.query(
            Department.name,
            func.count(Employee.id)
        ).join(Employee, Employee.department_id == Department.id).filter(
            Employee.tenant_id == self.tenant_id,
            Employee.is_active == True
        ).group_by(Department.name).all()

        by_department = {d[0]: d[1] for d in dept_counts}

        # Répartition par type de contrat
        contract_counts = self.db.query(
            Employee.contract_type,
            func.count(Employee.id)
        ).filter(
            Employee.tenant_id == self.tenant_id,
            Employee.is_active == True,
            Employee.contract_type.isnot(None)
        ).group_by(Employee.contract_type).all()

        by_contract = {str(c[0].value) if c[0] else "OTHER": c[1] for c in contract_counts}

        return HRDashboard(
            total_employees=total,
            active_employees=active,
            on_leave_employees=on_leave,
            new_hires_this_month=new_hires,
            departures_this_month=departures,
            cdi_count=cdi,
            cdd_count=cdd,
            probation_ending_soon=probation_soon,
            contracts_ending_soon=contracts_ending,
            pending_leave_requests=pending_leaves,
            employees_on_leave_today=on_leave_today,
            average_salary=avg_salary,
            trainings_in_progress=trainings,
            pending_evaluations=pending_evals,
            overdue_evaluations=overdue_evals,
            by_department=by_department,
            by_contract_type=by_contract
        )


def get_hr_service(db: Session, tenant_id: str) -> HRService:
    """Factory pour le service RH."""
    return HRService(db, tenant_id)
