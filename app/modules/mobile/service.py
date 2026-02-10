"""
AZALS MODULE 18 - Mobile App Service
=====================================
Logique métier pour le backend mobile.
"""

import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from .models import (
    MobileActivityLog,
    MobileAppConfig,
    MobileCrashReport,
    MobileDevice,
    MobilePreferences,
    MobileSession,
    PushNotification,
    SyncCheckpoint,
    SyncQueue,
)
from .schemas import (
    ActivityBatch,
    ActivityLog,
    CrashReport,
    DeviceRegister,
    DeviceUpdate,
    NotificationBulk,
    NotificationCreate,
    PreferencesUpdate,
    SyncBatch,
    SyncConflict,
)


class MobileService:
    """Service Mobile complet."""

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id  # Pour CORE SaaS v2

    # ========================================================================
    # DEVICES
    # ========================================================================

    def register_device(self, user_id: int, data: DeviceRegister) -> MobileDevice:
        """Enregistrer un nouvel appareil."""
        # Vérifier si l'appareil existe déjà
        existing = self.db.query(MobileDevice).filter(
            MobileDevice.device_id == data.device_id
        ).first()

        if existing:
            # Mettre à jour l'appareil existant
            existing.user_id = user_id
            existing.tenant_id = self.tenant_id
            existing.device_name = data.device_name or existing.device_name
            existing.platform = data.platform
            existing.os_version = data.os_version
            existing.app_version = data.app_version
            existing.model = data.model
            existing.push_token = data.push_token
            existing.is_active = True
            existing.last_active = datetime.utcnow()
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Créer nouvel appareil
        device = MobileDevice(
            tenant_id=self.tenant_id,
            user_id=user_id,
            device_id=data.device_id,
            device_name=data.device_name,
            platform=data.platform,
            os_version=data.os_version,
            app_version=data.app_version,
            model=data.model,
            push_token=data.push_token,
            push_provider="fcm" if data.platform == "android" else "apns",
            is_active=True,
            last_active=datetime.utcnow()
        )
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        return device

    def get_device(self, device_id: int) -> MobileDevice | None:
        """Récupérer un appareil par ID."""
        return self.db.query(MobileDevice).filter(
            MobileDevice.tenant_id == self.tenant_id,
            MobileDevice.id == device_id
        ).first()

    def get_device_by_uuid(self, device_uuid: str) -> MobileDevice | None:
        """Récupérer un appareil par UUID."""
        return self.db.query(MobileDevice).filter(
            MobileDevice.device_id == device_uuid
        ).first()

    def list_user_devices(self, user_id: int) -> list[MobileDevice]:
        """Lister les appareils d'un utilisateur."""
        return self.db.query(MobileDevice).filter(
            MobileDevice.tenant_id == self.tenant_id,
            MobileDevice.user_id == user_id,
            MobileDevice.is_active
        ).order_by(MobileDevice.last_active.desc()).all()

    def update_device(self, device_id: int, data: DeviceUpdate) -> MobileDevice | None:
        """Mettre à jour un appareil."""
        device = self.get_device(device_id)
        if not device:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(device, field, value)

        device.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(device)
        return device

    def deactivate_device(self, device_id: int) -> bool:
        """Désactiver un appareil."""
        device = self.get_device(device_id)
        if not device:
            return False

        device.is_active = False
        device.updated_at = datetime.utcnow()

        # Révoquer toutes les sessions
        self.db.query(MobileSession).filter(
            MobileSession.device_id == device_id,
            MobileSession.is_active
        ).update({
            "is_active": False,
            "revoked": True,
            "revoked_at": datetime.utcnow(),
            "revoked_reason": "Device deactivated"
        })

        self.db.commit()
        return True

    def update_device_activity(
        self, device_id: int, ip: str | None = None, location: dict | None = None
    ) -> None:
        """Mettre à jour l'activité d'un appareil."""
        device = self.get_device(device_id)
        if device:
            device.last_active = datetime.utcnow()
            if ip:
                device.last_ip = ip
            if location:
                device.last_location = location
            self.db.commit()

    # ========================================================================
    # SESSIONS
    # ========================================================================

    def create_session(
        self, user_id: int, device_id: int, hours_valid: int = 24
    ) -> MobileSession:
        """Créer une session mobile."""
        device = self.get_device(device_id)
        if not device:
            raise ValueError("Appareil introuvable")

        # Générer tokens
        session_token = secrets.token_urlsafe(64)
        refresh_token = secrets.token_urlsafe(64)

        session = MobileSession(
            tenant_id=self.tenant_id,
            user_id=user_id,
            device_id=device_id,
            session_token=session_token,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(hours=hours_valid),
            refresh_expires_at=datetime.utcnow() + timedelta(days=30),
            is_active=True,
            last_activity=datetime.utcnow()
        )
        self.db.add(session)

        # Mettre à jour activité appareil
        device.last_active = datetime.utcnow()

        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session_by_token(self, token: str) -> MobileSession | None:
        """Récupérer session par token."""
        return self.db.query(MobileSession).filter(
            MobileSession.session_token == token,
            MobileSession.is_active,
            not MobileSession.revoked
        ).first()

    def refresh_session(self, refresh_token: str) -> MobileSession | None:
        """Renouveler une session."""
        session = self.db.query(MobileSession).filter(
            MobileSession.refresh_token == refresh_token,
            not MobileSession.revoked
        ).first()

        if not session:
            return None

        if session.refresh_expires_at < datetime.utcnow():
            return None

        # Créer nouvelle session
        new_session = MobileSession(
            tenant_id=session.tenant_id,
            user_id=session.user_id,
            device_id=session.device_id,
            session_token=secrets.token_urlsafe(64),
            refresh_token=secrets.token_urlsafe(64),
            expires_at=datetime.utcnow() + timedelta(hours=24),
            refresh_expires_at=datetime.utcnow() + timedelta(days=30),
            is_active=True,
            last_activity=datetime.utcnow()
        )

        # Révoquer ancienne session
        session.is_active = False
        session.revoked = True
        session.revoked_at = datetime.utcnow()
        session.revoked_reason = "Token refreshed"

        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)
        return new_session

    def revoke_session(self, session_id: int, reason: str = "Manual logout") -> bool:
        """Révoquer une session."""
        session = self.db.query(MobileSession).filter(
            MobileSession.tenant_id == self.tenant_id,
            MobileSession.id == session_id
        ).first()

        if not session:
            return False

        session.is_active = False
        session.revoked = True
        session.revoked_at = datetime.utcnow()
        session.revoked_reason = reason
        self.db.commit()
        return True

    def revoke_user_sessions(self, user_id: int) -> int:
        """Révoquer toutes les sessions d'un utilisateur."""
        result = self.db.query(MobileSession).filter(
            MobileSession.tenant_id == self.tenant_id,
            MobileSession.user_id == user_id,
            MobileSession.is_active
        ).update({
            "is_active": False,
            "revoked": True,
            "revoked_at": datetime.utcnow(),
            "revoked_reason": "All sessions revoked"
        })
        self.db.commit()
        return result

    def update_session_activity(self, session: MobileSession, ip: str | None = None) -> None:
        """Mettre à jour l'activité d'une session."""
        session.last_activity = datetime.utcnow()
        if ip:
            session.last_ip = ip
        self.db.commit()

    # ========================================================================
    # NOTIFICATIONS
    # ========================================================================

    def send_notification(self, data: NotificationCreate) -> PushNotification:
        """Envoyer une notification push."""
        notification = PushNotification(
            tenant_id=self.tenant_id,
            user_id=data.user_id,
            title=data.title,
            body=data.body,
            image_url=data.image_url,
            notification_type=data.notification_type,
            category=data.category,
            priority=data.priority,
            data=data.data,
            action_url=data.action_url,
            scheduled_at=data.scheduled_at,
            status="pending" if data.scheduled_at else "sent",
            sent_at=None if data.scheduled_at else datetime.utcnow()
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        # TODO: Intégrer avec FCM/APNS pour envoi réel
        return notification

    def send_bulk_notifications(self, data: NotificationBulk) -> list[PushNotification]:
        """Envoyer notifications en masse."""
        notifications = []
        for user_id in data.user_ids:
            notif = PushNotification(
                tenant_id=self.tenant_id,
                user_id=user_id,
                title=data.title,
                body=data.body,
                notification_type=data.notification_type,
                data=data.data,
                status="sent",
                sent_at=datetime.utcnow()
            )
            self.db.add(notif)
            notifications.append(notif)

        self.db.commit()
        return notifications

    def get_user_notifications(
        self, user_id: int, unread_only: bool = False,
        skip: int = 0, limit: int = 50
    ) -> list[PushNotification]:
        """Récupérer notifications d'un utilisateur."""
        query = self.db.query(PushNotification).filter(
            PushNotification.tenant_id == self.tenant_id,
            PushNotification.user_id == user_id
        )

        if unread_only:
            query = query.filter(PushNotification.read_at is None)

        return query.order_by(
            PushNotification.created_at.desc()
        ).offset(skip).limit(limit).all()

    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """Marquer notification comme lue."""
        notif = self.db.query(PushNotification).filter(
            PushNotification.tenant_id == self.tenant_id,
            PushNotification.id == notification_id,
            PushNotification.user_id == user_id
        ).first()

        if not notif:
            return False

        notif.read_at = datetime.utcnow()
        notif.status = "read"
        self.db.commit()
        return True

    def mark_all_notifications_read(self, user_id: int) -> int:
        """Marquer toutes les notifications comme lues."""
        result = self.db.query(PushNotification).filter(
            PushNotification.tenant_id == self.tenant_id,
            PushNotification.user_id == user_id,
            PushNotification.read_at is None
        ).update({
            "read_at": datetime.utcnow(),
            "status": "read"
        })
        self.db.commit()
        return result

    def get_unread_count(self, user_id: int) -> int:
        """Compter notifications non lues."""
        return self.db.query(PushNotification).filter(
            PushNotification.tenant_id == self.tenant_id,
            PushNotification.user_id == user_id,
            PushNotification.read_at is None
        ).count()

    # ========================================================================
    # SYNC
    # ========================================================================

    def get_sync_data(
        self, user_id: int, entity_type: str,
        since_version: int = 0, limit: int = 100
    ) -> tuple[list[dict], int, bool]:
        """Récupérer données à synchroniser."""
        # Récupérer checkpoint
        self.db.query(SyncCheckpoint).filter(
            SyncCheckpoint.tenant_id == self.tenant_id,
            SyncCheckpoint.user_id == user_id,
            SyncCheckpoint.entity_type == entity_type
        ).first()

        # TODO: Implémenter récupération données par entity_type
        # Pour l'instant, retourner données vides
        items = []
        current_version = since_version
        has_more = False

        return items, current_version, has_more

    def process_sync_batch(
        self, user_id: int, batch: SyncBatch
    ) -> tuple[int, int, list[SyncConflict]]:
        """Traiter un batch de synchronisation."""
        success_count = 0
        error_count = 0
        conflicts = []

        for item in batch.items:
            try:
                # Ajouter à la queue
                queue_item = SyncQueue(
                    tenant_id=self.tenant_id,
                    user_id=user_id,
                    entity_type=item.entity_type,
                    entity_id=item.entity_id,
                    operation=item.operation,
                    data=item.data,
                    local_version=item.local_version,
                    status="pending"
                )
                self.db.add(queue_item)
                success_count += 1
            except Exception as e:
                logger.warning(
                    "[MOBILE_SYNC] Échec ajout item à la queue de sync",
                    extra={
                        "entity_type": item.entity_type,
                        "entity_id": str(item.entity_id),
                        "error": str(e)[:300],
                        "consequence": "sync_item_skipped"
                    }
                )
                error_count += 1

        self.db.commit()
        return success_count, error_count, conflicts

    def update_sync_checkpoint(
        self, user_id: int, entity_type: str, version: int, count: int
    ) -> None:
        """Mettre à jour le checkpoint de sync."""
        checkpoint = self.db.query(SyncCheckpoint).filter(
            SyncCheckpoint.tenant_id == self.tenant_id,
            SyncCheckpoint.user_id == user_id,
            SyncCheckpoint.entity_type == entity_type
        ).first()

        if checkpoint:
            checkpoint.last_sync_at = datetime.utcnow()
            checkpoint.last_sync_version = version
            checkpoint.total_synced = (checkpoint.total_synced or 0) + count
            checkpoint.last_sync_count = count
        else:
            checkpoint = SyncCheckpoint(
                tenant_id=self.tenant_id,
                user_id=user_id,
                entity_type=entity_type,
                last_sync_at=datetime.utcnow(),
                last_sync_version=version,
                total_synced=count,
                last_sync_count=count
            )
            self.db.add(checkpoint)

        self.db.commit()

    # ========================================================================
    # PREFERENCES
    # ========================================================================

    def get_preferences(self, user_id: int) -> MobilePreferences:
        """Récupérer préférences utilisateur."""
        prefs = self.db.query(MobilePreferences).filter(
            MobilePreferences.tenant_id == self.tenant_id,
            MobilePreferences.user_id == user_id
        ).first()

        if not prefs:
            # Créer préférences par défaut
            prefs = MobilePreferences(
                tenant_id=self.tenant_id,
                user_id=user_id
            )
            self.db.add(prefs)
            self.db.commit()
            self.db.refresh(prefs)

        return prefs

    def update_preferences(self, user_id: int, data: PreferencesUpdate) -> MobilePreferences:
        """Mettre à jour préférences."""
        prefs = self.get_preferences(user_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(prefs, field, value)

        prefs.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(prefs)
        return prefs

    # ========================================================================
    # ACTIVITY LOGS
    # ========================================================================

    def log_activity(
        self, user_id: int, activity: ActivityLog,
        device_id: int | None = None, session_id: int | None = None,
        ip: str | None = None
    ) -> MobileActivityLog:
        """Enregistrer une activité."""
        log = MobileActivityLog(
            tenant_id=self.tenant_id,
            user_id=user_id,
            device_id=device_id,
            session_id=session_id,
            action=activity.action,
            resource_type=activity.resource_type,
            resource_id=activity.resource_id,
            screen=activity.screen,
            duration_ms=activity.duration_ms,
            details=activity.details,
            latitude=activity.latitude,
            longitude=activity.longitude,
            connection_type=activity.connection_type,
            ip_address=ip
        )
        self.db.add(log)
        self.db.commit()
        return log

    def log_activity_batch(
        self, user_id: int, batch: ActivityBatch,
        device_id: int | None = None, session_id: int | None = None
    ) -> int:
        """Enregistrer batch d'activités."""
        count = 0
        for activity in batch.activities:
            log = MobileActivityLog(
                tenant_id=self.tenant_id,
                user_id=user_id,
                device_id=device_id,
                session_id=session_id,
                action=activity.action,
                resource_type=activity.resource_type,
                resource_id=activity.resource_id,
                screen=activity.screen,
                duration_ms=activity.duration_ms,
                details=activity.details,
                latitude=activity.latitude,
                longitude=activity.longitude,
                connection_type=activity.connection_type
            )
            self.db.add(log)
            count += 1

        self.db.commit()
        return count

    # ========================================================================
    # APP CONFIG
    # ========================================================================

    def get_app_config(self) -> MobileAppConfig | None:
        """Récupérer configuration app."""
        return self.db.query(MobileAppConfig).filter(
            MobileAppConfig.tenant_id == self.tenant_id,
            MobileAppConfig.is_active
        ).first()

    def check_app_version(self, platform: str, version: str) -> dict[str, Any]:
        """Vérifier version app."""
        config = self.get_app_config()
        if not config:
            return {
                "update_required": False,
                "force_update": False,
                "maintenance_mode": False
            }

        min_version = config.min_ios_version if platform == "ios" else config.min_android_version

        # Comparer versions (simple)
        update_required = False
        if min_version and version:
            update_required = version < min_version

        return {
            "update_required": update_required,
            "force_update": config.force_update and update_required,
            "current_version": config.current_version,
            "update_message": config.update_message if update_required else None,
            "maintenance_mode": config.maintenance_mode,
            "maintenance_message": config.maintenance_message if config.maintenance_mode else None,
            "store_url": config.store_url_ios if platform == "ios" else config.store_url_android
        }

    # ========================================================================
    # CRASH REPORTS
    # ========================================================================

    def report_crash(
        self, user_id: int | None, device_id: int | None, data: CrashReport
    ) -> MobileCrashReport:
        """Enregistrer un crash."""
        crash = MobileCrashReport(
            tenant_id=self.tenant_id,
            user_id=user_id,
            device_id=device_id,
            crash_id=str(uuid.uuid4()),
            error_type=data.error_type,
            error_message=data.error_message,
            stack_trace=data.stack_trace,
            app_version=data.app_version,
            os_version=data.os_version,
            platform=data.platform,
            device_model=data.device_model,
            screen=data.screen,
            last_action=data.last_action,
            memory_usage=data.memory_usage,
            battery_level=data.battery_level,
            console_logs=data.console_logs,
            breadcrumbs=data.breadcrumbs
        )
        self.db.add(crash)
        self.db.commit()
        self.db.refresh(crash)
        return crash

    def list_crashes(
        self, app_version: str | None = None,
        error_type: str | None = None,
        resolved: bool | None = None,
        skip: int = 0, limit: int = 50
    ) -> list[MobileCrashReport]:
        """Lister les crashes."""
        query = self.db.query(MobileCrashReport).filter(
            MobileCrashReport.tenant_id == self.tenant_id
        )

        if app_version:
            query = query.filter(MobileCrashReport.app_version == app_version)
        if error_type:
            query = query.filter(MobileCrashReport.error_type == error_type)
        if resolved is not None:
            query = query.filter(MobileCrashReport.is_resolved == resolved)

        return query.order_by(
            MobileCrashReport.created_at.desc()
        ).offset(skip).limit(limit).all()

    # ========================================================================
    # STATS & DASHBOARD
    # ========================================================================

    def get_mobile_stats(self) -> dict[str, Any]:
        """Statistiques mobile."""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Appareils
        total_devices = self.db.query(MobileDevice).filter(
            MobileDevice.tenant_id == self.tenant_id
        ).count()

        active_devices = self.db.query(MobileDevice).filter(
            MobileDevice.tenant_id == self.tenant_id,
            MobileDevice.is_active,
            MobileDevice.last_active >= now - timedelta(days=30)
        ).count()

        # Sessions
        total_sessions = self.db.query(MobileSession).filter(
            MobileSession.tenant_id == self.tenant_id
        ).count()

        active_sessions = self.db.query(MobileSession).filter(
            MobileSession.tenant_id == self.tenant_id,
            MobileSession.is_active,
            MobileSession.expires_at > now
        ).count()

        # Notifications
        notifications_sent = self.db.query(PushNotification).filter(
            PushNotification.tenant_id == self.tenant_id,
            PushNotification.sent_at >= today_start
        ).count()

        notifications_read = self.db.query(PushNotification).filter(
            PushNotification.tenant_id == self.tenant_id,
            PushNotification.sent_at >= today_start,
            PushNotification.read_at is not None
        ).count()

        read_rate = (notifications_read / notifications_sent * 100) if notifications_sent > 0 else 0

        # Sync pending
        sync_pending = self.db.query(SyncQueue).filter(
            SyncQueue.tenant_id == self.tenant_id,
            SyncQueue.status == "pending"
        ).count()

        # Crashes aujourd'hui
        crashes_today = self.db.query(MobileCrashReport).filter(
            MobileCrashReport.tenant_id == self.tenant_id,
            MobileCrashReport.created_at >= today_start
        ).count()

        # Par plateforme
        devices_by_platform = {}
        platform_counts = self.db.query(
            MobileDevice.platform,
            func.count(MobileDevice.id)
        ).filter(
            MobileDevice.tenant_id == self.tenant_id,
            MobileDevice.is_active
        ).group_by(MobileDevice.platform).all()

        for platform, count in platform_counts:
            devices_by_platform[platform] = count

        # Par version
        devices_by_version = {}
        version_counts = self.db.query(
            MobileDevice.app_version,
            func.count(MobileDevice.id)
        ).filter(
            MobileDevice.tenant_id == self.tenant_id,
            MobileDevice.is_active,
            MobileDevice.app_version is not None
        ).group_by(MobileDevice.app_version).all()

        for version, count in version_counts:
            devices_by_version[version] = count

        return {
            "total_devices": total_devices,
            "active_devices": active_devices,
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "notifications_sent": notifications_sent,
            "notifications_read_rate": round(read_rate, 1),
            "sync_pending": sync_pending,
            "crashes_today": crashes_today,
            "devices_by_platform": devices_by_platform,
            "devices_by_version": devices_by_version
        }
