"""
Tests des repositories du module E-Signature.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.modules.esignature.models import (
    SignatureEnvelope,
    EnvelopeSigner,
    SignatureProvider,
    SignatureLevel,
    EnvelopeStatus,
    SignerStatus,
    DocumentType,
)
from app.modules.esignature.repository import (
    ESignatureConfigRepository,
    SignatureTemplateRepository,
    SignatureEnvelopeRepository,
    EnvelopeSignerRepository,
    SignatureAuditEventRepository,
)
from app.modules.esignature.schemas import EnvelopeFilters, TemplateFilters


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
    return "tenant_repo_test"


@pytest.fixture
def user_id():
    return uuid4()


class TestSignatureEnvelopeRepository:
    """Tests pour SignatureEnvelopeRepository."""

    def test_base_query_filters_tenant(self, db_session, tenant_id):
        """Test que _base_query filtre par tenant_id."""
        repo = SignatureEnvelopeRepository(db_session, tenant_id)

        # Creer enveloppe pour ce tenant
        env1 = SignatureEnvelope(
            tenant_id=tenant_id,
            envelope_number="ENV-001",
            name="Test 1"
        )
        # Creer enveloppe pour autre tenant
        env2 = SignatureEnvelope(
            tenant_id="other_tenant",
            envelope_number="ENV-002",
            name="Test 2"
        )
        db_session.add_all([env1, env2])
        db_session.commit()

        # Ne doit trouver que celle du tenant
        envelopes, total = repo.list(page_size=100)
        assert total == 1
        assert envelopes[0].tenant_id == tenant_id

    def test_get_next_number(self, db_session, tenant_id):
        """Test generation numero enveloppe."""
        repo = SignatureEnvelopeRepository(db_session, tenant_id)

        num1 = repo.get_next_number()
        assert num1.startswith("ESIG-")
        assert num1.endswith("000001")

        # Creer une enveloppe
        env = SignatureEnvelope(
            tenant_id=tenant_id,
            envelope_number=num1,
            name="Test"
        )
        db_session.add(env)
        db_session.commit()

        num2 = repo.get_next_number()
        assert num2.endswith("000002")

    def test_create_envelope(self, db_session, tenant_id, user_id):
        """Test creation enveloppe via repository."""
        repo = SignatureEnvelopeRepository(db_session, tenant_id)

        data = {
            "name": "Test Envelope",
            "document_type": DocumentType.CONTRACT,
            "signers": [
                {
                    "email": "signer@test.com",
                    "first_name": "Test",
                    "last_name": "Signer",
                    "signing_order": 1
                }
            ]
        }
        envelope = repo.create(data, user_id)

        assert envelope.id is not None
        assert envelope.tenant_id == tenant_id
        assert envelope.created_by == user_id
        assert len(envelope.signers) == 1

    def test_list_with_filters(self, db_session, tenant_id):
        """Test liste avec filtres."""
        repo = SignatureEnvelopeRepository(db_session, tenant_id)

        # Creer plusieurs enveloppes
        for i, status in enumerate([
            EnvelopeStatus.DRAFT,
            EnvelopeStatus.SENT,
            EnvelopeStatus.COMPLETED
        ]):
            env = SignatureEnvelope(
                tenant_id=tenant_id,
                envelope_number=f"ENV-{i:03d}",
                name=f"Test {i}",
                status=status,
                document_type=DocumentType.CONTRACT if i == 0 else DocumentType.INVOICE
            )
            db_session.add(env)
        db_session.commit()

        # Filtrer par statut
        filters = EnvelopeFilters(status=[EnvelopeStatus.DRAFT])
        envelopes, total = repo.list(filters)
        assert total == 1
        assert envelopes[0].status == EnvelopeStatus.DRAFT

        # Filtrer par document_type
        filters = EnvelopeFilters(document_type=DocumentType.INVOICE)
        envelopes, total = repo.list(filters)
        assert total == 2

    def test_list_pagination(self, db_session, tenant_id):
        """Test pagination."""
        repo = SignatureEnvelopeRepository(db_session, tenant_id)

        # Creer 25 enveloppes
        for i in range(25):
            env = SignatureEnvelope(
                tenant_id=tenant_id,
                envelope_number=f"ENV-{i:03d}",
                name=f"Test {i}"
            )
            db_session.add(env)
        db_session.commit()

        # Page 1
        envelopes, total = repo.list(page=1, page_size=10)
        assert len(envelopes) == 10
        assert total == 25

        # Page 3
        envelopes, total = repo.list(page=3, page_size=10)
        assert len(envelopes) == 5

    def test_soft_delete(self, db_session, tenant_id, user_id):
        """Test soft delete."""
        repo = SignatureEnvelopeRepository(db_session, tenant_id)

        envelope = SignatureEnvelope(
            tenant_id=tenant_id,
            envelope_number="ENV-DEL",
            name="To Delete"
        )
        db_session.add(envelope)
        db_session.commit()

        # Soft delete
        result = repo.soft_delete(envelope, user_id)
        assert result is True
        assert envelope.is_deleted is True
        assert envelope.deleted_by == user_id

        # Ne doit plus apparaitre dans les resultats
        envelopes, total = repo.list()
        assert total == 0

        # Doit apparaitre avec include_deleted
        repo_with_deleted = SignatureEnvelopeRepository(db_session, tenant_id, include_deleted=True)
        envelopes, total = repo_with_deleted.list()
        assert total == 1

    def test_get_expiring_soon(self, db_session, tenant_id):
        """Test recuperation enveloppes expirant bientot."""
        repo = SignatureEnvelopeRepository(db_session, tenant_id)

        # Enveloppe expirant dans 2 jours
        env1 = SignatureEnvelope(
            tenant_id=tenant_id,
            envelope_number="ENV-EXP-1",
            name="Expiring soon",
            status=EnvelopeStatus.SENT,
            expires_at=datetime.utcnow() + timedelta(days=2)
        )
        # Enveloppe expirant dans 10 jours
        env2 = SignatureEnvelope(
            tenant_id=tenant_id,
            envelope_number="ENV-EXP-2",
            name="Not expiring soon",
            status=EnvelopeStatus.SENT,
            expires_at=datetime.utcnow() + timedelta(days=10)
        )
        db_session.add_all([env1, env2])
        db_session.commit()

        expiring = repo.get_expiring_soon(days=3)
        assert len(expiring) == 1
        assert expiring[0].envelope_number == "ENV-EXP-1"

    def test_count_by_status(self, db_session, tenant_id):
        """Test comptage par statut."""
        repo = SignatureEnvelopeRepository(db_session, tenant_id)

        for i, status in enumerate([
            EnvelopeStatus.DRAFT, EnvelopeStatus.DRAFT,
            EnvelopeStatus.SENT,
            EnvelopeStatus.COMPLETED, EnvelopeStatus.COMPLETED, EnvelopeStatus.COMPLETED
        ]):
            env = SignatureEnvelope(
                tenant_id=tenant_id,
                envelope_number=f"ENV-CNT-{i}",
                name=f"Count {i}",
                status=status
            )
            db_session.add(env)
        db_session.commit()

        counts = repo.count_by_status()
        assert counts.get("draft", 0) == 2
        assert counts.get("sent", 0) == 1
        assert counts.get("completed", 0) == 3


class TestEnvelopeSignerRepository:
    """Tests pour EnvelopeSignerRepository."""

    @pytest.fixture
    def envelope(self, db_session, tenant_id):
        """Cree une enveloppe de test."""
        env = SignatureEnvelope(
            tenant_id=tenant_id,
            envelope_number="ENV-SIGNER",
            name="Signer Test"
        )
        db_session.add(env)
        db_session.commit()
        return env

    def test_get_by_token(self, db_session, tenant_id, envelope):
        """Test recuperation par token."""
        repo = EnvelopeSignerRepository(db_session, tenant_id)

        signer = EnvelopeSigner(
            tenant_id=tenant_id,
            envelope_id=envelope.id,
            email="token@test.com",
            first_name="Token",
            last_name="Test",
            access_token="unique_token_123",
            token_expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db_session.add(signer)
        db_session.commit()

        found = repo.get_by_token("unique_token_123")
        assert found is not None
        assert found.email == "token@test.com"

        # Token expire
        signer.token_expires_at = datetime.utcnow() - timedelta(days=1)
        db_session.commit()

        not_found = repo.get_by_token("unique_token_123")
        assert not_found is None

    def test_get_pending_by_envelope(self, db_session, tenant_id, envelope):
        """Test recuperation signataires en attente."""
        repo = EnvelopeSignerRepository(db_session, tenant_id)

        signers = [
            EnvelopeSigner(
                tenant_id=tenant_id,
                envelope_id=envelope.id,
                email="pending@test.com",
                first_name="Pending",
                last_name="User",
                status=SignerStatus.PENDING
            ),
            EnvelopeSigner(
                tenant_id=tenant_id,
                envelope_id=envelope.id,
                email="signed@test.com",
                first_name="Signed",
                last_name="User",
                status=SignerStatus.SIGNED
            ),
            EnvelopeSigner(
                tenant_id=tenant_id,
                envelope_id=envelope.id,
                email="viewed@test.com",
                first_name="Viewed",
                last_name="User",
                status=SignerStatus.VIEWED
            )
        ]
        db_session.add_all(signers)
        db_session.commit()

        pending = repo.get_pending_by_envelope(envelope.id)
        assert len(pending) == 2  # PENDING et VIEWED

    def test_get_next_signer(self, db_session, tenant_id, envelope):
        """Test recuperation prochain signataire."""
        repo = EnvelopeSignerRepository(db_session, tenant_id)

        signers = [
            EnvelopeSigner(
                tenant_id=tenant_id,
                envelope_id=envelope.id,
                email="first@test.com",
                first_name="First",
                last_name="User",
                signing_order=1,
                status=SignerStatus.SIGNED
            ),
            EnvelopeSigner(
                tenant_id=tenant_id,
                envelope_id=envelope.id,
                email="second@test.com",
                first_name="Second",
                last_name="User",
                signing_order=2,
                status=SignerStatus.PENDING
            ),
            EnvelopeSigner(
                tenant_id=tenant_id,
                envelope_id=envelope.id,
                email="third@test.com",
                first_name="Third",
                last_name="User",
                signing_order=3,
                status=SignerStatus.PENDING
            )
        ]
        db_session.add_all(signers)
        db_session.commit()

        next_signer = repo.get_next_signer(envelope.id)
        assert next_signer.signing_order == 2
        assert next_signer.email == "second@test.com"

    def test_update_status(self, db_session, tenant_id, envelope):
        """Test mise a jour statut."""
        repo = EnvelopeSignerRepository(db_session, tenant_id)

        signer = EnvelopeSigner(
            tenant_id=tenant_id,
            envelope_id=envelope.id,
            email="status@test.com",
            first_name="Status",
            last_name="Test",
            status=SignerStatus.PENDING
        )
        db_session.add(signer)
        db_session.commit()

        # Marquer comme signe
        updated = repo.update_status(
            signer,
            SignerStatus.SIGNED,
            ip_address="192.168.1.1",
            user_agent="Test Browser"
        )

        assert updated.status == SignerStatus.SIGNED
        assert updated.signed_at is not None
        assert updated.signature_ip == "192.168.1.1"
        assert updated.signature_user_agent == "Test Browser"

    def test_add_action(self, db_session, tenant_id, envelope):
        """Test ajout action."""
        repo = EnvelopeSignerRepository(db_session, tenant_id)

        signer = EnvelopeSigner(
            tenant_id=tenant_id,
            envelope_id=envelope.id,
            email="action@test.com",
            first_name="Action",
            last_name="Test"
        )
        db_session.add(signer)
        db_session.commit()

        action = repo.add_action(
            signer,
            "viewed",
            details={"page": 1},
            ip_address="192.168.1.1"
        )

        assert action.id is not None
        assert action.action == "viewed"
        assert action.ip_address == "192.168.1.1"

        # Verifier lien avec signataire
        db_session.refresh(signer)
        assert len(signer.actions) == 1


class TestSignatureTemplateRepository:
    """Tests pour SignatureTemplateRepository."""

    def test_code_exists(self, db_session, tenant_id):
        """Test verification existence code."""
        repo = SignatureTemplateRepository(db_session, tenant_id)

        from app.modules.esignature.models import SignatureTemplate

        template = SignatureTemplate(
            tenant_id=tenant_id,
            code="EXISTING",
            name="Existing Template"
        )
        db_session.add(template)
        db_session.commit()

        assert repo.code_exists("EXISTING") is True
        assert repo.code_exists("NOT_EXISTING") is False

        # Exclure ID specifique
        assert repo.code_exists("EXISTING", exclude_id=template.id) is False

    def test_increment_usage(self, db_session, tenant_id):
        """Test incrementation usage."""
        repo = SignatureTemplateRepository(db_session, tenant_id)

        from app.modules.esignature.models import SignatureTemplate

        template = SignatureTemplate(
            tenant_id=tenant_id,
            code="USAGE",
            name="Usage Template",
            usage_count=0
        )
        db_session.add(template)
        db_session.commit()

        repo.increment_usage(template)
        db_session.refresh(template)

        assert template.usage_count == 1
        assert template.last_used_at is not None

        repo.increment_usage(template)
        db_session.refresh(template)

        assert template.usage_count == 2
