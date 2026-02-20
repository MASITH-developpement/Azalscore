"""
Module de Consolidation Comptable - GAP-026

Fonctionnalités pour groupes de sociétés:
- Consolidation par intégration globale
- Consolidation par intégration proportionnelle
- Mise en équivalence
- Éliminations intra-groupe
- Conversion des devises
- Calcul des intérêts minoritaires
- Écarts d'acquisition (goodwill)

Normes: ANC 2020-01, IFRS 10/11/12, US GAAP ASC 810
"""

from .service import (
    # Énumérations
    ConsolidationMethod,
    ControlType,
    CurrencyConversionMethod,
    EliminationType,
    AccountingStandard,

    # Data classes
    Entity,
    Participation,
    ExchangeRate,
    TrialBalanceEntry,
    EntityTrialBalance,
    IntercompanyTransaction,
    EliminationEntry,
    GoodwillCalculation,
    MinorityInterest,
    CurrencyTranslation,
    ConsolidationPackage,
    ConsolidationResult,

    # Service
    ConsolidationService,
    create_consolidation_service,
)

__all__ = [
    "ConsolidationMethod",
    "ControlType",
    "CurrencyConversionMethod",
    "EliminationType",
    "AccountingStandard",
    "Entity",
    "Participation",
    "ExchangeRate",
    "TrialBalanceEntry",
    "EntityTrialBalance",
    "IntercompanyTransaction",
    "EliminationEntry",
    "GoodwillCalculation",
    "MinorityInterest",
    "CurrencyTranslation",
    "ConsolidationPackage",
    "ConsolidationResult",
    "ConsolidationService",
    "create_consolidation_service",
]
