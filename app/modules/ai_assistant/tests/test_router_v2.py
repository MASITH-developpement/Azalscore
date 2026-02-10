"""Tests pour le router v2 du module AI Assistant - CORE SaaS v2."""

import pytest


BASE_URL = "/v2/ai"


# ============================================================================
# TESTS CONFIGURATION
# ============================================================================

def test_get_config(test_client):
    response = test_client.get(f"{BASE_URL}/config")
    assert response.status_code == 200
    data = response.json()
    assert data["is_enabled"] is True
    assert "enabled_features" in data


def test_update_config(test_client):
    update_data = {"daily_request_limit": 2000, "response_language": "en"}
    response = test_client.put(f"{BASE_URL}/config", json=update_data)
    assert response.status_code == 200


# ============================================================================
# TESTS CONVERSATIONS
# ============================================================================

def test_create_conversation_success(test_client, mock_ai_service, sample_conversation_data):
    response = test_client.post(f"{BASE_URL}/conversations", json=sample_conversation_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == sample_conversation_data["title"]
    assert data["is_active"] is True


def test_list_conversations(test_client):
    response = test_client.get(f"{BASE_URL}/conversations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_list_conversations_active_only(test_client):
    response = test_client.get(f"{BASE_URL}/conversations", params={"active_only": True})
    assert response.status_code == 200


def test_list_conversations_pagination(test_client):
    response = test_client.get(f"{BASE_URL}/conversations", params={"skip": 0, "limit": 10})
    assert response.status_code == 200


def test_get_conversation_success(test_client):
    response = test_client.get(f"{BASE_URL}/conversations/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1


def test_get_conversation_not_found(test_client, mock_ai_service, monkeypatch):
    def mock_get(self, conversation_id):
        return None

    from app.modules.ai_assistant import service
    monkeypatch.setattr(service.AIAssistantService, "get_conversation", mock_get)

    response = test_client.get(f"{BASE_URL}/conversations/999")
    assert response.status_code == 404


def test_add_message_success(test_client, mock_ai_service, sample_message_data):
    response = test_client.post(f"{BASE_URL}/conversations/1/messages", json=sample_message_data)
    assert response.status_code == 201
    data = response.json()
    assert "user_message" in data
    assert "assistant_message" in data
    assert data["user_message"]["role"] == "user"
    assert data["assistant_message"]["role"] == "assistant"


# ============================================================================
# TESTS ANALYSES
# ============================================================================

def test_create_analysis_success(test_client, mock_ai_service, sample_analysis_data):
    response = test_client.post(f"{BASE_URL}/analyses", json=sample_analysis_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == sample_analysis_data["title"]
    assert data["analysis_type"] == sample_analysis_data["analysis_type"]


def test_list_analyses(test_client):
    response = test_client.get(f"{BASE_URL}/analyses")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_analyses_by_type(test_client):
    response = test_client.get(f"{BASE_URL}/analyses", params={"analysis_type": "360"})
    assert response.status_code == 200


def test_list_analyses_pagination(test_client):
    response = test_client.get(f"{BASE_URL}/analyses", params={"skip": 0, "limit": 20})
    assert response.status_code == 200


def test_get_analysis_success(test_client):
    response = test_client.get(f"{BASE_URL}/analyses/1")
    assert response.status_code == 200
    data = response.json()
    assert "findings" in data
    assert "recommendations" in data


def test_get_analysis_not_found(test_client, mock_ai_service, monkeypatch):
    def mock_get(self, analysis_id):
        return None

    from app.modules.ai_assistant import service
    monkeypatch.setattr(service.AIAssistantService, "get_analysis", mock_get)

    response = test_client.get(f"{BASE_URL}/analyses/999")
    assert response.status_code == 404


# ============================================================================
# TESTS DECISION SUPPORT
# ============================================================================

def test_create_decision_support_success(test_client, mock_ai_service, sample_decision_data):
    response = test_client.post(f"{BASE_URL}/decisions", json=sample_decision_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == sample_decision_data["title"]
    assert data["status"] == "pending_review"


def test_list_pending_decisions(test_client):
    response = test_client.get(f"{BASE_URL}/decisions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_list_pending_decisions_pagination(test_client):
    response = test_client.get(f"{BASE_URL}/decisions", params={"skip": 0, "limit": 25})
    assert response.status_code == 200


def test_get_decision_success(test_client):
    response = test_client.get(f"{BASE_URL}/decisions/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1


def test_get_decision_not_found(test_client, mock_ai_service, monkeypatch):
    def mock_get(self, decision_id):
        return None

    from app.modules.ai_assistant import service
    monkeypatch.setattr(service.AIAssistantService, "get_decision", mock_get)

    response = test_client.get(f"{BASE_URL}/decisions/999")
    assert response.status_code == 404


def test_confirm_decision_success(test_client):
    confirmation_data = {"decision_made": "approved", "notes": "Decision approved"}
    response = test_client.post(f"{BASE_URL}/decisions/1/confirm", json=confirmation_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"


def test_reject_decision_success(test_client):
    response = test_client.post(
        f"{BASE_URL}/decisions/1/reject",
        params={"reason": "Not aligned with strategy"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"


# ============================================================================
# TESTS RISK DETECTION
# ============================================================================

def test_create_risk_alert_success(test_client, mock_ai_service, sample_risk_data):
    response = test_client.post(f"{BASE_URL}/risks", json=sample_risk_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == sample_risk_data["title"]
    assert data["category"] == sample_risk_data["category"]
    assert data["status"] == "active"


def test_list_active_risks(test_client):
    response = test_client.get(f"{BASE_URL}/risks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_list_active_risks_by_category(test_client):
    response = test_client.get(f"{BASE_URL}/risks", params={"category": "financial"})
    assert response.status_code == 200


def test_list_active_risks_by_level(test_client):
    response = test_client.get(f"{BASE_URL}/risks", params={"level": "high"})
    assert response.status_code == 200


def test_list_active_risks_pagination(test_client):
    response = test_client.get(f"{BASE_URL}/risks", params={"skip": 0, "limit": 30})
    assert response.status_code == 200


def test_get_risk_alert_success(test_client):
    response = test_client.get(f"{BASE_URL}/risks/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1


def test_get_risk_alert_not_found(test_client, mock_ai_service, monkeypatch):
    def mock_get(self, alert_id):
        return None

    from app.modules.ai_assistant import service
    monkeypatch.setattr(service.AIAssistantService, "get_risk_alert", mock_get)

    response = test_client.get(f"{BASE_URL}/risks/999")
    assert response.status_code == 404


def test_acknowledge_risk_success(test_client):
    ack_data = {"notes": "Risk acknowledged by team"}
    response = test_client.post(f"{BASE_URL}/risks/1/acknowledge", json=ack_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "acknowledged"


def test_resolve_risk_success(test_client):
    resolve_data = {"resolution_notes": "Issue fixed", "actions_taken": ["Action 1"]}
    response = test_client.post(f"{BASE_URL}/risks/1/resolve", json=resolve_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "resolved"


# ============================================================================
# TESTS PREDICTIONS
# ============================================================================

def test_create_prediction_success(test_client, mock_ai_service, sample_prediction_data):
    response = test_client.post(f"{BASE_URL}/predictions", json=sample_prediction_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == sample_prediction_data["title"]
    assert data["prediction_type"] == sample_prediction_data["prediction_type"]


def test_list_predictions(test_client):
    response = test_client.get(f"{BASE_URL}/predictions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_predictions_by_type(test_client):
    response = test_client.get(f"{BASE_URL}/predictions", params={"prediction_type": "financial"})
    assert response.status_code == 200


def test_list_predictions_pagination(test_client):
    response = test_client.get(f"{BASE_URL}/predictions", params={"skip": 0, "limit": 15})
    assert response.status_code == 200


def test_get_prediction_success(test_client):
    response = test_client.get(f"{BASE_URL}/predictions/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1


def test_get_prediction_not_found(test_client, mock_ai_service, monkeypatch):
    def mock_get(self, prediction_id):
        return None

    from app.modules.ai_assistant import service
    monkeypatch.setattr(service.AIAssistantService, "get_prediction", mock_get)

    response = test_client.get(f"{BASE_URL}/predictions/999")
    assert response.status_code == 404


# ============================================================================
# TESTS FEEDBACK
# ============================================================================

def test_add_feedback_success(test_client, mock_ai_service, sample_feedback_data):
    response = test_client.post(f"{BASE_URL}/feedback", json=sample_feedback_data)
    assert response.status_code == 201
    data = response.json()
    assert data["rating"] == sample_feedback_data["rating"]
    assert data["is_helpful"] is True


# ============================================================================
# TESTS SYNTHESIS
# ============================================================================

def test_generate_synthesis_success(test_client, mock_ai_service, sample_synthesis_data):
    response = test_client.post(f"{BASE_URL}/synthesis", json=sample_synthesis_data)
    assert response.status_code == 200
    data = response.json()
    assert "executive_summary" in data
    assert "key_metrics" in data
    assert "highlights" in data
    assert "concerns" in data
    assert "action_items" in data


# ============================================================================
# TESTS STATISTICS & HEALTH
# ============================================================================

def test_get_stats(test_client):
    response = test_client.get(f"{BASE_URL}/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_conversations" in data
    assert "total_messages" in data
    assert "total_analyses" in data
    assert "pending_decisions" in data
    assert "active_risks" in data
    assert "critical_risks" in data
    assert "avg_response_time_ms" in data


def test_health_check(test_client):
    response = test_client.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "features_status" in data
    assert "response_time_ms" in data


# ============================================================================
# TESTS AUDIT LOGS
# ============================================================================

def test_get_audit_logs(test_client):
    response = test_client.get(f"{BASE_URL}/audit")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_audit_logs_by_action(test_client):
    response = test_client.get(f"{BASE_URL}/audit", params={"action": "conversation_create"})
    assert response.status_code == 200


def test_get_audit_logs_pagination(test_client):
    response = test_client.get(f"{BASE_URL}/audit", params={"skip": 0, "limit": 50})
    assert response.status_code == 200


# ============================================================================
# TESTS VALIDATION & ERRORS
# ============================================================================

def test_create_conversation_missing_fields(test_client):
    response = test_client.post(f"{BASE_URL}/conversations", json={})
    assert response.status_code == 422


def test_create_analysis_missing_fields(test_client):
    response = test_client.post(f"{BASE_URL}/analyses", json={"title": "Only title"})
    assert response.status_code == 422


def test_create_decision_missing_fields(test_client):
    response = test_client.post(f"{BASE_URL}/decisions", json={"title": "Only title"})
    assert response.status_code == 422


def test_create_risk_missing_fields(test_client):
    response = test_client.post(f"{BASE_URL}/risks", json={"title": "Only title"})
    assert response.status_code == 422


def test_create_prediction_missing_fields(test_client):
    response = test_client.post(f"{BASE_URL}/predictions", json={"title": "Only title"})
    assert response.status_code == 422


# ============================================================================
# TESTS TENANT ISOLATION
# ============================================================================

def test_conversations_tenant_isolation(test_client):
    response = test_client.get(f"{BASE_URL}/conversations")
    assert response.status_code == 200


def test_analyses_tenant_isolation(test_client):
    response = test_client.get(f"{BASE_URL}/analyses")
    assert response.status_code == 200


def test_decisions_tenant_isolation(test_client):
    response = test_client.get(f"{BASE_URL}/decisions")
    assert response.status_code == 200


def test_risks_tenant_isolation(test_client):
    response = test_client.get(f"{BASE_URL}/risks")
    assert response.status_code == 200


def test_predictions_tenant_isolation(test_client):
    response = test_client.get(f"{BASE_URL}/predictions")
    assert response.status_code == 200
