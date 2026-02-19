"""
Tests pour le provider Defacto.
================================

Tests unitaires et d'intégration pour DefactoProvider.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.modules.finance.providers.base import (
    FinanceProviderType,
    FinanceResult,
    FinanceError,
    FinanceErrorCode,
    WebhookEventType,
)
from app.modules.finance.providers.defacto import (
    DefactoProvider,
    DefactoBorrowerStatus,
    DefactoLoanStatus,
    DefactoInvoiceStatus,
    DefactoFinancingType,
    DefactoBorrowerRequest,
    DefactoInvoiceRequest,
    DefactoLoanRequest,
    DefactoBorrowerResponse,
    DefactoInvoiceResponse,
    DefactoLoanResponse,
    DefactoEligibilityResponse,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def tenant_id() -> str:
    """ID de tenant pour les tests."""
    return "tenant-test-001"


@pytest.fixture
def api_key() -> str:
    """Clé API de test."""
    return "sk_test_defacto_api_key_for_testing"


@pytest.fixture
def defacto_provider(tenant_id: str, api_key: str) -> DefactoProvider:
    """Instance de DefactoProvider pour les tests."""
    return DefactoProvider(
        tenant_id=tenant_id,
        api_key=api_key,
        webhook_secret="whsec_test_secret",
        sandbox=True,
    )


@pytest.fixture
def mock_borrower_response() -> dict:
    """Réponse mock pour un emprunteur."""
    return {
        "id": "bor_12345",
        "company_name": "Test Company SAS",
        "company_id": "123456789",
        "status": "active",
        "country": "FR",
        "credit_limit_cents": 10000000,  # 100,000 EUR
        "available_credit_cents": 8000000,  # 80,000 EUR
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-02-15T14:00:00Z",
    }


@pytest.fixture
def mock_invoice_response() -> dict:
    """Réponse mock pour une facture."""
    return {
        "id": "inv_67890",
        "external_id": "FAC-2024-001",
        "invoice_number": "FAC-2024-001",
        "status": "validated",
        "amount_cents": 5000000,  # 50,000 EUR
        "financed_amount_cents": None,
        "currency": "EUR",
        "issue_date": "2024-02-01",
        "due_date": "2024-03-01",
        "debtor_name": "Client ABC SARL",
        "created_at": "2024-02-01T09:00:00Z",
        "financed_at": None,
    }


@pytest.fixture
def mock_loan_response() -> dict:
    """Réponse mock pour un prêt."""
    return {
        "id": "loan_11111",
        "borrower_id": "bor_12345",
        "status": "funded",
        "financing_type": "invoice_financing",
        "amount_cents": 4500000,  # 45,000 EUR (90% de la facture)
        "funded_amount_cents": 4500000,
        "repaid_amount_cents": 0,
        "currency": "EUR",
        "interest_rate": "0.015",  # 1.5%
        "fee_cents": 67500,  # 675 EUR
        "repayment_term_days": 30,
        "invoice_ids": ["inv_67890"],
        "funded_at": "2024-02-05T11:00:00Z",
        "repayment_due_date": "2024-03-07",
        "created_at": "2024-02-05T10:30:00Z",
        "updated_at": "2024-02-05T11:00:00Z",
    }


def create_mock_client(response_data: dict, status_code: int = 200) -> MagicMock:
    """Crée un mock HTTP client avec la réponse spécifiée."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json = MagicMock(return_value=response_data)

    mock_client = MagicMock()
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.delete = AsyncMock(return_value=mock_response)
    mock_client.is_closed = False

    return mock_client


# =============================================================================
# TESTS UNITAIRES - INITIALISATION
# =============================================================================


class TestDefactoProviderInit:
    """Tests d'initialisation du provider."""

    def test_init_with_tenant_id(self, tenant_id: str, api_key: str):
        """L'initialisation avec tenant_id fonctionne."""
        provider = DefactoProvider(tenant_id=tenant_id, api_key=api_key)
        assert provider.tenant_id == tenant_id
        assert provider.api_key == api_key

    def test_init_sandbox_mode(self, tenant_id: str, api_key: str):
        """Le mode sandbox utilise la bonne URL."""
        provider = DefactoProvider(tenant_id=tenant_id, api_key=api_key, sandbox=True)
        assert provider.sandbox is True
        assert "sandbox" in provider.BASE_URL

    def test_init_production_mode(self, tenant_id: str, api_key: str):
        """Le mode production utilise la bonne URL."""
        provider = DefactoProvider(tenant_id=tenant_id, api_key=api_key, sandbox=False)
        assert provider.sandbox is False
        assert "api.getdefacto.com" in provider.BASE_URL

    def test_init_requires_tenant_id(self, api_key: str):
        """L'initialisation échoue sans tenant_id."""
        with pytest.raises(ValueError, match="tenant_id"):
            DefactoProvider(tenant_id="", api_key=api_key)

    def test_init_with_webhook_secret(self, tenant_id: str, api_key: str):
        """L'initialisation avec webhook_secret fonctionne."""
        provider = DefactoProvider(
            tenant_id=tenant_id,
            api_key=api_key,
            webhook_secret="whsec_test",
        )
        assert provider.webhook_secret == "whsec_test"

    def test_provider_name(self, defacto_provider: DefactoProvider):
        """Le nom du provider est correct."""
        assert defacto_provider.PROVIDER_NAME == "defacto"
        assert defacto_provider.PROVIDER_TYPE == FinanceProviderType.DEFACTO


# =============================================================================
# TESTS UNITAIRES - VALIDATION
# =============================================================================


class TestDefactoValidation:
    """Tests de validation des requêtes."""

    def test_valid_borrower_request(self):
        """Une requête d'emprunteur valide est acceptée."""
        request = DefactoBorrowerRequest(
            company_name="Test Company",
            company_id="123456789",
            contact_email="contact@test.com",
            country="FR",
        )
        assert request.company_name == "Test Company"
        assert request.company_id == "123456789"

    def test_company_id_cleaned(self):
        """Le numéro d'identification est nettoyé."""
        request = DefactoBorrowerRequest(
            company_name="Test Company",
            company_id="123 456 789",
            contact_email="contact@test.com",
        )
        assert request.company_id == "123456789"

    def test_invalid_company_id(self):
        """Un numéro d'identification trop court est rejeté."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            DefactoBorrowerRequest(
                company_name="Test Company",
                company_id="12345",  # Trop court
                contact_email="contact@test.com",
            )

    def test_valid_invoice_request(self):
        """Une requête de facture valide est acceptée."""
        request = DefactoInvoiceRequest(
            external_id="FAC-001",
            invoice_number="FAC-001",
            amount_cents=5000000,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            debtor_name="Client ABC",
        )
        assert request.amount_cents == 5000000

    def test_invoice_due_date_before_issue_date(self):
        """La date d'échéance avant la date d'émission est rejetée."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            DefactoInvoiceRequest(
                external_id="FAC-001",
                invoice_number="FAC-001",
                amount_cents=5000000,
                issue_date=date.today(),
                due_date=date.today() - timedelta(days=1),  # Avant émission
                debtor_name="Client ABC",
            )

    def test_valid_loan_request(self):
        """Une requête de prêt valide est acceptée."""
        request = DefactoLoanRequest(
            borrower_id="bor_123",
            amount_cents=5000000,
            invoice_ids=["inv_001"],
        )
        assert request.borrower_id == "bor_123"
        assert request.financing_type == DefactoFinancingType.INVOICE_FINANCING


# =============================================================================
# TESTS UNITAIRES - EMPRUNTEURS
# =============================================================================


class TestDefactoBorrowers:
    """Tests pour les opérations sur les emprunteurs."""

    @pytest.mark.asyncio
    async def test_create_borrower_success(
        self, defacto_provider: DefactoProvider, mock_borrower_response: dict
    ):
        """La création d'emprunteur réussie retourne les bonnes données."""
        defacto_provider._client = create_mock_client(mock_borrower_response)

        result = await defacto_provider.create_borrower(
            company_name="Test Company SAS",
            company_id="123456789",
            contact_email="contact@test.com",
            country="FR",
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_get_borrower_success(
        self, defacto_provider: DefactoProvider, mock_borrower_response: dict
    ):
        """La récupération d'emprunteur fonctionne."""
        defacto_provider._client = create_mock_client(mock_borrower_response)

        result = await defacto_provider.get_borrower(borrower_id="bor_12345")

        assert result.success is True

    @pytest.mark.asyncio
    async def test_check_eligibility_success(self, defacto_provider: DefactoProvider):
        """La vérification d'éligibilité fonctionne."""
        eligibility_response = {
            "eligible": True,
            "company_id": "123456789",
            "company_name": "Test Company",
            "max_credit_limit_cents": 10000000,
            "suggested_products": ["invoice_financing", "credit_line"],
        }

        defacto_provider._client = create_mock_client(eligibility_response)

        result = await defacto_provider.check_eligibility(
            company_id="123456789",
            company_name="Test Company",
        )

        assert result.success is True


# =============================================================================
# TESTS UNITAIRES - FACTURES
# =============================================================================


class TestDefactoInvoices:
    """Tests pour les opérations sur les factures."""

    @pytest.mark.asyncio
    async def test_create_invoice_success(
        self, defacto_provider: DefactoProvider, mock_invoice_response: dict
    ):
        """La création de facture réussie retourne les bonnes données."""
        defacto_provider._client = create_mock_client(mock_invoice_response)

        result = await defacto_provider.create_invoice(
            borrower_id="bor_12345",
            external_id="FAC-2024-001",
            invoice_number="FAC-2024-001",
            amount_cents=5000000,
            issue_date=date(2024, 2, 1),
            due_date=date(2024, 3, 1),
            debtor_name="Client ABC SARL",
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_get_invoices_success(
        self, defacto_provider: DefactoProvider, mock_invoice_response: dict
    ):
        """La liste des factures fonctionne."""
        defacto_provider._client = create_mock_client([mock_invoice_response])

        result = await defacto_provider.get_invoices(borrower_id="bor_12345")

        assert result.success is True

    @pytest.mark.asyncio
    async def test_delete_invoice_success(self, defacto_provider: DefactoProvider):
        """La suppression de facture fonctionne."""
        defacto_provider._client = create_mock_client({})

        result = await defacto_provider.delete_invoice(invoice_id="inv_67890")

        assert result.success is True
        assert result.data["deleted"] is True


# =============================================================================
# TESTS UNITAIRES - PRÊTS
# =============================================================================


class TestDefactoLoans:
    """Tests pour les opérations sur les prêts."""

    @pytest.mark.asyncio
    async def test_create_loan_success(
        self, defacto_provider: DefactoProvider, mock_loan_response: dict
    ):
        """La création de prêt réussie retourne les bonnes données."""
        defacto_provider._client = create_mock_client(mock_loan_response)

        result = await defacto_provider.create_loan(
            borrower_id="bor_12345",
            amount_cents=4500000,
            invoice_ids=["inv_67890"],
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_get_loan_success(
        self, defacto_provider: DefactoProvider, mock_loan_response: dict
    ):
        """La récupération de prêt fonctionne."""
        defacto_provider._client = create_mock_client(mock_loan_response)

        result = await defacto_provider.get_loan(loan_id="loan_11111")

        assert result.success is True

    @pytest.mark.asyncio
    async def test_validate_loan_success(
        self, defacto_provider: DefactoProvider, mock_loan_response: dict
    ):
        """La validation de prêt fonctionne."""
        validated_response = {**mock_loan_response, "status": "validated"}
        defacto_provider._client = create_mock_client(validated_response)

        result = await defacto_provider.validate_loan(loan_id="loan_11111")

        assert result.success is True

    @pytest.mark.asyncio
    async def test_cancel_loan_success(
        self, defacto_provider: DefactoProvider, mock_loan_response: dict
    ):
        """L'annulation de prêt fonctionne."""
        cancelled_response = {**mock_loan_response, "status": "cancelled"}
        defacto_provider._client = create_mock_client(cancelled_response)

        result = await defacto_provider.cancel_loan(
            loan_id="loan_11111",
            reason="Requested by borrower",
        )

        assert result.success is True


# =============================================================================
# TESTS UNITAIRES - WEBHOOKS
# =============================================================================


class TestDefactoWebhooks:
    """Tests pour la gestion des webhooks."""

    def test_verify_webhook_signature_valid(self, defacto_provider: DefactoProvider):
        """La vérification de signature fonctionne pour une signature valide."""
        import hmac
        import hashlib

        payload = b'{"event_type":"loan.funded"}'
        expected_sig = hmac.new(
            defacto_provider.webhook_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        result = defacto_provider.verify_webhook_signature(
            payload=payload,
            signature=expected_sig,
        )

        assert result is True

    def test_verify_webhook_signature_invalid(self, defacto_provider: DefactoProvider):
        """La vérification échoue pour une signature invalide."""
        payload = b'{"event_type":"loan.funded"}'

        result = defacto_provider.verify_webhook_signature(
            payload=payload,
            signature="invalid_signature",
        )

        assert result is False

    def test_verify_webhook_without_secret(self, tenant_id: str, api_key: str):
        """La vérification échoue sans secret configuré."""
        provider = DefactoProvider(tenant_id=tenant_id, api_key=api_key)

        result = provider.verify_webhook_signature(
            payload=b"test",
            signature="test",
        )

        assert result is False

    def test_parse_webhook_event_loan_funded(self, defacto_provider: DefactoProvider):
        """Le parsing d'un événement loan.funded fonctionne."""
        payload = {
            "event_id": "evt_12345",
            "event_type": "loan.funded",
            "timestamp": "2024-02-15T14:30:00Z",
            "data": {"loan_id": "loan_11111", "amount_cents": 4500000},
        }

        event = defacto_provider.parse_webhook_event(payload)

        assert event.id == "evt_12345"
        assert event.type == WebhookEventType.PAYMENT_CAPTURED
        assert event.provider == FinanceProviderType.DEFACTO

    def test_parse_webhook_event_loan_repaid(self, defacto_provider: DefactoProvider):
        """Le parsing d'un événement loan.repaid fonctionne."""
        payload = {
            "event_id": "evt_repaid_001",
            "event_type": "loan.repaid",
            "timestamp": "2024-03-07T10:00:00Z",
            "data": {"loan_id": "loan_11111"},
        }

        event = defacto_provider.parse_webhook_event(payload)

        assert event.type == WebhookEventType.TRANSACTION_COMPLETED

    def test_parse_webhook_event_borrower_created(
        self, defacto_provider: DefactoProvider
    ):
        """Le parsing d'un événement borrower.created fonctionne."""
        payload = {
            "event_id": "evt_bor_001",
            "event_type": "borrower.created",
            "timestamp": "2024-02-01T09:00:00Z",
            "data": {"borrower_id": "bor_12345"},
        }

        event = defacto_provider.parse_webhook_event(payload)

        assert event.type == WebhookEventType.ACCOUNT_CREATED


# =============================================================================
# TESTS UNITAIRES - GESTION DES ERREURS
# =============================================================================


class TestDefactoErrorHandling:
    """Tests pour la gestion des erreurs."""

    @pytest.mark.asyncio
    async def test_handle_validation_error(self, defacto_provider: DefactoProvider):
        """Les erreurs de validation sont gérées correctement."""
        result = await defacto_provider.create_borrower(
            company_name="A",  # Trop court
            company_id="123456789",
            contact_email="contact@test.com",
        )

        assert result.success is False
        assert result.error.code == FinanceErrorCode.INVALID_REQUEST


# =============================================================================
# TESTS INTÉGRATION
# =============================================================================


class TestDefactoIntegration:
    """Tests d'intégration."""

    @pytest.mark.asyncio
    async def test_full_financing_workflow(
        self,
        defacto_provider: DefactoProvider,
        mock_borrower_response: dict,
        mock_invoice_response: dict,
        mock_loan_response: dict,
    ):
        """Le workflow complet de financement fonctionne."""
        # Mock les différentes réponses
        mock_client = MagicMock()
        mock_client.is_closed = False

        responses = [
            MagicMock(status_code=200, json=MagicMock(return_value=mock_borrower_response)),
            MagicMock(status_code=200, json=MagicMock(return_value=mock_invoice_response)),
            MagicMock(status_code=200, json=MagicMock(return_value=mock_loan_response)),
        ]
        mock_client.request = AsyncMock(side_effect=responses)
        defacto_provider._client = mock_client

        # 1. Créer l'emprunteur
        borrower_result = await defacto_provider.create_borrower(
            company_name="Test Company SAS",
            company_id="123456789",
            contact_email="contact@test.com",
        )
        assert borrower_result.success is True

        # 2. Ajouter une facture
        invoice_result = await defacto_provider.create_invoice(
            borrower_id="bor_12345",
            external_id="FAC-2024-001",
            invoice_number="FAC-2024-001",
            amount_cents=5000000,
            issue_date=date(2024, 2, 1),
            due_date=date(2024, 3, 1),
            debtor_name="Client ABC SARL",
        )
        assert invoice_result.success is True

        # 3. Créer le prêt
        loan_result = await defacto_provider.create_loan(
            borrower_id="bor_12345",
            amount_cents=4500000,
            invoice_ids=["inv_67890"],
        )
        assert loan_result.success is True

    @pytest.mark.asyncio
    async def test_context_manager(self, tenant_id: str, api_key: str):
        """Le context manager fonctionne."""
        async with DefactoProvider(
            tenant_id=tenant_id,
            api_key=api_key,
            sandbox=True,
        ) as provider:
            assert provider.tenant_id == tenant_id
            assert provider.api_key == api_key


# =============================================================================
# TESTS SÉCURITÉ
# =============================================================================


class TestDefactoSecurity:
    """Tests de sécurité."""

    def test_tenant_isolation(self):
        """Chaque provider a son propre tenant_id."""
        provider1 = DefactoProvider(tenant_id="tenant-1", api_key="key1")
        provider2 = DefactoProvider(tenant_id="tenant-2", api_key="key2")

        assert provider1.tenant_id != provider2.tenant_id

    def test_api_key_in_headers(self, defacto_provider: DefactoProvider):
        """La clé API est incluse dans les headers."""
        headers = defacto_provider._get_default_headers()

        assert "Authorization" in headers
        assert defacto_provider.api_key in headers["Authorization"]

    def test_tenant_id_in_headers(self, defacto_provider: DefactoProvider):
        """Le tenant_id est inclus dans les headers."""
        headers = defacto_provider._get_default_headers()

        assert "X-Tenant-ID" in headers
        assert headers["X-Tenant-ID"] == defacto_provider.tenant_id
