"""
Configuration pytest globale pour tous les modules CORE SaaS v2.
Fournit les fixtures de base pour les tests.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.core.saas_context import SaaSContext, UserRole


@pytest.fixture
def tenant_id():
    """ID de tenant pour les tests."""
    return "tenant-test-001"


@pytest.fixture
def user_id():
    """ID d'utilisateur pour les tests (UUID)."""
    return "12345678-1234-1234-1234-123456789001"


@pytest.fixture(scope="function", autouse=True)
def mock_saas_context_global(tenant_id, user_id):
    """
    Mock global de SaaSContext pour tous les tests.
    Utilise dependency_overrides de FastAPI.
    """
    from uuid import UUID
    from app.core.saas_context import TenantScope

    def mock_get_context():
        return SaaSContext(
            tenant_id=tenant_id,
            user_id=UUID(user_id),
            role=UserRole.ADMIN,
            permissions={"*"},
            scope=TenantScope.TENANT,
            ip_address="127.0.0.1",
            user_agent="pytest",
            correlation_id="test-correlation-id",
            timestamp=datetime.utcnow()
        )

    from app.core.dependencies_v2 import get_saas_context
    from app.main import app

    # Override dependency
    app.dependency_overrides[get_saas_context] = mock_get_context

    yield mock_get_context

    # Cleanup
    app.dependency_overrides.pop(get_saas_context, None)


@pytest.fixture(scope="function", autouse=True)
def mock_db_global():
    """Mock global de la session database."""
    class MockDB:
        def query(self, *args, **kwargs):
            return self

        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return None

        def all(self):
            return []

        def count(self):
            return 0

        def offset(self, *args):
            return self

        def limit(self, *args):
            return self

        def commit(self):
            pass

        def rollback(self):
            pass

        def refresh(self, obj):
            pass

        def add(self, obj):
            pass

        def delete(self, obj):
            pass

        def close(self):
            pass

    mock_session = MockDB()

    from app.core.database import get_db
    from app.main import app

    def mock_get_db():
        try:
            yield mock_session
        finally:
            pass

    app.dependency_overrides[get_db] = mock_get_db

    yield mock_session

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def test_client(mock_db_global, mock_saas_context_global, tenant_id, user_id):
    """
    Client de test FastAPI avec toutes les dépendances mockées et headers configurés.
    À utiliser dans les tests au lieu de créer un TestClient au niveau module.
    """
    from app.main import app

    class TestClientWithHeaders(TestClient):
        """TestClient qui ajoute automatiquement les headers requis."""

        def request(self, method: str, url: str, **kwargs):
            # Ajouter les headers requis si pas déjà présents
            headers = kwargs.get("headers") or {}

            if "X-Tenant-ID" not in headers:
                headers["X-Tenant-ID"] = tenant_id
            if "Authorization" not in headers:
                headers["Authorization"] = f"Bearer mock-jwt-{user_id}"

            kwargs["headers"] = headers
            return super().request(method, url, **kwargs)

    return TestClientWithHeaders(app)
