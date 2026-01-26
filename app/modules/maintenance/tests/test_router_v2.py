"""
Tests pour Maintenance Router v2 (CORE SaaS)
"""

import pytest
from unittest.mock import MagicMock

from app.modules.maintenance.models import (
    AssetCategory,
    AssetStatus,
    ContractStatus,
    PartRequestStatus,
    WorkOrderPriority,
    WorkOrderStatus,
)


# ============================================================================
# TESTS ASSETS
# ============================================================================

def test_create_asset_success(client, mock_maintenance_service, asset, asset_data):
    """Test création d'un actif"""
    mock_maintenance_service.create_asset.return_value = asset
    response = client.post("/v2/maintenance/assets", json=asset_data)
    assert response.status_code == 201
    mock_maintenance_service.create_asset.assert_called_once()


def test_list_assets_success(client, mock_maintenance_service, asset_list):
    """Test liste des actifs"""
    mock_maintenance_service.list_assets.return_value = (asset_list, len(asset_list))
    response = client.get("/v2/maintenance/assets")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(asset_list)
    assert len(data["items"]) == len(asset_list)


def test_list_assets_with_filters(client, mock_maintenance_service, asset_list):
    """Test liste des actifs avec filtres"""
    mock_maintenance_service.list_assets.return_value = (asset_list, len(asset_list))
    response = client.get(
        "/v2/maintenance/assets",
        params={
            "category": AssetCategory.MACHINERY.value,
            "status": AssetStatus.ACTIVE.value,
            "search": "Compresseur",
        }
    )
    assert response.status_code == 200


def test_get_asset_success(client, mock_maintenance_service, asset):
    """Test récupération d'un actif"""
    mock_maintenance_service.get_asset.return_value = asset
    response = client.get(f"/v2/maintenance/assets/{asset['id']}")
    assert response.status_code == 200
    mock_maintenance_service.get_asset.assert_called_once_with(asset["id"])


def test_get_asset_not_found(client, mock_maintenance_service):
    """Test récupération d'un actif inexistant"""
    mock_maintenance_service.get_asset.return_value = None
    response = client.get("/v2/maintenance/assets/999")
    assert response.status_code == 404
    assert "non trouvé" in response.json()["detail"]


def test_update_asset_success(client, mock_maintenance_service, asset):
    """Test mise à jour d'un actif"""
    mock_maintenance_service.update_asset.return_value = asset
    update_data = {"name": "Nouveau nom"}
    response = client.put(f"/v2/maintenance/assets/{asset['id']}", json=update_data)
    assert response.status_code == 200
    mock_maintenance_service.update_asset.assert_called_once()


def test_update_asset_not_found(client, mock_maintenance_service):
    """Test mise à jour d'un actif inexistant"""
    mock_maintenance_service.update_asset.return_value = None
    response = client.put("/v2/maintenance/assets/999", json={"name": "Test"})
    assert response.status_code == 404


def test_delete_asset_success(client, mock_maintenance_service, asset):
    """Test suppression d'un actif"""
    mock_maintenance_service.delete_asset.return_value = True
    response = client.delete(f"/v2/maintenance/assets/{asset['id']}")
    assert response.status_code == 204
    mock_maintenance_service.delete_asset.assert_called_once_with(asset["id"])


def test_delete_asset_not_found(client, mock_maintenance_service):
    """Test suppression d'un actif inexistant"""
    mock_maintenance_service.delete_asset.return_value = False
    response = client.delete("/v2/maintenance/assets/999")
    assert response.status_code == 404


# ============================================================================
# TESTS METERS
# ============================================================================

def test_create_meter_success(client, mock_maintenance_service, meter, meter_data, asset):
    """Test création d'un compteur"""
    mock_maintenance_service.create_meter.return_value = meter
    response = client.post(f"/v2/maintenance/assets/{asset['id']}/meters", json=meter_data)
    assert response.status_code == 201
    mock_maintenance_service.create_meter.assert_called_once()


def test_create_meter_asset_not_found(client, mock_maintenance_service, meter_data):
    """Test création d'un compteur pour actif inexistant"""
    mock_maintenance_service.create_meter.return_value = None
    response = client.post("/v2/maintenance/assets/999/meters", json=meter_data)
    assert response.status_code == 404


def test_record_meter_reading_success(client, mock_maintenance_service, meter, meter_reading_data):
    """Test enregistrement d'un relevé de compteur"""
    mock_maintenance_service.record_meter_reading.return_value = {
        "id": 1,
        "meter_id": meter["id"],
        **meter_reading_data
    }
    response = client.post(
        f"/v2/maintenance/meters/{meter['id']}/readings",
        json=meter_reading_data
    )
    assert response.status_code == 201


def test_record_meter_reading_not_found(client, mock_maintenance_service, meter_reading_data):
    """Test enregistrement d'un relevé pour compteur inexistant"""
    mock_maintenance_service.record_meter_reading.return_value = None
    response = client.post("/v2/maintenance/meters/999/readings", json=meter_reading_data)
    assert response.status_code == 404


# ============================================================================
# TESTS MAINTENANCE PLANS
# ============================================================================

def test_create_maintenance_plan_success(client, mock_maintenance_service, maintenance_plan, maintenance_plan_data):
    """Test création d'un plan de maintenance"""
    mock_maintenance_service.create_maintenance_plan.return_value = maintenance_plan
    response = client.post("/v2/maintenance/plans", json=maintenance_plan_data)
    assert response.status_code == 201


def test_list_maintenance_plans_success(client, mock_maintenance_service, maintenance_plan):
    """Test liste des plans de maintenance"""
    plans = [maintenance_plan]
    mock_maintenance_service.list_maintenance_plans.return_value = (plans, len(plans))
    response = client.get("/v2/maintenance/plans")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(plans)


def test_list_maintenance_plans_with_filters(client, mock_maintenance_service, maintenance_plan):
    """Test liste des plans avec filtres"""
    plans = [maintenance_plan]
    mock_maintenance_service.list_maintenance_plans.return_value = (plans, len(plans))
    response = client.get("/v2/maintenance/plans", params={"asset_id": 1, "is_active": True})
    assert response.status_code == 200


def test_get_maintenance_plan_success(client, mock_maintenance_service, maintenance_plan):
    """Test récupération d'un plan"""
    mock_maintenance_service.get_maintenance_plan.return_value = maintenance_plan
    response = client.get(f"/v2/maintenance/plans/{maintenance_plan['id']}")
    assert response.status_code == 200


def test_get_maintenance_plan_not_found(client, mock_maintenance_service):
    """Test récupération d'un plan inexistant"""
    mock_maintenance_service.get_maintenance_plan.return_value = None
    response = client.get("/v2/maintenance/plans/999")
    assert response.status_code == 404


def test_update_maintenance_plan_success(client, mock_maintenance_service, maintenance_plan):
    """Test mise à jour d'un plan"""
    mock_maintenance_service.update_maintenance_plan.return_value = maintenance_plan
    update_data = {"name": "Plan modifié"}
    response = client.put(f"/v2/maintenance/plans/{maintenance_plan['id']}", json=update_data)
    assert response.status_code == 200


def test_update_maintenance_plan_not_found(client, mock_maintenance_service):
    """Test mise à jour d'un plan inexistant"""
    mock_maintenance_service.update_maintenance_plan.return_value = None
    response = client.put("/v2/maintenance/plans/999", json={"name": "Test"})
    assert response.status_code == 404


# ============================================================================
# TESTS WORK ORDERS
# ============================================================================

def test_create_work_order_success(client, mock_maintenance_service, work_order, work_order_data):
    """Test création d'un ordre de travail"""
    mock_maintenance_service.create_work_order.return_value = work_order
    response = client.post("/v2/maintenance/work-orders", json=work_order_data)
    assert response.status_code == 201


def test_list_work_orders_success(client, mock_maintenance_service, work_order):
    """Test liste des ordres de travail"""
    work_orders = [work_order]
    mock_maintenance_service.list_work_orders.return_value = (work_orders, len(work_orders))
    response = client.get("/v2/maintenance/work-orders")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(work_orders)


def test_list_work_orders_with_filters(client, mock_maintenance_service, work_order):
    """Test liste des ordres de travail avec filtres"""
    work_orders = [work_order]
    mock_maintenance_service.list_work_orders.return_value = (work_orders, len(work_orders))
    response = client.get(
        "/v2/maintenance/work-orders",
        params={
            "asset_id": 1,
            "status": WorkOrderStatus.DRAFT.value,
            "priority": WorkOrderPriority.NORMAL.value,
        }
    )
    assert response.status_code == 200


def test_get_work_order_success(client, mock_maintenance_service, work_order):
    """Test récupération d'un ordre de travail"""
    mock_maintenance_service.get_work_order.return_value = work_order
    response = client.get(f"/v2/maintenance/work-orders/{work_order['id']}")
    assert response.status_code == 200


def test_get_work_order_not_found(client, mock_maintenance_service):
    """Test récupération d'un ordre inexistant"""
    mock_maintenance_service.get_work_order.return_value = None
    response = client.get("/v2/maintenance/work-orders/999")
    assert response.status_code == 404


def test_update_work_order_success(client, mock_maintenance_service, work_order):
    """Test mise à jour d'un ordre de travail"""
    mock_maintenance_service.update_work_order.return_value = work_order
    update_data = {"title": "Nouveau titre"}
    response = client.put(f"/v2/maintenance/work-orders/{work_order['id']}", json=update_data)
    assert response.status_code == 200


def test_update_work_order_not_found(client, mock_maintenance_service):
    """Test mise à jour d'un ordre inexistant"""
    mock_maintenance_service.update_work_order.return_value = None
    response = client.put("/v2/maintenance/work-orders/999", json={"title": "Test"})
    assert response.status_code == 404


def test_start_work_order_success(client, mock_maintenance_service, work_order):
    """Test démarrage d'un ordre de travail"""
    started_wo = {**work_order, "status": WorkOrderStatus.IN_PROGRESS}
    mock_maintenance_service.start_work_order.return_value = started_wo
    response = client.post(f"/v2/maintenance/work-orders/{work_order['id']}/start")
    assert response.status_code == 200


def test_start_work_order_cannot_start(client, mock_maintenance_service):
    """Test démarrage d'un ordre impossible"""
    mock_maintenance_service.start_work_order.return_value = None
    response = client.post("/v2/maintenance/work-orders/999/start")
    assert response.status_code == 400


def test_complete_work_order_success(client, mock_maintenance_service, work_order, work_order_complete_data):
    """Test complétion d'un ordre de travail"""
    completed_wo = {**work_order, "status": WorkOrderStatus.COMPLETED}
    mock_maintenance_service.complete_work_order.return_value = completed_wo
    response = client.post(
        f"/v2/maintenance/work-orders/{work_order['id']}/complete",
        json=work_order_complete_data
    )
    assert response.status_code == 200


def test_complete_work_order_cannot_complete(client, mock_maintenance_service, work_order_complete_data):
    """Test complétion d'un ordre impossible"""
    mock_maintenance_service.complete_work_order.return_value = None
    response = client.post(
        "/v2/maintenance/work-orders/999/complete",
        json=work_order_complete_data
    )
    assert response.status_code == 400


def test_add_labor_entry_success(client, mock_maintenance_service, work_order, labor_entry_data):
    """Test ajout d'une entrée de main d'oeuvre"""
    labor_entry = {"id": 1, "work_order_id": work_order["id"], **labor_entry_data}
    mock_maintenance_service.add_labor_entry.return_value = labor_entry
    response = client.post(
        f"/v2/maintenance/work-orders/{work_order['id']}/labor",
        json=labor_entry_data
    )
    assert response.status_code == 201


def test_add_labor_entry_wo_not_found(client, mock_maintenance_service, labor_entry_data):
    """Test ajout de main d'oeuvre pour ordre inexistant"""
    mock_maintenance_service.add_labor_entry.return_value = None
    response = client.post("/v2/maintenance/work-orders/999/labor", json=labor_entry_data)
    assert response.status_code == 404


def test_add_part_used_success(client, mock_maintenance_service, work_order, part_used_data):
    """Test ajout d'une pièce utilisée"""
    part_used = {"id": 1, "work_order_id": work_order["id"], **part_used_data}
    mock_maintenance_service.add_part_used.return_value = part_used
    response = client.post(
        f"/v2/maintenance/work-orders/{work_order['id']}/parts",
        json=part_used_data
    )
    assert response.status_code == 201


def test_add_part_used_wo_not_found(client, mock_maintenance_service, part_used_data):
    """Test ajout de pièce pour ordre inexistant"""
    mock_maintenance_service.add_part_used.return_value = None
    response = client.post("/v2/maintenance/work-orders/999/parts", json=part_used_data)
    assert response.status_code == 404


# ============================================================================
# TESTS FAILURES
# ============================================================================

def test_create_failure_success(client, mock_maintenance_service, failure, failure_data):
    """Test création d'une panne"""
    mock_maintenance_service.create_failure.return_value = failure
    response = client.post("/v2/maintenance/failures", json=failure_data)
    assert response.status_code == 201


def test_list_failures_success(client, mock_maintenance_service, failure):
    """Test liste des pannes"""
    failures = [failure]
    mock_maintenance_service.list_failures.return_value = (failures, len(failures))
    response = client.get("/v2/maintenance/failures")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(failures)


def test_list_failures_with_filters(client, mock_maintenance_service, failure):
    """Test liste des pannes avec filtres"""
    failures = [failure]
    mock_maintenance_service.list_failures.return_value = (failures, len(failures))
    response = client.get("/v2/maintenance/failures", params={"asset_id": 1, "status": "OPEN"})
    assert response.status_code == 200


def test_get_failure_success(client, mock_maintenance_service, failure):
    """Test récupération d'une panne"""
    mock_maintenance_service.get_failure.return_value = failure
    response = client.get(f"/v2/maintenance/failures/{failure['id']}")
    assert response.status_code == 200


def test_get_failure_not_found(client, mock_maintenance_service):
    """Test récupération d'une panne inexistante"""
    mock_maintenance_service.get_failure.return_value = None
    response = client.get("/v2/maintenance/failures/999")
    assert response.status_code == 404


def test_update_failure_success(client, mock_maintenance_service, failure):
    """Test mise à jour d'une panne"""
    mock_maintenance_service.update_failure.return_value = failure
    update_data = {"status": "RESOLVED"}
    response = client.put(f"/v2/maintenance/failures/{failure['id']}", json=update_data)
    assert response.status_code == 200


def test_update_failure_not_found(client, mock_maintenance_service):
    """Test mise à jour d'une panne inexistante"""
    mock_maintenance_service.update_failure.return_value = None
    response = client.put("/v2/maintenance/failures/999", json={"status": "RESOLVED"})
    assert response.status_code == 404


# ============================================================================
# TESTS SPARE PARTS
# ============================================================================

def test_create_spare_part_success(client, mock_maintenance_service, spare_part, spare_part_data):
    """Test création d'une pièce de rechange"""
    mock_maintenance_service.create_spare_part.return_value = spare_part
    response = client.post("/v2/maintenance/spare-parts", json=spare_part_data)
    assert response.status_code == 201


def test_list_spare_parts_success(client, mock_maintenance_service, spare_part):
    """Test liste des pièces de rechange"""
    parts = [spare_part]
    mock_maintenance_service.list_spare_parts.return_value = (parts, len(parts))
    response = client.get("/v2/maintenance/spare-parts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(parts)


def test_list_spare_parts_with_filters(client, mock_maintenance_service, spare_part):
    """Test liste des pièces avec filtres"""
    parts = [spare_part]
    mock_maintenance_service.list_spare_parts.return_value = (parts, len(parts))
    response = client.get("/v2/maintenance/spare-parts", params={"category": "FILTERS", "search": "filtre"})
    assert response.status_code == 200


def test_get_spare_part_success(client, mock_maintenance_service, spare_part):
    """Test récupération d'une pièce"""
    mock_maintenance_service.get_spare_part.return_value = spare_part
    response = client.get(f"/v2/maintenance/spare-parts/{spare_part['id']}")
    assert response.status_code == 200


def test_get_spare_part_not_found(client, mock_maintenance_service):
    """Test récupération d'une pièce inexistante"""
    mock_maintenance_service.get_spare_part.return_value = None
    response = client.get("/v2/maintenance/spare-parts/999")
    assert response.status_code == 404


def test_update_spare_part_success(client, mock_maintenance_service, spare_part):
    """Test mise à jour d'une pièce"""
    mock_maintenance_service.update_spare_part.return_value = spare_part
    update_data = {"unit_cost": "30.00"}
    response = client.put(f"/v2/maintenance/spare-parts/{spare_part['id']}", json=update_data)
    assert response.status_code == 200


def test_update_spare_part_not_found(client, mock_maintenance_service):
    """Test mise à jour d'une pièce inexistante"""
    mock_maintenance_service.update_spare_part.return_value = None
    response = client.put("/v2/maintenance/spare-parts/999", json={"unit_cost": "30.00"})
    assert response.status_code == 404


# ============================================================================
# TESTS PART REQUESTS
# ============================================================================

def test_create_part_request_success(client, mock_maintenance_service, part_request, part_request_data):
    """Test création d'une demande de pièce"""
    mock_maintenance_service.create_part_request.return_value = part_request
    response = client.post("/v2/maintenance/part-requests", json=part_request_data)
    assert response.status_code == 201


def test_list_part_requests_success(client, mock_maintenance_service, part_request):
    """Test liste des demandes de pièces"""
    requests = [part_request]
    mock_maintenance_service.list_part_requests.return_value = (requests, len(requests))
    response = client.get("/v2/maintenance/part-requests")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(requests)


def test_list_part_requests_with_filters(client, mock_maintenance_service, part_request):
    """Test liste des demandes avec filtres"""
    requests = [part_request]
    mock_maintenance_service.list_part_requests.return_value = (requests, len(requests))
    response = client.get(
        "/v2/maintenance/part-requests",
        params={"status": PartRequestStatus.REQUESTED.value, "work_order_id": 1}
    )
    assert response.status_code == 200


# ============================================================================
# TESTS CONTRACTS
# ============================================================================

def test_create_contract_success(client, mock_maintenance_service, contract, contract_data):
    """Test création d'un contrat"""
    mock_maintenance_service.create_contract.return_value = contract
    response = client.post("/v2/maintenance/contracts", json=contract_data)
    assert response.status_code == 201


def test_list_contracts_success(client, mock_maintenance_service, contract):
    """Test liste des contrats"""
    contracts = [contract]
    mock_maintenance_service.list_contracts.return_value = (contracts, len(contracts))
    response = client.get("/v2/maintenance/contracts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(contracts)


def test_list_contracts_with_filter(client, mock_maintenance_service, contract):
    """Test liste des contrats avec filtre"""
    contracts = [contract]
    mock_maintenance_service.list_contracts.return_value = (contracts, len(contracts))
    response = client.get("/v2/maintenance/contracts", params={"status": ContractStatus.DRAFT.value})
    assert response.status_code == 200


def test_get_contract_success(client, mock_maintenance_service, contract):
    """Test récupération d'un contrat"""
    mock_maintenance_service.get_contract.return_value = contract
    response = client.get(f"/v2/maintenance/contracts/{contract['id']}")
    assert response.status_code == 200


def test_get_contract_not_found(client, mock_maintenance_service):
    """Test récupération d'un contrat inexistant"""
    mock_maintenance_service.get_contract.return_value = None
    response = client.get("/v2/maintenance/contracts/999")
    assert response.status_code == 404


def test_update_contract_success(client, mock_maintenance_service, contract):
    """Test mise à jour d'un contrat"""
    mock_maintenance_service.update_contract.return_value = contract
    update_data = {"status": ContractStatus.ACTIVE.value}
    response = client.put(f"/v2/maintenance/contracts/{contract['id']}", json=update_data)
    assert response.status_code == 200


def test_update_contract_not_found(client, mock_maintenance_service):
    """Test mise à jour d'un contrat inexistant"""
    mock_maintenance_service.update_contract.return_value = None
    response = client.put("/v2/maintenance/contracts/999", json={"status": ContractStatus.ACTIVE.value})
    assert response.status_code == 404


# ============================================================================
# TESTS DASHBOARD
# ============================================================================

def test_get_dashboard_success(client, mock_maintenance_service, dashboard_data):
    """Test récupération du dashboard"""
    mock_maintenance_service.get_dashboard.return_value = dashboard_data
    response = client.get("/v2/maintenance/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "assets_total" in data
    assert "wo_total" in data
    assert "failures_this_month" in data
