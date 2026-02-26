"""
AZALS MODULE GATEWAY - Repository
===================================

Couche d'acces aux donnees avec isolation tenant automatique.
Utilise _base_query() filtre pour garantir l'isolation.
"""
from __future__ import annotations


import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar
from uuid import UUID

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, Query

from app.core.repository import BaseRepository

from .models import (
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
    ApiKeyStatus,
    CircuitState,
    DeliveryStatus,
    QuotaPeriod,
    WebhookStatus,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class GatewayBaseRepository(BaseRepository[T]):
    """
    Repository de base pour le module Gateway.
    Herite de BaseRepository avec _base_query() filtre par tenant_id.
    """

    def __init__(self, db: Session, model: Type[T], tenant_id: str):
        super().__init__(db, model, tenant_id)

    def _base_query(self) -> Query:
        """
        Query de base filtree par tenant_id.
        Tous les queries doivent passer par cette methode.
        """
        return self.db.query(self.model).filter(
            self.model.tenant_id == self.tenant_id
        )

    def _apply_soft_delete_filter(self, query: Query) -> Query:
        """Filtre les entites soft deleted."""
        if hasattr(self.model, 'deleted_at'):
            return query.filter(self.model.deleted_at.is_(None))
        return query

    def get_active(self, id: UUID) -> Optional[T]:
        """Recupere une entite active (non soft deleted)."""
        query = self._base_query().filter(self.model.id == id)
        query = self._apply_soft_delete_filter(query)
        return query.first()

    def soft_delete(self, id: UUID, deleted_by: Optional[UUID] = None) -> bool:
        """Soft delete d'une entite."""
        entity = self.get_by_id(id)
        if not entity:
            return False

        if hasattr(entity, 'deleted_at'):
            entity.deleted_at = datetime.utcnow()
            if hasattr(entity, 'deleted_by') and deleted_by:
                entity.deleted_by = deleted_by
            self.db.commit()
            return True
        return False


# ============================================================================
# API PLAN REPOSITORY
# ============================================================================

class ApiPlanRepository(GatewayBaseRepository[GatewayApiPlan]):
    """Repository pour les plans API."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, GatewayApiPlan, tenant_id)

    def get_by_code(self, code: str) -> Optional[GatewayApiPlan]:
        """Recupere un plan par son code."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(GatewayApiPlan.code == code)
        ).first()

    def get_default_plan(self) -> Optional[GatewayApiPlan]:
        """Recupere le plan par defaut."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(
                GatewayApiPlan.is_default == True,
                GatewayApiPlan.is_active == True
            )
        ).first()

    def list_active(self, tier: Optional[str] = None) -> List[GatewayApiPlan]:
        """Liste les plans actifs."""
        query = self._apply_soft_delete_filter(
            self._base_query().filter(GatewayApiPlan.is_active == True)
        )
        if tier:
            query = query.filter(GatewayApiPlan.tier == tier)
        return query.order_by(GatewayApiPlan.tier).all()

    def count_active(self) -> int:
        """Compte les plans actifs."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(GatewayApiPlan.is_active == True)
        ).count()


# ============================================================================
# API KEY REPOSITORY
# ============================================================================

class ApiKeyRepository(GatewayBaseRepository[GatewayApiKey]):
    """Repository pour les cles API."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, GatewayApiKey, tenant_id)

    def get_by_hash(self, key_hash: str) -> Optional[GatewayApiKey]:
        """Recupere une cle par son hash."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(GatewayApiKey.key_hash == key_hash)
        ).first()

    def get_by_prefix(self, prefix: str) -> Optional[GatewayApiKey]:
        """Recupere une cle par son prefixe."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(GatewayApiKey.key_prefix == prefix)
        ).first()

    def list_by_client(self, client_id: str) -> List[GatewayApiKey]:
        """Liste les cles d'un client."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(GatewayApiKey.client_id == client_id)
        ).order_by(desc(GatewayApiKey.created_at)).all()

    def list_by_plan(self, plan_id: UUID) -> List[GatewayApiKey]:
        """Liste les cles d'un plan."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(GatewayApiKey.plan_id == plan_id)
        ).all()

    def list_active(
        self,
        client_id: Optional[str] = None,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[GatewayApiKey], int]:
        """Liste les cles actives avec pagination."""
        query = self._apply_soft_delete_filter(
            self._base_query().filter(GatewayApiKey.status == ApiKeyStatus.ACTIVE)
        )

        if client_id:
            query = query.filter(GatewayApiKey.client_id == client_id)
        if user_id:
            query = query.filter(GatewayApiKey.user_id == user_id)

        total = query.count()
        items = query.order_by(desc(GatewayApiKey.created_at)).offset(skip).limit(limit).all()

        return items, total

    def list_expiring_soon(self, days: int = 7) -> List[GatewayApiKey]:
        """Liste les cles qui expirent bientot."""
        expiry_date = datetime.utcnow() + timedelta(days=days)
        return self._apply_soft_delete_filter(
            self._base_query().filter(
                GatewayApiKey.status == ApiKeyStatus.ACTIVE,
                GatewayApiKey.expires_at.isnot(None),
                GatewayApiKey.expires_at <= expiry_date,
                GatewayApiKey.expires_at > datetime.utcnow()
            )
        ).all()

    def count_active(self) -> int:
        """Compte les cles actives."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(GatewayApiKey.status == ApiKeyStatus.ACTIVE)
        ).count()

    def update_last_used(self, key_id: UUID, ip_address: str) -> None:
        """Met a jour la derniere utilisation."""
        key = self.get_by_id(key_id)
        if key:
            key.last_used_at = datetime.utcnow()
            key.last_used_ip = ip_address
            key.usage_count += 1
            self.db.commit()


# ============================================================================
# ENDPOINT REPOSITORY
# ============================================================================

class EndpointRepository(GatewayBaseRepository[GatewayEndpoint]):
    """Repository pour les endpoints."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, GatewayEndpoint, tenant_id)

    def get_by_code(self, code: str) -> Optional[GatewayEndpoint]:
        """Recupere un endpoint par son code."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(GatewayEndpoint.code == code)
        ).first()

    def find_by_path(self, path: str) -> Optional[GatewayEndpoint]:
        """
        Trouve un endpoint correspondant a un chemin.
        Supporte les patterns glob avec *.
        """
        # D'abord chercher une correspondance exacte
        exact = self._apply_soft_delete_filter(
            self._base_query().filter(
                GatewayEndpoint.path_pattern == path,
                GatewayEndpoint.is_active == True
            )
        ).first()

        if exact:
            return exact

        # Sinon, chercher avec patterns
        active_endpoints = self._apply_soft_delete_filter(
            self._base_query().filter(GatewayEndpoint.is_active == True)
        ).all()

        import fnmatch
        for endpoint in active_endpoints:
            if fnmatch.fnmatch(path, endpoint.path_pattern):
                return endpoint

        return None

    def list_active(self, endpoint_type: Optional[str] = None) -> List[GatewayEndpoint]:
        """Liste les endpoints actifs."""
        query = self._apply_soft_delete_filter(
            self._base_query().filter(GatewayEndpoint.is_active == True)
        )
        if endpoint_type:
            query = query.filter(GatewayEndpoint.endpoint_type == endpoint_type)
        return query.order_by(GatewayEndpoint.path_pattern).all()

    def list_deprecated(self) -> List[GatewayEndpoint]:
        """Liste les endpoints deprecies."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(GatewayEndpoint.is_deprecated == True)
        ).all()

    def count_active(self) -> int:
        """Compte les endpoints actifs."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(GatewayEndpoint.is_active == True)
        ).count()

    def count_deprecated(self) -> int:
        """Compte les endpoints deprecies."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(GatewayEndpoint.is_deprecated == True)
        ).count()


# ============================================================================
# TRANSFORMATION REPOSITORY
# ============================================================================

class TransformationRepository(GatewayBaseRepository[GatewayTransformation]):
    """Repository pour les transformations."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, GatewayTransformation, tenant_id)

    def get_by_code(self, code: str) -> Optional[GatewayTransformation]:
        """Recupere une transformation par son code."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(GatewayTransformation.code == code)
        ).first()

    def list_active(self, transform_type: Optional[str] = None) -> List[GatewayTransformation]:
        """Liste les transformations actives."""
        query = self._apply_soft_delete_filter(
            self._base_query().filter(GatewayTransformation.is_active == True)
        )
        if transform_type:
            query = query.filter(GatewayTransformation.transformation_type == transform_type)
        return query.order_by(GatewayTransformation.name).all()


# ============================================================================
# WEBHOOK REPOSITORY
# ============================================================================

class WebhookRepository(GatewayBaseRepository[GatewayWebhook]):
    """Repository pour les webhooks."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, GatewayWebhook, tenant_id)

    def get_by_code(self, code: str) -> Optional[GatewayWebhook]:
        """Recupere un webhook par son code."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(GatewayWebhook.code == code)
        ).first()

    def list_by_event_type(self, event_type: str) -> List[GatewayWebhook]:
        """Liste les webhooks pour un type d'evenement."""
        webhooks = self._apply_soft_delete_filter(
            self._base_query().filter(GatewayWebhook.status == WebhookStatus.ACTIVE)
        ).all()

        result = []
        for webhook in webhooks:
            event_types = json.loads(webhook.event_types) if isinstance(webhook.event_types, str) else webhook.event_types
            if event_type in event_types:
                result.append(webhook)

        return result

    def list_active(self) -> List[GatewayWebhook]:
        """Liste les webhooks actifs."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(GatewayWebhook.status == WebhookStatus.ACTIVE)
        ).all()

    def list_failed(self, min_consecutive_failures: int = 3) -> List[GatewayWebhook]:
        """Liste les webhooks en echec."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(
                GatewayWebhook.consecutive_failures >= min_consecutive_failures
            )
        ).all()

    def count_active(self) -> int:
        """Compte les webhooks actifs."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(GatewayWebhook.status == WebhookStatus.ACTIVE)
        ).count()

    def count_failed(self) -> int:
        """Compte les webhooks en echec."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(GatewayWebhook.status == WebhookStatus.FAILED)
        ).count()

    def update_stats(
        self,
        webhook_id: UUID,
        success: bool,
        triggered_at: Optional[datetime] = None
    ) -> None:
        """Met a jour les statistiques d'un webhook."""
        webhook = self.get_by_id(webhook_id)
        if not webhook:
            return

        now = triggered_at or datetime.utcnow()
        webhook.last_triggered_at = now

        if success:
            webhook.last_success_at = now
            webhook.success_count += 1
            webhook.consecutive_failures = 0
            if webhook.status == WebhookStatus.FAILED:
                webhook.status = WebhookStatus.ACTIVE
        else:
            webhook.last_failure_at = now
            webhook.failure_count += 1
            webhook.consecutive_failures += 1

            # Auto-disable apres trop d'echecs
            if webhook.consecutive_failures >= 10:
                webhook.status = WebhookStatus.FAILED

        self.db.commit()


# ============================================================================
# WEBHOOK DELIVERY REPOSITORY
# ============================================================================

class WebhookDeliveryRepository(GatewayBaseRepository[GatewayWebhookDelivery]):
    """Repository pour les livraisons de webhooks."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, GatewayWebhookDelivery, tenant_id)

    def list_by_webhook(
        self,
        webhook_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[GatewayWebhookDelivery], int]:
        """Liste les livraisons d'un webhook."""
        query = self._base_query().filter(GatewayWebhookDelivery.webhook_id == webhook_id)
        total = query.count()
        items = query.order_by(desc(GatewayWebhookDelivery.created_at)).offset(skip).limit(limit).all()
        return items, total

    def list_pending_retries(self, limit: int = 100) -> List[GatewayWebhookDelivery]:
        """Liste les livraisons en attente de retry."""
        now = datetime.utcnow()
        return self._base_query().filter(
            GatewayWebhookDelivery.status == DeliveryStatus.RETRYING,
            GatewayWebhookDelivery.next_retry_at <= now
        ).order_by(GatewayWebhookDelivery.next_retry_at).limit(limit).all()

    def list_failed_recent(self, hours: int = 24) -> List[GatewayWebhookDelivery]:
        """Liste les livraisons echouees recentes."""
        since = datetime.utcnow() - timedelta(hours=hours)
        return self._base_query().filter(
            GatewayWebhookDelivery.status == DeliveryStatus.FAILED,
            GatewayWebhookDelivery.completed_at >= since
        ).order_by(desc(GatewayWebhookDelivery.completed_at)).all()


# ============================================================================
# QUOTA USAGE REPOSITORY
# ============================================================================

class QuotaUsageRepository(GatewayBaseRepository[GatewayQuotaUsage]):
    """Repository pour l'utilisation des quotas."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, GatewayQuotaUsage, tenant_id)

    def get_current(self, api_key_id: UUID, period: QuotaPeriod) -> Optional[GatewayQuotaUsage]:
        """Recupere le quota actuel pour une cle et une periode."""
        now = datetime.utcnow()
        return self._base_query().filter(
            GatewayQuotaUsage.api_key_id == api_key_id,
            GatewayQuotaUsage.period == period,
            GatewayQuotaUsage.period_start <= now,
            GatewayQuotaUsage.period_end > now
        ).first()

    def get_or_create_current(
        self,
        api_key_id: UUID,
        period: QuotaPeriod,
        limit: int
    ) -> GatewayQuotaUsage:
        """Recupere ou cree le quota actuel."""
        current = self.get_current(api_key_id, period)
        if current:
            return current

        # Creer un nouveau quota
        now = datetime.utcnow()
        period_start, period_end = self._calculate_period_bounds(now, period)

        quota = GatewayQuotaUsage(
            tenant_id=self.tenant_id,
            api_key_id=api_key_id,
            period=period,
            period_start=period_start,
            period_end=period_end,
            requests_limit=limit
        )
        self.db.add(quota)
        self.db.commit()
        self.db.refresh(quota)

        return quota

    def _calculate_period_bounds(
        self,
        dt: datetime,
        period: QuotaPeriod
    ) -> Tuple[datetime, datetime]:
        """Calcule les bornes d'une periode."""
        if period == QuotaPeriod.MINUTE:
            start = dt.replace(second=0, microsecond=0)
            end = start + timedelta(minutes=1)
        elif period == QuotaPeriod.HOUR:
            start = dt.replace(minute=0, second=0, microsecond=0)
            end = start + timedelta(hours=1)
        elif period == QuotaPeriod.DAY:
            start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif period == QuotaPeriod.WEEK:
            start = (dt - timedelta(days=dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(weeks=1)
        elif period == QuotaPeriod.MONTH:
            start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if dt.month == 12:
                end = start.replace(year=dt.year + 1, month=1)
            else:
                end = start.replace(month=dt.month + 1)
        else:
            start = dt
            end = dt + timedelta(hours=1)

        return start, end

    def increment_usage(
        self,
        api_key_id: UUID,
        period: QuotaPeriod,
        limit: int,
        bytes_in: int = 0,
        bytes_out: int = 0,
        is_error: bool = False
    ) -> GatewayQuotaUsage:
        """Incremente l'utilisation du quota."""
        quota = self.get_or_create_current(api_key_id, period, limit)

        quota.requests_count += 1
        quota.bytes_in += bytes_in
        quota.bytes_out += bytes_out

        if is_error:
            quota.error_count += 1

        if quota.requests_count >= quota.requests_limit:
            if not quota.is_exceeded:
                quota.is_exceeded = True
                quota.exceeded_at = datetime.utcnow()
            quota.overage_count = quota.requests_count - quota.requests_limit

        self.db.commit()
        return quota


# ============================================================================
# RATE LIMIT STATE REPOSITORY
# ============================================================================

class RateLimitStateRepository(GatewayBaseRepository[GatewayRateLimitState]):
    """Repository pour l'etat du rate limiting."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, GatewayRateLimitState, tenant_id)

    def get_state(
        self,
        api_key_id: UUID,
        endpoint_pattern: str
    ) -> Optional[GatewayRateLimitState]:
        """Recupere l'etat du rate limiting."""
        return self._base_query().filter(
            GatewayRateLimitState.api_key_id == api_key_id,
            GatewayRateLimitState.endpoint_pattern == endpoint_pattern
        ).first()

    def get_or_create_state(
        self,
        api_key_id: UUID,
        endpoint_pattern: str,
        initial_tokens: float
    ) -> GatewayRateLimitState:
        """Recupere ou cree l'etat."""
        state = self.get_state(api_key_id, endpoint_pattern)
        if state:
            return state

        now = datetime.utcnow()
        state = GatewayRateLimitState(
            tenant_id=self.tenant_id,
            api_key_id=api_key_id,
            endpoint_pattern=endpoint_pattern,
            window_start=now,
            tokens_remaining=initial_tokens,
            last_refill=now
        )
        self.db.add(state)
        self.db.commit()
        self.db.refresh(state)

        return state

    def cleanup_old_states(self, older_than_hours: int = 24) -> int:
        """Nettoie les etats anciens."""
        cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
        count = self._base_query().filter(
            GatewayRateLimitState.updated_at < cutoff
        ).delete()
        self.db.commit()
        return count


# ============================================================================
# CIRCUIT BREAKER REPOSITORY
# ============================================================================

class CircuitBreakerRepository(GatewayBaseRepository[GatewayCircuitBreaker]):
    """Repository pour les circuit breakers."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, GatewayCircuitBreaker, tenant_id)

    def get_by_endpoint(self, endpoint_id: UUID) -> Optional[GatewayCircuitBreaker]:
        """Recupere le circuit breaker d'un endpoint."""
        return self._base_query().filter(
            GatewayCircuitBreaker.endpoint_id == endpoint_id
        ).first()

    def get_or_create(
        self,
        endpoint_id: UUID,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: int = 30
    ) -> GatewayCircuitBreaker:
        """Recupere ou cree le circuit breaker."""
        cb = self.get_by_endpoint(endpoint_id)
        if cb:
            return cb

        cb = GatewayCircuitBreaker(
            tenant_id=self.tenant_id,
            endpoint_id=endpoint_id,
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout_seconds=timeout_seconds
        )
        self.db.add(cb)
        self.db.commit()
        self.db.refresh(cb)

        return cb

    def count_open(self) -> int:
        """Compte les circuits ouverts."""
        return self._base_query().filter(
            GatewayCircuitBreaker.state == CircuitState.OPEN
        ).count()


# ============================================================================
# REQUEST LOG REPOSITORY
# ============================================================================

class RequestLogRepository(GatewayBaseRepository[GatewayRequestLog]):
    """Repository pour les logs de requetes."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, GatewayRequestLog, tenant_id)

    def list_recent(
        self,
        api_key_id: Optional[UUID] = None,
        path: Optional[str] = None,
        status_code: Optional[int] = None,
        since: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[GatewayRequestLog], int]:
        """Liste les logs recents avec filtres."""
        query = self._base_query()

        if api_key_id:
            query = query.filter(GatewayRequestLog.api_key_id == api_key_id)
        if path:
            query = query.filter(GatewayRequestLog.path.like(f"%{path}%"))
        if status_code:
            query = query.filter(GatewayRequestLog.status_code == status_code)
        if since:
            query = query.filter(GatewayRequestLog.timestamp >= since)

        total = query.count()
        items = query.order_by(desc(GatewayRequestLog.timestamp)).offset(skip).limit(limit).all()

        return items, total

    def count_by_status(
        self,
        since: datetime,
        api_key_id: Optional[UUID] = None
    ) -> Dict[int, int]:
        """Compte les requetes par code status."""
        query = self._base_query().filter(GatewayRequestLog.timestamp >= since)
        if api_key_id:
            query = query.filter(GatewayRequestLog.api_key_id == api_key_id)

        results = query.with_entities(
            GatewayRequestLog.status_code,
            func.count(GatewayRequestLog.id)
        ).group_by(GatewayRequestLog.status_code).all()

        return {status: count for status, count in results}

    def count_24h(self) -> Dict[str, int]:
        """Compte les requetes des dernieres 24h."""
        since = datetime.utcnow() - timedelta(hours=24)
        query = self._base_query().filter(GatewayRequestLog.timestamp >= since)

        total = query.count()
        successful = query.filter(GatewayRequestLog.status_code < 400).count()
        failed = query.filter(GatewayRequestLog.status_code >= 400).count()
        throttled = query.filter(GatewayRequestLog.was_throttled == True).count()

        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "throttled": throttled
        }

    def get_avg_response_time(
        self,
        since: datetime,
        api_key_id: Optional[UUID] = None
    ) -> float:
        """Calcule le temps de reponse moyen."""
        query = self._base_query().filter(GatewayRequestLog.timestamp >= since)
        if api_key_id:
            query = query.filter(GatewayRequestLog.api_key_id == api_key_id)

        result = query.with_entities(
            func.avg(GatewayRequestLog.response_time_ms)
        ).scalar()

        return float(result) if result else 0.0

    def get_top_endpoints(
        self,
        since: datetime,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Recupere les endpoints les plus utilises."""
        results = self._base_query().filter(
            GatewayRequestLog.timestamp >= since
        ).with_entities(
            GatewayRequestLog.path,
            func.count(GatewayRequestLog.id).label('count'),
            func.avg(GatewayRequestLog.response_time_ms).label('avg_time')
        ).group_by(GatewayRequestLog.path).order_by(
            desc('count')
        ).limit(limit).all()

        return [
            {"path": path, "count": count, "avg_response_time": float(avg_time or 0)}
            for path, count, avg_time in results
        ]

    def cleanup_old_logs(self, older_than_days: int = 30) -> int:
        """Nettoie les anciens logs."""
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        count = self._base_query().filter(
            GatewayRequestLog.timestamp < cutoff
        ).delete()
        self.db.commit()
        return count


# ============================================================================
# METRICS REPOSITORY
# ============================================================================

class MetricsRepository(GatewayBaseRepository[GatewayMetrics]):
    """Repository pour les metriques."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, GatewayMetrics, tenant_id)

    def get_for_period(
        self,
        period_type: str,
        period_start: datetime,
        api_key_id: Optional[UUID] = None,
        endpoint_id: Optional[UUID] = None
    ) -> Optional[GatewayMetrics]:
        """Recupere les metriques pour une periode."""
        query = self._base_query().filter(
            GatewayMetrics.period_type == period_type,
            GatewayMetrics.period_start == period_start
        )

        if api_key_id:
            query = query.filter(GatewayMetrics.api_key_id == api_key_id)
        else:
            query = query.filter(GatewayMetrics.api_key_id.is_(None))

        if endpoint_id:
            query = query.filter(GatewayMetrics.endpoint_id == endpoint_id)
        else:
            query = query.filter(GatewayMetrics.endpoint_id.is_(None))

        return query.first()

    def get_or_create_for_period(
        self,
        period_type: str,
        period_start: datetime,
        period_end: datetime,
        api_key_id: Optional[UUID] = None,
        endpoint_id: Optional[UUID] = None
    ) -> GatewayMetrics:
        """Recupere ou cree les metriques pour une periode."""
        metrics = self.get_for_period(period_type, period_start, api_key_id, endpoint_id)
        if metrics:
            return metrics

        metrics = GatewayMetrics(
            tenant_id=self.tenant_id,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            api_key_id=api_key_id,
            endpoint_id=endpoint_id
        )
        self.db.add(metrics)
        self.db.commit()
        self.db.refresh(metrics)

        return metrics

    def list_for_range(
        self,
        period_type: str,
        start_time: datetime,
        end_time: datetime,
        api_key_id: Optional[UUID] = None,
        endpoint_id: Optional[UUID] = None
    ) -> List[GatewayMetrics]:
        """Liste les metriques pour une plage."""
        query = self._base_query().filter(
            GatewayMetrics.period_type == period_type,
            GatewayMetrics.period_start >= start_time,
            GatewayMetrics.period_end <= end_time
        )

        if api_key_id:
            query = query.filter(GatewayMetrics.api_key_id == api_key_id)
        if endpoint_id:
            query = query.filter(GatewayMetrics.endpoint_id == endpoint_id)

        return query.order_by(GatewayMetrics.period_start).all()


# ============================================================================
# OAUTH REPOSITORIES
# ============================================================================

class OAuthClientRepository(GatewayBaseRepository[GatewayOAuthClient]):
    """Repository pour les clients OAuth."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, GatewayOAuthClient, tenant_id)

    def get_by_client_id(self, client_id: str) -> Optional[GatewayOAuthClient]:
        """Recupere un client par son client_id."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(GatewayOAuthClient.client_id == client_id)
        ).first()

    def list_active(self) -> List[GatewayOAuthClient]:
        """Liste les clients actifs."""
        return self._apply_soft_delete_filter(
            self._base_query().filter(GatewayOAuthClient.is_active == True)
        ).all()


class OAuthTokenRepository(GatewayBaseRepository[GatewayOAuthToken]):
    """Repository pour les tokens OAuth."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, GatewayOAuthToken, tenant_id)

    def get_by_access_token(self, token_hash: str) -> Optional[GatewayOAuthToken]:
        """Recupere un token par son hash d'access token."""
        return self._base_query().filter(
            GatewayOAuthToken.access_token_hash == token_hash,
            GatewayOAuthToken.is_revoked == False
        ).first()

    def get_by_refresh_token(self, token_hash: str) -> Optional[GatewayOAuthToken]:
        """Recupere un token par son hash de refresh token."""
        return self._base_query().filter(
            GatewayOAuthToken.refresh_token_hash == token_hash,
            GatewayOAuthToken.is_revoked == False
        ).first()

    def revoke_all_for_client(self, client_id: UUID) -> int:
        """Revoque tous les tokens d'un client."""
        count = self._base_query().filter(
            GatewayOAuthToken.client_id == client_id,
            GatewayOAuthToken.is_revoked == False
        ).update({
            "is_revoked": True,
            "revoked_at": datetime.utcnow()
        })
        self.db.commit()
        return count

    def cleanup_expired(self) -> int:
        """Nettoie les tokens expires."""
        now = datetime.utcnow()
        count = self._base_query().filter(
            GatewayOAuthToken.access_token_expires_at < now
        ).delete()
        self.db.commit()
        return count


# ============================================================================
# AUDIT LOG REPOSITORY
# ============================================================================

class AuditLogRepository(GatewayBaseRepository[GatewayAuditLog]):
    """Repository pour les logs d'audit (APPEND ONLY)."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, GatewayAuditLog, tenant_id)

    def log_action(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        api_key_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        details: Optional[dict] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> GatewayAuditLog:
        """Enregistre une action d'audit."""
        log = GatewayAuditLog(
            tenant_id=self.tenant_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            api_key_id=api_key_id,
            ip_address=ip_address,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            details=json.dumps(details) if details else None,
            success=success,
            error_message=error_message,
            correlation_id=correlation_id
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        return log

    def list_for_entity(
        self,
        entity_type: str,
        entity_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[GatewayAuditLog], int]:
        """Liste les logs d'audit pour une entite."""
        query = self._base_query().filter(
            GatewayAuditLog.entity_type == entity_type,
            GatewayAuditLog.entity_id == entity_id
        )

        total = query.count()
        items = query.order_by(desc(GatewayAuditLog.created_at)).offset(skip).limit(limit).all()

        return items, total

    def list_recent(
        self,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        user_id: Optional[UUID] = None,
        since: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[GatewayAuditLog], int]:
        """Liste les logs d'audit recents."""
        query = self._base_query()

        if action:
            query = query.filter(GatewayAuditLog.action == action)
        if entity_type:
            query = query.filter(GatewayAuditLog.entity_type == entity_type)
        if user_id:
            query = query.filter(GatewayAuditLog.user_id == user_id)
        if since:
            query = query.filter(GatewayAuditLog.created_at >= since)

        total = query.count()
        items = query.order_by(desc(GatewayAuditLog.created_at)).offset(skip).limit(limit).all()

        return items, total
