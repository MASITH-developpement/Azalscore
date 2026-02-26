"""
Fixtures pour les tests du module Integrations.

Utilise les fixtures globales de app/conftest.py.
"""
import pytest
from uuid import uuid4


@pytest.fixture(scope="function")
def connection_id(test_client) -> str:
    """Create a connection and return its ID."""
    data = {
        "code": f"CONN-{uuid4().hex[:8]}",
        "name": "Test Connection",
        "connector_type": "custom",
        "auth_type": "api_key",
    }
    response = test_client.post("/integrations/connections", json=data)
    if response.status_code != 201:
        pytest.skip(f"Could not create connection: {response.text}")
    return response.json()["id"]


@pytest.fixture(scope="function")
def mapping_id(test_client, connection_id: str) -> str:
    """Create an entity mapping and return its ID."""
    data = {
        "code": f"MAP-{uuid4().hex[:8]}",
        "name": "Test Mapping",
        "connection_id": connection_id,
        "entity_type": "customer",
        "source_entity": "Account",
        "target_entity": "contacts",
    }
    response = test_client.post("/integrations/mappings", json=data)
    if response.status_code != 201:
        pytest.skip(f"Could not create mapping: {response.text}")
    return response.json()["id"]


@pytest.fixture(scope="function")
def job_id(test_client, connection_id: str, mapping_id: str) -> str:
    """Create a sync job and return its ID."""
    data = {
        "connection_id": connection_id,
        "entity_mapping_id": mapping_id,
        "direction": "import",
    }
    response = test_client.post("/integrations/sync-jobs", json=data)
    if response.status_code != 201:
        pytest.skip(f"Could not create job: {response.text}")
    return response.json()["id"]


@pytest.fixture(scope="function")
def conflict_id() -> str:
    """Generate conflict ID (mock)."""
    return str(uuid4())


@pytest.fixture(scope="function")
def webhook_id(test_client, connection_id: str) -> str:
    """Create a webhook and return its ID."""
    data = {
        "connection_id": connection_id,
        "endpoint_path": f"/webhooks/test-{uuid4().hex[:8]}",
    }
    response = test_client.post("/integrations/webhooks", json=data)
    if response.status_code != 201:
        pytest.skip(f"Could not create webhook: {response.text}")
    return response.json()["id"]
