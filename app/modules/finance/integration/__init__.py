"""
AZALSCORE Finance Integration Module
=====================================

Module d'intégration entre Finance et les autres modules métier.

Fonctionnalités:
- Synchronisation Finance ↔ Comptabilité
- Synchronisation Finance ↔ Facturation
- Règles de mapping automatiques
- Validation croisée des écritures

Usage:
    from app.modules.finance.integration import FinanceIntegrationService

    service = FinanceIntegrationService(db, tenant_id)
    await service.sync_to_accounting(transaction_id)
"""

from .service import (
    FinanceIntegrationService,
    IntegrationMapping,
    SyncResult,
    SyncDirection,
    SyncStatus,
)
from .router import router as integration_router

__all__ = [
    "FinanceIntegrationService",
    "IntegrationMapping",
    "SyncResult",
    "SyncDirection",
    "SyncStatus",
    "integration_router",
]
