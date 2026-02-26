"""
AZALSCORE ERP - Module DASHBOARDS
==================================
Tableaux de bord personnalisables et KPIs.

Fonctionnalites:
- Dashboards personnalisables par utilisateur
- Widgets configurables (KPI, graphiques, listes)
- Sources de donnees multiples
- Filtres globaux (periode, entite)
- Mise en page drag & drop
- Partage de dashboards
- Rafraichissement automatique
- Export PDF/image
- Dashboards par role
- Alertes sur seuils
- Favoris et accueil
"""

# Enumerations
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

# Models
from .models import (
    Dashboard,
    DashboardWidget,
    DataSource,
    DataQuery,
    DashboardShare,
    DashboardFavorite,
    DashboardAlertRule,
    DashboardAlert,
    DashboardExport,
    ScheduledReport,
    UserDashboardPreference,
    DashboardTemplate,
)

# Schemas
from .schemas import (
    # Dashboard schemas
    DashboardCreate,
    DashboardUpdate,
    DashboardResponse,
    DashboardListItem,
    DashboardFilters,
    DashboardOverview,
    DashboardStats,
    # Widget schemas
    WidgetCreate,
    WidgetUpdate,
    WidgetResponse,
    WidgetFilters,
    WidgetLayoutUpdate,
    WidgetLayoutItem,
    WidgetDataResponse,
    # DataSource schemas
    DataSourceCreate,
    DataSourceUpdate,
    DataSourceResponse,
    # DataQuery schemas
    DataQueryCreate,
    DataQueryUpdate,
    DataQueryResponse,
    DataQueryExecuteRequest,
    DataQueryExecuteResponse,
    # Share schemas
    DashboardShareCreate,
    DashboardShareUpdate,
    DashboardShareResponse,
    # Favorite schemas
    DashboardFavoriteCreate,
    DashboardFavoriteUpdate,
    DashboardFavoriteResponse,
    # AlertRule schemas
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleResponse,
    # Alert schemas
    AlertResponse,
    AlertAcknowledge,
    AlertResolve,
    AlertSnooze,
    AlertListItem,
    AlertSummary,
    # Export schemas
    ExportRequest,
    ExportResponse,
    # ScheduledReport schemas
    ScheduledReportCreate,
    ScheduledReportUpdate,
    ScheduledReportResponse,
    # UserPreference schemas
    UserPreferenceUpdate,
    UserPreferenceResponse,
    # Template schemas
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListItem,
)

# Exceptions
from .exceptions import (
    DashboardException,
    DashboardNotFoundError,
    DashboardAccessDeniedError,
    DashboardCodeExistsError,
    DashboardValidationError,
    DashboardLimitExceededError,
    WidgetNotFoundError,
    WidgetValidationError,
    WidgetDataError,
    WidgetLayoutError,
    DataSourceNotFoundError,
    DataSourceConnectionError,
    DataSourceCodeExistsError,
    DataQueryNotFoundError,
    DataQueryExecutionError,
    DataQueryCodeExistsError,
    ShareNotFoundError,
    ShareInvalidLinkError,
    SharePermissionError,
    AlertRuleNotFoundError,
    AlertRuleCodeExistsError,
    AlertNotFoundError,
    AlertAlreadyResolvedError,
    ExportNotFoundError,
    ExportFailedError,
    ExportExpiredError,
    ExportFormatNotSupportedError,
    ScheduledReportNotFoundError,
    ScheduledReportCodeExistsError,
    InvalidCronExpressionError,
    TemplateNotFoundError,
    TemplateCodeExistsError,
    FavoriteNotFoundError,
    FavoriteAlreadyExistsError,
)

# Repositories
from .repository import (
    DashboardRepository,
    WidgetRepository,
    DataSourceRepository,
    DataQueryRepository,
    ShareRepository,
    FavoriteRepository,
    AlertRuleRepository,
    AlertRepository,
    ExportRepository,
    ScheduledReportRepository,
    UserPreferenceRepository,
    TemplateRepository,
)

# Service
from .service import DashboardService

# Router
from .router import router

__all__ = [
    # Enumerations
    "DashboardType",
    "WidgetType",
    "ChartType",
    "DataSourceType",
    "RefreshFrequency",
    "AlertSeverity",
    "AlertStatus",
    "AlertOperator",
    "SharePermission",
    "ExportFormat",
    "ExportStatus",
    # Models
    "Dashboard",
    "DashboardWidget",
    "DataSource",
    "DataQuery",
    "DashboardShare",
    "DashboardFavorite",
    "DashboardAlertRule",
    "DashboardAlert",
    "DashboardExport",
    "ScheduledReport",
    "UserDashboardPreference",
    "DashboardTemplate",
    # Schemas
    "DashboardCreate",
    "DashboardUpdate",
    "DashboardResponse",
    "DashboardListItem",
    "DashboardFilters",
    "DashboardOverview",
    "DashboardStats",
    "WidgetCreate",
    "WidgetUpdate",
    "WidgetResponse",
    "WidgetFilters",
    "WidgetLayoutUpdate",
    "WidgetLayoutItem",
    "WidgetDataResponse",
    "DataSourceCreate",
    "DataSourceUpdate",
    "DataSourceResponse",
    "DataQueryCreate",
    "DataQueryUpdate",
    "DataQueryResponse",
    "DataQueryExecuteRequest",
    "DataQueryExecuteResponse",
    "DashboardShareCreate",
    "DashboardShareUpdate",
    "DashboardShareResponse",
    "DashboardFavoriteCreate",
    "DashboardFavoriteUpdate",
    "DashboardFavoriteResponse",
    "AlertRuleCreate",
    "AlertRuleUpdate",
    "AlertRuleResponse",
    "AlertResponse",
    "AlertAcknowledge",
    "AlertResolve",
    "AlertSnooze",
    "AlertListItem",
    "AlertSummary",
    "ExportRequest",
    "ExportResponse",
    "ScheduledReportCreate",
    "ScheduledReportUpdate",
    "ScheduledReportResponse",
    "UserPreferenceUpdate",
    "UserPreferenceResponse",
    "TemplateCreate",
    "TemplateUpdate",
    "TemplateResponse",
    "TemplateListItem",
    # Exceptions
    "DashboardException",
    "DashboardNotFoundError",
    "DashboardAccessDeniedError",
    "DashboardCodeExistsError",
    "DashboardValidationError",
    "DashboardLimitExceededError",
    "WidgetNotFoundError",
    "WidgetValidationError",
    "WidgetDataError",
    "WidgetLayoutError",
    "DataSourceNotFoundError",
    "DataSourceConnectionError",
    "DataSourceCodeExistsError",
    "DataQueryNotFoundError",
    "DataQueryExecutionError",
    "DataQueryCodeExistsError",
    "ShareNotFoundError",
    "ShareInvalidLinkError",
    "SharePermissionError",
    "AlertRuleNotFoundError",
    "AlertRuleCodeExistsError",
    "AlertNotFoundError",
    "AlertAlreadyResolvedError",
    "ExportNotFoundError",
    "ExportFailedError",
    "ExportExpiredError",
    "ExportFormatNotSupportedError",
    "ScheduledReportNotFoundError",
    "ScheduledReportCodeExistsError",
    "InvalidCronExpressionError",
    "TemplateNotFoundError",
    "TemplateCodeExistsError",
    "FavoriteNotFoundError",
    "FavoriteAlreadyExistsError",
    # Repositories
    "DashboardRepository",
    "WidgetRepository",
    "DataSourceRepository",
    "DataQueryRepository",
    "ShareRepository",
    "FavoriteRepository",
    "AlertRuleRepository",
    "AlertRepository",
    "ExportRepository",
    "ScheduledReportRepository",
    "UserPreferenceRepository",
    "TemplateRepository",
    # Service
    "DashboardService",
    # Router
    "router",
]
