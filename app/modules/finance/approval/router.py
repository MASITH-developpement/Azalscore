"""
AZALSCORE Finance Approval Router V3
=====================================

Endpoints REST pour les workflows d'approbation.

Endpoints:
- GET  /v3/finance/approval/rules - Liste des règles
- POST /v3/finance/approval/rules - Créer une règle
- GET  /v3/finance/approval/rules/{id} - Détails règle
- PUT  /v3/finance/approval/rules/{id} - Modifier règle
- DELETE /v3/finance/approval/rules/{id} - Supprimer règle
- GET  /v3/finance/approval/requests - Liste des demandes
- POST /v3/finance/approval/requests - Créer demande
- GET  /v3/finance/approval/requests/{id} - Détails demande
- POST /v3/finance/approval/requests/{id}/approve - Approuver
- POST /v3/finance/approval/requests/{id}/reject - Rejeter
- POST /v3/finance/approval/requests/{id}/escalate - Escalader
- POST /v3/finance/approval/requests/{id}/cancel - Annuler
- POST /v3/finance/approval/requests/{id}/comment - Commenter
- GET  /v3/finance/approval/pending - Demandes en attente
- GET  /v3/finance/approval/delegations - Liste délégations
- POST /v3/finance/approval/delegations - Créer délégation
- DELETE /v3/finance/approval/delegations/{id} - Révoquer
- GET  /v3/finance/approval/stats - Statistiques
- GET  /v3/finance/approval/health - Health check
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.saas_context import SaaSContext
from app.core.dependencies_v2 import get_saas_context

from .service import (
    ApprovalWorkflowService,
    ApprovalRequest,
    ApprovalRule,
    ApprovalLevel,
    ApprovalAction,
    ApprovalStatus,
    DocumentType,
    ActionType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v3/finance/approval", tags=["Finance Approval"])


# =============================================================================
# SCHEMAS
# =============================================================================


class ApprovalLevelInput(BaseModel):
    """Niveau d'approbation en entrée."""

    name: str = Field(..., min_length=1, max_length=100)
    approvers: list[str] = Field(default_factory=list)
    min_approvers: int = Field(1, ge=1)
    timeout_hours: int = Field(48, ge=1)
    can_delegate: bool = True
    can_escalate: bool = True


class CreateRuleRequest(BaseModel):
    """Requête de création de règle."""

    name: str = Field(..., min_length=1, max_length=200)
    document_type: DocumentType
    levels: list[ApprovalLevelInput]
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)
    priority: int = Field(0, ge=0)
    conditions: Optional[dict] = None


class UpdateRuleRequest(BaseModel):
    """Requête de mise à jour de règle."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    levels: Optional[list[ApprovalLevelInput]] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class LevelResponse(BaseModel):
    """Niveau d'approbation en réponse."""

    level: int
    name: str
    approvers: list[str]
    min_approvers: int
    timeout_hours: int


class RuleResponse(BaseModel):
    """Réponse règle."""

    id: str
    name: str
    document_type: str
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    levels: list[LevelResponse]
    is_active: bool
    priority: int
    created_at: str


class CreateRequestInput(BaseModel):
    """Requête de création de demande."""

    document_type: DocumentType
    document_id: str = Field(..., min_length=1)
    document_reference: str = Field(..., min_length=1)
    amount: Decimal = Field(..., ge=0)
    currency: str = Field("EUR", min_length=3, max_length=3)
    description: str = Field(..., min_length=1, max_length=2000)
    requestor_id: str = Field(..., min_length=1)
    requestor_name: Optional[str] = None
    metadata: Optional[dict] = None


class ActionResponse(BaseModel):
    """Action d'approbation."""

    id: str
    action_type: str
    user_id: str
    user_name: Optional[str] = None
    comment: Optional[str] = None
    level: int
    created_at: str


class RequestResponse(BaseModel):
    """Réponse demande d'approbation."""

    id: str
    document_type: str
    document_id: str
    document_reference: str
    amount: Decimal
    currency: str
    description: str
    requestor_id: str
    requestor_name: Optional[str] = None
    status: str
    current_level: int
    total_levels: int
    pending_approvers: list[str]
    approved_by: list[str]
    rejected_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    actions: list[ActionResponse] = Field(default_factory=list)
    created_at: str
    expires_at: Optional[str] = None
    completed_at: Optional[str] = None


class ApproveRequest(BaseModel):
    """Requête d'approbation."""

    approver_id: str
    approver_name: Optional[str] = None
    comment: Optional[str] = None


class RejectRequest(BaseModel):
    """Requête de rejet."""

    rejector_id: str
    rejector_name: Optional[str] = None
    reason: str = Field(..., min_length=1, max_length=2000)


class EscalateRequest(BaseModel):
    """Requête d'escalade."""

    escalator_id: str
    reason: Optional[str] = None


class CancelRequest(BaseModel):
    """Requête d'annulation."""

    user_id: str
    reason: Optional[str] = None


class CommentRequest(BaseModel):
    """Requête de commentaire."""

    user_id: str
    user_name: Optional[str] = None
    comment: str = Field(..., min_length=1, max_length=2000)


class CreateDelegationRequest(BaseModel):
    """Requête de création de délégation."""

    delegator_id: str
    delegator_name: str
    delegate_id: str
    delegate_name: str
    document_types: list[DocumentType]
    max_amount: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    reason: Optional[str] = None


class DelegationResponse(BaseModel):
    """Réponse délégation."""

    id: str
    delegator_id: str
    delegator_name: str
    delegate_id: str
    delegate_name: str
    document_types: list[str]
    max_amount: Optional[Decimal] = None
    start_date: str
    end_date: Optional[str] = None
    is_active: bool


class StatsResponse(BaseModel):
    """Statistiques."""

    total_requests: int
    pending_requests: int
    approved_requests: int
    rejected_requests: int
    average_approval_time_hours: float
    approval_rate: float
    by_document_type: dict
    by_level: dict


# =============================================================================
# DEPENDENCIES
# =============================================================================


def get_approval_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
) -> ApprovalWorkflowService:
    """Dépendance pour obtenir le service d'approbation."""
    return ApprovalWorkflowService(db=db, tenant_id=context.tenant_id)


# =============================================================================
# HELPERS
# =============================================================================


def rule_to_response(rule: ApprovalRule) -> RuleResponse:
    """Convertit une règle en réponse."""
    return RuleResponse(
        id=rule.id,
        name=rule.name,
        document_type=rule.document_type.value,
        min_amount=rule.min_amount,
        max_amount=rule.max_amount,
        levels=[
            LevelResponse(
                level=l.level,
                name=l.name,
                approvers=l.approvers,
                min_approvers=l.min_approvers,
                timeout_hours=l.timeout_hours,
            )
            for l in rule.levels
        ],
        is_active=rule.is_active,
        priority=rule.priority,
        created_at=rule.created_at.isoformat(),
    )


def request_to_response(request: ApprovalRequest) -> RequestResponse:
    """Convertit une demande en réponse."""
    return RequestResponse(
        id=request.id,
        document_type=request.document_type.value,
        document_id=request.document_id,
        document_reference=request.document_reference,
        amount=request.amount,
        currency=request.currency,
        description=request.description,
        requestor_id=request.requestor_id,
        requestor_name=request.requestor_name,
        status=request.status.value,
        current_level=request.current_level,
        total_levels=request.total_levels,
        pending_approvers=request.pending_approvers,
        approved_by=request.approved_by,
        rejected_by=request.rejected_by,
        rejection_reason=request.rejection_reason,
        actions=[
            ActionResponse(
                id=a.id,
                action_type=a.action_type.value,
                user_id=a.user_id,
                user_name=a.user_name,
                comment=a.comment,
                level=a.level,
                created_at=a.created_at.isoformat(),
            )
            for a in request.actions
        ],
        created_at=request.created_at.isoformat(),
        expires_at=request.expires_at.isoformat() if request.expires_at else None,
        completed_at=request.completed_at.isoformat() if request.completed_at else None,
    )


# =============================================================================
# ENDPOINTS - RULES
# =============================================================================


@router.get(
    "/rules",
    response_model=list[RuleResponse],
    summary="Liste des règles",
    description="Retourne toutes les règles d'approbation.",
)
async def list_rules(
    document_type: Optional[DocumentType] = Query(None, description="Filtrer par type"),
    active_only: bool = Query(True, description="Uniquement actives"),
    service: ApprovalWorkflowService = Depends(get_approval_service),
):
    """Liste les règles d'approbation."""
    rules = await service.list_rules(
        document_type=document_type,
        active_only=active_only,
    )
    return [rule_to_response(r) for r in rules]


@router.post(
    "/rules",
    response_model=RuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une règle",
    description="Crée une nouvelle règle d'approbation.",
)
async def create_rule(
    request: CreateRuleRequest,
    service: ApprovalWorkflowService = Depends(get_approval_service),
):
    """Crée une règle d'approbation."""
    rule = await service.create_rule(
        name=request.name,
        document_type=request.document_type,
        levels=[l.model_dump() for l in request.levels],
        min_amount=request.min_amount,
        max_amount=request.max_amount,
        priority=request.priority,
        conditions=request.conditions,
    )
    return rule_to_response(rule)


@router.get(
    "/rules/{rule_id}",
    response_model=RuleResponse,
    summary="Détails d'une règle",
    description="Retourne les détails d'une règle.",
)
async def get_rule(
    rule_id: str,
    service: ApprovalWorkflowService = Depends(get_approval_service),
):
    """Détails d'une règle."""
    rule = await service.get_rule(rule_id)

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Règle non trouvée",
        )

    return rule_to_response(rule)


@router.put(
    "/rules/{rule_id}",
    response_model=RuleResponse,
    summary="Modifier une règle",
    description="Met à jour une règle d'approbation.",
)
async def update_rule(
    rule_id: str,
    request: UpdateRuleRequest,
    service: ApprovalWorkflowService = Depends(get_approval_service),
):
    """Met à jour une règle."""
    levels_data = [l.model_dump() for l in request.levels] if request.levels else None

    rule = await service.update_rule(
        rule_id=rule_id,
        name=request.name,
        levels=levels_data,
        min_amount=request.min_amount,
        max_amount=request.max_amount,
        priority=request.priority,
        is_active=request.is_active,
    )

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Règle non trouvée",
        )

    return rule_to_response(rule)


@router.delete(
    "/rules/{rule_id}",
    response_model=dict,
    summary="Supprimer une règle",
    description="Supprime une règle d'approbation.",
)
async def delete_rule(
    rule_id: str,
    service: ApprovalWorkflowService = Depends(get_approval_service),
):
    """Supprime une règle."""
    success = await service.delete_rule(rule_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Règle non trouvée",
        )

    return {"success": True, "message": "Règle supprimée"}


# =============================================================================
# ENDPOINTS - REQUESTS
# =============================================================================


@router.get(
    "/requests",
    response_model=list[RequestResponse],
    summary="Liste des demandes",
    description="Retourne les demandes d'approbation.",
)
async def list_requests(
    request_status: Optional[ApprovalStatus] = Query(None, alias="status"),
    document_type: Optional[DocumentType] = Query(None),
    requestor_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: ApprovalWorkflowService = Depends(get_approval_service),
):
    """Liste les demandes d'approbation."""
    requests = await service.list_requests(
        status=request_status,
        document_type=document_type,
        requestor_id=requestor_id,
        limit=limit,
    )
    return [request_to_response(r) for r in requests]


@router.post(
    "/requests",
    response_model=RequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une demande",
    description="Crée une nouvelle demande d'approbation.",
)
async def create_request(
    request: CreateRequestInput,
    service: ApprovalWorkflowService = Depends(get_approval_service),
):
    """Crée une demande d'approbation."""
    approval_request = await service.create_approval_request(
        document_type=request.document_type,
        document_id=request.document_id,
        document_reference=request.document_reference,
        amount=request.amount,
        currency=request.currency,
        description=request.description,
        requestor_id=request.requestor_id,
        requestor_name=request.requestor_name,
        metadata=request.metadata,
    )
    return request_to_response(approval_request)


@router.get(
    "/requests/{request_id}",
    response_model=RequestResponse,
    summary="Détails d'une demande",
    description="Retourne les détails d'une demande.",
)
async def get_request(
    request_id: str,
    service: ApprovalWorkflowService = Depends(get_approval_service),
):
    """Détails d'une demande."""
    request = await service.get_request(request_id)

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demande non trouvée",
        )

    return request_to_response(request)


@router.post(
    "/requests/{request_id}/approve",
    response_model=RequestResponse,
    summary="Approuver une demande",
    description="Approuve une demande d'approbation.",
)
async def approve_request(
    request_id: str,
    request: ApproveRequest,
    service: ApprovalWorkflowService = Depends(get_approval_service),
):
    """Approuve une demande."""
    result = await service.approve(
        request_id=request_id,
        approver_id=request.approver_id,
        approver_name=request.approver_name,
        comment=request.comment,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible d'approuver cette demande",
        )

    return request_to_response(result)


@router.post(
    "/requests/{request_id}/reject",
    response_model=RequestResponse,
    summary="Rejeter une demande",
    description="Rejette une demande d'approbation.",
)
async def reject_request(
    request_id: str,
    request: RejectRequest,
    service: ApprovalWorkflowService = Depends(get_approval_service),
):
    """Rejette une demande."""
    result = await service.reject(
        request_id=request_id,
        rejector_id=request.rejector_id,
        rejector_name=request.rejector_name,
        reason=request.reason,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de rejeter cette demande",
        )

    return request_to_response(result)


@router.post(
    "/requests/{request_id}/escalate",
    response_model=RequestResponse,
    summary="Escalader une demande",
    description="Escalade une demande au niveau supérieur.",
)
async def escalate_request(
    request_id: str,
    request: EscalateRequest,
    service: ApprovalWorkflowService = Depends(get_approval_service),
):
    """Escalade une demande."""
    result = await service.escalate(
        request_id=request_id,
        escalator_id=request.escalator_id,
        reason=request.reason,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible d'escalader cette demande",
        )

    return request_to_response(result)


@router.post(
    "/requests/{request_id}/cancel",
    response_model=RequestResponse,
    summary="Annuler une demande",
    description="Annule une demande d'approbation.",
)
async def cancel_request(
    request_id: str,
    request: CancelRequest,
    service: ApprovalWorkflowService = Depends(get_approval_service),
):
    """Annule une demande."""
    result = await service.cancel(
        request_id=request_id,
        user_id=request.user_id,
        reason=request.reason,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible d'annuler cette demande",
        )

    return request_to_response(result)


@router.post(
    "/requests/{request_id}/comment",
    response_model=RequestResponse,
    summary="Ajouter un commentaire",
    description="Ajoute un commentaire à une demande.",
)
async def add_comment(
    request_id: str,
    request: CommentRequest,
    service: ApprovalWorkflowService = Depends(get_approval_service),
):
    """Ajoute un commentaire."""
    result = await service.add_comment(
        request_id=request_id,
        user_id=request.user_id,
        user_name=request.user_name,
        comment=request.comment,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demande non trouvée",
        )

    return request_to_response(result)


@router.get(
    "/pending",
    response_model=list[RequestResponse],
    summary="Demandes en attente",
    description="Retourne les demandes en attente pour un utilisateur.",
)
async def get_pending_requests(
    user_id: str = Query(..., description="ID de l'utilisateur"),
    limit: int = Query(50, ge=1, le=500),
    service: ApprovalWorkflowService = Depends(get_approval_service),
):
    """Demandes en attente pour un utilisateur."""
    requests = await service.get_pending_for_user(user_id, limit)
    return [request_to_response(r) for r in requests]


# =============================================================================
# ENDPOINTS - DELEGATIONS
# =============================================================================


@router.get(
    "/delegations",
    response_model=list[DelegationResponse],
    summary="Liste des délégations",
    description="Retourne les délégations de pouvoir.",
)
async def list_delegations(
    delegator_id: Optional[str] = Query(None),
    delegate_id: Optional[str] = Query(None),
    active_only: bool = Query(True),
    service: ApprovalWorkflowService = Depends(get_approval_service),
):
    """Liste les délégations."""
    delegations = await service.list_delegations(
        delegator_id=delegator_id,
        delegate_id=delegate_id,
        active_only=active_only,
    )

    return [
        DelegationResponse(
            id=d.id,
            delegator_id=d.delegator_id,
            delegator_name=d.delegator_name,
            delegate_id=d.delegate_id,
            delegate_name=d.delegate_name,
            document_types=[dt.value for dt in d.document_types],
            max_amount=d.max_amount,
            start_date=d.start_date.isoformat(),
            end_date=d.end_date.isoformat() if d.end_date else None,
            is_active=d.is_active,
        )
        for d in delegations
    ]


@router.post(
    "/delegations",
    response_model=DelegationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une délégation",
    description="Crée une délégation de pouvoir.",
)
async def create_delegation(
    request: CreateDelegationRequest,
    service: ApprovalWorkflowService = Depends(get_approval_service),
):
    """Crée une délégation."""
    delegation = await service.create_delegation(
        delegator_id=request.delegator_id,
        delegator_name=request.delegator_name,
        delegate_id=request.delegate_id,
        delegate_name=request.delegate_name,
        document_types=request.document_types,
        max_amount=request.max_amount,
        start_date=request.start_date,
        end_date=request.end_date,
        reason=request.reason,
    )

    return DelegationResponse(
        id=delegation.id,
        delegator_id=delegation.delegator_id,
        delegator_name=delegation.delegator_name,
        delegate_id=delegation.delegate_id,
        delegate_name=delegation.delegate_name,
        document_types=[dt.value for dt in delegation.document_types],
        max_amount=delegation.max_amount,
        start_date=delegation.start_date.isoformat(),
        end_date=delegation.end_date.isoformat() if delegation.end_date else None,
        is_active=delegation.is_active,
    )


@router.delete(
    "/delegations/{delegation_id}",
    response_model=dict,
    summary="Révoquer une délégation",
    description="Révoque une délégation de pouvoir.",
)
async def revoke_delegation(
    delegation_id: str,
    service: ApprovalWorkflowService = Depends(get_approval_service),
):
    """Révoque une délégation."""
    success = await service.revoke_delegation(delegation_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Délégation non trouvée",
        )

    return {"success": True, "message": "Délégation révoquée"}


# =============================================================================
# ENDPOINTS - STATS & HEALTH
# =============================================================================


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Statistiques",
    description="Retourne les statistiques d'approbation.",
)
async def get_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    service: ApprovalWorkflowService = Depends(get_approval_service),
):
    """Statistiques d'approbation."""
    stats = await service.get_stats(start_date, end_date)

    return StatsResponse(
        total_requests=stats.total_requests,
        pending_requests=stats.pending_requests,
        approved_requests=stats.approved_requests,
        rejected_requests=stats.rejected_requests,
        average_approval_time_hours=stats.average_approval_time_hours,
        approval_rate=stats.approval_rate,
        by_document_type=stats.by_document_type,
        by_level=stats.by_level,
    )


@router.get(
    "/stats/user/{user_id}",
    summary="Statistiques utilisateur",
    description="Retourne les statistiques pour un utilisateur.",
)
async def get_user_stats(
    user_id: str,
    service: ApprovalWorkflowService = Depends(get_approval_service),
):
    """Statistiques pour un utilisateur."""
    return await service.get_user_stats(user_id)


@router.get(
    "/health",
    summary="Health check",
    description="Vérifie que le service d'approbation est fonctionnel.",
)
async def health_check():
    """Health check pour le service d'approbation."""
    return {
        "status": "healthy",
        "service": "finance-approval",
        "features": [
            "approval_rules",
            "multi_level_approval",
            "delegation",
            "escalation",
            "comments",
            "statistics",
        ],
        "document_types": [dt.value for dt in DocumentType],
        "action_types": [at.value for at in ActionType],
    }
