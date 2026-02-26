"""
AZALSCORE WMS Module
====================

Module de gestion d'entrepôt (Warehouse Management System).

Fonctionnalités:
- Gestion des emplacements (zones, allées, étagères, bins)
- Mouvements de stock (réception, transfert, picking)
- Inventaires et comptages
- Réapprovisionnement automatique
- Vagues de préparation (wave picking)
- Optimisation des trajets

Usage:
    from app.modules.production.wms import WMSService

    service = WMSService(db, tenant_id)
    location = await service.create_location(warehouse_id, data)
    movement = await service.transfer(from_loc, to_loc, product_id, qty)
"""

from .service import (
    WMSService,
    Warehouse,
    Location,
    StockMovement,
    InventoryCount,
    WavePick,
    LocationType,
    MovementType,
)
from .router import router as wms_router

__all__ = [
    "WMSService",
    "Warehouse",
    "Location",
    "StockMovement",
    "InventoryCount",
    "WavePick",
    "LocationType",
    "MovementType",
    "wms_router",
]
