"""
Module Approval Workflow / Approbations - GAP-083

Gestion des workflows d'approbation:
- Définition de workflows
- Règles et conditions
- Approbateurs et délégations
- Escalades automatiques
- Historique et audit
- Notifications
"""

from .service import (
    # Énumérations (service)
    ConditionOperator,

    # Data classes
    Condition,
    Approver as ApproverData,
    EscalationRule,
    WorkflowStep as WorkflowStepData,
    Workflow as WorkflowData,
    ApprovalAction as ApprovalActionData,
    StepStatus,
    ApprovalRequest as ApprovalRequestData,
    Delegation as DelegationData,
    ApprovalStats,

    # Service
    ApprovalService,
    create_approval_service,
)

# Models SQLAlchemy
from .models import (
    Workflow,
    WorkflowStep,
    ApprovalRequest,
    ApprovalAction,
    Delegation,
    WorkflowStatus,
    RequestStatus,
    ApprovalType,
    StepType,
    ApproverType,
    ActionType,
)

# Repositories
from .repository import (
    WorkflowRepository,
    ApprovalRequestRepository,
    DelegationRepository,
)

# Exceptions
from .exceptions import (
    ApprovalError,
    WorkflowNotFoundError,
    WorkflowDuplicateError,
    WorkflowValidationError,
    WorkflowStateError,
    WorkflowInactiveError,
    RequestNotFoundError,
    RequestDuplicateError,
    RequestValidationError,
    RequestStateError,
    RequestAlreadyProcessedError,
    ApproverNotAuthorizedError,
    ApproverAlreadyActedError,
    CommentsRequiredError,
    DelegationNotFoundError,
    DelegationValidationError,
    DelegationExpiredError,
    EscalationError,
)

# Router
from .router import router

__all__ = [
    # Enums
    "ApprovalType",
    "WorkflowStatus",
    "RequestStatus",
    "StepType",
    "ApproverType",
    "ActionType",
    "ConditionOperator",
    # Models SQLAlchemy
    "Workflow",
    "WorkflowStep",
    "ApprovalRequest",
    "ApprovalAction",
    "Delegation",
    # Repositories
    "WorkflowRepository",
    "ApprovalRequestRepository",
    "DelegationRepository",
    # Data classes (service)
    "Condition",
    "ApproverData",
    "EscalationRule",
    "WorkflowStepData",
    "WorkflowData",
    "ApprovalActionData",
    "StepStatus",
    "ApprovalRequestData",
    "DelegationData",
    "ApprovalStats",
    # Service
    "ApprovalService",
    "create_approval_service",
    # Exceptions
    "ApprovalError",
    "WorkflowNotFoundError",
    "WorkflowDuplicateError",
    "WorkflowValidationError",
    "WorkflowStateError",
    "WorkflowInactiveError",
    "RequestNotFoundError",
    "RequestDuplicateError",
    "RequestValidationError",
    "RequestStateError",
    "RequestAlreadyProcessedError",
    "ApproverNotAuthorizedError",
    "ApproverAlreadyActedError",
    "CommentsRequiredError",
    "DelegationNotFoundError",
    "DelegationValidationError",
    "DelegationExpiredError",
    "EscalationError",
    # Router
    "router",
]
