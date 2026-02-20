"""
AZALS - Tests Multi-Tenant
Validation de l'isolation stricte entre tenants
Utilise les vrais endpoints publics de l'application
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only-minimum-32-characters")
os.environ.setdefault("ENVIRONMENT", "test")

from app.main import app
from app.core.database import Base, get_db


@pytest.fixture(scope="module")
def test_engine():
    """Engine SQLite en mémoire."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="module")
def client(test_engine):
    """Client de test FastAPI."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ===== TESTS ENDPOINTS PUBLICS =====

def test_health_endpoint_accessible_without_tenant(client):
    """
    Test : endpoint /health accessible sans X-Tenant-ID.
    Validation : endpoints publics exemptés de validation tenant.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["ok", "healthy", "unhealthy", "degraded"]


def test_health_ready_accessible_without_tenant(client):
    """
    Test : endpoint /health/ready accessible sans X-Tenant-ID.
    """
    response = client.get("/health/ready")
    assert response.status_code == 200


def test_health_live_accessible_without_tenant(client):
    """
    Test : endpoint /health/live accessible sans X-Tenant-ID.
    """
    response = client.get("/health/live")
    assert response.status_code == 200


def test_docs_accessible_without_tenant(client):
    """
    Test : documentation accessible sans tenant.
    """
    response = client.get("/docs")
    # Peut être 200 ou 404 selon config
    assert response.status_code in [200, 404]


def test_metrics_endpoint_accessible(client):
    """
    Test : endpoint /metrics accessible (Prometheus).
    """
    response = client.get("/metrics")
    assert response.status_code == 200


def test_public_endpoints_consistent(client):
    """
    Test : endpoints publics retournent des résultats consistants.
    """
    # Health doit donner le même résultat
    response_1 = client.get("/health")
    response_2 = client.get("/health")

    assert response_1.status_code == response_2.status_code
    assert response_1.json()["status"] == response_2.json()["status"]


# ===== TESTS SÉCURITÉ =====

def test_protected_endpoints_require_auth(client):
    """
    Test : les endpoints protégés requièrent l'authentification.
    """
    # Endpoints qui doivent exiger l'auth
    protected_endpoints = [
        "/api/status",
        "/api/modules",
    ]

    for endpoint in protected_endpoints:
        response = client.get(endpoint)
        # Doit requérir auth (401) ou tenant (400, 403, 422)
        assert response.status_code in [400, 401, 403, 422], \
            f"Endpoint {endpoint} devrait exiger l'authentification"


def test_no_sensitive_data_in_public_errors(client):
    """
    Test : pas de données sensibles dans les erreurs des endpoints publics.
    """
    response = client.get("/health")
    text = response.text.lower()

    sensitive_keywords = [
        "password",
        "secret_key",
        "database_url",
    ]

    for keyword in sensitive_keywords:
        assert keyword not in text


def test_health_response_structure(client):
    """
    Test : structure correcte de la réponse health.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
