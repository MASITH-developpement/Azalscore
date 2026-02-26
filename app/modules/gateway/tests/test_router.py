"""
AZALS MODULE GATEWAY - Tests Router
=====================================

Tests d'integration pour les endpoints API du module Gateway.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.gateway.models import (
    ApiKeyStatus,
    CircuitState,
    GatewayApiKey,
    GatewayApiPlan,
    GatewayEndpoint,
    GatewayWebhook,
    HttpMethod,
    PlanTier,
    RateLimitStrategy,
    WebhookEventType,
    WebhookStatus,
)
from app.modules.gateway.router import router, get_gateway_service
from app.modules.gateway.service import GatewayService
from app.core.saas_context import Result


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_gateway_service():
    """Mock du service Gateway."""
    service = MagicMock(spec=GatewayService)
    service.tenant_id = "tenant_test_123"
    service.user_id = uuid4()
    return service


@pytest.fixture
def app(mock_gateway_service):
    """Application FastAPI de test."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    # Override la dependance
    app.dependency_overrides[get_gateway_service] = lambda: mock_gateway_service

    return app


@pytest.fixture
def client(app):
    """Client de test."""
    return TestClient(app)


@pytest.fixture
def sample_plan():
    """Plan API exemple."""
    return GatewayApiPlan(
        id=uuid4(),
        tenant_id="tenant_test_123",
        code="STARTER",
        name="Plan Starter",
        tier=PlanTier.STARTER,
        requests_per_minute=60,
        requests_per_hour=1000,
        requests_per_day=10000,
        requests_per_month=100000,
        burst_limit=10,
        concurrent_connections=10,
        rate_limit_strategy=RateLimitStrategy.SLIDING_WINDOW,
        is_active=True,
        is_default=False,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_api_key(sample_plan):
    """Cle API exemple."""
    return GatewayApiKey(
        id=uuid4(),
        tenant_id="tenant_test_123",
        name="Test Key",
        key_prefix="sk_live_abc123",
        key_hash="hash123",
        key_hint="3456",
        plan_id=sample_plan.id,
        status=ApiKeyStatus.ACTIVE,
        usage_count=0,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_endpoint():
    """Endpoint exemple."""
    return GatewayEndpoint(
        id=uuid4(),
        tenant_id="tenant_test_123",
        code="GET_ORDERS",
        name="Get Orders",
        path_pattern="/api/v1/orders/*",
        methods=json.dumps(["GET", "POST"]),
        is_active=True,
        is_deprecated=False,
        circuit_breaker_enabled=True,
        failure_threshold=5,
        recovery_timeout_seconds=30,
        success_threshold=2,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


# ============================================================================
# TESTS PLANS API
# ============================================================================

class TestPlanEndpoints:
    """Tests pour les endpoints de plans API."""

    def test_create_plan(self, client, mock_gateway_service, sample_plan):
        """Test POST /plans."""
        mock_gateway_service.create_plan.return_value = Result.ok(sample_plan)

        response = client.post(
            "/api/v1/gateway/plans",
            json={
                "code": "STARTER",
                "name": "Plan Starter",
                "tier": "STARTER",
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "requests_per_day": 10000,
                "requests_per_month": 100000
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "STARTER"

    def test_create_plan_duplicate(self, client, mock_gateway_service):
        """Test POST /plans avec code duplique."""
        mock_gateway_service.create_plan.return_value = Result.fail(
            "Plan avec code 'STARTER' existe deja",
            error_code="DUPLICATE"
        )

        response = client.post(
            "/api/v1/gateway/plans",
            json={
                "code": "STARTER",
                "name": "Plan Starter",
                "tier": "STARTER",
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "requests_per_day": 10000,
                "requests_per_month": 100000
            }
        )

        assert response.status_code == 400

    def test_list_plans(self, client, mock_gateway_service, sample_plan):
        """Test GET /plans."""
        mock_gateway_service.list_plans.return_value = Result.ok(([sample_plan], 1))

        response = client.get("/api/v1/gateway/plans")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    def test_get_plan(self, client, mock_gateway_service, sample_plan):
        """Test GET /plans/{id}."""
        mock_gateway_service.get_plan.return_value = Result.ok(sample_plan)

        response = client.get(f"/api/v1/gateway/plans/{sample_plan.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "STARTER"

    def test_get_plan_not_found(self, client, mock_gateway_service):
        """Test GET /plans/{id} non trouve."""
        mock_gateway_service.get_plan.return_value = Result.fail(
            "Plan non trouve",
            error_code="NOT_FOUND"
        )

        response = client.get(f"/api/v1/gateway/plans/{uuid4()}")

        assert response.status_code == 404

    def test_update_plan(self, client, mock_gateway_service, sample_plan):
        """Test PUT /plans/{id}."""
        updated_plan = sample_plan
        updated_plan.name = "Updated Plan"
        mock_gateway_service.update_plan.return_value = Result.ok(updated_plan)

        response = client.put(
            f"/api/v1/gateway/plans/{sample_plan.id}",
            json={"name": "Updated Plan"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Plan"

    def test_delete_plan(self, client, mock_gateway_service, sample_plan):
        """Test DELETE /plans/{id}."""
        mock_gateway_service.delete_plan.return_value = Result.ok(True)

        response = client.delete(f"/api/v1/gateway/plans/{sample_plan.id}")

        assert response.status_code == 204


# ============================================================================
# TESTS CLES API
# ============================================================================

class TestApiKeyEndpoints:
    """Tests pour les endpoints de cles API."""

    def test_create_api_key(self, client, mock_gateway_service, sample_api_key):
        """Test POST /keys."""
        mock_gateway_service.create_api_key.return_value = Result.ok(
            (sample_api_key, "sk_live_abc123_fullkey")
        )

        response = client.post(
            "/api/v1/gateway/keys",
            json={
                "name": "Test Key",
                "plan_id": str(sample_api_key.plan_id)
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Key"
        assert "api_key" in data  # Cle complete

    def test_list_api_keys(self, client, mock_gateway_service, sample_api_key):
        """Test GET /keys."""
        mock_gateway_service.list_api_keys.return_value = Result.ok(([sample_api_key], 1))

        response = client.get("/api/v1/gateway/keys")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_api_key(self, client, mock_gateway_service, sample_api_key):
        """Test GET /keys/{id}."""
        mock_gateway_service.get_api_key.return_value = Result.ok(sample_api_key)

        response = client.get(f"/api/v1/gateway/keys/{sample_api_key.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Key"

    def test_revoke_api_key(self, client, mock_gateway_service, sample_api_key):
        """Test POST /keys/{id}/revoke."""
        mock_gateway_service.revoke_api_key.return_value = Result.ok(True)

        response = client.post(
            f"/api/v1/gateway/keys/{sample_api_key.id}/revoke",
            json={"reason": "Security breach"}
        )

        assert response.status_code == 204


# ============================================================================
# TESTS ENDPOINTS
# ============================================================================

class TestEndpointEndpoints:
    """Tests pour les endpoints d'endpoints."""

    def test_create_endpoint(self, client, mock_gateway_service, sample_endpoint):
        """Test POST /endpoints."""
        mock_gateway_service.create_endpoint.return_value = Result.ok(sample_endpoint)

        response = client.post(
            "/api/v1/gateway/endpoints",
            json={
                "code": "GET_ORDERS",
                "name": "Get Orders",
                "path_pattern": "/api/v1/orders/*",
                "methods": ["GET"]
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "GET_ORDERS"

    def test_list_endpoints(self, client, mock_gateway_service, sample_endpoint):
        """Test GET /endpoints."""
        mock_gateway_service.list_endpoints.return_value = Result.ok(([sample_endpoint], 1))

        response = client.get("/api/v1/gateway/endpoints")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_endpoint(self, client, mock_gateway_service, sample_endpoint):
        """Test GET /endpoints/{id}."""
        mock_gateway_service.get_endpoint.return_value = Result.ok(sample_endpoint)

        response = client.get(f"/api/v1/gateway/endpoints/{sample_endpoint.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "GET_ORDERS"

    def test_get_circuit_breaker_status(self, client, mock_gateway_service, sample_endpoint):
        """Test GET /endpoints/{id}/circuit-breaker."""
        from app.modules.gateway.models import GatewayCircuitBreaker

        mock_gateway_service.get_endpoint.return_value = Result.ok(sample_endpoint)
        mock_gateway_service.get_circuit_state.return_value = GatewayCircuitBreaker(
            id=uuid4(),
            tenant_id="tenant_test_123",
            endpoint_id=sample_endpoint.id,
            state=CircuitState.CLOSED,
            failure_count=0,
            success_count=0,
            failure_threshold=5,
            success_threshold=2,
            timeout_seconds=30
        )

        response = client.get(f"/api/v1/gateway/endpoints/{sample_endpoint.id}/circuit-breaker")

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "CLOSED"


# ============================================================================
# TESTS WEBHOOKS
# ============================================================================

class TestWebhookEndpoints:
    """Tests pour les endpoints de webhooks."""

    def test_create_webhook(self, client, mock_gateway_service):
        """Test POST /webhooks."""
        webhook = GatewayWebhook(
            id=uuid4(),
            tenant_id="tenant_test_123",
            code="ORDER_CREATED",
            name="Order Created",
            url="https://example.com/webhook",
            method=HttpMethod.POST,
            event_types=json.dumps(["ORDER_CREATED"]),
            status=WebhookStatus.ACTIVE,
            max_retries=3,
            retry_delay_seconds=60,
            timeout_seconds=30,
            success_count=0,
            failure_count=0,
            consecutive_failures=0,
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_gateway_service.create_webhook.return_value = Result.ok(webhook)

        response = client.post(
            "/api/v1/gateway/webhooks",
            json={
                "code": "ORDER_CREATED",
                "name": "Order Created",
                "url": "https://example.com/webhook",
                "event_types": ["ORDER_CREATED"]
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "ORDER_CREATED"

    def test_list_webhooks(self, client, mock_gateway_service):
        """Test GET /webhooks."""
        webhook = GatewayWebhook(
            id=uuid4(),
            tenant_id="tenant_test_123",
            code="ORDER_CREATED",
            name="Order Created",
            url="https://example.com/webhook",
            method=HttpMethod.POST,
            event_types=json.dumps(["ORDER_CREATED"]),
            status=WebhookStatus.ACTIVE,
            max_retries=3,
            retry_delay_seconds=60,
            timeout_seconds=30,
            success_count=10,
            failure_count=1,
            consecutive_failures=0,
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_gateway_service.list_webhooks.return_value = Result.ok(([webhook], 1))

        response = client.get("/api/v1/gateway/webhooks")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


# ============================================================================
# TESTS LOGS ET METRIQUES
# ============================================================================

class TestLogsAndMetrics:
    """Tests pour les logs et metriques."""

    def test_list_request_logs(self, client, mock_gateway_service):
        """Test GET /logs."""
        from app.modules.gateway.models import GatewayRequestLog

        log = GatewayRequestLog(
            id=uuid4(),
            tenant_id="tenant_test_123",
            method=HttpMethod.GET,
            path="/api/v1/orders",
            status_code=200,
            client_ip="192.168.1.1",
            response_body_size=1024,
            response_time_ms=50,
            was_throttled=False,
            was_cached=False,
            timestamp=datetime.utcnow()
        )
        mock_gateway_service.get_request_logs.return_value = Result.ok(([log], 1))

        response = client.get("/api/v1/gateway/logs")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_metrics(self, client, mock_gateway_service):
        """Test GET /metrics."""
        from app.modules.gateway.models import GatewayMetrics
        from decimal import Decimal

        metrics = GatewayMetrics(
            id=uuid4(),
            tenant_id="tenant_test_123",
            period_type="hour",
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow(),
            total_requests=1000,
            successful_requests=950,
            failed_requests=50,
            throttled_requests=10,
            cached_requests=100,
            avg_response_time=Decimal("45.5"),
            min_response_time=10,
            max_response_time=500,
            p50_response_time=40,
            p95_response_time=100,
            p99_response_time=200,
            total_bytes_in=102400,
            total_bytes_out=1048576,
            error_4xx_count=30,
            error_5xx_count=20
        )
        mock_gateway_service.get_metrics.return_value = Result.ok([metrics])

        response = client.get("/api/v1/gateway/metrics")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["total_requests"] == 1000


# ============================================================================
# TESTS DASHBOARD
# ============================================================================

class TestDashboard:
    """Tests pour le dashboard."""

    def test_get_dashboard(self, client, mock_gateway_service):
        """Test GET /dashboard."""
        mock_gateway_service.get_dashboard_stats.return_value = Result.ok({
            "total_plans": 5,
            "active_plans": 4,
            "total_api_keys": 100,
            "active_api_keys": 80,
            "total_endpoints": 20,
            "active_endpoints": 18,
            "deprecated_endpoints": 2,
            "total_webhooks": 10,
            "active_webhooks": 8,
            "failed_webhooks": 1,
            "requests_24h": 50000,
            "successful_requests_24h": 48000,
            "failed_requests_24h": 2000,
            "throttled_requests_24h": 500,
            "avg_response_time_24h": 45.5,
            "p95_response_time_24h": 150.0,
            "error_rate_24h": 4.0,
            "top_errors": [],
            "open_circuits": 0
        })
        mock_gateway_service.get_request_logs.return_value = Result.ok(([], 0))
        mock_gateway_service._log_repo = MagicMock()
        mock_gateway_service._log_repo.get_top_endpoints.return_value = []
        mock_gateway_service._delivery_repo = MagicMock()
        mock_gateway_service._delivery_repo.list_failed_recent.return_value = []

        response = client.get("/api/v1/gateway/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        assert data["stats"]["requests_24h"] == 50000


# ============================================================================
# TESTS OPENAPI
# ============================================================================

class TestOpenApi:
    """Tests pour la generation OpenAPI."""

    def test_generate_openapi(self, client, mock_gateway_service):
        """Test POST /openapi/generate."""
        mock_gateway_service.generate_openapi_spec.return_value = Result.ok({
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "components": {},
            "tags": [],
            "servers": []
        })

        response = client.post(
            "/api/v1/gateway/openapi/generate",
            json={"title": "Test API", "version": "1.0.0"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["openapi"] == "3.0.3"

    def test_get_openapi_json(self, client, mock_gateway_service):
        """Test GET /openapi.json."""
        mock_gateway_service.generate_openapi_spec.return_value = Result.ok({
            "openapi": "3.0.3",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {},
            "components": {},
            "tags": [],
            "servers": []
        })

        response = client.get("/api/v1/gateway/openapi.json")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"


# ============================================================================
# TESTS VALIDATION
# ============================================================================

class TestValidation:
    """Tests pour la validation de cle API."""

    def test_validate_api_key(self, client, mock_gateway_service, sample_api_key, sample_plan):
        """Test POST /validate."""
        mock_gateway_service.validate_api_key.return_value = Result.ok(sample_api_key)
        mock_gateway_service.get_plan.return_value = Result.ok(sample_plan)

        response = client.post(
            "/api/v1/gateway/validate",
            headers={"X-API-Key": "sk_live_test_key"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_validate_api_key_missing_header(self, client, mock_gateway_service):
        """Test POST /validate sans header."""
        response = client.post("/api/v1/gateway/validate")

        assert response.status_code == 401

    def test_validate_api_key_invalid(self, client, mock_gateway_service):
        """Test POST /validate avec cle invalide."""
        mock_gateway_service.validate_api_key.return_value = Result.fail(
            "Invalid API key",
            error_code="INVALID_API_KEY"
        )

        response = client.post(
            "/api/v1/gateway/validate",
            headers={"X-API-Key": "invalid_key"}
        )

        assert response.status_code == 401


# ============================================================================
# TESTS HEALTH CHECK
# ============================================================================

class TestHealthCheck:
    """Tests pour le health check."""

    def test_health_check_healthy(self, client, mock_gateway_service):
        """Test GET /health - sain."""
        mock_gateway_service._plan_repo = MagicMock()
        mock_gateway_service._plan_repo.count_active.return_value = 5

        response = client.get("/api/v1/gateway/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_check_unhealthy(self, client, mock_gateway_service):
        """Test GET /health - non sain."""
        mock_gateway_service._plan_repo = MagicMock()
        mock_gateway_service._plan_repo.count_active.side_effect = Exception("DB Error")

        response = client.get("/api/v1/gateway/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
