"""
AZALS MODULE GATEWAY - Schemas Pydantic
=========================================

Schemas pour validation et serialisation.
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models import (
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
)


# ============================================================================
# SCHEMAS DE BASE
# ============================================================================

class PaginationParams(BaseModel):
    """Parametres de pagination."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class BaseAuditSchema(BaseModel):
    """Schema de base avec champs d'audit."""
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# API PLAN SCHEMAS
# ============================================================================

class ApiPlanCreateSchema(BaseModel):
    """Creation d'un plan API."""
    code: str = Field(..., min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    tier: PlanTier = Field(default=PlanTier.STARTER)

    # Limites
    requests_per_minute: int = Field(default=60, ge=1, le=100000)
    requests_per_hour: int = Field(default=1000, ge=1, le=1000000)
    requests_per_day: int = Field(default=10000, ge=1, le=10000000)
    requests_per_month: int = Field(default=100000, ge=1, le=100000000)

    # Burst
    burst_limit: int = Field(default=10, ge=1, le=1000)
    concurrent_connections: int = Field(default=10, ge=1, le=1000)

    # Taille
    max_request_size_kb: int = Field(default=1024, ge=1, le=102400)
    max_response_size_kb: int = Field(default=10240, ge=1, le=1024000)

    # Rate limiting
    rate_limit_strategy: RateLimitStrategy = Field(default=RateLimitStrategy.SLIDING_WINDOW)

    # Timeout
    timeout_seconds: int = Field(default=30, ge=1, le=300)

    # Tarification
    monthly_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    overage_price_per_1000: Decimal = Field(default=Decimal("0.00"), ge=0)

    # Features
    features: Optional[Dict[str, Any]] = None
    allowed_endpoints: Optional[List[str]] = None
    blocked_endpoints: Optional[List[str]] = None


class ApiPlanUpdateSchema(BaseModel):
    """Mise a jour d'un plan API."""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    tier: Optional[PlanTier] = None

    requests_per_minute: Optional[int] = Field(None, ge=1, le=100000)
    requests_per_hour: Optional[int] = Field(None, ge=1, le=1000000)
    requests_per_day: Optional[int] = Field(None, ge=1, le=10000000)
    requests_per_month: Optional[int] = Field(None, ge=1, le=100000000)

    burst_limit: Optional[int] = Field(None, ge=1, le=1000)
    concurrent_connections: Optional[int] = Field(None, ge=1, le=1000)

    max_request_size_kb: Optional[int] = Field(None, ge=1, le=102400)
    max_response_size_kb: Optional[int] = Field(None, ge=1, le=1024000)

    rate_limit_strategy: Optional[RateLimitStrategy] = None
    timeout_seconds: Optional[int] = Field(None, ge=1, le=300)

    monthly_price: Optional[Decimal] = Field(None, ge=0)
    overage_price_per_1000: Optional[Decimal] = Field(None, ge=0)

    features: Optional[Dict[str, Any]] = None
    allowed_endpoints: Optional[List[str]] = None
    blocked_endpoints: Optional[List[str]] = None

    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class ApiPlanResponseSchema(BaseModel):
    """Reponse pour un plan API."""
    id: UUID
    tenant_id: str
    code: str
    name: str
    description: Optional[str]
    tier: PlanTier

    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    requests_per_month: int

    burst_limit: int
    concurrent_connections: int

    max_request_size_kb: int
    max_response_size_kb: int

    rate_limit_strategy: RateLimitStrategy
    timeout_seconds: int

    monthly_price: Decimal
    overage_price_per_1000: Decimal

    features: Optional[Dict[str, Any]] = None
    allowed_endpoints: Optional[List[str]] = None
    blocked_endpoints: Optional[List[str]] = None

    is_active: bool
    is_default: bool
    version: int

    created_at: datetime
    updated_at: datetime

    @field_validator('features', 'allowed_endpoints', 'blocked_endpoints', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# API KEY SCHEMAS
# ============================================================================

class ApiKeyCreateSchema(BaseModel):
    """Creation d'une cle API."""
    name: str = Field(..., min_length=2, max_length=200)
    plan_id: UUID
    client_id: Optional[str] = Field(None, max_length=255)
    user_id: Optional[UUID] = None

    scopes: Optional[List[str]] = None
    allowed_ips: Optional[List[str]] = None
    allowed_origins: Optional[List[str]] = None
    allowed_endpoints: Optional[List[str]] = None

    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    is_live: bool = Field(default=True, description="True pour production, False pour test")

    @field_validator('allowed_ips')
    @classmethod
    def validate_ips(cls, v):
        if v:
            import ipaddress
            for ip in v:
                try:
                    ipaddress.ip_address(ip)
                except ValueError:
                    try:
                        ipaddress.ip_network(ip, strict=False)
                    except ValueError:
                        raise ValueError(f"IP invalide: {ip}")
        return v


class ApiKeyUpdateSchema(BaseModel):
    """Mise a jour d'une cle API."""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    scopes: Optional[List[str]] = None
    allowed_ips: Optional[List[str]] = None
    allowed_origins: Optional[List[str]] = None
    allowed_endpoints: Optional[List[str]] = None
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class ApiKeyResponseSchema(BaseModel):
    """Reponse pour une cle API."""
    id: UUID
    tenant_id: str
    name: str
    key_prefix: str
    key_hint: Optional[str]

    plan_id: UUID
    client_id: Optional[str]
    user_id: Optional[UUID]

    scopes: Optional[List[str]]
    allowed_ips: Optional[List[str]]
    allowed_origins: Optional[List[str]]
    allowed_endpoints: Optional[List[str]]

    status: ApiKeyStatus
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    last_used_ip: Optional[str]
    usage_count: int

    metadata: Optional[Dict[str, Any]]
    version: int

    created_at: datetime
    updated_at: datetime

    @field_validator('scopes', 'allowed_ips', 'allowed_origins', 'allowed_endpoints', 'metadata', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = ConfigDict(from_attributes=True)


class ApiKeyCreatedResponseSchema(ApiKeyResponseSchema):
    """Reponse a la creation d'une cle (inclut la cle complete une seule fois)."""
    api_key: str = Field(..., description="Cle API complete - CONSERVER SECURISEMENT")


class ApiKeyRevokeSchema(BaseModel):
    """Revocation d'une cle API."""
    reason: Optional[str] = Field(None, max_length=500)


# ============================================================================
# ENDPOINT SCHEMAS
# ============================================================================

class EndpointCreateSchema(BaseModel):
    """Creation d'un endpoint."""
    code: str = Field(..., min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

    path_pattern: str = Field(..., min_length=1, max_length=500)
    methods: List[HttpMethod] = Field(default=[HttpMethod.GET])
    endpoint_type: EndpointType = Field(default=EndpointType.AUTHENTICATED)

    target_url: Optional[str] = Field(None, max_length=1000)
    target_timeout_seconds: int = Field(default=30, ge=1, le=300)

    auth_required: bool = Field(default=True)
    auth_type: Optional[AuthType] = None
    required_scopes: Optional[List[str]] = None

    custom_rate_limit: Optional[int] = Field(None, ge=1, le=100000)
    custom_window_seconds: Optional[int] = Field(None, ge=1, le=86400)

    cache_enabled: bool = Field(default=False)
    cache_ttl_seconds: int = Field(default=60, ge=1, le=86400)
    cache_vary_headers: Optional[List[str]] = None

    request_transform_id: Optional[UUID] = None
    response_transform_id: Optional[UUID] = None

    request_schema: Optional[Dict[str, Any]] = None
    max_body_size_kb: int = Field(default=1024, ge=1, le=102400)

    circuit_breaker_enabled: bool = Field(default=True)
    failure_threshold: int = Field(default=5, ge=1, le=100)
    recovery_timeout_seconds: int = Field(default=30, ge=1, le=3600)

    openapi_summary: Optional[str] = Field(None, max_length=200)
    openapi_description: Optional[str] = Field(None, max_length=2000)
    openapi_tags: Optional[List[str]] = None


class EndpointUpdateSchema(BaseModel):
    """Mise a jour d'un endpoint."""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

    path_pattern: Optional[str] = Field(None, min_length=1, max_length=500)
    methods: Optional[List[HttpMethod]] = None
    endpoint_type: Optional[EndpointType] = None

    target_url: Optional[str] = Field(None, max_length=1000)
    target_timeout_seconds: Optional[int] = Field(None, ge=1, le=300)

    auth_required: Optional[bool] = None
    auth_type: Optional[AuthType] = None
    required_scopes: Optional[List[str]] = None

    custom_rate_limit: Optional[int] = Field(None, ge=1, le=100000)
    custom_window_seconds: Optional[int] = Field(None, ge=1, le=86400)

    cache_enabled: Optional[bool] = None
    cache_ttl_seconds: Optional[int] = Field(None, ge=1, le=86400)
    cache_vary_headers: Optional[List[str]] = None

    request_transform_id: Optional[UUID] = None
    response_transform_id: Optional[UUID] = None

    request_schema: Optional[Dict[str, Any]] = None
    max_body_size_kb: Optional[int] = Field(None, ge=1, le=102400)

    circuit_breaker_enabled: Optional[bool] = None
    failure_threshold: Optional[int] = Field(None, ge=1, le=100)
    recovery_timeout_seconds: Optional[int] = Field(None, ge=1, le=3600)

    openapi_summary: Optional[str] = Field(None, max_length=200)
    openapi_description: Optional[str] = Field(None, max_length=2000)
    openapi_tags: Optional[List[str]] = None

    is_active: Optional[bool] = None
    is_deprecated: Optional[bool] = None
    deprecated_message: Optional[str] = Field(None, max_length=500)


class EndpointResponseSchema(BaseModel):
    """Reponse pour un endpoint."""
    id: UUID
    tenant_id: str
    code: str
    name: str
    description: Optional[str]

    path_pattern: str
    methods: List[HttpMethod]
    endpoint_type: EndpointType

    target_url: Optional[str]
    target_timeout_seconds: int

    auth_required: bool
    auth_type: Optional[AuthType]
    required_scopes: Optional[List[str]]

    custom_rate_limit: Optional[int]
    custom_window_seconds: Optional[int]

    cache_enabled: bool
    cache_ttl_seconds: int
    cache_vary_headers: Optional[List[str]]

    circuit_breaker_enabled: bool
    failure_threshold: int
    recovery_timeout_seconds: int

    openapi_summary: Optional[str]
    openapi_description: Optional[str]
    openapi_tags: Optional[List[str]]

    is_active: bool
    is_deprecated: bool
    deprecated_message: Optional[str]
    version: int

    created_at: datetime
    updated_at: datetime

    @field_validator('methods', 'required_scopes', 'cache_vary_headers', 'openapi_tags', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TRANSFORMATION SCHEMAS
# ============================================================================

class TransformationCreateSchema(BaseModel):
    """Creation d'une transformation."""
    code: str = Field(..., min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

    transformation_type: TransformationType
    configuration: Dict[str, Any] = Field(...)

    add_headers: Optional[Dict[str, str]] = None
    remove_headers: Optional[List[str]] = None
    rename_headers: Optional[Dict[str, str]] = None

    body_template: Optional[str] = None
    content_type_output: Optional[str] = Field(None, max_length=100)

    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None


class TransformationUpdateSchema(BaseModel):
    """Mise a jour d'une transformation."""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

    transformation_type: Optional[TransformationType] = None
    configuration: Optional[Dict[str, Any]] = None

    add_headers: Optional[Dict[str, str]] = None
    remove_headers: Optional[List[str]] = None
    rename_headers: Optional[Dict[str, str]] = None

    body_template: Optional[str] = None
    content_type_output: Optional[str] = Field(None, max_length=100)

    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None

    is_active: Optional[bool] = None


class TransformationResponseSchema(BaseModel):
    """Reponse pour une transformation."""
    id: UUID
    tenant_id: str
    code: str
    name: str
    description: Optional[str]

    transformation_type: TransformationType
    configuration: Dict[str, Any]

    add_headers: Optional[Dict[str, str]]
    remove_headers: Optional[List[str]]
    rename_headers: Optional[Dict[str, str]]

    body_template: Optional[str]
    content_type_output: Optional[str]

    is_active: bool
    version: int

    created_at: datetime
    updated_at: datetime

    @field_validator('configuration', 'add_headers', 'remove_headers', 'rename_headers', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# WEBHOOK SCHEMAS
# ============================================================================

class WebhookCreateSchema(BaseModel):
    """Creation d'un webhook."""
    code: str = Field(..., min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

    url: str = Field(..., min_length=10, max_length=1000)
    method: HttpMethod = Field(default=HttpMethod.POST)
    headers: Optional[Dict[str, str]] = None

    auth_type: Optional[AuthType] = None
    auth_config: Optional[Dict[str, str]] = None

    event_types: List[WebhookEventType] = Field(...)
    event_filters: Optional[Dict[str, Any]] = None

    payload_template: Optional[str] = None
    transform_id: Optional[UUID] = None

    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: int = Field(default=60, ge=10, le=3600)
    retry_backoff_multiplier: Decimal = Field(default=Decimal("2.0"), ge=1, le=10)

    timeout_seconds: int = Field(default=30, ge=5, le=300)

    signing_secret: Optional[str] = Field(None, max_length=128)


class WebhookUpdateSchema(BaseModel):
    """Mise a jour d'un webhook."""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

    url: Optional[str] = Field(None, min_length=10, max_length=1000)
    method: Optional[HttpMethod] = None
    headers: Optional[Dict[str, str]] = None

    auth_type: Optional[AuthType] = None
    auth_config: Optional[Dict[str, str]] = None

    event_types: Optional[List[WebhookEventType]] = None
    event_filters: Optional[Dict[str, Any]] = None

    payload_template: Optional[str] = None
    transform_id: Optional[UUID] = None

    max_retries: Optional[int] = Field(None, ge=0, le=10)
    retry_delay_seconds: Optional[int] = Field(None, ge=10, le=3600)
    retry_backoff_multiplier: Optional[Decimal] = Field(None, ge=1, le=10)

    timeout_seconds: Optional[int] = Field(None, ge=5, le=300)

    status: Optional[WebhookStatus] = None


class WebhookResponseSchema(BaseModel):
    """Reponse pour un webhook."""
    id: UUID
    tenant_id: str
    code: str
    name: str
    description: Optional[str]

    url: str
    method: HttpMethod
    headers: Optional[Dict[str, str]]

    auth_type: Optional[AuthType]
    # auth_config omis pour securite

    event_types: List[WebhookEventType]
    event_filters: Optional[Dict[str, Any]]

    max_retries: int
    retry_delay_seconds: int
    timeout_seconds: int

    status: WebhookStatus

    last_triggered_at: Optional[datetime]
    last_success_at: Optional[datetime]
    last_failure_at: Optional[datetime]
    success_count: int
    failure_count: int
    consecutive_failures: int

    version: int
    created_at: datetime
    updated_at: datetime

    @field_validator('headers', 'event_types', 'event_filters', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = ConfigDict(from_attributes=True)


class WebhookTestSchema(BaseModel):
    """Test d'un webhook."""
    event_type: WebhookEventType
    sample_data: Dict[str, Any] = Field(default_factory=dict)


class WebhookTestResponseSchema(BaseModel):
    """Resultat du test d'un webhook."""
    success: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None


class WebhookDeliveryResponseSchema(BaseModel):
    """Reponse pour une livraison de webhook."""
    id: UUID
    webhook_id: UUID
    event_type: WebhookEventType
    event_id: str

    request_url: str
    request_method: HttpMethod

    response_status: Optional[int]
    response_time_ms: Optional[int]

    status: DeliveryStatus
    attempt_number: int
    next_retry_at: Optional[datetime]
    error_message: Optional[str]

    created_at: datetime
    sent_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# RATE LIMITING / QUOTA SCHEMAS
# ============================================================================

class QuotaUsageResponseSchema(BaseModel):
    """Reponse pour l'utilisation des quotas."""
    period: QuotaPeriod
    period_start: datetime
    period_end: datetime

    requests_count: int
    requests_limit: int
    requests_remaining: int
    usage_percentage: float

    bytes_in: int
    bytes_out: int
    error_count: int

    is_exceeded: bool
    exceeded_at: Optional[datetime]

    overage_count: int
    overage_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class RateLimitStatusSchema(BaseModel):
    """Statut du rate limiting."""
    is_throttled: bool
    throttled_until: Optional[datetime]

    rate_limit: int
    rate_limit_remaining: int
    rate_limit_reset: datetime

    window_seconds: int
    strategy: RateLimitStrategy


class CircuitBreakerStatusSchema(BaseModel):
    """Statut du circuit breaker."""
    endpoint_id: UUID
    state: CircuitState

    failure_count: int
    success_count: int
    failure_threshold: int
    success_threshold: int

    last_failure_at: Optional[datetime]
    last_success_at: Optional[datetime]

    opened_at: Optional[datetime]
    half_opened_at: Optional[datetime]
    closed_at: Optional[datetime]

    timeout_seconds: int


# ============================================================================
# METRICS SCHEMAS
# ============================================================================

class RequestLogResponseSchema(BaseModel):
    """Reponse pour un log de requete."""
    id: UUID
    api_key_id: Optional[UUID]

    method: HttpMethod
    path: str
    status_code: int

    client_ip: str
    user_agent: Optional[str]

    request_body_size: int
    response_body_size: int
    response_time_ms: int

    was_throttled: bool
    was_cached: bool

    error_code: Optional[str]
    error_message: Optional[str]

    correlation_id: Optional[str]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class MetricsResponseSchema(BaseModel):
    """Reponse pour les metriques."""
    period_type: str
    period_start: datetime
    period_end: datetime

    total_requests: int
    successful_requests: int
    failed_requests: int
    throttled_requests: int
    cached_requests: int

    success_rate: float
    error_rate: float

    avg_response_time: float
    min_response_time: int
    max_response_time: int
    p50_response_time: int
    p95_response_time: int
    p99_response_time: int

    total_bytes_in: int
    total_bytes_out: int

    error_4xx_count: int
    error_5xx_count: int

    requests_by_status: Optional[Dict[int, int]]
    requests_by_endpoint: Optional[Dict[str, int]]
    requests_by_method: Optional[Dict[str, int]]

    @field_validator('requests_by_status', 'requests_by_endpoint', 'requests_by_method', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = ConfigDict(from_attributes=True)


class MetricsQuerySchema(BaseModel):
    """Parametres de requete pour les metriques."""
    period_type: str = Field(default="hour", pattern=r'^(hour|day|week|month)$')
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    api_key_id: Optional[UUID] = None
    endpoint_id: Optional[UUID] = None


# ============================================================================
# OAUTH SCHEMAS
# ============================================================================

class OAuthClientCreateSchema(BaseModel):
    """Creation d'un client OAuth."""
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

    grant_types: List[str] = Field(default=["client_credentials"])
    redirect_uris: Optional[List[str]] = None
    scopes: Optional[List[str]] = None
    default_scopes: Optional[List[str]] = None

    access_token_lifetime: int = Field(default=3600, ge=60, le=86400)
    refresh_token_lifetime: int = Field(default=86400, ge=3600, le=2592000)

    plan_id: Optional[UUID] = None
    is_confidential: bool = Field(default=True)


class OAuthClientResponseSchema(BaseModel):
    """Reponse pour un client OAuth."""
    id: UUID
    tenant_id: str
    client_id: str
    name: str
    description: Optional[str]

    grant_types: List[str]
    redirect_uris: Optional[List[str]]
    scopes: Optional[List[str]]
    default_scopes: Optional[List[str]]

    access_token_lifetime: int
    refresh_token_lifetime: int

    plan_id: Optional[UUID]
    is_active: bool
    is_confidential: bool

    version: int
    created_at: datetime
    updated_at: datetime

    @field_validator('grant_types', 'redirect_uris', 'scopes', 'default_scopes', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = ConfigDict(from_attributes=True)


class OAuthClientCreatedResponseSchema(OAuthClientResponseSchema):
    """Reponse a la creation d'un client (inclut le secret)."""
    client_secret: str = Field(..., description="Secret client - CONSERVER SECURISEMENT")


class OAuthTokenRequestSchema(BaseModel):
    """Requete de token OAuth."""
    grant_type: str = Field(..., pattern=r'^(client_credentials|authorization_code|refresh_token)$')
    client_id: str
    client_secret: str
    scope: Optional[str] = None
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    refresh_token: Optional[str] = None


class OAuthTokenResponseSchema(BaseModel):
    """Reponse token OAuth."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================

class GatewayStatsSchema(BaseModel):
    """Statistiques du gateway."""
    # Plans et cles
    total_plans: int
    active_plans: int
    total_api_keys: int
    active_api_keys: int

    # Endpoints
    total_endpoints: int
    active_endpoints: int
    deprecated_endpoints: int

    # Webhooks
    total_webhooks: int
    active_webhooks: int
    failed_webhooks: int

    # Trafic (24h)
    requests_24h: int
    successful_requests_24h: int
    failed_requests_24h: int
    throttled_requests_24h: int

    # Performance
    avg_response_time_24h: float
    p95_response_time_24h: float

    # Erreurs
    error_rate_24h: float
    top_errors: List[Dict[str, Any]]

    # Circuit breakers
    open_circuits: int


class GatewayDashboardSchema(BaseModel):
    """Dashboard du gateway."""
    stats: GatewayStatsSchema
    recent_requests: List[RequestLogResponseSchema]
    top_endpoints: List[Dict[str, Any]]
    quota_alerts: List[Dict[str, Any]]
    webhook_failures: List[WebhookDeliveryResponseSchema]


# ============================================================================
# OPENAPI GENERATION SCHEMA
# ============================================================================

class OpenApiGenerationRequestSchema(BaseModel):
    """Requete de generation OpenAPI."""
    title: str = Field(default="AZALSCORE API")
    version: str = Field(default="1.0.0")
    description: Optional[str] = None
    include_deprecated: bool = Field(default=False)
    endpoint_ids: Optional[List[UUID]] = None


class OpenApiSpecResponseSchema(BaseModel):
    """Specification OpenAPI generee."""
    openapi: str = "3.0.3"
    info: Dict[str, Any]
    servers: List[Dict[str, Any]]
    paths: Dict[str, Any]
    components: Dict[str, Any]
    tags: List[Dict[str, Any]]
