"""
AZALS - Odoo Import Router (CRUDRouter v3)
=========================================

Router minimaliste utilisant CRUDRouter.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db

from app.modules.odoo_import.schemas import (
    OdooConnectionConfigCreate,
    OdooConnectionConfigUpdate,
    OdooConnectionConfigResponse,
    OdooTestConnectionResponse,
    OdooImportHistoryResponse,
    OdooFieldMappingCreate,
    OdooFieldMappingResponse,
    OdooDataPreviewResponse,
)
from app.modules.odoo_import.service import OdooImportService

# =============================================================================
# ROUTER PRINCIPAL
# =============================================================================

router = APIRouter(prefix="/odoo_import", tags=["Odoo Import"])


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/status")
async def get_module_status():
    """Statut du module Odoo Import."""
    return {
        "module": "odoo_import",
        "version": "v3",
        "status": "active"
    }


@router.get("/configs", response_model=List[OdooConnectionConfigResponse])
async def list_connection_configs(
    active_only: bool = Query(False, description="Filtrer les configs actives uniquement"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Liste les configurations de connexion Odoo."""
    service = OdooImportService(db, context.tenant_id)
    return service.list_configs(active_only=active_only)


@router.get("/history", response_model=List[OdooImportHistoryResponse])
async def list_import_history(
    config_id: Optional[UUID] = Query(None, description="Filtrer par config"),
    limit: int = Query(50, ge=1, le=200),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Liste l'historique des imports Odoo."""
    service = OdooImportService(db, context.tenant_id)
    return service.get_import_history(config_id=config_id, limit=limit)

