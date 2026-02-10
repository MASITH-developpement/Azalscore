"""
Configuration pytest et fixtures communes pour les tests Finance
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from uuid import uuid4

from app.core.saas_context import SaaSContext, UserRole
from fastapi import Depends


# ============================================================================
# FIXTURES GLOBALES
# ============================================================================

@pytest.fixture(scope="session")
def test_config():
    """Configuration de test"""
    return {
        "database_url": "sqlite:///:memory:",
        "testing": True
    }


@pytest.fixture(autouse=True)
def mock_saas_context(monkeypatch):
    """
    Mock get_saas_context pour tous les tests
    Remplace la dépendance FastAPI par un mock
    """
    def mock_get_context():
        return SaaSContext(
            tenant_id="tenant-test-001",
            user_id="user-test-001",
            role=UserRole.ADMIN,
            permissions=["finance.*"],
            scope="full",
            session_id="session-test",
            ip_address="127.0.0.1",
            user_agent="pytest",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow()
        )

    # Remplacer la dépendance FastAPI
    from app.modules.finance import router_v2
    monkeypatch.setattr(router_v2, "get_saas_context", mock_get_context)

    return mock_get_context


@pytest.fixture(scope="function")
def clean_database(db_session):
    """Nettoyer la base après chaque test"""
    yield
    db_session.rollback()


# ============================================================================
# FIXTURES HELPERS
# ============================================================================

@pytest.fixture
def create_test_data():
    """Factory pour créer des données de test"""
    def _create(model_class, **kwargs):
        instance = model_class(**kwargs)
        return instance
    return _create


@pytest.fixture
def mock_service():
    """Mock du service Finance pour tests unitaires"""
    service = Mock()
    service.create_account = Mock(return_value={"id": str(uuid4()), "code": "TEST"})
    service.list_accounts = Mock(return_value=[])
    return service


# ============================================================================
# FIXTURES ASSERTIONS
# ============================================================================

@pytest.fixture
def assert_response_success():
    """Helper pour asserter une réponse successful"""
    def _assert(response, expected_status=200):
        assert response.status_code == expected_status
        if response.status_code != 204:  # No content
            data = response.json()
            assert data is not None
            return data
    return _assert


@pytest.fixture
def assert_tenant_isolation():
    """Helper pour vérifier l'isolation tenant"""
    def _assert(response, tenant_id):
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                for item in data:
                    if "tenant_id" in item:
                        assert item["tenant_id"] == tenant_id
            elif isinstance(data, dict) and "tenant_id" in data:
                assert data["tenant_id"] == tenant_id
    return _assert
