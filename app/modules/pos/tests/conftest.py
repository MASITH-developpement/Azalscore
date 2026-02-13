"""
Fixtures pour les tests POS v2 - CORE SaaS

Hérite des fixtures globales de app/conftest.py.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from app.core.saas_context import SaaSContext, TenantScope, UserRole


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


@pytest.fixture
def mock_saas_context(saas_context) -> SaaSContext:
    """Alias pour saas_context du conftest global."""
    return saas_context


# ============================================================================
# DATA FIXTURES
# ============================================================================

@pytest.fixture
def store_data() -> Dict[str, Any]:
    """Données pour créer un magasin."""
    return {
        "code": "STORE001",
        "name": "Magasin Principal",
        "address": "123 Rue Test",
        "city": "Paris",
        "postal_code": "75001",
        "country": "France",
        "phone": "+33 1 23 45 67 89",
        "email": "store@example.com",
        "is_active": True
    }


@pytest.fixture
def terminal_data(sample_store: Dict[str, Any]) -> Dict[str, Any]:
    """Données pour créer un terminal."""
    return {
        "store_id": sample_store["id"],
        "terminal_id": "TERM001",
        "name": "Terminal 1",
        "hardware_id": "HW001",
        "is_active": True
    }


@pytest.fixture
def session_data(sample_terminal: Dict[str, Any], sample_user: Dict[str, Any]) -> Dict[str, Any]:
    """Données pour ouvrir une session."""
    return {
        "terminal_id": sample_terminal["id"],
        "cashier_id": sample_user["id"],
        "opening_cash": Decimal("100.00"),
        "opening_note": "Ouverture de session"
    }


@pytest.fixture
def transaction_data(sample_session: Dict[str, Any], sample_user: Dict[str, Any]) -> Dict[str, Any]:
    """Données pour créer une transaction."""
    return {
        "session_id": sample_session["id"],
        "cashier_id": sample_user["id"],
        "lines": [
            {
                "product_id": 1,
                "name": "Produit Test",
                "sku": "SKU001",
                "quantity": Decimal("2.0"),
                "unit_price": Decimal("10.00"),
                "tax_rate": Decimal("20.0")
            }
        ]
    }


@pytest.fixture
def payment_data() -> Dict[str, Any]:
    """Données pour créer un paiement."""
    return {
        "payment_method": "CASH",
        "amount": Decimal("24.00"),
        "amount_tendered": Decimal("30.00")
    }


@pytest.fixture
def hold_data(sample_session: Dict[str, Any]) -> Dict[str, Any]:
    """Données pour mettre une transaction en attente."""
    return {
        "session_id": sample_session["id"],
        "hold_name": "Client VIP",
        "customer_name": "John Doe",
        "transaction_data": {
            "lines": [
                {
                    "product_id": 1,
                    "name": "Produit Test",
                    "quantity": 1,
                    "unit_price": 10.00
                }
            ]
        }
    }


@pytest.fixture
def cash_movement_data(sample_session: Dict[str, Any]) -> Dict[str, Any]:
    """Données pour créer un mouvement de caisse."""
    return {
        "session_id": sample_session["id"],
        "movement_type": "IN",
        "amount": Decimal("50.00"),
        "reason": "Fond de caisse supplémentaire",
        "description": "Ajout de monnaie"
    }


@pytest.fixture
def quick_key_data(sample_store: Dict[str, Any]) -> Dict[str, Any]:
    """Données pour créer un quick key."""
    return {
        "store_id": sample_store["id"],
        "product_id": 1,
        "page": 1,
        "position": 1,
        "button_text": "Café",
        "button_color": "#FF5733"
    }


@pytest.fixture
def user_data() -> Dict[str, Any]:
    """Données pour créer un utilisateur POS."""
    return {
        "employee_code": "EMP001",
        "first_name": "John",
        "last_name": "Doe",
        "pin_code": "1234",
        "is_manager": False,
        "can_void_transaction": False,
        "can_refund": False,
        "can_open_drawer": True,
        "can_close_session": True
    }


# ============================================================================
# ENTITY FIXTURES (Mock complete entities)
# ============================================================================

@pytest.fixture
def sample_store() -> Dict[str, Any]:
    """Mock d'un magasin complet."""
    return {
        "id": 1,
        "tenant_id": "test-tenant-001",
        "code": "STORE001",
        "name": "Magasin Principal",
        "address": "123 Rue Test",
        "city": "Paris",
        "postal_code": "75001",
        "country": "France",
        "phone": "+33 1 23 45 67 89",
        "email": "store@example.com",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_terminal(sample_store: Dict[str, Any]) -> Dict[str, Any]:
    """Mock d'un terminal complet."""
    return {
        "id": 1,
        "tenant_id": "test-tenant-001",
        "store_id": sample_store["id"],
        "terminal_id": "TERM001",
        "name": "Terminal 1",
        "hardware_id": "HW001",
        "status": "ONLINE",
        "is_active": True,
        "current_session_id": None,
        "last_ping": datetime.utcnow(),
        "last_sync": datetime.utcnow(),
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def sample_session(sample_terminal: Dict[str, Any], sample_user: Dict[str, Any]) -> Dict[str, Any]:
    """Mock d'une session complète."""
    return {
        "id": 1,
        "tenant_id": "test-tenant-001",
        "terminal_id": sample_terminal["id"],
        "session_number": "S202601250001",
        "status": "OPEN",
        "opened_by_id": sample_user["id"],
        "opened_at": datetime.utcnow(),
        "opening_cash": Decimal("100.00"),
        "opening_note": "Ouverture de session",
        "total_sales": Decimal("0"),
        "total_refunds": Decimal("0"),
        "total_discounts": Decimal("0"),
        "transaction_count": 0,
        "cash_total": Decimal("0"),
        "card_total": Decimal("0"),
        "check_total": Decimal("0"),
        "voucher_total": Decimal("0"),
        "other_total": Decimal("0"),
        "closed_by_id": None,
        "closed_at": None,
        "actual_cash": None,
        "expected_cash": None,
        "cash_difference": None,
        "closing_note": None
    }


@pytest.fixture
def sample_transaction(sample_session: Dict[str, Any], sample_user: Dict[str, Any]) -> Dict[str, Any]:
    """Mock d'une transaction complète."""
    return {
        "id": 1,
        "tenant_id": "test-tenant-001",
        "session_id": sample_session["id"],
        "receipt_number": "T202601250000001",
        "status": "PENDING",
        "customer_id": None,
        "customer_name": None,
        "customer_email": None,
        "customer_phone": None,
        "cashier_id": sample_user["id"],
        "salesperson_id": None,
        "subtotal": Decimal("20.00"),
        "discount_total": Decimal("0"),
        "tax_total": Decimal("4.00"),
        "total": Decimal("24.00"),
        "amount_paid": Decimal("0"),
        "amount_due": Decimal("24.00"),
        "change_given": Decimal("0"),
        "discount_type": None,
        "discount_value": None,
        "discount_reason": None,
        "notes": None,
        "original_transaction_id": None,
        "void_reason": None,
        "voided_by_id": None,
        "voided_at": None,
        "completed_at": None,
        "created_at": datetime.utcnow(),
        "lines": [],
        "payments": []
    }


@pytest.fixture
def sample_hold() -> Dict[str, Any]:
    """Mock d'une transaction en attente."""
    return {
        "id": 1,
        "tenant_id": "test-tenant-001",
        "session_id": 1,
        "hold_number": "H202601250001",
        "hold_name": "Client VIP",
        "customer_id": None,
        "customer_name": "John Doe",
        "transaction_data": {"lines": []},
        "held_by_id": 1,
        "is_active": True,
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def sample_cash_movement(sample_session: Dict[str, Any], sample_user: Dict[str, Any]) -> Dict[str, Any]:
    """Mock d'un mouvement de caisse."""
    return {
        "id": 1,
        "tenant_id": "test-tenant-001",
        "session_id": sample_session["id"],
        "movement_type": "IN",
        "amount": Decimal("50.00"),
        "reason": "Fond de caisse supplémentaire",
        "description": "Ajout de monnaie",
        "performed_by_id": sample_user["id"],
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def sample_quick_key(sample_store: Dict[str, Any]) -> Dict[str, Any]:
    """Mock d'un quick key."""
    return {
        "id": 1,
        "tenant_id": "test-tenant-001",
        "store_id": sample_store["id"],
        "product_id": 1,
        "page": 1,
        "position": 1,
        "button_text": "Café",
        "button_color": "#FF5733",
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def sample_user() -> Dict[str, Any]:
    """Mock d'un utilisateur POS."""
    return {
        "id": 1,
        "tenant_id": "test-tenant-001",
        "employee_code": "EMP001",
        "first_name": "John",
        "last_name": "Doe",
        "pin_code": "1234",
        "is_active": True,
        "is_manager": False,
        "can_void_transaction": False,
        "can_refund": False,
        "can_open_drawer": True,
        "can_close_session": True,
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def sample_dashboard() -> Dict[str, Any]:
    """Mock d'un dashboard."""
    return {
        "sales_today": 1500.00,
        "transactions_today": 25,
        "average_transaction_today": 60.00,
        "items_sold_today": 75,
        "active_sessions": 3,
        "active_terminals": 5,
        "cash_today": 800.00,
        "card_today": 650.00,
        "other_today": 50.00,
        "top_products": [
            {"name": "Produit A", "quantity": 20, "total": 400.00},
            {"name": "Produit B", "quantity": 15, "total": 300.00}
        ],
        "recent_transactions": [
            {
                "id": 1,
                "receipt_number": "T202601250000001",
                "total": 24.00,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
    }


# ============================================================================
# HELPER ASSERTIONS
# ============================================================================

def assert_store_response(data: Dict[str, Any], expected: Dict[str, Any] = None):
    """Vérifie la structure d'une réponse store."""
    assert "id" in data
    assert "tenant_id" in data
    assert "code" in data
    assert "name" in data
    assert "is_active" in data

    if expected:
        assert data["code"] == expected["code"]
        assert data["name"] == expected["name"]


def assert_terminal_response(data: Dict[str, Any], expected: Dict[str, Any] = None):
    """Vérifie la structure d'une réponse terminal."""
    assert "id" in data
    assert "tenant_id" in data
    assert "terminal_id" in data
    assert "name" in data
    assert "status" in data

    if expected:
        assert data["terminal_id"] == expected["terminal_id"]
        assert data["name"] == expected["name"]


def assert_session_response(data: Dict[str, Any]):
    """Vérifie la structure d'une réponse session."""
    assert "id" in data
    assert "session_number" in data
    assert "status" in data
    assert "opened_by_id" in data
    assert "total_sales" in data
    assert "transaction_count" in data


def assert_transaction_response(data: Dict[str, Any]):
    """Vérifie la structure d'une réponse transaction."""
    assert "id" in data
    assert "receipt_number" in data
    assert "status" in data
    assert "subtotal" in data
    assert "total" in data
    assert "amount_paid" in data
    assert "amount_due" in data
