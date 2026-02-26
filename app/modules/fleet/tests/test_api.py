"""
Tests API - Module Fleet Management (GAP-062)

Tests des endpoints REST.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.modules.fleet.router import router
from app.modules.fleet.service import FleetService
from app.modules.fleet.models import (
    FleetVehicle, VehicleType, VehicleStatus, FuelType
)


# ============== Fixtures ==============

@pytest.fixture
def app():
    """Application FastAPI de test."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Client de test."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Utilisateur mocke."""
    user = MagicMock()
    user.id = uuid4()
    user.tenant_id = uuid4()
    return user


@pytest.fixture
def mock_service(db_session, mock_user):
    """Service mocke."""
    return FleetService(db_session, mock_user.tenant_id, mock_user.id)


# ============== Vehicle API Tests ==============

class TestVehicleAPI:
    """Tests des endpoints vehicules."""

    @patch('app.modules.fleet.router.get_fleet_service')
    @patch('app.modules.fleet.router.require_permission')
    def test_list_vehicles(self, mock_perm, mock_svc, client, mock_service):
        """Test liste des vehicules."""
        mock_svc.return_value = mock_service
        mock_perm.return_value = None

        response = client.get("/fleet/vehicles")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    @patch('app.modules.fleet.router.get_fleet_service')
    @patch('app.modules.fleet.router.require_permission')
    def test_list_vehicles_with_filters(self, mock_perm, mock_svc, client, mock_service):
        """Test liste avec filtres."""
        mock_svc.return_value = mock_service
        mock_perm.return_value = None

        response = client.get("/fleet/vehicles", params={
            "status": ["available"],
            "vehicle_type": ["car"],
            "search": "renault"
        })

        assert response.status_code == 200

    @patch('app.modules.fleet.router.get_fleet_service')
    @patch('app.modules.fleet.router.require_permission')
    def test_create_vehicle(self, mock_perm, mock_svc, client, mock_service):
        """Test creation vehicule."""
        mock_svc.return_value = mock_service
        mock_perm.return_value = None

        vehicle_data = {
            "registration_number": "XX-999-YY",
            "make": "Tesla",
            "model": "Model 3",
            "year": 2023,
            "vehicle_type": "electric",
            "fuel_type": "electric"
        }

        response = client.post("/fleet/vehicles", json=vehicle_data)

        assert response.status_code == 201
        data = response.json()
        assert data["registration_number"] == "XX-999-YY"
        assert data["make"] == "Tesla"

    @patch('app.modules.fleet.router.get_fleet_service')
    @patch('app.modules.fleet.router.require_permission')
    def test_create_vehicle_validation_error(self, mock_perm, mock_svc, client, mock_service):
        """Test erreur de validation."""
        mock_svc.return_value = mock_service
        mock_perm.return_value = None

        # Year invalide
        vehicle_data = {
            "registration_number": "XX-999-YY",
            "make": "Tesla",
            "model": "Model 3",
            "year": 1800,  # Invalide
        }

        response = client.post("/fleet/vehicles", json=vehicle_data)

        assert response.status_code == 422

    @patch('app.modules.fleet.router.get_fleet_service')
    @patch('app.modules.fleet.router.require_permission')
    def test_get_vehicle(self, mock_perm, mock_svc, client, mock_service, sample_vehicle):
        """Test recuperation vehicule."""
        mock_svc.return_value = mock_service
        mock_perm.return_value = None

        response = client.get(f"/fleet/vehicles/{sample_vehicle.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_vehicle.id)

    @patch('app.modules.fleet.router.get_fleet_service')
    @patch('app.modules.fleet.router.require_permission')
    def test_get_vehicle_not_found(self, mock_perm, mock_svc, client, mock_service):
        """Test vehicule non trouve."""
        mock_svc.return_value = mock_service
        mock_perm.return_value = None

        response = client.get(f"/fleet/vehicles/{uuid4()}")

        assert response.status_code == 404

    @patch('app.modules.fleet.router.get_fleet_service')
    @patch('app.modules.fleet.router.require_permission')
    def test_update_vehicle(self, mock_perm, mock_svc, client, mock_service, sample_vehicle):
        """Test mise a jour vehicule."""
        mock_svc.return_value = mock_service
        mock_perm.return_value = None

        response = client.put(
            f"/fleet/vehicles/{sample_vehicle.id}",
            json={"color": "Red", "current_mileage": 20000}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["color"] == "Red"
        assert data["current_mileage"] == 20000

    @patch('app.modules.fleet.router.get_fleet_service')
    @patch('app.modules.fleet.router.require_permission')
    def test_delete_vehicle(self, mock_perm, mock_svc, client, mock_service, sample_vehicle):
        """Test suppression vehicule."""
        mock_svc.return_value = mock_service
        mock_perm.return_value = None

        response = client.delete(f"/fleet/vehicles/{sample_vehicle.id}")

        assert response.status_code == 204


# ============== Driver API Tests ==============

class TestDriverAPI:
    """Tests des endpoints conducteurs."""

    @patch('app.modules.fleet.router.get_fleet_service')
    @patch('app.modules.fleet.router.require_permission')
    def test_list_drivers(self, mock_perm, mock_svc, client, mock_service):
        """Test liste conducteurs."""
        mock_svc.return_value = mock_service
        mock_perm.return_value = None

        response = client.get("/fleet/drivers")

        assert response.status_code == 200

    @patch('app.modules.fleet.router.get_fleet_service')
    @patch('app.modules.fleet.router.require_permission')
    def test_create_driver(self, mock_perm, mock_svc, client, mock_service):
        """Test creation conducteur."""
        mock_svc.return_value = mock_service
        mock_perm.return_value = None

        driver_data = {
            "first_name": "Marie",
            "last_name": "Martin",
            "email": "marie.martin@example.com",
            "license_number": "99ZZ88777"
        }

        response = client.post("/fleet/drivers", json=driver_data)

        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Marie"


# ============== Assignment Tests ==============

class TestAssignmentAPI:
    """Tests d'affectation conducteur/vehicule."""

    @patch('app.modules.fleet.router.get_fleet_service')
    @patch('app.modules.fleet.router.require_permission')
    def test_assign_driver(self, mock_perm, mock_svc, client, mock_service, sample_vehicle, sample_driver):
        """Test affectation conducteur."""
        mock_svc.return_value = mock_service
        mock_perm.return_value = None

        response = client.post(
            f"/fleet/vehicles/{sample_vehicle.id}/assign-driver",
            params={"driver_id": str(sample_driver.id)}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["assigned_driver_id"] == str(sample_driver.id)
        assert data["status"] == "assigned"

    @patch('app.modules.fleet.router.get_fleet_service')
    @patch('app.modules.fleet.router.require_permission')
    def test_unassign_driver(self, mock_perm, mock_svc, client, mock_service, sample_vehicle, sample_driver):
        """Test retrait affectation."""
        mock_svc.return_value = mock_service
        mock_perm.return_value = None

        # Assigner d'abord
        mock_service.assign_driver(sample_vehicle.id, sample_driver.id)

        response = client.post(f"/fleet/vehicles/{sample_vehicle.id}/unassign-driver")

        assert response.status_code == 200
        data = response.json()
        assert data["assigned_driver_id"] is None
        assert data["status"] == "available"


# ============== Mileage Tests ==============

class TestMileageAPI:
    """Tests de suivi kilometrique."""

    @patch('app.modules.fleet.router.get_fleet_service')
    @patch('app.modules.fleet.router.require_permission')
    def test_update_mileage(self, mock_perm, mock_svc, client, mock_service, sample_vehicle):
        """Test mise a jour kilometrage."""
        mock_svc.return_value = mock_service
        mock_perm.return_value = None

        response = client.post(
            f"/fleet/vehicles/{sample_vehicle.id}/mileage",
            json={"mileage": 20000, "source": "manual"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["current_mileage"] == 20000

    @patch('app.modules.fleet.router.get_fleet_service')
    @patch('app.modules.fleet.router.require_permission')
    def test_mileage_cannot_decrease(self, mock_perm, mock_svc, client, mock_service, sample_vehicle):
        """Test kilometrage ne peut pas diminuer."""
        mock_svc.return_value = mock_service
        mock_perm.return_value = None

        # sample_vehicle a 15000 km
        response = client.post(
            f"/fleet/vehicles/{sample_vehicle.id}/mileage",
            json={"mileage": 10000}  # Moins que 15000
        )

        assert response.status_code == 400


# ============== Dashboard Tests ==============

class TestDashboardAPI:
    """Tests du dashboard."""

    @patch('app.modules.fleet.router.get_fleet_service')
    @patch('app.modules.fleet.router.require_permission')
    def test_get_dashboard(self, mock_perm, mock_svc, client, mock_service, sample_vehicle):
        """Test recuperation dashboard."""
        mock_svc.return_value = mock_service
        mock_perm.return_value = None

        response = client.get("/fleet/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert "total_vehicles" in data
        assert "vehicles_by_status" in data
        assert "alerts_total" in data


# ============== TCO Report Tests ==============

class TestTCOAPI:
    """Tests des rapports TCO."""

    @patch('app.modules.fleet.router.get_fleet_service')
    @patch('app.modules.fleet.router.require_permission')
    def test_get_tco_report(self, mock_perm, mock_svc, client, mock_service, sample_vehicle):
        """Test rapport TCO."""
        mock_svc.return_value = mock_service
        mock_perm.return_value = None

        today = date.today()
        date_from = (today - timedelta(days=30)).isoformat()
        date_to = today.isoformat()

        response = client.get(
            f"/fleet/vehicles/{sample_vehicle.id}/tco",
            params={"date_from": date_from, "date_to": date_to}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_cost" in data
        assert "cost_per_km" in data
        assert "cost_breakdown" in data


# ============== Alert Tests ==============

class TestAlertAPI:
    """Tests des alertes."""

    @patch('app.modules.fleet.router.get_fleet_service')
    @patch('app.modules.fleet.router.require_permission')
    def test_list_alerts(self, mock_perm, mock_svc, client, mock_service):
        """Test liste alertes."""
        mock_svc.return_value = mock_service
        mock_perm.return_value = None

        response = client.get("/fleet/alerts")

        assert response.status_code == 200

    @patch('app.modules.fleet.router.get_fleet_service')
    @patch('app.modules.fleet.router.require_permission')
    def test_list_unresolved_alerts(self, mock_perm, mock_svc, client, mock_service):
        """Test alertes non resolues."""
        mock_svc.return_value = mock_service
        mock_perm.return_value = None

        response = client.get("/fleet/alerts/unresolved")

        assert response.status_code == 200
