"""
AZALSCORE ERP - Tests Service Dashboards
=========================================
Tests unitaires pour le service du module dashboards.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import MagicMock, patch, PropertyMock

from app.modules.dashboards.models import (
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

from app.modules.dashboards.schemas import (
    DashboardCreate,
    DashboardUpdate,
    DashboardFilters,
    WidgetCreate,
    WidgetUpdate,
    WidgetLayoutUpdate,
    DataSourceCreate,
    DataQueryCreate,
    ShareCreate,
    FavoriteCreate,
    AlertRuleCreate,
    AlertAcknowledge,
    AlertResolve,
    AlertSnooze,
    ExportRequest,
    ScheduledReportCreate,
    UserPreferenceCreate,
    TemplateCreate,
)

from app.modules.dashboards.service import DashboardService

from app.modules.dashboards.exceptions import (
    DashboardNotFoundError,
    DashboardAccessDeniedError,
    DashboardCodeExistsError,
    WidgetNotFoundError,
    DataSourceNotFoundError,
    ShareNotFoundError,
    AlertNotFoundError,
    AlertAlreadyResolvedError,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_db():
    """Creer une session de base de donnees mockee."""
    db = MagicMock()
    return db


@pytest.fixture
def mock_context():
    """Creer un contexte SaaS mocke."""
    context = MagicMock()
    context.tenant_id = "test-tenant"
    context.user_id = uuid4()
    context.user_roles = ["admin"]
    return context


@pytest.fixture
def service(mock_db, mock_context):
    """Creer une instance du service."""
    return DashboardService(mock_db, mock_context)


# =============================================================================
# TESTS DU SERVICE - DASHBOARDS
# =============================================================================

class TestDashboardServiceDashboards:
    """Tests du service - Tableaux de bord."""

    def test_service_initialization(self, mock_db, mock_context):
        """Tester l'initialisation du service."""
        service = DashboardService(mock_db, mock_context)
        assert service.db == mock_db
        assert service.context == mock_context

    def test_create_dashboard_success(self, service):
        """Tester la creation d'un dashboard."""
        data = DashboardCreate(
            code="DASH001",
            name="Dashboard Test",
            type=DashboardType.PERSONAL
        )

        # Mock repository
        with patch.object(service, '_dashboard_repo', create=True) as mock_repo:
            mock_repo.get_by_code.return_value = None
            mock_repo.create.return_value = None

            # Mock the property
            type(service)._dashboard_repo = PropertyMock(return_value=mock_repo)

            # Should not raise
            result = service.create_dashboard(data)

    def test_create_dashboard_code_exists(self, service):
        """Tester la creation avec code existant."""
        data = DashboardCreate(
            code="DASH001",
            name="Dashboard Test",
            type=DashboardType.PERSONAL
        )

        # Mock existing dashboard
        existing = MagicMock(spec=Dashboard)
        existing.code = "DASH001"

        with patch.object(service, '_dashboard_repo', create=True) as mock_repo:
            mock_repo.get_by_code.return_value = existing
            type(service)._dashboard_repo = PropertyMock(return_value=mock_repo)

            result = service.create_dashboard(data)

            # Should return error result
            assert not result.is_success or result.error is not None

    def test_get_dashboard_success(self, service):
        """Tester la recuperation d'un dashboard."""
        dashboard_id = uuid4()

        mock_dashboard = MagicMock(spec=Dashboard)
        mock_dashboard.id = dashboard_id
        mock_dashboard.owner_id = service.context.user_id
        mock_dashboard.type = DashboardType.PERSONAL

        with patch.object(service, '_dashboard_repo', create=True) as mock_repo:
            mock_repo.get_by_id.return_value = mock_dashboard
            type(service)._dashboard_repo = PropertyMock(return_value=mock_repo)

            result = service.get_dashboard(dashboard_id)

    def test_get_dashboard_not_found(self, service):
        """Tester recuperation dashboard inexistant."""
        dashboard_id = uuid4()

        with patch.object(service, '_dashboard_repo', create=True) as mock_repo:
            mock_repo.get_by_id.return_value = None
            type(service)._dashboard_repo = PropertyMock(return_value=mock_repo)

            result = service.get_dashboard(dashboard_id)

            # Should return error
            assert not result.is_success or result.value is None

    def test_update_dashboard(self, service):
        """Tester la mise a jour d'un dashboard."""
        dashboard_id = uuid4()
        data = DashboardUpdate(name="Nouveau nom")

        mock_dashboard = MagicMock(spec=Dashboard)
        mock_dashboard.id = dashboard_id
        mock_dashboard.owner_id = service.context.user_id
        mock_dashboard.type = DashboardType.PERSONAL

        with patch.object(service, '_dashboard_repo', create=True) as mock_repo:
            mock_repo.get_by_id.return_value = mock_dashboard
            mock_repo.update.return_value = None
            type(service)._dashboard_repo = PropertyMock(return_value=mock_repo)

            result = service.update_dashboard(dashboard_id, data)

    def test_delete_dashboard(self, service):
        """Tester la suppression d'un dashboard."""
        dashboard_id = uuid4()

        mock_dashboard = MagicMock(spec=Dashboard)
        mock_dashboard.id = dashboard_id
        mock_dashboard.owner_id = service.context.user_id
        mock_dashboard.type = DashboardType.PERSONAL

        with patch.object(service, '_dashboard_repo', create=True) as mock_repo:
            mock_repo.get_by_id.return_value = mock_dashboard
            mock_repo.soft_delete.return_value = None
            type(service)._dashboard_repo = PropertyMock(return_value=mock_repo)

            result = service.delete_dashboard(dashboard_id)

    def test_restore_dashboard(self, service):
        """Tester la restauration d'un dashboard."""
        dashboard_id = uuid4()

        mock_dashboard = MagicMock(spec=Dashboard)
        mock_dashboard.id = dashboard_id
        mock_dashboard.deleted_at = datetime.utcnow()
        mock_dashboard.owner_id = service.context.user_id

        with patch.object(service, '_dashboard_repo', create=True) as mock_repo:
            mock_repo.get_by_id_include_deleted.return_value = mock_dashboard
            mock_repo.restore.return_value = None
            type(service)._dashboard_repo = PropertyMock(return_value=mock_repo)

            result = service.restore_dashboard(dashboard_id)

    def test_list_dashboards(self, service):
        """Tester la liste des dashboards."""
        filters = DashboardFilters(type=DashboardType.OPERATIONAL)

        mock_dashboards = [
            MagicMock(spec=Dashboard),
            MagicMock(spec=Dashboard)
        ]

        with patch.object(service, '_dashboard_repo', create=True) as mock_repo:
            mock_repo.list_filtered.return_value = mock_dashboards
            mock_repo.count_filtered.return_value = 2
            type(service)._dashboard_repo = PropertyMock(return_value=mock_repo)

            result = service.list_dashboards(filters)

    def test_duplicate_dashboard(self, service):
        """Tester la duplication d'un dashboard."""
        dashboard_id = uuid4()

        mock_dashboard = MagicMock(spec=Dashboard)
        mock_dashboard.id = dashboard_id
        mock_dashboard.code = "DASH001"
        mock_dashboard.name = "Dashboard Original"
        mock_dashboard.type = DashboardType.PERSONAL
        mock_dashboard.owner_id = service.context.user_id
        mock_dashboard.widgets = []

        with patch.object(service, '_dashboard_repo', create=True) as mock_repo:
            mock_repo.get_by_id.return_value = mock_dashboard
            mock_repo.get_by_code.return_value = None
            mock_repo.create.return_value = None
            type(service)._dashboard_repo = PropertyMock(return_value=mock_repo)

            result = service.duplicate_dashboard(dashboard_id, "DASH002", "Dashboard Copie")


# =============================================================================
# TESTS DU SERVICE - WIDGETS
# =============================================================================

class TestDashboardServiceWidgets:
    """Tests du service - Widgets."""

    def test_add_widget(self, service):
        """Tester l'ajout d'un widget."""
        dashboard_id = uuid4()
        data = WidgetCreate(
            name="Widget Test",
            type=WidgetType.KPI
        )

        mock_dashboard = MagicMock(spec=Dashboard)
        mock_dashboard.id = dashboard_id
        mock_dashboard.owner_id = service.context.user_id
        mock_dashboard.type = DashboardType.PERSONAL

        with patch.object(service, '_dashboard_repo', create=True) as mock_dash_repo:
            with patch.object(service, '_widget_repo', create=True) as mock_widget_repo:
                mock_dash_repo.get_by_id.return_value = mock_dashboard
                mock_widget_repo.create.return_value = None
                type(service)._dashboard_repo = PropertyMock(return_value=mock_dash_repo)
                type(service)._widget_repo = PropertyMock(return_value=mock_widget_repo)

                result = service.add_widget(dashboard_id, data)

    def test_update_widget(self, service):
        """Tester la mise a jour d'un widget."""
        widget_id = uuid4()
        data = WidgetUpdate(name="Nouveau titre")

        mock_widget = MagicMock(spec=DashboardWidget)
        mock_widget.id = widget_id

        mock_dashboard = MagicMock(spec=Dashboard)
        mock_dashboard.owner_id = service.context.user_id
        mock_dashboard.type = DashboardType.PERSONAL
        mock_widget.dashboard = mock_dashboard

        with patch.object(service, '_widget_repo', create=True) as mock_repo:
            mock_repo.get_by_id.return_value = mock_widget
            mock_repo.update.return_value = None
            type(service)._widget_repo = PropertyMock(return_value=mock_repo)

            result = service.update_widget(widget_id, data)

    def test_delete_widget(self, service):
        """Tester la suppression d'un widget."""
        widget_id = uuid4()

        mock_widget = MagicMock(spec=DashboardWidget)
        mock_widget.id = widget_id

        mock_dashboard = MagicMock(spec=Dashboard)
        mock_dashboard.owner_id = service.context.user_id
        mock_dashboard.type = DashboardType.PERSONAL
        mock_widget.dashboard = mock_dashboard

        with patch.object(service, '_widget_repo', create=True) as mock_repo:
            mock_repo.get_by_id.return_value = mock_widget
            mock_repo.soft_delete.return_value = None
            type(service)._widget_repo = PropertyMock(return_value=mock_repo)

            result = service.delete_widget(widget_id)

    def test_update_widget_layout(self, service):
        """Tester la mise a jour du layout."""
        dashboard_id = uuid4()
        layouts = [
            WidgetLayoutUpdate(
                widget_id=uuid4(),
                position_x=0,
                position_y=0,
                width=4,
                height=3
            )
        ]

        mock_dashboard = MagicMock(spec=Dashboard)
        mock_dashboard.id = dashboard_id
        mock_dashboard.owner_id = service.context.user_id
        mock_dashboard.type = DashboardType.PERSONAL

        with patch.object(service, '_dashboard_repo', create=True) as mock_dash_repo:
            with patch.object(service, '_widget_repo', create=True) as mock_widget_repo:
                mock_dash_repo.get_by_id.return_value = mock_dashboard
                type(service)._dashboard_repo = PropertyMock(return_value=mock_dash_repo)
                type(service)._widget_repo = PropertyMock(return_value=mock_widget_repo)

                result = service.update_widget_layout(dashboard_id, layouts)


# =============================================================================
# TESTS DU SERVICE - DATA SOURCES
# =============================================================================

class TestDashboardServiceDataSources:
    """Tests du service - Sources de donnees."""

    def test_create_data_source(self, service):
        """Tester la creation d'une source."""
        data = DataSourceCreate(
            code="DS001",
            name="Source Test",
            type=DataSourceType.DATABASE
        )

        with patch.object(service, '_data_source_repo', create=True) as mock_repo:
            mock_repo.get_by_code.return_value = None
            mock_repo.create.return_value = None
            type(service)._data_source_repo = PropertyMock(return_value=mock_repo)

            result = service.create_data_source(data)

    def test_list_data_sources(self, service):
        """Tester la liste des sources."""
        mock_sources = [MagicMock(spec=DataSource)]

        with patch.object(service, '_data_source_repo', create=True) as mock_repo:
            mock_repo.list_active.return_value = mock_sources
            type(service)._data_source_repo = PropertyMock(return_value=mock_repo)

            result = service.list_data_sources()


# =============================================================================
# TESTS DU SERVICE - SHARES
# =============================================================================

class TestDashboardServiceShares:
    """Tests du service - Partages."""

    def test_share_dashboard_with_user(self, service):
        """Tester le partage avec un utilisateur."""
        dashboard_id = uuid4()
        data = ShareCreate(
            shared_with_user=uuid4(),
            permission=SharePermission.VIEW
        )

        mock_dashboard = MagicMock(spec=Dashboard)
        mock_dashboard.id = dashboard_id
        mock_dashboard.owner_id = service.context.user_id
        mock_dashboard.type = DashboardType.PERSONAL

        with patch.object(service, '_dashboard_repo', create=True) as mock_dash_repo:
            with patch.object(service, '_share_repo', create=True) as mock_share_repo:
                mock_dash_repo.get_by_id.return_value = mock_dashboard
                mock_share_repo.create.return_value = None
                type(service)._dashboard_repo = PropertyMock(return_value=mock_dash_repo)
                type(service)._share_repo = PropertyMock(return_value=mock_share_repo)

                result = service.share_dashboard(dashboard_id, data)

    def test_share_with_public_link(self, service):
        """Tester le partage par lien public."""
        dashboard_id = uuid4()
        data = ShareCreate(
            permission=SharePermission.VIEW,
            is_public_link=True
        )

        mock_dashboard = MagicMock(spec=Dashboard)
        mock_dashboard.id = dashboard_id
        mock_dashboard.owner_id = service.context.user_id
        mock_dashboard.type = DashboardType.PERSONAL

        with patch.object(service, '_dashboard_repo', create=True) as mock_dash_repo:
            with patch.object(service, '_share_repo', create=True) as mock_share_repo:
                mock_dash_repo.get_by_id.return_value = mock_dashboard
                mock_share_repo.create.return_value = None
                type(service)._dashboard_repo = PropertyMock(return_value=mock_dash_repo)
                type(service)._share_repo = PropertyMock(return_value=mock_share_repo)

                result = service.share_dashboard(dashboard_id, data)

    def test_revoke_share(self, service):
        """Tester la revocation d'un partage."""
        share_id = uuid4()

        mock_share = MagicMock(spec=DashboardShare)
        mock_share.id = share_id
        mock_share.shared_by = service.context.user_id

        with patch.object(service, '_share_repo', create=True) as mock_repo:
            mock_repo.get_by_id.return_value = mock_share
            mock_repo.soft_delete.return_value = None
            type(service)._share_repo = PropertyMock(return_value=mock_repo)

            result = service.revoke_share(share_id)


# =============================================================================
# TESTS DU SERVICE - FAVORITES
# =============================================================================

class TestDashboardServiceFavorites:
    """Tests du service - Favoris."""

    def test_add_to_favorites(self, service):
        """Tester l'ajout aux favoris."""
        dashboard_id = uuid4()
        data = FavoriteCreate(dashboard_id=dashboard_id)

        mock_dashboard = MagicMock(spec=Dashboard)
        mock_dashboard.id = dashboard_id

        with patch.object(service, '_dashboard_repo', create=True) as mock_dash_repo:
            with patch.object(service, '_favorite_repo', create=True) as mock_fav_repo:
                mock_dash_repo.get_by_id.return_value = mock_dashboard
                mock_fav_repo.get_by_user_and_dashboard.return_value = None
                mock_fav_repo.create.return_value = None
                type(service)._dashboard_repo = PropertyMock(return_value=mock_dash_repo)
                type(service)._favorite_repo = PropertyMock(return_value=mock_fav_repo)

                result = service.add_to_favorites(data)

    def test_remove_from_favorites(self, service):
        """Tester le retrait des favoris."""
        dashboard_id = uuid4()

        mock_favorite = MagicMock(spec=DashboardFavorite)
        mock_favorite.user_id = service.context.user_id

        with patch.object(service, '_favorite_repo', create=True) as mock_repo:
            mock_repo.get_by_user_and_dashboard.return_value = mock_favorite
            mock_repo.delete.return_value = None
            type(service)._favorite_repo = PropertyMock(return_value=mock_repo)

            result = service.remove_from_favorites(dashboard_id)

    def test_toggle_favorite(self, service):
        """Tester le basculement favori."""
        dashboard_id = uuid4()

        with patch.object(service, '_favorite_repo', create=True) as mock_fav_repo:
            with patch.object(service, '_dashboard_repo', create=True) as mock_dash_repo:
                mock_fav_repo.get_by_user_and_dashboard.return_value = None
                mock_dash_repo.get_by_id.return_value = MagicMock(spec=Dashboard)
                type(service)._favorite_repo = PropertyMock(return_value=mock_fav_repo)
                type(service)._dashboard_repo = PropertyMock(return_value=mock_dash_repo)

                result = service.toggle_favorite(dashboard_id)

    def test_list_favorites(self, service):
        """Tester la liste des favoris."""
        mock_favorites = [MagicMock(spec=DashboardFavorite)]

        with patch.object(service, '_favorite_repo', create=True) as mock_repo:
            mock_repo.get_by_user.return_value = mock_favorites
            type(service)._favorite_repo = PropertyMock(return_value=mock_repo)

            result = service.list_favorites()


# =============================================================================
# TESTS DU SERVICE - ALERTS
# =============================================================================

class TestDashboardServiceAlerts:
    """Tests du service - Alertes."""

    def test_create_alert_rule(self, service):
        """Tester la creation d'une regle d'alerte."""
        dashboard_id = uuid4()
        data = AlertRuleCreate(
            code="RULE001",
            name="Alerte Test",
            metric_name="total_sales",
            operator=AlertOperator.LESS_THAN,
            threshold_value=Decimal("10000"),
            severity=AlertSeverity.WARNING
        )

        mock_dashboard = MagicMock(spec=Dashboard)
        mock_dashboard.id = dashboard_id
        mock_dashboard.owner_id = service.context.user_id
        mock_dashboard.type = DashboardType.PERSONAL

        with patch.object(service, '_dashboard_repo', create=True) as mock_dash_repo:
            with patch.object(service, '_alert_rule_repo', create=True) as mock_rule_repo:
                mock_dash_repo.get_by_id.return_value = mock_dashboard
                mock_rule_repo.get_by_code.return_value = None
                mock_rule_repo.create.return_value = None
                type(service)._dashboard_repo = PropertyMock(return_value=mock_dash_repo)
                type(service)._alert_rule_repo = PropertyMock(return_value=mock_rule_repo)

                result = service.create_alert_rule(dashboard_id, data)

    def test_acknowledge_alert(self, service):
        """Tester l'acquittement d'une alerte."""
        alert_id = uuid4()
        data = AlertAcknowledge(note="Pris en compte")

        mock_alert = MagicMock(spec=DashboardAlert)
        mock_alert.id = alert_id
        mock_alert.status = AlertStatus.TRIGGERED

        with patch.object(service, '_alert_repo', create=True) as mock_repo:
            mock_repo.get_by_id.return_value = mock_alert
            mock_repo.acknowledge.return_value = None
            type(service)._alert_repo = PropertyMock(return_value=mock_repo)

            result = service.acknowledge_alert(alert_id, data)

    def test_resolve_alert(self, service):
        """Tester la resolution d'une alerte."""
        alert_id = uuid4()
        data = AlertResolve(resolution_note="Probleme resolu")

        mock_alert = MagicMock(spec=DashboardAlert)
        mock_alert.id = alert_id
        mock_alert.status = AlertStatus.ACKNOWLEDGED

        with patch.object(service, '_alert_repo', create=True) as mock_repo:
            mock_repo.get_by_id.return_value = mock_alert
            mock_repo.resolve.return_value = None
            type(service)._alert_repo = PropertyMock(return_value=mock_repo)

            result = service.resolve_alert(alert_id, data)

    def test_resolve_already_resolved_alert(self, service):
        """Tester resolution d'alerte deja resolue."""
        alert_id = uuid4()
        data = AlertResolve(resolution_note="Tentative")

        mock_alert = MagicMock(spec=DashboardAlert)
        mock_alert.id = alert_id
        mock_alert.status = AlertStatus.RESOLVED

        with patch.object(service, '_alert_repo', create=True) as mock_repo:
            mock_repo.get_by_id.return_value = mock_alert
            type(service)._alert_repo = PropertyMock(return_value=mock_repo)

            result = service.resolve_alert(alert_id, data)

            # Should return error

    def test_snooze_alert(self, service):
        """Tester la mise en veille d'une alerte."""
        alert_id = uuid4()
        snooze_until = datetime.utcnow() + timedelta(hours=2)
        data = AlertSnooze(snooze_until=snooze_until)

        mock_alert = MagicMock(spec=DashboardAlert)
        mock_alert.id = alert_id
        mock_alert.status = AlertStatus.TRIGGERED

        with patch.object(service, '_alert_repo', create=True) as mock_repo:
            mock_repo.get_by_id.return_value = mock_alert
            mock_repo.snooze.return_value = None
            type(service)._alert_repo = PropertyMock(return_value=mock_repo)

            result = service.snooze_alert(alert_id, data)


# =============================================================================
# TESTS DU SERVICE - EXPORTS
# =============================================================================

class TestDashboardServiceExports:
    """Tests du service - Exports."""

    def test_request_export_pdf(self, service):
        """Tester la demande d'export PDF."""
        dashboard_id = uuid4()
        data = ExportRequest(format=ExportFormat.PDF)

        mock_dashboard = MagicMock(spec=Dashboard)
        mock_dashboard.id = dashboard_id
        mock_dashboard.owner_id = service.context.user_id
        mock_dashboard.type = DashboardType.PERSONAL

        with patch.object(service, '_dashboard_repo', create=True) as mock_dash_repo:
            with patch.object(service, '_export_repo', create=True) as mock_export_repo:
                mock_dash_repo.get_by_id.return_value = mock_dashboard
                mock_export_repo.create.return_value = None
                type(service)._dashboard_repo = PropertyMock(return_value=mock_dash_repo)
                type(service)._export_repo = PropertyMock(return_value=mock_export_repo)

                result = service.request_export(dashboard_id, data)

    def test_get_export_status(self, service):
        """Tester la recuperation du statut d'export."""
        export_id = uuid4()

        mock_export = MagicMock(spec=DashboardExport)
        mock_export.id = export_id
        mock_export.status = ExportStatus.COMPLETED

        with patch.object(service, '_export_repo', create=True) as mock_repo:
            mock_repo.get_by_id.return_value = mock_export
            type(service)._export_repo = PropertyMock(return_value=mock_repo)

            result = service.get_export(export_id)


# =============================================================================
# TESTS DU SERVICE - SCHEDULED REPORTS
# =============================================================================

class TestDashboardServiceScheduledReports:
    """Tests du service - Rapports planifies."""

    def test_create_scheduled_report(self, service):
        """Tester la creation d'un rapport planifie."""
        dashboard_id = uuid4()
        data = ScheduledReportCreate(
            code="SCHD001",
            name="Rapport Test",
            cron_expression="0 8 * * *",
            format=ExportFormat.PDF,
            recipients=["test@example.com"]
        )

        mock_dashboard = MagicMock(spec=Dashboard)
        mock_dashboard.id = dashboard_id
        mock_dashboard.owner_id = service.context.user_id
        mock_dashboard.type = DashboardType.PERSONAL

        with patch.object(service, '_dashboard_repo', create=True) as mock_dash_repo:
            with patch.object(service, '_scheduled_report_repo', create=True) as mock_report_repo:
                mock_dash_repo.get_by_id.return_value = mock_dashboard
                mock_report_repo.get_by_code.return_value = None
                mock_report_repo.create.return_value = None
                type(service)._dashboard_repo = PropertyMock(return_value=mock_dash_repo)
                type(service)._scheduled_report_repo = PropertyMock(return_value=mock_report_repo)

                result = service.create_scheduled_report(dashboard_id, data)

    def test_list_scheduled_reports(self, service):
        """Tester la liste des rapports planifies."""
        dashboard_id = uuid4()

        mock_reports = [MagicMock(spec=ScheduledReport)]

        with patch.object(service, '_scheduled_report_repo', create=True) as mock_repo:
            mock_repo.get_by_dashboard.return_value = mock_reports
            type(service)._scheduled_report_repo = PropertyMock(return_value=mock_repo)

            result = service.list_scheduled_reports(dashboard_id)


# =============================================================================
# TESTS DU SERVICE - USER PREFERENCES
# =============================================================================

class TestDashboardServiceUserPreferences:
    """Tests du service - Preferences utilisateur."""

    def test_get_user_preferences(self, service):
        """Tester la recuperation des preferences."""
        mock_prefs = MagicMock(spec=UserDashboardPreference)
        mock_prefs.theme = "dark"

        with patch.object(service, '_user_preference_repo', create=True) as mock_repo:
            mock_repo.get_or_create.return_value = mock_prefs
            type(service)._user_preference_repo = PropertyMock(return_value=mock_repo)

            result = service.get_user_preferences()

    def test_update_user_preferences(self, service):
        """Tester la mise a jour des preferences."""
        data = UserPreferenceCreate(theme="light")

        mock_prefs = MagicMock(spec=UserDashboardPreference)

        with patch.object(service, '_user_preference_repo', create=True) as mock_repo:
            mock_repo.get_or_create.return_value = mock_prefs
            mock_repo.update.return_value = None
            type(service)._user_preference_repo = PropertyMock(return_value=mock_repo)

            result = service.update_user_preferences(data)


# =============================================================================
# TESTS DU SERVICE - TEMPLATES
# =============================================================================

class TestDashboardServiceTemplates:
    """Tests du service - Templates."""

    def test_list_templates(self, service):
        """Tester la liste des templates."""
        mock_templates = [MagicMock(spec=DashboardTemplate)]

        with patch.object(service, '_template_repo', create=True) as mock_repo:
            mock_repo.list_public.return_value = mock_templates
            type(service)._template_repo = PropertyMock(return_value=mock_repo)

            result = service.list_templates()

    def test_create_from_template(self, service):
        """Tester la creation depuis template."""
        template_id = uuid4()

        mock_template = MagicMock(spec=DashboardTemplate)
        mock_template.id = template_id
        mock_template.code = "TMPL001"
        mock_template.name = "Template Test"
        mock_template.type = DashboardType.OPERATIONAL
        mock_template.widget_config = []

        with patch.object(service, '_template_repo', create=True) as mock_tmpl_repo:
            with patch.object(service, '_dashboard_repo', create=True) as mock_dash_repo:
                mock_tmpl_repo.get_by_id.return_value = mock_template
                mock_dash_repo.get_by_code.return_value = None
                mock_dash_repo.create.return_value = None
                type(service)._template_repo = PropertyMock(return_value=mock_tmpl_repo)
                type(service)._dashboard_repo = PropertyMock(return_value=mock_dash_repo)

                result = service.create_from_template(template_id, "DASH001", "Dashboard depuis template")


# =============================================================================
# TESTS PERMISSION ET ACCES
# =============================================================================

class TestDashboardServicePermissions:
    """Tests des permissions et acces."""

    def test_owner_can_access_personal_dashboard(self, service):
        """Tester que le proprietaire peut acceder a son dashboard."""
        dashboard = MagicMock(spec=Dashboard)
        dashboard.type = DashboardType.PERSONAL
        dashboard.owner_id = service.context.user_id

        # Should not raise
        assert service._can_access_dashboard(dashboard, "view")

    def test_non_owner_cannot_access_personal_dashboard(self, service):
        """Tester qu'un non-proprietaire ne peut pas acceder."""
        dashboard = MagicMock(spec=Dashboard)
        dashboard.type = DashboardType.PERSONAL
        dashboard.owner_id = uuid4()  # Different user

        # Mock shares
        with patch.object(service, '_share_repo', create=True) as mock_repo:
            mock_repo.get_user_permission.return_value = None
            type(service)._share_repo = PropertyMock(return_value=mock_repo)

            # Should return False
            assert not service._can_access_dashboard(dashboard, "view")

    def test_admin_can_access_organization_dashboard(self, service):
        """Tester qu'un admin peut acceder aux dashboards organisation."""
        dashboard = MagicMock(spec=Dashboard)
        dashboard.type = DashboardType.ORGANIZATION
        dashboard.allowed_roles = []

        service.context.user_roles = ["admin"]

        assert service._can_access_dashboard(dashboard, "view")


# =============================================================================
# EXECUTION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
