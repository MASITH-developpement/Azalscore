"""
AZALS MODULE 18 - Mobile App Models
====================================
Modèles SQLAlchemy pour le backend mobile.
"""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Index, JSON, BigInteger
)
from sqlalchemy.orm import relationship

from app.core.database import Base


# ============================================================================
# ENUMS
# ============================================================================

class DevicePlatform(str, PyEnum):
    """Plateforme mobile."""
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


class NotificationStatus(str, PyEnum):
    """Statut notification."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class SyncStatus(str, PyEnum):
    """Statut synchronisation."""
    PENDING = "pending"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"


# ============================================================================
# DEVICES
# ============================================================================

class MobileDevice(Base):
    """Appareil mobile enregistré."""
    __tablename__ = "mobile_devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # Identification appareil
    device_id = Column(String(255), nullable=False)  # UUID unique
    device_name = Column(String(255))
    platform = Column(String(20), nullable=False)  # ios, android, web
    os_version = Column(String(50))
    app_version = Column(String(50))
    model = Column(String(100))  # iPhone 14, Galaxy S23

    # Push notifications
    push_token = Column(String(500))
    push_enabled = Column(Boolean, default=True)
    push_provider = Column(String(50))  # fcm, apns

    # Sécurité
    is_trusted = Column(Boolean, default=False)
    biometric_enabled = Column(Boolean, default=False)
    pin_enabled = Column(Boolean, default=False)
    last_security_check = Column(DateTime)

    # État
    is_active = Column(Boolean, default=True)
    last_active = Column(DateTime)
    last_ip = Column(String(50))
    last_location = Column(JSON)  # {lat, lng, city}

    # Métadonnées
    extra_data = Column(JSON)  # Infos supplémentaires
    registered_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    sessions = relationship("MobileSession", back_populates="device", cascade="all, delete-orphan")
    notifications = relationship("PushNotification", back_populates="device")

    __table_args__ = (
        Index('idx_mobile_device_tenant', 'tenant_id'),
        Index('idx_mobile_device_user', 'tenant_id', 'user_id'),
        Index('idx_mobile_device_id', 'device_id', unique=True),
    )


# ============================================================================
# SESSIONS
# ============================================================================

class MobileSession(Base):
    """Session mobile."""
    __tablename__ = "mobile_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("mobile_devices.id"), nullable=False)

    # Token
    session_token = Column(String(500), nullable=False, unique=True)
    refresh_token = Column(String(500))

    # Validité
    expires_at = Column(DateTime, nullable=False)
    refresh_expires_at = Column(DateTime)

    # État
    is_active = Column(Boolean, default=True)
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime)
    revoked_reason = Column(String(255))

    # Activité
    last_activity = Column(DateTime, default=datetime.utcnow)
    last_ip = Column(String(50))

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    device = relationship("MobileDevice", back_populates="sessions")

    __table_args__ = (
        Index('idx_mobile_session_tenant', 'tenant_id'),
        Index('idx_mobile_session_user', 'user_id'),
        Index('idx_mobile_session_token', 'session_token'),
    )


# ============================================================================
# PUSH NOTIFICATIONS
# ============================================================================

class PushNotification(Base):
    """Notification push."""
    __tablename__ = "mobile_notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Destinataire
    user_id = Column(Integer, nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("mobile_devices.id"))

    # Contenu
    title = Column(String(255), nullable=False)
    body = Column(Text)
    image_url = Column(String(500))

    # Catégorisation
    notification_type = Column(String(50), nullable=False)  # alert, info, reminder, action
    category = Column(String(50))  # order, message, system
    priority = Column(String(20), default="normal")  # low, normal, high, critical

    # Payload
    data = Column(JSON)  # Données supplémentaires
    action_url = Column(String(500))  # Deep link

    # Statut
    status = Column(String(20), default="pending")
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    failed_reason = Column(Text)

    # Provider
    provider = Column(String(50))  # fcm, apns
    provider_message_id = Column(String(255))

    # Planification
    scheduled_at = Column(DateTime)
    expires_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    device = relationship("MobileDevice", back_populates="notifications")

    __table_args__ = (
        Index('idx_mobile_notif_tenant', 'tenant_id'),
        Index('idx_mobile_notif_user', 'user_id'),
        Index('idx_mobile_notif_status', 'tenant_id', 'status'),
        Index('idx_mobile_notif_type', 'tenant_id', 'notification_type'),
    )


# ============================================================================
# SYNC DATA
# ============================================================================

class SyncQueue(Base):
    """File de synchronisation offline."""
    __tablename__ = "mobile_sync_queue"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("mobile_devices.id"))

    # Opération
    entity_type = Column(String(100), nullable=False)  # order, customer, etc.
    entity_id = Column(String(100))
    operation = Column(String(20), nullable=False)  # create, update, delete
    data = Column(JSON)  # Données à synchroniser

    # Versioning
    local_version = Column(Integer, default=1)
    server_version = Column(Integer)

    # Statut
    status = Column(String(20), default="pending")
    sync_attempts = Column(Integer, default=0)
    last_attempt = Column(DateTime)
    error_message = Column(Text)

    # Conflit
    has_conflict = Column(Boolean, default=False)
    conflict_data = Column(JSON)
    conflict_resolved = Column(Boolean, default=False)

    # Priorité
    priority = Column(Integer, default=0)  # 0=normal, 1=high, 2=critical

    created_at = Column(DateTime, default=datetime.utcnow)
    synced_at = Column(DateTime)

    __table_args__ = (
        Index('idx_sync_queue_tenant', 'tenant_id'),
        Index('idx_sync_queue_user', 'user_id'),
        Index('idx_sync_queue_status', 'tenant_id', 'status'),
        Index('idx_sync_queue_entity', 'tenant_id', 'entity_type', 'entity_id'),
    )


class SyncCheckpoint(Base):
    """Point de synchronisation par entité."""
    __tablename__ = "mobile_sync_checkpoints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("mobile_devices.id"))

    # Entité
    entity_type = Column(String(100), nullable=False)

    # Dernière sync
    last_sync_at = Column(DateTime)
    last_sync_version = Column(BigInteger, default=0)
    last_sync_token = Column(String(255))

    # Stats
    total_synced = Column(Integer, default=0)
    last_sync_count = Column(Integer, default=0)
    last_sync_duration = Column(Integer)  # ms

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_sync_checkpoint_tenant', 'tenant_id'),
        Index('idx_sync_checkpoint_user_entity', 'user_id', 'entity_type', unique=True),
    )


# ============================================================================
# USER PREFERENCES
# ============================================================================

class MobilePreferences(Base):
    """Préférences utilisateur mobile."""
    __tablename__ = "mobile_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # Notifications
    push_enabled = Column(Boolean, default=True)
    push_sound = Column(Boolean, default=True)
    push_vibrate = Column(Boolean, default=True)
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(5))  # "22:00"
    quiet_hours_end = Column(String(5))  # "07:00"

    # Catégories de notifications
    notify_orders = Column(Boolean, default=True)
    notify_messages = Column(Boolean, default=True)
    notify_reminders = Column(Boolean, default=True)
    notify_promotions = Column(Boolean, default=False)
    notify_system = Column(Boolean, default=True)

    # Affichage
    theme = Column(String(20), default="system")  # light, dark, system
    language = Column(String(10), default="fr")
    font_size = Column(String(20), default="medium")  # small, medium, large

    # Comportement
    auto_sync = Column(Boolean, default=True)
    sync_on_wifi_only = Column(Boolean, default=False)
    offline_mode = Column(Boolean, default=False)
    data_saver = Column(Boolean, default=False)

    # Sécurité
    biometric_login = Column(Boolean, default=False)
    auto_lock_minutes = Column(Integer, default=5)
    show_preview = Column(Boolean, default=True)

    # Cache
    cache_size_mb = Column(Integer, default=100)
    cache_images = Column(Boolean, default=True)
    cache_documents = Column(Boolean, default=False)

    # Personnalisé
    custom_settings = Column(JSON)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_mobile_prefs_tenant', 'tenant_id'),
        Index('idx_mobile_prefs_user', 'tenant_id', 'user_id', unique=True),
    )


# ============================================================================
# ACTIVITY LOG
# ============================================================================

class MobileActivityLog(Base):
    """Log d'activité mobile."""
    __tablename__ = "mobile_activity_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("mobile_devices.id"))
    session_id = Column(Integer, ForeignKey("mobile_sessions.id"))

    # Action
    action = Column(String(100), nullable=False)  # login, logout, view, create, etc.
    resource_type = Column(String(100))  # order, customer, product
    resource_id = Column(String(100))

    # Contexte
    screen = Column(String(100))  # Écran actuel
    previous_screen = Column(String(100))
    duration_ms = Column(Integer)  # Durée sur l'écran

    # Détails
    details = Column(JSON)

    # Géolocalisation
    latitude = Column(String(20))
    longitude = Column(String(20))

    # Réseau
    connection_type = Column(String(20))  # wifi, 4g, 5g
    ip_address = Column(String(50))

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_mobile_activity_tenant', 'tenant_id'),
        Index('idx_mobile_activity_user', 'user_id'),
        Index('idx_mobile_activity_action', 'tenant_id', 'action'),
        Index('idx_mobile_activity_date', 'tenant_id', 'created_at'),
    )


# ============================================================================
# APP CONFIG
# ============================================================================

class MobileAppConfig(Base):
    """Configuration application mobile."""
    __tablename__ = "mobile_app_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Version
    min_ios_version = Column(String(20))
    min_android_version = Column(String(20))
    current_version = Column(String(20))
    force_update = Column(Boolean, default=False)
    update_message = Column(Text)
    store_url_ios = Column(String(500))
    store_url_android = Column(String(500))

    # Maintenance
    maintenance_mode = Column(Boolean, default=False)
    maintenance_message = Column(Text)
    maintenance_end = Column(DateTime)

    # Fonctionnalités
    features_enabled = Column(JSON)  # {"feature_name": true/false}
    features_config = Column(JSON)  # Configuration par fonctionnalité

    # API
    api_timeout_ms = Column(Integer, default=30000)
    sync_interval_minutes = Column(Integer, default=15)
    max_offline_days = Column(Integer, default=7)

    # Limites
    max_devices_per_user = Column(Integer, default=5)
    max_sessions_per_device = Column(Integer, default=1)
    session_timeout_hours = Column(Integer, default=24)

    # Sécurité
    require_biometric = Column(Boolean, default=False)
    require_pin = Column(Boolean, default=False)
    allow_screenshots = Column(Boolean, default=True)
    allow_copy_paste = Column(Boolean, default=True)

    # Analytics
    analytics_enabled = Column(Boolean, default=True)
    crash_reporting = Column(Boolean, default=True)
    performance_monitoring = Column(Boolean, default=True)

    # Personnalisation
    branding = Column(JSON)  # {logo_url, colors, fonts}
    onboarding = Column(JSON)  # Configuration onboarding

    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_mobile_config_tenant', 'tenant_id', unique=True),
    )


# ============================================================================
# CRASH REPORTS
# ============================================================================

class MobileCrashReport(Base):
    """Rapport de crash mobile."""
    __tablename__ = "mobile_crash_reports"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, index=True)
    device_id = Column(Integer, ForeignKey("mobile_devices.id"))

    # Crash info
    crash_id = Column(String(100), unique=True)
    error_type = Column(String(255))
    error_message = Column(Text)
    stack_trace = Column(Text)

    # Contexte
    app_version = Column(String(50))
    os_version = Column(String(50))
    platform = Column(String(20))
    device_model = Column(String(100))

    # État app
    screen = Column(String(100))
    last_action = Column(String(255))
    memory_usage = Column(Integer)
    battery_level = Column(Integer)
    is_background = Column(Boolean)

    # Réseau
    connection_type = Column(String(20))
    connection_quality = Column(String(20))

    # Logs
    console_logs = Column(Text)
    breadcrumbs = Column(JSON)  # Actions avant le crash

    # Résolution
    is_resolved = Column(Boolean, default=False)
    resolved_in_version = Column(String(50))
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_crash_tenant', 'tenant_id'),
        Index('idx_crash_user', 'user_id'),
        Index('idx_crash_version', 'tenant_id', 'app_version'),
        Index('idx_crash_type', 'tenant_id', 'error_type'),
    )
