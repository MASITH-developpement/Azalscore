"""
Modèles SQLAlchemy Risk Management - GAP-075
=============================================
"""
from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean, Date, DateTime, Enum as SQLEnum, ForeignKey, Integer,
    Numeric, String, Text, UniqueConstraint, Index, CheckConstraint
)
from app.core.types import UniversalUUID as UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ============== Énumérations ==============

class RiskCategory(str, Enum):
    """Catégorie de risque."""
    STRATEGIC = "strategic"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    COMPLIANCE = "compliance"
    TECHNOLOGY = "technology"
    SECURITY = "security"
    REPUTATION = "reputation"
    ENVIRONMENTAL = "environmental"
    LEGAL = "legal"
    PROJECT = "project"


class RiskStatus(str, Enum):
    """Statut du risque."""
    IDENTIFIED = "identified"
    ASSESSED = "assessed"
    MITIGATING = "mitigating"
    MONITORING = "monitoring"
    CLOSED = "closed"
    ACCEPTED = "accepted"
    TRANSFERRED = "transferred"

    @classmethod
    def allowed_transitions(cls) -> dict:
        return {
            cls.IDENTIFIED: [cls.ASSESSED, cls.CLOSED],
            cls.ASSESSED: [cls.MITIGATING, cls.MONITORING, cls.ACCEPTED, cls.TRANSFERRED, cls.CLOSED],
            cls.MITIGATING: [cls.MONITORING, cls.ASSESSED, cls.CLOSED],
            cls.MONITORING: [cls.MITIGATING, cls.ASSESSED, cls.CLOSED, cls.ACCEPTED],
            cls.ACCEPTED: [cls.MITIGATING, cls.MONITORING, cls.CLOSED],
            cls.TRANSFERRED: [cls.MONITORING, cls.CLOSED],
            cls.CLOSED: [],
        }


class Probability(str, Enum):
    """Probabilité de survenance."""
    RARE = "rare"  # 1
    UNLIKELY = "unlikely"  # 2
    POSSIBLE = "possible"  # 3
    LIKELY = "likely"  # 4
    ALMOST_CERTAIN = "almost_certain"  # 5

    @property
    def value_numeric(self) -> int:
        return {
            self.RARE: 1,
            self.UNLIKELY: 2,
            self.POSSIBLE: 3,
            self.LIKELY: 4,
            self.ALMOST_CERTAIN: 5,
        }[self]


class Impact(str, Enum):
    """Impact du risque."""
    NEGLIGIBLE = "negligible"  # 1
    MINOR = "minor"  # 2
    MODERATE = "moderate"  # 3
    MAJOR = "major"  # 4
    CATASTROPHIC = "catastrophic"  # 5

    @property
    def value_numeric(self) -> int:
        return {
            self.NEGLIGIBLE: 1,
            self.MINOR: 2,
            self.MODERATE: 3,
            self.MAJOR: 4,
            self.CATASTROPHIC: 5,
        }[self]


class RiskLevel(str, Enum):
    """Niveau de risque."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MitigationStrategy(str, Enum):
    """Stratégie de mitigation."""
    AVOID = "avoid"
    REDUCE = "reduce"
    TRANSFER = "transfer"
    ACCEPT = "accept"
    EXPLOIT = "exploit"


class ActionStatus(str, Enum):
    """Statut des actions."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"

    @classmethod
    def allowed_transitions(cls) -> dict:
        return {
            cls.PLANNED: [cls.IN_PROGRESS, cls.CANCELLED],
            cls.IN_PROGRESS: [cls.COMPLETED, cls.CANCELLED, cls.OVERDUE],
            cls.OVERDUE: [cls.IN_PROGRESS, cls.COMPLETED, cls.CANCELLED],
            cls.COMPLETED: [],
            cls.CANCELLED: [],
        }


class ControlType(str, Enum):
    """Type de contrôle."""
    PREVENTIVE = "preventive"
    DETECTIVE = "detective"
    CORRECTIVE = "corrective"


class ControlEffectiveness(str, Enum):
    """Efficacité du contrôle."""
    NOT_EFFECTIVE = "not_effective"
    PARTIALLY_EFFECTIVE = "partially_effective"
    EFFECTIVE = "effective"
    HIGHLY_EFFECTIVE = "highly_effective"


class IndicatorStatus(str, Enum):
    """Statut de l'indicateur."""
    GREEN = "green"
    AMBER = "amber"
    RED = "red"


class IncidentStatus(str, Enum):
    """Statut de l'incident."""
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


# ============== Modèles ==============

class RiskMatrix(Base):
    """Matrice de risques."""
    __tablename__ = "risk_matrices"

    id: Mapped[UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")

    # Configuration des échelles
    probability_scale: Mapped[int] = mapped_column(Integer, default=5)
    impact_scale: Mapped[int] = mapped_column(Integer, default=5)

    # Seuils de niveau de risque (score = probabilité x impact)
    low_threshold: Mapped[int] = mapped_column(Integer, default=4)
    medium_threshold: Mapped[int] = mapped_column(Integer, default=9)
    high_threshold: Mapped[int] = mapped_column(Integer, default=15)

    # Labels personnalisés
    probability_labels: Mapped[dict] = mapped_column(JSONB, default=dict)
    impact_labels: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Couleurs
    color_low: Mapped[str] = mapped_column(String(20), default="#4CAF50")
    color_medium: Mapped[str] = mapped_column(String(20), default="#FFC107")
    color_high: Mapped[str] = mapped_column(String(20), default="#FF9800")
    color_critical: Mapped[str] = mapped_column(String(20), default="#F44336")

    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_risk_matrix_tenant_code"),
        Index("ix_risk_matrix_tenant_active", "tenant_id", "is_active"),
    )


class Risk(Base):
    """Risque identifié."""
    __tablename__ = "risks"

    id: Mapped[UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(), nullable=False, index=True
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")

    category: Mapped[RiskCategory] = mapped_column(
        SQLEnum(RiskCategory, name="risk_category"),
        default=RiskCategory.OPERATIONAL
    )
    status: Mapped[RiskStatus] = mapped_column(
        SQLEnum(RiskStatus, name="risk_status"),
        default=RiskStatus.IDENTIFIED
    )

    # Matrice de référence
    matrix_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(), ForeignKey("risk_matrices.id"), nullable=True
    )

    # Évaluation inhérente (avant contrôles)
    inherent_probability: Mapped[Probability] = mapped_column(
        SQLEnum(Probability, name="risk_probability"),
        default=Probability.POSSIBLE
    )
    inherent_impact: Mapped[Impact] = mapped_column(
        SQLEnum(Impact, name="risk_impact"),
        default=Impact.MODERATE
    )
    inherent_score: Mapped[int] = mapped_column(Integer, default=0)
    inherent_level: Mapped[RiskLevel] = mapped_column(
        SQLEnum(RiskLevel, name="risk_level"),
        default=RiskLevel.MEDIUM
    )

    # Évaluation résiduelle (après contrôles)
    residual_probability: Mapped[Optional[Probability]] = mapped_column(
        SQLEnum(Probability, name="risk_probability", create_type=False),
        nullable=True
    )
    residual_impact: Mapped[Optional[Impact]] = mapped_column(
        SQLEnum(Impact, name="risk_impact", create_type=False),
        nullable=True
    )
    residual_score: Mapped[int] = mapped_column(Integer, default=0)
    residual_level: Mapped[Optional[RiskLevel]] = mapped_column(
        SQLEnum(RiskLevel, name="risk_level", create_type=False),
        nullable=True
    )

    # Cible (niveau de risque acceptable)
    target_probability: Mapped[Optional[Probability]] = mapped_column(
        SQLEnum(Probability, name="risk_probability", create_type=False),
        nullable=True
    )
    target_impact: Mapped[Optional[Impact]] = mapped_column(
        SQLEnum(Impact, name="risk_impact", create_type=False),
        nullable=True
    )
    target_level: Mapped[Optional[RiskLevel]] = mapped_column(
        SQLEnum(RiskLevel, name="risk_level", create_type=False),
        nullable=True
    )

    # Impact financier estimé
    financial_impact_min: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0")
    )
    financial_impact_max: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0")
    )
    financial_impact_expected: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0")
    )

    # Propriétaire et responsables
    owner_id: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    reviewer_id: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    department_id: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)

    # Dates
    identified_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_assessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_review_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Contexte
    causes: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    consequences: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    affected_objectives: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    affected_processes: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)

    # Relations
    related_risk_ids: Mapped[List[UUID]] = mapped_column(ARRAY(UUID()), default=list)
    parent_risk_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(), ForeignKey("risks.id"), nullable=True
    )

    # Stratégie
    mitigation_strategy: Mapped[MitigationStrategy] = mapped_column(
        SQLEnum(MitigationStrategy, name="mitigation_strategy"),
        default=MitigationStrategy.REDUCE
    )

    # Tags et métadonnées
    tags: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    extra_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relations
    matrix = relationship("RiskMatrix", foreign_keys=[matrix_id])
    parent_risk = relationship("Risk", remote_side=[id], foreign_keys=[parent_risk_id])
    controls = relationship("Control", back_populates="risk", cascade="all, delete-orphan")
    actions = relationship("MitigationAction", back_populates="risk", cascade="all, delete-orphan")
    indicators = relationship("RiskIndicator", back_populates="risk", cascade="all, delete-orphan")
    assessments = relationship("RiskAssessment", back_populates="risk", cascade="all, delete-orphan")
    incidents = relationship("RiskIncident", back_populates="risk")

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_risk_tenant_code"),
        Index("ix_risk_tenant_status", "tenant_id", "status"),
        Index("ix_risk_tenant_category", "tenant_id", "category"),
        Index("ix_risk_tenant_level", "tenant_id", "inherent_level"),
        Index("ix_risk_tenant_owner", "tenant_id", "owner_id"),
    )


class Control(Base):
    """Contrôle de risque."""
    __tablename__ = "risk_controls"

    id: Mapped[UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(), nullable=False, index=True
    )

    risk_id: Mapped[UUID] = mapped_column(
        UUID(), ForeignKey("risks.id"), nullable=False
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")

    control_type: Mapped[ControlType] = mapped_column(
        SQLEnum(ControlType, name="control_type"),
        default=ControlType.PREVENTIVE
    )

    # Évaluation
    effectiveness: Mapped[ControlEffectiveness] = mapped_column(
        SQLEnum(ControlEffectiveness, name="control_effectiveness"),
        default=ControlEffectiveness.EFFECTIVE
    )
    cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))

    # Responsables
    owner_id: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    operator_id: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)

    # Fréquence d'exécution
    frequency: Mapped[str] = mapped_column(String(50), default="")
    last_executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_execution_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Documentation
    procedure: Mapped[str] = mapped_column(Text, default="")
    evidence_required: Mapped[str] = mapped_column(Text, default="")
    evidence_links: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)

    # Statut
    is_automated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relations
    risk = relationship("Risk", back_populates="controls")

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_control_tenant_code"),
        Index("ix_control_risk", "risk_id"),
        Index("ix_control_tenant_type", "tenant_id", "control_type"),
    )


class MitigationAction(Base):
    """Action de mitigation."""
    __tablename__ = "risk_mitigation_actions"

    id: Mapped[UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(), nullable=False, index=True
    )

    risk_id: Mapped[UUID] = mapped_column(
        UUID(), ForeignKey("risks.id"), nullable=False
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")

    status: Mapped[ActionStatus] = mapped_column(
        SQLEnum(ActionStatus, name="action_status"),
        default=ActionStatus.PLANNED
    )

    # Responsable
    assignee_id: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)

    # Planification
    planned_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    planned_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Progression
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)

    # Coût
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    actual_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")

    # Impact attendu sur les scores
    expected_probability_reduction: Mapped[int] = mapped_column(Integer, default=0)
    expected_impact_reduction: Mapped[int] = mapped_column(Integer, default=0)

    # Priorité
    priority: Mapped[int] = mapped_column(Integer, default=0)

    # Commentaires
    notes: Mapped[str] = mapped_column(Text, default="")

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relations
    risk = relationship("Risk", back_populates="actions")

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_action_tenant_code"),
        Index("ix_action_risk", "risk_id"),
        Index("ix_action_tenant_status", "tenant_id", "status"),
        Index("ix_action_tenant_assignee", "tenant_id", "assignee_id"),
        CheckConstraint("progress_percent >= 0 AND progress_percent <= 100", name="ck_action_progress"),
    )


class RiskIndicator(Base):
    """Indicateur de risque (KRI)."""
    __tablename__ = "risk_indicators"

    id: Mapped[UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(), nullable=False, index=True
    )

    risk_id: Mapped[UUID] = mapped_column(
        UUID(), ForeignKey("risks.id"), nullable=False
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")

    # Métrique
    metric_type: Mapped[str] = mapped_column(String(50), default="count")
    unit: Mapped[str] = mapped_column(String(50), default="")
    current_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))

    # Seuils
    green_threshold: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    amber_threshold: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    red_threshold: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))

    # Direction (higher_is_worse = true si valeur haute = mauvais)
    higher_is_worse: Mapped[bool] = mapped_column(Boolean, default=True)

    # Statut actuel
    current_status: Mapped[IndicatorStatus] = mapped_column(
        SQLEnum(IndicatorStatus, name="indicator_status"),
        default=IndicatorStatus.GREEN
    )

    # Fréquence de mesure
    measurement_frequency: Mapped[str] = mapped_column(String(50), default="monthly")
    last_measured_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Historique des valeurs
    historical_values: Mapped[List[dict]] = mapped_column(JSONB, default=list)

    # Source de données
    data_source: Mapped[str] = mapped_column(String(200), default="")
    is_automated: Mapped[bool] = mapped_column(Boolean, default=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relations
    risk = relationship("Risk", back_populates="indicators")

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_indicator_tenant_code"),
        Index("ix_indicator_risk", "risk_id"),
        Index("ix_indicator_tenant_status", "tenant_id", "current_status"),
    )


class RiskAssessment(Base):
    """Évaluation de risque."""
    __tablename__ = "risk_assessments"

    id: Mapped[UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(), nullable=False, index=True
    )

    risk_id: Mapped[UUID] = mapped_column(
        UUID(), ForeignKey("risks.id"), nullable=False
    )

    assessment_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    assessor_id: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)

    # Évaluation
    probability: Mapped[Probability] = mapped_column(
        SQLEnum(Probability, name="risk_probability", create_type=False),
        default=Probability.POSSIBLE
    )
    impact: Mapped[Impact] = mapped_column(
        SQLEnum(Impact, name="risk_impact", create_type=False),
        default=Impact.MODERATE
    )
    score: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[RiskLevel] = mapped_column(
        SQLEnum(RiskLevel, name="risk_level", create_type=False),
        default=RiskLevel.MEDIUM
    )

    # Type d'évaluation
    assessment_type: Mapped[str] = mapped_column(String(50), default="periodic")
    is_residual: Mapped[bool] = mapped_column(Boolean, default=False)
    trigger_event: Mapped[str] = mapped_column(Text, default="")

    # Justification
    rationale: Mapped[str] = mapped_column(Text, default="")
    supporting_evidence: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)

    # Contrôles évalués
    controls_evaluated: Mapped[List[UUID]] = mapped_column(ARRAY(UUID()), default=list)
    control_effectiveness_summary: Mapped[str] = mapped_column(Text, default="")

    # Validation
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    validated_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)

    # Relations
    risk = relationship("Risk", back_populates="assessments")

    __table_args__ = (
        Index("ix_assessment_risk", "risk_id"),
        Index("ix_assessment_tenant_date", "tenant_id", "assessment_date"),
        Index("ix_assessment_tenant_type", "tenant_id", "assessment_type"),
    )


class RiskIncident(Base):
    """Incident lié à un risque."""
    __tablename__ = "risk_incidents"

    id: Mapped[UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(), nullable=False, index=True
    )

    risk_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(), ForeignKey("risks.id"), nullable=True
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")

    status: Mapped[IncidentStatus] = mapped_column(
        SQLEnum(IncidentStatus, name="incident_status"),
        default=IncidentStatus.OPEN
    )

    # Dates
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    detected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Impact réel
    actual_impact: Mapped[Impact] = mapped_column(
        SQLEnum(Impact, name="risk_impact", create_type=False),
        default=Impact.MODERATE
    )
    financial_loss: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    affected_parties: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)

    # Analyse
    root_cause: Mapped[str] = mapped_column(Text, default="")
    contributing_factors: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    control_failures: Mapped[List[UUID]] = mapped_column(ARRAY(UUID()), default=list)

    # Actions correctives
    corrective_action_ids: Mapped[List[UUID]] = mapped_column(ARRAY(UUID()), default=list)

    # Leçons apprises
    lessons_learned: Mapped[str] = mapped_column(Text, default="")

    # Responsable
    reporter_id: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    owner_id: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relations
    risk = relationship("Risk", back_populates="incidents")

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_incident_tenant_code"),
        Index("ix_incident_risk", "risk_id"),
        Index("ix_incident_tenant_status", "tenant_id", "status"),
        Index("ix_incident_tenant_date", "tenant_id", "occurred_at"),
    )
