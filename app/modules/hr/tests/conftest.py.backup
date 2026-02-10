"""
Configuration pytest et fixtures communes pour les tests HR
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, date, timedelta
from uuid import uuid4

from app.core.saas_context import SaaSContext, UserRole
from fastapi import Depends

from app.modules.hr.models import (
    Department,
    Position,
    Employee,
    Contract,
    LeaveRequest,
    PayrollPeriod,
    Payslip,
    HRTimeEntry,
    Skill,
    EmployeeSkill,
    Training,
    TrainingParticipant,
    Evaluation,
    HRDocument,
    EmployeeStatus,
    ContractType,
    LeaveType,
    LeaveStatus,
    PayrollStatus,
    TrainingType,
    TrainingStatus,
    EvaluationStatus,
    DocumentType,
)


# ============================================================================
# FIXTURES GLOBALES
# ============================================================================

@pytest.fixture(scope="session")
def test_config():
    """Configuration de test"""
    return {
        "database_url": "sqlite:///:memory:",
        "testing": True
    }


@pytest.fixture(autouse=True)
def mock_saas_context(monkeypatch):
    """
    Mock get_saas_context pour tous les tests
    Remplace la dépendance FastAPI par un mock
    """
    def mock_get_context():
        return SaaSContext(
            tenant_id="tenant-test-001",
            user_id="user-test-001",
            role=UserRole.ADMIN,
            permissions=["hr.*"],
            scope="full",
            session_id="session-test",
            ip_address="127.0.0.1",
            user_agent="pytest",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow()
        )

    # Remplacer la dépendance FastAPI
    from app.modules.hr import router_v2
    monkeypatch.setattr(router_v2, "get_saas_context", mock_get_context)

    return mock_get_context


@pytest.fixture(scope="function")
def clean_database(db_session):
    """Nettoyer la base après chaque test"""
    yield
    db_session.rollback()


@pytest.fixture
def tenant_id():
    """ID du tenant de test"""
    return "tenant-test-001"


@pytest.fixture
def user_id():
    """ID de l'utilisateur de test"""
    return "user-test-001"


# ============================================================================
# FIXTURES DONNÉES HR
# ============================================================================

@pytest.fixture
def sample_department(db_session, tenant_id):
    """Fixture pour un département de test"""
    department = Department(
        id=uuid4(),
        tenant_id=tenant_id,
        code="DEV",
        name="Développement",
        description="Équipe de développement logiciel",
        is_active=True
    )
    db_session.add(department)
    db_session.commit()
    db_session.refresh(department)
    return department


@pytest.fixture
def sample_position(db_session, tenant_id, sample_department):
    """Fixture pour un poste de test"""
    position = Position(
        id=uuid4(),
        tenant_id=tenant_id,
        department_id=sample_department.id,
        code="DEV-SENIOR",
        title="Développeur Senior",
        description="Développeur avec 5+ ans d'expérience",
        is_active=True
    )
    db_session.add(position)
    db_session.commit()
    db_session.refresh(position)
    return position


@pytest.fixture
def sample_employee(db_session, tenant_id, sample_position, user_id):
    """Fixture pour un employé de test"""
    employee = Employee(
        id=uuid4(),
        tenant_id=tenant_id,
        position_id=sample_position.id,
        employee_number="EMP-TEST-001",
        first_name="Jean",
        last_name="Dupont",
        email="jean.dupont@company.com",
        phone="+33123456789",
        hire_date=date.today() - timedelta(days=365),
        status=EmployeeStatus.ACTIVE,
        created_by=user_id,
        created_at=datetime.utcnow()
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee


@pytest.fixture
def sample_contract(db_session, tenant_id, sample_employee, user_id):
    """Fixture pour un contrat de test"""
    contract = Contract(
        id=uuid4(),
        tenant_id=tenant_id,
        employee_id=sample_employee.id,
        contract_type=ContractType.CDI,
        start_date=date.today() - timedelta(days=365),
        salary=50000.0,
        weekly_hours=35.0,
        created_by=user_id,
        created_at=datetime.utcnow()
    )
    db_session.add(contract)
    db_session.commit()
    db_session.refresh(contract)
    return contract


@pytest.fixture
def sample_leave_request(db_session, tenant_id, sample_employee):
    """Fixture pour une demande de congé de test"""
    leave = LeaveRequest(
        id=uuid4(),
        tenant_id=tenant_id,
        employee_id=sample_employee.id,
        leave_type=LeaveType.PAID_LEAVE,
        start_date=date.today() + timedelta(days=7),
        end_date=date.today() + timedelta(days=12),
        status=LeaveStatus.PENDING,
        reason="Vacances d'été"
    )
    db_session.add(leave)
    db_session.commit()
    db_session.refresh(leave)
    return leave


@pytest.fixture
def sample_payroll_period(db_session, tenant_id, user_id):
    """Fixture pour une période de paie de test"""
    period = PayrollPeriod(
        id=uuid4(),
        tenant_id=tenant_id,
        year=2024,
        month=1,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        created_by=user_id
    )
    db_session.add(period)
    db_session.commit()
    db_session.refresh(period)
    return period


@pytest.fixture
def sample_payslip(db_session, tenant_id, sample_employee, sample_payroll_period, user_id):
    """Fixture pour un bulletin de paie de test"""
    payslip = Payslip(
        id=uuid4(),
        tenant_id=tenant_id,
        employee_id=sample_employee.id,
        period_id=sample_payroll_period.id,
        gross_salary=4000.0,
        net_salary=3000.0,
        worked_hours=151.67,
        status=PayrollStatus.DRAFT,
        created_by=user_id
    )
    db_session.add(payslip)
    db_session.commit()
    db_session.refresh(payslip)
    return payslip


@pytest.fixture
def sample_time_entry(db_session, tenant_id, sample_employee):
    """Fixture pour une saisie de temps de test"""
    time_entry = HRTimeEntry(
        id=uuid4(),
        tenant_id=tenant_id,
        employee_id=sample_employee.id,
        date=date.today(),
        hours=8.0,
        description="Développement feature X"
    )
    db_session.add(time_entry)
    db_session.commit()
    db_session.refresh(time_entry)
    return time_entry


@pytest.fixture
def sample_skill(db_session, tenant_id):
    """Fixture pour une compétence de test"""
    skill = Skill(
        id=uuid4(),
        tenant_id=tenant_id,
        name="Python",
        category="Développement",
        description="Langage de programmation"
    )
    db_session.add(skill)
    db_session.commit()
    db_session.refresh(skill)
    return skill


@pytest.fixture
def sample_employee_skill(db_session, tenant_id, sample_employee, sample_skill):
    """Fixture pour une compétence d'employé de test"""
    emp_skill = EmployeeSkill(
        id=uuid4(),
        tenant_id=tenant_id,
        employee_id=sample_employee.id,
        skill_id=sample_skill.id,
        level=4,
        acquired_date=date.today() - timedelta(days=180)
    )
    db_session.add(emp_skill)
    db_session.commit()
    db_session.refresh(emp_skill)
    return emp_skill


@pytest.fixture
def sample_training(db_session, tenant_id, user_id):
    """Fixture pour une formation de test"""
    training = Training(
        id=uuid4(),
        tenant_id=tenant_id,
        title="Formation Python Avancé",
        training_type=TrainingType.TECHNICAL,
        start_date=date.today() + timedelta(days=30),
        end_date=date.today() + timedelta(days=33),
        max_participants=10,
        status=TrainingStatus.PLANNED,
        created_by=user_id
    )
    db_session.add(training)
    db_session.commit()
    db_session.refresh(training)
    return training


@pytest.fixture
def sample_training_participant(db_session, tenant_id, sample_employee, sample_training):
    """Fixture pour un participant à une formation"""
    participant = TrainingParticipant(
        id=uuid4(),
        tenant_id=tenant_id,
        training_id=sample_training.id,
        employee_id=sample_employee.id,
        enrollment_date=date.today(),
        status="ENROLLED"
    )
    db_session.add(participant)
    db_session.commit()
    db_session.refresh(participant)
    return participant


@pytest.fixture
def sample_evaluation(db_session, tenant_id, sample_employee, user_id):
    """Fixture pour une évaluation de test"""
    evaluation = Evaluation(
        id=uuid4(),
        tenant_id=tenant_id,
        employee_id=sample_employee.id,
        evaluator_id=sample_employee.id,  # Auto-évaluation pour test
        evaluation_date=date.today(),
        status=EvaluationStatus.DRAFT,
        overall_rating=4,
        created_by=user_id
    )
    db_session.add(evaluation)
    db_session.commit()
    db_session.refresh(evaluation)
    return evaluation


@pytest.fixture
def sample_hr_document(db_session, tenant_id, sample_employee, user_id):
    """Fixture pour un document RH de test"""
    document = HRDocument(
        id=uuid4(),
        tenant_id=tenant_id,
        employee_id=sample_employee.id,
        document_type=DocumentType.CONTRACT,
        title="Contrat de travail CDI",
        file_path="/documents/contracts/emp001_cdi.pdf",
        uploaded_by=user_id,
        uploaded_at=datetime.utcnow()
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document


# ============================================================================
# FIXTURES HELPERS
# ============================================================================

@pytest.fixture
def create_test_data():
    """Factory pour créer des données de test"""
    def _create(model_class, **kwargs):
        instance = model_class(**kwargs)
        return instance
    return _create


@pytest.fixture
def mock_service():
    """Mock du service HR pour tests unitaires"""
    service = Mock()
    service.create_department = Mock(return_value={"id": str(uuid4()), "code": "TEST"})
    service.list_departments = Mock(return_value=[])
    service.create_employee = Mock(return_value={"id": str(uuid4())})
    return service


@pytest.fixture
def sample_employee_data(sample_position):
    """Données de test pour création employé"""
    return {
        "employee_number": "EMP-NEW-001",
        "first_name": "Nouveau",
        "last_name": "Employé",
        "email": "nouveau@company.com",
        "position_id": str(sample_position.id),
        "hire_date": str(date.today()),
        "status": "ACTIVE"
    }


@pytest.fixture
def sample_leave_data(sample_employee):
    """Données de test pour demande de congé"""
    return {
        "employee_id": str(sample_employee.id),
        "leave_type": "PAID_LEAVE",
        "start_date": str(date.today() + timedelta(days=7)),
        "end_date": str(date.today() + timedelta(days=12)),
        "reason": "Vacances"
    }


# ============================================================================
# FIXTURES ASSERTIONS
# ============================================================================

@pytest.fixture
def assert_response_success():
    """Helper pour asserter une réponse successful"""
    def _assert(response, expected_status=200):
        assert response.status_code == expected_status
        if response.status_code != 204:  # No content
            data = response.json()
            assert data is not None
            return data
    return _assert


@pytest.fixture
def assert_tenant_isolation():
    """Helper pour vérifier l'isolation tenant (CRITIQUE pour RH)"""
    def _assert(response, tenant_id):
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                for item in data:
                    if "tenant_id" in item:
                        assert item["tenant_id"] == tenant_id
            elif isinstance(data, dict):
                if "employees" in data:  # Liste paginée employés
                    for employee in data["employees"]:
                        if "tenant_id" in employee:
                            assert employee["tenant_id"] == tenant_id
                elif "tenant_id" in data:
                    assert data["tenant_id"] == tenant_id
    return _assert


@pytest.fixture
def assert_audit_trail():
    """Helper pour vérifier la présence d'audit trail"""
    def _assert(response_data):
        # Vérifier au moins un champ d'audit est présent
        audit_fields = ["created_by", "updated_by", "approved_by", "rejected_by",
                       "validated_by", "terminated_by", "uploaded_by"]
        has_audit = any(field in response_data for field in audit_fields)
        assert has_audit, "Aucun champ d'audit trail trouvé"
    return _assert


@pytest.fixture
def assert_sensitive_data_protection():
    """Helper pour valider la protection des données sensibles RH"""
    def _assert(response_data):
        # Vérifier que les données sensibles sont présentes UNIQUEMENT si autorisé
        # (dans ces tests, user a permission hr.* donc devrait voir)
        if "salary" in response_data:
            # Si présent, doit être non null pour employés actifs
            assert response_data["salary"] is not None or response_data.get("status") == "TERMINATED"
    return _assert
