"""Tests pour le router v2 du module Marketplace - CORE SaaS v2."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.marketplace.models import OrderStatus

client = TestClient(app)
BASE_URL = "/v2/marketplace"


# ============================================================================
# TESTS PLANS
# ============================================================================

def test_get_plans(mock_marketplace_service):
    response = client.get(f"{BASE_URL}/plans")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_get_plans_all(mock_marketplace_service):
    response = client.get(f"{BASE_URL}/plans", params={"active_only": False})
    assert response.status_code == 200


def test_get_plan_success(mock_marketplace_service):
    response = client.get(f"{BASE_URL}/plans/2")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "pro"


def test_get_plan_by_code_success(mock_marketplace_service):
    response = client.get(f"{BASE_URL}/plans/code/pro")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "pro"


def test_get_plan_by_code_not_found(mock_marketplace_service):
    response = client.get(f"{BASE_URL}/plans/code/invalid")
    assert response.status_code == 404


# ============================================================================
# TESTS CHECKOUT
# ============================================================================

def test_create_checkout_success(mock_marketplace_service, sample_checkout_data):
    response = client.post(f"{BASE_URL}/checkout", json=sample_checkout_data)
    assert response.status_code == 201
    data = response.json()
    assert "order_id" in data
    assert "order_number" in data
    assert data["status"] == OrderStatus.PAYMENT_PENDING.value


def test_create_checkout_invalid_plan(mock_marketplace_service, sample_checkout_data):
    sample_checkout_data["plan_code"] = "invalid"
    response = client.post(f"{BASE_URL}/checkout", json=sample_checkout_data)
    # Depends on mock behavior - should return error
    # Adjust based on actual implementation
    assert response.status_code in [400, 404]


# ============================================================================
# TESTS DISCOUNT CODES
# ============================================================================

def test_validate_discount_code_valid(mock_marketplace_service):
    response = client.post(
        f"{BASE_URL}/discount/validate",
        params={
            "code": "PROMO20",
            "plan_code": "pro",
            "order_amount": 149.00
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["discount_type"] == "percent"


def test_validate_discount_code_invalid(mock_marketplace_service):
    response = client.post(
        f"{BASE_URL}/discount/validate",
        params={
            "code": "INVALID",
            "plan_code": "pro",
            "order_amount": 149.00
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False


# ============================================================================
# TESTS ORDERS
# ============================================================================

def test_list_orders(mock_marketplace_service):
    response = client.get(f"{BASE_URL}/orders")
    assert response.status_code == 200
    data = response.json()
    assert "orders" in data
    assert "total" in data


def test_list_orders_with_filters(mock_marketplace_service):
    response = client.get(
        f"{BASE_URL}/orders",
        params={"status": OrderStatus.COMPLETED.value}
    )
    assert response.status_code == 200


def test_list_orders_pagination(mock_marketplace_service):
    response = client.get(
        f"{BASE_URL}/orders",
        params={"skip": 0, "limit": 10}
    )
    assert response.status_code == 200


def test_get_order_success(mock_marketplace_service):
    response = client.get(f"{BASE_URL}/orders/order-123")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "order-123"


def test_get_order_by_number_success(mock_marketplace_service):
    response = client.get(f"{BASE_URL}/orders/number/CMD-20240101-ABCD")
    assert response.status_code == 200
    data = response.json()
    assert data["order_number"] == "CMD-20240101-ABCD"


def test_get_order_by_number_not_found(mock_marketplace_service):
    response = client.get(f"{BASE_URL}/orders/number/INVALID")
    assert response.status_code == 404


# ============================================================================
# TESTS PROVISIONING
# ============================================================================

def test_provision_tenant_success(mock_marketplace_service):
    response = client.post(f"{BASE_URL}/orders/order-123/provision")
    assert response.status_code == 200
    data = response.json()
    assert "tenant_id" in data
    assert "admin_email" in data
    assert "login_url" in data
    assert "temporary_password" in data


def test_provision_tenant_invalid_order(mock_marketplace_service):
    response = client.post(f"{BASE_URL}/orders/invalid/provision")
    assert response.status_code == 400


# ============================================================================
# TESTS WEBHOOKS
# ============================================================================

def test_stripe_webhook(mock_marketplace_service):
    webhook_payload = {
        "id": "evt_test_123",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_123"
            }
        }
    }

    response = client.post(
        f"{BASE_URL}/webhooks/stripe",
        json=webhook_payload,
        headers={"stripe-signature": "sig_test"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["received"] is True


# ============================================================================
# TESTS STATISTICS
# ============================================================================

def test_get_stats(mock_marketplace_service):
    response = client.get(f"{BASE_URL}/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_orders" in data
    assert "total_revenue" in data
    assert "conversion_rate" in data
    assert "by_plan" in data


# ============================================================================
# TESTS SEED DATA
# ============================================================================

def test_seed_default_plans(mock_marketplace_service):
    response = client.post(f"{BASE_URL}/seed/plans")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
