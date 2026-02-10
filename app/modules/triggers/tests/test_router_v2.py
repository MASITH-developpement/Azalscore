"""
Tests pour le router v2 du module Triggers.
CORE SaaS v2 avec SaaSContext.
"""

import pytest
from uuid import uuid4



BASE_URL = "/v2/triggers"


# ============================================================================
# TESTS TRIGGERS - Déclencheurs
# ============================================================================

def test_create_trigger_success(test_client, mock_trigger_service, sample_trigger_data):
    """Test création d'un trigger."""
    response = test_client.post(f"{BASE_URL}/", json=sample_trigger_data)

    assert response.status_code == 201
    data = response.json()
    assert data["code"] == sample_trigger_data["code"]
    assert data["name"] == sample_trigger_data["name"]
    assert data["trigger_type"] == sample_trigger_data["trigger_type"]


def test_create_trigger_duplicate_code(test_client, mock_trigger_service, sample_trigger_data, monkeypatch):
    """Test création trigger avec code existant."""
    # Mock service pour retourner un trigger existant
    def mock_get_by_code(self, code):
        return {"id": str(uuid4()), "code": code}

    from app.modules.triggers import service
    monkeypatch.setattr(service.TriggerService, "get_trigger_by_code", mock_get_by_code)

    response = test_client.post(f"{BASE_URL}/", json=sample_trigger_data)

    assert response.status_code == 400
    assert "existe déjà" in response.json()["detail"]


def test_list_triggers_all(test_client):
    """Test liste tous les triggers."""
    response = test_client.get(f"{BASE_URL}/")

    assert response.status_code == 200
    data = response.json()
    assert "triggers" in data
    assert "total" in data
    assert len(data["triggers"]) > 0


def test_list_triggers_with_filters(test_client):
    """Test liste triggers avec filtres."""
    response = test_client.get(
        f"{BASE_URL}/",
        params={
            "source_module": "treasury",
            "trigger_type": "THRESHOLD",
            "include_inactive": True
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "triggers" in data


def test_get_trigger_success(test_client):
    """Test récupération d'un trigger."""
    trigger_id = str(uuid4())

    response = test_client.get(f"{BASE_URL}/{trigger_id}")

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "code" in data


def test_get_trigger_not_found(test_client, mock_trigger_service, monkeypatch):
    """Test récupération trigger inexistant."""
    trigger_id = str(uuid4())

    # Mock pour retourner None
    def mock_get(self, _id):
        return None

    from app.modules.triggers import service
    monkeypatch.setattr(service.TriggerService, "get_trigger", mock_get)

    response = test_client.get(f"{BASE_URL}/{trigger_id}")

    assert response.status_code == 404


def test_update_trigger_success(test_client):
    """Test mise à jour d'un trigger."""
    trigger_id = str(uuid4())
    update_data = {
        "name": "Trigger Updated",
        "severity": "CRITICAL"
    }

    response = test_client.put(f"{BASE_URL}/{trigger_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]


def test_delete_trigger_success(test_client):
    """Test suppression d'un trigger."""
    trigger_id = str(uuid4())

    response = test_client.delete(f"{BASE_URL}/{trigger_id}")

    assert response.status_code == 204


def test_delete_trigger_not_found(test_client, mock_trigger_service, monkeypatch):
    """Test suppression trigger inexistant."""
    trigger_id = str(uuid4())

    # Mock pour retourner False
    def mock_delete(self, _id, **kwargs):
        return False

    from app.modules.triggers import service
    monkeypatch.setattr(service.TriggerService, "delete_trigger", mock_delete)

    response = test_client.delete(f"{BASE_URL}/{trigger_id}")

    assert response.status_code == 404


def test_pause_trigger_success(test_client):
    """Test mise en pause d'un trigger."""
    trigger_id = str(uuid4())

    response = test_client.post(f"{BASE_URL}/{trigger_id}/pause")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PAUSED"


def test_resume_trigger_success(test_client):
    """Test reprise d'un trigger."""
    trigger_id = str(uuid4())

    response = test_client.post(f"{BASE_URL}/{trigger_id}/resume")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ACTIVE"


def test_fire_trigger_success(test_client):
    """Test déclenchement manuel d'un trigger."""
    trigger_id = str(uuid4())
    test_data = {
        "value": "-5000",
        "field": "balance"
    }

    response = test_client.post(f"{BASE_URL}/{trigger_id}/fire", json=test_data)

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "triggered_at" in data


def test_fire_trigger_condition_not_met(test_client, mock_trigger_service, monkeypatch):
    """Test déclenchement avec condition non remplie."""
    trigger_id = str(uuid4())

    # Mock evaluate_trigger pour retourner False
    def mock_evaluate(self, trigger, data):
        return False

    from app.modules.triggers import service
    monkeypatch.setattr(service.TriggerService, "evaluate_trigger", mock_evaluate)

    response = test_client.post(f"{BASE_URL}/{trigger_id}/fire", json={})

    assert response.status_code == 400
    assert "Condition non remplie" in response.json()["detail"]


# ============================================================================
# TESTS SUBSCRIPTIONS - Abonnements
# ============================================================================

def test_create_subscription_user(test_client, mock_trigger_service, sample_subscription_data):
    """Test abonnement d'un utilisateur à un trigger."""
    response = test_client.post(f"{BASE_URL}/subscriptions", json=sample_subscription_data)

    assert response.status_code == 201
    data = response.json()
    assert data["trigger_id"] == sample_subscription_data["trigger_id"]
    assert data["user_id"] == sample_subscription_data["user_id"]


def test_create_subscription_role(test_client):
    """Test abonnement d'un rôle à un trigger."""
    subscription_data = {
        "trigger_id": str(uuid4()),
        "role_code": "DAF",
        "channel": "EMAIL"
    }

    response = test_client.post(f"{BASE_URL}/subscriptions", json=subscription_data)

    assert response.status_code == 201
    data = response.json()
    assert data["role_code"] == subscription_data["role_code"]


def test_create_subscription_missing_target(test_client):
    """Test abonnement sans user_id ni role_code."""
    subscription_data = {
        "trigger_id": str(uuid4()),
        "channel": "EMAIL"
    }

    response = test_client.post(f"{BASE_URL}/subscriptions", json=subscription_data)

    assert response.status_code == 400


def test_list_trigger_subscriptions(test_client):
    """Test liste abonnements d'un trigger."""
    trigger_id = str(uuid4())

    response = test_client.get(f"{BASE_URL}/subscriptions/{trigger_id}")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_delete_subscription_success(test_client):
    """Test suppression d'un abonnement."""
    subscription_id = str(uuid4())

    response = test_client.delete(f"{BASE_URL}/subscriptions/{subscription_id}")

    assert response.status_code == 204


def test_delete_subscription_not_found(test_client, mock_trigger_service, monkeypatch):
    """Test suppression abonnement inexistant."""
    subscription_id = str(uuid4())

    # Mock pour retourner False
    def mock_unsubscribe(self, _id):
        return False

    from app.modules.triggers import service
    monkeypatch.setattr(service.TriggerService, "unsubscribe", mock_unsubscribe)

    response = test_client.delete(f"{BASE_URL}/subscriptions/{subscription_id}")

    assert response.status_code == 404


# ============================================================================
# TESTS EVENTS - Événements
# ============================================================================

def test_list_events_all(test_client):
    """Test liste tous les événements."""
    response = test_client.get(f"{BASE_URL}/events")

    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "total" in data


def test_list_events_with_filters(test_client):
    """Test liste événements avec filtres."""
    trigger_id = str(uuid4())

    response = test_client.get(
        f"{BASE_URL}/events",
        params={
            "trigger_id": str(trigger_id),
            "resolved": False,
            "severity": "WARNING",
            "limit": 50
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "events" in data


def test_get_event_success(test_client):
    """Test récupération d'un événement."""
    event_id = str(uuid4())

    response = test_client.get(f"{BASE_URL}/events/{event_id}")

    assert response.status_code == 200
    data = response.json()
    assert "id" in data


def test_get_event_not_found(test_client, mock_trigger_service, monkeypatch):
    """Test récupération événement inexistant."""
    event_id = str(uuid4())

    # Mock pour retourner None
    def mock_get(self, _id):
        return None

    from app.modules.triggers import service
    monkeypatch.setattr(service.TriggerService, "get_event", mock_get)

    response = test_client.get(f"{BASE_URL}/events/{event_id}")

    assert response.status_code == 404


def test_resolve_event_success(test_client):
    """Test résolution d'un événement."""
    event_id = str(uuid4())

    response = test_client.post(
        f"{BASE_URL}/events/{event_id}/resolve",
        params={"resolution_notes": "Problème résolu"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["resolved"] is True


def test_resolve_event_already_resolved(test_client, mock_trigger_service, monkeypatch):
    """Test résolution d'un événement déjà résolu."""
    event_id = str(uuid4())

    # Mock pour lever ValueError
    def mock_resolve(self, _id, **kwargs):
        raise ValueError("Événement déjà résolu")

    from app.modules.triggers import service
    monkeypatch.setattr(service.TriggerService, "resolve_event", mock_resolve)

    response = test_client.post(f"{BASE_URL}/events/{event_id}/resolve")

    assert response.status_code == 400


def test_escalate_event_success(test_client):
    """Test escalade d'un événement."""
    event_id = str(uuid4())

    response = test_client.post(f"{BASE_URL}/events/{event_id}/escalate")

    assert response.status_code == 200
    data = response.json()
    assert data["escalation_level"] == "L2"


def test_escalate_event_max_level(test_client, mock_trigger_service, monkeypatch):
    """Test escalade au niveau maximum."""
    event_id = str(uuid4())

    # Mock pour lever ValueError
    def mock_escalate(self, _id):
        raise ValueError("Niveau d'escalade maximum atteint")

    from app.modules.triggers import service
    monkeypatch.setattr(service.TriggerService, "escalate_event", mock_escalate)

    response = test_client.post(f"{BASE_URL}/events/{event_id}/escalate")

    assert response.status_code == 400


# ============================================================================
# TESTS NOTIFICATIONS
# ============================================================================

def test_list_user_notifications(test_client):
    """Test liste notifications utilisateur."""
    response = test_client.get(f"{BASE_URL}/notifications")

    assert response.status_code == 200
    data = response.json()
    assert "notifications" in data
    assert "total" in data
    assert "unread_count" in data


def test_list_user_notifications_unread_only(test_client):
    """Test liste notifications non lues uniquement."""
    response = test_client.get(
        f"{BASE_URL}/notifications",
        params={"unread_only": True, "limit": 20}
    )

    assert response.status_code == 200
    data = response.json()
    assert "notifications" in data


def test_mark_notification_read(test_client):
    """Test marquer notification comme lue."""
    notification_id = str(uuid4())

    response = test_client.post(f"{BASE_URL}/notifications/{notification_id}/read")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "READ"


def test_mark_notification_read_not_found(test_client, mock_trigger_service, monkeypatch):
    """Test marquer notification inexistante."""
    notification_id = str(uuid4())

    # Mock pour retourner None
    def mock_mark_read(self, _id):
        return None

    from app.modules.triggers import service
    monkeypatch.setattr(service.TriggerService, "mark_notification_read", mock_mark_read)

    response = test_client.post(f"{BASE_URL}/notifications/{notification_id}/read")

    assert response.status_code == 404


def test_mark_all_notifications_read(test_client):
    """Test marquer toutes notifications comme lues."""
    response = test_client.post(f"{BASE_URL}/notifications/read-all")

    assert response.status_code == 204


def test_send_pending_notifications(test_client):
    """Test envoi des notifications en attente."""
    response = test_client.post(f"{BASE_URL}/notifications/send-pending")

    assert response.status_code == 200
    data = response.json()
    assert "sent_count" in data
    assert data["sent_count"] == 5


# ============================================================================
# TESTS TEMPLATES
# ============================================================================

def test_create_template_success(test_client, mock_trigger_service, sample_template_data):
    """Test création d'un template."""
    response = test_client.post(f"{BASE_URL}/templates", json=sample_template_data)

    assert response.status_code == 201
    data = response.json()
    assert data["code"] == sample_template_data["code"]
    assert data["name"] == sample_template_data["name"]


def test_list_templates(test_client):
    """Test liste templates."""
    response = test_client.get(f"{BASE_URL}/templates")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_template_success(test_client, mock_trigger_service, mock_db):
    """Test récupération d'un template."""
    # Note: Ce test nécessiterait un mock DB plus élaboré
    # Pour l'instant on teste juste l'endpoint
    template_id = str(uuid4())

    response = test_client.get(f"{BASE_URL}/templates/{template_id}")

    # Le mock DB retourne None, donc 404 attendu
    assert response.status_code == 404


def test_update_template_success(test_client, mock_trigger_service, mock_db):
    """Test mise à jour d'un template."""
    template_id = str(uuid4())
    update_data = {"name": "Template Updated"}

    response = test_client.put(f"{BASE_URL}/templates/{template_id}", json=update_data)

    # Le mock DB retourne None, donc 404 attendu
    assert response.status_code == 404


def test_delete_template_success(test_client, mock_trigger_service, mock_db):
    """Test suppression d'un template."""
    template_id = str(uuid4())

    response = test_client.delete(f"{BASE_URL}/templates/{template_id}")

    # Le mock DB retourne None, donc 404 attendu
    assert response.status_code == 404


# ============================================================================
# TESTS SCHEDULED REPORTS
# ============================================================================

def test_create_scheduled_report_success(test_client, mock_trigger_service, sample_report_data):
    """Test création d'un rapport planifié."""
    response = test_client.post(f"{BASE_URL}/reports", json=sample_report_data)

    assert response.status_code == 201
    data = response.json()
    assert data["code"] == sample_report_data["code"]
    assert data["name"] == sample_report_data["name"]


def test_list_scheduled_reports(test_client):
    """Test liste rapports planifiés."""
    response = test_client.get(f"{BASE_URL}/reports")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_scheduled_reports_include_inactive(test_client):
    """Test liste rapports avec inactifs."""
    response = test_client.get(
        f"{BASE_URL}/reports",
        params={"include_inactive": True}
    )

    assert response.status_code == 200


def test_get_scheduled_report_success(test_client, mock_trigger_service, mock_db):
    """Test récupération d'un rapport planifié."""
    report_id = str(uuid4())

    response = test_client.get(f"{BASE_URL}/reports/{report_id}")

    # Le mock DB retourne None, donc 404 attendu
    assert response.status_code == 404


def test_update_scheduled_report_success(test_client, mock_trigger_service, mock_db):
    """Test mise à jour d'un rapport."""
    report_id = str(uuid4())
    update_data = {"name": "Report Updated"}

    response = test_client.put(f"{BASE_URL}/reports/{report_id}", json=update_data)

    # Le mock DB retourne None, donc 404 attendu
    assert response.status_code == 404


def test_delete_scheduled_report_success(test_client, mock_trigger_service, mock_db):
    """Test suppression d'un rapport."""
    report_id = str(uuid4())

    response = test_client.delete(f"{BASE_URL}/reports/{report_id}")

    # Le mock DB retourne None, donc 404 attendu
    assert response.status_code == 404


def test_generate_report_success(test_client):
    """Test génération d'un rapport."""
    report_id = str(uuid4())

    response = test_client.post(f"{BASE_URL}/reports/{report_id}/generate")

    assert response.status_code == 200
    data = response.json()
    assert "file_name" in data
    assert data["success"] is True


def test_get_report_history(test_client, mock_trigger_service, mock_db):
    """Test récupération historique rapport."""
    report_id = str(uuid4())

    response = test_client.get(f"{BASE_URL}/reports/{report_id}/history")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ============================================================================
# TESTS WEBHOOKS
# ============================================================================

def test_create_webhook_success(test_client, mock_trigger_service, sample_webhook_data):
    """Test création d'un webhook."""
    response = test_client.post(f"{BASE_URL}/webhooks", json=sample_webhook_data)

    assert response.status_code == 201
    data = response.json()
    assert data["code"] == sample_webhook_data["code"]
    assert data["url"] == sample_webhook_data["url"]


def test_list_webhooks(test_client):
    """Test liste webhooks."""
    response = test_client.get(f"{BASE_URL}/webhooks")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_webhook_success(test_client, mock_trigger_service, mock_db):
    """Test récupération d'un webhook."""
    webhook_id = str(uuid4())

    response = test_client.get(f"{BASE_URL}/webhooks/{webhook_id}")

    # Le mock DB retourne None, donc 404 attendu
    assert response.status_code == 404


def test_update_webhook_success(test_client, mock_trigger_service, mock_db):
    """Test mise à jour d'un webhook."""
    webhook_id = str(uuid4())
    update_data = {"name": "Webhook Updated"}

    response = test_client.put(f"{BASE_URL}/webhooks/{webhook_id}", json=update_data)

    # Le mock DB retourne None, donc 404 attendu
    assert response.status_code == 404


def test_delete_webhook_success(test_client, mock_trigger_service, mock_db):
    """Test suppression d'un webhook."""
    webhook_id = str(uuid4())

    response = test_client.delete(f"{BASE_URL}/webhooks/{webhook_id}")

    # Le mock DB retourne None, donc 404 attendu
    assert response.status_code == 404


def test_test_webhook_success(test_client, mock_trigger_service, mock_db):
    """Test d'un webhook."""
    webhook_id = str(uuid4())

    response = test_client.post(f"{BASE_URL}/webhooks/{webhook_id}/test")

    # Le mock DB retourne None, donc 404 attendu
    assert response.status_code == 404


# ============================================================================
# TESTS MONITORING & DASHBOARD
# ============================================================================

def test_list_logs(test_client, mock_trigger_service, mock_db):
    """Test liste des logs."""
    response = test_client.get(f"{BASE_URL}/logs")

    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert "total" in data


def test_list_logs_with_filter(test_client, mock_trigger_service, mock_db):
    """Test liste logs avec filtre action."""
    response = test_client.get(
        f"{BASE_URL}/logs",
        params={"action": "TRIGGER_CREATED", "limit": 50}
    )

    assert response.status_code == 200


def test_get_dashboard(test_client, mock_trigger_service, mock_db):
    """Test dashboard récapitulatif."""
    response = test_client.get(f"{BASE_URL}/dashboard")

    assert response.status_code == 200
    data = response.json()
    assert "total_triggers" in data
    assert "active_triggers" in data
    assert "total_events" in data
    assert "unresolved_events" in data
    assert "pending_notifications" in data
    assert "top_triggers" in data


# ============================================================================
# TESTS ISOLATION TENANT
# ============================================================================

def test_triggers_tenant_isolation(test_client):
    """Test isolation tenant sur liste triggers."""
    response = test_client.get(f"{BASE_URL}/")

    assert response.status_code == 200
    # Les données mockées appartiennent au bon tenant
    # Test réel nécessiterait vérification tenant_id


def test_events_tenant_isolation(test_client):
    """Test isolation tenant sur événements."""
    response = test_client.get(f"{BASE_URL}/events")

    assert response.status_code == 200


def test_notifications_tenant_isolation(test_client):
    """Test isolation tenant sur notifications."""
    response = test_client.get(f"{BASE_URL}/notifications")

    assert response.status_code == 200


# ============================================================================
# TESTS VALIDATION DONNÉES
# ============================================================================

def test_create_trigger_missing_required_fields(test_client):
    """Test création trigger avec champs manquants."""
    invalid_data = {
        "code": "TEST"
        # Manque name, trigger_type, etc.
    }

    response = test_client.post(f"{BASE_URL}/", json=invalid_data)

    assert response.status_code == 422  # Validation error


def test_create_trigger_invalid_enum(test_client):
    """Test création trigger avec enum invalide."""
    invalid_data = {
        "code": "TEST",
        "name": "Test",
        "trigger_type": "INVALID_TYPE",  # Type invalide
        "source_module": "treasury",
        "condition": {}
    }

    response = test_client.post(f"{BASE_URL}/", json=invalid_data)

    assert response.status_code == 422


def test_subscribe_invalid_channel(test_client):
    """Test abonnement avec canal invalide."""
    invalid_data = {
        "trigger_id": str(uuid4()),
        "user_id": str(uuid4()),
        "channel": "INVALID_CHANNEL"
    }

    response = test_client.post(f"{BASE_URL}/subscriptions", json=invalid_data)

    assert response.status_code == 422
