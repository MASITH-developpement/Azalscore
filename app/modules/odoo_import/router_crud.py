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


@router.get("/odooconnectionconfigs", response_model=List[OdooConnectionConfigResponse])
async def list_odooconnectionconfigs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Liste les odooconnectionconfigs."""
    # TODO: Implementer avec service
    return []

@router.get("/odootestconnections", response_model=List[OdooTestConnectionResponse])
async def list_odootestconnections(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Liste les odootestconnections."""
    # TODO: Implementer avec service
    return []

@router.get("/odooimporthistorys", response_model=List[OdooImportHistoryResponse])
async def list_odooimporthistorys(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Liste les odooimporthistorys."""
    # TODO: Implementer avec service
    return []

