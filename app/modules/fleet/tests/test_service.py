"""
Tests Service - Module Fleet Management (GAP-062)

Tests de la logique metier.
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.modules.fleet.service import FleetService
from app.modules.fleet.models import (
    VehicleStatus, VehicleType, FuelType,
    ContractType, ContractStatus,
    MaintenanceType, MaintenanceStatus,
    DocumentType, IncidentType, IncidentStatus,
    AlertType, AlertSeverity
)
from app.modules.fleet.exceptions import (
    VehicleNotFoundError, VehicleDuplicateError, VehicleStateError,
    DriverNotFoundError, DriverLicenseExpiredError,
    MaintenanceStateError, MileageDecrementError
)


class TestVehicleService:
    """Tests du service vehicules."""

    def test_create_vehicle(self, fleet_service, sample_vehicle_data):
        """Test creation vehicule."""
        vehicle = fleet_service.create_vehicle(sample_vehicle_data)

        assert vehicle.id is not None
        assert vehicle.registration_number == "AB-123-CD"
        assert vehicle.make == "Renault"
        assert vehicle.status == VehicleStatus.AVAILABLE

    def test_create_vehicle_generates_code(self, fleet_service, sample_vehicle_data):
        """Test generation automatique du code."""
        sample_vehicle_data.pop("code", None)
        vehicle = fleet_service.create_vehicle(sample_vehicle_data)

        assert vehicle.code is not None
        assert vehicle.code.startswith("VEH-")

    def test_update_vehicle(self, fleet_service, sample_vehicle):
        """Test mise a jour vehicule."""
        updated = fleet_service.update_vehicle(sample_vehicle.id, {
            "color": "Red",
            "current_mileage": 20000
        })

        assert updated.color == "Red"
        assert updated.current_mileage == 20000

    def test_delete_vehicle(self, fleet_service, sample_vehicle):
        """Test suppression vehicule."""
        result = fleet_service.delete_vehicle(sample_vehicle.id)
        assert result == True

        with pytest.raises(VehicleNotFoundError):
            fleet_service.get_vehicle(sample_vehicle.id)

    def test_list_vehicles_pagination(self, fleet_service, sample_vehicle_data):
        """Test pagination liste vehicules."""
        # Creer plusieurs vehicules
        for i in range(15):
            data = sample_vehicle_data.copy()
            data["registration_number"] = f"AA-{100+i:03d}-BB"
            data["code"] = None
            fleet_service.create_vehicle(data)

        # Page 1
        vehicles, total = fleet_service.list_vehicles(page=1, page_size=10)
        assert len(vehicles) == 10
        assert total == 15

        # Page 2
        vehicles, total = fleet_service.list_vehicles(page=2, page_size=10)
        assert len(vehicles) == 5


class TestDriverService:
    """Tests du service conducteurs."""

    def test_create_driver(self, fleet_service, sample_driver_data):
        """Test creation conducteur."""
        driver = fleet_service.create_driver(sample_driver_data)

        assert driver.id is not None
        assert driver.first_name == "Jean"
        assert driver.last_name == "Dupont"

    def test_assign_driver_to_vehicle(self, fleet_service, sample_vehicle, sample_driver):
        """Test affectation conducteur."""
        vehicle = fleet_service.assign_driver(sample_vehicle.id, sample_driver.id)

        assert vehicle.assigned_driver_id == sample_driver.id
        assert vehicle.status == VehicleStatus.ASSIGNED

    def test_unassign_driver(self, fleet_service, sample_vehicle, sample_driver):
        """Test retrait affectation."""
        fleet_service.assign_driver(sample_vehicle.id, sample_driver.id)
        vehicle = fleet_service.unassign_driver(sample_vehicle.id)

        assert vehicle.assigned_driver_id is None
        assert vehicle.status == VehicleStatus.AVAILABLE

    def test_cannot_assign_driver_with_expired_license(
        self, fleet_service, sample_vehicle, sample_driver_data
    ):
        """Test refus affectation si permis expire."""
        sample_driver_data["license_expiry_date"] = date.today() - timedelta(days=1)
        driver = fleet_service.create_driver(sample_driver_data)

        with pytest.raises(DriverLicenseExpiredError):
            fleet_service.assign_driver(sample_vehicle.id, driver.id)


class TestMileageService:
    """Tests du service kilometrage."""

    def test_update_mileage(self, fleet_service, sample_vehicle):
        """Test mise a jour kilometrage."""
        vehicle = fleet_service.update_vehicle_mileage(
            sample_vehicle.id, 20000
        )

        assert vehicle.current_mileage == 20000

    def test_mileage_cannot_decrease(self, fleet_service, sample_vehicle):
        """Test kilometrage ne peut pas diminuer."""
        with pytest.raises(MileageDecrementError):
            fleet_service.update_vehicle_mileage(
                sample_vehicle.id, 10000  # Moins que 15000
            )

    def test_mileage_log_created(self, fleet_service, sample_vehicle):
        """Test creation log kilometrage."""
        fleet_service.update_vehicle_mileage(sample_vehicle.id, 20000)

        logs = fleet_service.mileage_repo.get_by_vehicle(sample_vehicle.id)
        assert len(logs) == 1
        assert logs[0].mileage == 20000
        assert logs[0].previous_mileage == sample_vehicle.current_mileage


class TestFuelService:
    """Tests du service carburant."""

    def test_add_fuel_entry(self, fleet_service, sample_vehicle, sample_fuel_entry_data):
        """Test ajout entree carburant."""
        sample_fuel_entry_data["vehicle_id"] = sample_vehicle.id
        entry = fleet_service.add_fuel_entry(sample_fuel_entry_data)

        assert entry.id is not None
        assert entry.quantity_liters == Decimal("45.50")
        assert entry.total_cost == Decimal("45.50") * Decimal("1.85")

    def test_fuel_entry_updates_mileage(self, fleet_service, sample_vehicle, sample_fuel_entry_data):
        """Test mise a jour kilometrage via carburant."""
        sample_fuel_entry_data["vehicle_id"] = sample_vehicle.id
        sample_fuel_entry_data["mileage_at_fill"] = 20000
        fleet_service.add_fuel_entry(sample_fuel_entry_data)

        vehicle = fleet_service.get_vehicle(sample_vehicle.id)
        assert vehicle.current_mileage == 20000

    def test_fuel_consumption_calculation(self, fleet_service, sample_vehicle):
        """Test calcul consommation."""
        # Premiere entree (reference)
        fleet_service.add_fuel_entry({
            "vehicle_id": sample_vehicle.id,
            "fill_date": date.today() - timedelta(days=10),
            "fuel_type": FuelType.DIESEL,
            "quantity_liters": Decimal("40"),
            "price_per_liter": Decimal("1.80"),
            "mileage_at_fill": 15000,
            "full_tank": True
        })

        # Deuxieme entree
        entry = fleet_service.add_fuel_entry({
            "vehicle_id": sample_vehicle.id,
            "fill_date": date.today(),
            "fuel_type": FuelType.DIESEL,
            "quantity_liters": Decimal("35"),
            "price_per_liter": Decimal("1.85"),
            "mileage_at_fill": 15500,  # 500 km parcourus
            "full_tank": True
        })

        # 35L pour 500km = 7L/100km
        assert entry.consumption_per_100km == Decimal("7.00")


class TestMaintenanceService:
    """Tests du service maintenance."""

    def test_create_maintenance(self, fleet_service, sample_vehicle, sample_maintenance_data):
        """Test creation maintenance."""
        sample_maintenance_data["vehicle_id"] = sample_vehicle.id
        maintenance = fleet_service.create_maintenance(sample_maintenance_data)

        assert maintenance.id is not None
        assert maintenance.status == MaintenanceStatus.SCHEDULED

    def test_complete_maintenance(self, fleet_service, sample_vehicle, sample_maintenance_data):
        """Test completion maintenance."""
        sample_maintenance_data["vehicle_id"] = sample_vehicle.id
        maintenance = fleet_service.create_maintenance(sample_maintenance_data)

        completed = fleet_service.complete_maintenance(maintenance.id, {
            "cost_parts": Decimal("100"),
            "cost_labor": Decimal("50"),
            "mileage_at_maintenance": 16000,
            "work_performed": "Vidange effectuee"
        })

        assert completed.status == MaintenanceStatus.COMPLETED
        assert completed.cost_total == Decimal("150")

    def test_maintenance_creates_cost_entry(self, fleet_service, sample_vehicle, sample_maintenance_data):
        """Test creation cout avec maintenance."""
        sample_maintenance_data["vehicle_id"] = sample_vehicle.id
        maintenance = fleet_service.create_maintenance(sample_maintenance_data)

        fleet_service.complete_maintenance(maintenance.id, {
            "cost_parts": Decimal("100"),
            "cost_labor": Decimal("50"),
        })

        costs = fleet_service.cost_repo.get_by_vehicle(sample_vehicle.id)
        assert len(costs) >= 1
        assert any(c.category == "maintenance" for c in costs)


class TestContractService:
    """Tests du service contrats."""

    def test_create_contract(self, fleet_service, sample_vehicle):
        """Test creation contrat."""
        contract = fleet_service.create_contract({
            "vehicle_id": sample_vehicle.id,
            "contract_type": ContractType.LEASING,
            "provider_name": "ALD Automotive",
            "start_date": date.today(),
            "end_date": date.today() + timedelta(days=365),
            "monthly_payment": Decimal("450")
        })

        assert contract.id is not None
        assert contract.status == ContractStatus.ACTIVE

    def test_expiring_contracts(self, fleet_service, sample_vehicle):
        """Test detection contrats expirant."""
        # Contrat expirant dans 20 jours
        fleet_service.create_contract({
            "vehicle_id": sample_vehicle.id,
            "contract_type": ContractType.LEASING,
            "provider_name": "ALD",
            "start_date": date.today() - timedelta(days=345),
            "end_date": date.today() + timedelta(days=20),
        })

        expiring = fleet_service.get_expiring_contracts(30)
        assert len(expiring) == 1


class TestIncidentService:
    """Tests du service incidents."""

    def test_create_incident(self, fleet_service, sample_vehicle):
        """Test creation incident."""
        incident = fleet_service.create_incident({
            "vehicle_id": sample_vehicle.id,
            "incident_type": IncidentType.ACCIDENT,
            "incident_date": datetime.now(),
            "description": "Accident parking",
            "repair_cost": Decimal("500")
        })

        assert incident.id is not None
        assert incident.status == IncidentStatus.REPORTED

    def test_create_fine(self, fleet_service, sample_vehicle, sample_driver):
        """Test creation amende."""
        fleet_service.assign_driver(sample_vehicle.id, sample_driver.id)

        fine = fleet_service.create_incident({
            "vehicle_id": sample_vehicle.id,
            "driver_id": sample_driver.id,
            "incident_type": IncidentType.SPEED_FINE,
            "incident_date": datetime.now(),
            "description": "Exces de vitesse 20km/h",
            "fine_amount": Decimal("135"),
            "fine_points": 1
        })

        assert fine.id is not None
        assert fine.fine_amount == Decimal("135")

    def test_pay_fine(self, fleet_service, sample_vehicle):
        """Test paiement amende."""
        fine = fleet_service.create_incident({
            "vehicle_id": sample_vehicle.id,
            "incident_type": IncidentType.PARKING_FINE,
            "incident_date": datetime.now(),
            "description": "Stationnement genant",
            "fine_amount": Decimal("35")
        })

        paid = fleet_service.pay_fine(fine.id)
        assert paid.fine_paid == True
        assert paid.fine_paid_date is not None


class TestAlertService:
    """Tests du service alertes."""

    def test_license_expiry_alert(self, fleet_service, sample_driver_data):
        """Test alerte permis expirant."""
        sample_driver_data["license_expiry_date"] = date.today() + timedelta(days=15)
        driver = fleet_service.create_driver(sample_driver_data)

        alerts = fleet_service.get_unresolved_alerts()
        license_alerts = [a for a in alerts if a.alert_type == AlertType.LICENSE_EXPIRY]
        assert len(license_alerts) >= 1

    def test_contract_expiry_alert(self, fleet_service, sample_vehicle):
        """Test alerte contrat expirant."""
        fleet_service.create_contract({
            "vehicle_id": sample_vehicle.id,
            "contract_type": ContractType.INSURANCE,
            "provider_name": "AXA",
            "start_date": date.today() - timedelta(days=335),
            "end_date": date.today() + timedelta(days=30),
        })

        alerts = fleet_service.get_unresolved_alerts()
        contract_alerts = [a for a in alerts if a.alert_type == AlertType.CONTRACT_EXPIRY]
        assert len(contract_alerts) >= 1

    def test_resolve_alert(self, fleet_service, sample_driver_data):
        """Test resolution alerte."""
        sample_driver_data["license_expiry_date"] = date.today() + timedelta(days=15)
        driver = fleet_service.create_driver(sample_driver_data)

        alerts = fleet_service.get_unresolved_alerts()
        if alerts:
            resolved = fleet_service.resolve_alert(alerts[0].id, "Permis renouvele")
            assert resolved.is_resolved == True


class TestTCOReport:
    """Tests du rapport TCO."""

    def test_tco_report(self, fleet_service, sample_vehicle):
        """Test generation rapport TCO."""
        # Ajouter des couts
        fleet_service.add_fuel_entry({
            "vehicle_id": sample_vehicle.id,
            "fill_date": date.today() - timedelta(days=5),
            "fuel_type": FuelType.DIESEL,
            "quantity_liters": Decimal("50"),
            "price_per_liter": Decimal("1.80"),
            "mileage_at_fill": 15500
        })

        report = fleet_service.get_tco_report(
            sample_vehicle.id,
            date.today() - timedelta(days=30),
            date.today()
        )

        assert report.vehicle_id == sample_vehicle.id
        assert report.fuel_cost > 0
        assert "fuel" in report.cost_breakdown


class TestDashboard:
    """Tests du dashboard."""

    def test_dashboard(self, fleet_service, sample_vehicle, sample_driver):
        """Test generation dashboard."""
        dashboard = fleet_service.get_dashboard()

        assert dashboard.total_vehicles >= 1
        assert dashboard.total_drivers >= 1
        assert "available" in dashboard.vehicles_by_status or "assigned" in dashboard.vehicles_by_status


class TestScheduledChecks:
    """Tests des verifications planifiees."""

    def test_run_scheduled_checks(self, fleet_service, sample_vehicle):
        """Test execution verifications planifiees."""
        # Creer contrat expirant
        fleet_service.create_contract({
            "vehicle_id": sample_vehicle.id,
            "contract_type": ContractType.INSURANCE,
            "provider_name": "AXA",
            "start_date": date.today() - timedelta(days=350),
            "end_date": date.today() + timedelta(days=15),
        })

        # Executer les checks
        fleet_service.run_scheduled_checks()

        # Verifier alertes creees
        alerts = fleet_service.get_unresolved_alerts()
        assert len(alerts) >= 1
