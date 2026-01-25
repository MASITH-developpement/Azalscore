"""
Tests pour le module Inventory v2 - Router API
===============================================

✅ Tests conformes au pattern CORE SaaS:
- Utilisation de context.tenant_id pour isolation
- Utilisation de context.user_id pour audit trail
- Mock de get_saas_context via conftest.py

Coverage:
- Catégories (4 tests)
- Entrepôts (6 tests)
- Emplacements (4 tests)
- Produits (7 tests)
- Lots (4 tests)
- Numéros de série (2 tests)
- Mouvements de stock (6 tests)
- Inventaires physiques (6 tests)
- Préparations de commandes (7 tests)
- Dashboard (1 test)
- Workflows (5 tests)
- Security & Isolation (3 tests)

Total: ~55 tests couvrant 47 endpoints
"""

import pytest
from datetime import datetime, timedelta, date
from decimal import Decimal
from uuid import uuid4



# ============================================================================
# TESTS CATÉGORIES
# ============================================================================

def test_create_category(client, auth_headers, tenant_id, user_id, sample_category_data):
    """Test création d'une catégorie de produits"""
    response = client.post(
        "/api/v2/inventory/categories",
        json=sample_category_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["code"] == sample_category_data["code"]
    assert data["name"] == sample_category_data["name"]
    assert data["tenant_id"] == tenant_id
    # Vérifier audit trail
    assert data["created_by"] == user_id


def test_list_categories(client, auth_headers, sample_category, tenant_id):
    """Test liste des catégories"""
    response = client.get(
        "/api/v2/inventory/categories",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    # Vérifier isolation tenant
    for category in data:
        assert category["tenant_id"] == tenant_id


def test_get_category(client, auth_headers, sample_category):
    """Test récupération d'une catégorie par ID"""
    response = client.get(
        f"/api/v2/inventory/categories/{sample_category.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(sample_category.id)
    assert data["code"] == sample_category.code


def test_update_category(client, auth_headers, sample_category):
    """Test mise à jour d'une catégorie"""
    update_data = {
        "name": "Updated Electronics",
        "description": "Updated description"
    }

    response = client.put(
        f"/api/v2/inventory/categories/{sample_category.id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]


# ============================================================================
# TESTS ENTREPÔTS
# ============================================================================

def test_create_warehouse(client, auth_headers, tenant_id, user_id, sample_warehouse_data):
    """Test création d'un entrepôt"""
    response = client.post(
        "/api/v2/inventory/warehouses",
        json=sample_warehouse_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["code"] == sample_warehouse_data["code"]
    assert data["name"] == sample_warehouse_data["name"]
    assert data["tenant_id"] == tenant_id
    assert data["created_by"] == user_id


def test_list_warehouses(client, auth_headers, sample_warehouse, tenant_id):
    """Test liste des entrepôts"""
    response = client.get(
        "/api/v2/inventory/warehouses",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    for warehouse in data:
        assert warehouse["tenant_id"] == tenant_id


def test_get_warehouse(client, auth_headers, sample_warehouse):
    """Test récupération d'un entrepôt par ID"""
    response = client.get(
        f"/api/v2/inventory/warehouses/{sample_warehouse.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(sample_warehouse.id)
    assert data["code"] == sample_warehouse.code


def test_update_warehouse(client, auth_headers, sample_warehouse):
    """Test mise à jour d'un entrepôt"""
    update_data = {
        "name": "Updated Warehouse Name",
        "address": "789 New Address"
    }

    response = client.put(
        f"/api/v2/inventory/warehouses/{sample_warehouse.id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == update_data["name"]
    assert data["address"] == update_data["address"]


def test_get_warehouse_stock(client, auth_headers, sample_warehouse, sample_product, sample_location):
    """Test récupération du stock d'un entrepôt"""
    response = client.get(
        f"/api/v2/inventory/warehouses/{sample_warehouse.id}/stock",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    # Devrait retourner les niveaux de stock par produit


def test_list_warehouses_inactive(client, auth_headers, sample_warehouse):
    """Test liste des entrepôts inactifs"""
    response = client.get(
        "/api/v2/inventory/warehouses?is_active=false",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Tous les entrepôts retournés doivent être inactifs
    for warehouse in data:
        assert warehouse["is_active"] is False


# ============================================================================
# TESTS EMPLACEMENTS
# ============================================================================

def test_create_location(client, auth_headers, tenant_id, user_id, sample_warehouse, sample_location_data):
    """Test création d'un emplacement"""
    response = client.post(
        f"/api/v2/inventory/warehouses/{sample_warehouse.id}/locations",
        json=sample_location_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["code"] == sample_location_data["code"]
    assert data["warehouse_id"] == str(sample_warehouse.id)
    assert data["tenant_id"] == tenant_id


def test_list_locations(client, auth_headers, sample_location, tenant_id):
    """Test liste des emplacements"""
    response = client.get(
        "/api/v2/inventory/locations",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    for location in data:
        assert location["tenant_id"] == tenant_id


def test_list_locations_by_warehouse(client, auth_headers, sample_warehouse, sample_location):
    """Test liste des emplacements filtrés par entrepôt"""
    response = client.get(
        f"/api/v2/inventory/locations?warehouse_id={sample_warehouse.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for location in data:
        assert location["warehouse_id"] == str(sample_warehouse.id)


def test_get_location(client, auth_headers, sample_location):
    """Test récupération d'un emplacement par ID"""
    response = client.get(
        f"/api/v2/inventory/locations/{sample_location.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(sample_location.id)
    assert data["code"] == sample_location.code


# ============================================================================
# TESTS PRODUITS
# ============================================================================

def test_create_product(client, auth_headers, tenant_id, user_id, sample_product_data):
    """Test création d'un produit"""
    response = client.post(
        "/api/v2/inventory/products",
        json=sample_product_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["sku"] == sample_product_data["sku"]
    assert data["name"] == sample_product_data["name"]
    assert data["tenant_id"] == tenant_id
    assert data["created_by"] == user_id


def test_list_products(client, auth_headers, sample_product, tenant_id):
    """Test liste des produits avec pagination"""
    response = client.get(
        "/api/v2/inventory/products?page=1&page_size=50",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure pagination
    assert "products" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data

    # Vérifier isolation tenant
    for product in data["products"]:
        assert product["tenant_id"] == tenant_id


def test_list_products_by_category(client, auth_headers, sample_product, sample_category):
    """Test liste des produits filtrés par catégorie"""
    response = client.get(
        f"/api/v2/inventory/products?category_id={sample_category.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for product in data["products"]:
        assert product["category_id"] == str(sample_category.id)


def test_list_products_search(client, auth_headers, sample_product):
    """Test recherche de produits par nom"""
    response = client.get(
        f"/api/v2/inventory/products?search={sample_product.name[:6]}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data["products"], list)


def test_get_product(client, auth_headers, sample_product):
    """Test récupération d'un produit par ID"""
    response = client.get(
        f"/api/v2/inventory/products/{sample_product.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(sample_product.id)
    assert data["sku"] == sample_product.sku


def test_update_product(client, auth_headers, sample_product):
    """Test mise à jour d'un produit"""
    update_data = {
        "name": "Updated Laptop XPS 16",
        "unit_price": 1300.00
    }

    response = client.put(
        f"/api/v2/inventory/products/{sample_product.id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == update_data["name"]
    assert float(data["unit_price"]) == update_data["unit_price"]


def test_activate_product(client, auth_headers, sample_product):
    """Test activation d'un produit"""
    response = client.post(
        f"/api/v2/inventory/products/{sample_product.id}/activate",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ACTIVE"


def test_get_product_stock(client, auth_headers, sample_product):
    """Test récupération du stock d'un produit"""
    response = client.get(
        f"/api/v2/inventory/products/{sample_product.id}/stock",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    # Devrait retourner les niveaux de stock par emplacement


# ============================================================================
# TESTS LOTS
# ============================================================================

def test_create_lot(client, auth_headers, tenant_id, user_id, sample_lot_data):
    """Test création d'un lot"""
    response = client.post(
        "/api/v2/inventory/lots",
        json=sample_lot_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["lot_number"] == sample_lot_data["lot_number"]
    assert data["tenant_id"] == tenant_id
    assert data["created_by"] == user_id


def test_list_lots(client, auth_headers, sample_lot, tenant_id):
    """Test liste des lots"""
    response = client.get(
        "/api/v2/inventory/lots",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    for lot in data:
        assert lot["tenant_id"] == tenant_id


def test_list_lots_by_product(client, auth_headers, sample_lot, sample_product):
    """Test liste des lots filtrés par produit"""
    response = client.get(
        f"/api/v2/inventory/lots?product_id={sample_product.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for lot in data:
        assert lot["product_id"] == str(sample_product.id)


def test_get_lot(client, auth_headers, sample_lot):
    """Test récupération d'un lot par ID"""
    response = client.get(
        f"/api/v2/inventory/lots/{sample_lot.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(sample_lot.id)
    assert data["lot_number"] == sample_lot.lot_number


# ============================================================================
# TESTS NUMÉROS DE SÉRIE
# ============================================================================

def test_create_serial_number(client, auth_headers, tenant_id, user_id, sample_serial_data):
    """Test création d'un numéro de série"""
    response = client.post(
        "/api/v2/inventory/serials",
        json=sample_serial_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["serial_number"] == sample_serial_data["serial_number"]
    assert data["tenant_id"] == tenant_id
    assert data["created_by"] == user_id


def test_get_serial_number(client, auth_headers, sample_serial_number):
    """Test récupération d'un numéro de série par ID"""
    response = client.get(
        f"/api/v2/inventory/serials/{sample_serial_number.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(sample_serial_number.id)
    assert data["serial_number"] == sample_serial_number.serial_number


# ============================================================================
# TESTS MOUVEMENTS DE STOCK
# ============================================================================

def test_create_movement(client, auth_headers, tenant_id, user_id, sample_movement_data):
    """Test création d'un mouvement de stock"""
    response = client.post(
        "/api/v2/inventory/movements",
        json=sample_movement_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["movement_type"] == sample_movement_data["movement_type"]
    assert float(data["quantity"]) == sample_movement_data["quantity"]
    assert data["tenant_id"] == tenant_id
    assert data["created_by"] == user_id


def test_list_movements(client, auth_headers, sample_movement_in, tenant_id):
    """Test liste des mouvements avec pagination"""
    response = client.get(
        "/api/v2/inventory/movements?page=1&page_size=50",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure pagination
    assert "movements" in data
    assert "total" in data
    assert "page" in data

    # Vérifier isolation tenant
    for movement in data["movements"]:
        assert movement["tenant_id"] == tenant_id


def test_list_movements_by_product(client, auth_headers, sample_movement_in, sample_product):
    """Test liste des mouvements filtrés par produit"""
    response = client.get(
        f"/api/v2/inventory/movements?product_id={sample_product.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for movement in data["movements"]:
        assert movement["product_id"] == str(sample_product.id)


def test_list_movements_by_type(client, auth_headers, sample_movement_in):
    """Test liste des mouvements filtrés par type"""
    response = client.get(
        f"/api/v2/inventory/movements?movement_type={MovementType.IN.value}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for movement in data["movements"]:
        assert movement["movement_type"] == MovementType.IN.value


def test_get_movement(client, auth_headers, sample_movement_in):
    """Test récupération d'un mouvement par ID"""
    response = client.get(
        f"/api/v2/inventory/movements/{sample_movement_in.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(sample_movement_in.id)
    assert data["reference"] == sample_movement_in.reference


def test_confirm_movement(client, auth_headers, sample_movement_in):
    """Test confirmation d'un mouvement de stock"""
    response = client.post(
        f"/api/v2/inventory/movements/{sample_movement_in.id}/confirm",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "CONFIRMED"
    assert "confirmed_at" in data


def test_cancel_movement(client, auth_headers, sample_movement_in):
    """Test annulation d'un mouvement de stock"""
    response = client.post(
        f"/api/v2/inventory/movements/{sample_movement_in.id}/cancel?reason=Test+cancellation",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "CANCELLED"


# ============================================================================
# TESTS INVENTAIRES PHYSIQUES
# ============================================================================

def test_create_inventory_count(client, auth_headers, tenant_id, user_id, sample_inventory_count_data):
    """Test création d'un inventaire physique"""
    response = client.post(
        "/api/v2/inventory/counts",
        json=sample_inventory_count_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["warehouse_id"] == sample_inventory_count_data["warehouse_id"]
    assert data["tenant_id"] == tenant_id
    assert data["created_by"] == user_id


def test_list_inventory_counts(client, auth_headers, sample_inventory_count, tenant_id):
    """Test liste des inventaires physiques"""
    response = client.get(
        "/api/v2/inventory/counts",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    for count in data:
        assert count["tenant_id"] == tenant_id


def test_get_inventory_count(client, auth_headers, sample_inventory_count):
    """Test récupération d'un inventaire par ID"""
    response = client.get(
        f"/api/v2/inventory/counts/{sample_inventory_count.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(sample_inventory_count.id)
    assert data["reference"] == sample_inventory_count.reference


def test_start_inventory_count(client, auth_headers, sample_inventory_count):
    """Test démarrage d'un inventaire physique"""
    response = client.post(
        f"/api/v2/inventory/counts/{sample_inventory_count.id}/start",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "IN_PROGRESS"
    assert "started_at" in data


def test_update_count_line(client, auth_headers, sample_inventory_count, sample_count_line):
    """Test mise à jour d'une ligne d'inventaire"""
    update_data = {
        "counted_quantity": 95
    }

    response = client.put(
        f"/api/v2/inventory/counts/{sample_inventory_count.id}/lines/{sample_count_line.id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier que la mise à jour a été effectuée
    assert "success" in data or "status" in data


def test_validate_inventory_count(client, auth_headers, sample_inventory_count):
    """Test validation d'un inventaire physique"""
    response = client.post(
        f"/api/v2/inventory/counts/{sample_inventory_count.id}/validate",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "VALIDATED"
    assert "validated_at" in data


# ============================================================================
# TESTS PRÉPARATIONS DE COMMANDES
# ============================================================================

def test_create_picking(client, auth_headers, tenant_id, user_id, sample_picking_data):
    """Test création d'une préparation de commande"""
    response = client.post(
        "/api/v2/inventory/pickings",
        json=sample_picking_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["warehouse_id"] == sample_picking_data["warehouse_id"]
    assert data["tenant_id"] == tenant_id
    assert data["created_by"] == user_id


def test_list_pickings(client, auth_headers, sample_picking, tenant_id):
    """Test liste des préparations"""
    response = client.get(
        "/api/v2/inventory/pickings",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    for picking in data:
        assert picking["tenant_id"] == tenant_id


def test_list_pickings_by_status(client, auth_headers, sample_picking):
    """Test liste des préparations filtrées par statut"""
    response = client.get(
        f"/api/v2/inventory/pickings?status={PickingStatus.PENDING.value}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for picking in data:
        assert picking["status"] == PickingStatus.PENDING.value


def test_get_picking(client, auth_headers, sample_picking):
    """Test récupération d'une préparation par ID"""
    response = client.get(
        f"/api/v2/inventory/pickings/{sample_picking.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(sample_picking.id)
    assert data["reference"] == sample_picking.reference


def test_assign_picking(client, auth_headers, sample_picking, user_id):
    """Test assignation d'une préparation à un utilisateur"""
    response = client.post(
        f"/api/v2/inventory/pickings/{sample_picking.id}/assign/{user_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["assigned_to"] == user_id
    assert data["status"] == "ASSIGNED"


def test_start_picking(client, auth_headers, sample_picking):
    """Test démarrage d'une préparation"""
    response = client.post(
        f"/api/v2/inventory/pickings/{sample_picking.id}/start",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "IN_PROGRESS"
    assert "started_at" in data


def test_pick_line(client, auth_headers, sample_picking, sample_picking_line):
    """Test marquage d'une ligne comme préparée"""
    update_data = {
        "quantity_picked": 8
    }

    response = client.put(
        f"/api/v2/inventory/pickings/{sample_picking.id}/lines/{sample_picking_line.id}/pick",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier que la ligne a été mise à jour
    assert "success" in data or "status" in data


def test_complete_picking(client, auth_headers, sample_picking):
    """Test finalisation d'une préparation"""
    response = client.post(
        f"/api/v2/inventory/pickings/{sample_picking.id}/complete",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "DONE"
    assert "completed_at" in data


# ============================================================================
# TESTS DASHBOARD
# ============================================================================

def test_get_inventory_dashboard(client, auth_headers):
    """Test récupération du dashboard inventaire"""
    response = client.get(
        "/api/v2/inventory/dashboard",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure dashboard
    assert isinstance(data, dict)
    # Dashboard devrait contenir métriques clés
    assert any(key in data for key in ["total_products", "total_value", "low_stock", "stats"])


# ============================================================================
# TESTS WORKFLOWS COMPLEXES
# ============================================================================

def test_workflow_stock_movement_lifecycle(
    client,
    auth_headers,
    sample_product,
    sample_location,
    sample_movement_data
):
    """
    Test workflow complet: créer mouvement → confirmer → vérifier stock
    """
    # 1. Créer mouvement d'entrée
    response = client.post(
        "/api/v2/inventory/movements",
        json=sample_movement_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    movement = response.json()
    movement_id = movement["id"]

    # 2. Confirmer mouvement
    response = client.post(
        f"/api/v2/inventory/movements/{movement_id}/confirm",
        headers=auth_headers
    )
    assert response.status_code == 200
    confirmed = response.json()
    assert confirmed["status"] == "CONFIRMED"

    # 3. Vérifier stock produit mis à jour
    response = client.get(
        f"/api/v2/inventory/products/{sample_product.id}/stock",
        headers=auth_headers
    )
    assert response.status_code == 200
    stock = response.json()
    assert isinstance(stock, list)


def test_workflow_inventory_count_full(
    client,
    auth_headers,
    sample_warehouse,
    sample_inventory_count_data
):
    """
    Test workflow complet inventaire: créer → démarrer → compter → valider
    """
    # 1. Créer inventaire
    response = client.post(
        "/api/v2/inventory/counts",
        json=sample_inventory_count_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    count = response.json()
    count_id = count["id"]

    # 2. Démarrer inventaire
    response = client.post(
        f"/api/v2/inventory/counts/{count_id}/start",
        headers=auth_headers
    )
    assert response.status_code == 200
    started = response.json()
    assert started["status"] == "IN_PROGRESS"

    # 3. Valider inventaire
    response = client.post(
        f"/api/v2/inventory/counts/{count_id}/validate",
        headers=auth_headers
    )
    assert response.status_code == 200
    validated = response.json()
    assert validated["status"] == "VALIDATED"


def test_workflow_picking_full_cycle(
    client,
    auth_headers,
    user_id,
    sample_warehouse,
    sample_picking_data
):
    """
    Test workflow complet préparation: créer → assigner → démarrer → finaliser
    """
    # 1. Créer préparation
    response = client.post(
        "/api/v2/inventory/pickings",
        json=sample_picking_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    picking = response.json()
    picking_id = picking["id"]

    # 2. Assigner à utilisateur
    response = client.post(
        f"/api/v2/inventory/pickings/{picking_id}/assign/{user_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    assigned = response.json()
    assert assigned["status"] == "ASSIGNED"

    # 3. Démarrer préparation
    response = client.post(
        f"/api/v2/inventory/pickings/{picking_id}/start",
        headers=auth_headers
    )
    assert response.status_code == 200
    started = response.json()
    assert started["status"] == "IN_PROGRESS"

    # 4. Finaliser préparation
    response = client.post(
        f"/api/v2/inventory/pickings/{picking_id}/complete",
        headers=auth_headers
    )
    assert response.status_code == 200
    completed = response.json()
    assert completed["status"] == "DONE"


def test_workflow_product_with_lot(
    client,
    auth_headers,
    sample_product,
    sample_lot_data
):
    """
    Test workflow: créer produit avec lots
    """
    # 1. Créer lot pour produit
    response = client.post(
        "/api/v2/inventory/lots",
        json=sample_lot_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    lot = response.json()

    # 2. Récupérer lots du produit
    response = client.get(
        f"/api/v2/inventory/lots?product_id={sample_product.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    lots = response.json()
    assert any(l["id"] == lot["id"] for l in lots)


def test_workflow_product_with_serial(
    client,
    auth_headers,
    sample_serial_product,
    sample_serial_data
):
    """
    Test workflow: créer produit avec numéros de série
    """
    # 1. Créer numéro de série
    response = client.post(
        "/api/v2/inventory/serials",
        json=sample_serial_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    serial = response.json()

    # 2. Récupérer le numéro de série
    response = client.get(
        f"/api/v2/inventory/serials/{serial['id']}",
        headers=auth_headers
    )
    assert response.status_code == 200
    retrieved = response.json()
    assert retrieved["product_id"] == str(sample_serial_product.id)


# ============================================================================
# TESTS SÉCURITÉ & ISOLATION TENANT
# ============================================================================

def test_products_tenant_isolation(client, auth_headers, db_session, tenant_id):
    """
    Test CRITIQUE: vérifier l'isolation stricte des produits par tenant
    """
    # Créer produit pour un autre tenant
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
    db_session.commit()

    # Tenter de récupérer tous les produits
    response = client.get(
        "/api/v2/inventory/products",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier qu'AUCUN produit de l'autre tenant n'est retourné
    for product in data["products"]:
        assert product["tenant_id"] == tenant_id
        assert product["tenant_id"] != "other-tenant-999"


def test_movements_tenant_isolation(client, auth_headers, db_session, tenant_id):
    """
    Test CRITIQUE: isolation des mouvements de stock par tenant
    """
    # Créer mouvement pour autre tenant
    other_movement = StockMovement(
        id=uuid4(),
        tenant_id="other-tenant-999",
        reference="OTHER-MVT",
        movement_type=MovementType.IN,
        quantity=Decimal("10"),
        status=MovementStatus.CONFIRMED,
        date=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    db_session.add(other_movement)
    db_session.commit()

    # Récupérer mouvements
    response = client.get(
        "/api/v2/inventory/movements",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier isolation
    for movement in data["movements"]:
        assert movement["tenant_id"] == tenant_id


def test_warehouses_tenant_isolation(client, auth_headers, db_session, tenant_id):
    """
    Test CRITIQUE: isolation des entrepôts par tenant
    """
    # Créer entrepôt pour autre tenant
    other_warehouse = Warehouse(
        id=uuid4(),
        tenant_id="other-tenant-999",
        code="OTHER-WH",
        name="Other Warehouse",
        warehouse_type=WarehouseType.INTERNAL,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(other_warehouse)
    db_session.commit()

    # Récupérer entrepôts
    response = client.get(
        "/api/v2/inventory/warehouses",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier isolation
    for warehouse in data:
        assert warehouse["tenant_id"] == tenant_id


# ============================================================================
# TESTS ERREURS & CAS LIMITES
# ============================================================================

def test_get_nonexistent_product(client, auth_headers):
    """Test récupération d'un produit inexistant"""
    fake_id = uuid4()
    response = client.get(
        f"/api/v2/inventory/products/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404
    assert "non trouvé" in response.json()["detail"].lower()


def test_get_nonexistent_warehouse(client, auth_headers):
    """Test récupération d'un entrepôt inexistant"""
    fake_id = uuid4()
    response = client.get(
        f"/api/v2/inventory/warehouses/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


def test_get_nonexistent_movement(client, auth_headers):
    """Test récupération d'un mouvement inexistant"""
    fake_id = uuid4()
    response = client.get(
        f"/api/v2/inventory/movements/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


def test_get_nonexistent_picking(client, auth_headers):
    """Test récupération d'une préparation inexistante"""
    fake_id = uuid4()
    response = client.get(
        f"/api/v2/inventory/pickings/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


def test_get_nonexistent_lot(client, auth_headers):
    """Test récupération d'un lot inexistant"""
    fake_id = uuid4()
    response = client.get(
        f"/api/v2/inventory/lots/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


def test_create_product_duplicate_sku(client, auth_headers, sample_product):
    """Test création produit avec SKU dupliqué (devrait échouer)"""
    duplicate_data = {
        "sku": sample_product.sku,  # SKU existant
        "name": "Duplicate Product",
        "product_type": "STOCKABLE",
        "status": "ACTIVE",
        "unit_price": 50.00
    }

    response = client.post(
        "/api/v2/inventory/products",
        json=duplicate_data,
        headers=auth_headers
    )

    # Devrait échouer (409 Conflict ou 400 Bad Request)
    assert response.status_code in [400, 409, 422]


def test_confirm_already_confirmed_movement(client, auth_headers, sample_movement_out):
    """Test confirmer un mouvement déjà confirmé"""
    # sample_movement_out est déjà CONFIRMED
    response = client.post(
        f"/api/v2/inventory/movements/{sample_movement_out.id}/confirm",
        headers=auth_headers
    )

    # Devrait soit réussir idempotent soit échouer avec erreur appropriée
    assert response.status_code in [200, 400, 409]


def test_create_movement_with_negative_quantity(client, auth_headers, sample_product, sample_location):
    """Test création mouvement avec quantité négative (devrait échouer)"""
    invalid_data = {
        "movement_type": "IN",
        "product_id": str(sample_product.id),
        "quantity": -50,  # Quantité négative invalide
        "destination_location_id": str(sample_location.id)
    }

    response = client.post(
        "/api/v2/inventory/movements",
        json=invalid_data,
        headers=auth_headers
    )

    # Devrait échouer (validation)
    assert response.status_code in [400, 422]


# ============================================================================
# TESTS PAGINATION & FILTRES
# ============================================================================

def test_list_products_pagination(client, auth_headers, sample_product):
    """Test pagination de la liste des produits"""
    # Page 1
    response = client.get(
        "/api/v2/inventory/products?page=1&page_size=10",
        headers=auth_headers
    )
    assert response.status_code == 200
    page1 = response.json()
    assert page1["page"] == 1
    assert page1["page_size"] == 10

    # Page 2
    response = client.get(
        "/api/v2/inventory/products?page=2&page_size=10",
        headers=auth_headers
    )
    assert response.status_code == 200
    page2 = response.json()
    assert page2["page"] == 2


def test_list_movements_with_date_range(client, auth_headers, sample_movement_in):
    """Test liste des mouvements avec filtre de dates"""
    from_date = (date.today() - timedelta(days=7)).isoformat()
    to_date = date.today().isoformat()

    response = client.get(
        f"/api/v2/inventory/movements?from_date={from_date}&to_date={to_date}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["movements"], list)


def test_list_pickings_by_assigned_user(client, auth_headers, user_id):
    """Test liste des préparations filtrées par utilisateur assigné"""
    response = client.get(
        f"/api/v2/inventory/pickings?assigned_to={user_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for picking in data:
        if picking.get("assigned_to"):
            assert picking["assigned_to"] == user_id


def test_list_lots_by_status(client, auth_headers, sample_lot):
    """Test liste des lots filtrés par statut"""
    response = client.get(
        f"/api/v2/inventory/lots?status={sample_lot.status.value}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for lot in data:
        assert lot["status"] == sample_lot.status.value


# ============================================================================
# TESTS BUSINESS LOGIC
# ============================================================================

def test_product_status_transitions(client, auth_headers, sample_product):
    """Test transitions de statut produit"""
    # Activer produit
    response = client.post(
        f"/api/v2/inventory/products/{sample_product.id}/activate",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ACTIVE"


def test_warehouse_stock_summary(client, auth_headers, sample_warehouse):
    """Test récupération du résumé de stock d'un entrepôt"""
    response = client.get(
        f"/api/v2/inventory/warehouses/{sample_warehouse.id}/stock",
        headers=auth_headers
    )

    assert response.status_code == 200
    stock_data = response.json()

    # Vérifier structure
    assert isinstance(stock_data, list)


def test_product_stock_levels(client, auth_headers, sample_product):
    """Test récupération des niveaux de stock d'un produit"""
    response = client.get(
        f"/api/v2/inventory/products/{sample_product.id}/stock",
        headers=auth_headers
    )

    assert response.status_code == 200
    stock_levels = response.json()

    # Vérifier structure
    assert isinstance(stock_levels, list)


def test_inventory_count_by_warehouse(client, auth_headers, sample_warehouse, sample_inventory_count):
    """Test liste des inventaires filtrés par entrepôt"""
    response = client.get(
        f"/api/v2/inventory/counts?warehouse_id={sample_warehouse.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for count in data:
        assert count["warehouse_id"] == str(sample_warehouse.id)


def test_inventory_count_by_status(client, auth_headers, sample_inventory_count):
    """Test liste des inventaires filtrés par statut"""
    response = client.get(
        f"/api/v2/inventory/counts?status={InventoryStatus.DRAFT.value}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for count in data:
        assert count["status"] == InventoryStatus.DRAFT.value


# ============================================================================
# TESTS CATÉGORIES HIÉRARCHIQUES
# ============================================================================

def test_list_categories_with_parent(client, auth_headers, sample_category, sample_subcategory):
    """Test liste des catégories filtrées par parent"""
    response = client.get(
        f"/api/v2/inventory/categories?parent_id={sample_category.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier que toutes les catégories retournées ont le bon parent
    for category in data:
        assert category["parent_id"] == str(sample_category.id)


def test_create_subcategory(client, auth_headers, tenant_id, sample_category):
    """Test création d'une sous-catégorie"""
    subcategory_data = {
        "code": "SUB-CAT",
        "name": "Subcategory",
        "parent_id": str(sample_category.id)
    }

    response = client.post(
        "/api/v2/inventory/categories",
        json=subcategory_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["parent_id"] == str(sample_category.id)
    assert data["tenant_id"] == tenant_id


# ============================================================================
# TESTS TRAÇABILITÉ LOT/SÉRIE
# ============================================================================

def test_lot_expiration_tracking(client, auth_headers, sample_lot):
    """Test suivi de l'expiration des lots"""
    response = client.get(
        f"/api/v2/inventory/lots/{sample_lot.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier présence dates de traçabilité
    assert "manufacturing_date" in data
    assert "expiration_date" in data
    assert "status" in data


def test_serial_number_uniqueness(client, auth_headers, sample_serial_product):
    """Test unicité des numéros de série"""
    serial_data = {
        "product_id": str(sample_serial_product.id),
        "serial_number": "UNIQUE-SN-001"
    }

    # Créer premier numéro de série
    response1 = client.post(
        "/api/v2/inventory/serials",
        json=serial_data,
        headers=auth_headers
    )
    assert response1.status_code == 201

    # Tenter de créer doublon (devrait échouer)
    response2 = client.post(
        "/api/v2/inventory/serials",
        json=serial_data,
        headers=auth_headers
    )
    # Devrait échouer (409 Conflict ou 400 Bad Request)
    assert response2.status_code in [400, 409, 422]


# ============================================================================
# TESTS PERFORMANCE & VOLUME
# ============================================================================

def test_list_products_large_dataset(client, auth_headers, sample_product):
    """Test liste des produits avec pagination haute"""
    response = client.get(
        "/api/v2/inventory/products?page=1&page_size=100",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier réponse raisonnable
    assert "products" in data
    assert len(data["products"]) <= 100


def test_list_movements_with_multiple_filters(client, auth_headers, sample_product, sample_warehouse):
    """Test liste des mouvements avec filtres combinés"""
    response = client.get(
        f"/api/v2/inventory/movements?product_id={sample_product.id}&warehouse_id={sample_warehouse.id}&movement_type=IN",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier que tous les filtres sont appliqués
    for movement in data["movements"]:
        assert movement["product_id"] == str(sample_product.id)
        assert movement["movement_type"] == "IN"
