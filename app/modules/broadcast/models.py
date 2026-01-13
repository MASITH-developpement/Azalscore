"""
AZALS MODULE T6 - Modèles Diffusion Périodique
==============================================

Modèles SQLAlchemy pour la gestion des diffusions automatiques.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.types import JSON, UniversalUUID
from app.db import Base

# ============================================================================
# ENUMS
# ============================================================================

class DeliveryChannel(str, PyEnum):
    """Canaux de livraison"""
    EMAIL = "EMAIL"
    IN_APP = "IN_APP"
    WEBHOOK = "WEBHOOK"
    PDF_DOWNLOAD = "PDF_DOWNLOAD"
    SMS = "SMS"


class BroadcastFrequency(str, PyEnum):
    """Fréquences de diffusion"""
    ONCE = "ONCE"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    BIWEEKLY = "BIWEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"
    CUSTOM = "CUSTOM"


class ContentType(str, PyEnum):
    """Types de contenu"""
    DIGEST = "DIGEST"
    NEWSLETTER = "NEWSLETTER"
    REPORT = "REPORT"
    ALERT = "ALERT"
    KPI_SUMMARY = "KPI_SUMMARY"


class BroadcastStatus(str, PyEnum):
    """Statuts de diffusion"""
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"


class DeliveryStatus(str, PyEnum):
    """Statuts de livraison"""
    PENDING = "PENDING"
    SENDING = "SENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    BOUNCED = "BOUNCED"
    OPENED = "OPENED"
    CLICKED = "CLICKED"


class RecipientType(str, PyEnum):
    """Types de destinataires"""
    USER = "USER"
    GROUP = "GROUP"
    ROLE = "ROLE"
    EXTERNAL = "EXTERNAL"
    DYNAMIC = "DYNAMIC"


# ============================================================================
# MODÈLE: TEMPLATE DE DIFFUSION
# ============================================================================

class BroadcastTemplate(Base):
    """Template réutilisable pour les diffusions"""
    __tablename__ = "broadcast_templates"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    code: Mapped[str | None] = mapped_column(String(50), nullable=False)
    name: Mapped[str | None] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Type et contenu
    content_type: Mapped[str | None] = mapped_column(Enum(ContentType), nullable=False)
    subject_template: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    html_template: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Configuration
    default_channel: Mapped[str | None] = mapped_column(Enum(DeliveryChannel), default=DeliveryChannel.EMAIL)
    available_channels: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Liste des canaux supportés
    variables: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Variables disponibles
    styling: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # CSS et mise en forme

    # Data sources
    data_sources: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Sources de données à agréger
    aggregation_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Config d'agrégation

    # Localisation
    language: Mapped[str | None] = mapped_column(String(5), default="fr")
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)

    # État
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index("ix_broadcast_templates_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_broadcast_templates_tenant_type", "tenant_id", "content_type"),
    )


# ============================================================================
# MODÈLE: LISTE DE DESTINATAIRES
# ============================================================================

class RecipientList(Base):
    """Liste de destinataires réutilisable"""
    __tablename__ = "broadcast_recipient_lists"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    code: Mapped[str | None] = mapped_column(String(50), nullable=False)
    name: Mapped[str | None] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Configuration
    is_dynamic: Mapped[bool | None] = mapped_column(Boolean, default=False)  # Liste dynamique (requête)
    query_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Config pour listes dynamiques

    # Statistiques
    total_recipients: Mapped[int | None] = mapped_column(Integer, default=0)
    active_recipients: Mapped[int | None] = mapped_column(Integer, default=0)

    # État
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index("ix_recipient_lists_tenant_code", "tenant_id", "code", unique=True),
    )


# ============================================================================
# MODÈLE: MEMBRE D'UNE LISTE
# ============================================================================

class RecipientMember(Base):
    """Membre d'une liste de destinataires"""
    __tablename__ = "broadcast_recipient_members"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    list_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("broadcast_recipient_lists.id"), nullable=False)

    # Type et référence
    recipient_type: Mapped[str | None] = mapped_column(Enum(RecipientType), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)  # Pour USER
    group_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)  # Pour GROUP
    role_code: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Pour ROLE
    external_email: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Pour EXTERNAL
    external_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Préférences
    preferred_channel: Mapped[str | None] = mapped_column(Enum(DeliveryChannel), nullable=True)
    preferred_language: Mapped[str | None] = mapped_column(String(5), nullable=True)
    preferred_format: Mapped[str | None] = mapped_column(String(20), nullable=True)  # HTML, TEXT, PDF

    # État
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_unsubscribed: Mapped[bool | None] = mapped_column(Boolean, default=False)
    unsubscribed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Audit
    added_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    added_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index("ix_recipient_members_list", "tenant_id", "list_id"),
        Index("ix_recipient_members_user", "tenant_id", "user_id"),
    )


# ============================================================================
# MODÈLE: DIFFUSION PROGRAMMÉE
# ============================================================================

class ScheduledBroadcast(Base):
    """Diffusion programmée/récurrente"""
    __tablename__ = "scheduled_broadcasts"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    code: Mapped[str | None] = mapped_column(String(50), nullable=False)
    name: Mapped[str | None] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Template et destinataires
    template_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("broadcast_templates.id"), nullable=True)
    recipient_list_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("broadcast_recipient_lists.id"), nullable=True)

    # Contenu personnalisé (si pas de template)
    content_type: Mapped[str | None] = mapped_column(Enum(ContentType), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    html_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Configuration livraison
    delivery_channel: Mapped[str | None] = mapped_column(Enum(DeliveryChannel), nullable=False, default=DeliveryChannel.EMAIL)
    additional_channels: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Planification
    frequency: Mapped[str | None] = mapped_column(Enum(BroadcastFrequency), nullable=False)
    cron_expression: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Pour CUSTOM
    timezone: Mapped[str | None] = mapped_column(String(50), default="Europe/Paris")

    # Fenêtre de diffusion
    start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    send_time: Mapped[str | None] = mapped_column(String(5), nullable=True)  # HH:MM

    # Pour fréquence spécifique
    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-6 pour WEEKLY
    day_of_month: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-31 pour MONTHLY
    month_of_year: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-12 pour YEARLY

    # Data dynamique
    data_query: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Requête pour données
    data_filters: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Filtres

    # État
    status: Mapped[str | None] = mapped_column(Enum(BroadcastStatus), default=BroadcastStatus.DRAFT)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)

    # Statistiques
    total_sent: Mapped[int | None] = mapped_column(Integer, default=0)
    total_delivered: Mapped[int | None] = mapped_column(Integer, default=0)
    total_failed: Mapped[int | None] = mapped_column(Integer, default=0)
    total_opened: Mapped[int | None] = mapped_column(Integer, default=0)
    total_clicked: Mapped[int | None] = mapped_column(Integer, default=0)

    # Exécution
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index("ix_scheduled_broadcasts_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_scheduled_broadcasts_tenant_status", "tenant_id", "status"),
        Index("ix_scheduled_broadcasts_next_run", "tenant_id", "next_run_at"),
    )


# ============================================================================
# MODÈLE: EXÉCUTION DE DIFFUSION
# ============================================================================

class BroadcastExecution(Base):
    """Historique d'exécution d'une diffusion"""
    __tablename__ = "broadcast_executions"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    scheduled_broadcast_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("scheduled_broadcasts.id"), nullable=False)

    # Exécution
    execution_number: Mapped[int | None] = mapped_column(Integer, default=1)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Résultats
    status: Mapped[str | None] = mapped_column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING)
    total_recipients: Mapped[int | None] = mapped_column(Integer, default=0)
    sent_count: Mapped[int | None] = mapped_column(Integer, default=0)
    delivered_count: Mapped[int | None] = mapped_column(Integer, default=0)
    failed_count: Mapped[int | None] = mapped_column(Integer, default=0)
    bounced_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # Contenu généré
    generated_subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    generated_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachments: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Erreurs
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Métriques engagement
    opened_count: Mapped[int | None] = mapped_column(Integer, default=0)
    clicked_count: Mapped[int | None] = mapped_column(Integer, default=0)
    unsubscribed_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # Audit
    triggered_by: Mapped[str | None] = mapped_column(String(50), default="scheduler")  # scheduler, manual, api
    triggered_user: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index("ix_broadcast_executions_scheduled", "tenant_id", "scheduled_broadcast_id"),
        Index("ix_broadcast_executions_date", "tenant_id", "started_at"),
    )


# ============================================================================
# MODÈLE: DÉTAIL DE LIVRAISON
# ============================================================================

class DeliveryDetail(Base):
    """Détail de livraison par destinataire"""
    __tablename__ = "broadcast_delivery_details"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    execution_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("broadcast_executions.id"), nullable=False)

    # Destinataire
    recipient_type: Mapped[str | None] = mapped_column(Enum(RecipientType), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Livraison
    channel: Mapped[str | None] = mapped_column(Enum(DeliveryChannel), nullable=False)
    status: Mapped[str | None] = mapped_column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING)

    # Timing
    queued_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Engagement
    opened_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    opened_count: Mapped[int | None] = mapped_column(Integer, default=0)
    clicked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    click_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # Erreurs
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int | None] = mapped_column(Integer, default=0)
    last_retry_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Tracking
    tracking_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # UUID pour tracking
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)

    __table_args__ = (
        Index("ix_delivery_details_execution", "tenant_id", "execution_id"),
        Index("ix_delivery_details_user", "tenant_id", "user_id"),
        Index("ix_delivery_details_status", "tenant_id", "status"),
        Index("ix_delivery_details_tracking", "tracking_id"),
    )


# ============================================================================
# MODÈLE: PRÉFÉRENCES DE DIFFUSION
# ============================================================================

class BroadcastPreference(Base):
    """Préférences de diffusion par utilisateur"""
    __tablename__ = "broadcast_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=False)

    # Préférences globales
    receive_digests: Mapped[bool | None] = mapped_column(Boolean, default=True)
    receive_newsletters: Mapped[bool | None] = mapped_column(Boolean, default=True)
    receive_reports: Mapped[bool | None] = mapped_column(Boolean, default=True)
    receive_alerts: Mapped[bool | None] = mapped_column(Boolean, default=True)

    # Canal préféré
    preferred_channel: Mapped[str | None] = mapped_column(Enum(DeliveryChannel), default=DeliveryChannel.EMAIL)
    preferred_language: Mapped[str | None] = mapped_column(String(5), default="fr")
    preferred_format: Mapped[str | None] = mapped_column(String(20), default="HTML")  # HTML, TEXT, PDF

    # Fréquence
    digest_frequency: Mapped[str | None] = mapped_column(Enum(BroadcastFrequency), default=BroadcastFrequency.DAILY)
    report_frequency: Mapped[str | None] = mapped_column(Enum(BroadcastFrequency), default=BroadcastFrequency.WEEKLY)

    # Horaires
    preferred_send_time: Mapped[str | None] = mapped_column(String(5), nullable=True)  # HH:MM
    timezone: Mapped[str | None] = mapped_column(String(50), default="Europe/Paris")

    # Exclusions
    excluded_content_types: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    excluded_broadcasts: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # IDs de broadcasts exclus

    # État
    is_unsubscribed_all: Mapped[bool | None] = mapped_column(Boolean, default=False)
    unsubscribed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_broadcast_preferences_tenant_user", "tenant_id", "user_id", unique=True),
    )


# ============================================================================
# MODÈLE: MÉTRIQUES DE DIFFUSION
# ============================================================================

class BroadcastMetric(Base):
    """Métriques agrégées de diffusion"""
    __tablename__ = "broadcast_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Période
    metric_date: Mapped[datetime] = mapped_column(DateTime)
    period_type: Mapped[str | None] = mapped_column(String(20), default="DAILY")  # DAILY, WEEKLY, MONTHLY

    # Volumes
    total_broadcasts: Mapped[int | None] = mapped_column(Integer, default=0)
    total_executions: Mapped[int | None] = mapped_column(Integer, default=0)
    total_messages: Mapped[int | None] = mapped_column(Integer, default=0)

    # Par type
    digest_count: Mapped[int | None] = mapped_column(Integer, default=0)
    newsletter_count: Mapped[int | None] = mapped_column(Integer, default=0)
    report_count: Mapped[int | None] = mapped_column(Integer, default=0)
    alert_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # Par canal
    email_count: Mapped[int | None] = mapped_column(Integer, default=0)
    in_app_count: Mapped[int | None] = mapped_column(Integer, default=0)
    webhook_count: Mapped[int | None] = mapped_column(Integer, default=0)
    sms_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # Taux de succès
    delivered_count: Mapped[int | None] = mapped_column(Integer, default=0)
    failed_count: Mapped[int | None] = mapped_column(Integer, default=0)
    bounced_count: Mapped[int | None] = mapped_column(Integer, default=0)
    delivery_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Engagement
    opened_count: Mapped[int | None] = mapped_column(Integer, default=0)
    clicked_count: Mapped[int | None] = mapped_column(Integer, default=0)
    unsubscribed_count: Mapped[int | None] = mapped_column(Integer, default=0)
    open_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    click_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_broadcast_metrics_tenant_date", "tenant_id", "metric_date"),
        Index("ix_broadcast_metrics_period", "tenant_id", "period_type", "metric_date"),
    )
