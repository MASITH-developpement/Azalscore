"""
Fixtures pour les tests du module Expenses.

Utilise les fixtures globales de app/conftest.py.
"""
import pytest
from uuid import uuid4


@pytest.fixture(scope="function")
def report_id(test_client) -> str:
    """Create an expense report and return its ID."""
    data = {
        "code": f"NDF-{uuid4().hex[:8]}",
        "title": "Test Expense Report",
    }
    response = test_client.post("/expenses/reports", json=data)
    if response.status_code != 201:
        pytest.skip(f"Could not create report: {response.text}")
    return response.json()["id"]


@pytest.fixture(scope="function")
def policy_id(test_client) -> str:
    """Create an expense policy and return its ID."""
    data = {
        "code": f"POL-{uuid4().hex[:8]}",
        "name": "Test Policy",
    }
    response = test_client.post("/expenses/policies", json=data)
    if response.status_code != 201:
        pytest.skip(f"Could not create policy: {response.text}")
    return response.json()["id"]


@pytest.fixture(scope="function")
def vehicle_id(test_client) -> str:
    """Create an employee vehicle and return its ID."""
    data = {
        "vehicle_type": "car_5cv",
        "registration_number": f"AB-{uuid4().hex[:3]}-CD",
    }
    response = test_client.post("/expenses/vehicles", json=data)
    if response.status_code != 201:
        pytest.skip(f"Could not create vehicle: {response.text}")
    return response.json()["id"]
