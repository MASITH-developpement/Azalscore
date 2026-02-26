"""
Tests du service E-Signature.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.modules.esignature.models import (
    ESignatureConfig,
    SignatureTemplate,
    SignatureEnvelope,
    EnvelopeDocument,
    EnvelopeSigner,
    SignatureProvider,
    SignatureLevel,
    EnvelopeStatus,
    SignerStatus,
    DocumentType,
    FieldType,
)
from app.modules.esignature.schemas import (
    ESignatureConfigCreate,
    ESignatureConfigUpdate,
    SignatureTemplateCreate,
    EnvelopeCreate,
    SignerCreate,
    TemplateFieldCreate,
)
from app.modules.esignature.service import ESignatureService, get_esignature_service
from app.modules.esignature.exceptions import (
    ConfigAlreadyExistsError,
    ConfigNotFoundError,
    TemplateNotFoundError,
    TemplateDuplicateCodeError,
    EnvelopeNotFoundError,
    EnvelopeStateError,
    EnvelopeNoSignersError,
    InvalidAccessTokenError,
    SignerAlreadySignedError,
)


# Fixtures
@pytest.fixture
def db_session():
    """Cree une session de test en memoire."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def tenant_id():
    return "tenant_test_123"


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def service(db_session, tenant_id, user_id):
    """Cree une instance du service."""
    return get_esignature_service(db_session, tenant_id, user_id)


class TestConfigService:
    """Tests pour la configuration."""

    def test_create_config(self, service):
        """Test creation configuration."""
        data = ESignatureConfigCreate(
            default_provider=SignatureProvider.YOUSIGN,
            default_signature_level=SignatureLevel.SIMPLE,
            default_expiry_days=30,
            auto_reminders_enabled=True
        )
        config = service.create_config(data)

        assert config.id is not None
        assert config.default_provider == SignatureProvider.YOUSIGN
        assert config.default_expiry_days == 30

    def test_create_config_duplicate(self, service):
        """Test erreur si config existe deja."""
        data = ESignatureConfigCreate()
        service.create_config(data)

        with pytest.raises(ConfigAlreadyExistsError):
            service.create_config(data)

    def test_update_config(self, service):
        """Test mise a jour configuration."""
        create_data = ESignatureConfigCreate()
        service.create_config(create_data)

        update_data = ESignatureConfigUpdate(
            default_expiry_days=60,
            auto_reminders_enabled=False
        )
        config = service.update_config(update_data)

        assert config.default_expiry_days == 60
        assert config.auto_reminders_enabled is False

    def test_update_config_not_found(self, service):
        """Test erreur mise a jour config inexistante."""
        update_data = ESignatureConfigUpdate(default_expiry_days=60)

        with pytest.raises(ConfigNotFoundError):
            service.update_config(update_data)


class TestTemplateService:
    """Tests pour les templates."""

    def test_create_template(self, service):
        """Test creation template."""
        data = SignatureTemplateCreate(
            code="CONTRACT_001",
            name="Contrat standard",
            description="Template de contrat",
            document_type=DocumentType.CONTRACT,
            default_signature_level=SignatureLevel.SIMPLE
        )
        template = service.create_template(data)

        assert template.id is not None
        assert template.code == "CONTRACT_001"
        assert template.name == "Contrat standard"
        assert template.version == 1

    def test_create_template_with_file(self, service):
        """Test creation template avec fichier."""
        data = SignatureTemplateCreate(
            code="CONTRACT_002",
            name="Contrat avec PDF"
        )
        # Simuler un contenu PDF
        pdf_content = b"%PDF-1.4 fake content"
        template = service.create_template(data, pdf_content, "contrat.pdf")

        assert template.file_name == "contrat.pdf"
        assert template.file_size == len(pdf_content)

    def test_create_template_duplicate_code(self, service):
        """Test erreur code template duplique."""
        data = SignatureTemplateCreate(
            code="DUPLICATE",
            name="Template 1"
        )
        service.create_template(data)

        data2 = SignatureTemplateCreate(
            code="DUPLICATE",
            name="Template 2"
        )
        with pytest.raises(TemplateDuplicateCodeError):
            service.create_template(data2)

    def test_get_template_by_code(self, service):
        """Test recuperation template par code."""
        data = SignatureTemplateCreate(
            code="FIND_ME",
            name="Template a trouver"
        )
        created = service.create_template(data)

        found = service.get_template_by_code("FIND_ME")
        assert found is not None
        assert found.id == created.id

    def test_delete_template(self, service):
        """Test suppression template (soft delete)."""
        data = SignatureTemplateCreate(
            code="TO_DELETE",
            name="Template a supprimer"
        )
        template = service.create_template(data)

        result = service.delete_template(template.id)
        assert result is True

        # Le template ne doit plus etre trouve
        found = service.get_template(template.id)
        assert found is None


class TestEnvelopeService:
    """Tests pour les enveloppes."""

    def test_create_envelope(self, service):
        """Test creation enveloppe."""
        data = EnvelopeCreate(
            name="Test Envelope",
            document_type=DocumentType.CONTRACT,
            provider=SignatureProvider.INTERNAL,
            signers=[
                SignerCreate(
                    email="signer@test.com",
                    first_name="John",
                    last_name="Doe"
                )
            ]
        )
        envelope = service.create_envelope(data)

        assert envelope.id is not None
        assert envelope.envelope_number is not None
        assert envelope.status == EnvelopeStatus.DRAFT
        assert len(envelope.signers) == 1

    def test_create_envelope_multiple_signers(self, service):
        """Test enveloppe avec plusieurs signataires."""
        data = EnvelopeCreate(
            name="Multi-signer Envelope",
            signers=[
                SignerCreate(
                    email="signer1@test.com",
                    first_name="Alice",
                    last_name="Smith",
                    signing_order=1
                ),
                SignerCreate(
                    email="signer2@test.com",
                    first_name="Bob",
                    last_name="Jones",
                    signing_order=2
                ),
                SignerCreate(
                    email="signer3@test.com",
                    first_name="Charlie",
                    last_name="Brown",
                    signing_order=3
                )
            ]
        )
        envelope = service.create_envelope(data)

        assert len(envelope.signers) == 3
        assert envelope.total_signers == 3

    def test_envelope_number_uniqueness(self, service):
        """Test unicite numero enveloppe."""
        data = EnvelopeCreate(
            name="Test 1",
            signers=[SignerCreate(email="a@b.com", first_name="A", last_name="B")]
        )
        env1 = service.create_envelope(data)

        data.name = "Test 2"
        env2 = service.create_envelope(data)

        assert env1.envelope_number != env2.envelope_number

    def test_get_envelope_not_found(self, service):
        """Test enveloppe non trouvee."""
        result = service.get_envelope(uuid4())
        assert result is None


class TestEnvelopeActionsService:
    """Tests pour les actions sur enveloppes."""

    @pytest.fixture
    def envelope_with_doc(self, service):
        """Cree une enveloppe avec document."""
        data = EnvelopeCreate(
            name="Envelope with doc",
            signers=[
                SignerCreate(
                    email="signer@test.com",
                    first_name="Test",
                    last_name="Signer"
                )
            ]
        )
        envelope = service.create_envelope(data)

        # Ajouter un document
        service._add_document_to_envelope(
            envelope,
            b"%PDF-1.4 fake content",
            "document.pdf",
            1
        )
        service.db.refresh(envelope)

        return envelope

    @pytest.mark.asyncio
    async def test_send_envelope_no_documents(self, service):
        """Test erreur envoi sans documents."""
        data = EnvelopeCreate(
            name="No docs",
            signers=[SignerCreate(email="a@b.com", first_name="A", last_name="B")]
        )
        envelope = service.create_envelope(data)

        from app.modules.esignature.exceptions import EnvelopeNoDocumentsError
        with pytest.raises(EnvelopeNoDocumentsError):
            await service.send_envelope(envelope.id)

    @pytest.mark.asyncio
    async def test_cancel_envelope(self, service, envelope_with_doc):
        """Test annulation enveloppe."""
        # Simuler l'envoi
        envelope_with_doc.status = EnvelopeStatus.SENT
        envelope_with_doc.external_id = "test_external_id"
        service.db.commit()

        envelope = await service.cancel_envelope(
            envelope_with_doc.id,
            "Test cancellation"
        )

        assert envelope.status == EnvelopeStatus.CANCELLED
        assert envelope.status_message == "Test cancellation"

    @pytest.mark.asyncio
    async def test_cancel_envelope_wrong_status(self, service, envelope_with_doc):
        """Test erreur annulation enveloppe completee."""
        envelope_with_doc.status = EnvelopeStatus.COMPLETED
        service.db.commit()

        with pytest.raises(EnvelopeStateError):
            await service.cancel_envelope(envelope_with_doc.id, "Test")


class TestSignerActionsService:
    """Tests pour les actions des signataires."""

    @pytest.fixture
    def envelope_with_signer(self, service):
        """Cree une enveloppe avec signataire."""
        data = EnvelopeCreate(
            name="Signer test",
            signers=[
                SignerCreate(
                    email="signer@test.com",
                    first_name="Test",
                    last_name="Signer"
                )
            ]
        )
        envelope = service.create_envelope(data)
        service.db.refresh(envelope)
        return envelope

    def test_view_envelope_as_signer(self, service, envelope_with_signer):
        """Test consultation par signataire."""
        signer = envelope_with_signer.signers[0]
        token = signer.access_token

        envelope, viewed_signer = service.view_envelope_as_signer(
            token,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )

        assert viewed_signer.status == SignerStatus.VIEWED
        assert viewed_signer.viewed_at is not None
        assert envelope.viewed_at is not None

    def test_view_envelope_invalid_token(self, service):
        """Test erreur token invalide."""
        with pytest.raises(InvalidAccessTokenError):
            service.view_envelope_as_signer("invalid_token")

    def test_decline_envelope(self, service, envelope_with_signer):
        """Test refus de signature."""
        signer = envelope_with_signer.signers[0]
        token = signer.access_token

        # Mettre l'enveloppe en statut envoyee
        envelope_with_signer.status = EnvelopeStatus.SENT
        service.db.commit()

        envelope, declined_signer = service.decline_envelope(
            token,
            "Je ne suis pas d'accord avec les termes",
            ip_address="192.168.1.1"
        )

        assert declined_signer.status == SignerStatus.DECLINED
        assert declined_signer.decline_reason is not None
        assert envelope.status == EnvelopeStatus.DECLINED

    def test_delegate_signature(self, service, envelope_with_signer):
        """Test delegation de signature."""
        signer = envelope_with_signer.signers[0]
        token = signer.access_token

        # Configurer pour permettre delegation
        config = ESignatureConfig(
            tenant_id=service.tenant_id,
            allow_delegation=True
        )
        service.db.add(config)
        service.db.commit()

        new_signer = service.delegate_signature(
            token,
            delegate_email="delegate@test.com",
            delegate_first_name="Delegate",
            delegate_last_name="User",
            reason="Absence",
            ip_address="192.168.1.1"
        )

        assert new_signer.email == "delegate@test.com"
        assert new_signer.signing_order == signer.signing_order

        # Verifier l'original
        service.db.refresh(signer)
        assert signer.status == SignerStatus.DELEGATED
        assert signer.delegated_to_email == "delegate@test.com"


class TestApprovalService:
    """Tests pour l'approbation."""

    @pytest.fixture
    def pending_approval_envelope(self, service):
        """Cree une enveloppe en attente d'approbation."""
        data = EnvelopeCreate(
            name="Approval test",
            requires_approval=True,
            signers=[
                SignerCreate(
                    email="signer@test.com",
                    first_name="Test",
                    last_name="Signer"
                )
            ]
        )
        envelope = service.create_envelope(data)
        envelope.status = EnvelopeStatus.PENDING_APPROVAL
        service.db.commit()
        return envelope

    def test_approve_envelope(self, service, pending_approval_envelope):
        """Test approbation enveloppe."""
        envelope = service.approve_envelope(
            pending_approval_envelope.id,
            comments="Approuve"
        )

        assert envelope.approval_status == "approved"
        assert envelope.status == EnvelopeStatus.APPROVED
        assert envelope.approved_at is not None
        assert envelope.approved_by is not None

    def test_reject_envelope(self, service, pending_approval_envelope):
        """Test rejet enveloppe."""
        envelope = service.reject_envelope(
            pending_approval_envelope.id,
            reason="Montant incorrect"
        )

        assert envelope.approval_status == "rejected"
        assert envelope.status == EnvelopeStatus.DRAFT

    def test_approve_wrong_status(self, service):
        """Test erreur approbation mauvais statut."""
        data = EnvelopeCreate(
            name="Draft envelope",
            signers=[SignerCreate(email="a@b.com", first_name="A", last_name="B")]
        )
        envelope = service.create_envelope(data)

        with pytest.raises(EnvelopeStateError):
            service.approve_envelope(envelope.id)


class TestAuditService:
    """Tests pour l'audit."""

    def test_audit_trail_creation(self, service):
        """Test creation audit trail a la creation d'enveloppe."""
        data = EnvelopeCreate(
            name="Audit test",
            signers=[
                SignerCreate(
                    email="signer@test.com",
                    first_name="Test",
                    last_name="Signer"
                )
            ]
        )
        envelope = service.create_envelope(data)

        audit = service.get_audit_trail(envelope.id)
        assert len(audit) >= 1
        assert audit[0]["event_type"] == "created"

    def test_audit_trail_view(self, service):
        """Test audit trail lors de consultation."""
        data = EnvelopeCreate(
            name="Audit view test",
            signers=[
                SignerCreate(
                    email="signer@test.com",
                    first_name="Test",
                    last_name="Signer"
                )
            ]
        )
        envelope = service.create_envelope(data)
        signer = envelope.signers[0]

        service.view_envelope_as_signer(signer.access_token, "192.168.1.1")

        audit = service.get_audit_trail(envelope.id)
        viewed_events = [e for e in audit if e["event_type"] == "viewed"]
        assert len(viewed_events) == 1


class TestStatisticsService:
    """Tests pour les statistiques."""

    def test_dashboard_stats(self, service):
        """Test recuperation stats dashboard."""
        # Creer quelques enveloppes
        for i in range(3):
            data = EnvelopeCreate(
                name=f"Stats test {i}",
                signers=[SignerCreate(email=f"s{i}@test.com", first_name="S", last_name="T")]
            )
            service.create_envelope(data)

        stats = service.get_dashboard_stats()

        assert stats.tenant_id == service.tenant_id
        assert stats.today.envelopes_created >= 3

    def test_period_stats(self, service):
        """Test stats par periode."""
        data = EnvelopeCreate(
            name="Period stats test",
            signers=[SignerCreate(email="s@test.com", first_name="S", last_name="T")]
        )
        envelope = service.create_envelope(data)
        envelope.status = EnvelopeStatus.COMPLETED
        envelope.sent_at = datetime.utcnow()
        envelope.completed_at = datetime.utcnow()
        service.db.commit()

        stats = service._calculate_stats(
            datetime.utcnow() - timedelta(days=1),
            datetime.utcnow() + timedelta(days=1),
            "daily"
        )

        assert stats.envelopes_created >= 1
        assert stats.envelopes_completed >= 1
