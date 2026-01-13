"""
AZALSCORE Enterprise - API Router
==================================
Endpoints API pour les fonctionnalités enterprise.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.dependencies import get_current_user
from app.core.models import User

from app.enterprise.sla import TenantTier, get_sla_config, SLA_CONFIGS
from app.enterprise.governance import get_governor
from app.enterprise.observability import get_observer
from app.enterprise.resilience import get_resilience_status
from app.enterprise.security import (
    get_audit_logger,
    get_compliance_checker,
    SecurityEventType,
)
from app.enterprise.operations import (
    get_onboarding_service,
    get_offboarding_service,
    get_incident_manager,
    list_runbooks,
    get_runbook,
)

router = APIRouter(prefix="/enterprise", tags=["enterprise"])


# =============================================================================
# SLA & GOVERNANCE
# =============================================================================

@router.get("/sla/tiers")
async def list_sla_tiers():
    """Liste tous les tiers SLA disponibles."""
    return {
        "tiers": [
            {
                "tier": tier.value,
                "availability_target": config.availability_target,
                "p95_latency_ms": config.p95_latency_ms,
                "max_requests_per_minute": config.max_requests_per_minute,
                "max_requests_per_day": config.max_requests_per_day,
                "queue_priority": config.queue_priority,
                "dedicated_resources": config.dedicated_resources,
            }
            for tier, config in SLA_CONFIGS.items()
        ]
    }


@router.get("/sla/tenant/{tenant_id}")
async def get_tenant_sla(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
):
    """Récupère la configuration SLA d'un tenant."""
    governor = get_governor()
    tier = governor.get_tenant_tier(tenant_id)
    config = get_sla_config(tier)

    return {
        "tenant_id": tenant_id,
        "tier": tier.value,
        "sla": {
            "availability_target": config.availability_target,
            "p50_latency_ms": config.p50_latency_ms,
            "p95_latency_ms": config.p95_latency_ms,
            "p99_latency_ms": config.p99_latency_ms,
            "max_requests_per_minute": config.max_requests_per_minute,
            "max_requests_per_day": config.max_requests_per_day,
            "max_concurrent_requests": config.max_concurrent_requests,
            "max_db_connections": config.max_db_connections,
            "backup_frequency_hours": config.backup_frequency_hours,
            "backup_retention_days": config.backup_retention_days,
        }
    }


@router.get("/governance/stats")
async def get_governance_stats(
    current_user: User = Depends(get_current_user),
):
    """Statistiques globales de gouvernance."""
    governor = get_governor()
    return governor.get_platform_stats()


@router.get("/governance/tenant/{tenant_id}")
async def get_tenant_governance(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
):
    """Statistiques de gouvernance d'un tenant."""
    governor = get_governor()
    usage = governor.get_tenant_usage(tenant_id)

    if not usage:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return usage.to_dict()


@router.get("/governance/toxic-tenants")
async def get_toxic_tenants(
    threshold: int = Query(default=5, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """Liste les tenants toxiques."""
    governor = get_governor()
    toxic = governor.get_toxic_tenants(threshold)
    return {"toxic_tenants": toxic, "threshold": threshold}


# =============================================================================
# OBSERVABILITY
# =============================================================================

@router.get("/observability/dashboard")
async def get_executive_dashboard(
    current_user: User = Depends(get_current_user),
):
    """Dashboard exécutif enterprise."""
    observer = get_observer()
    return observer.get_executive_dashboard()


@router.get("/observability/tenant/{tenant_id}")
async def get_tenant_dashboard(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
):
    """Dashboard d'un tenant spécifique."""
    observer = get_observer()
    dashboard = observer.get_tenant_dashboard(tenant_id)

    if not dashboard:
        raise HTTPException(status_code=404, detail="Tenant metrics not found")

    return dashboard


@router.get("/observability/alerts")
async def get_active_alerts(
    tenant_id: Optional[str] = None,
    severity: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Liste les alertes actives."""
    observer = get_observer()

    from app.enterprise.observability import AlertSeverity
    sev = AlertSeverity(severity) if severity else None

    alerts = observer.get_active_alerts(tenant_id=tenant_id, severity=sev)
    return {"alerts": [a.to_dict() for a in alerts]}


@router.post("/observability/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
):
    """Acquitte une alerte."""
    observer = get_observer()
    success = observer.acknowledge_alert(alert_id, current_user.email)

    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {"acknowledged": True, "alert_id": alert_id}


# =============================================================================
# RESILIENCE
# =============================================================================

@router.get("/resilience/status")
async def get_resilience_status_endpoint(
    current_user: User = Depends(get_current_user),
):
    """Statut des composants de résilience."""
    return get_resilience_status()


# =============================================================================
# SECURITY & COMPLIANCE
# =============================================================================

@router.get("/security/audit-log")
async def get_audit_log(
    tenant_id: Optional[str] = None,
    event_type: Optional[str] = None,
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
):
    """Récupère le log d'audit de sécurité."""
    logger = get_audit_logger()

    evt_type = None
    if event_type:
        try:
            evt_type = SecurityEventType(event_type)
        except ValueError:
            pass

    since = datetime.utcnow() - timedelta(hours=hours)
    events = logger.get_events(
        tenant_id=tenant_id,
        event_type=evt_type,
        since=since,
        limit=limit,
    )

    return {"events": [e.to_dict() for e in events]}


@router.get("/security/audit-summary")
async def get_audit_summary(
    tenant_id: Optional[str] = None,
    hours: int = Query(default=24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
):
    """Résumé des événements d'audit."""
    logger = get_audit_logger()
    return logger.get_summary(tenant_id=tenant_id, hours=hours)


@router.get("/compliance/check/{framework}")
async def run_compliance_check(
    framework: str,
    current_user: User = Depends(get_current_user),
):
    """Exécute une vérification de conformité."""
    checker = get_compliance_checker()

    if framework == "iso27001":
        return checker.check_iso27001()
    elif framework == "soc2":
        return checker.check_soc2()
    elif framework == "rgpd":
        return checker.check_rgpd()
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown framework: {framework}. Use: iso27001, soc2, rgpd"
        )


# =============================================================================
# OPERATIONS
# =============================================================================

@router.get("/operations/runbooks")
async def list_runbooks_endpoint(
    current_user: User = Depends(get_current_user),
):
    """Liste les runbooks disponibles."""
    return {"runbooks": list_runbooks()}


@router.get("/operations/runbooks/{runbook_id}")
async def get_runbook_endpoint(
    runbook_id: str,
    current_user: User = Depends(get_current_user),
):
    """Récupère un runbook."""
    runbook = get_runbook(runbook_id)
    if not runbook:
        raise HTTPException(status_code=404, detail="Runbook not found")
    return runbook


@router.get("/operations/incidents")
async def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
):
    """Liste les incidents."""
    manager = get_incident_manager()

    from app.enterprise.operations import IncidentStatus, IncidentSeverity

    inc_status = IncidentStatus(status) if status else None
    inc_severity = IncidentSeverity(severity) if severity else None

    incidents = manager.list_incidents(
        status=inc_status,
        severity=inc_severity,
        active_only=active_only,
    )

    return {"incidents": [i.to_dict() for i in incidents]}


@router.get("/operations/incidents/{incident_id}")
async def get_incident(
    incident_id: str,
    current_user: User = Depends(get_current_user),
):
    """Récupère un incident."""
    manager = get_incident_manager()
    incident = manager.get_incident(incident_id)

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return incident.to_dict()


@router.get("/operations/incidents/stats")
async def get_incident_stats(
    current_user: User = Depends(get_current_user),
):
    """Statistiques des incidents."""
    manager = get_incident_manager()
    return manager.get_incident_stats()


@router.get("/operations/onboarding")
async def list_onboarding_processes(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Liste les processus d'onboarding."""
    service = get_onboarding_service()

    from app.enterprise.operations import OnboardingStatus

    onb_status = OnboardingStatus(status) if status else None
    processes = service.list_processes(status=onb_status)

    return {"processes": [p.to_dict() for p in processes]}


@router.get("/operations/onboarding/{tenant_id}")
async def get_onboarding_status(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
):
    """Statut d'un onboarding."""
    service = get_onboarding_service()
    process = service.get_status(tenant_id)

    if not process:
        raise HTTPException(status_code=404, detail="Onboarding not found")

    return process.to_dict()


# =============================================================================
# HEALTH & STATUS
# =============================================================================

@router.get("/health/enterprise")
async def enterprise_health():
    """Health check enterprise."""
    governor = get_governor()
    observer = get_observer()

    stats = governor.get_platform_stats()
    dashboard = observer.get_executive_dashboard()

    return {
        "status": "healthy",
        "enterprise_version": "1.0.0",
        "tenants": {
            "total": stats["total_tenants"],
            "blocked": stats["blocked_tenants"],
            "throttled": stats["throttled_tenants"],
        },
        "alerts": {
            "total": dashboard["summary"]["active_alerts"],
            "critical": dashboard["summary"]["critical_alerts"],
        },
        "component_health": dashboard.get("component_health", {}),
        "timestamp": datetime.utcnow().isoformat(),
    }
