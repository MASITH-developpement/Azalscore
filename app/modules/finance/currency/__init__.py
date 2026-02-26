"""
AZALSCORE Finance Currency Management
======================================

Service de gestion des devises et taux de change.

Fonctionnalités:
- Récupération automatique des taux BCE/ECB
- Conversion multi-devises
- Historique des taux
- Gains/pertes de change

Usage:
    from app.modules.finance.currency import CurrencyService

    service = CurrencyService(db, tenant_id)
    rate = await service.get_rate("USD", "EUR")
    converted = await service.convert(Decimal("100"), "USD", "EUR")
"""

from .service import (
    CurrencyService,
    ExchangeRate,
    CurrencyConversion,
    ConversionResult,
    RateSource,
)
from .router import router as currency_router

__all__ = [
    "CurrencyService",
    "ExchangeRate",
    "CurrencyConversion",
    "ConversionResult",
    "RateSource",
    "currency_router",
]
