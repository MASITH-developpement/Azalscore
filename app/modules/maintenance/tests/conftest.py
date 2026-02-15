"""
Fixtures pour les tests Maintenance v2

Hérite des fixtures globales de app/conftest.py.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock

from app.modules.maintenance.models import (
    AssetCategory,
    AssetCriticality,
    AssetStatus,
    ContractStatus,
    PartRequestStatus,
    WorkOrderPriority,
    WorkOrderStatus,
)


# ============================================================================
# FIXTURES HÉRITÉES DU CONFTEST GLOBAL
# ============================================================================
# Les fixtures suivantes sont héritées de app/conftest.py:
# - tenant_id, user_id, user_uuid
# - db_session, test_db_session
# - test_client (avec headers auto-injectés)
# - mock_auth_global (autouse=True)
# - saas_context


@pytest.fixture
def client(test_client):
    """
    Alias pour test_client (compatibilité avec anciens tests).

    Le test_client du conftest global ajoute déjà les headers requis.
    """
    return test_client


@pytest.fixture
def auth_headers(tenant_id):
    """Headers d'authentification avec tenant ID."""
    return {
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": tenant_id
    }


# ============================================================================
# FIXTURES SERVICE
# ============================================================================

@pytest.fixture
def mock_maintenance_service():
    """Mock MaintenanceService pour les tests"""
    mock_service = MagicMock()

    # Configuration par défaut - Assets
    mock_service.create_asset.return_value = None
    mock_service.get_asset.return_value = None
    mock_service.list_assets.return_value = ([], 0)
    mock_service.update_asset.return_value = None
    mock_service.delete_asset.return_value = False

    # Meters
    mock_service.create_meter.return_value = None
    mock_service.record_meter_reading.return_value = None

    # Maintenance Plans
    mock_service.create_maintenance_plan.return_value = None
    mock_service.get_maintenance_plan.return_value = None
    mock_service.list_maintenance_plans.return_value = ([], 0)
    mock_service.update_maintenance_plan.return_value = None

    # Work Orders
    mock_service.create_work_order.return_value = None
    mock_service.get_work_order.return_value = None
    mock_service.list_work_orders.return_value = ([], 0)
    mock_service.update_work_order.return_value = None
    mock_service.start_work_order.return_value = None
    mock_service.complete_work_order.return_value = None
    mock_service.add_labor_entry.return_value = None
    mock_service.add_part_used.return_value = None

    # Failures
    mock_service.create_failure.return_value = None
    mock_service.get_failure.return_value = None
    mock_service.list_failures.return_value = ([], 0)
    mock_service.update_failure.return_value = None

    # Spare Parts
    mock_service.create_spare_part.return_value = None
    mock_service.get_spare_part.return_value = None
    mock_service.list_spare_parts.return_value = ([], 0)
    mock_service.update_spare_part.return_value = None

    # Part Requests
    mock_service.create_part_request.return_value = None
    mock_service.list_part_requests.return_value = ([], 0)

    # Contracts
    mock_service.create_contract.return_value = None
    mock_service.get_contract.return_value = None
    mock_service.list_contracts.return_value = ([], 0)
    mock_service.update_contract.return_value = None

    # Dashboard
    mock_service.get_dashboard.return_value = None

    return mock_service


# ============================================================================
# FIXTURES DONNÉES ASSETS
# ============================================================================

@pytest.fixture
def asset_data():
    """Données d'actif sample"""
    return {
        "asset_code": "ASSET-001",
        "name": "Compresseur Principal",
        "description": "Compresseur d'air industriel",
        "category": AssetCategory.MACHINERY,
        "asset_type": "Compresseur",
        "criticality": AssetCriticality.HIGH,
        "location_description": "Zone Production A",
        "manufacturer": "ACME Corp",
        "model": "COMP-5000",
        "serial_number": "SN123456789",
        "purchase_date": date.today(),
    }


@pytest.fixture
def asset(asset_data, tenant_id, user_id):
    """Instance actif sample"""
    return {
        "id": 1,
        "tenant_id": int(tenant_id),
        "status": AssetStatus.ACTIVE,
        **asset_data,
        "created_by": int(user_id),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def asset_list(asset):
    """Liste d'actifs sample"""
    return [
        asset,
        {
            **asset,
            "id": 2,
            "asset_code": "ASSET-002",
            "name": "Compresseur Secondaire",
        },
    ]


# ============================================================================
# FIXTURES DONNÉES METERS
# ============================================================================

@pytest.fixture
def meter_data():
    """Données de compteur sample"""
    return {
        "meter_code": "METER-001",
        "name": "Heures de fonctionnement",
        "meter_type": "HOURS",
        "unit": "h",
        "initial_reading": Decimal("0"),
        "alert_threshold": Decimal("8000"),
        "critical_threshold": Decimal("10000"),
    }


@pytest.fixture
def meter(meter_data, tenant_id, user_id):
    """Instance compteur sample"""
    return {
        "id": 1,
        "tenant_id": int(tenant_id),
        "asset_id": 1,
        **meter_data,
        "current_reading": Decimal("5000"),
        "created_by": int(user_id),
        "created_at": datetime.utcnow(),
    }


@pytest.fixture
def meter_reading_data():
    """Données de relevé de compteur sample"""
    return {
        "reading_value": Decimal("5100"),
        "source": "MANUAL",
        "notes": "Relevé mensuel",
    }


# ============================================================================
# FIXTURES DONNÉES MAINTENANCE PLANS
# ============================================================================

@pytest.fixture
def maintenance_plan_data():
    """Données de plan de maintenance sample"""
    return {
        "plan_code": "PLAN-001",
        "name": "Maintenance Préventive Compresseur",
        "description": "Plan de maintenance préventive mensuel",
        "maintenance_type": "PREVENTIVE",
        "asset_id": 1,
        "trigger_type": "TIME",
        "frequency_value": 1,
        "frequency_unit": "MONTH",
        "estimated_duration_hours": Decimal("2"),
    }


@pytest.fixture
def maintenance_plan(maintenance_plan_data, tenant_id, user_id):
    """Instance plan de maintenance sample"""
    return {
        "id": 1,
        "tenant_id": int(tenant_id),
        **maintenance_plan_data,
        "is_active": True,
        "created_by": int(user_id),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


# ============================================================================
# FIXTURES DONNÉES WORK ORDERS
# ============================================================================

@pytest.fixture
def work_order_data():
    """Données d'ordre de travail sample"""
    return {
        "title": "Maintenance Compresseur",
        "description": "Maintenance préventive mensuelle",
        "maintenance_type": "PREVENTIVE",
        "priority": WorkOrderPriority.NORMAL,
        "asset_id": 1,
        "scheduled_start_date": datetime.utcnow(),
        "due_date": datetime.utcnow(),
        "estimated_labor_hours": Decimal("2"),
    }


@pytest.fixture
def work_order(work_order_data, tenant_id, user_id):
    """Instance ordre de travail sample"""
    return {
        "id": 1,
        "tenant_id": int(tenant_id),
        "wo_number": "WO-202401-0001",
        "status": WorkOrderStatus.DRAFT,
        **work_order_data,
        "created_by": int(user_id),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def work_order_complete_data():
    """Données de complétion d'ordre de travail sample"""
    return {
        "completion_notes": "Maintenance effectuée avec succès",
        "meter_reading_end": Decimal("5200"),
    }


@pytest.fixture
def labor_entry_data():
    """Données d'entrée de main d'oeuvre sample"""
    return {
        "technician_id": 1,
        "work_date": date.today(),
        "hours_worked": Decimal("2"),
        "overtime_hours": Decimal("0"),
        "labor_type": "REGULAR",
        "hourly_rate": Decimal("50"),
        "work_description": "Maintenance compresseur",
    }


@pytest.fixture
def part_used_data():
    """Données de pièce utilisée sample"""
    return {
        "spare_part_id": 1,
        "part_description": "Filtre à air",
        "quantity_used": Decimal("1"),
        "unit": "pcs",
        "unit_cost": Decimal("25.50"),
        "source": "STOCK",
    }


# ============================================================================
# FIXTURES DONNÉES FAILURES
# ============================================================================

@pytest.fixture
def failure_data():
    """Données de panne sample"""
    return {
        "asset_id": 1,
        "failure_type": "MECHANICAL",
        "description": "Surchauffe du compresseur",
        "symptoms": "Température élevée, bruit anormal",
        "failure_date": datetime.utcnow(),
        "production_stopped": True,
        "downtime_hours": Decimal("4"),
    }


@pytest.fixture
def failure(failure_data, tenant_id, user_id):
    """Instance panne sample"""
    return {
        "id": 1,
        "tenant_id": int(tenant_id),
        "failure_number": "FL-202401-0001",
        "status": "OPEN",
        **failure_data,
        "reported_by_id": int(user_id),
        "created_by": int(user_id),
        "created_at": datetime.utcnow(),
    }


# ============================================================================
# FIXTURES DONNÉES SPARE PARTS
# ============================================================================

@pytest.fixture
def spare_part_data():
    """Données de pièce de rechange sample"""
    return {
        "part_code": "PART-001",
        "name": "Filtre à air compresseur",
        "description": "Filtre haute performance",
        "category": "FILTERS",
        "manufacturer": "ACME Filters",
        "unit": "pcs",
        "unit_cost": Decimal("25.50"),
        "min_stock_level": Decimal("5"),
        "reorder_point": Decimal("10"),
        "criticality": "MEDIUM",
    }


@pytest.fixture
def spare_part(spare_part_data, tenant_id, user_id):
    """Instance pièce de rechange sample"""
    return {
        "id": 1,
        "tenant_id": int(tenant_id),
        **spare_part_data,
        "is_active": True,
        "created_by": int(user_id),
        "created_at": datetime.utcnow(),
    }


# ============================================================================
# FIXTURES DONNÉES PART REQUESTS
# ============================================================================

@pytest.fixture
def part_request_data():
    """Données de demande de pièce sample"""
    return {
        "work_order_id": 1,
        "spare_part_id": 1,
        "part_description": "Filtre à air",
        "quantity_requested": Decimal("2"),
        "unit": "pcs",
        "priority": "NORMAL",
        "required_date": date.today(),
        "request_reason": "Maintenance préventive",
    }


@pytest.fixture
def part_request(part_request_data, tenant_id, user_id):
    """Instance demande de pièce sample"""
    return {
        "id": 1,
        "tenant_id": int(tenant_id),
        "request_number": "PR-202401-0001",
        "status": PartRequestStatus.REQUESTED,
        **part_request_data,
        "requester_id": int(user_id),
        "created_by": int(user_id),
        "created_at": datetime.utcnow(),
    }


# ============================================================================
# FIXTURES DONNÉES CONTRACTS
# ============================================================================

@pytest.fixture
def contract_data():
    """Données de contrat de maintenance sample"""
    return {
        "contract_code": "CONT-001",
        "name": "Contrat Maintenance Compresseurs",
        "description": "Contrat annuel maintenance préventive",
        "contract_type": "PREVENTIVE",
        "vendor_id": 1,
        "vendor_contact": "Service Maintenance",
        "vendor_email": "maintenance@vendor.com",
        "start_date": date.today(),
        "end_date": date(2025, 12, 31),
        "contract_value": Decimal("10000"),
        "annual_cost": Decimal("10000"),
        "payment_frequency": "ANNUAL",
        "includes_parts": True,
        "includes_labor": True,
    }


@pytest.fixture
def contract(contract_data, tenant_id, user_id):
    """Instance contrat sample"""
    return {
        "id": 1,
        "tenant_id": int(tenant_id),
        "status": ContractStatus.DRAFT,
        **contract_data,
        "created_by": int(user_id),
        "created_at": datetime.utcnow(),
    }


# ============================================================================
# FIXTURES DONNÉES DASHBOARD
# ============================================================================

@pytest.fixture
def dashboard_data():
    """Données de dashboard sample"""
    return {
        "assets_total": 100,
        "assets_active": 85,
        "assets_in_maintenance": 5,
        "wo_total": 500,
        "wo_open": 50,
        "wo_overdue": 5,
        "wo_completed_this_month": 45,
        "failures_this_month": 3,
        "plans_active": 25,
        "plans_due_soon": 8,
        "contracts_active": 10,
        "contracts_expiring_soon": 2,
        "parts_below_min_stock": 12,
        "pending_part_requests": 6,
    }
