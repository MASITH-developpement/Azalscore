"""
Tests pour le router QC v2 - CORE SaaS
=======================================
"""

import pytest
from datetime import datetime


# ============================================================================
# TESTS - QC RULES (5 endpoints)
# ============================================================================

def test_create_rule(client, qc_rule_data, mock_qc_service, qc_rule_entity):
    """Test création d'une règle QC"""
    mock_qc_service.create_rule.return_value = qc_rule_entity
    response = client.post("/v2/qc/rules", json=qc_rule_data)
    assert response.status_code == 201
    assert response.json()["code"] == "QC001"
    assert response.json()["name"] == "Test Coverage Minimum"
    mock_qc_service.create_rule.assert_called_once()


def test_list_rules(client, mock_qc_service, qc_rule_entity):
    """Test liste des règles QC"""
    mock_qc_service.list_rules.return_value = ([qc_rule_entity], 1)
    response = client.get("/v2/qc/rules")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["code"] == "QC001"


def test_list_rules_with_filters(client, mock_qc_service, qc_rule_entity):
    """Test liste des règles avec filtres"""
    mock_qc_service.list_rules.return_value = ([qc_rule_entity], 1)
    response = client.get("/v2/qc/rules?category=TESTING&severity=WARNING&is_active=true")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


def test_get_rule(client, mock_qc_service, qc_rule_entity):
    """Test récupération d'une règle"""
    mock_qc_service.get_rule.return_value = qc_rule_entity
    response = client.get("/v2/qc/rules/1")
    assert response.status_code == 200
    assert response.json()["code"] == "QC001"
    mock_qc_service.get_rule.assert_called_once_with(1)


def test_get_rule_not_found(client, mock_qc_service):
    """Test règle non trouvée"""
    mock_qc_service.get_rule.return_value = None
    response = client.get("/v2/qc/rules/999")
    assert response.status_code == 404


def test_update_rule(client, mock_qc_service, qc_rule_entity):
    """Test mise à jour d'une règle"""
    updated_rule = qc_rule_entity
    updated_rule.name = "Updated Rule"
    mock_qc_service.update_rule.return_value = updated_rule
    response = client.put("/v2/qc/rules/1", json={"name": "Updated Rule"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Rule"


def test_update_rule_not_found(client, mock_qc_service):
    """Test mise à jour règle non trouvée"""
    mock_qc_service.update_rule.return_value = None
    response = client.put("/v2/qc/rules/999", json={"name": "Updated"})
    assert response.status_code == 404


def test_delete_rule(client, mock_qc_service):
    """Test suppression d'une règle"""
    mock_qc_service.delete_rule.return_value = True
    response = client.delete("/v2/qc/rules/1")
    assert response.status_code == 204


def test_delete_rule_not_found(client, mock_qc_service):
    """Test suppression règle non trouvée"""
    mock_qc_service.delete_rule.return_value = False
    response = client.delete("/v2/qc/rules/999")
    assert response.status_code == 404


# ============================================================================
# TESTS - MODULES REGISTRY (6 endpoints)
# ============================================================================

def test_register_module(client, module_registry_data, mock_qc_service, module_registry_entity):
    """Test enregistrement d'un module"""
    mock_qc_service.register_module.return_value = module_registry_entity
    response = client.post("/v2/qc/modules", json=module_registry_data)
    assert response.status_code == 201
    assert response.json()["module_code"] == "TEST_MODULE"
    assert response.json()["module_name"] == "Test Module"


def test_list_modules(client, mock_qc_service, module_registry_entity):
    """Test liste des modules"""
    mock_qc_service.list_modules.return_value = ([module_registry_entity], 1)
    response = client.get("/v2/qc/modules")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_list_modules_with_filters(client, mock_qc_service, module_registry_entity):
    """Test liste des modules avec filtres"""
    mock_qc_service.list_modules.return_value = ([module_registry_entity], 1)
    response = client.get("/v2/qc/modules?status=DEVELOPMENT&has_tests=true")
    assert response.status_code == 200


def test_get_module(client, mock_qc_service, module_registry_entity):
    """Test récupération d'un module"""
    mock_qc_service.get_module.return_value = module_registry_entity
    response = client.get("/v2/qc/modules/1")
    assert response.status_code == 200
    assert response.json()["module_code"] == "TEST_MODULE"


def test_get_module_not_found(client, mock_qc_service):
    """Test module non trouvé"""
    mock_qc_service.get_module.return_value = None
    response = client.get("/v2/qc/modules/999")
    assert response.status_code == 404


def test_get_module_by_code(client, mock_qc_service, module_registry_entity):
    """Test récupération d'un module par code"""
    mock_qc_service.get_module_by_code.return_value = module_registry_entity
    response = client.get("/v2/qc/modules/code/TEST_MODULE")
    assert response.status_code == 200
    assert response.json()["module_code"] == "TEST_MODULE"


def test_get_module_by_code_not_found(client, mock_qc_service):
    """Test module par code non trouvé"""
    mock_qc_service.get_module_by_code.return_value = None
    response = client.get("/v2/qc/modules/code/UNKNOWN")
    assert response.status_code == 404


def test_update_module_status(client, mock_qc_service, module_registry_entity):
    """Test mise à jour du statut d'un module"""
    mock_qc_service.update_module_status.return_value = module_registry_entity
    response = client.put("/v2/qc/modules/1/status", json={"status": "QC_PASSED"})
    assert response.status_code == 200


def test_update_module_status_not_found(client, mock_qc_service):
    """Test mise à jour statut module non trouvé"""
    mock_qc_service.update_module_status.return_value = None
    response = client.put("/v2/qc/modules/999/status", json={"status": "QC_PASSED"})
    assert response.status_code == 404


def test_get_module_scores(client, mock_qc_service, module_registry_entity):
    """Test récupération des scores d'un module"""
    module_registry_entity.overall_score = 85.5
    module_registry_entity.architecture_score = 90.0
    mock_qc_service.get_module.return_value = module_registry_entity
    response = client.get("/v2/qc/modules/1/scores")
    assert response.status_code == 200
    data = response.json()
    assert data["overall_score"] == 85.5
    assert data["architecture_score"] == 90.0


def test_get_module_scores_not_found(client, mock_qc_service):
    """Test scores module non trouvé"""
    mock_qc_service.get_module.return_value = None
    response = client.get("/v2/qc/modules/999/scores")
    assert response.status_code == 404


# ============================================================================
# TESTS - VALIDATIONS (4 endpoints)
# ============================================================================

def test_run_validation(client, validation_data, mock_qc_service, validation_entity):
    """Test exécution d'une validation"""
    mock_qc_service.run_validation.return_value = validation_entity
    response = client.post("/v2/qc/validations/run", json=validation_data)
    assert response.status_code == 200
    data = response.json()
    assert data["module_id"] == 1
    assert data["status"] == "RUNNING"


def test_run_validation_module_not_found(client, validation_data, mock_qc_service):
    """Test validation module non trouvé"""
    mock_qc_service.run_validation.side_effect = ValueError("Module not found")
    response = client.post("/v2/qc/validations/run", json=validation_data)
    assert response.status_code == 404


def test_list_validations(client, mock_qc_service, validation_entity):
    """Test liste des validations"""
    mock_qc_service.list_validations.return_value = ([validation_entity], 1)
    response = client.get("/v2/qc/validations")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_list_validations_with_filters(client, mock_qc_service, validation_entity):
    """Test liste des validations avec filtres"""
    mock_qc_service.list_validations.return_value = ([validation_entity], 1)
    response = client.get("/v2/qc/validations?module_id=1&phase=AUTOMATED&status=RUNNING")
    assert response.status_code == 200


def test_get_validation(client, mock_qc_service, validation_entity):
    """Test récupération d'une validation"""
    mock_qc_service.get_validation.return_value = validation_entity
    response = client.get("/v2/qc/validations/1")
    assert response.status_code == 200
    assert response.json()["module_id"] == 1


def test_get_validation_not_found(client, mock_qc_service):
    """Test validation non trouvée"""
    mock_qc_service.get_validation.return_value = None
    response = client.get("/v2/qc/validations/999")
    assert response.status_code == 404


def test_get_validation_results(client, mock_qc_service):
    """Test récupération des résultats d'une validation"""
    mock_qc_service.get_check_results.return_value = ([], 0)
    response = client.get("/v2/qc/validations/1/results")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0


def test_get_validation_results_with_filters(client, mock_qc_service):
    """Test résultats validation avec filtres"""
    mock_qc_service.get_check_results.return_value = ([], 0)
    response = client.get("/v2/qc/validations/1/results?status=PASSED&category=TESTING")
    assert response.status_code == 200


# ============================================================================
# TESTS - TESTS (3 endpoints)
# ============================================================================

def test_create_test_run(client, test_run_data, mock_qc_service, test_run_entity):
    """Test création d'un test run"""
    mock_qc_service.record_test_run.return_value = test_run_entity
    response = client.post("/v2/qc/tests", json=test_run_data)
    assert response.status_code == 201
    data = response.json()
    assert data["module_id"] == 1
    assert data["total_tests"] == 100
    assert data["passed_tests"] == 95


def test_list_test_runs(client, mock_qc_service, test_run_entity):
    """Test liste des test runs"""
    mock_qc_service.get_test_runs.return_value = ([test_run_entity], 1)
    response = client.get("/v2/qc/tests")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_list_test_runs_with_filters(client, mock_qc_service, test_run_entity):
    """Test liste des test runs avec filtres"""
    mock_qc_service.get_test_runs.return_value = ([test_run_entity], 1)
    response = client.get("/v2/qc/tests?module_id=1&test_type=UNIT&passed=true")
    assert response.status_code == 200


def test_get_module_tests(client, mock_qc_service, test_run_entity):
    """Test récupération des tests d'un module"""
    mock_qc_service.get_test_runs.return_value = ([test_run_entity], 1)
    response = client.get("/v2/qc/tests/module/1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["module_id"] == 1


# ============================================================================
# TESTS - METRICS (3 endpoints)
# ============================================================================

def test_record_metric(client, mock_qc_service, metric_entity):
    """Test enregistrement d'une métrique"""
    mock_qc_service.record_metrics.return_value = metric_entity
    response = client.post("/v2/qc/metrics/record")
    assert response.status_code == 200
    data = response.json()
    assert data["modules_total"] == 10
    assert data["avg_overall_score"] == 85.5


def test_get_metrics_history(client, mock_qc_service, metric_entity):
    """Test récupération de l'historique des métriques"""
    mock_qc_service.get_metrics_history.return_value = [metric_entity]
    response = client.get("/v2/qc/metrics/history")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["modules_total"] == 10


def test_get_metrics_history_with_filters(client, mock_qc_service, metric_entity):
    """Test historique métriques avec filtres"""
    mock_qc_service.get_metrics_history.return_value = [metric_entity]
    response = client.get("/v2/qc/metrics/history?module_id=1&start_date=2024-01-01T00:00:00&end_date=2024-12-31T23:59:59")
    assert response.status_code == 200


def test_get_latest_metrics(client, mock_qc_service, metric_entity):
    """Test récupération des dernières métriques"""
    mock_qc_service.get_metrics_history.return_value = [metric_entity]
    response = client.get("/v2/qc/metrics/latest")
    assert response.status_code == 200
    data = response.json()
    assert data["modules_total"] == 10


def test_get_latest_metrics_empty(client, mock_qc_service):
    """Test dernières métriques vides"""
    mock_qc_service.get_metrics_history.return_value = []
    response = client.get("/v2/qc/metrics/latest")
    assert response.status_code == 200
    assert response.json() is None


# ============================================================================
# TESTS - ALERTS (4 endpoints)
# ============================================================================

def test_create_alert(client, alert_data, mock_qc_service, alert_entity):
    """Test création d'une alerte"""
    mock_qc_service.create_alert.return_value = alert_entity
    response = client.post("/v2/qc/alerts", json=alert_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "QC Failed: TEST_MODULE"
    assert data["severity"] == "CRITICAL"


def test_list_alerts(client, mock_qc_service, alert_entity):
    """Test liste des alertes"""
    mock_qc_service.list_alerts.return_value = ([alert_entity], 1)
    response = client.get("/v2/qc/alerts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_list_alerts_with_filters(client, mock_qc_service, alert_entity):
    """Test liste des alertes avec filtres"""
    mock_qc_service.list_alerts.return_value = ([alert_entity], 1)
    response = client.get("/v2/qc/alerts?severity=CRITICAL&is_resolved=false&module_id=1")
    assert response.status_code == 200


def test_get_unresolved_alerts(client, mock_qc_service, alert_entity):
    """Test récupération des alertes non résolues"""
    mock_qc_service.list_alerts.return_value = ([alert_entity], 1)
    response = client.get("/v2/qc/alerts/unresolved")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["is_resolved"] is False


def test_resolve_alert(client, mock_qc_service, alert_entity):
    """Test résolution d'une alerte"""
    resolved_alert = alert_entity
    resolved_alert.is_resolved = True
    mock_qc_service.resolve_alert.return_value = resolved_alert
    response = client.post("/v2/qc/alerts/1/resolve", json={"resolution_notes": "Fixed"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_resolved"] is True


def test_resolve_alert_not_found(client, mock_qc_service):
    """Test résolution alerte non trouvée"""
    mock_qc_service.resolve_alert.return_value = None
    response = client.post("/v2/qc/alerts/999/resolve", json={"resolution_notes": "Fixed"})
    assert response.status_code == 404


# ============================================================================
# TESTS - DASHBOARDS (5 endpoints)
# ============================================================================

def test_create_dashboard(client, dashboard_data, mock_qc_service, dashboard_entity):
    """Test création d'un dashboard"""
    mock_qc_service.create_dashboard.return_value = dashboard_entity
    response = client.post("/v2/qc/dashboards", json=dashboard_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "QC Dashboard"
    assert data["is_default"] is True


def test_list_dashboards(client, mock_qc_service, dashboard_entity):
    """Test liste des dashboards"""
    mock_qc_service.list_dashboards.return_value = [dashboard_entity]
    response = client.get("/v2/qc/dashboards")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "QC Dashboard"


def test_get_dashboard(client, mock_qc_service, dashboard_entity):
    """Test récupération d'un dashboard"""
    mock_qc_service.get_dashboard.return_value = dashboard_entity
    response = client.get("/v2/qc/dashboards/1")
    assert response.status_code == 200
    assert response.json()["name"] == "QC Dashboard"


def test_get_dashboard_not_found(client, mock_qc_service):
    """Test dashboard non trouvé"""
    mock_qc_service.get_dashboard.return_value = None
    response = client.get("/v2/qc/dashboards/999")
    assert response.status_code == 404


def test_get_dashboard_data(client, mock_qc_service, dashboard_entity):
    """Test récupération des données d'un dashboard"""
    mock_qc_service.get_dashboard.return_value = dashboard_entity
    mock_qc_service.get_dashboard_data.return_value = {
        "summary": {
            "total_modules": 10,
            "validated_modules": 8,
            "production_modules": 5,
            "failed_modules": 2,
            "average_score": 85.5,
            "unresolved_alerts": 3,
        },
        "status_distribution": {},
        "recent_validations": [],
        "recent_tests": [],
        "critical_alerts": [],
    }
    response = client.get("/v2/qc/dashboards/1/data")
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_modules"] == 10


def test_get_dashboard_data_not_found(client, mock_qc_service):
    """Test données dashboard non trouvé"""
    mock_qc_service.get_dashboard.return_value = None
    response = client.get("/v2/qc/dashboards/999/data")
    assert response.status_code == 404


def test_get_default_dashboard_data(client, mock_qc_service):
    """Test récupération des données du dashboard par défaut"""
    mock_qc_service.get_dashboard_data.return_value = {
        "summary": {
            "total_modules": 10,
            "validated_modules": 8,
            "production_modules": 5,
            "failed_modules": 2,
            "average_score": 85.5,
            "unresolved_alerts": 3,
        },
        "status_distribution": {},
        "recent_validations": [],
        "recent_tests": [],
        "critical_alerts": [],
    }
    response = client.get("/v2/qc/dashboards/default/data")
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_modules"] == 10


# ============================================================================
# TESTS - TEMPLATES (4 endpoints)
# ============================================================================

def test_create_template(client, template_data, mock_qc_service, template_entity):
    """Test création d'un template"""
    mock_qc_service.create_template.return_value = template_entity
    response = client.post("/v2/qc/templates", json=template_data)
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "TPL_BASIC"
    assert data["name"] == "Basic QC Template"


def test_list_templates(client, mock_qc_service, template_entity):
    """Test liste des templates"""
    mock_qc_service.list_templates.return_value = [template_entity]
    response = client.get("/v2/qc/templates")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["code"] == "TPL_BASIC"


def test_list_templates_with_filter(client, mock_qc_service, template_entity):
    """Test liste des templates avec filtre"""
    mock_qc_service.list_templates.return_value = [template_entity]
    response = client.get("/v2/qc/templates?category=standard")
    assert response.status_code == 200


def test_get_template(client, mock_qc_service, template_entity):
    """Test récupération d'un template"""
    mock_qc_service.get_template.return_value = template_entity
    response = client.get("/v2/qc/templates/1")
    assert response.status_code == 200
    assert response.json()["code"] == "TPL_BASIC"


def test_get_template_not_found(client, mock_qc_service):
    """Test template non trouvé"""
    mock_qc_service.get_template.return_value = None
    response = client.get("/v2/qc/templates/999")
    assert response.status_code == 404


def test_apply_template(client, mock_qc_service, qc_rule_entity):
    """Test application d'un template"""
    mock_qc_service.apply_template.return_value = [qc_rule_entity]
    response = client.post("/v2/qc/templates/1/apply")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["code"] == "QC001"


def test_apply_template_not_found(client, mock_qc_service):
    """Test application template non trouvé"""
    mock_qc_service.apply_template.return_value = []
    response = client.post("/v2/qc/templates/999/apply")
    assert response.status_code == 404


# ============================================================================
# TESTS - STATS (2 endpoints)
# ============================================================================

def test_get_stats(client, mock_qc_service, module_registry_entity, qc_rule_entity, alert_entity, test_run_entity):
    """Test récupération des statistiques globales"""
    mock_qc_service.list_modules.return_value = ([module_registry_entity], 1)
    mock_qc_service.list_rules.return_value = ([qc_rule_entity], 1)
    mock_qc_service.list_alerts.return_value = ([alert_entity], 1)
    mock_qc_service.get_test_runs.return_value = ([test_run_entity], 1)

    response = client.get("/v2/qc/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_modules" in data
    assert "total_rules" in data
    assert "unresolved_alerts" in data


def test_get_module_stats(client, mock_qc_service, module_registry_entity):
    """Test récupération des statistiques des modules"""
    module_registry_entity.overall_score = 85.5
    module_registry_entity.architecture_score = 90.0
    mock_qc_service.list_modules.return_value = ([module_registry_entity], 1)

    response = client.get("/v2/qc/stats/modules")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["module_code"] == "TEST_MODULE"
    assert data[0]["overall_score"] == 85.5
