"""
AZALS ERP - Module M8: Maintenance (Asset Management / GMAO)
============================================================

Module de gestion de la maintenance et des actifs pour l'ERP AZALS.
GMAO - Gestion de Maintenance Assistée par Ordinateur.

Fonctionnalités:
- Gestion des équipements et actifs
- Maintenance préventive (planifiée)
- Maintenance corrective (curative)
- Ordres de travail (Work Orders)
- Planning et calendrier de maintenance
- Gestion des pièces de rechange
- Historique des interventions
- Indicateurs de performance (MTBF, MTTR, disponibilité)
- Gestion des contrats de maintenance
- Suivi des coûts de maintenance

Auteur: AZALS Team
Version: 1.0.0
"""

__version__ = "1.0.0"
__module_code__ = "M8"
__module_name__ = "Maintenance - Asset Management (GMAO)"
__dependencies__ = ["T0", "T5", "M5", "M6"]

from app.modules.maintenance.models import (
    AssetCategory,
    AssetStatus,
    AssetCriticality,
    MaintenanceType,
    WorkOrderStatus,
    WorkOrderPriority,
    FailureType,
    PartRequestStatus,
    ContractType,
    ContractStatus,
    Asset,
    AssetComponent,
    AssetDocument,
    AssetMeter,
    MeterReading,
    MaintenancePlan,
    MaintenancePlanTask,
    WorkOrder,
    WorkOrderTask,
    WorkOrderLabor,
    WorkOrderPart,
    Failure,
    FailureCause,
    SparePart,
    SparePartStock,
    PartRequest,
    MaintenanceContract,
    MaintenanceKPI,
)

__all__ = [
    # Enums
    "AssetCategory",
    "AssetStatus",
    "AssetCriticality",
    "MaintenanceType",
    "WorkOrderStatus",
    "WorkOrderPriority",
    "FailureType",
    "PartRequestStatus",
    "ContractType",
    "ContractStatus",
    # Models
    "Asset",
    "AssetComponent",
    "AssetDocument",
    "AssetMeter",
    "MeterReading",
    "MaintenancePlan",
    "MaintenancePlanTask",
    "WorkOrder",
    "WorkOrderTask",
    "WorkOrderLabor",
    "WorkOrderPart",
    "Failure",
    "FailureCause",
    "SparePart",
    "SparePartStock",
    "PartRequest",
    "MaintenanceContract",
    "MaintenanceKPI",
]
