"""
AZALS MODULE COMPLIANCE - Router Unifié
========================================
Router unifié compatible v1/v2 via double enregistrement.
Utilise get_context() de app.core.compat pour l'isolation tenant.
"""

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db

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
# REGLEMENTATIONS
# =============================================================================

@router.post("/regulations", response_model=RegulationResponse, status_code=status.HTTP_201_CREATED)
def create_regulation(
    data: RegulationCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer une nouvelle réglementation."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.create_regulation(data, context.user_id)

@router.get("/regulations", response_model=list[RegulationResponse])
def list_regulations(
    regulation_type: RegulationType | None = None,
    is_active: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les réglementations."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.get_regulations(regulation_type, is_active, skip, limit)

@router.get("/regulations/{regulation_id}", response_model=RegulationResponse)
def get_regulation(
    regulation_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer une réglementation."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    regulation = service.get_regulation(regulation_id)
    if not regulation:
        raise HTTPException(status_code=404, detail="Réglementation non trouvée")
    return regulation

@router.put("/regulations/{regulation_id}", response_model=RegulationResponse)
def update_regulation(
    regulation_id: UUID,
    data: RegulationUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Mettre à jour une réglementation."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    regulation = service.update_regulation(regulation_id, data, context.user_id)
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
    context: SaaSContext = Depends(get_context)
):
    """Créer une nouvelle exigence."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.create_requirement(data, context.user_id)

@router.get("/requirements", response_model=list[RequirementResponse])
def list_requirements(
    regulation_id: UUID | None = None,
    compliance_status: ComplianceStatus | None = None,
    priority: RequirementPriority | None = None,
    is_active: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les exigences."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.get_requirements(regulation_id, compliance_status, priority, is_active, skip, limit)

@router.get("/requirements/{requirement_id}", response_model=RequirementResponse)
def get_requirement(
    requirement_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer une exigence."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    requirement = service.get_requirement(requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Exigence non trouvée")
    return requirement

@router.put("/requirements/{requirement_id}", response_model=RequirementResponse)
def update_requirement(
    requirement_id: UUID,
    data: RequirementUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Mettre à jour une exigence."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    requirement = service.update_requirement(requirement_id, data, context.user_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Exigence non trouvée")
    return requirement

@router.post("/requirements/{requirement_id}/assess", response_model=RequirementResponse)
def assess_requirement(
    requirement_id: UUID,
    status: ComplianceStatus,
    score: Decimal | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Évaluer la conformité d'une exigence."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    requirement = service.assess_requirement(requirement_id, status, score, context.user_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Exigence non trouvée")
    return requirement

# =============================================================================
# EVALUATIONS
# =============================================================================

@router.post("/assessments", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_assessment(
    data: AssessmentCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer une nouvelle évaluation."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.create_assessment(data, context.user_id)

@router.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer une évaluation."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    assessment = service.get_assessment(assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Évaluation non trouvée")
    return assessment

@router.post("/assessments/{assessment_id}/start", response_model=AssessmentResponse)
def start_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Démarrer une évaluation."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
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
    context: SaaSContext = Depends(get_context)
):
    """Terminer une évaluation."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    assessment = service.complete_assessment(assessment_id, findings_summary, recommendations)
    if not assessment:
        raise HTTPException(status_code=400, detail="Impossible de terminer l'évaluation")
    return assessment

@router.post("/assessments/{assessment_id}/approve", response_model=AssessmentResponse)
def approve_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Approuver une évaluation."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    assessment = service.approve_assessment(assessment_id, context.user_id)
    if not assessment:
        raise HTTPException(status_code=400, detail="Impossible d'approuver l'évaluation")
    return assessment

# =============================================================================
# ECARTS
# =============================================================================

@router.post("/gaps", response_model=GapResponse, status_code=status.HTTP_201_CREATED)
def create_gap(
    data: GapCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer un écart de conformité."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.create_gap(data, context.user_id)

@router.post("/gaps/{gap_id}/close", response_model=GapResponse)
def close_gap(
    gap_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Clôturer un écart."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
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
    context: SaaSContext = Depends(get_context)
):
    """Créer une action corrective."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.create_action(data, context.user_id)

@router.get("/actions/{action_id}", response_model=ActionResponse)
def get_action(
    action_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer une action."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    action = service.get_action(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action non trouvée")
    return action

@router.post("/actions/{action_id}/start", response_model=ActionResponse)
def start_action(
    action_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Démarrer une action."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
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
    context: SaaSContext = Depends(get_context)
):
    """Terminer une action."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    action = service.complete_action(action_id, resolution_notes, evidence, actual_cost)
    if not action:
        raise HTTPException(status_code=400, detail="Impossible de terminer l'action")
    return action

@router.post("/actions/{action_id}/verify", response_model=ActionResponse)
def verify_action(
    action_id: UUID,
    verification_notes: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Vérifier une action."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    action = service.verify_action(action_id, context.user_id, verification_notes)
    if not action:
        raise HTTPException(status_code=400, detail="Impossible de vérifier l'action")
    return action

@router.get("/actions/overdue", response_model=list[ActionResponse])
def get_overdue_actions(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer les actions en retard."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
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
    context: SaaSContext = Depends(get_context)
):
    """Lister les politiques."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.get_policies(is_published, skip, limit)

@router.post("/policies", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
def create_policy(
    data: PolicyCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer une politique."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.create_policy(data, context.user_id)

@router.get("/policies/{policy_id}", response_model=PolicyResponse)
def get_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer une politique."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    policy = service.get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Politique non trouvée")
    return policy

@router.post("/policies/{policy_id}/publish", response_model=PolicyResponse)
def publish_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Publier une politique."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    policy = service.publish_policy(policy_id, context.user_id)
    if not policy:
        raise HTTPException(status_code=400, detail="Impossible de publier la politique")
    return policy

@router.post("/policies/acknowledge", response_model=AcknowledgmentResponse, status_code=status.HTTP_201_CREATED)
def acknowledge_policy(
    data: AcknowledgmentCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Accuser réception d'une politique."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.acknowledge_policy(data, context.user_id)

# =============================================================================
# FORMATIONS
# =============================================================================

@router.post("/trainings", response_model=TrainingResponse, status_code=status.HTTP_201_CREATED)
def create_training(
    data: TrainingCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer une formation."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.create_training(data, context.user_id)

@router.get("/trainings/{training_id}", response_model=TrainingResponse)
def get_training(
    training_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer une formation."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    training = service.get_training(training_id)
    if not training:
        raise HTTPException(status_code=404, detail="Formation non trouvée")
    return training

@router.post("/trainings/assign", response_model=CompletionResponse, status_code=status.HTTP_201_CREATED)
def assign_training(
    data: CompletionCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Assigner une formation à un utilisateur."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.assign_training(data, context.user_id)

@router.post("/trainings/completions/{completion_id}/start", response_model=CompletionResponse)
def start_training_completion(
    completion_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Démarrer une formation."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
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
    context: SaaSContext = Depends(get_context)
):
    """Terminer une formation."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    completion = service.complete_training(completion_id, score, certificate_number)
    if not completion:
        raise HTTPException(status_code=400, detail="Impossible de terminer la formation")
    return completion

# =============================================================================
# AUDITS
# =============================================================================

@router.get("/audits", response_model=list[AuditResponse])
def list_audits(
    audit_type: str | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les audits."""
    from .models import AuditStatus as AuditStatusEnum
    audit_status = AuditStatusEnum(status) if status else None
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.get_audits(audit_type, audit_status, skip, limit)

@router.post("/audits", response_model=AuditResponse, status_code=status.HTTP_201_CREATED)
def create_audit(
    data: AuditCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer un audit."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.create_audit(data, context.user_id)

@router.get("/audits/{audit_id}", response_model=AuditResponse)
def get_audit(
    audit_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un audit."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    audit = service.get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit non trouvé")
    return audit

@router.post("/audits/{audit_id}/start", response_model=AuditResponse)
def start_audit(
    audit_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Démarrer un audit."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
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
    context: SaaSContext = Depends(get_context)
):
    """Terminer un audit."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    audit = service.complete_audit(audit_id, executive_summary, conclusions, recommendations)
    if not audit:
        raise HTTPException(status_code=400, detail="Impossible de terminer l'audit")
    return audit

@router.post("/audits/{audit_id}/close", response_model=AuditResponse)
def close_audit(
    audit_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Clôturer un audit."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    audit = service.close_audit(audit_id, context.user_id)
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
    context: SaaSContext = Depends(get_context)
):
    """Créer une constatation d'audit."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.create_finding(data, context.user_id)

@router.post("/findings/{finding_id}/respond")
def respond_to_finding(
    finding_id: UUID,
    response: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Répondre à une constatation."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    finding = service.respond_to_finding(finding_id, response)
    if not finding:
        raise HTTPException(status_code=404, detail="Constatation non trouvée")
    return finding

@router.post("/findings/{finding_id}/close")
def close_finding(
    finding_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Clôturer une constatation."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
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
    context: SaaSContext = Depends(get_context)
):
    """Créer un risque."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.create_risk(data, context.user_id)

@router.get("/risks/{risk_id}", response_model=RiskResponse)
def get_risk(
    risk_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un risque."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    risk = service.get_risk(risk_id)
    if not risk:
        raise HTTPException(status_code=404, detail="Risque non trouvé")
    return risk

@router.put("/risks/{risk_id}", response_model=RiskResponse)
def update_risk(
    risk_id: UUID,
    data: RiskUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Mettre à jour un risque."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    risk = service.update_risk(risk_id, data, context.user_id)
    if not risk:
        raise HTTPException(status_code=404, detail="Risque non trouvé")
    return risk

@router.post("/risks/{risk_id}/accept", response_model=RiskResponse)
def accept_risk(
    risk_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Accepter un risque."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    risk = service.accept_risk(risk_id, context.user_id)
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
    context: SaaSContext = Depends(get_context)
):
    """Créer un incident."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.create_incident(data, context.user_id)

@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un incident."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    incident = service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident non trouvé")
    return incident

@router.post("/incidents/{incident_id}/assign", response_model=IncidentResponse)
def assign_incident(
    incident_id: UUID,
    assignee_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Assigner un incident."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
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
    context: SaaSContext = Depends(get_context)
):
    """Résoudre un incident."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    incident = service.resolve_incident(incident_id, resolution, root_cause, lessons_learned)
    if not incident:
        raise HTTPException(status_code=400, detail="Impossible de résoudre l'incident")
    return incident

@router.post("/incidents/{incident_id}/close", response_model=IncidentResponse)
def close_incident(
    incident_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Clôturer un incident."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
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
    context: SaaSContext = Depends(get_context)
):
    """Créer un rapport."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.create_report(data, context.user_id)

@router.post("/reports/{report_id}/publish", response_model=ReportResponse)
def publish_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Publier un rapport."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    report = service.publish_report(report_id, context.user_id)
    if not report:
        raise HTTPException(status_code=400, detail="Impossible de publier le rapport")
    return report

# =============================================================================
# METRIQUES
# =============================================================================

@router.get("/metrics", response_model=ComplianceMetrics)
def get_compliance_metrics(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer les métriques de conformité."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.get_compliance_metrics()

@router.get("/stats", response_model=ComplianceMetrics)
def get_compliance_stats(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Alias pour /metrics - Récupérer les statistiques de conformité."""
    service = get_compliance_service(db, context.tenant_id, context.user_id)
    return service.get_compliance_metrics()

# =============================================================================
# GDPR REQUESTS (Demandes RGPD)
# =============================================================================

@router.get("/gdpr-requests")
def list_gdpr_requests(
    request_type: str | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les demandes RGPD (droit d'accès, suppression, etc.)."""
    from app.modules.country_packs.france.models import RGPDRequest

    query = db.query(RGPDRequest).filter(
        RGPDRequest.tenant_id == context.tenant_id
    )

    if request_type:
        query = query.filter(RGPDRequest.request_type == request_type)
    if status:
        query = query.filter(RGPDRequest.status == status)

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
    context: SaaSContext = Depends(get_context)
):
    """Récupérer une demande RGPD."""
    from app.modules.country_packs.france.models import RGPDRequest

    request = db.query(RGPDRequest).filter(
        RGPDRequest.tenant_id == context.tenant_id,
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
    status: str | None = None,
    purpose: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les consentements RGPD."""
    from app.modules.country_packs.france.models import RGPDConsent

    query = db.query(RGPDConsent).filter(
        RGPDConsent.tenant_id == context.tenant_id
    )

    if status:
        query = query.filter(RGPDConsent.status == status)
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
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un consentement RGPD."""
    from app.modules.country_packs.france.models import RGPDConsent

    consent = db.query(RGPDConsent).filter(
        RGPDConsent.tenant_id == context.tenant_id,
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
