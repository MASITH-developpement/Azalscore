"""
AZALS MODULE - QC (Quality Control): Router Unifié
===================================================

Router complet compatible v1, v2 et v3 via app.azals.
Utilise get_context() qui fonctionne avec les deux patterns d'authentification.

Ce router remplace router.py et router_v2.py.

Enregistrement dans main.py:
    from app.modules.qc.router_unified import router as qc_router

    # Double enregistrement pour compatibilité
    app.include_router(qc_router, prefix="/v2")
    app.include_router(qc_router, prefix="/v1", deprecated=True)

Conformité : AZA-NF-006

ENDPOINTS (42 total):
- Rules (5): CRUD + delete
- Modules (5): register + list + get + get by code + update status + scores
- Validations (4): run + list + get + results
- Tests (3): create + list + by module
- Metrics (3): record + history + latest
- Alerts (4): create + list + unresolved + resolve
- Dashboards (5): create + list + get + data + default data
- Templates (4): create + list + get + apply
- Stats (2): global + modules
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db

from app.modules.qc.models import ModuleStatus, QCCheckStatus, QCRuleCategory, QCRuleSeverity, TestType, ValidationPhase
from app.modules.qc.schemas import (
    AlertResolveRequest,
    DashboardDataResponse,
    ModuleRegisterCreate,
    ModuleRegistryResponse,
    ModuleScoreBreakdown,
    ModuleStatusUpdate,
    PaginatedAlertsResponse,
    PaginatedCheckResultsResponse,
    PaginatedModulesResponse,
    PaginatedRulesResponse,
    PaginatedTestRunsResponse,
    PaginatedValidationsResponse,
    QCAlertCreate,
    QCAlertResponse,
    QCDashboardCreate,
    QCDashboardResponse,
    QCMetricResponse,
    QCRuleCreate,
    QCRuleResponse,
    QCRuleUpdate,
    QCStatsResponse,
    QCTemplateCreate,
    QCTemplateResponse,
    TestRunCreate,
    TestRunResponse,
    ValidationResponse,
    ValidationRunRequest,
)
from app.modules.qc.service import QCService

router = APIRouter(prefix="/qc", tags=["Quality Control - Contrôle Qualité"])

# ============================================================================
# FACTORY
# ============================================================================

def get_qc_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
) -> QCService:
    """Factory pour obtenir une instance du service QC."""
    return QCService(db, context.tenant_id, str(context.user_id))

# ============================================================================
# RÈGLES QC
# ============================================================================

@router.post("/rules", response_model=QCRuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(
    data: QCRuleCreate,
    service: QCService = Depends(get_qc_service),
    context: SaaSContext = Depends(get_context)
):
    """Crée une nouvelle règle QC."""
    rule = service.create_rule(
        code=data.code,
        name=data.name,
        category=data.category,
        check_type=data.check_type,
        description=data.description,
        severity=data.severity,
        applies_to_modules=data.applies_to_modules,
        applies_to_phases=data.applies_to_phases,
        check_config=data.check_config,
        threshold_value=data.threshold_value,
        threshold_operator=data.threshold_operator,
        created_by=int(str(context.user_id).replace('-', '')[:8], 16) % 2147483647
    )
    return rule

@router.get("/rules", response_model=PaginatedRulesResponse)
def list_rules(
    category: QCRuleCategory | None = None,
    severity: QCRuleSeverity | None = None,
    is_active: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: QCService = Depends(get_qc_service)
):
    """Liste les règles QC avec filtres."""
    rules, total = service.list_rules(
        category=category,
        severity=severity,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    return PaginatedRulesResponse(items=rules, total=total, skip=skip, limit=limit)

@router.get("/rules/{rule_id}", response_model=QCRuleResponse)
def get_rule(rule_id: int, service: QCService = Depends(get_qc_service)):
    """Récupère une règle QC par ID."""
    rule = service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule

@router.put("/rules/{rule_id}", response_model=QCRuleResponse)
def update_rule(
    rule_id: int,
    data: QCRuleUpdate,
    service: QCService = Depends(get_qc_service)
):
    """Met à jour une règle QC."""
    rule = service.update_rule(rule_id, **data.model_dump(exclude_unset=True))
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found or is system rule")
    return rule

@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: int, service: QCService = Depends(get_qc_service)):
    """Supprime une règle QC."""
    if not service.delete_rule(rule_id):
        raise HTTPException(status_code=404, detail="Rule not found or is system rule")

# ============================================================================
# MODULES
# ============================================================================

@router.post("/modules", response_model=ModuleRegistryResponse, status_code=status.HTTP_201_CREATED)
def register_module(
    data: ModuleRegisterCreate,
    service: QCService = Depends(get_qc_service)
):
    """Enregistre un nouveau module dans le registre QC."""
    module = service.register_module(
        module_code=data.module_code,
        module_name=data.module_name,
        module_type=data.module_type,
        module_version=data.module_version,
        description=data.description,
        dependencies=data.dependencies
    )
    return module

@router.get("/modules", response_model=PaginatedModulesResponse)
def list_modules(
    module_status: ModuleStatus | None = Query(None, alias="status"),
    has_tests: bool | None = None,
    has_validation: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: QCService = Depends(get_qc_service)
):
    """Liste les modules enregistrés."""
    modules, total = service.list_modules(
        module_type=None,
        status=module_status,
        skip=skip,
        limit=limit
    )
    return PaginatedModulesResponse(items=modules, total=total, skip=skip, limit=limit)

@router.get("/modules/{module_id}", response_model=ModuleRegistryResponse)
def get_module(module_id: int, service: QCService = Depends(get_qc_service)):
    """Récupère un module par ID."""
    module = service.get_module(module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module

@router.get("/modules/code/{module_code}", response_model=ModuleRegistryResponse)
def get_module_by_code(module_code: str, service: QCService = Depends(get_qc_service)):
    """Récupère un module par code."""
    module = service.get_module_by_code(module_code)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module

@router.put("/modules/{module_id}/status", response_model=ModuleRegistryResponse)
def update_module_status(
    module_id: int,
    data: ModuleStatusUpdate,
    service: QCService = Depends(get_qc_service),
    context: SaaSContext = Depends(get_context)
):
    """Met à jour le statut d'un module."""
    module = service.update_module_status(
        module_id=module_id,
        status=data.status,
        validated_by=int(str(context.user_id).replace('-', '')[:8], 16) % 2147483647
    )
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module

@router.get("/modules/{module_id}/scores", response_model=ModuleScoreBreakdown)
def get_module_scores(module_id: int, service: QCService = Depends(get_qc_service)):
    """Récupère le détail des scores d'un module."""
    module = service.get_module(module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    return ModuleScoreBreakdown(
        module_code=module.module_code,
        module_name=module.module_name,
        overall_score=module.overall_score or 0,
        architecture_score=module.architecture_score or 0,
        security_score=module.security_score or 0,
        performance_score=module.performance_score or 0,
        code_quality_score=module.code_quality_score or 0,
        testing_score=module.testing_score or 0,
        documentation_score=module.documentation_score or 0,
        status=module.status
    )

# ============================================================================
# VALIDATIONS
# ============================================================================

@router.post("/validations/run", response_model=ValidationResponse)
def run_validation(
    data: ValidationRunRequest,
    service: QCService = Depends(get_qc_service),
    context: SaaSContext = Depends(get_context)
):
    """Exécute une validation QC complète pour un module."""
    try:
        validation = service.run_validation(
            module_id=data.module_id,
            phase=data.phase,
            started_by=int(str(context.user_id).replace('-', '')[:8], 16) % 2147483647
        )
        return validation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/validations", response_model=PaginatedValidationsResponse)
def list_validations(
    module_id: int | None = None,
    phase: ValidationPhase | None = None,
    validation_status: QCCheckStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: QCService = Depends(get_qc_service)
):
    """Liste les validations QC."""
    validations, total = service.list_validations(
        module_id=module_id,
        status=validation_status,
        phase=phase,
        skip=skip,
        limit=limit
    )
    return PaginatedValidationsResponse(items=validations, total=total, skip=skip, limit=limit)

@router.get("/validations/{validation_id}", response_model=ValidationResponse)
def get_validation(validation_id: int, service: QCService = Depends(get_qc_service)):
    """Récupère une validation par ID."""
    validation = service.get_validation(validation_id)
    if not validation:
        raise HTTPException(status_code=404, detail="Validation not found")
    return validation

@router.get("/validations/{validation_id}/results", response_model=PaginatedCheckResultsResponse)
def get_validation_results(
    validation_id: int,
    result_status: QCCheckStatus | None = Query(None, alias="status"),
    category: QCRuleCategory | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: QCService = Depends(get_qc_service)
):
    """Récupère les résultats de checks d'une validation."""
    results, total = service.get_check_results(
        validation_id=validation_id,
        status=result_status,
        category=category,
        skip=skip,
        limit=limit
    )
    return PaginatedCheckResultsResponse(items=results, total=total, skip=skip, limit=limit)

# ============================================================================
# TESTS
# ============================================================================

@router.post("/tests", response_model=TestRunResponse, status_code=status.HTTP_201_CREATED)
def create_test_run(
    data: TestRunCreate,
    service: QCService = Depends(get_qc_service),
    context: SaaSContext = Depends(get_context)
):
    """Enregistre une exécution de tests."""
    run = service.record_test_run(
        module_id=data.module_id,
        test_type=data.test_type,
        total_tests=data.total_tests,
        passed_tests=data.passed_tests,
        failed_tests=data.failed_tests,
        skipped_tests=data.skipped_tests,
        error_tests=data.error_tests,
        coverage_percent=data.coverage_percent,
        test_suite=data.test_suite,
        duration_seconds=data.duration_seconds,
        failed_test_details=data.failed_test_details,
        output_log=data.output_log,
        triggered_by=data.triggered_by,
        triggered_user=int(str(context.user_id).replace('-', '')[:8], 16) % 2147483647,
        validation_id=data.validation_id
    )
    return run

@router.get("/tests", response_model=PaginatedTestRunsResponse)
def list_test_runs(
    module_id: int | None = None,
    test_type: TestType | None = None,
    passed: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: QCService = Depends(get_qc_service)
):
    """Liste les exécutions de tests."""
    runs, total = service.get_test_runs(
        module_id=module_id,
        test_type=test_type,
        skip=skip,
        limit=limit
    )
    return PaginatedTestRunsResponse(items=runs, total=total, skip=skip, limit=limit)

@router.get("/tests/module/{module_id}", response_model=list[TestRunResponse])
def get_module_tests(
    module_id: int,
    limit: int = Query(20, ge=1, le=100),
    service: QCService = Depends(get_qc_service)
):
    """Récupère les derniers tests d'un module."""
    runs, _ = service.get_test_runs(module_id=module_id, limit=limit)
    return runs

# ============================================================================
# MÉTRIQUES
# ============================================================================

@router.post("/metrics/record", response_model=QCMetricResponse)
def record_metric(
    module_id: int | None = None,
    service: QCService = Depends(get_qc_service)
):
    """Enregistre les métriques QC actuelles."""
    metric = service.record_metrics(module_id=module_id)
    return metric

@router.get("/metrics/history", response_model=list[QCMetricResponse])
def get_metrics_history(
    module_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = Query(30, ge=1, le=365),
    service: QCService = Depends(get_qc_service)
):
    """Récupère l'historique des métriques QC."""
    metrics = service.get_metrics_history(
        module_id=module_id,
        date_from=start_date,
        date_to=end_date,
        limit=limit
    )
    return metrics

@router.get("/metrics/latest", response_model=Optional[QCMetricResponse])
def get_latest_metrics(
    module_id: int | None = None,
    service: QCService = Depends(get_qc_service)
):
    """Récupère les dernières métriques QC."""
    metrics = service.get_metrics_history(module_id=module_id, limit=1)
    return metrics[0] if metrics else None

# ============================================================================
# ALERTES
# ============================================================================

@router.post("/alerts", response_model=QCAlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    data: QCAlertCreate,
    service: QCService = Depends(get_qc_service)
):
    """Crée une alerte QC."""
    alert = service.create_alert(
        alert_type=data.alert_type,
        title=data.title,
        message=data.message,
        severity=data.severity,
        module_id=data.module_id,
        validation_id=data.validation_id,
        check_result_id=data.check_result_id,
        details=data.details
    )
    return alert

@router.get("/alerts", response_model=PaginatedAlertsResponse)
def list_alerts(
    severity: QCRuleSeverity | None = None,
    is_resolved: bool | None = None,
    module_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: QCService = Depends(get_qc_service)
):
    """Liste les alertes QC."""
    alerts, total = service.list_alerts(
        is_resolved=is_resolved,
        severity=severity,
        module_id=module_id,
        skip=skip,
        limit=limit
    )
    return PaginatedAlertsResponse(items=alerts, total=total, skip=skip, limit=limit)

@router.get("/alerts/unresolved", response_model=list[QCAlertResponse])
def get_unresolved_alerts(
    limit: int = Query(20, ge=1, le=100),
    service: QCService = Depends(get_qc_service)
):
    """Récupère les alertes non résolues."""
    alerts, _ = service.list_alerts(is_resolved=False, limit=limit)
    return alerts

@router.post("/alerts/{alert_id}/resolve", response_model=QCAlertResponse)
def resolve_alert(
    alert_id: int,
    data: AlertResolveRequest,
    service: QCService = Depends(get_qc_service),
    context: SaaSContext = Depends(get_context)
):
    """Résout une alerte QC."""
    alert = service.resolve_alert(
        alert_id=alert_id,
        resolved_by=int(str(context.user_id).replace('-', '')[:8], 16) % 2147483647,
        resolution_notes=data.resolution_notes
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

# ============================================================================
# DASHBOARDS
# ============================================================================

@router.post("/dashboards", response_model=QCDashboardResponse, status_code=status.HTTP_201_CREATED)
def create_dashboard(
    data: QCDashboardCreate,
    service: QCService = Depends(get_qc_service),
    context: SaaSContext = Depends(get_context)
):
    """Crée un dashboard QC personnalisé."""
    dashboard = service.create_dashboard(
        name=data.name,
        owner_id=int(str(context.user_id).replace('-', '')[:8], 16) % 2147483647,
        description=data.description,
        layout=data.layout,
        widgets=data.widgets,
        filters=data.filters,
        is_default=data.is_default,
        is_public=data.is_public
    )
    return dashboard

@router.get("/dashboards", response_model=list[QCDashboardResponse])
def list_dashboards(
    service: QCService = Depends(get_qc_service),
    context: SaaSContext = Depends(get_context)
):
    """Liste les dashboards accessibles."""
    return service.list_dashboards(
        owner_id=int(str(context.user_id).replace('-', '')[:8], 16) % 2147483647
    )

@router.get("/dashboards/{dashboard_id}", response_model=QCDashboardResponse)
def get_dashboard(dashboard_id: int, service: QCService = Depends(get_qc_service)):
    """Récupère un dashboard."""
    dashboard = service.get_dashboard(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard

@router.get("/dashboards/{dashboard_id}/data", response_model=DashboardDataResponse)
def get_dashboard_data(dashboard_id: int, service: QCService = Depends(get_qc_service)):
    """Récupère les données d'un dashboard QC."""
    dashboard = service.get_dashboard(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    data = service.get_dashboard_data(dashboard_id)
    return DashboardDataResponse(**data)

@router.get("/dashboards/default/data", response_model=DashboardDataResponse)
def get_default_dashboard_data(service: QCService = Depends(get_qc_service)):
    """Récupère les données du dashboard QC par défaut."""
    data = service.get_dashboard_data()
    return DashboardDataResponse(**data)

# ============================================================================
# TEMPLATES
# ============================================================================

@router.post("/templates", response_model=QCTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    data: QCTemplateCreate,
    service: QCService = Depends(get_qc_service),
    context: SaaSContext = Depends(get_context)
):
    """Crée un template de règles QC."""
    template = service.create_template(
        code=data.code,
        name=data.name,
        rules=data.rules,
        description=data.description,
        category=data.category,
        created_by=int(str(context.user_id).replace('-', '')[:8], 16) % 2147483647
    )
    return template

@router.get("/templates", response_model=list[QCTemplateResponse])
def list_templates(
    category: str | None = None,
    service: QCService = Depends(get_qc_service)
):
    """Liste les templates de règles QC."""
    return service.list_templates(category=category)

@router.get("/templates/{template_id}", response_model=QCTemplateResponse)
def get_template(template_id: int, service: QCService = Depends(get_qc_service)):
    """Récupère un template."""
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.post("/templates/{template_id}/apply", response_model=list[QCRuleResponse])
def apply_template(
    template_id: int,
    service: QCService = Depends(get_qc_service),
    context: SaaSContext = Depends(get_context)
):
    """Applique un template pour créer des règles."""
    rules = service.apply_template(
        template_id,
        created_by=int(str(context.user_id).replace('-', '')[:8], 16) % 2147483647
    )
    if not rules:
        raise HTTPException(status_code=404, detail="Template not found or no rules created")
    return rules

# ============================================================================
# STATISTIQUES
# ============================================================================

@router.get("/stats", response_model=QCStatsResponse)
def get_stats(service: QCService = Depends(get_qc_service)):
    """Récupère les statistiques QC globales."""
    modules, _ = service.list_modules()
    rules, _ = service.list_rules()
    active_rules, _ = service.list_rules(is_active=True)
    alerts, alert_count = service.list_alerts(is_resolved=False)

    # Tests aujourd'hui
    test_runs, _ = service.get_test_runs(limit=100)
    today = datetime.utcnow().date()
    tests_today = [r for r in test_runs if r.started_at.date() == today]
    tests_passed_today = sum(r.passed_tests for r in tests_today)
    tests_run_today = sum(r.total_tests for r in tests_today)

    # Scores
    overall_scores = [m.overall_score for m in modules if m.overall_score]
    avg_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0

    return QCStatsResponse(
        total_modules=len(modules),
        validated_modules=len([m for m in modules if m.status == ModuleStatus.QC_PASSED]),
        production_modules=len([m for m in modules if m.status == ModuleStatus.PRODUCTION]),
        failed_modules=len([m for m in modules if m.status == ModuleStatus.QC_FAILED]),
        average_score=round(avg_score, 2),
        total_rules=len(rules),
        active_rules=len(active_rules),
        unresolved_alerts=alert_count,
        tests_run_today=tests_run_today,
        tests_passed_today=tests_passed_today
    )

@router.get("/stats/modules", response_model=list[ModuleScoreBreakdown])
def get_module_stats(service: QCService = Depends(get_qc_service)):
    """Récupère les scores de tous les modules."""
    modules, _ = service.list_modules()

    return [
        ModuleScoreBreakdown(
            module_code=m.module_code,
            module_name=m.module_name,
            overall_score=m.overall_score or 0,
            architecture_score=m.architecture_score or 0,
            security_score=m.security_score or 0,
            performance_score=m.performance_score or 0,
            code_quality_score=m.code_quality_score or 0,
            testing_score=m.testing_score or 0,
            documentation_score=m.documentation_score or 0,
            status=m.status
        )
        for m in modules
    ]
