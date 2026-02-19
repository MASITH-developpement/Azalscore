"""
Tests pour le système de webhooks finance.
==========================================

Tests unitaires et d'intégration pour WebhookService et WebhookRouter.
"""

import json
import hmac
import hashlib
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.finance.providers.base import (
    FinanceProviderType,
    WebhookEvent,
    WebhookEventType,
)
from app.modules.finance.webhooks.service import (
    WebhookService,
    WebhookResult,
    WebhookProcessingStatus,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def tenant_id() -> str:
    """ID de tenant pour les tests."""
    return "tenant-test-001"


@pytest.fixture
def mock_db():
    """Session de base de données mockée."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
    return db


@pytest.fixture
def webhook_service(mock_db, tenant_id: str) -> WebhookService:
    """Instance de WebhookService pour les tests."""
    return WebhookService(db=mock_db, tenant_id=tenant_id)


@pytest.fixture
def mock_swan_provider():
    """Provider Swan mocké."""
    provider = MagicMock()
    provider.verify_webhook_signature.return_value = True
    provider.parse_webhook_event.return_value = WebhookEvent(
        id="evt_12345",
        type=WebhookEventType.PAYMENT_CAPTURED,
        provider=FinanceProviderType.SWAN,
        tenant_id="tenant-test-001",
        payload={"amount": 10000},
        raw_payload='{"amount": 10000}',
        timestamp=datetime.utcnow(),
    )
    return provider


@pytest.fixture
def swan_webhook_payload() -> bytes:
    """Payload de webhook Swan."""
    return json.dumps({
        "eventId": "evt_12345",
        "eventType": "Transaction.Booked",
        "timestamp": "2024-02-15T14:30:00Z",
        "data": {"transactionId": "txn_abc", "amount": 10000},
    }).encode()


@pytest.fixture
def nmi_webhook_payload() -> bytes:
    """Payload de webhook NMI."""
    return json.dumps({
        "event_id": "evt_nmi_001",
        "event_type": "transaction.sale.success",
        "timestamp": "2024-02-15T14:30:00Z",
        "data": {"transaction_id": "txn_123", "amount": 50.00},
    }).encode()


# =============================================================================
# TESTS UNITAIRES - SERVICE INIT
# =============================================================================


class TestWebhookServiceInit:
    """Tests d'initialisation du service."""

    def test_init_with_tenant_id(self, mock_db, tenant_id: str):
        """L'initialisation avec tenant_id fonctionne."""
        service = WebhookService(db=mock_db, tenant_id=tenant_id)
        assert service.tenant_id == tenant_id
        assert service.db == mock_db

    def test_init_requires_tenant_id(self, mock_db):
        """L'initialisation échoue sans tenant_id."""
        with pytest.raises(ValueError, match="tenant_id"):
            WebhookService(db=mock_db, tenant_id="")


# =============================================================================
# TESTS UNITAIRES - HANDLERS
# =============================================================================


class TestWebhookHandlers:
    """Tests pour la gestion des handlers."""

    def test_register_handler(self, webhook_service: WebhookService):
        """L'enregistrement d'un handler fonctionne."""

        async def my_handler(event: WebhookEvent) -> bool:
            return True

        webhook_service.register_handler(
            WebhookEventType.PAYMENT_CAPTURED,
            my_handler,
        )

        assert WebhookEventType.PAYMENT_CAPTURED in webhook_service._handlers
        assert my_handler in webhook_service._handlers[WebhookEventType.PAYMENT_CAPTURED]

    def test_register_multiple_handlers(self, webhook_service: WebhookService):
        """Plusieurs handlers peuvent être enregistrés pour le même type."""

        async def handler1(event: WebhookEvent) -> bool:
            return True

        async def handler2(event: WebhookEvent) -> bool:
            return True

        webhook_service.register_handler(WebhookEventType.PAYMENT_CAPTURED, handler1)
        webhook_service.register_handler(WebhookEventType.PAYMENT_CAPTURED, handler2)

        assert len(webhook_service._handlers[WebhookEventType.PAYMENT_CAPTURED]) == 2

    def test_unregister_handler(self, webhook_service: WebhookService):
        """La suppression d'un handler fonctionne."""

        async def my_handler(event: WebhookEvent) -> bool:
            return True

        webhook_service.register_handler(WebhookEventType.PAYMENT_CAPTURED, my_handler)
        result = webhook_service.unregister_handler(
            WebhookEventType.PAYMENT_CAPTURED,
            my_handler,
        )

        assert result is True
        assert my_handler not in webhook_service._handlers.get(
            WebhookEventType.PAYMENT_CAPTURED, []
        )

    def test_unregister_nonexistent_handler(self, webhook_service: WebhookService):
        """La suppression d'un handler inexistant retourne False."""

        async def my_handler(event: WebhookEvent) -> bool:
            return True

        result = webhook_service.unregister_handler(
            WebhookEventType.PAYMENT_CAPTURED,
            my_handler,
        )

        assert result is False


# =============================================================================
# TESTS UNITAIRES - PROCESSING
# =============================================================================


class TestWebhookProcessing:
    """Tests pour le traitement des webhooks."""

    @pytest.mark.asyncio
    async def test_process_unknown_provider(
        self, webhook_service: WebhookService, swan_webhook_payload: bytes
    ):
        """Un provider inconnu retourne une erreur."""
        result = await webhook_service.process_webhook(
            provider="unknown_provider",
            payload=swan_webhook_payload,
            signature="test_signature",
        )

        assert result.success is False
        assert result.status == WebhookProcessingStatus.FAILED
        assert "inconnu" in result.error.lower()

    @pytest.mark.asyncio
    async def test_process_invalid_json(self, webhook_service: WebhookService):
        """Un payload JSON invalide retourne une erreur."""
        with patch.object(
            webhook_service._registry, "get_provider", new_callable=AsyncMock
        ) as mock_get:
            mock_provider = MagicMock()
            mock_provider.verify_webhook_signature.return_value = True
            mock_get.return_value = mock_provider

            result = await webhook_service.process_webhook(
                provider="swan",
                payload=b"not valid json {{{",
                signature="test_signature",
            )

            assert result.success is False
            assert "invalide" in result.error.lower()

    @pytest.mark.asyncio
    async def test_process_valid_webhook(
        self,
        webhook_service: WebhookService,
        swan_webhook_payload: bytes,
        mock_swan_provider,
    ):
        """Un webhook valide est traité correctement."""
        with patch.object(
            webhook_service._registry, "get_provider", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_swan_provider

            result = await webhook_service.process_webhook(
                provider="swan",
                payload=swan_webhook_payload,
                signature="valid_signature",
            )

            assert result.success is True
            assert result.status == WebhookProcessingStatus.PROCESSED

    @pytest.mark.asyncio
    async def test_process_invalid_signature(
        self,
        webhook_service: WebhookService,
        swan_webhook_payload: bytes,
    ):
        """Une signature invalide est détectée."""
        with patch.object(
            webhook_service._registry, "get_provider", new_callable=AsyncMock
        ) as mock_get:
            mock_provider = MagicMock()
            mock_provider.verify_webhook_signature.return_value = False
            mock_provider.parse_webhook_event.return_value = WebhookEvent(
                id="evt_12345",
                type=WebhookEventType.PAYMENT_CAPTURED,
                provider=FinanceProviderType.SWAN,
                tenant_id="tenant-test-001",
                payload={},
                raw_payload="{}",
                timestamp=datetime.utcnow(),
            )
            mock_get.return_value = mock_provider

            result = await webhook_service.process_webhook(
                provider="swan",
                payload=swan_webhook_payload,
                signature="invalid_signature",
            )

            assert result.success is False
            assert result.status == WebhookProcessingStatus.SIGNATURE_INVALID

    @pytest.mark.asyncio
    async def test_handler_execution(
        self,
        webhook_service: WebhookService,
        swan_webhook_payload: bytes,
        mock_swan_provider,
    ):
        """Les handlers sont exécutés pour un webhook valide."""
        handler_called = False

        async def test_handler(event: WebhookEvent) -> bool:
            nonlocal handler_called
            handler_called = True
            return True

        webhook_service.register_handler(
            WebhookEventType.PAYMENT_CAPTURED,
            test_handler,
        )

        with patch.object(
            webhook_service._registry, "get_provider", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_swan_provider

            await webhook_service.process_webhook(
                provider="swan",
                payload=swan_webhook_payload,
                signature="valid_signature",
            )

            assert handler_called is True

    @pytest.mark.asyncio
    async def test_handler_failure_reported(
        self,
        webhook_service: WebhookService,
        swan_webhook_payload: bytes,
        mock_swan_provider,
    ):
        """L'échec d'un handler est reporté."""

        async def failing_handler(event: WebhookEvent) -> bool:
            return False

        webhook_service.register_handler(
            WebhookEventType.PAYMENT_CAPTURED,
            failing_handler,
        )

        with patch.object(
            webhook_service._registry, "get_provider", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_swan_provider

            result = await webhook_service.process_webhook(
                provider="swan",
                payload=swan_webhook_payload,
                signature="valid_signature",
            )

            # Le webhook a été traité mais le handler a échoué
            assert result.success is False


# =============================================================================
# TESTS UNITAIRES - PROVIDER MAPPING
# =============================================================================


class TestProviderMapping:
    """Tests pour le mapping des providers."""

    def test_get_provider_type_swan(self, webhook_service: WebhookService):
        """Le mapping Swan fonctionne."""
        result = webhook_service._get_provider_type("swan")
        assert result == FinanceProviderType.SWAN

    def test_get_provider_type_nmi(self, webhook_service: WebhookService):
        """Le mapping NMI fonctionne."""
        result = webhook_service._get_provider_type("nmi")
        assert result == FinanceProviderType.NMI

    def test_get_provider_type_defacto(self, webhook_service: WebhookService):
        """Le mapping Defacto fonctionne."""
        result = webhook_service._get_provider_type("defacto")
        assert result == FinanceProviderType.DEFACTO

    def test_get_provider_type_solaris(self, webhook_service: WebhookService):
        """Le mapping Solaris fonctionne."""
        result = webhook_service._get_provider_type("solaris")
        assert result == FinanceProviderType.SOLARIS

    def test_get_provider_type_case_insensitive(self, webhook_service: WebhookService):
        """Le mapping est case insensitive."""
        assert webhook_service._get_provider_type("SWAN") == FinanceProviderType.SWAN
        assert webhook_service._get_provider_type("Swan") == FinanceProviderType.SWAN

    def test_get_provider_type_unknown(self, webhook_service: WebhookService):
        """Un provider inconnu retourne None."""
        result = webhook_service._get_provider_type("unknown")
        assert result is None


# =============================================================================
# TESTS UNITAIRES - SIGNATURE HEADERS
# =============================================================================


class TestSignatureHeaders:
    """Tests pour les headers de signature."""

    def test_signature_header_swan(self):
        """Le header Swan est correct."""
        assert WebhookService.SIGNATURE_HEADERS[FinanceProviderType.SWAN] == "X-Swan-Signature"

    def test_signature_header_nmi(self):
        """Le header NMI est correct."""
        assert WebhookService.SIGNATURE_HEADERS[FinanceProviderType.NMI] == "X-Nmi-Signature"

    def test_signature_header_defacto(self):
        """Le header Defacto est correct."""
        assert WebhookService.SIGNATURE_HEADERS[FinanceProviderType.DEFACTO] == "X-Defacto-Signature"

    def test_signature_header_solaris(self):
        """Le header Solaris est correct."""
        assert WebhookService.SIGNATURE_HEADERS[FinanceProviderType.SOLARIS] == "X-Solaris-Signature"


# =============================================================================
# TESTS INTÉGRATION
# =============================================================================


class TestWebhookIntegration:
    """Tests d'intégration."""

    @pytest.mark.asyncio
    async def test_full_webhook_flow(
        self,
        webhook_service: WebhookService,
        swan_webhook_payload: bytes,
        mock_swan_provider,
    ):
        """Le flux complet de webhook fonctionne."""
        events_received = []

        async def capture_handler(event: WebhookEvent) -> bool:
            events_received.append(event)
            return True

        # Enregistrer le handler
        webhook_service.register_handler(
            WebhookEventType.PAYMENT_CAPTURED,
            capture_handler,
        )

        with patch.object(
            webhook_service._registry, "get_provider", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_swan_provider

            # Traiter le webhook
            result = await webhook_service.process_webhook(
                provider="swan",
                payload=swan_webhook_payload,
                signature="valid_signature",
            )

            assert result.success is True
            assert len(events_received) == 1
            assert events_received[0].type == WebhookEventType.PAYMENT_CAPTURED

    @pytest.mark.asyncio
    async def test_multiple_providers(
        self,
        webhook_service: WebhookService,
        swan_webhook_payload: bytes,
        nmi_webhook_payload: bytes,
    ):
        """Plusieurs providers peuvent être traités."""
        with patch.object(
            webhook_service._registry, "get_provider", new_callable=AsyncMock
        ) as mock_get:
            # Mock pour Swan
            swan_provider = MagicMock()
            swan_provider.verify_webhook_signature.return_value = True
            swan_provider.parse_webhook_event.return_value = WebhookEvent(
                id="evt_swan",
                type=WebhookEventType.PAYMENT_CAPTURED,
                provider=FinanceProviderType.SWAN,
                tenant_id="tenant-test-001",
                payload={},
                raw_payload="{}",
                timestamp=datetime.utcnow(),
            )

            # Mock pour NMI
            nmi_provider = MagicMock()
            nmi_provider.verify_webhook_signature.return_value = True
            nmi_provider.parse_webhook_event.return_value = WebhookEvent(
                id="evt_nmi",
                type=WebhookEventType.PAYMENT_CAPTURED,
                provider=FinanceProviderType.NMI,
                tenant_id="tenant-test-001",
                payload={},
                raw_payload="{}",
                timestamp=datetime.utcnow(),
            )

            def get_provider_side_effect(provider_type):
                if provider_type == FinanceProviderType.SWAN:
                    return swan_provider
                elif provider_type == FinanceProviderType.NMI:
                    return nmi_provider
                return None

            mock_get.side_effect = get_provider_side_effect

            # Traiter webhook Swan
            result_swan = await webhook_service.process_webhook(
                provider="swan",
                payload=swan_webhook_payload,
                signature="valid",
            )

            # Traiter webhook NMI
            result_nmi = await webhook_service.process_webhook(
                provider="nmi",
                payload=nmi_webhook_payload,
                signature="valid",
            )

            assert result_swan.success is True
            assert result_nmi.success is True


# =============================================================================
# TESTS SÉCURITÉ
# =============================================================================


class TestWebhookSecurity:
    """Tests de sécurité."""

    def test_tenant_isolation(self, mock_db):
        """Chaque service a son propre tenant_id."""
        service1 = WebhookService(db=mock_db, tenant_id="tenant-1")
        service2 = WebhookService(db=mock_db, tenant_id="tenant-2")

        assert service1.tenant_id != service2.tenant_id

    @pytest.mark.asyncio
    async def test_signature_required_for_handlers(
        self,
        webhook_service: WebhookService,
        swan_webhook_payload: bytes,
    ):
        """Les handlers ne sont pas exécutés sans signature valide."""
        handler_called = False

        async def test_handler(event: WebhookEvent) -> bool:
            nonlocal handler_called
            handler_called = True
            return True

        webhook_service.register_handler(
            WebhookEventType.PAYMENT_CAPTURED,
            test_handler,
        )

        with patch.object(
            webhook_service._registry, "get_provider", new_callable=AsyncMock
        ) as mock_get:
            mock_provider = MagicMock()
            mock_provider.verify_webhook_signature.return_value = False
            mock_provider.parse_webhook_event.return_value = WebhookEvent(
                id="evt_12345",
                type=WebhookEventType.PAYMENT_CAPTURED,
                provider=FinanceProviderType.SWAN,
                tenant_id="tenant-test-001",
                payload={},
                raw_payload="{}",
                timestamp=datetime.utcnow(),
            )
            mock_get.return_value = mock_provider

            await webhook_service.process_webhook(
                provider="swan",
                payload=swan_webhook_payload,
                signature="invalid",
            )

            # Le handler ne doit pas être appelé
            assert handler_called is False
