"""
Tests d'intégration API - Module Expenses (GAP-084)

Tests des endpoints HTTP avec TestClient FastAPI.
"""
import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import date, timedelta


class TestExpenseReportAPI:
    """Tests API Expense Report."""

    def test_create_expense_report(self, test_client):
        """Créer une note de frais."""
        data = {
            "code": f"NDF-2026-{uuid4().hex[:6]}",
            "title": "Déplacement client Paris",
            "description": "Frais de déplacement pour réunion client",
            "period_start": str(date.today() - timedelta(days=7)),
            "period_end": str(date.today()),
            "mission_reference": "MISSION-001"
        }
        response = test_client.post("/expenses/reports", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["code"].startswith("NDF-2026")
        assert result["status"] == "draft"

    def test_list_expense_reports(self, test_client):
        """Lister les notes de frais."""
        response = test_client.get("/expenses/reports")
        assert response.status_code == 200
        result = response.json()
        assert "items" in result
        assert "total" in result

    def test_get_expense_report_by_id(self, test_client, report_id: str):
        """Récupérer une note de frais par ID."""
        response = test_client.get(f"/expenses/reports/{report_id}")
        assert response.status_code == 200

    def test_add_expense_line(self, test_client, report_id: str):
        """Ajouter une ligne de dépense."""
        data = {
            "category": "restaurant",
            "description": "Déjeuner client",
            "expense_date": str(date.today()),
            "amount": "45.00",
            "vat_rate": "10.00",
            "payment_method": "company_card",
            "guests": [{"name": "Jean Dupont", "company": "ACME Corp"}],
            "guest_count": 1
        }
        response = test_client.post(f"/expenses/reports/{report_id}/lines", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["category"] == "restaurant"
        assert float(result["amount"]) == 45.00

    def test_add_mileage_line(self, test_client, report_id: str):
        """Ajouter une ligne kilométrique."""
        data = {
            "category": "mileage",
            "description": "Trajet Paris - Lyon",
            "expense_date": str(date.today()),
            "mileage_departure": "Paris",
            "mileage_arrival": "Lyon",
            "mileage_distance_km": "465.00",
            "mileage_is_round_trip": False,
            "vehicle_type": "car_5cv",
            "mileage_purpose": "Réunion client"
        }
        response = test_client.post(f"/expenses/reports/{report_id}/lines", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["category"] == "mileage"
        assert float(result["mileage_distance_km"]) == 465.00

    def test_submit_expense_report(self, test_client, report_id: str):
        """Soumettre une note de frais."""
        response = test_client.post(f"/expenses/reports/{report_id}/submit")
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "submitted"
        assert result["submitted_at"] is not None

    def test_approve_expense_report(self, test_client, report_id: str):
        """Approuver une note de frais."""
        response = test_client.post(f"/expenses/reports/{report_id}/approve")
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "approved"

    def test_reject_expense_report(self, test_client, report_id: str):
        """Rejeter une note de frais."""
        data = {"reason": "Justificatifs manquants"}
        response = test_client.post(f"/expenses/reports/{report_id}/reject", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "rejected"

    def test_get_totals(self, test_client, report_id: str):
        """Récupérer les totaux d'une note de frais."""
        response = test_client.get(f"/expenses/reports/{report_id}")
        assert response.status_code == 200
        result = response.json()
        assert "total_amount" in result
        assert "total_vat" in result
        assert "total_reimbursable" in result


class TestExpensePolicyAPI:
    """Tests API Expense Policy."""

    def test_create_policy(self, test_client):
        """Créer une politique de dépenses."""
        data = {
            "code": f"POL-STD-{uuid4().hex[:6]}",
            "name": "Politique standard",
            "description": "Politique de dépenses standard",
            "is_default": True,
            "single_expense_limit": "500.00",
            "daily_limit": "200.00",
            "monthly_limit": "2000.00",
            "meal_solo_limit": "20.20",
            "meal_business_limit": "50.00",
            "category_limits": {
                "hotel": 150,
                "restaurant": 50
            }
        }
        response = test_client.post("/expenses/policies", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["code"].startswith("POL-STD")
        assert result["is_default"] is True

    def test_list_policies(self, test_client):
        """Lister les politiques."""
        response = test_client.get("/expenses/policies")
        assert response.status_code == 200

    def test_get_default_policy(self, test_client):
        """Récupérer la politique par défaut."""
        response = test_client.get("/expenses/policies/default")
        assert response.status_code in [200, 404]

    def test_validate_expense(self, test_client, policy_id: str):
        """Valider une dépense contre une politique."""
        data = {
            "category": "restaurant",
            "amount": "75.00"
        }
        response = test_client.post(f"/expenses/policies/{policy_id}/validate", json=data)
        assert response.status_code == 200
        result = response.json()
        assert "is_compliant" in result


class TestMileageRateAPI:
    """Tests API Mileage Rates."""

    def test_create_mileage_rate(self, test_client):
        """Créer un barème kilométrique."""
        data = {
            "year": 2026,
            "vehicle_type": "car_5cv",
            "rate_up_to_5000": "0.636",
            "rate_5001_to_20000": "0.357",
            "fixed_5001_to_20000": "1395.00",
            "rate_above_20000": "0.234",
            "source": "URSSAF 2026"
        }
        response = test_client.post("/expenses/mileage-rates", json=data)
        assert response.status_code == 201

    def test_list_mileage_rates(self, test_client):
        """Lister les barèmes."""
        response = test_client.get("/expenses/mileage-rates")
        assert response.status_code == 200

    def test_get_rate_for_vehicle(self, test_client):
        """Récupérer le taux pour un véhicule."""
        response = test_client.get("/expenses/mileage-rates?year=2026&vehicle_type=car_5cv")
        assert response.status_code == 200

    def test_calculate_mileage(self, test_client):
        """Calculer les indemnités kilométriques."""
        params = {
            "vehicle_type": "car_5cv",
            "distance_km": 1500,
            "annual_total_km": 8000
        }
        response = test_client.get("/expenses/mileage-rates/calculate", params=params)
        assert response.status_code == 200
        result = response.json()
        assert "amount" in result


class TestEmployeeVehicleAPI:
    """Tests API Employee Vehicle."""

    def test_create_vehicle(self, test_client):
        """Créer un véhicule employé."""
        data = {
            "vehicle_type": "car_5cv",
            "registration_number": f"AB-{uuid4().hex[:3]}-CD",
            "fiscal_power": 5,
            "make": "Renault",
            "model": "Clio",
            "is_default": True
        }
        response = test_client.post("/expenses/vehicles", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["registration_number"].startswith("AB-")

    def test_list_my_vehicles(self, test_client):
        """Lister mes véhicules."""
        response = test_client.get("/expenses/vehicles")
        assert response.status_code == 200

    def test_get_annual_mileage(self, test_client, vehicle_id: str):
        """Récupérer le kilométrage annuel."""
        response = test_client.get(f"/expenses/vehicles/{vehicle_id}/mileage?year=2026")
        assert response.status_code == 200


class TestExpenseExport:
    """Tests export comptable."""

    def test_export_to_accounting(self, test_client, report_id: str):
        """Exporter vers la comptabilité."""
        response = test_client.post(f"/expenses/reports/{report_id}/export")
        assert response.status_code in [200, 400]  # 400 si pas approuvé

    def test_bulk_export(self, test_client):
        """Export en masse."""
        data = {
            "report_ids": [str(uuid4())],
            "format": "csv"
        }
        response = test_client.post("/expenses/reports/export", json=data)
        assert response.status_code in [200, 400]
