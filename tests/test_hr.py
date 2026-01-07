"""
AZALS MODULE M3 - Tests RH (Ressources Humaines)
=================================================

Tests unitaires pour la gestion des ressources humaines.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

# Import des modèles
from app.modules.hr.models import (
    Department, Position, Employee, Contract, LeaveRequest, LeaveBalance,
    PayrollPeriod, Payslip, PayslipLine, HRTimeEntry as TimeEntry, Skill, EmployeeSkill,
    Training, TrainingParticipant, Evaluation, HRDocument,
    ContractType, EmployeeStatus, LeaveType, LeaveStatus, PayrollStatus,
    PayElementType, DocumentType, EvaluationType, EvaluationStatus,
    TrainingType, TrainingStatus
)

# Import des schémas
from app.modules.hr.schemas import (
    DepartmentCreate, DepartmentUpdate, PositionCreate,
    EmployeeCreate, EmployeeUpdate, ContractCreate,
    LeaveRequestCreate, LeaveBalanceUpdate,
    PayrollPeriodCreate, PayslipCreate, PayslipLineCreate,
    TimeEntryCreate, SkillCreate, EmployeeSkillCreate,
    TrainingCreate, TrainingParticipantCreate,
    EvaluationCreate, HRDocumentCreate,
    HRDashboard
)

# Import du service
from app.modules.hr.service import HRService, get_hr_service


# =============================================================================
# TESTS DES ENUMS
# =============================================================================

class TestEnums:
    """Tests des énumérations."""

    def test_contract_type_values(self):
        """Tester les types de contrats."""
        assert ContractType.CDI.value == "CDI"
        assert ContractType.CDD.value == "CDD"
        assert ContractType.INTERIM.value == "INTERIM"
        assert ContractType.STAGE.value == "STAGE"
        assert ContractType.APPRENTISSAGE.value == "APPRENTISSAGE"
        assert ContractType.FREELANCE.value == "FREELANCE"
        assert len(ContractType) == 6

    def test_employee_status_values(self):
        """Tester les statuts d'employé."""
        assert EmployeeStatus.ACTIVE.value == "ACTIVE"
        assert EmployeeStatus.ON_LEAVE.value == "ON_LEAVE"
        assert EmployeeStatus.SUSPENDED.value == "SUSPENDED"
        assert EmployeeStatus.TERMINATED.value == "TERMINATED"
        assert EmployeeStatus.RETIRED.value == "RETIRED"
        assert len(EmployeeStatus) == 5

    def test_leave_type_values(self):
        """Tester les types de congés."""
        assert LeaveType.PAID.value == "PAID"
        assert LeaveType.UNPAID.value == "UNPAID"
        assert LeaveType.SICK.value == "SICK"
        assert LeaveType.MATERNITY.value == "MATERNITY"
        assert LeaveType.PATERNITY.value == "PATERNITY"
        assert LeaveType.RTT.value == "RTT"
        assert len(LeaveType) == 10

    def test_leave_status_values(self):
        """Tester les statuts de congé."""
        assert LeaveStatus.PENDING.value == "PENDING"
        assert LeaveStatus.APPROVED.value == "APPROVED"
        assert LeaveStatus.REJECTED.value == "REJECTED"
        assert LeaveStatus.CANCELLED.value == "CANCELLED"
        assert len(LeaveStatus) == 4

    def test_payroll_status_values(self):
        """Tester les statuts de paie."""
        assert PayrollStatus.DRAFT.value == "DRAFT"
        assert PayrollStatus.CALCULATED.value == "CALCULATED"
        assert PayrollStatus.VALIDATED.value == "VALIDATED"
        assert PayrollStatus.PAID.value == "PAID"
        assert PayrollStatus.CANCELLED.value == "CANCELLED"
        assert len(PayrollStatus) == 5

    def test_pay_element_type_values(self):
        """Tester les types d'éléments de paie."""
        assert PayElementType.GROSS_SALARY.value == "GROSS_SALARY"
        assert PayElementType.BONUS.value == "BONUS"
        assert PayElementType.DEDUCTION.value == "DEDUCTION"
        assert PayElementType.TAX.value == "TAX"
        assert len(PayElementType) == 11

    def test_evaluation_type_values(self):
        """Tester les types d'évaluation."""
        assert EvaluationType.ANNUAL.value == "ANNUAL"
        assert EvaluationType.PROBATION.value == "PROBATION"
        assert EvaluationType.PROJECT.value == "PROJECT"
        assert len(EvaluationType) == 5

    def test_training_type_values(self):
        """Tester les types de formation."""
        assert TrainingType.INTERNAL.value == "INTERNAL"
        assert TrainingType.EXTERNAL.value == "EXTERNAL"
        assert TrainingType.ONLINE.value == "ONLINE"
        assert TrainingType.CERTIFICATION.value == "CERTIFICATION"
        assert len(TrainingType) == 5


# =============================================================================
# TESTS DES MODÈLES
# =============================================================================

class TestModels:
    """Tests des modèles SQLAlchemy."""

    def test_department_model(self):
        """Tester le modèle Department."""
        department = Department(
            tenant_id="test-tenant",
            code="IT",
            name="Informatique"
        )
        assert department.code == "IT"
        assert department.name == "Informatique"
        assert department.is_active == True

    def test_position_model(self):
        """Tester le modèle Position."""
        position = Position(
            tenant_id="test-tenant",
            code="DEV",
            title="Développeur",
            level=2
        )
        assert position.code == "DEV"
        assert position.title == "Développeur"
        assert position.level == 2

    def test_employee_model(self):
        """Tester le modèle Employee."""
        employee = Employee(
            tenant_id="test-tenant",
            employee_number="EMP001",
            first_name="Jean",
            last_name="Dupont",
            status=EmployeeStatus.ACTIVE
        )
        assert employee.employee_number == "EMP001"
        assert employee.first_name == "Jean"
        assert employee.status == EmployeeStatus.ACTIVE
        assert employee.annual_leave_balance == Decimal("0")

    def test_contract_model(self):
        """Tester le modèle Contract."""
        contract = Contract(
            tenant_id="test-tenant",
            employee_id=uuid4(),
            contract_number="CTR-2026-001",
            type=ContractType.CDI,
            start_date=date.today(),
            gross_salary=Decimal("3500")
        )
        assert contract.type == ContractType.CDI
        assert contract.gross_salary == Decimal("3500")
        assert contract.is_current == True

    def test_leave_request_model(self):
        """Tester le modèle LeaveRequest."""
        leave = LeaveRequest(
            tenant_id="test-tenant",
            employee_id=uuid4(),
            type=LeaveType.PAID,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=5),
            days_count=Decimal("5")
        )
        assert leave.type == LeaveType.PAID
        assert leave.status == LeaveStatus.PENDING
        assert leave.days_count == Decimal("5")

    def test_payslip_model(self):
        """Tester le modèle Payslip."""
        payslip = Payslip(
            tenant_id="test-tenant",
            employee_id=uuid4(),
            period_id=uuid4(),
            payslip_number="PAY-2026-01-001",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            gross_salary=Decimal("3500")
        )
        assert payslip.payslip_number == "PAY-2026-01-001"
        assert payslip.status == PayrollStatus.DRAFT
        assert payslip.net_salary == Decimal("0")

    def test_training_model(self):
        """Tester le modèle Training."""
        training = Training(
            tenant_id="test-tenant",
            code="FORM001",
            name="Formation Python",
            type=TrainingType.INTERNAL,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2)
        )
        assert training.code == "FORM001"
        assert training.type == TrainingType.INTERNAL
        assert training.status == TrainingStatus.PLANNED

    def test_evaluation_model(self):
        """Tester le modèle Evaluation."""
        evaluation = Evaluation(
            tenant_id="test-tenant",
            employee_id=uuid4(),
            type=EvaluationType.ANNUAL,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31)
        )
        assert evaluation.type == EvaluationType.ANNUAL
        assert evaluation.status == EvaluationStatus.SCHEDULED


# =============================================================================
# TESTS DES SCHÉMAS
# =============================================================================

class TestSchemas:
    """Tests des schémas Pydantic."""

    def test_employee_create_schema(self):
        """Tester le schéma EmployeeCreate."""
        data = EmployeeCreate(
            employee_number="EMP001",
            first_name="Marie",
            last_name="Martin",
            email="marie.martin@example.com",
            contract_type=ContractType.CDI
        )
        assert data.employee_number == "EMP001"
        assert data.first_name == "Marie"

    def test_contract_create_schema(self):
        """Tester le schéma ContractCreate."""
        data = ContractCreate(
            employee_id=uuid4(),
            contract_number="CTR-2026-001",
            type=ContractType.CDD,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            gross_salary=Decimal("3000"),
            weekly_hours=Decimal("35")
        )
        assert data.type == ContractType.CDD
        assert data.weekly_hours == Decimal("35")

    def test_leave_request_create_schema(self):
        """Tester le schéma LeaveRequestCreate."""
        data = LeaveRequestCreate(
            employee_id=uuid4(),
            type=LeaveType.PAID,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=10),
            reason="Vacances d'été"
        )
        assert data.type == LeaveType.PAID
        assert data.reason == "Vacances d'été"

    def test_training_create_schema(self):
        """Tester le schéma TrainingCreate."""
        data = TrainingCreate(
            code="FORM002",
            name="Formation Sécurité",
            type=TrainingType.EXTERNAL,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),
            max_participants=20,
            cost_per_person=Decimal("500")
        )
        assert data.code == "FORM002"
        assert data.max_participants == 20


# =============================================================================
# TESTS DU SERVICE - EMPLOYÉS
# =============================================================================

class TestHRServiceEmployees:
    """Tests du service HR - Employés."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return HRService(mock_db, "test-tenant")

    def test_create_employee(self, service, mock_db):
        """Tester la création d'un employé."""
        data = EmployeeCreate(
            employee_number="EMP001",
            first_name="Jean",
            last_name="Dupont",
            email="jean.dupont@example.com"
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_employee(data, uuid4())

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result.employee_number == "EMP001"
        assert result.tenant_id == "test-tenant"

    def test_get_employee(self, service, mock_db):
        """Tester la récupération d'un employé."""
        mock_employee = Employee(
            id=uuid4(),
            tenant_id="test-tenant",
            employee_number="EMP001",
            first_name="Jean",
            last_name="Dupont"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_employee

        result = service.get_employee(mock_employee.id)

        assert result.employee_number == "EMP001"

    def test_list_employees(self, service, mock_db):
        """Tester le listage des employés."""
        mock_employees = [
            Employee(id=uuid4(), tenant_id="test-tenant", employee_number="EMP001",
                     first_name="Jean", last_name="Dupont"),
            Employee(id=uuid4(), tenant_id="test-tenant", employee_number="EMP002",
                     first_name="Marie", last_name="Martin")
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_employees
        mock_db.query.return_value = mock_query

        items, total = service.list_employees()

        assert total == 2
        assert len(items) == 2


# =============================================================================
# TESTS DU SERVICE - CONGÉS
# =============================================================================

class TestHRServiceLeaves:
    """Tests du service HR - Congés."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return HRService(mock_db, "test-tenant")

    def test_create_leave_request(self, service, mock_db):
        """Tester la création d'une demande de congé."""
        employee_id = uuid4()
        data = LeaveRequestCreate(
            employee_id=employee_id,
            type=LeaveType.PAID,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=5)
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_leave_request(data, uuid4())

        mock_db.add.assert_called_once()
        assert result.type == LeaveType.PAID

    def test_approve_leave_request(self, service, mock_db):
        """Tester l'approbation d'une demande de congé."""
        leave_id = uuid4()
        approver_id = uuid4()
        mock_leave = MagicMock()
        mock_leave.status = LeaveStatus.PENDING
        mock_leave.days_count = Decimal("5")
        mock_leave.employee_id = uuid4()

        mock_db.query.return_value.filter.return_value.first.return_value = mock_leave

        result = service.approve_leave_request(leave_id, approver_id)

        assert mock_leave.status == LeaveStatus.APPROVED
        assert mock_leave.approved_by == approver_id
        mock_db.commit.assert_called()

    def test_reject_leave_request(self, service, mock_db):
        """Tester le rejet d'une demande de congé."""
        leave_id = uuid4()
        mock_leave = MagicMock()
        mock_leave.status = LeaveStatus.PENDING

        mock_db.query.return_value.filter.return_value.first.return_value = mock_leave

        result = service.reject_leave_request(leave_id, uuid4(), "Effectifs insuffisants")

        assert mock_leave.status == LeaveStatus.REJECTED
        assert mock_leave.rejection_reason == "Effectifs insuffisants"


# =============================================================================
# TESTS DU SERVICE - PAIE
# =============================================================================

class TestHRServicePayroll:
    """Tests du service HR - Paie."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return HRService(mock_db, "test-tenant")

    def test_create_payroll_period(self, service, mock_db):
        """Tester la création d'une période de paie."""
        data = PayrollPeriodCreate(
            name="Janvier 2026",
            year=2026,
            month=1,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31)
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_payroll_period(data)

        mock_db.add.assert_called_once()
        assert result.year == 2026
        assert result.month == 1

    def test_generate_payslips(self, service, mock_db):
        """Tester la génération des bulletins de paie."""
        period_id = uuid4()
        mock_period = MagicMock()
        mock_period.status = PayrollStatus.DRAFT
        mock_period.start_date = date(2026, 1, 1)
        mock_period.end_date = date(2026, 1, 31)

        mock_employees = [
            MagicMock(id=uuid4(), gross_salary=Decimal("3500")),
            MagicMock(id=uuid4(), gross_salary=Decimal("4000"))
        ]

        mock_db.query.return_value.filter.return_value.first.return_value = mock_period
        mock_db.query.return_value.filter.return_value.all.return_value = mock_employees
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        # Test que la méthode ne lève pas d'exception
        service.generate_payslips(period_id, uuid4())


# =============================================================================
# TESTS DU SERVICE - FORMATIONS
# =============================================================================

class TestHRServiceTraining:
    """Tests du service HR - Formations."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return HRService(mock_db, "test-tenant")

    def test_create_training(self, service, mock_db):
        """Tester la création d'une formation."""
        data = TrainingCreate(
            code="FORM001",
            name="Formation Management",
            type=TrainingType.INTERNAL,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2)
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_training(data, uuid4())

        mock_db.add.assert_called_once()
        assert result.code == "FORM001"

    def test_enroll_participant(self, service, mock_db):
        """Tester l'inscription à une formation."""
        training_id = uuid4()
        employee_id = uuid4()

        mock_training = MagicMock()
        mock_training.max_participants = 20
        mock_db.query.return_value.filter.return_value.first.return_value = mock_training
        mock_db.query.return_value.filter.return_value.count.return_value = 5

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        data = TrainingParticipantCreate(
            training_id=training_id,
            employee_id=employee_id
        )

        result = service.enroll_participant(data)

        mock_db.add.assert_called_once()


# =============================================================================
# TESTS DU SERVICE - ÉVALUATIONS
# =============================================================================

class TestHRServiceEvaluations:
    """Tests du service HR - Évaluations."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return HRService(mock_db, "test-tenant")

    def test_create_evaluation(self, service, mock_db):
        """Tester la création d'une évaluation."""
        data = EvaluationCreate(
            employee_id=uuid4(),
            type=EvaluationType.ANNUAL,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            scheduled_date=date(2026, 1, 15)
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_evaluation(data, uuid4())

        mock_db.add.assert_called_once()
        assert result.type == EvaluationType.ANNUAL

    def test_complete_evaluation(self, service, mock_db):
        """Tester la complétion d'une évaluation."""
        eval_id = uuid4()
        mock_eval = MagicMock()
        mock_eval.status = EvaluationStatus.IN_PROGRESS

        mock_db.query.return_value.filter.return_value.first.return_value = mock_eval

        result = service.complete_evaluation(
            eval_id,
            overall_score=Decimal("4.2"),
            comments="Excellent travail"
        )

        assert mock_eval.status == EvaluationStatus.COMPLETED
        assert mock_eval.overall_score == Decimal("4.2")


# =============================================================================
# TESTS FACTORY
# =============================================================================

class TestFactory:
    """Tests de la factory."""

    def test_get_hr_service(self):
        """Tester la factory."""
        mock_db = MagicMock()
        service = get_hr_service(mock_db, "test-tenant")

        assert isinstance(service, HRService)
        assert service.tenant_id == "test-tenant"


# =============================================================================
# TESTS MULTI-TENANT
# =============================================================================

class TestMultiTenant:
    """Tests d'isolation multi-tenant."""

    def test_tenant_isolation(self):
        """Tester l'isolation des tenants."""
        mock_db = MagicMock()

        service_a = HRService(mock_db, "tenant-A")
        service_b = HRService(mock_db, "tenant-B")

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # Créer employé pour tenant A
        emp_a = service_a.create_employee(EmployeeCreate(
            employee_number="EMP001", first_name="Jean", last_name="A"
        ), uuid4())

        # Créer employé pour tenant B
        emp_b = service_b.create_employee(EmployeeCreate(
            employee_number="EMP001", first_name="Jean", last_name="B"
        ), uuid4())

        # Vérifier isolation
        assert emp_a.tenant_id == "tenant-A"
        assert emp_b.tenant_id == "tenant-B"


# =============================================================================
# TESTS CALCULS RH
# =============================================================================

class TestHRCalculations:
    """Tests des calculs RH."""

    def test_leave_days_calculation(self):
        """Tester le calcul des jours de congés."""
        start = date(2026, 6, 1)
        end = date(2026, 6, 5)

        # Du 1er au 5 juin = 5 jours (weekend non inclus dépend de la logique)
        days = (end - start).days + 1
        assert days == 5

    def test_net_salary_calculation(self):
        """Tester le calcul du salaire net."""
        gross = Decimal("3500")
        employee_charges_rate = Decimal("0.22")  # 22%

        employee_charges = gross * employee_charges_rate
        net_before_tax = gross - employee_charges

        assert net_before_tax == Decimal("2730")

    def test_overtime_calculation(self):
        """Tester le calcul des heures supplémentaires."""
        worked_hours = Decimal("42")
        regular_hours = Decimal("35")
        overtime_rate = Decimal("1.25")
        hourly_rate = Decimal("20")

        overtime_hours = worked_hours - regular_hours
        overtime_pay = overtime_hours * hourly_rate * overtime_rate

        assert overtime_hours == Decimal("7")
        assert overtime_pay == Decimal("175")


# =============================================================================
# EXÉCUTION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
