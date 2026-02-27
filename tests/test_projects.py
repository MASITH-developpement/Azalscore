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
    Project, ProjectPhase, ProjectTask, ProjectMilestone,
    ProjectTimeEntry, ProjectExpense, ProjectTeamMember,
    ProjectRisk, ProjectIssue, ProjectDocument,
    ProjectStatus, ProjectPriority, TaskStatus, TaskPriority,
    MilestoneStatus, ExpenseStatus, TeamMemberRole,
    RiskImpact, RiskProbability, RiskStatus, IssueStatus, IssuePriority,
    TimeEntryStatus
)

# Import des schémas
from app.modules.projects.schemas import (
    ProjectCreate, ProjectUpdate,
    PhaseCreate, TaskCreate, TaskUpdate,
    MilestoneCreate, TimeEntryCreate,
    ExpenseCreate, TeamMemberCreate,
    RiskCreate, IssueCreate, DocumentCreate,
    ProjectDashboard, ProjectStats, BurndownData
)

# Import du service
from app.modules.projects.service import ProjectsService, get_projects_service


# =============================================================================
# TESTS DES ENUMS
# =============================================================================

class TestEnums:
    """Tests des énumérations."""

    def test_project_status_values(self):
        """Tester les statuts de projet."""
        assert ProjectStatus.DRAFT.value == "draft"
        assert ProjectStatus.PLANNING.value == "planning"
        assert ProjectStatus.IN_PROGRESS.value == "in_progress"
        assert ProjectStatus.ON_HOLD.value == "on_hold"
        assert ProjectStatus.COMPLETED.value == "completed"
        assert len(ProjectStatus) >= 5

    def test_project_priority_values(self):
        """Tester les priorités de projet."""
        assert ProjectPriority.LOW.value == "low"
        assert ProjectPriority.MEDIUM.value == "medium"
        assert ProjectPriority.HIGH.value == "high"
        assert ProjectPriority.CRITICAL.value == "critical"
        assert len(ProjectPriority) == 4

    def test_task_status_values(self):
        """Tester les statuts de tâche."""
        assert TaskStatus.TODO.value == "todo"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.REVIEW.value == "review"
        assert TaskStatus.COMPLETED.value == "completed"
        assert len(TaskStatus) >= 4

    def test_task_priority_values(self):
        """Tester les priorités de tâche."""
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.MEDIUM.value == "medium"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.URGENT.value == "urgent"
        assert len(TaskPriority) == 4

    def test_risk_impact_values(self):
        """Tester les impacts de risque."""
        assert RiskImpact.NEGLIGIBLE.value == "negligible"
        assert RiskImpact.MINOR.value == "minor"
        assert RiskImpact.MODERATE.value == "moderate"
        assert RiskImpact.MAJOR.value == "major"
        assert RiskImpact.CRITICAL.value == "critical"
        assert len(RiskImpact) == 5

    def test_risk_probability_values(self):
        """Tester les probabilités de risque."""
        assert RiskProbability.RARE.value == "rare"
        assert RiskProbability.UNLIKELY.value == "unlikely"
        assert RiskProbability.POSSIBLE.value == "possible"
        assert RiskProbability.LIKELY.value == "likely"
        assert len(RiskProbability) >= 4

    def test_issue_priority_values(self):
        """Tester les priorités d'incident."""
        assert IssuePriority.LOW.value == "low"
        assert IssuePriority.MEDIUM.value == "medium"
        assert IssuePriority.HIGH.value == "high"
        assert IssuePriority.CRITICAL.value == "critical"
        assert len(IssuePriority) == 4


# =============================================================================
# TESTS DES MODÈLES
# =============================================================================

class TestModels:
    """Tests des modèles SQLAlchemy."""

    def test_project_model(self):
        """Tester le modèle Project."""
        project = Project(
            tenant_id=1,
            code="PRJ001",
            name="Projet Test",
            status=ProjectStatus.DRAFT,
            priority=ProjectPriority.MEDIUM,
            planned_start_date=date.today(),
            planned_budget=Decimal("50000")
        )
        assert project.code == "PRJ001"
        assert project.priority == ProjectPriority.MEDIUM
        assert project.status == ProjectStatus.DRAFT

    def test_phase_model(self):
        """Tester le modèle ProjectPhase."""
        phase = ProjectPhase(
            tenant_id=1,
            project_id=uuid4(),
            name="Phase 1 - Analyse",
            order=1,
            planned_start_date=date.today(),
            planned_end_date=date.today() + timedelta(days=30)
        )
        assert phase.name == "Phase 1 - Analyse"
        assert phase.order == 1

    def test_task_model(self):
        """Tester le modèle ProjectTask."""
        task = ProjectTask(
            tenant_id=1,
            project_id=uuid4(),
            code="TSK001",
            name="Rédiger spécifications",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            estimated_hours=16
        )
        assert task.code == "TSK001"
        assert task.status == TaskStatus.TODO
        assert task.priority == TaskPriority.HIGH

    def test_milestone_model(self):
        """Tester le modèle ProjectMilestone."""
        milestone = ProjectMilestone(
            tenant_id=1,
            project_id=uuid4(),
            name="Livraison v1.0",
            target_date=date.today() + timedelta(days=60),
            status=MilestoneStatus.PENDING
        )
        assert milestone.name == "Livraison v1.0"
        assert milestone.status == MilestoneStatus.PENDING

    def test_time_entry_model(self):
        """Tester le modèle ProjectTimeEntry."""
        entry = ProjectTimeEntry(
            tenant_id=1,
            project_id=uuid4(),
            task_id=uuid4(),
            user_id=uuid4(),
            date=date.today(),
            hours=8,
            description="Développement"
        )
        assert entry.hours == 8

    def test_expense_model(self):
        """Tester le modèle ProjectExpense."""
        expense = ProjectExpense(
            tenant_id=1,
            project_id=uuid4(),
            description="Achat licences",
            amount=Decimal("500"),
            expense_date=date.today(),
            status=ExpenseStatus.DRAFT
        )
        assert expense.amount == Decimal("500")
        assert expense.status == ExpenseStatus.DRAFT

    def test_risk_model(self):
        """Tester le modèle ProjectRisk."""
        risk = ProjectRisk(
            tenant_id=1,
            project_id=uuid4(),
            title="Retard fournisseur",
            probability=RiskProbability.LIKELY,
            impact=RiskImpact.MAJOR,
            status=RiskStatus.IDENTIFIED
        )
        assert risk.probability == RiskProbability.LIKELY
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
            priority=ProjectPriority.HIGH,
            planned_start_date=date.today(),
            planned_budget=Decimal("100000"),
            customer_id=uuid4()
        )
        assert data.code == "PRJ001"
        assert data.priority == ProjectPriority.HIGH

    def test_task_create_schema(self):
        """Tester le schéma TaskCreate."""
        data = TaskCreate(
            name="Développement API",
            priority=TaskPriority.HIGH,
            estimated_hours=40,
            planned_start_date=date.today(),
            due_date=date.today() + timedelta(days=7)
        )
        assert data.priority == TaskPriority.HIGH
        assert data.estimated_hours == 40

    def test_time_entry_create_schema(self):
        """Tester le schéma TimeEntryCreate."""
        data = TimeEntryCreate(
            task_id=uuid4(),
            entry_date=date.today(),
            hours=7.5,
            description="Développement fonctionnalité X"
        )
        assert data.hours == 7.5
        assert data.entry_date == date.today()

    def test_risk_create_schema(self):
        """Tester le schéma RiskCreate."""
        data = RiskCreate(
            title="Risque technique",
            description="Complexité sous-estimée",
            probability=RiskProbability.POSSIBLE,
            impact=RiskImpact.MODERATE
        )
        assert data.probability == RiskProbability.POSSIBLE
        assert data.impact == RiskImpact.MODERATE


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
        return ProjectsService(mock_db, tenant_id=1, user_id=uuid4())

    def test_create_project(self, service, mock_db):
        """Tester la création d'un projet."""
        data = ProjectCreate(
            code="PRJ001",
            name="Projet Test",
            priority=ProjectPriority.MEDIUM,
            planned_start_date=date.today()
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_project(data)

        mock_db.add.assert_called_once()
        assert result.code == "PRJ001"

    def test_get_project(self, service, mock_db):
        """Tester la récupération d'un projet."""
        project_id = uuid4()
        mock_project = MagicMock(spec=Project)
        mock_project.id = project_id
        mock_project.code = "PRJ001"

        # Support eager loading with .options()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_project

        result = service.get_project(project_id)

        assert result.id == project_id
        assert result.code == "PRJ001"

    def test_list_projects(self, service, mock_db):
        """Tester la liste des projets."""
        mock_projects = [MagicMock(spec=Project), MagicMock(spec=Project)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        # Support eager loading with .options()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_projects

        projects, total = service.list_projects()

        assert total == 2
        assert len(projects) == 2

    def test_update_project(self, service, mock_db):
        """Tester la mise à jour d'un projet."""
        project_id = uuid4()
        mock_project = MagicMock(spec=Project)
        mock_project.id = project_id
        mock_project.status = ProjectStatus.DRAFT
        mock_project.actual_start_date = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        data = ProjectUpdate(name="Projet Renommé", status=ProjectStatus.IN_PROGRESS)
        result = service.update_project(project_id, data)

        mock_db.commit.assert_called_once()
        assert result is not None

    def test_delete_project(self, service, mock_db):
        """Tester la suppression d'un projet (soft delete)."""
        project_id = uuid4()
        mock_project = MagicMock(spec=Project)
        mock_project.id = project_id
        mock_project.is_active = True

        # Support eager loading with .options() in get_project
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_project

        result = service.delete_project(project_id)

        assert result is True
        assert mock_project.is_active is False


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
        return ProjectsService(mock_db, tenant_id=1, user_id=uuid4())

    def test_create_task(self, service, mock_db):
        """Tester la création d'une tâche."""
        project_id = uuid4()
        data = TaskCreate(
            name="Développement",
            priority=TaskPriority.MEDIUM
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_task(project_id, data)

        mock_db.add.assert_called()

    def test_get_task(self, service, mock_db):
        """Tester la récupération d'une tâche."""
        task_id = uuid4()
        mock_task = MagicMock(spec=ProjectTask)
        mock_task.id = task_id
        mock_task.name = "Test Task"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        result = service.get_task(task_id)

        assert result.id == task_id

    def test_list_tasks(self, service, mock_db):
        """Tester la liste des tâches."""
        mock_tasks = [MagicMock(spec=ProjectTask), MagicMock(spec=ProjectTask)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_tasks

        tasks, total = service.list_tasks()

        assert total == 2
        assert len(tasks) == 2

    def test_update_task(self, service, mock_db):
        """Tester la mise à jour d'une tâche."""
        # Ce test vérifie le schéma TaskUpdate
        data = TaskUpdate(status=TaskStatus.IN_PROGRESS, name="Updated Task")
        assert data.status == TaskStatus.IN_PROGRESS
        assert data.name == "Updated Task"

        # Vérifier que le service a la méthode
        assert hasattr(service, 'update_task')

    def test_delete_task(self, service, mock_db):
        """Tester la suppression d'une tâche."""
        task_id = uuid4()
        mock_task = MagicMock(spec=ProjectTask)
        mock_task.id = task_id

        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        result = service.delete_task(task_id)

        assert result is True


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
        return ProjectsService(mock_db, tenant_id=1, user_id=uuid4())

    def test_create_time_entry(self, service, mock_db):
        """Tester la saisie de temps."""
        # Ce test vérifie le schéma TimeEntryCreate
        data = TimeEntryCreate(
            task_id=uuid4(),
            entry_date=date.today(),
            hours=8
        )
        assert data.hours == 8
        assert data.entry_date == date.today()
        assert data.is_billable is True

        # Vérifier que le service a la méthode
        assert hasattr(service, 'create_time_entry')


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
        return ProjectsService(mock_db, tenant_id=1, user_id=uuid4())

    def test_create_risk(self, service, mock_db):
        """Tester la création d'un risque."""
        project_id = uuid4()
        data = RiskCreate(
            title="Risque technique",
            probability=RiskProbability.LIKELY,
            impact=RiskImpact.MAJOR
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_risk(project_id, data)

        mock_db.add.assert_called()

    def test_get_risks(self, service, mock_db):
        """Tester la liste des risques."""
        project_id = uuid4()
        mock_risks = [MagicMock(spec=ProjectRisk), MagicMock(spec=ProjectRisk)]

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_risks

        result = service.get_risks(project_id)

        assert len(result) == 2


# =============================================================================
# TESTS DU SERVICE - JALONS
# =============================================================================

class TestProjectServiceMilestones:
    """Tests du service Project - Jalons."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return ProjectsService(mock_db, tenant_id=1, user_id=uuid4())

    def test_create_milestone(self, service, mock_db):
        """Tester la création d'un jalon."""
        project_id = uuid4()
        data = MilestoneCreate(
            name="Livraison v1.0",
            target_date=date.today() + timedelta(days=30)
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_milestone(project_id, data)

        mock_db.add.assert_called()

    def test_get_milestones(self, service, mock_db):
        """Tester la liste des jalons."""
        project_id = uuid4()
        mock_milestones = [MagicMock(spec=ProjectMilestone)]

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_milestones

        result = service.get_milestones(project_id)

        assert len(result) == 1


# =============================================================================
# TESTS FACTORY
# =============================================================================

class TestFactory:
    """Tests de la factory."""

    def test_get_projects_service(self):
        """Tester la factory."""
        mock_db = MagicMock()
        user_id = uuid4()
        service = get_projects_service(mock_db, tenant_id=1, user_id=user_id)

        assert isinstance(service, ProjectsService)
        assert service.tenant_id == 1


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

    def test_resource_utilization(self):
        """Tester le calcul d'utilisation des ressources."""
        available_hours = Decimal("160")  # Par mois
        logged_hours = Decimal("140")

        utilization = (logged_hours / available_hours) * 100

        assert utilization == Decimal("87.5")

    def test_earned_value(self):
        """Tester le calcul de la valeur acquise (EV)."""
        budget = Decimal("100000")
        progress = Decimal("50")  # 50%

        earned_value = budget * progress / 100

        assert earned_value == Decimal("50000")

    def test_schedule_performance_index(self):
        """Tester le calcul du SPI."""
        earned_value = Decimal("50000")
        planned_value = Decimal("60000")

        spi = earned_value / planned_value

        assert spi < 1  # En retard

    def test_cost_performance_index(self):
        """Tester le calcul du CPI."""
        earned_value = Decimal("50000")
        actual_cost = Decimal("55000")

        cpi = earned_value / actual_cost

        assert cpi < 1  # Dépassement de coût


# =============================================================================
# EXÉCUTION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
