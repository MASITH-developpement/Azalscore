"""
AZALS - Enrichment Router (CRUDRouter v3)
========================================

Router minimaliste utilisant CRUDRouter.
"""
from __future__ import annotations


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


@router.get("/history", response_model=List[EnrichmentHistoryResponse])
async def list_enrichment_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Liste l'historique des enrichissements."""
    service = EnrichmentService(db, context.tenant_id)
    offset = (page - 1) * page_size
    history_list, _ = service.get_history(limit=page_size, offset=offset)
    return [EnrichmentHistoryResponse.from_orm_custom(h) for h in history_list]

