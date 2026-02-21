"""
AZALS MODULE GATEWAY - Modeles API Gateway / Integrations
============================================================

Modeles SQLAlchemy pour le systeme d'API Gateway complet:
- Endpoints API personnalises
- Authentification (API keys, OAuth)
- Rate limiting par tenant
- Webhooks sortants
- Transformations donnees
- Retry et circuit breaker
- Monitoring temps reel
- Quotas et facturation

Conformite: tenant_id obligatoire, soft delete, audit complet, version
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.types import UniversalUUID
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class ApiKeyStatus(str, enum.Enum):
    """Statut des cles API."""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class AuthType(str, enum.Enum):
    """Types d'authentification."""
    API_KEY = "API_KEY"
    OAUTH2 = "OAUTH2"
    JWT = "JWT"
    BASIC = "BASIC"
    HMAC = "HMAC"


class RateLimitStrategy(str, enum.Enum):
    """Strategies de rate limiting."""
    FIXED_WINDOW = "FIXED_WINDOW"
    SLIDING_WINDOW = "SLIDING_WINDOW"
    TOKEN_BUCKET = "TOKEN_BUCKET"
    LEAKY_BUCKET = "LEAKY_BUCKET"


class QuotaPeriod(str, enum.Enum):
    """Periodes de quota."""
    MINUTE = "MINUTE"
    HOUR = "HOUR"
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"


class PlanTier(str, enum.Enum):
    """Niveaux de plans API."""
    FREE = "FREE"
    STARTER = "STARTER"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"
    UNLIMITED = "UNLIMITED"


class EndpointType(str, enum.Enum):
    """Types d'endpoints."""
    PUBLIC = "PUBLIC"
    AUTHENTICATED = "AUTHENTICATED"
    INTERNAL = "INTERNAL"
    WEBHOOK = "WEBHOOK"
    PROXY = "PROXY"


class HttpMethod(str, enum.Enum):
    """Methodes HTTP."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class CircuitState(str, enum.Enum):
    """Etat du circuit breaker."""
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class WebhookStatus(str, enum.Enum):
    """Statut des webhooks."""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DISABLED = "DISABLED"
    FAILED = "FAILED"


class WebhookEventType(str, enum.Enum):
    """Types d'evenements webhook."""
    # Generiques
    ENTITY_CREATED = "ENTITY_CREATED"
    ENTITY_UPDATED = "ENTITY_UPDATED"
    ENTITY_DELETED = "ENTITY_DELETED"
    # Finance
    INVOICE_CREATED = "INVOICE_CREATED"
    INVOICE_PAID = "INVOICE_PAID"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    # Commercial
    ORDER_CREATED = "ORDER_CREATED"
    ORDER_COMPLETED = "ORDER_COMPLETED"
    CUSTOMER_CREATED = "CUSTOMER_CREATED"
    # Systeme
    ALERT_TRIGGERED = "ALERT_TRIGGERED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"


class DeliveryStatus(str, enum.Enum):
    """Statut de livraison webhook."""
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


class TransformationType(str, enum.Enum):
    """Types de transformation."""
    JMESPATH = "JMESPATH"
    JSONATA = "JSONATA"
    JINJA2 = "JINJA2"
    MAPPING = "MAPPING"
    SCRIPT = "SCRIPT"


# ============================================================================
# MODELES PRINCIPAUX
# ============================================================================

class GatewayApiPlan(Base):
    """
    Plan API avec quotas et tarification.
    Definit les limites et fonctionnalites pour un niveau d'abonnement.
    """
    __tablename__ = "gateway_api_plans"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    tier = Column(Enum(PlanTier), nullable=False, default=PlanTier.STARTER)

    # Limites de requetes
    requests_per_minute = Column(Integer, nullable=False, default=60)
    requests_per_hour = Column(Integer, nullable=False, default=1000)
    requests_per_day = Column(Integer, nullable=False, default=10000)
    requests_per_month = Column(Integer, nullable=False, default=100000)

    # Burst et concurrence
    burst_limit = Column(Integer, nullable=False, default=10)
    concurrent_connections = Column(Integer, nullable=False, default=10)

    # Taille des donnees
    max_request_size_kb = Column(Integer, nullable=False, default=1024)
    max_response_size_kb = Column(Integer, nullable=False, default=10240)

    # Fonctionnalites
    allowed_endpoints = Column(Text, nullable=True)  # JSON array
    blocked_endpoints = Column(Text, nullable=True)  # JSON array
    allowed_methods = Column(Text, nullable=True)  # JSON array
    features = Column(Text, nullable=True)  # JSON: {"webhooks": true, "analytics": true}

    # Rate limiting
    rate_limit_strategy = Column(
        Enum(RateLimitStrategy),
        nullable=False,
        default=RateLimitStrategy.SLIDING_WINDOW
    )

    # Priorite et timeout
    queue_priority = Column(Integer, nullable=False, default=0)
    timeout_seconds = Column(Integer, nullable=False, default=30)

    # Tarification
    monthly_price = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    overage_price_per_1000 = Column(Numeric(10, 4), nullable=False, default=Decimal("0.00"))

    # Etat
    is_active = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)

    # Soft delete
    deleted_at = Column(DateTime, nullable=True)

    # Version pour optimistic locking
    version = Column(Integer, nullable=False, default=1)

    # Audit
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_by = Column(UniversalUUID(), nullable=True)
    updated_by = Column(UniversalUUID(), nullable=True)

    # Relations
    api_keys = relationship("GatewayApiKey", back_populates="plan", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_gateway_plan_code'),
        Index('idx_gateway_plans_tenant', 'tenant_id'),
        Index('idx_gateway_plans_tier', 'tier'),
        Index('idx_gateway_plans_active', 'is_active'),
        Index('idx_gateway_plans_deleted', 'deleted_at'),
    )


class GatewayApiKey(Base):
    """
    Cle API pour authentification.
    Hash de la cle stocke, jamais en clair.
    """
    __tablename__ = "gateway_api_keys"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    name = Column(String(200), nullable=False)
    key_prefix = Column(String(20), nullable=False)  # Ex: "sk_live_abc..."
    key_hash = Column(String(128), nullable=False)  # SHA-256 hash
    key_hint = Column(String(10), nullable=True)  # Derniers caracteres

    # Association
    plan_id = Column(UniversalUUID(), ForeignKey('gateway_api_plans.id'), nullable=False)
    client_id = Column(String(255), nullable=True, index=True)  # ID client externe
    user_id = Column(UniversalUUID(), nullable=True, index=True)

    # Permissions et restrictions
    scopes = Column(Text, nullable=True)  # JSON array: ["read:orders", "write:invoices"]
    allowed_ips = Column(Text, nullable=True)  # JSON array
    allowed_origins = Column(Text, nullable=True)  # JSON array pour CORS
    allowed_endpoints = Column(Text, nullable=True)  # JSON array

    # Statut
    status = Column(Enum(ApiKeyStatus), nullable=False, default=ApiKeyStatus.ACTIVE)

    # Expiration et utilisation
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    last_used_ip = Column(String(50), nullable=True)
    usage_count = Column(Integer, nullable=False, default=0)

    # Revocation
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(UniversalUUID(), nullable=True)
    revoked_reason = Column(String(500), nullable=True)

    # Metadata
    metadata = Column(Text, nullable=True)  # JSON

    # Soft delete
    deleted_at = Column(DateTime, nullable=True)

    # Version
    version = Column(Integer, nullable=False, default=1)

    # Audit
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_by = Column(UniversalUUID(), nullable=True)

    # Relations
    plan = relationship("GatewayApiPlan", back_populates="api_keys")
    quota_usages = relationship("GatewayQuotaUsage", back_populates="api_key", cascade="all, delete-orphan")
    request_logs = relationship("GatewayRequestLog", back_populates="api_key", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_gateway_keys_tenant', 'tenant_id'),
        Index('idx_gateway_keys_prefix', 'key_prefix'),
        Index('idx_gateway_keys_hash', 'key_hash'),
        Index('idx_gateway_keys_status', 'status'),
        Index('idx_gateway_keys_client', 'client_id'),
        Index('idx_gateway_keys_deleted', 'deleted_at'),
    )


class GatewayEndpoint(Base):
    """
    Configuration d'un endpoint API personnalise.
    Permet de definir des routes avec transformations et rate limiting specifiques.
    """
    __tablename__ = "gateway_endpoints"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Route
    path_pattern = Column(String(500), nullable=False)  # Ex: "/api/v1/orders/*"
    methods = Column(Text, nullable=False)  # JSON array: ["GET", "POST"]
    endpoint_type = Column(Enum(EndpointType), nullable=False, default=EndpointType.AUTHENTICATED)

    # Backend / Proxy
    target_url = Column(String(1000), nullable=True)  # URL du backend
    target_timeout_seconds = Column(Integer, nullable=False, default=30)

    # Authentification
    auth_required = Column(Boolean, nullable=False, default=True)
    auth_type = Column(Enum(AuthType), nullable=True)
    required_scopes = Column(Text, nullable=True)  # JSON array

    # Rate limiting specifique
    custom_rate_limit = Column(Integer, nullable=True)
    custom_window_seconds = Column(Integer, nullable=True)
    rate_limit_key = Column(String(100), nullable=True)  # Ex: "api_key", "ip", "user"

    # Cache
    cache_enabled = Column(Boolean, nullable=False, default=False)
    cache_ttl_seconds = Column(Integer, nullable=False, default=60)
    cache_vary_headers = Column(Text, nullable=True)  # JSON array
    cache_key_template = Column(String(500), nullable=True)

    # Transformation
    request_transform_id = Column(UniversalUUID(), ForeignKey('gateway_transformations.id'), nullable=True)
    response_transform_id = Column(UniversalUUID(), ForeignKey('gateway_transformations.id'), nullable=True)

    # Validation
    request_schema = Column(Text, nullable=True)  # JSON Schema
    require_content_type = Column(String(100), nullable=True)
    max_body_size_kb = Column(Integer, nullable=False, default=1024)

    # Circuit breaker
    circuit_breaker_enabled = Column(Boolean, nullable=False, default=True)
    failure_threshold = Column(Integer, nullable=False, default=5)
    recovery_timeout_seconds = Column(Integer, nullable=False, default=30)
    success_threshold = Column(Integer, nullable=False, default=2)

    # Documentation OpenAPI
    openapi_summary = Column(String(200), nullable=True)
    openapi_description = Column(Text, nullable=True)
    openapi_tags = Column(Text, nullable=True)  # JSON array
    openapi_deprecated = Column(Boolean, nullable=False, default=False)
    openapi_response_schema = Column(Text, nullable=True)  # JSON Schema

    # Etat
    is_active = Column(Boolean, nullable=False, default=True)
    is_deprecated = Column(Boolean, nullable=False, default=False)
    deprecated_message = Column(String(500), nullable=True)
    deprecated_date = Column(DateTime, nullable=True)

    # Soft delete
    deleted_at = Column(DateTime, nullable=True)

    # Version
    version = Column(Integer, nullable=False, default=1)

    # Audit
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_by = Column(UniversalUUID(), nullable=True)
    updated_by = Column(UniversalUUID(), nullable=True)

    # Relations
    request_transform = relationship(
        "GatewayTransformation",
        foreign_keys=[request_transform_id],
        backref="endpoints_request"
    )
    response_transform = relationship(
        "GatewayTransformation",
        foreign_keys=[response_transform_id],
        backref="endpoints_response"
    )
    circuit_breaker = relationship("GatewayCircuitBreaker", back_populates="endpoint", uselist=False)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_gateway_endpoint_code'),
        Index('idx_gateway_endpoints_tenant', 'tenant_id'),
        Index('idx_gateway_endpoints_path', 'path_pattern'),
        Index('idx_gateway_endpoints_type', 'endpoint_type'),
        Index('idx_gateway_endpoints_active', 'is_active'),
        Index('idx_gateway_endpoints_deleted', 'deleted_at'),
    )


class GatewayTransformation(Base):
    """
    Configuration de transformation de donnees.
    Permet de transformer les requetes/reponses.
    """
    __tablename__ = "gateway_transformations"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Type et configuration
    transformation_type = Column(Enum(TransformationType), nullable=False)
    configuration = Column(Text, nullable=False)  # JSON ou expression selon le type

    # Headers
    add_headers = Column(Text, nullable=True)  # JSON: {"X-Custom": "value"}
    remove_headers = Column(Text, nullable=True)  # JSON array
    rename_headers = Column(Text, nullable=True)  # JSON: {"Old-Name": "New-Name"}

    # Body transformation
    body_template = Column(Text, nullable=True)
    content_type_output = Column(String(100), nullable=True)

    # Validation
    input_schema = Column(Text, nullable=True)  # JSON Schema
    output_schema = Column(Text, nullable=True)  # JSON Schema

    # Etat
    is_active = Column(Boolean, nullable=False, default=True)

    # Soft delete
    deleted_at = Column(DateTime, nullable=True)

    # Version
    version = Column(Integer, nullable=False, default=1)

    # Audit
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_gateway_transform_code'),
        Index('idx_gateway_transforms_tenant', 'tenant_id'),
        Index('idx_gateway_transforms_type', 'transformation_type'),
        Index('idx_gateway_transforms_deleted', 'deleted_at'),
    )


class GatewayCircuitBreaker(Base):
    """
    Etat du circuit breaker pour un endpoint.
    """
    __tablename__ = "gateway_circuit_breakers"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Relation
    endpoint_id = Column(UniversalUUID(), ForeignKey('gateway_endpoints.id', ondelete='CASCADE'), nullable=False, unique=True)

    # Etat
    state = Column(Enum(CircuitState), nullable=False, default=CircuitState.CLOSED)

    # Compteurs
    failure_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    total_requests = Column(Integer, nullable=False, default=0)

    # Seuils (herites de l'endpoint mais peuvent etre overrides)
    failure_threshold = Column(Integer, nullable=False, default=5)
    success_threshold = Column(Integer, nullable=False, default=2)
    timeout_seconds = Column(Integer, nullable=False, default=30)

    # Timestamps
    last_failure_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    half_opened_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    # Audit
    updated_at = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relations
    endpoint = relationship("GatewayEndpoint", back_populates="circuit_breaker")

    __table_args__ = (
        Index('idx_gateway_cb_tenant', 'tenant_id'),
        Index('idx_gateway_cb_state', 'state'),
    )


class GatewayQuotaUsage(Base):
    """
    Utilisation des quotas par periode.
    """
    __tablename__ = "gateway_quota_usages"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Relation
    api_key_id = Column(UniversalUUID(), ForeignKey('gateway_api_keys.id', ondelete='CASCADE'), nullable=False)

    # Periode
    period = Column(Enum(QuotaPeriod), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Compteurs
    requests_count = Column(Integer, nullable=False, default=0)
    requests_limit = Column(Integer, nullable=False)
    bytes_in = Column(Integer, nullable=False, default=0)
    bytes_out = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)

    # Etat
    is_exceeded = Column(Boolean, nullable=False, default=False)
    exceeded_at = Column(DateTime, nullable=True)

    # Facturation
    overage_count = Column(Integer, nullable=False, default=0)
    overage_amount = Column(Numeric(10, 4), nullable=False, default=Decimal("0.00"))

    # Relations
    api_key = relationship("GatewayApiKey", back_populates="quota_usages")

    __table_args__ = (
        UniqueConstraint('api_key_id', 'period', 'period_start', name='uq_gateway_quota_period'),
        Index('idx_gateway_quota_tenant', 'tenant_id'),
        Index('idx_gateway_quota_key', 'api_key_id'),
        Index('idx_gateway_quota_period', 'period', 'period_start'),
        Index('idx_gateway_quota_exceeded', 'is_exceeded'),
    )


class GatewayRateLimitState(Base):
    """
    Etat du rate limiting pour une cle/endpoint.
    Utilise pour les strategies token/leaky bucket.
    """
    __tablename__ = "gateway_rate_limit_states"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    api_key_id = Column(UniversalUUID(), nullable=False, index=True)
    endpoint_pattern = Column(String(500), nullable=False)
    rule_id = Column(UniversalUUID(), nullable=True)

    # Fixed/Sliding window
    request_count = Column(Integer, nullable=False, default=0)
    window_start = Column(DateTime, nullable=False)

    # Token bucket
    tokens_remaining = Column(Numeric(10, 2), nullable=False, default=0)
    last_refill = Column(DateTime, nullable=False)

    # Etat
    is_throttled = Column(Boolean, nullable=False, default=False)
    throttled_until = Column(DateTime, nullable=True)

    # Audit
    updated_at = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    __table_args__ = (
        UniqueConstraint('api_key_id', 'endpoint_pattern', name='uq_gateway_ratelimit'),
        Index('idx_gateway_ratelimit_tenant', 'tenant_id'),
        Index('idx_gateway_ratelimit_key', 'api_key_id'),
        Index('idx_gateway_ratelimit_throttled', 'is_throttled'),
    )


class GatewayWebhook(Base):
    """
    Configuration d'un webhook sortant.
    """
    __tablename__ = "gateway_webhooks"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Configuration
    url = Column(String(1000), nullable=False)
    method = Column(Enum(HttpMethod), nullable=False, default=HttpMethod.POST)
    headers = Column(Text, nullable=True)  # JSON

    # Authentification
    auth_type = Column(Enum(AuthType), nullable=True)
    auth_config = Column(Text, nullable=True)  # JSON (chiffre)

    # Evenements
    event_types = Column(Text, nullable=False)  # JSON array
    event_filters = Column(Text, nullable=True)  # JSON: conditions de filtrage

    # Transformation
    payload_template = Column(Text, nullable=True)  # Template Jinja2
    transform_id = Column(UniversalUUID(), ForeignKey('gateway_transformations.id'), nullable=True)

    # Retry
    max_retries = Column(Integer, nullable=False, default=3)
    retry_delay_seconds = Column(Integer, nullable=False, default=60)
    retry_backoff_multiplier = Column(Numeric(3, 1), nullable=False, default=Decimal("2.0"))
    retry_max_delay_seconds = Column(Integer, nullable=False, default=3600)

    # Timeout
    timeout_seconds = Column(Integer, nullable=False, default=30)

    # Signature
    signing_secret = Column(String(128), nullable=True)
    signature_header = Column(String(100), nullable=True, default="X-Signature-256")

    # Statut
    status = Column(Enum(WebhookStatus), nullable=False, default=WebhookStatus.ACTIVE)

    # Stats
    last_triggered_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_failure_at = Column(DateTime, nullable=True)
    success_count = Column(Integer, nullable=False, default=0)
    failure_count = Column(Integer, nullable=False, default=0)
    consecutive_failures = Column(Integer, nullable=False, default=0)

    # Soft delete
    deleted_at = Column(DateTime, nullable=True)

    # Version
    version = Column(Integer, nullable=False, default=1)

    # Audit
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_by = Column(UniversalUUID(), nullable=True)
    updated_by = Column(UniversalUUID(), nullable=True)

    # Relations
    deliveries = relationship("GatewayWebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_gateway_webhook_code'),
        Index('idx_gateway_webhooks_tenant', 'tenant_id'),
        Index('idx_gateway_webhooks_status', 'status'),
        Index('idx_gateway_webhooks_deleted', 'deleted_at'),
    )


class GatewayWebhookDelivery(Base):
    """
    Tentative de livraison d'un webhook.
    """
    __tablename__ = "gateway_webhook_deliveries"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Relations
    webhook_id = Column(UniversalUUID(), ForeignKey('gateway_webhooks.id', ondelete='CASCADE'), nullable=False)

    # Evenement
    event_type = Column(Enum(WebhookEventType), nullable=False)
    event_id = Column(String(100), nullable=False)  # ID de l'evenement source
    event_data = Column(Text, nullable=False)  # JSON payload

    # Requete
    request_url = Column(String(1000), nullable=False)
    request_method = Column(Enum(HttpMethod), nullable=False)
    request_headers = Column(Text, nullable=True)  # JSON
    request_body = Column(Text, nullable=True)

    # Reponse
    response_status = Column(Integer, nullable=True)
    response_headers = Column(Text, nullable=True)  # JSON
    response_body = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    # Statut
    status = Column(Enum(DeliveryStatus), nullable=False, default=DeliveryStatus.PENDING)

    # Retry
    attempt_number = Column(Integer, nullable=False, default=1)
    next_retry_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    sent_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relations
    webhook = relationship("GatewayWebhook", back_populates="deliveries")

    __table_args__ = (
        Index('idx_gateway_delivery_tenant', 'tenant_id'),
        Index('idx_gateway_delivery_webhook', 'webhook_id'),
        Index('idx_gateway_delivery_status', 'status'),
        Index('idx_gateway_delivery_event', 'event_type', 'event_id'),
        Index('idx_gateway_delivery_retry', 'next_retry_at'),
        Index('idx_gateway_delivery_created', 'created_at'),
    )


class GatewayRequestLog(Base):
    """
    Log d'une requete API.
    """
    __tablename__ = "gateway_request_logs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Relation
    api_key_id = Column(UniversalUUID(), ForeignKey('gateway_api_keys.id', ondelete='SET NULL'), nullable=True)
    endpoint_id = Column(UniversalUUID(), nullable=True)

    # Requete
    method = Column(Enum(HttpMethod), nullable=False)
    path = Column(String(2000), nullable=False)
    query_string = Column(Text, nullable=True)
    request_headers = Column(Text, nullable=True)  # JSON (filtre)
    request_body_size = Column(Integer, nullable=False, default=0)
    request_content_type = Column(String(100), nullable=True)

    # Client
    client_ip = Column(String(50), nullable=False)
    user_agent = Column(String(500), nullable=True)
    origin = Column(String(500), nullable=True)

    # Reponse
    status_code = Column(Integer, nullable=False)
    response_body_size = Column(Integer, nullable=False, default=0)
    response_content_type = Column(String(100), nullable=True)
    response_time_ms = Column(Integer, nullable=False)

    # Rate limiting
    rate_limit_remaining = Column(Integer, nullable=True)
    rate_limit_reset = Column(DateTime, nullable=True)
    was_throttled = Column(Boolean, nullable=False, default=False)
    was_cached = Column(Boolean, nullable=False, default=False)

    # Erreur
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    # Correlation
    correlation_id = Column(String(100), nullable=True)
    trace_id = Column(String(100), nullable=True)

    # Timestamp
    timestamp = Column(DateTime, nullable=False, server_default=func.current_timestamp())

    # Relations
    api_key = relationship("GatewayApiKey", back_populates="request_logs")

    __table_args__ = (
        Index('idx_gateway_logs_tenant', 'tenant_id'),
        Index('idx_gateway_logs_key', 'api_key_id'),
        Index('idx_gateway_logs_timestamp', 'timestamp'),
        Index('idx_gateway_logs_path', 'path'),
        Index('idx_gateway_logs_status', 'status_code'),
        Index('idx_gateway_logs_ip', 'client_ip'),
        Index('idx_gateway_logs_correlation', 'correlation_id'),
        Index('idx_gateway_logs_tenant_time', 'tenant_id', 'timestamp'),
    )


class GatewayMetrics(Base):
    """
    Metriques agregees des APIs par periode.
    """
    __tablename__ = "gateway_metrics"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Periode
    period_type = Column(String(20), nullable=False)  # "hour", "day", "month"
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Filtres (optionnels pour aggregation)
    api_key_id = Column(UniversalUUID(), nullable=True)
    endpoint_id = Column(UniversalUUID(), nullable=True)

    # Compteurs
    total_requests = Column(Integer, nullable=False, default=0)
    successful_requests = Column(Integer, nullable=False, default=0)
    failed_requests = Column(Integer, nullable=False, default=0)
    throttled_requests = Column(Integer, nullable=False, default=0)
    cached_requests = Column(Integer, nullable=False, default=0)

    # Performance (en ms)
    avg_response_time = Column(Numeric(10, 2), nullable=False, default=0)
    min_response_time = Column(Integer, nullable=False, default=0)
    max_response_time = Column(Integer, nullable=False, default=0)
    p50_response_time = Column(Integer, nullable=False, default=0)
    p95_response_time = Column(Integer, nullable=False, default=0)
    p99_response_time = Column(Integer, nullable=False, default=0)

    # Volume
    total_bytes_in = Column(Integer, nullable=False, default=0)
    total_bytes_out = Column(Integer, nullable=False, default=0)

    # Erreurs
    error_4xx_count = Column(Integer, nullable=False, default=0)
    error_5xx_count = Column(Integer, nullable=False, default=0)

    # Par status (JSON)
    requests_by_status = Column(Text, nullable=True)

    # Par endpoint (JSON)
    requests_by_endpoint = Column(Text, nullable=True)

    # Par methode (JSON)
    requests_by_method = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'period_type', 'period_start', 'api_key_id', 'endpoint_id', name='uq_gateway_metrics'),
        Index('idx_gateway_metrics_tenant', 'tenant_id'),
        Index('idx_gateway_metrics_period', 'period_type', 'period_start'),
        Index('idx_gateway_metrics_key', 'api_key_id'),
        Index('idx_gateway_metrics_endpoint', 'endpoint_id'),
    )


class GatewayOAuthClient(Base):
    """
    Client OAuth2 pour authentification.
    """
    __tablename__ = "gateway_oauth_clients"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    client_id = Column(String(100), nullable=False, unique=True)
    client_secret_hash = Column(String(128), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Configuration OAuth2
    grant_types = Column(Text, nullable=False)  # JSON array: ["authorization_code", "client_credentials"]
    redirect_uris = Column(Text, nullable=True)  # JSON array
    scopes = Column(Text, nullable=True)  # JSON array
    default_scopes = Column(Text, nullable=True)  # JSON array

    # Tokens
    access_token_lifetime = Column(Integer, nullable=False, default=3600)
    refresh_token_lifetime = Column(Integer, nullable=False, default=86400)
    token_type = Column(String(20), nullable=False, default="Bearer")

    # Association plan
    plan_id = Column(UniversalUUID(), ForeignKey('gateway_api_plans.id'), nullable=True)

    # Etat
    is_active = Column(Boolean, nullable=False, default=True)
    is_confidential = Column(Boolean, nullable=False, default=True)

    # Soft delete
    deleted_at = Column(DateTime, nullable=True)

    # Version
    version = Column(Integer, nullable=False, default=1)

    # Audit
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_by = Column(UniversalUUID(), nullable=True)

    # Relations
    tokens = relationship("GatewayOAuthToken", back_populates="client", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_gateway_oauth_tenant', 'tenant_id'),
        Index('idx_gateway_oauth_client_id', 'client_id'),
        Index('idx_gateway_oauth_active', 'is_active'),
        Index('idx_gateway_oauth_deleted', 'deleted_at'),
    )


class GatewayOAuthToken(Base):
    """
    Token OAuth2.
    """
    __tablename__ = "gateway_oauth_tokens"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Relations
    client_id = Column(UniversalUUID(), ForeignKey('gateway_oauth_clients.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UniversalUUID(), nullable=True)

    # Tokens
    access_token_hash = Column(String(128), nullable=False, unique=True)
    refresh_token_hash = Column(String(128), nullable=True, unique=True)
    token_type = Column(String(20), nullable=False, default="Bearer")

    # Scopes
    scopes = Column(Text, nullable=True)  # JSON array

    # Expiration
    access_token_expires_at = Column(DateTime, nullable=False)
    refresh_token_expires_at = Column(DateTime, nullable=True)

    # Etat
    is_revoked = Column(Boolean, nullable=False, default=False)
    revoked_at = Column(DateTime, nullable=True)

    # Audit
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    last_used_at = Column(DateTime, nullable=True)

    # Relations
    client = relationship("GatewayOAuthClient", back_populates="tokens")

    __table_args__ = (
        Index('idx_gateway_token_tenant', 'tenant_id'),
        Index('idx_gateway_token_client', 'client_id'),
        Index('idx_gateway_token_access', 'access_token_hash'),
        Index('idx_gateway_token_refresh', 'refresh_token_hash'),
        Index('idx_gateway_token_expires', 'access_token_expires_at'),
    )


class GatewayAuditLog(Base):
    """
    Journal d'audit des operations Gateway.
    APPEND-ONLY - Aucune modification/suppression.
    """
    __tablename__ = "gateway_audit_logs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Action
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UniversalUUID(), nullable=True)

    # Acteur
    user_id = Column(UniversalUUID(), nullable=True)
    api_key_id = Column(UniversalUUID(), nullable=True)
    ip_address = Column(String(50), nullable=True)

    # Details
    old_values = Column(Text, nullable=True)  # JSON
    new_values = Column(Text, nullable=True)  # JSON
    details = Column(Text, nullable=True)  # JSON

    # Resultat
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)

    # Correlation
    correlation_id = Column(String(100), nullable=True)

    # Timestamp
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())

    __table_args__ = (
        Index('idx_gateway_audit_tenant', 'tenant_id'),
        Index('idx_gateway_audit_action', 'action'),
        Index('idx_gateway_audit_entity', 'entity_type', 'entity_id'),
        Index('idx_gateway_audit_user', 'user_id'),
        Index('idx_gateway_audit_created', 'created_at'),
        Index('idx_gateway_audit_tenant_time', 'tenant_id', 'created_at'),
    )
