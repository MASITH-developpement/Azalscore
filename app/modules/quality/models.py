"""
AZALS MODULE M7 - Modèles Qualité (Quality Management)
======================================================

Modèles SQLAlchemy pour le module de gestion de la qualité.
REFACTORED: Migration vers UUID pour production SaaS industrielle.
NOTE: ForeignKey retirées des modèles pour bootstrap Alembic sécurisé.
"""

import enum
import uuid

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Date,
    Numeric,
    Enum as SQLEnum,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.core.types import UniversalUUID, JSONB


# ============================================================================
# ENUMS
# ============================================================================

class NonConformanceType(str, enum.Enum):
    """Types de non-conformité"""
    PRODUCT = "PRODUCT"
    PROCESS = "PROCESS"
    SERVICE = "SERVICE"
    SUPPLIER = "SUPPLIER"
    CUSTOMER = "CUSTOMER"
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"
    AUDIT = "AUDIT"
    REGULATORY = "REGULATORY"


class NonConformanceStatus(str, enum.Enum):
    """Statuts de non-conformité"""
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    UNDER_ANALYSIS = "UNDER_ANALYSIS"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    IN_PROGRESS = "IN_PROGRESS"
    VERIFICATION = "VERIFICATION"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class NonConformanceSeverity(str, enum.Enum):
    """Niveaux de sévérité"""
    MINOR = "MINOR"
    MAJOR = "MAJOR"
    CRITICAL = "CRITICAL"
    BLOCKING = "BLOCKING"


class ControlType(str, enum.Enum):
    """Types de contrôle qualité"""
    INCOMING = "INCOMING"
    IN_PROCESS = "IN_PROCESS"
    FINAL = "FINAL"
    OUTGOING = "OUTGOING"
    SAMPLING = "SAMPLING"
    DESTRUCTIVE = "DESTRUCTIVE"
    NON_DESTRUCTIVE = "NON_DESTRUCTIVE"
    VISUAL = "VISUAL"
    DIMENSIONAL = "DIMENSIONAL"
    FUNCTIONAL = "FUNCTIONAL"
    LABORATORY = "LABORATORY"


class ControlStatus(str, enum.Enum):
    """Statuts de contrôle qualité"""
    PLANNED = "PLANNED"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ControlResult(str, enum.Enum):
    """Résultats de contrôle"""
    PASSED = "PASSED"
    FAILED = "FAILED"
    CONDITIONAL = "CONDITIONAL"
    PENDING = "PENDING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AuditType(str, enum.Enum):
    """Types d'audit"""
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"
    SUPPLIER = "SUPPLIER"
    CUSTOMER = "CUSTOMER"
    CERTIFICATION = "CERTIFICATION"
    SURVEILLANCE = "SURVEILLANCE"
    PROCESS = "PROCESS"
    PRODUCT = "PRODUCT"
    SYSTEM = "SYSTEM"


class AuditStatus(str, enum.Enum):
    """Statuts d'audit"""
    PLANNED = "PLANNED"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REPORT_PENDING = "REPORT_PENDING"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class FindingSeverity(str, enum.Enum):
    """Sévérité des constats d'audit"""
    OBSERVATION = "OBSERVATION"
    MINOR = "MINOR"
    MAJOR = "MAJOR"
    CRITICAL = "CRITICAL"


class CAPAType(str, enum.Enum):
    """Types d'actions correctives/préventives"""
    CORRECTIVE = "CORRECTIVE"
    PREVENTIVE = "PREVENTIVE"
    IMPROVEMENT = "IMPROVEMENT"


class CAPAStatus(str, enum.Enum):
    """Statuts CAPA"""
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    ANALYSIS = "ANALYSIS"
    ACTION_PLANNING = "ACTION_PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    VERIFICATION = "VERIFICATION"
    CLOSED_EFFECTIVE = "CLOSED_EFFECTIVE"
    CLOSED_INEFFECTIVE = "CLOSED_INEFFECTIVE"
    CANCELLED = "CANCELLED"


class ClaimStatus(str, enum.Enum):
    """Statuts réclamation client"""
    RECEIVED = "RECEIVED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    PENDING_RESPONSE = "PENDING_RESPONSE"
    RESPONSE_SENT = "RESPONSE_SENT"
    IN_RESOLUTION = "IN_RESOLUTION"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


class CertificationStatus(str, enum.Enum):
    """Statuts de certification"""
    PLANNED = "PLANNED"
    IN_PREPARATION = "IN_PREPARATION"
    AUDIT_SCHEDULED = "AUDIT_SCHEDULED"
    AUDIT_COMPLETED = "AUDIT_COMPLETED"
    CERTIFIED = "CERTIFIED"
    SUSPENDED = "SUSPENDED"
    WITHDRAWN = "WITHDRAWN"
    EXPIRED = "EXPIRED"


# ============================================================================
# MODÈLES - NON-CONFORMITÉS
# ============================================================================

class NonConformance(Base):
    """Non-conformité"""
    __tablename__ = "quality_non_conformances"
    __table_args__ = (
        Index("idx_nc_tenant", "tenant_id"),
        Index("idx_nc_type", "tenant_id", "nc_type"),
        Index("idx_nc_status", "tenant_id", "status"),
        Index("idx_nc_severity", "tenant_id", "severity"),
        Index("idx_nc_detected", "tenant_id", "detected_date"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    nc_number = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    nc_type = Column(SQLEnum(NonConformanceType), nullable=False)
    status = Column(SQLEnum(NonConformanceStatus), default=NonConformanceStatus.DRAFT)
    severity = Column(SQLEnum(NonConformanceSeverity), nullable=False)

    # Détection
    detected_date = Column(Date, nullable=False)
    detected_by_id = Column(UniversalUUID())  # Référence users
    detection_location = Column(String(200))
    detection_phase = Column(String(100))

    # Origine
    source_type = Column(String(50))  # PRODUCTION, RECEPTION, CLIENT, AUDIT, etc.
    source_reference = Column(String(100))
    source_id = Column(UniversalUUID())

    # Produit/Article concerné - FK gérée via migration Alembic séparée
    product_id = Column(UniversalUUID())
    lot_number = Column(String(100))
    serial_number = Column(String(100))
    quantity_affected = Column(Numeric(15, 3))
    unit_id = Column(UniversalUUID())

    # Fournisseur (si applicable)
    supplier_id = Column(UniversalUUID())

    # Client (si applicable)
    customer_id = Column(UniversalUUID())

    # Analyse des causes
    immediate_cause = Column(Text)
    root_cause = Column(Text)
    cause_analysis_method = Column(String(100))  # 5 Pourquoi, Ishikawa, etc.
    cause_analysis_date = Column(Date)
    cause_analyzed_by_id = Column(UniversalUUID())  # Référence users

    # Impact
    impact_description = Column(Text)
    estimated_cost = Column(Numeric(15, 2))
    actual_cost = Column(Numeric(15, 2))
    cost_currency = Column(String(3), default="EUR")

    # Traitement immédiat
    immediate_action = Column(Text)
    immediate_action_date = Column(DateTime)
    immediate_action_by_id = Column(UniversalUUID())  # Référence users

    # Responsabilité
    responsible_id = Column(UniversalUUID())  # Référence users
    department = Column(String(100))

    # Décision
    disposition = Column(String(50))  # REWORK, SCRAP, USE_AS_IS, RETURN, etc.
    disposition_date = Column(Date)
    disposition_by_id = Column(UniversalUUID())  # Référence users
    disposition_justification = Column(Text)

    # CAPA associé - FK gérée via migration Alembic séparée
    capa_id = Column(UniversalUUID())
    capa_required = Column(Boolean, default=False)

    # Clôture
    closed_date = Column(Date)
    closed_by_id = Column(UniversalUUID())  # Référence users
    closure_justification = Column(Text)
    effectiveness_verified = Column(Boolean, default=False)
    effectiveness_date = Column(Date)

    # Pièces jointes et notes
    attachments = Column(JSONB, default=list)
    notes = Column(Text)

    # Métadonnées
    is_recurrent = Column(Boolean, default=False)
    recurrence_count = Column(Integer, default=0)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())
    updated_by = Column(UniversalUUID())

    # Relationships (FK gérée via Alembic, pas dans SQLAlchemy)
    actions = relationship(
        "NonConformanceAction",
        back_populates="non_conformance",
        cascade="all, delete-orphan",
        foreign_keys="NonConformanceAction.nc_id"
    )


class NonConformanceAction(Base):
    """Actions correctives pour non-conformité"""
    __tablename__ = "quality_nc_actions"
    __table_args__ = (
        Index("idx_nc_action_tenant", "tenant_id"),
        Index("idx_nc_action_nc", "nc_id"),
        Index("idx_nc_action_status", "status"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    # FK gérée via migration Alembic séparée
    nc_id = Column(UniversalUUID(), nullable=False)

    # Action
    action_number = Column(Integer, nullable=False)
    action_type = Column(String(50), nullable=False)  # IMMEDIATE, CORRECTIVE, PREVENTIVE
    description = Column(Text, nullable=False)

    # Responsabilité
    responsible_id = Column(UniversalUUID())  # Référence users

    # Planification
    planned_date = Column(Date)
    due_date = Column(Date)
    completed_date = Column(Date)

    # Statut
    status = Column(String(50), default="PLANNED")

    # Vérification
    verified = Column(Boolean, default=False)
    verified_date = Column(Date)
    verified_by_id = Column(UniversalUUID())  # Référence users
    verification_result = Column(Text)

    # Commentaires
    comments = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())

    # Relationship inverse
    non_conformance = relationship(
        "NonConformance",
        back_populates="actions",
        foreign_keys=[nc_id]
    )


# ============================================================================
# MODÈLES - CONTRÔLES QUALITÉ
# ============================================================================

class QualityControlTemplate(Base):
    """Modèle/Template de contrôle qualité"""
    __tablename__ = "quality_control_templates"
    __table_args__ = (
        Index("idx_qct_tenant", "tenant_id"),
        Index("idx_qct_code", "tenant_id", "code"),
        UniqueConstraint("tenant_id", "code", name="uq_qct_code"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    version = Column(String(20), default="1.0")

    # Type de contrôle
    control_type = Column(SQLEnum(ControlType), nullable=False)

    # Application
    applies_to = Column(String(50))  # PRODUCT, PROCESS, MATERIAL, etc.
    product_category_id = Column(UniversalUUID())

    # Instructions
    instructions = Column(Text)
    sampling_plan = Column(Text)
    acceptance_criteria = Column(Text)

    # Durée estimée
    estimated_duration_minutes = Column(Integer)

    # Équipements requis
    required_equipment = Column(JSONB, default=list)

    # Statut
    is_active = Column(Boolean, default=True)
    valid_from = Column(Date)
    valid_until = Column(Date)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())

    # Relationships
    items = relationship(
        "QualityControlTemplateItem",
        back_populates="template",
        cascade="all, delete-orphan",
        foreign_keys="QualityControlTemplateItem.template_id"
    )


class QualityControlTemplateItem(Base):
    """Point de contrôle dans un template"""
    __tablename__ = "quality_control_template_items"
    __table_args__ = (
        Index("idx_qcti_tenant", "tenant_id"),
        Index("idx_qcti_template", "template_id"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    # FK gérée via migration Alembic séparée
    template_id = Column(UniversalUUID(), nullable=False)

    # Identification
    sequence = Column(Integer, nullable=False)
    characteristic = Column(String(200), nullable=False)
    description = Column(Text)

    # Type de mesure
    measurement_type = Column(String(50), nullable=False)  # NUMERIC, BOOLEAN, VISUAL, TEXT
    unit = Column(String(50))

    # Spécifications
    nominal_value = Column(Numeric(15, 6))
    tolerance_min = Column(Numeric(15, 6))
    tolerance_max = Column(Numeric(15, 6))
    upper_limit = Column(Numeric(15, 6))
    lower_limit = Column(Numeric(15, 6))

    # Pour contrôle visuel/booléen
    expected_result = Column(String(200))

    # Méthode
    measurement_method = Column(Text)
    equipment_code = Column(String(100))

    # Criticité
    is_critical = Column(Boolean, default=False)
    is_mandatory = Column(Boolean, default=True)

    # Fréquence
    sampling_frequency = Column(String(100))

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship inverse
    template = relationship(
        "QualityControlTemplate",
        back_populates="items",
        foreign_keys=[template_id]
    )


class QualityControl(Base):
    """Contrôle qualité exécuté"""
    __tablename__ = "quality_controls"
    __table_args__ = (
        Index("idx_qc_tenant", "tenant_id"),
        Index("idx_qc_number", "tenant_id", "control_number"),
        Index("idx_qc_type", "tenant_id", "control_type"),
        Index("idx_qc_status", "tenant_id", "status"),
        Index("idx_qc_date", "tenant_id", "control_date"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification - FK gérées via migration Alembic séparée
    control_number = Column(String(50), nullable=False)
    template_id = Column(UniversalUUID())
    control_type = Column(SQLEnum(ControlType), nullable=False)

    # Objet du contrôle
    source_type = Column(String(50))  # RECEPTION, PRODUCTION, EXPEDITION
    source_reference = Column(String(100))
    source_id = Column(UniversalUUID())

    # Produit contrôlé - FK gérée via migration Alembic séparée
    product_id = Column(UniversalUUID())
    lot_number = Column(String(100))
    serial_number = Column(String(100))

    # Quantités
    quantity_to_control = Column(Numeric(15, 3))
    quantity_controlled = Column(Numeric(15, 3))
    quantity_conforming = Column(Numeric(15, 3))
    quantity_non_conforming = Column(Numeric(15, 3))
    unit_id = Column(UniversalUUID())

    # Fournisseur (réception)
    supplier_id = Column(UniversalUUID())

    # Client (expédition)
    customer_id = Column(UniversalUUID())

    # Exécution
    control_date = Column(Date, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    location = Column(String(200))

    # Contrôleur
    controller_id = Column(UniversalUUID())  # Référence users

    # Résultat global
    status = Column(SQLEnum(ControlStatus), default=ControlStatus.PLANNED)
    result = Column(SQLEnum(ControlResult))
    result_date = Column(DateTime)

    # Décision
    decision = Column(String(50))  # ACCEPT, REJECT, CONDITIONAL, REWORK
    decision_by_id = Column(UniversalUUID())  # Référence users
    decision_date = Column(DateTime)
    decision_comments = Column(Text)

    # Non-conformité générée - FK gérée via migration Alembic séparée
    nc_id = Column(UniversalUUID())

    # Observations
    observations = Column(Text)
    attachments = Column(JSONB, default=list)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())

    # Relationships
    lines = relationship(
        "QualityControlLine",
        back_populates="control",
        cascade="all, delete-orphan",
        foreign_keys="QualityControlLine.control_id"
    )


class QualityControlLine(Base):
    """Ligne de contrôle qualité (mesure)"""
    __tablename__ = "quality_control_lines"
    __table_args__ = (
        Index("idx_qcl_tenant", "tenant_id"),
        Index("idx_qcl_control", "control_id"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    # FK gérées via migration Alembic séparée
    control_id = Column(UniversalUUID(), nullable=False)
    template_item_id = Column(UniversalUUID())

    # Identification
    sequence = Column(Integer, nullable=False)
    characteristic = Column(String(200), nullable=False)

    # Spécifications
    nominal_value = Column(Numeric(15, 6))
    tolerance_min = Column(Numeric(15, 6))
    tolerance_max = Column(Numeric(15, 6))
    unit = Column(String(50))

    # Mesure
    measured_value = Column(Numeric(15, 6))
    measured_text = Column(String(500))
    measured_boolean = Column(Boolean)
    measurement_date = Column(DateTime)

    # Résultat
    result = Column(SQLEnum(ControlResult))
    deviation = Column(Numeric(15, 6))

    # Équipement utilisé
    equipment_code = Column(String(100))
    equipment_serial = Column(String(100))

    # Commentaires
    comments = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UniversalUUID())

    # Relationship inverse
    control = relationship(
        "QualityControl",
        back_populates="lines",
        foreign_keys=[control_id]
    )


# ============================================================================
# MODÈLES - AUDITS
# ============================================================================

class QualityAudit(Base):
    """Audit qualité"""
    __tablename__ = "quality_audits"
    __table_args__ = (
        Index("idx_audit_tenant", "tenant_id"),
        Index("idx_audit_number", "tenant_id", "audit_number"),
        Index("idx_audit_type", "tenant_id", "audit_type"),
        Index("idx_audit_status", "tenant_id", "status"),
        Index("idx_audit_date", "tenant_id", "planned_date"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    audit_number = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    audit_type = Column(SQLEnum(AuditType), nullable=False)

    # Référentiel
    reference_standard = Column(String(200))  # ISO 9001, ISO 14001, etc.
    reference_version = Column(String(50))
    audit_scope = Column(Text)

    # Planification
    planned_date = Column(Date)
    planned_end_date = Column(Date)
    actual_date = Column(Date)
    actual_end_date = Column(Date)

    # Statut
    status = Column(SQLEnum(AuditStatus), default=AuditStatus.PLANNED)

    # Équipe d'audit
    lead_auditor_id = Column(UniversalUUID())  # Référence users
    auditors = Column(JSONB, default=list)

    # Entité auditée
    audited_entity = Column(String(200))
    audited_department = Column(String(200))
    auditee_contact_id = Column(UniversalUUID())  # Référence users

    # Fournisseur (audit fournisseur)
    supplier_id = Column(UniversalUUID())

    # Résultats
    total_findings = Column(Integer, default=0)
    critical_findings = Column(Integer, default=0)
    major_findings = Column(Integer, default=0)
    minor_findings = Column(Integer, default=0)
    observations = Column(Integer, default=0)

    # Score/Note
    overall_score = Column(Numeric(5, 2))
    max_score = Column(Numeric(5, 2))

    # Conclusion
    audit_conclusion = Column(Text)
    recommendation = Column(Text)

    # Rapport
    report_date = Column(Date)
    report_file = Column(String(500))

    # Suivi
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(Date)
    follow_up_completed = Column(Boolean, default=False)

    # Clôture
    closed_date = Column(Date)
    closed_by_id = Column(UniversalUUID())  # Référence users

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())

    # Relationships
    findings = relationship(
        "AuditFinding",
        back_populates="audit",
        cascade="all, delete-orphan",
        foreign_keys="AuditFinding.audit_id"
    )


class AuditFinding(Base):
    """Constat d'audit"""
    __tablename__ = "quality_audit_findings"
    __table_args__ = (
        Index("idx_finding_tenant", "tenant_id"),
        Index("idx_finding_audit", "audit_id"),
        Index("idx_finding_severity", "severity"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    # FK gérée via migration Alembic séparée
    audit_id = Column(UniversalUUID(), nullable=False)

    # Identification
    finding_number = Column(Integer, nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)

    # Classification
    severity = Column(SQLEnum(FindingSeverity), nullable=False)
    category = Column(String(100))

    # Référence
    clause_reference = Column(String(100))
    process_reference = Column(String(100))
    evidence = Column(Text)

    # Risque
    risk_description = Column(Text)
    risk_level = Column(String(50))

    # CAPA - FK gérée via migration Alembic séparée
    capa_required = Column(Boolean, default=False)
    capa_id = Column(UniversalUUID())

    # Réponse
    auditee_response = Column(Text)
    response_date = Column(Date)

    # Suivi
    action_due_date = Column(Date)
    action_completed_date = Column(Date)
    status = Column(String(50), default="OPEN")

    # Vérification
    verified = Column(Boolean, default=False)
    verified_date = Column(Date)
    verified_by_id = Column(UniversalUUID())  # Référence users
    verification_comments = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())

    # Relationship inverse
    audit = relationship(
        "QualityAudit",
        back_populates="findings",
        foreign_keys=[audit_id]
    )


# ============================================================================
# MODÈLES - CAPA (Actions Correctives et Préventives)
# ============================================================================

class CAPA(Base):
    """CAPA - Corrective and Preventive Action"""
    __tablename__ = "quality_capas"
    __table_args__ = (
        Index("idx_capa_tenant", "tenant_id"),
        Index("idx_capa_number", "tenant_id", "capa_number"),
        Index("idx_capa_type", "tenant_id", "capa_type"),
        Index("idx_capa_status", "tenant_id", "status"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    capa_number = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    capa_type = Column(SQLEnum(CAPAType), nullable=False)

    # Origine
    source_type = Column(String(50))  # NC, AUDIT, CLAIM, INTERNAL, etc.
    source_reference = Column(String(100))
    source_id = Column(UniversalUUID())

    # Statut et priorité
    status = Column(SQLEnum(CAPAStatus), default=CAPAStatus.DRAFT)
    priority = Column(String(20), default="MEDIUM")

    # Dates
    open_date = Column(Date, nullable=False)
    target_close_date = Column(Date)
    actual_close_date = Column(Date)

    # Responsabilité
    owner_id = Column(UniversalUUID(), nullable=False)  # Référence users
    department = Column(String(100))

    # Analyse des causes
    problem_statement = Column(Text)
    immediate_containment = Column(Text)
    root_cause_analysis = Column(Text)
    root_cause_method = Column(String(100))  # 5 Why, Fishbone, 8D, etc.
    root_cause_verified = Column(Boolean, default=False)

    # Impact
    impact_assessment = Column(Text)
    risk_level = Column(String(50))

    # Vérification efficacité
    effectiveness_criteria = Column(Text)
    effectiveness_verified = Column(Boolean, default=False)
    effectiveness_date = Column(Date)
    effectiveness_result = Column(Text)
    verified_by_id = Column(UniversalUUID())  # Référence users

    # Extension/Déploiement
    extension_required = Column(Boolean, default=False)
    extension_scope = Column(Text)
    extension_completed = Column(Boolean, default=False)

    # Clôture
    closure_comments = Column(Text)
    closed_by_id = Column(UniversalUUID())  # Référence users

    # Pièces jointes
    attachments = Column(JSONB, default=list)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())

    # Relationships
    actions = relationship(
        "CAPAAction",
        back_populates="capa",
        cascade="all, delete-orphan",
        foreign_keys="CAPAAction.capa_id"
    )


class CAPAAction(Base):
    """Action d'un CAPA"""
    __tablename__ = "quality_capa_actions"
    __table_args__ = (
        Index("idx_capa_action_tenant", "tenant_id"),
        Index("idx_capa_action_capa", "capa_id"),
        Index("idx_capa_action_status", "status"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    # FK gérée via migration Alembic séparée
    capa_id = Column(UniversalUUID(), nullable=False)

    # Identification
    action_number = Column(Integer, nullable=False)
    action_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)

    # Responsabilité
    responsible_id = Column(UniversalUUID())  # Référence users

    # Planification
    planned_date = Column(Date)
    due_date = Column(Date, nullable=False)
    completed_date = Column(Date)

    # Statut
    status = Column(String(50), default="PLANNED")

    # Résultat
    result = Column(Text)
    evidence = Column(Text)

    # Vérification
    verification_required = Column(Boolean, default=True)
    verified = Column(Boolean, default=False)
    verified_date = Column(Date)
    verified_by_id = Column(UniversalUUID())  # Référence users
    verification_result = Column(Text)

    # Coût
    estimated_cost = Column(Numeric(15, 2))
    actual_cost = Column(Numeric(15, 2))

    # Commentaires
    comments = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())

    # Relationship inverse
    capa = relationship(
        "CAPA",
        back_populates="actions",
        foreign_keys=[capa_id]
    )


# ============================================================================
# MODÈLES - RÉCLAMATIONS CLIENTS
# ============================================================================

class CustomerClaim(Base):
    """Réclamation client"""
    __tablename__ = "quality_customer_claims"
    __table_args__ = (
        Index("idx_claim_tenant", "tenant_id"),
        Index("idx_claim_number", "tenant_id", "claim_number"),
        Index("idx_claim_status", "tenant_id", "status"),
        Index("idx_claim_customer", "tenant_id", "customer_id"),
        Index("idx_claim_date", "tenant_id", "received_date"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    claim_number = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)

    # Client
    customer_id = Column(UniversalUUID(), nullable=False)
    customer_contact = Column(String(200))
    customer_reference = Column(String(100))

    # Réception
    received_date = Column(Date, nullable=False)
    received_via = Column(String(50))  # EMAIL, PHONE, LETTER, PORTAL
    received_by_id = Column(UniversalUUID())  # Référence users

    # Produit/Service concerné - FK gérée via migration Alembic séparée
    product_id = Column(UniversalUUID())
    order_reference = Column(String(100))
    invoice_reference = Column(String(100))
    lot_number = Column(String(100))
    quantity_affected = Column(Numeric(15, 3))

    # Classification
    claim_type = Column(String(50))  # QUALITY, DELIVERY, SERVICE, DOCUMENTATION, OTHER
    severity = Column(SQLEnum(NonConformanceSeverity))
    priority = Column(String(20), default="MEDIUM")

    # Statut
    status = Column(SQLEnum(ClaimStatus), default=ClaimStatus.RECEIVED)

    # Responsable
    owner_id = Column(UniversalUUID())  # Référence users

    # Investigation
    investigation_summary = Column(Text)
    root_cause = Column(Text)
    our_responsibility = Column(Boolean)

    # Non-conformité associée - FK gérée via migration Alembic séparée
    nc_id = Column(UniversalUUID())

    # CAPA associé - FK gérée via migration Alembic séparée
    capa_id = Column(UniversalUUID())

    # Réponse
    response_due_date = Column(Date)
    response_date = Column(Date)
    response_content = Column(Text)
    response_by_id = Column(UniversalUUID())  # Référence users

    # Résolution
    resolution_type = Column(String(50))  # REPLACEMENT, CREDIT, REFUND, REPAIR, NONE
    resolution_description = Column(Text)
    resolution_date = Column(Date)

    # Coût
    claim_amount = Column(Numeric(15, 2))
    accepted_amount = Column(Numeric(15, 2))
    cost_currency = Column(String(3), default="EUR")

    # Satisfaction client
    customer_satisfied = Column(Boolean)
    satisfaction_feedback = Column(Text)

    # Clôture
    closed_date = Column(Date)
    closed_by_id = Column(UniversalUUID())  # Référence users

    # Pièces jointes
    attachments = Column(JSONB, default=list)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())

    # Relationships
    actions = relationship(
        "ClaimAction",
        back_populates="claim",
        cascade="all, delete-orphan",
        foreign_keys="ClaimAction.claim_id"
    )


class ClaimAction(Base):
    """Action pour une réclamation client"""
    __tablename__ = "quality_claim_actions"
    __table_args__ = (
        Index("idx_claim_action_tenant", "tenant_id"),
        Index("idx_claim_action_claim", "claim_id"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    # FK gérée via migration Alembic séparée
    claim_id = Column(UniversalUUID(), nullable=False)

    # Action
    action_number = Column(Integer, nullable=False)
    action_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)

    # Responsabilité
    responsible_id = Column(UniversalUUID())  # Référence users

    # Planification
    due_date = Column(Date)
    completed_date = Column(Date)

    # Statut
    status = Column(String(50), default="PLANNED")

    # Résultat
    result = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())

    # Relationship inverse
    claim = relationship(
        "CustomerClaim",
        back_populates="actions",
        foreign_keys=[claim_id]
    )


# ============================================================================
# MODÈLES - INDICATEURS QUALITÉ
# ============================================================================

class QualityIndicator(Base):
    """Indicateur qualité (KPI)"""
    __tablename__ = "quality_indicators"
    __table_args__ = (
        Index("idx_qi_tenant", "tenant_id"),
        Index("idx_qi_code", "tenant_id", "code"),
        UniqueConstraint("tenant_id", "code", name="uq_qi_code"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))

    # Formule
    formula = Column(Text)
    unit = Column(String(50))

    # Objectifs
    target_value = Column(Numeric(15, 4))
    target_min = Column(Numeric(15, 4))
    target_max = Column(Numeric(15, 4))

    # Seuils d'alerte
    warning_threshold = Column(Numeric(15, 4))
    critical_threshold = Column(Numeric(15, 4))

    # Direction
    direction = Column(String(20))  # HIGHER_BETTER, LOWER_BETTER, TARGET

    # Fréquence de mesure
    measurement_frequency = Column(String(50))

    # Source de données
    data_source = Column(String(100))
    calculation_query = Column(Text)

    # Responsable
    owner_id = Column(UniversalUUID())  # Référence users

    # Statut
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())

    # Relationships
    measurements = relationship(
        "IndicatorMeasurement",
        back_populates="indicator",
        cascade="all, delete-orphan",
        foreign_keys="IndicatorMeasurement.indicator_id"
    )


class IndicatorMeasurement(Base):
    """Mesure d'un indicateur qualité"""
    __tablename__ = "quality_indicator_measurements"
    __table_args__ = (
        Index("idx_qim_tenant", "tenant_id"),
        Index("idx_qim_indicator", "indicator_id"),
        Index("idx_qim_date", "measurement_date"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    # FK gérée via migration Alembic séparée
    indicator_id = Column(UniversalUUID(), nullable=False)

    # Période
    measurement_date = Column(Date, nullable=False)
    period_start = Column(Date)
    period_end = Column(Date)

    # Valeur
    value = Column(Numeric(15, 4), nullable=False)

    # Contexte
    numerator = Column(Numeric(15, 4))
    denominator = Column(Numeric(15, 4))

    # Comparaison avec objectif
    target_value = Column(Numeric(15, 4))
    deviation = Column(Numeric(15, 4))
    achievement_rate = Column(Numeric(5, 2))

    # Statut
    status = Column(String(20))  # ON_TARGET, WARNING, CRITICAL

    # Analyse
    comments = Column(Text)
    action_required = Column(Boolean, default=False)

    # Source
    source = Column(String(100))  # MANUAL, CALCULATED, IMPORTED

    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UniversalUUID())

    # Relationship inverse
    indicator = relationship(
        "QualityIndicator",
        back_populates="measurements",
        foreign_keys=[indicator_id]
    )


# ============================================================================
# MODÈLES - CERTIFICATIONS
# ============================================================================

class Certification(Base):
    """Certification qualité"""
    __tablename__ = "quality_certifications"
    __table_args__ = (
        Index("idx_cert_tenant", "tenant_id"),
        Index("idx_cert_code", "tenant_id", "code"),
        Index("idx_cert_status", "tenant_id", "status"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Norme/Référentiel
    standard = Column(String(100), nullable=False)
    standard_version = Column(String(50))
    scope = Column(Text)

    # Organisme de certification
    certification_body = Column(String(200))
    certification_body_accreditation = Column(String(100))

    # Dates
    initial_certification_date = Column(Date)
    current_certificate_date = Column(Date)
    expiry_date = Column(Date)
    next_surveillance_date = Column(Date)
    next_renewal_date = Column(Date)

    # Certificat
    certificate_number = Column(String(100))
    certificate_file = Column(String(500))

    # Statut
    status = Column(SQLEnum(CertificationStatus), default=CertificationStatus.PLANNED)

    # Responsable
    manager_id = Column(UniversalUUID())  # Référence users

    # Coût
    annual_cost = Column(Numeric(15, 2))
    cost_currency = Column(String(3), default="EUR")

    # Notes
    notes = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())

    # Relationships
    audits = relationship(
        "CertificationAudit",
        back_populates="certification",
        cascade="all, delete-orphan",
        foreign_keys="CertificationAudit.certification_id"
    )


class CertificationAudit(Base):
    """Audit de certification"""
    __tablename__ = "quality_certification_audits"
    __table_args__ = (
        Index("idx_cert_audit_tenant", "tenant_id"),
        Index("idx_cert_audit_cert", "certification_id"),
        Index("idx_cert_audit_date", "audit_date"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    # FK gérée via migration Alembic séparée
    certification_id = Column(UniversalUUID(), nullable=False)

    # Type d'audit
    audit_type = Column(String(50), nullable=False)  # INITIAL, SURVEILLANCE, RENEWAL, SPECIAL

    # Dates
    audit_date = Column(Date, nullable=False)
    audit_end_date = Column(Date)

    # Auditeur
    lead_auditor = Column(String(200))
    audit_team = Column(JSONB, default=list)

    # Résultat
    result = Column(String(50))  # PASSED, CONDITIONAL, FAILED
    findings_count = Column(Integer, default=0)
    major_nc_count = Column(Integer, default=0)
    minor_nc_count = Column(Integer, default=0)
    observations_count = Column(Integer, default=0)

    # Rapport
    report_date = Column(Date)
    report_file = Column(String(500))

    # Suivi
    corrective_actions_due = Column(Date)
    corrective_actions_closed = Column(Date)
    follow_up_audit_date = Column(Date)

    # Lien avec audit interne - FK gérée via migration Alembic séparée
    quality_audit_id = Column(UniversalUUID())

    # Notes
    notes = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())

    # Relationship inverse
    certification = relationship(
        "Certification",
        back_populates="audits",
        foreign_keys=[certification_id]
    )
