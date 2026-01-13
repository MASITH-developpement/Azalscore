"""
AZALS MODULE 18 - Mobile App Backend
=====================================
Backend pour applications mobiles iOS/Android.

Fonctionnalités:
- Gestion des appareils mobiles
- Sessions et authentification mobile
- Push notifications (FCM/APNS)
- Synchronisation offline
- Préférences utilisateur
- Logs d'activité
- Configuration app
- Rapports de crash
"""

from .models import (
    DevicePlatform,
    MobileActivityLog,
    MobileAppConfig,
    MobileCrashReport,
    MobileDevice,
    MobilePreferences,
    MobileSession,
    NotificationStatus,
    PushNotification,
    SyncCheckpoint,
    SyncQueue,
    SyncStatus,
)
from .router import router
from .schemas import (
    ActivityBatch,
    ActivityLog,
    AppConfigResponse,
    CrashReport,
    DeviceRegister,
    DeviceResponse,
    DeviceUpdate,
    MobileStats,
    NotificationBulk,
    NotificationCreate,
    NotificationResponse,
    PreferencesResponse,
    PreferencesUpdate,
    SessionCreate,
    SessionRefresh,
    SessionResponse,
    SyncBatch,
    SyncConflict,
    SyncItem,
    SyncRequest,
    SyncResponse,
)
from .service import MobileService

__all__ = [
    # Models
    "MobileDevice",
    "MobileSession",
    "PushNotification",
    "SyncQueue",
    "SyncCheckpoint",
    "MobilePreferences",
    "MobileActivityLog",
    "MobileAppConfig",
    "MobileCrashReport",
    # Enums
    "DevicePlatform",
    "NotificationStatus",
    "SyncStatus",
    # Schemas
    "DeviceRegister",
    "DeviceUpdate",
    "DeviceResponse",
    "SessionCreate",
    "SessionResponse",
    "SessionRefresh",
    "NotificationCreate",
    "NotificationBulk",
    "NotificationResponse",
    "SyncRequest",
    "SyncItem",
    "SyncBatch",
    "SyncResponse",
    "SyncConflict",
    "PreferencesUpdate",
    "PreferencesResponse",
    "ActivityLog",
    "ActivityBatch",
    "AppConfigResponse",
    "CrashReport",
    "MobileStats",
    # Service
    "MobileService",
    # Router
    "router"
]
