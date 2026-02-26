"""
AZALS MODULE GATEWAY - Tests Service
======================================

Tests unitaires pour le service Gateway.
"""

import hashlib
import json
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.modules.gateway.models import (
    ApiKeyStatus,
    CircuitState,
    GatewayApiKey,
    GatewayApiPlan,
    GatewayCircuitBreaker,
    GatewayEndpoint,
    GatewayQuotaUsage,
    GatewayRateLimitState,
    HttpMethod,
    PlanTier,
    QuotaPeriod,
    RateLimitStrategy,
    WebhookEventType,
    WebhookStatus,
)
from app.modules.gateway.schemas import (
    ApiKeyCreateSchema,
    ApiPlanCreateSchema,
    EndpointCreateSchema,
    WebhookCreateSchema,
)
from app.modules.gateway.service import GatewayService, ThrottleDecision


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock de la session DB."""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    return db


@pytest.fixture
def mock_context():
    """Mock du contexte SaaS."""
    context = MagicMock()
    context.tenant_id = "tenant_test_123"
    context.user_id = uuid4()
    return context


@pytest.fixture
def gateway_service(mock_db, mock_context):
    """Service Gateway avec mocks."""
    return GatewayService(mock_db, mock_context)


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
        is_active=True
    )


@pytest.fixture
def sample_api_key(sample_plan):
    """Cle API exemple."""
    return GatewayApiKey(
        id=uuid4(),
        tenant_id="tenant_test_123",
        name="Test Key",
        key_prefix="sk_live_abc123",
        key_hash=hashlib.sha256(b"test_key").hexdigest(),
        plan_id=sample_plan.id,
        status=ApiKeyStatus.ACTIVE,
        scopes=json.dumps(["read:orders", "write:orders"]),
        usage_count=0
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
        circuit_breaker_enabled=True,
        failure_threshold=5,
        recovery_timeout_seconds=30
    )


# ============================================================================
# TESTS PLANS API
# ============================================================================

class TestApiPlans:
    """Tests pour la gestion des plans API."""

    def test_create_plan_success(self, gateway_service, mock_db):
        """Test creation de plan reussie."""
        gateway_service._plan_repo.get_by_code = MagicMock(return_value=None)
        gateway_service._plan_repo.create = MagicMock(
            return_value=GatewayApiPlan(
                id=uuid4(),
                tenant_id="tenant_test_123",
                code="STARTER",
                name="Plan Starter",
                tier=PlanTier.STARTER,
                requests_per_minute=60,
                requests_per_hour=1000,
                requests_per_day=10000,
                requests_per_month=100000
            )
        )

        data = ApiPlanCreateSchema(
            code="STARTER",
            name="Plan Starter",
            tier=PlanTier.STARTER,
            requests_per_minute=60,
            requests_per_hour=1000,
            requests_per_day=10000,
            requests_per_month=100000
        )

        result = gateway_service.create_plan(data)

        assert result.success
        assert result.data.code == "STARTER"
        assert result.data.tier == PlanTier.STARTER

    def test_create_plan_duplicate_code(self, gateway_service, sample_plan):
        """Test creation de plan avec code duplique."""
        gateway_service._plan_repo.get_by_code = MagicMock(return_value=sample_plan)

        data = ApiPlanCreateSchema(
            code="STARTER",
            name="Plan Starter",
            tier=PlanTier.STARTER,
            requests_per_minute=60,
            requests_per_hour=1000,
            requests_per_day=10000,
            requests_per_month=100000
        )

        result = gateway_service.create_plan(data)

        assert not result.success
        assert result.error_code == "DUPLICATE"

    def test_get_plan_success(self, gateway_service, sample_plan):
        """Test recuperation de plan."""
        gateway_service._plan_repo.get_active = MagicMock(return_value=sample_plan)

        result = gateway_service.get_plan(sample_plan.id)

        assert result.success
        assert result.data.id == sample_plan.id

    def test_get_plan_not_found(self, gateway_service):
        """Test recuperation de plan inexistant."""
        gateway_service._plan_repo.get_active = MagicMock(return_value=None)

        result = gateway_service.get_plan(uuid4())

        assert not result.success
        assert result.error_code == "NOT_FOUND"


# ============================================================================
# TESTS CLES API
# ============================================================================

class TestApiKeys:
    """Tests pour la gestion des cles API."""

    def test_create_api_key_success(self, gateway_service, sample_plan):
        """Test creation de cle API."""
        gateway_service._plan_repo.get_active = MagicMock(return_value=sample_plan)
        gateway_service._key_repo.create = MagicMock(
            return_value=GatewayApiKey(
                id=uuid4(),
                tenant_id="tenant_test_123",
                name="Test Key",
                key_prefix="sk_live_xyz",
                key_hash="hash123",
                plan_id=sample_plan.id,
                status=ApiKeyStatus.ACTIVE
            )
        )
        gateway_service._quota_repo.get_or_create_current = MagicMock()

        data = ApiKeyCreateSchema(
            name="Test Key",
            plan_id=sample_plan.id
        )

        result = gateway_service.create_api_key(data)

        assert result.success
        api_key, full_key = result.data
        assert api_key.name == "Test Key"
        assert full_key.startswith("sk_live_")

    def test_create_api_key_plan_not_found(self, gateway_service):
        """Test creation de cle avec plan inexistant."""
        gateway_service._plan_repo.get_active = MagicMock(return_value=None)

        data = ApiKeyCreateSchema(
            name="Test Key",
            plan_id=uuid4()
        )

        result = gateway_service.create_api_key(data)

        assert not result.success
        assert result.error_code == "NOT_FOUND"

    def test_validate_api_key_success(self, gateway_service, sample_api_key):
        """Test validation de cle API valide."""
        raw_key = "test_key"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        sample_api_key.key_hash = key_hash

        gateway_service._key_repo.get_by_hash = MagicMock(return_value=sample_api_key)

        result = gateway_service.validate_api_key(raw_key)

        assert result.success
        assert result.data.id == sample_api_key.id

    def test_validate_api_key_invalid(self, gateway_service):
        """Test validation de cle API invalide."""
        gateway_service._key_repo.get_by_hash = MagicMock(return_value=None)

        result = gateway_service.validate_api_key("invalid_key")

        assert not result.success
        assert result.error_code == "INVALID_API_KEY"

    def test_validate_api_key_revoked(self, gateway_service, sample_api_key):
        """Test validation de cle API revoquee."""
        sample_api_key.status = ApiKeyStatus.REVOKED
        gateway_service._key_repo.get_by_hash = MagicMock(return_value=sample_api_key)

        result = gateway_service.validate_api_key("test_key")

        assert not result.success
        assert result.error_code == "REVOKED_API_KEY"

    def test_validate_api_key_expired(self, gateway_service, sample_api_key):
        """Test validation de cle API expiree."""
        sample_api_key.expires_at = datetime.utcnow() - timedelta(days=1)
        gateway_service._key_repo.get_by_hash = MagicMock(return_value=sample_api_key)

        result = gateway_service.validate_api_key("test_key")

        assert not result.success
        assert result.error_code == "EXPIRED_API_KEY"

    def test_revoke_api_key(self, gateway_service, sample_api_key):
        """Test revocation de cle API."""
        gateway_service._key_repo.get_active = MagicMock(return_value=sample_api_key)

        result = gateway_service.revoke_api_key(sample_api_key.id, "Security breach")

        assert result.success
        assert sample_api_key.status == ApiKeyStatus.REVOKED
        assert sample_api_key.revoked_reason == "Security breach"


# ============================================================================
# TESTS RATE LIMITING
# ============================================================================

class TestRateLimiting:
    """Tests pour le rate limiting."""

    def test_check_rate_limit_allowed(self, gateway_service, sample_api_key, sample_plan, sample_endpoint):
        """Test rate limiting - requete autorisee."""
        gateway_service._plan_repo.get_active = MagicMock(return_value=sample_plan)
        gateway_service._ratelimit_repo.get_or_create_state = MagicMock(
            return_value=GatewayRateLimitState(
                id=uuid4(),
                tenant_id="tenant_test_123",
                api_key_id=sample_api_key.id,
                endpoint_pattern="*",
                request_count=10,
                window_start=datetime.utcnow(),
                tokens_remaining=Decimal("50"),
                last_refill=datetime.utcnow()
            )
        )

        decision = gateway_service.check_rate_limit(
            sample_api_key,
            sample_endpoint,
            HttpMethod.GET
        )

        assert decision.allowed
        assert decision.action == "ALLOW"
        assert decision.rate_limit_remaining > 0

    def test_check_rate_limit_exceeded(self, gateway_service, sample_api_key, sample_plan, sample_endpoint):
        """Test rate limiting - limite depassee."""
        gateway_service._plan_repo.get_active = MagicMock(return_value=sample_plan)
        gateway_service._ratelimit_repo.get_or_create_state = MagicMock(
            return_value=GatewayRateLimitState(
                id=uuid4(),
                tenant_id="tenant_test_123",
                api_key_id=sample_api_key.id,
                endpoint_pattern="*",
                request_count=60,  # Egal a la limite
                window_start=datetime.utcnow(),
                tokens_remaining=Decimal("0"),
                last_refill=datetime.utcnow()
            )
        )

        decision = gateway_service.check_rate_limit(
            sample_api_key,
            sample_endpoint,
            HttpMethod.GET
        )

        assert not decision.allowed
        assert decision.action == "REJECT"
        assert decision.rate_limit_remaining == 0

    def test_check_quota_exceeded(self, gateway_service, sample_api_key, sample_plan):
        """Test quota depasse."""
        exceeded_quota = GatewayQuotaUsage(
            id=uuid4(),
            tenant_id="tenant_test_123",
            api_key_id=sample_api_key.id,
            period=QuotaPeriod.DAY,
            period_start=datetime.utcnow().replace(hour=0, minute=0),
            period_end=datetime.utcnow().replace(hour=23, minute=59),
            requests_count=10001,
            requests_limit=10000,
            is_exceeded=True,
            exceeded_at=datetime.utcnow()
        )

        gateway_service._quota_repo.get_or_create_current = MagicMock(
            return_value=exceeded_quota
        )

        result = gateway_service.check_quota(sample_api_key, sample_plan)

        assert not result.success
        assert result.error_code == "QUOTA_EXCEEDED"


# ============================================================================
# TESTS CIRCUIT BREAKER
# ============================================================================

class TestCircuitBreaker:
    """Tests pour le circuit breaker."""

    def test_circuit_closed_initially(self, gateway_service, sample_endpoint):
        """Test circuit ferme initialement."""
        gateway_service._circuit_repo.get_or_create = MagicMock(
            return_value=GatewayCircuitBreaker(
                id=uuid4(),
                tenant_id="tenant_test_123",
                endpoint_id=sample_endpoint.id,
                state=CircuitState.CLOSED,
                failure_count=0
            )
        )

        result = gateway_service.is_circuit_open(sample_endpoint)

        assert not result

    def test_circuit_opens_after_failures(self, gateway_service, sample_endpoint):
        """Test circuit ouvert apres echecs."""
        cb = GatewayCircuitBreaker(
            id=uuid4(),
            tenant_id="tenant_test_123",
            endpoint_id=sample_endpoint.id,
            state=CircuitState.CLOSED,
            failure_count=4,
            failure_threshold=5
        )
        gateway_service._circuit_repo.get_or_create = MagicMock(return_value=cb)

        # Enregistrer un echec supplementaire
        gateway_service.record_circuit_failure(sample_endpoint)

        assert cb.failure_count == 5
        assert cb.state == CircuitState.OPEN

    def test_circuit_half_open_after_timeout(self, gateway_service, sample_endpoint):
        """Test circuit half-open apres timeout."""
        cb = GatewayCircuitBreaker(
            id=uuid4(),
            tenant_id="tenant_test_123",
            endpoint_id=sample_endpoint.id,
            state=CircuitState.OPEN,
            opened_at=datetime.utcnow() - timedelta(seconds=35),
            timeout_seconds=30
        )
        gateway_service._circuit_repo.get_or_create = MagicMock(return_value=cb)

        result = gateway_service.get_circuit_state(sample_endpoint)

        assert result.state == CircuitState.HALF_OPEN

    def test_circuit_closes_after_successes(self, gateway_service, sample_endpoint):
        """Test circuit ferme apres succes."""
        cb = GatewayCircuitBreaker(
            id=uuid4(),
            tenant_id="tenant_test_123",
            endpoint_id=sample_endpoint.id,
            state=CircuitState.HALF_OPEN,
            success_count=1,
            success_threshold=2
        )
        gateway_service._circuit_repo.get_or_create = MagicMock(return_value=cb)

        # Enregistrer un succes supplementaire
        gateway_service.record_circuit_success(sample_endpoint)

        assert cb.success_count >= 2
        assert cb.state == CircuitState.CLOSED


# ============================================================================
# TESTS ENDPOINTS
# ============================================================================

class TestEndpoints:
    """Tests pour la gestion des endpoints."""

    def test_create_endpoint_success(self, gateway_service):
        """Test creation d'endpoint."""
        gateway_service._endpoint_repo.get_by_code = MagicMock(return_value=None)
        gateway_service._endpoint_repo.create = MagicMock(
            return_value=GatewayEndpoint(
                id=uuid4(),
                tenant_id="tenant_test_123",
                code="GET_ORDERS",
                name="Get Orders",
                path_pattern="/api/v1/orders/*",
                methods=json.dumps(["GET"]),
                is_active=True
            )
        )

        data = EndpointCreateSchema(
            code="GET_ORDERS",
            name="Get Orders",
            path_pattern="/api/v1/orders/*",
            methods=[HttpMethod.GET]
        )

        result = gateway_service.create_endpoint(data)

        assert result.success
        assert result.data.code == "GET_ORDERS"

    def test_find_endpoint_by_path_exact(self, gateway_service, sample_endpoint):
        """Test recherche endpoint par chemin exact."""
        gateway_service._endpoint_repo.find_by_path = MagicMock(return_value=sample_endpoint)

        result = gateway_service.find_endpoint_by_path("/api/v1/orders/123")

        assert result is not None
        assert result.id == sample_endpoint.id


# ============================================================================
# TESTS WEBHOOKS
# ============================================================================

class TestWebhooks:
    """Tests pour la gestion des webhooks."""

    def test_create_webhook_success(self, gateway_service):
        """Test creation de webhook."""
        from app.modules.gateway.models import GatewayWebhook

        gateway_service._webhook_repo.get_by_code = MagicMock(return_value=None)
        gateway_service._webhook_repo.create = MagicMock(
            return_value=GatewayWebhook(
                id=uuid4(),
                tenant_id="tenant_test_123",
                code="ORDER_CREATED",
                name="Order Created Webhook",
                url="https://example.com/webhook",
                method=HttpMethod.POST,
                event_types=json.dumps(["ORDER_CREATED"]),
                status=WebhookStatus.ACTIVE
            )
        )

        data = WebhookCreateSchema(
            code="ORDER_CREATED",
            name="Order Created Webhook",
            url="https://example.com/webhook",
            event_types=[WebhookEventType.ORDER_CREATED]
        )

        result = gateway_service.create_webhook(data)

        assert result.success
        assert result.data.code == "ORDER_CREATED"

    def test_trigger_webhook_creates_delivery(self, gateway_service):
        """Test declenchement de webhook cree une livraison."""
        from app.modules.gateway.models import GatewayWebhook

        webhook = GatewayWebhook(
            id=uuid4(),
            tenant_id="tenant_test_123",
            code="ORDER_CREATED",
            name="Order Webhook",
            url="https://example.com/webhook",
            method=HttpMethod.POST,
            event_types=json.dumps(["ORDER_CREATED"]),
            status=WebhookStatus.ACTIVE
        )

        gateway_service._webhook_repo.list_by_event_type = MagicMock(return_value=[webhook])
        gateway_service._webhook_repo.get_by_id = MagicMock(return_value=webhook)

        delivery_ids = gateway_service.trigger_webhook(
            event_type=WebhookEventType.ORDER_CREATED,
            event_id="order_123",
            event_data={"order_id": "123", "total": 100}
        )

        assert len(delivery_ids) == 1


# ============================================================================
# TESTS PROCESS REQUEST
# ============================================================================

class TestProcessRequest:
    """Tests pour le traitement des requetes."""

    def test_process_request_success(self, gateway_service, sample_api_key, sample_plan, sample_endpoint):
        """Test traitement de requete reussie."""
        raw_key = "sk_live_abc123_validkey"
        sample_api_key.key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        gateway_service._key_repo.get_by_hash = MagicMock(return_value=sample_api_key)
        gateway_service._plan_repo.get_active = MagicMock(return_value=sample_plan)
        gateway_service._endpoint_repo.find_by_path = MagicMock(return_value=sample_endpoint)
        gateway_service._circuit_repo.get_or_create = MagicMock(
            return_value=GatewayCircuitBreaker(
                id=uuid4(),
                tenant_id="tenant_test_123",
                endpoint_id=sample_endpoint.id,
                state=CircuitState.CLOSED
            )
        )
        gateway_service._quota_repo.get_or_create_current = MagicMock(
            return_value=GatewayQuotaUsage(
                id=uuid4(),
                tenant_id="tenant_test_123",
                api_key_id=sample_api_key.id,
                period=QuotaPeriod.MINUTE,
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow() + timedelta(minutes=1),
                requests_count=10,
                requests_limit=60,
                is_exceeded=False
            )
        )
        gateway_service._ratelimit_repo.get_or_create_state = MagicMock(
            return_value=GatewayRateLimitState(
                id=uuid4(),
                tenant_id="tenant_test_123",
                api_key_id=sample_api_key.id,
                endpoint_pattern="*",
                request_count=10,
                window_start=datetime.utcnow(),
                tokens_remaining=Decimal("50"),
                last_refill=datetime.utcnow()
            )
        )

        result = gateway_service.process_request(
            raw_api_key=raw_key,
            method=HttpMethod.GET,
            path="/api/v1/orders/123",
            client_ip="192.168.1.1"
        )

        assert result.success
        ctx = result.data
        assert ctx.api_key is not None
        assert ctx.plan is not None

    def test_process_request_invalid_key(self, gateway_service):
        """Test traitement avec cle invalide."""
        gateway_service._key_repo.get_by_hash = MagicMock(return_value=None)

        result = gateway_service.process_request(
            raw_api_key="invalid_key",
            method=HttpMethod.GET,
            path="/api/v1/orders",
            client_ip="192.168.1.1"
        )

        assert not result.success
        assert result.error_code == "INVALID_API_KEY"

    def test_process_request_ip_not_allowed(self, gateway_service, sample_api_key, sample_plan):
        """Test traitement avec IP non autorisee."""
        sample_api_key.allowed_ips = json.dumps(["10.0.0.1"])
        raw_key = "valid_key"
        sample_api_key.key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        gateway_service._key_repo.get_by_hash = MagicMock(return_value=sample_api_key)
        gateway_service._plan_repo.get_active = MagicMock(return_value=sample_plan)

        result = gateway_service.process_request(
            raw_api_key=raw_key,
            method=HttpMethod.GET,
            path="/api/v1/orders",
            client_ip="192.168.1.1"
        )

        assert not result.success
        assert result.error_code == "IP_NOT_ALLOWED"


# ============================================================================
# TESTS OPENAPI
# ============================================================================

class TestOpenApi:
    """Tests pour la generation OpenAPI."""

    def test_generate_openapi_spec(self, gateway_service, sample_endpoint):
        """Test generation de spec OpenAPI."""
        gateway_service._endpoint_repo.list_active = MagicMock(return_value=[sample_endpoint])

        result = gateway_service.generate_openapi_spec(
            title="Test API",
            version="1.0.0"
        )

        assert result.success
        spec = result.data
        assert spec["openapi"] == "3.0.3"
        assert spec["info"]["title"] == "Test API"
        assert len(spec["paths"]) > 0
