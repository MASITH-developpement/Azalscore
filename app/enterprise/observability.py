"""
AZALSCORE Enterprise - Observability SRE-Grade
==============================================
Observabilité niveau Salesforce/SAP pour équipes SRE.

Fonctionnalités:
- Métriques infra, applicatives, DB, IA, par tenant
- Métriques SLA/SLO contractuelles
- Alertes prédictives
- Dashboards exécutifs
- Health checks contractuels
- Détection proactive des dérives

Objectif: Savoir AVANT le client qu'un problème va arriver.
"""

import asyncio
import logging
import time
import threading
import statistics
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Callable, Any, Tuple
from enum import Enum
from collections import deque, defaultdict
import json

from prometheus_client import Counter, Histogram, Gauge, Info, Summary

from app.enterprise.sla import TenantTier, SLAConfig, get_sla_config, SLAReport, SLAViolation

logger = logging.getLogger(__name__)


# =============================================================================
# PROMETHEUS METRICS - ENTERPRISE GRADE
# =============================================================================

# Métriques par Tenant
TENANT_REQUESTS = Counter(
    'azals_enterprise_tenant_requests_total',
    'Total requests per tenant',
    ['tenant_id', 'tier', 'endpoint', 'method', 'status']
)

TENANT_LATENCY = Histogram(
    'azals_enterprise_tenant_latency_seconds',
    'Request latency per tenant',
    ['tenant_id', 'tier', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

TENANT_ERRORS = Counter(
    'azals_enterprise_tenant_errors_total',
    'Total errors per tenant',
    ['tenant_id', 'tier', 'error_type']
)

TENANT_QUOTA_USAGE = Gauge(
    'azals_enterprise_tenant_quota_usage_percent',
    'Quota usage percentage',
    ['tenant_id', 'tier', 'quota_type']
)

# Métriques SLA
SLA_COMPLIANCE = Gauge(
    'azals_enterprise_sla_compliance',
    'SLA compliance score (0-100)',
    ['tenant_id', 'tier', 'metric_type']
)

SLA_VIOLATIONS = Counter(
    'azals_enterprise_sla_violations_total',
    'SLA violations count',
    ['tenant_id', 'tier', 'violation_type', 'severity']
)

SLA_AVAILABILITY = Gauge(
    'azals_enterprise_sla_availability_percent',
    'Actual availability percentage',
    ['tenant_id', 'tier']
)

# Métriques Database
DB_QUERY_DURATION_BY_TENANT = Histogram(
    'azals_enterprise_db_query_duration_seconds',
    'Database query duration by tenant',
    ['tenant_id', 'operation', 'table'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

DB_CONNECTIONS_BY_TENANT = Gauge(
    'azals_enterprise_db_connections',
    'Active database connections by tenant',
    ['tenant_id', 'pool']
)

DB_SLOW_QUERIES = Counter(
    'azals_enterprise_db_slow_queries_total',
    'Slow queries count',
    ['tenant_id', 'operation']
)

# Métriques IA
AI_INFERENCE_DURATION = Histogram(
    'azals_enterprise_ai_inference_seconds',
    'AI inference duration',
    ['tenant_id', 'model', 'operation'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
)

AI_QUEUE_SIZE = Gauge(
    'azals_enterprise_ai_queue_size',
    'AI processing queue size',
    ['tenant_id', 'priority']
)

AI_TOKENS_USED = Counter(
    'azals_enterprise_ai_tokens_total',
    'AI tokens consumed',
    ['tenant_id', 'model', 'direction']
)

# Métriques Platform
PLATFORM_HEALTH = Gauge(
    'azals_enterprise_platform_health',
    'Platform health score (0-100)',
    ['component']
)

PLATFORM_CAPACITY = Gauge(
    'azals_enterprise_platform_capacity_percent',
    'Platform capacity usage',
    ['resource_type']
)


class AlertSeverity(str, Enum):
    """Niveaux de sévérité des alertes."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertCategory(str, Enum):
    """Catégories d'alertes."""
    AVAILABILITY = "availability"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    QUOTA = "quota"
    SECURITY = "security"
    CAPACITY = "capacity"
    SLA = "sla"
    PREDICTION = "prediction"


@dataclass
class Alert:
    """Représente une alerte détectée."""
    id: str
    timestamp: datetime
    category: AlertCategory
    severity: AlertSeverity
    tenant_id: Optional[str]
    title: str
    description: str
    metric_name: str
    metric_value: float
    threshold: float
    runbook_url: Optional[str] = None
    auto_resolved: bool = False
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "category": self.category.value,
            "severity": self.severity.value,
            "tenant_id": self.tenant_id,
            "title": self.title,
            "description": self.description,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "runbook_url": self.runbook_url,
            "auto_resolved": self.auto_resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "acknowledged": self.acknowledged_by is not None,
        }


@dataclass
class TenantMetrics:
    """Métriques en temps réel pour un tenant."""
    tenant_id: str
    tier: TenantTier

    # Compteurs
    requests_total: int = 0
    requests_success: int = 0
    requests_error: int = 0
    requests_slow: int = 0

    # Latences (sliding window)
    latencies_ms: deque = field(default_factory=lambda: deque(maxlen=1000))

    # Disponibilité
    uptime_checks: int = 0
    uptime_success: int = 0

    # Base de données
    db_queries_total: int = 0
    db_queries_slow: int = 0
    db_connections_active: int = 0

    # IA
    ai_requests_total: int = 0
    ai_tokens_used: int = 0
    ai_queue_depth: int = 0

    # Timestamps
    window_start: Optional[datetime] = None
    last_update: Optional[datetime] = None

    def get_availability(self) -> float:
        """Calcule le taux de disponibilité."""
        if self.uptime_checks == 0:
            return 100.0
        return (self.uptime_success / self.uptime_checks) * 100

    def get_error_rate(self) -> float:
        """Calcule le taux d'erreur."""
        if self.requests_total == 0:
            return 0.0
        return (self.requests_error / self.requests_total) * 100

    def get_latency_percentiles(self) -> Dict[str, float]:
        """Calcule les percentiles de latence."""
        if not self.latencies_ms:
            return {"p50": 0, "p95": 0, "p99": 0}

        sorted_latencies = sorted(self.latencies_ms)
        n = len(sorted_latencies)

        return {
            "p50": sorted_latencies[int(n * 0.50)],
            "p95": sorted_latencies[int(n * 0.95)],
            "p99": sorted_latencies[int(n * 0.99)] if n > 0 else sorted_latencies[-1],
        }


class EnterpriseObserver:
    """
    Observateur Enterprise - Monitoring SRE-Grade.

    Responsabilités:
    1. Collecter métriques par tenant
    2. Calculer SLA en temps réel
    3. Détecter anomalies et dérives
    4. Générer alertes prédictives
    5. Fournir dashboards exécutifs
    """

    def __init__(
        self,
        on_alert: Optional[Callable[[Alert], None]] = None,
        on_sla_violation: Optional[Callable[[str, SLAViolation], None]] = None,
    ):
        self._on_alert = on_alert
        self._on_sla_violation = on_sla_violation

        # Métriques par tenant
        self._tenant_metrics: Dict[str, TenantMetrics] = {}
        self._tier_cache: Dict[str, TenantTier] = {}

        # Alertes actives
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: deque = deque(maxlen=10000)
        self._alert_counter = 0

        # SLA tracking
        self._sla_reports: Dict[str, SLAReport] = {}

        # Prédictions (anomaly detection)
        self._baseline_latencies: Dict[str, List[float]] = defaultdict(list)
        self._baseline_error_rates: Dict[str, List[float]] = defaultdict(list)

        # Health checks
        self._component_health: Dict[str, float] = {}

        # Lock
        self._lock = threading.RLock()

        # Background tasks
        self._running = False
        self._background_task = None

        logger.info("[OBSERVER] EnterpriseObserver initialized")

    def start(self) -> None:
        """Démarre les tâches de fond."""
        self._running = True
        self._background_task = threading.Thread(target=self._background_loop, daemon=True)
        self._background_task.start()
        logger.info("[OBSERVER] Background monitoring started")

    def stop(self) -> None:
        """Arrête les tâches de fond."""
        self._running = False
        if self._background_task:
            self._background_task.join(timeout=5)
        logger.info("[OBSERVER] Background monitoring stopped")

    def _background_loop(self) -> None:
        """Boucle de fond pour analyses périodiques."""
        while self._running:
            try:
                self._check_sla_compliance()
                self._detect_anomalies()
                self._update_platform_metrics()
                self._cleanup_old_data()
            except Exception as e:
                logger.error(f"[OBSERVER] Background loop error: {e}")

            time.sleep(60)  # Check every minute

    def set_tenant_tier(self, tenant_id: str, tier: TenantTier) -> None:
        """Configure le tier d'un tenant."""
        with self._lock:
            self._tier_cache[tenant_id] = tier
            if tenant_id in self._tenant_metrics:
                self._tenant_metrics[tenant_id].tier = tier

    def _get_or_create_metrics(self, tenant_id: str) -> TenantMetrics:
        """Récupère ou crée les métriques pour un tenant."""
        if tenant_id not in self._tenant_metrics:
            tier = self._tier_cache.get(tenant_id, TenantTier.STANDARD)
            self._tenant_metrics[tenant_id] = TenantMetrics(
                tenant_id=tenant_id,
                tier=tier,
                window_start=datetime.utcnow(),
            )
        return self._tenant_metrics[tenant_id]

    # =========================================================================
    # RECORDING METHODS
    # =========================================================================

    def record_request(
        self,
        tenant_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: float,
        error_type: Optional[str] = None,
    ) -> None:
        """Enregistre une requête."""
        with self._lock:
            metrics = self._get_or_create_metrics(tenant_id)
            tier = metrics.tier

            metrics.requests_total += 1
            metrics.latencies_ms.append(latency_ms)
            metrics.last_update = datetime.utcnow()

            # Prometheus
            TENANT_REQUESTS.labels(
                tenant_id=tenant_id,
                tier=tier.value,
                endpoint=endpoint,
                method=method,
                status=str(status_code),
            ).inc()

            TENANT_LATENCY.labels(
                tenant_id=tenant_id,
                tier=tier.value,
                endpoint=endpoint,
            ).observe(latency_ms / 1000)

            if status_code >= 400:
                metrics.requests_error += 1
                TENANT_ERRORS.labels(
                    tenant_id=tenant_id,
                    tier=tier.value,
                    error_type=error_type or f"http_{status_code}",
                ).inc()
            else:
                metrics.requests_success += 1

            # Slow request?
            sla = get_sla_config(tier)
            if latency_ms > sla.p99_latency_ms:
                metrics.requests_slow += 1

    def record_db_query(
        self,
        tenant_id: str,
        operation: str,
        table: str,
        duration_ms: float,
    ) -> None:
        """Enregistre une requête DB."""
        with self._lock:
            metrics = self._get_or_create_metrics(tenant_id)

            metrics.db_queries_total += 1

            DB_QUERY_DURATION_BY_TENANT.labels(
                tenant_id=tenant_id,
                operation=operation,
                table=table,
            ).observe(duration_ms / 1000)

            # Slow query threshold: 100ms
            if duration_ms > 100:
                metrics.db_queries_slow += 1
                DB_SLOW_QUERIES.labels(
                    tenant_id=tenant_id,
                    operation=operation,
                ).inc()

    def record_ai_inference(
        self,
        tenant_id: str,
        model: str,
        operation: str,
        duration_ms: float,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """Enregistre une inférence IA."""
        with self._lock:
            metrics = self._get_or_create_metrics(tenant_id)

            metrics.ai_requests_total += 1
            metrics.ai_tokens_used += input_tokens + output_tokens

            AI_INFERENCE_DURATION.labels(
                tenant_id=tenant_id,
                model=model,
                operation=operation,
            ).observe(duration_ms / 1000)

            AI_TOKENS_USED.labels(
                tenant_id=tenant_id,
                model=model,
                direction="input",
            ).inc(input_tokens)

            AI_TOKENS_USED.labels(
                tenant_id=tenant_id,
                model=model,
                direction="output",
            ).inc(output_tokens)

    def record_uptime_check(self, tenant_id: str, success: bool) -> None:
        """Enregistre un check de disponibilité."""
        with self._lock:
            metrics = self._get_or_create_metrics(tenant_id)
            metrics.uptime_checks += 1
            if success:
                metrics.uptime_success += 1

            # Update Prometheus
            availability = metrics.get_availability()
            SLA_AVAILABILITY.labels(
                tenant_id=tenant_id,
                tier=metrics.tier.value,
            ).set(availability)

    def update_quota_usage(
        self,
        tenant_id: str,
        quota_type: str,
        usage_percent: float,
    ) -> None:
        """Met à jour l'utilisation d'un quota."""
        metrics = self._get_or_create_metrics(tenant_id)

        TENANT_QUOTA_USAGE.labels(
            tenant_id=tenant_id,
            tier=metrics.tier.value,
            quota_type=quota_type,
        ).set(usage_percent)

        # Alerte si proche du quota
        if usage_percent >= 90:
            self._create_alert(
                category=AlertCategory.QUOTA,
                severity=AlertSeverity.WARNING if usage_percent < 100 else AlertSeverity.CRITICAL,
                tenant_id=tenant_id,
                title=f"Quota {quota_type} proche de la limite",
                description=f"Utilisation à {usage_percent:.1f}%",
                metric_name=f"quota_{quota_type}",
                metric_value=usage_percent,
                threshold=90,
            )

    def update_component_health(self, component: str, health_score: float) -> None:
        """Met à jour la santé d'un composant."""
        self._component_health[component] = health_score
        PLATFORM_HEALTH.labels(component=component).set(health_score)

        if health_score < 50:
            self._create_alert(
                category=AlertCategory.AVAILABILITY,
                severity=AlertSeverity.CRITICAL,
                tenant_id=None,
                title=f"Composant {component} dégradé",
                description=f"Score de santé: {health_score:.1f}%",
                metric_name=f"health_{component}",
                metric_value=health_score,
                threshold=50,
            )

    # =========================================================================
    # SLA COMPLIANCE
    # =========================================================================

    def _check_sla_compliance(self) -> None:
        """Vérifie la conformité SLA pour tous les tenants."""
        for tenant_id, metrics in self._tenant_metrics.items():
            try:
                self._check_tenant_sla(tenant_id, metrics)
            except Exception as e:
                logger.error(f"[OBSERVER] SLA check error for {tenant_id}: {e}")

    def _check_tenant_sla(self, tenant_id: str, metrics: TenantMetrics) -> None:
        """Vérifie la conformité SLA d'un tenant."""
        sla_config = get_sla_config(metrics.tier)

        # Vérifier disponibilité
        availability = metrics.get_availability()
        if availability < sla_config.availability_target:
            violation = SLAViolation(
                tenant_id=tenant_id,
                tier=metrics.tier,
                violation_type="availability",
                expected_value=sla_config.availability_target,
                actual_value=availability,
                timestamp=datetime.utcnow().isoformat(),
                severity="critical" if availability < sla_config.availability_target - 1 else "warning",
                description=f"Availability {availability:.2f}% < target {sla_config.availability_target}%",
            )
            self._record_sla_violation(tenant_id, violation)

        # Vérifier latence
        percentiles = metrics.get_latency_percentiles()
        if percentiles["p95"] > sla_config.p95_latency_ms:
            violation = SLAViolation(
                tenant_id=tenant_id,
                tier=metrics.tier,
                violation_type="latency",
                expected_value=sla_config.p95_latency_ms,
                actual_value=percentiles["p95"],
                timestamp=datetime.utcnow().isoformat(),
                severity="warning",
                description=f"P95 latency {percentiles['p95']:.0f}ms > target {sla_config.p95_latency_ms}ms",
            )
            self._record_sla_violation(tenant_id, violation)

        # Vérifier taux d'erreur
        error_rate = metrics.get_error_rate()
        if error_rate > 1.0:  # 1% error rate threshold
            violation = SLAViolation(
                tenant_id=tenant_id,
                tier=metrics.tier,
                violation_type="error_rate",
                expected_value=1.0,
                actual_value=error_rate,
                timestamp=datetime.utcnow().isoformat(),
                severity="warning" if error_rate < 5.0 else "critical",
                description=f"Error rate {error_rate:.2f}% > target 1%",
            )
            self._record_sla_violation(tenant_id, violation)

        # Update SLA compliance gauge
        sla_score = self._calculate_sla_score(tenant_id, metrics, sla_config)
        SLA_COMPLIANCE.labels(
            tenant_id=tenant_id,
            tier=metrics.tier.value,
            metric_type="overall",
        ).set(sla_score)

    def _record_sla_violation(self, tenant_id: str, violation: SLAViolation) -> None:
        """Enregistre une violation SLA."""
        SLA_VIOLATIONS.labels(
            tenant_id=tenant_id,
            tier=violation.tier.value,
            violation_type=violation.violation_type,
            severity=violation.severity,
        ).inc()

        if self._on_sla_violation:
            try:
                self._on_sla_violation(tenant_id, violation)
            except Exception as e:
                logger.error(f"[OBSERVER] SLA violation callback error: {e}")

        # Créer alerte
        self._create_alert(
            category=AlertCategory.SLA,
            severity=AlertSeverity.WARNING if violation.severity == "warning" else AlertSeverity.CRITICAL,
            tenant_id=tenant_id,
            title=f"SLA Violation: {violation.violation_type}",
            description=violation.description,
            metric_name=f"sla_{violation.violation_type}",
            metric_value=violation.actual_value,
            threshold=violation.expected_value,
        )

    def _calculate_sla_score(
        self,
        tenant_id: str,
        metrics: TenantMetrics,
        sla_config: SLAConfig,
    ) -> float:
        """Calcule le score SLA global."""
        weights = {"availability": 0.5, "latency": 0.3, "error_rate": 0.2}
        score = 0.0

        # Disponibilité
        availability = metrics.get_availability()
        if sla_config.availability_target > 0:
            avail_score = min(availability / sla_config.availability_target, 1.0) * 100
            score += weights["availability"] * avail_score

        # Latence
        percentiles = metrics.get_latency_percentiles()
        if sla_config.p95_latency_ms > 0 and percentiles["p95"] > 0:
            latency_score = min(sla_config.p95_latency_ms / percentiles["p95"], 1.0) * 100
            score += weights["latency"] * latency_score

        # Taux d'erreur
        error_rate = metrics.get_error_rate()
        if error_rate == 0:
            score += weights["error_rate"] * 100
        elif error_rate < 1:
            score += weights["error_rate"] * (100 - error_rate * 10)

        return min(score, 100.0)

    # =========================================================================
    # ANOMALY DETECTION
    # =========================================================================

    def _detect_anomalies(self) -> None:
        """Détecte les anomalies et dérives."""
        for tenant_id, metrics in self._tenant_metrics.items():
            try:
                self._detect_tenant_anomalies(tenant_id, metrics)
            except Exception as e:
                logger.error(f"[OBSERVER] Anomaly detection error for {tenant_id}: {e}")

    def _detect_tenant_anomalies(self, tenant_id: str, metrics: TenantMetrics) -> None:
        """Détecte les anomalies pour un tenant."""
        if not metrics.latencies_ms:
            return

        # Calculer statistiques actuelles
        current_avg_latency = statistics.mean(metrics.latencies_ms)
        current_error_rate = metrics.get_error_rate()

        # Mettre à jour baseline
        self._baseline_latencies[tenant_id].append(current_avg_latency)
        self._baseline_error_rates[tenant_id].append(current_error_rate)

        # Garder 24h de baseline
        if len(self._baseline_latencies[tenant_id]) > 1440:
            self._baseline_latencies[tenant_id] = self._baseline_latencies[tenant_id][-1440:]
            self._baseline_error_rates[tenant_id] = self._baseline_error_rates[tenant_id][-1440:]

        # Pas assez de données pour détecter
        if len(self._baseline_latencies[tenant_id]) < 60:
            return

        # Calculer baseline
        baseline_latency = statistics.mean(self._baseline_latencies[tenant_id])
        baseline_latency_std = statistics.stdev(self._baseline_latencies[tenant_id]) if len(self._baseline_latencies[tenant_id]) > 1 else 0

        baseline_error = statistics.mean(self._baseline_error_rates[tenant_id])

        # Détecter anomalie de latence (> 3 écarts-types)
        if baseline_latency_std > 0:
            z_score = (current_avg_latency - baseline_latency) / baseline_latency_std
            if z_score > 3:
                self._create_alert(
                    category=AlertCategory.PREDICTION,
                    severity=AlertSeverity.WARNING,
                    tenant_id=tenant_id,
                    title="Anomalie de latence détectée",
                    description=f"Latence actuelle {current_avg_latency:.0f}ms vs baseline {baseline_latency:.0f}ms (z-score: {z_score:.1f})",
                    metric_name="latency_anomaly",
                    metric_value=current_avg_latency,
                    threshold=baseline_latency + 3 * baseline_latency_std,
                )

        # Détecter tendance à la hausse des erreurs
        if len(self._baseline_error_rates[tenant_id]) >= 10:
            recent_error_trend = statistics.mean(self._baseline_error_rates[tenant_id][-10:])
            if recent_error_trend > baseline_error * 2 and recent_error_trend > 1:
                self._create_alert(
                    category=AlertCategory.PREDICTION,
                    severity=AlertSeverity.WARNING,
                    tenant_id=tenant_id,
                    title="Tendance à la hausse des erreurs",
                    description=f"Taux d'erreur récent {recent_error_trend:.2f}% vs baseline {baseline_error:.2f}%",
                    metric_name="error_trend",
                    metric_value=recent_error_trend,
                    threshold=baseline_error * 2,
                )

    # =========================================================================
    # ALERTING
    # =========================================================================

    def _create_alert(
        self,
        category: AlertCategory,
        severity: AlertSeverity,
        tenant_id: Optional[str],
        title: str,
        description: str,
        metric_name: str,
        metric_value: float,
        threshold: float,
        runbook_url: Optional[str] = None,
    ) -> Alert:
        """Crée une nouvelle alerte."""
        with self._lock:
            self._alert_counter += 1
            alert_id = f"ALERT-{self._alert_counter:06d}"

            # Vérifier si alerte similaire déjà active
            for existing in self._active_alerts.values():
                if (
                    existing.category == category and
                    existing.tenant_id == tenant_id and
                    existing.metric_name == metric_name and
                    not existing.auto_resolved
                ):
                    # Mettre à jour l'alerte existante
                    existing.metric_value = metric_value
                    existing.timestamp = datetime.utcnow()
                    return existing

            alert = Alert(
                id=alert_id,
                timestamp=datetime.utcnow(),
                category=category,
                severity=severity,
                tenant_id=tenant_id,
                title=title,
                description=description,
                metric_name=metric_name,
                metric_value=metric_value,
                threshold=threshold,
                runbook_url=runbook_url,
            )

            self._active_alerts[alert_id] = alert
            self._alert_history.append(alert)

            logger.warning(
                f"[OBSERVER] Alert created: {title}",
                extra={
                    "alert_id": alert_id,
                    "category": category.value,
                    "severity": severity.value,
                    "tenant_id": tenant_id,
                }
            )

            if self._on_alert:
                try:
                    self._on_alert(alert)
                except Exception as e:
                    logger.error(f"[OBSERVER] Alert callback error: {e}")

            return alert

    def resolve_alert(self, alert_id: str, auto: bool = False) -> bool:
        """Résout une alerte."""
        with self._lock:
            if alert_id in self._active_alerts:
                alert = self._active_alerts[alert_id]
                alert.auto_resolved = auto
                alert.resolved_at = datetime.utcnow()
                del self._active_alerts[alert_id]
                logger.info(f"[OBSERVER] Alert {alert_id} resolved (auto={auto})")
                return True
            return False

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acquitte une alerte."""
        with self._lock:
            if alert_id in self._active_alerts:
                alert = self._active_alerts[alert_id]
                alert.acknowledged_by = acknowledged_by
                alert.acknowledged_at = datetime.utcnow()
                return True
            return False

    def get_active_alerts(
        self,
        tenant_id: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
    ) -> List[Alert]:
        """Récupère les alertes actives."""
        with self._lock:
            alerts = list(self._active_alerts.values())

            if tenant_id:
                alerts = [a for a in alerts if a.tenant_id == tenant_id]
            if severity:
                alerts = [a for a in alerts if a.severity == severity]

            return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    # =========================================================================
    # DASHBOARD DATA
    # =========================================================================

    def get_executive_dashboard(self) -> Dict[str, Any]:
        """Retourne les données pour le dashboard exécutif."""
        with self._lock:
            total_tenants = len(self._tenant_metrics)
            total_requests = sum(m.requests_total for m in self._tenant_metrics.values())
            total_errors = sum(m.requests_error for m in self._tenant_metrics.values())

            # Métriques par tier
            by_tier: Dict[str, Dict] = defaultdict(lambda: {
                "count": 0,
                "requests": 0,
                "errors": 0,
                "avg_latency": 0,
            })

            for metrics in self._tenant_metrics.values():
                tier = metrics.tier.value
                by_tier[tier]["count"] += 1
                by_tier[tier]["requests"] += metrics.requests_total
                by_tier[tier]["errors"] += metrics.requests_error
                if metrics.latencies_ms:
                    by_tier[tier]["avg_latency"] += statistics.mean(metrics.latencies_ms)

            # Normaliser latences
            for tier_data in by_tier.values():
                if tier_data["count"] > 0:
                    tier_data["avg_latency"] /= tier_data["count"]

            # Top 5 tenants par requêtes
            top_tenants = sorted(
                self._tenant_metrics.items(),
                key=lambda x: x[1].requests_total,
                reverse=True
            )[:5]

            # Alertes critiques
            critical_alerts = [
                a.to_dict() for a in self._active_alerts.values()
                if a.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]
            ]

            return {
                "summary": {
                    "total_tenants": total_tenants,
                    "total_requests": total_requests,
                    "total_errors": total_errors,
                    "error_rate": (total_errors / max(total_requests, 1)) * 100,
                    "active_alerts": len(self._active_alerts),
                    "critical_alerts": len(critical_alerts),
                },
                "by_tier": dict(by_tier),
                "top_tenants": [
                    {
                        "tenant_id": t_id,
                        "requests": m.requests_total,
                        "error_rate": m.get_error_rate(),
                        "tier": m.tier.value,
                    }
                    for t_id, m in top_tenants
                ],
                "critical_alerts": critical_alerts[:10],
                "component_health": dict(self._component_health),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def get_tenant_dashboard(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Retourne les données dashboard pour un tenant."""
        with self._lock:
            if tenant_id not in self._tenant_metrics:
                return None

            metrics = self._tenant_metrics[tenant_id]
            sla_config = get_sla_config(metrics.tier)

            return {
                "tenant_id": tenant_id,
                "tier": metrics.tier.value,
                "metrics": {
                    "requests": {
                        "total": metrics.requests_total,
                        "success": metrics.requests_success,
                        "errors": metrics.requests_error,
                        "slow": metrics.requests_slow,
                    },
                    "latency": metrics.get_latency_percentiles(),
                    "availability": metrics.get_availability(),
                    "error_rate": metrics.get_error_rate(),
                    "database": {
                        "queries_total": metrics.db_queries_total,
                        "queries_slow": metrics.db_queries_slow,
                        "connections": metrics.db_connections_active,
                    },
                    "ai": {
                        "requests": metrics.ai_requests_total,
                        "tokens_used": metrics.ai_tokens_used,
                        "queue_depth": metrics.ai_queue_depth,
                    },
                },
                "sla": {
                    "availability_target": sla_config.availability_target,
                    "availability_actual": metrics.get_availability(),
                    "latency_p95_target_ms": sla_config.p95_latency_ms,
                    "latency_p95_actual_ms": metrics.get_latency_percentiles()["p95"],
                    "compliance_score": self._calculate_sla_score(tenant_id, metrics, sla_config),
                },
                "alerts": [
                    a.to_dict() for a in self._active_alerts.values()
                    if a.tenant_id == tenant_id
                ],
                "last_update": metrics.last_update.isoformat() if metrics.last_update else None,
            }

    # =========================================================================
    # PLATFORM METRICS
    # =========================================================================

    def _update_platform_metrics(self) -> None:
        """Met à jour les métriques platform globales."""
        total_concurrent = sum(
            m.db_connections_active for m in self._tenant_metrics.values()
        )

        PLATFORM_CAPACITY.labels(resource_type="db_connections").set(
            total_concurrent / 100 * 100  # Assuming 100 max connections
        )

    def _cleanup_old_data(self) -> None:
        """Nettoie les données obsolètes."""
        cutoff = datetime.utcnow() - timedelta(hours=24)

        # Nettoyer alertes résolues
        to_remove = []
        for alert_id, alert in self._active_alerts.items():
            if alert.resolved_at and alert.resolved_at < cutoff:
                to_remove.append(alert_id)

        for alert_id in to_remove:
            del self._active_alerts[alert_id]

        # Nettoyer métriques tenants inactifs
        inactive = []
        for tenant_id, metrics in self._tenant_metrics.items():
            if metrics.last_update and metrics.last_update < cutoff:
                inactive.append(tenant_id)

        for tenant_id in inactive:
            del self._tenant_metrics[tenant_id]
            self._baseline_latencies.pop(tenant_id, None)
            self._baseline_error_rates.pop(tenant_id, None)

        if to_remove or inactive:
            logger.info(f"[OBSERVER] Cleanup: {len(to_remove)} alerts, {len(inactive)} tenants")


# Instance globale
_observer: Optional[EnterpriseObserver] = None


def get_observer() -> EnterpriseObserver:
    """Récupère l'instance globale de l'observateur."""
    global _observer
    if _observer is None:
        _observer = EnterpriseObserver()
    return _observer


def init_observer(
    on_alert: Optional[Callable] = None,
    on_sla_violation: Optional[Callable] = None,
) -> EnterpriseObserver:
    """Initialise l'observateur global."""
    global _observer
    _observer = EnterpriseObserver(
        on_alert=on_alert,
        on_sla_violation=on_sla_violation,
    )
    _observer.start()
    return _observer
