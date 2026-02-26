"""
Tests pour le provider NMI.
=============================

Tests unitaires et d'intégration pour NMIProvider.
"""

import pytest
from datetime import datetime
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
from app.modules.finance.providers.nmi import (
    NMIProvider,
    NMITransactionType,
    NMIResponseCode,
    NMIPaymentRequest,
    NMITransactionResponse,
    NMIVaultResponse,
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
    return "sk_test_nmi_api_key_for_testing"


@pytest.fixture
def nmi_provider(tenant_id: str, api_key: str) -> NMIProvider:
    """Instance de NMIProvider pour les tests."""
    return NMIProvider(
        tenant_id=tenant_id,
        api_key=api_key,
        webhook_secret="whsec_test_secret",
        sandbox=True,
    )


@pytest.fixture
def mock_success_response() -> str:
    """Réponse mock pour une transaction réussie."""
    return (
        "response=1&"
        "responsetext=SUCCESS&"
        "authcode=123456&"
        "transactionid=txn_987654321&"
        "avsresponse=Y&"
        "cvvresponse=M&"
        "orderid=order-001&"
        "type=sale&"
        "cc_type=visa"
    )


@pytest.fixture
def mock_declined_response() -> str:
    """Réponse mock pour une transaction refusée."""
    return (
        "response=2&"
        "responsetext=DECLINE - Insufficient funds&"
        "transactionid=txn_declined_001&"
        "avsresponse=N&"
        "cvvresponse=M"
    )


@pytest.fixture
def mock_error_response() -> str:
    """Réponse mock pour une erreur."""
    return (
        "response=3&"
        "responsetext=Invalid credit card number&"
        "transactionid="
    )


def create_mock_client(response_text: str, status_code: int = 200) -> MagicMock:
    """Crée un mock HTTP client avec la réponse spécifiée."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.text = response_text

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.is_closed = False

    return mock_client


# =============================================================================
# TESTS UNITAIRES - INITIALISATION
# =============================================================================


class TestNMIProviderInit:
    """Tests d'initialisation du provider."""

    def test_init_with_tenant_id(self, tenant_id: str, api_key: str):
        """L'initialisation avec tenant_id fonctionne."""
        provider = NMIProvider(tenant_id=tenant_id, api_key=api_key)
        assert provider.tenant_id == tenant_id
        assert provider.api_key == api_key

    def test_init_sandbox_mode(self, tenant_id: str, api_key: str):
        """Le mode sandbox utilise la bonne URL."""
        provider = NMIProvider(tenant_id=tenant_id, api_key=api_key, sandbox=True)
        assert provider.sandbox is True
        assert "sandbox" in provider.BASE_URL

    def test_init_production_mode(self, tenant_id: str, api_key: str):
        """Le mode production utilise la bonne URL."""
        provider = NMIProvider(tenant_id=tenant_id, api_key=api_key, sandbox=False)
        assert provider.sandbox is False
        assert "networkmerchants" in provider.BASE_URL

    def test_init_requires_tenant_id(self, api_key: str):
        """L'initialisation échoue sans tenant_id."""
        with pytest.raises(ValueError, match="tenant_id"):
            NMIProvider(tenant_id="", api_key=api_key)

    def test_init_with_webhook_secret(self, tenant_id: str, api_key: str):
        """L'initialisation avec webhook_secret fonctionne."""
        provider = NMIProvider(
            tenant_id=tenant_id,
            api_key=api_key,
            webhook_secret="whsec_test",
        )
        assert provider.webhook_secret == "whsec_test"

    def test_provider_name(self, nmi_provider: NMIProvider):
        """Le nom du provider est correct."""
        assert nmi_provider.PROVIDER_NAME == "nmi"
        assert nmi_provider.PROVIDER_TYPE == FinanceProviderType.NMI


# =============================================================================
# TESTS UNITAIRES - VALIDATION
# =============================================================================


class TestNMIValidation:
    """Tests de validation des requêtes."""

    def test_valid_payment_request(self):
        """Une requête de paiement valide est acceptée."""
        request = NMIPaymentRequest(
            amount=5000,
            card_number="4111111111111111",
            exp_month="12",
            exp_year="25",
        )
        assert request.amount == 5000
        assert request.card_number == "4111111111111111"

    def test_card_number_with_spaces(self):
        """Les numéros de carte avec espaces sont nettoyés."""
        request = NMIPaymentRequest(
            amount=1000,
            card_number="4111 1111 1111 1111",
            exp_month="12",
            exp_year="25",
        )
        assert request.card_number == "4111111111111111"

    def test_card_number_with_dashes(self):
        """Les numéros de carte avec tirets sont nettoyés."""
        request = NMIPaymentRequest(
            amount=1000,
            card_number="4111-1111-1111-1111",
            exp_month="12",
            exp_year="25",
        )
        assert request.card_number == "4111111111111111"

    def test_invalid_card_number_luhn(self):
        """Un numéro de carte invalide (Luhn) est rejeté."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            NMIPaymentRequest(
                amount=1000,
                card_number="4111111111111112",  # Invalid Luhn
                exp_month="12",
                exp_year="25",
            )

    def test_invalid_card_number_too_short(self):
        """Un numéro de carte trop court est rejeté."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            NMIPaymentRequest(
                amount=1000,
                card_number="411111",
                exp_month="12",
                exp_year="25",
            )

    def test_exp_year_normalization(self):
        """L'année d'expiration est normalisée à 2 chiffres."""
        request = NMIPaymentRequest(
            amount=1000,
            card_number="4111111111111111",
            exp_month="12",
            exp_year="2025",
        )
        assert request.exp_year == "25"

    def test_negative_amount_rejected(self):
        """Un montant négatif est rejeté."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            NMIPaymentRequest(
                amount=-100,
                card_number="4111111111111111",
                exp_month="12",
                exp_year="25",
            )

    def test_zero_amount_rejected(self):
        """Un montant de zéro est rejeté."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            NMIPaymentRequest(
                amount=0,
                card_number="4111111111111111",
                exp_month="12",
                exp_year="25",
            )


# =============================================================================
# TESTS UNITAIRES - TRANSACTIONS
# =============================================================================


class TestNMITransactions:
    """Tests pour les opérations de transaction."""

    @pytest.mark.asyncio
    async def test_process_payment_success(
        self, nmi_provider: NMIProvider, mock_success_response: str
    ):
        """Un paiement réussi retourne les bonnes données."""
        nmi_provider._client = create_mock_client(mock_success_response)

        result = await nmi_provider.process_payment(
            amount=5000,
            card_number="4111111111111111",
            exp_month="12",
            exp_year="25",
            cvv="123",
            order_id="order-001",
        )

        assert result.success is True
        assert result.data.transaction_id == "txn_987654321"
        assert result.data.response_code == NMIResponseCode.APPROVED
        assert result.data.is_approved is True
        assert result.data.auth_code == "123456"

    @pytest.mark.asyncio
    async def test_process_payment_declined(
        self, nmi_provider: NMIProvider, mock_declined_response: str
    ):
        """Un paiement refusé retourne une erreur appropriée."""
        nmi_provider._client = create_mock_client(mock_declined_response)

        result = await nmi_provider.process_payment(
            amount=5000,
            card_number="4111111111111111",
            exp_month="12",
            exp_year="25",
        )

        assert result.success is False
        assert result.error.code == FinanceErrorCode.TRANSACTION_REJECTED
        assert "Insufficient funds" in result.error.message

    @pytest.mark.asyncio
    async def test_process_payment_error(
        self, nmi_provider: NMIProvider, mock_error_response: str
    ):
        """Une erreur de transaction retourne une erreur appropriée."""
        nmi_provider._client = create_mock_client(mock_error_response)

        result = await nmi_provider.process_payment(
            amount=5000,
            card_number="4111111111111111",
            exp_month="12",
            exp_year="25",
        )

        assert result.success is False
        assert result.error.code == FinanceErrorCode.SERVICE_UNAVAILABLE

    @pytest.mark.asyncio
    async def test_authorize_success(
        self, nmi_provider: NMIProvider, mock_success_response: str
    ):
        """Une autorisation réussie retourne les bonnes données."""
        mock_client = create_mock_client(mock_success_response)
        nmi_provider._client = mock_client

        result = await nmi_provider.authorize(
            amount=5000,
            card_number="4111111111111111",
            exp_month="12",
            exp_year="25",
        )

        assert result.success is True
        assert result.data.transaction_id == "txn_987654321"

        # Vérifier que le type était "auth"
        call_args = mock_client.post.call_args
        assert call_args[1]["data"]["type"] == "auth"

    @pytest.mark.asyncio
    async def test_capture_success(
        self, nmi_provider: NMIProvider, mock_success_response: str
    ):
        """Une capture réussie retourne les bonnes données."""
        mock_client = create_mock_client(mock_success_response)
        nmi_provider._client = mock_client

        result = await nmi_provider.capture(
            transaction_id="txn_auth_001",
            amount=5000,
        )

        assert result.success is True

        # Vérifier les paramètres
        call_args = mock_client.post.call_args
        assert call_args[1]["data"]["type"] == "capture"
        assert call_args[1]["data"]["transactionid"] == "txn_auth_001"

    @pytest.mark.asyncio
    async def test_void_success(
        self, nmi_provider: NMIProvider, mock_success_response: str
    ):
        """Une annulation réussie fonctionne."""
        mock_client = create_mock_client(mock_success_response)
        nmi_provider._client = mock_client

        result = await nmi_provider.void(transaction_id="txn_to_void")

        assert result.success is True

        call_args = mock_client.post.call_args
        assert call_args[1]["data"]["type"] == "void"

    @pytest.mark.asyncio
    async def test_refund_success(
        self, nmi_provider: NMIProvider, mock_success_response: str
    ):
        """Un remboursement réussi fonctionne."""
        mock_client = create_mock_client(mock_success_response)
        nmi_provider._client = mock_client

        result = await nmi_provider.refund(
            transaction_id="txn_to_refund",
            amount=2500,  # Partial refund
        )

        assert result.success is True

        call_args = mock_client.post.call_args
        assert call_args[1]["data"]["type"] == "refund"
        assert call_args[1]["data"]["amount"] == "25.00"


# =============================================================================
# TESTS UNITAIRES - CUSTOMER VAULT
# =============================================================================


class TestNMICustomerVault:
    """Tests pour le Customer Vault (tokenisation)."""

    @pytest.mark.asyncio
    async def test_create_vault_customer_success(self, nmi_provider: NMIProvider):
        """La création d'un client vault fonctionne."""
        vault_response = (
            "response=1&"
            "responsetext=Customer Added&"
            "customer_vault_id=cust_vault_123&"
            "cc_type=visa"
        )

        nmi_provider._client = create_mock_client(vault_response)

        result = await nmi_provider.create_vault_customer(
            card_number="4111111111111111",
            exp_month="12",
            exp_year="25",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )

        assert result.success is True
        assert result.data.customer_vault_id == "cust_vault_123"

    @pytest.mark.asyncio
    async def test_charge_vault_customer_success(
        self, nmi_provider: NMIProvider, mock_success_response: str
    ):
        """Le débit d'un client vault fonctionne."""
        mock_client = create_mock_client(mock_success_response)
        nmi_provider._client = mock_client

        result = await nmi_provider.charge_vault_customer(
            customer_vault_id="cust_vault_123",
            amount=5000,
            order_id="order-vault-001",
        )

        assert result.success is True

        call_args = mock_client.post.call_args
        assert call_args[1]["data"]["customer_vault_id"] == "cust_vault_123"

    @pytest.mark.asyncio
    async def test_delete_vault_customer_success(self, nmi_provider: NMIProvider):
        """La suppression d'un client vault fonctionne."""
        delete_response = "response=1&responsetext=Customer Deleted"

        nmi_provider._client = create_mock_client(delete_response)

        result = await nmi_provider.delete_vault_customer(
            customer_vault_id="cust_vault_123"
        )

        assert result.success is True
        assert result.data["deleted"] is True


# =============================================================================
# TESTS UNITAIRES - WEBHOOKS
# =============================================================================


class TestNMIWebhooks:
    """Tests pour la gestion des webhooks."""

    def test_verify_webhook_signature_valid(self, nmi_provider: NMIProvider):
        """La vérification de signature fonctionne pour une signature valide."""
        import hmac
        import hashlib

        payload = b'{"event_type":"transaction.sale.success"}'
        expected_sig = hmac.new(
            nmi_provider.webhook_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        result = nmi_provider.verify_webhook_signature(
            payload=payload,
            signature=expected_sig,
        )

        assert result is True

    def test_verify_webhook_signature_invalid(self, nmi_provider: NMIProvider):
        """La vérification échoue pour une signature invalide."""
        payload = b'{"event_type":"transaction.sale.success"}'

        result = nmi_provider.verify_webhook_signature(
            payload=payload,
            signature="invalid_signature",
        )

        assert result is False

    def test_verify_webhook_without_secret(self, tenant_id: str, api_key: str):
        """La vérification échoue sans secret configuré."""
        provider = NMIProvider(tenant_id=tenant_id, api_key=api_key)

        result = provider.verify_webhook_signature(
            payload=b"test",
            signature="test",
        )

        assert result is False

    def test_parse_webhook_event_sale_success(self, nmi_provider: NMIProvider):
        """Le parsing d'un événement sale success fonctionne."""
        payload = {
            "event_id": "evt_12345",
            "event_type": "transaction.sale.success",
            "timestamp": "2024-02-15T14:30:00Z",
            "data": {"transaction_id": "txn_abc", "amount": 50.00},
        }

        event = nmi_provider.parse_webhook_event(payload)

        assert event.id == "evt_12345"
        assert event.type == WebhookEventType.PAYMENT_CAPTURED
        assert event.provider == FinanceProviderType.NMI

    def test_parse_webhook_event_refund(self, nmi_provider: NMIProvider):
        """Le parsing d'un événement refund fonctionne."""
        payload = {
            "event_id": "evt_refund_001",
            "event_type": "transaction.refund.success",
            "timestamp": "2024-02-15T15:00:00Z",
            "data": {"transaction_id": "txn_refund", "amount": 25.00},
        }

        event = nmi_provider.parse_webhook_event(payload)

        assert event.type == WebhookEventType.PAYMENT_REFUNDED


# =============================================================================
# TESTS UNITAIRES - GESTION DES ERREURS
# =============================================================================


class TestNMIErrorHandling:
    """Tests pour la gestion des erreurs."""

    @pytest.mark.asyncio
    async def test_handle_http_error(self, nmi_provider: NMIProvider):
        """Les erreurs HTTP sont gérées correctement."""
        nmi_provider._client = create_mock_client("Internal Server Error", 500)

        result = await nmi_provider.process_payment(
            amount=5000,
            card_number="4111111111111111",
            exp_month="12",
            exp_year="25",
        )

        assert result.success is False
        assert result.error.code == FinanceErrorCode.SERVICE_UNAVAILABLE

    @pytest.mark.asyncio
    async def test_handle_connection_error(self, nmi_provider: NMIProvider):
        """Les erreurs de connexion sont gérées correctement."""
        mock_client = MagicMock()
        mock_client.post = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        mock_client.is_closed = False
        nmi_provider._client = mock_client

        result = await nmi_provider.process_payment(
            amount=5000,
            card_number="4111111111111111",
            exp_month="12",
            exp_year="25",
        )

        assert result.success is False
        assert result.error.code == FinanceErrorCode.INTERNAL_ERROR

    @pytest.mark.asyncio
    async def test_handle_validation_error(self, nmi_provider: NMIProvider):
        """Les erreurs de validation sont gérées correctement."""
        result = await nmi_provider.process_payment(
            amount=-100,  # Invalid
            card_number="4111111111111111",
            exp_month="12",
            exp_year="25",
        )

        assert result.success is False
        assert result.error.code == FinanceErrorCode.INVALID_REQUEST


# =============================================================================
# TESTS INTÉGRATION
# =============================================================================


class TestNMIIntegration:
    """Tests d'intégration."""

    @pytest.mark.asyncio
    async def test_full_payment_workflow(
        self, nmi_provider: NMIProvider, mock_success_response: str
    ):
        """Le workflow complet de paiement fonctionne."""
        mock_client = create_mock_client(mock_success_response)
        nmi_provider._client = mock_client

        # 1. Autorisation
        auth_result = await nmi_provider.authorize(
            amount=10000,
            card_number="4111111111111111",
            exp_month="12",
            exp_year="25",
            cvv="123",
        )
        assert auth_result.success is True

        # 2. Capture
        capture_result = await nmi_provider.capture(
            transaction_id=auth_result.data.transaction_id,
        )
        assert capture_result.success is True

    @pytest.mark.asyncio
    async def test_context_manager(self, tenant_id: str, api_key: str):
        """Le context manager fonctionne."""
        async with NMIProvider(
            tenant_id=tenant_id,
            api_key=api_key,
            sandbox=True,
        ) as provider:
            assert provider.tenant_id == tenant_id
            assert provider.api_key == api_key


# =============================================================================
# TESTS SÉCURITÉ
# =============================================================================


class TestNMISecurity:
    """Tests de sécurité."""

    def test_tenant_isolation(self):
        """Chaque provider a son propre tenant_id."""
        provider1 = NMIProvider(tenant_id="tenant-1", api_key="key1")
        provider2 = NMIProvider(tenant_id="tenant-2", api_key="key2")

        assert provider1.tenant_id != provider2.tenant_id

    @pytest.mark.asyncio
    async def test_api_key_in_data(
        self, nmi_provider: NMIProvider, mock_success_response: str
    ):
        """La clé API est incluse dans les requêtes."""
        mock_client = create_mock_client(mock_success_response)
        nmi_provider._client = mock_client

        await nmi_provider.process_payment(
            amount=5000,
            card_number="4111111111111111",
            exp_month="12",
            exp_year="25",
        )

        call_args = mock_client.post.call_args
        assert call_args[1]["data"]["security_key"] == nmi_provider.api_key

    def test_card_number_masked_in_response(self):
        """Le numéro de carte est masqué dans la réponse."""
        response = NMITransactionResponse(
            transaction_id="txn_123",
            response_code=1,
            response_text="SUCCESS",
            amount=Decimal("50.00"),
            card_last_four="1111",
        )

        assert response.card_last_four == "1111"
        # Le numéro complet n'est jamais stocké
        assert not hasattr(response, "card_number")

    def test_luhn_validation_prevents_typos(self):
        """La validation Luhn empêche les erreurs de saisie."""
        from pydantic import ValidationError

        # Carte valide
        valid = NMIPaymentRequest(
            amount=1000,
            card_number="4111111111111111",
            exp_month="12",
            exp_year="25",
        )
        assert valid.card_number == "4111111111111111"

        # Même carte avec un chiffre changé = invalide
        with pytest.raises(ValidationError):
            NMIPaymentRequest(
                amount=1000,
                card_number="4111111111111112",  # Dernier chiffre changé
                exp_month="12",
                exp_year="25",
            )
