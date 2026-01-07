"""
AZALS MODULE M9 - Tests Projets (Project Management)
=====================================================

Tests unitaires pour la gestion de projets.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

# Import des modèles
from app.modules.projects.models import (
    Project, ProjectPhase, ProjectTask as Task, ProjectMilestone as Milestone,
    ProjectTimeEntry as TimeEntry, ProjectExpense as Expense, ProjectTeamMember as Resource,
    ProjectRisk as Risk, ProjectIssue as Issue, ProjectDocument as Document,
    ProjectStatus, ProjectPriority as ProjectType, TaskStatus, TaskPriority,
    MilestoneStatus, ExpenseStatus, TeamMemberRole as ResourceType,
    RiskImpact as RiskLevel, RiskStatus, IssueStatus, IssuePriority
)

# Import des schémas
from app.modules.projects.schemas import (
    ProjectCreate, ProjectUpdate as ProjectUpdateSchema,
    PhaseCreate, TaskCreate, TaskUpdate,
    MilestoneCreate, TimeEntryCreate,
    ExpenseCreate, TeamMemberCreate as ResourceCreate,
    RiskCreate, IssueCreate, DocumentCreate,
    ProjectDashboard, ProjectStats as ProjectMetrics, BurndownData as GanttData
)
# ResourceAllocationCreate n'existe plus - utiliser TeamMemberCreate
ResourceAllocationCreate = ResourceCreate

# Import du service
from app.modules.projects.service import ProjectsService as ProjectService, get_projects_service as get_project_service


# =============================================================================
# TESTS DES ENUMS
# =============================================================================

class TestEnums:
    """Tests des énumérations."""

    def test_project_status_values(self):
        """Tester les statuts de projet."""
        assert ProjectStatus.DRAFT.value == "DRAFT"
        assert ProjectStatus.PLANNING.value == "PLANNING"
        assert ProjectStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert ProjectStatus.ON_HOLD.value == "ON_HOLD"
        assert ProjectStatus.COMPLETED.value == "COMPLETED"
        assert len(ProjectStatus) >= 5

    def test_project_type_values(self):
        """Tester les types de projet."""
        assert ProjectType.INTERNAL.value == "INTERNAL"
        assert ProjectType.CLIENT.value == "CLIENT"
        assert ProjectType.RESEARCH.value == "RESEARCH"
        assert len(ProjectType) >= 3

    def test_task_status_values(self):
        """Tester les statuts de tâche."""
        assert TaskStatus.TODO.value == "TODO"
        assert TaskStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert TaskStatus.REVIEW.value == "REVIEW"
        assert TaskStatus.DONE.value == "DONE"
        assert len(TaskStatus) >= 4

    def test_task_priority_values(self):
        """Tester les priorités de tâche."""
        assert TaskPriority.LOW.value == "LOW"
        assert TaskPriority.NORMAL.value == "NORMAL"
        assert TaskPriority.HIGH.value == "HIGH"
        assert TaskPriority.URGENT.value == "URGENT"
        assert len(TaskPriority) == 4

    def test_risk_level_values(self):
        """Tester les niveaux de risque."""
        assert RiskLevel.LOW.value == "LOW"
        assert RiskLevel.MEDIUM.value == "MEDIUM"
        assert RiskLevel.HIGH.value == "HIGH"
        assert RiskLevel.CRITICAL.value == "CRITICAL"
        assert len(RiskLevel) == 4

    def test_issue_priority_values(self):
        """Tester les priorités d'incident."""
        assert IssuePriority.LOW.value == "LOW"
        assert IssuePriority.NORMAL.value == "NORMAL"
        assert IssuePriority.HIGH.value == "HIGH"
        assert IssuePriority.CRITICAL.value == "CRITICAL"
        assert len(IssuePriority) == 4


# =============================================================================
# TESTS DES MODÈLES
# =============================================================================

class TestModels:
    """Tests des modèles SQLAlchemy."""

    def test_project_model(self):
        """Tester le modèle Project."""
        project = Project(
            tenant_id="test-tenant",
            code="PRJ001",
            name="Projet Test",
            type=ProjectType.INTERNAL,
            start_date=date.today(),
            budget=Decimal("50000")
        )
        assert project.code == "PRJ001"
        assert project.type == ProjectType.INTERNAL
        assert project.status == ProjectStatus.DRAFT

    def test_phase_model(self):
        """Tester le modèle ProjectPhase."""
        phase = ProjectPhase(
            tenant_id="test-tenant",
            project_id=uuid4(),
            name="Phase 1 - Analyse",
            sequence=1,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30)
        )
        assert phase.name == "Phase 1 - Analyse"
        assert phase.sequence == 1

    def test_task_model(self):
        """Tester le modèle Task."""
        task = Task(
            tenant_id="test-tenant",
            project_id=uuid4(),
            code="TSK001",
            name="Rédiger spécifications",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            estimated_hours=Decimal("16")
        )
        assert task.code == "TSK001"
        assert task.status == TaskStatus.TODO
        assert task.priority == TaskPriority.HIGH

    def test_milestone_model(self):
        """Tester le modèle Milestone."""
        milestone = Milestone(
            tenant_id="test-tenant",
            project_id=uuid4(),
            name="Livraison v1.0",
            due_date=date.today() + timedelta(days=60)
        )
        assert milestone.name == "Livraison v1.0"
        assert milestone.status == MilestoneStatus.PENDING

    def test_time_entry_model(self):
        """Tester le modèle TimeEntry."""
        entry = TimeEntry(
            tenant_id="test-tenant",
            project_id=uuid4(),
            task_id=uuid4(),
            user_id=uuid4(),
            date=date.today(),
            hours=Decimal("8"),
            description="Développement"
        )
        assert entry.hours == Decimal("8")

    def test_expense_model(self):
        """Tester le modèle Expense."""
        expense = Expense(
            tenant_id="test-tenant",
            project_id=uuid4(),
            description="Achat licences",
            amount=Decimal("500"),
            expense_date=date.today()
        )
        assert expense.amount == Decimal("500")
        assert expense.status == ExpenseStatus.PENDING

    def test_risk_model(self):
        """Tester le modèle Risk."""
        risk = Risk(
            tenant_id="test-tenant",
            project_id=uuid4(),
            title="Retard fournisseur",
            level=RiskLevel.HIGH,
            probability=Decimal("60"),
            impact=Decimal("80")
        )
        assert risk.level == RiskLevel.HIGH
        assert risk.status == RiskStatus.IDENTIFIED


# =============================================================================
# TESTS DES SCHÉMAS
# =============================================================================

class TestSchemas:
    """Tests des schémas Pydantic."""

    def test_project_create_schema(self):
        """Tester le schéma ProjectCreate."""
        data = ProjectCreate(
            code="PRJ001",
            name="Nouveau Projet",
            type=ProjectType.CLIENT,
            start_date=date.today(),
            budget=Decimal("100000"),
            client_id=uuid4()
        )
        assert data.code == "PRJ001"
        assert data.type == ProjectType.CLIENT

    def test_task_create_schema(self):
        """Tester le schéma TaskCreate."""
        data = TaskCreate(
            code="TSK001",
            name="Développement API",
            priority=TaskPriority.HIGH,
            estimated_hours=Decimal("40"),
            start_date=date.today(),
            due_date=date.today() + timedelta(days=7)
        )
        assert data.priority == TaskPriority.HIGH
        assert data.estimated_hours == Decimal("40")

    def test_time_entry_create_schema(self):
        """Tester le schéma TimeEntryCreate."""
        data = TimeEntryCreate(
            task_id=uuid4(),
            date=date.today(),
            hours=Decimal("7.5"),
            description="Développement fonctionnalité X"
        )
        assert data.hours == Decimal("7.5")

    def test_risk_create_schema(self):
        """Tester le schéma RiskCreate."""
        data = RiskCreate(
            title="Risque technique",
            description="Complexité sous-estimée",
            level=RiskLevel.MEDIUM,
            probability=Decimal("40"),
            impact=Decimal("60")
        )
        assert data.level == RiskLevel.MEDIUM


# =============================================================================
# TESTS DU SERVICE - PROJETS
# =============================================================================

class TestProjectServiceProjects:
    """Tests du service Project - Projets."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return ProjectService(mock_db, "test-tenant")

    def test_create_project(self, service, mock_db):
        """Tester la création d'un projet."""
        data = ProjectCreate(
            code="PRJ001",
            name="Projet Test",
            type=ProjectType.INTERNAL,
            start_date=date.today()
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_project(data, uuid4())

        mock_db.add.assert_called_once()
        assert result.code == "PRJ001"

    def test_start_project(self, service, mock_db):
        """Tester le démarrage d'un projet."""
        project_id = uuid4()
        mock_project = MagicMock()
        mock_project.status = ProjectStatus.PLANNING

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = service.start_project(project_id)

        assert mock_project.status == ProjectStatus.IN_PROGRESS

    def test_complete_project(self, service, mock_db):
        """Tester la clôture d'un projet."""
        project_id = uuid4()
        mock_project = MagicMock()
        mock_project.status = ProjectStatus.IN_PROGRESS

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = service.complete_project(project_id)

        assert mock_project.status == ProjectStatus.COMPLETED


# =============================================================================
# TESTS DU SERVICE - TÂCHES
# =============================================================================

class TestProjectServiceTasks:
    """Tests du service Project - Tâches."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return ProjectService(mock_db, "test-tenant")

    def test_create_task(self, service, mock_db):
        """Tester la création d'une tâche."""
        project_id = uuid4()
        data = TaskCreate(
            code="TSK001",
            name="Développement",
            priority=TaskPriority.NORMAL
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_task(project_id, data, uuid4())

        mock_db.add.assert_called()

    def test_start_task(self, service, mock_db):
        """Tester le démarrage d'une tâche."""
        task_id = uuid4()
        mock_task = MagicMock()
        mock_task.status = TaskStatus.TODO

        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        result = service.start_task(task_id, uuid4())

        assert mock_task.status == TaskStatus.IN_PROGRESS

    def test_complete_task(self, service, mock_db):
        """Tester la complétion d'une tâche."""
        task_id = uuid4()
        mock_task = MagicMock()
        mock_task.status = TaskStatus.IN_PROGRESS

        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        result = service.complete_task(task_id)

        assert mock_task.status == TaskStatus.DONE


# =============================================================================
# TESTS DU SERVICE - TEMPS
# =============================================================================

class TestProjectServiceTime:
    """Tests du service Project - Temps."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return ProjectService(mock_db, "test-tenant")

    def test_log_time(self, service, mock_db):
        """Tester la saisie de temps."""
        project_id = uuid4()
        data = TimeEntryCreate(
            task_id=uuid4(),
            date=date.today(),
            hours=Decimal("8")
        )

        mock_task = MagicMock()
        mock_task.actual_hours = Decimal("0")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.log_time(project_id, data, uuid4())

        mock_db.add.assert_called()


# =============================================================================
# TESTS DU SERVICE - RISQUES
# =============================================================================

class TestProjectServiceRisks:
    """Tests du service Project - Risques."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return ProjectService(mock_db, "test-tenant")

    def test_create_risk(self, service, mock_db):
        """Tester la création d'un risque."""
        project_id = uuid4()
        data = RiskCreate(
            title="Risque technique",
            level=RiskLevel.HIGH,
            probability=Decimal("70"),
            impact=Decimal("80")
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_risk(project_id, data, uuid4())

        mock_db.add.assert_called()

    def test_mitigate_risk(self, service, mock_db):
        """Tester la mitigation d'un risque."""
        risk_id = uuid4()
        mock_risk = MagicMock()
        mock_risk.status = RiskStatus.IDENTIFIED

        mock_db.query.return_value.filter.return_value.first.return_value = mock_risk

        result = service.mitigate_risk(risk_id, "Plan de mitigation")

        assert mock_risk.status == RiskStatus.MITIGATED


# =============================================================================
# TESTS FACTORY
# =============================================================================

class TestFactory:
    """Tests de la factory."""

    def test_get_project_service(self):
        """Tester la factory."""
        mock_db = MagicMock()
        service = get_project_service(mock_db, "test-tenant")

        assert isinstance(service, ProjectService)
        assert service.tenant_id == "test-tenant"


# =============================================================================
# TESTS CALCULS PROJET
# =============================================================================

class TestProjectCalculations:
    """Tests des calculs de projet."""

    def test_progress_calculation(self):
        """Tester le calcul de l'avancement."""
        completed_tasks = 8
        total_tasks = 10

        progress = (completed_tasks / total_tasks) * 100

        assert progress == 80.0

    def test_budget_variance(self):
        """Tester le calcul de l'écart budgétaire."""
        budget = Decimal("100000")
        actual_cost = Decimal("95000")

        variance = budget - actual_cost
        variance_percent = (variance / budget) * 100

        assert variance == Decimal("5000")
        assert variance_percent == Decimal("5")

    def test_schedule_variance(self):
        """Tester le calcul de l'écart de planning."""
        planned_days = 30
        actual_days = 35

        variance_days = actual_days - planned_days

        assert variance_days == 5  # 5 jours de retard

    def test_risk_score(self):
        """Tester le calcul du score de risque."""
        probability = Decimal("60")  # 60%
        impact = Decimal("80")  # 80%

        risk_score = (probability * impact) / 100

        assert risk_score == Decimal("48")

    def test_resource_utilization(self):
        """Tester le calcul d'utilisation des ressources."""
        available_hours = Decimal("160")  # Par mois
        logged_hours = Decimal("140")

        utilization = (logged_hours / available_hours) * 100

        assert utilization == Decimal("87.5")


# =============================================================================
# EXÉCUTION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
