"""
Tests for Purchases Module Router v2 - CORE SaaS

Comprehensive test coverage for:
- Suppliers (create, list, get, update, delete)
- Orders (create, list, get, update, validate, cancel, delete)
- Invoices (create, list, get, update, validate, delete)
- Summary/Dashboard
- Workflows and edge cases
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta

from .conftest import (
    assert_supplier_fields,
    assert_order_fields,
    assert_invoice_fields,
    assert_pagination_fields
)


# ============================================================================
# SUPPLIER TESTS (10 tests)
# ============================================================================

def test_create_supplier(test_client, client, auth_headers, supplier_data, sample_supplier):
    """Test creating a new supplier."""
    with patch("app.modules.purchases.service.PurchasesService.create_supplier") as mock_create:
        mock_create.return_value = MagicMock(**sample_supplier)

        response = test_client.post(
            "/v2/purchases/suppliers",
            json=supplier_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert_supplier_fields(data)
        assert data["code"] == supplier_data["code"]
        assert data["name"] == supplier_data["name"]
        assert data["status"] == "APPROVED"


def test_list_suppliers(test_client, client, auth_headers, sample_supplier):
    """Test listing suppliers."""
    with patch("app.modules.purchases.service.PurchasesService.list_suppliers") as mock_list:
        mock_list.return_value = ([MagicMock(**sample_supplier)], 1)

        response = test_client.get(
            "/v2/purchases/suppliers",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert_pagination_fields(data)
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert_supplier_fields(data["items"][0])


def test_list_suppliers_with_filters(test_client, client, auth_headers, sample_supplier):
    """Test listing suppliers with various filters."""
    with patch("app.modules.purchases.service.PurchasesService.list_suppliers") as mock_list:
        mock_list.return_value = ([MagicMock(**sample_supplier)], 1)

        # Test status filter
        response = test_client.get(
            "/v2/purchases/suppliers?status=APPROVED",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Test search filter
        response = test_client.get(
            "/v2/purchases/suppliers?search=Test",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Test is_active filter
        response = test_client.get(
            "/v2/purchases/suppliers?is_active=true",
            headers=auth_headers
        )
        assert response.status_code == 200


def test_get_supplier(test_client, client, auth_headers, sample_supplier):
    """Test getting a specific supplier."""
    supplier_id = sample_supplier["id"]

    with patch("app.modules.purchases.service.PurchasesService.get_supplier") as mock_get:
        mock_get.return_value = MagicMock(**sample_supplier)

        response = test_client.get(
            f"/v2/purchases/suppliers/{supplier_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert_supplier_fields(data)
        assert data["id"] == supplier_id


def test_get_supplier_not_found(test_client, client, auth_headers):
    """Test getting a non-existent supplier."""
    supplier_id = str(uuid4())

    with patch("app.modules.purchases.service.PurchasesService.get_supplier") as mock_get:
        mock_get.return_value = None

        response = test_client.get(
            f"/v2/purchases/suppliers/{supplier_id}",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "non trouvé" in response.json()["detail"]


def test_update_supplier(test_client, client, auth_headers, sample_supplier):
    """Test updating a supplier."""
    supplier_id = sample_supplier["id"]
    update_data = {"name": "Updated Supplier Name"}

    updated_supplier = sample_supplier.copy()
    updated_supplier["name"] = update_data["name"]

    with patch("app.modules.purchases.service.PurchasesService.update_supplier") as mock_update:
        mock_update.return_value = MagicMock(**updated_supplier)

        response = test_client.put(
            f"/v2/purchases/suppliers/{supplier_id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]


def test_update_supplier_not_found(test_client, client, auth_headers):
    """Test updating a non-existent supplier."""
    supplier_id = str(uuid4())
    update_data = {"name": "Updated Name"}

    with patch("app.modules.purchases.service.PurchasesService.update_supplier") as mock_update:
        mock_update.return_value = None

        response = test_client.put(
            f"/v2/purchases/suppliers/{supplier_id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 404


def test_delete_supplier(test_client, client, auth_headers, sample_supplier):
    """Test deleting a supplier (soft delete)."""
    supplier_id = sample_supplier["id"]

    with patch("app.modules.purchases.service.PurchasesService.delete_supplier") as mock_delete:
        mock_delete.return_value = True

        response = test_client.delete(
            f"/v2/purchases/suppliers/{supplier_id}",
            headers=auth_headers
        )

        assert response.status_code == 204


def test_delete_supplier_not_found(test_client, client, auth_headers):
    """Test deleting a non-existent supplier."""
    supplier_id = str(uuid4())

    with patch("app.modules.purchases.service.PurchasesService.delete_supplier") as mock_delete:
        mock_delete.return_value = False

        response = test_client.delete(
            f"/v2/purchases/suppliers/{supplier_id}",
            headers=auth_headers
        )

        assert response.status_code == 404


def test_supplier_pagination(test_client, client, auth_headers, sample_supplier):
    """Test supplier pagination."""
    suppliers = [MagicMock(**{**sample_supplier, "id": str(uuid4())}) for _ in range(5)]

    with patch("app.modules.purchases.service.PurchasesService.list_suppliers") as mock_list:
        mock_list.return_value = (suppliers, 25)

        response = test_client.get(
            "/v2/purchases/suppliers?page=2&page_size=5",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["per_page"] == 5
        assert data["total"] == 25
        assert data["pages"] == 5


# ============================================================================
# ORDER TESTS (14 tests)
# ============================================================================

def test_create_order(test_client, client, auth_headers, order_data, sample_order):
    """Test creating a new order."""
    with patch("app.modules.purchases.service.PurchasesService.create_order") as mock_create:
        mock_create.return_value = MagicMock(**sample_order)

        response = test_client.post(
            "/v2/purchases/orders",
            json=order_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert_order_fields(data)
        assert data["status"] == "DRAFT"
        assert data["number"] == sample_order["number"]


def test_list_orders(test_client, client, auth_headers, sample_order):
    """Test listing orders."""
    with patch("app.modules.purchases.service.PurchasesService.list_orders") as mock_list:
        mock_list.return_value = ([MagicMock(**sample_order)], 1)

        response = test_client.get(
            "/v2/purchases/orders",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert_pagination_fields(data)
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert_order_fields(data["items"][0])


def test_list_orders_with_filters(test_client, client, auth_headers, sample_order):
    """Test listing orders with various filters."""
    with patch("app.modules.purchases.service.PurchasesService.list_orders") as mock_list:
        mock_list.return_value = ([MagicMock(**sample_order)], 1)

        # Test supplier_id filter
        response = test_client.get(
            f"/v2/purchases/orders?supplier_id={sample_order['supplier_id']}",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Test status filter
        response = test_client.get(
            "/v2/purchases/orders?status=DRAFT",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Test search filter
        response = test_client.get(
            "/v2/purchases/orders?search=CA-2024",
            headers=auth_headers
        )
        assert response.status_code == 200


def test_get_order(test_client, client, auth_headers, sample_order):
    """Test getting a specific order."""
    order_id = sample_order["id"]

    with patch("app.modules.purchases.service.PurchasesService.get_order") as mock_get:
        mock_get.return_value = MagicMock(**sample_order)

        response = test_client.get(
            f"/v2/purchases/orders/{order_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert_order_fields(data)
        assert data["id"] == order_id


def test_get_order_not_found(test_client, client, auth_headers):
    """Test getting a non-existent order."""
    order_id = str(uuid4())

    with patch("app.modules.purchases.service.PurchasesService.get_order") as mock_get:
        mock_get.return_value = None

        response = test_client.get(
            f"/v2/purchases/orders/{order_id}",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "non trouvée" in response.json()["detail"]


def test_update_order(test_client, client, auth_headers, sample_order):
    """Test updating an order."""
    order_id = sample_order["id"]
    update_data = {"reference": "UPDATED-REF-001"}

    updated_order = sample_order.copy()
    updated_order["reference"] = update_data["reference"]

    with patch("app.modules.purchases.service.PurchasesService.update_order") as mock_update:
        mock_update.return_value = MagicMock(**updated_order)

        response = test_client.put(
            f"/v2/purchases/orders/{order_id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["reference"] == update_data["reference"]


def test_update_order_not_found(test_client, client, auth_headers):
    """Test updating a non-existent order."""
    order_id = str(uuid4())
    update_data = {"reference": "UPDATED-REF"}

    with patch("app.modules.purchases.service.PurchasesService.update_order") as mock_update:
        mock_update.return_value = None

        response = test_client.put(
            f"/v2/purchases/orders/{order_id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 404


def test_validate_order(test_client, client, auth_headers, sample_order):
    """Test validating an order (DRAFT → SENT)."""
    order_id = sample_order["id"]

    validated_order = sample_order.copy()
    validated_order["status"] = "SENT"
    validated_order["validated_at"] = datetime.now().isoformat()

    with patch("app.modules.purchases.service.PurchasesService.validate_order") as mock_validate:
        mock_validate.return_value = MagicMock(**validated_order)

        response = test_client.post(
            f"/v2/purchases/orders/{order_id}/validate",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SENT"
        assert data["validated_at"] is not None


def test_validate_order_not_found(test_client, client, auth_headers):
    """Test validating a non-existent order."""
    order_id = str(uuid4())

    with patch("app.modules.purchases.service.PurchasesService.validate_order") as mock_validate:
        mock_validate.return_value = None

        response = test_client.post(
            f"/v2/purchases/orders/{order_id}/validate",
            headers=auth_headers
        )

        assert response.status_code == 404


def test_cancel_order(test_client, client, auth_headers, sample_order):
    """Test cancelling an order."""
    order_id = sample_order["id"]

    cancelled_order = sample_order.copy()
    cancelled_order["status"] = "CANCELLED"

    with patch("app.modules.purchases.service.PurchasesService.cancel_order") as mock_cancel:
        mock_cancel.return_value = MagicMock(**cancelled_order)

        response = test_client.post(
            f"/v2/purchases/orders/{order_id}/cancel",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CANCELLED"


def test_cancel_order_not_found(test_client, client, auth_headers):
    """Test cancelling a non-existent order."""
    order_id = str(uuid4())

    with patch("app.modules.purchases.service.PurchasesService.cancel_order") as mock_cancel:
        mock_cancel.return_value = None

        response = test_client.post(
            f"/v2/purchases/orders/{order_id}/cancel",
            headers=auth_headers
        )

        assert response.status_code == 404


def test_delete_order_draft(test_client, client, auth_headers, sample_order):
    """Test deleting a draft order."""
    order_id = sample_order["id"]

    # Mock order with DRAFT status
    draft_order = MagicMock(**sample_order)
    draft_order.status = MagicMock()
    draft_order.status.__eq__ = lambda self, other: other == "DRAFT"

    with patch("app.modules.purchases.service.PurchasesService.get_order") as mock_get:
        mock_get.return_value = draft_order

        with patch("app.modules.purchases.service.PurchasesService.db") as mock_db:
            response = test_client.delete(
                f"/v2/purchases/orders/{order_id}",
                headers=auth_headers
            )

            assert response.status_code == 204


def test_delete_order_not_draft(test_client, client, auth_headers, sample_order):
    """Test deleting a non-draft order (should fail)."""
    order_id = sample_order["id"]

    # Mock order with SENT status
    sent_order = sample_order.copy()
    sent_order["status"] = "SENT"
    mock_order = MagicMock(**sent_order)
    mock_order.status = MagicMock()
    mock_order.status.__eq__ = lambda self, other: other == "SENT"

    with patch("app.modules.purchases.service.PurchasesService.get_order") as mock_get:
        mock_get.return_value = mock_order

        response = test_client.delete(
            f"/v2/purchases/orders/{order_id}",
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "brouillon" in response.json()["detail"]


def test_order_pagination(test_client, client, auth_headers, sample_order):
    """Test order pagination."""
    orders = [MagicMock(**{**sample_order, "id": str(uuid4())}) for _ in range(10)]

    with patch("app.modules.purchases.service.PurchasesService.list_orders") as mock_list:
        mock_list.return_value = (orders, 50)

        response = test_client.get(
            "/v2/purchases/orders?page=3&page_size=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 3
        assert data["per_page"] == 10
        assert data["total"] == 50
        assert data["pages"] == 5


# ============================================================================
# INVOICE TESTS (13 tests)
# ============================================================================

def test_create_invoice(test_client, client, auth_headers, invoice_data, sample_invoice):
    """Test creating a new invoice."""
    with patch("app.modules.purchases.service.PurchasesService.create_invoice") as mock_create:
        mock_create.return_value = MagicMock(**sample_invoice)

        response = test_client.post(
            "/v2/purchases/invoices",
            json=invoice_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert_invoice_fields(data)
        assert data["status"] == "DRAFT"
        assert data["number"] == sample_invoice["number"]


def test_list_invoices(test_client, client, auth_headers, sample_invoice):
    """Test listing invoices."""
    with patch("app.modules.purchases.service.PurchasesService.list_invoices") as mock_list:
        mock_list.return_value = ([MagicMock(**sample_invoice)], 1)

        response = test_client.get(
            "/v2/purchases/invoices",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert_pagination_fields(data)
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert_invoice_fields(data["items"][0])


def test_list_invoices_with_filters(test_client, client, auth_headers, sample_invoice):
    """Test listing invoices with various filters."""
    with patch("app.modules.purchases.service.PurchasesService.list_invoices") as mock_list:
        mock_list.return_value = ([MagicMock(**sample_invoice)], 1)

        # Test supplier_id filter
        response = test_client.get(
            f"/v2/purchases/invoices?supplier_id={sample_invoice['supplier_id']}",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Test order_id filter
        response = test_client.get(
            f"/v2/purchases/invoices?order_id={sample_invoice['order_id']}",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Test status filter
        response = test_client.get(
            "/v2/purchases/invoices?status=DRAFT",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Test search filter
        response = test_client.get(
            "/v2/purchases/invoices?search=INV-SUPP",
            headers=auth_headers
        )
        assert response.status_code == 200


def test_get_invoice(test_client, client, auth_headers, sample_invoice):
    """Test getting a specific invoice."""
    invoice_id = sample_invoice["id"]

    with patch("app.modules.purchases.service.PurchasesService.get_invoice") as mock_get:
        mock_get.return_value = MagicMock(**sample_invoice)

        response = test_client.get(
            f"/v2/purchases/invoices/{invoice_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert_invoice_fields(data)
        assert data["id"] == invoice_id


def test_get_invoice_not_found(test_client, client, auth_headers):
    """Test getting a non-existent invoice."""
    invoice_id = str(uuid4())

    with patch("app.modules.purchases.service.PurchasesService.get_invoice") as mock_get:
        mock_get.return_value = None

        response = test_client.get(
            f"/v2/purchases/invoices/{invoice_id}",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "non trouvée" in response.json()["detail"]


def test_update_invoice(test_client, client, auth_headers, sample_invoice):
    """Test updating an invoice."""
    invoice_id = sample_invoice["id"]
    update_data = {"reference": "UPDATED-SUPP-REF"}

    updated_invoice = sample_invoice.copy()
    updated_invoice["reference"] = update_data["reference"]

    with patch("app.modules.purchases.service.PurchasesService.update_invoice") as mock_update:
        mock_update.return_value = MagicMock(**updated_invoice)

        response = test_client.put(
            f"/v2/purchases/invoices/{invoice_id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["reference"] == update_data["reference"]


def test_update_invoice_not_found(test_client, client, auth_headers):
    """Test updating a non-existent invoice."""
    invoice_id = str(uuid4())
    update_data = {"reference": "UPDATED-REF"}

    with patch("app.modules.purchases.service.PurchasesService.update_invoice") as mock_update:
        mock_update.return_value = None

        response = test_client.put(
            f"/v2/purchases/invoices/{invoice_id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 404


def test_validate_invoice(test_client, client, auth_headers, sample_invoice):
    """Test validating an invoice (DRAFT → VALIDATED)."""
    invoice_id = sample_invoice["id"]

    validated_invoice = sample_invoice.copy()
    validated_invoice["status"] = "VALIDATED"
    validated_invoice["validated_at"] = datetime.now().isoformat()

    with patch("app.modules.purchases.service.PurchasesService.validate_invoice") as mock_validate:
        mock_validate.return_value = MagicMock(**validated_invoice)

        response = test_client.post(
            f"/v2/purchases/invoices/{invoice_id}/validate",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "VALIDATED"
        assert data["validated_at"] is not None


def test_validate_invoice_not_found(test_client, client, auth_headers):
    """Test validating a non-existent invoice."""
    invoice_id = str(uuid4())

    with patch("app.modules.purchases.service.PurchasesService.validate_invoice") as mock_validate:
        mock_validate.return_value = None

        response = test_client.post(
            f"/v2/purchases/invoices/{invoice_id}/validate",
            headers=auth_headers
        )

        assert response.status_code == 404


def test_delete_invoice_draft(test_client, client, auth_headers, sample_invoice):
    """Test deleting a draft invoice."""
    invoice_id = sample_invoice["id"]

    # Mock invoice with DRAFT status
    draft_invoice = MagicMock(**sample_invoice)
    draft_invoice.status = MagicMock()
    draft_invoice.status.__eq__ = lambda self, other: other == "DRAFT"

    with patch("app.modules.purchases.service.PurchasesService.get_invoice") as mock_get:
        mock_get.return_value = draft_invoice

        with patch("app.modules.purchases.service.PurchasesService.db") as mock_db:
            response = test_client.delete(
                f"/v2/purchases/invoices/{invoice_id}",
                headers=auth_headers
            )

            assert response.status_code == 204


def test_delete_invoice_not_draft(test_client, client, auth_headers, sample_invoice):
    """Test deleting a non-draft invoice (should fail)."""
    invoice_id = sample_invoice["id"]

    # Mock invoice with VALIDATED status
    validated_invoice = sample_invoice.copy()
    validated_invoice["status"] = "VALIDATED"
    mock_invoice = MagicMock(**validated_invoice)
    mock_invoice.status = MagicMock()
    mock_invoice.status.__eq__ = lambda self, other: other == "VALIDATED"

    with patch("app.modules.purchases.service.PurchasesService.get_invoice") as mock_get:
        mock_get.return_value = mock_invoice

        response = test_client.delete(
            f"/v2/purchases/invoices/{invoice_id}",
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "brouillon" in response.json()["detail"]


def test_invoice_pagination(test_client, client, auth_headers, sample_invoice):
    """Test invoice pagination."""
    invoices = [MagicMock(**{**sample_invoice, "id": str(uuid4())}) for _ in range(15)]

    with patch("app.modules.purchases.service.PurchasesService.list_invoices") as mock_list:
        mock_list.return_value = (invoices, 45)

        response = test_client.get(
            "/v2/purchases/invoices?page=2&page_size=15",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["per_page"] == 15
        assert data["total"] == 45
        assert data["pages"] == 3


def test_invoice_with_order_link(test_client, client, auth_headers, sample_invoice):
    """Test invoice linked to an order."""
    with patch("app.modules.purchases.service.PurchasesService.create_invoice") as mock_create:
        mock_create.return_value = MagicMock(**sample_invoice)

        invoice_data = {
            "number": "INV-LINKED-001",
            "supplier_id": sample_invoice["supplier_id"],
            "order_id": sample_invoice["order_id"],
            "invoice_date": datetime.now().isoformat(),
            "lines": [
                {
                    "line_number": 1,
                    "description": "Test",
                    "quantity": "1.000",
                    "unit_price": "100.00"
                }
            ]
        }

        response = test_client.post(
            "/v2/purchases/invoices",
            json=invoice_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["order_id"] == sample_invoice["order_id"]


# ============================================================================
# SUMMARY TESTS (2 tests)
# ============================================================================

def test_get_summary(test_client, client, auth_headers, sample_summary):
    """Test getting summary/dashboard data."""
    with patch("app.modules.purchases.service.PurchasesService.get_summary") as mock_summary:
        mock_summary.return_value = MagicMock(**sample_summary)

        response = test_client.get(
            "/v2/purchases/summary",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_suppliers" in data
        assert "total_orders" in data
        assert "total_invoices" in data
        assert "period_orders_amount" in data


def test_summary_structure(test_client, client, auth_headers, sample_summary):
    """Test summary data structure and completeness."""
    with patch("app.modules.purchases.service.PurchasesService.get_summary") as mock_summary:
        mock_summary.return_value = MagicMock(**sample_summary)

        response = test_client.get(
            "/v2/purchases/summary",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Supplier stats
        assert data["total_suppliers"] == 10
        assert data["active_suppliers"] == 8
        assert data["pending_suppliers"] == 2

        # Order stats
        assert data["total_orders"] == 25
        assert data["draft_orders"] == 5
        assert data["sent_orders"] == 10

        # Invoice stats
        assert data["total_invoices"] == 20
        assert data["pending_invoices"] == 3
        assert data["validated_invoices"] == 12

        # Top suppliers
        assert "top_suppliers" in data
        assert len(data["top_suppliers"]) == 3


# ============================================================================
# WORKFLOW TESTS (5 tests)
# ============================================================================

def test_complete_purchase_flow(test_client, client, auth_headers, supplier_data, order_data, invoice_data, sample_supplier, sample_order, sample_invoice):
    """Test complete purchase workflow: supplier → order → invoice."""
    # Step 1: Create supplier
    with patch("app.modules.purchases.service.PurchasesService.create_supplier") as mock_create_supplier:
        mock_create_supplier.return_value = MagicMock(**sample_supplier)

        supplier_response = test_client.post(
            "/v2/purchases/suppliers",
            json=supplier_data,
            headers=auth_headers
        )
        assert supplier_response.status_code == 201
        supplier_id = supplier_response.json()["id"]

    # Step 2: Create order for supplier
    with patch("app.modules.purchases.service.PurchasesService.create_order") as mock_create_order:
        mock_create_order.return_value = MagicMock(**sample_order)

        order_response = test_client.post(
            "/v2/purchases/orders",
            json=order_data,
            headers=auth_headers
        )
        assert order_response.status_code == 201
        order_id = order_response.json()["id"]

    # Step 3: Create invoice for order
    with patch("app.modules.purchases.service.PurchasesService.create_invoice") as mock_create_invoice:
        mock_create_invoice.return_value = MagicMock(**sample_invoice)

        invoice_response = test_client.post(
            "/v2/purchases/invoices",
            json=invoice_data,
            headers=auth_headers
        )
        assert invoice_response.status_code == 201
        assert invoice_response.json()["order_id"] == order_id


def test_order_validation_workflow(test_client, client, auth_headers, sample_order):
    """Test order validation workflow: DRAFT → SENT."""
    order_id = sample_order["id"]

    # Create draft order
    with patch("app.modules.purchases.service.PurchasesService.create_order") as mock_create:
        mock_create.return_value = MagicMock(**sample_order)

        create_response = test_client.post(
            "/v2/purchases/orders",
            json={
                "supplier_id": sample_order["supplier_id"],
                "date": datetime.now().isoformat(),
                "lines": [
                    {
                        "line_number": 1,
                        "description": "Test",
                        "quantity": "1.000",
                        "unit_price": "100.00"
                    }
                ]
            },
            headers=auth_headers
        )
        assert create_response.json()["status"] == "DRAFT"

    # Validate order
    validated_order = sample_order.copy()
    validated_order["status"] = "SENT"
    validated_order["validated_at"] = datetime.now().isoformat()

    with patch("app.modules.purchases.service.PurchasesService.validate_order") as mock_validate:
        mock_validate.return_value = MagicMock(**validated_order)

        validate_response = test_client.post(
            f"/v2/purchases/orders/{order_id}/validate",
            headers=auth_headers
        )
        assert validate_response.status_code == 200
        assert validate_response.json()["status"] == "SENT"


def test_invoice_validation_workflow(test_client, client, auth_headers, sample_invoice):
    """Test invoice validation workflow: DRAFT → VALIDATED."""
    invoice_id = sample_invoice["id"]

    # Create draft invoice
    with patch("app.modules.purchases.service.PurchasesService.create_invoice") as mock_create:
        mock_create.return_value = MagicMock(**sample_invoice)

        create_response = test_client.post(
            "/v2/purchases/invoices",
            json={
                "number": "INV-TEST-001",
                "supplier_id": sample_invoice["supplier_id"],
                "invoice_date": datetime.now().isoformat(),
                "lines": [
                    {
                        "line_number": 1,
                        "description": "Test",
                        "quantity": "1.000",
                        "unit_price": "100.00"
                    }
                ]
            },
            headers=auth_headers
        )
        assert create_response.json()["status"] == "DRAFT"

    # Validate invoice
    validated_invoice = sample_invoice.copy()
    validated_invoice["status"] = "VALIDATED"
    validated_invoice["validated_at"] = datetime.now().isoformat()

    with patch("app.modules.purchases.service.PurchasesService.validate_invoice") as mock_validate:
        mock_validate.return_value = MagicMock(**validated_invoice)

        validate_response = test_client.post(
            f"/v2/purchases/invoices/{invoice_id}/validate",
            headers=auth_headers
        )
        assert validate_response.status_code == 200
        assert validate_response.json()["status"] == "VALIDATED"


def test_supplier_deactivation(test_client, client, auth_headers, sample_supplier):
    """Test supplier deactivation workflow."""
    supplier_id = sample_supplier["id"]

    # Deactivate supplier
    deactivated_supplier = sample_supplier.copy()
    deactivated_supplier["is_active"] = False
    deactivated_supplier["status"] = "INACTIVE"

    with patch("app.modules.purchases.service.PurchasesService.update_supplier") as mock_update:
        mock_update.return_value = MagicMock(**deactivated_supplier)

        response = test_client.put(
            f"/v2/purchases/suppliers/{supplier_id}",
            json={"is_active": False, "status": "INACTIVE"},
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is False
        assert response.json()["status"] == "INACTIVE"


def test_order_cancellation(test_client, client, auth_headers, sample_order):
    """Test order cancellation workflow."""
    order_id = sample_order["id"]

    # Cancel order
    cancelled_order = sample_order.copy()
    cancelled_order["status"] = "CANCELLED"

    with patch("app.modules.purchases.service.PurchasesService.cancel_order") as mock_cancel:
        mock_cancel.return_value = MagicMock(**cancelled_order)

        response = test_client.post(
            f"/v2/purchases/orders/{order_id}/cancel",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["status"] == "CANCELLED"


# ============================================================================
# SECURITY TESTS (3 tests)
# ============================================================================

def test_tenant_isolation(test_client, client, auth_headers, sample_supplier, tenant_id):
    """Test that tenant isolation is enforced."""
    with patch("app.modules.purchases.service.PurchasesService.list_suppliers") as mock_list:
        # Ensure only tenant-specific data is returned
        mock_list.return_value = ([MagicMock(**sample_supplier)], 1)

        response = test_client.get(
            "/v2/purchases/suppliers",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # Verify all items belong to the correct tenant
        for item in data["items"]:
            assert item["tenant_id"] == tenant_id


def test_context_propagation(test_client, client, auth_headers, supplier_data, tenant_id, user_id):
    """Test that SaaSContext is properly propagated."""
    with patch("app.modules.purchases.service.PurchasesService.create_supplier") as mock_create:
        def check_context(data, created_by):
            # Verify that user_id is passed correctly
            assert created_by == user_id
            return MagicMock(id=str(uuid4()), tenant_id=tenant_id, **supplier_data)

        mock_create.side_effect = check_context

        response = test_client.post(
            "/v2/purchases/suppliers",
            json=supplier_data,
            headers=auth_headers
        )

        assert response.status_code == 201


def test_audit_trail(test_client, client, auth_headers, supplier_data, sample_supplier, user_id):
    """Test that audit trail fields are properly set."""
    with patch("app.modules.purchases.service.PurchasesService.create_supplier") as mock_create:
        mock_create.return_value = MagicMock(**sample_supplier)

        response = test_client.post(
            "/v2/purchases/suppliers",
            json=supplier_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        # Verify audit fields
        assert "created_by" in data
        assert "created_at" in data
        assert "updated_at" in data


# ============================================================================
# EDGE CASES TESTS (3 tests)
# ============================================================================

def test_invalid_supplier_data(test_client, client, auth_headers):
    """Test creating supplier with invalid data."""
    invalid_data = {
        "code": "",  # Empty code should fail
        "name": "Test"
    }

    response = test_client.post(
        "/v2/purchases/suppliers",
        json=invalid_data,
        headers=auth_headers
    )

    # Should fail validation
    assert response.status_code == 422


def test_duplicate_order_reference(test_client, client, auth_headers, order_data, sample_order):
    """Test creating order with duplicate number."""
    with patch("app.modules.purchases.service.PurchasesService.create_order") as mock_create:
        # Simulate duplicate number error
        mock_create.side_effect = ValueError("Duplicate order number")

        response = test_client.post(
            "/v2/purchases/orders",
            json=order_data,
            headers=auth_headers
        )

        # Should return 500 or handle the error
        assert response.status_code >= 400


def test_validation_errors(test_client, client, auth_headers, invoice_data):
    """Test validation errors in invoice creation."""
    # Invalid invoice data (missing required fields)
    invalid_invoice_data = {
        "number": "INV-001",
        "supplier_id": str(uuid4()),
        # Missing invoice_date
        "lines": []  # Empty lines should fail
    }

    response = test_client.post(
        "/v2/purchases/invoices",
        json=invalid_invoice_data,
        headers=auth_headers
    )

    # Should fail validation
    assert response.status_code == 422
