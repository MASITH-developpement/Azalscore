"""
Configuration des tests - Module Fleet Management
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.modules.fleet.models import (
    FleetVehicle, FleetDriver, FleetContract, FleetMileageLog,
    FleetFuelEntry, FleetMaintenance, FleetDocument, FleetIncident,
    FleetCost, FleetAlert,
    VehicleType, VehicleStatus, FuelType, ContractType, ContractStatus,
    MaintenanceType, MaintenanceStatus, DocumentType, IncidentType,
    AlertType, AlertSeverity
)
from app.modules.fleet.service import FleetService
from app.modules.fleet.repository import (
    VehicleRepository, DriverRepository, ContractRepository,
    MaintenanceRepository, FuelEntryRepository
)


# ============== Database Fixtures ==============

@pytest.fixture(scope="function")
def db_engine():
    """Cree un moteur de base de donnees SQLite en memoire."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Cree une session de base de donnees."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ============== Tenant/User Fixtures ==============

@pytest.fixture
def tenant_id():
    """ID du tenant de test."""
    return uuid4()


@pytest.fixture
def user_id():
    """ID de l'utilisateur de test."""
    return uuid4()


@pytest.fixture
def other_tenant_id():
    """ID d'un autre tenant pour tests d'isolation."""
    return uuid4()


# ============== Service Fixtures ==============

@pytest.fixture
def fleet_service(db_session, tenant_id, user_id):
    """Service Fleet pour les tests."""
    return FleetService(db_session, tenant_id, user_id)


@pytest.fixture
def vehicle_repo(db_session, tenant_id):
    """Repository vehicules."""
    return VehicleRepository(db_session, tenant_id)


@pytest.fixture
def driver_repo(db_session, tenant_id):
    """Repository conducteurs."""
    return DriverRepository(db_session, tenant_id)


# ============== Data Fixtures ==============

@pytest.fixture
def sample_vehicle_data():
    """Donnees d'exemple pour un vehicule."""
    return {
        "registration_number": "AB-123-CD",
        "vin": "1HGBH41JXMN109186",
        "make": "Renault",
        "model": "Clio",
        "year": 2022,
        "vehicle_type": VehicleType.CAR,
        "fuel_type": FuelType.DIESEL,
        "color": "Blue",
        "seats": 5,
        "doors": 5,
        "power_hp": 100,
        "fiscal_power": 5,
        "transmission": "manual",
        "initial_mileage": 0,
        "current_mileage": 15000,
        "fuel_capacity_liters": 45,
        "purchase_date": date(2022, 1, 15),
        "purchase_price": Decimal("18000.00"),
        "current_value": Decimal("15000.00"),
    }


@pytest.fixture
def sample_driver_data():
    """Donnees d'exemple pour un conducteur."""
    return {
        "first_name": "Jean",
        "last_name": "Dupont",
        "email": "jean.dupont@example.com",
        "phone": "+33612345678",
        "license_number": "12AB34567",
        "license_type": "B",
        "license_expiry_date": date.today() + timedelta(days=365),
        "department": "Commercial",
    }


@pytest.fixture
def sample_contract_data(sample_vehicle):
    """Donnees d'exemple pour un contrat."""
    return {
        "vehicle_id": sample_vehicle.id,
        "contract_type": ContractType.LEASING,
        "provider_name": "ALD Automotive",
        "start_date": date.today() - timedelta(days=180),
        "end_date": date.today() + timedelta(days=365),
        "duration_months": 36,
        "monthly_payment": Decimal("450.00"),
        "mileage_limit_annual": 30000,
    }


@pytest.fixture
def sample_maintenance_data(sample_vehicle):
    """Donnees d'exemple pour une maintenance."""
    return {
        "vehicle_id": sample_vehicle.id,
        "maintenance_type": MaintenanceType.OIL_CHANGE,
        "title": "Vidange 30000km",
        "description": "Vidange huile et filtre",
        "scheduled_date": date.today() + timedelta(days=7),
        "provider_name": "Speedy",
    }


@pytest.fixture
def sample_fuel_entry_data(sample_vehicle):
    """Donnees d'exemple pour une entree carburant."""
    return {
        "vehicle_id": sample_vehicle.id,
        "fill_date": date.today(),
        "fuel_type": FuelType.DIESEL,
        "quantity_liters": Decimal("45.50"),
        "price_per_liter": Decimal("1.85"),
        "mileage_at_fill": 15500,
        "full_tank": True,
        "station_name": "TotalEnergies",
    }


# ============== Entity Fixtures ==============

@pytest.fixture
def sample_vehicle(fleet_service, sample_vehicle_data):
    """Cree un vehicule de test."""
    return fleet_service.create_vehicle(sample_vehicle_data)


@pytest.fixture
def sample_driver(fleet_service, sample_driver_data):
    """Cree un conducteur de test."""
    return fleet_service.create_driver(sample_driver_data)


@pytest.fixture
def sample_contract(fleet_service, sample_vehicle, sample_contract_data):
    """Cree un contrat de test."""
    sample_contract_data["vehicle_id"] = sample_vehicle.id
    return fleet_service.create_contract(sample_contract_data)


@pytest.fixture
def sample_maintenance(fleet_service, sample_vehicle, sample_maintenance_data):
    """Cree une maintenance de test."""
    sample_maintenance_data["vehicle_id"] = sample_vehicle.id
    return fleet_service.create_maintenance(sample_maintenance_data)


@pytest.fixture
def sample_fuel_entry(fleet_service, sample_vehicle, sample_fuel_entry_data):
    """Cree une entree carburant de test."""
    sample_fuel_entry_data["vehicle_id"] = sample_vehicle.id
    return fleet_service.add_fuel_entry(sample_fuel_entry_data)
