"""
API Workflows d'Approbation AZALSCORE
======================================

Endpoints pour soumettre, approuver et rejeter des documents.

Conformité: AZA-NF-003, Workflow RED
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.core.models import User
from app.core.workflow import (
    ApprovalAction,
    ApprovalAnalytics,
    ApprovalDelegation,
    EscalationService,
    WorkflowAnalyticsService,
    WorkflowEngine,
    WorkflowInstance,
    WorkflowNotification,
    WorkflowStatus,
    WorkflowStep,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/approvals", tags=["approvals"])


# =============================================================================
# SCHEMAS
# =============================================================================

class WorkflowSubmitRequest(BaseModel):
    """Requête de soumission pour approbation."""
    workflow_name: str = Field(..., description="Nom du workflow (ex: quote_approval)")
    document_type: str = Field(..., description="Type de document (ex: quote, invoice)")
    document_id: UUID = Field(..., description="ID du document")
    amount: Optional[int] = Field(None, description="Montant pour seuils d'approbation")
    metadata: Optional[dict] = Field(None, description="Métadonnées supplémentaires")


class WorkflowActionRequest(BaseModel):
    """Requête d'action sur un workflow."""
    comments: Optional[str] = Field(None, max_length=2000, description="Commentaires")


class WorkflowStepResponse(BaseModel):
    """Réponse pour une étape de workflow."""
    id: UUID
    step_number: int
    step_name: str
    required_role: str
    status: str
    action_taken: Optional[str]
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    comments: Optional[str]
    due_at: Optional[datetime]
    escalated: bool

    class Config:
        from_attributes = True


class WorkflowInstanceResponse(BaseModel):
    """Réponse pour une instance de workflow."""
    id: UUID
    workflow_name: str
    document_type: str
    document_id: UUID
    status: str
    current_step: int
    total_steps: int
    amount: Optional[int]
    initiated_by: UUID
    initiated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    expires_at: Optional[datetime]
    steps: List[WorkflowStepResponse] = []

    class Config:
        from_attributes = True


class PendingApprovalResponse(BaseModel):
    """Réponse pour une approbation en attente."""
    step_id: UUID
    workflow_id: UUID
    workflow_name: str
    document_type: str
    document_id: UUID
    step_name: str
    required_role: str
    due_at: Optional[datetime]
    amount: Optional[int]
    initiated_by: UUID
    initiated_at: datetime


class DelegationCreateRequest(BaseModel):
    """Requête de création de délégation."""
    delegate_id: UUID = Field(..., description="ID de l'utilisateur délégué")
    valid_from: datetime = Field(..., description="Date de début")
    valid_until: datetime = Field(..., description="Date de fin")
    workflow_names: List[str] = Field(default=[], description="Workflows concernés (vide = tous)")
    document_types: List[str] = Field(default=[], description="Types de documents (vide = tous)")
    max_amount: Optional[int] = Field(None, description="Montant maximum")
    reason: Optional[str] = Field(None, max_length=500, description="Raison de la délégation")


class DelegationResponse(BaseModel):
    """Réponse pour une délégation."""
    id: UUID
    delegator_id: UUID
    delegate_id: UUID
    valid_from: datetime
    valid_until: datetime
    workflow_names: List[str]
    document_types: List[str]
    max_amount: Optional[int]
    reason: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyticsResponse(BaseModel):
    """Réponse pour les analytics."""
    total_workflows: int
    approved_count: int
    rejected_count: int
    pending_count: int
    expired_count: int
    approval_rate: float
    rejection_rate: float
    avg_approval_time_hours: float
    avg_steps_to_approval: float
    by_workflow: dict
    by_approver: dict


class NotificationResponse(BaseModel):
    """Réponse pour une notification."""
    id: UUID
    workflow_id: UUID
    notification_type: str
    title: str
    message: str
    link: Optional[str]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# ENDPOINTS SOUMISSION & APPROBATION
# =============================================================================

@router.post("/submit", response_model=WorkflowInstanceResponse, status_code=status.HTTP_201_CREATED)
async def submit_for_approval(
    request: WorkflowSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soumet un document pour approbation.

    Le workflow est sélectionné automatiquement en fonction du type de document
    et du montant. Les étapes sont créées selon les seuils définis.
    """
    engine = WorkflowEngine(db, current_user.tenant_id, current_user.id)

    try:
        instance = engine.submit(
            workflow_name=request.workflow_name,
            document_type=request.document_type,
            document_id=request.document_id,
            amount=request.amount,
            metadata=request.metadata,
        )

        # Charger les étapes pour la réponse
        return _build_workflow_response(instance)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting workflow: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la soumission")


@router.post("/{workflow_id}/steps/{step_number}/approve", response_model=WorkflowInstanceResponse)
async def approve_step(
    workflow_id: UUID,
    step_number: int,
    request: WorkflowActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Approuve une étape du workflow.

    L'utilisateur doit avoir le rôle requis pour cette étape.
    Si c'est la dernière étape, le workflow est marqué comme approuvé.
    """
    engine = WorkflowEngine(db, current_user.tenant_id, current_user.id)

    try:
        instance = engine.approve(
            workflow_id=workflow_id,
            step_number=step_number,
            comments=request.comments,
        )
        return _build_workflow_response(instance)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error approving workflow: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'approbation")


@router.post("/{workflow_id}/steps/{step_number}/reject", response_model=WorkflowInstanceResponse)
async def reject_step(
    workflow_id: UUID,
    step_number: int,
    request: WorkflowActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Rejette une étape du workflow.

    Le rejet termine immédiatement le workflow avec statut REJECTED.
    Un commentaire est fortement recommandé pour expliquer le rejet.
    """
    engine = WorkflowEngine(db, current_user.tenant_id, current_user.id)

    try:
        instance = engine.reject(
            workflow_id=workflow_id,
            step_number=step_number,
            comments=request.comments,
        )
        return _build_workflow_response(instance)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error rejecting workflow: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors du rejet")


@router.get("/pending", response_model=List[PendingApprovalResponse])
async def get_pending_approvals(
    role: Optional[str] = Query(None, description="Filtrer par rôle"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Liste les approbations en attente pour l'utilisateur.

    Retourne les étapes de workflow en attente pour lesquelles
    l'utilisateur a le rôle requis.
    """
    engine = WorkflowEngine(db, current_user.tenant_id, current_user.id)
    steps = engine.get_pending_approvals(role=role)

    return [
        PendingApprovalResponse(
            step_id=step.id,
            workflow_id=step.workflow_id,
            workflow_name=step.workflow.workflow_name,
            document_type=step.workflow.document_type,
            document_id=step.workflow.document_id,
            step_name=step.step_name,
            required_role=step.required_role,
            due_at=step.due_at,
            amount=step.workflow.amount,
            initiated_by=step.workflow.initiated_by,
            initiated_at=step.workflow.initiated_at,
        )
        for step in steps
    ]


@router.get("/{workflow_id}", response_model=WorkflowInstanceResponse)
async def get_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Récupère le détail d'un workflow."""
    instance = db.query(WorkflowInstance).filter(
        WorkflowInstance.id == workflow_id,
        WorkflowInstance.tenant_id == current_user.tenant_id,
    ).first()

    if not instance:
        raise HTTPException(status_code=404, detail="Workflow non trouvé")

    return _build_workflow_response(instance)


@router.get("/document/{document_type}/{document_id}", response_model=Optional[WorkflowInstanceResponse])
async def get_document_workflow(
    document_type: str,
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Récupère le workflow actif pour un document."""
    engine = WorkflowEngine(db, current_user.tenant_id, current_user.id)
    instance = engine.get_workflow_status(document_type, document_id)

    if not instance:
        return None

    return _build_workflow_response(instance)


# =============================================================================
# ENDPOINTS DELEGATIONS
# =============================================================================

@router.post("/delegations", response_model=DelegationResponse, status_code=status.HTTP_201_CREATED)
async def create_delegation(
    request: DelegationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crée une délégation de pouvoir d'approbation.

    Permet de déléguer temporairement ses droits d'approbation
    à un autre utilisateur (ex: pendant les congés).
    """
    # Vérifier les dates
    if request.valid_until <= request.valid_from:
        raise HTTPException(status_code=400, detail="Date de fin doit être après date de début")

    delegation = ApprovalDelegation(
        tenant_id=current_user.tenant_id,
        delegator_id=current_user.id,
        delegator_role=current_user.role,
        delegate_id=request.delegate_id,
        workflow_names=request.workflow_names,
        document_types=request.document_types,
        max_amount=request.max_amount,
        valid_from=request.valid_from,
        valid_until=request.valid_until,
        reason=request.reason,
        created_by=current_user.id,
    )

    db.add(delegation)
    db.commit()
    db.refresh(delegation)

    return delegation


@router.get("/delegations", response_model=List[DelegationResponse])
async def list_delegations(
    active_only: bool = Query(True, description="Uniquement les délégations actives"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Liste les délégations de l'utilisateur (données et reçues)."""
    query = db.query(ApprovalDelegation).filter(
        ApprovalDelegation.tenant_id == current_user.tenant_id,
        (ApprovalDelegation.delegator_id == current_user.id) |
        (ApprovalDelegation.delegate_id == current_user.id),
    )

    if active_only:
        now = datetime.utcnow()
        query = query.filter(
            ApprovalDelegation.is_active == True,
            ApprovalDelegation.valid_from <= now,
            ApprovalDelegation.valid_until >= now,
        )

    return query.all()


@router.delete("/delegations/{delegation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_delegation(
    delegation_id: UUID,
    reason: Optional[str] = Query(None, description="Raison de la révocation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Révoque une délégation."""
    delegation = db.query(ApprovalDelegation).filter(
        ApprovalDelegation.id == delegation_id,
        ApprovalDelegation.tenant_id == current_user.tenant_id,
        ApprovalDelegation.delegator_id == current_user.id,
    ).first()

    if not delegation:
        raise HTTPException(status_code=404, detail="Délégation non trouvée")

    delegation.is_active = False
    delegation.revoked_at = datetime.utcnow()
    delegation.revoked_by = current_user.id
    delegation.revoke_reason = reason

    db.commit()


# =============================================================================
# ENDPOINTS ANALYTICS
# =============================================================================

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    start_date: Optional[datetime] = Query(None, description="Date de début"),
    end_date: Optional[datetime] = Query(None, description="Date de fin"),
    workflow_name: Optional[str] = Query(None, description="Filtrer par workflow"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Récupère les analytics d'approbation.

    Calcule les statistiques: taux d'approbation, temps moyen,
    répartition par workflow et par approbateur.
    """
    service = WorkflowAnalyticsService(db, current_user.tenant_id)
    analytics = service.get_analytics(
        start_date=start_date,
        end_date=end_date,
        workflow_name=workflow_name,
    )

    return AnalyticsResponse(
        total_workflows=analytics.total_workflows,
        approved_count=analytics.approved_count,
        rejected_count=analytics.rejected_count,
        pending_count=analytics.pending_count,
        expired_count=analytics.expired_count,
        approval_rate=analytics.approval_rate,
        rejection_rate=analytics.rejection_rate,
        avg_approval_time_hours=analytics.avg_approval_time_hours,
        avg_steps_to_approval=analytics.avg_steps_to_approval,
        by_workflow=analytics.by_workflow,
        by_approver=analytics.by_approver,
    )


# =============================================================================
# ENDPOINTS NOTIFICATIONS
# =============================================================================

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(False, description="Uniquement non lues"),
    limit: int = Query(50, le=100, description="Limite"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Liste les notifications de workflow pour l'utilisateur."""
    query = db.query(WorkflowNotification).filter(
        WorkflowNotification.tenant_id == current_user.tenant_id,
        WorkflowNotification.recipient_id == current_user.id,
    )

    if unread_only:
        query = query.filter(WorkflowNotification.is_read == False)

    return query.order_by(WorkflowNotification.created_at.desc()).limit(limit).all()


@router.post("/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Marque une notification comme lue."""
    notif = db.query(WorkflowNotification).filter(
        WorkflowNotification.id == notification_id,
        WorkflowNotification.tenant_id == current_user.tenant_id,
        WorkflowNotification.recipient_id == current_user.id,
    ).first()

    if not notif:
        raise HTTPException(status_code=404, detail="Notification non trouvée")

    notif.is_read = True
    notif.read_at = datetime.utcnow()
    db.commit()


# =============================================================================
# ENDPOINTS ADMIN
# =============================================================================

@router.get("/workflows/definitions")
async def list_workflow_definitions(
    current_user: User = Depends(get_current_user),
):
    """Liste toutes les définitions de workflows disponibles."""
    definitions = []
    for name, definition in WorkflowEngine.PREDEFINED_WORKFLOWS.items():
        definitions.append({
            "name": name,
            "description": definition.description,
            "version": definition.version,
            "document_types": definition.document_types,
            "steps": [
                {
                    "name": step.name,
                    "role": step.role,
                    "action": step.action,
                    "threshold": step.threshold,
                    "timeout_hours": step.timeout_hours,
                    "auto_escalate": step.auto_escalate,
                }
                for step in definition.steps
            ],
        })
    return definitions


@router.post("/admin/escalate", status_code=status.HTTP_200_OK)
async def run_escalation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Exécute manuellement le service d'escalade.

    Vérifie les étapes expirées et les escalade si configuré.
    Normalement exécuté par un scheduler automatique.
    """
    # Vérifier que l'utilisateur est admin
    if current_user.role not in ["SUPERADMIN", "admin", "system"]:
        raise HTTPException(status_code=403, detail="Accès refusé")

    service = EscalationService(db, current_user.tenant_id)
    escalated = service.check_and_escalate()
    reminders = service.send_reminders()

    return {
        "escalated_count": len(escalated),
        "reminders_sent": len(reminders),
    }


# =============================================================================
# HELPERS
# =============================================================================

def _build_workflow_response(instance: WorkflowInstance) -> WorkflowInstanceResponse:
    """Construit la réponse pour une instance de workflow."""
    return WorkflowInstanceResponse(
        id=instance.id,
        workflow_name=instance.workflow_name,
        document_type=instance.document_type,
        document_id=instance.document_id,
        status=instance.status.value,
        current_step=instance.current_step,
        total_steps=instance.total_steps,
        amount=instance.amount,
        initiated_by=instance.initiated_by,
        initiated_at=instance.initiated_at,
        started_at=instance.started_at,
        completed_at=instance.completed_at,
        expires_at=instance.expires_at,
        steps=[
            WorkflowStepResponse(
                id=step.id,
                step_number=step.step_number,
                step_name=step.step_name,
                required_role=step.required_role,
                status=step.status.value,
                action_taken=step.action_taken.value if step.action_taken else None,
                approved_by=step.approved_by,
                approved_at=step.approved_at,
                comments=step.comments,
                due_at=step.due_at,
                escalated=step.escalated,
            )
            for step in sorted(instance.steps, key=lambda s: s.step_number)
        ],
    )
