"""
Tests pour le Router Finance Providers V3.

Tests des endpoints REST pour Swan, NMI, Defacto, Solaris.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.finance.router_providers import (
    router,
    get_provider_registry,
    ProviderResponse,
    TransferRequest,
    PaymentRequest,
)
from app.modules.finance.providers.base import (
    FinanceProviderType,
    FinanceResult,
    FinanceError,
    FinanceErrorCode,
)
from app.modules.finance.providers.registry import FinanceProviderRegistry


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_registry():
    """Registry mocké."""
    registry = MagicMock(spec=FinanceProviderRegistry)
    registry.get_provider = AsyncMock(return_value=None)
    return registry


@pytest.fixture
def app(mock_registry):
    """Application FastAPI de test avec dépendances mockées."""
    test_app = FastAPI()
    test_app.include_router(router)

    # Override la dépendance
    async def override_get_registry():
        return mock_registry

    test_app.dependency_overrides[get_provider_registry] = override_get_registry
    return test_app


@pytest.fixture
def client(app):
    """Client de test."""
    return TestClient(app)


@pytest.fixture
def mock_swan_provider():
    """Provider Swan mocké."""
    provider = MagicMock()
    provider.get_accounts = AsyncMock()
    provider.get_transactions = AsyncMock()
    provider.create_transfer = AsyncMock()
    return provider


@pytest.fixture
def mock_nmi_provider():
    """Provider NMI mocké."""
    provider = MagicMock()
    provider.process_payment = AsyncMock()
    provider.authorize = AsyncMock()
    provider.capture = AsyncMock()
    provider.void = AsyncMock()
    provider.refund = AsyncMock()
    provider.create_vault_customer = AsyncMock()
    provider.charge_vault_customer = AsyncMock()
    return provider


@pytest.fixture
def mock_defacto_provider():
    """Provider Defacto mocké."""
    provider = MagicMock()
    provider.create_borrower = AsyncMock()
    provider.check_eligibility = AsyncMock()
    provider.create_invoice = AsyncMock()
    provider.create_loan = AsyncMock()
    provider.validate_loan = AsyncMock()
    return provider


@pytest.fixture
def mock_solaris_provider():
    """Provider Solaris mocké."""
    provider = MagicMock()
    provider.create_business = AsyncMock()
    provider.create_account = AsyncMock()
    provider.create_overdraft_application = AsyncMock()
    provider.create_transfer = AsyncMock()
    return provider


# =============================================================================
# TESTS SWAN
# =============================================================================


class TestSwanEndpoints:
    """Tests des endpoints Swan."""

    def test_list_accounts_provider_not_configured(self, client, mock_registry):
        """Test liste comptes - provider non configuré."""
        mock_registry.get_provider.return_value = None

        response = client.get("/v3/finance/providers/swan/accounts")

        assert response.status_code == 503
        assert "non configuré" in response.json()["detail"]

    def test_list_accounts_success(self, client, mock_registry, mock_swan_provider):
        """Test liste comptes - succès."""
        mock_swan_provider.get_accounts.return_value = FinanceResult(
            success=True,
            data={"accounts": [{"id": "acc-123", "iban": "FR76..."}]},
        )
        mock_registry.get_provider.return_value = mock_swan_provider

        response = client.get("/v3/finance/providers/swan/accounts")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["provider"] == "swan"
        assert "accounts" in data["data"]

    def test_list_transactions_success(self, client, mock_registry, mock_swan_provider):
        """Test liste transactions - succès."""
        mock_swan_provider.get_transactions.return_value = FinanceResult(
            success=True,
            data={"transactions": [{"id": "tx-123", "amount": 1000}]},
        )
        mock_registry.get_provider.return_value = mock_swan_provider

        response = client.get(
            "/v3/finance/providers/swan/transactions",
            params={"account_id": "acc-123", "limit": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_create_transfer_success(self, client, mock_registry, mock_swan_provider):
        """Test création virement - succès."""
        mock_swan_provider.create_transfer.return_value = FinanceResult(
            success=True,
            data={"transfer_id": "tr-123", "status": "pending"},
        )
        mock_registry.get_provider.return_value = mock_swan_provider

        response = client.post(
            "/v3/finance/providers/swan/transfers",
            json={
                "source_account_id": "acc-123",
                "beneficiary_iban": "FR7630001007941234567890185",
                "beneficiary_name": "John Doe",
                "amount": 10000,
                "currency": "EUR",
                "reference": "INV-2024-001",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["transfer_id"] == "tr-123"

    def test_create_transfer_error(self, client, mock_registry, mock_swan_provider):
        """Test création virement - erreur."""
        mock_swan_provider.create_transfer.return_value = FinanceResult(
            success=False,
            error=FinanceError(
                code=FinanceErrorCode.INSUFFICIENT_FUNDS,
                message="Solde insuffisant",
            ),
        )
        mock_registry.get_provider.return_value = mock_swan_provider

        response = client.post(
            "/v3/finance/providers/swan/transfers",
            json={
                "source_account_id": "acc-123",
                "beneficiary_iban": "FR7630001007941234567890185",
                "beneficiary_name": "John Doe",
                "amount": 10000,
            },
        )

        assert response.status_code == 201  # Toujours 201 car on retourne un ProviderResponse
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Solde insuffisant"


# =============================================================================
# TESTS NMI
# =============================================================================


class TestNMIEndpoints:
    """Tests des endpoints NMI."""

    def test_process_payment_success(self, client, mock_registry, mock_nmi_provider):
        """Test paiement - succès."""
        mock_nmi_provider.process_payment.return_value = FinanceResult(
            success=True,
            data={"transaction_id": "tx-nmi-123", "response_code": "100"},
        )
        mock_registry.get_provider.return_value = mock_nmi_provider

        response = client.post(
            "/v3/finance/providers/nmi/payments",
            json={
                "amount": 5000,
                "currency": "EUR",
                "card_number": "4111111111111111",
                "expiry_month": "12",
                "expiry_year": "25",
                "cvv": "123",
                "cardholder_name": "John Doe",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["provider"] == "nmi"

    def test_authorize_success(self, client, mock_registry, mock_nmi_provider):
        """Test autorisation - succès."""
        mock_nmi_provider.authorize.return_value = FinanceResult(
            success=True,
            data={"transaction_id": "auth-123", "authorization_code": "ABC123"},
        )
        mock_registry.get_provider.return_value = mock_nmi_provider

        response = client.post(
            "/v3/finance/providers/nmi/authorize",
            json={
                "amount": 5000,
                "card_number": "4111111111111111",
                "expiry_month": "12",
                "expiry_year": "25",
                "cvv": "123",
            },
        )

        assert response.status_code == 201
        assert response.json()["success"] is True

    def test_capture_success(self, client, mock_registry, mock_nmi_provider):
        """Test capture - succès."""
        mock_nmi_provider.capture.return_value = FinanceResult(
            success=True,
            data={"transaction_id": "auth-123", "captured": True},
        )
        mock_registry.get_provider.return_value = mock_nmi_provider

        response = client.post(
            "/v3/finance/providers/nmi/capture",
            json={"transaction_id": "auth-123"},
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_void_success(self, client, mock_registry, mock_nmi_provider):
        """Test annulation - succès."""
        mock_nmi_provider.void.return_value = FinanceResult(
            success=True,
            data={"transaction_id": "auth-123", "voided": True},
        )
        mock_registry.get_provider.return_value = mock_nmi_provider

        response = client.post(
            "/v3/finance/providers/nmi/void",
            json={"transaction_id": "auth-123"},
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_refund_success(self, client, mock_registry, mock_nmi_provider):
        """Test remboursement - succès."""
        mock_nmi_provider.refund.return_value = FinanceResult(
            success=True,
            data={"refund_id": "ref-123", "amount": 5000},
        )
        mock_registry.get_provider.return_value = mock_nmi_provider

        response = client.post(
            "/v3/finance/providers/nmi/refund",
            json={"transaction_id": "tx-123", "amount": 5000},
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_create_vault_customer_success(self, client, mock_registry, mock_nmi_provider):
        """Test création client vault - succès."""
        mock_nmi_provider.create_vault_customer.return_value = FinanceResult(
            success=True,
            data={"customer_vault_id": "vault-123"},
        )
        mock_registry.get_provider.return_value = mock_nmi_provider

        response = client.post(
            "/v3/finance/providers/nmi/vault/customers",
            json={
                "customer_id": "cust-123",
                "card_number": "4111111111111111",
                "expiry_month": "12",
                "expiry_year": "25",
            },
        )

        assert response.status_code == 201
        assert response.json()["success"] is True

    def test_charge_vault_customer_success(self, client, mock_registry, mock_nmi_provider):
        """Test facturation client vault - succès."""
        mock_nmi_provider.charge_vault_customer.return_value = FinanceResult(
            success=True,
            data={"transaction_id": "tx-vault-123"},
        )
        mock_registry.get_provider.return_value = mock_nmi_provider

        response = client.post(
            "/v3/finance/providers/nmi/vault/customers/vault-123/charge",
            json={"amount": 5000, "currency": "EUR"},
        )

        assert response.status_code == 201
        assert response.json()["success"] is True

    def test_payment_provider_not_configured(self, client, mock_registry):
        """Test paiement - provider non configuré."""
        mock_registry.get_provider.return_value = None

        response = client.post(
            "/v3/finance/providers/nmi/payments",
            json={
                "amount": 5000,
                "card_number": "4111111111111111",
                "expiry_month": "12",
                "expiry_year": "25",
                "cvv": "123",
            },
        )

        assert response.status_code == 503

    def test_payment_validation_error(self, client, mock_registry, mock_nmi_provider):
        """Test paiement - erreur validation."""
        mock_registry.get_provider.return_value = mock_nmi_provider

        # CVV trop court
        response = client.post(
            "/v3/finance/providers/nmi/payments",
            json={
                "amount": 5000,
                "card_number": "4111111111111111",
                "expiry_month": "12",
                "expiry_year": "25",
                "cvv": "12",  # Trop court
            },
        )

        assert response.status_code == 422  # Validation error


# =============================================================================
# TESTS DEFACTO
# =============================================================================


class TestDefactoEndpoints:
    """Tests des endpoints Defacto."""

    def test_create_borrower_success(self, client, mock_registry, mock_defacto_provider):
        """Test création emprunteur - succès."""
        mock_defacto_provider.create_borrower.return_value = FinanceResult(
            success=True,
            data={"borrower_id": "bor-123", "status": "created"},
        )
        mock_registry.get_provider.return_value = mock_defacto_provider

        response = client.post(
            "/v3/finance/providers/defacto/borrowers",
            json={
                "company_name": "ACME Corp",
                "siren": "123456789",
                "email": "contact@acme.com",
                "address_line1": "123 Rue de Paris",
                "postal_code": "75001",
                "city": "Paris",
                "legal_representative_first_name": "John",
                "legal_representative_last_name": "Doe",
                "legal_representative_email": "john@acme.com",
            },
        )

        assert response.status_code == 201
        assert response.json()["success"] is True

    def test_check_eligibility_success(self, client, mock_registry, mock_defacto_provider):
        """Test éligibilité - succès."""
        mock_defacto_provider.check_eligibility.return_value = FinanceResult(
            success=True,
            data={"eligible": True, "max_amount": 50000, "rate": 0.05},
        )
        mock_registry.get_provider.return_value = mock_defacto_provider

        response = client.post(
            "/v3/finance/providers/defacto/eligibility",
            json={
                "borrower_id": "bor-123",
                "amount": 25000,
                "duration_months": 12,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["eligible"] is True

    def test_create_invoice_success(self, client, mock_registry, mock_defacto_provider):
        """Test création facture - succès."""
        mock_defacto_provider.create_invoice.return_value = FinanceResult(
            success=True,
            data={"invoice_id": "inv-123"},
        )
        mock_registry.get_provider.return_value = mock_defacto_provider

        response = client.post(
            "/v3/finance/providers/defacto/invoices",
            json={
                "borrower_id": "bor-123",
                "invoice_number": "INV-2024-001",
                "amount": 10000,
                "issue_date": "2024-01-15",
                "due_date": "2024-02-15",
                "debtor_name": "Client SARL",
            },
        )

        assert response.status_code == 201
        assert response.json()["success"] is True

    def test_create_loan_success(self, client, mock_registry, mock_defacto_provider):
        """Test création prêt - succès."""
        mock_defacto_provider.create_loan.return_value = FinanceResult(
            success=True,
            data={"loan_id": "loan-123", "status": "pending"},
        )
        mock_registry.get_provider.return_value = mock_defacto_provider

        response = client.post(
            "/v3/finance/providers/defacto/loans",
            json={
                "borrower_id": "bor-123",
                "invoice_ids": ["inv-123", "inv-456"],
                "amount": 20000,
                "duration_months": 6,
            },
        )

        assert response.status_code == 201
        assert response.json()["success"] is True

    def test_validate_loan_success(self, client, mock_registry, mock_defacto_provider):
        """Test validation prêt - succès."""
        mock_defacto_provider.validate_loan.return_value = FinanceResult(
            success=True,
            data={"loan_id": "loan-123", "status": "validated"},
        )
        mock_registry.get_provider.return_value = mock_defacto_provider

        response = client.post(
            "/v3/finance/providers/defacto/loans/loan-123/validate",
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_defacto_provider_not_configured(self, client, mock_registry):
        """Test Defacto - provider non configuré."""
        mock_registry.get_provider.return_value = None

        response = client.post(
            "/v3/finance/providers/defacto/borrowers",
            json={
                "company_name": "ACME Corp",
                "siren": "123456789",
                "email": "contact@acme.com",
                "address_line1": "123 Rue de Paris",
                "postal_code": "75001",
                "city": "Paris",
                "legal_representative_first_name": "John",
                "legal_representative_last_name": "Doe",
                "legal_representative_email": "john@acme.com",
            },
        )

        assert response.status_code == 503


# =============================================================================
# TESTS SOLARIS
# =============================================================================


class TestSolarisEndpoints:
    """Tests des endpoints Solaris."""

    def test_create_business_success(self, client, mock_registry, mock_solaris_provider):
        """Test création entreprise - succès."""
        mock_solaris_provider.create_business.return_value = FinanceResult(
            success=True,
            data={"business_id": "bus-123", "status": "created"},
        )
        mock_registry.get_provider.return_value = mock_solaris_provider

        response = client.post(
            "/v3/finance/providers/solaris/businesses",
            json={
                "name": "ACME GmbH",
                "legal_form": "GmbH",
                "registration_number": "HRB123456",
                "address_line": "Hauptstraße 1",
                "postal_code": "10115",
                "city": "Berlin",
                "country": "DE",
            },
        )

        assert response.status_code == 201
        assert response.json()["success"] is True

    def test_create_account_success(self, client, mock_registry, mock_solaris_provider):
        """Test création compte - succès."""
        mock_solaris_provider.create_account.return_value = FinanceResult(
            success=True,
            data={"account_id": "acc-sol-123", "iban": "DE89370400440532013000"},
        )
        mock_registry.get_provider.return_value = mock_solaris_provider

        response = client.post(
            "/v3/finance/providers/solaris/accounts",
            json={
                "business_id": "bus-123",
                "account_type": "CHECKING",
                "currency": "EUR",
            },
        )

        assert response.status_code == 201
        assert response.json()["success"] is True

    def test_create_overdraft_success(self, client, mock_registry, mock_solaris_provider):
        """Test demande découvert - succès."""
        mock_solaris_provider.create_overdraft_application.return_value = FinanceResult(
            success=True,
            data={"application_id": "od-123", "status": "pending"},
        )
        mock_registry.get_provider.return_value = mock_solaris_provider

        response = client.post(
            "/v3/finance/providers/solaris/overdrafts",
            json={
                "account_id": "acc-sol-123",
                "amount": 10000,
                "duration_days": 30,
                "purpose": "Working capital",
            },
        )

        assert response.status_code == 201
        assert response.json()["success"] is True

    def test_create_transfer_success(self, client, mock_registry, mock_solaris_provider):
        """Test création virement - succès."""
        mock_solaris_provider.create_transfer.return_value = FinanceResult(
            success=True,
            data={"transfer_id": "tr-sol-123", "status": "pending"},
        )
        mock_registry.get_provider.return_value = mock_solaris_provider

        response = client.post(
            "/v3/finance/providers/solaris/transfers",
            json={
                "account_id": "acc-sol-123",
                "recipient_iban": "FR7630001007941234567890185",
                "recipient_name": "Fournisseur SARL",
                "amount": 5000,
                "currency": "EUR",
                "reference": "INV-2024-002",
            },
        )

        assert response.status_code == 201
        assert response.json()["success"] is True

    def test_solaris_provider_not_configured(self, client, mock_registry):
        """Test Solaris - provider non configuré."""
        mock_registry.get_provider.return_value = None

        response = client.post(
            "/v3/finance/providers/solaris/businesses",
            json={
                "name": "ACME GmbH",
                "legal_form": "GmbH",
                "registration_number": "HRB123456",
                "address_line": "Hauptstraße 1",
                "postal_code": "10115",
                "city": "Berlin",
            },
        )

        assert response.status_code == 503


# =============================================================================
# TESTS HEALTH CHECK
# =============================================================================


class TestHealthCheck:
    """Tests du health check."""

    def test_health_check_all_providers(self, client, mock_registry):
        """Test health check - tous providers."""
        mock_registry.get_provider.return_value = None  # Non configurés

        response = client.get("/v3/finance/providers/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "providers" in data
        assert "swan" in data["providers"]
        assert "nmi" in data["providers"]
        assert "defacto" in data["providers"]
        assert "solaris" in data["providers"]


# =============================================================================
# TESTS VALIDATION
# =============================================================================


class TestValidation:
    """Tests de validation des requêtes."""

    def test_transfer_invalid_amount(self, client, mock_registry):
        """Test virement - montant invalide."""
        response = client.post(
            "/v3/finance/providers/swan/transfers",
            json={
                "source_account_id": "acc-123",
                "beneficiary_iban": "FR7630001007941234567890185",
                "beneficiary_name": "John Doe",
                "amount": -100,  # Négatif
            },
        )

        assert response.status_code == 422

    def test_payment_invalid_card_number(self, client, mock_registry):
        """Test paiement - numéro carte invalide."""
        response = client.post(
            "/v3/finance/providers/nmi/payments",
            json={
                "amount": 5000,
                "card_number": "123",  # Trop court
                "expiry_month": "12",
                "expiry_year": "25",
                "cvv": "123",
            },
        )

        assert response.status_code == 422

    def test_borrower_invalid_siren(self, client, mock_registry):
        """Test emprunteur - SIREN invalide."""
        response = client.post(
            "/v3/finance/providers/defacto/borrowers",
            json={
                "company_name": "ACME Corp",
                "siren": "123",  # Trop court (doit être 9 chiffres)
                "email": "contact@acme.com",
                "address_line1": "123 Rue de Paris",
                "postal_code": "75001",
                "city": "Paris",
                "legal_representative_first_name": "John",
                "legal_representative_last_name": "Doe",
                "legal_representative_email": "john@acme.com",
            },
        )

        assert response.status_code == 422

    def test_loan_empty_invoices(self, client, mock_registry):
        """Test prêt - liste factures vide."""
        response = client.post(
            "/v3/finance/providers/defacto/loans",
            json={
                "borrower_id": "bor-123",
                "invoice_ids": [],  # Vide
                "amount": 20000,
                "duration_months": 6,
            },
        )

        assert response.status_code == 422

    def test_overdraft_duration_too_long(self, client, mock_registry):
        """Test découvert - durée trop longue."""
        response = client.post(
            "/v3/finance/providers/solaris/overdrafts",
            json={
                "account_id": "acc-123",
                "amount": 10000,
                "duration_days": 400,  # > 365
                "purpose": "Test",
            },
        )

        assert response.status_code == 422

    def test_expiry_month_invalid_format(self, client, mock_registry):
        """Test paiement - mois expiration invalide."""
        response = client.post(
            "/v3/finance/providers/nmi/payments",
            json={
                "amount": 5000,
                "card_number": "4111111111111111",
                "expiry_month": "1",  # Doit être 2 chiffres
                "expiry_year": "25",
                "cvv": "123",
            },
        )

        assert response.status_code == 422
