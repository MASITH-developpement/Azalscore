"""
Configuration et fixtures pour les tests du module Subscriptions
=================================================================
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Generator
from unittest.mock import Mock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.core.saas_context import SaaSContext, TenantScope, UserRole


# ============================================================================
# MOCK SAAS CONTEXT
# ============================================================================

@pytest.fixture
def mock_saas_context() -> SaaSContext:
    """Fixture de contexte SaaS pour les tests."""
    return SaaSContext(
        tenant_id="test-tenant-123",
        user_id=UUID("12345678-1234-5678-1234-567812345678"),
        role=UserRole.ADMIN,
        permissions={"subscriptions.*"},
        scope=TenantScope.TENANT,
        ip_address="127.0.0.1",
        user_agent="pytest",
        correlation_id="test-correlation-id"
    )


# ============================================================================
# DATA FIXTURES
# ============================================================================

@pytest.fixture
def plan_data() -> dict:
    """Données pour créer un plan."""
    return {
        "code": "PLAN_BASIC",
        "name": "Plan Basic",
        "description": "Plan de base pour petites entreprises",
        "interval": "monthly",
        "interval_count": 1,
        "base_price": Decimal("29.99"),
        "currency": "EUR",
        "trial_days": 14,
        "is_public": True,
        "max_users": 5,
        "features": ["feature1", "feature2"]
    }


@pytest.fixture
def addon_data() -> dict:
    """Données pour créer un add-on."""
    return {
        "plan_id": 1,
        "code": "ADDON_STORAGE",
        "name": "Stockage additionnel",
        "description": "100 GB de stockage supplémentaire",
        "price": Decimal("9.99"),
        "quantity": 1,
        "is_required": False
    }


@pytest.fixture
def subscription_data() -> dict:
    """Données pour créer un abonnement."""
    return {
        "plan_id": 1,
        "customer_id": 100,
        "customer_name": "Acme Corp",
        "customer_email": "contact@acme.com",
        "quantity": 1,
        "collection_method": "charge_automatically",
        "start_date": date.today()
    }


@pytest.fixture
def invoice_data() -> dict:
    """Données pour créer une facture."""
    return {
        "subscription_id": 1,
        "customer_id": 100,
        "customer_name": "Acme Corp",
        "customer_email": "contact@acme.com",
        "period_start": date(2024, 1, 1),
        "period_end": date(2024, 1, 31),
        "collection_method": "send_invoice",
        "lines": [
            {
                "description": "Abonnement Plan Basic - Janvier 2024",
                "item_type": "subscription",
                "quantity": 1,
                "unit_price": Decimal("29.99"),
                "discount_amount": Decimal("0"),
                "tax_rate": Decimal("20"),
                "period_start": date(2024, 1, 1),
                "period_end": date(2024, 1, 31)
            }
        ]
    }


@pytest.fixture
def payment_data() -> dict:
    """Données pour créer un paiement."""
    return {
        "invoice_id": 1,
        "amount": Decimal("35.99"),
        "currency": "EUR",
        "payment_method_type": "card",
        "payment_method_id": "pm_123456"
    }


@pytest.fixture
def coupon_data() -> dict:
    """Données pour créer un coupon."""
    return {
        "code": "SUMMER2024",
        "name": "Promotion d'été 2024",
        "discount_type": "percent",
        "discount_value": Decimal("20"),
        "valid_from": datetime.utcnow(),
        "valid_until": datetime(2024, 8, 31, 23, 59, 59),
        "max_redemptions": 100,
        "first_time_only": True
    }


@pytest.fixture
def usage_data() -> dict:
    """Données pour créer un enregistrement d'usage."""
    return {
        "subscription_item_id": 1,
        "quantity": Decimal("150"),
        "unit": "requests",
        "action": "increment",
        "timestamp": datetime.utcnow()
    }


# ============================================================================
# ENTITY FIXTURES (MOCKS)
# ============================================================================

@pytest.fixture
def sample_plan() -> dict:
    """Fixture d'un plan complet."""
    return {
        "id": 1,
        "tenant_id": "test-tenant-123",
        "code": "PLAN_BASIC",
        "name": "Plan Basic",
        "description": "Plan de base pour petites entreprises",
        "interval": "monthly",
        "interval_count": 1,
        "base_price": 29.99,
        "currency": "EUR",
        "trial_days": 14,
        "trial_once": True,
        "is_active": True,
        "is_public": True,
        "sort_order": 1,
        "max_users": 5,
        "max_storage_gb": 50,
        "features": ["feature1", "feature2"],
        "metadata": {},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_addon() -> dict:
    """Fixture d'un add-on complet."""
    return {
        "id": 1,
        "tenant_id": "test-tenant-123",
        "plan_id": 1,
        "code": "ADDON_STORAGE",
        "name": "Stockage additionnel",
        "description": "100 GB de stockage supplémentaire",
        "price": 9.99,
        "quantity": 1,
        "is_active": True,
        "is_required": False,
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_subscription() -> dict:
    """Fixture d'un abonnement complet."""
    today = date.today()
    return {
        "id": 1,
        "tenant_id": "test-tenant-123",
        "subscription_number": "SUB20240100001",
        "plan_id": 1,
        "customer_id": 100,
        "customer_name": "Acme Corp",
        "customer_email": "contact@acme.com",
        "status": "active",
        "quantity": 1,
        "current_users": 3,
        "trial_start": None,
        "trial_end": None,
        "current_period_start": today.isoformat(),
        "current_period_end": (today.replace(month=today.month + 1) if today.month < 12 else today.replace(year=today.year + 1, month=1)).isoformat(),
        "started_at": today.isoformat(),
        "ended_at": None,
        "canceled_at": None,
        "billing_cycle_anchor": 1,
        "collection_method": "charge_automatically",
        "discount_percent": 0,
        "mrr": 29.99,
        "arr": 359.88,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_invoice() -> dict:
    """Fixture d'une facture complète."""
    return {
        "id": 1,
        "tenant_id": "test-tenant-123",
        "subscription_id": 1,
        "invoice_number": "INV20240100001",
        "customer_id": 100,
        "customer_name": "Acme Corp",
        "customer_email": "contact@acme.com",
        "status": "draft",
        "period_start": date(2024, 1, 1).isoformat(),
        "period_end": date(2024, 1, 31).isoformat(),
        "subtotal": 29.99,
        "discount_amount": 0,
        "tax_amount": 6.00,
        "total": 35.99,
        "amount_paid": 0,
        "amount_remaining": 35.99,
        "currency": "EUR",
        "collection_method": "send_invoice",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_payment() -> dict:
    """Fixture d'un paiement complet."""
    return {
        "id": 1,
        "tenant_id": "test-tenant-123",
        "invoice_id": 1,
        "payment_number": "PAY20240100001",
        "customer_id": 100,
        "amount": 35.99,
        "currency": "EUR",
        "status": "succeeded",
        "payment_method_type": "card",
        "payment_method_id": "pm_123456",
        "refunded_amount": 0,
        "created_at": datetime.utcnow().isoformat(),
        "processed_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_coupon() -> dict:
    """Fixture d'un coupon complet."""
    return {
        "id": 1,
        "tenant_id": "test-tenant-123",
        "code": "SUMMER2024",
        "name": "Promotion d'été 2024",
        "discount_type": "percent",
        "discount_value": 20,
        "is_active": True,
        "valid_from": datetime.utcnow().isoformat(),
        "valid_until": datetime(2024, 8, 31, 23, 59, 59).isoformat(),
        "max_redemptions": 100,
        "times_redeemed": 5,
        "first_time_only": True,
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_metrics() -> dict:
    """Fixture de métriques complètes."""
    return {
        "id": 1,
        "tenant_id": "test-tenant-123",
        "metric_date": date.today().isoformat(),
        "mrr": 5000.00,
        "arr": 60000.00,
        "new_mrr": 500.00,
        "expansion_mrr": 200.00,
        "contraction_mrr": 50.00,
        "churned_mrr": 100.00,
        "total_subscriptions": 100,
        "active_subscriptions": 85,
        "trialing_subscriptions": 10,
        "canceled_subscriptions": 5,
        "new_subscriptions": 8,
        "churned_subscriptions": 2,
        "total_customers": 80,
        "churn_rate": 2.35,
        "arpu": 58.82,
        "created_at": datetime.utcnow().isoformat()
    }


# ============================================================================
# HELPER ASSERTIONS
# ============================================================================

def assert_plan_response(data: dict, expected: dict):
    """Vérifie qu'une réponse de plan contient les bonnes données."""
    assert data["id"] == expected["id"]
    assert data["code"] == expected["code"]
    assert data["name"] == expected["name"]
    assert data["interval"] == expected["interval"]
    assert float(data["base_price"]) == expected["base_price"]


def assert_subscription_response(data: dict, expected: dict):
    """Vérifie qu'une réponse d'abonnement contient les bonnes données."""
    assert data["id"] == expected["id"]
    assert data["subscription_number"] == expected["subscription_number"]
    assert data["status"] == expected["status"]
    assert data["customer_name"] == expected["customer_name"]


def assert_invoice_response(data: dict, expected: dict):
    """Vérifie qu'une réponse de facture contient les bonnes données."""
    assert data["id"] == expected["id"]
    assert data["invoice_number"] == expected["invoice_number"]
    assert data["status"] == expected["status"]
    assert float(data["total"]) == expected["total"]


def assert_pagination(response: dict, expected_total: int, expected_items: int):
    """Vérifie la structure de pagination."""
    assert "items" in response
    assert "total" in response
    assert response["total"] == expected_total
    assert len(response["items"]) == expected_items
