"""
Tests pour le provider Solaris Bank.
=====================================

Tests unitaires et d'intégration pour SolarisProvider.
"""

import pytest
from datetime import datetime, date
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
from app.modules.finance.providers.solaris import (
    SolarisProvider,
    SolarisAccountStatus,
    SolarisAccountType,
    SolarisOverdraftStatus,
    SolarisBusinessType,
    SolarisCountry,
    SolarisBusinessRequest,
    SolarisAccountRequest,
    SolarisOverdraftApplicationRequest,
    SolarisTransferRequest,
    SolarisBusinessResponse,
    SolarisAccountResponse,
    SolarisOverdraftResponse,
    SolarisTransferResponse,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def tenant_id() -> str:
    """ID de tenant pour les tests."""
    return "tenant-test-001"


@pytest.fixture
def client_id() -> str:
    """Client ID OAuth2 de test."""
    return "test_client_id"


@pytest.fixture
def client_secret() -> str:
    """Client Secret OAuth2 de test."""
    return "test_client_secret"


@pytest.fixture
def solaris_provider(tenant_id: str, client_id: str, client_secret: str) -> SolarisProvider:
    """Instance de SolarisProvider pour les tests."""
    provider = SolarisProvider(
        tenant_id=tenant_id,
        api_key=client_secret,
        client_id=client_id,
        webhook_secret="whsec_test_secret",
        sandbox=True,
    )
    # Pre-set token pour éviter les appels OAuth2
    provider._access_token = "test_access_token"
    provider._token_expires_at = datetime(2099, 12, 31)
    return provider


@pytest.fixture
def mock_business_response() -> dict:
    """Réponse mock pour une entreprise."""
    return {
        "id": "bus_12345",
        "name": "Test GmbH",
        "legal_form": "limited_company",
        "registration_number": "HRB123456",
        "address_line1": "Teststraße 1",
        "address_city": "Berlin",
        "address_postal_code": "10115",
        "address_country": "DE",
        "status": "active",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-02-15T14:00:00Z",
    }


@pytest.fixture
def mock_account_response() -> dict:
    """Réponse mock pour un compte."""
    return {
        "id": "acc_67890",
        "business_id": "bus_12345",
        "iban": "DE89370400440532013000",
        "bic": "COBADEFFXXX",
        "account_type": "current",
        "status": "active",
        "balance_cents": 10000000,  # 100,000 EUR
        "available_balance_cents": 8000000,  # 80,000 EUR
        "currency": "EUR",
        "overdraft_limit_cents": 5000000,  # 50,000 EUR
        "overdraft_used_cents": 0,
        "created_at": "2024-01-20T09:00:00Z",
        "closed_at": None,
    }


@pytest.fixture
def mock_overdraft_response() -> dict:
    """Réponse mock pour un overdraft."""
    return {
        "id": "ovd_11111",
        "business_id": "bus_12345",
        "account_iban": "DE89370400440532013000",
        "status": "approved",
        "requested_limit_cents": 5000000,
        "approved_limit_cents": 5000000,
        "used_amount_cents": 0,
        "currency": "EUR",
        "interest_rate": "0.095",
        "fee_cents": 25000,
        "valid_from": "2024-02-01",
        "valid_until": "2025-02-01",
        "created_at": "2024-01-25T11:00:00Z",
        "approved_at": "2024-01-26T14:00:00Z",
    }


@pytest.fixture
def mock_transfer_response() -> dict:
    """Réponse mock pour un virement."""
    return {
        "id": "tfr_22222",
        "account_id": "acc_67890",
        "status": "executed",
        "amount_cents": 150000,  # 1,500 EUR
        "currency": "EUR",
        "recipient_name": "Lieferant GmbH",
        "recipient_iban": "DE75512108001245126199",
        "reference": "Invoice INV-2024-001",
        "end_to_end_id": "E2E-12345",
        "created_at": "2024-02-15T10:00:00Z",
        "executed_at": "2024-02-15T10:05:00Z",
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
    mock_client.is_closed = False

    return mock_client


# =============================================================================
# TESTS UNITAIRES - INITIALISATION
# =============================================================================


class TestSolarisProviderInit:
    """Tests d'initialisation du provider."""

    def test_init_with_tenant_id(self, tenant_id: str, client_id: str, client_secret: str):
        """L'initialisation avec tenant_id fonctionne."""
        provider = SolarisProvider(
            tenant_id=tenant_id,
            api_key=client_secret,
            client_id=client_id,
        )
        assert provider.tenant_id == tenant_id
        assert provider.client_id == client_id
        assert provider.api_key == client_secret

    def test_init_sandbox_mode(self, tenant_id: str, client_id: str, client_secret: str):
        """Le mode sandbox utilise la bonne URL."""
        provider = SolarisProvider(
            tenant_id=tenant_id,
            api_key=client_secret,
            client_id=client_id,
            sandbox=True,
        )
        assert provider.sandbox is True
        assert "sandbox" in provider.BASE_URL

    def test_init_production_mode(self, tenant_id: str, client_id: str, client_secret: str):
        """Le mode production utilise la bonne URL."""
        provider = SolarisProvider(
            tenant_id=tenant_id,
            api_key=client_secret,
            client_id=client_id,
            sandbox=False,
        )
        assert provider.sandbox is False
        assert "solaris.de" in provider.BASE_URL
        assert "sandbox" not in provider.BASE_URL

    def test_init_requires_tenant_id(self, client_id: str, client_secret: str):
        """L'initialisation échoue sans tenant_id."""
        with pytest.raises(ValueError, match="tenant_id"):
            SolarisProvider(tenant_id="", api_key=client_secret, client_id=client_id)

    def test_init_with_webhook_secret(self, tenant_id: str, client_id: str, client_secret: str):
        """L'initialisation avec webhook_secret fonctionne."""
        provider = SolarisProvider(
            tenant_id=tenant_id,
            api_key=client_secret,
            client_id=client_id,
            webhook_secret="whsec_test",
        )
        assert provider.webhook_secret == "whsec_test"

    def test_provider_name(self, solaris_provider: SolarisProvider):
        """Le nom du provider est correct."""
        assert solaris_provider.PROVIDER_NAME == "solaris"
        assert solaris_provider.PROVIDER_TYPE == FinanceProviderType.SOLARIS


# =============================================================================
# TESTS UNITAIRES - VALIDATION
# =============================================================================


class TestSolarisValidation:
    """Tests de validation des requêtes."""

    def test_valid_business_request(self):
        """Une requête d'entreprise valide est acceptée."""
        request = SolarisBusinessRequest(
            name="Test GmbH",
            legal_form=SolarisBusinessType.LIMITED_COMPANY,
            registration_number="HRB123456",
            address_line1="Teststraße 1",
            address_city="Berlin",
            address_postal_code="10115",
            contact_email="contact@test.de",
        )
        assert request.name == "Test GmbH"

    def test_valid_account_request(self):
        """Une requête de compte valide est acceptée."""
        request = SolarisAccountRequest(
            business_id="bus_123",
            account_type=SolarisAccountType.CURRENT,
            iban_country=SolarisCountry.DE,
        )
        assert request.business_id == "bus_123"

    def test_valid_overdraft_request(self):
        """Une requête d'overdraft valide est acceptée."""
        request = SolarisOverdraftApplicationRequest(
            business_id="bus_123",
            account_iban="DE89370400440532013000",
            requested_limit_cents=5000000,
        )
        assert request.requested_limit_cents == 5000000

    def test_iban_cleaned(self):
        """L'IBAN est nettoyé."""
        request = SolarisOverdraftApplicationRequest(
            business_id="bus_123",
            account_iban="DE89 3704 0044 0532 0130 00",
            requested_limit_cents=5000000,
        )
        assert request.account_iban == "DE89370400440532013000"

    def test_invalid_iban(self):
        """Un IBAN invalide est rejeté."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SolarisOverdraftApplicationRequest(
                business_id="bus_123",
                account_iban="DE89",  # Trop court
                requested_limit_cents=5000000,
            )

    def test_overdraft_limit_max(self):
        """La limite max d'overdraft est respectée."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SolarisOverdraftApplicationRequest(
                business_id="bus_123",
                account_iban="DE89370400440532013000",
                requested_limit_cents=60000000,  # > 500k EUR
            )

    def test_valid_transfer_request(self):
        """Une requête de virement valide est acceptée."""
        request = SolarisTransferRequest(
            account_id="acc_123",
            amount_cents=150000,
            recipient_name="Test GmbH",
            recipient_iban="DE75512108001245126199",
        )
        assert request.amount_cents == 150000


# =============================================================================
# TESTS UNITAIRES - ENTREPRISES
# =============================================================================


class TestSolarisBusinesses:
    """Tests pour les opérations sur les entreprises."""

    @pytest.mark.asyncio
    async def test_create_business_success(
        self, solaris_provider: SolarisProvider, mock_business_response: dict
    ):
        """La création d'entreprise réussie retourne les bonnes données."""
        solaris_provider._client = create_mock_client(mock_business_response)

        result = await solaris_provider.create_business(
            name="Test GmbH",
            legal_form=SolarisBusinessType.LIMITED_COMPANY,
            registration_number="HRB123456",
            address_line1="Teststraße 1",
            address_city="Berlin",
            address_postal_code="10115",
            contact_email="contact@test.de",
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_get_business_success(
        self, solaris_provider: SolarisProvider, mock_business_response: dict
    ):
        """La récupération d'entreprise fonctionne."""
        solaris_provider._client = create_mock_client(mock_business_response)

        result = await solaris_provider.get_business(business_id="bus_12345")

        assert result.success is True


# =============================================================================
# TESTS UNITAIRES - COMPTES
# =============================================================================


class TestSolarisAccounts:
    """Tests pour les opérations sur les comptes."""

    @pytest.mark.asyncio
    async def test_create_account_success(
        self, solaris_provider: SolarisProvider, mock_account_response: dict
    ):
        """La création de compte réussie retourne les bonnes données."""
        solaris_provider._client = create_mock_client(mock_account_response)

        result = await solaris_provider.create_account(
            business_id="bus_12345",
            account_type=SolarisAccountType.CURRENT,
            iban_country=SolarisCountry.DE,
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_get_account_success(
        self, solaris_provider: SolarisProvider, mock_account_response: dict
    ):
        """La récupération de compte fonctionne."""
        solaris_provider._client = create_mock_client(mock_account_response)

        result = await solaris_provider.get_account(account_id="acc_67890")

        assert result.success is True

    @pytest.mark.asyncio
    async def test_get_accounts_success(
        self, solaris_provider: SolarisProvider, mock_account_response: dict
    ):
        """La liste des comptes fonctionne."""
        solaris_provider._client = create_mock_client([mock_account_response])

        result = await solaris_provider.get_accounts(business_id="bus_12345")

        assert result.success is True

    @pytest.mark.asyncio
    async def test_get_account_balance_success(
        self, solaris_provider: SolarisProvider, mock_account_response: dict
    ):
        """La récupération du solde fonctionne."""
        solaris_provider._client = create_mock_client(mock_account_response)

        result = await solaris_provider.get_account_balance(account_id="acc_67890")

        assert result.success is True
        assert "balance_cents" in result.data
        assert "available_balance_cents" in result.data


# =============================================================================
# TESTS UNITAIRES - OVERDRAFTS
# =============================================================================


class TestSolarisOverdrafts:
    """Tests pour les opérations sur les overdrafts."""

    @pytest.mark.asyncio
    async def test_create_overdraft_application_success(
        self, solaris_provider: SolarisProvider, mock_overdraft_response: dict
    ):
        """La création d'overdraft réussie retourne les bonnes données."""
        solaris_provider._client = create_mock_client(mock_overdraft_response)

        result = await solaris_provider.create_overdraft_application(
            business_id="bus_12345",
            account_iban="DE89370400440532013000",
            requested_limit_cents=5000000,
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_get_overdraft_success(
        self, solaris_provider: SolarisProvider, mock_overdraft_response: dict
    ):
        """La récupération d'overdraft fonctionne."""
        solaris_provider._client = create_mock_client(mock_overdraft_response)

        result = await solaris_provider.get_overdraft(overdraft_id="ovd_11111")

        assert result.success is True

    @pytest.mark.asyncio
    async def test_get_overdrafts_success(
        self, solaris_provider: SolarisProvider, mock_overdraft_response: dict
    ):
        """La liste des overdrafts fonctionne."""
        solaris_provider._client = create_mock_client([mock_overdraft_response])

        result = await solaris_provider.get_overdrafts(business_id="bus_12345")

        assert result.success is True


# =============================================================================
# TESTS UNITAIRES - VIREMENTS
# =============================================================================


class TestSolarisTransfers:
    """Tests pour les opérations sur les virements."""

    @pytest.mark.asyncio
    async def test_create_transfer_success(
        self, solaris_provider: SolarisProvider, mock_transfer_response: dict
    ):
        """La création de virement réussie retourne les bonnes données."""
        solaris_provider._client = create_mock_client(mock_transfer_response)

        result = await solaris_provider.create_transfer(
            account_id="acc_67890",
            amount_cents=150000,
            recipient_name="Lieferant GmbH",
            recipient_iban="DE75512108001245126199",
            reference="Invoice INV-2024-001",
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_get_transfer_success(
        self, solaris_provider: SolarisProvider, mock_transfer_response: dict
    ):
        """La récupération de virement fonctionne."""
        solaris_provider._client = create_mock_client(mock_transfer_response)

        result = await solaris_provider.get_transfer(transfer_id="tfr_22222")

        assert result.success is True


# =============================================================================
# TESTS UNITAIRES - WEBHOOKS
# =============================================================================


class TestSolarisWebhooks:
    """Tests pour la gestion des webhooks."""

    def test_verify_webhook_signature_valid(self, solaris_provider: SolarisProvider):
        """La vérification de signature fonctionne pour une signature valide."""
        import hmac
        import hashlib

        payload = b'{"event_type":"overdraft.approved"}'
        expected_sig = hmac.new(
            solaris_provider.webhook_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        result = solaris_provider.verify_webhook_signature(
            payload=payload,
            signature=expected_sig,
        )

        assert result is True

    def test_verify_webhook_signature_invalid(self, solaris_provider: SolarisProvider):
        """La vérification échoue pour une signature invalide."""
        payload = b'{"event_type":"overdraft.approved"}'

        result = solaris_provider.verify_webhook_signature(
            payload=payload,
            signature="invalid_signature",
        )

        assert result is False

    def test_verify_webhook_without_secret(self, tenant_id: str, client_id: str, client_secret: str):
        """La vérification échoue sans secret configuré."""
        provider = SolarisProvider(
            tenant_id=tenant_id,
            api_key=client_secret,
            client_id=client_id,
        )

        result = provider.verify_webhook_signature(
            payload=b"test",
            signature="test",
        )

        assert result is False

    def test_parse_webhook_event_overdraft_approved(self, solaris_provider: SolarisProvider):
        """Le parsing d'un événement overdraft.approved fonctionne."""
        payload = {
            "event_id": "evt_12345",
            "event_type": "overdraft.approved",
            "timestamp": "2024-02-15T14:30:00Z",
            "data": {"overdraft_id": "ovd_11111", "approved_limit_cents": 5000000},
        }

        event = solaris_provider.parse_webhook_event(payload)

        assert event.id == "evt_12345"
        assert event.type == WebhookEventType.PAYMENT_AUTHORIZED
        assert event.provider == FinanceProviderType.SOLARIS

    def test_parse_webhook_event_transfer_executed(self, solaris_provider: SolarisProvider):
        """Le parsing d'un événement transfer.executed fonctionne."""
        payload = {
            "event_id": "evt_tfr_001",
            "event_type": "transfer.executed",
            "timestamp": "2024-02-15T10:05:00Z",
            "data": {"transfer_id": "tfr_22222"},
        }

        event = solaris_provider.parse_webhook_event(payload)

        assert event.type == WebhookEventType.TRANSACTION_COMPLETED

    def test_parse_webhook_event_account_created(self, solaris_provider: SolarisProvider):
        """Le parsing d'un événement account.created fonctionne."""
        payload = {
            "event_id": "evt_acc_001",
            "event_type": "account.created",
            "timestamp": "2024-01-20T09:00:00Z",
            "data": {"account_id": "acc_67890"},
        }

        event = solaris_provider.parse_webhook_event(payload)

        assert event.type == WebhookEventType.ACCOUNT_CREATED


# =============================================================================
# TESTS UNITAIRES - GESTION DES ERREURS
# =============================================================================


class TestSolarisErrorHandling:
    """Tests pour la gestion des erreurs."""

    @pytest.mark.asyncio
    async def test_handle_validation_error(self, solaris_provider: SolarisProvider):
        """Les erreurs de validation sont gérées correctement."""
        result = await solaris_provider.create_business(
            name="A",  # Trop court
            legal_form=SolarisBusinessType.LIMITED_COMPANY,
            registration_number="HRB123456",
            address_line1="Teststraße 1",
            address_city="Berlin",
            address_postal_code="10115",
            contact_email="contact@test.de",
        )

        assert result.success is False
        assert result.error.code == FinanceErrorCode.INVALID_REQUEST

    @pytest.mark.asyncio
    async def test_handle_auth_error(self, tenant_id: str, client_id: str, client_secret: str):
        """Les erreurs d'authentification sont gérées correctement."""
        provider = SolarisProvider(
            tenant_id=tenant_id,
            api_key=client_secret,
            client_id=client_id,
        )
        # Ne pas pré-définir le token

        # Mock échec OAuth2
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        provider._client = mock_client

        result = await provider.get_business(business_id="bus_12345")

        assert result.success is False
        assert result.error.code == FinanceErrorCode.INVALID_API_KEY


# =============================================================================
# TESTS INTÉGRATION
# =============================================================================


class TestSolarisIntegration:
    """Tests d'intégration."""

    @pytest.mark.asyncio
    async def test_full_business_workflow(
        self,
        solaris_provider: SolarisProvider,
        mock_business_response: dict,
        mock_account_response: dict,
        mock_overdraft_response: dict,
    ):
        """Le workflow complet business fonctionne."""
        # Mock les différentes réponses
        mock_client = MagicMock()
        mock_client.is_closed = False

        responses = [
            MagicMock(status_code=200, json=MagicMock(return_value=mock_business_response)),
            MagicMock(status_code=200, json=MagicMock(return_value=mock_account_response)),
            MagicMock(status_code=200, json=MagicMock(return_value=mock_overdraft_response)),
        ]
        mock_client.request = AsyncMock(side_effect=responses)
        solaris_provider._client = mock_client

        # 1. Créer l'entreprise
        business_result = await solaris_provider.create_business(
            name="Test GmbH",
            legal_form=SolarisBusinessType.LIMITED_COMPANY,
            registration_number="HRB123456",
            address_line1="Teststraße 1",
            address_city="Berlin",
            address_postal_code="10115",
            contact_email="contact@test.de",
        )
        assert business_result.success is True

        # 2. Créer un compte
        account_result = await solaris_provider.create_account(
            business_id="bus_12345",
            account_type=SolarisAccountType.CURRENT,
        )
        assert account_result.success is True

        # 3. Demander un overdraft
        overdraft_result = await solaris_provider.create_overdraft_application(
            business_id="bus_12345",
            account_iban="DE89370400440532013000",
            requested_limit_cents=5000000,
        )
        assert overdraft_result.success is True

    @pytest.mark.asyncio
    async def test_context_manager(self, tenant_id: str, client_id: str, client_secret: str):
        """Le context manager fonctionne."""
        async with SolarisProvider(
            tenant_id=tenant_id,
            api_key=client_secret,
            client_id=client_id,
            sandbox=True,
        ) as provider:
            assert provider.tenant_id == tenant_id
            assert provider.client_id == client_id


# =============================================================================
# TESTS SÉCURITÉ
# =============================================================================


class TestSolarisSecurity:
    """Tests de sécurité."""

    def test_tenant_isolation(self, client_id: str, client_secret: str):
        """Chaque provider a son propre tenant_id."""
        provider1 = SolarisProvider(
            tenant_id="tenant-1",
            api_key=client_secret,
            client_id=client_id,
        )
        provider2 = SolarisProvider(
            tenant_id="tenant-2",
            api_key=client_secret,
            client_id=client_id,
        )

        assert provider1.tenant_id != provider2.tenant_id

    def test_token_in_headers(self, solaris_provider: SolarisProvider):
        """Le token est inclus dans les headers."""
        headers = solaris_provider._get_default_headers()

        assert "Authorization" in headers
        assert "Bearer" in headers["Authorization"]

    def test_tenant_id_in_headers(self, solaris_provider: SolarisProvider):
        """Le tenant_id est inclus dans les headers."""
        headers = solaris_provider._get_default_headers()

        assert "X-Tenant-ID" in headers
        assert headers["X-Tenant-ID"] == solaris_provider.tenant_id

    def test_oauth2_credentials_not_in_headers(self, solaris_provider: SolarisProvider):
        """Les credentials OAuth2 ne sont pas exposés dans les headers."""
        headers = solaris_provider._get_default_headers()

        assert solaris_provider.client_id not in str(headers)
        assert solaris_provider.api_key not in str(headers)
