"""
AZALS MODULE GATEWAY - API Gateway / Integrations
===================================================

Module complet pour la gestion d'API Gateway:

FONCTIONNALITES:
- Endpoints API personnalises avec documentation OpenAPI auto-generee
- Authentification multi-methodes (API keys, OAuth2, JWT, HMAC)
- Rate limiting par tenant avec strategies multiples (fixed/sliding window, token/leaky bucket)
- Quotas et facturation par periode (minute, heure, jour, mois)
- Webhooks sortants avec retry, backoff exponentiel et circuit breaker
- Transformations de donnees (JMESPath, JSONata, Jinja2, mapping)
- Circuit breaker pattern pour resilience
- Logs et metriques en temps reel
- Monitoring avec dashboard

CONFORMITE:
- tenant_id obligatoire sur tous les modeles
- Soft delete avec deleted_at
- Audit complet via GatewayAuditLog
- Version pour optimistic locking
- _base_query() filtre par tenant

USAGE:
    from app.modules.gateway import GatewayService, create_gateway_service
    from app.modules.gateway.models import (
        GatewayApiPlan, GatewayApiKey, GatewayEndpoint,
        GatewayWebhook, HttpMethod, PlanTier
    )
    from app.modules.gateway.schemas import (
        ApiPlanCreateSchema, ApiKeyCreateSchema, WebhookCreateSchema
    )
    from app.modules.gateway.router import router as gateway_router

    # Dans votre app FastAPI:
    app.include_router(gateway_router, prefix="/api/v1")

    # Utilisation du service:
    service = create_gateway_service(db, context)

    # Creer un plan
    plan = service.create_plan(ApiPlanCreateSchema(
        code="STARTER",
        name="Plan Starter",
        tier=PlanTier.STARTER,
        requests_per_minute=60,
        requests_per_hour=1000,
        requests_per_day=10000,
        requests_per_month=100000
    ))

    # Creer une cle API
    key, full_key = service.create_api_key(ApiKeyCreateSchema(
        name="Production Key",
        plan_id=plan.data.id
    ))

    # Valider une requete
    ctx = service.process_request(
        raw_api_key=full_key,
        method=HttpMethod.GET,
        path="/api/orders",
        client_ip="192.168.1.1"
    )
"""

from .models import (
    # Enums
    ApiKeyStatus,
    AuthType,
    CircuitState,
    DeliveryStatus,
    EndpointType,
    HttpMethod,
    PlanTier,
    QuotaPeriod,
    RateLimitStrategy,
    TransformationType,
    WebhookEventType,
    WebhookStatus,
    # Models
    GatewayApiKey,
    GatewayApiPlan,
    GatewayAuditLog,
    GatewayCircuitBreaker,
    GatewayEndpoint,
    GatewayMetrics,
    GatewayOAuthClient,
    GatewayOAuthToken,
    GatewayQuotaUsage,
    GatewayRateLimitState,
    GatewayRequestLog,
    GatewayTransformation,
    GatewayWebhook,
    GatewayWebhookDelivery,
)

from .schemas import (
    # Plan
    ApiPlanCreateSchema,
    ApiPlanUpdateSchema,
    ApiPlanResponseSchema,
    # Key
    ApiKeyCreateSchema,
    ApiKeyUpdateSchema,
    ApiKeyResponseSchema,
    ApiKeyCreatedResponseSchema,
    ApiKeyRevokeSchema,
    # Endpoint
    EndpointCreateSchema,
    EndpointUpdateSchema,
    EndpointResponseSchema,
    # Transformation
    TransformationCreateSchema,
    TransformationUpdateSchema,
    TransformationResponseSchema,
    # Webhook
    WebhookCreateSchema,
    WebhookUpdateSchema,
    WebhookResponseSchema,
    WebhookTestSchema,
    WebhookTestResponseSchema,
    WebhookDeliveryResponseSchema,
    # Rate limit / Quota
    QuotaUsageResponseSchema,
    RateLimitStatusSchema,
    CircuitBreakerStatusSchema,
    # Metrics
    RequestLogResponseSchema,
    MetricsResponseSchema,
    MetricsQuerySchema,
    # OAuth
    OAuthClientCreateSchema,
    OAuthClientResponseSchema,
    OAuthClientCreatedResponseSchema,
    OAuthTokenRequestSchema,
    OAuthTokenResponseSchema,
    # Dashboard
    GatewayStatsSchema,
    GatewayDashboardSchema,
    # OpenAPI
    OpenApiGenerationRequestSchema,
    OpenApiSpecResponseSchema,
)

from .exceptions import (
    GatewayException,
    # Auth
    AuthenticationError,
    InvalidApiKeyError,
    ExpiredApiKeyError,
    RevokedApiKeyError,
    SuspendedApiKeyError,
    InvalidOAuthTokenError,
    ExpiredOAuthTokenError,
    # Authorization
    AuthorizationError,
    InsufficientScopeError,
    IpNotAllowedError,
    OriginNotAllowedError,
    EndpointNotAllowedError,
    # Rate limiting
    RateLimitError,
    QuotaExceededError,
    # Circuit breaker
    CircuitBreakerError,
    CircuitOpenError,
    # Webhook
    WebhookError,
    WebhookDeliveryError,
    WebhookTimeoutError,
    WebhookSignatureError,
    # Transformation
    TransformationError,
    InvalidTransformationError,
    # Validation
    ValidationError,
    RequestSizeLimitError,
    InvalidContentTypeError,
    SchemaValidationError,
    # Resources
    ResourceNotFoundError,
    ResourceConflictError,
    DuplicateResourceError,
    # Backend
    BackendError,
    BackendTimeoutError,
    BackendConnectionError,
    BackendResponseError,
)

from .service import (
    GatewayService,
    create_gateway_service,
    ThrottleDecision,
    RequestContext,
)

from .router import router

__all__ = [
    # Router
    "router",
    # Service
    "GatewayService",
    "create_gateway_service",
    "ThrottleDecision",
    "RequestContext",
    # Enums
    "ApiKeyStatus",
    "AuthType",
    "CircuitState",
    "DeliveryStatus",
    "EndpointType",
    "HttpMethod",
    "PlanTier",
    "QuotaPeriod",
    "RateLimitStrategy",
    "TransformationType",
    "WebhookEventType",
    "WebhookStatus",
    # Models
    "GatewayApiKey",
    "GatewayApiPlan",
    "GatewayAuditLog",
    "GatewayCircuitBreaker",
    "GatewayEndpoint",
    "GatewayMetrics",
    "GatewayOAuthClient",
    "GatewayOAuthToken",
    "GatewayQuotaUsage",
    "GatewayRateLimitState",
    "GatewayRequestLog",
    "GatewayTransformation",
    "GatewayWebhook",
    "GatewayWebhookDelivery",
    # Schemas
    "ApiPlanCreateSchema",
    "ApiPlanUpdateSchema",
    "ApiPlanResponseSchema",
    "ApiKeyCreateSchema",
    "ApiKeyUpdateSchema",
    "ApiKeyResponseSchema",
    "ApiKeyCreatedResponseSchema",
    "ApiKeyRevokeSchema",
    "EndpointCreateSchema",
    "EndpointUpdateSchema",
    "EndpointResponseSchema",
    "TransformationCreateSchema",
    "TransformationUpdateSchema",
    "TransformationResponseSchema",
    "WebhookCreateSchema",
    "WebhookUpdateSchema",
    "WebhookResponseSchema",
    "WebhookTestSchema",
    "WebhookTestResponseSchema",
    "WebhookDeliveryResponseSchema",
    "QuotaUsageResponseSchema",
    "RateLimitStatusSchema",
    "CircuitBreakerStatusSchema",
    "RequestLogResponseSchema",
    "MetricsResponseSchema",
    "MetricsQuerySchema",
    "OAuthClientCreateSchema",
    "OAuthClientResponseSchema",
    "OAuthClientCreatedResponseSchema",
    "OAuthTokenRequestSchema",
    "OAuthTokenResponseSchema",
    "GatewayStatsSchema",
    "GatewayDashboardSchema",
    "OpenApiGenerationRequestSchema",
    "OpenApiSpecResponseSchema",
    # Exceptions
    "GatewayException",
    "AuthenticationError",
    "InvalidApiKeyError",
    "ExpiredApiKeyError",
    "RevokedApiKeyError",
    "SuspendedApiKeyError",
    "InvalidOAuthTokenError",
    "ExpiredOAuthTokenError",
    "AuthorizationError",
    "InsufficientScopeError",
    "IpNotAllowedError",
    "OriginNotAllowedError",
    "EndpointNotAllowedError",
    "RateLimitError",
    "QuotaExceededError",
    "CircuitBreakerError",
    "CircuitOpenError",
    "WebhookError",
    "WebhookDeliveryError",
    "WebhookTimeoutError",
    "WebhookSignatureError",
    "TransformationError",
    "InvalidTransformationError",
    "ValidationError",
    "RequestSizeLimitError",
    "InvalidContentTypeError",
    "SchemaValidationError",
    "ResourceNotFoundError",
    "ResourceConflictError",
    "DuplicateResourceError",
    "BackendError",
    "BackendTimeoutError",
    "BackendConnectionError",
    "BackendResponseError",
]
