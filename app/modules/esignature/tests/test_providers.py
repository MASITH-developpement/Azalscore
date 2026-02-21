"""
Tests des providers de signature.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.modules.esignature.providers import (
    YousignProvider,
    DocuSignProvider,
    HelloSignProvider,
    InternalProvider,
    ProviderFactory,
    ProviderEnvelopeInfo,
    ProviderDocumentInfo,
    ProviderSignerInfo,
    ProviderFieldInfo,
    WebhookEventInfo,
)
from app.modules.esignature.models import (
    SignatureProvider,
    SignatureLevel,
    FieldType,
)


class TestProviderFactory:
    """Tests pour ProviderFactory."""

    def test_create_internal_provider(self):
        """Test creation provider interne."""
        provider = ProviderFactory.create(SignatureProvider.INTERNAL, {})
        assert isinstance(provider, InternalProvider)

    def test_create_yousign_provider(self):
        """Test creation provider Yousign."""
        credentials = {
            "api_key": "test_api_key",
            "environment": "sandbox"
        }
        provider = ProviderFactory.create(SignatureProvider.YOUSIGN, credentials)
        assert isinstance(provider, YousignProvider)
        assert provider.environment == "sandbox"

    def test_create_docusign_provider(self):
        """Test creation provider DocuSign."""
        credentials = {
            "integration_key": "test_key",
            "account_id": "test_account",
            "user_id": "test_user",
            "private_key": "test_private_key",
            "environment": "demo"
        }
        provider = ProviderFactory.create(SignatureProvider.DOCUSIGN, credentials)
        assert isinstance(provider, DocuSignProvider)

    def test_create_hellosign_provider(self):
        """Test creation provider HelloSign."""
        credentials = {
            "api_key": "test_api_key",
            "client_id": "test_client_id"
        }
        provider = ProviderFactory.create(SignatureProvider.HELLOSIGN, credentials)
        assert isinstance(provider, HelloSignProvider)


class TestInternalProvider:
    """Tests pour InternalProvider."""

    @pytest.fixture
    def provider(self):
        return InternalProvider()

    @pytest.fixture
    def envelope_info(self):
        return ProviderEnvelopeInfo(
            name="Test Envelope",
            documents=[
                ProviderDocumentInfo(
                    name="document.pdf",
                    content=b"%PDF-1.4 test content",
                    fields=[
                        ProviderFieldInfo(
                            field_type=FieldType.SIGNATURE,
                            page=1,
                            x=70,
                            y=80
                        )
                    ]
                )
            ],
            signers=[
                ProviderSignerInfo(
                    email="signer@test.com",
                    first_name="Test",
                    last_name="Signer"
                )
            ],
            expires_at=datetime.utcnow() + timedelta(days=30)
        )

    @pytest.mark.asyncio
    async def test_create_envelope(self, provider, envelope_info):
        """Test creation enveloppe."""
        external_id = await provider.create_envelope(envelope_info)
        assert external_id.startswith("internal_")

    @pytest.mark.asyncio
    async def test_send_envelope(self, provider, envelope_info):
        """Test envoi enveloppe."""
        external_id = await provider.create_envelope(envelope_info)
        result = await provider.send_envelope(external_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_status(self, provider, envelope_info):
        """Test recuperation statut."""
        external_id = await provider.create_envelope(envelope_info)
        await provider.send_envelope(external_id)

        status = await provider.get_status(external_id)
        assert status.external_id == external_id
        assert status.status == "sent"

    @pytest.mark.asyncio
    async def test_cancel_envelope(self, provider, envelope_info):
        """Test annulation."""
        external_id = await provider.create_envelope(envelope_info)
        result = await provider.cancel_envelope(external_id)
        assert result is True

        status = await provider.get_status(external_id)
        assert status.status == "cancelled"

    @pytest.mark.asyncio
    async def test_verify_credentials(self, provider):
        """Test verification credentials."""
        result = await provider.verify_credentials()
        assert result is True

    def test_verify_webhook(self, provider):
        """Test verification webhook."""
        result = provider.verify_webhook(b"payload", "signature")
        assert result is True

    def test_parse_webhook(self, provider):
        """Test parsing webhook."""
        payload = {
            "event_type": "signed",
            "envelope_id": "test_123"
        }
        event = provider.parse_webhook(payload)
        assert event.event_type == "signed"
        assert event.envelope_external_id == "test_123"


class TestYousignProvider:
    """Tests pour YousignProvider."""

    @pytest.fixture
    def provider(self):
        return YousignProvider(
            api_key="test_api_key",
            environment="sandbox",
            webhook_secret="test_secret"
        )

    def test_initialization(self, provider):
        """Test initialisation."""
        assert provider.environment == "sandbox"
        assert "sandbox" in provider.base_url

    def test_get_headers(self, provider):
        """Test headers API."""
        headers = provider._get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")

    def test_map_signature_level(self, provider):
        """Test mapping niveau signature."""
        assert provider._map_signature_level(SignatureLevel.SIMPLE) == "electronic_signature"
        assert provider._map_signature_level(SignatureLevel.ADVANCED) == "advanced_electronic_signature"
        assert provider._map_signature_level(SignatureLevel.QUALIFIED) == "qualified_electronic_signature"

    def test_map_field_type(self, provider):
        """Test mapping type champ."""
        assert provider._map_field_type(FieldType.SIGNATURE) == "signature"
        assert provider._map_field_type(FieldType.INITIALS) == "initials"
        assert provider._map_field_type(FieldType.DATE) == "date"

    def test_get_auth_mode(self, provider):
        """Test determination mode auth."""
        signer = ProviderSignerInfo(
            email="test@test.com",
            first_name="Test",
            last_name="User"
        )
        assert provider._get_auth_mode(signer) == "no_otp"

        signer.require_sms_otp = True
        assert provider._get_auth_mode(signer) == "otp_sms"

        signer.require_id_verification = True
        assert provider._get_auth_mode(signer) == "id_document"

    def test_verify_webhook_valid(self, provider):
        """Test verification webhook valide."""
        import hmac
        import hashlib

        payload = b'{"event": "test"}'
        expected = hmac.new(
            provider.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        result = provider.verify_webhook(payload, expected)
        assert result is True

    def test_verify_webhook_invalid(self, provider):
        """Test verification webhook invalide."""
        payload = b'{"event": "test"}'
        result = provider.verify_webhook(payload, "invalid_signature")
        assert result is False

    def test_parse_webhook(self, provider):
        """Test parsing webhook."""
        payload = {
            "event_name": "signature_request.done",
            "data": {
                "signature_request": {"id": "yousign_123"},
                "signer": {"id": "signer_456"}
            }
        }
        event = provider.parse_webhook(payload)

        assert event.provider == SignatureProvider.YOUSIGN
        assert event.event_type == "signature_request.done"
        assert event.envelope_external_id == "yousign_123"
        assert event.signer_external_id == "signer_456"


class TestDocuSignProvider:
    """Tests pour DocuSignProvider."""

    @pytest.fixture
    def provider(self):
        return DocuSignProvider(
            integration_key="test_integration_key",
            account_id="test_account_id",
            user_id="test_user_id",
            private_key="test_private_key",
            environment="demo",
            webhook_secret="test_secret"
        )

    def test_initialization(self, provider):
        """Test initialisation."""
        assert provider.environment == "demo"
        assert "demo" in provider.base_url

    def test_build_tabs_signature(self, provider):
        """Test construction tabs signature."""
        documents = [
            ProviderDocumentInfo(
                name="doc.pdf",
                content=b"test",
                fields=[
                    ProviderFieldInfo(
                        field_type=FieldType.SIGNATURE,
                        page=1,
                        x=100,
                        y=200,
                        signer_index=0
                    )
                ]
            )
        ]
        tabs = provider._build_tabs(documents, 0)

        assert len(tabs["signHereTabs"]) == 1
        assert tabs["signHereTabs"][0]["pageNumber"] == "1"
        assert tabs["signHereTabs"][0]["xPosition"] == "100"

    def test_build_tabs_multiple_types(self, provider):
        """Test construction tabs multiples types."""
        documents = [
            ProviderDocumentInfo(
                name="doc.pdf",
                content=b"test",
                fields=[
                    ProviderFieldInfo(
                        field_type=FieldType.SIGNATURE,
                        page=1, x=100, y=200, signer_index=0
                    ),
                    ProviderFieldInfo(
                        field_type=FieldType.INITIALS,
                        page=1, x=100, y=250, signer_index=0
                    ),
                    ProviderFieldInfo(
                        field_type=FieldType.DATE,
                        page=1, x=100, y=300, signer_index=0
                    ),
                    ProviderFieldInfo(
                        field_type=FieldType.TEXT,
                        page=1, x=100, y=350, signer_index=0
                    ),
                    ProviderFieldInfo(
                        field_type=FieldType.CHECKBOX,
                        page=1, x=100, y=400, signer_index=0
                    )
                ]
            )
        ]
        tabs = provider._build_tabs(documents, 0)

        assert len(tabs["signHereTabs"]) == 1
        assert len(tabs["initialHereTabs"]) == 1
        assert len(tabs["dateSignedTabs"]) == 1
        assert len(tabs["textTabs"]) == 1
        assert len(tabs["checkboxTabs"]) == 1

    def test_parse_webhook(self, provider):
        """Test parsing webhook DocuSign."""
        payload = {
            "envelopeStatus": {
                "status": "completed",
                "envelopeId": "docusign_envelope_123"
            }
        }
        event = provider.parse_webhook(payload)

        assert event.provider == SignatureProvider.DOCUSIGN
        assert event.event_type == "completed"
        assert event.envelope_external_id == "docusign_envelope_123"


class TestHelloSignProvider:
    """Tests pour HelloSignProvider."""

    @pytest.fixture
    def provider(self):
        return HelloSignProvider(
            api_key="test_api_key",
            client_id="test_client_id",
            webhook_secret="test_secret"
        )

    def test_initialization(self, provider):
        """Test initialisation."""
        assert provider.api_key == "test_api_key"
        assert "hellosign" in provider.base_url

    def test_parse_webhook(self, provider):
        """Test parsing webhook HelloSign."""
        payload = {
            "event": {"event_type": "signature_request_all_signed"},
            "signature_request": {"signature_request_id": "hellosign_123"}
        }
        event = provider.parse_webhook(payload)

        assert event.provider == SignatureProvider.HELLOSIGN
        assert event.event_type == "signature_request_all_signed"
        assert event.envelope_external_id == "hellosign_123"


class TestWebhookEventInfo:
    """Tests pour WebhookEventInfo."""

    def test_create_webhook_event(self):
        """Test creation evenement webhook."""
        event = WebhookEventInfo(
            provider=SignatureProvider.YOUSIGN,
            event_type="signed",
            envelope_external_id="env_123",
            signer_external_id="signer_456"
        )

        assert event.provider == SignatureProvider.YOUSIGN
        assert event.event_type == "signed"
        assert event.envelope_external_id == "env_123"
        assert event.signer_external_id == "signer_456"
        assert event.timestamp is not None


class TestProviderEnvelopeInfo:
    """Tests pour ProviderEnvelopeInfo."""

    def test_create_envelope_info(self):
        """Test creation info enveloppe."""
        envelope = ProviderEnvelopeInfo(
            name="Test Envelope",
            documents=[],
            signers=[],
            signature_level=SignatureLevel.ADVANCED,
            metadata={"key": "value"}
        )

        assert envelope.name == "Test Envelope"
        assert envelope.signature_level == SignatureLevel.ADVANCED
        assert envelope.metadata["key"] == "value"


class TestProviderDocumentInfo:
    """Tests pour ProviderDocumentInfo."""

    def test_content_hash(self):
        """Test hash du contenu."""
        content = b"test content for hashing"
        doc = ProviderDocumentInfo(
            name="test.pdf",
            content=content
        )

        import hashlib
        expected_hash = hashlib.sha256(content).hexdigest()
        assert doc.content_hash == expected_hash

    def test_content_hash_different_content(self):
        """Test hash different pour contenu different."""
        doc1 = ProviderDocumentInfo(name="doc1.pdf", content=b"content 1")
        doc2 = ProviderDocumentInfo(name="doc2.pdf", content=b"content 2")

        assert doc1.content_hash != doc2.content_hash
