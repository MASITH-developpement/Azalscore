"""
Module Manufacturing / Fabrication - GAP-077
=============================================

Gestion complète de la fabrication:
- Nomenclatures (BOM) avec explosion multi-niveaux
- Ordres de fabrication avec workflow complet
- Gammes opératoires et routage
- Postes de travail et planification
- Suivi de production en temps réel
- Contrôles qualité intégrés
- Calcul des coûts de production
- Statistiques et KPIs
"""

# === Modèles SQLAlchemy ===
from .models import (
    # Énumérations
    BOMType,
    BOMStatus,
    WorkcenterType,
    WorkcenterState,
    WorkOrderStatus,
    OperationStatus,
    QualityCheckType,
    QualityResult,
    # Modèles
    BOM,
    ManufacturingBOMLine,
    Workcenter,
    Routing,
    Operation,
    WorkOrder,
    WorkOrderOperation,
    QualityCheck,
    ProductionLog,
)

# === Schémas Pydantic ===
from .schemas import (
    # BOM
    BOMCreate,
    BOMUpdate,
    BOMResponse,
    BOMListItem,
    BOMListResponse,
    BOMFilters,
    BOMLineCreate,
    BOMLineUpdate,
    BOMLineResponse,
    BOMExplodeItem,
    BOMExplodeResponse,
    # Workcenter
    WorkcenterCreate,
    WorkcenterUpdate,
    WorkcenterResponse,
    WorkcenterListItem,
    WorkcenterListResponse,
    WorkcenterFilters,
    # Routing
    RoutingCreate,
    RoutingUpdate,
    RoutingResponse,
    RoutingListItem,
    RoutingListResponse,
    OperationCreate,
    OperationUpdate,
    OperationResponse,
    # Work Order
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderResponse,
    WorkOrderListItem,
    WorkOrderListResponse,
    WorkOrderFilters,
    WorkOrderOperationResponse,
    RecordProductionRequest,
    StartOperationRequest,
    CompleteOperationRequest,
    # Quality
    QualityCheckCreate,
    QualityCheckUpdate,
    QualityCheckResponse,
    QualitySpecification,
    # Production Log
    ProductionLogCreate,
    ProductionLogResponse,
    # Common
    AutocompleteItem,
    AutocompleteResponse,
    BulkCreateRequest,
    BulkUpdateRequest,
    BulkDeleteRequest,
    BulkResult,
    ProductionStats,
)

# === Exceptions ===
from .exceptions import (
    ManufacturingError,
    BOMNotFoundError,
    BOMDuplicateError,
    BOMValidationError,
    BOMStateError,
    BOMLineNotFoundError,
    WorkcenterNotFoundError,
    WorkcenterDuplicateError,
    WorkcenterValidationError,
    WorkcenterBusyError,
    RoutingNotFoundError,
    RoutingDuplicateError,
    RoutingValidationError,
    OperationNotFoundError,
    WorkOrderNotFoundError,
    WorkOrderDuplicateError,
    WorkOrderValidationError,
    WorkOrderStateError,
    WorkOrderOperationNotFoundError,
    WorkOrderOperationStateError,
    QualityCheckNotFoundError,
    QualityCheckValidationError,
    ProductionLogValidationError,
)

# === Repository ===
from .repository import (
    BOMRepository,
    WorkcenterRepository,
    RoutingRepository,
    WorkOrderRepository,
    QualityCheckRepository,
    ProductionLogRepository,
)

# === Service ===
from .service import ManufacturingService, create_manufacturing_service

# === Router ===
from .router import router

__all__ = [
    # Énumérations
    "BOMType",
    "BOMStatus",
    "WorkcenterType",
    "WorkcenterState",
    "WorkOrderStatus",
    "OperationStatus",
    "QualityCheckType",
    "QualityResult",
    # Modèles
    "BOM",
    "ManufacturingBOMLine",
    "Workcenter",
    "Routing",
    "Operation",
    "WorkOrder",
    "WorkOrderOperation",
    "QualityCheck",
    "ProductionLog",
    # Schémas BOM
    "BOMCreate",
    "BOMUpdate",
    "BOMResponse",
    "BOMListItem",
    "BOMListResponse",
    "BOMFilters",
    "BOMLineCreate",
    "BOMLineUpdate",
    "BOMLineResponse",
    "BOMExplodeItem",
    "BOMExplodeResponse",
    # Schémas Workcenter
    "WorkcenterCreate",
    "WorkcenterUpdate",
    "WorkcenterResponse",
    "WorkcenterListItem",
    "WorkcenterListResponse",
    "WorkcenterFilters",
    # Schémas Routing
    "RoutingCreate",
    "RoutingUpdate",
    "RoutingResponse",
    "RoutingListItem",
    "RoutingListResponse",
    "OperationCreate",
    "OperationUpdate",
    "OperationResponse",
    # Schémas Work Order
    "WorkOrderCreate",
    "WorkOrderUpdate",
    "WorkOrderResponse",
    "WorkOrderListItem",
    "WorkOrderListResponse",
    "WorkOrderFilters",
    "WorkOrderOperationResponse",
    "RecordProductionRequest",
    "StartOperationRequest",
    "CompleteOperationRequest",
    # Schémas Quality
    "QualityCheckCreate",
    "QualityCheckUpdate",
    "QualityCheckResponse",
    "QualitySpecification",
    # Schémas Production Log
    "ProductionLogCreate",
    "ProductionLogResponse",
    # Common
    "AutocompleteItem",
    "AutocompleteResponse",
    "BulkCreateRequest",
    "BulkUpdateRequest",
    "BulkDeleteRequest",
    "BulkResult",
    "ProductionStats",
    # Exceptions
    "ManufacturingError",
    "BOMNotFoundError",
    "BOMDuplicateError",
    "BOMValidationError",
    "BOMStateError",
    "BOMLineNotFoundError",
    "WorkcenterNotFoundError",
    "WorkcenterDuplicateError",
    "WorkcenterValidationError",
    "WorkcenterBusyError",
    "RoutingNotFoundError",
    "RoutingDuplicateError",
    "RoutingValidationError",
    "OperationNotFoundError",
    "WorkOrderNotFoundError",
    "WorkOrderDuplicateError",
    "WorkOrderValidationError",
    "WorkOrderStateError",
    "WorkOrderOperationNotFoundError",
    "WorkOrderOperationStateError",
    "QualityCheckNotFoundError",
    "QualityCheckValidationError",
    "ProductionLogValidationError",
    # Repository
    "BOMRepository",
    "WorkcenterRepository",
    "RoutingRepository",
    "WorkOrderRepository",
    "QualityCheckRepository",
    "ProductionLogRepository",
    # Service
    "ManufacturingService",
    "create_manufacturing_service",
    # Router
    "router",
]
