"""
AZALS MODULE 18 - Mobile App Schemas
=====================================
Schémas Pydantic pour le backend mobile.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# DEVICE SCHEMAS
# ============================================================================

class DeviceRegister(BaseModel):
    """Enregistrement appareil."""
    device_id: str = Field(..., max_length=255)
    device_name: str | None = None
    platform: str = Field(..., max_length=20)
    os_version: str | None = None
    app_version: str | None = None
    model: str | None = None
    push_token: str | None = None


class DeviceUpdate(BaseModel):
    """Mise à jour appareil."""
    device_name: str | None = None
    push_token: str | None = None
    push_enabled: bool | None = None
    app_version: str | None = None


class DeviceResponse(BaseModel):
    """Réponse appareil."""
    id: int
    device_id: str
    device_name: str | None
    platform: str
    os_version: str | None
    app_version: str | None
    model: str | None
    push_enabled: bool
    is_trusted: bool
    is_active: bool
    last_active: datetime | None
    registered_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SESSION SCHEMAS
# ============================================================================

class SessionCreate(BaseModel):
    """Création session."""
    device_id: str


class SessionResponse(BaseModel):
    """Réponse session."""
    session_token: str
    refresh_token: str | None
    expires_at: datetime
    device_id: int


class SessionRefresh(BaseModel):
    """Refresh token."""
    refresh_token: str


# ============================================================================
# NOTIFICATION SCHEMAS
# ============================================================================

class NotificationCreate(BaseModel):
    """Création notification."""
    user_id: int
    title: str = Field(..., max_length=255)
    body: str | None = None
    image_url: str | None = None
    notification_type: str = "info"
    category: str | None = None
    priority: str = "normal"
    data: dict[str, Any] | None = None
    action_url: str | None = None
    scheduled_at: datetime | None = None


class NotificationBulk(BaseModel):
    """Notification en masse."""
    user_ids: list[int]
    title: str
    body: str | None = None
    notification_type: str = "info"
    data: dict[str, Any] | None = None


class NotificationResponse(BaseModel):
    """Réponse notification."""
    id: int
    title: str
    body: str | None
    notification_type: str
    category: str | None
    priority: str
    status: str
    data: dict[str, Any] | None
    action_url: str | None
    sent_at: datetime | None
    read_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SYNC SCHEMAS
# ============================================================================

class SyncRequest(BaseModel):
    """Requête sync."""
    entity_type: str
    since_version: int | None = 0
    limit: int = 100


class SyncItem(BaseModel):
    """Item à synchroniser."""
    entity_type: str
    entity_id: str | None = None
    operation: str  # create, update, delete
    data: dict[str, Any]
    local_version: int = 1


class SyncBatch(BaseModel):
    """Batch de sync."""
    items: list[SyncItem]
    device_id: str | None = None


class SyncResponse(BaseModel):
    """Réponse sync."""
    entity_type: str
    items: list[dict[str, Any]]
    version: int
    has_more: bool


class SyncConflict(BaseModel):
    """Conflit de sync."""
    entity_type: str
    entity_id: str
    local_data: dict[str, Any]
    server_data: dict[str, Any]
    resolution: str  # local, server, merge


# ============================================================================
# PREFERENCES SCHEMAS
# ============================================================================

class PreferencesUpdate(BaseModel):
    """Mise à jour préférences."""
    push_enabled: bool | None = None
    push_sound: bool | None = None
    push_vibrate: bool | None = None
    quiet_hours_enabled: bool | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    notify_orders: bool | None = None
    notify_messages: bool | None = None
    notify_reminders: bool | None = None
    notify_promotions: bool | None = None
    theme: str | None = None
    language: str | None = None
    font_size: str | None = None
    auto_sync: bool | None = None
    sync_on_wifi_only: bool | None = None
    biometric_login: bool | None = None
    auto_lock_minutes: int | None = None
    custom_settings: dict[str, Any] | None = None


class PreferencesResponse(BaseModel):
    """Réponse préférences."""
    push_enabled: bool
    push_sound: bool
    push_vibrate: bool
    quiet_hours_enabled: bool
    quiet_hours_start: str | None
    quiet_hours_end: str | None
    notify_orders: bool
    notify_messages: bool
    notify_reminders: bool
    theme: str
    language: str
    font_size: str
    auto_sync: bool
    sync_on_wifi_only: bool
    biometric_login: bool
    auto_lock_minutes: int
    custom_settings: dict[str, Any] | None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ACTIVITY SCHEMAS
# ============================================================================

class ActivityLog(BaseModel):
    """Log d'activité."""
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    screen: str | None = None
    duration_ms: int | None = None
    details: dict[str, Any] | None = None
    latitude: str | None = None
    longitude: str | None = None
    connection_type: str | None = None


class ActivityBatch(BaseModel):
    """Batch d'activités."""
    activities: list[ActivityLog]


# ============================================================================
# CONFIG SCHEMAS
# ============================================================================

class AppConfigResponse(BaseModel):
    """Configuration app."""
    min_version: str
    current_version: str
    force_update: bool
    update_message: str | None
    maintenance_mode: bool
    maintenance_message: str | None
    features_enabled: dict[str, bool]
    sync_interval_minutes: int
    session_timeout_hours: int
    branding: dict[str, Any] | None


# ============================================================================
# CRASH REPORT SCHEMAS
# ============================================================================

class CrashReport(BaseModel):
    """Rapport de crash."""
    error_type: str
    error_message: str
    stack_trace: str | None = None
    app_version: str
    os_version: str
    platform: str
    device_model: str | None = None
    screen: str | None = None
    last_action: str | None = None
    memory_usage: int | None = None
    battery_level: int | None = None
    console_logs: str | None = None
    breadcrumbs: list[dict[str, Any]] | None = None


# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================

class MobileStats(BaseModel):
    """Statistiques mobile."""
    total_devices: int = 0
    active_devices: int = 0
    total_sessions: int = 0
    active_sessions: int = 0
    notifications_sent: int = 0
    notifications_read_rate: float = 0.0
    sync_pending: int = 0
    crashes_today: int = 0
    devices_by_platform: dict[str, int] = {}
    devices_by_version: dict[str, int] = {}
