"""
AZALSCORE Traceability Module
==============================

Module de traçabilité pour lots et numéros de série.

Fonctionnalités:
- Gestion des lots (batch tracking)
- Numéros de série (individual tracking)
- Dates d'expiration
- Traçabilité amont/aval
- Gestion des rappels
- Mouvements avec traçabilité

Usage:
    from app.modules.production.traceability import TraceabilityService

    service = TraceabilityService(db, tenant_id)
    lot = await service.create_lot(product_id, quantity, expiry_date)
    serial = await service.create_serial(product_id, lot_id)
"""

from .service import (
    TraceabilityService,
    Lot,
    SerialNumber,
    TraceabilityMovement,
    LotStatus,
    SerialStatus,
    MovementType,
)
from .router import router as traceability_router

__all__ = [
    "TraceabilityService",
    "Lot",
    "SerialNumber",
    "TraceabilityMovement",
    "LotStatus",
    "SerialStatus",
    "MovementType",
    "traceability_router",
]
