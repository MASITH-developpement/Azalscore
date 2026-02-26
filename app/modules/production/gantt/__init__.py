"""
AZALSCORE Gantt Production Module
==================================

Module de visualisation Gantt pour la production.

Fonctionnalités:
- Diagramme Gantt interactif
- Gestion des dépendances
- Jalons de production
- Allocation des ressources
- Détection des conflits
- Optimisation du planning

Usage:
    from app.modules.production.gantt import GanttService

    service = GanttService(db, tenant_id)
    timeline = await service.get_production_timeline(start_date, end_date)
    conflicts = await service.detect_conflicts(workstation_id)
"""

from .service import (
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
from .router import router as gantt_router

__all__ = [
    "GanttService",
    "GanttTask",
    "GanttResource",
    "GanttDependency",
    "GanttMilestone",
    "ResourceAllocation",
    "ScheduleConflict",
    "TaskType",
    "DependencyType",
    "ConflictType",
    "gantt_router",
]
