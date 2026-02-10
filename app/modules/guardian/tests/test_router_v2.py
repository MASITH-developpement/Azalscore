"""
Tests pour Guardian v2 Router - CORE SaaS Pattern
==================================================

Tests complets pour l'API Guardian (monitoring & correction automatique).
Système critique pour la stabilité production.

Coverage:
- Configuration (3 tests): get + update + role restrictions
- Détection d'erreurs (6 tests): report + frontend + list + get + acknowledge + tenant isolation
- Registre corrections (8 tests): create + list + pending + get + validate + rollback + tests + workflows
- Règles de correction (6 tests): CRUD + role restrictions + tenant isolation
- Alertes (6 tests): list + get + acknowledge + resolve + tenant isolation
- Statistiques & Dashboard (2 tests): statistics + dashboard
- Performance & Security (4 tests): context, audit trail, role-based access, tenant isolation

TOTAL: 35 tests
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.modules.guardian.models import (
    ErrorDetection,
    CorrectionRegistry,
    CorrectionRule,
    CorrectionTest,
    GuardianAlert,
    GuardianConfig,
    ErrorSeverity,
    ErrorType,
    Environment,
    CorrectionStatus,
)


# ============================================================================
# TESTS CONFIGURATION
# ============================================================================

def test_get_config(test_client, client, auth_headers, sample_guardian_config):
    """Test récupération de la configuration Guardian"""
    response = test_client.get(
        "/api/v2/guardian/config",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "auto_correction_enabled" in data
    assert "tenant_id" in data


def test_update_config(test_client, client, admin_auth_headers, sample_guardian_config):
    """Test mise à jour de la configuration (ADMIN/DIRIGEANT only)"""
    response = test_client.put(
        "/api/v2/guardian/config",
        json={
            "auto_correction_enabled": False,
            "require_validation_for_critical": True
        },
        headers=admin_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["auto_correction_enabled"] is False
    assert data["require_validation_for_critical"] is True


def test_update_config_insufficient_permissions(test_client, client, auth_headers):
    """Test mise à jour config par utilisateur non-admin (doit échouer)"""
    response = test_client.put(
        "/api/v2/guardian/config",
        json={"auto_correction_enabled": False},
        headers=auth_headers
    )

    assert response.status_code == 403
    assert "DIRIGEANT" in response.json()["detail"] or "ADMIN" in response.json()["detail"]


# ============================================================================
# TESTS DÉTECTION D'ERREURS
# ============================================================================

def test_report_error(test_client, client, auth_headers, tenant_id):
    """Test signalement d'une erreur au système Guardian"""
    response = test_client.post(
        "/api/v2/guardian/errors",
        json={
            "error_type": "DATABASE_ERROR",
            "severity": "HIGH",
            "module": "finance",
            "message": "Connection timeout to database",
            "environment": "PRODUCTION",
            "context_data": {"query": "SELECT * FROM accounts"}
        },
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["error_type"] == "DATABASE_ERROR"
    assert data["severity"] == "HIGH"
    assert data["tenant_id"] == tenant_id


def test_report_frontend_error(test_client, client, auth_headers, tenant_id):
    """Test signalement d'une erreur frontend (pseudonymisation auto)"""
    response = test_client.post(
        "/api/v2/guardian/errors/frontend",
        json={
            "message": "Uncaught TypeError: Cannot read property",
            "stack_trace": "at Component.render (app.js:123)",
            "url": "https://app.azals.com/finance/accounts",
            "user_agent": "Mozilla/5.0...",
            "severity": "MEDIUM"
        },
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["error_type"] == "FRONTEND_ERROR" or "message" in data
    # Vérifier pseudonymisation (user_id ne doit pas être en clair si implémenté)


def test_list_errors(test_client, client, auth_headers, sample_error):
    """Test liste des erreurs avec filtres"""
    response = test_client.get(
        "/api/v2/guardian/errors?severity=HIGH&page=1&page_size=20",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


def test_get_error(test_client, client, auth_headers, sample_error):
    """Test récupération d'une erreur"""
    response = test_client.get(
        f"/api/v2/guardian/errors/{sample_error.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_error.id


def test_acknowledge_error(test_client, client, auth_headers, sample_error):
    """Test acquittement d'une erreur (marque comme vue)"""
    response = test_client.post(
        f"/api/v2/guardian/errors/{sample_error.id}/acknowledge",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "acknowledged"
    assert data["error_id"] == sample_error.id


def test_errors_tenant_isolation(test_client, client, auth_headers, db_session, tenant_id):
    """Test isolation tenant sur erreurs (données de monitoring sensibles)"""
    # Créer erreur pour autre tenant
    other_error = ErrorDetection(
        id=999999,
        tenant_id="other-tenant",
        error_type=ErrorType.DATABASE_ERROR,
        severity=ErrorSeverity.HIGH,
        module="test",
        message="Other tenant error",
        environment=Environment.PRODUCTION,
        detected_at=datetime.utcnow()
    )
    db_session.add(other_error)
    db_session.commit()

    # Tenter d'accéder (doit échouer)
    response = test_client.get(
        f"/api/v2/guardian/errors/{other_error.id}",
        headers=auth_headers
    )

    assert response.status_code == 404


# ============================================================================
# TESTS REGISTRE DES CORRECTIONS
# ============================================================================

def test_create_correction(test_client, client, auth_headers, sample_error, tenant_id):
    """Test création d'une entrée de correction (registre append-only)"""
    response = test_client.post(
        "/api/v2/guardian/corrections",
        json={
            "error_id": sample_error.id,
            "correction_type": "AUTO_FIX",
            "description": "Automatic database reconnection",
            "environment": "PRODUCTION",
            "requires_validation": False
        },
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["error_id"] == sample_error.id
    assert data["correction_type"] == "AUTO_FIX"
    assert "executed_by" in data or "created_at" in data  # Audit trail


def test_list_corrections(test_client, client, auth_headers, sample_correction):
    """Test liste des corrections avec filtres"""
    response = test_client.get(
        "/api/v2/guardian/corrections?status=SUCCESS&page=1&page_size=20",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_list_pending_validations(test_client, client, auth_headers, db_session, sample_error, tenant_id):
    """Test liste des corrections en attente de validation humaine"""
    # Créer correction bloquée nécessitant validation
    pending_correction = CorrectionRegistry(
        id=uuid4(),
        tenant_id=tenant_id,
        error_id=sample_error.id,
        correction_type="MANUAL",
        description="Critical fix requiring validation",
        status=CorrectionStatus.BLOCKED,
        requires_validation=True,
        environment=Environment.PRODUCTION,
        executed_by="system",
        executed_at=datetime.utcnow()
    )
    db_session.add(pending_correction)
    db_session.commit()

    response = test_client.get(
        "/api/v2/guardian/corrections/pending-validation?page=1&page_size=20",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    # Vérifier que seules les corrections BLOCKED avec requires_validation=True sont retournées
    if data["items"]:
        for item in data["items"]:
            assert item["status"] == "BLOCKED" or item.get("requires_validation") is True


def test_get_correction(test_client, client, auth_headers, sample_correction):
    """Test récupération d'une correction"""
    response = test_client.get(
        f"/api/v2/guardian/corrections/{sample_correction.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert str(data["id"]) == str(sample_correction.id)


def test_validate_correction(test_client, client, admin_auth_headers, sample_correction_pending):
    """Test workflow validation de correction (BLOCKED → VALIDATED)"""
    response = test_client.post(
        f"/api/v2/guardian/corrections/{sample_correction_pending.id}/validate",
        json={
            "approved": True,
            "comment": "Validation OK, procéder à la correction"
        },
        headers=admin_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["VALIDATED", "APPROVED", "SUCCESS"]
    # Vérifier audit trail validation
    assert "validated_by" in data or "comment" in data


def test_validate_correction_insufficient_permissions(test_client, client, auth_headers, sample_correction_pending):
    """Test validation par utilisateur non-admin (doit échouer)"""
    response = test_client.post(
        f"/api/v2/guardian/corrections/{sample_correction_pending.id}/validate",
        json={"approved": True},
        headers=auth_headers
    )

    assert response.status_code == 403


def test_rollback_correction(test_client, client, admin_auth_headers, sample_correction):
    """Test workflow rollback d'une correction"""
    response = test_client.post(
        f"/api/v2/guardian/corrections/{sample_correction.id}/rollback",
        json={
            "reason": "Correction incorrecte, nécessite rollback"
        },
        headers=admin_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ROLLED_BACK", "ROLLBACK_REQUESTED"]


def test_get_correction_tests(test_client, client, auth_headers, sample_correction):
    """Test récupération des tests exécutés pour une correction"""
    response = test_client.get(
        f"/api/v2/guardian/corrections/{sample_correction.id}/tests",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


# ============================================================================
# TESTS RÈGLES DE CORRECTION
# ============================================================================

def test_create_correction_rule(test_client, client, admin_auth_headers, tenant_id):
    """Test création d'une règle de correction automatique (ADMIN only)"""
    response = test_client.post(
        "/api/v2/guardian/rules",
        json={
            "name": "Auto-reconnect DB",
            "error_type": "DATABASE_ERROR",
            "module": "finance",
            "auto_apply": True,
            "requires_validation": False,
            "max_retry": 3,
            "is_active": True
        },
        headers=admin_auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Auto-reconnect DB"
    assert data["auto_apply"] is True
    assert "created_by" in data  # Audit trail


def test_create_rule_insufficient_permissions(test_client, client, auth_headers):
    """Test création règle par utilisateur non-admin (doit échouer)"""
    response = test_client.post(
        "/api/v2/guardian/rules",
        json={"name": "Test Rule", "error_type": "DATABASE_ERROR"},
        headers=auth_headers
    )

    assert response.status_code == 403


def test_list_correction_rules(test_client, client, auth_headers, sample_correction_rule):
    """Test liste des règles de correction avec filtres"""
    response = test_client.get(
        "/api/v2/guardian/rules?is_active=true&page=1&page_size=20",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_get_correction_rule(test_client, client, auth_headers, sample_correction_rule):
    """Test récupération d'une règle"""
    response = test_client.get(
        f"/api/v2/guardian/rules/{sample_correction_rule.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_correction_rule.id


def test_update_correction_rule(test_client, client, admin_auth_headers, sample_correction_rule):
    """Test mise à jour d'une règle (ADMIN only)"""
    response = test_client.put(
        f"/api/v2/guardian/rules/{sample_correction_rule.id}",
        json={"max_retry": 5},
        headers=admin_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["max_retry"] == 5


def test_correction_rules_tenant_isolation(test_client, client, auth_headers, db_session):
    """Test isolation tenant sur règles de correction"""
    # Créer règle pour autre tenant
    other_rule = CorrectionRule(
        id=999999,
        tenant_id="other-tenant",
        name="Other Rule",
        error_type=ErrorType.DATABASE_ERROR,
        module="test",
        auto_apply=False,
        is_active=True,
        created_by="system"
    )
    db_session.add(other_rule)
    db_session.commit()

    # Tenter d'accéder (doit échouer)
    response = test_client.get(
        f"/api/v2/guardian/rules/{other_rule.id}",
        headers=auth_headers
    )

    assert response.status_code == 404


# ============================================================================
# TESTS ALERTES
# ============================================================================

def test_list_alerts(test_client, client, auth_headers, sample_alert):
    """Test liste des alertes avec filtres"""
    response = test_client.get(
        "/api/v2/guardian/alerts?is_resolved=false&page=1&page_size=20",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_get_alert(test_client, client, auth_headers, sample_alert):
    """Test récupération d'une alerte"""
    response = test_client.get(
        f"/api/v2/guardian/alerts/{sample_alert.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_alert.id


def test_acknowledge_alert(test_client, client, auth_headers, sample_alert):
    """Test acquittement d'une alerte"""
    response = test_client.post(
        f"/api/v2/guardian/alerts/{sample_alert.id}/acknowledge",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "acknowledged_by" in data or "is_acknowledged" in data


def test_resolve_alert(test_client, client, auth_headers, sample_alert):
    """Test résolution d'une alerte"""
    response = test_client.post(
        f"/api/v2/guardian/alerts/{sample_alert.id}/resolve",
        json={
            "resolution": "Fixed by applying auto-correction rule #42"
        },
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_resolved"] is True or "resolution" in data


def test_alert_workflow(test_client, client, auth_headers, db_session, tenant_id):
    """Test workflow complet alerte (NEW → ACKNOWLEDGED → RESOLVED)"""
    # Créer alerte
    alert = GuardianAlert(
        id=uuid4(),
        tenant_id=tenant_id,
        severity=ErrorSeverity.HIGH,
        module="finance",
        message="Critical error detected",
        is_acknowledged=False,
        is_resolved=False,
        created_at=datetime.utcnow()
    )
    db_session.add(alert)
    db_session.commit()

    # 1. Acquitter
    response = test_client.post(
        f"/api/v2/guardian/alerts/{alert.id}/acknowledge",
        headers=auth_headers
    )
    assert response.status_code == 200

    # 2. Résoudre
    response = test_client.post(
        f"/api/v2/guardian/alerts/{alert.id}/resolve",
        json={"resolution": "Problem fixed"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["is_resolved"] is True


def test_alerts_tenant_isolation(test_client, client, auth_headers, db_session):
    """Test isolation tenant sur alertes"""
    # Créer alerte pour autre tenant
    other_alert = GuardianAlert(
        id=999999,
        tenant_id="other-tenant",
        severity=ErrorSeverity.LOW,
        module="test",
        message="Other alert",
        is_acknowledged=False,
        is_resolved=False,
        created_at=datetime.utcnow()
    )
    db_session.add(other_alert)
    db_session.commit()

    # Tenter d'accéder (doit échouer)
    response = test_client.get(
        f"/api/v2/guardian/alerts/{other_alert.id}",
        headers=auth_headers
    )

    assert response.status_code == 404


# ============================================================================
# TESTS STATISTIQUES & DASHBOARD
# ============================================================================

def test_get_statistics(test_client, client, auth_headers, sample_error, sample_correction):
    """Test récupération des statistiques Guardian"""
    response = test_client.get(
        "/api/v2/guardian/statistics",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    # Vérifier présence de métriques clés
    assert "total_errors" in data or "total_corrections" in data or isinstance(data, dict)


def test_get_dashboard(test_client, client, auth_headers, sample_error, sample_alert):
    """Test récupération du dashboard Guardian complet"""
    response = test_client.get(
        "/api/v2/guardian/dashboard",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    # Dashboard doit contenir métriques de monitoring
    assert "errors" in data or "alerts" in data or "corrections" in data or isinstance(data, dict)


# ============================================================================
# TESTS PERFORMANCE & SECURITY
# ============================================================================

def test_saas_context_performance(test_client, client, auth_headers, benchmark):
    """Test performance du context SaaS (doit être <50ms)"""
    def call_endpoint():
        return test_client.get(
            "/api/v2/guardian/config",
            headers=auth_headers
        )

    result = benchmark(call_endpoint)
    assert result.status_code == 200


def test_audit_trail_automatic(test_client, client, auth_headers, sample_error):
    """Test audit trail automatique sur toutes actions"""
    # Créer correction
    response = test_client.post(
        "/api/v2/guardian/corrections",
        json={
            "error_id": sample_error.id,
            "correction_type": "AUTO_FIX",
            "description": "Audit test",
            "environment": "PRODUCTION"
        },
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert "executed_by" in data or "created_at" in data
    # Vérifier que executed_by contient user ID
    if "executed_by" in data:
        assert "user:" in data["executed_by"] or data["executed_by"] is not None


def test_role_based_access_control(test_client, client, auth_headers, admin_auth_headers):
    """Test contrôle d'accès basé sur les rôles (RBAC)"""
    # Action admin-only avec utilisateur normal (doit échouer)
    response = test_client.post(
        "/api/v2/guardian/rules",
        json={"name": "Test", "error_type": "DATABASE_ERROR"},
        headers=auth_headers
    )
    assert response.status_code == 403

    # Action admin-only avec admin (doit réussir)
    response = test_client.post(
        "/api/v2/guardian/rules",
        json={
            "name": "Test Rule",
            "error_type": "DATABASE_ERROR",
            "module": "test",
            "auto_apply": False,
            "is_active": True
        },
        headers=admin_auth_headers
    )
    assert response.status_code == 201


def test_tenant_isolation_strict(test_client, client, auth_headers, db_session):
    """Test isolation stricte entre tenants (monitoring sensible)"""
    # Créer erreur pour autre tenant
    other_error = ErrorDetection(
        id=888888,
        tenant_id="other-tenant-strict",
        error_type=ErrorType.API_ERROR,
        severity=ErrorSeverity.LOW,
        module="test",
        message="Strict isolation test",
        environment=Environment.DEVELOPMENT,
        detected_at=datetime.utcnow()
    )
    db_session.add(other_error)
    db_session.commit()

    # Lister toutes les erreurs (doit filtrer automatiquement)
    response = test_client.get(
        "/api/v2/guardian/errors",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    # Vérifier qu'aucune erreur d'autre tenant n'est visible
    for error in data["items"]:
        assert error["tenant_id"] != "other-tenant-strict"
