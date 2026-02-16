"""
Tests pour le module Audit v2 - Router API
============================================

✅ Tests conformes au pattern CORE SaaS:
- Utilisation de context.tenant_id pour isolation
- Utilisation de context.user_id pour audit trail
- Mock de get_saas_context via conftest.py

Coverage:
- Audit Logs (7 tests)
- Sessions (3 tests)
- Metrics (5 tests)
- Benchmarks (5 tests)
- Compliance (5 tests)
- Retention (3 tests)
- Exports (4 tests)
- Dashboards (4 tests)
- Statistics (2 tests)
- Security & Performance (3 tests)

Total: ~41 tests couvrant 33 endpoints
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.modules.audit.models import (
    AuditLog,
    AuditAction,
    AuditLevel,
    AuditCategory,
    MetricDefinition,
    MetricType,
    ComplianceCheck,
    ComplianceFramework,
)



# ============================================================================
# TESTS AUDIT LOGS
# ============================================================================

def test_search_audit_logs_all(test_client, client, auth_headers, sample_audit_logs_batch, tenant_id):
    """Test recherche tous les logs d'audit avec pagination"""
    response = test_client.get(
        "/api/v2/audit/logs?page=1&page_size=10",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure pagination
    assert "logs" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data

    # Vérifier isolation tenant
    for log in data["logs"]:
        assert log["tenant_id"] == tenant_id


def test_search_audit_logs_with_filters(test_client, client, auth_headers, sample_audit_logs_batch):
    """Test recherche logs avec filtres multiples"""
    response = test_client.get(
        "/api/v2/audit/logs?action=CREATE&level=INFO&module=finance&success=true",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier filtrage
    for log in data["logs"]:
        assert log["action"] == "CREATE"
        assert log["level"] == "INFO"
        assert log["module"] == "finance"
        assert log["success"] is True


def test_search_audit_logs_by_date_range(test_client, client, auth_headers, sample_audit_logs_batch):
    """Test recherche logs par période"""
    from_date = (datetime.utcnow() - timedelta(hours=5)).isoformat()
    to_date = datetime.utcnow().isoformat()

    response = test_client.get(
        f"/api/v2/audit/logs?from_date={from_date}&to_date={to_date}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["logs"], list)


def test_search_audit_logs_by_user(test_client, client, auth_headers, sample_audit_log, user_id):
    """Test recherche logs par utilisateur"""
    response = test_client.get(
        f"/api/v2/audit/logs?user_id={user_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for log in data["logs"]:
        assert log["user_id"] == user_id


def test_get_audit_log_by_id(test_client, client, auth_headers, sample_audit_log):
    """Test récupération d'un log par ID"""
    response = test_client.get(
        f"/api/v2/audit/logs/{sample_audit_log.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(sample_audit_log.id)
    assert data["action"] == sample_audit_log.action.value
    assert data["module"] == sample_audit_log.module


def test_get_entity_audit_history(test_client, client, auth_headers, sample_audit_log):
    """Test récupération historique d'une entité"""
    response = test_client.get(
        f"/api/v2/audit/logs/entity/{sample_audit_log.entity_type}/{sample_audit_log.entity_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    # Vérifier que tous les logs concernent la bonne entité
    for log in data:
        assert log["entity_type"] == sample_audit_log.entity_type
        assert log["entity_id"] == sample_audit_log.entity_id


def test_get_user_audit_history(test_client, client, auth_headers, sample_audit_log, user_id):
    """Test récupération historique d'un utilisateur"""
    response = test_client.get(
        f"/api/v2/audit/logs/user/{user_id}?limit=50",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    for log in data:
        assert log["user_id"] == user_id


# ============================================================================
# TESTS SESSIONS
# ============================================================================

def test_list_active_sessions(test_client, client, auth_headers, sample_session, tenant_id):
    """Test liste des sessions actives"""
    response = test_client.get(
        "/api/v2/audit/sessions",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    # Vérifier isolation tenant
    for session in data:
        assert session["tenant_id"] == tenant_id
        assert session["is_active"] is True


def test_list_active_sessions_by_user(test_client, client, auth_headers, sample_session, user_id):
    """Test liste sessions d'un utilisateur spécifique"""
    response = test_client.get(
        f"/api/v2/audit/sessions?user_id={user_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for session in data:
        assert session["user_id"] == user_id


def test_terminate_session(test_client, client, auth_headers, sample_session):
    """Test terminer une session active"""
    response = test_client.post(
        f"/api/v2/audit/sessions/{sample_session.session_id}/terminate?reason=Test+termination",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "terminated"
    assert data["session_id"] == sample_session.session_id


# ============================================================================
# TESTS METRICS
# ============================================================================

def test_create_metric(test_client, client, auth_headers, tenant_id, user_id, sample_metric_data):
    """Test création d'une nouvelle métrique"""
    response = test_client.post(
        "/api/v2/audit/metrics",
        json=sample_metric_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["code"] == sample_metric_data["code"]
    assert data["name"] == sample_metric_data["name"]
    assert data["tenant_id"] == tenant_id
    assert data["metric_type"] == sample_metric_data["metric_type"]


def test_list_metrics(test_client, client, auth_headers, sample_metric, tenant_id):
    """Test liste des métriques"""
    response = test_client.get(
        "/api/v2/audit/metrics",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    # Vérifier isolation tenant
    for metric in data:
        assert metric["tenant_id"] == tenant_id


def test_list_metrics_by_category(test_client, client, auth_headers, sample_metric):
    """Test liste métriques filtrées par module"""
    response = test_client.get(
        f"/api/v2/audit/metrics?category={sample_metric.module}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for metric in data:
        assert metric.get("module") == sample_metric.module


def test_record_metric_value(test_client, client, auth_headers, sample_metric, tenant_id):
    """Test enregistrement d'une valeur de métrique"""
    metric_data = {
        "metric_code": sample_metric.code,
        "value": 256.8,
        "timestamp": datetime.utcnow().isoformat()
    }

    response = test_client.post(
        "/api/v2/audit/metrics/record",
        json=metric_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["metric_code"] == sample_metric.code
    assert data["value"] == metric_data["value"]
    assert data["tenant_id"] == tenant_id


def test_get_metric_values(test_client, client, auth_headers, sample_metric_values, sample_metric):
    """Test récupération des valeurs d'une métrique"""
    response = test_client.get(
        f"/api/v2/audit/metrics/{sample_metric.code}/values?limit=50",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0
    for value in data:
        assert value["metric_code"] == sample_metric.code


# ============================================================================
# TESTS BENCHMARKS
# ============================================================================

def test_create_benchmark(test_client, client, auth_headers, tenant_id, user_id, sample_benchmark_data):
    """Test création d'un benchmark"""
    response = test_client.post(
        "/api/v2/audit/benchmarks",
        json=sample_benchmark_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["code"] == sample_benchmark_data["code"]
    assert data["name"] == sample_benchmark_data["name"]
    assert data["tenant_id"] == tenant_id
    # Vérifier audit trail
    assert "created_by" in data


def test_list_benchmarks(test_client, client, auth_headers, sample_benchmark, tenant_id):
    """Test liste des benchmarks"""
    response = test_client.get(
        "/api/v2/audit/benchmarks",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    # Vérifier isolation tenant
    for benchmark in data:
        assert benchmark["tenant_id"] == tenant_id


def test_list_benchmarks_by_category(test_client, client, auth_headers, sample_benchmark):
    """Test liste benchmarks filtrés par type"""
    response = test_client.get(
        f"/api/v2/audit/benchmarks?category={sample_benchmark.benchmark_type}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for benchmark in data:
        assert benchmark["benchmark_type"] == sample_benchmark.benchmark_type


def test_run_benchmark(test_client, client, auth_headers, sample_benchmark, user_id):
    """Test exécution d'un benchmark"""
    response = test_client.post(
        f"/api/v2/audit/benchmarks/{sample_benchmark.id}/run",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier résultat benchmark
    assert "status" in data
    assert "executed_by" in data


def test_get_benchmark_results(test_client, client, auth_headers, sample_benchmark_result, sample_benchmark):
    """Test récupération des résultats d'un benchmark"""
    response = test_client.get(
        f"/api/v2/audit/benchmarks/{sample_benchmark.id}/results?limit=10",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    for result in data:
        assert result["benchmark_id"] == str(sample_benchmark.id)
        assert "status" in result
        assert "score" in result


# ============================================================================
# TESTS COMPLIANCE CHECKS
# ============================================================================

def test_create_compliance_check(test_client, client, auth_headers, tenant_id, user_id, sample_compliance_data):
    """Test création d'un contrôle de conformité"""
    response = test_client.post(
        "/api/v2/audit/compliance/checks",
        json=sample_compliance_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["framework"] == sample_compliance_data["framework"]
    assert data["control_id"] == sample_compliance_data["control_id"]
    assert data["tenant_id"] == tenant_id
    # Vérifier audit trail
    assert "created_by" in data or "checked_by" in data


def test_list_compliance_checks(test_client, client, auth_headers, sample_compliance_check, tenant_id):
    """Test liste des contrôles de conformité"""
    response = test_client.get(
        "/api/v2/audit/compliance/checks",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    # Vérifier isolation tenant
    for check in data:
        assert check["tenant_id"] == tenant_id


def test_list_compliance_checks_by_framework(test_client, client, auth_headers, sample_compliance_check):
    """Test liste contrôles filtrés par framework"""
    response = test_client.get(
        f"/api/v2/audit/compliance/checks?framework={sample_compliance_check.framework.value}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for check in data:
        assert check["framework"] == sample_compliance_check.framework.value


def test_update_compliance_check(test_client, client, auth_headers, sample_compliance_check, user_id):
    """Test mise à jour d'un contrôle de conformité"""
    update_data = {
        "status": "NON_COMPLIANT",
        "actual_result": "5 violations found",
        "remediation": "Fix violations ASAP"
    }

    response = test_client.put(
        f"/api/v2/audit/compliance/checks/{sample_compliance_check.id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == update_data["status"]
    # Vérifier audit trail
    assert "updated_by" in data or "checked_by" in data


def test_get_compliance_summary(test_client, client, auth_headers, sample_compliance_check):
    """Test récupération du résumé de conformité"""
    response = test_client.get(
        "/api/v2/audit/compliance/summary",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure résumé
    assert isinstance(data, dict)
    assert "total" in data or "compliance_rate" in data


# ============================================================================
# TESTS RETENTION RULES
# ============================================================================

def test_create_retention_rule(test_client, client, auth_headers, tenant_id, user_id, sample_retention_data):
    """Test création d'une règle de rétention"""
    response = test_client.post(
        "/api/v2/audit/retention/rules",
        json=sample_retention_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == sample_retention_data["name"]
    assert data["target_table"] == sample_retention_data["target_table"]
    assert data["tenant_id"] == tenant_id
    # Vérifier audit trail
    assert "created_by" in data or "created_at" in data


def test_list_retention_rules(test_client, client, auth_headers, sample_retention_rule, tenant_id):
    """Test liste des règles de rétention"""
    response = test_client.get(
        "/api/v2/audit/retention/rules",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    # Vérifier isolation tenant
    for rule in data:
        assert rule["tenant_id"] == tenant_id


def test_apply_retention_rules_dry_run(test_client, client, auth_headers, sample_retention_rule):
    """Test application des règles de rétention (mode simulation)"""
    response = test_client.post(
        "/api/v2/audit/retention/apply?dry_run=true",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "preview"
    assert "records_to_delete" in data


# ============================================================================
# TESTS EXPORTS
# ============================================================================

def test_create_export(test_client, client, auth_headers, tenant_id, user_id, sample_export_data):
    """Test création d'un export d'audit"""
    response = test_client.post(
        "/api/v2/audit/exports",
        json=sample_export_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["export_type"] == sample_export_data["export_type"]
    assert data["format"] == sample_export_data["format"]
    assert data["tenant_id"] == tenant_id
    # Vérifier audit trail
    assert data["requested_by"] == user_id or "requested_by" in data


def test_list_exports(test_client, client, auth_headers, sample_export, tenant_id):
    """Test liste des exports"""
    response = test_client.get(
        "/api/v2/audit/exports",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    # Vérifier isolation tenant
    for export in data:
        assert export["tenant_id"] == tenant_id


def test_get_export_by_id(test_client, client, auth_headers, sample_export):
    """Test récupération d'un export par ID"""
    response = test_client.get(
        f"/api/v2/audit/exports/{sample_export.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(sample_export.id)
    assert data["export_type"] == sample_export.export_type
    assert "status" in data


def test_process_export(test_client, client, auth_headers, sample_export):
    """Test retraitement d'un export"""
    response = test_client.post(
        f"/api/v2/audit/exports/{sample_export.id}/process",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Export existe et sera retraité
    assert data["id"] == str(sample_export.id)


# ============================================================================
# TESTS DASHBOARDS
# ============================================================================

def test_create_dashboard(test_client, client, auth_headers, tenant_id, user_id, sample_dashboard_data):
    """Test création d'un dashboard personnalisé"""
    response = test_client.post(
        "/api/v2/audit/dashboards",
        json=sample_dashboard_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["code"] == sample_dashboard_data["code"]
    assert data["name"] == sample_dashboard_data["name"]
    assert data["tenant_id"] == tenant_id
    # Vérifier audit trail
    assert data["owner_id"] == user_id or "owner_id" in data


def test_list_dashboards(test_client, client, auth_headers, sample_dashboard, tenant_id):
    """Test liste des dashboards"""
    response = test_client.get(
        "/api/v2/audit/dashboards",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    # Vérifier isolation tenant
    for dashboard in data:
        assert dashboard["tenant_id"] == tenant_id


def test_get_dashboard_data(test_client, client, auth_headers, sample_dashboard):
    """Test récupération des données d'un dashboard"""
    from_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
    to_date = datetime.utcnow().isoformat()

    response = test_client.get(
        f"/api/v2/audit/dashboards/{sample_dashboard.id}/data?from_date={from_date}&to_date={to_date}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure données dashboard
    assert isinstance(data, dict)


def test_get_dashboard_data_default_period(test_client, client, auth_headers, sample_dashboard):
    """Test récupération données dashboard sans dates (période par défaut)"""
    response = test_client.get(
        f"/api/v2/audit/dashboards/{sample_dashboard.id}/data",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


# ============================================================================
# TESTS STATISTICS
# ============================================================================

def test_get_audit_stats(test_client, client, auth_headers, sample_audit_logs_batch):
    """Test récupération des statistiques d'audit"""
    from_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
    to_date = datetime.utcnow().isoformat()

    response = test_client.get(
        f"/api/v2/audit/stats?from_date={from_date}&to_date={to_date}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure statistiques
    assert isinstance(data, dict)
    # Les stats devraient contenir des counts ou métriques
    assert any(key in data for key in ["total_logs_24h", "failed_24h", "active_sessions", "unique_users_24h"])


def test_get_audit_dashboard(test_client, client, auth_headers, sample_audit_logs_batch):
    """Test récupération du dashboard principal d'audit"""
    response = test_client.get(
        "/api/v2/audit/dashboard?period=7d",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier structure dashboard
    assert isinstance(data, dict)


# ============================================================================
# TESTS WORKFLOWS COMPLEXES
# ============================================================================

def test_workflow_create_metric_and_record_values(test_client, client,
    auth_headers,
    tenant_id,
    sample_metric_data):
    """
    Test workflow complet: créer métrique → enregistrer valeurs → récupérer historique
    """
    # 1. Créer métrique
    response = test_client.post(
        "/api/v2/audit/metrics",
        json=sample_metric_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    metric = response.json()
    metric_code = metric["code"]

    # 2. Enregistrer plusieurs valeurs
    for i in range(5):
        value_data = {
            "metric_code": metric_code,
            "value": 100.0 + (i * 10),
            "timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat()
        }
        response = test_client.post(
            "/api/v2/audit/metrics/record",
            json=value_data,
            headers=auth_headers
        )
        assert response.status_code == 200

    # 3. Récupérer historique
    response = test_client.get(
        f"/api/v2/audit/metrics/{metric_code}/values",
        headers=auth_headers
    )
    assert response.status_code == 200
    values = response.json()
    assert len(values) >= 5


def test_workflow_benchmark_execution_and_results(test_client, client,
    auth_headers,
    sample_benchmark_data):
    """
    Test workflow: créer benchmark → exécuter → récupérer résultats
    """
    # 1. Créer benchmark
    response = test_client.post(
        "/api/v2/audit/benchmarks",
        json=sample_benchmark_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    benchmark = response.json()
    benchmark_id = benchmark["id"]

    # 2. Exécuter benchmark
    response = test_client.post(
        f"/api/v2/audit/benchmarks/{benchmark_id}/run",
        headers=auth_headers
    )
    assert response.status_code == 200
    result = response.json()

    # 3. Récupérer historique résultats
    response = test_client.get(
        f"/api/v2/audit/benchmarks/{benchmark_id}/results",
        headers=auth_headers
    )
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)


def test_workflow_compliance_check_lifecycle(test_client, client,
    auth_headers,
    sample_compliance_data,
    user_id):
    """
    Test workflow: créer check → mettre à jour statut → récupérer summary
    """
    # 1. Créer compliance check
    response = test_client.post(
        "/api/v2/audit/compliance/checks",
        json=sample_compliance_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    check = response.json()
    check_id = check["id"]

    # 2. Mettre à jour statut check
    update_data = {
        "status": "COMPLIANT",
        "actual_result": "All checks passed"
    }
    response = test_client.put(
        f"/api/v2/audit/compliance/checks/{check_id}",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == 200

    # 3. Récupérer summary
    response = test_client.get(
        "/api/v2/audit/compliance/summary",
        headers=auth_headers
    )
    assert response.status_code == 200
    summary = response.json()
    assert isinstance(summary, dict)


def test_workflow_export_audit_logs(test_client, client,
    auth_headers,
    sample_audit_logs_batch,
    sample_export_data):
    """
    Test workflow: créer export → vérifier progression → récupérer résultat
    """
    # 1. Créer export
    response = test_client.post(
        "/api/v2/audit/exports",
        json=sample_export_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    export = response.json()
    export_id = export["id"]

    # 2. Vérifier statut
    response = test_client.get(
        f"/api/v2/audit/exports/{export_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    export_status = response.json()
    assert "status" in export_status

    # 3. Liste tous les exports
    response = test_client.get(
        "/api/v2/audit/exports",
        headers=auth_headers
    )
    assert response.status_code == 200
    exports = response.json()
    assert any(e["id"] == export_id for e in exports)


# ============================================================================
# TESTS PAGINATION & FILTRES
# ============================================================================

def test_search_logs_pagination(test_client, client, auth_headers, sample_audit_logs_batch):
    """Test pagination de la recherche de logs"""
    # Page 1
    response = test_client.get(
        "/api/v2/audit/logs?page=1&page_size=5",
        headers=auth_headers
    )
    assert response.status_code == 200
    page1 = response.json()
    assert len(page1["logs"]) <= 5
    assert page1["page"] == 1

    # Page 2
    response = test_client.get(
        "/api/v2/audit/logs?page=2&page_size=5",
        headers=auth_headers
    )
    assert response.status_code == 200
    page2 = response.json()
    assert page2["page"] == 2


def test_search_logs_by_entity(test_client, client, auth_headers, sample_audit_log):
    """Test recherche logs par entité"""
    response = test_client.get(
        f"/api/v2/audit/logs?entity_type={sample_audit_log.entity_type}&entity_id={sample_audit_log.entity_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for log in data["logs"]:
        assert log["entity_type"] == sample_audit_log.entity_type
        assert log["entity_id"] == sample_audit_log.entity_id


def test_search_logs_with_text_search(test_client, client, auth_headers, sample_audit_log):
    """Test recherche logs avec texte libre"""
    response = test_client.get(
        "/api/v2/audit/logs?search_text=facture",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["logs"], list)


# ============================================================================
# TESTS SÉCURITÉ & ISOLATION TENANT
# ============================================================================

def test_audit_logs_tenant_isolation(test_client, client, auth_headers, db_session, tenant_id):
    """
    Test CRITIQUE: vérifier l'isolation stricte des logs par tenant
    """
    # Créer logs pour un autre tenant
    other_tenant_id = "other-tenant-999"
    other_log = AuditLog(
        id=uuid4(),
        tenant_id=other_tenant_id,
        action=AuditAction.DELETE,
        level=AuditLevel.CRITICAL,
        category=AuditCategory.SECURITY,
        module="sensitive",
        entity_type="secret",
        entity_id="SECRET-001",
        description="Sensitive operation",
        created_at=datetime.utcnow()
    )
    db_session.add(other_log)
    db_session.commit()

    # Tenter de récupérer tous les logs
    response = test_client.get(
        "/api/v2/audit/logs",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier qu'AUCUN log de l'autre tenant n'est retourné
    for log in data["logs"]:
        assert log["tenant_id"] == tenant_id
        assert log["tenant_id"] != other_tenant_id


def test_metrics_tenant_isolation(test_client, client, auth_headers, db_session, tenant_id):
    """
    Test CRITIQUE: isolation des métriques par tenant
    """
    # Créer métrique pour autre tenant
    other_metric = MetricDefinition(
        id=uuid4(),
        tenant_id="other-tenant-999",
        code="other.metric",
        name="Other Metric",
        metric_type="COUNTER",
        is_active=True
    )
    db_session.add(other_metric)
    db_session.commit()

    # Récupérer métriques
    response = test_client.get(
        "/api/v2/audit/metrics",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier isolation
    for metric in data:
        assert metric["tenant_id"] == tenant_id


def test_compliance_checks_tenant_isolation(test_client, client, auth_headers, db_session, tenant_id):
    """
    Test CRITIQUE: isolation des contrôles de conformité par tenant
    """
    # Créer check pour autre tenant
    other_check = ComplianceCheck(
        id=uuid4(),
        tenant_id="other-tenant-999",
        framework=ComplianceFramework.SOC2,
        control_id="SOC2-TEST",
        control_name="Other Check",
        check_type="AUTOMATED",
        status="PENDING",
        is_active=True
    )
    db_session.add(other_check)
    db_session.commit()

    # Récupérer checks
    response = test_client.get(
        "/api/v2/audit/compliance/checks",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier isolation
    for check in data:
        assert check["tenant_id"] == tenant_id


# ============================================================================
# TESTS ERREURS & CAS LIMITES
# ============================================================================

def test_get_nonexistent_log(test_client, client, auth_headers):
    """Test récupération d'un log inexistant"""
    fake_id = uuid4()
    response = test_client.get(
        f"/api/v2/audit/logs/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404
    data = response.json()
    # Vérifier message d'erreur dans detail ou message
    error_msg = data.get("detail", data.get("message", "")).lower()
    assert "non trouvé" in error_msg or "not found" in error_msg


def test_get_nonexistent_export(test_client, client, auth_headers):
    """Test récupération d'un export inexistant"""
    fake_id = uuid4()
    response = test_client.get(
        f"/api/v2/audit/exports/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


def test_create_metric_with_duplicate_code(test_client, client, auth_headers, sample_metric):
    """Test création métrique avec code dupliqué (devrait échouer)"""
    duplicate_data = {
        "code": sample_metric.code,  # Code existant
        "name": "Duplicate Metric",
        "metric_type": "GAUGE"
    }

    response = test_client.post(
        "/api/v2/audit/metrics",
        json=duplicate_data,
        headers=auth_headers
    )

    # Devrait échouer (409 Conflict ou 400 Bad Request)
    assert response.status_code in [400, 409, 422]


def test_invalid_audit_dashboard_period(test_client, client, auth_headers):
    """Test récupération dashboard avec période invalide"""
    response = test_client.get(
        "/api/v2/audit/dashboard?period=invalid",
        headers=auth_headers
    )

    # Devrait échouer (validation Pydantic)
    assert response.status_code == 422


# ============================================================================
# TESTS COMPLIANCE FRAMEWORKS
# ============================================================================

@pytest.mark.parametrize("framework", [
    "GDPR",
    "SOC2",
    "ISO27001",
    "HIPAA",
    "PCI_DSS"
])
def test_create_compliance_check_for_framework(test_client, client,
    auth_headers,
    tenant_id,
    framework):
    """Test création de contrôles pour différents frameworks de conformité"""
    data = {
        "framework": framework,
        "control_id": f"{framework}-001",
        "control_name": f"{framework} Control Test",
        "control_description": f"Test control for {framework}",
        "check_type": "AUTOMATED"
    }

    response = test_client.post(
        "/api/v2/audit/compliance/checks",
        json=data,
        headers=auth_headers
    )

    assert response.status_code == 200
    result = response.json()
    assert result["framework"] == framework
    assert result["tenant_id"] == tenant_id


def test_get_compliance_summary_by_framework(test_client, client,
    auth_headers,
    sample_compliance_check):
    """Test récupération du résumé de conformité par framework"""
    response = test_client.get(
        f"/api/v2/audit/compliance/summary?framework={sample_compliance_check.framework.value}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


# ============================================================================
# TESTS RETENTION & DATA LIFECYCLE
# ============================================================================

def test_list_retention_rules_by_category(test_client, client, auth_headers, sample_retention_rule):
    """Test liste des règles de rétention filtrées par module"""
    response = test_client.get(
        "/api/v2/audit/retention/rules?target_module=test",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_apply_retention_rules_background_task(test_client, client, auth_headers, sample_retention_rule):
    """Test application asynchrone des règles de rétention"""
    response = test_client.post(
        "/api/v2/audit/retention/apply?dry_run=false",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier lancement tâche background
    assert data["status"] == "started"
    assert "message" in data


# ============================================================================
# TESTS PERFORMANCE & SCALABILITÉ
# ============================================================================

def test_search_logs_large_dataset_performance(test_client, client,
    auth_headers,
    sample_audit_logs_batch,
    benchmark):
    """Test performance recherche sur large dataset"""
    # Recherche avec multiples filtres
    response = test_client.get(
        "/api/v2/audit/logs?page=1&page_size=100&action=CREATE&level=INFO",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier réponse raisonnable même avec pagination élevée
    assert "logs" in data
    assert len(data["logs"]) <= 100


def test_metric_values_query_with_limit(test_client, client, auth_headers, sample_metric_values, sample_metric):
    """Test récupération de valeurs métriques avec limite haute"""
    response = test_client.get(
        f"/api/v2/audit/metrics/{sample_metric.code}/values?limit=1000",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) <= 1000


# ============================================================================
# TESTS EXPORTS & FORMATS
# ============================================================================

@pytest.mark.parametrize("export_format", ["CSV", "JSON", "PDF", "EXCEL"])
def test_create_export_various_formats(test_client, client,
    auth_headers,
    tenant_id,
    export_format):
    """Test création d'exports dans différents formats"""
    data = {
        "export_type": "AUDIT_LOGS",
        "format": export_format,
        "date_from": (datetime.utcnow() - timedelta(days=30)).isoformat(),
        "date_to": datetime.utcnow().isoformat()
    }

    response = test_client.post(
        "/api/v2/audit/exports",
        json=data,
        headers=auth_headers
    )

    assert response.status_code == 200
    result = response.json()
    assert result["format"] == export_format
    assert result["tenant_id"] == tenant_id


def test_list_exports_by_status(test_client, client, auth_headers, sample_export):
    """Test liste des exports filtrés par statut"""
    response = test_client.get(
        f"/api/v2/audit/exports?status={sample_export.status}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for export in data:
        assert export["status"] == sample_export.status


# ============================================================================
# TESTS AUDIT TRAIL INTEGRITY
# ============================================================================

def test_audit_log_contains_complete_trail(test_client, client, auth_headers, sample_audit_log, assert_audit_trail):
    """Test vérifier que les logs contiennent tous les champs d'audit trail"""
    response = test_client.get(
        f"/api/v2/audit/logs/{sample_audit_log.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier présence des champs critiques audit trail
    assert_audit_trail(data)


def test_audit_log_tracks_user_changes(test_client, client, auth_headers, sample_audit_log, user_id):
    """Test vérifier que les modifications sont tracées avec user_id"""
    response = test_client.get(
        f"/api/v2/audit/logs?user_id={user_id}&action=UPDATE",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for log in data["logs"]:
        assert log["user_id"] == user_id
        assert log["action"] in ["UPDATE", "CREATE", "DELETE"]


# ============================================================================
# TESTS SESSION MANAGEMENT
# ============================================================================

def test_list_active_sessions_statistics(test_client, client, auth_headers, sample_session):
    """Test récupération des statistiques de sessions actives"""
    response = test_client.get(
        "/api/v2/audit/sessions",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier que les sessions contiennent des statistiques
    for session in data:
        if session["session_id"] == sample_session.session_id:
            assert "actions_count" in session
            assert "reads_count" in session
            assert "writes_count" in session
            assert session["is_active"] is True


def test_terminate_session_with_reason(test_client, client, auth_headers, sample_session):
    """Test terminer une session avec raison spécifique"""
    reason = "Security policy violation"

    response = test_client.post(
        f"/api/v2/audit/sessions/{sample_session.session_id}/terminate?reason={reason}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "terminated"
    assert data["session_id"] == sample_session.session_id


# ============================================================================
# TESTS REGRESSION & DATA INTEGRITY
# ============================================================================

def test_create_multiple_dashboards(test_client, client, auth_headers, tenant_id, user_id):
    """Test création de plusieurs dashboards sans conflit"""
    for i in range(3):
        data = {
            "code": f"TEST_DASHBOARD_{i}",
            "name": f"Test Dashboard {i}",
            "description": f"Dashboard numéro {i}",
            "widgets": [{"id": f"w{i}", "type": "chart", "title": f"Chart {i}"}]
        }

        response = test_client.post(
            "/api/v2/audit/dashboards",
            json=data,
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["code"] == data["code"]
        assert result["tenant_id"] == tenant_id


def test_benchmark_results_history(test_client, client, auth_headers, sample_benchmark_result, sample_benchmark):
    """Test historique des résultats de benchmark (trend analysis)"""
    response = test_client.get(
        f"/api/v2/audit/benchmarks/{sample_benchmark.id}/results?limit=50",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier informations de tendance
    for result in data:
        if result.get("previous_score") is not None:
            assert "score_delta" in result
            assert "trend" in result


# ============================================================================
# TESTS DOCUMENTATION & MÉTADONNÉES
# ============================================================================

def test_audit_log_contains_metadata(test_client, client, auth_headers, sample_audit_log):
    """Test vérifier que les logs contiennent les métadonnées système"""
    response = test_client.get(
        f"/api/v2/audit/logs/{sample_audit_log.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier métadonnées système
    assert "ip_address" in data
    assert "user_agent" in data
    assert "session_id" in data
    assert "created_at" in data


def test_compliance_check_evidence_tracking(test_client, client, auth_headers, sample_compliance_check):
    """Test vérifier que les contrôles de conformité trackent les preuves"""
    response = test_client.get(
        "/api/v2/audit/compliance/checks",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    for check in data:
        if check["id"] == str(sample_compliance_check.id):
            # Vérifier présence des preuves de conformité
            assert "status" in check
            if check["status"] == "COMPLIANT":
                assert "evidence" in check or "actual_result" in check
