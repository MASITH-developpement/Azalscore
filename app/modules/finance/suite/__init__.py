"""
AZALSCORE Finance Suite - Orchestrateur Central
================================================

Module orchestrateur pour la suite Finance complète.

Fonctionnalités:
- Vue unifiée de tous les modules finance
- Tableau de bord consolidé
- Workflows cross-modules
- Configuration centralisée
- Health check global

Usage:
    from app.modules.finance.suite import FinanceSuiteService

    service = FinanceSuiteService(db, tenant_id)
    dashboard = await service.get_dashboard()
    health = await service.get_health_status()
"""

from .service import (
    FinanceSuiteService,
    FinanceDashboard,
    ModuleStatus,
    SuiteConfig,
)
from .router import router as suite_router

__all__ = [
    "FinanceSuiteService",
    "FinanceDashboard",
    "ModuleStatus",
    "SuiteConfig",
    "suite_router",
]
