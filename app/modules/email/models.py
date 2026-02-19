"""
AZALS - Module Email - Modèles
==============================
Modèles de données pour les emails transactionnels.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum

from app.db.base import Base
from app.core.types import JSON, UniversalUUID


class EmailStatus(str, Enum):
    """Statut d'un email."""
    PENDING = "pending"          # En attente d'envoi
    QUEUED = "queued"           # Dans la file d'attente
    SENDING = "sending"          # En cours d'envoi
    SENT = "sent"               # Envoyé avec succès
    DELIVERED = "delivered"      # Délivré (confirmation)
    OPENED = "opened"           # Ouvert par le destinataire
    CLICKED = "clicked"          # Lien cliqué
    BOUNCED = "bounced"          # Rejeté
    FAILED = "failed"            # Échec d'envoi
    SPAM = "spam"               # Marqué comme spam


class EmailType(str, Enum):
    """Type d'email transactionnel."""
    TENANT_CREATED = "tenant_created"
    PAYMENT_CONFIRMED = "payment_confirmed"
    INVOICE_SENT = "invoice_sent"
    PASSWORD_RESET = "password_reset"
    WELCOME = "welcome"
    SUPPORT_TICKET = "support_ticket"
    SUPPORT_REPLY = "support_reply"
    INCIDENT_ALERT = "incident_alert"
    SLA_BREACH = "sla_breach"
    BACKUP_COMPLETED = "backup_completed"
    SECURITY_ALERT = "security_alert"
    TWO_FACTOR = "two_factor"
    INVITATION = "invitation"
    REMINDER = "reminder"
    CUSTOM = "custom"


class EmailTemplate(Base):
    """Modèle de template d'email."""
    __tablename__ = "email_templates"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=True, index=True)  # NULL = template global
    code = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email_type = Column(SQLEnum(EmailType), nullable=False)
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text, nullable=True)
    variables = Column(JSON, default=list)  # Liste des variables disponibles
    language = Column(String(5), default="fr")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        {'extend_existing': True}
    )


class EmailLog(Base):
    """Log des emails envoyés."""
    __tablename__ = "email_logs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    template_id = Column(UniversalUUID(), ForeignKey("email_templates.id"), nullable=True)
    email_type = Column(SQLEnum(EmailType), nullable=False, index=True)
    status = Column(SQLEnum(EmailStatus), default=EmailStatus.PENDING, index=True)

    # Destinataires
    to_email = Column(String(255), nullable=False)
    to_name = Column(String(255), nullable=True)
    cc_emails = Column(JSON, default=list)
    bcc_emails = Column(JSON, default=list)

    # Contenu
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    variables_used = Column(JSON, default=dict)
    attachments = Column(JSON, default=list)

    # Métadonnées
    reference_type = Column(String(50), nullable=True)  # ex: "invoice", "ticket"
    reference_id = Column(String(100), nullable=True)
    priority = Column(Integer, default=5)  # 1=highest, 10=lowest
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Provider
    provider = Column(String(50), nullable=True)  # smtp, sendgrid, mailgun, etc.
    provider_message_id = Column(String(255), nullable=True)
    provider_response = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    queued_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Audit
    created_by = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)

    __table_args__ = (
        {'extend_existing': True}
    )


class EmailConfig(Base):
    """Configuration email par tenant."""
    __tablename__ = "email_configs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, unique=True, index=True)

    # Provider SMTP
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, default=587)
    smtp_username = Column(String(255), nullable=True)
    smtp_password_encrypted = Column(Text, nullable=True)
    smtp_use_tls = Column(Boolean, default=True)
    smtp_use_ssl = Column(Boolean, default=False)

    # Provider externe (Sendgrid, Mailgun, etc.)
    provider = Column(String(50), default="smtp")  # smtp, sendgrid, mailgun, ses
    api_key_encrypted = Column(Text, nullable=True)
    api_endpoint = Column(String(500), nullable=True)

    # Identité expéditeur
    from_email = Column(String(255), nullable=False)
    from_name = Column(String(255), nullable=False)
    reply_to_email = Column(String(255), nullable=True)

    # Options
    max_emails_per_hour = Column(Integer, default=100)
    max_emails_per_day = Column(Integer, default=1000)
    retry_delay_seconds = Column(Integer, default=300)
    track_opens = Column(Boolean, default=True)
    track_clicks = Column(Boolean, default=True)

    # État
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_verified_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        {'extend_existing': True}
    )


class EmailQueue(Base):
    """File d'attente des emails à envoyer."""
    __tablename__ = "email_queue"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    email_log_id = Column(UniversalUUID(), ForeignKey("email_logs.id"), nullable=False)
    tenant_id = Column(String(50), nullable=False, index=True)
    priority = Column(Integer, default=5, index=True)
    scheduled_at = Column(DateTime, default=datetime.utcnow, index=True)
    attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    next_attempt_at = Column(DateTime, nullable=True)
    locked_by = Column(String(100), nullable=True)
    locked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        {'extend_existing': True}
    )
