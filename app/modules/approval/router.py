"""
Router API - Module Approval Workflow (GAP-083)

Endpoints REST pour la gestion des workflows d'approbation.
"""
import math
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission

from .models import WorkflowStatus, RequestStatus, ActionType
from .schemas import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse, WorkflowList, WorkflowListItem,
    WorkflowStepCreate, WorkflowStepResponse,
    ApprovalRequestCreate, ApprovalRequestUpdate, ApprovalRequestResponse,
    ApprovalRequestList, ApprovalRequestListItem,
    TakeActionRequest, ApprovalActionResponse,
    DelegationCreate, DelegationResponse, DelegationList,
    ApprovalStatsResponse,
    WorkflowFilters, ApprovalRequestFilters,
    AutocompleteResponse, AutocompleteItem
)
from .repository import WorkflowRepository, ApprovalRequestRepository, DelegationRepository
from .exceptions import (
    WorkflowNotFoundError, WorkflowDuplicateError, WorkflowStateError, WorkflowInactiveError,
    RequestNotFoundError, RequestStateError, ApproverNotAuthorizedError, CommentsRequiredError,
    DelegationNotFoundError
)

router = APIRouter(prefix="/approval", tags=["Approval Workflow"])


# ============== Workflows ==============

@router.get("/workflows", response_model=WorkflowList)
async def list_workflows(
    search: Optional[str] = Query(None, min_length=2),
    status: Optional[List[WorkflowStatus]] = Query(None),
    approval_type: Optional[List[str]] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.workflow.read")
):
    """Lister les workflows."""
    filters = WorkflowFilters(search=search, status=status, approval_type=approval_type)
    repo = WorkflowRepository(db, current_user.tenant_id)
    items, total = repo.list(filters, page, page_size, sort_by, sort_dir)

    return WorkflowList(
        items=[WorkflowListItem(
            id=w.id,
            code=w.code,
            name=w.name,
            approval_type=w.approval_type,
            status=w.status,
            steps_count=len(w.steps) if w.steps else 0,
            created_at=w.created_at
        ) for w in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/workflows/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_workflows(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.workflow.read")
):
    """Autocomplete workflows."""
    repo = WorkflowRepository(db, current_user.tenant_id)
    results = repo.autocomplete(q, limit)
    return AutocompleteResponse(items=[AutocompleteItem(**r) for r in results])


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.workflow.read")
):
    """Obtenir un workflow."""
    repo = WorkflowRepository(db, current_user.tenant_id)
    workflow = repo.get_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow non trouvé")
    return workflow


@router.post("/workflows", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    data: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.workflow.create")
):
    """Créer un workflow."""
    repo = WorkflowRepository(db, current_user.tenant_id)

    if data.code and repo.code_exists(data.code):
        raise HTTPException(status_code=409, detail="Code workflow déjà existant")

    workflow_data = data.model_dump()
    workflow = repo.create(workflow_data, current_user.id)
    return workflow


@router.put("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: UUID,
    data: WorkflowUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.workflow.update")
):
    """Mettre à jour un workflow."""
    repo = WorkflowRepository(db, current_user.tenant_id)
    workflow = repo.get_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow non trouvé")

    if data.code and repo.code_exists(data.code, workflow_id):
        raise HTTPException(status_code=409, detail="Code workflow déjà existant")

    update_data = data.model_dump(exclude_unset=True)
    workflow = repo.update(workflow, update_data, current_user.id)
    return workflow


@router.post("/workflows/{workflow_id}/steps", response_model=WorkflowStepResponse)
async def add_workflow_step(
    workflow_id: UUID,
    data: WorkflowStepCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.workflow.update")
):
    """Ajouter une étape au workflow."""
    repo = WorkflowRepository(db, current_user.tenant_id)
    workflow = repo.get_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow non trouvé")

    if workflow.status == WorkflowStatus.ACTIVE.value:
        raise HTTPException(status_code=400, detail="Impossible de modifier un workflow actif")

    step_data = data.model_dump()
    step = repo.add_step(workflow, step_data, current_user.id)
    return step


@router.post("/workflows/{workflow_id}/activate", response_model=WorkflowResponse)
async def activate_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.workflow.update")
):
    """Activer un workflow."""
    repo = WorkflowRepository(db, current_user.tenant_id)
    workflow = repo.get_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow non trouvé")

    try:
        workflow = repo.activate(workflow, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return workflow


@router.post("/workflows/{workflow_id}/deactivate", response_model=WorkflowResponse)
async def deactivate_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.workflow.update")
):
    """Désactiver un workflow."""
    repo = WorkflowRepository(db, current_user.tenant_id)
    workflow = repo.get_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow non trouvé")

    workflow = repo.deactivate(workflow, current_user.id)
    return workflow


@router.delete("/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.workflow.delete")
):
    """Supprimer un workflow (soft delete)."""
    repo = WorkflowRepository(db, current_user.tenant_id)
    workflow = repo.get_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow non trouvé")

    repo.soft_delete(workflow, current_user.id)


# ============== Requests ==============

@router.get("/requests", response_model=ApprovalRequestList)
async def list_requests(
    search: Optional[str] = Query(None, min_length=2),
    status: Optional[List[RequestStatus]] = Query(None),
    entity_type: Optional[str] = Query(None),
    requester_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.request.read")
):
    """Lister les demandes d'approbation."""
    filters = ApprovalRequestFilters(
        search=search, status=status, entity_type=entity_type, requester_id=requester_id
    )
    repo = ApprovalRequestRepository(db, current_user.tenant_id)
    items, total = repo.list(filters, page, page_size, sort_by, sort_dir)

    return ApprovalRequestList(
        items=[ApprovalRequestListItem(
            id=r.id,
            request_number=r.request_number,
            status=r.status,
            entity_type=r.entity_type,
            entity_number=r.entity_number,
            entity_description=r.entity_description,
            amount=r.amount,
            requester_name=r.requester_name,
            current_step=r.current_step,
            submitted_at=r.submitted_at,
            due_date=r.due_date
        ) for r in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/requests/pending", response_model=ApprovalRequestList)
async def list_pending_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.request.read")
):
    """Lister les demandes en attente pour l'utilisateur courant."""
    repo = ApprovalRequestRepository(db, current_user.tenant_id)
    items = repo.get_pending_for_user(current_user.id)

    # Pagination manuelle
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]

    return ApprovalRequestList(
        items=[ApprovalRequestListItem(
            id=r.id,
            request_number=r.request_number,
            status=r.status,
            entity_type=r.entity_type,
            entity_number=r.entity_number,
            entity_description=r.entity_description,
            amount=r.amount,
            requester_name=r.requester_name,
            current_step=r.current_step,
            submitted_at=r.submitted_at,
            due_date=r.due_date
        ) for r in page_items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/requests/{request_id}", response_model=ApprovalRequestResponse)
async def get_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.request.read")
):
    """Obtenir une demande d'approbation."""
    repo = ApprovalRequestRepository(db, current_user.tenant_id)
    request = repo.get_by_id(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    return request


@router.post("/requests", response_model=ApprovalRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_request(
    data: ApprovalRequestCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.request.create")
):
    """Créer une demande d'approbation."""
    workflow_repo = WorkflowRepository(db, current_user.tenant_id)
    workflow = workflow_repo.get_by_id(data.workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow non trouvé")

    if workflow.status != WorkflowStatus.ACTIVE.value:
        raise HTTPException(status_code=400, detail="Workflow inactif")

    # Initialiser step_statuses
    step_statuses = []
    for step in workflow.steps:
        pending_approvers = [str(a.get("approver_id")) for a in (step.approvers or [])]
        step_statuses.append({
            "step_id": str(step.id),
            "step_name": step.name,
            "status": "pending",
            "required_approvals": _count_required_approvals(step),
            "received_approvals": 0,
            "received_rejections": 0,
            "pending_approvers": pending_approvers
        })

    request_data = data.model_dump()
    request_data["requester_id"] = current_user.id
    request_data["requester_name"] = current_user.full_name if hasattr(current_user, "full_name") else str(current_user.id)
    request_data["requester_email"] = current_user.email if hasattr(current_user, "email") else None
    request_data["step_statuses"] = step_statuses

    repo = ApprovalRequestRepository(db, current_user.tenant_id)
    request = repo.create(request_data, current_user.id)
    return request


@router.post("/requests/{request_id}/submit", response_model=ApprovalRequestResponse)
async def submit_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.request.submit")
):
    """Soumettre une demande."""
    repo = ApprovalRequestRepository(db, current_user.tenant_id)
    request = repo.get_by_id(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Demande non trouvée")

    if request.status != RequestStatus.DRAFT.value:
        raise HTTPException(status_code=400, detail="Demande déjà soumise")

    request = repo.submit(request)
    return request


@router.post("/requests/{request_id}/action", response_model=ApprovalRequestResponse)
async def take_action(
    request_id: UUID,
    action: TakeActionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.request.action")
):
    """Prendre une action sur une demande."""
    repo = ApprovalRequestRepository(db, current_user.tenant_id)
    approval_request = repo.get_by_id(request_id)
    if not approval_request:
        raise HTTPException(status_code=404, detail="Demande non trouvée")

    if approval_request.status != RequestStatus.IN_PROGRESS.value:
        raise HTTPException(status_code=400, detail="Demande non en cours")

    # Vérifier que l'utilisateur est approbateur
    step_statuses = approval_request.step_statuses or []
    if approval_request.current_step >= len(step_statuses):
        raise HTTPException(status_code=400, detail="Étape invalide")

    current_status = step_statuses[approval_request.current_step]
    pending_approvers = current_status.get("pending_approvers", [])

    # Vérifier délégation
    delegation_repo = DelegationRepository(db, current_user.tenant_id)
    actual_approver = str(current_user.id)
    delegator = delegation_repo.find_delegator(current_user.id)
    if delegator:
        actual_approver = str(delegator)

    if actual_approver not in [str(a) for a in pending_approvers]:
        raise HTTPException(status_code=403, detail="Non autorisé à approuver cette demande")

    # Vérifier commentaires pour rejet
    workflow_repo = WorkflowRepository(db, current_user.tenant_id)
    workflow = workflow_repo.get_by_id(approval_request.workflow_id)
    if action.action_type == ActionType.REJECT and workflow and workflow.require_comments_on_reject:
        if not action.comments:
            raise HTTPException(status_code=400, detail="Commentaires requis pour le rejet")

    # Enregistrer l'action
    step_id = UUID(current_status.get("step_id")) if current_status.get("step_id") else None
    ip_address = request.client.host if request.client else None

    repo.add_action(
        approval_request,
        step_id,
        current_user.id,
        current_user.full_name if hasattr(current_user, "full_name") else str(current_user.id),
        action.action_type,
        action.comments,
        action.delegate_to_id,
        action.delegate_to_name,
        ip_address
    )

    # Mettre à jour step_statuses
    step_statuses = list(approval_request.step_statuses)
    current_step_status = dict(step_statuses[approval_request.current_step])

    if action.action_type == ActionType.APPROVE:
        current_step_status["received_approvals"] = current_step_status.get("received_approvals", 0) + 1
        pending = [a for a in current_step_status.get("pending_approvers", []) if str(a) != actual_approver]
        current_step_status["pending_approvers"] = pending

        # Vérifier si étape complète
        if current_step_status["received_approvals"] >= current_step_status.get("required_approvals", 1):
            current_step_status["status"] = "approved"
            current_step_status["completed_at"] = datetime.utcnow().isoformat()

            # Passer à l'étape suivante
            if approval_request.current_step + 1 < len(step_statuses):
                approval_request.current_step += 1
                next_status = dict(step_statuses[approval_request.current_step])
                next_status["status"] = "in_progress"
                next_status["started_at"] = datetime.utcnow().isoformat()
                step_statuses[approval_request.current_step] = next_status
            else:
                approval_request.status = RequestStatus.APPROVED.value
                approval_request.completed_at = datetime.utcnow()

    elif action.action_type == ActionType.REJECT:
        current_step_status["received_rejections"] = current_step_status.get("received_rejections", 0) + 1
        current_step_status["status"] = "rejected"
        current_step_status["completed_at"] = datetime.utcnow().isoformat()
        approval_request.status = RequestStatus.REJECTED.value
        approval_request.completed_at = datetime.utcnow()

    elif action.action_type == ActionType.DELEGATE:
        if not action.delegate_to_id:
            raise HTTPException(status_code=400, detail="ID du délégué requis")
        pending = current_step_status.get("pending_approvers", [])
        pending = [str(action.delegate_to_id) if str(a) == actual_approver else a for a in pending]
        current_step_status["pending_approvers"] = pending

    elif action.action_type == ActionType.RETURN:
        approval_request.status = RequestStatus.DRAFT.value
        approval_request.current_step = 0
        for i, ss in enumerate(step_statuses):
            step_statuses[i] = {
                **ss,
                "status": "pending",
                "received_approvals": 0,
                "received_rejections": 0,
                "started_at": None,
                "completed_at": None
            }

    step_statuses[approval_request.current_step if action.action_type != ActionType.RETURN else 0] = current_step_status
    approval_request.step_statuses = step_statuses

    repo.update(approval_request, {"step_statuses": step_statuses}, current_user.id)

    return approval_request


@router.post("/requests/{request_id}/cancel", response_model=ApprovalRequestResponse)
async def cancel_request(
    request_id: UUID,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.request.cancel")
):
    """Annuler une demande."""
    repo = ApprovalRequestRepository(db, current_user.tenant_id)
    request = repo.get_by_id(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Demande non trouvée")

    if request.status in [RequestStatus.APPROVED.value, RequestStatus.REJECTED.value]:
        raise HTTPException(status_code=400, detail="Demande déjà finalisée")

    request = repo.update(request, {
        "status": RequestStatus.CANCELLED.value,
        "completed_at": datetime.utcnow()
    }, current_user.id)

    return request


@router.get("/requests/{request_id}/actions", response_model=List[ApprovalActionResponse])
async def get_request_actions(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.request.read")
):
    """Obtenir l'historique des actions."""
    repo = ApprovalRequestRepository(db, current_user.tenant_id)
    request = repo.get_by_id(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Demande non trouvée")

    return request.actions


# ============== Delegations ==============

@router.get("/delegations", response_model=DelegationList)
async def list_delegations(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.delegation.read")
):
    """Lister les délégations de l'utilisateur."""
    repo = DelegationRepository(db, current_user.tenant_id)
    items = repo.list(delegator_id=current_user.id, active_only=False)

    return DelegationList(items=items, total=len(items))


@router.get("/delegations/received", response_model=DelegationList)
async def list_received_delegations(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.delegation.read")
):
    """Lister les délégations reçues."""
    repo = DelegationRepository(db, current_user.tenant_id)
    items = repo.list(delegate_id=current_user.id, active_only=True)

    return DelegationList(items=items, total=len(items))


@router.post("/delegations", response_model=DelegationResponse, status_code=status.HTTP_201_CREATED)
async def create_delegation(
    data: DelegationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.delegation.create")
):
    """Créer une délégation."""
    repo = DelegationRepository(db, current_user.tenant_id)

    delegation_data = data.model_dump()
    delegation_data["delegator_id"] = current_user.id
    delegation_data["delegator_name"] = current_user.full_name if hasattr(current_user, "full_name") else str(current_user.id)

    delegation = repo.create(delegation_data, current_user.id)
    return delegation


@router.post("/delegations/{delegation_id}/revoke", response_model=DelegationResponse)
async def revoke_delegation(
    delegation_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.delegation.delete")
):
    """Révoquer une délégation."""
    repo = DelegationRepository(db, current_user.tenant_id)
    delegation = repo.get_by_id(delegation_id)
    if not delegation:
        raise HTTPException(status_code=404, detail="Délégation non trouvée")

    if delegation.delegator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non autorisé")

    delegation = repo.revoke(delegation, current_user.id)
    return delegation


# ============== Stats ==============

@router.get("/stats", response_model=ApprovalStatsResponse)
async def get_stats(
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("approval.stats.read")
):
    """Obtenir les statistiques d'approbation."""
    repo = ApprovalRequestRepository(db, current_user.tenant_id)
    filters = ApprovalRequestFilters(date_from=period_start, date_to=period_end)
    items, total = repo.list(filters, page=1, page_size=10000)

    stats = {
        "tenant_id": current_user.tenant_id,
        "period_start": period_start,
        "period_end": period_end,
        "total_requests": total,
        "pending_requests": len([r for r in items if r.status in [RequestStatus.PENDING.value, RequestStatus.IN_PROGRESS.value]]),
        "approved_requests": len([r for r in items if r.status == RequestStatus.APPROVED.value]),
        "rejected_requests": len([r for r in items if r.status == RequestStatus.REJECTED.value]),
        "average_approval_time_hours": 0,
        "by_type": {},
        "by_department": {}
    }

    # Temps moyen
    completed = [r for r in items if r.completed_at and r.submitted_at]
    if completed:
        total_hours = sum(
            (r.completed_at - r.submitted_at).total_seconds() / 3600
            for r in completed
        )
        stats["average_approval_time_hours"] = round(total_hours / len(completed), 2)

    # Par type
    for r in items:
        stats["by_type"][r.entity_type] = stats["by_type"].get(r.entity_type, 0) + 1

    return ApprovalStatsResponse(**stats)


# ============== Helpers ==============

def _count_required_approvals(step) -> int:
    """Compter les approbations requises pour une étape."""
    from .models import StepType

    step_type = step.step_type
    approvers = step.approvers or []

    if step_type == StepType.SINGLE.value:
        return 1
    elif step_type == StepType.ANY.value:
        return 1
    elif step_type == StepType.ALL.value:
        return len([a for a in approvers if a.get("is_required", True)])
    elif step_type == StepType.MAJORITY.value:
        return len(approvers) // 2 + 1
    elif step_type == StepType.SEQUENCE.value:
        return len([a for a in approvers if a.get("is_required", True)])
    return 1


