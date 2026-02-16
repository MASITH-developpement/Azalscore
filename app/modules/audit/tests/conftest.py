"""
Fixtures pour les tests audit v2

Hérite des fixtures globales de app/conftest.py.
"""

import pytest
from datetime import datetime, timedelta, date
from uuid import uuid4


# ============================================================================
# FIXTURES HÉRITÉES DU CONFTEST GLOBAL
# ============================================================================
# Les fixtures suivantes sont héritées de app/conftest.py:
# - tenant_id, user_id, user_uuid
# - db_session, test_db_session
# - test_client (avec headers auto-injectés)
# - mock_auth_global (autouse=True)
# - saas_context


@pytest.fixture
def client(test_client):
    """
    Alias pour test_client (compatibilité avec anciens tests).

    Le test_client du conftest global ajoute déjà les headers requis.
    """
    return test_client


@pytest.fixture
def auth_headers(tenant_id):
    """Headers d'authentification avec tenant ID."""
    return {
        # Token > 20 chars requis par CSRF middleware
        "Authorization": "Bearer mock-jwt-token-for-testing-audit-module-with-extra-length",
        "X-Tenant-ID": tenant_id
    }


@pytest.fixture
def sample_audit_logs_batch(test_db_session, tenant_id, user_uuid):
    """
    Cree un batch de logs d'audit pour les tests.

    Retourne une liste de 20 logs avec differentes combinaisons:
    - Actions: CREATE, READ, UPDATE, DELETE
    - Levels: INFO, WARNING, ERROR
    - Modules: finance, hr, commercial
    - Success: True/False
    """
    from app.modules.audit.models import AuditLog, AuditAction, AuditLevel, AuditCategory

    logs = []
    modules = ["finance", "hr", "commercial", "inventory"]
    actions = [AuditAction.CREATE, AuditAction.READ, AuditAction.UPDATE, AuditAction.DELETE]
    levels = [AuditLevel.INFO, AuditLevel.WARNING, AuditLevel.ERROR]
    categories = [AuditCategory.BUSINESS, AuditCategory.SECURITY, AuditCategory.DATA]

    for i in range(20):
        log = AuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            action=actions[i % len(actions)],
            level=levels[i % len(levels)],
            category=categories[i % len(categories)],
            module=modules[i % len(modules)],
            entity_type="TestEntity",
            entity_id=str(uuid4()),
            user_id=user_uuid,
            user_email=f"test_{i}@example.com",
            user_role="ADMIN",
            session_id=str(uuid4()),
            request_id=str(uuid4()),
            ip_address=f"192.168.1.{i + 1}",
            user_agent="pytest-test-agent",
            description=f"Test audit log {i}",
            success=(i % 3 != 0),  # ~66% success
            created_at=datetime.utcnow() - timedelta(hours=i)
        )
        test_db_session.add(log)
        logs.append(log)

    test_db_session.commit()

    yield logs

    # Cleanup
    for log in logs:
        try:
            test_db_session.delete(log)
        except Exception:
            pass
    test_db_session.commit()


@pytest.fixture
def sample_metric(test_db_session, tenant_id):
    """Cree une metrique de test."""
    from app.modules.audit.models import MetricDefinition, MetricType

    metric = MetricDefinition(
        id=uuid4(),
        tenant_id=tenant_id,
        code="TEST_METRIC_001",
        name="test_metric",
        description="Test metric for unit tests",
        metric_type=MetricType.COUNTER,
        unit="count",
        module="test",
        aggregation_period="HOUR",
        retention_days=90,
        is_active=True,
        is_system=False
    )
    test_db_session.add(metric)
    test_db_session.commit()

    yield metric

    try:
        test_db_session.delete(metric)
        test_db_session.commit()
    except Exception:
        pass


@pytest.fixture
def sample_benchmark(test_db_session, tenant_id, user_uuid):
    """Cree un benchmark de test."""
    from app.modules.audit.models import Benchmark, BenchmarkStatus

    benchmark = Benchmark(
        id=uuid4(),
        tenant_id=tenant_id,
        code="TEST_BENCHMARK_001",
        name="test_benchmark",
        description="Test benchmark for unit tests",
        version="1.0",
        benchmark_type="PERFORMANCE",
        module="test",
        config="{}",
        baseline="{}",
        is_scheduled=False,
        status=BenchmarkStatus.PENDING,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by=user_uuid
    )
    test_db_session.add(benchmark)
    test_db_session.commit()

    yield benchmark

    try:
        test_db_session.delete(benchmark)
        test_db_session.commit()
    except Exception:
        pass


@pytest.fixture
def sample_compliance_check(test_db_session, tenant_id):
    """Cree un controle de conformite de test."""
    from app.modules.audit.models import ComplianceCheck, ComplianceFramework

    check = ComplianceCheck(
        tenant_id=tenant_id,
        framework=ComplianceFramework.GDPR,
        control_id="GDPR-001",
        control_name="Data Protection",
        control_description="Test compliance check",
        category="privacy",
        check_type="MANUAL",
        severity="MEDIUM",
        status="PENDING"
    )
    test_db_session.add(check)
    test_db_session.commit()

    yield check

    try:
        test_db_session.delete(check)
        test_db_session.commit()
    except Exception:
        pass


@pytest.fixture
def sample_retention_rule(test_db_session, tenant_id):
    """Cree une regle de retention de test."""
    from app.modules.audit.models import DataRetentionRule, RetentionPolicy

    rule = DataRetentionRule(
        tenant_id=tenant_id,
        name="test_retention_rule",
        description="Test retention rule",
        target_table="audit_logs",
        policy=RetentionPolicy.SHORT,
        retention_days=30,
        action="DELETE",
        is_active=True
    )
    test_db_session.add(rule)
    test_db_session.commit()

    yield rule

    try:
        test_db_session.delete(rule)
        test_db_session.commit()
    except Exception:
        pass


@pytest.fixture
def sample_dashboard(test_db_session, tenant_id, user_uuid):
    """Cree un dashboard de test."""
    from app.modules.audit.models import AuditDashboard

    dashboard = AuditDashboard(
        id=uuid4(),
        tenant_id=tenant_id,
        code="TEST_DASHBOARD_001",
        name="test_dashboard",
        description="Test dashboard",
        widgets='[]',
        layout='{}',
        refresh_interval=60,
        is_public=False,
        owner_id=user_uuid,
        is_default=False,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db_session.add(dashboard)
    test_db_session.commit()

    yield dashboard

    try:
        test_db_session.delete(dashboard)
        test_db_session.commit()
    except Exception:
        pass


@pytest.fixture
def sample_audit_log(test_db_session, tenant_id, user_uuid):
    """Cree un seul log d'audit pour les tests."""
    from app.modules.audit.models import AuditLog, AuditAction, AuditLevel, AuditCategory

    log = AuditLog(
        id=uuid4(),
        tenant_id=tenant_id,
        action=AuditAction.CREATE,
        level=AuditLevel.INFO,
        category=AuditCategory.BUSINESS,
        module="finance",
        entity_type="Invoice",
        entity_id=str(uuid4()),
        user_id=user_uuid,
        user_email="test@example.com",
        user_role="ADMIN",
        session_id=str(uuid4()),
        request_id=str(uuid4()),
        ip_address="192.168.1.100",
        user_agent="pytest-test-agent",
        description="Test single audit log",
        success=True,
        created_at=datetime.utcnow()
    )
    test_db_session.add(log)
    test_db_session.commit()

    yield log

    try:
        test_db_session.delete(log)
        test_db_session.commit()
    except Exception:
        pass


@pytest.fixture
def sample_session(test_db_session, tenant_id, user_uuid):
    """Cree une session d'audit de test."""
    from app.modules.audit.models import AuditSession

    session = AuditSession(
        id=uuid4(),
        tenant_id=tenant_id,
        session_id=str(uuid4()),
        user_id=user_uuid,
        user_email="test@example.com",
        login_at=datetime.utcnow() - timedelta(hours=1),
        last_activity_at=datetime.utcnow(),
        ip_address="192.168.1.100",
        device_type="Desktop",
        browser="Chrome",
        os="Linux",
        country="FR",
        city="Paris",
        actions_count=10,
        reads_count=5,
        writes_count=5,
        is_active=True
    )
    test_db_session.add(session)
    test_db_session.commit()

    yield session

    try:
        test_db_session.delete(session)
        test_db_session.commit()
    except Exception:
        pass


@pytest.fixture
def sample_export_data():
    """Donnees pour creer un export."""
    return {
        "export_type": "AUDIT_LOGS",
        "format": "CSV",
        "date_from": (datetime.utcnow() - timedelta(days=7)).isoformat(),
        "date_to": datetime.utcnow().isoformat(),
        "filters": {"level": "INFO"}
    }


@pytest.fixture
def sample_metric_data():
    """Donnees pour creer une metrique."""
    return {
        "code": "TEST_METRIC_CREATE",
        "name": "Test Metric Create",
        "description": "Metric for creation tests",
        "metric_type": "COUNTER",
        "unit": "count",
        "module": "test",
        "aggregation_period": "HOUR",
        "retention_days": 90
    }


@pytest.fixture
def sample_metric_values(test_db_session, tenant_id, sample_metric):
    """Cree des valeurs de metrique pour les tests."""
    from app.modules.audit.models import MetricValue

    values = []
    for i in range(10):
        value = MetricValue(
            id=uuid4(),
            tenant_id=tenant_id,
            metric_id=sample_metric.id,
            metric_code=sample_metric.code,
            value=float(i * 10),
            min_value=float(i * 5),
            max_value=float(i * 15),
            avg_value=float(i * 10),
            count=i + 1,
            period_start=datetime.utcnow() - timedelta(hours=i+1),
            period_end=datetime.utcnow() - timedelta(hours=i)
        )
        test_db_session.add(value)
        values.append(value)

    test_db_session.commit()

    yield values

    for val in values:
        try:
            test_db_session.delete(val)
        except Exception:
            pass
    test_db_session.commit()


@pytest.fixture
def sample_benchmark_data():
    """Donnees pour creer un benchmark."""
    return {
        "code": "TEST_BENCHMARK_CREATE",
        "name": "Test Benchmark Create",
        "description": "Benchmark for creation tests",
        "version": "1.0",
        "benchmark_type": "PERFORMANCE",
        "module": "test",
        "config": {"threshold": 100},
        "baseline": {"value": 50},
        "is_scheduled": False
    }


@pytest.fixture
def sample_benchmark_result(test_db_session, tenant_id, sample_benchmark, user_uuid):
    """Cree un resultat de benchmark pour les tests."""
    from app.modules.audit.models import BenchmarkResult, BenchmarkStatus

    result = BenchmarkResult(
        id=uuid4(),
        tenant_id=tenant_id,
        benchmark_id=sample_benchmark.id,
        started_at=datetime.utcnow() - timedelta(minutes=5),
        completed_at=datetime.utcnow(),
        duration_ms=1500.0,
        status=BenchmarkStatus.COMPLETED,
        score=85.5,
        passed=True,
        results='{"tests": 10, "passed": 9}',
        summary="Test benchmark completed",
        executed_by=str(user_uuid)
    )
    test_db_session.add(result)
    test_db_session.commit()

    yield result

    try:
        test_db_session.delete(result)
        test_db_session.commit()
    except Exception:
        pass


@pytest.fixture
def sample_compliance_data():
    """Donnees pour creer un controle de conformite."""
    return {
        "framework": "GDPR",
        "control_id": "GDPR-TEST-001",
        "control_name": "Test Control",
        "control_description": "Test compliance control for unit tests",
        "category": "privacy",
        "check_type": "MANUAL",
        "severity": "MEDIUM"
    }


@pytest.fixture
def sample_retention_data():
    """Donnees pour creer une regle de retention."""
    return {
        "name": "test_retention_create",
        "description": "Retention rule for creation tests",
        "target_table": "audit_logs",
        "policy": "SHORT",
        "retention_days": 30,
        "action": "DELETE"
    }


@pytest.fixture
def sample_dashboard_data():
    """Donnees pour creer un dashboard."""
    return {
        "code": "TEST_DASHBOARD_CREATE",
        "name": "Test Dashboard Create",
        "description": "Dashboard for creation tests",
        "widgets": [
            {
                "id": "widget_1",
                "type": "audit_stats",
                "title": "Audit Statistics",
                "config": {},
                "size": "medium"
            }
        ],
        "layout": {"columns": 2},
        "refresh_interval": 60,
        "is_public": False,
        "is_default": False
    }


@pytest.fixture
def sample_export(test_db_session, tenant_id, user_uuid):
    """Cree un export de test."""
    from app.modules.audit.models import AuditExport

    export = AuditExport(
        id=uuid4(),
        tenant_id=tenant_id,
        export_type="AUDIT_LOGS",
        format="CSV",
        date_from=datetime.utcnow() - timedelta(days=7),
        date_to=datetime.utcnow(),
        filters='{"level": "INFO"}',
        status="PENDING",
        progress=0,
        requested_by=user_uuid,
        requested_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    test_db_session.add(export)
    test_db_session.commit()

    yield export

    try:
        test_db_session.delete(export)
        test_db_session.commit()
    except Exception:
        pass


@pytest.fixture
def benchmark():
    """
    Fixture de benchmark dummy pour les tests de performance.

    Remplace pytest-benchmark si non installé.
    """
    class DummyBenchmark:
        def __call__(self, func, *args, **kwargs):
            return func(*args, **kwargs)
    return DummyBenchmark()


@pytest.fixture
def assert_audit_trail():
    """
    Fixture helper pour valider les champs d'audit trail.

    Retourne une fonction qui vérifie qu'un dictionnaire
    contient les champs requis pour l'audit trail.
    """
    def _assert_audit_trail(data: dict, required_fields: list[str] = None):
        """Vérifie que les champs d'audit trail sont présents."""
        default_fields = [
            "id", "tenant_id", "action", "module",
            "user_id", "created_at"
        ]
        fields_to_check = required_fields or default_fields

        for field in fields_to_check:
            assert field in data, f"Champ audit trail manquant: {field}"

        return True

    return _assert_audit_trail
