"""
Configuration pytest et fixtures communes pour les tests Finance

Hérite des fixtures globales de app/conftest.py.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime
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


@pytest.fixture(scope="function")
def clean_database(db_session):
    """Nettoyer la base après chaque test."""
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
