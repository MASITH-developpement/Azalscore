"""
AZALS - Tests Monitoring & Observabilité
========================================
Tests pour les modules de monitoring production (BLOC C).
"""

import pytest
import time
from unittest.mock import MagicMock, patch
from datetime import datetime


# ============================================================================
# TESTS MÉTRIQUES PROMETHEUS
# ============================================================================

class TestPrometheusMetrics:
    """Tests des métriques Prometheus."""

    def test_request_count_metric_exists(self):
        """Test que le compteur de requêtes est défini."""
        from app.core.monitoring.metrics import REQUEST_COUNT
        assert REQUEST_COUNT is not None
        # Prometheus client doesn't include _total suffix in _name
        assert "azals_http_requests" in REQUEST_COUNT._name

    def test_request_latency_metric_exists(self):
        """Test que l'histogramme de latence est défini."""
        from app.core.monitoring.metrics import REQUEST_LATENCY
        assert REQUEST_LATENCY is not None
        assert REQUEST_LATENCY._name == "azals_http_request_duration_seconds"

    def test_active_requests_gauge_exists(self):
        """Test que la gauge des requêtes actives est définie."""
        from app.core.monitoring.metrics import ACTIVE_REQUESTS
        assert ACTIVE_REQUESTS is not None
        assert ACTIVE_REQUESTS._name == "azals_http_requests_in_progress"

    def test_tenant_requests_counter_exists(self):
        """Test que le compteur par tenant est défini."""
        from app.core.monitoring.metrics import TENANT_REQUESTS
        assert TENANT_REQUESTS is not None
        # Prometheus client doesn't include _total suffix in _name
        assert "azals_tenant_requests" in TENANT_REQUESTS._name

    def test_record_business_operation(self):
        """Test enregistrement d'une opération métier."""
        from app.core.monitoring.metrics import record_business_operation, BUSINESS_OPERATIONS

        initial_value = BUSINESS_OPERATIONS.labels(
            operation="test_op",
            module="test",
            status="success"
        )._value.get()

        record_business_operation("test_op", "test", "success", duration=0.5)

        new_value = BUSINESS_OPERATIONS.labels(
            operation="test_op",
            module="test",
            status="success"
        )._value.get()

        assert new_value == initial_value + 1

    def test_record_ai_decision(self):
        """Test enregistrement d'une décision IA."""
        from app.core.monitoring.metrics import record_ai_decision, AI_DECISIONS

        initial_value = AI_DECISIONS.labels(
            decision_type="recommendation",
            risk_level="green",
            status="proposed"
        )._value.get()

        record_ai_decision("recommendation", "green", "proposed")

        new_value = AI_DECISIONS.labels(
            decision_type="recommendation",
            risk_level="green",
            status="proposed"
        )._value.get()

        assert new_value == initial_value + 1

    def test_record_red_point(self):
        """Test enregistrement d'un point rouge."""
        from app.core.monitoring.metrics import record_ai_decision, RED_POINTS

        initial_value = RED_POINTS.labels(status="pending")._value.get()

        record_ai_decision("decision", "red", "pending")

        new_value = RED_POINTS.labels(status="pending")._value.get()

        assert new_value == initial_value + 1


class TestMetricsMiddleware:
    """Tests du middleware de métriques."""

    def test_normalize_endpoint_with_uuid(self):
        """Test normalisation des endpoints avec UUID."""
        from app.core.monitoring.metrics import MetricsMiddleware

        path = "/api/users/550e8400-e29b-41d4-a716-446655440000/orders"
        normalized = MetricsMiddleware._normalize_endpoint(path)

        assert "{uuid}" in normalized
        assert "550e8400" not in normalized

    def test_normalize_endpoint_with_numeric_id(self):
        """Test normalisation des endpoints avec ID numérique."""
        from app.core.monitoring.metrics import MetricsMiddleware

        path = "/api/orders/12345/items"
        normalized = MetricsMiddleware._normalize_endpoint(path)

        assert "{id}" in normalized
        assert "12345" not in normalized

    def test_extract_module(self):
        """Test extraction du nom de module."""
        from app.core.monitoring.metrics import MetricsMiddleware

        assert MetricsMiddleware._extract_module("/commercial/orders") == "commercial"
        assert MetricsMiddleware._extract_module("/finance/invoices") == "finance"
        # Empty path returns empty string
        result = MetricsMiddleware._extract_module("/")
        assert result in ["", "root"]


# ============================================================================
# TESTS LOGGING STRUCTURÉ
# ============================================================================

class TestStructuredLogging:
    """Tests du logging structuré."""

    def test_json_formatter_output(self):
        """Test que le formatter produit du JSON valide."""
        import json
        from app.core.monitoring.logging import JSONFormatter
        import logging

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="azals.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )

        output = formatter.format(record)

        # Doit être du JSON valide
        parsed = json.loads(output)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["line"] == 42
        assert "timestamp" in parsed

    def test_contextual_logger_bind(self):
        """Test du binding de contexte sur le logger."""
        from app.core.monitoring.logging import get_logger

        logger = get_logger("test")
        bound_logger = logger.bind(tenant_id="tenant-123", user_id=42)

        assert bound_logger._context["tenant_id"] == "tenant-123"
        assert bound_logger._context["user_id"] == 42

    def test_get_logger_returns_contextual_logger(self):
        """Test que get_logger retourne un ContextualLogger."""
        from app.core.monitoring.logging import get_logger, ContextualLogger

        logger = get_logger("commercial")
        assert isinstance(logger, ContextualLogger)

    def test_audit_logger_log_action(self):
        """Test du logger d'audit."""
        from app.core.monitoring.logging import audit_logger

        # Ne doit pas lever d'exception
        audit_logger.log_action(
            action="create",
            resource_type="invoice",
            resource_id=123,
            tenant_id="tenant-1",
            user_id=1,
            details={"amount": 1000}
        )

    def test_audit_logger_log_red_point(self):
        """Test du log de point rouge."""
        from app.core.monitoring.logging import audit_logger

        # Ne doit pas lever d'exception
        audit_logger.log_red_point(
            decision_id=1,
            action="first_confirmation",
            tenant_id="tenant-1",
            first_validator=1
        )


# ============================================================================
# TESTS HEALTH CHECKS
# ============================================================================

class TestHealthChecks:
    """Tests des endpoints de santé."""

    def test_health_status_enum(self):
        """Test de l'enum HealthStatus."""
        from app.core.monitoring.health import HealthStatus

        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

    def test_component_health_model(self):
        """Test du modèle ComponentHealth."""
        from app.core.monitoring.health import ComponentHealth, HealthStatus

        component = ComponentHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            latency_ms=5.2,
            message="OK"
        )

        assert component.name == "database"
        assert component.status == HealthStatus.HEALTHY
        assert component.latency_ms == 5.2

    def test_detailed_health_check_model(self):
        """Test du modèle DetailedHealthCheck."""
        from app.core.monitoring.health import (
            DetailedHealthCheck, ComponentHealth, HealthStatus
        )

        check = DetailedHealthCheck(
            status=HealthStatus.HEALTHY,
            version="0.3.0",
            timestamp="2024-01-01T00:00:00Z",
            uptime_seconds=3600.0,
            components=[
                ComponentHealth(name="db", status=HealthStatus.HEALTHY)
            ],
            checks_passed=1,
            checks_failed=0
        )

        assert check.status == HealthStatus.HEALTHY
        assert len(check.components) == 1
        assert check.checks_passed == 1

    @patch('app.core.monitoring.health.engine')
    def test_check_database_healthy(self, mock_engine):
        """Test check database quand DB est saine."""
        from app.core.monitoring.health import check_database, HealthStatus

        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        result = check_database()

        assert result.name == "database"
        assert result.status == HealthStatus.HEALTHY
        assert result.latency_ms is not None

    @patch('app.core.monitoring.health.engine')
    def test_check_database_unhealthy(self, mock_engine):
        """Test check database quand DB est en erreur."""
        from app.core.monitoring.health import check_database, HealthStatus

        mock_engine.connect.side_effect = Exception("Connection refused")

        result = check_database()

        assert result.name == "database"
        assert result.status == HealthStatus.UNHEALTHY
        assert "error" in result.message.lower()


# ============================================================================
# TESTS SECURITY MIDDLEWARE
# ============================================================================

class TestSecurityMiddleware:
    """Tests des middlewares de sécurité."""

    def test_rate_limit_middleware_initialization(self):
        """Test initialisation du rate limiter."""
        from app.core.security_middleware import RateLimitMiddleware

        app = MagicMock()
        middleware = RateLimitMiddleware(
            app,
            requests_per_minute=100,
            requests_per_minute_per_tenant=500
        )

        assert middleware.requests_per_minute == 100
        assert middleware.requests_per_minute_per_tenant == 500
        assert middleware.burst_limit == 150  # 100 * 1.5

    def test_rate_limit_excluded_paths(self):
        """Test que certains paths sont exclus du rate limiting."""
        from app.core.security_middleware import RateLimitMiddleware

        app = MagicMock()
        middleware = RateLimitMiddleware(app)

        assert "/health" in middleware.excluded_paths
        assert "/metrics" in middleware.excluded_paths

    def test_security_headers_middleware_exists(self):
        """Test que le middleware de headers existe."""
        from app.core.security_middleware import SecurityHeadersMiddleware

        app = MagicMock()
        middleware = SecurityHeadersMiddleware(app)

        assert middleware is not None

    def test_request_validation_max_content_length(self):
        """Test de la limite de taille de requête."""
        from app.core.security_middleware import RequestValidationMiddleware

        assert RequestValidationMiddleware.MAX_CONTENT_LENGTH == 10 * 1024 * 1024  # 10MB

    def test_request_validation_allowed_content_types(self):
        """Test des content-types autorisés."""
        from app.core.security_middleware import RequestValidationMiddleware

        allowed = RequestValidationMiddleware.ALLOWED_CONTENT_TYPES

        assert "application/json" in allowed
        assert "application/x-www-form-urlencoded" in allowed
        assert "multipart/form-data" in allowed

    def test_ip_blocklist_middleware_block_ip(self):
        """Test du blocage d'une IP."""
        from app.core.security_middleware import IPBlocklistMiddleware

        app = MagicMock()
        middleware = IPBlocklistMiddleware(app)

        middleware.block_ip("192.168.1.100")

        assert "192.168.1.100" in middleware.blocked_ips

    def test_ip_blocklist_middleware_unblock_ip(self):
        """Test du déblocage d'une IP."""
        from app.core.security_middleware import IPBlocklistMiddleware

        app = MagicMock()
        middleware = IPBlocklistMiddleware(app, blocked_ips={"192.168.1.100"})

        middleware.unblock_ip("192.168.1.100")

        assert "192.168.1.100" not in middleware.blocked_ips

    def test_ip_blocklist_auto_block_on_violations(self):
        """Test du blocage automatique après violations."""
        from app.core.security_middleware import IPBlocklistMiddleware

        app = MagicMock()
        middleware = IPBlocklistMiddleware(app)
        middleware._auto_block_threshold = 3

        # Simuler des violations
        for i in range(3):
            blocked = middleware.record_violation("192.168.1.50")

        assert blocked is True
        assert "192.168.1.50" in middleware.blocked_ips


# ============================================================================
# TESTS CI/CD WORKFLOW
# ============================================================================

class TestCICDWorkflow:
    """Tests de validation du workflow CI/CD."""

    def test_workflow_file_exists(self):
        """Test que le fichier workflow existe."""
        import os

        workflow_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..",
            ".github", "workflows", "ci-cd.yml"
        )

        # Normaliser le chemin
        workflow_path = os.path.normpath(workflow_path)

        assert os.path.exists(workflow_path), f"Workflow file not found at {workflow_path}"

    def test_workflow_valid_yaml(self):
        """Test que le workflow est du YAML valide."""
        import yaml
        import os

        workflow_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..",
            ".github", "workflows", "ci-cd.yml"
        )
        workflow_path = os.path.normpath(workflow_path)

        with open(workflow_path, 'r') as f:
            content = yaml.safe_load(f)

        # Vérifications basiques
        assert "name" in content
        # Note: YAML parses "on:" as boolean True
        assert True in content or "on" in content
        assert "jobs" in content

        # Vérifier les jobs essentiels
        jobs = content["jobs"]
        assert "test" in jobs
        # Security jobs ont été séparés en security-sast et security-sca
        assert "security-sast" in jobs or "security-sca" in jobs or "security" in jobs
        assert "build" in jobs


# ============================================================================
# TESTS INFRASTRUCTURE
# ============================================================================

class TestInfrastructureConfig:
    """Tests des fichiers de configuration infrastructure."""

    def test_prometheus_config_exists(self):
        """Test que la config Prometheus existe."""
        import os

        config_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..",
            "infra", "prometheus", "prometheus.yml"
        )
        config_path = os.path.normpath(config_path)

        assert os.path.exists(config_path)

    def test_nginx_config_exists(self):
        """Test que la config Nginx existe."""
        import os

        config_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..",
            "infra", "nginx", "nginx.conf"
        )
        config_path = os.path.normpath(config_path)

        assert os.path.exists(config_path)

    def test_docker_compose_prod_exists(self):
        """Test que docker-compose.prod.yml existe."""
        import os

        compose_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..",
            "docker-compose.prod.yml"
        )
        compose_path = os.path.normpath(compose_path)

        assert os.path.exists(compose_path)

    def test_dockerfile_prod_exists(self):
        """Test que Dockerfile.prod existe."""
        import os

        dockerfile_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..",
            "Dockerfile.prod"
        )
        dockerfile_path = os.path.normpath(dockerfile_path)

        assert os.path.exists(dockerfile_path)


# ============================================================================
# TESTS INTÉGRATION MONITORING
# ============================================================================

class TestMonitoringIntegration:
    """Tests d'intégration du module monitoring."""

    def test_monitoring_module_exports(self):
        """Test que le module monitoring exporte tous les composants."""
        from app.core.monitoring import (
            MetricsMiddleware,
            metrics_router,
            REQUEST_COUNT,
            REQUEST_LATENCY,
            setup_logging,
            get_logger,
            LoggingMiddleware,
            health_router,
            HealthStatus,
            DetailedHealthCheck,
        )

        # Tous les imports doivent réussir
        assert MetricsMiddleware is not None
        assert metrics_router is not None
        assert REQUEST_COUNT is not None
        assert REQUEST_LATENCY is not None
        assert setup_logging is not None
        assert get_logger is not None
        assert LoggingMiddleware is not None
        assert health_router is not None
        assert HealthStatus is not None
        assert DetailedHealthCheck is not None

    def test_setup_logging_does_not_raise(self):
        """Test que setup_logging ne lève pas d'exception."""
        from app.core.monitoring.logging import setup_logging

        # Ne doit pas lever d'exception
        setup_logging(level="DEBUG", json_output=True)
        setup_logging(level="INFO", json_output=False)
