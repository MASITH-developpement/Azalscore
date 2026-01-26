"""
Tests pour le router BI v2 - CORE SaaS v2
"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status

from app.modules.bi.models import AlertSeverity, AlertStatus, DashboardType, KPICategory, ReportType



# ============================================================================
# DASHBOARDS - 10 tests
# ============================================================================

@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_create_dashboard(test_client, mock_service, mock_context, mock_saas_context, dashboard_data, mock_dashboard):
    """Test création d'un tableau de bord."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.create_dashboard.return_value = mock_dashboard

    response = test_client.post("/v2/bi/dashboards", json=dashboard_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["code"] == "DASH-001"
    mock_service.return_value.create_dashboard.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_list_dashboards(test_client, mock_service, mock_context, mock_saas_context, mock_dashboard):
    """Test liste des tableaux de bord."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.list_dashboards.return_value = ([mock_dashboard], 1)

    response = test_client.get("/v2/bi/dashboards")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    mock_service.return_value.list_dashboards.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_list_dashboards_with_filters(test_client, mock_service, mock_context, mock_saas_context, mock_dashboard):
    """Test liste des tableaux de bord avec filtres."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.list_dashboards.return_value = ([mock_dashboard], 1)

    response = test_client.get("/v2/bi/dashboards?dashboard_type=operational&owner_only=true")

    assert response.status_code == status.HTTP_200_OK
    mock_service.return_value.list_dashboards.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_dashboard(test_client, mock_service, mock_context, mock_saas_context, mock_dashboard):
    """Test récupération d'un tableau de bord."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.get_dashboard.return_value = mock_dashboard

    response = test_client.get("/v2/bi/dashboards/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "DASH-001"
    mock_service.return_value.get_dashboard.assert_called_once_with(1)


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_dashboard_not_found(test_client, mock_service, mock_context, mock_saas_context):
    """Test récupération d'un tableau de bord inexistant."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.get_dashboard.return_value = None

    response = test_client.get("/v2/bi/dashboards/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_update_dashboard(test_client, mock_service, mock_context, mock_saas_context, mock_dashboard):
    """Test mise à jour d'un tableau de bord."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.update_dashboard.return_value = mock_dashboard

    update_data = {"name": "Nouveau nom"}
    response = test_client.put("/v2/bi/dashboards/1", json=update_data)

    assert response.status_code == status.HTTP_200_OK
    mock_service.return_value.update_dashboard.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_delete_dashboard(test_client, mock_service, mock_context, mock_saas_context):
    """Test suppression d'un tableau de bord."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.delete_dashboard.return_value = True

    response = test_client.delete("/v2/bi/dashboards/1")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_service.return_value.delete_dashboard.assert_called_once_with(1)


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_delete_dashboard_not_found(test_client, mock_service, mock_context, mock_saas_context):
    """Test suppression d'un tableau de bord inexistant."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.delete_dashboard.return_value = False

    response = test_client.delete("/v2/bi/dashboards/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_duplicate_dashboard(test_client, mock_service, mock_context, mock_saas_context, mock_dashboard):
    """Test duplication d'un tableau de bord."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.duplicate_dashboard.return_value = mock_dashboard

    response = test_client.post("/v2/bi/dashboards/1/duplicate?new_code=DASH-002&new_name=Copie")

    assert response.status_code == status.HTTP_200_OK
    mock_service.return_value.duplicate_dashboard.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_dashboard_stats(test_client, mock_service, mock_context, mock_saas_context):
    """Test récupération des statistiques d'un tableau de bord."""
    mock_context.return_value = mock_saas_context
    stats = {
        "dashboard_id": 1,
        "dashboard_name": "Test",
        "widget_count": 5,
        "view_count": 100
    }
    mock_service.return_value.get_dashboard_stats.return_value = stats

    response = test_client.get("/v2/bi/dashboards/1/stats")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["widget_count"] == 5


# ============================================================================
# WIDGETS - 8 tests
# ============================================================================

@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_add_widget(test_client, mock_service, mock_context, mock_saas_context, widget_data, mock_widget):
    """Test ajout d'un widget."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.add_widget.return_value = mock_widget

    response = test_client.post("/v2/bi/dashboards/1/widgets", json=widget_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["title"] == "Widget test"
    mock_service.return_value.add_widget.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_add_widget_chart(test_client, mock_service, mock_context, mock_saas_context, mock_widget):
    """Test ajout d'un widget graphique."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.add_widget.return_value = mock_widget

    widget_data = {
        "title": "Chart Widget",
        "widget_type": "chart",
        "chart_type": "line",
        "position_x": 0,
        "position_y": 0,
        "width": 6,
        "height": 4
    }
    response = test_client.post("/v2/bi/dashboards/1/widgets", json=widget_data)

    assert response.status_code == status.HTTP_201_CREATED


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_update_widget(test_client, mock_service, mock_context, mock_saas_context, mock_widget):
    """Test mise à jour d'un widget."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.update_widget.return_value = mock_widget

    update_data = {"title": "Nouveau titre"}
    response = test_client.put("/v2/bi/widgets/1", json=update_data)

    assert response.status_code == status.HTTP_200_OK
    mock_service.return_value.update_widget.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_update_widget_config(test_client, mock_service, mock_context, mock_saas_context, mock_widget):
    """Test mise à jour de la configuration d'un widget."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.update_widget.return_value = mock_widget

    update_data = {"config": {"color": "blue", "size": "large"}}
    response = test_client.put("/v2/bi/widgets/1", json=update_data)

    assert response.status_code == status.HTTP_200_OK


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_delete_widget(test_client, mock_service, mock_context, mock_saas_context):
    """Test suppression d'un widget."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.delete_widget.return_value = True

    response = test_client.delete("/v2/bi/widgets/1")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_service.return_value.delete_widget.assert_called_once_with(1)


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_delete_widget_not_found(test_client, mock_service, mock_context, mock_saas_context):
    """Test suppression d'un widget inexistant."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.delete_widget.return_value = False

    response = test_client.delete("/v2/bi/widgets/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_update_widget_positions(test_client, mock_service, mock_context, mock_saas_context):
    """Test mise à jour des positions des widgets."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.update_widget_positions.return_value = True

    positions = [
        {"id": 1, "x": 0, "y": 0, "width": 4, "height": 4},
        {"id": 2, "x": 4, "y": 0, "width": 4, "height": 4}
    ]
    response = test_client.put("/v2/bi/dashboards/1/widgets/positions", json=positions)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_update_widget_positions_empty(test_client, mock_service, mock_context, mock_saas_context):
    """Test mise à jour avec liste vide."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.update_widget_positions.return_value = True

    response = test_client.put("/v2/bi/dashboards/1/widgets/positions", json=[])

    assert response.status_code == status.HTTP_200_OK


# ============================================================================
# REPORTS - 12 tests
# ============================================================================

@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_create_report(test_client, mock_service, mock_context, mock_saas_context, report_data, mock_report):
    """Test création d'un rapport."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.create_report.return_value = mock_report

    response = test_client.post("/v2/bi/reports", json=report_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["code"] == "REP-001"
    mock_service.return_value.create_report.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_list_reports(test_client, mock_service, mock_context, mock_saas_context, mock_report):
    """Test liste des rapports."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.list_reports.return_value = ([mock_report], 1)

    response = test_client.get("/v2/bi/reports")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    mock_service.return_value.list_reports.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_list_reports_with_type(test_client, mock_service, mock_context, mock_saas_context, mock_report):
    """Test liste des rapports avec filtre type."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.list_reports.return_value = ([mock_report], 1)

    response = test_client.get("/v2/bi/reports?report_type=tabular")

    assert response.status_code == status.HTTP_200_OK


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_report(test_client, mock_service, mock_context, mock_saas_context, mock_report):
    """Test récupération d'un rapport."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.get_report.return_value = mock_report

    response = test_client.get("/v2/bi/reports/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "REP-001"
    mock_service.return_value.get_report.assert_called_once_with(1)


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_report_not_found(test_client, mock_service, mock_context, mock_saas_context):
    """Test récupération d'un rapport inexistant."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.get_report.return_value = None

    response = test_client.get("/v2/bi/reports/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_update_report(test_client, mock_service, mock_context, mock_saas_context, mock_report):
    """Test mise à jour d'un rapport."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.update_report.return_value = mock_report

    update_data = {"name": "Nouveau nom"}
    response = test_client.put("/v2/bi/reports/1", json=update_data)

    assert response.status_code == status.HTTP_200_OK
    mock_service.return_value.update_report.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_delete_report(test_client, mock_service, mock_context, mock_saas_context):
    """Test suppression d'un rapport."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.delete_report.return_value = True

    response = test_client.delete("/v2/bi/reports/1")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_service.return_value.delete_report.assert_called_once_with(1)


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_delete_report_not_found(test_client, mock_service, mock_context, mock_saas_context):
    """Test suppression d'un rapport inexistant."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.delete_report.return_value = False

    response = test_client.delete("/v2/bi/reports/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_execute_report(test_client, mock_service, mock_context, mock_saas_context, mock_report_execution):
    """Test exécution d'un rapport."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.execute_report.return_value = mock_report_execution

    execute_data = {"output_format": "pdf", "async_execution": False}
    response = test_client.post("/v2/bi/reports/1/execute", json=execute_data)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "completed"
    mock_service.return_value.execute_report.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_execute_report_async(test_client, mock_service, mock_context, mock_saas_context, mock_report_execution):
    """Test exécution asynchrone d'un rapport."""
    mock_context.return_value = mock_saas_context
    mock_report_execution.status = "pending"
    mock_service.return_value.execute_report.return_value = mock_report_execution

    execute_data = {"output_format": "xlsx", "async_execution": True}
    response = test_client.post("/v2/bi/reports/1/execute", json=execute_data)

    assert response.status_code == status.HTTP_200_OK


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_report_executions(test_client, mock_service, mock_context, mock_saas_context, mock_report_execution):
    """Test récupération des exécutions d'un rapport."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.get_report_executions.return_value = [mock_report_execution]

    response = test_client.get("/v2/bi/reports/1/executions")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    mock_service.return_value.get_report_executions.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_report_executions_with_pagination(test_client, mock_service, mock_context, mock_saas_context):
    """Test récupération avec pagination."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.get_report_executions.return_value = []

    response = test_client.get("/v2/bi/reports/1/executions?skip=10&limit=5")

    assert response.status_code == status.HTTP_200_OK


# ============================================================================
# REPORT SCHEDULES - 6 tests
# ============================================================================

@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_create_schedule(test_client, mock_service, mock_context, mock_saas_context):
    """Test création d'une planification."""
    mock_context.return_value = mock_saas_context
    mock_schedule = MagicMock()
    mock_schedule.id = 1
    mock_schedule.name = "Planning test"
    mock_service.return_value.create_schedule.return_value = mock_schedule

    schedule_data = {
        "name": "Planning test",
        "frequency": "daily",
        "output_format": "pdf",
        "recipients": ["user@test.com"],
        "is_enabled": True
    }
    response = test_client.post("/v2/bi/reports/1/schedules", json=schedule_data)

    assert response.status_code == status.HTTP_201_CREATED
    mock_service.return_value.create_schedule.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_create_schedule_weekly(test_client, mock_service, mock_context, mock_saas_context):
    """Test création d'une planification hebdomadaire."""
    mock_context.return_value = mock_saas_context
    mock_schedule = MagicMock()
    mock_schedule.id = 1
    mock_service.return_value.create_schedule.return_value = mock_schedule

    schedule_data = {
        "name": "Weekly report",
        "frequency": "weekly",
        "output_format": "xlsx",
        "recipients": ["manager@test.com"],
        "is_enabled": True
    }
    response = test_client.post("/v2/bi/reports/1/schedules", json=schedule_data)

    assert response.status_code == status.HTTP_201_CREATED


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_create_schedule_monthly(test_client, mock_service, mock_context, mock_saas_context):
    """Test création d'une planification mensuelle."""
    mock_context.return_value = mock_saas_context
    mock_schedule = MagicMock()
    mock_schedule.id = 1
    mock_service.return_value.create_schedule.return_value = mock_schedule

    schedule_data = {
        "name": "Monthly report",
        "frequency": "monthly",
        "output_format": "pdf",
        "recipients": ["exec@test.com"],
        "is_enabled": True
    }
    response = test_client.post("/v2/bi/reports/1/schedules", json=schedule_data)

    assert response.status_code == status.HTTP_201_CREATED


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_create_schedule_with_cron(test_client, mock_service, mock_context, mock_saas_context):
    """Test création avec expression cron."""
    mock_context.return_value = mock_saas_context
    mock_schedule = MagicMock()
    mock_schedule.id = 1
    mock_service.return_value.create_schedule.return_value = mock_schedule

    schedule_data = {
        "name": "Custom schedule",
        "cron_expression": "0 8 * * 1",
        "output_format": "pdf",
        "recipients": ["team@test.com"],
        "is_enabled": True
    }
    response = test_client.post("/v2/bi/reports/1/schedules", json=schedule_data)

    assert response.status_code == status.HTTP_201_CREATED


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_create_schedule_disabled(test_client, mock_service, mock_context, mock_saas_context):
    """Test création d'une planification désactivée."""
    mock_context.return_value = mock_saas_context
    mock_schedule = MagicMock()
    mock_schedule.id = 1
    mock_service.return_value.create_schedule.return_value = mock_schedule

    schedule_data = {
        "name": "Disabled schedule",
        "frequency": "daily",
        "output_format": "pdf",
        "recipients": ["user@test.com"],
        "is_enabled": False
    }
    response = test_client.post("/v2/bi/reports/1/schedules", json=schedule_data)

    assert response.status_code == status.HTTP_201_CREATED


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_create_schedule_with_parameters(test_client, mock_service, mock_context, mock_saas_context):
    """Test création avec paramètres."""
    mock_context.return_value = mock_saas_context
    mock_schedule = MagicMock()
    mock_schedule.id = 1
    mock_service.return_value.create_schedule.return_value = mock_schedule

    schedule_data = {
        "name": "Parametrized schedule",
        "frequency": "daily",
        "output_format": "pdf",
        "parameters": {"region": "EU", "year": 2024},
        "recipients": ["analyst@test.com"],
        "is_enabled": True
    }
    response = test_client.post("/v2/bi/reports/1/schedules", json=schedule_data)

    assert response.status_code == status.HTTP_201_CREATED


# ============================================================================
# KPIs - 10 tests
# ============================================================================

@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_create_kpi(test_client, mock_service, mock_context, mock_saas_context, kpi_data, mock_kpi):
    """Test création d'un KPI."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.create_kpi.return_value = mock_kpi

    response = test_client.post("/v2/bi/kpis", json=kpi_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["code"] == "KPI-001"
    mock_service.return_value.create_kpi.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_list_kpis(test_client, mock_service, mock_context, mock_saas_context, mock_kpi, mock_kpi_value):
    """Test liste des KPIs."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.list_kpis.return_value = ([mock_kpi], 1)
    mock_service.return_value.get_kpi_current_value.return_value = mock_kpi_value

    response = test_client.get("/v2/bi/kpis")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    mock_service.return_value.list_kpis.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_list_kpis_by_category(test_client, mock_service, mock_context, mock_saas_context, mock_kpi, mock_kpi_value):
    """Test liste des KPIs par catégorie."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.list_kpis.return_value = ([mock_kpi], 1)
    mock_service.return_value.get_kpi_current_value.return_value = mock_kpi_value

    response = test_client.get("/v2/bi/kpis?category=sales")

    assert response.status_code == status.HTTP_200_OK


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_kpi(test_client, mock_service, mock_context, mock_saas_context, mock_kpi, mock_kpi_value):
    """Test récupération d'un KPI."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.get_kpi.return_value = mock_kpi
    mock_service.return_value.get_kpi_current_value.return_value = mock_kpi_value

    response = test_client.get("/v2/bi/kpis/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "KPI-001"
    mock_service.return_value.get_kpi.assert_called_once_with(1)


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_kpi_not_found(test_client, mock_service, mock_context, mock_saas_context):
    """Test récupération d'un KPI inexistant."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.get_kpi.return_value = None

    response = test_client.get("/v2/bi/kpis/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_update_kpi(test_client, mock_service, mock_context, mock_saas_context, mock_kpi):
    """Test mise à jour d'un KPI."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.update_kpi.return_value = mock_kpi

    update_data = {"name": "Nouveau nom"}
    response = test_client.put("/v2/bi/kpis/1", json=update_data)

    assert response.status_code == status.HTTP_200_OK
    mock_service.return_value.update_kpi.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_record_kpi_value(test_client, mock_service, mock_context, mock_saas_context, kpi_value_data, mock_kpi_value):
    """Test enregistrement d'une valeur KPI."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.record_kpi_value.return_value = mock_kpi_value

    response = test_client.post("/v2/bi/kpis/1/values", json=kpi_value_data)

    assert response.status_code == status.HTTP_201_CREATED
    mock_service.return_value.record_kpi_value.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_kpi_values(test_client, mock_service, mock_context, mock_saas_context, mock_kpi_value):
    """Test récupération des valeurs d'un KPI."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.get_kpi_values.return_value = [mock_kpi_value]

    response = test_client.get("/v2/bi/kpis/1/values")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    mock_service.return_value.get_kpi_values.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_kpi_values_with_dates(test_client, mock_service, mock_context, mock_saas_context, mock_kpi_value):
    """Test récupération des valeurs avec dates."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.get_kpi_values.return_value = [mock_kpi_value]

    response = test_client.get("/v2/bi/kpis/1/values?start_date=2024-01-01&end_date=2024-12-31")

    assert response.status_code == status.HTTP_200_OK


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_set_kpi_target(test_client, mock_service, mock_context, mock_saas_context, kpi_target_data, mock_kpi_target):
    """Test définition d'un objectif KPI."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.set_kpi_target.return_value = mock_kpi_target

    response = test_client.post("/v2/bi/kpis/1/targets", json=kpi_target_data)

    assert response.status_code == status.HTTP_201_CREATED
    mock_service.return_value.set_kpi_target.assert_called_once()


# ============================================================================
# KPI TARGETS - 4 tests
# ============================================================================

@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_set_kpi_target_yearly(test_client, mock_service, mock_context, mock_saas_context, mock_kpi_target):
    """Test objectif annuel."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.set_kpi_target.return_value = mock_kpi_target

    target_data = {"year": 2024, "target_value": 10000.0}
    response = test_client.post("/v2/bi/kpis/1/targets", json=target_data)

    assert response.status_code == status.HTTP_201_CREATED


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_set_kpi_target_monthly(test_client, mock_service, mock_context, mock_saas_context, mock_kpi_target):
    """Test objectif mensuel."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.set_kpi_target.return_value = mock_kpi_target

    target_data = {"year": 2024, "month": 6, "target_value": 1000.0}
    response = test_client.post("/v2/bi/kpis/1/targets", json=target_data)

    assert response.status_code == status.HTTP_201_CREATED


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_set_kpi_target_quarterly(test_client, mock_service, mock_context, mock_saas_context, mock_kpi_target):
    """Test objectif trimestriel."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.set_kpi_target.return_value = mock_kpi_target

    target_data = {"year": 2024, "quarter": 2, "target_value": 3000.0}
    response = test_client.post("/v2/bi/kpis/1/targets", json=target_data)

    assert response.status_code == status.HTTP_201_CREATED


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_set_kpi_target_with_range(test_client, mock_service, mock_context, mock_saas_context, mock_kpi_target):
    """Test objectif avec plage min/max."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.set_kpi_target.return_value = mock_kpi_target

    target_data = {
        "year": 2024,
        "target_value": 5000.0,
        "min_value": 4000.0,
        "max_value": 6000.0
    }
    response = test_client.post("/v2/bi/kpis/1/targets", json=target_data)

    assert response.status_code == status.HTTP_201_CREATED


# ============================================================================
# KPI VALUES - 4 tests
# ============================================================================

@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_record_kpi_value_daily(test_client, mock_service, mock_context, mock_saas_context, mock_kpi_value):
    """Test valeur quotidienne."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.record_kpi_value.return_value = mock_kpi_value

    value_data = {
        "period_date": str(date.today()),
        "period_type": "daily",
        "value": 500.0
    }
    response = test_client.post("/v2/bi/kpis/1/values", json=value_data)

    assert response.status_code == status.HTTP_201_CREATED


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_record_kpi_value_weekly(test_client, mock_service, mock_context, mock_saas_context, mock_kpi_value):
    """Test valeur hebdomadaire."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.record_kpi_value.return_value = mock_kpi_value

    value_data = {
        "period_date": str(date.today()),
        "period_type": "weekly",
        "value": 3500.0
    }
    response = test_client.post("/v2/bi/kpis/1/values", json=value_data)

    assert response.status_code == status.HTTP_201_CREATED


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_record_kpi_value_monthly(test_client, mock_service, mock_context, mock_saas_context, mock_kpi_value):
    """Test valeur mensuelle."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.record_kpi_value.return_value = mock_kpi_value

    value_data = {
        "period_date": str(date.today()),
        "period_type": "monthly",
        "value": 15000.0
    }
    response = test_client.post("/v2/bi/kpis/1/values", json=value_data)

    assert response.status_code == status.HTTP_201_CREATED


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_record_kpi_value_with_dimension(test_client, mock_service, mock_context, mock_saas_context, mock_kpi_value):
    """Test valeur avec dimension."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.record_kpi_value.return_value = mock_kpi_value

    value_data = {
        "period_date": str(date.today()),
        "period_type": "daily",
        "value": 800.0,
        "dimension": "region",
        "dimension_value": "EU"
    }
    response = test_client.post("/v2/bi/kpis/1/values", json=value_data)

    assert response.status_code == status.HTTP_201_CREATED


# ============================================================================
# DATA SOURCES - 8 tests
# ============================================================================

@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_create_data_source(test_client, mock_service, mock_context, mock_saas_context, data_source_data, mock_data_source):
    """Test création d'une source de données."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.create_data_source.return_value = mock_data_source

    response = test_client.post("/v2/bi/data-sources", json=data_source_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["code"] == "DS-001"
    mock_service.return_value.create_data_source.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_list_data_sources(test_client, mock_service, mock_context, mock_saas_context, mock_data_source):
    """Test liste des sources de données."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.list_data_sources.return_value = ([mock_data_source], 1)

    response = test_client.get("/v2/bi/data-sources")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    mock_service.return_value.list_data_sources.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_list_data_sources_by_type(test_client, mock_service, mock_context, mock_saas_context, mock_data_source):
    """Test liste par type."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.list_data_sources.return_value = ([mock_data_source], 1)

    response = test_client.get("/v2/bi/data-sources?source_type=database")

    assert response.status_code == status.HTTP_200_OK


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_data_source(test_client, mock_service, mock_context, mock_saas_context, mock_data_source):
    """Test récupération d'une source."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.get_data_source.return_value = mock_data_source

    response = test_client.get("/v2/bi/data-sources/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "DS-001"


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_data_source_not_found(test_client, mock_service, mock_context, mock_saas_context):
    """Test source inexistante."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.get_data_source.return_value = None

    response = test_client.get("/v2/bi/data-sources/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_update_data_source(test_client, mock_service, mock_context, mock_saas_context, mock_data_source):
    """Test mise à jour d'une source."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.update_data_source.return_value = mock_data_source

    update_data = {"name": "Nouveau nom"}
    response = test_client.put("/v2/bi/data-sources/1", json=update_data)

    assert response.status_code == status.HTTP_200_OK
    mock_service.return_value.update_data_source.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_update_data_source_config(test_client, mock_service, mock_context, mock_saas_context, mock_data_source):
    """Test mise à jour de la configuration."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.update_data_source.return_value = mock_data_source

    update_data = {"connection_config": {"host": "new-host", "port": 5432}}
    response = test_client.put("/v2/bi/data-sources/1", json=update_data)

    assert response.status_code == status.HTTP_200_OK


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_create_data_source_api(test_client, mock_service, mock_context, mock_saas_context, mock_data_source):
    """Test création source API."""
    mock_context.return_value = mock_saas_context
    mock_data_source.source_type = DataSourceType.API
    mock_service.return_value.create_data_source.return_value = mock_data_source

    source_data = {
        "code": "API-001",
        "name": "API Source",
        "source_type": "api",
        "connection_config": {"url": "https://api.example.com"}
    }
    response = test_client.post("/v2/bi/data-sources", json=source_data)

    assert response.status_code == status.HTTP_201_CREATED


# ============================================================================
# DATA QUERIES - 4 tests
# ============================================================================

@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_create_query(test_client, mock_service, mock_context, mock_saas_context, data_query_data, mock_data_query):
    """Test création d'une requête."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.create_query.return_value = mock_data_query

    response = test_client.post("/v2/bi/queries", json=data_query_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["code"] == "QRY-001"
    mock_service.return_value.create_query.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_list_queries(test_client, mock_service, mock_context, mock_saas_context, mock_data_query):
    """Test liste des requêtes."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.list_queries.return_value = ([mock_data_query], 1)

    response = test_client.get("/v2/bi/queries")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    mock_service.return_value.list_queries.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_query(test_client, mock_service, mock_context, mock_saas_context, mock_data_query):
    """Test récupération d'une requête."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.get_query.return_value = mock_data_query

    response = test_client.get("/v2/bi/queries/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["code"] == "QRY-001"


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_query_not_found(test_client, mock_service, mock_context, mock_saas_context):
    """Test requête inexistante."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.get_query.return_value = None

    response = test_client.get("/v2/bi/queries/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# ALERTS - 6 tests
# ============================================================================

@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_list_alerts(test_client, mock_service, mock_context, mock_saas_context, mock_alert):
    """Test liste des alertes."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.list_alerts.return_value = ([mock_alert], 1)

    response = test_client.get("/v2/bi/alerts")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_list_alerts_with_filters(test_client, mock_service, mock_context, mock_saas_context, mock_alert):
    """Test liste avec filtres."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.list_alerts.return_value = ([mock_alert], 1)

    response = test_client.get("/v2/bi/alerts?status_filter=active&severity=warning")

    assert response.status_code == status.HTTP_200_OK


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_alert(test_client, mock_service, mock_context, mock_saas_context, mock_alert):
    """Test récupération d'une alerte."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.get_alert.return_value = mock_alert

    response = test_client.get("/v2/bi/alerts/1")

    assert response.status_code == status.HTTP_200_OK


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_acknowledge_alert(test_client, mock_service, mock_context, mock_saas_context, mock_alert):
    """Test acquittement d'une alerte."""
    mock_context.return_value = mock_saas_context
    mock_alert.status = AlertStatus.ACKNOWLEDGED
    mock_service.return_value.acknowledge_alert.return_value = mock_alert

    ack_data = {"notes": "Pris en compte"}
    response = test_client.post("/v2/bi/alerts/1/acknowledge", json=ack_data)

    assert response.status_code == status.HTTP_200_OK


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_snooze_alert(test_client, mock_service, mock_context, mock_saas_context, mock_alert):
    """Test mise en pause d'une alerte."""
    mock_context.return_value = mock_saas_context
    mock_alert.status = AlertStatus.SNOOZED
    mock_service.return_value.snooze_alert.return_value = mock_alert

    snooze_data = {"snooze_until": datetime.utcnow().isoformat()}
    response = test_client.post("/v2/bi/alerts/1/snooze", json=snooze_data)

    assert response.status_code == status.HTTP_200_OK


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_resolve_alert(test_client, mock_service, mock_context, mock_saas_context, mock_alert):
    """Test résolution d'une alerte."""
    mock_context.return_value = mock_saas_context
    mock_alert.status = AlertStatus.RESOLVED
    mock_service.return_value.resolve_alert.return_value = mock_alert

    resolve_data = {"resolution_notes": "Problème résolu"}
    response = test_client.post("/v2/bi/alerts/1/resolve", json=resolve_data)

    assert response.status_code == status.HTTP_200_OK


# ============================================================================
# ALERT RULES - 6 tests
# ============================================================================

@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_create_alert_rule(test_client, mock_service, mock_context, mock_saas_context, alert_rule_data, mock_alert_rule):
    """Test création d'une règle d'alerte."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.create_alert_rule.return_value = mock_alert_rule

    response = test_client.post("/v2/bi/alert-rules", json=alert_rule_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["code"] == "ALERT-001"


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_list_alert_rules(test_client, mock_service, mock_context, mock_saas_context, mock_alert_rule):
    """Test liste des règles."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.list_alert_rules.return_value = ([mock_alert_rule], 1)

    response = test_client.get("/v2/bi/alert-rules")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_alert_rule(test_client, mock_service, mock_context, mock_saas_context, mock_alert_rule):
    """Test récupération d'une règle."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.get_alert_rule.return_value = mock_alert_rule

    response = test_client.get("/v2/bi/alert-rules/1")

    assert response.status_code == status.HTTP_200_OK


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_alert_rule_not_found(test_client, mock_service, mock_context, mock_saas_context):
    """Test règle inexistante."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.get_alert_rule.return_value = None

    response = test_client.get("/v2/bi/alert-rules/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_update_alert_rule(test_client, mock_service, mock_context, mock_saas_context, mock_alert_rule):
    """Test mise à jour d'une règle."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.update_alert_rule.return_value = mock_alert_rule

    update_data = {"is_enabled": False}
    response = test_client.put("/v2/bi/alert-rules/1", json=update_data)

    assert response.status_code == status.HTTP_200_OK


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_update_alert_rule_severity(test_client, mock_service, mock_context, mock_saas_context, mock_alert_rule):
    """Test modification de la sévérité."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.update_alert_rule.return_value = mock_alert_rule

    update_data = {"severity": "critical"}
    response = test_client.put("/v2/bi/alert-rules/1", json=update_data)

    assert response.status_code == status.HTTP_200_OK


# ============================================================================
# BOOKMARKS - 4 tests
# ============================================================================

@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_create_bookmark(test_client, mock_service, mock_context, mock_saas_context, bookmark_data, mock_bookmark):
    """Test création d'un favori."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.create_bookmark.return_value = mock_bookmark

    response = test_client.post("/v2/bi/bookmarks", json=bookmark_data)

    assert response.status_code == status.HTTP_201_CREATED
    mock_service.return_value.create_bookmark.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_list_bookmarks(test_client, mock_service, mock_context, mock_saas_context, mock_bookmark):
    """Test liste des favoris."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.list_bookmarks.return_value = [mock_bookmark]

    response = test_client.get("/v2/bi/bookmarks")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_list_bookmarks_by_type(test_client, mock_service, mock_context, mock_saas_context, mock_bookmark):
    """Test liste par type."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.list_bookmarks.return_value = [mock_bookmark]

    response = test_client.get("/v2/bi/bookmarks?item_type=dashboard")

    assert response.status_code == status.HTTP_200_OK


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_delete_bookmark(test_client, mock_service, mock_context, mock_saas_context):
    """Test suppression d'un favori."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.delete_bookmark.return_value = True

    response = test_client.delete("/v2/bi/bookmarks/1")

    assert response.status_code == status.HTTP_204_NO_CONTENT


# ============================================================================
# EXPORTS - 2 tests
# ============================================================================

@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_create_export(test_client, mock_service, mock_context, mock_saas_context, export_data, mock_export):
    """Test création d'un export."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.create_export.return_value = mock_export

    response = test_client.post("/v2/bi/exports", json=export_data)

    assert response.status_code == status.HTTP_201_CREATED
    mock_service.return_value.create_export.assert_called_once()


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_list_exports(test_client, mock_service, mock_context, mock_saas_context, mock_export):
    """Test liste des exports."""
    mock_context.return_value = mock_saas_context
    mock_service.return_value.list_exports.return_value = [mock_export]

    response = test_client.get("/v2/bi/exports")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


# ============================================================================
# OVERVIEW - 2 tests
# ============================================================================

@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_overview(test_client, mock_service, mock_context, mock_saas_context):
    """Test vue d'ensemble."""
    mock_context.return_value = mock_saas_context
    overview_data = {
        "dashboards": {"total": 10},
        "reports": {"total": 5},
        "kpis": {"total": 20},
        "alerts": {"active": 3, "critical": 1},
        "data_sources": {"total": 4}
    }
    mock_service.return_value.get_overview.return_value = overview_data

    response = test_client.get("/v2/bi/overview")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "dashboards" in data
    assert "reports" in data
    assert "kpis" in data


@patch("app.modules.bi.router_v2.get_saas_context")
@patch("app.modules.bi.router_v2.get_bi_service")
def test_get_overview_empty(test_client, mock_service, mock_context, mock_saas_context):
    """Test vue d'ensemble vide."""
    mock_context.return_value = mock_saas_context
    overview_data = {
        "dashboards": {"total": 0},
        "reports": {"total": 0},
        "kpis": {"total": 0},
        "alerts": {"active": 0},
        "data_sources": {"total": 0}
    }
    mock_service.return_value.get_overview.return_value = overview_data

    response = test_client.get("/v2/bi/overview")

    assert response.status_code == status.HTTP_200_OK
