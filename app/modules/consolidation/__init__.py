"""
AZALS MODULE - CONSOLIDATION: Consolidation Comptable Multi-Entites
=====================================================================

Module complet de consolidation comptable pour groupes de societes.

FONCTIONNALITES:
- Perimetre de consolidation (filiales, participations)
- Methodes de consolidation:
  - Integration globale (controle >50%)
  - Integration proportionnelle (co-entreprises)
  - Mise en equivalence (influence notable 20-50%)
- Eliminations intra-groupe automatiques:
  - Titres vs capitaux propres
  - Creances/dettes intercompany
  - Ventes/achats internes
  - Dividendes intragroupes
  - Marges sur stocks internes
  - Plus-values sur immobilisations
- Conversion des devises (cloture, moyen, historique)
- Calcul des interets minoritaires
- Ecarts d'acquisition (goodwill)
- Retraitements de consolidation (IFRS 16, IAS 19, etc.)
- Reconciliation inter-societes
- Etats consolides:
  - Bilan consolide
  - Compte de resultat consolide
  - Tableau des flux de tresorerie
  - Variation des capitaux propres
- Liasse de consolidation
- Rapports reglementaires

NORMES SUPPORTEES:
- Reglement ANC 2020-01 (France)
- IFRS 10, 11, 12 (international)
- US GAAP ASC 810 (Etats-Unis)

CONFORMITE AZALSCORE:
- AZA-SEC-001: Isolation multi-tenant stricte (tenant_id obligatoire)
- AZA-NF-003: Module subordonné au noyau
- AZA-BE-003: Contrat backend avec audit complet

Auteur: AZALSCORE Team
Version: 2.0.0
Derniere mise a jour: 2026-02-21
"""

# Enumerations
from .models import (
    ConsolidationMethod,
    ControlType,
    CurrencyConversionMethod,
    EliminationType,
    AccountingStandard,
    ConsolidationStatus,
    PackageStatus,
    RestatementType,
    ReportType,
)

# Modeles
from .models import (
    ConsolidationPerimeter,
    ConsolidationEntity,
    Participation,
    ExchangeRate,
    Consolidation,
    ConsolidationPackage,
    EliminationEntry,
    Restatement,
    IntercompanyReconciliation,
    GoodwillCalculation,
    MinorityInterest,
    ConsolidatedReport,
    AccountMapping,
    ConsolidationAuditLog,
)

# Schemas
from .schemas import (
    # Perimetres
    ConsolidationPerimeterCreate,
    ConsolidationPerimeterUpdate,
    ConsolidationPerimeterResponse,
    PaginatedPerimeters,
    # Entites
    ConsolidationEntityCreate,
    ConsolidationEntityUpdate,
    ConsolidationEntityResponse,
    PaginatedEntities,
    EntityFilters,
    # Participations
    ParticipationCreate,
    ParticipationUpdate,
    ParticipationResponse,
    # Cours de change
    ExchangeRateCreate,
    ExchangeRateBulkCreate,
    ExchangeRateResponse,
    PaginatedExchangeRates,
    # Consolidations
    ConsolidationCreate,
    ConsolidationUpdate,
    ConsolidationResponse,
    PaginatedConsolidations,
    ConsolidationFilters,
    # Paquets
    ConsolidationPackageCreate,
    ConsolidationPackageUpdate,
    ConsolidationPackageResponse,
    PaginatedPackages,
    PackageFilters,
    TrialBalanceEntry,
    IntercompanyDetail,
    # Eliminations
    EliminationEntryCreate,
    EliminationEntryResponse,
    GenerateEliminationsRequest,
    GenerateEliminationsResponse,
    # Reconciliations
    IntercompanyReconciliationCreate,
    IntercompanyReconciliationResponse,
    ReconciliationSummary,
    ReconciliationFilters,
    # Rapports
    ConsolidatedReportResponse,
    GenerateReportRequest,
    # Dashboard
    ConsolidationDashboard,
    ConsolidationProgress,
)

# Repositories
from .repository import (
    ConsolidationPerimeterRepository,
    ConsolidationEntityRepository,
    ParticipationRepository,
    ExchangeRateRepository,
    ConsolidationRepository,
    ConsolidationPackageRepository,
    EliminationRepository,
    IntercompanyReconciliationRepository,
    ConsolidatedReportRepository,
    ConsolidationAuditLogRepository,
)

# Service
from .service import (
    ConsolidationService,
    create_consolidation_service,
)

# Router
from .router import router

# Exceptions
from .exceptions import (
    ConsolidationError,
    PerimeterNotFoundError,
    PerimeterDuplicateError,
    PerimeterClosedError,
    EntityNotFoundError,
    EntityDuplicateError,
    EntityCircularReferenceError,
    EntityOwnershipError,
    ParentEntityRequiredError,
    ParticipationNotFoundError,
    ParticipationDuplicateError,
    InvalidParticipationError,
    ConsolidationNotFoundError,
    ConsolidationDuplicateError,
    ConsolidationStatusError,
    ConsolidationValidationError,
    ConsolidationIncompleteError,
    PackageNotFoundError,
    PackageDuplicateError,
    PackageStatusError,
    PackageValidationError,
    PackageBalanceError,
    EliminationNotFoundError,
    EliminationValidationError,
    EliminationImbalanceError,
    RestatementNotFoundError,
    RestatementValidationError,
    ReconciliationNotFoundError,
    ReconciliationMismatchError,
    ExchangeRateNotFoundError,
    ExchangeRateDuplicateError,
    GoodwillCalculationError,
    GoodwillNotFoundError,
    ReportNotFoundError,
    ReportGenerationError,
    AccountMappingNotFoundError,
    AccountMappingDuplicateError,
    CurrencyConversionError,
    MissingExchangeRatesError,
    ConsolidationAccessDeniedError,
    TenantIsolationError,
)


__all__ = [
    # Enums
    "ConsolidationMethod",
    "ControlType",
    "CurrencyConversionMethod",
    "EliminationType",
    "AccountingStandard",
    "ConsolidationStatus",
    "PackageStatus",
    "RestatementType",
    "ReportType",
    # Models
    "ConsolidationPerimeter",
    "ConsolidationEntity",
    "Participation",
    "ExchangeRate",
    "Consolidation",
    "ConsolidationPackage",
    "EliminationEntry",
    "Restatement",
    "IntercompanyReconciliation",
    "GoodwillCalculation",
    "MinorityInterest",
    "ConsolidatedReport",
    "AccountMapping",
    "ConsolidationAuditLog",
    # Schemas
    "ConsolidationPerimeterCreate",
    "ConsolidationPerimeterUpdate",
    "ConsolidationPerimeterResponse",
    "PaginatedPerimeters",
    "ConsolidationEntityCreate",
    "ConsolidationEntityUpdate",
    "ConsolidationEntityResponse",
    "PaginatedEntities",
    "EntityFilters",
    "ParticipationCreate",
    "ParticipationUpdate",
    "ParticipationResponse",
    "ExchangeRateCreate",
    "ExchangeRateBulkCreate",
    "ExchangeRateResponse",
    "PaginatedExchangeRates",
    "ConsolidationCreate",
    "ConsolidationUpdate",
    "ConsolidationResponse",
    "PaginatedConsolidations",
    "ConsolidationFilters",
    "ConsolidationPackageCreate",
    "ConsolidationPackageUpdate",
    "ConsolidationPackageResponse",
    "PaginatedPackages",
    "PackageFilters",
    "TrialBalanceEntry",
    "IntercompanyDetail",
    "EliminationEntryCreate",
    "EliminationEntryResponse",
    "GenerateEliminationsRequest",
    "GenerateEliminationsResponse",
    "IntercompanyReconciliationCreate",
    "IntercompanyReconciliationResponse",
    "ReconciliationSummary",
    "ReconciliationFilters",
    "ConsolidatedReportResponse",
    "GenerateReportRequest",
    "ConsolidationDashboard",
    "ConsolidationProgress",
    # Repositories
    "ConsolidationPerimeterRepository",
    "ConsolidationEntityRepository",
    "ParticipationRepository",
    "ExchangeRateRepository",
    "ConsolidationRepository",
    "ConsolidationPackageRepository",
    "EliminationRepository",
    "IntercompanyReconciliationRepository",
    "ConsolidatedReportRepository",
    "ConsolidationAuditLogRepository",
    # Service
    "ConsolidationService",
    "create_consolidation_service",
    # Router
    "router",
    # Exceptions
    "ConsolidationError",
    "PerimeterNotFoundError",
    "PerimeterDuplicateError",
    "EntityNotFoundError",
    "EntityDuplicateError",
    "ConsolidationNotFoundError",
    "ConsolidationDuplicateError",
    "PackageNotFoundError",
    "ExchangeRateNotFoundError",
]

__version__ = "2.0.0"
__author__ = "AZALSCORE Team"
