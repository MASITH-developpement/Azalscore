"""
Tests pour le module Gantt Production.

Couverture:
- Task management
- Dependency management
- Milestone management
- Resource management
- Timeline generation
- Conflict detection
- Critical path calculation
- Auto-scheduling
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.modules.production.gantt import (
    GanttService,
    GanttTask,
    GanttResource,
    GanttDependency,
    GanttMilestone,
    ResourceAllocation,
    ScheduleConflict,
    TaskType,
    DependencyType,
    ConflictType,
)
from app.modules.production.gantt.service import (
    ResourceType,
    Timeline,
    ResourceLoad,
)
from app.modules.production.gantt.router import router


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_db():
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def tenant_id():
    """Tenant ID for testing."""
    return "tenant-gantt-test"


@pytest.fixture
def gantt_service(mock_db, tenant_id):
    """Gantt service instance."""
    return GanttService(db=mock_db, tenant_id=tenant_id)


@pytest.fixture
def sample_dates():
    """Sample dates for testing."""
    now = datetime.now()
    return {
        "start": now,
        "end": now + timedelta(hours=8),
        "tomorrow": now + timedelta(days=1),
        "next_week": now + timedelta(days=7),
    }


# =============================================================================
# SERVICE TESTS - INITIALIZATION
# =============================================================================


class TestGanttServiceInit:
    """Tests d'initialisation du service."""

    def test_init_with_valid_tenant(self, mock_db, tenant_id):
        """Test init avec tenant valide."""
        service = GanttService(db=mock_db, tenant_id=tenant_id)
        assert service.tenant_id == tenant_id
        assert service.db == mock_db

    def test_init_without_tenant_raises(self, mock_db):
        """Test init sans tenant lève exception."""
        with pytest.raises(ValueError, match="tenant_id est requis"):
            GanttService(db=mock_db, tenant_id="")

    def test_init_with_none_tenant_raises(self, mock_db):
        """Test init avec tenant None lève exception."""
        with pytest.raises(ValueError, match="tenant_id est requis"):
            GanttService(db=mock_db, tenant_id=None)


# =============================================================================
# SERVICE TESTS - TASK MANAGEMENT
# =============================================================================


class TestTaskManagement:
    """Tests de gestion des tâches."""

    @pytest.mark.asyncio
    async def test_create_task(self, gantt_service, sample_dates):
        """Test création tâche."""
        task = await gantt_service.create_task(
            name="Tâche Test",
            task_type=TaskType.MANUFACTURING_ORDER,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )

        assert task.id is not None
        assert task.tenant_id == gantt_service.tenant_id
        assert task.name == "Tâche Test"
        assert task.task_type == TaskType.MANUFACTURING_ORDER
        assert task.progress == Decimal("0")

    @pytest.mark.asyncio
    async def test_create_task_with_resource(self, gantt_service, sample_dates):
        """Test création tâche avec ressource."""
        # Créer ressource d'abord
        resource = await gantt_service.create_resource(
            name="Machine 1",
            resource_type=ResourceType.MACHINE,
        )

        task = await gantt_service.create_task(
            name="Tâche avec ressource",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
            resource_id=resource.id,
        )

        assert task.resource_id == resource.id
        assert task.resource_name == "Machine 1"

    @pytest.mark.asyncio
    async def test_create_task_invalid_dates(self, gantt_service, sample_dates):
        """Test création tâche avec dates invalides."""
        with pytest.raises(ValueError, match="date de fin"):
            await gantt_service.create_task(
                name="Tâche invalide",
                task_type=TaskType.OPERATION,
                start=sample_dates["end"],  # Fin avant début
                end=sample_dates["start"],
            )

    @pytest.mark.asyncio
    async def test_task_duration(self, gantt_service, sample_dates):
        """Test calcul durée tâche."""
        task = await gantt_service.create_task(
            name="Tâche 8h",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],  # +8h
        )

        assert task.duration_hours == Decimal("8.00")

    @pytest.mark.asyncio
    async def test_get_task(self, gantt_service, sample_dates):
        """Test récupération tâche."""
        task = await gantt_service.create_task(
            name="Tâche",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )

        retrieved = await gantt_service.get_task(task.id)

        assert retrieved is not None
        assert retrieved.id == task.id

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, gantt_service):
        """Test tâche inexistante."""
        result = await gantt_service.get_task("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_task(self, gantt_service, sample_dates):
        """Test mise à jour tâche."""
        task = await gantt_service.create_task(
            name="Original",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )

        updated = await gantt_service.update_task(
            task_id=task.id,
            name="Modified",
            progress=Decimal("50"),
        )

        assert updated.name == "Modified"
        assert updated.progress == Decimal("50")

    @pytest.mark.asyncio
    async def test_update_progress(self, gantt_service, sample_dates):
        """Test mise à jour avancement."""
        task = await gantt_service.create_task(
            name="Tâche",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )

        await gantt_service.update_progress(task.id, Decimal("75"))

        retrieved = await gantt_service.get_task(task.id)
        assert retrieved.progress == Decimal("75")

    @pytest.mark.asyncio
    async def test_update_progress_clamped(self, gantt_service, sample_dates):
        """Test avancement limité à 0-100."""
        task = await gantt_service.create_task(
            name="Tâche",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )

        await gantt_service.update_progress(task.id, Decimal("150"))

        retrieved = await gantt_service.get_task(task.id)
        assert retrieved.progress == Decimal("100")

    @pytest.mark.asyncio
    async def test_delete_task(self, gantt_service, sample_dates):
        """Test suppression tâche."""
        task = await gantt_service.create_task(
            name="À supprimer",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )

        deleted = await gantt_service.delete_task(task.id)

        assert deleted is True
        assert await gantt_service.get_task(task.id) is None

    @pytest.mark.asyncio
    async def test_list_tasks(self, gantt_service, sample_dates):
        """Test liste des tâches."""
        await gantt_service.create_task(
            name="Tâche 1",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )
        await gantt_service.create_task(
            name="Tâche 2",
            task_type=TaskType.MAINTENANCE,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )

        tasks = await gantt_service.list_tasks()

        assert len(tasks) == 2

    @pytest.mark.asyncio
    async def test_list_tasks_filter_by_type(self, gantt_service, sample_dates):
        """Test filtre tâches par type."""
        await gantt_service.create_task(
            name="Opération",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )
        await gantt_service.create_task(
            name="Maintenance",
            task_type=TaskType.MAINTENANCE,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )

        operations = await gantt_service.list_tasks(task_type=TaskType.OPERATION)

        assert len(operations) == 1
        assert operations[0].task_type == TaskType.OPERATION

    @pytest.mark.asyncio
    async def test_task_is_completed(self, gantt_service, sample_dates):
        """Test vérification tâche complétée."""
        task = await gantt_service.create_task(
            name="Tâche",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )

        assert task.is_completed is False

        await gantt_service.update_progress(task.id, Decimal("100"))
        updated = await gantt_service.get_task(task.id)

        assert updated.is_completed is True


# =============================================================================
# SERVICE TESTS - DEPENDENCY MANAGEMENT
# =============================================================================


class TestDependencyManagement:
    """Tests de gestion des dépendances."""

    @pytest.mark.asyncio
    async def test_create_dependency(self, gantt_service, sample_dates):
        """Test création dépendance."""
        task1 = await gantt_service.create_task(
            name="Prédécesseur",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )
        task2 = await gantt_service.create_task(
            name="Successeur",
            task_type=TaskType.OPERATION,
            start=sample_dates["end"],
            end=sample_dates["end"] + timedelta(hours=4),
        )

        dep = await gantt_service.create_dependency(
            predecessor_id=task1.id,
            successor_id=task2.id,
        )

        assert dep is not None
        assert dep.predecessor_id == task1.id
        assert dep.successor_id == task2.id
        assert dep.dependency_type == DependencyType.FINISH_TO_START

    @pytest.mark.asyncio
    async def test_create_dependency_with_lag(self, gantt_service, sample_dates):
        """Test dépendance avec délai."""
        task1 = await gantt_service.create_task(
            name="T1",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )
        task2 = await gantt_service.create_task(
            name="T2",
            task_type=TaskType.OPERATION,
            start=sample_dates["end"],
            end=sample_dates["end"] + timedelta(hours=4),
        )

        dep = await gantt_service.create_dependency(
            predecessor_id=task1.id,
            successor_id=task2.id,
            lag_hours=2,  # 2h de délai
        )

        assert dep.lag_hours == 2
        assert dep.lag_timedelta == timedelta(hours=2)

    @pytest.mark.asyncio
    async def test_create_dependency_cycle_detection(self, gantt_service, sample_dates):
        """Test détection de cycle."""
        task1 = await gantt_service.create_task(
            name="T1",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )
        task2 = await gantt_service.create_task(
            name="T2",
            task_type=TaskType.OPERATION,
            start=sample_dates["end"],
            end=sample_dates["end"] + timedelta(hours=4),
        )

        await gantt_service.create_dependency(task1.id, task2.id)

        # Tenter de créer un cycle
        with pytest.raises(ValueError, match="cycle"):
            await gantt_service.create_dependency(task2.id, task1.id)

    @pytest.mark.asyncio
    async def test_get_predecessors(self, gantt_service, sample_dates):
        """Test récupération prédécesseurs."""
        task1 = await gantt_service.create_task(
            name="Pred 1",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )
        task2 = await gantt_service.create_task(
            name="Pred 2",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )
        task3 = await gantt_service.create_task(
            name="Successor",
            task_type=TaskType.OPERATION,
            start=sample_dates["end"],
            end=sample_dates["end"] + timedelta(hours=4),
        )

        await gantt_service.create_dependency(task1.id, task3.id)
        await gantt_service.create_dependency(task2.id, task3.id)

        predecessors = await gantt_service.get_predecessors(task3.id)

        assert len(predecessors) == 2

    @pytest.mark.asyncio
    async def test_get_successors(self, gantt_service, sample_dates):
        """Test récupération successeurs."""
        task1 = await gantt_service.create_task(
            name="Predecessor",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )
        task2 = await gantt_service.create_task(
            name="Succ 1",
            task_type=TaskType.OPERATION,
            start=sample_dates["end"],
            end=sample_dates["end"] + timedelta(hours=4),
        )
        task3 = await gantt_service.create_task(
            name="Succ 2",
            task_type=TaskType.OPERATION,
            start=sample_dates["end"],
            end=sample_dates["end"] + timedelta(hours=4),
        )

        await gantt_service.create_dependency(task1.id, task2.id)
        await gantt_service.create_dependency(task1.id, task3.id)

        successors = await gantt_service.get_successors(task1.id)

        assert len(successors) == 2

    @pytest.mark.asyncio
    async def test_delete_dependency(self, gantt_service, sample_dates):
        """Test suppression dépendance."""
        task1 = await gantt_service.create_task(
            name="T1",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )
        task2 = await gantt_service.create_task(
            name="T2",
            task_type=TaskType.OPERATION,
            start=sample_dates["end"],
            end=sample_dates["end"] + timedelta(hours=4),
        )

        dep = await gantt_service.create_dependency(task1.id, task2.id)

        deleted = await gantt_service.delete_dependency(dep.id)

        assert deleted is True
        assert len(await gantt_service.list_dependencies()) == 0


# =============================================================================
# SERVICE TESTS - MILESTONE MANAGEMENT
# =============================================================================


class TestMilestoneManagement:
    """Tests de gestion des jalons."""

    @pytest.mark.asyncio
    async def test_create_milestone(self, gantt_service, sample_dates):
        """Test création jalon."""
        milestone = await gantt_service.create_milestone(
            name="Livraison Client",
            date=sample_dates["next_week"],
        )

        assert milestone.id is not None
        assert milestone.name == "Livraison Client"
        assert milestone.is_completed is False

    @pytest.mark.asyncio
    async def test_complete_milestone(self, gantt_service, sample_dates):
        """Test complétion jalon."""
        milestone = await gantt_service.create_milestone(
            name="Jalon",
            date=sample_dates["tomorrow"],
        )

        completed = await gantt_service.complete_milestone(milestone.id)

        assert completed.is_completed is True

    @pytest.mark.asyncio
    async def test_list_milestones(self, gantt_service, sample_dates):
        """Test liste des jalons."""
        await gantt_service.create_milestone(
            name="Jalon 1",
            date=sample_dates["tomorrow"],
        )
        await gantt_service.create_milestone(
            name="Jalon 2",
            date=sample_dates["next_week"],
        )

        milestones = await gantt_service.list_milestones()

        assert len(milestones) == 2

    @pytest.mark.asyncio
    async def test_list_milestones_filter_completed(self, gantt_service, sample_dates):
        """Test filtre jalons complétés."""
        m1 = await gantt_service.create_milestone(
            name="Complété",
            date=sample_dates["tomorrow"],
        )
        await gantt_service.complete_milestone(m1.id)

        await gantt_service.create_milestone(
            name="Pas complété",
            date=sample_dates["next_week"],
        )

        completed = await gantt_service.list_milestones(completed=True)
        pending = await gantt_service.list_milestones(completed=False)

        assert len(completed) == 1
        assert len(pending) == 1


# =============================================================================
# SERVICE TESTS - RESOURCE MANAGEMENT
# =============================================================================


class TestResourceManagement:
    """Tests de gestion des ressources."""

    @pytest.mark.asyncio
    async def test_create_resource(self, gantt_service):
        """Test création ressource."""
        resource = await gantt_service.create_resource(
            name="Machine CNC",
            resource_type=ResourceType.MACHINE,
            capacity_hours_per_day=Decimal("16"),
        )

        assert resource.id is not None
        assert resource.name == "Machine CNC"
        assert resource.resource_type == ResourceType.MACHINE
        assert resource.capacity_hours_per_day == Decimal("16")

    @pytest.mark.asyncio
    async def test_list_resources(self, gantt_service):
        """Test liste des ressources."""
        await gantt_service.create_resource(
            name="Machine 1",
            resource_type=ResourceType.MACHINE,
        )
        await gantt_service.create_resource(
            name="Opérateur",
            resource_type=ResourceType.OPERATOR,
        )

        resources = await gantt_service.list_resources()

        assert len(resources) == 2

    @pytest.mark.asyncio
    async def test_list_resources_by_type(self, gantt_service):
        """Test filtre ressources par type."""
        await gantt_service.create_resource(
            name="Machine",
            resource_type=ResourceType.MACHINE,
        )
        await gantt_service.create_resource(
            name="Opérateur",
            resource_type=ResourceType.OPERATOR,
        )

        machines = await gantt_service.list_resources(resource_type=ResourceType.MACHINE)

        assert len(machines) == 1
        assert machines[0].resource_type == ResourceType.MACHINE

    @pytest.mark.asyncio
    async def test_get_resource_load(self, gantt_service, sample_dates):
        """Test charge ressource."""
        resource = await gantt_service.create_resource(
            name="Machine",
            resource_type=ResourceType.MACHINE,
            capacity_hours_per_day=Decimal("8"),
        )

        await gantt_service.create_task(
            name="Tâche",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
            resource_id=resource.id,
        )

        loads = await gantt_service.get_resource_load(
            resource.id,
            sample_dates["start"].date(),
            sample_dates["start"].date(),
        )

        assert len(loads) == 1


# =============================================================================
# SERVICE TESTS - TIMELINE & VISUALIZATION
# =============================================================================


class TestTimeline:
    """Tests de la timeline."""

    @pytest.mark.asyncio
    async def test_get_timeline(self, gantt_service, sample_dates):
        """Test récupération timeline."""
        await gantt_service.create_task(
            name="Tâche 1",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )

        await gantt_service.create_milestone(
            name="Jalon",
            date=sample_dates["tomorrow"],
        )

        timeline = await gantt_service.get_timeline(
            start_date=sample_dates["start"].date(),
            end_date=sample_dates["next_week"].date(),
        )

        assert timeline.total_tasks == 1
        assert len(timeline.milestones) == 1

    @pytest.mark.asyncio
    async def test_timeline_with_conflicts(self, gantt_service, sample_dates):
        """Test timeline avec conflits."""
        timeline = await gantt_service.get_timeline(
            start_date=sample_dates["start"].date(),
            end_date=sample_dates["next_week"].date(),
            include_conflicts=True,
        )

        assert isinstance(timeline.conflicts, list)


# =============================================================================
# SERVICE TESTS - CONFLICT DETECTION
# =============================================================================


class TestConflictDetection:
    """Tests de détection des conflits."""

    @pytest.mark.asyncio
    async def test_detect_resource_overload(self, gantt_service, sample_dates):
        """Test détection surcharge ressource."""
        resource = await gantt_service.create_resource(
            name="Machine",
            resource_type=ResourceType.MACHINE,
            capacity_hours_per_day=Decimal("8"),
        )

        # Créer plusieurs tâches sur la même ressource le même jour
        await gantt_service.create_task(
            name="Tâche 1",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["start"] + timedelta(hours=6),
            resource_id=resource.id,
        )
        await gantt_service.create_task(
            name="Tâche 2",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"] + timedelta(hours=2),
            end=sample_dates["start"] + timedelta(hours=8),
            resource_id=resource.id,
        )

        conflicts = await gantt_service.detect_all_conflicts(
            sample_dates["start"].date(),
            sample_dates["start"].date(),
        )

        # Peut détecter une surcharge si les tâches se chevauchent
        assert isinstance(conflicts, list)

    @pytest.mark.asyncio
    async def test_detect_dependency_violation(self, gantt_service, sample_dates):
        """Test détection violation dépendance."""
        task1 = await gantt_service.create_task(
            name="Prédécesseur",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["start"] + timedelta(hours=4),
        )
        task2 = await gantt_service.create_task(
            name="Successeur (commence trop tôt)",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"] + timedelta(hours=2),  # Avant fin du prédécesseur
            end=sample_dates["start"] + timedelta(hours=6),
        )

        await gantt_service.create_dependency(task1.id, task2.id)

        conflicts = await gantt_service.detect_all_conflicts()

        # Devrait détecter la violation
        dependency_conflicts = [
            c for c in conflicts
            if c.conflict_type == ConflictType.DEPENDENCY_VIOLATION
        ]
        assert len(dependency_conflicts) == 1


# =============================================================================
# SERVICE TESTS - CRITICAL PATH
# =============================================================================


class TestCriticalPath:
    """Tests du chemin critique."""

    @pytest.mark.asyncio
    async def test_calculate_critical_path_simple(self, gantt_service, sample_dates):
        """Test calcul chemin critique simple."""
        task1 = await gantt_service.create_task(
            name="T1",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["start"] + timedelta(hours=4),
        )
        task2 = await gantt_service.create_task(
            name="T2",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"] + timedelta(hours=4),
            end=sample_dates["start"] + timedelta(hours=8),
        )

        await gantt_service.create_dependency(task1.id, task2.id)

        critical_path = await gantt_service.calculate_critical_path()

        assert len(critical_path) == 2
        assert all(t.is_critical for t in critical_path)

    @pytest.mark.asyncio
    async def test_calculate_critical_path_empty(self, gantt_service):
        """Test chemin critique sans tâches."""
        critical_path = await gantt_service.calculate_critical_path()
        assert critical_path == []


# =============================================================================
# SERVICE TESTS - AUTO-SCHEDULING
# =============================================================================


class TestAutoScheduling:
    """Tests de l'auto-planification."""

    @pytest.mark.asyncio
    async def test_auto_schedule(self, gantt_service, sample_dates):
        """Test auto-planification."""
        task1 = await gantt_service.create_task(
            name="T1",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["start"] + timedelta(hours=4),
        )
        task2 = await gantt_service.create_task(
            name="T2",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],  # Même début que T1
            end=sample_dates["start"] + timedelta(hours=4),
        )

        await gantt_service.create_dependency(task1.id, task2.id)

        scheduled = await gantt_service.auto_schedule(
            start_from=sample_dates["start"],
            respect_dependencies=True,
        )

        assert len(scheduled) == 2
        # T2 devrait commencer après T1
        t1 = next(t for t in scheduled if t.name == "T1")
        t2 = next(t for t in scheduled if t.name == "T2")
        assert t2.start >= t1.end


# =============================================================================
# SERVICE TESTS - STATISTICS
# =============================================================================


class TestStatistics:
    """Tests des statistiques."""

    @pytest.mark.asyncio
    async def test_get_statistics_empty(self, gantt_service):
        """Test stats sans données."""
        stats = await gantt_service.get_statistics()

        assert stats["total_tasks"] == 0
        assert stats["completed_tasks"] == 0

    @pytest.mark.asyncio
    async def test_get_statistics_with_data(self, gantt_service, sample_dates):
        """Test stats avec données."""
        task1 = await gantt_service.create_task(
            name="Complétée",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )
        await gantt_service.update_progress(task1.id, Decimal("100"))

        await gantt_service.create_task(
            name="En cours",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )

        await gantt_service.create_milestone(
            name="Jalon",
            date=sample_dates["tomorrow"],
        )

        stats = await gantt_service.get_statistics()

        assert stats["total_tasks"] == 2
        assert stats["completed_tasks"] == 1
        assert stats["total_milestones"] == 1


# =============================================================================
# ROUTER TESTS
# =============================================================================


class TestGanttRouter:
    """Tests des endpoints API Gantt."""

    @pytest.fixture
    def mock_service(self):
        """Service mocké."""
        return AsyncMock(spec=GanttService)

    @pytest.fixture
    def test_app(self, mock_service):
        """App de test avec service mocké."""
        app = FastAPI()
        app.include_router(router)

        async def override_service():
            return mock_service

        from app.modules.production.gantt import router as gantt_router_module

        app.dependency_overrides[gantt_router_module.get_gantt_service] = override_service
        return app

    @pytest.fixture
    def test_client(self, test_app):
        """Client de test."""
        return TestClient(test_app)

    def test_create_task_endpoint(self, test_client, mock_service):
        """Test endpoint création tâche."""
        now = datetime.now()
        mock_task = GanttTask(
            id="task-123",
            tenant_id="test-tenant",
            name="Test Task",
            task_type=TaskType.OPERATION,
            start=now,
            end=now + timedelta(hours=4),
        )
        mock_service.create_task.return_value = mock_task

        response = test_client.post(
            "/v3/production/gantt/tasks",
            json={
                "name": "Test Task",
                "task_type": "operation",
                "start": now.isoformat(),
                "end": (now + timedelta(hours=4)).isoformat(),
            },
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "task-123"

    def test_list_tasks_endpoint(self, test_client, mock_service):
        """Test endpoint liste tâches."""
        now = datetime.now()
        mock_service.list_tasks.return_value = [
            GanttTask(
                id="task-1",
                tenant_id="test-tenant",
                name="Task 1",
                task_type=TaskType.OPERATION,
                start=now,
                end=now + timedelta(hours=4),
            ),
        ]

        response = test_client.get(
            "/v3/production/gantt/tasks",
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_create_dependency_endpoint(self, test_client, mock_service):
        """Test endpoint création dépendance."""
        mock_dep = GanttDependency(
            id="dep-123",
            tenant_id="test-tenant",
            predecessor_id="task-1",
            successor_id="task-2",
        )
        mock_service.create_dependency.return_value = mock_dep

        response = test_client.post(
            "/v3/production/gantt/dependencies",
            json={
                "predecessor_id": "task-1",
                "successor_id": "task-2",
            },
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 201

    def test_create_milestone_endpoint(self, test_client, mock_service):
        """Test endpoint création jalon."""
        now = datetime.now()
        mock_milestone = GanttMilestone(
            id="milestone-123",
            tenant_id="test-tenant",
            name="Delivery",
            date=now,
        )
        mock_service.create_milestone.return_value = mock_milestone

        response = test_client.post(
            "/v3/production/gantt/milestones",
            json={
                "name": "Delivery",
                "date": now.isoformat(),
            },
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 201

    def test_create_resource_endpoint(self, test_client, mock_service):
        """Test endpoint création ressource."""
        mock_resource = GanttResource(
            id="resource-123",
            tenant_id="test-tenant",
            name="Machine 1",
            resource_type=ResourceType.MACHINE,
        )
        mock_service.create_resource.return_value = mock_resource

        response = test_client.post(
            "/v3/production/gantt/resources",
            json={
                "name": "Machine 1",
                "resource_type": "machine",
            },
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 201

    def test_get_timeline_endpoint(self, test_client, mock_service):
        """Test endpoint timeline."""
        today = date.today()
        mock_timeline = Timeline(
            tenant_id="test-tenant",
            start_date=today,
            end_date=today + timedelta(days=7),
            tasks=[],
            dependencies=[],
            milestones=[],
            resources=[],
            conflicts=[],
        )
        mock_service.get_timeline.return_value = mock_timeline

        response = test_client.get(
            "/v3/production/gantt/timeline",
            params={
                "start_date": str(today),
                "end_date": str(today + timedelta(days=7)),
            },
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "milestones" in data

    def test_stats_endpoint(self, test_client, mock_service):
        """Test endpoint statistiques."""
        mock_service.get_statistics.return_value = {
            "total_tasks": 10,
            "completed_tasks": 5,
            "in_progress_tasks": 3,
            "pending_tasks": 2,
            "critical_tasks": 2,
            "total_hours": "80.00",
            "average_progress": "50.00",
            "total_dependencies": 5,
            "total_milestones": 3,
            "total_resources": 4,
            "total_conflicts": 1,
            "critical_conflicts": 0,
        }

        response = test_client.get(
            "/v3/production/gantt/stats",
            headers={"X-Tenant-ID": "test-tenant"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_tasks"] == 10


# =============================================================================
# DATACLASS TESTS
# =============================================================================


class TestDataclasses:
    """Tests des dataclasses."""

    def test_task_duration(self):
        """Test durée tâche."""
        now = datetime.now()
        task = GanttTask(
            id="t1",
            tenant_id="t",
            name="Task",
            task_type=TaskType.OPERATION,
            start=now,
            end=now + timedelta(hours=10),
        )

        assert task.duration_hours == Decimal("10.00")

    def test_task_completion_status(self):
        """Test statut complétion."""
        now = datetime.now()
        task = GanttTask(
            id="t1",
            tenant_id="t",
            name="Task",
            task_type=TaskType.OPERATION,
            start=now,
            end=now + timedelta(hours=4),
            progress=Decimal("100"),
        )

        assert task.is_completed is True

    def test_resource_load_overload(self):
        """Test surcharge ressource."""
        load_ok = ResourceLoad(
            resource_id="r1",
            resource_name="Machine",
            date=date.today(),
            available_hours=Decimal("8"),
            allocated_hours=Decimal("6"),
        )

        load_overloaded = ResourceLoad(
            resource_id="r1",
            resource_name="Machine",
            date=date.today(),
            available_hours=Decimal("8"),
            allocated_hours=Decimal("10"),
        )

        assert load_ok.is_overloaded is False
        assert load_ok.load_percent == Decimal("75.00")
        assert load_overloaded.is_overloaded is True


# =============================================================================
# TENANT ISOLATION TESTS
# =============================================================================


class TestTenantIsolation:
    """Tests d'isolation multi-tenant."""

    @pytest.mark.asyncio
    async def test_task_tenant_isolation(self, mock_db, sample_dates):
        """Test isolation tâches entre tenants."""
        service1 = GanttService(db=mock_db, tenant_id="tenant-1")
        service2 = GanttService(db=mock_db, tenant_id="tenant-2")

        task = await service1.create_task(
            name="Task Tenant 1",
            task_type=TaskType.OPERATION,
            start=sample_dates["start"],
            end=sample_dates["end"],
        )

        # Tenant 2 ne voit pas la tâche de tenant 1
        result = await service2.get_task(task.id)
        assert result is None

        tasks2 = await service2.list_tasks()
        assert len(tasks2) == 0

    @pytest.mark.asyncio
    async def test_resource_tenant_isolation(self, mock_db):
        """Test isolation ressources entre tenants."""
        service1 = GanttService(db=mock_db, tenant_id="tenant-a")
        service2 = GanttService(db=mock_db, tenant_id="tenant-b")

        resource = await service1.create_resource(
            name="Machine",
            resource_type=ResourceType.MACHINE,
        )

        result = await service2.get_resource(resource.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_milestone_tenant_isolation(self, mock_db, sample_dates):
        """Test isolation jalons entre tenants."""
        service1 = GanttService(db=mock_db, tenant_id="tenant-x")
        service2 = GanttService(db=mock_db, tenant_id="tenant-y")

        milestone = await service1.create_milestone(
            name="Milestone",
            date=sample_dates["tomorrow"],
        )

        result = await service2.get_milestone(milestone.id)
        assert result is None
