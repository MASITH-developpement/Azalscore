"""
AZALS MODULE M10 - Tests BI & Reporting
========================================

Tests unitaires pour la Business Intelligence et le reporting.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

# Import des modèles
from app.modules.bi.models import (
    Dashboard, DashboardWidget, WidgetFilter,
    Report, ReportSchedule, ReportExecution,
    KPIDefinition, KPIValue, KPITarget,
    Alert, AlertRule, DataSource, DataQuery,
    Bookmark, ExportHistory,
    DashboardType, WidgetType, ChartType,
    ReportType, ReportFormat, ReportStatus,
    KPICategory, KPITrend, AlertSeverity, AlertStatus,
    DataSourceType, RefreshFrequency
)

# Import des schémas
from app.modules.bi.schemas import (
    DashboardCreate, DashboardUpdate, WidgetCreate, WidgetUpdate,
    ReportCreate, ReportScheduleCreate,
    KPICreate as KPIDefinitionCreate, KPIValueCreate, KPITargetCreate,
    AlertCreate, AlertRuleCreate,
    DataSourceCreate, DataQueryCreate,
    BookmarkCreate, ExportHistoryCreate,
    BIDashboard, KPIOverview
)

# Import du service
from app.modules.bi.service import BIService, get_bi_service


# =============================================================================
# TESTS DES ENUMS
# =============================================================================

class TestEnums:
    """Tests des énumérations."""

    def test_dashboard_type_values(self):
        """Tester les types de tableau de bord."""
        assert DashboardType.EXECUTIVE.value == "EXECUTIVE"
        assert DashboardType.OPERATIONAL.value == "OPERATIONAL"
        assert DashboardType.ANALYTICAL.value == "ANALYTICAL"
        assert DashboardType.STRATEGIC.value == "STRATEGIC"
        assert len(DashboardType) >= 4

    def test_widget_type_values(self):
        """Tester les types de widget."""
        assert WidgetType.CHART.value == "CHART"
        assert WidgetType.KPI.value == "KPI"
        assert WidgetType.TABLE.value == "TABLE"
        assert WidgetType.MAP.value == "MAP"
        assert len(WidgetType) >= 4

    def test_chart_type_values(self):
        """Tester les types de graphique."""
        assert ChartType.LINE.value == "LINE"
        assert ChartType.BAR.value == "BAR"
        assert ChartType.PIE.value == "PIE"
        assert ChartType.AREA.value == "AREA"
        assert ChartType.SCATTER.value == "SCATTER"
        assert len(ChartType) >= 5

    def test_report_type_values(self):
        """Tester les types de rapport."""
        assert ReportType.STANDARD.value == "STANDARD"
        assert ReportType.CUSTOM.value == "CUSTOM"
        assert ReportType.SCHEDULED.value == "SCHEDULED"
        assert len(ReportType) >= 3

    def test_report_format_values(self):
        """Tester les formats de rapport."""
        assert ReportFormat.PDF.value == "PDF"
        assert ReportFormat.EXCEL.value == "EXCEL"
        assert ReportFormat.CSV.value == "CSV"
        assert ReportFormat.HTML.value == "HTML"
        assert len(ReportFormat) >= 4

    def test_alert_severity_values(self):
        """Tester les niveaux d'alerte."""
        assert AlertSeverity.INFO.value == "INFO"
        assert AlertSeverity.WARNING.value == "WARNING"
        assert AlertSeverity.ERROR.value == "ERROR"
        assert AlertSeverity.CRITICAL.value == "CRITICAL"
        assert len(AlertSeverity) == 4

    def test_kpi_trend_values(self):
        """Tester les tendances KPI."""
        assert KPITrend.UP.value == "UP"
        assert KPITrend.DOWN.value == "DOWN"
        assert KPITrend.STABLE.value == "STABLE"
        assert len(KPITrend) == 3


# =============================================================================
# TESTS DES MODÈLES
# =============================================================================

class TestModels:
    """Tests des modèles SQLAlchemy."""

    def test_dashboard_model(self):
        """Tester le modèle Dashboard."""
        dashboard = Dashboard(
            tenant_id="test-tenant",
            code="DB001",
            name="Tableau de bord commercial",
            type=DashboardType.OPERATIONAL
        )
        assert dashboard.code == "DB001"
        assert dashboard.type == DashboardType.OPERATIONAL
        assert dashboard.is_active == True

    def test_dashboard_widget_model(self):
        """Tester le modèle DashboardWidget."""
        widget = DashboardWidget(
            tenant_id="test-tenant",
            dashboard_id=uuid4(),
            name="Chiffre d'affaires",
            type=WidgetType.CHART,
            chart_type=ChartType.LINE,
            position_x=0,
            position_y=0
        )
        assert widget.type == WidgetType.CHART
        assert widget.chart_type == ChartType.LINE

    def test_report_model(self):
        """Tester le modèle Report."""
        report = Report(
            tenant_id="test-tenant",
            code="RPT001",
            name="Rapport mensuel ventes",
            type=ReportType.SCHEDULED,
            format=ReportFormat.PDF
        )
        assert report.code == "RPT001"
        assert report.type == ReportType.SCHEDULED
        assert report.format == ReportFormat.PDF

    def test_kpi_definition_model(self):
        """Tester le modèle KPIDefinition."""
        kpi = KPIDefinition(
            tenant_id="test-tenant",
            code="KPI001",
            name="Taux de conversion",
            category=KPICategory.SALES,
            unit="%",
            target_value=Decimal("25")
        )
        assert kpi.code == "KPI001"
        assert kpi.category == KPICategory.SALES
        assert kpi.target_value == Decimal("25")

    def test_kpi_value_model(self):
        """Tester le modèle KPIValue."""
        value = KPIValue(
            tenant_id="test-tenant",
            kpi_id=uuid4(),
            period_date=date.today(),
            value=Decimal("23.5"),
            trend=KPITrend.UP
        )
        assert value.value == Decimal("23.5")
        assert value.trend == KPITrend.UP

    def test_alert_model(self):
        """Tester le modèle Alert."""
        alert = Alert(
            tenant_id="test-tenant",
            title="Seuil dépassé",
            severity=AlertSeverity.WARNING,
            message="Le stock est sous le seuil minimum"
        )
        assert alert.severity == AlertSeverity.WARNING
        assert alert.status == AlertStatus.ACTIVE

    def test_data_source_model(self):
        """Tester le modèle DataSource."""
        source = DataSource(
            tenant_id="test-tenant",
            code="DS001",
            name="Base commerciale",
            type=DataSourceType.DATABASE,
            refresh_frequency=RefreshFrequency.DAILY
        )
        assert source.code == "DS001"
        assert source.type == DataSourceType.DATABASE


# =============================================================================
# TESTS DES SCHÉMAS
# =============================================================================

class TestSchemas:
    """Tests des schémas Pydantic."""

    def test_dashboard_create_schema(self):
        """Tester le schéma DashboardCreate."""
        data = DashboardCreate(
            code="DB001",
            name="Dashboard Commercial",
            type=DashboardType.OPERATIONAL,
            description="Vue opérationnelle des ventes"
        )
        assert data.code == "DB001"
        assert data.type == DashboardType.OPERATIONAL

    def test_widget_create_schema(self):
        """Tester le schéma WidgetCreate."""
        data = WidgetCreate(
            name="CA mensuel",
            type=WidgetType.CHART,
            chart_type=ChartType.BAR,
            width=6,
            height=4
        )
        assert data.type == WidgetType.CHART
        assert data.chart_type == ChartType.BAR

    def test_report_create_schema(self):
        """Tester le schéma ReportCreate."""
        data = ReportCreate(
            code="RPT001",
            name="Rapport hebdomadaire",
            type=ReportType.SCHEDULED,
            format=ReportFormat.EXCEL
        )
        assert data.format == ReportFormat.EXCEL

    def test_kpi_definition_create_schema(self):
        """Tester le schéma KPIDefinitionCreate."""
        data = KPIDefinitionCreate(
            code="KPI001",
            name="Marge brute",
            category=KPICategory.FINANCE,
            unit="%",
            target_value=Decimal("35"),
            warning_threshold=Decimal("30"),
            critical_threshold=Decimal("25")
        )
        assert data.category == KPICategory.FINANCE
        assert data.target_value == Decimal("35")


# =============================================================================
# TESTS DU SERVICE - DASHBOARDS
# =============================================================================

class TestBIServiceDashboards:
    """Tests du service BI - Tableaux de bord."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return BIService(mock_db, "test-tenant", uuid4())

    def test_create_dashboard(self, service, mock_db):
        """Tester la création d'un tableau de bord."""
        data = DashboardCreate(
            code="DB001",
            name="Dashboard Test",
            type=DashboardType.OPERATIONAL
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_dashboard(data)

        mock_db.add.assert_called_once()
        assert result.code == "DB001"

    def test_add_widget(self, service, mock_db):
        """Tester l'ajout d'un widget."""
        dashboard_id = uuid4()
        data = WidgetCreate(
            name="Widget Test",
            type=WidgetType.KPI
        )

        mock_dashboard = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_dashboard
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.add_widget(dashboard_id, data)

        mock_db.add.assert_called()


# =============================================================================
# TESTS DU SERVICE - RAPPORTS
# =============================================================================

class TestBIServiceReports:
    """Tests du service BI - Rapports."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return BIService(mock_db, "test-tenant", uuid4())

    def test_create_report(self, service, mock_db):
        """Tester la création d'un rapport."""
        data = ReportCreate(
            code="RPT001",
            name="Rapport Test",
            type=ReportType.STANDARD,
            format=ReportFormat.PDF
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_report(data)

        mock_db.add.assert_called()

    def test_execute_report(self, service, mock_db):
        """Tester l'exécution d'un rapport."""
        report_id = uuid4()
        mock_report = MagicMock()
        mock_report.status = ReportStatus.ACTIVE

        mock_db.query.return_value.filter.return_value.first.return_value = mock_report
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.execute_report(report_id)

        mock_db.add.assert_called()


# =============================================================================
# TESTS DU SERVICE - KPIs
# =============================================================================

class TestBIServiceKPIs:
    """Tests du service BI - KPIs."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return BIService(mock_db, "test-tenant", uuid4())

    def test_create_kpi(self, service, mock_db):
        """Tester la création d'un KPI."""
        data = KPIDefinitionCreate(
            code="KPI001",
            name="Taux de service",
            category=KPICategory.OPERATIONS,
            target_value=Decimal("98")
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_kpi(data)

        mock_db.add.assert_called()

    def test_record_kpi_value(self, service, mock_db):
        """Tester l'enregistrement d'une valeur KPI."""
        data = KPIValueCreate(
            kpi_id=uuid4(),
            period_date=date.today(),
            value=Decimal("97.5")
        )

        mock_kpi = MagicMock()
        mock_kpi.target_value = Decimal("98")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_kpi
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.record_kpi_value(data)

        mock_db.add.assert_called()


# =============================================================================
# TESTS DU SERVICE - ALERTES
# =============================================================================

class TestBIServiceAlerts:
    """Tests du service BI - Alertes."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return BIService(mock_db, "test-tenant", uuid4())

    def test_create_alert(self, service, mock_db):
        """Tester la création d'une alerte."""
        data = AlertCreate(
            title="Alerte stock",
            severity=AlertSeverity.WARNING,
            message="Stock critique atteint"
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_alert(data)

        mock_db.add.assert_called()

    def test_acknowledge_alert(self, service, mock_db):
        """Tester l'acquittement d'une alerte."""
        alert_id = uuid4()
        mock_alert = MagicMock()
        mock_alert.status = AlertStatus.ACTIVE

        mock_db.query.return_value.filter.return_value.first.return_value = mock_alert

        result = service.acknowledge_alert(alert_id)

        assert mock_alert.status == AlertStatus.ACKNOWLEDGED


# =============================================================================
# TESTS FACTORY
# =============================================================================

class TestFactory:
    """Tests de la factory."""

    def test_get_bi_service(self):
        """Tester la factory."""
        mock_db = MagicMock()
        user_id = uuid4()
        service = get_bi_service(mock_db, "test-tenant", user_id)

        assert isinstance(service, BIService)
        assert service.tenant_id == "test-tenant"


# =============================================================================
# TESTS CALCULS BI
# =============================================================================

class TestBICalculations:
    """Tests des calculs BI."""

    def test_kpi_variance(self):
        """Tester le calcul de l'écart KPI."""
        target = Decimal("100")
        actual = Decimal("95")

        variance = actual - target
        variance_percent = (variance / target) * 100

        assert variance == Decimal("-5")
        assert variance_percent == Decimal("-5")

    def test_growth_rate(self):
        """Tester le calcul du taux de croissance."""
        previous = Decimal("1000")
        current = Decimal("1150")

        growth = ((current - previous) / previous) * 100

        assert growth == Decimal("15")

    def test_trend_detection(self):
        """Tester la détection de tendance."""
        previous = Decimal("100")
        current = Decimal("110")

        if current > previous:
            trend = KPITrend.UP
        elif current < previous:
            trend = KPITrend.DOWN
        else:
            trend = KPITrend.STABLE

        assert trend == KPITrend.UP

    def test_percentage_of_target(self):
        """Tester le calcul du pourcentage de l'objectif."""
        target = Decimal("1000")
        actual = Decimal("850")

        pct_achieved = (actual / target) * 100

        assert pct_achieved == Decimal("85")


# =============================================================================
# EXÉCUTION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
