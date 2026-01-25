"""
Fixtures pour les tests IAM v2
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient

from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext, UserRole
from app.main import app


# ============================================================================
# FIXTURES GLOBALES
# ============================================================================

@pytest.fixture
def client():
    """Client de test FastAPI"""
    return TestClient(app)


@pytest.fixture
def tenant_id():
    """Tenant ID de test"""
    return "tenant-test-001"


@pytest.fixture
def user_id():
    """User ID de test"""
    return "user-test-001"


@pytest.fixture
def auth_headers():
    """Headers d'authentification"""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture(autouse=True)
def mock_saas_context(monkeypatch, tenant_id, user_id):
    """Mock get_saas_context pour tous les tests"""
    def mock_get_context():
        return SaaSContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role=UserRole.ADMIN,
            permissions={"iam.*"},
            scope="tenant",
            session_id="session-test",
            ip_address="127.0.0.1",
            user_agent="pytest",
            correlation_id="test-correlation"
        )

    from app.modules.iam import router_v2
    monkeypatch.setattr(router_v2, "get_saas_context", mock_get_context)

    return mock_get_context


# ============================================================================
# FIXTURES DONNÉES IAM
# ============================================================================

@pytest.fixture
def sample_user_data():
    """Données utilisateur sample"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "password": "SecurePassword123!",
        "is_active": True
    }


@pytest.fixture
def sample_user(sample_user_data, tenant_id, user_id):
    """Utilisateur sample (dict simulant réponse API)"""
    return {
        "id": user_id,
        "tenant_id": tenant_id,
        "email": sample_user_data["email"],
        "username": sample_user_data["username"],
        "first_name": sample_user_data["first_name"],
        "last_name": sample_user_data["last_name"],
        "is_active": sample_user_data["is_active"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }


@pytest.fixture
def sample_role_data():
    """Données rôle sample"""
    return {
        "name": "Test Role",
        "code": "TEST_ROLE",
        "description": "Role for testing",
        "is_active": True
    }


@pytest.fixture
def sample_role(sample_role_data, tenant_id):
    """Rôle sample"""
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
    """Données groupe sample"""
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
# HELPERS
# ============================================================================

@pytest.fixture
def assert_no_password_in_response():
    """Helper pour vérifier qu'aucun mot de passe n'est retourné"""
    def _assert(response_data):
        assert "password" not in response_data
        assert "password_hash" not in response_data
        if "items" in response_data:
            for user in response_data["items"]:
                assert "password" not in user
                assert "password_hash" not in user
    return _assert
