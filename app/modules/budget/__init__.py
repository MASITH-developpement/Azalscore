"""
AZALS MODULE - BUDGET: Gestion Budgetaire Complete
====================================================

Module complet de gestion budgetaire pour AZALSCORE ERP.

Fonctionnalites:
- Budgets par periode (mensuel, trimestriel, annuel)
- Lignes budgetaires hierarchiques
- Multi-axes analytiques (departement, projet, centre de couts)
- Suivi realise vs prevu
- Alertes de depassement
- Controle budgetaire (soft/hard)
- Revisions budgetaires avec workflow
- Previsions glissantes (rolling forecast)
- Scenarios et simulations
- Consolidation multi-entites
- Dashboard et reporting

Inspire des fonctionnalites de:
- Sage FRP 1000 Budget
- Microsoft Dynamics 365 Finance
- Odoo Budget Management
- Pennylane
- Axonaut

Architecture:
- Multi-tenant strict
- Soft delete
- Audit trail complet
- Optimistic locking

Auteur: AZALSCORE Team
Version: 2.0.0
"""

from .models import (
    # Enumerations
    AlertSeverity,
    AlertStatus,
    AllocationMethod,
    BudgetLineType,
    BudgetPeriodType,
    BudgetStatus,
    BudgetType,
    ControlMode,
    ForecastConfidence,
    RevisionStatus,
    ScenarioType,
    VarianceType,
    # Models
    Budget,
    BudgetActual,
    BudgetAlert,
    BudgetApprovalRule,
    BudgetCategory,
    BudgetConsolidation,
    BudgetForecast,
    BudgetLine,
    BudgetPeriod,
    BudgetPeriodAmount,
    BudgetRevision,
    BudgetRevisionDetail,
    BudgetScenario,
    BudgetScenarioLine,
    BudgetTemplate,
    SeasonalProfile,
)

from .schemas import (
    # Category schemas
    BudgetCategoryCreate,
    BudgetCategoryResponse,
    BudgetCategoryUpdate,
    PaginatedBudgetCategories,
    # Budget schemas
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    BudgetDetailResponse,
    BudgetSummary,
    PaginatedBudgets,
    # Line schemas
    BudgetLineCreate,
    BudgetLineResponse,
    BudgetLineUpdate,
    PaginatedBudgetLines,
    # Actual schemas
    BudgetActualCreate,
    BudgetActualResponse,
    PaginatedBudgetActuals,
    # Revision schemas
    BudgetRevisionCreate,
    BudgetRevisionResponse,
    PaginatedBudgetRevisions,
    # Forecast schemas
    BudgetForecastCreate,
    BudgetForecastResponse,
    PaginatedBudgetForecasts,
    # Scenario schemas
    BudgetScenarioCreate,
    BudgetScenarioResponse,
    PaginatedBudgetScenarios,
    # Alert schemas
    BudgetAlertResponse,
    AlertAcknowledge,
    AlertResolve,
    PaginatedBudgetAlerts,
    # Analysis schemas
    BudgetVariance,
    BudgetExecutionRate,
    BudgetDashboard,
    # Control schemas
    BudgetControlCheck,
    BudgetControlResult,
    # Workflow schemas
    BudgetSubmit,
    BudgetApprove,
    BudgetReject,
    BudgetActivate,
)

from .exceptions import (
    BudgetException,
    BudgetNotFoundError,
    BudgetLineNotFoundError,
    BudgetCategoryNotFoundError,
    BudgetRevisionNotFoundError,
    BudgetAlreadyExistsError,
    BudgetStatusError,
    BudgetNotModifiableError,
    BudgetPeriodLockedError,
    BudgetControlViolationError,
    BudgetControlWarning,
    BudgetWorkflowError,
    BudgetApprovalError,
    BudgetRevisionError,
    BudgetCalculationError,
    BudgetImportError,
    BudgetExportError,
    BudgetConsolidationError,
    BudgetScenarioError,
    BudgetValidationError,
    InsufficientBudgetError,
    BudgetPermissionError,
    OptimisticLockError,
)

from .repository import BudgetRepository
from .service import BudgetService, create_budget_service
from .router import router

__all__ = [
    # Router
    "router",
    # Service
    "BudgetService",
    "create_budget_service",
    # Repository
    "BudgetRepository",
    # Enumerations
    "AlertSeverity",
    "AlertStatus",
    "AllocationMethod",
    "BudgetLineType",
    "BudgetPeriodType",
    "BudgetStatus",
    "BudgetType",
    "ControlMode",
    "ForecastConfidence",
    "RevisionStatus",
    "ScenarioType",
    "VarianceType",
    # Models
    "Budget",
    "BudgetActual",
    "BudgetAlert",
    "BudgetApprovalRule",
    "BudgetCategory",
    "BudgetConsolidation",
    "BudgetForecast",
    "BudgetLine",
    "BudgetPeriod",
    "BudgetPeriodAmount",
    "BudgetRevision",
    "BudgetRevisionDetail",
    "BudgetScenario",
    "BudgetScenarioLine",
    "BudgetTemplate",
    "SeasonalProfile",
    # Schemas
    "BudgetCategoryCreate",
    "BudgetCategoryResponse",
    "BudgetCategoryUpdate",
    "BudgetCreate",
    "BudgetUpdate",
    "BudgetResponse",
    "BudgetDetailResponse",
    "BudgetSummary",
    "BudgetLineCreate",
    "BudgetLineResponse",
    "BudgetLineUpdate",
    "BudgetActualCreate",
    "BudgetActualResponse",
    "BudgetRevisionCreate",
    "BudgetRevisionResponse",
    "BudgetForecastCreate",
    "BudgetForecastResponse",
    "BudgetScenarioCreate",
    "BudgetScenarioResponse",
    "BudgetAlertResponse",
    "AlertAcknowledge",
    "AlertResolve",
    "BudgetVariance",
    "BudgetExecutionRate",
    "BudgetDashboard",
    "BudgetControlCheck",
    "BudgetControlResult",
    "BudgetSubmit",
    "BudgetApprove",
    "BudgetReject",
    "BudgetActivate",
    # Paginated
    "PaginatedBudgetCategories",
    "PaginatedBudgets",
    "PaginatedBudgetLines",
    "PaginatedBudgetActuals",
    "PaginatedBudgetRevisions",
    "PaginatedBudgetForecasts",
    "PaginatedBudgetScenarios",
    "PaginatedBudgetAlerts",
    # Exceptions
    "BudgetException",
    "BudgetNotFoundError",
    "BudgetLineNotFoundError",
    "BudgetCategoryNotFoundError",
    "BudgetRevisionNotFoundError",
    "BudgetAlreadyExistsError",
    "BudgetStatusError",
    "BudgetNotModifiableError",
    "BudgetPeriodLockedError",
    "BudgetControlViolationError",
    "BudgetControlWarning",
    "BudgetWorkflowError",
    "BudgetApprovalError",
    "BudgetRevisionError",
    "BudgetCalculationError",
    "BudgetImportError",
    "BudgetExportError",
    "BudgetConsolidationError",
    "BudgetScenarioError",
    "BudgetValidationError",
    "InsufficientBudgetError",
    "BudgetPermissionError",
    "OptimisticLockError",
]
