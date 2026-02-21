"""
Exceptions métier - Module Forecasting (GAP-076)
"""


class ForecastingError(Exception):
    """Exception de base du module Forecasting."""
    pass


class ForecastNotFoundError(ForecastingError):
    """Prévision non trouvée."""
    pass


class ForecastDuplicateError(ForecastingError):
    """Code de prévision déjà existant."""
    pass


class ForecastValidationError(ForecastingError):
    """Erreur de validation métier."""
    pass


class ForecastStateError(ForecastingError):
    """Transition d'état invalide."""
    pass


class BudgetNotFoundError(ForecastingError):
    """Budget non trouvé."""
    pass


class BudgetDuplicateError(ForecastingError):
    """Code de budget déjà existant."""
    pass


class BudgetValidationError(ForecastingError):
    """Erreur de validation budget."""
    pass


class BudgetStateError(ForecastingError):
    """Transition d'état budget invalide."""
    pass


class KPINotFoundError(ForecastingError):
    """KPI non trouvé."""
    pass


class KPIDuplicateError(ForecastingError):
    """Code KPI déjà existant."""
    pass


class KPIValidationError(ForecastingError):
    """Erreur de validation KPI."""
    pass


class ScenarioNotFoundError(ForecastingError):
    """Scénario non trouvé."""
    pass


class ScenarioDuplicateError(ForecastingError):
    """Code scénario déjà existant."""
    pass


class ModelNotFoundError(ForecastingError):
    """Modèle de prévision non trouvé."""
    pass


class ModelDuplicateError(ForecastingError):
    """Code modèle déjà existant."""
    pass
