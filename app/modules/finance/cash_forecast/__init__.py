"""
AZALSCORE Finance Cash Forecast
================================

Service de prévision de trésorerie avec:
- Prévisions court/moyen/long terme
- Analyse de scénarios (optimiste/pessimiste)
- Alertes de trésorerie
- Intégration factures/commandes

Usage:
    from app.modules.finance.cash_forecast import CashForecastService

    service = CashForecastService(db, tenant_id)
    forecast = await service.generate_forecast(days=90)
"""

from .service import (
    CashForecastService,
    ForecastPeriod,
    ForecastEntry,
    ForecastResult,
    ScenarioType,
    CashAlert,
    AlertSeverity,
)
from .router import router as cash_forecast_router

__all__ = [
    "CashForecastService",
    "ForecastPeriod",
    "ForecastEntry",
    "ForecastResult",
    "ScenarioType",
    "CashAlert",
    "AlertSeverity",
    "cash_forecast_router",
]
