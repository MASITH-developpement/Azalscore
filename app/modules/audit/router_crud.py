"""
AZALS MODULE AUDIT - Router Unifié
==================================
Router unifié compatible v1/v2 via double enregistrement.
Utilise get_context() de app.core.compat pour l'isolation tenant.
"""

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db

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

router = APIRouter(prefix="/audit", tags=["Audit & Benchmark"])

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
    user_id: int | None = Query(None),
    session_id: str | None = Query(None),
    success: bool | None = Query(None),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    search_text: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Recherche dans les logs d'audit."""
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
    log_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupère un log d'audit par son ID."""
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
    context: SaaSContext = Depends(get_context)
):
    """Récupère l'historique d'audit d'une entité."""
    service = get_audit_service(db, context.tenant_id)
    logs = service.get_entity_logs(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        limit=limit
    )
    return logs

@router.get("/logs/user/{user_id}", response_model=list[AuditLogResponseSchema])
async def get_user_logs(
    user_id: int,
    action: AuditAction | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupère l'historique d'audit d'un utilisateur."""
    service = get_audit_service(db, context.tenant_id)
    logs = service.get_user_logs(
        user_id=user_id,
        action=action,
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
    user_id: int | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Liste les sessions actives."""
    service = get_audit_service(db, context.tenant_id)
    sessions = service.get_active_sessions(user_id=user_id)
    return sessions

@router.post("/sessions/{session_id}/terminate")
async def terminate_session(
    session_id: str,
    reason: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Termine une session active."""
    service = get_audit_service(db, context.tenant_id)
    service.terminate_session(
        session_id=session_id,
        terminated_by=context.user_id,
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
    context: SaaSContext = Depends(get_context)
):
    """Crée une nouvelle métrique."""
    service = get_audit_service(db, context.tenant_id)
    metric = service.create_metric(data, created_by=context.user_id)
    return metric

@router.get("/metrics", response_model=list[MetricResponseSchema])
async def list_metrics(
    category: str | None = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Liste les métriques."""
    service = get_audit_service(db, context.tenant_id)
    metrics = service.list_metrics(category=category, is_active=is_active)
    return metrics

@router.post("/metrics/record", response_model=MetricValueResponseSchema)
async def record_metric_value(
    data: MetricValueSchema,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Enregistre une valeur de métrique."""
    service = get_audit_service(db, context.tenant_id)
    value = service.record_metric_value(
        metric_code=data.metric_code,
        value=data.value,
        dimensions=data.dimensions,
        timestamp=data.timestamp
    )
    return value

@router.get("/metrics/{metric_code}/values", response_model=list[MetricValueResponseSchema])
async def get_metric_values(
    metric_code: str,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupère les valeurs d'une métrique."""
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
    context: SaaSContext = Depends(get_context)
):
    """Crée un nouveau benchmark."""
    service = get_audit_service(db, context.tenant_id)
    benchmark = service.create_benchmark(data, created_by=context.user_id)
    return benchmark

@router.get("/benchmarks", response_model=list[BenchmarkResponseSchema])
async def list_benchmarks(
    category: str | None = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Liste les benchmarks."""
    service = get_audit_service(db, context.tenant_id)
    benchmarks = service.list_benchmarks(category=category, is_active=is_active)
    return benchmarks

@router.post("/benchmarks/{benchmark_id}/run", response_model=BenchmarkResultResponseSchema)
async def run_benchmark(
    benchmark_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Exécute un benchmark."""
    service = get_audit_service(db, context.tenant_id)
    result = service.run_benchmark(benchmark_id, executed_by=context.user_id)
    return result

@router.get("/benchmarks/{benchmark_id}/results", response_model=list[BenchmarkResultResponseSchema])
async def get_benchmark_results(
    benchmark_id: int,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupère les résultats d'un benchmark."""
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
    context: SaaSContext = Depends(get_context)
):
    """Crée un contrôle de conformité."""
    service = get_audit_service(db, context.tenant_id)
    check = service.create_compliance_check(data, created_by=context.user_id)
    return check

@router.get("/compliance/checks", response_model=list[ComplianceCheckResponseSchema])
async def list_compliance_checks(
    framework: ComplianceFramework | None = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Liste les contrôles de conformité."""
    service = get_audit_service(db, context.tenant_id)
    checks = service.list_compliance_checks(framework=framework, is_active=is_active)
    return checks

@router.put("/compliance/checks/{check_id}", response_model=ComplianceCheckResponseSchema)
async def update_compliance_check(
    check_id: int,
    data: ComplianceUpdateSchema,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Met à jour un contrôle de conformité."""
    service = get_audit_service(db, context.tenant_id)
    check = service.update_compliance_check(check_id, data, updated_by=context.user_id)
    return check

@router.get("/compliance/summary", response_model=ComplianceSummarySchema)
async def get_compliance_summary(
    framework: ComplianceFramework | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupère le résumé de conformité."""
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
    context: SaaSContext = Depends(get_context)
):
    """Crée une règle de rétention."""
    service = get_audit_service(db, context.tenant_id)
    rule = service.create_retention_rule(data, created_by=context.user_id)
    return rule

@router.get("/retention/rules", response_model=list[RetentionRuleResponseSchema])
async def list_retention_rules(
    category: AuditCategory | None = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Liste les règles de rétention."""
    service = get_audit_service(db, context.tenant_id)
    rules = service.list_retention_rules(category=category, is_active=is_active)
    return rules

@router.post("/retention/apply")
async def apply_retention_rules(
    background_tasks: BackgroundTasks,
    dry_run: bool = Query(False),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Applique les règles de rétention."""
    service = get_audit_service(db, context.tenant_id)

    if dry_run:
        result = service.preview_retention_application()
        return {"status": "preview", "records_to_delete": result}

    background_tasks.add_task(
        service.apply_retention_rules,
        executed_by=context.user_id
    )

    return {"status": "started", "message": "Règles de rétention en cours d'application"}

# ============================================================================
# EXPORTS
# ============================================================================

@router.post("/exports", response_model=ExportResponseSchema)
async def create_export(
    data: ExportCreateSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Crée un export d'audit."""
    service = get_audit_service(db, context.tenant_id)
    export = service.create_export(data, created_by=context.user_id)

    background_tasks.add_task(service.generate_export, export.id)

    return export

@router.get("/exports", response_model=list[ExportResponseSchema])
async def list_exports(
    status: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Liste les exports d'audit."""
    service = get_audit_service(db, context.tenant_id)
    exports = service.list_exports(status=status)
    return exports

@router.get("/exports/{export_id}", response_model=ExportResponseSchema)
async def get_export(
    export_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupère un export par son ID."""
    service = get_audit_service(db, context.tenant_id)
    export = service.get_export(export_id)

    if not export:
        raise HTTPException(status_code=404, detail=f"Export {export_id} non trouvé")

    return export

@router.post("/exports/{export_id}/process", response_model=ExportResponseSchema)
async def process_export(
    export_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Traite (regénère) un export."""
    service = get_audit_service(db, context.tenant_id)

    export = service.get_export(export_id)
    if not export:
        raise HTTPException(status_code=404, detail=f"Export {export_id} non trouvé")

    background_tasks.add_task(service.generate_export, export_id)

    return export

# ============================================================================
# DASHBOARDS
# ============================================================================

@router.post("/dashboards", response_model=DashboardResponseSchema)
async def create_dashboard(
    data: DashboardCreateSchema,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Crée un dashboard personnalisé."""
    service = get_audit_service(db, context.tenant_id)
    dashboard = service.create_dashboard(data, created_by=context.user_id)
    return dashboard

@router.get("/dashboards", response_model=list[DashboardResponseSchema])
async def list_dashboards(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Liste les dashboards."""
    service = get_audit_service(db, context.tenant_id)
    dashboards = service.list_dashboards()
    return dashboards

@router.get("/dashboards/{dashboard_id}/data", response_model=DashboardDataResponseSchema)
async def get_dashboard_data(
    dashboard_id: int,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupère les données d'un dashboard."""
    service = get_audit_service(db, context.tenant_id)
    data = service.get_dashboard_data(
        dashboard_id=dashboard_id,
        from_date=from_date,
        to_date=to_date
    )
    return data

# ============================================================================
# STATISTICS
# ============================================================================

@router.get("/stats", response_model=AuditStatsSchema)
async def get_audit_stats(
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupère les statistiques d'audit."""
    service = get_audit_service(db, context.tenant_id)
    stats = service.get_stats(from_date=from_date, to_date=to_date)
    return stats

@router.get("/dashboard", response_model=AuditDashboardResponseSchema)
async def get_audit_dashboard(
    period: str = Query("7d", pattern="^(24h|7d|30d|90d|365d)$"),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupère le dashboard d'audit principal."""
    service = get_audit_service(db, context.tenant_id)
    dashboard = service.get_audit_dashboard(period=period)
    return dashboard
