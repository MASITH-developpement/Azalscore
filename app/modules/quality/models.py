"""
AZALS MODULE M7 - Modèles Qualité (Quality Management)
======================================================

Modèles SQLAlchemy pour le module de gestion de la qualité.
"""

import enum
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal

from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    Boolean,
    DateTime,
    Date,
    Numeric,
    ForeignKey,
    Enum,
    Index,
    CheckConstraint,
    UniqueConstraint,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


# ============================================================================
# ENUMS
# ============================================================================

class NonConformanceType(enum.Enum):
    """Types de non-conformité"""
    PRODUCT = "PRODUCT"                     # Non-conformité produit
    PROCESS = "PROCESS"                     # Non-conformité processus
    SERVICE = "SERVICE"                     # Non-conformité service
    SUPPLIER = "SUPPLIER"                   # Non-conformité fournisseur
    CUSTOMER = "CUSTOMER"                   # Réclamation client
    INTERNAL = "INTERNAL"                   # Détection interne
    EXTERNAL = "EXTERNAL"                   # Détection externe
    AUDIT = "AUDIT"                         # Issue d'audit
    REGULATORY = "REGULATORY"               # Non-conformité réglementaire


class NonConformanceStatus(enum.Enum):
    """Statuts de non-conformité"""
    DRAFT = "DRAFT"                         # Brouillon
    OPEN = "OPEN"                           # Ouverte
    UNDER_ANALYSIS = "UNDER_ANALYSIS"       # En cours d'analyse
    ACTION_REQUIRED = "ACTION_REQUIRED"     # Actions requises
    IN_PROGRESS = "IN_PROGRESS"             # Actions en cours
    VERIFICATION = "VERIFICATION"           # En vérification
    CLOSED = "CLOSED"                       # Clôturée
    CANCELLED = "CANCELLED"                 # Annulée


class NonConformanceSeverity(enum.Enum):
    """Niveaux de sévérité"""
    MINOR = "MINOR"                         # Mineure
    MAJOR = "MAJOR"                         # Majeure
    CRITICAL = "CRITICAL"                   # Critique
    BLOCKING = "BLOCKING"                   # Bloquante


class ControlType(enum.Enum):
    """Types de contrôle qualité"""
    INCOMING = "INCOMING"                   # Contrôle réception
    IN_PROCESS = "IN_PROCESS"               # Contrôle en-cours
    FINAL = "FINAL"                         # Contrôle final
    OUTGOING = "OUTGOING"                   # Contrôle expédition
    SAMPLING = "SAMPLING"                   # Contrôle échantillonnage
    DESTRUCTIVE = "DESTRUCTIVE"             # Contrôle destructif
    NON_DESTRUCTIVE = "NON_DESTRUCTIVE"     # Contrôle non-destructif
    VISUAL = "VISUAL"                       # Contrôle visuel
    DIMENSIONAL = "DIMENSIONAL"             # Contrôle dimensionnel
    FUNCTIONAL = "FUNCTIONAL"               # Contrôle fonctionnel
    LABORATORY = "LABORATORY"               # Analyse laboratoire


class ControlStatus(enum.Enum):
    """Statuts de contrôle qualité"""
    PLANNED = "PLANNED"                     # Planifié
    PENDING = "PENDING"                     # En attente
    IN_PROGRESS = "IN_PROGRESS"             # En cours
    COMPLETED = "COMPLETED"                 # Terminé
    CANCELLED = "CANCELLED"                 # Annulé


class ControlResult(enum.Enum):
    """Résultats de contrôle"""
    PASSED = "PASSED"                       # Conforme
    FAILED = "FAILED"                       # Non-conforme
    CONDITIONAL = "CONDITIONAL"             # Acceptation conditionnelle
    PENDING = "PENDING"                     # En attente de résultat
    NOT_APPLICABLE = "NOT_APPLICABLE"       # Non applicable


class AuditType(enum.Enum):
    """Types d'audit"""
    INTERNAL = "INTERNAL"                   # Audit interne
    EXTERNAL = "EXTERNAL"                   # Audit externe
    SUPPLIER = "SUPPLIER"                   # Audit fournisseur
    CUSTOMER = "CUSTOMER"                   # Audit client
    CERTIFICATION = "CERTIFICATION"         # Audit de certification
    SURVEILLANCE = "SURVEILLANCE"           # Audit de surveillance
    PROCESS = "PROCESS"                     # Audit processus
    PRODUCT = "PRODUCT"                     # Audit produit
    SYSTEM = "SYSTEM"                       # Audit système


class AuditStatus(enum.Enum):
    """Statuts d'audit"""
    PLANNED = "PLANNED"                     # Planifié
    SCHEDULED = "SCHEDULED"                 # Programmé
    IN_PROGRESS = "IN_PROGRESS"             # En cours
    COMPLETED = "COMPLETED"                 # Terminé
    REPORT_PENDING = "REPORT_PENDING"       # Rapport en attente
    CLOSED = "CLOSED"                       # Clôturé
    CANCELLED = "CANCELLED"                 # Annulé


class FindingSeverity(enum.Enum):
    """Sévérité des constats d'audit"""
    OBSERVATION = "OBSERVATION"             # Observation/piste d'amélioration
    MINOR = "MINOR"                         # Non-conformité mineure
    MAJOR = "MAJOR"                         # Non-conformité majeure
    CRITICAL = "CRITICAL"                   # Non-conformité critique


class CAPAType(enum.Enum):
    """Types d'actions correctives/préventives"""
    CORRECTIVE = "CORRECTIVE"               # Action corrective
    PREVENTIVE = "PREVENTIVE"               # Action préventive
    IMPROVEMENT = "IMPROVEMENT"             # Action d'amélioration


class CAPAStatus(enum.Enum):
    """Statuts CAPA"""
    DRAFT = "DRAFT"                         # Brouillon
    OPEN = "OPEN"                           # Ouvert
    ANALYSIS = "ANALYSIS"                   # En analyse
    ACTION_PLANNING = "ACTION_PLANNING"     # Planification actions
    IN_PROGRESS = "IN_PROGRESS"             # Actions en cours
    VERIFICATION = "VERIFICATION"           # Vérification efficacité
    CLOSED_EFFECTIVE = "CLOSED_EFFECTIVE"   # Clôturé - efficace
    CLOSED_INEFFECTIVE = "CLOSED_INEFFECTIVE"  # Clôturé - inefficace
    CANCELLED = "CANCELLED"                 # Annulé


class ClaimStatus(enum.Enum):
    """Statuts réclamation client"""
    RECEIVED = "RECEIVED"                   # Reçue
    ACKNOWLEDGED = "ACKNOWLEDGED"           # Accusée de réception
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"  # En cours d'investigation
    PENDING_RESPONSE = "PENDING_RESPONSE"   # Réponse en attente
    RESPONSE_SENT = "RESPONSE_SENT"         # Réponse envoyée
    IN_RESOLUTION = "IN_RESOLUTION"         # En résolution
    RESOLVED = "RESOLVED"                   # Résolue
    CLOSED = "CLOSED"                       # Clôturée
    REJECTED = "REJECTED"                   # Rejetée


class CertificationStatus(enum.Enum):
    """Statuts de certification"""
    PLANNED = "PLANNED"                     # Planifiée
    IN_PREPARATION = "IN_PREPARATION"       # En préparation
    AUDIT_SCHEDULED = "AUDIT_SCHEDULED"     # Audit programmé
    AUDIT_COMPLETED = "AUDIT_COMPLETED"     # Audit terminé
    CERTIFIED = "CERTIFIED"                 # Certifiée
    SUSPENDED = "SUSPENDED"                 # Suspendue
    WITHDRAWN = "WITHDRAWN"                 # Retirée
    EXPIRED = "EXPIRED"                     # Expirée


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

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False)

    # Identification
    nc_number = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    nc_type = Column(Enum(NonConformanceType), nullable=False)
    status = Column(Enum(NonConformanceStatus), default=NonConformanceStatus.DRAFT)
    severity = Column(Enum(NonConformanceSeverity), nullable=False)

    # Détection
    detected_date = Column(Date, nullable=False)
    detected_by_id = Column(BigInteger, ForeignKey("users.id"))
    detection_location = Column(String(200))
    detection_phase = Column(String(100))  # Phase de détection

    # Origine
    source_type = Column(String(50))  # PRODUCTION, RECEPTION, CLIENT, AUDIT, etc.
    source_reference = Column(String(100))  # Référence source (OF, BL, etc.)
    source_id = Column(BigInteger)  # ID de l'entité source

    # Produit/Article concerné
    product_id = Column(BigInteger, ForeignKey("inventory_products.id"))
    lot_number = Column(String(100))
    serial_number = Column(String(100))
    quantity_affected = Column(Numeric(15, 3))
    unit_id = Column(BigInteger)  # Référence unité (table settings non implémentée)

    # Fournisseur (si applicable)
    supplier_id = Column(BigInteger)  # Référence fournisseur (table purchase_suppliers non implémentée)

    # Client (si applicable)
    customer_id = Column(BigInteger)  # Référence client (table crm_clients non implémentée)

    # Analyse des causes
    immediate_cause = Column(Text)
    root_cause = Column(Text)
    cause_analysis_method = Column(String(100))  # 5 Pourquoi, Ishikawa, etc.
    cause_analysis_date = Column(Date)
    cause_analyzed_by_id = Column(BigInteger, ForeignKey("users.id"))

    # Impact
    impact_description = Column(Text)
    estimated_cost = Column(Numeric(15, 2))
    actual_cost = Column(Numeric(15, 2))
    cost_currency = Column(String(3), default="EUR")

    # Traitement immédiat
    immediate_action = Column(Text)
    immediate_action_date = Column(DateTime)
    immediate_action_by_id = Column(BigInteger, ForeignKey("users.id"))

    # Responsabilité
    responsible_id = Column(BigInteger, ForeignKey("users.id"))
    department = Column(String(100))

    # Décision
    disposition = Column(String(50))  # REWORK, SCRAP, USE_AS_IS, RETURN, etc.
    disposition_date = Column(Date)
    disposition_by_id = Column(BigInteger, ForeignKey("users.id"))
    disposition_justification = Column(Text)

    # CAPA associé
    capa_id = Column(BigInteger, ForeignKey("quality_capas.id"))
    capa_required = Column(Boolean, default=False)

    # Clôture
    closed_date = Column(Date)
    closed_by_id = Column(BigInteger, ForeignKey("users.id"))
    closure_justification = Column(Text)
    effectiveness_verified = Column(Boolean, default=False)
    effectiveness_date = Column(Date)

    # Pièces jointes et notes
    attachments = Column(JSON)  # Liste des fichiers joints
    notes = Column(Text)

    # Métadonnées
    is_recurrent = Column(Boolean, default=False)
    recurrence_count = Column(Integer, default=0)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(BigInteger, ForeignKey("users.id"))
    updated_by = Column(BigInteger, ForeignKey("users.id"))

    # Relations
    actions = relationship("NonConformanceAction", back_populates="non_conformance")


class NonConformanceAction(Base):
    """Actions correctives pour non-conformité"""
    __tablename__ = "quality_nc_actions"
    __table_args__ = (
        Index("idx_nc_action_nc", "nc_id"),
        Index("idx_nc_action_status", "status"),
        {"schema": None},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False)
    nc_id = Column(BigInteger, ForeignKey("quality_non_conformances.id"), nullable=False)

    # Action
    action_number = Column(Integer, nullable=False)
    action_type = Column(String(50), nullable=False)  # IMMEDIATE, CORRECTIVE, PREVENTIVE
    description = Column(Text, nullable=False)

    # Responsabilité
    responsible_id = Column(BigInteger, ForeignKey("users.id"))

    # Planification
    planned_date = Column(Date)
    due_date = Column(Date)
    completed_date = Column(Date)

    # Statut
    status = Column(String(50), default="PLANNED")  # PLANNED, IN_PROGRESS, COMPLETED, CANCELLED

    # Vérification
    verified = Column(Boolean, default=False)
    verified_date = Column(Date)
    verified_by_id = Column(BigInteger, ForeignKey("users.id"))
    verification_result = Column(Text)

    # Commentaires
    comments = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(BigInteger, ForeignKey("users.id"))

    # Relations
    non_conformance = relationship("NonConformance", back_populates="actions")


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

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    version = Column(String(20), default="1.0")

    # Type de contrôle
    control_type = Column(Enum(ControlType), nullable=False)

    # Application
    applies_to = Column(String(50))  # PRODUCT, PROCESS, MATERIAL, etc.
    product_category_id = Column(BigInteger)

    # Instructions
    instructions = Column(Text)
    sampling_plan = Column(Text)  # Plan d'échantillonnage
    acceptance_criteria = Column(Text)

    # Durée estimée
    estimated_duration_minutes = Column(Integer)

    # Équipements requis
    required_equipment = Column(JSON)  # Liste des équipements

    # Statut
    is_active = Column(Boolean, default=True)
    valid_from = Column(Date)
    valid_until = Column(Date)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(BigInteger, ForeignKey("users.id"))

    # Relations
    items = relationship("QualityControlTemplateItem", back_populates="template")


class QualityControlTemplateItem(Base):
    """Point de contrôle dans un template"""
    __tablename__ = "quality_control_template_items"
    __table_args__ = (
        Index("idx_qcti_template", "template_id"),
        {"schema": None},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False)
    template_id = Column(BigInteger, ForeignKey("quality_control_templates.id"), nullable=False)

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
    upper_limit = Column(Numeric(15, 6))  # Limite supérieure
    lower_limit = Column(Numeric(15, 6))  # Limite inférieure

    # Pour contrôle visuel/booléen
    expected_result = Column(String(200))

    # Méthode
    measurement_method = Column(Text)
    equipment_code = Column(String(100))

    # Criticité
    is_critical = Column(Boolean, default=False)
    is_mandatory = Column(Boolean, default=True)

    # Fréquence
    sampling_frequency = Column(String(100))  # 100%, 1/10, AQL, etc.

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relations
    template = relationship("QualityControlTemplate", back_populates="items")


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

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False)

    # Identification
    control_number = Column(String(50), nullable=False)
    template_id = Column(BigInteger, ForeignKey("quality_control_templates.id"))
    control_type = Column(Enum(ControlType), nullable=False)

    # Objet du contrôle
    source_type = Column(String(50))  # RECEPTION, PRODUCTION, EXPEDITION
    source_reference = Column(String(100))
    source_id = Column(BigInteger)

    # Produit contrôlé
    product_id = Column(BigInteger, ForeignKey("inventory_products.id"))
    lot_number = Column(String(100))
    serial_number = Column(String(100))

    # Quantités
    quantity_to_control = Column(Numeric(15, 3))
    quantity_controlled = Column(Numeric(15, 3))
    quantity_conforming = Column(Numeric(15, 3))
    quantity_non_conforming = Column(Numeric(15, 3))
    unit_id = Column(BigInteger)  # Référence unité (table settings non implémentée)

    # Fournisseur (réception)
    supplier_id = Column(BigInteger)  # Référence fournisseur (table purchase_suppliers non implémentée)

    # Client (expédition)
    customer_id = Column(BigInteger)  # Référence client (table crm_clients non implémentée)

    # Exécution
    control_date = Column(Date, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    location = Column(String(200))

    # Contrôleur
    controller_id = Column(BigInteger, ForeignKey("users.id"))

    # Résultat global
    status = Column(Enum(ControlStatus), default=ControlStatus.PLANNED)
    result = Column(Enum(ControlResult))
    result_date = Column(DateTime)

    # Décision
    decision = Column(String(50))  # ACCEPT, REJECT, CONDITIONAL, REWORK
    decision_by_id = Column(BigInteger, ForeignKey("users.id"))
    decision_date = Column(DateTime)
    decision_comments = Column(Text)

    # Non-conformité générée
    nc_id = Column(BigInteger, ForeignKey("quality_non_conformances.id"))

    # Observations
    observations = Column(Text)
    attachments = Column(JSON)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(BigInteger, ForeignKey("users.id"))

    # Relations
    lines = relationship("QualityControlLine", back_populates="control")


class QualityControlLine(Base):
    """Ligne de contrôle qualité (mesure)"""
    __tablename__ = "quality_control_lines"
    __table_args__ = (
        Index("idx_qcl_control", "control_id"),
        {"schema": None},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False)
    control_id = Column(BigInteger, ForeignKey("quality_controls.id"), nullable=False)
    template_item_id = Column(BigInteger, ForeignKey("quality_control_template_items.id"))

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
    measured_text = Column(String(500))  # Pour mesures non numériques
    measured_boolean = Column(Boolean)
    measurement_date = Column(DateTime)

    # Résultat
    result = Column(Enum(ControlResult))
    deviation = Column(Numeric(15, 6))

    # Équipement utilisé
    equipment_code = Column(String(100))
    equipment_serial = Column(String(100))

    # Commentaires
    comments = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(BigInteger, ForeignKey("users.id"))

    # Relations
    control = relationship("QualityControl", back_populates="lines")


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

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False)

    # Identification
    audit_number = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    audit_type = Column(Enum(AuditType), nullable=False)

    # Référentiel
    reference_standard = Column(String(200))  # ISO 9001, ISO 14001, etc.
    reference_version = Column(String(50))
    audit_scope = Column(Text)  # Périmètre de l'audit

    # Planification
    planned_date = Column(Date)
    planned_end_date = Column(Date)
    actual_date = Column(Date)
    actual_end_date = Column(Date)

    # Statut
    status = Column(Enum(AuditStatus), default=AuditStatus.PLANNED)

    # Équipe d'audit
    lead_auditor_id = Column(BigInteger, ForeignKey("users.id"))
    auditors = Column(JSON)  # Liste des auditeurs

    # Entité auditée
    audited_entity = Column(String(200))
    audited_department = Column(String(200))
    auditee_contact_id = Column(BigInteger, ForeignKey("users.id"))

    # Fournisseur (audit fournisseur)
    supplier_id = Column(BigInteger)  # Référence fournisseur (table purchase_suppliers non implémentée)

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
    closed_by_id = Column(BigInteger, ForeignKey("users.id"))

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(BigInteger, ForeignKey("users.id"))

    # Relations
    findings = relationship("AuditFinding", back_populates="audit")


class AuditFinding(Base):
    """Constat d'audit"""
    __tablename__ = "quality_audit_findings"
    __table_args__ = (
        Index("idx_finding_audit", "audit_id"),
        Index("idx_finding_severity", "severity"),
        {"schema": None},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False)
    audit_id = Column(BigInteger, ForeignKey("quality_audits.id"), nullable=False)

    # Identification
    finding_number = Column(Integer, nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)

    # Classification
    severity = Column(Enum(FindingSeverity), nullable=False)
    category = Column(String(100))  # Catégorie du constat

    # Référence
    clause_reference = Column(String(100))  # Clause de la norme
    process_reference = Column(String(100))  # Processus concerné
    evidence = Column(Text)  # Preuves

    # Risque
    risk_description = Column(Text)
    risk_level = Column(String(50))

    # CAPA
    capa_required = Column(Boolean, default=False)
    capa_id = Column(BigInteger, ForeignKey("quality_capas.id"))

    # Réponse
    auditee_response = Column(Text)
    response_date = Column(Date)

    # Suivi
    action_due_date = Column(Date)
    action_completed_date = Column(Date)
    status = Column(String(50), default="OPEN")  # OPEN, IN_PROGRESS, CLOSED

    # Vérification
    verified = Column(Boolean, default=False)
    verified_date = Column(Date)
    verified_by_id = Column(BigInteger, ForeignKey("users.id"))
    verification_comments = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(BigInteger, ForeignKey("users.id"))

    # Relations
    audit = relationship("QualityAudit", back_populates="findings")


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

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False)

    # Identification
    capa_number = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    capa_type = Column(Enum(CAPAType), nullable=False)

    # Origine
    source_type = Column(String(50))  # NC, AUDIT, CLAIM, INTERNAL, etc.
    source_reference = Column(String(100))
    source_id = Column(BigInteger)

    # Statut et priorité
    status = Column(Enum(CAPAStatus), default=CAPAStatus.DRAFT)
    priority = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL

    # Dates
    open_date = Column(Date, nullable=False)
    target_close_date = Column(Date)
    actual_close_date = Column(Date)

    # Responsabilité
    owner_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    department = Column(String(100))

    # Analyse des causes
    problem_statement = Column(Text)
    immediate_containment = Column(Text)  # Actions de confinement
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
    verified_by_id = Column(BigInteger, ForeignKey("users.id"))

    # Extension/Déploiement
    extension_required = Column(Boolean, default=False)
    extension_scope = Column(Text)
    extension_completed = Column(Boolean, default=False)

    # Clôture
    closure_comments = Column(Text)
    closed_by_id = Column(BigInteger, ForeignKey("users.id"))

    # Pièces jointes
    attachments = Column(JSON)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(BigInteger, ForeignKey("users.id"))

    # Relations
    actions = relationship("CAPAAction", back_populates="capa")


class CAPAAction(Base):
    """Action d'un CAPA"""
    __tablename__ = "quality_capa_actions"
    __table_args__ = (
        Index("idx_capa_action_capa", "capa_id"),
        Index("idx_capa_action_status", "status"),
        {"schema": None},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False)
    capa_id = Column(BigInteger, ForeignKey("quality_capas.id"), nullable=False)

    # Identification
    action_number = Column(Integer, nullable=False)
    action_type = Column(String(50), nullable=False)  # CONTAINMENT, CORRECTIVE, PREVENTIVE, VERIFICATION
    description = Column(Text, nullable=False)

    # Responsabilité
    responsible_id = Column(BigInteger, ForeignKey("users.id"))

    # Planification
    planned_date = Column(Date)
    due_date = Column(Date, nullable=False)
    completed_date = Column(Date)

    # Statut
    status = Column(String(50), default="PLANNED")  # PLANNED, IN_PROGRESS, COMPLETED, OVERDUE, CANCELLED

    # Résultat
    result = Column(Text)
    evidence = Column(Text)  # Preuves de réalisation

    # Vérification
    verification_required = Column(Boolean, default=True)
    verified = Column(Boolean, default=False)
    verified_date = Column(Date)
    verified_by_id = Column(BigInteger, ForeignKey("users.id"))
    verification_result = Column(Text)

    # Coût
    estimated_cost = Column(Numeric(15, 2))
    actual_cost = Column(Numeric(15, 2))

    # Commentaires
    comments = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(BigInteger, ForeignKey("users.id"))

    # Relations
    capa = relationship("CAPA", back_populates="actions")


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

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False)

    # Identification
    claim_number = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)

    # Client
    customer_id = Column(BigInteger, nullable=False)  # Référence client (table crm_clients non implémentée)
    customer_contact = Column(String(200))
    customer_reference = Column(String(100))  # Référence client

    # Réception
    received_date = Column(Date, nullable=False)
    received_via = Column(String(50))  # EMAIL, PHONE, LETTER, PORTAL
    received_by_id = Column(BigInteger, ForeignKey("users.id"))

    # Produit/Service concerné
    product_id = Column(BigInteger, ForeignKey("inventory_products.id"))
    order_reference = Column(String(100))
    invoice_reference = Column(String(100))
    lot_number = Column(String(100))
    quantity_affected = Column(Numeric(15, 3))

    # Classification
    claim_type = Column(String(50))  # QUALITY, DELIVERY, SERVICE, DOCUMENTATION, OTHER
    severity = Column(Enum(NonConformanceSeverity))
    priority = Column(String(20), default="MEDIUM")

    # Statut
    status = Column(Enum(ClaimStatus), default=ClaimStatus.RECEIVED)

    # Responsable
    owner_id = Column(BigInteger, ForeignKey("users.id"))

    # Investigation
    investigation_summary = Column(Text)
    root_cause = Column(Text)
    our_responsibility = Column(Boolean)  # Responsabilité établie

    # Non-conformité associée
    nc_id = Column(BigInteger, ForeignKey("quality_non_conformances.id"))

    # CAPA associé
    capa_id = Column(BigInteger, ForeignKey("quality_capas.id"))

    # Réponse
    response_due_date = Column(Date)
    response_date = Column(Date)
    response_content = Column(Text)
    response_by_id = Column(BigInteger, ForeignKey("users.id"))

    # Résolution
    resolution_type = Column(String(50))  # REPLACEMENT, CREDIT, REFUND, REPAIR, NONE
    resolution_description = Column(Text)
    resolution_date = Column(Date)

    # Coût
    claim_amount = Column(Numeric(15, 2))  # Montant réclamé
    accepted_amount = Column(Numeric(15, 2))  # Montant accepté
    cost_currency = Column(String(3), default="EUR")

    # Satisfaction client
    customer_satisfied = Column(Boolean)
    satisfaction_feedback = Column(Text)

    # Clôture
    closed_date = Column(Date)
    closed_by_id = Column(BigInteger, ForeignKey("users.id"))

    # Pièces jointes
    attachments = Column(JSON)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(BigInteger, ForeignKey("users.id"))

    # Relations
    actions = relationship("ClaimAction", back_populates="claim")


class ClaimAction(Base):
    """Action pour une réclamation client"""
    __tablename__ = "quality_claim_actions"
    __table_args__ = (
        Index("idx_claim_action_claim", "claim_id"),
        {"schema": None},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False)
    claim_id = Column(BigInteger, ForeignKey("quality_customer_claims.id"), nullable=False)

    # Action
    action_number = Column(Integer, nullable=False)
    action_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)

    # Responsabilité
    responsible_id = Column(BigInteger, ForeignKey("users.id"))

    # Planification
    due_date = Column(Date)
    completed_date = Column(Date)

    # Statut
    status = Column(String(50), default="PLANNED")

    # Résultat
    result = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(BigInteger, ForeignKey("users.id"))

    # Relations
    claim = relationship("CustomerClaim", back_populates="actions")


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

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # QUALITY, DELIVERY, COST, SAFETY, etc.

    # Formule
    formula = Column(Text)  # Description de la formule
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
    measurement_frequency = Column(String(50))  # DAILY, WEEKLY, MONTHLY, QUARTERLY

    # Source de données
    data_source = Column(String(100))
    calculation_query = Column(Text)  # SQL ou formule de calcul

    # Responsable
    owner_id = Column(BigInteger, ForeignKey("users.id"))

    # Statut
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(BigInteger, ForeignKey("users.id"))

    # Relations
    measurements = relationship("IndicatorMeasurement", back_populates="indicator")


class IndicatorMeasurement(Base):
    """Mesure d'un indicateur qualité"""
    __tablename__ = "quality_indicator_measurements"
    __table_args__ = (
        Index("idx_qim_indicator", "indicator_id"),
        Index("idx_qim_date", "measurement_date"),
        {"schema": None},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False)
    indicator_id = Column(BigInteger, ForeignKey("quality_indicators.id"), nullable=False)

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
    achievement_rate = Column(Numeric(5, 2))  # Pourcentage

    # Statut
    status = Column(String(20))  # ON_TARGET, WARNING, CRITICAL

    # Analyse
    comments = Column(Text)
    action_required = Column(Boolean, default=False)

    # Source
    source = Column(String(100))  # MANUAL, CALCULATED, IMPORTED

    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(BigInteger, ForeignKey("users.id"))

    # Relations
    indicator = relationship("QualityIndicator", back_populates="measurements")


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

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Norme/Référentiel
    standard = Column(String(100), nullable=False)  # ISO 9001, ISO 14001, etc.
    standard_version = Column(String(50))
    scope = Column(Text)  # Périmètre de certification

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
    status = Column(Enum(CertificationStatus), default=CertificationStatus.PLANNED)

    # Responsable
    manager_id = Column(BigInteger, ForeignKey("users.id"))

    # Coût
    annual_cost = Column(Numeric(15, 2))
    cost_currency = Column(String(3), default="EUR")

    # Notes
    notes = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(BigInteger, ForeignKey("users.id"))

    # Relations
    audits = relationship("CertificationAudit", back_populates="certification")


class CertificationAudit(Base):
    """Audit de certification"""
    __tablename__ = "quality_certification_audits"
    __table_args__ = (
        Index("idx_cert_audit_cert", "certification_id"),
        Index("idx_cert_audit_date", "audit_date"),
        {"schema": None},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False)
    certification_id = Column(BigInteger, ForeignKey("quality_certifications.id"), nullable=False)

    # Type d'audit
    audit_type = Column(String(50), nullable=False)  # INITIAL, SURVEILLANCE, RENEWAL, SPECIAL

    # Dates
    audit_date = Column(Date, nullable=False)
    audit_end_date = Column(Date)

    # Auditeur
    lead_auditor = Column(String(200))
    audit_team = Column(JSON)

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

    # Lien avec audit interne
    quality_audit_id = Column(BigInteger, ForeignKey("quality_audits.id"))

    # Notes
    notes = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(BigInteger, ForeignKey("users.id"))

    # Relations
    certification = relationship("Certification", back_populates="audits")
