"""
Tests Module 18 - Mobile App Backend
=====================================
Tests unitaires pour le backend mobile.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch

from app.modules.mobile.models import (
    MobileDevice, MobileSession, PushNotification, SyncQueue,
    SyncCheckpoint, MobilePreferences, MobileActivityLog,
    MobileAppConfig, MobileCrashReport,
    DevicePlatform, NotificationStatus, SyncStatus
)
from app.modules.mobile.schemas import (
    DeviceRegister, DeviceUpdate,
    NotificationCreate, NotificationBulk,
    SyncRequest, SyncItem, SyncBatch,
    PreferencesUpdate, ActivityLog, ActivityBatch, CrashReport
)
from app.modules.mobile.service import MobileService


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock de la session DB."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    return db


@pytest.fixture
def mobile_service(mock_db):
    """Service Mobile pour tests."""
    return MobileService(mock_db, "test-tenant")


@pytest.fixture
def sample_device():
    """Appareil exemple."""
    return MobileDevice(
        id=1,
        tenant_id="test-tenant",
        user_id=1,
        device_id="device-uuid-123",
        device_name="iPhone Test",
        platform="ios",
        os_version="17.0",
        app_version="1.0.0",
        model="iPhone 15",
        push_token="apns-token-123",
        push_enabled=True,
        is_active=True,
        last_active=datetime.utcnow()
    )


@pytest.fixture
def sample_session():
    """Session exemple."""
    return MobileSession(
        id=1,
        tenant_id="test-tenant",
        user_id=1,
        device_id=1,
        session_token="token-abc123",
        refresh_token="refresh-xyz789",
        expires_at=datetime.utcnow() + timedelta(hours=24),
        refresh_expires_at=datetime.utcnow() + timedelta(days=30),
        is_active=True,
        revoked=False
    )


# ============================================================================
# MODEL TESTS
# ============================================================================

class TestMobileModels:
    """Tests des modèles Mobile."""

    def test_device_model_creation(self):
        """Test création modèle appareil."""
        device = MobileDevice(
            tenant_id="test",
            user_id=1,
            device_id="uuid-123",
            platform="android",
            is_active=True
        )
        assert device.device_id == "uuid-123"
        assert device.platform == "android"

    def test_session_model_creation(self):
        """Test création modèle session."""
        session = MobileSession(
            tenant_id="test",
            user_id=1,
            device_id=1,
            session_token="token123",
            expires_at=datetime.utcnow() + timedelta(hours=24),
            is_active=True
        )
        assert session.session_token == "token123"
        assert session.is_active is True

    def test_notification_model_creation(self):
        """Test création modèle notification."""
        notif = PushNotification(
            tenant_id="test",
            user_id=1,
            title="Test",
            body="Test notification",
            notification_type="info",
            status="pending"
        )
        assert notif.title == "Test"
        assert notif.status == "pending"

    def test_preferences_model_creation(self):
        """Test création modèle préférences."""
        prefs = MobilePreferences(
            tenant_id="test",
            user_id=1,
            push_enabled=True,
            theme="dark",
            language="fr"
        )
        assert prefs.push_enabled is True
        assert prefs.theme == "dark"


# ============================================================================
# SCHEMA TESTS
# ============================================================================

class TestMobileSchemas:
    """Tests des schémas Mobile."""

    def test_device_register_schema(self):
        """Test schéma enregistrement appareil."""
        data = DeviceRegister(
            device_id="uuid-123",
            platform="ios",
            os_version="17.0",
            app_version="1.0.0"
        )
        assert data.device_id == "uuid-123"
        assert data.platform == "ios"

    def test_notification_create_schema(self):
        """Test schéma création notification."""
        data = NotificationCreate(
            user_id=1,
            title="Test",
            body="Notification body",
            notification_type="alert",
            priority="high"
        )
        assert data.title == "Test"
        assert data.priority == "high"

    def test_sync_item_schema(self):
        """Test schéma item sync."""
        data = SyncItem(
            entity_type="order",
            entity_id="123",
            operation="create",
            data={"id": 123, "status": "new"}
        )
        assert data.entity_type == "order"
        assert data.operation == "create"

    def test_preferences_update_schema(self):
        """Test schéma mise à jour préférences."""
        data = PreferencesUpdate(
            push_enabled=False,
            theme="light",
            language="en"
        )
        assert data.push_enabled is False
        assert data.theme == "light"


# ============================================================================
# DEVICE SERVICE TESTS
# ============================================================================

class TestDeviceService:
    """Tests service appareils."""

    def test_register_device_new(self, mobile_service, mock_db):
        """Test enregistrement nouvel appareil."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = DeviceRegister(
            device_id="new-uuid-123",
            platform="android",
            os_version="14.0",
            app_version="1.0.0",
            model="Galaxy S24"
        )

        device = mobile_service.register_device(1, data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    def test_register_device_existing(self, mobile_service, mock_db, sample_device):
        """Test enregistrement appareil existant."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_device

        data = DeviceRegister(
            device_id="device-uuid-123",
            platform="ios",
            app_version="2.0.0"
        )

        device = mobile_service.register_device(1, data)

        assert device.app_version == "2.0.0"
        mock_db.commit.assert_called()

    def test_get_device(self, mobile_service, mock_db, sample_device):
        """Test récupération appareil."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_device

        device = mobile_service.get_device(1)

        assert device.id == 1
        assert device.platform == "ios"

    def test_list_user_devices(self, mobile_service, mock_db, sample_device):
        """Test liste appareils utilisateur."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [sample_device]

        devices = mobile_service.list_user_devices(1)

        assert len(devices) == 1

    def test_deactivate_device(self, mobile_service, mock_db, sample_device):
        """Test désactivation appareil."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_device

        success = mobile_service.deactivate_device(1)

        assert success is True
        assert sample_device.is_active is False


# ============================================================================
# SESSION SERVICE TESTS
# ============================================================================

class TestSessionService:
    """Tests service sessions."""

    def test_create_session(self, mobile_service, mock_db, sample_device):
        """Test création session."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_device

        session = mobile_service.create_session(1, 1)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
        assert session.session_token is not None
        assert session.refresh_token is not None

    def test_create_session_device_not_found(self, mobile_service, mock_db):
        """Test création session appareil introuvable."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Appareil introuvable"):
            mobile_service.create_session(1, 999)

    def test_refresh_session(self, mobile_service, mock_db, sample_session):
        """Test renouvellement session."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_session

        new_session = mobile_service.refresh_session("refresh-xyz789")

        assert new_session is not None
        assert sample_session.revoked is True

    def test_refresh_session_invalid_token(self, mobile_service, mock_db):
        """Test refresh token invalide."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = mobile_service.refresh_session("invalid-token")

        assert result is None

    def test_revoke_session(self, mobile_service, mock_db, sample_session):
        """Test révocation session."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_session

        success = mobile_service.revoke_session(1)

        assert success is True
        assert sample_session.revoked is True


# ============================================================================
# NOTIFICATION SERVICE TESTS
# ============================================================================

class TestNotificationService:
    """Tests service notifications."""

    def test_send_notification(self, mobile_service, mock_db):
        """Test envoi notification."""
        data = NotificationCreate(
            user_id=1,
            title="Test Notification",
            body="This is a test",
            notification_type="info"
        )

        notification = mobile_service.send_notification(data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    def test_send_bulk_notifications(self, mobile_service, mock_db):
        """Test envoi notifications en masse."""
        data = NotificationBulk(
            user_ids=[1, 2, 3],
            title="Bulk Test",
            body="Bulk notification"
        )

        notifications = mobile_service.send_bulk_notifications(data)

        assert len(notifications) == 3

    def test_get_user_notifications(self, mobile_service, mock_db):
        """Test récupération notifications utilisateur."""
        notif = PushNotification(
            id=1,
            tenant_id="test",
            user_id=1,
            title="Test",
            status="sent"
        )
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [notif]

        notifications = mobile_service.get_user_notifications(1)

        assert len(notifications) == 1

    def test_mark_notification_read(self, mobile_service, mock_db):
        """Test marquer notification comme lue."""
        notif = PushNotification(
            id=1,
            tenant_id="test",
            user_id=1,
            title="Test",
            status="sent"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = notif

        success = mobile_service.mark_notification_read(1, 1)

        assert success is True
        assert notif.status == "read"

    def test_get_unread_count(self, mobile_service, mock_db):
        """Test comptage notifications non lues."""
        mock_db.query.return_value.filter.return_value.count.return_value = 5

        count = mobile_service.get_unread_count(1)

        assert count == 5


# ============================================================================
# SYNC SERVICE TESTS
# ============================================================================

class TestSyncService:
    """Tests service synchronisation."""

    def test_process_sync_batch(self, mobile_service, mock_db):
        """Test traitement batch sync."""
        batch = SyncBatch(
            items=[
                SyncItem(entity_type="order", operation="create", data={"id": 1}),
                SyncItem(entity_type="order", operation="update", data={"id": 2})
            ]
        )

        success, errors, conflicts = mobile_service.process_sync_batch(1, batch)

        assert success == 2
        assert errors == 0

    def test_update_sync_checkpoint(self, mobile_service, mock_db):
        """Test mise à jour checkpoint."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mobile_service.update_sync_checkpoint(1, "order", 100, 50)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()


# ============================================================================
# PREFERENCES SERVICE TESTS
# ============================================================================

class TestPreferencesService:
    """Tests service préférences."""

    def test_get_preferences_new(self, mobile_service, mock_db):
        """Test récupération préférences nouvelles."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        prefs = mobile_service.get_preferences(1)

        mock_db.add.assert_called_once()

    def test_get_preferences_existing(self, mobile_service, mock_db):
        """Test récupération préférences existantes."""
        existing = MobilePreferences(
            id=1,
            tenant_id="test",
            user_id=1,
            theme="dark"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing

        prefs = mobile_service.get_preferences(1)

        assert prefs.theme == "dark"

    def test_update_preferences(self, mobile_service, mock_db):
        """Test mise à jour préférences."""
        existing = MobilePreferences(
            id=1,
            tenant_id="test",
            user_id=1,
            theme="light"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing

        data = PreferencesUpdate(theme="dark", language="en")
        prefs = mobile_service.update_preferences(1, data)

        assert prefs.theme == "dark"
        assert prefs.language == "en"


# ============================================================================
# CRASH REPORTS TESTS
# ============================================================================

class TestCrashReportService:
    """Tests service rapports crash."""

    def test_report_crash(self, mobile_service, mock_db):
        """Test enregistrement crash."""
        data = CrashReport(
            error_type="NullPointerException",
            error_message="Null reference",
            app_version="1.0.0",
            os_version="14.0",
            platform="android"
        )

        crash = mobile_service.report_crash(1, 1, data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    def test_list_crashes(self, mobile_service, mock_db):
        """Test liste crashes."""
        crash = MobileCrashReport(
            id=1,
            tenant_id="test",
            crash_id="crash-123",
            error_type="Error",
            error_message="Test error",
            app_version="1.0.0"
        )
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [crash]

        crashes = mobile_service.list_crashes()

        assert len(crashes) == 1


# ============================================================================
# STATS TESTS
# ============================================================================

class TestMobileStats:
    """Tests statistiques mobile."""

    def test_get_mobile_stats(self, mobile_service, mock_db):
        """Test récupération statistiques."""
        mock_db.query.return_value.filter.return_value.count.return_value = 10
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        stats = mobile_service.get_mobile_stats()

        assert "total_devices" in stats
        assert "active_devices" in stats
        assert "crashes_today" in stats


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestMobileEnums:
    """Tests des énumérations Mobile."""

    def test_device_platform_values(self):
        """Test valeurs plateforme."""
        assert DevicePlatform.IOS.value == "ios"
        assert DevicePlatform.ANDROID.value == "android"
        assert DevicePlatform.WEB.value == "web"

    def test_notification_status_values(self):
        """Test valeurs statut notification."""
        assert NotificationStatus.PENDING.value == "pending"
        assert NotificationStatus.SENT.value == "sent"
        assert NotificationStatus.DELIVERED.value == "delivered"
        assert NotificationStatus.READ.value == "read"

    def test_sync_status_values(self):
        """Test valeurs statut sync."""
        assert SyncStatus.PENDING.value == "pending"
        assert SyncStatus.COMPLETED.value == "completed"
        assert SyncStatus.CONFLICT.value == "conflict"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestMobileIntegration:
    """Tests d'intégration Mobile."""

    def test_full_device_registration_flow(self, mobile_service, mock_db, sample_device):
        """Test flux complet enregistrement appareil."""
        # 1. Enregistrer appareil
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = DeviceRegister(
            device_id="new-device-uuid",
            platform="ios",
            app_version="1.0.0"
        )
        device = mobile_service.register_device(1, data)
        mock_db.add.assert_called()

        # 2. Créer session
        mock_db.reset_mock()
        mock_db.query.return_value.filter.return_value.first.return_value = sample_device

        session = mobile_service.create_session(1, 1)
        assert session.session_token is not None

    def test_notification_lifecycle(self, mobile_service, mock_db):
        """Test cycle de vie notification."""
        # 1. Créer notification
        data = NotificationCreate(
            user_id=1,
            title="Test",
            body="Body"
        )
        notif = mobile_service.send_notification(data)
        mock_db.add.assert_called()

        # 2. Marquer comme lue
        mock_db.reset_mock()
        existing_notif = PushNotification(
            id=1,
            tenant_id="test",
            user_id=1,
            title="Test",
            status="sent"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing_notif

        success = mobile_service.mark_notification_read(1, 1)
        assert success is True
        assert existing_notif.status == "read"
