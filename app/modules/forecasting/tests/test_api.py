"""
Tests d'intégration API - Module Forecasting (GAP-076)

Tests des endpoints HTTP avec TestClient FastAPI.
"""
import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import date, timedelta


class TestForecastAPI:
    """Tests API Forecast."""

    def test_create_forecast(self, test_client):
        """Créer une prévision."""
        data = {
            "code": f"FC-2026-{uuid4().hex[:6]}",
            "name": "Prévision CA Q1 2026",
            "description": "Prévision des ventes Q1",
            "forecast_type": "sales",
            "method": "moving_average",
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=90)),
            "granularity": "monthly"
        }
        response = test_client.post("/forecasting/forecasts", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["code"].startswith("FC-2026")
        assert result["status"] == "draft"

    def test_list_forecasts(self, test_client):
        """Lister les prévisions."""
        response = test_client.get("/forecasting/forecasts")
        assert response.status_code == 200
        result = response.json()
        assert "items" in result
        assert "total" in result

    def test_get_forecast_by_id(self, test_client, forecast_id: str):
        """Récupérer une prévision par ID."""
        response = test_client.get(f"/forecasting/forecasts/{forecast_id}")
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == forecast_id

    def test_update_forecast(self, test_client, forecast_id: str):
        """Mettre à jour une prévision."""
        data = {"name": "Prévision mise à jour"}
        response = test_client.patch(f"/forecasting/forecasts/{forecast_id}", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Prévision mise à jour"

    def test_activate_forecast(self, test_client, forecast_id: str):
        """Activer une prévision."""
        response = test_client.post(f"/forecasting/forecasts/{forecast_id}/activate")
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "active"

    def test_delete_forecast(self, test_client):
        """Supprimer une prévision (soft delete)."""
        # Créer d'abord
        data = {
            "code": f"FC-DEL-{uuid4().hex[:6]}",
            "name": "À supprimer",
            "forecast_type": "sales",
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=30)),
        }
        create_resp = test_client.post("/forecasting/forecasts", json=data)
        forecast_id = create_resp.json()["id"]

        # Supprimer
        response = test_client.delete(f"/forecasting/forecasts/{forecast_id}")
        assert response.status_code == 204

        # Vérifier qu'il n'est plus visible
        get_resp = test_client.get(f"/forecasting/forecasts/{forecast_id}")
        assert get_resp.status_code == 404


class TestBudgetAPI:
    """Tests API Budget."""

    def test_create_budget(self, test_client):
        """Créer un budget."""
        data = {
            "code": f"BUD-{uuid4().hex[:6]}",
            "name": "Budget 2026",
            "fiscal_year": 2026,
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "granularity": "monthly",
            "total_budget": "1000000.00"
        }
        response = test_client.post("/forecasting/budgets", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["code"].startswith("BUD-")
        assert result["fiscal_year"] == 2026

    def test_list_budgets(self, test_client):
        """Lister les budgets."""
        response = test_client.get("/forecasting/budgets")
        assert response.status_code == 200
        result = response.json()
        assert "items" in result

    def test_submit_budget(self, test_client, budget_id: str):
        """Soumettre un budget pour approbation."""
        response = test_client.post(f"/forecasting/budgets/{budget_id}/submit")
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "submitted"


class TestKPIAPI:
    """Tests API KPI."""

    def test_create_kpi(self, test_client):
        """Créer un KPI."""
        data = {
            "code": f"KPI-CA-{uuid4().hex[:6]}",
            "name": "Chiffre d'affaires mensuel",
            "category": "finance",
            "unit": "EUR",
            "target_value": "100000.00",
            "green_threshold": "90000.00",
            "amber_threshold": "70000.00",
            "red_threshold": "50000.00"
        }
        response = test_client.post("/forecasting/kpis", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["code"].startswith("KPI-CA-")

    def test_list_kpis(self, test_client):
        """Lister les KPIs."""
        response = test_client.get("/forecasting/kpis")
        assert response.status_code == 200

    def test_update_kpi_value(self, test_client, kpi_id: str):
        """Mettre à jour la valeur d'un KPI."""
        data = {"current_value": "85000.00"}
        response = test_client.patch(f"/forecasting/kpis/{kpi_id}", json=data)
        assert response.status_code == 200

    def test_kpi_dashboard(self, test_client):
        """Récupérer le dashboard KPI."""
        response = test_client.get("/forecasting/kpis/dashboard")
        assert response.status_code == 200
        result = response.json()
        assert "total_kpis" in result


class TestAutocomplete:
    """Tests autocomplete."""

    def test_forecast_autocomplete(self, test_client):
        """Autocomplete prévisions."""
        response = test_client.get("/forecasting/forecasts/autocomplete?prefix=FC")
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

    def test_budget_autocomplete(self, test_client):
        """Autocomplete budgets."""
        response = test_client.get("/forecasting/budgets/autocomplete?prefix=BUD")
        assert response.status_code == 200

    def test_kpi_autocomplete(self, test_client):
        """Autocomplete KPIs."""
        response = test_client.get("/forecasting/kpis/autocomplete?prefix=KPI")
        assert response.status_code == 200
