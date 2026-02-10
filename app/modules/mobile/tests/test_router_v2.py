"""Tests pour le router v2 du module Mobile - CORE SaaS v2."""

import pytest


BASE_URL = "/v2/mobile"


# ============================================================================
# TESTS DEVICES
# ============================================================================

def test_register_device(test_client, mock_mobile_service, sample_device_data):
    response = test_client.post(f"{BASE_URL}/devices/register", json=sample_device_data)
    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == sample_device_data["device_id"]
    assert data["platform"] == sample_device_data["platform"]


def test_list_user_devices(test_client):
    response = test_client.get(f"{BASE_URL}/devices")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_device_success(test_client):
    response = test_client.get(f"{BASE_URL}/devices/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1


def test_get_device_not_found(test_client):
    response = test_client.get(f"{BASE_URL}/devices/999")
    assert response.status_code == 404


def test_update_device_success(test_client):
    update_data = {
        "device_name": "iPhone 15 Pro",
        "push_token": "new_token_xyz"
    }
    response = test_client.put(f"{BASE_URL}/devices/1", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert "device_name" in data


def test_update_device_not_found(test_client):
    update_data = {"device_name": "Test"}
    response = test_client.put(f"{BASE_URL}/devices/999", json=update_data)
    assert response.status_code == 404


def test_deactivate_device_success(test_client):
    response = test_client.delete(f"{BASE_URL}/devices/1")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_deactivate_device_not_found(test_client):
    response = test_client.delete(f"{BASE_URL}/devices/999")
    assert response.status_code == 404


# ============================================================================
# TESTS SESSIONS
# ============================================================================

def test_create_session_success(test_client):
    response = test_client.post(
        f"{BASE_URL}/sessions",
        params={"device_uuid": "device-uuid-123", "ip_address": "192.168.1.1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_session_success(test_client):
    response = test_client.post(
        f"{BASE_URL}/sessions/refresh",
        params={"refresh_token": "refresh_token_123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_refresh_session_invalid_token(test_client):
    response = test_client.post(
        f"{BASE_URL}/sessions/refresh",
        params={"refresh_token": "invalid"}
    )
    assert response.status_code == 401


def test_revoke_session_success(test_client):
    response = test_client.delete(f"{BASE_URL}/sessions/1")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_revoke_session_not_found(test_client):
    response = test_client.delete(f"{BASE_URL}/sessions/999")
    assert response.status_code == 404


def test_revoke_all_sessions(test_client):
    response = test_client.delete(f"{BASE_URL}/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "3" in data["message"]


# ============================================================================
# TESTS NOTIFICATIONS
# ============================================================================

def test_send_notification_success(test_client, mock_mobile_service, sample_notification_data):
    response = test_client.post(f"{BASE_URL}/notifications", json=sample_notification_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == sample_notification_data["title"]
    assert data["status"] == "sent"


def test_send_bulk_notifications(test_client):
    bulk_data = {
        "user_ids": [1, 2, 3],
        "title": "Bulk Notification",
        "body": "This is a bulk notification"
    }
    response = test_client.post(f"{BASE_URL}/notifications/bulk", json=bulk_data)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3


def test_get_user_notifications(test_client):
    response = test_client.get(f"{BASE_URL}/notifications")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_unread_count(test_client):
    response = test_client.get(f"{BASE_URL}/notifications/unread-count")
    assert response.status_code == 200
    data = response.json()
    assert data["unread_count"] == 5


def test_mark_notification_read_success(test_client):
    response = test_client.put(f"{BASE_URL}/notifications/1/read")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_mark_notification_read_not_found(test_client):
    response = test_client.put(f"{BASE_URL}/notifications/999/read")
    assert response.status_code == 404


def test_mark_all_notifications_read(test_client):
    response = test_client.put(f"{BASE_URL}/notifications/read-all")
    assert response.status_code == 200
    data = response.json()
    assert "5" in data["message"]


# ============================================================================
# TESTS SYNCHRONISATION
# ============================================================================

def test_sync_pull(test_client):
    response = test_client.post(
        f"{BASE_URL}/sync/pull",
        params={
            "entity_type": "invoices",
            "last_sync": "2024-01-01T00:00:00Z"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "records" in data
    assert "checkpoint" in data
    assert "has_more" in data


def test_sync_push(test_client):
    sync_data = {
        "entity_type": "invoices",
        "records": [
            {"id": "1", "action": "update", "data": {"amount": 100}}
        ]
    }
    response = test_client.post(f"{BASE_URL}/sync/push", json=sync_data)
    assert response.status_code == 200
    data = response.json()
    assert "processed" in data


# ============================================================================
# TESTS PRÉFÉRENCES
# ============================================================================

def test_get_preferences(test_client):
    response = test_client.get(f"{BASE_URL}/preferences")
    assert response.status_code == 200
    data = response.json()
    assert "language" in data
    assert "theme" in data


def test_update_preferences(test_client):
    prefs_data = {
        "language": "en",
        "theme": "dark",
        "notifications_enabled": True
    }
    response = test_client.put(f"{BASE_URL}/preferences", json=prefs_data)
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "en"
    assert data["theme"] == "dark"


# ============================================================================
# TESTS ACTIVITY
# ============================================================================

def test_log_activity(test_client):
    activity_data = {
        "event_type": "screen_view",
        "screen_name": "Dashboard",
        "metadata": {"duration": 30}
    }
    response = test_client.post(f"{BASE_URL}/activity", json=activity_data)
    assert response.status_code == 200
    data = response.json()
    assert "activity_id" in data


def test_log_activity_batch(test_client):
    batch_data = {
        "activities": [
            {"event_type": "click", "metadata": {}},
            {"event_type": "scroll", "metadata": {}}
        ]
    }
    response = test_client.post(f"{BASE_URL}/activity/batch", json=batch_data)
    assert response.status_code == 200
    data = response.json()
    assert "2" in data["message"]


# ============================================================================
# TESTS CONFIGURATION
# ============================================================================

def test_get_app_config(test_client):
    response = test_client.get(f"{BASE_URL}/config")
    assert response.status_code == 200
    data = response.json()
    assert "min_version_ios" in data
    assert "min_version_android" in data
    assert "force_update" in data


def test_check_app_version_supported(test_client):
    response = test_client.get(
        f"{BASE_URL}/config/check-version",
        params={"platform": "ios", "version": "1.5.0"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_supported"] is True
    assert data["is_latest"] is True


def test_check_app_version_outdated(test_client):
    response = test_client.get(
        f"{BASE_URL}/config/check-version",
        params={"platform": "ios", "version": "1.0.0"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_latest"] is False


# ============================================================================
# TESTS CRASH REPORTS
# ============================================================================

def test_report_crash(test_client):
    crash_data = {
        "error_message": "NullPointerException",
        "stack_trace": "at com.example.MainActivity.onCreate(MainActivity.java:42)",
        "device_info": {"model": "iPhone 14", "os": "iOS 17"},
        "app_version": "1.5.0"
    }
    response = test_client.post(f"{BASE_URL}/crashes", json=crash_data)
    assert response.status_code == 200
    data = response.json()
    assert "crash_id" in data


def test_list_crashes(test_client):
    response = test_client.get(f"{BASE_URL}/crashes")
    assert response.status_code == 200
    data = response.json()
    assert "crashes" in data
    assert "total" in data


# ============================================================================
# TESTS STATISTIQUES
# ============================================================================

def test_get_mobile_stats(test_client):
    response = test_client.get(f"{BASE_URL}/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_devices" in data
    assert "active_devices" in data
    assert "total_sessions" in data
    assert "crash_reports_today" in data
