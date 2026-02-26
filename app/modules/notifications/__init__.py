"""
Module Notifications - GAP-046

Gestion multicanal des notifications:
- Email, SMS, Push, In-app
- Templates multilingues
- Préférences utilisateur
- Heures calmes
- Webhooks
- Batch et scheduling
- Statistiques
"""

from .service import (
    # Énumérations
    NotificationChannel,
    NotificationStatus,
    NotificationPriority,
    NotificationType,
    TemplateStatus,

    # Data classes
    NotificationTemplate,
    UserPreferences,
    Notification,
    NotificationBatch,
    WebhookSubscription,
    NotificationStats,

    # Service
    NotificationService,
    create_notification_service,
)

__all__ = [
    "NotificationChannel",
    "NotificationStatus",
    "NotificationPriority",
    "NotificationType",
    "TemplateStatus",
    "NotificationTemplate",
    "UserPreferences",
    "Notification",
    "NotificationBatch",
    "WebhookSubscription",
    "NotificationStats",
    "NotificationService",
    "create_notification_service",
]
