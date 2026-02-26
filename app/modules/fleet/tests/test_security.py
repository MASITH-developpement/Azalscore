"""
Tests de securite - Module Fleet Management (GAP-062)

Tests d'isolation multi-tenant et controles d'acces.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from app.modules.fleet.models import (
    FleetVehicle, FleetDriver, VehicleType, VehicleStatus, FuelType
)
from app.modules.fleet.service import FleetService
from app.modules.fleet.repository import VehicleRepository, DriverRepository
from app.modules.fleet.exceptions import VehicleNotFoundError, DriverNotFoundError


class TestTenantIsolation:
    """Tests d'isolation des donnees entre tenants."""

    def test_vehicle_not_visible_to_other_tenant(
        self, db_session, tenant_id, other_tenant_id, sample_vehicle_data
    ):
        """Un vehicule cree par un tenant n'est pas visible par un autre."""
        # Creer vehicule avec tenant 1
        service1 = FleetService(db_session, tenant_id, uuid4())
        vehicle = service1.create_vehicle(sample_vehicle_data)

        # Essayer de recuperer avec tenant 2
        service2 = FleetService(db_session, other_tenant_id, uuid4())
        with pytest.raises(VehicleNotFoundError):
            service2.get_vehicle(vehicle.id)

    def test_vehicle_list_filtered_by_tenant(
        self, db_session, tenant_id, other_tenant_id, sample_vehicle_data
    ):
        """La liste des vehicules est filtree par tenant."""
        # Creer vehicules pour tenant 1
        service1 = FleetService(db_session, tenant_id, uuid4())
        v1 = service1.create_vehicle(sample_vehicle_data)

        sample_vehicle_data["registration_number"] = "EF-456-GH"
        sample_vehicle_data["code"] = None
        v2 = service1.create_vehicle(sample_vehicle_data)

        # Creer vehicule pour tenant 2
        service2 = FleetService(db_session, other_tenant_id, uuid4())
        sample_vehicle_data["registration_number"] = "IJ-789-KL"
        sample_vehicle_data["code"] = None
        v3 = service2.create_vehicle(sample_vehicle_data)

        # Verifier liste tenant 1
        vehicles1, count1 = service1.list_vehicles()
        assert count1 == 2
        assert all(v.tenant_id == tenant_id for v in vehicles1)

        # Verifier liste tenant 2
        vehicles2, count2 = service2.list_vehicles()
        assert count2 == 1
        assert all(v.tenant_id == other_tenant_id for v in vehicles2)

    def test_driver_not_visible_to_other_tenant(
        self, db_session, tenant_id, other_tenant_id, sample_driver_data
    ):
        """Un conducteur cree par un tenant n'est pas visible par un autre."""
        # Creer conducteur avec tenant 1
        service1 = FleetService(db_session, tenant_id, uuid4())
        driver = service1.create_driver(sample_driver_data)

        # Essayer de recuperer avec tenant 2
        service2 = FleetService(db_session, other_tenant_id, uuid4())
        with pytest.raises(DriverNotFoundError):
            service2.get_driver(driver.id)

    def test_cannot_assign_driver_from_different_tenant(
        self, db_session, tenant_id, other_tenant_id,
        sample_vehicle_data, sample_driver_data
    ):
        """Ne peut pas assigner un conducteur d'un autre tenant."""
        # Creer vehicule tenant 1
        service1 = FleetService(db_session, tenant_id, uuid4())
        vehicle = service1.create_vehicle(sample_vehicle_data)

        # Creer conducteur tenant 2
        service2 = FleetService(db_session, other_tenant_id, uuid4())
        driver = service2.create_driver(sample_driver_data)

        # Essayer d'assigner
        with pytest.raises(DriverNotFoundError):
            service1.assign_driver(vehicle.id, driver.id)

    def test_autocomplete_filtered_by_tenant(
        self, db_session, tenant_id, other_tenant_id, sample_vehicle_data
    ):
        """L'autocomplete est filtre par tenant."""
        # Creer vehicule tenant 1
        service1 = FleetService(db_session, tenant_id, uuid4())
        v1 = service1.create_vehicle(sample_vehicle_data)

        # Creer vehicule tenant 2 avec meme prefixe
        service2 = FleetService(db_session, other_tenant_id, uuid4())
        sample_vehicle_data["registration_number"] = "AB-999-ZZ"
        sample_vehicle_data["code"] = None
        v2 = service2.create_vehicle(sample_vehicle_data)

        # Autocomplete tenant 1
        results1 = service1.vehicle_repo.autocomplete("AB")
        assert len(results1) == 1
        assert results1[0]["id"] == str(v1.id)

        # Autocomplete tenant 2
        results2 = service2.vehicle_repo.autocomplete("AB")
        assert len(results2) == 1
        assert results2[0]["id"] == str(v2.id)


class TestSoftDelete:
    """Tests de soft delete."""

    def test_deleted_vehicle_not_in_list(self, fleet_service, sample_vehicle):
        """Un vehicule supprime n'apparait pas dans la liste."""
        # Verifier qu'il existe
        vehicles, count = fleet_service.list_vehicles()
        assert count == 1

        # Supprimer
        fleet_service.delete_vehicle(sample_vehicle.id)

        # Verifier qu'il n'apparait plus
        vehicles, count = fleet_service.list_vehicles()
        assert count == 0

    def test_deleted_vehicle_not_found_by_id(self, fleet_service, sample_vehicle):
        """Un vehicule supprime n'est pas trouve par ID."""
        fleet_service.delete_vehicle(sample_vehicle.id)

        with pytest.raises(VehicleNotFoundError):
            fleet_service.get_vehicle(sample_vehicle.id)

    def test_deleted_vehicle_has_metadata(self, db_session, fleet_service, sample_vehicle, user_id):
        """Un vehicule supprime a les metadonnees de suppression."""
        fleet_service.delete_vehicle(sample_vehicle.id)

        # Recuperer directement en BDD
        vehicle = db_session.query(FleetVehicle).filter(
            FleetVehicle.id == sample_vehicle.id
        ).first()

        assert vehicle is not None
        assert vehicle.is_deleted == True
        assert vehicle.deleted_at is not None
        assert vehicle.deleted_by == user_id
        assert vehicle.is_active == False


class TestAuditFields:
    """Tests des champs d'audit."""

    def test_vehicle_created_with_audit(self, fleet_service, sample_vehicle_data, user_id):
        """Un vehicule cree a les champs d'audit remplis."""
        vehicle = fleet_service.create_vehicle(sample_vehicle_data)

        assert vehicle.created_at is not None
        assert vehicle.created_by == user_id
        assert vehicle.version == 1

    def test_vehicle_updated_increments_version(self, fleet_service, sample_vehicle, user_id):
        """La mise a jour incremente la version."""
        initial_version = sample_vehicle.version

        fleet_service.update_vehicle(sample_vehicle.id, {"color": "Red"})

        # Recharger
        vehicle = fleet_service.get_vehicle(sample_vehicle.id)
        assert vehicle.version == initial_version + 1
        assert vehicle.updated_by == user_id
        assert vehicle.updated_at is not None

    def test_driver_created_with_audit(self, fleet_service, sample_driver_data, user_id):
        """Un conducteur cree a les champs d'audit."""
        driver = fleet_service.create_driver(sample_driver_data)

        assert driver.created_at is not None
        assert driver.created_by == user_id


class TestCodeValidation:
    """Tests de validation des codes."""

    def test_code_uppercase(self, fleet_service, sample_vehicle_data):
        """Le code est converti en majuscules."""
        sample_vehicle_data["code"] = "veh-001"
        vehicle = fleet_service.create_vehicle(sample_vehicle_data)

        assert vehicle.code == "VEH-001"

    def test_registration_formatted(self, fleet_service, sample_vehicle_data):
        """L'immatriculation est formatee."""
        sample_vehicle_data["registration_number"] = "ab 123 cd"
        vehicle = fleet_service.create_vehicle(sample_vehicle_data)

        assert vehicle.registration_number == "AB-123-CD"

    def test_duplicate_code_rejected(self, fleet_service, sample_vehicle):
        """Un code duplique est rejete."""
        from app.modules.fleet.exceptions import VehicleDuplicateError

        new_data = {
            "code": sample_vehicle.code,
            "registration_number": "ZZ-999-ZZ",
            "make": "Peugeot",
            "model": "308",
            "year": 2023,
        }

        with pytest.raises(VehicleDuplicateError):
            fleet_service.create_vehicle(new_data)

    def test_duplicate_registration_rejected(self, fleet_service, sample_vehicle):
        """Une immatriculation dupliquee est rejetee."""
        from app.modules.fleet.exceptions import VehicleDuplicateError

        new_data = {
            "registration_number": sample_vehicle.registration_number,
            "make": "Peugeot",
            "model": "308",
            "year": 2023,
        }

        with pytest.raises(VehicleDuplicateError):
            fleet_service.create_vehicle(new_data)
