"""
AZALS MODULE T2 - Modèles Déclencheurs & Diffusion
===================================================

Modèles SQLAlchemy pour le système de déclencheurs.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Text, Boolean, ForeignKey,
    Index, Enum, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


# ============================================================================
# ENUMS
# ============================================================================

class TriggerType(str, enum.Enum):
    """Types de déclencheurs."""
    THRESHOLD = "THRESHOLD"          # Seuil dépassé
    CONDITION = "CONDITION"          # Condition complexe
    SCHEDULED = "SCHEDULED"          # Planifié (cron)
    EVENT = "EVENT"                  # Événement système
    MANUAL = "MANUAL"                # Déclenché manuellement


class TriggerStatus(str, enum.Enum):
    """Statut d'un déclencheur."""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DISABLED = "DISABLED"


class ConditionOperator(str, enum.Enum):
    """Opérateurs de condition."""
    EQ = "eq"           # Égal
    NE = "ne"           # Différent
    GT = "gt"           # Supérieur
    GE = "ge"           # Supérieur ou égal
    LT = "lt"           # Inférieur
    LE = "le"           # Inférieur ou égal
    IN = "in"           # Dans liste
    NOT_IN = "not_in"   # Pas dans liste
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    BETWEEN = "between"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class AlertSeverity(str, enum.Enum):
    """Niveau de sévérité des alertes."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class NotificationChannel(str, enum.Enum):
    """Canaux de notification."""
    EMAIL = "EMAIL"
    WEBHOOK = "WEBHOOK"
    IN_APP = "IN_APP"
    SMS = "SMS"
    SLACK = "SLACK"
    TEAMS = "TEAMS"


class NotificationStatus(str, enum.Enum):
    """Statut d'une notification."""
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    DELIVERED = "DELIVERED"
    READ = "READ"


class ReportFrequency(str, enum.Enum):
    """Fréquence des rapports."""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"
    CUSTOM = "CUSTOM"


class EscalationLevel(str, enum.Enum):
    """Niveaux d'escalade."""
    L1 = "L1"  # Opérationnel
    L2 = "L2"  # Manager
    L3 = "L3"  # Direction
    L4 = "L4"  # Dirigeant


# ============================================================================
# MODÈLES PRINCIPAUX
# ============================================================================

class Trigger(Base):
    """
    Déclencheur configurable.
    Définit les conditions et actions d'une alerte.
    """
    __tablename__ = "triggers_definitions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Type et configuration
    trigger_type = Column(Enum(TriggerType), nullable=False)
    status = Column(Enum(TriggerStatus), default=TriggerStatus.ACTIVE, nullable=False)

    # Source de données
    source_module = Column(String(50), nullable=False)  # ex: treasury, hr, accounting
    source_entity = Column(String(100), nullable=True)  # ex: forecast, employee
    source_field = Column(String(100), nullable=True)   # ex: balance, status

    # Condition (JSON)
    # {"operator": "lt", "value": 0} ou {"and": [cond1, cond2]}
    condition = Column(Text, nullable=False)

    # Seuil pour THRESHOLD
    threshold_value = Column(String(255), nullable=True)
    threshold_operator = Column(Enum(ConditionOperator), nullable=True)

    # Planification pour SCHEDULED (format cron)
    schedule_cron = Column(String(100), nullable=True)
    schedule_timezone = Column(String(50), default='Europe/Paris', nullable=True)

    # Sévérité et escalade
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.WARNING, nullable=False)
    escalation_enabled = Column(Boolean, default=False, nullable=False)
    escalation_delay_minutes = Column(Integer, default=60, nullable=True)
    escalation_level = Column(Enum(EscalationLevel), default=EscalationLevel.L1, nullable=True)

    # Actions
    action_template_id = Column(Integer, ForeignKey('triggers_templates.id'), nullable=True)

    # Cooldown (éviter spam)
    cooldown_minutes = Column(Integer, default=60, nullable=False)

    # Activation
    is_active = Column(Boolean, default=True, nullable=False)

    # Stats
    last_triggered_at = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, nullable=True)

    # Relations
    template = relationship("NotificationTemplate", foreign_keys=[action_template_id])
    subscriptions = relationship("TriggerSubscription", back_populates="trigger", cascade="all, delete-orphan")
    events = relationship("TriggerEvent", back_populates="trigger", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_trigger_code'),
        Index('idx_triggers_tenant', 'tenant_id'),
        Index('idx_triggers_module', 'source_module'),
        Index('idx_triggers_status', 'status'),
        Index('idx_triggers_type', 'trigger_type'),
    )


class TriggerSubscription(Base):
    """
    Abonnement à un déclencheur.
    Définit qui est notifié et comment.
    """
    __tablename__ = "triggers_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Relation
    trigger_id = Column(Integer, ForeignKey('triggers_definitions.id', ondelete='CASCADE'), nullable=False)

    # Cible
    user_id = Column(Integer, nullable=True)  # Utilisateur spécifique
    role_code = Column(String(50), nullable=True)  # Ou tous les utilisateurs d'un rôle
    group_code = Column(String(50), nullable=True)  # Ou tous les utilisateurs d'un groupe
    email_external = Column(String(255), nullable=True)  # Ou email externe

    # Canal de notification
    channel = Column(Enum(NotificationChannel), default=NotificationChannel.IN_APP, nullable=False)
    channel_config = Column(Text, nullable=True)  # JSON: config spécifique au canal

    # Niveau d'escalade
    escalation_level = Column(Enum(EscalationLevel), default=EscalationLevel.L1, nullable=False)

    # Configuration
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, nullable=True)

    # Relations
    trigger = relationship("Trigger", back_populates="subscriptions")

    __table_args__ = (
        Index('idx_subscriptions_tenant', 'tenant_id'),
        Index('idx_subscriptions_trigger', 'trigger_id'),
        Index('idx_subscriptions_user', 'user_id'),
    )


class TriggerEvent(Base):
    """
    Événement de déclenchement.
    Historique des fois où un trigger s'est déclenché.
    """
    __tablename__ = "triggers_events"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Relation
    trigger_id = Column(Integer, ForeignKey('triggers_definitions.id', ondelete='CASCADE'), nullable=False)

    # Contexte du déclenchement
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    triggered_value = Column(Text, nullable=True)  # Valeur qui a déclenché
    condition_details = Column(Text, nullable=True)  # JSON: détails de la condition

    # Sévérité au moment du déclenchement
    severity = Column(Enum(AlertSeverity), nullable=False)

    # Escalade
    escalation_level = Column(Enum(EscalationLevel), default=EscalationLevel.L1, nullable=False)
    escalated_at = Column(DateTime, nullable=True)

    # Résolution
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Relation
    trigger = relationship("Trigger", back_populates="events")
    notifications = relationship("Notification", back_populates="event", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_events_tenant', 'tenant_id'),
        Index('idx_events_trigger', 'trigger_id'),
        Index('idx_events_triggered_at', 'triggered_at'),
        Index('idx_events_resolved', 'resolved'),
    )


class Notification(Base):
    """
    Notification envoyée suite à un événement.
    """
    __tablename__ = "triggers_notifications"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Relation
    event_id = Column(Integer, ForeignKey('triggers_events.id', ondelete='CASCADE'), nullable=False)

    # Destinataire
    user_id = Column(Integer, nullable=True)
    email = Column(String(255), nullable=True)

    # Canal et contenu
    channel = Column(Enum(NotificationChannel), nullable=False)
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=False)

    # Statut
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False)

    # Envoi
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    failure_reason = Column(Text, nullable=True)

    # Retry
    retry_count = Column(Integer, default=0, nullable=False)
    next_retry_at = Column(DateTime, nullable=True)

    # Relation
    event = relationship("TriggerEvent", back_populates="notifications")

    __table_args__ = (
        Index('idx_notifications_tenant', 'tenant_id'),
        Index('idx_notifications_event', 'event_id'),
        Index('idx_notifications_user', 'user_id'),
        Index('idx_notifications_status', 'status'),
        Index('idx_notifications_sent_at', 'sent_at'),
    )


class NotificationTemplate(Base):
    """
    Template de notification réutilisable.
    """
    __tablename__ = "triggers_templates"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Contenu
    subject_template = Column(String(500), nullable=True)  # Support variables: {{variable}}
    body_template = Column(Text, nullable=False)
    body_html = Column(Text, nullable=True)  # Version HTML

    # Variables disponibles (JSON)
    available_variables = Column(Text, nullable=True)

    # Configuration
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_template_code'),
        Index('idx_templates_tenant', 'tenant_id'),
    )


class ScheduledReport(Base):
    """
    Rapport périodique planifié.
    """
    __tablename__ = "triggers_scheduled_reports"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Type de rapport
    report_type = Column(String(50), nullable=False)  # ex: cockpit_summary, treasury_forecast
    report_config = Column(Text, nullable=True)  # JSON: configuration du rapport

    # Planification
    frequency = Column(Enum(ReportFrequency), nullable=False)
    schedule_day = Column(Integer, nullable=True)  # Jour du mois/semaine
    schedule_time = Column(String(5), nullable=True)  # HH:MM
    schedule_timezone = Column(String(50), default='Europe/Paris', nullable=False)
    schedule_cron = Column(String(100), nullable=True)  # Pour CUSTOM

    # Destinataires (JSON)
    recipients = Column(Text, nullable=False)  # {"users": [1,2], "roles": ["DAF"], "emails": ["ext@test.com"]}

    # Format
    output_format = Column(String(20), default='PDF', nullable=False)  # PDF, EXCEL, HTML

    # Statut
    is_active = Column(Boolean, default=True, nullable=False)

    # Historique
    last_generated_at = Column(DateTime, nullable=True)
    next_generation_at = Column(DateTime, nullable=True)
    generation_count = Column(Integer, default=0, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_report_code'),
        Index('idx_reports_tenant', 'tenant_id'),
        Index('idx_reports_frequency', 'frequency'),
        Index('idx_reports_next', 'next_generation_at'),
    )


class ReportHistory(Base):
    """
    Historique des rapports générés.
    """
    __tablename__ = "triggers_report_history"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Relation
    report_id = Column(Integer, ForeignKey('triggers_scheduled_reports.id', ondelete='CASCADE'), nullable=False)

    # Génération
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    generated_by = Column(Integer, nullable=True)  # NULL si automatique

    # Fichier
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_format = Column(String(20), nullable=False)

    # Envoi
    sent_to = Column(Text, nullable=True)  # JSON: liste des destinataires
    sent_at = Column(DateTime, nullable=True)

    # Statut
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)

    __table_args__ = (
        Index('idx_report_history_tenant', 'tenant_id'),
        Index('idx_report_history_report', 'report_id'),
        Index('idx_report_history_generated', 'generated_at'),
    )


class WebhookEndpoint(Base):
    """
    Configuration d'un endpoint webhook.
    """
    __tablename__ = "triggers_webhooks"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Configuration
    url = Column(String(500), nullable=False)
    method = Column(String(10), default='POST', nullable=False)  # POST, PUT
    headers = Column(Text, nullable=True)  # JSON: headers additionnels
    auth_type = Column(String(20), nullable=True)  # none, basic, bearer, api_key
    auth_config = Column(Text, nullable=True)  # JSON: config auth (chiffré)

    # Retry
    max_retries = Column(Integer, default=3, nullable=False)
    retry_delay_seconds = Column(Integer, default=60, nullable=False)

    # Statut
    is_active = Column(Boolean, default=True, nullable=False)
    last_success_at = Column(DateTime, nullable=True)
    last_failure_at = Column(DateTime, nullable=True)
    consecutive_failures = Column(Integer, default=0, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_webhook_code'),
        Index('idx_webhooks_tenant', 'tenant_id'),
    )


class TriggerLog(Base):
    """
    Log des actions du système de triggers.
    """
    __tablename__ = "triggers_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Action
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)

    # Détails
    details = Column(Text, nullable=True)

    # Résultat
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)

    __table_args__ = (
        Index('idx_trigger_logs_tenant', 'tenant_id'),
        Index('idx_trigger_logs_action', 'action'),
        Index('idx_trigger_logs_created', 'created_at'),
    )
