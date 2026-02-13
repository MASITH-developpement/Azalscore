"""
Fixtures pour les tests du module BI - CORE SaaS v2

Hérite des fixtures globales de app/conftest.py.
"""

from datetime import date, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.modules.bi.models import (
    AlertSeverity,
    AlertStatus,
    DashboardType,
    DataSourceType,
    KPICategory,
    KPITrend,
    ReportType,
)


# ============================================================================
# FIXTURES HÉRITÉES DU CONFTEST GLOBAL
# ============================================================================
# Les fixtures suivantes sont héritées de app/conftest.py:
# - tenant_id, user_id, user_uuid
# - db_session, test_db_session
# - test_client (avec headers auto-injectés)
# - mock_auth_global (autouse=True)
# - saas_context


@pytest.fixture
def client(test_client):
    """
    Alias pour test_client (compatibilité avec anciens tests).

    Le test_client du conftest global ajoute déjà les headers requis.
    """
    return test_client


@pytest.fixture
def auth_headers(tenant_id):
    """Headers d'authentification avec tenant ID."""
    return {
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": tenant_id
    }


@pytest.fixture
def mock_saas_context(saas_context):
    """Alias pour saas_context du conftest global."""
    return saas_context


# ============================================================================
# DATA FIXTURES
# ============================================================================

@pytest.fixture
def dashboard_data() -> dict[str, Any]:
    """Données de tableau de bord."""
    return {
        "code": "DASH-001",
        "name": "Tableau de bord test",
        "description": "Description test",
        "dashboard_type": DashboardType.OPERATIONAL,
        "is_shared": False,
        "is_public": False,
    }


@pytest.fixture
def widget_data() -> dict[str, Any]:
    """Données de widget."""
    return {
        "title": "Widget test",
        "widget_type": "chart",
        "chart_type": "bar",
        "position_x": 0,
        "position_y": 0,
        "width": 4,
        "height": 4,
    }


@pytest.fixture
def report_data() -> dict[str, Any]:
    """Données de rapport."""
    return {
        "code": "REP-001",
        "name": "Rapport test",
        "description": "Description test",
        "report_type": ReportType.TABULAR,
        "available_formats": ["pdf", "xlsx"],
        "is_public": False,
    }


@pytest.fixture
def kpi_data() -> dict[str, Any]:
    """Données de KPI."""
    return {
        "code": "KPI-001",
        "name": "KPI test",
        "description": "Description test",
        "category": KPICategory.SALES,
        "unit": "€",
        "precision": 2,
    }


@pytest.fixture
def kpi_value_data() -> dict[str, Any]:
    """Données de valeur KPI."""
    return {
        "period_date": date.today(),
        "period_type": "daily",
        "value": 1000.0,
    }


@pytest.fixture
def kpi_target_data() -> dict[str, Any]:
    """Données d'objectif KPI."""
    return {
        "year": 2024,
        "month": 1,
        "target_value": 5000.0,
    }


@pytest.fixture
def alert_rule_data() -> dict[str, Any]:
    """Données de règle d'alerte."""
    return {
        "code": "ALERT-001",
        "name": "Règle test",
        "description": "Description test",
        "severity": AlertSeverity.WARNING,
        "source_type": "kpi",
        "source_id": 1,
        "condition": {"operator": ">=", "value": 100},
        "is_enabled": True,
    }


@pytest.fixture
def data_source_data() -> dict[str, Any]:
    """Données de source de données."""
    return {
        "code": "DS-001",
        "name": "Source test",
        "description": "Description test",
        "source_type": DataSourceType.DATABASE,
        "connection_config": {"host": "localhost"},
    }


@pytest.fixture
def data_query_data() -> dict[str, Any]:
    """Données de requête."""
    return {
        "code": "QRY-001",
        "name": "Requête test",
        "description": "Description test",
        "data_source_id": 1,
        "query_type": "sql",
        "query_text": "SELECT * FROM test",
    }


@pytest.fixture
def bookmark_data() -> dict[str, Any]:
    """Données de favori."""
    return {
        "item_type": "dashboard",
        "item_id": 1,
        "item_name": "Dashboard test",
    }


@pytest.fixture
def export_data() -> dict[str, Any]:
    """Données d'export."""
    return {
        "export_type": "dashboard",
        "item_type": "dashboard",
        "item_id": 1,
        "format": "pdf",
        "filename": "export-test.pdf",
    }


# ============================================================================
# ENTITY FIXTURES (MOCK ENTITIES)
# ============================================================================

@pytest.fixture
def mock_dashboard() -> MagicMock:
    """Mock d'un tableau de bord."""
    dashboard = MagicMock()
    dashboard.id = 1
    dashboard.code = "DASH-001"
    dashboard.name = "Tableau de bord test"
    dashboard.description = "Description test"
    dashboard.dashboard_type = DashboardType.OPERATIONAL
    dashboard.owner_id = 1
    dashboard.is_shared = False
    dashboard.is_public = False
    dashboard.view_count = 0
    dashboard.widgets = []
    dashboard.created_at = datetime.utcnow()
    return dashboard


@pytest.fixture
def mock_widget() -> MagicMock:
    """Mock d'un widget."""
    widget = MagicMock()
    widget.id = 1
    widget.dashboard_id = 1
    widget.title = "Widget test"
    widget.widget_type = "chart"
    widget.chart_type = "bar"
    widget.position_x = 0
    widget.position_y = 0
    widget.width = 4
    widget.height = 4
    widget.created_at = datetime.utcnow()
    return widget


@pytest.fixture
def mock_report() -> MagicMock:
    """Mock d'un rapport."""
    report = MagicMock()
    report.id = 1
    report.code = "REP-001"
    report.name = "Rapport test"
    report.description = "Description test"
    report.report_type = ReportType.TABULAR
    report.owner_id = 1
    report.is_public = False
    report.available_formats = ["pdf", "xlsx"]
    report.schedules = []
    report.created_at = datetime.utcnow()
    return report


@pytest.fixture
def mock_report_execution() -> MagicMock:
    """Mock d'une exécution de rapport."""
    execution = MagicMock()
    execution.id = 1
    execution.report_id = 1
    execution.status = "completed"
    execution.output_format = "pdf"
    execution.file_path = "/path/to/file.pdf"
    execution.created_at = datetime.utcnow()
    return execution


@pytest.fixture
def mock_kpi() -> MagicMock:
    """Mock d'un KPI."""
    kpi = MagicMock()
    kpi.id = 1
    kpi.code = "KPI-001"
    kpi.name = "KPI test"
    kpi.description = "Description test"
    kpi.category = KPICategory.SALES
    kpi.unit = "€"
    kpi.precision = 2
    kpi.is_active = True
    kpi.is_system = False
    kpi.created_at = datetime.utcnow()
    return kpi


@pytest.fixture
def mock_kpi_value() -> MagicMock:
    """Mock d'une valeur KPI."""
    value = MagicMock()
    value.id = 1
    value.kpi_id = 1
    value.period_date = date.today()
    value.period_type = "daily"
    value.value = 1000.0
    value.previous_value = 900.0
    value.change_percentage = 11.11
    value.trend = KPITrend.UP
    value.created_at = datetime.utcnow()
    return value


@pytest.fixture
def mock_kpi_target() -> MagicMock:
    """Mock d'un objectif KPI."""
    target = MagicMock()
    target.id = 1
    target.kpi_id = 1
    target.year = 2024
    target.month = 1
    target.target_value = 5000.0
    target.created_at = datetime.utcnow()
    return target


@pytest.fixture
def mock_alert_rule() -> MagicMock:
    """Mock d'une règle d'alerte."""
    rule = MagicMock()
    rule.id = 1
    rule.code = "ALERT-001"
    rule.name = "Règle test"
    rule.description = "Description test"
    rule.severity = AlertSeverity.WARNING
    rule.source_type = "kpi"
    rule.source_id = 1
    rule.condition = {"operator": ">=", "value": 100}
    rule.is_enabled = True
    rule.created_at = datetime.utcnow()
    return rule


@pytest.fixture
def mock_alert() -> MagicMock:
    """Mock d'une alerte."""
    alert = MagicMock()
    alert.id = 1
    alert.rule_id = 1
    alert.title = "Alerte test"
    alert.message = "Message test"
    alert.severity = AlertSeverity.WARNING
    alert.status = AlertStatus.ACTIVE
    alert.source_type = "kpi"
    alert.source_id = 1
    alert.triggered_at = datetime.utcnow()
    return alert


@pytest.fixture
def mock_data_source() -> MagicMock:
    """Mock d'une source de données."""
    source = MagicMock()
    source.id = 1
    source.code = "DS-001"
    source.name = "Source test"
    source.description = "Description test"
    source.source_type = DataSourceType.DATABASE
    source.connection_config = {"host": "localhost"}
    source.is_active = True
    source.created_at = datetime.utcnow()
    return source


@pytest.fixture
def mock_data_query() -> MagicMock:
    """Mock d'une requête."""
    query = MagicMock()
    query.id = 1
    query.code = "QRY-001"
    query.name = "Requête test"
    query.description = "Description test"
    query.data_source_id = 1
    query.query_type = "sql"
    query.query_text = "SELECT * FROM test"
    query.is_active = True
    query.created_at = datetime.utcnow()
    return query


@pytest.fixture
def mock_bookmark() -> MagicMock:
    """Mock d'un favori."""
    bookmark = MagicMock()
    bookmark.id = 1
    bookmark.user_id = 1
    bookmark.item_type = "dashboard"
    bookmark.item_id = 1
    bookmark.item_name = "Dashboard test"
    bookmark.created_at = datetime.utcnow()
    return bookmark


@pytest.fixture
def mock_export() -> MagicMock:
    """Mock d'un export."""
    export = MagicMock()
    export.id = 1
    export.user_id = 1
    export.export_type = "dashboard"
    export.item_type = "dashboard"
    export.item_id = 1
    export.format = "pdf"
    export.file_name = "export-test.pdf"
    export.status = "completed"
    export.created_at = datetime.utcnow()
    return export


# ============================================================================
# HELPER ASSERTIONS
# ============================================================================

def assert_dashboard_response(response: dict[str, Any], expected_code: str):
    """Vérifier une réponse de tableau de bord."""
    assert response["code"] == expected_code
    assert "id" in response
    assert "name" in response
    assert "created_at" in response


def assert_widget_response(response: dict[str, Any]):
    """Vérifier une réponse de widget."""
    assert "id" in response
    assert "title" in response
    assert "widget_type" in response
    assert "created_at" in response


def assert_report_response(response: dict[str, Any], expected_code: str):
    """Vérifier une réponse de rapport."""
    assert response["code"] == expected_code
    assert "id" in response
    assert "name" in response
    assert "created_at" in response


def assert_kpi_response(response: dict[str, Any], expected_code: str):
    """Vérifier une réponse de KPI."""
    assert response["code"] == expected_code
    assert "id" in response
    assert "name" in response
    assert "category" in response


def assert_alert_rule_response(response: dict[str, Any], expected_code: str):
    """Vérifier une réponse de règle d'alerte."""
    assert response["code"] == expected_code
    assert "id" in response
    assert "name" in response
    assert "severity" in response


def assert_data_source_response(response: dict[str, Any], expected_code: str):
    """Vérifier une réponse de source de données."""
    assert response["code"] == expected_code
    assert "id" in response
    assert "name" in response
    assert "source_type" in response
