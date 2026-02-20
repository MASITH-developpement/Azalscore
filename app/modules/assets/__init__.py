"""
Module de Gestion des Immobilisations et Actifs - GAP-036

Gestion complète du cycle de vie des actifs:
- Acquisition et mise en service
- Amortissements (linéaire, dégressif)
- Inventaire physique
- Cessions et mises au rebut
- Reporting comptable et fiscal

Conformité: PCG, CGI, IFRS 16, Règlement ANC 2014-03
"""

from .service import (
    # Énumérations
    AssetCategory,
    DepreciationMethod,
    AssetStatus,
    DisposalType,
    MovementType,

    # Data classes
    AssetLocation,
    DepreciationScheduleEntry,
    AssetMovement,
    AssetDisposal,
    AssetImpairment,
    Asset,
    DepreciationRun,
    PhysicalInventory,

    # Constantes
    DECLINING_BALANCE_COEFFICIENTS,
    RECOMMENDED_USEFUL_LIFE,
    ACCOUNTING_ACCOUNTS,

    # Service
    AssetService,
    create_asset_service,
)

__all__ = [
    "AssetCategory",
    "DepreciationMethod",
    "AssetStatus",
    "DisposalType",
    "MovementType",
    "AssetLocation",
    "DepreciationScheduleEntry",
    "AssetMovement",
    "AssetDisposal",
    "AssetImpairment",
    "Asset",
    "DepreciationRun",
    "PhysicalInventory",
    "DECLINING_BALANCE_COEFFICIENTS",
    "RECOMMENDED_USEFUL_LIFE",
    "ACCOUNTING_ACCOUNTS",
    "AssetService",
    "create_asset_service",
]
