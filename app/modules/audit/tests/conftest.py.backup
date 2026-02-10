"""
Fixtures pour les tests audit v2
"""

import pytest
from datetime import datetime, timedelta, date
from uuid import uuid4
from fastapi.testclient import TestClient

from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext, UserRole
from app.main import app


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
            permissions={"audit.*"},
            scope="tenant",
            session_id="session-test",
            ip_address="127.0.0.1",
            user_agent="pytest",
            correlation_id="test-correlation"
        )

    from app.modules.audit import router_v2
    monkeypatch.setattr(router_v2, "get_saas_context", mock_get_context)

    return mock_get_context
