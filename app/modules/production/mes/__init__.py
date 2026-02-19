"""
AZALSCORE MES Module
====================

Module MES Léger (Manufacturing Execution System).

Fonctionnalités:
- Gestion des postes de travail et machines
- Suivi des opérations en temps réel
- Temps de cycle et productivité
- Contrôles qualité en ligne
- Suivi des opérateurs
- OEE (Overall Equipment Effectiveness)
- Gestion des arrêts

Usage:
    from app.modules.production.mes import MESService

    service = MESService(db, tenant_id)
    workstation = await service.create_workstation(data)
    operation = await service.start_operation(workstation_id, order_id, operator_id)
"""

from .service import (
    MESService,
    Workstation,
    WorkstationStatus,
    ProductionOperation,
    OperationStatus,
    TimeEntry,
    QualityCheck,
    Downtime,
    DowntimeReason,
    OEEMetrics,
)
from .router import router as mes_router

__all__ = [
    "MESService",
    "Workstation",
    "WorkstationStatus",
    "ProductionOperation",
    "OperationStatus",
    "TimeEntry",
    "QualityCheck",
    "Downtime",
    "DowntimeReason",
    "OEEMetrics",
    "mes_router",
]
