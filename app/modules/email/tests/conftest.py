"""
Fixtures pour les tests Email v2

Hérite des fixtures globales de app/conftest.py.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

from app.modules.email.models import EmailStatus, EmailType


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


# ============================================================================
# FIXTURES EMAIL SERVICE
# ============================================================================

@pytest.fixture
def mock_email_service():
    """Mock EmailService pour les tests"""
    mock_service = MagicMock()

    # Configuration des méthodes par défaut
    mock_service.get_config.return_value = None
    mock_service.create_config.return_value = None
    mock_service.update_config.return_value = None
    mock_service.verify_config.return_value = (False, "Non configuré")

    mock_service.get_template.return_value = None
    mock_service.get_template_by_code.return_value = None
    mock_service.create_template.return_value = None
    mock_service.update_template.return_value = None
    mock_service.list_templates.return_value = []

    mock_service.send_email.return_value = None
    mock_service.send_bulk.return_value = None
    mock_service.process_queue.return_value = 0

    mock_service.get_log.return_value = None
    mock_service.list_logs.return_value = ([], 0)

    mock_service.get_dashboard.return_value = None

    return mock_service


# ============================================================================
# FIXTURES DONNÉES EMAIL CONFIG
# ============================================================================

@pytest.fixture
def email_config_data():
    """Données de configuration email sample"""
    return {
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_username": "noreply@example.com",
        "smtp_password": "secret123",
        "smtp_use_tls": True,
        "smtp_use_ssl": False,
        "provider": "smtp",
        "api_key": None,
        "api_endpoint": None,
        "from_email": "noreply@example.com",
        "from_name": "AZALS Platform",
        "reply_to_email": "support@example.com",
        "max_emails_per_hour": 100,
        "max_emails_per_day": 1000,
        "track_opens": True,
        "track_clicks": True,
    }


@pytest.fixture
def email_config(email_config_data, tenant_id):
    """Instance configuration email sample"""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "smtp_host": email_config_data["smtp_host"],
        "smtp_port": email_config_data["smtp_port"],
        "smtp_username": email_config_data["smtp_username"],
        "smtp_use_tls": email_config_data["smtp_use_tls"],
        "smtp_use_ssl": email_config_data["smtp_use_ssl"],
        "provider": email_config_data["provider"],
        "api_endpoint": email_config_data["api_endpoint"],
        "from_email": email_config_data["from_email"],
        "from_name": email_config_data["from_name"],
        "reply_to_email": email_config_data["reply_to_email"],
        "max_emails_per_hour": email_config_data["max_emails_per_hour"],
        "max_emails_per_day": email_config_data["max_emails_per_day"],
        "track_opens": email_config_data["track_opens"],
        "track_clicks": email_config_data["track_clicks"],
        "is_active": True,
        "is_verified": False,
        "last_verified_at": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


# ============================================================================
# FIXTURES DONNÉES EMAIL TEMPLATE
# ============================================================================

@pytest.fixture
def email_template_data():
    """Données de template email sample"""
    return {
        "code": "welcome",
        "name": "Email de bienvenue",
        "email_type": "TRANSACTIONAL",
        "subject": "Bienvenue {{name}}!",
        "body_html": "<h1>Bienvenue {{name}}</h1><p>Votre compte est créé.</p>",
        "body_text": "Bienvenue {{name}}! Votre compte est créé.",
        "variables": ["name"],
        "language": "fr",
    }


@pytest.fixture
def email_template(email_template_data, tenant_id):
    """Instance template email sample"""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "code": email_template_data["code"],
        "name": email_template_data["name"],
        "email_type": email_template_data["email_type"],
        "subject": email_template_data["subject"],
        "body_html": email_template_data["body_html"],
        "body_text": email_template_data["body_text"],
        "variables": email_template_data["variables"],
        "language": email_template_data["language"],
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def email_template_list(email_template):
    """Liste de templates email sample"""
    return [
        email_template,
        {
            **email_template,
            "id": str(uuid4()),
            "code": "password_reset",
            "name": "Réinitialisation mot de passe",
            "subject": "Réinitialisation de votre mot de passe",
        },
    ]


# ============================================================================
# FIXTURES DONNÉES EMAIL SEND
# ============================================================================

@pytest.fixture
def send_email_data():
    """Données d'envoi d'email sample"""
    return {
        "to_email": "user@example.com",
        "to_name": "John Doe",
        "email_type": "TRANSACTIONAL",
        "subject": "Test Email",
        "body_html": "<p>Test email content</p>",
        "body_text": "Test email content",
        "cc_emails": [],
        "bcc_emails": [],
        "variables": {},
        "attachments": [],
        "priority": 1,
        "schedule_at": None,
        "reference_type": None,
        "reference_id": None,
        "template_code": None,
    }


@pytest.fixture
def send_email_response(send_email_data):
    """Réponse d'envoi d'email sample"""
    return {
        "id": str(uuid4()),
        "status": "QUEUED",
        "to_email": send_email_data["to_email"],
        "subject": send_email_data["subject"],
        "queued_at": datetime.utcnow().isoformat(),
        "message": "Email mis en file d'attente",
    }


@pytest.fixture
def bulk_send_data():
    """Données d'envoi en masse sample"""
    return {
        "email_type": "MARKETING",
        "template_code": "newsletter",
        "base_variables": {"company": "AZALS"},
        "priority": 2,
        "recipients": [
            {"email": "user1@example.com", "name": "User 1", "variables": {"name": "User 1"}},
            {"email": "user2@example.com", "name": "User 2", "variables": {"name": "User 2"}},
        ],
    }


@pytest.fixture
def bulk_send_response():
    """Réponse d'envoi en masse sample"""
    return {
        "total": 2,
        "queued": 2,
        "failed": 0,
        "email_ids": [str(uuid4()), str(uuid4())],
    }


# ============================================================================
# FIXTURES DONNÉES EMAIL LOG
# ============================================================================

@pytest.fixture
def email_log(tenant_id, user_id):
    """Instance log email sample"""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "email_type": "TRANSACTIONAL",
        "to_email": "user@example.com",
        "to_name": "John Doe",
        "cc_emails": [],
        "bcc_emails": [],
        "subject": "Test Email",
        "body_html": "<p>Test email content</p>",
        "body_text": "Test email content",
        "variables_used": {},
        "attachments": [],
        "status": "SENT",
        "provider": "smtp",
        "reference_type": None,
        "reference_id": None,
        "priority": 1,
        "retry_count": 0,
        "max_retries": 3,
        "created_by": user_id,
        "queued_at": datetime.utcnow().isoformat(),
        "sent_at": datetime.utcnow().isoformat(),
        "delivered_at": None,
        "opened_at": None,
        "clicked_at": None,
        "bounced_at": None,
        "failed_at": None,
        "error_message": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def email_log_list(email_log):
    """Liste de logs email sample"""
    return [
        email_log,
        {
            **email_log,
            "id": str(uuid4()),
            "status": "QUEUED",
            "sent_at": None,
        },
    ]


# ============================================================================
# FIXTURES DASHBOARD
# ============================================================================

@pytest.fixture
def email_stats():
    """Statistiques email sample"""
    return {
        "total_sent": 100,
        "total_delivered": 95,
        "total_opened": 60,
        "total_clicked": 20,
        "total_bounced": 3,
        "total_failed": 2,
        "delivery_rate": 95.0,
        "open_rate": 63.16,
        "click_rate": 33.33,
        "bounce_rate": 3.0,
    }


@pytest.fixture
def email_dashboard(email_config, email_stats, email_log_list):
    """Dashboard email sample"""
    return {
        "config": email_config,
        "stats_today": email_stats,
        "stats_month": email_stats,
        "by_type": [
            {
                "email_type": "TRANSACTIONAL",
                "count": 50,
                "delivered": 48,
                "opened": 30,
                "clicked": 10,
                "bounced": 1,
            },
            {
                "email_type": "MARKETING",
                "count": 50,
                "delivered": 47,
                "opened": 30,
                "clicked": 10,
                "bounced": 2,
            },
        ],
        "recent_failures": [],
        "queue_size": 5,
    }
