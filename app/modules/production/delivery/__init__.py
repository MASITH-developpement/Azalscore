"""
AZALSCORE Delivery Notes Module
================================

Module de gestion des bons de livraison.

Fonctionnalités:
- Création de bons de livraison
- Listes de préparation (picking)
- Gestion des expéditions
- Preuve de livraison
- Gestion des retours

Usage:
    from app.modules.production.delivery import DeliveryService

    service = DeliveryService(db, tenant_id)
    note = await service.create_delivery_note(order_id, items)
    shipment = await service.ship(note.id, carrier, tracking)
"""

from .service import (
    DeliveryService,
    DeliveryNote,
    DeliveryLine,
    PickingList,
    Shipment,
    DeliveryStatus,
    ShipmentStatus,
)
from .router import router as delivery_router

__all__ = [
    "DeliveryService",
    "DeliveryNote",
    "DeliveryLine",
    "PickingList",
    "Shipment",
    "DeliveryStatus",
    "ShipmentStatus",
    "delivery_router",
]
