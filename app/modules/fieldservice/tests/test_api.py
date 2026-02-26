"""
Tests d'intégration API - Module Field Service (GAP-081)

Tests des endpoints HTTP avec TestClient FastAPI.
"""
import pytest
from uuid import uuid4
from datetime import date, datetime, timedelta


class TestTechnicianAPI:
    """Tests API Technician."""

    def test_create_technician(self, test_client):
        """Créer un technicien."""
        data = {
            "code": f"TECH-{uuid4().hex[:6]}",
            "first_name": "Jean",
            "last_name": "Dupont",
            "email": f"jean.dupont-{uuid4().hex[:6]}@example.com",
            "phone": "+33612345678",
            "status": "available",
            "max_daily_work_orders": 8,
            "hourly_rate": "45.00"
        }
        response = test_client.post("/fieldservice/technicians", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["code"].startswith("TECH-")
        assert result["first_name"] == "Jean"

    def test_list_technicians(self, test_client):
        """Lister les techniciens."""
        response = test_client.get("/fieldservice/technicians")
        assert response.status_code == 200
        result = response.json()
        assert "items" in result
        assert "total" in result

    def test_update_technician_status(self, test_client, technician_id: str):
        """Mettre à jour le statut d'un technicien."""
        data = {"status": "en_route"}
        response = test_client.patch(f"/fieldservice/technicians/{technician_id}", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "en_route"

    def test_update_technician_location(self, test_client, technician_id: str):
        """Mettre à jour la position GPS d'un technicien."""
        data = {"latitude": "48.8566", "longitude": "2.3522"}
        response = test_client.post(f"/fieldservice/technicians/{technician_id}/location", json=data)
        assert response.status_code == 200

    def test_get_available_technicians(self, test_client):
        """Récupérer les techniciens disponibles."""
        response = test_client.get("/fieldservice/technicians?status=available")
        assert response.status_code == 200


class TestWorkOrderAPI:
    """Tests API Work Order."""

    def test_create_work_order(self, test_client):
        """Créer un ordre de travail."""
        data = {
            "code": f"WO-2026-{uuid4().hex[:6]}",
            "title": "Installation climatisation",
            "description": "Installation d'un système de climatisation",
            "work_order_type": "installation",
            "priority": "medium",
            "customer_id": str(uuid4()),
            "customer_name": "ACME Corp",
            "scheduled_date": str(date.today() + timedelta(days=1)),
            "estimated_duration_minutes": 120
        }
        response = test_client.post("/fieldservice/work-orders", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["code"].startswith("WO-2026")
        assert result["status"] == "draft"

    def test_list_work_orders(self, test_client):
        """Lister les ordres de travail."""
        response = test_client.get("/fieldservice/work-orders")
        assert response.status_code == 200
        result = response.json()
        assert "items" in result

    def test_assign_technician(self, test_client, work_order_id: str, technician_id: str):
        """Assigner un technicien à un ordre de travail."""
        data = {"technician_id": technician_id}
        response = test_client.patch(f"/fieldservice/work-orders/{work_order_id}", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["technician_id"] == technician_id

    def test_schedule_work_order(self, test_client, work_order_id: str):
        """Planifier un ordre de travail."""
        response = test_client.post(f"/fieldservice/work-orders/{work_order_id}/schedule")
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "scheduled"

    def test_dispatch_work_order(self, test_client, work_order_id: str):
        """Dispatcher un ordre de travail."""
        response = test_client.post(f"/fieldservice/work-orders/{work_order_id}/dispatch")
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "dispatched"

    def test_start_work_order(self, test_client, work_order_id: str):
        """Démarrer un ordre de travail."""
        response = test_client.post(f"/fieldservice/work-orders/{work_order_id}/start")
        assert response.status_code == 200
        result = response.json()
        assert result["actual_start_time"] is not None

    def test_complete_work_order(self, test_client, work_order_id: str):
        """Terminer un ordre de travail."""
        data = {"resolution_notes": "Installation terminée avec succès"}
        response = test_client.post(f"/fieldservice/work-orders/{work_order_id}/complete", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "completed"

    def test_filter_by_status(self, test_client):
        """Filtrer par statut."""
        response = test_client.get("/fieldservice/work-orders?status=draft")
        assert response.status_code == 200

    def test_filter_by_date(self, test_client):
        """Filtrer par date."""
        today = date.today().isoformat()
        response = test_client.get(f"/fieldservice/work-orders?date_from={today}")
        assert response.status_code == 200


class TestServiceZoneAPI:
    """Tests API Service Zone."""

    def test_create_zone(self, test_client):
        """Créer une zone de service."""
        data = {
            "code": f"ZONE-{uuid4().hex[:6]}",
            "name": "Île-de-France",
            "description": "Zone couvrant l'Île-de-France",
            "center_lat": "48.8566",
            "center_lng": "2.3522",
            "radius_km": "50.00",
            "travel_time_minutes": 45
        }
        response = test_client.post("/fieldservice/zones", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["code"].startswith("ZONE-")

    def test_list_zones(self, test_client):
        """Lister les zones."""
        response = test_client.get("/fieldservice/zones")
        assert response.status_code == 200

    def test_assign_technicians_to_zone(self, test_client, zone_id: str):
        """Assigner des techniciens à une zone."""
        data = {"assigned_technicians": [str(uuid4()), str(uuid4())]}
        response = test_client.patch(f"/fieldservice/zones/{zone_id}", json=data)
        assert response.status_code == 200


class TestCustomerSiteAPI:
    """Tests API Customer Site."""

    def test_create_site(self, test_client):
        """Créer un site client."""
        data = {
            "code": f"SITE-{uuid4().hex[:6]}",
            "name": "Siège ACME",
            "customer_id": str(uuid4()),
            "customer_name": "ACME Corp",
            "address_line1": "123 Rue de la Paix",
            "city": "Paris",
            "postal_code": "75001",
            "country": "France",
            "contact_name": "Marie Martin",
            "contact_phone": "+33145678901"
        }
        response = test_client.post("/fieldservice/sites", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["code"].startswith("SITE-")

    def test_list_sites_by_customer(self, test_client, customer_id: str):
        """Lister les sites d'un client."""
        response = test_client.get(f"/fieldservice/sites?customer_id={customer_id}")
        assert response.status_code == 200


class TestSkillAPI:
    """Tests API Skill."""

    def test_create_skill(self, test_client):
        """Créer une compétence."""
        data = {
            "code": f"SKILL-{uuid4().hex[:6]}",
            "name": "Climatisation",
            "category": "HVAC",
            "certification_required": True,
            "certification_validity_days": 365
        }
        response = test_client.post("/fieldservice/skills", json=data)
        assert response.status_code == 201

    def test_list_skills(self, test_client):
        """Lister les compétences."""
        response = test_client.get("/fieldservice/skills")
        assert response.status_code == 200
