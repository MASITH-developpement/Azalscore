"""
AZALS MODULE AUDIT - Router API v2 (CORE SaaS)
===============================================

✅ MIGRÉ CORE SaaS Phase 2.2
- Utilise get_saas_context() au lieu de get_current_user()
- Isolation tenant automatique via context.tenant_id
- Audit trail automatique via context.user_id
- Suppression request.state.tenant_id (middleware)

Endpoints API pour l'audit et les benchmarks.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext

from .models import AuditAction, AuditCategory, AuditLevel, ComplianceFramework
from .schemas import (
    AuditDashboardResponseSchema,
    AuditLogListResponseSchema,
    AuditLogResponseSchema,
    AuditSessionResponseSchema,
    AuditStatsSchema,
    BenchmarkCreateSchema,
    BenchmarkResponseSchema,
    BenchmarkResultResponseSchema,
    ComplianceCheckCreateSchema,
    ComplianceCheckResponseSchema,
    ComplianceSummarySchema,
    ComplianceUpdateSchema,
    DashboardCreateSchema,
    DashboardDataResponseSchema,
    DashboardResponseSchema,
    ExportCreateSchema,
    ExportResponseSchema,
    MetricCreateSchema,
    MetricResponseSchema,
    MetricValueResponseSchema,
    MetricValueSchema,
    RetentionRuleCreateSchema,
    RetentionRuleResponseSchema,
)
from .service import get_audit_service

router = APIRouter(prefix="/v2/audit", tags=["Audit & Benchmark v2"])


# ============================================================================
# SERVICE DEPENDENCY v2
# ============================================================================

def get_service_v2(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
) -> object:
    """✅ MIGRÉ CORE SaaS: Utilise context.tenant_id"""
    return get_audit_service(db, context.tenant_id)


# ============================================================================
# AUDIT LOGS
# ============================================================================

@router.get("/logs", response_model=AuditLogListResponseSchema)
async def search_audit_logs(
    action: AuditAction | None = Query(None),
    level: AuditLevel | None = Query(None),
    category: AuditCategory | None = Query(None),
    module: str | None = Query(None),
    entity_type: str | None = Query(None),
    entity_id: str | None = Query(None),
    user_id: UUID | str | None = Query(None),
    session_id: str | None = Query(None),
    success: bool | None = Query(None),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    search_text: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Recherche dans les logs d'audit.

    Changements:
    - request.state.tenant_id → context.tenant_id
    - current_user → context
    - Nécessite: audit.logs.read (vérifié par decorateur)
    """
    service = get_audit_service(db, context.tenant_id)
    offset = (page - 1) * page_size

    logs, total = service.search_logs(
        action=action,
        level=level,
        category=category,
        module=module,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        session_id=session_id,
        success=success,
        from_date=from_date,
        to_date=to_date,
        search_text=search_text,
        limit=page_size,
        offset=offset
    )

    return AuditLogListResponseSchema(
        logs=logs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/logs/{log_id}", response_model=AuditLogResponseSchema)
async def get_audit_log(
    log_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère un log d'audit par son ID.

    Changements:
    - request.state.tenant_id → context.tenant_id
    """
    service = get_audit_service(db, context.tenant_id)
    log = service.get_log(log_id)

    if not log:
        raise HTTPException(status_code=404, detail=f"Log {log_id} non trouvé")

    return log


@router.get("/logs/entity/{entity_type}/{entity_id}", response_model=list[AuditLogResponseSchema])
async def get_entity_logs(
    entity_type: str,
    entity_id: str,
    action: AuditAction | None = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère l'historique d'audit d'une entité.

    Changements:
    - request.state.tenant_id → context.tenant_id
    """
    service = get_audit_service(db, context.tenant_id)
    logs = service.get_entity_history(
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit
    )
    return logs


@router.get("/logs/user/{user_id}", response_model=list[AuditLogResponseSchema])
async def get_user_logs(
    user_id: UUID | str,
    action: AuditAction | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère l'historique d'audit d'un utilisateur.

    Changements:
    - request.state.tenant_id → context.tenant_id
    """
    service = get_audit_service(db, context.tenant_id)
    logs = service.get_user_activity(
        user_id=user_id,
        from_date=from_date,
        to_date=to_date,
        limit=limit
    )
    return logs


# ============================================================================
# SESSIONS
# ============================================================================

@router.get("/sessions", response_model=list[AuditSessionResponseSchema])
async def list_active_sessions(
    user_id: UUID | str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Liste les sessions actives.

    Changements:
    - request.state.tenant_id → context.tenant_id
    """
    service = get_audit_service(db, context.tenant_id)
    sessions = service.get_active_sessions(user_id=user_id)
    return sessions


@router.post("/sessions/{session_id}/terminate")
async def terminate_session(
    session_id: str,
    reason: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Termine une session active.

    Changements:
    - request.state.tenant_id → context.tenant_id
    - current_user.id → context.user_id
    """
    service = get_audit_service(db, context.tenant_id)
    service.end_session(
        session_id=session_id,
        reason=reason
    )
    return {"status": "terminated", "session_id": session_id}


# ============================================================================
# METRICS
# ============================================================================

@router.post("/metrics", response_model=MetricResponseSchema)
async def create_metric(
    data: MetricCreateSchema,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Crée une nouvelle métrique.

    Changements:
    - request.state.tenant_id → context.tenant_id
    - current_user.id → context.user_id
    """
    service = get_audit_service(db, context.tenant_id)
    metric = service.create_metric(
        code=data.code,
        name=data.name,
        metric_type=data.metric_type,
        unit=data.unit,
        module=data.module,
        aggregation_period=data.aggregation_period,
        retention_days=data.retention_days,
        warning_threshold=data.warning_threshold,
        critical_threshold=data.critical_threshold
    )
    return metric


@router.get("/metrics", response_model=list[MetricResponseSchema])
async def list_metrics(
    module: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Liste les métriques.

    Changements:
    - request.state.tenant_id → context.tenant_id
    """
    service = get_audit_service(db, context.tenant_id)
    metrics = service.list_metrics(module=module)
    return metrics


@router.post("/metrics/record", response_model=MetricValueResponseSchema)
async def record_metric_value(
    data: MetricValueSchema,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Enregistre une valeur de métrique.

    Changements:
    - request.state.tenant_id → context.tenant_id
    """
    service = get_audit_service(db, context.tenant_id)
    value = service.record_metric(
        metric_code=data.metric_code,
        value=data.value,
        dimensions=data.dimensions
    )
    if not value:
        raise HTTPException(status_code=404, detail=f"Métrique {data.metric_code} non trouvée")
    return value


@router.get("/metrics/{metric_code}/values", response_model=list[MetricValueResponseSchema])
async def get_metric_values(
    metric_code: str,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère les valeurs d'une métrique.

    Changements:
    - request.state.tenant_id → context.tenant_id
    """
    service = get_audit_service(db, context.tenant_id)
    values = service.get_metric_values(
        metric_code=metric_code,
        from_date=from_date,
        to_date=to_date,
        limit=limit
    )
    return values


# ============================================================================
# BENCHMARKS
# ============================================================================

@router.post("/benchmarks", response_model=BenchmarkResponseSchema)
async def create_benchmark(
    data: BenchmarkCreateSchema,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Crée un nouveau benchmark.

    Changements:
    - request.state.tenant_id → context.tenant_id
    - current_user.id → context.user_id
    """
    service = get_audit_service(db, context.tenant_id)
    benchmark = service.create_benchmark(
        code=data.code,
        name=data.name,
        benchmark_type=data.benchmark_type,
        description=data.description,
        module=data.module,
        config=data.config,
        baseline=data.baseline,
        created_by=context.user_id
    )
    return benchmark


@router.get("/benchmarks", response_model=list[BenchmarkResponseSchema])
async def list_benchmarks(
    benchmark_type: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Liste les benchmarks.

    Changements:
    - request.state.tenant_id → context.tenant_id
    """
    service = get_audit_service(db, context.tenant_id)
    benchmarks = service.list_benchmarks(benchmark_type=benchmark_type)
    return benchmarks


@router.post("/benchmarks/{benchmark_id}/run", response_model=BenchmarkResultResponseSchema)
async def run_benchmark(
    benchmark_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Exécute un benchmark.

    Changements:
    - request.state.tenant_id → context.tenant_id
    - current_user.id → context.user_id
    """
    service = get_audit_service(db, context.tenant_id)
    result = service.run_benchmark(benchmark_id, executed_by=context.user_id)

    # Optionnel: exécution asynchrone
    # background_tasks.add_task(service.run_benchmark_async, benchmark_id, context.user_id)

    return result


@router.get("/benchmarks/{benchmark_id}/results", response_model=list[BenchmarkResultResponseSchema])
async def get_benchmark_results(
    benchmark_id: UUID,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère les résultats d'un benchmark.

    Changements:
    - request.state.tenant_id → context.tenant_id
    """
    service = get_audit_service(db, context.tenant_id)
    results = service.get_benchmark_results(benchmark_id, limit=limit)
    return results


# ============================================================================
# COMPLIANCE CHECKS
# ============================================================================

@router.post("/compliance/checks", response_model=ComplianceCheckResponseSchema)
async def create_compliance_check(
    data: ComplianceCheckCreateSchema,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Crée un contrôle de conformité.

    Changements:
    - request.state.tenant_id → context.tenant_id
    - current_user.id → context.user_id
    """
    service = get_audit_service(db, context.tenant_id)
    check = service.create_compliance_check(
        framework=data.framework,
        control_id=data.control_id,
        control_name=data.control_name,
        check_type=data.check_type,
        control_description=data.control_description,
        category=data.category,
        subcategory=data.subcategory,
        severity=data.severity
    )
    return check


@router.get("/compliance/checks", response_model=list[ComplianceCheckResponseSchema])
async def list_compliance_checks(
    framework: ComplianceFramework | None = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Liste les contrôles de conformité.

    Changements:
    - request.state.tenant_id → context.tenant_id
    """
    service = get_audit_service(db, context.tenant_id)
    checks = service.list_compliance_checks(framework=framework, is_active=is_active)
    return checks


@router.put("/compliance/checks/{check_id}", response_model=ComplianceCheckResponseSchema)
async def update_compliance_check(
    check_id: UUID,
    data: ComplianceUpdateSchema,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Met à jour un contrôle de conformité.

    Changements:
    - request.state.tenant_id → context.tenant_id
    - current_user.id → context.user_id
    """
    service = get_audit_service(db, context.tenant_id)
    check = service.update_compliance_status(
        check_id=check_id,
        status=data.status,
        actual_result=data.actual_result,
        evidence=data.evidence,
        checked_by=context.user_id
    )
    return check


@router.get("/compliance/summary", response_model=ComplianceSummarySchema)
async def get_compliance_summary(
    framework: ComplianceFramework | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère le résumé de conformité.

    Changements:
    - request.state.tenant_id → context.tenant_id
    """
    service = get_audit_service(db, context.tenant_id)
    summary = service.get_compliance_summary(framework=framework)
    return summary


# ============================================================================
# RETENTION RULES
# ============================================================================

@router.post("/retention/rules", response_model=RetentionRuleResponseSchema)
async def create_retention_rule(
    data: RetentionRuleCreateSchema,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Crée une règle de rétention.

    Changements:
    - request.state.tenant_id → context.tenant_id
    - current_user.id → context.user_id
    """
    service = get_audit_service(db, context.tenant_id)
    rule = service.create_retention_rule(
        name=data.name,
        target_table=data.target_table,
        policy=data.policy,
        retention_days=data.retention_days,
        target_module=data.target_module,
        condition=data.condition,
        action=data.action,
        schedule_cron=data.schedule_cron
    )
    return rule


@router.get("/retention/rules", response_model=list[RetentionRuleResponseSchema])
async def list_retention_rules(
    target_module: str | None = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Liste les règles de rétention.

    Changements:
    - request.state.tenant_id → context.tenant_id
    """
    service = get_audit_service(db, context.tenant_id)
    rules = service.list_retention_rules(target_module=target_module, is_active=is_active)
    return rules


@router.post("/retention/apply")
async def apply_retention_rules(
    background_tasks: BackgroundTasks,
    dry_run: bool = Query(False),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Applique les règles de rétention.

    Changements:
    - request.state.tenant_id → context.tenant_id
    - current_user.id → context.user_id
    """
    service = get_audit_service(db, context.tenant_id)

    if dry_run:
        # Preview: juste retourner le nombre de règles actives
        rules = service.list_retention_rules(is_active=True)
        return {"status": "preview", "rules_count": len(rules)}

    # Exécution asynchrone
    background_tasks.add_task(service.apply_retention_rules)

    return {"status": "started", "message": "Règles de rétention en cours d'application"}


# ============================================================================
# EXPORTS
# ============================================================================

@router.post("/exports", response_model=ExportResponseSchema)
async def create_export(
    data: ExportCreateSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Crée un export d'audit.

    Changements:
    - request.state.tenant_id → context.tenant_id
    - current_user.id → context.user_id
    """
    service = get_audit_service(db, context.tenant_id)
    export = service.create_export(
        export_type=data.export_type,
        format=data.format,
        requested_by=context.user_id,
        date_from=data.date_from,
        date_to=data.date_to,
        filters=data.filters
    )

    # Génération asynchrone
    background_tasks.add_task(service.process_export, export.id)

    return export


@router.get("/exports", response_model=list[ExportResponseSchema])
async def list_exports(
    status: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Liste les exports d'audit.

    Changements:
    - request.state.tenant_id → context.tenant_id
    """
    service = get_audit_service(db, context.tenant_id)
    exports = service.list_exports(status=status)
    return exports


@router.get("/exports/{export_id}", response_model=ExportResponseSchema)
async def get_export(
    export_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère un export par son ID.

    Changements:
    - request.state.tenant_id → context.tenant_id
    """
    service = get_audit_service(db, context.tenant_id)
    export = service.get_export(export_id)

    if not export:
        raise HTTPException(status_code=404, detail=f"Export {export_id} non trouvé")

    return export


@router.post("/exports/{export_id}/process", response_model=ExportResponseSchema)
async def process_export(
    export_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Traite (regénère) un export.

    Changements:
    - request.state.tenant_id → context.tenant_id
    """
    service = get_audit_service(db, context.tenant_id)

    # Vérifier que l'export existe
    export = service.get_export(export_id)
    if not export:
        raise HTTPException(status_code=404, detail=f"Export {export_id} non trouvé")

    # Traitement asynchrone
    background_tasks.add_task(service.process_export, export_id)

    return export


# ============================================================================
# DASHBOARDS
# ============================================================================

@router.post("/dashboards", response_model=DashboardResponseSchema)
async def create_dashboard(
    data: DashboardCreateSchema,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Crée un dashboard personnalisé.

    Changements:
    - request.state.tenant_id → context.tenant_id
    - current_user.id → context.user_id
    """
    service = get_audit_service(db, context.tenant_id)
    # Convertir les widgets en dictionnaires
    widgets_data = [w.model_dump() for w in data.widgets]
    dashboard = service.create_dashboard(
        code=data.code,
        name=data.name,
        widgets=widgets_data,
        owner_id=context.user_id,
        description=data.description,
        layout=data.layout,
        refresh_interval=data.refresh_interval
    )
    return dashboard


@router.get("/dashboards", response_model=list[DashboardResponseSchema])
async def list_dashboards(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Liste les dashboards.

    Changements:
    - request.state.tenant_id → context.tenant_id
    """
    service = get_audit_service(db, context.tenant_id)
    dashboards = service.list_dashboards()
    return dashboards


@router.get("/dashboards/{dashboard_id}/data", response_model=DashboardDataResponseSchema)
async def get_dashboard_data(
    dashboard_id: UUID,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère les données d'un dashboard.

    Changements:
    - request.state.tenant_id → context.tenant_id
    """
    service = get_audit_service(db, context.tenant_id)
    data = service.get_dashboard_data(dashboard_id=dashboard_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Dashboard {dashboard_id} non trouvé")
    return data


# ============================================================================
# STATISTICS
# ============================================================================

@router.get("/stats", response_model=AuditStatsSchema)
async def get_audit_stats(
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère les statistiques d'audit.

    Changements:
    - request.state.tenant_id → context.tenant_id
    """
    service = get_audit_service(db, context.tenant_id)
    stats = service.get_stats(from_date=from_date, to_date=to_date)
    return stats


@router.get("/dashboard", response_model=AuditDashboardResponseSchema)
async def get_audit_dashboard(
    period: str = Query("7d", regex="^(24h|7d|30d|90d|365d)$"),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupère le dashboard d'audit principal.

    Changements:
    - request.state.tenant_id → context.tenant_id
    """
    service = get_audit_service(db, context.tenant_id)
    dashboard = service.get_audit_dashboard(period=period)
    return dashboard
