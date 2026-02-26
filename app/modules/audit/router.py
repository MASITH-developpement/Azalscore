"""
AZALS MODULE T3 - Router Audit & Benchmark
===========================================

Endpoints API pour l'audit et les benchmarks.
"""
from __future__ import annotations


from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.models import User

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


def get_service(request: Request, db: Session = Depends(get_db)):
    """Factory pour le service d'audit."""
    tenant_id = request.state.tenant_id
    return get_audit_service(db, tenant_id)


# ============================================================================
# AUDIT LOGS
# ============================================================================

@router.get("/logs", response_model=AuditLogListResponseSchema)
async def search_audit_logs(
    request: Request,
    db: Session = Depends(get_db),
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
    current_user: User = Depends(get_current_user)
):
    """
    Recherche dans les logs d'audit.
    Nécessite: audit.logs.read
    """
    service = get_service(request, db)
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
        logs=[AuditLogResponseSchema.from_orm_custom(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/logs/{log_id}", response_model=AuditLogResponseSchema)
async def get_audit_log(
    log_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère un log d'audit par ID.
    Nécessite: audit.logs.read
    """
    service = get_service(request, db)
    log = service.get_log(log_id)

    if not log:
        raise HTTPException(status_code=404, detail="Log non trouvé")

    return AuditLogResponseSchema.from_orm_custom(log)


@router.get("/logs/entity/{entity_type}/{entity_id}", response_model=list[AuditLogResponseSchema])
async def get_entity_history(
    entity_type: str,
    entity_id: str,
    request: Request,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère l'historique d'une entité.
    Nécessite: audit.logs.read
    """
    service = get_service(request, db)
    logs = service.get_entity_history(entity_type, entity_id, limit=limit)
    return [AuditLogResponseSchema.from_orm_custom(log) for log in logs]


@router.get("/logs/user/{user_id}", response_model=list[AuditLogResponseSchema])
async def get_user_activity(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère l'activité d'un utilisateur.
    Nécessite: audit.logs.read
    """
    service = get_service(request, db)
    logs = service.get_user_activity(user_id, from_date, to_date, limit)
    return [AuditLogResponseSchema.from_orm_custom(log) for log in logs]


# ============================================================================
# SESSIONS
# ============================================================================

@router.get("/sessions", response_model=list[AuditSessionResponseSchema])
async def list_active_sessions(
    request: Request,
    db: Session = Depends(get_db),
    user_id: int | None = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les sessions actives.
    Nécessite: audit.sessions.read
    """
    service = get_service(request, db)
    sessions = service.get_active_sessions(user_id)
    return sessions


@router.post("/sessions/{session_id}/terminate")
async def terminate_session(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db),
    reason: str | None = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    Termine une session.
    Nécessite: audit.sessions.terminate
    """
    service = get_service(request, db)
    session = service.end_session(session_id, reason)

    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")

    return {"message": "Session terminée", "session_id": session_id}


# ============================================================================
# MÉTRIQUES
# ============================================================================

@router.post("/metrics", response_model=MetricResponseSchema)
async def create_metric(
    data: MetricCreateSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée une définition de métrique.
    Nécessite: audit.metrics.create
    """
    service = get_service(request, db)

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
    request: Request,
    db: Session = Depends(get_db),
    module: str | None = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les métriques définies.
    Nécessite: audit.metrics.read
    """
    service = get_service(request, db)
    return service.list_metrics(module)


@router.post("/metrics/record", response_model=MetricValueResponseSchema)
async def record_metric_value(
    data: MetricValueSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enregistre une valeur de métrique.
    Nécessite: audit.metrics.record
    """
    service = get_service(request, db)

    value = service.record_metric(
        metric_code=data.metric_code,
        value=data.value,
        dimensions=data.dimensions
    )

    if not value:
        raise HTTPException(status_code=404, detail="Métrique non trouvée")

    service.db.commit()
    return MetricValueResponseSchema.from_orm_custom(value)


@router.get("/metrics/{metric_code}/values", response_model=list[MetricValueResponseSchema])
async def get_metric_values(
    metric_code: str,
    request: Request,
    db: Session = Depends(get_db),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    limit: int = Query(1000, ge=1, le=10000),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les valeurs d'une métrique.
    Nécessite: audit.metrics.read
    """
    service = get_service(request, db)
    values = service.get_metric_values(metric_code, from_date, to_date, limit)
    return [MetricValueResponseSchema.from_orm_custom(v) for v in values]


# ============================================================================
# BENCHMARKS
# ============================================================================

@router.post("/benchmarks", response_model=BenchmarkResponseSchema)
async def create_benchmark(
    data: BenchmarkCreateSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée un benchmark.
    Nécessite: audit.benchmarks.create
    """
    service = get_service(request, db)

    benchmark = service.create_benchmark(
        code=data.code,
        name=data.name,
        benchmark_type=data.benchmark_type,
        description=data.description,
        module=data.module,
        config=data.config,
        baseline=data.baseline,
        created_by=current_user.id
    )
    return BenchmarkResponseSchema.from_orm_custom(benchmark)


@router.get("/benchmarks", response_model=list[BenchmarkResponseSchema])
async def list_benchmarks(
    request: Request,
    db: Session = Depends(get_db),
    benchmark_type: str | None = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les benchmarks.
    Nécessite: audit.benchmarks.read
    """
    service = get_service(request, db)
    benchmarks = service.list_benchmarks(benchmark_type)
    return [BenchmarkResponseSchema.from_orm_custom(b) for b in benchmarks]


@router.post("/benchmarks/{benchmark_id}/run", response_model=BenchmarkResultResponseSchema)
async def run_benchmark(
    benchmark_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exécute un benchmark.
    Nécessite: audit.benchmarks.execute
    """
    service = get_service(request, db)

    try:
        result = service.run_benchmark(
            benchmark_id=benchmark_id,
            executed_by=current_user.id
        )
        return BenchmarkResultResponseSchema.from_orm_custom(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/benchmarks/{benchmark_id}/results", response_model=list[BenchmarkResultResponseSchema])
async def get_benchmark_results(
    benchmark_id: int,
    request: Request,
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les résultats d'un benchmark.
    Nécessite: audit.benchmarks.read
    """
    service = get_service(request, db)
    results = service.get_benchmark_results(benchmark_id, limit)
    return [BenchmarkResultResponseSchema.from_orm_custom(r) for r in results]


# ============================================================================
# CONFORMITÉ
# ============================================================================

@router.post("/compliance/checks", response_model=ComplianceCheckResponseSchema)
async def create_compliance_check(
    data: ComplianceCheckCreateSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée un contrôle de conformité.
    Nécessite: audit.compliance.create
    """
    service = get_service(request, db)

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
    return ComplianceCheckResponseSchema.from_orm_custom(check)


@router.get("/compliance/checks", response_model=list[ComplianceCheckResponseSchema])
async def list_compliance_checks(
    request: Request,
    db: Session = Depends(get_db),
    framework: ComplianceFramework | None = Query(None),
    status: str | None = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les contrôles de conformité.
    Nécessite: audit.compliance.read
    """
    from .models import ComplianceCheck
    tenant_id = request.state.tenant_id

    query = db.query(ComplianceCheck).filter(
        ComplianceCheck.tenant_id == tenant_id,
        ComplianceCheck.is_active
    )

    if framework:
        query = query.filter(ComplianceCheck.framework == framework)
    if status:
        query = query.filter(ComplianceCheck.status == status)

    checks = query.all()
    return [ComplianceCheckResponseSchema.from_orm_custom(c) for c in checks]


@router.put("/compliance/checks/{check_id}", response_model=ComplianceCheckResponseSchema)
async def update_compliance_check(
    check_id: int,
    data: ComplianceUpdateSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Met à jour le statut d'un contrôle.
    Nécessite: audit.compliance.update
    """
    service = get_service(request, db)

    check = service.update_compliance_status(
        check_id=check_id,
        status=data.status,
        actual_result=data.actual_result,
        evidence=data.evidence,
        checked_by=current_user.id
    )

    if not check:
        raise HTTPException(status_code=404, detail="Contrôle non trouvé")

    return ComplianceCheckResponseSchema.from_orm_custom(check)


@router.get("/compliance/summary", response_model=ComplianceSummarySchema)
async def get_compliance_summary(
    request: Request,
    db: Session = Depends(get_db),
    framework: ComplianceFramework | None = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère un résumé de conformité.
    Nécessite: audit.compliance.read
    """
    service = get_service(request, db)
    summary = service.get_compliance_summary(framework)
    return summary


# ============================================================================
# RÉTENTION
# ============================================================================

@router.post("/retention/rules", response_model=RetentionRuleResponseSchema)
async def create_retention_rule(
    data: RetentionRuleCreateSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée une règle de rétention.
    Nécessite: audit.retention.create
    """
    service = get_service(request, db)

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
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les règles de rétention.
    Nécessite: audit.retention.read
    """
    from .models import DataRetentionRule
    tenant_id = request.state.tenant_id

    rules = db.query(DataRetentionRule).filter(
        DataRetentionRule.tenant_id == tenant_id
    ).all()

    return rules


@router.post("/retention/apply")
async def apply_retention_rules(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Applique les règles de rétention.
    Nécessite: audit.retention.execute
    """
    service = get_service(request, db)
    results = service.apply_retention_rules()
    return {"message": "Règles de rétention appliquées", "results": results}


# ============================================================================
# EXPORTS
# ============================================================================

@router.post("/exports", response_model=ExportResponseSchema)
async def create_export(
    data: ExportCreateSchema,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée une demande d'export.
    Nécessite: audit.exports.create
    """
    service = get_service(request, db)

    export = service.create_export(
        export_type=data.export_type,
        format=data.format,
        requested_by=current_user.id,
        date_from=data.date_from,
        date_to=data.date_to,
        filters=data.filters
    )

    # Lancer le traitement en arrière-plan
    # background_tasks.add_task(service.process_export, export.id)

    return ExportResponseSchema.from_orm_custom(export)


@router.get("/exports", response_model=list[ExportResponseSchema])
async def list_exports(
    request: Request,
    db: Session = Depends(get_db),
    status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les exports.
    Nécessite: audit.exports.read
    """
    from .models import AuditExport
    tenant_id = request.state.tenant_id

    query = db.query(AuditExport).filter(
        AuditExport.tenant_id == tenant_id
    )

    if status:
        query = query.filter(AuditExport.status == status)

    exports = query.order_by(AuditExport.requested_at.desc()).limit(limit).all()
    return [ExportResponseSchema.from_orm_custom(e) for e in exports]


@router.get("/exports/{export_id}", response_model=ExportResponseSchema)
async def get_export(
    export_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère un export par ID.
    Nécessite: audit.exports.read
    """
    from .models import AuditExport
    tenant_id = request.state.tenant_id

    export = db.query(AuditExport).filter(
        AuditExport.id == export_id,
        AuditExport.tenant_id == tenant_id
    ).first()

    if not export:
        raise HTTPException(status_code=404, detail="Export non trouvé")

    return ExportResponseSchema.from_orm_custom(export)


@router.post("/exports/{export_id}/process", response_model=ExportResponseSchema)
async def process_export(
    export_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Traite un export.
    Nécessite: audit.exports.process
    """
    service = get_service(request, db)

    try:
        export = service.process_export(export_id)
        return ExportResponseSchema.from_orm_custom(export)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# DASHBOARDS
# ============================================================================

@router.post("/dashboards", response_model=DashboardResponseSchema)
async def create_dashboard(
    data: DashboardCreateSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée un tableau de bord.
    Nécessite: audit.dashboards.create
    """
    service = get_service(request, db)

    dashboard = service.create_dashboard(
        code=data.code,
        name=data.name,
        widgets=[w.model_dump() for w in data.widgets],
        owner_id=current_user.id,
        description=data.description,
        layout=data.layout,
        refresh_interval=data.refresh_interval
    )
    return DashboardResponseSchema.from_orm_custom(dashboard)


@router.get("/dashboards", response_model=list[DashboardResponseSchema])
async def list_dashboards(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les tableaux de bord.
    Nécessite: audit.dashboards.read
    """
    from .models import AuditDashboard
    tenant_id = request.state.tenant_id
    user_id = current_user.id

    dashboards = db.query(AuditDashboard).filter(
        AuditDashboard.tenant_id == tenant_id,
        AuditDashboard.is_active
    ).filter(
        (AuditDashboard.owner_id == user_id) | (AuditDashboard.is_public)
    ).all()

    return [DashboardResponseSchema.from_orm_custom(d) for d in dashboards]


@router.get("/dashboards/{dashboard_id}/data", response_model=DashboardDataResponseSchema)
async def get_dashboard_data(
    dashboard_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les données d'un tableau de bord.
    Nécessite: audit.dashboards.read
    """
    service = get_service(request, db)
    data = service.get_dashboard_data(dashboard_id)

    if not data:
        raise HTTPException(status_code=404, detail="Dashboard non trouvé")

    return data


# ============================================================================
# STATISTIQUES GLOBALES
# ============================================================================

@router.get("/stats", response_model=AuditStatsSchema)
async def get_audit_stats(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les statistiques d'audit.
    Nécessite: audit.logs.read
    """
    service = get_service(request, db)
    return service._get_audit_stats()


@router.get("/dashboard", response_model=AuditDashboardResponseSchema)
async def get_audit_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère le dashboard d'audit complet.
    Nécessite: audit.logs.read
    """
    service = get_service(request, db)

    stats = service._get_audit_stats()

    logs, _ = service.search_logs(limit=10)
    recent_logs = [AuditLogResponseSchema.from_orm_custom(log) for log in logs]

    sessions = service.get_active_sessions()
    active_sessions = [AuditSessionResponseSchema.model_validate(s) for s in sessions]

    compliance = service.get_compliance_summary()

    benchmarks = service.list_benchmarks()
    latest_results = []
    for b in benchmarks[:5]:
        results = service.get_benchmark_results(b.id, limit=1)
        if results:
            latest_results.append(BenchmarkResultResponseSchema.from_orm_custom(results[0]))

    return AuditDashboardResponseSchema(
        stats=stats,
        recent_logs=recent_logs,
        active_sessions=active_sessions,
        compliance_summary=compliance,
        latest_benchmarks=latest_results
    )
