"""
Tests unitaires pour les services de sécurité - Phase 2
Tests pour audit_trail, encryption_advanced, mfa_advanced, session_management, disaster_recovery
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock
import hashlib
import json
import base64


# ============================================================================
# Tests Audit Trail
# ============================================================================

class TestAuditTrailService:
    """Tests pour le service d'audit trail"""

    @pytest.fixture
    def audit_service(self):
        from app.core.audit_trail import AuditTrailService, get_audit_service
        return get_audit_service()

    @pytest.fixture
    def sample_event_data(self):
        from app.core.audit_trail import AuditEventCategory
        return {
            "category": AuditEventCategory.AUTHENTICATION,
            "action": "login_success",
            "description": "Connexion réussie",
            "tenant_id": "tenant_001",
            "actor": {
                "user_id": "user_123",
                "email": "test@example.com",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0"
            },
            "target": {
                "entity_type": "user",
                "entity_id": "user_123"
            },
            "context": {
                "login_method": "password"
            }
        }

    @pytest.mark.asyncio
    async def test_log_event_creates_event(self, audit_service, sample_event_data):
        """Test création d'un événement d'audit"""
        event = await audit_service.log_event(**sample_event_data)

        assert event is not None
        assert event.id is not None
        assert event.category.value == "authentication"
        assert event.action == sample_event_data["action"]
        assert event.tenant_id == sample_event_data["tenant_id"]
        assert event.hash_chain is not None

    @pytest.mark.asyncio
    async def test_log_event_generates_hash_chain(self, audit_service, sample_event_data):
        """Test que les événements sont chaînés par hash"""
        event1 = await audit_service.log_event(**sample_event_data)

        sample_event_data["action"] = "login_failure"
        event2 = await audit_service.log_event(**sample_event_data)

        assert event1.hash_chain != event2.hash_chain
        assert event2.previous_hash == event1.hash_chain

    @pytest.mark.asyncio
    async def test_verify_chain_integrity_valid(self, audit_service, sample_event_data):
        """Test vérification d'intégrité de chaîne valide"""
        from app.core.audit_trail import AuditEventCategory

        events = []
        for i in range(5):
            sample_event_data["action"] = f"action_{i}"
            event = await audit_service.log_event(**sample_event_data)
            events.append(event)

        is_valid, errors = audit_service.verify_chain_integrity(
            tenant_id=sample_event_data["tenant_id"],
            category=AuditEventCategory.AUTHENTICATION,
            events=events
        )

        assert is_valid is True
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_search_events_by_category(self, audit_service, sample_event_data):
        """Test recherche d'événements par catégorie"""
        await audit_service.log_event(**sample_event_data)

        events = await audit_service.search_events(
            tenant_id=sample_event_data["tenant_id"],
            categories=[sample_event_data["category"]]
        )

        assert len(events) >= 1
        assert all(e.category.value == "authentication" for e in events)


class TestThreatDetectionEngine:
    """Tests pour le moteur de détection des menaces"""

    @pytest.fixture
    def threat_engine(self):
        from app.core.audit_trail import ThreatDetectionEngine
        return ThreatDetectionEngine()

    @pytest.fixture
    def login_failure_event(self):
        from app.core.audit_trail import AuditEvent, AuditEventCategory, AuditEventSeverity, AuditEventOutcome, AuditActor
        return AuditEvent(
            id="evt_001",
            timestamp=datetime.utcnow(),
            category=AuditEventCategory.AUTHENTICATION,
            action="login_failure",
            description="Échec de connexion",
            tenant_id="tenant_001",
            actor=AuditActor(
                user_id="user_123",
                ip_address="192.168.1.100"
            ),
            outcome=AuditEventOutcome.FAILURE,
            severity=AuditEventSeverity.WARNING,
            hash_chain="abc123"
        )

    @pytest.mark.asyncio
    async def test_detect_brute_force_attack(self, threat_engine, login_failure_event):
        """Test détection d'attaque par force brute"""
        for _ in range(10):
            await threat_engine.analyze_event(login_failure_event)

        alerts = threat_engine.get_recent_alerts(tenant_id="tenant_001")
        brute_force_alerts = [a for a in alerts if a.alert_type == "brute_force_login"]

        assert len(brute_force_alerts) >= 1


class TestSIEMExporter:
    """Tests pour les exporteurs SIEM"""

    @pytest.fixture
    def sample_audit_event(self):
        from app.core.audit_trail import AuditEvent, AuditEventCategory, AuditEventSeverity, AuditActor
        return AuditEvent(
            id="evt_001",
            timestamp=datetime.utcnow(),
            category=AuditEventCategory.DATA_ACCESS,
            action="read",
            description="Lecture de données",
            tenant_id="tenant_001",
            actor=AuditActor(user_id="user_123", ip_address="10.0.0.1"),
            severity=AuditEventSeverity.INFO,
            hash_chain="hash123"
        )

    def test_splunk_exporter_formats_event(self, sample_audit_event):
        """Test formatage pour Splunk HEC"""
        from app.core.audit_trail import SplunkExporter

        exporter = SplunkExporter(
            hec_url="https://splunk.example.com:8088",
            hec_token="test-token"
        )
        formatted = exporter.format_event(sample_audit_event)

        assert "time" in formatted
        assert "event" in formatted
        assert formatted["event"]["category"] == "data_access"

    def test_elasticsearch_exporter_formats_event(self, sample_audit_event):
        """Test formatage pour Elasticsearch"""
        from app.core.audit_trail import ElasticsearchExporter

        exporter = ElasticsearchExporter(
            hosts=["https://es.example.com:9200"],
            index_prefix="azalscore-audit"
        )
        formatted = exporter.format_event(sample_audit_event)

        assert "@timestamp" in formatted
        assert "_index" in formatted
        assert "tenant_id" in formatted

    def test_syslog_exporter_formats_rfc5424(self, sample_audit_event):
        """Test formatage Syslog RFC 5424"""
        from app.core.audit_trail import SyslogExporter

        exporter = SyslogExporter(host="syslog.example.com", port=514)
        formatted = exporter.format_event(sample_audit_event)

        assert formatted.startswith("<")
        assert "AZALSCORE" in formatted


# ============================================================================
# Tests Encryption Advanced
# ============================================================================

class TestKeyManagementService:
    """Tests pour le service de gestion des clés"""

    @pytest.fixture
    def kms(self):
        from app.core.encryption_advanced import KeyManagementService, get_kms
        return get_kms()

    def test_generate_aes_key(self, kms):
        """Test génération de clé AES"""
        key = kms.generate_key(
            key_type="data_encryption",
            algorithm="AES-256-GCM",
            tenant_id="tenant_001"
        )

        assert key is not None
        assert key.id.startswith("key_")
        assert key.algorithm == "AES-256-GCM"
        assert len(key.key_material) == 32  # 256 bits

    def test_generate_rsa_key_pair(self, kms):
        """Test génération de paire RSA"""
        key = kms.generate_key(
            key_type="key_encryption",
            algorithm="RSA-2048",
            tenant_id="tenant_001"
        )

        assert key is not None
        assert key.public_key is not None

    def test_rotate_key(self, kms):
        """Test rotation de clé"""
        original_key = kms.generate_key(
            key_type="data_encryption",
            algorithm="AES-256-GCM",
            tenant_id="tenant_001"
        )

        new_key = kms.rotate_key(original_key.id, keep_old_for_decryption=True)

        assert new_key.id != original_key.id
        assert original_key.rotated_to == new_key.id
        assert original_key.is_active is False

    def test_get_key_by_id(self, kms):
        """Test récupération de clé par ID"""
        key = kms.generate_key(
            key_type="data_encryption",
            algorithm="AES-256-GCM",
            tenant_id="tenant_001"
        )

        retrieved = kms.get_key(key.id)
        assert retrieved is not None
        assert retrieved.id == key.id


class TestEnvelopeEncryptionService:
    """Tests pour le chiffrement d'enveloppe"""

    @pytest.fixture
    def envelope_service(self):
        from app.core.encryption_advanced import EnvelopeEncryptionService, get_envelope_encryption
        return get_envelope_encryption()

    def test_encrypt_decrypt_roundtrip(self, envelope_service):
        """Test chiffrement/déchiffrement complet"""
        plaintext = b"Donnees confidentielles pour test"
        tenant_id = "tenant_001"

        encrypted = envelope_service.encrypt(plaintext, tenant_id)

        assert encrypted is not None
        assert encrypted.ciphertext != plaintext
        assert encrypted.encrypted_dek is not None
        assert encrypted.kek_id is not None

        decrypted = envelope_service.decrypt(encrypted, tenant_id)
        assert decrypted == plaintext

    def test_encrypt_with_context(self, envelope_service):
        """Test chiffrement avec contexte AAD"""
        plaintext = b"Donnees avec contexte"
        tenant_id = "tenant_001"
        context = {"document_type": "invoice", "document_id": "INV-001"}

        encrypted = envelope_service.encrypt(plaintext, tenant_id, context)

        decrypted = envelope_service.decrypt(encrypted, tenant_id)
        assert decrypted == plaintext


class TestTokenizationService:
    """Tests pour la tokenisation"""

    @pytest.fixture
    def tokenization_service(self):
        from app.core.encryption_advanced import TokenizationService, TokenizationType

        # Create a simple in-memory token store for testing
        class InMemoryTokenStore:
            def __init__(self):
                self._tokens = {}

            def store(self, token: str, data: dict) -> None:
                self._tokens[token] = data

            def retrieve(self, token: str) -> dict | None:
                return self._tokens.get(token)

            def delete(self, token: str) -> bool:
                if token in self._tokens:
                    del self._tokens[token]
                    return True
                return False

        return TokenizationService(
            token_store=InMemoryTokenStore(),
            secret_key=b"test-secret-key-for-tokenization"
        )

    def test_tokenize_credit_card(self, tokenization_service):
        """Test tokenisation carte bancaire"""
        from app.core.encryption_advanced import TokenizationType

        cc_number = "4111111111111111"

        token = tokenization_service.tokenize(
            value=cc_number,
            token_type=TokenizationType.CREDIT_CARD,
            tenant_id="tenant_001"
        )

        assert token is not None
        assert token != cc_number
        assert token.startswith("tok_")

    def test_detokenize_returns_original(self, tokenization_service):
        """Test détokenisation retourne valeur originale"""
        from app.core.encryption_advanced import TokenizationType

        original = "secret_value_123"

        token = tokenization_service.tokenize(
            value=original,
            token_type=TokenizationType.GENERIC,
            tenant_id="tenant_001"
        )

        retrieved = tokenization_service.detokenize(token, "tenant_001")
        assert retrieved == original

    def test_format_preserving_tokenization(self, tokenization_service):
        """Test tokenisation préservant le format"""
        from app.core.encryption_advanced import TokenizationType

        phone = "0612345678"

        token = tokenization_service.tokenize(
            value=phone,
            token_type=TokenizationType.PHONE,
            tenant_id="tenant_001",
            format_preserving=True
        )

        assert token.startswith("tok_")


# ============================================================================
# Tests MFA Advanced
# ============================================================================

class TestTOTPService:
    """Tests pour le service TOTP"""

    @pytest.fixture
    def totp_service(self):
        from app.core.mfa_advanced import TOTPService
        return TOTPService()

    def test_generate_secret(self, totp_service):
        """Test génération de secret TOTP"""
        secret = totp_service.generate_secret()

        assert secret is not None
        assert len(secret) == 32

    def test_generate_provisioning_uri(self, totp_service):
        """Test génération d'URI de provisioning"""
        secret = totp_service.generate_secret()
        uri = totp_service.generate_provisioning_uri(
            secret=secret,
            account_name="user@example.com",
            issuer="AZALSCORE"
        )

        assert uri.startswith("otpauth://totp/")
        assert "AZALSCORE" in uri
        assert "secret=" in uri

    def test_verify_valid_code(self, totp_service):
        """Test vérification de code valide"""
        secret = totp_service.generate_secret()
        code = totp_service.generate_code(secret)

        is_valid = totp_service.verify_code(secret, code)
        assert is_valid is True

    def test_verify_invalid_code(self, totp_service):
        """Test rejet de code invalide"""
        secret = totp_service.generate_secret()

        is_valid = totp_service.verify_code(secret, "000000")
        assert is_valid is False


class TestAdaptiveMFAService:
    """Tests pour le MFA adaptatif"""

    @pytest.fixture
    def adaptive_mfa(self):
        from app.core.mfa_advanced import AdaptiveMFAService
        return AdaptiveMFAService()

    def test_low_risk_score_for_known_context(self, adaptive_mfa):
        """Test score de risque bas pour contexte connu"""
        risk = adaptive_mfa.assess_risk(
            user_id="user_123",
            tenant_id="tenant_001",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0)",
            device_id="device_abc",
            geolocation={"country": "FR", "city": "Paris"}
        )

        assert risk.score <= 50
        assert risk.risk_level in ("low", "medium")

    def test_high_risk_for_new_device_and_location(self, adaptive_mfa):
        """Test score de risque élevé pour nouveau contexte"""
        adaptive_mfa.record_successful_auth(
            user_id="user_123",
            tenant_id="tenant_001",
            ip_address="192.168.1.100",
            geolocation={"country": "FR"}
        )

        risk = adaptive_mfa.assess_risk(
            user_id="user_123",
            tenant_id="tenant_001",
            ip_address="203.0.113.50",
            user_agent="Unknown Browser",
            device_id="new_device",
            geolocation={"country": "CN", "city": "Beijing"}
        )

        assert risk.score > 50


class TestDeviceTrustService:
    """Tests pour le service de confiance des appareils"""

    @pytest.fixture
    def device_trust(self):
        from app.core.mfa_advanced import DeviceTrustService
        return DeviceTrustService()

    def test_register_trusted_device(self, device_trust):
        """Test enregistrement d'un appareil de confiance"""
        device = device_trust.register_device(
            user_id="user_123",
            tenant_id="tenant_001",
            device_fingerprint="fp_abc123",
            device_name="Mon Ordinateur",
            user_agent="Mozilla/5.0"
        )

        assert device is not None
        assert device.is_trusted is True
        assert device.trust_level == "full"

    def test_verify_trusted_device(self, device_trust):
        """Test vérification d'un appareil de confiance"""
        device = device_trust.register_device(
            user_id="user_123",
            tenant_id="tenant_001",
            device_fingerprint="fp_xyz789",
            device_name="Téléphone"
        )

        is_trusted = device_trust.is_device_trusted(
            user_id="user_123",
            tenant_id="tenant_001",
            device_fingerprint="fp_xyz789"
        )

        assert is_trusted is True


# ============================================================================
# Tests Session Management
# ============================================================================

class TestSessionService:
    """Tests pour le service de gestion des sessions"""

    @pytest.fixture
    def session_service(self):
        from app.core.session_management import SessionService, get_session_service
        return get_session_service()

    def test_create_session(self, session_service):
        """Test création de session"""
        session, access_token, refresh_token = session_service.create_session(
            user_id="user_123",
            tenant_id="tenant_001",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            roles=["user", "admin"]
        )

        assert session is not None
        assert session.id.startswith("sess_")
        assert access_token is not None
        assert refresh_token is not None
        assert session.is_active is True

    def test_validate_session(self, session_service):
        """Test validation de session"""
        session, access_token, _ = session_service.create_session(
            user_id="user_123",
            tenant_id="tenant_001",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        )

        validated = session_service.validate_session(session.id)
        assert validated is not None
        assert validated.id == session.id

    def test_refresh_session(self, session_service):
        """Test rafraîchissement de session"""
        session, _, refresh_token = session_service.create_session(
            user_id="user_123",
            tenant_id="tenant_001",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        )

        new_access, new_refresh, updated_session, error = session_service.refresh_session(
            refresh_token=refresh_token,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        )

        assert error is None
        assert new_access is not None
        assert new_refresh is not None
        assert new_refresh != refresh_token

    def test_revoke_session(self, session_service):
        """Test révocation de session"""
        session, _, _ = session_service.create_session(
            user_id="user_123",
            tenant_id="tenant_001",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        )

        revoked = session_service.revoke_session(
            session_id=session.id,
            reason="user_logout"
        )

        assert revoked is True

        validated = session_service.validate_session(session.id)
        assert validated is None

    def test_concurrent_session_limit(self, session_service):
        """Test limite de sessions concurrentes"""
        user_id = "user_concurrent"
        tenant_id = "tenant_001"

        sessions = []
        for i in range(10):
            s, _, _ = session_service.create_session(
                user_id=user_id,
                tenant_id=tenant_id,
                ip_address=f"192.168.1.{i}",
                user_agent="Mozilla/5.0"
            )
            sessions.append(s)

        active_sessions = session_service.get_user_sessions(user_id, tenant_id)
        active_count = len([s for s in active_sessions if s.is_active])

        assert active_count <= session_service._max_sessions_per_user


class TestTokenService:
    """Tests pour le service de tokens"""

    @pytest.fixture
    def token_service(self):
        from app.core.session_management import TokenService
        return TokenService()

    def test_create_access_token(self, token_service):
        """Test création de token d'accès"""
        token, claims = token_service.create_access_token(
            user_id="user_123",
            tenant_id="tenant_001",
            session_id="sess_abc",
            roles=["user"]
        )

        assert token is not None
        assert claims.user_id == "user_123"
        assert claims.token_type == "access"

    def test_validate_access_token(self, token_service):
        """Test validation de token d'accès"""
        token, _ = token_service.create_access_token(
            user_id="user_123",
            tenant_id="tenant_001",
            session_id="sess_abc",
            roles=["user"]
        )

        claims = token_service.validate_access_token(token)
        assert claims is not None
        assert claims.user_id == "user_123"

    def test_token_rotation(self, token_service):
        """Test rotation de refresh token"""
        old_token, _ = token_service.create_refresh_token(
            user_id="user_123",
            tenant_id="tenant_001",
            session_id="sess_abc",
            device_id="device_123"
        )

        new_token, new_refresh, error = token_service.rotate_refresh_token(
            old_token=old_token,
            device_id="device_123"
        )

        assert error is None
        assert new_token is not None
        assert new_token != old_token


class TestAPIKeyService:
    """Tests pour le service de clés API"""

    @pytest.fixture
    def api_key_service(self):
        from app.core.session_management import APIKeyService
        return APIKeyService()

    def test_create_api_key(self, api_key_service):
        """Test création de clé API"""
        key_value, api_key = api_key_service.create_api_key(
            name="Test API Key",
            tenant_id="tenant_001",
            user_id="user_123",
            scopes=["read:invoices", "write:invoices"]
        )

        assert key_value is not None
        assert key_value.startswith("azs_")
        assert api_key.name == "Test API Key"
        assert "read:invoices" in api_key.scopes

    def test_validate_api_key(self, api_key_service):
        """Test validation de clé API"""
        key_value, _ = api_key_service.create_api_key(
            name="Validate Test",
            tenant_id="tenant_001",
            user_id="user_123"
        )

        api_key = api_key_service.validate_api_key(key_value)
        assert api_key is not None
        assert api_key.name == "Validate Test"

    def test_revoke_api_key(self, api_key_service):
        """Test révocation de clé API"""
        key_value, api_key = api_key_service.create_api_key(
            name="Revoke Test",
            tenant_id="tenant_001",
            user_id="user_123"
        )

        revoked = api_key_service.revoke_api_key(api_key.id, "user_123")
        assert revoked is True

        validated = api_key_service.validate_api_key(key_value)
        assert validated is None


# ============================================================================
# Tests Disaster Recovery
# ============================================================================

class TestDisasterRecoveryService:
    """Tests pour le service de récupération après sinistre"""

    @pytest.fixture
    def dr_service(self):
        from app.core.disaster_recovery import DisasterRecoveryService, get_dr_service
        return get_dr_service()

    def test_set_recovery_objectives(self, dr_service):
        """Test définition des objectifs de récupération"""
        objective = dr_service.set_recovery_objectives(
            tenant_id="tenant_001",
            rpo_minutes=15,
            rto_minutes=60,
            tier="gold"
        )

        assert objective is not None
        assert objective.rpo_minutes == 15
        assert objective.rto_minutes == 60
        assert objective.tier == "gold"

    @pytest.mark.asyncio
    async def test_create_recovery_point(self, dr_service):
        """Test création d'un point de récupération"""
        dr_service.set_recovery_objectives(
            tenant_id="tenant_001",
            rpo_minutes=15,
            rto_minutes=60
        )

        point = await dr_service.create_recovery_point(
            tenant_id="tenant_001",
            point_type="full",
            data_source="database"
        )

        assert point is not None
        assert point.id.startswith("rp_")
        assert point.status.value in ("pending", "in_progress", "completed")

    def test_list_recovery_points(self, dr_service):
        """Test liste des points de récupération"""
        points = dr_service.list_recovery_points(
            tenant_id="tenant_001",
            limit=10
        )

        assert isinstance(points, list)

    @pytest.mark.asyncio
    async def test_run_dr_test(self, dr_service):
        """Test exécution d'un test DR"""
        dr_service.set_recovery_objectives(
            tenant_id="tenant_001",
            rpo_minutes=15,
            rto_minutes=60
        )

        result = await dr_service.run_dr_test(
            tenant_id="tenant_001",
            test_type="connectivity",
            target_region="eu-west-1"
        )

        assert result is not None
        assert result.test_type == "connectivity"
        assert result.success is not None


class TestReplicationService:
    """Tests pour le service de réplication"""

    @pytest.fixture
    def replication_service(self):
        from app.core.disaster_recovery import ReplicationService
        return ReplicationService()

    def test_configure_replication(self, replication_service):
        """Test configuration de la réplication"""
        config = replication_service.configure(
            tenant_id="tenant_001",
            source_region="eu-west-1",
            target_regions=["eu-central-1", "us-east-1"],
            mode="async"
        )

        assert config is not None
        assert "eu-central-1" in config.target_regions

    @pytest.mark.asyncio
    async def test_replicate_data(self, replication_service):
        """Test réplication de données"""
        replication_service.configure(
            tenant_id="tenant_001",
            source_region="eu-west-1",
            target_regions=["eu-central-1"],
            mode="async"
        )

        result = await replication_service.replicate(
            tenant_id="tenant_001",
            data={"table": "invoices", "records": 100}
        )

        assert result is not None


class TestPITRService:
    """Tests pour le service Point-In-Time Recovery"""

    @pytest.fixture
    def pitr_service(self):
        from app.core.disaster_recovery import PITRService
        return PITRService()

    def test_enable_pitr(self, pitr_service):
        """Test activation du PITR"""
        result = pitr_service.enable(
            tenant_id="tenant_001",
            retention_days=30
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_available_restore_points(self, pitr_service):
        """Test liste des points de restauration disponibles"""
        pitr_service.enable(tenant_id="tenant_001", retention_days=30)

        points = await pitr_service.get_available_points(
            tenant_id="tenant_001",
            start_time=datetime.utcnow() - timedelta(days=7),
            end_time=datetime.utcnow()
        )

        assert isinstance(points, list)


# ============================================================================
# Tests d'Intégration
# ============================================================================

class TestSecurityIntegration:
    """Tests d'intégration entre les services de sécurité"""

    @pytest.mark.asyncio
    async def test_full_authentication_flow_with_mfa(self):
        """Test flux complet d'authentification avec MFA"""
        from app.core.session_management import get_session_service
        from app.core.mfa_advanced import MFAService
        from app.core.audit_trail import get_audit_service

        session_service = get_session_service()
        mfa_service = MFAService()
        audit_service = get_audit_service()

        setup = mfa_service.setup_totp(
            user_id="user_integration",
            tenant_id="tenant_001",
            email="test@example.com"
        )

        assert "secret" in setup
        assert "qr_code" in setup

        code = mfa_service._totp_service.generate_code(setup["secret"])
        result = mfa_service.verify_code(
            user_id="user_integration",
            tenant_id="tenant_001",
            code=code,
            method="totp"
        )

        assert result.success is True

        session, access_token, refresh_token = session_service.create_session(
            user_id="user_integration",
            tenant_id="tenant_001",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            mfa_verified=True
        )

        assert session is not None
        assert access_token is not None

        await audit_service.log_event(
            category="authentication",
            action="mfa_login_success",
            description="Connexion avec MFA réussie",
            tenant_id="tenant_001",
            actor={"user_id": "user_integration", "ip_address": "192.168.1.100"}
        )

    @pytest.mark.asyncio
    async def test_encryption_with_audit_trail(self):
        """Test chiffrement avec journalisation d'audit"""
        from app.core.encryption_advanced import get_envelope_encryption
        from app.core.audit_trail import get_audit_service

        envelope_service = get_envelope_encryption()
        audit_service = get_audit_service()

        plaintext = b"Donnees sensibles"
        tenant_id = "tenant_001"

        encrypted = envelope_service.encrypt(plaintext, tenant_id)

        await audit_service.log_event(
            category="data_access",
            action="encrypt",
            description="Chiffrement de données sensibles",
            tenant_id=tenant_id,
            actor={"user_id": "system"},
            target={"entity_type": "encrypted_data", "entity_id": encrypted.kek_id}
        )

        decrypted = envelope_service.decrypt(encrypted, tenant_id)

        await audit_service.log_event(
            category="data_access",
            action="decrypt",
            description="Déchiffrement de données",
            tenant_id=tenant_id,
            actor={"user_id": "system"}
        )

        assert decrypted == plaintext


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
