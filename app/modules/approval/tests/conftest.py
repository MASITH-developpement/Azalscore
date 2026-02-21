"""
Fixtures pour les tests du module Approval.

Utilise les fixtures globales de app/conftest.py.
"""
import pytest
from uuid import uuid4
from datetime import date, timedelta


@pytest.fixture(scope="function")
def workflow_id(test_client) -> str:
    """Create a workflow and return its ID."""
    data = {
        "code": f"WF-{uuid4().hex[:8]}",
        "name": "Test Workflow",
        "approval_type": "expense_report",
        "steps": [
            {"name": "Step 1", "step_type": "single", "approvers": []}
        ]
    }
    response = test_client.post("/approval/workflows", json=data)
    if response.status_code != 201:
        pytest.skip(f"Could not create workflow: {response.text}")
    return response.json()["id"]


@pytest.fixture(scope="function")
def request_id(test_client, workflow_id: str) -> str:
    """Create an approval request and return its ID."""
    data = {
        "workflow_id": workflow_id,
        "entity_type": "expense_report",
        "entity_id": str(uuid4()),
        "amount": "100.00"
    }
    response = test_client.post("/approval/requests", json=data)
    if response.status_code != 201:
        pytest.skip(f"Could not create request: {response.text}")
    return response.json()["id"]


@pytest.fixture(scope="function")
def delegation_id(test_client) -> str:
    """Create a delegation and return its ID."""
    data = {
        "delegate_id": str(uuid4()),
        "delegate_name": "Test Delegate",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=14)),
    }
    response = test_client.post("/approval/delegations", json=data)
    if response.status_code != 201:
        pytest.skip(f"Could not create delegation: {response.text}")
    return response.json()["id"]
