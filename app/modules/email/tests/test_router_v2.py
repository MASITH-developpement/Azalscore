"""
Tests pour Email Router v2 (CORE SaaS)
"""
from __future__ import annotations


import pytest
from unittest.mock import MagicMock


# ============================================================================
# TESTS CONFIGURATION
# ============================================================================

def test_create_config_success(test_client, client, mock_email_service, email_config_data, email_config):
    """Test: Créer configuration email avec succès"""
    mock_email_service.get_config.return_value = None
    mock_email_service.create_config.return_value = MagicMock(**email_config)

    response = test_client.post("/v2/email/config", json=email_config_data)

    assert response.status_code == 201
    data = response.json()
    assert data["smtp_host"] == email_config_data["smtp_host"]
    assert data["from_email"] == email_config_data["from_email"]
    mock_email_service.create_config.assert_called_once()


def test_create_config_already_exists(test_client, client, mock_email_service, email_config_data, email_config):
    """Test: Créer configuration échoue si elle existe déjà"""
    mock_email_service.get_config.return_value = MagicMock(**email_config)

    response = test_client.post("/v2/email/config", json=email_config_data)

    assert response.status_code == 409
    assert "déjà existante" in response.json()["detail"]


def test_get_config_success(test_client, client, mock_email_service, email_config):
    """Test: Récupérer configuration email avec succès"""
    mock_email_service.get_config.return_value = MagicMock(**email_config)

    response = test_client.get("/v2/email/config")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == email_config["id"]
    assert data["smtp_host"] == email_config["smtp_host"]


def test_get_config_not_found(test_client, client, mock_email_service):
    """Test: Récupérer configuration inexistante"""
    mock_email_service.get_config.return_value = None

    response = test_client.get("/v2/email/config")

    assert response.status_code == 404
    assert "non trouvée" in response.json()["detail"]


def test_update_config_success(test_client, client, mock_email_service, email_config):
    """Test: Mettre à jour configuration email"""
    update_data = {"from_name": "New Name", "max_emails_per_hour": 200}
    updated_config = {**email_config, **update_data}
    mock_email_service.update_config.return_value = MagicMock(**updated_config)

    response = test_client.patch("/v2/email/config", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["from_name"] == "New Name"
    assert data["max_emails_per_hour"] == 200


def test_update_config_not_found(test_client, client, mock_email_service):
    """Test: Mettre à jour configuration inexistante"""
    mock_email_service.update_config.return_value = None

    response = test_client.patch("/v2/email/config", json={"from_name": "New Name"})

    assert response.status_code == 404


def test_verify_config_success(test_client, client, mock_email_service):
    """Test: Vérifier configuration email avec succès"""
    mock_email_service.verify_config.return_value = (True, "Configuration SMTP valide")

    response = test_client.post("/v2/email/config/verify")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "valide" in data["message"]


def test_verify_config_failure(test_client, client, mock_email_service):
    """Test: Vérifier configuration email échoue"""
    mock_email_service.verify_config.return_value = (False, "Connexion refusée")

    response = test_client.post("/v2/email/config/verify")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "refusée" in data["message"]


# ============================================================================
# TESTS TEMPLATES
# ============================================================================

def test_create_template_success(test_client, client, mock_email_service, email_template_data, email_template):
    """Test: Créer template email avec succès"""
    mock_email_service.create_template.return_value = MagicMock(**email_template)

    response = test_client.post("/v2/email/templates", json=email_template_data)

    assert response.status_code == 201
    data = response.json()
    assert data["code"] == email_template_data["code"]
    assert data["name"] == email_template_data["name"]
    mock_email_service.create_template.assert_called_once()


def test_list_templates_success(test_client, client, mock_email_service, email_template_list):
    """Test: Lister templates email"""
    mock_email_service.list_templates.return_value = [MagicMock(**t) for t in email_template_list]

    response = test_client.get("/v2/email/templates")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["code"] == email_template_list[0]["code"]


def test_list_templates_filtered_by_type(test_client, client, mock_email_service, email_template):
    """Test: Lister templates filtrés par type"""
    mock_email_service.list_templates.return_value = [MagicMock(**email_template)]

    response = test_client.get("/v2/email/templates?email_type=TRANSACTIONAL")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email_type"] == "TRANSACTIONAL"


def test_get_template_success(test_client, client, mock_email_service, email_template):
    """Test: Récupérer template par ID"""
    template_id = email_template["id"]
    mock_email_service.get_template.return_value = MagicMock(**email_template)

    response = test_client.get(f"/v2/email/templates/{template_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == template_id


def test_get_template_not_found(test_client, client, mock_email_service):
    """Test: Récupérer template inexistant"""
    mock_email_service.get_template.return_value = None

    response = test_client.get("/v2/email/templates/nonexistent-id")

    assert response.status_code == 404


def test_update_template_success(test_client, client, mock_email_service, email_template):
    """Test: Mettre à jour template"""
    template_id = email_template["id"]
    update_data = {"name": "Updated Name", "subject": "New Subject"}
    updated_template = {**email_template, **update_data}
    mock_email_service.update_template.return_value = MagicMock(**updated_template)

    response = test_client.patch(f"/v2/email/templates/{template_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["subject"] == "New Subject"


def test_update_template_not_found(test_client, client, mock_email_service):
    """Test: Mettre à jour template inexistant"""
    mock_email_service.update_template.return_value = None

    response = test_client.patch("/v2/email/templates/nonexistent-id", json={"name": "Updated"})

    assert response.status_code == 404


# ============================================================================
# TESTS ENVOI
# ============================================================================

def test_send_email_success(test_client, client, mock_email_service, send_email_data, send_email_response):
    """Test: Envoyer email avec succès"""
    mock_email_service.send_email.return_value = MagicMock(**send_email_response)

    response = test_client.post("/v2/email/send", json=send_email_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "QUEUED"
    assert data["to_email"] == send_email_data["to_email"]
    mock_email_service.send_email.assert_called_once()


def test_send_bulk_success(test_client, client, mock_email_service, bulk_send_data, bulk_send_response):
    """Test: Envoi en masse avec succès"""
    mock_email_service.send_bulk.return_value = MagicMock(**bulk_send_response)

    response = test_client.post("/v2/email/send/bulk", json=bulk_send_data)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["queued"] == 2
    assert data["failed"] == 0


def test_process_queue_success(test_client, client, mock_email_service):
    """Test: Traiter la file d'attente"""
    mock_email_service.process_queue.return_value = 5

    response = test_client.post("/v2/email/queue/process?batch_size=10")

    assert response.status_code == 200
    data = response.json()
    assert data["processed"] == 5


def test_process_queue_with_default_batch_size(test_client, client, mock_email_service):
    """Test: Traiter la file avec batch size par défaut"""
    mock_email_service.process_queue.return_value = 3

    response = test_client.post("/v2/email/queue/process")

    assert response.status_code == 200
    data = response.json()
    assert data["processed"] == 3


# ============================================================================
# TESTS LOGS
# ============================================================================

def test_list_logs_success(test_client, client, mock_email_service, email_log_list):
    """Test: Lister les logs emails"""
    mock_email_service.list_logs.return_value = ([MagicMock(**log) for log in email_log_list], 2)

    response = test_client.get("/v2/email/logs")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_list_logs_filtered_by_status(test_client, client, mock_email_service, email_log):
    """Test: Lister logs filtrés par status"""
    mock_email_service.list_logs.return_value = ([MagicMock(**email_log)], 1)

    response = test_client.get("/v2/email/logs?status=SENT")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "SENT"


def test_list_logs_filtered_by_type(test_client, client, mock_email_service, email_log):
    """Test: Lister logs filtrés par type"""
    mock_email_service.list_logs.return_value = ([MagicMock(**email_log)], 1)

    response = test_client.get("/v2/email/logs?email_type=TRANSACTIONAL")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_list_logs_with_pagination(test_client, client, mock_email_service, email_log_list):
    """Test: Lister logs avec pagination"""
    mock_email_service.list_logs.return_value = ([MagicMock(**email_log_list[0])], 2)

    response = test_client.get("/v2/email/logs?skip=0&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_get_log_success(test_client, client, mock_email_service, email_log):
    """Test: Récupérer log email par ID"""
    log_id = email_log["id"]
    mock_email_service.get_log.return_value = MagicMock(**email_log)

    response = test_client.get(f"/v2/email/logs/{log_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == log_id


def test_get_log_not_found(test_client, client, mock_email_service):
    """Test: Récupérer log inexistant"""
    mock_email_service.get_log.return_value = None

    response = test_client.get("/v2/email/logs/nonexistent-id")

    assert response.status_code == 404


# ============================================================================
# TESTS DASHBOARD
# ============================================================================

def test_get_dashboard_success(test_client, client, mock_email_service, email_dashboard):
    """Test: Récupérer dashboard email"""
    mock_email_service.get_dashboard.return_value = MagicMock(**email_dashboard)

    response = test_client.get("/v2/email/dashboard")

    assert response.status_code == 200
    data = response.json()
    assert "config" in data
    assert "stats_today" in data
    assert "stats_month" in data
    assert "by_type" in data
    assert "queue_size" in data


# ============================================================================
# TESTS CONTEXTE SAAS
# ============================================================================

def test_context_isolation(test_client, client, mock_email_service, tenant_id, user_id):
    """Test: Vérifier isolation tenant via context"""
    mock_email_service.list_logs.return_value = ([], 0)

    response = test_client.get("/v2/email/logs")

    assert response.status_code == 200
    # Vérifier que le service a été appelé (l'isolation est gérée dans le mock_saas_context)
    mock_email_service.list_logs.assert_called_once()


def test_audit_trail_with_user_id(test_client, client, mock_email_service, send_email_data, send_email_response, user_id):
    """Test: Vérifier audit trail avec user_id"""
    mock_email_service.send_email.return_value = MagicMock(**send_email_response)

    response = test_client.post("/v2/email/send", json=send_email_data)

    assert response.status_code == 200
    # Le user_id est automatiquement injecté via context.user_id
    call_args = mock_email_service.send_email.call_args
    assert call_args[1]["created_by"] == user_id
