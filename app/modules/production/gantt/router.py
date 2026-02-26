"""
AZALSCORE Gantt Production Router V3
=====================================

Endpoints REST pour la visualisation Gantt de production.

Endpoints Tasks:
- GET  /v3/production/gantt/tasks - Liste tâches
- POST /v3/production/gantt/tasks - Créer tâche
- GET  /v3/production/gantt/tasks/{id} - Détails tâche
- PUT  /v3/production/gantt/tasks/{id} - Modifier tâche
- PATCH /v3/production/gantt/tasks/{id}/progress - Maj avancement
- DELETE /v3/production/gantt/tasks/{id} - Supprimer tâche

Endpoints Dependencies:
- GET  /v3/production/gantt/dependencies - Liste dépendances
- POST /v3/production/gantt/dependencies - Créer dépendance
- DELETE /v3/production/gantt/dependencies/{id} - Supprimer

Endpoints Milestones:
- GET  /v3/production/gantt/milestones - Liste jalons
- POST /v3/production/gantt/milestones - Créer jalon
- POST /v3/production/gantt/milestones/{id}/complete - Compléter

Endpoints Resources:
- GET  /v3/production/gantt/resources - Liste ressources
- POST /v3/production/gantt/resources - Créer ressource
- GET  /v3/production/gantt/resources/{id}/load - Charge ressource

Endpoints Timeline:
- GET  /v3/production/gantt/timeline - Timeline complète
- GET  /v3/production/gantt/conflicts - Conflits détectés
- POST /v3/production/gantt/schedule - Auto-planification
- GET  /v3/production/gantt/critical-path - Chemin critique
- GET  /v3/production/gantt/stats - Statistiques
"""
from __future__ import annotations


import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.saas_context import SaaSContext
from app.core.dependencies_v2 import get_saas_context

from .service import (
    GanttService,
    GanttTask,
    GanttDependency,
    GanttMilestone,
    GanttResource,
    TaskType,
    DependencyType,
    ResourceType,
    ConflictType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v3/production/gantt", tags=["Production Gantt"])


# =============================================================================
# SCHEMAS
# =============================================================================


class CreateTaskRequest(BaseModel):
    """Requête création tâche."""
    name: str
    task_type: TaskType
    start: datetime
    end: datetime
    resource_id: Optional[str] = None
    parent_id: Optional[str] = None
    order_id: Optional[str] = None
    order_number: Optional[str] = None
    priority: int = Field(5, ge=1, le=10)
    color: Optional[str] = None
    notes: Optional[str] = None


class UpdateTaskRequest(BaseModel):
    """Requête modification tâche."""
    name: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    progress: Optional[Decimal] = Field(None, ge=0, le=100)
    resource_id: Optional[str] = None
    is_critical: Optional[bool] = None


class UpdateProgressRequest(BaseModel):
    """Requête mise à jour avancement."""
    progress: Decimal = Field(..., ge=0, le=100)


class TaskResponse(BaseModel):
    """Réponse tâche."""
    id: str
    name: str
    task_type: str
    start: str
    end: str
    duration_hours: Decimal
    progress: Decimal
    resource_id: Optional[str]
    resource_name: Optional[str]
    parent_id: Optional[str]
    order_id: Optional[str]
    order_number: Optional[str]
    color: Optional[str]
    is_critical: bool
    priority: int
    is_completed: bool
    is_started: bool


class CreateDependencyRequest(BaseModel):
    """Requête création dépendance."""
    predecessor_id: str
    successor_id: str
    dependency_type: DependencyType = DependencyType.FINISH_TO_START
    lag_hours: int = Field(0, ge=-168, le=168)  # +/- 1 semaine


class DependencyResponse(BaseModel):
    """Réponse dépendance."""
    id: str
    predecessor_id: str
    successor_id: str
    dependency_type: str
    lag_hours: int


class CreateMilestoneRequest(BaseModel):
    """Requête création jalon."""
    name: str
    date: datetime
    related_task_ids: Optional[list[str]] = None
    color: Optional[str] = None
    notes: Optional[str] = None


class MilestoneResponse(BaseModel):
    """Réponse jalon."""
    id: str
    name: str
    date: str
    is_completed: bool
    related_task_ids: list[str]
    color: Optional[str]
    notes: Optional[str]


class CreateResourceRequest(BaseModel):
    """Requête création ressource."""
    name: str
    resource_type: ResourceType
    capacity_hours_per_day: Decimal = Field(Decimal("8"), gt=0, le=24)
    color: Optional[str] = None


class ResourceResponse(BaseModel):
    """Réponse ressource."""
    id: str
    name: str
    resource_type: str
    capacity_hours_per_day: Decimal
    is_available: bool
    color: Optional[str]


class ResourceLoadResponse(BaseModel):
    """Réponse charge ressource."""
    resource_id: str
    resource_name: str
    date: str
    available_hours: Decimal
    allocated_hours: Decimal
    load_percent: Decimal
    is_overloaded: bool
    tasks: list[str]


class ConflictResponse(BaseModel):
    """Réponse conflit."""
    id: str
    conflict_type: str
    severity: int
    description: str
    affected_task_ids: list[str]
    affected_resource_ids: list[str]
    suggested_resolution: Optional[str]


class TimelineResponse(BaseModel):
    """Réponse timeline complète."""
    start_date: str
    end_date: str
    total_tasks: int
    tasks: list[TaskResponse]
    dependencies: list[DependencyResponse]
    milestones: list[MilestoneResponse]
    resources: list[ResourceResponse]
    conflicts: list[ConflictResponse]
    has_conflicts: bool


class AutoScheduleRequest(BaseModel):
    """Requête auto-planification."""
    start_from: datetime
    respect_dependencies: bool = True


# =============================================================================
# DEPENDENCIES
# =============================================================================


def get_gantt_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
) -> GanttService:
    """Dépendance pour obtenir le service Gantt."""
    return GanttService(db=db, tenant_id=context.tenant_id)


# =============================================================================
# HELPERS
# =============================================================================


def task_to_response(task: GanttTask) -> TaskResponse:
    """Convertit une tâche en réponse."""
    return TaskResponse(
        id=task.id,
        name=task.name,
        task_type=task.task_type.value,
        start=task.start.isoformat(),
        end=task.end.isoformat(),
        duration_hours=task.duration_hours,
        progress=task.progress,
        resource_id=task.resource_id,
        resource_name=task.resource_name,
        parent_id=task.parent_id,
        order_id=task.order_id,
        order_number=task.order_number,
        color=task.color,
        is_critical=task.is_critical,
        priority=task.priority,
        is_completed=task.is_completed,
        is_started=task.is_started,
    )


def dependency_to_response(dep: GanttDependency) -> DependencyResponse:
    """Convertit une dépendance en réponse."""
    return DependencyResponse(
        id=dep.id,
        predecessor_id=dep.predecessor_id,
        successor_id=dep.successor_id,
        dependency_type=dep.dependency_type.value,
        lag_hours=dep.lag_hours,
    )


def milestone_to_response(milestone: GanttMilestone) -> MilestoneResponse:
    """Convertit un jalon en réponse."""
    return MilestoneResponse(
        id=milestone.id,
        name=milestone.name,
        date=milestone.date.isoformat(),
        is_completed=milestone.is_completed,
        related_task_ids=milestone.related_task_ids,
        color=milestone.color,
        notes=milestone.notes,
    )


def resource_to_response(resource: GanttResource) -> ResourceResponse:
    """Convertit une ressource en réponse."""
    return ResourceResponse(
        id=resource.id,
        name=resource.name,
        resource_type=resource.resource_type.value,
        capacity_hours_per_day=resource.capacity_hours_per_day,
        is_available=resource.is_available,
        color=resource.color,
    )


# =============================================================================
# ENDPOINTS - TASKS
# =============================================================================


@router.get(
    "/tasks",
    response_model=list[TaskResponse],
    summary="Liste des tâches Gantt",
)
async def list_tasks(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    resource_id: Optional[str] = Query(None),
    task_type: Optional[TaskType] = Query(None),
    order_id: Optional[str] = Query(None),
    service: GanttService = Depends(get_gantt_service),
):
    """Liste les tâches Gantt avec filtres."""
    tasks = await service.list_tasks(
        start_date=start_date,
        end_date=end_date,
        resource_id=resource_id,
        task_type=task_type,
        order_id=order_id,
    )
    return [task_to_response(t) for t in tasks]


@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une tâche Gantt",
)
async def create_task(
    request: CreateTaskRequest,
    service: GanttService = Depends(get_gantt_service),
):
    """Crée une nouvelle tâche Gantt."""
    try:
        task = await service.create_task(
            name=request.name,
            task_type=request.task_type,
            start=request.start,
            end=request.end,
            resource_id=request.resource_id,
            parent_id=request.parent_id,
            order_id=request.order_id,
            order_number=request.order_number,
            priority=request.priority,
            color=request.color,
            notes=request.notes,
        )
        return task_to_response(task)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Détails d'une tâche",
)
async def get_task(
    task_id: str,
    service: GanttService = Depends(get_gantt_service),
):
    """Récupère les détails d'une tâche."""
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    return task_to_response(task)


@router.put(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Modifier une tâche",
)
async def update_task(
    task_id: str,
    request: UpdateTaskRequest,
    service: GanttService = Depends(get_gantt_service),
):
    """Modifie une tâche Gantt."""
    task = await service.update_task(
        task_id=task_id,
        name=request.name,
        start=request.start,
        end=request.end,
        progress=request.progress,
        resource_id=request.resource_id,
        is_critical=request.is_critical,
    )
    if not task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    return task_to_response(task)


@router.patch(
    "/tasks/{task_id}/progress",
    response_model=TaskResponse,
    summary="Mettre à jour l'avancement",
)
async def update_task_progress(
    task_id: str,
    request: UpdateProgressRequest,
    service: GanttService = Depends(get_gantt_service),
):
    """Met à jour l'avancement d'une tâche."""
    task = await service.update_progress(task_id, request.progress)
    if not task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    return task_to_response(task)


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une tâche",
)
async def delete_task(
    task_id: str,
    service: GanttService = Depends(get_gantt_service),
):
    """Supprime une tâche Gantt."""
    deleted = await service.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")


# =============================================================================
# ENDPOINTS - DEPENDENCIES
# =============================================================================


@router.get(
    "/dependencies",
    response_model=list[DependencyResponse],
    summary="Liste des dépendances",
)
async def list_dependencies(
    task_id: Optional[str] = Query(None),
    service: GanttService = Depends(get_gantt_service),
):
    """Liste les dépendances entre tâches."""
    deps = await service.list_dependencies(task_id=task_id)
    return [dependency_to_response(d) for d in deps]


@router.post(
    "/dependencies",
    response_model=DependencyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une dépendance",
)
async def create_dependency(
    request: CreateDependencyRequest,
    service: GanttService = Depends(get_gantt_service),
):
    """Crée une dépendance entre deux tâches."""
    try:
        dep = await service.create_dependency(
            predecessor_id=request.predecessor_id,
            successor_id=request.successor_id,
            dependency_type=request.dependency_type,
            lag_hours=request.lag_hours,
        )
        if not dep:
            raise HTTPException(status_code=404, detail="Tâche(s) non trouvée(s)")
        return dependency_to_response(dep)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/dependencies/{dependency_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une dépendance",
)
async def delete_dependency(
    dependency_id: str,
    service: GanttService = Depends(get_gantt_service),
):
    """Supprime une dépendance."""
    deleted = await service.delete_dependency(dependency_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Dépendance non trouvée")


@router.get(
    "/tasks/{task_id}/predecessors",
    response_model=list[TaskResponse],
    summary="Prédécesseurs d'une tâche",
)
async def get_predecessors(
    task_id: str,
    service: GanttService = Depends(get_gantt_service),
):
    """Récupère les prédécesseurs d'une tâche."""
    predecessors = await service.get_predecessors(task_id)
    return [task_to_response(t) for t in predecessors]


@router.get(
    "/tasks/{task_id}/successors",
    response_model=list[TaskResponse],
    summary="Successeurs d'une tâche",
)
async def get_successors(
    task_id: str,
    service: GanttService = Depends(get_gantt_service),
):
    """Récupère les successeurs d'une tâche."""
    successors = await service.get_successors(task_id)
    return [task_to_response(t) for t in successors]


# =============================================================================
# ENDPOINTS - MILESTONES
# =============================================================================


@router.get(
    "/milestones",
    response_model=list[MilestoneResponse],
    summary="Liste des jalons",
)
async def list_milestones(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    completed: Optional[bool] = Query(None),
    service: GanttService = Depends(get_gantt_service),
):
    """Liste les jalons de production."""
    milestones = await service.list_milestones(
        start_date=start_date,
        end_date=end_date,
        completed=completed,
    )
    return [milestone_to_response(m) for m in milestones]


@router.post(
    "/milestones",
    response_model=MilestoneResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un jalon",
)
async def create_milestone(
    request: CreateMilestoneRequest,
    service: GanttService = Depends(get_gantt_service),
):
    """Crée un nouveau jalon."""
    milestone = await service.create_milestone(
        name=request.name,
        date=request.date,
        related_task_ids=request.related_task_ids,
        color=request.color,
        notes=request.notes,
    )
    return milestone_to_response(milestone)


@router.get(
    "/milestones/{milestone_id}",
    response_model=MilestoneResponse,
    summary="Détails d'un jalon",
)
async def get_milestone(
    milestone_id: str,
    service: GanttService = Depends(get_gantt_service),
):
    """Récupère les détails d'un jalon."""
    milestone = await service.get_milestone(milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Jalon non trouvé")
    return milestone_to_response(milestone)


@router.post(
    "/milestones/{milestone_id}/complete",
    response_model=MilestoneResponse,
    summary="Marquer un jalon comme complété",
)
async def complete_milestone(
    milestone_id: str,
    service: GanttService = Depends(get_gantt_service),
):
    """Marque un jalon comme complété."""
    milestone = await service.complete_milestone(milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Jalon non trouvé")
    return milestone_to_response(milestone)


# =============================================================================
# ENDPOINTS - RESOURCES
# =============================================================================


@router.get(
    "/resources",
    response_model=list[ResourceResponse],
    summary="Liste des ressources",
)
async def list_resources(
    resource_type: Optional[ResourceType] = Query(None),
    available_only: bool = Query(False),
    service: GanttService = Depends(get_gantt_service),
):
    """Liste les ressources."""
    resources = await service.list_resources(
        resource_type=resource_type,
        available_only=available_only,
    )
    return [resource_to_response(r) for r in resources]


@router.post(
    "/resources",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une ressource",
)
async def create_resource(
    request: CreateResourceRequest,
    service: GanttService = Depends(get_gantt_service),
):
    """Crée une nouvelle ressource."""
    resource = await service.create_resource(
        name=request.name,
        resource_type=request.resource_type,
        capacity_hours_per_day=request.capacity_hours_per_day,
        color=request.color,
    )
    return resource_to_response(resource)


@router.get(
    "/resources/{resource_id}",
    response_model=ResourceResponse,
    summary="Détails d'une ressource",
)
async def get_resource(
    resource_id: str,
    service: GanttService = Depends(get_gantt_service),
):
    """Récupère les détails d'une ressource."""
    resource = await service.get_resource(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Ressource non trouvée")
    return resource_to_response(resource)


@router.get(
    "/resources/{resource_id}/load",
    response_model=list[ResourceLoadResponse],
    summary="Charge d'une ressource",
)
async def get_resource_load(
    resource_id: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    service: GanttService = Depends(get_gantt_service),
):
    """Récupère la charge d'une ressource sur une période."""
    loads = await service.get_resource_load(resource_id, start_date, end_date)
    if not loads:
        raise HTTPException(status_code=404, detail="Ressource non trouvée")

    return [
        ResourceLoadResponse(
            resource_id=load.resource_id,
            resource_name=load.resource_name,
            date=load.date.isoformat(),
            available_hours=load.available_hours,
            allocated_hours=load.allocated_hours,
            load_percent=load.load_percent,
            is_overloaded=load.is_overloaded,
            tasks=load.tasks,
        )
        for load in loads
    ]


# =============================================================================
# ENDPOINTS - TIMELINE & VISUALIZATION
# =============================================================================


@router.get(
    "/timeline",
    response_model=TimelineResponse,
    summary="Timeline Gantt complète",
)
async def get_timeline(
    start_date: date = Query(...),
    end_date: date = Query(...),
    resource_id: Optional[str] = Query(None),
    include_conflicts: bool = Query(True),
    service: GanttService = Depends(get_gantt_service),
):
    """Récupère la timeline complète pour visualisation Gantt."""
    timeline = await service.get_timeline(
        start_date=start_date,
        end_date=end_date,
        resource_id=resource_id,
        include_conflicts=include_conflicts,
    )

    return TimelineResponse(
        start_date=timeline.start_date.isoformat(),
        end_date=timeline.end_date.isoformat(),
        total_tasks=timeline.total_tasks,
        tasks=[task_to_response(t) for t in timeline.tasks],
        dependencies=[dependency_to_response(d) for d in timeline.dependencies],
        milestones=[milestone_to_response(m) for m in timeline.milestones],
        resources=[resource_to_response(r) for r in timeline.resources],
        conflicts=[
            ConflictResponse(
                id=c.id,
                conflict_type=c.conflict_type.value,
                severity=c.severity,
                description=c.description,
                affected_task_ids=c.affected_task_ids,
                affected_resource_ids=c.affected_resource_ids,
                suggested_resolution=c.suggested_resolution,
            )
            for c in timeline.conflicts
        ],
        has_conflicts=timeline.has_conflicts,
    )


@router.get(
    "/conflicts",
    response_model=list[ConflictResponse],
    summary="Conflits de planning",
)
async def get_conflicts(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    service: GanttService = Depends(get_gantt_service),
):
    """Détecte les conflits de planning."""
    conflicts = await service.detect_all_conflicts(start_date, end_date)

    return [
        ConflictResponse(
            id=c.id,
            conflict_type=c.conflict_type.value,
            severity=c.severity,
            description=c.description,
            affected_task_ids=c.affected_task_ids,
            affected_resource_ids=c.affected_resource_ids,
            suggested_resolution=c.suggested_resolution,
        )
        for c in conflicts
    ]


@router.get(
    "/critical-path",
    response_model=list[TaskResponse],
    summary="Chemin critique",
)
async def get_critical_path(
    service: GanttService = Depends(get_gantt_service),
):
    """Calcule et retourne le chemin critique."""
    critical_tasks = await service.calculate_critical_path()
    return [task_to_response(t) for t in critical_tasks]


@router.post(
    "/schedule",
    response_model=list[TaskResponse],
    summary="Auto-planification",
)
async def auto_schedule(
    request: AutoScheduleRequest,
    service: GanttService = Depends(get_gantt_service),
):
    """Planifie automatiquement les tâches."""
    scheduled_tasks = await service.auto_schedule(
        start_from=request.start_from,
        respect_dependencies=request.respect_dependencies,
    )
    return [task_to_response(t) for t in scheduled_tasks]


# =============================================================================
# ENDPOINTS - STATS & HEALTH
# =============================================================================


@router.get(
    "/stats",
    summary="Statistiques Gantt",
)
async def get_stats(
    service: GanttService = Depends(get_gantt_service),
):
    """Statistiques du planning Gantt."""
    return await service.get_statistics()


@router.get(
    "/health",
    summary="Health check Gantt",
)
async def health_check():
    """Health check du service Gantt."""
    return {
        "status": "healthy",
        "service": "production-gantt",
        "features": [
            "task_management",
            "dependencies",
            "milestones",
            "resources",
            "conflict_detection",
            "critical_path",
            "auto_scheduling",
        ],
        "task_types": [t.value for t in TaskType],
        "dependency_types": [d.value for d in DependencyType],
        "resource_types": [r.value for r in ResourceType],
    }
