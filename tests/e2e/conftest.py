"""Configuration pytest pour tests E2E CORE SaaS v2."""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime

from app.main import app


@pytest.fixture
def e2e_client():
    """Client de test pour E2E."""
    return TestClient(app)


@pytest.fixture
def tenant_alpha():
    """Tenant Alpha pour tests E2E."""
    return {
        "tenant_id": "tenant-alpha-001",
        "name": "Alpha Corporation",
        "plan": "pro",
        "is_active": True
    }


@pytest.fixture
def tenant_beta():
    """Tenant Beta pour tests E2E (isolation)."""
    return {
        "tenant_id": "tenant-beta-002",
        "name": "Beta Industries",
        "plan": "essentiel",
        "is_active": True
    }


@pytest.fixture
def user_admin_alpha():
    """Utilisateur admin du tenant Alpha."""
    return {
        "user_id": "user-admin-alpha-001",
        "tenant_id": "tenant-alpha-001",
        "email": "admin@alpha.com",
        "role": "ADMIN",
        "name": "Admin Alpha"
    }


@pytest.fixture
def user_employee_alpha():
    """Utilisateur employé du tenant Alpha."""
    return {
        "user_id": "user-employee-alpha-002",
        "tenant_id": "tenant-alpha-001",
        "email": "employee@alpha.com",
        "role": "EMPLOYE",
        "name": "Employee Alpha"
    }


@pytest.fixture
def user_admin_beta():
    """Utilisateur admin du tenant Beta."""
    return {
        "user_id": "user-admin-beta-001",
        "tenant_id": "tenant-beta-002",
        "email": "admin@beta.com",
        "role": "ADMIN",
        "name": "Admin Beta"
    }


@pytest.fixture
def auth_headers_alpha_admin():
    """Headers d'authentification pour admin Alpha."""
    # Note: Dans un vrai test E2E, obtenir JWT via /auth/login
    # Pour simplifier, utiliser headers simulés
    return {
        "X-Tenant-ID": "tenant-alpha-001",
        "Authorization": "Bearer mock_jwt_alpha_admin"
    }


@pytest.fixture
def auth_headers_alpha_employee():
    """Headers d'authentification pour employee Alpha."""
    return {
        "X-Tenant-ID": "tenant-alpha-001",
        "Authorization": "Bearer mock_jwt_alpha_employee"
    }


@pytest.fixture
def auth_headers_beta_admin():
    """Headers d'authentification pour admin Beta."""
    return {
        "X-Tenant-ID": "tenant-beta-002",
        "Authorization": "Bearer mock_jwt_beta_admin"
    }


@pytest.fixture
def sample_customer_alpha():
    """Client exemple pour tenant Alpha."""
    return {
        "name": "Client Alpha Test",
        "email": "client@alphatest.com",
        "phone": "+33612345678",
        "company": "AlphaTest SARL",
        "siret": "12345678901234",
        "address_line1": "123 Rue Test",
        "city": "Paris",
        "postal_code": "75001",
        "country": "FR"
    }


@pytest.fixture
def sample_invoice_data():
    """Données facture exemple."""
    return {
        "customer_id": None,  # À remplir dans le test
        "invoice_number": f"INV-{datetime.now().strftime('%Y%m%d')}-TEST",
        "issue_date": datetime.now().isoformat(),
        "due_date": datetime.now().isoformat(),
        "currency": "EUR",
        "items": [
            {
                "description": "Service Test",
                "quantity": 1,
                "unit_price": 100.00,
                "tax_rate": 20.0
            }
        ]
    }


@pytest.fixture
def sample_payment_intent():
    """Données payment intent exemple."""
    return {
        "amount": 10000,  # 100.00 EUR en centimes
        "currency": "eur",
        "description": "Test payment intent E2E"
    }


@pytest.fixture
def e2e_cleanup():
    """Fixture de nettoyage après tests E2E."""
    # Setup
    cleanup_ids = {
        "customers": [],
        "invoices": [],
        "payment_intents": [],
        "devices": []
    }

    yield cleanup_ids

    # Teardown - nettoyer les ressources créées
    # Note: À implémenter selon besoin
    pass


@pytest.fixture
def mock_stripe_config():
    """Configuration Stripe mock pour tests E2E."""
    return {
        "api_key_test": "sk_test_mock_e2e",
        "webhook_secret": "whsec_test_mock_e2e",
        "is_live_mode": False
    }
