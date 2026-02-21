"""
Tests des models du module E-Signature.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.modules.esignature.models import (
    ESignatureConfig,
    ProviderCredential,
    SignatureTemplate,
    TemplateField,
    SignatureEnvelope,
    EnvelopeDocument,
    DocumentField,
    EnvelopeSigner,
    SignerAction,
    SignatureAuditEvent,
    SignatureCertificate,
    SignatureReminder,
    SignatureProvider,
    SignatureLevel,
    EnvelopeStatus,
    SignerStatus,
    DocumentType,
    FieldType,
    AuthMethod,
    AuditEventType,
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


class TestESignatureConfig:
    """Tests pour ESignatureConfig."""

    def test_create_config(self, db_session, tenant_id, user_id):
        """Test creation configuration."""
        config = ESignatureConfig(
            tenant_id=tenant_id,
            default_provider=SignatureProvider.YOUSIGN,
            default_signature_level=SignatureLevel.SIMPLE,
            default_expiry_days=30,
            auto_reminders_enabled=True,
            reminder_interval_days=3,
            created_by=user_id
        )
        db_session.add(config)
        db_session.commit()

        assert config.id is not None
        assert config.tenant_id == tenant_id
        assert config.default_provider == SignatureProvider.YOUSIGN
        assert config.is_active is True

    def test_config_defaults(self, db_session, tenant_id):
        """Test valeurs par defaut."""
        config = ESignatureConfig(tenant_id=tenant_id)
        db_session.add(config)
        db_session.commit()

        assert config.default_provider == SignatureProvider.INTERNAL
        assert config.default_signature_level == SignatureLevel.SIMPLE
        assert config.default_expiry_days == 30
        assert config.max_expiry_days == 90
        assert config.auto_reminders_enabled is True
        assert config.allow_decline is True
        assert config.allow_delegation is True


class TestSignatureTemplate:
    """Tests pour SignatureTemplate."""

    def test_create_template(self, db_session, tenant_id, user_id):
        """Test creation template."""
        template = SignatureTemplate(
            tenant_id=tenant_id,
            code="CONTRACT_SALE",
            name="Contrat de vente",
            description="Template pour contrats de vente",
            document_type=DocumentType.CONTRACT,
            default_signature_level=SignatureLevel.ADVANCED,
            default_expiry_days=15,
            signer_roles=[
                {"role": "seller", "name": "Vendeur", "order": 1},
                {"role": "buyer", "name": "Acheteur", "order": 2}
            ],
            created_by=user_id
        )
        db_session.add(template)
        db_session.commit()

        assert template.id is not None
        assert template.code == "CONTRACT_SALE"
        assert template.is_active is True
        assert template.version == 1
        assert len(template.signer_roles) == 2

    def test_template_with_fields(self, db_session, tenant_id, user_id):
        """Test template avec champs."""
        template = SignatureTemplate(
            tenant_id=tenant_id,
            code="NDA",
            name="Accord de confidentialite",
            created_by=user_id
        )
        db_session.add(template)
        db_session.flush()

        field1 = TemplateField(
            tenant_id=tenant_id,
            template_id=template.id,
            field_type=FieldType.SIGNATURE,
            page=1,
            x_position=70.0,
            y_position=80.0,
            signer_role="signatory"
        )
        field2 = TemplateField(
            tenant_id=tenant_id,
            template_id=template.id,
            field_type=FieldType.DATE,
            page=1,
            x_position=70.0,
            y_position=85.0,
            signer_role="signatory"
        )
        db_session.add_all([field1, field2])
        db_session.commit()

        db_session.refresh(template)
        assert len(template.fields) == 2


class TestSignatureEnvelope:
    """Tests pour SignatureEnvelope."""

    def test_create_envelope(self, db_session, tenant_id, user_id):
        """Test creation enveloppe."""
        envelope = SignatureEnvelope(
            tenant_id=tenant_id,
            envelope_number="ESIG-202501-000001",
            name="Contrat Client ABC",
            description="Contrat de service annuel",
            document_type=DocumentType.CONTRACT,
            provider=SignatureProvider.YOUSIGN,
            signature_level=SignatureLevel.SIMPLE,
            expires_at=datetime.utcnow() + timedelta(days=30),
            created_by=user_id
        )
        db_session.add(envelope)
        db_session.commit()

        assert envelope.id is not None
        assert envelope.status == EnvelopeStatus.DRAFT
        assert envelope.total_signers == 0
        assert envelope.signed_count == 0
        assert envelope.version == 1

    def test_envelope_with_signers(self, db_session, tenant_id, user_id):
        """Test enveloppe avec signataires."""
        envelope = SignatureEnvelope(
            tenant_id=tenant_id,
            envelope_number="ESIG-202501-000002",
            name="Test Multi-signataires",
            created_by=user_id
        )
        db_session.add(envelope)
        db_session.flush()

        signer1 = EnvelopeSigner(
            tenant_id=tenant_id,
            envelope_id=envelope.id,
            email="alice@example.com",
            first_name="Alice",
            last_name="Martin",
            signing_order=1,
            auth_method=AuthMethod.EMAIL
        )
        signer2 = EnvelopeSigner(
            tenant_id=tenant_id,
            envelope_id=envelope.id,
            email="bob@example.com",
            first_name="Bob",
            last_name="Dupont",
            signing_order=2,
            auth_method=AuthMethod.SMS_OTP,
            phone="+33612345678"
        )
        db_session.add_all([signer1, signer2])
        db_session.commit()

        db_session.refresh(envelope)
        assert len(envelope.signers) == 2
        assert envelope.signers[0].signing_order == 1
        assert envelope.signers[1].signing_order == 2

    def test_envelope_status_transitions(self, db_session, tenant_id, user_id):
        """Test transitions de statut."""
        envelope = SignatureEnvelope(
            tenant_id=tenant_id,
            envelope_number="ESIG-202501-000003",
            name="Test Status",
            created_by=user_id
        )
        db_session.add(envelope)
        db_session.commit()

        # Draft -> Sent
        envelope.status = EnvelopeStatus.SENT
        envelope.sent_at = datetime.utcnow()
        db_session.commit()
        assert envelope.status == EnvelopeStatus.SENT

        # Sent -> In Progress
        envelope.status = EnvelopeStatus.IN_PROGRESS
        db_session.commit()
        assert envelope.status == EnvelopeStatus.IN_PROGRESS

        # In Progress -> Completed
        envelope.status = EnvelopeStatus.COMPLETED
        envelope.completed_at = datetime.utcnow()
        db_session.commit()
        assert envelope.status == EnvelopeStatus.COMPLETED


class TestEnvelopeSigner:
    """Tests pour EnvelopeSigner."""

    def test_create_signer(self, db_session, tenant_id, user_id):
        """Test creation signataire."""
        envelope = SignatureEnvelope(
            tenant_id=tenant_id,
            envelope_number="ESIG-202501-000004",
            name="Test Signer",
            created_by=user_id
        )
        db_session.add(envelope)
        db_session.flush()

        signer = EnvelopeSigner(
            tenant_id=tenant_id,
            envelope_id=envelope.id,
            email="test@example.com",
            first_name="Jean",
            last_name="Test",
            phone="+33600000000",
            company="ACME Corp",
            job_title="CEO",
            auth_method=AuthMethod.EMAIL,
            access_token="token_unique_123"
        )
        db_session.add(signer)
        db_session.commit()

        assert signer.id is not None
        assert signer.status == SignerStatus.PENDING
        assert signer.notification_count == 0

    def test_signer_status_transitions(self, db_session, tenant_id, user_id):
        """Test transitions de statut signataire."""
        envelope = SignatureEnvelope(
            tenant_id=tenant_id,
            envelope_number="ESIG-202501-000005",
            name="Test Signer Status",
            created_by=user_id
        )
        db_session.add(envelope)
        db_session.flush()

        signer = EnvelopeSigner(
            tenant_id=tenant_id,
            envelope_id=envelope.id,
            email="status@test.com",
            first_name="Status",
            last_name="Test"
        )
        db_session.add(signer)
        db_session.commit()

        # Pending -> Notified
        signer.status = SignerStatus.NOTIFIED
        signer.notified_at = datetime.utcnow()
        signer.notification_count = 1
        db_session.commit()

        # Notified -> Viewed
        signer.status = SignerStatus.VIEWED
        signer.viewed_at = datetime.utcnow()
        db_session.commit()

        # Viewed -> Signed
        signer.status = SignerStatus.SIGNED
        signer.signed_at = datetime.utcnow()
        signer.signature_ip = "192.168.1.1"
        db_session.commit()

        assert signer.status == SignerStatus.SIGNED
        assert signer.signed_at is not None


class TestSignatureAuditEvent:
    """Tests pour SignatureAuditEvent."""

    def test_create_audit_event(self, db_session, tenant_id, user_id):
        """Test creation evenement audit."""
        envelope = SignatureEnvelope(
            tenant_id=tenant_id,
            envelope_number="ESIG-202501-000006",
            name="Test Audit",
            created_by=user_id
        )
        db_session.add(envelope)
        db_session.flush()

        event = SignatureAuditEvent(
            tenant_id=tenant_id,
            envelope_id=envelope.id,
            event_type=AuditEventType.CREATED,
            event_description="Enveloppe creee",
            actor_type="user",
            actor_id=user_id,
            actor_email="admin@test.com",
            ip_address="192.168.1.1"
        )
        db_session.add(event)
        db_session.commit()

        assert event.id is not None
        assert event.event_type == AuditEventType.CREATED

    def test_audit_chain(self, db_session, tenant_id, user_id):
        """Test chaine d'audit."""
        envelope = SignatureEnvelope(
            tenant_id=tenant_id,
            envelope_number="ESIG-202501-000007",
            name="Test Audit Chain",
            created_by=user_id
        )
        db_session.add(envelope)
        db_session.flush()

        events = []
        for i, event_type in enumerate([
            AuditEventType.CREATED,
            AuditEventType.SENT,
            AuditEventType.VIEWED,
            AuditEventType.SIGNED,
            AuditEventType.COMPLETED
        ]):
            previous_hash = events[-1].event_hash if events else None
            event = SignatureAuditEvent(
                tenant_id=tenant_id,
                envelope_id=envelope.id,
                event_type=event_type,
                actor_type="system",
                event_hash=f"hash_{i}",
                previous_hash=previous_hash
            )
            db_session.add(event)
            events.append(event)

        db_session.commit()

        # Verifier la chaine
        assert events[0].previous_hash is None
        for i in range(1, len(events)):
            assert events[i].previous_hash == events[i-1].event_hash


class TestEnums:
    """Tests des enumerations."""

    def test_signature_provider_values(self):
        """Test valeurs SignatureProvider."""
        assert SignatureProvider.INTERNAL.value == "internal"
        assert SignatureProvider.YOUSIGN.value == "yousign"
        assert SignatureProvider.DOCUSIGN.value == "docusign"
        assert SignatureProvider.HELLOSIGN.value == "hellosign"

    def test_signature_level_values(self):
        """Test valeurs SignatureLevel."""
        assert SignatureLevel.SIMPLE.value == "simple"
        assert SignatureLevel.ADVANCED.value == "advanced"
        assert SignatureLevel.QUALIFIED.value == "qualified"

    def test_envelope_status_values(self):
        """Test valeurs EnvelopeStatus."""
        statuses = [
            ("draft", EnvelopeStatus.DRAFT),
            ("sent", EnvelopeStatus.SENT),
            ("in_progress", EnvelopeStatus.IN_PROGRESS),
            ("completed", EnvelopeStatus.COMPLETED),
            ("declined", EnvelopeStatus.DECLINED),
            ("expired", EnvelopeStatus.EXPIRED),
            ("cancelled", EnvelopeStatus.CANCELLED)
        ]
        for value, enum in statuses:
            assert enum.value == value

    def test_field_type_values(self):
        """Test valeurs FieldType."""
        assert FieldType.SIGNATURE.value == "signature"
        assert FieldType.INITIALS.value == "initials"
        assert FieldType.DATE.value == "date"
        assert FieldType.TEXT.value == "text"
        assert FieldType.CHECKBOX.value == "checkbox"
