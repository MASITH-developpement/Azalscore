"""
AZALSCORE ERP - Module DASHBOARDS
==================================
Schemas Pydantic pour validation et serialisation.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import (
    DashboardType,
    WidgetType,
    ChartType,
    DataSourceType,
    RefreshFrequency,
    AlertSeverity,
    AlertStatus,
    AlertOperator,
    SharePermission,
    ExportFormat,
    ExportStatus,
)


# ============================================================================
# BASE SCHEMAS
# ============================================================================

class DashboardFilters(BaseModel):
    """Filtres pour recherche de dashboards."""
    search: Optional[str] = None
    dashboard_type: Optional[DashboardType] = None
    owner_id: Optional[UUID] = None
    is_shared: Optional[bool] = None
    is_public: Optional[bool] = None
    is_template: Optional[bool] = None
    is_favorite: Optional[bool] = None
    tags: Optional[list[str]] = None
    category: Optional[str] = None
    created_from: Optional[date] = None
    created_to: Optional[date] = None


class WidgetFilters(BaseModel):
    """Filtres pour recherche de widgets."""
    search: Optional[str] = None
    widget_type: Optional[WidgetType] = None
    dashboard_id: Optional[UUID] = None
    has_alerts: Optional[bool] = None


# ============================================================================
# WIDGET SCHEMAS
# ============================================================================

class WidgetPositionUpdate(BaseModel):
    """Mise a jour position widget."""
    position_x: int = Field(..., ge=0)
    position_y: int = Field(..., ge=0)
    width: int = Field(..., ge=1, le=12)
    height: int = Field(..., ge=1, le=20)


class WidgetLayoutItem(BaseModel):
    """Element de layout pour drag & drop."""
    widget_id: UUID
    position_x: int = Field(..., ge=0)
    position_y: int = Field(..., ge=0)
    width: int = Field(..., ge=1, le=12)
    height: int = Field(..., ge=1, le=20)


class WidgetLayoutUpdate(BaseModel):
    """Mise a jour layout complet."""
    layout: list[WidgetLayoutItem]


class WidgetBase(BaseModel):
    """Base pour widgets."""
    title: str = Field(..., min_length=1, max_length=200)
    subtitle: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    widget_type: WidgetType
    chart_type: Optional[ChartType] = None

    # Position
    position_x: int = Field(default=0, ge=0)
    position_y: int = Field(default=0, ge=0)
    width: int = Field(default=4, ge=1, le=12)
    height: int = Field(default=3, ge=1, le=20)
    min_width: int = Field(default=2, ge=1)
    min_height: int = Field(default=2, ge=1)
    max_width: Optional[int] = Field(None, le=12)
    max_height: Optional[int] = Field(None, le=20)

    # Configuration
    config: Optional[dict[str, Any]] = None
    chart_options: Optional[dict[str, Any]] = None
    display_options: Optional[dict[str, Any]] = None
    data_mapping: Optional[dict[str, Any]] = None
    aggregation: Optional[dict[str, Any]] = None
    colors: Optional[list[str]] = None
    custom_style: Optional[dict[str, Any]] = None

    # Interactions
    drill_down_config: Optional[dict[str, Any]] = None
    click_action: Optional[dict[str, Any]] = None
    links: Optional[list[dict[str, Any]]] = None

    # Filtres
    filters: Optional[dict[str, Any]] = None
    linked_to_global: bool = True

    # Affichage
    show_title: bool = True
    show_subtitle: bool = False
    show_legend: bool = True
    show_toolbar: bool = True
    show_border: bool = True


class WidgetCreate(WidgetBase):
    """Creation d'un widget."""
    code: Optional[str] = Field(None, max_length=50)
    data_source_id: Optional[UUID] = None
    query_config: Optional[dict[str, Any]] = None
    static_data: Optional[dict[str, Any]] = None
    refresh_frequency: Optional[RefreshFrequency] = None
    cache_ttl_seconds: int = Field(default=300, ge=0)


class WidgetUpdate(BaseModel):
    """Mise a jour d'un widget."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    subtitle: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    widget_type: Optional[WidgetType] = None
    chart_type: Optional[ChartType] = None

    position_x: Optional[int] = Field(None, ge=0)
    position_y: Optional[int] = Field(None, ge=0)
    width: Optional[int] = Field(None, ge=1, le=12)
    height: Optional[int] = Field(None, ge=1, le=20)

    data_source_id: Optional[UUID] = None
    query_config: Optional[dict[str, Any]] = None
    static_data: Optional[dict[str, Any]] = None

    config: Optional[dict[str, Any]] = None
    chart_options: Optional[dict[str, Any]] = None
    display_options: Optional[dict[str, Any]] = None
    data_mapping: Optional[dict[str, Any]] = None
    aggregation: Optional[dict[str, Any]] = None
    colors: Optional[list[str]] = None
    custom_style: Optional[dict[str, Any]] = None

    drill_down_config: Optional[dict[str, Any]] = None
    click_action: Optional[dict[str, Any]] = None
    filters: Optional[dict[str, Any]] = None
    linked_to_global: Optional[bool] = None

    show_title: Optional[bool] = None
    show_legend: Optional[bool] = None
    show_toolbar: Optional[bool] = None
    show_border: Optional[bool] = None

    refresh_frequency: Optional[RefreshFrequency] = None
    cache_ttl_seconds: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class WidgetResponse(WidgetBase):
    """Reponse widget."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: Optional[str]
    dashboard_id: UUID
    data_source_id: Optional[UUID]
    query_config: Optional[dict[str, Any]]
    static_data: Optional[dict[str, Any]]

    filter_fields: Optional[list[str]]
    refresh_frequency: Optional[RefreshFrequency]
    last_refreshed_at: Optional[datetime]
    cache_ttl_seconds: int

    has_alerts: bool
    is_active: bool
    display_order: int

    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]


class WidgetDataResponse(BaseModel):
    """Donnees d'un widget."""
    widget_id: UUID
    data: Any
    columns: Optional[list[dict[str, str]]] = None
    total_rows: Optional[int] = None
    aggregations: Optional[dict[str, Any]] = None
    last_updated: datetime
    cache_hit: bool = False
    execution_time_ms: int = 0


# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================

class DashboardBase(BaseModel):
    """Base pour dashboards."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=20)
    dashboard_type: DashboardType = DashboardType.CUSTOM

    # Mise en page
    layout_type: str = Field(default="grid", pattern="^(grid|flex|tabs)$")
    columns: int = Field(default=12, ge=1, le=24)
    row_height: int = Field(default=80, ge=20, le=500)
    margin: int = Field(default=10, ge=0, le=50)
    is_compact: bool = True
    is_draggable: bool = True
    is_resizable: bool = True

    # Theme
    theme: str = Field(default="default", max_length=50)
    background_color: Optional[str] = Field(None, max_length=20)
    custom_css: Optional[str] = None

    # Rafraichissement
    refresh_frequency: RefreshFrequency = RefreshFrequency.ON_DEMAND
    auto_refresh: bool = False

    # Filtres
    global_filters: Optional[dict[str, Any]] = None
    default_filters: Optional[dict[str, Any]] = None
    default_date_range: Optional[str] = Field(None, max_length=50)

    # Tags
    tags: Optional[list[str]] = None
    category: Optional[str] = Field(None, max_length=100)


class DashboardCreate(DashboardBase):
    """Creation d'un dashboard."""
    is_shared: bool = False
    is_public: bool = False
    is_template: bool = False
    is_default: bool = False
    is_home: bool = False

    # Widgets initiaux (optionnel)
    widgets: Optional[list[WidgetCreate]] = None

    # Depuis template
    template_id: Optional[UUID] = None


class DashboardUpdate(BaseModel):
    """Mise a jour d'un dashboard."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=20)
    dashboard_type: Optional[DashboardType] = None

    layout_type: Optional[str] = Field(None, pattern="^(grid|flex|tabs)$")
    layout_config: Optional[dict[str, Any]] = None
    columns: Optional[int] = Field(None, ge=1, le=24)
    row_height: Optional[int] = Field(None, ge=20, le=500)
    margin: Optional[int] = Field(None, ge=0, le=50)
    is_compact: Optional[bool] = None
    is_draggable: Optional[bool] = None
    is_resizable: Optional[bool] = None

    theme: Optional[str] = Field(None, max_length=50)
    background_color: Optional[str] = Field(None, max_length=20)
    custom_css: Optional[str] = None

    refresh_frequency: Optional[RefreshFrequency] = None
    auto_refresh: Optional[bool] = None

    global_filters: Optional[dict[str, Any]] = None
    default_filters: Optional[dict[str, Any]] = None
    default_date_range: Optional[str] = Field(None, max_length=50)

    is_shared: Optional[bool] = None
    is_public: Optional[bool] = None
    is_template: Optional[bool] = None
    is_default: Optional[bool] = None
    is_home: Optional[bool] = None
    is_active: Optional[bool] = None

    tags: Optional[list[str]] = None
    category: Optional[str] = Field(None, max_length=100)


class DashboardResponse(DashboardBase):
    """Reponse dashboard complete."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    owner_id: UUID

    layout_config: Optional[dict[str, Any]]

    is_shared: bool
    is_public: bool
    is_template: bool
    is_default: bool
    is_home: bool
    is_pinned: bool
    display_order: int

    view_count: int
    last_viewed_at: Optional[datetime]

    is_active: bool
    version: int

    widgets: list[WidgetResponse] = []

    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]


class DashboardListItem(BaseModel):
    """Element de liste dashboards."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: Optional[str]
    icon: Optional[str]
    color: Optional[str]
    dashboard_type: DashboardType
    owner_id: UUID
    is_shared: bool
    is_public: bool
    is_template: bool
    is_favorite: bool = False
    view_count: int
    widget_count: int = 0
    tags: Optional[list[str]]
    category: Optional[str]
    created_at: datetime
    last_viewed_at: Optional[datetime]


class DashboardStats(BaseModel):
    """Statistiques d'un dashboard."""
    dashboard_id: UUID
    dashboard_name: str
    widget_count: int
    view_count: int
    unique_viewers: int
    avg_session_duration_seconds: int
    last_viewed_at: Optional[datetime]
    most_used_widgets: list[dict[str, Any]]
    export_count: int
    alert_count: int
    share_count: int


# ============================================================================
# DATA SOURCE SCHEMAS
# ============================================================================

class DataSourceBase(BaseModel):
    """Base pour sources de donnees."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    source_type: DataSourceType

    # Configuration
    module: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    endpoint: Optional[str] = Field(None, max_length=500)
    connection_config: Optional[dict[str, Any]] = None

    # Schema
    schema_definition: Optional[dict[str, Any]] = None
    available_fields: Optional[list[dict[str, Any]]] = None
    available_aggregations: Optional[list[str]] = None
    available_filters: Optional[list[dict[str, Any]]] = None

    # Requete par defaut
    default_query: Optional[dict[str, Any]] = None
    default_filters: Optional[dict[str, Any]] = None
    default_sort: Optional[dict[str, Any]] = None
    default_limit: int = Field(default=1000, ge=1, le=100000)

    # Cache
    cache_enabled: bool = True
    cache_ttl_seconds: int = Field(default=300, ge=0)

    # Rafraichissement
    refresh_frequency: RefreshFrequency = RefreshFrequency.ON_DEMAND


class DataSourceCreate(DataSourceBase):
    """Creation d'une source de donnees."""
    is_encrypted: bool = True
    allowed_roles: Optional[list[str]] = None
    row_level_security: Optional[dict[str, Any]] = None


class DataSourceUpdate(BaseModel):
    """Mise a jour d'une source de donnees."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    connection_config: Optional[dict[str, Any]] = None
    schema_definition: Optional[dict[str, Any]] = None
    available_fields: Optional[list[dict[str, Any]]] = None
    default_query: Optional[dict[str, Any]] = None
    default_filters: Optional[dict[str, Any]] = None
    default_limit: Optional[int] = Field(None, ge=1, le=100000)
    cache_enabled: Optional[bool] = None
    cache_ttl_seconds: Optional[int] = Field(None, ge=0)
    refresh_frequency: Optional[RefreshFrequency] = None
    allowed_roles: Optional[list[str]] = None
    row_level_security: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class DataSourceResponse(DataSourceBase):
    """Reponse source de donnees."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str

    last_synced_at: Optional[datetime]
    sync_status: Optional[str]
    sync_error: Optional[str]

    is_encrypted: bool
    allowed_roles: Optional[list[str]]
    row_level_security: Optional[dict[str, Any]]

    is_active: bool
    is_system: bool
    version: int

    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]


class DataQueryBase(BaseModel):
    """Base pour requetes."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    query_type: str = Field(default="builder", pattern="^(builder|sql|api|aggregate)$")

    query_config: Optional[dict[str, Any]] = None
    raw_query: Optional[str] = None
    api_config: Optional[dict[str, Any]] = None
    parameters: Optional[list[dict[str, Any]]] = None
    transformations: Optional[list[dict[str, Any]]] = None

    cache_enabled: bool = False
    cache_ttl_seconds: int = Field(default=300, ge=0)


class DataQueryCreate(DataQueryBase):
    """Creation d'une requete."""
    data_source_id: Optional[UUID] = None
    allowed_roles: Optional[list[str]] = None
    is_public: bool = False


class DataQueryUpdate(BaseModel):
    """Mise a jour d'une requete."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    data_source_id: Optional[UUID] = None
    query_type: Optional[str] = Field(None, pattern="^(builder|sql|api|aggregate)$")
    query_config: Optional[dict[str, Any]] = None
    raw_query: Optional[str] = None
    api_config: Optional[dict[str, Any]] = None
    parameters: Optional[list[dict[str, Any]]] = None
    transformations: Optional[list[dict[str, Any]]] = None
    cache_enabled: Optional[bool] = None
    cache_ttl_seconds: Optional[int] = Field(None, ge=0)
    allowed_roles: Optional[list[str]] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None


class DataQueryResponse(DataQueryBase):
    """Reponse requete."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    data_source_id: Optional[UUID]

    result_columns: Optional[list[dict[str, str]]]
    sample_data: Optional[list[dict[str, Any]]]

    last_executed_at: Optional[datetime]
    last_execution_time_ms: Optional[int]
    avg_execution_time_ms: Optional[int]
    execution_count: int

    allowed_roles: Optional[list[str]]
    is_active: bool
    is_public: bool

    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]


class DataQueryExecuteRequest(BaseModel):
    """Execution de requete."""
    parameters: Optional[dict[str, Any]] = None
    filters: Optional[dict[str, Any]] = None
    sort: Optional[dict[str, Any]] = None
    limit: int = Field(default=1000, ge=1, le=100000)
    offset: int = Field(default=0, ge=0)
    use_cache: bool = True


class DataQueryExecuteResponse(BaseModel):
    """Resultat execution requete."""
    query_id: UUID
    columns: list[dict[str, str]]
    rows: list[dict[str, Any]]
    total_rows: int
    execution_time_ms: int
    cache_hit: bool
    executed_at: datetime


# ============================================================================
# SHARE SCHEMAS
# ============================================================================

class DashboardShareCreate(BaseModel):
    """Creation partage."""
    share_type: str = Field(..., pattern="^(user|role|team|link)$")
    shared_with_user_id: Optional[UUID] = None
    shared_with_role: Optional[str] = Field(None, max_length=100)
    shared_with_team_id: Optional[UUID] = None
    permission: SharePermission = SharePermission.VIEW
    can_export: bool = True
    can_share: bool = False
    notify_on_share: bool = True
    notify_on_update: bool = False
    message: Optional[str] = None
    expires_at: Optional[datetime] = None

    # Pour lien
    link_password: Optional[str] = Field(None, min_length=8)
    link_max_access: Optional[int] = Field(None, ge=1)


class DashboardShareUpdate(BaseModel):
    """Mise a jour partage."""
    permission: Optional[SharePermission] = None
    can_export: Optional[bool] = None
    can_share: Optional[bool] = None
    notify_on_update: Optional[bool] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class DashboardShareResponse(BaseModel):
    """Reponse partage."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dashboard_id: UUID
    share_type: str
    shared_with_user_id: Optional[UUID]
    shared_with_role: Optional[str]
    shared_with_team_id: Optional[UUID]
    share_link: Optional[str]
    link_expires_at: Optional[datetime]
    link_access_count: int
    permission: SharePermission
    can_export: bool
    can_share: bool
    shared_by: UUID
    message: Optional[str]
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    last_accessed_at: Optional[datetime]


# ============================================================================
# FAVORITE SCHEMAS
# ============================================================================

class DashboardFavoriteCreate(BaseModel):
    """Creation favori."""
    dashboard_id: UUID
    folder: Optional[str] = Field(None, max_length=100)
    is_pinned: bool = False
    custom_name: Optional[str] = Field(None, max_length=200)
    custom_icon: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class DashboardFavoriteUpdate(BaseModel):
    """Mise a jour favori."""
    folder: Optional[str] = Field(None, max_length=100)
    display_order: Optional[int] = Field(None, ge=0)
    is_pinned: Optional[bool] = None
    custom_name: Optional[str] = Field(None, max_length=200)
    custom_icon: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class DashboardFavoriteResponse(BaseModel):
    """Reponse favori."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    dashboard_id: UUID
    folder: Optional[str]
    display_order: int
    is_pinned: bool
    custom_name: Optional[str]
    custom_icon: Optional[str]
    notes: Optional[str]
    created_at: datetime

    # Dashboard info
    dashboard: Optional[DashboardListItem] = None


# ============================================================================
# ALERT SCHEMAS
# ============================================================================

class AlertRuleBase(BaseModel):
    """Base pour regles d'alerte."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    severity: AlertSeverity = AlertSeverity.WARNING

    metric_field: str = Field(..., max_length=200)
    operator: AlertOperator
    threshold_value: Optional[Decimal] = None
    threshold_value_2: Optional[Decimal] = None
    comparison_period: Optional[str] = Field(None, max_length=50)
    complex_condition: Optional[dict[str, Any]] = None

    check_frequency: RefreshFrequency = RefreshFrequency.MINUTE_15
    notification_channels: Optional[list[str]] = None
    recipients: Optional[list[dict[str, Any]]] = None
    cooldown_minutes: int = Field(default=60, ge=1, le=1440)
    max_triggers_per_day: Optional[int] = Field(None, ge=1)

    message_template: Optional[str] = None
    include_data: bool = True
    include_link: bool = True

    auto_resolve: bool = False
    auto_resolve_condition: Optional[dict[str, Any]] = None
    auto_actions: Optional[list[dict[str, Any]]] = None


class AlertRuleCreate(AlertRuleBase):
    """Creation regle d'alerte."""
    widget_id: Optional[UUID] = None
    dashboard_id: Optional[UUID] = None
    is_enabled: bool = True


class AlertRuleUpdate(BaseModel):
    """Mise a jour regle d'alerte."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    severity: Optional[AlertSeverity] = None
    metric_field: Optional[str] = Field(None, max_length=200)
    operator: Optional[AlertOperator] = None
    threshold_value: Optional[Decimal] = None
    threshold_value_2: Optional[Decimal] = None
    comparison_period: Optional[str] = Field(None, max_length=50)
    complex_condition: Optional[dict[str, Any]] = None
    check_frequency: Optional[RefreshFrequency] = None
    notification_channels: Optional[list[str]] = None
    recipients: Optional[list[dict[str, Any]]] = None
    cooldown_minutes: Optional[int] = Field(None, ge=1, le=1440)
    max_triggers_per_day: Optional[int] = Field(None, ge=1)
    message_template: Optional[str] = None
    include_data: Optional[bool] = None
    include_link: Optional[bool] = None
    auto_resolve: Optional[bool] = None
    auto_resolve_condition: Optional[dict[str, Any]] = None
    auto_actions: Optional[list[dict[str, Any]]] = None
    is_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class AlertRuleResponse(AlertRuleBase):
    """Reponse regle d'alerte."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    widget_id: Optional[UUID]
    dashboard_id: Optional[UUID]

    last_checked_at: Optional[datetime]
    last_triggered_at: Optional[datetime]
    trigger_count: int

    is_enabled: bool
    is_active: bool

    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]


class AlertResponse(BaseModel):
    """Reponse alerte declenchee."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    rule_id: Optional[UUID]
    widget_id: Optional[UUID]
    dashboard_id: Optional[UUID]

    title: str
    message: str
    severity: AlertSeverity
    status: AlertStatus

    metric_field: Optional[str]
    current_value: Optional[Decimal]
    threshold_value: Optional[Decimal]
    previous_value: Optional[Decimal]
    change_percentage: Optional[Decimal]

    context_data: Optional[dict[str, Any]]
    link: Optional[str]
    screenshot_url: Optional[str]

    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[UUID]
    acknowledged_notes: Optional[str]

    resolved_at: Optional[datetime]
    resolved_by: Optional[UUID]
    resolution_notes: Optional[str]
    resolution_type: Optional[str]

    snoozed_until: Optional[datetime]

    notifications_sent: Optional[list[dict[str, Any]]]
    triggered_at: datetime
    created_at: datetime


class AlertAcknowledge(BaseModel):
    """Acquittement alerte."""
    notes: Optional[str] = None


class AlertResolve(BaseModel):
    """Resolution alerte."""
    resolution_notes: str = Field(..., min_length=1)
    resolution_type: str = Field(default="manual", pattern="^(manual|auto|timeout|false_positive)$")


class AlertSnooze(BaseModel):
    """Mise en pause alerte."""
    snooze_until: datetime
    reason: Optional[str] = None


class AlertListItem(BaseModel):
    """Element liste alertes."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    severity: AlertSeverity
    status: AlertStatus
    widget_id: Optional[UUID]
    dashboard_id: Optional[UUID]
    current_value: Optional[Decimal]
    threshold_value: Optional[Decimal]
    triggered_at: datetime


class AlertSummary(BaseModel):
    """Resume des alertes."""
    total: int
    active: int
    acknowledged: int
    resolved: int
    snoozed: int
    by_severity: dict[str, int]
    recent: list[AlertListItem]


# ============================================================================
# EXPORT SCHEMAS
# ============================================================================

class ExportRequest(BaseModel):
    """Demande d'export."""
    export_type: str = Field(..., pattern="^(dashboard|widget|data)$")
    export_format: ExportFormat

    # Configuration
    export_config: Optional[dict[str, Any]] = None
    # {page_size: "A4", orientation: "landscape", include_header: true, quality: "high"}

    # Filtres a appliquer
    filters: Optional[dict[str, Any]] = None
    date_range: Optional[dict[str, Any]] = None

    # Nom fichier
    filename: Optional[str] = Field(None, max_length=200)


class ExportResponse(BaseModel):
    """Reponse export."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    export_type: str
    export_format: ExportFormat
    status: ExportStatus

    file_name: Optional[str]
    file_url: Optional[str]
    file_size: Optional[int]
    file_expires_at: Optional[datetime]

    duration_ms: Optional[int]
    error_message: Optional[str]

    created_at: datetime
    completed_at: Optional[datetime]


# ============================================================================
# SCHEDULED REPORT SCHEMAS
# ============================================================================

class ScheduledReportBase(BaseModel):
    """Base pour rapport planifie."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None

    cron_expression: Optional[str] = Field(None, max_length=100)
    frequency: Optional[RefreshFrequency] = None
    timezone: str = Field(default="Europe/Paris", max_length=50)

    export_format: ExportFormat = ExportFormat.PDF
    export_config: Optional[dict[str, Any]] = None

    filters: Optional[dict[str, Any]] = None
    date_range_type: Optional[str] = Field(None, max_length=50)

    distribution_method: str = Field(default="email", pattern="^(email|storage|webhook)$")
    recipients: Optional[list[dict[str, Any]]] = None
    email_subject: Optional[str] = Field(None, max_length=500)
    email_body: Optional[str] = None
    webhook_url: Optional[str] = Field(None, max_length=500)
    storage_path: Optional[str] = Field(None, max_length=500)

    include_summary: bool = True
    attach_data: bool = False


class ScheduledReportCreate(ScheduledReportBase):
    """Creation rapport planifie."""
    dashboard_id: UUID
    is_enabled: bool = True


class ScheduledReportUpdate(BaseModel):
    """Mise a jour rapport planifie."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    cron_expression: Optional[str] = Field(None, max_length=100)
    frequency: Optional[RefreshFrequency] = None
    timezone: Optional[str] = Field(None, max_length=50)
    export_format: Optional[ExportFormat] = None
    export_config: Optional[dict[str, Any]] = None
    filters: Optional[dict[str, Any]] = None
    date_range_type: Optional[str] = Field(None, max_length=50)
    distribution_method: Optional[str] = Field(None, pattern="^(email|storage|webhook)$")
    recipients: Optional[list[dict[str, Any]]] = None
    email_subject: Optional[str] = Field(None, max_length=500)
    email_body: Optional[str] = None
    webhook_url: Optional[str] = Field(None, max_length=500)
    storage_path: Optional[str] = Field(None, max_length=500)
    include_summary: Optional[bool] = None
    attach_data: Optional[bool] = None
    is_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class ScheduledReportResponse(ScheduledReportBase):
    """Reponse rapport planifie."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    dashboard_id: UUID

    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    last_status: Optional[ExportStatus]
    last_error: Optional[str]
    run_count: int

    is_enabled: bool
    is_active: bool

    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]


# ============================================================================
# USER PREFERENCE SCHEMAS
# ============================================================================

class UserPreferenceUpdate(BaseModel):
    """Mise a jour preferences utilisateur."""
    default_dashboard_id: Optional[UUID] = None
    home_dashboard_id: Optional[UUID] = None
    theme: Optional[str] = Field(None, pattern="^(light|dark|system)$")
    language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    date_format: Optional[str] = Field(None, max_length=50)
    number_format: Optional[str] = Field(None, max_length=50)
    default_date_range: Optional[str] = Field(None, max_length=50)
    auto_refresh_enabled: Optional[bool] = None
    compact_mode: Optional[bool] = None
    show_tooltips: Optional[bool] = None
    animation_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    notification_frequency: Optional[str] = Field(None, max_length=50)


class UserPreferenceResponse(BaseModel):
    """Reponse preferences utilisateur."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    default_dashboard_id: Optional[UUID]
    home_dashboard_id: Optional[UUID]
    theme: str
    language: str
    timezone: str
    date_format: str
    number_format: str
    default_date_range: str
    auto_refresh_enabled: bool
    compact_mode: bool
    show_tooltips: bool
    animation_enabled: bool
    email_notifications: bool
    push_notifications: bool
    notification_frequency: str
    recent_dashboards: Optional[list[UUID]]
    saved_filters: Optional[dict[str, Any]]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# TEMPLATE SCHEMAS
# ============================================================================

class TemplateBase(BaseModel):
    """Base pour templates."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    preview_image: Optional[str] = Field(None, max_length=500)
    dashboard_type: DashboardType = DashboardType.CUSTOM

    layout_config: dict[str, Any]
    widgets_config: list[dict[str, Any]]
    theme_config: Optional[dict[str, Any]] = None
    filters_config: Optional[dict[str, Any]] = None

    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[list[str]] = None
    target_roles: Optional[list[str]] = None


class TemplateCreate(TemplateBase):
    """Creation template."""
    is_public: bool = False


class TemplateUpdate(BaseModel):
    """Mise a jour template."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    preview_image: Optional[str] = Field(None, max_length=500)
    dashboard_type: Optional[DashboardType] = None
    layout_config: Optional[dict[str, Any]] = None
    widgets_config: Optional[list[dict[str, Any]]] = None
    theme_config: Optional[dict[str, Any]] = None
    filters_config: Optional[dict[str, Any]] = None
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[list[str]] = None
    target_roles: Optional[list[str]] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None


class TemplateResponse(TemplateBase):
    """Reponse template."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str

    usage_count: int
    rating: Optional[Decimal]
    rating_count: int

    is_public: bool
    is_system: bool
    is_active: bool
    version: int

    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]


class TemplateListItem(BaseModel):
    """Element liste templates."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: Optional[str]
    icon: Optional[str]
    preview_image: Optional[str]
    dashboard_type: DashboardType
    category: Optional[str]
    tags: Optional[list[str]]
    usage_count: int
    rating: Optional[Decimal]
    is_public: bool
    is_system: bool


# ============================================================================
# OVERVIEW SCHEMAS
# ============================================================================

class DashboardOverview(BaseModel):
    """Vue d'ensemble module dashboards."""
    total_dashboards: int
    my_dashboards: int
    shared_with_me: int
    public_dashboards: int
    templates: int

    recent_dashboards: list[DashboardListItem]
    favorite_dashboards: list[DashboardFavoriteResponse]
    pinned_dashboards: list[DashboardListItem]

    alerts: AlertSummary

    stats: dict[str, Any]
    # {views_today, views_week, exports_today, most_viewed}
