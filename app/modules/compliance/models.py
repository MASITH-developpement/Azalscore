"""
AZALS MODULE M11 - Modèles Conformité
=====================================

Modèles SQLAlchemy pour la gestion de la conformité réglementaire.
"""

import enum
from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.types import UniversalUUID
from app.db import Base

# =============================================================================
# ENUMS
# =============================================================================

class ComplianceStatus(str, enum.Enum):
    """Statut de conformité."""
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PARTIAL = "PARTIAL"
    PENDING = "PENDING"
    EXPIRED = "EXPIRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RegulationType(str, enum.Enum):
    """Type de réglementation."""
    ISO = "ISO"
    GDPR = "GDPR"
    SOX = "SOX"
    FDA = "FDA"
    CUSTOMS = "CUSTOMS"
    TAX = "TAX"
    LABOR = "LABOR"
    ENVIRONMENTAL = "ENVIRONMENTAL"
    SAFETY = "SAFETY"
    QUALITY = "QUALITY"
    INDUSTRY_SPECIFIC = "INDUSTRY_SPECIFIC"
    INTERNAL = "INTERNAL"


class RequirementPriority(str, enum.Enum):
    """Priorité d'exigence."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AssessmentStatus(str, enum.Enum):
    """Statut d'évaluation."""
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class RiskLevel(str, enum.Enum):
    """Niveau de risque."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ActionStatus(str, enum.Enum):
    """Statut d'action."""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    VERIFIED = "VERIFIED"
    CANCELLED = "CANCELLED"
    OVERDUE = "OVERDUE"


class DocumentType(str, enum.Enum):
    """Type de document."""
    POLICY = "POLICY"
    PROCEDURE = "PROCEDURE"
    WORK_INSTRUCTION = "WORK_INSTRUCTION"
    FORM = "FORM"
    RECORD = "RECORD"
    CERTIFICATE = "CERTIFICATE"
    LICENSE = "LICENSE"
    PERMIT = "PERMIT"
    REPORT = "REPORT"


class AuditStatus(str, enum.Enum):
    """Statut d'audit."""
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class FindingSeverity(str, enum.Enum):
    """Sévérité de constatation."""
    OBSERVATION = "OBSERVATION"
    MINOR = "MINOR"
    MAJOR = "MAJOR"
    CRITICAL = "CRITICAL"


class IncidentSeverity(str, enum.Enum):
    """Sévérité d'incident."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, enum.Enum):
    """Statut d'incident."""
    REPORTED = "REPORTED"
    INVESTIGATING = "INVESTIGATING"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class ReportType(str, enum.Enum):
    """Type de rapport."""
    COMPLIANCE_STATUS = "COMPLIANCE_STATUS"
    GAP_ANALYSIS = "GAP_ANALYSIS"
    RISK_ASSESSMENT = "RISK_ASSESSMENT"
    AUDIT_SUMMARY = "AUDIT_SUMMARY"
    INCIDENT_REPORT = "INCIDENT_REPORT"
    TRAINING_STATUS = "TRAINING_STATUS"
    REGULATORY_FILING = "REGULATORY_FILING"


# =============================================================================
# MODÈLES - RÉGLEMENTATIONS
# =============================================================================

class Regulation(Base):
    """Réglementation applicable."""
    __tablename__ = "compliance_regulations"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(Enum(RegulationType), nullable=False, default=RegulationType.INTERNAL)
    version = Column(String(50))

    # Description
    description = Column(Text)
    scope = Column(Text)
    authority = Column(String(200))  # Autorité émettrice

    # Dates
    effective_date = Column(Date)
    expiry_date = Column(Date)
    next_review_date = Column(Date)

    # Statut
    is_active = Column(Boolean, default=True)
    is_mandatory = Column(Boolean, default=True)

    # Métadonnées
    external_reference = Column(String(200))
    source_url = Column(Text)
    notes = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())
    updated_by = Column(UniversalUUID())

    # Relations
    requirements = relationship("Requirement", back_populates="regulation", lazy="dynamic")
    assessments = relationship("ComplianceAssessment", back_populates="regulation", lazy="dynamic")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_regulation_tenant_code'),
        Index('ix_regulation_tenant_type', 'tenant_id', 'type'),
    )


class Requirement(Base):
    """Exigence de conformité."""
    __tablename__ = "compliance_requirements"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Lien réglementation
    regulation_id = Column(UniversalUUID(), ForeignKey("compliance_regulations.id"), nullable=False)
    parent_id = Column(UniversalUUID(), ForeignKey("compliance_requirements.id"))

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Classement
    priority = Column(Enum(RequirementPriority), default=RequirementPriority.MEDIUM)
    category = Column(String(100))
    clause_reference = Column(String(100))  # Référence article/clause

    # Conformité
    compliance_status = Column(Enum(ComplianceStatus), default=ComplianceStatus.PENDING)
    current_score = Column(Numeric(5, 2))  # Score 0-100
    target_score = Column(Numeric(5, 2), default=100)

    # Responsabilité
    responsible_id = Column(UniversalUUID())  # Responsable conformité
    department = Column(String(100))

    # Contrôle
    control_frequency = Column(String(50))  # Daily, Weekly, Monthly, Quarterly, Annual
    last_assessed = Column(DateTime)
    next_assessment = Column(Date)

    # Preuves requises
    evidence_required = Column(JSON)  # Liste des types de preuves

    # Statut
    is_active = Column(Boolean, default=True)
    is_key_control = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())

    # Relations
    regulation = relationship("Regulation", back_populates="requirements")
    parent = relationship("Requirement", remote_side=[id], backref="children")
    gaps = relationship("ComplianceGap", back_populates="requirement", lazy="dynamic")
    actions = relationship("ComplianceAction", back_populates="requirement", lazy="dynamic")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'regulation_id', 'code', name='uq_requirement_code'),
        Index('ix_requirement_tenant_status', 'tenant_id', 'compliance_status'),
    )


# =============================================================================
# MODÈLES - ÉVALUATIONS
# =============================================================================

class ComplianceAssessment(Base):
    """Évaluation de conformité."""
    __tablename__ = "compliance_assessments"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    number = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Scope
    regulation_id = Column(UniversalUUID(), ForeignKey("compliance_regulations.id"))
    assessment_type = Column(String(50))  # Full, Partial, Gap Analysis
    scope_description = Column(Text)

    # Dates
    planned_date = Column(Date)
    start_date = Column(Date)
    end_date = Column(Date)

    # Statut
    status = Column(Enum(AssessmentStatus), default=AssessmentStatus.DRAFT)

    # Résultats
    overall_score = Column(Numeric(5, 2))
    overall_status = Column(Enum(ComplianceStatus))
    total_requirements = Column(Integer, default=0)
    compliant_count = Column(Integer, default=0)
    non_compliant_count = Column(Integer, default=0)
    partial_count = Column(Integer, default=0)

    # Conclusions
    findings_summary = Column(Text)
    recommendations = Column(Text)

    # Équipe
    lead_assessor_id = Column(UniversalUUID())
    assessor_ids = Column(JSON)  # Liste des évaluateurs

    # Approbation
    approved_by = Column(UniversalUUID())
    approved_at = Column(DateTime)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())

    # Relations
    regulation = relationship("Regulation", back_populates="assessments")
    gaps = relationship("ComplianceGap", back_populates="assessment", lazy="dynamic")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'number', name='uq_assessment_number'),
        Index('ix_assessment_tenant_status', 'tenant_id', 'status'),
    )


class ComplianceGap(Base):
    """Écart de conformité identifié."""
    __tablename__ = "compliance_gaps"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Liens
    assessment_id = Column(UniversalUUID(), ForeignKey("compliance_assessments.id"), nullable=False)
    requirement_id = Column(UniversalUUID(), ForeignKey("compliance_requirements.id"), nullable=False)

    # Description
    gap_description = Column(Text, nullable=False)
    root_cause = Column(Text)
    impact_description = Column(Text)

    # Évaluation
    severity = Column(Enum(RiskLevel), default=RiskLevel.MEDIUM)
    risk_score = Column(Numeric(5, 2))
    current_status = Column(Enum(ComplianceStatus), default=ComplianceStatus.NON_COMPLIANT)

    # Preuves
    evidence_reviewed = Column(JSON)
    evidence_gaps = Column(Text)

    # Dates
    identified_date = Column(Date, default=date.today)
    target_closure_date = Column(Date)
    actual_closure_date = Column(Date)

    # Statut
    is_open = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())

    # Relations
    assessment = relationship("ComplianceAssessment", back_populates="gaps")
    requirement = relationship("Requirement", back_populates="gaps")
    actions = relationship("ComplianceAction", back_populates="gap", lazy="dynamic")

    __table_args__ = (
        Index('ix_gap_tenant_open', 'tenant_id', 'is_open'),
    )


class ComplianceAction(Base):
    """Action corrective de conformité."""
    __tablename__ = "compliance_actions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Liens
    gap_id = Column(UniversalUUID(), ForeignKey("compliance_gaps.id"))
    requirement_id = Column(UniversalUUID(), ForeignKey("compliance_requirements.id"))

    # Identification
    number = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    action_type = Column(String(50))  # Corrective, Preventive, Improvement

    # Responsabilité
    responsible_id = Column(UniversalUUID(), nullable=False)
    department = Column(String(100))

    # Dates
    due_date = Column(Date, nullable=False)
    start_date = Column(Date)
    completion_date = Column(Date)

    # Statut
    status = Column(Enum(ActionStatus), default=ActionStatus.OPEN)
    priority = Column(Enum(RequirementPriority), default=RequirementPriority.MEDIUM)
    progress_percent = Column(Integer, default=0)

    # Résolution
    resolution_notes = Column(Text)
    evidence_provided = Column(JSON)

    # Vérification
    verified_by = Column(UniversalUUID())
    verified_at = Column(DateTime)
    verification_notes = Column(Text)

    # Coût
    estimated_cost = Column(Numeric(15, 2))
    actual_cost = Column(Numeric(15, 2))

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())

    # Relations
    gap = relationship("ComplianceGap", back_populates="actions")
    requirement = relationship("Requirement", back_populates="actions")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'number', name='uq_compliance_action_number'),
        Index('ix_compliance_action_tenant_status', 'tenant_id', 'status'),
    )


# =============================================================================
# MODÈLES - POLITIQUES
# =============================================================================

class Policy(Base):
    """Politique interne."""
    __tablename__ = "compliance_policies"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    type = Column(Enum(DocumentType), default=DocumentType.POLICY)

    # Classement
    category = Column(String(100))
    department = Column(String(100))

    # Version
    version = Column(String(20), default="1.0")
    version_date = Column(Date)
    previous_version_id = Column(UniversalUUID())

    # Contenu
    content = Column(Text)
    summary = Column(Text)

    # Dates
    effective_date = Column(Date)
    expiry_date = Column(Date)
    next_review_date = Column(Date)
    last_reviewed_date = Column(Date)

    # Approbation
    owner_id = Column(UniversalUUID())
    approved_by = Column(UniversalUUID())
    approved_at = Column(DateTime)

    # Distribution
    is_published = Column(Boolean, default=False)
    requires_acknowledgment = Column(Boolean, default=True)
    target_audience = Column(JSON)  # Départements/rôles concernés

    # Statut
    is_active = Column(Boolean, default=True)

    # Fichier
    file_path = Column(Text)
    file_name = Column(String(255))

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())

    # Relations
    acknowledgments = relationship("PolicyAcknowledgment", back_populates="policy", lazy="dynamic")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', 'version', name='uq_policy_version'),
        Index('ix_policy_tenant_active', 'tenant_id', 'is_active'),
    )


class PolicyAcknowledgment(Base):
    """Accusé de réception de politique."""
    __tablename__ = "compliance_policy_acknowledgments"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Liens
    policy_id = Column(UniversalUUID(), ForeignKey("compliance_policies.id"), nullable=False)
    user_id = Column(UniversalUUID(), nullable=False)

    # Acknowledgment
    acknowledged_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(50))

    # Statut
    is_valid = Column(Boolean, default=True)

    # Notes
    notes = Column(Text)

    # Relations
    policy = relationship("Policy", back_populates="acknowledgments")

    __table_args__ = (
        UniqueConstraint('policy_id', 'user_id', name='uq_acknowledgment_user'),
        Index('ix_acknowledgment_tenant_user', 'tenant_id', 'user_id'),
    )


# =============================================================================
# MODÈLES - FORMATIONS
# =============================================================================

class ComplianceTraining(Base):
    """Formation de conformité."""
    __tablename__ = "compliance_trainings"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Contenu
    content_type = Column(String(50))  # Online, Classroom, Video, Document
    duration_hours = Column(Numeric(5, 2))
    passing_score = Column(Integer)  # Score requis pour réussir

    # Catégorie
    category = Column(String(100))
    regulation_id = Column(UniversalUUID(), ForeignKey("compliance_regulations.id"))

    # Audience
    is_mandatory = Column(Boolean, default=True)
    target_departments = Column(JSON)
    target_roles = Column(JSON)

    # Périodicité
    recurrence_months = Column(Integer)  # Renouvellement tous les X mois

    # Dates
    available_from = Column(Date)
    available_until = Column(Date)

    # Statut
    is_active = Column(Boolean, default=True)

    # Ressources
    materials_url = Column(Text)
    quiz_enabled = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())

    # Relations
    completions = relationship("TrainingCompletion", back_populates="training", lazy="dynamic")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_training_code'),
    )


class TrainingCompletion(Base):
    """Complétion de formation."""
    __tablename__ = "compliance_training_completions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Liens
    training_id = Column(UniversalUUID(), ForeignKey("compliance_trainings.id"), nullable=False)
    user_id = Column(UniversalUUID(), nullable=False)

    # Dates
    assigned_date = Column(Date)
    due_date = Column(Date)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Résultats
    score = Column(Integer)
    passed = Column(Boolean)
    attempts = Column(Integer, default=0)

    # Certificat
    certificate_number = Column(String(100))
    expiry_date = Column(Date)

    # Statut
    is_current = Column(Boolean, default=True)  # Certification valide actuelle

    # Notes
    notes = Column(Text)

    # Relations
    training = relationship("ComplianceTraining", back_populates="completions")

    __table_args__ = (
        Index('ix_completion_tenant_user', 'tenant_id', 'user_id'),
    )


# =============================================================================
# MODÈLES - DOCUMENTS
# =============================================================================

class ComplianceDocument(Base):
    """Document de conformité."""
    __tablename__ = "compliance_documents"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    type = Column(Enum(DocumentType), nullable=False)

    # Classification
    category = Column(String(100))
    regulation_id = Column(UniversalUUID(), ForeignKey("compliance_regulations.id"))

    # Version
    version = Column(String(20), default="1.0")
    version_date = Column(Date, default=date.today)

    # Dates
    effective_date = Column(Date)
    expiry_date = Column(Date)
    next_review_date = Column(Date)

    # Fichier
    file_path = Column(Text)
    file_name = Column(String(255))
    file_size = Column(Integer)
    mime_type = Column(String(100))

    # Propriétaire
    owner_id = Column(UniversalUUID())
    department = Column(String(100))

    # Approbation
    approved_by = Column(UniversalUUID())
    approved_at = Column(DateTime)

    # Statut
    is_active = Column(Boolean, default=True)
    is_controlled = Column(Boolean, default=True)  # Document contrôlé

    # Métadonnées
    tags = Column(JSON)
    external_reference = Column(String(200))

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', 'version', name='uq_document_version'),
        Index('ix_compliance_document_tenant_type', 'tenant_id', 'type'),
    )


# =============================================================================
# MODÈLES - AUDITS
# =============================================================================

class ComplianceAudit(Base):
    """Audit de conformité."""
    __tablename__ = "compliance_audits"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    number = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Type
    audit_type = Column(String(50), nullable=False)  # Internal, External, Regulatory
    regulation_id = Column(UniversalUUID(), ForeignKey("compliance_regulations.id"))

    # Scope
    scope = Column(Text)
    departments = Column(JSON)

    # Dates
    planned_start = Column(Date)
    planned_end = Column(Date)
    actual_start = Column(Date)
    actual_end = Column(Date)

    # Équipe
    lead_auditor_id = Column(UniversalUUID())
    auditor_ids = Column(JSON)
    auditee_ids = Column(JSON)

    # Statut
    status = Column(Enum(AuditStatus), default=AuditStatus.PLANNED)

    # Résultats
    total_findings = Column(Integer, default=0)
    critical_findings = Column(Integer, default=0)
    major_findings = Column(Integer, default=0)
    minor_findings = Column(Integer, default=0)
    observations = Column(Integer, default=0)

    # Rapport
    executive_summary = Column(Text)
    conclusions = Column(Text)
    recommendations = Column(Text)
    report_file_path = Column(Text)

    # Approbation
    approved_by = Column(UniversalUUID())
    approved_at = Column(DateTime)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())

    # Relations
    findings = relationship("ComplianceAuditFinding", back_populates="audit", lazy="dynamic")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'number', name='uq_audit_number'),
        Index('ix_audit_tenant_status', 'tenant_id', 'status'),
    )


class ComplianceAuditFinding(Base):
    """Constatation d'audit (distinct de quality.AuditFinding)."""
    __tablename__ = "compliance_audit_findings"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Liens
    audit_id = Column(UniversalUUID(), ForeignKey("compliance_audits.id"), nullable=False)
    requirement_id = Column(UniversalUUID(), ForeignKey("compliance_requirements.id"))

    # Identification
    number = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # Classification
    severity = Column(Enum(FindingSeverity), default=FindingSeverity.OBSERVATION)
    category = Column(String(100))

    # Détails
    evidence = Column(Text)
    root_cause = Column(Text)
    recommendation = Column(Text)

    # Dates
    identified_date = Column(Date, default=date.today)
    response_due_date = Column(Date)
    closure_date = Column(Date)

    # Responsable
    responsible_id = Column(UniversalUUID())

    # Statut
    is_closed = Column(Boolean, default=False)

    # Réponse
    response = Column(Text)
    response_date = Column(Date)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())

    # Relations
    audit = relationship("ComplianceAudit", back_populates="findings")

    __table_args__ = (
        Index('ix_finding_tenant_severity', 'tenant_id', 'severity'),
    )


# =============================================================================
# MODÈLES - RISQUES
# =============================================================================

class ComplianceRisk(Base):
    """Risque de conformité."""
    __tablename__ = "compliance_risks"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)

    # Classification
    category = Column(String(100))
    regulation_id = Column(UniversalUUID(), ForeignKey("compliance_regulations.id"))

    # Évaluation
    likelihood = Column(Integer)  # 1-5
    impact = Column(Integer)  # 1-5
    risk_score = Column(Integer)  # likelihood * impact
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.MEDIUM)

    # Risque résiduel (après mitigation)
    residual_likelihood = Column(Integer)
    residual_impact = Column(Integer)
    residual_score = Column(Integer)
    residual_level = Column(Enum(RiskLevel))

    # Traitement
    treatment_strategy = Column(String(50))  # Mitigate, Accept, Transfer, Avoid
    treatment_description = Column(Text)

    # Contrôles
    current_controls = Column(Text)
    planned_controls = Column(Text)

    # Responsabilité
    owner_id = Column(UniversalUUID())
    department = Column(String(100))

    # Dates
    identified_date = Column(Date, default=date.today)
    last_review_date = Column(Date)
    next_review_date = Column(Date)

    # Statut
    is_active = Column(Boolean, default=True)
    is_accepted = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_risk_code'),
        Index('ix_compliance_risk_tenant_level', 'tenant_id', 'risk_level'),
    )


# =============================================================================
# MODÈLES - INCIDENTS
# =============================================================================

class ComplianceIncident(Base):
    """Incident de conformité."""
    __tablename__ = "compliance_incidents"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    number = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # Classification
    incident_type = Column(String(100))
    severity = Column(Enum(IncidentSeverity), default=IncidentSeverity.MEDIUM)
    regulation_id = Column(UniversalUUID(), ForeignKey("compliance_regulations.id"))

    # Dates
    incident_date = Column(DateTime, nullable=False)
    reported_date = Column(DateTime, default=datetime.utcnow)
    resolved_date = Column(DateTime)
    closed_date = Column(DateTime)

    # Personnes
    reporter_id = Column(UniversalUUID(), nullable=False)
    assigned_to = Column(UniversalUUID())
    department = Column(String(100))

    # Statut
    status = Column(Enum(IncidentStatus), default=IncidentStatus.REPORTED)

    # Investigation
    investigation_notes = Column(Text)
    root_cause = Column(Text)
    impact_assessment = Column(Text)

    # Résolution
    resolution = Column(Text)
    lessons_learned = Column(Text)

    # Notification
    requires_disclosure = Column(Boolean, default=False)
    disclosure_date = Column(Date)
    disclosure_recipients = Column(JSON)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'number', name='uq_incident_number'),
        Index('ix_compliance_incident_tenant_status', 'tenant_id', 'status'),
    )


# =============================================================================
# MODÈLES - RAPPORTS
# =============================================================================

class ComplianceReport(Base):
    """Rapport de conformité."""
    __tablename__ = "compliance_reports"

    id = Column(UniversalUUID(), primary_key=True, default=uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    number = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    type = Column(Enum(ReportType), nullable=False)

    # Période
    period_start = Column(Date)
    period_end = Column(Date)

    # Scope
    regulation_ids = Column(JSON)
    department_ids = Column(JSON)

    # Contenu
    executive_summary = Column(Text)
    content = Column(JSON)  # Structure JSON du rapport

    # Métriques
    metrics = Column(JSON)

    # Fichier
    file_path = Column(Text)
    file_name = Column(String(255))

    # Statut
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime)

    # Destinataires
    recipients = Column(JSON)

    # Approbation
    approved_by = Column(UniversalUUID())
    approved_at = Column(DateTime)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'number', name='uq_report_number'),
        Index('ix_report_tenant_type', 'tenant_id', 'type'),
    )
