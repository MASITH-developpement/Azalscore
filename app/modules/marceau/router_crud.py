"""
AZALS - Marceau Router (CRUDRouter)
====================================

Router minimaliste utilisant CRUDRouter.
Agent IA Marceau - Endpoints API.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.azals import CRUDRouter, SaaSContext, get_context, get_db, PaginatedResponse

from app.modules.marceau.service_v2 import (
    MarceauConfigService,
    MarceauActionService,
    MarceauConversationService,
    MarceauKnowledgeService,
    MarceauScheduledTaskService,
)
from app.modules.marceau.schemas import (
    MarceauConfigCreate,
    MarceauConfigUpdate,
    MarceauConfigResponse,
    MarceauActionCreate,
    MarceauActionResponse,
    MarceauConversationResponse,
    ActionValidationRequest,
    ConversationStatsResponse,
)

# =============================================================================
# ROUTERS CRUD AUTO-GENERES
# =============================================================================

config_router = CRUDRouter.create_crud_router(
    service_class=MarceauConfigService,
    resource_name="config",
    plural_name="configs",
    create_schema=MarceauConfigCreate,
    update_schema=MarceauConfigUpdate,
    response_schema=MarceauConfigResponse,
    tags=["Marceau - Configuration"],
)

actions_router = CRUDRouter.create_crud_router(
    service_class=MarceauActionService,
    resource_name="action",
    plural_name="actions",
    create_schema=MarceauActionCreate,
    update_schema=MarceauActionCreate,
    response_schema=MarceauActionResponse,
    tags=["Marceau - Actions"],
)

# =============================================================================
# ROUTER PRINCIPAL
# =============================================================================

router = APIRouter(prefix="/marceau", tags=["Marceau"])

router.include_router(config_router, prefix="/config")
router.include_router(actions_router, prefix="/actions")

# =============================================================================
# ENDPOINTS METIER PERSONNALISES
# =============================================================================

# --- Configuration ---

@router.get("/config", response_model=MarceauConfigResponse)
async def get_config(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Recupere ou cree la configuration Marceau du tenant."""
    service = MarceauConfigService(db, context)
    return service.get_or_create_config()


# --- Actions ---

@router.get("/actions/pending-validation", response_model=List[MarceauActionResponse])
async def list_pending_actions(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Liste les actions en attente de validation humaine."""
    service = MarceauActionService(db, context)
    return service.list_pending_validation()


@router.post("/actions/{action_id}/validate", response_model=MarceauActionResponse)
async def validate_action(
    action_id: UUID,
    request: ActionValidationRequest,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Valide ou rejette une action Marceau."""
    service = MarceauActionService(db, context)
    result = service.validate_action(
        action_id,
        request.approved,
        UUID(context.user_id),
        request.notes
    )
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


# --- Conversations ---

@router.get("/conversations", response_model=List[MarceauConversationResponse])
async def list_conversations(
    limit: int = Query(50, ge=1, le=200),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Liste les conversations recentes."""
    service = MarceauConversationService(db, context)
    return service.list_recent(limit=limit)


@router.get("/conversations/{conversation_id}", response_model=MarceauConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Recupere une conversation par ID."""
    service = MarceauConversationService(db, context)
    result = service.get_or_fail(conversation_id)
    if not result.success:
        raise HTTPException(status_code=404, detail=result.error)
    return result.data


@router.get("/conversations/stats", response_model=ConversationStatsResponse)
async def get_conversation_stats(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Calcule les statistiques des conversations."""
    service = MarceauConversationService(db, context)
    return service.get_stats()


# --- Knowledge Base ---

@router.get("/knowledge/search")
async def search_knowledge(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Recherche dans la base de connaissances."""
    service = MarceauKnowledgeService(db, context)
    return service.search(q, limit=limit)


# --- Scheduled Tasks ---

@router.get("/tasks/active")
async def list_active_tasks(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Liste les taches planifiees actives."""
    service = MarceauScheduledTaskService(db, context)
    return service.list_active()
