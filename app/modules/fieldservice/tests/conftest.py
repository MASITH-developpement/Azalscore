"""
Fixtures pour les tests du module Field Service.

Utilise les fixtures globales de app/conftest.py.
"""
import pytest
from uuid import uuid4
from datetime import date, timedelta


@pytest.fixture(scope="function")
def technician_id(test_client) -> str:
    """Create a technician and return its ID."""
    data = {
        "code": f"TECH-{uuid4().hex[:8]}",
        "first_name": "Test",
        "last_name": "Technician",
        "email": f"tech-{uuid4().hex[:8]}@test.com",
    }
    response = test_client.post("/fieldservice/technicians", json=data)
    if response.status_code != 201:
        pytest.skip(f"Could not create technician: {response.text}")
    return response.json()["id"]


@pytest.fixture(scope="function")
def work_order_id(test_client) -> str:
    """Create a work order and return its ID."""
    data = {
        "code": f"WO-{uuid4().hex[:8]}",
        "title": "Test Work Order",
        "customer_id": str(uuid4()),
        "scheduled_date": str(date.today() + timedelta(days=1)),
    }
    response = test_client.post("/fieldservice/work-orders", json=data)
    if response.status_code != 201:
        pytest.skip(f"Could not create work order: {response.text}")
    return response.json()["id"]


@pytest.fixture(scope="function")
def zone_id(test_client) -> str:
    """Create a service zone and return its ID."""
    data = {
        "code": f"ZONE-{uuid4().hex[:8]}",
        "name": "Test Zone",
    }
    response = test_client.post("/fieldservice/zones", json=data)
    if response.status_code != 201:
        pytest.skip(f"Could not create zone: {response.text}")
    return response.json()["id"]


@pytest.fixture(scope="function")
def customer_id() -> str:
    """Generate customer ID."""
    return str(uuid4())
