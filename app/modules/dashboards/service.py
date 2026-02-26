"""
AZALSCORE ERP - Module DASHBOARDS
==================================
Service metier principal.

Gere:
- CRUD dashboards et widgets
- Sources de donnees et requetes
- Partage et favoris
- Alertes sur seuils
- Exports PDF/image
- Rapports planifies
"""

from __future__ import annotations

import hashlib
import secrets
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.saas_context import SaaSContext, Result

from .exceptions import (
    DashboardNotFoundError,
    DashboardAccessDeniedError,
    DashboardCodeExistsError,
    DashboardValidationError,
    WidgetNotFoundError,
    WidgetDataError,
    DataSourceNotFoundError,
    DataSourceCodeExistsError,
    DataQueryNotFoundError,
    DataQueryCodeExistsError,
    DataQueryExecutionError,
    ShareNotFoundError,
    ShareInvalidLinkError,
    AlertRuleNotFoundError,
    AlertRuleCodeExistsError,
    AlertNotFoundError,
    AlertAlreadyResolvedError,
    ExportNotFoundError,
    ScheduledReportNotFoundError,
    ScheduledReportCodeExistsError,
    TemplateNotFoundError,
    TemplateCodeExistsError,
    FavoriteNotFoundError,
    FavoriteAlreadyExistsError,
)
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
    DashboardType,
    AlertStatus,
    AlertOperator,
    ExportStatus,
    ExportFormat,
    SharePermission,
)
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
from .schemas import (
    DashboardCreate,
    DashboardUpdate,
    DashboardResponse,
    DashboardListItem,
    DashboardFilters,
    DashboardStats,
    WidgetCreate,
    WidgetUpdate,
    WidgetResponse,
    WidgetLayoutUpdate,
    WidgetDataResponse,
    DataSourceCreate,
    DataSourceUpdate,
    DataSourceResponse,
    DataQueryCreate,
    DataQueryUpdate,
    DataQueryResponse,
    DataQueryExecuteRequest,
    DataQueryExecuteResponse,
    DashboardShareCreate,
    DashboardShareUpdate,
    DashboardShareResponse,
    DashboardFavoriteCreate,
    DashboardFavoriteUpdate,
    DashboardFavoriteResponse,
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleResponse,
    AlertResponse,
    AlertAcknowledge,
    AlertResolve,
    AlertSnooze,
    AlertSummary,
    ExportRequest,
    ExportResponse,
    ScheduledReportCreate,
    ScheduledReportUpdate,
    ScheduledReportResponse,
    UserPreferenceUpdate,
    UserPreferenceResponse,
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListItem,
    DashboardOverview,
)


class DashboardService:
    """Service principal pour gestion des dashboards."""

    def __init__(self, db: Session, context: SaaSContext):
        self.db = db
        self.context = context
        self.tenant_id = context.tenant_id
        self.user_id = context.user_id

        # Repositories
        self._dashboard_repo: Optional[DashboardRepository] = None
        self._widget_repo: Optional[WidgetRepository] = None
        self._datasource_repo: Optional[DataSourceRepository] = None
        self._query_repo: Optional[DataQueryRepository] = None
        self._share_repo: Optional[ShareRepository] = None
        self._favorite_repo: Optional[FavoriteRepository] = None
        self._alert_rule_repo: Optional[AlertRuleRepository] = None
        self._alert_repo: Optional[AlertRepository] = None
        self._export_repo: Optional[ExportRepository] = None
        self._scheduled_repo: Optional[ScheduledReportRepository] = None
        self._pref_repo: Optional[UserPreferenceRepository] = None
        self._template_repo: Optional[TemplateRepository] = None

    # =========================================================================
    # LAZY LOADING REPOSITORIES
    # =========================================================================

    @property
    def dashboard_repo(self) -> DashboardRepository:
        if self._dashboard_repo is None:
            self._dashboard_repo = DashboardRepository(self.db, self.tenant_id)
        return self._dashboard_repo

    @property
    def widget_repo(self) -> WidgetRepository:
        if self._widget_repo is None:
            self._widget_repo = WidgetRepository(self.db, self.tenant_id)
        return self._widget_repo

    @property
    def datasource_repo(self) -> DataSourceRepository:
        if self._datasource_repo is None:
            self._datasource_repo = DataSourceRepository(self.db, self.tenant_id)
        return self._datasource_repo

    @property
    def query_repo(self) -> DataQueryRepository:
        if self._query_repo is None:
            self._query_repo = DataQueryRepository(self.db, self.tenant_id)
        return self._query_repo

    @property
    def share_repo(self) -> ShareRepository:
        if self._share_repo is None:
            self._share_repo = ShareRepository(self.db, self.tenant_id)
        return self._share_repo

    @property
    def favorite_repo(self) -> FavoriteRepository:
        if self._favorite_repo is None:
            self._favorite_repo = FavoriteRepository(self.db, self.tenant_id)
        return self._favorite_repo

    @property
    def alert_rule_repo(self) -> AlertRuleRepository:
        if self._alert_rule_repo is None:
            self._alert_rule_repo = AlertRuleRepository(self.db, self.tenant_id)
        return self._alert_rule_repo

    @property
    def alert_repo(self) -> AlertRepository:
        if self._alert_repo is None:
            self._alert_repo = AlertRepository(self.db, self.tenant_id)
        return self._alert_repo

    @property
    def export_repo(self) -> ExportRepository:
        if self._export_repo is None:
            self._export_repo = ExportRepository(self.db, self.tenant_id)
        return self._export_repo

    @property
    def scheduled_repo(self) -> ScheduledReportRepository:
        if self._scheduled_repo is None:
            self._scheduled_repo = ScheduledReportRepository(self.db, self.tenant_id)
        return self._scheduled_repo

    @property
    def pref_repo(self) -> UserPreferenceRepository:
        if self._pref_repo is None:
            self._pref_repo = UserPreferenceRepository(self.db, self.tenant_id)
        return self._pref_repo

    @property
    def template_repo(self) -> TemplateRepository:
        if self._template_repo is None:
            self._template_repo = TemplateRepository(self.db, self.tenant_id)
        return self._template_repo

    # =========================================================================
    # DASHBOARD CRUD
    # =========================================================================

    def get_dashboard(self, dashboard_id: UUID, check_access: bool = True) -> Result[Dashboard]:
        """Recupere un dashboard par ID."""
        dashboard = self.dashboard_repo.get_by_id(dashboard_id)
        if not dashboard:
            return Result.fail(f"Dashboard non trouve: {dashboard_id}", "NOT_FOUND")

        if check_access and not self._can_access_dashboard(dashboard, SharePermission.VIEW):
            return Result.fail("Acces refuse", "FORBIDDEN")

        # Incrementer les vues
        self.dashboard_repo.increment_view_count(dashboard, self.user_id)

        # Ajouter aux recents
        self.pref_repo.add_recent_dashboard(self.user_id, dashboard_id)

        return Result.ok(dashboard)

    def get_dashboard_by_code(self, code: str) -> Result[Dashboard]:
        """Recupere un dashboard par code."""
        dashboard = self.dashboard_repo.get_by_code(code)
        if not dashboard:
            return Result.fail(f"Dashboard non trouve: {code}", "NOT_FOUND")

        if not self._can_access_dashboard(dashboard, SharePermission.VIEW):
            return Result.fail("Acces refuse", "FORBIDDEN")

        return Result.ok(dashboard)

    def list_dashboards(
        self,
        filters: Optional[DashboardFilters] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Result[dict[str, Any]]:
        """Liste les dashboards avec filtres."""
        dashboards, total = self.dashboard_repo.list(
            filters=filters,
            user_id=self.user_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir
        )

        # Enrichir avec info favori
        items = []
        for d in dashboards:
            item = DashboardListItem(
                id=d.id,
                code=d.code,
                name=d.name,
                description=d.description,
                icon=d.icon,
                color=d.color,
                dashboard_type=d.dashboard_type,
                owner_id=d.owner_id,
                is_shared=d.is_shared,
                is_public=d.is_public,
                is_template=d.is_template,
                is_favorite=self.favorite_repo.is_favorite(self.user_id, d.id),
                view_count=d.view_count,
                widget_count=len(d.widgets) if d.widgets else 0,
                tags=d.tags,
                category=d.category,
                created_at=d.created_at,
                last_viewed_at=d.last_viewed_at
            )
            items.append(item.model_dump())

        return Result.ok({
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        })

    def get_my_dashboards(self) -> Result[list[Dashboard]]:
        """Recupere les dashboards de l'utilisateur courant."""
        dashboards = self.dashboard_repo.get_user_dashboards(self.user_id)
        return Result.ok(dashboards)

    def get_recent_dashboards(self, limit: int = 5) -> Result[list[Dashboard]]:
        """Recupere les dashboards recemment vus."""
        dashboards = self.dashboard_repo.get_recent(self.user_id, limit)
        return Result.ok(dashboards)

    def get_default_dashboard(self) -> Result[Optional[Dashboard]]:
        """Recupere le dashboard par defaut."""
        dashboard = self.dashboard_repo.get_default(self.user_id)
        return Result.ok(dashboard)

    def get_home_dashboard(self) -> Result[Optional[Dashboard]]:
        """Recupere le dashboard accueil."""
        dashboard = self.dashboard_repo.get_home(self.user_id)
        return Result.ok(dashboard)

    def create_dashboard(self, data: DashboardCreate) -> Result[Dashboard]:
        """Cree un nouveau dashboard."""
        # Valider code unique
        if self.dashboard_repo.code_exists(data.code):
            return Result.fail(f"Code deja utilise: {data.code}", "CONFLICT")

        # Depuis template ?
        create_data = data.model_dump(exclude_unset=True, exclude={"template_id"})

        if data.template_id:
            template = self.template_repo.get_by_id(data.template_id)
            if template:
                create_data["layout_config"] = template.layout_config
                create_data["theme"] = template.theme_config.get("theme", "default") if template.theme_config else "default"
                create_data["global_filters"] = template.filters_config

                # Widgets depuis template
                if template.widgets_config:
                    create_data["widgets"] = template.widgets_config

                self.template_repo.increment_usage(template)

        # Creer
        dashboard = self.dashboard_repo.create(create_data, created_by=self.user_id)

        return Result.ok(dashboard)

    def update_dashboard(self, dashboard_id: UUID, data: DashboardUpdate) -> Result[Dashboard]:
        """Met a jour un dashboard."""
        dashboard = self.dashboard_repo.get_by_id(dashboard_id)
        if not dashboard:
            return Result.fail(f"Dashboard non trouve: {dashboard_id}", "NOT_FOUND")

        if not self._can_access_dashboard(dashboard, SharePermission.EDIT):
            return Result.fail("Acces refuse", "FORBIDDEN")

        update_data = data.model_dump(exclude_unset=True)
        dashboard = self.dashboard_repo.update(dashboard, update_data, self.user_id)

        return Result.ok(dashboard)

    def delete_dashboard(self, dashboard_id: UUID, hard: bool = False) -> Result[bool]:
        """Supprime un dashboard."""
        dashboard = self.dashboard_repo.get_by_id(dashboard_id, load_widgets=False)
        if not dashboard:
            return Result.fail(f"Dashboard non trouve: {dashboard_id}", "NOT_FOUND")

        if not self._can_access_dashboard(dashboard, SharePermission.MANAGE):
            return Result.fail("Acces refuse", "FORBIDDEN")

        if hard:
            self.dashboard_repo.hard_delete(dashboard)
        else:
            self.dashboard_repo.soft_delete(dashboard, self.user_id)

        return Result.ok(True)

    def restore_dashboard(self, dashboard_id: UUID) -> Result[Dashboard]:
        """Restaure un dashboard supprime."""
        repo = DashboardRepository(self.db, self.tenant_id, include_deleted=True)
        dashboard = repo.get_by_id(dashboard_id, load_widgets=False)
        if not dashboard:
            return Result.fail(f"Dashboard non trouve: {dashboard_id}", "NOT_FOUND")

        if not dashboard.deleted_at:
            return Result.fail("Dashboard non supprime", "INVALID")

        dashboard = repo.restore(dashboard)
        return Result.ok(dashboard)

    def duplicate_dashboard(
        self,
        dashboard_id: UUID,
        new_code: str,
        new_name: str
    ) -> Result[Dashboard]:
        """Duplique un dashboard."""
        dashboard = self.dashboard_repo.get_by_id(dashboard_id)
        if not dashboard:
            return Result.fail(f"Dashboard non trouve: {dashboard_id}", "NOT_FOUND")

        if not self._can_access_dashboard(dashboard, SharePermission.VIEW):
            return Result.fail("Acces refuse", "FORBIDDEN")

        if self.dashboard_repo.code_exists(new_code):
            return Result.fail(f"Code deja utilise: {new_code}", "CONFLICT")

        new_dashboard = self.dashboard_repo.duplicate(
            dashboard, new_code, new_name, self.user_id
        )

        return Result.ok(new_dashboard)

    def get_dashboard_stats(self, dashboard_id: UUID) -> Result[dict[str, Any]]:
        """Recupere les statistiques d'un dashboard."""
        dashboard = self.dashboard_repo.get_by_id(dashboard_id, load_widgets=False)
        if not dashboard:
            return Result.fail(f"Dashboard non trouve: {dashboard_id}", "NOT_FOUND")

        stats = self.dashboard_repo.get_stats(dashboard_id)
        return Result.ok(stats)

    # =========================================================================
    # WIDGET CRUD
    # =========================================================================

    def get_widget(self, widget_id: UUID) -> Result[DashboardWidget]:
        """Recupere un widget par ID."""
        widget = self.widget_repo.get_by_id(widget_id)
        if not widget:
            return Result.fail(f"Widget non trouve: {widget_id}", "NOT_FOUND")

        dashboard = self.dashboard_repo.get_by_id(widget.dashboard_id, load_widgets=False)
        if not self._can_access_dashboard(dashboard, SharePermission.VIEW):
            return Result.fail("Acces refuse", "FORBIDDEN")

        return Result.ok(widget)

    def get_dashboard_widgets(self, dashboard_id: UUID) -> Result[list[DashboardWidget]]:
        """Recupere les widgets d'un dashboard."""
        dashboard = self.dashboard_repo.get_by_id(dashboard_id, load_widgets=False)
        if not dashboard:
            return Result.fail(f"Dashboard non trouve: {dashboard_id}", "NOT_FOUND")

        if not self._can_access_dashboard(dashboard, SharePermission.VIEW):
            return Result.fail("Acces refuse", "FORBIDDEN")

        widgets = self.widget_repo.get_by_dashboard(dashboard_id)
        return Result.ok(widgets)

    def add_widget(self, dashboard_id: UUID, data: WidgetCreate) -> Result[DashboardWidget]:
        """Ajoute un widget a un dashboard."""
        dashboard = self.dashboard_repo.get_by_id(dashboard_id, load_widgets=False)
        if not dashboard:
            return Result.fail(f"Dashboard non trouve: {dashboard_id}", "NOT_FOUND")

        if not self._can_access_dashboard(dashboard, SharePermission.EDIT):
            return Result.fail("Acces refuse", "FORBIDDEN")

        create_data = data.model_dump(exclude_unset=True)
        widget = self.widget_repo.create(dashboard_id, create_data, self.user_id)

        return Result.ok(widget)

    def update_widget(self, widget_id: UUID, data: WidgetUpdate) -> Result[DashboardWidget]:
        """Met a jour un widget."""
        widget = self.widget_repo.get_by_id(widget_id)
        if not widget:
            return Result.fail(f"Widget non trouve: {widget_id}", "NOT_FOUND")

        dashboard = self.dashboard_repo.get_by_id(widget.dashboard_id, load_widgets=False)
        if not self._can_access_dashboard(dashboard, SharePermission.EDIT):
            return Result.fail("Acces refuse", "FORBIDDEN")

        update_data = data.model_dump(exclude_unset=True)
        widget = self.widget_repo.update(widget, update_data)

        return Result.ok(widget)

    def delete_widget(self, widget_id: UUID) -> Result[bool]:
        """Supprime un widget."""
        widget = self.widget_repo.get_by_id(widget_id)
        if not widget:
            return Result.fail(f"Widget non trouve: {widget_id}", "NOT_FOUND")

        dashboard = self.dashboard_repo.get_by_id(widget.dashboard_id, load_widgets=False)
        if not self._can_access_dashboard(dashboard, SharePermission.EDIT):
            return Result.fail("Acces refuse", "FORBIDDEN")

        self.widget_repo.delete(widget)
        return Result.ok(True)

    def update_layout(self, dashboard_id: UUID, data: WidgetLayoutUpdate) -> Result[bool]:
        """Met a jour le layout complet."""
        dashboard = self.dashboard_repo.get_by_id(dashboard_id, load_widgets=False)
        if not dashboard:
            return Result.fail(f"Dashboard non trouve: {dashboard_id}", "NOT_FOUND")

        if not self._can_access_dashboard(dashboard, SharePermission.EDIT):
            return Result.fail("Acces refuse", "FORBIDDEN")

        positions = [
            {
                "widget_id": item.widget_id,
                "position_x": item.position_x,
                "position_y": item.position_y,
                "width": item.width,
                "height": item.height
            }
            for item in data.layout
        ]
        self.widget_repo.update_positions(dashboard_id, positions)

        return Result.ok(True)

    def get_widget_data(self, widget_id: UUID, filters: Optional[dict] = None) -> Result[WidgetDataResponse]:
        """Recupere les donnees d'un widget."""
        widget = self.widget_repo.get_by_id(widget_id)
        if not widget:
            return Result.fail(f"Widget non trouve: {widget_id}", "NOT_FOUND")

        dashboard = self.dashboard_repo.get_by_id(widget.dashboard_id, load_widgets=False)
        if not self._can_access_dashboard(dashboard, SharePermission.VIEW):
            return Result.fail("Acces refuse", "FORBIDDEN")

        start_time = time.time()

        try:
            # Recuperer les donnees selon le type de source
            if widget.static_data:
                data = widget.static_data
                columns = None
                total_rows = len(data) if isinstance(data, list) else 1
            elif widget.data_source_id:
                # Executer la requete
                data, columns, total_rows = self._fetch_widget_data(widget, filters)
            else:
                data = []
                columns = None
                total_rows = 0

            execution_time = int((time.time() - start_time) * 1000)

            return Result.ok(WidgetDataResponse(
                widget_id=widget_id,
                data=data,
                columns=columns,
                total_rows=total_rows,
                last_updated=datetime.utcnow(),
                cache_hit=False,
                execution_time_ms=execution_time
            ))

        except Exception as e:
            return Result.fail(f"Erreur recuperation donnees: {str(e)}", "DATA_ERROR")

    def refresh_widget(self, widget_id: UUID) -> Result[WidgetDataResponse]:
        """Force le rafraichissement d'un widget."""
        return self.get_widget_data(widget_id, filters=None)

    def _fetch_widget_data(
        self,
        widget: DashboardWidget,
        filters: Optional[dict] = None
    ) -> tuple[Any, Optional[list], int]:
        """Recupere les donnees d'un widget depuis sa source."""
        # TODO: Implementer la recuperation des donnees
        # selon le type de source (module interne, API, SQL, etc.)
        return [], None, 0

    # =========================================================================
    # DATA SOURCES
    # =========================================================================

    def create_data_source(self, data: DataSourceCreate) -> Result[DataSource]:
        """Cree une source de donnees."""
        if self.datasource_repo.code_exists(data.code):
            return Result.fail(f"Code deja utilise: {data.code}", "CONFLICT")

        create_data = data.model_dump(exclude_unset=True)
        source = self.datasource_repo.create(create_data, self.user_id)

        return Result.ok(source)

    def get_data_source(self, source_id: UUID) -> Result[DataSource]:
        """Recupere une source de donnees."""
        source = self.datasource_repo.get_by_id(source_id)
        if not source:
            return Result.fail(f"Source non trouvee: {source_id}", "NOT_FOUND")
        return Result.ok(source)

    def list_data_sources(
        self,
        source_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Result[dict[str, Any]]:
        """Liste les sources de donnees."""
        sources, total = self.datasource_repo.list(
            source_type=source_type,
            is_active=True,
            page=page,
            page_size=page_size
        )

        return Result.ok({
            "items": [DataSourceResponse.model_validate(s).model_dump() for s in sources],
            "total": total,
            "page": page,
            "page_size": page_size
        })

    def update_data_source(self, source_id: UUID, data: DataSourceUpdate) -> Result[DataSource]:
        """Met a jour une source de donnees."""
        source = self.datasource_repo.get_by_id(source_id)
        if not source:
            return Result.fail(f"Source non trouvee: {source_id}", "NOT_FOUND")

        update_data = data.model_dump(exclude_unset=True)
        source = self.datasource_repo.update(source, update_data, self.user_id)

        return Result.ok(source)

    def delete_data_source(self, source_id: UUID) -> Result[bool]:
        """Supprime une source de donnees."""
        source = self.datasource_repo.get_by_id(source_id)
        if not source:
            return Result.fail(f"Source non trouvee: {source_id}", "NOT_FOUND")

        self.datasource_repo.soft_delete(source, self.user_id)
        return Result.ok(True)

    def test_data_source_connection(self, source_id: UUID) -> Result[dict[str, Any]]:
        """Teste la connexion a une source de donnees."""
        source = self.datasource_repo.get_by_id(source_id)
        if not source:
            return Result.fail(f"Source non trouvee: {source_id}", "NOT_FOUND")

        # TODO: Implementer le test de connexion
        return Result.ok({"status": "ok", "message": "Connexion reussie"})

    def sync_data_source(self, source_id: UUID) -> Result[dict[str, Any]]:
        """Synchronise une source de donnees."""
        source = self.datasource_repo.get_by_id(source_id)
        if not source:
            return Result.fail(f"Source non trouvee: {source_id}", "NOT_FOUND")

        # TODO: Implementer la synchronisation
        self.datasource_repo.update(source, {
            "last_synced_at": datetime.utcnow(),
            "sync_status": "success"
        }, self.user_id)

        return Result.ok({"status": "ok", "synced_at": datetime.utcnow().isoformat()})

    # =========================================================================
    # DATA QUERIES
    # =========================================================================

    def create_data_query(self, data: DataQueryCreate) -> Result[DataQuery]:
        """Cree une requete de donnees."""
        if self.query_repo.code_exists(data.code):
            return Result.fail(f"Code deja utilise: {data.code}", "CONFLICT")

        create_data = data.model_dump(exclude_unset=True)
        query = self.query_repo.create(create_data, self.user_id)

        return Result.ok(query)

    def get_data_query(self, query_id: UUID) -> Result[DataQuery]:
        """Recupere une requete."""
        query = self.query_repo.get_by_id(query_id)
        if not query:
            return Result.fail(f"Requete non trouvee: {query_id}", "NOT_FOUND")
        return Result.ok(query)

    def list_data_queries(
        self,
        data_source_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Result[dict[str, Any]]:
        """Liste les requetes."""
        queries, total = self.query_repo.list(
            data_source_id=data_source_id,
            is_active=True,
            page=page,
            page_size=page_size
        )

        return Result.ok({
            "items": [DataQueryResponse.model_validate(q).model_dump() for q in queries],
            "total": total,
            "page": page,
            "page_size": page_size
        })

    def update_data_query(self, query_id: UUID, data: DataQueryUpdate) -> Result[DataQuery]:
        """Met a jour une requete."""
        query = self.query_repo.get_by_id(query_id)
        if not query:
            return Result.fail(f"Requete non trouvee: {query_id}", "NOT_FOUND")

        update_data = data.model_dump(exclude_unset=True)
        query = self.query_repo.update(query, update_data)

        return Result.ok(query)

    def delete_data_query(self, query_id: UUID) -> Result[bool]:
        """Supprime une requete."""
        query = self.query_repo.get_by_id(query_id)
        if not query:
            return Result.fail(f"Requete non trouvee: {query_id}", "NOT_FOUND")

        self.query_repo.soft_delete(query)
        return Result.ok(True)

    def execute_data_query(
        self,
        query_id: UUID,
        request: DataQueryExecuteRequest
    ) -> Result[DataQueryExecuteResponse]:
        """Execute une requete de donnees."""
        query = self.query_repo.get_by_id(query_id)
        if not query:
            return Result.fail(f"Requete non trouvee: {query_id}", "NOT_FOUND")

        start_time = time.time()

        try:
            # TODO: Implementer l'execution reelle
            columns = query.result_columns or []
            rows = []
            total_rows = 0

            execution_time = int((time.time() - start_time) * 1000)
            self.query_repo.record_execution(query, execution_time)

            return Result.ok(DataQueryExecuteResponse(
                query_id=query_id,
                columns=columns,
                rows=rows,
                total_rows=total_rows,
                execution_time_ms=execution_time,
                cache_hit=False,
                executed_at=datetime.utcnow()
            ))

        except Exception as e:
            return Result.fail(f"Erreur execution: {str(e)}", "EXECUTION_ERROR")

    # =========================================================================
    # SHARING
    # =========================================================================

    def share_dashboard(
        self,
        dashboard_id: UUID,
        data: DashboardShareCreate
    ) -> Result[DashboardShare]:
        """Partage un dashboard."""
        dashboard = self.dashboard_repo.get_by_id(dashboard_id, load_widgets=False)
        if not dashboard:
            return Result.fail(f"Dashboard non trouve: {dashboard_id}", "NOT_FOUND")

        if not self._can_access_dashboard(dashboard, SharePermission.MANAGE):
            return Result.fail("Acces refuse", "FORBIDDEN")

        share_data = data.model_dump(exclude_unset=True, exclude={"link_password"})
        share_data["dashboard_id"] = dashboard_id
        share_data["shared_by"] = self.user_id

        # Generer lien si partage par lien
        if data.share_type == "link":
            share_data["share_link"] = secrets.token_urlsafe(32)
            if data.link_password:
                share_data["link_password_hash"] = hashlib.sha256(
                    data.link_password.encode()
                ).hexdigest()

        share = self.share_repo.create(share_data)

        # Mettre a jour le dashboard
        if not dashboard.is_shared:
            self.dashboard_repo.update(dashboard, {"is_shared": True}, self.user_id)

        return Result.ok(share)

    def get_dashboard_shares(self, dashboard_id: UUID) -> Result[list[DashboardShare]]:
        """Recupere les partages d'un dashboard."""
        dashboard = self.dashboard_repo.get_by_id(dashboard_id, load_widgets=False)
        if not dashboard:
            return Result.fail(f"Dashboard non trouve: {dashboard_id}", "NOT_FOUND")

        if not self._can_access_dashboard(dashboard, SharePermission.MANAGE):
            return Result.fail("Acces refuse", "FORBIDDEN")

        shares = self.share_repo.get_by_dashboard(dashboard_id)
        return Result.ok(shares)

    def get_share_by_link(self, share_link: str, password: Optional[str] = None) -> Result[DashboardShare]:
        """Recupere un partage par lien."""
        share = self.share_repo.get_by_link(share_link)
        if not share:
            return Result.fail("Lien invalide", "NOT_FOUND")

        # Verifier expiration
        if share.link_expires_at and share.link_expires_at < datetime.utcnow():
            return Result.fail("Lien expire", "EXPIRED")

        # Verifier limite d'acces
        if share.link_max_access and share.link_access_count >= share.link_max_access:
            return Result.fail("Limite d'acces atteinte", "LIMIT_REACHED")

        # Verifier mot de passe
        if share.link_password_hash:
            if not password:
                return Result.fail("Mot de passe requis", "PASSWORD_REQUIRED")
            if hashlib.sha256(password.encode()).hexdigest() != share.link_password_hash:
                return Result.fail("Mot de passe incorrect", "INVALID_PASSWORD")

        self.share_repo.increment_link_access(share)
        return Result.ok(share)

    def update_share(self, share_id: UUID, data: DashboardShareUpdate) -> Result[DashboardShare]:
        """Met a jour un partage."""
        share = self.share_repo.get_by_id(share_id)
        if not share:
            return Result.fail(f"Partage non trouve: {share_id}", "NOT_FOUND")

        dashboard = self.dashboard_repo.get_by_id(share.dashboard_id, load_widgets=False)
        if not self._can_access_dashboard(dashboard, SharePermission.MANAGE):
            return Result.fail("Acces refuse", "FORBIDDEN")

        update_data = data.model_dump(exclude_unset=True)
        share = self.share_repo.update(share, update_data)

        return Result.ok(share)

    def revoke_share(self, share_id: UUID) -> Result[bool]:
        """Revoque un partage."""
        share = self.share_repo.get_by_id(share_id)
        if not share:
            return Result.fail(f"Partage non trouve: {share_id}", "NOT_FOUND")

        dashboard = self.dashboard_repo.get_by_id(share.dashboard_id, load_widgets=False)
        if not self._can_access_dashboard(dashboard, SharePermission.MANAGE):
            return Result.fail("Acces refuse", "FORBIDDEN")

        self.share_repo.delete(share)
        return Result.ok(True)

    # =========================================================================
    # FAVORITES
    # =========================================================================

    def add_favorite(self, data: DashboardFavoriteCreate) -> Result[DashboardFavorite]:
        """Ajoute un dashboard aux favoris."""
        dashboard = self.dashboard_repo.get_by_id(data.dashboard_id, load_widgets=False)
        if not dashboard:
            return Result.fail(f"Dashboard non trouve: {data.dashboard_id}", "NOT_FOUND")

        if not self._can_access_dashboard(dashboard, SharePermission.VIEW):
            return Result.fail("Acces refuse", "FORBIDDEN")

        # Verifier si deja favori
        existing = self.favorite_repo.get_by_user_and_dashboard(self.user_id, data.dashboard_id)
        if existing:
            return Result.fail("Dashboard deja en favori", "CONFLICT")

        fav_data = data.model_dump(exclude_unset=True)
        fav_data["user_id"] = self.user_id

        favorite = self.favorite_repo.create(fav_data)
        return Result.ok(favorite)

    def get_favorites(self, folder: Optional[str] = None) -> Result[list[DashboardFavorite]]:
        """Recupere les favoris de l'utilisateur."""
        favorites = self.favorite_repo.get_user_favorites(self.user_id, folder)
        return Result.ok(favorites)

    def update_favorite(self, favorite_id: UUID, data: DashboardFavoriteUpdate) -> Result[DashboardFavorite]:
        """Met a jour un favori."""
        favorite = self.favorite_repo.get_by_id(favorite_id)
        if not favorite:
            return Result.fail(f"Favori non trouve: {favorite_id}", "NOT_FOUND")

        if favorite.user_id != self.user_id:
            return Result.fail("Acces refuse", "FORBIDDEN")

        update_data = data.model_dump(exclude_unset=True)
        favorite = self.favorite_repo.update(favorite, update_data)

        return Result.ok(favorite)

    def remove_favorite(self, favorite_id: UUID) -> Result[bool]:
        """Supprime un favori."""
        favorite = self.favorite_repo.get_by_id(favorite_id)
        if not favorite:
            return Result.fail(f"Favori non trouve: {favorite_id}", "NOT_FOUND")

        if favorite.user_id != self.user_id:
            return Result.fail("Acces refuse", "FORBIDDEN")

        self.favorite_repo.delete(favorite)
        return Result.ok(True)

    def toggle_favorite(self, dashboard_id: UUID) -> Result[bool]:
        """Bascule le statut favori."""
        existing = self.favorite_repo.get_by_user_and_dashboard(self.user_id, dashboard_id)

        if existing:
            self.favorite_repo.delete(existing)
            return Result.ok(False)  # N'est plus favori
        else:
            dashboard = self.dashboard_repo.get_by_id(dashboard_id, load_widgets=False)
            if not dashboard:
                return Result.fail(f"Dashboard non trouve: {dashboard_id}", "NOT_FOUND")

            self.favorite_repo.create({
                "user_id": self.user_id,
                "dashboard_id": dashboard_id
            })
            return Result.ok(True)  # Est maintenant favori

    # =========================================================================
    # ALERTS
    # =========================================================================

    def create_alert_rule(self, data: AlertRuleCreate) -> Result[DashboardAlertRule]:
        """Cree une regle d'alerte."""
        if self.alert_rule_repo.code_exists(data.code):
            return Result.fail(f"Code deja utilise: {data.code}", "CONFLICT")

        create_data = data.model_dump(exclude_unset=True)
        rule = self.alert_rule_repo.create(create_data, self.user_id)

        # Marquer le widget comme ayant des alertes
        if rule.widget_id:
            widget = self.widget_repo.get_by_id(rule.widget_id)
            if widget:
                self.widget_repo.update(widget, {"has_alerts": True})

        return Result.ok(rule)

    def get_alert_rule(self, rule_id: UUID) -> Result[DashboardAlertRule]:
        """Recupere une regle d'alerte."""
        rule = self.alert_rule_repo.get_by_id(rule_id)
        if not rule:
            return Result.fail(f"Regle non trouvee: {rule_id}", "NOT_FOUND")
        return Result.ok(rule)

    def get_alert_rules(
        self,
        dashboard_id: Optional[UUID] = None,
        widget_id: Optional[UUID] = None
    ) -> Result[list[DashboardAlertRule]]:
        """Recupere les regles d'alerte."""
        if widget_id:
            rules = self.alert_rule_repo.get_by_widget(widget_id)
        elif dashboard_id:
            rules = self.alert_rule_repo.get_by_dashboard(dashboard_id)
        else:
            rules = self.alert_rule_repo.get_enabled_rules()

        return Result.ok(rules)

    def update_alert_rule(self, rule_id: UUID, data: AlertRuleUpdate) -> Result[DashboardAlertRule]:
        """Met a jour une regle d'alerte."""
        rule = self.alert_rule_repo.get_by_id(rule_id)
        if not rule:
            return Result.fail(f"Regle non trouvee: {rule_id}", "NOT_FOUND")

        update_data = data.model_dump(exclude_unset=True)
        rule = self.alert_rule_repo.update(rule, update_data)

        return Result.ok(rule)

    def delete_alert_rule(self, rule_id: UUID) -> Result[bool]:
        """Supprime une regle d'alerte."""
        rule = self.alert_rule_repo.get_by_id(rule_id)
        if not rule:
            return Result.fail(f"Regle non trouvee: {rule_id}", "NOT_FOUND")

        self.alert_rule_repo.soft_delete(rule)
        return Result.ok(True)

    def get_alert(self, alert_id: UUID) -> Result[DashboardAlert]:
        """Recupere une alerte."""
        alert = self.alert_repo.get_by_id(alert_id)
        if not alert:
            return Result.fail(f"Alerte non trouvee: {alert_id}", "NOT_FOUND")
        return Result.ok(alert)

    def get_alerts(
        self,
        status: Optional[AlertStatus] = None,
        dashboard_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Result[dict[str, Any]]:
        """Liste les alertes."""
        alerts, total = self.alert_repo.list(
            status=status,
            dashboard_id=dashboard_id,
            page=page,
            page_size=page_size
        )

        return Result.ok({
            "items": [AlertResponse.model_validate(a).model_dump() for a in alerts],
            "total": total,
            "page": page,
            "page_size": page_size
        })

    def get_active_alerts(self) -> Result[list[DashboardAlert]]:
        """Recupere les alertes actives."""
        alerts = self.alert_repo.get_active()
        return Result.ok(alerts)

    def get_alert_summary(self) -> Result[dict[str, Any]]:
        """Recupere le resume des alertes."""
        summary = self.alert_repo.get_summary()
        return Result.ok(summary)

    def acknowledge_alert(self, alert_id: UUID, data: AlertAcknowledge) -> Result[DashboardAlert]:
        """Acquitte une alerte."""
        alert = self.alert_repo.get_by_id(alert_id)
        if not alert:
            return Result.fail(f"Alerte non trouvee: {alert_id}", "NOT_FOUND")

        if alert.status not in [AlertStatus.ACTIVE]:
            return Result.fail("Alerte deja traitee", "INVALID_STATUS")

        alert = self.alert_repo.update(alert, {
            "status": AlertStatus.ACKNOWLEDGED,
            "acknowledged_at": datetime.utcnow(),
            "acknowledged_by": self.user_id,
            "acknowledged_notes": data.notes
        })

        return Result.ok(alert)

    def resolve_alert(self, alert_id: UUID, data: AlertResolve) -> Result[DashboardAlert]:
        """Resout une alerte."""
        alert = self.alert_repo.get_by_id(alert_id)
        if not alert:
            return Result.fail(f"Alerte non trouvee: {alert_id}", "NOT_FOUND")

        if alert.status == AlertStatus.RESOLVED:
            return Result.fail("Alerte deja resolue", "ALREADY_RESOLVED")

        alert = self.alert_repo.update(alert, {
            "status": AlertStatus.RESOLVED,
            "resolved_at": datetime.utcnow(),
            "resolved_by": self.user_id,
            "resolution_notes": data.resolution_notes,
            "resolution_type": data.resolution_type
        })

        return Result.ok(alert)

    def snooze_alert(self, alert_id: UUID, data: AlertSnooze) -> Result[DashboardAlert]:
        """Met une alerte en pause."""
        alert = self.alert_repo.get_by_id(alert_id)
        if not alert:
            return Result.fail(f"Alerte non trouvee: {alert_id}", "NOT_FOUND")

        alert = self.alert_repo.update(alert, {
            "status": AlertStatus.SNOOZED,
            "snoozed_until": data.snooze_until,
            "snoozed_by": self.user_id
        })

        return Result.ok(alert)

    def check_and_trigger_alerts(self) -> Result[list[DashboardAlert]]:
        """Verifie et declenche les alertes."""
        rules = self.alert_rule_repo.get_enabled_rules()
        triggered = []

        for rule in rules:
            # Verifier cooldown
            if rule.last_triggered_at:
                cooldown_end = rule.last_triggered_at + timedelta(minutes=rule.cooldown_minutes)
                if datetime.utcnow() < cooldown_end:
                    continue

            # Verifier la condition
            is_triggered, current_value = self._evaluate_alert_condition(rule)

            self.alert_rule_repo.update_check_time(rule)

            if is_triggered:
                # Creer l'alerte
                alert = self.alert_repo.create({
                    "rule_id": rule.id,
                    "widget_id": rule.widget_id,
                    "dashboard_id": rule.dashboard_id,
                    "title": rule.name,
                    "message": self._format_alert_message(rule, current_value),
                    "severity": rule.severity,
                    "metric_field": rule.metric_field,
                    "current_value": current_value,
                    "threshold_value": rule.threshold_value
                })

                self.alert_rule_repo.record_trigger(rule)
                triggered.append(alert)

                # TODO: Envoyer notifications

        return Result.ok(triggered)

    def _evaluate_alert_condition(
        self,
        rule: DashboardAlertRule
    ) -> tuple[bool, Optional[Decimal]]:
        """Evalue la condition d'une regle d'alerte."""
        # TODO: Implementer l'evaluation reelle
        return False, None

    def _format_alert_message(
        self,
        rule: DashboardAlertRule,
        current_value: Optional[Decimal]
    ) -> str:
        """Formate le message d'alerte."""
        if rule.message_template:
            return rule.message_template.format(
                value=current_value,
                threshold=rule.threshold_value,
                metric=rule.metric_field
            )
        return f"Alerte: {rule.metric_field} = {current_value} (seuil: {rule.threshold_value})"

    # =========================================================================
    # EXPORTS
    # =========================================================================

    def export_dashboard(
        self,
        dashboard_id: UUID,
        request: ExportRequest
    ) -> Result[DashboardExport]:
        """Exporte un dashboard."""
        dashboard = self.dashboard_repo.get_by_id(dashboard_id)
        if not dashboard:
            return Result.fail(f"Dashboard non trouve: {dashboard_id}", "NOT_FOUND")

        if not self._can_access_dashboard(dashboard, SharePermission.VIEW):
            return Result.fail("Acces refuse", "FORBIDDEN")

        # Creer l'export
        export = self.export_repo.create({
            "user_id": self.user_id,
            "dashboard_id": dashboard_id,
            "export_type": request.export_type,
            "export_format": request.export_format,
            "export_config": request.export_config,
            "filters_applied": request.filters,
            "date_range_applied": request.date_range,
            "file_name": request.filename,
            "status": ExportStatus.PENDING
        })

        # TODO: Lancer l'export en arriere-plan
        # self._process_export(export)

        return Result.ok(export)

    def export_widget(
        self,
        widget_id: UUID,
        request: ExportRequest
    ) -> Result[DashboardExport]:
        """Exporte un widget."""
        widget = self.widget_repo.get_by_id(widget_id)
        if not widget:
            return Result.fail(f"Widget non trouve: {widget_id}", "NOT_FOUND")

        dashboard = self.dashboard_repo.get_by_id(widget.dashboard_id, load_widgets=False)
        if not self._can_access_dashboard(dashboard, SharePermission.VIEW):
            return Result.fail("Acces refuse", "FORBIDDEN")

        export = self.export_repo.create({
            "user_id": self.user_id,
            "widget_id": widget_id,
            "dashboard_id": widget.dashboard_id,
            "export_type": "widget",
            "export_format": request.export_format,
            "export_config": request.export_config,
            "filters_applied": request.filters,
            "file_name": request.filename,
            "status": ExportStatus.PENDING
        })

        return Result.ok(export)

    def get_export(self, export_id: UUID) -> Result[DashboardExport]:
        """Recupere un export."""
        export = self.export_repo.get_by_id(export_id)
        if not export:
            return Result.fail(f"Export non trouve: {export_id}", "NOT_FOUND")

        if export.user_id != self.user_id:
            return Result.fail("Acces refuse", "FORBIDDEN")

        return Result.ok(export)

    def get_my_exports(self, limit: int = 20) -> Result[list[DashboardExport]]:
        """Recupere mes exports."""
        exports = self.export_repo.get_user_exports(self.user_id, limit)
        return Result.ok(exports)

    def download_export(self, export_id: UUID) -> Result[dict[str, Any]]:
        """Telecharge un export."""
        export = self.export_repo.get_by_id(export_id)
        if not export:
            return Result.fail(f"Export non trouve: {export_id}", "NOT_FOUND")

        if export.user_id != self.user_id:
            return Result.fail("Acces refuse", "FORBIDDEN")

        if export.status != ExportStatus.COMPLETED:
            return Result.fail("Export non termine", "NOT_READY")

        if export.file_expires_at and export.file_expires_at < datetime.utcnow():
            return Result.fail("Export expire", "EXPIRED")

        self.export_repo.increment_download(export)

        return Result.ok({
            "file_url": export.file_url,
            "file_name": export.file_name,
            "file_size": export.file_size
        })

    # =========================================================================
    # SCHEDULED REPORTS
    # =========================================================================

    def create_scheduled_report(self, data: ScheduledReportCreate) -> Result[ScheduledReport]:
        """Cree un rapport planifie."""
        if self.scheduled_repo.code_exists(data.code):
            return Result.fail(f"Code deja utilise: {data.code}", "CONFLICT")

        dashboard = self.dashboard_repo.get_by_id(data.dashboard_id, load_widgets=False)
        if not dashboard:
            return Result.fail(f"Dashboard non trouve: {data.dashboard_id}", "NOT_FOUND")

        if not self._can_access_dashboard(dashboard, SharePermission.VIEW):
            return Result.fail("Acces refuse", "FORBIDDEN")

        create_data = data.model_dump(exclude_unset=True)

        # Calculer la prochaine execution
        next_run = self._calculate_next_run(data.cron_expression, data.frequency)
        create_data["next_run_at"] = next_run

        report = self.scheduled_repo.create(create_data, self.user_id)

        return Result.ok(report)

    def _calculate_next_run(
        self,
        cron_expression: Optional[str],
        frequency: Optional[str]
    ) -> Optional[datetime]:
        """Calcule la prochaine execution."""
        # TODO: Implementer le parsing cron
        if frequency:
            now = datetime.utcnow()
            if frequency == "daily":
                return now + timedelta(days=1)
            elif frequency == "weekly":
                return now + timedelta(weeks=1)
            elif frequency == "monthly":
                return now + timedelta(days=30)
        return None

    def get_scheduled_report(self, report_id: UUID) -> Result[ScheduledReport]:
        """Recupere un rapport planifie."""
        report = self.scheduled_repo.get_by_id(report_id)
        if not report:
            return Result.fail(f"Rapport non trouve: {report_id}", "NOT_FOUND")
        return Result.ok(report)

    def get_scheduled_reports(
        self,
        dashboard_id: Optional[UUID] = None
    ) -> Result[list[ScheduledReport]]:
        """Recupere les rapports planifies."""
        if dashboard_id:
            reports = self.scheduled_repo.get_by_dashboard(dashboard_id)
        else:
            reports, _ = self.scheduled_repo.list(page=1, page_size=100)
        return Result.ok(reports)

    def update_scheduled_report(
        self,
        report_id: UUID,
        data: ScheduledReportUpdate
    ) -> Result[ScheduledReport]:
        """Met a jour un rapport planifie."""
        report = self.scheduled_repo.get_by_id(report_id)
        if not report:
            return Result.fail(f"Rapport non trouve: {report_id}", "NOT_FOUND")

        update_data = data.model_dump(exclude_unset=True)

        # Recalculer la prochaine execution si planification modifiee
        if "cron_expression" in update_data or "frequency" in update_data:
            update_data["next_run_at"] = self._calculate_next_run(
                update_data.get("cron_expression", report.cron_expression),
                update_data.get("frequency", report.frequency)
            )

        report = self.scheduled_repo.update(report, update_data)

        return Result.ok(report)

    def delete_scheduled_report(self, report_id: UUID) -> Result[bool]:
        """Supprime un rapport planifie."""
        report = self.scheduled_repo.get_by_id(report_id)
        if not report:
            return Result.fail(f"Rapport non trouve: {report_id}", "NOT_FOUND")

        self.scheduled_repo.soft_delete(report)
        return Result.ok(True)

    def run_scheduled_report_now(self, report_id: UUID) -> Result[DashboardExport]:
        """Execute immediatement un rapport planifie."""
        report = self.scheduled_repo.get_by_id(report_id)
        if not report:
            return Result.fail(f"Rapport non trouve: {report_id}", "NOT_FOUND")

        # Creer l'export
        export = self.export_repo.create({
            "user_id": self.user_id,
            "dashboard_id": report.dashboard_id,
            "export_type": "scheduled_report",
            "export_format": report.export_format,
            "export_config": report.export_config,
            "filters_applied": report.filters,
            "status": ExportStatus.PENDING
        })

        # TODO: Executer l'export

        return Result.ok(export)

    # =========================================================================
    # USER PREFERENCES
    # =========================================================================

    def get_user_preferences(self) -> Result[UserDashboardPreference]:
        """Recupere les preferences de l'utilisateur."""
        pref = self.pref_repo.get_or_create(self.user_id)
        return Result.ok(pref)

    def update_user_preferences(self, data: UserPreferenceUpdate) -> Result[UserDashboardPreference]:
        """Met a jour les preferences de l'utilisateur."""
        update_data = data.model_dump(exclude_unset=True)
        pref = self.pref_repo.update(self.user_id, update_data)
        return Result.ok(pref)

    def set_default_dashboard(self, dashboard_id: UUID) -> Result[bool]:
        """Definit le dashboard par defaut."""
        dashboard = self.dashboard_repo.get_by_id(dashboard_id, load_widgets=False)
        if not dashboard:
            return Result.fail(f"Dashboard non trouve: {dashboard_id}", "NOT_FOUND")

        if not self._can_access_dashboard(dashboard, SharePermission.VIEW):
            return Result.fail("Acces refuse", "FORBIDDEN")

        self.pref_repo.update(self.user_id, {"default_dashboard_id": dashboard_id})
        return Result.ok(True)

    def set_home_dashboard(self, dashboard_id: UUID) -> Result[bool]:
        """Definit le dashboard accueil."""
        dashboard = self.dashboard_repo.get_by_id(dashboard_id, load_widgets=False)
        if not dashboard:
            return Result.fail(f"Dashboard non trouve: {dashboard_id}", "NOT_FOUND")

        if not self._can_access_dashboard(dashboard, SharePermission.VIEW):
            return Result.fail("Acces refuse", "FORBIDDEN")

        self.pref_repo.update(self.user_id, {"home_dashboard_id": dashboard_id})
        return Result.ok(True)

    # =========================================================================
    # TEMPLATES
    # =========================================================================

    def create_template(self, data: TemplateCreate) -> Result[DashboardTemplate]:
        """Cree un template."""
        if self.template_repo.code_exists(data.code):
            return Result.fail(f"Code deja utilise: {data.code}", "CONFLICT")

        create_data = data.model_dump(exclude_unset=True)
        template = self.template_repo.create(create_data, self.user_id)

        return Result.ok(template)

    def create_template_from_dashboard(
        self,
        dashboard_id: UUID,
        code: str,
        name: str,
        description: Optional[str] = None
    ) -> Result[DashboardTemplate]:
        """Cree un template depuis un dashboard."""
        dashboard = self.dashboard_repo.get_by_id(dashboard_id)
        if not dashboard:
            return Result.fail(f"Dashboard non trouve: {dashboard_id}", "NOT_FOUND")

        if self.template_repo.code_exists(code):
            return Result.fail(f"Code deja utilise: {code}", "CONFLICT")

        # Extraire la configuration
        layout_config = {
            "layout_type": dashboard.layout_type,
            "columns": dashboard.columns,
            "row_height": dashboard.row_height,
            "margin": dashboard.margin,
            "is_compact": dashboard.is_compact
        }

        widgets_config = []
        for widget in dashboard.widgets:
            widgets_config.append({
                "title": widget.title,
                "widget_type": widget.widget_type.value,
                "chart_type": widget.chart_type.value if widget.chart_type else None,
                "position_x": widget.position_x,
                "position_y": widget.position_y,
                "width": widget.width,
                "height": widget.height,
                "config": widget.config,
                "chart_options": widget.chart_options,
                "colors": widget.colors
            })

        theme_config = {
            "theme": dashboard.theme,
            "background_color": dashboard.background_color
        }

        template = self.template_repo.create({
            "code": code,
            "name": name,
            "description": description,
            "icon": dashboard.icon,
            "dashboard_type": dashboard.dashboard_type,
            "layout_config": layout_config,
            "widgets_config": widgets_config,
            "theme_config": theme_config,
            "filters_config": dashboard.global_filters,
            "tags": dashboard.tags,
            "category": dashboard.category
        }, self.user_id)

        return Result.ok(template)

    def list_templates(
        self,
        dashboard_type: Optional[DashboardType] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Result[dict[str, Any]]:
        """Liste les templates."""
        templates, total = self.template_repo.list(
            dashboard_type=dashboard_type,
            category=category,
            page=page,
            page_size=page_size
        )

        return Result.ok({
            "items": [TemplateListItem.model_validate(t).model_dump() for t in templates],
            "total": total,
            "page": page,
            "page_size": page_size
        })

    def get_template(self, template_id: UUID) -> Result[DashboardTemplate]:
        """Recupere un template."""
        template = self.template_repo.get_by_id(template_id)
        if not template:
            return Result.fail(f"Template non trouve: {template_id}", "NOT_FOUND")
        return Result.ok(template)

    def update_template(self, template_id: UUID, data: TemplateUpdate) -> Result[DashboardTemplate]:
        """Met a jour un template."""
        template = self.template_repo.get_by_id(template_id)
        if not template:
            return Result.fail(f"Template non trouve: {template_id}", "NOT_FOUND")

        update_data = data.model_dump(exclude_unset=True)
        template = self.template_repo.update(template, update_data)

        return Result.ok(template)

    def delete_template(self, template_id: UUID) -> Result[bool]:
        """Supprime un template."""
        template = self.template_repo.get_by_id(template_id)
        if not template:
            return Result.fail(f"Template non trouve: {template_id}", "NOT_FOUND")

        self.template_repo.soft_delete(template)
        return Result.ok(True)

    # =========================================================================
    # OVERVIEW
    # =========================================================================

    def get_overview(self) -> Result[dict[str, Any]]:
        """Recupere la vue d'ensemble."""
        # Dashboards
        my_dashboards, _ = self.dashboard_repo.list(
            filters=DashboardFilters(owner_id=self.user_id),
            page=1,
            page_size=1000
        )
        all_dashboards, total_dashboards = self.dashboard_repo.list(
            user_id=self.user_id,
            page=1,
            page_size=1000
        )

        shared_with_me = [
            d for d in all_dashboards
            if d.owner_id != self.user_id
        ]

        public_dashboards, _ = self.dashboard_repo.list(
            filters=DashboardFilters(is_public=True),
            page=1,
            page_size=100
        )

        templates, _ = self.template_repo.list(page=1, page_size=100)

        # Recents
        recent = self.dashboard_repo.get_recent(self.user_id, limit=5)

        # Favoris
        favorites = self.favorite_repo.get_user_favorites(self.user_id)

        # Pinned
        pinned = [f.dashboard for f in favorites if f.is_pinned and f.dashboard]

        # Alertes
        alert_summary = self.alert_repo.get_summary()

        return Result.ok({
            "total_dashboards": total_dashboards,
            "my_dashboards": len(my_dashboards),
            "shared_with_me": len(shared_with_me),
            "public_dashboards": len(public_dashboards),
            "templates": len(templates),
            "recent_dashboards": [
                DashboardListItem(
                    id=d.id,
                    code=d.code,
                    name=d.name,
                    description=d.description,
                    icon=d.icon,
                    color=d.color,
                    dashboard_type=d.dashboard_type,
                    owner_id=d.owner_id,
                    is_shared=d.is_shared,
                    is_public=d.is_public,
                    is_template=d.is_template,
                    view_count=d.view_count,
                    tags=d.tags,
                    category=d.category,
                    created_at=d.created_at,
                    last_viewed_at=d.last_viewed_at
                ).model_dump() for d in recent
            ],
            "favorite_dashboards": [
                DashboardFavoriteResponse.model_validate(f).model_dump()
                for f in favorites[:5]
            ],
            "pinned_dashboards": [
                DashboardListItem(
                    id=d.id,
                    code=d.code,
                    name=d.name,
                    description=d.description,
                    icon=d.icon,
                    color=d.color,
                    dashboard_type=d.dashboard_type,
                    owner_id=d.owner_id,
                    is_shared=d.is_shared,
                    is_public=d.is_public,
                    is_template=d.is_template,
                    view_count=d.view_count,
                    tags=d.tags,
                    category=d.category,
                    created_at=d.created_at,
                    last_viewed_at=d.last_viewed_at
                ).model_dump() for d in pinned[:5]
            ],
            "alerts": alert_summary
        })

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _can_access_dashboard(
        self,
        dashboard: Dashboard,
        required_permission: SharePermission
    ) -> bool:
        """Verifie si l'utilisateur peut acceder au dashboard."""
        # Proprietaire
        if dashboard.owner_id == self.user_id:
            return True

        # Admin
        if self.context.is_admin:
            return True

        # Public
        if dashboard.is_public and required_permission == SharePermission.VIEW:
            return True

        # Partage
        shares = self.share_repo.get_shared_with_user(self.user_id)
        for share in shares:
            if share.dashboard_id == dashboard.id:
                if self._permission_sufficient(share.permission, required_permission):
                    return True

        return False

    def _permission_sufficient(
        self,
        actual: SharePermission,
        required: SharePermission
    ) -> bool:
        """Verifie si la permission est suffisante."""
        hierarchy = {
            SharePermission.VIEW: 1,
            SharePermission.INTERACT: 2,
            SharePermission.EDIT: 3,
            SharePermission.MANAGE: 4
        }
        return hierarchy.get(actual, 0) >= hierarchy.get(required, 0)
