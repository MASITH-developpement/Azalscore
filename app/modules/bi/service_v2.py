"""
AZALS - Bi Service (v2 - CRUDRouter Compatible)
====================================================

Service compatible avec BaseService et CRUDRouter.
Migration automatique depuis service.py.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.base_service import BaseService
from app.core.saas_context import Result, SaaSContext

from app.modules.bi.models import (
    Dashboard,
    DashboardWidget,
    WidgetFilter,
    Report,
    ReportSchedule,
    ReportExecution,
    KPIDefinition,
    KPIValue,
    KPITarget,
    Alert,
    AlertRule,
    DataSource,
    DataQuery,
    Bookmark,
    ExportHistory,
)
from app.modules.bi.schemas import (
    AlertBase,
    AlertCreate,
    AlertResponse,
    AlertRuleBase,
    AlertRuleCreate,
    AlertRuleResponse,
    AlertRuleUpdate,
    AlertUpdate,
    BookmarkBase,
    BookmarkCreate,
    BookmarkResponse,
    DashboardBase,
    DashboardCreate,
    DashboardResponse,
    DashboardUpdate,
    DataQueryBase,
    DataQueryCreate,
    DataQueryResponse,
    DataQueryUpdate,
    DataSourceBase,
    DataSourceCreate,
    DataSourceResponse,
    DataSourceUpdate,
    ExportResponse,
    KPIBase,
    KPICreate,
    KPIResponse,
    KPITargetBase,
    KPITargetCreate,
    KPITargetResponse,
    KPIUpdate,
    KPIValueBase,
    KPIValueCreate,
    KPIValueResponse,
    ReportBase,
    ReportCreate,
    ReportExecutionResponse,
    ReportResponse,
    ReportScheduleBase,
    ReportScheduleCreate,
    ReportScheduleResponse,
    ReportUpdate,
    WidgetBase,
    WidgetCreate,
    WidgetFilterBase,
    WidgetFilterCreate,
    WidgetFilterResponse,
    WidgetResponse,
    WidgetUpdate,
)

logger = logging.getLogger(__name__)



class DashboardService(BaseService[Dashboard, Any, Any]):
    """Service CRUD pour dashboard."""

    model = Dashboard

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Dashboard]
    # - get_or_fail(id) -> Result[Dashboard]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Dashboard]
    # - update(id, data) -> Result[Dashboard]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class DashboardWidgetService(BaseService[DashboardWidget, Any, Any]):
    """Service CRUD pour dashboardwidget."""

    model = DashboardWidget

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[DashboardWidget]
    # - get_or_fail(id) -> Result[DashboardWidget]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[DashboardWidget]
    # - update(id, data) -> Result[DashboardWidget]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class WidgetFilterService(BaseService[WidgetFilter, Any, Any]):
    """Service CRUD pour widgetfilter."""

    model = WidgetFilter

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[WidgetFilter]
    # - get_or_fail(id) -> Result[WidgetFilter]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[WidgetFilter]
    # - update(id, data) -> Result[WidgetFilter]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ReportService(BaseService[Report, Any, Any]):
    """Service CRUD pour report."""

    model = Report

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Report]
    # - get_or_fail(id) -> Result[Report]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Report]
    # - update(id, data) -> Result[Report]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ReportScheduleService(BaseService[ReportSchedule, Any, Any]):
    """Service CRUD pour reportschedule."""

    model = ReportSchedule

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ReportSchedule]
    # - get_or_fail(id) -> Result[ReportSchedule]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ReportSchedule]
    # - update(id, data) -> Result[ReportSchedule]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ReportExecutionService(BaseService[ReportExecution, Any, Any]):
    """Service CRUD pour reportexecution."""

    model = ReportExecution

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ReportExecution]
    # - get_or_fail(id) -> Result[ReportExecution]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ReportExecution]
    # - update(id, data) -> Result[ReportExecution]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class KPIDefinitionService(BaseService[KPIDefinition, Any, Any]):
    """Service CRUD pour kpidefinition."""

    model = KPIDefinition

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[KPIDefinition]
    # - get_or_fail(id) -> Result[KPIDefinition]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[KPIDefinition]
    # - update(id, data) -> Result[KPIDefinition]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class KPIValueService(BaseService[KPIValue, Any, Any]):
    """Service CRUD pour kpivalue."""

    model = KPIValue

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[KPIValue]
    # - get_or_fail(id) -> Result[KPIValue]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[KPIValue]
    # - update(id, data) -> Result[KPIValue]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class KPITargetService(BaseService[KPITarget, Any, Any]):
    """Service CRUD pour kpitarget."""

    model = KPITarget

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[KPITarget]
    # - get_or_fail(id) -> Result[KPITarget]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[KPITarget]
    # - update(id, data) -> Result[KPITarget]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class AlertService(BaseService[Alert, Any, Any]):
    """Service CRUD pour alert."""

    model = Alert

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Alert]
    # - get_or_fail(id) -> Result[Alert]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Alert]
    # - update(id, data) -> Result[Alert]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class AlertRuleService(BaseService[AlertRule, Any, Any]):
    """Service CRUD pour alertrule."""

    model = AlertRule

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[AlertRule]
    # - get_or_fail(id) -> Result[AlertRule]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[AlertRule]
    # - update(id, data) -> Result[AlertRule]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class DataSourceService(BaseService[DataSource, Any, Any]):
    """Service CRUD pour datasource."""

    model = DataSource

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[DataSource]
    # - get_or_fail(id) -> Result[DataSource]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[DataSource]
    # - update(id, data) -> Result[DataSource]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class DataQueryService(BaseService[DataQuery, Any, Any]):
    """Service CRUD pour dataquery."""

    model = DataQuery

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[DataQuery]
    # - get_or_fail(id) -> Result[DataQuery]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[DataQuery]
    # - update(id, data) -> Result[DataQuery]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class BookmarkService(BaseService[Bookmark, Any, Any]):
    """Service CRUD pour bookmark."""

    model = Bookmark

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Bookmark]
    # - get_or_fail(id) -> Result[Bookmark]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Bookmark]
    # - update(id, data) -> Result[Bookmark]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ExportHistoryService(BaseService[ExportHistory, Any, Any]):
    """Service CRUD pour exporthistory."""

    model = ExportHistory

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ExportHistory]
    # - get_or_fail(id) -> Result[ExportHistory]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ExportHistory]
    # - update(id, data) -> Result[ExportHistory]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques

