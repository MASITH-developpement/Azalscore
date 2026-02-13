"""
AZALS API - Decisions v2 (CORE SaaS)
=====================================

Endpoints de classification decisionnelle - Version CORE SaaS.

MIGRATION CORE SaaS (Phase 2.2):
- Utilise get_saas_context() au lieu de get_current_user_and_tenant()
- SaaSContext fournit tenant_id + user_id directement
- Audit automatique via CoreAuthMiddleware
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext
from app.core.models import DecisionLevel
from app.services.decision import DecisionService

router = APIRouter(prefix="/v2/decision", tags=["Decision v2 - CORE SaaS"])


# ============================================================================
# SCHEMAS
# ============================================================================

class ClassifyRequest(BaseModel):
    """Requete de classification decisionnelle."""
    entity_type: str
    entity_id: str
    level: DecisionLevel
    reason: str


class DecisionResponse(BaseModel):
    """Reponse de classification."""
    id: UUID | int
    tenant_id: str
    entity_type: str
    entity_id: str
    level: DecisionLevel
    reason: str
    created_at: str

    model_config = {"from_attributes": True}


class DecisionStatusResponse(BaseModel):
    """Statut decisionnel d'une entite."""
    entity_type: str
    entity_id: str
    level: DecisionLevel | None = None
    reason: str | None = None
    created_at: str | None = None
    is_red: bool = False


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/classify", response_model=DecisionResponse)
async def classify_decision(
    request: ClassifyRequest,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Cree une decision de classification pour une entite.

    CORE SaaS: Utilise context.tenant_id et context.user_id.

    Regles:
    - GREEN -> ORANGE : autorise
    - ORANGE -> RED : autorise
    - RED -> * : INTERDIT (403)

    Toute decision RED est automatiquement journalisee.
    """
    try:
        decision = DecisionService.classify(
            db=db,
            tenant_id=context.tenant_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            level=request.level,
            reason=request.reason,
            user_id=str(context.user_id)
        )

        return DecisionResponse(
            id=decision.id,
            tenant_id=decision.tenant_id,
            entity_type=decision.entity_type,
            entity_id=decision.entity_id,
            level=decision.level,
            reason=decision.reason,
            created_at=decision.created_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/status/{entity_type}/{entity_id}", response_model=DecisionStatusResponse)
async def get_decision_status(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Recupere le statut decisionnel actuel d'une entite.

    CORE SaaS: Utilise context.tenant_id pour l'isolation.
    """
    current_decision = DecisionService.get_current_decision(
        db=db,
        tenant_id=context.tenant_id,
        entity_type=entity_type,
        entity_id=entity_id
    )

    if not current_decision:
        return DecisionStatusResponse(
            entity_type=entity_type,
            entity_id=entity_id,
            level=None,
            reason=None,
            is_red=False
        )

    return DecisionStatusResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        level=current_decision.level,
        reason=current_decision.reason,
        created_at=current_decision.created_at.isoformat(),
        is_red=current_decision.level == DecisionLevel.RED
    )
