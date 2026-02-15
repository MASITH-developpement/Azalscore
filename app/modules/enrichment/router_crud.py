"""
AZALS - Enrichment Router (CRUDRouter v3)
========================================

Router minimaliste utilisant CRUDRouter.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db

from app.modules.enrichment.schemas import (
    EnrichmentAcceptResponse,
    EnrichmentLookupResponse,
    EnrichmentHistoryResponse,
    EnrichmentStatsResponse,
    ProviderInfoResponse,
)
from app.modules.enrichment.service import EnrichmentService

# =============================================================================
# ROUTER PRINCIPAL
# =============================================================================

router = APIRouter(prefix="/enrichment", tags=["Enrichment"])


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/status")
async def get_module_status():
    """Statut du module Enrichment."""
    return {
        "module": "enrichment",
        "version": "v3",
        "status": "active"
    }


@router.get("/enrichmentaccepts", response_model=List[EnrichmentAcceptResponse])
async def list_enrichmentaccepts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Liste les enrichmentaccepts."""
    # TODO: Implementer avec service
    return []

@router.get("/enrichmentlookups", response_model=List[EnrichmentLookupResponse])
async def list_enrichmentlookups(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Liste les enrichmentlookups."""
    # TODO: Implementer avec service
    return []

@router.get("/enrichmenthistorys", response_model=List[EnrichmentHistoryResponse])
async def list_enrichmenthistorys(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Liste les enrichmenthistorys."""
    # TODO: Implementer avec service
    return []

