"""
AZALS API V3 - CRUDRouter Edition
==================================

Routers unifies sous /v3/ pour compatibilite frontend.
"""

from fastapi import APIRouter

# Import des routers modules
from app.modules.commercial.router_crud import router as commercial_router
from app.modules.projects.router_crud import router as projects_router
from app.modules.accounting.router_unified import router as accounting_router
from app.api.cockpit import router as cockpit_router

# Router V3 parent
router = APIRouter(prefix="/v3", tags=["API V3"])

# Monter les sous-routers
router.include_router(commercial_router)
router.include_router(projects_router)
router.include_router(accounting_router)
router.include_router(cockpit_router)

# Interventions (optionnel)
try:
    from app.modules.interventions.router_crud import router as interventions_router
    router.include_router(interventions_router)
except ImportError:
    pass

# Enrichment (optionnel)
try:
    from app.modules.enrichment.router import router as enrichment_router
    router.include_router(enrichment_router)
except ImportError:
    pass
