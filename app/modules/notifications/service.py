"""
Service de Notifications Multicanal - GAP-047

Gestion complete des notifications avec persistence SQLAlchemy:
- Email, SMS, Push, In-App, Webhooks
- Templates avec variables
- Preferences utilisateurs
- Envoi en masse (batches)
- Planification differee
- Suivi et analytics

CRITIQUE: Utilise les repositories pour l'isolation multi-tenant.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
import re

from sqlalchemy.orm import Session

from .models import (
    Notification,
    NotificationBatch,
    NotificationTemplate,
    UserNotificationPreference,
    WebhookSubscription,
    NotificationChannelDB,
    NotificationStatusDB,
    NotificationPriorityDB,
    NotificationTypeDB,
    TemplateStatusDB,
)
from .repository import (
    NotificationTemplateRepository,
    NotificationRepository,
    NotificationBatchRepository,
    UserPreferenceRepository,
    WebhookSubscriptionRepository,
)


# ============================================================
# ENUMERATIONS LOCALES
# ============================================================

class NotificationChannel:
    """Canaux de notification."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NotificationStatus:
    """Statuts de notification."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationPriority:
    """Priorites de notification."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class NotificationResult:
    """Resultat d'envoi de notification."""
    success: bool
    notification_id: Optional[str] = None
    channel: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None


@dataclass
class BatchResult:
    """Resultat d'envoi en masse."""
    batch_id: str
    total: int = 0
    sent: int = 0
    failed: int = 0
    pending: int = 0
    errors: List[str] = field(default_factory=list)


# ============================================================
# SERVICE PRINCIPAL
# ============================================================

class NotificationService:
    """Service de gestion des notifications avec persistence SQLAlchemy."""

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        email_provider: Optional[Callable] = None,
        sms_provider: Optional[Callable] = None,
        push_provider: Optional[Callable] = None,
        webhook_client: Optional[Callable] = None,
        rate_limiter: Optional[Any] = None
    ):
        self.db = db
        self.tenant_id = tenant_id

        # Providers
        self.email_provider = email_provider
        self.sms_provider = sms_provider
        self.push_provider = push_provider
        self.webhook_client = webhook_client
        self.rate_limiter = rate_limiter

        # Repositories avec isolation tenant
        self.template_repo = NotificationTemplateRepository(db, tenant_id)
        self.notification_repo = NotificationRepository(db, tenant_id)
        self.batch_repo = NotificationBatchRepository(db, tenant_id)
        self.preference_repo = UserPreferenceRepository(db, tenant_id)
        self.webhook_repo = WebhookSubscriptionRepository(db, tenant_id)

        # Regex pour les variables
        self._variable_pattern = re.compile(r'\{\{([^}]+)\}\}')

    # =========================================================================
    # Templates
    # =========================================================================

    def create_template(
        self,
        code: str,
        name: str,
        notification_type: str,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        html_body: Optional[str] = None,
        channels: Optional[List[str]] = None,
        category: Optional[str] = None,
        description: Optional[str] = None,
        variables: Optional[List[str]] = None,
        created_by: Optional[str] = None,
        **kwargs
    ) -> NotificationTemplate:
        """Cree un template de notification."""
        # Verifier unicite du code
        existing = self.template_repo.get_by_code(code)
        if existing:
            raise ValueError(f"Template {code} existe deja")

        # Extraire les variables du body si non fournies
        if not variables and body:
            variables = self._extract_variables(body)
            if html_body:
                variables.extend(self._extract_variables(html_body))
            variables = list(set(variables))

        data = {
            "code": code,
            "name": name,
            "notification_type": notification_type,
            "subject": subject,
            "body": body,
            "html_body": html_body,
            "channels": channels or [NotificationChannel.EMAIL],
            "category": category,
            "description": description,
            "variables": variables or [],
            "status": TemplateStatusDB.ACTIVE,
            **kwargs
        }
        return self.template_repo.create(data, user_id=created_by)

    def get_template(self, template_id: str) -> Optional[NotificationTemplate]:
        """Recupere un template par ID."""
        return self.template_repo.get_by_id(template_id)

    def get_template_by_code(self, code: str) -> Optional[NotificationTemplate]:
        """Recupere un template par code."""
        return self.template_repo.get_by_code(code)

    def list_templates(
        self,
        notification_type: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[NotificationTemplate], int]:
        """Liste les templates."""
        return self.template_repo.list(
            notification_type=notification_type,
            category=category,
            search=search,
            page=page,
            page_size=page_size
        )

    def update_template(
        self,
        template_id: str,
        updated_by: Optional[str] = None,
        **updates
    ) -> Optional[NotificationTemplate]:
        """Met a jour un template."""
        template = self.template_repo.get_by_id(template_id)
        if not template:
            return None
        return self.template_repo.update(template, updates, user_id=updated_by)

    def delete_template(self, template_id: str) -> bool:
        """Archive un template."""
        template = self.template_repo.get_by_id(template_id)
        if not template:
            return False
        self.template_repo.update(template, {"status": TemplateStatusDB.ARCHIVED})
        return True

    def _extract_variables(self, text: str) -> List[str]:
        """Extrait les variables d'un texte."""
        matches = self._variable_pattern.findall(text)
        return [m.strip() for m in matches]

    def _render_template(
        self,
        template: str,
        variables: Dict[str, Any]
    ) -> str:
        """Rend un template avec les variables."""
        def replace_var(match):
            var_name = match.group(1).strip()
            return str(variables.get(var_name, f"{{{{var_name}}}}"))

        return self._variable_pattern.sub(replace_var, template)

    # =========================================================================
    # Notifications
    # =========================================================================

    def send_notification(
        self,
        template_code: str,
        recipient_id: str,
        recipient_email: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        channels: Optional[List[str]] = None,
        priority: str = NotificationPriority.NORMAL,
        scheduled_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationResult:
        """Envoie une notification."""
        # Recuperer le template
        template = self.template_repo.get_by_code(template_code)
        if not template:
            return NotificationResult(
                success=False,
                error=f"Template {template_code} non trouve"
            )

        # Verifier les preferences utilisateur
        preferences = self.preference_repo.get_by_user(recipient_id)
        if preferences and not preferences.notifications_enabled:
            return NotificationResult(
                success=False,
                error="Notifications desactivees par l'utilisateur"
            )

        # Determiner les canaux
        effective_channels = channels or template.channels or [NotificationChannel.EMAIL]

        # Filtrer selon preferences
        if preferences and preferences.channel_preferences:
            effective_channels = [
                ch for ch in effective_channels
                if preferences.channel_preferences.get(ch, True)
            ]

        if not effective_channels:
            return NotificationResult(
                success=False,
                error="Aucun canal disponible"
            )

        # Rendre le contenu
        vars_dict = variables or {}
        subject = self._render_template(template.subject or "", vars_dict) if template.subject else None
        body = self._render_template(template.body or "", vars_dict) if template.body else None
        html_body = self._render_template(template.html_body or "", vars_dict) if template.html_body else None

        # Creer la notification
        notification_data = {
            "template_id": str(template.id),
            "recipient_id": recipient_id,
            "recipient_email": recipient_email,
            "recipient_phone": recipient_phone,
            "subject": subject,
            "body": body,
            "html_body": html_body,
            "channels": effective_channels,
            "priority": priority,
            "status": NotificationStatusDB.PENDING,
            "scheduled_at": scheduled_at,
            "variables": vars_dict,
            "metadata": metadata or {},
        }
        notification = self.notification_repo.create(notification_data)

        # Si planifiee, retourner sans envoyer
        if scheduled_at and scheduled_at > datetime.utcnow():
            return NotificationResult(
                success=True,
                notification_id=str(notification.id),
                message="Notification planifiee"
            )

        # Envoyer sur chaque canal
        results = []
        for channel in effective_channels:
            result = self._send_to_channel(notification, channel)
            results.append(result)

        # Mettre a jour le statut
        all_success = all(r.success for r in results)
        any_success = any(r.success for r in results)

        if all_success:
            self.notification_repo.mark_sent(notification)
        elif any_success:
            self.notification_repo.mark_partial(notification)
        else:
            self.notification_repo.mark_failed(
                notification,
                "; ".join(r.error or "" for r in results if r.error)
            )

        return NotificationResult(
            success=any_success,
            notification_id=str(notification.id),
            channel=",".join(effective_channels),
            message="Notification envoyee" if any_success else "Echec d'envoi"
        )

    def _send_to_channel(
        self,
        notification: Notification,
        channel: str
    ) -> NotificationResult:
        """Envoie une notification sur un canal specifique."""
        try:
            if channel == NotificationChannel.EMAIL:
                if self.email_provider and notification.recipient_email:
                    self.email_provider(
                        to=notification.recipient_email,
                        subject=notification.subject,
                        body=notification.body,
                        html_body=notification.html_body
                    )
                    return NotificationResult(success=True, channel=channel)
                return NotificationResult(
                    success=False,
                    channel=channel,
                    error="Email provider non configure ou email manquant"
                )

            elif channel == NotificationChannel.SMS:
                if self.sms_provider and notification.recipient_phone:
                    self.sms_provider(
                        to=notification.recipient_phone,
                        message=notification.body
                    )
                    return NotificationResult(success=True, channel=channel)
                return NotificationResult(
                    success=False,
                    channel=channel,
                    error="SMS provider non configure ou telephone manquant"
                )

            elif channel == NotificationChannel.PUSH:
                if self.push_provider:
                    self.push_provider(
                        user_id=notification.recipient_id,
                        title=notification.subject,
                        body=notification.body
                    )
                    return NotificationResult(success=True, channel=channel)
                return NotificationResult(
                    success=False,
                    channel=channel,
                    error="Push provider non configure"
                )

            elif channel == NotificationChannel.IN_APP:
                # In-app est toujours "envoye" (stocke en DB)
                return NotificationResult(success=True, channel=channel)

            elif channel == NotificationChannel.WEBHOOK:
                webhooks = self.webhook_repo.list_active_for_event(
                    notification.template_id
                )
                for webhook in webhooks:
                    self._send_webhook(webhook, notification)
                return NotificationResult(success=True, channel=channel)

            return NotificationResult(
                success=False,
                channel=channel,
                error=f"Canal {channel} non supporte"
            )

        except Exception as e:
            return NotificationResult(
                success=False,
                channel=channel,
                error=str(e)
            )

    def _send_webhook(
        self,
        webhook: WebhookSubscription,
        notification: Notification
    ) -> bool:
        """Envoie une notification webhook."""
        if not self.webhook_client or not webhook.url:
            return False

        try:
            payload = {
                "notification_id": str(notification.id),
                "template_id": str(notification.template_id),
                "recipient_id": notification.recipient_id,
                "subject": notification.subject,
                "body": notification.body,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.webhook_client(webhook.url, payload, webhook.secret)
            return True
        except Exception:
            return False

    def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Recupere une notification."""
        return self.notification_repo.get_by_id(notification_id)

    def list_notifications(
        self,
        recipient_id: Optional[str] = None,
        status: Optional[str] = None,
        channel: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Notification], int]:
        """Liste les notifications."""
        return self.notification_repo.list(
            recipient_id=recipient_id,
            status=status,
            channel=channel,
            page=page,
            page_size=page_size
        )

    def mark_as_read(self, notification_id: str) -> Optional[Notification]:
        """Marque une notification comme lue."""
        notification = self.notification_repo.get_by_id(notification_id)
        if notification:
            return self.notification_repo.mark_read(notification)
        return None

    def get_unread_count(self, recipient_id: str) -> int:
        """Compte les notifications non lues."""
        return self.notification_repo.count_unread(recipient_id)

    # =========================================================================
    # Envoi en masse
    # =========================================================================

    def send_batch(
        self,
        template_code: str,
        recipients: List[Dict[str, Any]],
        common_variables: Optional[Dict[str, Any]] = None,
        scheduled_at: Optional[datetime] = None,
        created_by: Optional[str] = None
    ) -> BatchResult:
        """Envoie une notification en masse."""
        # Creer le batch
        batch_data = {
            "template_code": template_code,
            "total_count": len(recipients),
            "status": "pending",
            "scheduled_at": scheduled_at,
            "created_by": created_by,
        }
        batch = self.batch_repo.create(batch_data)

        result = BatchResult(
            batch_id=str(batch.id),
            total=len(recipients)
        )

        # Envoyer a chaque destinataire
        for recipient in recipients:
            variables = {**(common_variables or {}), **recipient.get("variables", {})}

            notif_result = self.send_notification(
                template_code=template_code,
                recipient_id=recipient.get("id", ""),
                recipient_email=recipient.get("email"),
                recipient_phone=recipient.get("phone"),
                variables=variables,
                scheduled_at=scheduled_at
            )

            if notif_result.success:
                result.sent += 1
            else:
                result.failed += 1
                if notif_result.error:
                    result.errors.append(notif_result.error)

        # Mettre a jour le batch
        self.batch_repo.update(batch, {
            "sent_count": result.sent,
            "failed_count": result.failed,
            "status": "completed" if result.failed == 0 else "partial"
        })

        return result

    def get_batch(self, batch_id: str) -> Optional[NotificationBatch]:
        """Recupere un batch."""
        return self.batch_repo.get_by_id(batch_id)

    def list_batches(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[NotificationBatch], int]:
        """Liste les batches."""
        return self.batch_repo.list(status=status, page=page, page_size=page_size)

    # =========================================================================
    # Preferences utilisateur
    # =========================================================================

    def get_user_preferences(self, user_id: str) -> Optional[UserNotificationPreference]:
        """Recupere les preferences d'un utilisateur."""
        return self.preference_repo.get_by_user(user_id)

    def update_user_preferences(
        self,
        user_id: str,
        notifications_enabled: Optional[bool] = None,
        channel_preferences: Optional[Dict[str, bool]] = None,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None,
        frequency_cap: Optional[int] = None
    ) -> UserNotificationPreference:
        """Met a jour les preferences d'un utilisateur."""
        prefs = self.preference_repo.get_by_user(user_id)

        updates = {}
        if notifications_enabled is not None:
            updates["notifications_enabled"] = notifications_enabled
        if channel_preferences is not None:
            updates["channel_preferences"] = channel_preferences
        if quiet_hours_start is not None:
            updates["quiet_hours_start"] = quiet_hours_start
        if quiet_hours_end is not None:
            updates["quiet_hours_end"] = quiet_hours_end
        if frequency_cap is not None:
            updates["frequency_cap"] = frequency_cap

        if prefs:
            return self.preference_repo.update(prefs, updates)
        else:
            return self.preference_repo.create({
                "user_id": user_id,
                **updates
            })

    # =========================================================================
    # Webhooks
    # =========================================================================

    def create_webhook_subscription(
        self,
        url: str,
        events: List[str],
        name: Optional[str] = None,
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        created_by: Optional[str] = None
    ) -> WebhookSubscription:
        """Cree un abonnement webhook."""
        import secrets as secrets_module

        data = {
            "url": url,
            "events": events,
            "name": name,
            "secret": secret or secrets_module.token_urlsafe(32),
            "headers": headers or {},
            "is_active": True,
            "created_by": created_by,
        }
        return self.webhook_repo.create(data)

    def list_webhook_subscriptions(self) -> List[WebhookSubscription]:
        """Liste les abonnements webhook."""
        return self.webhook_repo.list_all()

    def delete_webhook_subscription(self, webhook_id: str) -> bool:
        """Supprime un abonnement webhook."""
        webhook = self.webhook_repo.get_by_id(webhook_id)
        if webhook:
            self.webhook_repo.delete(webhook)
            return True
        return False

    # =========================================================================
    # Statistiques
    # =========================================================================

    def get_statistics(
        self,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Recupere les statistiques de notifications."""
        return self.notification_repo.get_statistics(period_days)

    def process_scheduled(self) -> int:
        """Traite les notifications planifiees."""
        notifications = self.notification_repo.get_scheduled_due()
        processed = 0

        for notification in notifications:
            template = self.template_repo.get_by_id(str(notification.template_id))
            if template:
                for channel in notification.channels or []:
                    self._send_to_channel(notification, channel)
                self.notification_repo.mark_sent(notification)
                processed += 1

        return processed


# ============================================================
# FACTORY
# ============================================================

def create_notification_service(
    db: Session,
    tenant_id: str,
    email_provider: Optional[Callable] = None,
    sms_provider: Optional[Callable] = None,
    push_provider: Optional[Callable] = None,
    webhook_client: Optional[Callable] = None
) -> NotificationService:
    """Cree un service de notifications."""
    return NotificationService(
        db=db,
        tenant_id=tenant_id,
        email_provider=email_provider,
        sms_provider=sms_provider,
        push_provider=push_provider,
        webhook_client=webhook_client
    )
