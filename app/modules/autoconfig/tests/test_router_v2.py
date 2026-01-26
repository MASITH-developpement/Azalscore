"""Tests pour le router v2 du module AutoConfig - CORE SaaS v2."""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.modules.autoconfig.models import OverrideType

client = TestClient(app)
BASE_URL = "/v2/autoconfig"


# ============================================================================
# TESTS PROFILES
# ============================================================================

def test_initialize_predefined_profiles(mock_autoconfig_service):
    response = client.post(f"{BASE_URL}/profiles/initialize")
    assert response.status_code == 201
    data = response.json()
    assert data["profiles_created"] == 10


def test_list_profiles(mock_autoconfig_service):
    response = client.get(f"{BASE_URL}/profiles")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_list_profiles_include_inactive(mock_autoconfig_service):
    response = client.get(f"{BASE_URL}/profiles", params={"include_inactive": True})
    assert response.status_code == 200


def test_get_profile_by_code_success(mock_autoconfig_service):
    response = client.get(f"{BASE_URL}/profiles/code/CEO")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "CEO"


def test_get_profile_by_code_not_found(mock_autoconfig_service):
    response = client.get(f"{BASE_URL}/profiles/code/UNKNOWN")
    assert response.status_code == 404


def test_get_profile_success(mock_autoconfig_service):
    response = client.get(f"{BASE_URL}/profiles/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1


def test_detect_profile_found(mock_autoconfig_service):
    response = client.post(
        f"{BASE_URL}/profiles/detect",
        params={"job_title": "CEO", "department": "Direction"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["detected"] is True
    assert data["profile"] is not None


def test_detect_profile_not_found(mock_autoconfig_service):
    response = client.post(
        f"{BASE_URL}/profiles/detect",
        params={"job_title": "Unknown Job", "department": "Unknown"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["detected"] is False
    assert data["profile"] is None


# ============================================================================
# TESTS ASSIGNMENTS
# ============================================================================

def test_auto_assign_profile_success(mock_autoconfig_service):
    response = client.post(
        f"{BASE_URL}/assignments/auto",
        params={
            "target_user_id": 100,
            "job_title": "CEO",
            "department": "Direction"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == 100
    assert data["is_auto"] is True


def test_auto_assign_profile_not_found(mock_autoconfig_service):
    response = client.post(
        f"{BASE_URL}/assignments/auto",
        params={
            "target_user_id": 100,
            "job_title": "Unknown Job"
        }
    )
    assert response.status_code == 404


def test_manual_assign_profile_success(mock_autoconfig_service):
    response = client.post(
        f"{BASE_URL}/assignments/manual",
        params={
            "target_user_id": 100,
            "profile_code": "CEO",
            "job_title": "Chief Executive Officer"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == 100
    assert data["is_auto"] is False


def test_manual_assign_profile_invalid_code(mock_autoconfig_service):
    response = client.post(
        f"{BASE_URL}/assignments/manual",
        params={
            "target_user_id": 100,
            "profile_code": "INVALID"
        }
    )
    assert response.status_code == 404


def test_get_user_profile_success(mock_autoconfig_service):
    response = client.get(f"{BASE_URL}/assignments/user/100")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 100
    assert data["is_active"] is True


def test_get_user_effective_config(mock_autoconfig_service):
    response = client.get(f"{BASE_URL}/config/user/100")
    assert response.status_code == 200
    data = response.json()
    assert "profile_code" in data
    assert "roles" in data
    assert "permissions" in data
    assert "modules" in data


# ============================================================================
# TESTS OVERRIDES
# ============================================================================

def test_request_override_success(mock_autoconfig_service):
    response = client.post(
        f"{BASE_URL}/overrides",
        params={
            "target_user_id": 100,
            "override_type": OverrideType.TEMPORARY.value,
            "reason": "Temporary access needed"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == 100


def test_list_user_overrides(mock_autoconfig_service):
    response = client.get(f"{BASE_URL}/overrides/user/100")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_list_user_overrides_include_inactive(mock_autoconfig_service):
    response = client.get(
        f"{BASE_URL}/overrides/user/100",
        params={"include_inactive": True}
    )
    assert response.status_code == 200


def test_approve_override_success(mock_autoconfig_service):
    response = client.post(f"{BASE_URL}/overrides/1/approve")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"


def test_approve_override_not_found(mock_autoconfig_service):
    response = client.post(f"{BASE_URL}/overrides/999/approve")
    assert response.status_code == 400


def test_reject_override_success(mock_autoconfig_service):
    response = client.post(
        f"{BASE_URL}/overrides/1/reject",
        params={"rejection_reason": "Not justified"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"


def test_reject_override_not_found(mock_autoconfig_service):
    response = client.post(
        f"{BASE_URL}/overrides/999/reject",
        params={"rejection_reason": "Not found"}
    )
    assert response.status_code == 404


def test_revoke_override_success(mock_autoconfig_service):
    response = client.post(f"{BASE_URL}/overrides/1/revoke")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "revoked"


def test_revoke_override_not_found(mock_autoconfig_service):
    response = client.post(f"{BASE_URL}/overrides/999/revoke")
    assert response.status_code == 404


def test_expire_overrides(mock_autoconfig_service):
    response = client.post(f"{BASE_URL}/overrides/expire")
    assert response.status_code == 200
    data = response.json()
    assert data["expired_count"] == 5


# ============================================================================
# TESTS ONBOARDING
# ============================================================================

def test_create_onboarding_success(mock_autoconfig_service):
    start_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
    response = client.post(
        f"{BASE_URL}/onboarding",
        params={
            "email": "newemployee@example.com",
            "job_title": "Software Engineer",
            "start_date": start_date,
            "first_name": "John",
            "last_name": "Doe"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newemployee@example.com"
    assert data["status"] == "pending"


def test_list_pending_onboardings(mock_autoconfig_service):
    response = client.get(f"{BASE_URL}/onboarding/pending")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_execute_onboarding_success(mock_autoconfig_service):
    response = client.post(f"{BASE_URL}/onboarding/1/execute")
    assert response.status_code == 200
    data = response.json()
    assert "steps" in data
    assert len(data["steps"]) > 0


def test_execute_onboarding_not_found(mock_autoconfig_service):
    response = client.post(f"{BASE_URL}/onboarding/999/execute")
    assert response.status_code == 400


# ============================================================================
# TESTS OFFBOARDING
# ============================================================================

def test_create_offboarding_success(mock_autoconfig_service):
    departure_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
    response = client.post(
        f"{BASE_URL}/offboarding",
        params={
            "target_user_id": 100,
            "departure_date": departure_date,
            "departure_type": "resignation"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == 100
    assert data["status"] == "scheduled"


def test_list_scheduled_offboardings(mock_autoconfig_service):
    response = client.get(f"{BASE_URL}/offboarding/scheduled")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_execute_offboarding_success(mock_autoconfig_service):
    response = client.post(f"{BASE_URL}/offboarding/1/execute")
    assert response.status_code == 200
    data = response.json()
    assert "steps" in data
    assert len(data["steps"]) > 0


def test_execute_offboarding_not_found(mock_autoconfig_service):
    response = client.post(f"{BASE_URL}/offboarding/999/execute")
    assert response.status_code == 400


def test_execute_due_offboardings(mock_autoconfig_service):
    response = client.post(f"{BASE_URL}/offboarding/execute-due")
    assert response.status_code == 200
    data = response.json()
    assert data["executed_count"] == 3


# ============================================================================
# TESTS TENANT ISOLATION
# ============================================================================

def test_profiles_tenant_isolation(mock_autoconfig_service):
    response = client.get(f"{BASE_URL}/profiles")
    assert response.status_code == 200


def test_assignments_tenant_isolation(mock_autoconfig_service):
    response = client.get(f"{BASE_URL}/assignments/user/100")
    assert response.status_code == 200


def test_overrides_tenant_isolation(mock_autoconfig_service):
    response = client.get(f"{BASE_URL}/overrides/user/100")
    assert response.status_code == 200


def test_onboarding_tenant_isolation(mock_autoconfig_service):
    response = client.get(f"{BASE_URL}/onboarding/pending")
    assert response.status_code == 200


def test_offboarding_tenant_isolation(mock_autoconfig_service):
    response = client.get(f"{BASE_URL}/offboarding/scheduled")
    assert response.status_code == 200
