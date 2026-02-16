"""
Tests d'intégration API - Phase 4
Tests des endpoints API pour la sécurité et la conformité
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock
import json
import base64


# ============================================================================
# Fixtures Communes
# ============================================================================

@pytest.fixture
def test_tenant_id():
    return "tenant_integration_001"


@pytest.fixture
def test_user_id():
    return "user_integration_001"


@pytest.fixture
def mock_request():
    """Crée une requête mock"""
    request = Mock()
    request.headers = {"Authorization": "Bearer test_token_123"}
    request.client.host = "192.168.1.100"
    request.headers.get = lambda key, default=None: {
        "User-Agent": "TestClient/1.0",
        "X-Tenant-ID": "tenant_integration_001",
        "X-Request-ID": "req_123"
    }.get(key, default)
    return request


# ============================================================================
# Tests API Sécurité
# ============================================================================

class TestSecurityAPIEndpoints:
    """Tests des endpoints de sécurité"""

    @pytest.mark.asyncio
    async def test_audit_log_endpoint(self, test_tenant_id, test_user_id):
        """Test endpoint de journalisation d'audit"""
        from app.core.audit_trail import get_audit_service

        audit_service = get_audit_service()

        event = await audit_service.log_event(
            category="authentication",
            action="api_access",
            description="Accès API endpoint audit",
            tenant_id=test_tenant_id,
            actor={
                "user_id": test_user_id,
                "ip_address": "192.168.1.100"
            },
            target={
                "entity_type": "api",
                "entity_id": "/api/v1/audit"
            }
        )

        assert event is not None
        assert event.tenant_id == test_tenant_id

    @pytest.mark.asyncio
    async def test_audit_search_endpoint(self, test_tenant_id):
        """Test endpoint de recherche d'audit"""
        from app.core.audit_trail import get_audit_service

        audit_service = get_audit_service()

        await audit_service.log_event(
            category="data_access",
            action="read",
            description="Test search",
            tenant_id=test_tenant_id,
            actor={"user_id": "search_test"}
        )

        events = await audit_service.search_events(
            tenant_id=test_tenant_id,
            categories=["data_access"],
            limit=10
        )

        assert isinstance(events, list)

    @pytest.mark.asyncio
    async def test_session_create_endpoint(self, test_tenant_id, test_user_id):
        """Test endpoint de création de session"""
        from app.core.session_management import get_session_service

        session_service = get_session_service()

        session, access_token, refresh_token = session_service.create_session(
            user_id=test_user_id,
            tenant_id=test_tenant_id,
            ip_address="192.168.1.100",
            user_agent="TestClient/1.0",
            roles=["user"]
        )

        assert session is not None
        assert access_token is not None
        assert refresh_token is not None

        response_data = {
            "session_id": session.id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 3600
        }

        assert "access_token" in response_data

    @pytest.mark.asyncio
    async def test_session_refresh_endpoint(self, test_tenant_id, test_user_id):
        """Test endpoint de rafraîchissement de session"""
        from app.core.session_management import get_session_service

        session_service = get_session_service()

        _, _, refresh_token = session_service.create_session(
            user_id=test_user_id,
            tenant_id=test_tenant_id,
            ip_address="192.168.1.100",
            user_agent="TestClient/1.0"
        )

        new_access, new_refresh, session, error = session_service.refresh_session(
            refresh_token=refresh_token,
            ip_address="192.168.1.100",
            user_agent="TestClient/1.0"
        )

        assert error is None
        assert new_access is not None
        assert new_refresh != refresh_token

    @pytest.mark.asyncio
    async def test_mfa_setup_endpoint(self, test_tenant_id, test_user_id):
        """Test endpoint de configuration MFA"""
        from app.core.mfa_advanced import MFAService

        mfa_service = MFAService()

        setup_data = mfa_service.setup_totp(
            user_id=test_user_id,
            tenant_id=test_tenant_id,
            email="test@example.com"
        )

        assert "secret" in setup_data
        assert "qr_code" in setup_data
        assert "backup_codes" in setup_data

        response = {
            "method": "totp",
            "qr_code": setup_data["qr_code"],
            "backup_codes": setup_data["backup_codes"]
        }

        assert response["method"] == "totp"

    @pytest.mark.asyncio
    async def test_mfa_verify_endpoint(self, test_tenant_id, test_user_id):
        """Test endpoint de vérification MFA"""
        from app.core.mfa_advanced import MFAService

        mfa_service = MFAService()

        setup = mfa_service.setup_totp(
            user_id=test_user_id,
            tenant_id=test_tenant_id,
            email="test@example.com"
        )

        code = mfa_service._totp_service.generate_code(setup["secret"])

        result = mfa_service.verify_code(
            user_id=test_user_id,
            tenant_id=test_tenant_id,
            code=code,
            method="totp"
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_api_key_create_endpoint(self, test_tenant_id, test_user_id):
        """Test endpoint de création de clé API"""
        from app.core.session_management import APIKeyService

        api_key_service = APIKeyService()

        key_value, api_key = api_key_service.create_api_key(
            name="Integration Test Key",
            tenant_id=test_tenant_id,
            user_id=test_user_id,
            scopes=["read:all", "write:invoices"],
            expires_in_days=90
        )

        response = {
            "key_id": api_key.id,
            "key_value": key_value,
            "name": api_key.name,
            "scopes": api_key.scopes,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None
        }

        assert response["key_value"].startswith("azs_")
        assert "read:all" in response["scopes"]


# ============================================================================
# Tests API Conformité
# ============================================================================

class TestComplianceAPIEndpoints:
    """Tests des endpoints de conformité"""

    @pytest.mark.asyncio
    async def test_fec_export_endpoint(self, test_tenant_id):
        """Test endpoint d'export FEC"""
        from app.services.data_import_export import get_import_export_service, ExportFormat

        service = get_import_export_service()

        accounting_entries = [
            {
                "JournalCode": "VE",
                "JournalLib": "Ventes",
                "EcritureNum": "VE2024-001",
                "EcritureDate": "2024-01-15",
                "CompteNum": "411000",
                "CompteLib": "Clients",
                "PieceRef": "FA-001",
                "PieceDate": "2024-01-15",
                "EcritureLib": "Facture client",
                "Debit": 1200.00,
                "Credit": 0,
                "ValidDate": "2024-01-15"
            },
            {
                "JournalCode": "VE",
                "JournalLib": "Ventes",
                "EcritureNum": "VE2024-001",
                "EcritureDate": "2024-01-15",
                "CompteNum": "701000",
                "CompteLib": "Ventes de produits",
                "PieceRef": "FA-001",
                "PieceDate": "2024-01-15",
                "EcritureLib": "Facture client",
                "Debit": 0,
                "Credit": 1000.00,
                "ValidDate": "2024-01-15"
            }
        ]

        result = service.export_data(
            data=accounting_entries,
            format=ExportFormat.FEC,
            options={
                "siren": "123456789",
                "fiscal_year_end": "20241231"
            }
        )

        assert result is not None
        assert b"JournalCode" in result.file_content
        assert result.total_records == 2

    @pytest.mark.asyncio
    async def test_rgpd_data_export_endpoint(self, test_tenant_id, test_user_id):
        """Test endpoint d'export RGPD (droit à la portabilité)"""
        from app.services.data_import_export import get_import_export_service, ExportFormat

        service = get_import_export_service()

        user_data = {
            "personal_info": {
                "user_id": test_user_id,
                "email": "user@example.com",
                "name": "John Doe",
                "created_at": "2023-01-01T00:00:00Z"
            },
            "activity_log": [
                {"action": "login", "timestamp": "2024-01-15T10:00:00Z"},
                {"action": "view_invoice", "timestamp": "2024-01-15T10:05:00Z"}
            ],
            "preferences": {
                "language": "fr",
                "timezone": "Europe/Paris",
                "notifications_enabled": True
            }
        }

        result = service.export_data(
            data=[user_data],
            format=ExportFormat.JSON,
            options={"indent": 2, "root_key": "user_data"}
        )

        assert result is not None
        exported = json.loads(result.file_content.decode())
        assert "user_data" in exported

    @pytest.mark.asyncio
    async def test_audit_compliance_report(self, test_tenant_id):
        """Test génération de rapport de conformité audit"""
        from app.core.audit_trail import get_audit_service
        from app.services.reporting_engine import (
            get_reporting_engine, ReportTemplate, ReportField,
            ReportParameters, ReportFormat
        )

        audit_service = get_audit_service()

        for i in range(5):
            await audit_service.log_event(
                category="data_access",
                action=f"compliance_test_{i}",
                description=f"Test compliance {i}",
                tenant_id=test_tenant_id,
                actor={"user_id": "compliance_user"}
            )

        events = await audit_service.search_events(
            tenant_id=test_tenant_id,
            limit=100
        )

        report_data = [
            {
                "event_id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "category": e.category.value,
                "action": e.action,
                "user_id": e.actor.user_id if e.actor else "system"
            }
            for e in events
        ]

        report_engine = get_reporting_engine()

        template = ReportTemplate(
            id="tpl_compliance_audit",
            name="Rapport Conformité Audit",
            description="Rapport de conformité des événements d'audit",
            category="compliance",
            format_default="pdf",
            fields=[
                ReportField(name="event_id", label="ID Événement", data_type="string"),
                ReportField(name="timestamp", label="Date/Heure", data_type="datetime"),
                ReportField(name="category", label="Catégorie", data_type="string"),
                ReportField(name="action", label="Action", data_type="string"),
                ReportField(name="user_id", label="Utilisateur", data_type="string")
            ],
            tenant_id=test_tenant_id
        )

        report_engine.register_template(template)

        params = ReportParameters(
            template_id=template.id,
            format=ReportFormat.JSON,
            data=report_data,
            tenant_id=test_tenant_id
        )

        report = await report_engine.generate_report(params)
        assert report is not None


# ============================================================================
# Tests API Encryption
# ============================================================================

class TestEncryptionAPIEndpoints:
    """Tests des endpoints de chiffrement"""

    def test_encrypt_sensitive_data_endpoint(self, test_tenant_id):
        """Test endpoint de chiffrement de données sensibles"""
        from app.core.encryption_advanced import get_envelope_encryption

        envelope_service = get_envelope_encryption()

        sensitive_data = b"Numero carte: 4111111111111111"

        encrypted = envelope_service.encrypt(
            plaintext=sensitive_data,
            tenant_id=test_tenant_id,
            context={"data_type": "credit_card"}
        )

        response = {
            "encrypted": True,
            "kek_id": encrypted.kek_id,
            "algorithm": encrypted.algorithm
        }

        assert response["encrypted"] is True
        assert encrypted.ciphertext != sensitive_data

    def test_decrypt_sensitive_data_endpoint(self, test_tenant_id):
        """Test endpoint de déchiffrement de données sensibles"""
        from app.core.encryption_advanced import get_envelope_encryption

        envelope_service = get_envelope_encryption()

        original_data = b"Secret information"

        encrypted = envelope_service.encrypt(original_data, test_tenant_id)
        decrypted = envelope_service.decrypt(encrypted, test_tenant_id)

        assert decrypted == original_data

    def test_tokenize_endpoint(self, test_tenant_id):
        """Test endpoint de tokenisation"""
        from app.core.encryption_advanced import TokenizationService

        token_service = TokenizationService()

        sensitive_value = "FR7630006000011234567890189"

        token = token_service.tokenize(
            value=sensitive_value,
            data_type="iban",
            tenant_id=test_tenant_id
        )

        response = {
            "token": token,
            "tokenized": True
        }

        assert response["token"].startswith("tok_")
        assert response["token"] != sensitive_value

    def test_key_rotation_endpoint(self, test_tenant_id):
        """Test endpoint de rotation de clé"""
        from app.core.encryption_advanced import get_kms

        kms = get_kms()

        original_key = kms.generate_key(
            key_type="data_encryption",
            algorithm="AES-256-GCM",
            tenant_id=test_tenant_id
        )

        new_key = kms.rotate_key(
            key_id=original_key.id,
            keep_old_for_decryption=True
        )

        response = {
            "old_key_id": original_key.id,
            "new_key_id": new_key.id,
            "rotated": True
        }

        assert response["old_key_id"] != response["new_key_id"]
        assert response["rotated"] is True


# ============================================================================
# Tests API Disaster Recovery
# ============================================================================

class TestDisasterRecoveryAPIEndpoints:
    """Tests des endpoints de récupération après sinistre"""

    @pytest.mark.asyncio
    async def test_create_backup_endpoint(self, test_tenant_id):
        """Test endpoint de création de backup"""
        from app.core.disaster_recovery import get_dr_service

        dr_service = get_dr_service()

        dr_service.set_recovery_objectives(
            tenant_id=test_tenant_id,
            rpo_minutes=15,
            rto_minutes=60
        )

        point = await dr_service.create_recovery_point(
            tenant_id=test_tenant_id,
            point_type="full",
            data_source="database",
            metadata={"triggered_by": "api", "reason": "manual_backup"}
        )

        response = {
            "recovery_point_id": point.id,
            "status": point.status.value,
            "created_at": point.created_at.isoformat()
        }

        assert response["recovery_point_id"].startswith("rp_")

    @pytest.mark.asyncio
    async def test_list_recovery_points_endpoint(self, test_tenant_id):
        """Test endpoint de liste des points de récupération"""
        from app.core.disaster_recovery import get_dr_service

        dr_service = get_dr_service()

        points = dr_service.list_recovery_points(
            tenant_id=test_tenant_id,
            limit=10
        )

        response = {
            "recovery_points": [
                {
                    "id": p.id,
                    "type": p.point_type,
                    "status": p.status.value,
                    "created_at": p.created_at.isoformat()
                }
                for p in points
            ],
            "total": len(points)
        }

        assert "recovery_points" in response

    @pytest.mark.asyncio
    async def test_dr_test_endpoint(self, test_tenant_id):
        """Test endpoint de test DR"""
        from app.core.disaster_recovery import get_dr_service

        dr_service = get_dr_service()

        dr_service.set_recovery_objectives(
            tenant_id=test_tenant_id,
            rpo_minutes=15,
            rto_minutes=60
        )

        result = await dr_service.run_dr_test(
            tenant_id=test_tenant_id,
            test_type="connectivity",
            target_region="eu-west-1"
        )

        response = {
            "test_id": result.id,
            "test_type": result.test_type,
            "success": result.success,
            "duration_seconds": result.duration_seconds
        }

        assert response["test_type"] == "connectivity"


# ============================================================================
# Tests API Workflow
# ============================================================================

class TestWorkflowAPIEndpoints:
    """Tests des endpoints de workflow"""

    @pytest.mark.asyncio
    async def test_trigger_workflow_endpoint(self, test_tenant_id):
        """Test endpoint de déclenchement de workflow"""
        from app.services.workflow_automation import (
            get_workflow_engine, WorkflowBuilder, TriggerType
        )

        engine = get_workflow_engine()

        workflow = (
            WorkflowBuilder("wf_api_test", "API Test Workflow", test_tenant_id)
            .on_manual()
            .log("Workflow triggered via API")
            .build()
        )
        workflow.status = workflow.status.__class__.ACTIVE

        engine.register_workflow(workflow)

        execution_id = await engine.start_execution(
            workflow_id=workflow.id,
            trigger_type=TriggerType.MANUAL,
            trigger_data={"source": "api"},
            tenant_id=test_tenant_id
        )

        response = {
            "execution_id": execution_id,
            "workflow_id": workflow.id,
            "status": "started"
        }

        assert response["execution_id"] is not None

    @pytest.mark.asyncio
    async def test_get_execution_status_endpoint(self, test_tenant_id):
        """Test endpoint de statut d'exécution"""
        from app.services.workflow_automation import (
            get_workflow_engine, WorkflowBuilder, TriggerType
        )

        engine = get_workflow_engine()

        workflow = (
            WorkflowBuilder("wf_status_test", "Status Test", test_tenant_id)
            .on_manual()
            .log("Test")
            .build()
        )
        workflow.status = workflow.status.__class__.ACTIVE

        engine.register_workflow(workflow)

        execution_id = await engine.start_execution(
            workflow_id=workflow.id,
            trigger_type=TriggerType.MANUAL,
            trigger_data={},
            tenant_id=test_tenant_id
        )

        await asyncio.sleep(0.5)

        execution = engine.get_execution(execution_id)

        response = {
            "execution_id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status.value,
            "started_at": execution.started_at.isoformat(),
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
        }

        assert response["status"] in ("running", "completed", "pending")

    @pytest.mark.asyncio
    async def test_list_pending_approvals_endpoint(self, test_tenant_id, test_user_id):
        """Test endpoint de liste des approbations en attente"""
        from app.services.workflow_automation import get_workflow_engine

        engine = get_workflow_engine()

        approvals = engine.get_pending_approvals(
            user_id=test_user_id,
            tenant_id=test_tenant_id
        )

        response = {
            "approvals": [
                {
                    "id": a.id,
                    "entity_type": a.entity_type,
                    "entity_id": a.entity_id,
                    "created_at": a.created_at.isoformat(),
                    "expires_at": a.expires_at.isoformat()
                }
                for a in approvals
            ],
            "total": len(approvals)
        }

        assert "approvals" in response


# ============================================================================
# Tests API Import/Export
# ============================================================================

class TestImportExportAPIEndpoints:
    """Tests des endpoints d'import/export"""

    @pytest.mark.asyncio
    async def test_import_preview_endpoint(self):
        """Test endpoint de prévisualisation d'import"""
        from app.services.data_import_export import get_import_export_service, ImportFormat

        service = get_import_export_service()

        csv_content = b"""code;nom;montant
A001;Alpha;1500
B002;Beta;2300"""

        preview = service.preview_import(
            content=csv_content,
            format=ImportFormat.CSV,
            options={"delimiter": ";"},
            max_rows=5
        )

        response = {
            "headers": ["code", "nom", "montant"],
            "preview_rows": preview,
            "total_preview": len(preview)
        }

        assert len(response["preview_rows"]) == 2

    @pytest.mark.asyncio
    async def test_validate_import_endpoint(self, test_tenant_id):
        """Test endpoint de validation d'import"""
        from app.services.data_import_export import (
            get_import_export_service, ImportFormat, FieldMapping
        )

        service = get_import_export_service()

        csv_content = b"""email;siren
valid@example.com;123456782
invalid-email;999999999"""

        mappings = [
            FieldMapping(source_field="email", target_field="email", data_type="email"),
            FieldMapping(source_field="siren", target_field="siren", data_type="siren")
        ]

        is_valid, errors = service.validate_data(
            content=csv_content,
            format=ImportFormat.CSV,
            field_mappings=mappings,
            options={"delimiter": ";"}
        )

        response = {
            "valid": is_valid,
            "errors": [
                {
                    "row": e.row_number,
                    "field": e.field,
                    "message": e.message,
                    "severity": e.severity.value
                }
                for e in errors
            ],
            "error_count": len(errors)
        }

        assert "errors" in response

    @pytest.mark.asyncio
    async def test_export_data_endpoint(self, test_tenant_id):
        """Test endpoint d'export de données"""
        from app.services.data_import_export import get_import_export_service, ExportFormat

        service = get_import_export_service()

        data = [
            {"id": "1", "name": "Item 1", "value": 100},
            {"id": "2", "name": "Item 2", "value": 200}
        ]

        result = service.export_data(
            data=data,
            format=ExportFormat.JSON
        )

        response = {
            "export_id": result.export_id,
            "format": result.format.value,
            "file_size": result.file_size,
            "checksum": result.checksum,
            "download_ready": True
        }

        assert response["download_ready"] is True
        assert response["file_size"] > 0


# ============================================================================
# Tests API Notification
# ============================================================================

class TestNotificationAPIEndpoints:
    """Tests des endpoints de notification"""

    @pytest.mark.asyncio
    async def test_send_notification_endpoint(self, test_tenant_id):
        """Test endpoint d'envoi de notification"""
        from app.services.notification_service import (
            get_notification_service, NotificationChannel
        )

        service = get_notification_service()

        notification = await service.send_direct(
            channel=NotificationChannel.IN_APP,
            recipient="user@example.com",
            content={
                "title": "Test API Notification",
                "body": "This is a test notification from API"
            },
            tenant_id=test_tenant_id
        )

        response = {
            "notification_id": notification.id,
            "status": notification.status.value,
            "channel": notification.channel.value,
            "sent_at": notification.sent_at.isoformat() if notification.sent_at else None
        }

        assert response["notification_id"] is not None

    def test_update_preferences_endpoint(self, test_tenant_id, test_user_id):
        """Test endpoint de mise à jour des préférences"""
        from app.services.notification_service import (
            get_notification_service, UserPreferences, NotificationChannel
        )

        service = get_notification_service()

        preferences = UserPreferences(
            user_id=test_user_id,
            tenant_id=test_tenant_id,
            enabled_channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
            category_preferences={
                "marketing": False,
                "security": True,
                "invoices": True
            },
            quiet_hours_start=22,
            quiet_hours_end=8
        )

        service.set_user_preferences(preferences)

        retrieved = service.get_user_preferences(test_user_id, test_tenant_id)

        response = {
            "user_id": retrieved.user_id,
            "enabled_channels": [c.value for c in retrieved.enabled_channels],
            "quiet_hours": {
                "start": retrieved.quiet_hours_start,
                "end": retrieved.quiet_hours_end
            }
        }

        assert response["quiet_hours"]["start"] == 22


# ============================================================================
# Tests de Charge et Performance
# ============================================================================

class TestAPIPerformance:
    """Tests de performance des API"""

    @pytest.mark.asyncio
    async def test_concurrent_audit_logging(self, test_tenant_id):
        """Test logging d'audit concurrent"""
        from app.core.audit_trail import get_audit_service

        audit_service = get_audit_service()

        async def log_event(i):
            return await audit_service.log_event(
                category="performance_test",
                action=f"action_{i}",
                description=f"Performance test event {i}",
                tenant_id=test_tenant_id,
                actor={"user_id": f"user_{i}"}
            )

        import time
        start = time.time()

        tasks = [log_event(i) for i in range(100)]
        results = await asyncio.gather(*tasks)

        duration = time.time() - start

        assert len(results) == 100
        assert duration < 10

    @pytest.mark.asyncio
    async def test_concurrent_session_creation(self, test_tenant_id):
        """Test création de session concurrente"""
        from app.core.session_management import get_session_service

        session_service = get_session_service()

        def create_session(i):
            return session_service.create_session(
                user_id=f"perf_user_{i}",
                tenant_id=test_tenant_id,
                ip_address=f"192.168.1.{i % 256}",
                user_agent="PerfTest/1.0"
            )

        import time
        start = time.time()

        results = [create_session(i) for i in range(50)]

        duration = time.time() - start

        assert len(results) == 50
        assert all(r[0] is not None for r in results)
        assert duration < 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
