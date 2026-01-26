"""
Tests pour le router v2 du module broadcast (CORE SaaS).
"""

import pytest
from fastapi import status


# ============================================================================
# TESTS TEMPLATES (10 tests)
# ============================================================================

def test_create_template_success(test_client, client, template_data, mock_broadcast_service):
    """Test création d'un template avec succès."""
    mock_broadcast_service.get_template_by_code.return_value = None
    mock_broadcast_service.create_template.return_value = template_data

    response = test_client.post(
        "/v2/broadcast/templates",
        json={
            "code": "TMPL001",
            "name": "Template Test",
            "content_type": "EMAIL",
            "subject_template": "Sujet: {{title}}",
            "body_template": "Corps: {{message}}"
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["code"] == "TMPL001"
    mock_broadcast_service.create_template.assert_called_once()


def test_create_template_duplicate_code(test_client, client, template_data, mock_broadcast_service):
    """Test création d'un template avec code existant."""
    mock_broadcast_service.get_template_by_code.return_value = template_data

    response = test_client.post(
        "/v2/broadcast/templates",
        json={
            "code": "TMPL001",
            "name": "Template Test",
            "content_type": "EMAIL"
        }
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "existe déjà" in response.json()["detail"]


def test_list_templates(test_client, client, template_data, mock_broadcast_service):
    """Test liste des templates."""
    mock_broadcast_service.list_templates.return_value = ([template_data], 1)

    response = test_client.get("/v2/broadcast/templates")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["code"] == "TMPL001"


def test_list_templates_with_filters(test_client, client, mock_broadcast_service):
    """Test liste des templates avec filtres."""
    mock_broadcast_service.list_templates.return_value = ([], 0)

    response = test_client.get(
        "/v2/broadcast/templates",
        params={"content_type": "EMAIL", "is_active": True, "skip": 0, "limit": 10}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 0
    mock_broadcast_service.list_templates.assert_called_once()


def test_get_template(test_client, client, template_data, mock_broadcast_service):
    """Test récupération d'un template."""
    mock_broadcast_service.get_template.return_value = template_data

    response = test_client.get("/v2/broadcast/templates/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == 1
    assert response.json()["code"] == "TMPL001"


def test_get_template_not_found(test_client, client, mock_broadcast_service):
    """Test récupération d'un template inexistant."""
    mock_broadcast_service.get_template.return_value = None

    response = test_client.get("/v2/broadcast/templates/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_template(test_client, client, template_data, mock_broadcast_service):
    """Test mise à jour d'un template."""
    updated_data = template_data.copy()
    updated_data["name"] = "Template Modifié"
    mock_broadcast_service.update_template.return_value = updated_data

    response = test_client.put(
        "/v2/broadcast/templates/1",
        json={"name": "Template Modifié"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Template Modifié"


def test_update_template_not_found(test_client, client, mock_broadcast_service):
    """Test mise à jour d'un template inexistant."""
    mock_broadcast_service.update_template.return_value = None

    response = test_client.put(
        "/v2/broadcast/templates/999",
        json={"name": "Template Modifié"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_template(test_client, client, mock_broadcast_service):
    """Test suppression d'un template."""
    mock_broadcast_service.delete_template.return_value = True

    response = test_client.delete("/v2/broadcast/templates/1")

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_template_not_found(test_client, client, mock_broadcast_service):
    """Test suppression d'un template inexistant."""
    mock_broadcast_service.delete_template.return_value = False

    response = test_client.delete("/v2/broadcast/templates/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# TESTS RECIPIENT LISTS (12 tests)
# ============================================================================

def test_create_recipient_list(test_client, client, recipient_list_data, mock_broadcast_service):
    """Test création d'une liste de destinataires."""
    mock_broadcast_service.create_recipient_list.return_value = recipient_list_data

    response = test_client.post(
        "/v2/broadcast/recipient-lists",
        json={
            "code": "LIST001",
            "name": "Liste Test",
            "description": "Liste de test"
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["code"] == "LIST001"


def test_list_recipient_lists(test_client, client, recipient_list_data, mock_broadcast_service):
    """Test liste des listes de destinataires."""
    mock_broadcast_service.list_recipient_lists.return_value = ([recipient_list_data], 1)

    response = test_client.get("/v2/broadcast/recipient-lists")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_list_recipient_lists_with_pagination(test_client, client, mock_broadcast_service):
    """Test liste avec pagination."""
    mock_broadcast_service.list_recipient_lists.return_value = ([], 0)

    response = test_client.get(
        "/v2/broadcast/recipient-lists",
        params={"skip": 10, "limit": 20}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["skip"] == 10
    assert data["limit"] == 20


def test_get_recipient_list(test_client, client, recipient_list_data, mock_broadcast_service):
    """Test récupération d'une liste."""
    mock_broadcast_service.get_recipient_list.return_value = recipient_list_data

    response = test_client.get("/v2/broadcast/recipient-lists/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == 1


def test_get_recipient_list_not_found(test_client, client, mock_broadcast_service):
    """Test récupération d'une liste inexistante."""
    mock_broadcast_service.get_recipient_list.return_value = None

    response = test_client.get("/v2/broadcast/recipient-lists/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_add_member_to_list(test_client, client, recipient_member_data, recipient_list_data, mock_broadcast_service):
    """Test ajout d'un membre à une liste."""
    mock_broadcast_service.get_recipient_list.return_value = recipient_list_data
    mock_broadcast_service.add_member_to_list.return_value = recipient_member_data

    response = test_client.post(
        "/v2/broadcast/recipient-lists/1/members",
        json={
            "recipient_type": "USER",
            "user_id": 123
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["user_id"] == 123


def test_add_member_list_not_found(test_client, client, mock_broadcast_service):
    """Test ajout d'un membre à une liste inexistante."""
    mock_broadcast_service.get_recipient_list.return_value = None

    response = test_client.post(
        "/v2/broadcast/recipient-lists/999/members",
        json={
            "recipient_type": "USER",
            "user_id": 123
        }
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_members(test_client, client, recipient_member_data, mock_broadcast_service):
    """Test liste des membres d'une liste."""
    mock_broadcast_service.get_list_members.return_value = ([recipient_member_data], 1)

    response = test_client.get("/v2/broadcast/recipient-lists/1/members")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_list_members_with_filters(test_client, client, mock_broadcast_service):
    """Test liste des membres avec filtres."""
    mock_broadcast_service.get_list_members.return_value = ([], 0)

    response = test_client.get(
        "/v2/broadcast/recipient-lists/1/members",
        params={"is_active": True, "skip": 0, "limit": 50}
    )

    assert response.status_code == status.HTTP_200_OK


def test_delete_member(test_client, client, mock_broadcast_service):
    """Test suppression d'un membre."""
    mock_broadcast_service.remove_member_from_list.return_value = True

    response = test_client.delete("/v2/broadcast/recipient-lists/1/members/1")

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_member_not_found(test_client, client, mock_broadcast_service):
    """Test suppression d'un membre inexistant."""
    mock_broadcast_service.remove_member_from_list.return_value = False

    response = test_client.delete("/v2/broadcast/recipient-lists/1/members/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_add_member_external_email(test_client, client, recipient_list_data, mock_broadcast_service):
    """Test ajout d'un membre avec email externe."""
    member_data = {
        "recipient_type": "EXTERNAL",
        "external_email": "external@test.com",
        "external_name": "External User"
    }
    mock_broadcast_service.get_recipient_list.return_value = recipient_list_data
    mock_broadcast_service.add_member_to_list.return_value = member_data

    response = test_client.post(
        "/v2/broadcast/recipient-lists/1/members",
        json=member_data
    )

    assert response.status_code == status.HTTP_201_CREATED


# ============================================================================
# TESTS SCHEDULED BROADCASTS (16 tests)
# ============================================================================

def test_create_scheduled_broadcast(test_client, client, broadcast_data, mock_broadcast_service):
    """Test création d'une diffusion programmée."""
    mock_broadcast_service.create_scheduled_broadcast.return_value = broadcast_data

    response = test_client.post(
        "/v2/broadcast/scheduled",
        json={
            "code": "BROAD001",
            "name": "Diffusion Test",
            "content_type": "EMAIL",
            "frequency": "DAILY",
            "delivery_channel": "EMAIL",
            "subject": "Sujet test"
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["code"] == "BROAD001"


def test_list_scheduled_broadcasts(test_client, client, broadcast_data, mock_broadcast_service):
    """Test liste des diffusions programmées."""
    mock_broadcast_service.list_scheduled_broadcasts.return_value = ([broadcast_data], 1)

    response = test_client.get("/v2/broadcast/scheduled")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_list_scheduled_broadcasts_with_status_filter(test_client, client, mock_broadcast_service):
    """Test liste avec filtre de statut."""
    mock_broadcast_service.list_scheduled_broadcasts.return_value = ([], 0)

    response = test_client.get(
        "/v2/broadcast/scheduled",
        params={"status": "ACTIVE"}
    )

    assert response.status_code == status.HTTP_200_OK


def test_list_scheduled_broadcasts_with_frequency_filter(test_client, client, mock_broadcast_service):
    """Test liste avec filtre de fréquence."""
    mock_broadcast_service.list_scheduled_broadcasts.return_value = ([], 0)

    response = test_client.get(
        "/v2/broadcast/scheduled",
        params={"frequency": "DAILY"}
    )

    assert response.status_code == status.HTTP_200_OK


def test_get_scheduled_broadcast(test_client, client, broadcast_data, mock_broadcast_service):
    """Test récupération d'une diffusion."""
    mock_broadcast_service.get_scheduled_broadcast.return_value = broadcast_data

    response = test_client.get("/v2/broadcast/scheduled/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == 1


def test_get_scheduled_broadcast_not_found(test_client, client, mock_broadcast_service):
    """Test récupération d'une diffusion inexistante."""
    mock_broadcast_service.get_scheduled_broadcast.return_value = None

    response = test_client.get("/v2/broadcast/scheduled/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_scheduled_broadcast(test_client, client, broadcast_data, mock_broadcast_service):
    """Test mise à jour d'une diffusion."""
    updated_data = broadcast_data.copy()
    updated_data["name"] = "Diffusion Modifiée"
    mock_broadcast_service.update_scheduled_broadcast.return_value = updated_data

    response = test_client.put(
        "/v2/broadcast/scheduled/1",
        json={"name": "Diffusion Modifiée"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Diffusion Modifiée"


def test_update_scheduled_broadcast_not_found(test_client, client, mock_broadcast_service):
    """Test mise à jour d'une diffusion inexistante."""
    mock_broadcast_service.update_scheduled_broadcast.return_value = None

    response = test_client.put(
        "/v2/broadcast/scheduled/999",
        json={"name": "Diffusion Modifiée"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_activate_broadcast(test_client, client, broadcast_data, mock_broadcast_service):
    """Test activation d'une diffusion."""
    activated_data = broadcast_data.copy()
    activated_data["status"] = "ACTIVE"
    mock_broadcast_service.activate_broadcast.return_value = activated_data

    response = test_client.post("/v2/broadcast/scheduled/1/activate")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "ACTIVE"


def test_activate_broadcast_not_found(test_client, client, mock_broadcast_service):
    """Test activation d'une diffusion inexistante."""
    mock_broadcast_service.activate_broadcast.return_value = None

    response = test_client.post("/v2/broadcast/scheduled/999/activate")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_pause_broadcast(test_client, client, broadcast_data, mock_broadcast_service):
    """Test mise en pause d'une diffusion."""
    paused_data = broadcast_data.copy()
    paused_data["status"] = "PAUSED"
    mock_broadcast_service.pause_broadcast.return_value = paused_data

    response = test_client.post("/v2/broadcast/scheduled/1/pause")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "PAUSED"


def test_pause_broadcast_not_found(test_client, client, mock_broadcast_service):
    """Test mise en pause d'une diffusion inexistante."""
    mock_broadcast_service.pause_broadcast.return_value = None

    response = test_client.post("/v2/broadcast/scheduled/999/pause")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_cancel_broadcast(test_client, client, broadcast_data, mock_broadcast_service):
    """Test annulation d'une diffusion."""
    cancelled_data = broadcast_data.copy()
    cancelled_data["status"] = "CANCELLED"
    mock_broadcast_service.cancel_broadcast.return_value = cancelled_data

    response = test_client.post("/v2/broadcast/scheduled/1/cancel")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "CANCELLED"


def test_cancel_broadcast_not_found(test_client, client, mock_broadcast_service):
    """Test annulation d'une diffusion inexistante."""
    mock_broadcast_service.cancel_broadcast.return_value = None

    response = test_client.post("/v2/broadcast/scheduled/999/cancel")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_execute_broadcast_now(test_client, client, execution_data, mock_broadcast_service):
    """Test exécution manuelle d'une diffusion."""
    mock_broadcast_service.execute_broadcast.return_value = execution_data

    response = test_client.post(
        "/v2/broadcast/scheduled/1/execute",
        json={"triggered_by": "manual"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == 1


def test_execute_broadcast_not_found(test_client, client, mock_broadcast_service):
    """Test exécution d'une diffusion inexistante."""
    mock_broadcast_service.execute_broadcast.side_effect = ValueError("Broadcast not found")

    response = test_client.post(
        "/v2/broadcast/scheduled/999/execute",
        json={"triggered_by": "manual"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# TESTS EXECUTIONS (6 tests)
# ============================================================================

def test_list_executions(test_client, client, execution_data, mock_broadcast_service):
    """Test liste des exécutions."""
    mock_broadcast_service.list_executions.return_value = ([execution_data], 1)

    response = test_client.get("/v2/broadcast/executions")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_list_executions_with_filters(test_client, client, mock_broadcast_service):
    """Test liste des exécutions avec filtres."""
    mock_broadcast_service.list_executions.return_value = ([], 0)

    response = test_client.get(
        "/v2/broadcast/executions",
        params={"broadcast_id": 1, "status": "DELIVERED"}
    )

    assert response.status_code == status.HTTP_200_OK


def test_get_execution(test_client, client, execution_data, mock_broadcast_service):
    """Test récupération d'une exécution."""
    mock_broadcast_service.get_execution.return_value = execution_data

    response = test_client.get("/v2/broadcast/executions/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == 1


def test_get_execution_not_found(test_client, client, mock_broadcast_service):
    """Test récupération d'une exécution inexistante."""
    mock_broadcast_service.get_execution.return_value = None

    response = test_client.get("/v2/broadcast/executions/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_execution_details(test_client, client, delivery_detail_data, mock_broadcast_service):
    """Test récupération des détails d'exécution."""
    mock_broadcast_service.get_delivery_details.return_value = ([delivery_detail_data], 1)

    response = test_client.get("/v2/broadcast/executions/1/details")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_get_execution_details_with_filters(test_client, client, mock_broadcast_service):
    """Test détails d'exécution avec filtres."""
    mock_broadcast_service.get_delivery_details.return_value = ([], 0)

    response = test_client.get(
        "/v2/broadcast/executions/1/details",
        params={"status": "DELIVERED", "channel": "EMAIL"}
    )

    assert response.status_code == status.HTTP_200_OK


# ============================================================================
# TESTS PREFERENCES (4 tests)
# ============================================================================

def test_get_preferences(test_client, client, preference_data, mock_broadcast_service):
    """Test récupération des préférences."""
    mock_broadcast_service.get_user_preferences.return_value = preference_data

    response = test_client.get("/v2/broadcast/preferences")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["user_id"] == 123


def test_get_preferences_create_default(test_client, client, preference_data, mock_broadcast_service):
    """Test création des préférences par défaut."""
    mock_broadcast_service.get_user_preferences.return_value = None
    mock_broadcast_service.set_user_preferences.return_value = preference_data

    response = test_client.get("/v2/broadcast/preferences")

    assert response.status_code == status.HTTP_200_OK
    mock_broadcast_service.set_user_preferences.assert_called_once()


def test_update_preferences(test_client, client, preference_data, mock_broadcast_service):
    """Test mise à jour des préférences."""
    updated_data = preference_data.copy()
    updated_data["receive_digest"] = False
    mock_broadcast_service.set_user_preferences.return_value = updated_data

    response = test_client.put(
        "/v2/broadcast/preferences",
        json={"receive_digest": False}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["receive_digest"] == False


def test_update_preferences_with_channel(test_client, client, preference_data, mock_broadcast_service):
    """Test mise à jour avec canal préféré."""
    updated_data = preference_data.copy()
    updated_data["preferred_channel"] = "SMS"
    mock_broadcast_service.set_user_preferences.return_value = updated_data

    response = test_client.put(
        "/v2/broadcast/preferences",
        json={"preferred_channel": "SMS"}
    )

    assert response.status_code == status.HTTP_200_OK


# ============================================================================
# TESTS UNSUBSCRIBE (2 tests)
# ============================================================================

def test_unsubscribe_from_broadcast(test_client, client, mock_broadcast_service):
    """Test désabonnement d'une diffusion spécifique."""
    mock_broadcast_service.unsubscribe_user.return_value = True

    response = test_client.post(
        "/v2/broadcast/unsubscribe",
        json={"broadcast_id": 1}
    )

    assert response.status_code == status.HTTP_200_OK
    assert "Désabonnement effectué" in response.json()["message"]


def test_unsubscribe_from_all(test_client, client, mock_broadcast_service):
    """Test désabonnement de toutes les diffusions."""
    mock_broadcast_service.unsubscribe_user.return_value = True

    response = test_client.post(
        "/v2/broadcast/unsubscribe",
        json={}
    )

    assert response.status_code == status.HTTP_200_OK


# ============================================================================
# TESTS METRICS (4 tests)
# ============================================================================

def test_list_metrics(test_client, client, metric_data, mock_broadcast_service):
    """Test liste des métriques."""
    mock_broadcast_service.get_metrics.return_value = [metric_data]

    response = test_client.get("/v2/broadcast/metrics")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_list_metrics_with_period(test_client, client, mock_broadcast_service):
    """Test liste des métriques avec période."""
    mock_broadcast_service.get_metrics.return_value = []

    response = test_client.get(
        "/v2/broadcast/metrics",
        params={"period_type": "WEEKLY", "limit": 10}
    )

    assert response.status_code == status.HTTP_200_OK


def test_record_metric(test_client, client, metric_data, mock_broadcast_service):
    """Test enregistrement de métriques."""
    mock_broadcast_service.record_metrics.return_value = metric_data

    response = test_client.post("/v2/broadcast/metrics/record")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["period_type"] == "DAILY"


def test_record_metric_monthly(test_client, client, metric_data, mock_broadcast_service):
    """Test enregistrement de métriques mensuelles."""
    monthly_data = metric_data.copy()
    monthly_data["period_type"] = "MONTHLY"
    mock_broadcast_service.record_metrics.return_value = monthly_data

    response = test_client.post(
        "/v2/broadcast/metrics/record",
        params={"period_type": "MONTHLY"}
    )

    assert response.status_code == status.HTTP_200_OK


# ============================================================================
# TESTS DASHBOARD & PROCESSING (6 tests)
# ============================================================================

def test_get_dashboard_stats(test_client, client, dashboard_stats, mock_broadcast_service):
    """Test récupération des stats du dashboard."""
    mock_broadcast_service.get_dashboard_stats.return_value = dashboard_stats

    response = test_client.get("/v2/broadcast/dashboard")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_broadcasts"] == 10
    assert data["active_broadcasts"] == 5
    assert len(data["upcoming_broadcasts"]) == 2


def test_get_dashboard_stats_empty(test_client, client, mock_broadcast_service):
    """Test dashboard sans données."""
    mock_broadcast_service.get_dashboard_stats.return_value = {
        "total_broadcasts": 0,
        "active_broadcasts": 0,
        "executions_this_week": 0,
        "messages_sent_this_week": 0,
        "delivery_rate": 0,
        "open_rate": 0,
        "upcoming_broadcasts": []
    }

    response = test_client.get("/v2/broadcast/dashboard")

    assert response.status_code == status.HTTP_200_OK


def test_get_due_broadcasts(test_client, client, broadcast_data, mock_broadcast_service):
    """Test récupération des diffusions à traiter."""
    mock_broadcast_service.get_broadcasts_due.return_value = [broadcast_data]

    response = test_client.get("/v2/broadcast/due")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_get_due_broadcasts_empty(test_client, client, mock_broadcast_service):
    """Test aucune diffusion à traiter."""
    mock_broadcast_service.get_broadcasts_due.return_value = []

    response = test_client.get("/v2/broadcast/due")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0


def test_process_due_broadcasts(test_client, client, broadcast_data, execution_data, mock_broadcast_service):
    """Test traitement des diffusions en attente."""
    mock_broadcast_service.get_broadcasts_due.return_value = [broadcast_data]
    mock_broadcast_service.execute_broadcast.return_value = execution_data

    response = test_client.post("/v2/broadcast/process-due")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_process_due_broadcasts_with_error(test_client, client, broadcast_data, mock_broadcast_service):
    """Test traitement avec erreur sur une diffusion."""
    mock_broadcast_service.get_broadcasts_due.return_value = [broadcast_data]
    mock_broadcast_service.execute_broadcast.side_effect = Exception("Erreur d'exécution")

    response = test_client.post("/v2/broadcast/process-due")

    # Le endpoint doit continuer malgré l'erreur
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0  # Aucune exécution réussie
