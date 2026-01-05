"""
AZALS MODULE T6 - Modèles Diffusion Périodique
==============================================

Modèles SQLAlchemy pour la gestion des diffusions automatiques.
"""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float,
    ForeignKey, Enum, Index, JSON
)
from app.core.database import Base


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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Type et contenu
    content_type = Column(Enum(ContentType), nullable=False)
    subject_template = Column(String(500), nullable=True)
    body_template = Column(Text, nullable=True)
    html_template = Column(Text, nullable=True)

    # Configuration
    default_channel = Column(Enum(DeliveryChannel), default=DeliveryChannel.EMAIL)
    available_channels = Column(JSON, nullable=True)  # Liste des canaux supportés
    variables = Column(JSON, nullable=True)  # Variables disponibles
    styling = Column(JSON, nullable=True)  # CSS et mise en forme

    # Data sources
    data_sources = Column(JSON, nullable=True)  # Sources de données à agréger
    aggregation_config = Column(JSON, nullable=True)  # Config d'agrégation

    # Localisation
    language = Column(String(5), default="fr")
    country_code = Column(String(2), nullable=True)

    # État
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, nullable=True)

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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Configuration
    is_dynamic = Column(Boolean, default=False)  # Liste dynamique (requête)
    query_config = Column(JSON, nullable=True)  # Config pour listes dynamiques

    # Statistiques
    total_recipients = Column(Integer, default=0)
    active_recipients = Column(Integer, default=0)

    # État
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_recipient_lists_tenant_code", "tenant_id", "code", unique=True),
    )


# ============================================================================
# MODÈLE: MEMBRE D'UNE LISTE
# ============================================================================

class RecipientMember(Base):
    """Membre d'une liste de destinataires"""
    __tablename__ = "broadcast_recipient_members"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    list_id = Column(Integer, ForeignKey("broadcast_recipient_lists.id"), nullable=False)

    # Type et référence
    recipient_type = Column(Enum(RecipientType), nullable=False)
    user_id = Column(Integer, nullable=True)  # Pour USER
    group_id = Column(Integer, nullable=True)  # Pour GROUP
    role_code = Column(String(50), nullable=True)  # Pour ROLE
    external_email = Column(String(255), nullable=True)  # Pour EXTERNAL
    external_name = Column(String(200), nullable=True)

    # Préférences
    preferred_channel = Column(Enum(DeliveryChannel), nullable=True)
    preferred_language = Column(String(5), nullable=True)
    preferred_format = Column(String(20), nullable=True)  # HTML, TEXT, PDF

    # État
    is_active = Column(Boolean, default=True)
    is_unsubscribed = Column(Boolean, default=False)
    unsubscribed_at = Column(DateTime, nullable=True)

    # Audit
    added_at = Column(DateTime, default=datetime.utcnow)
    added_by = Column(Integer, nullable=True)

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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Template et destinataires
    template_id = Column(Integer, ForeignKey("broadcast_templates.id"), nullable=True)
    recipient_list_id = Column(Integer, ForeignKey("broadcast_recipient_lists.id"), nullable=True)

    # Contenu personnalisé (si pas de template)
    content_type = Column(Enum(ContentType), nullable=False)
    subject = Column(String(500), nullable=True)
    body_content = Column(Text, nullable=True)
    html_content = Column(Text, nullable=True)

    # Configuration livraison
    delivery_channel = Column(Enum(DeliveryChannel), nullable=False, default=DeliveryChannel.EMAIL)
    additional_channels = Column(JSON, nullable=True)

    # Planification
    frequency = Column(Enum(BroadcastFrequency), nullable=False)
    cron_expression = Column(String(100), nullable=True)  # Pour CUSTOM
    timezone = Column(String(50), default="Europe/Paris")

    # Fenêtre de diffusion
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    send_time = Column(String(5), nullable=True)  # HH:MM

    # Pour fréquence spécifique
    day_of_week = Column(Integer, nullable=True)  # 0-6 pour WEEKLY
    day_of_month = Column(Integer, nullable=True)  # 1-31 pour MONTHLY
    month_of_year = Column(Integer, nullable=True)  # 1-12 pour YEARLY

    # Data dynamique
    data_query = Column(JSON, nullable=True)  # Requête pour données
    data_filters = Column(JSON, nullable=True)  # Filtres

    # État
    status = Column(Enum(BroadcastStatus), default=BroadcastStatus.DRAFT)
    is_active = Column(Boolean, default=True)

    # Statistiques
    total_sent = Column(Integer, default=0)
    total_delivered = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    total_opened = Column(Integer, default=0)
    total_clicked = Column(Integer, default=0)

    # Exécution
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, nullable=True)

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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    scheduled_broadcast_id = Column(Integer, ForeignKey("scheduled_broadcasts.id"), nullable=False)

    # Exécution
    execution_number = Column(Integer, default=1)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Résultats
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING)
    total_recipients = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    bounced_count = Column(Integer, default=0)

    # Contenu généré
    generated_subject = Column(String(500), nullable=True)
    generated_content = Column(Text, nullable=True)
    attachments = Column(JSON, nullable=True)

    # Erreurs
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    # Métriques engagement
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    unsubscribed_count = Column(Integer, default=0)

    # Audit
    triggered_by = Column(String(50), default="scheduler")  # scheduler, manual, api
    triggered_user = Column(Integer, nullable=True)

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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    execution_id = Column(Integer, ForeignKey("broadcast_executions.id"), nullable=False)

    # Destinataire
    recipient_type = Column(Enum(RecipientType), nullable=False)
    user_id = Column(Integer, nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)

    # Livraison
    channel = Column(Enum(DeliveryChannel), nullable=False)
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING)

    # Timing
    queued_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    # Engagement
    opened_at = Column(DateTime, nullable=True)
    opened_count = Column(Integer, default=0)
    clicked_at = Column(DateTime, nullable=True)
    click_count = Column(Integer, default=0)

    # Erreurs
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime, nullable=True)

    # Tracking
    tracking_id = Column(String(100), nullable=True)  # UUID pour tracking
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)

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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, nullable=False)

    # Préférences globales
    receive_digests = Column(Boolean, default=True)
    receive_newsletters = Column(Boolean, default=True)
    receive_reports = Column(Boolean, default=True)
    receive_alerts = Column(Boolean, default=True)

    # Canal préféré
    preferred_channel = Column(Enum(DeliveryChannel), default=DeliveryChannel.EMAIL)
    preferred_language = Column(String(5), default="fr")
    preferred_format = Column(String(20), default="HTML")  # HTML, TEXT, PDF

    # Fréquence
    digest_frequency = Column(Enum(BroadcastFrequency), default=BroadcastFrequency.DAILY)
    report_frequency = Column(Enum(BroadcastFrequency), default=BroadcastFrequency.WEEKLY)

    # Horaires
    preferred_send_time = Column(String(5), nullable=True)  # HH:MM
    timezone = Column(String(50), default="Europe/Paris")

    # Exclusions
    excluded_content_types = Column(JSON, nullable=True)
    excluded_broadcasts = Column(JSON, nullable=True)  # IDs de broadcasts exclus

    # État
    is_unsubscribed_all = Column(Boolean, default=False)
    unsubscribed_at = Column(DateTime, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_broadcast_preferences_tenant_user", "tenant_id", "user_id", unique=True),
    )


# ============================================================================
# MODÈLE: MÉTRIQUES DE DIFFUSION
# ============================================================================

class BroadcastMetric(Base):
    """Métriques agrégées de diffusion"""
    __tablename__ = "broadcast_metrics"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Période
    metric_date = Column(DateTime, nullable=False)
    period_type = Column(String(20), default="DAILY")  # DAILY, WEEKLY, MONTHLY

    # Volumes
    total_broadcasts = Column(Integer, default=0)
    total_executions = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)

    # Par type
    digest_count = Column(Integer, default=0)
    newsletter_count = Column(Integer, default=0)
    report_count = Column(Integer, default=0)
    alert_count = Column(Integer, default=0)

    # Par canal
    email_count = Column(Integer, default=0)
    in_app_count = Column(Integer, default=0)
    webhook_count = Column(Integer, default=0)
    sms_count = Column(Integer, default=0)

    # Taux de succès
    delivered_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    bounced_count = Column(Integer, default=0)
    delivery_rate = Column(Float, nullable=True)

    # Engagement
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    unsubscribed_count = Column(Integer, default=0)
    open_rate = Column(Float, nullable=True)
    click_rate = Column(Float, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_broadcast_metrics_tenant_date", "tenant_id", "metric_date"),
        Index("ix_broadcast_metrics_period", "tenant_id", "period_type", "metric_date"),
    )
