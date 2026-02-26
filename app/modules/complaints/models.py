"""
AZALS MODULE - Complaints (Reclamations Clients)
=================================================

Modeles SQLAlchemy pour le systeme de gestion des reclamations clients.
Inspire des meilleures pratiques de:
- Microsoft Dynamics 365 Customer Service (Case Management)
- Odoo Helpdesk (Workflow & SLA)
- Sage X3 (Alerts & Workflow)
- Axonaut (Ticketing SAV)

Conformite:
- ISO 10002 (Satisfaction client - Traitement des reclamations)
- RGPD (Protection des donnees personnelles)
- Mediation de la consommation (Code de la consommation)

Architecture multi-tenant avec isolation stricte par tenant_id.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.types import UniversalUUID
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class ComplaintChannel(str, PyEnum):
    """Canal de reception de la reclamation."""
    EMAIL = "email"
    PHONE = "phone"
    WEB_FORM = "web_form"
    CHAT = "chat"
    SOCIAL_MEDIA = "social_media"
    LETTER = "letter"
    IN_PERSON = "in_person"
    MOBILE_APP = "mobile_app"
    API = "api"


class ComplaintCategory(str, PyEnum):
    """Categorie de reclamation."""
    PRODUCT_QUALITY = "product_quality"
    PRODUCT_DEFECT = "product_defect"
    DELIVERY = "delivery"
    DELIVERY_DELAY = "delivery_delay"
    BILLING = "billing"
    PRICING = "pricing"
    SERVICE = "service"
    COMMUNICATION = "communication"
    WEBSITE = "website"
    CONTRACT = "contract"
    RETURNS = "returns"
    WARRANTY = "warranty"
    GDPR = "gdpr"
    FRAUD = "fraud"
    OTHER = "other"


class ComplaintPriority(str, PyEnum):
    """Priorite de la reclamation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class ComplaintStatus(str, PyEnum):
    """Statut de la reclamation (workflow)."""
    DRAFT = "draft"
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    PENDING_INFO = "pending_info"
    PENDING_CUSTOMER = "pending_customer"
    UNDER_INVESTIGATION = "under_investigation"
    ESCALATED = "escalated"
    PENDING_APPROVAL = "pending_approval"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"
    CANCELLED = "cancelled"


class ResolutionType(str, PyEnum):
    """Type de resolution."""
    EXPLANATION = "explanation"
    REFUND = "refund"
    PARTIAL_REFUND = "partial_refund"
    REPLACEMENT = "replacement"
    REPAIR = "repair"
    CREDIT_NOTE = "credit_note"
    COMMERCIAL_GESTURE = "commercial_gesture"
    VOUCHER = "voucher"
    COMPENSATION = "compensation"
    APOLOGY = "apology"
    NO_ACTION = "no_action"
    ESCALATED_EXTERNAL = "escalated_external"


class EscalationLevel(str, PyEnum):
    """Niveau d'escalade."""
    LEVEL_1 = "level_1"  # Agent
    LEVEL_2 = "level_2"  # Superviseur
    LEVEL_3 = "level_3"  # Manager
    LEVEL_4 = "level_4"  # Direction
    LEGAL = "legal"
    MEDIATOR = "mediator"
    EXTERNAL = "external"


class SatisfactionRating(str, PyEnum):
    """Note de satisfaction client."""
    VERY_DISSATISFIED = "very_dissatisfied"
    DISSATISFIED = "dissatisfied"
    NEUTRAL = "neutral"
    SATISFIED = "satisfied"
    VERY_SATISFIED = "very_satisfied"


class ActionType(str, PyEnum):
    """Type d'action corrective."""
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    INVESTIGATION = "investigation"
    REFUND_PROCESS = "refund_process"
    REPLACEMENT_ORDER = "replacement_order"
    INTERNAL_REVIEW = "internal_review"
    PROCESS_IMPROVEMENT = "process_improvement"
    TRAINING = "training"
    OTHER = "other"


class RootCauseCategory(str, PyEnum):
    """Categorie de cause racine."""
    PRODUCT = "product"
    PROCESS = "process"
    PEOPLE = "people"
    SYSTEM = "system"
    SUPPLIER = "supplier"
    COMMUNICATION = "communication"
    EXTERNAL = "external"
    UNKNOWN = "unknown"


# ============================================================================
# COMPLAINT CATEGORY (Configuration)
# ============================================================================

class ComplaintCategoryConfig(Base):
    """Configuration des categories de reclamation."""
    __tablename__ = "complaints_category_config"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Hierarchie
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UniversalUUID(), ForeignKey("complaints_category_config.id")
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(String(50))

    # Configuration par defaut
    default_priority: Mapped[str] = mapped_column(
        Enum(ComplaintPriority), default=ComplaintPriority.MEDIUM
    )
    default_team_id: Mapped[uuid.UUID | None] = mapped_column(
        UniversalUUID(), ForeignKey("complaints_teams.id")
    )
    sla_policy_id: Mapped[uuid.UUID | None] = mapped_column(
        UniversalUUID(), ForeignKey("complaints_sla_policies.id")
    )

    # Options
    require_order: Mapped[bool] = mapped_column(Boolean, default=False)
    require_product: Mapped[bool] = mapped_column(Boolean, default=False)
    require_invoice: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_assign: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Audit
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relations
    parent = relationship("ComplaintCategoryConfig", remote_side=[id], backref="children")
    complaints = relationship("Complaint", back_populates="category_config")

    __table_args__ = (
        Index("idx_complaint_cat_tenant", "tenant_id"),
        Index("idx_complaint_cat_code", "tenant_id", "code", unique=True),
        Index("idx_complaint_cat_active", "tenant_id", "is_active"),
    )


# ============================================================================
# COMPLAINT TEAM
# ============================================================================

class ComplaintTeam(Base):
    """Equipe de traitement des reclamations."""
    __tablename__ = "complaints_teams"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(String(255))

    # Manager
    manager_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())

    # Configuration
    default_sla_policy_id: Mapped[uuid.UUID | None] = mapped_column(
        UniversalUUID(), ForeignKey("complaints_sla_policies.id")
    )
    auto_assign_method: Mapped[str] = mapped_column(
        String(30), default="round_robin"
    )  # round_robin, least_busy, random, manual
    max_complaints_per_agent: Mapped[int] = mapped_column(Integer, default=25)

    # Horaires
    working_hours: Mapped[dict | None] = mapped_column(JSON)
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Paris")

    # Audit
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relations
    members = relationship("ComplaintAgent", back_populates="team")
    complaints = relationship("Complaint", back_populates="team")

    __table_args__ = (
        Index("idx_complaint_team_tenant", "tenant_id"),
        Index("idx_complaint_team_active", "tenant_id", "is_active"),
    )


# ============================================================================
# COMPLAINT AGENT
# ============================================================================

class ComplaintAgent(Base):
    """Agent de traitement des reclamations."""
    __tablename__ = "complaints_agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Lien utilisateur
    user_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=False, index=True)
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UniversalUUID(), ForeignKey("complaints_teams.id")
    )

    # Profil
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    signature: Mapped[str | None] = mapped_column(Text)

    # Competences
    skills: Mapped[dict | None] = mapped_column(JSON)  # ["billing", "technical", "legal"]
    categories: Mapped[dict | None] = mapped_column(JSON)  # Categories qu'il peut traiter
    languages: Mapped[dict | None] = mapped_column(JSON)  # ["fr", "en"]
    max_escalation_level: Mapped[str] = mapped_column(
        Enum(EscalationLevel), default=EscalationLevel.LEVEL_2
    )

    # Permissions
    can_assign: Mapped[bool] = mapped_column(Boolean, default=True)
    can_escalate: Mapped[bool] = mapped_column(Boolean, default=True)
    can_resolve: Mapped[bool] = mapped_column(Boolean, default=True)
    can_close: Mapped[bool] = mapped_column(Boolean, default=False)
    can_approve_compensation: Mapped[bool] = mapped_column(Boolean, default=False)
    max_compensation_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0")
    )
    can_view_all: Mapped[bool] = mapped_column(Boolean, default=False)
    is_supervisor: Mapped[bool] = mapped_column(Boolean, default=False)

    # Statut
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    current_load: Mapped[int] = mapped_column(Integer, default=0)
    last_assigned_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Statistiques
    complaints_assigned: Mapped[int] = mapped_column(Integer, default=0)
    complaints_resolved: Mapped[int] = mapped_column(Integer, default=0)
    avg_resolution_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    satisfaction_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0"))

    # Audit
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relations
    team = relationship("ComplaintTeam", back_populates="members")
    assigned_complaints = relationship(
        "Complaint", back_populates="assigned_agent", foreign_keys="Complaint.assigned_to_id"
    )

    __table_args__ = (
        Index("idx_complaint_agent_tenant", "tenant_id"),
        Index("idx_complaint_agent_user", "tenant_id", "user_id", unique=True),
        Index("idx_complaint_agent_team", "team_id"),
        Index("idx_complaint_agent_available", "tenant_id", "is_available", "is_active"),
    )


# ============================================================================
# SLA POLICY
# ============================================================================

class ComplaintSLAPolicy(Base):
    """Politique SLA pour les reclamations."""
    __tablename__ = "complaints_sla_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Delais d'accuse de reception (en heures)
    ack_hours_low: Mapped[int] = mapped_column(Integer, default=48)
    ack_hours_medium: Mapped[int] = mapped_column(Integer, default=24)
    ack_hours_high: Mapped[int] = mapped_column(Integer, default=4)
    ack_hours_urgent: Mapped[int] = mapped_column(Integer, default=2)
    ack_hours_critical: Mapped[int] = mapped_column(Integer, default=1)

    # Delais de resolution (en heures)
    resolution_hours_low: Mapped[int] = mapped_column(Integer, default=240)  # 10 jours
    resolution_hours_medium: Mapped[int] = mapped_column(Integer, default=120)  # 5 jours
    resolution_hours_high: Mapped[int] = mapped_column(Integer, default=48)
    resolution_hours_urgent: Mapped[int] = mapped_column(Integer, default=24)
    resolution_hours_critical: Mapped[int] = mapped_column(Integer, default=8)

    # Delais d'escalade automatique (en heures)
    escalation_hours_low: Mapped[int] = mapped_column(Integer, default=168)  # 7 jours
    escalation_hours_medium: Mapped[int] = mapped_column(Integer, default=72)
    escalation_hours_high: Mapped[int] = mapped_column(Integer, default=24)
    escalation_hours_urgent: Mapped[int] = mapped_column(Integer, default=8)
    escalation_hours_critical: Mapped[int] = mapped_column(Integer, default=2)

    # Configuration
    business_hours_only: Mapped[bool] = mapped_column(Boolean, default=True)
    working_hours: Mapped[dict | None] = mapped_column(JSON)
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Paris")
    holidays: Mapped[dict | None] = mapped_column(JSON)

    # Escalade
    auto_escalation_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    escalation_rules: Mapped[dict | None] = mapped_column(JSON)

    # Notifications
    notify_on_breach: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_before_breach_hours: Mapped[int] = mapped_column(Integer, default=4)

    # Audit
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    version: Mapped[int] = mapped_column(Integer, default=1)

    __table_args__ = (
        Index("idx_complaint_sla_tenant", "tenant_id"),
        Index("idx_complaint_sla_active", "tenant_id", "is_active"),
    )


# ============================================================================
# COMPLAINT (Main Entity)
# ============================================================================

class Complaint(Base):
    """Reclamation client."""
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    reference: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    # Classification
    category: Mapped[str] = mapped_column(Enum(ComplaintCategory), default=ComplaintCategory.OTHER)
    category_config_id: Mapped[uuid.UUID | None] = mapped_column(
        UniversalUUID(), ForeignKey("complaints_category_config.id")
    )
    priority: Mapped[str] = mapped_column(Enum(ComplaintPriority), default=ComplaintPriority.MEDIUM)
    status: Mapped[str] = mapped_column(Enum(ComplaintStatus), default=ComplaintStatus.NEW)

    # Canal
    channel: Mapped[str] = mapped_column(Enum(ComplaintChannel), default=ComplaintChannel.EMAIL)
    original_message_id: Mapped[str | None] = mapped_column(String(255))

    # Contenu
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    original_language: Mapped[str] = mapped_column(String(10), default="fr")

    # Client
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID(), index=True)
    customer_name: Mapped[str | None] = mapped_column(String(255))
    customer_email: Mapped[str | None] = mapped_column(String(255), index=True)
    customer_phone: Mapped[str | None] = mapped_column(String(50))
    customer_company: Mapped[str | None] = mapped_column(String(255))
    customer_account_number: Mapped[str | None] = mapped_column(String(50))
    is_vip_customer: Mapped[bool] = mapped_column(Boolean, default=False)

    # References metier
    order_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    order_reference: Mapped[str | None] = mapped_column(String(100))
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    invoice_reference: Mapped[str | None] = mapped_column(String(100))
    product_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    product_reference: Mapped[str | None] = mapped_column(String(100))
    product_name: Mapped[str | None] = mapped_column(String(255))
    contract_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())

    # Montants
    disputed_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")

    # Assignation
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UniversalUUID(), ForeignKey("complaints_teams.id")
    )
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        UniversalUUID(), ForeignKey("complaints_agents.id")
    )
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime)

    # SLA
    sla_policy_id: Mapped[uuid.UUID | None] = mapped_column(
        UniversalUUID(), ForeignKey("complaints_sla_policies.id")
    )
    acknowledgment_due: Mapped[datetime | None] = mapped_column(DateTime)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime)
    acknowledgment_breached: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution_due: Mapped[datetime | None] = mapped_column(DateTime)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    resolution_breached: Mapped[bool] = mapped_column(Boolean, default=False)
    escalation_due: Mapped[datetime | None] = mapped_column(DateTime)

    # Escalade
    current_escalation_level: Mapped[str] = mapped_column(
        Enum(EscalationLevel), default=EscalationLevel.LEVEL_1
    )
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime)
    escalation_count: Mapped[int] = mapped_column(Integer, default=0)

    # Resolution
    resolution_type: Mapped[str | None] = mapped_column(Enum(ResolutionType))
    resolution_summary: Mapped[str | None] = mapped_column(Text)
    compensation_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    compensation_type: Mapped[str | None] = mapped_column(String(50))
    credit_note_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    refund_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())

    # Analyse
    root_cause_category: Mapped[str | None] = mapped_column(Enum(RootCauseCategory))
    root_cause_description: Mapped[str | None] = mapped_column(Text)
    sentiment: Mapped[str | None] = mapped_column(String(20))
    ai_analysis: Mapped[dict | None] = mapped_column(JSON)

    # Satisfaction
    satisfaction_rating: Mapped[str | None] = mapped_column(Enum(SatisfactionRating))
    satisfaction_comment: Mapped[str | None] = mapped_column(Text)
    satisfaction_submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    nps_score: Mapped[int | None] = mapped_column(Integer)

    # Tags et metadata
    tags: Mapped[dict | None] = mapped_column(JSON)
    custom_fields: Mapped[dict | None] = mapped_column(JSON)
    source_system: Mapped[str | None] = mapped_column(String(50))

    # Liens
    parent_complaint_id: Mapped[uuid.UUID | None] = mapped_column(
        UniversalUUID(), ForeignKey("complaints.id")
    )
    merged_into_id: Mapped[uuid.UUID | None] = mapped_column(
        UniversalUUID(), ForeignKey("complaints.id")
    )

    # Compteurs
    exchange_count: Mapped[int] = mapped_column(Integer, default=0)
    internal_note_count: Mapped[int] = mapped_column(Integer, default=0)
    attachment_count: Mapped[int] = mapped_column(Integer, default=0)

    # Dates
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)
    reopened_at: Mapped[datetime | None] = mapped_column(DateTime)
    reopen_count: Mapped[int] = mapped_column(Integer, default=0)

    # Audit complet
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relations
    category_config = relationship("ComplaintCategoryConfig", back_populates="complaints")
    team = relationship("ComplaintTeam", back_populates="complaints")
    assigned_agent = relationship(
        "ComplaintAgent", back_populates="assigned_complaints", foreign_keys=[assigned_to_id]
    )
    exchanges = relationship(
        "ComplaintExchange", back_populates="complaint", cascade="all, delete-orphan"
    )
    attachments = relationship(
        "ComplaintAttachment", back_populates="complaint", cascade="all, delete-orphan"
    )
    actions = relationship(
        "ComplaintAction", back_populates="complaint", cascade="all, delete-orphan"
    )
    escalations = relationship(
        "ComplaintEscalation", back_populates="complaint", cascade="all, delete-orphan"
    )
    history = relationship(
        "ComplaintHistory", back_populates="complaint", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_complaint_tenant", "tenant_id"),
        Index("idx_complaint_ref", "reference"),
        Index("idx_complaint_status", "tenant_id", "status"),
        Index("idx_complaint_priority", "tenant_id", "priority"),
        Index("idx_complaint_customer", "tenant_id", "customer_id"),
        Index("idx_complaint_customer_email", "tenant_id", "customer_email"),
        Index("idx_complaint_assigned", "tenant_id", "assigned_to_id"),
        Index("idx_complaint_team", "tenant_id", "team_id"),
        Index("idx_complaint_sla_breach", "tenant_id", "resolution_breached"),
        Index("idx_complaint_created", "tenant_id", "created_at"),
        Index("idx_complaint_category", "tenant_id", "category"),
        Index("idx_complaint_deleted", "tenant_id", "is_deleted"),
    )


# ============================================================================
# COMPLAINT EXCHANGE
# ============================================================================

class ComplaintExchange(Base):
    """Echange/communication sur une reclamation."""
    __tablename__ = "complaints_exchanges"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), ForeignKey("complaints.id"), nullable=False
    )

    # Auteur
    author_type: Mapped[str] = mapped_column(String(20), nullable=False)  # agent, customer, system
    author_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    author_name: Mapped[str | None] = mapped_column(String(255))
    author_email: Mapped[str | None] = mapped_column(String(255))

    # Contenu
    subject: Mapped[str | None] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    body_html: Mapped[str | None] = mapped_column(Text)

    # Type
    exchange_type: Mapped[str] = mapped_column(String(30), default="reply")
    # reply, note, email_in, email_out, call, chat
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False)
    is_first_response: Mapped[bool] = mapped_column(Boolean, default=False)

    # Email
    message_id: Mapped[str | None] = mapped_column(String(255))
    in_reply_to: Mapped[str | None] = mapped_column(String(255))
    cc_emails: Mapped[dict | None] = mapped_column(JSON)
    bcc_emails: Mapped[dict | None] = mapped_column(JSON)

    # Canal
    channel: Mapped[str | None] = mapped_column(Enum(ComplaintChannel))
    call_duration_seconds: Mapped[int | None] = mapped_column(Integer)

    # Sentiment
    sentiment: Mapped[str | None] = mapped_column(String(20))

    # Audit
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    complaint = relationship("Complaint", back_populates="exchanges")
    attachments = relationship("ComplaintAttachment", back_populates="exchange")

    __table_args__ = (
        Index("idx_exchange_tenant", "tenant_id"),
        Index("idx_exchange_complaint", "complaint_id"),
        Index("idx_exchange_type", "tenant_id", "exchange_type"),
    )


# ============================================================================
# COMPLAINT ATTACHMENT
# ============================================================================

class ComplaintAttachment(Base):
    """Piece jointe."""
    __tablename__ = "complaints_attachments"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), ForeignKey("complaints.id"), nullable=False
    )
    exchange_id: Mapped[uuid.UUID | None] = mapped_column(
        UniversalUUID(), ForeignKey("complaints_exchanges.id")
    )

    # Fichier
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    file_path: Mapped[str | None] = mapped_column(String(500))
    file_url: Mapped[str | None] = mapped_column(String(500))
    file_size: Mapped[int | None] = mapped_column(Integer)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    checksum: Mapped[str | None] = mapped_column(String(64))

    # Description
    description: Mapped[str | None] = mapped_column(Text)
    is_evidence: Mapped[bool] = mapped_column(Boolean, default=False)

    # Upload
    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    uploaded_by_name: Mapped[str | None] = mapped_column(String(255))

    # Audit
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    complaint = relationship("Complaint", back_populates="attachments")
    exchange = relationship("ComplaintExchange", back_populates="attachments")

    __table_args__ = (
        Index("idx_attachment_tenant", "tenant_id"),
        Index("idx_attachment_complaint", "complaint_id"),
    )


# ============================================================================
# COMPLAINT ACTION
# ============================================================================

class ComplaintAction(Base):
    """Action corrective ou tache liee a une reclamation."""
    __tablename__ = "complaints_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), ForeignKey("complaints.id"), nullable=False
    )

    # Type et description
    action_type: Mapped[str] = mapped_column(Enum(ActionType), default=ActionType.OTHER)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Assignation
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    assigned_to_name: Mapped[str | None] = mapped_column(String(255))
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Echeances
    due_date: Mapped[datetime | None] = mapped_column(DateTime)
    reminder_date: Mapped[datetime | None] = mapped_column(DateTime)

    # Statut
    status: Mapped[str] = mapped_column(String(30), default="pending")
    # pending, in_progress, completed, cancelled
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_by_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    completion_notes: Mapped[str | None] = mapped_column(Text)

    # Resultat
    outcome: Mapped[str | None] = mapped_column(String(30))  # success, partial, failed
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False)

    # Audit
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relations
    complaint = relationship("Complaint", back_populates="actions")

    __table_args__ = (
        Index("idx_action_tenant", "tenant_id"),
        Index("idx_action_complaint", "complaint_id"),
        Index("idx_action_status", "tenant_id", "status"),
        Index("idx_action_due", "tenant_id", "due_date"),
    )


# ============================================================================
# COMPLAINT ESCALATION
# ============================================================================

class ComplaintEscalation(Base):
    """Historique des escalades."""
    __tablename__ = "complaints_escalations"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), ForeignKey("complaints.id"), nullable=False
    )

    # Niveau
    from_level: Mapped[str] = mapped_column(Enum(EscalationLevel))
    to_level: Mapped[str] = mapped_column(Enum(EscalationLevel))

    # Raison
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    is_automatic: Mapped[bool] = mapped_column(Boolean, default=False)

    # Escalade par
    escalated_by_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    escalated_by_name: Mapped[str | None] = mapped_column(String(255))

    # Assignation
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    assigned_to_name: Mapped[str | None] = mapped_column(String(255))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Resolution
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    resolution_notes: Mapped[str | None] = mapped_column(Text)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    complaint = relationship("Complaint", back_populates="escalations")

    __table_args__ = (
        Index("idx_escalation_tenant", "tenant_id"),
        Index("idx_escalation_complaint", "complaint_id"),
        Index("idx_escalation_level", "tenant_id", "to_level"),
    )


# ============================================================================
# COMPLAINT HISTORY
# ============================================================================

class ComplaintHistory(Base):
    """Historique des changements (audit trail)."""
    __tablename__ = "complaints_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), ForeignKey("complaints.id"), nullable=False
    )

    # Action
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    # created, updated, status_changed, assigned, escalated, resolved, closed, reopened, etc.

    # Changement
    field_name: Mapped[str | None] = mapped_column(String(100))
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)

    # Acteur
    actor_type: Mapped[str] = mapped_column(String(20), default="user")
    # user, system, automation, api
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    actor_name: Mapped[str | None] = mapped_column(String(255))
    actor_ip: Mapped[str | None] = mapped_column(String(45))

    # Contexte
    context: Mapped[dict | None] = mapped_column(JSON)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    complaint = relationship("Complaint", back_populates="history")

    __table_args__ = (
        Index("idx_history_tenant", "tenant_id"),
        Index("idx_history_complaint", "complaint_id"),
        Index("idx_history_action", "tenant_id", "action"),
        Index("idx_history_created", "tenant_id", "created_at"),
    )


# ============================================================================
# COMPLAINT TEMPLATE
# ============================================================================

class ComplaintTemplate(Base):
    """Modele de reponse pre-enregistree."""
    __tablename__ = "complaints_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Categorie
    category: Mapped[str | None] = mapped_column(Enum(ComplaintCategory))
    template_type: Mapped[str] = mapped_column(String(30), default="response")
    # response, acknowledgment, resolution, escalation

    # Contenu
    subject: Mapped[str | None] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    body_html: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(10), default="fr")

    # Variables disponibles
    variables: Mapped[dict | None] = mapped_column(JSON)

    # Scope
    scope: Mapped[str] = mapped_column(String(20), default="global")  # personal, team, global
    team_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    owner_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())

    # Stats
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Audit
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    version: Mapped[int] = mapped_column(Integer, default=1)

    __table_args__ = (
        Index("idx_template_tenant", "tenant_id"),
        Index("idx_template_code", "tenant_id", "code", unique=True),
        Index("idx_template_type", "tenant_id", "template_type"),
        Index("idx_template_category", "tenant_id", "category"),
    )


# ============================================================================
# COMPLAINT AUTOMATION RULE
# ============================================================================

class ComplaintAutomationRule(Base):
    """Regle d'automatisation."""
    __tablename__ = "complaints_automation_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Declencheur
    trigger_event: Mapped[str] = mapped_column(String(50), nullable=False)
    # complaint_created, complaint_updated, status_changed, sla_warning, sla_breached
    trigger_conditions: Mapped[dict | None] = mapped_column(JSON)

    # Actions
    actions: Mapped[dict] = mapped_column(JSON, nullable=False)
    # [{type: "assign", params: {...}}, {type: "notify", params: {...}}]

    # Priorite
    priority: Mapped[int] = mapped_column(Integer, default=0)
    stop_processing: Mapped[bool] = mapped_column(Boolean, default=False)

    # Stats
    execution_count: Mapped[int] = mapped_column(Integer, default=0)
    last_executed_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_error: Mapped[str | None] = mapped_column(Text)

    # Audit
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    version: Mapped[int] = mapped_column(Integer, default=1)

    __table_args__ = (
        Index("idx_complaints_automation_tenant", "tenant_id"),
        Index("idx_complaints_automation_trigger", "tenant_id", "trigger_event"),
        Index("idx_complaints_automation_active", "tenant_id", "is_active"),
    )


# ============================================================================
# COMPLAINT METRICS (KPI aggregees)
# ============================================================================

class ComplaintMetrics(Base):
    """Metriques agregees pour reporting."""
    __tablename__ = "complaints_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Periode
    metric_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_type: Mapped[str] = mapped_column(String(20), default="daily")  # daily, weekly, monthly

    # Dimensions optionnelles
    team_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    agent_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID())
    category: Mapped[str | None] = mapped_column(Enum(ComplaintCategory))
    channel: Mapped[str | None] = mapped_column(Enum(ComplaintChannel))

    # Volumes
    complaints_created: Mapped[int] = mapped_column(Integer, default=0)
    complaints_resolved: Mapped[int] = mapped_column(Integer, default=0)
    complaints_closed: Mapped[int] = mapped_column(Integer, default=0)
    complaints_reopened: Mapped[int] = mapped_column(Integer, default=0)
    complaints_escalated: Mapped[int] = mapped_column(Integer, default=0)

    # SLA
    sla_ack_met: Mapped[int] = mapped_column(Integer, default=0)
    sla_ack_breached: Mapped[int] = mapped_column(Integer, default=0)
    sla_resolution_met: Mapped[int] = mapped_column(Integer, default=0)
    sla_resolution_breached: Mapped[int] = mapped_column(Integer, default=0)

    # Temps (en heures)
    avg_first_response_hours: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    avg_resolution_hours: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    avg_handling_time_hours: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    # Satisfaction
    surveys_sent: Mapped[int] = mapped_column(Integer, default=0)
    surveys_completed: Mapped[int] = mapped_column(Integer, default=0)
    avg_satisfaction_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    avg_nps_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    very_satisfied_count: Mapped[int] = mapped_column(Integer, default=0)
    dissatisfied_count: Mapped[int] = mapped_column(Integer, default=0)

    # Compensation
    total_compensation_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    refund_count: Mapped[int] = mapped_column(Integer, default=0)
    replacement_count: Mapped[int] = mapped_column(Integer, default=0)

    # Par priorite
    complaints_low: Mapped[int] = mapped_column(Integer, default=0)
    complaints_medium: Mapped[int] = mapped_column(Integer, default=0)
    complaints_high: Mapped[int] = mapped_column(Integer, default=0)
    complaints_critical: Mapped[int] = mapped_column(Integer, default=0)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("idx_metrics_tenant_date", "tenant_id", "metric_date"),
        Index("idx_metrics_period", "tenant_id", "period_type", "metric_date"),
        Index("idx_metrics_team", "tenant_id", "team_id", "metric_date"),
        Index("idx_metrics_agent", "tenant_id", "agent_id", "metric_date"),
    )
