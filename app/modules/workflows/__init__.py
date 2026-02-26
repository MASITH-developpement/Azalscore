"""
Module Workflows et BPM - GAP-045

Gestion des processus métier:
- Workflows visuels
- Étapes et transitions conditionnelles
- Approbations multi-niveaux
- Parallélisme (fork/join)
- Escalade automatique
- Délégation
- Historique complet
"""

from .service import (
    # Énumérations
    WorkflowStatus,
    InstanceStatus,
    StepType,
    TaskStatus,
    ApprovalType,
    ConditionOperator,

    # Data classes
    Condition,
    Transition,
    AssignmentRule,
    EscalationRule,
    Step,
    WorkflowDefinition,
    TaskInstance,
    StepExecution,
    WorkflowInstance,
    WorkflowHistory,

    # Service
    WorkflowService,
    create_workflow_service,
)

__all__ = [
    "WorkflowStatus",
    "InstanceStatus",
    "StepType",
    "TaskStatus",
    "ApprovalType",
    "ConditionOperator",
    "Condition",
    "Transition",
    "AssignmentRule",
    "EscalationRule",
    "Step",
    "WorkflowDefinition",
    "TaskInstance",
    "StepExecution",
    "WorkflowInstance",
    "WorkflowHistory",
    "WorkflowService",
    "create_workflow_service",
]
