"""
Fixtures pour les tests IAM v2
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext, UserRole, TenantScope
from app.main import app


# ============================================================================
# FIXTURES GLOBALES
# ============================================================================

@pytest.fixture
def client():
    """Client de test FastAPI"""
    return TestClient(app)


@pytest.fixture
def db_session(mock_db_global):
    """
    Alias for mock_db_global - provides a mock DB session for tests.
    This fixture is used by tests that need direct DB access.
    """
    return mock_db_global


@pytest.fixture
def tenant_id():
    """Tenant ID de test"""
    return "tenant-test-001"


@pytest.fixture
def user_id():
    """User ID de test (UUID format)"""
    return "12345678-1234-1234-1234-123456789012"


@pytest.fixture
def auth_headers(tenant_id):
    """Headers d'authentification avec tenant ID"""
    return {
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": tenant_id
    }


@pytest.fixture(autouse=True)
def mock_saas_context(monkeypatch, tenant_id, user_id):
    """Mock get_saas_context et SaaSCore.authenticate pour tous les tests"""
    from uuid import UUID

    # Convert user_id to UUID if it's a string
    user_uuid = UUID(user_id) if isinstance(user_id, str) and "-" in user_id else uuid4()

    mock_context = SaaSContext(
        tenant_id=tenant_id,
        user_id=user_uuid,
        role=UserRole.ADMIN,
        permissions={"iam.*", "*"},
        scope=TenantScope.TENANT,
        ip_address="127.0.0.1",
        user_agent="pytest",
        correlation_id="test-correlation",
        timestamp=datetime.utcnow()
    )

    # Mock get_saas_context dependency
    def mock_get_context():
        return mock_context

    from app.modules.iam import router_v2
    monkeypatch.setattr(router_v2, "get_saas_context", mock_get_context)

    # Also override via FastAPI dependency_overrides
    app.dependency_overrides[get_saas_context] = mock_get_context

    # Mock SaaSCore.authenticate to return success
    mock_auth_result = MagicMock()
    mock_auth_result.success = True
    mock_auth_result.context = mock_context

    # Mock SessionLocal to avoid real DB connections
    # Create a mock user for DB queries
    from app.core.models import UserRole as ModelUserRole

    mock_user = MagicMock()
    mock_user.id = user_uuid
    mock_user.tenant_id = tenant_id
    mock_user.email = "test@example.com"
    mock_user.role = ModelUserRole.ADMIN  # Use model enum
    mock_user.is_active = True

    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = mock_user

    def mock_session_local():
        return mock_session

    monkeypatch.setattr(
        "app.core.core_auth_middleware.SessionLocal",
        mock_session_local
    )

    # Mock SaaSCore class
    mock_core = MagicMock()
    mock_core.authenticate.return_value = mock_auth_result

    def mock_saas_core_init(*args, **kwargs):
        return mock_core

    monkeypatch.setattr(
        "app.core.core_auth_middleware.SaaSCore",
        mock_saas_core_init
    )

    yield mock_context

    # Cleanup
    app.dependency_overrides.pop(get_saas_context, None)


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


class MockUser:
    """Mock user object with attributes for tests."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)


@pytest.fixture
def sample_user(sample_user_data, tenant_id, user_id):
    """Utilisateur sample (objet simulant User model)"""
    return MockUser(
        id=user_id,
        tenant_id=tenant_id,
        email=sample_user_data["email"],
        username=sample_user_data["username"],
        first_name=sample_user_data["first_name"],
        last_name=sample_user_data["last_name"],
        is_active=sample_user_data["is_active"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


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
    """Helper pour vérifier qu'aucun mot de passe n'est retourné"""
    def _assert(response_data):
        assert "password" not in response_data
        assert "password_hash" not in response_data
        if "items" in response_data:
            for user in response_data["items"]:
                assert "password" not in user
                assert "password_hash" not in user
    return _assert
