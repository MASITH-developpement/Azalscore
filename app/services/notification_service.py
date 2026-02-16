"""
AZALSCORE - Service de Notifications Multi-Canal
=================================================

Service de notifications unifié:
- Email (SMTP, SendGrid, Mailgun, SES)
- SMS (Twilio, OVH, Vonage)
- Push notifications (FCM, APNs)
- Webhooks
- In-app notifications

Features:
- Templates personnalisables (Jinja2)
- Préférences utilisateur
- Throttling et rate limiting
- Retry automatique
- Historique et analytics
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional, Callable, Union
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & TYPES
# =============================================================================

class NotificationChannel(str, Enum):
    """Canaux de notification."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    SLACK = "slack"
    TEAMS = "teams"


class NotificationPriority(str, Enum):
    """Priorité des notifications."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationStatus(str, Enum):
    """Statut d'une notification."""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"


class NotificationCategory(str, Enum):
    """Catégories de notifications."""
    TRANSACTIONAL = "transactional"  # Confirmations, factures
    ALERT = "alert"  # Alertes système
    MARKETING = "marketing"  # Promotions (opt-in requis)
    REMINDER = "reminder"  # Rappels
    SECURITY = "security"  # MFA, changement de mot de passe
    SYSTEM = "system"  # Maintenance, mises à jour


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class NotificationRecipient:
    """Destinataire d'une notification."""
    user_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    device_token: Optional[str] = None
    webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    teams_webhook: Optional[str] = None
    locale: str = "fr"
    timezone: str = "Europe/Paris"
    name: Optional[str] = None


@dataclass
class NotificationContent:
    """Contenu d'une notification."""
    subject: Optional[str] = None
    title: Optional[str] = None
    body: str = ""
    html_body: Optional[str] = None
    short_message: Optional[str] = None  # Pour SMS
    data: dict = field(default_factory=dict)  # Données additionnelles

    # Actions
    action_url: Optional[str] = None
    action_label: Optional[str] = None

    # Pièces jointes
    attachments: list[dict] = field(default_factory=list)


@dataclass
class NotificationTemplate:
    """Template de notification."""
    template_id: str
    name: str
    tenant_id: str
    category: NotificationCategory
    channels: list[NotificationChannel]

    # Templates par canal
    email_subject: Optional[str] = None
    email_body: Optional[str] = None  # HTML template
    email_text: Optional[str] = None  # Plain text fallback
    sms_body: Optional[str] = None
    push_title: Optional[str] = None
    push_body: Optional[str] = None
    webhook_payload: Optional[str] = None  # JSON template
    slack_message: Optional[str] = None
    in_app_title: Optional[str] = None
    in_app_body: Optional[str] = None

    # Variables disponibles
    variables: list[str] = field(default_factory=list)

    # Métadonnées
    is_active: bool = True
    is_system: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Notification:
    """Notification individuelle."""
    notification_id: str
    tenant_id: str
    template_id: Optional[str]
    category: NotificationCategory
    channel: NotificationChannel
    priority: NotificationPriority
    status: NotificationStatus
    created_at: datetime

    # Destinataire
    recipient: NotificationRecipient

    # Contenu
    content: NotificationContent

    # Tracking
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    # Retries
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: Optional[datetime] = None

    # Métadonnées
    metadata: dict = field(default_factory=dict)
    external_id: Optional[str] = None  # ID du provider


@dataclass
class UserPreferences:
    """Préférences de notification utilisateur."""
    user_id: str
    tenant_id: str

    # Canaux activés
    email_enabled: bool = True
    sms_enabled: bool = True
    push_enabled: bool = True
    in_app_enabled: bool = True

    # Catégories par canal
    email_categories: list[NotificationCategory] = field(
        default_factory=lambda: [
            NotificationCategory.TRANSACTIONAL,
            NotificationCategory.ALERT,
            NotificationCategory.SECURITY,
        ]
    )
    sms_categories: list[NotificationCategory] = field(
        default_factory=lambda: [
            NotificationCategory.SECURITY,
            NotificationCategory.ALERT,
        ]
    )
    push_categories: list[NotificationCategory] = field(
        default_factory=lambda: [
            NotificationCategory.TRANSACTIONAL,
            NotificationCategory.ALERT,
            NotificationCategory.REMINDER,
        ]
    )

    # Quiet hours
    quiet_hours_enabled: bool = False
    quiet_hours_start: int = 22  # 22h00
    quiet_hours_end: int = 8  # 08h00

    # Unsubscribe
    unsubscribed_templates: list[str] = field(default_factory=list)
    global_unsubscribe: bool = False


@dataclass
class NotificationBatch:
    """Lot de notifications."""
    batch_id: str
    tenant_id: str
    template_id: str
    status: str
    created_at: datetime
    total_count: int
    sent_count: int = 0
    failed_count: int = 0
    completed_at: Optional[datetime] = None


# =============================================================================
# CHANNEL PROVIDERS
# =============================================================================

class NotificationProvider(ABC):
    """Interface pour les providers de notification."""

    @abstractmethod
    async def send(
        self,
        notification: Notification
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Envoie une notification.

        Returns:
            Tuple (success, external_id, error_message)
        """
        pass


class SMTPEmailProvider(NotificationProvider):
    """Provider email SMTP."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        from_name: str = "AZALSCORE",
        use_tls: bool = True,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.from_name = from_name
        self.use_tls = use_tls

    async def send(
        self,
        notification: Notification
    ) -> tuple[bool, Optional[str], Optional[str]]:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart('alternative')
            msg['Subject'] = notification.content.subject or "Notification"
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = notification.recipient.email

            # Plain text
            if notification.content.body:
                part1 = MIMEText(notification.content.body, 'plain')
                msg.attach(part1)

            # HTML
            if notification.content.html_body:
                part2 = MIMEText(notification.content.html_body, 'html')
                msg.attach(part2)

            # Envoi
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.sendmail(
                    self.from_email,
                    [notification.recipient.email],
                    msg.as_string()
                )

            message_id = f"smtp_{uuid.uuid4().hex[:8]}"
            return True, message_id, None

        except Exception as e:
            logger.error(f"SMTP send error: {e}")
            return False, None, str(e)


class SendGridProvider(NotificationProvider):
    """Provider SendGrid."""

    def __init__(self, api_key: str, from_email: str, from_name: str = "AZALSCORE"):
        self.api_key = api_key
        self.from_email = from_email
        self.from_name = from_name

    async def send(
        self,
        notification: Notification
    ) -> tuple[bool, Optional[str], Optional[str]]:
        try:
            import aiohttp

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "personalizations": [{
                    "to": [{"email": notification.recipient.email}]
                }],
                "from": {
                    "email": self.from_email,
                    "name": self.from_name
                },
                "subject": notification.content.subject,
                "content": []
            }

            if notification.content.body:
                payload["content"].append({
                    "type": "text/plain",
                    "value": notification.content.body
                })

            if notification.content.html_body:
                payload["content"].append({
                    "type": "text/html",
                    "value": notification.content.html_body
                })

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers=headers,
                    json=payload
                ) as resp:
                    if resp.status in (200, 202):
                        message_id = resp.headers.get("X-Message-Id", f"sg_{uuid.uuid4().hex[:8]}")
                        return True, message_id, None
                    else:
                        error = await resp.text()
                        return False, None, f"SendGrid error: {resp.status} - {error}"

        except Exception as e:
            return False, None, str(e)


class TwilioSMSProvider(NotificationProvider):
    """Provider SMS Twilio."""

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
    ):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

    async def send(
        self,
        notification: Notification
    ) -> tuple[bool, Optional[str], Optional[str]]:
        try:
            import aiohttp
            import base64

            credentials = base64.b64encode(
                f"{self.account_sid}:{self.auth_token}".encode()
            ).decode()

            headers = {
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            data = {
                "To": notification.recipient.phone,
                "From": self.from_number,
                "Body": notification.content.short_message or notification.content.body[:160]
            }

            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as resp:
                    result = await resp.json()
                    if resp.status == 201:
                        return True, result.get("sid"), None
                    else:
                        return False, None, result.get("message", "Unknown error")

        except Exception as e:
            return False, None, str(e)


class FCMPushProvider(NotificationProvider):
    """Provider Firebase Cloud Messaging."""

    def __init__(self, server_key: str, project_id: str):
        self.server_key = server_key
        self.project_id = project_id

    async def send(
        self,
        notification: Notification
    ) -> tuple[bool, Optional[str], Optional[str]]:
        try:
            import aiohttp

            headers = {
                "Authorization": f"key={self.server_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "to": notification.recipient.device_token,
                "notification": {
                    "title": notification.content.title,
                    "body": notification.content.body,
                },
                "data": notification.content.data
            }

            if notification.content.action_url:
                payload["notification"]["click_action"] = notification.content.action_url

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://fcm.googleapis.com/fcm/send",
                    headers=headers,
                    json=payload
                ) as resp:
                    result = await resp.json()
                    if result.get("success", 0) > 0:
                        message_id = result.get("results", [{}])[0].get("message_id")
                        return True, message_id, None
                    else:
                        error = result.get("results", [{}])[0].get("error", "Unknown error")
                        return False, None, error

        except Exception as e:
            return False, None, str(e)


class WebhookProvider(NotificationProvider):
    """Provider Webhook avec protection SSRF."""

    # Liste des hôtes/réseaux bloqués (protection SSRF)
    BLOCKED_HOSTS = {
        "localhost", "127.0.0.1", "0.0.0.0", "::1",
        "metadata.google.internal", "169.254.169.254",
    }

    BLOCKED_NETWORKS = [
        "10.", "172.16.", "172.17.", "172.18.", "172.19.",
        "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
        "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
        "172.30.", "172.31.", "192.168.",
    ]

    def __init__(
        self,
        default_headers: Optional[dict] = None,
        timeout: int = 30,
        signing_secret: Optional[str] = None
    ):
        self.default_headers = default_headers or {}
        self.timeout = min(timeout, 60)  # Max 60 secondes
        self.signing_secret = signing_secret

    def _is_safe_url(self, url: str) -> tuple[bool, str]:
        """Vérifie si l'URL est sûre (protection SSRF)."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)

            # Vérifier le schéma
            if parsed.scheme not in ("http", "https"):
                return False, f"Schéma non autorisé: {parsed.scheme}"

            # Vérifier l'hôte
            host = parsed.hostname or ""
            host_lower = host.lower()

            if host_lower in self.BLOCKED_HOSTS:
                return False, f"Hôte bloqué: {host}"

            # Vérifier les réseaux privés
            for network in self.BLOCKED_NETWORKS:
                if host.startswith(network):
                    return False, f"Réseau privé non autorisé: {host}"

            return True, ""
        except Exception as e:
            return False, f"URL invalide: {str(e)}"

    def _generate_signature(self, payload: str, timestamp: str) -> str:
        """Génère une signature HMAC pour le webhook."""
        if not self.signing_secret:
            return ""
        import hmac
        message = f"{timestamp}.{payload}"
        signature = hmac.new(
            self.signing_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    async def send(
        self,
        notification: Notification
    ) -> tuple[bool, Optional[str], Optional[str]]:
        try:
            import aiohttp

            url = notification.recipient.webhook_url
            if not url:
                return False, None, "No webhook URL"

            # Validation SSRF
            is_safe, error_msg = self._is_safe_url(url)
            if not is_safe:
                logger.warning(f"Webhook URL bloquée (SSRF): {url} - {error_msg}")
                return False, None, f"URL non autorisée: {error_msg}"

            timestamp = datetime.utcnow().isoformat()

            payload = {
                "notification_id": notification.notification_id,
                "timestamp": timestamp,
                "event": notification.category.value,
                "data": notification.content.data,
                "content": {
                    "title": notification.content.title,
                    "body": notification.content.body,
                }
            }

            payload_str = json.dumps(payload, sort_keys=True)

            # Signature pour validation
            signature = self._generate_signature(payload_str, timestamp)

            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Timestamp": timestamp,
                **self.default_headers
            }

            if signature:
                headers["X-Webhook-Signature"] = signature

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    data=payload_str,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    allow_redirects=False  # Pas de redirections (sécurité)
                ) as resp:
                    if resp.status in range(200, 300):
                        return True, f"webhook_{resp.status}", None
                    else:
                        error = await resp.text()
                        return False, None, f"Webhook error: {resp.status} - {error[:200]}"

        except asyncio.TimeoutError:
            return False, None, "Webhook timeout"
        except Exception as e:
            return False, None, str(e)


class SlackProvider(NotificationProvider):
    """Provider Slack via Webhooks avec validation URL."""

    # URLs Slack autorisées (protection SSRF)
    ALLOWED_SLACK_DOMAINS = {
        "hooks.slack.com",
        "hooks.slack-gov.com",
    }

    def __init__(self, default_webhook_url: Optional[str] = None):
        self.default_webhook_url = default_webhook_url

    def _is_valid_slack_url(self, url: str) -> tuple[bool, str]:
        """Vérifie que l'URL est un webhook Slack valide."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)

            # Doit être HTTPS
            if parsed.scheme != "https":
                return False, "Les webhooks Slack doivent utiliser HTTPS"

            # Doit être un domaine Slack officiel
            hostname = parsed.hostname or ""
            if hostname not in self.ALLOWED_SLACK_DOMAINS:
                return False, f"Domaine non autorisé: {hostname}. Domaines Slack valides: {', '.join(self.ALLOWED_SLACK_DOMAINS)}"

            return True, ""
        except Exception as e:
            return False, f"URL invalide: {str(e)}"

    async def send(
        self,
        notification: Notification
    ) -> tuple[bool, Optional[str], Optional[str]]:
        try:
            import aiohttp

            url = notification.recipient.slack_channel or self.default_webhook_url
            if not url:
                return False, None, "No Slack webhook URL"

            # Validation de l'URL Slack
            is_valid, error_msg = self._is_valid_slack_url(url)
            if not is_valid:
                logger.warning(f"URL Slack invalide: {url} - {error_msg}")
                return False, None, f"URL Slack invalide: {error_msg}"

            # Limiter la taille du contenu pour éviter les abus
            body_text = notification.content.body or ""
            if len(body_text) > 3000:
                body_text = body_text[:2997] + "..."

            title_text = notification.content.title or "Notification"
            if len(title_text) > 150:
                title_text = title_text[:147] + "..."

            payload = {
                "text": body_text,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": title_text
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": body_text
                        }
                    }
                ]
            }

            if notification.content.action_url:
                # Validation basique de l'URL d'action
                action_url = notification.content.action_url
                if action_url.startswith(("http://", "https://")):
                    action_label = notification.content.action_label or "Voir"
                    if len(action_label) > 75:
                        action_label = action_label[:72] + "..."
                    payload["blocks"].append({
                        "type": "actions",
                        "elements": [{
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": action_label
                            },
                            "url": action_url
                        }]
                    })

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        return True, f"slack_{uuid.uuid4().hex[:8]}", None
                    else:
                        error = await resp.text()
                        return False, None, f"Slack error: {error[:200]}"

        except asyncio.TimeoutError:
            return False, None, "Slack webhook timeout"
        except Exception as e:
            return False, None, str(e)


class InAppProvider(NotificationProvider):
    """Provider notifications in-app (stockage en DB)."""

    def __init__(self, notification_store: Optional[Callable] = None):
        self._store = notification_store
        self._in_memory_store: dict[str, list[Notification]] = defaultdict(list)

    async def send(
        self,
        notification: Notification
    ) -> tuple[bool, Optional[str], Optional[str]]:
        try:
            # Stocker la notification pour récupération ultérieure
            user_id = notification.recipient.user_id
            if user_id:
                self._in_memory_store[user_id].append(notification)

                # Garder seulement les 100 dernières
                if len(self._in_memory_store[user_id]) > 100:
                    self._in_memory_store[user_id] = self._in_memory_store[user_id][-100:]

            notification_id = f"inapp_{uuid.uuid4().hex[:8]}"
            return True, notification_id, None

        except Exception as e:
            return False, None, str(e)

    def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> list[Notification]:
        """Récupère les notifications d'un utilisateur."""
        notifications = self._in_memory_store.get(user_id, [])

        if unread_only:
            notifications = [n for n in notifications if n.read_at is None]

        return notifications[-limit:][::-1]

    def mark_as_read(self, user_id: str, notification_ids: list[str]) -> int:
        """Marque des notifications comme lues."""
        count = 0
        for notif in self._in_memory_store.get(user_id, []):
            if notif.notification_id in notification_ids and notif.read_at is None:
                notif.read_at = datetime.utcnow()
                count += 1
        return count


# =============================================================================
# TEMPLATE ENGINE
# =============================================================================

class TemplateEngine:
    """Moteur de templates pour les notifications."""

    def __init__(self):
        self._templates: dict[str, NotificationTemplate] = {}

    def register_template(self, template: NotificationTemplate) -> None:
        """Enregistre un template."""
        self._templates[template.template_id] = template

    def get_template(self, template_id: str) -> Optional[NotificationTemplate]:
        """Récupère un template."""
        return self._templates.get(template_id)

    def render(
        self,
        template: NotificationTemplate,
        channel: NotificationChannel,
        variables: dict,
        locale: str = "fr"
    ) -> NotificationContent:
        """Rend un template avec les variables fournies."""
        content = NotificationContent()

        # Fonction de rendu simple (en production, utiliser Jinja2)
        def render_string(template_str: Optional[str]) -> Optional[str]:
            if not template_str:
                return None
            result = template_str
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                result = result.replace(placeholder, str(value))
            return result

        if channel == NotificationChannel.EMAIL:
            content.subject = render_string(template.email_subject)
            content.html_body = render_string(template.email_body)
            content.body = render_string(template.email_text) or content.html_body or ""

        elif channel == NotificationChannel.SMS:
            content.short_message = render_string(template.sms_body)
            content.body = content.short_message or ""

        elif channel == NotificationChannel.PUSH:
            content.title = render_string(template.push_title)
            content.body = render_string(template.push_body) or ""

        elif channel == NotificationChannel.SLACK:
            content.body = render_string(template.slack_message) or ""

        elif channel == NotificationChannel.IN_APP:
            content.title = render_string(template.in_app_title)
            content.body = render_string(template.in_app_body) or ""

        elif channel == NotificationChannel.WEBHOOK:
            payload_str = render_string(template.webhook_payload)
            if payload_str:
                try:
                    content.data = json.loads(payload_str)
                except json.JSONDecodeError:
                    content.data = {"raw": payload_str}

        return content


# =============================================================================
# THROTTLING & RATE LIMITING
# =============================================================================

class NotificationThrottler:
    """Gestionnaire de throttling pour éviter le spam."""

    def __init__(
        self,
        max_per_minute: int = 10,
        max_per_hour: int = 50,
        max_per_day: int = 200,
    ):
        self.max_per_minute = max_per_minute
        self.max_per_hour = max_per_hour
        self.max_per_day = max_per_day
        self._counters: dict[str, list[datetime]] = defaultdict(list)
        self._lock = threading.Lock()

    def _clean_old_entries(self, key: str) -> None:
        """Nettoie les entrées anciennes."""
        now = datetime.utcnow()
        cutoff = now - timedelta(days=1)
        self._counters[key] = [t for t in self._counters[key] if t > cutoff]

    def can_send(
        self,
        user_id: str,
        channel: NotificationChannel,
        category: NotificationCategory
    ) -> tuple[bool, Optional[str]]:
        """
        Vérifie si on peut envoyer une notification.

        Returns:
            Tuple (can_send, reason_if_blocked)
        """
        # Notifications critiques passent toujours
        if category == NotificationCategory.SECURITY:
            return True, None

        key = f"{user_id}:{channel.value}"

        with self._lock:
            self._clean_old_entries(key)

            now = datetime.utcnow()
            timestamps = self._counters[key]

            # Vérifier par minute
            minute_ago = now - timedelta(minutes=1)
            minute_count = sum(1 for t in timestamps if t > minute_ago)
            if minute_count >= self.max_per_minute:
                return False, f"Rate limit exceeded: {self.max_per_minute}/minute"

            # Vérifier par heure
            hour_ago = now - timedelta(hours=1)
            hour_count = sum(1 for t in timestamps if t > hour_ago)
            if hour_count >= self.max_per_hour:
                return False, f"Rate limit exceeded: {self.max_per_hour}/hour"

            # Vérifier par jour
            day_count = len(timestamps)
            if day_count >= self.max_per_day:
                return False, f"Rate limit exceeded: {self.max_per_day}/day"

            return True, None

    def record_send(self, user_id: str, channel: NotificationChannel) -> None:
        """Enregistre un envoi."""
        key = f"{user_id}:{channel.value}"
        with self._lock:
            self._counters[key].append(datetime.utcnow())


# =============================================================================
# NOTIFICATION SERVICE
# =============================================================================

class NotificationService:
    """
    Service principal de notifications.

    Coordonne:
    - Templates
    - Providers
    - Préférences utilisateur
    - Throttling
    - Retry
    - Historique
    """

    def __init__(
        self,
        template_engine: Optional[TemplateEngine] = None,
        throttler: Optional[NotificationThrottler] = None,
    ):
        self._template_engine = template_engine or TemplateEngine()
        self._throttler = throttler or NotificationThrottler()

        # Providers par canal
        self._providers: dict[NotificationChannel, NotificationProvider] = {}

        # Préférences utilisateur
        self._user_preferences: dict[str, UserPreferences] = {}

        # Historique
        self._notifications: dict[str, Notification] = {}
        self._notification_history: dict[str, list[str]] = defaultdict(list)  # user_id -> notification_ids

        # Queue de retry
        self._retry_queue: list[Notification] = []

        self._lock = threading.Lock()

    # -------------------------------------------------------------------------
    # CONFIGURATION
    # -------------------------------------------------------------------------

    def register_provider(
        self,
        channel: NotificationChannel,
        provider: NotificationProvider
    ) -> None:
        """Enregistre un provider pour un canal."""
        self._providers[channel] = provider
        logger.info(f"Provider registered for channel: {channel.value}")

    def register_template(self, template: NotificationTemplate) -> None:
        """Enregistre un template."""
        self._template_engine.register_template(template)

    def set_user_preferences(self, preferences: UserPreferences) -> None:
        """Définit les préférences d'un utilisateur."""
        key = f"{preferences.tenant_id}:{preferences.user_id}"
        self._user_preferences[key] = preferences

    def get_user_preferences(
        self,
        user_id: str,
        tenant_id: str
    ) -> Optional[UserPreferences]:
        """Récupère les préférences d'un utilisateur."""
        key = f"{tenant_id}:{user_id}"
        return self._user_preferences.get(key)

    # -------------------------------------------------------------------------
    # ENVOI
    # -------------------------------------------------------------------------

    async def send(
        self,
        template_id: str,
        recipient: NotificationRecipient,
        variables: dict,
        tenant_id: str,
        channels: Optional[list[NotificationChannel]] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        category: Optional[NotificationCategory] = None,
        metadata: Optional[dict] = None,
    ) -> list[Notification]:
        """
        Envoie une notification basée sur un template.

        Returns:
            Liste des notifications créées (une par canal)
        """
        template = self._template_engine.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        # Déterminer les canaux
        target_channels = channels or template.channels
        actual_category = category or template.category

        # Vérifier les préférences utilisateur
        if recipient.user_id:
            prefs = self.get_user_preferences(recipient.user_id, tenant_id)
            if prefs:
                target_channels = self._filter_channels_by_preferences(
                    target_channels,
                    actual_category,
                    prefs
                )

                # Vérifier quiet hours
                if prefs.quiet_hours_enabled:
                    if self._in_quiet_hours(prefs):
                        if priority not in (NotificationPriority.HIGH, NotificationPriority.CRITICAL):
                            target_channels = []

        notifications = []

        for channel in target_channels:
            # Vérifier le throttling
            if recipient.user_id:
                can_send, reason = self._throttler.can_send(
                    recipient.user_id,
                    channel,
                    actual_category
                )
                if not can_send:
                    logger.warning(f"Throttled: {recipient.user_id} - {reason}")
                    continue

            # Rendre le contenu
            content = self._template_engine.render(
                template,
                channel,
                variables,
                recipient.locale
            )

            # Créer la notification
            notification = Notification(
                notification_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                template_id=template_id,
                category=actual_category,
                channel=channel,
                priority=priority,
                status=NotificationStatus.PENDING,
                created_at=datetime.utcnow(),
                recipient=recipient,
                content=content,
                metadata=metadata or {},
            )

            # Envoyer
            notification = await self._send_notification(notification)
            notifications.append(notification)

            # Enregistrer dans l'historique
            self._store_notification(notification)

        return notifications

    async def send_direct(
        self,
        channel: NotificationChannel,
        recipient: NotificationRecipient,
        content: NotificationContent,
        tenant_id: str,
        category: NotificationCategory = NotificationCategory.TRANSACTIONAL,
        priority: NotificationPriority = NotificationPriority.NORMAL,
    ) -> Notification:
        """
        Envoie une notification directe sans template.
        """
        notification = Notification(
            notification_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            template_id=None,
            category=category,
            channel=channel,
            priority=priority,
            status=NotificationStatus.PENDING,
            created_at=datetime.utcnow(),
            recipient=recipient,
            content=content,
        )

        notification = await self._send_notification(notification)
        self._store_notification(notification)

        return notification

    async def _send_notification(self, notification: Notification) -> Notification:
        """Envoie une notification via le provider approprié."""
        provider = self._providers.get(notification.channel)
        if not provider:
            notification.status = NotificationStatus.FAILED
            notification.error_message = f"No provider for channel: {notification.channel.value}"
            notification.failed_at = datetime.utcnow()
            return notification

        notification.status = NotificationStatus.SENDING

        success, external_id, error = await provider.send(notification)

        if success:
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            notification.external_id = external_id

            # Enregistrer le throttle
            if notification.recipient.user_id:
                self._throttler.record_send(
                    notification.recipient.user_id,
                    notification.channel
                )

            logger.info(
                f"Notification sent: {notification.notification_id}",
                extra={
                    "channel": notification.channel.value,
                    "external_id": external_id,
                }
            )
        else:
            notification.retry_count += 1

            if notification.retry_count < notification.max_retries:
                # Programmer un retry
                notification.status = NotificationStatus.QUEUED
                notification.next_retry_at = datetime.utcnow() + timedelta(
                    minutes=5 * notification.retry_count
                )
                self._retry_queue.append(notification)
            else:
                notification.status = NotificationStatus.FAILED
                notification.failed_at = datetime.utcnow()

            notification.error_message = error
            logger.warning(
                f"Notification failed: {notification.notification_id} - {error}",
                extra={
                    "channel": notification.channel.value,
                    "retry_count": notification.retry_count,
                }
            )

        return notification

    async def process_retries(self) -> int:
        """Traite la queue de retry."""
        now = datetime.utcnow()
        processed = 0

        with self._lock:
            to_retry = [
                n for n in self._retry_queue
                if n.next_retry_at and n.next_retry_at <= now
            ]
            self._retry_queue = [
                n for n in self._retry_queue
                if n not in to_retry
            ]

        for notification in to_retry:
            await self._send_notification(notification)
            processed += 1

        return processed

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    def _filter_channels_by_preferences(
        self,
        channels: list[NotificationChannel],
        category: NotificationCategory,
        prefs: UserPreferences
    ) -> list[NotificationChannel]:
        """Filtre les canaux selon les préférences utilisateur."""
        if prefs.global_unsubscribe:
            return []

        filtered = []

        for channel in channels:
            if channel == NotificationChannel.EMAIL:
                if prefs.email_enabled and category in prefs.email_categories:
                    filtered.append(channel)
            elif channel == NotificationChannel.SMS:
                if prefs.sms_enabled and category in prefs.sms_categories:
                    filtered.append(channel)
            elif channel == NotificationChannel.PUSH:
                if prefs.push_enabled and category in prefs.push_categories:
                    filtered.append(channel)
            elif channel == NotificationChannel.IN_APP:
                if prefs.in_app_enabled:
                    filtered.append(channel)
            else:
                # Autres canaux (webhook, slack) passent par défaut
                filtered.append(channel)

        return filtered

    def _in_quiet_hours(self, prefs: UserPreferences) -> bool:
        """Vérifie si on est dans les heures calmes."""
        # Simplification: utiliser l'heure UTC
        current_hour = datetime.utcnow().hour

        if prefs.quiet_hours_start < prefs.quiet_hours_end:
            return prefs.quiet_hours_start <= current_hour < prefs.quiet_hours_end
        else:
            # Passage par minuit (ex: 22h-8h)
            return current_hour >= prefs.quiet_hours_start or current_hour < prefs.quiet_hours_end

    def _store_notification(self, notification: Notification) -> None:
        """Stocke une notification dans l'historique."""
        with self._lock:
            self._notifications[notification.notification_id] = notification

            if notification.recipient.user_id:
                self._notification_history[notification.recipient.user_id].append(
                    notification.notification_id
                )
                # Garder les 500 dernières
                if len(self._notification_history[notification.recipient.user_id]) > 500:
                    old_ids = self._notification_history[notification.recipient.user_id][:-500]
                    for old_id in old_ids:
                        self._notifications.pop(old_id, None)
                    self._notification_history[notification.recipient.user_id] = \
                        self._notification_history[notification.recipient.user_id][-500:]

    # -------------------------------------------------------------------------
    # QUERIES
    # -------------------------------------------------------------------------

    def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Récupère une notification."""
        return self._notifications.get(notification_id)

    def get_user_notifications(
        self,
        user_id: str,
        status: Optional[NotificationStatus] = None,
        channel: Optional[NotificationChannel] = None,
        limit: int = 50
    ) -> list[Notification]:
        """Liste les notifications d'un utilisateur."""
        notification_ids = self._notification_history.get(user_id, [])
        notifications = []

        for nid in reversed(notification_ids):
            notif = self._notifications.get(nid)
            if notif:
                if status and notif.status != status:
                    continue
                if channel and notif.channel != channel:
                    continue
                notifications.append(notif)
                if len(notifications) >= limit:
                    break

        return notifications

    def get_statistics(self, tenant_id: str) -> dict:
        """Statistiques des notifications."""
        notifications = [n for n in self._notifications.values() if n.tenant_id == tenant_id]

        stats = {
            "total": len(notifications),
            "by_status": defaultdict(int),
            "by_channel": defaultdict(int),
            "by_category": defaultdict(int),
        }

        for n in notifications:
            stats["by_status"][n.status.value] += 1
            stats["by_channel"][n.channel.value] += 1
            stats["by_category"][n.category.value] += 1

        return dict(stats)


# =============================================================================
# FACTORY & BUILT-IN TEMPLATES
# =============================================================================

def create_welcome_template(tenant_id: str) -> NotificationTemplate:
    """Template de bienvenue."""
    return NotificationTemplate(
        template_id=f"welcome_{tenant_id}",
        name="Email de Bienvenue",
        tenant_id=tenant_id,
        category=NotificationCategory.TRANSACTIONAL,
        channels=[NotificationChannel.EMAIL],
        email_subject="Bienvenue sur AZALSCORE, {{user_name}} !",
        email_body="""
        <h1>Bienvenue {{user_name}} !</h1>
        <p>Votre compte AZALSCORE a été créé avec succès.</p>
        <p>Vous pouvez dès maintenant accéder à votre tableau de bord :</p>
        <p><a href="{{login_url}}">Se connecter</a></p>
        """,
        email_text="Bienvenue {{user_name}} ! Connectez-vous sur {{login_url}}",
        is_system=True,
    )


def create_password_reset_template(tenant_id: str) -> NotificationTemplate:
    """Template de réinitialisation de mot de passe."""
    return NotificationTemplate(
        template_id=f"password_reset_{tenant_id}",
        name="Réinitialisation de mot de passe",
        tenant_id=tenant_id,
        category=NotificationCategory.SECURITY,
        channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
        email_subject="Réinitialisation de votre mot de passe",
        email_body="""
        <p>Une demande de réinitialisation de mot de passe a été effectuée.</p>
        <p>Cliquez sur le lien ci-dessous pour définir un nouveau mot de passe :</p>
        <p><a href="{{reset_url}}">Réinitialiser mon mot de passe</a></p>
        <p>Ce lien expire dans {{expiry_hours}} heures.</p>
        <p>Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.</p>
        """,
        sms_body="AZALSCORE: Votre code de réinitialisation est {{reset_code}}. Valide {{expiry_minutes}} min.",
        is_system=True,
    )


def create_invoice_template(tenant_id: str) -> NotificationTemplate:
    """Template de facture."""
    return NotificationTemplate(
        template_id=f"invoice_{tenant_id}",
        name="Nouvelle facture",
        tenant_id=tenant_id,
        category=NotificationCategory.TRANSACTIONAL,
        channels=[NotificationChannel.EMAIL],
        email_subject="Facture {{invoice_number}} - {{company_name}}",
        email_body="""
        <p>Bonjour {{customer_name}},</p>
        <p>Veuillez trouver ci-joint votre facture {{invoice_number}} d'un montant de {{total_amount}} €.</p>
        <p>Date d'échéance : {{due_date}}</p>
        <p><a href="{{invoice_url}}">Voir la facture</a></p>
        """,
        is_system=True,
    )


_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Retourne l'instance du service de notifications."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service


def initialize_notification_service(
    email_config: Optional[dict] = None,
    sms_config: Optional[dict] = None,
    push_config: Optional[dict] = None,
) -> NotificationService:
    """Initialise le service de notifications avec les providers."""
    global _notification_service

    service = NotificationService()

    # Email provider
    if email_config:
        if email_config.get("provider") == "sendgrid":
            provider = SendGridProvider(
                api_key=email_config["api_key"],
                from_email=email_config["from_email"],
                from_name=email_config.get("from_name", "AZALSCORE"),
            )
        else:
            provider = SMTPEmailProvider(
                host=email_config.get("host", "smtp.gmail.com"),
                port=email_config.get("port", 587),
                username=email_config.get("username", ""),
                password=email_config.get("password", ""),
                from_email=email_config.get("from_email", ""),
                from_name=email_config.get("from_name", "AZALSCORE"),
            )
        service.register_provider(NotificationChannel.EMAIL, provider)

    # SMS provider
    if sms_config:
        if sms_config.get("provider") == "twilio":
            provider = TwilioSMSProvider(
                account_sid=sms_config["account_sid"],
                auth_token=sms_config["auth_token"],
                from_number=sms_config["from_number"],
            )
            service.register_provider(NotificationChannel.SMS, provider)

    # Push provider
    if push_config:
        if push_config.get("provider") == "fcm":
            provider = FCMPushProvider(
                server_key=push_config["server_key"],
                project_id=push_config["project_id"],
            )
            service.register_provider(NotificationChannel.PUSH, provider)

    # In-app notifications (toujours activé)
    service.register_provider(NotificationChannel.IN_APP, InAppProvider())

    # Webhook (toujours activé)
    service.register_provider(NotificationChannel.WEBHOOK, WebhookProvider())

    # Slack (si configuré)
    service.register_provider(NotificationChannel.SLACK, SlackProvider())

    _notification_service = service
    logger.info("Notification service initialized")

    return service
