"""
AZALS - Module M10: BI & Reporting
Service métier pour Business Intelligence
"""

from datetime import date, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import desc, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.query_optimizer import QueryOptimizer

from .models import (
    Alert,
    AlertRule,
    AlertSeverity,
    AlertStatus,
    Bookmark,
    Dashboard,
    DashboardType,
    DashboardWidget,
    DataQuery,
    DataSource,
    DataSourceType,
    ExportHistory,
    KPICategory,
    KPIDefinition,
    KPITarget,
    KPITrend,
    KPIValue,
    RefreshFrequency,
    Report,
    ReportExecution,
    ReportSchedule,
    ReportStatus,
    ReportType,
    WidgetFilter,
)
from .schemas import (
    AlertCreate,
    AlertRuleCreate,
    AlertRuleUpdate,
    BookmarkCreate,
    DashboardCreate,
    DashboardUpdate,
    DataQueryCreate,
    DataSourceCreate,
    DataSourceUpdate,
    ExportRequest,
    KPICreate,
    KPITargetCreate,
    KPIUpdate,
    KPIValueCreate,
    ReportCreate,
    ReportExecuteRequest,
    ReportScheduleCreate,
    ReportUpdate,
    WidgetCreate,
    WidgetUpdate,
)


class BIService:
    """Service pour la Business Intelligence."""

    def __init__(self, db: Session, tenant_id: str, user_id: int):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self._optimizer = QueryOptimizer(db)

    # ========================================================================
    # DASHBOARDS
    # ========================================================================

    def create_dashboard(self, data: DashboardCreate) -> Dashboard:
        """Créer un tableau de bord."""
        dashboard = Dashboard(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            dashboard_type=data.dashboard_type,
            owner_id=self.user_id,
            is_shared=data.is_shared,
            shared_with=data.shared_with,
            layout=data.layout,
            theme=data.theme,
            refresh_frequency=data.refresh_frequency,
            auto_refresh=data.auto_refresh,
            global_filters=data.global_filters,
            default_date_range=data.default_date_range,
            is_default=data.is_default,
            is_public=data.is_public,
            created_by=self.user_id
        )

        self.db.add(dashboard)
        self.db.commit()
        self.db.refresh(dashboard)
        return dashboard

    def get_dashboard(self, dashboard_id: int) -> Dashboard | None:
        """Récupérer un tableau de bord."""
        dashboard = self.db.query(Dashboard).filter(
            Dashboard.id == dashboard_id,
            Dashboard.tenant_id == self.tenant_id
        ).first()

        if dashboard:
            # Incrémenter le compteur de vues
            dashboard.view_count += 1
            dashboard.last_viewed_at = datetime.utcnow()
            self.db.commit()

        return dashboard

    def get_dashboard_by_code(self, code: str) -> Dashboard | None:
        """Récupérer un tableau de bord par code."""
        return self.db.query(Dashboard).filter(
            Dashboard.code == code,
            Dashboard.tenant_id == self.tenant_id
        ).first()

    def list_dashboards(
        self,
        dashboard_type: DashboardType | None = None,
        owner_only: bool = False,
        include_shared: bool = True,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[Dashboard], int]:
        """Lister les tableaux de bord."""
        query = self.db.query(Dashboard).filter(
            Dashboard.tenant_id == self.tenant_id,
            Dashboard.is_active
        )

        if dashboard_type:
            query = query.filter(Dashboard.dashboard_type == dashboard_type)

        if owner_only:
            query = query.filter(Dashboard.owner_id == self.user_id)
        elif include_shared:
            query = query.filter(
                or_(
                    Dashboard.owner_id == self.user_id,
                    Dashboard.is_public,
                    Dashboard.is_shared
                )
            )

        total = query.count()
        dashboards = query.order_by(desc(Dashboard.view_count)).offset(skip).limit(limit).all()

        return dashboards, total

    def update_dashboard(self, dashboard_id: int, data: DashboardUpdate) -> Dashboard:
        """Mettre à jour un tableau de bord."""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tableau de bord non trouvé"
            )

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(dashboard, field, value)

        dashboard.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(dashboard)
        return dashboard

    def delete_dashboard(self, dashboard_id: int) -> bool:
        """Supprimer un tableau de bord."""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return False

        self.db.delete(dashboard)
        self.db.commit()
        return True

    def duplicate_dashboard(self, dashboard_id: int, new_code: str, new_name: str) -> Dashboard:
        """Dupliquer un tableau de bord."""
        source = self.get_dashboard(dashboard_id)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tableau de bord source non trouvé"
            )

        new_dashboard = Dashboard(
            tenant_id=self.tenant_id,
            code=new_code,
            name=new_name,
            description=source.description,
            dashboard_type=source.dashboard_type,
            owner_id=self.user_id,
            layout=source.layout,
            theme=source.theme,
            refresh_frequency=source.refresh_frequency,
            auto_refresh=source.auto_refresh,
            global_filters=source.global_filters,
            default_date_range=source.default_date_range,
            created_by=self.user_id
        )

        self.db.add(new_dashboard)
        self.db.flush()

        # Dupliquer les widgets
        for widget in source.widgets:
            new_widget = DashboardWidget(
                tenant_id=self.tenant_id,
                dashboard_id=new_dashboard.id,
                title=widget.title,
                widget_type=widget.widget_type,
                chart_type=widget.chart_type,
                position_x=widget.position_x,
                position_y=widget.position_y,
                width=widget.width,
                height=widget.height,
                data_source_id=widget.data_source_id,
                query_id=widget.query_id,
                kpi_id=widget.kpi_id,
                config=widget.config,
                chart_options=widget.chart_options,
                colors=widget.colors,
                static_data=widget.static_data,
                data_mapping=widget.data_mapping,
                show_title=widget.show_title,
                show_legend=widget.show_legend,
                show_toolbar=widget.show_toolbar,
                display_order=widget.display_order
            )
            self.db.add(new_widget)

        self.db.commit()
        self.db.refresh(new_dashboard)
        return new_dashboard

    # ========================================================================
    # WIDGETS
    # ========================================================================

    def add_widget(self, dashboard_id: int, data: WidgetCreate) -> DashboardWidget:
        """Ajouter un widget à un tableau de bord."""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tableau de bord non trouvé"
            )

        widget = DashboardWidget(
            tenant_id=self.tenant_id,
            dashboard_id=dashboard_id,
            title=data.title,
            widget_type=data.widget_type,
            chart_type=data.chart_type,
            position_x=data.position_x,
            position_y=data.position_y,
            width=data.width,
            height=data.height,
            data_source_id=data.data_source_id,
            query_id=data.query_id,
            kpi_id=data.kpi_id,
            config=data.config,
            chart_options=data.chart_options,
            colors=data.colors,
            static_data=data.static_data,
            data_mapping=data.data_mapping,
            drill_down_config=data.drill_down_config,
            click_action=data.click_action,
            show_title=data.show_title,
            show_legend=data.show_legend,
            show_toolbar=data.show_toolbar
        )

        self.db.add(widget)
        self.db.flush()

        # Ajouter les filtres
        if data.filters:
            for f in data.filters:
                widget_filter = WidgetFilter(
                    tenant_id=self.tenant_id,
                    widget_id=widget.id,
                    field_name=f.field_name,
                    operator=f.operator,
                    value=f.value,
                    is_dynamic=f.is_dynamic
                )
                self.db.add(widget_filter)

        self.db.commit()
        self.db.refresh(widget)
        return widget

    def update_widget(self, widget_id: int, data: WidgetUpdate) -> DashboardWidget:
        """Mettre à jour un widget."""
        widget = self.db.query(DashboardWidget).filter(
            DashboardWidget.id == widget_id,
            DashboardWidget.tenant_id == self.tenant_id
        ).first()

        if not widget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Widget non trouvé"
            )

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(widget, field, value)

        self.db.commit()
        self.db.refresh(widget)
        return widget

    def delete_widget(self, widget_id: int) -> bool:
        """Supprimer un widget."""
        widget = self.db.query(DashboardWidget).filter(
            DashboardWidget.id == widget_id,
            DashboardWidget.tenant_id == self.tenant_id
        ).first()

        if not widget:
            return False

        self.db.delete(widget)
        self.db.commit()
        return True

    def update_widget_positions(self, dashboard_id: int, positions: list[dict[str, int]]) -> bool:
        """Mettre à jour les positions de plusieurs widgets."""
        for pos in positions:
            widget = self.db.query(DashboardWidget).filter(
                DashboardWidget.id == pos.get("id"),
                DashboardWidget.dashboard_id == dashboard_id,
                DashboardWidget.tenant_id == self.tenant_id
            ).first()

            if widget:
                widget.position_x = pos.get("x", widget.position_x)
                widget.position_y = pos.get("y", widget.position_y)
                widget.width = pos.get("width", widget.width)
                widget.height = pos.get("height", widget.height)

        self.db.commit()
        return True

    # ========================================================================
    # REPORTS
    # ========================================================================

    def create_report(self, data: ReportCreate) -> Report:
        """Créer un rapport."""
        report = Report(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            report_type=data.report_type,
            template=data.template,
            template_file=data.template_file,
            data_sources=data.data_sources,
            queries=data.queries,
            parameters=data.parameters,
            available_formats=data.available_formats,
            default_format=data.default_format,
            page_size=data.page_size,
            orientation=data.orientation,
            owner_id=self.user_id,
            is_public=data.is_public,
            allowed_roles=data.allowed_roles,
            created_by=self.user_id
        )

        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_report(self, report_id: int) -> Report | None:
        """Récupérer un rapport."""
        return self.db.query(Report).filter(
            Report.id == report_id,
            Report.tenant_id == self.tenant_id
        ).first()

    def list_reports(
        self,
        report_type: ReportType | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[Report], int]:
        """Lister les rapports."""
        query = self.db.query(Report).filter(
            Report.tenant_id == self.tenant_id,
            Report.is_active
        )

        if report_type:
            query = query.filter(Report.report_type == report_type)

        total = query.count()
        reports = query.order_by(Report.name).offset(skip).limit(limit).all()

        return reports, total

    def update_report(self, report_id: int, data: ReportUpdate) -> Report:
        """Mettre à jour un rapport."""
        report = self.get_report(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rapport non trouvé"
            )

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(report, field, value)

        report.updated_by = self.user_id
        report.version += 1
        self.db.commit()
        self.db.refresh(report)
        return report

    def delete_report(self, report_id: int) -> bool:
        """Supprimer un rapport."""
        report = self.get_report(report_id)
        if not report:
            return False

        self.db.delete(report)
        self.db.commit()
        return True

    def execute_report(
        self,
        report_id: int,
        request: ReportExecuteRequest
    ) -> ReportExecution:
        """Exécuter un rapport."""
        report = self.get_report(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rapport non trouvé"
            )

        execution = ReportExecution(
            tenant_id=self.tenant_id,
            report_id=report_id,
            status=ReportStatus.PENDING,
            parameters=request.parameters,
            output_format=request.output_format,
            triggered_by=self.user_id
        )

        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        if not request.async_execution:
            # Exécution synchrone
            self._run_report_execution(execution)

        return execution

    def _run_report_execution(self, execution: ReportExecution) -> None:
        """Exécuter un rapport (logique interne)."""
        execution.status = ReportStatus.RUNNING
        execution.started_at = datetime.utcnow()
        self.db.commit()

        # NOTE: Phase 2 - Génération rapport via report_engine

        execution.status = ReportStatus.COMPLETED
        execution.completed_at = datetime.utcnow()
        execution.duration_seconds = int(
            (execution.completed_at - execution.started_at).total_seconds()
        )
        execution.file_path = f"/reports/{execution.id}.{execution.output_format.value}"
        execution.row_count = 0

        self.db.commit()

    def get_report_executions(
        self,
        report_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> list[ReportExecution]:
        """Récupérer les exécutions d'un rapport."""
        return self.db.query(ReportExecution).filter(
            ReportExecution.report_id == report_id,
            ReportExecution.tenant_id == self.tenant_id
        ).order_by(desc(ReportExecution.created_at)).offset(skip).limit(limit).all()

    # ========================================================================
    # REPORT SCHEDULES
    # ========================================================================

    def create_schedule(self, report_id: int, data: ReportScheduleCreate) -> ReportSchedule:
        """Créer une planification de rapport."""
        report = self.get_report(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rapport non trouvé"
            )

        schedule = ReportSchedule(
            tenant_id=self.tenant_id,
            report_id=report_id,
            name=data.name,
            cron_expression=data.cron_expression,
            frequency=data.frequency,
            parameters=data.parameters,
            output_format=data.output_format,
            recipients=data.recipients,
            distribution_method=data.distribution_method,
            is_enabled=data.is_enabled,
            timezone=data.timezone,
            created_by=self.user_id
        )

        # Calculer la prochaine exécution
        schedule.next_run_at = self._calculate_next_run(schedule)

        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def _calculate_next_run(self, schedule: ReportSchedule) -> datetime | None:
        """Calculer la prochaine exécution."""
        # NOTE: Phase 2 - Parser cron_expression avec croniter
        if schedule.frequency == RefreshFrequency.DAILY:
            return datetime.utcnow() + timedelta(days=1)
        elif schedule.frequency == RefreshFrequency.WEEKLY:
            return datetime.utcnow() + timedelta(weeks=1)
        elif schedule.frequency == RefreshFrequency.MONTHLY:
            return datetime.utcnow() + timedelta(days=30)
        return None

    # ========================================================================
    # KPIs
    # ========================================================================

    def create_kpi(self, data: KPICreate) -> KPIDefinition:
        """Créer un KPI."""
        kpi = KPIDefinition(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            category=data.category,
            formula=data.formula,
            unit=data.unit,
            precision=data.precision,
            aggregation_method=data.aggregation_method,
            data_source_id=data.data_source_id,
            query=data.query,
            display_format=data.display_format,
            good_threshold=data.good_threshold,
            warning_threshold=data.warning_threshold,
            bad_threshold=data.bad_threshold,
            higher_is_better=data.higher_is_better,
            refresh_frequency=data.refresh_frequency,
            compare_to_previous=data.compare_to_previous,
            comparison_period=data.comparison_period,
            created_by=self.user_id
        )

        self.db.add(kpi)
        self.db.commit()
        self.db.refresh(kpi)
        return kpi

    def get_kpi(self, kpi_id: int) -> KPIDefinition | None:
        """Récupérer un KPI."""
        return self.db.query(KPIDefinition).filter(
            KPIDefinition.id == kpi_id,
            KPIDefinition.tenant_id == self.tenant_id
        ).first()

    def get_kpi_by_code(self, code: str) -> KPIDefinition | None:
        """Récupérer un KPI par code."""
        return self.db.query(KPIDefinition).filter(
            KPIDefinition.code == code,
            KPIDefinition.tenant_id == self.tenant_id
        ).first()

    def list_kpis(
        self,
        category: KPICategory | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[KPIDefinition], int]:
        """Lister les KPIs."""
        query = self.db.query(KPIDefinition).filter(
            KPIDefinition.tenant_id == self.tenant_id,
            KPIDefinition.is_active
        )

        if category:
            query = query.filter(KPIDefinition.category == category)

        total = query.count()
        kpis = query.order_by(KPIDefinition.category, KPIDefinition.name).offset(skip).limit(limit).all()

        return kpis, total

    def update_kpi(self, kpi_id: int, data: KPIUpdate) -> KPIDefinition:
        """Mettre à jour un KPI."""
        kpi = self.get_kpi(kpi_id)
        if not kpi:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KPI non trouvé"
            )

        if kpi.is_system:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="KPI système non modifiable"
            )

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(kpi, field, value)

        self.db.commit()
        self.db.refresh(kpi)
        return kpi

    def record_kpi_value(self, kpi_id: int, data: KPIValueCreate) -> KPIValue:
        """Enregistrer une valeur de KPI."""
        kpi = self.get_kpi(kpi_id)
        if not kpi:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KPI non trouvé"
            )

        # Récupérer la valeur précédente
        previous = self.db.query(KPIValue).filter(
            KPIValue.kpi_id == kpi_id,
            KPIValue.tenant_id == self.tenant_id,
            KPIValue.period_type == data.period_type,
            KPIValue.dimension == data.dimension
        ).order_by(desc(KPIValue.period_date)).first()

        # Calculer la tendance
        trend = KPITrend.UNKNOWN
        change_percentage = None
        if previous and previous.value:
            if data.value > previous.value:
                trend = KPITrend.UP
            elif data.value < previous.value:
                trend = KPITrend.DOWN
            else:
                trend = KPITrend.STABLE

            if previous.value != 0:
                change_percentage = ((data.value - previous.value) / previous.value) * 100

        kpi_value = KPIValue(
            tenant_id=self.tenant_id,
            kpi_id=kpi_id,
            period_date=data.period_date,
            period_type=data.period_type,
            value=data.value,
            previous_value=previous.value if previous else None,
            change_percentage=change_percentage,
            trend=trend,
            dimension=data.dimension,
            dimension_value=data.dimension_value,
            extra_data=data.extra_data,
            source=data.source
        )

        self.db.add(kpi_value)
        kpi.last_calculated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(kpi_value)
        return kpi_value

    def get_kpi_values(
        self,
        kpi_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        period_type: str = "daily",
        limit: int = 100
    ) -> list[KPIValue]:
        """Récupérer les valeurs d'un KPI."""
        query = self.db.query(KPIValue).filter(
            KPIValue.kpi_id == kpi_id,
            KPIValue.tenant_id == self.tenant_id,
            KPIValue.period_type == period_type
        )

        if start_date:
            query = query.filter(KPIValue.period_date >= start_date)
        if end_date:
            query = query.filter(KPIValue.period_date <= end_date)

        return query.order_by(desc(KPIValue.period_date)).limit(limit).all()

    def get_kpi_current_value(self, kpi_id: int) -> KPIValue | None:
        """Récupérer la valeur actuelle d'un KPI."""
        return self.db.query(KPIValue).filter(
            KPIValue.kpi_id == kpi_id,
            KPIValue.tenant_id == self.tenant_id
        ).order_by(desc(KPIValue.period_date)).first()

    def set_kpi_target(self, kpi_id: int, data: KPITargetCreate) -> KPITarget:
        """Définir un objectif pour un KPI."""
        kpi = self.get_kpi(kpi_id)
        if not kpi:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KPI non trouvé"
            )

        # Vérifier si un objectif existe déjà pour cette période
        existing = self.db.query(KPITarget).filter(
            KPITarget.kpi_id == kpi_id,
            KPITarget.tenant_id == self.tenant_id,
            KPITarget.year == data.year,
            KPITarget.month == data.month,
            KPITarget.quarter == data.quarter
        ).first()

        if existing:
            # Mettre à jour l'existant
            existing.target_value = data.target_value
            existing.min_value = data.min_value
            existing.max_value = data.max_value
            existing.notes = data.notes
            self.db.commit()
            self.db.refresh(existing)
            return existing

        target = KPITarget(
            tenant_id=self.tenant_id,
            kpi_id=kpi_id,
            year=data.year,
            month=data.month,
            quarter=data.quarter,
            target_value=data.target_value,
            min_value=data.min_value,
            max_value=data.max_value,
            notes=data.notes,
            created_by=self.user_id
        )

        self.db.add(target)
        self.db.commit()
        self.db.refresh(target)
        return target

    # ========================================================================
    # ALERTS
    # ========================================================================

    def create_alert_rule(self, data: AlertRuleCreate) -> AlertRule:
        """Créer une règle d'alerte."""
        rule = AlertRule(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            severity=data.severity,
            source_type=data.source_type,
            source_id=data.source_id,
            condition=data.condition,
            check_frequency=data.check_frequency,
            notification_channels=data.notification_channels,
            recipients=data.recipients,
            cooldown_minutes=data.cooldown_minutes,
            is_enabled=data.is_enabled,
            auto_resolve=data.auto_resolve,
            created_by=self.user_id
        )

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def get_alert_rule(self, rule_id: int) -> AlertRule | None:
        """Récupérer une règle d'alerte."""
        return self.db.query(AlertRule).filter(
            AlertRule.id == rule_id,
            AlertRule.tenant_id == self.tenant_id
        ).first()

    def list_alert_rules(self, skip: int = 0, limit: int = 50) -> tuple[list[AlertRule], int]:
        """Lister les règles d'alerte."""
        query = self.db.query(AlertRule).filter(
            AlertRule.tenant_id == self.tenant_id
        )

        total = query.count()
        rules = query.order_by(AlertRule.name).offset(skip).limit(limit).all()

        return rules, total

    def update_alert_rule(self, rule_id: int, data: AlertRuleUpdate) -> AlertRule:
        """Mettre à jour une règle d'alerte."""
        rule = self.get_alert_rule(rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Règle non trouvée"
            )

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(rule, field, value)

        self.db.commit()
        self.db.refresh(rule)
        return rule

    def trigger_alert(self, data: AlertCreate) -> Alert:
        """Déclencher une alerte."""
        alert = Alert(
            tenant_id=self.tenant_id,
            rule_id=data.rule_id,
            title=data.title,
            message=data.message,
            severity=data.severity,
            source_type=data.source_type,
            source_id=data.source_id,
            source_value=data.source_value,
            threshold_value=data.threshold_value,
            context=data.context,
            link=data.link
        )

        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        # NOTE: Phase 2 - Envoi notifications via notification_service
        return alert

    def get_alert(self, alert_id: int) -> Alert | None:
        """Récupérer une alerte."""
        return self.db.query(Alert).filter(
            Alert.id == alert_id,
            Alert.tenant_id == self.tenant_id
        ).first()

    def list_alerts(
        self,
        status_filter: AlertStatus | None = None,
        severity: AlertSeverity | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[Alert], int]:
        """Lister les alertes."""
        query = self.db.query(Alert).filter(
            Alert.tenant_id == self.tenant_id
        )

        if status_filter:
            query = query.filter(Alert.status == status_filter)
        if severity:
            query = query.filter(Alert.severity == severity)

        total = query.count()
        alerts = query.order_by(desc(Alert.triggered_at)).offset(skip).limit(limit).all()

        return alerts, total

    def acknowledge_alert(self, alert_id: int, notes: str | None = None) -> Alert:
        """Acquitter une alerte."""
        alert = self.get_alert(alert_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alerte non trouvée"
            )

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = self.user_id

        self.db.commit()
        self.db.refresh(alert)
        return alert

    def resolve_alert(self, alert_id: int, resolution_notes: str) -> Alert:
        """Résoudre une alerte."""
        alert = self.get_alert(alert_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alerte non trouvée"
            )

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = self.user_id
        alert.resolution_notes = resolution_notes

        self.db.commit()
        self.db.refresh(alert)
        return alert

    def snooze_alert(self, alert_id: int, snooze_until: datetime) -> Alert:
        """Mettre en pause une alerte."""
        alert = self.get_alert(alert_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alerte non trouvée"
            )

        alert.status = AlertStatus.SNOOZED
        alert.snoozed_until = snooze_until

        self.db.commit()
        self.db.refresh(alert)
        return alert

    # ========================================================================
    # DATA SOURCES
    # ========================================================================

    def create_data_source(self, data: DataSourceCreate) -> DataSource:
        """Créer une source de données."""
        source = DataSource(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            source_type=data.source_type,
            connection_config=data.connection_config,
            schema_definition=data.schema_definition,
            refresh_frequency=data.refresh_frequency,
            cache_enabled=data.cache_enabled,
            cache_ttl_seconds=data.cache_ttl_seconds,
            is_encrypted=data.is_encrypted,
            allowed_roles=data.allowed_roles,
            created_by=self.user_id
        )

        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    def get_data_source(self, source_id: int) -> DataSource | None:
        """Récupérer une source de données."""
        return self.db.query(DataSource).filter(
            DataSource.id == source_id,
            DataSource.tenant_id == self.tenant_id
        ).first()

    def list_data_sources(
        self,
        source_type: DataSourceType | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[DataSource], int]:
        """Lister les sources de données."""
        query = self.db.query(DataSource).filter(
            DataSource.tenant_id == self.tenant_id,
            DataSource.is_active
        )

        if source_type:
            query = query.filter(DataSource.source_type == source_type)

        total = query.count()
        sources = query.order_by(DataSource.name).offset(skip).limit(limit).all()

        return sources, total

    def update_data_source(self, source_id: int, data: DataSourceUpdate) -> DataSource:
        """Mettre à jour une source de données."""
        source = self.get_data_source(source_id)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source non trouvée"
            )

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(source, field, value)

        self.db.commit()
        self.db.refresh(source)
        return source

    # ========================================================================
    # DATA QUERIES
    # ========================================================================

    def create_query(self, data: DataQueryCreate) -> DataQuery:
        """Créer une requête."""
        query_obj = DataQuery(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            data_source_id=data.data_source_id,
            query_type=data.query_type,
            query_text=data.query_text,
            parameters=data.parameters,
            result_columns=data.result_columns,
            cache_enabled=data.cache_enabled,
            cache_ttl_seconds=data.cache_ttl_seconds,
            created_by=self.user_id
        )

        self.db.add(query_obj)
        self.db.commit()
        self.db.refresh(query_obj)
        return query_obj

    def get_query(self, query_id: int) -> DataQuery | None:
        """Récupérer une requête."""
        return self.db.query(DataQuery).filter(
            DataQuery.id == query_id,
            DataQuery.tenant_id == self.tenant_id
        ).first()

    def list_queries(self, skip: int = 0, limit: int = 50) -> tuple[list[DataQuery], int]:
        """Lister les requêtes."""
        query = self.db.query(DataQuery).filter(
            DataQuery.tenant_id == self.tenant_id,
            DataQuery.is_active
        )

        total = query.count()
        queries = query.order_by(DataQuery.name).offset(skip).limit(limit).all()

        return queries, total

    # ========================================================================
    # BOOKMARKS
    # ========================================================================

    def create_bookmark(self, data: BookmarkCreate) -> Bookmark:
        """Créer un favori."""
        bookmark = Bookmark(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            item_type=data.item_type,
            item_id=data.item_id,
            item_name=data.item_name,
            folder=data.folder
        )

        self.db.add(bookmark)
        self.db.commit()
        self.db.refresh(bookmark)
        return bookmark

    def list_bookmarks(self, item_type: str | None = None) -> list[Bookmark]:
        """Lister les favoris de l'utilisateur."""
        query = self.db.query(Bookmark).filter(
            Bookmark.tenant_id == self.tenant_id,
            Bookmark.user_id == self.user_id
        )

        if item_type:
            query = query.filter(Bookmark.item_type == item_type)

        return query.order_by(Bookmark.folder, Bookmark.display_order).all()

    def delete_bookmark(self, bookmark_id: int) -> bool:
        """Supprimer un favori."""
        bookmark = self.db.query(Bookmark).filter(
            Bookmark.id == bookmark_id,
            Bookmark.user_id == self.user_id,
            Bookmark.tenant_id == self.tenant_id
        ).first()

        if not bookmark:
            return False

        self.db.delete(bookmark)
        self.db.commit()
        return True

    # ========================================================================
    # EXPORTS
    # ========================================================================

    def create_export(self, data: ExportRequest) -> ExportHistory:
        """Créer un export."""
        export = ExportHistory(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            export_type=data.export_type,
            item_type=data.item_type,
            item_id=data.item_id,
            format=data.format,
            file_name=data.filename,
            parameters=data.parameters,
            status=ReportStatus.PENDING
        )

        self.db.add(export)
        self.db.commit()
        self.db.refresh(export)

        # NOTE: Phase 2 - Export via Celery task en arrière-plan
        return export

    def get_export(self, export_id: int) -> ExportHistory | None:
        """Récupérer un export."""
        return self.db.query(ExportHistory).filter(
            ExportHistory.id == export_id,
            ExportHistory.user_id == self.user_id,
            ExportHistory.tenant_id == self.tenant_id
        ).first()

    def list_exports(self, skip: int = 0, limit: int = 20) -> list[ExportHistory]:
        """Lister les exports de l'utilisateur."""
        return self.db.query(ExportHistory).filter(
            ExportHistory.tenant_id == self.tenant_id,
            ExportHistory.user_id == self.user_id
        ).order_by(desc(ExportHistory.created_at)).offset(skip).limit(limit).all()

    # ========================================================================
    # OVERVIEW & STATS
    # ========================================================================

    def get_overview(self) -> dict[str, Any]:
        """Vue d'ensemble BI."""
        # Dashboards
        total_dashboards = self.db.query(Dashboard).filter(
            Dashboard.tenant_id == self.tenant_id,
            Dashboard.is_active
        ).count()

        recent_dashboards = self.db.query(Dashboard).filter(
            Dashboard.tenant_id == self.tenant_id,
            Dashboard.is_active
        ).order_by(desc(Dashboard.last_viewed_at)).limit(5).all()

        # Reports
        total_reports = self.db.query(Report).filter(
            Report.tenant_id == self.tenant_id,
            Report.is_active
        ).count()

        recent_executions = self.db.query(ReportExecution).filter(
            ReportExecution.tenant_id == self.tenant_id
        ).order_by(desc(ReportExecution.created_at)).limit(5).all()

        # KPIs
        total_kpis = self.db.query(KPIDefinition).filter(
            KPIDefinition.tenant_id == self.tenant_id,
            KPIDefinition.is_active
        ).count()

        # Alertes
        active_alerts = self.db.query(Alert).filter(
            Alert.tenant_id == self.tenant_id,
            Alert.status == AlertStatus.ACTIVE
        ).count()

        critical_alerts = self.db.query(Alert).filter(
            Alert.tenant_id == self.tenant_id,
            Alert.status == AlertStatus.ACTIVE,
            Alert.severity == AlertSeverity.CRITICAL
        ).count()

        # Data sources
        total_sources = self.db.query(DataSource).filter(
            DataSource.tenant_id == self.tenant_id,
            DataSource.is_active
        ).count()

        return {
            "dashboards": {
                "total": total_dashboards,
                "recent": [{"id": d.id, "name": d.name, "code": d.code} for d in recent_dashboards]
            },
            "reports": {
                "total": total_reports,
                "recent_executions": len(recent_executions)
            },
            "kpis": {
                "total": total_kpis
            },
            "alerts": {
                "active": active_alerts,
                "critical": critical_alerts
            },
            "data_sources": {
                "total": total_sources
            }
        }

    def get_dashboard_stats(self, dashboard_id: int) -> dict[str, Any]:
        """Statistiques d'un tableau de bord."""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return {}

        return {
            "dashboard_id": dashboard.id,
            "dashboard_name": dashboard.name,
            "widget_count": len(dashboard.widgets),
            "view_count": dashboard.view_count,
            "last_viewed_at": dashboard.last_viewed_at,
            "created_at": dashboard.created_at
        }


def get_bi_service(db: Session, tenant_id: str, user_id: int) -> BIService:
    """Factory pour créer un service BI."""
    return BIService(db=db, tenant_id=tenant_id, user_id=user_id)
