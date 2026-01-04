"""
AZALS MODULE 16 - Helpdesk Models
==================================
Modèles SQLAlchemy pour le système de support client.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Numeric, Enum, Index, JSON
)
from sqlalchemy.orm import relationship

from app.core.database import Base


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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Hiérarchie
    parent_id = Column(Integer, ForeignKey("helpdesk_categories.id"))
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Configuration
    default_priority = Column(Enum(TicketPriority), default=TicketPriority.MEDIUM)
    default_team_id = Column(Integer, ForeignKey("helpdesk_teams.id"))
    sla_id = Column(Integer, ForeignKey("helpdesk_sla.id"))

    # Options
    is_public = Column(Boolean, default=True)  # Visible clients
    require_approval = Column(Boolean, default=False)
    auto_assign = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    name = Column(String(100), nullable=False)
    description = Column(Text)
    email = Column(String(255))

    # Configuration
    manager_id = Column(Integer)  # Agent manager
    default_sla_id = Column(Integer, ForeignKey("helpdesk_sla.id"))
    auto_assign_method = Column(String(20), default="round_robin")  # round_robin, least_busy, random

    # Paramètres
    max_tickets_per_agent = Column(Integer, default=20)
    working_hours = Column(JSON)  # {mon: {start: "09:00", end: "18:00"}, ...}
    timezone = Column(String(50), default="Europe/Paris")

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Lien utilisateur
    user_id = Column(Integer, nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("helpdesk_teams.id"))

    # Profil
    display_name = Column(String(255), nullable=False)
    email = Column(String(255))
    avatar_url = Column(String(500))
    signature = Column(Text)

    # Statut
    status = Column(Enum(AgentStatus), default=AgentStatus.OFFLINE)
    last_seen = Column(DateTime)

    # Compétences
    skills = Column(JSON)  # ["billing", "technical", "sales"]
    languages = Column(JSON, default=["fr"])  # ["fr", "en", "es"]

    # Permissions
    can_assign = Column(Boolean, default=True)
    can_merge = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_view_all = Column(Boolean, default=False)
    is_supervisor = Column(Boolean, default=False)

    # Stats
    tickets_assigned = Column(Integer, default=0)
    tickets_resolved = Column(Integer, default=0)
    avg_resolution_time = Column(Integer, default=0)  # En minutes
    satisfaction_score = Column(Numeric(3, 2), default=0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Temps de réponse (en minutes)
    first_response_low = Column(Integer, default=1440)  # 24h
    first_response_medium = Column(Integer, default=480)  # 8h
    first_response_high = Column(Integer, default=120)  # 2h
    first_response_urgent = Column(Integer, default=60)  # 1h
    first_response_critical = Column(Integer, default=15)  # 15min

    # Temps de résolution (en minutes)
    resolution_low = Column(Integer, default=10080)  # 7 jours
    resolution_medium = Column(Integer, default=2880)  # 2 jours
    resolution_high = Column(Integer, default=1440)  # 1 jour
    resolution_urgent = Column(Integer, default=480)  # 8h
    resolution_critical = Column(Integer, default=120)  # 2h

    # Heures ouvrées
    business_hours_only = Column(Boolean, default=True)
    working_hours = Column(JSON)  # {mon: {start: "09:00", end: "18:00"}, ...}
    timezone = Column(String(50), default="Europe/Paris")
    holidays = Column(JSON)  # ["2024-12-25", ...]

    # Escalade
    escalation_enabled = Column(Boolean, default=True)
    escalation_rules = Column(JSON)  # [{delay_minutes, action, target}, ...]

    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_helpdesk_sla_tenant', 'tenant_id'),
    )


# ============================================================================
# TICKETS
# ============================================================================

class Ticket(Base):
    """Ticket support."""
    __tablename__ = "helpdesk_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    ticket_number = Column(String(50), nullable=False, unique=True)

    # Classification
    category_id = Column(Integer, ForeignKey("helpdesk_categories.id"))
    team_id = Column(Integer, ForeignKey("helpdesk_teams.id"))
    sla_id = Column(Integer, ForeignKey("helpdesk_sla.id"))

    # Contenu
    subject = Column(String(500), nullable=False)
    description = Column(Text)
    source = Column(Enum(TicketSource), default=TicketSource.WEB)

    # Statut et priorité
    status = Column(Enum(TicketStatus), nullable=False, default=TicketStatus.NEW)
    priority = Column(Enum(TicketPriority), nullable=False, default=TicketPriority.MEDIUM)

    # Demandeur
    requester_id = Column(Integer, index=True)  # ID client CRM
    requester_name = Column(String(255))
    requester_email = Column(String(255), index=True)
    requester_phone = Column(String(50))
    company_id = Column(Integer)  # Entreprise cliente

    # Assignation
    assigned_to_id = Column(Integer, ForeignKey("helpdesk_agents.id"))

    # SLA tracking
    first_response_due = Column(DateTime)
    first_responded_at = Column(DateTime)
    resolution_due = Column(DateTime)
    resolved_at = Column(DateTime)
    sla_breached = Column(Boolean, default=False)

    # Tags et metadata
    tags = Column(JSON)  # ["urgent", "vip", "billing"]
    custom_fields = Column(JSON)  # Champs personnalisés

    # Ticket lié
    parent_ticket_id = Column(Integer, ForeignKey("helpdesk_tickets.id"))
    merged_into_id = Column(Integer, ForeignKey("helpdesk_tickets.id"))

    # Stats
    reply_count = Column(Integer, default=0)
    internal_note_count = Column(Integer, default=0)
    satisfaction_rating = Column(Integer)  # 1-5

    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    ticket_id = Column(Integer, ForeignKey("helpdesk_tickets.id"), nullable=False)

    # Auteur
    author_type = Column(String(20), nullable=False)  # agent, customer, system
    author_id = Column(Integer)
    author_name = Column(String(255))
    author_email = Column(String(255))

    # Contenu
    body = Column(Text, nullable=False)
    body_html = Column(Text)

    # Type
    is_internal = Column(Boolean, default=False)  # Note interne
    is_first_response = Column(Boolean, default=False)

    # Forward/CC
    cc_emails = Column(JSON)
    bcc_emails = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    ticket = relationship("Ticket", back_populates="replies")
    attachments = relationship("TicketAttachment", back_populates="reply")

    __table_args__ = (
        Index('idx_helpdesk_replies_ticket', 'ticket_id'),
    )


class TicketAttachment(Base):
    """Pièce jointe."""
    __tablename__ = "helpdesk_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    ticket_id = Column(Integer, ForeignKey("helpdesk_tickets.id"), nullable=False)
    reply_id = Column(Integer, ForeignKey("helpdesk_replies.id"))

    # Fichier
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500))
    file_url = Column(String(500))
    file_size = Column(Integer)  # En bytes
    mime_type = Column(String(100))

    # Upload
    uploaded_by_id = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    ticket = relationship("Ticket", back_populates="attachments")
    reply = relationship("TicketReply", back_populates="attachments")

    __table_args__ = (
        Index('idx_helpdesk_attach_ticket', 'ticket_id'),
    )


class TicketHistory(Base):
    """Historique des changements."""
    __tablename__ = "helpdesk_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    ticket_id = Column(Integer, ForeignKey("helpdesk_tickets.id"), nullable=False)

    # Changement
    action = Column(String(50), nullable=False)  # created, status_changed, assigned, etc.
    field_name = Column(String(50))
    old_value = Column(String(500))
    new_value = Column(String(500))

    # Auteur
    actor_type = Column(String(20))  # agent, customer, system, automation
    actor_id = Column(Integer)
    actor_name = Column(String(255))

    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    title = Column(String(255), nullable=False)
    shortcut = Column(String(50))  # Ex: #greeting

    # Contenu
    body = Column(Text, nullable=False)
    body_html = Column(Text)

    # Classification
    category = Column(String(100))
    tags = Column(JSON)

    # Scope
    scope = Column(String(20), default="team")  # personal, team, global
    team_id = Column(Integer, ForeignKey("helpdesk_teams.id"))
    agent_id = Column(Integer, ForeignKey("helpdesk_agents.id"))

    # Stats
    usage_count = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    parent_id = Column(Integer, ForeignKey("helpdesk_kb_categories.id"))
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    description = Column(Text)
    icon = Column(String(50))

    sort_order = Column(Integer, default=0)
    is_public = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("helpdesk_kb_categories.id"))

    # Contenu
    title = Column(String(500), nullable=False)
    slug = Column(String(500), nullable=False)
    excerpt = Column(Text)
    body = Column(Text, nullable=False)
    body_html = Column(Text)

    # SEO
    meta_title = Column(String(255))
    meta_description = Column(String(500))
    keywords = Column(JSON)

    # Auteur
    author_id = Column(Integer)
    author_name = Column(String(255))

    # Statut
    status = Column(String(20), default="draft")  # draft, published, archived
    is_featured = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)

    # Stats
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)

    # Dates
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    ticket_id = Column(Integer, ForeignKey("helpdesk_tickets.id"), nullable=False)

    # Note
    rating = Column(Integer, nullable=False)  # 1-5
    feedback = Column(Text)

    # Auteur
    customer_id = Column(Integer)
    customer_email = Column(String(255))

    # Agent évalué
    agent_id = Column(Integer, ForeignKey("helpdesk_agents.id"))

    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Déclencheur
    trigger_type = Column(String(50), nullable=False)  # ticket_created, ticket_updated, time_based
    trigger_conditions = Column(JSON)  # [{field, operator, value}, ...]

    # Actions
    actions = Column(JSON)  # [{type, params}, ...]

    # Priorité d'exécution
    priority = Column(Integer, default=0)

    # Stats
    execution_count = Column(Integer, default=0)
    last_executed_at = Column(DateTime)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_automation_tenant', 'tenant_id'),
        Index('idx_automation_trigger', 'tenant_id', 'trigger_type'),
    )
