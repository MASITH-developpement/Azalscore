"""
AZALSCORE Gantt Production Service
===================================

Service pour la visualisation et gestion Gantt de production.

Fonctionnalités:
- Génération de timeline Gantt
- Gestion des dépendances entre tâches
- Jalons de production
- Allocation et charge des ressources
- Détection et résolution des conflits
- Optimisation du planning (earliest/latest start)
"""
from __future__ import annotations


import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class TaskType(str, Enum):
    """Type de tâche Gantt."""
    MANUFACTURING_ORDER = "manufacturing_order"
    OPERATION = "operation"
    MAINTENANCE = "maintenance"
    SETUP = "setup"
    QUALITY_CHECK = "quality_check"
    MILESTONE = "milestone"
    SUMMARY = "summary"


class DependencyType(str, Enum):
    """Type de dépendance."""
    FINISH_TO_START = "FS"  # Predecessor must finish before successor starts
    START_TO_START = "SS"   # Predecessor must start before successor starts
    FINISH_TO_FINISH = "FF"  # Predecessor must finish before successor finishes
    START_TO_FINISH = "SF"  # Predecessor must start before successor finishes


class ConflictType(str, Enum):
    """Type de conflit de planning."""
    RESOURCE_OVERLOAD = "resource_overload"
    DEPENDENCY_VIOLATION = "dependency_violation"
    DEADLINE_EXCEEDED = "deadline_exceeded"
    OVERLAP = "overlap"
    MISSING_RESOURCE = "missing_resource"


class ResourceType(str, Enum):
    """Type de ressource."""
    MACHINE = "machine"
    WORKSTATION = "workstation"
    OPERATOR = "operator"
    TOOL = "tool"


# =============================================================================
# DATACLASSES
# =============================================================================


@dataclass
class GanttResource:
    """Ressource pour le Gantt."""
    id: str
    tenant_id: str
    name: str
    resource_type: ResourceType
    capacity_hours_per_day: Decimal = Decimal("8")
    is_available: bool = True
    color: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class GanttTask:
    """Tâche Gantt."""
    id: str
    tenant_id: str
    name: str
    task_type: TaskType
    start: datetime
    end: datetime
    progress: Decimal = Decimal("0")  # 0-100
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    parent_id: Optional[str] = None
    order_id: Optional[str] = None
    order_number: Optional[str] = None
    color: Optional[str] = None
    is_critical: bool = False
    priority: int = 5
    notes: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @property
    def duration_hours(self) -> Decimal:
        """Durée en heures."""
        delta = self.end - self.start
        return Decimal(str(delta.total_seconds() / 3600)).quantize(Decimal("0.01"))

    @property
    def duration_days(self) -> Decimal:
        """Durée en jours."""
        delta = self.end - self.start
        return Decimal(str(delta.days + delta.seconds / 86400)).quantize(Decimal("0.01"))

    @property
    def is_completed(self) -> bool:
        """Vérifie si la tâche est complétée."""
        return self.progress >= Decimal("100")

    @property
    def is_started(self) -> bool:
        """Vérifie si la tâche est démarrée."""
        return self.progress > Decimal("0") or datetime.now() >= self.start


@dataclass
class GanttDependency:
    """Dépendance entre tâches."""
    id: str
    tenant_id: str
    predecessor_id: str
    successor_id: str
    dependency_type: DependencyType = DependencyType.FINISH_TO_START
    lag_hours: int = 0  # Délai entre les tâches (peut être négatif)

    @property
    def lag_timedelta(self) -> timedelta:
        """Convertit le lag en timedelta."""
        return timedelta(hours=self.lag_hours)


@dataclass
class GanttMilestone:
    """Jalon de production."""
    id: str
    tenant_id: str
    name: str
    date: datetime
    is_completed: bool = False
    related_task_ids: list[str] = field(default_factory=list)
    color: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class ResourceAllocation:
    """Allocation de ressource."""
    id: str
    tenant_id: str
    resource_id: str
    resource_name: str
    task_id: str
    task_name: str
    start: datetime
    end: datetime
    load_percent: Decimal = Decimal("100")


@dataclass
class ScheduleConflict:
    """Conflit de planning détecté."""
    id: str
    tenant_id: str
    conflict_type: ConflictType
    severity: int  # 1-10, 10 = critical
    description: str
    affected_task_ids: list[str] = field(default_factory=list)
    affected_resource_ids: list[str] = field(default_factory=list)
    suggested_resolution: Optional[str] = None
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class Timeline:
    """Timeline complète pour visualisation Gantt."""
    tenant_id: str
    start_date: date
    end_date: date
    tasks: list[GanttTask] = field(default_factory=list)
    dependencies: list[GanttDependency] = field(default_factory=list)
    milestones: list[GanttMilestone] = field(default_factory=list)
    resources: list[GanttResource] = field(default_factory=list)
    conflicts: list[ScheduleConflict] = field(default_factory=list)

    @property
    def total_tasks(self) -> int:
        """Nombre total de tâches."""
        return len(self.tasks)

    @property
    def critical_tasks(self) -> list[GanttTask]:
        """Tâches sur le chemin critique."""
        return [t for t in self.tasks if t.is_critical]

    @property
    def has_conflicts(self) -> bool:
        """Vérifie s'il y a des conflits."""
        return len(self.conflicts) > 0


@dataclass
class ResourceLoad:
    """Charge d'une ressource sur une période."""
    resource_id: str
    resource_name: str
    date: date
    available_hours: Decimal
    allocated_hours: Decimal
    tasks: list[str] = field(default_factory=list)

    @property
    def load_percent(self) -> Decimal:
        """Pourcentage de charge."""
        if self.available_hours == 0:
            return Decimal("0")
        return (self.allocated_hours / self.available_hours * 100).quantize(Decimal("0.01"))

    @property
    def is_overloaded(self) -> bool:
        """Vérifie si la ressource est surchargée."""
        return self.allocated_hours > self.available_hours


# =============================================================================
# SERVICE
# =============================================================================


class GanttService:
    """
    Service de gestion Gantt pour la production.

    Multi-tenant: OUI - Données isolées par tenant
    Fonctionnalités: Timeline, Dépendances, Jalons, Conflits
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
    ):
        if not tenant_id:
            raise ValueError("tenant_id est requis")

        self.db = db
        self.tenant_id = tenant_id
        self._tasks: dict[str, GanttTask] = {}
        self._dependencies: dict[str, GanttDependency] = {}
        self._milestones: dict[str, GanttMilestone] = {}
        self._resources: dict[str, GanttResource] = {}
        self._allocations: dict[str, ResourceAllocation] = {}

        logger.info(f"GanttService initialisé pour tenant {tenant_id}")

    # =========================================================================
    # TASK MANAGEMENT
    # =========================================================================

    async def create_task(
        self,
        name: str,
        task_type: TaskType,
        start: datetime,
        end: datetime,
        resource_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        order_id: Optional[str] = None,
        order_number: Optional[str] = None,
        priority: int = 5,
        color: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> GanttTask:
        """Crée une tâche Gantt."""
        if end <= start:
            raise ValueError("La date de fin doit être après la date de début")

        resource_name = None
        if resource_id and resource_id in self._resources:
            resource_name = self._resources[resource_id].name

        task = GanttTask(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            task_type=task_type,
            start=start,
            end=end,
            resource_id=resource_id,
            resource_name=resource_name,
            parent_id=parent_id,
            order_id=order_id,
            order_number=order_number,
            priority=priority,
            color=color,
            notes=notes,
        )

        self._tasks[task.id] = task

        # Auto-créer allocation si ressource spécifiée
        if resource_id:
            await self._create_allocation(task, resource_id)

        logger.info(f"Tâche Gantt créée: {name}")
        return task

    async def get_task(self, task_id: str) -> Optional[GanttTask]:
        """Récupère une tâche."""
        task = self._tasks.get(task_id)
        if task and task.tenant_id == self.tenant_id:
            return task
        return None

    async def update_task(
        self,
        task_id: str,
        name: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        progress: Optional[Decimal] = None,
        resource_id: Optional[str] = None,
        is_critical: Optional[bool] = None,
    ) -> Optional[GanttTask]:
        """Met à jour une tâche."""
        task = await self.get_task(task_id)
        if not task:
            return None

        if name is not None:
            task.name = name
        if start is not None:
            task.start = start
        if end is not None:
            task.end = end
        if progress is not None:
            task.progress = min(Decimal("100"), max(Decimal("0"), progress))
        if resource_id is not None:
            task.resource_id = resource_id
            if resource_id in self._resources:
                task.resource_name = self._resources[resource_id].name
        if is_critical is not None:
            task.is_critical = is_critical

        return task

    async def update_progress(
        self,
        task_id: str,
        progress: Decimal,
    ) -> Optional[GanttTask]:
        """Met à jour l'avancement d'une tâche."""
        return await self.update_task(task_id, progress=progress)

    async def delete_task(self, task_id: str) -> bool:
        """Supprime une tâche."""
        task = await self.get_task(task_id)
        if not task:
            return False

        # Supprimer les dépendances associées
        deps_to_remove = [
            d.id for d in self._dependencies.values()
            if d.predecessor_id == task_id or d.successor_id == task_id
        ]
        for dep_id in deps_to_remove:
            del self._dependencies[dep_id]

        # Supprimer les allocations associées
        allocs_to_remove = [
            a.id for a in self._allocations.values()
            if a.task_id == task_id
        ]
        for alloc_id in allocs_to_remove:
            del self._allocations[alloc_id]

        del self._tasks[task_id]
        return True

    async def list_tasks(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        resource_id: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        order_id: Optional[str] = None,
    ) -> list[GanttTask]:
        """Liste les tâches avec filtres."""
        tasks = [t for t in self._tasks.values() if t.tenant_id == self.tenant_id]

        if start_date:
            tasks = [t for t in tasks if t.end.date() >= start_date]
        if end_date:
            tasks = [t for t in tasks if t.start.date() <= end_date]
        if resource_id:
            tasks = [t for t in tasks if t.resource_id == resource_id]
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        if order_id:
            tasks = [t for t in tasks if t.order_id == order_id]

        return sorted(tasks, key=lambda t: (t.start, t.priority))

    # =========================================================================
    # DEPENDENCY MANAGEMENT
    # =========================================================================

    async def create_dependency(
        self,
        predecessor_id: str,
        successor_id: str,
        dependency_type: DependencyType = DependencyType.FINISH_TO_START,
        lag_hours: int = 0,
    ) -> Optional[GanttDependency]:
        """Crée une dépendance entre deux tâches."""
        # Vérifier que les tâches existent
        predecessor = await self.get_task(predecessor_id)
        successor = await self.get_task(successor_id)

        if not predecessor or not successor:
            return None

        # Vérifier pas de cycle
        if await self._would_create_cycle(predecessor_id, successor_id):
            raise ValueError("Cette dépendance créerait un cycle")

        dependency = GanttDependency(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            predecessor_id=predecessor_id,
            successor_id=successor_id,
            dependency_type=dependency_type,
            lag_hours=lag_hours,
        )

        self._dependencies[dependency.id] = dependency

        logger.info(f"Dépendance créée: {predecessor.name} -> {successor.name}")
        return dependency

    async def _would_create_cycle(
        self,
        predecessor_id: str,
        successor_id: str,
    ) -> bool:
        """Vérifie si ajouter cette dépendance créerait un cycle."""
        visited = set()

        def has_path_to(current_id: str, target_id: str) -> bool:
            if current_id == target_id:
                return True
            if current_id in visited:
                return False
            visited.add(current_id)

            for dep in self._dependencies.values():
                if dep.predecessor_id == current_id:
                    if has_path_to(dep.successor_id, target_id):
                        return True
            return False

        # Vérifie si successor peut atteindre predecessor (cycle)
        return has_path_to(successor_id, predecessor_id)

    async def delete_dependency(self, dependency_id: str) -> bool:
        """Supprime une dépendance."""
        dep = self._dependencies.get(dependency_id)
        if dep and dep.tenant_id == self.tenant_id:
            del self._dependencies[dependency_id]
            return True
        return False

    async def get_predecessors(self, task_id: str) -> list[GanttTask]:
        """Récupère les prédécesseurs d'une tâche."""
        predecessor_ids = [
            d.predecessor_id
            for d in self._dependencies.values()
            if d.successor_id == task_id and d.tenant_id == self.tenant_id
        ]
        return [self._tasks[pid] for pid in predecessor_ids if pid in self._tasks]

    async def get_successors(self, task_id: str) -> list[GanttTask]:
        """Récupère les successeurs d'une tâche."""
        successor_ids = [
            d.successor_id
            for d in self._dependencies.values()
            if d.predecessor_id == task_id and d.tenant_id == self.tenant_id
        ]
        return [self._tasks[sid] for sid in successor_ids if sid in self._tasks]

    async def list_dependencies(
        self,
        task_id: Optional[str] = None,
    ) -> list[GanttDependency]:
        """Liste les dépendances."""
        deps = [d for d in self._dependencies.values() if d.tenant_id == self.tenant_id]

        if task_id:
            deps = [
                d for d in deps
                if d.predecessor_id == task_id or d.successor_id == task_id
            ]

        return deps

    # =========================================================================
    # MILESTONE MANAGEMENT
    # =========================================================================

    async def create_milestone(
        self,
        name: str,
        date: datetime,
        related_task_ids: Optional[list[str]] = None,
        color: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> GanttMilestone:
        """Crée un jalon."""
        milestone = GanttMilestone(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            date=date,
            related_task_ids=related_task_ids or [],
            color=color,
            notes=notes,
        )

        self._milestones[milestone.id] = milestone

        logger.info(f"Jalon créé: {name}")
        return milestone

    async def get_milestone(self, milestone_id: str) -> Optional[GanttMilestone]:
        """Récupère un jalon."""
        milestone = self._milestones.get(milestone_id)
        if milestone and milestone.tenant_id == self.tenant_id:
            return milestone
        return None

    async def complete_milestone(self, milestone_id: str) -> Optional[GanttMilestone]:
        """Marque un jalon comme complété."""
        milestone = await self.get_milestone(milestone_id)
        if milestone:
            milestone.is_completed = True
            return milestone
        return None

    async def list_milestones(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        completed: Optional[bool] = None,
    ) -> list[GanttMilestone]:
        """Liste les jalons."""
        milestones = [m for m in self._milestones.values() if m.tenant_id == self.tenant_id]

        if start_date:
            milestones = [m for m in milestones if m.date.date() >= start_date]
        if end_date:
            milestones = [m for m in milestones if m.date.date() <= end_date]
        if completed is not None:
            milestones = [m for m in milestones if m.is_completed == completed]

        return sorted(milestones, key=lambda m: m.date)

    # =========================================================================
    # RESOURCE MANAGEMENT
    # =========================================================================

    async def create_resource(
        self,
        name: str,
        resource_type: ResourceType,
        capacity_hours_per_day: Decimal = Decimal("8"),
        color: Optional[str] = None,
    ) -> GanttResource:
        """Crée une ressource."""
        resource = GanttResource(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            resource_type=resource_type,
            capacity_hours_per_day=capacity_hours_per_day,
            color=color,
        )

        self._resources[resource.id] = resource

        logger.info(f"Ressource créée: {name}")
        return resource

    async def get_resource(self, resource_id: str) -> Optional[GanttResource]:
        """Récupère une ressource."""
        resource = self._resources.get(resource_id)
        if resource and resource.tenant_id == self.tenant_id:
            return resource
        return None

    async def list_resources(
        self,
        resource_type: Optional[ResourceType] = None,
        available_only: bool = False,
    ) -> list[GanttResource]:
        """Liste les ressources."""
        resources = [r for r in self._resources.values() if r.tenant_id == self.tenant_id]

        if resource_type:
            resources = [r for r in resources if r.resource_type == resource_type]
        if available_only:
            resources = [r for r in resources if r.is_available]

        return sorted(resources, key=lambda r: r.name)

    async def _create_allocation(
        self,
        task: GanttTask,
        resource_id: str,
    ) -> ResourceAllocation:
        """Crée une allocation de ressource."""
        resource = self._resources.get(resource_id)
        resource_name = resource.name if resource else "Unknown"

        allocation = ResourceAllocation(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            resource_id=resource_id,
            resource_name=resource_name,
            task_id=task.id,
            task_name=task.name,
            start=task.start,
            end=task.end,
        )

        self._allocations[allocation.id] = allocation
        return allocation

    # =========================================================================
    # TIMELINE & VISUALIZATION
    # =========================================================================

    async def get_timeline(
        self,
        start_date: date,
        end_date: date,
        resource_id: Optional[str] = None,
        include_conflicts: bool = True,
    ) -> Timeline:
        """Génère la timeline complète pour visualisation Gantt."""
        tasks = await self.list_tasks(
            start_date=start_date,
            end_date=end_date,
            resource_id=resource_id,
        )

        # Récupérer les IDs des tâches dans la timeline
        task_ids = {t.id for t in tasks}

        # Dépendances pertinentes
        dependencies = [
            d for d in self._dependencies.values()
            if d.tenant_id == self.tenant_id
            and (d.predecessor_id in task_ids or d.successor_id in task_ids)
        ]

        # Jalons
        milestones = await self.list_milestones(
            start_date=start_date,
            end_date=end_date,
        )

        # Ressources
        resources = await self.list_resources()

        # Conflits
        conflicts = []
        if include_conflicts:
            conflicts = await self.detect_all_conflicts(start_date, end_date)

        return Timeline(
            tenant_id=self.tenant_id,
            start_date=start_date,
            end_date=end_date,
            tasks=tasks,
            dependencies=dependencies,
            milestones=milestones,
            resources=resources,
            conflicts=conflicts,
        )

    async def get_resource_load(
        self,
        resource_id: str,
        start_date: date,
        end_date: date,
    ) -> list[ResourceLoad]:
        """Calcule la charge d'une ressource jour par jour."""
        resource = await self.get_resource(resource_id)
        if not resource:
            return []

        loads = []
        current = start_date

        while current <= end_date:
            # Tâches du jour pour cette ressource
            day_tasks = [
                t for t in self._tasks.values()
                if t.tenant_id == self.tenant_id
                and t.resource_id == resource_id
                and t.start.date() <= current <= t.end.date()
            ]

            # Calculer les heures allouées
            allocated = Decimal("0")
            task_ids = []

            for task in day_tasks:
                # Portion de la tâche sur ce jour
                task_start = max(task.start.date(), current)
                task_end = min(task.end.date(), current)

                if task.duration_days > 0:
                    daily_hours = task.duration_hours / task.duration_days
                else:
                    daily_hours = task.duration_hours

                allocated += min(daily_hours, resource.capacity_hours_per_day)
                task_ids.append(task.id)

            loads.append(ResourceLoad(
                resource_id=resource_id,
                resource_name=resource.name,
                date=current,
                available_hours=resource.capacity_hours_per_day,
                allocated_hours=allocated,
                tasks=task_ids,
            ))

            current += timedelta(days=1)

        return loads

    # =========================================================================
    # CONFLICT DETECTION
    # =========================================================================

    async def detect_all_conflicts(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[ScheduleConflict]:
        """Détecte tous les conflits de planning."""
        conflicts = []

        # Conflits de ressources
        conflicts.extend(await self._detect_resource_conflicts(start_date, end_date))

        # Conflits de dépendances
        conflicts.extend(await self._detect_dependency_conflicts())

        # Conflits de deadline
        conflicts.extend(await self._detect_deadline_conflicts(end_date))

        return conflicts

    async def _detect_resource_conflicts(
        self,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> list[ScheduleConflict]:
        """Détecte les surcharges de ressources."""
        conflicts = []

        for resource in self._resources.values():
            if resource.tenant_id != self.tenant_id:
                continue

            # Vérifier la charge
            sd = start_date or date.today()
            ed = end_date or (date.today() + timedelta(days=30))

            loads = await self.get_resource_load(resource.id, sd, ed)

            for load in loads:
                if load.is_overloaded:
                    conflicts.append(ScheduleConflict(
                        id=str(uuid.uuid4()),
                        tenant_id=self.tenant_id,
                        conflict_type=ConflictType.RESOURCE_OVERLOAD,
                        severity=7,
                        description=(
                            f"Ressource {resource.name} surchargée le {load.date}: "
                            f"{load.allocated_hours}h / {load.available_hours}h disponibles"
                        ),
                        affected_task_ids=load.tasks,
                        affected_resource_ids=[resource.id],
                        suggested_resolution="Redistribuer les tâches ou augmenter la capacité",
                    ))

        return conflicts

    async def _detect_dependency_conflicts(self) -> list[ScheduleConflict]:
        """Détecte les violations de dépendances."""
        conflicts = []

        for dep in self._dependencies.values():
            if dep.tenant_id != self.tenant_id:
                continue

            pred = self._tasks.get(dep.predecessor_id)
            succ = self._tasks.get(dep.successor_id)

            if not pred or not succ:
                continue

            violation = False
            expected_start = None

            if dep.dependency_type == DependencyType.FINISH_TO_START:
                expected_start = pred.end + dep.lag_timedelta
                violation = succ.start < expected_start

            elif dep.dependency_type == DependencyType.START_TO_START:
                expected_start = pred.start + dep.lag_timedelta
                violation = succ.start < expected_start

            elif dep.dependency_type == DependencyType.FINISH_TO_FINISH:
                expected_end = pred.end + dep.lag_timedelta
                violation = succ.end < expected_end

            elif dep.dependency_type == DependencyType.START_TO_FINISH:
                expected_end = pred.start + dep.lag_timedelta
                violation = succ.end < expected_end

            if violation:
                conflicts.append(ScheduleConflict(
                    id=str(uuid.uuid4()),
                    tenant_id=self.tenant_id,
                    conflict_type=ConflictType.DEPENDENCY_VIOLATION,
                    severity=8,
                    description=(
                        f"Violation de dépendance {dep.dependency_type.value}: "
                        f"'{succ.name}' commence avant que '{pred.name}' soit terminé"
                    ),
                    affected_task_ids=[pred.id, succ.id],
                    suggested_resolution=f"Décaler '{succ.name}' après {expected_start}",
                ))

        return conflicts

    async def _detect_deadline_conflicts(
        self,
        deadline: Optional[date],
    ) -> list[ScheduleConflict]:
        """Détecte les dépassements de deadline."""
        if not deadline:
            return []

        conflicts = []

        for task in self._tasks.values():
            if task.tenant_id != self.tenant_id:
                continue

            if task.end.date() > deadline:
                conflicts.append(ScheduleConflict(
                    id=str(uuid.uuid4()),
                    tenant_id=self.tenant_id,
                    conflict_type=ConflictType.DEADLINE_EXCEEDED,
                    severity=9,
                    description=(
                        f"Tâche '{task.name}' dépasse la deadline: "
                        f"fin prévue {task.end.date()} vs deadline {deadline}"
                    ),
                    affected_task_ids=[task.id],
                    suggested_resolution="Réduire la durée ou augmenter les ressources",
                ))

        return conflicts

    # =========================================================================
    # SCHEDULING OPTIMIZATION
    # =========================================================================

    async def calculate_critical_path(self) -> list[GanttTask]:
        """Calcule le chemin critique."""
        tasks = [t for t in self._tasks.values() if t.tenant_id == self.tenant_id]

        if not tasks:
            return []

        # Trouver les tâches sans successeurs (fins)
        end_tasks = []
        for task in tasks:
            successors = await self.get_successors(task.id)
            if not successors:
                end_tasks.append(task)

        if not end_tasks:
            # Pas de dépendances, prendre la tâche la plus longue
            return sorted(tasks, key=lambda t: t.duration_hours, reverse=True)[:1]

        # Trouver le chemin le plus long
        critical_path = []
        latest_end = max(t.end for t in end_tasks)

        def find_path(task: GanttTask, path: list) -> list:
            current_path = path + [task]
            predecessors = [
                self._tasks.get(d.predecessor_id)
                for d in self._dependencies.values()
                if d.successor_id == task.id
            ]
            predecessors = [p for p in predecessors if p]

            if not predecessors:
                return current_path

            # Prendre le chemin le plus long parmi les prédécesseurs
            longest = current_path
            for pred in predecessors:
                candidate = find_path(pred, current_path)
                if len(candidate) > len(longest):
                    longest = candidate

            return longest

        for end_task in end_tasks:
            if end_task.end == latest_end:
                path = find_path(end_task, [])
                if len(path) > len(critical_path):
                    critical_path = path

        # Marquer les tâches comme critiques
        for task in critical_path:
            task.is_critical = True

        return list(reversed(critical_path))

    async def auto_schedule(
        self,
        start_from: datetime,
        respect_dependencies: bool = True,
    ) -> list[GanttTask]:
        """Planifie automatiquement les tâches."""
        tasks = [t for t in self._tasks.values() if t.tenant_id == self.tenant_id]

        if not tasks or not respect_dependencies:
            return tasks

        # Trier par dépendances (topological sort)
        scheduled = []
        remaining = list(tasks)

        while remaining:
            # Trouver les tâches sans prédécesseurs non planifiés
            for task in remaining[:]:
                predecessors = await self.get_predecessors(task.id)
                unscheduled_preds = [p for p in predecessors if p not in scheduled]

                if not unscheduled_preds:
                    # Calculer le début au plus tôt
                    earliest_start = start_from
                    for pred in predecessors:
                        dep = next(
                            (d for d in self._dependencies.values()
                             if d.predecessor_id == pred.id and d.successor_id == task.id),
                            None
                        )
                        if dep and dep.dependency_type == DependencyType.FINISH_TO_START:
                            earliest = pred.end + dep.lag_timedelta
                            if earliest > earliest_start:
                                earliest_start = earliest

                    # Ajuster les dates
                    duration = task.end - task.start
                    task.start = earliest_start
                    task.end = earliest_start + duration

                    scheduled.append(task)
                    remaining.remove(task)
                    break
            else:
                # Cycle détecté ou erreur
                break

        return scheduled

    # =========================================================================
    # STATISTICS
    # =========================================================================

    async def get_statistics(self) -> dict:
        """Statistiques du planning Gantt."""
        tasks = [t for t in self._tasks.values() if t.tenant_id == self.tenant_id]

        total = len(tasks)
        completed = len([t for t in tasks if t.is_completed])
        in_progress = len([t for t in tasks if t.is_started and not t.is_completed])
        critical = len([t for t in tasks if t.is_critical])

        # Calculs de durée
        total_hours = sum(t.duration_hours for t in tasks)
        avg_progress = Decimal("0")
        if tasks:
            avg_progress = sum(t.progress for t in tasks) / len(tasks)

        # Conflits
        conflicts = await self.detect_all_conflicts()

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "in_progress_tasks": in_progress,
            "pending_tasks": total - completed - in_progress,
            "critical_tasks": critical,
            "total_hours": str(total_hours),
            "average_progress": str(avg_progress.quantize(Decimal("0.01"))),
            "total_dependencies": len([
                d for d in self._dependencies.values()
                if d.tenant_id == self.tenant_id
            ]),
            "total_milestones": len([
                m for m in self._milestones.values()
                if m.tenant_id == self.tenant_id
            ]),
            "total_resources": len([
                r for r in self._resources.values()
                if r.tenant_id == self.tenant_id
            ]),
            "total_conflicts": len(conflicts),
            "critical_conflicts": len([c for c in conflicts if c.severity >= 8]),
        }
