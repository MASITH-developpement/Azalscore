"""
AZALS MODULE - NOTIFICATIONS: Repository
=========================================

Repositories SQLAlchemy pour la gestion des notifications multicanal.
Conforme aux normes AZALSCORE (isolation tenant, type hints).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc
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


class NotificationTemplateRepository:
    """Repository pour les templates de notification."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(NotificationTemplate).filter(
            NotificationTemplate.tenant_id == self.tenant_id
        )

    def get_by_id(self, template_id: UUID) -> Optional[NotificationTemplate]:
        """Recupere un template par ID."""
        return self._base_query().filter(
            NotificationTemplate.id == template_id
        ).first()

    def get_by_code(self, code: str) -> Optional[NotificationTemplate]:
        """Recupere un template par code."""
        return self._base_query().filter(
            NotificationTemplate.code == code,
            NotificationTemplate.status == TemplateStatusDB.ACTIVE
        ).first()

    def list(
        self,
        notification_type: Optional[NotificationTypeDB] = None,
        status: Optional[TemplateStatusDB] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[NotificationTemplate], int]:
        """Liste les templates avec filtres."""
        query = self._base_query()

        if notification_type:
            query = query.filter(NotificationTemplate.notification_type == notification_type)
        if status:
            query = query.filter(NotificationTemplate.status == status)
        if category:
            query = query.filter(NotificationTemplate.category == category)
        if search:
            query = query.filter(
                or_(
                    NotificationTemplate.name.ilike(f"%{search}%"),
                    NotificationTemplate.code.ilike(f"%{search}%"),
                    NotificationTemplate.description.ilike(f"%{search}%")
                )
            )

        total = query.count()
        items = query.order_by(desc(NotificationTemplate.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def create(self, data: Dict[str, Any], user_id: Optional[UUID] = None) -> NotificationTemplate:
        """Cree un nouveau template."""
        template = NotificationTemplate(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def update(
        self,
        template: NotificationTemplate,
        data: Dict[str, Any]
    ) -> NotificationTemplate:
        """Met a jour un template."""
        for key, value in data.items():
            if hasattr(template, key) and value is not None:
                setattr(template, key, value)
        template.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(template)
        return template

    def delete(self, template: NotificationTemplate) -> None:
        """Supprime un template (archive)."""
        template.status = TemplateStatusDB.ARCHIVED
        template.updated_at = datetime.utcnow()
        self.db.commit()


class NotificationRepository:
    """Repository pour les notifications."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(Notification).filter(
            Notification.tenant_id == self.tenant_id
        )

    def get_by_id(self, notification_id: UUID) -> Optional[Notification]:
        """Recupere une notification par ID."""
        return self._base_query().filter(
            Notification.id == notification_id
        ).first()

    def list(
        self,
        user_id: Optional[UUID] = None,
        channel: Optional[NotificationChannelDB] = None,
        status: Optional[NotificationStatusDB] = None,
        notification_type: Optional[NotificationTypeDB] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Notification], int]:
        """Liste les notifications avec filtres."""
        query = self._base_query()

        if user_id:
            query = query.filter(Notification.user_id == user_id)
        if channel:
            query = query.filter(Notification.channel == channel)
        if status:
            query = query.filter(Notification.status == status)
        if notification_type:
            query = query.filter(Notification.notification_type == notification_type)
        if reference_type:
            query = query.filter(Notification.reference_type == reference_type)
        if reference_id:
            query = query.filter(Notification.reference_id == reference_id)
        if date_from:
            query = query.filter(Notification.created_at >= date_from)
        if date_to:
            query = query.filter(Notification.created_at <= date_to)

        total = query.count()
        items = query.order_by(desc(Notification.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def get_pending(self, limit: int = 100) -> List[Notification]:
        """Recupere les notifications en attente d'envoi."""
        now = datetime.utcnow()
        return self._base_query().filter(
            Notification.status == NotificationStatusDB.PENDING,
            or_(
                Notification.scheduled_at.is_(None),
                Notification.scheduled_at <= now
            ),
            or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > now
            )
        ).order_by(
            Notification.priority.desc(),
            Notification.created_at.asc()
        ).limit(limit).all()

    def get_for_retry(self, limit: int = 50) -> List[Notification]:
        """Recupere les notifications a reessayer."""
        now = datetime.utcnow()
        return self._base_query().filter(
            Notification.status == NotificationStatusDB.FAILED,
            Notification.retry_count < Notification.max_retries,
            Notification.next_retry_at <= now
        ).order_by(Notification.next_retry_at.asc()).limit(limit).all()

    def get_user_unread(self, user_id: UUID, limit: int = 50) -> List[Notification]:
        """Recupere les notifications non lues d'un utilisateur."""
        return self._base_query().filter(
            Notification.user_id == user_id,
            Notification.channel == NotificationChannelDB.IN_APP,
            Notification.status.in_([
                NotificationStatusDB.SENT,
                NotificationStatusDB.DELIVERED
            ]),
            Notification.read_at.is_(None)
        ).order_by(desc(Notification.created_at)).limit(limit).all()

    def count_unread(self, user_id: UUID) -> int:
        """Compte les notifications non lues."""
        return self._base_query().filter(
            Notification.user_id == user_id,
            Notification.channel == NotificationChannelDB.IN_APP,
            Notification.status.in_([
                NotificationStatusDB.SENT,
                NotificationStatusDB.DELIVERED
            ]),
            Notification.read_at.is_(None)
        ).count()

    def create(self, data: Dict[str, Any]) -> Notification:
        """Cree une nouvelle notification."""
        notification = Notification(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def create_batch(self, notifications_data: List[Dict[str, Any]]) -> List[Notification]:
        """Cree plusieurs notifications en lot."""
        notifications = []
        for data in notifications_data:
            notification = Notification(
                tenant_id=self.tenant_id,
                **data
            )
            self.db.add(notification)
            notifications.append(notification)
        self.db.commit()
        for n in notifications:
            self.db.refresh(n)
        return notifications

    def update(self, notification: Notification, data: Dict[str, Any]) -> Notification:
        """Met a jour une notification."""
        for key, value in data.items():
            if hasattr(notification, key) and value is not None:
                setattr(notification, key, value)
        notification.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_sent(self, notification: Notification, provider_id: Optional[str] = None) -> Notification:
        """Marque une notification comme envoyee."""
        notification.status = NotificationStatusDB.SENT
        notification.sent_at = datetime.utcnow()
        if provider_id:
            notification.provider_id = provider_id
        notification.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_delivered(self, notification: Notification) -> Notification:
        """Marque une notification comme livree."""
        notification.status = NotificationStatusDB.DELIVERED
        notification.delivered_at = datetime.utcnow()
        notification.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_read(self, notification: Notification) -> Notification:
        """Marque une notification comme lue."""
        notification.status = NotificationStatusDB.READ
        notification.read_at = datetime.utcnow()
        notification.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_failed(
        self,
        notification: Notification,
        reason: str,
        schedule_retry: bool = True
    ) -> Notification:
        """Marque une notification comme echouee."""
        notification.status = NotificationStatusDB.FAILED
        notification.failed_at = datetime.utcnow()
        notification.failure_reason = reason
        notification.retry_count += 1

        if schedule_retry and notification.retry_count < notification.max_retries:
            # Backoff exponentiel: 1min, 5min, 15min, 1h
            delays = [1, 5, 15, 60]
            delay_idx = min(notification.retry_count - 1, len(delays) - 1)
            notification.next_retry_at = datetime.utcnow() + timedelta(minutes=delays[delay_idx])

        notification.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_all_read(self, user_id: UUID) -> int:
        """Marque toutes les notifications d'un utilisateur comme lues."""
        now = datetime.utcnow()
        result = self._base_query().filter(
            Notification.user_id == user_id,
            Notification.channel == NotificationChannelDB.IN_APP,
            Notification.read_at.is_(None)
        ).update({
            Notification.status: NotificationStatusDB.READ,
            Notification.read_at: now,
            Notification.updated_at: now
        })
        self.db.commit()
        return result

    def delete_old(self, days: int = 90) -> int:
        """Supprime les notifications anciennes."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = self._base_query().filter(
            Notification.created_at < cutoff
        ).delete(synchronize_session=False)
        self.db.commit()
        return result


class NotificationBatchRepository:
    """Repository pour les lots de notifications."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(NotificationBatch).filter(
            NotificationBatch.tenant_id == self.tenant_id
        )

    def get_by_id(self, batch_id: UUID) -> Optional[NotificationBatch]:
        """Recupere un batch par ID."""
        return self._base_query().filter(
            NotificationBatch.id == batch_id
        ).first()

    def list(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[NotificationBatch], int]:
        """Liste les batches."""
        query = self._base_query()

        if status:
            query = query.filter(NotificationBatch.status == status)

        total = query.count()
        items = query.order_by(desc(NotificationBatch.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def create(self, data: Dict[str, Any], user_id: Optional[UUID] = None) -> NotificationBatch:
        """Cree un nouveau batch."""
        batch = NotificationBatch(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data
        )
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def update_progress(
        self,
        batch: NotificationBatch,
        processed: int,
        sent: int,
        failed: int
    ) -> NotificationBatch:
        """Met a jour la progression d'un batch."""
        batch.processed_count = processed
        batch.sent_count = sent
        batch.failed_count = failed
        batch.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def complete(self, batch: NotificationBatch) -> NotificationBatch:
        """Marque un batch comme termine."""
        batch.status = "completed"
        batch.completed_at = datetime.utcnow()
        batch.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(batch)
        return batch


class UserPreferenceRepository:
    """Repository pour les preferences utilisateur."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(UserNotificationPreference).filter(
            UserNotificationPreference.tenant_id == self.tenant_id
        )

    def get_by_user(self, user_id: UUID) -> Optional[UserNotificationPreference]:
        """Recupere les preferences d'un utilisateur."""
        return self._base_query().filter(
            UserNotificationPreference.user_id == user_id
        ).first()

    def get_or_create(self, user_id: UUID) -> UserNotificationPreference:
        """Recupere ou cree les preferences d'un utilisateur."""
        pref = self.get_by_user(user_id)
        if not pref:
            pref = UserNotificationPreference(
                tenant_id=self.tenant_id,
                user_id=user_id
            )
            self.db.add(pref)
            self.db.commit()
            self.db.refresh(pref)
        return pref

    def update(
        self,
        pref: UserNotificationPreference,
        data: Dict[str, Any]
    ) -> UserNotificationPreference:
        """Met a jour les preferences."""
        for key, value in data.items():
            if hasattr(pref, key) and value is not None:
                setattr(pref, key, value)
        pref.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(pref)
        return pref

    def list_with_digest(self, frequency: str = "daily") -> List[UserNotificationPreference]:
        """Liste les utilisateurs avec digest active."""
        return self._base_query().filter(
            UserNotificationPreference.digest_enabled == True,
            UserNotificationPreference.digest_frequency == frequency
        ).all()


class WebhookSubscriptionRepository:
    """Repository pour les abonnements webhook."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(WebhookSubscription).filter(
            WebhookSubscription.tenant_id == self.tenant_id
        )

    def get_by_id(self, subscription_id: UUID) -> Optional[WebhookSubscription]:
        """Recupere un abonnement par ID."""
        return self._base_query().filter(
            WebhookSubscription.id == subscription_id
        ).first()

    def list(
        self,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[WebhookSubscription], int]:
        """Liste les abonnements."""
        query = self._base_query()

        if is_active is not None:
            query = query.filter(WebhookSubscription.is_active == is_active)

        total = query.count()
        items = query.order_by(desc(WebhookSubscription.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def get_by_event(self, event_type: str) -> List[WebhookSubscription]:
        """Recupere les abonnements pour un type d'evenement."""
        return self._base_query().filter(
            WebhookSubscription.is_active == True,
            WebhookSubscription.event_types.contains([event_type])
        ).all()

    def create(self, data: Dict[str, Any], user_id: Optional[UUID] = None) -> WebhookSubscription:
        """Cree un nouvel abonnement."""
        subscription = WebhookSubscription(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data
        )
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def update(
        self,
        subscription: WebhookSubscription,
        data: Dict[str, Any]
    ) -> WebhookSubscription:
        """Met a jour un abonnement."""
        for key, value in data.items():
            if hasattr(subscription, key) and value is not None:
                setattr(subscription, key, value)
        subscription.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def delete(self, subscription: WebhookSubscription) -> None:
        """Supprime un abonnement."""
        self.db.delete(subscription)
        self.db.commit()

    def increment_failure(self, subscription: WebhookSubscription) -> WebhookSubscription:
        """Incremente le compteur d'echecs."""
        subscription.failure_count += 1
        subscription.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def reset_failure(self, subscription: WebhookSubscription) -> WebhookSubscription:
        """Reinitialise le compteur d'echecs."""
        subscription.failure_count = 0
        subscription.last_triggered_at = datetime.utcnow()
        subscription.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(subscription)
        return subscription
