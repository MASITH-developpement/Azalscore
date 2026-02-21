"""
Module Fleet Management - GAP-062

Gestion complete de flotte de vehicules:
- Inventaire vehicules
- Affectation conducteurs
- Contrats (leasing, assurance, entretien)
- Suivi kilometrique
- Consommation carburant
- Maintenance preventive et corrective
- Controles techniques
- Amendes et sinistres
- Calcul TCO (Total Cost of Ownership)
- Alertes echeances
- Dashboard et rapports
"""

from .models import (
    # Enumerations
    VehicleType,
    VehicleStatus,
    FuelType,
    ContractType,
    ContractStatus,
    MaintenanceType,
    MaintenanceStatus,
    DocumentType,
    AlertType,
    AlertSeverity,
    IncidentType,
    IncidentStatus,

    # Models SQLAlchemy
    FleetVehicle,
    FleetDriver,
    FleetContract,
    FleetMileageLog,
    FleetFuelEntry,
    FleetMaintenance,
    FleetDocument,
    FleetIncident,
    FleetCost,
    FleetAlert,
)

from .schemas import (
    # Vehicle schemas
    VehicleCreate,
    VehicleUpdate,
    VehicleResponse,
    VehicleList,
    VehicleFilters,

    # Driver schemas
    DriverCreate,
    DriverUpdate,
    DriverResponse,
    DriverList,
    DriverFilters,

    # Contract schemas
    ContractCreate,
    ContractUpdate,
    ContractResponse,
    ContractList,
    ContractFilters,

    # Maintenance schemas
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceResponse,
    MaintenanceList,
    MaintenanceFilters,

    # Fuel schemas
    FuelEntryCreate,
    FuelEntryResponse,
    FuelEntryList,

    # Document schemas
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentList,

    # Incident schemas
    IncidentCreate,
    IncidentUpdate,
    IncidentResponse,
    IncidentList,
    IncidentFilters,

    # Alert schemas
    AlertResponse,
    AlertList,
    AlertFilters,

    # Dashboard/Reports
    FleetDashboard,
    TCOReport,
    ConsumptionStats,
)

from .repository import (
    VehicleRepository,
    DriverRepository,
    ContractRepository,
    FuelEntryRepository,
    MaintenanceRepository,
    DocumentRepository,
    IncidentRepository,
    CostRepository,
    AlertRepository,
    MileageLogRepository,
)

from .service import (
    FleetService,
    create_fleet_service,
)

from .router import router

from .exceptions import (
    FleetError,
    VehicleNotFoundError,
    VehicleDuplicateError,
    VehicleValidationError,
    VehicleStateError,
    DriverNotFoundError,
    DriverDuplicateError,
    DriverLicenseExpiredError,
    ContractNotFoundError,
    ContractDuplicateError,
    MaintenanceNotFoundError,
    MaintenanceDuplicateError,
    MaintenanceStateError,
    FuelEntryNotFoundError,
    FuelAnomalyError,
    DocumentNotFoundError,
    IncidentNotFoundError,
    IncidentDuplicateError,
    AlertNotFoundError,
    MileageDecrementError,
)

__all__ = [
    # Enums
    "VehicleType",
    "VehicleStatus",
    "FuelType",
    "ContractType",
    "ContractStatus",
    "MaintenanceType",
    "MaintenanceStatus",
    "DocumentType",
    "AlertType",
    "AlertSeverity",
    "IncidentType",
    "IncidentStatus",

    # Models
    "FleetVehicle",
    "FleetDriver",
    "FleetContract",
    "FleetMileageLog",
    "FleetFuelEntry",
    "FleetMaintenance",
    "FleetDocument",
    "FleetIncident",
    "FleetCost",
    "FleetAlert",

    # Schemas
    "VehicleCreate",
    "VehicleUpdate",
    "VehicleResponse",
    "VehicleList",
    "VehicleFilters",
    "DriverCreate",
    "DriverUpdate",
    "DriverResponse",
    "DriverList",
    "DriverFilters",
    "ContractCreate",
    "ContractUpdate",
    "ContractResponse",
    "ContractList",
    "ContractFilters",
    "MaintenanceCreate",
    "MaintenanceUpdate",
    "MaintenanceResponse",
    "MaintenanceList",
    "MaintenanceFilters",
    "FuelEntryCreate",
    "FuelEntryResponse",
    "FuelEntryList",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentList",
    "IncidentCreate",
    "IncidentUpdate",
    "IncidentResponse",
    "IncidentList",
    "IncidentFilters",
    "AlertResponse",
    "AlertList",
    "AlertFilters",
    "FleetDashboard",
    "TCOReport",
    "ConsumptionStats",

    # Repositories
    "VehicleRepository",
    "DriverRepository",
    "ContractRepository",
    "FuelEntryRepository",
    "MaintenanceRepository",
    "DocumentRepository",
    "IncidentRepository",
    "CostRepository",
    "AlertRepository",
    "MileageLogRepository",

    # Service
    "FleetService",
    "create_fleet_service",

    # Router
    "router",

    # Exceptions
    "FleetError",
    "VehicleNotFoundError",
    "VehicleDuplicateError",
    "VehicleValidationError",
    "VehicleStateError",
    "DriverNotFoundError",
    "DriverDuplicateError",
    "DriverLicenseExpiredError",
    "ContractNotFoundError",
    "ContractDuplicateError",
    "MaintenanceNotFoundError",
    "MaintenanceDuplicateError",
    "MaintenanceStateError",
    "FuelEntryNotFoundError",
    "FuelAnomalyError",
    "DocumentNotFoundError",
    "IncidentNotFoundError",
    "IncidentDuplicateError",
    "AlertNotFoundError",
    "MileageDecrementError",
]
