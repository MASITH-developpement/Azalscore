"""
Tests pour le provider Swan.
=============================

Tests unitaires et d'intégration pour SwanProvider.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx

from app.modules.finance.providers.base import (
    FinanceProviderType,
    FinanceResult,
    FinanceError,
    FinanceErrorCode,
    WebhookEventType,
)
from app.modules.finance.providers.swan import (
    SwanProvider,
    SwanAccountStatus,
    SwanTransactionStatus,
    SwanTransferRequest,
    SwanAccountResponse,
    SwanTransactionResponse,
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
    return "sk_test_swan_api_key_for_testing"


@pytest.fixture
def swan_provider(tenant_id: str, api_key: str) -> SwanProvider:
    """Instance de SwanProvider pour les tests."""
    return SwanProvider(
        tenant_id=tenant_id,
        api_key=api_key,
        project_id="prj_test_123",
        webhook_secret="whsec_test_secret",
        sandbox=True,
    )


@pytest.fixture
def mock_account_response() -> dict:
    """Réponse mock pour un compte Swan."""
    return {
        "id": "acc_123456",
        "name": "Compte Principal",
        "status": "Opened",
        "IBAN": "FR7630001007941234567890185",
        "BIC": "SABORFRP",
        "currency": "EUR",
        "availableBalance": {"value": 150000, "currency": "EUR"},
        "bookedBalance": {"value": 148500, "currency": "EUR"},
        "pendingBalance": {"value": 1500, "currency": "EUR"},
        "holder": {"name": "AZALS SAS"},
        "createdAt": "2024-01-15T10:30:00Z",
    }


@pytest.fixture
def mock_transaction_response() -> dict:
    """Réponse mock pour une transaction Swan."""
    return {
        "id": "txn_789012",
        "status": "Booked",
        "type": "SepaCreditTransferIn",
        "amount": {"value": 50000, "currency": "EUR"},
        "reference": "FACTURE-2024-001",
        "label": "Paiement client ABC",
        "counterparty": {
            "name": "Client ABC SARL",
            "IBAN": "FR7612345678901234567890123",
        },
        "executionDate": "2024-02-15",
        "bookingDate": "2024-02-15",
        "createdAt": "2024-02-15T14:22:00Z",
    }


# =============================================================================
# TESTS UNITAIRES - INITIALISATION
# =============================================================================

class TestSwanProviderInit:
    """Tests d'initialisation du provider Swan."""

    def test_init_with_tenant_id(self, tenant_id: str, api_key: str):
        """Le provider s'initialise avec un tenant_id."""
        provider = SwanProvider(tenant_id=tenant_id, api_key=api_key)

        assert provider.tenant_id == tenant_id
        assert provider.api_key == api_key
        assert provider.sandbox is False  # Default

    def test_init_sandbox_mode(self, tenant_id: str, api_key: str):
        """Le provider peut être initialisé en mode sandbox."""
        provider = SwanProvider(tenant_id=tenant_id, api_key=api_key, sandbox=True)

        assert provider.sandbox is True
        assert provider._get_base_url() == "https://api.sandbox.swan.io"

    def test_init_production_mode(self, tenant_id: str, api_key: str):
        """Le provider peut être initialisé en mode production."""
        provider = SwanProvider(tenant_id=tenant_id, api_key=api_key, sandbox=False)

        assert provider.sandbox is False
        assert provider._get_base_url() == "https://api.swan.io"

    def test_init_requires_tenant_id(self, api_key: str):
        """Le tenant_id est obligatoire."""
        with pytest.raises(ValueError, match="tenant_id"):
            SwanProvider(tenant_id="", api_key=api_key)

    def test_init_with_webhook_secret(self, tenant_id: str, api_key: str):
        """Le webhook_secret peut être configuré."""
        provider = SwanProvider(
            tenant_id=tenant_id,
            api_key=api_key,
            webhook_secret="whsec_test_123",
        )

        assert provider.webhook_secret == "whsec_test_123"

    def test_provider_name(self, swan_provider: SwanProvider):
        """Le provider a le bon nom."""
        assert swan_provider.PROVIDER_NAME == "swan"
        assert swan_provider.PROVIDER_TYPE == FinanceProviderType.SWAN


# =============================================================================
# TESTS UNITAIRES - COMPTES
# =============================================================================

class TestSwanAccounts:
    """Tests pour les opérations sur les comptes."""

    @pytest.mark.asyncio
    async def test_get_accounts_success(
        self,
        swan_provider: SwanProvider,
        mock_account_response: dict,
    ):
        """get_accounts retourne les comptes avec succès."""
        mock_response = httpx.Response(
            200,
            json={"accounts": [mock_account_response]},
        )

        with patch.object(swan_provider, "_request") as mock_request:
            mock_request.return_value = FinanceResult.ok(
                data={"accounts": [mock_account_response]},
                provider="swan",
                request_id="req_123",
                response_time_ms=150,
            )

            result = await swan_provider.get_accounts()

            assert result.success is True
            assert len(result.data) == 1
            assert result.data[0].id == "acc_123456"
            assert result.data[0].iban == "FR7630001007941234567890185"
            assert result.data[0].balance_available == 150000

    @pytest.mark.asyncio
    async def test_get_accounts_with_pagination(
        self,
        swan_provider: SwanProvider,
        mock_account_response: dict,
    ):
        """get_accounts gère la pagination."""
        with patch.object(swan_provider, "_request") as mock_request:
            mock_request.return_value = FinanceResult.ok(
                data={
                    "accounts": [mock_account_response],
                    "pageInfo": {"hasNextPage": True, "endCursor": "cursor_abc"},
                    "totalCount": 25,
                },
                provider="swan",
            )

            result = await swan_provider.get_accounts(first=10, after="cursor_xyz")

            assert result.success is True
            assert result.has_more is True
            assert result.total_count == 25

    @pytest.mark.asyncio
    async def test_get_account_by_id(
        self,
        swan_provider: SwanProvider,
        mock_account_response: dict,
    ):
        """get_account retourne un compte par ID."""
        with patch.object(swan_provider, "_request") as mock_request:
            mock_request.return_value = FinanceResult.ok(
                data=mock_account_response,
                provider="swan",
            )

            result = await swan_provider.get_account("acc_123456")

            assert result.success is True
            assert result.data.id == "acc_123456"
            assert result.data.status == SwanAccountStatus.OPENED

    @pytest.mark.asyncio
    async def test_get_account_balance(
        self,
        swan_provider: SwanProvider,
        mock_account_response: dict,
    ):
        """get_account_balance retourne les soldes formatés."""
        with patch.object(swan_provider, "get_account") as mock_get:
            mock_get.return_value = FinanceResult.ok(
                data=SwanAccountResponse(**swan_provider._map_account(mock_account_response)),
                provider="swan",
            )

            result = await swan_provider.get_account_balance("acc_123456")

            assert result.success is True
            assert result.data["available"] == 150000
            assert result.data["booked"] == 148500
            assert result.data["formatted_available"] == "1500.00 EUR"


# =============================================================================
# TESTS UNITAIRES - TRANSACTIONS
# =============================================================================

class TestSwanTransactions:
    """Tests pour les opérations sur les transactions."""

    @pytest.mark.asyncio
    async def test_get_transactions_success(
        self,
        swan_provider: SwanProvider,
        mock_transaction_response: dict,
    ):
        """get_transactions retourne les transactions."""
        with patch.object(swan_provider, "_request") as mock_request:
            mock_request.return_value = FinanceResult.ok(
                data={"transactions": [mock_transaction_response]},
                provider="swan",
            )

            result = await swan_provider.get_transactions(account_id="acc_123")

            assert result.success is True
            assert len(result.data) == 1
            assert result.data[0].id == "txn_789012"
            assert result.data[0].amount == 50000
            assert result.data[0].status == SwanTransactionStatus.BOOKED

    @pytest.mark.asyncio
    async def test_get_transactions_with_filters(
        self,
        swan_provider: SwanProvider,
        mock_transaction_response: dict,
    ):
        """get_transactions accepte des filtres."""
        with patch.object(swan_provider, "_request") as mock_request:
            mock_request.return_value = FinanceResult.ok(
                data={"transactions": [mock_transaction_response]},
                provider="swan",
            )

            result = await swan_provider.get_transactions(
                account_id="acc_123",
                status=SwanTransactionStatus.BOOKED,
                from_date=datetime(2024, 1, 1),
                to_date=datetime(2024, 12, 31),
            )

            assert result.success is True
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert "params" in call_args.kwargs
            params = call_args.kwargs["params"]
            assert params["status"] == "Booked"


# =============================================================================
# TESTS UNITAIRES - VIREMENTS
# =============================================================================

class TestSwanTransfers:
    """Tests pour les virements SEPA."""

    @pytest.mark.asyncio
    async def test_create_transfer_success(self, swan_provider: SwanProvider):
        """create_transfer crée un virement avec succès."""
        transfer_request = SwanTransferRequest(
            amount=10000,  # 100.00€
            creditor_name="Jean Dupont",
            creditor_iban="FR7630001007941234567890185",
            reference="FACTURE-001",
        )

        with patch.object(swan_provider, "_request") as mock_request:
            mock_request.return_value = FinanceResult.ok(
                data={
                    "id": "pay_abc123",
                    "status": "Initiated",
                    "createdAt": datetime.utcnow().isoformat(),
                },
                provider="swan",
            )

            result = await swan_provider.create_transfer(
                account_id="acc_123",
                request=transfer_request,
            )

            assert result.success is True
            assert result.data.id == "pay_abc123"
            assert result.data.amount == 10000
            assert result.data.creditor_name == "Jean Dupont"

    def test_transfer_request_validation(self):
        """La validation du virement fonctionne."""
        # Montant valide
        request = SwanTransferRequest(
            amount=10000,
            creditor_name="Test",
            creditor_iban="FR7630001007941234567890185",
        )
        assert request.amount == 10000

        # Montant invalide (négatif)
        with pytest.raises(ValueError):
            SwanTransferRequest(
                amount=-100,
                creditor_name="Test",
                creditor_iban="FR7630001007941234567890185",
            )

    def test_iban_validation(self):
        """La validation IBAN fonctionne."""
        # IBAN valide avec espaces
        request = SwanTransferRequest(
            amount=1000,
            creditor_name="Test",
            creditor_iban="FR76 3000 1007 9412 3456 7890 185",
        )
        assert request.creditor_iban == "FR7630001007941234567890185"

        # IBAN trop court - Pydantic raises ValidationError
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SwanTransferRequest(
                amount=1000,
                creditor_name="Test",
                creditor_iban="FR76",
            )


# =============================================================================
# TESTS UNITAIRES - WEBHOOKS
# =============================================================================

class TestSwanWebhooks:
    """Tests pour la gestion des webhooks."""

    def test_verify_webhook_signature_valid(self, swan_provider: SwanProvider):
        """La vérification de signature fonctionne pour une signature valide."""
        import hmac
        import hashlib

        payload = b'{"eventId":"evt_123","eventType":"Transaction.Booked"}'
        timestamp = "1708000000"

        # Calculer la signature attendue
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
        expected_signature = hmac.new(
            swan_provider.webhook_secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        result = swan_provider.verify_webhook_signature(
            payload=payload,
            signature=expected_signature,
            timestamp=timestamp,
        )

        assert result is True

    def test_verify_webhook_signature_invalid(self, swan_provider: SwanProvider):
        """La vérification de signature échoue pour une signature invalide."""
        payload = b'{"eventId":"evt_123"}'

        result = swan_provider.verify_webhook_signature(
            payload=payload,
            signature="invalid_signature_abc123",
            timestamp="1708000000",
        )

        assert result is False

    def test_verify_webhook_without_secret(self, tenant_id: str, api_key: str):
        """La vérification échoue sans secret configuré."""
        provider = SwanProvider(tenant_id=tenant_id, api_key=api_key)  # Pas de webhook_secret

        result = provider.verify_webhook_signature(
            payload=b"test",
            signature="test",
        )

        assert result is False

    def test_parse_webhook_event(self, swan_provider: SwanProvider):
        """Le parsing d'événement webhook fonctionne."""
        payload = {
            "eventId": "evt_12345",
            "eventType": "Transaction.Booked",
            "resourceId": "txn_abc",
            "projectId": "prj_123",
            "timestamp": "2024-02-15T14:30:00Z",
            "data": {"transactionId": "txn_abc", "amount": 10000},
        }

        event = swan_provider.parse_webhook_event(payload)

        assert event.id == "evt_12345"
        assert event.type == WebhookEventType.TRANSACTION_COMPLETED
        assert event.provider == FinanceProviderType.SWAN
        assert event.tenant_id == swan_provider.tenant_id
        assert event.payload["transactionId"] == "txn_abc"


# =============================================================================
# TESTS UNITAIRES - GESTION D'ERREURS
# =============================================================================

class TestSwanErrorHandling:
    """Tests pour la gestion des erreurs."""

    @pytest.mark.asyncio
    async def test_handle_timeout(self, swan_provider: SwanProvider):
        """Le timeout est géré correctement."""
        with patch.object(swan_provider, "_get_client") as mock_client:
            mock_client.return_value.request = AsyncMock(
                side_effect=httpx.TimeoutException("Connection timeout")
            )

            result = await swan_provider._request("GET", "/test")

            assert result.success is False
            assert result.error.code == FinanceErrorCode.TIMEOUT
            assert result.error.retryable is True

    @pytest.mark.asyncio
    async def test_handle_connection_error(self, swan_provider: SwanProvider):
        """Les erreurs de connexion sont gérées."""
        with patch.object(swan_provider, "_get_client") as mock_client:
            mock_client.return_value.request = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )

            result = await swan_provider._request("GET", "/test", retry=False)

            assert result.success is False
            assert result.error.code == FinanceErrorCode.CONNECTION_ERROR

    @pytest.mark.asyncio
    async def test_handle_401_unauthorized(self, swan_provider: SwanProvider):
        """Le 401 est mappé vers INVALID_API_KEY."""
        with patch.object(swan_provider, "_get_client") as mock_client:
            mock_response = httpx.Response(
                401,
                json={"error": "Invalid API key"},
            )
            mock_client.return_value.request = AsyncMock(return_value=mock_response)

            result = await swan_provider._request("GET", "/test", retry=False)

            assert result.success is False
            assert result.error.code == FinanceErrorCode.INVALID_API_KEY

    @pytest.mark.asyncio
    async def test_handle_429_rate_limit(self, swan_provider: SwanProvider):
        """Le 429 est géré avec retry."""
        with patch.object(swan_provider, "_get_client") as mock_client:
            # Premier appel: 429, deuxième: 200
            mock_client.return_value.request = AsyncMock(
                side_effect=[
                    httpx.Response(429, json={"error": "Rate limited"}),
                    httpx.Response(200, json={"data": "ok"}),
                ]
            )

            with patch.object(swan_provider, "_sleep"):  # Skip sleep
                result = await swan_provider._request("GET", "/test")

            assert result.success is True
            assert result.data == {"data": "ok"}


# =============================================================================
# TESTS D'INTÉGRATION (MOCK)
# =============================================================================

class TestSwanIntegration:
    """Tests d'intégration avec mocks."""

    @pytest.mark.asyncio
    async def test_full_workflow_accounts(
        self,
        swan_provider: SwanProvider,
        mock_account_response: dict,
    ):
        """Workflow complet: liste comptes -> détails -> solde."""
        with patch.object(swan_provider, "_request") as mock_request:
            # 1. Liste des comptes
            mock_request.return_value = FinanceResult.ok(
                data={"accounts": [mock_account_response]},
                provider="swan",
            )

            accounts = await swan_provider.get_accounts()
            assert accounts.success
            assert len(accounts.data) == 1

            # 2. Détails d'un compte
            mock_request.return_value = FinanceResult.ok(
                data=mock_account_response,
                provider="swan",
            )

            account = await swan_provider.get_account(accounts.data[0].id)
            assert account.success
            assert account.data.holder_name == "AZALS SAS"

    @pytest.mark.asyncio
    async def test_context_manager(self, tenant_id: str, api_key: str):
        """Le context manager fonctionne."""
        async with SwanProvider(tenant_id=tenant_id, api_key=api_key) as provider:
            assert provider.tenant_id == tenant_id

        # Client fermé après __aexit__
        assert provider._client is None or provider._client.is_closed


# =============================================================================
# TESTS DE SÉCURITÉ
# =============================================================================

class TestSwanSecurity:
    """Tests de sécurité."""

    def test_tenant_isolation(self, api_key: str):
        """Chaque provider est isolé par tenant."""
        provider_a = SwanProvider(tenant_id="tenant-a", api_key=api_key)
        provider_b = SwanProvider(tenant_id="tenant-b", api_key=api_key)

        assert provider_a.tenant_id != provider_b.tenant_id
        assert provider_a._cache_key("test") != provider_b._cache_key("test")

    def test_api_key_in_headers(self, swan_provider: SwanProvider):
        """La clé API est incluse dans les headers."""
        headers = swan_provider._get_default_headers()

        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")

    def test_tenant_id_in_headers(self, swan_provider: SwanProvider):
        """Le tenant_id est inclus dans les headers."""
        headers = swan_provider._get_default_headers()

        assert headers["X-Tenant-ID"] == swan_provider.tenant_id
