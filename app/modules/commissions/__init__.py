"""
Module de Gestion des Commissions Commerciales - GAP-041

Module complet pour la gestion des commissions:
- Plans de commissionnement multi-niveaux (flat, progressive, retroactive, regressive, stepped)
- Calcul automatique sur factures/encaissements/livraisons
- Paliers progressifs et degressifs
- Accelerateurs de performance
- Split commission multi-vendeurs
- Override manager sur equipe
- Validation workflow multi-niveaux
- Periodes de commissionnement
- Releves et paiement des commissions
- Ajustements manuels (bonus, penalites, corrections)
- Clawbacks (recuperation si annulation)
- Dashboard et reporting
- Integration paie

Architecture:
- Multi-tenant strict (tenant_id obligatoire)
- Soft delete avec audit complet
- Versioning des entites
- _base_query() filtre sur tenant_id

Inspire de:
- Sage: Plans de commission flexibles
- Axonaut: Simplicity of commission rules
- Pennylane: Integration comptable
- Odoo: Commission multi-niveaux
- Microsoft Dynamics 365: Sales performance management
"""

from .models import (
    # Enums
    CommissionBasis,
    TierType,
    CommissionStatus,
    PlanStatus,
    PaymentFrequency,
    PeriodType,
    AdjustmentType,
    WorkflowStatus,
    # Models
    CommissionPlan,
    CommissionTier,
    CommissionAccelerator,
    CommissionAssignment,
    SalesTeamMember,
    CommissionTransaction,
    CommissionCalculation,
    CommissionPeriod,
    CommissionStatement,
    CommissionAdjustment,
    CommissionClawback,
    CommissionWorkflow,
    CommissionAuditLog,
)

from .schemas import (
    # Plans
    CommissionPlanCreate,
    CommissionPlanUpdate,
    CommissionPlanResponse,
    CommissionPlanList,
    CommissionPlanListItem,
    PlanFilters,
    # Tiers
    CommissionTierCreate,
    CommissionTierUpdate,
    CommissionTierResponse,
    # Accelerators
    AcceleratorCreate,
    AcceleratorUpdate,
    AcceleratorResponse,
    # Assignments
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
    AssignmentList,
    # Team
    TeamMemberCreate,
    TeamMemberUpdate,
    TeamMemberResponse,
    # Transactions
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionList,
    TransactionFilters,
    # Calculations
    CalculationResponse,
    CalculationList,
    CalculationFilters,
    CalculationRequest,
    BulkCalculationRequest,
    # Periods
    PeriodCreate,
    PeriodUpdate,
    PeriodResponse,
    PeriodList,
    # Statements
    StatementResponse,
    StatementList,
    # Adjustments
    AdjustmentCreate,
    AdjustmentUpdate,
    AdjustmentResponse,
    AdjustmentList,
    # Clawbacks
    ClawbackCreate,
    ClawbackUpdate,
    ClawbackResponse,
    ClawbackList,
    # Workflow
    WorkflowAction,
    WorkflowResponse,
    # Stats
    SalesRepPerformance,
    TeamPerformance,
    CommissionDashboard,
    Leaderboard,
    # Common
    AutocompleteItem,
    AutocompleteResponse,
    BulkActionResult,
    ExportRequest,
)

from .service import (
    CommissionService,
    create_commission_service,
)

from .repository import (
    CommissionPlanRepository,
    CommissionAssignmentRepository,
    SalesTeamMemberRepository,
    CommissionTransactionRepository,
    CommissionCalculationRepository,
    CommissionPeriodRepository,
    CommissionStatementRepository,
    CommissionAdjustmentRepository,
    CommissionClawbackRepository,
    CommissionAuditLogRepository,
)

from .exceptions import (
    CommissionError,
    PlanNotFoundError,
    PlanDuplicateError,
    PlanInvalidStateError,
    PlanActivationError,
    PlanValidationError,
    TierConfigurationError,
    AssignmentNotFoundError,
    AssignmentDuplicateError,
    AssignmentOverlapError,
    TransactionNotFoundError,
    TransactionDuplicateError,
    TransactionLockedError,
    TransactionValidationError,
    CalculationNotFoundError,
    CalculationError,
    CalculationAlreadyExistsError,
    CalculationLockedError,
    NoPlanApplicableError,
    PeriodNotFoundError,
    PeriodDuplicateError,
    PeriodLockedError,
    PeriodOverlapError,
    StatementNotFoundError,
    StatementAlreadyPaidError,
    StatementGenerationError,
    AdjustmentNotFoundError,
    AdjustmentNotPendingError,
    AdjustmentValidationError,
    ClawbackNotFoundError,
    ClawbackNotEligibleError,
    ClawbackAlreadyAppliedError,
    ClawbackPeriodExpiredError,
    WorkflowNotFoundError,
    WorkflowInvalidActionError,
    WorkflowUnauthorizedError,
    WorkflowAlreadyCompletedError,
    TeamMemberNotFoundError,
    TeamHierarchyError,
    CircularHierarchyError,
    PayrollIntegrationError,
    ExportError,
    UnauthorizedAccessError,
    InsufficientPermissionsError,
)

from .router import router

__all__ = [
    # Router
    "router",
    # Enums
    "CommissionBasis",
    "TierType",
    "CommissionStatus",
    "PlanStatus",
    "PaymentFrequency",
    "PeriodType",
    "AdjustmentType",
    "WorkflowStatus",
    # Models
    "CommissionPlan",
    "CommissionTier",
    "CommissionAccelerator",
    "CommissionAssignment",
    "SalesTeamMember",
    "CommissionTransaction",
    "CommissionCalculation",
    "CommissionPeriod",
    "CommissionStatement",
    "CommissionAdjustment",
    "CommissionClawback",
    "CommissionWorkflow",
    "CommissionAuditLog",
    # Schemas - Plans
    "CommissionPlanCreate",
    "CommissionPlanUpdate",
    "CommissionPlanResponse",
    "CommissionPlanList",
    "CommissionPlanListItem",
    "PlanFilters",
    "CommissionTierCreate",
    "CommissionTierUpdate",
    "CommissionTierResponse",
    "AcceleratorCreate",
    "AcceleratorUpdate",
    "AcceleratorResponse",
    # Schemas - Assignments
    "AssignmentCreate",
    "AssignmentUpdate",
    "AssignmentResponse",
    "AssignmentList",
    # Schemas - Team
    "TeamMemberCreate",
    "TeamMemberUpdate",
    "TeamMemberResponse",
    # Schemas - Transactions
    "TransactionCreate",
    "TransactionUpdate",
    "TransactionResponse",
    "TransactionList",
    "TransactionFilters",
    # Schemas - Calculations
    "CalculationResponse",
    "CalculationList",
    "CalculationFilters",
    "CalculationRequest",
    "BulkCalculationRequest",
    # Schemas - Periods
    "PeriodCreate",
    "PeriodUpdate",
    "PeriodResponse",
    "PeriodList",
    # Schemas - Statements
    "StatementResponse",
    "StatementList",
    # Schemas - Adjustments
    "AdjustmentCreate",
    "AdjustmentUpdate",
    "AdjustmentResponse",
    "AdjustmentList",
    # Schemas - Clawbacks
    "ClawbackCreate",
    "ClawbackUpdate",
    "ClawbackResponse",
    "ClawbackList",
    # Schemas - Workflow
    "WorkflowAction",
    "WorkflowResponse",
    # Schemas - Stats
    "SalesRepPerformance",
    "TeamPerformance",
    "CommissionDashboard",
    "Leaderboard",
    # Schemas - Common
    "AutocompleteItem",
    "AutocompleteResponse",
    "BulkActionResult",
    "ExportRequest",
    # Service
    "CommissionService",
    "create_commission_service",
    # Repositories
    "CommissionPlanRepository",
    "CommissionAssignmentRepository",
    "SalesTeamMemberRepository",
    "CommissionTransactionRepository",
    "CommissionCalculationRepository",
    "CommissionPeriodRepository",
    "CommissionStatementRepository",
    "CommissionAdjustmentRepository",
    "CommissionClawbackRepository",
    "CommissionAuditLogRepository",
    # Exceptions
    "CommissionError",
    "PlanNotFoundError",
    "PlanDuplicateError",
    "PlanInvalidStateError",
    "PlanActivationError",
    "PlanValidationError",
    "TierConfigurationError",
    "AssignmentNotFoundError",
    "AssignmentDuplicateError",
    "AssignmentOverlapError",
    "TransactionNotFoundError",
    "TransactionDuplicateError",
    "TransactionLockedError",
    "TransactionValidationError",
    "CalculationNotFoundError",
    "CalculationError",
    "CalculationAlreadyExistsError",
    "CalculationLockedError",
    "NoPlanApplicableError",
    "PeriodNotFoundError",
    "PeriodDuplicateError",
    "PeriodLockedError",
    "PeriodOverlapError",
    "StatementNotFoundError",
    "StatementAlreadyPaidError",
    "StatementGenerationError",
    "AdjustmentNotFoundError",
    "AdjustmentNotPendingError",
    "AdjustmentValidationError",
    "ClawbackNotFoundError",
    "ClawbackNotEligibleError",
    "ClawbackAlreadyAppliedError",
    "ClawbackPeriodExpiredError",
    "WorkflowNotFoundError",
    "WorkflowInvalidActionError",
    "WorkflowUnauthorizedError",
    "WorkflowAlreadyCompletedError",
    "TeamMemberNotFoundError",
    "TeamHierarchyError",
    "CircularHierarchyError",
    "PayrollIntegrationError",
    "ExportError",
    "UnauthorizedAccessError",
    "InsufficientPermissionsError",
]
