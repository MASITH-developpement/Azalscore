"""
Fixtures pour les tests IAM v2
==============================

Ce fichier fournit des fixtures specifiques aux tests IAM.
Les fixtures globales (mock_auth_global, test_client, db_session, etc.)
sont heritees du conftest.py global dans app/conftest.py.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.core.saas_context import SaaSContext, UserRole, TenantScope


# ============================================================================
# FIXTURES LOCALES (complement au conftest global)
# ============================================================================

@pytest.fixture
def client(test_client):
    """
    Alias pour test_client (compatibilite avec anciens tests).

    Le test_client du conftest global ajoute deja les headers requis.
    """
    return test_client


@pytest.fixture
def auth_headers(tenant_id):
    """Headers d'authentification avec tenant ID"""
    return {
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": tenant_id
    }


# ============================================================================
# FIXTURES DONNEES IAM
# ============================================================================

@pytest.fixture
def sample_user_data():
    """Donnees utilisateur sample"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "password": "SecurePassword123!",
        "is_active": True
    }


@pytest.fixture
def sample_role_data():
    """Donnees role sample"""
    return {
        "name": "Test Role",
        "code": "TEST_ROLE",
        "description": "Role for testing",
        "is_active": True
    }


@pytest.fixture
def sample_role(sample_role_data, tenant_id):
    """Role sample"""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        **sample_role_data,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }


@pytest.fixture
def sample_permission():
    """Permission sample"""
    return {
        "id": str(uuid4()),
        "code": "iam.users.read",
        "name": "Read Users",
        "description": "Permission to read users",
        "module": "iam",
        "resource": "users",
        "action": "read"
    }


@pytest.fixture
def sample_group_data():
    """Donnees groupe sample"""
    return {
        "name": "Test Group",
        "code": "TEST_GROUP",
        "description": "Group for testing",
        "is_active": True
    }


@pytest.fixture
def sample_group(sample_group_data, tenant_id):
    """Groupe sample"""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        **sample_group_data,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }


@pytest.fixture
def sample_session(user_id, tenant_id):
    """Session sample"""
    return {
        "id": str(uuid4()),
        "user_id": user_id,
        "tenant_id": tenant_id,
        "token": "sample-jwt-token",
        "ip_address": "127.0.0.1",
        "user_agent": "pytest",
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
    }


@pytest.fixture
def sample_password_policy(tenant_id):
    """Politique de mot de passe sample"""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special_chars": True,
        "max_age_days": 90,
        "prevent_reuse_count": 5
    }


@pytest.fixture
def sample_invitation(tenant_id):
    """Invitation sample"""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "email": "invitee@example.com",
        "role_id": str(uuid4()),
        "token": "invitation-token-123",
        "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
        "created_at": datetime.now().isoformat()
    }


# ============================================================================
# BENCHMARK FIXTURE (mock if pytest-benchmark not installed)
# ============================================================================

@pytest.fixture
def benchmark():
    """Mock benchmark fixture if pytest-benchmark is not installed."""
    class MockBenchmark:
        def __call__(self, func, *args, **kwargs):
            return func(*args, **kwargs)

        def pedantic(self, func, *args, **kwargs):
            return func(*args, **kwargs)

    return MockBenchmark()


# ============================================================================
# HELPERS
# ============================================================================

@pytest.fixture
def assert_no_password_in_response():
    """Helper pour verifier qu'aucun mot de passe n'est retourne"""
    def _assert(response_data):
        assert "password" not in response_data
        assert "password_hash" not in response_data
        if "items" in response_data:
            for user in response_data["items"]:
                assert "password" not in user
                assert "password_hash" not in user
    return _assert
