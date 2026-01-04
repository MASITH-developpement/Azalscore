"""
AZALS MODULE M11 - Router Conformité
====================================

Routes API pour la gestion de la conformité réglementaire.
"""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, get_current_tenant

from .schemas import (
    RegulationCreate, RegulationUpdate, RegulationResponse,
    RequirementCreate, RequirementUpdate, RequirementResponse,
    AssessmentCreate, AssessmentUpdate, AssessmentResponse,
    GapCreate, GapResponse,
    ActionCreate, ActionUpdate, ActionResponse,
    PolicyCreate, PolicyUpdate, PolicyResponse,
    AcknowledgmentCreate, AcknowledgmentResponse,
    TrainingCreate, TrainingUpdate, TrainingResponse,
    CompletionCreate, CompletionResponse,
    DocumentCreate, DocumentUpdate, DocumentResponse,
    AuditCreate, AuditUpdate, AuditResponse,
    FindingCreate, FindingResponse,
    RiskCreate, RiskUpdate, RiskResponse,
    IncidentCreate, IncidentUpdate, IncidentResponse,
    ReportCreate, ReportResponse,
    ComplianceMetrics
)

from .models import (
    ComplianceStatus, RegulationType, RequirementPriority,
    AssessmentStatus, RiskLevel, ActionStatus, AuditStatus
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Créer une nouvelle réglementation."""
    service = get_compliance_service(db, tenant_id)
    return service.create_regulation(data, current_user["id"])


@router.get("/regulations", response_model=List[RegulationResponse])
def list_regulations(
    regulation_type: Optional[RegulationType] = None,
    is_active: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Lister les réglementations."""
    service = get_compliance_service(db, tenant_id)
    return service.get_regulations(regulation_type, is_active, skip, limit)


@router.get("/regulations/{regulation_id}", response_model=RegulationResponse)
def get_regulation(
    regulation_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour une réglementation."""
    service = get_compliance_service(db, tenant_id)
    regulation = service.update_regulation(regulation_id, data, current_user["id"])
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Créer une nouvelle exigence."""
    service = get_compliance_service(db, tenant_id)
    return service.create_requirement(data, current_user["id"])


@router.get("/requirements", response_model=List[RequirementResponse])
def list_requirements(
    regulation_id: Optional[UUID] = None,
    compliance_status: Optional[ComplianceStatus] = None,
    priority: Optional[RequirementPriority] = None,
    is_active: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Lister les exigences."""
    service = get_compliance_service(db, tenant_id)
    return service.get_requirements(regulation_id, compliance_status, priority, is_active, skip, limit)


@router.get("/requirements/{requirement_id}", response_model=RequirementResponse)
def get_requirement(
    requirement_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour une exigence."""
    service = get_compliance_service(db, tenant_id)
    requirement = service.update_requirement(requirement_id, data, current_user["id"])
    if not requirement:
        raise HTTPException(status_code=404, detail="Exigence non trouvée")
    return requirement


@router.post("/requirements/{requirement_id}/assess", response_model=RequirementResponse)
def assess_requirement(
    requirement_id: UUID,
    status: ComplianceStatus,
    score: Optional[Decimal] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Évaluer la conformité d'une exigence."""
    service = get_compliance_service(db, tenant_id)
    requirement = service.assess_requirement(requirement_id, status, score, current_user["id"])
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Créer une nouvelle évaluation."""
    service = get_compliance_service(db, tenant_id)
    return service.create_assessment(data, current_user["id"])


@router.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    findings_summary: Optional[str] = None,
    recommendations: Optional[str] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Approuver une évaluation."""
    service = get_compliance_service(db, tenant_id)
    assessment = service.approve_assessment(assessment_id, current_user["id"])
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Créer un écart de conformité."""
    service = get_compliance_service(db, tenant_id)
    return service.create_gap(data, current_user["id"])


@router.post("/gaps/{gap_id}/close", response_model=GapResponse)
def close_gap(
    gap_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Créer une action corrective."""
    service = get_compliance_service(db, tenant_id)
    return service.create_action(data, current_user["id"])


@router.get("/actions/{action_id}", response_model=ActionResponse)
def get_action(
    action_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    evidence: Optional[List[str]] = None,
    actual_cost: Optional[Decimal] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    verification_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Vérifier une action."""
    service = get_compliance_service(db, tenant_id)
    action = service.verify_action(action_id, current_user["id"], verification_notes)
    if not action:
        raise HTTPException(status_code=400, detail="Impossible de vérifier l'action")
    return action


@router.get("/actions/overdue", response_model=List[ActionResponse])
def get_overdue_actions(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les actions en retard."""
    service = get_compliance_service(db, tenant_id)
    return service.get_overdue_actions()


# =============================================================================
# POLITIQUES
# =============================================================================

@router.post("/policies", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
def create_policy(
    data: PolicyCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Créer une politique."""
    service = get_compliance_service(db, tenant_id)
    return service.create_policy(data, current_user["id"])


@router.get("/policies/{policy_id}", response_model=PolicyResponse)
def get_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Publier une politique."""
    service = get_compliance_service(db, tenant_id)
    policy = service.publish_policy(policy_id, current_user["id"])
    if not policy:
        raise HTTPException(status_code=400, detail="Impossible de publier la politique")
    return policy


@router.post("/policies/acknowledge", response_model=AcknowledgmentResponse, status_code=status.HTTP_201_CREATED)
def acknowledge_policy(
    data: AcknowledgmentCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Accuser réception d'une politique."""
    service = get_compliance_service(db, tenant_id)
    return service.acknowledge_policy(data, current_user["id"])


# =============================================================================
# FORMATIONS
# =============================================================================

@router.post("/trainings", response_model=TrainingResponse, status_code=status.HTTP_201_CREATED)
def create_training(
    data: TrainingCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Créer une formation."""
    service = get_compliance_service(db, tenant_id)
    return service.create_training(data, current_user["id"])


@router.get("/trainings/{training_id}", response_model=TrainingResponse)
def get_training(
    training_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Assigner une formation à un utilisateur."""
    service = get_compliance_service(db, tenant_id)
    return service.assign_training(data, current_user["id"])


@router.post("/trainings/completions/{completion_id}/start", response_model=CompletionResponse)
def start_training_completion(
    completion_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    certificate_number: Optional[str] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Créer un audit."""
    service = get_compliance_service(db, tenant_id)
    return service.create_audit(data, current_user["id"])


@router.get("/audits/{audit_id}", response_model=AuditResponse)
def get_audit(
    audit_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    executive_summary: Optional[str] = None,
    conclusions: Optional[str] = None,
    recommendations: Optional[str] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Clôturer un audit."""
    service = get_compliance_service(db, tenant_id)
    audit = service.close_audit(audit_id, current_user["id"])
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Créer une constatation d'audit."""
    service = get_compliance_service(db, tenant_id)
    return service.create_finding(data, current_user["id"])


@router.post("/findings/{finding_id}/respond")
def respond_to_finding(
    finding_id: UUID,
    response: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Créer un risque."""
    service = get_compliance_service(db, tenant_id)
    return service.create_risk(data, current_user["id"])


@router.get("/risks/{risk_id}", response_model=RiskResponse)
def get_risk(
    risk_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour un risque."""
    service = get_compliance_service(db, tenant_id)
    risk = service.update_risk(risk_id, data, current_user["id"])
    if not risk:
        raise HTTPException(status_code=404, detail="Risque non trouvé")
    return risk


@router.post("/risks/{risk_id}/accept", response_model=RiskResponse)
def accept_risk(
    risk_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Accepter un risque."""
    service = get_compliance_service(db, tenant_id)
    risk = service.accept_risk(risk_id, current_user["id"])
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Créer un incident."""
    service = get_compliance_service(db, tenant_id)
    return service.create_incident(data, current_user["id"])


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    root_cause: Optional[str] = None,
    lessons_learned: Optional[str] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
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
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Créer un rapport."""
    service = get_compliance_service(db, tenant_id)
    return service.create_report(data, current_user["id"])


@router.post("/reports/{report_id}/publish", response_model=ReportResponse)
def publish_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Publier un rapport."""
    service = get_compliance_service(db, tenant_id)
    report = service.publish_report(report_id, current_user["id"])
    if not report:
        raise HTTPException(status_code=400, detail="Impossible de publier le rapport")
    return report


# =============================================================================
# MÉTRIQUES
# =============================================================================

@router.get("/metrics", response_model=ComplianceMetrics)
def get_compliance_metrics(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les métriques de conformité."""
    service = get_compliance_service(db, tenant_id)
    return service.get_compliance_metrics()
