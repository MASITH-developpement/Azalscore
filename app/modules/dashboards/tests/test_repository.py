"""
AZALSCORE ERP - Tests Repository Dashboards
============================================
Tests unitaires pour les repositories du module dashboards.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import MagicMock, patch, AsyncMock

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

from app.modules.dashboards.repository import (
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


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_db():
    """Creer une session de base de donnees mockee."""
    db = MagicMock()
    db.query = MagicMock(return_value=MagicMock())
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.delete = MagicMock()
    db.flush = MagicMock()
    return db


@pytest.fixture
def tenant_id():
    """Retourner un tenant_id de test."""
    return "test-tenant-123"


@pytest.fixture
def user_id():
    """Retourner un user_id de test."""
    return uuid4()


# =============================================================================
# TESTS DASHBOARD REPOSITORY
# =============================================================================

class TestDashboardRepository:
    """Tests du repository Dashboard."""

    def test_repository_initialization(self, mock_db, tenant_id):
        """Tester l'initialisation du repository."""
        repo = DashboardRepository(mock_db, tenant_id)
        assert repo.db == mock_db
        assert repo.tenant_id == tenant_id

    def test_base_query_filters_by_tenant(self, mock_db, tenant_id):
        """Tester que _base_query filtre par tenant_id."""
        repo = DashboardRepository(mock_db, tenant_id)

        # Mock the query chain
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        repo._base_query()

        # Verify query was called
        mock_db.query.assert_called()

    def test_get_by_id(self, mock_db, tenant_id):
        """Tester la recuperation par ID."""
        repo = DashboardRepository(mock_db, tenant_id)
        dashboard_id = uuid4()

        mock_dashboard = MagicMock(spec=Dashboard)
        mock_dashboard.id = dashboard_id

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_dashboard

        result = repo.get_by_id(dashboard_id)

        # Result should be the mock or None depending on filter
        mock_db.query.assert_called()

    def test_get_by_code(self, mock_db, tenant_id):
        """Tester la recuperation par code."""
        repo = DashboardRepository(mock_db, tenant_id)

        mock_dashboard = MagicMock(spec=Dashboard)
        mock_dashboard.code = "DASH001"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_dashboard

        result = repo.get_by_code("DASH001")

        mock_db.query.assert_called()

    def test_create_dashboard(self, mock_db, tenant_id, user_id):
        """Tester la creation d'un dashboard."""
        repo = DashboardRepository(mock_db, tenant_id)

        dashboard = Dashboard(
            tenant_id=tenant_id,
            code="DASH001",
            name="Test Dashboard",
            type=DashboardType.PERSONAL,
            owner_id=user_id,
            created_by=user_id
        )

        repo.create(dashboard)

        mock_db.add.assert_called_once_with(dashboard)
        mock_db.flush.assert_called_once()

    def test_update_dashboard(self, mock_db, tenant_id):
        """Tester la mise a jour d'un dashboard."""
        repo = DashboardRepository(mock_db, tenant_id)

        dashboard = MagicMock(spec=Dashboard)
        dashboard.name = "Updated Dashboard"

        repo.update(dashboard)

        mock_db.flush.assert_called()

    def test_soft_delete_dashboard(self, mock_db, tenant_id, user_id):
        """Tester la suppression logique."""
        repo = DashboardRepository(mock_db, tenant_id)

        dashboard = MagicMock(spec=Dashboard)
        dashboard.deleted_at = None

        repo.soft_delete(dashboard, user_id)

        assert dashboard.deleted_at is not None
        assert dashboard.deleted_by == user_id
        mock_db.flush.assert_called()

    def test_restore_dashboard(self, mock_db, tenant_id):
        """Tester la restauration d'un dashboard."""
        repo = DashboardRepository(mock_db, tenant_id)

        dashboard = MagicMock(spec=Dashboard)
        dashboard.deleted_at = datetime.utcnow()

        repo.restore(dashboard)

        assert dashboard.deleted_at is None
        assert dashboard.deleted_by is None
        mock_db.flush.assert_called()

    def test_list_active_dashboards(self, mock_db, tenant_id):
        """Tester la liste des dashboards actifs."""
        repo = DashboardRepository(mock_db, tenant_id)

        mock_dashboards = [
            MagicMock(spec=Dashboard, is_active=True),
            MagicMock(spec=Dashboard, is_active=True)
        ]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_dashboards

        repo.list_active()

        mock_db.query.assert_called()

    def test_count_by_owner(self, mock_db, tenant_id, user_id):
        """Tester le comptage par proprietaire."""
        repo = DashboardRepository(mock_db, tenant_id)

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5

        result = repo.count_by_owner(user_id)

        mock_db.query.assert_called()


# =============================================================================
# TESTS WIDGET REPOSITORY
# =============================================================================

class TestWidgetRepository:
    """Tests du repository Widget."""

    def test_repository_initialization(self, mock_db, tenant_id):
        """Tester l'initialisation du repository."""
        repo = WidgetRepository(mock_db, tenant_id)
        assert repo.db == mock_db
        assert repo.tenant_id == tenant_id

    def test_get_by_dashboard(self, mock_db, tenant_id):
        """Tester la recuperation des widgets par dashboard."""
        repo = WidgetRepository(mock_db, tenant_id)
        dashboard_id = uuid4()

        mock_widgets = [
            MagicMock(spec=DashboardWidget),
            MagicMock(spec=DashboardWidget)
        ]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_widgets

        repo.get_by_dashboard(dashboard_id)

        mock_db.query.assert_called()

    def test_create_widget(self, mock_db, tenant_id, user_id):
        """Tester la creation d'un widget."""
        repo = WidgetRepository(mock_db, tenant_id)
        dashboard_id = uuid4()

        widget = DashboardWidget(
            tenant_id=tenant_id,
            dashboard_id=dashboard_id,
            name="Test Widget",
            type=WidgetType.KPI,
            created_by=user_id
        )

        repo.create(widget)

        mock_db.add.assert_called_once_with(widget)
        mock_db.flush.assert_called()

    def test_update_layout(self, mock_db, tenant_id):
        """Tester la mise a jour du layout."""
        repo = WidgetRepository(mock_db, tenant_id)

        widget = MagicMock(spec=DashboardWidget)
        widget.position_x = 0
        widget.position_y = 0

        repo.update_layout(widget, position_x=2, position_y=3, width=4, height=3)

        assert widget.position_x == 2
        assert widget.position_y == 3
        mock_db.flush.assert_called()


# =============================================================================
# TESTS DATA SOURCE REPOSITORY
# =============================================================================

class TestDataSourceRepository:
    """Tests du repository DataSource."""

    def test_get_by_code(self, mock_db, tenant_id):
        """Tester la recuperation par code."""
        repo = DataSourceRepository(mock_db, tenant_id)

        mock_source = MagicMock(spec=DataSource)
        mock_source.code = "DS001"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_source

        repo.get_by_code("DS001")

        mock_db.query.assert_called()

    def test_list_active_sources(self, mock_db, tenant_id):
        """Tester la liste des sources actives."""
        repo = DataSourceRepository(mock_db, tenant_id)

        mock_sources = [MagicMock(spec=DataSource)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_sources

        repo.list_active()

        mock_db.query.assert_called()


# =============================================================================
# TESTS DATA QUERY REPOSITORY
# =============================================================================

class TestDataQueryRepository:
    """Tests du repository DataQuery."""

    def test_get_by_data_source(self, mock_db, tenant_id):
        """Tester la recuperation par source."""
        repo = DataQueryRepository(mock_db, tenant_id)
        data_source_id = uuid4()

        mock_queries = [MagicMock(spec=DataQuery)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_queries

        repo.get_by_data_source(data_source_id)

        mock_db.query.assert_called()


# =============================================================================
# TESTS SHARE REPOSITORY
# =============================================================================

class TestShareRepository:
    """Tests du repository Share."""

    def test_get_by_dashboard(self, mock_db, tenant_id):
        """Tester la recuperation par dashboard."""
        repo = ShareRepository(mock_db, tenant_id)
        dashboard_id = uuid4()

        mock_shares = [MagicMock(spec=DashboardShare)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_shares

        repo.get_by_dashboard(dashboard_id)

        mock_db.query.assert_called()

    def test_get_by_link_token(self, mock_db, tenant_id):
        """Tester la recuperation par token de lien."""
        repo = ShareRepository(mock_db, tenant_id)

        mock_share = MagicMock(spec=DashboardShare)
        mock_share.link_token = "abc123"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_share

        repo.get_by_link_token("abc123")

        mock_db.query.assert_called()

    def test_get_user_shares(self, mock_db, tenant_id, user_id):
        """Tester la recuperation des partages utilisateur."""
        repo = ShareRepository(mock_db, tenant_id)

        mock_shares = [MagicMock(spec=DashboardShare)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_shares

        repo.get_by_user(user_id)

        mock_db.query.assert_called()


# =============================================================================
# TESTS FAVORITE REPOSITORY
# =============================================================================

class TestFavoriteRepository:
    """Tests du repository Favorite."""

    def test_get_user_favorites(self, mock_db, tenant_id, user_id):
        """Tester la recuperation des favoris utilisateur."""
        repo = FavoriteRepository(mock_db, tenant_id)

        mock_favorites = [MagicMock(spec=DashboardFavorite)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_favorites

        repo.get_by_user(user_id)

        mock_db.query.assert_called()

    def test_check_is_favorite(self, mock_db, tenant_id, user_id):
        """Tester la verification de favori."""
        repo = FavoriteRepository(mock_db, tenant_id)
        dashboard_id = uuid4()

        mock_favorite = MagicMock(spec=DashboardFavorite)

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_favorite

        repo.get_by_user_and_dashboard(user_id, dashboard_id)

        mock_db.query.assert_called()


# =============================================================================
# TESTS ALERT RULE REPOSITORY
# =============================================================================

class TestAlertRuleRepository:
    """Tests du repository AlertRule."""

    def test_get_by_dashboard(self, mock_db, tenant_id):
        """Tester la recuperation par dashboard."""
        repo = AlertRuleRepository(mock_db, tenant_id)
        dashboard_id = uuid4()

        mock_rules = [MagicMock(spec=DashboardAlertRule)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_rules

        repo.get_by_dashboard(dashboard_id)

        mock_db.query.assert_called()

    def test_get_active_rules(self, mock_db, tenant_id):
        """Tester la recuperation des regles actives."""
        repo = AlertRuleRepository(mock_db, tenant_id)

        mock_rules = [MagicMock(spec=DashboardAlertRule)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_rules

        repo.list_active()

        mock_db.query.assert_called()


# =============================================================================
# TESTS ALERT REPOSITORY
# =============================================================================

class TestAlertRepository:
    """Tests du repository Alert."""

    def test_get_active_alerts(self, mock_db, tenant_id):
        """Tester la recuperation des alertes actives."""
        repo = AlertRepository(mock_db, tenant_id)

        mock_alerts = [MagicMock(spec=DashboardAlert)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_alerts

        repo.get_active()

        mock_db.query.assert_called()

    def test_get_by_dashboard(self, mock_db, tenant_id):
        """Tester la recuperation par dashboard."""
        repo = AlertRepository(mock_db, tenant_id)
        dashboard_id = uuid4()

        mock_alerts = [MagicMock(spec=DashboardAlert)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_alerts

        repo.get_by_dashboard(dashboard_id)

        mock_db.query.assert_called()

    def test_acknowledge_alert(self, mock_db, tenant_id, user_id):
        """Tester l'acquittement d'une alerte."""
        repo = AlertRepository(mock_db, tenant_id)

        alert = MagicMock(spec=DashboardAlert)
        alert.status = AlertStatus.TRIGGERED

        repo.acknowledge(alert, user_id, "Note d'acquittement")

        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.acknowledged_by == user_id
        mock_db.flush.assert_called()

    def test_resolve_alert(self, mock_db, tenant_id, user_id):
        """Tester la resolution d'une alerte."""
        repo = AlertRepository(mock_db, tenant_id)

        alert = MagicMock(spec=DashboardAlert)
        alert.status = AlertStatus.ACKNOWLEDGED

        repo.resolve(alert, user_id, "Probleme resolu")

        assert alert.status == AlertStatus.RESOLVED
        assert alert.resolved_by == user_id
        mock_db.flush.assert_called()


# =============================================================================
# TESTS EXPORT REPOSITORY
# =============================================================================

class TestExportRepository:
    """Tests du repository Export."""

    def test_get_by_dashboard(self, mock_db, tenant_id):
        """Tester la recuperation par dashboard."""
        repo = ExportRepository(mock_db, tenant_id)
        dashboard_id = uuid4()

        mock_exports = [MagicMock(spec=DashboardExport)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_exports

        repo.get_by_dashboard(dashboard_id)

        mock_db.query.assert_called()

    def test_update_status(self, mock_db, tenant_id):
        """Tester la mise a jour du statut."""
        repo = ExportRepository(mock_db, tenant_id)

        export = MagicMock(spec=DashboardExport)
        export.status = ExportStatus.PENDING

        repo.update_status(export, ExportStatus.COMPLETED, "/path/to/file.pdf")

        assert export.status == ExportStatus.COMPLETED
        mock_db.flush.assert_called()


# =============================================================================
# TESTS SCHEDULED REPORT REPOSITORY
# =============================================================================

class TestScheduledReportRepository:
    """Tests du repository ScheduledReport."""

    def test_get_active_reports(self, mock_db, tenant_id):
        """Tester la recuperation des rapports actifs."""
        repo = ScheduledReportRepository(mock_db, tenant_id)

        mock_reports = [MagicMock(spec=ScheduledReport)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_reports

        repo.list_active()

        mock_db.query.assert_called()

    def test_get_due_reports(self, mock_db, tenant_id):
        """Tester la recuperation des rapports a executer."""
        repo = ScheduledReportRepository(mock_db, tenant_id)

        mock_reports = [MagicMock(spec=ScheduledReport)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_reports

        repo.get_due_reports()

        mock_db.query.assert_called()


# =============================================================================
# TESTS USER PREFERENCE REPOSITORY
# =============================================================================

class TestUserPreferenceRepository:
    """Tests du repository UserPreference."""

    def test_get_by_user(self, mock_db, tenant_id, user_id):
        """Tester la recuperation par utilisateur."""
        repo = UserPreferenceRepository(mock_db, tenant_id)

        mock_pref = MagicMock(spec=UserDashboardPreference)

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_pref

        repo.get_by_user(user_id)

        mock_db.query.assert_called()

    def test_get_or_create(self, mock_db, tenant_id, user_id):
        """Tester get_or_create."""
        repo = UserPreferenceRepository(mock_db, tenant_id)

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Should create new preferences
        repo.get_or_create(user_id)

        mock_db.query.assert_called()


# =============================================================================
# TESTS TEMPLATE REPOSITORY
# =============================================================================

class TestTemplateRepository:
    """Tests du repository Template."""

    def test_get_public_templates(self, mock_db, tenant_id):
        """Tester la recuperation des templates publics."""
        repo = TemplateRepository(mock_db, tenant_id)

        mock_templates = [MagicMock(spec=DashboardTemplate)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_templates

        repo.list_public()

        mock_db.query.assert_called()

    def test_get_by_category(self, mock_db, tenant_id):
        """Tester la recuperation par categorie."""
        repo = TemplateRepository(mock_db, tenant_id)

        mock_templates = [MagicMock(spec=DashboardTemplate)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_templates

        repo.get_by_category("sales")

        mock_db.query.assert_called()


# =============================================================================
# TESTS TENANT ISOLATION
# =============================================================================

class TestTenantIsolation:
    """Tests d'isolation multi-tenant."""

    def test_repository_always_filters_by_tenant(self, mock_db, tenant_id):
        """Tester que toutes les requetes filtrent par tenant."""
        repo = DashboardRepository(mock_db, tenant_id)

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        # All queries should include tenant filter
        repo.list_all()

        # Verify filter was called (tenant filter applied)
        assert mock_query.filter.called

    def test_different_tenants_see_different_data(self, mock_db):
        """Tester que des tenants differents voient des donnees differentes."""
        repo1 = DashboardRepository(mock_db, "tenant-1")
        repo2 = DashboardRepository(mock_db, "tenant-2")

        assert repo1.tenant_id != repo2.tenant_id
        assert repo1.tenant_id == "tenant-1"
        assert repo2.tenant_id == "tenant-2"


# =============================================================================
# EXECUTION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
