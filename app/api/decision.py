"""
AZALS - API Décisions
Endpoints de classification décisionnelle protégés JWT + tenant
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_and_tenant
from app.core.models import DecisionLevel
from app.services.decision import DecisionService

router = APIRouter(prefix="/decision", tags=["decision"])


class ClassifyRequest(BaseModel):
    """
    Requête de classification décisionnelle.
    """
    entity_type: str
    entity_id: str
    level: DecisionLevel
    reason: str


class DecisionResponse(BaseModel):
    """
    Réponse de classification.
    """
    id: int
    tenant_id: str
    entity_type: str
    entity_id: str
    level: DecisionLevel
    reason: str
    created_at: str

    model_config = {"from_attributes": True}


@router.post("/classify", response_model=DecisionResponse)
async def classify_decision(
    request: ClassifyRequest,
    db: Session = Depends(get_db),
    auth_data: dict = Depends(get_current_user_and_tenant)
):
    """
    Crée une décision de classification pour une entité.

    Protection :
    - JWT requis (DIRIGEANT)
    - X-Tenant-ID requis

    Règles :
    - GREEN → ORANGE : autorisé
    - ORANGE → RED : autorisé
    - RED → * : INTERDIT (403)

    Toute décision RED est automatiquement journalisée.
    """
    tenant_id = auth_data["tenant_id"]
    user_id = auth_data["user_id"]

    try:
        decision = DecisionService.classify(
            db=db,
            tenant_id=tenant_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            level=request.level,
            reason=request.reason,
            user_id=user_id
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
        # SÉCURITÉ: Ne pas exposer les détails d'erreur internes
        import logging
        logger = logging.getLogger(__name__)
        logger.error(
            "[DECISION] Erreur création décision",
            extra={"error": str(e)[:200], "entity_type": request.entity_type},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Erreur interne lors de la création de la décision"
        )


@router.get("/status/{entity_type}/{entity_id}")
async def get_decision_status(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db),
    auth_data: dict = Depends(get_current_user_and_tenant)
):
    """
    Récupère le statut décisionnel actuel d'une entité.

    Protection : JWT + X-Tenant-ID
    """
    tenant_id = auth_data["tenant_id"]

    current_decision = DecisionService.get_current_decision(
        db=db,
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id
    )

    if not current_decision:
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "level": None,
            "reason": None,
            "is_red": False
        }

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "level": current_decision.level,
        "reason": current_decision.reason,
        "created_at": current_decision.created_at.isoformat(),
        "is_red": current_decision.level == DecisionLevel.RED
    }
