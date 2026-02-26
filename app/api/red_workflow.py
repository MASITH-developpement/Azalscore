"""
AZALS - API endpoints pour validation workflow RED
Endpoints de validation en 3 étapes pour décisions RED
"""
from __future__ import annotations


import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_and_tenant
from app.core.models import RedWorkflowStep
from app.services.red_workflow import RedWorkflowService

router = APIRouter(prefix="/decision/red", tags=["red-workflow"])


class WorkflowStepResponse(BaseModel):
    """Réponse après validation d'une étape."""
    decision_id: int
    step: str
    confirmed_at: str
    message: str

    model_config = {"from_attributes": True}


class WorkflowStatusResponse(BaseModel):
    """État complet du workflow."""
    decision_id: int
    level: str
    completed_steps: list[str]
    pending_steps: list[str]
    is_fully_validated: bool


class RedReportResponse(BaseModel):
    """Rapport 🔴 AZALS - IMMUTABLE."""
    id: int
    decision_id: int
    decision_reason: str
    trigger_data: dict
    validated_at: str
    validator_id: int
    journal_references: list[str]
    created_at: str

    model_config = {"from_attributes": True}


@router.post("/acknowledge/{decision_id}", response_model=WorkflowStepResponse)
def acknowledge_red_risks(
    decision_id: int,
    context: dict = Depends(get_current_user_and_tenant),
    db: Session = Depends(get_db)
):
    """
    Étape 1/3 : Accusé de lecture des risques.
    Confirme que le DIRIGEANT a pris connaissance des risques associés à la décision RED.
    """
    service = RedWorkflowService(db)
    workflow = service.validate_step(
        decision_id=decision_id,
        step=RedWorkflowStep.ACKNOWLEDGE,
        user_id=context["user_id"],
        tenant_id=context["tenant_id"]
    )

    return WorkflowStepResponse(
        decision_id=workflow.decision_id,
        step=workflow.step.value,
        confirmed_at=workflow.confirmed_at.isoformat(),
        message="Risks acknowledged. Proceed to confirm completeness."
    )


@router.post("/confirm-completeness/{decision_id}", response_model=WorkflowStepResponse)
def confirm_information_completeness(
    decision_id: int,
    context: dict = Depends(get_current_user_and_tenant),
    db: Session = Depends(get_db)
):
    """
    Étape 2/3 : Confirmation de complétude des informations.
    Confirme que toutes les informations nécessaires sont présentes et complètes.
    """
    service = RedWorkflowService(db)
    workflow = service.validate_step(
        decision_id=decision_id,
        step=RedWorkflowStep.COMPLETENESS,
        user_id=context["user_id"],
        tenant_id=context["tenant_id"]
    )

    return WorkflowStepResponse(
        decision_id=workflow.decision_id,
        step=workflow.step.value,
        confirmed_at=workflow.confirmed_at.isoformat(),
        message="Completeness confirmed. Proceed to final validation."
    )


@router.post("/confirm-final/{decision_id}", response_model=WorkflowStepResponse)
def final_red_validation(
    decision_id: int,
    context: dict = Depends(get_current_user_and_tenant),
    db: Session = Depends(get_db)
):
    """
    Étape 3/3 : Confirmation finale explicite.
    Validation définitive et irréversible de la décision RED.
    """
    service = RedWorkflowService(db)
    workflow = service.validate_step(
        decision_id=decision_id,
        step=RedWorkflowStep.FINAL,
        user_id=context["user_id"],
        tenant_id=context["tenant_id"]
    )

    return WorkflowStepResponse(
        decision_id=workflow.decision_id,
        step=workflow.step.value,
        confirmed_at=workflow.confirmed_at.isoformat(),
        message="RED decision fully validated. Workflow complete."
    )


@router.get("/status/{decision_id}", response_model=WorkflowStatusResponse)
def get_red_workflow_status(
    decision_id: int,
    context: dict = Depends(get_current_user_and_tenant),
    db: Session = Depends(get_db)
):
    """
    Récupère l'état actuel du workflow de validation pour une décision RED.
    """
    service = RedWorkflowService(db)
    status = service.get_workflow_status(decision_id, context["tenant_id"])

    return WorkflowStatusResponse(**status)


@router.get("/report/{decision_id}", response_model=RedReportResponse)
def get_red_decision_report(
    decision_id: int,
    context: dict = Depends(get_current_user_and_tenant),
    db: Session = Depends(get_db)
):
    """
    Récupère le rapport 🔴 IMMUTABLE pour une décision RED validée.

    Règles :
    - Accessible UNIQUEMENT après validation complète (step FINAL)
    - Rapport en lecture seule (IMMUTABLE)
    - Isolation stricte par tenant
    - Contient snapshot complet des données décisionnelles
    """
    service = RedWorkflowService(db)
    report = service.get_red_report(decision_id, context["tenant_id"])

    return RedReportResponse(
        id=report.id,
        decision_id=report.decision_id,
        decision_reason=report.decision_reason,
        trigger_data=json.loads(report.trigger_data),
        validated_at=report.validated_at.isoformat(),
        validator_id=report.validator_id,
        journal_references=json.loads(report.journal_references),
        created_at=report.created_at.isoformat()
    )
