"""
AZALS MODULE - CURRENCY
========================

Module de gestion multi-devises pour AZALSCORE ERP.

FONCTIONNALITES:
- Liste des devises ISO 4217
- Taux de change manuels et automatiques
- Integration API BCE, OpenExchange, Fixer
- Historique complet des taux
- Conversion avec triangulation
- Devise de base par tenant
- Calcul des ecarts de change (realises et latents)
- Reevaluation periodique
- Alertes sur variations de taux
- Rapports multi-devises

ARCHITECTURE:
- models.py: Modeles SQLAlchemy (Currency, ExchangeRate, etc.)
- schemas.py: Schemas Pydantic (validation)
- repository.py: Acces aux donnees avec isolation tenant
- service.py: Logique metier
- router.py: Endpoints API REST
- exceptions.py: Exceptions metier

CONFORMITE:
- Isolation multi-tenant stricte
- Soft delete avec audit
- Versioning des entites
- Tracabilite complete

USAGE:
    from app.modules.currency import CurrencyService, create_currency_service

    # Creer le service
    service = create_currency_service(db_session, tenant_id)

    # Convertir un montant
    result = service.convert(
        amount=Decimal("100"),
        from_currency="EUR",
        to_currency="USD"
    )

    # Recuperer un taux
    rate = service.get_rate("EUR", "USD")

    # Calculer un ecart de change
    gain_loss = service.calculate_exchange_gain_loss(
        document_type="invoice",
        document_id=invoice_id,
        ...
    )
"""

from .models import (
    Currency,
    ExchangeRate,
    CurrencyConfig,
    ExchangeGainLoss,
    CurrencyRevaluation,
    CurrencyConversionLog,
    RateAlert,
    # Enums
    RateSource,
    RateType,
    ConversionMethod,
    GainLossType,
    CurrencyStatus,
    RevaluationStatus,
)

from .schemas import (
    # Currency
    CurrencyCreate,
    CurrencyUpdate,
    CurrencyResponse,
    CurrencyList,
    CurrencyListItem,
    CurrencyFilters,
    # Rates
    ExchangeRateCreate,
    ExchangeRateUpdate,
    ExchangeRateResponse,
    ExchangeRateList,
    ExchangeRateFilters,
    RateHistoryResponse,
    # Conversion
    ConversionRequest,
    ConversionResult,
    MultiConversionRequest,
    MultiConversionResult,
    # Config
    CurrencyConfigCreate,
    CurrencyConfigUpdate,
    CurrencyConfigResponse,
    # Gain/Loss
    ExchangeGainLossResponse,
    ExchangeGainLossList,
    ExchangeGainLossSummary,
    # Revaluation
    RevaluationCreate,
    RevaluationResponse,
    RevaluationPreview,
)

from .repository import (
    CurrencyRepository,
    ExchangeRateRepository,
    CurrencyConfigRepository,
    ExchangeGainLossRepository,
    CurrencyRevaluationRepository,
    CurrencyConversionLogRepository,
    RateAlertRepository,
)

from .service import (
    CurrencyService,
    create_currency_service,
    ISO_4217_CURRENCIES,
    MAJOR_CURRENCIES,
)

from .exceptions import (
    CurrencyError,
    CurrencyNotFoundError,
    CurrencyAlreadyExistsError,
    CurrencyDisabledError,
    ExchangeRateNotFoundError,
    ExchangeRateAlreadyExistsError,
    InvalidExchangeRateError,
    ConversionError,
    NoConversionPathError,
    TriangulationFailedError,
    RateToleranceExceededError,
    GainLossNotFoundError,
    RevaluationNotFoundError,
    RateAPIError,
    ConfigNotFoundError,
)

from .router import router


__all__ = [
    # Models
    "Currency",
    "ExchangeRate",
    "CurrencyConfig",
    "ExchangeGainLoss",
    "CurrencyRevaluation",
    "CurrencyConversionLog",
    "RateAlert",
    # Enums
    "RateSource",
    "RateType",
    "ConversionMethod",
    "GainLossType",
    "CurrencyStatus",
    "RevaluationStatus",
    # Schemas
    "CurrencyCreate",
    "CurrencyUpdate",
    "CurrencyResponse",
    "CurrencyList",
    "ExchangeRateCreate",
    "ExchangeRateUpdate",
    "ExchangeRateResponse",
    "ConversionRequest",
    "ConversionResult",
    "CurrencyConfigResponse",
    "ExchangeGainLossSummary",
    "RevaluationResponse",
    # Repositories
    "CurrencyRepository",
    "ExchangeRateRepository",
    "CurrencyConfigRepository",
    "ExchangeGainLossRepository",
    "CurrencyRevaluationRepository",
    # Service
    "CurrencyService",
    "create_currency_service",
    "ISO_4217_CURRENCIES",
    "MAJOR_CURRENCIES",
    # Exceptions
    "CurrencyError",
    "CurrencyNotFoundError",
    "ExchangeRateNotFoundError",
    "ConversionError",
    "RateAPIError",
    # Router
    "router",
]
