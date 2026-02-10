"""
Pytest fixtures for purchases module tests.

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
    return "tenant-test-purchases"


@pytest.fixture
def user_id():
    """Test user ID."""
    return "user-test-purchases"


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
            permissions={"purchases.*"},
            scope="tenant",
            session_id="session-test",
            ip_address="127.0.0.1",
            user_agent="pytest",
            correlation_id="test-correlation"
        )

    from app.modules.purchases import router_v2
    monkeypatch.setattr(router_v2, "get_saas_context", mock_get_context)
    return mock_get_context


# ===========================
# Supplier Fixtures
# ===========================

@pytest.fixture
def supplier_data():
    """Base supplier data for creation."""
    return {
        "code": "FRS001",
        "name": "Test Supplier Ltd",
        "supplier_type": "BOTH",
        "contact_name": "John Doe",
        "email": "contact@testsupplier.com",
        "phone": "+33123456789",
        "address": "123 Test Street",
        "city": "Paris",
        "postal_code": "75001",
        "country": "France",
        "tax_id": "FR12345678901",
        "payment_terms": "30 jours",
        "currency": "EUR",
        "notes": "Test supplier notes"
    }


@pytest.fixture
def sample_supplier(supplier_data, tenant_id, user_id):
    """Complete supplier entity with metadata."""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "status": "APPROVED",
        "is_active": True,
        "created_by": user_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        **supplier_data
    }


# ===========================
# Order Fixtures
# ===========================

@pytest.fixture
def order_data(sample_supplier):
    """Base order data for creation."""
    return {
        "supplier_id": sample_supplier["id"],
        "date": datetime.now().isoformat(),
        "expected_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "reference": "REF-TEST-001",
        "delivery_address": "456 Delivery Street, Paris 75002",
        "currency": "EUR",
        "notes": "Test order notes",
        "lines": [
            {
                "line_number": 1,
                "product_code": "PROD001",
                "description": "Test Product 1",
                "quantity": "10.000",
                "unit": "unité",
                "unit_price": "100.00",
                "discount_percent": "0.00",
                "tax_rate": "20.00"
            },
            {
                "line_number": 2,
                "product_code": "PROD002",
                "description": "Test Product 2",
                "quantity": "5.000",
                "unit": "unité",
                "unit_price": "200.00",
                "discount_percent": "10.00",
                "tax_rate": "20.00"
            }
        ]
    }


@pytest.fixture
def sample_order(order_data, tenant_id, user_id):
    """Complete order entity with metadata."""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "number": "CA-2024-001",
        "status": "DRAFT",
        "total_ht": "1900.00",
        "total_tax": "380.00",
        "total_ttc": "2280.00",
        "validated_at": None,
        "validated_by": None,
        "created_by": user_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        **{k: v for k, v in order_data.items() if k != "lines"},
        "lines": []
    }


# ===========================
# Invoice Fixtures
# ===========================

@pytest.fixture
def invoice_data(sample_supplier, sample_order):
    """Base invoice data for creation."""
    return {
        "number": "INV-SUPP-001",
        "supplier_id": sample_supplier["id"],
        "order_id": sample_order["id"],
        "invoice_date": datetime.now().isoformat(),
        "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "reference": "SUPP-REF-001",
        "currency": "EUR",
        "notes": "Test invoice notes",
        "lines": [
            {
                "line_number": 1,
                "product_code": "PROD001",
                "description": "Test Product 1",
                "quantity": "10.000",
                "unit": "unité",
                "unit_price": "100.00",
                "discount_percent": "0.00",
                "tax_rate": "20.00"
            }
        ]
    }


@pytest.fixture
def sample_invoice(invoice_data, tenant_id, user_id):
    """Complete invoice entity with metadata."""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "status": "DRAFT",
        "total_ht": "1000.00",
        "total_tax": "200.00",
        "total_ttc": "1200.00",
        "paid_amount": "0.00",
        "validated_at": None,
        "validated_by": None,
        "paid_at": None,
        "payment_method": None,
        "created_by": user_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        **{k: v for k, v in invoice_data.items() if k != "lines"},
        "lines": []
    }


# ===========================
# Summary Fixture
# ===========================

@pytest.fixture
def sample_summary():
    """Sample summary/dashboard data."""
    return {
        "total_suppliers": 10,
        "active_suppliers": 8,
        "pending_suppliers": 2,
        "total_orders": 25,
        "draft_orders": 5,
        "sent_orders": 10,
        "confirmed_orders": 7,
        "received_orders": 3,
        "total_invoices": 20,
        "pending_invoices": 3,
        "validated_invoices": 12,
        "paid_invoices": 5,
        "period_orders_amount": "50000.00",
        "period_invoices_amount": "45000.00",
        "period_paid_amount": "30000.00",
        "pending_payments_amount": "15000.00",
        "average_order_amount": "2000.00",
        "average_invoice_amount": "2250.00",
        "top_suppliers": [
            {"id": str(uuid4()), "name": "Supplier A", "total": 15000.0},
            {"id": str(uuid4()), "name": "Supplier B", "total": 12000.0},
            {"id": str(uuid4()), "name": "Supplier C", "total": 8000.0}
        ]
    }


# ===========================
# Helper Functions
# ===========================

def assert_supplier_fields(supplier_dict):
    """Assert that a supplier dict contains required fields."""
    required_fields = ["id", "tenant_id", "code", "name", "status", "is_active", "created_at"]
    for field in required_fields:
        assert field in supplier_dict, f"Missing required field: {field}"


def assert_order_fields(order_dict):
    """Assert that an order dict contains required fields."""
    required_fields = ["id", "tenant_id", "number", "supplier_id", "status", "total_ht", "total_tax", "total_ttc", "created_at"]
    for field in required_fields:
        assert field in order_dict, f"Missing required field: {field}"


def assert_invoice_fields(invoice_dict):
    """Assert that an invoice dict contains required fields."""
    required_fields = ["id", "tenant_id", "number", "supplier_id", "status", "total_ht", "total_tax", "total_ttc", "created_at"]
    for field in required_fields:
        assert field in invoice_dict, f"Missing required field: {field}"


def assert_pagination_fields(response_dict):
    """Assert that a paginated response contains required fields."""
    required_fields = ["total", "page", "per_page", "pages", "items"]
    for field in required_fields:
        assert field in response_dict, f"Missing required pagination field: {field}"
