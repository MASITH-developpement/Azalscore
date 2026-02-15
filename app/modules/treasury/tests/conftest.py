"""
Configuration pytest et fixtures communes pour les tests Treasury

Hérite des fixtures globales de app/conftest.py.

Fixtures spécifiques:
- Données de test: comptes, transactions, rapprochements
- Helpers pour assertions
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4, UUID

from app.modules.treasury.models import (
    AccountType,
    TransactionType,
)


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


# ============================================================================
# FIXTURES DONNÉES TREASURY
# ============================================================================

@pytest.fixture
def account_data():
    """Données pour créer un compte bancaire"""
    return {
        "code": "BNK001",
        "name": "Compte Courant Principal",
        "bank_name": "BNP Paribas",
        "iban": "FR7630004000031234567890143",
        "bic": "BNPAFRPP",
        "account_number": "12345678901",
        "account_type": "CURRENT",
        "balance": "10000.00",
        "currency": "EUR",
        "is_default": True,
        "is_active": True,
        "contact_name": "Jean Dupont",
        "contact_phone": "+33123456789",
        "contact_email": "contact@bank.fr",
        "notes": "Compte principal de l'entreprise"
    }


@pytest.fixture
def transaction_data(sample_account):
    """Données pour créer une transaction"""
    return {
        "account_id": str(sample_account["id"]),
        "date": datetime.utcnow().isoformat(),
        "value_date": datetime.utcnow().isoformat(),
        "description": "Virement client ABC",
        "reference": "VIR-2024-001",
        "bank_reference": "BANK-REF-12345",
        "amount": "1500.50",
        "currency": "EUR",
        "type": "CREDIT",
        "category": "VENTE",
        "notes": "Paiement facture INV-001"
    }


@pytest.fixture
def reconciliation_data():
    """Données pour rapprochement bancaire"""
    return {
        "document_type": "INVOICE",
        "document_id": str(uuid4())
    }


@pytest.fixture
def forecast_data():
    """Données de prévision de trésorerie"""
    today = date.today()
    return [
        {
            "date": (today + timedelta(days=i)).isoformat(),
            "projected_balance": str(Decimal("10000.00") + Decimal(i * 100)),
            "pending_in": str(Decimal("500.00")),
            "pending_out": str(Decimal("300.00"))
        }
        for i in range(30)
    ]


# ============================================================================
# FIXTURES ENTITÉS
# ============================================================================

@pytest.fixture
def sample_account(tenant_id, user_id):
    """Fixture pour un compte bancaire de test (mock response)"""
    account_id = uuid4()
    return {
        "id": str(account_id),
        "tenant_id": tenant_id,
        "code": "BNK-TEST-001",
        "name": "Compte Test",
        "bank_name": "Banque de Test",
        "iban": "FR7630004000031234567890143",
        "bic": "TESTFRPP",
        "account_number": "12345678901",
        "account_type": "CURRENT",
        "is_default": True,
        "is_active": True,
        "balance": "10000.00",
        "available_balance": "9500.00",
        "pending_in": "500.00",
        "pending_out": "0.00",
        "currency": "EUR",
        "opening_date": datetime.utcnow().isoformat(),
        "contact_name": "Contact Test",
        "contact_phone": "+33123456789",
        "contact_email": "test@bank.fr",
        "notes": "Compte de test",
        "last_sync": None,
        "last_statement_date": None,
        "transactions_count": 0,
        "unreconciled_count": 0,
        "created_by": str(user_id),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_transaction(tenant_id, sample_account):
    """Fixture pour une transaction de test (mock response)"""
    transaction_id = uuid4()
    return {
        "id": str(transaction_id),
        "tenant_id": tenant_id,
        "account_id": sample_account["id"],
        "account_name": sample_account["name"],
        "date": datetime.utcnow().isoformat(),
        "value_date": datetime.utcnow().isoformat(),
        "description": "Transaction Test",
        "reference": "TXN-TEST-001",
        "bank_reference": "BANK-REF-001",
        "amount": "1500.00",
        "currency": "EUR",
        "type": "CREDIT",
        "category": "VENTE",
        "notes": "Transaction de test",
        "reconciled": False,
        "reconciled_at": None,
        "reconciled_by": None,
        "linked_document": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_summary(sample_account):
    """Fixture pour un résumé de trésorerie (mock response)"""
    return {
        "total_balance": "10000.00",
        "total_pending_in": "500.00",
        "total_pending_out": "300.00",
        "forecast_7d": "10200.00",
        "forecast_30d": "11500.00",
        "accounts": [sample_account]
    }


@pytest.fixture
def sample_forecast():
    """Fixture pour des prévisions (mock response)"""
    today = date.today()
    return [
        {
            "date": (today + timedelta(days=i)).isoformat(),
            "projected_balance": str(Decimal("10000.00") + Decimal(i * 100)),
            "pending_in": str(Decimal("500.00")),
            "pending_out": str(Decimal("300.00"))
        }
        for i in range(7)
    ]


# ============================================================================
# HELPERS
# ============================================================================

def assert_account_response(data, expected_values=None):
    """Helper pour vérifier la structure d'une réponse de compte"""
    required_fields = [
        "id", "tenant_id", "code", "name", "bank_name", "iban",
        "account_type", "balance", "currency", "is_active",
        "created_at", "updated_at"
    ]

    for field in required_fields:
        assert field in data, f"Champ manquant: {field}"

    if expected_values:
        for key, value in expected_values.items():
            assert data[key] == value, f"Valeur incorrecte pour {key}: {data[key]} != {value}"


def assert_transaction_response(data, expected_values=None):
    """Helper pour vérifier la structure d'une réponse de transaction"""
    required_fields = [
        "id", "tenant_id", "account_id", "date", "value_date",
        "description", "amount", "currency", "type", "reconciled",
        "created_at", "updated_at"
    ]

    for field in required_fields:
        assert field in data, f"Champ manquant: {field}"

    if expected_values:
        for key, value in expected_values.items():
            assert data[key] == value, f"Valeur incorrecte pour {key}: {data[key]} != {value}"


def assert_paginated_response(data, min_items=0):
    """Helper pour vérifier la structure d'une réponse paginée"""
    required_fields = ["total", "page", "per_page", "pages", "items"]

    for field in required_fields:
        assert field in data, f"Champ manquant: {field}"

    assert isinstance(data["items"], list), "items doit être une liste"
    assert data["total"] >= min_items, f"Total insuffisant: {data['total']} < {min_items}"
    assert data["page"] >= 1, "page doit être >= 1"
    assert data["per_page"] >= 1, "per_page doit être >= 1"
