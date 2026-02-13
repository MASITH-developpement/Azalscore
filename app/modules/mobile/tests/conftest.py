"""Configuration pytest et fixtures pour les tests Mobile.

Hérite des fixtures globales de app/conftest.py.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4


# ============================================================================
# FIXTURES HÉRITÉES DU CONFTEST GLOBAL
# ============================================================================
# Les fixtures suivantes sont héritées de app/conftest.py:
# - tenant_id, user_id, user_uuid
# - db_session, test_db_session
# - test_client (avec headers auto-injectés)
# - mock_auth_global (autouse=True)
# - saas_context


@pytest.fixture
def client(test_client):
    """
    Alias pour test_client (compatibilité avec anciens tests).

    Le test_client du conftest global ajoute déjà les headers requis.
    """
    return test_client


@pytest.fixture
def auth_headers(tenant_id):
    """Headers d'authentification avec tenant ID."""
    return {
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": tenant_id
    }


@pytest.fixture
def mock_mobile_service(monkeypatch):
    """Mock du service Mobile."""

    class MockMobileService:
        def __init__(self, db, tenant_id, user_id=None):
            self.db = db
            self.tenant_id = tenant_id
            self.user_id = user_id

        # Devices
        def register_device(self, user_id, data):
            class MockDevice:
                id = 1
                tenant_id = self.tenant_id
                user_id = user_id
                device_id = data.device_id
                device_name = data.device_name
                platform = data.platform
                os_version = data.os_version
                app_version = data.app_version
                model = data.model
                push_token = data.push_token
                push_provider = "fcm" if data.platform == "android" else "apns"
                is_active = True
                last_active = datetime.utcnow()
                created_at = datetime.utcnow()
                updated_at = datetime.utcnow()
            return MockDevice()

        def get_device(self, device_id):
            if device_id == 999:
                return None
            class MockDevice:
                id = device_id
                tenant_id = self.tenant_id
                device_name = "Test Device"
                platform = "ios"
            return MockDevice()

        def list_user_devices(self, user_id):
            class MockDevice:
                id = 1
                tenant_id = self.tenant_id
                user_id = user_id
                device_name = "iPhone 14"
                platform = "ios"
            return [MockDevice()]

        def update_device(self, device_id, data):
            if device_id == 999:
                return None
            class MockDevice:
                id = device_id
                tenant_id = self.tenant_id
                device_name = data.device_name or "Updated Device"
                push_token = data.push_token
            return MockDevice()

        def deactivate_device(self, device_id):
            return device_id != 999

        # Sessions
        def create_session(self, user_id, device_uuid, ip_address):
            class MockSession:
                id = 1
                tenant_id = self.tenant_id
                user_id = user_id
                device_id = 1
                access_token = "access_token_123"
                refresh_token = "refresh_token_123"
                expires_at = datetime.utcnow() + timedelta(hours=24)
                is_active = True
                created_at = datetime.utcnow()
            return MockSession()

        def refresh_session(self, refresh_token):
            if refresh_token == "invalid":
                return None
            class MockSession:
                id = 1
                access_token = "new_access_token_123"
                refresh_token = "new_refresh_token_123"
                expires_at = datetime.utcnow() + timedelta(hours=24)
            return MockSession()

        def revoke_session(self, session_id, reason):
            return session_id != 999

        def revoke_user_sessions(self, user_id):
            return 3  # Number of sessions revoked

        # Notifications
        def send_notification(self, data):
            class MockNotification:
                id = 1
                tenant_id = self.tenant_id
                user_id = data.user_id
                title = data.title
                body = data.body
                data_payload = data.data
                status = "sent"
                sent_at = datetime.utcnow()
                created_at = datetime.utcnow()
            return MockNotification()

        def send_bulk_notifications(self, data):
            notifications = []
            for user_id in data.user_ids:
                class MockNotification:
                    id = user_id
                    tenant_id = self.tenant_id
                    user_id = user_id
                    title = data.title
                    body = data.body
                notifications.append(MockNotification())
            return notifications

        def get_user_notifications(self, user_id, skip, limit):
            class MockNotification:
                id = 1
                tenant_id = self.tenant_id
                user_id = user_id
                title = "Test Notification"
                body = "Test body"
                is_read = False
                created_at = datetime.utcnow()
            return [MockNotification()]

        def get_unread_count(self, user_id):
            return 5

        def mark_notification_read(self, notification_id, user_id):
            return notification_id != 999

        def mark_all_notifications_read(self, user_id):
            return 5

        # Sync
        def get_sync_data(self, entity_type, user_id, last_sync):
            return {
                "records": [{"id": "1", "name": "Record 1"}],
                "checkpoint": "2024-01-23T10:00:00Z",
                "has_more": False
            }

        def process_sync_batch(self, user_id, data):
            return {
                "processed": len(data.records),
                "conflicts": [],
                "errors": []
            }

        # Preferences
        def get_preferences(self, user_id):
            class MockPreferences:
                id = 1
                tenant_id = self.tenant_id
                user_id = user_id
                language = "fr"
                theme = "light"
                notifications_enabled = True
                sync_enabled = True
                created_at = datetime.utcnow()
                updated_at = datetime.utcnow()
            return MockPreferences()

        def update_preferences(self, user_id, data):
            class MockPreferences:
                id = 1
                tenant_id = self.tenant_id
                user_id = user_id
                language = data.language or "fr"
                theme = data.theme or "light"
                notifications_enabled = data.notifications_enabled
                updated_at = datetime.utcnow()
            return MockPreferences()

        # Activity
        def log_activity(self, user_id, data):
            class MockActivity:
                id = 1
                tenant_id = self.tenant_id
                user_id = user_id
                event_type = data.event_type
                created_at = datetime.utcnow()
            return MockActivity()

        def log_activity_batch(self, user_id, data):
            return len(data.activities)

        # App Config
        def get_app_config(self):
            class MockConfig:
                id = 1
                tenant_id = self.tenant_id
                min_version_ios = "1.0.0"
                min_version_android = "1.0.0"
                latest_version_ios = "1.5.0"
                latest_version_android = "1.5.0"
                force_update = False
                maintenance_mode = False
                api_base_url = "https://api.azalscore.com"
                features_enabled = {"offline_mode": True}
            return MockConfig()

        def check_app_version(self, platform, version):
            return {
                "is_supported": True,
                "is_latest": version == "1.5.0",
                "force_update": False,
                "latest_version": "1.5.0"
            }

        # Crashes
        def report_crash(self, user_id, data):
            class MockCrash:
                id = 1
                tenant_id = self.tenant_id
                user_id = user_id
                error_message = data.error_message
                created_at = datetime.utcnow()
            return MockCrash()

        def list_crashes(self, skip, limit):
            return [
                {
                    "id": 1,
                    "error_message": "Test crash",
                    "created_at": datetime.utcnow()
                }
            ]

        # Stats
        def get_stats(self):
            return {
                "total_devices": 100,
                "active_devices": 80,
                "total_sessions": 500,
                "active_sessions": 50,
                "total_notifications": 1000,
                "notifications_sent_today": 50,
                "crash_reports_today": 2
            }

    from app.modules.mobile import router_v2

    def mock_get_service(db, tenant_id, user_id):
        return MockMobileService(db, tenant_id, user_id)

    monkeypatch.setattr(router_v2, "get_mobile_service", mock_get_service)
    return MockMobileService(None, "test-tenant", "1")


@pytest.fixture
def sample_device_data():
    return {
        "device_id": "device-uuid-123",
        "device_name": "iPhone 14 Pro",
        "platform": "ios",
        "os_version": "17.0",
        "app_version": "1.5.0",
        "model": "iPhone 14 Pro",
        "push_token": "fcm_token_xyz"
    }


@pytest.fixture
def sample_notification_data():
    return {
        "user_id": 1,
        "title": "Test Notification",
        "body": "This is a test notification",
        "data": {"action": "open_app"}
    }
