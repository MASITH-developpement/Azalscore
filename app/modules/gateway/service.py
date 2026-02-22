"""
AZALS MODULE GATEWAY - Service Principal
==========================================

Service metier complet pour API Gateway / Integrations:
- Gestion des plans et cles API
- Rate limiting multi-strategies
- Circuit breaker pattern
- Webhooks sortants avec retry
- Transformations de donnees
- Metriques et monitoring
- Generation OpenAPI

Conformite: BaseService pattern avec Result
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import httpx
from sqlalchemy.orm import Session

from app.core.base_service import BaseService
from app.core.saas_context import Result, SaaSContext

from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    BackendConnectionError,
    BackendTimeoutError,
    CircuitOpenError,
    DuplicateResourceError,
    EndpointNotAllowedError,
    ExpiredApiKeyError,
    InsufficientScopeError,
    InvalidApiKeyError,
    IpNotAllowedError,
    QuotaExceededError,
    RateLimitError,
    ResourceNotFoundError,
    RevokedApiKeyError,
    SuspendedApiKeyError,
    TransformationError,
    WebhookDeliveryError,
    WebhookTimeoutError,
)
from .models import (
    ApiKeyStatus,
    AuthType,
    CircuitState,
    DeliveryStatus,
    EndpointType,
    GatewayApiKey,
    GatewayApiPlan,
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
    HttpMethod,
    PlanTier,
    QuotaPeriod,
    RateLimitStrategy,
    TransformationType,
    WebhookEventType,
    WebhookStatus,
)
from .repository import (
    ApiKeyRepository,
    ApiPlanRepository,
    AuditLogRepository,
    CircuitBreakerRepository,
    EndpointRepository,
    MetricsRepository,
    OAuthClientRepository,
    OAuthTokenRepository,
    QuotaUsageRepository,
    RateLimitStateRepository,
    RequestLogRepository,
    TransformationRepository,
    WebhookDeliveryRepository,
    WebhookRepository,
)
from .schemas import (
    ApiKeyCreateSchema,
    ApiKeyUpdateSchema,
    ApiPlanCreateSchema,
    ApiPlanUpdateSchema,
    EndpointCreateSchema,
    EndpointUpdateSchema,
    OAuthClientCreateSchema,
    TransformationCreateSchema,
    TransformationUpdateSchema,
    WebhookCreateSchema,
    WebhookUpdateSchema,
)

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES INTERNES
# ============================================================================

@dataclass
class ThrottleDecision:
    """Decision de throttling."""
    allowed: bool
    action: str = "ALLOW"  # ALLOW, DELAY, REJECT
    delay_ms: int = 0
    retry_after_seconds: int = 0
    reason: Optional[str] = None
    rate_limit: int = 0
    rate_limit_remaining: int = 0
    rate_limit_reset: Optional[datetime] = None


@dataclass
class RequestContext:
    """Contexte d'une requete API."""
    api_key: Optional[GatewayApiKey]
    plan: Optional[GatewayApiPlan]
    endpoint: Optional[GatewayEndpoint]
    method: HttpMethod
    path: str
    client_ip: str
    user_agent: Optional[str] = None
    origin: Optional[str] = None
    correlation_id: Optional[str] = None
    start_time: Optional[datetime] = None


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class GatewayService:
    """
    Service principal du module Gateway.

    Gere:
    - Plans API et quotas
    - Cles API avec authentification
    - Rate limiting multi-strategies
    - Circuit breaker
    - Webhooks sortants
    - Metriques et logs
    """

    def __init__(self, db: Session, context: SaaSContext):
        self.db = db
        self.context = context
        self.tenant_id = context.tenant_id
        self.user_id = context.user_id

        # Repositories
        self._plan_repo = ApiPlanRepository(db, self.tenant_id)
        self._key_repo = ApiKeyRepository(db, self.tenant_id)
        self._endpoint_repo = EndpointRepository(db, self.tenant_id)
        self._transform_repo = TransformationRepository(db, self.tenant_id)
        self._webhook_repo = WebhookRepository(db, self.tenant_id)
        self._delivery_repo = WebhookDeliveryRepository(db, self.tenant_id)
        self._quota_repo = QuotaUsageRepository(db, self.tenant_id)
        self._ratelimit_repo = RateLimitStateRepository(db, self.tenant_id)
        self._circuit_repo = CircuitBreakerRepository(db, self.tenant_id)
        self._log_repo = RequestLogRepository(db, self.tenant_id)
        self._metrics_repo = MetricsRepository(db, self.tenant_id)
        self._oauth_client_repo = OAuthClientRepository(db, self.tenant_id)
        self._oauth_token_repo = OAuthTokenRepository(db, self.tenant_id)
        self._audit_repo = AuditLogRepository(db, self.tenant_id)

        # Logger
        self._logger = logging.LoggerAdapter(
            logger,
            extra={
                "service": "GatewayService",
                "tenant_id": self.tenant_id,
                "user_id": str(self.user_id)
            }
        )

    # ========================================================================
    # GESTION DES PLANS API
    # ========================================================================

    def create_plan(self, data: ApiPlanCreateSchema) -> Result[GatewayApiPlan]:
        """Cree un plan API."""
        # Verifier l'unicite du code
        existing = self._plan_repo.get_by_code(data.code)
        if existing:
            return Result.fail(
                f"Plan avec code '{data.code}' existe deja",
                error_code="DUPLICATE"
            )

        plan = GatewayApiPlan(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            tier=data.tier,
            requests_per_minute=data.requests_per_minute,
            requests_per_hour=data.requests_per_hour,
            requests_per_day=data.requests_per_day,
            requests_per_month=data.requests_per_month,
            burst_limit=data.burst_limit,
            concurrent_connections=data.concurrent_connections,
            max_request_size_kb=data.max_request_size_kb,
            max_response_size_kb=data.max_response_size_kb,
            rate_limit_strategy=data.rate_limit_strategy,
            timeout_seconds=data.timeout_seconds,
            monthly_price=data.monthly_price,
            overage_price_per_1000=data.overage_price_per_1000,
            features=json.dumps(data.features) if data.features else None,
            allowed_endpoints=json.dumps(data.allowed_endpoints) if data.allowed_endpoints else None,
            blocked_endpoints=json.dumps(data.blocked_endpoints) if data.blocked_endpoints else None,
            created_by=self.user_id
        )

        created = self._plan_repo.create(plan)

        self._audit_repo.log_action(
            action="CREATE_PLAN",
            entity_type="GatewayApiPlan",
            entity_id=created.id,
            user_id=self.user_id,
            new_values={"code": data.code, "tier": data.tier.value}
        )

        self._logger.info(f"Plan API cree: {data.code}")
        return Result.ok(created)

    def get_plan(self, plan_id: UUID) -> Result[GatewayApiPlan]:
        """Recupere un plan par ID."""
        plan = self._plan_repo.get_active(plan_id)
        if not plan:
            return Result.fail(f"Plan non trouve: {plan_id}", error_code="NOT_FOUND")
        return Result.ok(plan)

    def update_plan(self, plan_id: UUID, data: ApiPlanUpdateSchema) -> Result[GatewayApiPlan]:
        """Met a jour un plan."""
        plan = self._plan_repo.get_active(plan_id)
        if not plan:
            return Result.fail(f"Plan non trouve: {plan_id}", error_code="NOT_FOUND")

        old_values = {"tier": plan.tier.value, "name": plan.name}

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field in ('features', 'allowed_endpoints', 'blocked_endpoints') and value is not None:
                value = json.dumps(value)
            if hasattr(plan, field):
                setattr(plan, field, value)

        plan.updated_by = self.user_id
        plan.version += 1

        updated = self._plan_repo.update(plan)

        self._audit_repo.log_action(
            action="UPDATE_PLAN",
            entity_type="GatewayApiPlan",
            entity_id=plan_id,
            user_id=self.user_id,
            old_values=old_values,
            new_values=update_data
        )

        return Result.ok(updated)

    def delete_plan(self, plan_id: UUID) -> Result[bool]:
        """Supprime un plan (soft delete)."""
        plan = self._plan_repo.get_active(plan_id)
        if not plan:
            return Result.fail(f"Plan non trouve: {plan_id}", error_code="NOT_FOUND")

        # Verifier qu'il n'y a pas de cles actives
        keys = self._key_repo.list_by_plan(plan_id)
        active_keys = [k for k in keys if k.status == ApiKeyStatus.ACTIVE and k.deleted_at is None]
        if active_keys:
            return Result.fail(
                f"Plan a {len(active_keys)} cles actives",
                error_code="CONFLICT"
            )

        success = self._plan_repo.soft_delete(plan_id, self.user_id)

        if success:
            self._audit_repo.log_action(
                action="DELETE_PLAN",
                entity_type="GatewayApiPlan",
                entity_id=plan_id,
                user_id=self.user_id
            )

        return Result.ok(success)

    def list_plans(
        self,
        tier: Optional[PlanTier] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Result[Tuple[List[GatewayApiPlan], int]]:
        """Liste les plans."""
        plans = self._plan_repo.list_active(tier.value if tier else None)
        total = len(plans)

        # Pagination manuelle
        start = (page - 1) * page_size
        end = start + page_size
        paginated = plans[start:end]

        return Result.ok((paginated, total))

    # ========================================================================
    # GESTION DES CLES API
    # ========================================================================

    def create_api_key(self, data: ApiKeyCreateSchema) -> Result[Tuple[GatewayApiKey, str]]:
        """
        Cree une cle API.
        Retourne la cle et la valeur complete (a afficher UNE SEULE FOIS).
        """
        # Verifier le plan
        plan = self._plan_repo.get_active(data.plan_id)
        if not plan:
            return Result.fail(f"Plan non trouve: {data.plan_id}", error_code="NOT_FOUND")

        # Generer la cle
        raw_key = secrets.token_urlsafe(32)
        prefix = f"sk_{'live' if data.is_live else 'test'}_{secrets.token_hex(4)}"
        full_key = f"{prefix}_{raw_key}"
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        key_hint = full_key[-4:]

        api_key = GatewayApiKey(
            tenant_id=self.tenant_id,
            name=data.name,
            key_prefix=prefix,
            key_hash=key_hash,
            key_hint=key_hint,
            plan_id=data.plan_id,
            client_id=data.client_id,
            user_id=data.user_id,
            scopes=json.dumps(data.scopes) if data.scopes else None,
            allowed_ips=json.dumps(data.allowed_ips) if data.allowed_ips else None,
            allowed_origins=json.dumps(data.allowed_origins) if data.allowed_origins else None,
            allowed_endpoints=json.dumps(data.allowed_endpoints) if data.allowed_endpoints else None,
            expires_at=data.expires_at,
            extra_data=json.dumps(data.metadata) if data.metadata else None,
            created_by=self.user_id
        )

        created = self._key_repo.create(api_key)

        # Initialiser les quotas
        self._initialize_quotas_for_key(created.id, plan)

        self._audit_repo.log_action(
            action="CREATE_API_KEY",
            entity_type="GatewayApiKey",
            entity_id=created.id,
            user_id=self.user_id,
            new_values={
                "name": data.name,
                "plan_id": str(data.plan_id),
                "client_id": data.client_id
            }
        )

        self._logger.info(f"Cle API creee: {prefix}")
        return Result.ok((created, full_key))

    def _initialize_quotas_for_key(self, api_key_id: UUID, plan: GatewayApiPlan) -> None:
        """Initialise les quotas pour une cle."""
        periods = [
            (QuotaPeriod.MINUTE, plan.requests_per_minute),
            (QuotaPeriod.HOUR, plan.requests_per_hour),
            (QuotaPeriod.DAY, plan.requests_per_day),
            (QuotaPeriod.MONTH, plan.requests_per_month),
        ]

        for period, limit in periods:
            self._quota_repo.get_or_create_current(api_key_id, period, limit)

    def validate_api_key(self, raw_key: str) -> Result[GatewayApiKey]:
        """
        Valide une cle API.
        Retourne la cle si valide.
        """
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = self._key_repo.get_by_hash(key_hash)

        if not api_key:
            return Result.fail("Cle API invalide", error_code="INVALID_API_KEY")

        # Verifier le statut
        if api_key.status == ApiKeyStatus.REVOKED:
            return Result.fail("Cle API revoquee", error_code="REVOKED_API_KEY")

        if api_key.status == ApiKeyStatus.SUSPENDED:
            return Result.fail("Cle API suspendue", error_code="SUSPENDED_API_KEY")

        if api_key.status == ApiKeyStatus.EXPIRED:
            return Result.fail("Cle API expiree", error_code="EXPIRED_API_KEY")

        # Verifier l'expiration
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            api_key.status = ApiKeyStatus.EXPIRED
            self.db.commit()
            return Result.fail("Cle API expiree", error_code="EXPIRED_API_KEY")

        return Result.ok(api_key)

    def get_api_key(self, key_id: UUID) -> Result[GatewayApiKey]:
        """Recupere une cle par ID."""
        api_key = self._key_repo.get_active(key_id)
        if not api_key:
            return Result.fail(f"Cle non trouvee: {key_id}", error_code="NOT_FOUND")
        return Result.ok(api_key)

    def update_api_key(self, key_id: UUID, data: ApiKeyUpdateSchema) -> Result[GatewayApiKey]:
        """Met a jour une cle."""
        api_key = self._key_repo.get_active(key_id)
        if not api_key:
            return Result.fail(f"Cle non trouvee: {key_id}", error_code="NOT_FOUND")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field in ('scopes', 'allowed_ips', 'allowed_origins', 'allowed_endpoints', 'metadata') and value is not None:
                value = json.dumps(value)
            if hasattr(api_key, field):
                setattr(api_key, field, value)

        api_key.version += 1
        updated = self._key_repo.update(api_key)

        self._audit_repo.log_action(
            action="UPDATE_API_KEY",
            entity_type="GatewayApiKey",
            entity_id=key_id,
            user_id=self.user_id,
            new_values=update_data
        )

        return Result.ok(updated)

    def revoke_api_key(self, key_id: UUID, reason: Optional[str] = None) -> Result[bool]:
        """Revoque une cle API."""
        api_key = self._key_repo.get_active(key_id)
        if not api_key:
            return Result.fail(f"Cle non trouvee: {key_id}", error_code="NOT_FOUND")

        api_key.status = ApiKeyStatus.REVOKED
        api_key.revoked_at = datetime.utcnow()
        api_key.revoked_by = self.user_id
        api_key.revoked_reason = reason
        api_key.version += 1

        self.db.commit()

        self._audit_repo.log_action(
            action="REVOKE_API_KEY",
            entity_type="GatewayApiKey",
            entity_id=key_id,
            user_id=self.user_id,
            details={"reason": reason}
        )

        self._logger.info(f"Cle API revoquee: {api_key.key_prefix}")
        return Result.ok(True)

    def list_api_keys(
        self,
        client_id: Optional[str] = None,
        user_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Result[Tuple[List[GatewayApiKey], int]]:
        """Liste les cles API."""
        skip = (page - 1) * page_size
        keys, total = self._key_repo.list_active(
            client_id=client_id,
            user_id=user_id,
            skip=skip,
            limit=page_size
        )
        return Result.ok((keys, total))

    # ========================================================================
    # RATE LIMITING
    # ========================================================================

    def check_rate_limit(
        self,
        api_key: GatewayApiKey,
        endpoint: Optional[GatewayEndpoint],
        method: HttpMethod
    ) -> ThrottleDecision:
        """
        Verifie le rate limiting pour une requete.
        Utilise la strategie du plan.
        """
        plan = self._plan_repo.get_active(api_key.plan_id)
        if not plan:
            return ThrottleDecision(allowed=False, action="REJECT", reason="Plan not found")

        # Determiner le pattern
        endpoint_pattern = endpoint.path_pattern if endpoint else "*"

        # Obtenir ou creer l'etat
        state = self._ratelimit_repo.get_or_create_state(
            api_key.id,
            endpoint_pattern,
            float(plan.requests_per_minute)
        )

        # Appliquer la strategie
        if plan.rate_limit_strategy == RateLimitStrategy.FIXED_WINDOW:
            return self._check_fixed_window(state, plan)
        elif plan.rate_limit_strategy == RateLimitStrategy.SLIDING_WINDOW:
            return self._check_sliding_window(state, plan)
        elif plan.rate_limit_strategy == RateLimitStrategy.TOKEN_BUCKET:
            return self._check_token_bucket(state, plan)
        elif plan.rate_limit_strategy == RateLimitStrategy.LEAKY_BUCKET:
            return self._check_leaky_bucket(state, plan)

        return ThrottleDecision(allowed=True, action="ALLOW")

    def _check_fixed_window(
        self,
        state: GatewayRateLimitState,
        plan: GatewayApiPlan
    ) -> ThrottleDecision:
        """Strategie fenetre fixe."""
        now = datetime.utcnow()
        window_end = state.window_start + timedelta(seconds=60)  # 1 minute window

        # Nouvelle fenetre?
        if now >= window_end:
            state.window_start = now
            state.request_count = 0

        # Verifier la limite
        if state.request_count >= plan.requests_per_minute:
            retry_after = int((window_end - now).total_seconds())
            return ThrottleDecision(
                allowed=False,
                action="REJECT",
                retry_after_seconds=max(1, retry_after),
                reason="Rate limit exceeded",
                rate_limit=plan.requests_per_minute,
                rate_limit_remaining=0,
                rate_limit_reset=window_end
            )

        # Incrementer
        state.request_count += 1
        self.db.commit()

        return ThrottleDecision(
            allowed=True,
            action="ALLOW",
            rate_limit=plan.requests_per_minute,
            rate_limit_remaining=plan.requests_per_minute - state.request_count,
            rate_limit_reset=window_end
        )

    def _check_sliding_window(
        self,
        state: GatewayRateLimitState,
        plan: GatewayApiPlan
    ) -> ThrottleDecision:
        """Strategie fenetre glissante."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=60)

        # Compter les requetes dans la fenetre
        current_count = state.request_count

        if state.window_start < window_start:
            # Recalculer proportionnellement
            elapsed = (now - state.window_start).total_seconds()
            if elapsed > 0:
                decay_ratio = max(0, 1 - (elapsed / 60))
                current_count = int(state.request_count * decay_ratio)

        # Verifier la limite
        if current_count >= plan.requests_per_minute:
            return ThrottleDecision(
                allowed=False,
                action="REJECT",
                retry_after_seconds=1,
                reason="Rate limit exceeded (sliding window)",
                rate_limit=plan.requests_per_minute,
                rate_limit_remaining=0
            )

        # Mettre a jour
        state.request_count = current_count + 1
        state.window_start = now
        self.db.commit()

        return ThrottleDecision(
            allowed=True,
            action="ALLOW",
            rate_limit=plan.requests_per_minute,
            rate_limit_remaining=max(0, plan.requests_per_minute - state.request_count)
        )

    def _check_token_bucket(
        self,
        state: GatewayRateLimitState,
        plan: GatewayApiPlan
    ) -> ThrottleDecision:
        """Strategie token bucket."""
        now = datetime.utcnow()

        # Calculer les tokens a ajouter
        elapsed = (now - state.last_refill).total_seconds()
        refill_rate = plan.requests_per_minute / 60.0  # tokens par seconde
        tokens_to_add = elapsed * refill_rate

        # Mettre a jour les tokens
        max_tokens = plan.burst_limit
        state.tokens_remaining = min(
            Decimal(str(max_tokens)),
            Decimal(str(float(state.tokens_remaining) + tokens_to_add))
        )
        state.last_refill = now

        # Verifier si on peut consommer un token
        if state.tokens_remaining < 1:
            wait_time = (1 - float(state.tokens_remaining)) / refill_rate
            return ThrottleDecision(
                allowed=False,
                action="REJECT",
                retry_after_seconds=int(wait_time) + 1,
                reason="Rate limit exceeded (token bucket)",
                rate_limit=plan.requests_per_minute,
                rate_limit_remaining=0
            )

        # Consommer un token
        state.tokens_remaining = state.tokens_remaining - 1
        self.db.commit()

        return ThrottleDecision(
            allowed=True,
            action="ALLOW",
            rate_limit=plan.requests_per_minute,
            rate_limit_remaining=int(state.tokens_remaining)
        )

    def _check_leaky_bucket(
        self,
        state: GatewayRateLimitState,
        plan: GatewayApiPlan
    ) -> ThrottleDecision:
        """Strategie leaky bucket (ajoute un delai)."""
        now = datetime.utcnow()

        # Calculer le "niveau" du bucket
        elapsed = (now - state.last_refill).total_seconds()
        leak_rate = plan.requests_per_minute / 60.0

        leaked = elapsed * leak_rate
        state.tokens_remaining = max(
            Decimal(0),
            Decimal(str(float(state.tokens_remaining) - leaked))
        )
        state.last_refill = now

        max_bucket = plan.burst_limit

        if float(state.tokens_remaining) >= max_bucket:
            return ThrottleDecision(
                allowed=False,
                action="REJECT",
                reason="Rate limit exceeded (leaky bucket full)",
                rate_limit=plan.requests_per_minute,
                rate_limit_remaining=0
            )

        # Calculer le delai
        delay_ms = 0
        if float(state.tokens_remaining) > 0:
            delay_ms = int((float(state.tokens_remaining) / leak_rate) * 1000)

        state.tokens_remaining = state.tokens_remaining + 1
        self.db.commit()

        if delay_ms > 0 and delay_ms < 5000:  # Max 5 secondes de delai
            return ThrottleDecision(
                allowed=True,
                action="DELAY",
                delay_ms=delay_ms,
                rate_limit=plan.requests_per_minute,
                rate_limit_remaining=int(max_bucket - float(state.tokens_remaining))
            )

        return ThrottleDecision(
            allowed=True,
            action="ALLOW",
            rate_limit=plan.requests_per_minute,
            rate_limit_remaining=int(max_bucket - float(state.tokens_remaining))
        )

    def check_quota(
        self,
        api_key: GatewayApiKey,
        plan: GatewayApiPlan
    ) -> Result[Dict[QuotaPeriod, GatewayQuotaUsage]]:
        """Verifie les quotas pour toutes les periodes."""
        quotas = {}
        exceeded = None

        periods = [
            (QuotaPeriod.MINUTE, plan.requests_per_minute),
            (QuotaPeriod.HOUR, plan.requests_per_hour),
            (QuotaPeriod.DAY, plan.requests_per_day),
            (QuotaPeriod.MONTH, plan.requests_per_month),
        ]

        for period, limit in periods:
            quota = self._quota_repo.get_or_create_current(api_key.id, period, limit)
            quotas[period] = quota

            if quota.is_exceeded and exceeded is None:
                exceeded = (period, quota)

        if exceeded:
            period, quota = exceeded
            return Result.fail(
                f"Quota depasse pour {period.value}: {quota.requests_count}/{quota.requests_limit}",
                error_code="QUOTA_EXCEEDED"
            )

        return Result.ok(quotas)

    def increment_quota(
        self,
        api_key_id: UUID,
        bytes_in: int = 0,
        bytes_out: int = 0,
        is_error: bool = False
    ) -> None:
        """Incremente l'utilisation des quotas."""
        plan = None
        api_key = self._key_repo.get_by_id(api_key_id)
        if api_key:
            plan = self._plan_repo.get_active(api_key.plan_id)

        if not plan:
            return

        periods = [
            (QuotaPeriod.MINUTE, plan.requests_per_minute),
            (QuotaPeriod.HOUR, plan.requests_per_hour),
            (QuotaPeriod.DAY, plan.requests_per_day),
            (QuotaPeriod.MONTH, plan.requests_per_month),
        ]

        for period, limit in periods:
            self._quota_repo.increment_usage(
                api_key_id, period, limit, bytes_in, bytes_out, is_error
            )

    # ========================================================================
    # CIRCUIT BREAKER
    # ========================================================================

    def get_circuit_state(self, endpoint: GatewayEndpoint) -> GatewayCircuitBreaker:
        """Recupere l'etat du circuit breaker."""
        cb = self._circuit_repo.get_or_create(
            endpoint.id,
            endpoint.failure_threshold,
            endpoint.success_threshold,
            endpoint.recovery_timeout_seconds
        )

        # Verifier la transition half-open
        now = datetime.utcnow()
        if cb.state == CircuitState.OPEN and cb.opened_at:
            if (now - cb.opened_at).total_seconds() >= cb.timeout_seconds:
                cb.state = CircuitState.HALF_OPEN
                cb.half_opened_at = now
                self.db.commit()

        return cb

    def is_circuit_open(self, endpoint: GatewayEndpoint) -> bool:
        """Verifie si le circuit est ouvert."""
        if not endpoint.circuit_breaker_enabled:
            return False

        cb = self.get_circuit_state(endpoint)
        return cb.state == CircuitState.OPEN

    def record_circuit_success(self, endpoint: GatewayEndpoint) -> None:
        """Enregistre un succes."""
        if not endpoint.circuit_breaker_enabled:
            return

        cb = self.get_circuit_state(endpoint)
        now = datetime.utcnow()

        if cb.state == CircuitState.HALF_OPEN:
            cb.success_count += 1
            cb.last_success_at = now
            if cb.success_count >= cb.success_threshold:
                cb.state = CircuitState.CLOSED
                cb.closed_at = now
                cb.failure_count = 0
                cb.success_count = 0
        elif cb.state == CircuitState.CLOSED:
            cb.failure_count = 0
            cb.last_success_at = now

        cb.total_requests += 1
        self.db.commit()

    def record_circuit_failure(self, endpoint: GatewayEndpoint) -> None:
        """Enregistre un echec."""
        if not endpoint.circuit_breaker_enabled:
            return

        cb = self.get_circuit_state(endpoint)
        now = datetime.utcnow()

        cb.failure_count += 1
        cb.last_failure_at = now
        cb.total_requests += 1

        if cb.state == CircuitState.HALF_OPEN:
            cb.state = CircuitState.OPEN
            cb.opened_at = now
            cb.success_count = 0
        elif cb.state == CircuitState.CLOSED:
            if cb.failure_count >= cb.failure_threshold:
                cb.state = CircuitState.OPEN
                cb.opened_at = now

        self.db.commit()

        if cb.state == CircuitState.OPEN:
            self._logger.warning(
                f"Circuit ouvert pour endpoint {endpoint.code}",
                extra={"endpoint_id": str(endpoint.id), "failures": cb.failure_count}
            )

    # ========================================================================
    # ENDPOINTS
    # ========================================================================

    def create_endpoint(self, data: EndpointCreateSchema) -> Result[GatewayEndpoint]:
        """Cree un endpoint."""
        existing = self._endpoint_repo.get_by_code(data.code)
        if existing:
            return Result.fail(f"Endpoint '{data.code}' existe deja", error_code="DUPLICATE")

        endpoint = GatewayEndpoint(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            path_pattern=data.path_pattern,
            methods=json.dumps([m.value for m in data.methods]),
            endpoint_type=data.endpoint_type,
            target_url=data.target_url,
            target_timeout_seconds=data.target_timeout_seconds,
            auth_required=data.auth_required,
            auth_type=data.auth_type,
            required_scopes=json.dumps(data.required_scopes) if data.required_scopes else None,
            custom_rate_limit=data.custom_rate_limit,
            custom_window_seconds=data.custom_window_seconds,
            cache_enabled=data.cache_enabled,
            cache_ttl_seconds=data.cache_ttl_seconds,
            cache_vary_headers=json.dumps(data.cache_vary_headers) if data.cache_vary_headers else None,
            request_transform_id=data.request_transform_id,
            response_transform_id=data.response_transform_id,
            request_schema=json.dumps(data.request_schema) if data.request_schema else None,
            max_body_size_kb=data.max_body_size_kb,
            circuit_breaker_enabled=data.circuit_breaker_enabled,
            failure_threshold=data.failure_threshold,
            recovery_timeout_seconds=data.recovery_timeout_seconds,
            openapi_summary=data.openapi_summary,
            openapi_description=data.openapi_description,
            openapi_tags=json.dumps(data.openapi_tags) if data.openapi_tags else None,
            created_by=self.user_id
        )

        created = self._endpoint_repo.create(endpoint)

        self._audit_repo.log_action(
            action="CREATE_ENDPOINT",
            entity_type="GatewayEndpoint",
            entity_id=created.id,
            user_id=self.user_id,
            new_values={"code": data.code, "path_pattern": data.path_pattern}
        )

        return Result.ok(created)

    def get_endpoint(self, endpoint_id: UUID) -> Result[GatewayEndpoint]:
        """Recupere un endpoint."""
        endpoint = self._endpoint_repo.get_active(endpoint_id)
        if not endpoint:
            return Result.fail(f"Endpoint non trouve: {endpoint_id}", error_code="NOT_FOUND")
        return Result.ok(endpoint)

    def find_endpoint_by_path(self, path: str) -> Optional[GatewayEndpoint]:
        """Trouve un endpoint par son chemin."""
        return self._endpoint_repo.find_by_path(path)

    def update_endpoint(self, endpoint_id: UUID, data: EndpointUpdateSchema) -> Result[GatewayEndpoint]:
        """Met a jour un endpoint."""
        endpoint = self._endpoint_repo.get_active(endpoint_id)
        if not endpoint:
            return Result.fail(f"Endpoint non trouve: {endpoint_id}", error_code="NOT_FOUND")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == 'methods' and value is not None:
                value = json.dumps([m.value for m in value])
            elif field in ('required_scopes', 'cache_vary_headers', 'openapi_tags', 'request_schema') and value is not None:
                value = json.dumps(value)
            if hasattr(endpoint, field):
                setattr(endpoint, field, value)

        endpoint.updated_by = self.user_id
        endpoint.version += 1

        updated = self._endpoint_repo.update(endpoint)

        self._audit_repo.log_action(
            action="UPDATE_ENDPOINT",
            entity_type="GatewayEndpoint",
            entity_id=endpoint_id,
            user_id=self.user_id,
            new_values=update_data
        )

        return Result.ok(updated)

    def delete_endpoint(self, endpoint_id: UUID) -> Result[bool]:
        """Supprime un endpoint."""
        success = self._endpoint_repo.soft_delete(endpoint_id, self.user_id)
        if success:
            self._audit_repo.log_action(
                action="DELETE_ENDPOINT",
                entity_type="GatewayEndpoint",
                entity_id=endpoint_id,
                user_id=self.user_id
            )
        return Result.ok(success)

    def list_endpoints(
        self,
        endpoint_type: Optional[EndpointType] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Result[Tuple[List[GatewayEndpoint], int]]:
        """Liste les endpoints."""
        endpoints = self._endpoint_repo.list_active(
            endpoint_type.value if endpoint_type else None
        )
        total = len(endpoints)

        start = (page - 1) * page_size
        paginated = endpoints[start:start + page_size]

        return Result.ok((paginated, total))

    # ========================================================================
    # TRANSFORMATIONS
    # ========================================================================

    def create_transformation(self, data: TransformationCreateSchema) -> Result[GatewayTransformation]:
        """Cree une transformation."""
        existing = self._transform_repo.get_by_code(data.code)
        if existing:
            return Result.fail(f"Transformation '{data.code}' existe deja", error_code="DUPLICATE")

        transform = GatewayTransformation(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            transformation_type=data.transformation_type,
            configuration=json.dumps(data.configuration),
            add_headers=json.dumps(data.add_headers) if data.add_headers else None,
            remove_headers=json.dumps(data.remove_headers) if data.remove_headers else None,
            rename_headers=json.dumps(data.rename_headers) if data.rename_headers else None,
            body_template=data.body_template,
            content_type_output=data.content_type_output,
            input_schema=json.dumps(data.input_schema) if data.input_schema else None,
            output_schema=json.dumps(data.output_schema) if data.output_schema else None,
            created_by=self.user_id
        )

        created = self._transform_repo.create(transform)

        self._audit_repo.log_action(
            action="CREATE_TRANSFORMATION",
            entity_type="GatewayTransformation",
            entity_id=created.id,
            user_id=self.user_id
        )

        return Result.ok(created)

    def apply_transformation(
        self,
        transform: GatewayTransformation,
        data: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Result[Tuple[Dict[str, Any], Dict[str, str]]]:
        """Applique une transformation aux donnees."""
        try:
            config = json.loads(transform.configuration) if isinstance(transform.configuration, str) else transform.configuration
            transformed_data = data.copy()
            transformed_headers = headers.copy()

            # Transformer les headers
            if transform.remove_headers:
                remove = json.loads(transform.remove_headers) if isinstance(transform.remove_headers, str) else transform.remove_headers
                for h in remove:
                    transformed_headers.pop(h, None)

            if transform.rename_headers:
                rename = json.loads(transform.rename_headers) if isinstance(transform.rename_headers, str) else transform.rename_headers
                for old_name, new_name in rename.items():
                    if old_name in transformed_headers:
                        transformed_headers[new_name] = transformed_headers.pop(old_name)

            if transform.add_headers:
                add = json.loads(transform.add_headers) if isinstance(transform.add_headers, str) else transform.add_headers
                transformed_headers.update(add)

            # Transformer le body selon le type
            if transform.transformation_type == TransformationType.MAPPING:
                # Simple mapping de champs
                mapping = config.get('mapping', {})
                for source, target in mapping.items():
                    if source in transformed_data:
                        transformed_data[target] = transformed_data.pop(source)

            elif transform.transformation_type == TransformationType.JMESPATH:
                # Transformation JMESPath
                import jmespath
                expression = config.get('expression', '@')
                transformed_data = jmespath.search(expression, transformed_data) or {}

            elif transform.transformation_type == TransformationType.JINJA2:
                # Template Jinja2
                from jinja2 import Template
                if transform.body_template:
                    template = Template(transform.body_template)
                    result = template.render(**transformed_data)
                    transformed_data = json.loads(result)

            return Result.ok((transformed_data, transformed_headers))

        except Exception as e:
            self._logger.error(f"Transformation failed: {e}")
            return Result.fail(f"Transformation failed: {str(e)}", error_code="TRANSFORMATION_ERROR")

    # ========================================================================
    # WEBHOOKS
    # ========================================================================

    def create_webhook(self, data: WebhookCreateSchema) -> Result[GatewayWebhook]:
        """Cree un webhook."""
        existing = self._webhook_repo.get_by_code(data.code)
        if existing:
            return Result.fail(f"Webhook '{data.code}' existe deja", error_code="DUPLICATE")

        # Generer le signing secret si non fourni
        signing_secret = data.signing_secret or secrets.token_hex(32)

        webhook = GatewayWebhook(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            url=data.url,
            method=data.method,
            headers=json.dumps(data.headers) if data.headers else None,
            auth_type=data.auth_type,
            auth_config=json.dumps(data.auth_config) if data.auth_config else None,
            event_types=json.dumps([e.value for e in data.event_types]),
            event_filters=json.dumps(data.event_filters) if data.event_filters else None,
            payload_template=data.payload_template,
            transform_id=data.transform_id,
            max_retries=data.max_retries,
            retry_delay_seconds=data.retry_delay_seconds,
            retry_backoff_multiplier=data.retry_backoff_multiplier,
            timeout_seconds=data.timeout_seconds,
            signing_secret=signing_secret,
            created_by=self.user_id
        )

        created = self._webhook_repo.create(webhook)

        self._audit_repo.log_action(
            action="CREATE_WEBHOOK",
            entity_type="GatewayWebhook",
            entity_id=created.id,
            user_id=self.user_id,
            new_values={"code": data.code, "url": data.url}
        )

        return Result.ok(created)

    def get_webhook(self, webhook_id: UUID) -> Result[GatewayWebhook]:
        """Recupere un webhook."""
        webhook = self._webhook_repo.get_active(webhook_id)
        if not webhook:
            return Result.fail(f"Webhook non trouve: {webhook_id}", error_code="NOT_FOUND")
        return Result.ok(webhook)

    def update_webhook(self, webhook_id: UUID, data: WebhookUpdateSchema) -> Result[GatewayWebhook]:
        """Met a jour un webhook."""
        webhook = self._webhook_repo.get_active(webhook_id)
        if not webhook:
            return Result.fail(f"Webhook non trouve: {webhook_id}", error_code="NOT_FOUND")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == 'event_types' and value is not None:
                value = json.dumps([e.value for e in value])
            elif field in ('headers', 'auth_config', 'event_filters') and value is not None:
                value = json.dumps(value)
            if hasattr(webhook, field):
                setattr(webhook, field, value)

        webhook.updated_by = self.user_id
        webhook.version += 1

        updated = self._webhook_repo.update(webhook)

        self._audit_repo.log_action(
            action="UPDATE_WEBHOOK",
            entity_type="GatewayWebhook",
            entity_id=webhook_id,
            user_id=self.user_id,
            new_values=update_data
        )

        return Result.ok(updated)

    def delete_webhook(self, webhook_id: UUID) -> Result[bool]:
        """Supprime un webhook."""
        success = self._webhook_repo.soft_delete(webhook_id, self.user_id)
        if success:
            self._audit_repo.log_action(
                action="DELETE_WEBHOOK",
                entity_type="GatewayWebhook",
                entity_id=webhook_id,
                user_id=self.user_id
            )
        return Result.ok(success)

    def trigger_webhook(
        self,
        event_type: WebhookEventType,
        event_id: str,
        event_data: Dict[str, Any]
    ) -> List[UUID]:
        """
        Declenche les webhooks pour un evenement.
        Retourne les IDs des livraisons creees.
        """
        webhooks = self._webhook_repo.list_by_event_type(event_type.value)
        delivery_ids = []

        for webhook in webhooks:
            if webhook.status != WebhookStatus.ACTIVE:
                continue

            # Verifier les filtres
            if webhook.event_filters:
                filters = json.loads(webhook.event_filters) if isinstance(webhook.event_filters, str) else webhook.event_filters
                if not self._match_filters(event_data, filters):
                    continue

            # Creer la livraison
            delivery = self._create_webhook_delivery(webhook, event_type, event_id, event_data)
            delivery_ids.append(delivery.id)

        return delivery_ids

    def _match_filters(self, data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Verifie si les donnees correspondent aux filtres."""
        for key, expected in filters.items():
            actual = data.get(key)
            if isinstance(expected, dict):
                if not isinstance(actual, dict) or not self._match_filters(actual, expected):
                    return False
            elif actual != expected:
                return False
        return True

    def _create_webhook_delivery(
        self,
        webhook: GatewayWebhook,
        event_type: WebhookEventType,
        event_id: str,
        event_data: Dict[str, Any]
    ) -> GatewayWebhookDelivery:
        """Cree une livraison de webhook."""
        # Preparer le payload
        payload = event_data.copy()
        if webhook.payload_template:
            try:
                from jinja2 import Template
                template = Template(webhook.payload_template)
                payload = json.loads(template.render(event=event_data))
            except Exception as e:
                self._logger.error(f"Template error: {e}")

        # Preparer les headers
        headers = {"Content-Type": "application/json"}
        if webhook.headers:
            wh_headers = json.loads(webhook.headers) if isinstance(webhook.headers, str) else webhook.headers
            headers.update(wh_headers)

        # Ajouter la signature
        if webhook.signing_secret:
            payload_bytes = json.dumps(payload).encode()
            signature = hmac.new(
                webhook.signing_secret.encode(),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()
            headers[webhook.signature_header or "X-Signature-256"] = f"sha256={signature}"

        delivery = GatewayWebhookDelivery(
            tenant_id=self.tenant_id,
            webhook_id=webhook.id,
            event_type=event_type,
            event_id=event_id,
            event_data=json.dumps(event_data),
            request_url=webhook.url,
            request_method=webhook.method,
            request_headers=json.dumps(headers),
            request_body=json.dumps(payload),
            status=DeliveryStatus.PENDING
        )

        self.db.add(delivery)
        self.db.commit()
        self.db.refresh(delivery)

        return delivery

    async def send_webhook_delivery(self, delivery_id: UUID) -> Result[bool]:
        """Envoie une livraison de webhook."""
        delivery = self._delivery_repo.get_by_id(delivery_id)
        if not delivery:
            return Result.fail(f"Delivery non trouvee: {delivery_id}", error_code="NOT_FOUND")

        webhook = self._webhook_repo.get_by_id(delivery.webhook_id)
        if not webhook:
            return Result.fail("Webhook non trouve", error_code="NOT_FOUND")

        try:
            headers = json.loads(delivery.request_headers) if delivery.request_headers else {}
            body = delivery.request_body

            # Ajouter l'auth si configure
            if webhook.auth_type and webhook.auth_config:
                auth_config = json.loads(webhook.auth_config)
                if webhook.auth_type == AuthType.BASIC:
                    import base64
                    creds = base64.b64encode(
                        f"{auth_config['username']}:{auth_config['password']}".encode()
                    ).decode()
                    headers["Authorization"] = f"Basic {creds}"
                elif webhook.auth_type == AuthType.API_KEY:
                    headers[auth_config.get('header', 'X-API-Key')] = auth_config['key']

            start_time = datetime.utcnow()
            delivery.sent_at = start_time

            async with httpx.AsyncClient(timeout=webhook.timeout_seconds) as client:
                response = await client.request(
                    method=delivery.request_method.value,
                    url=delivery.request_url,
                    headers=headers,
                    content=body
                )

            response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            delivery.response_status = response.status_code
            delivery.response_headers = json.dumps(dict(response.headers))
            delivery.response_body = response.text[:10000]  # Truncate
            delivery.response_time_ms = response_time

            if 200 <= response.status_code < 300:
                delivery.status = DeliveryStatus.DELIVERED
                delivery.completed_at = datetime.utcnow()
                self._webhook_repo.update_stats(webhook.id, True)
                self.db.commit()
                return Result.ok(True)
            else:
                return self._handle_webhook_failure(delivery, webhook, f"HTTP {response.status_code}")

        except httpx.TimeoutException:
            return self._handle_webhook_failure(delivery, webhook, "Timeout")

        except httpx.ConnectError as e:
            return self._handle_webhook_failure(delivery, webhook, f"Connection error: {e}")

        except Exception as e:
            return self._handle_webhook_failure(delivery, webhook, str(e))

    def _handle_webhook_failure(
        self,
        delivery: GatewayWebhookDelivery,
        webhook: GatewayWebhook,
        error: str
    ) -> Result[bool]:
        """Gere un echec de livraison."""
        delivery.error_message = error

        if delivery.attempt_number < webhook.max_retries:
            # Planifier un retry
            delay = webhook.retry_delay_seconds * (
                float(webhook.retry_backoff_multiplier) ** (delivery.attempt_number - 1)
            )
            delay = min(delay, webhook.retry_max_delay_seconds)
            delivery.status = DeliveryStatus.RETRYING
            delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=int(delay))
            delivery.attempt_number += 1
        else:
            delivery.status = DeliveryStatus.FAILED
            delivery.completed_at = datetime.utcnow()
            self._webhook_repo.update_stats(webhook.id, False)

        self.db.commit()
        return Result.fail(error, error_code="WEBHOOK_DELIVERY_FAILED")

    async def test_webhook(
        self,
        webhook_id: UUID,
        event_type: WebhookEventType,
        sample_data: Dict[str, Any]
    ) -> Result[Dict[str, Any]]:
        """Teste un webhook avec des donnees d'exemple."""
        webhook = self._webhook_repo.get_active(webhook_id)
        if not webhook:
            return Result.fail(f"Webhook non trouve: {webhook_id}", error_code="NOT_FOUND")

        # Creer une livraison de test
        delivery = self._create_webhook_delivery(
            webhook,
            event_type,
            f"test_{uuid4().hex[:8]}",
            sample_data
        )

        # Envoyer
        result = await self.send_webhook_delivery(delivery.id)

        # Rafraichir pour obtenir la reponse
        self.db.refresh(delivery)

        return Result.ok({
            "success": delivery.status == DeliveryStatus.DELIVERED,
            "status_code": delivery.response_status,
            "response_time_ms": delivery.response_time_ms,
            "response_body": delivery.response_body[:500] if delivery.response_body else None,
            "error": delivery.error_message
        })

    def list_webhooks(
        self,
        status: Optional[WebhookStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Result[Tuple[List[GatewayWebhook], int]]:
        """Liste les webhooks."""
        if status == WebhookStatus.ACTIVE:
            webhooks = self._webhook_repo.list_active()
        elif status == WebhookStatus.FAILED:
            webhooks = self._webhook_repo.list_failed()
        else:
            webhooks, _ = self._webhook_repo.list_all(
                skip=0, limit=1000,
                filters={"status": status.value} if status else None
            )

        total = len(webhooks)
        start = (page - 1) * page_size
        paginated = webhooks[start:start + page_size]

        return Result.ok((paginated, total))

    # ========================================================================
    # LOGS ET METRIQUES
    # ========================================================================

    def log_request(
        self,
        ctx: RequestContext,
        status_code: int,
        response_time_ms: int,
        response_body_size: int = 0,
        throttle_decision: Optional[ThrottleDecision] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> GatewayRequestLog:
        """Enregistre une requete."""
        log = GatewayRequestLog(
            tenant_id=self.tenant_id,
            api_key_id=ctx.api_key.id if ctx.api_key else None,
            endpoint_id=ctx.endpoint.id if ctx.endpoint else None,
            method=ctx.method,
            path=ctx.path,
            client_ip=ctx.client_ip,
            user_agent=ctx.user_agent,
            origin=ctx.origin,
            status_code=status_code,
            response_body_size=response_body_size,
            response_time_ms=response_time_ms,
            rate_limit_remaining=throttle_decision.rate_limit_remaining if throttle_decision else None,
            rate_limit_reset=throttle_decision.rate_limit_reset if throttle_decision else None,
            was_throttled=throttle_decision.action == "REJECT" if throttle_decision else False,
            error_code=error_code,
            error_message=error_message,
            correlation_id=ctx.correlation_id
        )

        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        # Mettre a jour les metriques
        self._update_metrics(log)

        # Mettre a jour last_used sur la cle
        if ctx.api_key:
            self._key_repo.update_last_used(ctx.api_key.id, ctx.client_ip)

        # Incrementer les quotas
        if ctx.api_key:
            self.increment_quota(
                ctx.api_key.id,
                bytes_in=0,  # A calculer depuis la requete
                bytes_out=response_body_size,
                is_error=status_code >= 400
            )

        return log

    def _update_metrics(self, log: GatewayRequestLog) -> None:
        """Met a jour les metriques agregees."""
        now = datetime.utcnow()
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        hour_end = hour_start + timedelta(hours=1)

        metrics = self._metrics_repo.get_or_create_for_period(
            "hour", hour_start, hour_end
        )

        metrics.total_requests += 1

        if 200 <= log.status_code < 400:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
            if 400 <= log.status_code < 500:
                metrics.error_4xx_count += 1
            else:
                metrics.error_5xx_count += 1

        if log.was_throttled:
            metrics.throttled_requests += 1

        if log.was_cached:
            metrics.cached_requests += 1

        metrics.total_bytes_out += log.response_body_size

        # Moyenne temps de reponse
        total_time = float(metrics.avg_response_time) * (metrics.total_requests - 1)
        metrics.avg_response_time = Decimal(str((total_time + log.response_time_ms) / metrics.total_requests))

        if log.response_time_ms < metrics.min_response_time or metrics.min_response_time == 0:
            metrics.min_response_time = log.response_time_ms
        if log.response_time_ms > metrics.max_response_time:
            metrics.max_response_time = log.response_time_ms

        # Par status
        by_status = json.loads(metrics.requests_by_status or '{}')
        by_status[str(log.status_code)] = by_status.get(str(log.status_code), 0) + 1
        metrics.requests_by_status = json.dumps(by_status)

        # Par endpoint
        by_endpoint = json.loads(metrics.requests_by_endpoint or '{}')
        by_endpoint[log.path] = by_endpoint.get(log.path, 0) + 1
        metrics.requests_by_endpoint = json.dumps(by_endpoint)

        # Par methode
        by_method = json.loads(metrics.requests_by_method or '{}')
        by_method[log.method.value] = by_method.get(log.method.value, 0) + 1
        metrics.requests_by_method = json.dumps(by_method)

        self.db.commit()

    def get_request_logs(
        self,
        api_key_id: Optional[UUID] = None,
        path: Optional[str] = None,
        status_code: Optional[int] = None,
        since: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Result[Tuple[List[GatewayRequestLog], int]]:
        """Recupere les logs de requetes."""
        skip = (page - 1) * page_size
        logs, total = self._log_repo.list_recent(
            api_key_id=api_key_id,
            path=path,
            status_code=status_code,
            since=since,
            skip=skip,
            limit=page_size
        )
        return Result.ok((logs, total))

    def get_metrics(
        self,
        period_type: str = "hour",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        api_key_id: Optional[UUID] = None,
        endpoint_id: Optional[UUID] = None
    ) -> Result[List[GatewayMetrics]]:
        """Recupere les metriques."""
        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=24)
        if not end_time:
            end_time = datetime.utcnow()

        metrics = self._metrics_repo.list_for_range(
            period_type, start_time, end_time,
            api_key_id=api_key_id,
            endpoint_id=endpoint_id
        )

        return Result.ok(metrics)

    def get_dashboard_stats(self) -> Result[Dict[str, Any]]:
        """Recupere les statistiques du dashboard."""
        stats_24h = self._log_repo.count_24h()
        since_24h = datetime.utcnow() - timedelta(hours=24)

        stats = {
            "total_plans": self._plan_repo.count_active(),
            "active_plans": self._plan_repo.count_active(),
            "total_api_keys": self._key_repo.count_active(),
            "active_api_keys": self._key_repo.count_active(),
            "total_endpoints": self._endpoint_repo.count_active(),
            "active_endpoints": self._endpoint_repo.count_active(),
            "deprecated_endpoints": self._endpoint_repo.count_deprecated(),
            "total_webhooks": self._webhook_repo.count_active(),
            "active_webhooks": self._webhook_repo.count_active(),
            "failed_webhooks": self._webhook_repo.count_failed(),
            "requests_24h": stats_24h["total"],
            "successful_requests_24h": stats_24h["successful"],
            "failed_requests_24h": stats_24h["failed"],
            "throttled_requests_24h": stats_24h["throttled"],
            "avg_response_time_24h": self._log_repo.get_avg_response_time(since_24h),
            "p95_response_time_24h": 0,  # A calculer
            "error_rate_24h": (stats_24h["failed"] / stats_24h["total"] * 100) if stats_24h["total"] > 0 else 0,
            "top_errors": [],  # A implementer
            "open_circuits": self._circuit_repo.count_open()
        }

        return Result.ok(stats)

    # ========================================================================
    # GENERATION OPENAPI
    # ========================================================================

    def generate_openapi_spec(
        self,
        title: str = "AZALSCORE API",
        version: str = "1.0.0",
        description: Optional[str] = None,
        include_deprecated: bool = False,
        endpoint_ids: Optional[List[UUID]] = None
    ) -> Result[Dict[str, Any]]:
        """Genere une specification OpenAPI."""
        endpoints = self._endpoint_repo.list_active()

        if endpoint_ids:
            endpoints = [e for e in endpoints if e.id in endpoint_ids]

        if not include_deprecated:
            endpoints = [e for e in endpoints if not e.is_deprecated]

        paths = {}
        tags = set()

        for endpoint in endpoints:
            methods = json.loads(endpoint.methods) if isinstance(endpoint.methods, str) else endpoint.methods

            # Tags
            endpoint_tags = []
            if endpoint.openapi_tags:
                ep_tags = json.loads(endpoint.openapi_tags) if isinstance(endpoint.openapi_tags, str) else endpoint.openapi_tags
                endpoint_tags.extend(ep_tags)
                tags.update(ep_tags)

            path_item = {}
            for method in methods:
                method_lower = method.lower()
                operation = {
                    "summary": endpoint.openapi_summary or endpoint.name,
                    "description": endpoint.openapi_description or endpoint.description or "",
                    "tags": endpoint_tags,
                    "operationId": f"{method_lower}_{endpoint.code}",
                    "deprecated": endpoint.is_deprecated,
                    "responses": {
                        "200": {"description": "Successful response"},
                        "400": {"description": "Bad request"},
                        "401": {"description": "Unauthorized"},
                        "403": {"description": "Forbidden"},
                        "404": {"description": "Not found"},
                        "429": {"description": "Rate limit exceeded"},
                        "500": {"description": "Internal server error"}
                    }
                }

                # Securite
                if endpoint.auth_required:
                    operation["security"] = [{"ApiKeyAuth": []}]

                path_item[method_lower] = operation

            paths[endpoint.path_pattern] = path_item

        spec = {
            "openapi": "3.0.3",
            "info": {
                "title": title,
                "version": version,
                "description": description or "API Gateway AZALSCORE"
            },
            "servers": [
                {"url": "/api/v1", "description": "API Server"}
            ],
            "paths": paths,
            "components": {
                "securitySchemes": {
                    "ApiKeyAuth": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-API-Key"
                    },
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer"
                    }
                }
            },
            "tags": [{"name": tag} for tag in sorted(tags)]
        }

        return Result.ok(spec)

    # ========================================================================
    # PROCESS REQUEST (MIDDLEWARE PRINCIPAL)
    # ========================================================================

    def process_request(
        self,
        raw_api_key: str,
        method: HttpMethod,
        path: str,
        client_ip: str,
        user_agent: Optional[str] = None,
        origin: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> Result[RequestContext]:
        """
        Traite une requete entrante.
        Valide l'authentification, rate limiting, circuit breaker.
        """
        ctx = RequestContext(
            api_key=None,
            plan=None,
            endpoint=None,
            method=method,
            path=path,
            client_ip=client_ip,
            user_agent=user_agent,
            origin=origin,
            correlation_id=correlation_id or uuid4().hex,
            start_time=datetime.utcnow()
        )

        # 1. Valider la cle API
        key_result = self.validate_api_key(raw_api_key)
        if not key_result.success:
            return Result.fail(key_result.error, error_code=key_result.error_code)
        ctx.api_key = key_result.data

        # 2. Recuperer le plan
        plan_result = self.get_plan(ctx.api_key.plan_id)
        if not plan_result.success:
            return Result.fail(plan_result.error, error_code=plan_result.error_code)
        ctx.plan = plan_result.data

        # 3. Verifier les IPs autorisees
        if ctx.api_key.allowed_ips:
            allowed = json.loads(ctx.api_key.allowed_ips) if isinstance(ctx.api_key.allowed_ips, str) else ctx.api_key.allowed_ips
            if allowed and client_ip not in allowed:
                return Result.fail(f"IP {client_ip} non autorisee", error_code="IP_NOT_ALLOWED")

        # 4. Verifier l'origine
        if ctx.api_key.allowed_origins and origin:
            origins = json.loads(ctx.api_key.allowed_origins) if isinstance(ctx.api_key.allowed_origins, str) else ctx.api_key.allowed_origins
            if origins and origin not in origins:
                return Result.fail(f"Origine {origin} non autorisee", error_code="ORIGIN_NOT_ALLOWED")

        # 5. Trouver l'endpoint
        ctx.endpoint = self.find_endpoint_by_path(path)

        # 6. Verifier le circuit breaker
        if ctx.endpoint and self.is_circuit_open(ctx.endpoint):
            return Result.fail(
                "Service temporairement indisponible (circuit ouvert)",
                error_code="CIRCUIT_OPEN"
            )

        # 7. Verifier les quotas
        quota_result = self.check_quota(ctx.api_key, ctx.plan)
        if not quota_result.success:
            return Result.fail(quota_result.error, error_code=quota_result.error_code)

        # 8. Verifier le rate limiting
        throttle = self.check_rate_limit(ctx.api_key, ctx.endpoint, method)
        if not throttle.allowed:
            return Result.fail(
                throttle.reason or "Rate limit exceeded",
                error_code="RATE_LIMIT_EXCEEDED"
            )

        return Result.ok(ctx)


# ============================================================================
# FACTORY
# ============================================================================

def create_gateway_service(db: Session, context: SaaSContext) -> GatewayService:
    """Cree une instance du service Gateway."""
    return GatewayService(db, context)
