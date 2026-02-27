"""
AZALS MODULE NOTIFICATIONS - Exceptions
========================================

Exceptions metier specifiques au module de notifications.
"""

from typing import Optional, List
from uuid import UUID


class NotificationError(Exception):
    """Exception de base du module Notifications."""

    def __init__(self, message: str, tenant_id: Optional[UUID] = None):
        self.message = message
        self.tenant_id = tenant_id
        super().__init__(self.message)


# ============================================================================
# NOTIFICATION ERRORS
# ============================================================================

class NotificationNotFoundError(NotificationError):
    """Notification non trouvee."""

    def __init__(self, notification_id: Optional[str] = None):
        self.notification_id = notification_id
        super().__init__(f"Notification {notification_id} non trouvee")


class NotificationAlreadySentError(NotificationError):
    """Notification deja envoyee."""

    def __init__(self, notification_id: str):
        self.notification_id = notification_id
        super().__init__(f"La notification {notification_id} a deja ete envoyee")


class NotificationValidationError(NotificationError):
    """Erreur de validation de la notification."""

    def __init__(self, message: str, errors: Optional[List[str]] = None):
        self.errors = errors or []
        super().__init__(message)


# ============================================================================
# CHANNEL ERRORS
# ============================================================================

class ChannelNotConfiguredError(NotificationError):
    """Canal de notification non configure."""

    def __init__(self, channel: str):
        self.channel = channel
        super().__init__(f"Le canal {channel} n'est pas configure")


class ChannelSendError(NotificationError):
    """Erreur lors de l'envoi via un canal."""

    def __init__(self, channel: str, reason: str):
        self.channel = channel
        self.reason = reason
        super().__init__(f"Erreur d'envoi via {channel}: {reason}")


class EmailSendError(ChannelSendError):
    """Erreur lors de l'envoi d'email."""

    def __init__(self, reason: str, recipient: Optional[str] = None):
        self.recipient = recipient
        super().__init__("email", reason)


class SMSSendError(ChannelSendError):
    """Erreur lors de l'envoi de SMS."""

    def __init__(self, reason: str, recipient: Optional[str] = None):
        self.recipient = recipient
        super().__init__("sms", reason)


class PushSendError(ChannelSendError):
    """Erreur lors de l'envoi de notification push."""

    def __init__(self, reason: str, device_id: Optional[str] = None):
        self.device_id = device_id
        super().__init__("push", reason)


class WebhookSendError(ChannelSendError):
    """Erreur lors de l'envoi de webhook."""

    def __init__(self, reason: str, url: Optional[str] = None, status_code: Optional[int] = None):
        self.url = url
        self.status_code = status_code
        super().__init__("webhook", reason)


# ============================================================================
# TEMPLATE ERRORS
# ============================================================================

class TemplateNotFoundError(NotificationError):
    """Template de notification non trouve."""

    def __init__(self, template_id: Optional[str] = None, template_code: Optional[str] = None):
        self.template_id = template_id
        self.template_code = template_code
        identifier = template_code or template_id
        super().__init__(f"Template {identifier} non trouve")


class TemplateRenderError(NotificationError):
    """Erreur lors du rendu du template."""

    def __init__(self, template_code: str, reason: str):
        self.template_code = template_code
        self.reason = reason
        super().__init__(f"Erreur de rendu du template {template_code}: {reason}")


# ============================================================================
# RECIPIENT ERRORS
# ============================================================================

class RecipientNotFoundError(NotificationError):
    """Destinataire non trouve."""

    def __init__(self, recipient_id: Optional[str] = None):
        self.recipient_id = recipient_id
        super().__init__(f"Destinataire {recipient_id} non trouve")


class RecipientInvalidError(NotificationError):
    """Informations du destinataire invalides."""

    def __init__(self, channel: str, reason: str):
        self.channel = channel
        self.reason = reason
        super().__init__(f"Destinataire invalide pour {channel}: {reason}")


# ============================================================================
# PREFERENCE ERRORS
# ============================================================================

class PreferenceNotFoundError(NotificationError):
    """Preferences de notification non trouvees."""

    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id
        super().__init__(f"Preferences de notification non trouvees pour {user_id}")


class NotificationBlockedError(NotificationError):
    """Notification bloquee par les preferences utilisateur."""

    def __init__(self, user_id: str, channel: str, notification_type: str):
        self.user_id = user_id
        self.channel = channel
        self.notification_type = notification_type
        super().__init__(
            f"Notification {notification_type} bloquee pour {user_id} "
            f"via {channel}"
        )


# ============================================================================
# RETRY ERRORS
# ============================================================================

class MaxRetriesExceededError(NotificationError):
    """Nombre maximum de tentatives atteint."""

    def __init__(self, notification_id: str, max_retries: int):
        self.notification_id = notification_id
        self.max_retries = max_retries
        super().__init__(
            f"Notification {notification_id}: {max_retries} tentatives echouees"
        )
