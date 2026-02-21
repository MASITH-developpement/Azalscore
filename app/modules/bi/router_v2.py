"""
AZALS - Module M10: BI & Reporting
Router FastAPI v2 pour Business Intelligence - CORE SaaS v2
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext

from .models import AlertSeverity, AlertStatus, DashboardType, DataSourceType, KPICategory, ReportType
from .schemas import (
    AlertAcknowledge,
    AlertList,
    AlertResolve,
    AlertResponse,
    AlertRuleCreate,
    AlertRuleResponse,
    AlertRuleUpdate,
    AlertSnooze,
    AlertSummary,
    BIOverview,
    BookmarkCreate,
    BookmarkResponse,
    DashboardCreate,
    DashboardList,
    DashboardResponse,
    DashboardStats,
    DashboardUpdate,
    DataQueryCreate,
    DataQueryResponse,
    DataSourceCreate,
    DataSourceResponse,
    DataSourceUpdate,
    ExportRequest,
    ExportResponse,
    KPICreate,
    KPIList,
    KPIResponse,
    KPITargetCreate,
    KPITargetResponse,
    KPIUpdate,
    KPIValueCreate,
    KPIValueResponse,
    ReportCreate,
    ReportExecuteRequest,
    ReportExecutionResponse,
    ReportList,
    ReportResponse,
    ReportScheduleCreate,
    ReportScheduleResponse,
    ReportUpdate,
    WidgetCreate,
    WidgetResponse,
    WidgetUpdate,
)
from .service import get_bi_service

router = APIRouter(prefix="/v2/bi", tags=["BI v2 - CORE SaaS"])


# ============================================================================
# DASHBOARDS
# ============================================================================

@router.post("/dashboards", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
def create_dashboard(
    data: DashboardCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Créer un nouveau tableau de bord."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.create_dashboard(data)


@router.get("/dashboards", response_model=list[DashboardList])
def list_dashboards(
    dashboard_type: DashboardType | None = None,
    owner_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Lister les tableaux de bord."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    dashboards, _ = service.list_dashboards(
        dashboard_type=dashboard_type,
        owner_only=owner_only,
        skip=skip,
        limit=limit
    )

    return [
        DashboardList(
            id=d.id,
            code=d.code,
            name=d.name,
            description=d.description,
            dashboard_type=d.dashboard_type,
            owner_id=d.owner_id,
            is_shared=d.is_shared,
            is_public=d.is_public,
            view_count=d.view_count,
            widget_count=len(d.widgets),
            created_at=d.created_at
        )
        for d in dashboards
    ]


@router.get("/dashboards/{dashboard_id}", response_model=DashboardResponse)
def get_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer un tableau de bord."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    dashboard = service.get_dashboard(dashboard_id)
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tableau de bord non trouvé"
        )
    return dashboard


@router.put("/dashboards/{dashboard_id}", response_model=DashboardResponse)
def update_dashboard(
    dashboard_id: int,
    data: DashboardUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Mettre à jour un tableau de bord."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.update_dashboard(dashboard_id, data)


@router.delete("/dashboards/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Supprimer un tableau de bord."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    if not service.delete_dashboard(dashboard_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tableau de bord non trouvé"
        )


@router.post("/dashboards/{dashboard_id}/duplicate", response_model=DashboardResponse)
def duplicate_dashboard(
    dashboard_id: int,
    new_code: str = Query(..., min_length=2, max_length=50),
    new_name: str = Query(..., min_length=1, max_length=200),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Dupliquer un tableau de bord."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.duplicate_dashboard(dashboard_id, new_code, new_name)


@router.get("/dashboards/{dashboard_id}/stats", response_model=DashboardStats)
def get_dashboard_stats(
    dashboard_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Statistiques d'un tableau de bord."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    stats = service.get_dashboard_stats(dashboard_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tableau de bord non trouvé"
        )
    return stats


# ============================================================================
# WIDGETS
# ============================================================================

@router.post("/dashboards/{dashboard_id}/widgets", response_model=WidgetResponse, status_code=status.HTTP_201_CREATED)
def add_widget(
    dashboard_id: int,
    data: WidgetCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Ajouter un widget à un tableau de bord."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.add_widget(dashboard_id, data)


@router.put("/widgets/{widget_id}", response_model=WidgetResponse)
def update_widget(
    widget_id: int,
    data: WidgetUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Mettre à jour un widget."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.update_widget(widget_id, data)


@router.delete("/widgets/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_widget(
    widget_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Supprimer un widget."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    if not service.delete_widget(widget_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget non trouvé"
        )


@router.put("/dashboards/{dashboard_id}/widgets/positions")
def update_widget_positions(
    dashboard_id: int,
    positions: list[dict],
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Mettre à jour les positions des widgets."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    service.update_widget_positions(dashboard_id, positions)
    return {"success": True}


# ============================================================================
# REPORTS
# ============================================================================

@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    data: ReportCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Créer un nouveau rapport."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.create_report(data)


@router.get("/reports", response_model=list[ReportList])
def list_reports(
    report_type: ReportType | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Lister les rapports."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    reports, _ = service.list_reports(
        report_type=report_type,
        skip=skip,
        limit=limit
    )

    return [
        ReportList(
            id=r.id,
            code=r.code,
            name=r.name,
            description=r.description,
            report_type=r.report_type,
            owner_id=r.owner_id,
            is_public=r.is_public,
            available_formats=r.available_formats,
            schedule_count=len(r.schedules),
            created_at=r.created_at
        )
        for r in reports
    ]


@router.get("/reports/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer un rapport."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    report = service.get_report(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rapport non trouvé"
        )
    return report


@router.put("/reports/{report_id}", response_model=ReportResponse)
def update_report(
    report_id: int,
    data: ReportUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Mettre à jour un rapport."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.update_report(report_id, data)


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Supprimer un rapport."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    if not service.delete_report(report_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rapport non trouvé"
        )


@router.post("/reports/{report_id}/execute", response_model=ReportExecutionResponse)
def execute_report(
    report_id: int,
    request: ReportExecuteRequest,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Exécuter un rapport."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.execute_report(report_id, request)


@router.get("/reports/{report_id}/executions", response_model=list[ReportExecutionResponse])
def get_report_executions(
    report_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer les exécutions d'un rapport."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.get_report_executions(report_id, skip, limit)


# ============================================================================
# REPORT SCHEDULES
# ============================================================================

@router.post("/reports/{report_id}/schedules", response_model=ReportScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    report_id: int,
    data: ReportScheduleCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Créer une planification de rapport."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.create_schedule(report_id, data)


# ============================================================================
# KPIs
# ============================================================================

@router.post("/kpis", response_model=KPIResponse, status_code=status.HTTP_201_CREATED)
def create_kpi(
    data: KPICreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Créer un nouveau KPI."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.create_kpi(data)


@router.get("/kpis", response_model=list[KPIList])
def list_kpis(
    category: KPICategory | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Lister les KPIs."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    kpis, _ = service.list_kpis(
        category=category,
        skip=skip,
        limit=limit
    )

    result = []
    for kpi in kpis:
        current = service.get_kpi_current_value(kpi.id)
        result.append(KPIList(
            id=kpi.id,
            code=kpi.code,
            name=kpi.name,
            category=kpi.category,
            unit=kpi.unit,
            current_value=current.value if current else None,
            change_percentage=current.change_percentage if current else None,
            trend=current.trend if current else None,
            is_active=kpi.is_active
        ))

    return result


@router.get("/kpis/{kpi_id}", response_model=KPIResponse)
def get_kpi(
    kpi_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer un KPI."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    kpi = service.get_kpi(kpi_id)
    if not kpi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KPI non trouvé"
        )

    # Enrichir avec la valeur actuelle
    current = service.get_kpi_current_value(kpi_id)
    response = KPIResponse.model_validate(kpi)
    if current:
        response.current_value = current.value
        response.previous_value = current.previous_value
        response.change_percentage = current.change_percentage
        response.trend = current.trend

    return response


@router.put("/kpis/{kpi_id}", response_model=KPIResponse)
def update_kpi(
    kpi_id: int,
    data: KPIUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Mettre à jour un KPI."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.update_kpi(kpi_id, data)


@router.post("/kpis/{kpi_id}/values", response_model=KPIValueResponse, status_code=status.HTTP_201_CREATED)
def record_kpi_value(
    kpi_id: int,
    data: KPIValueCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Enregistrer une valeur de KPI."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.record_kpi_value(kpi_id, data)


@router.get("/kpis/{kpi_id}/values", response_model=list[KPIValueResponse])
def get_kpi_values(
    kpi_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    period_type: str = "daily",
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer les valeurs d'un KPI."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.get_kpi_values(kpi_id, start_date, end_date, period_type, limit)


@router.post("/kpis/{kpi_id}/targets", response_model=KPITargetResponse, status_code=status.HTTP_201_CREATED)
def set_kpi_target(
    kpi_id: int,
    data: KPITargetCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Définir un objectif pour un KPI."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.set_kpi_target(kpi_id, data)


# ============================================================================
# ALERTS
# ============================================================================

@router.post("/alert-rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
def create_alert_rule(
    data: AlertRuleCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Créer une règle d'alerte."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.create_alert_rule(data)


@router.get("/alert-rules", response_model=list[AlertRuleResponse])
def list_alert_rules(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Lister les règles d'alerte."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    rules, _ = service.list_alert_rules(skip, limit)
    return rules


@router.get("/alert-rules/{rule_id}", response_model=AlertRuleResponse)
def get_alert_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer une règle d'alerte."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    rule = service.get_alert_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Règle non trouvée"
        )
    return rule


@router.put("/alert-rules/{rule_id}", response_model=AlertRuleResponse)
def update_alert_rule(
    rule_id: int,
    data: AlertRuleUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Mettre à jour une règle d'alerte."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.update_alert_rule(rule_id, data)


@router.get("/alerts", response_model=list[AlertList])
def list_alerts(
    status_filter: AlertStatus | None = None,
    severity: AlertSeverity | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Lister les alertes."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    alerts, _ = service.list_alerts(status_filter, severity, skip, limit)
    return [
        AlertList(
            id=a.id,
            title=a.title,
            severity=a.severity,
            status=a.status,
            source_type=a.source_type,
            triggered_at=a.triggered_at
        )
        for a in alerts
    ]


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer une alerte."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    alert = service.get_alert(alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerte non trouvée"
        )
    return alert


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(
    alert_id: int,
    data: AlertAcknowledge,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Acquitter une alerte."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.acknowledge_alert(alert_id, data.notes)


@router.post("/alerts/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(
    alert_id: int,
    data: AlertResolve,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Résoudre une alerte."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.resolve_alert(alert_id, data.resolution_notes)


@router.post("/alerts/{alert_id}/snooze", response_model=AlertResponse)
def snooze_alert(
    alert_id: int,
    data: AlertSnooze,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Mettre en pause une alerte."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.snooze_alert(alert_id, data.snooze_until)


# ============================================================================
# DATA SOURCES
# ============================================================================

@router.post("/data-sources", response_model=DataSourceResponse, status_code=status.HTTP_201_CREATED)
def create_data_source(
    data: DataSourceCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Créer une source de données."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.create_data_source(data)


@router.get("/data-sources", response_model=list[DataSourceResponse])
def list_data_sources(
    source_type: DataSourceType | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Lister les sources de données."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    sources, _ = service.list_data_sources(source_type, skip, limit)
    return sources


@router.get("/data-sources/{source_id}", response_model=DataSourceResponse)
def get_data_source(
    source_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer une source de données."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    source = service.get_data_source(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source non trouvée"
        )
    return source


@router.put("/data-sources/{source_id}", response_model=DataSourceResponse)
def update_data_source(
    source_id: int,
    data: DataSourceUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Mettre à jour une source de données."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.update_data_source(source_id, data)


# ============================================================================
# DATA QUERIES
# ============================================================================

@router.post("/queries", response_model=DataQueryResponse, status_code=status.HTTP_201_CREATED)
def create_query(
    data: DataQueryCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Créer une requête."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.create_query(data)


@router.get("/queries", response_model=list[DataQueryResponse])
def list_queries(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Lister les requêtes."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    queries, _ = service.list_queries(skip, limit)
    return queries


@router.get("/queries/{query_id}", response_model=DataQueryResponse)
def get_query(
    query_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer une requête."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    query = service.get_query(query_id)
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requête non trouvée"
        )
    return query


# ============================================================================
# BOOKMARKS
# ============================================================================

@router.post("/bookmarks", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
def create_bookmark(
    data: BookmarkCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Créer un favori."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.create_bookmark(data)


@router.get("/bookmarks", response_model=list[BookmarkResponse])
def list_bookmarks(
    item_type: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Lister les favoris."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.list_bookmarks(item_type)


@router.delete("/bookmarks/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bookmark(
    bookmark_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Supprimer un favori."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    if not service.delete_bookmark(bookmark_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favori non trouvé"
        )


# ============================================================================
# EXPORTS
# ============================================================================

@router.post("/exports", response_model=ExportResponse, status_code=status.HTTP_201_CREATED)
def create_export(
    data: ExportRequest,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Créer un export."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.create_export(data)


@router.get("/exports", response_model=list[ExportResponse])
def list_exports(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Lister les exports."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    return service.list_exports(skip, limit)


@router.get("/exports/{export_id}", response_model=ExportResponse)
def get_export(
    export_id: int,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer un export."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    export = service.get_export(export_id)
    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export non trouvé"
        )
    return export


# ============================================================================
# OVERVIEW
# ============================================================================

@router.get("/overview", response_model=BIOverview)
@router.get("/stats", response_model=BIOverview)
def get_overview(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Vue d'ensemble BI (alias: /stats)."""
    service = get_bi_service(db, context.tenant_id, str(context.user_id))
    data = service.get_overview()

    return BIOverview(
        dashboards=data.get("dashboards", {}),
        reports=data.get("reports", {}),
        kpis=data.get("kpis", {}),
        alerts=AlertSummary(
            total=data.get("alerts", {}).get("active", 0),
            by_severity={},
            by_status={},
            recent=[]
        ),
        exports={},
        data_sources=data.get("data_sources", {})
    )
