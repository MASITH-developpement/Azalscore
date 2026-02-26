"""
Tests d'intégration API - Module Integrations (GAP-086)

Tests des endpoints HTTP avec TestClient FastAPI.
"""
import pytest
from uuid import uuid4
from datetime import datetime


class TestConnectionAPI:
    """Tests API Connection."""

    def test_create_connection(self, test_client):
        """Créer une connexion."""
        data = {
            "code": f"CONN-SAGE-{uuid4().hex[:6]}",
            "name": "Connexion Sage 100c",
            "connector_type": "sage",
            "auth_type": "api_key",
            "base_url": "https://api.sage.com/v1",
            "credentials": {
                "api_key": "test-api-key"
            },
            "settings": {
                "company_id": "COMPANY001"
            }
        }
        response = test_client.post("/integrations/connections", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["code"].startswith("CONN-SAGE")
        assert result["status"] == "pending"

    def test_list_connections(self, test_client):
        """Lister les connexions."""
        response = test_client.get("/integrations/connections")
        assert response.status_code == 200
        result = response.json()
        assert "items" in result

    def test_get_connection_by_id(self, test_client, connection_id: str):
        """Récupérer une connexion par ID."""
        response = test_client.get(f"/integrations/connections/{connection_id}")
        assert response.status_code == 200

    def test_test_connection(self, test_client, connection_id: str):
        """Tester une connexion."""
        response = test_client.post(f"/integrations/connections/{connection_id}/test")
        assert response.status_code in [200, 400, 503]  # Dépend de la disponibilité

    def test_update_credentials(self, test_client, connection_id: str):
        """Mettre à jour les credentials."""
        data = {
            "credentials": {
                "api_key": "new-api-key"
            }
        }
        response = test_client.patch(f"/integrations/connections/{connection_id}", json=data)
        assert response.status_code == 200

    def test_disconnect(self, test_client, connection_id: str):
        """Déconnecter."""
        response = test_client.post(f"/integrations/connections/{connection_id}/disconnect")
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "disconnected"


class TestOAuth2Flow:
    """Tests OAuth2."""

    def test_get_oauth_url(self, test_client):
        """Récupérer l'URL d'autorisation OAuth2."""
        data = {
            "connector_type": "salesforce",
            "redirect_uri": "https://app.example.com/callback"
        }
        response = test_client.post("/integrations/oauth/authorize", json=data)
        assert response.status_code == 200
        result = response.json()
        assert "authorization_url" in result

    def test_oauth_callback(self, test_client):
        """Callback OAuth2."""
        data = {
            "code": "test-auth-code",
            "state": "test-state"
        }
        response = test_client.post("/integrations/oauth/callback", json=data)
        assert response.status_code in [200, 400]  # 400 si code invalide


class TestEntityMappingAPI:
    """Tests API Entity Mapping."""

    def test_create_mapping(self, test_client, connection_id: str):
        """Créer un mapping d'entité."""
        data = {
            "code": f"MAP-CUST-{uuid4().hex[:6]}",
            "name": "Synchronisation clients",
            "connection_id": connection_id,
            "entity_type": "customer",
            "source_entity": "Account",
            "target_entity": "contacts",
            "direction": "import",
            "field_mappings": [
                {"source": "Name", "target": "company_name", "transform": "uppercase"},
                {"source": "Phone", "target": "phone"},
                {"source": "Email", "target": "email"}
            ],
            "dedup_key_source": "Id",
            "dedup_key_target": "external_id"
        }
        response = test_client.post("/integrations/mappings", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["code"].startswith("MAP-CUST")

    def test_list_mappings(self, test_client, connection_id: str):
        """Lister les mappings."""
        response = test_client.get(f"/integrations/mappings?connection_id={connection_id}")
        assert response.status_code == 200

    def test_update_mapping(self, test_client, mapping_id: str):
        """Mettre à jour un mapping."""
        data = {
            "field_mappings": [
                {"source": "Name", "target": "name"}
            ]
        }
        response = test_client.patch(f"/integrations/mappings/{mapping_id}", json=data)
        assert response.status_code == 200


class TestSyncJobAPI:
    """Tests API Sync Job."""

    def test_create_sync_job(self, test_client, connection_id: str, mapping_id: str):
        """Créer un job de synchronisation."""
        data = {
            "connection_id": connection_id,
            "entity_mapping_id": mapping_id,
            "direction": "import",
            "frequency": "daily",
            "conflict_resolution": "newest_wins"
        }
        response = test_client.post("/integrations/sync-jobs", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["status"] == "pending"

    def test_list_sync_jobs(self, test_client):
        """Lister les jobs."""
        response = test_client.get("/integrations/sync-jobs")
        assert response.status_code == 200

    def test_run_sync_job(self, test_client, job_id: str):
        """Lancer un job de synchronisation."""
        response = test_client.post(f"/integrations/sync-jobs/{job_id}/run")
        assert response.status_code in [200, 202]  # 202 si async

    def test_cancel_sync_job(self, test_client, job_id: str):
        """Annuler un job."""
        response = test_client.post(f"/integrations/sync-jobs/{job_id}/cancel")
        assert response.status_code in [200, 400]  # 400 si pas en cours

    def test_get_sync_job_status(self, test_client, job_id: str):
        """Récupérer le statut d'un job."""
        response = test_client.get(f"/integrations/sync-jobs/{job_id}")
        assert response.status_code == 200
        result = response.json()
        assert "status" in result
        assert "processed_records" in result

    def test_get_sync_logs(self, test_client, job_id: str):
        """Récupérer les logs de synchronisation."""
        response = test_client.get(f"/integrations/sync-jobs/{job_id}/logs")
        assert response.status_code == 200


class TestConflictAPI:
    """Tests API Conflict."""

    def test_list_conflicts(self, test_client):
        """Lister les conflits non résolus."""
        response = test_client.get("/integrations/conflicts")
        assert response.status_code == 200

    def test_resolve_conflict(self, test_client, conflict_id: str):
        """Résoudre un conflit."""
        data = {
            "resolution": "source_wins",
            "resolved_data": {"name": "Test Company"}
        }
        response = test_client.post(f"/integrations/conflicts/{conflict_id}/resolve", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["resolved_at"] is not None

    def test_bulk_resolve_conflicts(self, test_client):
        """Résoudre en masse."""
        data = {
            "conflict_ids": [str(uuid4())],
            "resolution": "target_wins"
        }
        response = test_client.post("/integrations/conflicts/bulk-resolve", json=data)
        assert response.status_code in [200, 400]


class TestWebhookAPI:
    """Tests API Webhook."""

    def test_create_webhook(self, test_client, connection_id: str):
        """Créer un webhook."""
        data = {
            "connection_id": connection_id,
            "endpoint_path": f"/webhooks/salesforce-{uuid4().hex[:6]}",
            "subscribed_events": ["contact.created", "contact.updated"]
        }
        response = test_client.post("/integrations/webhooks", json=data)
        assert response.status_code == 201
        result = response.json()
        assert "secret_key" in result  # Secret généré

    def test_list_webhooks(self, test_client):
        """Lister les webhooks."""
        response = test_client.get("/integrations/webhooks")
        assert response.status_code == 200

    def test_regenerate_secret(self, test_client, webhook_id: str):
        """Régénérer le secret."""
        response = test_client.post(f"/integrations/webhooks/{webhook_id}/regenerate-secret")
        assert response.status_code == 200
        result = response.json()
        assert "secret_key" in result

    def test_disable_webhook(self, test_client, webhook_id: str):
        """Désactiver un webhook."""
        data = {"is_active": False}
        response = test_client.patch(f"/integrations/webhooks/{webhook_id}", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["is_active"] is False


class TestConnectorTypes:
    """Tests types de connecteurs."""

    def test_list_connector_types(self, test_client):
        """Lister les types de connecteurs disponibles."""
        response = test_client.get("/integrations/connector-types")
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_connector_schema(self, test_client):
        """Récupérer le schéma d'un connecteur."""
        response = test_client.get("/integrations/connector-types/sage/schema")
        assert response.status_code == 200
        result = response.json()
        assert "required_fields" in result
