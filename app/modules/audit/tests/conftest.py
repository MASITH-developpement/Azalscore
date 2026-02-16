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
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": tenant_id
    }


@pytest.fixture
def sample_audit_logs_batch(db_session, tenant_id, user_uuid):
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
        db_session.add(log)
        logs.append(log)

    db_session.commit()

    yield logs

    # Cleanup
    for log in logs:
        try:
            db_session.delete(log)
        except Exception:
            pass
    db_session.commit()


@pytest.fixture
def sample_metric(db_session, tenant_id):
    """Cree une metrique de test."""
    from app.modules.audit.models import MetricDefinition, MetricType

    metric = MetricDefinition(
        tenant_id=tenant_id,
        name="test_metric",
        description="Test metric for unit tests",
        metric_type=MetricType.COUNTER,
        unit="count",
        category="test",
        is_active=True
    )
    db_session.add(metric)
    db_session.commit()

    yield metric

    try:
        db_session.delete(metric)
        db_session.commit()
    except Exception:
        pass


@pytest.fixture
def sample_benchmark(db_session, tenant_id):
    """Cree un benchmark de test."""
    from app.modules.audit.models import Benchmark, BenchmarkStatus

    benchmark = Benchmark(
        tenant_id=tenant_id,
        name="test_benchmark",
        description="Test benchmark for unit tests",
        benchmark_type="PERFORMANCE",
        config="{}",
        baseline="{}",
        is_active=True
    )
    db_session.add(benchmark)
    db_session.commit()

    yield benchmark

    try:
        db_session.delete(benchmark)
        db_session.commit()
    except Exception:
        pass


@pytest.fixture
def sample_compliance_check(db_session, tenant_id):
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
    db_session.add(check)
    db_session.commit()

    yield check

    try:
        db_session.delete(check)
        db_session.commit()
    except Exception:
        pass


@pytest.fixture
def sample_retention_rule(db_session, tenant_id):
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
    db_session.add(rule)
    db_session.commit()

    yield rule

    try:
        db_session.delete(rule)
        db_session.commit()
    except Exception:
        pass


@pytest.fixture
def sample_dashboard(db_session, tenant_id, user_uuid):
    """Cree un dashboard de test."""
    from app.modules.audit.models import AuditDashboard

    dashboard = AuditDashboard(
        tenant_id=tenant_id,
        name="test_dashboard",
        description="Test dashboard",
        config='{"widgets": []}',
        created_by=user_uuid
    )
    db_session.add(dashboard)
    db_session.commit()

    yield dashboard

    try:
        db_session.delete(dashboard)
        db_session.commit()
    except Exception:
        pass
