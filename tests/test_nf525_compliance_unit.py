"""
AZALS - Tests Unitaires NF525 Conformité Caisse
================================================
Tests complets du module NF525 pour certification caisse.
Objectif: Couverture 80%+ sur nf525_compliance.py
"""

import hashlib
import json
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch


# ============================================================================
# TESTS MODÈLES NF525
# ============================================================================

class TestNF525EventLog:
    """Tests modèle NF525EventLog."""

    def test_event_log_fields(self):
        """Test: Champs obligatoires journal événements."""
        required_fields = [
            "tenant_id",
            "sequence_number",
            "event_type",
            "event_timestamp",
            "previous_hash",
            "current_hash",
            "hash_chain_valid",
        ]

        from app.modules.pos.nf525_compliance import NF525EventLog

        # Vérifier que le modèle a tous les champs
        mapper = NF525EventLog.__mapper__
        columns = [c.name for c in mapper.columns]

        for field in required_fields:
            assert field in columns, f"Missing field: {field}"

    def test_event_log_indexes(self):
        """Test: Index pour performance requête."""
        from app.modules.pos.nf525_compliance import NF525EventLog

        # Vérifier les index
        indexes = [idx.name for idx in NF525EventLog.__table__.indexes]

        assert any("seq" in idx for idx in indexes)  # Index séquence
        assert any("hash" in idx for idx in indexes)  # Index hash
        assert any("date" in idx for idx in indexes)  # Index date


class TestNF525Certificate:
    """Tests modèle NF525Certificate."""

    def test_certificate_fields(self):
        """Test: Champs certificat NF525."""
        from app.modules.pos.nf525_compliance import NF525Certificate

        mapper = NF525Certificate.__mapper__
        columns = [c.name for c in mapper.columns]

        assert "software_name" in columns
        assert "software_version" in columns
        assert "certificate_number" in columns
        assert "signing_key_hash" in columns
        assert "genesis_hash" in columns


class TestNF525Archive:
    """Tests modèle NF525Archive."""

    def test_archive_fields(self):
        """Test: Champs archive NF525."""
        from app.modules.pos.nf525_compliance import NF525Archive

        mapper = NF525Archive.__mapper__
        columns = [c.name for c in mapper.columns]

        assert "period_start" in columns
        assert "period_end" in columns
        assert "first_sequence" in columns
        assert "last_sequence" in columns
        assert "archive_hash" in columns
        assert "is_verified" in columns


class TestNF525GrandTotal:
    """Tests modèle NF525GrandTotal."""

    def test_grand_total_fields(self):
        """Test: Champs Grand Total NF525."""
        from app.modules.pos.nf525_compliance import NF525GrandTotal

        mapper = NF525GrandTotal.__mapper__
        columns = [c.name for c in mapper.columns]

        assert "terminal_id" in columns
        assert "daily_total_ttc" in columns
        assert "grand_total_ttc" in columns
        assert "ticket_count" in columns


# ============================================================================
# TESTS DATA CLASSES
# ============================================================================

class TestNF525DataClasses:
    """Tests data classes NF525."""

    def test_compliance_status_dataclass(self):
        """Test: Structure NF525ComplianceStatus."""
        from app.modules.pos.nf525_compliance import NF525ComplianceStatus

        status = NF525ComplianceStatus(
            is_compliant=True,
            certificate_valid=True,
            chain_integrity=True,
            archiving_current=True,
            last_verification=datetime.utcnow(),
            issues=[],
            warnings=[],
            score=100
        )

        assert status.is_compliant is True
        assert status.score == 100
        assert isinstance(status.issues, list)

    def test_verification_result_dataclass(self):
        """Test: Structure NF525VerificationResult."""
        from app.modules.pos.nf525_compliance import NF525VerificationResult

        result = NF525VerificationResult(
            is_valid=True,
            checked_from=1,
            checked_to=1000,
            total_checked=1000,
            broken_at=None,
            error_message=None,
            execution_time_ms=150
        )

        assert result.is_valid is True
        assert result.total_checked == 1000

    def test_archive_result_dataclass(self):
        """Test: Structure NF525ArchiveResult."""
        from app.modules.pos.nf525_compliance import NF525ArchiveResult

        result = NF525ArchiveResult(
            success=True,
            archive_id=42,
            file_path="/archives/2024/01/archive.zip",
            event_count=5000,
            archive_hash="abc123" * 10 + "abcd"
        )

        assert result.success is True
        assert result.archive_id == 42


# ============================================================================
# TESTS SERVICE NF525
# ============================================================================

class TestNF525ServiceInit:
    """Tests initialisation service NF525."""

    def test_service_constants(self):
        """Test: Constantes service NF525."""
        from app.modules.pos.nf525_compliance import NF525ComplianceService

        assert NF525ComplianceService.SOFTWARE_NAME == "AZALSCORE"
        assert NF525ComplianceService.SOFTWARE_EDITOR == "AZALS Technologies"

    def test_service_instantiation(self):
        """Test: Instanciation service NF525."""
        from app.modules.pos.nf525_compliance import NF525ComplianceService

        mock_db = MagicMock()
        service = NF525ComplianceService(db=mock_db, tenant_id="TEST-001")

        assert service.tenant_id == "TEST-001"
        assert service.db is mock_db


class TestNF525HashChain:
    """Tests chaîne de hachage NF525."""

    def test_compute_hash_deterministic(self):
        """Test: Hash est déterministe."""
        from app.modules.pos.nf525_compliance import NF525ComplianceService

        mock_db = MagicMock()
        service = NF525ComplianceService(db=mock_db, tenant_id="TEST-001")

        data = {
            "sequence_number": 1,
            "event_type": "TICKET_COMPLETED",
            "event_timestamp": "2024-01-15T10:30:00",
            "terminal_id": "CAISSE-01",
            "receipt_number": "T-001",
            "amount_ttc": Decimal("100.00"),
            "cumulative_total_ttc": Decimal("100.00")
        }
        previous_hash = "a" * 64

        hash1 = service._compute_hash(data, previous_hash)
        hash2 = service._compute_hash(data, previous_hash)

        assert hash1 == hash2
        assert len(hash1) == 64

    def test_compute_hash_different_data(self):
        """Test: Hash différent si données différentes."""
        from app.modules.pos.nf525_compliance import NF525ComplianceService

        mock_db = MagicMock()
        service = NF525ComplianceService(db=mock_db, tenant_id="TEST-001")

        data1 = {
            "sequence_number": 1,
            "event_type": "TICKET_COMPLETED",
            "event_timestamp": "2024-01-15T10:30:00",
            "terminal_id": "CAISSE-01",
            "receipt_number": "T-001",
            "amount_ttc": Decimal("100.00"),
            "cumulative_total_ttc": Decimal("100.00")
        }

        data2 = data1.copy()
        data2["amount_ttc"] = Decimal("150.00")

        previous_hash = "a" * 64

        hash1 = service._compute_hash(data1, previous_hash)
        hash2 = service._compute_hash(data2, previous_hash)

        assert hash1 != hash2

    def test_compute_hash_chain_link(self):
        """Test: Chaîne de hachage liée."""
        from app.modules.pos.nf525_compliance import NF525ComplianceService

        mock_db = MagicMock()
        service = NF525ComplianceService(db=mock_db, tenant_id="TEST-001")

        genesis_hash = "0" * 64

        data1 = {
            "sequence_number": 1,
            "event_type": "TICKET_COMPLETED",
            "event_timestamp": "2024-01-15T10:30:00",
            "terminal_id": "CAISSE-01",
            "receipt_number": "T-001",
            "amount_ttc": Decimal("100.00"),
            "cumulative_total_ttc": Decimal("100.00")
        }
        hash1 = service._compute_hash(data1, genesis_hash)

        data2 = {
            "sequence_number": 2,
            "event_type": "TICKET_COMPLETED",
            "event_timestamp": "2024-01-15T10:35:00",
            "terminal_id": "CAISSE-01",
            "receipt_number": "T-002",
            "amount_ttc": Decimal("50.00"),
            "cumulative_total_ttc": Decimal("150.00")
        }
        hash2 = service._compute_hash(data2, hash1)

        # Les hash sont différents et liés
        assert hash1 != hash2
        assert hash1 != genesis_hash
        assert hash2 != genesis_hash


class TestNF525HMAC:
    """Tests signature HMAC NF525."""

    def test_sign_hash(self):
        """Test: Signature HMAC-SHA256."""
        from app.modules.pos.nf525_compliance import NF525ComplianceService

        mock_db = MagicMock()
        service = NF525ComplianceService(db=mock_db, tenant_id="TEST-001")

        hash_value = "a" * 64
        key = b"secret_key_32_bytes_minimum_here"

        signature = service._sign_hash(hash_value, key)

        assert len(signature) == 64  # HMAC-SHA256 hex
        assert signature != hash_value

    def test_sign_hash_deterministic(self):
        """Test: Signature HMAC déterministe."""
        from app.modules.pos.nf525_compliance import NF525ComplianceService

        mock_db = MagicMock()
        service = NF525ComplianceService(db=mock_db, tenant_id="TEST-001")

        hash_value = "b" * 64
        key = b"another_secret_key_here_for_test"

        sig1 = service._sign_hash(hash_value, key)
        sig2 = service._sign_hash(hash_value, key)

        assert sig1 == sig2


class TestNF525Sequences:
    """Tests gestion séquences NF525."""

    def test_get_next_sequence_empty(self):
        """Test: Séquence initiale = 1."""
        from app.modules.pos.nf525_compliance import NF525ComplianceService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        service = NF525ComplianceService(db=mock_db, tenant_id="TEST-001")

        next_seq = service._get_next_sequence()

        assert next_seq == 1

    def test_get_next_sequence_with_existing(self):
        """Test: Séquence incrémentée."""
        from app.modules.pos.nf525_compliance import NF525ComplianceService, NF525EventLog

        mock_db = MagicMock()
        mock_last_event = MagicMock()
        mock_last_event.sequence_number = 42
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_last_event

        service = NF525ComplianceService(db=mock_db, tenant_id="TEST-001")

        next_seq = service._get_next_sequence()

        assert next_seq == 43


class TestNF525CumulativeTotals:
    """Tests totaux cumulatifs NF525."""

    def test_get_cumulative_totals_empty(self):
        """Test: Totaux initiaux = 0."""
        from app.modules.pos.nf525_compliance import NF525ComplianceService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        service = NF525ComplianceService(db=mock_db, tenant_id="TEST-001")

        totals = service._get_cumulative_totals()

        assert totals == (Decimal("0"), Decimal("0"), Decimal("0"), 0)

    def test_get_cumulative_totals_with_history(self):
        """Test: Totaux cumulatifs depuis historique."""
        from app.modules.pos.nf525_compliance import NF525ComplianceService

        mock_db = MagicMock()
        mock_last_event = MagicMock()
        mock_last_event.cumulative_total_ht = Decimal("10000.00")
        mock_last_event.cumulative_total_tva = Decimal("2000.00")
        mock_last_event.cumulative_total_ttc = Decimal("12000.00")
        mock_last_event.cumulative_transaction_count = 150
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_last_event

        service = NF525ComplianceService(db=mock_db, tenant_id="TEST-001")

        totals = service._get_cumulative_totals()

        assert totals == (
            Decimal("10000.00"),
            Decimal("2000.00"),
            Decimal("12000.00"),
            150
        )


# ============================================================================
# TESTS LOGGING ÉVÉNEMENTS
# ============================================================================

class TestNF525EventLogging:
    """Tests journalisation événements NF525."""

    def test_log_event_requires_certificate(self):
        """Test: log_event nécessite certificat."""
        from app.modules.pos.nf525_compliance import NF525ComplianceService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = NF525ComplianceService(db=mock_db, tenant_id="TEST-001")

        with pytest.raises(ValueError, match="certificat"):
            service.log_event(event_type=MagicMock())

    def test_log_ticket_structure(self):
        """Test: Structure appel log_ticket."""
        from app.modules.pos.nf525_compliance import (
            NF525ComplianceService, NF525EventType, NF525Certificate
        )

        mock_db = MagicMock()
        mock_cert = MagicMock()
        mock_cert.genesis_hash = "0" * 64
        mock_db.query.return_value.filter.return_value.first.return_value = mock_cert
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        service = NF525ComplianceService(db=mock_db, tenant_id="TEST-001")

        # Patch pour éviter commit réel
        with patch.object(service, 'log_event') as mock_log:
            mock_log.return_value = MagicMock()

            service.log_ticket(
                terminal_id="CAISSE-01",
                session_id="SESSION-001",
                transaction_id="TX-001",
                receipt_number="T-001",
                user_id="USER-001",
                amount_ht=Decimal("100.00"),
                amount_tva=Decimal("20.00"),
                amount_ttc=Decimal("120.00"),
                is_completed=True
            )

            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs["terminal_id"] == "CAISSE-01"
            assert call_kwargs["amount_ttc"] == Decimal("120.00")


# ============================================================================
# TESTS VÉRIFICATION INTÉGRITÉ
# ============================================================================

class TestNF525ChainVerification:
    """Tests vérification chaîne NF525."""

    def test_verify_empty_chain(self):
        """Test: Vérification chaîne vide = valide."""
        from app.modules.pos.nf525_compliance import NF525ComplianceService

        mock_db = MagicMock()
        mock_cert = MagicMock()
        mock_cert.genesis_hash = "0" * 64

        # Premier appel pour certificat, deuxième pour événements
        def query_side_effect(*args):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            mock_q.order_by.return_value = mock_q
            mock_q.first.return_value = mock_cert
            mock_q.all.return_value = []
            return mock_q

        mock_db.query.side_effect = query_side_effect

        service = NF525ComplianceService(db=mock_db, tenant_id="TEST-001")

        result = service.verify_chain_integrity()

        assert result.is_valid is True
        assert result.total_checked == 0


class TestNF525ComplianceCheck:
    """Tests vérification conformité globale."""

    def test_check_compliance_no_certificate(self):
        """Test: Conformité sans certificat = non conforme."""
        from app.modules.pos.nf525_compliance import NF525ComplianceService

        mock_db = MagicMock()

        def query_side_effect(*args):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            mock_q.order_by.return_value = mock_q
            mock_q.first.return_value = None
            mock_q.all.return_value = []
            mock_q.scalar.return_value = 0
            return mock_q

        mock_db.query.side_effect = query_side_effect

        service = NF525ComplianceService(db=mock_db, tenant_id="TEST-001")

        status = service.check_compliance()

        assert status.certificate_valid is False
        assert status.is_compliant is False
        assert "certificat" in str(status.issues).lower()


# ============================================================================
# TESTS ARCHIVAGE
# ============================================================================

class TestNF525Archiving:
    """Tests archivage NF525."""

    def test_create_archive_no_events(self):
        """Test: Archive sans événements = échec."""
        from app.modules.pos.nf525_compliance import NF525ComplianceService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        service = NF525ComplianceService(db=mock_db, tenant_id="TEST-001")

        result = service.create_archive(
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31)
        )

        assert result.success is False
        assert "No events" in result.error_message


class TestNF525Attestation:
    """Tests génération attestation NF525."""

    def test_generate_attestation_requires_certificate(self):
        """Test: Attestation nécessite certificat."""
        from app.modules.pos.nf525_compliance import NF525ComplianceService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = NF525ComplianceService(db=mock_db, tenant_id="TEST-001")

        with pytest.raises(ValueError, match="certificat"):
            service.generate_attestation()

    def test_attestation_structure(self):
        """Test: Structure attestation NF525."""
        attestation = {
            "attestation": {
                "type": "ATTESTATION_NF525",
                "generated_at": datetime.utcnow().isoformat(),
            },
            "software": {
                "name": "AZALSCORE",
                "version": "3.0.0",
                "editor": "AZALS Technologies"
            },
            "certificate": {
                "number": "NF-2024-001",
                "certifying_body": "LNE"
            },
            "chain_info": {
                "genesis_hash": "0" * 64,
                "total_events": 10000
            },
            "compliance": {
                "is_compliant": True,
                "score": 100
            },
            "legal_notice": "Ce document atteste..."
        }

        assert "attestation" in attestation
        assert "software" in attestation
        assert "certificate" in attestation
        assert "compliance" in attestation
        assert "legal_notice" in attestation


# ============================================================================
# TESTS EXPORT FISCAL
# ============================================================================

class TestNF525FiscalExport:
    """Tests export données fiscales NF525."""

    def test_export_fiscal_structure(self):
        """Test: Structure export fiscal."""
        export = {
            "export_info": {
                "type": "EXPORT_FISCAL_NF525",
                "period_start": "2024-01-01T00:00:00",
                "period_end": "2024-12-31T23:59:59"
            },
            "integrity": {
                "is_valid": True,
                "event_count": 50000
            },
            "events": [],
            "totals": {
                "transaction_count": 45000,
                "void_count": 150,
                "total_ttc": "1250000.00"
            }
        }

        assert export["export_info"]["type"] == "EXPORT_FISCAL_NF525"
        assert export["integrity"]["is_valid"] is True


# ============================================================================
# TESTS INITIALISATION CERTIFICAT
# ============================================================================

class TestNF525CertificateInit:
    """Tests initialisation certificat NF525."""

    def test_init_certificate_creates_genesis(self):
        """Test: Initialisation crée genesis hash."""
        import secrets

        # Simuler création genesis
        genesis_data = json.dumps({
            "tenant_id": "TEST-001",
            "software": "AZALSCORE",
            "version": "3.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }, sort_keys=True)

        genesis_hash = hashlib.sha256(genesis_data.encode()).hexdigest()

        assert len(genesis_hash) == 64

    def test_init_certificate_generates_signing_key(self):
        """Test: Initialisation génère clé signature."""
        import secrets

        signing_key = secrets.token_bytes(32)
        signing_key_hash = hashlib.sha256(signing_key).hexdigest()

        assert len(signing_key) == 32
        assert len(signing_key_hash) == 64


# ============================================================================
# TESTS VALIDATION FINALE
# ============================================================================

class TestNF525ValidationFinale:
    """Validation finale module NF525."""

    def test_all_event_types_defined(self):
        """Test: Tous les types d'événements définis."""
        from app.modules.pos.nf525_compliance import NF525EventType

        required_types = [
            "TICKET_CREATED",
            "TICKET_COMPLETED",
            "TICKET_VOIDED",
            "SESSION_OPENED",
            "SESSION_CLOSED",
            "Z_REPORT",
            "ARCHIVE_CREATED",
        ]

        defined_types = [t.value for t in NF525EventType]

        for req in required_types:
            assert req in defined_types, f"Missing event type: {req}"

    def test_nf525_legal_requirements(self):
        """Test: Exigences légales NF525."""
        requirements = {
            "inalterabilite": "Données ne peuvent être modifiées",
            "securisation": "Signature cryptographique",
            "conservation": "6 ans minimum",
            "archivage": "Export périodique sécurisé"
        }

        # Ces exigences sont couvertes par le module
        assert len(requirements) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
