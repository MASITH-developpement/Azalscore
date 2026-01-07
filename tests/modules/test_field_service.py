"""
Tests MODULE 17 - Field Service
================================
Tests unitaires pour la gestion des interventions terrain.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from app.modules.field_service.models import (
    ServiceZone, Technician, Vehicle, InterventionTemplate,
    Intervention, InterventionHistory, FSTimeEntry as TimeEntry, Route, Expense, ServiceContract,
    TechnicianStatus, InterventionStatus, InterventionPriority, InterventionType
)
from app.modules.field_service.schemas import (
    ZoneCreate, ZoneUpdate,
    TechnicianCreate, TechnicianUpdate,
    VehicleCreate,
    TemplateCreate,
    InterventionCreate, InterventionUpdate, InterventionAssign, InterventionComplete,
    TimeEntryCreate,
    RouteCreate,
    ExpenseCreate,
    ContractCreate
)
from app.modules.field_service.service import FieldServiceService


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock de la session DB."""
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    return db


@pytest.fixture
def service(mock_db):
    """Service Field Service avec mock DB."""
    return FieldServiceService(mock_db, "test-tenant")


@pytest.fixture
def sample_zone():
    """Zone exemple."""
    zone = MagicMock(spec=ServiceZone)
    zone.id = 1
    zone.tenant_id = "test-tenant"
    zone.code = "PARIS"
    zone.name = "Région Paris"
    zone.is_active = True
    return zone


@pytest.fixture
def sample_technician():
    """Technicien exemple."""
    tech = MagicMock(spec=Technician)
    tech.id = 1
    tech.tenant_id = "test-tenant"
    tech.user_id = 100
    tech.first_name = "Jean"
    tech.last_name = "Dupont"
    tech.status = TechnicianStatus.AVAILABLE
    tech.total_interventions = 50
    tech.completed_interventions = 45
    tech.avg_rating = Decimal("4.5")
    tech.total_km_traveled = Decimal("1500")
    tech.is_active = True
    return tech


@pytest.fixture
def sample_vehicle():
    """Véhicule exemple."""
    vehicle = MagicMock(spec=Vehicle)
    vehicle.id = 1
    vehicle.tenant_id = "test-tenant"
    vehicle.registration = "AB-123-CD"
    vehicle.make = "Renault"
    vehicle.model = "Kangoo"
    vehicle.current_odometer = 45000
    vehicle.is_active = True
    return vehicle


@pytest.fixture
def sample_intervention():
    """Intervention exemple."""
    intervention = MagicMock(spec=Intervention)
    intervention.id = 1
    intervention.tenant_id = "test-tenant"
    intervention.reference = "INT-202401-ABC123"
    intervention.title = "Maintenance préventive"
    intervention.status = InterventionStatus.SCHEDULED
    intervention.priority = InterventionPriority.NORMAL
    intervention.intervention_type = InterventionType.MAINTENANCE
    intervention.technician_id = None
    intervention.scheduled_date = date.today()
    intervention.actual_start = None
    intervention.actual_end = None
    intervention.labor_hours = Decimal("0")
    intervention.labor_cost = Decimal("0")
    intervention.parts_cost = Decimal("0")
    intervention.travel_cost = Decimal("0")
    intervention.total_cost = Decimal("0")
    return intervention


# ============================================================================
# TESTS ZONES
# ============================================================================

class TestZones:
    """Tests zones."""

    def test_create_zone(self, service, mock_db):
        """Test création zone."""
        data = ZoneCreate(
            code="LYON",
            name="Région Lyon",
            country="France"
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_zone(data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_zone(self, service, mock_db, sample_zone):
        """Test récupération zone."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_zone

        result = service.get_zone(1)

        assert result == sample_zone
        assert result.code == "PARIS"

    def test_update_zone(self, service, mock_db, sample_zone):
        """Test mise à jour zone."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_zone

        data = ZoneUpdate(name="Île-de-France")
        result = service.update_zone(1, data)

        assert result is not None
        mock_db.commit.assert_called()


# ============================================================================
# TESTS TECHNICIANS
# ============================================================================

class TestTechnicians:
    """Tests techniciens."""

    def test_create_technician(self, service, mock_db):
        """Test création technicien."""
        data = TechnicianCreate(
            user_id=100,
            first_name="Marie",
            last_name="Martin",
            email="marie@example.com"
        )

        result = service.create_technician(data)

        mock_db.add.assert_called_once()

    def test_get_technician(self, service, mock_db, sample_technician):
        """Test récupération technicien."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_technician

        result = service.get_technician(1)

        assert result.first_name == "Jean"
        assert result.last_name == "Dupont"

    def test_update_technician_status(self, service, mock_db, sample_technician):
        """Test mise à jour statut."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_technician

        result = service.update_technician_status(1, TechnicianStatus.ON_MISSION)

        assert sample_technician.status == TechnicianStatus.ON_MISSION
        mock_db.commit.assert_called()

    def test_update_technician_location(self, service, mock_db, sample_technician):
        """Test mise à jour position GPS."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_technician

        result = service.update_technician_location(
            1,
            Decimal("48.8566"),
            Decimal("2.3522")
        )

        assert sample_technician.last_location_lat == Decimal("48.8566")
        assert sample_technician.last_location_lng == Decimal("2.3522")


# ============================================================================
# TESTS VEHICLES
# ============================================================================

class TestVehicles:
    """Tests véhicules."""

    def test_create_vehicle(self, service, mock_db):
        """Test création véhicule."""
        data = VehicleCreate(
            registration="EF-456-GH",
            make="Peugeot",
            model="Partner"
        )

        result = service.create_vehicle(data)

        mock_db.add.assert_called_once()

    def test_get_vehicle(self, service, mock_db, sample_vehicle):
        """Test récupération véhicule."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_vehicle

        result = service.get_vehicle(1)

        assert result.registration == "AB-123-CD"


# ============================================================================
# TESTS TEMPLATES
# ============================================================================

class TestTemplates:
    """Tests templates."""

    def test_create_template(self, service, mock_db):
        """Test création template."""
        data = TemplateCreate(
            code="PREV-CLIM",
            name="Maintenance préventive climatisation",
            estimated_duration=90,
            intervention_type=InterventionType.MAINTENANCE
        )

        result = service.create_template(data)

        mock_db.add.assert_called_once()


# ============================================================================
# TESTS INTERVENTIONS
# ============================================================================

class TestInterventions:
    """Tests interventions."""

    def test_generate_reference(self, service):
        """Test génération référence."""
        ref = service._generate_reference()

        assert ref.startswith("INT-")
        assert len(ref) > 10

    def test_create_intervention(self, service, mock_db):
        """Test création intervention."""
        data = InterventionCreate(
            title="Réparation chaudière",
            customer_name="Client A",
            address_city="Paris"
        )

        mock_db.flush = MagicMock()
        result = service.create_intervention(data)

        mock_db.add.assert_called()

    def test_get_intervention(self, service, mock_db, sample_intervention):
        """Test récupération intervention."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_intervention

        result = service.get_intervention(1)

        assert result.reference == "INT-202401-ABC123"

    def test_assign_intervention(self, service, mock_db, sample_intervention, sample_technician):
        """Test assignation intervention."""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_intervention,
            sample_technician
        ]

        data = InterventionAssign(technician_id=1)
        result = service.assign_intervention(1, data)

        assert sample_intervention.technician_id == 1
        assert sample_intervention.status == InterventionStatus.ASSIGNED

    def test_start_travel(self, service, mock_db, sample_intervention, sample_technician):
        """Test démarrage trajet."""
        sample_intervention.technician_id = 1
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_intervention,
            sample_technician
        ]

        result = service.start_travel(1, 1, Decimal("48.8"), Decimal("2.3"))

        assert sample_intervention.status == InterventionStatus.EN_ROUTE
        assert sample_technician.status == TechnicianStatus.TRAVELING

    def test_arrive_on_site(self, service, mock_db, sample_intervention):
        """Test arrivée sur site."""
        sample_intervention.technician_id = 1
        # Le service fait d'abord une query pour l'intervention, puis une pour travel_entry
        # On retourne l'intervention, puis None pour travel_entry (pas de trajet en cours)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_intervention,  # get_intervention
            None  # travel_entry query (pas de trajet à clôturer)
        ]

        result = service.arrive_on_site(1, 1)

        assert sample_intervention.status == InterventionStatus.ON_SITE
        assert sample_intervention.arrival_time is not None

    def test_start_intervention(self, service, mock_db, sample_intervention, sample_technician):
        """Test démarrage intervention."""
        sample_intervention.technician_id = 1
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_intervention,
            sample_technician
        ]

        result = service.start_intervention(1, 1)

        assert sample_intervention.status == InterventionStatus.IN_PROGRESS
        assert sample_intervention.actual_start is not None
        assert sample_technician.status == TechnicianStatus.ON_MISSION

    def test_complete_intervention(self, service, mock_db, sample_intervention, sample_technician):
        """Test complétion intervention."""
        sample_intervention.technician_id = 1
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_intervention,
            None,  # work_entry
            sample_technician
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = []

        data = InterventionComplete(
            completion_notes="Travail terminé",
            labor_hours=Decimal("2.5")
        )
        result = service.complete_intervention(1, 1, data)

        assert sample_intervention.status == InterventionStatus.COMPLETED
        assert sample_intervention.actual_end is not None
        assert sample_technician.status == TechnicianStatus.AVAILABLE
        assert sample_technician.completed_interventions == 46

    def test_cancel_intervention(self, service, mock_db, sample_intervention):
        """Test annulation intervention."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_intervention

        result = service.cancel_intervention(1, "Client absent")

        assert sample_intervention.status == InterventionStatus.CANCELLED
        assert sample_intervention.failure_reason == "Client absent"

    def test_rate_intervention(self, service, mock_db, sample_intervention, sample_technician):
        """Test notation intervention."""
        sample_intervention.technician_id = 1
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_intervention,
            sample_technician
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_intervention]

        result = service.rate_intervention(1, 5, "Excellent service!")

        assert sample_intervention.customer_rating == 5
        assert sample_intervention.customer_feedback == "Excellent service!"


# ============================================================================
# TESTS TIME ENTRIES
# ============================================================================

class TestTimeEntries:
    """Tests entrées de temps."""

    def test_create_time_entry(self, service, mock_db):
        """Test création entrée de temps."""
        data = TimeEntryCreate(
            technician_id=1,
            entry_type="work",
            start_time=datetime.utcnow()
        )

        result = service.create_time_entry(data)

        mock_db.add.assert_called_once()

    def test_update_time_entry_with_duration(self, service, mock_db):
        """Test mise à jour avec calcul durée."""
        entry = MagicMock(spec=TimeEntry)
        entry.start_time = datetime.utcnow() - timedelta(hours=2)
        entry.end_time = None

        mock_db.query.return_value.filter.return_value.first.return_value = entry

        from app.modules.field_service.schemas import TimeEntryUpdate
        data = TimeEntryUpdate(end_time=datetime.utcnow())

        result = service.update_time_entry(1, data)

        assert entry.duration_minutes is not None


# ============================================================================
# TESTS ROUTES
# ============================================================================

class TestRoutes:
    """Tests tournées."""

    def test_create_route(self, service, mock_db):
        """Test création tournée."""
        data = RouteCreate(
            technician_id=1,
            route_date=date.today(),
            intervention_order=[1, 2, 3]
        )

        result = service.create_route(data)

        mock_db.add.assert_called_once()

    def test_get_route(self, service, mock_db):
        """Test récupération tournée."""
        route = MagicMock(spec=Route)
        route.technician_id = 1
        route.route_date = date.today()
        mock_db.query.return_value.filter.return_value.first.return_value = route

        result = service.get_route(1, date.today())

        assert result.technician_id == 1


# ============================================================================
# TESTS EXPENSES
# ============================================================================

class TestExpenses:
    """Tests frais."""

    def test_create_expense(self, service, mock_db):
        """Test création frais."""
        data = ExpenseCreate(
            technician_id=1,
            expense_type="fuel",
            amount=Decimal("45.00"),
            expense_date=date.today()
        )

        result = service.create_expense(data)

        mock_db.add.assert_called_once()

    def test_approve_expense(self, service, mock_db):
        """Test approbation frais."""
        expense = MagicMock(spec=Expense)
        expense.status = "pending"
        mock_db.query.return_value.filter.return_value.first.return_value = expense

        result = service.approve_expense(1, approved_by=100)

        assert expense.status == "approved"
        assert expense.approved_by == 100

    def test_reject_expense(self, service, mock_db):
        """Test rejet frais."""
        expense = MagicMock(spec=Expense)
        expense.status = "pending"
        mock_db.query.return_value.filter.return_value.first.return_value = expense

        result = service.reject_expense(1, "Justificatif manquant")

        assert expense.status == "rejected"
        assert expense.notes == "Justificatif manquant"


# ============================================================================
# TESTS CONTRACTS
# ============================================================================

class TestContracts:
    """Tests contrats."""

    def test_create_contract(self, service, mock_db):
        """Test création contrat."""
        data = ContractCreate(
            contract_number="CT-2024-001",
            name="Contrat maintenance",
            customer_id=100,
            start_date=date.today(),
            monthly_fee=Decimal("500.00")
        )

        result = service.create_contract(data)

        mock_db.add.assert_called_once()


# ============================================================================
# TESTS STATS & DASHBOARD
# ============================================================================

class TestDashboard:
    """Tests dashboard."""

    def test_get_intervention_stats(self, service, mock_db):
        """Test statistiques interventions."""
        # Configurer correctement les chaînes de mock pour retourner des valeurs vides
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.all.return_value = []  # Liste vide, pas MagicMock

        result = service.get_intervention_stats(days=30)

        assert result.total == 0

    def test_get_technician_stats(self, service, mock_db, sample_technician):
        """Test statistiques techniciens."""
        # list_technicians retourne une liste vide, donc pas de stats à calculer
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []  # Pas de techniciens actifs
        mock_query.count.return_value = 0

        result = service.get_technician_stats(days=30)

        assert len(result) == 0  # Pas de techniciens = pas de stats


# ============================================================================
# TESTS ENUMS
# ============================================================================

class TestEnums:
    """Tests des énumérations."""

    def test_technician_status_values(self):
        """Test valeurs statut technicien."""
        assert TechnicianStatus.AVAILABLE.value == "available"
        assert TechnicianStatus.ON_MISSION.value == "on_mission"
        assert TechnicianStatus.TRAVELING.value == "traveling"

    def test_intervention_status_values(self):
        """Test valeurs statut intervention."""
        assert InterventionStatus.DRAFT.value == "draft"
        assert InterventionStatus.SCHEDULED.value == "scheduled"
        assert InterventionStatus.IN_PROGRESS.value == "in_progress"
        assert InterventionStatus.COMPLETED.value == "completed"

    def test_intervention_type_values(self):
        """Test valeurs type intervention."""
        assert InterventionType.MAINTENANCE.value == "maintenance"
        assert InterventionType.REPAIR.value == "repair"
        assert InterventionType.INSTALLATION.value == "installation"

    def test_intervention_priority_values(self):
        """Test valeurs priorité."""
        assert InterventionPriority.NORMAL.value == "normal"
        assert InterventionPriority.URGENT.value == "urgent"
        assert InterventionPriority.EMERGENCY.value == "emergency"
