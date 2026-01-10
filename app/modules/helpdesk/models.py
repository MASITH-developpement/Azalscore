"""
AZALS MODULE 16 - Helpdesk Models
==================================
Modèles SQLAlchemy pour le système de support client.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db import Base
from app.core.types import UniversalUUID
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional

# ============================================================================
# ENUMS
# ============================================================================

class TicketStatus(str, PyEnum):
    """Statut ticket."""
    NEW = "new"
    OPEN = "open"
    PENDING = "pending"
    ON_HOLD = "on_hold"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, PyEnum):
    """Priorité ticket."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class TicketSource(str, PyEnum):
    """Source du ticket."""
    WEB = "web"
    EMAIL = "email"
    PHONE = "phone"
    CHAT = "chat"
    API = "api"
    INTERNAL = "internal"


class AgentStatus(str, PyEnum):
    """Statut agent."""
    AVAILABLE = "available"
    BUSY = "busy"
    AWAY = "away"
    OFFLINE = "offline"


# ============================================================================
# CATEGORY & DEPARTMENT
# ============================================================================

class TicketCategory(Base):
    """Catégorie de ticket."""
    __tablename__ = "helpdesk_categories"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Hiérarchie
    parent_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_categories.id"))
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Configuration
    default_priority: Mapped[Optional[str]] = mapped_column(Enum(TicketPriority), default=TicketPriority.MEDIUM)
    default_team_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_teams.id"))
    sla_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_sla.id"))

    # Options
    is_public: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)  # Visible clients
    require_approval: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    auto_assign: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    sort_order: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    parent = relationship("TicketCategory", remote_side=[id], backref="children")
    tickets = relationship("Ticket", back_populates="category")

    __table_args__ = (
        Index('idx_helpdesk_cat_tenant', 'tenant_id'),
        Index('idx_helpdesk_cat_code', 'tenant_id', 'code', unique=True),
    )


class HelpdeskTeam(Base):
    """Équipe support."""
    __tablename__ = "helpdesk_teams"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    email: Mapped[Optional[str]] = mapped_column(String(255))

    # Configuration
    manager_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # Agent manager
    default_sla_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_sla.id"))
    auto_assign_method: Mapped[Optional[str]] = mapped_column(String(20), default="round_robin")  # round_robin, least_busy, random

    # Paramètres
    max_tickets_per_agent: Mapped[Optional[int]] = mapped_column(Integer, default=20)
    working_hours: Mapped[Optional[dict]] = mapped_column(JSON)  # {mon: {start: "09:00", end: "18:00"}, ...}
    timezone: Mapped[Optional[str]] = mapped_column(String(50), default="Europe/Paris")

    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    members = relationship("HelpdeskAgent", back_populates="team")
    tickets = relationship("Ticket", back_populates="team")

    __table_args__ = (
        Index('idx_helpdesk_team_tenant', 'tenant_id'),
    )


# ============================================================================
# AGENTS
# ============================================================================

class HelpdeskAgent(Base):
    """Agent support."""
    __tablename__ = "helpdesk_agents"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Lien utilisateur
    user_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=False, index=True)
    team_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_teams.id"))

    # Profil
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    signature: Mapped[Optional[str]] = mapped_column(Text)

    # Statut
    status: Mapped[Optional[str]] = mapped_column(Enum(AgentStatus), default=AgentStatus.OFFLINE)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Compétences
    skills: Mapped[Optional[dict]] = mapped_column(JSON)  # ["billing", "technical", "sales"]
    languages: Mapped[Optional[dict]] = mapped_column(JSON, default=["fr"])  # ["fr", "en", "es"]

    # Permissions
    can_assign: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    can_merge: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    can_delete: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    can_view_all: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_supervisor: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Stats
    tickets_assigned: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    tickets_resolved: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    avg_resolution_time: Mapped[Optional[int]] = mapped_column(Integer, default=0)  # En minutes
    satisfaction_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), default=0)

    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    team = relationship("HelpdeskTeam", back_populates="members")
    assigned_tickets = relationship("Ticket", back_populates="assigned_agent", foreign_keys="Ticket.assigned_to_id")

    __table_args__ = (
        Index('idx_helpdesk_agent_tenant', 'tenant_id'),
        Index('idx_helpdesk_agent_user', 'tenant_id', 'user_id', unique=True),
        Index('idx_helpdesk_agent_team', 'team_id'),
    )


# ============================================================================
# SLA (Service Level Agreements)
# ============================================================================

class HelpdeskSLA(Base):
    """SLA Helpdesk."""
    __tablename__ = "helpdesk_sla"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Temps de réponse (en minutes)
    first_response_low: Mapped[Optional[int]] = mapped_column(Integer, default=1440)  # 24h
    first_response_medium: Mapped[Optional[int]] = mapped_column(Integer, default=480)  # 8h
    first_response_high: Mapped[Optional[int]] = mapped_column(Integer, default=120)  # 2h
    first_response_urgent: Mapped[Optional[int]] = mapped_column(Integer, default=60)  # 1h
    first_response_critical: Mapped[Optional[int]] = mapped_column(Integer, default=15)  # 15min

    # Temps de résolution (en minutes)
    resolution_low: Mapped[Optional[int]] = mapped_column(Integer, default=10080)  # 7 jours
    resolution_medium: Mapped[Optional[int]] = mapped_column(Integer, default=2880)  # 2 jours
    resolution_high: Mapped[Optional[int]] = mapped_column(Integer, default=1440)  # 1 jour
    resolution_urgent: Mapped[Optional[int]] = mapped_column(Integer, default=480)  # 8h
    resolution_critical: Mapped[Optional[int]] = mapped_column(Integer, default=120)  # 2h

    # Heures ouvrées
    business_hours_only: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    working_hours: Mapped[Optional[dict]] = mapped_column(JSON)  # {mon: {start: "09:00", end: "18:00"}, ...}
    timezone: Mapped[Optional[str]] = mapped_column(String(50), default="Europe/Paris")
    holidays: Mapped[Optional[dict]] = mapped_column(JSON)  # ["2024-12-25", ...]

    # Escalade
    escalation_enabled: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    escalation_rules: Mapped[Optional[dict]] = mapped_column(JSON)  # [{delay_minutes, action, target}, ...]

    is_default: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_helpdesk_sla_tenant', 'tenant_id'),
    )


# ============================================================================
# TICKETS
# ============================================================================

class Ticket(Base):
    """Ticket support."""
    __tablename__ = "helpdesk_tickets"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    ticket_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, unique=True)

    # Classification
    category_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_categories.id"))
    team_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_teams.id"))
    sla_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_sla.id"))

    # Contenu
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    source: Mapped[Optional[str]] = mapped_column(Enum(TicketSource), default=TicketSource.WEB)

    # Statut et priorité
    status: Mapped[Optional[str]] = mapped_column(Enum(TicketStatus), nullable=False, default=TicketStatus.NEW)
    priority: Mapped[Optional[str]] = mapped_column(Enum(TicketPriority), nullable=False, default=TicketPriority.MEDIUM)

    # Demandeur
    requester_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), index=True)  # ID client CRM
    requester_name: Mapped[Optional[str]] = mapped_column(String(255))
    requester_email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    requester_phone: Mapped[Optional[str]] = mapped_column(String(50))
    company_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # Entreprise cliente

    # Assignation
    assigned_to_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_agents.id"))

    # SLA tracking
    first_response_due: Mapped[Optional[datetime]] = mapped_column(DateTime)
    first_responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolution_due: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sla_breached: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Tags et metadata
    tags: Mapped[Optional[dict]] = mapped_column(JSON)  # ["urgent", "vip", "billing"]
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSON)  # Champs personnalisés

    # Ticket lié
    parent_ticket_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_tickets.id"))
    merged_into_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_tickets.id"))

    # Stats
    reply_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    internal_note_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    satisfaction_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5

    # Dates
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relations
    category = relationship("TicketCategory", back_populates="tickets")
    team = relationship("HelpdeskTeam", back_populates="tickets")
    assigned_agent = relationship("HelpdeskAgent", back_populates="assigned_tickets", foreign_keys=[assigned_to_id])
    replies = relationship("TicketReply", back_populates="ticket", cascade="all, delete-orphan")
    attachments = relationship("TicketAttachment", back_populates="ticket", cascade="all, delete-orphan")
    history = relationship("TicketHistory", back_populates="ticket", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_helpdesk_tickets_tenant', 'tenant_id'),
        Index('idx_helpdesk_tickets_number', 'ticket_number'),
        Index('idx_helpdesk_tickets_status', 'tenant_id', 'status'),
        Index('idx_helpdesk_tickets_priority', 'tenant_id', 'priority'),
        Index('idx_helpdesk_tickets_requester', 'tenant_id', 'requester_id'),
        Index('idx_helpdesk_tickets_assigned', 'tenant_id', 'assigned_to_id'),
        Index('idx_helpdesk_tickets_sla', 'tenant_id', 'sla_breached'),
    )


class TicketReply(Base):
    """Réponse à un ticket."""
    __tablename__ = "helpdesk_replies"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_tickets.id"), nullable=False)

    # Auteur
    author_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=False)  # agent, customer, system
    author_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    author_name: Mapped[Optional[str]] = mapped_column(String(255))
    author_email: Mapped[Optional[str]] = mapped_column(String(255))

    # Contenu
    body: Mapped[str] = mapped_column(Text)
    body_html: Mapped[Optional[str]] = mapped_column(Text)

    # Type
    is_internal: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)  # Note interne
    is_first_response: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Forward/CC
    cc_emails: Mapped[Optional[dict]] = mapped_column(JSON)
    bcc_emails: Mapped[Optional[dict]] = mapped_column(JSON)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    ticket = relationship("Ticket", back_populates="replies")
    attachments = relationship("TicketAttachment", back_populates="reply")

    __table_args__ = (
        Index('idx_helpdesk_replies_ticket', 'ticket_id'),
    )


class TicketAttachment(Base):
    """Pièce jointe."""
    __tablename__ = "helpdesk_attachments"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_tickets.id"), nullable=False)
    reply_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_replies.id"))

    # Fichier
    filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    file_url: Mapped[Optional[str]] = mapped_column(String(500))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)  # En bytes
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))

    # Upload
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    ticket = relationship("Ticket", back_populates="attachments")
    reply = relationship("TicketReply", back_populates="attachments")

    __table_args__ = (
        Index('idx_helpdesk_attach_ticket', 'ticket_id'),
    )


class TicketHistory(Base):
    """Historique des changements."""
    __tablename__ = "helpdesk_history"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_tickets.id"), nullable=False)

    # Changement
    action: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)  # created, status_changed, assigned, etc.
    field_name: Mapped[Optional[str]] = mapped_column(String(50))
    old_value: Mapped[Optional[str]] = mapped_column(String(500))
    new_value: Mapped[Optional[str]] = mapped_column(String(500))

    # Auteur
    actor_type: Mapped[Optional[str]] = mapped_column(String(20))  # agent, customer, system, automation
    actor_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    actor_name: Mapped[Optional[str]] = mapped_column(String(255))

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    ticket = relationship("Ticket", back_populates="history")

    __table_args__ = (
        Index('idx_helpdesk_history_ticket', 'ticket_id'),
    )


# ============================================================================
# CANNED RESPONSES
# ============================================================================

class CannedResponse(Base):
    """Réponse pré-enregistrée."""
    __tablename__ = "helpdesk_canned_responses"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    shortcut: Mapped[Optional[str]] = mapped_column(String(50))  # Ex: #greeting

    # Contenu
    body: Mapped[str] = mapped_column(Text)
    body_html: Mapped[Optional[str]] = mapped_column(Text)

    # Classification
    category: Mapped[Optional[str]] = mapped_column(String(100))
    tags: Mapped[Optional[dict]] = mapped_column(JSON)

    # Scope
    scope: Mapped[Optional[str]] = mapped_column(String(20), default="team")  # personal, team, global
    team_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_teams.id"))
    agent_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_agents.id"))

    # Stats
    usage_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_helpdesk_canned_tenant', 'tenant_id'),
        Index('idx_helpdesk_canned_shortcut', 'tenant_id', 'shortcut'),
    )


# ============================================================================
# KNOWLEDGE BASE
# ============================================================================

class KBCategory(Base):
    """Catégorie base de connaissances."""
    __tablename__ = "helpdesk_kb_categories"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    parent_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_kb_categories.id"))
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    slug: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    icon: Mapped[Optional[str]] = mapped_column(String(50))

    sort_order: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    is_public: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    parent = relationship("KBCategory", remote_side=[id], backref="subcategories")
    articles = relationship("KBArticle", back_populates="category")

    __table_args__ = (
        Index('idx_kb_cat_tenant', 'tenant_id'),
        Index('idx_kb_cat_slug', 'tenant_id', 'slug'),
    )


class KBArticle(Base):
    """Article base de connaissances."""
    __tablename__ = "helpdesk_kb_articles"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_kb_categories.id"))

    # Contenu
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=False)
    slug: Mapped[Optional[str]] = mapped_column(String(500), nullable=False)
    excerpt: Mapped[Optional[str]] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    body_html: Mapped[Optional[str]] = mapped_column(Text)

    # SEO
    meta_title: Mapped[Optional[str]] = mapped_column(String(255))
    meta_description: Mapped[Optional[str]] = mapped_column(String(500))
    keywords: Mapped[Optional[dict]] = mapped_column(JSON)

    # Auteur
    author_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    author_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Statut
    status: Mapped[Optional[str]] = mapped_column(String(20), default="draft")  # draft, published, archived
    is_featured: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_public: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    # Stats
    view_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    helpful_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    not_helpful_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Dates
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    category = relationship("KBCategory", back_populates="articles")

    __table_args__ = (
        Index('idx_kb_article_tenant', 'tenant_id'),
        Index('idx_kb_article_slug', 'tenant_id', 'slug'),
        Index('idx_kb_article_status', 'tenant_id', 'status'),
    )


# ============================================================================
# SATISFACTION SURVEYS
# ============================================================================

class SatisfactionSurvey(Base):
    """Enquête satisfaction."""
    __tablename__ = "helpdesk_satisfaction"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_tickets.id"), nullable=False)

    # Note
    rating: Mapped[int] = mapped_column(Integer)  # 1-5
    feedback: Mapped[Optional[str]] = mapped_column(Text)

    # Auteur
    customer_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    customer_email: Mapped[Optional[str]] = mapped_column(String(255))

    # Agent évalué
    agent_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("helpdesk_agents.id"))

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_satisfaction_tenant', 'tenant_id'),
        Index('idx_satisfaction_ticket', 'ticket_id'),
        Index('idx_satisfaction_agent', 'agent_id'),
    )


# ============================================================================
# AUTOMATIONS
# ============================================================================

class HelpdeskAutomation(Base):
    """Règle d'automatisation."""
    __tablename__ = "helpdesk_automations"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Déclencheur
    trigger_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)  # ticket_created, ticket_updated, time_based
    trigger_conditions: Mapped[Optional[dict]] = mapped_column(JSON)  # [{field, operator, value}, ...]

    # Actions
    actions: Mapped[Optional[dict]] = mapped_column(JSON)  # [{type, params}, ...]

    # Priorité d'exécution
    priority: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Stats
    execution_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    last_executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_automation_tenant', 'tenant_id'),
        Index('idx_automation_trigger', 'tenant_id', 'trigger_type'),
    )
