"""
AZALS MODULE M11 - Service Conformité
=====================================

Service métier pour la gestion de la conformité réglementaire.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import (
    Regulation, Requirement, ComplianceAssessment, ComplianceGap,
    ComplianceAction, Policy, PolicyAcknowledgment,
    ComplianceTraining, TrainingCompletion,
    ComplianceDocument, ComplianceAudit, ComplianceAuditFinding as AuditFinding,
    ComplianceRisk, ComplianceIncident, ComplianceReport,
    ComplianceStatus, RegulationType, RequirementPriority,
    AssessmentStatus, RiskLevel, ActionStatus, AuditStatus, FindingSeverity, IncidentStatus
)

from .schemas import (
    RegulationCreate, RegulationUpdate,
    RequirementCreate, RequirementUpdate,
    AssessmentCreate, GapCreate,
    ActionCreate, PolicyCreate, AcknowledgmentCreate,
    TrainingCreate, CompletionCreate, DocumentCreate, AuditCreate, FindingCreate, RiskCreate, RiskUpdate,
    IncidentCreate, ReportCreate,
    ComplianceMetrics
)


class ComplianceService:
    """Service de gestion de la conformité."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # =========================================================================
    # RÉGLEMENTATIONS
    # =========================================================================

    def create_regulation(self, data: RegulationCreate, user_id: UUID) -> Regulation:
        """Créer une réglementation."""
        regulation = Regulation(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data.model_dump()
        )
        self.db.add(regulation)
        self.db.commit()
        self.db.refresh(regulation)
        return regulation

    def get_regulation(self, regulation_id: UUID) -> Optional[Regulation]:
        """Récupérer une réglementation."""
        return self.db.query(Regulation).filter(
            Regulation.id == regulation_id,
            Regulation.tenant_id == self.tenant_id
        ).first()

    def get_regulations(
        self,
        regulation_type: Optional[RegulationType] = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Regulation]:
        """Récupérer les réglementations."""
        query = self.db.query(Regulation).filter(
            Regulation.tenant_id == self.tenant_id,
            Regulation.is_active == is_active
        )

        if regulation_type:
            query = query.filter(Regulation.type == regulation_type)

        return query.order_by(Regulation.code).offset(skip).limit(limit).all()

    def update_regulation(
        self,
        regulation_id: UUID,
        data: RegulationUpdate,
        user_id: UUID
    ) -> Optional[Regulation]:
        """Mettre à jour une réglementation."""
        regulation = self.get_regulation(regulation_id)
        if not regulation:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(regulation, field, value)

        regulation.updated_by = user_id
        self.db.commit()
        self.db.refresh(regulation)
        return regulation

    # =========================================================================
    # EXIGENCES
    # =========================================================================

    def create_requirement(self, data: RequirementCreate, user_id: UUID) -> Requirement:
        """Créer une exigence."""
        requirement = Requirement(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data.model_dump()
        )
        self.db.add(requirement)
        self.db.commit()
        self.db.refresh(requirement)
        return requirement

    def get_requirement(self, requirement_id: UUID) -> Optional[Requirement]:
        """Récupérer une exigence."""
        return self.db.query(Requirement).filter(
            Requirement.id == requirement_id,
            Requirement.tenant_id == self.tenant_id
        ).first()

    def get_requirements(
        self,
        regulation_id: Optional[UUID] = None,
        compliance_status: Optional[ComplianceStatus] = None,
        priority: Optional[RequirementPriority] = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Requirement]:
        """Récupérer les exigences."""
        query = self.db.query(Requirement).filter(
            Requirement.tenant_id == self.tenant_id,
            Requirement.is_active == is_active
        )

        if regulation_id:
            query = query.filter(Requirement.regulation_id == regulation_id)
        if compliance_status:
            query = query.filter(Requirement.compliance_status == compliance_status)
        if priority:
            query = query.filter(Requirement.priority == priority)

        return query.order_by(Requirement.code).offset(skip).limit(limit).all()

    def update_requirement(
        self,
        requirement_id: UUID,
        data: RequirementUpdate,
        user_id: UUID
    ) -> Optional[Requirement]:
        """Mettre à jour une exigence."""
        requirement = self.get_requirement(requirement_id)
        if not requirement:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(requirement, field, value)

        requirement.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(requirement)
        return requirement

    def assess_requirement(
        self,
        requirement_id: UUID,
        status: ComplianceStatus,
        score: Optional[Decimal] = None,
        user_id: Optional[UUID] = None
    ) -> Optional[Requirement]:
        """Évaluer la conformité d'une exigence."""
        requirement = self.get_requirement(requirement_id)
        if not requirement:
            return None

        requirement.compliance_status = status
        if score is not None:
            requirement.current_score = score
        requirement.last_assessed = datetime.utcnow()

        self.db.commit()
        self.db.refresh(requirement)
        return requirement

    # =========================================================================
    # ÉVALUATIONS
    # =========================================================================

    def create_assessment(self, data: AssessmentCreate, user_id: UUID) -> ComplianceAssessment:
        """Créer une évaluation de conformité."""
        # Générer le numéro
        year = datetime.utcnow().year
        count = self.db.query(ComplianceAssessment).filter(
            ComplianceAssessment.tenant_id == self.tenant_id,
            func.extract('year', ComplianceAssessment.created_at) == year
        ).count()

        assessment = ComplianceAssessment(
            tenant_id=self.tenant_id,
            number=f"ASS-{year}-{count + 1:04d}",
            created_by=user_id,
            **data.model_dump()
        )
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment

    def get_assessment(self, assessment_id: UUID) -> Optional[ComplianceAssessment]:
        """Récupérer une évaluation."""
        return self.db.query(ComplianceAssessment).filter(
            ComplianceAssessment.id == assessment_id,
            ComplianceAssessment.tenant_id == self.tenant_id
        ).first()

    def start_assessment(self, assessment_id: UUID) -> Optional[ComplianceAssessment]:
        """Démarrer une évaluation."""
        assessment = self.get_assessment(assessment_id)
        if not assessment or assessment.status != AssessmentStatus.DRAFT:
            return None

        assessment.status = AssessmentStatus.IN_PROGRESS
        assessment.start_date = date.today()

        self.db.commit()
        self.db.refresh(assessment)
        return assessment

    def complete_assessment(
        self,
        assessment_id: UUID,
        findings_summary: Optional[str] = None,
        recommendations: Optional[str] = None
    ) -> Optional[ComplianceAssessment]:
        """Terminer une évaluation."""
        assessment = self.get_assessment(assessment_id)
        if not assessment or assessment.status != AssessmentStatus.IN_PROGRESS:
            return None

        # Calculer les résultats
        gaps = self.db.query(ComplianceGap).filter(
            ComplianceGap.assessment_id == assessment_id
        ).all()

        compliant_count = 0
        non_compliant_count = 0
        partial_count = 0

        for gap in gaps:
            if gap.current_status == ComplianceStatus.COMPLIANT:
                compliant_count += 1
            elif gap.current_status == ComplianceStatus.NON_COMPLIANT:
                non_compliant_count += 1
            elif gap.current_status == ComplianceStatus.PARTIAL:
                partial_count += 1

        total = compliant_count + non_compliant_count + partial_count
        if total > 0:
            assessment.overall_score = Decimal(compliant_count / total * 100)
        else:
            assessment.overall_score = Decimal("100")

        assessment.total_requirements = total
        assessment.compliant_count = compliant_count
        assessment.non_compliant_count = non_compliant_count
        assessment.partial_count = partial_count

        if non_compliant_count > 0:
            assessment.overall_status = ComplianceStatus.NON_COMPLIANT
        elif partial_count > 0:
            assessment.overall_status = ComplianceStatus.PARTIAL
        else:
            assessment.overall_status = ComplianceStatus.COMPLIANT

        assessment.status = AssessmentStatus.COMPLETED
        assessment.end_date = date.today()
        assessment.findings_summary = findings_summary
        assessment.recommendations = recommendations

        self.db.commit()
        self.db.refresh(assessment)
        return assessment

    def approve_assessment(
        self,
        assessment_id: UUID,
        user_id: UUID
    ) -> Optional[ComplianceAssessment]:
        """Approuver une évaluation."""
        assessment = self.get_assessment(assessment_id)
        if not assessment or assessment.status != AssessmentStatus.COMPLETED:
            return None

        assessment.status = AssessmentStatus.APPROVED
        assessment.approved_by = user_id
        assessment.approved_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(assessment)
        return assessment

    # =========================================================================
    # ÉCARTS
    # =========================================================================

    def create_gap(self, data: GapCreate, user_id: UUID) -> ComplianceGap:
        """Créer un écart de conformité."""
        gap = ComplianceGap(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data.model_dump()
        )

        # Calculer le score de risque
        severity_scores = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }
        gap.risk_score = Decimal(severity_scores.get(gap.severity, 2) * 25)

        self.db.add(gap)
        self.db.commit()
        self.db.refresh(gap)
        return gap

    def close_gap(
        self,
        gap_id: UUID,
        resolution_notes: Optional[str] = None
    ) -> Optional[ComplianceGap]:
        """Clôturer un écart."""
        gap = self.db.query(ComplianceGap).filter(
            ComplianceGap.id == gap_id,
            ComplianceGap.tenant_id == self.tenant_id
        ).first()

        if not gap or not gap.is_open:
            return None

        gap.is_open = False
        gap.actual_closure_date = date.today()
        gap.current_status = ComplianceStatus.COMPLIANT

        self.db.commit()
        self.db.refresh(gap)
        return gap

    # =========================================================================
    # ACTIONS
    # =========================================================================

    def create_action(self, data: ActionCreate, user_id: UUID) -> ComplianceAction:
        """Créer une action corrective."""
        # Générer le numéro
        year = datetime.utcnow().year
        count = self.db.query(ComplianceAction).filter(
            ComplianceAction.tenant_id == self.tenant_id,
            func.extract('year', ComplianceAction.created_at) == year
        ).count()

        action = ComplianceAction(
            tenant_id=self.tenant_id,
            number=f"ACT-{year}-{count + 1:04d}",
            created_by=user_id,
            **data.model_dump()
        )
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action

    def get_action(self, action_id: UUID) -> Optional[ComplianceAction]:
        """Récupérer une action."""
        return self.db.query(ComplianceAction).filter(
            ComplianceAction.id == action_id,
            ComplianceAction.tenant_id == self.tenant_id
        ).first()

    def start_action(self, action_id: UUID) -> Optional[ComplianceAction]:
        """Démarrer une action."""
        action = self.get_action(action_id)
        if not action or action.status != ActionStatus.OPEN:
            return None

        action.status = ActionStatus.IN_PROGRESS
        action.start_date = date.today()

        self.db.commit()
        self.db.refresh(action)
        return action

    def complete_action(
        self,
        action_id: UUID,
        resolution_notes: str,
        evidence: Optional[List[str]] = None,
        actual_cost: Optional[Decimal] = None
    ) -> Optional[ComplianceAction]:
        """Terminer une action."""
        action = self.get_action(action_id)
        if not action or action.status != ActionStatus.IN_PROGRESS:
            return None

        action.status = ActionStatus.COMPLETED
        action.completion_date = date.today()
        action.progress_percent = 100
        action.resolution_notes = resolution_notes
        if evidence:
            action.evidence_provided = evidence
        if actual_cost is not None:
            action.actual_cost = actual_cost

        self.db.commit()
        self.db.refresh(action)
        return action

    def verify_action(
        self,
        action_id: UUID,
        user_id: UUID,
        verification_notes: Optional[str] = None
    ) -> Optional[ComplianceAction]:
        """Vérifier une action."""
        action = self.get_action(action_id)
        if not action or action.status != ActionStatus.COMPLETED:
            return None

        action.status = ActionStatus.VERIFIED
        action.verified_by = user_id
        action.verified_at = datetime.utcnow()
        action.verification_notes = verification_notes

        # Fermer l'écart associé si applicable
        if action.gap_id:
            self.close_gap(action.gap_id)

        self.db.commit()
        self.db.refresh(action)
        return action

    def get_overdue_actions(self) -> List[ComplianceAction]:
        """Récupérer les actions en retard."""
        return self.db.query(ComplianceAction).filter(
            ComplianceAction.tenant_id == self.tenant_id,
            ComplianceAction.status.in_([ActionStatus.OPEN, ActionStatus.IN_PROGRESS]),
            ComplianceAction.due_date < date.today()
        ).all()

    # =========================================================================
    # POLITIQUES
    # =========================================================================

    def create_policy(self, data: PolicyCreate, user_id: UUID) -> Policy:
        """Créer une politique."""
        policy = Policy(
            tenant_id=self.tenant_id,
            version_date=date.today(),
            created_by=user_id,
            **data.model_dump()
        )
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def get_policy(self, policy_id: UUID) -> Optional[Policy]:
        """Récupérer une politique."""
        return self.db.query(Policy).filter(
            Policy.id == policy_id,
            Policy.tenant_id == self.tenant_id
        ).first()

    def publish_policy(self, policy_id: UUID, user_id: UUID) -> Optional[Policy]:
        """Publier une politique."""
        policy = self.get_policy(policy_id)
        if not policy:
            return None

        policy.is_published = True
        policy.approved_by = user_id
        policy.approved_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(policy)
        return policy

    def acknowledge_policy(
        self,
        data: AcknowledgmentCreate,
        user_id: UUID,
        ip_address: Optional[str] = None
    ) -> PolicyAcknowledgment:
        """Accuser réception d'une politique."""
        acknowledgment = PolicyAcknowledgment(
            tenant_id=self.tenant_id,
            policy_id=data.policy_id,
            user_id=user_id,
            ip_address=ip_address,
            notes=data.notes
        )
        self.db.add(acknowledgment)
        self.db.commit()
        self.db.refresh(acknowledgment)
        return acknowledgment

    def get_user_acknowledgments(self, user_id: UUID) -> List[PolicyAcknowledgment]:
        """Récupérer les accusés de réception d'un utilisateur."""
        return self.db.query(PolicyAcknowledgment).filter(
            PolicyAcknowledgment.tenant_id == self.tenant_id,
            PolicyAcknowledgment.user_id == user_id,
            PolicyAcknowledgment.is_valid == True
        ).all()

    # =========================================================================
    # FORMATIONS
    # =========================================================================

    def create_training(self, data: TrainingCreate, user_id: UUID) -> ComplianceTraining:
        """Créer une formation."""
        training = ComplianceTraining(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data.model_dump()
        )
        self.db.add(training)
        self.db.commit()
        self.db.refresh(training)
        return training

    def get_training(self, training_id: UUID) -> Optional[ComplianceTraining]:
        """Récupérer une formation."""
        return self.db.query(ComplianceTraining).filter(
            ComplianceTraining.id == training_id,
            ComplianceTraining.tenant_id == self.tenant_id
        ).first()

    def assign_training(
        self,
        data: CompletionCreate,
        assigner_id: UUID
    ) -> TrainingCompletion:
        """Assigner une formation à un utilisateur."""
        completion = TrainingCompletion(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(completion)
        self.db.commit()
        self.db.refresh(completion)
        return completion

    def start_training(
        self,
        completion_id: UUID
    ) -> Optional[TrainingCompletion]:
        """Démarrer une formation."""
        completion = self.db.query(TrainingCompletion).filter(
            TrainingCompletion.id == completion_id,
            TrainingCompletion.tenant_id == self.tenant_id
        ).first()

        if not completion or completion.started_at:
            return None

        completion.started_at = datetime.utcnow()
        completion.attempts += 1

        self.db.commit()
        self.db.refresh(completion)
        return completion

    def complete_training(
        self,
        completion_id: UUID,
        score: int,
        certificate_number: Optional[str] = None
    ) -> Optional[TrainingCompletion]:
        """Terminer une formation."""
        completion = self.db.query(TrainingCompletion).filter(
            TrainingCompletion.id == completion_id,
            TrainingCompletion.tenant_id == self.tenant_id
        ).first()

        if not completion:
            return None

        training = self.get_training(completion.training_id)
        passed = True
        if training and training.passing_score:
            passed = score >= training.passing_score

        completion.completed_at = datetime.utcnow()
        completion.score = score
        completion.passed = passed
        completion.certificate_number = certificate_number

        # Calculer la date d'expiration si récurrent
        if training and training.recurrence_months and passed:
            completion.expiry_date = date.today() + timedelta(days=training.recurrence_months * 30)

        self.db.commit()
        self.db.refresh(completion)
        return completion

    def get_user_training_status(self, user_id: UUID) -> List[TrainingCompletion]:
        """Récupérer le statut de formation d'un utilisateur."""
        return self.db.query(TrainingCompletion).filter(
            TrainingCompletion.tenant_id == self.tenant_id,
            TrainingCompletion.user_id == user_id,
            TrainingCompletion.is_current == True
        ).all()

    # =========================================================================
    # DOCUMENTS
    # =========================================================================

    def create_document(self, data: DocumentCreate, user_id: UUID) -> ComplianceDocument:
        """Créer un document."""
        document = ComplianceDocument(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data.model_dump()
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def get_document(self, document_id: UUID) -> Optional[ComplianceDocument]:
        """Récupérer un document."""
        return self.db.query(ComplianceDocument).filter(
            ComplianceDocument.id == document_id,
            ComplianceDocument.tenant_id == self.tenant_id
        ).first()

    def approve_document(
        self,
        document_id: UUID,
        user_id: UUID
    ) -> Optional[ComplianceDocument]:
        """Approuver un document."""
        document = self.get_document(document_id)
        if not document:
            return None

        document.approved_by = user_id
        document.approved_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(document)
        return document

    # =========================================================================
    # AUDITS
    # =========================================================================

    def create_audit(self, data: AuditCreate, user_id: UUID) -> ComplianceAudit:
        """Créer un audit."""
        # Générer le numéro
        year = datetime.utcnow().year
        count = self.db.query(ComplianceAudit).filter(
            ComplianceAudit.tenant_id == self.tenant_id,
            func.extract('year', ComplianceAudit.created_at) == year
        ).count()

        audit = ComplianceAudit(
            tenant_id=self.tenant_id,
            number=f"AUD-{year}-{count + 1:04d}",
            created_by=user_id,
            **data.model_dump()
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        return audit

    def get_audit(self, audit_id: UUID) -> Optional[ComplianceAudit]:
        """Récupérer un audit."""
        return self.db.query(ComplianceAudit).filter(
            ComplianceAudit.id == audit_id,
            ComplianceAudit.tenant_id == self.tenant_id
        ).first()

    def start_audit(self, audit_id: UUID) -> Optional[ComplianceAudit]:
        """Démarrer un audit."""
        audit = self.get_audit(audit_id)
        if not audit or audit.status != AuditStatus.PLANNED:
            return None

        audit.status = AuditStatus.IN_PROGRESS
        audit.actual_start = date.today()

        self.db.commit()
        self.db.refresh(audit)
        return audit

    def complete_audit(
        self,
        audit_id: UUID,
        executive_summary: Optional[str] = None,
        conclusions: Optional[str] = None,
        recommendations: Optional[str] = None
    ) -> Optional[ComplianceAudit]:
        """Terminer un audit."""
        audit = self.get_audit(audit_id)
        if not audit or audit.status != AuditStatus.IN_PROGRESS:
            return None

        # Comptabiliser les constatations
        findings = self.db.query(AuditFinding).filter(
            AuditFinding.audit_id == audit_id
        ).all()

        audit.total_findings = len(findings)
        audit.critical_findings = sum(1 for f in findings if f.severity == FindingSeverity.CRITICAL)
        audit.major_findings = sum(1 for f in findings if f.severity == FindingSeverity.MAJOR)
        audit.minor_findings = sum(1 for f in findings if f.severity == FindingSeverity.MINOR)
        audit.observations = sum(1 for f in findings if f.severity == FindingSeverity.OBSERVATION)

        audit.status = AuditStatus.COMPLETED
        audit.actual_end = date.today()
        audit.executive_summary = executive_summary
        audit.conclusions = conclusions
        audit.recommendations = recommendations

        self.db.commit()
        self.db.refresh(audit)
        return audit

    def close_audit(self, audit_id: UUID, user_id: UUID) -> Optional[ComplianceAudit]:
        """Clôturer un audit."""
        audit = self.get_audit(audit_id)
        if not audit or audit.status != AuditStatus.COMPLETED:
            return None

        audit.status = AuditStatus.CLOSED
        audit.approved_by = user_id
        audit.approved_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(audit)
        return audit

    # =========================================================================
    # CONSTATATIONS
    # =========================================================================

    def create_finding(self, data: FindingCreate, user_id: UUID) -> AuditFinding:
        """Créer une constatation d'audit."""
        # Générer le numéro
        audit = self.get_audit(data.audit_id)
        count = self.db.query(AuditFinding).filter(
            AuditFinding.audit_id == data.audit_id
        ).count()

        finding = AuditFinding(
            tenant_id=self.tenant_id,
            number=f"{audit.number}-F{count + 1:02d}" if audit else f"F-{count + 1:04d}",
            created_by=user_id,
            **data.model_dump()
        )
        self.db.add(finding)
        self.db.commit()
        self.db.refresh(finding)
        return finding

    def respond_to_finding(
        self,
        finding_id: UUID,
        response: str
    ) -> Optional[AuditFinding]:
        """Répondre à une constatation."""
        finding = self.db.query(AuditFinding).filter(
            AuditFinding.id == finding_id,
            AuditFinding.tenant_id == self.tenant_id
        ).first()

        if not finding:
            return None

        finding.response = response
        finding.response_date = date.today()

        self.db.commit()
        self.db.refresh(finding)
        return finding

    def close_finding(self, finding_id: UUID) -> Optional[AuditFinding]:
        """Clôturer une constatation."""
        finding = self.db.query(AuditFinding).filter(
            AuditFinding.id == finding_id,
            AuditFinding.tenant_id == self.tenant_id
        ).first()

        if not finding:
            return None

        finding.is_closed = True
        finding.closure_date = date.today()

        self.db.commit()
        self.db.refresh(finding)
        return finding

    # =========================================================================
    # RISQUES
    # =========================================================================

    def create_risk(self, data: RiskCreate, user_id: UUID) -> ComplianceRisk:
        """Créer un risque."""
        risk = ComplianceRisk(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data.model_dump()
        )

        # Calculer le score et le niveau
        risk.risk_score = risk.likelihood * risk.impact
        risk.risk_level = self._calculate_risk_level(risk.risk_score)

        self.db.add(risk)
        self.db.commit()
        self.db.refresh(risk)
        return risk

    def _calculate_risk_level(self, score: int) -> RiskLevel:
        """Calculer le niveau de risque."""
        if score >= 16:
            return RiskLevel.CRITICAL
        elif score >= 9:
            return RiskLevel.HIGH
        elif score >= 4:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def get_risk(self, risk_id: UUID) -> Optional[ComplianceRisk]:
        """Récupérer un risque."""
        return self.db.query(ComplianceRisk).filter(
            ComplianceRisk.id == risk_id,
            ComplianceRisk.tenant_id == self.tenant_id
        ).first()

    def update_risk(
        self,
        risk_id: UUID,
        data: RiskUpdate,
        user_id: UUID
    ) -> Optional[ComplianceRisk]:
        """Mettre à jour un risque."""
        risk = self.get_risk(risk_id)
        if not risk:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(risk, field, value)

        # Recalculer le score et le niveau
        if risk.likelihood and risk.impact:
            risk.risk_score = risk.likelihood * risk.impact
            risk.risk_level = self._calculate_risk_level(risk.risk_score)

        if risk.residual_likelihood and risk.residual_impact:
            risk.residual_score = risk.residual_likelihood * risk.residual_impact
            risk.residual_level = self._calculate_risk_level(risk.residual_score)

        risk.last_review_date = date.today()
        self.db.commit()
        self.db.refresh(risk)
        return risk

    def accept_risk(
        self,
        risk_id: UUID,
        user_id: UUID
    ) -> Optional[ComplianceRisk]:
        """Accepter un risque."""
        risk = self.get_risk(risk_id)
        if not risk:
            return None

        risk.is_accepted = True
        risk.last_review_date = date.today()

        self.db.commit()
        self.db.refresh(risk)
        return risk

    # =========================================================================
    # INCIDENTS
    # =========================================================================

    def create_incident(self, data: IncidentCreate, user_id: UUID) -> ComplianceIncident:
        """Créer un incident."""
        # Générer le numéro
        year = datetime.utcnow().year
        count = self.db.query(ComplianceIncident).filter(
            ComplianceIncident.tenant_id == self.tenant_id,
            func.extract('year', ComplianceIncident.created_at) == year
        ).count()

        incident = ComplianceIncident(
            tenant_id=self.tenant_id,
            number=f"INC-{year}-{count + 1:04d}",
            reporter_id=user_id,
            **data.model_dump()
        )
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def get_incident(self, incident_id: UUID) -> Optional[ComplianceIncident]:
        """Récupérer un incident."""
        return self.db.query(ComplianceIncident).filter(
            ComplianceIncident.id == incident_id,
            ComplianceIncident.tenant_id == self.tenant_id
        ).first()

    def assign_incident(
        self,
        incident_id: UUID,
        assignee_id: UUID
    ) -> Optional[ComplianceIncident]:
        """Assigner un incident."""
        incident = self.get_incident(incident_id)
        if not incident:
            return None

        incident.assigned_to = assignee_id
        incident.status = IncidentStatus.INVESTIGATING

        self.db.commit()
        self.db.refresh(incident)
        return incident

    def resolve_incident(
        self,
        incident_id: UUID,
        resolution: str,
        root_cause: Optional[str] = None,
        lessons_learned: Optional[str] = None
    ) -> Optional[ComplianceIncident]:
        """Résoudre un incident."""
        incident = self.get_incident(incident_id)
        if not incident:
            return None

        incident.status = IncidentStatus.RESOLVED
        incident.resolved_date = datetime.utcnow()
        incident.resolution = resolution
        incident.root_cause = root_cause
        incident.lessons_learned = lessons_learned

        self.db.commit()
        self.db.refresh(incident)
        return incident

    def close_incident(self, incident_id: UUID) -> Optional[ComplianceIncident]:
        """Clôturer un incident."""
        incident = self.get_incident(incident_id)
        if not incident or incident.status != IncidentStatus.RESOLVED:
            return None

        incident.status = IncidentStatus.CLOSED
        incident.closed_date = datetime.utcnow()

        self.db.commit()
        self.db.refresh(incident)
        return incident

    # =========================================================================
    # RAPPORTS
    # =========================================================================

    def create_report(self, data: ReportCreate, user_id: UUID) -> ComplianceReport:
        """Créer un rapport."""
        # Générer le numéro
        year = datetime.utcnow().year
        count = self.db.query(ComplianceReport).filter(
            ComplianceReport.tenant_id == self.tenant_id,
            func.extract('year', ComplianceReport.created_at) == year
        ).count()

        report = ComplianceReport(
            tenant_id=self.tenant_id,
            number=f"RPT-{year}-{count + 1:04d}",
            created_by=user_id,
            **data.model_dump()
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def publish_report(
        self,
        report_id: UUID,
        user_id: UUID
    ) -> Optional[ComplianceReport]:
        """Publier un rapport."""
        report = self.db.query(ComplianceReport).filter(
            ComplianceReport.id == report_id,
            ComplianceReport.tenant_id == self.tenant_id
        ).first()

        if not report:
            return None

        report.is_published = True
        report.published_at = datetime.utcnow()
        report.approved_by = user_id
        report.approved_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(report)
        return report

    # =========================================================================
    # DASHBOARD & MÉTRIQUES
    # =========================================================================

    def get_compliance_metrics(self) -> ComplianceMetrics:
        """Calculer les métriques de conformité."""
        # Exigences
        requirements = self.db.query(Requirement).filter(
            Requirement.tenant_id == self.tenant_id,
            Requirement.is_active == True
        ).all()

        total_requirements = len(requirements)
        compliant = sum(1 for r in requirements if r.compliance_status == ComplianceStatus.COMPLIANT)
        non_compliant = sum(1 for r in requirements if r.compliance_status == ComplianceStatus.NON_COMPLIANT)
        partial = sum(1 for r in requirements if r.compliance_status == ComplianceStatus.PARTIAL)
        pending = sum(1 for r in requirements if r.compliance_status == ComplianceStatus.PENDING)

        compliance_rate = Decimal(compliant / total_requirements * 100) if total_requirements > 0 else Decimal("0")

        # Écarts et actions
        open_gaps = self.db.query(ComplianceGap).filter(
            ComplianceGap.tenant_id == self.tenant_id,
            ComplianceGap.is_open == True
        ).count()

        open_actions = self.db.query(ComplianceAction).filter(
            ComplianceAction.tenant_id == self.tenant_id,
            ComplianceAction.status.in_([ActionStatus.OPEN, ActionStatus.IN_PROGRESS])
        ).count()

        overdue_actions = self.db.query(ComplianceAction).filter(
            ComplianceAction.tenant_id == self.tenant_id,
            ComplianceAction.status.in_([ActionStatus.OPEN, ActionStatus.IN_PROGRESS]),
            ComplianceAction.due_date < date.today()
        ).count()

        # Audits
        active_audits = self.db.query(ComplianceAudit).filter(
            ComplianceAudit.tenant_id == self.tenant_id,
            ComplianceAudit.status == AuditStatus.IN_PROGRESS
        ).count()

        open_findings = self.db.query(AuditFinding).filter(
            AuditFinding.tenant_id == self.tenant_id,
            AuditFinding.is_closed == False
        ).count()

        critical_findings = self.db.query(AuditFinding).filter(
            AuditFinding.tenant_id == self.tenant_id,
            AuditFinding.is_closed == False,
            AuditFinding.severity == FindingSeverity.CRITICAL
        ).count()

        # Risques
        active_risks = self.db.query(ComplianceRisk).filter(
            ComplianceRisk.tenant_id == self.tenant_id,
            ComplianceRisk.is_active == True
        ).count()

        high_risks = self.db.query(ComplianceRisk).filter(
            ComplianceRisk.tenant_id == self.tenant_id,
            ComplianceRisk.is_active == True,
            ComplianceRisk.risk_level == RiskLevel.HIGH
        ).count()

        critical_risks = self.db.query(ComplianceRisk).filter(
            ComplianceRisk.tenant_id == self.tenant_id,
            ComplianceRisk.is_active == True,
            ComplianceRisk.risk_level == RiskLevel.CRITICAL
        ).count()

        # Incidents
        open_incidents = self.db.query(ComplianceIncident).filter(
            ComplianceIncident.tenant_id == self.tenant_id,
            ComplianceIncident.status.in_([IncidentStatus.REPORTED, IncidentStatus.INVESTIGATING])
        ).count()

        # Formations
        training_compliance_rate = Decimal("95")  # Placeholder

        # Politiques
        policies_requiring_ack = self.db.query(Policy).filter(
            Policy.tenant_id == self.tenant_id,
            Policy.is_active == True,
            Policy.is_published == True,
            Policy.requires_acknowledgment == True
        ).count()

        return ComplianceMetrics(
            overall_compliance_rate=compliance_rate,
            compliant_requirements=compliant,
            non_compliant_requirements=non_compliant,
            partial_requirements=partial,
            pending_requirements=pending,
            total_requirements=total_requirements,
            open_gaps=open_gaps,
            open_actions=open_actions,
            overdue_actions=overdue_actions,
            active_audits=active_audits,
            open_findings=open_findings,
            critical_findings=critical_findings,
            active_risks=active_risks,
            high_risks=high_risks,
            critical_risks=critical_risks,
            open_incidents=open_incidents,
            training_compliance_rate=training_compliance_rate,
            policies_requiring_acknowledgment=policies_requiring_ack
        )


def get_compliance_service(db: Session, tenant_id: str) -> ComplianceService:
    """Factory pour obtenir une instance du service."""
    return ComplianceService(db, tenant_id)
