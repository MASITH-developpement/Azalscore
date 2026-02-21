"""
Module Field Service / Service Terrain - GAP-081

Gestion des interventions terrain:
- Ordres de travail
- Techniciens et équipes
- Planification et dispatch
- Suivi GPS et géolocalisation
- Pièces détachées et stock mobile
- Signatures et photos
- Rapports d'intervention
"""

from .service import (
    # Énumérations (service)
    PartUsageType,

    # Data classes
    FSSkill as SkillData,
    TechnicianSkill,
    FSTechnician as TechnicianData,
    FSServiceZone as ServiceZoneData,
    FSCustomerSite as CustomerSiteData,
    WorkOrderLine,
    PartUsage,
    TimeEntry,
    Attachment,
    FSWorkOrder as WorkOrderData,
    Route,
    MobileInventory,
    ServiceReport,
    DispatchStats,

    # Service
    FieldService,
    create_field_service,
)

# Models SQLAlchemy
from .models import (
    FSWorkOrder,
    FSTechnician,
    FSCustomerSite,
    FSServiceZone,
    FSSkill,
    WorkOrderStatus,
    TechnicianStatus,
    Priority,
    WorkOrderType,
    SkillLevel,
)

# Repositories
from .repository import (
    WorkOrderRepository,
    TechnicianRepository,
    CustomerSiteRepository,
    ServiceZoneRepository,
)

# Exceptions
from .exceptions import (
    FieldServiceError,
    WorkOrderNotFoundError,
    WorkOrderDuplicateError,
    WorkOrderValidationError,
    WorkOrderStateError,
    TechnicianNotFoundError,
    TechnicianDuplicateError,
    TechnicianValidationError,
    TechnicianUnavailableError,
    CustomerSiteNotFoundError,
    CustomerSiteDuplicateError,
    ServiceZoneNotFoundError,
    ServiceZoneDuplicateError,
    SkillNotFoundError,
    SkillDuplicateError,
    DispatchError,
    SchedulingError,
)

# Router
from .router import router

__all__ = [
    # Enums
    "WorkOrderType",
    "WorkOrderStatus",
    "TechnicianStatus",
    "Priority",
    "SkillLevel",
    "PartUsageType",
    # Models SQLAlchemy
    "FSWorkOrder",
    "FSTechnician",
    "FSCustomerSite",
    "FSServiceZone",
    "FSSkill",
    # Repositories
    "WorkOrderRepository",
    "TechnicianRepository",
    "CustomerSiteRepository",
    "ServiceZoneRepository",
    # Data classes (service)
    "SkillData",
    "TechnicianSkill",
    "TechnicianData",
    "ServiceZoneData",
    "CustomerSiteData",
    "WorkOrderLine",
    "PartUsage",
    "TimeEntry",
    "Attachment",
    "WorkOrderData",
    "Route",
    "MobileInventory",
    "ServiceReport",
    "DispatchStats",
    # Service
    "FieldService",
    "create_field_service",
    # Exceptions
    "FieldServiceError",
    "WorkOrderNotFoundError",
    "WorkOrderDuplicateError",
    "WorkOrderValidationError",
    "WorkOrderStateError",
    "TechnicianNotFoundError",
    "TechnicianDuplicateError",
    "TechnicianValidationError",
    "TechnicianUnavailableError",
    "CustomerSiteNotFoundError",
    "CustomerSiteDuplicateError",
    "ServiceZoneNotFoundError",
    "ServiceZoneDuplicateError",
    "SkillNotFoundError",
    "SkillDuplicateError",
    "DispatchError",
    "SchedulingError",
    # Router
    "router",
]
