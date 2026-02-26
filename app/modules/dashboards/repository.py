"""
AZALSCORE ERP - Module DASHBOARDS
==================================
Repository avec isolation tenant et soft delete.

CRITIQUE: Toutes les requetes sont filtrees par tenant_id.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc, case
from sqlalchemy.orm import Session, joinedload, selectinload

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
    WidgetType,
    AlertStatus,
    AlertSeverity,
    ExportStatus,
)
from .schemas import DashboardFilters, WidgetFilters


class DashboardRepository:
    """Repository Dashboard avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        query = self.db.query(Dashboard).filter(Dashboard.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(Dashboard.deleted_at.is_(None))
        return query

    def get_by_id(self, id: UUID, load_widgets: bool = True) -> Optional[Dashboard]:
        """Recupere un dashboard par ID."""
        query = self._base_query()
        if load_widgets:
            query = query.options(selectinload(Dashboard.widgets))
        return query.filter(Dashboard.id == id).first()

    def get_by_code(self, code: str) -> Optional[Dashboard]:
        """Recupere un dashboard par code."""
        return self._base_query().filter(Dashboard.code == code.upper()).first()

    def exists(self, id: UUID) -> bool:
        """Verifie si un dashboard existe."""
        return self._base_query().filter(Dashboard.id == id).count() > 0

    def code_exists(self, code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Verifie si un code existe."""
        query = self._base_query().filter(Dashboard.code == code.upper())
        if exclude_id:
            query = query.filter(Dashboard.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: Optional[DashboardFilters] = None,
        user_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> tuple[list[Dashboard], int]:
        """Liste les dashboards avec filtres."""
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    Dashboard.name.ilike(term),
                    Dashboard.code.ilike(term),
                    Dashboard.description.ilike(term)
                ))
            if filters.dashboard_type:
                query = query.filter(Dashboard.dashboard_type == filters.dashboard_type)
            if filters.owner_id:
                query = query.filter(Dashboard.owner_id == filters.owner_id)
            if filters.is_shared is not None:
                query = query.filter(Dashboard.is_shared == filters.is_shared)
            if filters.is_public is not None:
                query = query.filter(Dashboard.is_public == filters.is_public)
            if filters.is_template is not None:
                query = query.filter(Dashboard.is_template == filters.is_template)
            if filters.tags:
                for tag in filters.tags:
                    query = query.filter(Dashboard.tags.contains([tag]))
            if filters.category:
                query = query.filter(Dashboard.category == filters.category)
            if filters.created_from:
                query = query.filter(Dashboard.created_at >= filters.created_from)
            if filters.created_to:
                query = query.filter(Dashboard.created_at <= filters.created_to)

        # Filtrer par acces utilisateur si specifie
        if user_id and not filters.owner_id:
            # Dashboard dont on est proprietaire ou partages avec nous
            query = query.filter(or_(
                Dashboard.owner_id == user_id,
                Dashboard.is_public == True,
                Dashboard.id.in_(
                    self.db.query(DashboardShare.dashboard_id).filter(
                        DashboardShare.tenant_id == self.tenant_id,
                        DashboardShare.shared_with_user_id == user_id,
                        DashboardShare.is_active == True
                    )
                )
            ))

        total = query.count()

        # Tri
        sort_column = getattr(Dashboard, sort_by, Dashboard.created_at)
        query = query.order_by(desc(sort_column) if sort_dir == "desc" else asc(sort_column))

        # Pagination
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_user_dashboards(
        self,
        user_id: UUID,
        include_shared: bool = True
    ) -> list[Dashboard]:
        """Recupere les dashboards d'un utilisateur."""
        query = self._base_query().filter(Dashboard.owner_id == user_id)

        if include_shared:
            shared_ids = self.db.query(DashboardShare.dashboard_id).filter(
                DashboardShare.tenant_id == self.tenant_id,
                DashboardShare.shared_with_user_id == user_id,
                DashboardShare.is_active == True
            ).subquery()

            query = self._base_query().filter(or_(
                Dashboard.owner_id == user_id,
                Dashboard.id.in_(shared_ids),
                Dashboard.is_public == True
            ))

        return query.order_by(Dashboard.name).all()

    def get_recent(self, user_id: UUID, limit: int = 5) -> list[Dashboard]:
        """Recupere les dashboards recemment vus."""
        return self._base_query().filter(
            Dashboard.last_viewed_by == user_id
        ).order_by(desc(Dashboard.last_viewed_at)).limit(limit).all()

    def get_default(self, user_id: UUID) -> Optional[Dashboard]:
        """Recupere le dashboard par defaut d'un utilisateur."""
        # D'abord verifier les preferences utilisateur
        pref = self.db.query(UserDashboardPreference).filter(
            UserDashboardPreference.tenant_id == self.tenant_id,
            UserDashboardPreference.user_id == user_id
        ).first()

        if pref and pref.default_dashboard_id:
            dashboard = self.get_by_id(pref.default_dashboard_id)
            if dashboard:
                return dashboard

        # Sinon, dashboard marque comme defaut
        return self._base_query().filter(
            Dashboard.owner_id == user_id,
            Dashboard.is_default == True
        ).first()

    def get_home(self, user_id: UUID) -> Optional[Dashboard]:
        """Recupere le dashboard accueil d'un utilisateur."""
        pref = self.db.query(UserDashboardPreference).filter(
            UserDashboardPreference.tenant_id == self.tenant_id,
            UserDashboardPreference.user_id == user_id
        ).first()

        if pref and pref.home_dashboard_id:
            dashboard = self.get_by_id(pref.home_dashboard_id)
            if dashboard:
                return dashboard

        return self._base_query().filter(
            Dashboard.owner_id == user_id,
            Dashboard.is_home == True
        ).first()

    def create(self, data: dict[str, Any], created_by: Optional[UUID] = None) -> Dashboard:
        """Cree un dashboard."""
        widgets_data = data.pop("widgets", [])

        entity = Dashboard(
            tenant_id=self.tenant_id,
            created_by=created_by,
            owner_id=data.pop("owner_id", created_by),
            **data
        )
        self.db.add(entity)
        self.db.flush()

        # Creer les widgets
        for i, widget_data in enumerate(widgets_data):
            widget = DashboardWidget(
                tenant_id=self.tenant_id,
                dashboard_id=entity.id,
                display_order=i,
                created_by=created_by,
                **widget_data
            )
            self.db.add(widget)

        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(
        self,
        entity: Dashboard,
        data: dict[str, Any],
        updated_by: Optional[UUID] = None
    ) -> Dashboard:
        """Met a jour un dashboard."""
        for key, value in data.items():
            if hasattr(entity, key) and key not in ["id", "tenant_id", "created_at"]:
                setattr(entity, key, value)

        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: Dashboard, deleted_by: Optional[UUID] = None) -> bool:
        """Suppression logique."""
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        entity.is_active = False
        self.db.commit()
        return True

    def restore(self, entity: Dashboard) -> Dashboard:
        """Restaure un dashboard supprime."""
        entity.deleted_at = None
        entity.deleted_by = None
        entity.is_active = True
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def hard_delete(self, entity: Dashboard) -> bool:
        """Suppression definitive."""
        self.db.delete(entity)
        self.db.commit()
        return True

    def increment_view_count(self, entity: Dashboard, user_id: UUID) -> None:
        """Incremente le compteur de vues."""
        entity.view_count += 1
        entity.last_viewed_at = datetime.utcnow()
        entity.last_viewed_by = user_id
        self.db.commit()

    def duplicate(
        self,
        entity: Dashboard,
        new_code: str,
        new_name: str,
        owner_id: UUID
    ) -> Dashboard:
        """Duplique un dashboard."""
        # Creer le nouveau dashboard
        new_dashboard = Dashboard(
            tenant_id=self.tenant_id,
            code=new_code,
            name=new_name,
            description=entity.description,
            icon=entity.icon,
            color=entity.color,
            dashboard_type=entity.dashboard_type,
            owner_id=owner_id,
            layout_type=entity.layout_type,
            layout_config=entity.layout_config,
            columns=entity.columns,
            row_height=entity.row_height,
            margin=entity.margin,
            is_compact=entity.is_compact,
            is_draggable=entity.is_draggable,
            is_resizable=entity.is_resizable,
            theme=entity.theme,
            background_color=entity.background_color,
            custom_css=entity.custom_css,
            refresh_frequency=entity.refresh_frequency,
            auto_refresh=entity.auto_refresh,
            global_filters=entity.global_filters,
            default_filters=entity.default_filters,
            default_date_range=entity.default_date_range,
            tags=entity.tags,
            category=entity.category,
            created_by=owner_id
        )
        self.db.add(new_dashboard)
        self.db.flush()

        # Dupliquer les widgets
        for widget in entity.widgets:
            new_widget = DashboardWidget(
                tenant_id=self.tenant_id,
                dashboard_id=new_dashboard.id,
                code=widget.code,
                title=widget.title,
                subtitle=widget.subtitle,
                description=widget.description,
                icon=widget.icon,
                widget_type=widget.widget_type,
                chart_type=widget.chart_type,
                position_x=widget.position_x,
                position_y=widget.position_y,
                width=widget.width,
                height=widget.height,
                min_width=widget.min_width,
                min_height=widget.min_height,
                max_width=widget.max_width,
                max_height=widget.max_height,
                data_source_id=widget.data_source_id,
                query_config=widget.query_config,
                static_data=widget.static_data,
                config=widget.config,
                chart_options=widget.chart_options,
                display_options=widget.display_options,
                data_mapping=widget.data_mapping,
                aggregation=widget.aggregation,
                colors=widget.colors,
                custom_style=widget.custom_style,
                drill_down_config=widget.drill_down_config,
                click_action=widget.click_action,
                hover_action=widget.hover_action,
                links=widget.links,
                filters=widget.filters,
                linked_to_global=widget.linked_to_global,
                filter_fields=widget.filter_fields,
                refresh_frequency=widget.refresh_frequency,
                cache_ttl_seconds=widget.cache_ttl_seconds,
                show_title=widget.show_title,
                show_subtitle=widget.show_subtitle,
                show_legend=widget.show_legend,
                show_toolbar=widget.show_toolbar,
                show_border=widget.show_border,
                show_loading=widget.show_loading,
                display_order=widget.display_order,
                created_by=owner_id
            )
            self.db.add(new_widget)

        self.db.commit()
        self.db.refresh(new_dashboard)
        return new_dashboard

    def get_stats(self, dashboard_id: UUID) -> dict[str, Any]:
        """Recupere les statistiques d'un dashboard."""
        dashboard = self.get_by_id(dashboard_id)
        if not dashboard:
            return {}

        # Nombre de widgets
        widget_count = self.db.query(DashboardWidget).filter(
            DashboardWidget.dashboard_id == dashboard_id,
            DashboardWidget.is_active == True
        ).count()

        # Nombre de partages
        share_count = self.db.query(DashboardShare).filter(
            DashboardShare.dashboard_id == dashboard_id,
            DashboardShare.is_active == True
        ).count()

        # Nombre d'exports
        export_count = self.db.query(DashboardExport).filter(
            DashboardExport.dashboard_id == dashboard_id
        ).count()

        # Nombre d'alertes actives
        alert_count = self.db.query(DashboardAlert).filter(
            DashboardAlert.dashboard_id == dashboard_id,
            DashboardAlert.status == AlertStatus.ACTIVE
        ).count()

        return {
            "dashboard_id": str(dashboard_id),
            "dashboard_name": dashboard.name,
            "widget_count": widget_count,
            "view_count": dashboard.view_count,
            "share_count": share_count,
            "export_count": export_count,
            "alert_count": alert_count,
            "last_viewed_at": dashboard.last_viewed_at.isoformat() if dashboard.last_viewed_at else None,
            "created_at": dashboard.created_at.isoformat()
        }


class WidgetRepository:
    """Repository Widget avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(DashboardWidget).filter(
            DashboardWidget.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[DashboardWidget]:
        """Recupere un widget par ID."""
        return self._base_query().filter(DashboardWidget.id == id).first()

    def get_by_dashboard(self, dashboard_id: UUID) -> list[DashboardWidget]:
        """Recupere les widgets d'un dashboard."""
        return self._base_query().filter(
            DashboardWidget.dashboard_id == dashboard_id,
            DashboardWidget.is_active == True
        ).order_by(DashboardWidget.display_order).all()

    def create(
        self,
        dashboard_id: UUID,
        data: dict[str, Any],
        created_by: Optional[UUID] = None
    ) -> DashboardWidget:
        """Cree un widget."""
        # Determiner l'ordre d'affichage
        max_order = self.db.query(func.max(DashboardWidget.display_order)).filter(
            DashboardWidget.dashboard_id == dashboard_id
        ).scalar() or 0

        entity = DashboardWidget(
            tenant_id=self.tenant_id,
            dashboard_id=dashboard_id,
            display_order=max_order + 1,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: DashboardWidget, data: dict[str, Any]) -> DashboardWidget:
        """Met a jour un widget."""
        for key, value in data.items():
            if hasattr(entity, key) and key not in ["id", "tenant_id", "dashboard_id"]:
                setattr(entity, key, value)

        entity.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update_positions(
        self,
        dashboard_id: UUID,
        positions: list[dict[str, Any]]
    ) -> None:
        """Met a jour les positions de plusieurs widgets."""
        for pos in positions:
            widget = self.get_by_id(pos["widget_id"])
            if widget and widget.dashboard_id == dashboard_id:
                widget.position_x = pos.get("position_x", widget.position_x)
                widget.position_y = pos.get("position_y", widget.position_y)
                widget.width = pos.get("width", widget.width)
                widget.height = pos.get("height", widget.height)

        self.db.commit()

    def delete(self, entity: DashboardWidget) -> bool:
        """Supprime un widget."""
        self.db.delete(entity)
        self.db.commit()
        return True

    def bulk_delete(self, dashboard_id: UUID) -> int:
        """Supprime tous les widgets d'un dashboard."""
        count = self._base_query().filter(
            DashboardWidget.dashboard_id == dashboard_id
        ).delete()
        self.db.commit()
        return count


class DataSourceRepository:
    """Repository DataSource avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        query = self.db.query(DataSource).filter(DataSource.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(DataSource.deleted_at.is_(None))
        return query

    def get_by_id(self, id: UUID) -> Optional[DataSource]:
        """Recupere une source par ID."""
        return self._base_query().filter(DataSource.id == id).first()

    def get_by_code(self, code: str) -> Optional[DataSource]:
        """Recupere une source par code."""
        return self._base_query().filter(DataSource.code == code.upper()).first()

    def code_exists(self, code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Verifie si un code existe."""
        query = self._base_query().filter(DataSource.code == code.upper())
        if exclude_id:
            query = query.filter(DataSource.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        source_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[DataSource], int]:
        """Liste les sources de donnees."""
        query = self._base_query()

        if source_type:
            query = query.filter(DataSource.source_type == source_type)
        if is_active is not None:
            query = query.filter(DataSource.is_active == is_active)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(DataSource.name).offset(offset).limit(page_size).all()

        return items, total

    def get_internal_sources(self) -> list[DataSource]:
        """Recupere les sources internes."""
        return self._base_query().filter(
            DataSource.source_type == "internal",
            DataSource.is_active == True
        ).all()

    def create(self, data: dict[str, Any], created_by: Optional[UUID] = None) -> DataSource:
        """Cree une source de donnees."""
        entity = DataSource(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(
        self,
        entity: DataSource,
        data: dict[str, Any],
        updated_by: Optional[UUID] = None
    ) -> DataSource:
        """Met a jour une source de donnees."""
        for key, value in data.items():
            if hasattr(entity, key) and key not in ["id", "tenant_id", "created_at"]:
                setattr(entity, key, value)

        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: DataSource, deleted_by: Optional[UUID] = None) -> bool:
        """Suppression logique."""
        entity.deleted_at = datetime.utcnow()
        entity.is_active = False
        self.db.commit()
        return True


class DataQueryRepository:
    """Repository DataQuery avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        query = self.db.query(DataQuery).filter(DataQuery.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(DataQuery.deleted_at.is_(None))
        return query

    def get_by_id(self, id: UUID) -> Optional[DataQuery]:
        """Recupere une requete par ID."""
        return self._base_query().filter(DataQuery.id == id).first()

    def get_by_code(self, code: str) -> Optional[DataQuery]:
        """Recupere une requete par code."""
        return self._base_query().filter(DataQuery.code == code.upper()).first()

    def code_exists(self, code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Verifie si un code existe."""
        query = self._base_query().filter(DataQuery.code == code.upper())
        if exclude_id:
            query = query.filter(DataQuery.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        data_source_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[DataQuery], int]:
        """Liste les requetes."""
        query = self._base_query()

        if data_source_id:
            query = query.filter(DataQuery.data_source_id == data_source_id)
        if is_active is not None:
            query = query.filter(DataQuery.is_active == is_active)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(DataQuery.name).offset(offset).limit(page_size).all()

        return items, total

    def create(self, data: dict[str, Any], created_by: Optional[UUID] = None) -> DataQuery:
        """Cree une requete."""
        entity = DataQuery(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: DataQuery, data: dict[str, Any]) -> DataQuery:
        """Met a jour une requete."""
        for key, value in data.items():
            if hasattr(entity, key) and key not in ["id", "tenant_id", "created_at"]:
                setattr(entity, key, value)

        self.db.commit()
        self.db.refresh(entity)
        return entity

    def record_execution(
        self,
        entity: DataQuery,
        execution_time_ms: int
    ) -> None:
        """Enregistre une execution."""
        entity.last_executed_at = datetime.utcnow()
        entity.last_execution_time_ms = execution_time_ms
        entity.execution_count += 1

        # Calculer la moyenne
        if entity.avg_execution_time_ms:
            entity.avg_execution_time_ms = (
                entity.avg_execution_time_ms * (entity.execution_count - 1) + execution_time_ms
            ) // entity.execution_count
        else:
            entity.avg_execution_time_ms = execution_time_ms

        self.db.commit()

    def soft_delete(self, entity: DataQuery) -> bool:
        """Suppression logique."""
        entity.deleted_at = datetime.utcnow()
        entity.is_active = False
        self.db.commit()
        return True


class ShareRepository:
    """Repository DashboardShare avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(DashboardShare).filter(
            DashboardShare.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[DashboardShare]:
        """Recupere un partage par ID."""
        return self._base_query().filter(DashboardShare.id == id).first()

    def get_by_link(self, share_link: str) -> Optional[DashboardShare]:
        """Recupere un partage par lien."""
        return self._base_query().filter(
            DashboardShare.share_link == share_link,
            DashboardShare.is_active == True
        ).first()

    def get_by_dashboard(self, dashboard_id: UUID) -> list[DashboardShare]:
        """Recupere les partages d'un dashboard."""
        return self._base_query().filter(
            DashboardShare.dashboard_id == dashboard_id,
            DashboardShare.is_active == True
        ).all()

    def get_shared_with_user(self, user_id: UUID) -> list[DashboardShare]:
        """Recupere les dashboards partages avec un utilisateur."""
        return self._base_query().filter(
            DashboardShare.shared_with_user_id == user_id,
            DashboardShare.is_active == True
        ).all()

    def create(self, data: dict[str, Any]) -> DashboardShare:
        """Cree un partage."""
        entity = DashboardShare(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: DashboardShare, data: dict[str, Any]) -> DashboardShare:
        """Met a jour un partage."""
        for key, value in data.items():
            if hasattr(entity, key) and key not in ["id", "tenant_id"]:
                setattr(entity, key, value)

        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity: DashboardShare) -> bool:
        """Supprime un partage."""
        self.db.delete(entity)
        self.db.commit()
        return True

    def increment_link_access(self, entity: DashboardShare) -> None:
        """Incremente le compteur d'acces lien."""
        entity.link_access_count += 1
        entity.last_accessed_at = datetime.utcnow()
        self.db.commit()


class FavoriteRepository:
    """Repository DashboardFavorite avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(DashboardFavorite).filter(
            DashboardFavorite.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[DashboardFavorite]:
        """Recupere un favori par ID."""
        return self._base_query().filter(DashboardFavorite.id == id).first()

    def get_user_favorites(
        self,
        user_id: UUID,
        folder: Optional[str] = None
    ) -> list[DashboardFavorite]:
        """Recupere les favoris d'un utilisateur."""
        query = self._base_query().filter(DashboardFavorite.user_id == user_id)

        if folder:
            query = query.filter(DashboardFavorite.folder == folder)

        return query.options(
            joinedload(DashboardFavorite.dashboard)
        ).order_by(
            DashboardFavorite.is_pinned.desc(),
            DashboardFavorite.display_order
        ).all()

    def get_by_user_and_dashboard(
        self,
        user_id: UUID,
        dashboard_id: UUID
    ) -> Optional[DashboardFavorite]:
        """Recupere un favori par utilisateur et dashboard."""
        return self._base_query().filter(
            DashboardFavorite.user_id == user_id,
            DashboardFavorite.dashboard_id == dashboard_id
        ).first()

    def is_favorite(self, user_id: UUID, dashboard_id: UUID) -> bool:
        """Verifie si un dashboard est en favori."""
        return self.get_by_user_and_dashboard(user_id, dashboard_id) is not None

    def create(self, data: dict[str, Any]) -> DashboardFavorite:
        """Cree un favori."""
        entity = DashboardFavorite(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: DashboardFavorite, data: dict[str, Any]) -> DashboardFavorite:
        """Met a jour un favori."""
        for key, value in data.items():
            if hasattr(entity, key) and key not in ["id", "tenant_id", "user_id", "dashboard_id"]:
                setattr(entity, key, value)

        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity: DashboardFavorite) -> bool:
        """Supprime un favori."""
        self.db.delete(entity)
        self.db.commit()
        return True


class AlertRuleRepository:
    """Repository AlertRule avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base avec filtre tenant."""
        query = self.db.query(DashboardAlertRule).filter(
            DashboardAlertRule.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(DashboardAlertRule.deleted_at.is_(None))
        return query

    def get_by_id(self, id: UUID) -> Optional[DashboardAlertRule]:
        """Recupere une regle par ID."""
        return self._base_query().filter(DashboardAlertRule.id == id).first()

    def get_by_code(self, code: str) -> Optional[DashboardAlertRule]:
        """Recupere une regle par code."""
        return self._base_query().filter(DashboardAlertRule.code == code.upper()).first()

    def code_exists(self, code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Verifie si un code existe."""
        query = self._base_query().filter(DashboardAlertRule.code == code.upper())
        if exclude_id:
            query = query.filter(DashboardAlertRule.id != exclude_id)
        return query.count() > 0

    def get_by_widget(self, widget_id: UUID) -> list[DashboardAlertRule]:
        """Recupere les regles d'un widget."""
        return self._base_query().filter(
            DashboardAlertRule.widget_id == widget_id,
            DashboardAlertRule.is_active == True
        ).all()

    def get_by_dashboard(self, dashboard_id: UUID) -> list[DashboardAlertRule]:
        """Recupere les regles d'un dashboard."""
        return self._base_query().filter(
            DashboardAlertRule.dashboard_id == dashboard_id,
            DashboardAlertRule.is_active == True
        ).all()

    def get_enabled_rules(self) -> list[DashboardAlertRule]:
        """Recupere toutes les regles actives."""
        return self._base_query().filter(
            DashboardAlertRule.is_enabled == True,
            DashboardAlertRule.is_active == True
        ).all()

    def create(self, data: dict[str, Any], created_by: Optional[UUID] = None) -> DashboardAlertRule:
        """Cree une regle."""
        entity = DashboardAlertRule(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: DashboardAlertRule, data: dict[str, Any]) -> DashboardAlertRule:
        """Met a jour une regle."""
        for key, value in data.items():
            if hasattr(entity, key) and key not in ["id", "tenant_id", "created_at"]:
                setattr(entity, key, value)

        entity.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update_check_time(self, entity: DashboardAlertRule) -> None:
        """Met a jour le dernier check."""
        entity.last_checked_at = datetime.utcnow()
        self.db.commit()

    def record_trigger(self, entity: DashboardAlertRule) -> None:
        """Enregistre un declenchement."""
        entity.last_triggered_at = datetime.utcnow()
        entity.trigger_count += 1
        self.db.commit()

    def soft_delete(self, entity: DashboardAlertRule) -> bool:
        """Suppression logique."""
        entity.deleted_at = datetime.utcnow()
        entity.is_active = False
        self.db.commit()
        return True


class AlertRepository:
    """Repository Alert avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(DashboardAlert).filter(
            DashboardAlert.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[DashboardAlert]:
        """Recupere une alerte par ID."""
        return self._base_query().filter(DashboardAlert.id == id).first()

    def list(
        self,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        dashboard_id: Optional[UUID] = None,
        widget_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[DashboardAlert], int]:
        """Liste les alertes."""
        query = self._base_query()

        if status:
            query = query.filter(DashboardAlert.status == status)
        if severity:
            query = query.filter(DashboardAlert.severity == severity)
        if dashboard_id:
            query = query.filter(DashboardAlert.dashboard_id == dashboard_id)
        if widget_id:
            query = query.filter(DashboardAlert.widget_id == widget_id)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(desc(DashboardAlert.triggered_at)).offset(offset).limit(page_size).all()

        return items, total

    def get_active(self) -> list[DashboardAlert]:
        """Recupere les alertes actives."""
        return self._base_query().filter(
            DashboardAlert.status == AlertStatus.ACTIVE
        ).order_by(desc(DashboardAlert.triggered_at)).all()

    def create(self, data: dict[str, Any]) -> DashboardAlert:
        """Cree une alerte."""
        entity = DashboardAlert(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: DashboardAlert, data: dict[str, Any]) -> DashboardAlert:
        """Met a jour une alerte."""
        for key, value in data.items():
            if hasattr(entity, key) and key not in ["id", "tenant_id", "created_at"]:
                setattr(entity, key, value)

        self.db.commit()
        self.db.refresh(entity)
        return entity

    def get_summary(self) -> dict[str, Any]:
        """Recupere le resume des alertes."""
        total = self._base_query().count()

        by_status = {}
        for status in AlertStatus:
            count = self._base_query().filter(DashboardAlert.status == status).count()
            by_status[status.value] = count

        by_severity = {}
        for severity in AlertSeverity:
            count = self._base_query().filter(
                DashboardAlert.severity == severity,
                DashboardAlert.status == AlertStatus.ACTIVE
            ).count()
            by_severity[severity.value] = count

        recent = self._base_query().filter(
            DashboardAlert.status == AlertStatus.ACTIVE
        ).order_by(desc(DashboardAlert.triggered_at)).limit(5).all()

        return {
            "total": total,
            "active": by_status.get(AlertStatus.ACTIVE.value, 0),
            "acknowledged": by_status.get(AlertStatus.ACKNOWLEDGED.value, 0),
            "resolved": by_status.get(AlertStatus.RESOLVED.value, 0),
            "snoozed": by_status.get(AlertStatus.SNOOZED.value, 0),
            "by_severity": by_severity,
            "recent": recent
        }


class ExportRepository:
    """Repository Export avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(DashboardExport).filter(
            DashboardExport.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[DashboardExport]:
        """Recupere un export par ID."""
        return self._base_query().filter(DashboardExport.id == id).first()

    def get_user_exports(
        self,
        user_id: UUID,
        limit: int = 20
    ) -> list[DashboardExport]:
        """Recupere les exports d'un utilisateur."""
        return self._base_query().filter(
            DashboardExport.user_id == user_id
        ).order_by(desc(DashboardExport.created_at)).limit(limit).all()

    def create(self, data: dict[str, Any]) -> DashboardExport:
        """Cree un export."""
        entity = DashboardExport(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: DashboardExport, data: dict[str, Any]) -> DashboardExport:
        """Met a jour un export."""
        for key, value in data.items():
            if hasattr(entity, key) and key not in ["id", "tenant_id"]:
                setattr(entity, key, value)

        self.db.commit()
        self.db.refresh(entity)
        return entity

    def increment_download(self, entity: DashboardExport) -> None:
        """Incremente le compteur de telechargement."""
        entity.download_count += 1
        entity.last_downloaded_at = datetime.utcnow()
        self.db.commit()


class ScheduledReportRepository:
    """Repository ScheduledReport avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base avec filtre tenant."""
        query = self.db.query(ScheduledReport).filter(
            ScheduledReport.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(ScheduledReport.deleted_at.is_(None))
        return query

    def get_by_id(self, id: UUID) -> Optional[ScheduledReport]:
        """Recupere un rapport planifie par ID."""
        return self._base_query().filter(ScheduledReport.id == id).first()

    def get_by_code(self, code: str) -> Optional[ScheduledReport]:
        """Recupere un rapport planifie par code."""
        return self._base_query().filter(ScheduledReport.code == code.upper()).first()

    def code_exists(self, code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Verifie si un code existe."""
        query = self._base_query().filter(ScheduledReport.code == code.upper())
        if exclude_id:
            query = query.filter(ScheduledReport.id != exclude_id)
        return query.count() > 0

    def get_by_dashboard(self, dashboard_id: UUID) -> list[ScheduledReport]:
        """Recupere les rapports planifies d'un dashboard."""
        return self._base_query().filter(
            ScheduledReport.dashboard_id == dashboard_id,
            ScheduledReport.is_active == True
        ).all()

    def get_due_reports(self) -> list[ScheduledReport]:
        """Recupere les rapports a executer."""
        return self._base_query().filter(
            ScheduledReport.is_enabled == True,
            ScheduledReport.is_active == True,
            ScheduledReport.next_run_at <= datetime.utcnow()
        ).all()

    def create(self, data: dict[str, Any], created_by: Optional[UUID] = None) -> ScheduledReport:
        """Cree un rapport planifie."""
        entity = ScheduledReport(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: ScheduledReport, data: dict[str, Any]) -> ScheduledReport:
        """Met a jour un rapport planifie."""
        for key, value in data.items():
            if hasattr(entity, key) and key not in ["id", "tenant_id", "created_at"]:
                setattr(entity, key, value)

        entity.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def record_execution(
        self,
        entity: ScheduledReport,
        status: ExportStatus,
        error: Optional[str] = None
    ) -> None:
        """Enregistre une execution."""
        entity.last_run_at = datetime.utcnow()
        entity.last_status = status
        entity.last_error = error
        entity.run_count += 1
        self.db.commit()

    def soft_delete(self, entity: ScheduledReport) -> bool:
        """Suppression logique."""
        entity.deleted_at = datetime.utcnow()
        entity.is_active = False
        self.db.commit()
        return True


class UserPreferenceRepository:
    """Repository UserPreference avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def get_by_user(self, user_id: UUID) -> Optional[UserDashboardPreference]:
        """Recupere les preferences d'un utilisateur."""
        return self.db.query(UserDashboardPreference).filter(
            UserDashboardPreference.tenant_id == self.tenant_id,
            UserDashboardPreference.user_id == user_id
        ).first()

    def get_or_create(self, user_id: UUID) -> UserDashboardPreference:
        """Recupere ou cree les preferences d'un utilisateur."""
        pref = self.get_by_user(user_id)
        if not pref:
            pref = UserDashboardPreference(
                tenant_id=self.tenant_id,
                user_id=user_id
            )
            self.db.add(pref)
            self.db.commit()
            self.db.refresh(pref)
        return pref

    def update(
        self,
        user_id: UUID,
        data: dict[str, Any]
    ) -> UserDashboardPreference:
        """Met a jour les preferences."""
        pref = self.get_or_create(user_id)

        for key, value in data.items():
            if hasattr(pref, key) and key not in ["id", "tenant_id", "user_id"]:
                setattr(pref, key, value)

        pref.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(pref)
        return pref

    def add_recent_dashboard(self, user_id: UUID, dashboard_id: UUID) -> None:
        """Ajoute un dashboard aux recents."""
        pref = self.get_or_create(user_id)
        recent = list(pref.recent_dashboards or [])

        # Retirer si deja present
        dashboard_str = str(dashboard_id)
        if dashboard_str in recent:
            recent.remove(dashboard_str)

        # Ajouter en tete
        recent.insert(0, dashboard_str)

        # Garder les 10 derniers
        pref.recent_dashboards = recent[:10]
        self.db.commit()


class TemplateRepository:
    """Repository Template avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base avec filtre tenant."""
        query = self.db.query(DashboardTemplate).filter(
            or_(
                DashboardTemplate.tenant_id == self.tenant_id,
                DashboardTemplate.is_public == True
            )
        )
        if not self.include_deleted:
            query = query.filter(DashboardTemplate.deleted_at.is_(None))
        return query

    def get_by_id(self, id: UUID) -> Optional[DashboardTemplate]:
        """Recupere un template par ID."""
        return self._base_query().filter(DashboardTemplate.id == id).first()

    def get_by_code(self, code: str) -> Optional[DashboardTemplate]:
        """Recupere un template par code."""
        return self._base_query().filter(DashboardTemplate.code == code.upper()).first()

    def code_exists(self, code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Verifie si un code existe."""
        query = self.db.query(DashboardTemplate).filter(
            DashboardTemplate.tenant_id == self.tenant_id,
            DashboardTemplate.code == code.upper()
        )
        if exclude_id:
            query = query.filter(DashboardTemplate.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        dashboard_type: Optional[DashboardType] = None,
        category: Optional[str] = None,
        is_public: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[DashboardTemplate], int]:
        """Liste les templates."""
        query = self._base_query().filter(DashboardTemplate.is_active == True)

        if dashboard_type:
            query = query.filter(DashboardTemplate.dashboard_type == dashboard_type)
        if category:
            query = query.filter(DashboardTemplate.category == category)
        if is_public is not None:
            query = query.filter(DashboardTemplate.is_public == is_public)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(desc(DashboardTemplate.usage_count)).offset(offset).limit(page_size).all()

        return items, total

    def create(self, data: dict[str, Any], created_by: Optional[UUID] = None) -> DashboardTemplate:
        """Cree un template."""
        entity = DashboardTemplate(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: DashboardTemplate, data: dict[str, Any]) -> DashboardTemplate:
        """Met a jour un template."""
        for key, value in data.items():
            if hasattr(entity, key) and key not in ["id", "tenant_id", "created_at"]:
                setattr(entity, key, value)

        entity.version += 1
        entity.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def increment_usage(self, entity: DashboardTemplate) -> None:
        """Incremente le compteur d'usage."""
        entity.usage_count += 1
        self.db.commit()

    def soft_delete(self, entity: DashboardTemplate) -> bool:
        """Suppression logique."""
        entity.deleted_at = datetime.utcnow()
        entity.is_active = False
        self.db.commit()
        return True
