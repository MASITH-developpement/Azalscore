"""
Fixtures de test pour le module Field Service - CORE SaaS v2
=============================================================
"""

from datetime import date, datetime, time
from decimal import Decimal
from unittest.mock import MagicMock, Mock
from uuid import UUID, uuid4

import pytest

from app.core.saas_context import SaaSContext, TenantScope, UserRole
from app.modules.field_service.models import (
    InterventionPriority,
    InterventionStatus,
    InterventionType,
    TechnicianStatus,
)


# =============================================================================
# MOCK SAAS CONTEXT
# =============================================================================

@pytest.fixture
def mock_saas_context():
    """Mock SaaSContext pour les tests."""
    return SaaSContext(
        tenant_id="test-tenant-123",
        user_id=UUID("12345678-1234-5678-1234-567812345678"),
        role=UserRole.ADMIN,
        permissions={"field_service.*"},
        scope=TenantScope.TENANT,
        ip_address="192.168.1.100",
        user_agent="pytest-agent",
        correlation_id="test-correlation-123",
        timestamp=datetime.utcnow(),
    )


@pytest.fixture
def mock_technician_context():
    """Mock SaaSContext pour un technicien."""
    return SaaSContext(
        tenant_id="test-tenant-123",
        user_id=UUID("87654321-4321-8765-4321-876543218765"),
        role=UserRole.EMPLOYE,
        permissions={"field_service.intervention.read", "field_service.intervention.update"},
        scope=TenantScope.TENANT,
        ip_address="192.168.1.101",
        user_agent="pytest-agent",
        correlation_id="test-correlation-456",
        timestamp=datetime.utcnow(),
    )


# =============================================================================
# MOCK SERVICE
# =============================================================================

@pytest.fixture
def mock_field_service():
    """Mock FieldServiceService."""
    service = MagicMock()
    service.tenant_id = "test-tenant-123"
    service.user_id = "12345678-1234-5678-1234-567812345678"
    return service


# =============================================================================
# FIXTURES DATA - ZONES
# =============================================================================

@pytest.fixture
def zone_create_data():
    """Données de création d'une zone."""
    return {
        "name": "Zone Nord",
        "code": "NORD",
        "description": "Zone de service nord de la ville",
        "postal_codes": ["75001", "75002", "75003"],
        "color": "#FF5733",
        "is_active": True,
    }


@pytest.fixture
def zone_update_data():
    """Données de mise à jour d'une zone."""
    return {
        "name": "Zone Nord Étendue",
        "description": "Zone nord étendue avec nouveaux codes postaux",
        "postal_codes": ["75001", "75002", "75003", "75004"],
    }


@pytest.fixture
def mock_zone():
    """Mock d'une zone."""
    zone = Mock()
    zone.id = 1
    zone.tenant_id = "test-tenant-123"
    zone.name = "Zone Nord"
    zone.code = "NORD"
    zone.description = "Zone de service nord"
    zone.postal_codes = ["75001", "75002", "75003"]
    zone.color = "#FF5733"
    zone.is_active = True
    zone.created_at = datetime.utcnow()
    zone.updated_at = datetime.utcnow()
    return zone


# =============================================================================
# FIXTURES DATA - TECHNICIANS
# =============================================================================

@pytest.fixture
def technician_create_data():
    """Données de création d'un technicien."""
    return {
        "user_id": 101,
        "employee_number": "TECH001",
        "first_name": "Jean",
        "last_name": "Dupont",
        "email": "jean.dupont@example.com",
        "phone": "+33612345678",
        "zone_id": 1,
        "skills": ["plomberie", "électricité", "chauffage"],
        "certifications": ["CAP Plombier", "Habilitation électrique"],
        "hourly_rate": Decimal("45.00"),
        "status": TechnicianStatus.AVAILABLE,
        "is_active": True,
    }


@pytest.fixture
def technician_update_data():
    """Données de mise à jour d'un technicien."""
    return {
        "phone": "+33687654321",
        "skills": ["plomberie", "électricité", "chauffage", "climatisation"],
        "hourly_rate": Decimal("50.00"),
    }


@pytest.fixture
def mock_technician():
    """Mock d'un technicien."""
    tech = Mock()
    tech.id = 1
    tech.tenant_id = "test-tenant-123"
    tech.user_id = 101
    tech.employee_number = "TECH001"
    tech.first_name = "Jean"
    tech.last_name = "Dupont"
    tech.email = "jean.dupont@example.com"
    tech.phone = "+33612345678"
    tech.zone_id = 1
    tech.skills = ["plomberie", "électricité"]
    tech.certifications = ["CAP Plombier"]
    tech.hourly_rate = Decimal("45.00")
    tech.status = TechnicianStatus.AVAILABLE
    tech.is_active = True
    tech.avg_rating = Decimal("4.5")
    tech.total_interventions = 150
    tech.completed_interventions = 142
    tech.total_km_traveled = Decimal("2500.5")
    tech.last_location_lat = None
    tech.last_location_lng = None
    tech.last_location_at = None
    tech.created_at = datetime.utcnow()
    tech.updated_at = datetime.utcnow()
    return tech


# =============================================================================
# FIXTURES DATA - VEHICLES
# =============================================================================

@pytest.fixture
def vehicle_create_data():
    """Données de création d'un véhicule."""
    return {
        "registration": "AB-123-CD",
        "brand": "Renault",
        "model": "Kangoo",
        "year": 2022,
        "mileage": 15000,
        "fuel_type": "diesel",
        "is_active": True,
    }


@pytest.fixture
def mock_vehicle():
    """Mock d'un véhicule."""
    vehicle = Mock()
    vehicle.id = 1
    vehicle.tenant_id = "test-tenant-123"
    vehicle.registration = "AB-123-CD"
    vehicle.brand = "Renault"
    vehicle.model = "Kangoo"
    vehicle.year = 2022
    vehicle.mileage = 15000
    vehicle.fuel_type = "diesel"
    vehicle.is_active = True
    vehicle.created_at = datetime.utcnow()
    vehicle.updated_at = datetime.utcnow()
    return vehicle


# =============================================================================
# FIXTURES DATA - TEMPLATES
# =============================================================================

@pytest.fixture
def template_create_data():
    """Données de création d'un template."""
    return {
        "name": "Maintenance Chaudière",
        "intervention_type": InterventionType.MAINTENANCE,
        "description": "Maintenance annuelle chaudière gaz",
        "estimated_duration": 120,
        "default_priority": InterventionPriority.MEDIUM,
        "checklist_template": [
            {"step": "Vérifier pression", "required": True},
            {"step": "Nettoyer brûleur", "required": True},
            {"step": "Contrôler fumées", "required": True},
        ],
        "is_active": True,
    }


@pytest.fixture
def mock_template():
    """Mock d'un template."""
    template = Mock()
    template.id = 1
    template.tenant_id = "test-tenant-123"
    template.name = "Maintenance Chaudière"
    template.intervention_type = InterventionType.MAINTENANCE
    template.description = "Maintenance annuelle"
    template.estimated_duration = 120
    template.default_priority = InterventionPriority.MEDIUM
    template.checklist_template = [{"step": "Vérifier pression", "required": True}]
    template.is_active = True
    template.created_at = datetime.utcnow()
    template.updated_at = datetime.utcnow()
    return template


# =============================================================================
# FIXTURES DATA - INTERVENTIONS
# =============================================================================

@pytest.fixture
def intervention_create_data():
    """Données de création d'une intervention."""
    return {
        "title": "Fuite d'eau cuisine",
        "description": "Fuite sous l'évier de la cuisine",
        "intervention_type": InterventionType.CORRECTIVE,
        "priority": InterventionPriority.HIGH,
        "customer_id": 501,
        "customer_name": "Marie Martin",
        "customer_phone": "+33698765432",
        "customer_email": "marie.martin@example.com",
        "site_address": "15 rue de la Paix",
        "site_postal_code": "75001",
        "site_city": "Paris",
        "site_latitude": Decimal("48.8566"),
        "site_longitude": Decimal("2.3522"),
        "scheduled_date": date.today(),
        "scheduled_time_start": time(9, 0),
        "scheduled_time_end": time(11, 0),
        "estimated_duration": 120,
        "zone_id": 1,
    }


@pytest.fixture
def intervention_update_data():
    """Données de mise à jour d'une intervention."""
    return {
        "priority": InterventionPriority.URGENT,
        "description": "Fuite importante sous l'évier - intervention urgente",
    }


@pytest.fixture
def mock_intervention():
    """Mock d'une intervention."""
    intervention = Mock()
    intervention.id = 1
    intervention.tenant_id = "test-tenant-123"
    intervention.reference = "INT-202601-ABC123"
    intervention.title = "Fuite d'eau cuisine"
    intervention.description = "Fuite sous l'évier"
    intervention.intervention_type = InterventionType.CORRECTIVE
    intervention.priority = InterventionPriority.HIGH
    intervention.status = InterventionStatus.SCHEDULED
    intervention.customer_id = 501
    intervention.customer_name = "Marie Martin"
    intervention.customer_phone = "+33698765432"
    intervention.customer_email = "marie.martin@example.com"
    intervention.site_address = "15 rue de la Paix"
    intervention.site_postal_code = "75001"
    intervention.site_city = "Paris"
    intervention.site_latitude = Decimal("48.8566")
    intervention.site_longitude = Decimal("2.3522")
    intervention.scheduled_date = date.today()
    intervention.scheduled_time_start = time(9, 0)
    intervention.scheduled_time_end = time(11, 0)
    intervention.estimated_duration = 120
    intervention.zone_id = 1
    intervention.technician_id = None
    intervention.template_id = None
    intervention.actual_start = None
    intervention.actual_end = None
    intervention.arrival_time = None
    intervention.departure_time = None
    intervention.labor_hours = None
    intervention.labor_cost = None
    intervention.parts_cost = None
    intervention.travel_cost = None
    intervention.total_cost = None
    intervention.completion_notes = None
    intervention.checklist = None
    intervention.parts_used = None
    intervention.photos = None
    intervention.signature_data = None
    intervention.signature_name = None
    intervention.signed_at = None
    intervention.customer_rating = None
    intervention.customer_feedback = None
    intervention.failure_reason = None
    intervention.created_at = datetime.utcnow()
    intervention.updated_at = datetime.utcnow()
    return intervention


@pytest.fixture
def mock_assigned_intervention(mock_intervention, mock_technician):
    """Mock d'une intervention assignée."""
    intervention = mock_intervention
    intervention.status = InterventionStatus.ASSIGNED
    intervention.technician_id = mock_technician.id
    return intervention


@pytest.fixture
def mock_completed_intervention(mock_assigned_intervention):
    """Mock d'une intervention complétée."""
    intervention = mock_assigned_intervention
    intervention.status = InterventionStatus.COMPLETED
    intervention.actual_start = datetime.utcnow()
    intervention.actual_end = datetime.utcnow()
    intervention.labor_hours = Decimal("2.0")
    intervention.labor_cost = Decimal("100.00")
    intervention.parts_cost = Decimal("50.00")
    intervention.travel_cost = Decimal("10.00")
    intervention.total_cost = Decimal("160.00")
    intervention.completion_notes = "Intervention terminée avec succès"
    intervention.signed_at = datetime.utcnow()
    return intervention


# =============================================================================
# FIXTURES DATA - TIME ENTRIES
# =============================================================================

@pytest.fixture
def time_entry_create_data():
    """Données de création d'une entrée de temps."""
    return {
        "technician_id": 1,
        "intervention_id": 1,
        "entry_type": "work",
        "start_time": datetime.utcnow(),
        "start_lat": Decimal("48.8566"),
        "start_lng": Decimal("2.3522"),
    }


@pytest.fixture
def mock_time_entry():
    """Mock d'une entrée de temps."""
    entry = Mock()
    entry.id = 1
    entry.tenant_id = "test-tenant-123"
    entry.technician_id = 1
    entry.intervention_id = 1
    entry.entry_type = "work"
    entry.start_time = datetime.utcnow()
    entry.end_time = None
    entry.duration_minutes = None
    entry.start_lat = Decimal("48.8566")
    entry.start_lng = Decimal("2.3522")
    entry.end_lat = None
    entry.end_lng = None
    entry.distance_km = None
    entry.notes = None
    entry.created_at = datetime.utcnow()
    entry.updated_at = datetime.utcnow()
    return entry


# =============================================================================
# FIXTURES DATA - ROUTES
# =============================================================================

@pytest.fixture
def route_create_data():
    """Données de création d'une tournée."""
    return {
        "technician_id": 1,
        "route_date": date.today(),
        "intervention_ids": [1, 2, 3],
        "optimized_order": [1, 3, 2],
        "total_distance_km": Decimal("45.5"),
        "estimated_duration": 360,
    }


@pytest.fixture
def mock_route():
    """Mock d'une tournée."""
    route = Mock()
    route.id = 1
    route.tenant_id = "test-tenant-123"
    route.technician_id = 1
    route.route_date = date.today()
    route.intervention_ids = [1, 2, 3]
    route.optimized_order = [1, 3, 2]
    route.total_distance_km = Decimal("45.5")
    route.estimated_duration = 360
    route.actual_distance_km = None
    route.actual_duration = None
    route.notes = None
    route.created_at = datetime.utcnow()
    route.updated_at = datetime.utcnow()
    return route


# =============================================================================
# FIXTURES DATA - EXPENSES
# =============================================================================

@pytest.fixture
def expense_create_data():
    """Données de création d'un frais."""
    return {
        "technician_id": 1,
        "intervention_id": 1,
        "expense_type": "fuel",
        "amount": Decimal("45.50"),
        "expense_date": date.today(),
        "description": "Carburant pour déplacement",
        "receipt_url": "https://example.com/receipts/123.pdf",
    }


@pytest.fixture
def mock_expense():
    """Mock d'un frais."""
    expense = Mock()
    expense.id = 1
    expense.tenant_id = "test-tenant-123"
    expense.technician_id = 1
    expense.intervention_id = 1
    expense.expense_type = "fuel"
    expense.amount = Decimal("45.50")
    expense.expense_date = date.today()
    expense.description = "Carburant"
    expense.receipt_url = "https://example.com/receipts/123.pdf"
    expense.status = "pending"
    expense.approved_by = None
    expense.approved_at = None
    expense.notes = None
    expense.created_at = datetime.utcnow()
    expense.updated_at = datetime.utcnow()
    return expense


# =============================================================================
# FIXTURES DATA - CONTRACTS
# =============================================================================

@pytest.fixture
def contract_create_data():
    """Données de création d'un contrat."""
    return {
        "customer_id": 501,
        "contract_number": "CTR-2026-001",
        "contract_type": "maintenance",
        "start_date": date.today(),
        "end_date": date(2027, 1, 25),
        "annual_amount": Decimal("1200.00"),
        "intervention_count": 4,
        "description": "Contrat maintenance annuelle chaudière",
        "status": "active",
    }


@pytest.fixture
def mock_contract():
    """Mock d'un contrat."""
    contract = Mock()
    contract.id = 1
    contract.tenant_id = "test-tenant-123"
    contract.customer_id = 501
    contract.contract_number = "CTR-2026-001"
    contract.contract_type = "maintenance"
    contract.start_date = date.today()
    contract.end_date = date(2027, 1, 25)
    contract.annual_amount = Decimal("1200.00")
    contract.intervention_count = 4
    contract.interventions_done = 0
    contract.description = "Contrat maintenance"
    contract.status = "active"
    contract.created_at = datetime.utcnow()
    contract.updated_at = datetime.utcnow()
    return contract


# =============================================================================
# FIXTURES DATA - STATS & DASHBOARD
# =============================================================================

@pytest.fixture
def mock_intervention_stats():
    """Mock des statistiques d'interventions."""
    return {
        "total": 150,
        "scheduled": 30,
        "in_progress": 5,
        "completed": 100,
        "cancelled": 15,
        "by_type": {
            "corrective": 80,
            "preventive": 40,
            "maintenance": 30,
        },
        "by_priority": {
            "low": 50,
            "medium": 70,
            "high": 25,
            "urgent": 5,
        },
        "avg_completion_time": 125.5,
    }


@pytest.fixture
def mock_technician_stats():
    """Mock des statistiques par technicien."""
    return [
        {
            "technician_id": 1,
            "technician_name": "Jean Dupont",
            "total_interventions": 50,
            "completed": 45,
            "cancelled": 5,
            "avg_rating": 4.5,
            "total_km": 1500.0,
            "total_revenue": 5000.0,
        },
        {
            "technician_id": 2,
            "technician_name": "Marie Durant",
            "total_interventions": 60,
            "completed": 55,
            "cancelled": 5,
            "avg_rating": 4.8,
            "total_km": 1800.0,
            "total_revenue": 6000.0,
        },
    ]


@pytest.fixture
def mock_dashboard():
    """Mock du dashboard complet."""
    return {
        "intervention_stats": {
            "total": 150,
            "scheduled": 30,
            "in_progress": 5,
            "completed": 100,
            "cancelled": 15,
        },
        "technician_stats": [
            {"technician_id": 1, "technician_name": "Jean Dupont", "total_interventions": 50}
        ],
        "today_interventions": 8,
        "active_technicians": 5,
        "pending_assignments": 10,
        "overdue_interventions": 3,
        "total_revenue": Decimal("15000.00"),
        "avg_satisfaction": 4.6,
    }


# =============================================================================
# HELPER ASSERTIONS
# =============================================================================

def assert_zone_response(response_data, expected_data=None):
    """Assertions pour une réponse zone."""
    assert "id" in response_data
    assert "tenant_id" in response_data
    assert "name" in response_data
    assert "code" in response_data

    if expected_data:
        for key, value in expected_data.items():
            assert response_data.get(key) == value


def assert_technician_response(response_data, expected_data=None):
    """Assertions pour une réponse technicien."""
    assert "id" in response_data
    assert "tenant_id" in response_data
    assert "first_name" in response_data
    assert "last_name" in response_data
    assert "status" in response_data

    if expected_data:
        for key, value in expected_data.items():
            assert response_data.get(key) == value


def assert_intervention_response(response_data, expected_data=None):
    """Assertions pour une réponse intervention."""
    assert "id" in response_data
    assert "tenant_id" in response_data
    assert "reference" in response_data
    assert "title" in response_data
    assert "status" in response_data
    assert "priority" in response_data

    if expected_data:
        for key, value in expected_data.items():
            assert response_data.get(key) == value


def assert_list_response(response_data, min_items=0):
    """Assertions pour une réponse liste."""
    assert isinstance(response_data, list)
    assert len(response_data) >= min_items


def assert_paginated_response(response_data, expected_total=None):
    """Assertions pour une réponse paginée."""
    assert "items" in response_data
    assert "total" in response_data
    assert "skip" in response_data
    assert "limit" in response_data
    assert isinstance(response_data["items"], list)

    if expected_total is not None:
        assert response_data["total"] == expected_total
