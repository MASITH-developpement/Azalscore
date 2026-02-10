"""Tests pour le router v2 du module Marketplace - CORE SaaS v2."""

import pytest

from app.modules.marketplace.models import OrderStatus

BASE_URL = "/v2/marketplace"


# ============================================================================
# TESTS PLANS
# ============================================================================

def test_get_plans(test_client):
    response = test_client.get(f"{BASE_URL}/plans")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_get_plans_all(test_client):
    response = test_client.get(f"{BASE_URL}/plans", params={"active_only": False})
    assert response.status_code == 200


def test_get_plan_success(test_client):
    response = test_client.get(f"{BASE_URL}/plans/2")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "pro"


def test_get_plan_by_code_success(test_client):
    response = test_client.get(f"{BASE_URL}/plans/code/pro")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "pro"


def test_get_plan_by_code_not_found(test_client):
    response = test_client.get(f"{BASE_URL}/plans/code/invalid")
    assert response.status_code == 404


# ============================================================================
# TESTS CHECKOUT
# ============================================================================

def test_create_checkout_success(test_client, mock_marketplace_service, sample_checkout_data):
    response = test_client.post(f"{BASE_URL}/checkout", json=sample_checkout_data)
    assert response.status_code == 201
    data = response.json()
    assert "order_id" in data
    assert "order_number" in data
    assert data["status"] == OrderStatus.PAYMENT_PENDING.value


def test_create_checkout_invalid_plan(test_client, mock_marketplace_service, sample_checkout_data):
    sample_checkout_data["plan_code"] = "invalid"
    response = test_client.post(f"{BASE_URL}/checkout", json=sample_checkout_data)
    # Depends on mock behavior - should return error
    # Adjust based on actual implementation
    assert response.status_code in [400, 404]


# ============================================================================
# TESTS DISCOUNT CODES
# ============================================================================

def test_validate_discount_code_valid(test_client):
    response = test_client.post(
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


def test_validate_discount_code_invalid(test_client):
    response = test_client.post(
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

def test_list_orders(test_client):
    response = test_client.get(f"{BASE_URL}/orders")
    assert response.status_code == 200
    data = response.json()
    assert "orders" in data
    assert "total" in data


def test_list_orders_with_filters(test_client):
    response = test_client.get(
        f"{BASE_URL}/orders",
        params={"status": OrderStatus.COMPLETED.value}
    )
    assert response.status_code == 200


def test_list_orders_pagination(test_client):
    response = test_client.get(
        f"{BASE_URL}/orders",
        params={"skip": 0, "limit": 10}
    )
    assert response.status_code == 200


def test_get_order_success(test_client):
    response = test_client.get(f"{BASE_URL}/orders/order-123")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "order-123"


def test_get_order_by_number_success(test_client):
    response = test_client.get(f"{BASE_URL}/orders/number/CMD-20240101-ABCD")
    assert response.status_code == 200
    data = response.json()
    assert data["order_number"] == "CMD-20240101-ABCD"


def test_get_order_by_number_not_found(test_client):
    response = test_client.get(f"{BASE_URL}/orders/number/INVALID")
    assert response.status_code == 404


# ============================================================================
# TESTS PROVISIONING
# ============================================================================

def test_provision_tenant_success(test_client):
    response = test_client.post(f"{BASE_URL}/orders/order-123/provision")
    assert response.status_code == 200
    data = response.json()
    assert "tenant_id" in data
    assert "admin_email" in data
    assert "login_url" in data
    assert "temporary_password" in data


def test_provision_tenant_invalid_order(test_client):
    response = test_client.post(f"{BASE_URL}/orders/invalid/provision")
    assert response.status_code == 400


# ============================================================================
# TESTS WEBHOOKS
# ============================================================================

def test_stripe_webhook(test_client):
    webhook_payload = {
        "id": "evt_test_123",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_123"
            }
        }
    }

    response = test_client.post(
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

def test_get_stats(test_client):
    response = test_client.get(f"{BASE_URL}/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_orders" in data
    assert "total_revenue" in data
    assert "conversion_rate" in data
    assert "by_plan" in data


# ============================================================================
# TESTS SEED DATA
# ============================================================================

def test_seed_default_plans(test_client):
    response = test_client.post(f"{BASE_URL}/seed/plans")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
