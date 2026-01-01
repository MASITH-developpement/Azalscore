"""
AZALS - Tests de l'endpoint /health
Tests automatisés pour la validation du point de santé de l'API
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """
    Fixture pytest qui fournit un client de test FastAPI.
    Permet de tester l'API sans la démarrer réellement.
    """
    return TestClient(app)


def test_health_endpoint_exists(client):
    """
    Vérifie que l'endpoint /health existe et répond.
    Code HTTP 200 attendu.
    """
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_returns_status(client):
    """
    Vérifie que /health retourne un JSON avec la clé 'status'.
    Valeur attendue : 'ok' ou 'degraded'.
    """
    response = client.get("/health")
    data = response.json()
    
    assert "status" in data
    assert data["status"] in ["ok", "degraded"]


def test_health_endpoint_returns_api_status(client):
    """
    Vérifie que /health retourne l'état de l'API.
    La clé 'api' doit être présente et à True.
    """
    response = client.get("/health")
    data = response.json()
    
    assert "api" in data
    assert data["api"] is True


def test_health_endpoint_returns_database_status(client):
    """
    Vérifie que /health retourne l'état de la base de données.
    La clé 'database' doit être présente et être un booléen.
    """
    response = client.get("/health")
    data = response.json()
    
    assert "database" in data
    assert isinstance(data["database"], bool)


def test_health_endpoint_json_structure(client):
    """
    Vérifie la structure complète du JSON retourné par /health.
    Toutes les clés obligatoires doivent être présentes.
    """
    response = client.get("/health")
    data = response.json()
    
    # Structure attendue
    expected_keys = {"status", "api", "database"}
    assert set(data.keys()) == expected_keys
    
    # Types des valeurs
    assert isinstance(data["status"], str)
    assert isinstance(data["api"], bool)
    assert isinstance(data["database"], bool)
