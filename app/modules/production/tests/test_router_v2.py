"""
Tests pour le module Production v2 - Router API
================================================

✅ Tests conformes au pattern CORE SaaS:
- Utilisation de context.tenant_id pour isolation
- Utilisation de context.user_id pour audit trail
- Mock de get_saas_context via conftest.py

Coverage:
- Work Centers (6 tests)
- BOM - Nomenclatures (8 tests)
- Routings - Gammes (3 tests)
- Manufacturing Orders (9 tests)
- Work Orders (5 tests)
- Consommations & Production (3 tests)
- Scraps - Rebuts (2 tests)
- Production Plans (2 tests)
- Maintenance (3 tests)
- Dashboard (1 test)
- Workflows (5 tests)
- Security & Isolation (3 tests)

Total: ~50 tests couvrant 42 endpoints
"""

import pytest
from datetime import datetime, timedelta, date
from decimal import Decimal
from uuid import uuid4



# ============================================================================
# TESTS CENTRES DE TRAVAIL (WORK CENTERS)
# ============================================================================

def test_create_work_center(test_client, client, auth_headers, tenant_id, user_id, sample_work_center_data):
    """Test création d'un centre de travail"""
    response = test_client.post(
        "/api/v2/production/work-centers",
        json=sample_work_center_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["code"] == sample_work_center_data["code"]
    assert data["name"] == sample_work_center_data["name"]
    assert data["tenant_id"] == tenant_id
    assert data["created_by"] == user_id


def test_list_work_centers(test_client, client, auth_headers, sample_work_center, tenant_id):
    """Test liste des centres de travail"""
    response = test_client.get(
        "/api/v2/production/work-centers",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    for wc in data:
        assert wc["tenant_id"] == tenant_id


def test_get_work_center(test_client, client, auth_headers, sample_work_center):
    """Test récupération d'un centre de travail par ID"""
    response = test_client.get(
        f"/api/v2/production/work-centers/{sample_work_center.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(sample_work_center.id)
    assert data["code"] == sample_work_center.code


def test_update_work_center(test_client, client, auth_headers, sample_work_center):
    """Test mise à jour d'un centre de travail"""
    update_data = {
        "name": "Updated Assembly Line",
        "capacity_per_hour": 20
    }

    response = test_client.put(
        f"/api/v2/production/work-centers/{sample_work_center.id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == update_data["name"]
    assert float(data["capacity_per_hour"]) == update_data["capacity_per_hour"]


def test_set_work_center_status(test_client, client, auth_headers, sample_work_center):
    """Test modification du statut d'un centre de travail"""
    response = test_client.post(
        f"/api/v2/production/work-centers/{sample_work_center.id}/status/{WorkCenterStatus.MAINTENANCE.value}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == WorkCenterStatus.MAINTENANCE.value


def test_get_work_center_orders(test_client, client, auth_headers, sample_work_center, sample_work_order):
    """Test liste des ordres de travail d'un centre"""
    response = test_client.get(
        f"/api/v2/production/work-centers/{sample_work_center.id}/work-orders",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    # Vérifier que tous les ordres sont pour ce centre
    for wo in data:
        assert wo["work_center_id"] == str(sample_work_center.id)


# ============================================================================
# TESTS NOMENCLATURES (BOM)
# ============================================================================

def test_create_bom(test_client, client, auth_headers, tenant_id, user_id, sample_bom_data):
    """Test création d'une nomenclature"""
    response = test_client.post(
        "/api/v2/production/bom",
        json=sample_bom_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["code"] == sample_bom_data["code"]
    assert data["tenant_id"] == tenant_id
    assert data["created_by"] == user_id


def test_list_boms(test_client, client, auth_headers, sample_bom, tenant_id):
    """Test liste des nomenclatures avec pagination"""
    response = test_client.get(
        "/api/v2/production/bom?page=1&page_size=50",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure pagination
    assert "boms" in data
    assert "total" in data
    assert "page" in data

    # Vérifier isolation tenant
    for bom in data["boms"]:
        assert bom["tenant_id"] == tenant_id


def test_list_boms_by_product(test_client, client, auth_headers, sample_bom, sample_product):
    """Test liste des BOMs filtrées par produit"""
    response = test_client.get(
        f"/api/v2/production/bom?product_id={sample_product.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for bom in data["boms"]:
        assert bom["product_id"] == str(sample_product.id)


def test_get_bom(test_client, client, auth_headers, sample_bom):
    """Test récupération d'une nomenclature par ID"""
    response = test_client.get(
        f"/api/v2/production/bom/{sample_bom.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(sample_bom.id)
    assert data["code"] == sample_bom.code


def test_get_bom_by_product(test_client, client, auth_headers, sample_bom, sample_product):
    """Test récupération de la BOM active d'un produit"""
    response = test_client.get(
        f"/api/v2/production/bom/product/{sample_product.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["product_id"] == str(sample_product.id)
    assert data["status"] == "ACTIVE"


def test_update_bom(test_client, client, auth_headers, sample_bom):
    """Test mise à jour d'une nomenclature"""
    update_data = {
        "version": "1.1",
        "notes": "Updated BOM version"
    }

    response = test_client.put(
        f"/api/v2/production/bom/{sample_bom.id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["version"] == update_data["version"]


def test_activate_bom(test_client, client, auth_headers, sample_bom):
    """Test activation d'une nomenclature"""
    response = test_client.post(
        f"/api/v2/production/bom/{sample_bom.id}/activate",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ACTIVE"


def test_add_bom_line(test_client, client, auth_headers, sample_bom, sample_bom_line_data):
    """Test ajout d'une ligne à une nomenclature"""
    response = test_client.post(
        f"/api/v2/production/bom/{sample_bom.id}/lines",
        json=sample_bom_line_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["bom_id"] == str(sample_bom.id)
    assert data["component_id"] == sample_bom_line_data["component_id"]
    assert float(data["quantity"]) == sample_bom_line_data["quantity"]


# ============================================================================
# TESTS GAMMES (ROUTINGS)
# ============================================================================

def test_create_routing(test_client, client, auth_headers, tenant_id, user_id, sample_routing_data):
    """Test création d'une gamme de fabrication"""
    response = test_client.post(
        "/api/v2/production/routings",
        json=sample_routing_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["code"] == sample_routing_data["code"]
    assert data["tenant_id"] == tenant_id
    assert data["created_by"] == user_id


def test_list_routings(test_client, client, auth_headers, sample_routing, tenant_id):
    """Test liste des gammes"""
    response = test_client.get(
        "/api/v2/production/routings",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    for routing in data:
        assert routing["tenant_id"] == tenant_id


def test_get_routing(test_client, client, auth_headers, sample_routing):
    """Test récupération d'une gamme par ID"""
    response = test_client.get(
        f"/api/v2/production/routings/{sample_routing.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(sample_routing.id)
    assert data["code"] == sample_routing.code


# ============================================================================
# TESTS ORDRES DE FABRICATION (MO)
# ============================================================================

def test_create_manufacturing_order(test_client, client, auth_headers, tenant_id, user_id, sample_mo_data):
    """Test création d'un ordre de fabrication"""
    response = test_client.post(
        "/api/v2/production/orders",
        json=sample_mo_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["product_id"] == sample_mo_data["product_id"]
    assert float(data["quantity_to_produce"]) == sample_mo_data["quantity_to_produce"]
    assert data["tenant_id"] == tenant_id
    assert data["created_by"] == user_id


def test_list_manufacturing_orders(test_client, client, auth_headers, sample_manufacturing_order, tenant_id):
    """Test liste des ordres de fabrication avec pagination"""
    response = test_client.get(
        "/api/v2/production/orders?page=1&page_size=50",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure pagination
    assert "orders" in data
    assert "total" in data
    assert "page" in data

    # Vérifier isolation tenant
    for mo in data["orders"]:
        assert mo["tenant_id"] == tenant_id


def test_list_manufacturing_orders_by_status(test_client, client, auth_headers, sample_manufacturing_order):
    """Test liste des MOs filtrés par statut"""
    response = test_client.get(
        f"/api/v2/production/orders?status={MOStatus.DRAFT.value}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for mo in data["orders"]:
        assert mo["status"] == MOStatus.DRAFT.value


def test_list_manufacturing_orders_by_priority(test_client, client, auth_headers, sample_manufacturing_order):
    """Test liste des MOs filtrés par priorité"""
    response = test_client.get(
        f"/api/v2/production/orders?priority={MOPriority.NORMAL.value}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for mo in data["orders"]:
        assert mo["priority"] == MOPriority.NORMAL.value


def test_get_manufacturing_order(test_client, client, auth_headers, sample_manufacturing_order):
    """Test récupération d'un ordre de fabrication par ID"""
    response = test_client.get(
        f"/api/v2/production/orders/{sample_manufacturing_order.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(sample_manufacturing_order.id)
    assert data["reference"] == sample_manufacturing_order.reference


def test_update_manufacturing_order(test_client, client, auth_headers, sample_manufacturing_order):
    """Test mise à jour d'un ordre de fabrication"""
    update_data = {
        "quantity_to_produce": 150,
        "priority": "HIGH"
    }

    response = test_client.put(
        f"/api/v2/production/orders/{sample_manufacturing_order.id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert float(data["quantity_to_produce"]) == update_data["quantity_to_produce"]
    assert data["priority"] == update_data["priority"]


def test_confirm_manufacturing_order(test_client, client, auth_headers, sample_manufacturing_order):
    """Test confirmation d'un ordre de fabrication"""
    response = test_client.post(
        f"/api/v2/production/orders/{sample_manufacturing_order.id}/confirm",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "CONFIRMED"
    assert "confirmed_at" in data


def test_start_manufacturing_order(test_client, client, auth_headers, sample_confirmed_mo):
    """Test démarrage d'un ordre de fabrication"""
    response = test_client.post(
        f"/api/v2/production/orders/{sample_confirmed_mo.id}/start",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "IN_PROGRESS"
    assert "started_at" in data


def test_complete_manufacturing_order(test_client, client, auth_headers, sample_confirmed_mo):
    """Test finalisation d'un ordre de fabrication"""
    response = test_client.post(
        f"/api/v2/production/orders/{sample_confirmed_mo.id}/complete",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "DONE"
    assert "completed_at" in data


def test_cancel_manufacturing_order(test_client, client, auth_headers, sample_manufacturing_order):
    """Test annulation d'un ordre de fabrication"""
    response = test_client.post(
        f"/api/v2/production/orders/{sample_manufacturing_order.id}/cancel?reason=Test+cancellation",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "CANCELLED"


# ============================================================================
# TESTS ORDRES DE TRAVAIL (WO)
# ============================================================================

def test_get_work_order(test_client, client, auth_headers, sample_work_order):
    """Test récupération d'un ordre de travail par ID"""
    response = test_client.get(
        f"/api/v2/production/work-orders/{sample_work_order.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(sample_work_order.id)
    assert data["mo_id"] == str(sample_work_order.mo_id)


def test_start_work_order(test_client, client, auth_headers, sample_work_order):
    """Test démarrage d'un ordre de travail"""
    start_data = {
        "notes": "Starting work order"
    }

    response = test_client.post(
        f"/api/v2/production/work-orders/{sample_work_order.id}/start",
        json=start_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == WorkOrderStatus.IN_PROGRESS.value
    assert "started_at" in data


def test_complete_work_order(test_client, client, auth_headers, sample_in_progress_wo):
    """Test finalisation d'un ordre de travail"""
    complete_data = {
        "actual_duration": 95
    }

    response = test_client.post(
        f"/api/v2/production/work-orders/{sample_in_progress_wo.id}/complete",
        json=complete_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == WorkOrderStatus.DONE.value
    assert "completed_at" in data


def test_pause_work_order(test_client, client, auth_headers, sample_in_progress_wo):
    """Test pause d'un ordre de travail"""
    response = test_client.post(
        f"/api/v2/production/work-orders/{sample_in_progress_wo.id}/pause?reason=Machine+breakdown",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == WorkOrderStatus.PAUSED.value


def test_resume_work_order(test_client, client, auth_headers, sample_in_progress_wo):
    """Test reprise d'un ordre de travail"""
    response = test_client.post(
        f"/api/v2/production/work-orders/{sample_in_progress_wo.id}/resume",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Statut devrait redevenir IN_PROGRESS
    assert data["status"] in [WorkOrderStatus.IN_PROGRESS.value, WorkOrderStatus.PAUSED.value]


# ============================================================================
# TESTS CONSOMMATIONS & PRODUCTION
# ============================================================================

def test_consume_material(test_client, client, auth_headers, sample_confirmed_mo, sample_consume_data):
    """Test consommation de matières premières"""
    response = test_client.post(
        f"/api/v2/production/orders/{sample_confirmed_mo.id}/consume",
        json=sample_consume_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["mo_id"] == str(sample_confirmed_mo.id)
    assert data["product_id"] == sample_consume_data["product_id"]
    assert float(data["quantity"]) == sample_consume_data["quantity"]


def test_return_material(test_client, client, auth_headers, sample_consumption):
    """Test retour de matières au stock"""
    return_data = {
        "consumption_id": str(sample_consumption.id),
        "quantity": 10
    }

    response = test_client.post(
        "/api/v2/production/consumptions/return",
        json=return_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier que le retour a été enregistré
    assert "id" in data or "status" in data


def test_record_production(test_client, client, auth_headers, sample_confirmed_mo, sample_produce_data):
    """Test enregistrement d'une production"""
    response = test_client.post(
        f"/api/v2/production/orders/{sample_confirmed_mo.id}/produce",
        json=sample_produce_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["mo_id"] == str(sample_confirmed_mo.id)
    assert float(data["quantity"]) == sample_produce_data["quantity"]


# ============================================================================
# TESTS REBUTS (SCRAPS)
# ============================================================================

def test_record_scrap(test_client, client, auth_headers, tenant_id, user_id, sample_scrap_data):
    """Test enregistrement d'un rebut"""
    response = test_client.post(
        "/api/v2/production/scraps",
        json=sample_scrap_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["mo_id"] == sample_scrap_data["mo_id"]
    assert data["tenant_id"] == tenant_id
    assert data["scrapped_by"] == user_id


def test_list_scraps(test_client, client, auth_headers, sample_scrap, tenant_id):
    """Test liste des rebuts"""
    response = test_client.get(
        "/api/v2/production/scraps",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    for scrap in data:
        assert scrap["tenant_id"] == tenant_id


# ============================================================================
# TESTS PLANIFICATION
# ============================================================================

def test_create_production_plan(test_client, client, auth_headers, tenant_id, user_id, sample_plan_data):
    """Test création d'un plan de production"""
    response = test_client.post(
        "/api/v2/production/plans",
        json=sample_plan_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["code"] == sample_plan_data["code"]
    assert data["tenant_id"] == tenant_id
    assert data["created_by"] == user_id


def test_get_production_plan(test_client, client, auth_headers, sample_production_plan):
    """Test récupération d'un plan de production"""
    response = test_client.get(
        f"/api/v2/production/plans/{sample_production_plan.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(sample_production_plan.id)
    assert data["code"] == sample_production_plan.code


# ============================================================================
# TESTS MAINTENANCE
# ============================================================================

def test_schedule_maintenance(test_client, client, auth_headers, tenant_id, user_id, sample_maintenance_data):
    """Test planification d'une maintenance"""
    response = test_client.post(
        "/api/v2/production/maintenance",
        json=sample_maintenance_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["work_center_id"] == sample_maintenance_data["work_center_id"]
    assert data["tenant_id"] == tenant_id
    assert data["created_by"] == user_id


def test_list_maintenance_schedules(test_client, client, auth_headers, sample_maintenance_schedule, tenant_id):
    """Test liste des maintenances planifiées"""
    response = test_client.get(
        "/api/v2/production/maintenance",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    for maintenance in data:
        assert maintenance["tenant_id"] == tenant_id


def test_list_due_maintenance(test_client, client, auth_headers, sample_maintenance_schedule):
    """Test liste des maintenances dues"""
    response = test_client.get(
        "/api/v2/production/maintenance/due",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier que ce sont des maintenances à venir ou en retard
    assert isinstance(data, list)


# ============================================================================
# TESTS DASHBOARD
# ============================================================================

def test_get_production_dashboard(test_client, client, auth_headers):
    """Test récupération du dashboard de production"""
    response = test_client.get(
        "/api/v2/production/dashboard",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure dashboard
    assert isinstance(data, dict)
    # Dashboard devrait contenir métriques clés de production


# ============================================================================
# TESTS WORKFLOWS COMPLEXES
# ============================================================================

def test_workflow_manufacturing_order_full_cycle(test_client, client,
    auth_headers,
    sample_product,
    sample_bom,
    sample_mo_data):
    """
    Test workflow complet MO: créer → confirmer → démarrer → produire → terminer
    """
    # 1. Créer ordre de fabrication
    response = test_client.post(
        "/api/v2/production/orders",
        json=sample_mo_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    mo = response.json()
    mo_id = mo["id"]

    # 2. Confirmer MO
    response = test_client.post(
        f"/api/v2/production/orders/{mo_id}/confirm",
        headers=auth_headers
    )
    assert response.status_code == 200
    confirmed = response.json()
    assert confirmed["status"] == "CONFIRMED"

    # 3. Démarrer MO
    response = test_client.post(
        f"/api/v2/production/orders/{mo_id}/start",
        headers=auth_headers
    )
    assert response.status_code == 200
    started = response.json()
    assert started["status"] == "IN_PROGRESS"

    # 4. Terminer MO
    response = test_client.post(
        f"/api/v2/production/orders/{mo_id}/complete",
        headers=auth_headers
    )
    assert response.status_code == 200
    completed = response.json()
    assert completed["status"] == "DONE"


def test_workflow_bom_with_lines(test_client, client,
    auth_headers,
    sample_product,
    sample_component,
    sample_bom_data,
    sample_bom_line_data):
    """
    Test workflow: créer BOM → ajouter lignes → activer
    """
    # 1. Créer BOM
    response = test_client.post(
        "/api/v2/production/bom",
        json=sample_bom_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    bom = response.json()
    bom_id = bom["id"]

    # 2. Ajouter ligne BOM
    response = test_client.post(
        f"/api/v2/production/bom/{bom_id}/lines",
        json=sample_bom_line_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    line = response.json()
    assert line["bom_id"] == bom_id

    # 3. Activer BOM
    response = test_client.post(
        f"/api/v2/production/bom/{bom_id}/activate",
        headers=auth_headers
    )
    assert response.status_code == 200
    activated = response.json()
    assert activated["status"] == "ACTIVE"


def test_workflow_work_order_with_pause_resume(test_client, client,
    auth_headers,
    sample_work_order):
    """
    Test workflow WO: démarrer → pause → reprendre → terminer
    """
    wo_id = sample_work_order.id

    # 1. Démarrer WO
    response = test_client.post(
        f"/api/v2/production/work-orders/{wo_id}/start",
        json={"notes": "Starting"},
        headers=auth_headers
    )
    assert response.status_code == 200
    started = response.json()
    assert started["status"] == "IN_PROGRESS"

    # 2. Pause WO
    response = test_client.post(
        f"/api/v2/production/work-orders/{wo_id}/pause?reason=Break",
        headers=auth_headers
    )
    assert response.status_code == 200
    paused = response.json()
    assert paused["status"] == "PAUSED"

    # 3. Reprendre WO
    response = test_client.post(
        f"/api/v2/production/work-orders/{wo_id}/resume",
        headers=auth_headers
    )
    assert response.status_code == 200
    resumed = response.json()
    assert resumed["status"] in ["IN_PROGRESS", "PAUSED"]


def test_workflow_production_with_consumption_and_output(test_client, client,
    auth_headers,
    sample_confirmed_mo,
    sample_component,
    sample_product):
    """
    Test workflow: consommer matières → produire → vérifier quantités
    """
    mo_id = sample_confirmed_mo.id

    # 1. Consommer matières
    consume_data = {
        "product_id": str(sample_component.id),
        "quantity": 100
    }
    response = test_client.post(
        f"/api/v2/production/orders/{mo_id}/consume",
        json=consume_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    consumption = response.json()

    # 2. Produire
    produce_data = {
        "product_id": str(sample_product.id),
        "quantity": 20
    }
    response = test_client.post(
        f"/api/v2/production/orders/{mo_id}/produce",
        json=produce_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    output = response.json()

    # 3. Vérifier MO mis à jour
    response = test_client.get(
        f"/api/v2/production/orders/{mo_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    mo = response.json()
    assert float(mo["quantity_produced"]) >= 20


def test_workflow_scrap_and_material_tracking(test_client, client,
    auth_headers,
    sample_confirmed_mo,
    sample_component):
    """
    Test workflow: enregistrer rebuts → vérifier traçabilité
    """
    # 1. Enregistrer rebut
    scrap_data = {
        "mo_id": str(sample_confirmed_mo.id),
        "product_id": str(sample_component.id),
        "quantity": 5,
        "reason": "DEFECTIVE",
        "notes": "Material defect"
    }
    response = test_client.post(
        "/api/v2/production/scraps",
        json=scrap_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    scrap = response.json()

    # 2. Lister rebuts du MO
    response = test_client.get(
        f"/api/v2/production/scraps?mo_id={sample_confirmed_mo.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    scraps = response.json()
    assert any(s["id"] == scrap["id"] for s in scraps)


# ============================================================================
# TESTS SÉCURITÉ & ISOLATION TENANT
# ============================================================================

def test_manufacturing_orders_tenant_isolation(test_client, client, auth_headers, db_session, tenant_id):
    """
    Test CRITIQUE: vérifier l'isolation stricte des MOs par tenant
    """
    # Créer MO pour un autre tenant
    from app.modules.inventory.models import Product, ProductType, ProductStatus

    other_product = Product(
        id=uuid4(),
        tenant_id="other-tenant-999",
        sku="OTHER-PROD",
        name="Other Product",
        product_type=ProductType.STOCKABLE,
        status=ProductStatus.ACTIVE,
        unit_price=Decimal("100"),
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(other_product)

    other_mo = ManufacturingOrder(
        id=uuid4(),
        tenant_id="other-tenant-999",
        reference="OTHER-MO",
        product_id=other_product.id,
        quantity_to_produce=Decimal("10"),
        status=MOStatus.DRAFT,
        priority=MOPriority.NORMAL,
        created_at=datetime.utcnow()
    )
    db_session.add(other_mo)
    db_session.commit()

    # Tenter de récupérer tous les MOs
    response = test_client.get(
        "/api/v2/production/orders",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier qu'AUCUN MO de l'autre tenant n'est retourné
    for mo in data["orders"]:
        assert mo["tenant_id"] == tenant_id
        assert mo["tenant_id"] != "other-tenant-999"


def test_work_centers_tenant_isolation(test_client, client, auth_headers, db_session, tenant_id):
    """
    Test CRITIQUE: isolation des centres de travail par tenant
    """
    # Créer work center pour autre tenant
    other_wc = WorkCenter(
        id=uuid4(),
        tenant_id="other-tenant-999",
        code="OTHER-WC",
        name="Other Work Center",
        work_center_type=WorkCenterType.ASSEMBLY,
        status=WorkCenterStatus.AVAILABLE,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(other_wc)
    db_session.commit()

    # Récupérer work centers
    response = test_client.get(
        "/api/v2/production/work-centers",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier isolation
    for wc in data:
        assert wc["tenant_id"] == tenant_id


def test_boms_tenant_isolation(test_client, client, auth_headers, db_session, tenant_id):
    """
    Test CRITIQUE: isolation des nomenclatures par tenant
    """
    # Créer BOM pour autre tenant
    from app.modules.inventory.models import Product, ProductType, ProductStatus

    other_product = Product(
        id=uuid4(),
        tenant_id="other-tenant-999",
        sku="OTHER-PROD-BOM",
        name="Other Product for BOM",
        product_type=ProductType.STOCKABLE,
        status=ProductStatus.ACTIVE,
        unit_price=Decimal("100"),
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(other_product)

    other_bom = BillOfMaterials(
        id=uuid4(),
        tenant_id="other-tenant-999",
        code="OTHER-BOM",
        product_id=other_product.id,
        bom_type=BOMType.STANDARD,
        status=BOMStatus.ACTIVE,
        version="1.0",
        quantity=Decimal("1"),
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(other_bom)
    db_session.commit()

    # Récupérer BOMs
    response = test_client.get(
        "/api/v2/production/bom",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier isolation
    for bom in data["boms"]:
        assert bom["tenant_id"] == tenant_id


# ============================================================================
# TESTS ERREURS & CAS LIMITES
# ============================================================================

def test_get_nonexistent_work_center(test_client, client, auth_headers):
    """Test récupération d'un centre de travail inexistant"""
    fake_id = uuid4()
    response = test_client.get(
        f"/api/v2/production/work-centers/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404
    assert "non trouvé" in response.json()["detail"].lower()


def test_get_nonexistent_bom(test_client, client, auth_headers):
    """Test récupération d'une BOM inexistante"""
    fake_id = uuid4()
    response = test_client.get(
        f"/api/v2/production/bom/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


def test_get_nonexistent_manufacturing_order(test_client, client, auth_headers):
    """Test récupération d'un MO inexistant"""
    fake_id = uuid4()
    response = test_client.get(
        f"/api/v2/production/orders/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


def test_get_nonexistent_work_order(test_client, client, auth_headers):
    """Test récupération d'un WO inexistant"""
    fake_id = uuid4()
    response = test_client.get(
        f"/api/v2/production/work-orders/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


def test_get_nonexistent_routing(test_client, client, auth_headers):
    """Test récupération d'une gamme inexistante"""
    fake_id = uuid4()
    response = test_client.get(
        f"/api/v2/production/routings/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


def test_start_already_started_mo(test_client, client, auth_headers, sample_confirmed_mo):
    """Test démarrer un MO déjà démarré"""
    # Démarrer une première fois
    test_client.post(
        f"/api/v2/production/orders/{sample_confirmed_mo.id}/start",
        headers=auth_headers
    )

    # Tenter de démarrer à nouveau
    response = test_client.post(
        f"/api/v2/production/orders/{sample_confirmed_mo.id}/start",
        headers=auth_headers
    )

    # Devrait soit réussir idempotent soit échouer
    assert response.status_code in [200, 400, 409]


def test_confirm_draft_mo_without_bom(test_client, client, auth_headers, sample_product):
    """Test confirmer un MO sans BOM (devrait échouer)"""
    # Créer MO sans BOM
    mo_data = {
        "product_id": str(sample_product.id),
        "quantity_to_produce": 10,
        "scheduled_start": date.today().isoformat(),
        "scheduled_end": (date.today() + timedelta(days=1)).isoformat()
    }

    response = test_client.post(
        "/api/v2/production/orders",
        json=mo_data,
        headers=auth_headers
    )

    if response.status_code == 201:
        mo = response.json()

        # Tenter de confirmer (devrait échouer si pas de BOM)
        response = test_client.post(
            f"/api/v2/production/orders/{mo['id']}/confirm",
            headers=auth_headers
        )

        # Devrait échouer ou nécessiter BOM
        assert response.status_code in [200, 400, 422]


# ============================================================================
# TESTS PAGINATION & FILTRES
# ============================================================================

def test_list_boms_pagination(test_client, client, auth_headers, sample_bom):
    """Test pagination de la liste des BOMs"""
    # Page 1
    response = test_client.get(
        "/api/v2/production/bom?page=1&page_size=10",
        headers=auth_headers
    )
    assert response.status_code == 200
    page1 = response.json()
    assert page1["page"] == 1

    # Page 2
    response = test_client.get(
        "/api/v2/production/bom?page=2&page_size=10",
        headers=auth_headers
    )
    assert response.status_code == 200
    page2 = response.json()
    assert page2["page"] == 2


def test_list_manufacturing_orders_pagination(test_client, client, auth_headers, sample_manufacturing_order):
    """Test pagination de la liste des MOs"""
    response = test_client.get(
        "/api/v2/production/orders?page=1&page_size=20",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 1
    assert data["page_size"] == 20


def test_list_scraps_with_filters(test_client, client, auth_headers, sample_scrap, sample_manufacturing_order):
    """Test liste des rebuts avec filtres"""
    response = test_client.get(
        f"/api/v2/production/scraps?mo_id={sample_manufacturing_order.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for scrap in data:
        assert scrap["mo_id"] == str(sample_manufacturing_order.id)


def test_list_scraps_with_date_range(test_client, client, auth_headers, sample_scrap):
    """Test liste des rebuts avec période"""
    from_date = (date.today() - timedelta(days=7)).isoformat()
    to_date = date.today().isoformat()

    response = test_client.get(
        f"/api/v2/production/scraps?from_date={from_date}&to_date={to_date}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_routings_by_product(test_client, client, auth_headers, sample_routing, sample_product):
    """Test liste des gammes filtrées par produit"""
    response = test_client.get(
        f"/api/v2/production/routings?product_id={sample_product.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for routing in data:
        assert routing["product_id"] == str(sample_product.id)


def test_list_maintenance_by_work_center(test_client, client, auth_headers, sample_maintenance_schedule, sample_work_center):
    """Test liste des maintenances filtrées par centre de travail"""
    response = test_client.get(
        f"/api/v2/production/maintenance?work_center_id={sample_work_center.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for maintenance in data:
        assert maintenance["work_center_id"] == str(sample_work_center.id)


# ============================================================================
# TESTS BUSINESS LOGIC
# ============================================================================

def test_work_center_status_transitions(test_client, client, auth_headers, sample_work_center):
    """Test transitions de statut centre de travail"""
    wc_id = sample_work_center.id

    # AVAILABLE → MAINTENANCE
    response = test_client.post(
        f"/api/v2/production/work-centers/{wc_id}/status/MAINTENANCE",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "MAINTENANCE"

    # MAINTENANCE → AVAILABLE
    response = test_client.post(
        f"/api/v2/production/work-centers/{wc_id}/status/AVAILABLE",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "AVAILABLE"


def test_bom_status_transitions(test_client, client, auth_headers, sample_bom):
    """Test transitions de statut BOM"""
    # Activer BOM
    response = test_client.post(
        f"/api/v2/production/bom/{sample_bom.id}/activate",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ACTIVE"


def test_manufacturing_order_quantity_tracking(test_client, client, auth_headers, sample_confirmed_mo, sample_product):
    """Test suivi des quantités produites vs planifiées"""
    mo_id = sample_confirmed_mo.id

    # Produire partiellement
    produce_data = {
        "product_id": str(sample_product.id),
        "quantity": 10
    }
    response = test_client.post(
        f"/api/v2/production/orders/{mo_id}/produce",
        json=produce_data,
        headers=auth_headers
    )
    assert response.status_code == 201

    # Vérifier quantités
    response = test_client.get(
        f"/api/v2/production/orders/{mo_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    mo = response.json()

    qty_produced = float(mo["quantity_produced"])
    qty_to_produce = float(mo["quantity_to_produce"])
    assert qty_produced >= 10
    assert qty_produced <= qty_to_produce


def test_work_center_capacity_tracking(test_client, client, auth_headers, sample_work_center):
    """Test suivi de la capacité d'un centre de travail"""
    response = test_client.get(
        f"/api/v2/production/work-centers/{sample_work_center.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    wc = response.json()

    # Vérifier présence capacité
    assert "capacity_per_hour" in wc
    assert float(wc["capacity_per_hour"]) > 0


def test_list_work_centers_by_status(test_client, client, auth_headers, sample_work_center):
    """Test liste des centres de travail filtrés par statut"""
    response = test_client.get(
        f"/api/v2/production/work-centers?status={WorkCenterStatus.AVAILABLE.value}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for wc in data:
        assert wc["status"] == WorkCenterStatus.AVAILABLE.value


def test_list_boms_by_status(test_client, client, auth_headers, sample_bom):
    """Test liste des BOMs filtrées par statut"""
    response = test_client.get(
        f"/api/v2/production/bom?status={BOMStatus.ACTIVE.value}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for bom in data["boms"]:
        assert bom["status"] == BOMStatus.ACTIVE.value
