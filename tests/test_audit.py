"""
AZALS MODULE T3 - Tests Audit & Benchmark
==========================================

Tests unitaires et d'intégration pour le module Audit.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import json

from app.modules.audit.models import (
    AuditLog, AuditSession, MetricDefinition, MetricValue,
    Benchmark, BenchmarkResult, ComplianceCheck, DataRetentionRule,
    AuditExport, AuditDashboard,
    AuditAction, AuditLevel, AuditCategory, MetricType,
    BenchmarkStatus, RetentionPolicy, ComplianceFramework
)
from app.modules.audit.service import AuditService, get_audit_service
from app.modules.audit.schemas import (
    AuditLogCreateSchema, AuditSearchSchema, MetricCreateSchema,
    BenchmarkCreateSchema, ComplianceCheckCreateSchema,
    RetentionRuleCreateSchema, ExportCreateSchema, DashboardCreateSchema
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock de la session DB."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    return db


@pytest.fixture
def audit_service(mock_db):
    """Service d'audit avec mock DB."""
    return AuditService(mock_db, "tenant_test")


@pytest.fixture
def sample_audit_log():
    """Log d'audit d'exemple."""
    return AuditLog(
        id=1,
        tenant_id="tenant_test",
        action=AuditAction.CREATE,
        level=AuditLevel.INFO,
        category=AuditCategory.BUSINESS,
        module="treasury",
        entity_type="forecast",
        entity_id="123",
        user_id=10,
        user_email="user@test.com",
        description="Création d'une prévision",
        success=True,
        created_at=datetime.utcnow()
    )


# ============================================================================
# TESTS SCHEMAS
# ============================================================================

class TestAuditSchemas:
    """Tests des schémas Pydantic."""

    def test_audit_log_create_valid(self):
        """Création valide d'un log."""
        data = AuditLogCreateSchema(
            action=AuditAction.CREATE,
            module="treasury",
            description="Test log"
        )
        assert data.action == AuditAction.CREATE
        assert data.level == AuditLevel.INFO

    def test_metric_create_valid(self):
        """Création valide d'une métrique."""
        data = MetricCreateSchema(
            code="API_RESPONSE",
            name="Temps de réponse API",
            metric_type=MetricType.TIMER,
            unit="ms"
        )
        assert data.code == "API_RESPONSE"
        assert data.metric_type == MetricType.TIMER

    def test_benchmark_create_valid(self):
        """Création valide d'un benchmark."""
        data = BenchmarkCreateSchema(
            code="PERF_TEST",
            name="Test de performance",
            benchmark_type="PERFORMANCE",
            config={"max_response_time": 100}
        )
        assert data.benchmark_type == "PERFORMANCE"

    def test_compliance_check_create_valid(self):
        """Création valide d'un contrôle."""
        data = ComplianceCheckCreateSchema(
            framework=ComplianceFramework.GDPR,
            control_id="GDPR-5.1",
            control_name="Consentement",
            check_type="MANUAL"
        )
        assert data.framework == ComplianceFramework.GDPR


# ============================================================================
# TESTS SERVICE - LOGGING
# ============================================================================

class TestAuditLogging:
    """Tests du logging d'audit."""

    def test_log_basic(self, audit_service, mock_db):
        """Log basique."""
        log = audit_service.log(
            action=AuditAction.CREATE,
            module="treasury",
            description="Test log"
        )

        mock_db.add.assert_called()

    def test_log_with_values(self, audit_service, mock_db):
        """Log avec anciennes/nouvelles valeurs."""
        old_value = {"balance": 1000}
        new_value = {"balance": 1500}

        log = audit_service.log(
            action=AuditAction.UPDATE,
            module="treasury",
            old_value=old_value,
            new_value=new_value
        )

        mock_db.add.assert_called()

    def test_calculate_diff(self, audit_service):
        """Calcul des différences."""
        old_value = {"name": "Test", "amount": 100}
        new_value = {"name": "Test Updated", "amount": 100, "status": "active"}

        diff = audit_service._calculate_diff(old_value, new_value)

        assert "added" in diff
        assert "changed" in diff
        assert "status" in diff["added"]
        assert "name" in diff["changed"]

    def test_calculate_expiration_short(self, audit_service):
        """Calcul expiration politique SHORT."""
        expires = audit_service._calculate_expiration(RetentionPolicy.SHORT)
        expected = datetime.utcnow() + timedelta(days=30)
        assert abs((expires - expected).total_seconds()) < 60

    def test_calculate_expiration_permanent(self, audit_service):
        """Pas d'expiration pour PERMANENT."""
        expires = audit_service._calculate_expiration(RetentionPolicy.PERMANENT)
        assert expires is None

    def test_search_logs(self, audit_service, mock_db):
        """Recherche de logs."""
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        logs, total = audit_service.search_logs(
            module="treasury",
            from_date=datetime.utcnow() - timedelta(days=1)
        )

        assert total == 0
        assert logs == []


# ============================================================================
# TESTS SERVICE - SESSIONS
# ============================================================================

class TestAuditSessions:
    """Tests de gestion des sessions."""

    def test_start_session(self, audit_service, mock_db):
        """Démarrage de session."""
        session = audit_service.start_session(
            session_id="sess_123",
            user_id=10,
            user_email="user@test.com",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0"
        )

        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_parse_user_agent(self, audit_service):
        """Parsing du user agent."""
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0"
        device, browser, os = audit_service._parse_user_agent(user_agent)

        assert device == "Desktop"
        assert browser == "Chrome"
        assert os == "Windows"

    def test_parse_user_agent_mobile(self, audit_service):
        """Parsing user agent mobile."""
        user_agent = "Mozilla/5.0 (Linux; Android 10; Mobile) Chrome/91.0"
        device, browser, os = audit_service._parse_user_agent(user_agent)

        assert device == "Mobile"
        assert os == "Android"

    def test_end_session(self, audit_service, mock_db):
        """Fin de session."""
        session = AuditSession(
            id=1,
            tenant_id="tenant_test",
            session_id="sess_123",
            user_id=10,
            is_active=True
        )
        mock_db.query.return_value.filter.return_value.first.return_value = session

        result = audit_service.end_session("sess_123", "logout")

        assert result.is_active is False
        assert result.terminated_reason == "logout"


# ============================================================================
# TESTS SERVICE - MÉTRIQUES
# ============================================================================

class TestMetrics:
    """Tests de gestion des métriques."""

    def test_create_metric(self, audit_service, mock_db):
        """Création de métrique."""
        metric = audit_service.create_metric(
            code="TEST_METRIC",
            name="Test Métrique",
            metric_type=MetricType.GAUGE,
            unit="%"
        )

        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_record_metric_new(self, audit_service, mock_db):
        """Enregistrement nouvelle valeur."""
        metric_def = MetricDefinition(
            id=1,
            tenant_id="tenant_test",
            code="TEST",
            name="Test",
            metric_type=MetricType.GAUGE,
            aggregation_period="HOUR"
        )
        mock_db.query.return_value.filter.return_value.first.side_effect = [metric_def, None]

        value = audit_service.record_metric("TEST", 50.0)

        mock_db.add.assert_called()

    def test_record_metric_update(self, audit_service, mock_db):
        """Mise à jour valeur existante."""
        metric_def = MetricDefinition(
            id=1,
            tenant_id="tenant_test",
            code="TEST",
            name="Test",
            metric_type=MetricType.GAUGE,
            aggregation_period="HOUR"
        )
        existing_value = MetricValue(
            id=1,
            metric_id=1,
            metric_code="TEST",
            value=40.0,
            avg_value=40.0,
            min_value=40.0,
            max_value=40.0,
            count=1,
            period_start=datetime.utcnow().replace(minute=0, second=0, microsecond=0),
            period_end=datetime.utcnow().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        )
        mock_db.query.return_value.filter.return_value.first.side_effect = [metric_def, existing_value]

        value = audit_service.record_metric("TEST", 60.0)

        assert value.count == 2
        assert value.max_value == 60.0


# ============================================================================
# TESTS SERVICE - BENCHMARKS
# ============================================================================

class TestBenchmarks:
    """Tests de gestion des benchmarks."""

    def test_create_benchmark(self, audit_service, mock_db):
        """Création de benchmark."""
        benchmark = audit_service.create_benchmark(
            code="PERF_TEST",
            name="Test Performance",
            benchmark_type="PERFORMANCE",
            config={"max_time": 100}
        )

        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_run_benchmark(self, audit_service, mock_db):
        """Exécution de benchmark."""
        benchmark = Benchmark(
            id=1,
            tenant_id="tenant_test",
            code="PERF_TEST",
            name="Test",
            benchmark_type="PERFORMANCE",
            status=BenchmarkStatus.PENDING,
            config='{"max_api_response_ms": 100}'
        )
        mock_db.query.return_value.filter.return_value.first.return_value = benchmark
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = audit_service.run_benchmark(1, executed_by=10)

        assert result.status == BenchmarkStatus.COMPLETED
        mock_db.commit.assert_called()

    def test_run_performance_benchmark(self, audit_service):
        """Benchmark de performance."""
        benchmark = Benchmark(
            benchmark_type="PERFORMANCE",
            config='{"max_api_response_ms": 100}'
        )
        config = {"max_api_response_ms": 100}
        baseline = {"max_api_response_ms": 100}

        score, details, warnings = audit_service._run_performance_benchmark(benchmark, config, baseline)

        assert score >= 0
        assert isinstance(details, dict)

    def test_run_security_benchmark(self, audit_service):
        """Benchmark de sécurité."""
        benchmark = Benchmark(benchmark_type="SECURITY")

        score, details, warnings = audit_service._run_security_benchmark(benchmark, {}, {})

        assert score == 100
        assert "jwt_enabled" in details


# ============================================================================
# TESTS SERVICE - CONFORMITÉ
# ============================================================================

class TestCompliance:
    """Tests de gestion de la conformité."""

    def test_create_compliance_check(self, audit_service, mock_db):
        """Création contrôle conformité."""
        check = audit_service.create_compliance_check(
            framework=ComplianceFramework.GDPR,
            control_id="GDPR-5.1",
            control_name="Consentement",
            check_type="MANUAL",
            severity="HIGH"
        )

        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_update_compliance_status(self, audit_service, mock_db):
        """Mise à jour statut conformité."""
        check = ComplianceCheck(
            id=1,
            tenant_id="tenant_test",
            framework=ComplianceFramework.GDPR,
            control_id="GDPR-5.1",
            control_name="Test",
            check_type="MANUAL",
            status="PENDING"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = check

        result = audit_service.update_compliance_status(
            check_id=1,
            status="COMPLIANT",
            checked_by=10
        )

        assert result.status == "COMPLIANT"
        mock_db.commit.assert_called()

    def test_get_compliance_summary(self, audit_service, mock_db):
        """Résumé conformité."""
        checks = [
            MagicMock(status="COMPLIANT", severity="HIGH"),
            MagicMock(status="COMPLIANT", severity="MEDIUM"),
            MagicMock(status="NON_COMPLIANT", severity="HIGH"),
            MagicMock(status="PENDING", severity="LOW")
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = checks

        summary = audit_service.get_compliance_summary()

        assert summary["total"] == 4
        assert summary["compliant"] == 2
        assert summary["non_compliant"] == 1
        assert summary["compliance_rate"] == 50.0


# ============================================================================
# TESTS SERVICE - RÉTENTION
# ============================================================================

class TestRetention:
    """Tests de gestion de la rétention."""

    def test_create_retention_rule(self, audit_service, mock_db):
        """Création règle rétention."""
        rule = audit_service.create_retention_rule(
            name="Logs audit 1 an",
            target_table="audit_logs",
            policy=RetentionPolicy.MEDIUM,
            retention_days=365
        )

        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_apply_retention_rules(self, audit_service, mock_db):
        """Application règles rétention."""
        rule = DataRetentionRule(
            id=1,
            tenant_id="tenant_test",
            name="Test",
            target_table="audit_logs",
            policy=RetentionPolicy.SHORT,
            retention_days=30,
            action="DELETE",
            is_active=True
        )
        mock_db.query.return_value.filter.return_value.all.return_value = [rule]
        mock_db.query.return_value.filter.return_value.delete.return_value = 10

        results = audit_service.apply_retention_rules()

        assert "Test" in results


# ============================================================================
# TESTS SERVICE - EXPORTS
# ============================================================================

class TestExports:
    """Tests de gestion des exports."""

    def test_create_export(self, audit_service, mock_db):
        """Création demande export."""
        export = audit_service.create_export(
            export_type="AUDIT_LOGS",
            format="CSV",
            requested_by=10
        )

        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_generate_export_file_json(self, audit_service):
        """Génération fichier JSON."""
        data = [{"id": 1, "name": "Test"}]
        content = audit_service._generate_export_file(data, "JSON")

        assert isinstance(content, bytes)
        parsed = json.loads(content.decode())
        assert parsed[0]["id"] == 1

    def test_generate_export_file_csv(self, audit_service):
        """Génération fichier CSV."""
        data = [{"id": 1, "name": "Test"}]
        content = audit_service._generate_export_file(data, "CSV")

        assert isinstance(content, bytes)
        assert b"id,name" in content


# ============================================================================
# TESTS SERVICE - DASHBOARDS
# ============================================================================

class TestDashboards:
    """Tests de gestion des dashboards."""

    def test_create_dashboard(self, audit_service, mock_db):
        """Création dashboard."""
        dashboard = audit_service.create_dashboard(
            code="MAIN_DASHBOARD",
            name="Dashboard Principal",
            widgets=[{"id": "w1", "type": "audit_stats"}],
            owner_id=10
        )

        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_get_audit_stats(self, audit_service, mock_db):
        """Récupération stats."""
        mock_db.query.return_value.filter.return_value.count.return_value = 100
        mock_db.query.return_value.filter.return_value.scalar.return_value = 5

        stats = audit_service._get_audit_stats()

        assert "total_logs_24h" in stats
        assert "active_sessions" in stats


# ============================================================================
# TESTS MODÈLES
# ============================================================================

class TestModels:
    """Tests des modèles SQLAlchemy."""

    def test_audit_log_model(self):
        """Test modèle AuditLog."""
        log = AuditLog(
            tenant_id="test",
            action=AuditAction.CREATE,
            module="treasury",
            level=AuditLevel.INFO
        )
        assert log.action == AuditAction.CREATE
        assert log.success is True

    def test_audit_session_model(self):
        """Test modèle AuditSession."""
        session = AuditSession(
            tenant_id="test",
            session_id="sess_123",
            user_id=10
        )
        assert session.is_active is True
        assert session.actions_count == 0

    def test_benchmark_model(self):
        """Test modèle Benchmark."""
        benchmark = Benchmark(
            tenant_id="test",
            code="TEST",
            name="Test",
            benchmark_type="PERFORMANCE"
        )
        assert benchmark.status == BenchmarkStatus.PENDING
        assert benchmark.version == "1.0"

    def test_compliance_check_model(self):
        """Test modèle ComplianceCheck."""
        check = ComplianceCheck(
            tenant_id="test",
            framework=ComplianceFramework.GDPR,
            control_id="GDPR-1",
            control_name="Test",
            check_type="MANUAL"
        )
        assert check.status == "PENDING"
        assert check.severity == "MEDIUM"


# ============================================================================
# TESTS ENUMS
# ============================================================================

class TestEnums:
    """Tests des enums."""

    def test_audit_action_values(self):
        """Valeurs AuditAction."""
        assert AuditAction.CREATE.value == "CREATE"
        assert AuditAction.LOGIN.value == "LOGIN"

    def test_audit_level_values(self):
        """Valeurs AuditLevel."""
        assert AuditLevel.DEBUG.value == "DEBUG"
        assert AuditLevel.CRITICAL.value == "CRITICAL"

    def test_retention_policy_values(self):
        """Valeurs RetentionPolicy."""
        assert RetentionPolicy.SHORT.value == "SHORT"
        assert RetentionPolicy.PERMANENT.value == "PERMANENT"

    def test_compliance_framework_values(self):
        """Valeurs ComplianceFramework."""
        assert ComplianceFramework.GDPR.value == "GDPR"
        assert ComplianceFramework.SOC2.value == "SOC2"


# ============================================================================
# TOTAL: 42 TESTS
# ============================================================================
