"""
AZALS MODULE 18 - Mobile App Schemas
=====================================
Schémas Pydantic pour le backend mobile.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# DEVICE SCHEMAS
# ============================================================================

class DeviceRegister(BaseModel):
    """Enregistrement appareil."""
    device_id: str = Field(..., max_length=255)
    device_name: Optional[str] = None
    platform: str = Field(..., max_length=20)
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    model: Optional[str] = None
    push_token: Optional[str] = None


class DeviceUpdate(BaseModel):
    """Mise à jour appareil."""
    device_name: Optional[str] = None
    push_token: Optional[str] = None
    push_enabled: Optional[bool] = None
    app_version: Optional[str] = None


class DeviceResponse(BaseModel):
    """Réponse appareil."""
    id: int
    device_id: str
    device_name: Optional[str]
    platform: str
    os_version: Optional[str]
    app_version: Optional[str]
    model: Optional[str]
    push_enabled: bool
    is_trusted: bool
    is_active: bool
    last_active: Optional[datetime]
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
    refresh_token: Optional[str]
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
    body: Optional[str] = None
    image_url: Optional[str] = None
    notification_type: str = "info"
    category: Optional[str] = None
    priority: str = "normal"
    data: Optional[Dict[str, Any]] = None
    action_url: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class NotificationBulk(BaseModel):
    """Notification en masse."""
    user_ids: List[int]
    title: str
    body: Optional[str] = None
    notification_type: str = "info"
    data: Optional[Dict[str, Any]] = None


class NotificationResponse(BaseModel):
    """Réponse notification."""
    id: int
    title: str
    body: Optional[str]
    notification_type: str
    category: Optional[str]
    priority: str
    status: str
    data: Optional[Dict[str, Any]]
    action_url: Optional[str]
    sent_at: Optional[datetime]
    read_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SYNC SCHEMAS
# ============================================================================

class SyncRequest(BaseModel):
    """Requête sync."""
    entity_type: str
    since_version: Optional[int] = 0
    limit: int = 100


class SyncItem(BaseModel):
    """Item à synchroniser."""
    entity_type: str
    entity_id: Optional[str] = None
    operation: str  # create, update, delete
    data: Dict[str, Any]
    local_version: int = 1


class SyncBatch(BaseModel):
    """Batch de sync."""
    items: List[SyncItem]
    device_id: Optional[str] = None


class SyncResponse(BaseModel):
    """Réponse sync."""
    entity_type: str
    items: List[Dict[str, Any]]
    version: int
    has_more: bool


class SyncConflict(BaseModel):
    """Conflit de sync."""
    entity_type: str
    entity_id: str
    local_data: Dict[str, Any]
    server_data: Dict[str, Any]
    resolution: str  # local, server, merge


# ============================================================================
# PREFERENCES SCHEMAS
# ============================================================================

class PreferencesUpdate(BaseModel):
    """Mise à jour préférences."""
    push_enabled: Optional[bool] = None
    push_sound: Optional[bool] = None
    push_vibrate: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    notify_orders: Optional[bool] = None
    notify_messages: Optional[bool] = None
    notify_reminders: Optional[bool] = None
    notify_promotions: Optional[bool] = None
    theme: Optional[str] = None
    language: Optional[str] = None
    font_size: Optional[str] = None
    auto_sync: Optional[bool] = None
    sync_on_wifi_only: Optional[bool] = None
    biometric_login: Optional[bool] = None
    auto_lock_minutes: Optional[int] = None
    custom_settings: Optional[Dict[str, Any]] = None


class PreferencesResponse(BaseModel):
    """Réponse préférences."""
    push_enabled: bool
    push_sound: bool
    push_vibrate: bool
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
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
    custom_settings: Optional[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ACTIVITY SCHEMAS
# ============================================================================

class ActivityLog(BaseModel):
    """Log d'activité."""
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    screen: Optional[str] = None
    duration_ms: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    connection_type: Optional[str] = None


class ActivityBatch(BaseModel):
    """Batch d'activités."""
    activities: List[ActivityLog]


# ============================================================================
# CONFIG SCHEMAS
# ============================================================================

class AppConfigResponse(BaseModel):
    """Configuration app."""
    min_version: str
    current_version: str
    force_update: bool
    update_message: Optional[str]
    maintenance_mode: bool
    maintenance_message: Optional[str]
    features_enabled: Dict[str, bool]
    sync_interval_minutes: int
    session_timeout_hours: int
    branding: Optional[Dict[str, Any]]


# ============================================================================
# CRASH REPORT SCHEMAS
# ============================================================================

class CrashReport(BaseModel):
    """Rapport de crash."""
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    app_version: str
    os_version: str
    platform: str
    device_model: Optional[str] = None
    screen: Optional[str] = None
    last_action: Optional[str] = None
    memory_usage: Optional[int] = None
    battery_level: Optional[int] = None
    console_logs: Optional[str] = None
    breadcrumbs: Optional[List[Dict[str, Any]]] = None


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
    devices_by_platform: Dict[str, int] = {}
    devices_by_version: Dict[str, int] = {}
