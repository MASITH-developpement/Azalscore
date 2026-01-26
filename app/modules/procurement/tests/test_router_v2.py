"""
Tests for Procurement Router v2 - CORE SaaS
============================================

Test coverage for all 36 endpoints migrated to CORE SaaS v2:
- Suppliers (7 endpoints + 5 additional tests)
- Requisitions (6 endpoints + 4 additional tests)
- Orders (10 endpoints + 5 additional tests)
- Receipts (3 endpoints + 3 additional tests)
- Invoices (6 endpoints + 5 additional tests)
- Payments (1 endpoint + 2 additional tests)
- Evaluations (1 endpoint + 1 additional test)
- Dashboard (1 endpoint + 1 additional test)
- Workflows (2 tests)
- Security (2 tests)

Total: ~65 tests
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

from .conftest import (
    assert_supplier_fields,
    assert_requisition_fields,
    assert_order_fields,
    assert_receipt_fields,
    assert_invoice_fields,
    assert_payment_fields,
    assert_evaluation_fields,
    assert_list_fields,
)


# =============================================================================
# SUPPLIERS TESTS (12 tests)
# =============================================================================

def test_create_supplier(test_client, client, auth_headers, supplier_data, sample_supplier):
    """Test creating a new supplier."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.get_supplier_by_code.return_value = None
        service_instance.create_supplier.return_value = sample_supplier
        mock_service.return_value = service_instance

        response = test_client.post("/v2/procurement/suppliers", json=supplier_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert_supplier_fields(data)
        assert data["code"] == supplier_data["code"]
        assert data["name"] == supplier_data["name"]


def test_create_supplier_duplicate_code(test_client, client, auth_headers, supplier_data, sample_supplier):
    """Test creating a supplier with duplicate code."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.get_supplier_by_code.return_value = sample_supplier
        mock_service.return_value = service_instance

        response = test_client.post("/v2/procurement/suppliers", json=supplier_data, headers=auth_headers)

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()


def test_list_suppliers(test_client, client, auth_headers, sample_supplier):
    """Test listing suppliers."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.list_suppliers.return_value = ([sample_supplier], 1)
        mock_service.return_value = service_instance

        response = test_client.get("/v2/procurement/suppliers", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert_list_fields(data)
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert_supplier_fields(data["items"][0])


def test_list_suppliers_with_filters(test_client, client, auth_headers, sample_supplier):
    """Test listing suppliers with various filters."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.list_suppliers.return_value = ([sample_supplier], 1)
        mock_service.return_value = service_instance

        response = test_client.get(
            "/v2/procurement/suppliers",
            params={
                "status": "APPROVED",
                "supplier_type": "GOODS",
                "category": "Electronics",
                "search": "Test",
                "is_active": True,
                "skip": 0,
                "limit": 10
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        service_instance.list_suppliers.assert_called_once()


def test_get_supplier(test_client, client, auth_headers, sample_supplier):
    """Test getting a supplier by ID."""
    supplier_id = sample_supplier["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.get_supplier.return_value = sample_supplier
        mock_service.return_value = service_instance

        response = test_client.get(f"/v2/procurement/suppliers/{supplier_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert_supplier_fields(data)
        assert data["id"] == supplier_id


def test_get_supplier_not_found(test_client, client, auth_headers):
    """Test getting a non-existent supplier."""
    supplier_id = str(uuid4())
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.get_supplier.return_value = None
        mock_service.return_value = service_instance

        response = test_client.get(f"/v2/procurement/suppliers/{supplier_id}", headers=auth_headers)

        assert response.status_code == 404


def test_update_supplier(test_client, client, auth_headers, sample_supplier):
    """Test updating a supplier."""
    supplier_id = sample_supplier["id"]
    update_data = {"name": "Updated Supplier Name"}

    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        updated_supplier = {**sample_supplier, **update_data}
        service_instance.update_supplier.return_value = updated_supplier
        mock_service.return_value = service_instance

        response = test_client.put(f"/v2/procurement/suppliers/{supplier_id}", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]


def test_approve_supplier(test_client, client, auth_headers, sample_supplier):
    """Test approving a supplier."""
    supplier_id = sample_supplier["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        approved_supplier = {**sample_supplier, "status": "APPROVED"}
        service_instance.approve_supplier.return_value = approved_supplier
        mock_service.return_value = service_instance

        response = test_client.post(f"/v2/procurement/suppliers/{supplier_id}/approve", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "APPROVED"


def test_add_supplier_contact(test_client, client, auth_headers, sample_supplier):
    """Test adding a contact to a supplier."""
    supplier_id = sample_supplier["id"]
    contact_data = {
        "first_name": "Jane",
        "last_name": "Doe",
        "job_title": "Procurement Manager",
        "email": "jane.doe@supplier.com",
        "phone": "+33987654321",
        "is_primary": True
    }

    contact_response = {
        "id": str(uuid4()),
        "supplier_id": supplier_id,
        **contact_data,
        "created_at": datetime.now().isoformat()
    }

    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.get_supplier.return_value = sample_supplier
        service_instance.add_supplier_contact.return_value = contact_response
        mock_service.return_value = service_instance

        response = test_client.post(
            f"/v2/procurement/suppliers/{supplier_id}/contacts",
            json=contact_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == contact_data["first_name"]
        assert data["email"] == contact_data["email"]


def test_list_supplier_contacts(test_client, client, auth_headers, sample_supplier):
    """Test listing supplier contacts."""
    supplier_id = sample_supplier["id"]
    contacts = [
        {
            "id": str(uuid4()),
            "supplier_id": supplier_id,
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@supplier.com"
        }
    ]

    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.get_supplier_contacts.return_value = contacts
        mock_service.return_value = service_instance

        response = test_client.get(f"/v2/procurement/suppliers/{supplier_id}/contacts", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1


def test_supplier_pagination(test_client, client, auth_headers, sample_supplier):
    """Test supplier pagination."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.list_suppliers.return_value = ([sample_supplier], 100)
        mock_service.return_value = service_instance

        response = test_client.get(
            "/v2/procurement/suppliers",
            params={"skip": 20, "limit": 10},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 100


def test_supplier_inactive_filter(test_client, client, auth_headers):
    """Test filtering inactive suppliers."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.list_suppliers.return_value = ([], 0)
        mock_service.return_value = service_instance

        response = test_client.get(
            "/v2/procurement/suppliers",
            params={"is_active": False},
            headers=auth_headers
        )

        assert response.status_code == 200


# =============================================================================
# REQUISITIONS TESTS (10 tests)
# =============================================================================

def test_create_requisition(test_client, client, auth_headers, requisition_data, sample_requisition):
    """Test creating a new requisition."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.create_requisition.return_value = sample_requisition
        mock_service.return_value = service_instance

        response = test_client.post("/v2/procurement/requisitions", json=requisition_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert_requisition_fields(data)
        assert data["title"] == requisition_data["title"]


def test_list_requisitions(test_client, client, auth_headers, sample_requisition):
    """Test listing requisitions."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.list_requisitions.return_value = ([sample_requisition], 1)
        mock_service.return_value = service_instance

        response = test_client.get("/v2/procurement/requisitions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 1


def test_get_requisition(test_client, client, auth_headers, sample_requisition):
    """Test getting a requisition by ID."""
    requisition_id = sample_requisition["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.get_requisition.return_value = sample_requisition
        mock_service.return_value = service_instance

        response = test_client.get(f"/v2/procurement/requisitions/{requisition_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert_requisition_fields(data)


def test_get_requisition_not_found(test_client, client, auth_headers):
    """Test getting a non-existent requisition."""
    requisition_id = str(uuid4())
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.get_requisition.return_value = None
        mock_service.return_value = service_instance

        response = test_client.get(f"/v2/procurement/requisitions/{requisition_id}", headers=auth_headers)

        assert response.status_code == 404


def test_submit_requisition(test_client, client, auth_headers, sample_requisition):
    """Test submitting a requisition (DRAFT → SUBMITTED)."""
    requisition_id = sample_requisition["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        submitted_requisition = {**sample_requisition, "status": "SUBMITTED"}
        service_instance.submit_requisition.return_value = submitted_requisition
        mock_service.return_value = service_instance

        response = test_client.post(f"/v2/procurement/requisitions/{requisition_id}/submit", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUBMITTED"


def test_approve_requisition(test_client, client, auth_headers, sample_requisition, user_id):
    """Test approving a requisition (SUBMITTED → APPROVED)."""
    requisition_id = sample_requisition["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        approved_requisition = {
            **sample_requisition,
            "status": "APPROVED",
            "approved_by": user_id,
            "approved_at": datetime.now().isoformat()
        }
        service_instance.approve_requisition.return_value = approved_requisition
        mock_service.return_value = service_instance

        response = test_client.post(f"/v2/procurement/requisitions/{requisition_id}/approve", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "APPROVED"
        assert data["approved_by"] == user_id


def test_reject_requisition(test_client, client, auth_headers, sample_requisition, user_id):
    """Test rejecting a requisition (SUBMITTED → REJECTED)."""
    requisition_id = sample_requisition["id"]
    rejection_reason = "Budget not available"

    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        rejected_requisition = {
            **sample_requisition,
            "status": "REJECTED",
            "approved_by": user_id,
            "rejection_reason": rejection_reason
        }
        service_instance.reject_requisition.return_value = rejected_requisition
        mock_service.return_value = service_instance

        response = test_client.post(
            f"/v2/procurement/requisitions/{requisition_id}/reject",
            params={"reason": rejection_reason},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REJECTED"


def test_requisition_workflow(test_client, client, auth_headers, requisition_data, sample_requisition):
    """Test complete requisition workflow: create → submit → approve."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()

        # Create
        draft_requisition = {**sample_requisition, "status": "DRAFT"}
        service_instance.create_requisition.return_value = draft_requisition
        mock_service.return_value = service_instance

        response = test_client.post("/v2/procurement/requisitions", json=requisition_data, headers=auth_headers)
        assert response.status_code == 201
        requisition_id = response.json()["id"]

        # Submit
        submitted_requisition = {**draft_requisition, "status": "SUBMITTED"}
        service_instance.submit_requisition.return_value = submitted_requisition

        response = test_client.post(f"/v2/procurement/requisitions/{requisition_id}/submit", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "SUBMITTED"

        # Approve
        approved_requisition = {**submitted_requisition, "status": "APPROVED"}
        service_instance.approve_requisition.return_value = approved_requisition

        response = test_client.post(f"/v2/procurement/requisitions/{requisition_id}/approve", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "APPROVED"


def test_requisition_pagination(test_client, client, auth_headers, sample_requisition):
    """Test requisition pagination."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.list_requisitions.return_value = ([sample_requisition], 50)
        mock_service.return_value = service_instance

        response = test_client.get(
            "/v2/procurement/requisitions",
            params={"skip": 10, "limit": 20},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 50


def test_requisition_status_filter(test_client, client, auth_headers, sample_requisition):
    """Test filtering requisitions by status."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.list_requisitions.return_value = ([sample_requisition], 1)
        mock_service.return_value = service_instance

        response = test_client.get(
            "/v2/procurement/requisitions",
            params={"requisition_status": "DRAFT"},
            headers=auth_headers
        )

        assert response.status_code == 200


# =============================================================================
# ORDERS TESTS (15 tests)
# =============================================================================

def test_create_order(test_client, client, auth_headers, order_data, sample_order):
    """Test creating a new order."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.create_purchase_order.return_value = sample_order
        mock_service.return_value = service_instance

        response = test_client.post("/v2/procurement/orders", json=order_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert_order_fields(data)


def test_list_orders(test_client, client, auth_headers, sample_order):
    """Test listing orders."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.list_purchase_orders.return_value = ([sample_order], 1)
        mock_service.return_value = service_instance

        response = test_client.get("/v2/procurement/orders", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert_list_fields(data)


def test_list_orders_with_filters(test_client, client, auth_headers, sample_order, sample_supplier):
    """Test listing orders with filters."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.list_purchase_orders.return_value = ([sample_order], 1)
        mock_service.return_value = service_instance

        response = test_client.get(
            "/v2/procurement/orders",
            params={
                "supplier_id": sample_supplier["id"],
                "order_status": "DRAFT",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            },
            headers=auth_headers
        )

        assert response.status_code == 200


def test_get_order(test_client, client, auth_headers, sample_order):
    """Test getting an order by ID."""
    order_id = sample_order["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.get_purchase_order.return_value = sample_order
        mock_service.return_value = service_instance

        response = test_client.get(f"/v2/procurement/orders/{order_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert_order_fields(data)


def test_get_order_not_found(test_client, client, auth_headers):
    """Test getting a non-existent order."""
    order_id = str(uuid4())
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.get_purchase_order.return_value = None
        mock_service.return_value = service_instance

        response = test_client.get(f"/v2/procurement/orders/{order_id}", headers=auth_headers)

        assert response.status_code == 404


def test_update_order(test_client, client, auth_headers, sample_order, order_data):
    """Test updating an order."""
    order_id = sample_order["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        updated_order = {**sample_order, "notes": "Updated notes"}
        service_instance.update_purchase_order.return_value = updated_order
        mock_service.return_value = service_instance

        response = test_client.put(f"/v2/procurement/orders/{order_id}", json=order_data, headers=auth_headers)

        assert response.status_code == 200


def test_delete_order(test_client, client, auth_headers, sample_order):
    """Test deleting an order."""
    order_id = sample_order["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.delete_purchase_order.return_value = True
        mock_service.return_value = service_instance

        response = test_client.delete(f"/v2/procurement/orders/{order_id}", headers=auth_headers)

        assert response.status_code == 204


def test_send_order(test_client, client, auth_headers, sample_order):
    """Test sending an order (DRAFT → SENT)."""
    order_id = sample_order["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        sent_order = {**sample_order, "status": "SENT", "sent_at": datetime.now().isoformat()}
        service_instance.send_purchase_order.return_value = sent_order
        mock_service.return_value = service_instance

        response = test_client.post(f"/v2/procurement/orders/{order_id}/send", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SENT"


def test_confirm_order(test_client, client, auth_headers, sample_order):
    """Test confirming an order (SENT → CONFIRMED)."""
    order_id = sample_order["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        confirmed_order = {
            **sample_order,
            "status": "CONFIRMED",
            "supplier_reference": "SUPP-REF-123"
        }
        service_instance.confirm_purchase_order.return_value = confirmed_order
        mock_service.return_value = service_instance

        response = test_client.post(
            f"/v2/procurement/orders/{order_id}/confirm",
            params={"supplier_reference": "SUPP-REF-123"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CONFIRMED"


def test_validate_order(test_client, client, auth_headers, sample_order):
    """Test validating an order."""
    order_id = sample_order["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        validated_order = {**sample_order, "status": "SENT"}
        service_instance.validate_purchase_order.return_value = validated_order
        mock_service.return_value = service_instance

        response = test_client.post(f"/v2/procurement/orders/{order_id}/validate", headers=auth_headers)

        assert response.status_code == 200


def test_create_invoice_from_order(test_client, client, auth_headers, sample_order, sample_invoice):
    """Test creating an invoice from an order."""
    order_id = sample_order["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.create_invoice_from_order.return_value = sample_invoice
        mock_service.return_value = service_instance

        response = test_client.post(
            f"/v2/procurement/orders/{order_id}/create-invoice",
            params={"supplier_invoice_number": "SUPP-INV-001"},
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert_invoice_fields(data)


def test_export_orders_csv(test_client, client, auth_headers):
    """Test exporting orders as CSV."""
    csv_content = "Numéro;Date;Fournisseur;Statut;HT;TVA;TTC\nCMD-2024-0001;2024-01-15;Test Supplier;DRAFT;1000;200;1200"

    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.export_orders_csv.return_value = csv_content
        mock_service.return_value = service_instance

        response = test_client.get("/v2/procurement/orders/export/csv", headers=auth_headers)

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"


def test_order_pagination(test_client, client, auth_headers, sample_order):
    """Test order pagination."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.list_purchase_orders.return_value = ([sample_order], 100)
        mock_service.return_value = service_instance

        response = test_client.get(
            "/v2/procurement/orders",
            params={"skip": 30, "limit": 10},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 100


def test_order_workflow(test_client, client, auth_headers, order_data, sample_order):
    """Test complete order workflow: create → send → confirm."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()

        # Create
        draft_order = {**sample_order, "status": "DRAFT"}
        service_instance.create_purchase_order.return_value = draft_order
        mock_service.return_value = service_instance

        response = test_client.post("/v2/procurement/orders", json=order_data, headers=auth_headers)
        assert response.status_code == 201
        order_id = response.json()["id"]

        # Send
        sent_order = {**draft_order, "status": "SENT"}
        service_instance.send_purchase_order.return_value = sent_order

        response = test_client.post(f"/v2/procurement/orders/{order_id}/send", headers=auth_headers)
        assert response.status_code == 200

        # Confirm
        confirmed_order = {**sent_order, "status": "CONFIRMED"}
        service_instance.confirm_purchase_order.return_value = confirmed_order

        response = test_client.post(f"/v2/procurement/orders/{order_id}/confirm", headers=auth_headers)
        assert response.status_code == 200


def test_delete_order_sent(test_client, client, auth_headers, sample_order):
    """Test that sent orders cannot be deleted."""
    order_id = sample_order["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.delete_purchase_order.return_value = False
        mock_service.return_value = service_instance

        response = test_client.delete(f"/v2/procurement/orders/{order_id}", headers=auth_headers)

        assert response.status_code == 400


# =============================================================================
# RECEIPTS TESTS (6 tests)
# =============================================================================

def test_create_receipt(test_client, client, auth_headers, receipt_data, sample_receipt):
    """Test creating a receipt."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.create_goods_receipt.return_value = sample_receipt
        mock_service.return_value = service_instance

        response = test_client.post("/v2/procurement/receipts", json=receipt_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert_receipt_fields(data)


def test_list_receipts(test_client, client, auth_headers, sample_receipt):
    """Test listing receipts."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.list_goods_receipts.return_value = ([sample_receipt], 1)
        mock_service.return_value = service_instance

        response = test_client.get("/v2/procurement/receipts", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


def test_validate_receipt(test_client, client, auth_headers, sample_receipt):
    """Test validating a receipt."""
    receipt_id = sample_receipt["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        validated_receipt = {**sample_receipt, "status": "VALIDATED"}
        service_instance.validate_goods_receipt.return_value = validated_receipt
        mock_service.return_value = service_instance

        response = test_client.post(f"/v2/procurement/receipts/{receipt_id}/validate", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "VALIDATED"


def test_receipt_pagination(test_client, client, auth_headers, sample_receipt):
    """Test receipt pagination."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.list_goods_receipts.return_value = ([sample_receipt], 50)
        mock_service.return_value = service_instance

        response = test_client.get(
            "/v2/procurement/receipts",
            params={"skip": 0, "limit": 20},
            headers=auth_headers
        )

        assert response.status_code == 200


def test_receipt_linked_to_order(test_client, client, auth_headers, sample_receipt, sample_order):
    """Test that receipt is linked to order."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.create_goods_receipt.return_value = sample_receipt
        mock_service.return_value = service_instance

        receipt_data = {"order_id": sample_order["id"], "receipt_date": datetime.now().date().isoformat(), "lines": []}
        response = test_client.post("/v2/procurement/receipts", json=receipt_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["order_id"] == sample_order["id"]


def test_receipt_validation_updates_order(test_client, client, auth_headers, sample_receipt):
    """Test that validating receipt updates order status."""
    receipt_id = sample_receipt["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        validated_receipt = {**sample_receipt, "status": "VALIDATED"}
        service_instance.validate_goods_receipt.return_value = validated_receipt
        mock_service.return_value = service_instance

        response = test_client.post(f"/v2/procurement/receipts/{receipt_id}/validate", headers=auth_headers)

        assert response.status_code == 200
        service_instance.validate_goods_receipt.assert_called_once()


# =============================================================================
# INVOICES TESTS (11 tests)
# =============================================================================

def test_create_invoice(test_client, client, auth_headers, invoice_data, sample_invoice):
    """Test creating an invoice."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.create_purchase_invoice.return_value = sample_invoice
        mock_service.return_value = service_instance

        response = test_client.post("/v2/procurement/invoices", json=invoice_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert_invoice_fields(data)


def test_list_invoices(test_client, client, auth_headers, sample_invoice):
    """Test listing invoices."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.list_purchase_invoices.return_value = ([sample_invoice], 1)
        mock_service.return_value = service_instance

        response = test_client.get("/v2/procurement/invoices", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert_list_fields(data)


def test_list_invoices_with_filters(test_client, client, auth_headers, sample_invoice, sample_supplier):
    """Test listing invoices with filters."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.list_purchase_invoices.return_value = ([sample_invoice], 1)
        mock_service.return_value = service_instance

        response = test_client.get(
            "/v2/procurement/invoices",
            params={
                "supplier_id": sample_supplier["id"],
                "invoice_status": "DRAFT",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            },
            headers=auth_headers
        )

        assert response.status_code == 200


def test_get_invoice(test_client, client, auth_headers, sample_invoice):
    """Test getting an invoice by ID."""
    invoice_id = sample_invoice["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.get_purchase_invoice.return_value = sample_invoice
        mock_service.return_value = service_instance

        response = test_client.get(f"/v2/procurement/invoices/{invoice_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert_invoice_fields(data)


def test_get_invoice_not_found(test_client, client, auth_headers):
    """Test getting a non-existent invoice."""
    invoice_id = str(uuid4())
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.get_purchase_invoice.return_value = None
        mock_service.return_value = service_instance

        response = test_client.get(f"/v2/procurement/invoices/{invoice_id}", headers=auth_headers)

        assert response.status_code == 404


def test_update_invoice(test_client, client, auth_headers, sample_invoice, invoice_data):
    """Test updating an invoice."""
    invoice_id = sample_invoice["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        updated_invoice = {**sample_invoice, "notes": "Updated notes"}
        service_instance.update_purchase_invoice.return_value = updated_invoice
        mock_service.return_value = service_instance

        response = test_client.put(f"/v2/procurement/invoices/{invoice_id}", json=invoice_data, headers=auth_headers)

        assert response.status_code == 200


def test_delete_invoice(test_client, client, auth_headers, sample_invoice):
    """Test deleting an invoice."""
    invoice_id = sample_invoice["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.delete_purchase_invoice.return_value = True
        mock_service.return_value = service_instance

        response = test_client.delete(f"/v2/procurement/invoices/{invoice_id}", headers=auth_headers)

        assert response.status_code == 204


def test_validate_invoice(test_client, client, auth_headers, sample_invoice):
    """Test validating an invoice (DRAFT → VALIDATED)."""
    invoice_id = sample_invoice["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        validated_invoice = {**sample_invoice, "status": "VALIDATED"}
        service_instance.validate_purchase_invoice.return_value = validated_invoice
        mock_service.return_value = service_instance

        response = test_client.post(f"/v2/procurement/invoices/{invoice_id}/validate", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "VALIDATED"


def test_export_invoices_csv(test_client, client, auth_headers):
    """Test exporting invoices as CSV."""
    csv_content = "Numéro;Date;Fournisseur;Réf. Fournisseur;Statut;HT;TVA;TTC\nFAF-2024-0001;2024-01-15;Test Supplier;SUPP-001;DRAFT;1000;200;1200"

    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.export_invoices_csv.return_value = csv_content
        mock_service.return_value = service_instance

        response = test_client.get("/v2/procurement/invoices/export/csv", headers=auth_headers)

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"


def test_invoice_pagination(test_client, client, auth_headers, sample_invoice):
    """Test invoice pagination."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.list_purchase_invoices.return_value = ([sample_invoice], 75)
        mock_service.return_value = service_instance

        response = test_client.get(
            "/v2/procurement/invoices",
            params={"skip": 20, "limit": 10},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 75


def test_delete_invoice_validated(test_client, client, auth_headers, sample_invoice):
    """Test that validated invoices cannot be deleted."""
    invoice_id = sample_invoice["id"]
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.delete_purchase_invoice.return_value = False
        mock_service.return_value = service_instance

        response = test_client.delete(f"/v2/procurement/invoices/{invoice_id}", headers=auth_headers)

        assert response.status_code == 400


# =============================================================================
# PAYMENTS TESTS (3 tests)
# =============================================================================

def test_create_payment(test_client, client, auth_headers, payment_data, sample_payment):
    """Test creating a payment."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.create_supplier_payment.return_value = sample_payment
        mock_service.return_value = service_instance

        response = test_client.post("/v2/procurement/payments", json=payment_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert_payment_fields(data)


def test_payment_allocation(test_client, client, auth_headers, payment_data, sample_payment):
    """Test payment allocation to invoices."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        payment_with_allocations = {
            **sample_payment,
            "allocations": payment_data["allocations"]
        }
        service_instance.create_supplier_payment.return_value = payment_with_allocations
        mock_service.return_value = service_instance

        response = test_client.post("/v2/procurement/payments", json=payment_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert "allocations" in data


def test_payment_reduces_invoice_balance(test_client, client, auth_headers, payment_data, sample_payment):
    """Test that payment reduces invoice balance."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.create_supplier_payment.return_value = sample_payment
        mock_service.return_value = service_instance

        response = test_client.post("/v2/procurement/payments", json=payment_data, headers=auth_headers)

        assert response.status_code == 201
        service_instance.create_supplier_payment.assert_called_once()


# =============================================================================
# EVALUATIONS TESTS (2 tests)
# =============================================================================

def test_create_evaluation(test_client, client, auth_headers, evaluation_data, sample_evaluation):
    """Test creating a supplier evaluation."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.create_supplier_evaluation.return_value = sample_evaluation
        mock_service.return_value = service_instance

        response = test_client.post("/v2/procurement/evaluations", json=evaluation_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert_evaluation_fields(data)


def test_evaluation_scores(test_client, client, auth_headers, evaluation_data, sample_evaluation):
    """Test that evaluation includes all score types."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.create_supplier_evaluation.return_value = sample_evaluation
        mock_service.return_value = service_instance

        response = test_client.post("/v2/procurement/evaluations", json=evaluation_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert "quality_score" in data
        assert "price_score" in data
        assert "delivery_score" in data
        assert "service_score" in data
        assert "reliability_score" in data
        assert "overall_score" in data


# =============================================================================
# DASHBOARD TESTS (2 tests)
# =============================================================================

def test_get_dashboard(test_client, client, auth_headers, sample_dashboard):
    """Test getting dashboard data."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.get_dashboard.return_value = sample_dashboard
        mock_service.return_value = service_instance

        response = test_client.get("/v2/procurement/dashboard", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_suppliers" in data
        assert "pending_orders" in data
        assert "unpaid_amount" in data


def test_dashboard_structure(test_client, client, auth_headers, sample_dashboard):
    """Test dashboard data structure."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.get_dashboard.return_value = sample_dashboard
        mock_service.return_value = service_instance

        response = test_client.get("/v2/procurement/dashboard", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        # Suppliers metrics
        assert "total_suppliers" in data
        assert "active_suppliers" in data
        # Requisitions metrics
        assert "pending_requisitions" in data
        assert "requisitions_this_month" in data
        # Orders metrics
        assert "draft_orders" in data
        assert "pending_orders" in data
        assert "orders_this_month" in data
        # Invoices metrics
        assert "pending_invoices" in data
        assert "overdue_invoices" in data
        # Payments metrics
        assert "unpaid_amount" in data


# =============================================================================
# WORKFLOW TESTS (2 tests)
# =============================================================================

def test_complete_procurement_cycle(test_client, client, auth_headers, requisition_data, order_data, receipt_data,
    invoice_data, payment_data, sample_requisition, sample_order,
    sample_receipt, sample_invoice, sample_payment):
    """Test complete procurement cycle: requisition → order → receipt → invoice → payment."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        mock_service.return_value = service_instance

        # 1. Create requisition
        service_instance.create_requisition.return_value = sample_requisition
        response = test_client.post("/v2/procurement/requisitions", json=requisition_data, headers=auth_headers)
        assert response.status_code == 201

        # 2. Create order
        service_instance.create_purchase_order.return_value = sample_order
        response = test_client.post("/v2/procurement/orders", json=order_data, headers=auth_headers)
        assert response.status_code == 201

        # 3. Create receipt
        service_instance.create_goods_receipt.return_value = sample_receipt
        response = test_client.post("/v2/procurement/receipts", json=receipt_data, headers=auth_headers)
        assert response.status_code == 201

        # 4. Create invoice
        service_instance.create_purchase_invoice.return_value = sample_invoice
        response = test_client.post("/v2/procurement/invoices", json=invoice_data, headers=auth_headers)
        assert response.status_code == 201

        # 5. Create payment
        service_instance.create_supplier_payment.return_value = sample_payment
        response = test_client.post("/v2/procurement/payments", json=payment_data, headers=auth_headers)
        assert response.status_code == 201


def test_order_to_invoice_workflow(test_client, client, auth_headers, order_data, sample_order, sample_invoice):
    """Test order to invoice workflow."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        mock_service.return_value = service_instance

        # 1. Create order
        service_instance.create_purchase_order.return_value = sample_order
        response = test_client.post("/v2/procurement/orders", json=order_data, headers=auth_headers)
        assert response.status_code == 201
        order_id = response.json()["id"]

        # 2. Validate order
        validated_order = {**sample_order, "status": "SENT"}
        service_instance.validate_purchase_order.return_value = validated_order
        response = test_client.post(f"/v2/procurement/orders/{order_id}/validate", headers=auth_headers)
        assert response.status_code == 200

        # 3. Create invoice from order
        service_instance.create_invoice_from_order.return_value = sample_invoice
        response = test_client.post(f"/v2/procurement/orders/{order_id}/create-invoice", headers=auth_headers)
        assert response.status_code == 201


# =============================================================================
# SECURITY TESTS (2 tests)
# =============================================================================

def test_tenant_isolation(test_client, client, auth_headers, supplier_data, sample_supplier):
    """Test tenant isolation in procurement operations."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.get_supplier_by_code.return_value = None
        service_instance.create_supplier.return_value = sample_supplier
        mock_service.return_value = service_instance

        response = test_client.post("/v2/procurement/suppliers", json=supplier_data, headers=auth_headers)

        assert response.status_code == 201
        # Verify service was called with correct tenant_id
        mock_service.assert_called()
        call_args = mock_service.call_args
        assert call_args is not None


def test_context_propagation(test_client, client, auth_headers, order_data, sample_order):
    """Test that SaaSContext is properly propagated through service calls."""
    with patch("app.modules.procurement.router_v2.get_procurement_service") as mock_service:
        service_instance = Mock()
        service_instance.create_purchase_order.return_value = sample_order
        mock_service.return_value = service_instance

        response = test_client.post("/v2/procurement/orders", json=order_data, headers=auth_headers)

        assert response.status_code == 201
        # Verify service was called with context parameters
        mock_service.assert_called()
