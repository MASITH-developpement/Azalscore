"""
AZALS - Module M10: BI & Reporting
Schémas Pydantic pour Business Intelligence
"""

from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from .models import (
    DashboardType,
    WidgetType,
    ChartType,
    ReportType,
    ReportFormat,
    ReportStatus,
    KPICategory,
    KPITrend,
    AlertSeverity,
    AlertStatus,
    DataSourceType,
    RefreshFrequency,
)


# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================

class WidgetFilterBase(BaseModel):
    """Base pour les filtres de widget."""
    field_name: str
    operator: str
    value: Optional[Any] = None
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
    chart_type: Optional[ChartType] = None
    position_x: int = 0
    position_y: int = 0
    width: int = 4
    height: int = 3
    config: Optional[Dict[str, Any]] = None
    chart_options: Optional[Dict[str, Any]] = None
    colors: Optional[List[str]] = None
    static_data: Optional[Any] = None
    data_mapping: Optional[Dict[str, str]] = None
    drill_down_config: Optional[Dict[str, Any]] = None
    click_action: Optional[Dict[str, Any]] = None
    show_title: bool = True
    show_legend: bool = True
    show_toolbar: bool = True


class WidgetCreate(WidgetBase):
    """Création d'un widget."""
    data_source_id: Optional[int] = None
    query_id: Optional[int] = None
    kpi_id: Optional[int] = None
    filters: Optional[List[WidgetFilterCreate]] = None


class WidgetUpdate(BaseModel):
    """Mise à jour d'un widget."""
    title: Optional[str] = None
    widget_type: Optional[WidgetType] = None
    chart_type: Optional[ChartType] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    data_source_id: Optional[int] = None
    query_id: Optional[int] = None
    kpi_id: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    chart_options: Optional[Dict[str, Any]] = None
    colors: Optional[List[str]] = None
    static_data: Optional[Any] = None
    data_mapping: Optional[Dict[str, str]] = None
    show_title: Optional[bool] = None
    show_legend: Optional[bool] = None
    show_toolbar: Optional[bool] = None
    is_active: Optional[bool] = None


class WidgetResponse(WidgetBase):
    """Réponse widget."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    dashboard_id: int
    data_source_id: Optional[int]
    query_id: Optional[int]
    kpi_id: Optional[int]
    is_active: bool
    display_order: int
    filters: List[WidgetFilterResponse] = []
    created_at: datetime
    updated_at: datetime


class DashboardBase(BaseModel):
    """Base pour les tableaux de bord."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    dashboard_type: DashboardType = DashboardType.CUSTOM
    layout: Optional[Dict[str, Any]] = None
    theme: str = "default"
    refresh_frequency: RefreshFrequency = RefreshFrequency.ON_DEMAND
    auto_refresh: bool = False
    global_filters: Optional[Dict[str, Any]] = None
    default_date_range: Optional[str] = None


class DashboardCreate(DashboardBase):
    """Création d'un tableau de bord."""
    is_shared: bool = False
    shared_with: Optional[List[int]] = None
    is_default: bool = False
    is_public: bool = False


class DashboardUpdate(BaseModel):
    """Mise à jour d'un tableau de bord."""
    name: Optional[str] = None
    description: Optional[str] = None
    dashboard_type: Optional[DashboardType] = None
    layout: Optional[Dict[str, Any]] = None
    theme: Optional[str] = None
    refresh_frequency: Optional[RefreshFrequency] = None
    auto_refresh: Optional[bool] = None
    global_filters: Optional[Dict[str, Any]] = None
    default_date_range: Optional[str] = None
    is_shared: Optional[bool] = None
    shared_with: Optional[List[int]] = None
    is_default: Optional[bool] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None


class DashboardResponse(DashboardBase):
    """Réponse tableau de bord."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    owner_id: int
    is_shared: bool
    shared_with: Optional[List[int]]
    is_default: bool
    is_public: bool
    view_count: int
    last_viewed_at: Optional[datetime]
    is_active: bool
    widgets: List[WidgetResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]


class DashboardList(BaseModel):
    """Liste de tableaux de bord."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: Optional[str]
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
    cron_expression: Optional[str] = None
    frequency: Optional[RefreshFrequency] = None
    parameters: Optional[Dict[str, Any]] = None
    output_format: ReportFormat = ReportFormat.PDF
    recipients: Optional[List[str]] = None
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
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    last_status: Optional[ReportStatus]
    is_enabled: bool
    created_at: datetime


class ReportBase(BaseModel):
    """Base pour les rapports."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    report_type: ReportType
    template: Optional[str] = None
    template_file: Optional[str] = None
    data_sources: Optional[List[Dict[str, Any]]] = None
    queries: Optional[List[Dict[str, Any]]] = None
    parameters: Optional[Dict[str, Any]] = None
    available_formats: List[str] = ["pdf", "excel"]
    default_format: ReportFormat = ReportFormat.PDF
    page_size: str = "A4"
    orientation: str = "portrait"


class ReportCreate(ReportBase):
    """Création d'un rapport."""
    is_public: bool = False
    allowed_roles: Optional[List[str]] = None


class ReportUpdate(BaseModel):
    """Mise à jour d'un rapport."""
    name: Optional[str] = None
    description: Optional[str] = None
    report_type: Optional[ReportType] = None
    template: Optional[str] = None
    template_file: Optional[str] = None
    data_sources: Optional[List[Dict[str, Any]]] = None
    queries: Optional[List[Dict[str, Any]]] = None
    parameters: Optional[Dict[str, Any]] = None
    available_formats: Optional[List[str]] = None
    default_format: Optional[ReportFormat] = None
    page_size: Optional[str] = None
    orientation: Optional[str] = None
    is_public: Optional[bool] = None
    allowed_roles: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ReportResponse(ReportBase):
    """Réponse rapport."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    owner_id: int
    is_public: bool
    allowed_roles: Optional[List[str]]
    is_active: bool
    version: int
    schedules: List[ReportScheduleResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]


class ReportList(BaseModel):
    """Liste de rapports."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: Optional[str]
    report_type: ReportType
    owner_id: int
    is_public: bool
    available_formats: List[str]
    schedule_count: int = 0
    created_at: datetime


class ReportExecutionResponse(BaseModel):
    """Réponse exécution."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_id: int
    schedule_id: Optional[int]
    status: ReportStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    parameters: Optional[Dict[str, Any]]
    output_format: ReportFormat
    file_path: Optional[str]
    file_size: Optional[int]
    file_url: Optional[str]
    row_count: Optional[int]
    error_message: Optional[str]
    triggered_by: Optional[int]
    created_at: datetime


class ReportExecuteRequest(BaseModel):
    """Demande d'exécution de rapport."""
    output_format: ReportFormat = ReportFormat.PDF
    parameters: Optional[Dict[str, Any]] = None
    async_execution: bool = False


# ============================================================================
# KPI SCHEMAS
# ============================================================================

class KPITargetBase(BaseModel):
    """Base pour objectifs KPI."""
    year: int
    month: Optional[int] = None
    quarter: Optional[int] = None
    target_value: Decimal
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    notes: Optional[str] = None


class KPITargetCreate(KPITargetBase):
    """Création d'un objectif."""
    pass


class KPITargetResponse(KPITargetBase):
    """Réponse objectif."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    kpi_id: int
    current_value: Optional[Decimal]
    achievement_percentage: Optional[Decimal]
    created_at: datetime


class KPIValueBase(BaseModel):
    """Base pour valeurs KPI."""
    period_date: date
    period_type: str = "daily"
    value: Decimal
    dimension: Optional[str] = None
    dimension_value: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


class KPIValueCreate(KPIValueBase):
    """Création d'une valeur."""
    source: str = "manual"


class KPIValueResponse(KPIValueBase):
    """Réponse valeur."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    kpi_id: int
    previous_value: Optional[Decimal]
    change_percentage: Optional[Decimal]
    trend: KPITrend
    source: str
    calculated_at: datetime


class KPIBase(BaseModel):
    """Base pour les KPIs."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: KPICategory
    formula: Optional[str] = None
    unit: Optional[str] = None
    precision: int = 2
    aggregation_method: str = "sum"
    display_format: Optional[str] = None
    good_threshold: Optional[Decimal] = None
    warning_threshold: Optional[Decimal] = None
    bad_threshold: Optional[Decimal] = None
    higher_is_better: bool = True
    refresh_frequency: RefreshFrequency = RefreshFrequency.DAILY
    compare_to_previous: bool = True
    comparison_period: str = "previous_period"


class KPICreate(KPIBase):
    """Création d'un KPI."""
    data_source_id: Optional[int] = None
    query: Optional[str] = None


class KPIUpdate(BaseModel):
    """Mise à jour d'un KPI."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[KPICategory] = None
    formula: Optional[str] = None
    unit: Optional[str] = None
    precision: Optional[int] = None
    aggregation_method: Optional[str] = None
    data_source_id: Optional[int] = None
    query: Optional[str] = None
    display_format: Optional[str] = None
    good_threshold: Optional[Decimal] = None
    warning_threshold: Optional[Decimal] = None
    bad_threshold: Optional[Decimal] = None
    higher_is_better: Optional[bool] = None
    refresh_frequency: Optional[RefreshFrequency] = None
    compare_to_previous: Optional[bool] = None
    comparison_period: Optional[str] = None
    is_active: Optional[bool] = None


class KPIResponse(KPIBase):
    """Réponse KPI."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    data_source_id: Optional[int]
    query: Optional[str]
    last_calculated_at: Optional[datetime]
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]

    # Valeur actuelle (calculée dynamiquement)
    current_value: Optional[Decimal] = None
    previous_value: Optional[Decimal] = None
    change_percentage: Optional[Decimal] = None
    trend: Optional[KPITrend] = None
    target: Optional[KPITargetResponse] = None


class KPIList(BaseModel):
    """Liste de KPIs."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    category: KPICategory
    unit: Optional[str]
    current_value: Optional[Decimal] = None
    change_percentage: Optional[Decimal] = None
    trend: Optional[KPITrend] = None
    is_active: bool


# ============================================================================
# ALERT SCHEMAS
# ============================================================================

class AlertRuleBase(BaseModel):
    """Base pour règles d'alerte."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    severity: AlertSeverity
    source_type: str
    source_id: Optional[int] = None
    condition: Dict[str, Any]
    check_frequency: RefreshFrequency = RefreshFrequency.HOURLY
    notification_channels: Optional[List[str]] = None
    recipients: Optional[List[str]] = None
    cooldown_minutes: int = 60
    auto_resolve: bool = False


class AlertRuleCreate(AlertRuleBase):
    """Création d'une règle."""
    is_enabled: bool = True


class AlertRuleUpdate(BaseModel):
    """Mise à jour d'une règle."""
    name: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[AlertSeverity] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    condition: Optional[Dict[str, Any]] = None
    check_frequency: Optional[RefreshFrequency] = None
    notification_channels: Optional[List[str]] = None
    recipients: Optional[List[str]] = None
    cooldown_minutes: Optional[int] = None
    auto_resolve: Optional[bool] = None
    is_enabled: Optional[bool] = None


class AlertRuleResponse(AlertRuleBase):
    """Réponse règle."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    is_enabled: bool
    last_checked_at: Optional[datetime]
    last_triggered_at: Optional[datetime]
    created_at: datetime
    created_by: Optional[int]


class AlertBase(BaseModel):
    """Base pour les alertes."""
    title: str = Field(..., min_length=1, max_length=200)
    message: str
    severity: AlertSeverity
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    source_value: Optional[Decimal] = None
    threshold_value: Optional[Decimal] = None
    context: Optional[Dict[str, Any]] = None
    link: Optional[str] = None


class AlertCreate(AlertBase):
    """Création d'une alerte."""
    rule_id: Optional[int] = None


class AlertUpdate(BaseModel):
    """Mise à jour d'une alerte."""
    status: Optional[AlertStatus] = None
    resolution_notes: Optional[str] = None
    snoozed_until: Optional[datetime] = None


class AlertResponse(AlertBase):
    """Réponse alerte."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    rule_id: Optional[int]
    status: AlertStatus
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[int]
    resolved_at: Optional[datetime]
    resolved_by: Optional[int]
    resolution_notes: Optional[str]
    snoozed_until: Optional[datetime]
    notifications_sent: Optional[Dict[str, Any]]
    triggered_at: datetime
    created_at: datetime


class AlertList(BaseModel):
    """Liste d'alertes."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    severity: AlertSeverity
    status: AlertStatus
    source_type: Optional[str]
    triggered_at: datetime


class AlertAcknowledge(BaseModel):
    """Acquittement d'alerte."""
    notes: Optional[str] = None


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
    description: Optional[str] = None
    source_type: DataSourceType
    connection_config: Optional[Dict[str, Any]] = None
    schema_definition: Optional[Dict[str, Any]] = None
    refresh_frequency: RefreshFrequency = RefreshFrequency.DAILY
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600


class DataSourceCreate(DataSourceBase):
    """Création d'une source."""
    is_encrypted: bool = True
    allowed_roles: Optional[List[str]] = None


class DataSourceUpdate(BaseModel):
    """Mise à jour d'une source."""
    name: Optional[str] = None
    description: Optional[str] = None
    connection_config: Optional[Dict[str, Any]] = None
    schema_definition: Optional[Dict[str, Any]] = None
    refresh_frequency: Optional[RefreshFrequency] = None
    cache_enabled: Optional[bool] = None
    cache_ttl_seconds: Optional[int] = None
    allowed_roles: Optional[List[str]] = None
    is_active: Optional[bool] = None


class DataSourceResponse(DataSourceBase):
    """Réponse source."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    is_encrypted: bool
    allowed_roles: Optional[List[str]]
    is_active: bool
    is_system: bool
    last_synced_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]


class DataQueryBase(BaseModel):
    """Base pour requêtes."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    query_type: str = "sql"
    query_text: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    result_columns: Optional[List[Dict[str, str]]] = None
    cache_enabled: bool = False
    cache_ttl_seconds: int = 300


class DataQueryCreate(DataQueryBase):
    """Création d'une requête."""
    data_source_id: Optional[int] = None


class DataQueryUpdate(BaseModel):
    """Mise à jour d'une requête."""
    name: Optional[str] = None
    description: Optional[str] = None
    data_source_id: Optional[int] = None
    query_type: Optional[str] = None
    query_text: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    result_columns: Optional[List[Dict[str, str]]] = None
    cache_enabled: Optional[bool] = None
    cache_ttl_seconds: Optional[int] = None
    is_active: Optional[bool] = None


class DataQueryResponse(DataQueryBase):
    """Réponse requête."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    data_source_id: Optional[int]
    sample_data: Optional[Any]
    last_executed_at: Optional[datetime]
    last_execution_time_ms: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]


class DataQueryExecute(BaseModel):
    """Exécution de requête."""
    parameters: Optional[Dict[str, Any]] = None
    limit: int = 1000
    offset: int = 0


class DataQueryResult(BaseModel):
    """Résultat de requête."""
    columns: List[Dict[str, str]]
    rows: List[Dict[str, Any]]
    total_rows: int
    execution_time_ms: int


# ============================================================================
# USER FEATURES SCHEMAS
# ============================================================================

class BookmarkBase(BaseModel):
    """Base pour favoris."""
    item_type: str  # dashboard, report, kpi
    item_id: int
    item_name: Optional[str] = None
    folder: Optional[str] = None


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
    item_type: Optional[str] = None
    item_id: Optional[int] = None
    format: ReportFormat
    parameters: Optional[Dict[str, Any]] = None
    filename: Optional[str] = None


class ExportResponse(BaseModel):
    """Réponse export."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    export_type: str
    item_type: Optional[str]
    item_id: Optional[int]
    item_name: Optional[str]
    format: ReportFormat
    file_name: Optional[str]
    file_url: Optional[str]
    file_size: Optional[int]
    status: ReportStatus
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


# ============================================================================
# DASHBOARD STATS & OVERVIEW
# ============================================================================

class DashboardStats(BaseModel):
    """Statistiques d'un tableau de bord."""
    dashboard_id: int
    dashboard_name: str
    widget_count: int
    view_count: int
    last_viewed_at: Optional[datetime]
    avg_load_time_ms: Optional[int]
    active_users: int = 0


class KPISummary(BaseModel):
    """Résumé d'un KPI."""
    id: int
    code: str
    name: str
    category: KPICategory
    current_value: Optional[Decimal]
    unit: Optional[str]
    trend: Optional[KPITrend]
    change_percentage: Optional[Decimal]
    status: str = "normal"  # normal, warning, critical


class AlertSummary(BaseModel):
    """Résumé des alertes."""
    total: int
    by_severity: Dict[str, int]
    by_status: Dict[str, int]
    recent: List[AlertList]


class BIOverview(BaseModel):
    """Vue d'ensemble BI."""
    dashboards: Dict[str, Any]  # total, recent, most_viewed
    reports: Dict[str, Any]  # total, recent_executions, scheduled
    kpis: Dict[str, Any]  # total, by_category, critical
    alerts: AlertSummary
    exports: Dict[str, Any]  # total_today, by_format
    data_sources: Dict[str, Any]  # total, by_type, last_synced
