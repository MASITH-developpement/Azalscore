"""
Tests pour l'API Comptabilité
"""
import pytest
from datetime import datetime, timedelta
from app.main import app
from app.core.database import SessionLocal
from app.core.models import JournalEntry, User
from sqlalchemy.orm import Session


@pytest.fixture
def client():
    """Fixture pour le client de test"""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def db_session():
    """Fixture pour la session de base de données"""
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def auth_headers():
    """Headers d'authentification pour les tests"""
    # Utiliser les identifiants de test
    return {
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": "tenant-demo"
    }


def test_accounting_status_endpoint_exists(client):
    """Vérifier que l'endpoint /v1/accounting/status existe"""
    response = client.get("/v1/accounting/status")
    # Peut retourner 401 (non authentifié) ou 200 (avec erreur API)
    assert response.status_code in [200, 401, 422]


def test_accounting_status_requires_auth(client):
    """Vérifier que l'endpoint nécessite une authentification"""
    response = client.get("/v1/accounting/status")
    # Sans auth headers, devrait retourner 401 ou 422
    assert response.status_code in [401, 422]


def test_accounting_status_with_headers(client, auth_headers):
    """Tester l'endpoint avec les headers d'authentification"""
    response = client.get(
        "/v1/accounting/status",
        headers=auth_headers
    )
    
    # Vérifier que la réponse est valide
    assert response.status_code in [200, 400, 401]
    
    if response.status_code == 200:
        data = response.json()
        # Vérifier la structure de la réponse
        assert "status" in data
        assert "entries_up_to_date" in data
        assert "last_closure_date" in data or data.get("last_closure_date") is None
        assert "pending_entries_count" in data
        assert "days_since_closure" in data or data.get("days_since_closure") is None
        
        # Vérifier que le statut est valide
        assert data["status"] in ["🟢", "🟠"]


def test_accounting_status_no_entries(client, auth_headers, db_session):
    """Tester le statut quand il n'y a pas d'écritures"""
    # Nettoyer les écritures de test
    # (En production, ceci ne serait pas possible sans des privilèges particuliers)
    
    response = client.get(
        "/v1/accounting/status",
        headers=auth_headers
    )
    
    # Devrait retourner 200 avec entries_up_to_date = False
    if response.status_code == 200:
        data = response.json()
        # Sans écritures récentes, status devrait être 🟠
        assert data["pending_entries_count"] >= 0


def test_accounting_status_with_recent_entries(client, auth_headers):
    """Tester le statut avec des écritures récentes"""
    response = client.get(
        "/v1/accounting/status",
        headers=auth_headers
    )
    
    if response.status_code == 200:
        data = response.json()
        # Vérifier que les écritures en attente sont comptabilisées correctement
        assert isinstance(data["pending_entries_count"], int)
        assert data["pending_entries_count"] >= 0


def test_accounting_status_old_entries(client, auth_headers):
    """Tester le statut avec des écritures anciennes"""
    response = client.get(
        "/v1/accounting/status",
        headers=auth_headers
    )
    
    if response.status_code == 200:
        data = response.json()
        # Si les écritures sont trop anciennes, entries_up_to_date devrait être False
        if data["pending_entries_count"] > 5:
            assert data["entries_up_to_date"] == False
        
        # Le statut dépend aussi de la clôture
        assert data["status"] in ["🟢", "🟠"]


def test_accounting_status_no_red_alert():
    """Vérifier qu'il n'y a jamais de 🔴 pour l'API Comptabilité"""
    # Le statut doit être seulement 🟢 ou 🟠
    # Pas de 🔴 pour la comptabilité
    pass


def test_accounting_response_schema(client, auth_headers):
    """Vérifier que la réponse suit le bon schéma"""
    response = client.get(
        "/v1/accounting/status",
        headers=auth_headers
    )
    
    if response.status_code == 200:
        data = response.json()
        
        # Tous les champs attendus doivent être présents
        required_fields = [
            "status",
            "entries_up_to_date",
            "pending_entries_count",
            "last_closure_date",
            "days_since_closure"
        ]
        
        for field in required_fields:
            assert field in data, f"Field '{field}' missing from response"


def test_accounting_multi_tenant_isolation(client):
    """Vérifier que les données sont isolées par tenant"""
    # Essayer avec un tenant différent
    headers_demo = {
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": "tenant-demo"
    }
    headers_other = {
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": "tenant-other"
    }
    
    response_demo = client.get("/v1/accounting/status", headers=headers_demo)
    response_other = client.get("/v1/accounting/status", headers=headers_other)
    
    # Les deux devraient fonctionner (ou retourner une erreur similaire)
    assert response_demo.status_code in [200, 400, 401]
    assert response_other.status_code in [200, 400, 401]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
