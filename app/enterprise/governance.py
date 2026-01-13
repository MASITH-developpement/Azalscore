"""
AZALSCORE Enterprise - Tenant Governance
=========================================
Gouvernance des tenants niveau enterprise.

Fonctionnalités:
- Quotas et limites par tenant
- Détection et isolation des tenants toxiques
- Priorisation SLA
- Suspension graduée
- Reporting par client

Niveau Enterprise: Comparable à Salesforce Governor Limits.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Set, Callable, Any
from enum import Enum
from collections import defaultdict
import threading

from app.enterprise.sla import TenantTier, SLAConfig, get_sla_config

logger = logging.getLogger(__name__)


class TenantHealthStatus(str, Enum):
    """Statut de santé d'un tenant."""
    HEALTHY = "healthy"
    WARNING = "warning"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"


class ViolationType(str, Enum):
    """Types de violations détectées."""
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    QUOTA_EXCEEDED = "quota_exceeded"
    SLOW_QUERIES = "slow_queries"
    HIGH_ERROR_RATE = "high_error_rate"
    RESOURCE_ABUSE = "resource_abuse"
    SECURITY_VIOLATION = "security_violation"


@dataclass
class TenantQuotaUsage:
    """Usage des quotas pour un tenant."""
    tenant_id: str
    tier: TenantTier

    # Compteurs de requêtes
    requests_this_minute: int = 0
    requests_this_hour: int = 0
    requests_today: int = 0
    concurrent_requests: int = 0

    # Métriques de performance
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    error_count_today: int = 0
    error_rate: float = 0.0

    # Ressources
    db_connections_active: int = 0
    storage_used_gb: float = 0.0
    records_count: int = 0

    # Timestamps
    last_request_at: Optional[datetime] = None
    minute_reset_at: Optional[datetime] = None
    hour_reset_at: Optional[datetime] = None
    day_reset_at: Optional[datetime] = None

    # Violations
    violations: List[Dict] = field(default_factory=list)
    violation_count_24h: int = 0

    # Statut
    status: TenantHealthStatus = TenantHealthStatus.HEALTHY
    is_throttled: bool = False
    throttle_until: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "tier": self.tier.value,
            "requests": {
                "this_minute": self.requests_this_minute,
                "this_hour": self.requests_this_hour,
                "today": self.requests_today,
                "concurrent": self.concurrent_requests,
            },
            "performance": {
                "avg_latency_ms": self.avg_latency_ms,
                "p95_latency_ms": self.p95_latency_ms,
                "error_count_today": self.error_count_today,
                "error_rate": self.error_rate,
            },
            "resources": {
                "db_connections": self.db_connections_active,
                "storage_gb": self.storage_used_gb,
                "records": self.records_count,
            },
            "status": self.status.value,
            "is_throttled": self.is_throttled,
            "violation_count_24h": self.violation_count_24h,
        }


@dataclass
class ThrottleDecision:
    """Décision de throttling pour une requête."""
    allowed: bool
    tenant_id: str
    reason: Optional[str] = None
    retry_after_seconds: Optional[int] = None
    queue_priority: int = 5
    degraded_mode: bool = False


class TenantGovernor:
    """
    Gouverneur de tenants - Contrôle des quotas et ressources.

    Comparable à:
    - Salesforce Governor Limits
    - SAP Cloud Platform Quotas
    - AWS Service Quotas

    Responsabilités:
    1. Appliquer les quotas par tier
    2. Détecter les tenants toxiques
    3. Protéger la plateforme des abus
    4. Prioriser les tenants premium
    """

    def __init__(
        self,
        on_violation: Optional[Callable[[str, ViolationType, Dict], None]] = None,
        on_tenant_blocked: Optional[Callable[[str, str], None]] = None,
    ):
        # Usage par tenant
        self._usage: Dict[str, TenantQuotaUsage] = {}
        self._tier_cache: Dict[str, TenantTier] = {}

        # Callbacks
        self._on_violation = on_violation
        self._on_tenant_blocked = on_tenant_blocked

        # Tenants bloqués/suspendus
        self._blocked_tenants: Set[str] = set()
        self._throttled_tenants: Dict[str, datetime] = {}

        # Métriques de latence (sliding window)
        self._latencies: Dict[str, List[float]] = defaultdict(list)
        self._latency_window_size = 100

        # Lock pour thread safety
        self._lock = threading.RLock()

        # Configuration des seuils
        self._violation_thresholds = {
            ViolationType.RATE_LIMIT_EXCEEDED: 3,      # 3 violations -> throttle
            ViolationType.QUOTA_EXCEEDED: 2,           # 2 violations -> throttle
            ViolationType.SLOW_QUERIES: 5,             # 5 slow queries -> warning
            ViolationType.HIGH_ERROR_RATE: 3,          # 3 high error periods -> throttle
            ViolationType.RESOURCE_ABUSE: 1,           # 1 abuse -> immediate block
            ViolationType.SECURITY_VIOLATION: 1,       # 1 security issue -> immediate block
        }

        # Durées de throttle progressives (en secondes)
        self._throttle_durations = [60, 300, 900, 3600, 86400]  # 1m, 5m, 15m, 1h, 24h

        logger.info("[GOVERNOR] TenantGovernor initialized")

    def set_tenant_tier(self, tenant_id: str, tier: TenantTier) -> None:
        """Configure le tier d'un tenant."""
        with self._lock:
            self._tier_cache[tenant_id] = tier
            if tenant_id in self._usage:
                self._usage[tenant_id].tier = tier
            logger.debug(f"[GOVERNOR] Tenant {tenant_id} tier set to {tier.value}")

    def get_tenant_tier(self, tenant_id: str) -> TenantTier:
        """Récupère le tier d'un tenant."""
        return self._tier_cache.get(tenant_id, TenantTier.STANDARD)

    def _get_or_create_usage(self, tenant_id: str) -> TenantQuotaUsage:
        """Récupère ou crée l'usage pour un tenant."""
        if tenant_id not in self._usage:
            tier = self.get_tenant_tier(tenant_id)
            self._usage[tenant_id] = TenantQuotaUsage(
                tenant_id=tenant_id,
                tier=tier,
                minute_reset_at=datetime.utcnow(),
                hour_reset_at=datetime.utcnow(),
                day_reset_at=datetime.utcnow().replace(hour=0, minute=0, second=0),
            )
        return self._usage[tenant_id]

    def _reset_counters_if_needed(self, usage: TenantQuotaUsage) -> None:
        """Réinitialise les compteurs si nécessaire."""
        now = datetime.utcnow()

        # Reset minute
        if usage.minute_reset_at and (now - usage.minute_reset_at) >= timedelta(minutes=1):
            usage.requests_this_minute = 0
            usage.minute_reset_at = now

        # Reset heure
        if usage.hour_reset_at and (now - usage.hour_reset_at) >= timedelta(hours=1):
            usage.requests_this_hour = 0
            usage.hour_reset_at = now

        # Reset jour
        if usage.day_reset_at and (now - usage.day_reset_at) >= timedelta(days=1):
            usage.requests_today = 0
            usage.error_count_today = 0
            usage.violations = []
            usage.violation_count_24h = 0
            usage.day_reset_at = now.replace(hour=0, minute=0, second=0)

    def check_request(self, tenant_id: str) -> ThrottleDecision:
        """
        Vérifie si une requête est autorisée.

        Returns:
            ThrottleDecision indiquant si la requête est autorisée
        """
        with self._lock:
            # Tenant bloqué?
            if tenant_id in self._blocked_tenants:
                return ThrottleDecision(
                    allowed=False,
                    tenant_id=tenant_id,
                    reason="Tenant blocked due to policy violation",
                    retry_after_seconds=3600,
                )

            # Tenant throttlé?
            if tenant_id in self._throttled_tenants:
                throttle_until = self._throttled_tenants[tenant_id]
                if datetime.utcnow() < throttle_until:
                    remaining = int((throttle_until - datetime.utcnow()).total_seconds())
                    return ThrottleDecision(
                        allowed=False,
                        tenant_id=tenant_id,
                        reason="Rate limited - too many requests",
                        retry_after_seconds=remaining,
                    )
                else:
                    # Throttle expiré
                    del self._throttled_tenants[tenant_id]

            # Récupérer usage et config
            usage = self._get_or_create_usage(tenant_id)
            self._reset_counters_if_needed(usage)
            sla = get_sla_config(usage.tier)

            # Vérifier concurrent requests
            if usage.concurrent_requests >= sla.max_concurrent_requests:
                self._record_violation(tenant_id, ViolationType.RATE_LIMIT_EXCEEDED, {
                    "type": "concurrent_requests",
                    "limit": sla.max_concurrent_requests,
                    "actual": usage.concurrent_requests,
                })
                return ThrottleDecision(
                    allowed=False,
                    tenant_id=tenant_id,
                    reason=f"Max concurrent requests ({sla.max_concurrent_requests}) exceeded",
                    retry_after_seconds=5,
                    degraded_mode=True,
                )

            # Vérifier rate limit par minute
            if usage.requests_this_minute >= sla.max_requests_per_minute:
                # Appliquer burst si disponible
                burst_limit = int(sla.max_requests_per_minute * sla.burst_multiplier)
                if usage.requests_this_minute >= burst_limit:
                    self._record_violation(tenant_id, ViolationType.RATE_LIMIT_EXCEEDED, {
                        "type": "requests_per_minute",
                        "limit": sla.max_requests_per_minute,
                        "burst_limit": burst_limit,
                        "actual": usage.requests_this_minute,
                    })
                    return ThrottleDecision(
                        allowed=False,
                        tenant_id=tenant_id,
                        reason=f"Rate limit exceeded ({sla.max_requests_per_minute}/min)",
                        retry_after_seconds=60,
                    )

            # Vérifier quota journalier
            if usage.requests_today >= sla.max_requests_per_day:
                self._record_violation(tenant_id, ViolationType.QUOTA_EXCEEDED, {
                    "type": "requests_per_day",
                    "limit": sla.max_requests_per_day,
                    "actual": usage.requests_today,
                })
                return ThrottleDecision(
                    allowed=False,
                    tenant_id=tenant_id,
                    reason=f"Daily quota exceeded ({sla.max_requests_per_day}/day)",
                    retry_after_seconds=3600,
                )

            # Autoriser avec priorité
            return ThrottleDecision(
                allowed=True,
                tenant_id=tenant_id,
                queue_priority=sla.queue_priority,
            )

    def record_request_start(self, tenant_id: str) -> None:
        """Enregistre le début d'une requête."""
        with self._lock:
            usage = self._get_or_create_usage(tenant_id)
            usage.concurrent_requests += 1
            usage.requests_this_minute += 1
            usage.requests_this_hour += 1
            usage.requests_today += 1
            usage.last_request_at = datetime.utcnow()

    def record_request_end(
        self,
        tenant_id: str,
        latency_ms: float,
        success: bool,
        error_type: Optional[str] = None,
    ) -> None:
        """Enregistre la fin d'une requête."""
        with self._lock:
            usage = self._get_or_create_usage(tenant_id)
            usage.concurrent_requests = max(0, usage.concurrent_requests - 1)

            # Enregistrer latence
            self._latencies[tenant_id].append(latency_ms)
            if len(self._latencies[tenant_id]) > self._latency_window_size:
                self._latencies[tenant_id] = self._latencies[tenant_id][-self._latency_window_size:]

            # Calculer métriques
            latencies = sorted(self._latencies[tenant_id])
            usage.avg_latency_ms = sum(latencies) / len(latencies)
            p95_idx = int(len(latencies) * 0.95)
            usage.p95_latency_ms = latencies[min(p95_idx, len(latencies) - 1)]

            # Gérer les erreurs
            if not success:
                usage.error_count_today += 1

            # Calculer error rate
            if usage.requests_today > 0:
                usage.error_rate = usage.error_count_today / usage.requests_today

            # Vérifier les seuils
            sla = get_sla_config(usage.tier)

            # Slow query detection
            if latency_ms > sla.p99_latency_ms * 2:
                self._record_violation(tenant_id, ViolationType.SLOW_QUERIES, {
                    "latency_ms": latency_ms,
                    "threshold_ms": sla.p99_latency_ms,
                })

            # High error rate detection
            if usage.error_rate > 0.1 and usage.requests_today > 100:
                self._record_violation(tenant_id, ViolationType.HIGH_ERROR_RATE, {
                    "error_rate": usage.error_rate,
                    "threshold": 0.1,
                })

    def _record_violation(
        self,
        tenant_id: str,
        violation_type: ViolationType,
        details: Dict,
    ) -> None:
        """Enregistre une violation."""
        usage = self._get_or_create_usage(tenant_id)

        violation = {
            "type": violation_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
        }
        usage.violations.append(violation)
        usage.violation_count_24h += 1

        # Callback
        if self._on_violation:
            try:
                self._on_violation(tenant_id, violation_type, details)
            except Exception as e:
                logger.error(f"[GOVERNOR] Violation callback error: {e}")

        # Vérifier seuils pour actions automatiques
        threshold = self._violation_thresholds.get(violation_type, 5)
        violation_count = len([v for v in usage.violations if v["type"] == violation_type.value])

        if violation_type in [ViolationType.RESOURCE_ABUSE, ViolationType.SECURITY_VIOLATION]:
            # Blocage immédiat
            self._block_tenant(tenant_id, f"Immediate block due to {violation_type.value}")
        elif violation_count >= threshold:
            # Throttle progressif
            self._apply_throttle(tenant_id, violation_type, violation_count)

        logger.warning(
            f"[GOVERNOR] Violation recorded",
            extra={
                "tenant_id": tenant_id,
                "violation_type": violation_type.value,
                "details": details,
                "total_violations_24h": usage.violation_count_24h,
            }
        )

    def _apply_throttle(
        self,
        tenant_id: str,
        violation_type: ViolationType,
        violation_count: int,
    ) -> None:
        """Applique un throttle progressif."""
        usage = self._get_or_create_usage(tenant_id)

        # Déterminer la durée de throttle
        throttle_idx = min(violation_count - 1, len(self._throttle_durations) - 1)
        duration_seconds = self._throttle_durations[throttle_idx]

        # Appliquer
        self._throttled_tenants[tenant_id] = datetime.utcnow() + timedelta(seconds=duration_seconds)
        usage.is_throttled = True
        usage.throttle_until = self._throttled_tenants[tenant_id]
        usage.status = TenantHealthStatus.DEGRADED

        logger.warning(
            f"[GOVERNOR] Tenant throttled",
            extra={
                "tenant_id": tenant_id,
                "duration_seconds": duration_seconds,
                "violation_type": violation_type.value,
                "violation_count": violation_count,
            }
        )

    def _block_tenant(self, tenant_id: str, reason: str) -> None:
        """Bloque un tenant."""
        self._blocked_tenants.add(tenant_id)

        if tenant_id in self._usage:
            self._usage[tenant_id].status = TenantHealthStatus.BLOCKED

        if self._on_tenant_blocked:
            try:
                self._on_tenant_blocked(tenant_id, reason)
            except Exception as e:
                logger.error(f"[GOVERNOR] Block callback error: {e}")

        logger.critical(
            f"[GOVERNOR] Tenant BLOCKED",
            extra={"tenant_id": tenant_id, "reason": reason}
        )

    def unblock_tenant(self, tenant_id: str) -> bool:
        """Débloque un tenant."""
        with self._lock:
            if tenant_id in self._blocked_tenants:
                self._blocked_tenants.discard(tenant_id)
                if tenant_id in self._usage:
                    self._usage[tenant_id].status = TenantHealthStatus.WARNING
                logger.info(f"[GOVERNOR] Tenant {tenant_id} unblocked")
                return True
            return False

    def reset_throttle(self, tenant_id: str) -> bool:
        """Réinitialise le throttle d'un tenant."""
        with self._lock:
            if tenant_id in self._throttled_tenants:
                del self._throttled_tenants[tenant_id]
                if tenant_id in self._usage:
                    self._usage[tenant_id].is_throttled = False
                    self._usage[tenant_id].throttle_until = None
                    self._usage[tenant_id].status = TenantHealthStatus.HEALTHY
                logger.info(f"[GOVERNOR] Tenant {tenant_id} throttle reset")
                return True
            return False

    def get_tenant_usage(self, tenant_id: str) -> Optional[TenantQuotaUsage]:
        """Récupère l'usage d'un tenant."""
        with self._lock:
            if tenant_id in self._usage:
                return self._usage[tenant_id]
            return None

    def get_tenant_health(self, tenant_id: str) -> TenantHealthStatus:
        """Récupère le statut de santé d'un tenant."""
        with self._lock:
            if tenant_id in self._blocked_tenants:
                return TenantHealthStatus.BLOCKED
            if tenant_id in self._throttled_tenants:
                return TenantHealthStatus.DEGRADED
            if tenant_id in self._usage:
                return self._usage[tenant_id].status
            return TenantHealthStatus.HEALTHY

    def get_platform_stats(self) -> Dict:
        """Retourne les statistiques globales de la plateforme."""
        with self._lock:
            total_tenants = len(self._usage)
            blocked = len(self._blocked_tenants)
            throttled = len(self._throttled_tenants)

            by_tier = defaultdict(int)
            by_status = defaultdict(int)
            total_requests = 0
            total_errors = 0

            for usage in self._usage.values():
                by_tier[usage.tier.value] += 1
                by_status[usage.status.value] += 1
                total_requests += usage.requests_today
                total_errors += usage.error_count_today

            return {
                "total_tenants": total_tenants,
                "blocked_tenants": blocked,
                "throttled_tenants": throttled,
                "tenants_by_tier": dict(by_tier),
                "tenants_by_status": dict(by_status),
                "total_requests_today": total_requests,
                "total_errors_today": total_errors,
                "platform_error_rate": total_errors / max(total_requests, 1),
            }

    def get_toxic_tenants(self, threshold: int = 5) -> List[str]:
        """Identifie les tenants toxiques (nombreuses violations)."""
        with self._lock:
            toxic = []
            for tenant_id, usage in self._usage.items():
                if usage.violation_count_24h >= threshold:
                    toxic.append(tenant_id)
            return sorted(toxic, key=lambda t: self._usage[t].violation_count_24h, reverse=True)

    def cleanup_stale_data(self, max_age_hours: int = 24) -> int:
        """Nettoie les données obsolètes."""
        with self._lock:
            cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
            to_remove = []

            for tenant_id, usage in self._usage.items():
                if usage.last_request_at and usage.last_request_at < cutoff:
                    if tenant_id not in self._blocked_tenants:
                        to_remove.append(tenant_id)

            for tenant_id in to_remove:
                del self._usage[tenant_id]
                self._latencies.pop(tenant_id, None)

            logger.info(f"[GOVERNOR] Cleaned up {len(to_remove)} stale tenant records")
            return len(to_remove)


# Instance globale
_governor: Optional[TenantGovernor] = None


def get_governor() -> TenantGovernor:
    """Récupère l'instance globale du gouverneur."""
    global _governor
    if _governor is None:
        _governor = TenantGovernor()
    return _governor


def init_governor(
    on_violation: Optional[Callable] = None,
    on_tenant_blocked: Optional[Callable] = None,
) -> TenantGovernor:
    """Initialise le gouverneur global."""
    global _governor
    _governor = TenantGovernor(
        on_violation=on_violation,
        on_tenant_blocked=on_tenant_blocked,
    )
    return _governor
