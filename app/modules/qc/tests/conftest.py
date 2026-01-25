"""
Fixtures pour les tests du module QC - CORE SaaS v2
====================================================
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.saas_context import SaaSContext, UserRole, TenantScope
from app.modules.qc.models import (
    ModuleRegistry,
    ModuleStatus,
    QCAlert,
    QCCheckResult,
    QCCheckStatus,
    QCDashboard,
    QCMetric,
    QCRule,
    QCRuleCategory,
    QCRuleSeverity,
    QCTemplate,
    QCValidation,
    TestRun,
    TestType,
    ValidationPhase,
)


# ============================================================================
# MOCK SAAS CONTEXT
# ============================================================================

@pytest.fixture
def mock_saas_context():
    """Mock SaaSContext pour les tests"""
    return SaaSContext(
        tenant_id="1",
        user_id=UUID("00000000-0000-0000-0000-000000000101"),
        role=UserRole.ADMIN,
        permissions={"qc.*"},
        scope=TenantScope.TENANT,
        ip_address="127.0.0.1",
        user_agent="pytest",
        correlation_id="test-qc-001"
    )


@pytest.fixture
def client():
    """Client de test FastAPI."""
    return TestClient(app)


# ============================================================================
# DATA FIXTURES - QC Rules
# ============================================================================

@pytest.fixture
def qc_rule_data():
    """Données pour créer une règle QC"""
    return {
        "code": "QC001",
        "name": "Test Coverage Minimum",
        "category": "TESTING",
        "check_type": "test_coverage",
        "description": "Coverage must be at least 80%",
        "severity": "WARNING",
        "threshold_value": 80.0,
        "threshold_operator": ">=",
    }


@pytest.fixture
def qc_rule_entity():
    """Entité règle QC pour les tests"""
    return QCRule(
        id=1,
        tenant_id="1",
        code="QC001",
        name="Test Coverage Minimum",
        category=QCRuleCategory.TESTING,
        check_type="test_coverage",
        description="Coverage must be at least 80%",
        severity=QCRuleSeverity.WARNING,
        threshold_value=80.0,
        threshold_operator=">=",
        is_active=True,
        is_system=False,
        applies_to_modules="*",
        created_at=datetime.utcnow(),
    )


# ============================================================================
# DATA FIXTURES - Module Registry
# ============================================================================

@pytest.fixture
def module_registry_data():
    """Données pour enregistrer un module"""
    return {
        "module_code": "TEST_MODULE",
        "module_name": "Test Module",
        "module_type": "business",
        "module_version": "1.0.0",
        "description": "Module for testing",
        "dependencies": ["core", "common"],
    }


@pytest.fixture
def module_registry_entity():
    """Entité module registry pour les tests"""
    return ModuleRegistry(
        id=1,
        tenant_id="1",
        module_code="TEST_MODULE",
        module_name="Test Module",
        module_type="business",
        module_version="1.0.0",
        description="Module for testing",
        status=ModuleStatus.DEVELOPMENT,
        overall_score=0.0,
        registered_at=datetime.utcnow(),
    )


# ============================================================================
# DATA FIXTURES - Validations
# ============================================================================

@pytest.fixture
def validation_data():
    """Données pour créer une validation"""
    return {
        "module_id": 1,
        "phase": "AUTOMATED",
    }


@pytest.fixture
def validation_entity():
    """Entité validation pour les tests"""
    return QCValidation(
        id=1,
        tenant_id="1",
        module_id=1,
        validation_phase=ValidationPhase.AUTOMATED,
        status=QCCheckStatus.RUNNING,
        started_at=datetime.utcnow(),
        total_rules=10,
        passed_rules=8,
        failed_rules=2,
        blocked_rules=0,
        skipped_rules=0,
        overall_score=80.0,
    )


# ============================================================================
# DATA FIXTURES - Test Runs
# ============================================================================

@pytest.fixture
def test_run_data():
    """Données pour créer un test run"""
    return {
        "module_id": 1,
        "test_type": "UNIT",
        "total_tests": 100,
        "passed_tests": 95,
        "failed_tests": 5,
        "skipped_tests": 0,
        "error_tests": 0,
        "coverage_percent": 85.5,
        "test_suite": "pytest",
        "duration_seconds": 120.5,
        "triggered_by": "manual",
    }


@pytest.fixture
def test_run_entity():
    """Entité test run pour les tests"""
    return TestRun(
        id=1,
        tenant_id="1",
        module_id=1,
        test_type=TestType.UNIT,
        status=QCCheckStatus.PASSED,
        total_tests=100,
        passed_tests=95,
        failed_tests=5,
        skipped_tests=0,
        error_tests=0,
        coverage_percent=85.5,
        test_suite="pytest",
        duration_seconds=120.5,
        triggered_by="manual",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )


# ============================================================================
# DATA FIXTURES - Metrics
# ============================================================================

@pytest.fixture
def metric_data():
    """Données pour créer une métrique"""
    return {
        "module_id": None,
    }


@pytest.fixture
def metric_entity():
    """Entité métrique pour les tests"""
    return QCMetric(
        id=1,
        tenant_id="1",
        metric_date=datetime.utcnow(),
        modules_total=10,
        modules_validated=8,
        modules_production=5,
        modules_failed=2,
        avg_overall_score=85.5,
        avg_architecture_score=90.0,
        avg_security_score=88.0,
        avg_performance_score=85.0,
        avg_code_quality_score=87.0,
        avg_testing_score=83.0,
        avg_documentation_score=80.0,
        total_tests_run=1000,
        total_tests_passed=950,
        avg_coverage=85.5,
        total_checks_run=500,
        total_checks_passed=475,
        critical_issues=2,
        blocker_issues=0,
        score_trend="UP",
        score_delta=2.5,
    )


# ============================================================================
# DATA FIXTURES - Alerts
# ============================================================================

@pytest.fixture
def alert_data():
    """Données pour créer une alerte"""
    return {
        "alert_type": "validation_failed",
        "title": "QC Failed: TEST_MODULE",
        "message": "Module failed validation",
        "severity": "CRITICAL",
        "module_id": 1,
        "validation_id": 1,
        "details": {"score": 50.0, "failed": 5},
    }


@pytest.fixture
def alert_entity():
    """Entité alerte pour les tests"""
    return QCAlert(
        id=1,
        tenant_id="1",
        module_id=1,
        validation_id=1,
        alert_type="validation_failed",
        severity=QCRuleSeverity.CRITICAL,
        title="QC Failed: TEST_MODULE",
        message="Module failed validation",
        is_resolved=False,
        created_at=datetime.utcnow(),
    )


# ============================================================================
# DATA FIXTURES - Dashboards
# ============================================================================

@pytest.fixture
def dashboard_data():
    """Données pour créer un dashboard"""
    return {
        "name": "QC Dashboard",
        "description": "Main quality control dashboard",
        "layout": {"rows": 3, "cols": 2},
        "widgets": [{"type": "chart", "data": "modules"}],
        "filters": {"status": "active"},
        "is_default": True,
        "is_public": False,
    }


@pytest.fixture
def dashboard_entity():
    """Entité dashboard pour les tests"""
    return QCDashboard(
        id=1,
        tenant_id="1",
        name="QC Dashboard",
        description="Main quality control dashboard",
        is_default=True,
        is_public=False,
        owner_id=1,
        created_at=datetime.utcnow(),
    )


# ============================================================================
# DATA FIXTURES - Templates
# ============================================================================

@pytest.fixture
def template_data():
    """Données pour créer un template"""
    return {
        "code": "TPL_BASIC",
        "name": "Basic QC Template",
        "description": "Basic quality control rules",
        "category": "standard",
        "rules": [
            {
                "code": "R001",
                "name": "Rule 1",
                "category": "CODE_QUALITY",
                "check_type": "generic",
                "severity": "WARNING",
            }
        ],
    }


@pytest.fixture
def template_entity():
    """Entité template pour les tests"""
    return QCTemplate(
        id=1,
        tenant_id="1",
        code="TPL_BASIC",
        name="Basic QC Template",
        description="Basic quality control rules",
        category="standard",
        is_active=True,
        created_at=datetime.utcnow(),
    )


# ============================================================================
# MOCK SERVICES
# ============================================================================

@pytest.fixture
def mock_qc_service(
    qc_rule_entity,
    module_registry_entity,
    validation_entity,
    test_run_entity,
    metric_entity,
    alert_entity,
    dashboard_entity,
    template_entity,
):
    """Mock du service QC avec toutes les méthodes"""
    service = MagicMock()

    # Rules
    service.create_rule.return_value = qc_rule_entity
    service.get_rule.return_value = qc_rule_entity
    service.list_rules.return_value = ([qc_rule_entity], 1)
    service.update_rule.return_value = qc_rule_entity
    service.delete_rule.return_value = True

    # Modules
    service.register_module.return_value = module_registry_entity
    service.get_module.return_value = module_registry_entity
    service.get_module_by_code.return_value = module_registry_entity
    service.list_modules.return_value = ([module_registry_entity], 1)
    service.update_module_status.return_value = module_registry_entity

    # Validations
    service.run_validation.return_value = validation_entity
    service.get_validation.return_value = validation_entity
    service.list_validations.return_value = ([validation_entity], 1)
    service.get_check_results.return_value = ([], 0)

    # Tests
    service.record_test_run.return_value = test_run_entity
    service.get_test_runs.return_value = ([test_run_entity], 1)

    # Metrics
    service.record_metrics.return_value = metric_entity
    service.get_metrics_history.return_value = [metric_entity]

    # Alerts
    service.create_alert.return_value = alert_entity
    service.list_alerts.return_value = ([alert_entity], 1)
    service.resolve_alert.return_value = alert_entity

    # Dashboards
    service.create_dashboard.return_value = dashboard_entity
    service.get_dashboard.return_value = dashboard_entity
    service.list_dashboards.return_value = [dashboard_entity]
    service.get_dashboard_data.return_value = {
        "summary": {
            "total_modules": 10,
            "validated_modules": 8,
            "production_modules": 5,
            "failed_modules": 2,
            "average_score": 85.5,
            "unresolved_alerts": 3,
        },
        "status_distribution": {},
        "recent_validations": [],
        "recent_tests": [],
        "critical_alerts": [],
    }

    # Templates
    service.create_template.return_value = template_entity
    service.get_template.return_value = template_entity
    service.list_templates.return_value = [template_entity]
    service.apply_template.return_value = [qc_rule_entity]

    return service


# ============================================================================
# MOCK DEPENDENCIES
# ============================================================================

@pytest.fixture(autouse=True)
def mock_dependencies(mock_saas_context, mock_qc_service):
    """Mock des dépendances FastAPI pour tous les tests"""
    from unittest.mock import patch

    with patch("app.modules.qc.router_v2.get_saas_context", return_value=mock_saas_context), \
         patch("app.modules.qc.router_v2.get_qc_service", return_value=mock_qc_service):
        yield
