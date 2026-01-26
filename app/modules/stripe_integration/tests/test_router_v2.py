"""Tests pour le router v2 du module Stripe Integration - CORE SaaS v2."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
BASE_URL = "/v2/stripe"


# ============================================================================
# TESTS CONFIGURATION
# ============================================================================

def test_create_config_success(mock_stripe_service, sample_config_data):
    response = client.post(f"{BASE_URL}/config", json=sample_config_data)
    assert response.status_code == 201
    data = response.json()
    assert data["api_key_test"] == sample_config_data["api_key_test"]
    assert data["is_live_mode"] == sample_config_data["is_live_mode"]


def test_get_config_success(mock_stripe_service):
    response = client.get(f"{BASE_URL}/config")
    assert response.status_code == 200
    data = response.json()
    assert "api_key_test" in data
    assert "is_live_mode" in data


def test_update_config_success(mock_stripe_service):
    update_data = {"is_live_mode": True}
    response = client.patch(f"{BASE_URL}/config", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert "is_live_mode" in data


# ============================================================================
# TESTS CUSTOMERS
# ============================================================================

def test_create_customer_success(mock_stripe_service, sample_customer_data):
    response = client.post(f"{BASE_URL}/customers", json=sample_customer_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == sample_customer_data["email"]
    assert "stripe_customer_id" in data


def test_list_customers(mock_stripe_service):
    response = client.get(f"{BASE_URL}/customers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_customer_success(mock_stripe_service):
    response = client.get(f"{BASE_URL}/customers/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "stripe_customer_id" in data


def test_get_customer_not_found(mock_stripe_service):
    response = client.get(f"{BASE_URL}/customers/999")
    assert response.status_code == 404


def test_get_customer_by_crm_id_success(mock_stripe_service):
    response = client.get(f"{BASE_URL}/customers/crm/123")
    assert response.status_code == 200
    data = response.json()
    assert data["crm_customer_id"] == 123


def test_get_customer_by_crm_id_not_found(mock_stripe_service):
    response = client.get(f"{BASE_URL}/customers/crm/999")
    assert response.status_code == 404


def test_update_customer_success(mock_stripe_service):
    update_data = {
        "email": "newemail@example.com",
        "name": "Jane Doe"
    }
    response = client.patch(f"{BASE_URL}/customers/1", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == update_data["email"]


def test_update_customer_not_found(mock_stripe_service):
    update_data = {"email": "test@example.com"}
    response = client.patch(f"{BASE_URL}/customers/999", json=update_data)
    assert response.status_code == 404


def test_sync_customer_success(mock_stripe_service):
    response = client.post(f"{BASE_URL}/customers/1/sync")
    assert response.status_code == 200
    data = response.json()
    assert "updated_at" in data


# ============================================================================
# TESTS PAYMENT METHODS
# ============================================================================

def test_add_payment_method_success(mock_stripe_service):
    pm_data = {
        "customer_id": 1,
        "stripe_payment_method_id": "pm_test123",
        "is_default": True
    }
    response = client.post(f"{BASE_URL}/payment-methods", json=pm_data)
    assert response.status_code == 201
    data = response.json()
    assert data["stripe_payment_method_id"] == pm_data["stripe_payment_method_id"]
    assert data["is_default"] is True


def test_list_payment_methods(mock_stripe_service):
    response = client.get(f"{BASE_URL}/customers/1/payment-methods")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_delete_payment_method_success(mock_stripe_service):
    response = client.delete(f"{BASE_URL}/payment-methods/1")
    assert response.status_code == 204


def test_delete_payment_method_not_found(mock_stripe_service):
    response = client.delete(f"{BASE_URL}/payment-methods/999")
    assert response.status_code == 404


# ============================================================================
# TESTS SETUP INTENTS
# ============================================================================

def test_create_setup_intent_success(mock_stripe_service):
    setup_data = {
        "customer_id": 1
    }
    response = client.post(f"{BASE_URL}/setup-intents", json=setup_data)
    assert response.status_code == 200
    data = response.json()
    assert "client_secret" in data
    assert "status" in data


# ============================================================================
# TESTS PAYMENT INTENTS
# ============================================================================

def test_create_payment_intent_success(mock_stripe_service, sample_payment_intent_data):
    response = client.post(f"{BASE_URL}/payment-intents", json=sample_payment_intent_data)
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == sample_payment_intent_data["amount"]
    assert data["currency"] == sample_payment_intent_data["currency"]
    assert "client_secret" in data


def test_list_payment_intents(mock_stripe_service):
    response = client.get(f"{BASE_URL}/payment-intents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_payment_intents_with_filters(mock_stripe_service):
    response = client.get(
        f"{BASE_URL}/payment-intents",
        params={"customer_id": 1, "status": "succeeded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_payment_intent_success(mock_stripe_service):
    response = client.get(f"{BASE_URL}/payment-intents/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "stripe_payment_intent_id" in data


def test_get_payment_intent_not_found(mock_stripe_service):
    response = client.get(f"{BASE_URL}/payment-intents/999")
    assert response.status_code == 404


def test_confirm_payment_intent_success(mock_stripe_service):
    confirm_data = {
        "payment_method_id": "pm_test123"
    }
    response = client.post(f"{BASE_URL}/payment-intents/1/confirm", json=confirm_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "succeeded"


def test_confirm_payment_intent_not_found(mock_stripe_service):
    confirm_data = {"payment_method_id": "pm_test123"}
    response = client.post(f"{BASE_URL}/payment-intents/999/confirm", json=confirm_data)
    assert response.status_code == 400


def test_capture_payment_intent_success(mock_stripe_service):
    response = client.post(f"{BASE_URL}/payment-intents/1/capture")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "succeeded"


def test_capture_payment_intent_with_amount(mock_stripe_service):
    response = client.post(
        f"{BASE_URL}/payment-intents/1/capture",
        params={"amount": 500}
    )
    assert response.status_code == 200


def test_cancel_payment_intent_success(mock_stripe_service):
    response = client.post(f"{BASE_URL}/payment-intents/1/cancel")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "canceled"


# ============================================================================
# TESTS CHECKOUT SESSIONS
# ============================================================================

def test_create_checkout_session_success(mock_stripe_service):
    checkout_data = {
        "success_url": "https://example.com/success",
        "cancel_url": "https://example.com/cancel",
        "line_items": [
            {
                "price": "price_test123",
                "quantity": 1
            }
        ]
    }
    response = client.post(f"{BASE_URL}/checkout-sessions", json=checkout_data)
    assert response.status_code == 201
    data = response.json()
    assert "stripe_session_id" in data
    assert "url" in data


def test_get_checkout_session_success(mock_stripe_service):
    response = client.get(f"{BASE_URL}/checkout-sessions/cs_test123")
    assert response.status_code == 200
    data = response.json()
    assert data["stripe_session_id"] == "cs_test123"


# ============================================================================
# TESTS REFUNDS
# ============================================================================

def test_create_refund_success(mock_stripe_service):
    refund_data = {
        "payment_intent_id": 1,
        "amount": 500,
        "reason": "requested_by_customer"
    }
    response = client.post(f"{BASE_URL}/refunds", json=refund_data)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "succeeded"
    assert "stripe_refund_id" in data


def test_list_refunds(mock_stripe_service):
    response = client.get(f"{BASE_URL}/refunds")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_refunds_by_payment_intent(mock_stripe_service):
    response = client.get(f"{BASE_URL}/refunds", params={"payment_intent_id": 1})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ============================================================================
# TESTS PRODUCTS & PRICES
# ============================================================================

def test_create_product_success(mock_stripe_service):
    product_data = {
        "name": "Premium Plan",
        "description": "Monthly premium subscription",
        "active": True
    }
    response = client.post(f"{BASE_URL}/products", json=product_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == product_data["name"]
    assert "stripe_product_id" in data


def test_create_price_success(mock_stripe_service):
    price_data = {
        "product_id": 1,
        "unit_amount": 1000,
        "currency": "eur",
        "recurring_interval": "month"
    }
    response = client.post(f"{BASE_URL}/prices", json=price_data)
    assert response.status_code == 201
    data = response.json()
    assert data["unit_amount"] == price_data["unit_amount"]
    assert "stripe_price_id" in data


# ============================================================================
# TESTS STRIPE CONNECT
# ============================================================================

def test_create_connect_account_success(mock_stripe_service):
    account_data = {
        "email": "business@example.com",
        "country": "FR",
        "account_type": "standard"
    }
    response = client.post(f"{BASE_URL}/connect/accounts", json=account_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == account_data["email"]
    assert "stripe_account_id" in data


def test_get_connect_account_success(mock_stripe_service):
    response = client.get(f"{BASE_URL}/connect/accounts/acct_test123")
    assert response.status_code == 200
    data = response.json()
    assert data["stripe_account_id"] == "acct_test123"


# ============================================================================
# TESTS WEBHOOKS
# ============================================================================

def test_stripe_webhook_success(mock_stripe_service):
    webhook_payload = {
        "id": "evt_test_123",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_123",
                "metadata": {
                    "tenant_id": "test-tenant"
                }
            }
        }
    }
    response = client.post(
        f"{BASE_URL}/webhooks",
        json=webhook_payload,
        headers={"stripe-signature": "sig_test"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["received"] is True
    assert "webhook_id" in data


def test_stripe_webhook_missing_tenant(mock_stripe_service):
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
        f"{BASE_URL}/webhooks",
        json=webhook_payload,
        headers={"stripe-signature": "sig_test"}
    )
    assert response.status_code == 400


# ============================================================================
# TESTS DASHBOARD
# ============================================================================

def test_get_dashboard(mock_stripe_service):
    response = client.get(f"{BASE_URL}/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "total_customers" in data
    assert "total_payment_intents" in data
    assert "successful_payments" in data
    assert "total_revenue" in data
