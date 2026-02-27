"""
Service de Notifications - GAP-046

Gestion multicanal des notifications:
- Email (SMTP, SendGrid, Mailjet)
- SMS (Twilio, OVH)
- Push (Firebase, APNs)
- In-app (temps réel)
- Webhooks
- Templates multilingues
- Préférences utilisateur
- Historique et tracking
- Rate limiting
- Batch et scheduling
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4
import json
import logging
import re

from .exceptions import (
    ChannelSendError,
    EmailSendError,
    SMSSendError,
    PushSendError,
    WebhookSendError,
)

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Canal de notification."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"


class NotificationStatus(Enum):
    """Statut d'une notification."""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    BOUNCED = "bounced"
    CANCELLED = "cancelled"


class NotificationPriority(Enum):
    """Priorité de notification."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(Enum):
    """Type de notification."""
    TRANSACTIONAL = "transactional"  # Commande, facture, etc.
    SYSTEM = "system"  # Alertes système
    MARKETING = "marketing"  # Promotions
    REMINDER = "reminder"  # Rappels
    ALERT = "alert"  # Alertes métier
    WORKFLOW = "workflow"  # Actions workflow
    SOCIAL = "social"  # Interactions utilisateur


class TemplateStatus(Enum):
    """Statut d'un template."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass
class NotificationTemplate:
    """Template de notification."""
    template_id: str
    tenant_id: str
    code: str  # Identifiant unique (ex: "order_confirmation")
    name: str
    description: str
    notification_type: NotificationType
    status: TemplateStatus = TemplateStatus.DRAFT

    # Canaux supportés
    channels: List[NotificationChannel] = field(default_factory=list)

    # Contenu par canal
    email_subject: Optional[str] = None
    email_html: Optional[str] = None
    email_text: Optional[str] = None
    sms_text: Optional[str] = None
    push_title: Optional[str] = None
    push_body: Optional[str] = None
    push_data: Optional[Dict[str, Any]] = None
    in_app_title: Optional[str] = None
    in_app_body: Optional[str] = None
    in_app_icon: Optional[str] = None
    in_app_action_url: Optional[str] = None
    webhook_payload: Optional[Dict[str, Any]] = None
    slack_message: Optional[Dict[str, Any]] = None

    # Traductions
    translations: Dict[str, Dict[str, str]] = field(default_factory=dict)

    # Variables
    variables: List[str] = field(default_factory=list)
    variable_defaults: Dict[str, Any] = field(default_factory=dict)

    # Configuration
    default_priority: NotificationPriority = NotificationPriority.NORMAL
    expiry_hours: Optional[int] = None  # Expiration si non lu

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    updated_at: Optional[datetime] = None
    version: int = 1
    category: str = "general"
    tags: List[str] = field(default_factory=list)


@dataclass
class UserPreferences:
    """Préférences de notification utilisateur."""
    user_id: str
    tenant_id: str

    # Canaux activés
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    in_app_enabled: bool = True

    # Contacts
    email_address: Optional[str] = None
    phone_number: Optional[str] = None
    push_tokens: List[str] = field(default_factory=list)

    # Préférences par type
    type_preferences: Dict[str, Dict[str, bool]] = field(default_factory=dict)

    # Heures calmes (ne pas déranger)
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = None  # "22:00"
    quiet_hours_end: Optional[str] = None  # "07:00"
    quiet_hours_timezone: str = "Europe/Paris"

    # Fréquence
    digest_enabled: bool = False
    digest_frequency: str = "daily"  # daily, weekly
    digest_time: str = "09:00"

    # Langue
    language: str = "fr"

    # Désabonnements
    unsubscribed_templates: List[str] = field(default_factory=list)
    marketing_consent: bool = False
    marketing_consent_date: Optional[datetime] = None

    # Métadonnées
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Notification:
    """Notification individuelle."""
    notification_id: str
    tenant_id: str
    template_id: Optional[str]
    template_code: Optional[str]
    notification_type: NotificationType
    channel: NotificationChannel
    priority: NotificationPriority
    status: NotificationStatus

    # Destinataire
    user_id: Optional[str] = None
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    recipient_device_token: Optional[str] = None
    recipient_webhook_url: Optional[str] = None

    # Contenu
    subject: Optional[str] = None
    title: Optional[str] = None
    body: str = ""
    html_body: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

    # Variables utilisées
    variables: Dict[str, Any] = field(default_factory=dict)

    # Référence
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None

    # Scheduling
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Tracking
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None

    # Provider
    provider_id: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None

    # Retry
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: Optional[datetime] = None

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    batch_id: Optional[str] = None


@dataclass
class NotificationBatch:
    """Lot de notifications."""
    batch_id: str
    tenant_id: str
    template_id: str
    status: str = "pending"  # pending, processing, completed, failed

    # Destinataires
    recipients: List[Dict[str, Any]] = field(default_factory=list)
    total_recipients: int = 0

    # Progression
    processed_count: int = 0
    sent_count: int = 0
    failed_count: int = 0

    # Scheduling
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""


@dataclass
class WebhookSubscription:
    """Abonnement webhook."""
    subscription_id: str
    tenant_id: str
    name: str
    url: str
    secret: str  # Pour signature HMAC
    is_active: bool = True

    # Événements
    event_types: List[str] = field(default_factory=list)

    # Configuration
    headers: Dict[str, str] = field(default_factory=dict)
    retry_policy: Dict[str, Any] = field(default_factory=dict)

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    last_triggered_at: Optional[datetime] = None
    failure_count: int = 0


@dataclass
class NotificationStats:
    """Statistiques de notifications."""
    tenant_id: str
    period_start: datetime
    period_end: datetime

    total_sent: int = 0
    total_delivered: int = 0
    total_read: int = 0
    total_clicked: int = 0
    total_failed: int = 0
    total_bounced: int = 0

    by_channel: Dict[str, Dict[str, int]] = field(default_factory=dict)
    by_type: Dict[str, Dict[str, int]] = field(default_factory=dict)
    by_template: Dict[str, Dict[str, int]] = field(default_factory=dict)

    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0


class NotificationService:
    """Service de gestion des notifications."""

    def __init__(
        self,
        tenant_id: str,
        template_repository: Optional[Any] = None,
        notification_repository: Optional[Any] = None,
        preference_repository: Optional[Any] = None,
        email_provider: Optional[Callable] = None,
        sms_provider: Optional[Callable] = None,
        push_provider: Optional[Callable] = None,
        webhook_client: Optional[Callable] = None,
        rate_limiter: Optional[Any] = None
    ):
        self.tenant_id = tenant_id
        self.template_repo = template_repository or {}
        self.notification_repo = notification_repository or {}
        self.preference_repo = preference_repository or {}

        # Providers
        self.email_provider = email_provider
        self.sms_provider = sms_provider
        self.push_provider = push_provider
        self.webhook_client = webhook_client
        self.rate_limiter = rate_limiter

        # Caches
        self._templates: Dict[str, NotificationTemplate] = {}
        self._notifications: Dict[str, Notification] = {}
        self._preferences: Dict[str, UserPreferences] = {}
        self._batches: Dict[str, NotificationBatch] = {}
        self._webhooks: Dict[str, WebhookSubscription] = {}

        # Regex pour les variables
        self._variable_pattern = re.compile(r'\{\{([^}]+)\}\}')

    # =========================================================================
    # Templates
    # =========================================================================

    def create_template(
        self,
        code: str,
        name: str,
        notification_type: NotificationType,
        channels: List[NotificationChannel],
        **kwargs
    ) -> NotificationTemplate:
        """Crée un template de notification."""
        template_id = f"tpl_{uuid4().hex[:12]}"

        # Extraire les variables du contenu
        variables = set()
        for content_field in ["email_subject", "email_html", "email_text",
                              "sms_text", "push_title", "push_body",
                              "in_app_title", "in_app_body"]:
            content = kwargs.get(content_field)
            if content:
                found = self._variable_pattern.findall(content)
                variables.update(found)

        template = NotificationTemplate(
            template_id=template_id,
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            description=kwargs.get("description", ""),
            notification_type=notification_type,
            channels=channels,
            email_subject=kwargs.get("email_subject"),
            email_html=kwargs.get("email_html"),
            email_text=kwargs.get("email_text"),
            sms_text=kwargs.get("sms_text"),
            push_title=kwargs.get("push_title"),
            push_body=kwargs.get("push_body"),
            push_data=kwargs.get("push_data"),
            in_app_title=kwargs.get("in_app_title"),
            in_app_body=kwargs.get("in_app_body"),
            in_app_icon=kwargs.get("in_app_icon"),
            in_app_action_url=kwargs.get("in_app_action_url"),
            webhook_payload=kwargs.get("webhook_payload"),
            slack_message=kwargs.get("slack_message"),
            translations=kwargs.get("translations", {}),
            variables=list(variables),
            variable_defaults=kwargs.get("variable_defaults", {}),
            default_priority=kwargs.get("default_priority", NotificationPriority.NORMAL),
            expiry_hours=kwargs.get("expiry_hours"),
            created_by=kwargs.get("created_by", "system"),
            category=kwargs.get("category", "general"),
            tags=kwargs.get("tags", [])
        )

        self._templates[template_id] = template
        return template

    def activate_template(self, template_id: str) -> NotificationTemplate:
        """Active un template."""
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} non trouvé")

        template.status = TemplateStatus.ACTIVE
        template.updated_at = datetime.now()
        return template

    def get_template_by_code(self, code: str) -> Optional[NotificationTemplate]:
        """Récupère un template par son code."""
        for template in self._templates.values():
            if template.tenant_id == self.tenant_id and template.code == code:
                return template
        return None

    # =========================================================================
    # Préférences Utilisateur
    # =========================================================================

    def get_or_create_preferences(
        self,
        user_id: str,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> UserPreferences:
        """Récupère ou crée les préférences utilisateur."""
        if user_id in self._preferences:
            return self._preferences[user_id]

        prefs = UserPreferences(
            user_id=user_id,
            tenant_id=self.tenant_id,
            email_address=email,
            phone_number=phone
        )

        self._preferences[user_id] = prefs
        return prefs

    def update_preferences(
        self,
        user_id: str,
        **kwargs
    ) -> UserPreferences:
        """Met à jour les préférences utilisateur."""
        prefs = self._preferences.get(user_id)
        if not prefs:
            prefs = self.get_or_create_preferences(user_id)

        for key, value in kwargs.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)

        prefs.updated_at = datetime.now()
        return prefs

    def register_push_token(
        self,
        user_id: str,
        token: str,
        platform: str = "fcm"
    ) -> UserPreferences:
        """Enregistre un token push."""
        prefs = self.get_or_create_preferences(user_id)

        if token not in prefs.push_tokens:
            prefs.push_tokens.append(token)
            prefs.updated_at = datetime.now()

        return prefs

    def unsubscribe(
        self,
        user_id: str,
        template_code: Optional[str] = None,
        channel: Optional[NotificationChannel] = None,
        notification_type: Optional[NotificationType] = None
    ) -> UserPreferences:
        """Désabonne un utilisateur."""
        prefs = self._preferences.get(user_id)
        if not prefs:
            return None

        if template_code:
            if template_code not in prefs.unsubscribed_templates:
                prefs.unsubscribed_templates.append(template_code)

        if channel:
            if channel == NotificationChannel.EMAIL:
                prefs.email_enabled = False
            elif channel == NotificationChannel.SMS:
                prefs.sms_enabled = False
            elif channel == NotificationChannel.PUSH:
                prefs.push_enabled = False

        if notification_type:
            type_key = notification_type.value
            if type_key not in prefs.type_preferences:
                prefs.type_preferences[type_key] = {}
            prefs.type_preferences[type_key]["enabled"] = False

        prefs.updated_at = datetime.now()
        return prefs

    # =========================================================================
    # Envoi de Notifications
    # =========================================================================

    def send(
        self,
        template_code: str,
        user_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        channels: Optional[List[NotificationChannel]] = None,
        **kwargs
    ) -> List[Notification]:
        """Envoie une notification à partir d'un template."""
        template = self.get_template_by_code(template_code)
        if not template or template.status != TemplateStatus.ACTIVE:
            raise ValueError(f"Template {template_code} non disponible")

        # Récupérer les préférences si user_id fourni
        prefs = None
        if user_id:
            prefs = self._preferences.get(user_id)

        # Vérifier les désabonnements
        if prefs and template_code in prefs.unsubscribed_templates:
            return []

        # Déterminer les canaux
        target_channels = channels or template.channels

        # Filtrer selon les préférences
        if prefs:
            target_channels = self._filter_channels_by_preferences(
                target_channels, prefs, template.notification_type
            )

        # Vérifier les heures calmes
        if prefs and prefs.quiet_hours_enabled:
            if self._is_quiet_hours(prefs):
                # Programmer pour plus tard
                kwargs["scheduled_at"] = self._get_end_of_quiet_hours(prefs)

        # Préparer les variables
        all_variables = {**template.variable_defaults, **(variables or {})}

        # Envoyer sur chaque canal
        notifications = []
        for channel in target_channels:
            notification = self._send_to_channel(
                template, channel, user_id, prefs, all_variables, **kwargs
            )
            if notification:
                notifications.append(notification)

        return notifications

    def _filter_channels_by_preferences(
        self,
        channels: List[NotificationChannel],
        prefs: UserPreferences,
        notification_type: NotificationType
    ) -> List[NotificationChannel]:
        """Filtre les canaux selon les préférences."""
        filtered = []

        for channel in channels:
            # Vérifier si le canal est activé
            if channel == NotificationChannel.EMAIL and not prefs.email_enabled:
                continue
            if channel == NotificationChannel.SMS and not prefs.sms_enabled:
                continue
            if channel == NotificationChannel.PUSH and not prefs.push_enabled:
                continue
            if channel == NotificationChannel.IN_APP and not prefs.in_app_enabled:
                continue

            # Vérifier les préférences par type
            type_key = notification_type.value
            if type_key in prefs.type_preferences:
                type_prefs = prefs.type_preferences[type_key]
                if not type_prefs.get("enabled", True):
                    continue
                if not type_prefs.get(channel.value, True):
                    continue

            filtered.append(channel)

        return filtered

    def _is_quiet_hours(self, prefs: UserPreferences) -> bool:
        """Vérifie si on est dans les heures calmes."""
        if not prefs.quiet_hours_start or not prefs.quiet_hours_end:
            return False

        now = datetime.now()
        current_time = now.strftime("%H:%M")

        start = prefs.quiet_hours_start
        end = prefs.quiet_hours_end

        if start < end:
            return start <= current_time <= end
        else:
            # Période nocturne (ex: 22:00 - 07:00)
            return current_time >= start or current_time <= end

    def _get_end_of_quiet_hours(self, prefs: UserPreferences) -> datetime:
        """Calcule la fin des heures calmes."""
        if not prefs.quiet_hours_end:
            return datetime.now()

        now = datetime.now()
        end_parts = prefs.quiet_hours_end.split(":")
        end_time = now.replace(
            hour=int(end_parts[0]),
            minute=int(end_parts[1]),
            second=0,
            microsecond=0
        )

        if end_time <= now:
            end_time += timedelta(days=1)

        return end_time

    def _send_to_channel(
        self,
        template: NotificationTemplate,
        channel: NotificationChannel,
        user_id: Optional[str],
        prefs: Optional[UserPreferences],
        variables: Dict[str, Any],
        **kwargs
    ) -> Optional[Notification]:
        """Envoie sur un canal spécifique."""
        notification_id = f"notif_{uuid4().hex[:12]}"

        # Construire le contenu
        content = self._build_content(template, channel, variables,
                                       prefs.language if prefs else "fr")

        # Créer la notification
        notification = Notification(
            notification_id=notification_id,
            tenant_id=self.tenant_id,
            template_id=template.template_id,
            template_code=template.code,
            notification_type=template.notification_type,
            channel=channel,
            priority=kwargs.get("priority", template.default_priority),
            status=NotificationStatus.PENDING,
            user_id=user_id,
            subject=content.get("subject"),
            title=content.get("title"),
            body=content.get("body", ""),
            html_body=content.get("html_body"),
            data=content.get("data", {}),
            variables=variables,
            reference_type=kwargs.get("reference_type"),
            reference_id=kwargs.get("reference_id"),
            scheduled_at=kwargs.get("scheduled_at"),
            metadata=kwargs.get("metadata", {})
        )

        # Définir le destinataire
        if channel == NotificationChannel.EMAIL:
            notification.recipient_email = kwargs.get("email") or \
                (prefs.email_address if prefs else None)
        elif channel == NotificationChannel.SMS:
            notification.recipient_phone = kwargs.get("phone") or \
                (prefs.phone_number if prefs else None)
        elif channel == NotificationChannel.PUSH:
            # Utiliser tous les tokens de l'utilisateur
            if prefs and prefs.push_tokens:
                notification.recipient_device_token = prefs.push_tokens[0]
        elif channel == NotificationChannel.WEBHOOK:
            notification.recipient_webhook_url = kwargs.get("webhook_url")

        # Définir l'expiration
        if template.expiry_hours:
            notification.expires_at = datetime.now() + timedelta(
                hours=template.expiry_hours
            )

        self._notifications[notification_id] = notification

        # Envoyer ou programmer
        if notification.scheduled_at and notification.scheduled_at > datetime.now():
            notification.status = NotificationStatus.QUEUED
        else:
            self._deliver(notification)

        return notification

    def _build_content(
        self,
        template: NotificationTemplate,
        channel: NotificationChannel,
        variables: Dict[str, Any],
        language: str
    ) -> Dict[str, Any]:
        """Construit le contenu de la notification."""
        content = {}

        # Récupérer le contenu traduit si disponible
        translations = template.translations.get(language, {})

        if channel == NotificationChannel.EMAIL:
            subject = translations.get("email_subject") or template.email_subject
            html = translations.get("email_html") or template.email_html
            text = translations.get("email_text") or template.email_text

            content["subject"] = self._render_template(subject, variables)
            content["html_body"] = self._render_template(html, variables)
            content["body"] = self._render_template(text, variables)

        elif channel == NotificationChannel.SMS:
            text = translations.get("sms_text") or template.sms_text
            content["body"] = self._render_template(text, variables)

        elif channel == NotificationChannel.PUSH:
            title = translations.get("push_title") or template.push_title
            body = translations.get("push_body") or template.push_body

            content["title"] = self._render_template(title, variables)
            content["body"] = self._render_template(body, variables)
            content["data"] = template.push_data or {}

        elif channel == NotificationChannel.IN_APP:
            title = translations.get("in_app_title") or template.in_app_title
            body = translations.get("in_app_body") or template.in_app_body

            content["title"] = self._render_template(title, variables)
            content["body"] = self._render_template(body, variables)
            content["data"] = {
                "icon": template.in_app_icon,
                "action_url": self._render_template(
                    template.in_app_action_url, variables
                ) if template.in_app_action_url else None
            }

        elif channel == NotificationChannel.WEBHOOK:
            payload = template.webhook_payload or {}
            content["body"] = json.dumps(payload)
            content["data"] = self._render_dict(payload, variables)

        return content

    def _render_template(
        self,
        template: Optional[str],
        variables: Dict[str, Any]
    ) -> str:
        """Remplace les variables dans un template."""
        if not template:
            return ""

        def replace_var(match):
            var_name = match.group(1).strip()
            parts = var_name.split("|")
            name = parts[0]

            value = self._get_nested_value(variables, name)
            if value is None:
                return ""

            # Appliquer les filtres
            for filter_name in parts[1:]:
                value = self._apply_filter(value, filter_name)

            return str(value)

        return self._variable_pattern.sub(replace_var, template)

    def _render_dict(
        self,
        data: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Remplace les variables dans un dictionnaire."""
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._render_template(value, variables)
            elif isinstance(value, dict):
                result[key] = self._render_dict(value, variables)
            elif isinstance(value, list):
                result[key] = [
                    self._render_dict(item, variables) if isinstance(item, dict)
                    else self._render_template(item, variables) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Récupère une valeur imbriquée."""
        parts = path.split(".")
        value = data
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value

    def _apply_filter(self, value: Any, filter_name: str) -> Any:
        """Applique un filtre à une valeur."""
        filter_name = filter_name.strip().lower()

        if filter_name == "upper":
            return str(value).upper()
        elif filter_name == "lower":
            return str(value).lower()
        elif filter_name == "title":
            return str(value).title()
        elif filter_name == "currency":
            return f"{float(value):,.2f} €".replace(",", " ").replace(".", ",")
        elif filter_name == "date":
            if isinstance(value, datetime):
                return value.strftime("%d/%m/%Y")
        elif filter_name == "datetime":
            if isinstance(value, datetime):
                return value.strftime("%d/%m/%Y %H:%M")

        return value

    def _deliver(self, notification: Notification):
        """Effectue la livraison de la notification."""
        # Rate limiting
        if self.rate_limiter:
            if not self.rate_limiter.allow(
                f"{self.tenant_id}:{notification.channel.value}"
            ):
                notification.status = NotificationStatus.QUEUED
                notification.next_retry_at = datetime.now() + timedelta(minutes=1)
                return

        notification.status = NotificationStatus.SENDING

        try:
            if notification.channel == NotificationChannel.EMAIL:
                self._send_email(notification)
            elif notification.channel == NotificationChannel.SMS:
                self._send_sms(notification)
            elif notification.channel == NotificationChannel.PUSH:
                self._send_push(notification)
            elif notification.channel == NotificationChannel.IN_APP:
                self._send_in_app(notification)
            elif notification.channel == NotificationChannel.WEBHOOK:
                self._send_webhook(notification)

            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.now()

        except (ChannelSendError, ConnectionError, TimeoutError, ValueError, OSError) as e:
            logger.warning(
                "Notification send failed: %s (channel=%s, retry=%d)",
                str(e), notification.channel.value, notification.retry_count
            )
            notification.status = NotificationStatus.FAILED
            notification.failed_at = datetime.now()
            notification.failure_reason = str(e)
            notification.retry_count += 1

            if notification.retry_count < notification.max_retries:
                notification.status = NotificationStatus.QUEUED
                notification.next_retry_at = datetime.now() + timedelta(
                    minutes=5 * notification.retry_count
                )

    def _send_email(self, notification: Notification):
        """Envoie un email."""
        if not self.email_provider:
            raise ValueError("Email provider non configuré")

        if not notification.recipient_email:
            raise ValueError("Adresse email manquante")

        result = self.email_provider(
            to=notification.recipient_email,
            subject=notification.subject,
            html=notification.html_body,
            text=notification.body
        )

        notification.provider_response = result

    def _send_sms(self, notification: Notification):
        """Envoie un SMS."""
        if not self.sms_provider:
            raise ValueError("SMS provider non configuré")

        if not notification.recipient_phone:
            raise ValueError("Numéro de téléphone manquant")

        result = self.sms_provider(
            to=notification.recipient_phone,
            message=notification.body
        )

        notification.provider_response = result

    def _send_push(self, notification: Notification):
        """Envoie une notification push."""
        if not self.push_provider:
            raise ValueError("Push provider non configuré")

        if not notification.recipient_device_token:
            raise ValueError("Token push manquant")

        result = self.push_provider(
            token=notification.recipient_device_token,
            title=notification.title,
            body=notification.body,
            data=notification.data
        )

        notification.provider_response = result

    def _send_in_app(self, notification: Notification):
        """Enregistre une notification in-app."""
        # Les notifications in-app sont stockées et récupérées via l'API
        notification.status = NotificationStatus.DELIVERED
        notification.delivered_at = datetime.now()

    def _send_webhook(self, notification: Notification):
        """Envoie un webhook."""
        if not self.webhook_client:
            raise ValueError("Webhook client non configuré")

        if not notification.recipient_webhook_url:
            raise ValueError("URL webhook manquante")

        result = self.webhook_client(
            url=notification.recipient_webhook_url,
            payload=notification.data
        )

        notification.provider_response = result

    # =========================================================================
    # Batch Notifications
    # =========================================================================

    def send_batch(
        self,
        template_code: str,
        recipients: List[Dict[str, Any]],
        **kwargs
    ) -> NotificationBatch:
        """Envoie des notifications en lot."""
        template = self.get_template_by_code(template_code)
        if not template:
            raise ValueError(f"Template {template_code} non trouvé")

        batch_id = f"batch_{uuid4().hex[:12]}"

        batch = NotificationBatch(
            batch_id=batch_id,
            tenant_id=self.tenant_id,
            template_id=template.template_id,
            recipients=recipients,
            total_recipients=len(recipients),
            scheduled_at=kwargs.get("scheduled_at"),
            created_by=kwargs.get("created_by", "system")
        )

        self._batches[batch_id] = batch

        # Traitement asynchrone ou immédiat
        if not batch.scheduled_at or batch.scheduled_at <= datetime.now():
            self._process_batch(batch, template, **kwargs)

        return batch

    def _process_batch(
        self,
        batch: NotificationBatch,
        template: NotificationTemplate,
        **kwargs
    ):
        """Traite un lot de notifications."""
        batch.status = "processing"
        batch.started_at = datetime.now()

        for recipient in batch.recipients:
            try:
                user_id = recipient.get("user_id")
                variables = recipient.get("variables", {})

                self.send(
                    template.code,
                    user_id=user_id,
                    variables=variables,
                    email=recipient.get("email"),
                    phone=recipient.get("phone"),
                    **kwargs
                )

                batch.sent_count += 1

            except (ChannelSendError, ConnectionError, TimeoutError, ValueError, OSError) as e:
                logger.warning("Batch send failed for recipient: %s", str(e))
                batch.failed_count += 1

            batch.processed_count += 1

        batch.status = "completed"
        batch.completed_at = datetime.now()

    # =========================================================================
    # In-App Notifications
    # =========================================================================

    def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """Récupère les notifications in-app d'un utilisateur."""
        notifications = []

        for notif in self._notifications.values():
            if notif.tenant_id != self.tenant_id:
                continue
            if notif.user_id != user_id:
                continue
            if notif.channel != NotificationChannel.IN_APP:
                continue
            if unread_only and notif.read_at:
                continue

            notifications.append(notif)

        # Trier par date décroissante
        notifications.sort(key=lambda n: n.created_at, reverse=True)

        return notifications[:limit]

    def mark_as_read(
        self,
        notification_id: str,
        user_id: str
    ) -> Notification:
        """Marque une notification comme lue."""
        notification = self._notifications.get(notification_id)
        if not notification:
            raise ValueError(f"Notification {notification_id} non trouvée")

        if notification.user_id != user_id:
            raise ValueError("Notification non accessible")

        notification.read_at = datetime.now()
        notification.status = NotificationStatus.READ

        return notification

    def mark_all_as_read(self, user_id: str) -> int:
        """Marque toutes les notifications comme lues."""
        count = 0

        for notification in self._notifications.values():
            if notification.user_id == user_id and not notification.read_at:
                notification.read_at = datetime.now()
                notification.status = NotificationStatus.READ
                count += 1

        return count

    def get_unread_count(self, user_id: str) -> int:
        """Compte les notifications non lues."""
        count = 0

        for notification in self._notifications.values():
            if (notification.user_id == user_id and
                notification.channel == NotificationChannel.IN_APP and
                not notification.read_at):
                count += 1

        return count

    # =========================================================================
    # Webhooks
    # =========================================================================

    def register_webhook(
        self,
        name: str,
        url: str,
        event_types: List[str],
        **kwargs
    ) -> WebhookSubscription:
        """Enregistre un webhook."""
        import secrets

        subscription_id = f"webhook_{uuid4().hex[:12]}"
        secret = secrets.token_urlsafe(32)

        subscription = WebhookSubscription(
            subscription_id=subscription_id,
            tenant_id=self.tenant_id,
            name=name,
            url=url,
            secret=secret,
            event_types=event_types,
            headers=kwargs.get("headers", {}),
            retry_policy=kwargs.get("retry_policy", {
                "max_retries": 3,
                "initial_delay_seconds": 5
            })
        )

        self._webhooks[subscription_id] = subscription
        return subscription

    def trigger_webhooks(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ):
        """Déclenche les webhooks pour un événement."""
        for subscription in self._webhooks.values():
            if not subscription.is_active:
                continue
            if subscription.tenant_id != self.tenant_id:
                continue
            if event_type not in subscription.event_types:
                continue

            self._send_webhook_event(subscription, event_type, payload)

    def _send_webhook_event(
        self,
        subscription: WebhookSubscription,
        event_type: str,
        payload: Dict[str, Any]
    ):
        """Envoie un événement webhook."""
        if not self.webhook_client:
            return

        import hmac
        import hashlib

        # Signer le payload
        body = json.dumps(payload)
        signature = hmac.new(
            subscription.secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

        headers = {
            **subscription.headers,
            "X-Webhook-Signature": signature,
            "X-Event-Type": event_type
        }

        try:
            self.webhook_client(
                url=subscription.url,
                payload=payload,
                headers=headers
            )
            subscription.last_triggered_at = datetime.now()
            subscription.failure_count = 0

        except (WebhookSendError, ConnectionError, TimeoutError, OSError) as e:
            logger.warning("Webhook trigger failed: %s", str(e))
            subscription.failure_count += 1

    # =========================================================================
    # Statistiques
    # =========================================================================

    def get_statistics(
        self,
        from_date: datetime,
        to_date: datetime
    ) -> NotificationStats:
        """Calcule les statistiques de notifications."""
        stats = NotificationStats(
            tenant_id=self.tenant_id,
            period_start=from_date,
            period_end=to_date
        )

        for notification in self._notifications.values():
            if notification.tenant_id != self.tenant_id:
                continue
            if notification.created_at < from_date or notification.created_at > to_date:
                continue

            # Comptages globaux
            if notification.status in (NotificationStatus.SENT,
                                        NotificationStatus.DELIVERED,
                                        NotificationStatus.READ):
                stats.total_sent += 1

            if notification.status in (NotificationStatus.DELIVERED,
                                        NotificationStatus.READ):
                stats.total_delivered += 1

            if notification.status == NotificationStatus.READ:
                stats.total_read += 1

            if notification.clicked_at:
                stats.total_clicked += 1

            if notification.status == NotificationStatus.FAILED:
                stats.total_failed += 1

            if notification.status == NotificationStatus.BOUNCED:
                stats.total_bounced += 1

            # Par canal
            channel = notification.channel.value
            if channel not in stats.by_channel:
                stats.by_channel[channel] = {"sent": 0, "delivered": 0, "read": 0}
            if notification.sent_at:
                stats.by_channel[channel]["sent"] += 1
            if notification.delivered_at:
                stats.by_channel[channel]["delivered"] += 1
            if notification.read_at:
                stats.by_channel[channel]["read"] += 1

            # Par type
            ntype = notification.notification_type.value
            if ntype not in stats.by_type:
                stats.by_type[ntype] = {"sent": 0, "delivered": 0, "read": 0}
            if notification.sent_at:
                stats.by_type[ntype]["sent"] += 1

        # Calculer les taux
        if stats.total_sent > 0:
            stats.delivery_rate = stats.total_delivered / stats.total_sent * 100
            stats.open_rate = stats.total_read / stats.total_sent * 100
            stats.click_rate = stats.total_clicked / stats.total_sent * 100

        return stats


def create_notification_service(
    tenant_id: str,
    **kwargs
) -> NotificationService:
    """Factory pour créer un service de notifications."""
    return NotificationService(tenant_id=tenant_id, **kwargs)
