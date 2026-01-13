"""
AZALSCORE Enterprise - SLA & Tenant Tiers
==========================================
Configuration des niveaux de service et tiers de tenants.

Niveau Enterprise: Comparable à Salesforce Trust / SAP SLA.
"""

import enum
from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import timedelta


class TenantTier(str, enum.Enum):
    """
    Niveaux de service tenant - Classification enterprise.

    CRITICAL: Clients CAC40, administrations, >1M€ ARR
    PREMIUM: ETI, >100K€ ARR
    STANDARD: PME, <100K€ ARR
    TRIAL: Période d'essai
    SANDBOX: Environnement de test/développement
    """
    CRITICAL = "critical"    # SLA 99.99%, support 24/7, isolation dédiée
    PREMIUM = "premium"      # SLA 99.95%, support heures ouvrées étendu
    STANDARD = "standard"    # SLA 99.5%, support heures ouvrées
    TRIAL = "trial"          # Best effort, pas de SLA
    SANDBOX = "sandbox"      # Aucune garantie


@dataclass
class SLAConfig:
    """
    Configuration SLA par niveau de service.

    Conforme aux standards:
    - Salesforce Trust: 99.9% (Enterprise), 99.99% (Unlimited)
    - SAP Cloud: 99.5% (Standard), 99.9% (Premium)
    """
    tier: TenantTier

    # Disponibilité garantie (%)
    availability_target: float = 99.5

    # Temps de réponse API (percentiles en ms)
    p50_latency_ms: int = 100
    p95_latency_ms: int = 500
    p99_latency_ms: int = 1000

    # Limites de ressources
    max_requests_per_minute: int = 1000
    max_requests_per_day: int = 100000
    max_concurrent_requests: int = 50
    max_db_connections: int = 10

    # Quotas stockage et données
    max_storage_gb: int = 10
    max_records_per_table: int = 100000
    max_api_payload_mb: int = 10

    # Temps de réponse support
    critical_response_hours: int = 4
    high_response_hours: int = 8
    medium_response_hours: int = 24
    low_response_hours: int = 72

    # Rétention et backup
    backup_frequency_hours: int = 24
    backup_retention_days: int = 30
    log_retention_days: int = 90

    # Priorité dans les files d'attente (1=max, 10=min)
    queue_priority: int = 5

    # Isolation
    dedicated_resources: bool = False
    dedicated_db_pool: bool = False

    # Burst capacity (multiplicateur temporaire)
    burst_multiplier: float = 1.5
    burst_duration_seconds: int = 60


# Configurations SLA pré-définies par tier
SLA_CONFIGS: Dict[TenantTier, SLAConfig] = {
    TenantTier.CRITICAL: SLAConfig(
        tier=TenantTier.CRITICAL,
        availability_target=99.99,
        p50_latency_ms=50,
        p95_latency_ms=200,
        p99_latency_ms=500,
        max_requests_per_minute=10000,
        max_requests_per_day=1000000,
        max_concurrent_requests=500,
        max_db_connections=50,
        max_storage_gb=1000,
        max_records_per_table=10000000,
        max_api_payload_mb=100,
        critical_response_hours=1,
        high_response_hours=2,
        medium_response_hours=4,
        low_response_hours=8,
        backup_frequency_hours=1,
        backup_retention_days=365,
        log_retention_days=365,
        queue_priority=1,
        dedicated_resources=True,
        dedicated_db_pool=True,
        burst_multiplier=3.0,
        burst_duration_seconds=300,
    ),
    TenantTier.PREMIUM: SLAConfig(
        tier=TenantTier.PREMIUM,
        availability_target=99.95,
        p50_latency_ms=75,
        p95_latency_ms=300,
        p99_latency_ms=750,
        max_requests_per_minute=5000,
        max_requests_per_day=500000,
        max_concurrent_requests=200,
        max_db_connections=25,
        max_storage_gb=100,
        max_records_per_table=1000000,
        max_api_payload_mb=50,
        critical_response_hours=2,
        high_response_hours=4,
        medium_response_hours=8,
        low_response_hours=24,
        backup_frequency_hours=6,
        backup_retention_days=90,
        log_retention_days=180,
        queue_priority=2,
        dedicated_resources=False,
        dedicated_db_pool=True,
        burst_multiplier=2.0,
        burst_duration_seconds=180,
    ),
    TenantTier.STANDARD: SLAConfig(
        tier=TenantTier.STANDARD,
        availability_target=99.5,
        p50_latency_ms=100,
        p95_latency_ms=500,
        p99_latency_ms=1000,
        max_requests_per_minute=1000,
        max_requests_per_day=100000,
        max_concurrent_requests=50,
        max_db_connections=10,
        max_storage_gb=10,
        max_records_per_table=100000,
        max_api_payload_mb=10,
        critical_response_hours=4,
        high_response_hours=8,
        medium_response_hours=24,
        low_response_hours=72,
        backup_frequency_hours=24,
        backup_retention_days=30,
        log_retention_days=90,
        queue_priority=5,
        dedicated_resources=False,
        dedicated_db_pool=False,
        burst_multiplier=1.5,
        burst_duration_seconds=60,
    ),
    TenantTier.TRIAL: SLAConfig(
        tier=TenantTier.TRIAL,
        availability_target=95.0,
        p50_latency_ms=200,
        p95_latency_ms=1000,
        p99_latency_ms=3000,
        max_requests_per_minute=100,
        max_requests_per_day=10000,
        max_concurrent_requests=10,
        max_db_connections=3,
        max_storage_gb=1,
        max_records_per_table=10000,
        max_api_payload_mb=5,
        critical_response_hours=24,
        high_response_hours=48,
        medium_response_hours=72,
        low_response_hours=168,
        backup_frequency_hours=168,
        backup_retention_days=7,
        log_retention_days=14,
        queue_priority=8,
        dedicated_resources=False,
        dedicated_db_pool=False,
        burst_multiplier=1.0,
        burst_duration_seconds=0,
    ),
    TenantTier.SANDBOX: SLAConfig(
        tier=TenantTier.SANDBOX,
        availability_target=90.0,
        p50_latency_ms=500,
        p95_latency_ms=2000,
        p99_latency_ms=5000,
        max_requests_per_minute=50,
        max_requests_per_day=5000,
        max_concurrent_requests=5,
        max_db_connections=2,
        max_storage_gb=0.5,
        max_records_per_table=1000,
        max_api_payload_mb=1,
        critical_response_hours=168,
        high_response_hours=168,
        medium_response_hours=168,
        low_response_hours=168,
        backup_frequency_hours=0,  # Pas de backup
        backup_retention_days=0,
        log_retention_days=7,
        queue_priority=10,
        dedicated_resources=False,
        dedicated_db_pool=False,
        burst_multiplier=1.0,
        burst_duration_seconds=0,
    ),
}


def get_sla_config(tier: TenantTier) -> SLAConfig:
    """Récupère la configuration SLA pour un tier donné."""
    return SLA_CONFIGS.get(tier, SLA_CONFIGS[TenantTier.STANDARD])


@dataclass
class SLAViolation:
    """Représente une violation de SLA détectée."""
    tenant_id: str
    tier: TenantTier
    violation_type: str  # 'availability', 'latency', 'error_rate'
    expected_value: float
    actual_value: float
    timestamp: str
    severity: str  # 'critical', 'warning', 'info'
    description: str

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "tier": self.tier.value,
            "violation_type": self.violation_type,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "timestamp": self.timestamp,
            "severity": self.severity,
            "description": self.description,
        }


@dataclass
class SLAReport:
    """Rapport SLA pour un tenant sur une période."""
    tenant_id: str
    tier: TenantTier
    period_start: str
    period_end: str

    # Métriques de disponibilité
    availability_target: float = 0.0
    availability_actual: float = 0.0
    availability_met: bool = True

    # Métriques de latence
    p50_target_ms: int = 0
    p50_actual_ms: int = 0
    p95_target_ms: int = 0
    p95_actual_ms: int = 0
    p99_target_ms: int = 0
    p99_actual_ms: int = 0
    latency_met: bool = True

    # Métriques d'erreur
    error_rate_target: float = 0.0
    error_rate_actual: float = 0.0
    error_rate_met: bool = True

    # Volume
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    # Violations
    violations: List[SLAViolation] = field(default_factory=list)

    # Score global
    sla_score: float = 100.0  # 0-100
    sla_compliant: bool = True

    def calculate_score(self) -> float:
        """Calcule le score SLA global."""
        weights = {
            'availability': 0.5,
            'latency': 0.3,
            'error_rate': 0.2,
        }

        score = 0.0

        # Disponibilité
        if self.availability_target > 0:
            avail_ratio = min(self.availability_actual / self.availability_target, 1.0)
            score += weights['availability'] * avail_ratio * 100

        # Latence (utilise P95)
        if self.p95_target_ms > 0:
            latency_ratio = min(self.p95_target_ms / max(self.p95_actual_ms, 1), 1.0)
            score += weights['latency'] * latency_ratio * 100

        # Taux d'erreur
        if self.total_requests > 0:
            actual_error_rate = self.failed_requests / self.total_requests
            if self.error_rate_target > 0:
                error_ratio = min(self.error_rate_target / max(actual_error_rate, 0.0001), 1.0)
            else:
                error_ratio = 1.0 if actual_error_rate == 0 else 0.5
            score += weights['error_rate'] * error_ratio * 100

        self.sla_score = round(score, 2)
        self.sla_compliant = (
            self.availability_met and
            self.latency_met and
            self.error_rate_met
        )

        return self.sla_score

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "tier": self.tier.value,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "availability": {
                "target": self.availability_target,
                "actual": self.availability_actual,
                "met": self.availability_met,
            },
            "latency": {
                "p50_target_ms": self.p50_target_ms,
                "p50_actual_ms": self.p50_actual_ms,
                "p95_target_ms": self.p95_target_ms,
                "p95_actual_ms": self.p95_actual_ms,
                "p99_target_ms": self.p99_target_ms,
                "p99_actual_ms": self.p99_actual_ms,
                "met": self.latency_met,
            },
            "error_rate": {
                "target": self.error_rate_target,
                "actual": self.error_rate_actual,
                "met": self.error_rate_met,
            },
            "volume": {
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
            },
            "violations_count": len(self.violations),
            "sla_score": self.sla_score,
            "sla_compliant": self.sla_compliant,
        }
