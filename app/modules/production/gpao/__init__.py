"""
AZALSCORE GPAO/MRP Module
==========================

Module de Gestion de Production Assistée par Ordinateur.

Fonctionnalités:
- Ordres de fabrication (OF)
- Nomenclatures (BOM)
- Gammes de fabrication
- Calcul des besoins (MRP)
- Planification de capacité
- Suivi de production

Usage:
    from app.modules.production.gpao import GPAOService

    service = GPAOService(db, tenant_id)
    of = await service.create_manufacturing_order(product_id, quantity)
    mrp = await service.calculate_requirements(product_id, quantity, due_date)
"""

from .service import (
    GPAOService,
    ManufacturingOrder,
    BillOfMaterials,
    BOMComponent,
    RoutingOperation,
    MRPRequirement,
    ProductionStatus,
    OperationType,
)
from .router import router as gpao_router

__all__ = [
    "GPAOService",
    "ManufacturingOrder",
    "BillOfMaterials",
    "BOMComponent",
    "RoutingOperation",
    "MRPRequirement",
    "ProductionStatus",
    "OperationType",
    "gpao_router",
]
