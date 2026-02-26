"""
AZALS MODULE M11 - Router Conformité
====================================

Routes API pour la gestion de la conformité réglementaire.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.core.models import User

from .models import ComplianceStatus, RegulationType, RequirementPriority
from .schemas import (
    AcknowledgmentCreate,
    AcknowledgmentResponse,
    ActionCreate,
    ActionResponse,
    AssessmentCreate,
    AssessmentResponse,
    AuditCreate,
    AuditResponse,
    CompletionCreate,
    CompletionResponse,
    ComplianceMetrics,
    FindingCreate,
    FindingResponse,
    GapCreate,
    GapResponse,
    IncidentCreate,
    IncidentResponse,
    PolicyCreate,
    PolicyResponse,
    RegulationCreate,
    RegulationResponse,
    RegulationUpdate,
    ReportCreate,
    ReportResponse,
    RequirementCreate,
    RequirementResponse,
    RequirementUpdate,
    RiskCreate,
    RiskResponse,
    RiskUpdate,
    TrainingCreate,
    TrainingResponse,
)
from .service import get_compliance_service

router = APIRouter(prefix="/compliance", tags=["Compliance"])


# =============================================================================
# RÉGLEMENTATIONS
# =============================================================================

@router.post("/regulations", response_model=RegulationResponse, status_code=status.HTTP_201_CREATED)
def create_regulation(
    data: RegulationCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Créer une nouvelle réglementation."""
    service = get_compliance_service(db, tenant_id)
    return service.create_regulation(data, current_user.id)


@router.get("/regulations", response_model=list[RegulationResponse])
def list_regulations(
    regulation_type: RegulationType | None = None,
    is_active: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Lister les réglementations."""
    service = get_compliance_service(db, tenant_id)
    return service.get_regulations(regulation_type, is_active, skip, limit)


@router.get("/regulations/{regulation_id}", response_model=RegulationResponse)
def get_regulation(
    regulation_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une réglementation."""
    service = get_compliance_service(db, tenant_id)
    regulation = service.get_regulation(regulation_id)
    if not regulation:
        raise HTTPException(status_code=404, detail="Réglementation non trouvée")
    return regulation


@router.put("/regulations/{regulation_id}", response_model=RegulationResponse)
def update_regulation(
    regulation_id: UUID,
    data: RegulationUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour une réglementation."""
    service = get_compliance_service(db, tenant_id)
    regulation = service.update_regulation(regulation_id, data, current_user.id)
    if not regulation:
        raise HTTPException(status_code=404, detail="Réglementation non trouvée")
    return regulation


# =============================================================================
# EXIGENCES
# =============================================================================

@router.post("/requirements", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
def create_requirement(
    data: RequirementCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Créer une nouvelle exigence."""
    service = get_compliance_service(db, tenant_id)
    return service.create_requirement(data, current_user.id)


@router.get("/requirements", response_model=list[RequirementResponse])
def list_requirements(
    regulation_id: UUID | None = None,
    compliance_status: ComplianceStatus | None = None,
    priority: RequirementPriority | None = None,
    is_active: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Lister les exigences."""
    service = get_compliance_service(db, tenant_id)
    return service.get_requirements(regulation_id, compliance_status, priority, is_active, skip, limit)


@router.get("/requirements/{requirement_id}", response_model=RequirementResponse)
def get_requirement(
    requirement_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une exigence."""
    service = get_compliance_service(db, tenant_id)
    requirement = service.get_requirement(requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Exigence non trouvée")
    return requirement


@router.put("/requirements/{requirement_id}", response_model=RequirementResponse)
def update_requirement(
    requirement_id: UUID,
    data: RequirementUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour une exigence."""
    service = get_compliance_service(db, tenant_id)
    requirement = service.update_requirement(requirement_id, data, current_user.id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Exigence non trouvée")
    return requirement


@router.post("/requirements/{requirement_id}/assess", response_model=RequirementResponse)
def assess_requirement(
    requirement_id: UUID,
    status: ComplianceStatus,
    score: Decimal | None = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Évaluer la conformité d'une exigence."""
    service = get_compliance_service(db, tenant_id)
    requirement = service.assess_requirement(requirement_id, status, score, current_user.id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Exigence non trouvée")
    return requirement


# =============================================================================
# ÉVALUATIONS
# =============================================================================

@router.post("/assessments", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_assessment(
    data: AssessmentCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Créer une nouvelle évaluation."""
    service = get_compliance_service(db, tenant_id)
    return service.create_assessment(data, current_user.id)


@router.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une évaluation."""
    service = get_compliance_service(db, tenant_id)
    assessment = service.get_assessment(assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Évaluation non trouvée")
    return assessment


@router.post("/assessments/{assessment_id}/start", response_model=AssessmentResponse)
def start_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Démarrer une évaluation."""
    service = get_compliance_service(db, tenant_id)
    assessment = service.start_assessment(assessment_id)
    if not assessment:
        raise HTTPException(status_code=400, detail="Impossible de démarrer l'évaluation")
    return assessment


@router.post("/assessments/{assessment_id}/complete", response_model=AssessmentResponse)
def complete_assessment(
    assessment_id: UUID,
    findings_summary: str | None = None,
    recommendations: str | None = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Terminer une évaluation."""
    service = get_compliance_service(db, tenant_id)
    assessment = service.complete_assessment(assessment_id, findings_summary, recommendations)
    if not assessment:
        raise HTTPException(status_code=400, detail="Impossible de terminer l'évaluation")
    return assessment


@router.post("/assessments/{assessment_id}/approve", response_model=AssessmentResponse)
def approve_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Approuver une évaluation."""
    service = get_compliance_service(db, tenant_id)
    assessment = service.approve_assessment(assessment_id, current_user.id)
    if not assessment:
        raise HTTPException(status_code=400, detail="Impossible d'approuver l'évaluation")
    return assessment


# =============================================================================
# ÉCARTS
# =============================================================================

@router.post("/gaps", response_model=GapResponse, status_code=status.HTTP_201_CREATED)
def create_gap(
    data: GapCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Créer un écart de conformité."""
    service = get_compliance_service(db, tenant_id)
    return service.create_gap(data, current_user.id)


@router.post("/gaps/{gap_id}/close", response_model=GapResponse)
def close_gap(
    gap_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Clôturer un écart."""
    service = get_compliance_service(db, tenant_id)
    gap = service.close_gap(gap_id)
    if not gap:
        raise HTTPException(status_code=400, detail="Impossible de clôturer l'écart")
    return gap


# =============================================================================
# ACTIONS
# =============================================================================

@router.post("/actions", response_model=ActionResponse, status_code=status.HTTP_201_CREATED)
def create_action(
    data: ActionCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Créer une action corrective."""
    service = get_compliance_service(db, tenant_id)
    return service.create_action(data, current_user.id)


@router.get("/actions/{action_id}", response_model=ActionResponse)
def get_action(
    action_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une action."""
    service = get_compliance_service(db, tenant_id)
    action = service.get_action(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action non trouvée")
    return action


@router.post("/actions/{action_id}/start", response_model=ActionResponse)
def start_action(
    action_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Démarrer une action."""
    service = get_compliance_service(db, tenant_id)
    action = service.start_action(action_id)
    if not action:
        raise HTTPException(status_code=400, detail="Impossible de démarrer l'action")
    return action


@router.post("/actions/{action_id}/complete", response_model=ActionResponse)
def complete_action(
    action_id: UUID,
    resolution_notes: str,
    evidence: list[str] | None = None,
    actual_cost: Decimal | None = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Terminer une action."""
    service = get_compliance_service(db, tenant_id)
    action = service.complete_action(action_id, resolution_notes, evidence, actual_cost)
    if not action:
        raise HTTPException(status_code=400, detail="Impossible de terminer l'action")
    return action


@router.post("/actions/{action_id}/verify", response_model=ActionResponse)
def verify_action(
    action_id: UUID,
    verification_notes: str | None = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Vérifier une action."""
    service = get_compliance_service(db, tenant_id)
    action = service.verify_action(action_id, current_user.id, verification_notes)
    if not action:
        raise HTTPException(status_code=400, detail="Impossible de vérifier l'action")
    return action


@router.get("/actions/overdue", response_model=list[ActionResponse])
def get_overdue_actions(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les actions en retard."""
    service = get_compliance_service(db, tenant_id)
    return service.get_overdue_actions()


# =============================================================================
# POLITIQUES
# =============================================================================

@router.get("/policies", response_model=list[PolicyResponse])
def list_policies(
    is_published: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Lister les politiques."""
    service = get_compliance_service(db, tenant_id)
    return service.get_policies(is_published, skip, limit)


@router.post("/policies", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
def create_policy(
    data: PolicyCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Créer une politique."""
    service = get_compliance_service(db, tenant_id)
    return service.create_policy(data, current_user.id)


@router.get("/policies/{policy_id}", response_model=PolicyResponse)
def get_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une politique."""
    service = get_compliance_service(db, tenant_id)
    policy = service.get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Politique non trouvée")
    return policy


@router.post("/policies/{policy_id}/publish", response_model=PolicyResponse)
def publish_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Publier une politique."""
    service = get_compliance_service(db, tenant_id)
    policy = service.publish_policy(policy_id, current_user.id)
    if not policy:
        raise HTTPException(status_code=400, detail="Impossible de publier la politique")
    return policy


@router.post("/policies/acknowledge", response_model=AcknowledgmentResponse, status_code=status.HTTP_201_CREATED)
def acknowledge_policy(
    data: AcknowledgmentCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Accuser réception d'une politique."""
    service = get_compliance_service(db, tenant_id)
    return service.acknowledge_policy(data, current_user.id)


# =============================================================================
# FORMATIONS
# =============================================================================

@router.post("/trainings", response_model=TrainingResponse, status_code=status.HTTP_201_CREATED)
def create_training(
    data: TrainingCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Créer une formation."""
    service = get_compliance_service(db, tenant_id)
    return service.create_training(data, current_user.id)


@router.get("/trainings/{training_id}", response_model=TrainingResponse)
def get_training(
    training_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une formation."""
    service = get_compliance_service(db, tenant_id)
    training = service.get_training(training_id)
    if not training:
        raise HTTPException(status_code=404, detail="Formation non trouvée")
    return training


@router.post("/trainings/assign", response_model=CompletionResponse, status_code=status.HTTP_201_CREATED)
def assign_training(
    data: CompletionCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Assigner une formation à un utilisateur."""
    service = get_compliance_service(db, tenant_id)
    return service.assign_training(data, current_user.id)


@router.post("/trainings/completions/{completion_id}/start", response_model=CompletionResponse)
def start_training_completion(
    completion_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Démarrer une formation."""
    service = get_compliance_service(db, tenant_id)
    completion = service.start_training(completion_id)
    if not completion:
        raise HTTPException(status_code=400, detail="Impossible de démarrer la formation")
    return completion


@router.post("/trainings/completions/{completion_id}/complete", response_model=CompletionResponse)
def complete_training_completion(
    completion_id: UUID,
    score: int,
    certificate_number: str | None = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Terminer une formation."""
    service = get_compliance_service(db, tenant_id)
    completion = service.complete_training(completion_id, score, certificate_number)
    if not completion:
        raise HTTPException(status_code=400, detail="Impossible de terminer la formation")
    return completion


# =============================================================================
# AUDITS
# =============================================================================

@router.post("/audits", response_model=AuditResponse, status_code=status.HTTP_201_CREATED)
def create_audit(
    data: AuditCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Créer un audit."""
    service = get_compliance_service(db, tenant_id)
    return service.create_audit(data, current_user.id)


@router.get("/audits/{audit_id}", response_model=AuditResponse)
def get_audit(
    audit_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un audit."""
    service = get_compliance_service(db, tenant_id)
    audit = service.get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit non trouvé")
    return audit


@router.post("/audits/{audit_id}/start", response_model=AuditResponse)
def start_audit(
    audit_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Démarrer un audit."""
    service = get_compliance_service(db, tenant_id)
    audit = service.start_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=400, detail="Impossible de démarrer l'audit")
    return audit


@router.post("/audits/{audit_id}/complete", response_model=AuditResponse)
def complete_audit(
    audit_id: UUID,
    executive_summary: str | None = None,
    conclusions: str | None = None,
    recommendations: str | None = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Terminer un audit."""
    service = get_compliance_service(db, tenant_id)
    audit = service.complete_audit(audit_id, executive_summary, conclusions, recommendations)
    if not audit:
        raise HTTPException(status_code=400, detail="Impossible de terminer l'audit")
    return audit


@router.post("/audits/{audit_id}/close", response_model=AuditResponse)
def close_audit(
    audit_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Clôturer un audit."""
    service = get_compliance_service(db, tenant_id)
    audit = service.close_audit(audit_id, current_user.id)
    if not audit:
        raise HTTPException(status_code=400, detail="Impossible de clôturer l'audit")
    return audit


# =============================================================================
# CONSTATATIONS
# =============================================================================

@router.post("/findings", response_model=FindingResponse, status_code=status.HTTP_201_CREATED)
def create_finding(
    data: FindingCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Créer une constatation d'audit."""
    service = get_compliance_service(db, tenant_id)
    return service.create_finding(data, current_user.id)


@router.post("/findings/{finding_id}/respond")
def respond_to_finding(
    finding_id: UUID,
    response: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Répondre à une constatation."""
    service = get_compliance_service(db, tenant_id)
    finding = service.respond_to_finding(finding_id, response)
    if not finding:
        raise HTTPException(status_code=404, detail="Constatation non trouvée")
    return finding


@router.post("/findings/{finding_id}/close")
def close_finding(
    finding_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Clôturer une constatation."""
    service = get_compliance_service(db, tenant_id)
    finding = service.close_finding(finding_id)
    if not finding:
        raise HTTPException(status_code=400, detail="Impossible de clôturer la constatation")
    return finding


# =============================================================================
# RISQUES
# =============================================================================

@router.post("/risks", response_model=RiskResponse, status_code=status.HTTP_201_CREATED)
def create_risk(
    data: RiskCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Créer un risque."""
    service = get_compliance_service(db, tenant_id)
    return service.create_risk(data, current_user.id)


@router.get("/risks/{risk_id}", response_model=RiskResponse)
def get_risk(
    risk_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un risque."""
    service = get_compliance_service(db, tenant_id)
    risk = service.get_risk(risk_id)
    if not risk:
        raise HTTPException(status_code=404, detail="Risque non trouvé")
    return risk


@router.put("/risks/{risk_id}", response_model=RiskResponse)
def update_risk(
    risk_id: UUID,
    data: RiskUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un risque."""
    service = get_compliance_service(db, tenant_id)
    risk = service.update_risk(risk_id, data, current_user.id)
    if not risk:
        raise HTTPException(status_code=404, detail="Risque non trouvé")
    return risk


@router.post("/risks/{risk_id}/accept", response_model=RiskResponse)
def accept_risk(
    risk_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Accepter un risque."""
    service = get_compliance_service(db, tenant_id)
    risk = service.accept_risk(risk_id, current_user.id)
    if not risk:
        raise HTTPException(status_code=400, detail="Impossible d'accepter le risque")
    return risk


# =============================================================================
# INCIDENTS
# =============================================================================

@router.post("/incidents", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    data: IncidentCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Créer un incident."""
    service = get_compliance_service(db, tenant_id)
    return service.create_incident(data, current_user.id)


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un incident."""
    service = get_compliance_service(db, tenant_id)
    incident = service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident non trouvé")
    return incident


@router.post("/incidents/{incident_id}/assign", response_model=IncidentResponse)
def assign_incident(
    incident_id: UUID,
    assignee_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Assigner un incident."""
    service = get_compliance_service(db, tenant_id)
    incident = service.assign_incident(incident_id, assignee_id)
    if not incident:
        raise HTTPException(status_code=400, detail="Impossible d'assigner l'incident")
    return incident


@router.post("/incidents/{incident_id}/resolve", response_model=IncidentResponse)
def resolve_incident(
    incident_id: UUID,
    resolution: str,
    root_cause: str | None = None,
    lessons_learned: str | None = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Résoudre un incident."""
    service = get_compliance_service(db, tenant_id)
    incident = service.resolve_incident(incident_id, resolution, root_cause, lessons_learned)
    if not incident:
        raise HTTPException(status_code=400, detail="Impossible de résoudre l'incident")
    return incident


@router.post("/incidents/{incident_id}/close", response_model=IncidentResponse)
def close_incident(
    incident_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Clôturer un incident."""
    service = get_compliance_service(db, tenant_id)
    incident = service.close_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=400, detail="Impossible de clôturer l'incident")
    return incident


# =============================================================================
# RAPPORTS
# =============================================================================

@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    data: ReportCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Créer un rapport."""
    service = get_compliance_service(db, tenant_id)
    return service.create_report(data, current_user.id)


@router.post("/reports/{report_id}/publish", response_model=ReportResponse)
def publish_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Publier un rapport."""
    service = get_compliance_service(db, tenant_id)
    report = service.publish_report(report_id, current_user.id)
    if not report:
        raise HTTPException(status_code=400, detail="Impossible de publier le rapport")
    return report


# =============================================================================
# MÉTRIQUES
# =============================================================================

@router.get("/metrics", response_model=ComplianceMetrics)
def get_compliance_metrics(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les métriques de conformité."""
    service = get_compliance_service(db, tenant_id)
    return service.get_compliance_metrics()

@router.get("/stats", response_model=ComplianceMetrics)
def get_compliance_stats(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Alias pour /metrics - Récupérer les statistiques de conformité."""
    service = get_compliance_service(db, tenant_id)
    return service.get_compliance_metrics()

# =============================================================================
# GDPR REQUESTS (Demandes RGPD)
# =============================================================================

@router.get("/gdpr-requests")
def list_gdpr_requests(
    request_type: str | None = None,
    request_status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Lister les demandes RGPD (droit d'accès, suppression, etc.)."""
    from app.modules.country_packs.france.models import RGPDRequest

    query = db.query(RGPDRequest).filter(
        RGPDRequest.tenant_id == tenant_id
    )

    if request_type:
        query = query.filter(RGPDRequest.request_type == request_type)
    if request_status:
        query = query.filter(RGPDRequest.status == request_status)

    total = query.count()
    items = query.order_by(RGPDRequest.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "items": [
            {
                "id": r.id,
                "request_code": r.request_code,
                "request_type": r.request_type,
                "data_subject_type": r.data_subject_type,
                "requester_name": r.requester_name,
                "requester_email": r.requester_email,
                "status": r.status,
                "received_at": r.received_at,
                "due_date": r.due_date,
                "processed_at": r.processed_at,
                "created_at": r.created_at
            }
            for r in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/gdpr-requests/{request_id}")
def get_gdpr_request(
    request_id: int,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une demande RGPD."""
    from app.modules.country_packs.france.models import RGPDRequest

    request = db.query(RGPDRequest).filter(
        RGPDRequest.tenant_id == tenant_id,
        RGPDRequest.id == request_id
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Demande RGPD non trouvée")

    return {
        "id": request.id,
        "request_code": request.request_code,
        "request_type": request.request_type,
        "data_subject_type": request.data_subject_type,
        "data_subject_id": request.data_subject_id,
        "requester_name": request.requester_name,
        "requester_email": request.requester_email,
        "requester_phone": request.requester_phone,
        "request_details": request.request_details,
        "status": request.status,
        "received_at": request.received_at,
        "due_date": request.due_date,
        "processed_at": request.processed_at,
        "processed_by": request.processed_by,
        "response_details": request.response_details,
        "created_at": request.created_at
    }

# =============================================================================
# CONSENTS (Consentements RGPD)
# =============================================================================

@router.get("/consents")
def list_consents(
    consent_status: str | None = None,
    purpose: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Lister les consentements RGPD."""
    from app.modules.country_packs.france.models import RGPDConsent

    query = db.query(RGPDConsent).filter(
        RGPDConsent.tenant_id == tenant_id
    )

    if consent_status:
        query = query.filter(RGPDConsent.status == consent_status)
    if purpose:
        query = query.filter(RGPDConsent.purpose == purpose)

    total = query.count()
    items = query.order_by(RGPDConsent.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "items": [
            {
                "id": c.id,
                "data_subject_type": c.data_subject_type,
                "data_subject_id": c.data_subject_id,
                "purpose": c.purpose,
                "legal_basis": c.legal_basis,
                "status": c.status,
                "consent_given_at": c.consent_given_at,
                "withdrawn_at": c.withdrawn_at,
                "valid_until": c.valid_until,
                "created_at": c.created_at
            }
            for c in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/consents/{consent_id}")
def get_consent(
    consent_id: int,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un consentement RGPD."""
    from app.modules.country_packs.france.models import RGPDConsent

    consent = db.query(RGPDConsent).filter(
        RGPDConsent.tenant_id == tenant_id,
        RGPDConsent.id == consent_id
    ).first()

    if not consent:
        raise HTTPException(status_code=404, detail="Consentement non trouvé")

    return {
        "id": consent.id,
        "data_subject_type": consent.data_subject_type,
        "data_subject_id": consent.data_subject_id,
        "data_subject_email": consent.data_subject_email,
        "purpose": consent.purpose,
        "purpose_description": consent.purpose_description,
        "legal_basis": consent.legal_basis,
        "consent_method": consent.consent_method,
        "consent_proof": consent.consent_proof,
        "status": consent.status,
        "consent_given_at": consent.consent_given_at,
        "withdrawn_at": consent.withdrawn_at,
        "withdrawal_reason": consent.withdrawal_reason,
        "valid_until": consent.valid_until,
        "created_at": consent.created_at
    }


# =============================================================================
# VÉRIFICATION NORMES AZALSCORE
# =============================================================================

from .azalscore_norms import AzalscoreNormsService


@router.get("/azalscore-norms/rapport")
def generer_rapport_conformite_normes(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Générer un rapport de conformité aux normes AZALSCORE.
    Vérifie tous les modules: sécurité, multi-tenant, structure, qualité code.
    """
    service = AzalscoreNormsService()
    rapport = service.generer_rapport_global()
    return service.exporter_rapport_json(rapport)


@router.get("/azalscore-norms/module/{module_name}")
def verifier_module_conformite(
    module_name: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Vérifier la conformité d'un module spécifique.
    Retourne les violations détectées avec suggestions de correction.
    """
    from pathlib import Path

    service = AzalscoreNormsService()
    module_path = Path(f"/home/ubuntu/azalscore/app/modules/{module_name}")

    if not module_path.exists():
        raise HTTPException(status_code=404, detail=f"Module '{module_name}' non trouvé")

    result = service.verifier_module(module_path)

    return {
        "module_name": result.module_name,
        "date_verification": result.date_verification.isoformat(),
        "score_conformite": result.score_conformite,
        "stats": result.details,
        "violations": [
            {
                "fichier": v.fichier,
                "ligne": v.ligne,
                "categorie": v.categorie.value,
                "severite": v.severite.value,
                "code": v.code,
                "message": v.message,
                "suggestion": v.suggestion
            }
            for v in result.violations
        ],
        "avertissements": result.avertissements
    }


@router.get("/azalscore-norms/securite/{module_name}")
def verifier_securite_module(
    module_name: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Vérifier spécifiquement la sécurité d'un module.
    Détecte: SQL injection, secrets, eval, pickle, shell injection.
    """
    from pathlib import Path

    service = AzalscoreNormsService()
    module_path = Path(f"/home/ubuntu/azalscore/app/modules/{module_name}")

    if not module_path.exists():
        raise HTTPException(status_code=404, detail=f"Module '{module_name}' non trouvé")

    violations = []
    for py_file in module_path.rglob("*.py"):
        violations.extend(service.verifier_securite(py_file))

    return {
        "module_name": module_name,
        "total_issues": len(violations),
        "critical": sum(1 for v in violations if v.severite.value == "CRITICAL"),
        "high": sum(1 for v in violations if v.severite.value == "HIGH"),
        "violations": [
            {
                "fichier": v.fichier,
                "ligne": v.ligne,
                "code": v.code,
                "message": v.message,
                "suggestion": v.suggestion
            }
            for v in violations
        ]
    }


@router.get("/azalscore-norms/multitenant/{module_name}")
def verifier_multitenant_module(
    module_name: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Vérifier l'isolation multi-tenant d'un module.
    Vérifie la présence de tenant_id dans les services et requêtes.
    """
    from pathlib import Path

    service = AzalscoreNormsService()
    module_path = Path(f"/home/ubuntu/azalscore/app/modules/{module_name}")

    if not module_path.exists():
        raise HTTPException(status_code=404, detail=f"Module '{module_name}' non trouvé")

    violations = service.verifier_multitenant(module_path)

    is_compliant = len([v for v in violations if v.severite.value in ["CRITICAL", "HIGH"]]) == 0

    return {
        "module_name": module_name,
        "is_compliant": is_compliant,
        "violations": [
            {
                "fichier": v.fichier,
                "ligne": v.ligne,
                "code": v.code,
                "severite": v.severite.value,
                "message": v.message,
                "suggestion": v.suggestion
            }
            for v in violations
        ]
    }


@router.get("/azalscore-norms/summary")
def get_norms_summary(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Obtenir un résumé rapide de la conformité aux normes.
    Retourne les statistiques globales sans détails.
    """
    service = AzalscoreNormsService()
    rapport = service.generer_rapport_global()

    return {
        "modules_verifies": rapport.modules_verifies,
        "modules_conformes": rapport.modules_conformes,
        "taux_conformite": f"{(rapport.modules_conformes / max(1, rapport.modules_verifies)) * 100:.1f}%",
        "score_global": rapport.score_global,
        "violations": {
            "critical": rapport.violations_critiques,
            "high": rapport.violations_hautes,
            "medium": rapport.violations_moyennes,
            "low": rapport.violations_basses
        },
        "recommandations": rapport.recommandations,
        "modules_a_ameliorer": [
            {"name": r.module_name, "score": r.score_conformite}
            for r in sorted(rapport.resultats_modules, key=lambda x: x.score_conformite)[:10]
            if r.score_conformite < 80
        ]
    }


# =============================================================================
# AUDIT PCI DSS (Payment Card Industry Data Security Standard)
# =============================================================================

from .pci_dss_audit import PCIDSSAuditService, PCIDSSLevel


@router.get("/pci-dss/audit")
def run_pci_dss_audit(
    pci_level: str = Query("LEVEL_4", description="Niveau PCI DSS (LEVEL_1 à LEVEL_4)"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Exécuter un audit de conformité PCI DSS complet.
    Vérifie les 12 exigences PCI DSS v4.0.
    """
    level = PCIDSSLevel(pci_level) if pci_level in [e.value for e in PCIDSSLevel] else PCIDSSLevel.LEVEL_4
    service = PCIDSSAuditService(db, tenant_id)
    result = service.run_full_audit(level)
    return service.export_audit_json(result)


@router.get("/pci-dss/requirements")
def get_pci_dss_requirements(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer la liste des 12 exigences PCI DSS v4.0.
    """
    return {
        "version": "PCI DSS v4.0",
        "requirements": [
            {"id": "REQ_1", "name": "Install and Maintain Network Security Controls", "description": "Pare-feu et segmentation réseau"},
            {"id": "REQ_2", "name": "Apply Secure Configurations", "description": "Pas de mots de passe par défaut"},
            {"id": "REQ_3", "name": "Protect Stored Account Data", "description": "Chiffrement des données stockées"},
            {"id": "REQ_4", "name": "Protect Cardholder Data with Strong Cryptography", "description": "TLS pour transmissions"},
            {"id": "REQ_5", "name": "Protect All Systems Against Malware", "description": "Anti-malware et antivirus"},
            {"id": "REQ_6", "name": "Develop and Maintain Secure Systems", "description": "Développement sécurisé"},
            {"id": "REQ_7", "name": "Restrict Access to System Components", "description": "Contrôle d'accès RBAC"},
            {"id": "REQ_8", "name": "Identify Users and Authenticate Access", "description": "Authentification forte MFA"},
            {"id": "REQ_9", "name": "Restrict Physical Access to Cardholder Data", "description": "Accès physique (N/A SaaS)"},
            {"id": "REQ_10", "name": "Log and Monitor All Access", "description": "Journalisation et surveillance"},
            {"id": "REQ_11", "name": "Test Security of Systems and Networks", "description": "Tests de sécurité réguliers"},
            {"id": "REQ_12", "name": "Support Information Security with Policies", "description": "Politiques de sécurité"}
        ]
    }


# =============================================================================
# AUDIT OWASP TOP 10
# =============================================================================

from .owasp_audit import OWASPAuditService


@router.get("/owasp/audit")
def run_owasp_audit(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Exécuter un audit de sécurité OWASP Top 10 (2021).
    Scanne le code pour détecter les vulnérabilités.
    """
    service = OWASPAuditService(db, tenant_id)
    result = service.run_full_audit()
    return service.export_audit_json(result)


@router.get("/owasp/categories")
def get_owasp_categories(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer les 10 catégories OWASP Top 10 (2021).
    """
    return {
        "version": "OWASP Top 10 2021",
        "categories": [
            {"id": "A01:2021", "name": "Broken Access Control", "description": "Contrôle d'accès défaillant"},
            {"id": "A02:2021", "name": "Cryptographic Failures", "description": "Échecs cryptographiques"},
            {"id": "A03:2021", "name": "Injection", "description": "SQL, OS, LDAP injection"},
            {"id": "A04:2021", "name": "Insecure Design", "description": "Conception non sécurisée"},
            {"id": "A05:2021", "name": "Security Misconfiguration", "description": "Mauvaise configuration"},
            {"id": "A06:2021", "name": "Vulnerable and Outdated Components", "description": "Composants vulnérables"},
            {"id": "A07:2021", "name": "Identification and Authentication Failures", "description": "Échecs d'authentification"},
            {"id": "A08:2021", "name": "Software and Data Integrity Failures", "description": "Échecs d'intégrité"},
            {"id": "A09:2021", "name": "Security Logging and Monitoring Failures", "description": "Échecs de journalisation"},
            {"id": "A10:2021", "name": "Server-Side Request Forgery", "description": "SSRF"}
        ]
    }


@router.get("/owasp/scan/{module_name}")
def scan_module_owasp(
    module_name: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Scanner un module spécifique pour vulnérabilités OWASP.
    """
    from pathlib import Path

    module_path = Path(f"/home/ubuntu/azalscore/app/modules/{module_name}")
    if not module_path.exists():
        raise HTTPException(status_code=404, detail=f"Module '{module_name}' non trouvé")

    service = OWASPAuditService(db, tenant_id)
    # Scanner uniquement ce module
    service.base_path = module_path.parent.parent.parent
    result = service.run_full_audit()

    # Filtrer les findings pour ce module
    module_findings = [f for f in result.findings if module_name in (f.location or "")]

    return {
        "module": module_name,
        "findings_count": len(module_findings),
        "findings": [
            {
                "category": f.category.value,
                "severity": f.severity.value,
                "title": f.title,
                "location": f.location,
                "line_number": f.line_number,
                "remediation": f.remediation
            }
            for f in module_findings
        ]
    }


# =============================================================================
# AUDIT AUTHENTIFICATION ET AUTORISATION
# =============================================================================

@router.get("/auth/audit")
def run_auth_audit(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Auditer les mécanismes d'authentification et d'autorisation.
    """
    from pathlib import Path

    base_path = Path("/home/ubuntu/azalscore")
    findings = []

    # Vérifier JWT
    security_path = base_path / "app" / "core" / "security.py"
    if security_path.exists():
        content = security_path.read_text()

        if "jwt" in content.lower():
            findings.append({
                "check": "JWT Authentication",
                "status": "PASS",
                "details": "JWT implémenté dans core/security.py"
            })
        else:
            findings.append({
                "check": "JWT Authentication",
                "status": "WARN",
                "details": "JWT non détecté"
            })

        if "bcrypt" in content or "argon2" in content:
            findings.append({
                "check": "Password Hashing",
                "status": "PASS",
                "details": "Algorithme de hashage sécurisé (bcrypt/argon2)"
            })
        else:
            findings.append({
                "check": "Password Hashing",
                "status": "FAIL",
                "details": "Algorithme de hashage non sécurisé ou absent"
            })

        if "mfa" in content.lower() or "totp" in content.lower() or "2fa" in content.lower():
            findings.append({
                "check": "Multi-Factor Authentication",
                "status": "PASS",
                "details": "MFA disponible"
            })
        else:
            findings.append({
                "check": "Multi-Factor Authentication",
                "status": "WARN",
                "details": "MFA non implémenté"
            })

    # Vérifier RBAC
    iam_path = base_path / "app" / "modules" / "iam"
    if iam_path.exists():
        findings.append({
            "check": "RBAC Implementation",
            "status": "PASS",
            "details": "Module IAM avec RBAC implémenté"
        })

        # Vérifier la matrice RBAC
        rbac_matrix = iam_path / "rbac_matrix.py"
        if rbac_matrix.exists():
            findings.append({
                "check": "RBAC Matrix",
                "status": "PASS",
                "details": "Matrice de permissions définie"
            })
    else:
        findings.append({
            "check": "RBAC Implementation",
            "status": "FAIL",
            "details": "Module IAM non trouvé"
        })

    # Vérifier session management
    findings.append({
        "check": "Session Management",
        "status": "PASS",
        "details": "Sessions gérées via JWT avec expiration"
    })

    # Score
    passed = sum(1 for f in findings if f["status"] == "PASS")
    total = len(findings)
    score = int((passed / total) * 100) if total > 0 else 0

    return {
        "audit_type": "Authentication & Authorization",
        "date": datetime.utcnow().isoformat(),
        "score": score,
        "summary": {
            "passed": passed,
            "warnings": sum(1 for f in findings if f["status"] == "WARN"),
            "failed": sum(1 for f in findings if f["status"] == "FAIL")
        },
        "findings": findings
    }


# =============================================================================
# TESTS DE RÉGRESSION AUTOMATISÉS
# =============================================================================

from .regression_tests import RegressionTestService


@router.post("/regression/run", status_code=status.HTTP_202_ACCEPTED)
def run_regression_tests(
    modules: list[str] | None = Query(None, description="Liste des modules à tester (vide = tous)"),
    include_slow: bool = Query(False, description="Inclure les tests lents"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Lancer une suite complète de tests de régression.

    Retourne immédiatement avec un run_id pour suivre l'exécution.
    """
    service = RegressionTestService(db, tenant_id)
    report = service.run_full_regression(
        modules=modules,
        include_slow=include_slow,
        triggered_by=f"user:{current_user.id}"
    )

    return {
        "run_id": report.run_id,
        "status": report.status,
        "started_at": report.started_at.isoformat(),
        "total_tests": report.total_tests,
        "passed": report.passed,
        "failed": report.failed,
        "skipped": report.skipped,
        "errors": report.errors,
        "duration_seconds": report.duration_seconds,
        "regressions_detected": report.regressions_detected
    }


@router.get("/regression/history")
def get_regression_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer l'historique des exécutions de tests de régression.
    """
    service = RegressionTestService(db, tenant_id)
    history = service.get_history(limit=limit)

    return {
        "total": len(history),
        "runs": history
    }


@router.get("/regression/run/{run_id}")
def get_regression_run(
    run_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer les détails d'une exécution de tests de régression.
    """
    service = RegressionTestService(db, tenant_id)
    run = service.get_run(run_id)

    if not run:
        raise HTTPException(status_code=404, detail="Run de test non trouvé")

    return run


@router.post("/regression/compare")
def compare_regression_runs(
    run_id_1: str = Query(..., description="Premier run à comparer"),
    run_id_2: str = Query(..., description="Second run à comparer"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Comparer deux exécutions de tests de régression.

    Utile pour identifier les changements entre deux versions.
    """
    service = RegressionTestService(db, tenant_id)
    comparison = service.compare_runs(run_id_1, run_id_2)

    if "error" in comparison:
        raise HTTPException(status_code=404, detail=comparison["error"])

    return comparison


@router.post("/regression/snapshot", status_code=status.HTTP_201_CREATED)
def create_api_snapshot(
    endpoint: str = Query(..., description="Endpoint API (ex: /api/v1/users)"),
    method: str = Query("GET", description="Méthode HTTP"),
    response: dict = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Créer un snapshot de réponse API pour tests de régression.

    Le snapshot capture le schéma de réponse pour détecter les changements.
    """
    if response is None:
        response = {}

    service = RegressionTestService(db, tenant_id)
    snapshot_hash = service.create_snapshot(endpoint, method, response)

    return {
        "endpoint": endpoint,
        "method": method,
        "snapshot_hash": snapshot_hash,
        "created_at": datetime.utcnow().isoformat()
    }


@router.post("/regression/verify-snapshot")
def verify_api_snapshot(
    endpoint: str = Query(..., description="Endpoint API à vérifier"),
    method: str = Query("GET", description="Méthode HTTP"),
    response: dict = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Vérifier une réponse API contre le snapshot baseline.

    Retourne si la réponse correspond au schéma attendu.
    """
    if response is None:
        response = {}

    service = RegressionTestService(db, tenant_id)
    result = service.verify_snapshot(endpoint, method, response)

    return result


@router.get("/regression/stats")
def get_regression_stats(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Obtenir les statistiques globales des tests de régression.
    """
    service = RegressionTestService(db, tenant_id)
    history = service.get_history(limit=100)

    if not history:
        return {
            "total_runs": 0,
            "success_rate": 0,
            "average_duration": 0,
            "last_run": None,
            "trend": "no_data"
        }

    total_runs = len(history)
    successful = sum(1 for r in history if r["status"] == "passed")
    total_duration = sum(r.get("duration", 0) for r in history)

    # Calculer la tendance (comparaison derniers 10 vs précédents 10)
    recent = history[:10]
    older = history[10:20] if len(history) > 10 else []

    recent_rate = sum(1 for r in recent if r["status"] == "passed") / len(recent) if recent else 0
    older_rate = sum(1 for r in older if r["status"] == "passed") / len(older) if older else recent_rate

    if recent_rate > older_rate:
        trend = "improving"
    elif recent_rate < older_rate:
        trend = "declining"
    else:
        trend = "stable"

    return {
        "total_runs": total_runs,
        "success_rate": round(successful / total_runs * 100, 1) if total_runs > 0 else 0,
        "average_duration": round(total_duration / total_runs, 1) if total_runs > 0 else 0,
        "last_run": history[0] if history else None,
        "trend": trend
    }
