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
    Valeur attendue : 'healthy', 'unhealthy' ou 'degraded'.
    """
    response = client.get("/health")
    data = response.json()

    assert "status" in data
    assert data["status"] in ["healthy", "unhealthy", "degraded"]


def test_health_endpoint_returns_components(client):
    """
    Vérifie que /health retourne les composants système.
    La clé 'components' doit être présente et contenir une liste.
    """
    response = client.get("/health")
    data = response.json()

    assert "components" in data
    assert isinstance(data["components"], list)
    assert len(data["components"]) > 0

    # Vérifier la structure d'un composant
    component = data["components"][0]
    assert "name" in component
    assert "status" in component
    assert "message" in component


def test_health_endpoint_returns_database_component(client):
    """
    Vérifie que /health retourne l'état de la base de données.
    Un composant 'database' doit être présent.
    """
    response = client.get("/health")
    data = response.json()

    # Trouver le composant database
    db_component = next(
        (c for c in data["components"] if c["name"] == "database"),
        None
    )
    assert db_component is not None
    assert db_component["status"] in ["healthy", "unhealthy"]


def test_health_endpoint_json_structure(client):
    """
    Vérifie la structure complète du JSON retourné par /health.
    Toutes les clés obligatoires doivent être présentes.
    """
    response = client.get("/health")
    data = response.json()

    # Structure attendue (nouveau format ÉLITE)
    expected_keys = {"status", "components", "environment", "timestamp", "version", "uptime_seconds"}
    assert expected_keys.issubset(set(data.keys()))

    # Types des valeurs
    assert isinstance(data["status"], str)
    assert isinstance(data["components"], list)
    assert isinstance(data["environment"], str)
    assert isinstance(data["timestamp"], str)
    assert isinstance(data["version"], str)
    assert isinstance(data["uptime_seconds"], (int, float))
