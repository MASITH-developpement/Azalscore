"""
AZALS MODULE ASSETS - Gestion des Immobilisations
==================================================

Module complet de gestion des immobilisations pour AZALSCORE ERP.
Fonctionnalites inspirees de: Sage, Odoo, Microsoft Dynamics 365, Pennylane, Axonaut.

Fonctionnalites:
- Gestion du cycle de vie complet des actifs
- Categories et hierarchie d'immobilisations
- Calcul des amortissements (lineaire, degressif, unites de production, SOFTY)
- Suivi maintenance preventive et corrective
- Cessions et mises au rebut
- Inventaire physique avec codes-barres/QR
- Transferts entre sites et responsables
- Gestion des assurances
- Valorisation et reporting
- Integration comptable (PCG, CGI, IFRS)

Architecture:
- Multi-tenant avec isolation stricte
- Soft delete et audit trail complets
- Optimistic locking pour la concurrence

Conformite:
- PCG (Plan Comptable General)
- Code General des Impots (amortissements fiscaux)
- IFRS 16 (contrats de location)
- Reglement ANC 2014-03
"""

# Modeles SQLAlchemy
from .models import (
    # Enums
    AssetStatus,
    AssetType,
    DepreciationMethod,
    DisposalType,
    InsuranceStatus,
    InventoryStatus,
    MaintenanceStatus,
    MaintenanceType,
    MovementType,
    # Modeles
    AssetCategory,
    AssetDocument,
    AssetInsuranceItem,
    AssetInsurancePolicy,
    AssetInventory,
    AssetInventoryItem,
    AssetMaintenance,
    AssetMovement,
    AssetTransfer,
    AssetValuation,
    DepreciationRun,
    DepreciationSchedule,
    FixedAsset,
)

# Schemas Pydantic
from .schemas import (
    AssetAutocompleteItem,
    AssetAutocompleteResponse,
    AssetCategoryCreate,
    AssetCategoryResponse,
    AssetCategoryUpdate,
    AssetDashboard,
    AssetFilters,
    AssetInsuranceItemCreate,
    AssetInsurancePolicyCreate,
    AssetInsurancePolicyResponse,
    AssetInventoryCreate,
    AssetInventoryItemResponse,
    AssetInventoryItemUpdate,
    AssetInventoryResponse,
    AssetMaintenanceComplete,
    AssetMaintenanceCreate,
    AssetMaintenanceResponse,
    AssetMaintenanceUpdate,
    AssetMovementCreate,
    AssetMovementResponse,
    AssetStatistics,
    AssetTransferCreate,
    AssetTransferResponse,
    AssetValuationResponse,
    DepreciationRunCreate,
    DepreciationRunResponse,
    DepreciationScheduleEntryResponse,
    DepreciationScheduleResponse,
    DisposalResponse,
    DisposeAssetRequest,
    FixedAssetCreate,
    FixedAssetResponse,
    FixedAssetSummary,
    FixedAssetUpdate,
    PaginatedAssetResponse,
    PaginatedMaintenanceResponse,
    PaginatedMovementResponse,
    PutInServiceRequest,
)

# Exceptions
from .exceptions import (
    AssetAlreadyDisposedError,
    AssetAlreadyInServiceError,
    AssetCodeExistsError,
    AssetHasComponentsError,
    AssetLockedError,
    AssetModuleError,
    AssetNotFoundError,
    AssetNotInServiceError,
    CategoryCodeExistsError,
    CategoryHasAssetsError,
    CategoryHasChildrenError,
    CategoryNotFoundError,
    DateValidationError,
    DepreciationAlreadyPostedError,
    DepreciationCalculationError,
    DepreciationRunNotFoundError,
    DisposalDateBeforeAcquisitionError,
    InServiceDateBeforeAcquisitionError,
    InsurancePolicyExpiredError,
    InsurancePolicyNotFoundError,
    InventoryAlreadyCompletedError,
    InventoryInProgressError,
    InventoryItemNotFoundError,
    InventoryNotFoundError,
    InvalidDepreciationMethodError,
    InvalidMovementAmountError,
    MaintenanceAlreadyCompletedError,
    MaintenanceInvalidStatusError,
    MaintenanceNotFoundError,
    MissingAccountError,
    MovementAlreadyPostedError,
    MovementNotFoundError,
    OptimisticLockError,
    PeriodClosedError,
    TransferAlreadyCompletedError,
    TransferInvalidDestinationError,
    TransferNotFoundError,
    UsefulLifeNotSetError,
    ValidationError,
)

# Repositories
from .repository import (
    AssetCategoryRepository,
    AssetInsurancePolicyRepository,
    AssetInventoryRepository,
    AssetMaintenanceRepository,
    AssetMovementRepository,
    AssetTransferRepository,
    DepreciationRunRepository,
    DepreciationScheduleRepository,
    FixedAssetRepository,
)

# Service avec DB
from .service_db import (
    ACCOUNTING_ACCOUNTS,
    DECLINING_BALANCE_COEFFICIENTS,
    RECOMMENDED_USEFUL_LIFE,
    AssetService,
    get_asset_service,
)

# Service legacy (en memoire)
from .service import (
    AssetService as LegacyAssetService,
    create_asset_service as create_legacy_asset_service,
)

# Router
from .router import router

__all__ = [
    # Enums
    "AssetStatus",
    "AssetType",
    "DepreciationMethod",
    "DisposalType",
    "InsuranceStatus",
    "InventoryStatus",
    "MaintenanceStatus",
    "MaintenanceType",
    "MovementType",
    # Modeles
    "AssetCategory",
    "AssetDocument",
    "AssetInsuranceItem",
    "AssetInsurancePolicy",
    "AssetInventory",
    "AssetInventoryItem",
    "AssetMaintenance",
    "AssetMovement",
    "AssetTransfer",
    "AssetValuation",
    "DepreciationRun",
    "DepreciationSchedule",
    "FixedAsset",
    # Schemas
    "AssetAutocompleteItem",
    "AssetAutocompleteResponse",
    "AssetCategoryCreate",
    "AssetCategoryResponse",
    "AssetCategoryUpdate",
    "AssetDashboard",
    "AssetFilters",
    "AssetInsuranceItemCreate",
    "AssetInsurancePolicyCreate",
    "AssetInsurancePolicyResponse",
    "AssetInventoryCreate",
    "AssetInventoryItemResponse",
    "AssetInventoryItemUpdate",
    "AssetInventoryResponse",
    "AssetMaintenanceComplete",
    "AssetMaintenanceCreate",
    "AssetMaintenanceResponse",
    "AssetMaintenanceUpdate",
    "AssetMovementCreate",
    "AssetMovementResponse",
    "AssetStatistics",
    "AssetTransferCreate",
    "AssetTransferResponse",
    "AssetValuationResponse",
    "DepreciationRunCreate",
    "DepreciationRunResponse",
    "DepreciationScheduleEntryResponse",
    "DepreciationScheduleResponse",
    "DisposalResponse",
    "DisposeAssetRequest",
    "FixedAssetCreate",
    "FixedAssetResponse",
    "FixedAssetSummary",
    "FixedAssetUpdate",
    "PaginatedAssetResponse",
    "PaginatedMaintenanceResponse",
    "PaginatedMovementResponse",
    "PutInServiceRequest",
    # Exceptions
    "AssetAlreadyDisposedError",
    "AssetAlreadyInServiceError",
    "AssetCodeExistsError",
    "AssetHasComponentsError",
    "AssetLockedError",
    "AssetModuleError",
    "AssetNotFoundError",
    "AssetNotInServiceError",
    "CategoryCodeExistsError",
    "CategoryHasAssetsError",
    "CategoryHasChildrenError",
    "CategoryNotFoundError",
    "DateValidationError",
    "DepreciationAlreadyPostedError",
    "DepreciationCalculationError",
    "DepreciationRunNotFoundError",
    "DisposalDateBeforeAcquisitionError",
    "InServiceDateBeforeAcquisitionError",
    "InsurancePolicyExpiredError",
    "InsurancePolicyNotFoundError",
    "InventoryAlreadyCompletedError",
    "InventoryInProgressError",
    "InventoryItemNotFoundError",
    "InventoryNotFoundError",
    "InvalidDepreciationMethodError",
    "InvalidMovementAmountError",
    "MaintenanceAlreadyCompletedError",
    "MaintenanceInvalidStatusError",
    "MaintenanceNotFoundError",
    "MissingAccountError",
    "MovementAlreadyPostedError",
    "MovementNotFoundError",
    "OptimisticLockError",
    "PeriodClosedError",
    "TransferAlreadyCompletedError",
    "TransferInvalidDestinationError",
    "TransferNotFoundError",
    "UsefulLifeNotSetError",
    "ValidationError",
    # Repositories
    "AssetCategoryRepository",
    "AssetInsurancePolicyRepository",
    "AssetInventoryRepository",
    "AssetMaintenanceRepository",
    "AssetMovementRepository",
    "AssetTransferRepository",
    "DepreciationRunRepository",
    "DepreciationScheduleRepository",
    "FixedAssetRepository",
    # Service
    "ACCOUNTING_ACCOUNTS",
    "DECLINING_BALANCE_COEFFICIENTS",
    "RECOMMENDED_USEFUL_LIFE",
    "AssetService",
    "get_asset_service",
    "LegacyAssetService",
    "create_legacy_asset_service",
    # Router
    "router",
]
