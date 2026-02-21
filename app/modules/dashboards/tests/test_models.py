"""
AZALSCORE ERP - Tests Modeles Dashboards
=========================================
Tests unitaires pour les modeles SQLAlchemy du module dashboards.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

from app.modules.dashboards.models import (
    # Enumerations
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
    # Models
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


# =============================================================================
# TESTS DES ENUMERATIONS
# =============================================================================

class TestEnums:
    """Tests des enumerations."""

    def test_dashboard_type_values(self):
        """Tester les types de tableau de bord."""
        assert DashboardType.PERSONAL.value == "PERSONAL"
        assert DashboardType.TEAM.value == "TEAM"
        assert DashboardType.DEPARTMENT.value == "DEPARTMENT"
        assert DashboardType.ORGANIZATION.value == "ORGANIZATION"
        assert DashboardType.ROLE_BASED.value == "ROLE_BASED"
        assert DashboardType.EXECUTIVE.value == "EXECUTIVE"
        assert DashboardType.OPERATIONAL.value == "OPERATIONAL"
        assert DashboardType.ANALYTICAL.value == "ANALYTICAL"
        assert len(DashboardType) >= 8

    def test_widget_type_values(self):
        """Tester les types de widget."""
        assert WidgetType.KPI.value == "KPI"
        assert WidgetType.CHART.value == "CHART"
        assert WidgetType.TABLE.value == "TABLE"
        assert WidgetType.LIST.value == "LIST"
        assert WidgetType.MAP.value == "MAP"
        assert WidgetType.GAUGE.value == "GAUGE"
        assert WidgetType.PROGRESS.value == "PROGRESS"
        assert WidgetType.METRIC.value == "METRIC"
        assert WidgetType.TEXT.value == "TEXT"
        assert WidgetType.IMAGE.value == "IMAGE"
        assert WidgetType.IFRAME.value == "IFRAME"
        assert WidgetType.CALENDAR.value == "CALENDAR"
        assert WidgetType.TIMELINE.value == "TIMELINE"
        assert len(WidgetType) >= 13

    def test_chart_type_values(self):
        """Tester les types de graphique."""
        assert ChartType.LINE.value == "LINE"
        assert ChartType.BAR.value == "BAR"
        assert ChartType.PIE.value == "PIE"
        assert ChartType.DOUGHNUT.value == "DOUGHNUT"
        assert ChartType.AREA.value == "AREA"
        assert ChartType.SCATTER.value == "SCATTER"
        assert ChartType.RADAR.value == "RADAR"
        assert ChartType.POLAR.value == "POLAR"
        assert ChartType.HEATMAP.value == "HEATMAP"
        assert ChartType.TREEMAP.value == "TREEMAP"
        assert ChartType.FUNNEL.value == "FUNNEL"
        assert ChartType.WATERFALL.value == "WATERFALL"
        assert ChartType.SANKEY.value == "SANKEY"
        assert ChartType.BUBBLE.value == "BUBBLE"
        assert ChartType.CANDLESTICK.value == "CANDLESTICK"
        assert len(ChartType) >= 15

    def test_data_source_type_values(self):
        """Tester les types de source de donnees."""
        assert DataSourceType.DATABASE.value == "DATABASE"
        assert DataSourceType.API.value == "API"
        assert DataSourceType.FILE.value == "FILE"
        assert DataSourceType.MODULE.value == "MODULE"
        assert DataSourceType.CUSTOM.value == "CUSTOM"
        assert len(DataSourceType) >= 5

    def test_refresh_frequency_values(self):
        """Tester les frequences de rafraichissement."""
        assert RefreshFrequency.REALTIME.value == "REALTIME"
        assert RefreshFrequency.MINUTE_1.value == "MINUTE_1"
        assert RefreshFrequency.MINUTE_5.value == "MINUTE_5"
        assert RefreshFrequency.MINUTE_15.value == "MINUTE_15"
        assert RefreshFrequency.MINUTE_30.value == "MINUTE_30"
        assert RefreshFrequency.HOURLY.value == "HOURLY"
        assert RefreshFrequency.DAILY.value == "DAILY"
        assert RefreshFrequency.WEEKLY.value == "WEEKLY"
        assert RefreshFrequency.MONTHLY.value == "MONTHLY"
        assert RefreshFrequency.MANUAL.value == "MANUAL"
        assert len(RefreshFrequency) >= 10

    def test_alert_severity_values(self):
        """Tester les niveaux d'alerte."""
        assert AlertSeverity.INFO.value == "INFO"
        assert AlertSeverity.WARNING.value == "WARNING"
        assert AlertSeverity.ERROR.value == "ERROR"
        assert AlertSeverity.CRITICAL.value == "CRITICAL"
        assert len(AlertSeverity) == 4

    def test_alert_status_values(self):
        """Tester les statuts d'alerte."""
        assert AlertStatus.TRIGGERED.value == "TRIGGERED"
        assert AlertStatus.ACKNOWLEDGED.value == "ACKNOWLEDGED"
        assert AlertStatus.RESOLVED.value == "RESOLVED"
        assert AlertStatus.SNOOZED.value == "SNOOZED"
        assert len(AlertStatus) >= 4

    def test_alert_operator_values(self):
        """Tester les operateurs d'alerte."""
        assert AlertOperator.EQUALS.value == "EQUALS"
        assert AlertOperator.NOT_EQUALS.value == "NOT_EQUALS"
        assert AlertOperator.GREATER_THAN.value == "GREATER_THAN"
        assert AlertOperator.GREATER_OR_EQUAL.value == "GREATER_OR_EQUAL"
        assert AlertOperator.LESS_THAN.value == "LESS_THAN"
        assert AlertOperator.LESS_OR_EQUAL.value == "LESS_OR_EQUAL"
        assert AlertOperator.BETWEEN.value == "BETWEEN"
        assert AlertOperator.NOT_BETWEEN.value == "NOT_BETWEEN"
        assert AlertOperator.IN_LIST.value == "IN_LIST"
        assert AlertOperator.NOT_IN_LIST.value == "NOT_IN_LIST"
        assert AlertOperator.CONTAINS.value == "CONTAINS"
        assert AlertOperator.NOT_CONTAINS.value == "NOT_CONTAINS"
        assert len(AlertOperator) >= 12

    def test_share_permission_values(self):
        """Tester les permissions de partage."""
        assert SharePermission.VIEW.value == "VIEW"
        assert SharePermission.EDIT.value == "EDIT"
        assert SharePermission.ADMIN.value == "ADMIN"
        assert len(SharePermission) >= 3

    def test_export_format_values(self):
        """Tester les formats d'export."""
        assert ExportFormat.PDF.value == "PDF"
        assert ExportFormat.PNG.value == "PNG"
        assert ExportFormat.JPEG.value == "JPEG"
        assert ExportFormat.SVG.value == "SVG"
        assert ExportFormat.EXCEL.value == "EXCEL"
        assert ExportFormat.CSV.value == "CSV"
        assert ExportFormat.JSON.value == "JSON"
        assert ExportFormat.HTML.value == "HTML"
        assert len(ExportFormat) >= 8

    def test_export_status_values(self):
        """Tester les statuts d'export."""
        assert ExportStatus.PENDING.value == "PENDING"
        assert ExportStatus.PROCESSING.value == "PROCESSING"
        assert ExportStatus.COMPLETED.value == "COMPLETED"
        assert ExportStatus.FAILED.value == "FAILED"
        assert ExportStatus.EXPIRED.value == "EXPIRED"
        assert len(ExportStatus) >= 5


# =============================================================================
# TESTS DES MODELES
# =============================================================================

class TestDashboardModel:
    """Tests du modele Dashboard."""

    def test_dashboard_creation(self):
        """Tester la creation d'un dashboard."""
        dashboard = Dashboard(
            tenant_id="test-tenant",
            code="DASH001",
            name="Tableau de bord commercial",
            type=DashboardType.OPERATIONAL
        )
        assert dashboard.code == "DASH001"
        assert dashboard.name == "Tableau de bord commercial"
        assert dashboard.type == DashboardType.OPERATIONAL
        assert dashboard.is_active == True
        assert dashboard.is_default == False

    def test_dashboard_with_description(self):
        """Tester dashboard avec description."""
        dashboard = Dashboard(
            tenant_id="test-tenant",
            code="DASH002",
            name="Dashboard Executif",
            type=DashboardType.EXECUTIVE,
            description="Vue executive des KPIs strategiques"
        )
        assert dashboard.description == "Vue executive des KPIs strategiques"

    def test_dashboard_type_personal(self):
        """Tester dashboard personnel."""
        dashboard = Dashboard(
            tenant_id="test-tenant",
            code="DASH003",
            name="Mon Dashboard",
            type=DashboardType.PERSONAL,
            owner_id=uuid4()
        )
        assert dashboard.type == DashboardType.PERSONAL
        assert dashboard.owner_id is not None


class TestWidgetModel:
    """Tests du modele DashboardWidget."""

    def test_widget_creation(self):
        """Tester la creation d'un widget."""
        widget = DashboardWidget(
            tenant_id="test-tenant",
            dashboard_id=uuid4(),
            name="Chiffre d'affaires",
            type=WidgetType.CHART,
            chart_type=ChartType.LINE,
            position_x=0,
            position_y=0,
            width=6,
            height=4
        )
        assert widget.name == "Chiffre d'affaires"
        assert widget.type == WidgetType.CHART
        assert widget.chart_type == ChartType.LINE
        assert widget.position_x == 0
        assert widget.position_y == 0
        assert widget.width == 6
        assert widget.height == 4

    def test_widget_kpi_type(self):
        """Tester widget de type KPI."""
        widget = DashboardWidget(
            tenant_id="test-tenant",
            dashboard_id=uuid4(),
            name="Nombre de ventes",
            type=WidgetType.KPI
        )
        assert widget.type == WidgetType.KPI

    def test_widget_table_type(self):
        """Tester widget de type table."""
        widget = DashboardWidget(
            tenant_id="test-tenant",
            dashboard_id=uuid4(),
            name="Liste des commandes",
            type=WidgetType.TABLE
        )
        assert widget.type == WidgetType.TABLE

    def test_widget_gauge_type(self):
        """Tester widget de type jauge."""
        widget = DashboardWidget(
            tenant_id="test-tenant",
            dashboard_id=uuid4(),
            name="Taux de completion",
            type=WidgetType.GAUGE
        )
        assert widget.type == WidgetType.GAUGE


class TestDataSourceModel:
    """Tests du modele DataSource."""

    def test_data_source_creation(self):
        """Tester la creation d'une source de donnees."""
        source = DataSource(
            tenant_id="test-tenant",
            code="DS001",
            name="Base commerciale",
            type=DataSourceType.DATABASE,
            refresh_frequency=RefreshFrequency.DAILY
        )
        assert source.code == "DS001"
        assert source.name == "Base commerciale"
        assert source.type == DataSourceType.DATABASE
        assert source.refresh_frequency == RefreshFrequency.DAILY
        assert source.is_active == True

    def test_data_source_api_type(self):
        """Tester source de donnees API."""
        source = DataSource(
            tenant_id="test-tenant",
            code="DS002",
            name="API Externe",
            type=DataSourceType.API,
            connection_string="https://api.example.com/data"
        )
        assert source.type == DataSourceType.API
        assert source.connection_string == "https://api.example.com/data"

    def test_data_source_module_type(self):
        """Tester source de donnees module."""
        source = DataSource(
            tenant_id="test-tenant",
            code="DS003",
            name="Module Ventes",
            type=DataSourceType.MODULE
        )
        assert source.type == DataSourceType.MODULE


class TestDataQueryModel:
    """Tests du modele DataQuery."""

    def test_data_query_creation(self):
        """Tester la creation d'une requete."""
        query = DataQuery(
            tenant_id="test-tenant",
            data_source_id=uuid4(),
            code="QRY001",
            name="Ventes mensuelles",
            query_text="SELECT * FROM sales WHERE month = :month"
        )
        assert query.code == "QRY001"
        assert query.name == "Ventes mensuelles"
        assert "SELECT" in query.query_text


class TestShareModel:
    """Tests du modele DashboardShare."""

    def test_share_creation(self):
        """Tester la creation d'un partage."""
        share = DashboardShare(
            tenant_id="test-tenant",
            dashboard_id=uuid4(),
            permission=SharePermission.VIEW,
            shared_by=uuid4()
        )
        assert share.permission == SharePermission.VIEW

    def test_share_with_user(self):
        """Tester partage avec utilisateur."""
        share = DashboardShare(
            tenant_id="test-tenant",
            dashboard_id=uuid4(),
            shared_with_user=uuid4(),
            permission=SharePermission.EDIT,
            shared_by=uuid4()
        )
        assert share.permission == SharePermission.EDIT
        assert share.shared_with_user is not None

    def test_share_with_link(self):
        """Tester partage avec lien."""
        share = DashboardShare(
            tenant_id="test-tenant",
            dashboard_id=uuid4(),
            permission=SharePermission.VIEW,
            is_public_link=True,
            link_token="abc123xyz",
            shared_by=uuid4()
        )
        assert share.is_public_link == True
        assert share.link_token == "abc123xyz"


class TestAlertRuleModel:
    """Tests du modele DashboardAlertRule."""

    def test_alert_rule_creation(self):
        """Tester la creation d'une regle d'alerte."""
        rule = DashboardAlertRule(
            tenant_id="test-tenant",
            dashboard_id=uuid4(),
            code="RULE001",
            name="Alerte seuil ventes",
            metric_name="total_sales",
            operator=AlertOperator.LESS_THAN,
            threshold_value=Decimal("10000"),
            severity=AlertSeverity.WARNING
        )
        assert rule.code == "RULE001"
        assert rule.operator == AlertOperator.LESS_THAN
        assert rule.threshold_value == Decimal("10000")
        assert rule.severity == AlertSeverity.WARNING

    def test_alert_rule_critical(self):
        """Tester regle d'alerte critique."""
        rule = DashboardAlertRule(
            tenant_id="test-tenant",
            dashboard_id=uuid4(),
            code="RULE002",
            name="Alerte critique stock",
            metric_name="stock_level",
            operator=AlertOperator.LESS_OR_EQUAL,
            threshold_value=Decimal("0"),
            severity=AlertSeverity.CRITICAL
        )
        assert rule.severity == AlertSeverity.CRITICAL


class TestAlertModel:
    """Tests du modele DashboardAlert."""

    def test_alert_creation(self):
        """Tester la creation d'une alerte."""
        alert = DashboardAlert(
            tenant_id="test-tenant",
            alert_rule_id=uuid4(),
            dashboard_id=uuid4(),
            severity=AlertSeverity.WARNING,
            message="Seuil de ventes non atteint",
            current_value=Decimal("8500"),
            threshold_value=Decimal("10000")
        )
        assert alert.severity == AlertSeverity.WARNING
        assert alert.status == AlertStatus.TRIGGERED
        assert alert.current_value == Decimal("8500")

    def test_alert_acknowledged(self):
        """Tester alerte acquittee."""
        alert = DashboardAlert(
            tenant_id="test-tenant",
            alert_rule_id=uuid4(),
            dashboard_id=uuid4(),
            severity=AlertSeverity.ERROR,
            message="Erreur de traitement",
            status=AlertStatus.ACKNOWLEDGED,
            acknowledged_by=uuid4(),
            acknowledged_at=datetime.utcnow()
        )
        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.acknowledged_by is not None


class TestExportModel:
    """Tests du modele DashboardExport."""

    def test_export_creation(self):
        """Tester la creation d'un export."""
        export = DashboardExport(
            tenant_id="test-tenant",
            dashboard_id=uuid4(),
            format=ExportFormat.PDF,
            requested_by=uuid4()
        )
        assert export.format == ExportFormat.PDF
        assert export.status == ExportStatus.PENDING

    def test_export_completed(self):
        """Tester export termine."""
        export = DashboardExport(
            tenant_id="test-tenant",
            dashboard_id=uuid4(),
            format=ExportFormat.PNG,
            status=ExportStatus.COMPLETED,
            file_path="/exports/dashboard_123.png",
            file_size=524288,
            requested_by=uuid4()
        )
        assert export.status == ExportStatus.COMPLETED
        assert export.file_path == "/exports/dashboard_123.png"


class TestScheduledReportModel:
    """Tests du modele ScheduledReport."""

    def test_scheduled_report_creation(self):
        """Tester la creation d'un rapport planifie."""
        report = ScheduledReport(
            tenant_id="test-tenant",
            dashboard_id=uuid4(),
            code="SCHD001",
            name="Rapport hebdomadaire ventes",
            cron_expression="0 8 * * 1",
            format=ExportFormat.PDF
        )
        assert report.code == "SCHD001"
        assert report.cron_expression == "0 8 * * 1"
        assert report.format == ExportFormat.PDF
        assert report.is_active == True


class TestFavoriteModel:
    """Tests du modele DashboardFavorite."""

    def test_favorite_creation(self):
        """Tester l'ajout en favori."""
        favorite = DashboardFavorite(
            tenant_id="test-tenant",
            dashboard_id=uuid4(),
            user_id=uuid4()
        )
        assert favorite.dashboard_id is not None
        assert favorite.user_id is not None


class TestUserPreferenceModel:
    """Tests du modele UserDashboardPreference."""

    def test_user_preference_creation(self):
        """Tester les preferences utilisateur."""
        pref = UserDashboardPreference(
            tenant_id="test-tenant",
            user_id=uuid4(),
            default_dashboard_id=uuid4(),
            theme="dark",
            refresh_interval=300
        )
        assert pref.theme == "dark"
        assert pref.refresh_interval == 300


class TestTemplateModel:
    """Tests du modele DashboardTemplate."""

    def test_template_creation(self):
        """Tester la creation d'un template."""
        template = DashboardTemplate(
            tenant_id="test-tenant",
            code="TMPL001",
            name="Template Commercial",
            type=DashboardType.OPERATIONAL,
            category="sales",
            is_public=True
        )
        assert template.code == "TMPL001"
        assert template.is_public == True
        assert template.category == "sales"


# =============================================================================
# EXECUTION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
