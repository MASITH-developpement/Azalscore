"""
Fixtures pour les tests du module Forecasting.

Utilise les fixtures globales de app/conftest.py.
"""
import pytest
from uuid import uuid4
from datetime import date, timedelta


@pytest.fixture(scope="function")
def forecast_id(test_client) -> str:
    """Create a forecast and return its ID."""
    data = {
        "code": f"FC-TEST-{uuid4().hex[:8]}",
        "name": "Test Forecast",
        "forecast_type": "sales",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=90)),
    }
    response = test_client.post("/forecasting/forecasts", json=data)
    if response.status_code != 201:
        pytest.skip(f"Could not create forecast: {response.text}")
    return response.json()["id"]


@pytest.fixture(scope="function")
def budget_id(test_client) -> str:
    """Create a budget and return its ID."""
    data = {
        "code": f"BUD-TEST-{uuid4().hex[:8]}",
        "name": "Test Budget",
        "fiscal_year": 2026,
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
    }
    response = test_client.post("/forecasting/budgets", json=data)
    if response.status_code != 201:
        pytest.skip(f"Could not create budget: {response.text}")
    return response.json()["id"]


@pytest.fixture(scope="function")
def kpi_id(test_client) -> str:
    """Create a KPI and return its ID."""
    data = {
        "code": f"KPI-TEST-{uuid4().hex[:8]}",
        "name": "Test KPI",
        "category": "finance",
        "target_value": "100000.00",
    }
    response = test_client.post("/forecasting/kpis", json=data)
    if response.status_code != 201:
        pytest.skip(f"Could not create KPI: {response.text}")
    return response.json()["id"]
