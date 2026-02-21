"""
AZALSCORE ERP - Tests Schemas Dashboards
=========================================
Tests unitaires pour les schemas Pydantic du module dashboards.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

from app.modules.dashboards.models import (
    DashboardType,
    WidgetType,
    ChartType,
    DataSourceType,
    RefreshFrequency,
    AlertSeverity,
    AlertOperator,
    SharePermission,
    ExportFormat,
)

from app.modules.dashboards.schemas import (
    # Dashboard schemas
    DashboardCreate,
    DashboardUpdate,
    DashboardResponse,
    DashboardFilters,
    # Widget schemas
    WidgetCreate,
    WidgetUpdate,
    WidgetLayoutUpdate,
    # DataSource schemas
    DataSourceCreate,
    DataSourceUpdate,
    # DataQuery schemas
    DataQueryCreate,
    DataQueryUpdate,
    # Share schemas
    ShareCreate,
    ShareUpdate,
    # Favorite schemas
    FavoriteCreate,
    # AlertRule schemas
    AlertRuleCreate,
    AlertRuleUpdate,
    # Alert schemas
    AlertAcknowledge,
    AlertResolve,
    AlertSnooze,
    # Export schemas
    ExportRequest,
    # ScheduledReport schemas
    ScheduledReportCreate,
    ScheduledReportUpdate,
    # UserPreference schemas
    UserPreferenceCreate,
    UserPreferenceUpdate,
    # Template schemas
    TemplateCreate,
    TemplateUpdate,
)


# =============================================================================
# TESTS DES SCHEMAS DASHBOARD
# =============================================================================

class TestDashboardSchemas:
    """Tests des schemas Dashboard."""

    def test_dashboard_create_minimal(self):
        """Tester creation dashboard minimale."""
        data = DashboardCreate(
            code="DASH001",
            name="Dashboard Test"
        )
        assert data.code == "DASH001"
        assert data.name == "Dashboard Test"
        assert data.type == DashboardType.PERSONAL  # default

    def test_dashboard_create_full(self):
        """Tester creation dashboard complete."""
        data = DashboardCreate(
            code="DASH002",
            name="Dashboard Commercial",
            type=DashboardType.OPERATIONAL,
            description="Vue operationnelle des ventes",
            icon="chart-line",
            color="#3498db",
            is_default=True,
            tags=["ventes", "commercial", "kpi"],
            refresh_frequency=RefreshFrequency.MINUTE_5,
            layout_config={"columns": 12, "row_height": 50}
        )
        assert data.type == DashboardType.OPERATIONAL
        assert data.description == "Vue operationnelle des ventes"
        assert data.is_default == True
        assert "ventes" in data.tags
        assert data.refresh_frequency == RefreshFrequency.MINUTE_5

    def test_dashboard_update_partial(self):
        """Tester mise a jour partielle dashboard."""
        data = DashboardUpdate(
            name="Nouveau nom"
        )
        assert data.name == "Nouveau nom"
        assert data.type is None
        assert data.description is None

    def test_dashboard_filters(self):
        """Tester filtres dashboard."""
        filters = DashboardFilters(
            type=DashboardType.EXECUTIVE,
            is_active=True,
            owner_id=uuid4(),
            tags=["finance"],
            search="budget"
        )
        assert filters.type == DashboardType.EXECUTIVE
        assert filters.is_active == True
        assert "finance" in filters.tags


# =============================================================================
# TESTS DES SCHEMAS WIDGET
# =============================================================================

class TestWidgetSchemas:
    """Tests des schemas Widget."""

    def test_widget_create_kpi(self):
        """Tester creation widget KPI."""
        data = WidgetCreate(
            name="Total Ventes",
            type=WidgetType.KPI
        )
        assert data.name == "Total Ventes"
        assert data.type == WidgetType.KPI

    def test_widget_create_chart(self):
        """Tester creation widget graphique."""
        data = WidgetCreate(
            name="Evolution CA",
            type=WidgetType.CHART,
            chart_type=ChartType.LINE,
            width=6,
            height=4
        )
        assert data.type == WidgetType.CHART
        assert data.chart_type == ChartType.LINE
        assert data.width == 6

    def test_widget_create_table(self):
        """Tester creation widget table."""
        data = WidgetCreate(
            name="Liste Commandes",
            type=WidgetType.TABLE,
            config={
                "columns": ["date", "client", "montant"],
                "sortable": True,
                "pagination": True
            }
        )
        assert data.type == WidgetType.TABLE
        assert "columns" in data.config

    def test_widget_create_gauge(self):
        """Tester creation widget jauge."""
        data = WidgetCreate(
            name="Taux Completion",
            type=WidgetType.GAUGE,
            config={
                "min": 0,
                "max": 100,
                "thresholds": [30, 70]
            }
        )
        assert data.type == WidgetType.GAUGE

    def test_widget_update(self):
        """Tester mise a jour widget."""
        data = WidgetUpdate(
            name="Nouveau titre",
            config={"refreshInterval": 60}
        )
        assert data.name == "Nouveau titre"

    def test_widget_layout_update(self):
        """Tester mise a jour layout widget."""
        data = WidgetLayoutUpdate(
            widget_id=uuid4(),
            position_x=2,
            position_y=3,
            width=4,
            height=3
        )
        assert data.position_x == 2
        assert data.position_y == 3
        assert data.width == 4


# =============================================================================
# TESTS DES SCHEMAS DATA SOURCE
# =============================================================================

class TestDataSourceSchemas:
    """Tests des schemas DataSource."""

    def test_data_source_create_database(self):
        """Tester creation source base de donnees."""
        data = DataSourceCreate(
            code="DS001",
            name="Base Commerciale",
            type=DataSourceType.DATABASE,
            connection_string="postgresql://host:5432/db"
        )
        assert data.code == "DS001"
        assert data.type == DataSourceType.DATABASE

    def test_data_source_create_api(self):
        """Tester creation source API."""
        data = DataSourceCreate(
            code="DS002",
            name="API Meteo",
            type=DataSourceType.API,
            connection_string="https://api.weather.com",
            config={
                "method": "GET",
                "headers": {"Authorization": "Bearer xxx"}
            }
        )
        assert data.type == DataSourceType.API

    def test_data_source_create_module(self):
        """Tester creation source module."""
        data = DataSourceCreate(
            code="DS003",
            name="Module Ventes",
            type=DataSourceType.MODULE,
            config={"module": "sales", "method": "get_monthly_stats"}
        )
        assert data.type == DataSourceType.MODULE

    def test_data_source_update(self):
        """Tester mise a jour source."""
        data = DataSourceUpdate(
            refresh_frequency=RefreshFrequency.HOURLY,
            is_active=False
        )
        assert data.refresh_frequency == RefreshFrequency.HOURLY
        assert data.is_active == False


# =============================================================================
# TESTS DES SCHEMAS DATA QUERY
# =============================================================================

class TestDataQuerySchemas:
    """Tests des schemas DataQuery."""

    def test_data_query_create(self):
        """Tester creation requete."""
        data = DataQueryCreate(
            code="QRY001",
            name="Ventes par mois",
            query_text="SELECT month, SUM(amount) FROM sales GROUP BY month"
        )
        assert data.code == "QRY001"
        assert "SELECT" in data.query_text

    def test_data_query_with_params(self):
        """Tester requete avec parametres."""
        data = DataQueryCreate(
            code="QRY002",
            name="Ventes periode",
            query_text="SELECT * FROM sales WHERE date BETWEEN :start AND :end",
            parameters={
                "start": {"type": "date", "required": True},
                "end": {"type": "date", "required": True}
            }
        )
        assert "parameters" in str(data.parameters)

    def test_data_query_update(self):
        """Tester mise a jour requete."""
        data = DataQueryUpdate(
            query_text="SELECT * FROM sales WHERE status = 'completed'"
        )
        assert "completed" in data.query_text


# =============================================================================
# TESTS DES SCHEMAS SHARE
# =============================================================================

class TestShareSchemas:
    """Tests des schemas Share."""

    def test_share_create_user(self):
        """Tester partage avec utilisateur."""
        user_id = uuid4()
        data = ShareCreate(
            shared_with_user=user_id,
            permission=SharePermission.VIEW
        )
        assert data.shared_with_user == user_id
        assert data.permission == SharePermission.VIEW

    def test_share_create_role(self):
        """Tester partage avec role."""
        data = ShareCreate(
            shared_with_role="manager",
            permission=SharePermission.EDIT
        )
        assert data.shared_with_role == "manager"
        assert data.permission == SharePermission.EDIT

    def test_share_create_public_link(self):
        """Tester partage par lien public."""
        data = ShareCreate(
            permission=SharePermission.VIEW,
            is_public_link=True,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        assert data.is_public_link == True
        assert data.expires_at is not None

    def test_share_update(self):
        """Tester mise a jour partage."""
        data = ShareUpdate(
            permission=SharePermission.ADMIN,
            is_active=True
        )
        assert data.permission == SharePermission.ADMIN


# =============================================================================
# TESTS DES SCHEMAS FAVORITE
# =============================================================================

class TestFavoriteSchemas:
    """Tests des schemas Favorite."""

    def test_favorite_create(self):
        """Tester creation favori."""
        dashboard_id = uuid4()
        data = FavoriteCreate(
            dashboard_id=dashboard_id,
            display_order=1
        )
        assert data.dashboard_id == dashboard_id
        assert data.display_order == 1


# =============================================================================
# TESTS DES SCHEMAS ALERT RULE
# =============================================================================

class TestAlertRuleSchemas:
    """Tests des schemas AlertRule."""

    def test_alert_rule_create(self):
        """Tester creation regle d'alerte."""
        data = AlertRuleCreate(
            code="RULE001",
            name="Alerte ventes basses",
            metric_name="daily_sales",
            operator=AlertOperator.LESS_THAN,
            threshold_value=Decimal("5000"),
            severity=AlertSeverity.WARNING
        )
        assert data.code == "RULE001"
        assert data.operator == AlertOperator.LESS_THAN
        assert data.threshold_value == Decimal("5000")
        assert data.severity == AlertSeverity.WARNING

    def test_alert_rule_create_between(self):
        """Tester regle avec operateur BETWEEN."""
        data = AlertRuleCreate(
            code="RULE002",
            name="Alerte plage stock",
            metric_name="stock_level",
            operator=AlertOperator.BETWEEN,
            threshold_value=Decimal("10"),
            threshold_value_2=Decimal("50"),
            severity=AlertSeverity.INFO
        )
        assert data.operator == AlertOperator.BETWEEN
        assert data.threshold_value_2 == Decimal("50")

    def test_alert_rule_update(self):
        """Tester mise a jour regle."""
        data = AlertRuleUpdate(
            threshold_value=Decimal("7500"),
            severity=AlertSeverity.ERROR
        )
        assert data.threshold_value == Decimal("7500")


# =============================================================================
# TESTS DES SCHEMAS ALERT
# =============================================================================

class TestAlertSchemas:
    """Tests des schemas Alert."""

    def test_alert_acknowledge(self):
        """Tester acquittement alerte."""
        data = AlertAcknowledge(
            note="Pris en compte par l'equipe"
        )
        assert data.note == "Pris en compte par l'equipe"

    def test_alert_resolve(self):
        """Tester resolution alerte."""
        data = AlertResolve(
            resolution_note="Probleme corrige, stock reapprovisionne"
        )
        assert "corrige" in data.resolution_note

    def test_alert_snooze(self):
        """Tester mise en veille alerte."""
        snooze_until = datetime.utcnow() + timedelta(hours=2)
        data = AlertSnooze(
            snooze_until=snooze_until
        )
        assert data.snooze_until == snooze_until


# =============================================================================
# TESTS DES SCHEMAS EXPORT
# =============================================================================

class TestExportSchemas:
    """Tests des schemas Export."""

    def test_export_request_pdf(self):
        """Tester requete export PDF."""
        data = ExportRequest(
            format=ExportFormat.PDF,
            include_filters=True
        )
        assert data.format == ExportFormat.PDF
        assert data.include_filters == True

    def test_export_request_excel(self):
        """Tester requete export Excel."""
        data = ExportRequest(
            format=ExportFormat.EXCEL,
            widget_ids=[uuid4(), uuid4()]
        )
        assert data.format == ExportFormat.EXCEL
        assert len(data.widget_ids) == 2

    def test_export_request_png(self):
        """Tester requete export PNG."""
        data = ExportRequest(
            format=ExportFormat.PNG,
            options={"width": 1920, "height": 1080, "quality": 90}
        )
        assert data.format == ExportFormat.PNG
        assert data.options["width"] == 1920


# =============================================================================
# TESTS DES SCHEMAS SCHEDULED REPORT
# =============================================================================

class TestScheduledReportSchemas:
    """Tests des schemas ScheduledReport."""

    def test_scheduled_report_create(self):
        """Tester creation rapport planifie."""
        data = ScheduledReportCreate(
            code="SCHD001",
            name="Rapport quotidien ventes",
            cron_expression="0 8 * * *",
            format=ExportFormat.PDF,
            recipients=["manager@company.com", "director@company.com"]
        )
        assert data.code == "SCHD001"
        assert data.cron_expression == "0 8 * * *"
        assert len(data.recipients) == 2

    def test_scheduled_report_update(self):
        """Tester mise a jour rapport planifie."""
        data = ScheduledReportUpdate(
            cron_expression="0 9 * * 1-5",
            is_active=True
        )
        assert data.cron_expression == "0 9 * * 1-5"


# =============================================================================
# TESTS DES SCHEMAS USER PREFERENCE
# =============================================================================

class TestUserPreferenceSchemas:
    """Tests des schemas UserPreference."""

    def test_user_preference_create(self):
        """Tester creation preferences."""
        data = UserPreferenceCreate(
            default_dashboard_id=uuid4(),
            theme="dark",
            refresh_interval=300,
            timezone="Europe/Paris"
        )
        assert data.theme == "dark"
        assert data.refresh_interval == 300
        assert data.timezone == "Europe/Paris"

    def test_user_preference_update(self):
        """Tester mise a jour preferences."""
        data = UserPreferenceUpdate(
            theme="light",
            notifications_enabled=False
        )
        assert data.theme == "light"
        assert data.notifications_enabled == False


# =============================================================================
# TESTS DES SCHEMAS TEMPLATE
# =============================================================================

class TestTemplateSchemas:
    """Tests des schemas Template."""

    def test_template_create(self):
        """Tester creation template."""
        data = TemplateCreate(
            code="TMPL001",
            name="Template Commercial",
            type=DashboardType.OPERATIONAL,
            category="sales",
            description="Template pour tableaux de bord commerciaux",
            is_public=True,
            preview_image_url="/images/template_sales.png"
        )
        assert data.code == "TMPL001"
        assert data.is_public == True
        assert data.category == "sales"

    def test_template_update(self):
        """Tester mise a jour template."""
        data = TemplateUpdate(
            name="Template Commercial v2",
            is_public=False
        )
        assert data.name == "Template Commercial v2"
        assert data.is_public == False


# =============================================================================
# TESTS DE VALIDATION
# =============================================================================

class TestValidation:
    """Tests de validation des schemas."""

    def test_dashboard_code_required(self):
        """Tester que code est requis."""
        with pytest.raises(Exception):
            DashboardCreate(name="Dashboard sans code")

    def test_dashboard_name_required(self):
        """Tester que nom est requis."""
        with pytest.raises(Exception):
            DashboardCreate(code="DASH001")

    def test_widget_name_required(self):
        """Tester que nom widget est requis."""
        with pytest.raises(Exception):
            WidgetCreate(type=WidgetType.KPI)

    def test_widget_type_required(self):
        """Tester que type widget est requis."""
        with pytest.raises(Exception):
            WidgetCreate(name="Widget sans type")

    def test_alert_rule_metric_required(self):
        """Tester que metrique regle est requise."""
        with pytest.raises(Exception):
            AlertRuleCreate(
                code="RULE001",
                name="Regle sans metrique",
                operator=AlertOperator.EQUALS,
                threshold_value=Decimal("100")
            )


# =============================================================================
# EXECUTION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
