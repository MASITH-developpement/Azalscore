"""
Module Forecasting / Prévisions - GAP-076

Prévisions et projections:
- Prévision des ventes
- Prévision de trésorerie
- Prévision de stock
- Modèles statistiques
- Scénarios What-If
- Budgétisation
- KPIs et tableaux de bord
"""

# Modèles SQLAlchemy
from .models import (
    Forecast,
    ForecastModel,
    Scenario,
    Budget,
    KPI,
    ForecastType,
    ForecastMethod,
    Granularity,
    ForecastStatus,
    ScenarioType,
    BudgetStatus,
    KPIStatus,
)

# Repository
from .repository import (
    ForecastRepository,
    BudgetRepository,
    KPIRepository,
    ScenarioRepository,
    ForecastModelRepository,
)

# Router
from .router import router

# Exceptions
from .exceptions import (
    ForecastingError,
    ForecastNotFoundError,
    ForecastDuplicateError,
    ForecastValidationError,
    ForecastStateError,
    BudgetNotFoundError,
    BudgetDuplicateError,
    BudgetValidationError,
    BudgetStateError,
    KPINotFoundError,
    KPIDuplicateError,
    KPIValidationError,
    ScenarioNotFoundError,
    ScenarioDuplicateError,
    ModelNotFoundError,
    ModelDuplicateError,
)

# Service legacy (pour compatibilité)
from .service import (
    ForecastingService,
    create_forecasting_service,
)

__all__ = [
    # Modèles
    "Forecast",
    "ForecastModel",
    "Scenario",
    "Budget",
    "KPI",
    # Enums
    "ForecastType",
    "ForecastMethod",
    "Granularity",
    "ForecastStatus",
    "ScenarioType",
    "BudgetStatus",
    "KPIStatus",
    # Repository
    "ForecastRepository",
    "BudgetRepository",
    "KPIRepository",
    "ScenarioRepository",
    "ForecastModelRepository",
    # Router
    "router",
    # Exceptions
    "ForecastingError",
    "ForecastNotFoundError",
    "ForecastDuplicateError",
    "ForecastValidationError",
    "ForecastStateError",
    "BudgetNotFoundError",
    "BudgetDuplicateError",
    "BudgetValidationError",
    "BudgetStateError",
    "KPINotFoundError",
    "KPIDuplicateError",
    "KPIValidationError",
    "ScenarioNotFoundError",
    "ScenarioDuplicateError",
    "ModelNotFoundError",
    "ModelDuplicateError",
    # Service legacy
    "ForecastingService",
    "create_forecasting_service",
]
