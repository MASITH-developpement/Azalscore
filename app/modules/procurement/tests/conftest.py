"""
Pytest fixtures for procurement module tests.

Provides reusable test fixtures following CORE SaaS v2 patterns:
- Test client configuration
- Mock SaaSContext with tenant isolation
- Sample data dictionaries for all entities
- Helper utilities for assertions
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4
from fastapi.testclient import TestClient

from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext, UserRole
from app.main import app


# ===========================
# Client and Auth
# ===========================

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def tenant_id():
    """Test tenant ID."""
    return "tenant-test-procurement"


@pytest.fixture
def user_id():
    """Test user ID."""
    return "user-test-procurement"


@pytest.fixture
def auth_headers():
    """Authentication headers for requests."""
    return {"Authorization": "Bearer test-token"}


# ===========================
# SaaSContext Mock
# ===========================

@pytest.fixture(autouse=True)
def mock_saas_context(monkeypatch, tenant_id, user_id):
    """
    Mock SaaSContext for all tests.

    Automatically applied to all tests via autouse=True.
    Provides a tenant-scoped admin context with full permissions.
    """
    def mock_get_context():
        return SaaSContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role=UserRole.ADMIN,
            permissions={"procurement.*"},
            scope="tenant",
            session_id="session-test",
            ip_address="127.0.0.1",
            user_agent="pytest",
            correlation_id="test-correlation"
        )

    from app.modules.procurement import router_v2
    monkeypatch.setattr(router_v2, "get_saas_context", mock_get_context)
    return mock_get_context


# ===========================
# Supplier Fixtures
# ===========================

@pytest.fixture
def supplier_data():
    """Base supplier data for creation."""
    return {
        "code": "FRN-001",
        "name": "Test Supplier Ltd",
        "legal_name": "Test Supplier Limited",
        "type": "GOODS",
        "tax_id": "FR12345678901",
        "vat_number": "FR12345678901",
        "email": "contact@testsupplier.com",
        "phone": "+33123456789",
        "website": "https://testsupplier.com",
        "address_line1": "123 Test Street",
        "address_line2": "Building A",
        "postal_code": "75001",
        "city": "Paris",
        "country": "France",
        "payment_terms": "30 days",
        "currency": "EUR",
        "credit_limit": "50000.00",
        "discount_rate": "5.00",
        "category": "Electronics",
        "bank_name": "Test Bank",
        "iban": "FR7612345678901234567890123",
        "bic": "TESTFRPP",
        "notes": "Test supplier notes",
        "tags": ["electronics", "hardware"]
    }


@pytest.fixture
def sample_supplier(supplier_data, tenant_id, user_id):
    """Complete supplier entity with metadata."""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "status": "APPROVED",
        "is_active": True,
        "rating": "4.5",
        "created_by": user_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        **supplier_data
    }


# ===========================
# Requisition Fixtures
# ===========================

@pytest.fixture
def requisition_data(sample_supplier):
    """Base requisition data for creation."""
    return {
        "title": "Office Supplies Request",
        "description": "Monthly office supplies requisition",
        "justification": "Running low on office supplies",
        "priority": "MEDIUM",
        "department_id": str(uuid4()),
        "requested_date": datetime.now().isoformat(),
        "required_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "budget_code": "DEPT-001-2024",
        "notes": "Urgent items needed by next week",
        "lines": [
            {
                "product_id": str(uuid4()),
                "product_code": "PROD-001",
                "description": "Office Paper A4",
                "quantity": "50.000",
                "unit": "box",
                "estimated_price": "15.00",
                "preferred_supplier_id": sample_supplier["id"],
                "required_date": (datetime.now() + timedelta(days=7)).isoformat(),
                "notes": "White paper only"
            }
        ]
    }


@pytest.fixture
def sample_requisition(requisition_data, tenant_id, user_id):
    """Complete requisition entity with metadata."""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "number": "REQ-202401-0001",
        "status": "DRAFT",
        "estimated_total": "750.00",
        "requester_id": user_id,
        "approved_by": None,
        "approved_at": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        **{k: v for k, v in requisition_data.items() if k != "lines"},
        "lines": []
    }


# ===========================
# Order Fixtures
# ===========================

@pytest.fixture
def order_data(sample_supplier):
    """Base order data for creation."""
    return {
        "supplier_id": sample_supplier["id"],
        "requisition_id": None,
        "quotation_id": None,
        "order_date": datetime.now().date().isoformat(),
        "expected_date": (datetime.now() + timedelta(days=14)).date().isoformat(),
        "delivery_address": "456 Delivery Street, Paris 75002",
        "delivery_contact": "John Doe",
        "currency": "EUR",
        "payment_terms": "30 days",
        "incoterms": "DAP",
        "shipping_cost": "50.00",
        "notes": "Please deliver during business hours",
        "internal_notes": "High priority order",
        "lines": [
            {
                "product_id": str(uuid4()),
                "product_code": "PROD-001",
                "description": "Test Product 1",
                "quantity": "10.000",
                "unit": "piece",
                "unit_price": "100.00",
                "discount_percent": "0.00",
                "tax_rate": "20.00",
                "expected_date": (datetime.now() + timedelta(days=14)).date().isoformat(),
                "notes": "Standard packaging"
            },
            {
                "product_id": str(uuid4()),
                "product_code": "PROD-002",
                "description": "Test Product 2",
                "quantity": "5.000",
                "unit": "piece",
                "unit_price": "200.00",
                "discount_percent": "10.00",
                "tax_rate": "20.00",
                "expected_date": (datetime.now() + timedelta(days=14)).date().isoformat(),
                "notes": "Fragile items"
            }
        ]
    }


@pytest.fixture
def sample_order(order_data, tenant_id, user_id):
    """Complete order entity with metadata."""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "number": "CMD-2024-0001",
        "status": "DRAFT",
        "subtotal": "1900.00",
        "tax_amount": "380.00",
        "total": "2330.00",
        "invoiced_amount": "0.00",
        "sent_at": None,
        "confirmed_at": None,
        "confirmed_date": None,
        "supplier_reference": None,
        "created_by": user_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        **{k: v for k, v in order_data.items() if k != "lines"},
        "lines": []
    }


# ===========================
# Receipt Fixtures
# ===========================

@pytest.fixture
def receipt_data(sample_order):
    """Base receipt data for creation."""
    return {
        "order_id": sample_order["id"],
        "receipt_date": datetime.now().date().isoformat(),
        "delivery_note": "DN-2024-001",
        "carrier": "Test Carrier",
        "tracking_number": "TRACK123456",
        "warehouse_id": str(uuid4()),
        "location": "Zone A, Rack 1",
        "notes": "Received in good condition",
        "lines": [
            {
                "order_line_id": str(uuid4()),
                "product_id": str(uuid4()),
                "product_code": "PROD-001",
                "description": "Test Product 1",
                "ordered_quantity": "10.000",
                "received_quantity": "10.000",
                "rejected_quantity": "0.000",
                "unit": "piece",
                "rejection_reason": None,
                "lot_number": "LOT-2024-001",
                "expiry_date": (datetime.now() + timedelta(days=365)).date().isoformat(),
                "notes": "All items checked"
            }
        ]
    }


@pytest.fixture
def sample_receipt(receipt_data, tenant_id, user_id, sample_supplier):
    """Complete receipt entity with metadata."""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "number": "GR-202401-0001",
        "supplier_id": sample_supplier["id"],
        "status": "DRAFT",
        "received_by": user_id,
        "validated_by": None,
        "validated_at": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        **{k: v for k, v in receipt_data.items() if k != "lines"},
        "lines": []
    }


# ===========================
# Invoice Fixtures
# ===========================

@pytest.fixture
def invoice_data(sample_supplier, sample_order):
    """Base invoice data for creation."""
    return {
        "supplier_id": sample_supplier["id"],
        "order_id": sample_order["id"],
        "invoice_date": datetime.now().date().isoformat(),
        "due_date": (datetime.now() + timedelta(days=30)).date().isoformat(),
        "supplier_invoice_number": "SUPP-INV-001",
        "supplier_invoice_date": datetime.now().date().isoformat(),
        "currency": "EUR",
        "payment_terms": "30 days",
        "payment_method": "BANK_TRANSFER",
        "notes": "Invoice notes",
        "lines": [
            {
                "order_line_id": str(uuid4()),
                "product_id": str(uuid4()),
                "product_code": "PROD-001",
                "description": "Test Product 1",
                "quantity": "10.000",
                "unit": "piece",
                "unit_price": "100.00",
                "discount_percent": "0.00",
                "tax_rate": "20.00",
                "account_id": str(uuid4()),
                "analytic_code": "DEPT-001",
                "notes": "Line notes"
            }
        ]
    }


@pytest.fixture
def sample_invoice(invoice_data, tenant_id, user_id):
    """Complete invoice entity with metadata."""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "number": "FAF-2024-0001",
        "status": "DRAFT",
        "subtotal": "1000.00",
        "tax_amount": "200.00",
        "total": "1200.00",
        "paid_amount": "0.00",
        "remaining_amount": "1200.00",
        "validated_by": None,
        "validated_at": None,
        "created_by": user_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        **{k: v for k, v in invoice_data.items() if k != "lines"},
        "lines": []
    }


# ===========================
# Payment Fixtures
# ===========================

@pytest.fixture
def payment_data(sample_supplier, sample_invoice):
    """Base payment data for creation."""
    return {
        "supplier_id": sample_supplier["id"],
        "payment_date": datetime.now().date().isoformat(),
        "amount": "1200.00",
        "currency": "EUR",
        "payment_method": "BANK_TRANSFER",
        "reference": "PAY-REF-001",
        "bank_account_id": str(uuid4()),
        "notes": "Payment for invoice FAF-2024-0001",
        "allocations": [
            {
                "invoice_id": sample_invoice["id"],
                "amount": "1200.00"
            }
        ]
    }


@pytest.fixture
def sample_payment(payment_data, tenant_id, user_id):
    """Complete payment entity with metadata."""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "number": "PAY-202401-0001",
        "created_by": user_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        **{k: v for k, v in payment_data.items() if k != "allocations"},
        "allocations": []
    }


# ===========================
# Evaluation Fixtures
# ===========================

@pytest.fixture
def evaluation_data(sample_supplier):
    """Base evaluation data for creation."""
    return {
        "supplier_id": sample_supplier["id"],
        "evaluation_date": datetime.now().date().isoformat(),
        "period_start": (datetime.now() - timedelta(days=90)).date().isoformat(),
        "period_end": datetime.now().date().isoformat(),
        "quality_score": "4.5",
        "price_score": "4.0",
        "delivery_score": "4.8",
        "service_score": "4.3",
        "reliability_score": "4.6",
        "comments": "Excellent supplier performance",
        "recommendations": "Continue partnership"
    }


@pytest.fixture
def sample_evaluation(evaluation_data, tenant_id, user_id):
    """Complete evaluation entity with metadata."""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "overall_score": "4.44",
        "total_orders": 25,
        "total_amount": "50000.00",
        "evaluated_by": user_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        **evaluation_data
    }


# ===========================
# Dashboard Fixtures
# ===========================

@pytest.fixture
def sample_dashboard():
    """Sample dashboard data."""
    return {
        "total_suppliers": 50,
        "active_suppliers": 45,
        "pending_approvals": 5,
        "pending_requisitions": 10,
        "requisitions_this_month": 25,
        "draft_orders": 8,
        "pending_orders": 15,
        "orders_this_month": 30,
        "orders_amount_this_month": "75000.00",
        "pending_invoices": 12,
        "overdue_invoices": 3,
        "invoices_this_month": 28,
        "invoices_amount_this_month": "68000.00",
        "unpaid_amount": "25000.00",
        "payments_due_this_week": "8000.00"
    }


# ===========================
# Helper Functions
# ===========================

def assert_supplier_fields(supplier_dict):
    """Assert that a supplier dict contains required fields."""
    required_fields = ["id", "tenant_id", "code", "name", "status", "is_active", "created_at"]
    for field in required_fields:
        assert field in supplier_dict, f"Missing required field: {field}"


def assert_requisition_fields(requisition_dict):
    """Assert that a requisition dict contains required fields."""
    required_fields = ["id", "tenant_id", "number", "status", "title", "requester_id", "created_at"]
    for field in required_fields:
        assert field in requisition_dict, f"Missing required field: {field}"


def assert_order_fields(order_dict):
    """Assert that an order dict contains required fields."""
    required_fields = ["id", "tenant_id", "number", "supplier_id", "status", "subtotal", "tax_amount", "total", "created_at"]
    for field in required_fields:
        assert field in order_dict, f"Missing required field: {field}"


def assert_receipt_fields(receipt_dict):
    """Assert that a receipt dict contains required fields."""
    required_fields = ["id", "tenant_id", "number", "order_id", "status", "received_by", "created_at"]
    for field in required_fields:
        assert field in receipt_dict, f"Missing required field: {field}"


def assert_invoice_fields(invoice_dict):
    """Assert that an invoice dict contains required fields."""
    required_fields = ["id", "tenant_id", "number", "supplier_id", "status", "subtotal", "tax_amount", "total", "created_at"]
    for field in required_fields:
        assert field in invoice_dict, f"Missing required field: {field}"


def assert_payment_fields(payment_dict):
    """Assert that a payment dict contains required fields."""
    required_fields = ["id", "tenant_id", "number", "supplier_id", "amount", "payment_date", "created_at"]
    for field in required_fields:
        assert field in payment_dict, f"Missing required field: {field}"


def assert_evaluation_fields(evaluation_dict):
    """Assert that an evaluation dict contains required fields."""
    required_fields = ["id", "tenant_id", "supplier_id", "evaluation_date", "overall_score", "evaluated_by", "created_at"]
    for field in required_fields:
        assert field in evaluation_dict, f"Missing required field: {field}"


def assert_list_fields(response_dict):
    """Assert that a list response contains required fields."""
    required_fields = ["items", "total"]
    for field in required_fields:
        assert field in response_dict, f"Missing required list field: {field}"
