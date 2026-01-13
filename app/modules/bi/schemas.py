"""
AZALS - Module M10: BI & Reporting
Schémas Pydantic pour Business Intelligence
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .models import (
    AlertSeverity,
    AlertStatus,
    ChartType,
    DashboardType,
    DataSourceType,
    KPICategory,
    KPITrend,
    RefreshFrequency,
    ReportFormat,
    ReportStatus,
    ReportType,
    WidgetType,
)

# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================

class WidgetFilterBase(BaseModel):
    """Base pour les filtres de widget."""
    field_name: str
    operator: str
    value: Any | None = None
    is_dynamic: bool = False


class WidgetFilterCreate(WidgetFilterBase):
    """Création d'un filtre."""
    pass


class WidgetFilterResponse(WidgetFilterBase):
    """Réponse filtre."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    widget_id: int


class WidgetBase(BaseModel):
    """Base pour les widgets."""
    title: str = Field(..., min_length=1, max_length=200)
    widget_type: WidgetType
    chart_type: ChartType | None = None
    position_x: int = 0
    position_y: int = 0
    width: int = 4
    height: int = 3
    config: dict[str, Any] | None = None
    chart_options: dict[str, Any] | None = None
    colors: list[str] | None = None
    static_data: Any | None = None
    data_mapping: dict[str, str] | None = None
    drill_down_config: dict[str, Any] | None = None
    click_action: dict[str, Any] | None = None
    show_title: bool = True
    show_legend: bool = True
    show_toolbar: bool = True


class WidgetCreate(WidgetBase):
    """Création d'un widget."""
    data_source_id: int | None = None
    query_id: int | None = None
    kpi_id: int | None = None
    filters: list[WidgetFilterCreate] | None = None


class WidgetUpdate(BaseModel):
    """Mise à jour d'un widget."""
    title: str | None = None
    widget_type: WidgetType | None = None
    chart_type: ChartType | None = None
    position_x: int | None = None
    position_y: int | None = None
    width: int | None = None
    height: int | None = None
    data_source_id: int | None = None
    query_id: int | None = None
    kpi_id: int | None = None
    config: dict[str, Any] | None = None
    chart_options: dict[str, Any] | None = None
    colors: list[str] | None = None
    static_data: Any | None = None
    data_mapping: dict[str, str] | None = None
    show_title: bool | None = None
    show_legend: bool | None = None
    show_toolbar: bool | None = None
    is_active: bool | None = None


class WidgetResponse(WidgetBase):
    """Réponse widget."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    dashboard_id: int
    data_source_id: int | None
    query_id: int | None
    kpi_id: int | None
    is_active: bool
    display_order: int
    filters: list[WidgetFilterResponse] = []
    created_at: datetime
    updated_at: datetime


class DashboardBase(BaseModel):
    """Base pour les tableaux de bord."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    dashboard_type: DashboardType = DashboardType.CUSTOM
    layout: dict[str, Any] | None = None
    theme: str = "default"
    refresh_frequency: RefreshFrequency = RefreshFrequency.ON_DEMAND
    auto_refresh: bool = False
    global_filters: dict[str, Any] | None = None
    default_date_range: str | None = None


class DashboardCreate(DashboardBase):
    """Création d'un tableau de bord."""
    is_shared: bool = False
    shared_with: list[int] | None = None
    is_default: bool = False
    is_public: bool = False


class DashboardUpdate(BaseModel):
    """Mise à jour d'un tableau de bord."""
    name: str | None = None
    description: str | None = None
    dashboard_type: DashboardType | None = None
    layout: dict[str, Any] | None = None
    theme: str | None = None
    refresh_frequency: RefreshFrequency | None = None
    auto_refresh: bool | None = None
    global_filters: dict[str, Any] | None = None
    default_date_range: str | None = None
    is_shared: bool | None = None
    shared_with: list[int] | None = None
    is_default: bool | None = None
    is_public: bool | None = None
    is_active: bool | None = None


class DashboardResponse(DashboardBase):
    """Réponse tableau de bord."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    owner_id: int
    is_shared: bool
    shared_with: list[int] | None
    is_default: bool
    is_public: bool
    view_count: int
    last_viewed_at: datetime | None
    is_active: bool
    widgets: list[WidgetResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: int | None


class DashboardList(BaseModel):
    """Liste de tableaux de bord."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None
    dashboard_type: DashboardType
    owner_id: int
    is_shared: bool
    is_public: bool
    view_count: int
    widget_count: int = 0
    created_at: datetime


# ============================================================================
# REPORT SCHEMAS
# ============================================================================

class ReportScheduleBase(BaseModel):
    """Base pour planification."""
    name: str = Field(..., min_length=1, max_length=200)
    cron_expression: str | None = None
    frequency: RefreshFrequency | None = None
    parameters: dict[str, Any] | None = None
    output_format: ReportFormat = ReportFormat.PDF
    recipients: list[str] | None = None
    distribution_method: str = "email"
    timezone: str = "Europe/Paris"


class ReportScheduleCreate(ReportScheduleBase):
    """Création d'une planification."""
    is_enabled: bool = True


class ReportScheduleResponse(ReportScheduleBase):
    """Réponse planification."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_id: int
    next_run_at: datetime | None
    last_run_at: datetime | None
    last_status: ReportStatus | None
    is_enabled: bool
    created_at: datetime


class ReportBase(BaseModel):
    """Base pour les rapports."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    report_type: ReportType
    template: str | None = None
    template_file: str | None = None
    data_sources: list[dict[str, Any]] | None = None
    queries: list[dict[str, Any]] | None = None
    parameters: dict[str, Any] | None = None
    available_formats: list[str] = ["pdf", "excel"]
    default_format: ReportFormat = ReportFormat.PDF
    page_size: str = "A4"
    orientation: str = "portrait"


class ReportCreate(ReportBase):
    """Création d'un rapport."""
    is_public: bool = False
    allowed_roles: list[str] | None = None


class ReportUpdate(BaseModel):
    """Mise à jour d'un rapport."""
    name: str | None = None
    description: str | None = None
    report_type: ReportType | None = None
    template: str | None = None
    template_file: str | None = None
    data_sources: list[dict[str, Any]] | None = None
    queries: list[dict[str, Any]] | None = None
    parameters: dict[str, Any] | None = None
    available_formats: list[str] | None = None
    default_format: ReportFormat | None = None
    page_size: str | None = None
    orientation: str | None = None
    is_public: bool | None = None
    allowed_roles: list[str] | None = None
    is_active: bool | None = None


class ReportResponse(ReportBase):
    """Réponse rapport."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    owner_id: int
    is_public: bool
    allowed_roles: list[str] | None
    is_active: bool
    version: int
    schedules: list[ReportScheduleResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: int | None


class ReportList(BaseModel):
    """Liste de rapports."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None
    report_type: ReportType
    owner_id: int
    is_public: bool
    available_formats: list[str]
    schedule_count: int = 0
    created_at: datetime


class ReportExecutionResponse(BaseModel):
    """Réponse exécution."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_id: int
    schedule_id: int | None
    status: ReportStatus
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: int | None
    parameters: dict[str, Any] | None
    output_format: ReportFormat
    file_path: str | None
    file_size: int | None
    file_url: str | None
    row_count: int | None
    error_message: str | None
    triggered_by: int | None
    created_at: datetime


class ReportExecuteRequest(BaseModel):
    """Demande d'exécution de rapport."""
    output_format: ReportFormat = ReportFormat.PDF
    parameters: dict[str, Any] | None = None
    async_execution: bool = False


# ============================================================================
# KPI SCHEMAS
# ============================================================================

class KPITargetBase(BaseModel):
    """Base pour objectifs KPI."""
    year: int
    month: int | None = None
    quarter: int | None = None
    target_value: Decimal
    min_value: Decimal | None = None
    max_value: Decimal | None = None
    notes: str | None = None


class KPITargetCreate(KPITargetBase):
    """Création d'un objectif."""
    pass


class KPITargetResponse(KPITargetBase):
    """Réponse objectif."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    kpi_id: int
    current_value: Decimal | None
    achievement_percentage: Decimal | None
    created_at: datetime


class KPIValueBase(BaseModel):
    """Base pour valeurs KPI."""
    period_date: date
    period_type: str = "daily"
    value: Decimal
    dimension: str | None = None
    dimension_value: str | None = None
    extra_data: dict[str, Any] | None = None


class KPIValueCreate(KPIValueBase):
    """Création d'une valeur."""
    source: str = "manual"


class KPIValueResponse(KPIValueBase):
    """Réponse valeur."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    kpi_id: int
    previous_value: Decimal | None
    change_percentage: Decimal | None
    trend: KPITrend
    source: str
    calculated_at: datetime


class KPIBase(BaseModel):
    """Base pour les KPIs."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    category: KPICategory
    formula: str | None = None
    unit: str | None = None
    precision: int = 2
    aggregation_method: str = "sum"
    display_format: str | None = None
    good_threshold: Decimal | None = None
    warning_threshold: Decimal | None = None
    bad_threshold: Decimal | None = None
    higher_is_better: bool = True
    refresh_frequency: RefreshFrequency = RefreshFrequency.DAILY
    compare_to_previous: bool = True
    comparison_period: str = "previous_period"


class KPICreate(KPIBase):
    """Création d'un KPI."""
    data_source_id: int | None = None
    query: str | None = None


class KPIUpdate(BaseModel):
    """Mise à jour d'un KPI."""
    name: str | None = None
    description: str | None = None
    category: KPICategory | None = None
    formula: str | None = None
    unit: str | None = None
    precision: int | None = None
    aggregation_method: str | None = None
    data_source_id: int | None = None
    query: str | None = None
    display_format: str | None = None
    good_threshold: Decimal | None = None
    warning_threshold: Decimal | None = None
    bad_threshold: Decimal | None = None
    higher_is_better: bool | None = None
    refresh_frequency: RefreshFrequency | None = None
    compare_to_previous: bool | None = None
    comparison_period: str | None = None
    is_active: bool | None = None


class KPIResponse(KPIBase):
    """Réponse KPI."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    data_source_id: int | None
    query: str | None
    last_calculated_at: datetime | None
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    created_by: int | None

    # Valeur actuelle (calculée dynamiquement)
    current_value: Decimal | None = None
    previous_value: Decimal | None = None
    change_percentage: Decimal | None = None
    trend: KPITrend | None = None
    target: KPITargetResponse | None = None


class KPIList(BaseModel):
    """Liste de KPIs."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    category: KPICategory
    unit: str | None
    current_value: Decimal | None = None
    change_percentage: Decimal | None = None
    trend: KPITrend | None = None
    is_active: bool


# ============================================================================
# ALERT SCHEMAS
# ============================================================================

class AlertRuleBase(BaseModel):
    """Base pour règles d'alerte."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    severity: AlertSeverity
    source_type: str
    source_id: int | None = None
    condition: dict[str, Any]
    check_frequency: RefreshFrequency = RefreshFrequency.HOURLY
    notification_channels: list[str] | None = None
    recipients: list[str] | None = None
    cooldown_minutes: int = 60
    auto_resolve: bool = False


class AlertRuleCreate(AlertRuleBase):
    """Création d'une règle."""
    is_enabled: bool = True


class AlertRuleUpdate(BaseModel):
    """Mise à jour d'une règle."""
    name: str | None = None
    description: str | None = None
    severity: AlertSeverity | None = None
    source_type: str | None = None
    source_id: int | None = None
    condition: dict[str, Any] | None = None
    check_frequency: RefreshFrequency | None = None
    notification_channels: list[str] | None = None
    recipients: list[str] | None = None
    cooldown_minutes: int | None = None
    auto_resolve: bool | None = None
    is_enabled: bool | None = None


class AlertRuleResponse(AlertRuleBase):
    """Réponse règle."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    is_enabled: bool
    last_checked_at: datetime | None
    last_triggered_at: datetime | None
    created_at: datetime
    created_by: int | None


class AlertBase(BaseModel):
    """Base pour les alertes."""
    title: str = Field(..., min_length=1, max_length=200)
    message: str
    severity: AlertSeverity
    source_type: str | None = None
    source_id: int | None = None
    source_value: Decimal | None = None
    threshold_value: Decimal | None = None
    context: dict[str, Any] | None = None
    link: str | None = None


class AlertCreate(AlertBase):
    """Création d'une alerte."""
    rule_id: int | None = None


class AlertUpdate(BaseModel):
    """Mise à jour d'une alerte."""
    status: AlertStatus | None = None
    resolution_notes: str | None = None
    snoozed_until: datetime | None = None


class AlertResponse(AlertBase):
    """Réponse alerte."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    rule_id: int | None
    status: AlertStatus
    acknowledged_at: datetime | None
    acknowledged_by: int | None
    resolved_at: datetime | None
    resolved_by: int | None
    resolution_notes: str | None
    snoozed_until: datetime | None
    notifications_sent: dict[str, Any] | None
    triggered_at: datetime
    created_at: datetime


class AlertList(BaseModel):
    """Liste d'alertes."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    severity: AlertSeverity
    status: AlertStatus
    source_type: str | None
    triggered_at: datetime


class AlertAcknowledge(BaseModel):
    """Acquittement d'alerte."""
    notes: str | None = None


class AlertResolve(BaseModel):
    """Résolution d'alerte."""
    resolution_notes: str


class AlertSnooze(BaseModel):
    """Mise en pause d'alerte."""
    snooze_until: datetime


# ============================================================================
# DATA SOURCE SCHEMAS
# ============================================================================

class DataSourceBase(BaseModel):
    """Base pour sources de données."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    source_type: DataSourceType
    connection_config: dict[str, Any] | None = None
    schema_definition: dict[str, Any] | None = None
    refresh_frequency: RefreshFrequency = RefreshFrequency.DAILY
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600


class DataSourceCreate(DataSourceBase):
    """Création d'une source."""
    is_encrypted: bool = True
    allowed_roles: list[str] | None = None


class DataSourceUpdate(BaseModel):
    """Mise à jour d'une source."""
    name: str | None = None
    description: str | None = None
    connection_config: dict[str, Any] | None = None
    schema_definition: dict[str, Any] | None = None
    refresh_frequency: RefreshFrequency | None = None
    cache_enabled: bool | None = None
    cache_ttl_seconds: int | None = None
    allowed_roles: list[str] | None = None
    is_active: bool | None = None


class DataSourceResponse(DataSourceBase):
    """Réponse source."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    is_encrypted: bool
    allowed_roles: list[str] | None
    is_active: bool
    is_system: bool
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime
    created_by: int | None


class DataQueryBase(BaseModel):
    """Base pour requêtes."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    query_type: str = "sql"
    query_text: str | None = None
    parameters: dict[str, Any] | None = None
    result_columns: list[dict[str, str]] | None = None
    cache_enabled: bool = False
    cache_ttl_seconds: int = 300


class DataQueryCreate(DataQueryBase):
    """Création d'une requête."""
    data_source_id: int | None = None


class DataQueryUpdate(BaseModel):
    """Mise à jour d'une requête."""
    name: str | None = None
    description: str | None = None
    data_source_id: int | None = None
    query_type: str | None = None
    query_text: str | None = None
    parameters: dict[str, Any] | None = None
    result_columns: list[dict[str, str]] | None = None
    cache_enabled: bool | None = None
    cache_ttl_seconds: int | None = None
    is_active: bool | None = None


class DataQueryResponse(DataQueryBase):
    """Réponse requête."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    data_source_id: int | None
    sample_data: Any | None
    last_executed_at: datetime | None
    last_execution_time_ms: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: int | None


class DataQueryExecute(BaseModel):
    """Exécution de requête."""
    parameters: dict[str, Any] | None = None
    limit: int = 1000
    offset: int = 0


class DataQueryResult(BaseModel):
    """Résultat de requête."""
    columns: list[dict[str, str]]
    rows: list[dict[str, Any]]
    total_rows: int
    execution_time_ms: int


# ============================================================================
# USER FEATURES SCHEMAS
# ============================================================================

class BookmarkBase(BaseModel):
    """Base pour favoris."""
    item_type: str  # dashboard, report, kpi
    item_id: int
    item_name: str | None = None
    folder: str | None = None


class BookmarkCreate(BookmarkBase):
    """Création d'un favori."""
    pass


class BookmarkResponse(BookmarkBase):
    """Réponse favori."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    display_order: int
    created_at: datetime


# ============================================================================
# EXPORT SCHEMAS
# ============================================================================

class ExportRequest(BaseModel):
    """Demande d'export."""
    export_type: str  # dashboard, report, data, kpi
    item_type: str | None = None
    item_id: int | None = None
    format: ReportFormat
    parameters: dict[str, Any] | None = None
    filename: str | None = None


class ExportResponse(BaseModel):
    """Réponse export."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    export_type: str
    item_type: str | None
    item_id: int | None
    item_name: str | None
    format: ReportFormat
    file_name: str | None
    file_url: str | None
    file_size: int | None
    status: ReportStatus
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


# ============================================================================
# DASHBOARD STATS & OVERVIEW
# ============================================================================

class DashboardStats(BaseModel):
    """Statistiques d'un tableau de bord."""
    dashboard_id: int
    dashboard_name: str
    widget_count: int
    view_count: int
    last_viewed_at: datetime | None
    avg_load_time_ms: int | None
    active_users: int = 0


class KPISummary(BaseModel):
    """Résumé d'un KPI."""
    id: int
    code: str
    name: str
    category: KPICategory
    current_value: Decimal | None
    unit: str | None
    trend: KPITrend | None
    change_percentage: Decimal | None
    status: str = "normal"  # normal, warning, critical


class AlertSummary(BaseModel):
    """Résumé des alertes."""
    total: int
    by_severity: dict[str, int]
    by_status: dict[str, int]
    recent: list[AlertList]


class BIOverview(BaseModel):
    """Vue d'ensemble BI."""
    dashboards: dict[str, Any]  # total, recent, most_viewed
    reports: dict[str, Any]  # total, recent_executions, scheduled
    kpis: dict[str, Any]  # total, by_category, critical
    alerts: AlertSummary
    exports: dict[str, Any]  # total_today, by_format
    data_sources: dict[str, Any]  # total, by_type, last_synced
